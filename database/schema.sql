CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS zones (
    id BIGSERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    nom TEXT NOT NULL,
    type TEXT DEFAULT 'Zone FDSU',
    parent_id BIGINT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    geom GEOMETRY(Geometry, 4326),
    source TEXT,
    quality_score DOUBLE PRECISION,
    status TEXT DEFAULT 'official_candidate',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS provinces (
    id BIGSERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    nom TEXT NOT NULL,
    type TEXT DEFAULT 'Province',
    parent_id BIGINT REFERENCES zones(id),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    geom GEOMETRY(Geometry, 4326),
    source TEXT,
    quality_score DOUBLE PRECISION,
    status TEXT DEFAULT 'official_candidate',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS territoires (
    id BIGSERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    nom TEXT NOT NULL,
    type TEXT DEFAULT 'Territoire',
    parent_id BIGINT REFERENCES provinces(id),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    geom GEOMETRY(Geometry, 4326),
    source TEXT,
    quality_score DOUBLE PRECISION,
    status TEXT DEFAULT 'official_candidate',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS villes (
    id BIGSERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    nom TEXT NOT NULL,
    type TEXT DEFAULT 'Ville',
    parent_id BIGINT REFERENCES provinces(id),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    geom GEOMETRY(Geometry, 4326),
    source TEXT,
    quality_score DOUBLE PRECISION,
    status TEXT DEFAULT 'official_candidate',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS collectivites (
    id BIGSERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    nom TEXT NOT NULL,
    type TEXT,
    parent_id BIGINT REFERENCES territoires(id),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    geom GEOMETRY(Geometry, 4326),
    source TEXT,
    quality_score DOUBLE PRECISION,
    status TEXT DEFAULT 'official_candidate',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS groupements (
    id BIGSERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    nom TEXT NOT NULL,
    type TEXT DEFAULT 'Groupement',
    parent_id BIGINT REFERENCES collectivites(id),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    geom GEOMETRY(Geometry, 4326),
    source TEXT,
    quality_score DOUBLE PRECISION,
    status TEXT DEFAULT 'official_candidate',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS localites (
    id BIGSERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    nom TEXT NOT NULL,
    type TEXT DEFAULT 'Localité',
    parent_id BIGINT REFERENCES groupements(id),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    geom GEOMETRY(Geometry, 4326),
    source TEXT,
    quality_score DOUBLE PRECISION,
    status TEXT DEFAULT 'official_candidate',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sites (
    id BIGSERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    nom TEXT NOT NULL,
    type TEXT DEFAULT 'Site FDSU',
    parent_id BIGINT REFERENCES localites(id),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    geom GEOMETRY(Geometry, 4326),
    source TEXT,
    quality_score DOUBLE PRECISION,
    status TEXT DEFAULT 'draft',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS missions (
    id BIGSERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    nom TEXT NOT NULL,
    type TEXT DEFAULT 'Mission',
    parent_id BIGINT REFERENCES sites(id),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    geom GEOMETRY(Geometry, 4326),
    source TEXT,
    quality_score DOUBLE PRECISION,
    status TEXT DEFAULT 'draft',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS import_batches (
    id BIGSERIAL PRIMARY KEY,
    source TEXT,
    status TEXT DEFAULT 'completed',
    inserted_count INTEGER DEFAULT 0,
    ignored_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    report JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS import_errors (
    id BIGSERIAL PRIMARY KEY,
    batch_id BIGINT REFERENCES import_batches(id),
    table_name TEXT,
    entity_code TEXT,
    entity_name TEXT,
    error_message TEXT,
    raw_entity JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_zones_code ON zones(code);
CREATE INDEX IF NOT EXISTS idx_zones_nom ON zones(nom);
CREATE INDEX IF NOT EXISTS idx_zones_parent_id ON zones(parent_id);
CREATE INDEX IF NOT EXISTS idx_zones_geom ON zones USING GIST(geom);

CREATE INDEX IF NOT EXISTS idx_provinces_code ON provinces(code);
CREATE INDEX IF NOT EXISTS idx_provinces_nom ON provinces(nom);
CREATE INDEX IF NOT EXISTS idx_provinces_parent_id ON provinces(parent_id);
CREATE INDEX IF NOT EXISTS idx_provinces_geom ON provinces USING GIST(geom);

CREATE INDEX IF NOT EXISTS idx_territoires_code ON territoires(code);
CREATE INDEX IF NOT EXISTS idx_territoires_nom ON territoires(nom);
CREATE INDEX IF NOT EXISTS idx_territoires_parent_id ON territoires(parent_id);
CREATE INDEX IF NOT EXISTS idx_territoires_geom ON territoires USING GIST(geom);

CREATE INDEX IF NOT EXISTS idx_villes_code ON villes(code);
CREATE INDEX IF NOT EXISTS idx_villes_nom ON villes(nom);
CREATE INDEX IF NOT EXISTS idx_villes_parent_id ON villes(parent_id);
CREATE INDEX IF NOT EXISTS idx_villes_geom ON villes USING GIST(geom);

CREATE INDEX IF NOT EXISTS idx_collectivites_code ON collectivites(code);
CREATE INDEX IF NOT EXISTS idx_collectivites_nom ON collectivites(nom);
CREATE INDEX IF NOT EXISTS idx_collectivites_parent_id ON collectivites(parent_id);
CREATE INDEX IF NOT EXISTS idx_collectivites_geom ON collectivites USING GIST(geom);

CREATE INDEX IF NOT EXISTS idx_groupements_code ON groupements(code);
CREATE INDEX IF NOT EXISTS idx_groupements_nom ON groupements(nom);
CREATE INDEX IF NOT EXISTS idx_groupements_parent_id ON groupements(parent_id);
CREATE INDEX IF NOT EXISTS idx_groupements_geom ON groupements USING GIST(geom);

CREATE INDEX IF NOT EXISTS idx_localites_code ON localites(code);
CREATE INDEX IF NOT EXISTS idx_localites_nom ON localites(nom);
CREATE INDEX IF NOT EXISTS idx_localites_parent_id ON localites(parent_id);
CREATE INDEX IF NOT EXISTS idx_localites_geom ON localites USING GIST(geom);

CREATE INDEX IF NOT EXISTS idx_sites_code ON sites(code);
CREATE INDEX IF NOT EXISTS idx_sites_nom ON sites(nom);
CREATE INDEX IF NOT EXISTS idx_sites_parent_id ON sites(parent_id);
CREATE INDEX IF NOT EXISTS idx_sites_geom ON sites USING GIST(geom);

CREATE INDEX IF NOT EXISTS idx_missions_code ON missions(code);
CREATE INDEX IF NOT EXISTS idx_missions_nom ON missions(nom);
CREATE INDEX IF NOT EXISTS idx_missions_parent_id ON missions(parent_id);
CREATE INDEX IF NOT EXISTS idx_missions_geom ON missions USING GIST(geom);
