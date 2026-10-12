from uuid import UUID
from urllib.parse import urlsplit

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from . import rates, services
from .forms import AcceptInvitationForm, AccessForm, EmailForm, InviteForm, PasswordForm, SignInForm
from .models import Invitation, User
from .tokens import invitation_digest, invitation_valid, reset_tokens

INVITATION_SESSION = "invitation_claim"
RESET_SESSION = "password_reset_claim"


def throttled(request, error):
    response = render(request, "accounts/notice.html", {
        "heading": "Veuillez patienter", "description": "Trop de tentatives ont été effectuées. Réessayez après le délai indiqué.",
        "retry_after": error.retry_after,
    }, status=429)
    response.headers["Retry-After"] = str(error.retry_after)
    return response


def invalid_link(request, invitation=False):
    return render(request, "accounts/notice.html", {
        "heading": "Ce lien n’est plus valide",
        "description": "Le lien a expiré, a déjà été utilisé ou a été remplacé. " + (
            "Demandez une nouvelle invitation à un administrateur." if invitation else "Faites une nouvelle demande de récupération."
        ),
        "recovery_link": not invitation,
    }, status=400)


def success_url(request):
    target = request.POST.get("next", request.GET.get("next", ""))
    if target and url_has_allowed_host_and_scheme(target, {request.get_host()}, require_https=request.is_secure()):
        path = urlsplit(target).path
        if path and path != "/" and not path.startswith("/auth/"):
            return target
    return "/applications/"


@login_not_required
@sensitive_post_parameters("password")
@require_http_methods(["GET", "POST"])
def sign_in(request):
    if request.user.is_authenticated:
        return redirect(success_url(request))
    form = SignInForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        try:
            rates.source(request, "login")
            if form.is_valid():
                rates.account("login", form.cleaned_data["email"])
                user = authenticate(request, username=form.cleaned_data["email"], password=form.cleaned_data["password"])
                if user:
                    login(request, user)
                    request.session["account_access_version"] = user.access_version
                    return redirect(success_url(request))
                form.add_error(None, "Adresse email ou mot de passe incorrect. Vérifiez également que votre compte est actif.")
        except rates.Throttled as error:
            return throttled(request, error)
    return render(request, "accounts/login.html", {"form": form, "next": request.GET.get("next", request.POST.get("next", ""))})


@require_POST
def sign_out(request):
    logout(request)
    messages.success(request, "Vous êtes déconnecté.")
    return redirect("login")


@login_not_required
@sensitive_variables("token", "digest")
@require_safe
def invitation_exchange(request, invitation_id, token):
    try:
        rates.source(request, "proof")
    except rates.Throttled as error:
        return throttled(request, error)
    invitation = Invitation.objects.filter(pk=invitation_id).first()
    digest = invitation_digest(token) if len(token) <= 128 else ""
    if not invitation_valid(invitation, digest):
        return invalid_link(request, invitation=True)
    request.session.cycle_key()
    request.session[INVITATION_SESSION] = {"id": str(invitation.pk), "digest": digest}
    return redirect("invitation-accept")


def session_invitation(request):
    state = request.session.get(INVITATION_SESSION, {})
    try:
        invitation_id = UUID(state["id"])
        digest = state["digest"]
    except (ValueError, KeyError, TypeError, AttributeError):
        return None, ""
    invitation = Invitation.objects.filter(pk=invitation_id).first()
    return (invitation, digest) if invitation_valid(invitation, digest) else (None, "")


@login_not_required
@sensitive_post_parameters("new_password1", "new_password2")
@require_http_methods(["GET", "POST"])
def invitation_accept(request):
    invitation, digest = session_invitation(request)
    if not invitation:
        return invalid_link(request, invitation=True)
    pending_user = User(email=invitation.email, role=invitation.role)
    form = AcceptInvitationForm(pending_user, request.POST if request.method == "POST" else None)
    status = 200
    if request.method == "POST":
        try:
            rates.source(request, "proof")
            rates.account("proof", str(invitation.pk))
            if form.is_valid():
                services.accept_invitation(invitation.pk, digest, form.cleaned_data["display_name"], form.cleaned_data["new_password1"])
                # Never retain another user's authenticated session during acceptance.
                logout(request)
                messages.success(request, "Votre compte est activé. Connectez-vous pour rejoindre le projet.")
                return redirect("login")
        except rates.Throttled as error:
            return throttled(request, error)
        except services.AccountError as error:
            form.add_error(None, error.message)
            status = error.status
        except ValidationError as error:
            form.add_error(None, error)
            status = 422
    return render(request, "accounts/accept.html", {"form": form, "invitation": invitation}, status=status)


@login_not_required
@require_http_methods(["GET", "POST"])
def recovery(request):
    form = EmailForm(request.POST if request.method == "POST" else None)
    status = 200
    if request.method == "POST":
        try:
            rates.source(request, "recovery")
            if form.is_valid():
                rates.account("recovery", form.cleaned_data["email"])
                services.request_recovery(form.cleaned_data["email"])
                return redirect("recovery-done")
        except rates.Throttled as error:
            return throttled(request, error)
        except services.MailUnavailable:
            form.add_error(None, "Le service d’envoi est momentanément indisponible. Réessayez plus tard ou contactez les urbanistes.")
            status = 503
    return render(request, "accounts/recovery.html", {"form": form}, status=status)


