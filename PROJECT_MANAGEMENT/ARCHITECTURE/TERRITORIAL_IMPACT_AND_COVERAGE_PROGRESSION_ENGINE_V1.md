# Moteur d’Impact Territorial et d’Évolution de la Couverture — v1.0

**Statut :** opérationnel (v1)  
**Moteur :** `tie-1.0.0`  
**Doctrine :** Data First / No Black Box — aucune population, date ou taux inventé.

---

## 1. Objectif

Enrichir le Spatial Decision Graph et le dossier de décision avec l’**impact humain** :

- localités desservies (liste nominative) ;
- population concernée ;
- déjà couverte / nouvellement couverte / restante ;
- progression cumulative par déploiement ;
- distinction stricte **site FDSU (couverture réseau estimée)** vs **CCN (accès services numériques)**.

Les relations SDG/NSME existantes sont **réutilisées**, non remplacées.

---

## 2. Audit des sources

| Source | Identifiant | Localité | Population | Couverture | Site associé | Géométrie | Qualité |
|--------|-------------|----------|------------|------------|--------------|-----------|---------|
| NCI uncovered | `NCI-UNC-…` | name + admin | `population` | uncovered | `destination` (soft) | lat/lon | CDQS |
| NCI covered | `NCI-COV-…` | name + admin | `population` | covered | soft | lat/lon | CDQS |
| NCI aggregates | province / territoire | counts | covered+uncovered | ratios | — | — | medium/high |
| Sites 40 / 300 | id / code | admin | **absente** | — | self | point | coords |
| Sites 20 476 | `site_code` | admin | `population` + range | indirect NCI | self | point | import CSV |
| `public.localites` | id/code | nom | **aucune** | — | hiérarchie | geom | référentiel |
| CCN DEMO | `CCN-DEMO-…` | admin | `population_served` | n/a (services) | `site_fdsu_code` | point | démonstration |

Endpoint matrice : `GET /api/territorial-impact/audit/sources`

---

## 3. Résolution des localités

Priorité :

1. Identifiant NCI (`need_id`)  
2. Appariement spatial NSME dans le rayon de service  
3. Alignement nominal (documenté, non fusionnant à lui seul)

Chaque ligne expose `resolution.{method,confidence,source,ambiguity}`.

---

## 4. Garde anti double-comptage

Clé stable : `nci:{need_id}` (sinon géo+nom normalisé).

- Au niveau **site** : dédup séparée covered / uncovered.  
- Au niveau **scénario** : ensemble global `covered_keys` — une localité NCI n’est crédité qu’au **premier** déploiement qui l’atteint.  
- CCN **n’incrémente pas** le cumul radio.

Champs exposés : `population_brute`, `population_dedupliquee`, `doublons_exclus`, `localites_sans_population`.

---

## 5. Profil site FDSU

`GET /api/territorial-impact/sites/{id}?program_code=sites_40`

Contient baseline rayon, impact avant/après (estimé), liste localités, sources, limites, `explainability.calculation_detail`.

`deployment_date` reste `null` si inconnue — **jamais inventée**.

---

## 6. Profil CCN

`GET /api/territorial-impact/ccn/{id}`

- `nature = acces_services_numeriques_ccn`  
- Pas de `new_population_covered` radio  
- Badge **Donnée partielle** / mode demonstration  

---

## 7. Scénario de déploiement

`GET /api/territorial-impact/scenario?programs=sites_40,sites_300&mode=planned&limit_per_program=25`

Modes : `planned` | `simulation` (badges).  
Ordre v1 : phase programme (40 → 300 → 20476 → CCN) puis id.

Charts :

- `cumulative_curve`  
- `contribution_bars` (CCN colorés distinctement)  
- `coverage_composition`  
- `by_program`  
- `localities_progression`

Cache TTL 300 s (`_meta.last_calculation`).

---

## 8. Intégration UI

| Surface | Comportement |
|---------|--------------|
| Dossier de décision | Section `#dxl-section-territorial-impact` + clic localité → focus Leaflet |
| Salle de Pilotage | Bloc « Progression de la couverture du Service Universel » |
| Mode Présentation | KPI « Nouveaux bénéficiaires » (bandeau) → scroll/focus section Impact ; section `#dxl-section-territorial-impact` non masquée |

Fichiers : `dashboard/modules/shared/territorial-impact/`

---

## 9. Réel / planifié / simulé

| Badge | Condition |
|-------|-----------|
| Réalisé | Statuts opérationnels explicites |
| En cours | Chantier / en cours |
| Planifié | défaut (ex. « à qualifier ») |
| Simulé | `mode=simulation` |
| Donnée partielle | CCN DEMO |

---

## 10. Limites v1

- Sites 40/300 sans population native → impact = NCI spatial.  
- Pas de dates réelles de mise en service dans le référentiel actuel.  
- Taux « après » = estimation sur populations **connues** du rayon ; localités sans pop → pas d’affirmation de couverture totale absolue nationale.  
- Scénario limité (`limit_per_program`) pour la performance.  
- FK NCI ↔ `public.localites` non encore matérialisée.

---

## 11. Tests

- Backend : `tests/test_territorial_impact_engine.py`  
- Playwright : `tests/e2e/territorial-impact.spec.js`  
- Captures : `PROJECT_MANAGEMENT/ARCHITECTURE/captures/territorial-impact/`

---

## 12. Non modifié

Matrices officielles, scores de priorité, doctrines, données brutes, relations SDG (enrichissement UI non destructif uniquement).
