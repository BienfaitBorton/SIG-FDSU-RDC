# NIRE Phase 5 — Real MNO Audit, Operator Partitioning & Controlled Identity Resolution

**Branche :** `feature/smart-map-interactions`
**Base :** commit Phase 4 `d5b0f03e1eec715d7aa3b137fdec2904d79c9a20`
**Moteur :** `nire-mno-audit-5.0.0` · **Règles :** `nire-mno-rules-5.0.0`
**Contraintes :** lecture seule sur `telecom.infrastructure` · source MNO immuable · **aucun commit** · **aucun push**

---

## 1. Architecture mise en place

```
data/raw/Operators existing and planned sites_20260713.xlsx  (immuable)
        │
        ▼
api/services/nire/mno_audit.py
  • fingerprint SHA-256 + métadonnées
  • ingestion + quarantaine géométrie
  • partitions logiques MNO_VODACOM / AIRTEL / ORANGE / AFRICELL
  • normalisation statut + RAT
  • grille spatiale vs telecom.infrastructure (PostGIS lecture)
  • classifications NIRE + COLLOCATION_GROUP
  • agrégats KPI d’audit (sans toucher le KPI national)
        │
        ▼
api/routes/nire.py
  GET  /api/nire/mno-audit/status
  POST /api/nire/mno-audit/run
  GET  /api/nire/mno-audit/rows          (pagination + filtres)
  GET  /api/nire/mno-audit/colocations
  GET  /api/nire/mno-audit/layers/{op}   (GeoJSON plafonné)
  GET  /api/nire/mno-audit/source
        │
        ├── Review Queue Phase 4 (option enqueue_reviews)
        └── dashboard/modules/nire-workspace (onglet Audit MNO)
```

**KPI national 14 580** = `SELECT COUNT(*) FROM telecom.infrastructure`
(`api/services/national_dashboard_service.py`). **Jamais modifié** par Phase 5.

---

## 2. Fichier source et empreinte

| Propriété | Valeur |
|-----------|--------|
| Fichier | `data/raw/Operators existing and planned sites_20260713.xlsx` |
| Taille | 645 658 octets |
| SHA-256 | `79560e2217679d9244ee679810863b723e6ca07003e58f0a56ab6708b77ac242` |
| Colonnes | `Site Name`, `Latitude`, `Longitude`, `RAT`, `Status`, `Operator name` |
| Hors commit | **Oui** (sauf instruction ultérieure) |

Le fichier n’est **jamais** réécrit (pas de `Workbook.save` côté produit).

---

## 3. Statistiques exactes du fichier

| Indicateur | Valeur |
|------------|-------:|
| Lignes analysées | **12 615** |
| Coordonnées valides | **12 611** |
| Coordonnées invalides / quarantaine | **4** |
| (0,0) | **0** dans ce fichier (règle NIRE toujours active) |

### Quarantaine identifiée

| Site | Latitude | Longitude |
|------|----------|-----------|
| Beni-Butsili-Relief_NKV | `#REF!` | `#REF!` |
| Butembo-Vuhira_NKV | 2.307038 | `#REF!` |
| Butembo-Kingdom_NKV | 1.353397 | `#REF!` |
| Butembo-Regideso_NKV | 1.540915 | `#REF!` |

---

## 4. Statistiques exactes par opérateur

| Opérateur | Partition | Lignes |
|-----------|-----------|-------:|
| Vodacom | `MNO_VODACOM` | **4 133** |
| Airtel | `MNO_AIRTEL` | **4 477** |
| Orange | `MNO_ORANGE` | **3 221** |
| Africell | `MNO_AFRICELL` | **784** |
| **Total** | | **12 615** |

---

## 5. Statistiques exactes par statut (normalisé)

| Statut normalisé | Lignes | Originaux observés |
|------------------|-------:|--------------------|
| ONLINE | 7 432 | Online |
| IN_SERVICE | 3 716 | In Service / in Service / IN Service |
| PLANNED | 1 463 | Planned |
| TX_ONLY | 2 | Only Tx / Only TX |
| OUT_OF_SERVICE | 2 | Out Service |

Valeurs originales **conservées** (`status_original`).

---

## 6. Qualité coordonnées

