# Data Activation Audit V1 — SIG-FDSU RDC

**Branche :** `feature/smart-map-interactions`

**Baseline commit :** `9621cebcd6fb5b1dcca9477d0b26389ef5c3d745`

**Date audit :** 2026-07-19

**Statut :** Audit + corrections P0 faible risque (pas de commit)

---

## Devise

> Une donnée n’est réellement intégrée que lorsqu’elle est exploitable dans les modules pertinents — pas parce que le fichier existe, qu’elle est en base, qu’un endpoint existe ou qu’elle apparaît dans un rapport.

Chaîne d’activation cible :

```
SOURCE → NORMALISATION / NIRE → RÉFÉRENTIEL / POSTGIS → API → CARTOGRAPHIE
→ RECHERCHE / FICHE → RELATIONS SPATIALES → NSME → SDG → INTELLIGENCE TERRITORIALE
→ CENTRE DE DÉCISION → DECISION WORKSPACE / DXL → SALLE DE PILOTAGE / EDVS → KPI
```

Statuts utilisés : `ACTIVE` | `PARTIAL` | `DORMANT` | `FALLBACK` | `BLOCKED` | `NOT_APPLICABLE` | `ABSENT`

---

## 1. Inventaire des sources

| Famille | Source autoritative | Persistance | API |
|---|---|---|---|
| Sites 40 | `data/programs/sites_40/` + `programs.fdsu_sites` | PostGIS | programmes / decision / inventory |
| Sites 300 | `data/programs/sites_300/` + `programs.fdsu_sites` | PostGIS | idem + scores |
| Sites 20 476 | `data/programs/sites_20476/` → sync NSME | PostGIS (native) | inventory + nsme-status |
| Portefeuille 340 | Agrégat 40+300 | dérivé | inventory `portfolio_340` |
| CCN | `data/programs/ccn/demo_ccn.json` (24) | fichier DEMO | `/api/ccn` |
| Télécom Vodacom/Orange/Fibre/MW/Fiberco/FTTX | `telecom.infrastructure` + layers | PostGIS | `/api/telecom/*` |
| Airtel / Africell / Planned | staging / NIRE MNO audit | partiel | couches map ; KPI exclus |
| Santé | `health.health_facilities` (37 562) | PostGIS | `/api/health/*` |
| Éducation | projection CENI SCHOOL (~23 604) | fichier/API | `/api/education/*` |
| CENI | registry fichier (~31 956 intégrés) | pas de schéma `ceni.*` | `/api/ceni/*` |
| Population / NCI | `data/coverage/*` (Excel → aggregates) | JSONL + agrégats | `/api/coverage/*` |
| Localités admin | `public.localites` (26 710) | PostGIS | admin / TI |
| Admin (26 / 145 / 733 / groupements) | référentiel territorial | PostGIS | admin |
| Routes | `transport.routes` (6 512) | PostGIS | transport / Smart Map |
| Autres (Energy, Agri, Hydro, Environnement) | NDF `planned` | — | ABSENT |

---

## 2. Matrice d’activation

Légende cellules : `Y` = oui / `P` = partiel / `N` = non / `—` = non applicable / `F` = fallback.

