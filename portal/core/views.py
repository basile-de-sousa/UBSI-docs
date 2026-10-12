import logging
import os
import shutil

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST, require_safe

from accounts.middleware import api_endpoint

from .assets import frontend_assets

logger = logging.getLogger(__name__)


@login_not_required
@require_safe
def entry(request):
    return render(request, "core/entry.html")


@login_not_required
@require_safe
def preview(request):
    # This route is registered only in explicit debug development mode.
    return render(request, "core/preview.html")


@require_safe
def applications(request):
    return render(request, "core/applications.html", {"page_title": "Applications", "page_section": "applications"})


@require_safe
def admin_placeholder(request):
    return render(request, "core/construction.html", {"page_title": "Administration des contenus", "page_section": "knowledge"})


@require_safe
def document_placeholder(request, document_id, revision=None):
    raise Http404


@api_endpoint
@require_POST
def assistant_placeholder(request):
    return JsonResponse({"status": "unavailable", "message": "L’assistant n’est pas encore disponible."}, status=503)


@login_not_required
@require_safe
def live(request):
    return JsonResponse({"status": "ok"})


@login_not_required
@require_safe
def ready(request):
    try:
        from search.policy import qualification
        from search import runtime
        if qualification() and not runtime.loaded():
            raise RuntimeError
        assets = frontend_assets()
        if not settings.DEBUG and not all(
            (settings.STATIC_ROOT / path).is_file()
            for path in assets["files"]
        ):
            raise RuntimeError
        document_assets = ["assets/drawio-config.js", "assets/drawio-frame.js", "assets/document-frame.mjs", "assets/document-frame.css", "vendor/viewer-static.min.js", "vendor/stencils.min.js", "vendor/pdfjs/build/pdf.mjs", "vendor/pdfjs/build/pdf.worker.mjs"]
        if not all((settings.STATIC_ROOT / path).is_file() for path in document_assets):
            raise RuntimeError
        if not all((settings.DOCUMENT_VENDOR_ROOT / name).is_file() for name in ["plantuml.jar", "drawio-shapes.json"]) or not shutil.which("java"):
            raise RuntimeError
        if not os.access(settings.PRIVATE_STORAGE_ROOT, os.R_OK | os.W_OK | os.X_OK):
            raise RuntimeError
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        executor = MigrationExecutor(connection)
        if executor.migration_plan(executor.loader.graph.leaf_nodes()):
            raise RuntimeError
    except Exception:
        # Deliberately omit exception messages: they can contain DB credentials/paths.
        logger.warning("Portal readiness failed.")
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


@login_not_required
def not_found(request, exception):
    return render(request, "core/error.html", {"error_title": "Page indisponible", "error_message": "Cette page n’existe pas ou n’est pas accessible."}, status=404)


@login_not_required
def server_error(request):
    # Keep error pages independent of the asset manifest and database.
    return render(request, "core/500.html", status=500)


@login_not_required
def forbidden(request, exception):
    return render(request, "core/error.html", {"error_title": "Accès réservé", "error_message": "Vous ne disposez pas des droits nécessaires."}, status=403)


@login_not_required
def csrf_failure(request, reason=""):
    # Keep diagnostics useful without logging headers, submitted tokens or URLs.
    if "cookie not set" in reason.lower():
        code = "missing_cookie"
    elif "origin" in reason.lower() or "referer" in reason.lower():
        code = "untrusted_origin"
    elif "incorrect" in reason.lower():
        code = "token_mismatch"
    else:
        code = "missing_or_malformed_token"
    logger.warning("portal.csrf_rejected.%s", code)
    return render(request, "core/error.html", {"error_title": "Formulaire expiré", "error_message": "Rechargez la page puis réessayez. Aucune modification n’a été enregistrée."}, status=403)
