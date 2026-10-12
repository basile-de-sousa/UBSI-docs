from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4
from datetime import timedelta
import os
import subprocess
import sys
from urllib.parse import quote

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections, connections
from django.test import TransactionTestCase
from django.utils import timezone
from django.db import connection

from accounts.models import User
from accounts.services import AccountError, update_access
from jobs.worker import claim
from jobs.models import Job
from documents.services import upload
from knowledge import services
from knowledge.models import ContentDraft, Kind, Relation
from search.retrieval import acquire_slot
from search.models import RetrievalSlot
from search.policy import Busy
from sprints.services import activate

from .helpers import Fixtures


class ConcurrentAcceptance(Fixtures, TransactionTestCase):
    def race(self, *actions):
        barrier = Barrier(len(actions))
        def invoke(action):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return action()
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=len(actions)) as pool:
            return list(pool.map(invoke, actions))

    def test_two_sprint_activations_allow_only_one(self):
        a, b = self.sprint(), self.sprint()
        def start(sprint):
            try: activate(self.admin.pk, sprint.pk, sprint.edit_version); return "active"
            except ValidationError: return "refused"
        self.assertCountEqual(self.race(lambda: start(a), lambda: start(b)), ["active", "refused"])

    def test_two_saves_have_one_conflict(self):
        faq = self.faq()
        faq = services.begin_edit(self.admin.pk, faq.pk, faq.edit_version)
        def save(label):
            try: services.save_draft(self.admin.pk, faq.pk, faq.edit_version, label, {"answer": label}, {}); return "saved"
            except services.Conflict: return "conflict"
        self.assertCountEqual(self.race(lambda: save("First"), lambda: save("Second")), ["saved", "conflict"])
        self.assertIn(ContentDraft.objects.get(record=faq).title, ["First", "Second"])

    def test_two_admin_demotions_preserve_one_admin(self):
        other = User.objects.create_user("other@example.invalid", display_name="Other fictional admin", role="admin")
        def demote(target):
            try: update_access(target.pk, target.pk, "user", True, target.management_version); return "demoted"
            except AccountError: return "refused"
        self.assertCountEqual(self.race(lambda: demote(self.admin), lambda: demote(other)), ["demoted", "refused"])
        self.assertEqual(User.objects.filter(role="admin", is_active=True).count(), 1)

    def test_parallel_worker_claims_do_not_duplicate_job(self):
        app = self.application()
        doc = self.draft(Kind.DOCUMENT, {"category": "spreadsheet", "description": "Table"}, {Relation.APPLICATION: [app.pk]})
        file = upload(self.admin.pk, doc.pk, doc.edit_version, SimpleUploadedFile("table.csv", b"a;b\n1;2\n"))
        job = Job.objects.get(file=file, kind="preview")
        rows = self.race(claim, claim)
        self.assertEqual(sum(row is not None for row in rows), 1)
        self.assertEqual(next(row.pk for row in rows if row), job.pk)

    def test_six_simultaneous_slot_claims_are_bounded_at_five(self):
        for i in range(1, 6): RetrievalSlot.objects.get_or_create(pk=i)
        def reserve():
            try: return acquire_slot()[0]
            except Busy: return None
        rows = self.race(*[reserve for _ in range(6)])
        self.assertEqual(len(set(row for row in rows if row)), 5)
        self.assertEqual(rows.count(None), 1)

    def test_crashed_worker_claim_is_reclaimed_and_completed(self):
        app = self.application()
        doc = self.draft(Kind.DOCUMENT, {"category": "spreadsheet", "description": "Table"}, {Relation.APPLICATION: [app.pk]})
        file = upload(self.admin.pk, doc.pk, doc.edit_version, SimpleUploadedFile("table.csv", b"a;b\n1;2\n"))
        database = connection.settings_dict
        env = os.environ.copy()
        env["DATABASE_URL"] = "postgresql://{}:{}@{}:{}/{}".format(quote(database["USER"], safe=""), quote(database["PASSWORD"], safe=""), database["HOST"], database["PORT"], quote(database["NAME"], safe=""))
        code = "import django,os; django.setup(); from jobs.worker import claim; claim(); os._exit(77)"
        result = subprocess.run([sys.executable, "-c", code], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
        self.assertEqual(result.returncode, 77)
        job = Job.objects.get(file=file)
        self.assertEqual(job.state, "running")
        # Advance only this synthetic lease instead of waiting its full duration.
        Job.objects.filter(pk=job.pk).update(lease_until=timezone.now()-timedelta(seconds=1))
        fresh = claim()
        self.assertEqual(fresh.attempts, 2)
        from jobs.worker import execute
        execute(fresh)
        fresh.refresh_from_db()
        self.assertEqual(fresh.state, "done")
