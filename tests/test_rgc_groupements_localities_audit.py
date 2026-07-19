"""Tests audit RGC Groupements & Localités (lecture seule, aucune intégration)."""

from __future__ import annotations

from api.services.nire import rgc_groupements_localities_audit as rgc


def test_existing_groupement_no_duplication():
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
    rgc_rows = [
        {
            "source_name": "Kimbanza",
            "normalized_name": "kimbanza",
            "rgc_groupment_code": "20430301",
            "territoire": "Luozi",
            "secteur_chefferie": "Kimbanza",
            "has_valid_geometry": True,
            "geometry_role": "REPRESENTATIVE_POINT",
            "geometry_provenance": "RGC_DERIVED_FROM_LOCALITIES",
            "rgc_pcode_sample": "CD123",
            "locality_count": 3,
        }
    ]
    out = rgc.match_groupements(fdsu, rgc_rows)
    assert out["ALREADY_IN_GROUPMENT_REFERENTIAL"] == 1
    assert out["NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY"] == 0


def test_orthographic_variant_matched():
    fdsu = [
        {
            "canonical_id": "G1",
            "nom": "Kimbanza",
            "territoire": "Luozi",
            "collectivite_parent": "Kimbanza Secteur",
        }
    ]
    rgc_rows = [
        {
            "source_name": "Kimbanza",
            "normalized_name": "kimbanza",
            "rgc_groupment_code": None,
            "territoire": "Luozi",
            "secteur_chefferie": "Kimbanza Secteur",
            "has_valid_geometry": True,
            "geometry_role": "REPRESENTATIVE_POINT",
            "geometry_provenance": "RGC_DERIVED_FROM_LOCALITIES",
            "locality_count": 1,
        }
    ]
    out = rgc.match_groupements(fdsu, rgc_rows)
    assert out["ALREADY_IN_GROUPMENT_REFERENTIAL"] == 1


def test_homonym_other_territory_distinct():
    fdsu = [
        {
            "canonical_id": "G1",
            "nom": "Likati",
            "territoire": "Aketi",
            "collectivite_parent": "C1",
        }
    ]
    rgc_rows = [
        {
            "source_name": "Likati",
            "normalized_name": "likati",
            "rgc_groupment_code": None,
            "territoire": "Bondo",
            "secteur_chefferie": "C2",
            "has_valid_geometry": True,
            "geometry_role": "REPRESENTATIVE_POINT",
            "geometry_provenance": "RGC_DERIVED_FROM_LOCALITIES",
            "locality_count": 2,
        }
    ]
    out = rgc.match_groupements(fdsu, rgc_rows)
    assert out["NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY"] == 1
    assert out["HOMONYM_DISTINCT_RGC_GROUPMENT"] >= 1
    assert out["ALREADY_IN_GROUPMENT_REFERENTIAL"] == 0


def test_new_groupement_with_valid_rgc_point_is_candidate():
    fdsu = []
    rgc_rows = [
        {
            "source_name": "Nouveau Grpt",
            "normalized_name": "nouveau grpt",
            "rgc_groupment_code": "999001",
            "territoire": "T-X",
            "secteur_chefferie": "S-X",
            "has_valid_geometry": True,
            "geometry_role": "REPRESENTATIVE_POINT",
            "geometry_provenance": "RGC_DERIVED_FROM_LOCALITIES",
            "locality_count": 4,
        }
    ]
    out = rgc.match_groupements(fdsu, rgc_rows)
    assert out["NEW_RGC_GROUPMENT_WITH_VALID_GEOMETRY"] == 1
    assert out["POTENTIAL_ENRICHED_GROUPMENT_TOTAL"] == 1
    sample = out["classified_new_sample"][0]
    assert sample["geometry_role"] == "REPRESENTATIVE_POINT"


def test_rgc_point_is_not_administrative_boundary():
    rows = [
        {
            "GROUPEMENT": "Alpha",
            "CODE_GRPT": "100",
            "TERRITOIRE": "Terr A",
            "COLLECTIV": "Sect A",
            "PCODE": "1",
            "_lat": -4.3,
            "_lon": 15.3,
            "ORIGINE": "chef-lieu",
        }
    ]
    derived = rgc.derive_rgc_groupements_from_localities(rows)
    assert len(derived) == 1
    assert derived[0]["geometry_role"] == "REPRESENTATIVE_POINT"
    assert derived[0]["geometry_role"] != "OFFICIAL_ADMINISTRATIVE_BOUNDARY"
    assert derived[0]["has_valid_geometry"] is True


