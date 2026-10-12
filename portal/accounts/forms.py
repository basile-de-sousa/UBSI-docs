from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.core.validators import MaxLengthValidator

from .models import User, UserManager


class EmailForm(forms.Form):
    email = forms.EmailField(label="Adresse email", max_length=254, widget=forms.EmailInput(attrs={"autocomplete": "email", "autocapitalize": "none"}))

    def clean_email(self):
        return UserManager.normalize_email(self.cleaned_data["email"])


class SignInForm(EmailForm):
    password = forms.CharField(label="Mot de passe", max_length=1024, strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))


class InviteForm(EmailForm):
    role = forms.ChoiceField(label="Rôle", choices=User.Role.choices, initial=User.Role.USER)


class AccessForm(forms.Form):
    role = forms.ChoiceField(label="Rôle", choices=User.Role.choices)
    is_active = forms.BooleanField(label="Compte actif", required=False)
    expected_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)


class PasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        for name in ("new_password1", "new_password2"):
            self.fields[name].max_length = 1024
            self.fields[name].validators.append(MaxLengthValidator(1024))
            self.fields[name].widget.attrs["maxlength"] = 1024
        self.fields["new_password1"].label = "Mot de passe"
        self.fields["new_password2"].label = "Confirmer le mot de passe"


class AcceptInvitationForm(PasswordForm):
    display_name = forms.CharField(label="Nom affiché", max_length=120, widget=forms.TextInput(attrs={"autocomplete": "name"}))
    field_order = ["display_name", "new_password1", "new_password2"]

    def clean(self):
        # Include the chosen name in Django's password similarity validation.
        self.user.display_name = self.cleaned_data.get("display_name", "")
        return super().clean()
