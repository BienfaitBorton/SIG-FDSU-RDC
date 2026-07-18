# Intégration Télécom FDSU — NIRE non bloquant

**Branche :** `feature/smart-map-interactions`
**Principe :** le NIRE qualifie, rapproche, détecte les conflits et mesure la confiance — **il n’occulte pas** une source FDSU valide.

---

## 1. Sources FDSU vs référentiel KPI

| Source | Rôle | KPI `COUNT(telecom.infrastructure)` |
|--------|------|-------------------------------------|
| KMZ Vodacom / Orange / Fibre-MW / Fiberco / FTTX (seed PostGIS) | Référentiel physique historique | **Inclus** (baseline 14 580 points) |
| Excel MNO FDSU (`Operators existing and planned sites_*.xlsx`) | Déclarations opérateurs (4 MNO) | **Exclu** — couches provisoires |
| Staging `telecom.fdsu_mno_sites` | Copie dérivée pour relations PostGIS | **Exclu** |

Sources brutes KMZ / Excel : **immuables**.

Chemins bruts documentés :

- `data/raw/08092023_Fiber & MW Footprint_KMZ.kmz`
- `data/raw/Fiberco view.kmz`
- Copies seed : `data/sectoral/telecom/raw/` (via `database/seed_telecom.py`)

---

## 2. NIRE non bloquant — statuts qualité

| Statut carto | Sens | Visible ? |
|--------------|------|-----------|
| VERIFIED | Match fort auto | Oui |
| HIGH_CONFIDENCE | Match / Planned fort | Oui |
| PROVISIONAL | Présence / nouvelle candidate / Planned | Oui |
| NEEDS_REVIEW | Ambigu / doublon / revue | Oui |
| CONFLICT | Conflit identité | Oui |

**Ne jamais confondre** « non vérifié » avec « inexistant ».

---

## 3. Catalogue de couches (extensible)

API : `GET /api/telecom/layer-catalog`
Module : `api/services/telecom_layer_catalog.py`

Couches Smart Map :

- Sites Vodacom / Orange (DB)
- Sites Airtel / Africell (FDSU MNO audit)
- Sites MNO Planned (FDSU)
- Fibre (Fiberco + FTTX typés)
- Microwave / MW (opérateur FIBER_MW)
- Fiberco / Fibre-MW combiné / FTTX (historique)

Nouveaux opérateurs futurs = nouvelles entrées catalogue, sans refonte globale.

---

## 4. Fibre / MW / Fiberco — typage dérivé

Module `api/services/telecom_asset_typing.py` :

- Conserve `original_type`
- Propose `FIBER_LINK`, `MICROWAVE_LINK`, `NETWORK_NODE`, `POP`, `TECHNICAL_SITE`, `COVERAGE_OR_SERVICE_AREA`, `OTHER`

Répartition opérationnelle retenue (attributs seed) :

- **Fibre** ≈ Fiberco + FTTX
- **MW** ≈ lignes `FIBER_MW` (source Fiber & MW Footprint)
- **Fiberco** = couche opérateur complète (points / lignes / polygones)

---

## 5. Relations spatiales

Endpoint : `GET /api/telecom/spatial-context?latitude=&longitude=`

Relations ajoutées :

- `NEAREST_MNO_VODACOM` / `ORANGE` / `AIRTEL` / `AFRICELL`
- `NEAREST_FIBER_LINK`, `DISTANCE_TO_FIBER_M`
- `NEAREST_MICROWAVE_LINK`
- `MULTI_OPERATOR_PROXIMITY`, `COLOCATION_SIGNAL`
- `BACKHAUL_CANDIDATE`, `MUTUALIZATION_POTENTIAL`

Intégrées aussi dans `match_site_to_telecom` (Spatial Matching).

Staging : `POST /api/telecom/fdsu-mno-staging/sync` → `telecom.fdsu_mno_sites` (hors KPI).

---

## 6. Modules enrichis

| Module | Enrichissement |
|--------|----------------|
| Smart Map | Couches 4 MNO + Planned + Fibre + MW + légende + popups NIRE |
| Spatial Matching | Relations nearest MNO / fibre / MW |
| NIRE | Audit inchangé ; qualités exposées à la carte |
| KPI national | **Inchangé** (Infrastructures Télécom) |

---

## 7. Cause des « détails indisponibles » (corrigée ciblée)

1. Airtel/Africell absents du catalogue Smart Map / `telecom.infrastructure` → **couches FDSU ajoutées**
2. Popups sans statut / RAT / provenance → **enrichis**
3. Fibre vs MW non séparés → **sous-couches typées**
4. NIRE layers isolés → **branchés via `/api/telecom/layers/*`**

---

## 8. Évolution future

- Ajouter un opérateur : entrée dans `LAYER_CATALOG` + éventuelle partition MNO
- Nouvelles sources fibre : seed KMZ + typage dérivé
- Promotion KPI : uniquement après validation institutionnelle explicite (écriture contrôlée dans `telecom.infrastructure`)

---

## 9. Référentiel sites opérateurs FDSU (prioritaire)

Voir [`TELECOM_OPERATOR_SITES_CONSOLIDATION_FDSU.md`](TELECOM_OPERATOR_SITES_CONSOLIDATION_FDSU.md) :

| Indicateur | Valeur |
|------------|-------:|
| Vodacom consolidé | **4 133** |
| Orange consolidé | **4 912** |
| Airtel | **4 477** |
| Africell | **784** |
| **TOTAL_MOBILE_OPERATOR_SITES_ALL** | **14 306** |
| Existing hors Planned | **12 843** |
| Planned | **1 463** |

Aucune déduplication inter-opérateurs. Fibre/MW hors ce total.

> Les chiffres d’infrastructures physiques mutualisées (12 289 / 15 614) sont une **autre** analyse — ne pas les mélanger avec ce référentiel sites opérateurs.
