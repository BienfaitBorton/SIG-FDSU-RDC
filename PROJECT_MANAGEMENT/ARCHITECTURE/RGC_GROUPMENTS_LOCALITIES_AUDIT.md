# RGC Groupements & Localities Referential Enrichment Audit

**Projet :** SIG-FDSU RDC
**Branche :** `feature/smart-map-interactions`
**HEAD validé :** `93004b7a7e8123b25e2cd88959a0f4e848f68dcf`
**Engine :** `nire-rgc-groupements-localities-audit-1.0.0`
**Date audit :** 2026-07-19
**Mode :** lecture seule — **aucune intégration réelle**

---

## 0. Contexte

Suite à l’audit NCI + CENI (gap Groupements inchangé : 1 681 / cible indicative 6 053) :

| KPI NCI+CENI | Valeur |
|---|---:|
| CURRENT_GROUPMENTS | 1 681 |
| GROUPMENTS_FOUND_IN_NCI | 0 |
| GROUPMENTS_FOUND_IN_CENI (structurés) | 0 |
| LOCALITIES (référentiel unifié) | 47 130 |
| LOCALITIES_WITH_EXPLICIT_GROUPMENT | 3 775 |

Source complémentaire structurée retenue : **Référentiel Géographique Commun (RGC RDC)**.

Périmètre strict de ce sprint : **Groupements**, **Localités/Villages**, **rattachement Groupement → Localité**.
Aucun compteur Zones / Provinces / Territoires / Collectivités / Secteurs / Chefferies modifié.

---

## 1. Acquisition

### 1.1 Producteur original

- **Producteur :** Référentiel Géographique Commun (RGC RDC)
- **Catalogue :** `https://rgc.cd/...` (catégorie jeux administratifs)
- **Millésime annoncé catalogue :** **2010-09-22**
- **Statut site RGC (2026-07-19) :** inaccessible (erreur fatale PHP)

### 1.2 Localités — obtenues via miroir institutionnel

