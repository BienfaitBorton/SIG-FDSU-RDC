# SIG-FDSU RDC v1.0 - Schéma Directeur de la Plateforme Nationale

## 1. Vision

Le SIG-FDSU RDC est conçu comme une plateforme nationale destinée à structurer, centraliser, analyser et valoriser les données territoriales, géographiques, numériques et opérationnelles utiles au Fonds de Développement du Service Universel.

La plateforme ne doit pas être comprise comme un simple logiciel SIG. Elle constitue progressivement un système national d'aide à la décision pour la planification, le suivi et l'évaluation des investissements numériques en République Démocratique du Congo.

La vision cible est de disposer d'une plateforme unique permettant de :

- centraliser le référentiel administratif officiel ;
- centraliser les données territoriales ;
- centraliser les données de connectivité ;
- centraliser les données relatives aux infrastructures numériques ;
- documenter les sites FDSU, missions terrain et Centres Communautaires Numériques ;
- assister les décisions stratégiques du FDSU ;
- planifier les investissements numériques ;
- produire des rapports fiables pour la Direction Générale, les partenaires techniques et financiers, et les équipes opérationnelles.

Le SIG-FDSU RDC devient ainsi un instrument institutionnel de connaissance du territoire, de réduction des inégalités numériques et d'orientation des priorités d'intervention.

## 2. Mission

La mission de la plateforme est de donner aux décideurs et équipes opérationnelles une vision consolidée, fiable et exploitable du territoire national et des besoins en connectivité.

Elle doit permettre aux décideurs de :

- connaître le territoire et ses subdivisions ;
- analyser les besoins des populations et localités ;
- mesurer les inégalités numériques ;
- identifier les zones faiblement couvertes ;
- prioriser les investissements ;
- suivre les projets, sites et missions ;
- documenter les interventions terrain ;
- produire des rapports stratégiques et opérationnels ;
- renforcer la traçabilité des décisions ;
- appuyer le développement des infrastructures numériques et des Centres Communautaires Numériques.

La plateforme doit servir à la fois les usages de pilotage national, d'analyse SIG, de suivi terrain, de reporting institutionnel et de planification budgétaire.

## 3. Piliers de la plateforme

### Pilier 1 - Référentiel National

Le Référentiel National constitue la base commune de toutes les données. Il organise les Zones FDSU, provinces, territoires, villes, secteurs, chefferies, collectivités, groupements, localités, villages si applicables, sites FDSU et autres objets opérationnels.

Il garantit l'unicité des entités, la cohérence des rattachements et la stabilité des codes.

### Pilier 2 - Cartographie

La cartographie permet de visualiser les entités administratives, les Zones FDSU, les localités, les sites, les services, les données de connectivité, les activités économiques, les missions et les résultats décisionnels.

Elle doit être synchronisée avec les tableaux et les fiches détaillées.

### Pilier 3 - Profils territoriaux

Les profils territoriaux enrichissent les entités avec les données de population, superficie, activités économiques, potentiel, défis, services publics, enclavement, électricité et couverture réseau.

Ils constituent le socle de l'analyse métier.

### Pilier 4 - Connectivité

Le pilier Connectivité centralise les informations relatives à la couverture 2G, 3G, 4G, 5G, aux zones blanches, aux scores de connectivité, aux opérateurs et aux besoins de renforcement.

### Pilier 5 - Télécommunications

Ce pilier rassemble les infrastructures et données techniques liées aux télécommunications : sites, technologies, réseaux, capacités, alimentation, équipements, opérateurs et observations terrain.

### Pilier 6 - Sites FDSU

Les Sites FDSU représentent les infrastructures planifiées, en construction, actives ou à renforcer. Chaque site doit être codifié, rattaché à une hiérarchie territoriale, documenté et suivi dans le temps.

### Pilier 7 - Centres Communautaires Numériques

Les CCN constituent un axe majeur de l'inclusion numérique. La plateforme doit permettre d'identifier les localités prioritaires, de planifier les implantations, de suivre les sites associés et de produire des rapports d'impact.

### Pilier 8 - Missions terrain

Les missions terrain documentent la collecte, la vérification, le suivi, l'audit et la validation des données. Elles relient le système central aux observations réelles du terrain.

### Pilier 9 - Import / Export

Le pilier Import / Export assure l'intégration contrôlée de fichiers Excel, CSV, JSON, GeoJSON, KML, KMZ et Shapefile, ainsi que l'export de listes, fiches, cartes et rapports.

