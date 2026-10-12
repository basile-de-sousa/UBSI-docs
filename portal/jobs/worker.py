"""Leased, fenced at-least-once preview work; search.semantic handles indexing."""
from datetime import timedelta
import json
import os
import signal
import shutil
import subprocess
import sys
from uuid import uuid4

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from documents.models import Preview
from documents.policy import ADAPTER_VERSION, ERRORS
from documents.storage import digest, private_path
from .models import Job


@transaction.atomic
def claim():
    from knowledge.models import ProjectState
    ProjectState.objects.select_for_update().get(pk=1)
    now = timezone.now()
    job = Job.objects.select_for_update(skip_locked=True).filter(kind="preview").filter(Q(state="pending", next_run_at__lte=now) | Q(state="running", lease_until__lt=now)).order_by("next_run_at", "created_at").first()
    if not job: return None
    if job.attempts >= 3:
        job.state, job.error_code = "failed", "unavailable"
        job.save(update_fields=["state", "error_code"])
        Preview.objects.filter(file=job.file).exclude(state="ready").update(state="failed", error_code="unavailable", updated_at=now)
        return job
    job.state, job.lease_token = "running", uuid4()
    job.attempts += 1
    job.lease_until = now + timedelta(seconds=settings.DOCUMENT_JOB_SECONDS + 30)
    job.save(update_fields=["state", "lease_token", "attempts", "lease_until"])
    return job


@transaction.atomic
def finish(job, prefix, manifest, code="", transient=False, detail=""):
    current = Job.objects.select_for_update().get(pk=job.pk)
    if current.lease_token != job.lease_token or current.state != "running": return False
    preview = Preview.objects.select_for_update().get(file=job.file)
    if preview.state == Preview.State.READY:
        current.state = "done"
    elif not code:
        preview.state, preview.manifest, preview.asset_prefix, preview.error_code = "ready", manifest, prefix, ""
        preview.updated_at = timezone.now()
        preview.save()
        current.state = "done"
    elif transient and current.attempts < 3:
        current.state = "pending"
        current.next_run_at = timezone.now() + timedelta(seconds=15 * 2 ** (current.attempts - 1))
    else:
        preview.state, preview.error_code, preview.updated_at, preview.failure_detail = "failed", code, timezone.now(), detail[:500]
        preview.save(update_fields=["state", "error_code", "updated_at", "failure_detail"])
        current.state = "failed"
    current.error_code, current.lease_until, current.lease_token = code, None, None
    current.save()
    return not code and preview.asset_prefix == prefix


def execute(job):
    if job.state != "running": return
    file = job.file
    prefix = f"previews/{file.pk}/{job.lease_token}"
    output = private_path(prefix)
    output.mkdir(mode=0o700, parents=True)
    code, manifest, transient, process, detail = "", {}, False, None, ""
    try:
        source = private_path(file.storage_key)
        if file.adapter_version != ADAPTER_VERSION:
            code = "adapter"
        elif digest(source) != file.sha256:
            code = "integrity"
        else:
            config = {"source": str(source), "format": file.format, "output": str(output), "limits": file.options.get("limits", settings.DOCUMENT_LIMITS), "options": file.options, "vendor": str(settings.DOCUMENT_VENDOR_ROOT), "seconds": settings.DOCUMENT_JOB_SECONDS, "memory_mb": settings.DOCUMENT_JAVA_ADDRESS_SPACE_MB if file.format == "plantuml" else settings.DOCUMENT_CHILD_MEMORY_MB}
            # The child gets no database, SMTP or application secret environment.
            process = subprocess.Popen([sys.executable, "-m", "documents.runner"], cwd=settings.BASE_DIR, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True, env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(output)})
            stdout, _ = process.communicate(json.dumps(config).encode(), timeout=settings.DOCUMENT_JOB_SECONDS)
            if process.returncode:
                reported = stdout.decode(errors="replace").strip()
                if reported.startswith("{"):
                    report = json.loads(reported)
                    reported, detail = report["code"], report.get("detail", "")
                code = reported if reported in ERRORS else "limit" if process.returncode < 0 else "invalid"
                transient = code == "unavailable"
            else:
                manifest = json.loads((output / "manifest.json").read_text())
                manifest["assets"] = {path.name: {"sha256": digest(path), "size": path.stat().st_size, "mime": {".json": "application/json", ".png": "image/png", ".pdf": "application/pdf"}[path.suffix]} for path in output.iterdir() if path.name != "manifest.json" and path.suffix in {".json", ".png", ".pdf"}}
                if sum(entry["size"] for entry in manifest["assets"].values()) > file.options.get("limits", settings.DOCUMENT_LIMITS)["expanded_bytes"]:
                    code = "limit"
                if manifest.get("kind") not in {"drawio", "image", "pdf", "table"}: code = "invalid"
    except subprocess.TimeoutExpired:
        code = "timeout"
    except (OSError, ValueError):
        code, transient = "unavailable", True
    finally:
        if process is not None:
            # Terminate Java descendants too, even if the parser exited first.
            try: os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            process.wait()
    keep = finish(job, prefix, manifest, code, transient, detail)
    if not keep: shutil.rmtree(output, ignore_errors=True)
