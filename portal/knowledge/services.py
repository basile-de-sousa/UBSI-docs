"""All lifecycle writes serialize account checks, project state and content."""
from copy import deepcopy
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.http import Http404
from django.utils import timezone

from accounts.services import locked_admin
from accounts.models import User
from search import indexing
from .models import ApplicationCode, ContentDraft, ContentRecord, ContentRevision, DraftRelation, Kind, ProjectState, Relation, RevisionRelation, State
from .schema import RELATIONS, application_code, normalise

UNSET = object()


class Conflict(Exception):
    def __init__(self, message="Le contenu a changé entre-temps. Vos saisies sont conservées ; ouvrez la version actuelle dans un autre onglet avant de les reprendre."):
        self.message = message


def lock_project(actor_id):
    actor = locked_admin(actor_id)
    return actor, ProjectState.objects.select_for_update().get(pk=1)


def locked_record(record_id):
    # PostgreSQL cannot lock the nullable revision side of this outer join.
    record = ContentRecord.objects.select_for_update(of=("self",)).select_related("current_revision").filter(pk=record_id, discarded_at__isnull=True).first()
    if not record:
        raise Http404
    return record


def check_version(record, expected):
    if record.edit_version != expected:
        raise Conflict


def advance(record):
    record.edit_version += 1
    record.updated_at = timezone.now()
    record.save()


def relations_for(kind, record_id, values, publishing=False):
    if not isinstance(values, dict) or set(values) - RELATIONS[kind].keys():
        raise ValidationError("Les liens transmis ne sont pas autorisés.")
    clean = []
    for relation_kind, expected_kind in RELATIONS[kind].items():
        raw_ids = values.get(relation_kind, [])
        try:
            if not isinstance(raw_ids, (list, tuple)) or len(raw_ids) > 100:
                raise ValueError
            ids = {UUID(str(value)) for value in raw_ids}
        except (ValueError, TypeError, AttributeError):
            raise ValidationError({relation_kind: "La sélection contient un identifiant invalide ou trop de liens."}) from None
        targets = list(ContentRecord.objects.select_related("current_revision").filter(pk__in=ids, discarded_at__isnull=True))
        if len(targets) != len(ids) or record_id in ids or any(expected_kind and target.kind != expected_kind for target in targets):
            raise ValidationError({relation_kind: "Un lien est invalide, supprimé ou renvoie vers le contenu lui-même."})
        if publishing and any(target.state != State.PUBLISHED or not target.current_revision_id for target in targets):
            raise ValidationError({relation_kind: "Publiez les contenus liés ou retirez les liens vers leurs brouillons/archives."})
        clean.extend((relation_kind, target) for target in targets)
    if publishing and kind in {Kind.SPECIFICATION, Kind.DOCUMENT} and not any(key == Relation.APPLICATION for key, _ in clean):
        raise ValidationError({"application": "Associez au moins une application publiée."})
    return clean


def reserve_code(record, code):
    code = application_code(code)
    reservation = ApplicationCode.objects.filter(code=code).first()
    collision = ContentRecord.objects.filter(reference=code).exclude(pk=record.pk).exists()
    if collision or (reservation and reservation.record_id != record.pk):
        raise ValidationError({"code": "Ce code est déjà réservé, y compris dans l’historique."})
    ApplicationCode.objects.get_or_create(code=code, defaults={"record": record})


def allocate_reference(project, kind):
    prefix = {Kind.SPECIFICATION: "SPEC", Kind.FAQ: "FAQ", Kind.EPIC: "EPIC", Kind.STORY: "US", Kind.SPRINT: "SPRINT", Kind.DOCUMENT: "DOC"}[kind]
    number = project.counters.get(kind, 0)
    while True:
        number += 1
        reference = f"{prefix}-{number:03d}"
        if not ContentRecord.objects.filter(reference=reference).exists() and not ApplicationCode.objects.filter(code=reference).exists():
            break
    project.counters[kind] = number
    project.save(update_fields=["counters"])
    return reference


