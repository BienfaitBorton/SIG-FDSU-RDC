# Dashboard national enrichi et Référentiel Éducation — Architecture v1.0

## 1. Objet

Cette architecture introduit une synthèse nationale légère dans le Dashboard SIG-FDSU RDC et une première projection métier Éducation dérivée des Sites CENI. Elle préserve le chargement différé : le premier écran reçoit uniquement des agrégats, jamais les registres complets.

## 2. Synthèse nationale

`GET /dashboard/summary` conserve les compteurs historiques et ajoute `national_kpis`, `administrative_coverage`, `administrative_baseline` et `_meta`. Le contrat `_meta.payload_type = aggregates_only` interdit d'y inclure des géométries ou listes détaillées.

| KPI | Valeur auditée | Provenance | Règle |
|---|---:|---|---|
| Sites FDSU | 20 476 | `data/programs/sites_20476/sites_20476.json` | Le programme national inclut la vague 300; les programmes 40, 300 et national ne sont pas additionnés. |
| Sites CENI | 31 956 intégrés | Référentiel National CENI v1.0 | 32 221 disponibles dans la source; 265 en quarantaine pour coordonnées non exploitables; 25 262 classifiés; 6 959 non classifiés; 19 à vérifier. |
| Établissements scolaires | 23 604 | Sites CENI classifiés `SCHOOL` | Projection provisoire, non assimilée au registre officiel du Ministère de l'Éducation. |
| Établissements de santé | 37 562 | `health.health_facilities` | Comptage PostgreSQL national. |
| Infrastructures télécom | 14 580 infrastructures ponctuelles | schéma PostgreSQL `telecom` | 31 401 éléments géospatiaux intégrés au total : 14 580 points + 11 357 lignes + 5 464 polygones. Les lignes et polygones ne sont pas assimilés à des infrastructures unitaires. |

## 3. Baseline administrative UNSD/UNGEGN

Le registre `data/business/administrative_baseline_unsd_ungegn_v1.json` porte la baseline retenue par le projet : 26 provinces, 33 villes, 145 territoires, 259 chefferies, 478 secteurs, 6 053 groupements et 78 855 villages.

La baseline est une référence de comparaison, pas une mise à jour administrative 2026. L'année de publication n'étant pas renseignée dans la source projet disponible, elle reste explicitement `null`; la version interne et la date d'intégration assurent la traçabilité sans inventer une date.

## 4. Référence nationale, intégré SIG et géolocalisé

- **Référence nationale** : valeur attendue dans la baseline.
- **Intégré SIG** : lignes réellement présentes dans PostgreSQL ou le registre de compteurs contrôlé.
- **Géolocalisé** : à publier seulement lorsqu'un comptage géométrique fiable et comparable est disponible.

Les collectivités ne sont pas comparées à `secteurs + chefferies` sans table d'équivalence. La comparaison villages/localités reste indicative, car le SIG contient aussi camps, cités, quartiers et types résiduels.

## 5. Référentiel Éducation dérivé

Le service `api/services/education_referential_service.py` projette à la demande les Sites CENI dont `normalized_category = SCHOOL`. Il ne modifie ni ne recopie le registre CENI.

Le total sémantique principal reste fixé à 23 604 classifications scolaires. Parmi elles, 90 proviennent de lignes en quarantaine et sont exposées séparément comme candidats non intégrés et non validés; elles sont exclues de la liste géographiquement exploitable tant qu'une source complémentaire n'a pas fourni de position vérifiable.

## Quarantaine des coordonnées sentinelles

Les 265 placemarks dont la géométrie KML et les champs étendus portent simultanément `longitude = 0` et `latitude = 0` reçoivent le statut `coordinates_missing_or_sentinel`. Ils restent dans le registre avec leurs identifiants, nom, coordonnées originales, provenance, classification et batch, mais ne sont ni intégrés au KPI exploitable ni envoyés à la carte.

La valeur `0,0` est une sentinelle d'absence de localisation, pas une preuve de présence hors RDC. Elle est exclue des rapprochements `exact`, `same_geometry` et `probable`; seule une ressemblance lexicale sans action automatique peut subsister. Trente-huit lignes portent en mémoire `resolution_candidate = true` parce que leur nom normalisé existe également parmi les sites intégrés. Cette indication prépare un futur adaptateur NIRE sans créer d'identifiant national, sans fusion et sans conclure qu'il s'agit de doublons. Une similarité de nom seule ne constitue jamais une preuve d'identité.

Chaque projection conserve l'identifiant CENI, les noms original et normalisé, le sous-type, les coordonnées, les rattachements administratifs, le moteur, la règle, le mot-clé, la confiance, le statut de validation et la provenance.

Les endpoints sont :

- `GET /api/education/statistics` : agrégats uniquement;
- `GET /api/education/establishments` : projection paginée et filtrable, appelée seulement à l'ouverture du module.

## 6. Qualité et doctrine CS/C.S

| Niveau | Règle actuelle | Nombre |
|---|---|---:|
| Validé | Confiance très élevée | 4 736 |
| Probable | Confiance élevée DNAI/NSCE | 18 849 |
| À vérifier | Confiance moyenne ou revue requise | 19 |

Dans le contexte CENI, `CS` ou `C.S` privilégie « Complexe scolaire ». Un indice sanitaire explicite reste prioritaire. Un conflit fort n'est jamais transformé automatiquement en établissement scolaire certain.

## 7. Extension multi-source

Le modèle sépare `source_system`, `source_id`, catégorie métier et provenance. De futures sources — Ministère de l'Éducation, enquêtes terrain, partenaires ou référentiels institutionnels — pourront produire le même contrat sans changer l'identité CENI d'origine.

## 8. Chargement différé et performance

Le Dashboard initial appelle seulement le résumé agrégé, la frontière RDC et les provinces nécessaires. Les Sites CENI, le Référentiel Éducation, les données Santé, Télécom, Sites FDSU détaillés et couches administratives secondaires restent chargés après interaction.

Le test `tests/e2e/dashboard-performance.spec.js` protège l'absence d'appels initiaux vers les couches secondaires, `/api/ceni/sites`, `/api/education/establishments` et le moteur de décision complet.

## 9. Rôle futur de NIRE

NIRE devra rapprocher les identités provenant de CENI, du Ministère de l'Éducation, du terrain et des partenaires; détecter les doublons; conserver les identifiants sources; produire une identité consolidée explicable; et soumettre les conflits à validation humaine. NIRE ne devra jamais écraser automatiquement les sources institutionnelles.

## 10. Limites et prochaines intégrations

- La classification Éducation est lexicale et non une validation terrain.
- La baseline administrative nécessite une référence documentaire précisant l'année/édition UNSD/UNGEGN.
- Le futur fichier MNO doit être audité avant import : schéma, opérateurs, dates, unités géométriques, doublons, couverture, licence et correspondances avec les tables `telecom`.
