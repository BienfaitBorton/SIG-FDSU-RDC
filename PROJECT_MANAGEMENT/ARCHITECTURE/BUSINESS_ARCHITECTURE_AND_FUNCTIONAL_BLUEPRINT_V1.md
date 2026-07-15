# SIG-FDSU RDC
# Business Architecture & Functional Blueprint — V1.0

**Statut :** Document de référence officiel — vision produit et architecture métier  
**Date :** 14 juillet 2026  
**Version :** 1.0  
**Classification :** Architecture métier — diffusion interne projet et validation institutionnelle  
**Périmètre :** Documentation uniquement — **aucun code, aucun test, aucun commit**

---

## Déclaration officielle

> **Le SIG-FDSU RDC n'est plus défini comme un simple SIG.**  
> **Le logiciel est officiellement :**
>
> **SIG-FDSU RDC — Plateforme Nationale de Planification, de Priorisation et d'Aide à la Décision pour le Service Universel.**

Cette définition devient la **référence officielle** du projet pour toute conception, tout développement, toute communication institutionnelle et toute validation métier.

La cartographie reste un **instrument de décision**, jamais une finalité. L'objectif n'est pas de « faire une belle carte », mais de **planifier, prioriser, justifier, suivre et évaluer** les investissements du Service Universel au bénéfice des populations congolaises.

**Documents liés (architecture existante) :**
- [`FDSU_BUSINESS_ARCHITECTURE.md`](./FDSU_BUSINESS_ARCHITECTURE.md)
- [`FDSU_ENTERPRISE_BUSINESS_MODEL.md`](./FDSU_ENTERPRISE_BUSINESS_MODEL.md)
- [`SIG_FDSU_RDC_V1_FUNCTIONAL_ARCHITECTURE.md`](./SIG_FDSU_RDC_V1_FUNCTIONAL_ARCHITECTURE.md)
- [`NATIONAL_DATA_FABRIC_V1.md`](./NATIONAL_DATA_FABRIC_V1.md)
- [`FDSU_CCN_BUSINESS_MODEL.md`](./FDSU_CCN_BUSINESS_MODEL.md)
- [`DATA_FIRST_INTEGRATION_POLICY.md`](./DATA_FIRST_INTEGRATION_POLICY.md)

---

## 1. Alignement stratégique avec la Stratégie Nationale FDSU

La plateforme traduit la stratégie nationale du Fonds de Développement du Service Universel (FDSU) en **capacités opérationnelles vérifiables**. Elle ne remplace pas la gouvernance humaine : elle la **structure, l'éclaire et la rend auditable**.

### 1.1 Planification territoriale

Le SIG-FDSU RDC permet de :

- connaître l'état réel des territoires (population, services, infrastructures, accessibilité) ;
- situer les programmes nationaux (sites, CCN, corridors, vagues opérationnelles) dans leur contexte spatial ;
- simuler des scénarios d'intervention avant engagement budgétaire ;
- aligner les décisions locales sur une vision nationale cohérente.

**Traduction plateforme :** Intelligence Territoriale, Territorial Digital Twin, cartographie nationale, National Data Fabric, parcours décisionnel.

### 1.2 Priorisation des investissements

Les ressources du Service Universel sont limitées. La plateforme doit rendre **explicites** les critères de priorisation : déficit de couverture, population, services publics, faisabilité, coût, impact social, équilibre territorial.

**Traduction plateforme :** moteurs de priorisation, matrices métier, Decision Intelligence, Spatial Decision Graph, dossiers de décision explicables.

### 1.3 Réduction de la fracture numérique

La stratégie FDSU vise à rapprocher les populations des services numériques essentiels. La plateforme identifie les **zones blanches**, les **localités non couvertes**, les **corridors prioritaires** et mesure l'évolution de la couverture dans le temps.

**Traduction plateforme :** National Coverage Intelligence, NSME, référentiels télécom, CCN, indicateurs de couverture et d'inclusion.

### 1.4 Service Universel

Le Service Universel n'est pas seulement un objectif de connectivité : c'est un **engagement institutionnel** envers l'accès aux services numériques pour tous. La plateforme relie connectivité, services publics numériques, inclusion et obligations des opérateurs.

**Traduction plateforme :** programmes Sites FDSU, CCN, référentiels sectoriels, suivi des obligations, rapports institutionnels.

### 1.5 Viability Gap Funding (VGF)

Le VGF comble l'écart entre le coût réel d'un investissement et ce que le marché peut supporter seul. La plateforme doit permettre de **justifier** un besoin de subvention par des faits territoriaux, des coûts estimés, des impacts attendus et des scénarios comparés.

**Traduction plateforme :** Decision Scenarios, simulations, dossiers de décision, traçabilité des hypothèses — **sans inventer de chiffres non sourcés**.

### 1.6 Obligations des opérateurs

Les opérateurs de télécommunications ont des obligations de couverture et de qualité de service. La plateforme consolide les référentiels d'infrastructure, la couverture réelle et les écarts constatés pour **objectiver** le dialogue réglementaire et le pilotage du Service Universel.

**Traduction plateforme :** référentiel télécom, routes, fibre, couverture radio (cible), rapports de conformité (cible).

### 1.7 Transparence des décisions

Toute recommandation ou priorité affichée doit être **explicable** : sources, règles, relations spatiales, limites connues, données manquantes explicitement signalées.

**Traduction plateforme :** Data First, Explainability, Spatial Decision Graph, Decision Case, politique « No Black Box ».

### 1.8 Suivi des impacts

Une décision n'est complète que si son exécution et ses effets peuvent être suivis. La plateforme relie planification → déploiement → résultats mesurables.

**Traduction plateforme :** pilier Impact / Suivi / Évaluation, Executive Situation Room, indicateurs nationaux (NIF), rapports CA / bailleurs / gouvernement.

---

## 1A. Documents officiels FDSU — Source of Truth institutionnelle

Les **documents officiels FDSU** déjà présents dans le dépôt constituent la **Source of Truth** du SIG-FDSU RDC. Ils ne sont ni des annexes techniques ni des fichiers d'import secondaires : ils fondent la légitimité institutionnelle de toute règle, priorité ou recommandation affichée par la plateforme.

### 1A.1 Périmètre documentaire

Le dépôt conserve ces documents sous forme **brute et non altérée**, principalement dans :

