# Sprint 3.4 - Moteur intelligent d'enrichissement documentaire CNCT

Date : 2026-07-05

## Objectif

Mettre en place un moteur CNCT capable d'auditer les donnees internes, d'extraire des informations documentaires sourcées et de préparer des propositions d'enrichissement, sans collecte web automatique et sans modification directe des référentiels officiels.

## Objectifs réalisés

- Audit documentaire local ajouté sur les répertoires `data`, `docs`, `PROJECT_MANAGEMENT`, `database`, `imports` et `resources`.
- Moteur interne d'extraction légère ajouté pour les formats texte structurés : JSON, GeoJSON, Markdown, TXT et CSV.
- Connecteurs publics préparés mais désactivés pour CAID, INS, Ministères RDC, ARPTC, OCHA, FAO, UNICEF, UNDP, OpenStreetMap et Wikipedia.
- Sources interdites déclarées : blogs, Facebook, TikTok, YouTube, forums, contenus générés par IA, sources sans auteur institutionnel.
- Fusion des propositions identiques par entité, champ et valeur proposée.
- Score de confiance implémenté : CAID +40, INS +40, Ministères +35, ARPTC +35, Banque mondiale +30, FAO/OCHA/UNDP/UNICEF +25, OSM/Wikipedia +10, plafond 100.
- Tableau de bord CNCT enrichi avec l'origine des données, la confiance, le nombre de sources et le statut de validation.
- Script expérimental ajouté en mode simulation par défaut.

## Fichiers modifiés ou ajoutés

- `api/services/documentary_enrichment_service.py`
- `api/routes/knowledge.py`
- `dashboard/app.js`
- `dashboard/index.html`
- `dashboard/styles.css`
- `database/documentary_enrichment_engine.py`
- `tests/test_documentary_enrichment_engine.py`
- `PROJECT_MANAGEMENT/SPRINT_REPORTS/SPRINT_3_4_INTELLIGENT_DOCUMENTARY_ENGINE.md`

## Endpoints ajoutés

- `GET /knowledge/documentary/audit`
- `GET /knowledge/documentary/origins`
- `GET /knowledge/documentary/internal-suggestions`
- `GET /knowledge/documentary/status`

Ces endpoints exposent l'audit, les origines de données, les suggestions internes préparées et l'état complet du moteur. Ils ne publient aucune donnée dans les tables officielles.

## Audit documentaire

Résultat de simulation :

- Fichiers totaux détectés : 115
- Fichiers documentaires supportés : 97
- Rapports internes exploitables : 87
- Connecteurs binaires préparés : 10
- Fichiers analysés pendant le test : 20
- Propositions internes préparées : 26
- Insertions en base : 0
- Tables officielles modifiées : 0

Principales sources internes détectées :

- `data/reports/locality_official/locality_referential_official.json`
- `data/sources/ceni/pdf/ceni_rapport_annuel_2023_2024.pdf`
- `data/reports/collectivity_official/collectivity_referential_official.json`
- `data/reports/territory_hierarchy/territoires_hierarchie_kmz.report.json`
- `data/reports/locality_official/locality_fact_sheets.json`
- `data/generated/collectivites.geojson`
- `data/reports/province_official/province_referential_official.json`
- `data/generated/zones_fdsu.geojson`
- `data/reports/groupement_official/groupement_referential_official.json`

## Moteur interne

Le moteur extrait aujourd'hui les champs structurés suivants lorsqu'ils sont présents dans les documents internes :

- `chef_lieu`
- `superficie`
- `population`
- `activites_economiques_principales`
- `activites_economiques_secondaires`
- `particularites`
- `defis`
- `potentiel_agricole`
- `potentiel_minier`
- `potentiel_commercial`
- `potentiel_touristique`
- `services_publics`
- `connectivite`
- `infrastructures`

Cas validé : la fiche interne de la province Tshopo produit une proposition `chef_lieu = Kisangani` depuis `data/reports/province_official/province_fact_sheets.json`.

## Moteur internet

La collecte internet automatique reste désactivée.

Les connecteurs sont déclarés avec les sources autorisées et leurs poids de confiance, mais aucune recherche publique n'est lancée par défaut. Une exécution web future devra continuer à écrire uniquement dans `territorial_enrichment_suggestions`, après conservation de la source, de l'URL, de la date de consultation, du résumé et du statut `proposé`.

## Fusion et confiance

Les propositions identiques sont fusionnées selon :

- entité concernée
- champ concerné
- valeur proposée normalisée

La fusion conserve les sources distinctes et recalcule un score plafonné à 100.

## Contraintes de sécurité maintenues

- Aucune donnée externe n'est injectée dans les fiches officielles.
- Aucune écriture dans `territorial_profiles`, `knowledge`, `localites`, `territoires`, `provinces`, `collectivites` ou `groupements`.
- Les propositions sont préparées avec statut `proposé`.
- La publication directe reste désactivée.
- La validation humaine reste obligatoire.

## Tests effectués

- Compilation :
  - `.\.venv\Scripts\python.exe -m py_compile api\services\documentary_enrichment_service.py api\routes\knowledge.py database\documentary_enrichment_engine.py`
- Tests ciblés :
  - `.\.venv\Scripts\python.exe -m pytest tests\test_documentary_enrichment_engine.py -q`
  - Résultat : 3 tests passés.
- Simulation moteur :
  - `.\.venv\Scripts\python.exe database\documentary_enrichment_engine.py --max-files 20`
  - Résultat : 26 propositions préparées, aucune insertion.

## Limites restantes

- Les PDF, DOCX, XLSX, KML et KMZ sont audités et déclarés comme connecteurs préparés, mais leur parsing métier complet reste à industrialiser.
- L'extraction actuelle privilégie les libellés structurés et évite les inférences libres.
- Les connecteurs web publics ne sont pas exécutés dans cet environnement.
- Les propositions internes préparées ne sont pas encore insérées automatiquement dans la file de validation, sauf exécution explicite du script avec `--commit`.
- Le serveur FastAPI déjà lancé doit être redémarré pour exposer les nouvelles routes si une instance était active avant cette livraison.

## Recommandations Sprint 3.5

- Ajouter un parseur PDF/DOCX/XLSX robuste avec journal d'extraction.
- Ajouter un écran CNCT dédié aux propositions documentaires internes.
- Ajouter une table d'historique des recherches et analyses documentaires.
- Ajouter un workflow de comparaison avant validation.
- Ajouter une exécution web contrôlée par liste blanche, avec quota par entité et preuve de source.
- Ajouter une détection automatique des champs déjà présents dans PostgreSQL afin d'éviter les propositions doublons.
