# Contribuer

Toute modification passe par une **pull request** : elle est relue, l'historique garde qui a changé quoi et pourquoi, et le site n'est mis à jour qu'une fois la PR fusionnée.

## Modifier un référentiel (données, flux, applications)

1. Ouvrez le CSV concerné dans `data/` (sur GitHub : bouton crayon, ou dans votre éditeur).
2. Une ligne par élément, en respectant les colonnes de `data/schema.yaml`.
3. Pour une cellule à plusieurs valeurs, séparez-les par `;` (exemple : `BKG;BIL`).
4. Les applications sont référencées par leur **code** (`PLA`, `BKG`...), les données par leur **id** (`D-01`...).
5. Ouvrez une PR. La vérification automatique refuse la PR si une valeur est inconnue, un champ obligatoire vide ou un id en double.

Pour vérifier en local avant de pousser :

```bash
pip install -r requirements.txt
python scripts/validate.py   # contrôle des données
mkdocs serve                 # aperçu du site sur http://127.0.0.1:8000
```

!!! tip "Éditer un CSV dans un tableur"
    Vous pouvez ouvrir un CSV dans Excel ou Google Sheets, mais réenregistrez-le en **CSV UTF-8, séparateur virgule**, sans changer l'ordre des colonnes.

## Écrire une spec ou un ADR

- Specs : `docs/specs/NNN-titre.md`
- Décisions d'architecture : `docs/adr/NNN-titre.md`

Le format est celui du workflow `/spec` (voir le `README.md` du dépôt). Les index des pages Specs et ADR se mettent à jour tout seuls.

## Ajouter une colonne ou un nouveau référentiel

C'est un changement de structure : déclarez-le d'abord dans `data/schema.yaml`, puis mettez à jour le CSV. Si le changement est structurant pour tout le SI, tracez-le dans un ADR.
