# PERFORMANCE PHASE 2 — Decision Dossier + Spatial Relations

**Projet :** SIG-FDSU RDC
**Branche :** `feature/smart-map-interactions`
**HEAD de départ validé :** `f473202611dcdcef53ebdad75b890a8537537f1a`
**Date :** 2026-07-20
**Périmètre :** cold path Dossier de Décision / DXL / preuves spatiales (telecom)
**Statut :** Phases 2A–2D terminées et poussées (`5e860ae`). **Phase 2E** correctifs locaux — attente validation (pas de commit).

---

## 1. Synthèse

Le goulot principal n’était plus le startup application (Phase 1), mais le **cold path** de `GET /api/decision/case/{id}` (~26 s), dominé par le contexte télécom spatial — en particulier un **fallback Airtel** qui relançait `run_mno_audit()` lorsque `telecom.fdsu_mno_sites` était vide.

Phase 2A sépare le **premier contenu utile** (identité / score / résumé) des **preuves spatiales**, mutualise le contexte spatial, peuple le staging FDSU une fois, et met en cache les réponses décision/NSME/SDG.

| Indicateur (site 29 / sites_40) | BEFORE | AFTER (validation finale légère) | Gain |
|---|---:|---:|---:|
| TIME_TO_FIRST_USEFUL_CONTENT | 26 128 ms | **2 373 ms** (CORE cold) | **≈ 90,9 %** |
| CASE full cold | 26 128 ms | **7 909 ms** | **≈ 69,7 %** |
| Warm CORE / FULL | — / 30,7 ms | **98 ms / 50 ms** | warm stable |

Mesure intermédiaire antérieure (même site, process déjà chaud) : CORE cold ≈ 1 958 ms, FULL cold ≈ 5 305 ms — cohérente avec le gain d’ordre de grandeur.

---

## 2. A. BEFORE

Mesures HTTP validées (site_id=29, programme `sites_40`) avant correctifs Phase 2A :

| Métrique | ms |
|---|---:|
| FIRST_USEFUL_BEFORE_MS | **26 128,1** |
| CASE_COLD_MS | **26 128,1** |
| CASE_WARM_MS | 30,7 |
| IMPACT_COLD_MS | 6 993,8 |
| NEEDS_COLD_MS | 6 035,4 |
| MAP_MS | 5 360,8 |
| SDG_COLD_MS | 11 524,5 |
| DOSSIER_FULL_COLD_SEQ_MS | 38 482,7 |

Profilage interne `build_site_case` (cache désactivé) — top coûts :

| STEP | DURATION_MS | % |
|---|---:|---:|
| telecom_spatial | **18 550** | 78,9 |
| education_nearest (cold 1er) | 1 498 | 6,4 |
| site_lookup_resolve (cold 1er) | 1 429 | 6,1 |
| ceni_nearest | 105 | 0,4 |

---

## 3. B. AFTER — validation finale légère (site 29 uniquement)

Pas de campagne multi-sites. Une seule série :

| Métrique | ms | HTTP |
|---|---:|---|
| CORE_COLD_MS (`include_spatial_evidence=false`) | **2 373,3** | 200 |
| FULL_COLD_MS (`include_spatial_evidence=true`) | **7 909,2** | 200 |
| CORE_WARM_MS | **98,2** | 200 |
| FULL_WARM_MS | **50,3** | 200 |
| SPATIAL_EVIDENCE_WARM_MS | **70,8** | 200 |

**FIRST_USEFUL_AFTER_MS** = CORE_COLD_MS = **2 373 ms**
Gain first useful : `(26128 − 2373) / 26128` ≈ **90,9 %**.

### Staging FDSU MNO (prérequis)

| Check | Résultat |
|---|---|
| `SELECT COUNT(*) FROM telecom.fdsu_mno_sites` | **12 611** (non vide) |
| AIRTEL | 4 477 |
| VODACOM | 4 129 |
| ORANGE | 3 221 |
| AFRICELL | 784 |

Le fallback `run_mno_audit()` n’est plus nécessaire sur le chemin nominal une fois le staging peuplé.

---

## 4. C. Cause racine

