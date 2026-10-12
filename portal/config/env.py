"""Small, strict environment parsers. Never include secret values in errors."""
import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from django.core.exceptions import ImproperlyConfigured


def required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"{name} is required.")
    return value


def boolean(name, default=False):
    value = os.environ.get(name, str(default)).lower()
    if value not in {"true", "false", "1", "0"}:
        raise ImproperlyConfigured(f"{name} must be true or false.")
    return value in {"true", "1"}


def integer(name, default, minimum=1, maximum=65535):
    try:
        value = int(os.environ.get(name, default))
    except ValueError:
        raise ImproperlyConfigured(f"{name} must be an integer.") from None
    if not minimum <= value <= maximum:
        raise ImproperlyConfigured(f"{name} is outside the permitted range.")
    return value


def items(name, default=""):
    return [part.strip() for part in os.environ.get(name, default).split(",") if part.strip()]


def private_path(name, forbidden):
    raw = required(name)
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ImproperlyConfigured(f"{name} must be absolute.")
    path = path.resolve()
    for root in forbidden:
        root = root.resolve()
        if path.is_relative_to(root) or root.is_relative_to(path):
            raise ImproperlyConfigured(f"{name} overlaps source or public assets.")
    return path


def database():
    try:
        url = urlsplit(required("DATABASE_URL"))
        query = parse_qs(url.query, strict_parsing=True, keep_blank_values=True)
        port = url.port if url.port is not None else 5432
        if (
            url.scheme not in {"postgres", "postgresql"}
            or not url.hostname or not url.username or not url.password
            or not url.path.strip("/") or url.fragment
            or set(query) - {"sslmode"}
            or not 1 <= port <= 65535
        ):
            raise ValueError
        sslmode = query.get("sslmode", ["prefer"])
        if len(sslmode) != 1 or sslmode[0] not in {
            "disable", "allow", "prefer", "require", "verify-ca", "verify-full"
        }:
            raise ValueError
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(url.path.lstrip("/")),
            "USER": unquote(url.username),
            "PASSWORD": unquote(url.password),
            "HOST": url.hostname,
            "PORT": port,
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {"sslmode": sslmode[0], "connect_timeout": 3},
        }
    except (ValueError, TypeError):
        raise ImproperlyConfigured("DATABASE_URL must be a valid PostgreSQL URL.") from None
