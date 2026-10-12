import time
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from jobs.worker import claim, execute
from search import semantic


class Command(BaseCommand):
    help = "Prepare document previews and semantic indexes with bounded leases."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Drain currently due jobs then exit.")
        parser.add_argument("--kind", choices=["all", "preview", "semantic_index"], default="all")

    def handle(self, *args, **options):
        try:
            turn = 0
            while True:
                close_old_connections()
                operations = [(claim, execute), (semantic.claim, semantic.execute)]
                if options["kind"] == "preview": operations = operations[:1]
                elif options["kind"] == "semantic_index": operations = operations[1:]
                elif turn % 2: operations.reverse()
                job = None
                for claim_job, execute_job in operations:
                    job = claim_job()
                    if job:
                        execute_job(job)
                        break
                turn += 1
                if job:
                    self.stdout.write(f"{job.kind} {job.pk}: handled")
                elif options["once"]:
                    return
                else:
                    time.sleep(2)
        except KeyboardInterrupt:
            return