| Champ | Valeur |
|---|---|
| Obtained | **Oui** |
| Producteur original | RGC |
| Miroir de téléchargement | HDX / OCHA DRC |
| Dataset miroir | [dr-congo-settlements](https://data.humdata.org/dataset/dr-congo-settlements) |
| Fichier local | `data/raw/rgc/Localite.zip` |
| SHA-256 | `77448bf0ff28652c2914468e22d664d8f37e2b0540537e651a2359a4ae31c650` |
| Taille | 3 323 162 octets |
| Couches | `Localite.shp`, `Localite_p.shp` |
| Projection brute | World Mercator (mètres) → conversion WGS84 pour analyse |
| Encoding | cp1252 |
| Immutabilité | source brute **non modifiée en place** |

> HDX/OCHA = miroir institutionnel. **Ne pas présenter HDX comme producteur original.**

### 1.3 Groupements shapefile — non obtenu

| Champ | Valeur |
|---|---|
| Obtained | **Non** |
| Catalogue | ~92 Ko, 2010-09-22 |
| Cause | Site RGC cassé ; `Groupements.zip` absent de HDX / Wayback CDX |
| Fallback audit | Inventaire dérivé des attributs Localite : `GROUPEMENT`, `CODE_GRPT`, `TERRITOIRE`, `COLLECTIV` |
| geometry_role | **REPRESENTATIVE_POINT** (jamais frontière administrative) |

Manifeste : `data/reports/rgc_official/rgc_acquisition_manifest.json`
Cache audit : `data/cache/nire_rgc_groupements_localities_audit_v1.json` (hors commit).

---

## 2. Audit Localités RGC

### 2.1 Couche `Localite.shp` (base)

| KPI | Valeur |
|---|---:|
| RGC_LOCALITIES_RAW_COUNT | **26 710** |
| RGC_LOCALITIES_VALID_GEOMETRY | **26 710** |
| RGC_LOCALITIES_INVALID_GEOMETRY | 0 |
| RGC_LOCALITIES_MISSING_NAME | 0 |
| RGC_LOCALITIES_WITH_PCODE | 26 710 |
| RGC_LOCALITIES_WITH_GROUPMENT_NAME | 7 342 |
| RGC_LOCALITIES_WITH_GROUPMENT_CODE | 4 291 |
| RGC_LOCALITIES_WITH_TERRITORY | 26 679 |
| RGC_LOCALITIES_WITH_SECTOR_CHEFFERIE | 25 646 |
| RGC_LOCALITIES_UNIQUE_IDENTITY_ESTIMATE | 26 710 |

**Constats critiques :**

1. `Localite.shp` (26 710) = **même jeu** que `locality_referential_official` historique FDSU (intersection PCODE **26 680 / 26 680**).
2. Donc la couche de base RGC Localités **n’apporte pas** de nouvelles localités au référentiel historique — elle **est** ce référentiel.
3. Valeur principale = attributs de rattachement (`GROUPEMENT`, `CODE_GRPT`) et métadonnées.

### 2.2 Couche `Localite_p.shp` (élargie)

| KPI | Valeur |
|---|---:|
| RGC_LOCALITIES_RAW_COUNT | **30 272** |
| RGC_LOCALITIES_VALID_GEOMETRY | **30 271** |
| RGC_LOCALITIES_INVALID_GEOMETRY | 1 |
| RGC_LOCALITIES_MISSING_NAME | 12 |
| RGC_LOCALITIES_WITH_PCODE | 26 061 |
| RGC_LOCALITIES_WITH_GROUPMENT_NAME | 7 871 |
| RGC_LOCALITIES_WITH_GROUPMENT_CODE | 3 919 |
| RGC_LOCALITIES_UNIQUE_IDENTITY_ESTIMATE | 30 092 |

### 2.3 Catégories TYPE

`TYPE` est un **code numérique** RGC (0, 7, 8, 9, …).
**Aucune sémantique ville/village inventée.** Conserver `source_entity_type=RGC_TYPE_CODE`.

| TYPE (Localite) | Count |
|---|---:|
| 0 | 23 643 |
| 7 | 1 541 |
| 9 | 641 |
| 8 | 533 |
| autres | … |

geometry_role localités = `SETTLEMENT_POINT` ; provenance = `RGC`.

---

## 3. Audit Groupements (dérivés)

Inventaire construit depuis Localite_p (attributs groupement) — **pas** le shapefile catalogue Groupements.

| KPI | Valeur |
|---|---:|
| RGC_GROUPMENTS_RAW_COUNT | **2 222** |
| RGC_GROUPMENTS_VALID_GEOMETRY | **2 222** |
| RGC_GROUPMENTS_INVALID_GEOMETRY | 0 |
| RGC_GROUPMENTS_MISSING_NAME | 4 |
| RGC_GROUPMENTS_MISSING_TERRITORY | 3 |
| RGC_GROUPMENTS_MISSING_SECTOR_CHEFFERIE | 120 |
| RGC_GROUPMENTS_WITH_PCODE | 2 119 |
| RGC_GROUPMENTS_WITH_GROUPMENT_CODE | 993 |
| RGC_GROUPMENTS_UNIQUE_IDENTITY_ESTIMATE | **2 222** |
| geometry_role | **REPRESENTATIVE_POINT** |
| geometry_provenance | RGC_DERIVED_FROM_LOCALITIES |

Point représentatif = moyenne des localités du bucket (proxy chef-lieu).
**Ne jamais présenter comme limite administrative officielle.**

---

## 4. Rapprochement Groupements (NIRE)

Comparaison : inventaire RGC dérivé (2 222) ↔ référentiel FDSU (1 681).

Identité : nom normalisé + territoire + secteur/chefferie + code groupement (+ PCode échantillon).
**Proximité spatiale seule non utilisée pour l’identité.**

| Classification | Count |
|---|---:|
| CURRENT_GROUPMENTS | **1 681** |
| ALREADY_IN_GROUPMENT_REFERENTIAL | **1 098** |
| EXISTING_GROUPMENT_VARIANT | **25** |
| EXISTING_GROUPMENT_GEOMETRY_ENRICHMENT | **1 123** (alternatives de provenance, non écrasement) |
| NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY | **961** |
| DUPLICATE_RGC_GROUPMENT | 0 |
| AMBIGUOUS_RGC_GROUPMENT | **138** |
| HOMONYM_DISTINCT_RGC_GROUPMENT | **65** (homonymes autre territoire ; candidats NEW inclus) |
| POTENTIAL_ENRICHED_GROUPMENT_TOTAL | **2 642** (= 1 681 + 961) |

### Gap (cible indicative uniquement — non officielle)

| Indicateur | Valeur |
|---|---:|
| Cible indicative | 6 053 |
| Gap avant | **4 372** |
| Gap après simulation | **3 411** |
| Réduction du gap | **961** |

**Aucune intégration réelle** — simulation uniquement.

### Codes / correspondance

Table logique (échantillons en cache) :

```
fdsu_groupment_id  ↔  rgc_groupment_code  ↔  rgc_pcode_sample
```

Les `canonical_id` FDSU **ne sont jamais remplacés**.

---

## 5. Rapprochement Localités (NIRE)

Comparaison : Localite_p (30 272) ↔ référentiel unifié **47 130** (historique 26 710 + NCI 20 420, égalité analytique).

| Classification | Count |
|---|---:|
| CURRENT_LOCALITIES | **47 130** |
| ALREADY_IN_LOCALITY_REFERENTIAL | **26 370** |
| EXISTING_LOCALITY_VARIANT | **4** |
| NEW_RGC_LOCALITY_WITH_VALID_GEOMETRY | **3 814** |
| NEW_RGC_VILLAGE_WITH_VALID_GEOMETRY | **0** (pas de libellé « village » lexical fiable) |
| AMBIGUOUS_RGC_LOCALITY | **1** |
| DUPLICATE_RGC_LOCALITY (PCODE répété) | (dédoublonnage interne) |
| HOMONYM_DISTINCT_RGC_LOCALITY | (homonymes autre territoire parmi NEW) |
| POTENTIAL_ENRICHED_LOCALITY_TOTAL | **50 944** (= 47 130 + 3 814) |

**Lecture Data First :**

- La base `Localite.shp` est déjà dans le référentiel historique → pas de gain d’identité.
- Les **3 814** candidats NEW viennent surtout de `Localite_p` (millésime ~2010) : **revue manuelle obligatoire** avant toute intégration (risque de doublons NCI / obsolescence).
- Après intégration future validée : égalité analytique RGC = historique = NCI ; provenance = métadonnée d’audit.

---

## 6. Rattachement Groupement → Localité (simulation)

Situation actuelle :

| KPI | Valeur |
|---|---:|
| TOTAL_LOCALITIES | 47 130 |
| LOCALITIES_WITH_EXPLICIT_GROUPMENT | **3 775** |
| LOCALITIES_WITHOUT_EXPLOITABLE_GROUPMENT | **43 355** |
| Taux couverture avant | **8,01 %** |

Simulation (attributs RGC `GROUPEMENT` / `CODE_GRPT` uniquement — **pas** de proximité spatiale) :

| KPI | Valeur |
|---|---:|
| RGC_LOCALITIES_MATCHED_TO_CURRENT_REFERENTIAL | (voir cache `links`) |
| NEW_GROUPMENT_LINKS_FROM_RGC | **3 635** |
| CROSS_SOURCE_CONFIRMED_GROUPMENT_LINKS | **3 363** |
| AMBIGUOUS_GROUPMENT_LINKS | **284** |
| LOCALITIES_WITHOUT_GROUPMENT_AFTER_SIMULATION | **39 720** |
| Taux couverture après simulation | **15,72 %** |

Un lien administratif explicite RGC peut servir de **preuve de rattachement**.
La proximité spatiale seule **ne crée jamais** le rattachement administratif.

---

## 7. Exemple Site FDSU (site 29)

| Relation | Résultat |
|---|---|
| Coordonnées site | −4,963924 / 14,589993 |
| NEAREST_GROUPMENT_CURRENT | **Kimbanza** (`RDC-OT-GRPT-KIMBANZA-…`) — ~30 295 m |
| NEAREST_GROUPMENT_RGC_CANDIDATE | **Kimbanza** (code RGC `20430301`, REPRESENTATIVE_POINT) — ~33 021 m |
| Distinction | `SPATIAL_PROXIMITY` ≠ `ADMINISTRATIVE_MEMBERSHIP` |

---

## 8. Impact NSME (simulation documentaire)

Relations futures (à la demande / cache / batch contrôlé / PostGIS) :

- `NEAREST_GROUPMENT` / `DISTANCE_TO_GROUPMENT_M` / `GROUPMENT_ADMIN_CONTEXT`
- `NEAREST_LOCALITY` / `DISTANCE_TO_LOCALITY_M` / `LOCALITY_GROUPMENT_CONTEXT`

**Pas de matérialisation massive** dans cet audit.

Pour nouveaux groupements RGC (si intégration future) :

- `geometry_role = REPRESENTATIVE_POINT`
- `geometry_provenance = RGC`
- ne pas convertir en frontière administrative
- pour groupements existants : géométrie RGC = **alternative**, jamais écrasement automatique

---

## 9. Impact SDG

Chaîne documentée :

```
Site FDSU → Groupement → Localité/Village → CENI → Santé → Éducation → Télécom → Population/Couverture
```

Après intégration future validée, les entités RGC participent à égalité à : Cartographie, Recherche, Spatial Matching, NSME, SDG, Intelligence Territoriale, Centre de Décision, DXL.
La provenance RGC reste métadonnée d’audit.

---

## 10. Limites (millésime 2010)

1. Jeux RGC ~**22 septembre 2010** — source **complémentaire**, jamais vérité prioritaire.
2. Ne jamais écraser : 1 681 groupements FDSU, 47 130 localités unifiées, NCI/CENI plus récents.
3. Shapefile Groupements catalogue **indisponible** → inventaire dérivé (qualité moindre qu’un jeu officiel points/chefs-lieux).
4. Candidats NEW Localite_p (3 814) et NEW Groupements (961) = **simulation** ; revue NIRE + validation métier avant intégration.
5. Codes TYPE sans dictionnaire officiel dans le shapefile.

---

## 11. Livraison KPI (A–F)

### A. Source

1. Localités RGC : **obtenues** (miroir HDX) ; Groupements shapefile : **non**
2. Méthode : téléchargement HDX après échec rgc.cd
3. Miroir : HDX/OCHA — producteur original = RGC
4. Hash Localite.zip : `77448bf0…1c650`
5. Millésime catalogue : **2010-09-22**

### B. Groupements

6–17. Voir §4 (CURRENT=1681, NEW_VALID=961, POTENTIAL=2642, …)

### C. Localités

18–26. Voir §5 (CURRENT=47130, NEW=3814, POTENTIAL=50944, …)

### D. Rattachements

27–31. Voir §6 (BEFORE=3775, NEW_LINKS=3635, AFTER_WITHOUT=39720)

### E. Gap

32. Gap groupements avant : **4 372**
33. Gap après simulation : **3 411**
34. Réduction : **961**
35. Couverture Groupement→Localité : **8,01 % → 15,72 %** (simulation)

### F. Technique

36. Exemple site 29 : §7
37. NSME : §8
38. SDG : §9
39. Tests : `tests/test_rgc_groupements_localities_audit.py`
40. Fichiers principaux :
   - `api/services/nire/rgc_groupements_localities_audit.py`
   - `PROJECT_MANAGEMENT/ARCHITECTURE/RGC_GROUPMENTS_LOCALITIES_AUDIT.md`
   - `data/reports/rgc_official/rgc_acquisition_manifest.json`
   - `data/raw/rgc/*` (hors commit)
   - `data/cache/nire_rgc_groupements_localities_audit_v1.json` (hors commit)
41. `git status --short` : artefacts RGC + audit NCI/CENI précédent + hors-périmètre (telecom, PLATFORM, case_history, raw…) — **aucun commit** dans ce sprint.

---

## 12. Décision recommandée (attente validation)

| Action | Statut |
|---|---|
| Intégration réelle groupements RGC | **ATTENDRE validation** |
| Intégration réelle localités Localite_p | **ATTENDRE validation** (revue 3 814) |
| Application liens groupement simulés | **ATTENDRE validation** |
| Commit / push | **NON** (consigne sprint) |

**Principe Data First :** exploiter les attributs RGC déjà présents (liens groupement, codes) sans inventer d’objets ; indiquer explicitement le manque du shapefile Groupements officiel et l’ancienneté 2010.
