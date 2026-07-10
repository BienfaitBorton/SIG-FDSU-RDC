# SIG-FDSU RDC — Business Capabilities

**Statut :** Document d’architecture métier  
**Date :** 10 juillet 2026  
**Périmètre :** Cartographie des capacités métier (Business Capabilities)  
**Règle :** Documentation uniquement — aucune logique applicative modifiée

**Documents liés :**
- [`FDSU_ENTERPRISE_BUSINESS_MODEL.md`](./FDSU_ENTERPRISE_BUSINESS_MODEL.md)
- [`FDSU_MASTER_DATA_MODEL.md`](./FDSU_MASTER_DATA_MODEL.md)
- [`FDSU_CCN_BUSINESS_MODEL.md`](./FDSU_CCN_BUSINESS_MODEL.md)
- [`SIG_FDSU_RDC_V1_FUNCTIONAL_ARCHITECTURE.md`](./SIG_FDSU_RDC_V1_FUNCTIONAL_ARCHITECTURE.md)

---

## 1. Qu’est-ce qu’une Business Capability ?

Une **Business Capability** (capacité métier) est une aptitude stable de l’organisation FDSU à produire un résultat métier identifiable.

Elle répond à la question :

> **Que doit pouvoir faire** le FDSU / la plateforme, indépendamment des écrans, des technologies ou des sprints en cours ?

Caractéristiques :

| Propriété | Description |
|---|---|
| **Métier d’abord** | Décrite en langage FDSU, pas en termes techniques |
| **Stable** | Survit aux refontes UI / API / base de données |
| **Composable** | Peut s’appuyer sur d’autres capacités |
| **Gouvernée** | Possède un périmètre, des actifs, des décisions associées |
| **Traçable** | S’appuie sur le Référentiel National pour ses entités |

Une capacité **n’est pas** :

- un module UI ;
- un endpoint API ;
- une table PostGIS ;
- un sprint de développement.

Ces éléments **réalisent** une capacité ; ils ne la définissent pas.

---

## 2. Rôle dans l’architecture SIG-FDSU RDC

L’architecture de la plateforme s’organise désormais en trois niveaux complémentaires :

```text
Business Capabilities          ← quoi le FDSU doit pouvoir faire
        │
        ▼
Enterprise Business Model      ← entités, relations, cycles de vie
        │
        ▼
Référentiel / SIG / APIs / UI  ← comment c’est réalisé techniquement
```

### Pourquoi des capacités ?

1. **Aligner** les développements Phase 2+ sur les besoins métier FDSU ;
2. **Éviter** les modules techniques orphelins sans finalité métier ;
3. **Prioriser** les sprints par valeur (CCN, Missions, Subventions…) ;
4. **Relier** clairement actifs, décisions et pilotage DG ;
5. **Préparer** la Salle de Pilotage DG comme capacité, pas comme simple écran.

### Règle d’architecture

> Tout développement structurant doit être rattaché à au moins une Business Capability.  
> Aucune capacité ne contourne le Référentiel National des Actifs.

---

## 3. Lien avec le Référentiel National

Le **Référentiel National des Actifs FDSU** est la source de vérité des entités.

| Capacité | Consomme / produit dans le référentiel |
|---|---|
| Sites FDSU | Actifs `SITE` (codes officiels) |
| CCN | Actifs `CCN` (distincts des sites) |
| Missions | Actifs `MISSION` + liens de vérification |
| Programmes | Actifs `PROGRAM` / `BATCH` / `PROJECT` |
| Partenaires | Actifs `PARTNER` |
| Subventions | Financements liés programmes / projets / CCN (futur) |
| Infrastructures télécom | Actifs `TELCO` / `FIBER` |
| Référentiels | Gouvernance des sources et nomenclatures |
| Centre de Décision | Scores, recommandations, décisions |
| Salle de Pilotage DG | Synthèses nationales sur les actifs & décisions |

Le référentiel **ne remplace pas** les capacités : il les **alimente** et les **contraint** (nomenclature, traçabilité, non-duplication).

---

## 4. Lien avec le Centre de Décision

Le **Centre de Décision** est lui-même une Business Capability (Capability 09).

Il orchestre :

- les intents décisionnels ;
- les KPI explicables ;
- la priorisation ;
- les simulations ;
- le suivi opérationnel.

