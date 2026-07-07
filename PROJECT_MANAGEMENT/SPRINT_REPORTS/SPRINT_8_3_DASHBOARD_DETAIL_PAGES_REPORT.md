# Sprint 8.3 — Pages analytiques dédiées par indicateur

**Date :** 7 juillet 2026  
**Branche :** `feature/smart-map-interactions`  
**Statut :** ✅ Implémenté — **21/21 tests Playwright passants**

---

## 1. Fichiers modifiés

| Fichier | Changements |
|---------|-------------|
| `dashboard/index.html` | Carte KPI Zones FDSU, vues `#dashboard-main-view` / `#dashboard-detail-view`, layout carte + liste |
| `dashboard/app.js` | `dashboardViewState`, pages analytiques, redirection KPI → pages dédiées |
| `dashboard/styles.css` | Styles pages analytiques, liste interactive, layout responsive |
| `tests/e2e/smart-map.spec.js` | 5 nouveaux tests pages analytiques |

---

## 2. Comportement obtenu

### Tableau de bord principal (`#dashboard-main-view`)

- **Ordre KPI :** Zones FDSU (5) → Provinces → Territoires → Collectivités → Groupements → Localités → Sites FDSU → Missions → Utilisateurs
- Carte nationale hiérarchique **conservée** sous les KPI
- **Plus de workbench superposé** au clic KPI

### Pages analytiques (`#dashboard-detail-view`)

Chaque clic KPI ouvre une **vue interne pleine page** (sans overlay) :

| Indicateur | Page | Contenu |
|------------|------|---------|
| Zones FDSU | `zones` | Carte 5 zones colorées, liste avec stats, clic zone → provinces |
| Provinces | `provinces` | Carte 26 provinces, liste, fiche stats |
| Territoires | `territories` | Carte territoires, filtre province |
| Collectivités | `collectivities` | Carte + filtres province/territoire |
| Groupements | `groupements` | Carte points/polygones + filtres |
| Localités | `localities` | Carte points + filtres hiérarchiques |
| Sites FDSU | `sites` | Carte sites + filtres |
| Missions | `missions` | Carte missions + filtres |

**Chaque page inclut :**
- Bouton **Retour au tableau de bord**
- Carte Leaflet (`#dashboard-detail-map`)
- Liste interactive (`#dashboard-detail-list`)
- Panneau statistiques contextuel (`#dashboard-detail-stats`)
- Recherche + filtres province/territoire (selon page)

### État de navigation

```javascript
dashboardViewState = {
  page: 'main' | 'detail',
  detailType: 'zones' | 'provinces' | 'territories' | ...,
  selectedEntityId, selectedZoneCode, filters, rows, features, map
}
```

### Compatibilité préservée

- Module **Cartographie libre** inchangé
- **Carte nationale hiérarchique** visible uniquement sur la vue principale
- Recherche globale / raccourcis zones → pages analytiques (plus workbench)
- Données via `fetchPlatformLayerData()` (json-reports / PostGIS)

---

## 3. Tests Playwright

**Commande :** `npx playwright test --config playwright.config.js`

| Suite | Tests |
|-------|-------|
| Smart Map (régression) | 10 ✅ |
| Cartographie libre | 1 ✅ |
| Cartographie nationale | 5 ✅ |
| **Pages analytiques dashboard** | **5 ✅** |

**Total : 21 passed (≈ 1,6 min)**

Nouveaux tests :
1. Clic Zones FDSU → page dédiée sans superposition
2. Clic Provinces → carte + liste
3. Clic Territoires → carte + filtre province
4. Retour au tableau de bord
5. Aucun workbench visible après clic KPI

---

## 4. Limites connues

1. **Utilisateurs** — Redirige toujours vers le module Utilisateurs (pas de page analytique dédiée).
2. **Pagination** — Liste limitée à 300 éléments affichés (localités volumineuses).
3. **Géométries** — Entités sans géométrie visibles en liste mais absentes de la carte.
4. **Workbench legacy** — Conservé en DOM masqué pour compatibilité code existant, non utilisé par les KPI.
5. **Panneau droit dashboard** — Reste visible sur les pages analytiques (espace réduit sur petits écrans).

---

## 5. Recommandation de commit

```
feat(dashboard): add dedicated analytic pages for KPI indicators
```

---

## 6. Pistes sprint suivant

1. Pagination virtualisée pour localités (26k+).
2. Export CSV/Excel depuis chaque page analytique.
3. Lien « Ouvrir dans Cartographie » depuis une entité sélectionnée.
4. Masquer le panneau droit en mode page analytique pour plus d'espace carte.
5. Page analytique Utilisateurs intégrée au dashboard.
