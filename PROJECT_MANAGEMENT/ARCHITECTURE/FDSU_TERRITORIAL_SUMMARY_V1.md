# Tableau de Synthèse Territoriale (TST) v1.0

**Branche** : `feature/smart-map-interactions`  
**Statut** : livrable pré-commit — **aucun commit automatique**

## Architecture

```
TerritorialSummary.mount(container, options)
        │
        ├── GET /api/territorial-summary/metrics
        ├── GET /api/territorial-summary/layer?level&metric&parent_id
        ├── GET /api/territorial-summary/entity?level&id&name
        └── GET /map/layers/provinces (géométries)
        │
        ├── TerritorialContext (session — conservation inter-modules)
        ├── SigMapTooltips / UxPremium / EdvsCharts
        └── Decision Workspace (trail aligné)
```

Cycle de vie obligatoire : `mount` → `update` → `resize` → `destroy` (map.remove, clear layers, abort fetch).

## Hiérarchie

RDC → Province → Territoire → (Collectivité / Groupement / Localité / Site — extensions futures)

## API composant

```js
TerritorialSummary.mount(container, {
  metric, level, parentId, context,
  onSelectionChange, preserveContext,
  showLegend, showKpis, allowDrilldown,
})
instance.update(options)
instance.resize()
instance.destroy()
```

## Métriques (sources réelles)

| ID | Source | Agrégation |
|----|--------|------------|
| priority | decision.fdsu_site_scores + sites | (critical+high)/scored × 100 |
| sites_fdsu | programs.fdsu_sites | COUNT par province |
| sites_priority | fdsu_site_scores | COUNT critical+high |
| needs | coverage aggregates | population_uncovered |
| coverage | coverage aggregates | covered/(covered+uncovered) |
| health | /api/health/statistics | by_province |
| ccn | /api/ccn/statistics | by_province |
| data_quality | disponibilité agrégats NCI | binaire (pas de score inventé) |

Absences → **« Données insuffisantes »**.

## Intégrations

| Module | Mode |
|--------|------|
| Centre de Décision (vue nationale) | Permanent |
| Salle de Pilotage DG | Permanent (remplace carte OSM vide) |
| Intelligence territoriale | Optionnel (bouton + drawer, exclusive vs carte TI) |

## Limites

- Drill-down géométrique territoires : liste + synthèse (polygones TI à brancher progressivement).
- Niveaux collectivité → site : structure prête via LEVELS / contexte, couche TST non encore peuplée.
- CCN `by_province` peut être DEMO — libellé source transparent.

## Extensions futures

- Polygones territoires/collectivités
- Heatmap NCI
- Export PDF synthèse
- Brancher CCN / Spatial Impact / Cartographie en mode drawer
