# Decision Intelligence Design Principles — SIG-FDSU RDC

**Document :** Charte officielle de conception  
**Référence :** `DECISION_INTELLIGENCE_DESIGN_PRINCIPLES_V1`  
**Version :** 1.1 — revue institutionnelle  
**Statut :** Doctrine de référence soumise à validation institutionnelle  
**Date :** 2026-07-13  
**Destinataires :** Direction Générale · Directions métiers · partenaires techniques · bailleurs · chefs de projet · administrateurs · développeurs  

---

## Statut et portée

La présente charte formule la philosophie de conception durable du SIG-FDSU RDC. Elle répond à la question : **pourquoi la plateforme est-elle construite de cette manière ?**

Elle ne remplace ni l’architecture fonctionnelle, ni le modèle métier, ni les spécifications de capacités. Elle les complète et leur donne un cadre commun de gouvernance, d’expérience et de qualité.

Les documents de référence restent notamment :

- `SIG_FDSU_RDC_V1_FUNCTIONAL_ARCHITECTURE.md` — architecture fonctionnelle ;
- `FDSU_ENTERPRISE_BUSINESS_MODEL.md` et `FDSU_BUSINESS_ARCHITECTURE.md` — modèle et capacités métier ;
- `NATIONAL_DATA_FABRIC_V1.md` — gouvernance des référentiels ;
- `DATA_FIRST_INTEGRATION_POLICY.md` — politique obligatoire d’intégration ;
- `E2E_INTEGRITY_GATE.md` — contrôle de l’intégrité fonctionnelle ;
- `SPATIAL_DECISION_GRAPH_V2.md`, `FDSU_TERRITORIAL_INTELLIGENCE.md`,
  `FDSU_EXPLAINABLE_DECISION_ENGINE.md`, `TERRITORIAL_DIGITAL_TWIN_V1.md` et
  `EXECUTIVE_SITUATION_ROOM_V1.md` — capacités de décision.

> Toute évolution de la plateforme doit respecter cette doctrine sans contredire les documents normatifs ci-dessus.

---

## 1. Vision

Le SIG-FDSU RDC n’est pas un logiciel de cartographie.

C’est une **plateforme nationale d’Intelligence Territoriale et d’Aide à la Décision**. Elle permet au FDSU de comprendre les réalités territoriales, identifier les besoins, expliquer les priorités, comparer des scénarios, simuler les investissements, justifier chaque décision et piloter les programmes du Service Universel.

La carte est un langage de décision : elle rend visibles les faits, les écarts, les relations et les conséquences. Elle ne constitue jamais une fin en soi.

## 2. Mission

> **Transformer des données multisectorielles en décisions territoriales explicables.**

Les données administratives, démographiques, de connectivité, de santé, de transport, de couverture et de programmes FDSU deviennent utiles lorsqu’elles sont :

1. compréhensibles par les décideurs ;
2. localisables dans le territoire ;
3. comparables entre situations et dans le temps ;
4. interprétables avec leurs limites ;
5. convertibles en actions et en décisions justifiées.

---

## 3. Valeurs fondamentales

| Valeur | Engagement institutionnel |
|---|---|
| **Transparence** | Les faits, sources, limites et règles de décision sont visibles à un niveau approprié. |
| **Traçabilité** | Toute donnée, relation, calcul et recommandation peut être relié à sa source et à sa méthode. |
| **Explicabilité** | Aucun score, priorité, relation ou recommandation n’est livré sans réponse intelligible au « pourquoi ». |
| **Neutralité** | La plateforme présente des faits, règles et hypothèses ; elle ne maquille pas l’incertitude pour produire une réponse attendue. |
| **Fiabilité** | Les résultats doivent être cohérents, vérifiés, reproductibles et soumis aux contrôles d’intégrité. |
| **Évolutivité** | Un nouveau référentiel ou une nouvelle capacité doit s’intégrer sans remettre en cause les principes ou les contrats communs. |
| **Interopérabilité** | Les référentiels sont gouvernés et composables par le National Data Fabric ; la plateforme évite les silos. |
| **Qualité des données** | Complétude, fraîcheur, cohérence, géométrie et précision sont considérées dans l’interprétation. |
| **Orientation décisionnelle** | Chaque écran doit aider une personne identifiée à comprendre, arbitrer, prioriser ou suivre une décision. |
| **Simplicité d’utilisation** | La sophistication analytique ne doit jamais imposer une complexité inutile au décideur. |