| Emplacement | Nature | Exemples |
|-------------|--------|----------|
| **`data/raw/`** | Référentiels et jeux de données officiels FDSU | Nomenclature sites (`FDSU Structure code Territoire zones.xlsx`), couverture (`Localités non couvertes_*.xlsx`, `Population coverage-*.xlsx`), référentiels géographiques (`Groupements.kmz`, `Routes_principales.shp.kmz`) |
| **`data/strategic/`** | Documents stratégiques normatifs | Stratégie FDSU–CCN 2026–2030 (`strategie_fdsu_ccn_2026_2030.docx`), matrice officielle de priorisation (`matrice_priorisation_300_sites.xlsx`) |
| **`data/business/`** | Règles métier structurées **dérivées** des documents officiels | `decision_rules.json`, `priority_matrix.json`, `scoring_rules.json`, doctrines CCN et Sites |

**Types de documents couverts :**

- **Stratégie Nationale pour le Service Universel** ;
- **matrice officielle de priorisation** ;
- **critères officiels des CCN** ;
- **doctrines** métier (Sites, CCN, Subventions, Gouvernance…) ;
- **politiques** d'intégration et de gouvernance des données ;
- **référentiels institutionnels** (nomenclature, couverture, territoires, programmes).

### 1A.2 Principe fondamental : les moteurs ne remplacent jamais les documents

Les moteurs du SIG-FDSU RDC — priorisation, scoring, Spatial Decision Graph, Explainable Decision Engine, simulations — **ne remplacent jamais** les documents officiels FDSU.

Ils en constituent l'**implémentation opérationnelle** :

| Couche | Rôle |
|--------|------|
| **Documents officiels** | Autorité normative ; référence institutionnelle ; version de vérité juridique et stratégique |
| **Règles métier** | Traduction structurée et versionnée des critères officiels |
| **Référentiels** | Données nationales intégrées, qualifiées et gouvernées |
| **Moteurs** | Application explicable des règles sur les référentiels |
| **Décisions** | Recommandations et dossiers traçables, toujours reliés à la source documentaire |

Aucun score, aucune priorité et aucune recommandation ne peut prétendre à une valeur institutionnelle si elle n'est pas **rattachée** à un document officiel, une règle métier dérivée ou un référentiel sourcé.

### 1A.3 Chaîne de dérivation institutionnelle

```text
Documents officiels FDSU
        ↓
Règles métier
        ↓
Référentiels
        ↓
Moteurs
        ↓
Décisions
```

**Lecture de la chaîne :**

1. **Documents officiels FDSU** — stratégie, matrices, critères CCN, nomenclatures, politiques ;
2. **Règles métier** — critères, seuils, typologies et doctrines externalisées (`data/business/`) ;
3. **Référentiels** — actifs, territoires, couverture, sectoriels, intégrés via le National Data Fabric ;
4. **Moteurs** — priorisation, SDG, NSME, Decision Intelligence, simulations ;
5. **Décisions** — Decision Case, recommandations DG, rapports, justifications VGF.

Cette chaîne garantit que le SIG-FDSU RDC est le **système institutionnel de mise en œuvre** de la Stratégie Nationale pour le Service Universel — et non une couche applicative autonome.

---

## 1B. Bibliothèque Stratégique FDSU

La **Bibliothèque Stratégique FDSU** est la future **mémoire institutionnelle** de la plateforme. Elle consolide l'ensemble des documents officiels, doctrines, politiques et référentiels normatifs dans un espace unique, gouverné et traçable.

### 1B.1 Ambition

Devenir le référentiel documentaire central permettant à tout acteur FDSU — direction, analystes, partenaires, auditeurs — de comprendre **d'où viennent** les règles appliquées par la plateforme et **comment** elles se traduisent en décisions.

### 1B.2 Contenu cible

| Catégorie | Exemples |
|-----------|----------|
| Stratégie et programmes | Stratégie Nationale SU, stratégie CCN 2026–2030, plans de déploiement |
| Matrices et critères | Matrice de priorisation Sites 300, critères officiels CCN, classes S1–S4 |
| Doctrines | Doctrine CCN, Doctrine Sites, Subventions, Gouvernance, Télécom |
| Politiques | Data First, gouvernance des données, intégration référentielle |
| Référentiels institutionnels | Nomenclature FDSU, catalogues programmes, statuts de cycle de vie |

### 1B.3 Traçabilité complète — liens documentaires

Chaque document de la Bibliothèque Stratégique devra pouvoir être relié, de manière explicite et consultable, à :

| Lien | Description |
|------|-------------|
| **Règles métier** | Critères, seuils, pondérations dérivés du document (`decision_rules.json`, `scoring_rules.json`, doctrines) |
| **Moteurs** | Moteurs de priorisation, SDG, NSME, EDE, simulations — version et paramètres appliqués |
| **Écrans** | Vues cartographiques, tableaux de bord, Decision Case, ESR, parcours CCN |
| **Recommandations** | Propositions affichées, scores, rangs, alertes — avec citation de la règle source |
| **Décisions** | Dossiers formalisés, validations DG, historique décisionnel |
| **Rapports** | Livre Blanc, rapports CA, bailleurs, gouvernementaux, évaluations périodiques |

### 1B.4 Modèle de traçabilité

```text
Document officiel (Bibliothèque Stratégique FDSU)
        │
        ├──→ Règle métier (id, version, article / critère)
        │         │
        │         ├──→ Moteur (nom, version, exécution)
        │         │         │
        │         │         ├──→ Écran / vue
        │         │         ├──→ Recommandation
        │         │         └──→ Décision (Decision Case)
        │         │
        │         └──→ Rapport institutionnel
        │
        └──→ Référentiel intégré (NDF, source, date, qualité)
```

**Exigences de traçabilité :**

1. **Identifiant document** — nom, version, date, auteur institutionnel ;
2. **Lien vers règle** — critère métier et phase décisionnelle concernée ;
3. **Lien vers exécution** — moteur, date d'application, périmètre territorial ;
4. **Lien vers artefact produit** — écran, score, dossier, export PDF ;
5. **Réversibilité** — depuis toute décision, remonter jusqu'au document officiel source.

La Bibliothèque Stratégique FDSU s'appuiera sur les documents déjà indexés dans `data/raw/`, `data/strategic/` et `data/business/doctrines/`, puis sera exposée progressivement via le Knowledge Hub et les parcours décisionnels.

---

## 2. Les cinq missions du SIG-FDSU RDC

La plateforme poursuit **cinq grandes missions**. Chacune correspond à une étape du cycle de valeur institutionnel du FDSU.

### 2.1 Planifier

**Mission :** construire une vision partagée du territoire et des programmes.

- cartographier et structurer les référentiels nationaux ;
- consolider la connaissance territoriale multi-sectorielle ;
- préparer les scénarios et les plans d'intervention ;
- identifier les données manquantes sans les masquer.

**Capacités clés :** Intelligence Territoriale, National Data Fabric, cartographie, Knowledge Hub, référentiels administratifs et sectoriels.

### 2.2 Prioriser

