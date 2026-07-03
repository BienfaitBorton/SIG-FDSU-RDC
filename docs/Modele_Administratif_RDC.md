# Modèle Administratif RDC

## Hiérarchie administrative validée

La hiérarchie administrative de la République démocratique du Congo est formalisée comme suit :

1. Province
2. Territoire
3. Collectivité
4. Groupement
5. Village

Cette structure est utilisée par le logiciel pour modéliser le référentiel administratif et préparer l’intégration des données territoriales.

## Niveau territorial FDSU

Les 5 Zones FDSU sont retenues comme premier niveau métier pour l’organisation des données :

- **ND** : Nord
- **SD** : Sud
- **CE** : Centre
- **OT** : Ouest
- **ET** : Est

Ces zones FDSU sont destinées à servir de premier niveau de classification métier, en parallèle de la hiérarchie administrative.

## Distinction entre organisation FDSU et organisation administrative

- **Organisation FDSU** : structure métier propre au projet, basée sur les 5 zones FDSU et les entités du réseau FDSU.
- **Organisation administrative** : structure officielle de l’État, basée sur les provinces, territoires, collectivités, groupements et villages.

Le logiciel conserve cette distinction pour garantir la cohérence entre la logique opérationnelle FDSU et le référentiel administratif national.

## Entités principales

- Province
- Territoire
- Collectivité
- Groupement
- Village

## Principes de modélisation

- Les provinces sont gérées en premier lieu dans le module `Référentiel administratif`.
- Les territoires, collectivités, groupements et villages seront implémentés ultérieurement.
- Les zones FDSU servent de cadre métier transverse aux entités administratives.
