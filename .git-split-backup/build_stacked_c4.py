#!/usr/bin/env python3
"""Build stacked C4-on-C2 index stats and COMMIT_PLAN.md (no commits)."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = Path(__file__).resolve().parent
FINAL = B / "final"
INTER = B / "intermediate"
MANIFEST = B / "manifests"


def run(cmd, env=None):
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
        raise RuntimeError(r.stderr)
    return r.stdout.strip()


def main() -> None:
    # Build a temporary index = HEAD + C2 files, write tree, then apply C4 on top
    env = os.environ.copy()
    idx = B / "index-stack-base"
    if idx.exists():
        idx.unlink()
    env["GIT_INDEX_FILE"] = str(idx)
    r = run(["git", "read-tree", "HEAD"], env=env)
    assert r.returncode == 0, r.stderr

    c2_overlay = {
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
        "PROJECT_MANAGEMENT/ARCHITECTURE/SPATIAL_DECISION_GRAPH_V2.md": FINAL
        / "PROJECT_MANAGEMENT/ARCHITECTURE/SPATIAL_DECISION_GRAPH_V2.md",
        "PROJECT_MANAGEMENT/ARCHITECTURE/DXL_MODULE_SPLIT_IG_SDG.md": FINAL
        / "PROJECT_MANAGEMENT/ARCHITECTURE/DXL_MODULE_SPLIT_IG_SDG.md",
    }
    for rel, src in c2_overlay.items():
        blob = hash_object(src)
        r = run(
            ["git", "update-index", "--add", "--cacheinfo", f"100644,{blob},{rel}"],
            env=env,
        )
        assert r.returncode == 0, r.stderr

    # Also overlay C3 docs pre-P0 so C4 doc delta is meaningful
    c3_overlay = {
        "PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_AUDIT_V1.md": INTER
        / "c3/PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_AUDIT_V1.md",
        "PROJECT_MANAGEMENT/ARCHITECTURE/INTEGRITY_GATE_REPORT_V1.md": INTER
        / "c3/PROJECT_MANAGEMENT/ARCHITECTURE/INTEGRITY_GATE_REPORT_V1.md",
        ".cursor/rules/data-first-integration.mdc": FINAL
        / ".cursor/rules/data-first-integration.mdc",
        "PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_POLICY.md": FINAL
        / "PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_POLICY.md",
    }
    for rel, src in c3_overlay.items():
        blob = hash_object(src)
        r = run(
            ["git", "update-index", "--add", "--cacheinfo", f"100644,{blob},{rel}"],
            env=env,
        )
        assert r.returncode == 0, r.stderr

    r = run(["git", "write-tree"], env=env)
    assert r.returncode == 0, r.stderr
    base_tree = r.stdout.strip()
    (MANIFEST / "stack-base-tree.txt").write_text(base_tree + "\n", encoding="utf-8")

    # Now C4 delta on that base
    idx4 = B / "index-c4-stacked"
    if idx4.exists():
        idx4.unlink()
    env4 = os.environ.copy()
    env4["GIT_INDEX_FILE"] = str(idx4)
    r = run(["git", "read-tree", base_tree], env=env4)
    assert r.returncode == 0, r.stderr

    c4_files = {
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
    for rel, src in c4_files.items():
        blob = hash_object(src)
        r = run(
            ["git", "update-index", "--add", "--cacheinfo", f"100644,{blob},{rel}"],
            env=env4,
        )
        assert r.returncode == 0, r.stderr

    # Diff stacked index vs base tree
    r = run(["git", "diff", "--cached", "--stat", base_tree], env=env4)
    (MANIFEST / "c4-stacked-on-c2c3-stat.txt").write_text(r.stdout, encoding="utf-8")
    r2 = run(["git", "diff", "--cached", "--name-status", base_tree], env=env4)
    (MANIFEST / "c4-stacked-on-c2c3-name-status.txt").write_text(r2.stdout, encoding="utf-8")
    print("=== c4 stacked on c2+c3 ===")
    print(r.stdout)

    # Also produce unified diffs for shared hunks
    pairs = [
        (
            "spatial_decision_graph_service.py",
            INTER / "c2/api/services/spatial_decision_graph_service.py",
            INTER / "c4/api/services/spatial_decision_graph_service.py",
        ),
        (
            "spatial-decision-graph.js",
            INTER
            / "c2/dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js",
            INTER
            / "c4/dashboard/modules/shared/spatial-decision-graph/spatial-decision-graph.js",
        ),
        (
            "DATA_FIRST_INTEGRATION_AUDIT_V1.md",
            INTER / "c3/PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_AUDIT_V1.md",
            INTER / "c4/PROJECT_MANAGEMENT/ARCHITECTURE/DATA_FIRST_INTEGRATION_AUDIT_V1.md",
        ),
        (
            "INTEGRITY_GATE_REPORT_V1.md",
            INTER / "c3/PROJECT_MANAGEMENT/ARCHITECTURE/INTEGRITY_GATE_REPORT_V1.md",
            INTER / "c4/PROJECT_MANAGEMENT/ARCHITECTURE/INTEGRITY_GATE_REPORT_V1.md",
        ),
    ]
    for label, a, b in pairs:
        r = run(["git", "diff", "--no-index", "--stat", str(a), str(b)])
        # exit 1 is normal for diffs
        (MANIFEST / f"hunk-{label}.stat.txt").write_text(r.stdout or r.stderr, encoding="utf-8")
        r = run(["git", "diff", "--no-index", str(a), str(b)])
        (MANIFEST / f"hunk-{label}.diff").write_text(r.stdout, encoding="utf-8")
        print(f"hunk {label}:", (r.stdout or "").count("\n"), "lines")

    print("STACK_OK")


if __name__ == "__main__":
    main()
