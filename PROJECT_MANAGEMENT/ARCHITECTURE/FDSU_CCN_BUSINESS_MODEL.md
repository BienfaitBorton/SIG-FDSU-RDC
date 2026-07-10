# SIG-FDSU RDC — Modèle métier CCN (Centres Communautaires Numériques)

**Capacité :** Capability 02 — Gestion des CCN  
**Phase :** 2  
**Statut :** Module opérationnel v1 (démonstration DG) — doctrine versionnée + API lecture + UI  
**Date :** 10 juillet 2026  

**Documents liés :**
- [`FDSU_ENTERPRISE_BUSINESS_MODEL.md`](./FDSU_ENTERPRISE_BUSINESS_MODEL.md)
- [`FDSU_MASTER_DATA_MODEL.md`](./FDSU_MASTER_DATA_MODEL.md)
- [`FDSU_KNOWLEDGE_HUB.md`](./FDSU_KNOWLEDGE_HUB.md)
- Artefact : `api/models/business_entities.py`
- Socle capacité : `api/services/ccn_capability_service.py`
- Opérationnel : `api/services/ccn_operational_service.py`
- Doctrine : `data/business/doctrines/ccn_doctrine_v1.json`
- UI : `dashboard/modules/ccn/`

---

## 1. Vision métier

Un **Centre Communautaire Numérique (CCN)** est un **actif de service numérique** du FDSU.

Il offre à la population un accès local aux services numériques (formation, e-services, information, inclusion numérique), dans un lieu d’implantation identifié.

### Distinction fondamentale

| | **Site FDSU** | **CCN** |
|---|---|---|
| Nature | Actif d’**infrastructure / connectivité** | Actif de **service numérique** |
| Apporte | Couverture, capacité réseau, lien télécom | Accès population, usages, impacts sociaux |
| Codification | Nomenclature officielle sites | Schéma préparatoire (non officiel) |
| Confusion | **Interdite** | **Interdite** |

> Le Site FDSU **alimente** le CCN en connectivité.  
> Le CCN **sert** la population.  
> Ce sont deux actifs distincts du Référentiel National.

---

## 2. Rôle dans la stratégie FDSU

Dans la stratégie FDSU 2026–2030, les CCN traduisent la connectivité en **valeur sociale et économique** :

1. **Inclusion numérique** des territoires mal desservis ;
2. **Ancrage local** des services (école, santé, administration, marché) ;
3. **Mesure d’impact** (fréquentation, services rendus, satisfaction) ;
4. **Pilotage décisionnel** (où implanter, quoi prioriser, quoi auditer).

Le programme national des sites (20 476) fournit le socle de connectivité.  
Les CCN constituent la couche **service** qui s’appuie sur ce socle — sans le remplacer.

---

## 3. Domaines d’attributs du modèle CCN

### 3.1 Identification

- `business_id` (futur code CCN ou préfixe générique `CCN-######` tant que non officialisé)
- `uuid` technique
- `name` / libellé
- `asset_type` = `CCN`
- `status` (cycle de vie actif)
- `program_ref` / `batch_ref`
- `source`, `confidence_level`, `validation_status`, `version`

### 3.2 Implantation

- Localité / village / territoire / province / zone FDSU
- Type de lieu d’accueil (`CcnHostType`) : école, bâtiment administratif, centre de santé, marché, autre
- Adresse / description du lieu
- Coordonnées (après géocodage contrôlé)
- Capacité d’accueil (places, salles)

### 3.3 Connectivité

- Site(s) FDSU alimentant le CCN (`FEEDS_CONNECTIVITY`)
- Mode d’accès (fibre, radio, satellite, autre)
- Qualité de service attendue / mesurée
- Redondance éventuelle

### 3.4 Équipements

- Postes utilisateurs, serveurs, réseau local
- Énergie (réseau, solaire, hybride)
- Impression / numérisation
- Accessibilité PMR (si renseigné)

### 3.5 Services

Catalogue de services (`CcnServiceType`) :

- accès Internet public
- formation numérique
- e-administration / accompagnement
- e-santé / information santé
- e-éducation
- services aux entrepreneurs / marché
- autres services locaux

### 3.6 Exploitation

- Opérateur / gestionnaire local
- Horaires d’ouverture
- Modèle d’exploitation (public, partenarial, communautaire)
- Effectifs / animateurs

### 3.7 Maintenance

- Contrat de maintenance
- Incidents / tickets (futur)
- Dernière visite technique
- Statut maintenance (`maintenance` / `operational` / `suspended`)

### 3.8 Indicateurs (KPI)

- Fréquentation (visites / mois)
- Nombre de services rendus
- Taux d’ouverture
- Disponibilité connectivité
- Satisfaction (si enquête)
- Population desservie estimée

### 3.9 Impacts

- Inclusion numérique (qualitatif / quantitatif)
- Emploi / formation
- Accès aux services publics
- Dynamique économique locale

