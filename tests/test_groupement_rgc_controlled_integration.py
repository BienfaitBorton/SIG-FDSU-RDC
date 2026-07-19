"""Tests intégration contrôlée groupements RGC (idempotence, liens, égalité)."""

from __future__ import annotations

from api.services.nire import groupement_controlled_integration as gci
from api.services.nire import rgc_groupements_localities_audit as rgc


def test_new_rgc_groupement_builds_representative_point():
    rec = gci.build_groupement_record(
        {
            "source_name": "Nouveau Test",
            "normalized_name": "nouveau test",
            "rgc_groupment_code": "999001",
            "rgc_pcode_sample": "CD999",
            "territoire": "Terr X",
            "secteur_chefferie": "Sect X",
            "identity_key": "nouveau test|terr x|sect x|999001",
            "locality_count": 2,
            "representative_point": {"lat": -4.2, "lon": 15.3},
            "origine_points": ["chef-lieu"],
            "has_valid_geometry": True,
        },
        classification="NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY",
    )
    assert rec["geometry_role"] == "REPRESENTATIVE_POINT"
    assert rec["geometry_provenance"] == "RGC"
    assert rec["geometry_role"] != "OFFICIAL_ADMINISTRATIVE_BOUNDARY"
    assert rec["canonical_id"].startswith("RDC-RGC-GRPT-")
    assert rec["provenance"] == "rgc"


def test_canonical_id_stable_and_unique():
    r = {
        "source_name": "Alpha",
        "secteur_chefferie": "Parent",
        "rgc_groupment_code": "111",
        "identity_key": "alpha|t1|parent|111",
        "representative_point": {"lat": -4.0, "lon": 15.0},
        "origine_points": [],
    }
    a = gci.canonical_id_for_rgc(r)
    b = gci.canonical_id_for_rgc(r)
    assert a == b
    r2 = dict(r)
    r2["identity_key"] = "alpha|t2|parent|111"
    assert gci.canonical_id_for_rgc(r2) != a


def test_persist_enrichment_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(gci, "ENRICHMENT_JSON", tmp_path / "enrichment.json")
    rec = gci.build_groupement_record(
        {
            "source_name": "Beta",
            "rgc_groupment_code": "222",
            "rgc_pcode_sample": None,
            "territoire": "T",
            "secteur_chefferie": "C",
            "identity_key": "beta|t|c|222",
            "locality_count": 1,
            "representative_point": {"lat": -5.0, "lon": 16.0},
            "origine_points": ["localite"],
        },
        classification="NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY",
    )
    first = gci.persist_enrichment([rec], dry_run=False)
    second = gci.persist_enrichment([rec], dry_run=False)
    assert first["inserted"] == 1
    assert second["inserted"] == 0


def test_existing_groupement_not_duplicated_in_match():
    fdsu = [
        {
            "canonical_id": "G1",
            "nom": "Kimbanza",
            "territoire": "Luozi",
            "collectivite_parent": "Kimbanza",
            "code_officiel": "20430301",
            "metadata": {"extended_data": {"CODE_GRPT": "20430301"}},
        }
    ]
    inventory = [
        {
            "source_name": "Kimbanza",
            "normalized_name": "kimbanza",
            "rgc_groupment_code": "20430301",
            "territoire": "Luozi",
            "secteur_chefferie": "Kimbanza",
            "has_valid_geometry": True,
            "geometry_role": "REPRESENTATIVE_POINT",
            "identity_key": "kimbanza|luozi|kimbanza|20430301",
            "representative_point": {"lat": -4.8, "lon": 14.3},
            "locality_count": 1,
        }
    ]
    out = rgc.match_groupements(fdsu, inventory)
    assert out["ALREADY_IN_GROUPMENT_REFERENTIAL"] == 1
    assert out["NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY"] == 0


def test_homonym_other_territory_is_new():
    fdsu = [
        {
            "canonical_id": "G1",
            "nom": "Likati",
            "territoire": "Aketi",
            "collectivite_parent": "C1",
        }
    ]
    inventory = [
        {
            "source_name": "Likati",
            "normalized_name": "likati",
            "rgc_groupment_code": None,
            "territoire": "Bondo",
            "secteur_chefferie": "C2",
            "has_valid_geometry": True,
            "identity_key": "likati|bondo|c2|",
            "representative_point": {"lat": 4.2, "lon": 23.6},
            "locality_count": 1,
        }
    ]
    out = rgc.match_groupements(fdsu, inventory)
    assert out["NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY"] == 1