Ces valeurs sont permanentes. Les compromis de mise en œuvre ne peuvent les contredire sans décision de gouvernance explicite.

---

## 4. Acteurs de la plateforme

| Acteur | Rôle dans la plateforme | Attentes principales | Décisions / niveau d’information |
|---|---|---|---|
| **Directeur Général** | Porte la vision, arbitre et pilote | Situation immédiate, risques, recommandation, preuves | Synthèse DG et arbitrage stratégique |
| **Comité de Pilotage** | Oriente les priorités et suit l’exécution | Comparaisons, portefeuille, indicateurs d’impact | Pilotage et validation des orientations |
| **Directions Techniques** | Définissent les exigences sectorielles | Référentiels fiables, analyses et actions sectorielles | Niveau métier et analyse |
| **Direction Planification** | Structure les programmes et scénarios | Besoins, couverture, coûts, trajectoires | Priorisation et scénarios |
| **Direction Ingénierie** | Qualifie la faisabilité technique | Infrastructures, accessibilité, contraintes, interconnexions | Niveau expert et technique |
| **Experts SIG** | Garantissent l’intégrité spatiale | Géométries, méthodes, couches, relations spatiales | Analyse territoriale et technique |
| **Agents Terrain** | Alimentent et confirment les réalités | Missions, objets à vérifier, retour opérationnel | Fiche opérationnelle et collecte |
| **Partenaires techniques** | Appuient l’intégration et l’expertise | Interopérabilité, transparence, contrats de données | Information partagée selon mandat |
| **Bailleurs** | Suivent l’utilisation et l’impact des ressources | Justification, résultats, risques, traçabilité | Synthèse, portefeuille et preuve |
| **Administrateurs** | Assurent disponibilité, sécurité et gouvernance | Qualité de service, droits, référentiels, audit | Niveau d’administration |
| **Développeurs** | Construisent et maintiennent les capacités | Principes stables, contrats clairs, critères de qualité | Niveau technique et conformité doctrine |

Le niveau d’information doit être adapté au rôle ; il ne doit jamais cacher les limites qui modifient l’interprétation d’une décision.

---

## 5. Les dix principes fondateurs

### 5.1 Data First

Toute donnée disponible dans un référentiel réel doit être exploitée. Une donnée existante ne peut pas être affichée comme « indisponible », `0` ou « non renseignée » si une recherche adaptée établit sa présence.

**Exemple SIG-FDSU :** un établissement de santé présent dans `health.health_facilities` et spatialement contenu dans un territoire doit alimenter le profil territorial. Le masquer au motif qu’un champ textuel de rattachement est vide constitue une anomalie d’intégration.

Si le référentiel n’existe pas, la capacité reste visible avec l’état **En cours d’intégration** et sa limite métier explicite.

### 5.2 Explainability First

Toute donnée affichée doit répondre, au niveau adapté, à : **Combien ? Lesquels ? Où ? Qui ? Pourquoi ? Quel impact ? Quelle recommandation ?**

**Exemple SIG-FDSU :** « Télécom : 22 » doit devenir une lecture incluant répartition par type, opérateurs identifiés, localisation, source, niveau de confiance, impact et action proposée.

Un chiffre seul n’est jamais une décision.

### 5.3 Spatial First

Toute donnée territoriale doit pouvoir être représentée spatialement lorsque sa géométrie ou une localisation fiable existe.

**Exemple SIG-FDSU :** l’ouverture du détail Santé met en évidence les établissements concernés ; l’ouverture du détail Routes montre les tronçons correspondants. Carte et panneau restent synchronisés.

