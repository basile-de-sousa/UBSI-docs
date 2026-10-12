from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import RateBucket


class Command(BaseCommand):
    help = "Remove expired rate counters and sessions; run daily through the host scheduler."

    def handle(self, *args, **options):
        now = timezone.now()
        buckets, _ = RateBucket.objects.filter(expires_at__lte=now).delete()
        sessions, _ = Session.objects.filter(expire_date__lte=now).delete()
        self.stdout.write(f"Compteurs expirés supprimés : {buckets}. Sessions expirées supprimées : {sessions}.")