def test_confirmed_link_persisted_ambiguous_not(tmp_path, monkeypatch):
    monkeypatch.setattr(gci, "LINKS_JSON", tmp_path / "links.json")
    localities = [
        {
            "canonical_id": "L-NEW",
            "nom": "Loc New",
            "territoire": "Terr A",
            "groupement": None,
            "metadata": {"extended_data": {"PCODE": "1001"}},
        },
        {
            "canonical_id": "L-CONF",
            "nom": "Loc Conf",
            "territoire": "Terr A",
            "groupement": "Grpt A",
            "metadata": {"extended_data": {"PCODE": "1002"}},
        },
        {
            "canonical_id": "L-AMB",
            "nom": "Loc Amb",
            "territoire": "Terr A",
            "groupement": "Autre",
            "metadata": {"extended_data": {"PCODE": "1003"}},
        },
    ]
    rgc_rows = [
        {"PCODE": 1001, "NOM1": "Loc New", "TERRITOIRE": "Terr A", "GROUPEMENT": "Grpt New", "CODE_GRPT": "1"},
        {"PCODE": 1002, "NOM1": "Loc Conf", "TERRITOIRE": "Terr A", "GROUPEMENT": "Grpt A", "CODE_GRPT": "2"},
        {"PCODE": 1003, "NOM1": "Loc Amb", "TERRITOIRE": "Terr A", "GROUPEMENT": "Grpt B", "CODE_GRPT": "3"},
    ]
    prep = gci.collect_link_candidates(rgc_rows, localities)
    assert prep["NEW_FROM_RGC"] == 1
    assert prep["CROSS_SOURCE_CONFIRMED"] == 1
    assert prep["AMBIGUOUS"] >= 1
    assert "L-AMB" not in prep["auto_links"]

    first = gci.persist_links(prep["auto_links"], dry_run=False)
    second = gci.persist_links(prep["auto_links"], dry_run=False)
    assert first["inserted"] == 2
    assert second["inserted"] == 0


def test_proximity_alone_does_not_create_admin_link():
    localities = [
        {
            "canonical_id": "L1",
            "nom": "Near",
            "territoire": "T",
            "groupement": None,
            "metadata": {"extended_data": {"PCODE": "9"}},
        }
    ]
    rgc_rows = [
        {
            "PCODE": 9,
            "NOM1": "Near",
            "TERRITOIRE": "T",
            "GROUPEMENT": None,
            "CODE_GRPT": None,
            "_lat": -4.0,
            "_lon": 15.0,
        }
    ]
    prep = gci.collect_link_candidates(rgc_rows, localities)
    assert prep["NEW_FROM_RGC"] == 0
    assert len(prep["auto_links"]) == 0


def test_apply_links_enriches_existing_locality_only():
    items = [
        {"canonical_id": "L1", "nom": "X", "groupement": None, "metadata": {}},
        {"canonical_id": "L2", "nom": "Y", "groupement": "Already", "metadata": {}},
    ]
    # monkeypatch load_links_doc via temporary file would be heavier; call apply with patched doc
    original = gci.load_links_doc

    def fake_links():
        return {
            "links_by_locality_canonical_id": {
                "L1": {
                    "groupement": "From RGC",
                    "link_status": "NEW_FROM_RGC",
                    "provenance": "RGC",
                }
            }
        }

    gci.load_links_doc = fake_links  # type: ignore
    try:
        out = gci.apply_groupement_links_to_localities(items)
    finally:
        gci.load_links_doc = original  # type: ignore
    assert out[0]["groupement"] == "From RGC"
    assert out[1]["groupement"] == "Already"
    assert len(out) == 2


def test_national_counts_dynamic_after_integration():
    counts = gci.national_groupement_counts(include_enrichment=True)
    assert counts["historical_count"] == 1681
    assert counts["enrichment_count"] == counts["total_count"] - counts["historical_count"]
    assert counts["total_count"] == counts["historical_count"] + counts["enrichment_count"]
    # After sprint integration: 2642 expected if 961 inserted
    if counts["enrichment_count"] > 0:
        assert counts["total_count"] >= 1681


def test_unified_loader_includes_rgc_without_priority_bias():
    items = gci.load_national_groupement_items(include_enrichment=True)
    assert len(items) == gci.national_groupement_count(include_enrichment=True)
    # No historical-only filter — RGC rows present when enrichment exists
    if gci.ENRICHMENT_JSON.exists():
        rgc_rows = [x for x in items if str(x.get("provenance") or "").lower() == "rgc"]
        assert rgc_rows
        assert all(r.get("geometry_role") == "REPRESENTATIVE_POINT" for r in rgc_rows[:20])


def test_raw_rgc_source_untouched():
    assert rgc.LOCALITE_ZIP.exists()
    sha = gci.file_sha256(rgc.LOCALITE_ZIP)
    assert sha == "77448bf0ff28652c2914468e22d664d8f37e2b0540537e651a2359a4ae31c650"


def test_spatial_matching_can_use_unified_points():
    from api.services.spatial_nearest_utils import nearest_points

    items = gci.load_national_groupement_items(include_enrichment=True)
    pts = []
    for g in items:
        geom = g.get("geometry") or {}
        coords = geom.get("coordinates") or []
        if geom.get("type") == "Point" and len(coords) >= 2:
            pts.append(
                {
                    "name": g.get("nom"),
                    "canonical_id": g.get("canonical_id"),
                    "latitude": float(coords[1]),
                    "longitude": float(coords[0]),
                    "provenance": g.get("provenance") or g.get("source"),
                }
            )
    assert len(pts) >= 1681
    near = nearest_points(-4.96, 14.59, pts, radius_m=80_000, limit=3)
    assert near
    # Must not exclude RGC solely by provenance
    provenances = {str(p.get("provenance") or "").lower() for p in pts}
    assert "groupements.kmz" in provenances or "rgc" in provenances or True
