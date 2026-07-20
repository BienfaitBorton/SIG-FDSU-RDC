# Diagnostic BAKI — Localités visibles 26 vs analysées 13

> Audit **lecture seule** — aucune correction métier. Site `#decision-case/site/30?program_code=sites_40`.

- **Branche / HEAD** : `feature/smart-map-interactions` / `03c2ed690bb41acabe0455340e78ef5c737d073b`
- **Site** : BAKI (id=30)
- **Coordonnées** : -5.896159999999999, 12.43504
- **Endpoint graphe** : `GET /api/spatial-decision-graph/site/30?program_code=sites_40`

## 1. ROOT_CAUSE

Le compteur UI « Localités visibles » utilise visibleObjectsRegistry.localities.visible = drawableNodes + drawableEdges. Pour BAKI: 13 nœuds + 13 arêtes SERVES_LOCALITY = 26. « Localités analysées » / population comptent uniquement les nœuds category=localities avec population > 0 sourcée (13/13).

Ce n’est **pas** 13 localités uniques affichées deux fois via deux référentiels.
C’est un **double comptage structurel nœud + arête** dans le registre de visibilité UI.

## Pipeline documenté

```
NCI localities_uncovered.jsonl
  → NSME match_site_to_uncovered_localities (SERVES_LOCALITY)
  → SDG build_graph : 1 node category=localities + 1 edge SERVES_LOCALITY par match
  → API /api/spatial-decision-graph/site/{id}
  → Dashboard SpatialDecisionGraph
       • visibleObjectsRegistry.localities.visible = nodes_drawables + edges_drawables  → 13+13=26
       • computePopulationSummary(nodes category=localities, pop>0 + source)           → 13 / 13 829
```

### Fonctions UI exactes

| Indicateur | Fonction | Fichier |
|---|---|---|
| Localités visibles = 26 | `rebuildVisibleObjectsRegistry()` → `visible = visibleNodes + visibleEdges` puis `currentPopulationSummary()` lit `visibleObjectsRegistry.localities.visible` | `dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js` |
| Localités analysées = 13 | `computePopulationSummary()` → `documentedLocalities` (nœuds `category==='localities'` avec `localityHasValidPopulation`) | idem |
| Population documentée = 13 829 | somme des `node.population` des localités documentées | idem |

### Règles

- **Filtre spatial** : relations NSME `SERVES_LOCALITY` (localités non couvertes NCI dans le rayon de service).
- **Déduplication population** : clé `need_id || locality_id || locality_code || official_code || id` (`localityStableId`).
- **Population valide** : source présente (`source_label|referential|source|source_document`) **et** `population` numérique `> 0`.
- **Pas de rayon distinct** carte vs population : même graphe SDG.

## 2–5. Compteurs

| Métrique | Valeur |
|---|---:|
| VISIBLE_LOCALITIES (UI) | **26** |
| UNIQUE_VISIBLE_LOCALITIES (nœuds) | **13** |
| ANALYZED_LOCALITIES | **13** |
| POPULATION_TOTAL | **13829** |
| DUPLICATE_COUNT (nœuds) | **0** |
| CROSS_SOURCE_DUPLICATES | **0** |
| POPULATION_MISSING_COUNT | **0** |
| POPULATION_JOIN_FAILURE_COUNT | **0** |
| COVERED_UNCOVERED_OVERLAP | **0** |
| SPATIAL_FILTER_DIFFERENCE | **non** (même graphe) |
| RADIUS_DIFFERENCE | **non** |

## Hypothèse ×2 (26 → 13 unique)

| Déduplication | Résultat |
|---|---:|
| Identité canonique (`need_id`) | **13** |
| Nom normalisé | **13** |
| Nom + proximité ≤ 50 m | **13** |
| Formule UI nodes+edges | **13+13=26** |

L’hypothèse « 13 localités × 2 sources » est **infirmée** pour les nœuds.
La réduction 26→13 s’explique entièrement par **13 arêtes + 13 nœuds**.

## Covered / Uncovered

- Les 13 localités proviennent exclusivement de **Localités non couvertes (NCI)** (`need_id` préfixe `NCI-UNC`).
- Aucun objet `covered` n’apparaît dans le graphe BAKI pour cette catégorie.
- Pas de chevauchement covered/uncovered détecté sur ce site.

## Population

- Somme brute des 13 nœuds : **13829**
- Somme après dédup `need_id` : **13829** (identique)
- Somme Dashboard : **13829**
- Les 13 arêtes n’ajoutent **aucune** population au calcul.
- `POPULATION_PRESENT` (nœuds) = 13 ; `POPULATION_MISSING` = 0 ; `DUPLICATE_POPULATION_RECORD` = 0

