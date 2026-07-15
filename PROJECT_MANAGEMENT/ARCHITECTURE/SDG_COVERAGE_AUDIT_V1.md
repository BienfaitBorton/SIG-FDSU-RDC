# SDG Coverage Audit & Explainability — v1.0

**Moteur :** `sdg-coverage-1.0.0`  
**Doctrine :** Data First / No Black Box — aucun graphe fictif, aucune géométrie / population / rayon inventés.  
**Date de référence audit structurel :** 2026-07-15

---

## 1. Constat

Le message unique « Analyse d’Impact Territorial indisponible — aucun rendu générique » masquait les causes réelles.

Cause dominante pour les **Sites 20 476** :

> Les sites du programme national sont présents en fichier (`data/programs/sites_20476`) **avec géométries**, mais **absents** de `programs.fdsu_sites` (NSME).  
> Seuls Sites 40 (40) et Sites 300 (300) sont chargés en base.

---

## 2. Matrice structurelle (snapshot)

| Programme | Total | Complet (NSME) | Partiel | Impossible | % atteignable |
|-----------|------:|---------------:|--------:|-----------:|--------------:|
| Sites 40 | 40 | 40 | 0 | 0 | 100 |
| Sites 300 | 300 | 300 | 0 | 0 | 100 |
| Sites 20 476 | 20 476 | 0 | 20 476 | 0 | 100* |
| CCN DEMO | 24 | 0 | 24 | 0 | 100* |
| **Total** | **20 840** | **340** | **20 500** | **0** | — |

\* Atteignable = coords valides → une analyse **peut être tentée** (fallback fichier+spatial pour 20 476 ; DEMO pour CCN).  
**Taux NSME natif** = 340 / 20 840 ≈ **1,6 %**.

### Qualité

| Indicateur | Valeur |
|------------|-------:|
| Sans coordonnées | 0 |
| Sans population native (40+300) | 340 |
| Sans rattachement admin | 0 |
| Hors référentiel NSME | 20 476 |

---

## 3. Classification A / B / C

| Classe | Sens |
|--------|------|
| **A** Complet | NSME + coords + couches locales nombreuses |
| **B** Partiel | Certaines couches seulement, ou inventaire fichier / DEMO |
| **C** Impossible | Pas de coords / actif introuvable — **fiche explicative obligatoire** |

---

## 4. Explicabilité UI

Le graphe expose désormais `explainability` :

- données disponibles (province, territoire, score, programme, …) ;
- données manquantes (coordonnées, localités, rayon, population, relations) ;
- causes techniques (`site_hors_referentiel_nsme`, …) ;
- badge « Analyse complète / partielle / impossible ».

En cas d’échec de mount, le client appelle  
`GET /api/sdg/assets/{id}/explainability`  
au lieu d’afficher le message générique.

---

## 5. Analyse partielle

`build_graph` ne retourne plus `None` systématiquement :

- actif résolu hors NSME avec coords → matching spatial réel (NCI, santé, télécom, routes) ;
- aucune arête inventée ;
- si vraiment introuvable → payload `classification=C` + explicabilité (HTTP 200).

Fallback NSME : `get_asset_needs` résout via `site_entity_resolver` / fichiers programmes.

---

## 6. API

| Endpoint | Rôle |
|----------|------|
| `GET /api/sdg/coverage` | Matrice nationale |
| `GET /api/sdg/assets/{id}/explainability` | Diagnostic d’un dossier |

Champs clés coverage : `coverage_rate`, `nsme_native_rate`, `complete`, `partial`, `missing`, `pending_nsme_load`, `missing_by_reason`, `programs`, `matrix`.

---

## 7. Salle de Pilotage

Carte **« Maturité analytique du SIG »** :

- SDG complet (NSME) ;
- SDG partiel ;
- À charger en NSME ;
- Taux NSME natif %.

---

## 8. Recommandations (priorité données)

1. **Charger Sites 20 476** dans `programs.fdsu_sites` (seed contrôlé).  
2. Matérialiser / cacher les relations spatiales (performance dossiers).  
3. Consolider population native (40/300 restent sur NCI spatial).  
4. Séparer clairement inventaire CCN DEMO vs production.  
5. Ne pas confondre « référentiel intégré » (data) et « site opérationnel » (PLE).

---

## 9. Tests & captures

- Backend : `tests/test_sdg_coverage_audit.py`  
- Playwright : `tests/e2e/sdg-coverage-audit.spec.js`  
- Captures : `PROJECT_MANAGEMENT/ARCHITECTURE/captures/sdg-coverage/`

---

## 10. Limites

- L’audit structurel national ne recalcule pas les 20 476 intersections spatiales (coût).  
- Les échantillons `deep_sample` permettent une vérification profonde ciblée.  
- Le fallback fichier est un **pont** Data First, pas la cible architecture cible.
