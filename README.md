# UBSI docs

Documents versionnés du projet UBSI (SI de la compagnie AirSIGL, EPITA SIGL).

## Télécharger

Toujours la dernière version :

| Quoi | Lien |
|---|---|
| Tous les référentiels (un onglet par CSV) | [UBSI_referentiels.xlsx](https://github.com/basile-de-sousa/UBSI-docs/releases/latest/download/UBSI_referentiels.xlsx) |
| Applications | [applications.xlsx](https://github.com/basile-de-sousa/UBSI-docs/releases/latest/download/applications.xlsx) |
| Données | [donnees.xlsx](https://github.com/basile-de-sousa/UBSI-docs/releases/latest/download/donnees.xlsx) |
| Flux | [flux.xlsx](https://github.com/basile-de-sousa/UBSI-docs/releases/latest/download/flux.xlsx) |
| Tous les autres fichiers (zip de `files/`) | [UBSI_fichiers.zip](https://github.com/basile-de-sousa/UBSI-docs/releases/latest/download/UBSI_fichiers.zip) |

- **Un seul fichier** : ouvrez-le dans [`files/`](files/), puis bouton *Download raw file*.
- **Une ancienne version** : page [Releases](https://github.com/basile-de-sousa/UBSI-docs/releases). Chaque publication liste les fichiers modifiés.

Un nouveau CSV dans `data/` donne automatiquement son propre `.xlsx` et un onglet dans le classeur global.

## Organisation

```
data/      Référentiels en CSV (source de vérité, convertis en Excel à chaque publication)
files/     Autres documents : PDF, Word, PowerPoint, images...
docs/      Specs (docs/specs/) et décisions d'architecture (docs/adr/), en Markdown
scripts/   Conversion CSV → Excel
```

## Modifier

1. Modifiez un CSV dans `data/` ou ajoutez un fichier dans `files/` (sur GitHub : *Add file > Upload files*).
2. Ouvrez une pull request. La conversion Excel est vérifiée automatiquement.
3. Une fois la PR fusionnée, une nouvelle Release est publiée en quelques minutes.

CSV depuis Excel : *Enregistrer sous > CSV UTF-8*. Les séparateurs `,` et `;` sont acceptés tous les deux.

Le dépôt est public : aucune donnée personnelle (emails, logins Forge, identifiants).

Pour tester la conversion en local :

```bash
pip install -r requirements.txt
python scripts/csv_to_xlsx.py   # écrit les .xlsx dans dist/
```
