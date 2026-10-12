from django.db import models
from django.db.models import F

from .models import ContentRecord, Kind, Relation, RevisionRelation, State

PATHS = {Kind.APPLICATION: "applications", Kind.SPECIFICATION: "specifications", Kind.FAQ: "faq", Kind.EPIC: "epics", Kind.STORY: "stories", Kind.SPRINT: "sprints", Kind.DOCUMENT: "documents"}


def canonical_url(record):
    return f"/{PATHS[record.kind]}/{record.pk}/"


def published_records():
    # Reader projections never join ContentDraft, even for an administrator reader.
    return ContentRecord.objects.filter(state=State.PUBLISHED, discarded_at__isnull=True, current_revision__isnull=False).select_related("current_revision", "current_revision__author")


def reader_links(record, revision=None):
    revision = revision or record.current_revision
    groups = {}
    for link in revision.relations.select_related("target", "target__current_revision").filter(target__state=State.PUBLISHED):
        label = "Epic parent" if record.kind == Kind.STORY and link.kind == Relation.EPIC else link.get_kind_display()
        groups.setdefault(label, {})[link.target.pk] = link.target
    if revision.pk == record.current_revision_id and record.state == State.PUBLISHED:
        incoming = RevisionRelation.objects.filter(target=record, revision__record__state=State.PUBLISHED, revision_id=F("revision__record__current_revision_id")).select_related("revision__record", "revision__record__current_revision")
        if record.kind == Kind.SPRINT:
            incoming = incoming.exclude(revision__record__kind=Kind.STORY)
        for link in incoming:
            source = link.revision.record
            label = "Stories dépendantes" if link.kind == Relation.DEPENDENCY else {Kind.EPIC: "Epics", Kind.STORY: "User stories", Kind.SPECIFICATION: "Spécifications", Kind.DOCUMENT: "Documents"}.get(source.kind, source.get_kind_display())
            groups.setdefault(label, {})[source.pk] = source
        if record.kind == Kind.EPIC:
            from sprints.models import SprintSnapshotRow
            stories = published_records().filter(kind=Kind.STORY, current_revision__relations__kind=Relation.EPIC, current_revision__relations__target=record)
            sprint_ids = RevisionRelation.objects.filter(revision_id__in=stories.values("current_revision_id"), kind=Relation.SPRINT).values_list("target_id", flat=True)
            historical_ids = SprintSnapshotRow.objects.filter(epic=record, story__state=State.PUBLISHED).values_list("snapshot_id", flat=True)
            for sprint in published_records().filter(kind=Kind.SPRINT).filter(models.Q(pk__in=sprint_ids) | models.Q(pk__in=historical_ids)):
                groups.setdefault("Sprints concernés", {})[sprint.pk] = sprint
    return [{"label": label, "items": [{"title": target.current_revision.title, "reference": target.display_reference, "url": canonical_url(target)} for target in values.values()]} for label, values in groups.items()]