| Famille | Source | Autoritative | Norm. | NIRE | Base | Géom. | Index | API | Page/filtre | Carto | Couche | Popup | Fiche | Recherche | Rel. spat. | NSME | SDG | TI | CD | DXL | EDVS | KPI | **Statut** | Blocage principal | Action |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sites 40 | Y | Y | Y | P | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | **ACTIVE** | — | Maintenir |
| Sites 300 | Y | Y | Y | P | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | **ACTIVE** | UI score était manquant (corrigé) | Consommer scores dans DXL |
| Sites 20476 | Y | Y | Y | P | Y | Y | Y | Y | Y | N | N | P | Y | Y | P | Y | Y | P | Y | P | P | Y | **PARTIAL** | Pas de couche Smart Map (perf) | Enrichissement spatial par site |
| Portefeuille 340 | Y | Y | Y | — | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | **ACTIVE** | Confusion nominale historique | Garder = agrégat |
| CCN | Y | N (demo) | P | N | N | F | N | Y | P | P | P | P | P | P | F | F | P | P | P | P | P | P | **FALLBACK** | Inventaire prod absent | Sprint CCN natif |
| Vodacom | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | P | P | P | P | Y | **ACTIVE** | Propagation décision partielle | Brancher relations dans CD/DXL |
| Orange | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | P | P | P | P | Y | **ACTIVE** | Écart consolidé vs audit | Harmoniser comptages |
| Airtel | Y | P | P | Y | P | P | P | P | P | Y | Y | P | P | P | P | P | P | P | N | N | N | N | **PARTIAL** | `kpi_excluded` | Politique KPI officielle |
| Africell | Y | P | P | Y | P | P | P | P | P | Y | Y | P | P | P | P | P | P | P | N | N | N | N | **PARTIAL** | idem | idem |
| Planned MNO | Y | P | P | Y | P | P | P | P | P | Y | Y | P | P | P | P | P | P | P | N | N | N | N | **PARTIAL** | provisoire | Clarifier doctrine |
| Fibre / MW / Fiberco / FTTX | Y | Y | Y | P | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | P | P | P | P | P | **PARTIAL** | Linéaire TI incomplet | Consommation décision |
| Santé | Y | Y | Y | P | Y | Y | Y | Y | Y | P | P | Y | Y | Y | Y | Y | Y | Y | Y | P | P | Y | **ACTIVE** | Hors stack Smart Map principal | Overlay décision OK |
| Éducation | Y | N (proj.) | P | Y | N | P | N | Y | Y | N | N | P | P | P | N | N | N | P | P | N | N | P | **PARTIAL** | `nsme_wired: false` | Wiring NSME + SDG |
| CENI | Y | Y (KMZ) | Y | Y | N | Y | — | Y | Y | P | P | Y | Y | Y | N | N | N | P | N | N | N | Y | **PARTIAL** | Pas de relations SDG | Relations signal (pas sites FDSU) |
| Population NCI | Y | Y | Y | N | F | Y | — | Y | Y | P | P | P | P | Y | Y | P | Y | Y | Y* | P | Y | Y* | **PARTIAL→ACTIVE KPI** | UI CD était dormante (*corrigé*) | NIRE localités |
| Localités 26 710 | Y | Y | Y | P | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | P | P | Y | **ACTIVE** | Qualité/orphelins | Qualité continue |
| NCI cov/uncov | Y | Y | Y | N | F | Y | — | Y | Y | P | P | P | P | Y | P | P | Y | Y | Y | P | Y | Y | **PARTIAL** | Univers ≠ admin 26 710 | Classification NIRE |
| Admin provinces/terr. | Y | Y | Y | — | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | — | Y | Y | Y | Y | Y | Y | **ACTIVE** | — | — |
| Groupements | Y | Y | P | P | Y | Y | Y | Y | Y | Y | Y | P | P | P | P | — | P | P | P | P | P | P | **PARTIAL** | 27,8 % couverture | Compléter référentiel |
| Routes | Y | Y | Y | — | Y | Y | Y | Y | P | Y | Y | P | P | P | Y | Y | Y | P | P | P | P | P | **ACTIVE** | UI endpoints sous-utilisés | Brancher accessibilité |
| Energy / Agri / Hydro / Env | N | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | **ABSENT** | Sources non livrées | Hors sprint |
| Knowledge Hub / NDF UI | Y | P | P | — | P | — | — | Y | P | N | N | N | P | P | — | — | — | P | P | N | N | P | **DORMANT** | UI non consommée | Activation UI ciblée |

\* Population CD/EDVS : KPI nationaux branchés dans ce sprint.

### Synthèse comptages familles auditées

| Statut | Nombre | Familles |
|---|---:|---|
| **ACTIVE** | 9 | Sites 40, Sites 300, Portefeuille 340, Vodacom, Orange, Santé, Localités admin, Admin prov/terr, Routes |
| **PARTIAL** | 11 | Sites 20476, Airtel, Africell, Planned, Fibre/MW/Fiberco/FTTX, Éducation, CENI, Population NCI, NCI cov/uncov, Groupements, Collectivités (qualité) |
| **FALLBACK** | 1 | CCN DEMO |
| **DORMANT** | 1 | Knowledge Hub / NDF UI |
| **ABSENT** | 4 | Energy, Agriculture, Hydrographie, Environnement |
| **BLOCKED** | 0 | — |
| **Total familles** | **26** | (regroupements métier de la matrice) |

