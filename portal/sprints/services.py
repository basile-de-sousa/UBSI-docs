"""Explicit sprint publications and immutable closure, under one transaction."""
from copy import deepcopy

from django.core.exceptions import ValidationError
from django.db import transaction

from knowledge import services as knowledge
from knowledge.models import Kind, Relation, SprintProgress, State, StoryProgress
from knowledge.projections import published_records
from knowledge.schema import normalise
from .models import SprintClosureSnapshot, SprintSnapshotApplication, SprintSnapshotRow
from .validation import validate_publication


def assigned_stories(sprint):
    return published_records().filter(kind=Kind.STORY, current_revision__relations__kind=Relation.SPRINT, current_revision__relations__target=sprint).select_related("current_revision__responsible").order_by("reference")


def planned_sprints():
    return published_records().filter(kind=Kind.SPRINT, current_revision__payload__sprint_state=SprintProgress.PLANNED).order_by("current_revision__payload__start_date", "reference")


def close_report(sprint):
    return {"sprint": str(sprint.pk), "version": sprint.edit_version, "stories": {str(row.pk): row.edit_version for row in assigned_stories(sprint)}, "targets": {str(row.pk): row.edit_version for row in planned_sprints().exclude(pk=sprint.pk)}}


def ready_sprint(record, state):
    if record.kind != Kind.SPRINT or record.state != State.PUBLISHED or record.current_revision.payload["sprint_state"] != state:
        raise knowledge.Conflict("Le sprint n’est plus dans l’état attendu. Rechargez sa page.")
    if hasattr(record, "draft"):
        raise ValidationError("Publiez ou abandonnez le brouillon du sprint avant cette action.")


def prepared(record, payload, relation_ids, responsible, transition=False):
    title, payload, html, text, sections = normalise(record.kind, record.current_revision.title, payload, publishing=True)
    links = knowledge.relations_for(record.kind, record.pk, relation_ids, publishing=True)
    validate_publication(record, title, payload, links, responsible, transition=transition)
    return title, payload, links, responsible, html, text, sections


@transaction.atomic
def activate(actor_id, record_id, expected_version):
    actor, project = knowledge.lock_project(actor_id)
    record = knowledge.locked_record(record_id)
    if record.kind == Kind.SPRINT and record.state == State.PUBLISHED and record.current_revision.payload["sprint_state"] == SprintProgress.ACTIVE and record.current_revision.source_version == expected_version:
        return record
    knowledge.check_version(record, expected_version)
    ready_sprint(record, SprintProgress.PLANNED)
    if project.active_sprint_id or published_records().filter(kind=Kind.SPRINT, current_revision__payload__sprint_state=SprintProgress.ACTIVE).exists():
        raise ValidationError("Un sprint est déjà actif. Clôturez-le avant d’en démarrer un autre.")
    owner = record.current_revision.responsible
    if not owner or not owner.is_active:
        raise ValidationError("Le responsable du sprint doit être un membre actif pour le démarrer.")
    for story in assigned_stories(record):
        if not story.current_revision.responsible or not story.current_revision.responsible.is_active:
            raise ValidationError(f"Attribuez un responsable actif à {story.reference} avant de démarrer le sprint.")
    payload = deepcopy(record.current_revision.payload)
    payload["sprint_state"] = SprintProgress.ACTIVE
    values = prepared(record, payload, {}, owner, transition=True)
    knowledge.commit_revision(record, actor, project, *values)
    project.active_sprint = record
    project.save(update_fields=["active_sprint"])
    return record


@transaction.atomic
def close(actor_id, report, decisions):
    actor, project = knowledge.lock_project(actor_id)
    record = knowledge.locked_record(report["sprint"])
    previous = SprintClosureSnapshot.objects.filter(sprint=record).first()
    if previous:
        if previous.request_version == report["version"]:
            return record
        raise knowledge.Conflict("Ce sprint possède déjà un instantané de clôture.")
    knowledge.check_version(record, report["version"])
    ready_sprint(record, SprintProgress.ACTIVE)
    if project.active_sprint_id != record.pk:
        raise knowledge.Conflict("Le sprint actif a changé. Rechargez la page avant de clôturer.")
    members = list(assigned_stories(record))
    if {str(row.pk): row.edit_version for row in members} != report["stories"]:
        raise knowledge.Conflict("Les stories ou leurs affectations ont changé. Rechargez la clôture pour revoir la liste complète.")
    incomplete = {str(row.pk) for row in members if row.current_revision.payload["work_state"] not in {StoryProgress.DONE, StoryProgress.CANCELLED}}
    if set(decisions) != incomplete:
        raise ValidationError("Choisissez une décision pour chaque story inachevée, et uniquement celles-ci.")
    plans = []
    for member in members:
        story = knowledge.locked_record(member.pk)
        if hasattr(story, "draft"):
            raise ValidationError(f"Publiez ou abandonnez le brouillon de {story.reference} avant la clôture.")
        revision = story.current_revision
        links = list(revision.relations.select_related("target", "target__current_revision"))
        relation_ids = {}
        for link in links:
            if link.kind != Relation.SPRINT:
                relation_ids.setdefault(link.kind, []).append(link.target_id)
        payload = deepcopy(revision.payload)
        choice = decisions.get(str(story.pk))
        if choice == "backlog":
            payload["work_state"] = StoryProgress.BACKLOG
        elif choice:
            if choice not in report["targets"]:
                raise ValidationError("Le sprint de report ne figure pas dans la liste présentée.")
            target = knowledge.locked_record(choice)
            knowledge.check_version(target, report["targets"][choice])
            if target.kind != Kind.SPRINT or target.state != State.PUBLISHED or target.current_revision.payload["sprint_state"] != SprintProgress.PLANNED:
                raise ValidationError("Choisissez un sprint de report encore publié et planifié.")
            relation_ids[Relation.SPRINT] = [target.pk]
        try:
            values = prepared(story, payload, relation_ids, revision.responsible)
        except ValidationError as error:
            raise ValidationError(f"{story.reference} : {' ; '.join(error.messages)}") from None
        plans.append((story, revision, links, values))
    source = record.current_revision
    closed_payload = {**source.payload, "sprint_state": SprintProgress.CLOSED}
    closed_values = prepared(record, closed_payload, {}, source.responsible, transition=True)
    for story, revision, links, values in plans:
        knowledge.commit_revision(story, actor, project, *values)
    # Clear the singleton pointer before publishing closed state, in the same transaction.
    project.active_sprint = None
    project.save(update_fields=["active_sprint"])
    closed_revision = knowledge.commit_revision(record, actor, project, *closed_values)
    snapshot = SprintClosureSnapshot.objects.create(sprint=record, source_revision=source, closed_revision=closed_revision, request_version=report["version"], responsible_name=source.responsible.display_name)
    for story, revision, links, _ in plans:
        epic = next(link.target for link in links if link.kind == Relation.EPIC)
        row = SprintSnapshotRow.objects.create(snapshot=snapshot, story=story, story_revision=revision, reference=story.reference, title=revision.title, work_state=revision.payload["work_state"], responsible=revision.responsible, responsible_name=revision.responsible.display_name if revision.responsible else "", epic=epic, epic_reference=epic.reference, epic_title=epic.current_revision.title)
        SprintSnapshotApplication.objects.bulk_create([SprintSnapshotApplication(row=row, application=link.target, revision=link.target.current_revision, reference=link.target.display_reference, title=link.target.current_revision.title) for link in links if link.kind == Relation.APPLICATION])
    return record
