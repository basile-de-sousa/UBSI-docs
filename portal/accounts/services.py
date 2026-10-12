"""Account writes are explicit transactions; SMTP failures never activate accounts."""
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import EmailMessage, get_connection
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .models import AccountControl, Invitation, User, UserManager
from .tokens import invitation_digest, invitation_valid, reset_tokens

logger = logging.getLogger(__name__)


class AccountError(Exception):
    def __init__(self, message, status=409):
        self.message = message
        self.status = status


class MailUnavailable(AccountError):
    def __init__(self):
        super().__init__("L’email n’a pas pu être envoyé. Vérifiez le service d’envoi puis réessayez.", 503)


def lock_directory():
    # Seeded by migration; the shared lock also protects bootstrap against races.
    return AccountControl.objects.select_for_update().get(pk=1)


def locked_admin(actor_id):
    lock_directory()
    actor = User.objects.select_for_update().filter(pk=actor_id, is_active=True, role=User.Role.ADMIN).first()
    if not actor:
        raise PermissionDenied
    return actor


def mail_connection():
    if not settings.EMAIL_HOST or not settings.DEFAULT_FROM_EMAIL:
        raise MailUnavailable
    return get_connection(fail_silently=False)


@sensitive_variables("body")
def deliver(subject, body, email, connection=None):
    try:
        if connection is None:
            connection = mail_connection()
        sent = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [email], connection=connection).send()
        if sent != 1:
            raise MailUnavailable
    except Exception:
        # SMTP exception strings may contain recipients, credentials or message content.
        logger.warning("accounts.mail_delivery_failed")
        raise MailUnavailable from None


@transaction.atomic
@sensitive_variables("password")
def bootstrap_admin(email, display_name, password):
    lock_directory()
    if User.objects.exists():
        raise AccountError("L’annuaire contient déjà un compte. Le bootstrap est réservé au premier administrateur.")
    user = User(email=UserManager.normalize_email(email), display_name=display_name, role=User.Role.ADMIN)
    validate_password(password, user)
    user.set_password(password)
    user.full_clean()
    user.save()
    return user


@transaction.atomic
@sensitive_variables("token", "url", "body")
def invite(actor_id, email, role):
    actor = locked_admin(actor_id)
    email = UserManager.normalize_email(email)
    if User.objects.filter(email=email).exists():
        raise AccountError("Ce compte existe déjà. Gérez ses accès depuis la liste des membres.")
    invitation = Invitation.objects.select_for_update().filter(email=email).first()
    if invitation and invitation.consumed_at:
        raise AccountError("Cette invitation a déjà été utilisée.")
    now = timezone.now()
    token = secrets.token_urlsafe(32)
    if not invitation:
        invitation = Invitation(email=email, invited_by=actor)
    invitation.role = role
    invitation.invited_by = actor
    invitation.token_digest = invitation_digest(token)
    invitation.sent_at = now
    invitation.expires_at = now + timedelta(hours=settings.INVITATION_HOURS)
    invitation.full_clean()
    invitation.save()
    url = settings.PUBLIC_BASE_URL + reverse("invitation-exchange", args=[invitation.pk, token])
    body = (
        "Bonjour,\n\nVous êtes invité à rejoindre le portail privé UBSI.\n"
        f"Choisissez votre nom affiché et votre mot de passe :\n{url}\n\n"
        f"Ce lien est personnel, utilisable une seule fois et valable {settings.INVITATION_HOURS} heures.\n"
        "Si vous n’attendiez pas cette invitation, ignorez ce message.\n\nLes urbanistes UBSI\n"
    )
    # A failed synchronous delivery rolls back the draft invitation/token replacement.
    deliver("Votre invitation au portail UBSI", body, email)
    logger.info("accounts.invitation_sent")
    return invitation


@transaction.atomic
@sensitive_variables("digest", "password")
def accept_invitation(invitation_id, digest, display_name, password):
    lock_directory()
    invitation = Invitation.objects.select_for_update().filter(pk=invitation_id).first()
    if not invitation_valid(invitation, digest):
        raise AccountError("Ce lien a expiré, a déjà été utilisé ou a été remplacé. Demandez une nouvelle invitation.", 400)
    if User.objects.filter(email=invitation.email).exists():
        raise AccountError("Un compte existe déjà pour cette invitation.")
    user = User(email=invitation.email, display_name=display_name, role=invitation.role)
    validate_password(password, user)
    user.set_password(password)
    user.full_clean()
    user.save()
    invitation.consumed_at = timezone.now()
    invitation.save(update_fields=["consumed_at"])
    logger.info("accounts.invitation_accepted")
    return user


@transaction.atomic
def update_access(actor_id, target_id, role, is_active, expected_version):
    locked_admin(actor_id)
    user = User.objects.select_for_update().get(pk=target_id)
    if user.management_version != expected_version:
        raise AccountError("Ce compte a été modifié entre-temps. Rechargez la liste avant de réessayer.")
    withdrawing_admin = user.is_active and user.role == User.Role.ADMIN and (not is_active or role != User.Role.ADMIN)
    if withdrawing_admin and User.objects.filter(is_active=True, role=User.Role.ADMIN).count() <= 1:
        raise AccountError("Le dernier administrateur actif doit conserver ses accès.")
    if user.is_active and not is_active:
        user.access_version += 1
    user.role = role
    user.is_active = is_active
    if role != User.Role.ADMIN:
        user.is_staff = False
        user.is_superuser = False
    user.management_version += 1
    user.full_clean()
    user.save()
    logger.info("accounts.access_updated")
    return user


@sensitive_variables("token", "url", "body")
def request_recovery(email):
    # Open the same transport even for an unknown email. Connectivity errors use
    # the same public response for every address; recipient-specific failures don't.
    try:
        backend = mail_connection()
        backend.open()
    except Exception:
        logger.warning("accounts.mail_transport_unavailable")
        raise MailUnavailable from None
    try:
        user = User.objects.filter(email=UserManager.normalize_email(email), is_active=True).first()
        if not user or not user.has_usable_password():
            return
        token = reset_tokens.make_token(user)
        url = settings.PUBLIC_BASE_URL + reverse("reset-exchange", args=[user.pk, token])
        body = (
            "Bonjour,\n\nUne récupération de mot de passe a été demandée pour votre compte UBSI.\n"
            f"Choisissez un nouveau mot de passe :\n{url}\n\n"
            "Ce lien est personnel, à usage unique et valable une heure.\n"
            "Si vous n’êtes pas à l’origine de cette demande, ignorez ce message.\n"
        )
        try:
            deliver("Récupération de votre accès UBSI", body, user.email, backend)
            User.objects.filter(pk=user.pk).update(recovery_failure_at=None)
        except MailUnavailable:
            User.objects.filter(pk=user.pk).update(recovery_failure_at=timezone.now())
    finally:
        try:
            backend.close()
        except Exception:
            logger.warning("accounts.mail_close_failed")


@transaction.atomic
@sensitive_variables("token", "password")
def reset_password(user_id, token, password):
    lock_directory()
    user = User.objects.select_for_update().filter(pk=user_id, is_active=True).first()
    if not user or not reset_tokens.check_token(user, token):
        raise AccountError("Ce lien de récupération n’est plus valide. Faites une nouvelle demande.", 400)
    validate_password(password, user)
    user.set_password(password)
    user.save(update_fields=["password"])
    logger.info("accounts.password_reset")
    return user
