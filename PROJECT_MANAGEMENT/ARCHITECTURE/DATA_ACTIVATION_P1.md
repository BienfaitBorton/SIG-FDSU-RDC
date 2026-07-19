# Data Activation P1 — SIG-FDSU RDC

**Branche :** `feature/smart-map-interactions`  
**Baseline :** `cd2d275` (Data Activation Audit V1 + P0)  
**Date :** 2026-07-19  
**Statut :** Implémentation P1 — **aucun commit** (en attente validation)

---

## 1. Éducation — avant / après

| Dimension | Avant | Après |
|---|---|---|
| Source | Projection CENI SCHOOL (~23 604) API seule | Inchangée (autoritative dérivée) |
| PostGIS dédié | Non | Non (Haversine + bbox, cache mémoire) |
| `nsme_wired` | `false` | **`true`** |
| SDG `available` | `false` / future | **`true`** |
| Relations | Stub `NEAR_SCHOOL` NCI seulement | **`NEAREST_SCHOOL`**, **`NEAR_SCHOOL`**, `EDUCATION_SEARCH_EXECUTED` |
| Maturité | `_eval_absent` | `_eval_education()` |
| Scoring moteur | poids `education` = 0 | **Inchangé** — signal exposé, non pondéré |
| DXL / dossier | Absent | `education_context` + impacts `ecoles_concernees` |

**Note :** pas de registre ministériel officiel — `derived_projection: true`.

---

## 2. CENI — avant / après

| Dimension | Avant | Après |
|---|---|---|
| Registry fichier | ~31 956 intégrés | Inchangé |
| PostGIS `ceni.*` | Absent | Absent |
| NSME / SDG | Non | **`NEAREST_CENI_SIGNAL`**, **`NEAR_CENI_SITE`** |
| Catégorie SDG | — | **`ceni`** (signal institutionnel) |
| = sites FDSU ? | — | **Non** (`not_fdsu_sites`, `asset_domain=INSTITUTIONAL`) |
| Scoring | — | **Non pondéré** — « Signal disponible — non pondéré dans le scoring actuel » |
| DXL | Absent | `ceni_context` |

Les SCHOOL CENI sont exclus du matcher CENI (évite double comptage avec Éducation).

---

## 3. Télécom / Fibre / MW → DXL — avant / après

| Dimension | Avant | Après |
|---|---|---|
| Calcul NSME / `/api/telecom/spatial-context` | Oui | Oui |
| Styles SDG MNO/fibre/MW/mutualisation | Absents → category `needs` | **Enregistrés** dans `RELATION_STYLES` + `CATEGORIES.telecom` |
| `need_lat` / `need_lon` sur matches contexte | Souvent absents | **Ajoutés** |
| Dossier (`build_site_case`) | Pas de telecom | **`telecom_context`** (opérateurs, fibre, MW, backhaul, mutualisation, `summary_lines`) |
| UI DXL | Contexte TI seulement | **Bloc « Preuves spatiales »** (télécom / éducation / CENI) |

Aucune recommandation automatique inventée.

---

## 4. Localités NCI ↔ admin (NIRE)

Service : `api/services/nire/locality_coverage.py`  
API : `POST/GET /api/nire/locality-coverage/{run,status,summary,rows}`

### Univers (non forcés égaux)

| Univers | Effectif |
|---|---:|
| Admin `localites` | 26 710 |
| NCI covered | 4 993 |
| NCI uncovered | 24 604 |
| Observations NCI | 29 597 |

### Résultats run post-audit cohérence (2026-07-19)

| Classification | Nombre |
|---|---:|
| `MATCHED_LOCALITY` | **3 727** |
| `PROBABLE_MATCH` | **89** |
| `AMBIGUOUS_LOCALITY` | **391** |
| `UNMATCHED_COVERED` | **0** |
| `UNMATCHED_UNCOVERED` | **16 636** |
| `DUPLICATE_LOCALITY` | **29** |
| `COVERAGE_STATUS_REQUIRES_REVIEW` | **8 725** |
| `CONFLICTING_COVERAGE_STATUS` | **0** (confirmés) |
| Identités dual-source | **4 971** (10 154 observations) |
| Taux MATCHED+PROBABLE | **12,89 %** |

Voir **FINAL COHERENCE AUDIT** ci-dessous.

---

## 5–8. Population territoriale

