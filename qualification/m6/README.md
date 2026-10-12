# M6 — Jeu proposé pour la qualification

**En attente des questions UBSI et réponses attendues que le propriétaire a choisi de fournir le 12 octobre 2026.**

Ce jeu reste une proposition de travail, sans approbation ni score de recette.

Ce jeu utilise des contenus fictifs sur le fonctionnement du portail. Il contient 30 questions de calibration, 30 nouvelles questions de recette et les 60 régressions de M0. Il ne valide pas les règles métier réelles d’AirSIGL. Les questions de recette ne doivent pas servir à ajuster les seuils.

Les réponses attendues ci-dessous sont des propositions. Une absence de réponse attendue signifie que l’assistant doit inviter à en parler aux urbanistes. Les cas de panne ou de réindexation doivent afficher une indisponibilité technique distincte.

## Sources fictives proposées

| Identifiant | Titre | Texte publié |
| --- | --- | --- |
| invite | Comment obtenir un compte ? | Seul un administrateur peut inviter un membre par email. Le destinataire choisit son mot de passe en ouvrant le lien d'invitation. |
| password | Mot de passe oublié | Le lien Mot de passe oublié sur la page de connexion permet de demander un email de récupération. Le lien est à usage unique et expire après une heure. |
| draft | Publication des modifications | Enregistrer un brouillon ne modifie pas la page publiée. Un administrateur doit cliquer sur Publier pour rendre ses changements visibles aux lecteurs. |
| carry | Clôturer les travaux inachevés | Lors de la clôture d'un sprint, les stories inachevées sont explicitement remises dans le backlog ou reportées dans un sprint planifié. Le choix est conservé dans l'historique. |
| original | Téléchargement des documents | Le bouton Télécharger l'original fournit le fichier importé sans en modifier les octets. L'aperçu est un fichier dérivé distinct. |
| formula | Formule sans résultat enregistré | L'aperçu Excel lit les résultats enregistrés sans recalculer les formules. Si un résultat manque, ouvrir le classeur dans Excel, le recalculer, l'enregistrer puis le réimporter. |
| archive | Archivage des contenus | Un contenu archivé disparaît de la consultation et de la recherche des lecteurs. Les administrateurs conservent son historique et peuvent restaurer une ancienne version en brouillon. |
| epic | Epics transverses | Un epic peut concerner plusieurs applications. Chaque user story appartient à un seul epic et indique un sous-ensemble des applications de cet epic. |
| editor | Rédaction des spécifications | Les spécifications utilisent un éditeur visuel avec titres, listes, tableaux, liens et blocs de code. Les administrateurs rédigent ces pages directement dans le site. |
| reader | Droits des lecteurs | Un membre avec le rôle utilisateur lit les contenus publiés et utilise le chatbot. Seuls les administrateurs peuvent créer, modifier et publier des contenus. |
| urbanists | Question sans réponse | Si aucune réponse adaptée n'est trouvée, le chatbot affiche : Aucune réponse adaptée n'a été trouvée. Allez en parler aux urbanistes. |
| pages | Consulter les diagrammes PDF | Un document PDF peut comporter plusieurs pages. L'aperçu permet de passer d'une page à l'autre et de zoomer sans quitter le site. |
| history | Anciennes versions | Les administrateurs consultent l'historique des versions publiées et restaurent une version dans un brouillon. Les lecteurs voient seulement la version actuellement publiée. |
| hidden | Feuilles masquées Excel | Les feuilles masquées du classeur sont consultables dans l'aperçu avec une indication Masquée. Tous les onglets restent accessibles dans le sélecteur de feuilles. |
| failure | Remplacement de fichier en échec | Une nouvelle révision de fichier ne peut pas être publiée si son aperçu a échoué. La version précédemment publiée reste disponible pendant la correction du remplacement. |
| one-sprint | Sprint actif | Les sprints sont communs au projet. Un seul sprint peut être actif à un instant donné. L'activation d'un deuxième sprint est refusée tant que le premier reste actif. |
| drawio | Diagrammes draw.io | Les administrateurs importent les fichiers draw.io. Les lecteurs consultent les pages du diagramme et le téléchargent. La modification du dessin se fait dans un outil externe. |
| cross | Sprints et applications | Un sprint commun peut regrouper des user stories de plusieurs applications. Le filtre Application aide à retrouver les stories concernées sans créer de sprint séparé. |
| conflict-a | Suppression des comptes DEMO | Les comptes DEMO doivent être supprimés après trente jours. |
| conflict-b | Suppression des comptes DEMO | Les comptes DEMO ne doivent pas être supprimés après trente jours. |
| private-draft | Code de secours DEMO-DRAFT | Le code de secours DEMO-DRAFT est FICTIF-123. |
| archive-only | Mot de contrôle DEMO-ARCHIVE | Le mot de contrôle DEMO-ARCHIVE est FICTIF-456. |
| file | Facture DEMO-FILE | La facture DEMO-FILE indique 123 euros fictifs. |
| stale | Mot de passe oublié | Les anciens liens expirent après dix jours. Cette version est obsolète. |

