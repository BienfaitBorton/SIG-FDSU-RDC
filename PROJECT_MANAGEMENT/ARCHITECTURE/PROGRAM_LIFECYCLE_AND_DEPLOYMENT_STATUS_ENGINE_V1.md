# Program Lifecycle & Deployment Status Engine — v1.0

**Statut doc :** v1 livré  
**Moteur :** `ple-1.0.0`  
**Doctrine :** Data First / No Black Box — aucun statut opérationnel inventé.

---

## 1. Problème traité

Le SIG confondait :

1. disponibilité des données (intégration) ;
2. état du programme ;
3. état physique du site ;
4. chantier ;
5. mise en service ;
6. impact (estimé / projeté / observé).

Le même mot « Opérationnel » servait à tout cela.

---

## 2. Six dimensions

| Dimension | Codes (extrait) | Libellé exemple |
|-----------|-----------------|-----------------|
| `data_status` | integrated, partial, unavailable, error | Données intégrées |
| `program_status` | strategic_planning, planned, preparation, deployment_in_progress, … | En cours de déploiement |
| `asset_status` | candidate … operational / unknown | Statut individuel à confirmer |
| `worksite_status` | not_started … completed | À consolider |
| `service_status` | not_available … available | Service non disponible |
| `impact_status` | not_measured, estimated, projected, observed… | Impact estimé |

---

## 3. Règles institutionnelles initiales

| Programme | program_status | data_status |
|-----------|----------------|-------------|
| Sites 40 | `deployment_in_progress` | integrated |
| Sites 300 | `planned` | integrated |
| Sites 20 476 | `strategic_planning` | partial |
| CCN | `preparation` | partial (DEMO) |

Compteurs `installed` / `commissioned` / `operational` → **null** + « À consolider ».

---

## 4. API

Préfixe : `/api/program-lifecycle`

- `GET /programs` — tableau de suivi
- `GET /programs/{code}`
- `GET /assets/{id}?program_code=&raw_status=`
- `GET /audit/matrix`
- `GET /history/contract` — modèle sans historique inventé
- `GET /labels/data-maturity/{code}`

Registre : `data/business/program_lifecycle_registry_v1.json`

---

## 5. Compatibilité non destructive

| Ancien | Interprétation PLE |
|--------|--------------------|
| SDG `maturity=operational` | `data_status` → **Référentiel intégré** |
| `program_status=EN_EXECUTION` | `deployment_in_progress` |
| `status=active` (catalogue) | ≠ site opérationnel |
| CCN DEMO `operational` | non promu production |
| site `à qualifier` / `actif` | `asset_status=unknown` |

Champs legacy conservés ; couche PLE ajoutée.

---

## 6. Impact territorial

- Couverture **observée** uniquement si preuve individuelle (`counts_as_observed_coverage`).
- Sinon : **estimée / projetée** (trait pointillé UI).
- CCN : bénéficiaires potentiels ≠ couverture radio.
- Libellés : population et localités **jamais fusionnés** (« +N bénéficiaires projetés dans K localités »).

---

## 7. Surfaces corrigées

- Spatial Decision Graph (libellés maturité)
- Territorial Intelligence (notes programme + humanize)
- Dossier de décision / Impact (4 badges)
- Salle de Pilotage (tableau cycle de vie + KPI CCN DEMO)
- `program_service.sites_to_panel_payload` / `get_sites_followup`
- Cartographie popup (« Statut source » / « Statut de donnée »)

---

## 8. Gouvernance future

Contrat d’historique + capacité admin (preuve, date, validation) documentés — **non inventés** dans v1.

---

## 9. Limites / données manquantes

- Pas de dates de mise en service officielles dans le référentiel actuel.
- Pas de répartition réelle installé / en test / opérationnel par site.
- Inventaire CCN = DEMO.
- Symbologie carto par `asset_status` : partielle (badge/API prêts ; couche couleur à enrichir).

---

## 10. Tests

- Backend : `tests/test_program_lifecycle_engine.py`
- Playwright : `tests/e2e/program-lifecycle.spec.js`
- Captures : `PROJECT_MANAGEMENT/ARCHITECTURE/captures/program-lifecycle/`
