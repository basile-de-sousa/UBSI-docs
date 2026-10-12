import re
from datetime import date

from django.core.exceptions import ValidationError

from .editor import validate_document
from .models import EpicProgress, Kind, Priority, Relation, SprintProgress, StoryProgress

EDITABLE_KINDS = [Kind.APPLICATION, Kind.EPIC, Kind.STORY, Kind.SPRINT, Kind.SPECIFICATION, Kind.FAQ, Kind.DOCUMENT]
RELATIONS = {
    Kind.APPLICATION: {},
    Kind.DOCUMENT: {Relation.APPLICATION: Kind.APPLICATION, Relation.EPIC: Kind.EPIC, Relation.STORY: Kind.STORY, Relation.SPECIFICATION: Kind.SPECIFICATION},
    Kind.SPECIFICATION: {Relation.APPLICATION: Kind.APPLICATION, Relation.EPIC: Kind.EPIC, Relation.STORY: Kind.STORY, Relation.DOCUMENT: Kind.DOCUMENT},
    Kind.FAQ: {Relation.APPLICATION: Kind.APPLICATION, Relation.SUPPORT: None},
    Kind.EPIC: {Relation.APPLICATION: Kind.APPLICATION, Relation.SPECIFICATION: Kind.SPECIFICATION, Relation.DOCUMENT: Kind.DOCUMENT},
    Kind.STORY: {Relation.APPLICATION: Kind.APPLICATION, Relation.EPIC: Kind.EPIC, Relation.DEPENDENCY: Kind.STORY, Relation.SPRINT: Kind.SPRINT, Relation.SPECIFICATION: Kind.SPECIFICATION, Relation.DOCUMENT: Kind.DOCUMENT},
    Kind.SPRINT: {},
}

PAYLOAD_FIELDS = {
    Kind.APPLICATION: {"code", "type", "description"},
    Kind.DOCUMENT: {"category", "description"},
    Kind.SPECIFICATION: {"body"},
    Kind.FAQ: {"answer", "aliases", "category"},
    Kind.EPIC: {"objective", "description", "scope", "exclusions", "acceptance_conditions", "target_date", "work_state"},
    Kind.STORY: {"actor", "need", "benefit", "context", "criteria", "priority", "work_state"},
    Kind.SPRINT: {"objective", "start_date", "end_date", "sprint_state"},
}


def backlog_payload(kind, result, payload, title, publishing):
    errors = {}
    if kind == Kind.STORY:
        criteria = payload.get("criteria", [])
        if not isinstance(criteria, list) or len(criteria) > 100 or any(not isinstance(item, str) or len(item) > 2000 or "\x00" in item for item in criteria):
            errors["criteria"] = "Saisissez au plus 100 critères de 2 000 caractères."
        else:
            result["criteria"] = [item.strip() for item in criteria if item.strip()]
            if publishing and not result["criteria"]:
                errors["criteria"] = "Ajoutez au moins un critère d’acceptation."
    choices = {Kind.EPIC: ("work_state", EpicProgress, EpicProgress.PLANNED), Kind.STORY: ("work_state", StoryProgress, StoryProgress.BACKLOG), Kind.SPRINT: ("sprint_state", SprintProgress, SprintProgress.PLANNED)}
    key, enum, default = choices[kind]
    result[key] = result.get(key) or default
    if result[key] not in enum.values:
        errors[key] = "Sélectionnez un état autorisé."
    if kind == Kind.STORY:
        result["priority"] = result.get("priority") or Priority.NORMAL
        if result["priority"] not in Priority.values:
            errors["priority"] = "Sélectionnez une priorité autorisée."
    for key in {Kind.EPIC: ["target_date"], Kind.STORY: [], Kind.SPRINT: ["start_date", "end_date"]}[kind]:
        if result[key]:
            try:
                result[key] = date.fromisoformat(result[key]).isoformat()
            except ValueError:
                errors[key] = "Saisissez une date valide."
        elif publishing and kind == Kind.SPRINT:
            errors[key] = "Cette date est obligatoire pour publier."
    if kind == Kind.SPRINT and not errors and result["start_date"] and result["end_date"] and result["end_date"] < result["start_date"]:
        errors["end_date"] = "La date de fin doit suivre ou égaler la date de début."
    required = {Kind.EPIC: {"objective": "objectif", "description": "description", "scope": "périmètre"}, Kind.STORY: {"actor": "acteur", "need": "besoin", "benefit": "bénéfice attendu"}, Kind.SPRINT: {"objective": "objectif"}}[kind]
    for key, label in required.items():
        if publishing and not result[key]:
            errors[key] = f"Renseignez le champ {label} avant publication."
    if errors:
        raise ValidationError(errors)
    text_fields = {Kind.EPIC: ["objective", "description", "scope", "exclusions", "acceptance_conditions"], Kind.STORY: ["actor", "need", "benefit", "context"], Kind.SPRINT: ["objective"]}[kind]
    text = "\n\n".join(result[key] for key in text_fields if result[key])
    if kind == Kind.STORY:
        text += "\n\n" + "\n".join(result["criteria"])
    return text, [{"id": "", "title": title, "text": text}]


