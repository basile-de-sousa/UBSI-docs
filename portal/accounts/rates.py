"""Fixed-window limits using PostgreSQL row locks and expiring HMAC keys."""
import math
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import RateBucket


class Throttled(Exception):
    def __init__(self, retry_after):
        self.retry_after = max(1, retry_after)


def consume(scope, identity, limit, seconds):
    key = salted_hmac("accounts.rate", f"{scope}:{identity}", algorithm="sha256").hexdigest()
    with transaction.atomic():
        now = timezone.now()
        RateBucket.objects.get_or_create(key=key, defaults={"expires_at": now + timedelta(seconds=seconds)})
        bucket = RateBucket.objects.select_for_update().get(key=key)
        if bucket.expires_at <= now:
            bucket.count = 0
            bucket.expires_at = now + timedelta(seconds=seconds)
        if bucket.count >= limit:
            raise Throttled(math.ceil((bucket.expires_at - now).total_seconds()))
        bucket.count += 1
        bucket.save(update_fields=["count", "expires_at"])


def source(request, scope):
    policy = settings.AUTH_RATE_LIMITS[scope]
    # REMOTE_ADDR is rewritten only by the explicit trusted-proxy middleware.
    consume(scope + ":source", request.META.get("REMOTE_ADDR", "unknown"), policy["source"], policy["seconds"])


def account(scope, email):
    policy = settings.AUTH_RATE_LIMITS[scope]
    consume(scope + ":account", email, policy["account"], policy["seconds"])
