# RGC Groupements & Localities — Controlled Integration

**Projet :** SIG-FDSU RDC
**Branche :** `feature/smart-map-interactions`
**HEAD de départ :** `93004b7a7e8123b25e2cd88959a0f4e848f68dcf`
**Engine :** `nire-groupement-rgc-controlled-integration-1.0.0`
**Date :** 2026-07-19
**Mode :** intégration contrôlée — **aucun commit / push** dans ce sprint

---

## 1. Doctrine

Référentiel évolutif multi-source :

> Si une source institutionnelle fiable apporte une entité absente, géolocalisée et suffisamment distincte → elle peut être ajoutée pour réduire le gap.
> Provenance conservée. Après intégration : **égalité analytique** (pas de priorité historique vs RGC).

Architecture :

```
GROUPMENT_HISTORICAL_REFERENTIAL (1 681, intact)
+ GROUPMENT_RGC_ENRICHMENT (961)
= UNIFIED_GROUPMENT_REFERENTIAL (dynamique)
```

---

## 2. Source

| Champ | Valeur |
|---|---|
| Producteur original | RGC RDC |
| Miroir acquisition | HDX / OCHA |
| Fichier brut | `data/raw/rgc/Localite.zip` |
| SHA-256 | `77448bf0ff28652c2914468e22d664d8f37e2b0540537e651a2359a4ae31c650` |
| Millésime | **2010-09-22** |
| Shapefile Groupements catalogue | non obtenu → inventaire dérivé attributs Localite |
| Brut modifié | **Non** |

---

## 3. Groupements — résultats d’intégration

| KPI | Valeur |
|---|---:|
| OLD_GROUPMENTS | **1 681** |
| RGC_GROUPMENTS_ANALYZED | **2 222** |
| ALREADY_IN_REFERENTIAL | **1 098** |
| EXISTING_VARIANTS | **25** |
| NEW_GROUPMENTS_INSERTED | **961** |
| HOMONYM_DISTINCT_INSERTED | **65** (inclus dans les 961) |
| AMBIGUOUS_NOT_INSERTED | **138** |
| NEW_TOTAL_GROUPMENTS | **2 642** |
| historical_count | **1 681** |
| enrichment_count | **961** |
| total_count | **2 642** |

Géométrie RGC :

- `geometry_role = REPRESENTATIVE_POINT`
- `geometry_provenance = RGC`
- `geometry_source_date = 2010-09-22`
- **jamais** présentée comme frontière administrative

Enrichissement des existants (crosswalk) :

- mappings identité FDSU ↔ code RGC ↔ PCode : **1 001** nouveaux enregistrements crosswalk
- géométries alternatives conservées sans écrasement

Identifiants :

- historiques inchangés
- nouveaux : `RDC-RGC-GRPT-{parent}-{name}-{code}-{hash8}`

---

## 4. Rattachements Groupement → Localité

### 4.1 Clarification des 6 999 enregistrements overlay

Les **6 999** ne sont **pas** 6 999 nouveaux rattachements.

Ce sont des **enregistrements de preuve** (`link evidence records`) dans l’overlay
`locality_groupement_links_rgc.json`, ventilés ainsi :

| KPI clarifié | Valeur | Signification |
|---|---:|---|
| **NEW_UNIQUE_GROUPMENT_LINKS** | **3 635** | Localités **sans** groupement avant → rattachement admin RGC ajouté |
| **EXISTING_LINKS_CONFIRMED_BY_RGC** | **3 364** | Localités **déjà** rattachées ; RGC confirme le **même** groupement (preuve croisée, pas un 2ᵉ parent) |
| **TOTAL_LINK_EVIDENCE_RECORDS** | **6 999** | 3 635 + 3 364 — somme des preuves overlay |

Contrôle arithmétique de couverture :

```
LOCALITIES_WITH_GROUPMENT_AFTER − BEFORE
= 7 410 − 3 775
= 3 635
= NEW_UNIQUE_GROUPMENT_LINKS
```

Donc **aucun des 3 364 confirmés n’est compté une deuxième fois** comme nouveau lien :
- `NEW_BUT_HAD_EXISTING = 0`
- `CONFIRMED_BUT_EMPTY = 0`
- delta de couverture = uniquement les NEW_UNIQUE

### 4.2 Compteurs de rattachement

| KPI | Valeur |
|---|---:|
| LOCALITIES_WITH_GROUPMENT_BEFORE | **3 775** |
| NEW_UNIQUE_GROUPMENT_LINKS | **3 635** |
| EXISTING_LINKS_CONFIRMED_BY_RGC | **3 364** |
| TOTAL_LINK_EVIDENCE_RECORDS | **6 999** |
| AMBIGUOUS_GROUPMENT_LINKS_NOT_INSERTED | **313** (enregistrements revue) |
| LOCALITIES_WITH_GROUPMENT_AFTER | **7 410** |
| LOCALITIES_WITHOUT_GROUPMENT_AFTER | **39 720** |
| COVERAGE_RATE_BEFORE | **8,01 %** |
| COVERAGE_RATE_AFTER | **15,72 %** |
| ACTIVE_PARENT_CONFLICTS | **0** |

