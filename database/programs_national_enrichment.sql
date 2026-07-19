-- Enrichissement schema programs pour Sites 20 476 (NSME natif)
-- Idempotent — safe à rejouer.

CREATE SCHEMA IF NOT EXISTS programs;

INSERT INTO programs.fdsu_programs (program_code, program_name, description, status, planned_sites, executed_sites, progress)
SELECT 'PROG_SITES_20476', 'Sites 20 476', 'Programme national complet FDSU (5 ans)', 'PLANIFIE', 20476, 0, 0
WHERE NOT EXISTS (
  SELECT 1 FROM programs.fdsu_programs WHERE program_code = 'PROG_SITES_20476'
);

ALTER TABLE programs.fdsu_sites ADD COLUMN IF NOT EXISTS population INTEGER;
ALTER TABLE programs.fdsu_sites ADD COLUMN IF NOT EXISTS population_range TEXT;
ALTER TABLE programs.fdsu_sites ADD COLUMN IF NOT EXISTS nearest_site TEXT;
ALTER TABLE programs.fdsu_sites ADD COLUMN IF NOT EXISTS distance_m DOUBLE PRECISION;
ALTER TABLE programs.fdsu_sites ADD COLUMN IF NOT EXISTS distance_level TEXT;
ALTER TABLE programs.fdsu_sites ADD COLUMN IF NOT EXISTS is_300_planned BOOLEAN DEFAULT FALSE;
ALTER TABLE programs.fdsu_sites ADD COLUMN IF NOT EXISTS phase TEXT;
ALTER TABLE programs.fdsu_sites ADD COLUMN IF NOT EXISTS technical_id TEXT;
ALTER TABLE programs.fdsu_sites ADD COLUMN IF NOT EXISTS display_name TEXT;
ALTER TABLE programs.fdsu_sites ADD COLUMN IF NOT EXISTS infra_name TEXT;
ALTER TABLE programs.fdsu_sites ADD COLUMN IF NOT EXISTS source_site_id INTEGER;
ALTER TABLE programs.fdsu_sites ADD COLUMN IF NOT EXISTS display_name_source TEXT;

COMMENT ON COLUMN programs.fdsu_sites.technical_id IS
  'Identifiant source technique (ex. Part2_*_NewSite_*) — jamais perdu.';
COMMENT ON COLUMN programs.fdsu_sites.display_name IS
  'Libellé métier résolu (helper site_display_name).';
COMMENT ON COLUMN programs.fdsu_sites.is_300_planned IS
  'True si le site est marqué calibration / vague 300 dans le programme national.';
COMMENT ON COLUMN programs.fdsu_sites.source_site_id IS
  'site_id du fichier programme (data/programs/sites_20476), distinct du PK DB.';

DROP INDEX IF EXISTS programs.uq_fdsu_sites_program_site_code;
CREATE UNIQUE INDEX uq_fdsu_sites_program_site_code
  ON programs.fdsu_sites (program_id, site_code);

CREATE INDEX IF NOT EXISTS idx_fdsu_sites_program_phase
  ON programs.fdsu_sites (program_id, is_300_planned);
CREATE INDEX IF NOT EXISTS idx_fdsu_sites_population
  ON programs.fdsu_sites (population);
CREATE INDEX IF NOT EXISTS idx_fdsu_sites_technical_id
  ON programs.fdsu_sites (technical_id);
CREATE INDEX IF NOT EXISTS idx_fdsu_sites_source_site_id
  ON programs.fdsu_sites (program_id, source_site_id);