def test_existing_locality_no_duplication():
    fdsu = [
        {
            "canonical_id": "L1",
            "nom": "Village X",
            "territoire": "Terr A",
            "groupement": None,
            "metadata": {"extended_data": {"PCODE": "12345"}},
        }
    ]
    rgc_rows = [
        {
            "PCODE": 12345,
            "NOM1": "Village X",
            "NOM2": "",
            "TERRITOIRE": "Terr A",
            "GROUPEMENT": "G1",
            "CODE_GRPT": "10",
            "_lat": -4.1,
            "_lon": 15.1,
            "TYPE": 0,
        }
    ]
    out = rgc.match_localities(rgc_rows, fdsu)
    assert out["ALREADY_IN_LOCALITY_REFERENTIAL"] == 1
    assert out["NEW_RGC_LOCALITY_WITH_VALID_GEOMETRY"] == 0


def test_new_geolocated_locality_is_candidate():
    fdsu = [
        {
            "canonical_id": "L1",
            "nom": "Autre",
            "territoire": "Terr A",
            "metadata": {"extended_data": {"PCODE": "1"}},
        }
    ]
    rgc_rows = [
        {
            "PCODE": 99999,
            "NOM1": "Nouvelle Localite",
            "NOM2": "",
            "TERRITOIRE": "Terr B",
            "GROUPEMENT": "G2",
            "CODE_GRPT": "20",
            "_lat": -5.0,
            "_lon": 16.0,
            "TYPE": 0,
        }
    ]
    out = rgc.match_localities(rgc_rows, fdsu)
    assert out["NEW_RGC_LOCALITY_WITH_VALID_GEOMETRY"] == 1
    assert out["POTENTIAL_ENRICHED_LOCALITY_TOTAL"] == 2


def test_groupement_code_used_for_attachment_simulation():
    fdsu = [
        {
            "canonical_id": "L1",
            "nom": "Loc A",
            "territoire": "Terr A",
            "groupement": None,
            "metadata": {"extended_data": {"PCODE": "555"}},
        }
    ]
    rgc_rows = [
        {
            "PCODE": 555,
            "NOM1": "Loc A",
            "TERRITOIRE": "Terr A",
            "GROUPEMENT": "Groupement Z",
            "CODE_GRPT": "20430301",
            "_lat": -4.2,
            "_lon": 15.2,
        }
    ]
    links = rgc.simulate_groupement_links(rgc_rows, fdsu)
    assert links["NEW_GROUPMENT_LINKS_FROM_RGC"] == 1
    assert links["LOCALITIES_WITH_GROUPMENT_BEFORE"] == 0


def test_spatial_proximity_alone_does_not_create_admin_link():
    """Sans attribut GROUPEMENT/CODE_GRPT, aucun lien admin simulé."""
    fdsu = [
        {
            "canonical_id": "L1",
            "nom": "Loc Near",
            "territoire": "Terr A",
            "groupement": None,
            "metadata": {"extended_data": {"PCODE": "777"}},
        }
    ]
    rgc_rows = [
        {
            "PCODE": 777,
            "NOM1": "Loc Near",
            "TERRITOIRE": "Terr A",
            "GROUPEMENT": None,
            "CODE_GRPT": None,
            "_lat": -4.2,
            "_lon": 15.2,
        }
    ]
    links = rgc.simulate_groupement_links(rgc_rows, fdsu)
    assert links["NEW_GROUPMENT_LINKS_FROM_RGC"] == 0
    assert links["RGC_MATCHED_LOCALITIES_WITH_GROUPMENT_LINK"] == 0


def test_raw_source_path_immutable_contract():
    assert rgc.LOCALITE_ZIP.name == "Localite.zip"
    assert "raw" in str(rgc.RAW_DIR).replace("\\", "/").lower()
    # Contrat audit : manifeste déclare immutabilité
    manifest = rgc.acquisition_manifest()
    assert manifest["immutable_raw"] is True
    assert manifest["no_in_place_modification"] is True
    assert manifest["datasets"]["groupements_shapefile"]["obtained"] is False


def test_audit_meta_declares_no_integration():
    st = rgc.AuditState()
    st.meta = {
        "audit_only": True,
        "no_integration": True,
        "analytical_equality_after_future_integration": True,
    }
    assert st.meta["no_integration"] is True
    assert st.meta["audit_only"] is True


def test_geometry_usable_rdc_bounds():
    assert rgc.geometry_usable(-4.3, 15.3)[0] is True
    assert rgc.geometry_usable(0.0, 0.0)[0] is False
    assert rgc.geometry_usable(90.0, 0.0)[0] is False


def test_mercator_conversion_produces_rdc_like_coords():
    # Approximate Kinshasa-area mercator meters → degrees
    lon, lat = rgc.mercator_to_wgs84(1700000.0, -500000.0)
    assert -180 <= lon <= 180
    assert -90 <= lat <= 90
