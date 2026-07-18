-- Staging FDSU MNO — hors KPI COUNT(telecom.infrastructure)
-- Copie dérivée contrôlée pour relations spatiales PostGIS (4 MNO).

CREATE TABLE IF NOT EXISTS telecom.fdsu_mno_sites (
    id                   SERIAL PRIMARY KEY,
    row_id               VARCHAR(128) NOT NULL UNIQUE,
    operator_code        VARCHAR(64) NOT NULL,
    site_name            VARCHAR(512) NOT NULL,
    status_normalized    VARCHAR(64),
    rat                  VARCHAR(255),
    nire_classification  VARCHAR(128),
    nire_quality_status  VARCHAR(64),
    requires_human_review BOOLEAN NOT NULL DEFAULT FALSE,
    latitude             DOUBLE PRECISION NOT NULL,
    longitude            DOUBLE PRECISION NOT NULL,
    geom                 geometry(Point, 4326),
    source_file          VARCHAR(512),
    source_row           INTEGER,
    source_hash          VARCHAR(128),
    properties           JSONB NOT NULL DEFAULT '{}'::jsonb,
    synced_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fdsu_mno_sites_operator
    ON telecom.fdsu_mno_sites (operator_code);

CREATE INDEX IF NOT EXISTS idx_fdsu_mno_sites_geom
    ON telecom.fdsu_mno_sites USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_fdsu_mno_sites_quality
    ON telecom.fdsu_mno_sites (nire_quality_status);

COMMENT ON TABLE telecom.fdsu_mno_sites IS
    'Sites MNO FDSU provisoires — exclus du KPI national telecom.infrastructure';
