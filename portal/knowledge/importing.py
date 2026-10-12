"""One-time directory import: explicit dry run, no overwrite or automatic publish."""
import csv
import hashlib
import io
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import ApplicationCode, ApplicationImport, ImportedApplication, Kind
from .schema import application_code, normalise
from .services import create_draft, lock_project


def parse_csv(source):
    if not source or len(source) > 65536:
        raise ValidationError("Le CSV doit contenir entre 1 octet et 64 Kio.")
    try:
        text = source.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if reader.fieldnames != ["code", "nom", "type", "description"]:
            raise ValueError
        rows, codes = [], set()
        for row in reader:
            if None in row or any(value is None for value in row.values()) or len(rows) >= 100:
                raise ValueError
            code = application_code(row["code"])
            if code in codes:
                raise ValidationError(f"Le code {code} apparaît plusieurs fois.")
            codes.add(code)
            title, payload, _, _, _ = normalise(Kind.APPLICATION, row["nom"], {"code": code, "type": row["type"], "description": row["description"]}, publishing=True)
            rows.append({"title": title, "payload": payload})
        if not rows:
            raise ValueError
        return rows, hashlib.sha256(source).hexdigest()
    except (UnicodeError, csv.Error, ValueError):
        raise ValidationError("Utilisez le CSV UTF-8 à virgules avec les colonnes code,nom,type,description et des lignes complètes (100 maximum).") from None


def preview_rows(rows):
    existing = set(ApplicationCode.objects.filter(code__in=[row["payload"]["code"] for row in rows]).values_list("code", flat=True))
    return [{**row, "existing": row["payload"]["code"] in existing} for row in rows]


@transaction.atomic
def import_applications(actor_id, rows, digest):
    actor, _ = lock_project(actor_id)
    receipt = ApplicationImport.objects.filter(pk=1).first()
    if receipt:
        return receipt, False
    if not rows or len(rows) > 100 or len(digest) != 64:
        raise ValidationError("Le rapport d’import est invalide.")
    receipt = ApplicationImport.objects.create(pk=1, source_digest=digest, completed_by=actor)
    for row in rows:
        title, payload, _, _, _ = normalise(Kind.APPLICATION, row["title"], row["payload"], publishing=True)
        reservation = ApplicationCode.objects.select_related("record").filter(code=payload["code"]).first()
        record = reservation.record if reservation else create_draft(actor.pk, uuid4(), Kind.APPLICATION, title, payload, {})
        ImportedApplication.objects.create(receipt=receipt, code=payload["code"], record=record, created=not bool(reservation))
    return receipt, True
