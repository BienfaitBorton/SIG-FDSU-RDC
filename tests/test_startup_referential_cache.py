"""Tests cache runtime référentiels (startup performance)."""

from __future__ import annotations

from pathlib import Path

from api.services import referential_runtime_cache as rrc
from api.services.nire import groupement_controlled_integration as gci
from api.services.nire import locality_controlled_integration as lci


def setup_function():
    rrc.set_cache_enabled(True)
    rrc.clear_all_caches()
    rrc.reset_stats()


def test_json_file_not_reparsed_when_cached(tmp_path: Path):
    path = tmp_path / "sample.json"
    path.write_text('{"a": 1}', encoding="utf-8")
    rrc.reset_stats()
    a = rrc.load_json_file(path, label="sample.json")
    b = rrc.load_json_file(path, label="sample.json")
    assert a == b == {"a": 1}
    stats = rrc.file_stats_snapshot()["sample.json"]
    assert stats["READ_COUNT"] == 1
    assert stats["PARSE_COUNT"] == 1
    assert stats["CACHE_HIT"] >= 1


def test_locality_count_stable_and_cached():
    rrc.reset_stats()
    n1 = lci.national_locality_count(include_enrichment=True)
    stats1 = rrc.file_stats_snapshot()
    n2 = lci.national_locality_count(include_enrichment=True)
    stats2 = rrc.file_stats_snapshot()
    assert n1 == n2 == 47130
    # Second call must not increase READ_COUNT for heavy locality files
    for name in (
        "locality_referential_official.json",
        "locality_referential_nci_enrichment.json",
        "locality_groupement_links_rgc.json",
    ):
        if name in stats1:
            assert stats2[name]["READ_COUNT"] == stats1[name]["READ_COUNT"]


def test_groupement_count_stable_and_cached():
    rrc.reset_stats()
    c1 = gci.national_groupement_counts(include_enrichment=True)
    stats1 = rrc.file_stats_snapshot()
    c2 = gci.national_groupement_counts(include_enrichment=True)
    stats2 = rrc.file_stats_snapshot()
    assert c1["historical_count"] == 1681
    assert c1["enrichment_count"] == 961
    assert c1["total_count"] == 2642
    assert c2 == c1
    for name in (
        "groupement_referential_official.json",
        "groupement_referential_rgc_enrichment.json",
    ):
        if name in stats1:
            assert stats2[name]["READ_COUNT"] == stats1[name]["READ_COUNT"]


def test_cache_disabled_reparses(tmp_path: Path):
    path = tmp_path / "nocache.json"
    path.write_text('{"x": 2}', encoding="utf-8")
    rrc.set_cache_enabled(False)
    rrc.reset_stats()
    rrc.load_json_file(path, label="nocache.json")
    rrc.load_json_file(path, label="nocache.json")
    stats = rrc.file_stats_snapshot()["nocache.json"]
    assert stats["READ_COUNT"] == 2
    assert stats["CACHE_HIT"] == 0
    rrc.set_cache_enabled(True)


def test_ceni_lazy_lru_same_object():
    from api.services import ceni_registry_service

    ceni_registry_service.registry.cache_clear()
    a = ceni_registry_service.registry()
    b = ceni_registry_service.registry()
    assert a is b
    assert len(a.get("assets") or []) > 0


def test_invalidate_forces_reread(tmp_path: Path):
    path = tmp_path / "inv.json"
    path.write_text('{"v": 1}', encoding="utf-8")
    rrc.reset_stats()
    rrc.load_json_file(path, label="inv.json")
    rrc.invalidate_paths(path)
    rrc.load_json_file(path, label="inv.json")
    assert rrc.file_stats_snapshot()["inv.json"]["READ_COUNT"] == 2
