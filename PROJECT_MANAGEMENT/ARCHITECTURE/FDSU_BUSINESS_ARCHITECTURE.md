# SIG-FDSU RDC — Business Architecture

**Statut :** Document de référence d’architecture métier  
**Date :** 10 juillet 2026  
**Périmètre :** Relier stratégie FDSU ↔ métiers ↔ capacités ↔ données ↔ plateforme  
**Règle :** Documentation uniquement — aucun changement API / services

**Documents liés :**
- [`FDSU_ENTERPRISE_BUSINESS_MODEL.md`](./FDSU_ENTERPRISE_BUSINESS_MODEL.md) — modèle métier d’entreprise (EBM)
- [`FDSU_BUSINESS_CAPABILITIES.md`](./FDSU_BUSINESS_CAPABILITIES.md) — cartographie des Business Capabilities
- [`FDSU_MASTER_DATA_MODEL.md`](./FDSU_MASTER_DATA_MODEL.md) — Référentiel National des Actifs
- [`FDSU_CCN_BUSINESS_MODEL.md`](./FDSU_CCN_BUSINESS_MODEL.md) — Capability CCN
- [`FDSU_KNOWLEDGE_HUB.md`](./FDSU_KNOWLEDGE_HUB.md) — Knowledge Hub & National Indicators Framework
- [`SIG_FDSU_RDC_V1_FUNCTIONAL_ARCHITECTURE.md`](./SIG_FDSU_RDC_V1_FUNCTIONAL_ARCHITECTURE.md) — architecture fonctionnelle

---

## A. Vision stratégique du FDSU

Le Fonds de Développement du Service Universel (FDSU) vise à réduire la fracture numérique en République démocratique du Congo en déployant, sur 5 ans, un programme national de connectivité et de services numériques au bénéfice des populations et des territoires mal desservis.

Le **SIG-FDSU RDC** est la plateforme nationale d’intelligence territoriale qui permet de **connaître**, **prioriser**, **décider** et **piloter** ce déploiement de façon traçable et explicable.

---

## B. Mission

Mettre à disposition de la Direction Générale et des équipes opérationnelles un système d’information géographique et décisionnel capable de :

1. référencer les actifs FDSU (sites, CCN, infrastructures, programmes) ;
2. consolider la connaissance territoriale et sectorielle ;
3. prioriser les interventions selon des critères métier calibrés ;
4. produire des décisions gouvernées et auditables ;
5. suivre l’exécution des programmes nationaux.

---

## C. Objectifs nationaux

| Objectif | Description |
|---|---|
| **O1 — Couverture** | Étendre la connectivité sur le territoire national (programme 20 476 sites) |
| **O2 — Inclusion** | Transformer la connectivité en services numériques accessibles (CCN) |
| **O3 — Priorisation** | Allouer les efforts là où l’impact social et le déficit sont les plus élevés |
| **O4 — Traçabilité** | Garantir une source de vérité unique et une gouvernance des données |
| **O5 — Pilotage** | Donner à la DG une vision nationale consolidée (Salle de Pilotage) |

---

## D. Programmes FDSU

| Programme / vague | Rôle |
|---|---|
| **Sites 20 476** | Programme national complet (cadre stratégique 5 ans) |
| **Sites 40** | Phase pilote |
| **Sites 300** | Première vague opérationnelle / calibration de priorisation |
| **CCN** | Couche service numérique (distincte des sites) |
| **Subventions / projets** | Mécanismes de financement (capacité à construire) |

Les vagues 40 et 300 ne sont **pas** des référentiels concurrents : ce sont des **découpages opérationnels** du programme national.

---

## E. Actifs FDSU

Un actif FDSU est une entité métier gouvernée par le Référentiel National (`uuid` + `business_id` + cycle de vie + traçabilité).

Actifs principaux :

