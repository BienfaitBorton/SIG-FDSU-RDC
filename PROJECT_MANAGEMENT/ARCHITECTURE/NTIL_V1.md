# NTIL v1.0 — National Terminology Intelligence Layer

## Architecture

Le NTIL est la couche nationale de gouvernance terminologique du SIG-FDSU RDC. Le DNAI reste responsable de la normalisation; NTIL gouverne les connaissances, leur qualité, leur histoire et leur publication.

```text
National Terminology Intelligence Layer
├── DNAI Core
├── National Terminology Registry (NTR)
├── Discovery Engine
├── Validation Workflow
├── Terminology Quality Engine (TQE)
├── Version Manager
├── Analytics
└── APIs et Dashboard
```

Le pipeline métier reste `texte brut → DNAI → texte normalisé → NSCE → classification`. NTIL observe et gouverne ce pipeline sans modifier les données sources.

## National Terminology Registry

Le registre officiel est `data/business/national_terminology_registry.json`. Chaque fiche conserve identifiant, terme original et normalisé, type, catégorie, famille, expansion éventuelle, statut, confiance, référentiels, occurrences, dates, validation, source, version, règle, contexte, justification et commentaires.

Une expansion absente reste `null`. `EDAC`, `ISGEA`, `IS` et `ISIPA` sont enregistrés sans expansion automatique. Le registre contient aussi des instantanés de qualité par référentiel et des groupes de synonymes nationaux.

## Gouvernance et workflow

Les états autorisés sont :

`DÉCOUVERT → EN ANALYSE → EN VALIDATION → VALIDÉ → PUBLIÉ → DÉPRÉCIÉ`

Le Discovery Engine crée uniquement des propositions. Le passage à `VALIDÉ` exige une décision humaine sourcée; `PUBLIÉ` rend la connaissance utilisable par le DNAI. Toute évolution ajoute une entrée d’historique avec version, date, auteur, origine, justification et changement.

## Terminology Quality Engine

Le TQE calcule : taux de normalisation, reconnaissance, ambiguïtés résolues, termes inconnus, validation, confiance moyenne et qualité par référentiel. Le `Terminology Quality Score` est la moyenne de ces dimensions, le taux d’inconnus étant inversé. Le score mesure la maturité terminologique, pas la qualité terrain du référentiel.

Les instantanés conservent la méthode et le hash de la source afin de rendre chaque mesure reproductible et explicable.

## Synonymes et contextes

Un groupe de synonymes associe plusieurs graphies à une famille canonique sans effacer le texte original. Les familles initiales couvrent Santé, Éducation et Administration.

Une même forme peut avoir plusieurs fiches contextuelles. Ainsi `CS` est `COMPLEXE SCOLAIRE` dans le contexte CENI par défaut et `CENTRE DE SANTÉ` lorsqu’un contexte sanitaire explicite est présent.

## API

- `GET /api/ntil/statistics`
- `GET /api/ntil/registry`
- `GET /api/ntil/term/{id}`
- `GET /api/ntil/discoveries`
- `GET /api/ntil/quality`
- `GET /api/ntil/history`
- `GET /api/ntil/families`
- `GET /api/ntil/dashboard`

Les listes du registre acceptent recherche, statut, famille, référentiel et pagination.

## Dashboard

La route `#ntil`, présentée comme `Intelligence · Terminologie Nationale`, affiche KPI, score global, qualité par référentiel, familles, découvertes, validations, historique, recherche avancée et couverture nationale. Les codes internes restent dans les contrats API; l’interface privilégie les libellés institutionnels.

## Stratégie d’évolution

1. Générer un instantané de découverte immuable à chaque import.
2. Ajouter une identité de validateur et une preuve documentaire aux transitions.
3. Publier les familles Télécommunications et Énergie après audit des référentiels concernés.
4. Comparer automatiquement les scores et populations entre versions.
5. Exposer ultérieurement des commandes de transition protégées par rôle, sans publication automatique.