Déjà calculable via NCI `aggregates.json` / `/api/coverage/provinces|territories` :

- population couverte / non couverte **par province**
- population couverte / non couverte **par territoire**
- nationaux : **20 690 227** / **52 575 042**

Le service NIRE **ne recalcule pas** ces totaux — il les expose dans `summary`.

---

## 9. Signaux NSME / SDG

| Signal | Calculé | NSME | SDG style | Pondéré scoring |
|---|---|---|---|---|
| NEAREST/NEAR_SCHOOL | Oui | Oui | Oui | Non (poids 0) |
| NEAREST_CENI / NEAR_CENI | Oui | Oui | Oui | Non |
| NEAREST_MNO_* / FIBER / MW / MUTUALIZATION | Oui (existait) | Oui | **Oui (nouveau)** | Non (preuves) |
| Canonical locality match | Oui (NIRE) | API NIRE | Indirect | Non |

« SDG complet » **non déclaré** : enrichissement de signaux, pas couverture structurelle totale.

---

## 10. Signaux réellement utilisés en décision

| Signal | Dans dossier / DXL | Dans score priorité |
|---|---|---|
| NCI population / NDCI | Oui (`needs_intelligence`) | Via critères existants |
| Télécom contexte | **Oui** (`telecom_context`) | Non (preuves) |
| Éducation | **Oui** (`education_context`) | Non (poids 0) |
| CENI | **Oui** (`ceni_context`) | Non |
| Santé | NSME existant | Non (poids 0) |

---

## 11. Corrections appliquées

1. Matcher + nearest Éducation ; probe/maturité/SDG  
2. Matcher + nearest signal CENI ; catégorie SDG  
3. Styles télécom étendus + coords + `telecom_context` + UI DXL  
4. Service NIRE localités + API  
5. Règles spatiales (`school_*`, `ceni_*`, relations MNO)  
6. Tests P1 + mise à jour SDG  

## 12. Actions restantes

| Priorité | Action |
|---|---|
| P1+ | Campagne revue humaine NIRE (ambiguïtés / conflits) |
| P1+ | PostGIS `education.*` / `ceni.*` si perf nationale requise |
| P2 | Couches Smart Map éduc/CENI/NCI avec clustering |
| P2 | Activer poids critères `education` / `sante` / `population` quand doctrine métier validée |
| P2 | Clarifier côté métier le chevauchement des deux Excel NCI (dual-source) |

---

## Tests

- `tests/test_data_activation_p1.py` — homonymes, dual-source revue, conservation observations
- `tests/test_spatial_decision_graph.py`, coverage, CENI, education, spatial matching
- E2E navigateur : non bloquant si Chromium absent

---

## FINAL COHERENCE AUDIT

### Définition réelle covered / uncovered

| Statut NCI | Fichier source | Dataset | Sémantique |
|---|---|---|---|
| **covered** | `Population coverage-*.xlsx` | `population_coverage` | Observation du fichier « population couverte » — **par observation / source**, pas un statut national global |
| **uncovered** | `Localités non couvertes_*.xlsx` | `localities_uncovered` | Observation du fichier « localités non couvertes » — liste de besoins / planification |

**Ce n’est pas :**

- un booléen exclusif global ;
- un statut par opérateur ;
- un statut par technologie ;
- une série temporelle datée dans les champs importés.

Les deux listes se chevauchent massivement sur les projets communs (ex. CENI 4 604 dans chaque fichier, Project Simba New 333, etc.). Une même identité dans les deux fichiers **n’est donc pas une contradiction métier prouvée**.

### Explication des 4 971 identités dual-source

- Clé : toponyme normalisé + province + territoire + cellule géo (~100 m).
- **10 154 observations** partagent une identité présente dans covered **et** uncovered.
- Classification finale : **`COVERAGE_STATUS_REQUIRES_REVIEW`** si aucun match admin fiable ; si match admin → MATCHED/PROBABLE/AMBIGUOUS **conservé** + flag `dual_source_observation`.
- **`CONFLICTING_COVERAGE_STATUS` = 0** confirmés (aucune contradiction prouvée après audit).

### Classification finale des cas

