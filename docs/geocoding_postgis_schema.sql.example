-- Module Géocodage Intelligent FDSU
-- Structure PostGIS prête pour enregistrer les résultats de géocodage contrôlé.
-- Ne pas exécuter automatiquement en production sans revue DBA.

CREATE SCHEMA IF NOT EXISTS geocoding;

CREATE TABLE IF NOT EXISTS geocoding.geocoding_results (
    id                  BIGSERIAL PRIMARY KEY,
    site_id             BIGINT NULL,
    nom_site            TEXT NULL,
    adresse_originale   TEXT NULL,
    latitude            DOUBLE PRECISION NULL,
    longitude           DOUBLE PRECISION NULL,
    geom                geometry(Point, 4326) NULL,
    source_geocoding    TEXT NULL,
    confidence_level    TEXT NULL CHECK (confidence_level IN ('high', 'medium', 'low') OR confidence_level IS NULL),
    validation_status   TEXT NULL,
    job_id              TEXT NULL,
    source_row_number   INTEGER NULL,
    old_latitude        DOUBLE PRECISION NULL,
    old_longitude       DOUBLE PRECISION NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_geocoding_results_geom
    ON geocoding.geocoding_results USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_geocoding_results_job
    ON geocoding.geocoding_results (job_id);

CREATE INDEX IF NOT EXISTS idx_geocoding_results_validation
    ON geocoding.geocoding_results (validation_status);

COMMENT ON TABLE geocoding.geocoding_results IS
    'Résultats de géocodage contrôlé FDSU — ne remplace pas programs.fdsu_sites sans validation métier.';
