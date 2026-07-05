# Dashboard SIG-FDSU RDC

Ce dossier contient l'interface graphique du SIG-FDSU RDC.

## Structure

- `index.html` : page principale.
- `styles.css` : styles visuels.
- `app.js` : navigation client-side et chargement des donnees.
- `serve_utf8.py` : serveur statique UTF-8 pour le dashboard.

## Lancer le dashboard

Depuis la racine du depot :

```powershell
python dashboard/serve_utf8.py
```

Puis ouvrir :

```text
http://127.0.0.1:8000/index.html#dashboard
```

## Mode de donnees

Le dashboard detecte automatiquement FastAPI/PostgreSQL et conserve le fallback JSON local uniquement si l'API n'est pas disponible.

Configuration attendue dans `dashboard/app.js` :

```javascript
const DATA_MODE = 'auto';
const API_BASE_URL = 'http://127.0.0.1:8001';
```

- `DATA_MODE = 'auto'` : teste `GET /health` et utilise FastAPI si `mode = db`.
- `DATA_MODE = 'json'` : force les fichiers `data/reports/*.json`.
- `DATA_MODE = 'api'` : force FastAPI sur `API_BASE_URL`.

## Lancer l'API

Depuis la racine du depot :

```powershell
$env:DATA_MODE="db"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8001
```

Endpoints utilises par le dashboard :

- `GET /health`
- `GET /dashboard/summary`
- `GET /provinces`
- `GET /territoires`
- `GET /territories`
- `GET /collectivites`
- `GET /groupements`
- `GET /localites`
- `GET /map/layers/{layer_name}`
