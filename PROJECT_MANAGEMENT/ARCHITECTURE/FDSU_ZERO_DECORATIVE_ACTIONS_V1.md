# Zero Decorative Actions v1.0

## Règle produit

**Aucun bouton décoratif** dans SIG-FDSU RDC.

Chaque contrôle visible doit être :

1. réellement fonctionnel ; **ou**
2. désactivé avec une raison métier claire ; **ou**
3. masqué si la capacité n’existe pas.

Interdit : faux succès, messages qui renvoient verbalement ailleurs, placeholders « bientôt », routes mortes, erreurs silencieuses.

## Convention de contribution

> Tout nouveau bouton doit être livré avec son handler, sa route ou API, ses états UX et au moins un test.

## Registre de capacités

- Backend : `GET /api/exports/capabilities` (`api/services/export_service.py`)
- Frontend : `dashboard/modules/shared/capability-registry/capability-registry.js` → `window.CapabilityRegistry`

| Capacité | v1 |
|----------|----|
| `export_excel` | true |
| `export_pdf` | false |
| `export_powerpoint` | false |
| `mission_planning` | false |
| `simulation` | false |
| `comparison` | false |
| `map_navigation` | true |

## Infrastructure d’export

| Format | Endpoint | État |
|--------|----------|------|
| Excel | `GET /api/exports/decision-case/{type}/{id}/excel` | **réel** (.xlsx openpyxl) |
| PDF | `.../pdf` | 501 — bouton disabled |
| PowerPoint | `.../powerpoint` | 501 — bouton disabled |

## Inventaire initial (Dossier de décision)

| Module | Libellé | Sélecteur | Action attendue | État initial | Correction |
|--------|---------|-----------|-----------------|--------------|------------|
| DXL | Retour | `[data-dxl-action=back]` | Historique / contexte | functional (faible) | returnHash session |
| DXL | Voir sur la carte | `map` | Centrer site | partial | `openDecisionSiteOnMap` |
| DXL | Intelligence territoriale | `ti` | Ouvrir TI | misleading si sans territoire | erreur métier |
| DXL | Expliquer | `explain` | Scroll justification | functional | inchangé + feedback |
| DXL | Impact spatial | `spatial` | Route NSME | functional | inchangé |
| DXL | Préparer une mission | `mission` | Workflow | placeholder | **masqué** |
| DXL | Exporter Excel | `export` | Télécharger xlsx | placeholder | **export réel** |
| DXL | Préparer PDF | `pdf` | PDF | placeholder | **disabled + motif** |
| DXL | Préparer PowerPoint | `ppt` | PPT | placeholder | **disabled + motif** |
| DXL | Simulation future | `simulate` | Simulation | placeholder | **masqué** |

## Corrections de rendu

- `[object Object]` → extraction `summary.text` / `recommendation`
- Dates ISO → format FR utilisateur ; ISO en détail technique
- Chemins fichiers → libellés métier ; chemin sous `<details>` traçabilité
- Lacunes `—` → « Aucune lacune identifiée »

## Tests obligatoires

- `tests/test_zero_decorative_actions.py`
- `tests/e2e/zero-decorative-actions.spec.js`

## Limites restantes

- Audit exhaustif de tous les modules (gouvernance, profil entité PDF, démo actions) partiellement traité ; DXL + détail KPI + capacités centralisées en priorité.
- PDF / PPT / mission / simulation non générés (volontairement absents ou disabled).
- Comparaison Decision Workspace reste scaffoldée (capacité `comparison=false`).
