# Spatial Decision Graph (SDG) v2.0 — Analyse d’Impact Territorial

## Vision

Transformer la vue technique « Spatial Impact » en un **graphe décisionnel territorial explicable** pour le Directeur Général.

En moins d’une minute, la carte doit raconter :

1. pourquoi intervenir ;
2. quelles populations / localités sont concernées ;
3. quelles infrastructures influencent la décision ;
4. quelles relations portent le raisonnement ;
5. quels bénéfices sont attendus.

Le libellé UI est **Analyse d’Impact Territorial**.  
Le nom technique interne reste **Spatial Impact / Spatial Decision Graph (SDG)**.

## Principes

| Principe | Règle |
|---|---|
| Traçabilité | Toute arête provient exclusivement du **NSME** (`nsme_trace`) |
| Pas d’invention | Aucun lien artificiel, aucun score inventé |
| Contribution | Mappée depuis le **Decision Engine** si critère sourcé ; sinon proxy populationnel ou « Non chiffrée » |
| Carte | **Une** instance Leaflet DXL (`#dxl-map`) — mount / update / resize, pas de destroy inutile |
| Explicabilité | Panneau « Pourquoi ce site ? » + tooltips décideur (sans jargon SIG) |

## Architecture

```
NSME (matches) ──┐
                 ├──► spatial_decision_graph_service.build_graph()
Decision Engine ─┘              │
                                ▼
              GET /api/spatial-decision-graph/{type}/{id}
              GET /api/spatial-decision-graph/{type}/{id}/presentation
              GET /api/spatial-decision-graph/meta/categories
                                │
                                ▼
              SpatialDecisionGraph (dashboard JS)
                 ├─ nœuds / arêtes typées
                 ├─ animation progressive
                 ├─ mode Présentation DG
                 ├─ filtres + légende
                 └─ panneau « Pourquoi ce site ? »
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
   Territorial Digital Twin   Decision Case   Decision Workspace
```

Composition uniquement — pas de nouveau datastore.

## Catégories

| ID | Label UI | Couleur | Statut |
|---|---|---|---|
| `site` | Site étudié | ambre | actif (nœud central) |
| `population` | Population | bleu | actif |
| `localities` | Localités | bleu clair | actif |
| `health` | Santé | vert | actif |
| `telecom` | Télécommunications | cyan | actif |
| `roads` | Routes | orange | actif |
| `ccn` | CCN | violet | actif |
| `admin` | Services administratifs | gris | actif |
| `fdsu_sites` | Sites FDSU | brun | actif si relation NSME |
| `needs` | Besoins critiques | rouge | badge / relations mission |
| `education` | Éducation | teal | future |
| `energy` | Énergie | or | future |
| `markets` | Marchés | rose | future |

Chaque catégorie expose : couleur, symbole, style, légende, compteur.

## Types de relation

Styles dans `RELATION_STYLES` (service) — exemples :

| Relation NSME | Catégorie | Style |
|---|---|---|
| `SERVES_LOCALITY` | localités | trait bleu |
| `NEAR_HEALTH_FACILITY` | santé | trait vert |
| `NEAR_FIBER` / `NEAR_BACKBONE` | télécom | trait cyan |
| `NEAR_MAIN_ROAD` / `ROAD_ACCESSIBILITY` | routes | trait orange |
| `CONNECTS_CCN` | CCN | violet |
| `CANDIDATE_FOR_MISSION` | besoins | rouge tireté |

Chaque arête porte : type, couleur, épaisseur, dash, distance, confiance, source humaine, contribution, `why`, `nsme_trace`.

## Animation & présentation DG

Ordre des étapes (`PRESENTATION_STEPS`) :

1. Site sélectionné  
2. Population / localités / besoins  
3. Santé  
4. Télécommunications  
5. Routes  
6. CCN / admin / sites FDSU  
7. Recommandation (vue complète)

- Bouton **Présenter le raisonnement** (DXL + Salle DG / EDVS)  
- **Interrompre** à tout moment  
- Respect de `prefers-reduced-motion`  
- Transitions fluides, sans animation excessive  

## Panneau « Pourquoi ce site ? »

Blocs : Population, Accessibilité, Santé, Télécommunications, Services, Priorité, Investissements.  
Chacun : score, justification, source, statut.

## Filtres & légende

- Filtres case à cocher : Population, Localités, Santé, Télécom, Routes, CCN, Administration, Besoins, Sites FDSU  
- Légende : clic = activer/désactiver ; double-clic (ou Shift+Entrée) = isoler  
- Filtrage par opacité / retrait de couches Leaflet **sans** recréer la carte  

## Intégrations

| Destination | Action UI |
|---|---|
| Territorial Digital Twin | « Profil territorial » |
| Dossier de décision | « Ouvrir le dossier » |
| Decision Workspace | « Analyser » |
| Salle DG | « Présenter le raisonnement » |

## Performances

- Réutilisation de `#dxl-map` / `L.map` existant  
- Un `layerGroup` SDG dédié  
- Pas de superposition avec les segments génériques NSME (le calque DXL est vidé avant paint SDG)  
- Fetch parallèle graphe + présentation  
- FitBounds uniquement sur nœuds visibles  

## Accessibilité

- Boutons focusables, `aria-pressed` sur légende  
- Contraste des pastilles + contour sombre  
- Navigation clavier (Entrée / Espace / Shift+Entrée isoler)  
- `aria-live` sur l’étape de présentation  

## API

```
GET /api/spatial-decision-graph/meta/categories
GET /api/spatial-decision-graph/{asset_type}/{asset_id}
GET /api/spatial-decision-graph/{asset_type}/{asset_id}/presentation
```

Query optionnelle : `program_code`.

## Composants

| Couche | Fichier |
|---|---|
| Service | `api/services/spatial_decision_graph_service.py` |
| Routes | `api/routes/spatial_decision_graph.py` |
| UI | `dashboard/modules/shared/spatial-decision-graph/` |
| DXL | `dashboard/modules/decision-experience/decision-experience.js` |
| EDVS | `dashboard/modules/shared/executive-dashboard/executive-dashboard.js` |
| E2E | `tests/e2e/spatial-decision-graph.spec.js` |

## Feuille de route

| Version | Contenu |
|---|---|
| **v2.0** | Graphe typé NSME, animation, présentation DG, panneau, filtres, légende, TDT/Workspace |
| v2.1 | Catégories Éducation / Énergie / Marchés dès référentiels NSME |
| v2.2 | Contribution Decision Engine nativement par relation (sans proxy) |
| v2.3 | Export scénario présentation (PDF/PPT quand capacités réelles) |
| v2.4 | Mode multi-sites comparatif pour arbitrage DG |

## Tests

Voir `tests/e2e/spatial-decision-graph.spec.js` :

- API graphe / présentation / meta  
- Shell UI + légende + filtres  
- Animation + interruption  
- Navigation TDT / Workspace / dossier  
- Bouton Salle DG  
- Absence d’erreur JS / double Leaflet  
