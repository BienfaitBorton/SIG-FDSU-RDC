# SIG-FDSU RDC - Rapport de correction

## Regression Dashboard / connexion base

Date : 2026-07-05

## Cause exacte

La regression venait de `dashboard/app.js` restaure avec :

```javascript
const DATA_MODE = 'json';
const API_BASE_URL = 'http://localhost:8001';
const LOCAL_JSON_MODE = DATA_MODE !== 'api';
```

Cette configuration forcait le dashboard en fallback JSON local avant tout appel a `GET /health`. Les fonctions de chargement des KPI, des listes metier et des couches cartographiques lisaient donc les rapports locaux au lieu des endpoints FastAPI, meme lorsque l'API et PostgreSQL etaient disponibles.

Le fichier `dashboard/serve_utf8.py` n'ecrit pas en base et n'est pas la cause directe : il sert uniquement les fichiers statiques. La regression fonctionnelle venait du mode client fige a `json`.

## Fichiers modifies

- `dashboard/app.js`
- `dashboard/README.md`
- `README.md`
- `PROJECT_MANAGEMENT/SPRINT_REPORTS/DB_CONNECTION_REGRESSION_FIX.md`

## Corrections realisees

- Passage de `DATA_MODE` a `auto`.
- Passage de `API_BASE_URL` a `http://127.0.0.1:8001`.
- Remplacement du mode local fige par une variable dynamique `LOCAL_JSON_MODE`.
- Ajout de `detectDataMode()` avant l'initialisation des modules.
- Test automatique de `GET /health` :
  - si `mode = db` et `status = ok`, le dashboard utilise FastAPI ;
  - sinon, il conserve le fallback JSON local.
- Ajout de `fetchApiJson()` pour centraliser les appels API.
- Affichage attendu restaure :
  - API : `Mode DB`
  - Base de donnees : `Connectée`
- Mise a jour de la documentation pour eviter de reintroduire `DATA_MODE = 'json'`.

## Endpoints verifies

- `GET http://127.0.0.1:8001/health`
- `GET http://127.0.0.1:8001/dashboard/summary`
- `GET http://127.0.0.1:8001/provinces?limit=500`
- `GET http://127.0.0.1:8001/territoires?limit=500`
- `GET http://127.0.0.1:8001/collectivites?limit=500`
- `GET http://127.0.0.1:8001/groupements?limit=500`
- `GET http://127.0.0.1:8001/localites?limit=500`
- `GET http://127.0.0.1:8001/map/layers/provinces?limit=5000`

## Tests effectues

- `GET /health` retourne `status = ok`, `mode = db`, `database = Connectée`.
- `GET /dashboard/summary` retourne :
  - provinces : 26
  - territories : 145
  - collectivites : 733
  - groupements : 1681
  - localites : 26710
- Listes API verifiees :
  - provinces : 26
  - territoires : 145
  - collectivites : 500 lignes sur la page demandee
  - groupements : 500 lignes sur la page demandee
  - localites : 500 lignes sur la page demandee
- Couche cartographique provinces : 26 features.
- Simulation de detection client :
  - `databaseConnected = true`
  - libelle API attendu : `Mode DB`
  - libelle base attendu : `Connectée`

## Limites

- Le navigateur integre Codex n'etait pas disponible dans cette session ; la validation visuelle a donc ete remplacee par des tests HTTP reels et une simulation de la logique client.
- `node --check` n'etait pas disponible sur la machine ; la verification JavaScript a ete faite par inspection ciblee et simulation de la detection.

## Confirmation

Le dashboard n'est plus bloque en `Mode JSON local`. Lorsque FastAPI repond sur `http://127.0.0.1:8001` avec `mode = db`, l'initialisation utilise les endpoints FastAPI et les KPI/listes metier sont rechargees depuis PostgreSQL, sans modification des donnees PostgreSQL.
