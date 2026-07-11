-- Schéma Moteur de Décision FDSU v1.0 — scores de priorité des sites.

CREATE SCHEMA IF NOT EXISTS decision;

CREATE TABLE IF NOT EXISTS decision.fdsu_site_scores (
    id              BIGSERIAL PRIMARY KEY,
    site_id         INTEGER NOT NULL REFERENCES programs.fdsu_sites(id) ON DELETE CASCADE,
    program_code    VARCHAR(64) NOT NULL,
    priority_score  NUMERIC(5, 2) NOT NULL CHECK (priority_score >= 0 AND priority_score <= 100),
    priority_level  VARCHAR(32) NOT NULL,
    criteria_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fdsu_site_scores_site_id
    ON decision.fdsu_site_scores (site_id);

CREATE INDEX IF NOT EXISTS idx_fdsu_site_scores_program_code
    ON decision.fdsu_site_scores (program_code);

CREATE INDEX IF NOT EXISTS idx_fdsu_site_scores_priority_level
    ON decision.fdsu_site_scores (priority_level);

CREATE INDEX IF NOT EXISTS idx_fdsu_site_scores_priority_score
    ON decision.fdsu_site_scores (priority_score DESC);

CREATE INDEX IF NOT EXISTS idx_fdsu_site_scores_computed_at
    ON decision.fdsu_site_scores (computed_at DESC);
