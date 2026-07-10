# SIG-FDSU RDC — Enterprise Business Model (EBM)

**Statut :** Document de référence métier  
**Date :** 10 juillet 2026  
**Périmètre :** Modèle métier d’entreprise — sans refonte des modules existants  
**Documents liés :**
- [`FDSU_BUSINESS_ARCHITECTURE.md`](./FDSU_BUSINESS_ARCHITECTURE.md) — Architecture métier de référence
- [`FDSU_BUSINESS_CAPABILITIES.md`](./FDSU_BUSINESS_CAPABILITIES.md) — Cartographie des Business Capabilities
- [`FDSU_MASTER_DATA_MODEL.md`](./FDSU_MASTER_DATA_MODEL.md) — Référentiel National (application technique du modèle)
- [`FDSU_CCN_BUSINESS_MODEL.md`](./FDSU_CCN_BUSINESS_MODEL.md) — Capability 02 (CCN)
- [`FDSU_KNOWLEDGE_HUB.md`](./FDSU_KNOWLEDGE_HUB.md) — Knowledge Hub & National Indicators Framework
- [`SIG_FDSU_RDC_V1_FUNCTIONAL_ARCHITECTURE.md`](./SIG_FDSU_RDC_V1_FUNCTIONAL_ARCHITECTURE.md) — Architecture fonctionnelle

---

## 1. Vision métier de la plateforme

Le **SIG-FDSU RDC** est la plateforme nationale d’intelligence territoriale du Fonds de Développement du Service Universel (FDSU).

Elle permet de :

1. **Connaître** le territoire et les actifs FDSU (sites, CCN, infrastructures, services) ;
2. **Prioriser** les interventions sur le programme national (20 476 sites / 5 ans) ;
3. **Décider** de façon traçable et explicable (Centre de Décision) ;
4. **Piloter** le déploiement et le suivi opérationnel (vagues 40, 300, national).

Le programme national **20 476 sites** constitue le cadre stratégique.  
Les programmes **40 sites** (pilote) et **300 sites** (première vague) sont des **vagues opérationnelles** de ce programme national, non des référentiels concurrents.

---

## 2. Différence entre les briques de la plateforme

| Brique | Rôle | Ce qu’elle n’est pas |
|---|---|---|
| **SIG / Cartographie** | Visualiser et interroger le territoire (couches, géométries, navigation) | Pas la source de vérité métier |
| **Référentiel National des Actifs** | Source officielle de vérité des entités métier (`business_id`, versions, validation) | Pas un moteur de scoring |
| **Moteur de priorisation** | Scorer et classer les sites / territoires selon des critères calibrés | Pas un registre d’actifs |
| **Centre de Décision** | Orchestrer intents, KPI explicables, priorités, simulations, rapports | Pas un simple dashboard cartographique |

**Règle d’architecture :**  
Toute entité métier durable doit être représentée dans le Référentiel National.  
Le SIG affiche ; le moteur priorise ; le Centre de Décision décide ; le Référentiel conserve.

---

## 2.1 Architecture par capacités métier

Le modèle d’entreprise s’organise également par **Business Capabilities** : aptitudes métier stables du FDSU, indépendantes des écrans et de la technique.

Référence complète : [`FDSU_BUSINESS_CAPABILITIES.md`](./FDSU_BUSINESS_CAPABILITIES.md).

Cartographie v1 :

| ID | Capacité |
|---|---|
| Capability 01 | Gestion des Sites FDSU |
| Capability 02 | Gestion des CCN |
| Capability 03 | Gestion des Missions |
| Capability 04 | Gestion des Programmes |
| Capability 05 | Gestion des Partenaires |
| Capability 06 | Gestion des Subventions |
| Capability 07 | Gestion des Infrastructures Télécom |
| Capability 08 | Gestion des Référentiels |
| Capability 09 | Centre de Décision |
| Capability 10 | Salle de Pilotage DG |

**Lien avec le Référentiel National :** chaque capacité consomme et/ou produit des actifs gouvernés (`business_id`, versions, validation).  
**Lien avec le Centre de Décision :** Capability 09 orchestre les décisions ; les autres capacités y exposent des points d’extension (priorisation, simulation, suivi).

Règle : tout développement structurant Phase 2+ doit être rattaché à au moins une capacité métier.

---

## 3. Notion d’Actif FDSU

Un **Actif FDSU** est toute entité métier gérée par la plateforme qui :

- possède un `uuid` technique et un `business_id` métier ;
- appartient à un type d’actif (`AssetType`) ;
- suit un cycle de vie (`AssetStatus`) ;
- est tracée (source, confiance, validation, versions).

### Distinction critique : Site FDSU ≠ CCN

| | **Site FDSU** | **CCN** |
|---|---|---|
| Rôle | Apporte la **connectivité** (infrastructure télécom / couverture) | Apporte le **service numérique** à la population |
| Nature | Actif d’infrastructure réseau | Actif de service communautaire |
| Codification | Nomenclature officielle sites | Schéma préparatoire distinct (non officiel) |
| Confusion | **Interdite** | **Interdite** |