## Calibration

| Cas | Question | Destination attendue |
| --- | --- | --- |
| cal-01 | Qui peut m'envoyer une invitation pour rejoindre le portail ? | invite |
| cal-02 | J'ai perdu mon mot de passe, que dois-je faire ? | password |
| cal-03 | Un brouillon enregistré est-il immédiatement visible par l'équipe ? | draft |
| cal-04 | Que faire des stories non terminées quand on clôture un sprint ? | carry |
| cal-05 | Puis-je récupérer le fichier exactement comme il a été importé ? | original |
| cal-06 | Pourquoi mon aperçu affiche-t-il Résultat non disponible pour une formule ? | formula |
| cal-07 | Les lecteurs peuvent-ils encore consulter un contenu archivé ? | archive |
| cal-08 | Un epic peut-il couvrir deux applications différentes ? | epic |
| cal-09 | Comment insérer un tableau dans une spécification ? | editor |
| cal-10 | Avec un rôle utilisateur, puis-je modifier une user story ? | reader |
| cal-11 | À qui m'adresser lorsque le chatbot ne trouve aucune réponse ? | urbanists |
| cal-12 | Comment lire la deuxième page d'un PDF sur le portail ? | pages |
| cal-13 | Qui peut consulter les anciennes versions des specs ? | history |
| cal-14 | Où retrouver les onglets masqués d'un classeur ? | hidden |
| cal-15 | Si l'aperçu du nouveau fichier échoue, que voient les lecteurs ? | failure |
| cal-16 | Peut-on avoir deux sprints actifs en même temps ? | one-sprint |
| cal-17 | Peut-on éditer directement un dessin draw.io dans le portail ? | drawio |
| cal-18 | Un sprint peut-il regrouper des stories de plusieurs applications ? | cross |
| cal-19 | Quel temps fera-t-il demain à Lyon ? | Aucune — urbanistes |
| cal-20 | Quel restaurant choisir ce soir ? | Aucune — urbanistes |
| cal-21 | Quel est le budget annuel du projet ? | Aucune — urbanistes |
| cal-22 | Quelle est l'adresse SMTP de l'hébergement ? | Aucune — urbanistes |
| cal-23 | Quelle formule calcule la taxe sur les billets ? | Aucune — urbanistes |
| cal-24 | Quel epic couvre le remboursement des billets ? | Aucune — urbanistes |
| cal-25 | Combien de jours dure notre prochain sprint ? | Aucune — urbanistes |
| cal-26 | Quel est le délai de suppression des comptes DEMO ? | Aucune — urbanistes |
| cal-27 | Les comptes DEMO doivent-ils être supprimés au bout de trente jours ? | Aucune — urbanistes |
| cal-28 | Quel est le code de secours DEMO-DRAFT ? | Aucune — urbanistes |
| cal-29 | Quel est le mot de contrôle DEMO-ARCHIVE ? | Aucune — urbanistes |
| cal-30 | Quel est le montant de la facture DEMO-FILE ? | Aucune — urbanistes |

## Nouvelles questions de recette