| Classe | Sens métier |
|---|---|
| MATCHED / PROBABLE / AMBIGUOUS | Rapprochement admin (nom + province/territoire + géo) |
| UNMATCHED_UNCOVERED | Observation uncovered sans pair admin |
| UNMATCHED_COVERED | Aucune (toutes les covered non matchées sont dual-source → revue) |
| DUPLICATE_LOCALITY | Doublon intra-source |
| COVERAGE_STATUS_REQUIRES_REVIEW | Dual-source sans match admin — revue neutre |
| CONFLICTING_COVERAGE_STATUS | Réservé aux contradictions confirmées (non utilisé) |

### Funnel de rapprochement

| Étape | Effectif |
|---|---:|
| Observations NCI totales | 29 597 |
| Toponyme exploitable | 29 597 |
| Province identifiable | 29 597 |
| Territoire identifiable | 29 597 |
| Coordonnées exploitables | 29 597 |
| Hit nom dans index admin | **4 833** |
| Exact match | 3 727 |
| Probable | 89 |
| Ambiguous | 391 |
| Unmatched / revue | 25 361 |
| Dual-source observations | 10 154 |

### Cause principale du taux (~12,9 %)

**Principal facteur des 16 636 UNMATCHED_UNCOVERED :** `toponyme_absent_du_referentiel_admin` — le toponyme NCI (`destination`) n’existe pas (ou pas sous cette forme) dans les 26 710 localités admin.

Second facteur : **8 725** dual-source sans match admin → `COVERAGE_STATUS_REQUIRES_REVIEW`.

Le taux n’a **pas** été artificiellement augmenté (seuils inchangés ; blocage homonymes province/territoire renforcé).

### Homonymes

- Province différente → `PROVINCE_MISMATCH_BLOCKED` (score 0).
- Même province, territoire différent → `TERRITORY_MISMATCH_BLOCKED` (score 0).
- MATCHED exige `PROVINCE_MATCH` (pas de fusion sur nom seul).

### Limites des données

- Univers NCI ≠ admin (29 597 obs. vs 26 710 localités).
- `name` NCI souvent technique ; toponyme utile = `destination` (homonymes fréquents).
- Pas de date / opérateur / techno dans le statut de couverture importé.
- Province `#N/A` : pop couverte 23 046 / non couverte 34 350.

### Exemples vérifiés

**Éducation — Site FDSU 1 (Yengembana-Ext_KOC, Kasaï)**  
- `NEAREST_SCHOOL` / `NEAR_SCHOOL` → **EP ITONO** à **2,0 km**  
- Source : projection CENI SCHOOL · `nsme_wired=true` · poids moteur education = 0  

**Éducation — Site 29 (Village Nsona)**  
- Plus proche : **EP KIMAZA NORD** à **3,2 km**

**CENI — Site 29**  
- `NEAREST_CENI_SIGNAL` → **CENTRE DE SANTE ET MATERNITE PAPA DIALUNGANA** à **12,0 km**  
- `not_fdsu_site=true` · `scoring_weighted=false` · sources brutes non modifiées  

**CENI — Site 15 (Mukoyi)**  
- Signal à **428 m** (CENTRE DE SANT MUKOYI) · famille institutionnelle distincte  

**Télécom/DXL — Site 29** (`telecom_context.summary_lines`)  
- Fibre : 8,2 km · MW : 9,8 km · Vodacom : 7,9 km · Orange : 8,0 km · Airtel : 8,0 km  
- Absence d’opérateur ≠ erreur technique (`available` + hits null)  

**Population**  
- National 20 690 227 / 52 575 042  
- Somme provinces = national exact (`delta 0`)  
- Clé non rattachable : `#N/A`

### Corrections appliquées dans cet audit

1. Remplacement du conflit automatique par **`COVERAGE_STATUS_REQUIRES_REVIEW`**.  
2. Conservation des MATCHED malgré dual-source.  
3. Blocage homonymes inter-province / inter-territoire.  
4. Funnel + sémantique documentés dans KPIs NIRE.  
5. Tests homonymes / dual-source / conservation observations.  
6. Mise à jour de ce rapport.

---

## LOCALITY REFERENTIAL ENRICHMENT AUDIT

**Date :** 2026-07-19  
**Statut :** Audit préparatoire — **référentiel non modifié** — **aucune intégration** — **aucun commit**

### 1. Référentiel actuel (26 710)

