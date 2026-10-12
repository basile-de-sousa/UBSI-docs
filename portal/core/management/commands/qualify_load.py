"""Local HTTP measurements with temporary fictional sessions, never production."""
from concurrent.futures import ThreadPoolExecutor
import json
import math
from threading import Barrier
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand, CommandError
from django.utils.crypto import salted_hmac

from accounts.models import RateBucket, User
from knowledge.models import Kind
from search.corpus import records
from search.policy import qualification


def summary(rows):
    times = sorted(row["seconds"] for row in rows)
    statuses = {str(status): sum(row["status"] == status for row in rows) for status in sorted({row["status"] for row in rows})}
    return {"requests": len(rows), "p95_seconds": round(times[math.ceil(len(times)*.95)-1], 4), "maximum_seconds": round(times[-1], 4), "statuses": statuses}


class Command(BaseCommand):
    help = "Measure an isolated development server using 46 ephemeral readers and five admin preview requests."

    def add_arguments(self, parser):
        parser.add_argument("--server", default="http://127.0.0.1:8000")
        parser.add_argument("--confirm-isolated", action="store_true")
        parser.add_argument("--chat-batches", type=int, choices=range(1, 11), default=10)

    def handle(self, *args, **options):
        origin = urlsplit(options["server"])
        if settings.PRODUCTION or not options["confirm_isolated"] or origin.hostname not in {"127.0.0.1", "localhost"} or origin.scheme != "http" or origin.path or origin.query or origin.fragment:
            raise CommandError("Only an explicitly isolated development server on loopback is supported.")
        users, sessions, cookies = [], [], []
        try:
            for index in range(46):
                user = User(email=f"m7-load-{uuid4()}@example.invalid", display_name="Fictional M7 load member", role="admin" if index < 5 else "user")
                user.set_unusable_password()
                user.save()
                users.append(user.pk)
                session = SessionStore()
                session.update({SESSION_KEY: str(user.pk), BACKEND_SESSION_KEY: "accounts.backends.EmailBackend", HASH_SESSION_KEY: user.get_session_auth_hash(), "account_access_version": user.access_version})
                session.set_expiry(300)
                session.save()
                sessions.append(session.session_key)
                cookies.append(settings.SESSION_COOKIE_NAME+"="+session.session_key)

            def request(index, path, body=None):
                headers = {"Cookie": cookies[index]}
                if body is not None:
                    # CSRF is acquired through a regular page, without token logging.
                    page = urlopen(Request(options["server"]+"/admin/search/", headers=headers), timeout=30)
                    import re
                    token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page.read().decode()).group(1)
                    csrf_cookie = next(value.split(';')[0] for name, value in page.headers.items() if name.lower() == "set-cookie" and value.startswith(settings.CSRF_COOKIE_NAME+'='))
                    headers.update({"Cookie": cookies[index]+"; "+csrf_cookie, "X-CSRFToken": token, "Content-Type": "application/json", "Origin": options["server"]})
                started = time.perf_counter()
                try:
                    with urlopen(Request(options["server"]+path, headers=headers, data=body), timeout=40) as response:
                        status = response.status if response.geturl() == options["server"]+path else 302
                        response.read()
                except HTTPError as error:
                    status = error.code
                    error.read()
                return {"status": status, "seconds": time.perf_counter()-started}

            report = {"scope": "Local loopback HTTP; synthetic corpus; admin experimental preview, not reader business acceptance or real-host qualification", "members": 46, "chatbot_qualified": qualification(), "ordinary": {}}
            with ThreadPoolExecutor(max_workers=46) as pool:
                for path in ["/applications/", "/search/?q=modification", "/documents/"]:
                    request(0, path)  # Warm template/static/database paths.
                    rows = list(pool.map(lambda index: request(index % 46, path), range(138)))
                    report["ordinary"][path] = summary(rows)
            faq = records().filter(kind=Kind.FAQ).first()
            if faq:
                body = json.dumps({"question": faq.current_revision.title}).encode()
                request(0, "/admin/search/preview/", body)  # Warm local model pair.
                barrier = Barrier(5)
                def chat(index):
                    barrier.wait(timeout=10)
                    return request(index, "/admin/search/preview/", body)
                rows = []
                for _ in range(options["chat_batches"]):
                    with ThreadPoolExecutor(max_workers=5) as pool: rows.extend(pool.map(chat, range(5)))
                report["chat_preview"] = {**summary(rows), "batches": options["chat_batches"], "concurrent_per_batch": 5}
            else: report["chat_preview"] = {"skipped": "No published FAQ in the isolated corpus"}
            report["ordinary_local_target_met"] = all(row["p95_seconds"] < 2 and row["statuses"] == {"200": row["requests"]} for row in report["ordinary"].values())
            chat = report["chat_preview"]
            report["chat_preview_local_target_met"] = chat.get("statuses") == {"200": 5*options["chat_batches"]} and chat.get("p95_seconds", 99) < 5
            self.stdout.write(json.dumps(report, indent=2))
        finally:
            Session.objects.filter(session_key__in=sessions).delete()
            RateBucket.objects.filter(key__in=[salted_hmac("accounts.rate", f"assistant:{identifier}", algorithm="sha256").hexdigest() for identifier in users]).delete()
            User.objects.filter(pk__in=users).delete()
