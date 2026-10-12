"""Shared settings; production is the fail-closed default."""
import os
from ipaddress import ip_network
from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from . import env

BASE_DIR = Path(__file__).resolve().parent.parent
ENVIRONMENT = os.environ.get("PORTAL_ENV", "production")
if ENVIRONMENT not in {"development", "production"}:
    raise ImproperlyConfigured("PORTAL_ENV must be development or production.")
PRODUCTION = ENVIRONMENT == "production"
DEBUG = env.boolean("DEBUG")
if PRODUCTION and DEBUG:
    raise ImproperlyConfigured("DEBUG is forbidden in production.")
SECRET_KEY = env.required("SECRET_KEY")
if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith(("change-me", "django-insecure-")):
    raise ImproperlyConfigured("SECRET_KEY must be a generated secret of at least 50 characters.")
ALLOWED_HOSTS = env.items("ALLOWED_HOSTS")
if not ALLOWED_HOSTS or any(
    "*" in host or "://" in host or host.startswith(".") or "/" in host
    or any(char.isspace() for char in host)
    for host in ALLOWED_HOSTS
):
    raise ImproperlyConfigured("ALLOWED_HOSTS must contain explicit host names.")
CSRF_TRUSTED_ORIGINS = env.items("CSRF_TRUSTED_ORIGINS")
for origin in CSRF_TRUSTED_ORIGINS:
    try:
        parsed_origin = urlsplit(origin)
        if (
            parsed_origin.scheme != "https" or not parsed_origin.hostname or "*" in origin
            or parsed_origin.username or parsed_origin.password or parsed_origin.path
            or parsed_origin.query or parsed_origin.fragment
            or (parsed_origin.port is not None and not 1 <= parsed_origin.port <= 65535)
        ):
            raise ValueError
    except ValueError:
        raise ImproperlyConfigured("CSRF_TRUSTED_ORIGINS accepts explicit HTTPS origins only.") from None

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig",
    "core.apps.CoreConfig",
    "knowledge.apps.KnowledgeConfig",
    "documents.apps.DocumentsConfig",
    "search.apps.SearchConfig",
    "jobs.apps.JobsConfig",
    "sprints.apps.SprintsConfig",
]
MIDDLEWARE = [
    "core.middleware.TrustedProxyMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "core.middleware.ResponsePolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.middleware.AccessMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "core.context_processors.environment",
    ]},
}]
DATABASES = {"default": env.database()}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["accounts.backends.EmailBackend"]
LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
     "OPTIONS": {"user_attributes": ["email", "display_name"]}},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static-collected"
FRONTEND_ROOT = BASE_DIR / "static-built"
STATICFILES_DIRS = [FRONTEND_ROOT] if FRONTEND_ROOT.exists() else []
STORAGES = {
    "default": {"BACKEND": "documents.storage.PrivateStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
# No MEDIA_URL, URL mapping, or static server for this tree.
PRIVATE_STORAGE_ROOT = env.private_path("PRIVATE_STORAGE_ROOT", [BASE_DIR.parent, STATIC_ROOT, FRONTEND_ROOT])

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 12 * 60 * 60
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = PRODUCTION
CSRF_COOKIE_SECURE = PRODUCTION
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
PASSWORD_RESET_TIMEOUT = 60 * 60
SECURE_SSL_REDIRECT = PRODUCTION
SECURE_HSTS_SECONDS = 31536000 if PRODUCTION else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = PRODUCTION and env.boolean("HSTS_INCLUDE_SUBDOMAINS")
SECURE_HSTS_PRELOAD = PRODUCTION and env.boolean("HSTS_PRELOAD")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
# Opt in only when the host proxy overwrites incoming forwarding headers.
try:
    TRUSTED_PROXY_NETWORKS = [ip_network(value) for value in env.items("TRUSTED_PROXY_CIDRS")]
    if any(network.prefixlen == 0 for network in TRUSTED_PROXY_NETWORKS): raise ValueError
except ValueError:
    raise ImproperlyConfigured("TRUSTED_PROXY_CIDRS requires explicit proxy networks, never a default route.") from None
if env.boolean("TRUST_HTTPS_PROXY"):
    if not TRUSTED_PROXY_NETWORKS:
        raise ImproperlyConfigured("TRUST_HTTPS_PROXY requires TRUSTED_PROXY_CIDRS.")
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Loopback/container health probes do not traverse the HTTPS proxy.
SECURE_REDIRECT_EXEMPT = [r"^health/live/$", r"^health/ready/$"]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = env.integer("EMAIL_PORT", 587)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env.boolean("EMAIL_USE_TLS", True)
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "")
EMAIL_USE_SSL = env.boolean("EMAIL_USE_SSL")
if EMAIL_USE_SSL and EMAIL_USE_TLS:
    raise ImproperlyConfigured("Choose EMAIL_USE_TLS or EMAIL_USE_SSL, not both.")
if PRODUCTION and (not EMAIL_HOST or not DEFAULT_FROM_EMAIL):
    raise ImproperlyConfigured("Production requires EMAIL_HOST and DEFAULT_FROM_EMAIL.")

PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "" if PRODUCTION else "http://127.0.0.1:8000").rstrip("/")
try:
    public_url = urlsplit(PUBLIC_BASE_URL)
    if (
        public_url.scheme not in ({"https"} if PRODUCTION else {"http", "https"})
        or not public_url.hostname or public_url.path or public_url.query or public_url.fragment
        or public_url.username or public_url.password
        or (public_url.port is not None and not 1 <= public_url.port <= 65535)
        or (f"[{public_url.hostname}]" if ":" in public_url.hostname else public_url.hostname) not in ALLOWED_HOSTS
    ):
        raise ValueError
