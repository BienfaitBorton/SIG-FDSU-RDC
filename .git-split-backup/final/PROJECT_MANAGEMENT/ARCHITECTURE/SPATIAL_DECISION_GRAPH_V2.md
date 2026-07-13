# Spatial Decision Graph (SDG) v2.1 — Analyse d’Impact Territorial

Correctif bloquant du raccordement et de l’expérience décideur.

## Cause du non-affichage v2.0 (diagnostic)

| Élément | Constat |
|---|---|
| Renderer visible | Ancien `renderMapFromNsme` (points rouges + traits orange) + légende `#ux-legend-dxl` « Actif / Besoin-localité » (ux-premium) |
| Nouveau SDG | Scripts chargés dans `index.html`, API OK, mais fallback silencieux vers NSME et légende générique restaient dominants |
| Dossier de décision | Montait encore `renderMapFromNsme` indépendamment du SDG |
| Correction | Un seul renderer officiel : `SpatialDecisionGraph` v2.1 sur `#spatial-impact` **et** carte du dossier ; plus de fallback NSME silencieux ; suppression de `#ux-legend-dxl` |

## Renderer unique

- Route : `#spatial-impact/site/{id}` et alias `#analyse-impact-territorial/...`
- Action dossier / Decision Workspace / Salle DG → même parcours
- `renderMapFromNsme` conservé uniquement pour le détail de couverture territoriale (`#coverage-detail`), pas pour l’Analyse d’Impact Territorial

## Contrat API (`sdg-2.1.0`)

- `center`, `nodes`, `edges` (typés + `nsme_trace`)
- `categories` avec `status`: `active` | `empty` | `future`
- `decision_summary`, `kpis`, `missing_data`, `why_panel`
- `score_contribution.status` ∈ mapped | proxy | unavailable (jamais inventé)
- Présentation : `/presentation`

## UI v2.1

Trois zones : filtres (gauche) · carte + KPI + légende (centre) · détail (droite).

Symbologie `L.divIcon`, filtres sans recréer Leaflet, tooltips métier, mode Présentation DG.

## Données honnêtes

Aucun objet fictif. Catégories sans référentiel → `future` + « Non disponible ». Catégories intégrées sans match → `empty` / zéro calculé.