@login_not_required
@require_safe
def recovery_done(request):
    return render(request, "accounts/notice.html", {
        "heading": "Consultez votre messagerie",
        "description": "Si un compte actif correspond à cette adresse, un lien de récupération vous sera envoyé. Il est valable une heure. Si vous ne recevez rien, contactez les urbanistes.",
    })


@login_not_required
@sensitive_variables("token")
@require_safe
def reset_exchange(request, user_id, token):
    try:
        rates.source(request, "proof")
    except rates.Throttled as error:
        return throttled(request, error)
    user = User.objects.filter(pk=user_id, is_active=True).first()
    if len(token) > 128 or not user or not reset_tokens.check_token(user, token):
        return invalid_link(request)
    request.session.cycle_key()
    request.session[RESET_SESSION] = {"id": str(user.pk), "token": token}
    return redirect("reset-confirm")


def session_reset(request):
    state = request.session.get(RESET_SESSION, {})
    try:
        user_id, token = UUID(state["id"]), state["token"]
    except (ValueError, KeyError, TypeError, AttributeError):
        return None, ""
    user = User.objects.filter(pk=user_id, is_active=True).first()
    return (user, token) if user and reset_tokens.check_token(user, token) else (None, "")


@login_not_required
@sensitive_post_parameters("new_password1", "new_password2")
@require_http_methods(["GET", "POST"])
def reset_confirm(request):
    user, token = session_reset(request)
    if not user:
        return invalid_link(request)
    form = PasswordForm(user, request.POST if request.method == "POST" else None)
    status = 200
    if request.method == "POST":
        try:
            rates.source(request, "proof")
            rates.account("proof", str(user.pk))
            if form.is_valid():
                services.reset_password(user.pk, token, form.cleaned_data["new_password1"])
                logout(request)
                messages.success(request, "Votre mot de passe a été modifié. Reconnectez-vous avec le nouveau mot de passe.")
                return redirect("login")
        except rates.Throttled as error:
            return throttled(request, error)
        except services.AccountError as error:
            form.add_error(None, error.message)
            status = error.status
        except ValidationError as error:
            form.add_error(None, error)
            status = 422
    return render(request, "accounts/reset.html", {"form": form}, status=status)


def directory_response(request, invite_form=None, row_id=None, row_form=None, status=200):
    members = list(User.objects.order_by("display_name", "email"))
    for member in members:
        member.access_form = row_form if member.pk == row_id else AccessForm(initial={
            "role": member.role, "is_active": member.is_active, "expected_version": member.management_version,
        }, prefix=str(member.pk))
    return render(request, "accounts/directory.html", {
        "members": members, "invite_form": invite_form if invite_form is not None else InviteForm(),
        "invitations": Invitation.objects.filter(consumed_at__isnull=True).order_by("-sent_at"),
        "page_title": "Comptes", "page_section": "accounts",
        "active_count": sum(member.is_active for member in members),
    }, status=status)


@require_safe
def directory(request):
    return directory_response(request)


@require_POST
def send_invitation(request):
    form = InviteForm(request.POST)
    try:
        rates.source(request, "manage")
        rates.account("manage", str(request.user.pk))
        if form.is_valid():
            services.invite(request.user.pk, form.cleaned_data["email"], form.cleaned_data["role"])
            messages.success(request, "Invitation envoyée. Le membre dispose de 72 heures pour activer son compte.")
            return redirect("accounts")
    except rates.Throttled as error:
        return throttled(request, error)
    except services.AccountError as error:
        form.add_error(None, error.message)
        return directory_response(request, invite_form=form, status=error.status)
    return directory_response(request, invite_form=form, status=422)


@require_POST
def resend_invitation(request, invitation_id):
    invitation = Invitation.objects.filter(pk=invitation_id, consumed_at__isnull=True).first()
    if not invitation:
        raise Http404
    try:
        rates.source(request, "manage")
        rates.account("manage", str(request.user.pk))
        services.invite(request.user.pk, invitation.email, invitation.role)
        messages.success(request, "Invitation renvoyée. Le précédent lien a été remplacé.")
    except rates.Throttled as error:
        return throttled(request, error)
    except services.AccountError as error:
        form = InviteForm({"email": invitation.email, "role": invitation.role})
        form.is_valid()
        form.add_error(None, error.message)
        return directory_response(request, invite_form=form, status=error.status)
    return redirect("accounts")


@require_POST
def change_access(request, user_id):
    if not User.objects.filter(pk=user_id).exists():
        raise Http404
    form = AccessForm(request.POST, prefix=str(user_id))
    try:
        rates.source(request, "manage")
        rates.account("manage", str(request.user.pk))
        if form.is_valid():
            user = services.update_access(request.user.pk, user_id, **form.cleaned_data)
            if user.pk == request.user.pk:
                if not user.is_active:
                    logout(request)
                    messages.success(request, "Votre compte est désactivé. Vous êtes déconnecté.")
                    return redirect("login")
                if user.role != User.Role.ADMIN:
                    messages.success(request, "Vos droits ont été mis à jour. Vous disposez maintenant d’un accès utilisateur.")
                    return redirect("applications")
            messages.success(request, "Les accès du compte ont été mis à jour.")
            return redirect("accounts")
    except rates.Throttled as error:
        return throttled(request, error)
    except services.AccountError as error:
        form.add_error(None, error.message)
        return directory_response(request, row_id=user_id, row_form=form, status=error.status)
    return directory_response(request, row_id=user_id, row_form=form, status=422)