Une couche disponible mais non visible lorsqu’elle est utile est un défaut fonctionnel.

### 5.4 Decision First

Chaque écran est conçu autour d’une décision métier, et non autour d’un simple affichage de données.

**Exemple SIG-FDSU :** le Centre de Décision ne présente pas uniquement des scores de sites ; il prépare un arbitrage d’investissement avec faits, critères, lacunes et actions possibles.

Questions obligatoires : qui décide ? quelle décision est soutenue ? quelles preuves sont nécessaires ? quelle action est attendue ?

### 5.5 Evidence First

Toute recommandation est fondée sur des faits observables, des sources identifiées, une méthode explicite et un niveau de confiance.

**Exemple SIG-FDSU :** une priorité de site doit distinguer les critères mesurés, les proxys autorisés et les informations manquantes. Aucune distance, relation, score ou impact ne peut être inventé pour compléter une maquette.

### 5.6 Progressive Disclosure

La plateforme révèle l’information progressivement :

```text
Synthèse
  ↓
Explication métier
  ↓
Analyse territoriale
  ↓
Exploration détaillée
  ↓
Détail technique
```

**Exemple SIG-FDSU :** le Directeur Général lit d’abord la situation et la recommandation ; l’analyste ouvre le drawer ; l’expert accède ensuite aux méthodes spatiales, sources et attributs.

### 5.7 Spatial Explainability

Une relation spatiale doit raconter une histoire : origine, destination, distance lorsqu’elle est calculable, rôle métier, impact et contribution à la décision.

**Exemple SIG-FDSU :** le Spatial Decision Graph explique pourquoi un actif est associé à un besoin territorial et quelle conséquence cette relation a sur une priorité d’investissement.

Une ligne, une flèche ou une proximité sans explication n’est pas une intelligence spatiale.

### 5.8 Decision Conversation

Le système doit progressivement permettre une conversation naturelle avec le décideur : « Pourquoi ? », « Où ? », « Qui ? », « Depuis quand ? », « Combien ? », « Que se passe-t-il si… ? », « Comparer avec… ».

**Exemple SIG-FDSU :** la comparaison de deux territoires doit produire une réponse sourcée et non une phrase générée sans preuve. La forme conversationnelle peut évoluer ; le contenu factuel reste obligatoire.

### 5.9 Integrity by Design

Une capacité n’est terminée que lorsqu’elle est développée, branchée, alimentée, visible, testée et validée fonctionnellement.

**Exemple SIG-FDSU :** une API Santé valide sans affichage des établissements sur la carte ne constitue pas une livraison complète. Les tests automatisés complètent, mais ne remplacent pas, la validation humaine dans le navigateur.

### 5.10 Evolution by Design

L’architecture accueille les nouveaux référentiels et capacités sans créer de calculs concurrents, d’écrans isolés ou de contrats propriétaires.

**Exemple SIG-FDSU :** un futur référentiel Énergie doit être enregistré, qualifié et consommé dans les mêmes parcours de décision, sans reconstruire une architecture parallèle.

---

## 6. Le parcours décisionnel officiel

```text
Observation
  ↓
Compréhension
  ↓
Analyse
  ↓
Explication
  ↓
Comparaison
  ↓
Simulation
  ↓
Recommandation
  ↓
Décision
  ↓
Suivi
  ↓
Évaluation
```