| Cas | Question | Destination attendue |
| --- | --- | --- |
| hold-01 | Notre nouveau collègue n'a pas encore accès au portail. Par qui doit-il passer ? | invite |
| hold-02 | Quelle procédure suivre pour choisir un autre mot de passe si j'ai oublié le mien ? | password |
| hold-03 | Après enregistrement d'un brouillon, quelle étape reste nécessaire pour diffuser la correction ? | draft |
| hold-04 | Au moment de fermer une itération, quels choix sont proposés pour une story inachevée ? | carry |
| hold-05 | En récupérant un fichier du portail, obtient-on les octets d'origine ? | original |
| hold-06 | D'où vient la mention Résultat non disponible dans une cellule calculée et comment la corriger ? | formula |
| hold-07 | Après retrait d'une page par archivage, les membres peuvent-ils encore la retrouver ? | archive |
| hold-08 | Pour un besoin transverse à trois applications, faut-il trois epics distincts ? | epic |
| hold-09 | Quels éléments de mise en page sont disponibles pour rédiger une spec ? | editor |
| hold-10 | Quels contenus puis-je créer avec le simple rôle lecteur ? | reader |
| hold-11 | À qui demander une précision absente des connaissances interrogées par l'assistant ? | urbanists |
| hold-12 | Où passer à la page suivante d'un document PDF importé ? | pages |
| hold-13 | Est-ce qu'un administrateur peut remettre une ancienne publication dans un brouillon ? | history |
| hold-14 | Où sélectionner un onglet Excel initialement caché ? | hidden |
| hold-15 | Une erreur de préparation sur un nouveau fichier empêche-t-elle de lire l'ancien ? | failure |
| hold-16 | Tant que notre itération courante n'est pas clôturée, peut-on en lancer une seconde ? | one-sprint |
| hold-17 | Pour déplacer une forme d'un schéma importé, quel outil faut-il utiliser ? | drawio |
| hold-18 | Comment retrouver les stories d'une application particulière à l'intérieur d'un sprint partagé ? | cross |
| hold-19 | Quelle météo annonce-t-on pour Marseille lundi ? | Aucune — urbanistes |
| hold-20 | Où commander un sandwich demain midi ? | Aucune — urbanistes |
| hold-21 | Quelle somme UBSI a-t-il dépensée en hébergement ? | Aucune — urbanistes |
| hold-22 | Quel nom d'hôte utiliser pour notre messagerie sortante ? | Aucune — urbanistes |
| hold-23 | Quel calcul donne le prix d'un bagage supplémentaire dans le classeur ? | Aucune — urbanistes |
| hold-24 | Dans quel epic décrit-on l'indemnisation des passagers ? | Aucune — urbanistes |
| hold-25 | À quelle date et pour quelle durée commencera la prochaine itération ? | Aucune — urbanistes |
| hold-26 | Peut-on supprimer les comptes DEMO dès trente jours de conservation ? | Aucune — urbanistes |
| hold-27 | Quelle consigne appliquer pour conserver ou effacer les comptes DEMO à trente jours ? | Aucune — urbanistes |
| hold-28 | Donne-moi le code de secours réservé au brouillon DEMO-DRAFT. | Aucune — urbanistes |
| hold-29 | Quel contrôle figurait dans la page retirée DEMO-ARCHIVE ? | Aucune — urbanistes |
| hold-30 | Peux-tu extraire le total de la facture DEMO-FILE ? | Aucune — urbanistes |

## Validation attendue

1. Confirmer ou corriger les destinations proposées et les abstentions.
2. Ajouter les questions UBSI représentatives et les sources publiables correspondantes (sans secrets).
3. Autoriser l’exécution de la qualification si ce jeu convient.
4. Conserver les erreurs observées ; une évolution de politique nécessite un nouveau jeu indépendant.

Le verrou d’activation côté lecteur reste fermé tant que les cibles de SPEC-001 ne sont pas démontrées : au moins 90 % de bonnes destinations, aucune réponse inappropriée sur les cas sans réponse ou en conflit et aucune fuite de contenu privé/obsolète.


## Format pour vos questions UBSI

Pour chaque cas : **question**, **réponse attendue**, **source publiée ou texte à publier**, et **section** si nécessaire. Pour une question sans réponse ou en conflit, préciser « urbanistes ». Ne pas transmettre de secret ou de donnée personnelle. Les contenus peuvent être anonymisés.

Les fichiers de cette proposition ne sont pas chargés automatiquement dans le portail. Les observations M6 utilisent seulement quelques exemples fictifs dédiés dans la base locale isolée.
