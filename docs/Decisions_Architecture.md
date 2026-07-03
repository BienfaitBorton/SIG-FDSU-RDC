# Décisions d’architecture SIG-FDSU RDC

## Principes validés

- Le logiciel est structuré en modules métier clairement séparés.
- L’interface est une application web moderne, sur fond sombre et responsive.
- L’API FastAPI existante est le point d’accès principal aux données.
- Aucun module ne doit accéder directement à la base de données depuis le front-end.

## Zone FDSU comme premier niveau métier

Les 5 zones FDSU validées sont :

- ND : Nord
- SD : Sud
- CE : Centre
- OT : Ouest
- ET : Est

Ces zones constituent le premier niveau de classification métier dans l’architecture du projet.

## Hiérarchie administrative validée

- Province
- Territoire
- Collectivité
- Groupement
- Village

Cette hiérarchie reflète la structure administrative officielle de la RDC et sert de modèle pour le référentiel.

## Distinction organisationnelle

- **Organisation FDSU** : niveau métier FDSU et zones opérationnelles.
- **Organisation administrative** : référentiel national des entités territoriales.

Cette distinction est essentielle pour conserver la flexibilité métier tout en respectant le cadre administratif.

## Modules principaux confirmés

- Tableau de bord
- Cartographie
- Référentiel administratif
- Sites FDSU
- Import
- Export
- Statistiques
- Utilisateurs
- Paramètres

## Décision sur les écrans et rôles

- Le premier écran fonctionnel est `Référentiel administratif` avec gestion des provinces.
- Les modules cartographie et sites seront ajoutés après la stabilisation du référentiel.
- Import / export seront construits comme des actions serveur, sans logique métier côté UI.

## Documentation projet

- La documentation officielle est centralisée dans `docs/`.
- Les futures décisions seront consignées dans `Decisions_Architecture.md`.
