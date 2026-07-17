# Moteur national de classification sémantique en français v1

## Objet et principes

Ce composant transversal enrichit un nom source par des règles lexicales françaises explicites. Il ne modifie jamais le nom, la catégorie ou les propriétés brutes. Une absence de preuve conserve la catégorie « Non classifié ». Le registre métier versionné est `data/business/semantic_classification_rules_fr_v1.json`; l’exécution est assurée par `api/services/national_semantic_classification_engine.py`.

Le résultat comprend le nom source et normalisé, la catégorie source, le code interne et son libellé français, la méthode, la règle, le mot-clé, la confiance numérique et française, la justification, la version du moteur, la date, le statut de revue et les propriétés brutes.

## Normalisation

La normalisation Unicode supprime les diacritiques pour la comparaison, unifie la casse, les apostrophes, la ponctuation et les espaces. Elle rapproche notamment `EP`, `E.P.` et `É.P.`, ou `CENTRE DE SANTÉ` et `CENTRE DE SANTE`. Le champ `source_name` reste inchangé; le résultat distinct est `normalized_name`.

## Priorité et conflits

La catégorie officielle source, lorsqu’elle existe, prévaut. Les règles sont ensuite parcourues dans l’ordre du registre : santé explicite, école explicite, administration, religieux, marché, télécommunications, énergie, transport, bâtiment public, fonctions électorales. Les contraintes `requires_any` et `excludes_any` empêchent les déductions hors contexte.

`CS` seul est ambigu et reste « Non classifié ». Il n’est classé qu’en présence d’un indice sanitaire ou scolaire supplémentaire. Ces décisions reçoivent une confiance moyenne (0,76) et le statut « À vérifier ».

## Confiance et explicabilité

| Intervalle | Libellé |
|---|---|
| 0,95–1,00 | Très élevée |
| 0,85–0,94 | Élevée |
| 0,65–0,84 | Moyenne |
| 0,40–0,64 | Faible |
| < 0,40 | Insuffisante |

Chaque décision identifie la règle et le mot-clé. Une règle ambiguë ne peut pas produire une confiance élevée. Le moteur est déterministe et idempotent à registre et date d’exécution identiques.

## Gouvernance et validation humaine

Les statuts préparés sont « Non revu », « Validé », « Rejeté » et « À vérifier ». La v1 n’offre aucune écriture destructive ni validation automatique. Toute évolution lexicale exige une nouvelle version du registre, des tests de non-régression, un rapport avant/après et une validation métier. Les codes internes restent stables; les interfaces présentent exclusivement les libellés français.

## Intégration CENI et réutilisation

Le service CENI appelle le moteur transversal et stocke l’enrichissement dans l’artefact généré `ceni_registry_v1.json`; le KMZ officiel reste intact. Les endpoints historiques sont conservés et quatre lectures additives exposent statistiques, règles, revue et détail de classification. Le registre peut accueillir de nouveaux domaines (justice, agriculture, énergie ou santé) sans intégrer de logique CENI dans le moteur.

## Limites

Le moteur établit une vraisemblance lexicale, pas la fonction juridique réelle d’un site. Il ne déduit ni propriété, ni fonction électorale, ni rattachement administratif. Les toponymes isolés, opérateurs commerciaux sans indice d’infrastructure et occurrences ambiguës restent non classifiés.
