# PERFORMANCE PHASE 2 — Decision Dossier + Spatial Relations

**Projet :** SIG-FDSU RDC
**Branche :** `feature/smart-map-interactions`
**HEAD de départ validé :** `f473202611dcdcef53ebdad75b890a8537537f1a`
**Date :** 2026-07-20
**Périmètre :** cold path Dossier de Décision / DXL / preuves spatiales (telecom)
**Statut :** Phase 2A terminée (correctif cœur + validation légère). **Phase 2B** ouverte pour impact/needs/SDG/map.

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
