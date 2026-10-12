# Qualification technique M0 — SPEC-001

Ces scripts constituent le banc d'essai de l'étape 1. Ils utilisent uniquement des fichiers et des textes fictifs. Ils ne sont pas les composants du futur portail et n'offrent aucune authentification.

Les conclusions et les mesures conservées sont dans [le rapport M0](../docs/qualification/M0-technical-qualification.md). Les résultats de recherche insuffisants sont conservés aussi : aucun essai ne doit être présenté comme une validation du chatbot.

## Préparer

Python 3.12, Java et la bibliothèque système Cairo sont nécessaires. Le téléchargement initial demande un accès Internet et environ 1 Go pour les deux modèles, en plus de l'environnement Python. Les essais de recherche suivants fonctionnent hors ligne, sur CPU.

```bash
python3.12 -m venv .qualification/venv
.qualification/venv/bin/python -m pip install -r qualification/requirements.lock
.qualification/venv/bin/python qualification/acquire.py
```

Les versions, révisions de modèles, URL officielles et empreintes des lecteurs sont figées dans `assets.lock.json`. Les versions frontend qui y figurent sont des candidates pour les étapes suivantes, pas un build déjà validé. Le verrou Python décrit l'environnement macOS mesuré ; le verrou de production Linux sera créé en M1.

## Exécuter

```bash
.qualification/venv/bin/python qualification/files.py
.qualification/venv/bin/python qualification/limits.py
.qualification/venv/bin/python qualification/retrieval.py
.qualification/venv/bin/python qualification/rerank.py
.qualification/venv/bin/python scripts/csv_to_xlsx.py
```

Sur macOS avec Cairo installé par Homebrew, si la bibliothèque n'est pas trouvée, préfixer les deux premières commandes par `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`. Aucun réglage système permanent n'est nécessaire.

Le contrôle d'include PlantUML lance brièvement un serveur sur `127.0.0.1` avec un port libre. Un processus de contrôle peut lire uniquement la ressource fictive demandée ; le rendu SANDBOX doit ensuite échouer sans aucune requête. Aucun serveur externe n'est utilisé pour ce contrôle.

`files.py` et `limits.py` terminent en erreur si un contrôle échoue. Les deux scripts de recherche produisent des mesures et un champ `acceptance_target_met` ; leur code de sortie indique l'exécution du banc, pas la réussite du critère métier. Lire les comptes d'erreurs et les abstentions dans les résultats.

Le corpus, ses 30 questions de calibration et ses 30 premières questions de validation sont versionnés dans `retrieval-fixture.json`. `retrieval_fixture.py` est leur générateur. Le second essai utilise **30 nouvelles questions** dans `retrieval-holdout-v2.json` ; le premier jeu de validation devient un jeu de régression. Les seuils sont calculés uniquement sur la calibration, puis enregistrés avant l'évaluation. Après toute adaptation fondée sur un jeu de validation, créer un nouveau jeu indépendant avant de mesurer la généralisation.

## Consulter les aperçus

```bash
.qualification/venv/bin/python qualification/serve.py
```

Ouvrir `http://127.0.0.1:8788/`. Vérifier les pages et le zoom draw.io/PDF, le changement de feuille Excel, les cellules de formule, le CSV et les images. Le diagnostic affiche les ressources chargées et les contrôles d'isolation. Arrêter le serveur avec Ctrl+C après usage. Il écoute uniquement sur l'interface locale ; ne pas l'exposer ni lui confier de documents réels.

Le dossier ignoré `.qualification/` contient l'environnement, les modèles, les dépendances téléchargées, les fixtures générées et les résultats. Aucun classeur Excel n'est versionné. Les preuves sélectionnées dans `docs/qualification/evidence/` sont entièrement synthétiques.

## Limites du banc

- Les contrôles de permissions, de publication, de stockage privé, de pagination, de concurrence et de reprise des jobs seront implémentés dans le portail.
- La mesure du classeur à 200 000 cellules porte sur sa lecture en flux ; elle ne valide pas l'affichage simultané de toutes les cellules.
- La limite d'expansion ZIP est vérifiée sur des métadonnées synthétiques, sans créer une archive de 200 Mio.
- L'aperçu PDF utilise directement le rendu canvas de PDF.js. Le cadre privé de production et sa livraison authentifiée restent à intégrer.
- Les résultats de recherche sont des mesures sur un petit corpus fictif, sans revue métier des urbanistes ni essai de charge sur l'hébergement final.
