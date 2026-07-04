# SIG-FDSU RDC v1.0 - Master Data Model

## 1. Présentation

Le Master Data Model du SIG-FDSU RDC constitue le modèle de données officiel de la plateforme nationale. Il définit les entités de référence, leurs relations, les règles métier, les géométries, les métadonnées, les contraintes d'intégrité et les principes de structuration de la base PostgreSQL/PostGIS.

Ce document est la référence unique pour :

- PostgreSQL ;
- PostGIS ;
- FastAPI ;
- Dashboard ;
- Import ;
- Export ;
- Rapports ;
- Intelligence FDSU.

Le modèle de données doit permettre à toutes les couches de la plateforme de partager la même compréhension des objets métier : zones, provinces, territoires, collectivités, groupements, localités, sites, missions, profils territoriaux, connectivité, documents, photos, imports, anomalies, utilisateurs, rôles et règles décisionnelles.

Le Master Data Model n'est pas seulement un dictionnaire technique. Il est le contrat de cohérence entre la base de données, l'API, les modules fonctionnels, les imports, les exports et les rapports décisionnels.

## 2. Principes

Le modèle de données repose sur les règles fondamentales suivantes :

- une donnée existe une seule fois ;
- toutes les données sont reliées ;
- toutes les données sont historisées ;
- toutes les données possèdent une source ;
- toutes les données possèdent un identifiant unique ;
- toutes les données possèdent des métadonnées.

Principes complémentaires :

- PostgreSQL/PostGIS est la source principale ;
- l'API FastAPI est le point d'accès applicatif ;
- le dashboard ne doit pas accéder directement à la base ;
- les fichiers JSON servent uniquement de secours, d'échange ou de génération ;
- les imports ne doivent pas écraser silencieusement les données existantes ;
- les anomalies doivent rester visibles ;
- les règles métier doivent être paramétrables ;
- les pondérations de score ne doivent pas être codées en dur ;
- les géométries doivent être validées et indexées ;
- les entités supprimées doivent être archivées, non effacées définitivement.

## 3. Modèle conceptuel

Schéma conceptuel principal :

```text
Zone FDSU
   |
   v
Province
   |
   v
Territoire
   |
   v
Collectivité
   |
   v
Groupement
   |
   v
Localité
   |
   v
Site FDSU
   |
   v
Mission
```

Liens transverses :

```text
                         +------------------------+
                         |   Profils territoriaux |
                         +-----------+------------+
                                     |
                                     v
Zone > Province > Territoire > Collectivité > Groupement > Localité > Site > Mission
                                     ^
                                     |
        +----------------------------+-----------------------------+
        |                            |                             |
        v                            v                             v
+---------------+          +------------------+          +------------------+
| Connectivité  |          | Services publics |          | Activités éco.   |
+---------------+          +------------------+          +------------------+
        |                            |                             |
        +----------------------------+-----------------------------+
                                     |
                                     v
                          +-------------------+
                          | Score / Décision  |
                          +-------------------+
                                     |
        +----------------------------+-----------------------------+
        |                            |                             |
        v                            v                             v
+---------------+          +------------------+          +------------------+
| Documents     |          | Photos           |          | Historique       |
+---------------+          +------------------+          +------------------+
```

Règle de lecture :

- les entités administratives structurent le territoire ;
- les profils enrichissent les entités ;
- les sites et missions documentent l'action opérationnelle ;
- les documents, photos et historiques assurent la preuve et la traçabilité ;
- l'Intelligence FDSU utilise les profils, services, connectivité et scores pour produire des priorités.

## 4. Dictionnaire complet des tables

Les tables ci-dessous constituent le dictionnaire cible du SIG-FDSU RDC. Certaines tables existent déjà, d'autres sont prévues pour les versions futures.

### zones

