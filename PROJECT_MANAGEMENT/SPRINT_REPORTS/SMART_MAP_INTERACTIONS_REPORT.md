# SIG-FDSU RDC - Sprint smart map interactions

Date : 2026-07-06

## Architecture

La cartographie reste integree au dashboard existant et ajoute une couche d'interactions decisionnelles autour de Leaflet :

- `rdcBoundary` : contour national RDC toujours visible ;
- `FDSU_LAYER_STACK_ORDER` : ordre professionnel des couches ;
- `spatialContext` : entite administrative active ;
- `spatialContextTrail` : fil d'Ariane cliquable ;
- `refreshVisibleCartographyLayer()` : filtrage spatial des couches cochees ;
- `renderSynchronizedLayerList()` : liste synchronisee carte/liste ;
- `computeSpatialContextStats()` : statistiques contextuelles calculees depuis les referentiels charges.

Les donnees restent exclusivement issues du SIG-FDSU RDC et des fichiers locaux du depot. Aucun code, logo, donnee ou ressource externe n'a ete copie.

## Logique

- Demarrage : contour RDC uniquement.
- Couches : chaque case reste independante.
- Survol carte : infobulle metier avec nom, type, codes, zone et compteurs.
- Clic carte : zoom, selection lumineuse, contexte spatial, panneau lateral, fiche disponible.
- Survol liste : surbrillance de l'entite sur la carte.
- Clic liste : zoom et selection carte.
- Double clic liste : ouverture de la fiche complete.
- Retour vue nationale : suppression du contexte spatial et recentrage RDC.

## Modes cartographiques

Le mode administratif est implemente comme mode principal.

Les modes suivants sont prepares dans la configuration :

- connectivite ;
- potentiel economique ;
- priorite CCN ;
- qualite des donnees ;
- aide a la decision.

## Performances

- Les provinces sont chargees au demarrage pour construire les 5 zones FDSU.
- Les autres couches sont chargees au premier cochage.
- Les donnees chargees restent cachees via `platformState.dataPromises`.
- Les filtres spatiaux reconstruisent les couches visibles localement sans rechargement complet.

## Tests

Tests statiques realises :

- verification du depot propre avant modification ;
- verification de la branche `feature/smart-map-interactions` ;
- verification des fonctions cartographiques ajoutees ;
- verification du contour `data/generated/rdc_boundary.geojson` ;
- verification de l'equilibre accolades, parentheses et templates ;
- verification `git diff --check`.

Tests Playwright :

- serveur dashboard lance sur `http://127.0.0.1:8000/dashboard/index.html#map` ;
- Microsoft Edge pilote via Playwright disponible ;
- chargement de la page effectue ;
- echec de validation fonctionnelle : `window.L` absent, donc Leaflet non charge ;
- erreurs console observees : `ERR_NETWORK_ACCESS_DENIED` sur ressources externes et un `404`.

## Captures

Capture produite :

- `PROJECT_MANAGEMENT/SPRINT_REPORTS/smart_map_interactions_playwright_blocked.png`

Elle documente l'etat bloque : la page est accessible, mais la carte ne peut pas s'initialiser sans Leaflet.

## Limites

- Les compteurs contextuels affichent `0` pour les couches non encore chargees.
- Les zones FDSU sont une synthese visuelle par provinces, pas une fusion topologique SIG complete.
- Le masquage du reste du pays est realise par filtrage spatial des couches visibles et attenuation du fond, pas encore par masque polygonal hors contexte.
- La validation Playwright est bloquee par des dependances front externes chargees depuis CDN :
  - `https://unpkg.com/leaflet@1.9.4/dist/leaflet.css`
  - `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js`
  - `https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js`

## Recommandations

- Ajouter une vraie fusion topologique des zones FDSU.
- Ajouter un masque visuel hors entite selectionnee.
- Ajouter des tests Playwright automatises au depot pour figer les interactions carte/liste/panneau.
- Vendoriser Leaflet et SheetJS dans le depot ou les servir depuis l'API/dashboard local afin de permettre les tests offline et le mode demo sans reseau externe.

## Statut

✗ À CORRIGER - Playwright lance, mais validation fonctionnelle bloquee par le chargement externe de Leaflet/SheetJS.
