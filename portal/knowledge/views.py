from uuid import uuid4

from django.contrib import messages
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import Http404
from django.http import QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from . import importing, services
from .editor import validate_document
from .forms import ConfirmForm, ContentForm, ImportConfirm, ImportUpload, ReaderFilters, RestoreForm, VersionForm
from .models import ApplicationImport, ContentRecord, EpicProgress, Kind, Priority, Relation, RevisionRelation, SprintProgress, State, StoryProgress
from .projections import canonical_url, published_records, reader_links
from .schema import EDITABLE_KINDS, normalise

LABELS = {Kind.APPLICATION: "Applications", Kind.EPIC: "Epics", Kind.STORY: "User stories", Kind.SPRINT: "Sprints", Kind.SPECIFICATION: "Spécifications", Kind.FAQ: "FAQ", Kind.DOCUMENT: "Documents"}


def errors_to_form(form, error):
    if hasattr(error, "message_dict"):
        for key, values in error.message_dict.items():
            form.add_error(key if key in form.fields else None, values)
    else:
        form.add_error(None, error)


def record_context(record):
    return {"record": record, "page_title": "Administration des contenus", "page_section": "knowledge", "reader_url": canonical_url(record), "version_form": VersionForm(initial={"expected_version": record.edit_version})}


@require_safe
def reader_list(request, kind):
    if kind not in EDITABLE_KINDS:
        raise Http404
    queryset = published_records().filter(kind=kind).order_by("current_revision__title", "id")
    any_published = queryset.exists()
    form = ReaderFilters(request.GET, kind=kind)
    valid = form.is_valid()
    if valid:
        query = form.cleaned_data.get("q", "")
        if query:
            terms = Q(current_revision__title__icontains=query) | Q(current_revision__plain_text__icontains=query) | Q(current_revision__payload__aliases__icontains=query) | Q(current_revision__payload__code__icontains=query)
            if kind != Kind.APPLICATION:
                terms |= Q(reference__icontains=query)
            queryset = queryset.filter(terms)
        if form.cleaned_data.get("application"):
            queryset = queryset.filter(current_revision__relations__kind=Relation.APPLICATION, current_revision__relations__target=form.cleaned_data["application"]).distinct()
        if form.cleaned_data.get("category"):
            queryset = queryset.filter(current_revision__payload__category__iexact=form.cleaned_data["category"])
        if form.cleaned_data.get("epic"):
            queryset = queryset.filter(current_revision__relations__kind=Relation.EPIC, current_revision__relations__target=form.cleaned_data["epic"]).distinct()
        if form.cleaned_data.get("progress"):
            queryset = queryset.filter(**{f"current_revision__payload__{'sprint_state' if kind == Kind.SPRINT else 'work_state'}": form.cleaned_data["progress"]})
        if form.cleaned_data.get("priority"):
            queryset = queryset.filter(current_revision__payload__priority=form.cleaned_data["priority"])
    else:
        queryset = queryset.none()
    cleaned_query = request.GET.copy()
    for key in list(cleaned_query):
        if key not in form.fields:
            del cleaned_query[key]
    page = Paginator(queryset, 24).get_page(request.GET.get("page"))
    for record in page:
        record.reader_url = canonical_url(record)
        record.current_revision.record = record
    active_sprint = published_records().filter(kind=Kind.SPRINT, current_revision__payload__sprint_state=SprintProgress.ACTIVE).first() if kind == Kind.APPLICATION else None
    return render(request, "knowledge/list.html", {"page_title": LABELS[kind], "page_section": kind if kind != Kind.APPLICATION else "applications", "kind": kind, "filters": form, "page": page, "any_published": any_published, "filter_query": cleaned_query.urlencode(), "active_sprint": active_sprint}, status=200 if valid else 422)


