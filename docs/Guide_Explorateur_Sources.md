# Explorateur de Sources - Guide d'architecture

## Objectif

Fournir un outil officiel d'exploration de sources géographiques en lecture seule pour des fichiers volumineux (KMZ/KML/GeoJSON/Shapefile), sans import en base et sans modification des API existantes.

## Périmètre Sprint

- Lecture de fichiers source sans écriture PostgreSQL.
- Construction automatique d'un catalogue de données.
- Construction automatique d'un dictionnaire de données.
- Génération de rapports JSON et Markdown.
- Consultation dans le Dashboard via chargement d'un rapport JSON généré.

## Architecture du module

Le module Python est situé dans `app/referentials/source_explorer/`.

### Composants

- `readers.py`
  - Lecture read-only de formats : KMZ, KML, GeoJSON, Shapefile (optionnel via `pyshp`), GeoPackage (placeholder).
  - Réutilise `app/geospatial/kmz_reader.py` et `app/geospatial/description_parser.py`.

- `analyzer.py`
  - Agrège par dossier/folder.
  - Compte les objets et champs.
  - Identifie les géométries (Point, Ligne, Polygone, MultiPolygone).
  - Calcule un score de qualité de complétude.
  - Produit dictionnaire de données (type, valeurs, uniques, nulles, exemple).

- `tagging.py`
  - Classification automatique des dossiers en catégories métiers.
  - Attribution des tags.
  - Suggestion de module SIG cible.

- `reporting.py`
  - Export des rapports en JSON et Markdown.

- `explorer.py`
  - Service orchestrateur `SourceExplorerService`.
  - Point d'entrée unique pour exécuter une exploration.

- `__main__.py`
  - CLI : `python -m app.referentials.source_explorer <source>`.

- `models.py`
  - Dataclasses normalisées de sortie (catalogue + dictionnaire).

## Flux d'exécution

1. Détection du format source.
2. Lecture des objets en mémoire (read-only).
3. Construction d'une vue normalisée `FeatureRecord`.
4. Analyse : catalogue, tags, dictionnaire.
5. Export de deux rapports : JSON et Markdown.
6. Publication locale de `latest.catalog.json` et `latest.catalog.md`.

## Sorties générées

Par défaut dans `data/reports/source_explorer/` :

- `<nom_source>.catalog.json`
- `<nom_source>.catalog.md`
- `latest.catalog.json`
- `latest.catalog.md`

## Dashboard

Un nouveau module UI `Explorateur de Sources` a été ajouté dans `dashboard/`.

### Usage UI

1. Générer un rapport via CLI.
2. Ouvrir le module Explorateur de Sources.
3. Charger le fichier JSON de rapport.
4. Consulter :
   - KPI source
   - Catalogue des dossiers
   - Dictionnaire de données
   - Tags consolidés

Le bouton `Extraire` est présent mais volontairement inactif (prévu pour sprint futur).

## Contraintes respectées

- Aucune modification PostgreSQL.
- Aucune modification API existante.
- Aucun import de données.
- Aucun enregistrement métier.
- Traitement en lecture seule.

## Extension future

- Support GeoPackage effectif (lecture couches et champs).
- Support extraction par catégorie/tag via bouton `Extraire`.
- Support batch multi-fichiers.
- Profiling mémoire pour très gros KMZ (> 190k objets).
- Visualisation cartographique d'aperçu (échantillon) dans le Dashboard.
- Connecteurs sources officielles (CAID, CENI, HDX, FDSU, KMZ) déjà préparés côté tagging/catalogue.
