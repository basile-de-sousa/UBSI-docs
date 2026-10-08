# Documentation du SI AirSIGL

Point d'entrée unique du projet UBSI : référentiels de données et de flux, fiches par application, specs et décisions d'architecture.

## Où trouver quoi

| Je cherche... | Où |
|---|---|
| Qui possède une donnée, qui la copie ou la consulte | [Référentiels > Données](referentiels/donnees.md) |
| Les échanges entre applications | [Référentiels > Flux](referentiels/flux.md) |
| Tout ce qui concerne une application | [Applications](applications/index.md) |
| Ce qu'un sprint doit livrer | [Specs](specs/index.md) |
| Pourquoi une décision a été prise | [Décisions (ADR)](adr/index.md) |
| Comment modifier quelque chose | [Contribuer](contribuer.md) |

## Comment le dépôt est organisé

| Dossier | Contenu | Rôle |
|---|---|---|
| `data/` | Fichiers CSV + `schema.yaml` | **Source de vérité** des référentiels |
| `docs/` | Pages Markdown rédigées | Specs, ADR, guides |
| `site/` | Thème et générateur | **Présentation uniquement**, aucune donnée |

Les pages des référentiels et des applications sont générées à chaque build à partir de `data/`. Elles ne sont jamais modifiées à la main.

Les fichiers bureautiques (présentations, livrables Word, exports PDF) restent sur le Google Drive du projet.