**Mission :** classer les interventions selon des critères métier officiels, explicites et auditables.

- appliquer les matrices de priorisation FDSU (sites, CCN, corridors) ;
- croiser déficit, population, services, faisabilité, coût, impact ;
- produire des scores et des rangs **explicables** ;
- éviter toute « boîte noire » algorithmique.

**Capacités clés :** moteurs de priorisation, Decision Intelligence, NSME, matrices CCN (cf. chapitre 6).

### 2.3 Décider

**Mission :** transformer l'analyse en recommandations et décisions traçables.

- ouvrir un dossier de décision par actif ou territoire ;
- exposer le Spatial Decision Graph et les relations spatiales ;
- documenter la recommandation, la justification et le niveau de confiance ;
- lier la décision aux sources et aux règles appliquées.

**Capacités clés :** Decision Case, Explainable Decision Engine, Spatial Decision Graph, Decision Workspace, Decision Scenarios.

### 2.4 Suivre

**Mission :** monitorer l'exécution des programmes et l'avancement des déploiements.

- suivre les sites, CCN, missions et vagues opérationnelles ;
- comparer planifié vs réalisé ;
- alerter sur les retards, anomalies d'intégration ou écarts de couverture ;
- alimenter la Salle de Pilotage Exécutive.

**Capacités clés :** Executive Situation Room, tableaux de bord, missions, traçabilité des actifs, rapports opérationnels.

### 2.5 Évaluer l'impact

**Mission :** démontrer la **valeur créée** pour les populations — pas seulement ce qui a été déployé.

- mesurer l'évolution de la couverture et de l'inclusion ;
- quantifier les bénéficiaires, écoles connectées, structures de santé impactées ;
- évaluer les CCN opérationnels et les services publics numérisés ;
- produire des rapports pour le CA, les bailleurs et le gouvernement.

**Capacités clés :** pilier Impact / Suivi / Évaluation (cf. chapitre 4), NIF, rapports institutionnels.

---

## 2A. Cycle de vie complet du Service Universel

Le SIG-FDSU RDC couvre désormais **l'intégralité du cycle de vie d'un investissement** du Service Universel — de la vision stratégique à l'amélioration continue. La plateforme n'intervient pas seulement en amont (cartographie, analyse) : elle accompagne **chaque étape** jusqu'à la démonstration des résultats.

### 2A.1 Schéma conceptuel du cycle

```text
Vision stratégique
        ↓
Planification
        ↓
Priorisation
        ↓
Décision
        ↓
Financement
        ↓
Déploiement
        ↓
Exploitation
        ↓
Suivi
        ↓
Évaluation
        ↓
Amélioration continue
```

### 2A.2 Soutien de chaque étape

| Étape | Rôle institutionnel | Soutien plateforme | Documents / règles |
|-------|---------------------|-------------------|-------------------|
| **Vision stratégique** | Orientations nationales FDSU, programmes, séquences | Bibliothèque Stratégique, ESR, Knowledge Hub | Stratégie Nationale SU, stratégie CCN, doctrines |
| **Planification** | Définir où, quand, pour qui intervenir | Intelligence Territoriale, cartographie, NDF | Nomenclature FDSU, référentiels territoriaux (`data/raw/`) |
| **Priorisation** | Classer les interventions selon critères officiels | Matrices, scoring, NSME, moteurs CCN / Sites | Matrice officielle de priorisation, `decision_rules.json` |
| **Décision** | Valider, justifier, formaliser | Decision Case, SDG, EDE, Explainability | Doctrines, règles métier, dossiers traçables |
| **Financement** | Justifier VGF, subventions, enveloppes | Simulations, scénarios, coûts estimés | `subsidy_rules.json`, critères VGF, politiques FDSU |
| **Déploiement** | Exécuter sur le terrain | Missions, suivi actifs, programmes | Statuts cycle de vie, référentiels opérationnels |
| **Exploitation** | Mettre en service sites, CCN, services | Suivi opérationnel CCN, connectivité, maintenance | Doctrine CCN, catalogues types CCN |
| **Suivi** | Monitorer planifié vs réalisé | ESR, tableaux de bord, alertes | KPI catalog, indicateurs NIF |
| **Évaluation** | Mesurer impacts et valeur créée | Pilier 9 — Impact / Suivi / Évaluation | Critères d'impact, rapports institutionnels |
| **Amélioration continue** | Réviser stratégie, matrices, priorités | Retour Bibliothèque Stratégique, révision règles | Documents officiels mis à jour, nouvelles versions |

### 2A.3 Portée institutionnelle

Chaque étape du cycle est soutenue par la **triade** :

1. **référentiels nationaux** (données intégrées, qualifiées, gouvernées) ;
2. **règles métier** (critères externalisés, versionnés, dérivés des documents officiels) ;
3. **documents officiels FDSU** (Source of Truth — cf. chapitre 1A).

Le SIG-FDSU RDC n'est donc pas seulement une plateforme SIG : c'est le **système institutionnel de mise en œuvre** de la Stratégie Nationale pour le Service Universel, couvrant le cycle complet de la vision à la preuve d'impact.

---

## 3. Les neuf piliers du produit

Le SIG-FDSU RDC repose sur **neuf piliers stratégiques**. Ils structurent l'architecture fonctionnelle et la feuille de route produit.

| # | Pilier | Rôle institutionnel |
|---|--------|---------------------|
| **1** | **Intelligence Territoriale** | Comprendre un territoire dans sa globalité : population, services, infrastructures, programmes, déficits. |
| **2** | **Planification et Priorisation** | Classer les interventions selon critères FDSU explicites ; matrices, scores, scénarios. |
| **3** | **Spatial Decision Graph (SDG)** | Rendre visibles et explicables les relations spatiales entre actifs, besoins, territoires et domaines sectoriels. |
| **4** | **Decision Intelligence** | Transformer données, règles et analyses en dossiers de décision, recommandations et parcours exécutifs. |
| **5** | **National Data Fabric (NDF)** | Gouverner, cataloguer et relier les référentiels nationaux sans duplication anarchique. |
| **6** | **Executive Situation Room (ESR)** | Vue DG : synthèse nationale, alertes, décisions clés, avancement programmes. |
| **7** | **Programme National des CCN** | Programme stratégique de transformation connectivité → services numériques communautaires. |
| **8** | **Gouvernance des Données** | Source de vérité, qualité, traçabilité, Data First, politique d'intégration. |
| **9** | **Impact, Suivi et Évaluation** | Mesurer les résultats des investissements du Service Universel et alimenter l'amélioration continue. |

### 3.1 Intelligence Territoriale

Lecture consolidée d'un territoire (province, territoire, collectivité, zone FDSU) : ce qui existe, ce qui manque, ce qui est en cours, ce qui est prioritaire.