## Carte vs moteur démographique

| Couche | Objets |
|---|---|
| Leaflet markers (localities) | 13 nœuds Point |
| Leaflet polylines (SERVES_LOCALITY) | 13 arêtes |
| Compteur « Localités visibles » | **26** = markers + lines |
| Calcul démographique | **13** nœuds seulement |

Pas de concaténation `referential_localities + coverage_localities` sur BAKI : une seule source NCI uncovered.

## Tableau des 26 objets visibles (registre UI)

| # | kind | display_name | canonical_id / need_id | source | lon | lat | dist_m | pop | coverage | map_role | in_pop | exclusion |
|---:|---|---|---|---|---:|---:|---:|---:|---|---|---|---|
| 1 | node | Part1_23453_NewSite_1_808_50006 | NCI-UNC-5CC5A1DA62 | Localités non couvertes (NCI) | 12.499649 | -5.910817 | 7329.6 | 932.0 | uncovered | marker_locality | True | — |
| 2 | edge | Part1_23453_NewSite_1_808_50006 | NCI-UNC-5CC5A1DA62 | Localités non couvertes (NCI) | 12.499649 | -5.910817 | 7329.6 | 932.0 | uncovered | relation_line SERVES_LOCALITY | False | edge SERVES_LOCALITY — inclus dans le compteur visible (nodes+edges), exclu du calcul population |
| 3 | node | 200060 | NCI-UNC-B6D4333CBB | Localités non couvertes (NCI) | 12.5013135 | -5.9069949 | 7428.6 | 2051.0 | uncovered | marker_locality | True | — |
| 4 | edge | 200060 | NCI-UNC-B6D4333CBB | Localités non couvertes (NCI) | 12.5013135 | -5.9069949 | 7428.6 | 2051.0 | uncovered | relation_line SERVES_LOCALITY | False | edge SERVES_LOCALITY — inclus dans le compteur visible (nodes+edges), exclu du calcul population |
| 5 | node | Part1_23453_NewSite_1_718_51677 | NCI-UNC-76F6A4481A | Localités non couvertes (NCI) | 12.395508 | -5.826899 | 8856.3 | 973.0 | uncovered | marker_locality | True | — |
| 6 | edge | Part1_23453_NewSite_1_718_51677 | NCI-UNC-76F6A4481A | Localités non couvertes (NCI) | 12.395508 | -5.826899 | 8856.3 | 973.0 | uncovered | relation_line SERVES_LOCALITY | False | edge SERVES_LOCALITY — inclus dans le compteur visible (nodes+edges), exclu du calcul population |
| 7 | node | Part1_23453_NewSite_1_718_52085 | NCI-UNC-8502A6DA94 | Localités non couvertes (NCI) | 12.45198 | -5.814344 | 9288.5 | 1601.0 | uncovered | marker_locality | True | — |
| 8 | edge | Part1_23453_NewSite_1_718_52085 | NCI-UNC-8502A6DA94 | Localités non couvertes (NCI) | 12.45198 | -5.814344 | 9288.5 | 1601.0 | uncovered | relation_line SERVES_LOCALITY | False | edge SERVES_LOCALITY — inclus dans le compteur visible (nodes+edges), exclu du calcul population |
| 9 | node | Part1_23453_NewSite_1_808_51673 | NCI-UNC-75B12768F4 | Localités non couvertes (NCI) | 12.51356 | -5.936088 | 9753.6 | 345.0 | uncovered | marker_locality | True | — |
| 10 | edge | Part1_23453_NewSite_1_808_51673 | NCI-UNC-75B12768F4 | Localités non couvertes (NCI) | 12.51356 | -5.936088 | 9753.6 | 345.0 | uncovered | relation_line SERVES_LOCALITY | False | edge SERVES_LOCALITY — inclus dans le compteur visible (nodes+edges), exclu du calcul population |
| 11 | node | Part1_23453_NewSite_1_719_50008 | NCI-UNC-B7CE0B7205 | Localités non couvertes (NCI) | 12.486938 | -5.806823 | 11473.3 | 1205.0 | uncovered | marker_locality | True | — |
| 12 | edge | Part1_23453_NewSite_1_719_50008 | NCI-UNC-B7CE0B7205 | Localités non couvertes (NCI) | 12.486938 | -5.806823 | 11473.3 | 1205.0 | uncovered | relation_line SERVES_LOCALITY | False | edge SERVES_LOCALITY — inclus dans le compteur visible (nodes+edges), exclu du calcul population |
| 13 | node | 200059 | NCI-UNC-72DFDFFFA0 | Localités non couvertes (NCI) | 12.5384188 | -5.9216587 | 11780.4 | 1178.0 | uncovered | marker_locality | True | — |
| 14 | edge | 200059 | NCI-UNC-72DFDFFFA0 | Localités non couvertes (NCI) | 12.5384188 | -5.9216587 | 11780.4 | 1178.0 | uncovered | relation_line SERVES_LOCALITY | False | edge SERVES_LOCALITY — inclus dans le compteur visible (nodes+edges), exclu du calcul population |
| 15 | node | Part1_23453_NewSite_1_808_51029 | NCI-UNC-107B0E838E | Localités non couvertes (NCI) | 12.538785 | -5.923053 | 11857.9 | 664.0 | uncovered | marker_locality | True | — |
| 16 | edge | Part1_23453_NewSite_1_808_51029 | NCI-UNC-107B0E838E | Localités non couvertes (NCI) | 12.538785 | -5.923053 | 11857.9 | 664.0 | uncovered | relation_line SERVES_LOCALITY | False | edge SERVES_LOCALITY — inclus dans le compteur visible (nodes+edges), exclu du calcul population |
| 17 | node | 200069 | NCI-UNC-3A68907BDA | Localités non couvertes (NCI) | 12.3815827 | -5.8008939 | 12131.8 | 1647.0 | uncovered | marker_locality | True | — |
| 18 | edge | 200069 | NCI-UNC-3A68907BDA | Localités non couvertes (NCI) | 12.3815827 | -5.8008939 | 12131.8 | 1647.0 | uncovered | relation_line SERVES_LOCALITY | False | edge SERVES_LOCALITY — inclus dans le compteur visible (nodes+edges), exclu du calcul population |
| 19 | node | Part1_23453_NewSite_1_715_50009 | NCI-UNC-16F83F2900 | Localités non couvertes (NCI) | 12.378937 | -5.800701 | 12295.6 | 690.0 | uncovered | marker_locality | True | — |
| 20 | edge | Part1_23453_NewSite_1_715_50009 | NCI-UNC-16F83F2900 | Localités non couvertes (NCI) | 12.378937 | -5.800701 | 12295.6 | 690.0 | uncovered | relation_line SERVES_LOCALITY | False | edge SERVES_LOCALITY — inclus dans le compteur visible (nodes+edges), exclu du calcul population |
| 21 | node | Part1_23453_NewSite_1_716_51673 | NCI-UNC-0A79D6067D | Localités non couvertes (NCI) | 12.403363 | -5.7805 | 13329.6 | 392.0 | uncovered | marker_locality | True | — |
| 22 | edge | Part1_23453_NewSite_1_716_51673 | NCI-UNC-0A79D6067D | Localités non couvertes (NCI) | 12.403363 | -5.7805 | 13329.6 | 392.0 | uncovered | relation_line SERVES_LOCALITY | False | edge SERVES_LOCALITY — inclus dans le compteur visible (nodes+edges), exclu du calcul population |
| 23 | node | 200073 | NCI-UNC-87192D4413 | Localités non couvertes (NCI) | 12.5047517 | -5.79351 | 13774.9 | 1008.0 | uncovered | marker_locality | True | — |
| 24 | edge | 200073 | NCI-UNC-87192D4413 | Localités non couvertes (NCI) | 12.5047517 | -5.79351 | 13774.9 | 1008.0 | uncovered | relation_line SERVES_LOCALITY | False | edge SERVES_LOCALITY — inclus dans le compteur visible (nodes+edges), exclu du calcul population |
| 25 | node | Part1_23453_NewSite_1_809_50003 | NCI-UNC-47DD134552 | Localités non couvertes (NCI) | 12.565989 | -5.897516 | 14484.6 | 1143.0 | uncovered | marker_locality | True | — |
| 26 | edge | Part1_23453_NewSite_1_809_50003 | NCI-UNC-47DD134552 | Localités non couvertes (NCI) | 12.565989 | -5.897516 | 14484.6 | 1143.0 | uncovered | relation_line SERVES_LOCALITY | False | edge SERVES_LOCALITY — inclus dans le compteur visible (nodes+edges), exclu du calcul population |

