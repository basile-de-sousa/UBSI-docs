from datetime import timedelta
import io
import json
from pathlib import Path
from unittest.mock import patch

from django.core import mail, signing
from django.core.management import call_command
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, connection, transaction
from django.test import TestCase, override_settings
from django.conf import settings
from django.utils import timezone

from accounts import services as accounts
from accounts.models import Invitation, User
from accounts.tokens import invitation_digest, reset_tokens
from documents import services as documents
from documents.models import FileRevision, Preview
from jobs import worker
from jobs.models import Job
from knowledge import services
from knowledge.editor import safe_href, validate_document
from knowledge.models import ContentDraft, ContentRevision, Kind, Relation
from search import retrieval
from search.corpus import passages
from search.models import RetrievalSlot
from search.policy import Busy, Unavailable, qualification
from sprints import services as sprints
from sprints.models import SprintSnapshotRow

from .helpers import Fixtures


class IntegratedAcceptance(Fixtures, TestCase):
    def test_ac01_anonymous_pages_and_files(self):
        faq = self.faq()
        self.assertEqual(self.client.get("/").status_code, 200)  # Public login form only.
        for url in ["/search/", "/faq/", f"/faq/{faq.pk}/", f"/documents/{faq.pk}/download/", f"/documents/{faq.pk}/preview/"]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response["Location"], "/auth/login/")
                self.assertNotIn(b"Published fictional answer", response.content)
        self.assertEqual(self.client.post("/assistant/query/", {"question": "Why?"}).status_code, 401)

    def test_ac02_reader_writes_are_rejected_without_changes(self):
        faq = self.faq()
        client = self.client_for(self.reader)
        before = ContentRevision.objects.count()
        for action in ["publish", "begin", "archive", "discard", "restore/1"]:
            with self.subTest(action=action):
                self.assertEqual(client.post(f"/admin/knowledge/{faq.pk}/{action}/", {"expected_version": faq.edit_version}).status_code, 403)
        self.assertEqual(before, ContentRevision.objects.count())
        self.assertFalse(ContentDraft.objects.filter(record=faq).exists())
        with self.assertRaises(PermissionDenied): services.begin_edit(self.reader.pk, faq.pk, faq.edit_version)

    def test_ac03_cross_application_epic(self):
        a, b = self.application(), self.application("APP-M8")
        epic = self.epic([a, b])
        client = self.client_for(self.reader)
        for app in [a, b]:
            self.assertContains(client.get(f"/applications/{app.pk}/"), str(epic.pk))

    def test_ac04_story_parent_and_application_subset(self):
        a, b = self.application(), self.application("APP-M8")
        epic = self.epic([a])
        story = self.story(epic, a)
        self.assertEqual(story.current_revision.relations.get(kind=Relation.EPIC).target_id, epic.pk)
        invalid = self.draft(Kind.STORY, story.current_revision.payload, {Relation.EPIC: [epic.pk], Relation.APPLICATION: [b.pk]})
        with self.assertRaises(ValidationError): self.publish(invalid)
        self.assertTrue(ContentDraft.objects.filter(record=invalid).exists())

    def test_ac05_draft_does_not_replace_reader_or_passages(self):
        faq = self.faq()
        self.edit(faq, {"answer": "PRIVATE DRAFT SENTINEL", "aliases": []})
        client = self.client_for(self.reader)
        self.assertContains(client.get(f"/faq/{faq.pk}/"), "Published fictional answer")
        self.assertNotContains(client.get("/search/?q=SENTINEL"), "PRIVATE DRAFT")
        self.assertEqual(passages().get(record=faq).excerpt, "Published fictional answer")

    def test_ac06_invalid_publication_preserves_draft(self):
        draft = self.draft(Kind.FAQ, {"answer": ""})
        with self.assertRaises(ValidationError): self.publish(draft)
        self.assertTrue(ContentDraft.objects.filter(record=draft).exists())
        self.assertFalse(draft.revisions.exists())

    def test_ac12_archive_withdraws_search_and_source_link(self):
        faq = self.faq()
        token = signing.dumps({"record": str(faq.pk), "revision": str(faq.current_revision_id), "section": ""}, salt="search.source", compress=True)
        client = self.client_for(self.reader)
        self.assertEqual(client.get(f"/assistant/source/{token}/").status_code, 302)
        services.archive(self.admin.pk, faq.pk, faq.edit_version)
        self.assertFalse(passages().filter(record=faq).exists())
        self.assertEqual(client.get(f"/assistant/source/{token}/").status_code, 404)
        self.assertNotContains(client.get("/search/?q=fictional"), "Published fictional answer")

    def test_ac13_invitation_is_single_use(self):
        invitation = accounts.invite(self.admin.pk, "invited@example.invalid", "user")
        self.assertEqual(len(mail.outbox), 1)
        user = accounts.accept_invitation(invitation.pk, invitation.token_digest, "Fictional invitee", "Fictional-safe-passphrase-724!")
        self.assertEqual(user.role, "user")
        with self.assertRaises(accounts.AccountError): accounts.accept_invitation(invitation.pk, invitation.token_digest, "Duplicate", "Fictional-safe-passphrase-724!")
        self.assertEqual(User.objects.filter(email=invitation.email).count(), 1)

    def test_expired_and_replaced_invitations(self):
        old = accounts.invite(self.admin.pk, "invited@example.invalid", "user")
        renewed = accounts.invite(self.admin.pk, "invited@example.invalid", "user")
        with self.assertRaises(accounts.AccountError): accounts.accept_invitation(old.pk, old.token_digest, "Old", "Fictional-safe-passphrase-724!")
        Invitation.objects.filter(pk=renewed.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        with self.assertRaises(accounts.AccountError): accounts.accept_invitation(renewed.pk, renewed.token_digest, "Expired", "Fictional-safe-passphrase-724!")

    def test_mail_failure_rolls_back_invitation(self):
        with patch("accounts.services.deliver", side_effect=accounts.MailUnavailable):
            with self.assertRaises(accounts.MailUnavailable): accounts.invite(self.admin.pk, "failed@example.invalid", "user")
        self.assertFalse(Invitation.objects.filter(email="failed@example.invalid").exists())

    def test_ac14_deactivation_revokes_session_and_preserves_authorship(self):
        client = self.client_for(self.reader)
        self.assertEqual(client.get("/search/").status_code, 200)
        accounts.update_access(self.admin.pk, self.reader.pk, "user", False, self.reader.management_version)
        self.assertEqual(client.get("/search/").status_code, 302)
        self.assertTrue(User.objects.filter(pk=self.reader.pk).exists())

    def test_last_admin_cannot_be_removed(self):
        with self.assertRaises(accounts.AccountError): accounts.update_access(self.admin.pk, self.admin.pk, "user", False, self.admin.management_version)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertEqual(self.admin.role, "admin")

    def test_deactivated_author_is_retained_in_history(self):
        author = User.objects.create_user("author@example.invalid", display_name="Fictional author", role="admin")
        from uuid import uuid4
        record = services.create_draft(author.pk, uuid4(), Kind.FAQ, "Historical question", {"answer": "Historical answer"}, {})
        record = services.publish(author.pk, record.pk, record.edit_version)
        accounts.update_access(self.admin.pk, author.pk, "admin", False, author.management_version)
        record.current_revision.refresh_from_db()
        self.assertEqual(record.current_revision.author_id, author.pk)

    def test_password_reset_is_single_use(self):
        self.reader.set_password("Old-fictional-password-812!")
        self.reader.save()
        token = reset_tokens.make_token(self.reader)
        accounts.reset_password(self.reader.pk, token, "New-fictional-password-927!")
        with self.assertRaises(accounts.AccountError): accounts.reset_password(self.reader.pk, token, "Another-fictional-password-928!")

    def test_ac15_ac18_sprint_closure_and_history(self):
        app = self.application()
        epic = self.epic([app])
        sprint, target = self.sprint(), self.sprint()
        story = self.story(epic, app, sprint)
        sprint = sprints.activate(self.admin.pk, sprint.pk, sprint.edit_version)
        report = sprints.close_report(sprint)
        sprints.close(self.admin.pk, report, {str(story.pk): str(target.pk)})
        row = SprintSnapshotRow.objects.get(story=story)
        self.assertEqual(row.work_state, "backlog")
        frozen_revision = row.story_revision_id
        story.refresh_from_db()
        self.assertEqual(story.current_revision.relations.get(kind=Relation.SPRINT).target_id, target.pk)
        self.publish(self.edit(story, {**story.current_revision.payload, "work_state": "done"}))
        row.refresh_from_db()
        self.assertEqual(row.work_state, "backlog")
        self.assertEqual(row.story_revision_id, frozen_revision)
        self.assertEqual(sprints.close(self.admin.pk, report, {str(story.pk): str(target.pk)}).pk, sprint.pk)

    def test_sprint_closure_rejects_unpublished_changes_atomically(self):
        app = self.application()
        sprint = self.sprint()
        story = self.story(self.epic([app]), app, sprint)
        sprint = sprints.activate(self.admin.pk, sprint.pk, sprint.edit_version)
        self.edit(story)
        report = sprints.close_report(sprint)
        with self.assertRaises(ValidationError): sprints.close(self.admin.pk, report, {str(story.pk): "backlog"})
        self.assertFalse(SprintSnapshotRow.objects.exists())
        sprint.refresh_from_db()
        self.assertEqual(sprint.current_revision.payload["sprint_state"], "active")

    def test_ac16_stale_save_preserves_current_draft(self):
        faq = self.faq()
        draft = services.begin_edit(self.admin.pk, faq.pk, faq.edit_version)
        old_version = draft.edit_version
        services.save_draft(self.admin.pk, faq.pk, old_version, "New draft", {"answer": "New draft answer"}, {})
        with self.assertRaises(services.Conflict): services.save_draft(self.admin.pk, faq.pk, old_version, "Stale draft", {"answer": "Lost answer"}, {})
        self.assertEqual(ContentDraft.objects.get(record=faq).title, "New draft")

    def test_ac17_restore_creates_draft_and_history_is_private(self):
        faq = self.faq()
        self.publish(self.edit(faq, {"answer": "Second published answer"}))
        faq.refresh_from_db()
        services.restore_to_draft(self.admin.pk, faq.pk, 1, faq.edit_version)
        self.assertEqual(ContentDraft.objects.get(record=faq).payload["answer"], "Published fictional answer")
        self.assertContains(self.client_for(self.reader).get(f"/faq/{faq.pk}/"), "Second published answer")
        self.assertEqual(self.client_for(self.reader).get(f"/admin/knowledge/{faq.pk}/history/1/").status_code, 403)

    def test_ac20_editor_structures_and_heading_identity(self):
        heading = {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Section"}]}
        paragraph = {"type": "paragraph", "content": [{"type": "text", "text": "<script>inert</script>"}]}
        body = {"type": "doc", "content": [heading, paragraph, {"type": "bulletList", "content": [{"type": "listItem", "content": [paragraph]}]}, {"type": "table", "content": [{"type": "tableRow", "content": [{"type": "tableCell", "content": [paragraph]}]}]}, {"type": "codeBlock", "content": [{"type": "text", "text": "SELECT 1"}]}]}
        doc = validate_document(body)
        identifier = doc.json["content"][0]["attrs"]["id"]
        doc.json["content"][0]["content"][0]["text"] = "Renamed"
        renamed = validate_document(doc.json)
        self.assertEqual(renamed.json["content"][0]["attrs"]["id"], identifier)
        for tag in ["<ul>", "<table>", "<pre><code>", "&lt;script&gt;"]:
            self.assertIn(tag, renamed.html)
        for href in ["javascript:alert(1)", "//untrusted.invalid", "data:text/html,x"]:
            with self.assertRaises(ValidationError): safe_href(href)

    def test_ac22_required_parent_archive_refused(self):
        app = self.application()
        self.epic([app])
        with self.assertRaises(ValidationError): services.archive(self.admin.pk, app.pk, app.edit_version)
        app.refresh_from_db()
        self.assertEqual(app.state, "published")

    def test_dependency_cycle_refused(self):
        app = self.application()
        epic = self.epic([app])
        a, b = self.story(epic, app), self.story(epic, app)
        links = {Relation.APPLICATION: [app.pk], Relation.EPIC: [epic.pk]}
        self.publish(self.edit(a, links={**links, Relation.DEPENDENCY: [b.pk]}))
        self.edit(b, links={**links, Relation.DEPENDENCY: [a.pk]})
        with self.assertRaises(ValidationError): self.publish(b)

    def test_database_history_and_identity_guards(self):
        faq, other = self.faq(), self.faq(title="Other")
        commands = [("UPDATE knowledge_contentrevision SET title = 'corrupt' WHERE id = %s", [faq.current_revision_id]), ("DELETE FROM knowledge_contentrevision WHERE id = %s", [faq.current_revision_id]), ("UPDATE knowledge_contentrecord SET current_revision_id = %s WHERE id = %s", [other.current_revision_id, faq.pk])]
        for sql, args in commands:
            with self.subTest(sql=sql):
                with self.assertRaises(DatabaseError), transaction.atomic():
                    with connection.cursor() as cursor: cursor.execute(sql, args)

    def test_csrf_direct_write_refused(self):
        faq = self.faq()
        response = self.client_for(self.admin, csrf=True).post(f"/admin/knowledge/{faq.pk}/archive/", {"expected_version": faq.edit_version})
        self.assertEqual(response.status_code, 403)
        faq.refresh_from_db()
        self.assertEqual(faq.state, "published")

    def test_reader_chatbot_gate_and_admin_transport_errors(self):
        self.assertFalse(qualification())
        response = self.client_for(self.reader).post("/assistant/query/", {"question": "Question"})
        self.assertEqual(response.json()["status"], "qualification_pending")
        self.assertEqual(response.json()["sources"], [])
        with patch("search.views.answer", side_effect=Unavailable):
            response = self.client_for(self.admin).post("/admin/search/preview/", {"question": "Question"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response["Retry-After"], "5")

    def test_chatbot_input_bounds(self):
        client = self.client_for(self.admin)
        for body in [b'{"question":""}', b'{"question":"x","extra":1}', b'{"question":"\\ud800"}', b'[]', b'{"question":1}', b'{' + b' ' * 9000]:
            with self.subTest(body=body[:20]):
                self.assertEqual(client.post("/admin/search/preview/", data=body, content_type="application/json").status_code, 422)

    def test_retrieval_capacity_and_release_on_failure(self):
        for i in range(1, 6): RetrievalSlot.objects.get_or_create(pk=i)
        slots = [retrieval.acquire_slot() for _ in range(5)]
        with self.assertRaises(Busy): retrieval.acquire_slot()
        RetrievalSlot.objects.update(token=None, lease_until=None)
        with patch("search.retrieval.rank", side_effect=Unavailable):
            with self.assertRaises(Unavailable): retrieval.answer("Question")
        self.assertFalse(RetrievalSlot.objects.filter(lease_until__isnull=False).exists())

    def test_stale_generation_cannot_return_source(self):
        faq = self.faq()
        generation = retrieval.generation()
        services.archive(self.admin.pk, faq.pk, faq.edit_version)
        with self.assertRaises(Unavailable): retrieval.final(generation, [])

    def test_document_failure_preserves_previous_publication(self):
        app = self.application()
        doc = self.draft(Kind.DOCUMENT, {"category": "spreadsheet", "description": "Synthetic table"}, {Relation.APPLICATION: [app.pk]})
        file = documents.upload(self.admin.pk, doc.pk, doc.edit_version, SimpleUploadedFile("table.csv", b"a;b\n1;2\n"), ";")
        worker.execute(worker.claim())
        file.preview.refresh_from_db()
        self.assertEqual(file.preview.state, "ready")
        doc = self.publish(doc)
        client = self.client_for(self.reader)
        response = client.get(f"/documents/{doc.pk}/download/")
        self.assertEqual(b"".join(response.streaming_content), b"a;b\n1;2\n")
        self.edit(doc)
        doc.refresh_from_db()
        replacement = documents.upload(self.admin.pk, doc.pk, doc.edit_version, SimpleUploadedFile("invalid.csv", b"\xff\xfe"))
        worker.execute(worker.claim())
        replacement.preview.refresh_from_db()
        self.assertEqual(replacement.preview.state, "failed")
        with self.assertRaises(ValidationError): self.publish(doc)
        response = client.get(f"/documents/{doc.pk}/download/")
        self.assertEqual(b"".join(response.streaming_content), b"a;b\n1;2\n")
        doc.refresh_from_db()
        services.restore_to_draft(self.admin.pk, doc.pk, 1, doc.edit_version, replace_draft=True)
        self.assertEqual(ContentDraft.objects.get(record=doc).file_revision_id, file.pk)

    def test_preview_lease_reclamation_fences_previous_attempt(self):
        app = self.application()
        doc = self.draft(Kind.DOCUMENT, {"category": "spreadsheet", "description": "Table"}, {Relation.APPLICATION: [app.pk]})
        documents.upload(self.admin.pk, doc.pk, doc.edit_version, SimpleUploadedFile("table.csv", b"a;b\n1;2\n"))
        old = worker.claim()
        Job.objects.filter(pk=old.pk).update(lease_until=timezone.now()-timedelta(seconds=1))
        fresh = worker.claim()
        self.assertNotEqual(old.lease_token, fresh.lease_token)
        self.assertFalse(worker.finish(old, "wrong", {}))
        worker.execute(fresh)
        fresh.refresh_from_db()
        self.assertEqual(fresh.state, "done")

    def test_ac21_missing_preview_and_oversized_source_are_refused(self):
        app = self.application()
        doc = self.draft(Kind.DOCUMENT, {"category": "spreadsheet", "description": "Table"}, {Relation.APPLICATION: [app.pk]})
        with self.assertRaises(ValidationError): self.publish(doc)
        with override_settings(DOCUMENT_LIMITS={**settings.DOCUMENT_LIMITS, "source_bytes": 4}):
            with self.assertRaises(ValidationError): documents.upload(self.admin.pk, doc.pk, doc.edit_version, SimpleUploadedFile("too-big.csv", b"a;b\n1;2\n"))
        self.assertEqual(FileRevision.objects.count(), 0)
        self.assertFalse(list(Path(self.private.name).rglob("source")))
        self.assertTrue(ContentDraft.objects.filter(record=doc).exists())

    def test_original_digest_corruption_is_refused(self):
        app = self.application()
        doc = self.draft(Kind.DOCUMENT, {"category": "spreadsheet", "description": "Table"}, {Relation.APPLICATION: [app.pk]})
        file = documents.upload(self.admin.pk, doc.pk, doc.edit_version, SimpleUploadedFile("table.csv", b"a;b\n1;2\n"))
        worker.execute(worker.claim())
        doc = self.publish(doc)
        (Path(self.private.name)/file.storage_key).write_bytes(b"corrupt")
        self.assertEqual(self.client_for(self.reader).get(f"/documents/{doc.pk}/download/").status_code, 503)

    def test_audit_fingerprints_metadata_without_disclosing_text(self):
        before, after = io.StringIO(), io.StringIO()
        call_command("audit_portal", stdout=before)
        self.faq(text="PRIVATE AUDIT SENTINEL")
        call_command("audit_portal", stdout=after)
        first, second = json.loads(before.getvalue()), json.loads(after.getvalue())
        self.assertTrue(second["ok"])
        self.assertNotEqual(first["database_fingerprint"]["knowledge_contentrevision"], second["database_fingerprint"]["knowledge_contentrevision"])
        self.assertNotIn("PRIVATE AUDIT SENTINEL", after.getvalue())
        self.assertNotIn("admin@example.invalid", after.getvalue())
