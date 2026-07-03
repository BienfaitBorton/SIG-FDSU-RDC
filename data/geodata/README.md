# Référentiel géographique SIG-FDSU RDC

Ce dossier organise les données géographiques du projet SIG-FDSU RDC sans contenir de données fictives ni de logique métier.

## Structure

- `reference/` : couches officielles de référence validées pour le projet.
- `imported/` : fichiers géographiques importés avant validation ou transformation.
- `generated/` : couches produites par le système à partir des traitements internes.
- `exports/` : sorties géographiques générées pour diffusion ou partage.

## Sous-dossiers `reference/`

- `rdc/` : couche de cadrage national de la RDC.
- `zones/` : zones FDSU officielles.
- `provinces/` : provinces du référentiel administratif.
- `territoires/` : territoires du référentiel administratif.
- `villes/` : villes du référentiel géographique.
- `communes/` : communes du référentiel géographique.
- `secteurs/` : secteurs administratifs.
- `chefferies/` : chefferies administratives.
- `groupements/` : groupements administratifs.
- `villages/` : villages du référentiel administratif.
- `sites/` : sites FDSU géolocalisés.

## Formats attendus

- Les couches officielles du projet seront stockées au format GeoJSON.
- Les imports pourront provenir de Shapefile, GeoPackage, KML, KMZ ou GeoJSON.

## Principe d’utilisation

- `reference/` contient les couches validées et stables.
- `imported/` contient les sources brutes ou intermédiaires à traiter.
- `generated/` contient les productions géographiques calculées par le système.
- `exports/` contient les fichiers prêts à être distribués.