| Élément | Description |
|---|---|
| Nom | `zones` |
| Description | Zones FDSU nationales : ND, SD, CE, OT, ET. |
| Clé primaire | `id` |
| Clés étrangères | aucune ou parent optionnel selon modélisation générique |
| Colonnes principales | `id`, `code`, `nom`, `type`, `parent_id`, `geom`, `source`, `quality_score`, `status`, `metadata`, `created_at`, `updated_at` |
| Types SQL | `BIGINT`, `TEXT`, `GEOMETRY`, `JSONB`, `TIMESTAMP` |
| Contraintes | code unique, nom obligatoire, géométrie valide si fournie |
| Index | index code, index GIST sur géométrie |
| Description métier | Premier niveau métier de lecture nationale du FDSU. |

### provinces

| Élément | Description |
|---|---|
| Nom | `provinces` |
| Description | Provinces de la RDC rattachées aux Zones FDSU. |
| Clé primaire | `id` |
| Clés étrangères | `parent_id` vers `zones.id` ou `zone_id` selon modèle physique |
| Colonnes principales | `id`, `code`, `nom`, `type`, `parent_id`, `latitude`, `longitude`, `geom`, `source`, `quality_score`, `status`, `metadata`, `created_at`, `updated_at` |
| Types SQL | `BIGINT`, `TEXT`, `DOUBLE PRECISION`, `GEOMETRY(MULTIPOLYGON,4326)`, `JSONB` |
| Contraintes | code unique, rattachement zone requis, géométrie valide si publiée |
| Index | code, parent, GIST |
| Description métier | Niveau administratif national de référence. |

### territoires

| Élément | Description |
|---|---|
| Nom | `territoires` |
| Description | Territoires rattachés aux provinces. |
| Clé primaire | `id` |
| Clés étrangères | `parent_id` vers `provinces.id` ou `province_id` selon modèle physique |
| Colonnes principales | `id`, `code`, `nom`, `type`, `parent_id`, `geom`, `source`, `quality_score`, `status`, `metadata`, `nb_sites_reference`, `created_at`, `updated_at` |
| Types SQL | `BIGINT`, `TEXT`, `GEOMETRY(MULTIPOLYGON,4326)`, `JSONB`, `INTEGER` |
| Contraintes | code unique dans le référentiel, province obligatoire |
| Index | code, parent, GIST |
| Description métier | Niveau clé pour la planification territoriale et les analyses de priorité. |

### villes

| Élément | Description |
|---|---|
| Nom | `villes` |
| Description | Villes administratives ou entités urbaines reconnues. |
| Clé primaire | `id` |
| Clés étrangères | `parent_id` vers `provinces.id` ou entité administrative parent |
| Colonnes principales | `id`, `code`, `nom`, `type`, `parent_id`, `geom`, `source`, `quality_score`, `status`, `metadata` |
| Types SQL | `BIGINT`, `TEXT`, `GEOMETRY`, `JSONB` |
| Contraintes | nom obligatoire, source documentée |
| Index | code, parent, GIST |
| Description métier | Niveau urbain à rattacher au référentiel national. |

### collectivites

| Élément | Description |
|---|---|
| Nom | `collectivites` |
| Description | Collectivités, secteurs, chefferies ou entités équivalentes selon le référentiel. |
| Clé primaire | `id` |
| Clés étrangères | `parent_id` vers `territoires.id` ou `territoire_id` |
| Colonnes principales | `id`, `code`, `nom`, `type`, `parent_id`, `geom`, `source`, `quality_score`, `status`, `metadata` |
| Types SQL | `BIGINT`, `TEXT`, `GEOMETRY(MULTIPOLYGON,4326)`, `JSONB` |
| Contraintes | rattachement territoire requis |
| Index | code, parent, GIST |
| Description métier | Niveau administratif intermédiaire reliant territoires et groupements. |

### groupements

