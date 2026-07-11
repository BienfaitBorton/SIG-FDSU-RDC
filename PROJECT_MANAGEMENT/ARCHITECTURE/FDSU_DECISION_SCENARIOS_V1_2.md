# Decision Scenarios & Mission Workflows v1.2 — Rapport

**Date** : 2026-07-11  
**Statut** : livrable prêt pour validation — **aucun commit**

## Architecture retenue

```
Questions métier / onglet Simulations / #decision-scenario/<id>
        │
        ▼
DecisionScenarios (UI) ── GET /api/decision/scenarios
        │                   GET /api/decision/scenarios/{id}/run
        ▼
decision_scenarios_service (orchestration pure)
        ├── Decision Engine / site priorities / explain-kpi
        ├── CCN doctrine + extensions
        ├── Territorial Intelligence (profil / explain / reco)
        ├── NSME impact / explain
        └── Explainable Decision (case / explain / pdf-template)
        │
        ▼
Rendu : résumé · KPI (Edvs) · graphiques (EdvsCharts) · reco · justification · liens · actions
        │
        ├── Decision Workspace (chrome sync)
        ├── DXL (dossiers / impact spatial)
        └── Routes existantes préservées
```

**Principe** : aucune logique métier dupliquée — le service v1.2 **orchestre** uniquement.

**Extensibilité** : ajouter une entrée dans `SCENARIO_CATALOG` + une fonction `_run_*` dans `RUNNERS`.

## Composants réutilisés

| Composant | Usage |
|-----------|--------|
| Decision Workspace | Attache / message sync à l’exécution |
| EDVS / EdvsCharts | KPI strip + graphiques |
| UX Premium | États vides / erreurs |
| Explainable Decision Engine | Dossier DG, justification |
| NSME | Impact investissement |
| Territorial Intelligence | Priorité territoire / CCN |
| CCN doctrine & extensions | Implantation CCN |
| SigMapTooltips / DXL | Actions carte & dossiers |
| Master Registry / Knowledge Hub | Via profils TI & dossiers (indirect) |

## Nouveaux scénarios disponibles

| Code | ID | Question |
|------|-----|----------|
| A | `invest_priority` | Où investir en priorité ? |
| B | `ccn_implantation` | Où implanter un nouveau CCN ? |
| C | `territory_priority` | Pourquoi ce territoire est-il prioritaire ? |
| D | `investment_impact` | Quel sera l’impact de cet investissement ? |
| E | `dg_dossier` | Préparer un dossier de décision pour le DG |

UI : onglet **Simulations** du Centre de Décision + hash `#decision-scenario/<id>`.

## Fichiers modifiés / créés

**Créés**
- `api/services/decision_scenarios_service.py`
- `dashboard/modules/shared/decision-scenarios/decision-scenarios.js`
- `dashboard/modules/shared/decision-scenarios/decision-scenarios.css`
- `tests/e2e/decision-scenarios.spec.js`
- `PROJECT_MANAGEMENT/ARCHITECTURE/FDSU_DECISION_SCENARIOS_V1_2.md`

**Modifiés**
- `api/routes/decision_engine.py` — endpoints `/scenarios*`
- `api/services/decision_demo_service.py` — intents branchés sur scénarios v1.2
- `dashboard/index.html` — panel Simulations + assets
- `dashboard/modules/decision-center/decision-center.js` — tab + intents + `setDecisionCenterTab` export
- `dashboard/app.js` — route `#decision-scenario/*`

## Tests exécutés

```
npx playwright test tests/e2e/decision-scenarios.spec.js
```

| Test | Résultat |
|------|----------|
| API + catalogue UI (5 scénarios) | OK |
| Ouverture scénario A — investir en priorité | OK |
| Recommandations et actions cliquables | OK |
| Cohérence hash scénario | OK |
| Pas de régression CD + Workspace | OK |

**5/5 passed** (~52 s, chromium-desktop)

## Performances

- Catalogue : 1 GET léger
- Run : agrégation de services existants (top sites limités à 5–10)
- Pas de recalcul massif de scores dans le runner
- UI : rendu DOM local + EdvsCharts SVG

## Recommandations scénarios suivants

1. Brancher `prepare_mission` sur `POST /missions` avec contexte dossier.  
2. Scénario « zones blanches télécom » (NCI + NSME).  
3. Comparaison multi-sites dans Decision Workspace.  
4. Export PDF DG one-click depuis `dg_dossier`.  
5. Paramètres de contexte UI (choix territoire / programme) avant run.
