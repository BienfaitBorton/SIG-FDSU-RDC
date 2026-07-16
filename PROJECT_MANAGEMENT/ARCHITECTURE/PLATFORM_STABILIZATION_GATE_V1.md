# Platform Stabilization Gate V1.0

## Gate V1.1 — vérification du 15 juillet 2026

| Domaine | Avant | Après | Statut |
|---|---:|---:|---|
| Backend passés | 280 | 303 | VERT |
| Backend échoués | 23 | 0 | VERT |
| Playwright passés | 90 | 27 Smart Map validés + 17 DXL/EPM validés + contrôles ciblés | PARTIEL |
| Playwright échoués | 35 | 0 Smart Map restant ; Centre de Décision en reprise | EN COURS |
| Non exécutés | 18 | 23 du lot critique après limite de 15 min, puis reste de la suite | BLOQUANT |
| CRUD | 405 | 22/22 tests ciblés passés | VERT |
| Crash Leaflet | Oui | non reproduit après dépendance locale | VERT CIBLÉ |
| SDG monté | Non stable | backend vert ; Playwright dédié non terminé | À CONFIRMER |
| Centre de Décision | Régressé | carte remontée ; revalidation incomplète | EN COURS |
| Exports | Régressés | non validés dans cette passe | À FAIRE |

### Classification et causes racines V1.1

1. Les erreurs Pytest précoces provenaient d'un `PermissionError` sur le répertoire temporaire Windows. Avec un `--basetemp` local, la suite donne `303 passed, 1 skipped, 0 failed` en 444,75 s.
2. Les 405 ne se reproduisent pas à `HEAD aaf21bb` : les onze fichiers CRUD demandés donnent `22 passed`.
3. Smart Map dépendait exclusivement du CDN `unpkg.com` pour Leaflet 1.9.4. Hors réseau, `L` restait indéfini et le montage quittait avant `cartographyState.initialized`.
4. La toolbar premium avait perdu les sélecteurs stables `.cartography-toolbar-row` et `.cartography-tool-btn` malgré un comportement équivalent.
5. Deux tests utilisaient `.check()` sur des couches DB volontairement décochées en l'absence de géométrie après affichage du message métier.
6. `#decision-center-national-map` avait disparu du HTML alors que son JS et son CSS étaient toujours actifs.
7. Les assertions Centre de Décision `7 onglets`, `8 intentions` et « Moteur de décision FDSU » étaient antérieures aux contrats présents : `8 onglets`, `10 intentions`, « Priorisation nationale ».
8. Sous Windows, les webservers enfants Playwright ne se ferment pas toujours. La réutilisation d'une API unique 8001 et d'un dashboard unique 8000 permet une terminaison normale, mais le dashboard manuel est ensuite devenu indisponible.

### Corrections et contrats restaurés

- Leaflet 1.9.4 est servi localement depuis `dashboard/vendor/leaflet/` avec JS, CSS, images et licence.
- `dashboard/index.html` référence Leaflet local, restaure les classes DOM stables et remonte la carte nationale sans retirer le Tableau de Synthèse Territoriale.
- Les deux interactions de couches DB utilisent `.click()` tout en conservant leurs assertions métier.
- Les assertions Centre de Décision sont alignées sur les nombres et libellés institutionnels déjà présents.
- Aucun try/catch silencieux, skip, timeout global ou mock fonctionnel n'a été ajouté.

### Performances et tests

- Backend complet : 303 passés, 1 skipped, 0 échec, 444,75 s.
- CRUD ciblé : 22 passés, 0 échec, 5,17 s.
- Smart Map : 24/27 lors de la passe complète, puis les trois résidus ciblés validés. Les deux tests racines passent en 1,4 s et 9,8 s au lieu d'expirer à 45–60 s.
- DXL/EPM : 17 scénarios critiques consécutifs passés, dont fermeture, réouverture, responsive, contribution et unicité Leaflet.
- Aucun code worker 134 ou 3221226505 observé.
- Les mesures HTTP isolées SDG/Impact/TI et l'export Excel restent à exécuter.

### Fichiers modifiés V1.1

- `dashboard/index.html`
- `dashboard/vendor/leaflet/*`
- `package.json`
- `tests/e2e/smart-map.spec.js`
- `tests/e2e/decision-center.spec.js`
- ce rapport.

### Skipped, captures et protection

- Backend : 1 skipped existant, à justifier avant gate final.
- Les captures versionnées et `data/decision/case_history.json` modifiés automatiquement par les tests ont été restaurés à `HEAD`.
- Aucune donnée brute ou officielle, aucun `_stab_*` ou `_val_*` n'est inclus.
- Aucun commit n'a été créé.

### Verdict V1.1

Backend et Smart Map sont stabilisés sur les validations exécutées. Le gate global reste **PARTIEL / NON PUBLIABLE** jusqu'à exécution complète de Playwright, validation SDG/Impact, export Excel et revalidation du Centre de Décision avec un dashboard 8000 stable.

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
