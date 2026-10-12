"""Read-only consistency evidence without account details or content text."""
import json
import hashlib
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.db.migrations.recorder import MigrationRecorder
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from django.db.models import F
from django.utils import timezone

from accounts.models import User
from documents.models import FileRevision, Preview
from documents.storage import digest, private_path
from jobs.models import Job
from knowledge.models import ContentRecord, ContentRevision, RevisionRelation, State
from search.corpus import passages
from search.models import SearchPassage
from search.policy import qualification


class Command(BaseCommand):
    help = "Audit retained originals/previews and current publication pointers without changes."

    def handle(self, *args, **options):
        errors, inventory = [], []
        for file in FileRevision.objects.select_related("preview").order_by("id"):
            entry = {"id": str(file.pk), "sha256": file.sha256, "size": file.size, "assets": {}}
            try:
                source = private_path(file.storage_key)
                if not source.is_file() or source.stat().st_size != file.size or digest(source) != file.sha256:
                    raise ValueError
            except (OSError, ValueError): errors.append({"code": "original_integrity", "file": str(file.pk)})
            preview = file.preview
            if preview.state == Preview.State.READY:
                for name, asset in sorted(preview.manifest.get("assets", {}).items()):
                    try:
                        if Path(name).name != name or name in {".", ".."}: raise ValueError
                        target = private_path(preview.asset_prefix) / name
                        if not target.resolve().is_relative_to(private_path(preview.asset_prefix)) or not target.is_file() or target.stat().st_size != asset["size"] or digest(target) != asset["sha256"]: raise ValueError
                        entry["assets"][name] = {"sha256": asset["sha256"], "size": asset["size"]}
                    except (OSError, ValueError, KeyError): errors.append({"code": "preview_integrity", "file": str(file.pk)})
            inventory.append(entry)
        executor = MigrationExecutor(connection)
        if executor.migration_plan(executor.loader.graph.leaf_nodes()): errors.append({"code": "migrations_pending"})
        if ContentRecord.objects.filter(current_revision__isnull=False).exclude(current_revision__record_id=F("id")).exists(): errors.append({"code": "revision_pointer"})
        if SearchPassage.objects.exclude(pk__in=passages().values("pk")).exists(): errors.append({"code": "ineligible_passage"})
        current = RevisionRelation.objects.filter(revision__record__state=State.PUBLISHED, revision_id=F("revision__record__current_revision_id"))
        if current.filter(kind__in=["application", "epic"], revision__record__kind__in=["epic", "story", "specification", "document"]).exclude(target__state=State.PUBLISHED).exists(): errors.append({"code": "required_parent_unpublished"})
        pending = Job.objects.filter(state="pending").order_by("created_at").first()
        database_fingerprint = {}
        models = [*apps.get_models(include_auto_created=True), MigrationRecorder.Migration]
        for model in sorted(models, key=lambda model: model._meta.db_table):
            table = model._meta.db_table
            hasher, count = hashlib.sha256(), 0
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT to_jsonb(t)::text FROM {connection.ops.quote_name(table)} t ORDER BY {connection.ops.quote_name(model._meta.pk.column)}")
                while rows := cursor.fetchmany(1000):
                    for (value,) in rows:
                        hasher.update(value.encode()+b"\n")
                        count += 1
            database_fingerprint[table] = {"rows": count, "sha256": hasher.hexdigest()}
        report = {"ok": not errors, "migrations": len(executor.loader.applied_migrations), "counts": {"accounts": User.objects.count(), "records": ContentRecord.objects.count(), "revisions": ContentRevision.objects.count(), "files": len(inventory), "passages": passages().count()}, "jobs": {"pending": Job.objects.filter(state="pending").count(), "running": Job.objects.filter(state="running").count(), "expired_leases": Job.objects.filter(state="running", lease_until__lt=timezone.now()).count(), "failed": Job.objects.filter(state="failed").count(), "oldest_pending_seconds": int((timezone.now()-pending.created_at).total_seconds()) if pending else None}, "chatbot_qualified": qualification(), "inventory": inventory, "errors": errors}
        report["database_fingerprint"] = database_fingerprint
        self.stdout.write(json.dumps(report, indent=2))
        if errors: raise CommandError("Portal consistency audit failed; consult safe error codes.")
