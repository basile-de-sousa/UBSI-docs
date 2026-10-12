import os

from django.conf import settings
from django.core.checks import Error, register
from django.core.exceptions import ImproperlyConfigured

from .assets import frontend_assets


@register()
def foundation_checks(app_configs, **kwargs):
    errors = []
    try:
        frontend_assets()
    except ImproperlyConfigured as error:
        errors.append(Error(str(error), id="portal.E001"))
    root = settings.PRIVATE_STORAGE_ROOT
    if not root.is_dir() or not os.access(root, os.R_OK | os.W_OK | os.X_OK):
        errors.append(Error("PRIVATE_STORAGE_ROOT must be a readable, writable directory.", id="portal.E002"))
    return errors