| Étape | Finalité | Capacités SIG-FDSU associées |
|---|---|---|
| **Observation** | Voir une situation, une alerte ou un écart | Cartographie, référentiels, National Data Fabric |
| **Compréhension** | Identifier la nature, l’étendue et les acteurs | Intelligence Territoriale, fiches, profils territoriaux |
| **Analyse** | Croiser les besoins, actifs et contraintes | Territorial Digital Twin, Spatial Matching, SDG |
| **Explication** | Rendre les faits et méthodes intelligibles | Explainable Decision Engine, drill-down, sources |
| **Comparaison** | Mettre en regard territoires, sites ou options | Centre de Décision, futurs comparateurs |
| **Simulation** | Examiner un scénario sous hypothèses déclarées | Decision Scenarios, futures simulations budgétaires |
| **Recommandation** | Proposer une action traçable | Decision Engine, Dossier de décision, Salle DG |
| **Décision** | Arbitrer et formaliser l’orientation | Direction Générale, Comité de Pilotage |
| **Suivi** | Mesurer l’avancement et les effets | Salle de Pilotage, programmes, indicateurs |
| **Évaluation** | Vérifier l’impact réel et corriger | National Data Fabric, audit, retours terrain |

Le parcours n’est pas toujours linéaire : une lacune révélée à l’étape d’explication peut renvoyer vers l’observation, la qualification des données ou une mission terrain.

---

## 7. Le modèle d’intelligence

Le schéma conceptuel officiel est le suivant :

```text
Référentiels réels
        ↓
National Data Fabric
        ↓
Spatial Matching
        ↓
Territorial Intelligence
        ↓
Spatial Decision Graph
        ↓
Explainable Decision Engine
        ↓
Executive Situation Room
        ↓
Décision
```

| Élément | Responsabilité institutionnelle |
|---|---|
| **Référentiels réels** | Fournir les faits de base, sous gouvernance et avec qualité connue |
| **National Data Fabric** | Cataloguer, relier, qualifier et rendre les référentiels interopérables sans les dupliquer |
| **Spatial Matching** | Établir des relations spatiales calculées et traçables |
| **Territorial Intelligence** | Composer une lecture territoriale multi-sectorielle |
| **Spatial Decision Graph** | Rendre visibles les relations, impacts et lacunes décisionnelles |
| **Explainable Decision Engine** | Produire des recommandations justifiées et auditées |
| **Executive Situation Room** | Donner à la Direction Générale une lecture priorisée et pilotable |
| **Décision** | Permettre l’arbitrage humain responsable ; la plateforme n’en transfère pas la responsabilité |

Ce schéma n’impose pas un ordre technique strict. Il décrit le chemin de valeur et la responsabilité de chaque capacité.

---

## 8. Règle « No Black Box »

### Principe

Aucune décision du SIG-FDSU RDC ne peut être inexplicable.

Chaque :

- score ;
- priorité ;
- relation spatiale ;
- simulation ;
- recommandation ;
- alerte ;

doit être justifiable par un utilisateur habilité.

### Exigences minimales

| Élément | Justification attendue |
|---|---|
| Score | critères, pondérations ou règle, date et confiance |
| Priorité | faits observés, risques, lacunes et règle d’arbitrage |
| Relation | objets reliés, méthode, distance si applicable, rôle et impact |
| Simulation | hypothèses, périmètre, données d’entrée, résultat et limites |
| Recommandation | action, pourquoi, preuves, impact attendu et incertitudes |

Le détail technique peut être réservé aux niveaux habilités ; l’explication métier ne peut pas être absente.

---

## 9. Règles UX officielles

1. Chaque KPI est cliquable lorsqu’un détail existe.
2. Chaque KPI ouvre un drawer, un panneau ou un parcours de détail équivalent.
3. Chaque drawer pilote la carte et met en évidence les objets concernés.
4. Chaque carte pilote les fiches et les informations détaillées.
5. Chaque fiche explique le rôle de l’objet dans la décision.
6. Aucun bouton décoratif n’est autorisé.
7. Aucune donnée métier ne reste sans contexte, source ou statut de maturité.
8. Aucune donnée disponible ne reste non exploitée.
9. Les codes techniques restent au niveau technique ; les vues métier utilisent des libellés compréhensibles.
10. Une action inaccessible ou non fonctionnelle n’est pas présentée comme disponible.

---

## 10. Règles cartographiques officielles

### 10.1 Principes