### Pilier 10 - Rapports

Les rapports traduisent les données en supports de décision : synthèses territoriales, cartes, indicateurs, priorités, anomalies, recommandations et états d'avancement.

### Pilier 11 - Intelligence FDSU

L'Intelligence FDSU constitue le cerveau analytique de la plateforme. Elle regroupe les scores, règles, KPI, simulations, scénarios, classements, recommandations et historiques de décision.

## 4. Architecture globale

Schéma cible simplifié :

```text
                              +-------------------------+
                              |   Utilisateurs FDSU     |
                              | DG / SIG / Terrain / PM |
                              +------------+------------+
                                           |
                                           v
+----------------+        +-----------------------------+        +------------------+
| Import terrain | -----> |        Dashboard Web        | <----> | Administration   |
| Excel/CSV/KMZ  |        | Accueil / Carte / Fiches    |        | Rôles / Sources  |
| GeoJSON/SHP    |        | Décision / Sites / Missions |        | Paramètres       |
+-------+--------+        +---------------+-------------+        +------------------+
        |                                 |
        v                                 v
+----------------+        +-----------------------------+
| Validation     | -----> |        API FastAPI          |
| Anomalies      |        | Référentiel / Cartographie  |
| Normalisation  |        | Décision / Sites / Missions |
+-------+--------+        +---------------+-------------+
        |                                 |
        v                                 v
+----------------+        +-----------------------------+
| Référentiels   | -----> |    PostgreSQL / PostGIS     |
| Nomenclatures  |        | Données métier + géométries |
+----------------+        +---------------+-------------+
                                          |
                                          v
        +----------------+----------------+----------------+
        |                |                |                |
        v                v                v                v
+-------------+  +---------------+  +-------------+  +-------------+
| Cartographie|  | Aide décision |  | Sites FDSU  |  | Missions    |
+-------------+  +---------------+  +-------------+  +-------------+
        \                |                |                /
         \               |                |               /
          v              v                v              v
                 +-----------------------------+
                 |          Rapports           |
                 | Cartes / Listes / Synthèses |
                 +-----------------------------+
```

Principes structurants :

- l'API précède l'interface ;
- PostgreSQL/PostGIS constitue la source principale ;
- les fichiers JSON ne sont utilisés qu'en secours, en mode démonstration ou en sortie de génération ;
- le dashboard ne doit pas accéder directement à la base ;
- les imports doivent passer par validation et normalisation ;
- les modules métier doivent partager le même référentiel.

## 5. Cycle de vie des données

Le cycle de vie cible des données est le suivant :

```text
Collecte terrain
    ↓
Import
    ↓
Validation
    ↓
Normalisation
    ↓
Référentiel
    ↓
Base PostgreSQL/PostGIS
    ↓
API
    ↓
Dashboard
    ↓
Analyse
    ↓
Décision
    ↓
Rapport
```

### Collecte terrain

Les données peuvent provenir de missions terrain, fichiers administratifs, relevés GPS, photos géolocalisées, fichiers KMZ/KML, données partenaires, opérateurs, institutions ou sources ouvertes.

### Import

L'import doit permettre la prévisualisation, la validation de structure, le contrôle des champs obligatoires et la détection d'anomalies.

### Validation

La validation contrôle la cohérence des codes, noms, rattachements, géométries, doublons, champs manquants et formats.

### Normalisation

La normalisation transforme les données vers les nomenclatures FDSU et les structures internes sans altérer silencieusement les anomalies.

### Référentiel

Les données validées alimentent le référentiel national et les modules métier.

### Base PostgreSQL/PostGIS

La base conserve les données structurées, géométries, métadonnées, historiques, scores, profils et relations.

### API

L'API expose les données à l'interface, aux futurs systèmes interconnectés et aux rapports.

### Dashboard

Le dashboard permet la consultation, l'analyse, la cartographie, la priorisation et la production d'exports.

### Analyse, décision et rapport

Les résultats sont interprétés par les utilisateurs puis transformés en décisions, recommandations et rapports.

## 6. Référentiel national

La hiérarchie cible du référentiel national est :

```text
Zone FDSU
  > Province
    > Territoire
      > Ville
      > Secteur
      > Chefferie
      > Collectivité
        > Groupement
          > Localité
            > Village si applicable
              > Site FDSU
```

Le référentiel doit permettre :