| Élément | Valeur |
|---|---|
| Source autoritative | `data/reports/locality_official/locality_referential_official.json` (dérivé `Localités.kmz`) |
| Identifiant | `canonical_id` |
| Nom | `nom` |
| Province / territoire | `province`, `territoire` |
| Collectivité | `collectivité` / metadata `COLLECTIV` |
| Groupement | `groupement` |
| Coordonnées | `geometry.coordinates` [lon, lat] |
| Provenance | `source` / `metadata.source_file` |
| Effectif | **26 710** |
| Modifié pendant l’audit | **Non** |

Fallback PostGIS `public.localites` possible si JSON absent — non utilisé ici.

### 2. Univers NCI

| Univers | Effectif |
|---|---:|
| Observations covered (`population_coverage`) | 4 993 |
| Observations uncovered (`localities_uncovered`) | 24 604 |
| Total observations brutes | **29 597** |
| Identités NCI uniques estimées (topo+prov+terr+geo~100 m) | **24 391** |

29 597 ≠ 29 597 localités uniques — déduplication **analytique** uniquement (sources inchangées).

### 3. Méthode de comparaison

1. Réutiliser le rapprochement NIRE (`locality_coverage`) → scope = `UNMATCHED_*` + `COVERAGE_STATUS_REQUIRES_REVIEW`.
2. Grouper par identité canonique (covered∩uncovered = **une** localité ; statut couverture = observation).
3. Classer chaque identité / observation :
   - `EXISTING_LOCALITY_VARIANT` — même contexte (province + territoire ou géo) + nom proche
   - `DUPLICATE_NCI_OBSERVATION` — observations supplémentaires de la même identité
   - `HOMONYM_DIFFERENT_LOCALITY` — même nom normalisé, autre contexte admin
   - `AMBIGUOUS_LOCALITY` — plusieurs variantes proches
   - `NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE` — preuves multiples + isolé (>2,5 km admin) + bbox province
   - `NEW_LOCALITY_CANDIDATE_REVIEW` — potentiel mais preuves partielles / voisinage géo
   - `UNRESOLVED_LOCALITY` — champs insuffisants
4. **Jamais** : fusion sur nom seul ; création auto ; forçage du référentiel à croître.
5. Service : `api/services/nire/locality_enrichment_audit.py`  
   API : `POST/GET /api/nire/locality-enrichment/{run,status,summary,rows}`

### 4. Funnel UNMATCHED_UNCOVERED (16 636)

| Étape | Effectif |
|---|---:|
| UNMATCHED_UNCOVERED | 16 636 |
| Nom exploitable | 16 636 |
| Coordonnées valides | 16 636 |
| Province identifiable | 16 636 |
| Territoire identifiable | 16 636 |
| Contexte admin suffisant | 16 636 |
| Variantes existantes probables | 3 588 |
| Ambiguïtés | 736 |
| Homonymes | 1 070 |
| Doublons NCI (obs.) | 2 |
| Candidates high confidence | **6 296** |
| Candidates review | **4 944** |
| Unresolved | 0 |

**Cause principale du non-appariement :** `absent_from_admin_referential_with_coherent_context` (toponyme absent du référentiel avec contexte admin/géo cohérent) — pas une création automatique.

### 5–10. Bilan classifications (identités in-scope, sauf DUP = observations)

| Classe | Identités / obs. |
|---|---:|
| EXISTING_LOCALITY_VARIANT | **4 595** |
| DUPLICATE_NCI_OBSERVATION | **4 450** obs. |
| HOMONYM_DIFFERENT_LOCALITY | **1 240** |
| AMBIGUOUS_LOCALITY | **941** |
| NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE | **7 532** |
| NEW_LOCALITY_CANDIDATE_REVIEW | **6 603** |
| UNRESOLVED_LOCALITY | **0** |

Dont covered absorbés (dual-source / non canoniques) → HC **1 236** / review **1 659** (l’enrichissement n’est pas limité aux uncovered).

### 11. Nouveau total potentiel (préparatoire)

```
POTENTIAL_ENRICHED_LOCALITY_COUNT = 26 710 + 7 532 = 34 242
```

**Non appliqué** au référentiel pendant cet audit.

### 12. Impact couverture (si HC validées puis intégrées — hypothétique)

| Indicateur | Actuel | Potentiel (HC only) |
|---|---:|---:|
| Localités référentiel | 26 710 | 34 242 |
| Taux appariement NCI (MATCHED+PROBABLE) | 12,89 % | **~42,7 %** |
| Population rattachable HC (somme obs. identités) | — | ~12,9 M |
| Population rattachable review | — | ~15,9 M |
| `coverage_status_requires_review` | 8 725 | Non recalculé artificiellement |