**Référence technique :** [`FDSU_TERRITORIAL_INTELLIGENCE.md`](./FDSU_TERRITORIAL_INTELLIGENCE.md), Territorial Digital Twin, Territorial Summary.

### 3.2 Planification et Priorisation

Capacité transversale : matrices métier, critères officiels FDSU, scoring explicable, équilibre territorial.

**Référence :** moteurs de priorisation, Decision Scenarios, futures matrices CCN.

### 3.3 Spatial Decision Graph

Graphe spatial décisionnel : nœuds (sites, localités, télécom, santé, routes, CCN…), arêtes NSME, statuts par domaine, rayons, nearest context — **sans relation inventée**.

**Référence :** [`SPATIAL_DECISION_GRAPH_V2.md`](./SPATIAL_DECISION_GRAPH_V2.md), [`SDG_DOMAIN_STATUS_AND_INTEGRATION_COHERENCE_V1.md`](./SDG_DOMAIN_STATUS_AND_INTEGRATION_COHERENCE_V1.md).

### 3.4 Decision Intelligence

Ensemble des capacités qui produisent une **expérience de décision** : Decision Case, Explainable Decision Engine, KPI explicables, parcours DG → dossier → recommandation.

**Référence :** [`FDSU_EXPLAINABLE_DECISION_ENGINE.md`](./FDSU_EXPLAINABLE_DECISION_ENGINE.md), [`FDSU_DECISION_EXPERIENCE_LAYER.md`](./FDSU_DECISION_EXPERIENCE_LAYER.md).

### 3.5 National Data Fabric

Couche de gouvernance des référentiels : catalogue, métadonnées, qualité, relations documentées, extensibilité.

**Référence :** [`NATIONAL_DATA_FABRIC_V1.md`](./NATIONAL_DATA_FABRIC_V1.md).

### 3.6 Executive Situation Room

Salle de pilotage DG : vision exécutive, programmes, alertes, décisions — consomme les piliers 1–5 et 9.

**Référence :** [`EXECUTIVE_SITUATION_ROOM_V1.md`](./EXECUTIVE_SITUATION_ROOM_V1.md).

### 3.7 Programme National des CCN

Programme stratégique majeur — **pas un simple module applicatif** (cf. chapitre 5).

### 3.8 Gouvernance des Données

Principes : Référentiel National des Actifs, Data First, traçabilité, Site FDSU ≠ CCN, pas de valeur inventée, maturités d'intégration explicites.

**Référence :** [`DATA_FIRST_INTEGRATION_POLICY.md`](./DATA_FIRST_INTEGRATION_POLICY.md), [`FDSU_MASTER_DATA_MODEL.md`](./FDSU_MASTER_DATA_MODEL.md).

### 3.9 Impact, Suivi et Évaluation

**Pilier stratégique dédié** — cf. chapitre 4.

---

## 4. Pilier 9 — Impact, Suivi et Évaluation

Le SIG-FDSU RDC ne doit pas uniquement aider à **décider**. Il doit **démontrer les résultats** des décisions et des investissements du Service Universel.

### 4.1 Ambition

Permettre au FDSU de répondre, avec preuves, aux questions institutionnelles :

- La couverture numérique a-t-elle progressé ?
- Combien de citoyens bénéficient réellement des interventions ?
- Combien d'écoles et d'établissements de santé sont connectés ?
- Combien de CCN sont opérationnels et utilisés ?
- Quels services publics ont été numérisés ?
- Quel est l'effet sur le développement économique local ?
- Les opérateurs respectent-ils leurs obligations ?

### 4.2 Indicateurs cibles (à terme)

| Domaine | Exemples d'indicateurs |
|---------|------------------------|
| Couverture | Évolution couverture radio / fibre ; réduction zones blanches |
| Inclusion | Citoyens bénéficiaires ; localités desservies |
| Éducation | Écoles connectées ; élèves impactés |
| Santé | Établissements impactés ; télémédecine activée |
| CCN | Centres opérationnels ; fréquentation ; services rendus |
| Services publics | Démarches numérisées ; administrations connectées |
| Économie locale | PME / marchés / agriculture digitalisés |
| Littératie numérique | Formations ; usages mesurés |
| Opérateurs | Conformité aux obligations ; qualité de service |

**Règle :** aucun indicateur affiché sans source, méthode et limite explicites.

### 4.3 Intégration au parcours décisionnel

```text
Planification
      ↓
Priorisation
      ↓
Décision
      ↓
Déploiement
      ↓
Suivi
      ↓
Mesure des résultats
      ↓
Évaluation des impacts
      ↓
Amélioration continue
```

### 4.4 Consommateurs du pilier Impact

- **Executive Situation Room** — tableau de bord DG ;
- **tableaux de bord institutionnels** — directions métiers ;
- **rapports au Conseil d'Administration** ;
- **rapports aux bailleurs** et partenaires techniques ;
- **rapports gouvernementaux** ;
- **évaluations périodiques** de la stratégie nationale FDSU.

### 4.5 Valeur institutionnelle

Ce pilier permet au SIG-FDSU RDC de démontrer non seulement **ce qui a été réalisé**, mais surtout **la valeur créée pour les populations** — condition essentielle de la légitimité et du financement du Service Universel.

---

## 5. Programme National des CCN

Les **Centres Communautaires Numériques (CCN)** constituent un **programme structurant du Service Universel** et un **programme stratégique majeur** du SIG-FDSU RDC. Ils ne doivent plus être présentés comme un simple module applicatif.

Le Programme National des CCN traduit dans l'opérationnel une ambition centrale de la Stratégie Nationale : **transformer la connectivité en inclusion numérique mesurable** pour les populations. Il occupe une place symétrique aux programmes Sites FDSU dans l'architecture produit.

### 5.1 Définition institutionnelle

Un CCN est un **actif de service numérique** du FDSU : il transforme la connectivité (fournie par les sites FDSU) en **accès population**, usages, formation et services locaux.

| | Site FDSU | CCN |
|---|-----------|-----|
| Nature | Infrastructure / connectivité | Service numérique communautaire |
| Apporte | Couverture réseau | Accès, usages, impacts sociaux |
| Relation | Alimente le CCN | Sert la population |

### 5.2 Rôle dans la stratégie nationale

1. **Réduction de la fracture numérique** — accès local aux services numériques dans les territoires mal desservis ;
2. **Développement local** — ancrage des usages numériques dans l'économie et l'administration de proximité ;
3. **Littératie numérique** — formation, accompagnement, inclusion des publics vulnérables ;
4. **Services publics numériques** — e-administration, e-santé, e-éducation, information citoyenne ;
5. **Mesure d'impact social** — fréquentation, services rendus, satisfaction, effets mesurables.