- Site FDSU (connectivité) — nomenclature officielle `data/raw/FDSU Structure code Territoire zones.xlsx`
- CCN (service numérique) — actif distinct ; schéma `FDSU_CCN_*` préparatoire non officiel
- Programme / Vague / Projet
- Infrastructure télécom / Fibre
- Services publics (santé, école, marché…)
- Mission, Score, Recommandation, Décision, Partenaire, Source

Référence : [`FDSU_ENTERPRISE_BUSINESS_MODEL.md`](./FDSU_ENTERPRISE_BUSINESS_MODEL.md) · [`FDSU_MASTER_DATA_MODEL.md`](./FDSU_MASTER_DATA_MODEL.md)

---

## F. Capacités métier

| ID | Capacité |
|---|---|
| 01 | Gestion des Sites FDSU |
| 02 | Gestion des CCN |
| 03 | Gestion des Missions |
| 04 | Gestion des Programmes |
| 05 | Gestion des Partenaires |
| 06 | Gestion des Subventions |
| 07 | Gestion des Infrastructures Télécom |
| 08 | Gestion des Référentiels |
| 09 | Centre de Décision |
| 10 | Salle de Pilotage DG |

Référence : [`FDSU_BUSINESS_CAPABILITIES.md`](./FDSU_BUSINESS_CAPABILITIES.md)

---

## G. Domaines de connaissance

Le Knowledge Hub structure ce que l’on **sait** (sans décider à sa place) :

| Domaine | Contenu |
|---|---|
| Territoire | Hiérarchie, population, accessibilité |
| Connectivité | Opérateurs, couverture, fibre, backbone, qualité |
| Services publics | Santé, éducation, administration, marchés |
| Socio-économique | Agriculture, pêche, élevage, mines, commerce, tourisme, PME |
| Programmes FDSU | Sites, CCN, subventions, projets, vagues |
| Indicateurs nationaux | Catalogue NIF |
| Décision | Règles, matrices, scénarios, simulations, recommandations (structure) |

Référence : [`FDSU_KNOWLEDGE_HUB.md`](./FDSU_KNOWLEDGE_HUB.md)

---

## H. Moteurs de la plateforme

| Moteur | Rôle | Ne fait pas |
|---|---|---|
| **SIG / Cartographie** | Localiser et visualiser | Source de vérité métier |
| **Géocodage intelligent** | Contrôler / corriger les coordonnées | Décider |
| **Moteur de priorisation** | Scorer et classer | Remplacer le référentiel |
| **Knowledge Hub** | Organiser la connaissance | Calculer les recommandations |
| **Decision Engine / Centre de Décision** | Recommander et tracer les décisions | Inventer des actifs |
| **Territorial Intelligence Engine** | (cible) Intelligence territoriale avancée | Pas encore démarré |

---

## I. Référentiels

| Référentiel | Objet |
|---|---|
| **Référentiel National des Actifs** | Source de vérité des entités FDSU |
| **Nomenclature sites** | `data/raw/FDSU Structure code Territoire zones.xlsx` |
| **National Reference Framework** | Référentiels sectoriels (santé, etc.) |
| **Référentiel Télécom** | Infrastructures / opérateurs |
| **Référentiel Santé** | Structures sanitaires |
| **NIF** | Catalogue d’indicateurs nationaux |

---

## J. Gouvernance des données

Principes :

1. Une donnée métier durable passe par le Référentiel National ;
2. Toute connaissance exposée cite une source ou est `pending_source` ;
3. Aucune valeur d’indicateur inventée ;
4. Traçabilité : source, dates, confiance, validation, versions ;
5. Site FDSU ≠ CCN ;
6. Pas d’écrasement silencieux des anomalies.

---

## K. Indicateurs nationaux

Le **National Indicators Framework (NIF)** catalogue les indicateurs mobilisables (connectivité, inclusion, santé, éducation, économie, accessibilité, énergie, priorité FDSU).

État actuel : **structure only** — pas de valeurs chiffrées non sourcées.

---

## L. Centre de Décision

Capability 09 — orchestre intents, KPI explicables, priorisation, simulations, suivi.