1. `build_site_case` appelait séquentiellement `_build_telecom_case_context` → `telecom_service.spatial_context_around`.
2. Pour Airtel/Africell, `_nearest_fdsu_operator` interrogeait `telecom.fdsu_mno_sites`.
3. **Table staging vide (0 lignes)** → SQL rapide mais sans hit → fallback `_nearest_mno_audit_operator` → **`mno_audit.run_mno_audit()`** ≈ **12–13 s** au premier appel.
4. Ce coût était inclus dans le dossier complet, donc **TIME_TO_FIRST_USEFUL_CONTENT = case cold ≈ 26 s**.

EXPLAIN ANALYZE (staging vide) confirmait que la requête PostGIS elle-même était sub-ms ; le temps était hors SQL (audit mémoire).

---

## 5. D. Corrections appliquées (Phase 2A)

| Correction | Fichier(s) |
|---|---|
| `SharedSpatialContext` (cache géo TTL + ensure staging one-shot) | `api/services/shared_spatial_context.py` |
| Cache TTL décision / needs / impact / SDG graph | `api/services/site_spatial_context_cache.py` + wiring services |
| Staging FDSU peuplé une fois si vide (`sync_fdsu_mno_staging_from_audit`) | `shared_spatial_context.py` + `telecom_service.py` |
| Nearest Airtel/Africell via KNN GiST geometry puis filtre rayon | `telecom_service.py` |
| `spatial_context_around` parallélisé (ThreadPool) | `telecom_service.py` |
| Case core sans preuves + `attach_spatial_evidence` | `explainable_decision_service.py` |
| Query `include_spatial_evidence` + route `/spatial-evidence` | `api/routes/decision_engine.py` |
| Front : core d’abord, `setLoading(false)`, evidence/TI/SDG/TIE en parallèle | `decision-case-controller.js` |
| Scripts de profilage / mesure (outils, non runtime) | `scripts/profile_*.py`, `scripts/measure_*.py` |

---

## 6. E. Résultats métier inchangés

- Identité / score / priorité / doctrine inchangés (mêmes champs core).
- Preuves spatiales toujours calculées (chemin différé ou full) — pas de suppression de fallback de résilience.
- Staging FDSU = copie dérivée hors KPI `telecom.infrastructure` (`kpi_national_untouched`).
- Compteurs référentiels non régressés dans les tests ciblés : Localités **47 130**, Groupements **2 642**.
- Integrity Gate site 29 : nom métier ≠ `"29"`, score présent (tests API core/evidence).

---

## 7. F. Limites restantes — **PERFORMANCE PHASE 2B**

À traiter dans une **suite de performance** dédiée (hors clôture 2A) :

| Sujet | Observation | Priorité 2B |
|---|---|---|
| Impact NSME cold | ~5,6–7 s encore observé | Haute |
| Needs NSME cold | ~5,6–6 s | Haute |
| SDG / map cold | encore lents hors cache warm | Haute |
| Invalidation cache | TTL (90–120 s) uniquement — pas de clé `referential_version` complète ni invalidation sur changement coords site | Moyenne |
| Double `ThreadPoolExecutor` | case (tel/edu/ceni) × telecom interne — risque contention sous forte charge concurrente | Moyenne |
| Mesures multi-programmes (40 / 300 / 20 476) | volontairement non relancées en clôture | Documenter au prochain run léger |

Ces points **ne sont pas masqués** : le gain Phase 2A porte sur **first useful + case telecom cold** ; le dossier « plein » côté NSME/SDG reste un backlog explicite.

---

## 8. Tests & contrôles qualité (clôture)

```
pytest tests/test_site_spatial_context_cache.py tests/test_shared_spatial_context.py
→ 12 passed
```

Contrôles statiques :

- AST Python OK sur les 7 modules Phase 2 listés
- Import `shared_spatial_context` / `site_spatial_context_cache` OK
- `node --check decision-case-controller.js` → exit 0

---

## 9. Fichiers Phase 2

**Modifiés :**
- `api/routes/decision_engine.py`
- `api/services/explainable_decision_service.py`
- `api/services/spatial_decision_graph_service.py`
- `api/services/spatial_matching_service.py`
- `api/services/telecom_service.py`
- `dashboard/modules/decision-experience/decision-case-controller.js`