### 3.10 Partenaires

- Bailleur / financeur
- Opérateur télécom
- Collectivité / école / structure hôte
- ONG / partenaire technique

---

## 4. Relations métier

```text
Programme FDSU ──finance──► CCN
Site FDSU ──FEEDS_CONNECTIVITY──► CCN
CCN ──HOSTED_IN──► École | Bât. admin | Santé | Marché | Autre
CCN ──SERVES_POPULATION──► Localité / population cible
CCN ──OFFERS──► Service(s) CCN
CCN ──TRACKED_BY──► Indicateur(s)
CCN ──VERIFIES (Mission)──► audit / enrichissement terrain
CCN ──SCORED_BY──► Score ──► Recommandation ──► Décision
```

| Relation | Sens | Description |
|---|---|---|
| `FEEDS_CONNECTIVITY` | Site → CCN | Le site apporte la connectivité |
| `HOSTED_IN` | CCN → lieu | Implantation physique |
| `SERVES_POPULATION` | CCN → population/localité | Bassin de desserte |
| `OFFERS` | CCN → service | Catalogue de services |
| `TRACKED_BY` | CCN → indicateur | Suivi de performance |
| `CONTRIBUTES_TO` / financement | Programme/Partenaire → CCN | Cadre financier |
| `VERIFIES` | Mission → CCN | Audit / contrôle terrain |
| `CONCERNS` | Décision → CCN | Arbitrage d’implantation ou d’exploitation |

---

## 5. Cycle de vie CCN

Aligné sur `AssetStatus` de l’EBM :

```text
proposé → pré-identifié → géocodé → validé → planifié
  → en déploiement → opérationnel → en maintenance
  → suspendu → archivé
```

Spécificités CCN :

- **pré-identifié** : lieu hôte pressenti, population cible estimée ;
- **géocodé** : implantation contrôlée (module Géocodage) ;
- **planifié** : inscrit dans une vague / budget ;
- **opérationnel** : services ouverts à la population ;
- **maintenance** : équipement ou connectivité dégradée.

---

## 6. Gouvernance

1. Le CCN est une entité du **Référentiel National** (`AssetType.CCN`).
2. Il ne réutilise **jamais** le `business_id` d’un Site FDSU.
3. Tant que la nomenclature CCN n’est pas officialisée :
   - usage possible de `CCN-######` (générique master) ;
   - le schéma `FDSU_CCN_*` est **préparé** mais `is_official=False`.
4. Toute donnée CCN conserve source, confiance, validation, versions.
5. Les décisions d’implantation passent par le Centre de Décision (futur).

---

## 7. Nomenclature (préparatoire)

Schéma proposé :

```text
FDSU_CCN_[ZONE]_[PROVINCE]_[TERRITOIRE]_[NUMERO]
```

Exemple : `FDSU_CCN_ND_18_003_00001`

| État | Règle |
|---|---|
| Aujourd’hui | `CCN_CODE_SCHEME.is_official = False` |
| Moteur | Parser / validateur / générateur **prêts** (`ccn_capability_service`) |
| Activation | Uniquement après validation métier officielle |

La nomenclature sites reste exclusive :

```text
data/raw/FDSU Structure code Territoire zones.xlsx
```

---

## 8. Indicateurs de performance (cible)

| Domaine | Exemples |
|---|---|
| Accès | Population desservie, distance moyenne |
| Usage | Visites, sessions, services rendus |
| Qualité | Disponibilité, incidents, temps de rétablissement |
| Inclusion | Formations, publics vulnérables |
| Gouvernance | Missions réalisées, décisions exécutées |

Ces indicateurs alimenteront le Centre de Décision et, plus tard, la Salle de Pilotage DG.

---

## 9. Scénarios décisionnels futurs

1. **Priorisation des CCN** — où ouvrir en premier (population, déficit numérique, présence site FDSU).
2. **Simulation d’implantation** — comparer lieux hôtes (école vs marché vs santé).
3. **Suivi des performances** — alerter sur CCN sous-utilisés ou en panne de connectivité.
4. **Couplage Site↔CCN** — détecter sites sans CCN à fort potentiel, ou CCN sans connectivité stable.

Points d’extension Centre de Décision (préparés, non branchés UI complète) :

- `ccn.prioritization`
- `ccn.implantation_simulation`
- `ccn.performance_monitoring`

---

## 10. Hors périmètre de ce sprint

- CRUD opérationnel CCN
- Tables PostGIS définitives dédiées
- Écran complet Centre de Décision
- Activation officielle de `FDSU_CCN_*`

## 11. Prochaines étapes (module opérationnel)

1. Valider la nomenclature CCN côté métier ;
2. Persister les CCN dans `master.entities` (type `CCN`) ;
3. Lier Site↔CCN et CCN↔lieu hôte ;
4. Brancher priorisation / simulation / KPI dans le Centre de Décision ;
5. Intégrer missions d’audit CCN.
