# Territorial Explainability & Drill-down v1.0

**Statut :** livré (sans commit)  
**Date :** 2026-07-13  
**Moteur :** `territorial-explainability-1.0.0`  
**Source unique :** `territorial_profile_service` + `territorial_explainability_service` (consommé via le profil TI)

## Objectif

Chaque indicateur territorial agrégé doit répondre à la chaîne :

1. Combien ?  
2. Lesquels ?  
3. Où ?  
4. Quelles caractéristiques ?  
5. Pourquoi est-ce important ?  
6. Quelle action recommander ?

Deux niveaux de lecture :

- **Décideur** — cartes de synthèse (`explainability` dans le profil)  
- **Expert** — drawer détail paginé (`/details/{domain}`) + focus carte

Aucun nouveau référentiel. Aucune invention d’attributs, technologies ou impacts.

## Contrat commun

```json
{
  "domain": "telecom",
  "domain_label": "Télécommunications",
  "summary": {
    "count": 22,
    "status": "operational|partial|integration_pending|integration_anomaly|demonstration",
    "source": "...",
    "confidence": "high|medium|low",
    "updated_at": "...",
    "headline": "...",
    "business_impact": "...",
    "recommendation": "..."
  },
  "breakdown": [{ "label": "…", "count": 0, "display": "…" }],
  "top_items": [{ "id": "…", "name": "…", "coordinates": {}, "source": "…", "confidence": "…" }],
  "quality": {},
  "pagination": { "page": 1, "page_size": 50, "total": 22, "pages": 1 },
  "actions": [
    { "id": "details", "label": "Voir les …" },
    { "id": "map", "label": "Afficher sur la carte" },
    { "id": "impact", "label": "Analyser l’impact" }
  ],
  "technical": { "method": "ST_Intersects / ST_Within …" }
}
```

Extras domaine possibles : `operators`, `technologies`, `typology`, `named_axes`, `accessibility_label`, `limit_note`.

## Endpoints

| Méthode | Chemin | Rôle |
|---------|--------|------|
| GET | `/api/territorial-intelligence/territories/{id}` | Profil + `explainability` embarquée |
| GET | `/api/territorial-intelligence/territories/{id}/explainability` | Bundle décideur |
| GET | `/api/territorial-intelligence/territories/{id}/details/{domain}` | Liste expert paginée |

Domaines : `telecom`, `fiber`, `health`, `routes`, `sites_20476`, `sites_300`, `sites_40`, `ccn`, `localites`, `groupements`, `collectivites`.

## Sources (Data First)

| Domaine | Source | Méthode spatiale |
|---------|--------|------------------|
| Télécom | `telecom.infrastructure` (+ `telecom.operators`) | `ST_Intersects` |
| Fibre | FTTX dans `telecom.infrastructure` + `telecom.network_lines` | `ST_Intersects` |
| Santé | `health.health_facilities` | `ST_Within` |
| Routes | couche routes du profil / PostGIS | intersection territoire |
| Programmes | jeux programmes FDSU existants | filtre territoire |
| CCN | API CCN DEMO | explicité comme démonstration |
| Administratif | `public.collectivites` / `groupements` / `localites` | rattachement existant |

## Règles de faux zéro

Un `0` n’est affiché que si la recherche a été exécutée, le référentiel existe et le résultat est réellement nul.

Sinon : **Non calculable**, **Non renseigné**, **En cours d’intégration**, **Anomalie d’intégration**, **Données insuffisantes**.

Santé : si tous les `facility_type_code` sont `OTHER` / absents, HGR / CS / PS → **Non calculable** (pas `0`).

Fibre : ne pas présenter N nœuds FTTX comme N réseaux complets ; `limit_note` si pas de table linéaire dédiée hors `network_lines`.

## UX

- Cartes `.ti-explain-card` dans Intelligence territoriale  
- Drawer `#ti-detail-drawer` : recherche, filtre, pagination, détail technique, clic ligne → focus Leaflet  
- Une seule instance Leaflet (`tiState.map` + `detailLayer`)  
- Normalisation métier : `high` → Élevée, `medium` → Moyenne, `low` → Faible, etc.  
- Codes internes uniquement dans **Détail technique**

## Modules consommateurs

Tous doivent consommer la même structure (profil / explainability) :

- Intelligence territoriale (TI)  
- Territorial Digital Twin (TDT)  
- Territorial Summary (TST)  
- Salle DG / Centre de Décision / exports (via API partagée)

## Limites

- Technologies télécom : uniquement attributs présents (`Technologie` / `technology`) — sinon « Non renseignée »  
- Impacts métier : dérivés uniquement de comptes / opérateurs / typologies observés  
- CCN : jeu DEMO  
- Pas d’export CSV dédié si capacité absente (pas de bouton décoratif)

## Extensions futures

- Export CSV/GeoJSON expert  
- Nearest fibre / nearest health consolidés dans le contrat  
- Mission terrain depuis la recommandation DG  
- Harmonisation typologie santé (HGR/CS/PS) côté référentiel

## Fichiers clés

- `api/services/territorial_explainability_service.py`  
- `api/services/territorial_profile_service.py` / `territorial_intelligence_service.py`  
- `api/routes/territorial_intelligence.py`  
- `dashboard/modules/territorial-intelligence/territorial-intelligence.js`  
- `dashboard/modules/territorial-intelligence/territorial-intelligence.css`  
- `tests/test_territorial_explainability.py`  
- `tests/e2e/territorial-explainability.spec.js`