| Métrique | Valeur |
|----------|-------:|
| Valides | 12 611 |
| Invalides | 4 |
| Soft hors enveloppe RDC | signalées (`outside_rdc_soft_bounds`) sans suppression |

---

## 7. Résultats de normalisation RAT

Variantes supportées : `2G/3G/4G`, `2G-3G-4G`, `2G3G4G`, `2G+3G+4G`, `2G_3G_FDD`, `2G_3G_TDD-FDD`, `2G-RCS`, etc.

Champs produits : `has_2g`, `has_3g`, `has_4g`, `has_5g`, `has_fdd`, `has_tdd`, `has_rcs`, `rat_normalized` + `rat_original`.

Top observés (échantillon fichier) : `2G/3G/4G`, `2G-3G-4G`, `2G_3G_FDD`, `2G_3G_TDD-FDD`, `2G-RCS`, …

---

## 8–17. Rapprochement avec les 14 580 infrastructures

**Référentiel cible (lecture seule) :** `telecom.infrastructure` (+ join `telecom.operators`).
**Indexés pour matching spatial :** 14 576 points avec lat/lon non nuls (sur 14 580 totaux).
**Méthode :** grille spatiale (pas de boucle O(n²)), seuils configurables 1 m / 50 m / 250 m + similarité de nom + accord opérateur.

---

## Audit de cohérence statistique (Phase 5 — final)

### A. Classification principale exclusive (somme = 12 615)

Chaque ligne MNO a **exactement une** classification primaire finale.
Ces compteurs sont les seuls à additionner pour retrouver la population.

| Classification primaire | Lignes |
|-------------------------|-------:|
| MATCH_EXISTING_INFRASTRUCTURE | **7 500** |
| CONFLICT | **1 336** |
| PLANNED_SITE | **1 032** |
| NEW_INFRASTRUCTURE_CANDIDATE | **943** |
| OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE | **936** |
| AMBIGUOUS | **812** |
| COLOCATED_MULTI_OPERATOR | **28** |
| POSSIBLE_DUPLICATE | **24** |
| INVALID_GEOMETRY | **4** |
| UNRESOLVED | **0** |
| **Somme de contrôle** | **12 615** |

> **Attention :** le rapport ne doit **pas** présenter « Sites Planned = 1 463 » dans ce tableau exclusif.
> Le statut `PLANNED` (1 463) est un **indicateur transversal** : 1 032 lignes ont la classe primaire `PLANNED_SITE`, les 431 autres Planned ont une autre classe primaire (MATCH, CONFLICT, etc.).

### B. Indicateurs transversaux non exclusifs

Une même ligne **peut** être comptée dans plusieurs indicateurs ci-dessous.
**Ne pas additionner** ces valeurs avec (ou à la place de) la classification exclusive.

| Indicateur transversal | Valeur | Nature |
|------------------------|-------:|--------|
| Planned (`status_normalized=PLANNED`) | **1 463** | Statut (chevauche toute classe primaire) |
| Flag / classe COLOCATED_MULTI_OPERATOR (lignes) | **1 506** | Flag secondaire + 28 primaires |
| Flag secondaire `MATCH_WITH_COLLOCATION` | **892** | Flag |
| Flag secondaire `PLANNED_SITE` | **1 459** | Flag (quasi-statut Planned) |
| POSSIBLE_DUPLICATE (primaire) | **24** | Aussi classe exclusive |
| AMBIGUOUS (primaire) | **812** | Aussi classe exclusive |
| CONFLICT (primaire) | **1 336** | Aussi classe exclusive |
| INVALID_GEOMETRY (primaire) | **4** | Aussi classe exclusive |
| `requires_human_review` (lignes uniques) | **3 881** | Revue |

Répartition Planned (1 463) par classe primaire :

| Classe primaire des lignes Planned | Lignes |
|------------------------------------|-------:|
| PLANNED_SITE | 1 032 |
| MATCH_EXISTING_INFRASTRUCTURE | 236 |
| AMBIGUOUS | 117 |
| OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE | 50 |
| CONFLICT | 20 |
| POSSIBLE_DUPLICATE | 4 |
| INVALID_GEOMETRY | 4 |

### C. Co-localisations — 721 vs 736 (deux métriques distinctes)