Note : CCN compté **FALLBACK**. Population NCI reste PARTIAL (KPI CD branchés ; NIRE localités manquant).

---

## 3. Données actives

- Sites 40 / 300 (NSME, scores, Smart Map, Decision Center)
- Santé 37 562 (`nsme_wired: true`)
- Vodacom / Orange consolidés + backbone partiel
- Référentiel administratif 26 / 145 + localités 26 710
- Routes principales 6 512
- Inventaire Sites + NSME 20 476 natif (structurel)

---

## 4. Données partiellement actives

- **Sites 20 476** : NSME natif + inventaire + SDG ; pas de couche Smart Map ; enrichissement spatial site-à-site inégal
- **Éducation** : API/KPI oui ; NSME/SDG non
- **CENI** : module + KPI oui ; relations décisionnelles non
- **NCI population** : API/TI/EDVS oui ; CD était non branché (corrigé)
- **Airtel/Africell/Planned** : carte/NIRE ; KPI nationaux exclus
- **Groupements** : couverture référentielle incomplète

---

## 5. Données dormantes

- UI Knowledge Hub / exploration NDF (API présente, surface produit faible)
- Couches NCI covered/uncovered peu exposées en Smart Map principale

---

## 6. Fallbacks

| Domaine | Fallback | Chemin nominal attendu |
|---|---|---|
| CCN | fichier DEMO 24 | PostGIS inventaire CCN |
| Sites 20476 | fichier si NSME vide | `programs.fdsu_sites` (désormais rempli) |
| Spatial matching CCN | fichier | PostGIS |
| Display name 20476 | `technical_id` (~427) | `infra_name` NCI (~20 049) |

---

## 7. Placeholders / textes à risque

| Occurrence | Classification | Action |
|---|---|---|
| CD Population « non encore calculée » | **B → corrigé** (données NCI existaient) | Branché |
| Sites 300 « Score FDSU À calculer » | **B → corrigé** (300 scores en DB) | Affiche « 300 scorés » |
| Définition KPI Sites FDSU « = 40+300 » | **C → corrigé** (valeur 20 816) | Texte mis à jour |
| CCN / Investissement pending | **A** (inventaire/budget absents) | Conserver pending |
| TI Éducation « En cours d’intégration » | **B/E** (projection CENI existe, NSME non) | P1 wiring |
| SDG « integrating » référentiels absents | **A/E** selon domaine | Cas par cas |
| Tooltip map `À calculer` si score null | **D** acceptable si vraiment null | OK |
| `Module Sites à construire` (historique) | **C** remplacé par inventaire | OK |

---

## 8. Population / couverture — audit

### Sources

| Rôle | Chemin | Comptage |
|---|---|---:|
| Localités non couvertes | `Localités non couvertes_10072026.xlsx` → `localities_uncovered.jsonl` | 24 575 uniques (24 604 lignes, 29 doublons) |
| Population coverage | `Population coverage-20260709-pop_vf.xlsx` → `localities_covered.jsonl` | 4 993 |
| Agrégats | `data/coverage/aggregates.json` | pop couverte **20 690 227** ; non couverte **52 575 042** ; total observé **73 265 269** |
| Ratios NCI | aggregates | localités **16,89 %** ; population **28,24 %** |

### Disponibilité calcul

| KPI | Calculable ? | Source | Branchement |
|---|---|---|---|
| Population couverte | **Oui** | NCI aggregates | **CD + explain-kpi corrigés** ; EDVS déjà OK |
| Population non couverte | **Oui** | NCI aggregates | idem |
| Localités couvertes / non couvertes | **Oui** (univers NCI) | NCI | TI / coverage API |
| Taux couverture pop / localités | **Oui** (NCI) | aggregates | API |
| Couverture par province / territoire | **Oui** | `by_province` / `by_territory` | API |
| Couverture par zone FDSU | **Partiel** | champ `fdsu_zone` NCI | à exposer KPI CD |
| Population « FDSU service universel effectif » | **Non** (définition métier distincte de NCI) | — | Ne pas inventer |

