import json
from pathlib import Path

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management.base import BaseCommand, CommandError

from knowledge.importing import import_applications, parse_csv, preview_rows
from knowledge.models import ApplicationImport


class Command(BaseCommand):
    help = "Preview or execute the one-time application CSV import; never publish or overwrite."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--actor", type=str)

    def handle(self, *args, **options):
        try:
            with Path(options["file"]).open("rb") as source:
                rows, digest = parse_csv(source.read(65537))
            if options["dry_run"]:
                self.stdout.write(json.dumps({"already_imported": ApplicationImport.objects.exists(), "rows": [{"code": row["payload"]["code"], "action": "keep" if row["existing"] else "create_draft"} for row in preview_rows(rows)]}, indent=2))
                return
            if not options["actor"]:
                raise CommandError("Indiquez l’UUID d’un administrateur actif avec --actor, ou utilisez --dry-run.")
            receipt, created = import_applications(options["actor"], rows, digest)
            self.stdout.write(f"{'Import terminé' if created else 'Import déjà effectué'} : {receipt.rows.filter(created=True).count()} brouillons créés ; {receipt.rows.filter(created=False).count()} applications conservées.")
        except PermissionDenied:
            raise CommandError("L’import nécessite un administrateur actif.") from None
        except (OSError, ValueError, ValidationError) as error:
            raise CommandError(" ".join(error.messages) if isinstance(error, ValidationError) else "Le fichier ou l’identifiant fourni est invalide.") from None
