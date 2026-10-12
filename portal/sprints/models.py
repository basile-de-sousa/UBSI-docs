from django.conf import settings
from django.db import models

from knowledge.models import ImmutableModel, StoryProgress


class SprintClosureSnapshot(ImmutableModel):
    sprint = models.OneToOneField("knowledge.ContentRecord", primary_key=True, on_delete=models.PROTECT, related_name="closure")
    source_revision = models.ForeignKey("knowledge.ContentRevision", on_delete=models.PROTECT, related_name="closure_sources")
    closed_revision = models.OneToOneField("knowledge.ContentRevision", on_delete=models.PROTECT, related_name="closed_snapshot")
    request_version = models.PositiveBigIntegerField()
    responsible_name = models.CharField(max_length=150)


class SprintSnapshotRow(ImmutableModel):
    snapshot = models.ForeignKey(SprintClosureSnapshot, on_delete=models.PROTECT, related_name="rows")
    story = models.ForeignKey("knowledge.ContentRecord", on_delete=models.PROTECT, related_name="sprint_snapshots")
    story_revision = models.ForeignKey("knowledge.ContentRevision", on_delete=models.PROTECT, related_name="sprint_snapshot_rows")
    reference = models.CharField(max_length=40)
    title = models.CharField(max_length=200)
    work_state = models.CharField(max_length=20, choices=StoryProgress.choices)
    responsible = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    responsible_name = models.CharField(max_length=150, blank=True)
    epic = models.ForeignKey("knowledge.ContentRecord", on_delete=models.PROTECT, related_name="epic_snapshots")
    epic_reference = models.CharField(max_length=40)
    epic_title = models.CharField(max_length=200)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["snapshot", "story"], name="sprint_snapshot_story_unique")]


class SprintSnapshotApplication(ImmutableModel):
    row = models.ForeignKey(SprintSnapshotRow, on_delete=models.PROTECT, related_name="applications")
    application = models.ForeignKey("knowledge.ContentRecord", on_delete=models.PROTECT, related_name="sprint_application_snapshots")
    revision = models.ForeignKey("knowledge.ContentRevision", on_delete=models.PROTECT)
    reference = models.CharField(max_length=40)
    title = models.CharField(max_length=200)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["row", "application"], name="sprint_snapshot_application_unique")]
