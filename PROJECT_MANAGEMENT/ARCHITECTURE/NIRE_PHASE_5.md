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

### D. Revue humaine — dossiers uniques

| Métrique | Valeur |
|----------|-------:|
| **Lignes uniques `requires_human_review=true`** | **3 881** |

Ventilation par motif (= classification primaire de la ligne, **sans double comptage** ; somme = 3 881) :

| Motif (classe primaire) | Lignes |
|-------------------------|-------:|
| CONFLICT | 1 336 |
| NEW_INFRASTRUCTURE_CANDIDATE | 943 |
| AMBIGUOUS | 812 |
| OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE | 498 |
| MATCH_EXISTING_INFRASTRUCTURE | 236 |
| COLOCATED_MULTI_OPERATOR | 28 |
| POSSIBLE_DUPLICATE | 24 |
| INVALID_GEOMETRY | 4 |

> Ne pas additionner « ambiguïtés + conflits + doublons » hors de ce tableau unique : les flags transversaux (coloc, Planned) chevauchent ces classes.

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
