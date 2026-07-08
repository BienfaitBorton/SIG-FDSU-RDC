# Référentiel Télécom National — SIG-FDSU RDC

Ce dossier contient les **supports d'import/export** du référentiel télécom national. En mode DB, la source officielle est PostgreSQL/PostGIS (`telecom.*`).

## Structure

| Dossier / fichier | Rôle |
| --- | --- |
| `raw/` | KMZ et KML sources officiels |
| `processed/` | GeoJSON dérivés lors de l'import (audit / export) |

## Sources KMZ intégrées

| Fichier | Opérateur | Contenu |
| --- | --- | --- |
| `20260623_vdc_sites_database.csv.kmz` | VODACOM | Sites radio Vodacom |
| `orange_existing_infrastructures_decembre_2025.kmz` | ORANGE | Infrastructures Orange |
| `08092023_fiber_mw_footprint.kmz` | FIBER_MW | Empreinte fibre et micro-ondes |
| `fiberco_view.kmz` | FIBERCO | Réseau Fiberco |
| `fttx.kmz` | FTTX | Référentiel FTTX |

## Import PostgreSQL

```powershell
python database/seed_telecom.py
```

Le script :
- applique `database/telecom_schema.sql`
- crée les opérateurs VODACOM, ORANGE, FIBER_MW, FIBERCO, FTTX
- importe points / lignes / polygones selon la géométrie KML détectée
- conserve les attributs KML dans `properties` (JSONB)

## API (mode DB)

- `GET /api/telecom/operators`
- `GET /api/telecom/infrastructure`
- `GET /api/telecom/network-lines`
- `GET /api/telecom/coverage-polygons`
- `GET /api/telecom/statistics`
- `GET /api/telecom/layers/{layer_key}`
- `GET /api/telecom/nearby-sites` (préparé, retour vide)

## Mode JSON

Les données télécom ne sont pas dupliquées en JSON statique. Le dashboard affiche :

> Données télécom disponibles en mode DB

Lancez l'application avec :

```powershell
.\start_sig.ps1 -Mode db
```
