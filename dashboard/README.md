# Dashboard SIG-FDSU RDC

Ce dossier contient l’architecture de l’interface graphique du SIG-FDSU RDC.

## Objectif

- page d’accueil professionnelle
- menu latéral
- barre supérieure
- zone centrale de contenu
- navigation entre les modules

## Structure

- `index.html` : page principale
- `styles.css` : styles visuels
- `app.js` : navigation client-side entre les modules

## Utilisation

Servir la racine du dépôt pour permettre au dashboard de lire les rapports JSON :

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

Puis ouvrir `http://localhost:8000/dashboard/index.html#dashboard`.

## Mode de données

Le dashboard v0.7.0 conserve le fallback JSON local et prépare un mode API optionnel.

Dans `dashboard/app.js` :

```javascript
const DATA_MODE = 'json';
const API_BASE_URL = 'http://localhost:8001';
```

- `DATA_MODE = 'json'` : lit les fichiers `data/reports/*.json` via le serveur statique.
- `DATA_MODE = 'api'` : interroge FastAPI sur `API_BASE_URL`.

## Lancer l'API expérimentale

Depuis la racine du dépôt :

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8001
```

Endpoints minimum exposés pour l'expérimentation :

- `GET /health`
- `GET /dashboard/summary`
- `GET /provinces`
- `GET /territories`
- `GET /collectivites`
- `GET /groupements`
- `GET /localites`
- `GET /sites`

L'API v0.7.0 lit les rapports JSON déjà générés et ne lance aucun import en base.
