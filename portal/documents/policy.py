"""Shared format contract; limits are passed to isolated preparation processes."""
from django.core.exceptions import ValidationError

from .models import Category

ADAPTER_VERSION = "m5.1"
FORMATS = {
    "drawio": ("drawio", "application/xml"), "xml": ("drawio", "application/xml"),
    "xlsx": ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    "csv": ("csv", "text/csv"), "puml": ("plantuml", "text/plain"), "plantuml": ("plantuml", "text/plain"),
    "pdf": ("pdf", "application/pdf"), "png": ("png", "image/png"), "jpg": ("jpeg", "image/jpeg"), "jpeg": ("jpeg", "image/jpeg"), "svg": ("svg", "image/svg+xml"),
}
ALLOWED = {Category.FLOW: {"drawio"}, Category.SPREADSHEET: {"xlsx", "csv"}, Category.DATABASE: {"drawio", "plantuml", "pdf", "png", "jpeg", "svg"}}
ERRORS = {
    "invalid": "Le contenu ne correspond pas au format attendu ou est endommagé. Exportez un fichier valide puis réimportez-le.",
    "unsafe": "Le fichier contient une ressource externe ou un élément actif non pris en charge. Intégrez les images localement, retirez les scripts/includes puis réimportez.",
    "limit": "Le fichier dépasse une limite de préparation. Réduisez sa complexité selon les limites affichées puis réimportez-le.",
    "csv": "CSV ambigu ou lignes incohérentes. Choisissez explicitement le séparateur lors du nouvel import, ou corrigez le fichier UTF-8.",
    "timeout": "La préparation a dépassé le délai autorisé. Simplifiez le fichier puis réimportez-le.",
    "renderer": "Le rendu local n’a pas abouti. Vérifiez la syntaxe et les formes prises en charge, puis réessayez ou réimportez une version corrigée.",
    "unavailable": "Le service de préparation ou le stockage est indisponible. Réessayez ; si le problème persiste, contactez un administrateur.",
    "adapter": "Cette version de préparation n’est plus disponible. Réimportez l’original pour utiliser l’adaptateur actuel.",
    "integrity": "Le fichier stocké ne correspond plus à son empreinte. Réimportez l’original et prévenez un administrateur.",
}


def validate_category(category, format):
    if format not in ALLOWED.get(category, set()):
        raise ValidationError("Ce format n’est pas autorisé dans la catégorie choisie.")