Un Site FDSU peut **alimenter** un CCN (connectivité).  
Un CCN peut être **implanté** dans une école, un bâtiment administratif, un centre de santé, un marché ou un autre lieu.  
Ce sont deux actifs distincts, même s’ils sont liés.

---

## 4. Entités métier principales

### 4.1 Pilotage & programmes

| Entité | Description |
|---|---|
| **Programme FDSU** | Cadre stratégique (ex. Sites 20 476, CCN national) |
| **Vague / Batch** | Découpage opérationnel d’un programme (pilote 40, vague 300, vagues futures) |
| **Projet** | Unité de mise en œuvre (marché, lot, contrat) rattachée à une vague ou un programme |
| **Partenaire** | Opérateur, bailleur, institution, prestataire contribuant à un programme / projet / site / CCN |
| **Source de données** | Origine documentaire ou système (Excel officiel, import, API, mission terrain) |

### 4.2 Territoire administratif

| Entité | Description |
|---|---|
| **Province** | Niveau provincial RDC, codifié FDSU |
| **Territoire** | Territoire / ville, codifié FDSU |
| **Collectivité** | Collectivité territoriale |
| **Groupement** | Groupement / secteur / chefferie selon le référentiel |
| **Localité** | Localité de rattachement d’un site ou d’un service |
| **Village** | Village / hameau (niveau fin) |

Hiérarchie de référence :

```text
Zone FDSU → Province → Territoire → Collectivité → Groupement → Localité / Village
```

### 4.3 Actifs d’infrastructure & de service

| Entité | Description |
|---|---|
| **Site FDSU** | Site du programme (connectivité) — `business_id` = code FDSU officiel |
| **CCN** | Centre Communautaire Numérique — actif de service distinct |
| **Infrastructure télécom** | Tour, BTS, backhaul, etc. |
| **Fibre** | Tronçon / réseau fibre |
| **Route** | Axe routier pertinent pour l’accessibilité |
| **École** | Établissement scolaire (lieu potentiel d’implantation CCN) |
| **Centre de santé** | Structure sanitaire |
| **Marché** | Marché / pôle économique local |

### 4.4 Décision & opération

| Entité | Description |
|---|---|
| **Score** | Résultat d’évaluation multicritère d’un actif / territoire |
| **Recommandation** | Proposition issue d’un score (prioriser, reporter, investiguer…) |
| **Décision** | Acte de gouvernance tracé (approbation, arbitrage, exécution) |
| **Mission** | Mission terrain de vérification / enrichissement |

---

## 5. Relations métier

```text
Programme
  └── contient → Vague / Batch
                    └── cible → Site FDSU / CCN / Projet

Site FDSU
  ├── appartient à → Localité
  │                    └── Groupement → Collectivité → Territoire → Province
  ├── peut alimenter → CCN
  ├── est évalué par → Score
  │                      └── produit → Recommandation
  │                                      └── alimente → Décision
  └── est vérifié / enrichi par → Mission

CCN
  ├── implanté dans → École | Bâtiment administratif | Centre de santé | Marché | Autre lieu
  ├── alimenté par → Site FDSU (connectivité)
  └── concerné par → Décision / Mission / Projet

Décision
  └── concerne → Programme | Site | CCN | Territoire | Province | Vague

Source de données
  └── alimente → Entité (toute entité du référentiel)

Partenaire
  └── contribue à → Programme | Projet | Site | CCN
```

### Matrice relationnelle (types)

| Relation | De | Vers | Cardinalité typique |
|---|---|---|---|
| `CONTAINS` | Programme | Vague | 1 → N |
| `TARGETS` | Vague | Site / CCN | 1 → N |
| `LOCATED_IN` | Site | Localité | N → 1 |
| `ADMIN_PARENT` | Localité… | Groupement…Province | N → 1 |
| `FEEDS_CONNECTIVITY` | Site FDSU | CCN | N → N |
| `HOSTED_IN` | CCN | École / Santé / Marché / … | N → 1 |
| `SCORED_BY` | Site / Territoire | Score | 1 → N |
| `PRODUCES` | Score | Recommandation | 1 → N |
| `FEEDS` | Recommandation | Décision | N → 1 |
| `CONCERNS` | Décision | Programme / Site / CCN / Territoire / Province | N → N |
| `VERIFIES` | Mission | Site / CCN / Localité | N → N |
| `SOURCED_FROM` | Entité | Source de données | N → 1..N |
| `CONTRIBUTES_TO` | Partenaire | Programme / Projet / Site / CCN | N → N |

---

## 6. Cycles de vie

### 6.1 Cycle de vie d’un actif

```text
proposé → pré-identifié → géocodé → validé → planifié
  → en déploiement → opérationnel → en maintenance
  → suspendu → archivé
```

| Statut | Signification |
|---|---|
| `proposed` | Idée / candidature non encore cadrée |
| `pre_identified` | Identifié dans une source, non encore consolidé |
| `geocoded` | Coordonnées contrôlées / géocodage intelligent |
| `validated` | Validé métier / référentiel |
| `planned` | Inscrit dans une vague / planning |
| `deploying` | Travaux / mise en service en cours |
| `operational` | En service |
| `maintenance` | Maintenance corrective / évolutive |
| `suspended` | Temporairement hors service |
| `archived` | Sorti du périmètre actif (conservé pour historique) |

