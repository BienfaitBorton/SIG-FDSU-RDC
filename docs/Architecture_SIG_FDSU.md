# Architecture SIG-FDSU RDC

## Objectif

Ce document formalise l’architecture du projet SIG-FDSU RDC en tant que logiciel de gestion et cartographie des données FDSU pour la République démocratique du Congo.

## Principes d’architecture

- Application frontale légère basée sur une interface web professionnelle.
- API FastAPI existante comme back-end REST principal.
- Séparation nette entre l’interface utilisateur et la logique métier / accès aux données.
- Aucun accès direct à la base de données depuis le dashboard : toutes les données sont consommées via l’API.
- Extensibilité prioritaire pour les modules métier futurs.

## Modules du logiciel

Le logiciel s’organise en modules métiers :

- Tableau de bord
- Cartographie
- Référentiel administratif
- Sites FDSU
- Import
- Export
- Statistiques
- Utilisateurs
- Paramètres

Chaque module constitue un écran dédié, ce qui facilite la navigation et l’évolution progressive du produit.

## Architecture fonctionnelle

- **Interface utilisateur** : dossier `dashboard/` avec page HTML, styles et scripts JavaScript.
- **API FastAPI** : expose les entités métier via des routes REST existantes, notamment `/provinces`.
- **Schémas métier** : définis dans `api/schemas/base.py` et utilisés par l’API.
- **Services métier** : séparés de l’interface pour garantir une architecture cloisonnée.

## Décision de design

- Interface sombre, professionnelle, responsive.
- Menu latéral et barre supérieure comme éléments UI principaux.
- Espace central réservé à la carte dans le module cartographie.
- Panneau secondaire pour les détails et le contexte métier.

## Dossier documentation

Cette documentation se trouve dans le dossier `docs/` et pourra être complétée par des guides métier et des décisions futures.
