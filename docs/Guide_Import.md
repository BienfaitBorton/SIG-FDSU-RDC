# Guide Import SIG-FDSU RDC

## Objectif

Ce guide décrit le concept du module `Import` et les principes à suivre pour la future intégration des données.

## Principes d’import

- Les données sont importées via l’API ou un service d’import dédié, sans connexion directe à la base de données à partir du dashboard.
- Les imports doivent être traçables et validés avant injection dans le référentiel.
- Le module doit prévoir la prise en charge de formats standard : CSV, Excel, GeoJSON, shapefile, KML.

## Flux d’import prévu

1. Sélection du fichier ou du jeu de données.
2. Analyse du format et mappage des champs.
3. Validation des données métier.
4. Pré-visualisation et extraction des erreurs.
5. Import effectif dans le référentiel via l’API.

## Données cibles pour le premier cycle

- Provinces
- Territoires
- Collectivités
- Groupements
- Villages

## Bonnes pratiques

- Ne pas modifier la base de données directement depuis le front-end.
- Centraliser les règles métier dans le back-end.
- Prévoir des messages clairs pour l’utilisateur en cas d’erreur.
- Garder la logique d’import distincte de l’interface graphique.
