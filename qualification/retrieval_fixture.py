"""Versioned synthetic French corpus and independent query wordings for M0.

No actual UBSI business rules, member identities or private documents are used.
Calibration and held-out questions are generated before any model scoring.
"""

import json
from pathlib import Path


TOPICS = [
    ("invite", "faq", "Comment obtenir un compte ?", "Seul un administrateur peut inviter un membre par email. Le destinataire choisit son mot de passe en ouvrant le lien d'invitation.",
     "Qui peut m'envoyer une invitation pour rejoindre le portail ?", "Je rejoins l'équipe : comment ouvrir mon accès au site ?"),
    ("password", "faq", "Mot de passe oublié", "Le lien Mot de passe oublié sur la page de connexion permet de demander un email de récupération. Le lien est à usage unique et expire après une heure.",
     "J'ai perdu mon mot de passe, que dois-je faire ?", "Je ne me souviens plus de mon secret de connexion : comment le remplacer ?"),
    ("draft", "spec", "Publication des modifications", "Enregistrer un brouillon ne modifie pas la page publiée. Un administrateur doit cliquer sur Publier pour rendre ses changements visibles aux lecteurs.",
     "Un brouillon enregistré est-il immédiatement visible par l'équipe ?", "J'ai sauvegardé une correction, pourquoi les membres voient-ils encore l'ancien texte ?"),
    ("carry", "story", "Clôturer les travaux inachevés", "Lors de la clôture d'un sprint, les stories inachevées sont explicitement remises dans le backlog ou reportées dans un sprint planifié. Le choix est conservé dans l'historique.",
     "Que faire des stories non terminées quand on clôture un sprint ?", "Une tâche reste en cours à la fin de l'itération : où la placer ?"),
    ("original", "spec", "Téléchargement des documents", "Le bouton Télécharger l'original fournit le fichier importé sans en modifier les octets. L'aperçu est un fichier dérivé distinct.",
     "Puis-je récupérer le fichier exactement comme il a été importé ?", "Le téléchargement conserve-t-il le document source intact ?"),
    ("formula", "faq", "Formule sans résultat enregistré", "L'aperçu Excel lit les résultats enregistrés sans recalculer les formules. Si un résultat manque, ouvrir le classeur dans Excel, le recalculer, l'enregistrer puis le réimporter.",
     "Pourquoi mon aperçu affiche-t-il Résultat non disponible pour une formule ?", "Comment faire apparaître le total calculé manquant dans le classeur importé ?"),
    ("archive", "spec", "Archivage des contenus", "Un contenu archivé disparaît de la consultation et de la recherche des lecteurs. Les administrateurs conservent son historique et peuvent restaurer une ancienne version en brouillon.",
     "Les lecteurs peuvent-ils encore consulter un contenu archivé ?", "Que devient une page dans la recherche quand un admin l'archive ?"),
    ("epic", "epic", "Epics transverses", "Un epic peut concerner plusieurs applications. Chaque user story appartient à un seul epic et indique un sous-ensemble des applications de cet epic.",
     "Un epic peut-il couvrir deux applications différentes ?", "Peut-on rattacher un même besoin majeur à plusieurs applications ?"),
    ("editor", "spec", "Rédaction des spécifications", "Les spécifications utilisent un éditeur visuel avec titres, listes, tableaux, liens et blocs de code. Les administrateurs rédigent ces pages directement dans le site.",
     "Comment insérer un tableau dans une spécification ?", "Quel outil permet de structurer une page de spec avec titres et code ?"),
    ("reader", "faq", "Droits des lecteurs", "Un membre avec le rôle utilisateur lit les contenus publiés et utilise le chatbot. Seuls les administrateurs peuvent créer, modifier et publier des contenus.",
     "Avec un rôle utilisateur, puis-je modifier une user story ?", "Mon compte de lecteur permet-il de créer un epic ?"),
    ("urbanists", "faq", "Question sans réponse", "Si aucune réponse adaptée n'est trouvée, le chatbot affiche : Aucune réponse adaptée n'a été trouvée. Allez en parler aux urbanistes.",
     "À qui m'adresser lorsque le chatbot ne trouve aucune réponse ?", "Que m'indique l'assistant lorsqu'il n'a pas de réponse dans les pages ?"),
    ("pages", "spec", "Consulter les diagrammes PDF", "Un document PDF peut comporter plusieurs pages. L'aperçu permet de passer d'une page à l'autre et de zoomer sans quitter le site.",
     "Comment lire la deuxième page d'un PDF sur le portail ?", "Peut-on parcourir toutes les pages d'un diagramme PDF dans le site ?"),
    ("history", "spec", "Anciennes versions", "Les administrateurs consultent l'historique des versions publiées et restaurent une version dans un brouillon. Les lecteurs voient seulement la version actuellement publiée.",
     "Qui peut consulter les anciennes versions des specs ?", "Comment un admin reprend-il une ancienne version sans la publier immédiatement ?"),
    ("hidden", "faq", "Feuilles masquées Excel", "Les feuilles masquées du classeur sont consultables dans l'aperçu avec une indication Masquée. Tous les onglets restent accessibles dans le sélecteur de feuilles.",
     "Où retrouver les onglets masqués d'un classeur ?", "Une feuille cachée dans Excel est-elle consultable sur le site ?"),
    ("failure", "spec", "Remplacement de fichier en échec", "Une nouvelle révision de fichier ne peut pas être publiée si son aperçu a échoué. La version précédemment publiée reste disponible pendant la correction du remplacement.",
     "Si l'aperçu du nouveau fichier échoue, que voient les lecteurs ?", "L'ancien document reste-t-il lisible quand son remplacement est invalide ?"),
    ("one-sprint", "spec", "Sprint actif", "Les sprints sont communs au projet. Un seul sprint peut être actif à un instant donné. L'activation d'un deuxième sprint est refusée tant que le premier reste actif.",
     "Peut-on avoir deux sprints actifs en même temps ?", "Combien d'itérations peut-on démarrer simultanément dans le projet ?"),
    ("drawio", "spec", "Diagrammes draw.io", "Les administrateurs importent les fichiers draw.io. Les lecteurs consultent les pages du diagramme et le téléchargent. La modification du dessin se fait dans un outil externe.",
     "Peut-on éditer directement un dessin draw.io dans le portail ?", "Faut-il retourner dans draw.io pour modifier le diagramme importé ?"),
    ("cross", "epic", "Sprints et applications", "Un sprint commun peut regrouper des user stories de plusieurs applications. Le filtre Application aide à retrouver les stories concernées sans créer de sprint séparé.",
     "Un sprint peut-il regrouper des stories de plusieurs applications ?", "Comment voir les tâches d'une application dans une itération transverse ?"),
]