Les autres capacités **exposent** des points d’extension au Centre de Décision (ex. priorisation CCN, suivi missions, alertes programmes), sans fusionner leurs modèles.

```text
Capability métier  ──produit──►  faits / scores / alertes
        │
        ▼
Centre de Décision ──orchestre──►  recommandations / décisions
        │
        ▼
Référentiel National ──conserve──►  actifs & historique
```

---

## 5. Cartographie des capacités métier (v1)

| ID | Capacité | Maturité actuelle | Notes |
|---|---|---|---|
| **Capability 01** | Gestion des Sites FDSU | Avancée | Nomenclature officielle, programme 20 476, priorisation nationale |
| **Capability 02** | Gestion des CCN | Fondations | Modèle métier + extensions CD ; pas de CRUD opérationnel |
| **Capability 03** | Gestion des Missions | Partielle | CRUD / API existants ; à aligner EBM |
| **Capability 04** | Gestion des Programmes | Partielle | Programmes 40 / 300 / 20 476 ; vagues formalisées |
| **Capability 05** | Gestion des Partenaires | À construire | Entité EBM prévue |
| **Capability 06** | Gestion des Subventions | À construire | Capacité financière FDSU |
| **Capability 07** | Gestion des Infrastructures Télécom | Partielle | Référentiel télécom / fibre existant |
| **Capability 08** | Gestion des Référentiels | Avancée | Référentiel National + nomenclatures + NRF sectoriel |
| **Capability 09** | Centre de Décision | Avancée | Intents, priorisation, KPI, extensions CCN préparées |
| **Capability 10** | Salle de Pilotage DG | Cible | Vue exécutive nationale — non implémentée |

### Capability 01 — Gestion des Sites FDSU

Gérer le cycle de vie des sites du programme national (identification, géocodage, validation, priorisation, déploiement).  
`business_id` = code FDSU officiel (`data/raw/FDSU Structure code Territoire zones.xlsx`).

### Capability 02 — Gestion des CCN

Gérer les Centres Communautaires Numériques comme actifs de **service numérique**, distincts des sites.  
Voir [`FDSU_CCN_BUSINESS_MODEL.md`](./FDSU_CCN_BUSINESS_MODEL.md).

### Capability 03 — Gestion des Missions

Planifier, exécuter et tracer les missions terrain (vérification, enrichissement, audit d’actifs).

### Capability 04 — Gestion des Programmes

Piloter programmes et vagues (40, 300, 20 476, futures) : périmètre, avancement, rattachement d’actifs.

### Capability 05 — Gestion des Partenaires

Référencer et suivre les partenaires (opérateurs, bailleurs, collectivités, prestataires) et leurs contributions.

### Capability 06 — Gestion des Subventions

Gérer les mécanismes de financement / subvention liés aux programmes, projets, sites et CCN.

### Capability 07 — Gestion des Infrastructures Télécom

Connaître et relier les infrastructures (sites radio, fibre, backhaul) au territoire et aux actifs FDSU.

### Capability 08 — Gestion des Référentiels

Gouverner nomenclatures, sources, qualité, versions et le Référentiel National des Actifs.

### Capability 09 — Centre de Décision

Décider de façon explicable : prioriser, simuler, suivre, recommander, tracer les décisions.

### Capability 10 — Salle de Pilotage DG

Fournir à la Direction Générale une vue nationale consolidée (programmes, alertes, décisions, impacts).

---

## 6. Principes de gouvernance des capacités

1. Une capacité a un **responsable métier** (à désigner) et un **périmètre d’actifs**.
2. Les évolutions de capacité passent par l’EBM puis le Référentiel.
3. Les capacités Phase 2 se livrent par **fondations → opérationnel → pilotage**.
4. Capability 02 (CCN) est la première capacité Phase 2 formalisée après les fondations plateforme.
5. Capability 10 (Salle de Pilotage DG) consomme les sorties des capacités 01–09 ; elle ne les remplace pas.

---

## 7. Prochaines étapes documentaires

- Fiches détaillées Capability 03 à 07 (sur le modèle CCN) ;
- Matrice capacité ↔ endpoints / modules UI ;
- Roadmap Phase 2 ordonnée par capacité.
