from django.core.management.base import BaseCommand
from accounts.models import User
from search.indexing import queue_reindex


class Command(BaseCommand):
    help = "Queue current published sources for indexing; requires an active administrator UUID."

    def add_arguments(self, parser):
        parser.add_argument("--actor", required=True)

    def handle(self, *args, **options):
        actor = User.objects.get(pk=options["actor"], is_active=True, role=User.Role.ADMIN)
        queue_reindex(actor)
        self.stdout.write("Current published sources queued. Reader activation is unchanged.")
