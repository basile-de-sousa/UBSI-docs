from pathlib import Path

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST, require_safe
from django.conf import settings
from django.urls import reverse

from accounts.middleware import api_endpoint
from knowledge import services as knowledge_services
from knowledge.models import ContentRecord, Kind
from knowledge.projections import published_records
from knowledge.views import admin_record, edit_response, errors_to_form
from knowledge.forms import VersionForm
from . import services
from .policy import ADAPTER_VERSION
from .forms import UploadForm
from .models import Preview
from .projections import document_context
from .storage import digest, private_path


def resolve(request, document_id, mode, revision=None):
    if mode == "reader":
        record = get_object_or_404(published_records(), pk=document_id, kind=Kind.DOCUMENT)
        content = record.current_revision
        version = str(content.pk)
    else:
        record = admin_record(document_id)
        if record.kind != Kind.DOCUMENT: raise Http404
        if mode == "draft":
            if not hasattr(record, "draft"): raise Http404
            content, version = record.draft, str(record.edit_version)
        else:
            content = get_object_or_404(record.revisions, number=revision)
            version = str(content.pk)
    if request.GET.get("v", version) != version or not content.file_revision_id: raise Http404
    return record, content, content.file_revision


@require_POST
def upload(request, document_id):
    record = admin_record(document_id)
    if record.kind != Kind.DOCUMENT: raise Http404
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            services.upload(request.user.pk, record.pk, form.cleaned_data["expected_version"], form.cleaned_data["source"], form.cleaned_data["delimiter"])
            messages.success(request, "Original importé. Son aperçu est en préparation ; la version publiée reste inchangée.")
            return redirect("knowledge-edit", record_id=record.pk)
        except ValidationError as error: errors_to_form(form, error)
        except knowledge_services.Conflict as error:
            form.add_error(None, error.message + " Le fichier n’a pas été importé ; resélectionnez-le dans la version actuelle.")
            return edit_response(request, record, status=409, upload_form=form, publication_errors=[error.message] if not hasattr(record, "draft") else None)
    if getattr(request, "upload_too_large", False):
        form.add_error(None, "Le fichier dépasse la taille maximale affichée. Aucun nouvel original n’a été enregistré.")
    return edit_response(request, record, status=413 if getattr(request, "upload_too_large", False) else 422, upload_form=form, publication_errors=["L’import n’a pas abouti. Ouvrez le contenu actuel et créez un brouillon avant de réessayer."] if not hasattr(record, "draft") else None)


@require_POST
def retry(request, document_id):
    record, form = admin_record(document_id), VersionForm(request.POST)
    if form.is_valid():
        try:
            services.retry(request.user.pk, record.pk, form.cleaned_data["expected_version"])
            messages.success(request, "La préparation sera relancée par le worker.")
            return redirect("knowledge-edit", record_id=record.pk)
        except ValidationError as error: return edit_response(request, record, status=422, publication_errors=error.messages)
        except knowledge_services.Conflict as error: return edit_response(request, record, status=409, publication_errors=[error.message])
    return edit_response(request, record, status=422, publication_errors=["Rechargez la page avant de réessayer."])


@require_safe
def preview(request, document_id, mode="reader", revision=None):
    record, content, _ = resolve(request, document_id, mode, revision)
    context = {"record": record, "revision": content, "page_title": "Aperçu du document", "page_section": "document", "admin_preview": mode != "reader"}
    context.update(document_context(record, content, request.GET, mode))
    return render(request, "documents/preview.html", context)


@api_endpoint
@require_safe
def status(request, document_id, mode="draft", revision=None):
    record, content, file = resolve(request, document_id, mode, revision)
    return JsonResponse({"state": file.preview.state, "label": file.preview.get_state_display(), "refresh_url": reverse("knowledge-edit", args=[record.pk]) if mode == "draft" else f"/documents/{record.pk}/"})


@require_safe
def download(request, document_id, mode="reader", revision=None):
    _, _, file = resolve(request, document_id, mode, revision)
    path = private_path(file.storage_key)
    try:
        if digest(path) != file.sha256:
            return HttpResponse("Original indisponible : échec de vérification de l’empreinte.", status=503, content_type="text/plain; charset=utf-8")
        response = FileResponse(path.open("rb"), as_attachment=True, filename=file.filename, content_type="application/octet-stream")
    except OSError:
        return HttpResponse("Original temporairement indisponible.", status=503, content_type="text/plain; charset=utf-8")
    response["X-Content-Type-Options"] = "nosniff"
    return response


@api_endpoint
@require_safe
def asset(request, document_id, asset_name, mode="reader", revision=None):
    _, _, file = resolve(request, document_id, mode, revision)
    preview = file.preview
    entry = preview.manifest.get("assets", {}).get(asset_name)
    if preview.state != Preview.State.READY or not entry or Path(asset_name).name != asset_name:
        raise Http404
    path = private_path(preview.asset_prefix) / asset_name
    try:
        response = FileResponse(path.open("rb"), content_type=entry["mime"])
    except OSError: raise Http404 from None
    response["Content-Disposition"] = 'inline; filename="preview"'
    return response


@require_safe
@xframe_options_sameorigin
def frame(request, document_id, mode="reader", revision=None):
    _, _, file = resolve(request, document_id, mode, revision)
    if file.preview.state != Preview.State.READY or file.preview.manifest.get("kind") == "table": raise Http404
    response = render(request, "documents/frame.html", {"drawio": file.format == "drawio", "viewer_version": ADAPTER_VERSION})
    origin = request.build_absolute_uri("/").rstrip("/")
    response.document_frame = True
    response["Content-Security-Policy"] = (
        f"default-src 'none'; script-src {origin}/static/ 'wasm-unsafe-eval'; style-src {origin}/static/ 'unsafe-inline'; "
        f"img-src data: blob:; font-src {origin}/static/vendor/ data:; connect-src {origin}/static/vendor/pdfjs/; "
        "worker-src 'none'; base-uri 'none'; object-src 'none'; frame-ancestors 'self'; form-action 'none'; sandbox allow-scripts"
    )
    return response
