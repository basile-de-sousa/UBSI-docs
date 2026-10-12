import uuid

from django.db import models
from django.utils import timezone


class Job(models.Model):
    """Transactional outbox with lease-fenced preview and semantic execution."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=30)
    file = models.ForeignKey("documents.FileRevision", null=True, on_delete=models.CASCADE, related_name="jobs")
    lease_token = models.UUIDField(null=True)
    error_code = models.CharField(max_length=40, blank=True)
    revision = models.ForeignKey("knowledge.ContentRevision", null=True, on_delete=models.PROTECT, related_name="jobs")
    idempotency_key = models.CharField(max_length=100, unique=True)
    state = models.CharField(max_length=20, default="pending", db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    lease_until = models.DateTimeField(null=True)
    next_run_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.CheckConstraint(condition=(models.Q(kind="preview", file__isnull=False, revision__isnull=True) | models.Q(kind="semantic_index", file__isnull=True, revision__isnull=False)), name="job_source_kind")]
