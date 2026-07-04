# SIG-FDSU RDC v1.0 - Charte Nationale des Données

## Préambule

La présente Charte Nationale des Données définit les règles de gouvernance applicables à l'ensemble des données utilisées, produites, importées, validées, publiées et archivées dans le SIG-FDSU RDC.

Elle constitue le cadre institutionnel de référence pour garantir que les données mobilisées par la plateforme nationale soient fiables, traçables, pérennes, interopérables et exploitables pour la décision publique.

La charte s'applique à toutes les données du SIG-FDSU RDC : référentiel administratif, Zones FDSU, profils territoriaux, connectivité, sites FDSU, missions terrain, documents, photos, rapports, imports, exports, couches géographiques et données d'aide à la décision.

## 1. Objectifs

La charte a pour objectif de définir les principes de gestion des données du SIG-FDSU RDC.

Elle vise à garantir :

- **unicité** : une même entité ne doit pas être représentée par plusieurs objets concurrents non maîtrisés ;
- **cohérence** : les relations, codes, noms, géométries et rattachements doivent être compatibles avec les référentiels validés ;
- **qualité** : chaque donnée doit pouvoir être évaluée selon des critères explicites ;
- **traçabilité** : chaque donnée doit conserver sa source, son historique et son statut ;
- **pérennité** : les identifiants, codifications et métadonnées doivent rester stables dans le temps ;
- **interopérabilité** : les données doivent pouvoir être échangées avec les outils, formats et institutions partenaires.

Toute donnée utilisée dans le SIG-FDSU RDC doit répondre à une finalité métier : connaissance du territoire, planification, suivi des infrastructures numériques, analyse de connectivité, mission terrain, rapport ou aide à la décision.

## 2. Sources officielles

Les données du SIG-FDSU RDC peuvent provenir de plusieurs sources reconnues. Chaque source doit être identifiée, documentée et conservée dans les métadonnées.

Sources reconnues :

- FDSU ;
- CAID ;
- INS ;
- ARPTC ;
- Ministères ;
- Gouvernorats ;
- Missions terrain ;
- Google Earth ;
- OpenStreetMap ;
- Imagerie satellite ;
- Excel ;
- KMZ ;
- KML ;
- GeoJSON ;
- Shapefile.

Chaque donnée doit conserver au minimum :

- nom de la source ;
- organisme producteur ;
- fichier ou système d'origine ;
- date de production si connue ;
- date d'import ;
- version ;
- format ;
- méthode de collecte si disponible ;
- niveau de confiance.

Une donnée sans source documentée ne doit pas être considérée comme officielle. Elle peut être utilisée comme donnée provisoire, pilote ou à vérifier, mais son statut doit être explicitement affiché.

## 3. Identifiants

Chaque entité gérée par la plateforme doit disposer d'un identifiant unique, stable et permanent.

Entités concernées :

- Province ;
- Territoire ;
- Collectivité ;
- Groupement ;
- Localité ;
- Village ;
- Site ;
- Mission ;
- Photo ;
- Document.

Règles applicables :

- un identifiant ne doit pas être réutilisé pour une autre entité ;
- un identifiant ne doit pas changer lors d'une simple correction de nom ;
- un identifiant supprimé ou désactivé doit rester historisé ;
- les imports doivent chercher à réconcilier les entités existantes avant de créer de nouveaux objets ;
- les identifiants techniques internes doivent être distingués des codes métier FDSU.

Les identifiants permanents constituent le socle de la traçabilité, des historiques, des exports, des rapports et de l'interopérabilité.

## 4. Codification officielle

La codification officielle FDSU est obligatoire pour les sites et objets opérationnels nécessitant un code métier FDSU.

Format obligatoire :

```text
FDSU_<ZONE>_<PROVINCE>_<TERRITOIRE>_<SITE>
```

Exemple :

```text
FDSU_ND_05_001_001
```

Aucune autre codification ne doit être utilisée pour les objets relevant de la nomenclature FDSU.

La codification officielle doit être appliquée dans :

- Sites FDSU ;
- Missions ;
- Couverture réseau ;
- Télécommunications ;
- Rapports ;
- Import/Export ;
- tableaux de bord ;
- fiches détaillées.

Toute modification d'un code FDSU doit être exceptionnelle, justifiée, historisée et validée par un profil autorisé.

## 5. Convention de nommage

Les noms officiels doivent être conservés dans leur forme institutionnelle de référence.

Règles générales :

