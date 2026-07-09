-- Référentiel Santé v1.0 — structures sanitaires RDC (structure uniquement).

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS health;

CREATE TABLE IF NOT EXISTS health.health_facility_types (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(32) NOT NULL UNIQUE,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    category        VARCHAR(64),
    symbology       JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS health.health_facilities (
    id                  SERIAL PRIMARY KEY,
    official_code       VARCHAR(128),
    name                VARCHAR(512) NOT NULL,
    facility_type_code  VARCHAR(32) REFERENCES health.health_facility_types(code),
    province_name       VARCHAR(255),
    territory_name      VARCHAR(255),
    collectivity_name   VARCHAR(255),
    groupement_name     VARCHAR(255),
    locality_name       VARCHAR(255),
    manager_type        VARCHAR(128),
    level               VARCHAR(64),
    population_served   INTEGER,
    has_electricity     BOOLEAN,
    has_internet        BOOLEAN,
    data_source         VARCHAR(255),
    observations        TEXT,
    geom                geometry(Point, 4326),
    properties          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS health.health_statistics (
    id                          BIGSERIAL PRIMARY KEY,
    scope_type                  VARCHAR(64) NOT NULL DEFAULT 'national',
    scope_name                  VARCHAR(255) NOT NULL DEFAULT 'RDC',
    total_facilities            INTEGER NOT NULL DEFAULT 0,
    hospitals                   INTEGER NOT NULL DEFAULT 0,
    health_centers              INTEGER NOT NULL DEFAULT 0,
    health_posts                INTEGER NOT NULL DEFAULT 0,
    facilities_with_geometry    INTEGER NOT NULL DEFAULT 0,
    facilities_without_geometry INTEGER NOT NULL DEFAULT 0,
    facilities_with_electricity INTEGER NOT NULL DEFAULT 0,
    facilities_with_internet    INTEGER NOT NULL DEFAULT 0,
    computed_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    details                     JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_health_facilities_geom
    ON health.health_facilities USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_health_facilities_type
    ON health.health_facilities (facility_type_code);

CREATE INDEX IF NOT EXISTS idx_health_facilities_province
    ON health.health_facilities (province_name);

CREATE INDEX IF NOT EXISTS idx_health_facilities_territory
    ON health.health_facilities (territory_name);

CREATE INDEX IF NOT EXISTS idx_health_facilities_official_code
    ON health.health_facilities (official_code);

CREATE INDEX IF NOT EXISTS idx_health_statistics_scope
    ON health.health_statistics (scope_type, scope_name);