def application_code(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z][A-Z0-9_-]{1,39}", value):
        raise ValidationError({"code": "Utilisez 2 à 40 caractères : lettres majuscules, chiffres, tirets ou underscores."})
    return value


def normalise(kind, title, payload, publishing=False):
    if kind not in EDITABLE_KINDS:
        raise ValidationError("Les parcours de ce type de contenu seront disponibles au jalon suivant.")
    if not isinstance(title, str) or len(title) > 200 or "\x00" in title or not isinstance(payload, dict):
        raise ValidationError("Le titre ou les champs sont invalides.")
    title = title.strip()
    fields = PAYLOAD_FIELDS[kind]
    if set(payload) - fields:
        raise ValidationError("Un champ non autorisé a été transmis.")
    result, html, text, sections = {}, "", "", []
    errors = {}
    if publishing and not title:
        errors["title"] = "Renseignez le titre ou la question avant publication."
    for key in fields - {"body", "aliases", "criteria"}:
        value = payload.get(key, "")
        limit = 80 if key in {"type", "category"} else (40 if key == "code" else 200000 if key == "answer" else 10000)
        if not isinstance(value, str) or len(value) > limit or "\x00" in value:
            errors[key] = f"Ce champ doit être un texte de {limit} caractères maximum."
        else:
            result[key] = value.strip()
    if errors:
        raise ValidationError(errors)
    if kind == Kind.APPLICATION:
        result["code"] = application_code(result["code"])
        text = result["description"]
        if publishing and not text:
            errors["description"] = "La description est obligatoire pour publier."
    elif kind == Kind.DOCUMENT:
        from documents.models import Category
        if result["category"] not in Category.values:
            errors["category"] = "Sélectionnez une catégorie de document."
        text = result["description"]
        if publishing and not text:
            errors["description"] = "Renseignez la description avant publication."
    elif kind == Kind.FAQ:
        aliases = payload.get("aliases", [])
        if not isinstance(aliases, list) or len(aliases) > 20 or any(not isinstance(alias, str) or len(alias) > 200 or "\x00" in alias for alias in aliases):
            errors["aliases"] = "Saisissez au plus 20 formulations de 200 caractères."
        else:
            result["aliases"] = list(dict.fromkeys(alias.strip() for alias in aliases if alias.strip()))
        text = result["answer"]
        sections = [{"id": "", "title": title, "text": text}]
        if publishing and not text:
            errors["answer"] = "La réponse est obligatoire pour publier."
    elif kind in {Kind.EPIC, Kind.STORY, Kind.SPRINT}:
        text, sections = backlog_payload(kind, result, payload, title, publishing)
    else:
        try:
            document = validate_document(payload.get("body", {"type": "doc", "content": [{"type": "paragraph"}]}))
            result["body"], html, text, sections = document.json, document.html, document.text, document.sections
            def has_text(node):
                return bool(node.get("text", "").strip()) or any(has_text(child) for child in node.get("content", []))
            meaningful = any(has_text(node) for node in document.json.get("content", []) if node["type"] != "heading")
            if publishing and (not text.strip() or not meaningful):
                errors["body"] = "Ajoutez un texte de spécification avant publication."
        except ValidationError as error:
            errors["body"] = error.messages
    if errors:
        raise ValidationError(errors)
    return title, result, html, text, sections