Les KPI nationaux population/coverage **ne sont pas recalculés** tant que les candidates ne sont pas validées.

### 13. Impact modules (futur, non activé)

| Module | Impact potentiel |
|---|---|
| Cartographie | Nouveaux points localités après intégration validée |
| Référentiel hiérarchique | Attachements province/territoire/collectivité à valider |
| NIRE | Statut `pending_human_validation` → matched |
| NSME / SDG | Relations sites↔localités élargies — pas d’activation audit |
| Intelligence territoriale | Population rattachable documentée seulement |
| Centre de Décision | Pas de nouveau score tant que non validé |

### 14. Stratégie d’intégration future (idempotente, non exécutée)

1. Validation humaine des `NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE` (puis review).
2. `canonical_id = RDC-NCI-LOC-{sha1(name|prov|terr|geo|nci)[:12]}`.
3. Upsert par `idempotency_key` — 2ᵉ exécution = no-op.
4. Champs : provenance NCI, nom source/normalisé, rattachement, géométrie, statut NIRE, date intégration.
5. Conserver séparément identité canonique ↔ observations covered/uncovered.
6. **Aucune intégration massive sans validation.**

Cache dérivé (non brut) : `data/cache/nire_locality_enrichment_audit_v1.json`.

---

## PRE-INTEGRATION IDENTITY VALIDATION

**Date :** 2026-07-19  
**Statut :** Validation d’identité territoriale — **aucune intégration** — **référentiel 26 710 inchangé** — **aucun commit**

### Politique corrigée

- La distance à une autre localité **n’est ni une preuve de nouveauté ni un motif de rejet**.
- La proximité spatiale reste un **signal de rapprochement** (avec nom), jamais une règle de fusion/exclusion.
- Critère retiré : « aucune localité admin < 2,5 km ».

### 1–2. Requalification des HIGH_CONFIDENCE

| Étape | Effectif |
|---|---:|
| HC baseline (audit précédent, règle 2,5 km) | **7 532** |
| HC après retrait règle distance (re-pool) | **12 036** |
| → READY_FOR_INTEGRATION | **3 182** |
| → REQUIRES_HUMAN_REVIEW | **8 802** |
| → EXISTING_LOCALITY_VARIANT (récupérées) | **52** |
| → DUPLICATE_NCI_OBSERVATION | **0** |
| → HOMONYM_DISTINCT_CONFIRMED | **0** |

READY exige : nom exploitable non technique, coords, province + territoire, **bbox territoire** cohérente, absence de variante avancée même contexte, pas de fusion sur nom seul.

### 3. Homonymes (1 240)

| Classe | Effectif |
|---|---:|
| HOMONYM_ALREADY_IN_REFERENTIAL | **0** |
| HOMONYM_NEW_LOCALITY_READY | **857** |
| HOMONYM_REQUIRES_REVIEW | **383** |

Un homonyme dans un autre territoire peut être une vraie nouvelle localité — non rejeté parce que le nom existe ailleurs.

### 4–5. Plan d’intégration (non exécuté)

- Lot éligible strict : **READY_FOR_INTEGRATION = 3 182**
- Homonymes ready : **857** (lot séparé, validation humaine dédiée)
- `canonical_id` idempotent `RDC-NCI-LOC-…`
- Couverture = observation liée, pas identité
- **Aucune écriture** sur `locality_referential_official.json` / sources brutes / compteur 26 710

Service : `api/services/nire/locality_preintegration_validation.py`  
API : `POST/GET /api/nire/locality-preintegration/{run,status,summary}`  
Cache : `data/cache/nire_locality_preintegration_v1.json`

### 6. Simulation (non appliquée)

| Indicateur | Valeur |
|---|---:|
| CURRENT_LOCALITIES | 26 710 |
| READY_FOR_INTEGRATION | 3 182 |
| PROJECTED_LOCALITIES | **29 892** |
| Si + HOMONYM_NEW_LOCALITY_READY | 30 749 |
| Taux appariement actuel | **12,89 %** |
| Taux potentiel (READY only) | **~26,2 %** |
| Observations NCI rattachables | 3 948 |
| Covered rattachables (obs.) | 1 501 |
| Uncovered rattachables (obs.) | 3 948 |
| Réduction gap (obs.) | ~3 948 |
| Population potentiellement rattachable | ~9,18 M |
| Reste en revue (HC+homonymes) | ~9 185 |

