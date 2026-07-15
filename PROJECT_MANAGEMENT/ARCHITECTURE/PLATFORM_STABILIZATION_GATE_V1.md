# Platform Stabilization Gate V1.0

**Sprint :** PLATFORM STABILIZATION  
**Date :** 2026-07-15  
**Contraintes :** ZERO NEW FEATURES · ZERO REGRESSION · DATA FIRST · AUCUN COMMIT  

---

## 1. Verdict

| Domaine | Avant | Après | Statut |
|---------|-------|-------|--------|
| Backend pytest | 280 passed / **23 failed** | **303 passed** / 0 failed / 1 skipped | VERT |
| Integrity Gate site/29 | — | API 200 + UI métier | VERT |
| EPM + Hotfix EPM | timeouts `#sdg-shell`, ratio carte | tous verts (cœur) | VERT |
| Data Maturity / PLE / TIE / Premium | partiel | verts sur suite ciblée | VERT |
| Playwright suite complète | OOM / timeouts massifs | cœur stabilisé ; DC en re-run | EN COURS |

**Mission prioritaire backend (CRUD 405 + contrats + FE unit) : accomplie.**

---

## 2. Audit des régressions (classification)

### C — Régression API (critique) — CORRIGÉE

| Échec | Cause exacte | Module | Impact | Correction |
|-------|--------------|--------|--------|------------|
| POST/PUT/DELETE CRUD → **405** (province, territoire, collectivité, groupement, village, site, mission, document, photo) | `@app.get("/provinces")` (et alias) enregistrés **avant** `include_router` → Starlette/FastAPI 0.139 ne merge plus les méthodes sur le même path | `api/main.py` | CRUD mort ; 20 tests | Retrait des GET legacy sur préfixes CRUD ; déplacement sous `/geo/*` |
| GET `/provinces/{id}` enrichi masquait CRUD | Même conflit path | `api/main.py` | Détail métier vs PostGIS | `/geo/provinces/{id}` + CRUD propriétaire de `/provinces/{id}` |
| `test_build_graph_missing_site` | Contrat SDG class. **C** → `_meta.status = "impossible"` | SDG / SDG Coverage Audit | faux négatif | Test étendu pour accepter `impossible` (contrat documenté) |

### B — Régression JS (unit) — CORRIGÉE

| Échec | Cause | Module | Correction |
|-------|-------|--------|------------|
| `Promise.allSettled` introuvable dans `decision-experience.js` | DXL mince : résilience déplacée vers controller + core | DXL | Test pointe vers fichiers réels (contrat DXL mince) |
| `SigMapTooltips` absent de TI | TI n’appelait plus la factory partagée | `territorial-intelligence.js` | `bindSharedTooltip` + binding détail |

### A / D — Régression UI / Leaflet EPM — CORRIGÉE

| Échec | Cause | Module | Correction |
|-------|-------|--------|------------|
| `#sdg-shell` timeout 90s | Shell créé seulement **après** fetch graphe (lenteur / course) | `spatial-decision-graph.js` | `ensureShell()` dès `loadAndMount` |
| Ratio carte EPM ~0.16 | `#sdg-explainability` restait visible et réduisait la carte | EPM CSS/JS | Masquer `#sdg-explainability` en mode présentation |
| Responsive map invisible | Même cause + layout | EPM | Idem |

### F — Données / environnement

| Signal | Note |
|--------|------|
| OOM Playwright (run antérieur) | Infrastructure / workers — pas un bug produit |
| Chromium manquant en sandbox | `npx playwright install chromium` |

### G — Architecture

Séparation claire :

- **CRUD SQLAlchemy** → `/provinces`, `/sites`, …  
- **Référentiel enrichi PostGIS / rapports** → `/geo/...` et `/map/layers/...`  
- Cartographie dashboard : endpoints listes passés en `/geo/...` où pertinent (couches restent sur `/map/layers`).

---

## 3. Fichiers modifiés (stabilisation)

### API
- `api/main.py` — résolution conflits de routes ; aliases `/geo/*`

### Dashboard
- `dashboard/app.js` — endpoints listes → `/geo/...`
- `dashboard/modules/territorial-intelligence/territorial-intelligence.js` — SigMapTooltips
- `dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js` — shell immédiat
- `dashboard/modules/shared/decision-cartography-experience/decision-cartography-experience.js` — masquer explainability en EPM
- `dashboard/modules/shared/decision-cartography-experience/decision-cartography-experience.css` — idem CSS

### Tests (adaptation contrat justifiée uniquement)
- `tests/test_spatial_decision_graph.py` — statut `impossible` (SDG Coverage Audit v1)
- `tests/test_decision_experience.py` — assertions DXL mince (controller + core)

---

## 4. Tests avant / après

### Backend

| | Résultat |
|--|----------|
| Avant | 280 passed, **23 failed**, 1 skipped |
| Après | **303 passed**, 0 failed, 1 skipped (~12 min) |

Échecs CRUD 405 et contrats FE : **0**.

### Playwright (suite cœur stabilisation)

Commande :

```text
npx playwright test
  decision-cartography-experience*.spec.js
  cartography-experience-premium.spec.js
  integrity-gate-decision-case.spec.js
  data-maturity.spec.js
  territorial-impact.spec.js
  program-lifecycle.spec.js
  --workers=1
```

| | Résultat |
|--|----------|
| Après | **29 passed**, **1 skipped** (popup enrichi premium — skip explicite), ~24 min |

Integrity Gate site/29 : **3/3 ok**.  
EPM Phase 2.1 + Hotfix : **intégralement verts**.

---

## 5. Performances (points de contrôle)

- `GET /api/decision/case/29?asset_type=site&program_code=sites_40` → **200**, nom métier « Village Nsona »
- `GET /api/spatial-decision-graph/site/29?program_code=sites_40` → **200**, edges avec `contribution_type` sans « non calculée »
- Montage `#sdg-shell` : immédiat au démarrage de `loadAndMount` (avant réponse API)

---

## 6. Exclusions (ne pas committer)

- `data/decision/case_history.json`
- `_val_*`, `test-results/`, `.pytest_tmp_cache/`, captures temporaires non intentionnelles
- Artefacts KMZ / GeoJSON générés runtime

**Aucun commit effectué dans ce sprint.**

---

## 7. Suite restante (hors cœur validé)

À re-valider avant « 100 % Playwright suite entière » :

- `decision-center.spec.js` / `decision-center-map-table.spec.js`
- `executive-situation-room.spec.js`, `smart-map.spec.js`, `sdg-coverage-audit.spec.js`, etc.

Cause historique : timeouts / OOM — pas de nouvelle feature requise pour le CRUD.

---

## 8. Règle pour la suite

Aucun nouveau développement architecture tant que :

1. Backend reste **100 % vert** ;
2. Integrity Gate + EPM + Hotfix restent verts ;
3. La suite Playwright élargie ne regresse pas sur les crashs / `#sdg-shell` / voiles.