| Élément | Description |
|---|---|
| Nom | `groupements` |
| Description | Groupements rattachés aux collectivités. |
| Clé primaire | `id` |
| Clés étrangères | `parent_id` vers `collectivites.id` ou `collectivite_id` |
| Colonnes principales | `id`, `code`, `nom`, `type`, `parent_id`, `geom`, `source`, `quality_score`, `status`, `metadata` |
| Types SQL | `BIGINT`, `TEXT`, `GEOMETRY(MULTIPOLYGON,4326)` ou `GEOMETRY(POINT,4326)` selon source, `JSONB` |
| Contraintes | rattachement collectivité requis lorsque connu |
| Index | code, parent, GIST |
| Description métier | Niveau de rattachement immédiat des localités. |

### localites

| Élément | Description |
|---|---|
| Nom | `localites` |
| Description | Localités, villages ou lieux habités rattachés aux groupements. |
| Clé primaire | `id` |
| Clés étrangères | `parent_id` vers `groupements.id` |
| Colonnes principales | `id`, `code`, `nom`, `type`, `parent_id`, `latitude`, `longitude`, `altitude`, `geom`, `source`, `quality_score`, `status`, `metadata`, `created_at`, `updated_at` |
| Types SQL | `BIGINT`, `TEXT`, `DOUBLE PRECISION`, `GEOMETRY(POINT,4326)`, `JSONB` |
| Contraintes | rattachement groupement requis lorsque connu, coordonnées valides si fournies |
| Index | code, parent, GIST |
| Description métier | Entité centrale pour les CCN, profils territoriaux, services, connectivité et priorisation. |

### sites

| Élément | Description |
|---|---|
| Nom | `sites` |
| Description | Sites FDSU, infrastructures numériques, points techniques ou sites planifiés. |
| Clé primaire | `id` |
| Clés étrangères | `parent_id` vers `localites.id` ou `village_id` selon modèle physique |
| Colonnes principales | `id`, `code`, `nom`, `type`, `parent_id`, `geom`, `source`, `quality_score`, `status`, `programme`, `annee_planification`, `phase`, `priorite`, `metadata` |
| Types SQL | `BIGINT`, `TEXT`, `INTEGER`, `GEOMETRY(POINT,4326)`, `JSONB` |
| Contraintes | code FDSU obligatoire pour site opérationnel, rattachement territorial requis |
| Index | code, parent, statut, GIST |
| Description métier | Objet de suivi des infrastructures FDSU. |

### missions

| Élément | Description |
|---|---|
| Nom | `missions` |
| Description | Missions terrain liées aux sites, localités, projets ou validations. |
| Clé primaire | `id` |
| Clés étrangères | `site_id`, `parent_id` ou rattachement métier selon type de mission |
| Colonnes principales | `id`, `titre` ou `nom`, `description`, `date_debut`, `date_fin`, `site_id`, `status`, `metadata`, `geom` |
| Types SQL | `BIGINT`, `TEXT`, `DATE`, `GEOMETRY(POINT,4326)` ou `GEOMETRY(LINESTRING,4326)` |
| Contraintes | mission rattachée à un objet métier ou territoire |
| Index | site, dates, statut, GIST |
| Description métier | Trace les activités terrain, audits, collectes et vérifications. |

### documents

| Élément | Description |
|---|---|
| Nom | `documents` |
| Description | Documents associés aux missions, sites ou entités. |
| Clé primaire | `id` |
| Clés étrangères | `mission_id`, `site_id` ou entité cible selon modèle futur |
| Colonnes principales | `id`, `nom`, `type`, `chemin`, `mission_id`, `created_at`, `metadata` |
| Types SQL | `BIGINT`, `TEXT`, `TIMESTAMP`, `JSONB` |
| Contraintes | chemin obligatoire, source documentée |
| Index | mission, type |
| Description métier | Pièces justificatives et supports documentaires. |

### photos

| Élément | Description |
|---|---|
| Nom | `photos` |
| Description | Photos terrain, photos de sites, missions ou équipements. |
| Clé primaire | `id` |
| Clés étrangères | `mission_id`, `site_id` ou entité cible selon modèle futur |
| Colonnes principales | `id`, `nom`, `caption`, `chemin`, `mission_id`, `latitude`, `longitude`, `geom`, `created_at`, `metadata` |
| Types SQL | `BIGINT`, `TEXT`, `DOUBLE PRECISION`, `GEOMETRY(POINT,4326)`, `JSONB` |
| Contraintes | fichier obligatoire, coordonnées valides si géolocalisée |
| Index | mission, site, GIST si géométrie |
| Description métier | Preuve visuelle et documentation terrain. |

