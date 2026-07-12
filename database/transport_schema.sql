-- Schéma PostgreSQL — Référentiel Transport & Accessibility Intelligence FDSU.
-- Source d'exploitation : tables PostGIS uniquement (jamais le KMZ brut en production).

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS transport;

CREATE TABLE IF NOT EXISTS transport.routes (
    id              SERIAL PRIMARY KEY,
    source_id       VARCHAR(128),
    nom             VARCHAR(512),
    type_route      VARCHAR(128),
    categorie       VARCHAR(128),
    etat            VARCHAR(128),
    revetement      VARCHAR(128),
    numero          VARCHAR(64),
    cl_admin        VARCHAR(128),
    gestion         VARCHAR(128),
    sens            VARCHAR(128),
    nb_voies        VARCHAR(32),
    source          VARCHAR(255) NOT NULL DEFAULT 'OpenStreetMap',
    source_file     VARCHAR(255) NOT NULL,
    date_maj_source DATE,
    longueur_m      DOUBLE PRECISION,
    geom            geometry(LineString, 4326) NOT NULL,
    properties      JSONB NOT NULL DEFAULT '{}'::jsonb,
    date_import     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_transport_routes_source_id
    ON transport.routes (source_id)
    WHERE source_id IS NOT NULL AND source_id <> '';

CREATE INDEX IF NOT EXISTS idx_transport_routes_geom
    ON transport.routes USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_transport_routes_type
    ON transport.routes (type_route);

CREATE INDEX IF NOT EXISTS idx_transport_routes_nom
    ON transport.routes (nom);

CREATE INDEX IF NOT EXISTS idx_transport_routes_source_file
    ON transport.routes (source_file);

CREATE TABLE IF NOT EXISTS transport.import_runs (
    id              SERIAL PRIMARY KEY,
    source_file     VARCHAR(255) NOT NULL,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    status          VARCHAR(32) NOT NULL DEFAULT 'running',
    rows_parsed     INTEGER DEFAULT 0,
    rows_imported   INTEGER DEFAULT 0,
    rows_rejected   INTEGER DEFAULT 0,
    quality_report  JSONB NOT NULL DEFAULT '{}'::jsonb,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS transport.quality_checks (
    id              SERIAL PRIMARY KEY,
    check_code      VARCHAR(64) NOT NULL,
    check_label     VARCHAR(255) NOT NULL,
    severity        VARCHAR(32) NOT NULL DEFAULT 'info',
    count_value     INTEGER NOT NULL DEFAULT 0,
    details         JSONB NOT NULL DEFAULT '{}'::jsonb,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transport.statistics (
    id              SERIAL PRIMARY KEY,
    metric_key      VARCHAR(64) NOT NULL UNIQUE,
    metric_value    DOUBLE PRECISION,
    metric_label    VARCHAR(255),
    details         JSONB NOT NULL DEFAULT '{}'::jsonb,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON SCHEMA transport IS 'Référentiel Transport national FDSU — Routes principales';
COMMENT ON TABLE transport.routes IS 'Tronçons routiers (LineString EPSG:4326) importés depuis Routes_principales.shp.kmz';
