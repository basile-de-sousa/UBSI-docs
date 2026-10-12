# Documentation du portail UBSI

État au 12 octobre 2026 : M0 à M5 réalisés localement ; M6 intégré avec qualification métier ouverte ; M7 réalisé pour la recette technique locale et la préparation de l’exploitation. Aucun déploiement de production n’est réalisé. Le chatbot lecteur reste désactivé jusqu’à sa qualification.

## Selon votre besoin

| Besoin | Document |
| --- | --- |
| Comprendre le périmètre et les règles fonctionnelles approuvées | [SPEC-001](specs/SPEC-001-project-knowledge-portal.md) |
| Consulter les jalons, l’architecture prévue et les conditions de livraison | [PLAN-001](plans/PLAN-001-project-knowledge-portal.md) |
| Utiliser le portail ou administrer ses contenus | [Guide utilisateur et administrateur](guides/PORTAL-USAGE.md) |
| Installer et démarrer en local, connaître les commandes et limites | [README du portail](../portal/README.md) |
| Comprendre le code, les données et les transactions | [Architecture et maintenance](architecture/PORTAL-ARCHITECTURE.md) |
| Préparer le déploiement, sauvegarder ou restaurer | [Guide d’exploitation](operations/PORTAL-RUNBOOK.md) |
| Préparer les questions et destinations attendues pour le chatbot | [Qualification M6](../qualification/m6/README.md) |
| Reproduire les sondes techniques initiales | [Qualification M0](../qualification/README.md) |

## Décisions d’architecture

Les ADR sont rédigés en anglais. Les ADR-005 à ADR-009 consignent les choix réalisés pendant l’exécution du plan ; leur statut ne vaut pas recette métier ni autorisation de mise en production.

| ADR | Décision | Statut |
| --- | --- | --- |
| [001](adr/001-data-and-site-separation.md) | CSV et ancien site documentaire généré | Remplacé par 002 |
| [002](adr/002-downloads-via-releases.md) | Téléchargements par GitHub Releases | Conservé, sauf la politique excluant un site |
| [003](adr/003-project-knowledge-portal.md) | Portail privé sur mesure et périmètre initial | Accepté |
| [004](adr/004-m0-preview-and-retrieval-decisions.md) | Composants locaux retenus après M0 ; politiques de recherche mesurées rejetées | Accepté |
| [005](adr/005-application-platform-and-private-access.md) | Django/PostgreSQL, interface locale et comptes privés | Accepté pour l’implémentation |
| [006](adr/006-publication-history-and-sprint-transactions.md) | Brouillons, historique immuable et clôture atomique des sprints | Accepté pour l’implémentation |
| [007](adr/007-private-documents-and-durable-jobs.md) | Originaux privés, aperçus bornés et jobs avec baux | Accepté pour l’implémentation |
| [008](adr/008-grounded-retrieval-and-qualification-gate.md) | Réponses extraites des publications et activation conditionnée à une qualification | Accepté pour le mécanisme ; candidat non qualifié |
| [009](adr/009-deployment-backup-and-operational-acceptance.md) | Proxy explicite, sauvegardes cohérentes et restauration isolée | Accepté pour la préparation ; hébergement à qualifier |

## Réalisations et preuves

Les rapports sont des comptes rendus datés : leurs sections « prochaine étape » et « non exécuté » décrivent l’état au jalon concerné. Le présent index, PLAN-001 et le rapport M7 indiquent l’état consolidé actuel. Les preuves versionnées utilisent uniquement des données fictives ou publiques.

Avant publication du dépôt, le chemin du répertoire personnel présent dans le journal natif M3 a été remplacé par `/workspace/UBSI-docs` et les espaces de fin de ligne des journaux ont été normalisés ; leurs résultats et compteurs sont conservés.

| Jalon | Compte rendu |
| --- | --- |
| M0 — Faisabilité des aperçus et recherche CPU | [Rapport](qualification/M0-technical-qualification.md) |
| M1 — Socle, packaging et configuration | [Rapport](qualification/M1-application-foundation.md) |
| M2 — Connexion, invitations, récupération et rôles | [Rapport](qualification/M2-private-access.md) |
| M3 — Contenus, éditeur, publication et historique | [Rapport](qualification/M3-revisioned-knowledge.md) |
| M4 — Epics, stories et sprints | [Rapport](qualification/M4-backlog-and-sprints.md) |
| M5 — Imports, aperçus et originaux | [Rapport](qualification/M5-imported-documents.md) |
| M6 — Recherche et aperçu expérimental du chatbot | [Rapport](qualification/M6-search-and-chatbot.md) |
| M7 — Recette intégrée et exploitation | [Rapport et matrice des 22 scénarios](qualification/M7-integrated-acceptance-and-operations.md) |

La recette M7 compte 49 contrôles techniques distincts : 45 passent dans l’image Docker et quatre contrôles de l’outil d’exploitation passent séparément sur l’hôte. Les mesures de charge et la restauration portent sur un corpus fictif local ; elles ne garantissent pas les performances de l’hébergement futur.

## Conditions encore ouvertes

- Fournir les questions UBSI, les réponses et sources attendues, les faire revoir par les urbanistes puis réaliser la qualification indépendante du candidat M6.
- Confirmer l’hébergement, le domaine, le proxy/TLS, le SMTP et le stockage persistant ; qualifier la charge et la restauration hors hôte dans cet environnement.
- Compléter les essais avec des fichiers privés représentatifs et la revue clavier, navigateurs et technologies d’assistance.

Les comptes, secrets, emails réels, documents importés et sauvegardes restent hors de ce dépôt public. L’authentification GitHub est une évolution préparée par le modèle d’identité, pas une fonctionnalité livrée.
