# Feuille de route SIG-FDSU RDC

## Vision globale

Construire un SIG national pour le référentiel administratif, les sites FDSU et les opérations cartographiques en RDC.

## Phases prévues

### Phase 1 : Architecture et prototype UI

- Mise en place de l’interface graphique `dashboard/`
- Menu latéral, barre supérieure, zone carte et panneau d’information
- Modules identifiés sans logique métier complexe
- Documenter l’architecture officielle

### Phase 2 : Référentiel administratif

- Module fonctionnel `Référentiel administratif`
- Consommation de l’API existing FastAPI
- Affichage des provinces dans un tableau professionnel
- Recherche, tri et fiche détaillée

### Phase 3 : Cartographie et sites

- Module `Cartographie` avec visualisation de la carte
- Module `Sites FDSU` pour inventaire des sites
- Intégration des couches géospatiales, affichage d’objets sur carte

### Phase 4 : Import/export

- Module `Import` pour chargement des fichiers et référentiels
- Module `Export` pour extraction des données et rapports
- Validation des formats et prétraitement

### Phase 5 : Statistiques et administration

- Module `Statistiques` pour indicateurs métier et tendances
- Module `Utilisateurs` pour gestion des accès
- Module `Paramètres` pour configuration globale

## Jalons clés

- Prototype UI validé
- Module référentiel administratif opérationnel
- Cartographie de base intégrée
- Import/Export stabilisés
- Tableau de bord et statistiques finalisés

## Objectifs de qualité

- Application responsive et moderne
- Séparation interface/API
- Documentation claire et mise à jour continue
- Évolutivité pour les entités territoriales futures