| Métrique | Groupes (≥2 lignes) | dont multi-opérateurs | Règle |
|----------|--------------------:|----------------------:|-------|
| **Exact-coordinate groups** (égalité float Python) | **714** | **705** | `(lat, lon)` bit-identiques |
| **Spatial colocation groups Phase 5** (arrondi 6 décimales) | **745** | **736** | `f"{lat:.6f}|{lon:.6f}"` |

**Règle réellement implémentée en Phase 5 :** égalité après **arrondi à 6 décimales** (~0,11 m).
- **Pas** de rayon PostGIS pour les groupes MNO↔MNO.
- **Pas** de tolérance spatiale au-delà de cet arrondi.
- Les seuils 1 / 50 / 250 m servent uniquement au **rapprochement MNO → telecom.infrastructure**.

**Pourquoi ≠ ~721 / ~712 de l’audit exploratoire :**
l’exploratoire se rapproche de l’égalité float stricte (714 / 705). L’écart résiduel (~7–10 groupes) vient de différences de méthodologie exploratoire (arrondi alternatif, filtre statut, agrégation pandas). Phase 5 **n’utilise pas** 721 : il publie **745 / 736** via arrondi 6 décimales, qui crée des groupes supplémentaires en fusionnant des couples non bit-identiques mais indistinguables à 6 décimales.

### D. Revue humaine — dossiers uniques (aperçu)

| Métrique | Valeur |
|----------|-------:|
| **Lignes uniques `requires_human_review=true`** | **3 881** (30,76 % de 12 615) |

Analyse détaillée : section **Human Review Analysis — 3,881 Unique Cases** ci-dessous.

### E. KPI 14 580 + 943 = 15 523 (théorique uniquement)

| Contrôle | Résultat |
|----------|----------|
| NEW_INFRASTRUCTURE_CANDIDATE exclusives | **943** |
| Dont aussi classées MATCH existant | **0** (aucune ; `match` vide) |
| Formule | 14 580 + 943 = **15 523** |
| Nature | Scénario maximal théorique **avant validation** |
| KPI officiel | **reste 14 580** (aucune écriture telecom) |

### F. Dashboard Audit MNO

L’UI distingue visuellement : (1) population 12 615, (2) classification exclusive, (3) indicateurs non exclusifs, (4) co-localisations en **groupes**, (5) opérateurs, (6) statuts.
Aucun panneau ne présente Planned / coloc / ambiguïtés comme une partition additive de 12 615.

### Ventilation opérateur (extrait)

| Opérateur | Match | Présence | Nouveaux | Planned (statut) | Ambigus | Conflits | Doublons | Géom. invalide |
|-----------|------:|---------:|---------:|-----------------:|--------:|---------:|---------:|---------------:|
| Vodacom | 3 545 | 206 | 0 | 413 | 8 | 167 | 24 | 4 |
| Airtel | 1 139 | 496 | 770 | 1 050 | 619 | 583 | 0 | 0 |
| Orange | 2 816 | 86 | 140 | 0 | 87 | 84 | 0 | 0 |
| Africell | 0 | 148 | 33 | 0 | 98 | 502 | 0 | 0 |

---

## Human Review Analysis — 3,881 Unique Cases

**Périmètre :** lignes avec `requires_human_review=true` après `run_mno_audit` (lecture seule).
**Somme de contrôle :** 3 881 lignes uniques. Aucun enqueue massif pendant cet audit.
**Sources :** inchangées (Excel MNO + `telecom.infrastructure`).

### Pourquoi exactement 3 881 ?

Le moteur n’accepte automatiquement que les `MATCH_EXISTING_INFRASTRUCTURE` **non Planned** (score 85/92, confiance 0,8/0,9, `requires_human_review=false`) et les `PLANNED_SITE` primaires sans voisin infra (`requires_human_review=false`).
Tout le reste déclenche une revue selon des règles explicites (conflit, ambiguïté 50–250 m, nouvelle candidate, doublon, coloc, géométrie invalide, Planned sur match/présence).

### A. Ventilation exclusive par classe primaire (somme = 3 881)

