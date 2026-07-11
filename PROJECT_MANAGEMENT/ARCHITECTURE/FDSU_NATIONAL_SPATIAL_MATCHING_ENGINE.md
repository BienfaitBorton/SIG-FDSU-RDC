# National Spatial Matching Engine (NSME)

**Version** : nsme-1.0.0
**Date** : 2026-07-11
**Branche** : `feature/smart-map-interactions`

## Question métier

> Quel actif FDSU répond à quels besoins territoriaux, pour quelle population, à quelle distance et avec quel impact attendu ?

## Architecture

| Couche | Rôle |
|--------|------|
| `analysis.spatial_relations` | SIE existant (site → télécom/santé/admin) — **non écrasé** |
| `analysis.asset_need_matches` | NSME — actifs ↔ besoins (NCI) |
| `analysis.matching_runs` | Journal d'exécution batch |
| `data/business/spatial_matching_rules.json` | Rayons / relations / confiance (configurables) |
| `api/services/spatial_matching_service.py` | Moteur métier |
| `/api/spatial-matching/*` | API |

## Sources

- Actifs : `programs.fdsu_sites`, CCN fichier démo, télécom/santé (relations dérivées)
- Besoins : `data/coverage/localities_uncovered.jsonl` (NCI) — **non modifiés**

## Relations

`SERVES_LOCALITY`, `IMPACTS_POPULATION`, `CONNECTS_CCN`, `NEAR_*`, `WITHIN_TERRITORY`, `CANDIDATE_FOR_MISSION`, `OVERLAPS_EXISTING_COVERAGE`

## Calcul

Priorité PostGIS pour persistance ; matching NCI fichier via équivalent `ST_DWithin` (haversine + rayon configurable).
Statuts d'impact : `calcule` / `estime` / `partiel` / `non_disponible`.

## Intégrations

- Territorial Intelligence → bloc `spatial_matching`
- Salle de Pilotage DG / EDVS → `spatial_matching.charts`
- Centre de Décision → actions « besoins desservis / population / carte / expliquer »
- Cartographie → couche `Correspondance Actifs ↔ Besoins`

## Refresh

`POST /api/spatial-matching/refresh` — **ciblé** (programme / province / territoire / actif).
Ne pas recalculer tout le pays à chaque requête lecture.

## Hors scope (volontaire)

- National Investment Simulator (préparé via actions `simulate_investment`)
- Second moteur de priorisation