- conserver les accents officiels ;
- conserver les traits d'union officiels ;
- éviter les transformations arbitraires en majuscules ;
- éviter les substitutions non documentées ;
- éviter les underscores dans les noms métier ;
- ne pas supprimer les caractères distinctifs lorsqu'ils appartiennent au nom officiel ;
- stocker les noms alternatifs ou historiques dans des champs dédiés, pas à la place du nom officiel.

Exemple :

Toujours :

```text
Haut-Uélé
```

Jamais :

```text
HAUT UELE
Haut Uele
haut_uele
```

Lorsque les sources divergent, la plateforme doit conserver la valeur source, la valeur normalisée et l'anomalie ou justification de rapprochement.

## 6. Coordonnées GPS

Les coordonnées géographiques doivent respecter le système de référence suivant :

- système géodésique : **WGS84** ;
- référence spatiale : **EPSG:4326** ;
- latitude en degrés décimaux ;
- longitude en degrés décimaux ;
- altitude en mètres si disponible.

Règles de saisie et validation :

- latitude comprise entre -90 et 90 ;
- longitude comprise entre -180 et 180 ;
- altitude facultative mais numérique si fournie ;
- nombre recommandé de décimales : 6 pour latitude et longitude ;
- les coordonnées nulles, inversées ou hors territoire attendu doivent être signalées ;
- toute correction de coordonnées doit être historisée.

Les coordonnées GPS doivent être stockées de manière compatible avec PostGIS et exportables en GeoJSON, KML, KMZ et Shapefile.

## 7. Géométries

Les géométries représentent les objets spatiaux du SIG-FDSU RDC.

Types autorisés :

- **Point** : localité, site, mission ponctuelle, infrastructure ;
- **Ligne** : axe, liaison, corridor, tracé technique ;
- **Polygone** : zone, emprise, limite simple ;
- **MultiPolygon** : province, territoire, collectivité ou zone composée de plusieurs surfaces.

Règles de validation :

- la géométrie doit être compatible avec le type d'objet ;
- la géométrie doit utiliser EPSG:4326 ;
- les polygones doivent être fermés et valides ;
- les géométries vides doivent être signalées ;
- les géométries invalides doivent être conservées comme anomalies et non corrigées silencieusement ;
- les transformations de géométrie doivent être documentées ;
- les imports doivent distinguer géométrie source et géométrie validée lorsque nécessaire.

Une entité peut exister sans géométrie si la source ne la fournit pas. Dans ce cas, l'interface doit afficher **donnée à compléter**.

## 8. Qualité

Chaque objet doit posséder ou pouvoir recevoir un score qualité.

Indicateurs de qualité :

- **complétude** : proportion de champs obligatoires ou attendus renseignés ;
- **cohérence** : compatibilité entre nom, code, rattachement, géométrie et source ;
- **unicité** : absence de doublon non résolu ;
- **validité** : respect des formats, types et domaines de valeurs ;
- **actualité** : fraîcheur de la donnée ;
- **fiabilité** : niveau de confiance accordé à la source ou à la validation.

Le score qualité doit être interprété comme un indicateur d'aide à la validation, non comme une preuve absolue.

Les objets à faible qualité doivent être visibles dans les rapports d'anomalies et dans les workflows de validation.

## 9. Métadonnées

Toutes les entités doivent conserver les métadonnées nécessaires à leur gouvernance.

Métadonnées minimales :

- source ;
- date création ;
- date modification ;
- créateur ;
- validateur ;
- version ;
- niveau de confiance.

Métadonnées complémentaires recommandées :

- fichier d'origine ;
- lot d'import ;
- statut de validation ;
- commentaire de validation ;
- date de publication ;
- licence ou restriction d'utilisation ;
- méthode de collecte ;
- précision géographique ;
- historique des rapprochements.

Les métadonnées doivent être exploitables dans les filtres, exports, rapports et audits.

## 10. Gestion des anomalies

Les anomalies sont des écarts entre une donnée importée, attendue, validée ou publiée.

Types d'anomalies :

- orphelins ;
- doublons ;
- codes manquants ;
- géométries invalides ;
- coordonnées invalides ;
- noms incohérents ;
- rattachements incohérents ;
- champs obligatoires manquants ;
- format non conforme ;
- source non documentée.

Chaque anomalie doit recevoir :

- identifiant ;
- niveau ;
- statut ;
- responsable ;
- date.

Niveaux recommandés :

- critique ;
- majeur ;
- mineur ;
- information.