| Classification primaire | Lignes revue | % des 3 881 |
|-------------------------|-------------:|------------:|
| CONFLICT | **1 336** | 34,4 % |
| NEW_INFRASTRUCTURE_CANDIDATE | **943** | 24,3 % |
| AMBIGUOUS | **812** | 20,9 % |
| OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE | **498** | 12,8 % |
| MATCH_EXISTING_INFRASTRUCTURE | **236** | 6,1 % |
| COLOCATED_MULTI_OPERATOR | **28** | 0,7 % |
| POSSIBLE_DUPLICATE | **24** | 0,6 % |
| INVALID_GEOMETRY | **4** | 0,1 % |
| PLANNED_SITE | **0** | 0 % |
| UNRESOLVED | **0** | 0 % |
| **Total** | **3 881** | **100 %** |

> `PLANNED_SITE` primaire = 0 en revue : les Planned « purs » (sans voisin infra) sont acceptés sans revue. Les 431 Planned présents dans les 3 881 ont une **autre** classe primaire (MATCH, CONFLICT, AMBIGUOUS, etc.).

### B. Occurrences par motif de revue (non exclusif — peut dépasser 3 881)

Motifs dérivés des `rules_applied`, flags, match et classification. **Une ligne peut porter plusieurs motifs.** Somme des occurrences observées : **16 891** (> 3 881).

| Motif | Occurrences | Ancrage moteur |
|-------|------------:|----------------|
| OPERATEUR_ABSENT_OU_INCOMPATIBLE | 2 700 | règle `OPERATOR_DIFFERENT_ON_NEAR_INFRA` |
| GEOMETRIE_PROCHE_NOM_INCOMPATIBLE | 1 336 | `CONFLICT_NEAR_DISSIMILAR` (≤50 m, name_sim&lt;0,2, ops ≠) |
| CONFLIT_OPERATEUR | 1 336 | même règle CONFLICT |
| NOUVELLE_INFRASTRUCTURE_CANDIDATE_VALIDATION | 943 | `NO_NEARBY_INFRASTRUCTURE` |
| DISTANCE_SPATIALE_LIMITE_OU_TROP_GRANDE | 812 | `WEAK_SPATIAL_CANDIDATE` / bande 50–250 m |
| CANDIDATS_A_DISTANCE_COMPARABLE / RAPPROCHEMENT_NON_DECIDABLE_AUTO | 812 | classe AMBIGUOUS |
| COLOCALISATION_MULTI_OPERATEUR_A_CONFIRMER | 635 | `COLLOCATION_MULTI_OPERATOR` / flag |
| SIMILARITE_NOM_INSUFFISANTE | 522 | name_sim &lt; 0,4 sur cas ambigus |
| SITE_PLANNED_VALIDATION | 431 | statut PLANNED + revue |
| SIMILARITE_NOM_PARTIELLE | 160 | `NAME_SIMILARITY_PARTIAL` |
| NOM_SIMILAIRE_GEOMETRIE_INCOMPATIBLE | 130 | nom fort + distance hors très proche |
| DOUBLON_PROBABLE_INTRA_OPERATEUR | 24 | `INTRA_OPERATOR_SAME_COORD` |
| GEOMETRIE_INVALIDE | 4 | quarantaine `#REF!` / invalide |

**Overlays analytiques** (pas de constante `ACCEPTANCE_THRESHOLD` dans le code) :

| Overlay | Occurrences | Sens |
|---------|------------:|------|
| SCORE_SOUS_SEUIL_ACCEPTATION_AUTO | 3 143 | score assigné &lt; 70 (hors chemin auto MATCH 85/92) |
| FAIBLE_CONFIANCE_GLOBALE | 3 091 | confiance assignée &lt; 0,7 |

**Non observés / non instrumentés dans le moteur actuel :** conflit entre plusieurs infrastructures candidates stockées en liste ; rattachement administratif contradictoire (province/territoire non comparés comme règle bloquante).

### C. Ventilation par opérateur (somme = 3 881)

| Opérateur | Lignes revue | Total opérateur | % revue / opérateur |
|-----------|-------------:|----------------:|--------------------:|
| Vodacom | 538 | 4 133 | 13,0 % |
| **Airtel** | **2 154** | 4 477 | **48,1 %** |
| Orange | 405 | 3 221 | 12,6 % |
| Africell | 784 | 784 | **100 %** |
| **Total** | **3 881** | 12 615 | 30,8 % |

### D. Ventilation par statut normalisé (somme = 3 881)

