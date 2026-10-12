import json
from uuid import uuid4

from django import forms
from django.db.models import Q
from accounts.models import User

from .editor import specification_template, validate_document
from .models import ContentRecord, EpicProgress, Kind, Priority, SprintProgress, State, StoryProgress
from .schema import PAYLOAD_FIELDS, RELATIONS, application_code


class RecordChoices(forms.ModelMultipleChoiceField):
    def label_from_instance(self, record):
        return f"{record.display_reference} — {record.admin_title} ({record.get_state_display()})"


class RecordChoice(forms.ModelChoiceField):
    def label_from_instance(self, record):
        return f"{record.display_reference} — {record.admin_title} ({record.get_state_display()})"


class MemberChoice(forms.ModelChoiceField):
    def label_from_instance(self, member):
        return member.display_name + (" (désactivé)" if not member.is_active else "")


class ContentForm(forms.Form):
    creation_id = forms.UUIDField(widget=forms.HiddenInput, required=False)
    expected_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    title = forms.CharField(label="Titre", max_length=200, required=False)

    def __init__(self, kind, *args, record=None, **kwargs):
        initial = kwargs.setdefault("initial", {})
        payload = {}
        if record:
            initial["expected_version"] = record.edit_version
            if hasattr(record, "draft"):
                initial["title"] = record.draft.title
                payload = record.draft.payload
                for link in record.draft.relations.all():
                    initial.setdefault(link.kind, []).append(link.target_id)
        else:
            initial.setdefault("creation_id", uuid4())
            initial["expected_version"] = 0
        initial.update(payload)
        if kind == Kind.SPECIFICATION:
            initial["body"] = json.dumps(payload.get("body", specification_template()), ensure_ascii=False)
        if kind == Kind.FAQ:
            initial["aliases"] = "\n".join(payload.get("aliases", []))
        if kind == Kind.STORY:
            initial["criteria"] = "\n".join(payload.get("criteria", []))
        if kind in {Kind.EPIC, Kind.STORY, Kind.SPRINT}:
            initial["responsible"] = record.draft.responsible_id if record and hasattr(record, "draft") else None
            for key, value in {Kind.EPIC: {"work_state": EpicProgress.PLANNED}, Kind.STORY: {"work_state": StoryProgress.BACKLOG, "priority": Priority.NORMAL}, Kind.SPRINT: {"sprint_state": SprintProgress.PLANNED}}[kind].items():
                initial.setdefault(key, value)
        super().__init__(*args, **kwargs)
        self.kind = kind
        if not record:
            self.fields["creation_id"].required = True
        if kind == Kind.APPLICATION:
            self.fields.update({
                "code": forms.CharField(label="Code application", max_length=40, help_text="Code réservé dès la création. Les anciens codes publiés restent réservés après renommage."),
                "type": forms.CharField(label="Type", max_length=80, required=False, help_text="Par exemple : metier ou transverse."),
                "description": forms.CharField(label="Description", max_length=10000, required=False, widget=forms.Textarea(attrs={"rows": 5})),
            })
        elif kind == Kind.DOCUMENT:
            from documents.models import Category
            self.fields["category"] = forms.ChoiceField(label="Catégorie du document", choices=Category.choices)
            self.fields["description"] = forms.CharField(label="Description", max_length=10000, required=False, widget=forms.Textarea(attrs={"rows": 4}), help_text="Renseignez les métadonnées, puis importez le fichier dans le brouillon enregistré.")
        elif kind == Kind.SPECIFICATION:
            self.fields["body"] = forms.CharField(label="Texte de la spécification", max_length=1024 * 1024, required=False, widget=forms.HiddenInput)
        elif kind == Kind.FAQ:
            self.fields["title"].label = "Question"
            self.fields.update({
                "answer": forms.CharField(label="Réponse", max_length=200000, required=False, widget=forms.Textarea(attrs={"rows": 8})),
                "aliases": forms.CharField(label="Autres formulations", max_length=4200, required=False, widget=forms.Textarea(attrs={"rows": 3}), help_text="Une formulation par ligne, 20 maximum."),
                "category": forms.CharField(label="Catégorie", max_length=80, required=False),
            })
        elif kind in {Kind.EPIC, Kind.STORY, Kind.SPRINT}:
            labels = {"objective": "Objectif", "description": "Description", "scope": "Périmètre", "exclusions": "Hors périmètre", "acceptance_conditions": "Conditions d’acceptation", "actor": "En tant que", "need": "Je veux", "benefit": "Afin de", "context": "Contexte"}
            for key in PAYLOAD_FIELDS[kind] & labels.keys():
                self.fields[key] = forms.CharField(label=labels[key], required=False, max_length=10000, widget=forms.Textarea(attrs={"rows": 3}))
            for key, label in {Kind.EPIC: {"target_date": "Date cible"}, Kind.STORY: {}, Kind.SPRINT: {"start_date": "Date de début", "end_date": "Date de fin"}}[kind].items():
                self.fields[key] = forms.DateField(label=label, required=False, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"), input_formats=["%Y-%m-%d"])
            if kind == Kind.STORY:
                self.fields["criteria"] = forms.CharField(label="Critères d’acceptation", required=False, max_length=200100, widget=forms.Textarea(attrs={"rows": 5}), help_text="Un critère par ligne ; 100 critères de 2 000 caractères maximum.")
                self.fields["priority"] = forms.ChoiceField(label="Priorité", choices=Priority.choices)
            if kind != Kind.SPRINT:
                self.fields["work_state"] = forms.ChoiceField(label="Avancement", choices=(EpicProgress if kind == Kind.EPIC else StoryProgress).choices)
            else:
                self.fields["sprint_state"] = forms.ChoiceField(label="État du sprint", choices=SprintProgress.choices, disabled=True, help_text="Démarrer et Clôturer sont des actions de publication distinctes.")
            previous_owner = record.current_revision.responsible_id if record and record.current_revision_id else None
            draft_owner = initial.get("responsible")
            self.fields["responsible"] = MemberChoice(label="Responsable", required=False, queryset=User.objects.filter(Q(is_active=True) | Q(pk=previous_owner) | Q(pk=draft_owner)).order_by("display_name", "id"), empty_label="Non attribué", help_text="L’attribution ne change pas les droits du membre. Obligatoire pour publier un sprint et pour une story dans le sprint actif.")
        choices = ContentRecord.objects.filter(discarded_at__isnull=True).select_related("current_revision", "draft").order_by("reference")
        if record:
            choices = choices.exclude(pk=record.pk)
        labels = {"application": "Applications", "epic": "Epic parent" if kind == Kind.STORY else "Epics associés", "story": "User stories associées", "document": "Documents associés", "support": "Contenus associés", "specification": "Spécifications associées", "dependency": "Dépendances", "sprint": "Sprint courant"}
        for relation, target_kind in RELATIONS[kind].items():
            single = kind == Kind.STORY and relation in {"epic", "sprint"}
            if single and relation in initial:
                initial[relation] = initial[relation][0] if initial[relation] else None
            self.fields[relation] = (RecordChoice if single else RecordChoices)(label=labels[relation], queryset=choices.filter(kind=target_kind) if target_kind else choices, required=False, widget=forms.Select() if single else forms.SelectMultiple(attrs={"size": 5}), help_text="Les liens doivent viser des contenus publiés lors de la publication." if single else "Sélection multiple avec Ctrl/Cmd. Les liens doivent viser des contenus publiés lors de la publication.")
        if kind in {Kind.EPIC, Kind.STORY, Kind.SPRINT}:
            order = ["creation_id", "expected_version", "title", "objective", "description", "scope", "exclusions", "acceptance_conditions", "actor", "need", "benefit", "context", "criteria", "work_state", "priority", "responsible", "target_date", "start_date", "end_date", "sprint_state", *RELATIONS[kind]]
            self.order_fields(order)

    def clean_code(self):
        try:
            return application_code(self.cleaned_data["code"].strip().upper())
        except forms.ValidationError as error:
            raise forms.ValidationError(error.messages) from None

    def clean_body(self):
        return validate_document(self.cleaned_data.get("body") or {"type": "doc", "content": [{"type": "paragraph"}]}).json

    def clean_aliases(self):
        return [line.strip() for line in self.cleaned_data["aliases"].splitlines() if line.strip()]

    def clean_criteria(self):
        return [line.strip() for line in self.cleaned_data["criteria"].splitlines() if line.strip()]

    def responsibility(self):
        return {"responsible_id": self.cleaned_data["responsible"].pk if self.cleaned_data["responsible"] else None} if "responsible" in self.fields else {}

    def payload_and_relations(self):
        payload = {key: self.cleaned_data[key].isoformat() if key.endswith("_date") and self.cleaned_data[key] else "" if key.endswith("_date") else self.cleaned_data[key] for key in PAYLOAD_FIELDS[self.kind]}
        relations = {}
        for key in RELATIONS[self.kind]:
            value = self.cleaned_data[key]
            relations[key] = [value.pk] if isinstance(value, ContentRecord) else [] if value is None else [item.pk for item in value]
        return payload, relations


class VersionForm(forms.Form):
    expected_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)


