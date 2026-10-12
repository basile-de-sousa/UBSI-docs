"""Private staging before a serialized metadata transaction; ready files publish separately."""
import hashlib
import json
from pathlib import Path
import re
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from jobs.models import Job
from knowledge.models import Kind
from knowledge.services import advance, check_version, lock_project, locked_record
from .models import FileRevision, Preview
from .policy import ADAPTER_VERSION, FORMATS, validate_category
from .storage import PrivateStorage


def upload(actor_id, record_id, expected_version, source, delimiter="auto"):
    filename = Path(source.name.replace("\\", "/")).name
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)[:255]
    extension = filename.rsplit(".", 1)[-1].lower()
    if extension not in FORMATS:
        raise ValidationError("Extension non prise en charge. Consultez les formats autorisés.")
    format, mime = FORMATS[extension]
    if delimiter not in {"auto", ",", ";", "\t"}:
        raise ValidationError("Séparateur invalide.")
    storage, file_id, hasher, size = PrivateStorage(), uuid4(), hashlib.sha256(), 0
    # A random staging key is never derived from user filenames.
    key = f"originals/{file_id}/source"
    try:
        def chunks():
            nonlocal size
            for chunk in source.chunks():
                size += len(chunk)
                if size > settings.DOCUMENT_LIMITS["source_bytes"]:
                    raise ValidationError("Le fichier dépasse la taille autorisée. Réduisez-le puis réimportez-le.")
                hasher.update(chunk)
                yield chunk
        class Stream:
            def chunks(self): return chunks()
        key = storage.save(key, Stream())
        if not size:
            raise ValidationError("Le fichier est vide.")
        with transaction.atomic():
            actor, _ = lock_project(actor_id)
            record = locked_record(record_id)
            check_version(record, expected_version)
            if record.kind != Kind.DOCUMENT or not hasattr(record, "draft"):
                raise ValidationError("Créez un brouillon de document avant d’importer un fichier.")
            category = record.draft.payload["category"]
            validate_category(category, format)
            file = FileRevision.objects.create(id=file_id, record=record, storage_key=key, sha256=hasher.hexdigest(), size=size, filename=filename, format=format, mime=mime, category=category, options={"limits": dict(settings.DOCUMENT_LIMITS), **({"delimiter": delimiter} if format == "csv" else {})}, adapter_version=ADAPTER_VERSION, uploaded_by=actor)
            Preview.objects.create(file=file)
            fingerprint = hashlib.sha256(json.dumps({"digest": file.sha256, "format": format, "adapter": ADAPTER_VERSION, "options": file.options}, sort_keys=True).encode()).hexdigest()[:16]
            Job.objects.create(kind="preview", file=file, idempotency_key=f"preview:{file.pk}:{fingerprint}")
            record.draft.file_revision = file
            record.draft.save(update_fields=["file_revision"])
            advance(record)
        return file
    except Exception:
        storage.delete(key)
        raise


def validate_file(record, draft):
    file = draft.file_revision
    if not file or file.record_id != record.pk:
        raise ValidationError("Importez un fichier original avant publication.")
    if file.category != draft.payload["category"]:
        raise ValidationError("La catégorie a changé depuis l’import. Réimportez le fichier dans cette catégorie.")
    validate_category(file.category, file.format)
    if file.preview.state != Preview.State.READY:
        raise ValidationError("L’aperçu doit être prêt avant publication. Consultez l’état du fichier et corrigez l’import si nécessaire.")


@transaction.atomic
def retry(actor_id, record_id, expected_version):
    lock_project(actor_id)
    record = locked_record(record_id)
    check_version(record, expected_version)
    if record.kind != Kind.DOCUMENT or not hasattr(record, "draft") or not record.draft.file_revision_id:
        raise ValidationError("Aucun fichier de brouillon à reprendre.")
    Job.objects.select_for_update().get(file_id=record.draft.file_revision_id, kind="preview")
    preview = Preview.objects.select_for_update().get(file_id=record.draft.file_revision_id)
    if preview.state != Preview.State.FAILED:
        raise ValidationError("Seule une préparation échouée peut être relancée.")
    Job.objects.filter(file=preview.file, kind="preview").update(state="pending", attempts=0, lease_until=None, lease_token=None, next_run_at=timezone.now(), error_code="")
    preview.state, preview.error_code, preview.failure_detail = Preview.State.PROCESSING, "", ""
    preview.save(update_fields=["state", "error_code", "failure_detail"])
    advance(record)
