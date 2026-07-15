"""Decision Experience Layer + anti-exposition API métier."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dxl_module_and_routes_exist():
    html = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "dashboard/app.js").read_text(encoding="utf-8")
    dxl = (ROOT / "dashboard/modules/decision-experience/decision-experience.js").read_text(encoding="utf-8")
    assert "decision-experience-panel" in html
    assert "modules/decision-experience/decision-experience.js" in html
    assert "decision_experience" in app_js
    assert "decision-case" in app_js
    assert "spatial-impact" in app_js
    assert "openDecisionCase" in dxl
    assert "openSpatialImpact" in dxl
    assert "Dossier de décision" in html


def test_no_business_user_redirect_to_decision_case_api():
    detail = (ROOT / "dashboard/modules/decision-center/decision-detail.js").read_text(encoding="utf-8")
    center = (ROOT / "dashboard/modules/decision-center/decision-center.js").read_text(encoding="utf-8")
    assert "open(`/api/decision/case" not in detail.replace(" ", "")
    assert 'open(`${API_BASE}/api/decision/case' not in detail
    assert "openDecisionCase" in detail
    assert "openDecisionCase" in center
    # explain button navigates to DXL, not raw JSON tab
    assert "openDecisionCase('site'" in center or 'openDecisionCase("site"' in center


def test_case_ref_is_dashboard_hash():
    explain = (ROOT / "api/services/explainable_decision_service.py").read_text(encoding="utf-8")
    assert '#decision-case/site/' in explain
    assert '"case_ref": f"/api/decision/case/' not in explain


def test_sig_map_tooltips_bind_api():
    tip = (ROOT / "dashboard/modules/shared/map-tooltips.js").read_text(encoding="utf-8")
    assert "function bind(layer, featureOrData, entityType" in tip or "function bind(layer, featureOrData, entityType," in tip
    assert "SigMapTooltips.bind" in tip or "bind," in tip
    for kind in (
        "site",
        "ccn",
        "uncovered_locality",
        "territory",
        "health",
        "telecom",
        "fiber",
        "backbone",
        "spatial_match",
        "mission_candidate",
        "cluster",
    ):
        assert kind in tip
    assert "undefined" in tip  # filtered as non-presentable
    assert "feature" in tip.lower()
    assert "point" in tip.lower()

def test_tooltip_factory_rejects_technical_noise():
    # Execute filter logic via node-less static checks
    tip = (ROOT / "dashboard/modules/shared/map-tooltips.js").read_text(encoding="utf-8")
    assert "isPresentable" in tip
    assert "null" in tip
    assert "Cliquer pour analyser en détail" in tip
    assert "/api/" in tip  # guard against api routes in click resolver


def test_vocabulary_no_decision_detail_workspace():
    html = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    assert "Decision Detail Workspace" not in html
    assert "Analyse détaillée" in html or "Dossier de décision" in html


def test_spatial_impact_resilience_patterns():
    """Explain KO ne doit plus bloquer toute la vue via Promise.all.

    Contrat DXL mince (orchestrateur) : la résilience allSettled / tracedFetch
    vit dans SpatialImpactController + DxlCore ; decision-experience.js délègue.
    """
    dxl = (ROOT / "dashboard/modules/decision-experience/decision-experience.js").read_text(encoding="utf-8")
    controller = (ROOT / "dashboard/modules/decision-experience/spatial-impact-controller.js").read_text(
        encoding="utf-8"
    )
    core = (ROOT / "dashboard/modules/decision-experience/dxl-core.js").read_text(encoding="utf-8")
    html = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    assert "Promise.allSettled" in controller
    assert "tracedFetch" in core and "tracedFetch" in controller
    assert "timeoutMs" in controller or "timeoutMs" in core
    assert "loadSpatialImpact" in dxl
    assert "dxl-section-services" in html
    assert "État des services" in html
    assert "Analyse explicative indisponible" in controller
    assert "Les données d’impact restent consultables" in controller or "Les données d'impact restent consultables" in controller
    assert "const [needs, impact, explain, mapPayload] = await Promise.all([" not in dxl
    assert "const [needs, impact, explain, mapPayload] = await Promise.all([" not in controller
    assert "softLoadingHtml" in core and "softLoadingHtml" in controller
    assert "AbortController" in core
    assert "Promise.resolve(boot).catch" in dxl
