# Decision Workspace v1.1 — Rapport sprint

**Date** : 2026-07-11  
**Branche** : working tree (non commité)  
**Statut** : socle livré pour validation — **aucun commit**

## Architecture retenue

```
KPI / UxPremium / openDecisionWorkspace
        │
        ▼
#decision-detail/<slug>   ←── alias #decision-workspace/<slug>
        │
        ▼
decision-detail.js (inchangé contractuellement)
        │  syncFromDetailPayload / selectEntity / map click
        ▼
DecisionWorkspace (shared) ── chrome : fil · résumé · reco · historique · comparaison (socle)
        │
        ├── UxPremium (états, légendes)
        ├── EdvsCharts / Edvs (réutilisés, non dupliqués)
        ├── SigMapTooltips (sélection + DXL)
        └── openDecisionCase → Decision Experience Layer
```

**Principe** : le Workspace est un **composant d’attache** sur `#decision-detail-panel`, pas un module concurrent. Les modules existants (CD, TI, CCN, DXL) restent les sources ; ils convergent progressivement via `openDecisionWorkspace` / adapters de domaine.

**Extensibilité** : `DecisionWorkspace.registerDomainAdapter(domainId, adapter)` pour économie, énergie, routes, santé, télécoms, éducation, marchés.

## Composants créés

| Artefact | Rôle |
|----------|------|
| `dashboard/modules/shared/decision-workspace/decision-workspace.js` | État, fil hiérarchique, sync sélection, sections, API publique |
| `dashboard/modules/shared/decision-workspace/decision-workspace.css` | Chrome UI (tokens UX Premium) |
| `tests/e2e/decision-workspace.spec.js` | Couverture e2e v1.1 |
| `PROJECT_MANAGEMENT/ARCHITECTURE/FDSU_DECISION_WORKSPACE_V1.md` | Ce rapport |

## Composants réutilisés

- UX Premium (`stateHtml`, légendes)
- Edvs / EdvsCharts (KPI & charts déjà dans decision-detail / CD)
- SigMapTooltips (clic carte → sélection + dossier)
- Decision Experience Layer (`openDecisionCase`)
- Routes / APIs decision-detail inchangées (`/api/decision/details/...`)
- Master Registry / Knowledge Hub : hooks documentés (historique session socle ; persistance ultérieure)

## Fil d’analyse

`RDC → Province → Territoire → Collectivité → Groupement → Localité → Site`

- Rendu dans `#decision-workspace-trail`
- Clic sur un cran → recentrage filtres province/territoire + rechargement détail (contrat API existant)
- Construit depuis l’entité sélectionnée (ligne / carte)

## Vues raccordées

| Point d’entrée | Comportement |
|----------------|--------------|
| `openDecisionDetail` | Attache le chrome Workspace, hash `#decision-detail/...` |
| `openDecisionWorkspace` | Contexte (trail/sélection) + ouverture détail |
| UxPremium KPI (`detailKey`) | Préfère `openDecisionWorkspace` |
| Alias `#decision-workspace/...` | Même module `decision_detail` |
| Clic ligne tableau | Sélection synchronisée (sans casser « Fiche » → DXL) |
| Clic marqueur carte | `bindMapFeatureSelection` puis DXL |

## Tests exécutés

```
npx playwright test tests/e2e/decision-workspace.spec.js
```

| Test | Résultat |
|------|----------|
| API DecisionWorkspace chargée | OK |
| Ouverture via KPI — chrome + fil RDC + route préservée | OK |
| Alias `#decision-workspace` | OK |
| Synchronisation sélection ligne → fil + sync | OK |
| Pas de régression — DXL priorisation | OK |

**5/5 passed** (~90 s, chromium-desktop)

## Performances

- Chrome injecté une fois (DOM léger)
- Pas de refetch API supplémentaire hors filtres spatiaux déjà prévus
- Sync sélection = DOM + event bus mémoire (`syncToken`)
- Compatible responsive (trail wrap, grilles auto-fit)

## Risques résiduels

1. **Historique** : session-only ; pas encore lié Master Registry / case_history.  
2. **Comparaison** : socle UI uniquement.  
3. **Clic trail → apply filters** : dépend des champs texte province/territoire (pas d’IDs admin stricts).  
4. **Double attache** possible si `initializeDecisionDetailModule` rappelé souvent — idempotent via `#decision-workspace-chrome`.  
5. Migration complète des autres modules (TI/CCN) vers Workspace : sprint suivant.

## Fichiers working tree (commit après validation)

- `dashboard/modules/shared/decision-workspace/*`
- `dashboard/index.html`
- `dashboard/modules/decision-center/decision-detail.js`
- `dashboard/modules/shared/ux-premium/ux-premium.js`
- `dashboard/app.js`
- `tests/e2e/decision-workspace.spec.js`
- `PROJECT_MANAGEMENT/ARCHITECTURE/FDSU_DECISION_WORKSPACE_V1.md`

**Ne pas committer** : `data/decision/case_history.json` s’il apparaît dirty.