### 4.3 Cohérence parents / ambiguïtés (contrôle final)

| Contrôle | Résultat |
|---|---|
| Aucune localité avec deux parents groupement actifs contradictoires | **OK** (`OVERWRITES_OF_EXISTING_PARENT = 0`, `ACTIVE_PARENT_CONFLICTS = 0`) |
| Overlay n’écrase jamais un groupement historique existant | **OK** (remplit seulement si vide) |
| 313 liens ambigus hors rattachement automatique conflictuel | **OK** — file revue ; 298 conflits + 15 multi-hits |
| Cas limite documenté | 1 localité (`Makutano` / Shabunda) a une preuve `CROSS_SOURCE_CONFIRMED` (Bagabo = existant) **et** 2 lignes RGC contradictoires en file ambiguë — le parent actif reste Bagabo, pas de double parent |
| 138 groupements ambigus hors référentiel actif | **OK** — enrichment = 961 NEW uniquement ; total unifié 2 642 |
| 3 814 localités RGC candidates non intégrées | **OK** — audit seul ; NCI enrichment inchangé (20 420) ; total localités 47 130 |

Règles :

- attribut RGC explicite uniquement (pas de proximité spatiale)
- conflits existants → revue NIRE (`locality_groupement_links_rgc_ambiguous.json`)
- aucune nouvelle localité créée pour porter un lien

Fichier overlay : `data/reports/locality_official/locality_groupement_links_rgc.json`
Appliqué dynamiquement dans `load_national_locality_items`.

---

## 5. Idempotence

| Run | Groupements | Liens |
|---|---:|---:|
| FIRST | **961** | **6 999** |
| SECOND | **0** | **0** |

Re-contrôle final : `LINKS_WOULD_INSERT_ON_RERUN = 0`, `LINKS_SECOND_RUN_INSERTED = 0`.

---

## 6. Localités RGC candidates (audit seul — non intégrées)

| KPI | Valeur |
|---|---:|
| RGC_LOCALITY_CANDIDATES_ANALYZED | 30 272 (Localite_p) |
| ALREADY_IN_47130 | 26 370 |
| EXISTING_VARIANTS | 4 |
| NEW_WITH_VALID_GEOMETRY | **3 814** |
| AMBIGUOUS | 1 |
| HOMONYM_DISTINCT | 745 |
| DUPLICATES | 83 |

**Recommandation :** intégration future candidate-par-candidate après revue NIRE. Millésime 2010 — pas d’intégration de masse sans validation d’identité.

Rapport : `data/reports/locality_official/locality_rgc_candidates_audit_v1.json`

---

## 7. SIG — branchements

| Surface | Comportement |
|---|---|
| API `/groupements`, `/geo/groupements` | fusion dynamique |
| API `/groupements/count` | `historical_count` / `enrichment_count` / `total_count` |
| `/dashboard/summary` | total fusionné dynamique |
| Dashboard registry | KMZ + RGC |
| Cartographie | points RGC (symbole distinct) ; popup = point représentatif + millésime |
| Recherche | parcourt l’univers unifié (jusqu’à 100 000) |
| Spatial Matching / NSME / SDG | consomment le référentiel unifié ; proximité ≠ appartenance admin |

---

## 8. Fichiers

**Créés**

- `api/services/nire/groupement_controlled_integration.py`
- `data/reports/groupement_official/groupement_referential_rgc_enrichment.json`
- `data/reports/groupement_official/groupement_rgc_crosswalk.json`
- `data/reports/groupement_official/groupement_referential_national_manifest.json`
- `data/reports/locality_official/locality_groupement_links_rgc.json`
- `data/reports/locality_official/locality_groupement_links_rgc_ambiguous.json`
- `data/reports/locality_official/locality_rgc_candidates_audit_v1.json`
- `tests/test_groupement_rgc_controlled_integration.py`
- `PROJECT_MANAGEMENT/ARCHITECTURE/RGC_GROUPMENTS_LOCALITIES_INTEGRATION.md`

**Modifiés**

- `api/main.py`
- `api/routes/nire.py`
- `api/services/national_dashboard_service.py`
- `api/services/nire/locality_controlled_integration.py`
- `api/services/nire/rgc_groupements_localities_audit.py`
- `dashboard/app.js`
- `data/reports/national_counter_registry.json` (compteurs groupements uniquement)

**Non modifiés**

- `groupement_referential_official.json` (base)
- `data/raw/rgc/*` (bruts)
- compteurs Zones / Provinces / Territoires / Collectivités

---

## 9. Décision

Intégration réelle **effectuée** pour :

1. 961 nouveaux groupements RGC géolocalisés
2. liens admin confirmés / nouveaux (overlay)

**En attente validation** avant :

- commit / push
- intégration des 3 814 localités candidates
- matérialisation DB PostGIS des nouveaux groupements