except ValueError:
    raise ImproperlyConfigured("PUBLIC_BASE_URL must be a trusted application origin (HTTPS in production).") from None
INVITATION_HOURS = 72
AUTH_RATE_LIMITS = {
    "login": {"source": env.integer("LOGIN_SOURCE_LIMIT", 30), "account": env.integer("LOGIN_ACCOUNT_LIMIT", 5), "seconds": 900},
    "recovery": {"source": env.integer("RECOVERY_SOURCE_LIMIT", 20), "account": env.integer("RECOVERY_ACCOUNT_LIMIT", 3), "seconds": 3600},
    "proof": {"source": env.integer("TOKEN_SOURCE_LIMIT", 60), "account": 20, "seconds": 900},
    "manage": {"source": 120, "account": 100, "seconds": 3600},
}
CSRF_FAILURE_VIEW = "core.views.csrf_failure"

# Avoid access logs containing future invite/reset tokens or question text.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "discard": {"class": "logging.NullHandler"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django.server": {"handlers": ["discard"], "propagate": False},
        "django.request": {"handlers": ["discard"], "propagate": False},
        "django.security": {"handlers": ["discard"], "propagate": False},
    },
}

# Approved source bounds and qualified initial adapter defaults.
DOCUMENT_LIMITS = {
    "source_bytes": env.integer("DOCUMENT_SOURCE_BYTES", 20 * 1024**2, maximum=100 * 1024**2),
    "sheets": env.integer("DOCUMENT_MAX_SHEETS", 50, maximum=100),
    "cells": env.integer("DOCUMENT_MAX_CELLS", 200000, maximum=1000000),
    "rows": env.integer("DOCUMENT_MAX_ROWS", 20000, maximum=100000),
    "columns": env.integer("DOCUMENT_MAX_COLUMNS", 200, maximum=1000),
    "expanded_bytes": env.integer("DOCUMENT_EXPANDED_BYTES", 200 * 1024**2, maximum=500 * 1024**2),
    "pages": env.integer("DOCUMENT_MAX_PAGES", 50, maximum=100),
    "pixels": env.integer("DOCUMENT_MAX_PIXELS", 16000000, maximum=32000000),
    "side": env.integer("DOCUMENT_MAX_SIDE", 8000, maximum=16000),
    "drawio_page_bytes": env.integer("DRAWIO_PAGE_BYTES", 8 * 1024**2, maximum=20 * 1024**2),
    "plantuml_seconds": env.integer("PLANTUML_SECONDS", 20, maximum=45),
    "plantuml_heap_mb": env.integer("PLANTUML_HEAP_MB", 256, minimum=128, maximum=512),
}
DOCUMENT_JOB_SECONDS = env.integer("DOCUMENT_JOB_SECONDS", 60, maximum=120)
DOCUMENT_CHILD_MEMORY_MB = env.integer("DOCUMENT_CHILD_MEMORY_MB", 1536, minimum=512, maximum=4096)
DOCUMENT_JAVA_ADDRESS_SPACE_MB = env.integer("DOCUMENT_JAVA_ADDRESS_SPACE_MB", 4096, minimum=1024, maximum=8192)
DOCUMENT_VENDOR_ROOT = BASE_DIR / ".vendor"
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024**2
DATA_UPLOAD_MAX_NUMBER_FILES = 1
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024**2
FILE_UPLOAD_HANDLERS = ["documents.upload.BoundedUploadHandler", "django.core.files.uploadhandler.MemoryFileUploadHandler", "django.core.files.uploadhandler.TemporaryFileUploadHandler"]

# Model artifacts are reproducible public files, never served as browser assets.
SEARCH_MODEL_ROOT = Path(os.environ.get("SEARCH_MODEL_ROOT", str(BASE_DIR / ".models"))).expanduser().resolve()
if SEARCH_MODEL_ROOT.is_relative_to(STATIC_ROOT) or SEARCH_MODEL_ROOT.is_relative_to(FRONTEND_ROOT):
    raise ImproperlyConfigured("SEARCH_MODEL_ROOT must be outside browser assets.")
SEARCH_CPU_THREADS = env.integer("SEARCH_CPU_THREADS", 2, maximum=4)
SEARCH_MAX_CHUNKS = env.integer("SEARCH_MAX_CHUNKS", 10000, maximum=10000)
SEARCH_JOB_SECONDS = env.integer("SEARCH_JOB_SECONDS", 300, minimum=30, maximum=900)
SEARCH_INFERENCE_WAIT_SECONDS = 4
CHATBOT_QUALIFICATION_FILE = Path(os.environ["CHATBOT_QUALIFICATION_FILE"]).expanduser().resolve() if os.environ.get("CHATBOT_QUALIFICATION_FILE") else None
if CHATBOT_QUALIFICATION_FILE and not CHATBOT_QUALIFICATION_FILE.is_relative_to(PRIVATE_STORAGE_ROOT):
    raise ImproperlyConfigured("CHATBOT_QUALIFICATION_FILE must be inside private storage.")
from documents.headers import static_headers
WHITENOISE_ADD_HEADERS_FUNCTION = static_headers