### 5.3 Position dans l'architecture produit

Le Programme National des CCN s'appuie sur :

- le **Référentiel National des Actifs** (entité CCN gouvernée) ;
- l'**Intelligence Territoriale** (où implanter, pourquoi) ;
- la **Planification et Priorisation** (matrice CCN — cf. chapitre 6) ;
- le **Spatial Decision Graph** (relations site ↔ CCN ↔ services) ;
- la **Decision Intelligence** (dossier CCN, recommandation) ;
- le pilier **Impact / Suivi / Évaluation** (résultats opérationnels).

**Référence existante :** [`FDSU_CCN_BUSINESS_MODEL.md`](./FDSU_CCN_BUSINESS_MODEL.md).

### 5.4 Ancrage dans les documents officiels FDSU

Le Programme National des CCN est **directement guidé** par les documents officiels déjà présents dans le dépôt. Ceux-ci restent les **références institutionnelles** du futur moteur CCN — la plateforme ne crée pas de critères parallèles.

| Document / source | Rôle pour le programme CCN |
|-------------------|---------------------------|
| **`data/strategic/strategie_fdsu_ccn_2026_2030.docx`** | Stratégie Nationale CCN, orientations, séquences de déploiement, logique territoriale |
| **`data/strategic/matrice_priorisation_300_sites.xlsx`** | Matrice officielle de priorisation — critères, rangs, typologie S1–S4 |
| **`data/raw/FDSU Structure code Territoire zones.xlsx`** | Nomenclature et structure territoriale officielle FDSU |
| **`data/raw/`** (couverture, localités) | Déficit de couverture, localités non couvertes, population |
| **`data/business/doctrines/ccn_doctrine_v1.json`** | Doctrine CCN opérationnelle dérivée des documents stratégiques |
| **`data/business/decision_rules.json`** | Critères officiels structurés pour priorisation et simulation |

### 5.5 Pilotage par les critères et la matrice officiels

Les **critères officiels FDSU** et la **matrice officielle de priorisation** guident directement, à terme, l'ensemble du parcours CCN :

| Phase du parcours CCN | Guidage documentaire |
|----------------------|---------------------|
| **Sélection des sites** | Nomenclature FDSU, classes stratégiques, déficit de couverture, référentiels territoriaux |
| **Scoring** | Critères officiels CCN, matrice de priorisation, règles métier versionnées |
| **Priorisation** | Matrice officielle, équilibre territorial, séquences stratégiques 2026–2030 |
| **Choix du type de CCN** | Doctrine CCN, typologie (Social, Éducatif, Administratif, Entrepreneurial, Mixte) |
| **Simulations d'impact** | Critères d'impact social, population, services publics, coûts VGF |
| **Suivi des déploiements** | Statuts cycle de vie, indicateurs opérationnels, pilier Impact / Suivi / Évaluation |

Chaque phase produit un artefact **relié à la Bibliothèque Stratégique FDSU** (cf. chapitre 1B) : depuis une priorité CCN affichée, il doit être possible de remonter au critère officiel, au document source et à la version de la matrice appliquée.

### 5.6 Position dans le cycle de vie du Service Universel

Le Programme National des CCN s'inscrit sur l'ensemble du cycle de vie (cf. chapitre 2A) :

- **Planification** — où implanter les CCN, dans quel territoire, pour quelle population ;
- **Priorisation** — classement selon la matrice officielle ;
- **Décision** — dossier CCN, choix de site et de type, justification VGF ;
- **Financement** — simulation des coûts et subventions ;
- **Déploiement et exploitation** — mise en service, connectivité via sites FDSU ;
- **Suivi et évaluation** — fréquentation, services rendus, impact social, rapports institutionnels.

Le CCN est ainsi le **vecteur opérationnel** par lequel le Service Universel se matérialise au plus près des populations.

---

## 6. Matrice de priorisation CCN (futur moteur)

### 6.1 Objectif

Définir le **futur moteur de priorisation des CCN**, aligné sur les critères officiels du FDSU et calqué sur la **matrice officielle** déjà présente dans le dépôt (`data/strategic/matrice_priorisation_300_sites.xlsx`, critères structurés dans `data/business/decision_rules.json`). Chaque critère sera **explicable** : source, règle, poids, limite — **aucune boîte noire**. Les documents officiels de `data/raw/` et `data/strategic/` restent les références institutionnelles ; le moteur n'en est que l'implémentation opérationnelle (cf. chapitre 1A).

### 6.2 Classes stratégiques S1 à S4

| Classe | Signification indicative | Usage priorisation |
|--------|-------------------------|-------------------|
| **S1** | Territoire à impact stratégique maximal | Priorité nationale absolue |
| **S2** | Territoire à fort potentiel / déficit élevé | Priorité haute |
| **S3** | Territoire intermédiaire | Priorisation conditionnelle |
| **S4** | Territoire à faible urgence relative | Report ou phase ultérieure |

*Les définitions exactes S1–S4 seront calibrées avec la Direction FDSU et documentées dans la doctrine CCN.*

### 6.3 Critères de scoring (catalogue officiel cible)

| # | Critère | Description | Source typique |
|---|---------|-------------|----------------|
| 1 | **Classe stratégique S1–S4** | Importance territoriale FDSU | Doctrine / planification nationale |
| 2 | **Déficit de couverture** | Écart entre besoin et couverture existante | NCI, télécom, NSME |
| 3 | **Population** | Population desservie ou à desservir | Démographie, localités |
| 4 | **Établissements scolaires** | Écoles, collèges, lycées à proximité | Référentiel Éducation (cible) |
| 5 | **Établissements de santé** | Centres de santé, hôpitaux | Référentiel Santé |
| 6 | **Administrations** | Présence services administratifs | Référentiel administration |
| 7 | **Marchés** | Centres économiques locaux | Référentiel Économie (cible) |
| 8 | **Agriculture** | Potentiel agricole / chaînes valeur | Référentiel Agriculture (cible) |
| 9 | **Mines** | Corridors miniers, activité extractive | Référentiel Économie / mines (cible) |
| 10 | **Corridors** | Axes de développement prioritaires | Planification nationale |
| 11 | **Énergie** | Disponibilité / déficit énergétique | Référentiel Énergie (cible) |
| 12 | **Fibre** | Proximité backbone / fibre | Référentiel télécom |
| 13 | **Accessibilité** | Distance, routes, saisonnalité | Transport, NSME |
| 14 | **Sécurité** | Contexte sécuritaire du déploiement | Données terrain (cible) |
| 15 | **Faisabilité technique** | Faisabilité radio, fibre, énergie | Ingénierie FDSU |
| 16 | **Coût estimé** | Enveloppe prévisionnelle VGF | Estimation métier |
| 17 | **Impact social** | Bénéficiaires estimés, inclusion | Matrice impact |
| 18 | **Équilibre territorial** | Répartition géographique équitable | Règle nationale |