@require_safe
def reader_detail(request, kind, record_id):
    record = get_object_or_404(published_records(), pk=record_id, kind=kind)
    revision = record.current_revision
    if request.GET.get("source_revision") and request.GET["source_revision"] != str(revision.pk):
        raise Http404
    revision.record = record
    sections = validate_document(revision.payload["body"]).sections if kind == Kind.SPECIFICATION else []
    section = request.GET.get("section", "")
    missing = bool(section and not any(row["id"] == section for row in sections))
    context = {"record": record, "revision": revision, "sections": [row for row in sections if row["id"]], "missing_section": missing, "links": reader_links(record), "page_title": LABELS.get(kind, record.get_kind_display()), "page_section": kind if kind != Kind.APPLICATION else "applications"}
    if kind == Kind.DOCUMENT:
        from documents.projections import document_context
        context.update(document_context(record, revision, request.GET))
    if kind == Kind.SPRINT:
        from sprints.projections import sprint_context
        context.update(sprint_context(record, request.GET))
    return render(request, "knowledge/detail.html", context)


@require_safe
def directory(request):
    records = ContentRecord.objects.filter(discarded_at__isnull=True, kind__in=EDITABLE_KINDS).select_related("current_revision", "draft", "draft__file_revision__preview").order_by("-updated_at", "id")
    counts = {"drafts": records.filter(draft__isnull=False).count(), "published": records.filter(state=State.PUBLISHED).count(), "archived": records.filter(state=State.ARCHIVED).count(), "processing": records.filter(draft__file_revision__preview__state="processing").count(), "failed": records.filter(draft__file_revision__preview__state="failed").count()}
    query, state, kind = request.GET.get("q", "")[:200], request.GET.get("state", ""), request.GET.get("kind", "")
    if query:
        records = records.filter(Q(reference__icontains=query) | Q(draft__title__icontains=query) | Q(current_revision__title__icontains=query))
    if state == "drafts":
        records = records.filter(draft__isnull=False)
    elif state == "changed":
        records = records.filter(state=State.PUBLISHED, draft__isnull=False)
    elif state in {"processing", "failed"}:
        records = records.filter(draft__file_revision__preview__state=state)
    elif state in State.values:
        records = records.filter(state=state)
    if kind in EDITABLE_KINDS:
        records = records.filter(kind=kind)
    filters = QueryDict(mutable=True)
    filters["q"] = query
    filters["state"] = state if state in [*State.values, "drafts", "changed", "processing", "failed"] else ""
    filters["kind"] = kind if kind in EDITABLE_KINDS else ""
    return render(request, "knowledge/admin_list.html", {"page_title": "Contenus", "page_section": "knowledge", "page": Paginator(records, 25).get_page(request.GET.get("page")), "counts": counts, "q": query, "selected_state": filters["state"], "selected_kind": filters["kind"], "kinds": [(value, LABELS[value]) for value in EDITABLE_KINDS], "states": State.choices, "filter_query": filters.urlencode()})


def admin_record(record_id):
    return get_object_or_404(ContentRecord.objects.select_related("current_revision", "draft"), pk=record_id, discarded_at__isnull=True, kind__in=EDITABLE_KINDS)


def edit_response(request, record, form=None, status=200, publication_errors=None, conflict=False, upload_form=None):
    context = record_context(record)
    context.update({"form": form if form is not None else ContentForm(record.kind, record=record) if hasattr(record, "draft") else None, "kind": record.kind, "kind_label": record.get_kind_display(), "publication_errors": publication_errors, "conflict": conflict})
    if record.kind == Kind.DOCUMENT and hasattr(record, "draft"):
        from django.conf import settings
        from documents.forms import UploadForm
        from documents.projections import document_context
        context.update(document_context(record, record.draft, request.GET, "draft"))
        context.update({"upload_form": upload_form or UploadForm(initial={"expected_version": record.edit_version}), "document_limits": settings.DOCUMENT_LIMITS, "document_job_seconds": settings.DOCUMENT_JOB_SECONDS})
    return render(request, "knowledge/edit.html", context, status=status)


@require_http_methods(["GET", "POST"])
def create(request, kind):
    if kind not in EDITABLE_KINDS:
        raise Http404
    form = ContentForm(kind, request.POST if request.method == "POST" else None)
    status, conflict = 200, False
    if request.method == "POST" and form.is_valid():
        try:
            payload, relations = form.payload_and_relations()
            record = services.create_draft(request.user.pk, form.cleaned_data["creation_id"], kind, form.cleaned_data["title"], payload, relations, **form.responsibility())
            messages.success(request, "Brouillon enregistré. Il reste invisible aux lecteurs tant qu’il n’est pas publié.")
            return redirect("knowledge-edit", record_id=record.pk)
        except ValidationError as error:
            errors_to_form(form, error)
            status = 422
        except services.Conflict as error:
            form.add_error(None, error.message)
            status, conflict = 409, True
    elif request.method == "POST":
        status = 422
    return render(request, "knowledge/edit.html", {"form": form, "kind": kind, "kind_label": Kind(kind).label, "page_title": "Nouveau contenu", "page_section": "knowledge", "conflict": conflict}, status=status)


