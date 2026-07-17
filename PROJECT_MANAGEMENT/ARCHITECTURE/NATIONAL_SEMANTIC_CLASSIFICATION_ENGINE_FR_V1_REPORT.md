# Rapport final — Classification sémantique française CENI v1

Date d’exécution : 16 juillet 2026. Moteur : `fr-1.0.0`. Population : 32 221 objets.

| Indicateur | Avant | Après |
|---|---:|---:|
| Non classifiés | 29 517 | 6 959 |
| Écoles | 1 148 | 23 604 |
| Santé | 1 524 | 1 565 |
| Administration publique | 9 | 21 |
| Édifices religieux | 17 | 25 |
| Marchés | 0 | 0 |
| Bâtiments publics | 6 | 28 |
| Autres catégories | 0 | 19 |

La réduction nette est de 22 558 objets, soit 76,42 % des objets auparavant non classifiés. Les autres catégories après traitement sont : infrastructures routières ou de transport 12, télécommunications 5 et énergie 2. Aucune occurrence ne justifie la catégorie Marché selon les règles v1.

## Règles principales

| Règle | Occurrences |
|---|---:|
| Préfixe EP | 17 387 |
| École explicite par nom | 3 314 |
| Santé explicite | 1 554 |
| Préfixe INST | 1 462 |
| Forme scolaire explicite | 1 422 |
| Bâtiment public explicite | 28 |
| Religieux explicite | 25 |

## Confiance et revue

Après l’audit de précision, 6 366 classifications ont une confiance très élevée, 18 877 élevée, 19 moyenne et 6 959 insuffisante. EP est ramené à 0,92 et INST à 0,86. Les 19 cas moyens correspondent à `CS` désambiguïsé par un contexte scolaire explicite; ils sont marqués « À vérifier ». Les 6 959 noms sans règle fiable restent « Non classifié ».

## Performance et contrôles

L’enrichissement complet, incluant lecture et réécriture de l’artefact JSON de 32 221 lignes, s’est exécuté en 42,7 secondes. Les 13 tests Python du moteur et de l’intégration CENI passent en 13,53 secondes. Les tests couvrent normalisation, priorités, ambiguïté CS, conservation de source, justification, confiance, stabilité, idempotence et endpoints.

## Intégrité

- KMZ avant : `C3762911DF483D0B291145AF31CF612A30332039BB3D7BFD86FA894C650ABE9D`
- KMZ après : `C3762911DF483D0B291145AF31CF612A30332039BB3D7BFD86FA894C650ABE9D` — identique.
- `case_history.json` avant : `B4BBE00BA55E4735D6E474DDE2654317A868338A0DD54E43095AA0E43EF64BB1`
- `case_history.json` après : `B4BBE00BA55E4735D6E474DDE2654317A868338A0DD54E43095AA0E43EF64BB1` — identique.
- Aucun enregistrement source, identifiant stable ou propriété KMZ n’a été remplacé.

Les sorties `git status --short` et `git diff --stat` sont consignées lors de la clôture du micro-sprint afin d’inclure l’état de travail préexistant.