Statuts recommandés :

- détectée ;
- en analyse ;
- à corriger ;
- validée provisoirement ;
- corrigée ;
- rejetée ;
- acceptée avec justification.

Aucune anomalie ne doit être masquée par une correction automatique non documentée.

## 11. Historique

Toutes les modifications importantes doivent être historisées.

Éléments à historiser :

- création ;
- modification ;
- validation ;
- publication ;
- correction de code ;
- correction de nom ;
- changement de rattachement ;
- changement de géométrie ;
- ajout ou suppression de document ;
- changement de score qualité ;
- changement de score FDSU ;
- changement de statut.

Règle fondamentale :

```text
Aucune suppression définitive.
```

Lorsqu'une donnée n'est plus active, elle doit être désactivée, archivée ou marquée comme obsolète, mais son historique doit rester consultable.

## 12. Sauvegardes

La pérennité des données repose sur une politique de sauvegarde claire.

Objets à sauvegarder :

- base PostgreSQL/PostGIS ;
- exports ;
- fichiers importés ;
- documents ;
- photos ;
- rapports ;
- scripts ;
- configuration ;
- documentation ;
- historique Git.

Dispositifs recommandés :

- sauvegardes PostgreSQL régulières ;
- exports périodiques des référentiels critiques ;
- archivage des fichiers sources ;
- gestion du code et de la documentation par Git ;
- conservation des versions publiées ;
- vérification régulière de la capacité de restauration.

Une sauvegarde non testée ne doit pas être considérée comme fiable.

## 13. Sécurité

Les accès aux données doivent être encadrés par des rôles et permissions.

Niveaux d'accès :

- lecture ;
- écriture ;
- validation ;
- administration ;
- journalisation.

Principes :

- un utilisateur ne doit disposer que des droits nécessaires à sa mission ;
- les actions sensibles doivent être journalisées ;
- les imports, validations et publications doivent être traçables ;
- les exports contenant des données sensibles doivent être contrôlés ;
- les administrateurs doivent pouvoir auditer les modifications ;
- les accès partenaires doivent être limités aux périmètres autorisés.

Les rôles doivent permettre de distinguer au minimum Administrateur, Analyste SIG, Technicien terrain, Responsable projet et Direction générale.

## 14. Validation

Le workflow de validation des données est le suivant :

```text
Import
  ↓
Contrôle
  ↓
Validation
  ↓
Publication
  ↓
Utilisation
```

### Import

Le fichier ou flux est chargé, identifié, prévisualisé et associé à une source.

### Contrôle

Le système vérifie la structure, les champs obligatoires, les formats, les codes, la géométrie, les doublons et les rattachements.

### Validation

Un utilisateur autorisé examine les anomalies, accepte, rejette, corrige ou marque les données comme provisoires.

### Publication

Les données validées deviennent disponibles pour les modules métier, cartes, fiches, rapports et exports.

### Utilisation

Les données publiées peuvent être utilisées pour l'aide à la décision, les sites FDSU, les missions, les rapports et la planification.

## 15. Principes fondamentaux

Les principes suivants sont obligatoires :

- ne jamais inventer une donnée ;
- toute donnée doit être traçable ;
- toute donnée doit être versionnée ;
- toute donnée doit être documentée ;
- toute donnée doit être reproductible ;
- toute donnée doit être validable ;
- toute anomalie doit rester visible jusqu'à traitement ;
- toute correction doit être justifiée ;
- toute source doit être conservée ;
- toute publication doit pouvoir être auditée.

Lorsqu'une donnée est inconnue, absente ou non validée, l'interface et les exports doivent afficher un statut explicite, par exemple **donnée à compléter**.

## 16. Conclusion

La Charte Nationale des Données constitue la référence officielle de gouvernance des données du SIG-FDSU RDC.

Elle fixe les règles applicables à l'identification, la codification, la qualité, la traçabilité, la validation, l'historisation, la sécurité, l'interopérabilité et la pérennité des données.

Tout développement futur devra respecter cette charte. Toute nouvelle fonctionnalité, tout nouveau module, tout nouveau flux d'import et toute nouvelle règle de calcul devront être évalués selon leur conformité aux principes définis dans le présent document.

La qualité du SIG-FDSU RDC dépend de la qualité de ses données. Cette charte garantit que la plateforme nationale reste un outil fiable, durable et institutionnellement exploitable au service de la connectivité et du développement numérique en République Démocratique du Congo.
