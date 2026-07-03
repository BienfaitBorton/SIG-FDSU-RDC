# app.geospatial

Moteur d'import géospatial intelligent du projet SIG-FDSU RDC.

## Composants

- `kmz_reader.py` : lecture du KMZ sans altérer le fichier d'origine.
- `geometry_parser.py` : extraction des géométries KML.
- `description_parser.py` : transformation des descriptions HTML en dictionnaire clé/valeur.
- `feature_classifier.py` : classification automatique du type d'entité.
- `geojson_writer.py` : génération d'un GeoJSON enrichi.
- `report.py` : rapport d'analyse géospatial.

## Principe

Le module lit un KMZ, extrait les placemarks, analyse les attributs et descriptions, classe l'entité, puis produit un GeoJSON enrichi et un rapport d'analyse. Aucune écriture n'est faite dans PostgreSQL et l'archive KMZ d'origine reste intacte.
