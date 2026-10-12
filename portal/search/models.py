from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.utils import timezone


class SearchPassage(models.Model):
    record = models.ForeignKey("knowledge.ContentRecord", on_delete=models.PROTECT, related_name="passages")
    revision = models.ForeignKey("knowledge.ContentRevision", on_delete=models.PROTECT, related_name="passages")
    ordinal = models.PositiveIntegerField()
    section = models.CharField(max_length=36, blank=True)
    title = models.CharField(max_length=200)
    excerpt = models.TextField()
    vector = SearchVectorField(null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["revision", "ordinal"], name="search_passage_ordinal_unique")]
        indexes = [GinIndex(fields=["vector"])]


class SemanticIndex(models.Model):
    revision = models.OneToOneField("knowledge.ContentRevision", primary_key=True, on_delete=models.CASCADE, related_name="semantic_index")
    version = models.CharField(max_length=100)
    source_digest = models.CharField(max_length=64)
    chunk_count = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=timezone.now)


class SemanticChunk(models.Model):
    passage = models.ForeignKey(SearchPassage, on_delete=models.CASCADE, related_name="chunks")
    ordinal = models.PositiveIntegerField()
    start = models.PositiveIntegerField()
    end = models.PositiveIntegerField()
    embedding = models.BinaryField(max_length=1536)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["passage", "ordinal"], name="search_chunk_ordinal_unique"),
            models.CheckConstraint(condition=models.Q(end__gt=models.F("start")), name="search_chunk_nonempty"),
        ]


class RetrievalSlot(models.Model):
    """A cross-process concurrency lease; contains no submitted question."""
    id = models.PositiveSmallIntegerField(primary_key=True)
    token = models.UUIDField(null=True)
    lease_until = models.DateTimeField(null=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(id__gte=1, id__lte=5), name="search_five_slots")]