### 7. Propagation future (documentée, inactive)

Master Registry → hiérarchie admin → Smart Map → NIRE → NSME/SDG → Intelligence territoriale → Centre de Décision → couverture/population — **idempotente**, après validation du lot READY uniquement.

### 8. Tests ajoutés

- villages proches distincts (distance ≠ fusion)
- homonymes inter-territoires distincts
- variante orthographique → non READY
- doublon NCI → non ajouté
- identité territoriale forte → READY
- insuffisant → REVIEW
- simulation sans création réelle

---

*Fin Data Activation P1 + Coherence + Enrichment + Pre-Integration Validation.*

---

## NCI LOCALITIES — CONTROLLED REFERENTIAL INTEGRATION

**Date :** 2026-07-19  
**Statut :** **Intégration réelle exécutée** (couche enrichment) — base KMZ **non modifiée** — **aucun commit**

### Référentiel avant

| Élément | Valeur |
|---|---|
| CURRENT_LOCALITIES | **26 710** |
| Fichier de base | `data/reports/locality_official/locality_referential_official.json` |
| SHA256 base | `af0fd9108975a7ec53275db26b38a94b792e996fbce11adb30a1cabbd06d7ebe` |
| Base modifiée | **Non** |

### Règles métier appliquées

1. Géométrie exploitable (WGS84, bornes RDC, ≠ (0,0), pas NaN) **et** absente des 26 710 → intégrable.  
2. « Déjà représentée » = même **contexte territorial** (province + territoire) + nom/variante normalisée — **jamais** distance seule, **jamais** nom seul inter-territoires.  
3. Homonymes territoriaux distincts → intégrés comme identités séparées.  
4. Covered + uncovered → **une** identité canonique ; couverture = observation.  
5. Idempotence : `canonical_id = RDC-NCI-LOC-…`.

### Résultats d’intégration (exécutés)

| Indicateur | Valeur |
|---|---:|
| UNIQUE_NCI_IDENTITIES_ANALYZED | **24 391** |
| ALREADY_IN_REFERENTIAL (base 26 710) | **3 971** |
| NEW_LOCALITY_WITH_VALID_GEOMETRY | **20 420** |
| INVALID_GEOMETRY | **0** |
| REQUIRES_IDENTITY_REVIEW | **0** |
| DUPLICATE_NCI_OBSERVATION | **5 206** |
| HOMONYM_NEW_LOCALITIES_ADDED | **1 435** |
| NEW_LOCALITIES_ADDED | **20 420** |
| NEW_TOTAL_LOCALITIES | **47 130** |
| INSERTED_FIRST_RUN | **20 420** |
| INSERTED_SECOND_RUN | **0** |

Couche d’ajouts : `locality_referential_nci_enrichment.json`  
Manifeste : `locality_referential_national_manifest.json`  
KPI qualité dynamique : `locality_count = 47 130`

### Après intégration — NIRE

| Indicateur | Avant | Après |
|---|---:|---:|
| Admin localités chargées | 26 710 | **47 130** |
| Taux MATCHED+PROBABLE | 12,89 % | **71,12 %** |
| MATCHED_LOCALITY | 3 727 | **21 050** |
| UNMATCHED_UNCOVERED | 16 636 | **390** |

### Couverture / population (identités rattachables)

| Indicateur | Valeur |
|---|---:|
| Identités covered rattachées | 4 971 |
| Identités uncovered rattachées | 24 391 |
| Dual-source | 4 971 |
| Population rattachable (somme obs. représentatives) | ~52 008 181 |

Totaux nationaux population NCI **non recalculés artificiellement**.

### Propagation

- API `/localites` + `/localites/count` → fusion base + enrichment  
- NIRE `_load_admin_localities` → référentiel national fusionné  
- Dashboard : `locality_count` dynamique, fusion enrichment dans le Master Registry JSON  
- Smart Map : charge base + enrichment (clustering/viewport inchangés)  
- NSME/SDG : calcul à la demande — pas de batch massif forcé  

### Idempotence

Confirmée : première exécution 20 420 inserts ; seconde exécution **0** insert.

---

## BILAN FINAL P1 — RÉFÉRENTIEL ENRICHI