### import_batches

| Élément | Description |
|---|---|
| Nom | `import_batches` |
| Description | Lots d'import de données. |
| Clé primaire | `id` |
| Clés étrangères | utilisateur ou source si disponible |
| Colonnes principales | `id`, `filename`, `source`, `format`, `status`, `rows_total`, `rows_inserted`, `rows_rejected`, `created_at`, `metadata` |
| Types SQL | `BIGINT`, `TEXT`, `INTEGER`, `TIMESTAMP`, `JSONB` |
| Contraintes | statut obligatoire, source documentée |
| Index | source, statut, date |
| Description métier | Assure la traçabilité des imports. |

### import_errors

| Élément | Description |
|---|---|
| Nom | `import_errors` |
| Description | Erreurs et anomalies détectées pendant un import. |
| Clé primaire | `id` |
| Clés étrangères | `batch_id` vers `import_batches.id` |
| Colonnes principales | `id`, `batch_id`, `row_number`, `entity`, `field`, `error_type`, `message`, `status`, `created_at`, `metadata` |
| Types SQL | `BIGINT`, `TEXT`, `INTEGER`, `TIMESTAMP`, `JSONB` |
| Contraintes | batch obligatoire, message obligatoire |
| Index | batch, status, entity |
| Description métier | Permet le suivi et la correction des anomalies d'import. |

### territorial_profiles

| Élément | Description |
|---|---|
| Nom | `territorial_profiles` |
| Description | Profils territoriaux des localités ou territoires. |
| Clé primaire | `id` |
| Clés étrangères | `localite_id`, `territoire_id` |
| Colonnes principales | `id`, `localite_id`, `territoire_id`, `population`, `niveau_enclavement`, `source`, `observation`, `created_at`, `updated_at` |
| Types SQL | `BIGINT`, `VARCHAR`, `TEXT`, `TIMESTAMP` |
| Contraintes | au moins un rattachement localité ou territoire |
| Index | localite, territoire |
| Description métier | Base socio-territoriale de l'aide à la décision. |

### connectivity_profiles

| Élément | Description |
|---|---|
| Nom | `connectivity_profiles` |
| Description | Profils de connectivité par localité ou territoire. |
| Clé primaire | `id` |
| Clés étrangères | `localite_id`, `territoire_id` |
| Colonnes principales | `couverture_2g`, `couverture_3g`, `couverture_4g`, `couverture_5g`, `score_connectivite`, `source`, `observation` |
| Types SQL | `BOOLEAN`, `NUMERIC(6,2)`, `TEXT`, `TIMESTAMP` |
| Contraintes | valeurs booléennes, score borné cible 0-100 |
| Index | localite, territoire |
| Description métier | Mesure la couverture et les déficits de connectivité. |

### public_services

| Élément | Description |
|---|---|
| Nom | `public_services` |
| Description | Présence de services publics et équipements de base. |
| Clé primaire | `id` |
| Clés étrangères | `localite_id`, `territoire_id` |
| Colonnes principales | `centre_sante`, `ecole_primaire`, `ecole_secondaire`, `marche`, `electricite`, `source`, `observation` |
| Types SQL | `BOOLEAN`, `TEXT`, `TIMESTAMP` |
| Contraintes | booléens ou donnée à compléter |
| Index | localite, territoire |
| Description métier | Évalue les besoins et capacités de service public. |

### economic_activities

