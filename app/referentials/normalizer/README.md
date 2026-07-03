# Referential Normalizer

## Purpose

This package normalizes administrative referential data on a staging copy only.
It never writes to PostgreSQL and never mutates the source files.

## Supported source families

- Excel FDSU
- HDX / OCHA COD Administrative Boundaries
- KMZ
- GeoJSON
- Shapefile
- CENI
- CAID
- INS

## Adapters

- `ExcelFDSUAdapter`: converts FDSU workbook sheets into `StagingEntity` records.
- `HDXAdapter`: converts official HDX COD GeoJSON layers into `StagingEntity` records.
- `KMZAdapter`: converts KMZ placemarks into `StagingEntity` records.
- `CeniStagingAdapter`: reserved contract for official CENI machine-readable layers.
- `CaidStagingAdapter`: reserved contract for CAID statistical referentials.
- `InsStagingAdapter`: reserved contract for INS nomenclatures.

## Governance integration

`NormalizationModuleBridge` is the staging-only connector meant to feed the
`Gestion des Référentiels` module later, without changing existing APIs.

## Main responsibilities

- detect the administrative entity type
- normalize names and codes
- build parent-child hierarchy
- detect structural and semantic issues
- suggest merge candidates with a confidence score
- compute quality and coverage statistics
- generate JSON and Markdown reports

## Processing flow

1. Load source data into `StagingEntity` objects.
2. Normalize names, codes, and geometry type.
3. Classify each entity level.
4. Build hierarchy links.
5. Validate issues against structural rules and reference counts.
6. Match likely duplicates.
7. Produce merge proposals without auto-merge.
8. Compute statistics and quality indicators.
9. Generate JSON and Markdown reports.

## Reference counts used for validation

- province: 26
- ville: 33
- territoire: 145
- chefferie: 259
- secteur: 478
- commune_urbaine: 137
- commune_rurale: 202
- groupement: 6053
- groupement_incorpore: 87
- quartier: 2187
- village: 78855

## Extension points

- source-specific adapters can prepare `StagingEntity` objects upstream
- HDX adapter can be used to benchmark national administrative coverage and Pcode compatibility
- classification heuristics can be enriched without changing orchestration
- geometry validation can be replaced by a stronger spatial validator later
- merge scoring can be tuned per source system
- report generation can be plugged into dashboard and referential management modules later
