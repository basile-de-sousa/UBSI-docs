# Portail UBSI — guide utilisateur et administrateur

État au 12 octobre 2026. Ce guide décrit les fonctions implémentées localement. L’adresse de production sera communiquée après définition de l’hébergement et recette. Le chatbot lecteur attend encore sa qualification métier.

## 1. Accéder au portail

Un administrateur invite chaque membre par email avec le rôle utilisateur ou administrateur. Il n’existe pas d’inscription libre. Suivre le lien reçu, valable 72 heures, puis choisir un mot de passe d’au moins 12 caractères respectant les règles affichées. Le lien est personnel et à usage unique ; demander un nouvel envoi s’il a expiré.

Se connecter avec l’email et le mot de passe. **Mot de passe oublié** permet de demander un lien personnel de récupération valable une heure. Le portail affiche le même accusé pour une adresse connue ou inconnue. En cas d’échec d’envoi, contacter un administrateur. Une déconnexion termine la session courante ; une désactivation de compte ou une réinitialisation invalide les anciennes sessions.

La connexion GitHub n’est pas encore disponible. En développement, Mailpit intercepte les emails sans les envoyer aux vrais destinataires ; son usage est décrit dans le [README du portail](../../portal/README.md).

## 2. Consulter les informations

Tous les membres actifs consultent les publications actuelles. La navigation donne accès aux applications, epics, user stories, sprints, spécifications, documents et FAQ. Les brouillons et l’historique des versions sont réservés aux administrateurs.

Les epics peuvent concerner plusieurs applications. Une story appartient à un epic et précise les applications concernées, son responsable, son état et son éventuelle affectation à un sprint. Les sprints sont communs au projet. Les liens de chaque fiche permettent de suivre les contenus associés.

Utiliser la recherche transversale pour trouver une référence ou des mots, puis filtrer selon les options affichées. Les résultats suivent la publication actuelle : un texte encore en brouillon ou archivé n’apparaît pas. Une section renommée conserve son ancre lorsque c’est possible ; si elle a été retirée, la page signale la section manquante.

Sur mobile, ouvrir la navigation avec le bouton de menu. La touche Échap ferme ce menu et rend le focus au bouton. Le lien d’accès au contenu permet d’éviter de parcourir toute la navigation au clavier. La revue complète avec technologies d’assistance reste à terminer.

## 3. Consulter et télécharger les documents

Ouvrir la bibliothèque documentaire, puis une fiche publiée. Utiliser les contrôles de pages, d’onglets ou de zoom selon le format. Les grands tableaux disposent d’une consultation paginée ; les feuilles Excel masquées restent identifiées comme telles.

| Catégorie | Formats importables |
| --- | --- |
| Flux de données | `.drawio`, XML draw.io valide |
| Tableaux | `.xlsx`, `.csv` |
| Diagrammes de bases de données | draw.io/XML, `.puml`, `.plantuml`, `.pdf`, `.png`, `.jpg`, `.jpeg`, `.svg` |

L’aperçu Excel affiche les résultats de formules déjà enregistrés dans le fichier ; il ne recalcule pas les formules. Si un résultat n’est pas enregistré, un indicateur le signale. Enregistrer/recalculer le classeur dans l’outil d’origine puis réimporter si nécessaire.

**Télécharger l’original** restitue les octets du fichier importé. L’aperçu peut être une représentation sécurisée différente de cet original. Une erreur d’intégrité ou d’indisponibilité doit être signalée à un administrateur. Il n’existe pas d’édition draw.io ou Excel directement dans le portail.

## 4. FAQ et assistant

La FAQ contient les questions/réponses publiées, avec filtres et liens associés. La recherche et la FAQ restent utilisables pendant la qualification du chatbot.

**À ce stade, les lecteurs voient un message de qualification en cours.** Après qualification et activation par l’opérateur, le fonctionnement prévu est le suivant : saisir une question, recevoir un extrait exact d’une publication et suivre son lien, ou lire : « Aucune réponse adaptée n’a été trouvée. Allez en parler aux urbanistes. » Ce message n’envoie aucune notification aux urbanistes ; le membre les contacte lui-même.

L’assistant cherche dans la FAQ et les textes publiés des epics, stories et spécifications. Il ne lit pas le contenu des fichiers Excel ou des schémas importés. Les échanges restent dans la mémoire de la page et peuvent être effacés ; ils ne constituent pas un historique partagé. Une erreur technique ou une attente excessive se distingue de l’absence de réponse : réessayer selon le message affiché.