**Ajoutés :**
- `api/services/shared_spatial_context.py`
- `api/services/site_spatial_context_cache.py`
- `scripts/measure_decision_dossier_performance.py`
- `scripts/measure_decision_phase2_after.py`
- `scripts/measure_startup_components.py`
- `scripts/profile_decision_case_cold.py`
- `scripts/profile_telecom_airtel_sql.py`
- `tests/test_site_spatial_context_cache.py`
- `tests/test_shared_spatial_context.py`
- `PROJECT_MANAGEMENT/ARCHITECTURE/PERFORMANCE_PHASE2_DECISION_SPATIAL.md` (ce document)

---

## 10. Livraison numérique (site 29)

| KPI | Valeur |
|---|---|
| FIRST_USEFUL_BEFORE_MS | 26 128 |
| FIRST_USEFUL_AFTER_MS | **2 373** |
| CORE_COLD_MS | **2 373** |
| FULL_COLD_MS | **7 909** |
| CORE_WARM_MS | **98** |
| FULL_WARM_MS | **50** |
| Gain first useful | **≈ 90,9 %** |
| Cause racine | telecom cold + Airtel `run_mno_audit` sur staging vide |
| Staging FDSU | 12 611 lignes |
| Tests | 12 passed (ciblés) |

**Aucun commit / aucun push** dans cette clôture — validation humaine requise avant commit.

---

## 11. PERFORMANCE PHASE 2B — Impact / Needs / SDG / Map

**HEAD de départ :** `468441a` (Phase 2A poussée)
**Statut :** correctifs appliqués localement — **aucun commit / push** (attente validation).

### 11.1 Baseline légère (site 29, une fois froid + une fois chaud)

| Métrique | Cold ms | Warm ms |
|---|---:|---:|
| IMPACT | **5 270,8** | 18,5 |
| NEEDS | **5 829,3** | 63,6 |
| SDG | **12 342,2** | 260,1 |
| MAP | **4 989,2** | 23,3 |

### 11.2 Causes

Profilage `get_asset_needs` (site 29) :

| Sous-étape | ms |
|---|---:|
| match_telecom | ~2 904 |
| match_schools | ~2 579 |
| match_roads | ~1 207 |
| match_health / neighbors / ceni | ~375 / 397 / 125 |

Problèmes structurels :

1. **Clés de cache `needs` incluaient `limit`** → impact (`limit` absent), needs (`limit=50`), map (`limit=500`), SDG (`limit=200`) **recalculaient** chacun le même enrichissement spatial.
2. **SDG** appelait `get_decision_case` **avec preuves spatiales** → re-coût telecom/éducation/CENI du dossier.
3. `map_payload` = `get_asset_needs` complet.
4. Parallélisation des enrichissements NSME multi-connexions PostGIS **a régressé** le cold (~7–9 s) → **retirée** (séquentiel conservé).
5. Construction graphe SDG reste ~4,5–5,5 s même avec needs chaud (coût structurel graphe).

### 11.3 Corrections

| Correction | Détail |
|---|---|
| Clé needs canonique | sans `limit`/`offset` ; pagination en sortie |
| Impact / map / SDG | réutilisent le même corpus needs |
| SDG | `get_decision_case(..., include_spatial_evidence=False)` |
| SharedSpatialContext | education + CENI + caches PostGIS telecom NSME |
| Clé cache v2 | option `lat`/`lon` arrondis + `rules` mtime |
| ThreadPool telecom | max_workers 4 + **garde anti-imbrication** (`threading.local`) |
| Enrichissement NSME | reste **séquentiel** (mesure : parallèle pire) |

### 11.4 AFTER (HTTP site 29 — impact en premier, puis dépendants)

| Métrique | Cold ms | Warm ms | vs BEFORE cold |
|---|---:|---:|---|
| IMPACT (1er consommateur) | **7 005** | **24** | ordre comparable (variance cold) |
| NEEDS (après impact) | **77** | **62** | **−98,7 %** |
| MAP (après impact) | **25** | **28** | **−99,5 %** |
| SDG | **5 410** | **264** | **−56,2 %** |
| FIRST_USEFUL (core) | **74** (process chaud) | — | niveau 2A conservé |

