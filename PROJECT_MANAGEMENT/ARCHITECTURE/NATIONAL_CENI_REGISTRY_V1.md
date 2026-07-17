# Référentiel National CENI — Architecture v1.0

## Finalité

Le Référentiel National CENI fournit une identité déterministe, une provenance, une classification prudente, une qualité géométrique et un rattachement administratif aux 32 221 objets du KMZ officiel. Il reste séparé des actifs FDSU.

## Contrat institutionnel

```text
asset_domain = INSTITUTIONAL
institution  = CENI
asset_type   = CENI_SITE
asset_type != FDSU
```

`CENI_SITE` est ici le type technique du registre dédié. La nature fonctionnelle reste portée par `normalized_category`, souvent `UNCLASSIFIED`. Aucun actif CENI n’est injecté dans les tables ou règles FDSU.

## Modèle métier

Chaque objet conserve notamment :

- `asset_uid`, déterministe à partir du hash source, du fingerprint et de l’occurrence ;
- `source_record_id`, distinct d’un simple numéro de ligne ;
- `aliases`, `fingerprint`, `legacy_ids` ;
- `source_category`, `normalized_category`, justification et confiance ;
- longitude, latitude et état géométrique ;
- rattachement Province, Territoire, Collectivité, Groupement et Localité ;
- provenance et SHA-256 du KMZ ;
- `raw_properties`, équivalent fichier du futur champ JSONB ;
- état et groupe de doublon, sans action automatique.

## Taxonomie extensible

`CENI_SITE`, `VOTING_CENTER`, `REGISTRATION_CENTER`, `PUBLIC_BUILDING`, `SCHOOL`, `HEALTH_FACILITY`, `ADMINISTRATIVE_BUILDING`, `RELIGIOUS_BUILDING`, `OTHER`, `UNCLASSIFIED`.

Les règles v1 n’utilisent que des termes explicites du nom. Une nouvelle règle doit être testée, documentée et ne peut reclasser silencieusement les données historiques.

## Rattachement administratif

L’ordre contractuel est : codes officiels, noms normalisés, `ST_Contains`, `ST_Intersects`, proximité, puis `unresolved`. Le KMZ ne contenant ni codes ni noms administratifs, la v1 commence réellement à l’étape géométrique :

1. inclusion dans une Collectivité officielle, qui fournit Province et Territoire ;
2. inclusion dans une Province officielle si aucune Collectivité ne contient le point ;
3. `unresolved` sinon.

La v1 n’invente pas de Groupement ou de Localité par voisinage. Ces champs restent `null` jusqu’à une règle de proximité explicitement validée.

## Déduplication

Le fingerprint combine le nom normalisé et les coordonnées. Les doublons exacts reçoivent un groupe et des identifiants liés. Tous les enregistrements sont conservés. Les cas « même infrastructure, plusieurs fonctions » ne peuvent pas être fusionnés automatiquement.

## API

- `GET /api/ceni/sites`
- `GET /api/ceni/sites/{id}`
- `GET /api/ceni/statistics`
- `GET /api/ceni/data-quality`
- `GET /api/ceni/categories`
- `GET /api/ceni/map`
- `GET /api/ceni/import-batches`

## Dashboard

La route `#ceni-registry` expose les indicateurs, la provenance et le hash source, les filtres, la recherche, une carte, un tableau et une fiche. La carte limite par défaut le volume rendu par l’API pour préserver l’interface.

## Compatibilité préparatoire

### National Asset Registry

Le contrat `INSTITUTIONAL/CENI` est exposé sans injecter les objets dans le NFAR existant. Une future publication devra garder `asset_type != FDSU`.

### NTIE

Les seules dimensions prévues sont le nombre de sites, la densité, la qualité et la couverture documentaire. Aucun score, seuil ou pondération n’est ajouté.

### Spatial Decision Graph

La chaîne future `Site FDSU → Site CENI → Population → Santé → Télécom → Routes` est documentée mais `sdg_relations_active=false`. Aucune relation ou contribution de score n’est créée en v1.

## Rollback et idempotence

Le batch est identifié par le SHA-256 source. Une réexécution produit les mêmes identifiants. Le rollback est volontairement manuel et limité aux artefacts générés du batch ; le KMZ source n’est jamais modifié.
