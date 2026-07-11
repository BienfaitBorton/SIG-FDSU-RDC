-- Schéma PostgreSQL du Référentiel Télécom National FDSU.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS telecom;

CREATE TABLE IF NOT EXISTS telecom.operators (
    id              SERIAL PRIMARY KEY,
    operator_code   VARCHAR(64) NOT NULL UNIQUE,
    operator_name   VARCHAR(255) NOT NULL,
    operator_type   VARCHAR(64),
    country         VARCHAR(64) DEFAULT 'RDC',
    status          VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS telecom.infrastructure (
    id              SERIAL PRIMARY KEY,
    operator_id     INTEGER NOT NULL REFERENCES telecom.operators(id) ON DELETE CASCADE,
    infra_code      VARCHAR(128),
    infra_name      VARCHAR(512) NOT NULL,
    infra_type      VARCHAR(64),
    technology      VARCHAR(128),
    source_file     VARCHAR(255),
    province        VARCHAR(255),
    territoire      VARCHAR(255),
    status          VARCHAR(64),
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    geom            geometry(Point, 4326),
    properties      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS telecom.network_lines (
    id              SERIAL PRIMARY KEY,
    operator_id     INTEGER NOT NULL REFERENCES telecom.operators(id) ON DELETE CASCADE,
    line_code       VARCHAR(128),
    line_name       VARCHAR(512) NOT NULL,
    line_type       VARCHAR(64),
    technology      VARCHAR(128),
    source_file     VARCHAR(255),
    geom            geometry(LineString, 4326),
    properties      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS telecom.coverage_polygons (
    id              SERIAL PRIMARY KEY,
    operator_id     INTEGER NOT NULL REFERENCES telecom.operators(id) ON DELETE CASCADE,
    polygon_code    VARCHAR(128),
    polygon_name    VARCHAR(512) NOT NULL,
    polygon_type    VARCHAR(64),
    technology      VARCHAR(128),
    source_file     VARCHAR(255),
    geom            geometry(Geometry, 4326),
    properties      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT coverage_polygons_geom_type_chk CHECK (
        GeometryType(geom) IN ('POLYGON', 'MULTIPOLYGON')
    )
);

CREATE INDEX IF NOT EXISTS idx_telecom_operators_code
    ON telecom.operators (operator_code);

CREATE INDEX IF NOT EXISTS idx_telecom_infrastructure_operator
    ON telecom.infrastructure (operator_id);

CREATE INDEX IF NOT EXISTS idx_telecom_infrastructure_geom
    ON telecom.infrastructure USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_telecom_infrastructure_province
    ON telecom.infrastructure (province);

CREATE INDEX IF NOT EXISTS idx_telecom_network_lines_operator
    ON telecom.network_lines (operator_id);

CREATE INDEX IF NOT EXISTS idx_telecom_network_lines_geom
    ON telecom.network_lines USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_telecom_coverage_polygons_operator
    ON telecom.coverage_polygons (operator_id);

CREATE INDEX IF NOT EXISTS idx_telecom_coverage_polygons_geom
    ON telecom.coverage_polygons USING GIST (geom);
