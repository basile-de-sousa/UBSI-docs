import json

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core import signing
from django.core.exceptions import RequestDataTooBig
from django.core.paginator import Paginator
from django.db import DatabaseError, transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_safe
from accounts.middleware import api_endpoint
from accounts.models import User
from accounts.rates import Throttled, consume
from jobs.models import Job
from knowledge.models import ProjectState, Relation
from knowledge.projections import canonical_url, published_records
from .corpus import passages, records
from .forms import QuestionForm, SearchForm, related_filter
from .models import SemanticIndex
from .policy import Busy, INDEX_VERSION, InvalidQuestion, PENDING, POLICY, UNAVAILABLE, Unavailable, fingerprint, qualification
from .retrieval import answer


@require_safe
def directory(request):
    form = SearchForm(request.GET)
    valid = form.is_valid()
    rows = published_records()
    any_published = rows.exists()
    query = ""
    if valid:
        query = form.cleaned_data["q"]
        if form.cleaned_data["kind"]: rows = rows.filter(kind=form.cleaned_data["kind"])
        for field, relation in (("application", Relation.APPLICATION), ("epic", Relation.EPIC), ("sprint", Relation.SPRINT)):
            if form.cleaned_data[field]: rows = related_filter(rows, relation, form.cleaned_data[field])
        if query:
            vector = SearchVector("current_revision__title", weight="A", config="french") + SearchVector("current_revision__plain_text", weight="B", config="french")
            search_query = SearchQuery(query, search_type="websearch", config="french")
            rows = rows.annotate(search_vector=vector, rank=SearchRank(vector, search_query)).filter(Q(search_vector=search_query) | Q(reference__icontains=query) | Q(current_revision__payload__code__icontains=query) | Q(current_revision__payload__aliases__icontains=query)).order_by("-rank", "reference")
        else:
            rows = rows.order_by("current_revision__title", "id")
    else:
        rows = rows.none()
    page = Paginator(rows, 25).get_page(request.GET.get("page"))
    for row in page: row.reader_url = canonical_url(row)
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "search/results.html", {"page_title": "Recherche", "page_section": "search", "form": form, "page": page, "q": query, "filter_query": params.urlencode(), "any_published": any_published}, status=200 if valid else 422)


@require_safe
def assistant(request):
    return render(request, "search/assistant.html", {"page_title": "Assistant FAQ", "page_section": "assistant", "form": QuestionForm(), "qualified": qualification(), "query_url": reverse("assistant-query")})


@require_safe
def administration(request):
    current = records()
    ready = SemanticIndex.objects.filter(version=INDEX_VERSION, revision_id__in=current.values("current_revision_id")).count()
    jobs = Job.objects.filter(kind="semantic_index", revision_id__in=current.values("current_revision_id"))
    counts = {"records": current.count(), "passages": passages().count(), "ready": ready, "pending": jobs.filter(state__in=["pending", "running"]).count(), "failed": jobs.filter(state="failed").count()}
    return render(request, "search/admin.html", {"page_title": "Recherche & assistant", "page_section": "search-admin", "form": QuestionForm(), "counts": counts, "qualified": qualification(), "fingerprint": fingerprint(), "policy": POLICY, "query_url": reverse("assistant-preview-query")})


def error(message, status, kind="unavailable", retry=None):
    response = JsonResponse({"status": kind, "message": message, "sources": []}, status=status)
    if retry: response["Retry-After"] = str(retry)
    return response


@api_endpoint
@require_POST
def query(request, preview=False):
    if preview and request.user.role != User.Role.ADMIN:
        return error("Accès administrateur requis.", 403, "forbidden")
    # Read a small body only; invalid questions never consume an inference slot.
    try:
        if int(request.META.get("CONTENT_LENGTH") or 0) > 8192: raise ValueError
        if request.content_type == "application/json":
            if len(request.body) > 8192: raise ValueError
            data = json.loads(request.body)
            if not isinstance(data, dict) or set(data) != {"question"} or not isinstance(data["question"], str): raise ValueError
        else:
            data = request.POST
        form = QuestionForm(data)
        if not form.is_valid():
            return error("Saisissez une question de 1 à 500 caractères.", 422, "invalid")
    except (ValueError, UnicodeError, RequestDataTooBig, RecursionError):
        return error("La question transmise est invalide ou trop longue.", 422, "invalid")
    try:
        consume("assistant", str(request.user.pk), 20, 300)
        if not preview and not qualification():
            return error(PENDING, 503, "qualification_pending")
        result = answer(form.cleaned_data["question"])
        # Account/session revocation during inference also suppresses the answer.
        if not User.objects.filter(pk=request.user.pk, is_active=True, access_version=request.user.access_version, **({"role": User.Role.ADMIN} if preview else {})).exists():
            return error("Votre session a expiré. Veuillez vous reconnecter.", 401, "unauthenticated")
        if preview: result["experimental"] = True
        return JsonResponse(result)
    except Throttled as exc:
        return error("Trop de questions ont été envoyées. Patientez avant de réessayer.", 429, "rate_limited", exc.retry_after)
    except Busy:
        return error("L’assistant est occupé. Réessayez dans quelques instants.", 429, "busy", 3)
    except InvalidQuestion:
        return error("La question est trop longue pour le moteur. Raccourcissez-la.", 422, "invalid")
    except (Unavailable, DatabaseError, OSError):
        return error(UNAVAILABLE, 503, retry=5)
    except Exception:
        # Model/backend errors may include input tensors or source text. Neither
        # they nor the question belong in request diagnostics or the response.
        return error(UNAVAILABLE, 503, retry=5)


@require_safe
def source(request, token):
    try:
        data = signing.loads(token, salt="search.source", max_age=12 * 60 * 60)
        record = published_records().filter(pk=data["record"], current_revision_id=data["revision"]).first()
        if not record or not passages().filter(record=record, revision_id=data["revision"], section=data["section"]).exists(): raise ValueError
    except (signing.BadSignature, ValueError, KeyError, TypeError):
        raise Http404 from None
    url = canonical_url(record) + f'?source_revision={data["revision"]}'
    if data["section"]: url += f'&section={data["section"]}#section-{data["section"]}'
    return redirect(url)


@require_POST
def reindex(request):
    # Account role is guarded by the admin URL and middleware. Explicit retry
    # never publishes data or enables the candidate policy.
    from .indexing import queue_reindex
    queue_reindex(request.user)
    return redirect("search-admin")