| Élément | Description |
|---|---|
| Nom | `economic_activities` |
| Description | Activités et potentiels économiques. |
| Clé primaire | `id` |
| Clés étrangères | `localite_id`, `territoire_id` |
| Colonnes principales | `activite_principale`, `activite_secondaire`, `potentiel_agricole`, `potentiel_minier`, `potentiel_commercial`, `potentiel_numerique`, `score_potentiel`, `source`, `observation` |
| Types SQL | `VARCHAR`, `NUMERIC(6,2)`, `TEXT`, `TIMESTAMP` |
| Contraintes | score borné cible 0-100, source obligatoire si publié |
| Index | localite, territoire |
| Description métier | Décrit le potentiel économique utile à la priorisation. |

### development_challenges

| Élément | Description |
|---|---|
| Nom | `development_challenges` |
| Description | Défis, contraintes et niveau d'enclavement. |
| Clé primaire | `id` |
| Clés étrangères | `localite_id`, `territoire_id` |
| Colonnes principales | `niveau_enclavement`, `defis`, `source`, `observation`, `created_at`, `updated_at` |
| Types SQL | `VARCHAR`, `TEXT`, `TIMESTAMP` |
| Contraintes | défi documenté par source si utilisé pour scoring |
| Index | localite, territoire |
| Description métier | Qualifie les contraintes d'accès et de développement. |

### fdsu_priority_scores

| Élément | Description |
|---|---|
| Nom | `fdsu_priority_scores` |
| Description | Scores FDSU et recommandations de priorisation. |
| Clé primaire | `id` |
| Clés étrangères | `localite_id`, `territoire_id` |
| Colonnes principales | `score_connectivite`, `score_potentiel`, `score_priorite_fdsu`, `recommandation`, `source`, `observation` |
| Types SQL | `NUMERIC(6,2)`, `TEXT`, `TIMESTAMP` |
| Contraintes | score cible 0-100, règles de calcul versionnées |
| Index | localite, territoire, score_priorite |
| Description métier | Sert au classement des localités et territoires prioritaires. |

### users

| Élément | Description |
|---|---|
| Nom | `users` |
| Description | Utilisateurs de la plateforme. |
| Clé primaire | `id` |
| Clés étrangères | rôle principal ou table de liaison utilisateurs-rôles |
| Colonnes principales | `id`, `username`, `email`, `full_name`, `status`, `created_at`, `updated_at`, `metadata` |
| Types SQL | `BIGINT`, `TEXT`, `TIMESTAMP`, `JSONB` |
| Contraintes | username unique, email unique si utilisé |
| Index | username, email, status |
| Description métier | Contrôle l'accès, l'audit et la responsabilité des actions. |

### roles

| Élément | Description |
|---|---|
| Nom | `roles` |
| Description | Rôles applicatifs. |
| Clé primaire | `id` |
| Clés étrangères | aucune |
| Colonnes principales | `id`, `code`, `nom`, `description`, `status`, `created_at` |
| Types SQL | `BIGINT`, `TEXT`, `TIMESTAMP` |
| Contraintes | code unique |
| Index | code |
| Description métier | Définit les profils Administrateur, Analyste SIG, Technicien terrain, Responsable projet, Direction générale. |

### permissions

| Élément | Description |
|---|---|
| Nom | `permissions` |
| Description | Permissions applicatives. |
| Clé primaire | `id` |
| Clés étrangères | rôle ou table de liaison rôles-permissions |
| Colonnes principales | `id`, `code`, `module`, `action`, `description`, `created_at` |
| Types SQL | `BIGINT`, `TEXT`, `TIMESTAMP` |
| Contraintes | couple module/action unique |
| Index | code, module |
| Description métier | Encadre lecture, écriture, validation, administration et export. |

### audit_logs

| Élément | Description |
|---|---|
| Nom | `audit_logs` |
| Description | Journal d'audit des actions sensibles. |
| Clé primaire | `id` |
| Clés étrangères | `user_id` si disponible |
| Colonnes principales | `id`, `user_id`, `action`, `entity`, `entity_id`, `before_data`, `after_data`, `created_at`, `ip_address`, `metadata` |
| Types SQL | `BIGINT`, `TEXT`, `JSONB`, `TIMESTAMP` |
| Contraintes | action obligatoire, date obligatoire |
| Index | user, entity, action, date |
| Description métier | Assure la traçabilité et la sécurité institutionnelle. |

