# Base PostgreSQL/PostGIS SIG-FDSU RDC

Ce dossier prépare le passage v0.8.0 du fallback JSON vers une base PostgreSQL/PostGIS.

## Fichiers

- `init.sql` : active PostGIS.
- `schema.sql` : crée les tables géographiques, tables d'import et index.
- `seed_from_json.py` : lit les rapports JSON locaux et insère les données en base avec `ON CONFLICT DO NOTHING`.

## Préparation

Créer la base :

```powershell
createdb -U postgres sig_fdsu_rdc
```

Initialiser PostGIS et le schéma :

```powershell
psql -U postgres -d sig_fdsu_rdc -f database/init.sql
psql -U postgres -d sig_fdsu_rdc -f database/schema.sql
```

Si le schéma existait déjà avant l'ajout de `altitude`, appliquer :

```powershell
psql -U postgres -d sig_fdsu_rdc -f database/fix_2d_altitude.sql
```

Les géométries sont normalisées en 2D avant insertion. Les coordonnées `[longitude, latitude, altitude]` deviennent une géométrie 2D `[longitude, latitude]`, et `altitude` est stockée dans la colonne dédiée.

Charger les référentiels JSON :

```powershell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/sig_fdsu_rdc"
python database/seed_from_json.py
```

Le seed ne supprime rien, ignore les doublons et produit un rapport `inserted / ignored / errors`.
