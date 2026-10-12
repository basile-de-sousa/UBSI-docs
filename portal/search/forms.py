from django import forms
from knowledge.models import Kind, Relation
from knowledge.projections import published_records


class QuestionForm(forms.Form):
    question = forms.CharField(label="Votre question", max_length=500, strip=True, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Ex. Comment reprendre une ancienne version de spécification ?", "autocomplete": "off"}))

    def clean_question(self):
        value = self.cleaned_data["question"]
        try:
            value.encode("utf-8")
        except UnicodeError:
            raise forms.ValidationError("La question contient un caractère invalide.") from None
        if any(ord(char) < 32 and char not in "\n\t\r" for char in value):
            raise forms.ValidationError("Saisissez une question sans caractère de contrôle.")
        return value


class SearchForm(forms.Form):
    q = forms.CharField(label="Termes recherchés", max_length=200, required=False, widget=forms.TextInput(attrs={"placeholder": "Un sujet, un mot ou une référence…"}))
    kind = forms.ChoiceField(label="Type de contenu", choices=[("", "Tous les contenus"), *Kind.choices], required=False)
    application = forms.ModelChoiceField(label="Application", queryset=published_records().none(), required=False, empty_label="Toutes les applications")
    epic = forms.ModelChoiceField(label="Epic", queryset=published_records().none(), required=False, empty_label="Tous les epics")
    sprint = forms.ModelChoiceField(label="Sprint actuel", queryset=published_records().none(), required=False, empty_label="Tous les sprints")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field, kind in (("application", Kind.APPLICATION), ("epic", Kind.EPIC), ("sprint", Kind.SPRINT)):
            self.fields[field].queryset = published_records().filter(kind=kind).order_by("current_revision__title")
            self.fields[field].label_from_instance = lambda row: f"{row.display_reference} — {row.current_revision.title}"


def related_filter(queryset, kind, target):
    # Stories' current sprint relation is the shared published assignment.
    return queryset.filter(current_revision__relations__kind=kind, current_revision__relations__target=target).distinct()
