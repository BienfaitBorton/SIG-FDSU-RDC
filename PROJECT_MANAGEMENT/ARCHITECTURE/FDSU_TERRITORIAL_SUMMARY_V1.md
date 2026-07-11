# Tableau de Synthèse Territoriale (TST) v1.1

**Branche** : `feature/smart-map-interactions`  
**Statut** : livrable pré-commit — **aucun commit automatique**

## Cause v1.0 — disparition au drill-down

1. `build_territory_layer` renvoyait `geometry: null` pour tous les territoires.  
2. Le frontend appelait `state.layer.clearLayers()` puis affichait uniquement une liste.

Correction v1.1 : géométries via `/map/layers/territoires` (même source que la Cartographie nationale), contour parent conservé, transition sans carte vide.

## Architecture

```
TerritorialSummary.mount(container, options)
        │
        ├── GET /api/territorial-summary/metrics
        ├── GET /api/territorial-summary/layer?level&metric&parent_id&province&territory
        ├── GET /api/territorial-summary/entity?level&id&name
        └── Géométries : /map/layers/{provinces|territoires|collectivites|groupements|localites}
        │
        ├── TerritorialContext (session)
        ├── SigMapTooltips / UxPremium / EdvsCharts
        └── parentLayer (contour) + childLayer (choroplèthe) — une carte Leaflet
```

Cycle de vie : `mount` → `update` → `resize` → `destroy`.

## Réponse `/layer` (niveaux enfants)

```json
{
  "level": "territoire",
  "parent": { "id": "...", "name": "Haut-Lomami", "level": "province", "geometry": {} },
  "features": { "type": "FeatureCollection", "features": [] },
  "expected_count": 5,
  "geometry_count": 5,
  "geometry_status": "complete|partial|unavailable",
  "message": null
}
```

## Sources géométriques

| Niveau | Source | Type |
|--------|--------|------|
| Province | `/map/layers/provinces` | MultiPolygon |
| Territoire | `/map/layers/territoires` | Polygon |
| Collectivité / Secteur / Chefferie | `/map/layers/collectivites` | MultiPolygon |
| Groupement | `/map/layers/groupements` | Point |
| Localité | `/map/layers/localites` | Point |
| Site | panneau / Decision Workspace | — |

## Hiérarchie

RDC → Province → Territoire → Collectivité → Groupement → Localité → Site

## Limites

- Métriques chiffrées riches surtout province / territoire (NDCI, NCI) ; collectivités → souvent « Données insuffisantes ».
- Filtre province **strict** (pas de sous-chaîne) pour éviter Haut-Lomami ↔ Lomami.
- Sites : pas de couche TST dédiée (actions panneau).
- Haut-Lomami exemple : 5/6 territoires avec polygone (`partial` — ex. Kamina Ville sans limite).
