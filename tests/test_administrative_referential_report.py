from app.models import Collectivite, CollectiviteType, Groupement, Province, Territoire, Village
from app.referentiel_service import build_administrative_referential_report
from app.referentials.normalizer import SourceKind, StagingEntity
from app.referentials.quality import QualityService


def test_build_administrative_referential_report_compiles_tree_and_quality(db_session):
    province = Province(nom="Kinshasa", code="11", zone="ND", chef_lieu="Kinshasa", population=15000000, superficie=9965.0)
    db_session.add(province)
    db_session.flush()

    territoire = Territoire(nom="Funa", code="145", chef_lieu="Matete", province_id=province.id)
    db_session.add(territoire)
    db_session.flush()

    collectivite = Collectivite(
        nom="Kasa-Vubu",
        code="001",
        type_collectivite=CollectiviteType.Secteur,
        territoire_id=territoire.id,
    )
    db_session.add(collectivite)
    db_session.flush()

    groupement = Groupement(nom="Groupement Alpha", code="001", collectivite_id=collectivite.id)
    db_session.add(groupement)
    db_session.flush()

    village = Village(nom="Village Exemple", code="001", groupement_id=groupement.id)
    db_session.add(village)
    db_session.flush()
    db_session.commit()

    staging_entities = [
        StagingEntity(
            source_id="ville-kin",
            source_kind=SourceKind.CENI,
            raw_name="Ville de Kinshasa",
            raw_code="V01",
            entity_type="ville",
        )
    ]

    report = build_administrative_referential_report(db_session, staging_entities=staging_entities)

    assert report.statistics["province_count"] == 1
    assert report.statistics["territoire_count"] == 1
    assert report.statistics["groupement_count"] == 1
    assert report.statistics["village_count"] == 1
    assert report.root.children[0].level == "zone_fdsu"
    assert report.root.children[0].children[0].label == "Kinshasa"
    assert report.quality["global_quality"] is not None
    assert report.compatibility["future_levels"]["ville"] == 1
    assert any(anomaly.level == "ville" for anomaly in report.anomalies)
    assert "# Référentiel administratif national" in report.markdown


def test_quality_service_computes_global_score_when_metrics_are_provided():
    service = QualityService()

    report = service.evaluate(
        ["referentiel_administratif_national"],
        metrics={
            "referentiel_administratif_national": {
                "completeness": 95.0,
                "consistency": 90.0,
                "global_quality": 92.5,
                "entity_count": 10,
                "orphan_count": 1,
                "issue_count": 2,
            }
        },
    )

    assert report.global_quality == 92.5
    assert report.indicators[0].entity_count == 10
    assert report.indicators[0].orphan_count == 1