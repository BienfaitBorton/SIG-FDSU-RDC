# SDG — Cohérence des statuts et branchements (v1.0)

## Objectif

Aligner Spatial Decision Graph, KPI du dossier de décision, NSME et référentiels sectoriels autour d’un **modèle unique de statuts métier**, conforme Data First et No Black Box.

## Modèle officiel des statuts

| Code | Libellé UI | Condition |
|------|------------|-----------|
| `operational` | Opérationnel | Référentiel disponible, recherche exécutée, relations trouvées |
| `empty` | Aucun objet trouvé | Référentiel disponible, recherche exécutée, résultat réellement nul |
| `integration_pending` / `integrating` | En cours d’intégration | Référentiel absent / non importé |
| `error` | Erreur d’intégration | Échec technique réel empêchant l’analyse |
| `partial` | Partiel | Référentiel présent mais couverture / attributs incomplets (explication obligatoire) |
| `demonstration` | Démonstration / partiel | Jeu DEMO (ex. CCN) |

**Interdit :**

- « Anomalie d’intégration » pour un branchement manquant connu (désormais `partial` avec message explicite, ou branchement réel) ;
- « Partiellement intégré » comme formule générique ;
- zéro sans explication ;
- « Non disponible » pour un rayon déjà utilisé par le graphe.

Chaque statut doit indiquer : ce qui existe, ce qui a été exécuté, ce qui manque, l’impact décisionnel.

## Règles Data First / zéro / nearest context

1. Si le référentiel existe, il doit être interrogé.
2. Un `0` n’est affiché que si la recherche a été exécutée ; la note explique le rayon et le volume du référentiel.
3. Si aucun objet n’est dans le rayon, exposer le **plus proche** (`nearest_context`) avec nom, type, opérateur, distance.
4. Distinguer nœuds télécom (`telecom.infrastructure`) et tronçons fibre (`telecom.network_lines`).
5. CCN DEMO : message « Aucun CCN du jeu DEMO trouvé… » — jamais un 0 ambigu.

## Source unique KPI = graphe

Contrat partagé exposé dans le payload SDG :

```json
{
  "domain": "telecom",
  "status": "operational|empty|integration_pending|error|partial|demonstration",
  "reference_available": true,
  "search_executed": true,
  "relation_count": 0,
  "nearest_context": {},
  "radius": {},
  "source": "...",
  "confidence": "...",
  "message": "...",
  "business_impact": "..."
}
```

Champs associés : `domain_statuses[]`, `radii`, `categories[].nearest_context`, `kpis[].note` / `kpis[].detail`.

## Branchements NSME ajoutés / consolidés

| Domaine | Recherche | Relations |
|---------|-----------|-----------|
| Sites FDSU | `match_site_to_neighbor_fdsu` | `NEAR_FDSU_SITE`, `SAME_PROGRAM`, `COMPLEMENTS_FDSU_SITE`, `OVERLAPPING_SERVICE_AREA` |
| Télécom | `match_site_to_telecom` → PostGIS | `NEAR_FIBER`, `NEAR_BACKBONE`, `NEAREST_TELECOM_INFRA`, `NEAREST_FIBER_LINE` |
| Routes | `match_site_to_roads` (existant) | `NEAR_MAIN_ROAD`, `ROAD_ACCESSIBILITY`, `WITHIN_ROAD_CORRIDOR` |
| CCN | `match_site_to_near_ccn` | `NEAR_CCN` (+ marqueur DEMO) |
| Santé / Localités | existants | inchangés sur le principe |

Rayons configurables dans `data/business/spatial_matching_rules.json` :

- principal site : 15 km
- santé : 5 km
- routes : 50 km (corridor 2 km)
- télécom : 25 km
- fibre (tronçon) : 5 km
- sites FDSU voisins : 25 km
- CCN DEMO : 10 km

## Domaines encore réellement en cours d’intégration

- Éducation
- Énergie
- Marchés / économie
- CCN production (seul le jeu DEMO est disponible)
- Services administratifs : dérivation NCI partielle (pas de référentiel admin PostGIS dédié)

## Limites

- Les relations `SAME_PROGRAM` / complémentarité sont limitées au rayon de proximité pour éviter d’inonder le graphe.
- Les marqueurs `*_SEARCH_EXECUTED` ne sont pas rendus comme arêtes cartographiques (`suppress_graph_edge`).
- Les messages techniques (NSME, SQL, FK) restent hors vue principale ; le détail technique peut exposer la méthode de calcul.

## Fichiers clés

- `api/services/spatial_matching_service.py`
- `api/services/telecom_service.py`
- `api/services/spatial_decision_graph_service.py`
- `dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js`
- `tests/test_spatial_decision_graph.py`
- `tests/e2e/sdg-domain-status-coherence.spec.js`