| Statut | Lignes revue |
|--------|-------------:|
| ONLINE | 3 146 |
| PLANNED | 431 |
| IN_SERVICE | 302 |
| OUT_OF_SERVICE | 1 |
| TX_ONLY | 1 |
| UNKNOWN | 0 |

### E. Niveaux de confiance (valeurs réellement assignées par le moteur)

Valeurs moteur : INVALID 1,0 · MATCH exact 0,9 / très proche 0,8 · PLANNED_SITE (sans revue) 0,85 · PRESENCE 0,78 · COLOC 0,75 · DUPLICATE 0,7 · NEW 0,6 · CONFLICT 0,55 · AMBIGUOUS `0,45+0,2×name_sim` · UNRESOLVED 0,3.

| Bande (dérivée des valeurs moteur) | Lignes |
|------------------------------------|-------:|
| CONFLIT_BLOQUANT_OU_FAIBLE (classe CONFLICT, conf=0,55) | 1 336 |
| CONFIANCE_MOYENNE (NEW 0,6 + DUPLICATE 0,7) | 967 |
| FAIBLE_CONFIANCE (AMBIGUOUS) | 812 |
| CONFIANCE_MOYENNE_HAUTE (PRESENCE 0,78 + COLOC 0,75 + MATCH 0,8) | 718 |
| HAUTE_CONFIANCE_VALIDATION_INSTITUTIONNELLE (MATCH Planned exact 0,9) | 44 |
| CERTITUDE_QUARANTAINE_GEOMETRIE (INVALID, conf=1,0) | 4 |
| **Total** | **3 881** |

### F. Pourquoi MATCH / OPERATOR_PRESENCE peuvent quand même exiger une revue

| Classe | Lignes revue | Cause moteur |
|--------|-------------:|--------------|
| MATCH_EXISTING_INFRASTRUCTURE | 236 | **100 % Planned** — `status==PLANNED` force `requires_human_review=True` même si score ~86 et confiance ~0,82. Pas un score insuffisant. |
| OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE | 498 | **481** avec co-localisation multi-opérateurs ; **50** Planned ; **498** avec opérateur infra différent. Score typique 80 / conf 0,78. |

Ce n’est **pas** : score insuffisant sur MATCH opérationnel, ni absence d’identifiant stable comme règle séparée.

### G. Review Queue Phase 4 — correction d’éligibilité

#### Gap historique des 448

Avant correction, `enqueue_review_items` n’acceptait que :
- classification ∈ `{AMBIGUOUS, CONFLICT, POSSIBLE_DUPLICATE, INVALID_GEOMETRY, NEW_INFRASTRUCTURE_CANDIDATE, COLOCATED_MULTI_OPERATOR, UNRESOLVED}`, **ou**
- flag secondaire `PLANNED_SITE`.

Conséquence : **448** lignes `OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE` avec co-localisation multi-opérateurs (sans Planned) étaient `requires_human_review=true` mais **non enfilables**.

#### Correction (minimale)

| Avant | Après |
|------:|------:|
| `requires_human_review` | **3 881** | **3 881** |
| Review-eligible (`is_review_queue_eligible`) | **3 433** | **3 881** |
| Gap | **448** | **0** |
| Enqueue durant audit / fermeture workflow | 0 | **0** (pas d’enqueue massif) |

Règle : `requires_human_review=true` ⇒ éligible Review Queue, sauf `review_queue_excluded=true` (hook documenté, inutilisé).
Plafond `max_review_items` (défaut **500**) et contrôles de rôles Phase 4 inchangés.
`OPERATOR_PRESENCE` et `MATCH` (Planned) ajoutés à `REVIEW_CLASSIFICATIONS` pour cohérence documentaire ; l’éligibilité technique repose sur `is_review_queue_eligible`.

| Indicateur | Valeur |
|------------|-------:|
| Lignes `requires_human_review=true` | **3 881** |
| Lignes review-eligible uniques | **3 881** |
| Égalité des deux ensembles | **oui** |
| Plafond défaut `max_review_items` | 500 |
| Persistés DB source MNO | **0** (aucun enqueue massif) |

### Gbis. Africell — pourquoi 100 % en revue (784 / 784)

