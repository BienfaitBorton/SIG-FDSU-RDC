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

## Lancement de l'API

1. Vérifier que la base de données est accessible et configurée.
2. Démarrer le serveur Uvicorn :

```bash
uvicorn api.main:app --reload
```

3. L'API sera disponible par défaut sur `http://127.0.0.1:8000`.
4. La documentation interactive peut être consultée sur `http://127.0.0.1:8000/docs`.

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
