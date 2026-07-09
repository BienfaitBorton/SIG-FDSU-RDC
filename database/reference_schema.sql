-- National Reference Framework — socle générique des référentiels sectoriels FDSU.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS reference;

CREATE TABLE IF NOT EXISTS reference.reference_catalog (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(64) NOT NULL UNIQUE,
    name            VARCHAR(255) NOT NULL,
    category        VARCHAR(64) NOT NULL,
    description     TEXT,
    source_name     VARCHAR(255),
    source_type     VARCHAR(64),
    update_frequency VARCHAR(64),
    status          VARCHAR(32) NOT NULL DEFAULT 'planned',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS reference.reference_object_types (
    id              SERIAL PRIMARY KEY,
    reference_code  VARCHAR(64) NOT NULL REFERENCES reference.reference_catalog(code) ON DELETE CASCADE,
    type_code       VARCHAR(64) NOT NULL,
    type_name       VARCHAR(255) NOT NULL,
    description     TEXT,
    symbology       JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (reference_code, type_code)
);

CREATE TABLE IF NOT EXISTS reference.reference_quality_indicators (
    id                          BIGSERIAL PRIMARY KEY,
    reference_code              VARCHAR(64) NOT NULL REFERENCES reference.reference_catalog(code) ON DELETE CASCADE,
    total_objects               INTEGER NOT NULL DEFAULT 0,
    objects_with_geometry       INTEGER NOT NULL DEFAULT 0,
    objects_without_geometry    INTEGER NOT NULL DEFAULT 0,
    objects_with_admin_link     INTEGER NOT NULL DEFAULT 0,
    objects_without_admin_link  INTEGER NOT NULL DEFAULT 0,
    quality_score               NUMERIC(5, 2),
    computed_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    details                     JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_reference_catalog_status
    ON reference.reference_catalog (status);

CREATE INDEX IF NOT EXISTS idx_reference_catalog_category
    ON reference.reference_catalog (category);

CREATE INDEX IF NOT EXISTS idx_reference_object_types_reference_code
    ON reference.reference_object_types (reference_code);

CREATE INDEX IF NOT EXISTS idx_reference_quality_reference_code
    ON reference.reference_quality_indicators (reference_code);

CREATE INDEX IF NOT EXISTS idx_reference_quality_computed_at
    ON reference.reference_quality_indicators (computed_at DESC);
