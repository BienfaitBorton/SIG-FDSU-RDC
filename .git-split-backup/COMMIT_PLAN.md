# Plan de commits — IG / SDG / Data First / P0 Santé

**Date :** 2026-07-12  
**Aucun commit créé automatiquement.**  
**Sauvegarde :** `.git-split-backup/` + `refs/backup/pre-split-20260712`

## Ordre obligatoire

1. Integrity Gate  
2. Spatial Decision Graph v2.1  
3. Data First Integration Policy  
4. P0 Santé  

## Méthode sûre (index alternatif — working tree intact)

Les index préparés sont dans `.git-split-backup/index-c{1,2,3,4}` et `index-c4-stacked`.  
Le working tree reste à l’état **FINAL** (P0 Santé inclus).

Pour inspecter un ensemble sans toucher le working tree :

```powershell
$env:GIT_INDEX_FILE = (Resolve-Path .git-split-backup/index-c1)
git diff --cached --stat
```

Pour **créer** un commit (manuel, quand vous le demandez) — procédure recommandée :

1. Vérifier que le WT = FINAL (déjà le cas).  
2. Appliquer l’état C2/C3 intermédiaire **uniquement au moment du commit 2/3** via copies depuis `.git-split-backup/intermediate/`, commit, puis restaurer FINAL depuis `.git-split-backup/final/` avant le commit suivant.  
3. Ou : `git apply` des hunks dans `manifests/hunk-*.diff` après le commit précédent.

Les diffs empilés C4 sont dans `manifests/c4-stacked-on-c2c3-stat.txt` (380 insertions — delta P0 réel).

## COMMIT 1 — Integrity Gate

**Message :** `fix(integrity): harden decision case integrity gate`

### Fichiers (15)

- `.cursor/rules/e2e-integrity-gate.mdc`
- `PROJECT_MANAGEMENT/ARCHITECTURE/E2E_INTEGRITY_GATE.md`
- `api/routes/decision_engine.py`
- `api/services/explainable_decision_service.py`
- `api/services/site_entity_resolver.py`
- `dashboard/app.js`
- `dashboard/index.html` *(tags scripts DXL/IG — prérequis C2)*
- `dashboard/modules/decision-experience/decision-case-controller.js`
- `dashboard/modules/decision-experience/decision-error-handler.js`
- `dashboard/modules/decision-experience/decision-experience.css`
- `dashboard/modules/decision-experience/decision-experience.js` *(orchestrateur mince)*
- `dashboard/modules/decision-experience/dxl-core.js`
- `dashboard/modules/shared/executive-situation-room/executive-situation-room.css`
- `tests/e2e/integrity-gate-decision-case.spec.js`
- `tests/test_integrity_gate_decision_case.py`

### `git diff --cached --stat` (index-c1)

```
15 files changed, 1579 insertions(+), 1226 deletions(-)
```

### Hunks partagés

- `index.html` / `decision-experience.js` : shell DXL + IG ; C2 dépend de C1 pour le chargement des scripts.

### Tests

- `pytest tests/test_integrity_gate_decision_case.py`
- Playwright `tests/e2e/integrity-gate-decision-case.spec.js`
- Sites 7, 29, 30 ; historique corrompu ; pas d’HTTP technique

### Dépendances

- Aucune (base)

### Revert

- Indépendant : retire IG/DXL shell ; SDG seul ne monte plus via DXL mais le code SDG reste.

---

## COMMIT 2 — Spatial Decision Graph v2.1

**Message :** `feat(spatial): deliver Spatial Decision Graph v2.1`

### Fichiers (9)

- `PROJECT_MANAGEMENT/ARCHITECTURE/SPATIAL_DECISION_GRAPH_V2.md`
- `PROJECT_MANAGEMENT/ARCHITECTURE/DXL_MODULE_SPLIT_IG_SDG.md`
- `api/services/spatial_decision_graph_service.py` **← version C2** (sans PostGIS Santé)
- `dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js` **← version C2** (sans bouton recalcul)
- `dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.css`
- `dashboard/modules/decision-experience/spatial-impact-controller.js`
- `dashboard/modules/shared/ux-premium/ux-premium.js`
- `tests/e2e/spatial-decision-graph.spec.js`
- `tests/test_spatial_decision_graph.py`