| Couche | Effectif | Provenance |
|---|---:|---|
| Référentiel historique | **26 710** | `Localités.kmz` → `locality_referential_official.json` |
| Enrichissement FDSU/NCI | **20 420** | `locality_referential_nci_enrichment.json` |
| **Référentiel enrichi total** | **47 130** | Fusion dynamique (pas un seul KMZ) |

**Égalité :** 26 710 + 20 420 = **47 130**

### Fusion dynamique

- Chargeur unique : `locality_controlled_integration.load_national_locality_items()`
- API : `GET /localites`, `GET /localites/count`
- Dashboard : `locality_quality.locality_count` prioritaire + registre (`nombre=47130`, `historique_kmz=26710`, `enrichissement_nci_fdsu=20420`)
- NIRE / NSME / SDG consomment le référentiel fusionné sans duplication d’identité

### Covered / uncovered

Observations de couverture distinctes ; dual-source (4 971) = revue neutre, **pas** conflit automatique.

### Domaines P1

| Domaine | Statut |
|---|---|
| Éducation → NSME/SDG | Actif, non pondéré (poids 0) |
| CENI signal | Actif, ≠ Sites FDSU, non pondéré |
| Télécom/Fibre/MW → DXL | `telecom_context` + preuves |
| Population nationale | Agrégats NCI inchangés (pas de double comptage via enrichissement) |
| NIRE post-enrichissement | Taux appariement **71,12 %** |

---

## AUDIT GIT FINAL P1 (pré-commit)

**Branche :** `feature/smart-map-interactions`  
**HEAD référence :** `cd2d275`  
**Commit :** non exécuté — en attente validation périmètre  
**`git diff --check` :** aucun marqueur de conflit ; avertissements CRLF Windows uniquement (non bloquants)

### Classification artefacts

| Classe | Exemples | Décision |
|---|---|---|
| **A. Runtime nécessaire** | code API/dashboard, couche enrichment 20 420, manifeste, quality, registry national, `ceni_registry_v1.json` | **À committer** |
| **B. Caches reproductibles** | `data/cache/nire_locality_*.json` | **Exclure** |
| **C. Traçabilité utile légère** | `ceni_import_batches_v1.json` (433 o), `DATA_ACTIVATION_P1.md` | **À committer** |
| **D. Analytique / audit CENI reproductible** | `ceni_anomalies_v1.json` (~17 Mo), `ceni_kmz_audit_v1.json` | **Exclure** — dérivables du registry / KMZ |

### Verdict CENI (4 artefacts)

| Fichier | Runtime | API | NSME/SDG | Commit |
|---|---|---|---|---|
| `ceni_registry_v1.json` (~52 Mo) | **Oui** | sites/map/nearest/stats | **Oui** | **Inclure** |
| `ceni_anomalies_v1.json` (~17 Mo) | Non (qualité seule) | `/data-quality` (régénère si absent) | Non | **Exclure** |
| `ceni_import_batches_v1.json` (433 o) | Non critique | `/import-batches` | Non | **Inclure** (traçabilité) |
| `ceni_kmz_audit_v1.json` (3 Ko) | Non lu | — | Non | **Exclure** |

### Architecture compteur (mode DB)

- Table Postgres `localites` = miroir historique KMZ (**26 710**) — **pas** le total national enrichi.
- `GET /localites/count` / `GET /localites` / couche carte localités lisent la **fusion fichier** (base + NCI) même si `use_database()` est vrai.
- Dashboard : `locality_quality.locality_count` (= 47 130) + registre (`historique_kmz` / `enrichissement_nci_fdsu`).
- Redémarrage Uvicorn requis pour que le processus `:8001` serve le code courant.

### Idempotence & intégrité

| Contrôle | Résultat |
|---|---|
| Base SHA256 `locality_referential_official.json` | `af0fd910…d7ebe` inchangé |
| Enrichissement | **20 420** (dédupliqués si besoin après test audit) |
| Fusion | 26 710 + 20 420 = **47 130** |
| Re-persist couche NCI | `inserted=0`, `skipped_existing=20420` |
| Manifeste | `INSERTED_SECOND_RUN=0`, `idempotent=true` |

### Correctif audit (pré-commit)

`persist_enrichment` court-circuite désormais sur `canonical_id` déjà présent et réutilise `nom` / id existants — évite la régénération d’ids si on rejoue des fiches déjà intégrées.

---

*Fin Data Activation P1 — bilan définitif + audit Git pré-commit. Commit non exécuté.*
