# DNAI v2.0 — Dictionnaire national des abréviations institutionnelles

## Statut et rôle

Le DNAI est la source officielle et transversale de normalisation terminologique du SIG-FDSU RDC. Il transforme un libellé institutionnel avant son passage dans le National Semantic Classification Engine (NSCE). Les moteurs métier ne développent plus eux-mêmes les abréviations.

## Architecture et pipeline

`Texte brut → détection des identifiants techniques → nettoyage → reconnaissance morphologique → DNAI → texte normalisé → NSCE → classification métier → confiance → justification`

- `data/business/dnai_dictionary_v1.json` est le registre publié et versionné.
- `api/services/dnai_service.py` applique les règles, résout le contexte et produit l’explicabilité.
- `api/services/national_semantic_classification_engine.py` consomme exclusivement le texte produit par DNAI avant ses règles métier.
- Les données sources ne sont jamais modifiées.

Chaque résultat conserve le texte original, le texte nettoyé, la règle et l’expression régulière, l’expansion, le référentiel de contexte, la catégorie, la famille, la confiance, le statut et la justification.

## Taxonomie

Le dictionnaire est organisé en familles : Administration, Éducation, Santé, Télécommunications et Institutions. Une entrée publiée porte un identifiant stable, une expansion officielle, ses variantes et synonymes, les référentiels concernés, leur priorité, sa source, sa version et sa confiance.

La version 2.0 publie les formes validées nécessaires au référentiel CENI : EP, INST, IT, ISP, ISTM, ISDR, ISC, ISAM, CS, HGR, CSR, HOP et BAT ADM, ainsi que les institutions dont la dénomination est documentée. `EDAC`, `ISGEA`, `IS` et `ISIPA` restent en validation : aucune expansion n’est inventée.

## Reconnaissance morphologique et sécurité

La règle EP numérotée accepte notamment `EP1`, `E.P2`, `EP N°1`, `EP NO2` et `EP-1`, uniquement en tête du libellé. Les zéros initiaux sont supprimés sans perdre le numéro. Les identifiants `CENI-EP-001`, `REF_EP_001`, `CODE_EP2` et `FDSU_EP_001` sont détectés avant le nettoyage et restent non classifiés.

Les accents, la casse, les points, espaces et séparateurs sont normalisés. Les variantes sanitaires explicites sont classées avec une confiance élevée.

## Résolution contextuelle

Dans le référentiel CENI, `CS` signifie par défaut `COMPLEXE SCOLAIRE`. La présence d’un indice sanitaire explicite — santé, sanitaire, clinique, maternité, dispensaire, hôpital, HGR, CSR, centre hospitalier, centre médical ou poste de santé — donne priorité à `CENTRE DE SANTÉ`. Cette décision est exclusivement prise dans DNAI.

## Discovery Engine et gouvernance

Le Discovery Engine scanne les libellés importés, compte les sigles inconnus, conserve des contextes représentatifs et produit des propositions sans les publier. Le cycle obligatoire est :

`Découverte → Analyse → Validation humaine → Publication → Utilisation par les moteurs`

Une découverte ne reçoit jamais automatiquement une expansion. La publication nécessite une source institutionnelle vérifiable et une mise à jour versionnée du dictionnaire.

## API

- `GET /api/dnai/search`
- `GET /api/dnai/expand/{abbr}`
- `POST /api/dnai/normalize`
- `GET /api/dnai/statistics`
- `GET /api/dnai/discover`
- `GET /api/dnai/pending-validations`

Le corps de normalisation est `{ "text": "EP1 MFUAMBA", "referential": "CENI" }`.

## Dashboard

La route `#dnai`, sous Référentiels, présente les abréviations publiées, variantes, familles, ambiguïtés, couverture par référentiel, recherche plein texte et propositions en attente de validation.

## Stratégie d’évolution

1. Produire un rapport de découverte à chaque import.
2. Faire valider les expansions par le responsable du référentiel et le métier concerné.
3. Ajouter source, version et tests négatifs avant publication.
4. Mesurer les populations avant/après par référentiel.
5. Préserver les cas ambigus dans la file de validation humaine.
