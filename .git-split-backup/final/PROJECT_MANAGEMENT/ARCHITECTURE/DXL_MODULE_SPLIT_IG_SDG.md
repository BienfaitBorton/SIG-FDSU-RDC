# DXL Module Split — Integrity Gate vs Spatial Decision Graph

**Date :** 2026-07-12  
**Objectif :** commits indépendants et `git revert` sûr.

## Architecture

```
index.html
  ├─ dxl-core.js                    → window.DxlCore          (socle partagé)
  ├─ decision-error-handler.js      → window.DecisionErrorHandler   [IG]
  ├─ decision-case-controller.js    → window.DecisionCaseController [IG]
  ├─ spatial-impact-controller.js   → window.SpatialImpactController [SDG]
  └─ decision-experience.js         → orchestrateur mince (routes / bindEvents)
```

## Propriété

| Module | Sprint | Responsabilité |
|---|---|---|
| `decision-error-handler.js` | Integrity Gate | humanizeFetchError, businessErrorHtml |
| `decision-case-controller.js` | Integrity Gate | load dossier `#decision-case` |
| `spatial-impact-controller.js` | SDG v2.1 | load spatial-impact, mount SDG, coverage-detail |
| `dxl-core.js` | Socle DXL (prérequis) | state, fetch, map Leaflet, renderers de sections |
| `decision-experience.js` | Socle DXL | hash routing, actions toolbar |

## Couplage éliminé

- `DecisionCaseController` **n’appelle plus** `SpatialDecisionGraph`.
- Il appelle uniquement `SpatialImpactController.mountOnCaseMap(...)` si présent.
- Sans le module SDG : `ensureMap()` seul — dossier reste utilisable.
- Sans le module IG errors : fallback minimal dans `DxlCore.tracedFetch`.

## Revert

- `git revert` du commit SDG → retire `spatial-impact-controller.js` + SDG assets → dossier IG continue.
- `git revert` du commit IG → retire error-handler + case-controller (+ backend IG) → spatial-impact peut encore monter si le socle reste.
