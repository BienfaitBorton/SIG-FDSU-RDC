# Territorial Data First Completeness Audit v1.0

**Date :** 2026-07-13  
**Cas de reproduction :** `#territorial-intelligence/TERRITOIRE-05-002` (DUNGU)  
**Mode :** `DATA_MODE=db`  
**Moteur :** `territorial-profile-1.0.0` → consommé par Territorial Intelligence / TDT

## Cause racine globale

Le profil TI construisait les KPI **sans interroger les référentiels PostGIS déjà peuplés** :

- Superficie / densité : hardcodées `unavailable` alors que `public.territoires.geom` et l’attribut KMZ `SURFACE` existaient.
- Groupements / localités : lecture de clés absentes du rapport KMZ, **sans** `public.groupements` / `public.localites`.
- Santé : filtre texte `territory_name` (souvent NULL) → **0 faux** ; intersection spatiale donne 121 établissements pour Dungu.
- Télécom / routes : non agrégés spatialement dans le profil TI.
- CCN : 0 DEMO affiché comme indisponible sans expliquer la recherche exécutée.

## Architecture retenue

```
territorial_entity_resolver.py  → identité canonique
territorial_profile_service.py  → composition blocs indépendants (Data First)
territorial_intelligence_service.build_territorial_profile()  → adapte le contrat UI
TDT / Decision / map / recommendations  → réutilisent le même profil
```

## Matrice indicateurs — TERRITOIRE-05-002 (DUNGU)

| Indicateur | Source attendue | Source actuelle | Requête | Avant | Après | Anomalie |
|---|---|---|---|---|---|---|
| Population | Recensement / NCI | NCI covered+uncovered | aggregates.json | 72943 (sites) partial | **129675** partial NCI | — |
| Superficie | PostGIS geom | `ST_Area(geography)` | public.territoires | indisponible | **33715,12 km²** operational | Fermée |
| Densité | pop/area | NCI / area | calcul | indisponible | **3,85** partial | Fermée |
| Collectivités | admin | public.collectivites | parent_id | — | **3** partial | Fermée |
| Groupements | admin | FK + ST_Within | public.groupements | indisponible | **5** partial | Fermée |
| Localités | admin | ST_Within prioritaire | public.localites | indisponible | **218** partial | Fermée |
| Santé | health.* | ST_Within | health.health_facilities | **0** faux | **121** partial | Fermée |
| Télécom | telecom.* | ST_Intersects | telecom.infrastructure | not_sourced | **22** operational | Fermée |
| Fibre | fibre linéaire | nœuds FTTX | telecom (fttx) | not_sourced | **2** nœuds | Partiel — pas de linéaire |
| Routes | transport.* | ST_Intersects | transport.routes | not_sourced | **19** / **159,11 km** | Fermée |
| Sites 40/300/20476 | programmes | JSON | sites_* | 0/4/88 | inchangé confirmed | — |
| CCN | production | DEMO only | demo_ccn.json | 0 unavailable | **0** operational + note DEMO | Qualifié |
| Éducation | — | absente | — | not_sourced | integration_pending | Absente réelle |
| Énergie / agriculture | — | absente | — | not_sourced | integration_pending | Absente réelle |

## Règles de rattachement administratif

1. territoire → collectivité → groupement → localité  
2. territoire → groupement direct  
3. territoire → localité directe  
4. collectivité → localité directe  
5. **ST_Within(geom, territoire.geom)** si géométrie disponible (prioritaire anti sous-comptage FK)

## Modules corrigés (provider partagé)

| Module | Indicateur | Donnée existe | Requête exécutée | État avant | État après | Source |
|---|---|---|---|---|---|---|
| TI / TDT | Superficie | Oui | Oui | indisponible | operational | public.territoires |
| TI / TDT | Groupements | Oui | Oui | indisponible | partial | public.groupements |
| TI / TDT | Localités | Oui | Oui | indisponible | partial | public.localites |
| TI / TDT | Santé | Oui | Oui (spatiale) | 0 ambigu | partial 121 | health.health_facilities |
| TI / TDT | Télécom | Oui | Oui | not_sourced | operational | telecom.infrastructure |
| TI / TDT | Fibre | Partiel | Oui (nœuds) | not_sourced | operational nœuds / pending linéaire | telecom FTTX |
| TI / TDT | Routes | Oui | Oui | not_sourced | operational | transport.routes |
| TI / TDT | CCN | DEMO only | Oui | 0 unavailable | 0 + note DEMO | demo_ccn |

## Anomalie globale

**« Profil territorial incomplet malgré référentiels existants »** — **CLOTURÉE** pour les référentiels déjà peuplés (admin, santé spatiale, télécom, routes, superficie, programmes).

Restent en **En cours d’intégration** (absents réels) : éducation, énergie, agriculture, backbone linéaire fibre, CCN production.

## Performances (ordre de grandeur, Dungu)

Composition profil ~2–4 s (PostGIS intersections + programmes + NCI). Blocs indépendants : une erreur Santé n’empêche pas Groupements.