@require_http_methods(["GET", "POST"])
def edit(request, record_id):
    record = admin_record(record_id)
    if request.method == "GET":
        return edit_response(request, record)
    form = ContentForm(record.kind, request.POST, record=record)
    if form.is_valid():
        try:
            payload, relations = form.payload_and_relations()
            services.save_draft(request.user.pk, record.pk, form.cleaned_data["expected_version"], form.cleaned_data["title"], payload, relations, **form.responsibility())
            messages.success(request, "Brouillon enregistré. La version publiée reste inchangée.")
            return redirect("knowledge-preview" if request.POST.get("intent") == "preview" else "knowledge-edit", record_id=record.pk)
        except ValidationError as error:
            errors_to_form(form, error)
        except services.Conflict as error:
            form.add_error(None, error.message)
            return edit_response(request, record, form, status=409, conflict=True)
    return edit_response(request, record, form, status=422)


@require_POST
def begin(request, record_id):
    form, record = VersionForm(request.POST), admin_record(record_id)
    if form.is_valid():
        try:
            services.begin_edit(request.user.pk, record_id, form.cleaned_data["expected_version"])
            return redirect("knowledge-edit", record_id=record_id)
        except services.Conflict as error:
            return edit_response(request, record, status=409, publication_errors=[error.message])
    return edit_response(request, record, status=422, publication_errors=["Rechargez la page avant de réessayer."])


@require_POST
def publish(request, record_id):
    record, form = admin_record(record_id), VersionForm(request.POST)
    if form.is_valid():
        try:
            services.publish(request.user.pk, record_id, form.cleaned_data["expected_version"])
            messages.success(request, "Une nouvelle version complète est publiée.")
            return redirect("knowledge-edit", record_id=record_id)
        except ValidationError as error:
            return edit_response(request, record, status=422, publication_errors=error.messages)
        except services.Conflict as error:
            return edit_response(request, record, status=409, publication_errors=[error.message])
    return edit_response(request, record, status=422, publication_errors=["Rechargez la page avant de publier."])


@require_safe
def preview(request, record_id):
    record = admin_record(record_id)
    if not hasattr(record, "draft"):
        raise Http404
    draft = record.draft
    _, payload, html, text, sections = normalise(record.kind, draft.title, draft.payload)
    context = record_context(record)
    context.update({"revision": {"title": draft.title or "Sans titre", "payload": payload, "body_html": html, "plain_text": text, "author": draft.updated_by, "responsible": draft.responsible}, "is_preview": True, "sections": [row for row in sections if row["id"]], "links": reader_links(record, draft)})
    progress = {Kind.EPIC: EpicProgress, Kind.STORY: StoryProgress, Kind.SPRINT: SprintProgress}.get(record.kind)
    if progress:
        context["revision"]["progress_label"] = dict(progress.choices).get(payload.get("sprint_state" if record.kind == Kind.SPRINT else "work_state"), "")
        context["revision"]["priority_label"] = dict(Priority.choices).get(payload.get("priority"), "")
    if record.kind == Kind.DOCUMENT:
        from documents.projections import document_context
        context.update(document_context(record, draft, request.GET, "draft"))
    return render(request, "knowledge/detail.html", context)


@require_safe
def history(request, record_id, number=None):
    record = admin_record(record_id)
    revisions = record.revisions.select_related("author").order_by("-number")
    revision = get_object_or_404(revisions, number=number) if number else None
    context = record_context(record)
    context.update({"revisions": revisions, "revision": revision, "historical_relations": revision.relations.all() if revision else []})
    if record.kind == Kind.SPRINT and hasattr(record, "closure") and (not revision or revision.number >= record.closure.closed_revision.number):
        from sprints.projections import sprint_context
        context.update(sprint_context(record, {}, admin=True))
    if record.kind == Kind.DOCUMENT and revision:
        from documents.projections import document_context
        context.update(document_context(record, revision, request.GET, "history"))
    return render(request, "knowledge/history.html", context)


