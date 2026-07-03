# Guide Export SIG-FDSU RDC

## Objectif

Ce document décrit la stratégie d’export des données depuis le logiciel SIG-FDSU RDC.

## Objectifs du module Export

- Permettre l’extraction des jeux de données métier.
- Produire des formats exploitables pour diffusion ou analyse.
- Offrir des exports sécurisés via l’API.

## Principes d’export

- L’export doit rester une action serveur accessible via API.
- L’interface fournit des options de filtrage et de sélection.
- Les données doivent pouvoir être exportées en formats standard : CSV, Excel, GeoJSON.

## Données prioritaires

- Provinces
- Territoires
- Collectivités
- Sites FDSU

## Workflow envisagé

1. Choisir l’objet métier à exporter.
2. Définir les filtres et le périmètre.
3. Lancer la génération du fichier.
4. Télécharger le résultat.

## Contraintes

- Ne pas exposer de données sensibles sans contrôle d’accès.
- Ne pas modifier la base de données lors de l’export.
- Prévoir un format de fichier clair et reproductible.