### Jointure

- Clé NCI `name` = souvent technique (pas toponyme admin)
- Toponyme utile ≈ `destination` (ambigu, fortes collisions)
- **Pas de FK NCI → `public.localites`**
- Appariement naïf `destination` ↔ `localites.nom` ≈ **14 %** → NIRE requis

---

## 9. Gap localités

| Métrique | Valeur | Lecture |
|---|---:|---|
| Référentiel national admin | **26 710** | Actifs territoriaux |
| NCI uncovered uniques | **24 575** | Univers besoins |
| NCI covered | **4 993** | Univers couverture pop |
| Somme NCI | **29 568** | ≠ 26 710 — **pas le même référentiel** |
| Doublons uncovered (lignes) | 29 | quality_report |
| Collision `destination` covered∩uncovered | élevée | homonymes / destinations partagées |
| Match naïf destination → admin | ~14 % | nomenclature divergente |

### Classification NIRE proposée

| Code | Sens |
|---|---|
| `MATCHED_LOCALITY` | Appariement confiant NCI ↔ admin |
| `PROBABLE_MATCH` | Score NIRE élevé, revue optionnelle |
| `AMBIGUOUS_LOCALITY` | Plusieurs candidats admin |
| `UNMATCHED_COVERED` | Couverte NCI sans pair admin |
| `UNMATCHED_UNCOVERED` | Non couverte NCI sans pair admin |
| `DUPLICATE_LOCALITY` | Doublon intra-source |
| `CONFLICTING_COVERAGE_STATUS` | Même identité dans covered et uncovered |

**Ne pas forcer l’égalité des totaux.** Expliquer les univers (admin ≠ NCI ≠ baseline UNSD ~78 855).

---

## 10. CENI

| Question | Réponse |
|---|---|
| En base PostGIS dédiée ? | **Non** (registry fichier) |
| Cartographiés ? | **Oui** (module CENI) |
| Couche Smart Map principale ? | **Non** |
| Popups / fiches ? | **Oui** (module) |
| Relations spatiales NSME ? | **Non** |
| SDG ? | **Non** (`sdg_relations_active: false`) |
| Intelligence territoriale ? | **Partiel** (NIRE / projection éducation) |
| Moteur de décision ? | **Non direct** |

Doctrine : CENI ≠ sites FDSU. Usages légitimes : signal de présence humaine, infrastructure publique, activité administrative, besoin de connectivité.

---

## 11. Santé

- **ACTIVE** bout-en-bout moteurs (NSME/SDG/KPI)
- 37 562 établissements, types ESS
- Moins visible dans stack Smart Map « connectivité » (overlay décision)
- Critères décision `sante` encore poids 0 dans moteur (pending sectoriel) → P1

---

## 12. Éducation

- **PARTIAL** : projection CENI SCHOOL + API nationale
- `nsme_wired: false`, SDG `available: false`
- Chaînon manquant : persistance PostGIS + relations `NEAR_SCHOOL` + consommation Decision Engine
- Pas de registre ministériel officiel distinct

---

## 13. Télécom / Fibre / MW

- Activation cartographique récente consolidée (Vodacom/Orange/backbone)
- Relations NSME (`NEAREST_MNO_*`, `NEAR_FIBER`, MW) présentes
- Propagation **inégale** vers Decision Workspace / DXL / fiches d’impact
- Airtel/Africell/Planned : carte oui, KPI national non (politique)

---

## 14. Sites FDSU

| Programme | NSME | Inventaire | Smart Map | Scores | Notes |
|---|---|---|---|---|---|
| 40 | Y | Y | Y | Y | ACTIVE |
| 300 | Y | Y | Y | Y (300) | UI score corrigée |
| 20 476 | Y | Y | N | structurel SDG | Enrichissement spatial ≠ « loaded » |
| 340 | agrégat | Y | via 40/300 | Y | Pas un 3ᵉ programme |

