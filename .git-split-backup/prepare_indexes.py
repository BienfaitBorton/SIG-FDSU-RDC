#!/usr/bin/env python3
"""Prepare four alternate git indexes for IG / SDG / Data First / Health P0 (no commit)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = Path(__file__).resolve().parent
FINAL = B / "final"
INTER = B / "intermediate"
MANIFEST = B / "manifests"
MANIFEST.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def hash_object(path: Path) -> str:
    r = run(["git", "hash-object", "-w", str(path)])
    if r.returncode != 0:
        raise RuntimeError(f"hash-object failed for {path}: {r.stderr}")
    return r.stdout.strip()


def mode_for(rel: str) -> str:
    return "100644"


def write_rules_c2() -> Path:
    """Rules without health P0 radii / relation types."""
    src = FINAL / "data/business/spatial_matching_rules.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    rels = data.get("relation_types") or []
    data["relation_types"] = [
        r
        for r in rels
        if r
        not in {
            "NEAREST_HEALTH_FACILITY",
            "WITHIN_HEALTH_SERVICE_AREA",
        }
    ]
    # Keep NEAR_HEALTH_FACILITY in generic contract
    if "NEAR_HEALTH_FACILITY" not in data["relation_types"]:
        # insert after CONNECTS_CCN if present
        try:
            i = data["relation_types"].index("CONNECTS_CCN") + 1
            data["relation_types"].insert(i, "NEAR_HEALTH_FACILITY")
        except ValueError:
            data["relation_types"].append("NEAR_HEALTH_FACILITY")
    radii = data.get("service_radii_m") or {}
    for k in (
        "health_proximity",
        "health_service_area",
        "health_nearest_max",
        "health_max_matches",
    ):
        radii.pop(k, None)
    data["service_radii_m"] = radii
    meta = data.get("_meta") or {}
    meta["updated_at"] = "2026-07-11"
    meta["note"] = (
        "Rayons et règles configurables — ne pas hardcoder dans les services."
    )
    data["_meta"] = meta
    out = INTER / "c2" / "data/business/spatial_matching_rules.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return out


# Commit file maps: path -> content source path (absolute or relative to ROOT)
# For new files from FINAL; for intermediates from INTER.

C1_FILES = {
    ".cursor/rules/e2e-integrity-gate.mdc": FINAL
    / ".cursor/rules/e2e-integrity-gate.mdc",
    "PROJECT_MANAGEMENT/ARCHITECTURE/E2E_INTEGRITY_GATE.md": FINAL
    / "PROJECT_MANAGEMENT/ARCHITECTURE/E2E_INTEGRITY_GATE.md",
    "api/routes/decision_engine.py": FINAL / "api/routes/decision_engine.py",
    "api/services/explainable_decision_service.py": FINAL
    / "api/services/explainable_decision_service.py",
    "api/services/site_entity_resolver.py": FINAL / "api/services/site_entity_resolver.py",
    "dashboard/app.js": FINAL / "dashboard/app.js",
    "dashboard/modules/decision-experience/decision-experience.css": FINAL
    / "dashboard/modules/decision-experience/decision-experience.css",
    "dashboard/modules/decision-experience/decision-case-controller.js": FINAL
    / "dashboard/modules/decision-experience/decision-case-controller.js",
    "dashboard/modules/decision-experience/decision-error-handler.js": FINAL
    / "dashboard/modules/decision-experience/decision-error-handler.js",
    "dashboard/modules/decision-experience/dxl-core.js": FINAL
    / "dashboard/modules/decision-experience/dxl-core.js",
    "dashboard/modules/shared/executive-situation-room/executive-situation-room.css": FINAL
    / "dashboard/modules/shared/executive-situation-room/executive-situation-room.css",
    "tests/e2e/integrity-gate-decision-case.spec.js": FINAL
    / "tests/e2e/integrity-gate-decision-case.spec.js",
    "tests/test_integrity_gate_decision_case.py": FINAL
    / "tests/test_integrity_gate_decision_case.py",
}

# decision-experience.js + index.html are shared IG/SDG — assign carefully:
# C1 gets thin orchestrator changes needed for IG modules; C2 gets SDG wiring.
# Current FINAL decision-experience.js is the thin orchestrator for both → put in C1
# as DXL shell prerequisite, and C2 depends on C1. User said dxl-core is shared;
# spatial-impact in C2. index.html script tags: both need them — put index.html in C1
# with all script tags if FINAL has them, C2 doesn't re-add. OR split: C1 has IG scripts,
# C2 adds SDG scripts. Safest: index.html FINAL in C1 if it only adds script includes
# for the split modules; check later.

C2_FILES = {
    "PROJECT_MANAGEMENT/ARCHITECTURE/SPATIAL_DECISION_GRAPH_V2.md": FINAL
    / "PROJECT_MANAGEMENT/ARCHITECTURE/SPATIAL_DECISION_GRAPH_V2.md",
    "PROJECT_MANAGEMENT/ARCHITECTURE/DXL_MODULE_SPLIT_IG_SDG.md": FINAL
    / "PROJECT_MANAGEMENT/ARCHITECTURE/DXL_MODULE_SPLIT_IG_SDG.md",
    "api/services/spatial_decision_graph_service.py": INTER
    / "c2/api/services/spatial_decision_graph_service.py",
    "dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js": INTER
    / "c2/dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js",
    "dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.css": FINAL
    / "dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.css",
    "dashboard/modules/decision-experience/spatial-impact-controller.js": FINAL
    / "dashboard/modules/decision-experience/spatial-impact-controller.js",
    "dashboard/modules/shared/ux-premium/ux-premium.js": FINAL
    / "dashboard/modules/shared/ux-premium/ux-premium.js",
    "tests/e2e/spatial-decision-graph.spec.js": FINAL
    / "tests/e2e/spatial-decision-graph.spec.js",
    "tests/test_spatial_decision_graph.py": FINAL / "tests/test_spatial_decision_graph.py",
}

C3_FILES = {
    ".cursor/rules/data-first-integration.mdc": FINAL
    / ".cursor/rules/data-first-integration.mdc",
    "PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_POLICY.md": FINAL
    / "PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_POLICY.md",
    "PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_AUDIT_V1.md": INTER
    / "c3/PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_AUDIT_V1.md",
    "PROJECT_MANAGEMENT/ARCHITECTURE/INTEGRITY_GATE_REPORT_V1.md": INTER
    / "c3/PROJECT_MANAGEMENT/ARCHITECTURE/INTEGRITY_GATE_REPORT_V1.md",
}

C4_FILES = {
    "api/services/health_service.py": FINAL / "api/services/health_service.py",
    "api/services/spatial_matching_service.py": FINAL
    / "api/services/spatial_matching_service.py",
    "data/business/spatial_matching_rules.json": FINAL
    / "data/business/spatial_matching_rules.json",
    "api/services/spatial_decision_graph_service.py": INTER
    / "c4/api/services/spatial_decision_graph_service.py",
    "dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js": INTER
    / "c4/dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js",
    "PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_AUDIT_V1.md": INTER
    / "c4/PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_AUDIT_V1.md",
    "PROJECT_MANAGEMENT/ARCHITECTURE/INTEGRITY_GATE_REPORT_V1.md": INTER
    / "c4/PROJECT_MANAGEMENT/ARCHITECTURE/INTEGRITY_GATE_REPORT_V1.md",
}

# Shared orchestrator files: FINAL versions belong primarily to C1 (IG + DXL shell).
# decision-experience.js thin orchestrator loads both — C1.
# index.html script order — C1 includes IG scripts; if SDG script tags present, C2
# must also update index.html. Put FINAL index.html in C1 if it contains both,
# document that C2 depends on C1 for script tags OR put index in C2 only for SDG script.
# Practical: C1 gets index.html + decision-experience.js FINAL (DXL split complete).
C1_FILES[
    "dashboard/modules/decision-experience/decision-experience.js"
] = FINAL / "dashboard/modules/decision-experience/decision-experience.js"
C1_FILES["dashboard/index.html"] = FINAL / "dashboard/index.html"


def build_index(name: str, files: dict[str, Path], base_tree: str | None = None) -> Path:
    index_path = B / f"index-{name}"
    if index_path.exists():
        index_path.unlink()
    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = str(index_path)
    # Start from HEAD tree or empty
    if base_tree:
        r = run(["git", "read-tree", base_tree], env=env)
        if r.returncode != 0:
            raise RuntimeError(r.stderr)
    else:
        r = run(["git", "read-tree", "HEAD"], env=env)
        if r.returncode != 0:
            raise RuntimeError(r.stderr)

    for rel, src in files.items():
        if not src.exists():
            raise FileNotFoundError(f"{name}: missing {src}")
        blob = hash_object(src)
        r = run(
            ["git", "update-index", "--add", "--cacheinfo", f"{mode_for(rel)},{blob},{rel}"],
            env=env,
        )
        if r.returncode != 0:
            raise RuntimeError(f"update-index {rel}: {r.stderr}")

    # Diff vs HEAD for this index
    r = run(["git", "diff", "--cached", "--stat"], env=env)
    stat = r.stdout
    (MANIFEST / f"{name}-cached-stat.txt").write_text(stat, encoding="utf-8")
    r2 = run(["git", "diff", "--cached", "--name-status"], env=env)
    (MANIFEST / f"{name}-name-status.txt").write_text(r2.stdout, encoding="utf-8")
    file_list = "\n".join(sorted(files.keys())) + "\n"
    (MANIFEST / f"{name}-files.txt").write_text(file_list, encoding="utf-8")
    print(f"=== {name} ===")
    print(stat)
    return index_path


def main() -> None:
    write_rules_c2()
    # C2 should NOT include spatial_matching_rules (health radii are C4-only;
    # generic rules unchanged from HEAD for C2 unless we need NEAR already present)
    # Do not add rules to C2 — HEAD already has NEAR_HEALTH_FACILITY.

    build_index("c1", C1_FILES)
    build_index("c2", C2_FILES)
    build_index("c3", C3_FILES)
    build_index("c4", C4_FILES)

    # Manifest summary JSON
    summary = {
        "c1": sorted(C1_FILES),
        "c2": sorted(C2_FILES),
        "c3": sorted(C3_FILES),
        "c4": sorted(C4_FILES),
        "shared_hunks": {
            "spatial_decision_graph_service.py": "C2=generic maturity/SDG; C4=PostGIS health probe+styles+filter",
            "spatial-decision-graph.js": "C2=shell/filters/detail; C4=refresh button+API",
            "DATA_FIRST_INTEGRATION_AUDIT_V1.md": "C3=pre-P0 anomaly; C4=A14 fixed",
            "INTEGRITY_GATE_REPORT_V1.md": "C3=A14 open; C4=A14/A4 fixed",
            "index.html + decision-experience.js": "C1=DXL/IG shell (prerequisite for C2)",
        },
        "excluded_runtime": [
            "data/decision/case_history.json",
            "data/raw/Routes_principales.shp.kmz",
            "data/sectoral/transport/processed/routes_principales.geojson",
            "PROJECT_MANAGEMENT/ARCHITECTURE/captures/",
            ".git-split-backup/",
        ],
    }
    (MANIFEST / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("MANIFESTS_OK")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR", exc, file=sys.stderr)
        sys.exit(1)