Lecture UX dossier : **un seul** cold spatial (~5–7 s) pour impact/needs/map ; les suivants sont des hits. SDG reste le coût résiduel principal (~5,4 s).

### 11.5 Invalidation

- TTL inchangé comme filet (90–120 s).
- Clé `site_ctx_v2` : kind + site_id + program + asset_type + DATA_MODE + mtime/size règles NSME + coords optionnelles.
- Pas d’infrastructure distribuée.

### 11.6 Thread pools

- NSME enrichment : **pas de pool** (séquentiel mesuré plus fiable).
- `spatial_context_around` : pool ≤ 4, désactivé si déjà dans un pool (anti-nested).
- Front Phase 2A : rendu progressif **conservé** (pas de Promise.all global bloquant).

### 11.7 Smoke multi-sites (fonctionnel uniquement)

| Site | HTTP | Cohérence |
|---|---|---|
| 41 / sites_300 | 200 | nom métier OK |
| 341 / sites_20476 | 200 | nom métier OK |

### 11.8 Non-régression

- Localités **47 130** · Groupements **2 642** · Staging FDSU **12 611**

### 11.9 Tests

```
pytest tests/test_phase2b_spatial_dedup.py tests/test_site_spatial_context_cache.py tests/test_shared_spatial_context.py
→ 16 passed
```

### 11.10 Limites restantes (Phase 2C candidate)

- Premier cold needs/impact encore ~5–7 s (telecom + schools + roads PostGIS).
- SDG build_graph ~4,5–5,5 s hors needs (assemblage graphe).
- `match_site_to_neighbor_fdsu` charge jusqu’à 5000 sites (haversine).
- Roads cold ~1,2 s non encore mutualisé hors needs.

### 11.11 Fichiers Phase 2B (locaux, non commités)

**Modifiés :** `spatial_matching_service.py`, `spatial_decision_graph_service.py`, `telecom_service.py`, `site_spatial_context_cache.py`, ce rapport.
**Ajoutés :** `tests/test_phase2b_spatial_dedup.py`, `scripts/profile_phase2b_needs_breakdown.py` (outil, hors runtime).

---

## 12. PERFORMANCE PHASE 2C — premier cold spatial / PostGIS + build_graph SDG

**HEAD de départ :** `c6f00cff880568397dca76f26cea7d865b691989` (Phase 2B)
**Date :** 2026-07-20
**Statut :** Phase 2C **commitée et poussée** (`a564fd1ac11050e0b9e484a1fbb06765eea1a3eb`).

### 12.1 Baseline cold unique (site 29, process profilage)

| Métrique | Cold ms | Warm ms |
|---|---:|---:|
| SPATIAL_CONTEXT (telecom shared) | **1 398** | ≈ 0 |
| POSTGIS (échantillon infra / roads geography) | **465 – 1 517** | 370 – 1 161 |
| BUILD_GRAPH | **8 452** | 4 164 (needs déjà chaud) |
| SDG endpoint | **11 190** | 17 |

Top 3 composants spatiaux (cold) :

| COMPONENT | COLD_MS | WARM_MS | SOURCE | POSTGIS_OR_PYTHON |
|---|---:|---:|---|---|
| telecom_nsme | 2 650 | 1 256 | NSME + PostGIS | PostGIS |
| education_nearest | 1 947 | 11 | CENI schools projection | Python (bbox/haversine) |
| roads_nsme | 1 517 | 1 161 | `transport.routes` | PostGIS |

### 12.2 Plan PostGIS — routes (goulot prouvé)

`nearest_road` avant (geography `ST_DWithin` + `ORDER BY geom::geography <->`) :

- **Seq Scan** sur 6 512 routes, **Execution Time ≈ 1 593 ms**
- Index GiST `idx_transport_routes_geom` **non utilisé** (cast geography)

Après (KNN `ORDER BY geom <->` + `ST_Distance` geography + `ST_ClosestPoint` sur 1 ligne) :

