"""Tests Intelligence Territoriale multi-échelle — Data First, pas d’invention."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services import cartography_symbology_registry as symbology
from api.services import territorial_multiscale_service as tms

CLIENT = TestClient(app)
DUNGU = "TERRITOIRE-05-002"


def test_symbology_registry_has_distinct_domains():
    domains = {d["domain"] for d in symbology.list_domains()}
    assert "telecom" in domains
    assert "fiber" in domains
    assert "fiber_line" in domains
    assert "route" in domains
    assert "health" in domains
    assert "site_fdsu" in domains
    telecom = symbology.style_for("telecom")
    fiber = symbology.style_for("fiber")
    route = symbology.style_for("route")
    assert telecom["color"] != fiber["color"]
    assert telecom["color"] != route["color"]
    assert fiber["color"] != route["color"]


def test_map_legend_colors_match_registry_and_counts():
    mapped = CLIENT.get(f"/api/territorial-intelligence/territories/{DUNGU}/map")
    assert mapped.status_code == 200
    body = mapped.json()
    legend = body.get("legend") or []
    counts = (body.get("_meta") or {}).get("layer_counts") or {}
    assert legend, "Légende dynamique attendue"
    by_kind = {item["kind"]: item for item in legend}
    # Pas de regroupement Télécom / Fibre / Routes
    labels = " ".join(str(i.get("label") or "") for i in legend)
    assert "Télécom / Fibre / Routes" not in labels
    if counts.get("telecom"):
        assert "telecom" in by_kind
        assert by_kind["telecom"]["color"] == symbology.style_for("telecom")["color"]
        assert by_kind["telecom"]["count"] == counts["telecom"]
    if counts.get("fiber"):
        assert "fiber" in by_kind
        assert by_kind["fiber"]["color"] == symbology.style_for("fiber")["color"]
    if counts.get("route"):
        assert "route" in by_kind
        assert by_kind["route"]["color"] == symbology.style_for("route")["color"]
    # Aucune entrée légende sans objets visibles
    for item in legend:
        assert int(item.get("count") or 0) > 0


def test_entity_dungu_breadcrumb_children_coverage():
    res = CLIENT.get(f"/api/territorial-intelligence/entities/{DUNGU}")
    assert res.status_code == 200
    body = res.json()
    assert body["entity"]["type"] == "territoire"
    assert body["entity"]["name"]
    crumbs = body.get("breadcrumb") or []
    assert crumbs[0]["type"] == "rdc"
    assert any(c.get("type") == "territoire" for c in crumbs)
    children = body.get("children") or []
    cov = body.get("coverage") or {}
    covered = cov.get("population_covered") or {}
    uncovered = cov.get("population_uncovered") or {}
    if covered.get("value") is not None and uncovered.get("value") is not None:
        total = int(covered["value"]) + int(uncovered["value"])
        pop = body.get("population") or {}
        if pop.get("value") is not None:
            assert int(pop["value"]) == total
        assert cov.get("double_counting_guard")
    # En mode DB : au moins les chefferies de Dungu
    if os.environ.get("DATA_MODE", "").lower() == "db" or children:
        assert len(children) >= 1
        for child in children:
            assert child.get("id")
            assert child.get("type") == "collectivite"


@pytest.mark.skipif(
    os.environ.get("DATA_MODE", "json").lower() != "db",
    reason="Drill-down administratif nécessite PostGIS",
)
def test_drilldown_dungu_collectivite_groupement_localite():
    dungu = CLIENT.get(f"/api/territorial-intelligence/entities/{DUNGU}").json()
    children = dungu.get("children") or []
    assert children, "Collectivités Dungu attendues en DB"
    # Choisir une collectivité qui a réellement des enfants (hiérarchie inégale)
    coll_id = None
    coll_body = None
    for cand in children:
        probe = CLIENT.get(f"/api/territorial-intelligence/entities/{cand['id']}")
        assert probe.status_code == 200
        body = probe.json()
        if body.get("children"):
            coll_id = cand["id"]
            coll_body = body
            break
    assert coll_id and coll_body, "Au moins une chefferie de Dungu doit exposer des groupements"
    assert coll_body["entity"]["type"] == "collectivite"
    assert coll_body["entity"]["parent"]["type"] == "territoire"
    crumbs = coll_body["breadcrumb"]
    assert any(c.get("type") == "province" for c in crumbs)
    assert any(c.get("type") == "territoire" for c in crumbs)
    assert crumbs[-1]["id"] == coll_id
    assert any(c.get("id") == DUNGU for c in crumbs)

    g_children = coll_body.get("children") or []
    assert g_children, "Groupements attendus sous la chefferie"
    grp_id = g_children[0]["id"]
    grp = CLIENT.get(f"/api/territorial-intelligence/entities/{grp_id}")
    assert grp.status_code == 200
    assert grp.json()["entity"]["type"] == "groupement"

    locs = grp.json().get("children") or []
    if locs:
        loc = CLIENT.get(f"/api/territorial-intelligence/entities/{locs[0]['id']}")
        assert loc.status_code == 200
        loc_body = loc.json()
        assert loc_body["entity"]["type"] == "localite"
        # Pas de faux « nombre de localités » comme KPI inventé
        assert loc_body["entity"]["parent"]


@pytest.mark.skipif(
    os.environ.get("DATA_MODE", "json").lower() != "db",
    reason="Carte scoped DB",
)
def test_other_territory_and_province_resolution():
    listed = CLIENT.get("/api/territorial-intelligence/territories?limit=20")
    assert listed.status_code == 200
    territories = [t for t in listed.json().get("territories") or [] if t.get("territory_id") != DUNGU]
    if territories:
        tid = territories[0]["territory_id"]
        res = CLIENT.get(f"/api/territorial-intelligence/entities/{tid}")
        assert res.status_code == 200
        assert res.json()["entity"]["id"] == tid
    dungu = CLIENT.get(f"/api/territorial-intelligence/entities/{DUNGU}").json()
    province = (dungu.get("entity") or {}).get("hierarchy", {}).get("province")
    if province:
        pres = CLIENT.get(f"/api/territorial-intelligence/entities/PROVINCE-{province}")
        # Résolution souple par nom
        assert pres.status_code in {200, 404}
        if pres.status_code == 200:
            assert pres.json()["entity"]["type"] == "province"


def test_symbology_api():
    res = CLIENT.get("/api/territorial-intelligence/symbology")
    assert res.status_code == 200
    body = res.json()
    assert body.get("domains")
    kinds = {d["domain"] for d in body["domains"]}
    assert {"telecom", "fiber", "route", "health"}.issubset(kinds)
