# SIG-FDSU RDC - Sprint 3.1

## Navigation metier et base de connaissances territoriale

Date: 2026-07-04

## Fichiers modifies

- `dashboard/index.html`
- `dashboard/app.js`
- `dashboard/styles.css`
- `api/main.py`
- `docs/SPRINT_3_1_RAPPORT_REALISATION.md`
- `PROJECT_MANAGEMENT/SPRINT_REPORTS/SPRINT_3.1_REPORT.md`
- `PROJECT_MANAGEMENT/BACKLOG.md`
- `PROJECT_MANAGEMENT/ROADMAP.md`
- `PROJECT_MANAGEMENT/CHANGELOG.md`
- `PROJECT_MANAGEMENT/MILESTONES.md`
- `PROJECT_MANAGEMENT/KNOWN_ISSUES.md`
- `PROJECT_MANAGEMENT/IDEAS.md`
- `PROJECT_MANAGEMENT/DECISIONS.md`
- `PROJECT_MANAGEMENT/RELEASE_NOTES.md`

## Realisations

- Les compteurs du dashboard restent des portes d'entree vers des listes, jamais directement vers une fiche.
- Le workbench dashboard dispose de recherche, filtres province/territoire, tri, pagination, selection simple, ouverture fiche, affichage carte, export CSV et impression.
- La recherche globale ouvre une liste de resultats navigable avant la fiche.
- Les fiches metier proposent les formats PDF navigateur, Word, Excel, CSV, JSON, GeoJSON, KML et KMZ sous forme KML pret a compresser.
- Les fiches affichent un socle "Base de connaissances territoriale" avec les champs de preparation Sprint 3.1.
- Les donnees absentes dans les fiches passent par le libelle explicite "Donnée non encore renseignée".
- Les couleurs officielles Zones FDSU sont appliquees selon le sprint: OT jaune, CE rose, SD vert sombre, ND gris olive, ET bleu.
- La documentation projet obligatoire est initialisee dans `PROJECT_MANAGEMENT/`.

## Nouveaux endpoints API

- `GET /entities/search?q=&layer=&skip=&limit=`
- `GET /provinces/{entity_id}`
- `GET /territoires/{entity_id}`
- `GET /collectivites/{entity_id}`
- `GET /groupements/{entity_id}`
- `GET /localites/{entity_id}`

## Endpoints renforces

- `GET /sites?skip=&limit=`
- `GET /missions?skip=&limit=`

## Nouveaux composants ou comportements UI

- Commandes de liste: export, impression, tri et taille de page.
- Selection simple de ligne sans ouverture automatique.
- Double clic ou bouton "Ouvrir fiche" pour ouvrir la fiche.
- Bouton "Voir carte" par ligne.
- Resultats de recherche globale convertis en liste metier filtrable.
- Section "Base de connaissances territoriale" dans la fiche.

## Tests realises

- Compilation Python de `api/main.py`.
- Verification statique des fonctions Sprint 3.1 dans `dashboard/app.js`.
- Appels FastAPI directs sur `search_entities`, `read_province_detail` et pagination JSON.
- Verification `git diff --check`.

## Reste a developper pour Sprint 3.2

- Synchronisation carte-table-fiche complete avec filtrage cartographique des resultats de recherche.
- Exports KMZ natifs compresses et exports PDF serveur.
- Persistance des profils territoriaux en tables dediees.
- Endpoints de listes avec enveloppe uniforme `{items,total,skip,limit}` pour toutes les entites.
- Autocomplete API branche sur le dashboard en mode `DATA_MODE = api`.
- Tests navigateur multi-resolution lorsque le navigateur integre est disponible.

## Rapport projet obligatoire

- Rapport complet: `PROJECT_MANAGEMENT/SPRINT_REPORTS/SPRINT_3.1_REPORT.md`
- Version projet: `0.8.4-sprint-3.1`