**Cause structurelle dominante :** le référentiel `telecom.infrastructure` indexé pour le matching **ne contient aucun point opérateur AFRICELL** (0). Opérateurs présents : ORANGE 4 498 · VODACOM 3 904 · FIBERCO 3 328 · FTTX 2 846 — **pas d’AIRTEL non plus**.

Donc Africell ne peut **jamais** obtenir `OPERATOR_AGREEMENT`. Un `MATCH_EXISTING_INFRASTRUCTURE` n’est possible que via `name_sim ≥ 0,5` — **0 cas** observés. Aucune auto-acceptation.

#### Ventilation exclusive des 784 lignes Africell

| Classification primaire | Lignes | % |
|-------------------------|-------:|--:|
| CONFLICT | **502** | 64,0 % |
| OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE | **148** | 18,9 % |
| AMBIGUOUS | **98** | 12,5 % |
| NEW_INFRASTRUCTURE_CANDIDATE | **33** | 4,2 % |
| COLOCATED_MULTI_OPERATOR | **3** | 0,4 % |
| MATCH / PLANNED_SITE / DUPLICATE / INVALID / UNRESOLVED | **0** | 0 % |
| **Total** | **784** | 100 % |

#### Causes dominantes (règles)

| Signal | Occurrences |
|--------|------------:|
| `OPERATOR_DIFFERENT_ON_NEAR_INFRA` | 748 |
| `VERY_CLOSE_SPATIAL_MATCH` | 593 |
| `CONFLICT_NEAR_DISSIMILAR` | 502 |
| Co-localisation (flag/classe) | 154 |
| `WEAK_SPATIAL_CANDIDATE` (50–250 m) | 98 |
| `NO_NEARBY_INFRASTRUCTURE` | 33 |

Infra les plus proches rencontrées : ORANGE 418 · VODACOM 287 · FIBERCO 29 · FTTX 14 · aucun match 36.

**Interprétation :** ce n’est pas un seuil de confiance « trop strict » artificiel — c’est l’**absence d’Africell dans le référentiel télécom** + proximité fréquente de tours Orange/Vodacom avec noms incompatibles → CONFLICT / PRESENCE / AMBIGUOUS. Les règles n’ont **pas** été assouplies pour baisser le taux.

Lanes analytiques Africell : FAST **181** · COMPLEX **603**.

### Gter. Airtel — 2 154 revues (≈ 55,5 % de la charge nationale)

| | |
|--|--:|
| Lignes Airtel | 4 477 |
| Dont revue | **2 154** (48,1 %) |
| Part des 3 881 revues nationales | **55,5 %** |
| Auto-acceptés | 2 323 (MATCH 1 103 + PRESENCE sans revue 367 + PLANNED_SITE 853) |

**Même absence d’AIRTEL dans telecom** : les MATCH Airtel (1 139 dont 1 103 auto) passent presque uniquement par **similarité de nom ≥ 0,5**, pas par accord opérateur.

#### Ventilation exclusive des 2 154 dossiers Airtel en revue

| Classification primaire | Lignes | % des revues Airtel |
|-------------------------|-------:|--------------------:|
| NEW_INFRASTRUCTURE_CANDIDATE | **770** | 35,7 % |
| AMBIGUOUS | **619** | 28,7 % |
| CONFLICT | **583** | 27,1 % |
| OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE | **129** | 6,0 % |
| MATCH_EXISTING_INFRASTRUCTURE (Planned) | **36** | 1,7 % |
| COLOCATED_MULTI_OPERATOR | **17** | 0,8 % |
| Autres | **0** | 0 % |
| **Total** | **2 154** | 100 % |

#### Motifs / règles dominants

| Signal | Occurrences |
|--------|------------:|
| `OPERATOR_DIFFERENT_ON_NEAR_INFRA` | 1 367 |
| `NO_NEARBY_INFRASTRUCTURE` | 770 |
| `WEAK_SPATIAL_CANDIDATE` / AMBIGUOUS | 619 |
| `CONFLICT_NEAR_DISSIMILAR` | 583 |
| `STATUS_PLANNED` (parmi revues) | 197 |
| Co-localisation | 170 |

