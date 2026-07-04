# SIG-FDSU RDC v1.0 - Architecture fonctionnelle

## 1. Vision générale

Le SIG-FDSU RDC est une plateforme nationale d'information géographique et d'aide à la décision destinée à structurer, visualiser, analyser et exploiter les données territoriales utiles au Fonds de Développement du Service Universel en République démocratique du Congo.

La plateforme doit dépasser la logique d'un simple visualiseur cartographique. Elle devient un outil métier national capable de relier le référentiel administratif, les localités, les sites FDSU, les missions terrain, les données de connectivité, les profils territoriaux, les services publics, les activités économiques et les scores de priorisation FDSU.

La vision cible repose sur les piliers suivants :

- **Référentiel administratif national** : organisation officielle des Zones FDSU, provinces, territoires, collectivités, groupements et localités.
- **Cartographie opérationnelle** : affichage et exploration des couches administratives, sites, services, connectivité et activités économiques.
- **Sites FDSU** : inventaire, codification, statut, planification, suivi et rattachement territorial des sites.
- **Missions terrain** : planification, exécution, documentation, photos, rapports et historique.
- **Connectivité** : suivi de la couverture 2G, 3G, 4G, 5G et des scores de connectivité.
- **Profils territoriaux** : population, économie, services publics, défis, enclavement et potentiel.
- **Aide à la décision** : filtres métier, scoring, classement, justification, carte, tableau et export.
- **Import/Export** : intégration contrôlée de fichiers terrain, référentiels, données géospatiales et exports exploitables.
- **Rapports** : production de rapports décisionnels, cartes, fiches et listes filtrées.

## 2. Objectifs métier

Le système doit permettre aux utilisateurs de répondre rapidement à des questions métier complexes, sans retraitement manuel dispersé dans plusieurs fichiers.

Questions prioritaires :

- Quelles sont les localités de plus de 3 000 habitants, sans couverture 4G, avec centre de santé, école secondaire et fort potentiel agricole ?
- Quels sont les territoires de la Zone Nord avec fort potentiel économique mais faible connectivité ?
- Quelles localités sont prioritaires pour l'implantation ou le renforcement de CCN ?
- Quelles zones sont mal couvertes tout en étant économiquement stratégiques ?
- Quels territoires cumulent faible connectivité, enclavement, forte population et potentiel économique ?
- Quels sites FDSU sont associés à une localité, un groupement, une collectivité ou un territoire ?
- Quelles missions terrain sont prévues, en cours ou terminées pour une zone donnée ?

Le système ne doit jamais inventer une donnée manquante. Lorsqu'une information n'est pas disponible, l'interface doit afficher clairement **donnée à compléter**.

## 3. Modules fonctionnels

### Accueil

Le module Accueil présente une synthèse opérationnelle de la plateforme : compteurs globaux, accès rapides, état de la base, derniers imports, indicateurs de couverture et alertes qualité. Les compteurs doivent être interactifs et ouvrir des listes filtrables.

### Cartographie

Le module Cartographie permet d'afficher les couches administratives, Zones FDSU, localités, sites, missions, connectivité, services publics et activités économiques. Il synchronise carte, tableau et fiche détaillée.

### Référentiel National

Le Référentiel National centralise la hiérarchie administrative et métier : Zones FDSU, provinces, territoires, collectivités, groupements et localités. Il doit permettre la recherche, le filtrage, la consultation de listes, l'ouverture de fiches et le contrôle de cohérence.

### Profils territoriaux

Le module Profils territoriaux enrichit les entités administratives avec des données socio-économiques, de services, de connectivité, de potentiel et de défis. Il constitue la base analytique du moteur d'aide à la décision.

### Connectivité

Le module Connectivité suit la couverture réseau 2G, 3G, 4G, 5G, les scores de connectivité, les zones blanches, les zones partiellement couvertes et les besoins de renforcement.

### Sites FDSU

Le module Sites FDSU gère l'inventaire des sites, leur codification, leur rattachement territorial, leur statut, leur technologie, leurs capacités, leurs documents, leurs photos et leur historique.

### Missions terrain

Le module Missions terrain permet de planifier, documenter, suivre et clôturer les missions. Chaque mission doit être rattachée à une zone, une entité administrative, un site ou une problématique métier.

### Aide à la décision

Le module Aide à la décision permet de filtrer, classer, cartographier et exporter les localités ou territoires selon des critères métier. Il affiche le score FDSU, la justification du score et les champs à compléter.

### Import

Le module Import permet d'intégrer des fichiers Excel, CSV, JSON, GeoJSON, KML, KMZ et Shapefile. Il doit inclure prévisualisation, validation, détection d'anomalies, rapport d'import et import contrôlé.