Contexte Santé/Éducation/Télécom/CENI/Population pour un site 20 476 : **disponible au niveau plateforme**, pas systématiquement matérialisé site-à-site.

---

## 15. NSME / SDG

- Taux NSME natif sites FDSU ≈ **99,9 %** après sync 20 476
- SDG : Sites + Santé + Télécom + Routes + NCI ; Éducation/CENI hors relations
- « Complete » SDG = structurel (en base + coords), **pas** enrichissement sectoriel total

---

## 16. Corrections appliquées (ce sprint)

1. **P0** — KPI CD `population_covered` / `population_uncovered` branchés sur NCI (`decision_engine_service` + `decision_demo_service` + HTML).
2. **P0** — Panneau Sites 300 : « À calculer » → « 300 scorés » via `/api/decision/site-scores`.
3. **P0** — Définition KPI Sites FDSU alignée sur le total NSME réel (~20 816).
4. Tests unitaires `tests/test_data_activation_population_kpis.py` + E2E expectations mises à jour.
5. Rapport + doctrine d’activation (ci-dessous).

---

## 17. Corrections restantes (hors scope contrôlé)

| Priorité | Item |
|---|---|
| P1 | Wiring NSME/SDG Éducation + relations décision |
| P1 | Relations spatiales CENI (signal, pas site FDSU) |
| P1 | Consommation relations télécom dans DXL / dossiers |
| P1 | Critères sectoriels moteur (`sante`, `education`, `population` poids > 0 quand données OK) |
| P1 | Campagne NIRE localités NCI ↔ admin |
| P2 | Couche Smart Map NCI covered/uncovered ; option Sites 20476 (perf) |
| P2 | CCN PostGIS inventaire réel |
| P2 | Harmonisation comptages Orange consolidé vs audit |
| P3 | UI Knowledge Hub / NDF |
| P3 | Couverture groupements |

---

## 18. Recommandations prioritaires

### P0

1. ~~Population CD affichée vide alors que NCI existe~~ **FAIT**
2. ~~Sites 300 score UI faux~~ **FAIT**
3. ~~Libellé Sites FDSU obsolète~~ **FAIT**

### P1

1. Brancher Éducation dans NSME/SDG
2. Relations CENI → décision (signal)
3. Propager télécom nearest/fibre/MW dans workspace décisionnel
4. NIRE gap localités (classification ci-dessus)
5. Activer poids critères sectoriels là où données existent

### P2 / P3

Voir §17.

---

## Doctrine d’activation des données (checklist obligatoire)

Toute nouvelle source **doit** passer cette checklist avant d’être déclarée « intégrée » :

1. **Provenance** documentée (fichier, producteur, date, hash)
2. **Source autoritative** désignée (une seule)
3. **Normalisation** (schéma, types, unités)
4. **NIRE** si identités / toponymes variables
5. **Persistance** PostGIS ou store officiel
6. **Géométrie** + validité
7. **API** paginée / filtrable
8. **Cartographie** (couche ou justification d’exclusion)
9. **Fiche** détail métier
10. **Relations spatiales** si valeur décisionnelle
11. **NSME** si actif spatial
12. **SDG** si contribution au graphe
13. **Décision** (CD / DXL / dossier) si pertinent
14. **KPI** branchés (jamais « À calculer » si calculable)
15. **Tests** (unitaires + integrity gate si impact décision)
16. **Documentation** (audit / changelog activation)

Réf. croisée : `DATA_FIRST_INTEGRATION_POLICY.md`, `E2E_INTEGRITY_GATE.md`.

---

## Validations

| Suite | Statut |
|---|---|
| `tests/test_data_activation_population_kpis.py` | **3 passed** |
| `test_coverage_intelligence` + `test_decision_kpi_details` | **passed** (avec activation) |
| sites / NSME / SDG / telecom / CCN (batch ciblé) | **89 passed** (+1 assertion test fixée ensuite → 3/3 activation OK) |
| E2E Playwright `decision-center.spec.js` | Expectations mises à jour ; **exécution navigateur** non garantie si Chromium absent |

---

*Fin Data Activation Audit V1.*
