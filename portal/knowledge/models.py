import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Kind(models.TextChoices):
    APPLICATION = "application", "Application"
    EPIC = "epic", "Epic"
    STORY = "story", "User story"
    SPRINT = "sprint", "Sprint"
    SPECIFICATION = "specification", "Spécification"
    DOCUMENT = "document", "Document"
    FAQ = "faq", "FAQ"


class State(models.TextChoices):
    DRAFT = "draft_only", "Brouillon"
    PUBLISHED = "published", "Publié"
    ARCHIVED = "archived", "Archivé"


class Relation(models.TextChoices):
    APPLICATION = "application", "Applications"
    EPIC = "epic", "Epics"
    STORY = "story", "User stories"
    DOCUMENT = "document", "Documents"
    SPECIFICATION = "specification", "Spécifications"
    SUPPORT = "support", "Contenus associés"
    DEPENDENCY = "dependency", "Dépendances"
    SPRINT = "sprint", "Sprint"


class EpicProgress(models.TextChoices):
    PLANNED = "planned", "Planifié"
    IN_PROGRESS = "in_progress", "En cours"
    COMPLETED = "completed", "Terminé"
    CANCELLED = "cancelled", "Annulé"


class StoryProgress(models.TextChoices):
    BACKLOG = "backlog", "Backlog"
    READY = "ready", "Prête"
    IN_PROGRESS = "in_progress", "En cours"
    IN_REVIEW = "in_review", "En revue"
    DONE = "done", "Terminée"
    CANCELLED = "cancelled", "Annulée"


class SprintProgress(models.TextChoices):
    PLANNED = "planned", "Planifié"
    ACTIVE = "active", "Actif"
    CLOSED = "closed", "Clôturé"


class Priority(models.TextChoices):
    LOW = "low", "Basse"
    NORMAL = "normal", "Normale"
    HIGH = "high", "Haute"
    CRITICAL = "critical", "Critique"


class ProjectState(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    counters = models.JSONField(default=dict)
    search_generation = models.PositiveBigIntegerField(default=0)
    active_sprint = models.ForeignKey("ContentRecord", null=True, blank=True, on_delete=models.PROTECT, related_name="active_for")

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name="knowledge_project_singleton")]


class ContentRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    reference = models.CharField(max_length=40, unique=True)
    state = models.CharField(max_length=12, choices=State.choices, default=State.DRAFT)
    current_revision = models.ForeignKey("ContentRevision", null=True, blank=True, on_delete=models.PROTECT, related_name="current_for")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="content_created")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now, db_index=True)
    edit_version = models.PositiveBigIntegerField(default=1)
    revision_sequence = models.PositiveIntegerField(default=0)
    discarded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(kind__in=Kind.values), name="knowledge_valid_kind"),
            models.CheckConstraint(condition=(models.Q(state=State.DRAFT, current_revision__isnull=True) | models.Q(state__in=[State.PUBLISHED, State.ARCHIVED], current_revision__isnull=False)), name="knowledge_state_pointer"),
            models.CheckConstraint(condition=models.Q(discarded_at__isnull=True) | models.Q(state=State.DRAFT, current_revision__isnull=True), name="knowledge_discard_only_unpublished"),
        ]

    @property
    def display_reference(self):
        if self.kind == Kind.APPLICATION and self.current_revision_id:
            return self.current_revision.payload["code"]
        return self.reference

    @property
    def admin_title(self):
        if self.current_revision_id:
            return self.current_revision.title or self.reference
        try:
            return self.draft.title or self.reference
        except ContentDraft.DoesNotExist:
            return self.reference


class ContentDraft(models.Model):
    file_revision = models.ForeignKey("documents.FileRevision", null=True, blank=True, on_delete=models.PROTECT, related_name="drafts")
    record = models.OneToOneField(ContentRecord, primary_key=True, on_delete=models.PROTECT, related_name="draft")
    title = models.CharField(max_length=200, blank=True)
    payload = models.JSONField(default=dict)
    responsible = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="content_drafts")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="drafts_updated")
    updated_at = models.DateTimeField(default=timezone.now)


class ImmutableQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValueError("Published history is immutable.")

    def delete(self):
        raise ValueError("Published history is immutable.")


class ImmutableModel(models.Model):
    objects = ImmutableQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("Published history is immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Published history is immutable.")


class ContentRevision(ImmutableModel):
    file_revision = models.ForeignKey("documents.FileRevision", null=True, blank=True, on_delete=models.PROTECT, related_name="publications")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(ContentRecord, on_delete=models.PROTECT, related_name="revisions")
    number = models.PositiveIntegerField()
    source_version = models.PositiveBigIntegerField()
    title = models.CharField(max_length=200)
    payload = models.JSONField()
    body_html = models.TextField(blank=True)
    plain_text = models.TextField(blank=True)
    responsible = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="content_revisions")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="revisions_authored")
    published_at = models.DateTimeField(default=timezone.now)

    @property
    def progress_label(self):
        choices = {Kind.EPIC: EpicProgress, Kind.STORY: StoryProgress, Kind.SPRINT: SprintProgress}.get(self.record.kind)
        value = self.payload.get("sprint_state" if self.record.kind == Kind.SPRINT else "work_state")
        return dict(choices.choices).get(value, "") if choices else ""

    @property
    def priority_label(self):
        return dict(Priority.choices).get(self.payload.get("priority"), "")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["record", "number"], name="knowledge_revision_number_unique")]


class DraftRelation(models.Model):
    draft = models.ForeignKey(ContentDraft, on_delete=models.CASCADE, related_name="relations")
    target = models.ForeignKey(ContentRecord, on_delete=models.PROTECT, related_name="incoming_drafts")
    kind = models.CharField(max_length=20, choices=Relation.choices)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["draft", "target", "kind"], name="knowledge_draft_relation_unique")]


class RevisionRelation(ImmutableModel):
    revision = models.ForeignKey(ContentRevision, on_delete=models.PROTECT, related_name="relations")
    target = models.ForeignKey(ContentRecord, on_delete=models.PROTECT, related_name="incoming_revisions")
    kind = models.CharField(max_length=20, choices=Relation.choices)
    target_title = models.CharField(max_length=200)
    target_reference = models.CharField(max_length=40)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["revision", "target", "kind"], name="knowledge_revision_relation_unique")]


class ApplicationCode(models.Model):
    code = models.CharField(max_length=40, primary_key=True)
    record = models.ForeignKey(ContentRecord, on_delete=models.PROTECT, related_name="application_codes")


class ApplicationImport(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    source_digest = models.CharField(max_length=64)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    completed_at = models.DateTimeField(default=timezone.now)


class ImportedApplication(models.Model):
    receipt = models.ForeignKey(ApplicationImport, on_delete=models.PROTECT, related_name="rows")
    code = models.CharField(max_length=40, unique=True)
    record = models.ForeignKey(ContentRecord, on_delete=models.PROTECT)
    created = models.BooleanField()
