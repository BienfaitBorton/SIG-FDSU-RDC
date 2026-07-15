# Territorial Intelligence Multi-Scale v1

**Statut :** opérationnel (v1)  
**Moteur :** `ti-multiscale-1.0.0`  
**Registre symbologie :** `data/cartography/symbology_registry_v1.json`  
**Doctrine :** Data First / No Black Box — aucune population, rattachement ou taux inventé.

---

## 1. Objectif

Faire évoluer Territorial Intelligence d’une synthèse **uniquement territoriale** vers une intelligence administrative multi-échelle :

```
RDC
→ Province
→ Territoire
→ Secteur / Chefferie / Cité / Collectivité
→ Groupement
→ Localité
→ Site
```

Le parcours s’adapte à la hiérarchie réelle (`parent_id` PostGIS). Un niveau absent n’est pas simulé.

---

## 2. Hiérarchie et identifiants

| Niveau | Exemple d’ID | Source |
|--------|--------------|--------|
| Province | `PROVINCE-66` ou `PROVINCE-Haut-Uele` | `public.provinces` |
| Territoire | `TERRITOIRE-05-002` | Master Registry + `public.territoires` |
| Collectivité | `COLLECTIVITE-328` | `public.collectivites` (`type` = Chefferie / Secteur / …) |
| Groupement | `GROUPEMENT-783` | `public.groupements` |
| Localité | `LOCALITE-12022` | `public.localites` |

Routes UI : `#territorial-intelligence/{entity_id}`  
API : `GET /api/territorial-intelligence/entities/{entity_id}`

---

## 3. Contrat partagé

Chaque entité renvoie le même noyau :

- `entity` (type, id, name, parent, hierarchy, geometry/centroid, sources)
- `breadcrumb`
- `population` / `coverage` (value, source, method, confidence, double_counting_guard, note)
- `administrative.children`
- `map` + `map_payload` (GeoJSON + légende dynamique)
- `sources`, `confidence`, `explainability`
- domaines métier (programs, health, telecom, routes, score) selon disponibilité

Le frontend **ne recalcule pas** les KPI.

---

## 4. Population et couverture

### Sources

1. `data/coverage/aggregates.json` — agrégats province / territoire (NCI)
2. `data/coverage/localities_covered.jsonl` / `localities_uncovered.jsonl` — populations ponctuelles
3. `public.localites` — référentiel administratif (**pas** de colonne population)

### Priorité

1. Agrégat NCI lié directement au territoire / province  
2. Somme NCI spatiale dans la géométrie de l’entité (collectivité / groupement / localité)  
3. Indisponible déclaré si aucune correspondance fiable

### Garde anti double-comptage

- Ensembles **couvert** et **non couvert** exclusifs  
- Dédupe par `id` NCI  
- Total = covered + uncovered uniquement lorsque les deux sont présents  
- Taux = covered / (covered + uncovered) seulement si compatibles  
- Mode spatial → statut **`partial`**, note explicite (« pas un recensement officiel »)

### Anomalie documentée

`public.localites` n’expose pas de population officielle. Les populations multi-échelle infra-territoriales reposent donc sur le NCI spatial filtré par territoire parent.

---

## 5. Audit légende (avant / après)

| Domaine | Type géométrique | Couleur carte | Icône | Couleur légende (avant) | Cohérent ? |
|---------|------------------|---------------|-------|-------------------------|------------|
| territoire | polygon | `#38bdf8` | poly | poly OK | oui |
| collectivité | polygon | `#67e8f9` | poly | absente | **corrigé** |
| groupement | point | `#eab308` | circle | absente / générique | **corrigé** |
| localité | point | `#64748b` | circle | absente | **corrigé** |
| site FDSU | point | `#f59e0b` | circle | ambre OK | oui |
| santé | point | `#10b981` | circle | vert OK | oui |
| télécommunications | point | `#0ea5e9` cyan | circle | **violet générique** | **corrigé** |
| fibre nœud | point | `#db2777` | circle | **violet générique** | **corrigé** |
| fibre tronçon | line | `#db2777` | line | **violet générique** | **corrigé** |
| routes | line | `#94a3b8` | line | **violet générique** | **corrigé** |
| CCN | point | `#8b5cf6` | circle | violet OK | oui |
| localité couverte | point | `#22c55e` | circle | (registre prêt, couche carte à brancher) | partiel |
| localité non couverte | point | `#ef4444` | circle | (registre prêt, couche carte à brancher) | partiel |

Cause racine : `UxPremium.mountMapLegend` regroupait « Télécom / Fibre / Routes » sous `.is-ccn` (violet), indépendamment de `LAYER_STYLES`.

## 6. Symbologie unique

Fichier : `data/cartography/symbology_registry_v1.json`  
Service : `api/services/cartography_symbology_registry.py`  
Endpoint : `GET /api/territorial-intelligence/symbology`

**Règle :** carte, légende, popups et filtres consomment le même registre.

Domaines distincts (plus de regroupement « Télécom / Fibre / Routes ») :

| Domaine | Couleur carte | Géométrie |
|---------|---------------|-----------|
| territory_boundary | `#38bdf8` | polygone |
| collectivite | `#67e8f9` | polygone |
| groupement | `#eab308` | point |
| locality | `#64748b` | point |
| locality_covered | `#22c55e` | point |
| locality_uncovered | `#ef4444` | point |
| site_fdsu | `#f59e0b` | point |
| health | `#10b981` | point |
| telecom | `#0ea5e9` | point |
| fiber | `#db2777` | point |
| fiber_line | `#db2777` | ligne |
| route | `#94a3b8` | ligne |
| ccn | `#8b5cf6` | point |

La légende est **dynamique** : uniquement les couches avec `count > 0` dans le payload `/map`.

---

## 7. Drill-down UI

- Fil d’Ariane cliquable  
- Liste des enfants administratifs  
- Clic carte sur collectivité / groupement / localité  
- Hash mis à jour sans rechargement complet  
- Légende et KPI recalculés depuis l’API

---

## 8. Limites v1

- Enrichissement explicabilité domaine (cartes telecom/santé détaillées) reste centré territoire  
- Agrégation spatiale NCI peut être partielle (points hors géométrie, noms sans coordonnées)  
- Province via slug texte : résolution ILIKE, privilégier `PROVINCE-{db_id}`  
- Sites FDSU au niveau collectivité : comptage spatial non encore généralisé (territoire via programmes)

---

## 9. Tests

- Backend : `tests/test_territorial_multiscale.py`  
- Playwright : `tests/e2e/territorial-intelligence-multiscale.spec.js`  
- Captures : `PROJECT_MANAGEMENT/ARCHITECTURE/captures/territorial-intelligence-multiscale/`  
- Intégrité : ne pas committer données runtime / KMZ générés

---

## 10. Progression future

- Couches localités couvertes / non couvertes sur la carte TI (kinds dédiés)  
- Lien direct Localité → dossier de décision site  
- Matrice de correspondance NCI ↔ `public.localites` (FK) pour hausser la confiance  
- Zoom / atténuation voisinage plus fine par niveau