## 5. Relations

Relations administratives principales :

- une Zone possède plusieurs Provinces ;
- une Province appartient à une Zone ;
- une Province possède plusieurs Territoires ;
- un Territoire appartient à une Province ;
- un Territoire possède plusieurs Collectivités ;
- une Collectivité appartient à un Territoire ;
- une Collectivité possède plusieurs Groupements ;
- un Groupement appartient à une Collectivité ;
- un Groupement possède plusieurs Localités ;
- une Localité appartient à un Groupement.

Relations opérationnelles :

- une Localité peut posséder plusieurs Sites ;
- un Site peut posséder plusieurs Missions ;
- une Mission peut posséder plusieurs Photos ;
- une Mission peut posséder plusieurs Documents ;
- un Site peut posséder plusieurs Documents et Photos dans le modèle cible ;
- une Localité peut posséder un Profil territorial ;
- une Localité peut posséder un Profil de connectivité ;
- une Localité peut posséder plusieurs informations de services publics ;
- une Localité ou un Territoire peut posséder un score FDSU ;
- une anomalie d'import appartient à un lot d'import ;
- un utilisateur peut être responsable d'une validation, d'un import ou d'une correction.

Règle cible :

```text
Toute relation métier importante doit être explicite en base.
```

## 6. Géométries PostGIS

Les géométries utilisent WGS84 / EPSG:4326.

| Entité | Géométrie cible |
|---|---|
| Province | `MULTIPOLYGON` |
| Territoire | `MULTIPOLYGON` |
| Collectivité | `MULTIPOLYGON` |
| Groupement | `MULTIPOLYGON` |
| Localité | `POINT` |
| Site | `POINT` |
| Mission | `POINT` ou `LINESTRING` |

Règles :

- toutes les géométries publiées doivent être valides ;
- les points doivent respecter latitude et longitude ;
- les polygones doivent être fermés ;
- les MultiPolygons doivent être utilisés pour les entités administratives multi-surfaces ;
- les géométries source peuvent être conservées séparément si une normalisation est appliquée ;
- une géométrie absente doit être affichée comme donnée à compléter ;
- les anomalies géométriques doivent être documentées.

Index GIST :

- chaque colonne géométrique utilisée en cartographie doit disposer d'un index GIST ;
- les requêtes de proximité et d'intersection doivent utiliser PostGIS ;
- les exports GeoJSON/KML/KMZ/Shapefile doivent partir des géométries validées.

## 7. Métadonnées

Toutes les tables doivent comporter, lorsque pertinent :

- `created_at` ;
- `updated_at` ;
- `created_by` ;
- `validated_by` ;
- `source` ;
- `version` ;
- `confidence_level` ;
- `status`.

Rôle des métadonnées :

- identifier l'origine de la donnée ;
- suivre l'état de validation ;
- permettre l'audit ;
- faciliter les exports ;
- distinguer données officielles, pilotes, terrain et démonstration ;
- garantir la reproductibilité.

Les tables qui ne contiennent pas encore ces champs doivent les intégrer progressivement dans les futures migrations.

## 8. Tables métier futures

Le modèle doit préparer l'intégration des tables futures suivantes :

| Table | Objet métier |
|---|---|
| `ccn` | Centres Communautaires Numériques |
| `fiber_network` | Réseau fibre optique |
| `mobile_operator` | Opérateurs mobiles |
| `radio_links` | Faisceaux hertziens ou liaisons radio |
| `towers` | Pylônes et tours |
| `coverage_measurements` | Mesures terrain de couverture |
| `backbone` | Backbone national ou régional |
| `budget` | Budgets associés aux projets |
| `investment_projects` | Projets d'investissement numérique |
| `maintenance` | Maintenance des infrastructures |
| `incidents` | Incidents techniques ou opérationnels |
| `equipment` | Équipements techniques |
| `inventories` | Inventaires terrain |
| `contracts` | Contrats et conventions |
| `partners` | Partenaires techniques, financiers ou institutionnels |