- une identification unique des entités ;
- une hiérarchie claire et navigable ;
- la recherche par code, nom, type et rattachement ;
- la consultation en liste avant l'ouverture de fiche ;
- le rattachement des sites, missions, profils et données de connectivité ;
- l'historique des corrections ;
- la conservation des sources et métadonnées.

Les Zones FDSU constituent le premier niveau métier. Elles structurent la lecture opérationnelle nationale et peuvent coexister avec la hiérarchie administrative officielle.

## 7. Intelligence FDSU

L'Intelligence FDSU est le cerveau du système. Elle transforme les données en priorités, recommandations, scores, scénarios et analyses comparatives.

Elle comprend :

- matrice de priorisation ;
- KPI ;
- Score FDSU ;
- simulations ;
- scénarios ;
- comparaisons ;
- classements ;
- recommandations ;
- historique des décisions ;
- versions des règles ;
- justification des résultats ;
- identification des données manquantes.

### Matrice de priorisation

La matrice de priorisation combine des critères territoriaux, techniques, sociaux, économiques et opérationnels. Elle doit pouvoir être ajustée selon les politiques du FDSU.

Exemples de critères :

- population ;
- absence de couverture 4G ;
- faible score de connectivité ;
- présence de services publics ;
- potentiel agricole ;
- potentiel commercial ;
- niveau d'enclavement ;
- absence d'électricité ;
- existence ou absence de site FDSU ;
- présence de missions ou observations terrain.

### Score FDSU

Le Score FDSU mesure la priorité relative d'une localité, d'un territoire ou d'une zone. Il ne remplace pas la décision humaine ; il éclaire la décision.

Le score doit toujours être accompagné :

- des critères utilisés ;
- des pondérations ;
- des données manquantes ;
- de la justification ;
- de la date de calcul ;
- de la version des règles.

### Règles paramétrables

Toutes les règles doivent être paramétrables. Aucun poids ne doit être codé en dur dans l'interface ou dans les requêtes.

Les paramètres doivent pouvoir évoluer selon :

- les orientations stratégiques ;
- les contraintes budgétaires ;
- les priorités nationales ;
- les exigences des partenaires ;
- les retours terrain ;
- les nouvelles données disponibles.

## 8. Gouvernance des données

La gouvernance des données garantit la confiance dans la plateforme.

Elle couvre :

- qualité ;
- validation ;
- traçabilité ;
- historique ;
- sources ;
- métadonnées ;
- contrôle qualité ;
- gestion des anomalies.

### Qualité

Chaque donnée doit pouvoir être évaluée selon son origine, sa complétude, sa cohérence et sa fraîcheur.

### Validation

La validation doit distinguer les données acceptées, rejetées, à compléter et à vérifier manuellement.

### Traçabilité

Chaque donnée critique doit conserver sa source, sa date d'import, son auteur ou producteur, et son statut de validation.

### Historique

Les modifications importantes doivent être historisées : code, nom, rattachement, géométrie, statut, score, fiche, site ou mission.

### Sources et métadonnées

Les sources doivent être documentées : organisme, fichier, date, version, format, méthode de collecte, licence ou restriction.

### Gestion des anomalies

Les anomalies ne doivent pas être masquées. Elles doivent être visibles dans les rapports, tableaux d'import, fiches et workflows de validation.

## 9. Interopérabilité

La plateforme doit être pensée pour échanger avec des systèmes nationaux, techniques et géospatiaux.

Interopérabilités cibles :

- CAID ;
- ARPTC ;
- INS ;
- OpenStreetMap ;
- QGIS ;
- ArcGIS ;
- GeoServer ;
- Google Earth ;
- Excel ;
- KML ;
- KMZ ;
- GeoJSON ;
- Shapefile ;
- API REST.

Principes :

- utiliser des formats ouverts lorsque possible ;
- conserver la géométrie dans PostGIS ;
- exposer des API documentées ;
- permettre l'export de couches filtrées ;
- importer sans écraser les sources officielles ;
- garder les métadonnées d'origine ;
- distinguer données officielles, pilotes, terrain et démonstration.

## 10. Évolutivité

La plateforme doit être conçue pour évoluer au-delà du dashboard web initial.

Modules et capacités futures :

- application Android ;
- application iOS ;
- mode hors ligne ;
- synchronisation différée ;
- photos géolocalisées ;
- collecte GPS ;
- drone ;
- imagerie satellite ;
- intelligence artificielle ;
- prévisions ;
- alertes ;
- tableaux de bord DG ;
- notifications ;
- workflows de validation ;
- intégration des opérateurs télécoms ;
- rapports automatisés.