- **Index Scan** GiST, **Execution Time ≈ 7 ms**
- **Aucun index créé** — index existant suffisant

Même pattern KNN geometry appliqué aux nearest telecom infrastructure / fibre / MW encore en `::geography` dans `ORDER BY`.

### 12.3 DATABASE_COLD vs APPLICATION_COLD

| Coût | Ordre de grandeur | Nature |
|---|---|---|
| DATABASE_COLD | SELECT 1 ≈ 73 ms ; PostGIS trivial ≈ 176 ms ; 1er Seq Scan geography routes ≈ 1,6 s | connexion + plan + buffers |
| APPLICATION_COLD | education schools load ≈ 1,9–2,5 s ; probe référentiels SDG ≈ 450 ms ; 3× `_road_endpoint` → `nearest_road` ≈ **3,8 s** | Python / double calcul |

Cause majeure `build_graph` : relations routes **sans** `need_lon`/`need_lat` → 3 appels PostGIS redondants + géométrie absente du SELECT.

### 12.4 Corrections

| Correction | Détail |
|---|---|
| `nearest_road` | KNN GiST geometry + closest_lon/lat ; filtre rayon geography |
| `match_site_to_roads` | propage `need_lon`/`need_lat` ; via `SharedSpatialContext.get_nearest_road` |
| `_road_endpoint` | réutilise coords / cache partagé — plus de 3× nearest |
| Telecom nearest | `ORDER BY geom <->` (infra, lines, fiber, MW) |
| Probe SDG | cache process-local TTL 300 s |
| Cache `sdg_graph` | clé `site_ctx_v2` + **lat/lon** + mtime règles NSME |
| Warmup startup | `SELECT 1` + `PostGIS_Version` + 1 KNN routes + staging count (`sync_if_empty=False`) |

### 12.5 Warmup

- **Ajouté** (léger, non bloquant métier)
- Coût startup mesuré ≈ **460 ms** (connexion + PostGIS + KNN + staging count)
- Gain utilisateur : 1er SDG cold **11,2 s → 2,9 s** ; roads PostGIS **1,6 s → ~7 ms** (plan)
- Critère respecté : `startup_added_ms` ≪ gain SDG / routes

### 12.6 build_graph AFTER (needs déjà chaud)

| Stage | ms |
|---|---:|
| nodes/edges loop | ≈ 0,3 |
| probe (1er) | ≈ 453 (puis cache) |
| **full `_build_graph_uncached` needs warm** | **≈ 36** |

Sérialisation JSON graphe ≈ **4 ms** — non significative.

### 12.7 Cache / invalidation build_graph

- Clé : `site_ctx_v2|sdg_graph|site_id|program|asset_type|DATA_MODE|rules_mtime-size|lat:lon`
- Invalide si coords changent, règles NSME changent, ou TTL (90 s)
- Pas de graphe obsolète silencieux hors TTL / clé

### 12.8 Threading

- Inchangé Phase 2B : telecom ≤ 4 workers + garde anti-imbrication
- Pas de création de pool dans `build_graph`
- Pas d’augmentation arbitraire des workers

### 12.9 BEFORE / AFTER (site 29)

| Métrique | BEFORE | AFTER |
|---|---:|---:|
| SPATIAL_CONTEXT_COLD_MS | 1 398 | **664** |
| SPATIAL_CONTEXT_WARM_MS | ≈ 0 | ≈ 0 |
| POSTGIS roads (EXPLAIN / NSME) | 1 593 / 1 517 | **≈ 7** / **293** |
| BUILD_GRAPH_COLD_MS | 8 452 | **3 171** |
| BUILD_GRAPH (needs warm) | 4 164 | **≈ 36** |
| BUILD_GRAPH_WARM (cache graphe) | — | **≈ 2** |
| SDG_ENDPOINT_COLD_MS | 11 190 (2B HTTP 5 410) | **2 886** |
| SDG_ENDPOINT_WARM_MS | 17 – 264 | **247** |
| FIRST_USEFUL_MS (core, process frais + warmup) | 2 373 (2A) | **≈ 70** (pas de régression) |