Ces tables devront respecter les mêmes règles : identifiant unique, source, métadonnées, historique, statut, relations explicites et audit.

## 9. Intelligence FDSU

L'Intelligence FDSU regroupe les données de calcul, règles et résultats qui alimentent l'aide à la décision.

Objets à modéliser :

- matrice ;
- KPI ;
- scores ;
- historique ;
- versions ;
- règles ;
- simulations ;
- scénarios ;
- comparaisons ;
- recommandations.

Règles obligatoires :

- toutes les règles doivent être stockées en base ;
- les pondérations ne doivent jamais être codées directement dans le logiciel ;
- chaque calcul doit être rattaché à une version de règle ;
- chaque score doit pouvoir être justifié ;
- chaque recommandation doit pouvoir être reproduite ;
- les anciennes versions de règles doivent rester consultables.

Tables cibles possibles :

- `decision_rules` ;
- `decision_rule_versions` ;
- `decision_weights` ;
- `kpi_definitions` ;
- `kpi_values` ;
- `simulation_runs` ;
- `scenario_results` ;
- `recommendation_history`.

## 10. Vues SQL

Le modèle prévoit des vues SQL pour simplifier les usages API, dashboard, rapports et exports.

Vues cibles :

- `vw_dashboard_summary` ;
- `vw_localites_prioritaires` ;
- `vw_territoires_prioritaires` ;
- `vw_sites_ccn` ;
- `vw_couverture` ;
- `vw_kpi` ;
- `vw_anomalies`.

Rôle des vues :

- consolider les jointures fréquentes ;
- isoler les modules des détails physiques ;
- accélérer les rapports ;
- standardiser les exports ;
- garantir une lecture métier stable ;
- préparer la matérialisation lorsque nécessaire.

Les vues critiques pourront être matérialisées si le volume de données ou la complexité PostGIS l'exige.

## 11. API

Le modèle de données doit se refléter dans l'API FastAPI et dans les écrans du dashboard.

Chaîne cible :

```text
Tables
  ↓
Endpoints FastAPI
  ↓
Écrans Dashboard
  ↓
Carte
  ↓
Fiche
```

Exemple :

```text
Table provinces
  ↓
GET /provinces
  ↓
Module Référentiel
  ↓
Carte
  ↓
Fiche Province
```

Correspondances cibles :

| Table ou vue | Endpoint | Module |
|---|---|---|
| `zones` | `GET /zones` | Référentiel / Cartographie |
| `provinces` | `GET /provinces` | Référentiel |
| `territoires` | `GET /territoires` | Référentiel |
| `collectivites` | `GET /collectivites` | Référentiel |
| `groupements` | `GET /groupements` | Référentiel |
| `localites` | `GET /localites` | Référentiel / Aide décision |
| `sites` | `GET /sites` | Sites FDSU |
| `missions` | `GET /missions` | Missions terrain |
| `vw_localites_prioritaires` | `GET /decision/localites-prioritaires` | Aide à la décision |
| `vw_territoires_prioritaires` | `GET /decision/territoires-prioritaires` | Aide à la décision |
| `import_batches` | `GET /imports` | Import |

Règle : aucune logique métier structurante ne doit être dupliquée entre API et dashboard. Les calculs de référence doivent être portés par la base, l'API ou les services métier.

## 12. Règles d'intégrité

Les règles d'intégrité garantissent la cohérence de la plateforme.

### CASCADE

À utiliser avec prudence pour les entités dépendantes strictes, par exemple les erreurs d'un lot d'import.

### RESTRICT

À privilégier pour empêcher la suppression d'une entité administrative encore utilisée.

### SET NULL

À utiliser lorsqu'un rattachement peut devenir inconnu sans supprimer l'objet, par exemple un document dont l'entité source est archivée.

### UNIQUE

À appliquer aux codes officiels, codes FDSU, usernames, emails et identifiants métier.

