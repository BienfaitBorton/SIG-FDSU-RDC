from app.referentials.normalizer import SourceKind, StagingEntity
from app.referentials.normalizer.adapters import ExcelFDSUAdapter, HDXAdapter, KMZAdapter
from app.referentials.normalizer.entity_classifier import EntityClassifier
from app.referentials.normalizer.entity_matcher import EntityMatcher
from app.referentials.normalizer.entity_merger import EntityMerger
from app.referentials.normalizer.entity_statistics import EntityStatisticsService
from app.referentials.normalizer.entity_validator import EntityValidator
from app.referentials.normalizer.hierarchy import HierarchyResolver
from app.referentials.normalizer.integration import NormalizationModuleBridge, NormalizationModuleSnapshot, NormalizationRunRequest
from app.referentials.normalizer.normalizer import ReferentialNormalizer
from app.referentials.normalizer.report_generator import ReportGenerator


TEST_WORKBOOK = "data/imports/referentiel/FDSU Structure.xlsx"
TEST_KMZ = "data/raw/zones_fdsu.kmz"
TEST_HDX = "data/sources/hdx/cod_admin_boundaries.geojson.zip"


def build_normalizer() -> ReferentialNormalizer:
    hierarchy = HierarchyResolver()
    return ReferentialNormalizer(
        classifier=EntityClassifier(),
        hierarchy_resolver=hierarchy,
        validator=EntityValidator(hierarchy),
        matcher=EntityMatcher(),
        merger=EntityMerger(),
        statistics_service=EntityStatisticsService(),
        report_generator=ReportGenerator(),
    )


def test_normalizer_builds_hierarchy_and_reports_quality():
    normalizer = build_normalizer()
    entities = [
        StagingEntity(source_id="zone-nd", source_kind=SourceKind.EXCEL_FDSU, raw_name="Zone ND", zone_code="ND"),
        StagingEntity(source_id="prov-kin", source_kind=SourceKind.CENI, raw_name="Kinshasa", raw_code="P01", attributes={"TYPE": "PROVINCE"}, province_name="KINSHASA"),
        StagingEntity(source_id="ville-kin", source_kind=SourceKind.CENI, raw_name="Ville de Kinshasa", raw_code="V01", attributes={"TYPE": "VILLE"}, province_name="KINSHASA"),
        StagingEntity(source_id="com-gom", source_kind=SourceKind.CENI, raw_name="Commune urbaine de Gombe", raw_code="C01", attributes={"TYPE": "COMMUNE URBAINE"}, province_name="KINSHASA"),
    ]

    result = normalizer.normalize("sample", SourceKind.CENI, entities, reference_counts={})

    assert result.entities[1].entity_type == "province"
    assert result.entities[2].entity_type == "ville"
    assert result.entities[2].parent_source_id == "prov-kin"
    assert "# Normalization Report - sample" in result.markdown_report
    assert "quality_score" in result.report.quality


def test_matcher_proposes_non_automatic_merge_candidates():
    normalizer = build_normalizer()
    entities = [
        StagingEntity(source_id="grp-1", source_kind=SourceKind.CENI, raw_name="Groupement Lemba", raw_code="G100", attributes={"TYPE": "GROUPEMENT"}),
        StagingEntity(source_id="grp-2", source_kind=SourceKind.INS, raw_name="Groupement-Lemba", raw_code="G100", attributes={"TYPE": "GROUPEMENT"}),
    ]

    result = normalizer.normalize("merge-sample", SourceKind.CENI, entities, reference_counts={})

    assert len(result.report.merge_candidates) == 1
    assert result.report.merge_candidates[0]["auto_merge"] is False
    assert result.report.merge_candidates[0]["confidence"] >= 0.6


def test_excel_adapter_creates_staging_entities_from_workbook():
    adapter = ExcelFDSUAdapter()

    entities = adapter.load(TEST_WORKBOOK)

    assert len(entities) > 0
    assert any(entity.metadata.get("level") == "zone_fdsu" for entity in entities)
    assert any(entity.metadata.get("level") == "province" for entity in entities)
    assert any(entity.metadata.get("level") in {"ville", "territoire"} for entity in entities)


def test_kmz_adapter_creates_staging_entities_from_kmz():
    adapter = KMZAdapter()

    entities = adapter.load(TEST_KMZ)

    assert len(entities) > 0
    assert any(entity.geometry_type for entity in entities)
    assert any(entity.attributes for entity in entities)


def test_hdx_adapter_creates_staging_entities_from_official_geojson_zip():
    adapter = HDXAdapter()

    entities = adapter.load(TEST_HDX)

    assert len(entities) > 0
    assert any(entity.source_kind == SourceKind.HDX for entity in entities)
    assert any(entity.raw_code for entity in entities)
    assert any(entity.metadata.get("pcode_fields") for entity in entities)


def test_normalization_bridge_builds_snapshot():
    normalizer = build_normalizer()
    bridge = NormalizationModuleBridge(normalizer=normalizer, adapters={SourceKind.EXCEL_FDSU: ExcelFDSUAdapter()})

    result = bridge.run(
        NormalizationRunRequest(
            source_name="FDSU workbook",
            source_kind=SourceKind.EXCEL_FDSU,
            source_path=TEST_WORKBOOK,
        )
    )
    snapshot = bridge.build_snapshot(result)

    assert isinstance(snapshot, NormalizationModuleSnapshot)
    assert snapshot.entity_count > 0
    assert isinstance(snapshot.by_level, dict)
