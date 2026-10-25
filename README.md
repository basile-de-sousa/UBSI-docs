# UBSI docs

Documents versionnés du projet UBSI (SI de la compagnie AirSIGL, EPITA SIGL).

**Tous les liens utiles : [portail UBSI](https://basile-de-sousa.github.io/UBSI-docs/)** (page provisoire tenue par les urbanistes, en attendant le portail privé).

Pour ajouter ou retirer un lien : modifiez [`site/liens.yml`](site/liens.yml) sur GitHub (crayon *Edit*), commitez sur `main`. La page est republiée en 1 à 2 minutes ; si le fichier est mal formé, la publication échoue et l'ancienne page reste en ligne. Voir [SPEC-002](docs/specs/SPEC-002-interim-link-portal.md).

## Portail UBSI — spécifications et plan d'implémentation

Le projet prépare un site privé pour consulter les applications, epics, user stories, sprints, spécifications, schémas, fichiers Excel et FAQ, avec une administration des contenus et un chatbot d'orientation.

- [Index de la documentation et état consolidé](docs/README.md)
- [Guide utilisateur et administrateur](docs/guides/PORTAL-USAGE.md)
- [Architecture et maintenance](docs/architecture/PORTAL-ARCHITECTURE.md)
- [Spécifications fonctionnelles — SPEC-001 (validées, en anglais)](docs/specs/SPEC-001-project-knowledge-portal.md)
- [Plan d'implémentation — PLAN-001 (exécution commencée, en anglais)](docs/plans/PLAN-001-project-knowledge-portal.md)
- [Décision de développer le portail — ADR-003](docs/adr/003-project-knowledge-portal.md)
- [Rapport de qualification de l'étape 1 — M0](docs/qualification/M0-technical-qualification.md)
- [Rejouer les essais locaux](qualification/README.md)
- [Démarrer le portail en local](portal/README.md)
- [Compte rendu du socle applicatif — M1](docs/qualification/M1-application-foundation.md)
- [Compte rendu des accès privés — M2](docs/qualification/M2-private-access.md)
- [Compte rendu des contenus versionnés — M3](docs/qualification/M3-revisioned-knowledge.md)
- [Compte rendu des epics, stories et sprints — M4](docs/qualification/M4-backlog-and-sprints.md)
- [Compte rendu des documents importés — M5](docs/qualification/M5-imported-documents.md)
- [Recherche et chatbot — M6, qualification en attente](docs/qualification/M6-search-and-chatbot.md)
- [Recette intégrée et exploitation — M7, préparation locale](docs/qualification/M7-integrated-acceptance-and-operations.md)
- [Guide de déploiement, sauvegarde et restauration](docs/operations/PORTAL-RUNBOOK.md)

Les spécifications ont été validées le 11 octobre 2026. M0 a produit 56 contrôles de fichiers réussis et des aperçus locaux. M1 fournit le socle Django/PostgreSQL, Docker et les ressources locales ; M2 ajoute les comptes privés et la gestion des accès. M3 permet de créer, prévisualiser et publier les applications, spécifications et FAQ, avec éditeur visuel et historique. M4 ajoute les epics transverses, stories structurées et sprints communs, avec démarrage, report et mémoire de clôture. M5 ajoute la bibliothèque documentaire, les aperçus locaux draw.io/Excel/CSV/PlantUML/PDF/images, le téléchargement exact des originaux et l’historique des fichiers. Les parcours ont été observés dans un environnement fictif isolé ; le build et les 30 migrations passent. M6 intègre la recherche transversale, les index hors ligne et les cartes de réponse sourcées. **Le chatbot reste en qualification** : les questions UBSI et les réponses attendues seront fournies par les urbanistes avant son activation pour les lecteurs.

La recherche sur CPU est faisable, mais les deux politiques essayées n'atteignent pas les critères de qualité : le nouveau candidat M6 doit être qualifié indépendamment ; les observations locales ne constituent pas une validation métier. Les capacités de l'hébergement restent à préciser avant le déploiement. Les téléchargements actuels restent disponibles ci-dessous.

M7 ajoute la recette automatisée sur PostgreSQL isolé, les essais simultanés, l’audit des originaux/aperçus, les mesures locales avec 46 sessions et une répétition de sauvegarde/restauration. La configuration de production et les procédures sont préparées ; la validation finale attend les questions UBSI, les fichiers représentatifs et les contrôles sur l’hébergement réel.

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
docs/      Specs, plan, ADR, guides, architecture et rapports de qualification
scripts/   Conversion CSV → Excel, construction du portail de liens
site/      Portail de liens provisoire (liens.yml + page)
portal/    Portail privé Django/PostgreSQL (démarrage dans portal/README.md)
```

## Modifier

1. Modifiez un CSV dans `data/` ou ajoutez un fichier dans `files/` (sur GitHub : *Add file > Upload files*).
2. Commitez directement sur `main`.
3. Une nouvelle Release est publiée en quelques minutes. Si un CSV est mal formé, la publication échoue (croix rouge sur le commit) et la Release précédente reste en ligne.

CSV depuis Excel : *Enregistrer sous > CSV UTF-8*. Les séparateurs `,` et `;` sont acceptés tous les deux.

Le dépôt est public : aucune donnée personnelle (emails, logins Forge, identifiants).

Pour tester la conversion en local :

```bash
pip install -r requirements.txt
python scripts/csv_to_xlsx.py   # écrit les .xlsx dans dist/
```
