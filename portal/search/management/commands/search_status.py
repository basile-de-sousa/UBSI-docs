import json
from django.core.management.base import BaseCommand
from jobs.models import Job
from search.corpus import passages, records
from search.models import SemanticChunk, SemanticIndex
from search.policy import INDEX_VERSION, POLICY, fingerprint, qualification


class Command(BaseCommand):
    help = "Report search readiness and the qualification fingerprint, without source text."

    def handle(self, *args, **options):
        current = records().values("current_revision_id")
        self.stdout.write(json.dumps({"policy": POLICY["version"], "policy_sha256": fingerprint(), "qualified": qualification(), "records": records().count(), "passages": passages().count(), "chunks": SemanticChunk.objects.filter(passage__in=passages()).count(), "indexes": SemanticIndex.objects.filter(revision_id__in=current, version=INDEX_VERSION).count(), "pending": Job.objects.filter(kind="semantic_index", revision_id__in=current, state__in=["pending", "running"]).count(), "failed": Job.objects.filter(kind="semantic_index", revision_id__in=current, state="failed").count()}, indent=2))