class ConfirmForm(VersionForm):
    confirm = forms.BooleanField(label="Je confirme cette action.")


class RestoreForm(VersionForm):
    replace_draft = forms.BooleanField(label="Remplacer le brouillon existant par cette version.", required=False)


class ReaderFilters(forms.Form):
    q = forms.CharField(label="Rechercher", max_length=200, required=False, widget=forms.SearchInput(attrs={"placeholder": "Titre, texte, référence…"}))
    application = forms.ModelChoiceField(label="Application", queryset=ContentRecord.objects.none(), required=False, empty_label="Toutes les applications")
    category = forms.CharField(label="Catégorie FAQ", max_length=80, required=False)
    epic = forms.ModelChoiceField(label="Epic", queryset=ContentRecord.objects.none(), required=False, empty_label="Tous les epics")

    def __init__(self, *args, kind, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["application"].queryset = ContentRecord.objects.filter(kind=Kind.APPLICATION, state=State.PUBLISHED).select_related("current_revision").order_by("reference")
        self.fields["application"].label_from_instance = lambda row: f"{row.display_reference} — {row.current_revision.title}"
        if kind in {Kind.APPLICATION, Kind.SPRINT}:
            del self.fields["application"]
        if kind == Kind.DOCUMENT:
            from documents.models import Category
            self.fields["category"] = forms.ChoiceField(label="Catégorie", choices=[("", "Toutes les catégories"), *Category.choices], required=False)
        elif kind != Kind.FAQ:
            del self.fields["category"]
        if kind == Kind.STORY:
            self.fields["epic"].queryset = ContentRecord.objects.filter(kind=Kind.EPIC, state=State.PUBLISHED).select_related("current_revision").order_by("reference")
            self.fields["epic"].label_from_instance = lambda row: f"{row.reference} — {row.current_revision.title}"
            self.fields["priority"] = forms.ChoiceField(label="Priorité", choices=[("", "Toutes les priorités"), *Priority.choices], required=False)
        else:
            del self.fields["epic"]
        progress = {Kind.EPIC: EpicProgress, Kind.STORY: StoryProgress, Kind.SPRINT: SprintProgress}.get(kind)
        if progress:
            self.fields["progress"] = forms.ChoiceField(label="Avancement", choices=[("", "Tous les états"), *progress.choices], required=False)


class ImportUpload(forms.Form):
    source = forms.FileField(label="data/applications.csv", help_text="CSV UTF-8, colonnes code,nom,type,description ; 64 Kio maximum.", widget=forms.ClearableFileInput(attrs={"accept": ".csv,text/csv"}))

    def clean_source(self):
        source = self.cleaned_data["source"]
        if source.size > 65536:
            raise forms.ValidationError("Le fichier dépasse 64 Kio.")
        return source


class ImportConfirm(forms.Form):
    report = forms.CharField(max_length=150000, widget=forms.HiddenInput)
    confirm = forms.BooleanField(label="Créer les brouillons présentés ; conserver les applications déjà existantes.")
