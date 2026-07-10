# FDSU National Coverage Intelligence (NCI)

## Objectif

Constituer le **Référentiel National des Besoins Numériques**, patrimoine distinct du **Référentiel National des Actifs**.

Le système compare désormais :

| Patrimoine | Contenu |
|---|---|
| Actifs | Sites, CCN, programmes, partenaires, missions |
| Besoins (NCI) | Population, localités non couvertes, priorités, distances, infrastructures, catégories |

Ces données **ne sont pas des investissements** : elles représentent les besoins nationaux.

## Architecture

```
data/raw/*.xlsx (originaux conservés)
        │
        ▼
scripts/import_national_coverage.py
        │
        ▼
data/coverage/
  ├── nci_config.json          # NDCI + CDQS configurables
  ├── localities_uncovered.jsonl
  ├── localities_covered.jsonl
  ├── aggregates.json          # national / province / territoire + NDCI
  ├── quality_report.json
  └── manifest.json
        │
        ▼
api/services/coverage_intelligence_service.py
        │
        ├── /api/coverage/*
        ├── Knowledge Hub (domain national_coverage)
        ├── Territorial Intelligence (section coverage)
        ├── Explainable Decision Engine (needs_intelligence)
        └── EDVS / Salle de Pilotage DG
```

## Modèle métier

### Localité (besoin)

- `id`, `name`, `latitude`, `longitude`, `coords_valid`
- `coverage_status` : `uncovered` | `covered`
- `priority` : High / Medium / Low (invalid → `invalid`)
- `population`, `distance_km`
- `province`, `territoire`, `fdsu_zone`
- `categorie` (A–E, >10000) — fichier non couvertes uniquement
- `infra_name`, `infra_type`, `infra_distance_km`
- `data_quality` : Coverage Data Quality Score (CDQS)

### Agrégat territorial

- populations couverte / restante
- localités couvertes / non couvertes
- priorités, catégories, distance moyenne
- **NDCI** (National Digital Coverage Index)
- qualité moyenne des données

## Indices configurables

Fichier : `data/coverage/nci_config.json`

### NDCI (National Digital Coverage Index)

Pondérations par défaut :

- population 30 %
- priorité 25 %
- catégorie 15 %
- distance 15 %
- infrastructures 15 %

### CDQS (Coverage Data Quality Score)

Contrôles : coordonnées, territoire, province, population, priorité, catégorie, infrastructure.

## API

| Endpoint | Rôle |
|---|---|
| `GET /api/coverage` | Vue d'ensemble |
| `GET /api/coverage/statistics` | KPI nationaux |
| `GET /api/coverage/provinces` | Agrégats provinces |
| `GET /api/coverage/territories` | Agrégats + NDCI |
| `GET /api/coverage/localities` | Pagination / filtres |
| `GET /api/coverage/population` | Population couverte / restante |
| `GET /api/coverage/priority` | High / Medium / Low |
| `GET /api/coverage/categories` | Catégories |
| `GET /api/coverage/infrastructure` | Types d'infra |
| `GET /api/coverage/map` | GeoJSON progressif |
| `GET /api/coverage/explain` | Explicabilité |
| `GET /api/coverage/edvs` | Graphiques exécutifs |

## Intégrations

### Territorial Intelligence

Chaque profil territoire expose `sections.coverage` + `needs.coverage` :

- population couverte / non couverte
- localités couvertes / non couvertes
- catégories, priorités, distance moyenne
- NDCI, qualité données

### Decision Engine

Les dossiers site (`needs_intelligence`) et les recommandations TI utilisent :

population, priorité, distance, infrastructure, catégorie **en plus de** doctrine, matrice, sites, CCN.

### Knowledge Hub

Domaine `national_coverage` — expose les KPI NCI sans calculer de recommandation.

### Salle de Pilotage DG / EDVS

KPI nationaux, barres provinces, répartition High/Medium/Low, catégories, treemap, heatmap NDCI, waterfall couverture, radar besoins, sparklines.

## Performance

- Agrégats précalculés à l'import
- Cache mémoire invalidé sur mtime de `aggregates.json`
- Localités en JSONL + pagination (`limit` / `offset`)
- Carte progressive (filtre province/territoire recommandé)

## Pipeline

```powershell
python scripts/import_national_coverage.py
```

Les Excel officiels restent dans `data/raw/` (SHA-256 dans le manifeste).

## Principes

1. Ne pas traiter NCI comme un simple import Excel
2. Ne pas confondre besoins et actifs / investissements
3. Aucune valeur inventée
4. Pondérations NDCI/CDQS versionnées en JSON
5. Aucune régression sur Master Registry, CCN, TI, EDVS, Decision Engine
