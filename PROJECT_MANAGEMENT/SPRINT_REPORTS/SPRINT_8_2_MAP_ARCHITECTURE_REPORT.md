# Sprint 8.2 — Séparation Cartographie libre / Carte nationale hiérarchique

**Date :** 7 juillet 2026  
**Branche :** `feature/smart-map-interactions`  
**Statut :** ✅ Implémenté — **16/16 tests Playwright passants**

---

## 1. Fichiers modifiés

| Fichier | Changements |
|---------|-------------|
| `dashboard/app.js` | `nationalMapState`, module carte nationale, restauration SIG libre cartographie |
| `dashboard/index.html` | Carte Leaflet dashboard (`#dashboard-national-map`), retrait bouton Retour cartographie |
| `dashboard/styles.css` | Styles `.dashboard-national-map`, shell navigation nationale |
| `tests/e2e/smart-map.spec.js` | Tests séparés cartographie libre + carte nationale dashboard |

---

## 2. Architecture obtenue

### Module Cartographie (SIG libre)

- Couches cochées affichées **librement** et **superposables** (provinces + zones, etc.).
- Plus de filtrage hiérarchique exclusif au clic.
- `refreshVisibleCartographyLayer()` affiche **toutes** les entités de la couche active.
- `renderSynchronizedLayerList()` liste les entités des **couches visibles**.
- Clic carte / liste : sélection, zoom, popup, panneau latéral — **sans drill-down exclusif**.
- Bouton « Retour vue nationale » : recentre sur la RDC (plus de navigation hiérarchique).

### Tableau de bord → Cartographie nationale

- Placeholder remplacé par **carte Leaflet réelle** (`#dashboard-national-map`).
- État dédié : `nationalMapState` (indépendant de `cartographyState`).
- Données : `fetchPlatformLayerData()` (json-reports ou PostGIS via API).
- **Navigation hiérarchique exclusive** (Sprint 8.1 réutilisé) :
  - RDC → provinces → territoires → collectivités → groupements → localités → sites
  - Fil d’Ariane `#dashboard-map-breadcrumb`
  - Boutons Retour / Vue nationale
  - Liste synchronisée `#dashboard-map-synchronized-list`
  - Message « Aucune subdivision disponible pour ce niveau. »

### Fonctions clés (carte nationale)

| Fonction | Rôle |
|----------|------|
| `initializeNationalMapModule()` | Init Leaflet dashboard + chargement provinces |
| `renderNationalContextMap()` | Affichage exclusif contexte + enfants |
| `activateNationalSpatialContext()` | Drill-down au clic |
| `isWithinHierarchyContext()` | Filtre exclusif (national uniquement) |
| `resetDashboardNationalView()` | Retour vue RDC |
| `goBackNationalContext()` | Remonte d’un niveau |

---

## 3. Tests Playwright

**Commande :** `npx playwright test --config playwright.config.js`

| Suite | Tests | Résultat |
|-------|-------|----------|
| Smart Map (régression) | 10 | ✅ |
| Module Cartographie libre | 1 | ✅ |
| Cartographie nationale (dashboard) | 5 | ✅ |

**Total : 16 passed (≈ 1,2 min)**

---

## 4. Limites connues

1. **Deux instances Leaflet** — Cartographie et dashboard chargent chacun leurs données (cache partiel via `platformState.dataPromises`).
2. **Zones FDSU** — Couche synthétique disponible en cartographie libre ; absente de la carte nationale hiérarchique (focus administratif).
3. **Géométries partielles** — Certaines couches (territoires) peuvent être attributaires seules selon json-reports.
4. **Compteurs dashboard** — KPI du bloc carte nationale non encore liés au contexte hiérarchique (stats sidebar existantes inchangées).

---

## 5. Recommandation de commit

```
feat(dashboard): split free cartography from hierarchical national map
```

---

## 6. Pistes sprint suivant

1. Synchroniser les compteurs KPI du dashboard avec `nationalMapState.spatialContext`.
2. Partager un cache features entre `cartographyState` et `nationalMapState` pour éviter double chargement.
3. Lien « Ouvrir dans Cartographie » depuis la carte nationale avec entité présélectionnée.
4. Deep linking URL pour contexte national (`#dashboard?context=province/KASAI`).