L'évolutivité doit rester compatible avec le principe central : la base PostgreSQL/PostGIS et l'API constituent le noyau de vérité de la plateforme.

## 11. Sécurité

La plateforme doit intégrer progressivement une politique de sécurité adaptée à une plateforme nationale.

Domaines de sécurité :

- utilisateurs ;
- rôles ;
- permissions ;
- audit ;
- journalisation ;
- sauvegardes ;
- versionnement.

### Utilisateurs et rôles

Les accès doivent être structurés par profils : Administrateur, Analyste SIG, Technicien terrain, Responsable projet, Direction Générale et partenaires autorisés.

### Permissions

Les permissions doivent distinguer consultation, import, validation, modification, suppression, export, administration et publication.

### Audit et journalisation

Les actions sensibles doivent être journalisées : connexion, import, validation, modification, suppression, export, génération de rapport et changement de paramètres.

### Sauvegardes

La plateforme doit prévoir des sauvegardes régulières de la base, des fichiers importés, des documents, des photos et des rapports.

### Versionnement

Les règles de scoring, nomenclatures, référentiels, rapports et imports structurants doivent être versionnés.

## 12. Vision 2030

À l'horizon 2030, le SIG-FDSU RDC doit devenir :

- le référentiel géographique officiel du FDSU ;
- le système officiel de planification des investissements numériques ;
- le système officiel de suivi des missions ;
- le système officiel de suivi des sites ;
- le système officiel de suivi des Centres Communautaires Numériques ;
- le système officiel d'aide à la décision ;
- l'outil national de consolidation des données territoriales utiles au service universel ;
- une plateforme de dialogue technique avec les partenaires, institutions et opérateurs.

La vision 2030 suppose une plateforme robuste, documentée, sécurisée, interopérable, évolutive et gouvernée. Elle doit soutenir les décisions de long terme, les arbitrages budgétaires, la planification territoriale et le suivi des impacts.

## 13. Principes de développement

Tous les futurs développements doivent respecter les principes suivants :

- architecture fonctionnelle ;
- nomenclature officielle FDSU ;
- codification FDSU ;
- couleurs officielles Zones FDSU ;
- liste avant fiche ;
- aucun bouton mort ;
- aucune donnée inventée ;
- API avant interface ;
- PostgreSQL/PostGIS comme source principale ;
- JSON uniquement comme secours ;
- traçabilité des sources ;
- validation avant import définitif ;
- anomalies visibles ;
- documentation maintenue ;
- compatibilité avec les rapports et exports ;
- évolutivité sans rupture du référentiel national.

### Codification FDSU

La codification cible obligatoire pour les sites et objets opérationnels est :

```text
FDSU_<CODE_ZONE>_<CODE_PROVINCE>_<CODE_TERRITOIRE>_<CODE_SITE>
```

Exemple :

```text
FDSU_ND_05_001_001
```

Cette codification doit être utilisée dans les sites FDSU, missions, données de couverture réseau, télécommunications, rapports et imports/exports.

### Couleurs officielles Zones FDSU

Les couleurs officielles des Zones FDSU doivent être appliquées de manière cohérente :

| Code | Zone | Couleur |
|---|---|---|
| OT | Ouest | Jaune |
| CE | Centre | Rose |
| SD | Sud | Vert sombre |
| ND | Nord | Gris olive |
| ET | Est | Bleu |

## 14. Conclusion

Le SIG-FDSU RDC est conçu comme une plateforme nationale évolutive, destinée à accompagner durablement le développement de la connectivité, des infrastructures numériques et des Centres Communautaires Numériques en République Démocratique du Congo.

Il doit devenir un outil institutionnel de référence pour connaître le territoire, mesurer les inégalités numériques, prioriser les investissements, suivre les projets, documenter les missions et produire des rapports stratégiques.

Ce schéma directeur fixe la vision cible de la plateforme. Il doit guider les développements futurs, les choix techniques, l'organisation des données, les règles d'interface, la gouvernance, l'interopérabilité et l'évolution progressive du SIG-FDSU RDC vers un système national d'aide à la décision.

Le document est destiné à la Direction Générale, aux partenaires techniques et financiers, aux équipes SIG, aux responsables projet, aux techniciens terrain et aux futurs développeurs du projet.