### Export

Le module Export permet d'exporter des listes, fiches, cartes et couches en CSV, JSON, GeoJSON, KML, KMZ ou Shapefile selon les besoins opérationnels.

### Rapports

Le module Rapports produit des synthèses décisionnelles : localités prioritaires, territoires à fort potentiel, zones faiblement couvertes, sites planifiés, missions, anomalies et recommandations FDSU.

### Administration

Le module Administration gère les utilisateurs, rôles, permissions, paramètres système, sources de données, référentiels, nomenclatures et journaux d'activité.

## 4. Navigation cible

La navigation cible suit la hiérarchie territoriale suivante :

```text
Zones FDSU
  > Provinces
    > Territoires
      > Collectivités
      > Groupements
        > Localités
```

Règle obligatoire :

- Un compteur n'ouvre jamais une fiche unique.
- Un compteur ouvre toujours une liste filtrable.
- La fiche s'ouvre uniquement après clic sur une ligne de tableau ou un objet cartographique.
- La navigation doit rester progressive : liste, sélection, fiche, puis actions.
- Les listes doivent être filtrables par zone, province, territoire, type, statut, source, qualité et critères métier disponibles.

Exemples :

- Clic sur le compteur **Territoires** : ouvre la liste des territoires.
- Clic sur une province dans la liste : ouvre la fiche de la province et la liste de ses territoires.
- Clic sur un territoire : ouvre sa fiche et les listes de collectivités, groupements et localités associées.
- Clic sur un objet carte : ouvre la fiche correspondante et met à jour le tableau associé.

## 5. Fiches détaillées

Chaque fiche doit présenter une information exploitable et contextualisée. Les fiches ne doivent pas être de simples fenêtres descriptives : elles doivent permettre de comprendre la situation territoriale, opérationnelle et décisionnelle.

### Fiche Zone

La fiche Zone contient l'identité de la zone, les provinces rattachées, la carte de la zone, les statistiques agrégées, les localités, les sites, les missions, les niveaux de couverture, les défis majeurs, les scores agrégés, les documents et les exports.

### Fiche Province

La fiche Province contient l'identité, la zone FDSU, les territoires, la carte, les statistiques, les activités économiques dominantes, les services publics, la connectivité, les sites associés, les missions associées, les documents, les photos, l'historique, le score FDSU agrégé et les actions d'export/impression.

### Fiche Territoire

La fiche Territoire contient l'identité, la province, les collectivités, groupements et localités, la carte, les statistiques, la population, les activités principales et secondaires, les particularités, les défis, les services publics, la connectivité, les sites, les missions, les documents, les photos, l'historique, le score FDSU et l'export.

### Fiche Collectivité

La fiche Collectivité contient l'identité, le territoire parent, les groupements et localités associés, la carte, les statistiques, les activités économiques, particularités, défis, services publics, connectivité, sites, missions, documents, photos, historique, score FDSU et export.

### Fiche Groupement

La fiche Groupement contient l'identité, la collectivité parent, les localités associées, la carte, les statistiques, les activités principales et secondaires, particularités, défis, services publics, connectivité, sites, missions, documents, photos, historique, score FDSU et export.

### Fiche Localité

La fiche Localité est la fiche opérationnelle la plus importante pour la priorisation. Elle contient identité, hiérarchie complète, localisation carte, population, services publics, connectivité, activités économiques, particularités, défis, niveau d'enclavement, sites associés, missions associées, documents, photos, historique, score FDSU, justification du score, recommandation et export/impression.

### Fiche Site FDSU

La fiche Site FDSU contient identité, code FDSU, hiérarchie territoriale, carte, type de site, statut, technologie, capacité, alimentation, opérateur, dates, missions, documents, photos, historique, couverture associée, observations terrain et export/impression.

### Fiche Mission

La fiche Mission contient identité, objectif, zone ou entité concernée, site associé, statut, dates, équipe, compte rendu, documents, photos, observations, décisions, historique et export/impression.

Contenu commun minimal à toutes les fiches :

- identité ;
- hiérarchie ;
- carte ;
- statistiques ;
- activités économiques principales et secondaires ;
- particularités ;
- défis ;
- services publics ;
- connectivité ;
- sites associés ;
- missions associées ;
- documents ;
- photos ;
- historique ;
- score FDSU ;
- export/impression.

## 6. Profils territoriaux

Les profils territoriaux enrichissent les entités administratives et permettent les analyses métier.

Champs cibles :

