-- Schéma Spatial Intelligence Engine — relations spatiales génériques FDSU.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS analysis;

CREATE TABLE IF NOT EXISTS analysis.spatial_relations (
    id              BIGSERIAL PRIMARY KEY,
    source_type     VARCHAR(64) NOT NULL,
    source_id       BIGINT NOT NULL,
    target_type     VARCHAR(64) NOT NULL,
    target_id       BIGINT NOT NULL,
    relation_type   VARCHAR(64) NOT NULL,
    distance_m      DOUBLE PRECISION,
    analysis_date   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    properties      JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_spatial_relations_source
    ON analysis.spatial_relations (source_type, source_id);

CREATE INDEX IF NOT EXISTS idx_spatial_relations_target
    ON analysis.spatial_relations (target_type, target_id);

CREATE INDEX IF NOT EXISTS idx_spatial_relations_relation_type
    ON analysis.spatial_relations (relation_type);

CREATE INDEX IF NOT EXISTS idx_spatial_relations_analysis_date
    ON analysis.spatial_relations (analysis_date DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_spatial_relations_unique
    ON analysis.spatial_relations (source_type, source_id, target_type, target_id, relation_type);

-- =========================================================
-- National Spatial Matching Engine (NSME)
-- Correspondances actifs FDSU ↔ besoins territoriaux
-- N'écrase PAS analysis.spatial_relations
-- =========================================================

CREATE TABLE IF NOT EXISTS analysis.asset_need_matches (
    id                    BIGSERIAL PRIMARY KEY,
    asset_type            VARCHAR(64) NOT NULL,
    asset_id              BIGINT,
    asset_business_id     VARCHAR(128),
    need_type             VARCHAR(64) NOT NULL,
    need_id               VARCHAR(128) NOT NULL,
    relation_type         VARCHAR(64) NOT NULL,
    distance_m            DOUBLE PRECISION,
    service_radius_m      DOUBLE PRECISION,
    population_impacted   DOUBLE PRECISION,
    localities_impacted   INTEGER DEFAULT 1,
    infrastructure_type   VARCHAR(128),
    priority_level        VARCHAR(64),
    category              VARCHAR(64),
    ndci_before           DOUBLE PRECISION,
    ndci_after_estimated  DOUBLE PRECISION,
    confidence_level      VARCHAR(32) NOT NULL DEFAULT 'partial',
    source_asset          VARCHAR(256),
    source_need           VARCHAR(256),
    calculation_method    VARCHAR(128),
    calculated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    province              VARCHAR(128),
    territoire            VARCHAR(128),
    program_code          VARCHAR(64),
    properties            JSONB NOT NULL DEFAULT '{}'::jsonb,
    geom_link             geometry(LineString, 4326)
);

CREATE INDEX IF NOT EXISTS idx_anm_asset
    ON analysis.asset_need_matches (asset_type, asset_id);

CREATE INDEX IF NOT EXISTS idx_anm_asset_business
    ON analysis.asset_need_matches (asset_type, asset_business_id);

CREATE INDEX IF NOT EXISTS idx_anm_need
    ON analysis.asset_need_matches (need_type, need_id);

CREATE INDEX IF NOT EXISTS idx_anm_relation
    ON analysis.asset_need_matches (relation_type);

CREATE INDEX IF NOT EXISTS idx_anm_distance
    ON analysis.asset_need_matches (distance_m);

CREATE INDEX IF NOT EXISTS idx_anm_territoire
    ON analysis.asset_need_matches (territoire);

CREATE INDEX IF NOT EXISTS idx_anm_province
    ON analysis.asset_need_matches (province);

CREATE INDEX IF NOT EXISTS idx_anm_program
    ON analysis.asset_need_matches (program_code);

CREATE INDEX IF NOT EXISTS idx_anm_priority
    ON analysis.asset_need_matches (priority_level);

CREATE INDEX IF NOT EXISTS idx_anm_calculated
    ON analysis.asset_need_matches (calculated_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_anm_unique
    ON analysis.asset_need_matches (asset_type, asset_business_id, need_type, need_id, relation_type);

CREATE INDEX IF NOT EXISTS idx_anm_geom_link
    ON analysis.asset_need_matches USING GIST (geom_link);

CREATE TABLE IF NOT EXISTS analysis.matching_runs (
    id              BIGSERIAL PRIMARY KEY,
    run_scope       VARCHAR(128) NOT NULL,
    status          VARCHAR(32) NOT NULL,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    assets_processed INTEGER DEFAULT 0,
    matches_written INTEGER DEFAULT 0,
    mode            VARCHAR(32),
    message         TEXT,
    details         JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_matching_runs_started
    ON analysis.matching_runs (started_at DESC);
