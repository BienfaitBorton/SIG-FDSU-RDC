#!/usr/bin/env python3
"""Build intermediate C2/C3 file versions for commit split (no git commit)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = Path(__file__).resolve().parent
FINAL = B / "final"
INTER = B / "intermediate"


def read_final(rel: str) -> str:
    return (FINAL / rel).read_text(encoding="utf-8")


def write_inter(name: str, rel: str, content: str) -> None:
    path = INTER / name / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def build_c2_service(svc: str) -> str:
    svc2 = svc.replace(
        '"relation_types": ["NEAR_HEALTH_FACILITY", "NEAREST_HEALTH_FACILITY", "WITHIN_HEALTH_SERVICE_AREA"]',
        '"relation_types": ["NEAR_HEALTH_FACILITY"]',
    )
    svc2 = re.sub(
        r'\n    "NEAREST_HEALTH_FACILITY": \{.*?\n    \},\n',
        "\n",
        svc2,
        count=1,
        flags=re.S,
    )
    svc2 = re.sub(
        r'\n    "WITHIN_HEALTH_SERVICE_AREA": \{.*?\n    \},\n',
        "\n",
        svc2,
        count=1,
        flags=re.S,
    )
    svc2 = re.sub(
        r'probes\["health"\] = \{.*?\n    \}',
        '''probes["health"] = {
        "referential_exists": bool(health_count and int(health_count) > 0),
        "record_count": health_count,
        "nsme_wired": False,
        "nsme_source": None,
        "search_radius_m": None,
    }''',
        svc2,
        count=1,
        flags=re.S,
    )
    svc2 = re.sub(
        r"\n    try:\n        from api\.services\.spatial_matching_service import get_rules\n\n"
        r"        radii = \(get_rules\(\)\.get\(\"service_radii_m\"\) or \{\}\)\n"
        r"        probes\[\"health\"\]\[\"search_radius_m\"\] = radii\.get\(\"health_proximity\"\) or 5000\n"
        r"        probes\[\"health\"\]\[\"nearest_max_m\"\] = radii\.get\(\"health_nearest_max\"\) or 25000\n"
        r"    except Exception:\n"
        r"        probes\[\"health\"\]\[\"search_radius_m\"\] = 5000\n"
        r"        probes\[\"health\"\]\[\"nearest_max_m\"\] = 25000\n",
        "\n",
        svc2,
        count=1,
    )
    svc2 = re.sub(
        r"\n    if cat_id == \"health\" and ref_exists and nsme_wired and not produced:.*?"
        r"return \{\n"
        r"            \"status\": \"empty\",\n"
        r"            \"maturity\": \"partial\" if matches else \"partial\",\n"
        r"            \"empty_reason\": \"no_relations_found\",\n"
        r"            \"integration_case\": 1,\n"
        r"            \"note\": note,\n"
        r"        \}\n",
        "\n",
        svc2,
        count=1,
        flags=re.S,
    )
    svc2 = svc2.replace(
        '        "health.health_facilities": "Référentiel Santé (health.health_facilities)",\n',
        "",
    )
    svc2 = svc2.replace(
        '        "postgis_nearest_health": "Analyse PostGIS — établissement de santé",\n',
        "",
    )
    svc2 = re.sub(
        r"\n    # Filtrer les anciennes relations Santé dérivées NCI.*?"
        r"if not matches and needs\.get\(\"_meta\", \{\}\)\.get\(\"status\"\) == \"not_found\":\n"
        r"        return None\n",
        "\n    if not matches and needs.get(\"_meta\", {}).get(\"status\") == \"not_found\":\n"
        "        return None\n",
        svc2,
        count=1,
        flags=re.S,
    )
    svc2 = re.sub(
        r"\n    # Santé : si seulement NEAREST hors rayon.*?break\n\n    why_panel",
        "\n    why_panel",
        svc2,
        count=1,
        flags=re.S,
    )
    return svc2


def build_c2_js(js: str) -> str:
    js2 = js.replace(
        '\n          <button type="button" class="secondary-button" id="sdg-refresh-btn">'
        "Recalculer les relations spatiales</button>",
        "",
    )
    js2 = re.sub(
        r"\n      const refresh = event\.target\?\.closest\?\.\('#sdg-refresh-btn'\);\n"
        r"      if \(refresh\) \{\n"
        r"        refreshSpatialRelations\(refresh\);\n"
        r"        return;\n"
        r"      \}\n",
        "\n",
        js2,
        count=1,
    )
    js2 = re.sub(
        r"\n  function refreshSpatialRelations\(btn\) \{.*?\n  \}\n\n  /\* ── Public API",
        "\n\n  /* ── Public API",
        js2,
        count=1,
        flags=re.S,
    )
    js2 = js2.replace("\n    refreshSpatialRelations,\n", "\n")
    return js2


def build_c3_audit(audit: str) -> str:
    audit3 = audit.replace(
        "| Santé | Oui | 37 562 établissements | Points | `/api/health/*` | health_service | "
        "Stats, nearest PostGIS | NEAREST / NEAR / WITHIN_HEALTH (NSME ← `health.health_facilities`) | "
        "SDG + Decision Center | 🟢* |",
        "| Santé | Oui | 37 562 établissements | Points | `/api/health/*` | health_service | "
        "Stats, nearest | NEAR_HEALTH (NCI) | Decision Center panel | 🔴* |",
    )
    audit3 = re.sub(
        r"\* Santé \(correctif P0 2026-07-12\).*",
        "* Santé : référentiel peuplé, mais NSME n’interroge pas `health.health_facilities` "
        "(dérivation NCI) → **anomalie CAS 4**.",
        audit3,
        count=1,
    )
    audit3 = audit3.replace(
        "| Santé 37k établissements | **Corrigé P0** — matching NSME PostGIS `health.health_facilities` |",
        "| Santé 37k établissements | Pas de matching NSME sur `health.*` |",
    )
    audit3 = audit3.replace(
        "| P0 | ~~Brancher NSME sur `health.health_facilities` (CAS 4)~~ **FAIT** |",
        "| P0 | Brancher NSME sur `health.health_facilities` (CAS 4) |",
    )
    return audit3


def build_c3_report(report: str) -> str:
    report3 = report.replace(
        "| Anomalies P0 entièrement résolues (câblage santé NSME) | "
        "**Pass** — A14 corrigé (PostGIS `health.health_facilities`) |",
        "| Anomalies P0 entièrement résolues (câblage santé NSME) | "
        "**Ouvert** — planifié, non inventé dans ce sprint |",
    )
    report3 = report3.replace(
        "| A4 | `POST /spatial-matching/refresh` jamais depuis UI | 2 | P0 | "
        "**Corrigé** — bouton SDG « Recalculer les relations spatiales » |",
        "| A4 | `POST /spatial-matching/refresh` jamais depuis UI | 2 | P0 | Documentée |",
    )
    report3 = report3.replace(
        "| A14 | **Santé 37k** — NSME branché sur `health.health_facilities` | **4→1** | **P0** | "
        "**Corrigé** — relations PostGIS ; SDG maturité 🟢/🟡 |",
        "| A14 | **Santé 37k** non interrogée par NSME (`health.*`) | **4** | **P0** | "
        "**Signalée dans SDG** (`maturity=anomaly`) |",
    )
    report3 = report3.replace(
        "| Santé | 🟢 Opérationnel (PostGIS) ou 🟡 Partiel si 0 dans le rayon documenté |",
        "| Santé | 🔴 Anomalie — référentiel peuplé, matching non sur `health.*` |",
    )
    report3 = re.sub(
        r"\n6\. \*\*P0 Santé \(2026-07-12\)\*\*.*",
        "",
        report3,
        count=1,
    )
    return report3


def main() -> None:
    svc = read_final("api/services/spatial_decision_graph_service.py")
    js = read_final(
        "dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js"
    )
    audit = read_final("PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_AUDIT_V1.md")
    report = read_final("PROJECT_MANAGEMENT/ARCHITECTURE/INTEGRITY_GATE_REPORT_V1.md")

    svc2 = build_c2_service(svc)
    js2 = build_c2_js(js)
    audit3 = build_c3_audit(audit)
    report3 = build_c3_report(report)

    write_inter("c2", "api/services/spatial_decision_graph_service.py", svc2)
    write_inter(
        "c2",
        "dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js",
        js2,
    )
    write_inter("c3", "PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_AUDIT_V1.md", audit3)
    write_inter(
        "c3", "PROJECT_MANAGEMENT/ARCHITECTURE/INTEGRITY_GATE_REPORT_V1.md", report3
    )
    write_inter("c4", "api/services/spatial_decision_graph_service.py", svc)
    write_inter(
        "c4",
        "dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js",
        js,
    )
    write_inter("c4", "PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_AUDIT_V1.md", audit)
    write_inter(
        "c4", "PROJECT_MANAGEMENT/ARCHITECTURE/INTEGRITY_GATE_REPORT_V1.md", report
    )

    # Sanity markers
    assert "NEAREST_HEALTH_FACILITY" not in svc2 or 'relation_types": ["NEAR_HEALTH_FACILITY"]' in svc2
    assert "nsme_wired\": False" in svc2 or '"nsme_wired": False' in svc2
    assert "refreshSpatialRelations" not in js2
    assert "sdg-refresh-btn" not in js2
    assert "Anomalie CAS 4" in audit3 or "anomalie CAS 4" in audit3
    assert "A14 corrigé" not in report3
    assert "NEAREST_HEALTH_FACILITY" in svc
    assert "refreshSpatialRelations" in js
    print("C2 svc delta bytes", len(svc) - len(svc2))
    print("C2 js delta bytes", len(js) - len(js2))
    print("OK intermediates")


if __name__ == "__main__":
    main()