- population ;
- superficie ;
- activité principale ;
- activité secondaire ;
- potentiel agricole ;
- potentiel minier ;
- potentiel commercial ;
- potentiel numérique ;
- particularités ;
- défis ;
- niveau d'enclavement ;
- services publics ;
- couverture réseau.

Les champs non disponibles doivent rester vides ou nuls en base et apparaître comme **donnée à compléter** dans l'interface. Aucune correction automatique, interpolation ou estimation non documentée ne doit être appliquée.

## 7. Moteur d'aide à la décision

Le moteur d'aide à la décision doit permettre de transformer les données territoriales en listes d'intervention priorisées.

Fonctions principales :

- filtres par zone, province, territoire, population, couverture réseau, services publics, activité économique, potentiel, connectivité et score ;
- requêtes métier préconfigurées ;
- classement par score FDSU ;
- tableau des résultats ;
- carte des résultats ;
- fiche détaillée après sélection ;
- justification du score ;
- indication des données à compléter ;
- export CSV, JSON, GeoJSON ou rapport.

Requêtes métier prioritaires :

- localités de plus de 3 000 habitants sans 4G avec centre de santé, école secondaire et fort potentiel agricole ;
- territoires de la Zone Nord avec fort potentiel économique et faible connectivité ;
- localités prioritaires pour CCN ;
- zones mal couvertes mais économiquement stratégiques.

Formule cible du score FDSU :

| Critère | Pondération |
|---|---:|
| Population | 20 % |
| Connectivité | 20 % |
| Services publics | 15 % |
| Activités économiques | 15 % |
| Enclavement | 10 % |
| Électricité | 10 % |
| Potentiel économique | 10 % |

Le score doit être accompagné d'une justification lisible : critères favorables, critères défavorables, données manquantes et recommandation FDSU.

## 8. Cartographie

La cartographie est un module central de navigation, d'analyse et de restitution.

Couches cibles :

- couches administratives ;
- couches Zones FDSU colorées ;
- couches provinces, territoires, collectivités, groupements et localités ;
- sites FDSU ;
- couverture réseau ;
- services publics ;
- activités économiques ;
- cartes thématiques ;
- missions terrain ;
- résultats du moteur d'aide à la décision.

Interactions obligatoires :

- clic carte vers fiche ;
- clic tableau vers zoom carte ;
- filtre dans le tableau vers mise à jour carte ;
- sélection carte vers ligne de tableau ;
- affichage clair lorsque la géométrie est absente ;
- export de la carte ou de la couche filtrée.

Couleurs officielles Zones FDSU :

| Code | Zone | Couleur |
|---|---|---|
| OT | Ouest | Jaune |
| CE | Centre | Rose |
| SD | Sud | Vert sombre |
| ND | Nord | Gris olive |
| ET | Est | Bleu |

Lorsque les polygones de Zones FDSU ne sont pas disponibles, la plateforme doit pouvoir colorer les provinces selon leur zone FDSU comme solution de continuité cartographique.

## 9. Codification FDSU

La codification FDSU est obligatoire pour les objets opérationnels.

Format :

```text
FDSU_<CODE_ZONE>_<CODE_PROVINCE>_<CODE_TERRITOIRE>_<CODE_SITE>
```

Exemple :

```text
FDSU_ND_05_001_001
```

Cette nomenclature doit être utilisée dans :

- Sites FDSU ;
- Missions ;
- Couverture réseau ;
- Télécommunications ;
- Rapports ;
- Import/Export.

La codification doit rester stable dans le temps. Toute correction de code doit être historisée et justifiée.

## 10. Import/Export

Le système doit prendre en charge les formats suivants :

- Excel ;
- CSV ;
- JSON ;
- GeoJSON ;
- KML ;
- KMZ ;
- Shapefile.

Fonctions d'import :

- chargement du fichier ;
- prévisualisation ;
- détection du format ;
- lecture des feuilles ou couches ;
- validation des colonnes ;
- validation des géométries ;
- détection des anomalies ;
- rapport d'import ;
- import contrôlé ;
- traçabilité de la source ;
- conservation des lignes rejetées ou à vérifier.

Fonctions d'export :

- export de listes filtrées ;
- export de fiches ;
- export de couches géographiques ;
- export de résultats décisionnels ;
- export de rapports ;
- formats CSV, JSON, GeoJSON, KML, KMZ et Shapefile selon disponibilité.

Règle : un import ne doit jamais corriger silencieusement les anomalies. Les anomalies doivent être visibles, documentées et traitées selon un workflow explicite.

## 11. Rôles utilisateurs

### Administrateur

Gère les utilisateurs, rôles, paramètres, référentiels, sources, imports structurants et droits d'accès.

