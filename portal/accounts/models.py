"""Stable business identity, independent of the current login provider."""
import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.functions import Lower, Trim
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        return super().normalize_email(email).strip().lower()

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email is required.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if not all(extra_fields.get(key) is True for key in ("is_staff", "is_superuser", "is_active")):
            raise ValueError("Superusers must be active staff with superuser privileges.")
        if extra_fields["role"] != User.Role.ADMIN:
            raise ValueError("Superusers must have the admin role.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        USER = "user", "Utilisateur"
        ADMIN = "admin", "Administrateur"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("Adresse email", unique=True)
    display_name = models.CharField("Nom affiché", max_length=120)
    role = models.CharField("Rôle", max_length=10, choices=Role.choices, default=Role.USER)
    is_active = models.BooleanField("Actif", default=True)
    is_staff = models.BooleanField("Accès technique", default=False)
    date_joined = models.DateTimeField("Créé le", default=timezone.now)
    access_version = models.PositiveIntegerField(default=1, editable=False)
    management_version = models.PositiveIntegerField(default=1, editable=False)
    recovery_failure_at = models.DateTimeField(null=True, blank=True, editable=False)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    class Meta:
        verbose_name = "Compte"
        verbose_name_plural = "Comptes"
        constraints = [
            models.UniqueConstraint(Lower("email"), name="accounts_user_email_case_unique"),
            models.CheckConstraint(condition=models.Q(email=Lower(Trim("email"))), name="accounts_user_email_normalized"),
            models.CheckConstraint(condition=models.Q(role__in=["user", "admin"]), name="accounts_user_valid_role"),
            models.CheckConstraint(condition=models.Q(is_superuser=False) | models.Q(role="admin"), name="accounts_superuser_is_admin"),
        ]

    def clean(self):
        super().clean()
        self.email = UserManager.normalize_email(self.email)
        self.display_name = self.display_name.strip()

    def save(self, *args, **kwargs):
        self.email = UserManager.normalize_email(self.email)
        return super().save(*args, **kwargs)

    def get_full_name(self):
        return self.display_name

    def get_short_name(self):
        return self.display_name

    def __str__(self):
        return self.display_name


class AccountControl(models.Model):
    """Serialize account lifecycle writes, including first/last administrator rules."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name="accounts_control_singleton")]


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=User.Role.choices)
    token_digest = models.CharField(max_length=64, editable=False)
    invited_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="invitations_sent")
    created_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(email=Lower(Trim("email"))), name="accounts_invite_email_normalized"),
            models.CheckConstraint(condition=models.Q(role__in=["user", "admin"]), name="accounts_invite_valid_role"),
        ]

    @property
    def expired(self):
        return self.expires_at <= timezone.now()


class RateBucket(models.Model):
    # HMAC key: no raw source address or submitted email is retained here.
    key = models.CharField(max_length=64, primary_key=True)
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)


class LoginIdentity(models.Model):
    """Future provider boundary; no OAuth endpoint or automatic linking exists."""
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="login_identities")
    provider = models.CharField(max_length=32)
    provider_subject = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "provider_subject"], name="accounts_identity_subject_unique"),
        ]