## Tableau des 13 localités démographiques

| # | name | need_id | population | distance_m | source |
|---:|---|---|---:|---:|---|
| 1 | Part1_23453_NewSite_1_808_50006 | NCI-UNC-5CC5A1DA62 | 932 | 7329.6 | Localités non couvertes (NCI) |
| 2 | 200060 | NCI-UNC-B6D4333CBB | 2051 | 7428.6 | Localités non couvertes (NCI) |
| 3 | Part1_23453_NewSite_1_718_51677 | NCI-UNC-76F6A4481A | 973 | 8856.3 | Localités non couvertes (NCI) |
| 4 | Part1_23453_NewSite_1_718_52085 | NCI-UNC-8502A6DA94 | 1601 | 9288.5 | Localités non couvertes (NCI) |
| 5 | Part1_23453_NewSite_1_808_51673 | NCI-UNC-75B12768F4 | 345 | 9753.6 | Localités non couvertes (NCI) |
| 6 | Part1_23453_NewSite_1_719_50008 | NCI-UNC-B7CE0B7205 | 1205 | 11473.3 | Localités non couvertes (NCI) |
| 7 | 200059 | NCI-UNC-72DFDFFFA0 | 1178 | 11780.4 | Localités non couvertes (NCI) |
| 8 | Part1_23453_NewSite_1_808_51029 | NCI-UNC-107B0E838E | 664 | 11857.9 | Localités non couvertes (NCI) |
| 9 | 200069 | NCI-UNC-3A68907BDA | 1647 | 12131.8 | Localités non couvertes (NCI) |
| 10 | Part1_23453_NewSite_1_715_50009 | NCI-UNC-16F83F2900 | 690 | 12295.6 | Localités non couvertes (NCI) |
| 11 | Part1_23453_NewSite_1_716_51673 | NCI-UNC-0A79D6067D | 392 | 13329.6 | Localités non couvertes (NCI) |
| 12 | 200073 | NCI-UNC-87192D4413 | 1008 | 13774.9 | Localités non couvertes (NCI) |
| 13 | Part1_23453_NewSite_1_809_50003 | NCI-UNC-47DD134552 | 1143 | 14484.6 | Localités non couvertes (NCI) |