- Une couleur et une symbologie cohérentes par domaine ;
- une légende interactive correspondant aux couches réellement chargées ;
- des filtres sans perte inutile du contexte ;
- des couches synchronisées avec les panneaux et fiches ;
- des relations spatiales expliquées ;
- aucun objet disponible rendu invisible ;
- une seule instance cartographique par contexte d’écran ;
- des emprises, niveaux de zoom et redessins basés sur les objets réellement rendus.

### 10.2 Registre de symbologie cible

Cette table définit l’intention de design. Toute évolution visuelle doit conserver la distinction de domaines, l’accessibilité et la cohérence avec les composants partagés.

| Domaine | Couleur de référence | Icône / symbole | Signification métier |
|---|---|---|---|
| Télécom | Bleu | Antenne / signal | Infrastructure de connectivité |
| Santé | Vert | Croix / établissement | Service de santé |
| Routes | Gris ardoise | Axe / ligne | Accessibilité et logistique |
| Fibre | Magenta | Nœud / ligne optique | Potentiel de raccordement |
| CCN | Violet | Centre communautaire | Service numérique communautaire |
| Sites FDSU | Ambre | Site / balise | Intervention ou programme FDSU |
| Éducation | Bleu-vert | École | Service éducatif |
| Énergie | Jaune | Éclair | Disponibilité énergétique |
| Population | Indigo | Groupe de personnes | Bénéficiaires et pression démographique |
| Administratif | Jaune-or | Polygone / repère | Cadre institutionnel territorial |
| Marchés | Orange | Marché | Activité économique et services |
| Environnement | Vert foncé | Feuille / zone | Contraintes ou opportunités environnementales |

Une couleur ne vaut pas à elle seule une interprétation : elle est toujours accompagnée d’une légende, d’un libellé et d’un état.

---

## 11. Data First — hiérarchie officielle

```text
Référentiel réel
        ↓
Calcul dérivé documenté
        ↓
Estimation explicite et sourcée
        ↓
En cours d’intégration
```

Il est interdit d’afficher « Indisponible » ou `0` lorsqu’une donnée existe réellement.

Un zéro est autorisé uniquement si :

1. le référentiel existe ;
2. la recherche a été exécutée ;
3. le résultat est réellement nul.

Dans les autres cas, le système affiche selon le cas : **Non calculable**, **Non renseigné**, **En cours d’intégration**, **Anomalie d’intégration** ou **Données insuffisantes**.

Les états de maturité opérationnelle sont définis par `DATA_FIRST_INTEGRATION_POLICY.md` : Opérationnel, Partiellement intégré, En cours d’intégration et Anomalie d’intégration.

---

## 12. Niveaux d’explication

| Niveau | Nom | Public principal | Réponse attendue |
|---|---|---|---|
| **1** | Synthèse DG | Direction Générale | Que se passe-t-il et quelle décision est recommandée ? |
| **2** | Explication métier | Directions et comité de pilotage | Pourquoi, qui est concerné, quel impact ? |
| **3** | Analyse territoriale | Planification, SIG, ingénierie | Où, quelles relations, quelles contraintes et comparaisons ? |
| **4** | Exploration détaillée | Experts métier et terrain | Quels objets, attributs, localisations et statuts ? |
| **5** | Détail technique | Administration, ingénierie, audit | Quelle source, quelle méthode, quelle qualité et quelle trace ? |

La transition entre niveaux applique la progressive disclosure. Elle ne doit ni cacher une limite décisive ni imposer d’emblée une information technique inutile.

---

## 13. Checklist officielle de qualité

Chaque sprint mettant à disposition une capacité décisionnelle doit satisfaire, pour le périmètre annoncé :

- [ ] Données réelles exploitées ou absence réelle explicitement déclarée
- [ ] Source affichée lorsque pertinente
- [ ] Niveau de confiance et limites indiqués
- [ ] KPI explicable
- [ ] Carte synchronisée lorsque la donnée est territoriale
- [ ] Drawer ou parcours de détail disponible
- [ ] Drill-down vers les objets, lorsque des objets existent
- [ ] Impact métier expliqué ou déclaré non calculable
- [ ] Recommandation justifiée, lorsque la capacité recommande une action
- [ ] Traçabilité des données, règles et calculs
- [ ] Tests backend adaptés
- [ ] Tests Playwright / E2E adaptés
- [ ] Validation visuelle dans le navigateur
- [ ] Validation métier