### CHECK

À utiliser pour les domaines de valeurs :

- score entre 0 et 100 ;
- latitude entre -90 et 90 ;
- longitude entre -180 et 180 ;
- statut dans une liste autorisée ;
- type de couverture dans un domaine contrôlé.

### NOT NULL

À appliquer aux champs indispensables : identifiant, nom, code lorsque officiel, source lorsque publié, statut et dates de création.

### Validation des codes

Les codes doivent respecter la nomenclature officielle et les règles de format FDSU.

### Validation des géométries

Les géométries doivent être compatibles avec le type d'objet et valides selon PostGIS.

### Validation des coordonnées

Les coordonnées doivent respecter WGS84 / EPSG:4326 et les bornes géographiques.

## 13. Performance

Le modèle doit anticiper les volumes nationaux, les couches géographiques et les requêtes décisionnelles.

Principes de performance :

- indexer les clés étrangères ;
- indexer les codes et statuts ;
- utiliser des index GIST pour les géométries ;
- paginer toutes les listes API ;
- limiter les exports volumineux ;
- mettre en cache les référentiels stables ;
- matérialiser les vues coûteuses si nécessaire ;
- optimiser les requêtes PostGIS ;
- éviter les jointures inutiles dans le dashboard ;
- préparer les filtres côté API ou base.

Optimisation PostGIS :

- utiliser `ST_Intersects`, `ST_Within`, `ST_DWithin` avec index GIST ;
- simplifier les géométries lourdes pour l'affichage web ;
- conserver les géométries complètes pour l'analyse et l'export ;
- distinguer couches de consultation et couches de calcul.

## 14. Sauvegarde

La sauvegarde fait partie du modèle de gouvernance des données.

Objets à sauvegarder :

- dump PostgreSQL ;
- tables PostGIS ;
- fichiers sources ;
- exports ;
- documents ;
- photos ;
- scripts ;
- migrations Alembic ;
- documentation ;
- configuration ;
- version Git.

Règles :

- les dumps PostgreSQL doivent être réguliers ;
- les restaurations doivent être testées ;
- les fichiers sources doivent être archivés ;
- Git doit conserver les versions du code, des migrations et des documents ;
- les exports officiels doivent être datés et versionnés ;
- les sauvegardes critiques doivent être stockées hors du poste local.

## 15. Roadmap du modèle

### Version 1.0 - Référentiel

Stabiliser le référentiel administratif, les tables principales, les documents de gouvernance et les premières migrations.

### Version 1.1 - Profils

Structurer les profils territoriaux, services publics, activités économiques, défis et scores de base.

### Version 1.2 - Connectivité

Renforcer les profils de couverture, mesures réseau, opérateurs, technologies et scores de connectivité.

### Version 1.3 - Sites

Stabiliser les Sites FDSU, codification, statuts, technologies, équipements, missions et documents.

### Version 1.4 - CCN

Ajouter les Centres Communautaires Numériques, leur implantation, suivi, statut, impact et rattachement aux localités.

### Version 1.5 - Intelligence FDSU

Modéliser les règles, pondérations, KPI, simulations, scénarios, recommandations et historiques de décision.

## 16. Règles d'or

Règles fondamentales :

- une donnée ne doit jamais être dupliquée ;
- une relation doit toujours être explicite ;
- toutes les entités doivent être documentées ;
- toutes les modifications doivent être historisées ;
- toutes les géométries doivent être valides ;
- toutes les données doivent être traçables ;
- toutes les règles métier doivent être paramétrables ;
- les pondérations ne doivent jamais être codées en dur ;
- les anomalies ne doivent jamais être masquées ;
- les données manquantes ne doivent jamais être inventées ;
- les exports doivent refléter les données validées ou clairement marquées comme provisoires.

Le modèle de données constitue la référence technique officielle du SIG-FDSU RDC. Tout développement futur, toute migration, tout import, tout endpoint API et tout module dashboard devront respecter ce Master Data Model.
