# Rapport Sprint 3.2 - Centre National de Connaissances Territoriales

Date: 2026-07-04

## Architecture

Le Sprint 3.2 crée le socle du CNCT comme module principal du SIG-FDSU RDC. L'architecture sépare les profils encyclopédiques, les sources, les documents, les statistiques, l'historique, la qualité, la complétude et les suggestions.

Aucune donnée publique n'est collectée automatiquement. Les informations externes restent destinées au workflow : Recherche > Propositions > Comparaison > Validation > Publication.

## Tables

- `territorial_profiles` existe déjà comme base de profils territoriaux.
- `territorial_documents`
- `territorial_sources`
- `territorial_statistics`
- `territorial_history`
- `territorial_quality`
- `territorial_completeness`

## API

- `GET /knowledge`
- `GET /knowledge/{entity}`
- `GET /knowledge/search`
- `GET /knowledge/completeness`
- `GET /knowledge/suggestions`
- Endpoints complémentaires préparatoires :
  - `GET /knowledge/types`
  - `GET /knowledge/sections`

## Dashboard

- Nouveau menu principal `Centre de connaissances`.
- Tableau de bord CNCT :
  - profils complets ;
  - profils incomplets ;
  - profils sans photo ;
  - profils sans activités ;
  - profils sans défis ;
  - profils sans services publics ;
  - profils sans connectivité ;
  - profils sans documents.
- Tableau des priorités d'enrichissement :
  - province ;
  - territoire ;
  - complétude ;
  - nombre de champs manquants ;
  - priorité ;
  - date de dernière mise à jour ;
  - tri, filtres et recherche.
- Fiche encyclopédique à onglets avec toutes les rubriques demandées.

## Limites

- Aucune collecte web automatique.
- Aucun enrichissement public réel injecté.
- Les profils CNCT exposés dans ce sprint servent de socle fonctionnel et technique.
- La publication contrôlée vers les profils officiels reste séparée.
- Les tests navigateur automatisés restent à compléter dans l'environnement local.

## Travaux restants

- Implémenter la publication contrôlée après validation.
- Ajouter les rôles et permissions de validation CNCT.
- Brancher les profils CNCT sur les données PostgreSQL réelles après migration.
- Ajouter les tests API avec base de test.
- Relier les écrans CNCT à la Matrice FDSU, aux KPI, aux scores, simulations, classements et recommandations.
- Préparer le connecteur de collecte publique, désactivé par défaut et soumis au workflow de validation.
