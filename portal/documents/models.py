import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from knowledge.models import ImmutableModel


class Category(models.TextChoices):
    FLOW = "flow", "Flux de données"
    SPREADSHEET = "spreadsheet", "Tableau Excel / CSV"
    DATABASE = "database", "Diagramme de base de données"


class FileRevision(ImmutableModel):
    """Immutable uploaded bytes and preparation inputs, independent of publication."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey("knowledge.ContentRecord", on_delete=models.PROTECT, related_name="files")
    storage_key = models.CharField(max_length=200, unique=True)
    sha256 = models.CharField(max_length=64)
    filename = models.CharField(max_length=255)
    format = models.CharField(max_length=20)
    mime = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    category = models.CharField(max_length=20, choices=Category.choices)
    options = models.JSONField(default=dict)
    adapter_version = models.CharField(max_length=30)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)


class Preview(models.Model):
    class State(models.TextChoices):
        PROCESSING = "processing", "Préparation en cours"
        READY = "ready", "Aperçu prêt"
        FAILED = "failed", "Préparation échouée"
    file = models.OneToOneField(FileRevision, primary_key=True, on_delete=models.CASCADE, related_name="preview")
    state = models.CharField(max_length=12, choices=State.choices, default=State.PROCESSING)
    manifest = models.JSONField(default=dict)
    asset_prefix = models.CharField(max_length=200, blank=True)
    failure_detail = models.CharField(max_length=500, blank=True)
    error_code = models.CharField(max_length=40, blank=True)
    updated_at = models.DateTimeField(default=timezone.now)