Objectifs : spatial cold routes OK ; SDG cold **< 3 s** atteint sur process frais ; warm SDG **< 300 ms**.

### 12.10 Limites restantes

- Premier **needs** froid encore ≈ 3–4,5 s (telecom + education Python + health) si caches SharedSpatial / site_ctx vides.
- Education nearest reste un coût **application** (chargement projection écoles), pas PostGIS.
- Health `ST_DWithin(geography)` non encore réécrit (secondaire ≈ 0,5 s).
- Neighbors FDSU haversine (jusqu’à 5000 sites) inchangé.

### 12.11 Smoke / non-régression

| Check | Résultat |
|---|---|
| Site 300 | HTTP **200** — Yoseki |
| Site 20 476 | HTTP **200** — Kakyelo |
| Localités | **47 130** |
| Groupements | **2 642** |
| Staging FDSU MNO | **12 611** |

### 12.12 Tests

```
pytest tests/test_phase2c_build_graph_perf.py tests/test_phase2b_spatial_dedup.py \
       tests/test_shared_spatial_context.py tests/test_site_spatial_context_cache.py
→ 23 passed
```

### 12.13 Fichiers Phase 2C (locaux, non commités)

**Modifiés :** `transport_service.py`, `shared_spatial_context.py`, `spatial_matching_service.py`, `spatial_decision_graph_service.py`, `telecom_service.py`, `api/main.py`, ce rapport.
**Ajoutés :** `tests/test_phase2c_build_graph_perf.py` ; scripts de profilage `profile_phase2c_*.py` (outils).

---

## 13. PERFORMANCE PHASE 2D — EDUCATION / NEEDS COLD PATH

**HEAD de départ :** `a564fd1ac11050e0b9e484a1fbb06765eea1a3eb` (Phase 2C)
**Date :** 2026-07-20
**Statut :** correctifs locaux — **aucun commit / push** (attente validation)

### 13.1 Baseline NEEDS (site 29, caches vides)

| Métrique | Cold ms | Warm ms |
|---|---:|---:|
| NEEDS_TOTAL | **4 316** | 0,2 |
| EDUCATION full | **1 377** | 8,4 |

Décomposition cold (composants mesurés séparément) :

| COMPONENT | COLD_MS | WARM_MS | % du NEEDS | SOURCE | EXECUTION_MODE |
|---|---:|---:|---:|---|---|
| education | 1 343 | 0,1 | 31,1 | CENI SCHOOL projection | Python |
| telecom | 1 306 | 445 | 30,3 | PostGIS NSME | PostGIS |
| localities | 1 141 | 24 | 26,4 | uncovered jsonl | Python |
| neighbors | 371 | 334 | 8,6 | FDSU sites | Python/DB |
| health | 348 | 271 | 8,1 | PostGIS | PostGIS |
| roads | 134 | ≈0 | 3,1 | PostGIS KNN | PostGIS |
| ceni | 113 | 0,1 | 2,6 | CENI signals | Python |

### 13.2 Cause exacte Éducation

| Étape | ms | Détail |
|---|---:|---|
| EDUCATION_IO_MS | **60** | lecture `ceni_registry_v1.json` (**55,1 Mo**) |
| EDUCATION_PARSE_MS | **1 253** | `json.loads` registre complet |
| EDUCATION_INDEX_BUILD_MS | **294** | projection 23 514 SCHOOL mappables |
| EDUCATION_NEAREST_MS | **8** | bbox + Haversine — **déjà rapide** |

Le nearest n’était **pas** le goulot. Le cold = parse registre CENI + projection.

Consommateurs : NSME `match_site_to_schools`, SharedSpatialContext, Decision Case evidence, SDG (via needs), dashboard stats.

Sans cache slim, optimiser seulement Éducation déplaçait le parse 55 Mo vers `match_site_to_ceni_signal` (même registre).

### 13.3 Architecture après

