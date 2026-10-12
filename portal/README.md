# Portail UBSI

Socle applicatif de [SPEC-001](../docs/specs/SPEC-001-project-knowledge-portal.md), développé directement sur `main` selon [PLAN-001](../docs/plans/PLAN-001-project-knowledge-portal.md).

Documentation complémentaire : [index et ADR](../docs/README.md), [guide utilisateur/administrateur](../docs/guides/PORTAL-USAGE.md), [architecture et maintenance](../docs/architecture/PORTAL-ARCHITECTURE.md), [exploitation](../docs/operations/PORTAL-RUNBOOK.md). Les comptes rendus M0–M7 sont des observations datées ; l’index et le plan donnent l’état actuel et les validations ouvertes.

## État — M7 : recette locale et exploitation préparées

Le portail dispose de la connexion email/mot de passe, des invitations, de la récupération d’accès et d’un annuaire administrateur. Un utilisateur consulte l’espace privé ; un administrateur peut inviter, changer les rôles et désactiver les comptes. Le dernier administrateur actif est protégé. Aucun compte ni mot de passe n’est créé automatiquement.

M3 ajoute les applications, les pages de spécifications avec éditeur visuel et la FAQ. Les administrateurs préparent un brouillon, le prévisualisent puis le publient explicitement. L’historique permet de restaurer une version en brouillon ; les lecteurs consultent uniquement la publication actuelle. L’import initial des applications est disponible dans l’administration. [Compte rendu local M3](../docs/qualification/M3-revisioned-knowledge.md).

M4 ajoute les epics transverses, les user stories structurées, les sprints communs et leur clôture avec instantané historique. L’accueil indique le sprint actif. [Compte rendu local M4](../docs/qualification/M4-backlog-and-sprints.md).

M5 ajoute la bibliothèque documentaire, les imports privés, les aperçus locaux et le téléchargement des originaux, avec remplacement et historique. [Compte rendu local M5](../docs/qualification/M5-imported-documents.md). M6 ajoute la recherche transversale, l’indexation sémantique hors ligne et le chatbot avec cartes sourcées. Le candidat reste en aperçu administrateur : le propriétaire fournira les questions UBSI et leurs réponses attendues avant qualification et activation lecteur. [Compte rendu M6](../docs/qualification/M6-search-and-chatbot.md). Une installation neuve ne contient ni compte ni contenu ; l’import n’est jamais exécuté au démarrage.

## Démarrage avec Docker

Prérequis : Docker Desktop ou Docker Engine avec Compose, Python 3.12 pour générer la configuration locale. Node n’est pas nécessaire sur la machine hôte pour cette méthode.

Depuis la racine du dépôt :

```bash
python3 portal/scripts/init_dev.py
docker compose -f portal/compose.yaml up --build -d
docker compose -f portal/compose.yaml ps -a
```

L’initialisation crée `portal/.env` avec des secrets aléatoires, des permissions `0600` et un dossier temporaire privé hors du dépôt. Elle refuse de remplacer un fichier existant. Si `.env` existe déjà, omettre la première commande. Le fichier `.env.example` documente les variables ; ses valeurs d’exemple ne permettent pas un démarrage valide.

Le build compile les ressources, installe les dépendances Python verrouillées puis collecte les fichiers statiques. Compose démarre PostgreSQL, applique les migrations avec un service ponctuel, puis démarre Gunicorn et le worker d’aperçus et d’indexation. Le build acquiert les viewers et les modèles publics verrouillés par empreinte et installe Java/Cairo ; aucun document privé n’est envoyé à un service de rendu externe. Une migration en erreur empêche le démarrage du service web. Le service `migrate` terminé avec le code `0` est normal.

