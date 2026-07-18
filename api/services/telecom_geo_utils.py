"""Utilitaires géo / inventaire Fibre-MW neutres — partagés par le livrable FDSU.

Sans dépendance aux moteurs analytiques abandonnés (consolidation physique,
audit KPI fourchettes, KPI 12 289).
"""
from __future__ import annotations

from typing import Any


def coord_key(lat: float, lon: float) -> str:
    """Normalisation d'arrondi source (~6 décimales) — pas une tolérance spatiale métier."""
    return f"{float(lat):.6f}|{float(lon):.6f}"


def inventory_fiber_mw_assets() -> dict[str, Any]:
    """Métriques Fibre / MW séparées du référentiel sites opérateurs mobiles."""
    from api.config import connect_db
    from psycopg2.extras import RealDictCursor

    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT o.operator_code, i.infra_type, COUNT(*)::int AS c
                FROM telecom.infrastructure i
                JOIN telecom.operators o ON o.id = i.operator_id
                WHERE o.operator_code IN ('FIBERCO', 'FTTX')
                GROUP BY 1, 2 ORDER BY 3 DESC
                """
            )
            nodes = [dict(r) for r in cur.fetchall()]
            cur.execute(
                """
                SELECT o.operator_code, COUNT(*)::int AS c
                FROM telecom.infrastructure i
                JOIN telecom.operators o ON o.id = i.operator_id
                WHERE o.operator_code IN ('FIBERCO', 'FTTX')
                GROUP BY 1
                """
            )
            nodes_by_op = {r["operator_code"]: int(r["c"]) for r in cur.fetchall()}
            cur.execute(
                """
                SELECT o.operator_code, l.line_type, l.technology, COUNT(*)::int AS c
                FROM telecom.network_lines l
                JOIN telecom.operators o ON o.id = l.operator_id
                WHERE o.operator_code IN ('FIBERCO', 'FTTX', 'FIBER_MW')
                GROUP BY 1, 2, 3 ORDER BY 4 DESC
                """
            )
            lines = [dict(r) for r in cur.fetchall()]
            cur.execute(
                """
                SELECT o.operator_code, COUNT(*)::int AS c
                FROM telecom.network_lines l
                JOIN telecom.operators o ON o.id = l.operator_id
                WHERE o.operator_code IN ('FIBERCO', 'FTTX', 'FIBER_MW')
                GROUP BY 1
                """
            )
            lines_by_op = {r["operator_code"]: int(r["c"]) for r in cur.fetchall()}
            cur.execute("SELECT COUNT(*)::int AS c FROM telecom.coverage_polygons")
            coverage = int(cur.fetchone()["c"])

    fiber_nodes = sum(nodes_by_op.values())
    fiber_lines = lines_by_op.get("FIBERCO", 0) + lines_by_op.get("FTTX", 0)
    mw_lines = lines_by_op.get("FIBER_MW", 0)
    return {
        "FIBER_NETWORK_ASSETS": {
            "nodes_in_infrastructure": fiber_nodes,
            "nodes_by_operator": nodes_by_op,
            "nodes_by_type": nodes,
            "lines_in_network_lines": fiber_lines,
            "lines_by_operator": {
                "FIBERCO": lines_by_op.get("FIBERCO", 0),
                "FTTX": lines_by_op.get("FTTX", 0),
            },
            "lines_detail": [x for x in lines if x["operator_code"] in {"FIBERCO", "FTTX"}],
            "note": (
                "Nœuds et lignes sont des objets métier distincts — "
                "ne pas les additionner avec des sites opérateurs mobiles."
            ),
        },
        "MICROWAVE_ASSETS": {
            "links_in_network_lines": mw_lines,
            "detail": [x for x in lines if x["operator_code"] == "FIBER_MW"],
            "note": "Liaisons MW (network_lines FIBER_MW) — hors total sites opérateurs.",
        },
        "EXCLUDED_FROM_MOBILE_AND_NOT_SUMMED": {
            "coverage_polygons": coverage,
            "orange_transmission_lines_not_classified_as_mw_kpi": True,
        },
        "TELECOM_PLATFORM_ASSETS": {
            "recommended": False,
            "reason": (
                "Sommer sites opérateurs + nœuds fibre + lignes + MW "
                "n'a pas de sens métier unique."
            ),
        },
    }
