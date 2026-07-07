# SIG-FDSU RDC

SIG-FDSU RDC est un système d'information géographique dédié au référentiel administratif et aux sites du projet FDSU en République démocratique du Congo.

## Architecture

- API FastAPI exposant les points de terminaison REST.
- SQLAlchemy + GeoAlchemy2 pour la gestion des données spatiales et relationnelles.
- PostgreSQL avec extension PostGIS pour le stockage des géométries.
- Structure modulaire : `api/` pour routes, schémas et services ; `app/` pour configuration, base de données et importateurs.

## Prérequis

- Python 3.13+ (compatible avec les dépendances listées).
- PostgreSQL 15+ installé.
- PostGIS installé sur la base de données PostgreSQL.
- Un environnement virtuel Python recommandé.

## Installation

1. Cloner le dépôt :

```bash
git clone <url-du-repo>
cd SIG-FDSU-RDC
```

2. Créer et activer un environnement virtuel :

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

4. Configurer la base de données PostgreSQL et activer PostGIS.

### Configuration (`.env`)

Copier le modèle et ajuster si nécessaire :

```powershell
Copy-Item .env.example .env
```

Variables principales (voir `.env.example`) :

| Variable | Rôle |
|----------|------|
| `DATABASE_URL` | Connexion PostgreSQL/PostGIS |
| `DATA_MODE=json` | Mode démonstration — API sert les rapports JSON locaux (défaut) |
| `DATA_MODE=db` | Mode production locale — API lit/écrit PostgreSQL/PostGIS |

Le fichier `.env` est chargé automatiquement au démarrage de l'API (`app/config.py`). Les variables déjà définies dans le shell priment sur `.env`.

## Démarrage rapide (Windows)

Depuis la racine du projet, après création de l'environnement virtuel et installation des dépendances :

```powershell
.\start_sig.ps1
```

Le script `start_sig.ps1` :

- vérifie la présence de `.venv`, `api\main.py` et `dashboard\serve_utf8.py` ;
- ouvre **deux fenêtres PowerShell** (API + dashboard) pour consulter les logs ;
- affiche les URLs utiles ;
- ouvre automatiquement le dashboard dans le navigateur.

URLs locales :

- **Dashboard** : http://127.0.0.1:8000
- **API Docs** : http://127.0.0.1:8001/docs

## Lancement de l'API

1. Vérifier que la base de données est accessible et configurée.
2. Démarrer le serveur Uvicorn :

```bash
uvicorn api.main:app --reload
```

3. L'API sera disponible par défaut sur `http://127.0.0.1:8000`.
4. La documentation interactive peut être consultée sur `http://127.0.0.1:8000/docs`.

## SIG-FDSU RDC v0.8.0 - Modes JSON et PostgreSQL/PostGIS

Le dashboard conserve deux modes et demarre par defaut en detection automatique :

- `DATA_MODE = 'auto'` dans `dashboard/app.js` : detection de `GET /health` et utilisation de FastAPI si `mode = db`.
- `DATA_MODE = 'json'` dans `dashboard/app.js` : lecture directe des rapports JSON locaux.
- `DATA_MODE = 'api'` dans `dashboard/app.js` : lecture via FastAPI sur `API_BASE_URL = 'http://127.0.0.1:8001'`.

L'API conserve aussi un fallback JSON et peut lire PostgreSQL/PostGIS via la variable d'environnement `DATA_MODE`.

Créer un fichier `.env` local à partir de `.env.example` ou définir :

```powershell
$env:DATABASE_URL="postgresql://postgres:test123@localhost:5432/sig_fdsu_rdc"
$env:DATA_MODE="db"
```

### Installer PostgreSQL/PostGIS

Installer PostgreSQL et PostGIS, puis créer la base :

```powershell
createdb -U postgres sig_fdsu_rdc
```

Initialiser PostGIS et le schéma :

```powershell
psql -U postgres -d sig_fdsu_rdc -f database/init.sql
psql -U postgres -d sig_fdsu_rdc -f database/schema.sql
```

Charger les référentiels JSON existants :

```powershell
python database/seed_from_json.py
```

Le seed lit uniquement `data/reports`, ignore les doublons et produit un rapport `inserted / ignored / errors`.

### Lancer en mode API PostgreSQL/PostGIS

```powershell
$env:DATA_MODE="db"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8001
```

Endpoints métier v0.8.0 :

- `GET /health`
- `GET /dashboard/summary`
- `GET /provinces`
- `GET /territoires`
- `GET /collectivites`
- `GET /groupements`
- `GET /localites`
- `GET /sites`
- `GET /map/layers/{layer_name}`
- `GET /entities/{layer}/{id}`

### Lancer le dashboard

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

Ouvrir `http://localhost:8000/dashboard/index.html#dashboard`.

## Tests

Exécuter les tests avec Pytest :

```bash
pytest
```

## Import des référentiels

Le projet inclut des importateurs et des scripts pour charger les référentiels administratifs et les données SIG.

- `app/importer.py` et `app/importer_clean.py` pour le traitement des importations.
- `scripts/import_referentiel.py` et `scripts/import_fdsu.py` peuvent être utilisés pour charger des données.

## Structure des dossiers

- `api/`
  - `routes/` : définitions des routes FastAPI.
  - `schemas/` : schémas Pydantic et modèles de données.
  - `services/` : logique métier et accès aux données.
  - `middlewares/` : gestion des erreurs et middleware.
- `app/`
  - `config.py` : configuration de l'application.
  - `database.py` : connexion et sessions SQLAlchemy.
  - `models.py` : définitions des entités de base de données.
  - `importer.py`, `importer_clean.py` : importation des données.
- `database/` : scripts SQL et schémas de base de données.
- `scripts/` : utilitaires de déploiement et d'import.
- `tests/` : suite de tests pour les entités et l'API.

---

## Remarques

- Ce dépôt est centré sur une API SIG avec des données spatiales PostGIS et des entités administratives.
- Le code métier n'a pas été modifié.
