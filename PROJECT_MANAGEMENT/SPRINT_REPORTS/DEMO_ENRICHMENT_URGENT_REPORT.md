# Sprint urgent - Démo hiérarchie : enrichissement intelligent des fiches

Date : 2026-07-05

## Objectif

Préparer une version de démonstration où les fiches prioritaires ne paraissent plus vides lorsque des informations existent dans les données internes ou dans des sources publiques autorisées. Les ajouts restent des propositions de démonstration à valider et ne modifient pas les référentiels officiels.

## Réalisations

- Mode `DEMO_ENRICHMENT_MODE = true` activé côté dashboard.
- Cache de démonstration ajouté : `data/demo_enrichment_cache.json`.
- Route CNCT ajoutée : `GET /knowledge/demo-enrichment`.
- Fusion d'affichage ajoutée dans les fiches : les données officielles restent prioritaires, les propositions ne complètent que les champs vides.
- Badge ajouté dans les fiches : `Enrichissement CNCT démo`, `Proposition à valider`, confiance, date et source.
- Libellé vide de fiche remplacé par `À compléter` dans les sections métier de démonstration.
- Les compteurs relationnels calculés existants sont conservés et restent affichables via l'API.

## Entités enrichies

- Tshopo
- Kinshasa
- Haut-Uele
- Dungu
- Banalia
- Wando
- Isiro
- Bas-Uele
- Équateur
- Kasaï
- Kongo Central

## Sources utilisées

- Référentiel interne SIG-FDSU : `data/reports/province_official/province_fact_sheets.json`
- Wikipedia Tshopo : `https://fr.wikipedia.org/wiki/Tshopo_(province)`
- Wikipedia Kinshasa : `https://en.wikipedia.org/wiki/Kinshasa`
- Wikipedia Haut-Uele : `https://fr.wikipedia.org/wiki/Haut-Uele`
- Wikipedia Dungu : `https://fr.wikipedia.org/wiki/Dungu_(territoire)`
- Wikipedia Banalia : `https://fr.wikipedia.org/wiki/Banalia_(territoire)`
- Wikipedia Isiro : `https://fr.wikipedia.org/wiki/Isiro`
- Wikipedia Bas-Uele : `https://fr.wikipedia.org/wiki/Bas-Uele`
- Wikipedia Équateur : `https://fr.wikipedia.org/wiki/Équateur_(province)`
- Wikipedia Kasaï : `https://en.wikipedia.org/wiki/Kasaï_Province`
- Wikipedia Kongo Central : `https://fr.wikipedia.org/wiki/Kongo_Central`

Les pages Wikipedia sont utilisées comme sources complémentaires. Certaines pages citent CENI, CAID, OCHA, INS ou d'autres références institutionnelles ; ces données restent marquées comme propositions à valider.

## Champs complétés

Champs couverts selon disponibilité par entité :

- description
- chef-lieu
- superficie
- population
- subdivision
- géographie
- climat
- activités économiques principales
- activités économiques secondaires
- particularités
- défis
- potentiel agricole
- potentiel minier
- potentiel commercial
- potentiel touristique
- potentiel numérique
- sources

## Champs encore manquants

- Services publics détaillés par localité.
- Connectivité réseau validée par ARPTC.
- Infrastructures détaillées par territoire ou groupement.
- Données statistiques fines pour Wando.
- Données économiques sectorielles institutionnelles pour Kasaï, Wando et certaines entités territoriales.

## Niveaux de confiance

- `70%` : données croisées entre référentiel interne SIG-FDSU et source publique complémentaire.
- `45%` : source publique complémentaire avec références institutionnelles citées.
- `35%` : information administrative minimale à valider par une source institutionnelle locale.

## Sécurité des données

- Aucune écriture dans `provinces`, `territoires`, `collectivites`, `groupements`, `localites`, `territorial_profiles` ou `knowledge`.
- Aucune publication automatique.
- Les informations enrichies sont affichées comme propositions à valider.
- Le cache peut être retiré sans impact sur les données officielles.

## Tests effectués

- Validation JSON du cache : OK.
- Compilation Python des routes/services CNCT : OK.
- Tests ciblés : `tests/test_documentary_enrichment_engine.py` : 3 tests passés.
- Vérification de la route `GET /knowledge/demo-enrichment` dans les tests FastAPI : OK.

Limite : `node` n'est pas installé dans l'environnement, donc la vérification syntaxique JS par `node --check` n'a pas pu être exécutée.

## Limites

- Les sources publiques consultées pendant cette passe sont surtout complémentaires.
- Les données web ne sont pas injectées dans la base officielle.
- Le serveur FastAPI déjà lancé doit être redémarré pour exposer la nouvelle route.
- La démonstration dépend du chargement API du cache CNCT.

## Recommandations après démonstration

- Valider manuellement les propositions prioritaires et les insérer dans `territorial_enrichment_suggestions`.
- Ajouter les sources institutionnelles directes CAID/INS/ARPTC/OCHA lorsque les connecteurs web seront stabilisés.
- Ajouter un écran de validation CNCT dédié aux données de démonstration.
- Transformer le cache en file de propositions avec journal de validation.
- Compléter les services publics, connectivité et infrastructures par territoire/localité.