**Pourquoi ~55 % de la charge nationale :** Airtel est le plus gros volume MNO (4 477) **et** cumule (1) beaucoup de **NEW** sans voisin (770), (2) beaucoup d’**AMBIGUOUS/CONFLICT** faute d’opérateur AIRTEL dans le référentiel, (3) une base Planned importante (1 050 statut) dont une partie en revue. Lanes : FAST **935** · COMPLEX **1 219**.

### Gquater. FAST_REVIEW_CANDIDATE vs COMPLEX_REVIEW (analytique uniquement)

Ces labels **n’altèrent aucune classification métier** ni score. Ils guident la priorisation de la file.

| Lane | Classes primaires | Effectif national |
|------|-------------------|------------------:|
| **FAST_REVIEW_CANDIDATE** | NEW_INFRASTRUCTURE_CANDIDATE · MATCH (Planned) · OPERATOR_PRESENCE · POSSIBLE_DUPLICATE · INVALID_GEOMETRY | **1 705** |
| **COMPLEX_REVIEW** | CONFLICT · AMBIGUOUS · COLOCATED_MULTI_OPERATOR · UNRESOLVED | **2 176** |
| **Somme** | | **3 881** |

**FAST — conditions d’une validation humaine rapide :**
- NEW : confirmer « pas d’infra connue » puis décision institutionnelle créer / reporter ;
- MATCH Planned : ratifier le rattachement déjà spatialement fort (score ~85–92) ;
- PRESENCE : confirmer présence sur tour existante / coloc (ne crée pas d’infra) ;
- DUPLICATE : fusionner ou distinguer 2 déclarations même coord ;
- INVALID : corriger `#REF!` puis relancer.

**COMPLEX — investigation approfondie :**
- CONFLICT : géométrie ≤50 m + nom incompatible + opérateur différent — arbitrage identité ;
- AMBIGUOUS : voisin 50–250 m non décidable ;
- COLOCATED primaire : multi-op sans rattachement infra clair ;
- UNRESOLVED : fallback.

**Risques métier :**
- Enfiler les 448 PRESENCE sans les traiter → file incomplète (corrigé en éligibilité).
- Traiter Africell/Airtel sans enrichir le référentiel opérateur → CONFLICT récurrents.
- Enqueue massif 3 881 d’un coup → saturation Review Workspace (plafond 500 conservé).
- Confondre FAST avec auto-acceptation → violation Data First / Integrity Gate.

### H. Exemples représentatifs

**Conflits (5) :** `15Rue-Bobozo_KIN` Vodacom↔Orange 0,81 m name_sim=0 ; `7Maisons_HKT` ; `Abattoire-Goma_NKV` ; `Abimva_POR`↔FTTX ; `Aero2_HKT` — reco : arbitrer identité partagée vs erreur.

**Ambiguïtés (5) :** voisins 50–250 m (`Katongola2_HKT` 139 m Planned ; `Kapeluto3_KOC` 81 m) — reco : vérification terrain/admin.

**Nouvelles candidates (5) :** `GOM013`, `GOM022`, `KAB004`, `KAS005`, `KEN001` (Africell, ONLINE, aucun voisin) — reco : validation institutionnelle avant création KPI.

**Co-localisations sensibles (5) :** primaires `GOM046/049/045` Africell ; `685_Kilomines`, `134_Dikapa` Airtel — reco : confirmer coloc physique.

**Doublons (5, tous Vodacom) :** `Bracongo-Smallcell(_2)_KIN`, `CEO-House-Small-cell1/2_KIN`, `CMOC-Kisanfu2_HLU` — reco : fusionner ou distinguer.

**Géométries invalides (4) :** `Beni-Butsili-Relief_NKV`, `Butembo-Vuhira_NKV`, `Butembo-Kingdom_NKV`, `Butembo-Regideso_NKV` (Vodacom, `#REF!`).

### I. Lecture opérationnelle

| Question | Réponse |
|----------|---------|
| 5 causes principales (classes) | CONFLICT 1 336 · NEW 943 · AMBIGUOUS 812 · PRESENCE 498 · MATCH Planned 236 |
| Opérateur le plus concentré | **Airtel** (2 154 ; 55,5 % des revues) ; Africell 100 % de ses lignes |
| Cause Africell 100 % | **0 point AFRICELL** dans telecom indexé → aucun MATCH auto |
| Review-eligible | **3 881 = requires_human_review** (gap 448 corrigé) |
| Proportion / 12 615 | **30,76 %** |
| FAST_REVIEW_CANDIDATE | **1 705** (analytique) |
| COMPLEX_REVIEW | **2 176** (analytique) |