### 6.2 Cycle de vie d’une donnée

```text
brute → normalisée → enrichie → validée → obsolète → archivée
```

| Statut | Signification |
|---|---|
| `raw` | Import brut, non transformé |
| `normalized` | Aligné sur nomenclatures / schémas |
| `enriched` | Complété (géocodage, relations, attributs) |
| `validated` | Accepté comme référence |
| `obsolete` | Remplacé / périmé |
| `archived` | Conservé hors usage courant |

### 6.3 Cycle de vie d’un programme

```text
conçu → approuvé → en exécution (vagues) → suivi → clôturé
```

Les vagues (40, 300, futures) héritent du programme national et portent leur propre avancement.

### 6.4 Cycle de vie d’une décision

```text
brouillon → proposée → validée → approuvée → exécutée → clôturée
```

| Statut | Signification |
|---|---|
| `draft` | Travail en cours, non soumis |
| `proposed` | Soumise à revue |
| `validated` | Validée techniquement / métier |
| `approved` | Approuvée par l’autorité compétente |
| `executed` | Mise en œuvre engagée |
| `closed` | Clôturée avec bilan |

---

## 7. Gouvernance des données

Principes :

1. **Une source de vérité** : le Référentiel National des Actifs.
2. **Nomenclature officielle sites** : `data/raw/FDSU Structure code Territoire zones.xlsx`.
3. **Pas d’identifiant artificiel de site** (`SITE-FDSU-000001` interdit).
4. **Traçabilité obligatoire** : source, dates, confiance, validation, versions.
5. **Pas d’écrasement silencieux** : les anomalies restent visibles.
6. **Séparation Site / CCN** : deux actifs, deux codes, deux cycles éventuels.

### Métadonnées minimales par entité

- `uuid`
- `business_id`
- `entity_type` / `asset_type`
- `status` (actif)
- `data_status` (donnée)
- `validation_status`
- `confidence_level`
- `source`
- `version`
- `created_at` / `updated_at`

---

## 8. Règles de traçabilité

| Événement | Trace attendue |
|---|---|
| Import | Source, date, opérateur/système, rapport d’anomalies |
| Géocodage | Ancien / nouveau couple lat-lon, statut, confiance |
| Scoring | Version des poids, critères, score, niveau |
| Recommandation | Lien score → texte / action proposée |
| Décision | Auteur, statut, objets concernés, horodatage |
| Fusion d’entités | Alias, lien `merged_into`, historique versions |
| Mission | Périmètre, constats, pièces jointes |

Aucune décision stratégique ne doit être prise sur une donnée sans `source` ni `confidence_level`.

---

## 9. Business Code Registry

### 9.1 Sites FDSU (officiel)

Source unique :

```text
data/raw/FDSU Structure code Territoire zones.xlsx
```

Format :

```text
FDSU_<ZONE>_<PROVINCE>_<TERRITOIRE>_<SITE>
```

Exemple : `FDSU_ND_18_003_10100`

### 9.2 CCN (proposition technique préparatoire — non officielle)

Les CCN sont des **actifs distincts**.  
Schéma **proposé** pour préparation technique :

```text
FDSU_CCN_[ZONE]_[PROVINCE]_[TERRITOIRE]_[NUMERO]
```

Exemple illustratif : `FDSU_CCN_ND_18_003_00001`

> **Important :** ce schéma CCN est une **proposition technique préparatoire**,  
> **pas encore une nomenclature officielle validée**.  
> Il ne doit pas être présenté comme code officiel FDSU tant qu’une validation métier n’a pas été émise.

### 9.3 Autres entités

Préfixes génériques du Référentiel National :  
`PROGRAM-######`, `MISSION-######`, `HEALTH-######`, `TELCO-######`, `CCN-######` (si non encore basculé sur le schéma FDSU_CCN_*), etc.

---

## 10. Évolution future

| Horizon | Contenu |
|---|---|
| **CCN** | Voir [`FDSU_CCN_BUSINESS_MODEL.md`](./FDSU_CCN_BUSINESS_MODEL.md) — Capability 1 (fondations Phase 2) |
| **PostGIS `master.*`** | Persistance complète du Référentiel National (déjà préparé en schéma exemple) |
| **Salle de Pilotage DG** | Vue exécutive nationale : programmes, vagues, décisions, alertes, KPI DG |
| **Intégration progressive** | Sites, Géocodage, Priorisation, Télécom, Santé, Cartographie, Missions, Programmes, Décision → tous via le Référentiel |

---

## 11. Artefact technique associé

Constantes et dataclasses légères (sans ORM) :

```text
api/models/business_entities.py
```

Le Référentiel National (`FDSU_MASTER_DATA_MODEL.md`) **applique** ce modèle métier EBM.  
Aucun module ne doit créer une nomenclature ou un cycle de vie parallèle.