def write_draft(record, actor, title, payload, links, responsible=UNSET):
    draft, _ = ContentDraft.objects.update_or_create(record=record, defaults={"title": title, "payload": payload, "updated_by": actor, "updated_at": timezone.now()})
    DraftRelation.objects.filter(draft=draft).delete()
    DraftRelation.objects.bulk_create([DraftRelation(draft=draft, kind=kind, target=target) for kind, target in links])
    if responsible is not UNSET:
        draft.responsible = responsible
        draft.save(update_fields=["responsible"])
    return draft


def resolve_responsible(record, value):
    if value is UNSET:
        return UNSET
    if value is None:
        return None
    member = User.objects.filter(pk=value).first()
    previous = record.current_revision.responsible_id if record.current_revision_id else None
    if not member or (not member.is_active and member.pk != previous):
        raise ValidationError({"responsible": "Sélectionnez un membre actif. Une attribution historique peut être conservée."})
    return member


@transaction.atomic
def create_draft(actor_id, record_id, kind, title, payload, relations, responsible_id=UNSET):
    actor, project = lock_project(actor_id)
    existing = ContentRecord.objects.filter(pk=record_id).first()
    if existing:
        if existing.kind != kind or existing.created_by_id != actor.pk or existing.discarded_at:
            raise Conflict("Cette demande de création a déjà été utilisée. Rechargez le formulaire.")
        return existing
    title, payload, _, _, _ = normalise(kind, title, payload)
    links = relations_for(kind, record_id, relations)
    reference = payload["code"] if kind == Kind.APPLICATION else allocate_reference(project, kind)
    if ContentRecord.objects.filter(reference=reference).exists() or ApplicationCode.objects.filter(code=reference).exists():
        raise ValidationError({"code": "Ce code est déjà réservé."})
    record = ContentRecord.objects.create(id=record_id, kind=kind, reference=reference, created_by=actor)
    if kind == Kind.APPLICATION:
        reserve_code(record, payload["code"])
    write_draft(record, actor, title, payload, links, resolve_responsible(record, responsible_id))
    return record


@transaction.atomic
def begin_edit(actor_id, record_id, expected_version):
    actor, _ = lock_project(actor_id)
    record = locked_record(record_id)
    if hasattr(record, "draft"):
        return record
    check_version(record, expected_version)
    from sprints.validation import editable_sprint
    editable_sprint(record)
    if record.state != State.PUBLISHED:
        raise Conflict("Restaurez une version depuis l’historique pour reprendre un contenu archivé.")
    revision = record.current_revision
    links = [(link.kind, link.target) for link in revision.relations.select_related("target")]
    draft = write_draft(record, actor, revision.title, deepcopy(revision.payload), links)
    draft.file_revision = revision.file_revision
    draft.save(update_fields=["file_revision"])
    draft.responsible = revision.responsible
    draft.save(update_fields=["responsible"])
    advance(record)
    return record


@transaction.atomic
def save_draft(actor_id, record_id, expected_version, title, payload, relations, responsible_id=UNSET):
    actor, _ = lock_project(actor_id)
    record = locked_record(record_id)
    check_version(record, expected_version)
    if not hasattr(record, "draft"):
        raise Conflict("Le brouillon n’existe plus. Vos saisies sont conservées.")
    title, payload, _, _, _ = normalise(record.kind, title, payload)
    links = relations_for(record.kind, record.pk, relations)
    responsible = resolve_responsible(record, responsible_id)
    from sprints.validation import closed_sprint_values
    closed_sprint_values(record, title, payload, record.draft.responsible if responsible is UNSET else responsible)
    write_draft(record, actor, title, payload, links, responsible)
    advance(record)
    return record


@transaction.atomic
def publish(actor_id, record_id, expected_version):
    actor, project = lock_project(actor_id)
    record = locked_record(record_id)
    if not hasattr(record, "draft") and record.state == State.PUBLISHED and record.current_revision.source_version == expected_version:
        return record
    check_version(record, expected_version)
    if not hasattr(record, "draft"):
        raise Conflict("Il n’existe aucun brouillon à publier.")
    draft = record.draft
    title, payload, html, text, sections = normalise(record.kind, draft.title, draft.payload, publishing=True)
    relation_ids = {}
    for link in draft.relations.all():
        relation_ids.setdefault(link.kind, []).append(link.target_id)
    links = relations_for(record.kind, record.pk, relation_ids, publishing=True)
    from sprints.validation import validate_publication
    validate_publication(record, title, payload, links, draft.responsible)
    if record.kind == Kind.DOCUMENT:
        from documents.services import validate_file
        validate_file(record, draft)
    if record.kind == Kind.APPLICATION:
        reserve_code(record, payload["code"])
    commit_revision(record, actor, project, title, payload, links, draft.responsible, html, text, sections, file_revision=draft.file_revision)
    draft.delete()
    return record