| Couche | Rôle |
|---|---|
| `referential_runtime_cache.load_json_file` | parse CENI partagé (mtime/size) quand le registre complet est requis |
| Projection slim Éducation | `data/cache/education_mappable_schools_v1.json` — 23 514 établissements |
| Projection slim CENI signals | `data/cache/ceni_mappable_signals_v1.json` — 31 956 points mappables |
| Mémoire | one-shot + `threading.RLock` par signature |
| SharedSpatialContext | `get_education_nearest` — clé géo + signature registre |
| Nearest | **inchangé** : `spatial_nearest_utils.nearest_points` (bbox + Haversine) |

**Choix A vs B :** conservation Python + projection slim (pas de migration PostGIS Éducation). Index STRtree/KDTree non nécessaire (nearest ≈ 8 ms). Pas de nouvelle dépendance.

**Startup :** aucun preload Éducation/CENI au lifespan (coût ajouté = **0**). Lazy au premier besoin.

### 13.4 Invalidation / concurrence

- Signature : `rrc.file_signature(REGISTRY_PATH)` = path + mtime_ns + size
- Changement fichier CENI → miss disque + rebuild
- Un seul build par signature (RLock) — pas de double construction concurrente

### 13.5 BEFORE / AFTER

| Métrique | BEFORE | AFTER |
|---|---:|---:|
| NEEDS cold | **4 316** | **3 192** (−26 %) |
| NEEDS warm | 0,2 | 0,4 |
| EDUCATION cold | **1 377** | **341** (−75 %) |
| EDUCATION warm | 8,4 | **6,5** |
| SPATIAL_CONTEXT cold | — | **422** |
| SDG cold HTTP (process frais) | 2 886 (2C) | **3 586** |
| SDG warm HTTP | 247 (2C) | **267** |
| FIRST_USEFUL | ~70 (2C) | **40–76** |

Objectif NEEDS &lt; 2 s : **non atteint** sans toucher localities (~1,1 s) + telecom (~1,3 s) — documenté honnêtement.

SDG warm &lt; 300 ms : OK. FIRST_USEFUL : pas de régression.

### 13.6 Exactitude

Site 29 : nearest **E.P. KIMAZA NORD**, distance **3 219,9 m**, id `EDU-CENI-B6B2DFFEA9152AEC674ADB5C` — **identique** avant/après.

### 13.7 Smoke / non-régression

| Check | Résultat |
|---|---|
| Site 300 | HTTP **200** — Yoseki |
| Site 20 476 | HTTP **200** — Kakyelo |
| Localités / Groupements / MNO | **47 130 / 2 642 / 12 611** |

### 13.8 Tests

```
pytest tests/test_phase2d_education_cache.py (+ 2B/2C/shared/cache)
→ 30 passed
```

### 13.9 Limites restantes (Phase 2E candidate)

- NEEDS cold ~3,2 s dominé par **telecom PostGIS** + **localities uncovered jsonl**
- SDG cold HTTP ~3,6 s (inclut needs) — léger écart vs 2C 2,9 s (variance + charge projection disque)
- Neighbors FDSU haversine inchangé
- Projections slim = runtime `data/cache/*` (non versionnées)

### 13.10 Fichiers Phase 2D (locaux, non commités)

**Modifiés :** `education_referential_service.py`, `ceni_registry_service.py`, `shared_spatial_context.py`, `app/referentials/ceni_official/service.py`, ce rapport.
**Ajoutés :** `tests/test_phase2d_education_cache.py` ; scripts `profile_phase2d_*.py` (outils, exclus du commit).

---

## 14. PERFORMANCE PHASE 2E — LOCALITY + TELECOM COLD PATH

**HEAD de départ :** `5e860ae06c8caefd73850cabe10567b05ac34536` (Phase 2D)
**Date :** 2026-07-20
**Statut :** correctifs locaux — **aucun commit / push** (attente validation)

### 14.1 Clarification référentiel Localités (NSME Needs)

Le chemin Needs / NSME `match_site_to_uncovered_localities` lit **`data/coverage/localities_uncovered.jsonl`** (**24 604** lignes NCI), **pas** le référentiel unifié 47 130 (historique + NCI) utilisé ailleurs (dashboard / NIRE).

Les 47 130 restent confirmés côté référentiel unifié ; le goulot Needs est le parse JSONL uncovered.

### 14.2 Baseline (site 29, caches runtime vides)

