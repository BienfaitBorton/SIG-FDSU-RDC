# SIG-FDSU RDC — FDSU Knowledge Hub & National Indicators Framework

**Statut :** Fondations architecturales (Phase 2)  
**Date :** 10 juillet 2026  
**Périmètre :** Couche de connaissance métier — pas de moteur de recommandation  
**Documents liés :**
- [`FDSU_ENTERPRISE_BUSINESS_MODEL.md`](./FDSU_ENTERPRISE_BUSINESS_MODEL.md)
- [`FDSU_BUSINESS_CAPABILITIES.md`](./FDSU_BUSINESS_CAPABILITIES.md)
- [`FDSU_MASTER_DATA_MODEL.md`](./FDSU_MASTER_DATA_MODEL.md)
- [`FDSU_CCN_BUSINESS_MODEL.md`](./FDSU_CCN_BUSINESS_MODEL.md)

---

## 1. Rôle

Le **FDSU Knowledge Hub** est la source consolidée de la **connaissance métier** de la plateforme.

Il répond à la question :

> **Que sait-on** de ce territoire ou de cet actif ?

Il **organise, structure et expose** la connaissance.  
Il **ne calcule pas** encore les recommandations (rôle du moteur décisionnel / Territorial Intelligence Engine).

### Distinction des briques

| Brique | Question | Rôle |
|---|---|---|
| **Référentiel National** | *Qu’est-ce que cet actif ?* | Identité, `business_id`, cycle de vie, versions |
| **Knowledge Hub** | *Que sait-on de cet actif / territoire ?* | Domaines de connaissance, indicateurs, sources |
| **Moteur décisionnel / Centre de Décision** | *Que faut-il faire ?* | Scores, recommandations, décisions |
| **SIG / Cartographie** | *Où est-ce ?* | Visualisation spatiale |

---

## 2. Responsabilités

1. Cataloguer les **domaines de connaissance** FDSU ;
2. Maintenir le **National Indicators Framework** (catalogue d’indicateurs) ;
3. Exposer la connaissance via API (`/api/knowledge/*`) ;
4. Relier chaque domaine / indicateur à ses **sources** et **niveaux territoriaux** ;
5. Préparer l’alimentation du Territorial Intelligence Engine (sprint ultérieur) ;
6. Ne jamais inventer de valeurs chiffrées non sourcées.

Hors périmètre actuel :

- calcul automatique de recommandations ;
- moteur d’intelligence territoriale ;
- écrans complets Knowledge Hub ;
- remplacement du Centre de connaissances CNCT (`/knowledge`).

> Note : le routeur historique `/knowledge` (CNCT / fiches enrichies) reste distinct.  
> Le Knowledge Hub national utilise le préfixe `/api/knowledge`.

---

## 3. Domaines de connaissance

| ID | Domaine | Contenu principal |
|---|---|---|
| `territory` | Territoire | Hiérarchie administrative, population, accessibilité |
| `connectivity` | Connectivité | Opérateurs, couverture, fibre, backbone, qualité réseau |
| `public_services` | Services publics | Santé, éducation, administration, marchés |
| `socio_economic` | Développement socio-économique | Agriculture, pêche, élevage, mines, commerce, tourisme, PME |
| `fdsu_programs` | Programmes FDSU | Sites, CCN, subventions, projets, vagues |
| `national_indicators` | Indicateurs nationaux | Catalogue NIF (connectivité, inclusion, santé, etc.) |
| `decision` | Décision | Règles, matrices, scénarios, simulations, recommandations (structure) |
| `business_doctrine` | Doctrine Métier FDSU | Doctrines versionnées (CCN active ; Sites, Subventions, Partenaires, Gouvernance, Télécom prévues) |

Première doctrine active : **Doctrine CCN FDSU v1** (`data/business/doctrines/ccn_doctrine_v1.json`), exposée via `/api/ccn/doctrine` et le catalogue Knowledge Hub (`GET /api/knowledge/domain/business_doctrine`).

Chaque domaine possède :

- un identifiant stable ;
- une description ;
- des sous-thèmes ;
- des sources de données connues / à brancher ;
- des points de connexion vers les modules plateforme.

---

## 4. National Indicators Framework (NIF)

Le NIF est le **catalogue officiel des indicateurs** utilisables par le FDSU.

Pour chaque indicateur :

| Champ | Description |
|---|---|
| `id` | Identifiant stable (`IND_*`) |
| `name` | Nom métier |
| `definition` | Définition |
| `source` | Source documentaire / système (ou `à renseigner`) |
| `update_frequency` | Fréquence cible |
| `territorial_level` | national / province / territoire / localité / site |
| `unit` | Unité |
| `calculation_mode` | Mode de calcul si connu, sinon `pending` |
| `decision_usage` | Usage dans la décision FDSU |
| `value_status` | `structure_only` — aucune valeur inventée |

Les valeurs numériques ne sont **pas** stockées dans ce sprint : seule la structure d’accueil est créée.

Familles d’indicateurs :

- connectivité ;
- inclusion numérique ;
- santé ;
- éducation ;
- économie ;
- accessibilité ;
- énergie ;
- priorité FDSU.

Catalogue versionné : `data/knowledge/national_indicators.json`

---

## 5. Gouvernance

1. Toute connaissance exposée doit citer une **source** ou être marquée `pending_source` ;
2. Le Knowledge Hub ne remplace pas le Référentiel National ;
3. Les indicateurs utilisés en décision doivent être référencés dans le NIF ;
4. Les évolutions du catalogue sont versionnées (`schema_version`) ;
5. Aucune recommandation automatique n’est produite par le Hub.

---

## 6. Intégration avec les autres composants

| Composant | Connexion Knowledge Hub |
|---|---|
| Référentiel National | Identité des actifs ; le Hub enrichit la connaissance associée |
| Priorisation | Consomme les indicateurs / critères documentés (NIF + matrices) |
| CCN | Domaine programmes + indicateurs d’inclusion / service |
| Géocodage | Qualité de localisation → connaissance territoriale |
| Télécommunications | Domaine connectivité |
| Santé | Domaine services publics |
| Cartographie | Visualisation des couches liées aux domaines |
| Centre de Décision | Lit la connaissance ; ne la calcule pas ici |
| Territorial Intelligence Engine | Sprint suivant — consommera le Hub |

Points d’extension techniques : `api/services/knowledge_hub_service.py` → `integration_points()`.

---

## 7. API

Préfixe : `/api/knowledge`

- `GET /domains`
- `GET /domain/{id}`
- `GET /indicators`
- `GET /indicator/{id}`

---

## 8. Sprint suivant (proposé)

1. Brancher les premières valeurs d’indicateurs **sourcées** (sans invention) ;
2. Profil de connaissance par territoire / actif (`/api/knowledge/profile/...`) ;
3. Amorcer le **Territorial Intelligence Engine** sur le Hub ;
4. UI Centre de Décision : panneau « Que sait-on ? » ;
5. Alignement CNCT (`/knowledge`) ↔ Knowledge Hub (`/api/knowledge`).