## 5. Administrer les comptes

Dans **Comptes & accès**, inviter un membre, renvoyer une invitation, modifier un rôle ou désactiver/réactiver un compte. Les changements de droits sont contrôlés au serveur et affectent les sessions existantes. Le dernier administrateur actif ne peut pas être désactivé ou rétrogradé.

La désactivation conserve les attributions et auteurs historiques. Après réactivation, le membre se reconnecte ; ses anciennes sessions ne reviennent pas. Si une invitation échoue à l’envoi, corriger le transport avec l’opérateur puis réessayer. Le tout premier administrateur est créé par la commande interactive documentée, sans mot de passe partagé.

## 6. Rédiger et publier un contenu

1. Ouvrir l’administration des contenus et choisir le type à créer, ou ouvrir une publication et commencer sa modification.
2. Renseigner les champs et les liens. Publier d’abord les applications et parents nécessaires. Une spécification ou un document doit être associé à une application publiée ; les applications d’une story doivent appartenir à son epic.
3. Enregistrer le brouillon. Pour les textes riches, utiliser les titres, listes, liens, tableaux simples et blocs de code de l’éditeur.
4. Prévisualiser, vérifier les liens et publier explicitement. Les utilisateurs voient alors la nouvelle version.

Enregistrer une modification ne change pas la version déjà visible. Une publication invalide indique les corrections nécessaires. Si un autre administrateur a modifié le même contenu, la page signale un conflit et conserve la saisie : consulter la version actuelle avant de reprendre. Ne pas supposer qu’un rechargement écrasera les changements de l’autre personne.

L’historique permet de consulter une ancienne version et de la restaurer **en brouillon**. Relire puis publier pour la rendre courante. L’archivage retire le contenu de la consultation actuelle et de la recherche ; il peut être refusé tant que des publications dépendent de ce parent. L’abandon d’un brouillon ne remplace pas la publication existante.

L’import des applications depuis le CSV est une initialisation unique avec prévisualisation/confirmation. Il crée des brouillons et ne synchronise pas les modifications futures du dépôt avec le portail.

## 7. Importer ou remplacer un document

Créer une fiche document, choisir sa catégorie, renseigner ses liens et importer le fichier. Attendre la préparation de l’aperçu puis le consulter avant publication. La taille maximale initiale est de 20 MiB ; des limites de complexité s’appliquent aussi aux pages, cellules, images et fichiers compressés. Voir les limites détaillées dans le [README](../../portal/README.md).

Les sources utilisant des ressources externes, du contenu actif ou des formats non pris en charge peuvent être refusées. Corriger/réexporter le fichier puis réimporter. Une panne transitoire peut proposer une reprise. Le worker prépare l’aperçu mais ne publie jamais automatiquement.

Pour remplacer une publication, importer le nouveau fichier dans son brouillon. L’ancien reste visible tant que le remplacement n’est pas prêt et publié. En cas d’échec, il reste inchangé. L’historique administrateur permet de télécharger les anciens originaux et de les restaurer dans un brouillon.

## 8. Gérer les sprints

Créer et publier un sprint planifié avec son objectif, ses dates et son responsable. Affecter les stories publiées et leurs responsables. Démarrer le sprint depuis l’action prévue ; il ne peut y avoir qu’un seul sprint actif.

À la clôture, publier ou abandonner les brouillons concernés, puis choisir pour chaque story inachevée un retour au backlog ou un report vers un sprint planifié. Si les affectations ou versions ont changé depuis l’ouverture de l’écran, recharger la clôture et revoir les décisions.

La clôture conserve un instantané des stories avant leur réaffectation. La fiche du sprint fermé garde ces états/titres/responsables historiques ; le lien d’une story ouvre sa fiche actuelle. Un sprint fermé ne se rouvre pas.

## 9. Qualifier le chatbot et préparer la mise en service

Les administrateurs disposent d’un aperçu expérimental dans l’administration de la recherche. Réindexer prépare les publications actuelles ; cela n’approuve pas le candidat et n’active pas le chatbot lecteur.

Fournir aux urbanistes les questions UBSI, les destinations et réponses attendues, y compris les questions sans réponse adaptée. Suivre le [guide de qualification M6](../../qualification/m6/README.md). La validation des réponses, la mise en place de l’hébergement et la recette d’exploitation sont encore ouvertes ; le [guide d’exploitation](../operations/PORTAL-RUNBOOK.md) précise la suite.