- Connexion : [127.0.0.1:8000](http://127.0.0.1:8000/). Utiliser la même origine que `PUBLIC_BASE_URL` pour suivre les emails.
- Répertoire privé : `/applications/`, `/epics/`, `/stories/`, `/sprints/`, `/specifications/`, `/documents/`, `/faq/`, `/search/`, `/assistant/` ; administration des contenus : `/admin/knowledge/` et des comptes : `/admin/accounts/`. Suivi des index et aperçu expérimental : `/admin/search/`.
- Vie du processus : `/health/live/`.
- Disponibilité : `/health/ready/` — base accessible, migrations appliquées, build présent et stockage privé accessible ; réponse `503` sinon.

Les seuls ports publiés sont `127.0.0.1:8000` (web) et `127.0.0.1:55432` (PostgreSQL local). Les volumes nommés `database` et `private` conservent leurs données entre les redémarrages. Les fichiers privés ne sont jamais servis par WhiteNoise ni par une URL média publique.

Commandes courantes :

```bash
docker compose -f portal/compose.yaml exec web python manage.py check
docker compose -f portal/compose.yaml exec web python manage.py makemigrations --check --dry-run
docker compose -f portal/compose.yaml exec web python manage.py migrate --check
docker compose -f portal/compose.yaml logs --tail=50 migrate web
docker compose -f portal/compose.yaml down
```

`down` conserve les volumes. **Ne pas ajouter `--volumes` pour un arrêt ordinaire** : cela supprimerait les données. Ne pas changer `POSTGRES_PASSWORD` dans `.env` après l’initialisation de PostgreSQL sans modifier aussi le mot de passe du rôle en base.

Pour reconstruire après une modification du code, relancer `up --build -d`. Les sources ne sont pas montées dans le conteneur : le rechargement automatique n’est pas activé avec Gunicorn.

## Premier administrateur et emails locaux

Créer le premier administrateur dans un terminal interactif, après le démarrage :

```bash
docker compose -f portal/compose.yaml exec web python manage.py bootstrap_admin
```

La commande demande l’email, le nom affiché et deux saisies masquées du mot de passe. Elle exige un annuaire vide et un mot de passe conforme ; aucun identifiant n’est passé en argument ou fourni par défaut. Ensuite, se connecter et ouvrir **Comptes & accès** pour inviter l’équipe. Il n’existe pas d’inscription publique ni d’éditeur Django admin.

Pour développer sans serveur SMTP externe, démarrer explicitement la boîte Mailpit :

```bash
docker compose -f portal/compose.yaml -f portal/compose.dev.yaml up --build -d
docker compose -f portal/compose.yaml -f portal/compose.dev.yaml exec web python manage.py bootstrap_admin
```

Si l’annuaire contient déjà un compte, ne pas relancer le bootstrap. Consulter les emails dans [Mailpit local](http://127.0.0.1:8025/) puis suivre le lien d’invitation ou de récupération. **Cette boîte intercepte les emails : elle ne les remet pas aux destinataires réels.** Utiliser des adresses fictives `@example.invalid` pour le développement. Aucun relais n’est configuré ; le contenu de la boîte est temporaire, sans volume persistant, et ses liens personnels restent confidentiels. Le port SMTP `1025` et l’interface `8025` sont publiés uniquement sur loopback.

L’extension de développement impose `DEBUG=false` au serveur web pour afficher les erreurs françaises et masquer l’ancien aperçu public M1. Elle fixe également l’origine locale et le transport SMTP Mailpit. Toujours reprendre les **deux** fichiers Compose pour reconstruire ou arrêter cette variante :

```bash
docker compose -f portal/compose.yaml -f portal/compose.dev.yaml down
```

Pour utiliser le véritable SMTP, omettre `compose.dev.yaml` et renseigner `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, `EMAIL_USE_TLS` ou `EMAIL_USE_SSL`, ainsi que `PUBLIC_BASE_URL` dans l’environnement. TLS et SSL sont mutuellement exclusifs. `PUBLIC_BASE_URL` est une origine de confiance, sans chemin, dont l’hôte figure dans `ALLOWED_HOSTS` ; HTTPS est obligatoire en production. Les liens ne sont jamais construits à partir de l’en-tête Host soumis par un visiteur.

### Cycle de vie des accès

- Invitation : valable **72 h**, à usage unique, email fixé. Renvoyer remplace le précédent lien après réussite de l’envoi. Un compte existant, même désactivé, se gère depuis l’annuaire et ne peut pas être recréé par invitation.
- Mot de passe : **12 caractères minimum**, contrôles Django de similarité, mots courants et mot de passe entièrement numérique ; hash Argon2. La saisie web est bornée à 1 024 caractères.
- Récupération : lien personnel valable **1 h**, invalidé après usage/changement de mot de passe, connexion ou désactivation. La réponse publique ne confirme jamais l’existence d’une adresse. Une panne globale SMTP donne le même message d’indisponibilité pour toutes les adresses. Un échec propre au destinataire reste générique côté public et est signalé dans l’annuaire admin.
- Session : durée **12 h** ; déconnexion par POST protégé CSRF. Une désactivation révoque les anciennes sessions, même si le compte est réactivé avant leur prochaine requête. Une récupération du mot de passe invalide les anciennes sessions. Un changement de rôle est relu dès la requête suivante.
- Administration : pas de suppression des comptes ; la désactivation conserve leur identité. Les écritures utilisent un verrou commun PostgreSQL, protégeant aussi le premier/dernier admin. Un formulaire périmé renvoie un conflit `409` et conserve les choix soumis.
- Limites partagées en base : connexion **30/source et 5/adresse sur 15 min**, récupération **20/source et 3/adresse sur 1 h**, échange de liens **60/source sur 15 min** et soumission d’un lien **20/identité sur 15 min**. Une limite atteinte donne `429` et `Retry-After`. Les variables `*_LIMIT` de `.env.example` règlent les limites publiques principales. Les compteurs utilisent des clés HMAC et une expiration fixe ; ils ne contiennent pas l’email ou l’adresse réseau en clair.

La source réseau est `REMOTE_ADDR`. Les en-têtes clients sont ignorés, sauf lorsqu’un proxy explicitement configuré dans `TRUSTED_PROXY_CIDRS` les remplace avec une seule adresse valide. Sans cette configuration, les membres derrière un proxy partagent sa limite ; les vrais pairs et leur configuration devront être qualifiés avant ouverture.

Purger quotidiennement les compteurs et sessions expirés avec l’ordonnanceur de l’hébergement :

```bash
docker compose -f portal/compose.yaml exec -T web python manage.py purge_access_state
```

La commande est disponible ; aucune tâche système n’est installée automatiquement. Les invitations expirées restent visibles dans l’annuaire et peuvent être renvoyées.

L’envoi SMTP d’une invitation est synchrone, avec délai maximal de 10 s, dans la transaction. Un échec annule la création/remplacement du lien. Si le serveur accepte le mail puis que le commit échoue, le lien reçu peut être invalide : renvoyer l’invitation après résolution de l’incident. La remise effective aux boîtes réelles dépend du SMTP de l’hébergeur et reste à qualifier.

## Contenus et publication

Depuis **Contenus**, créer une application, un epic, une story, un sprint, une spécification, un document ou une question FAQ. La création et **Enregistrer le brouillon** ne rendent rien visible aux lecteurs. **Enregistrer et prévisualiser** enregistre puis ouvre un aperçu réservé aux administrateurs. **Publier le brouillon enregistré** publie une nouvelle version complète après validation. Toute nouvelle saisie désactive ce bouton jusqu’au prochain enregistrement.

Pour modifier un contenu publié, ouvrir son administration puis **Créer un brouillon de modification**. Les utilisateurs conservent la publication actuelle pendant les modifications. Un enregistrement depuis un formulaire périmé est refusé avec `409` : la saisie reste affichée et un lien ouvre la version actuelle dans un autre onglet pour la comparer. Ne pas recharger la page du conflit avant d’avoir repris sa saisie.

| Contenu | Champs et règles de publication |
| --- | --- |
| Application | Code de 2 à 40 caractères, nom et description obligatoires ; type facultatif. Le code initial est réservé dès la création. Publier un renommage réserve le nouveau code et conserve les précédents ; l’UUID, les liens et l’URL restent identiques. |
| Spécification | Titre, texte et au moins une application publiée. Plusieurs applications peuvent partager la même page. Liens facultatifs vers epics, stories et documents. |
| FAQ | Question et réponse obligatoires ; catégorie, applications, contenus associés et jusqu’à 20 formulations alternatives facultatifs. Les formulations peuvent être retrouvées par la recherche de la liste FAQ. |

Les brouillons peuvent contenir des liens vers des contenus encore privés ; publier exige que tous les liens choisis visent des contenus publiés. Une erreur conserve le brouillon et indique la condition bloquante. Les listes lecteur proposent une recherche textuelle, des filtres et une pagination. Les liens réciproques utilisent les publications actuelles et masquent les contenus privés ou archivés.

### Epics et user stories

Les epics et stories utilisent les mêmes brouillons, publication explicite, historique et contrôles de conflit que les spécifications. **Avancement et publication sont distincts** : une story terminée reste lisible, et modifier son avancement exige de publier une nouvelle version.

| Contenu | Champs et règles |
| --- | --- |
| Epic | Titre, objectif, description, périmètre et au moins une application publiée obligatoires. Hors périmètre, conditions d’acceptation, responsable et date cible facultatifs. Un epic peut concerner plusieurs applications et plusieurs sprints. |
| User story | Titre, exactement un epic publié, applications, acteur « En tant que », besoin « Je veux », bénéfice « Afin de » et au moins un critère d’acceptation obligatoires. Contexte, responsable, dépendances, priorité et sprint courant facultatifs. |

Les applications d’une story doivent appartenir à son epic parent. Retirer une application de l’epic est refusé si cela invalide une story publiée : réaffecter ou archiver d’abord cette story. Une story ne peut dépendre d’elle-même ; les cycles sont refusés à la publication. Les dépendances restent informatives et ne bloquent pas automatiquement l’avancement.

Avancements proposés :

- Epic : **Planifié**, **En cours**, **Terminé**, **Annulé**. Ces valeurs n’imposent pas de transition automatique aux stories.
- Story : **Backlog**, **Prête**, **En cours**, **En revue**, **Terminée**, **Annulée**.
- Priorité : **Basse**, **Normale**, **Haute**, **Critique**.

Un critère d’acceptation par ligne ; **100 critères de 2 000 caractères maximum**. Les champs de description structurés sont bornés à **10 000 caractères chacun** ; les titres à **200**. Le responsable est une attribution vers le compte du membre, sans modification de ses droits. Une attribution historique à un compte désactivé peut être conservée ; une nouvelle attribution nécessite un compte actif.

Les pages d’application regroupent les epics/stories associés. Les pages d’epic montrent leurs stories, spécifications et sprints concernés ; une page de story présente ses critères, son epic parent, ses applications, ses dépendances et son sprint courant. Les listes proposent recherche, filtres et pagination.

### Sprints : préparer, démarrer, clôturer

Un sprint est commun à UBSI. Créer puis publier son **nom**, son **objectif**, son **responsable**, sa **date de début** et sa **date de fin**. La fin doit suivre ou égaler le début. Le responsable peut être un lecteur : seuls les administrateurs effectuent les mises à jour. Les dates de sprints planifiés peuvent se chevaucher et ne déclenchent aucune action automatique.

L’affectation se règle dans le champ **Sprint courant** de la story, puis se publie. Une story possède au plus un sprint courant. Les pages de sprint affichent les affectations publiées, filtrables par application et par epic.

Depuis l’administration du sprint :

1. **Démarrer le sprint** publie son passage de Planifié à Actif. Un seul sprint peut être actif. Publier ou abandonner d’abord le brouillon du sprint ; son responsable et ceux de toutes ses stories affectées doivent être actifs et renseignés dans les versions publiées.
2. Une nouvelle affectation au sprint actif exige également un responsable actif sur la story. Les changements de dates, d’objectif, d’avancement ou d’affectation restent des publications explicites.
3. **Clôturer le sprint** présente les stories et exige une décision pour chacune des stories inachevées : **Retour au backlog** retire l’affectation et passe son état à Backlog ; **Reporter vers un sprint planifié** remplace l’affectation en conservant l’avancement. Les stories terminées ou annulées quittent automatiquement l’affectation courante.
4. Publier ou abandonner les brouillons du sprint et de ses stories avant de confirmer. Le bilan expire après **30 minutes**. Une modification des stories, de leur affectation ou du sprint de report peut rendre ce bilan périmé : recharger la clôture pour revoir toutes les décisions.
5. Confirmer **Publier la clôture et les affectations** crée l’instantané, les nouvelles versions des stories et la version clôturée du sprint dans une seule transaction. Un refus laisse ces éléments inchangés. Reprendre la même demande réussie ne crée pas un second instantané.

L’instantané conserve l’objectif, les dates et le responsable du sprint, ainsi que le titre, l’epic, les applications, le responsable et l’avancement de chaque story **avant** les changements d’affectation. La colonne **À la clôture** reste identique après les modifications ultérieures ; les liens ouvrent les versions actuelles des stories.

Un sprint clôturé ne peut être modifié ni rouvert, y compris par restauration d’une ancienne version planifiée/active. Son instantané reste consultable dans l’historique administrateur. Après archivage, seule une version clôturée identique peut être restaurée puis republiée. Clôturer le sprint actif avant de l’archiver.

Si une story est archivée, ses détails historiques sont remplacés par un marqueur d’indisponibilité dans la vue lecteur ; l’historique administrateur conserve l’instantané complet. Les liens optionnels vers des contenus archivés sont masqués et doivent être résolus avant une nouvelle publication. Aucun calcul de capacité, points ou métrique agile n’est livré.

### Éditeur de spécifications

L’éditeur visuel est chargé localement lorsqu’une page de spécification est ouverte. Il propose les titres de niveaux 2 à 4, paragraphes, gras, italique, listes simples ou numérotées, liens, tableaux avec ajout/retrait de lignes et colonnes, blocs de code en texte brut et annuler/rétablir. Il nécessite JavaScript ; les autres formulaires restent utilisables sans éditeur.

Les sections reçoivent un identifiant stable : renommer un titre conserve son lien de sommaire. Une section absente mène au contenu actuel avec un message explicite. Le serveur valide le JSON et produit le HTML à partir des seules structures autorisées ; le texte saisi n’est jamais interprété comme du HTML libre. Les liens acceptent HTTP(S), mailto et les chemins locaux. Les images, styles intégrés, cellules fusionnées et langages de coloration ne sont pas proposés dans cette version.

Limites : document JSON de **1 Mio**, **200 000 caractères** de texte, **10 000 nœuds**, profondeur **16** ; tableau rectangulaire de **50 lignes × 20 colonnes** maximum. Une spécification contenant uniquement les titres du modèle ne peut pas être publiée. Les fichiers s’importent dans un contenu Document, séparément de l’éditeur de texte.

### Historique, restauration et archivage

**Historique des versions** conserve les textes et les liens publiés avec numéro, auteur et date. **Restaurer en brouillon** copie une version sans modifier celle des lecteurs. Si un brouillon existe déjà, son remplacement doit être confirmé. Pour remettre un contenu archivé à disposition, restaurer une version puis publier le brouillon.

**Archiver le contenu** retire sa visibilité et ses passages de recherche, en conservant son historique et son éventuel brouillon. Une application requise par une spécification publiée ne peut pas être archivée : réaffecter ou archiver d’abord la spécification. **Abandonner le brouillon** retire sa saisie ; les versions publiées restent conservées. Un contenu jamais publié doit être sans lien entrant pour être abandonné. Ses identifiants et codes restent réservés, même après abandon ; la saisie d’un brouillon jamais publié ne dispose pas d’un historique de restauration.

La publication et les liens sont validés dans une transaction PostgreSQL avec verrou commun et contrôle de version. Les révisions publiées sont protégées contre les modifications et suppressions par le modèle et des déclencheurs en base. Les passages lexicaux sont remplacés et les travaux d’indexation sémantique sont inscrits dans cette même transaction. Le worker traite désormais ces travaux, avec contrôle de la révision courante et protection contre les résultats d’un ancien bail. La recherche transversale française est accessible dans `/search/` ; les recherches propres aux listes restent disponibles.

### Import initial des applications

Dans **Contenus → Importer les applications**, sélectionner `data/applications.csv`, relire le rapport puis confirmer la création des brouillons. Format : CSV UTF-8 à virgules, colonnes exactes `code,nom,type,description`, **64 Kio et 100 applications maximum**. L’import préserve les codes, noms, types et descriptions. Il conserve les applications dont le code est déjà réservé et ne publie jamais automatiquement.

L’import initial est effectué **une seule fois**. Après sa réussite, tout nouvel appel conserve les contenus existants, y compris leurs modifications dans le portail. La maintenance suivante se fait dans l’administration ; modifier le CSV n’alimente pas automatiquement le site. Le rapport préalable expire au bout de 30 minutes ; relancer sa préparation si nécessaire.

Équivalent en ligne de commande, depuis la racine du dépôt :

```bash
docker compose -f portal/compose.yaml exec -T web python manage.py import_applications --file /dev/stdin --dry-run < data/applications.csv
docker compose -f portal/compose.yaml exec -T web python manage.py import_applications --file /dev/stdin --actor UUID_ADMIN_ACTIF < data/applications.csv
```

Remplacer `UUID_ADMIN_ACTIF` par l’UUID d’un administrateur actif. Le mode `--dry-run` est sans écriture. En natif, après chargement de l’environnement : `portal/.venv/bin/python portal/manage.py import_applications --file data/applications.csv --dry-run`, puis ajouter `--actor UUID_ADMIN_ACTIF` pour appliquer. Reprendre les deux fichiers Compose si la variante Mailpit est utilisée. Un import déjà effectué rapporte les compteurs de son exécution initiale ; il ne recrée pas les brouillons.

## Documents importés et aperçus

Depuis **Contenus → Documents**, renseigner le titre, la catégorie, la description et au moins une application. Les liens vers epics, stories et spécifications sont facultatifs. Enregistrer les métadonnées, puis choisir le fichier dans **Importer un original**. L’import et le worker ne publient rien : consulter l’aperçu, puis utiliser **Publier le brouillon enregistré**.

| Catégorie | Formats autorisés |
| --- | --- |
| Flux de données | `.drawio`, `.xml` dont le contenu est un diagramme draw.io valide |
| Tableau Excel / CSV | `.xlsx`, `.csv` |
| Diagramme de base de données | draw.io/XML validé, `.puml`, `.plantuml`, `.pdf`, `.png`, `.jpg`, `.jpeg`, `.svg` |

La bibliothèque **Documents** filtre les publications par texte, application et catégorie. Les téléchargements retournent exactement les octets importés, avec le nom de fichier ; les aperçus dérivés ne remplacent jamais l’original.

### Préparation et remplacement

- États : **Préparation en cours**, **Aperçu prêt**, **Préparation échouée**. La page suit l’état pendant trois minutes ; une saisie non enregistrée empêche le rechargement automatique. Le suivi reprend sur la page actuelle après enregistrement.
- Une publication exige un aperçu prêt et une catégorie identique à celle de l’import. Modifier la catégorie exige de réimporter le fichier.
- Pour remplacer un fichier publié, créer un brouillon de modification et importer un nouvel original. Un import en attente, invalide ou trop volumineux ne modifie jamais la publication actuelle.
- En cas de conflit de version, resélectionner le fichier dans le brouillon actuel : le navigateur ne conserve pas une sélection de fichier après réponse du serveur.
- Les échecs indiquent une correction possible. **Réessayer la préparation** convient à un incident temporaire ; corriger et réimporter les sources invalides ou trop complexes. Le tableau d’administration filtre les préparations en cours ou échouées.
- L’historique admin conserve les originaux et aperçus des versions publiées. **Restaurer en brouillon** reprend aussi le fichier historique, sans modifier la publication actuelle. Archiver retire immédiatement le document et ses fichiers des vues lecteur.

### Consultation

**Excel** : toutes les feuilles, y compris celles masquées, sont proposées dans le sélecteur. Chaque page contient au plus 100 lignes ; le tableau défile horizontalement et au clavier. Les valeurs enregistrées sont affichées sans recalcul des formules. Un résultat absent affiche **Résultat non disponible** ; un résultat enregistré réellement vide reste vide. La formule est consultable comme texte inerte. Nombres, dates, pourcentages, gras et retours à la ligne sont simplifiés ; graphiques, mise en forme conditionnelle et disposition exacte des cellules fusionnées ne sont pas reproduits. Les feuilles graphiques seules sont refusées avec une erreur de rendu.

**CSV** : UTF-8 avec ou sans BOM ; virgule, point-virgule ou tabulation. La détection refuse les résultats ambigus ou les lignes incohérentes. Réimporter avec le séparateur explicite si nécessaire. Les cellules restent du texte, sans exécution de formules.

**draw.io** : pages compressées ou non, sélecteur, déplacement et zoom ; viewer et 9 089 noms de stencils locaux verrouillés en version 32.4.1. Les stencils intégrés simples sont validés. Ressources externes, actions, mathématiques et bibliothèques personnalisées non représentables sont refusées ; simplifier le diagramme ou exporter dans un autre format autorisé si nécessaire.

**PlantUML** : rendu local 1.2026.8, profil `SANDBOX`, moteur Smetana, plusieurs blocs/pages. Includes, thèmes externes, liens et ressources externes sont refusés. Aucun service public PlantUML n’est utilisé.

**PDF et images** : PDF.js 6.4.299 dessine les pages sur canvas, sans actions, liens, formulaires ni pièces jointes. Les décodeurs WebAssembly de PDF.js sont chargés localement dans ce cadre ; l’évaluation de JavaScript dynamique reste désactivée. Le gestionnaire PDF s’exécute dans le cadre isolé ; son avertissement « fake worker » désigne ce choix local. PNG/JPEG sont décodés et réencodés ; les SVG autorisés sont rasterisés par CairoSVG, jamais insérés comme contenu actif. Le téléchargement SVG reste une pièce jointe.

Les cadres des diagrammes ont une origine opaque, sans accès au parent, aux cookies ou aux fichiers privés par leur propre script. La page autorisée leur transmet uniquement l’aperçu sélectionné. Les scripts, fonts et stencils viennent du site ; aucune source n’est transmise à diagrams.net ou à un renderer distant.

### Limites et exploitation

Limites par défaut, affichées avant sélection : **20 Mio** par original, **50 feuilles ou pages**, **200 000 cellules renseignées**, **20 000 lignes et 200 colonnes renseignées** par feuille, **200 Mio** de classeur décompressé. Le formatage vide hors étendue des données n’agrandit pas un aperçu Excel. Autres bornes : **16 millions de pixels**, **8 000 px** par côté, **8 Mio XML draw.io** décompressés par page, **200 Mio** cumulés d’aperçus dérivés. Une limite entraîne un échec visible, sans publication partielle.

Le worker est livré avec Compose. Sa branche documentaire réclame les tâches `preview`, utilise un bail de durée supérieure au délai du job, vérifie l’empreinte de la source et prépare les fichiers dans un sous-processus privé. Délai global : **60 s**, PlantUML : **20 s**, tas Java : **256 Mio**. Les formats invalides échouent directement ; les incidents temporaires ont au plus trois tentatives automatiques avec reprise différée. Les tâches `semantic_index` sont traitées en alternance par la branche M6, dans un sous-processus hors ligne limité à 300 s, avec trois tentatives au maximum.

Compose borne le worker à **2 Gio**, **1,5 CPU** et **128 processus/threads**. Sous Linux, les parseurs ont une limite d’espace virtuel de **1 536 Mio** ; Java nécessite **4 096 Mio d’espace virtuel réservé**, distincts du tas et de la mémoire effectivement consommée. Ces valeurs restent à qualifier sur l’hébergement réel. Le proxy devra limiter le corps de requête à la taille autorisée plus l’enveloppe multipart ; confirmer quotas et sauvegardes avant usage réel.

```bash
docker compose -f portal/compose.yaml logs --tail=50 worker
docker compose -f portal/compose.yaml exec web python manage.py cleanup_documents
docker compose -f portal/compose.yaml exec web python manage.py cleanup_documents --apply
```

Le nettoyage est **sans suppression par défaut**. Avec `--apply`, il retire uniquement les fichiers abandonnés, les préparations sans référence et les objets temporaires après **24 h minimum**, en revérifiant les liens sous verrou. Tout fichier lié à un brouillon ou à une publication historique est conservé. Un archivage n’est pas une suppression d’historique.

En natif, après installation de Java/Cairo, acquisition des assets, build et chargement de `.env`, lancer dans un second terminal :

```bash
portal/.venv/bin/python portal/manage.py run_worker
# Ou traiter les tâches d’aperçu immédiatement dues, puis quitter :
portal/.venv/bin/python portal/manage.py run_worker --once
```

Les ressources téléchargées sont ignorées par Git et reconstruisibles par empreinte : `python3 portal/scripts/document-assets.py`, puis `(cd portal && node scripts/document-shapes.mjs)`, avant le build frontend. Les licences sont distribuées avec les assets ; le JAR MIT conserve ses notices (`java -jar portal/.vendor/plantuml.jar -license`). Le conteneur expose aussi `vendor/PLANTUML-LICENSE.txt` parmi les ressources statiques.

## Développement natif

Prérequis : Python **3.12**, Node **24.19 ou version ultérieure de la branche 24**, npm, PostgreSQL **17**, Java **17 ou supérieur** et la bibliothèque native **Cairo**. Sur Linux, les sous-processus ont une limite d’espace virtuel ; utiliser Compose pour disposer aussi de la limite mémoire du conteneur. Une base native équivalente peut remplacer le conteneur `db` en adaptant `DATABASE_URL`.

```bash
python3.12 -m venv portal/.venv
portal/.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r portal/requirements.lock
npm --prefix portal ci --ignore-scripts
python3 portal/scripts/document-assets.py
python3 portal/scripts/search-assets.py
(cd portal && node scripts/document-shapes.mjs)
npm --prefix portal run typecheck
npm --prefix portal run build
python3.12 portal/scripts/init_dev.py
docker compose -f portal/compose.yaml up -d db
```

Si `.env` a déjà été créé, omettre la commande d’initialisation. Charger uniquement votre fichier local de confiance, puis lancer Django :

```bash
set -a
source portal/.env
set +a
portal/.venv/bin/python portal/manage.py check
portal/.venv/bin/python portal/manage.py migrate --noinput
portal/.venv/bin/python portal/manage.py collectstatic --noinput
portal/.venv/bin/python portal/manage.py runserver 127.0.0.1:8000 --nostatic
```

Le mode natif utilise le stockage temporaire indiqué dans `.env` ; s’il a été nettoyé par le système, recréer ce dossier avec des permissions `0700` ou choisir un nouveau chemin privé absolu. Ne pas y stocker de documents réels : le stockage persistant de déploiement sera confirmé avec l’hébergeur. Après une modification du frontend, relancer le build puis redémarrer le serveur pour actualiser la liste des ressources WhiteNoise. Le conteneur web doit être arrêté pour libérer le port avant le lancement natif.

## Organisation

| Dossier | Rôle actuel |
| --- | --- |
| `config/` | Paramètres validés, routes et WSGI |
| `accounts/` | Identité UUID, invitations, récupération, limites, sessions, contrôles de rôles et annuaire |
| `core/` | Accueil, aperçu, état de service, contrôles de configuration et politique HTTP |
| `knowledge/` | Contenus, brouillons, révisions immuables, relations, publication et import initial |
| `sprints/` | Cohérence epic/story, démarrage, clôture atomique et instantanés immuables |
| `search/` | Recherche publiée, index lexicaux/sémantiques, politique expérimentale et verrou de qualification |
| `jobs/` | File durable, baux, reprises et worker d’aperçus / indexation |
| `documents/` | Imports, originaux immuables, adaptateurs bornés, viewers privés, historique et nettoyage |
| `templates/`, `frontend/`, `public/` | Interface française et ressources locales |
| `scripts/` | Initialisation locale et conservation des licences des dépendances du navigateur |

Le worker est distinct du serveur web et ne publie jamais un brouillon. `LoginIdentity` prépare une association future fournisseur/identifiant vers le même UUID ; aucun endpoint GitHub ni rapprochement automatique par email n’est activé.

## Configuration et production

L’environnement par défaut est **production**, avec refus de `DEBUG=true`, d’une clé absente/courte/d’exemple, des hôtes génériques, d’une URL SQLite, d’un stockage privé dans les sources ou ressources publiques, et d’une configuration email de production absente. Les erreurs de configuration n’affichent pas les secrets.

| Variable | Utilisation |
| --- | --- |
| `PORTAL_ENV` | `development` pour le local ; `production` par défaut |
| `DEBUG` | Booléen explicite ; aperçu accessible uniquement si développement **et** debug |
| `SECRET_KEY` | Secret aléatoire d’au moins 50 caractères |
| `ALLOWED_HOSTS` | Hôtes explicites séparés par des virgules ; inclure `127.0.0.1` pour le contrôle interne du conteneur |
| `DATABASE_URL` | PostgreSQL avec identifiants ; option `sslmode` acceptée |
| `PRIVATE_STORAGE_ROOT` | Dossier privé existant et accessible, chemin absolu hors du dépôt et des ressources publiques |
| `CSRF_TRUSTED_ORIGINS` | Origines HTTPS explicites si nécessaires ; vide pour un fonctionnement de même origine |
| `PUBLIC_BASE_URL` | Origine canonique de confiance pour les emails ; requise en production |
| `TRUST_HTTPS_PROXY` | Activer uniquement si le proxy de confiance supprime puis réécrit `X-Forwarded-Proto` |
| `EMAIL_*`, `DEFAULT_FROM_EMAIL` | Transport SMTP, TLS et expéditeur ; aucune sortie console de secours |
| `HSTS_INCLUDE_SUBDOMAINS`, `HSTS_PRELOAD` | Désactivés par défaut ; à décider selon le domaine fourni |

Les cookies de production sont sécurisés, HTTP-only et SameSite ; les sessions sont en base. Les vues sont privées par défaut via `accounts.middleware.AccessMiddleware`. Les pages de connexion/invitation/récupération et les contrôles minimaux d’état sont publics ; l’aperçu synthétique M1 n’existe qu’en développement avec debug explicite. Une page privée demandée sans connexion redirige vers le login sans recopier son URL. L’API privée renvoie `401`, et une action admin demandée par un lecteur renvoie `403`. Les routes de fichiers contrôlent la session, le rôle, la publication courante et la version à chaque requête. Les originaux sont servis en pièce jointe après vérification SHA-256 ; les anciens originaux et les brouillons sont réservés aux admins. L’API assistant lecteur renvoie `503 qualification_pending` tant que la qualification métier n’a pas été approuvée. L’aperçu expérimental est réservé aux administrateurs et conserve le même corpus publié.

Les réponses HTML sont privées et non stockables ; la CSP refuse scripts/styles intégrés, ressources externes, objets et encadrement du portail. HTMX est local, avec évaluation dynamique et scripts reçus désactivés. Son code contient une branche `eval`, signalée au build, que la configuration et la CSP interdisent ; ne pas ajouter `unsafe-eval` pour masquer cet avertissement. La licence distribuée est disponible dans `/static/THIRD-PARTY-NOTICES.txt`.

Le conteneur fonctionne sous un utilisateur sans privilèges. Ses journaux d’accès bruts sont désactivés pour éviter d’enregistrer les liens personnels. Les erreurs SMTP et CSRF sont journalisées par code sans destinataire, token ni contenu. Les événements de cycle de vie sont émis au niveau INFO (non affiché par le niveau WARNING par défaut). Les URL portant un lien personnel imposent `Referrer-Policy: no-referrer` et redirigent vers un formulaire à URL propre ; les formulaires conservent `same-origin`, nécessaire à la vérification CSRF de certains navigateurs. L’invitation ne conserve en base qu’une empreinte du secret ; le jeton Django de récupération reste dans la session serveur jusqu’à son invalidation. Les journaux du futur proxy devront aussi masquer les chemins personnels.

**Ce Compose est une référence locale, pas un déploiement de production.** L’hébergeur reste à préciser : proxy HTTPS, secrets, stockage persistant, SMTP, sauvegardes et ressources doivent être confirmés avant ouverture. Les aperçus et modèles hors ligne sont intégrés. M7 fournit une recette technique locale et des outils/procédures d’exploitation ; la validation métier du chatbot et la recette sur le vrai hébergement restent ouvertes.

## Dépendances et CI

- Python : versions transitives et hashes dans `requirements.lock`, résolution universelle Python 3.12 ; installation effectuée sur macOS ARM64 et dans l’image Linux ARM64.
- JavaScript : graphe exact et intégrités dans `package-lock.json` ; `npm ci --ignore-scripts` puis build.
- Images Node, Python et PostgreSQL : versions et digests épinglés dans le Dockerfile et Compose.
- [Licences et sources](THIRD-PARTY.md).
- [CI du portail](../.github/workflows/portal.yml) : installation depuis les verrous, types, build, contrôles Django, migrations PostgreSQL, collecte statique, conversion CSV et construction du conteneur. Son exécution distante sera confirmée après publication des changements.

Le workflow Release existant conserve son périmètre `data/`, `files/`, `scripts/` et sa propre définition. Les changements limités à `portal/` ne publient pas de Release de téléchargements. L’export CSV conserve son `requirements.txt` indépendant à la racine.


## Recherche et assistant — M6

- **Recherche** : `/search/`, titres et textes publiés de tous les types, recherche française, références, filtres type/application/epic/sprint courant et pagination. Les descriptions documentaires sont recherchables ; le contenu des fichiers ne l’est pas.
- **Corpus du chatbot** : uniquement FAQ (question, formulations et réponse), epics, stories et sections de spécifications publiés. Applications, sprints, fichiers, brouillons et archives sont exclus.
- **Indexation** : passages lexicaux remplacés dans la transaction de publication, puis préparation de fenêtres de 350 tokens maximum avec chevauchement de 50, ancrage dans la section et vecteurs E5 normalisés de 384 dimensions. Les deux tokenizers sont bornés à 512 tokens, sans accepter une troncature silencieuse de la preuve. Capacité initiale : 10 000 fenêtres éligibles.
- **Candidat** : union des candidats E5 et lexicaux, questions/alias FAQ exacts, reclassement local, garde contre plusieurs réponses différentes à une même question, références explicites absentes et marges ambiguës. Il propose actuellement au plus une carte. Ces heuristiques ne détectent pas tous les conflits et leurs seuils ne sont pas qualifiés.
- **Réponse** : extrait exact et lien signé vers la publication et la section. Le lien est revérifié à l’ouverture ; une publication remplacée ou archivée rend l’ancien lien indisponible. Un changement pendant la recherche, un index incomplet ou une panne produit une indisponibilité, jamais une conclusion erronée « aucune réponse ».
- **Abstention** : « Aucune réponse adaptée n’a été trouvée. Allez en parler aux urbanistes. » Aucun envoi de message ou ticket n’est créé.
- **Échanges** : questions POST, 500 caractères maximum, 20 requêtes par compte sur 5 minutes et cinq baux concurrents en base. Une inférence par processus CPU ; saturation : `429` avec délai de reprise. Les messages restent uniquement dans la page (12 échanges maximum), sont effaçables et disparaissent à la navigation. Aucun transcript ou journal de questions n’est collecté.

### Préparation et reprise des index

Le build Docker acquiert les artefacts publics dans `.models/`, hors des ressources navigateur. En natif, exécuter `python3 portal/scripts/search-assets.py` ; le script réutilise le cache public M0 s’il existe et vérifie les 17 empreintes. Il télécharge uniquement des fichiers de révisions épinglées. Le modèle E5 est sous MIT et le cross-encoder sous Apache-2.0 ; les cartes et attributions accompagnent les artefacts. Les données du projet ne sortent pas du serveur.

```bash
python portal/manage.py search_status
python portal/manage.py reindex_search --actor UUID_ADMIN_ACTIF
python portal/manage.py run_worker --once --kind semantic_index
```

Charger la configuration locale avant ces commandes, comme dans la section native, ou utiliser `docker compose … exec web python manage.py …`. Le worker permanent alterne les aperçus et les index pour éviter qu’une file bloque l’autre. `--kind preview` et `--kind semantic_index` servent aux reprises ciblées. Une reprise d’index ne publie rien et ne débloque pas le chatbot.

Les dépendances Python CPU sont verrouillées avec hashes. Le verrou utilise PyPI et l’index CPU officiel PyTorch ; `pip install --require-hashes --only-binary=:all: -r portal/requirements.lock` est la référence. Pour `uv pip sync`, ajouter `--index-strategy unsafe-best-match --require-hashes` afin de résoudre les versions exactes parmi ces deux index ; les empreintes restent obligatoires. La génération utilise `uv pip compile --universal --python-version 3.12 --torch-backend cpu --generate-hashes`, puis conserve explicitement l’index CPU dans le fichier produit.

### Qualification et activation

**M6 n’est pas encore accepté.** Le propriétaire a choisi de fournir les questions UBSI et leurs réponses attendues. Le [jeu fictif proposé](../qualification/m6/README.md) et les 60 régressions M0 sont conservés ; aucune réussite métier n’est revendiquée. Ne pas transformer les questions de recette en données de calibration.

Après revue des destinations par les urbanistes, figer la politique, exécuter la qualification indépendante et consigner les résultats effectifs. Le [modèle de compte rendu](../qualification/m6/activation-report.example.json) reste inactif. Chaque cas comporte `id`, `expected`, `returned`, `status` et `private_or_stale` ; les destinations sont les références avec ancre de section. Les groupes contiennent au moins 30 cas de calibration, 30 cas nouveaux et les 60 régressions M0. L’activation exige ≥ 90 % de bonnes destinations et zéro source incorrecte/privée/obsolète, ainsi que les vérifications de cycle de vie. Un échec garde le verrou fermé ; une nouvelle politique nécessite une nouvelle recette indépendante.

L’opérateur place le compte rendu validé dans un fichier privé hors du dépôt, renseigne `CHATBOT_QUALIFICATION_FILE` et redémarre le serveur. Le code vérifie l’empreinte de la politique, des modèles et de l’implémentation, la revue et les résultats ; aucune commande ou interface web ne valide automatiquement un rapport. Les modèles sont alors chargés au démarrage, et la disponibilité échoue si ce chargement n’a pas abouti. Une modification de la politique invalide le rapport. M7 a mesuré les pages locales avec 46 sessions et cinq demandes simultanées à l’aperçu admin ; la qualification métier et les mesures sur l’hébergement réel restent ouvertes.

## M7 — recette et exploitation

La [recette M7](../docs/qualification/M7-integrated-acceptance-and-operations.md) conserve les résultats, les limites et la matrice des 22 scénarios. Le [guide d’exploitation](../docs/operations/PORTAL-RUNBOOK.md) décrit le futur déploiement, les prérequis du proxy/SMTP, les sauvegardes et la restauration. L’hébergement reste à préciser ; le chatbot lecteur attend toujours les cas UBSI validés.

### Rejouer les contrôles techniques

La demande M7 couvre ces essais automatisés. Ils utilisent exclusivement des comptes/fichiers fictifs et une base PostgreSQL `test_*` créée puis supprimée par Django. Ne pas les lancer avec une configuration de production. Utiliser Docker pour disposer de Java et Cairo :

```sh
docker compose -f portal/compose.yaml run --rm migrate python manage.py test acceptance --noinput
docker compose -f portal/compose.yaml exec web python manage.py audit_portal
```

Les contrôles de l’outil hôte se rejouent séparément, avec l’environnement natif chargé :

```sh
portal/.venv/bin/python portal/manage.py test acceptance.test_operations --noinput
```

L’audit vérifie les empreintes de tous les originaux et des aperçus prêts, les pointeurs de publication, les liens obligatoires et l’éligibilité des passages. Il fournit aussi l’âge de la file et les baux expirés. Son inventaire complet doit rester privé sur un déploiement réel.

Pour mesurer une **démonstration locale isolée** déjà peuplée, `qualify_load --confirm-isolated` crée 46 comptes/sessions fictifs temporaires, utilise le serveur HTTP sur loopback, puis supprime ses comptes/sessions. Il mesure les pages puis dix lots de cinq demandes à l’aperçu admin après chauffe ; il n’active jamais le chatbot lecteur et ne valide pas ses réponses métier. Ne pas l’utiliser sur les vrais comptes/contenus. Exécuter cette mesure de référence sans sauvegarde/restauration ni autre recette simultanée ; conserver séparément les observations de saturation. L’attente du verrou d’inférence est bornée à quatre secondes, et les cinq places globales restent protégées.

### Sauvegarde et restauration

`scripts/operations.py` prépare des sauvegardes privées cohérentes avec arrêt/reprise du web et du worker. Il vérifie les empreintes et ne restaure que vers un nouveau projet `ubsi-restore-*`, sans ports publics ni envoi d’emails. L’image doit correspondre exactement à celle de la sauvegarde. La répétition locale a comparé les comptes, révisions, originaux et aperçus restaurés ; les volumes de la copie sont conservés après son arrêt.

La rétention liste les sept points quotidiens et quatre hebdomadaires à conserver et les candidats expirés, sans suppression automatique. Le calendrier, le chiffrement et la destination indépendante seront configurés sur l’hébergement fourni. Voir les commandes complètes dans le guide d’exploitation. Le fichier `compose.production.yaml` est une référence à adapter avec un environnement privé et une image par digest ; les secrets ne sont jamais copiés dans le dépôt.

### Proxy de production

`TRUST_HTTPS_PROXY=true` exige désormais `TRUSTED_PROXY_CIDRS`. Le proxy doit remplacer les en-têtes de provenance, transmettre une seule adresse client et être le seul à joindre l’entrée web privée. Les adresses/en-têtes venant d’un autre pair sont ignorés ; les limites de connexion peuvent ainsi distinguer les membres derrière le proxy. Confirmer les vrais pairs du proxy avant le déploiement.