def commit_revision(record, actor, project, title, payload, links, responsible, html, text, sections, file_revision=None):
    """Internal publication primitive; caller holds account/project/record locks."""
    revision = ContentRevision.objects.create(record=record, file_revision=file_revision, number=record.revision_sequence + 1, source_version=record.edit_version, title=title, payload=payload, body_html=html, plain_text=text, author=actor, responsible=responsible)
    RevisionRelation.objects.bulk_create([RevisionRelation(revision=revision, kind=kind, target=target, target_title=target.current_revision.title, target_reference=target.display_reference) for kind, target in links])
    record.current_revision, record.revision_sequence, record.state = revision, revision.number, State.PUBLISHED
    advance(record)
    indexing.replace_passages(record, revision, sections)
    project.search_generation += 1
    project.save(update_fields=["search_generation"])
    return revision


def required_dependents(record):
    links = RevisionRelation.objects.filter(target=record, revision__record__state=State.PUBLISHED, revision_id=F("revision__record__current_revision_id"))
    return links.filter(kind=Relation.APPLICATION, revision__record__kind__in=[Kind.SPECIFICATION, Kind.EPIC, Kind.STORY, Kind.DOCUMENT]) | links.filter(kind=Relation.EPIC, revision__record__kind=Kind.STORY)


@transaction.atomic
def archive(actor_id, record_id, expected_version):
    _, project = lock_project(actor_id)
    record = locked_record(record_id)
    if record.state == State.ARCHIVED:
        return record
    check_version(record, expected_version)
    if record.state != State.PUBLISHED:
        raise Conflict("Seul un contenu publié peut être archivé.")
    from .models import SprintProgress
    if record.kind == Kind.SPRINT and record.current_revision.payload["sprint_state"] == SprintProgress.ACTIVE:
        raise ValidationError("Clôturez le sprint actif avant de l’archiver.")
    if required_dependents(record).exists():
        raise ValidationError("Des contenus publiés dépendent encore de ce contenu. Réaffectez-les ou archivez-les d’abord.")
    record.state = State.ARCHIVED
    advance(record)
    indexing.withdraw(record)
    project.search_generation += 1
    project.save(update_fields=["search_generation"])
    return record


@transaction.atomic
def restore_to_draft(actor_id, record_id, number, expected_version, replace_draft=False):
    actor, _ = lock_project(actor_id)
    record = locked_record(record_id)
    check_version(record, expected_version)
    if hasattr(record, "draft") and not replace_draft:
        raise Conflict("Un brouillon existe déjà. Confirmez son remplacement avant de restaurer.")
    revision = record.revisions.filter(number=number).first()
    if not revision:
        raise Http404
    from sprints.validation import closed_sprint_values
    closed_sprint_values(record, revision.title, revision.payload, revision.responsible)
    links = [(link.kind, link.target) for link in revision.relations.select_related("target")]
    draft = write_draft(record, actor, revision.title, deepcopy(revision.payload), links)
    draft.file_revision = revision.file_revision
    draft.save(update_fields=["file_revision"])
    draft.responsible = revision.responsible
    draft.save(update_fields=["responsible"])
    advance(record)
    return record


@transaction.atomic
def discard_draft(actor_id, record_id, expected_version):
    lock_project(actor_id)
    record = locked_record(record_id)
    check_version(record, expected_version)
    if not hasattr(record, "draft"):
        raise Conflict("Le brouillon n’existe plus.")
    if record.state == State.DRAFT:
        if record.incoming_drafts.exists() or record.incoming_revisions.exists():
            raise ValidationError("Ce brouillon est encore référencé. Retirez ses liens entrants avant de l’abandonner.")
        # A tombstone reserves identity/reference without offering permanent deletion.
        record.discarded_at = timezone.now()
    record.draft.delete()
    advance(record)
    return record
