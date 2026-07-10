# Référentiel National des Actifs FDSU — Master Data Model

## 1. Objet

Le **Référentiel National des Actifs FDSU** est la source officielle de vérité de la plateforme SIG-FDSU RDC.

Il **applique** le modèle métier d’entreprise défini dans
[`FDSU_ENTERPRISE_BUSINESS_MODEL.md`](./FDSU_ENTERPRISE_BUSINESS_MODEL.md)
(entités, relations, cycles de vie, gouvernance, Business Code Registry).

Aucun module futur (Sites, Géocodage, Priorisation, Télécom, Santé, Cartographie, Missions, Programmes, Décision) ne doit contourner ce référentiel.

## 2. Nomenclature officielle des sites

La nomenclature officielle FDSU est issue du fichier
`data/raw/FDSU Structure code Territoire zones.xlsx`
et constitue la référence unique pour la génération et la validation des codes FDSU.

### Source

- **Fichier officiel unique :** `data/raw/FDSU Structure code Territoire zones.xlsx`
- Feuilles : `ZONE ND`, `ZONE SD`, `ZONE CE`, `ZONE OT`, `ZONE ET`
- Colonnes : N° province, Province, Town/Territory, CODE, Nombre des sites GSM
- Dérivé applicatif : `data/reports/fdsu_nomenclature.json` (toujours aligné sur ce fichier)

### Format du code site (business_id)

```text
FDSU_<ZONE>_<CODE_PROVINCE>_<CODE_TERRITOIRE>_<CODE_SITE>
```

Exemple :

```text
FDSU_ND_18_003_10100
```

| Segment | Valeur | Signification |
|---|---|---|
| Préfixe | `FDSU` | Programme Service Universel |
| Zone | `ND` | Zone Nord |
| Province | `18` | MONGALA |
| Territoire | `003` | LISALA TERRITOIRE |
| Site | `10100` | Identifiant site dans le territoire |

Variante étendue acceptée (collectivité) :

```text
FDSU_<ZONE>_<PROV>_<TERR>_<COLLECTIVITE>_<SITE>
```

### Interdictions

- `SITE-FDSU-000001`
- toute codification artificielle de site
- UUID exposé comme identifiant métier

### Zones officielles

| Code | Libellé |
|---|---|
| ND | Zone Nord |
| SD | Zone Sud |
| CE | Zone Centre |
| OT | Zone Ouest |
| ET | Zone Est |

Alias historiques A/B/C/D/E → ND/SD/CE/OT/ET (compatibilité lecture seule).

## 3. Modèle métier extensible

Entités supportées :

Programme, Vague (Batch), Projet, Site, CCN, Zone, Province, Territoire, Collectivité, Groupement, Localité, Village, Infrastructure Télécom, Centre de Santé, École, Marché, Route, Fibre, Mission, Décision, Scoring.

Hiérarchie territoriale :

```text
Zone FDSU → Province → Territoire → Collectivité → Groupement → Localité/Village → Site
```

Programmes / vagues :

```text
Programme national (20 476)
  ├── Vague pilote (40)
  └── Première vague opérationnelle (300)
```

## 4. Identifiants

| Entité | business_id | uuid |
|---|---|---|
| Site | Code FDSU officiel | technique, invisible métier |
| Autres | `PROGRAM-000001`, `MISSION-000001`, `HEALTH-000001`, `TELCO-000001`, `CCN-000001`, … | technique |

Métadonnées obligatoires :

- `uuid`
- `business_id`
- `created_at`
- `updated_at`
- `status`
- `validation_status`
- `confidence_level`
- `source`
- `version`

## 5. Règles de génération

1. Zone ∈ {ND, SD, CE, OT, ET}
2. Province = code officiel 2 chiffres (nomenclature)
3. Territoire = code officiel 3 chiffres dans la province
4. Site = 3 à 5 chiffres, unique dans le périmètre territoire (+ collectivité si présente)
5. Jamais de préfixe `SITE-FDSU`

## 6. Règles de validation

1. Format regex officiel
2. Zone reconnue
3. Province présente dans la nomenclature
4. Territoire présent pour la province
5. Cohérence zone code ↔ zone province
6. Détection doublon `business_id`
7. Détection incohérence territoire réel (attendu vs code)

## 7. Schéma de données `master.*`

Tables :

- `master.entities`
- `master.entity_versions`
- `master.entity_aliases`
- `master.entity_sources`
- `master.entity_links`
- `master.validation_log`

Voir : `docs/master_registry_schema.sql.example`

Stockage applicatif v1 : `data/master/registry.json` (bootstrap nomenclature) + schéma PostGIS prêt.

## 8. Gouvernance des données

Chaque donnée conserve :

- source
- date d’import / création
- date de mise à jour
- niveau de confiance
- statut de validation
- historique des modifications (`versions`)

Cycle de vie :

```text
draft → active → archived
              ↘ merged
needs_review / validated / rejected
```

## 9. API

Préfixe : `/api/master`

- `GET /entities`
- `GET /entities/{id}`
- `POST /entities`
- `PUT /entities/{id}`
- `GET /search`
- `GET /statistics`
- `GET /fdsu-code/{business_id}`
- `POST /fdsu-code/validate`
- `POST /fdsu-code/generate`

## 10. Intégration progressive

Les modules Sites, Géocodage, Priorisation, Télécom, Santé, Cartographie, Missions, Programmes et Décision doivent progressivement résoudre leurs objets via `business_id` master, sans créer de nomenclatures parallèles. Tous s’appuient sur la même source officielle : `data/raw/FDSU Structure code Territoire zones.xlsx`.

## 11. Lien avec l’Enterprise Business Model

Le présent document décrit **comment** le Référentiel National stocke et gouverne les actifs.

Le document
[`FDSU_ENTERPRISE_BUSINESS_MODEL.md`](./FDSU_ENTERPRISE_BUSINESS_MODEL.md)
définit **quoi** sont les entités métier, leurs relations, cycles de vie et règles de gouvernance.

Artefact technique léger associé : `api/models/business_entities.py`.

Capability CCN (Phase 2) : [`FDSU_CCN_BUSINESS_MODEL.md`](./FDSU_CCN_BUSINESS_MODEL.md).