# Every pair has different wording; the held-out side is never used to choose thresholds.
NEGATIVES = [
    ("Quel temps fera-t-il demain à Lyon ?", "Va-t-il pleuvoir à Paris demain ?", "unknown"),
    ("Quel restaurant choisir ce soir ?", "Où réserver un repas pour vendredi ?", "unknown"),
    ("Quel est le budget annuel du projet ?", "Combien coûte le projet UBSI cette année ?", "unknown"),
    ("Quelle est l'adresse SMTP de l'hébergement ?", "Quel serveur de messagerie doit-on configurer ?", "unknown"),
    ("Quelle formule calcule la taxe sur les billets ?", "Quel taux de TVA utiliser dans mon tableau Excel ?", "keyword_overlap"),
    ("Quel epic couvre le remboursement des billets ?", "Quelle story détaille les bagages perdus ?", "keyword_overlap"),
    ("Combien de jours dure notre prochain sprint ?", "Quelle est la date du prochain démarrage de sprint ?", "keyword_overlap"),
    ("Quel est le délai de suppression des comptes DEMO ?", "Après combien de jours efface-t-on les comptes DEMO ?", "conflict"),
    ("Les comptes DEMO doivent-ils être supprimés au bout de trente jours ?", "Est-il interdit d'effacer les comptes DEMO après trente jours ?", "conflict"),
    ("Quel est le code de secours DEMO-DRAFT ?", "Où trouver le code de secours du brouillon DEMO-DRAFT ?", "draft_only"),
    ("Quel est le mot de contrôle DEMO-ARCHIVE ?", "Quel mot de contrôle était dans DEMO-ARCHIVE ?", "archived_only"),
    ("Quel est le montant de la facture DEMO-FILE ?", "Combien indique la facture importée DEMO-FILE ?", "file_only"),
]


def fixture():
    sources = [{"id": key, "kind": kind, "title": title, "text": text, "state": "published", "revision": 1, "current_revision": 1}
               for key, kind, title, text, _, _ in TOPICS]
    sources.extend([
        {"id": "conflict-a", "kind": "faq", "title": "Suppression des comptes DEMO", "text": "Les comptes DEMO doivent être supprimés après trente jours.", "state": "published", "revision": 1, "current_revision": 1},
        {"id": "conflict-b", "kind": "spec", "title": "Suppression des comptes DEMO", "text": "Les comptes DEMO ne doivent pas être supprimés après trente jours.", "state": "published", "revision": 1, "current_revision": 1},
        {"id": "private-draft", "kind": "spec", "title": "Code de secours DEMO-DRAFT", "text": "Le code de secours DEMO-DRAFT est FICTIF-123.", "state": "draft", "revision": 1, "current_revision": None},
        {"id": "archive-only", "kind": "faq", "title": "Mot de contrôle DEMO-ARCHIVE", "text": "Le mot de contrôle DEMO-ARCHIVE est FICTIF-456.", "state": "archived", "revision": 1, "current_revision": 1},
        {"id": "file", "kind": "document", "title": "Facture DEMO-FILE", "text": "La facture DEMO-FILE indique 123 euros fictifs.", "state": "published", "revision": 1, "current_revision": 1},
        {"id": "stale", "kind": "faq", "title": "Mot de passe oublié", "text": "Les anciens liens expirent après dix jours. Cette version est obsolète.", "state": "published", "revision": 1, "current_revision": 2},
    ])
    splits = {}
    for split, position in [("calibration", 4), ("held_out", 5)]:
        questions = [{"question": topic[position], "expected": topic[0], "category": "answerable"} for topic in TOPICS]
        questions.extend({"question": row[0 if split == "calibration" else 1], "expected": None, "category": row[2]} for row in NEGATIVES)
        splits[split] = questions
    return {"synthetic": True, "sources": sources, **splits}


if __name__ == "__main__":
    path = Path(__file__).with_name("retrieval-fixture.json")
    path.write_text(json.dumps(fixture(), ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {path.name}: 30 calibration + 30 held-out questions.")
