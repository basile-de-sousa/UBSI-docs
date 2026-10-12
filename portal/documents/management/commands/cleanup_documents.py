from datetime import timedelta
import shutil
from uuid import UUID

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from documents.models import FileRevision
from documents.storage import private_path
from knowledge.models import ProjectState


class Command(BaseCommand):
    help = "List or remove abandoned private objects after a minimum 24-hour grace; never remove a retained file."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--grace-hours", type=int, default=24)

    def handle(self, *args, **options):
        if options["grace_hours"] < 24:
            raise ValueError("Grace must be at least 24 hours")
        cutoff = timezone.now() - timedelta(hours=options["grace_hours"])
        count = 0
        with transaction.atomic():
            ProjectState.objects.select_for_update().get(pk=1)
            files = FileRevision.objects.filter(created_at__lt=cutoff, drafts__isnull=True, publications__isnull=True).exclude(jobs__state="running").distinct()
            for file in list(files):
                count += 1
                if options["apply"]:
                    # ORM PROTECT checks and database foreign keys also protect history.
                    FileRevision.objects.filter(pk=file.pk, drafts__isnull=True, publications__isnull=True).delete()
                    shutil.rmtree(private_path(f"originals/{file.pk}"), ignore_errors=True)
                    shutil.rmtree(private_path(f"previews/{file.pk}"), ignore_errors=True)
            # Orphan staging from interrupted upload/metadata transactions.
            for folder in ["originals", "previews"]:
                root = private_path(folder)
                if not root.exists(): continue
                for candidate in root.iterdir():
                    try: file_id = UUID(candidate.name)
                    except ValueError: continue
                    if not candidate.is_dir() or candidate.is_symlink(): continue
                    if candidate.stat().st_mtime >= cutoff.timestamp(): continue
                    if not FileRevision.objects.filter(pk=file_id).exists():
                        count += 1
                        if options["apply"]: shutil.rmtree(candidate)
                    elif folder == "previews" and not FileRevision.objects.filter(pk=file_id, jobs__state="running").exists():
                        current = FileRevision.objects.get(pk=file_id).preview.asset_prefix
                        for attempt in candidate.iterdir():
                            if not attempt.is_dir() or attempt.is_symlink() or attempt.stat().st_mtime >= cutoff.timestamp():
                                continue
                            if current and attempt.resolve() == private_path(current):
                                continue
                            count += 1
                            if options["apply"]: shutil.rmtree(attempt)
        self.stdout.write(f"{'Removed' if options['apply'] else 'Candidates'}: {count}")