@require_http_methods(["GET", "POST"])
def restore(request, record_id, number):
    record = admin_record(record_id)
    revision = get_object_or_404(record.revisions, number=number)
    form = RestoreForm(request.POST if request.method == "POST" else None, initial={"expected_version": record.edit_version})
    status = 422 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            services.restore_to_draft(request.user.pk, record_id, number, **form.cleaned_data)
            messages.success(request, "Version restaurée en brouillon. La publication actuelle reste inchangée.")
            return redirect("knowledge-edit", record_id=record_id)
        except services.Conflict as error:
            form.add_error(None, error.message)
            status = 409
        except ValidationError as error:
            form.add_error(None, error)
    context = record_context(record)
    context.update({"form": form, "action_title": f"Restaurer la version {revision.number}", "action_description": "Cette version sera copiée dans un brouillon. Les lecteurs conserveront la version actuellement publiée ; un contenu archivé restera invisible.", "has_draft": hasattr(record, "draft"), "restore_action": True})
    return render(request, "knowledge/action.html", context, status=status)


@require_http_methods(["GET", "POST"])
def archive_or_discard(request, record_id, operation):
    record = admin_record(record_id)
    form = ConfirmForm(request.POST if request.method == "POST" else None, initial={"expected_version": record.edit_version})
    archiving = operation == "archive"
    status = 422 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            if archiving:
                services.archive(request.user.pk, record_id, form.cleaned_data["expected_version"])
            else:
                services.discard_draft(request.user.pk, record_id, form.cleaned_data["expected_version"])
            messages.success(request, "Contenu archivé." if archiving else "Brouillon abandonné. Les versions publiées sont conservées.")
            return redirect("knowledge-admin")
        except services.Conflict as error:
            form.add_error(None, error.message)
            status = 409
        except ValidationError as error:
            form.add_error(None, error)
            status = 422
    context = record_context(record)
    context.update({"form": form, "action_title": "Archiver le contenu" if archiving else "Abandonner le brouillon", "action_description": "Le contenu sera retiré des vues lecteur. Son historique et son éventuel brouillon seront conservés." if archiving else "La saisie du brouillon sera retirée. Une version déjà publiée restera disponible. Un contenu jamais publié doit être sans lien entrant pour être abandonné.", "dependents": services.required_dependents(record).select_related("revision") if archiving else []})
    return render(request, "knowledge/action.html", context, status=status)


@require_http_methods(["GET", "POST"])
def import_directory(request):
    upload, confirmation, rows, status = ImportUpload(), None, None, 200
    receipt = ApplicationImport.objects.prefetch_related("rows").filter(pk=1).first()
    if request.method == "POST" and request.POST.get("intent") == "apply":
        confirmation = ImportConfirm(request.POST)
        if confirmation.is_valid():
            try:
                report = signing.loads(confirmation.cleaned_data["report"], salt="knowledge.import", max_age=1800)
                receipt, created = importing.import_applications(request.user.pk, report["rows"], report["digest"])
                messages.success(request, "Import terminé. Les nouveaux brouillons attendent votre publication." if created else "L’import a déjà été effectué. Aucun contenu n’a été écrasé.")
                return redirect("knowledge-import")
            except (signing.BadSignature, KeyError, TypeError):
                confirmation.add_error(None, "Le rapport a expiré ou est invalide. Recommencez la prévisualisation.")
            except ValidationError as error:
                confirmation.add_error(None, error.messages)
        status = 422
    elif request.method == "POST":
        upload = ImportUpload(request.POST, request.FILES)
        if upload.is_valid():
            try:
                source_rows, digest = importing.parse_csv(upload.cleaned_data["source"].read(65537))
                rows = importing.preview_rows(source_rows)
                confirmation = ImportConfirm(initial={"report": signing.dumps({"rows": source_rows, "digest": digest}, salt="knowledge.import", compress=True)})
            except ValidationError as error:
                upload.add_error("source", error.messages)
                status = 422
        else:
            status = 422
    return render(request, "knowledge/import.html", {"page_title": "Import des applications", "page_section": "knowledge", "upload": upload, "confirmation": confirmation, "rows": rows, "receipt": receipt}, status=status)