Il consomme :

- actifs (Référentiel) ;
- connaissance (Knowledge Hub) ;
- scores (moteur de priorisation) ;

et produit des **recommandations** puis des **décisions** tracées.

---

## M. Salle de Pilotage DG

Capability 10 — cible.

Vue exécutive nationale : avancement programmes, alertes, décisions clés, impacts.  
Elle **consomme** les capacités 01–09 ; elle ne les remplace pas.

---

## 1. Cartographie stratégique → décision

```text
Objectifs stratégiques (O1–O5)
        │
        ▼
Programmes FDSU (20 476 / 40 / 300 / CCN / subventions)
        │
        ▼
Capacités métier (01–10)
        │
        ▼
Référentiels (National, Télécom, Santé, NRF, Nomenclature)
        │
        ▼
Knowledge Hub (domaines + NIF)
        │
        ▼
Decision Engine / Priorisation
        │
        ▼
Recommandations
        │
        ▼
Décisions (Centre de Décision)
        │
        ▼
Pilotage DG (Salle de Pilotage — cible)
```

---

## 2. Questions décisionnelles du FDSU

### 2.1 Connectivité

| Question | Importance | Capacités | Données nécessaires | Indicateurs |
|---|---|---|---|---|
| Où le déficit de couverture est-il le plus critique ? | Oriente le déploiement national | 01, 07, 09 | Couverture, sites, distances | `IND_CONN_COVERAGE_GAP`, `IND_FDSU_PRIORITY_SCORE` |
| Quelle proximité fibre / backbone pour un site candidat ? | Coût et faisabilité technique | 07, 01, 09 | Couches fibre, géométrie sites | `IND_CONN_FIBER_PROXIMITY` |
| Quels opérateurs sont présents sur le territoire ? | Partenariats et options techniques | 07, 05 | Référentiel télécom | `IND_CONN_OPERATOR_PRESENCE` |

### 2.2 Inclusion numérique

| Question | Importance | Capacités | Données nécessaires | Indicateurs |
|---|---|---|---|---|
| Quelles populations restent exclues des services numériques ? | Mission sociale du FDSU | 02, 09, 10 | Population, CCN, accès | `IND_INCL_DIGITAL_ACCESS`, `IND_POP_POPULATION_SIZE` |
| Un CCN améliore-t-il l’accès local aux services ? | Justifie la couche service | 02, 03, 09 | Fréquentation, services CCN | `IND_INCL_CCN_SERVICE_REACH` |

### 2.3 Programmes

| Question | Importance | Capacités | Données nécessaires | Indicateurs |
|---|---|---|---|---|
| Où en sont les vagues 40 / 300 / 20 476 ? | Pilotage d’exécution | 04, 09, 10 | Programmes, sites, statuts | `IND_PROG_SITES_WAVE_COVERAGE` |
| Quelle vague doit absorber un site prioritaire ? | Arbitrage opérationnel | 01, 04, 09 | Priorité, programme, territoire | `IND_FDSU_PRIORITY_LEVEL` |

### 2.4 CCN

| Question | Importance | Capacités | Données nécessaires | Indicateurs |
|---|---|---|---|---|
| Où implanter un CCN en premier ? | Transformer connectivité en service | 02, 01, 09 | Sites, population, lieux hôtes | `IND_INCL_DIGITAL_ACCESS`, `IND_POP_POPULATION_SIZE` |
| Quel lieu hôte (école, santé, marché, admin) ? | Faisabilité et impact | 02, 08, 09 | Services publics, géocodage | `IND_EDU_FACILITY_PRESENCE`, `IND_HEALTH_FACILITY_DENSITY` |
| Le CCN a-t-il une connectivité Site FDSU stable ? | Exploitation | 02, 01, 07 | Lien Site↔CCN, qualité réseau | `IND_CONN_COVERAGE_GAP` |

