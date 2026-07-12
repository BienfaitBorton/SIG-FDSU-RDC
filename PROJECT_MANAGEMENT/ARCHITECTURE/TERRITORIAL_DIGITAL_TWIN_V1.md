# Territorial Digital Twin Foundation v1.0

## Vision

Le **Jumeau Numérique Territorial** est le dossier unifié d’une entité administrative (Province → Localité). Il répond à :

> Que savons-nous de ce territoire, quels sont ses besoins, ses infrastructures, ses contraintes, ses investissements et ses priorités ?

Ce socle **compose** les moteurs existants. Il ne duplique pas leurs données et n’invente aucune valeur manquante.

## Architecture

```
UI (Decision Workspace · mode TDT)
        │  hash #territorial-twin/{type}/{id}
        ▼
/api/territorial-digital-twin/...
        │
        ▼
territorial_digital_twin_service  (agrégation résiliente)
        │
        ├── Master Registry          (identité)
        ├── Territorial Intelligence (profil, priorité, reco)
        ├── Territorial Summary      (synthèse province)
        ├── National Coverage Intel. (connectivité)
        ├── Transport Intelligence   (accessibilité)
        ├── Health                   (services sanitaires)
        ├── Programs / CCN           (investissements)
        ├── Decision / Explainable   (via TI)
        ├── National Data Fabric     (qualité / provenance)
        └── Knowledge Hub            (doctrines — via moteurs)
```

Principe : **une couche d’agrégation**, pas un référentiel parallèle.

## Contrat commun

Réponse stable du endpoint principal :

- `entity`, `hierarchy`
- `summary`, `connectivity`, `public_services`, `accessibility`
- `energy`, `economy`, `programs`, `decision`, `quality`
- `timeline[]`, `sources[]`, `section_status{}`
- `_meta.overall_status` ∈ `success | partial | unavailable | error`

Chaque section porte `_section.status`, `source`, `updated_at`, `note`.

Aucune valeur `undefined` / `NaN` côté sérialisation JSON.

## Sources

| Bloc | Source | Statut v1 |
|------|--------|-----------|
| Identité | Master Registry / TI | alimenté |
| Profil | TI / TST | alimenté (province, territoire) |
| Connectivité | NCI | alimenté si agrégat |
| Santé | `/api/health` | alimenté |
| Éducation / admin / marchés | NDF planned | préparés |
| Accessibilité | Transport + sites | alimenté si géométrie |
| Énergie | NDF planned | **unavailable** explicite |
| Économie | TI / NDF | partial ou unavailable |
| Programmes | TI / TST / CCN | alimenté |
| Décision | TI / TST scores | alimenté |
| Qualité | NDF | alimenté |
| Timeline | TDT extensible (hors `case_history.json`) | socle |

## Composition des moteurs

`build_twin` exécute les sections en **série résiliente** (`_compose_section` isole les exceptions). Un échec secondaire ne bloque pas la réponse : statut `error` / `partial` / `unavailable` local.

Le parallélisme utilisateur est assuré par les endpoints sectionnels + chargement progressif frontend.

## Cycle de vie

1. Résolution d’identité (`resolve_entity`)
2. Hiérarchie administrative (`build_hierarchy`)
3. Composition des sections
4. Agrégation `section_status` + `sources`
5. Affichage progressif UI (résumé rapide, puis rafraîchissements sectionnels)

## Résultats partiels

- `success` — données présentes
- `partial` — sous-parties manquantes ou niveaux non couverts
- `unavailable` — référentiel absent / non branché (ex. Énergie)
- `error` — exception technique (loguée ; message métier en UI)

## Performance

- Composition backend **séquentielle résiliente** (évite les deadlocks psycopg2 multi-thread)
- Parallélisme UI via endpoints sectionnels + `AbortController`
- Réutilisation d’**une** instance Leaflet via `TerritorialSummary` dans le panneau TDT
- Accessibilité province : pas de recalcul massif `nearest_road` dans le jumeau (hint vers `/api/transport`)
- Objectif : résumé visible rapidement, sections secondaires non bloquantes

## Qualité et transparence

Chaque indicateur expose source / date / statut. Les données DEMO doivent être signalées (`demo: true`). Pas de mélange silencieux officiel / calculé / démo.

## Intégrations

| Point d’entrée | Comportement |
|----------------|--------------|
| TST | Action **Ouvrir le profil territorial** → `#territorial-twin/...` |
| Centre de Décision | Classement « Profil territorial », KPI territoriaux si sélection |
| Scénario `territory_priority` | Action jumeau |
| Salle de Pilotage DG | Clic province/territoire → résumé TDT |
| Hash | `#territorial-twin/{entity_type}/{entity_id}` (module Decision Workspace) |

## Limites v1

- Niveaux collectivite / groupement / localite : identité partielle
- Énergie, éducation, hydrographie, environnement : contrats prêts, non alimentés
- Timeline : événements pipeline / ouverture — persistance DB dédiée à venir
- Géométrie fine : réutilise TST, pas de nouveau store géométrique

## Feuille de route

1. Persistance timeline DB compatible PostGIS
2. Branching Éducation / Énergie / Économie via NDF
3. Enrichissement hiérarchie Master Registry multi-niveaux
4. Mode présentation EDVS « résumé jumeau » plein écran
5. Cache HTTP sections stables

## Fichiers clés

- `api/services/territorial_digital_twin_service.py`
- `api/routes/territorial_digital_twin.py`
- `dashboard/modules/shared/territorial-digital-twin/*`
- `tests/test_territorial_digital_twin.py`
- `tests/e2e/territorial-digital-twin.spec.js`
