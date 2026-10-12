from django import forms
from django.conf import settings

from knowledge.forms import VersionForm


class UploadForm(VersionForm):
    source = forms.FileField(label="Fichier original", widget=forms.FileInput(attrs={"accept": ".drawio,.xml,.xlsx,.csv,.puml,.plantuml,.pdf,.png,.jpg,.jpeg,.svg"}))
    delimiter = forms.ChoiceField(label="Séparateur CSV", choices=[("auto", "Détection automatique"), (";", "Point-virgule"), (",", "Virgule"), ("\t", "Tabulation")], initial="auto", help_text="UTF-8, avec ou sans BOM. En cas d’ambiguïté, réimportez avec le séparateur explicite.")

    def clean_source(self):
        source = self.cleaned_data["source"]
        if not source.size or source.size > settings.DOCUMENT_LIMITS["source_bytes"]:
            raise forms.ValidationError("Le fichier est vide ou dépasse la limite affichée.")
        return source
