# Architecture métier FDSU — SIG-FDSU RDC

Ce dossier constitue la **couche métier externalisée** du moteur décisionnel FDSU. Toute règle, programme, critère ou indicateur doit être lu depuis ces fichiers — **jamais codé en dur** dans le JavaScript, l'API ou les modules UI.

Les documents stratégiques source restent dans `data/strategic/` ; cette couche en dérive la structure opérationnelle sans en modifier le contenu binaire.

## Rôle dans la plateforme

Le SIG-FDSU évolue d'un SIG générique vers une **plateforme nationale de planification, de suivi, d'analyse et d'aide à la décision** du Fonds de Développement du Service Universel (FDSU).

L'organisation pivot est le **programme FDSU**, et non une simple liste de sites.

## Fichiers du référentiel

| Fichier | Rôle |
| --- | --- |
| `fdsu_programs.json` | Catalogue extensible des programmes FDSU (Sites 40, Sites 300, CCN, Subventions, secteurs, etc.) avec statuts et métadonnées. |
| `decision_rules.json` | Critères décisionnels issus de la stratégie FDSU (classe stratégique, déficit de couverture, population, CAPEX, etc.) — référentiel sans calcul. |
| `priority_matrix.json` | Niveaux de priorité (critique → basse) et typologies de matrices (sites, CCN, subventions, partenaires). |
| `kpi_catalog.json` | Indicateurs de performance organisés par programme pour les tableaux de bord et rapports. |
| `scoring_rules.json` | Familles de scores préparées (Site, CCN, Projet, Province, Zone, Partenaire) — structure sans formules. |
| `ccn_model.json` | Typologie des CCN (Social, Éducatif, Administratif, Entrepreneurial, Mixte) et indicateurs futurs. |
| `subsidy_rules.json` | Critères, éligibilité, types, phases et indicateurs du programme de subventions. |

Chaque fichier JSON inclut un bloc `_meta` (version, description, sources, date).

## Accès depuis l'application

Les fichiers sont servis en lecture seule par le serveur dashboard :

```
/business/<nom_fichier>.json  →  data/business/<nom_fichier>.json
```

Exemple côté module :

```javascript
fetch('/business/fdsu_programs.json').then((r) => r.json());
```

## Utilisation prévue — prochains sprints

### Sprint scoring et priorisation

- Charger `decision_rules.json` et `scoring_rules.json` pour implémenter le calcul des scores.
- Appliquer les seuils de `priority_matrix.json` aux entités géolocalisées.
- Importer les données tabulaires de `data/strategic/matrice_priorisation_300_sites.xlsx` vers une structure normalisée référencée par `priority_matrix.json`.

### Sprint programmes et KPI

- Lier chaque entité (site, CCN, projet) à un `program_id` de `fdsu_programs.json`.
- Alimenter les tableaux de bord depuis `kpi_catalog.json` via l'API ou des agrégations batch.

### Sprint CCN et subventions

- Instancier les fiches CCN selon `ccn_model.json`.
- Piloter les workflows de subvention depuis `subsidy_rules.json` (phases, éligibilité, indicateurs).

### Sprint centre de décision

- Remplacer les placeholders (KPI statiques, listes fictives) par des lectures dynamiques depuis `data/business/`.
- Brancher les onglets Priorisation, Analyse multicritère et Simulations sur les rule sets et familles de scores.

## Principes

1. **Externalisation** — Toute évolution métier passe par un fichier JSON versionné dans ce dossier.
2. **Extensibilité** — Nouveaux programmes, critères ou KPI ajoutés sans refactor du code.
3. **Traçabilité** — Chaque règle référence ses documents source dans `_meta` ou `source_documents`.
4. **Progressivité** — À ce stade : référentiel + affichage informatif ; calcul et scoring dans les sprints suivants.

## Relation avec `data/strategic/`

| Couche | Contenu |
| --- | --- |
| `data/strategic/` | Documents officiels bruts (DOCX, XLSX) — archive normative. |
| `data/business/` | Modèle opérationnel structuré dérivé de ces documents — moteur décisionnel. |
