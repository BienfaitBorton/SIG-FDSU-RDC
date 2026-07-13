# Data First Integration Audit v1.0 — SIG-FDSU RDC

**Date :** 2026-07-12  
**Périmètre :** Plateforme complète (API, services, data/, dashboard)  
**Mode de référence :** `DATA_MODE=db`

---

## 1. Inventaire des référentiels

| Référentiel | Existe | Données | Géométries | API | Service | Calculs | Relations spatiales | Modules UI | Maturité |
|---|---|---|---|---|---|---|---|---|---|
| Administratif (prov→loc) | Oui | Peuplé (PostGIS) | Oui | `/provinces`…`/villages`, map | province…village_service | TST/TI | NDF contains | Cartographie, TST, TDT | 🟢 |
| Population / NCI | Oui | 24k+ loc. non couvertes | Points | `/api/coverage/*` | coverage_intelligence | NDCI, agrégats | SERVES_LOCALITY | Indirect (ESR, TI, TST) — **pas de module Coverage** | 🟡 |
| Localités non couvertes | Oui | JSONL | Points | via Coverage + NSME | NCI / NSME | Matching | Oui | SDG, DXL | 🟢 |
| Sites 40 | Oui | Fichier + DB | Oui | `/api/programs/sites40` | program_service | Scores | Asset NSME | Cartographie, Decision Center | 🟢 |
| Sites 300 | Oui | Fichier + DB | Oui | `/api/programs/sites300` | program_service | Scores | Asset NSME | Cartographie, Decision Center | 🟢 |
| Sites / Programme 20476 | Oui | 20 476 fichiers | GeoJSON | priorities + import-national | fdsu_sites_import | Scores si importé | Asset | Decision Center (filtre) | 🟡 |
| Master Registry | Oui | Bootstrap (~267) | Partiel | `/api/master/*` | master_registry | Codes FDSU | Identité TDT | Panel Decision Center | 🟡 |
| National Data Fabric | Oui | Catalog 18 registres | Meta | `/api/national-data-fabric/*` | ndf_service | Qualité | 42 relations doc. | **Aucun UI** | 🟡 |
| Santé | Oui | 37 562 établissements | Points | `/api/health/*` | health_service | Stats, nearest PostGIS | NEAREST / NEAR / WITHIN_HEALTH (NSME ← `health.health_facilities`) | SDG + Decision Center | 🟢* |
| Télécom / Fibre | Oui | Sectoral + DB | Multi | `/api/telecom/*` | telecom_service | Stats | NEAR_FIBER/BACKBONE | Cartographie + panel | 🟡 |
| Routes / Transport | Oui | 6 512 segments | LineString | `/api/transport/*` | transport_service | Accessibilité | NEAR_MAIN_ROAD… | Carte + Workspace | 🟡 |
| CCN | Oui | 24 demo | Points | `/api/ccn/*` | ccn_* | Capability | CONNECTS_CCN | Module CCN | 🟡 |
| Knowledge Hub | Oui | Structure | — | `/api/knowledge/*` | knowledge_hub | — | — | **Non consommé** (CNCT legacy `/knowledge`) | 🔴 |
| Éducation | Non | — | — | — | — | — | NEAR_SCHOOL (futur) | SDG future | 🔵 |
| Énergie | Non | — | — | — | — | — | — | TDT notes / SDG future | 🔵 |
| Marchés / économie | Non | — | — | — | — | — | NEAR_MARKET (futur) | SDG future | 🔵 |
| Agriculture / Climat / Eau / Sécurité | Non (NDF planned) | — | — | — | — | — | — | — | 🔵 |

\* Santé (correctif P0 2026-07-12) : NSME interroge `health.health_facilities` (SRID 4326, GIST). Relations `NEAREST_HEALTH_FACILITY`, `NEAR_HEALTH_FACILITY`, `WITHIN_HEALTH_SERVICE_AREA`. Rayons configurés dans `spatial_matching_rules.json` (`health_proximity` / `health_service_area` = 5 km, `health_nearest_max` = 25 km). Maturité 🟢 Opérationnel si relations PostGIS ; 🟡 Partiel si recherche exécutée sans établissement dans le rayon.

---

## 2. Inventaire des API (préfixes)

| Préfixe | Rôle | Consommé UI ? |
|---|---|---|
| `/api/decision` | Decision Engine / cases / scenarios | Oui |
| `/api/executive` | Cockpit + Situation Room | Oui |
| `/api/spatial-decision-graph` | SDG v2.1 | Oui |
| `/api/spatial-matching` | NSME | Partiel (pas `/refresh`) |
| `/api/coverage` | NCI | **Non** |
| `/api/territorial-summary` | TST | Oui |
| `/api/territorial-intelligence` | TI | Oui |
| `/api/territorial-digital-twin` | TDT | Oui |
| `/api/transport` | Routes | Partiel |
| `/api/telecom` | Télécom | Partiel (layers + panel) |
| `/api/health` | Santé | Panel + layer |
| `/api/programs` | Programmes | Oui |
| `/api/master` | Master Registry | Panel seulement |
| `/api/national-data-fabric` | NDF | **Non** |
| `/api/knowledge` | Knowledge Hub | **Non** |
| `/api/ccn` | CCN | Oui |
| `/api/analysis` | Spatial Intelligence | Partiel |
| `/api/reference` | NRF | Panel |
| `/api/geocoding` | Géocodage | Oui |
| `/api/exports` | Exports | Oui |
| `/knowledge` | CNCT legacy | Oui (app.js) |
| `/provinces`…`/photos` | CRUD admin | Backend / legacy |