### 6.4 Principes du moteur

1. **Explicabilité totale** — chaque point de score affiche critère, valeur, source, règle ;
2. **Data First** — si un référentiel n'est pas intégré, le critère est « en cours d'intégration », jamais simulé ;
3. **Pas de score unique opaque** — décomposition visible par critère ;
4. **Traçabilité** — version de la matrice, date, auteur de la calibration ;
5. **Révision institutionnelle** — la matrice est un artefact gouverné, pas un paramètre technique.

---

## 7. Parcours décisionnel CCN

Parcours cible du Programme National des CCN, de l'analyse territoriale à l'évaluation.

```text
Analyse territoriale
        ↓
Scoring (matrice CCN)
        ↓
Priorisation
        ↓
Choix du site
        ↓
Choix du type de CCN
        ↓
Simulation des impacts
        ↓
Décision
        ↓
Déploiement
        ↓
Suivi
        ↓
Évaluation
```

### 7.1 Détail des étapes

| Étape | Description | Capacités plateforme |
|-------|-------------|---------------------|
| **Analyse territoriale** | Comprendre le territoire, la population, les services, le déficit | TI, TDT, cartographie, NDF |
| **Scoring** | Appliquer la matrice CCN critère par critère | Moteur priorisation CCN (cible) |
| **Priorisation** | Classer les candidats CCN | Planification & Priorisation |
| **Choix du site** | Sélectionner l'implantation (site FDSU ou lieu d'accueil) | Géocodage, NSME, SDG |
| **Choix du type de CCN** | Modèle de service, équipements, catalogue | Doctrine CCN, Decision Case |
| **Simulation des impacts** | Estimer bénéficiaires, coûts, effets | Decision Scenarios (cible CCN) |
| **Décision** | Recommandation formalisée, traçable | Decision Intelligence, ESR |
| **Déploiement** | Exécution terrain, missions | Missions, suivi actifs |
| **Suivi** | État opérationnel, connectivité, maintenance | CCN operational, rapports |
| **Évaluation** | Mesure des résultats et valeur créée | Pilier Impact / Suivi / Évaluation |

---

## 8. Design System institutionnel FDSU

### 8.1 Principe

Toute l'identité visuelle du SIG-FDSU RDC doit s'inspirer de l'**identité officielle du FDSU**. L'objectif n'est pas de copier le site web institutionnel, mais de garantir une **cohérence visuelle** avec l'institution que la plateforme sert.

### 8.2 Référence

Le **site officiel du FDSU** sert de référence pour :

- les **couleurs institutionnelles** ;
- le **logo** et les règles d'usage ;
- les **principes graphiques** (typographie, espacements, iconographie) ;
- les **standards de présentation** institutionnelle (rapports, slides, captures).

### 8.3 Futur Design System produit

Le Design System SIG-FDSU (tokens, composants, cartographie, rapports) sera construit à partir de :

| Élément | Application |
|---------|-------------|
| Couleurs institutionnelles | UI dashboard, cartes, rapports, présentations |
| Logo FDSU | En-têtes, exports, mode Démonstration |
| Principes graphiques FDSU | Cohérence avec communication institutionnelle |
| Standards présentation | Livre Blanc, Présentation Exécutive, ESR, captures officielles |

### 8.4 Règles

1. **Cohérence institutionnelle** — un décideur doit reconnaître le FDSU dans l'interface ;
2. **Lisibilité exécutive** — contrastes, typographie, hiérarchie adaptés aux réunions DG ;
3. **Pas de décoratif** — Zero Decorative Actions ; chaque élément visuel a une fonction ;
4. **Cartographie premium** — expérience digne d'une plateforme nationale (cf. Decision Experience Premium) ;
5. **Validation institutionnelle** — charte graphique soumise à validation DG / communication FDSU avant généralisation.

**Référence existante :** `PROJECT_MANAGEMENT/PRESENTATION_SIG_FDSU_RDC_ASSETS/layout/CHARTE_GRAPHIQUE_V2.md`.

---

## 9. Référentiels nationaux — feuille de route des données

### 9.1 Principe directeur

Le SIG-FDSU RDC progresse par **intégration progressive** des référentiels nationaux via le National Data Fabric. Aucun référentiel n'est « déclaré intégré » sans API, qualité documentée et exploitation réelle dans au moins un parcours décisionnel.

### 9.2 Référentiels déjà intégrés (ou partiellement opérationnels)

| Référentiel | État | Usage principal |
|-------------|------|-----------------|
| **Hiérarchie administrative FDSU** | Opérationnel | Zones, provinces, territoires, collectivités, groupements, localités |
| **Sites FDSU** | Opérationnel | Programmes 40 / 300 / national, priorisation, SDG |
| **CCN (jeu DEMO + socle)** | Partiel | Programme CCN, démonstration DG |
| **Télécommunications** | Partiel | Vodacom, Orange, fibre, MW, FTTX, PostGIS |
| **Santé** | Partiel | Établissements de santé, SDG domaine santé |
| **Routes / transport** | Partiel | Routes principales, accessibilité |
| **Missions terrain** | Partiel | Opérations, traçabilité |
| **Décision / cas** | Opérationnel | Decision Case, historique (hors commit runtime) |
| **Profils territoriaux / CNCT** | Socle | Base nationale de connaissances |

### 9.3 Référentiels en cours d'intégration

| Référentiel | Priorité | Statut |
|-------------|----------|--------|
| **Couverture radio réelle** | Haute | Référencé, exploitation partielle |
| **Données de terrain validées** | Haute | Missions + workflow validation |
| **CCN production (hors DEMO)** | Haute | Doctrine v1, en attente référentiel officiel |
| **Démographie fine** | Moyenne | Croisement population / localités |
| **Relations NSME complètes** | Haute | SDG 2.2, matching rules |

### 9.4 Référentiels prioritaires (prochaines vagues)

| Référentiel | Justification stratégique FDSU |
|-------------|-------------------------------|
| **Éducation** | CCN, écoles connectées, impact inclusion |
| **Énergie** | Faisabilité CCN et sites, alimentation |
| **Agriculture** | Développement local, corridors ruraux |
| **Économie / marchés / PME** | Ancrage économique des CCN |
| **Administration / services publics** | e-services, points d'accès |
| **Mines / corridors extractifs** | Priorisation territoriale S1–S2 |
| **Couverture radio opérateurs (obligations)** | Conformité, VGF, planification |

