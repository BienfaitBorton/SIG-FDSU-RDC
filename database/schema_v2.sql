-- database/schema_v2.sql
-- Schéma de base de données pour le référentiel administratif FDSU RDC.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TYPE collectivite_type AS ENUM ('Secteur', 'Chefferie', 'Cité');
CREATE TYPE site_status AS ENUM ('Projet', 'Survey', 'Installation', 'Actif', 'Maintenance', 'Hors service');

CREATE TABLE provinces (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(200) NOT NULL UNIQUE,
    code VARCHAR(5) NOT NULL UNIQUE,
    zone VARCHAR(5) NOT NULL,
    chef_lieu VARCHAR(200),
    population BIGINT,
    superficie NUMERIC(14, 2),
    geom geometry(MULTIPOLYGON, 4326)
);

CREATE INDEX provinces_geom_gix ON provinces USING GIST (geom);

CREATE TABLE territoires (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    code VARCHAR(5) NOT NULL,
    chef_lieu VARCHAR(200),
    province_id BIGINT NOT NULL REFERENCES provinces(id) ON DELETE CASCADE,
    geom geometry(MULTIPOLYGON, 4326)
);

CREATE INDEX territoires_geom_gix ON territoires USING GIST (geom);

CREATE TABLE collectivites (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    code VARCHAR(5) NOT NULL,
    type_collectivite collectivite_type NOT NULL,
    territoire_id BIGINT NOT NULL REFERENCES territoires(id) ON DELETE CASCADE,
    geom geometry(MULTIPOLYGON, 4326)
);

CREATE INDEX collectivites_geom_gix ON collectivites USING GIST (geom);

CREATE TABLE groupements (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    code VARCHAR(5) NOT NULL,
    collectivite_id BIGINT NOT NULL REFERENCES collectivites(id) ON DELETE CASCADE,
    geom geometry(MULTIPOLYGON, 4326)
);

CREATE INDEX groupements_geom_gix ON groupements USING GIST (geom);

CREATE TABLE villages (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    code VARCHAR(5) NOT NULL,
    groupement_id BIGINT NOT NULL REFERENCES groupements(id) ON DELETE CASCADE,
    geom geometry(POINT, 4326)
);

CREATE INDEX villages_geom_gix ON villages USING GIST (geom);

CREATE TABLE sites (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    code_site VARCHAR(30) NOT NULL UNIQUE,
    zone_fdsu VARCHAR(50),
    operateur VARCHAR(100),
    technologie VARCHAR(100),
    energie VARCHAR(100),
    statut site_status,
    date_creation DATE,
    date_installation DATE,
    date_mise_service DATE,
    altitude DOUBLE PRECISION,
    precision_gps DOUBLE PRECISION,
    observations TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    village_id BIGINT NOT NULL REFERENCES villages(id) ON DELETE CASCADE,
    geom geometry(POINT, 4326)
);

CREATE INDEX sites_statut_idx ON sites (statut);
CREATE INDEX sites_geom_gix ON sites USING GIST (geom);

CREATE TABLE missions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    titre VARCHAR(200) NOT NULL,
    description TEXT,
    date_debut DATE,
    date_fin DATE,
    site_id BIGINT REFERENCES sites(id) ON DELETE SET NULL
);

CREATE TABLE documents (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    type VARCHAR(100) NOT NULL,
    chemin VARCHAR(500) NOT NULL,
    mission_id BIGINT NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE photos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    caption VARCHAR(400),
    chemin VARCHAR(500) NOT NULL,
    mission_id BIGINT NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE import_history (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    username VARCHAR(200) NOT NULL,
    imported_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    entity VARCHAR(100) NOT NULL,
    rows_total BIGINT NOT NULL,
    rows_inserted BIGINT NOT NULL,
    rows_updated BIGINT NOT NULL,
    rows_rejected BIGINT NOT NULL,
    duration_seconds NUMERIC(10, 3) NOT NULL,
    status VARCHAR(50) NOT NULL,
    summary TEXT,
    file_hash VARCHAR(128)
);
