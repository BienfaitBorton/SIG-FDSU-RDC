# SPRINT 3.1 REPORT - SIG-FDSU RDC

## Identification

- Sprint: 3.1
- Version: 0.8.4-sprint-3.1
- Date: 2026-07-04
- Theme: Navigation metier et base de connaissances territoriale
- Cadre documentaire: `docs/ARCHITECTURE_FONCTIONNELLE_v1.0.md`, `docs/SCHEMA_DIRECTEUR_SIG_FDSU_v1.0.md`, `docs/CHARTE_NATIONALE_DES_DONNEES_FDSU_v1.0.md`, `docs/MASTER_DATA_MODEL_v1.0.md`

## Objectifs du sprint

- Transformer les compteurs Dashboard en portes d'entree vers des listes metier.
- Imposer le parcours `Liste > Selection > Fiche`.
- Ajouter recherche, tri, filtres, pagination, export et impression aux listes.
- Preparer le socle de base de connaissances territoriale.
- Ajouter les endpoints API necessaires a la recherche et aux fiches.
- Maintenir la coherence avec les documents officiels sans modifier l'architecture generale.

## Fonctionnalites realisees

- Les compteurs Dashboard ouvrent des listes.
- Le workbench Dashboard gere recherche, filtres province/territoire, tri, pagination, selection simple, double clic, ouverture fiche, affichage carte, export CSV et impression.
- La recherche globale ouvre une liste de resultats au lieu d'ouvrir directement une fiche.
- Les fiches proposent PDF navigateur, Word, Excel, CSV, JSON, GeoJSON, KML et KMZ sous forme KML pret a compresser.
- Les fiches integrent une section "Base de connaissances territoriale".
- Les donnees absentes sont affichees avec `Donnée non encore renseignée`.
- Les couleurs officielles Zones FDSU Sprint 3.1 sont appliquees.

## Fichiers crees

- `PROJECT_MANAGEMENT/BACKLOG.md`
- `PROJECT_MANAGEMENT/ROADMAP.md`
- `PROJECT_MANAGEMENT/CHANGELOG.md`
- `PROJECT_MANAGEMENT/MILESTONES.md`
- `PROJECT_MANAGEMENT/KNOWN_ISSUES.md`
- `PROJECT_MANAGEMENT/IDEAS.md`
- `PROJECT_MANAGEMENT/DECISIONS.md`
- `PROJECT_MANAGEMENT/RELEASE_NOTES.md`
- `PROJECT_MANAGEMENT/SPRINT_REPORTS/SPRINT_3.1_REPORT.md`
- `docs/SPRINT_3_1_RAPPORT_REALISATION.md`

## Fichiers modifies

- `api/main.py`
- `dashboard/app.js`
- `dashboard/index.html`
- `dashboard/styles.css`

## Nouvelles tables PostgreSQL

- Aucune nouvelle table PostgreSQL creee dans Sprint 3.1.
- Les profils territoriaux sont prepares cote UI/API et devront etre persistants lors du Sprint 3.3.

## Nouveaux endpoints FastAPI

- `GET /entities/search?q=&layer=&skip=&limit=`
- `GET /provinces/{entity_id}`
- `GET /territoires/{entity_id}`
- `GET /collectivites/{entity_id}`
- `GET /groupements/{entity_id}`
- `GET /localites/{entity_id}`

## Endpoints FastAPI renforces

- `GET /sites?skip=&limit=`
- `GET /missions?skip=&limit=`

## Nouveaux composants Dashboard

- Commandes de liste: export, impression, tri et taille de page.
- Selection simple de ligne.
- Double clic et bouton "Ouvrir fiche".
- Bouton "Voir carte" par ligne.
- Resultats de recherche globale convertis en liste metier.
- Section "Base de connaissances territoriale" dans la fiche.

## Tests effectues

- Compilation Python: `python -m py_compile api\main.py`.
- Verification directe des fonctions API:
  - `read_provinces_json(skip=0, limit=5)` retourne 5 lignes.
  - `search_entities(q='kinshasa', skip=0, limit=3)` retourne 90 resultats au total et 3 items pagines.
  - `read_province_detail('KINSHASA')` retourne une fiche.
- Verification statique des fonctions Dashboard ajoutees.
- Verification `git diff --check`.

## Anomalies corrigees

- Compteur ouvrant directement une fiche: corrige par la liste metier.
- Recherche globale ouvrant directement une fiche: corrige par liste filtrable.
- Couleurs ND/ET non conformes a la demande Sprint 3.1: corrige.

## Limitations restantes

- Synchronisation complete carte-table-fiche-recherche non finalisee.
- Autocomplete API non branche au Dashboard en mode `DATA_MODE = api`.
- KMZ natif non compresse cote navigateur.
- PDF serveur non implemente.
- Profils territoriaux non persistants en PostgreSQL.

## Risques identifies

- Coexistence de routes detail ajoutees dans `api/main.py` avec les routeurs CRUD existants.
- Gros referentiels JSON charges en memoire pour la recherche.
- Tests navigateur non executes dans cette session.

## Dette technique eventuelle

- Uniformiser les endpoints de listes avec une enveloppe commune `{items,total,skip,limit}`.
- Centraliser la recherche dans un service dedie.
- Ajouter des tests d'integration Dashboard/API.
- Remplacer l'export KMZ de transition par une generation archivee native.

## Performances

- Les listes Dashboard restent paginees cote interface.
- L'endpoint `/entities/search` limite les resultats renvoyes avec `skip` et `limit`.
- Risque actuel: la recherche parcourt encore les referentiels JSON en memoire; une indexation ou une recherche base/API sera necessaire pour les volumes definitifs.

## Recommandations

- Prioriser Sprint 3.2 sur la synchronisation carte-table-fiche-recherche.
- Ajouter des tests API et Dashboard automatises.
- Preparer une migration PostgreSQL pour `territorial_profiles`.
- Conserver le principe `Liste > Selection > Fiche` comme regle UX obligatoire.

## Dependances pour le sprint suivant

- Disponibilite d'un navigateur de test ou d'un runner Playwright.
- Decision sur le schema PostgreSQL des profils territoriaux.
- Choix technique pour les exports serveur PDF/KMZ.
- Stabilisation de la convention de reponse API paginee.

## Taux d'avancement estime du projet

- Phase 3: 35%.
- Projet global SIG-FDSU RDC: 45%.

## Estimation de la prochaine version

- Version suivante estimee: 0.8.5-sprint-3.2.
- Objectif: synchronisation Dashboard/API/Carte et autocomplete universel.