### 9.5 Référentiels futurs

| Référentiel | Horizon |
|-------------|---------|
| Littératie numérique (indicateurs) | Post-CCN déploiement massif |
| Qualité de service mesurée (QoS) | Obligations opérateurs |
| Impact social post-déploiement | Pilier 9 |
| Finances / subventions / VGF | Traçabilité investissements |
| Partenaires / bailleurs | Rapports multi-acteurs |

### 9.6 Accent sectoriel (vision V1.0)

Les référentiels **Éducation**, **Énergie**, **Agriculture**, **Économie**, **Couverture radio réelle**, **Données de terrain**, **Démographie** et **Services publics** sont identifiés comme **leviers structurants** de la prochaine phase produit — en particulier pour la matrice CCN et le pilier Impact / Suivi / Évaluation.

---

## 10. Cartographie des piliers et modules (vue d'ensemble)

```text
                    STRATÉGIE NATIONALE FDSU
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   PLANIFIER            PRIORISER              DÉCIDER
        │                     │                     │
        └──────────┬──────────┴──────────┬──────────┘
                   ▼                     ▼
         Intelligence Territoriale   Decision Intelligence
         National Data Fabric       Spatial Decision Graph
         Cartographie               Decision Case / EDE
                   │                     │
                   └──────────┬──────────┘
                              ▼
                    SUIVRE · ÉVALUER L'IMPACT
                              │
              Executive Situation Room · Pilier 9
                              │
              Programme National CCN (transversal)
```

---

## 11. Principes non négociables (hérités et confirmés)

1. **Data First** — exploiter toute donnée disponible ; signaler explicitement ce qui manque.
2. **No Black Box** — toute recommandation, score ou statut est explicable.
3. **Site FDSU ≠ CCN** — actifs distincts, relations explicites.
4. **Zero Decorative Actions** — aucun bouton ou widget sans fonction réelle.
5. **Traçabilité** — source, date, confiance, version sur toute information sensible.
6. **Une source de vérité** — Référentiel National des Actifs + NDF.
7. **Décision humaine** — la plateforme informe ; elle ne décide pas à la place des responsables.

---

## 12. Vision V1.0 — conclusion

Le **SIG-FDSU RDC** doit devenir la **plateforme nationale de référence** permettant au Fonds de Développement du Service Universel de :

- **planifier** les interventions sur l'ensemble du territoire ;
- **prioriser** les investissements selon des critères officiels et explicables ;
- **justifier** les décisions, y compris les demandes de Viability Gap Funding ;
- **suivre** l'exécution des programmes sites, CCN et infrastructures ;
- **évaluer** les impacts réels pour les populations.

Cette plateforme n'est pas un outil cartographique. C'est l'**environnement national** où la stratégie du Service Universel devient **visible, mesurable, explicable et auditable** — et le **système institutionnel de mise en œuvre** de la Stratégie Nationale pour le Service Universel, de la vision stratégique à l'amélioration continue (cf. chapitres 1A, 1B, 2A).

Le présent document — **Business Architecture & Functional Blueprint V1.0** — constitue la **base officielle** de tous les futurs développements, sprints produit, validations institutionnelles et communications du projet SIG-FDSU RDC.

---

## 13. Vision V1.1 — Vers la Plateforme Nationale d'Intelligence du Service Universel

> **Extension de la vision stratégique — évolutions futures, non développements immédiats.**

Le Business Blueprint V1.0 décrit l'architecture métier et les capacités actuelles ou en cours. Le présent chapitre V1.1 projette l'**évolution stratégique** du SIG-FDSU RDC vers une plateforme d'intelligence institutionnelle intégrée — au-delà du SIG et au-delà de la seule gestion de référentiels spatiaux.

### 13.1 Ambition V1.1

Le SIG-FDSU RDC évoluera vers une **Plateforme Nationale d'Intelligence du Service Universel** : un environnement où données territoriales, connaissances institutionnelles, règles métier et décisions forment un **système cohérent, traçable et explicable**, au service de la Stratégie Nationale FDSU.

---

### 13.2 FDSU Digital Knowledge Graph

Le projet introduit officiellement le concept de **FDSU Digital Knowledge Graph** (DKG).

Le SIG-FDSU RDC ne manipulera plus uniquement :

- des **données spatiales** ;
- des **référentiels**.

Il manipulera également :

- les **connaissances institutionnelles** ;
- les **stratégies** ;
- les **politiques** ;
- les **doctrines** ;
- les **matrices** ;
- les **décisions**.

Le FDSU Digital Knowledge Graph est le **graphe de connaissance institutionnelle** qui relie ces entités entre elles et avec les actifs territoriaux, les programmes et les impacts mesurés. Il complète le Spatial Decision Graph (relations spatiales) par une couche de **sens métier et de provenance documentaire**.

| Couche | Objet | Rôle |
|--------|-------|------|
| **Spatial Decision Graph** | Relations spatiales actifs ↔ territoires ↔ besoins | Comprendre le *où* et le *avec quoi* |
| **FDSU Digital Knowledge Graph** | Relations documentaires stratégie ↔ règles ↔ décisions ↔ impacts | Comprendre le *pourquoi* et le *d'où* |

---

### 13.3 Objectif — chaîne de liaison automatique

Le FDSU Digital Knowledge Graph permettra au SIG de relier automatiquement :

```text
Document officiel
        ↓
Chapitre
        ↓
Objectif stratégique
        ↓
Programme
        ↓
Critère
        ↓
Règle métier
        ↓
Référentiel
        ↓
Analyse
        ↓
Décision
        ↓
Impact
```

Chaque maillon de cette chaîne sera **navigable** : depuis un impact mesuré, remonter jusqu'au document officiel ; depuis un document stratégique, descendre jusqu'aux décisions et aux résultats qu'il a produits.

---

### 13.4 Bibliothèque Stratégique Vivante

La **Bibliothèque Stratégique FDSU** (cf. chapitre 1B) évoluera vers une **Bibliothèque Stratégique Vivante**. Elle ne sera pas un simple dépôt documentaire statique.

Chaque document indexé devra exposer explicitement :

| Exposition | Description |
|------------|-------------|
| **Objectifs** | Objectifs stratégiques que le document porte ou contribue à atteindre |
| **Programmes concernés** | Sites FDSU, CCN, subventions, secteurs, vagues opérationnelles |
| **Règles métier dérivées** | Critères, seuils, typologies issus du document (`data/business/`) |
| **Moteurs qui l'utilisent** | Priorisation, SDG, NSME, EDE, simulations CCN / Sites |
| **Tableaux de bord concernés** | ESR, vues priorisation, Decision Case, rapports sectoriels |
| **Décisions concernées** | Dossiers de décision, recommandations, validations DG |
| **Rapports concernés** | Livre Blanc, CA, bailleurs, gouvernement, évaluations périodiques |

