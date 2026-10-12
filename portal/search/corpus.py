"""The same current-only boundary for readers, ranking and final delivery."""
import hashlib
import json

from django.db.models import F
from knowledge.models import Kind, State
from knowledge.projections import published_records
from knowledge.schema import normalise
from .models import SearchPassage
from .policy import Unavailable

KINDS = (Kind.FAQ, Kind.EPIC, Kind.STORY, Kind.SPECIFICATION)


def passages():
    return SearchPassage.objects.filter(record__state=State.PUBLISHED, record__discarded_at__isnull=True, record__kind__in=KINDS, revision_id=F("record__current_revision_id"))


def records():
    return published_records().filter(kind__in=KINDS)


def source_digest(rows):
    return hashlib.sha256(json.dumps([(row.pk, str(row.revision_id), row.section, row.title, row.excerpt) for row in rows], ensure_ascii=False).encode()).hexdigest()


def validate_passage(passage):
    revision = passage.revision
    sections = normalise(passage.record.kind, revision.title, revision.payload, publishing=True)[4]
    if not any(section["id"] == passage.section and section["title"] == passage.title and section["text"] == passage.excerpt for section in sections):
        raise Unavailable
