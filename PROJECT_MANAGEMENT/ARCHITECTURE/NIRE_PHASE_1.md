# NIRE Phase 1 — Core Domain, preuves et contrats de résolution

## 1. Portée évolutive

NIRE — National Identity Resolution Engine — répond à la question : « plusieurs enregistrements représentent-ils la même entité réelle ? ». La Phase 1 constitue un socle extensible en mémoire. Elle ne crée ni API publique, ni table, ni migration, ni identité nationale persistante, ni fusion réelle. Toute sortie est une recommandation explicable soumise à revue humaine.

Cette architecture est une première fondation et non une architecture définitive.

### Principes d'évolutivité obligatoires

- Les modèles constituent des contrats extensibles : leurs évolutions doivent privilégier l'ajout de champs optionnels et préserver la lecture des versions antérieures.
- `evidence_type` est un code ouvert; de nouveaux types de preuves peuvent être publiés sans figer une énumération définitive dans le cœur.
- Le National Rule Registry est versionné. Ses règles, poids et seuils sont calibrables et ne sont pas considérés comme définitifs.
- Les `SourceAdapter` sont pluggables : une nouvelle source ou un nouveau domaine doit pouvoir s'ajouter sans modifier l'algorithme central de fusion.
- Les futurs domaines NEIL peuvent étendre les contrats communs sans coupler NIRE à CENI, à l'Éducation, aux télécommunications ou à un autre référentiel particulier.
- Toute persistance future doit rester derrière un contrat dédié et découplé du moteur en mémoire; le cœur ne doit pas dépendre d'un schéma PostgreSQL concret.
- Les futures API doivent dépendre des interfaces et modèles NIRE, jamais des implémentations concrètes d'adaptateurs ou de stockage.
- NEIL reste une couche gouvernée évolutive, rectifiable et réversible; aucune structure d'identité nationale n'est figée par la Phase 1.
- Les extensions additives sont préférées aux ruptures de contrat. Toute rupture indispensable devra introduire une nouvelle version explicite et une stratégie de compatibilité.

## 2. Positionnement des moteurs

| Composant | Responsabilité |
|---|---|
| DNAI | Normalisation morphologique et expansion terminologique contrôlée. |
| NTIL | Gouvernance des termes, variantes et nomenclatures nationales. |
| NSCE | Classification sémantique métier d'un enregistrement. |
| NIRE | Comparaison d'identité multi-preuves entre enregistrements. |
| NEIL | Future couche gouvernée d'identité nationale consommant uniquement des décisions validées. |

NIRE ne remplace aucun moteur amont. NEIL, NSI, NHI, NEI, NTI, NCI et NAI ne sont pas implémentés dans cette phase.

## 3. Modules

- `models.py` : `NationalEvidence`, `EntityReference`, `ResolutionCandidate`, `ResolutionDecision`, `ResolutionRun`, statuts et ambiguïté;
- `adapters.py` : contrat abstrait `SourceAdapter` et adaptateur fictif `InMemorySourceAdapter`;
- `rules.py` : chargement et validation du registre versionné;
- `engine.py` : extraction de preuves, fusion, décisions et explications;
- `nire_resolution_rules_v1.json` : poids, polarités, seuils et règles bloquantes.

Les identifiants de preuves, candidats et décisions sont déterministes pour assurer l'idempotence. `VALIDATED_MATCH` existe dans le contrat mais le moteur ne peut jamais le produire automatiquement.

## 4. NationalEvidence

Une preuve conserve son type extensible, ses deux entités, valeur brute et normalisée, poids, confiance, fiabilité, polarité, métadonnées et horodatage. Sa contribution est `poids × confiance × fiabilité`.

Le registre couvre les preuves positives demandées : identifiants, nom normalisé ou officiel, alias, distance, coordonnées, contexte administratif, province, territoire, localité, opérateur, type métier, téléphone, courriel, référence externe et validation manuelle. Il couvre également les conflits d'identifiant, type, opérateur, administration et géographie.

De nouveaux types pourront être ajoutés au JSON sans changer les modèles, `evidence_type` restant un code métier ouvert.

## 5. Evidence Fusion Engine

Le moteur sépare les contributions positives et négatives, puis calcule un score borné entre 0 et 100. Les poids Phase 1 sont notamment : nom normalisé 30, territoire 20, distance proche 35, coordonnées identiques 45 et identifiant institutionnel identique 90.

Le score n'a jamais priorité sur une règle bloquante. Un conflit bloquant force le score de résolution à zéro et produit `NO_MATCH`, même si plusieurs preuves positives existent.

Seuils versionnés :

- moins de 40 : preuves insuffisantes;
- 40 à 64,99 : correspondance possible;
- 65 à 84,99 : correspondance recommandée avec revue;
- 85 à 100 : candidat fort, toujours sans fusion automatique.

