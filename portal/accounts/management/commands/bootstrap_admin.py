import getpass
import sys

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.forms import EmailForm
from accounts.services import AccountError, bootstrap_admin


class Command(BaseCommand):
    help = "Create the first administrator interactively; no credentials in arguments or fixtures."

    def handle(self, *args, **options):
        if not sys.stdin.isatty():
            raise CommandError("Utilisez un terminal interactif pour créer le premier administrateur.")
        email_form = EmailForm({"email": input("Adresse email : ")})
        if not email_form.is_valid():
            raise CommandError("Adresse email invalide.")
        name = input("Nom affiché : ").strip()
        if not name or len(name) > 120:
            raise CommandError("Le nom affiché doit contenir entre 1 et 120 caractères.")
        password = getpass.getpass("Mot de passe (12 caractères minimum) : ")
        if password != getpass.getpass("Confirmer le mot de passe : "):
            raise CommandError("Les mots de passe ne correspondent pas.")
        try:
            bootstrap_admin(email_form.cleaned_data["email"], name, password)
        except AccountError as error:
            raise CommandError(error.message) from None
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from None
        self.stdout.write(self.style.SUCCESS("Premier administrateur créé. Vous pouvez vous connecter."))