Référence modèle : [`FDSU_CCN_BUSINESS_MODEL.md`](./FDSU_CCN_BUSINESS_MODEL.md)

### 2.5 Télécommunications

| Question | Importance | Capacités | Données nécessaires | Indicateurs |
|---|---|---|---|---|
| Quelles infrastructures télécom conditionnent le déploiement ? | Planification technique | 07, 01 | Tours, BTS, fibre | `IND_CONN_FIBER_PROXIMITY`, `IND_CONN_OPERATOR_PRESENCE` |

### 2.6 Santé

| Question | Importance | Capacités | Données nécessaires | Indicateurs |
|---|---|---|---|---|
| Un territoire sous-équipé en santé peut-il accueillir un CCN utile ? | Synergie services publics | 08, 02, 09 | Référentiel santé | `IND_HEALTH_FACILITY_DENSITY` |

### 2.7 Éducation

| Question | Importance | Capacités | Données nécessaires | Indicateurs |
|---|---|---|---|---|
| Quelles écoles peuvent héberger un CCN ? | Implantation pragmatique | 02, 08 | Établissements scolaires | `IND_EDU_FACILITY_PRESENCE` |

### 2.8 Économie

| Question | Importance | Capacités | Données nécessaires | Indicateurs |
|---|---|---|---|---|
| Quelles dynamiques économiques locales maximisent l’impact FDSU ? | Priorisation territoriale | 08, 09 | Profils socio-économiques | `IND_ECO_ACTIVITY_PROFILE` |

### 2.9 Pilotage

| Question | Importance | Capacités | Données nécessaires | Indicateurs |
|---|---|---|---|---|
| Quels arbitrages présenter à la DG cette semaine ? | Décision exécutive | 09, 10, 04 | Décisions, alertes, programmes | `IND_FDSU_PRIORITY_SCORE`, `IND_PROG_SITES_WAVE_COVERAGE` |
| Quels sites / CCN sont en dérive d’exécution ? | Suivi opérationnel | 01, 02, 03, 09 | Statuts actifs, missions | niveaux de priorité + statuts actifs |

### 2.10 Gouvernance

| Question | Importance | Capacités | Données nécessaires | Indicateurs |
|---|---|---|---|---|
| La donnée est-elle assez fiable pour décider ? | Qualité décisionnelle | 08, 09 | Source, confiance, validation | métadonnées référentiel / NIF `value_status` |
| Un code site / CCN est-il conforme à la nomenclature ? | Intégrité métier | 01, 02, 08 | Codes, nomenclature officielle | — (règles de codification) |

---

## 3. Principes d’architecture métier

1. **Stratégie → Capacités → Données → Décision** (jamais l’inverse).
2. Le Référentiel National est la source de vérité des **actifs**.
3. Le Knowledge Hub est la source consolidée de la **connaissance**.
4. Le Centre de Décision est le lieu des **arbitrages**.
5. Toute capacité Phase 2+ doit être rattachée à cette Business Architecture.

---

## 4. Recommandations avant / autour du Knowledge Hub

État : les **fondations** du Knowledge Hub et du NIF existent déjà (catalogues + API `/api/knowledge`).

Avant d’aller plus loin (Territorial Intelligence Engine / recommandations automatiques), il est recommandé de :

1. **Valider métier** la Business Architecture et la liste des questions décisionnelles ;
2. **Prioriser 5–10 indicateurs** à sourcer en premier (sans inventer de valeurs) ;
3. **Figer** les responsabilités : Référentiel vs Knowledge Hub vs Decision Engine ;
4. **Aligner** CNCT (`/knowledge`) et Knowledge Hub (`/api/knowledge`) ;
5. **Ne démarrer** le Territorial Intelligence Engine qu’après validation du NIF sourcé sur un premier périmètre (ex. priorité FDSU + déficit couverture + population).

---

## 5. Hors périmètre de ce document

- Développement API / services
- Calcul de recommandations
- Implémentation Salle de Pilotage DG
- Activation nomenclature CCN officielle
