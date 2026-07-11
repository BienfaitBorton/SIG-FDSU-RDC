-- Schéma PostgreSQL des programmes FDSU — source officielle en mode DB.
-- Les fichiers JSON / GeoJSON / KMZ / Excel restent des supports d'import/export.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS programs;

CREATE TABLE IF NOT EXISTS programs.fdsu_programs (
    id              SERIAL PRIMARY KEY,
    program_code    VARCHAR(64) NOT NULL UNIQUE,
    program_name    VARCHAR(255) NOT NULL,
    description     TEXT,
    status          VARCHAR(32) NOT NULL DEFAULT 'PLANIFIE',
    start_date      DATE,
    end_date        DATE,
    planned_sites   INTEGER NOT NULL DEFAULT 0,
    executed_sites  INTEGER NOT NULL DEFAULT 0,
    progress        NUMERIC(5, 2) NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS programs.fdsu_sites (
    id              SERIAL PRIMARY KEY,
    program_id      INTEGER NOT NULL REFERENCES programs.fdsu_programs(id) ON DELETE CASCADE,
    site_code       VARCHAR(128),
    site_name       VARCHAR(512) NOT NULL,
    province        VARCHAR(255),
    territoire      VARCHAR(255),
    zone            VARCHAR(64),
    status          VARCHAR(64),
    priority_status VARCHAR(128),
    fdsu_score      NUMERIC(8, 2),
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    geom            geometry(Point, 4326),
    source          VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fdsu_sites_program_id
    ON programs.fdsu_sites (program_id);

CREATE INDEX IF NOT EXISTS idx_fdsu_sites_geom
    ON programs.fdsu_sites USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_fdsu_sites_province
    ON programs.fdsu_sites (province);

CREATE INDEX IF NOT EXISTS idx_fdsu_sites_status
    ON programs.fdsu_sites (status);

CREATE INDEX IF NOT EXISTS idx_fdsu_programs_status
    ON programs.fdsu_programs (status);