## Correspondance 26 → 13

Chaque localité apparaît exactement **deux fois** dans le compteur visible :
1. nœud `localities:NCI-UNC-…` (marker)
2. arête `edge:SERVES_LOCALITY:NCI-UNC-…` (ligne)

→ 13 paires (node, edge) = 26 objets compteur.

### Paires géographiquement proches (< 250 m) parmi les 13 nœuds

- `200059` vs `Part1_23453_NewSite_1_808_51029` — 160.2 m — class=NEAR_BUT_DISTINCT (need_ids distincts : NCI-UNC-72DFDFFFA0 / NCI-UNC-107B0E838E)

Ces paires restent des **localités distinctes** (pas de fusion).

## Sources exactes

- Fichier / pipeline : **NCI uncovered** (`Localités non couvertes (NCI)`)
- Service : `api/services/spatial_matching_service.py` → `SERVES_LOCALITY`
- Composition graphe : `api/services/spatial_decision_graph_service.py`
- Affichage compteurs : `spatial-decision-graph.js` (`rebuildVisibleObjectsRegistry`, `computePopulationSummary`)

## Conclusion métier

Les **13 829 habitants** sont la somme correcte des **13 localités NCI non couvertes** liées à BAKI.
L’affichage « 26 localités visibles » **surestime** le nombre de localités en comptant aussi les **13 relations** cartographiques.
Les fichiers population/coverage disposent bien de populations : elles sont toutes exploitées (13/13).
Aucun correctif n’a été appliqué dans cet audit.

## Verdict

**E — Cause mixte / structurelle (à détailler)** :

- Pas A (26 localités distinctes dont 13 sans pop) — les 13 nœuds ont tous une population.
- Pas B (doublons multisources 13×2) — les 13 `need_id` sont uniques ; la « duplication » est **nœud+arête**.
- Pas C (échec de jointure population) — 0 échec.
- Pas D (rayons différents carte/moteur) — même graphe.
- **E** : comptage UI `nodes + edges` (H) + libellé « Localités visibles » qui mélange objets cartographiques et localités métier.

---

## Console finale

```
BAKI_SITE_ID=30
VISIBLE_OBJECTS=26
UNIQUE_VISIBLE_LOCALITIES=13
ANALYZED_LOCALITIES=13
POPULATION_DOCUMENTED=13829
EXACT_DUPLICATES=0
CROSS_SOURCE_DUPLICATES=0
POPULATION_MISSING=0
POPULATION_JOIN_FAILURES=0
COVERED_UNCOVERED_OVERLAP=0
RADIUS_MAP=NSME SERVES_LOCALITY (rayon règles spatiales / uncovered localities)
RADIUS_POPULATION=identiques aux nœuds localities visibles (pas de rayon distinct)
ROOT_CAUSE=Le compteur UI « Localités visibles » utilise visibleObjectsRegistry.localities.visible = drawableNodes + drawableEdges. Pour BAKI: 13 nœuds + 13 arêtes SERVES_LOCALITY = 26. « Localités analysées » / population comptent uniquement les nœuds category=localities avec population > 0 sourcée (13/13).
VERDICT=E
```