---

## 18. Estimation KPI potentiel (NON APPLIQUÉE / NON OFFICIELLE)

| Estimation | Valeur |
|------------|-------:|
| KPI officiel infrastructures | **14 580** |
| Si **toutes** les 943 nouvelles candidates étaient validées | **15 523** (théorique) |
| Sites Planned exclus du KPI « existantes » | 1 463 |
| Présences opérateurs ≠ nouvelles infra | 936 |

**Interdits confirmés :**
- ne pas remplacer 14 580 par 12 615 ;
- ne pas calculer 14 580 + 12 615 ;
- ne pas présenter 15 523 comme KPI officiel ;
- ne pas écrire dans `telecom.infrastructure`.

---

## Pourquoi 14 580 ≠ 12 615

1. **14 580** = objets physiques ponctuels déjà intégrés (tous opérateurs / backbones historiques KMZ).
2. **12 615** = déclarations MNO (présence, RAT, statut opérationnel ou planifié).
3. Une même tour peut porter Vodacom + Airtel + Orange → **plusieurs lignes MNO / une infra**.
4. **736** groupes multi-opérateurs Phase 5 (arrondi 6 décimales) ; **705** en égalité float stricte.
5. **1 463 Planned** ne sont pas des infrastructures « existantes ».
6. Le référentiel actuel et le fichier MNO ne couvrent pas les mêmes univers (Fiber/MW, Fiberco, etc. vs 4 MNO mobiles).

---

## 19. Tests exécutés

```text
tests/test_nire_phase5.py              → 16 passed
tests/test_nire_phase4.py + test_nire.py → 52 passed (non-régression)
```

Couverture Phase 5 : ingestion, SHA-256, partitions, statuts, RAT, `#REF!`, `(0,0)`, match, présence, coloc, Planned, doublon, ambiguïté/conflit, review queue, pagination/filtres, couches GeoJSON, API, UI paradoxe / exclusive vs transversal, immutabilité source, checksum exclusif 12 615.

---

## 20. Performances (run réel DB)

| Étape | Durée |
|-------|------:|
| Ingestion Excel | ~3,9 s |
| Chargement telecom | ~1,6 s |
| Réconciliation spatiale | ~33–34 s |
| **Total** | **~33–40 s** |

UI : pagination `limit≤200`, couches GeoJSON plafonnées (`limit` défaut 2 000), pas de dump brut 12 615 points.

---

## 21. Fichiers créés / modifiés

### Créés
- `api/services/nire/mno_audit.py`
- `tests/test_nire_phase5.py`
- `PROJECT_MANAGEMENT/ARCHITECTURE/NIRE_PHASE_5.md`

### Modifiés
- `api/routes/nire.py` — endpoints audit MNO
- `dashboard/modules/nire-workspace/nire-workspace.js` — onglet Audit MNO opérationnel
- `dashboard/modules/nire-workspace/nire-workspace.css` — styles aide / couches

### Non touchés (contraintes)
- `PLATFORM_STABILIZATION_GATE_V1.md`
- `decision-cartography-experience.js` (dirty EOL local uniquement)
- `data/decision/case_history.json`
- `data/raw/ceni/`, `data/reports/ceni_official/`, `work/`
- fichier MNO Excel (hors index Git)

---

## 22. État Git final (après Phase 5, sans commit)

Fichiers Phase 5 attendus pour un commit ultérieur (non effectué) :

- `api/services/nire/mno_audit.py`
- `api/routes/nire.py`
- `dashboard/modules/nire-workspace/nire-workspace.js`
- `dashboard/modules/nire-workspace/nire-workspace.css`
- `tests/test_nire_phase5.py`
- `PROJECT_MANAGEMENT/ARCHITECTURE/NIRE_PHASE_5.md`

**Aucun commit. Aucun push.**

---

## API — démarrage audit

```http
POST /api/nire/mno-audit/run
X-NIRE-Role: ADMIN
{"enqueue_reviews": true, "max_review_items": 500}
```

Puis consulter `GET /api/nire/mno-audit/status` et la File de revue Phase 4 pour les dossiers enfilés.