> Aucun sprint n’est terminé sans validation complète. Les tests automatisés attestent la non-régression ; ils ne remplacent pas la validation fonctionnelle et métier.

---

## 14. Échelle de maturité

| Niveau | Définition | Conséquence de gouvernance |
|---|---|---|
| **Prototype** | Démonstration exploratoire, donnée ou parcours non stabilisé | Non utilisé pour un arbitrage institutionnel |
| **Expérimental** | Capacité utilisable sur périmètre limité, avec limites visibles | Décision assistée et contrôlée |
| **Partiel** | Référentiels ou couverture incomplète, mais exploitation réelle | Utilisable avec note de limite obligatoire |
| **Opérationnel** | Données, parcours, intégrité et validation fonctionnelle établis | Utilisable dans le pilotage courant |
| **Référence nationale** | Gouvernance, interopérabilité, qualité et adoption institutionnelle durables | Référence pour la planification et le suivi nationaux |

Chaque module doit pouvoir être évalué sur cette échelle indépendamment de son ambition finale.

---

## 15. Axes d’évolution

L’architecture actuelle prépare les évolutions suivantes :

| Axe | Apport attendu | Garde-fou doctrinal |
|---|---|---|
| IA décisionnelle | Assistance à l’analyse et à la priorisation | No Black Box, Evidence First |
| Assistant conversationnel | Questions naturelles et réponses contextualisées | Sources, limites et traçabilité visibles |
| Simulation budgétaire | Arbitrage entre impact, coûts et enveloppes | Hypothèses et résultats explicites |
| Projection temporelle | Trajectoires de déploiement et couverture | Dates, sources et incertitudes déclarées |
| Comparaison automatique | Comparaison équilibrée de territoires ou scénarios | Indicateurs comparables et méthode documentée |
| Optimisation territoriale | Allocation sous contraintes | Objectif, contraintes et compromis explicables |
| Analyse prédictive | Anticipation de besoins ou risques | Validation, confiance et biais documentés |
| Vision prospective | Planification multi-scénarios | Scénarios distingués des faits observés |

Ces évolutions ne changent pas la responsabilité humaine de la décision. Elles élargissent la qualité des preuves disponibles.

---

## 16. Conclusion institutionnelle

Le SIG-FDSU RDC a vocation à devenir la plateforme nationale de référence pour :

- la planification ;
- la priorisation ;
- la simulation ;
- la justification ;
- le pilotage ;

des investissements du Service Universel en République Démocratique du Congo.

Cette ambition repose sur une règle durable :

> **Chaque décision doit exploiter les connaissances disponibles, déclarer explicitement les connaissances manquantes, et rendre visibles les faits, les impacts et les raisons de l’action proposée.**

Tous les futurs développements devront respecter la présente doctrine.

---

## Annexe A — Règles DG

Tout écran destiné au Directeur Général répond immédiatement à :

| Question | Réponse attendue |
|---|---|
| Que se passe-t-il ? | Situation claire et priorisée |
| Pourquoi ? | Causes, faits et limites |
| Où ? | Emprise et objets concernés |
| Quelles conséquences ? | Impact sur population, services, accès ou programme |
| Que recommande le système ? | Action argumentée |
| Quelles preuves ? | Sources, indicateurs, confiance et lacunes |

## Annexe B — Historique

| Version | Date | Nature |
|---|---|---|
| 1.0 | 2026-07-13 | Création de la charte |
| 1.1 | 2026-07-13 | Revue institutionnelle : valeurs, acteurs, parcours décisionnel, modèle d’intelligence, No Black Box, symbologie cible, maturité et checklist officielle |

---

*Document soumis à validation institutionnelle avant versionnement dans le référentiel de gouvernance produit.*
