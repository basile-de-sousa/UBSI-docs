from tempfile import TemporaryDirectory
from uuid import uuid4
from pathlib import Path

from django.test import Client, override_settings

from accounts.models import AccountControl, User
from knowledge import services
from knowledge.models import Kind, ProjectState, Relation


class Fixtures:
    def setUp(self):
        super().setUp()
        self.private = TemporaryDirectory(prefix="ubsi-m7-test-")
        self.addCleanup(self.private.cleanup)
        override = override_settings(PRIVATE_STORAGE_ROOT=Path(self.private.name), ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"], EMAIL_HOST="unused.invalid", DEFAULT_FROM_EMAIL="portal@example.invalid", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", CHATBOT_QUALIFICATION_FILE=None)
        override.enable()
        self.addCleanup(override.disable)
        AccountControl.objects.get_or_create(pk=1)
        ProjectState.objects.get_or_create(pk=1)
        self.admin = User.objects.create_user("admin@example.invalid", display_name="Fictional administrator", role="admin")
        self.reader = User.objects.create_user("reader@example.invalid", display_name="Fictional reader")

    def client_for(self, user=None, csrf=False):
        client = Client(enforce_csrf_checks=csrf)
        if user:
            client.force_login(user)
            session = client.session
            session["account_access_version"] = user.access_version
            session.save()
        return client

    def draft(self, kind, payload, links=None, title="Fictional content", owner=None):
        return services.create_draft(self.admin.pk, uuid4(), kind, title, payload, links or {}, responsible_id=owner.pk if owner else None)

    def publish(self, record):
        record.refresh_from_db()
        return services.publish(self.admin.pk, record.pk, record.edit_version)

    def application(self, code="APP-M7"):
        return self.publish(self.draft(Kind.APPLICATION, {"code": code, "description": "Fictional application", "type": "internal"}, title=code))

    def faq(self, text="Published fictional answer", title="Fictional question"):
        return self.publish(self.draft(Kind.FAQ, {"answer": text, "aliases": []}, title=title))

    def epic(self, apps):
        return self.publish(self.draft(Kind.EPIC, {"objective": "Goal", "description": "Description", "scope": "Scope"}, {Relation.APPLICATION: [a.pk for a in apps]}))

    def story(self, epic, app, sprint=None):
        links = {Relation.APPLICATION: [app.pk], Relation.EPIC: [epic.pk]}
        if sprint: links[Relation.SPRINT] = [sprint.pk]
        return self.publish(self.draft(Kind.STORY, {"actor": "Member", "need": "Browse", "benefit": "Find knowledge", "criteria": ["Published content is visible"]}, links, owner=self.reader))

    def sprint(self):
        return self.publish(self.draft(Kind.SPRINT, {"objective": "Fictional objective", "start_date": "2026-10-12", "end_date": "2026-10-23"}, owner=self.reader))

    def edit(self, record, payload=None, links=None, title=None):
        record.refresh_from_db()
        record = services.begin_edit(self.admin.pk, record.pk, record.edit_version)
        draft = record.draft
        if links is None:
            links = {}
            for relation in draft.relations.all(): links.setdefault(relation.kind, []).append(relation.target_id)
        return services.save_draft(self.admin.pk, record.pk, record.edit_version, title or draft.title, payload or draft.payload, links)
