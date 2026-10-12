"""Cross-record publication invariants, called under the shared project lock."""
from django.core.exceptions import ValidationError
from django.db.models import F

from knowledge.models import Kind, Relation, RevisionRelation, SprintProgress, State
from .models import SprintClosureSnapshot


def current_links():
    return RevisionRelation.objects.filter(revision__record__state=State.PUBLISHED, revision_id=F("revision__record__current_revision_id"))


def editable_sprint(record):
    if record.kind == Kind.SPRINT and SprintClosureSnapshot.objects.filter(sprint=record).exists():
        from knowledge.services import Conflict
        raise Conflict("Un sprint clôturé ne peut plus être modifié. Son instantané reste consultable dans l’historique.")


def closed_sprint_values(record, title, payload, responsible):
    if record.kind != Kind.SPRINT:
        return
    snapshot = SprintClosureSnapshot.objects.filter(sprint=record).select_related("closed_revision").first()
    if snapshot:
        frozen = snapshot.closed_revision
        if title != frozen.title or payload != frozen.payload or (responsible.pk if responsible else None) != frozen.responsible_id:
            raise ValidationError("Un sprint clôturé ne peut être rouvert ni modifié. Seule sa version clôturée identique peut être restaurée pour republication après archivage.")


def validate_publication(record, title, payload, links, responsible, transition=False):
    groups = {}
    for key, target in links:
        groups.setdefault(key, []).append(target)
    applications = {item.pk for item in groups.get(Relation.APPLICATION, [])}
    if record.kind in {Kind.EPIC, Kind.STORY} and not applications:
        raise ValidationError({"application": "Associez au moins une application publiée."})
    if responsible and not responsible.is_active and (not record.current_revision_id or responsible.pk != record.current_revision.responsible_id):
        raise ValidationError({"responsible": "Le responsable choisi n’est plus actif."})
    if record.kind == Kind.EPIC:
        children = current_links().filter(kind=Relation.EPIC, target=record, revision__record__kind=Kind.STORY).select_related("revision__record")
        for child in children:
            child_apps = set(child.revision.relations.filter(kind=Relation.APPLICATION).values_list("target_id", flat=True))
            if not child_apps <= applications:
                raise ValidationError({"application": f"Les applications de {child.revision.record.reference} doivent rester couvertes. Réaffectez ou archivez cette story avant de retirer l’application."})
    if record.kind == Kind.STORY:
        parents = groups.get(Relation.EPIC, [])
        if len(parents) != 1:
            raise ValidationError({"epic": "Sélectionnez exactement un epic publié."})
        parent_apps = set(parents[0].current_revision.relations.filter(kind=Relation.APPLICATION).values_list("target_id", flat=True))
        if not applications <= parent_apps:
            raise ValidationError({"application": "Les applications de la story doivent appartenir à son epic parent."})
        assignments = groups.get(Relation.SPRINT, [])
        if len(assignments) > 1:
            raise ValidationError({"sprint": "Une story possède au plus un sprint courant."})
        if assignments:
            state = assignments[0].current_revision.payload["sprint_state"]
            if state == SprintProgress.CLOSED:
                raise ValidationError({"sprint": "Un sprint clôturé n’accepte plus d’affectation."})
            if state == SprintProgress.ACTIVE and (not responsible or not responsible.is_active):
                raise ValidationError({"responsible": "Une story affectée au sprint actif exige un responsable actif."})
        graph = {}
        for source, target in current_links().filter(kind=Relation.DEPENDENCY, revision__record__kind=Kind.STORY).exclude(revision__record=record).values_list("revision__record_id", "target_id"):
            graph.setdefault(source, set()).add(target)
        pending, visited = [target.pk for target in groups.get(Relation.DEPENDENCY, [])], set()
        while pending:
            target = pending.pop()
            if target == record.pk:
                raise ValidationError({"dependency": "Cette dépendance créerait un cycle entre les stories."})
            if target not in visited:
                visited.add(target)
                pending.extend(graph.get(target, []))
    if record.kind == Kind.SPRINT:
        if not responsible:
            raise ValidationError({"responsible": "Renseignez le responsable du sprint."})
        closed_sprint_values(record, title, payload, responsible)
        previous = record.current_revision.payload["sprint_state"] if record.current_revision_id else SprintProgress.PLANNED
        if not transition and payload["sprint_state"] != previous:
            raise ValidationError({"sprint_state": "Utilisez les actions explicites Démarrer ou Clôturer pour changer l’état du sprint."})