La Bibliothèque devient ainsi le **noyau documentaire actif** du FDSU Digital Knowledge Graph — chaque document est un nœud connecté, pas une archive isolée.

---

### 13.5 Traçabilité complète — réponses automatiques au « pourquoi »

À terme, le SIG-FDSU RDC devra pouvoir répondre automatiquement aux questions institutionnelles suivantes, en remontant jusqu'au **document officiel correspondant** :

| Question | Remontée attendue |
|----------|-------------------|
| **Pourquoi ce site ?** | Critère, matrice, programme, objectif stratégique, document source |
| **Pourquoi cette décision ?** | Règle métier, analyse, recommandation, dossier Decision Case, doctrine |
| **Pourquoi cette priorité ?** | Score décomposé, critères officiels, matrice de priorisation, classe S1–S4 |
| **Pourquoi ce CCN ?** | Parcours CCN, typologie, territoire, stratégie CCN 2026–2030 |
| **Pourquoi ce score ?** | Valeur par critère, source référentiel, règle appliquée, version moteur |

Cette traçabilité est la condition de la **confiance institutionnelle** : aucune priorité, aucun score et aucune recommandation ne peut rester opaque face à la Direction, au Conseil d'Administration ou aux partenaires.

---

### 13.6 Programme National des CCN — moteur exclusivement documentaire

Les CCN deviennent un **programme national structurant** du Service Universel (cf. chapitre 5). Le futur **moteur CCN** devra être construit **exclusivement** à partir de :

- la **stratégie nationale** (`data/strategic/strategie_fdsu_ccn_2026_2030.docx`) ;
- les **critères officiels FDSU** (`data/business/decision_rules.json`, doctrines) ;
- la **matrice officielle de priorisation** (`data/strategic/matrice_priorisation_300_sites.xlsx`) ;
- les **doctrines du Service Universel** (`data/business/doctrines/`).

**Règle absolue :** aucune règle métier ne devra être inventée sans **justification documentaire** explicite. Toute règle ajoutée au moteur CCN devra référencer son document source, son auteur institutionnel et sa version.

---

### 13.7 Référentiels officiels — sources de vérité permanentes

Les documents présents dans :

| Emplacement | Rôle |
|-------------|------|
| **`data/raw/`** | Référentiels et jeux de données officiels bruts (nomenclature, couverture, territoires, infrastructures) |
| **`data/strategic/`** | Documents stratégiques normatifs (stratégie, matrices de priorisation) |
| **`data/business/`** | Règles métier structurées dérivées — jamais autonomes vis-à-vis des sources officielles |

constituent les **sources officielles de vérité** du projet.

Les moteurs du SIG — présents et futurs — devront **toujours rester alignés** sur ces documents. Toute dérive entre un moteur en production et un document officiel mis à jour constitue une **anomalie d'intégration bloquante** (cf. politique Data First et Integrity Gate).

---

### 13.8 Service Universel — au-delà de la connectivité

Le SIG-FDSU RDC ne doit **jamais** être présenté comme une plateforme de **connectivité uniquement**.

La connectivité constitue un **levier** — les sites FDSU et les infrastructures télécom sont des moyens, non une finalité.

L'**objectif final** du Service Universel est :

- l'**accès aux services numériques** ;
- l'**éducation** ;
- la **santé** ;
- les **services publics** ;
- le **développement économique** ;
- l'**inclusion numérique** ;
- la **réduction durable de la fracture numérique**.

**Exigence V1.1 :** tous les futurs modules devront **démontrer leur contribution** à ces objectifs. Un module qui ne peut pas expliquer son lien avec l'un de ces leviers d'impact n'a pas sa place dans la feuille de route produit.

---

### 13.9 Conclusion V1.1

Le **SIG-FDSU RDC** constitue la **traduction numérique de la Stratégie Nationale du Service Universel**.

La plateforme a vocation à devenir le **système national de référence** pour la planification, la priorisation, le suivi, l'évaluation et la gouvernance des investissements du Service Universel en République Démocratique du Congo.

À travers le **FDSU Digital Knowledge Graph**, la **Bibliothèque Stratégique Vivante** et la **traçabilité complète** document → décision → impact, le SIG-FDSU RDC dépassera le statut de plateforme SIG pour devenir l'**intelligence institutionnelle** du Fonds de Développement du Service Universel.

---

## Annexe A — Glossaire complémentaire

| Terme | Définition |
|-------|------------|
| **VGF** | Viability Gap Funding — financement comblant l'écart de viabilité économique |
| **CCN** | Centre Communautaire Numérique — programme et actif de service numérique |
| **NDF** | National Data Fabric — gouvernance des référentiels |
| **SDG** | Spatial Decision Graph — graphe spatial décisionnel explicable |
| **NSME** | National Spatial Matching Engine — correspondances spatiales actifs ↔ besoins |
| **NCI** | National Coverage Intelligence — intelligence de couverture |
| **ESR** | Executive Situation Room — salle de pilotage DG |
| **EDE** | Explainable Decision Engine — moteur de décision explicable |
| **NIF** | National Indicators Framework — cadre d'indicateurs nationaux |
| **Data First** | Doctrine d'exploitation maximale des données existantes |
| **Source of Truth** | Documents officiels FDSU (`data/raw/`, `data/strategic/`) — autorité normative du projet |
| **Bibliothèque Stratégique FDSU** | Mémoire institutionnelle documentaire de la plateforme, avec traçabilité vers règles, moteurs et décisions |
| **FDSU Digital Knowledge Graph (DKG)** | Graphe de connaissance institutionnelle reliant documents, stratégies, règles, programmes, décisions et impacts |
| **Bibliothèque Stratégique Vivante** | Évolution de la Bibliothèque Stratégique — documents connectés et exposant objectifs, programmes, moteurs et décisions |

---

## Annexe B — Historique documentaire

| Version | Date | Nature |
|---------|------|--------|
| **1.0** | 2026-07-14 | Première édition — Business Blueprint officiel, 9 piliers, CCN programme, matrice priorisation, Design System FDSU |
| **1.0 compl.** | 2026-07-14 | Revue d'architecture — Documents officiels FDSU (Source of Truth), Bibliothèque Stratégique, renforcement CCN, cycle de vie complet SU |
| **1.1** | 2026-07-14 | Extension vision stratégique — FDSU Digital Knowledge Graph, Bibliothèque Stratégique Vivante, traçabilité complète, Service Universel au-delà de la connectivité |

---

*Document produit dans le cadre de l'évolution de la vision produit SIG-FDSU RDC — aucun développement applicatif associé.*
