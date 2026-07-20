# Startup Performance Audit — SIG-FDSU RDC

**Branche :** `feature/smart-map-interactions`
**HEAD de départ :** `54c840f6e74e6710fbd8825096add79fb1c509fe`
**Date :** 2026-07-20
**Mode mesuré :** `DATA_MODE=json` (processus Python in-process + probes référentiels)
**Commit :** aucun (attente validation)

---

## 1. Définition STARTUP_READY

`STARTUP_READY` = moment où le processus API a importé `api.main` et monté les routes FastAPI, **sans** précharger les référentiels lourds.

Les référentiels (localités ~115 Mo, CENI ~52 Mo, groupements) restent **lazy** à la première requête qui en a besoin, puis **cachés en mémoire** (mtime).

Dashboard `serve_utf8.py` (port 8000) : serveur statique léger — pas de preload JSON.

---

## 2. Baseline (avant cache partagé)

Mesure `SIG_REF_CACHE=0` (une exécution instrumentée) :

| Étape | ms |
|---|---:|
| import `api.main` / STARTUP_READY | **21 978,6** |
| first `/localites/count` équivalent | **12 711,8** |
| second `/localites/count` | **14 909,1** |
| first groupements count | **614,5** |
| second groupements count | **803,4** |
| first CENI registry | **6 415,3** |
| second CENI registry | **0,0** (déjà `@lru_cache`) |
| spatial_matching_rules | **0,9** |
| dashboard_summary | **13 883,9** |
| TOTAL_PROBE | **71 773,7** |

### Lectures répétées détectées (un seul probe)

| Fichier | READ_COUNT | BYTES_READ | PARSE_MS |
|---|---:|---:|---:|
| `locality_referential_official.json` | **3** | 281,8 Mo | 22 512 |
| `locality_referential_nci_enrichment.json` | **3** | 79,2 Mo | 11 033 |
| `locality_groupement_links_rgc.json` | **3** | 10,5 Mo | 1 236 |
| `groupement_referential_official.json` | **3** | 15,6 Mo | 1 420 |
| `groupement_referential_rgc_enrichment.json` | **3** | 3,4 Mo | 380 |

**Cause principale :** chaque appel `national_locality_count` / `build_summary` / fusion reconstruisait et reparsait les JSON.

**Second goulot :** cold load CENI (~6,4 s) — déjà lazy + `@lru_cache` ensuite.

**Non-goulot au boot :** NSME rules, SDG (pas de preload au démarrage).

---

## 3. Corrections appliquées

1. **`api/services/referential_runtime_cache.py`** — cache JSON mtime + cache de fusions/counts + stats `READ/PARSE/BYTES/MS` + `SIG_REF_CACHE` / `SIG_STARTUP_TRACE`.
2. **Localités** — `load_national_locality_items` / enrichment via cache ; invalidation sur `persist_enrichment`.
3. **Groupements** — official / RGC enrichment / crosswalk / links + counts via cache ; invalidation sur écritures.
4. **`load_report` (api/main.py)** — lectures rapports via cache mtime.
5. **DNAI `discover_ceni`** — réutilise `ceni_registry_service.registry()` (plus de second parse 52 Mo).
6. **`national_dashboard_service.counter_registry`** — via cache runtime.
7. **Logs lifespan** — `[STARTUP] API ready / CENI deferred / Localities cache` sans preload.

Fallbacks DB/JSON conservés. Aucune source brute modifiée.

---

## 4. Après optimisation — 3 runs

| Run | STARTUP_READY_MS | first loc count | warm loc count | first CENI | warm CENI | dashboard_summary |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 14 009,1 | 9 639,2 | **2,8** | 4 620,7 | 0,0 | **25,7** |
| 2 | 12 391,7 | 10 337,2 | **2,4** | 4 538,9 | 0,0 | **18,3** |
| 3 | 12 351,6 | 8 985,2 | **2,0** | 4 296,6 | 0,0 | **19,9** |
| **Médiane** | **12 391,7** | **9 639,2** | **2,4** | **4 538,9** | **0,0** | **19,9** |
| **Moyenne** | **12 917,5** | **9 653,9** | **2,4** | **4 485,4** | **0,0** | **21,3** |

Après cache : chaque gros fichier **READ_COUNT = 1** sur le probe (plus de ×3).

---

## 5. Gains

| Métrique | Avant | Après (médiane) | Gain |
|---|---:|---:|---:|
| STARTUP_READY_MS | 21 978,6 | 12 391,7 | **≈ 43,6 %** |
| SECOND_REQUEST warm localités | 14 909,1 | 2,4 | **≈ 99,98 %** |
| dashboard_summary | 13 883,9 | 19,9 | **≈ 99,86 %** |
| TOTAL_PROBE (run1 after) | 71 773,7 | 29 827,2 | **≈ 58,4 %** |

`FIRST_REQUEST_COLD_MS` (localités) reste ~9–10 s (parse inévitable une fois).
`SECOND_REQUEST_WARM_MS` ≈ **2–3 ms**.

---

## 6. Comportements par domaine

| Domaine | Startup | Runtime |
|---|---|---|
| **CENI** | deferred / lazy | 1er appel ~4,5 s ; suivants 0 ms (`@lru_cache`) |
| **Localités 47 130** | pas de preload | 1 fusion cache mtime ; count/list/search réutilisent |
| **Groupements 2 642** | pas de preload | counts/items cache mtime |
| **NSME / SDG** | pas d’index lourd au boot | rules déjà `@lru_cache` |
| **Dashboard static** | healthz immédiat | JSON à la demande navigateur |

Compteurs validés : localités **47 130**, groupements **1 681 + 961 = 2 642** (dynamiques, non hardcodés).

---

## 7. Mémoire (tracemalloc probe)

| | Avant (no cache) | Après (cache) |
|---|---:|---:|
| current MB | 217 | ~528 |
| peak MB | 598 | ~633 |

Le cache conserve volontairement les objets en RAM (trade-off : CPU/disque ↓, RAM ↑). Acceptable pour un processus serveur unique.

---

## 8. Limites restantes / recommandations futures

1. **Import `api.main` ~12–14 s** : nombreux routeurs ; scinder imports paresseux des packages lourds (til / telecom / dnai) si besoin.
2. **Cold localités ~9–10 s** : incompressible sans format binaire (msgpack/parquet) ou lecture PostGIS seule en mode DB.
3. **Cold CENI ~4,5 s** : envisager index léger (stats only) + assets à la demande.
4. **Dashboard navigateur** : différer `preloadCartographyLayers` villages (client) — hors ce sprint backend.
5. **uvicorn --reload** : double process ; mesurer aussi sans reload en prod.

---

## 9. Tests

`tests/test_startup_referential_cache.py` + régression localités/groupements/NIRE :

- **35 passed**

---

## 10. Fichiers

**Créés**

- `api/services/referential_runtime_cache.py`
- `scripts/measure_startup_performance.py`
- `tests/test_startup_referential_cache.py`
- `PROJECT_MANAGEMENT/ARCHITECTURE/STARTUP_PERFORMANCE_AUDIT.md`

**Modifiés**

- `api/main.py`
- `api/services/nire/locality_controlled_integration.py`
- `api/services/nire/groupement_controlled_integration.py`
- `api/services/dnai_service.py`
- `api/services/national_dashboard_service.py`

**Hors commit attendu :** `data/cache/startup_*`, sources brutes, artefacts hors sprint.