### Analyste SIG

Explore les données, contrôle les couches, produit des analyses, prépare des cartes, vérifie les anomalies et contribue aux rapports.

### Technicien terrain

Consulte les fiches, prépare ou renseigne les missions, ajoute observations, documents, photos et données terrain.

### Responsable projet

Suit les sites, missions, priorités, alertes, rapports, indicateurs et décisions opérationnelles.

### Direction générale

Consulte les tableaux de bord, rapports décisionnels, zones prioritaires, recommandations et synthèses stratégiques.

## 12. Workflows

### Consulter une localité

1. Rechercher la localité ou naviguer par Zone FDSU.
2. Ouvrir la liste filtrable.
3. Cliquer sur la ligne de la localité.
4. Consulter la fiche, la carte, les services, la connectivité, les sites, les missions et le score FDSU.
5. Exporter ou imprimer la fiche si nécessaire.

### Rechercher une zone sans couverture

1. Ouvrir Aide à la décision ou Cartographie.
2. Filtrer par couverture 4G absente ou connectivité faible.
3. Filtrer par zone, potentiel ou population.
4. Examiner la carte et le tableau.
5. Ouvrir les fiches pertinentes.
6. Exporter la liste ou la carte.

### Importer des données terrain

1. Choisir le format d'import.
2. Charger le fichier.
3. Prévisualiser les données.
4. Valider les colonnes et géométries.
5. Examiner les anomalies.
6. Lancer l'import contrôlé.
7. Consulter le rapport d'import.

### Créer un site FDSU

1. Sélectionner la localité ou l'entité de rattachement.
2. Créer le site avec la codification FDSU obligatoire.
3. Renseigner type, statut, technologie, capacité, alimentation et observations.
4. Associer documents, photos et missions.
5. Vérifier la fiche site et la carte.

### Planifier une mission

1. Sélectionner une zone, localité, site ou problématique.
2. Créer la mission.
3. Définir objectif, période, équipe et statut.
4. Associer documents et fiches terrain.
5. Suivre l'avancement et clôturer avec rapport.

### Produire un rapport

1. Choisir le type de rapport.
2. Définir les filtres.
3. Générer les tableaux, cartes et recommandations.
4. Vérifier les données manquantes.
5. Exporter le rapport.

### Exporter une carte ou une fiche

1. Appliquer les filtres.
2. Vérifier le périmètre affiché.
3. Choisir le format.
4. Exporter.
5. Conserver la source et la date d'export.

## 13. Règles UX importantes

Règles obligatoires :

- aucun bouton mort ;
- aucun compteur statique ;
- recherche toujours exploitable ;
- liste avant fiche ;
- carte, tableau et fiche synchronisés ;
- message clair si donnée manquante ;
- ne jamais inventer les données manquantes ;
- toute donnée absente affiche **donnée à compléter** ;
- les exports doivent refléter exactement le filtre actif ;
- les erreurs doivent être compréhensibles par un utilisateur métier ;
- les actions destructives doivent être confirmées ;
- les anomalies doivent être visibles et traçables.

## 14. Roadmap

### v1.0 - Architecture fonctionnelle

Figer la vision, les modules, la navigation, les fiches, les règles UX, la cartographie cible, la codification et le moteur décisionnel.

### v1.1 - Navigation hiérarchique complète

Implémenter le parcours Zones FDSU > Provinces > Territoires > Collectivités > Groupements > Localités, avec listes filtrables et fiches synchronisées.

### v1.2 - Profils territoriaux

Structurer les profils population, économie, services publics, connectivité, défis, potentiel et enclavement.

### v1.3 - Sites FDSU

Stabiliser l'inventaire des sites, la codification FDSU, les statuts, les technologies et le rattachement administratif.

### v1.4 - Missions terrain

Mettre en place la planification, le suivi, les documents, photos, rapports et historiques de mission.

### v1.5 - Couverture réseau

Intégrer les données de couverture 2G, 3G, 4G, 5G, les zones blanches et les analyses de connectivité.

### v1.6 - Rapports décisionnels

Produire des rapports métier consolidés : localités prioritaires, territoires stratégiques, zones mal couvertes, sites à créer, missions à planifier et recommandations FDSU.

## 15. Principe de gouvernance

Ce document constitue la référence fonctionnelle v1.0 avant tout développement futur. Toute nouvelle fonctionnalité doit être évaluée selon sa cohérence avec cette architecture, son impact sur les modules existants, sa capacité à préserver la traçabilité des données et son respect du principe fondamental : **ne jamais inventer les données manquantes**.