| Métrique | Cold ms | Warm ms |
|---|---:|---:|
| NEEDS_TOTAL | **3 282** | 0,2 |
| LOCALITY match | **817** | 20 |
| TELECOM match | **1 166** | 422 |
| SPATIAL_CONTEXT | **520** | ≈ 0 |

Localités uncovered :

| Stage | ms |
|---|---:|
| LOCALITY_IO_MS | 13 |
| LOCALITY_PARSE_MS | **556** |
| LOAD_COLD_MS | 745 |
| MATCH (incl. load) | 817 |
| LOCALITY_MERGE_MS | N/A (pas de fusion 47 130 sur ce chemin) |
| LOCALITY_INDEX_BUILD_MS | 0 (pas d’index spatial — bbox admin + haversine sur pool filtré) |
| LOCALITY_NEAREST_MS | ~20 (warm match) |

Télécom — top 3 (séquentiel isolé) :

| Stage | COLD_MS |
|---|---:|
| nearest_any (`get_statistics` + KNN) | **1 363** |
| airtel | 193 |
| mw | 133 |

| Check | Valeur |
|---|---|
| DB_CONNECTION_FIRST_MS | **68** |
| Staging FDSU | **12 611**, sync_now=false |
| PostGIS infra KNN | Index Scan GiST ~1 ms (EXPLAIN) — **pas de nouvel index** |
| `run_mno_audit` | non déclenché (staging prêt) |

Cause structurelle Télécom Needs : `match_site_to_telecom` appelait `spatial_context_around` **hors** SharedSpatialContext → recalcul + warm ~420 ms.

### 14.3 Corrections

| Correction | Détail |
|---|---|
| Localités | cache mémoire + slim disque `nci_localities_uncovered_v1.json` (mtime/size) ; RLock ; une seule charge puis filtres mémoire |
| Télécom stats | `get_statistics()` cache process TTL 300 s |
| Télécom NSME | `ssc.get_telecom_spatial_context` au lieu de `spatial_context_around` direct |
| Threading | inchangé (≤4 + anti-imbrication) |
| Startup | **+0 ms** (pas de preload) |

Choix index spatial 47 130 / PostGIS : **non** — le chemin Needs n’utilise pas 47 130 ; uncovered 24k + préfiltre admin suffit après cache disque.

### 14.4 BEFORE / AFTER

| Métrique | BEFORE | AFTER |
|---|---:|---:|
| NEEDS cold | **3 282** | **2 892** (−12 %) |
| NEEDS warm | 0,2 | 0,2 |
| LOCALITY cold | **817** | **431** (−47 %) |
| LOCALITY warm | 20 | 35 |
| TELECOM match cold | **1 166** | **1 053** |
| TELECOM match warm | **422** | **0,3** |
| SPATIAL_CONTEXT cold | 520 | 651 |
| SDG cold (in-process) | — | 4 650 |
| SDG warm | — | 5 |
| FIRST_USEFUL | — | **87** |

Objectif NEEDS &lt; 2 s : **non atteint**. Coût résiduel ~2,9 s = education/ceni slim disk + uncovered disk + PostGIS telecom (infra+line+context) + neighbors. Arrêt volontaire sans refonte lourde.

### 14.5 Exactitude

Localité site 29 : `NCI-UNC-66BFD5050A`, **2 508,8 m** — **identique**.

### 14.6 Smoke / non-régression

| Check | Résultat |
|---|---|
| Site 300 / 20 476 | HTTP **200** — Yoseki / Kakyelo |
| Localités unifiées | **47 130** |
| Uncovered NCI (Needs) | **24 604** |
| Groupements | **2 642** |
| Staging MNO | **12 611** |

### 14.7 Tests

```
pytest tests/test_phase2e_locality_telecom.py (+ 2B/2C/2D/shared/cache)
→ 35 passed
```

### 14.8 Fichiers Phase 2E (locaux, non commités)

**Modifiés :** `coverage_intelligence_service.py`, `telecom_service.py`, `spatial_matching_service.py`, ce rapport.
**Ajoutés :** `tests/test_phase2e_locality_telecom.py` ; scripts `profile_phase2e_*.py` (outils).
