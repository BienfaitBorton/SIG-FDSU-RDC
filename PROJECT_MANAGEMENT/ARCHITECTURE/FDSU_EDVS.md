# SIG-FDSU RDC — Executive Data Visualization System (EDVS) v1

**Statut :** Framework opérationnel  
**Date :** 10 juillet 2026  
**UI :** `#salle-pilotage`  
**API :** `/api/executive/*`

## Architecture

```
dashboard/modules/shared/executive-dashboard/
  executive-colors.js      # Charte officielle
  executive-icons.js
  executive-utils.js       # Cache + format
  executive-kpi.js         # KPI + sparkline
  executive-cards.js       # Ranking, alertes, timeline, recommandations
  executive-charts.js      # Stacked, radar, gauge, waterfall, treemap, heatmap
  executive-layout.js      # Ratio 30/30/20/20 + Mode Présentation
  executive-dashboard.js   # Salle de Pilotage DG
  executive-dashboard.css
```

## Charte

| Couleur | Signification |
|---|---|
| Vert | Positif / opérationnel / confiance élevée |
| Orange | Attention / priorité élevée |
| Rouge | Critique / alerte |
| Bleu | Information stratégique |
| Gris | Indisponible / non sourcé |
| Jaune | Partiel / estimé / démonstration |

## Mode Présentation

Barre persistante ← Retour / Quitter + ESC (règle UX_NO_DEAD_ENDS).

## Consommation

Master Registry · CCN · Decision Engine · Territorial Intelligence · Knowledge Hub · Doctrines
