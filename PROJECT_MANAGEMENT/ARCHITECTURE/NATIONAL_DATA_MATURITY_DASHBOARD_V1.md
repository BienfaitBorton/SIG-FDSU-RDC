# National Data Maturity & Readiness Dashboard — v1.0

**Moteur :** `ndm-1.0.0`  
**Doctrine :** Data First — aucun score inventé ; dimensions absentes exclues (jamais remplacées par 0).  
**Complément :** SDG Coverage Audit + Program Lifecycle Engine.

---

## 1. Objectif

Donner à la Direction FDSU une **vue institutionnelle de gouvernance des données** :

- quels référentiels sont solides ;
- lesquels restent incomplets ;
- quelles campagnes de collecte prioriser.

Cette vue mesure la **maturité documentaire / analytique**, pas le niveau de couverture radio.

---

## 2. Moteur

`api/services/data_maturity_engine.py`

Consomme en lecture seule :

- PostgreSQL admin / santé / télécom / routes ;
- NCI (`coverage_intelligence_service`) ;
- programmes JSON + NSME ;
- CCN DEMO ;
- audits `/api/sdg/coverage`, PLE, TIE, TI.

**Ne modifie aucun moteur métier.**

---

## 3. Dimensions (par référentiel)

Complétude · Qualité · Géolocalisation · Normalisation · Relations spatiales · Documentation · Traçabilité · Fraîcheur · Source officielle · Interopérabilité.

- Score domaine = **moyenne des dimensions non-null**.  
- Fraîcheur uniquement si mtime fichier connu.

---

## 4. Score national

Moyenne **pondérée** des domaines scorés (`DOMAIN_WEIGHTS`).

Bandes UI :

| Score | Libellé |
|------:|---------|
| ≥ 95 | Excellent |
| 90–95 | Très bon |
| 80–90 | Bon |
| 60–80 | À renforcer |
| < 60 | Prioritaire |

---

## 5. API

| Endpoint | Rôle |
|----------|------|
| `GET /api/data-maturity` | Dashboard + score national |
| `GET /api/data-maturity/details` | Détails domaines |
| `GET /api/data-maturity/roadmap` | Priorités + feuille de route |
| `GET /api/data-maturity/map` | GeoJSON maturité data (≠ radio) |
| `GET /api/data-maturity/report` | JSON rapport Direction |
| `GET /api/data-maturity/report.html` | Impression / PDF navigateur |

---

## 6. UI

Salle de Pilotage — carte **« Maturité des Données Nationales »** :

- score national ;
- tuiles par référentiel (clic → détail) ;
- données prioritaires (étoiles) ;
- roadmap court / moyen / long terme ;
- bouton Rapport Direction.

Fichiers : `dashboard/modules/shared/data-maturity/`

---

## 7. Priorités typiques (auto)

Générées depuis scores bas / absences :

- Sites 20 476 hors NSME ;
- CCN DEMO ≠ production ;
- Éducation / Énergie / Services publics / Économie non intégrés ;
- consolidation population / preuves de mise en service.

---

## 8. Cartographie

`/api/data-maturity/map` expose un FeatureCollection par province NCI avec `kind=data_maturity`.  
**Interdiction** de l’interpréter comme couverture réseau.

---

## 9. Export

La capacité `export_pdf` plateforme reste inactive (Zero Decorative Actions).  
Le rapport HTML imprimable remplace un faux PDF métier.

---

## 10. Tests

- `tests/test_data_maturity_engine.py`  
- `tests/e2e/data-maturity.spec.js`  
- Captures : `PROJECT_MANAGEMENT/ARCHITECTURE/captures/data-maturity/`

---

## 11. Limites

- Pondérations = règles documentées, non « magiques ».  
- Éducation / énergie : absents → score bas explicite.  
- Géométries admin sur la carte maturité : à joindre côté client (centroïdes non inventés).  
- Cache TTL 180 s.
