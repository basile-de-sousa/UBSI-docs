#!/usr/bin/env python3
"""Create local secrets once; never print their values or overwrite an environment."""
import os
from pathlib import Path
import secrets
import tempfile


def main():
    portal = Path(__file__).resolve().parent.parent
    target = portal / ".env"
    if target.exists():
        raise SystemExit("portal/.env existe déjà ; aucun fichier modifié.")
    private = Path(tempfile.mkdtemp(prefix="ubsi-portal-private-"))
    password = secrets.token_hex(24)
    values = {
        "PORTAL_ENV": "development", "DEBUG": "true",
        "SECRET_KEY": secrets.token_hex(48),
        "ALLOWED_HOSTS": "localhost,127.0.0.1,[::1]",
        "PUBLIC_BASE_URL": "http://127.0.0.1:8000",
        "POSTGRES_DB": "ubsi", "POSTGRES_USER": "ubsi",
        "POSTGRES_PASSWORD": password,
        "DATABASE_URL": f"postgresql://ubsi:{password}@127.0.0.1:55432/ubsi",
        "PRIVATE_STORAGE_ROOT": str(private),
        "EMAIL_HOST": "", "DEFAULT_FROM_EMAIL": "",
        "TRUST_HTTPS_PROXY": "false",
    }
    with os.fdopen(os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "w") as stream:
        stream.write("# Local development only. Never commit this file.\n")
        stream.writelines(f"{key}={value}\n" for key, value in values.items())
    print("portal/.env créé avec des secrets aléatoires (permissions 0600).")
    print("Stockage privé temporaire créé hors du dépôt. Consultez le README pour le démarrage.")


if __name__ == "__main__":
    main()
