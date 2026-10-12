from django.contrib.auth.backends import ModelBackend

from .models import UserManager


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username if username is not None else kwargs.get("email")
        if email is not None:
            email = UserManager.normalize_email(email)
        return super().authenticate(request, username=email, password=password)
