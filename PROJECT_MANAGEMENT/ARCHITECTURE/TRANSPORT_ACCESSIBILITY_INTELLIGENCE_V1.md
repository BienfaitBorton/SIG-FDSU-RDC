# Transport & Accessibility Intelligence v1.0

**Branche** : `feature/smart-map-interactions`  
**Statut** : livrable pré-commit — **aucun commit automatique**  
**API** : `/api/transport`

## Principes

1. Le KMZ brut (`data/raw/Routes_principales.shp.kmz`) **n’est jamais servi** en production.
2. Source d’exploitation exclusive : `transport.routes` (PostGIS, EPSG:4326).
3. Score d’accessibilité **entièrement documenté** (aucune formule cachée).
4. Intégration NDF, NSME, TST, Decision Engine, Scenarios, Workspace.

## Architecture

```
Routes_principales.shp.kmz (raw)
        │
        ▼
scripts/import_routes_principales_kmz.py
        ├── GeoJSON traité → data/sectoral/transport/processed/
        ├── Rapport qualité → data/sectoral/transport/quality/
        └── --db → transport.routes (PostGIS)
        │
        ├── /api/transport/*  (service + couche carte)
        ├── Accessibility Engine
        ├── NSME (NEAR_MAIN_ROAD / CORRIDOR / ACCESSIBILITY)
        ├── TST métrique accessibility
        └── Decision Engine critère routes
```

## Pipeline

```bash
python scripts/import_routes_principales_kmz.py           # parse + qualité + GeoJSON
python scripts/import_routes_principales_kmz.py --db      # + import PostGIS
python scripts/import_routes_principales_kmz.py --db --limit 500
```

Étapes : extract KML → parse LineString → CRS WGS84 → dédup `source_id` → contrôles géométrie / hors RDC / sans nom → tables PostGIS + index GIST.

## PostGIS

Schéma `transport` :

| Table | Rôle |
|-------|------|
| `routes` | Tronçons LineString + attributs métier |
| `import_runs` | Historique d’import |
| `quality_checks` | Contrôles qualité |
| `statistics` | Compteurs |

Index : GIST(`geom`), `type_route`, `nom`, unique partiel `source_id`.

## Score d’accessibilité

```
score = clamp(0, 100, distance_component + type_component)
```

| Distance | Points |
|----------|--------|
| ≤ 500 m | 80 |
| ≤ 2 km | 65 |
| ≤ 5 km | 50 |
| ≤ 15 km | 35 |
| > 15 km | 20 |

| Type | Points |
|------|--------|
| Route primaire / Voie rapide | 20 |
| Route secondaire | 12 |
| Autre | 5 |

API : `GET /api/transport/formula`

## Qualité

Contrôles : géométries invalides, doublons, sans nom, hors RDC (bbox), tronçons < 5 m.  
`GET /api/transport/quality`

## NDF

Référentiel `transport` : **active** — relations avec administratif, sites FDSU, télécom, CCN, santé, TST, priorisation, NSME.

## NSME

Relations : `NEAR_MAIN_ROAD`, `WITHIN_ROAD_CORRIDOR`, `ROAD_ACCESSIBILITY`.

## TST

Métrique `accessibility` — moyenne des scores sites par province (échantillon borné). Absences → « Données insuffisantes ».

## Decision Engine

Critère `routes` (poids 0.10) avec justification explicite distance + type.

## UX

Couche cartographique **Routes principales** (checkbox Cartographie) — tooltips Nom / Type / Longueur / Source / État. Une seule instance Leaflet par conteneur.

## Limites

- Agrégat provincial borné (performance KNN).
- Territoires TST : métrique accessibilité encore partielle.
- Attributs OSM souvent `NC` (état / revêtement).
- Source OSM — pas un inventaire officiel RTNC exclusif.

## Feuille de route

| Phase | Contenu |
|-------|---------|
| v1.1 | Précalcul accessibilité en table dédiée |
| v1.2 | Corridors multi-routes + isochrones |
| v1.3 | Couches secondaires / pistes |
