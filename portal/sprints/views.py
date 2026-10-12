from django.contrib import messages
from django.core import signing
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from knowledge.models import Kind
from knowledge.services import Conflict
from knowledge.views import admin_record, record_context
from . import services
from .forms import ActivateForm, CloseForm


@require_http_methods(["GET", "POST"])
def activate(request, record_id):
    record = admin_record(record_id)
    if record.kind != Kind.SPRINT:
        raise Http404
    form = ActivateForm(request.POST if request.method == "POST" else None, initial={"expected_version": record.edit_version})
    status = 422 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            services.activate(request.user.pk, record_id, form.cleaned_data["expected_version"])
            messages.success(request, "Sprint démarré. Son état actif est publié.")
            return redirect("knowledge-edit", record_id=record_id)
        except ValidationError as error:
            form.add_error(None, error)
        except Conflict as error:
            form.add_error(None, error.message)
            status = 409
    return render(request, "sprints/activate.html", {**record_context(record), "form": form, "members": services.assigned_stories(record)}, status=status)


@require_http_methods(["GET", "POST"])
def close(request, record_id):
    record = admin_record(record_id)
    if record.kind != Kind.SPRINT:
        raise Http404
    members, targets = list(services.assigned_stories(record)), list(services.planned_sprints().exclude(pk=record.pk))
    form = CloseForm(request.POST if request.method == "POST" else None, members=members, targets=targets, initial={"report": signing.dumps(services.close_report(record), salt="sprints.close.v1", compress=True)})
    status = 422 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            report = signing.loads(form.cleaned_data["report"], salt="sprints.close.v1", max_age=1800)
            if report["sprint"] != str(record.pk):
                raise signing.BadSignature
            services.close(request.user.pk, report, form.decisions())
            messages.success(request, "Sprint clôturé. L’instantané et les affectations ont été publiés ensemble.")
            return redirect("sprint-detail", record_id=record.pk)
        except (signing.BadSignature, KeyError, TypeError):
            form.add_error(None, "Le bilan a expiré ou est invalide. Rechargez la clôture avant de confirmer.")
        except ValidationError as error:
            form.add_error(None, error)
        except Conflict as error:
            form.add_error(None, error.message)
            status = 409
    return render(request, "sprints/close.html", {**record_context(record), "form": form, "members": members}, status=status)
