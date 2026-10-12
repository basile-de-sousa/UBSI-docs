"""Lease-fenced indexing; publication never waits for model inference."""
from datetime import timedelta
import json
import os
import signal
import subprocess
import sys
from uuid import uuid4

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from jobs.models import Job
from knowledge.models import ProjectState
from .corpus import passages, source_digest, validate_passage
from .models import SemanticChunk, SemanticIndex
from .policy import INDEX_VERSION


@transaction.atomic
def claim():
    ProjectState.objects.select_for_update().get(pk=1)
    now = timezone.now()
    job = Job.objects.select_for_update(skip_locked=True).filter(kind="semantic_index").filter(Q(state="pending", next_run_at__lte=now) | Q(state="running", lease_until__lt=now)).order_by("next_run_at", "created_at").first()
    if not job: return None
    if job.attempts >= 3:
        job.state, job.error_code = "failed", "index_unavailable"
    else:
        job.state, job.lease_token = "running", uuid4()
        job.attempts += 1
        job.lease_until = now + timedelta(seconds=settings.SEARCH_JOB_SECONDS + 30)
    job.save()
    return job


def execute(job):
    if job.state != "running": return
    rows = list(passages().filter(revision_id=job.revision_id).select_related("record", "revision").order_by("ordinal"))
    digest = source_digest(rows)
    result, process, failed = [], None, False
    try:
        for row in rows: validate_passage(row)
        if rows:
            safe_env = {key: value for key, value in os.environ.items() if key in {"PATH", "LANG", "SYSTEMROOT"}}
            # The child needs model settings only. No production DB/email/app secrets.
            safe_env.update(PORTAL_ENV="development", DEBUG="false", SECRET_KEY="unused-offline-index-child-secret-key-0000000000000000", ALLOWED_HOSTS="localhost,127.0.0.1", DATABASE_URL="postgresql://unused:unused@localhost/unused", PRIVATE_STORAGE_ROOT="/tmp/ubsi-unused-index-private", SEARCH_MODEL_ROOT=str(settings.SEARCH_MODEL_ROOT), SEARCH_CPU_THREADS=str(settings.SEARCH_CPU_THREADS), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1", PYTHONDONTWRITEBYTECODE="1")
            process = subprocess.Popen([sys.executable, "-m", "search.semantic_runner"], cwd=settings.BASE_DIR, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True, env=safe_env)
            config = {"passages": [{"id": row.pk, "title": row.revision.title + "\n" + row.title, "text": row.excerpt} for row in rows], "max_chunks": settings.SEARCH_MAX_CHUNKS}
            stdout, _ = process.communicate(json.dumps(config).encode(), timeout=settings.SEARCH_JOB_SECONDS)
            if process.returncode or len(stdout) > 40 * 1024**2: raise ValueError
            result = json.loads(stdout)
            if len(result) > settings.SEARCH_MAX_CHUNKS: raise ValueError
            for item in result:
                if len(bytes.fromhex(item["embedding"])) != 1536: raise ValueError
    except Exception:
        failed = True
    finally:
        if process:
            try: os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            process.wait()
    with transaction.atomic():
        ProjectState.objects.select_for_update().get(pk=1)
        current = Job.objects.select_for_update().get(pk=job.pk)
        if current.state != "running" or current.lease_token != job.lease_token: return
        fresh = list(passages().filter(revision_id=job.revision_id).order_by("ordinal"))
        if not fresh or source_digest(fresh) != digest:
            current.state, current.error_code = "superseded", ""
        elif failed:
            current.state = "pending" if current.attempts < 3 else "failed"
            current.error_code = "index_unavailable"
            current.next_run_at = timezone.now() + timedelta(seconds=15 * 2**(current.attempts-1))
        else:
            SemanticChunk.objects.filter(passage__revision_id=job.revision_id).delete()
            SemanticChunk.objects.bulk_create([SemanticChunk(passage_id=item["passage"], ordinal=item["ordinal"], start=item["start"], end=item["end"], embedding=bytes.fromhex(item["embedding"])) for item in result])
            SemanticIndex.objects.update_or_create(revision_id=job.revision_id, defaults={"version": INDEX_VERSION, "source_digest": digest, "chunk_count": len(result)})
            current.state, current.error_code = "done", ""
        current.lease_until, current.lease_token = None, None
        current.save()
