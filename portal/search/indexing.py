from django.contrib.postgres.search import SearchVector
from django.db.models import TextField, Value

from jobs.models import Job
from knowledge.models import Kind
from .models import SearchPassage
from .policy import INDEX_VERSION


def replace_passages(record, revision, sections):
    # Called inside the publication transaction; no asynchronous gap for lexical data.
    SearchPassage.objects.filter(record=record).delete()
    Job.objects.filter(revision__record=record, state="pending").update(state="superseded")
    if record.kind not in {Kind.FAQ, Kind.SPECIFICATION, Kind.EPIC, Kind.STORY}:
        return
    aliases = "\n".join(revision.payload.get("aliases", []))
    for ordinal, section in enumerate(sections):
        passage = SearchPassage.objects.create(record=record, revision=revision, ordinal=ordinal, section=section["id"], title=section["title"], excerpt=section["text"])
        SearchPassage.objects.filter(pk=passage.pk).update(vector=SearchVector(Value(revision.title, output_field=TextField()), weight="A", config="french") + SearchVector(Value(section["text"], output_field=TextField()), weight="B", config="french") + SearchVector(Value(aliases, output_field=TextField()), weight="C", config="french"))
    Job.objects.create(kind="semantic_index", revision=revision, idempotency_key=f"semantic:{revision.pk}:{INDEX_VERSION}")


def withdraw(record):
    SearchPassage.objects.filter(record=record).delete()
    Job.objects.filter(revision__record=record, state="pending").update(state="superseded")


def queue_reindex(actor):
    from django.db import transaction
    from django.utils import timezone
    from accounts.models import AccountControl, User
    from knowledge.models import ProjectState
    from .corpus import records
    with transaction.atomic():
        AccountControl.objects.select_for_update().get(pk=1)
        if not User.objects.filter(pk=actor.pk, is_active=True, role=User.Role.ADMIN, access_version=actor.access_version).exists():
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        ProjectState.objects.select_for_update().get(pk=1)
        for record in records():
            key = f"semantic:{record.current_revision_id}:{INDEX_VERSION}"
            job, created = Job.objects.get_or_create(idempotency_key=key, defaults={"kind": "semantic_index", "revision_id": record.current_revision_id})
            if not created and job.state not in {"running", "pending"}:
                job.state, job.attempts, job.error_code = "pending", 0, ""
                job.next_run_at, job.lease_until, job.lease_token = timezone.now(), None, None
                job.save()
