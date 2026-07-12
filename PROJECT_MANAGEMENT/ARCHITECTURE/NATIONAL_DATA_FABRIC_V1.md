# National Data Fabric (NDF) v1.0

**Branche** : `feature/smart-map-interactions`  
**Statut** : livrable pré-commit — **aucun commit automatique**  
**API** : `/api/national-data-fabric`

## Principes

1. **Gouvernance, pas duplication** — le NDF catalogue les référentiels ; il ne remplace pas Master Registry, Knowledge Hub, NCI, TST, CCN, etc.
2. **Contrat commun** — tout référentiel (actif ou futur) documente le même modèle de métadonnées.
3. **Extensibilité** — un nouveau jeu (Transport, Énergie, …) s’enregistre via `POST /registries` dans `data/ndf/registries_extensions.json` sans modifier le cœur.
4. **Honnêteté des mesures** — indicateurs qualité absents → « Données insuffisantes », jamais de score inventé.
5. **Pas d’UI principale** — le NDF est une couche API + métadonnées consommée par TST, Decision Engine, Knowledge Hub, NSME.

## Architecture

```
National Data Fabric
├── data/ndf/registries.json           # catalogue cœur
├── data/ndf/registries_extensions.json # enregistrements dynamiques
├── data/ndf/relations.json            # graphe documenté
├── api/services/national_data_fabric_service.py
└── api/routes/national_data_fabric.py  → /api/national-data-fabric
         │
         ├── inventaire / métadonnées / recherche
         ├── qualité (5 dimensions)
         ├── statistiques / relations
         └── consumers (TST, Decision, KH, NSME)
```

## Modèle commun (référentiel)

| Champ | Rôle |
|-------|------|
| id, name, category, description | Identité |
| owner, official_source, update_frequency, version | Gouvernance |
| quality_baseline, confidence_level | Confiance |
| geographic_coverage, geometry_type, crs | Spatial |
| related_registry_ids, apis, metrics_exposed | Intégration |
| aggregation_rules, update_history | Traçabilité |

## Indicateurs qualité

`completeness` · `freshness` · `coherence` · `geometry` · `precision`

Sources réelles branchées lorsque disponibles (ex. NCI `quality_report`, couches `/map/layers`, stats Master Registry).

## Relations

Documentées dans `relations.json` (`spatial_contains`, `serves`, `prioritizes`, `informs`, `overlaps`, `planned_link`).  
Elles **n’imposent pas** la présence des données cibles.

## Cycle de vie des données

1. **Planifié** — entrée `status: planned` dans le catalogue cœur.  
2. **Enregistrement** — `POST /registries` + dépôt des données + API métier.  
3. **Actif** — métadonnées mises à jour, qualité branchée.  
4. **Consommation** — TST / Decision / KH / NSME interrogent le NDF.

## Stratégie d’intégration d’un nouveau référentiel

1. Déposer les données (ex. `data/sectoral/transport/`).  
2. Créer le service/API métier du référentiel.  
3. `POST /api/national-data-fabric/registries` avec le modèle commun.  
4. Ajouter les relations dans `relations.json` (ou extension future).  
5. **Sans** modifier l’architecture générale ni les moteurs existants.

## API

| Méthode | Route | Rôle |
|---------|-------|------|
| GET | `/manifest` | Manifeste NDF |
| GET | `/registries` | Inventaire |
| GET | `/registries/{id}` | Métadonnées + qualité + relations |
| POST | `/registries` | Enregistrement extension |
| GET | `/registries/{id}/quality` | Qualité unitaire |
| GET | `/quality` | Vue qualité globale |
| GET | `/statistics` | Stats globales |
| GET | `/search?q=` | Recherche |
| GET | `/relations` | Graphe de relations |
| GET | `/consumers` | Compatibilité moteurs |

## Feuille de route

| Phase | Contenu |
|-------|---------|
| v1.0 | Catalogue + relations + API + qualité NCI/admin |
| v1.1 | Branche qualité telecom/health/CCN depuis leurs APIs |
| v1.2 | Intégration réelle Transport / Énergie / Éducation |
| v1.3 | Hooks UI optionnels (panneau métadonnées dans Decision Center) |

## Limites

- Pas de stockage métier dans le NDF.  
- Qualité encore partielle pour certains référentiels actifs (`composed` / `structure_only`).  
- Relations planifiées sans données sous-jacentes.