La confiance combine fiabilité moyenne et couverture probatoire. Elle ne constitue pas une autorisation de fusion.

## 6. Règles bloquantes

- identifiants institutionnels incompatibles;
- types métier incompatibles;
- opérateurs incompatibles pour les infrastructures télécom;
- provinces contradictoires;
- distance géographique supérieure ou égale à 100 km.

Ces règles sont explicites, versionnées et restituées dans `ResolutionDecision.blocking_rules`.

## 7. Ambiguïté

Le modèle utilise `NONE`, `LOW`, `MEDIUM`, `HIGH` et `CRITICAL`.

- nom identique sans géographie ni contexte : `HIGH`;
- plusieurs candidats aux scores séparés de cinq points ou moins : `HIGH`;
- au moins cent homonymes : `CRITICAL`;
- candidat unique soutenu par plusieurs preuves : `LOW` ou `MEDIUM` selon le score.

Toutes les décisions Phase 1 portent `requires_human_review = true`.

## 8. Explicabilité et sécurité

L'explication française est composée uniquement à partir des preuves réellement extraites : nom normalisé, territoire, province, distance, coordonnées, identifiant ou conflits. Les identifiants des preuves positives, négatives et utilisées restent disponibles sous forme structurée pour une future API.

Protections contre les fausses fusions :

- aucun nom seul ne valide une identité;
- `0,0` et les coordonnées invalides ne deviennent jamais une preuve géographique;
- un homonyme n'est jamais traité comme doublon;
- les conflits bloquants priment sur le score;
- aucune mutation des entités sources;
- aucune décision automatique `VALIDATED_MATCH`;
- aucune action de fusion dans le moteur.

## 9. Cas CENI en quarantaine

Les 38 candidats CENI restent un cas d'usage architectural, sans lecture automatique ni modification de leurs données pendant cette phase.

- **E.P KABAMBA** : un même nom normalisé sans coordonnée produit une preuve `NORMALIZED_NAME`, une ambiguïté élevée et `INSUFFICIENT_EVIDENCE`. Un territoire ou un identifiant institutionnel futur pourra renforcer le dossier.
- **CABANE** : 114 correspondances possibles produisent une ambiguïté `CRITICAL`; aucune fusion n'est recommandée.

Un futur `CeniSourceAdapter` devra lire la quarantaine en lecture seule et conserver `asset_uid`, `source_record_id`, provenance et motif de quarantaine.

## 10. Futur cas national MNO

Le workflow cible est :

```text
SOURCE MNO (Vodacom, Airtel, Orange, Africell)
  → audit qualité
  → DNAI / NTIL si nécessaire
  → NSCE si nécessaire
  → Candidate Generation Engine
  → NIRE contre le référentiel télécom existant
  → MATCH_RECOMMENDED / POSSIBLE_MATCH / AMBIGUOUS / NO_MATCH
  → validation humaine ou institutionnelle
  → NEIL / NTI
  → référentiel télécom enrichi
```

Les preuves attendues incluent opérateur, identifiant MNO, type d'infrastructure, coordonnées, distance et contexte administratif. Un opérateur différent est bloquant pour une même infrastructure supposée. Aucun fichier MNO n'est importé en Phase 1.

## 11. Contrat SourceAdapter

Chaque source future devra exposer son nom, son type d'entité, l'itération et la lecture par identifiant, la normalisation, les caractéristiques d'identité et les preuves spécifiques. Les adaptateurs ne doivent ni écrire dans la source ni masquer sa provenance.

`InMemorySourceAdapter` démontre le contrat avec des données fictives et non sensibles.

## 12. Traçabilité ResolutionRun

`ResolutionRun` trace les dates, domaines source/cible, volumes, candidats, résolutions recommandées, ambiguïtés, conflits, insuffisances et versions moteur/règles. Il reste en mémoire en Phase 1.

## 13. Trajectoire Phase 2

Phase 2 devra être proposée et validée avant implémentation :

1. adaptateurs réels CENI, Éducation, Santé, Télécom, FDSU et Administration;
2. Candidate Generation Engine avec blocage par domaine, territoire et index spatial;
3. résolution multi-source et comparaison de plusieurs candidats;
4. API NIRE interne versionnée;
5. persistance contrôlée et migrations réversibles;
6. file de revue humaine et décisions institutionnelles;
7. audit trail immuable des preuves, règles et décisions;
8. jeux d'étalonnage et mesure précision/rappel par domaine;
9. supervision des biais, faux positifs et dérive des règles;
10. intégration progressive de NEIL après validation de gouvernance.

Avant toute persistance, le projet devra définir les rôles d'approbation, le droit de rectification, les politiques de réversibilité et les seuils par domaine.
