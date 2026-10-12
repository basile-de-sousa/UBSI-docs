from django import forms

from knowledge.forms import ReaderFilters, VersionForm
from knowledge.models import Kind, StoryProgress


class SprintMemberFilters(ReaderFilters):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, kind=Kind.STORY, **kwargs)
        for name in ["q", "priority", "progress"]:
            del self.fields[name]


class ActivateForm(VersionForm):
    confirm = forms.BooleanField(label="Démarrer le sprint et publier son nouvel état.")


class CloseForm(forms.Form):
    report = forms.CharField(max_length=200000, widget=forms.HiddenInput)
    confirm = forms.BooleanField(label="Publier la clôture, l’instantané et toutes les nouvelles affectations présentées.")

    def __init__(self, *args, members, targets, **kwargs):
        super().__init__(*args, **kwargs)
        for story in members:
            if story.current_revision.payload["work_state"] not in {StoryProgress.DONE, StoryProgress.CANCELLED}:
                self.fields[f"story_{story.pk}"] = forms.ChoiceField(label=f"{story.reference} — {story.current_revision.title}", choices=[("", "Choisir une décision…"), ("backlog", "Retour au backlog — retirer l’affectation et passer en backlog"), *[(str(sprint.pk), f"Reporter vers {sprint.reference} — {sprint.current_revision.title} (avancement conservé)") for sprint in targets]])
        self.order_fields(["report", *[key for key in self.fields if key.startswith("story_")], "confirm"])

    def decisions(self):
        return {key.removeprefix("story_"): value for key, value in self.cleaned_data.items() if key.startswith("story_")}
