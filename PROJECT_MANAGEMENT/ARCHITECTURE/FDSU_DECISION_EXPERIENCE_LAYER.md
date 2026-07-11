# Decision Experience Layer & Infobulles — Rapport final sprint

**Date** : 2026-07-11  
**Branche** : `feature/smart-map-interactions`  
**Statut** : implémentation prête pour validation manuelle — **aucun commit sans validation**

---

## 1. Inventaire des cartes

| Vue | Couche | Géométrie | Tooltip | Clic | Vue métier | Test |
|-----|--------|-----------|---------|------|------------|------|
| Cartographie générale | provinces, territoires, collectivites, groupements, villages | Poly/Point | Oui (`SigMapTooltips.bind`) | Fiche / TI (dblclick territoire) | Profil + `#territorial-intelligence/<id>` | Unitaire + e2e factory |
| Cartographie | sites_40 / sites_300 / sites_all | Point | Oui | `#decision-case/site/<id>` | DXL | Unitaire |
| Cartographie | telecom_* | Point/Line | Oui | Sélection + popup | Fiche télécom | Unitaire |
| Cartographie | spatial_relations | Line | Oui | Popup | — | Unitaire |
| Cartographie | asset_need_matches (NSME) | Point/Line | Oui | DXL / spatial-impact | `#decision-case` / `#spatial-impact` | Unitaire NSME |
| Cartographie | missions | Point | Oui | Fiche | Profil | Unitaire |
| Intelligence territoriale | site, ccn, health, uncovered, territory | Point/Poly | Oui | DXL / decision-detail | Hash métier | Unitaire |
| Centre de Décision — moteur | sites scorés | Point | Oui | DXL | `#decision-case/site/<id>` | e2e DXL |
| Centre de Décision — santé | établissements | Point | Oui | Analyse détaillée | `#decision-detail/sante` | e2e santé |
| Centre de Décision — vue nationale | provinces | Poly | Oui | — | Contexte | Unitaire |
| Analyse détaillée KPI | objets KPI | Point | Oui | DXL | `#decision-case` | Unitaire |
| Dossier DXL | actif / besoins / liaisons | Point/Line | Oui | reste dans dossier | DXL | e2e |
| Module CCN | CCN, sites, liaisons | Point/Line | Oui | DXL | `#decision-case/ccn/<id>` | Unitaire |
| Géocodage | résultats | Point | Oui | Popup | — | Unitaire |
| Dashboard détail | zones / couches | Poly/Point | Oui | Sélection liste | — | Unitaire |
| Carte nationale | admin / sites | Poly/Point | Oui | Contexte spatial | — | Unitaire |
| Salle Pilotage DG (EDVS) | carte cockpit | Variable | Partiel | Navigation métier | EDVS | Limite |

## 2. Endpoints API consommés (fetch interne uniquement)

- `/api/decision/case/{id}`
- `/api/decision/details/{kpi}` (+ map/export)
- `/api/spatial-matching/assets/{id}/needs|impact|explain`
- `/api/spatial-matching/map`
- `/api/territorial-intelligence/territories[/{id}[/map|/recommendations|/explain]]`
- `/api/ccn/*`
- `/api/executive/cockpit`

## 3. Routes front créées / renforcées

| Route | Module |
|-------|--------|
| `#decision-detail/<kpi_code>` | Analyse détaillée |
| `#decision-case/<asset_type>/<id>` | DXL dossier |
| `#spatial-impact/<asset_type>/<id>` | DXL impact |
| `#coverage-detail/<territory_id>` | DXL couverture |
| `#ccn-detail/<id>` | DXL (alias CCN) |
| `#territorial-intelligence/<territory_id>` | TI préchargée |

## 4. Dossiers de décision disponibles

- Site FDSU (Sites 40 / 20 476 / scorés) via `#decision-case/site/<id>?program_code=`
- CCN via `#decision-case/ccn/<id>` ou `#ccn-detail/<id>`
- Impact spatial via `#spatial-impact/site/<id>`
- Couverture via `#coverage-detail/<territory_id>`

## 5. Visualisations DXL

- Résumé exécutif (KPI métier)
- Carte interactive NSME / TI
- Waterfall « Pourquoi ? »
- Bandeau contexte territorial (population restante, NDCI, …)
- Impacts attendus (population, localités, confiance)
- Risques / lacunes
- Doctrine & traçabilité
- Recommandation rédigée

## 6. Actions métier

Retour · Voir sur la carte · Intelligence territoriale · Expliquer · Impact spatial · Préparer une mission · Exporter Excel · Préparer PDF · Préparer PowerPoint · Simulation future  

PDF/PPT : boutons **préparés** (statut métier, pas décoratifs).

## 7. Tests exécutés

- `tests/test_map_tooltips.py`
- `tests/test_decision_experience.py`
- `tests/test_decision_kpi_details.py`
- `tests/test_spatial_matching.py`
- e2e : `tests/e2e/map-tooltips.spec.js`, extension `decision-center.spec.js`

## 8. Performance

- Tooltips liés à la création de couche (plus de rebind systématique au seul mouseover)
- Fetch DXL en parallèle (case + impact + map)
- TI contextuelle optionnelle (non bloquante si échec)

## 9. Limites restantes

1. **EDVS cockpit map** : tooltips encore légers selon payload.
2. **Export PDF/PPT** : préparation UX, pas d’export binaire.
3. **MarkerCluster** : résumé cluster si introduit plus tard.
4. **Popups historiques** : restent en complément des tooltips (non bloquants).
5. **Validation manuelle navigateur** : obligatoire avant commit (cartographie, TI, CCN, Centre, DXL, EDVS, NCI, NSME).

## 10. Fichiers clés

- `dashboard/modules/shared/map-tooltips.js`
- `dashboard/modules/decision-experience/decision-experience.js`
- `dashboard/modules/decision-experience/decision-experience.css`
- `PROJECT_MANAGEMENT/ARCHITECTURE/FDSU_DECISION_EXPERIENCE_LAYER.md`