---

## 3. Inventaire des moteurs

| Moteur | Service | Exploité ? |
|---|---|---|
| National Coverage Intelligence (NCI) | `coverage_intelligence_service` | Oui (indirect) |
| NSME | `spatial_matching_service` | Oui — refresh UI manquant |
| Spatial Decision Graph | `spatial_decision_graph_service` | Oui (v2.1) |
| Decision Engine | `decision_engine_service` | Oui |
| Explainable Decision | `explainable_decision_service` | Oui |
| Decision Scenarios | `decision_scenarios_service` | Oui |
| Territorial Summary (TST) | `territorial_summary_service` | Oui |
| Territorial Intelligence | `territorial_intelligence_service` | Oui |
| Territorial Digital Twin | `territorial_digital_twin_service` | Oui |
| Executive / ESR | `executive_*` | Oui |
| Transport Accessibility | `transport_service` | Partiel |
| Spatial Analysis (legacy) | `spatial_analysis_service` | Partiel |
| Knowledge Hub | `knowledge_hub_service` | **Non branché UI** |
| Master Registry | `master_registry_service` | Partiel |
| Site Entity Resolver | `site_entity_resolver` | Oui |

---

## 4. Données déjà exploitées

- Localités / population NCI → NSME → SDG → DXL  
- Sites FDSU 40/300 → cartographie, scoring, dossier  
- Routes (si DB) → carte + NSME + Workspace  
- Télécom layers → cartographie  
- Santé panel → Decision Center  
- CCN demo → module CCN + NSME CONNECTS_CCN  
- TST / TI / TDT / ESR → composition multi-sources  

---

## 5. Données disponibles mais non (ou mal) exploitées

| Donnée | Symptôme |
|---|---|
| NCI `/api/coverage` | Aucun appel dashboard |
| NDF catalog | API-only, pas d’explorateur |
| Knowledge Hub `/api/knowledge` | UI utilise CNCT `/knowledge` |
| Santé 37k établissements | **Corrigé P0** — matching NSME PostGIS `health.health_facilities` |
| Transport stats / nearest | Endpoints non appelés UI |
| Telecom infrastructure / nearby-sites | Non appelés |
| NSME `POST /refresh` | Jamais depuis l’UI |
| sites_20476 import-national | API sans bouton opérationnel |
| Master SITE/CCN | 0 entités SITE dans registry.json |
| SDG types `NEAR_FDSU_SITE`, `NEAR_CCN`, `COVERAGE_NEED` | Déclarés, non émis NSME |

---

## 6. Anomalies d’intégration (extrait)

Voir `INTEGRITY_GATE_REPORT_V1.md` pour la liste priorisée A1–A14.

---

## 7. Priorisation (matrice métier FDSU)

| Priorité | Action |
|---|---|
| P0 | ~~Brancher NSME sur `health.health_facilities` (CAS 4)~~ **FAIT** |
| P0 | ~~Profil territorial partagé (admin/santé/télécom/routes/superficie)~~ **FAIT** — voir `TERRITORIAL_DATA_FIRST_COMPLETENESS_AUDIT_V1.md` |
| P0 | Exposer refresh NSME depuis Decision Center |
| P1 | Surface NCI / Coverage dans UI ou liens ESR→coverage |
| P1 | Aligner SDG relation_types ↔ NSME émis |
| P1 | Consolider Knowledge Hub vs CNCT |
| P2 | Import sites_20476 + Master SITE |
| P2 | Explorateur NDF léger |
| P2 | Fibre linéaire + CCN production |
| P3 | Référentiels Education / Énergie / Marchés (🔵 normal) |

---

## 8. Plan d’intégration recommandé

1. **Court terme** — Corriger anomalies P0 (santé NSME, refresh, zéros expliqués SDG).  
2. **Moyen terme** — NCI UI, alignement SDG/NSME, Knowledge Hub.  
3. **Long terme** — Nouveaux référentiels (Education…) en maturité 🔵 jusqu’à peuplement.

Correctifs livrés dans ce sprint :

- Politique Data First officielle  
- Classification SDG CAS 1–4 + `maturity` / `empty_reason`  
- Panneau détail enrichi  
- Rapports d’audit et Integrity Gate  

---

## Confirmation d’exhaustivité

L’inventaire couvre Master Registry, NDF, TST, TDT, Decision Engine, Explainable Decision, Workspace, ESR, Scenarios, NSME, Spatial Matching, Santé, Télécom, Fibre, Routes, Transport, Population, Localités, Admin, Sites 40/300/20476, CCN, Knowledge Hub, ainsi que les routers `api/routes/*` et services `api/services/*` recensés.
