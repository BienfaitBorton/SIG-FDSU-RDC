# Consolidation FDSU — référentiel des sites opérateurs mobiles

**Moteur :** `telecom-operator-sites-consolidation-fdsu-1.0.0`
**Source MNO (immuable) :** `data/raw/Operators existing and planned sites_20260713.xlsx`
**API :** `GET /api/telecom/operator-sites-consolidation`

> Ce document porte sur le **référentiel consolidé des sites opérateurs**.
> Il **n’utilise pas** les scénarios d’infrastructures physiques mutualisées (12 289 / 15 614 / min-max).

---

## Règles institutionnelles

| Règle | Effet |
|-------|--------|
| Opérateur par opérateur | Pas de dédup Vodacom↔Orange↔Airtel↔Africell |
| Même site même opérateur | Compté **une fois** ; enrichissement MNO + provenance |
| Absent du MNO | **Conservé** (Vodacom/Orange DB) |
| Absent de la DB | **Ajouté** depuis MNO |
| Proximité seule | Ne fusionne pas ; `POSSIBLE_DUPLICATE` si signal faible |
| Nom identique + petites différences GPS | Même site (intra-opérateur) |
| Planned | Conservés + couche dédiée ; exclus du compteur Existing |
| Fibre / MW / Fiberco / FTTX | **Hors** `TOTAL_MOBILE_OPERATOR_SITES` |

---

## Résultats (run validé)

### VODACOM

| Poste | Valeur |
|-------|-------:|
| Ancien DB | **3 904** |
| Nouveau fichier | **4 133** |
| Correspondances / doublons ancien↔nouveau | **3 904** |
| Nouveaux sites ajoutés | **229** |
| Anciens absents MNO (conservés) | **0** |
| **Total Vodacom consolidé** | **4 133** |

### ORANGE

| Poste | Valeur |
|-------|-------:|
| Ancien DB | **4 499** |
| Nouveau fichier | **3 221** |
| Correspondances / doublons ancien↔nouveau | **2 808** |
| Nouveaux sites ajoutés | **413** |
| Anciens absents MNO (conservés) | **1 691** |
| **Total Orange consolidé** | **4 912** |

### AIRTEL

| Poste | Valeur |
|-------|-------:|
| Source | **4 477** |
| Doublons internes collapsed | **0** |
| **Total consolidé** | **4 477** |

### AFRICELL

| Poste | Valeur |
|-------|-------:|
| Source | **784** |
| Doublons internes collapsed | **0** |
| **Total consolidé** | **784** |

---

## Totaux sites opérateurs

| Indicateur | Valeur |
|------------|-------:|
| **TOTAL_MOBILE_OPERATOR_SITES_ALL** | **14 306** |
| **TOTAL_EXISTING_MOBILE_OPERATOR_SITES** (hors Planned) | **12 843** |
| **TOTAL_PLANNED** | **1 463** |

```
14 306 = 4 133 + 4 912 + 4 477 + 784
12 843 + 1 463 = 14 306
```

Aucune soustraction de mutualisation inter-opérateurs.

---

## Métriques séparées (hors total opérateurs)

| Domaine | Valeur |
|---------|-------:|
| Fiberco (nœuds) | **3 331** |
| FTTX (nœuds) | **2 846** |
| Fibre nœuds total | **6 177** |
| Lignes Fibre | **9 029** |
| MW (liaisons) | **1 515** |

---

## Cartographie

Couches indépendantes : Vodacom · Orange · Airtel · Africell · MNO Planned
Non mélangées au compteur opérateurs : Fibre · MW · Fiberco · FTTX

Attributs site : nom, opérateur, coordonnées, statut, RAT, provenance.

---

## NIRE

Aide à la détection des doublons **intra-opérateur**, provenance, variantes de noms, anomalies.
Ne remet pas en cause l’intégration institutionnelle FDSU.
Incertitude → conserver les deux + `POSSIBLE_DUPLICATE`.

---

## Tests

`tests/test_telecom_operator_sites_consolidation.py`