### `git diff --cached --stat` (index-c2 vs HEAD)

```
9 files changed, 2578 insertions(+), 491 deletions(-)
```

### Hunks partagés attribués à C2

- SDG service : renderer, maturité générique, `data_first`, catégories ; **health `nsme_wired=False`**
- SDG JS : 3 panneaux, filtres, détail, présentation — **sans** `#sdg-refresh-btn`

### Source intermédiaire

- `.git-split-backup/intermediate/c2/...`

### Tests

- `pytest tests/test_spatial_decision_graph.py`
- Playwright `tests/e2e/spatial-decision-graph.spec.js`
- Shell / filtres / détail / présentation ; pas d’ancienne légende ; pas de double Leaflet

### Dépendances

- **C1** (dxl-core, index.html, orchestrateur)

### Revert

- Retire SDG v2.1 ; dossier IG reste via `DecisionCaseController` + map sans SDG.

---

## COMMIT 3 — Data First Integration Policy

**Message :** `docs(architecture): adopt Data First Integration Policy`

### Fichiers (4)

- `.cursor/rules/data-first-integration.mdc`
- `PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_POLICY.md`
- `PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_AUDIT_V1.md` **← état pré-P0** (Santé 🔴)
- `PROJECT_MANAGEMENT/ARCHITECTURE/INTEGRITY_GATE_REPORT_V1.md` **← état pré-P0** (A14 ouverte)

### `git diff --cached --stat` (index-c3)

```
4 files changed, 357 insertions(+)
```

### Source intermédiaire

- `.git-split-backup/intermediate/c3/...`

### Tests

- Revue docs ; règle Cursor valide ; maturités documentées

### Dépendances

- Docs seules ; idéalement après C2 (référence SDG maturité)

### Revert

- Indépendant (docs only)

---

## COMMIT 4 — P0 Santé

**Message :** `feat(health): integrate real health relations into spatial intelligence`

### Fichiers (7) — delta empilé sur C2+C3

- `api/services/health_service.py`
- `api/services/spatial_matching_service.py`
- `data/business/spatial_matching_rules.json`
- `api/services/spatial_decision_graph_service.py` **← hunks PostGIS / NEAREST / WITHIN / notes rayon**
- `dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js` **← bouton recalcul**
- `PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_AUDIT_V1.md` **← A14 corrigé**
- `PROJECT_MANAGEMENT/ARCHITECTURE/INTEGRITY_GATE_REPORT_V1.md` **← A14/A4 corrigés**

### `git diff --cached --stat` (index-c4-stacked vs base C2+C3)

```
7 files changed, 380 insertions(+), 16 deletions(-)
```

### Hunks partagés (C4)

| Fichier | Contenu P0 |
|---|---|
| `spatial_decision_graph_service.py` | Styles NEAREST/WITHIN ; probe `health.health_facilities` wired ; filtre NCI ; note rayon 5 km |
| `spatial-decision-graph.js` | `#sdg-refresh-btn` + `refreshSpatialRelations` |
| Audits | Santé 🟢/🟡 ; A14/A4 corrigés |

Hunks bruts : `manifests/hunk-*.diff`

### Tests

- Sites 7, 29, 30, 34, 42 ; nearest ; rayon 5 km ; refresh ; filtre Santé ; pas de points inventés

### Dépendances

- **C1 + C2 + C3**

### Revert

- Retire le branchement Santé ; SDG générique + Data First (A14 ouverte) restent.

---

## Exclusions runtime (ne jamais indexer)

- `data/decision/case_history.json`
- `data/raw/Routes_principales.shp.kmz`
- `data/sectoral/transport/processed/routes_principales.geojson`
- `PROJECT_MANAGEMENT/ARCHITECTURE/captures/` (preuves locales, non référencées en docs)
- `.git-split-backup/` (outil de séparation)

## Restauration d’urgence

```powershell
git show refs/backup/pre-split-20260712
# ou recopier depuis .git-split-backup/final/
```
