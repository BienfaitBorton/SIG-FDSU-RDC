"""TerritorialProfileService — profil territorial composé (Data First).

Source de vérité partagée pour Intelligence territoriale, TDT, TST, Decision Center.
Chaque bloc est indépendant : une panne Santé n'empêche pas les Groupements.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from psycopg2.extras import RealDictCursor

from api.config import DATA_MODE, connect_db
from api.services.territorial_entity_resolver import resolve_territory, _names_match, _norm

ENGINE_VERSION = "territorial-profile-1.0.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROGRAMS_DIR = PROJECT_ROOT / "data" / "programs"
HIERARCHY_PATH = (
    PROJECT_ROOT / "data" / "reports" / "territory_hierarchy" / "territoires_hierarchie_kmz.report.json"
)

# Statuts Data First obligatoires
ST_OPERATIONAL = "operational"
ST_PARTIAL = "partial"
ST_PENDING = "integration_pending"
ST_ANOMALY = "integration_anomaly"
ST_NA = "not_applicable"
ST_ERROR = "error"

# Alias rétrocompat UI historique
ST_CONFIRMED = "confirmed"
ST_ESTIMATED = "estimated"
ST_UNAVAILABLE = "unavailable"
ST_NOT_SOURCED = "not_sourced"
ST_DEMO = "demonstration"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def indicator(
    value: Any,
    status: str,
    *,
    source: str | None = None,
    note: str | None = None,
    confidence: str | None = None,
    method: str | None = None,
    unit: str | None = None,
    updated_at: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    available = value is not None and status not in {ST_PENDING, ST_ANOMALY, ST_ERROR, ST_NA, ST_UNAVAILABLE, ST_NOT_SOURCED}
    # Compat: operational ≡ confirmed pour consommateurs historiques
    legacy = status
    if status == ST_OPERATIONAL:
        legacy = ST_CONFIRMED
    elif status == ST_PENDING:
        legacy = ST_NOT_SOURCED
    elif status == ST_ANOMALY:
        legacy = ST_UNAVAILABLE
    return {
        "value": value,
        "status": status,
        "legacy_status": legacy,
        "source": source,
        "note": note,
        "confidence": confidence,
        "method": method,
        "unit": unit,
        "updated_at": updated_at or _now(),
        "available": bool(available) if value is not None else False,
        "details": details or {},
    }


def _safe_block(name: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 — résilience par bloc
        return {
            "_error": str(exc),
            "status": ST_ERROR,
            "note": f"Bloc « {name} » en erreur — les autres blocs restent disponibles.",
        }


def _load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _program_sites(program_code: str, territory_name: str) -> list[dict[str, Any]]:
    path = PROGRAMS_DIR / program_code / f"{program_code}.json"
    payload = _load_json(path)
    sites = payload.get("sites") if isinstance(payload, dict) else payload
    if not isinstance(sites, list):
        return []
    return [s for s in sites if _names_match(s.get("territoire"), territory_name)]


def _hierarchy_surface_km2(territory_name: str, province: str | None) -> float | None:
    payload = _load_json(HIERARCHY_PATH)
    for item in payload.get("territories") or []:
        name = item.get("nom") or item.get("name")
        item_province = item.get("province")
        if not _names_match(name, territory_name):
            continue
        if province and item_province and not _names_match(item_province, province):
            continue
        attrs = (item.get("attributs") or {}).get("extended_data") or {}
        surface = attrs.get("SURFACE")
        try:
            return float(surface) if surface not in (None, "") else None
        except (TypeError, ValueError):
            return None
    return None


def _db_admin_counts(db_id: int) -> dict[str, Any]:
    """Règles de rattachement (documentées) :
    1. Collectivités : parent_id = territoire
    2. Groupements : parent collectivité du territoire OU parent_id = territoire OU ST_Within(geom)
    3. Localités : via groupements / collectivités / parent territoire OU ST_Within(geom)
    Priorité spatiale si géométrie valide (évite sous-comptage FK incomplet).
    """
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                  COUNT(*) AS collectivites,
                  COUNT(*) FILTER (WHERE type ILIKE '%%secteur%%') AS secteurs,
                  COUNT(*) FILTER (WHERE type ILIKE '%%chefferie%%') AS chefferies,
                  COUNT(*) FILTER (WHERE type ILIKE '%%cit%%') AS cites
                FROM public.collectivites WHERE parent_id = %s
                """,
                (db_id,),
            )
            coll = dict(cur.fetchone() or {})

            cur.execute(
                """
                SELECT COUNT(DISTINCT g.id) AS n
                FROM public.groupements g
                LEFT JOIN public.collectivites c ON g.parent_id = c.id
                WHERE c.parent_id = %s OR g.parent_id = %s
                """,
                (db_id, db_id),
            )
            grp_fk = int((cur.fetchone() or {}).get("n") or 0)

            cur.execute(
                """
                SELECT COUNT(*) AS n FROM public.groupements g
                JOIN public.territoires t ON t.id = %s
                WHERE g.geom IS NOT NULL AND t.geom IS NOT NULL AND ST_Within(g.geom, t.geom)
                """,
                (db_id,),
            )
            grp_spatial = int((cur.fetchone() or {}).get("n") or 0)

            cur.execute(
                """
                WITH gids AS (
                  SELECT g.id FROM public.groupements g
                  LEFT JOIN public.collectivites c ON g.parent_id = c.id
                  WHERE c.parent_id = %s OR g.parent_id = %s
                ),
                cids AS (SELECT id FROM public.collectivites WHERE parent_id = %s)
                SELECT
                  (SELECT COUNT(DISTINCT l.id) FROM public.localites l JOIN gids ON l.parent_id = gids.id) AS via_grp,
                  (SELECT COUNT(DISTINCT l.id) FROM public.localites l JOIN cids ON l.parent_id = cids.id) AS via_coll,
                  (SELECT COUNT(*) FROM public.localites WHERE parent_id = %s) AS direct_terr
                """,
                (db_id, db_id, db_id, db_id),
            )
            loc_fk = dict(cur.fetchone() or {})
            loc_fk_total = int(loc_fk.get("via_grp") or 0) + int(loc_fk.get("via_coll") or 0) + int(
                loc_fk.get("direct_terr") or 0
            )

            cur.execute(
                """
                SELECT COUNT(*) AS n FROM public.localites l
                JOIN public.territoires t ON t.id = %s
                WHERE l.geom IS NOT NULL AND t.geom IS NOT NULL AND ST_Within(l.geom, t.geom)
                """,
                (db_id,),
            )
            loc_spatial = int((cur.fetchone() or {}).get("n") or 0)

    groupements = max(grp_fk, grp_spatial)
    localites = max(loc_fk_total, loc_spatial)
    method = "spatial_preferred" if (loc_spatial >= loc_fk_total or grp_spatial >= grp_fk) else "hierarchy_fk"
    return {
        "collectivites": int(coll.get("collectivites") or 0),
        "secteurs": int(coll.get("secteurs") or 0),
        "chefferies": int(coll.get("chefferies") or 0),
        "cites": int(coll.get("cites") or 0),
        "groupements": groupements,
        "groupements_fk": grp_fk,
        "groupements_spatial": grp_spatial,
        "localites": localites,
        "localites_fk": loc_fk_total,
        "localites_spatial": loc_spatial,
        "method": method,
        "attachment_rules": [
            "territoire → collectivité → groupement → localité",
            "territoire → groupement direct",
            "territoire → localité directe",
            "collectivité → localité directe",
            "ST_Within(geom, territoire.geom) si géométrie disponible (anti sous-comptage)",
        ],
    }


def _db_area_km2(db_id: int) -> dict[str, Any] | None:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                  ROUND((ST_Area(geom::geography) / 1000000.0)::numeric, 2) AS km2,
                  ST_IsValid(geom) AS is_valid,
                  ST_SRID(geom) AS srid
                FROM public.territoires
                WHERE id = %s AND geom IS NOT NULL
                """,
                (db_id,),
            )
            row = cur.fetchone()
    return dict(row) if row else None


def _db_health(db_id: int) -> dict[str, Any]:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                  COUNT(*) AS total,
                  COUNT(*) FILTER (WHERE f.geom IS NOT NULL) AS with_geom,
                  COUNT(*) FILTER (WHERE UPPER(COALESCE(f.facility_type_code,'')) IN ('HGR','HOSPITAL','CH')) AS hospitals,
                  COUNT(*) FILTER (WHERE UPPER(COALESCE(f.facility_type_code,'')) IN ('CS','CSR','CM','CLINIC','POLYCLINIC')) AS health_centers,
                  COUNT(*) FILTER (WHERE UPPER(COALESCE(f.facility_type_code,'')) IN ('PS','DISP','SSC','MAT')) AS health_posts
                FROM health.health_facilities f
                JOIN public.territoires t ON t.id = %s
                WHERE f.geom IS NOT NULL AND t.geom IS NOT NULL AND ST_Within(f.geom, t.geom)
                """,
                (db_id,),
            )
            agg = dict(cur.fetchone() or {})
            cur.execute(
                """
                SELECT COALESCE(f.facility_type_code, 'OTHER') AS code, COUNT(*) AS n
                FROM health.health_facilities f
                JOIN public.territoires t ON t.id = %s
                WHERE f.geom IS NOT NULL AND ST_Within(f.geom, t.geom)
                GROUP BY 1 ORDER BY n DESC LIMIT 15
                """,
                (db_id,),
            )
            by_type = {r["code"]: int(r["n"]) for r in cur.fetchall()}
    return {**agg, "by_type": by_type, "method": "ST_Within(health.health_facilities, territoires.geom)"}


def _db_telecom(db_id: int) -> dict[str, Any]:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                  COUNT(*) AS total,
                  COUNT(DISTINCT operator_id) AS operators,
                  COUNT(*) FILTER (WHERE infra_type ILIKE '%%fttx%%' OR infra_type ILIKE '%%fibre%%' OR infra_type ILIKE '%%fiber%%') AS fiber_nodes,
                  COUNT(*) FILTER (WHERE infra_type ILIKE '%%radio%%' OR infra_type ILIKE '%%site%%' OR infra_type ILIKE '%%rcs%%') AS radio_sites
                FROM telecom.infrastructure i
                JOIN public.territoires t ON t.id = %s
                WHERE i.geom IS NOT NULL AND t.geom IS NOT NULL AND ST_Intersects(i.geom, t.geom)
                """,
                (db_id,),
            )
            agg = dict(cur.fetchone() or {})
            cur.execute(
                """
                SELECT COALESCE(infra_type, 'OTHER') AS code, COUNT(*) AS n
                FROM telecom.infrastructure i
                JOIN public.territoires t ON t.id = %s
                WHERE i.geom IS NOT NULL AND ST_Intersects(i.geom, t.geom)
                GROUP BY 1 ORDER BY n DESC LIMIT 12
                """,
                (db_id,),
            )
            by_type = {r["code"]: int(r["n"]) for r in cur.fetchall()}
    return {**agg, "by_type": by_type, "method": "ST_Intersects(telecom.infrastructure, territoires.geom)"}


def _db_routes(db_id: int) -> dict[str, Any]:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                  COUNT(*) AS routes_count,
                  COALESCE(SUM(ST_Length(r.geom::geography)) / 1000.0, 0) AS length_km
                FROM transport.routes r
                JOIN public.territoires t ON t.id = %s
                WHERE r.geom IS NOT NULL AND t.geom IS NOT NULL AND ST_Intersects(r.geom, t.geom)
                """,
                (db_id,),
            )
            row = dict(cur.fetchone() or {})
    return {
        "routes_count": int(row.get("routes_count") or 0),
        "length_km": round(float(row.get("length_km") or 0), 2),
        "method": "ST_Intersects(transport.routes, territoires.geom)",
    }


def build_composed_profile(territory_ref: str, *, light: bool = False) -> dict[str, Any] | None:
    entity = resolve_territory(territory_ref)
    if not entity:
        return None

    name = entity.get("name")
    province = (entity.get("hierarchy") or {}).get("province") or (entity.get("parent") or {}).get("name")
    db_id = entity.get("db_id")
    sources: list[str] = list(entity.get("sources") or [])
    section_status: dict[str, str] = {}

    # --- Administrative ---
    def block_admin() -> dict[str, Any]:
        if DATA_MODE != "db" or not db_id:
            return {
                "status": ST_ANOMALY if DATA_MODE != "db" else ST_PENDING,
                "note": "Référentiel administratif PostGIS non accessible pour ce territoire."
                if DATA_MODE != "db"
                else "Territoire non résolu dans public.territoires.",
                "collectivites": indicator(None, ST_ANOMALY if DATA_MODE != "db" else ST_PENDING, source="public.collectivites"),
                "groupements": indicator(None, ST_ANOMALY if DATA_MODE != "db" else ST_PENDING, source="public.groupements"),
                "localites": indicator(None, ST_ANOMALY if DATA_MODE != "db" else ST_PENDING, source="public.localites"),
            }
        counts = _db_admin_counts(int(db_id))
        sources.append("public.territoires/collectivites/groupements/localites")
        partial = counts["localites_fk"] < counts["localites_spatial"] or counts["groupements_fk"] < counts["groupements_spatial"]
        st = ST_PARTIAL if partial else ST_OPERATIONAL
        note = None
        if partial:
            note = (
                f"Comptage spatial prioritaire (localités FK={counts['localites_fk']} / spatial={counts['localites_spatial']}). "
                "Rattachements FK incomplets."
            )
        return {
            "status": st,
            "method": counts["method"],
            "attachment_rules": counts["attachment_rules"],
            "collectivites": indicator(
                counts["collectivites"], st, source="public.collectivites", confidence="high", note=note, method=counts["method"]
            ),
            "secteurs": indicator(counts["secteurs"], st, source="public.collectivites.type", confidence="high"),
            "chefferies": indicator(counts["chefferies"], st, source="public.collectivites.type", confidence="high"),
            "cites": indicator(counts["cites"], st, source="public.collectivites.type", confidence="high"),
            "groupements": indicator(
                counts["groupements"], st, source="public.groupements", confidence="high", note=note, method=counts["method"],
                details={"fk": counts["groupements_fk"], "spatial": counts["groupements_spatial"]},
            ),
            "localites": indicator(
                counts["localites"], st, source="public.localites", confidence="high", note=note, method=counts["method"],
                details={"fk": counts["localites_fk"], "spatial": counts["localites_spatial"]},
            ),
        }

    administrative = _safe_block("administrative", block_admin)
    section_status["administrative"] = administrative.get("status") or ST_ERROR

    # --- Geography ---
    def block_geo() -> dict[str, Any]:
        area_val = None
        area_status = ST_PENDING
        area_source = None
        area_method = None
        area_note = None
        if DATA_MODE == "db" and db_id:
            area = _db_area_km2(int(db_id))
            if area and area.get("km2") is not None:
                area_val = float(area["km2"])
                area_status = ST_OPERATIONAL if area.get("is_valid") else ST_PARTIAL
                area_source = "public.territoires.geom"
                area_method = "ST_Area(geom::geography)/1e6"
                sources.append(area_source)
                if not area.get("is_valid"):
                    area_note = "Géométrie non valide — superficie calculée avec réserve."
        if area_val is None:
            kmz = _hierarchy_surface_km2(name, province)
            if kmz is not None:
                area_val = round(kmz, 2)
                area_status = ST_PARTIAL
                area_source = "territory_hierarchy KMZ SURFACE"
                area_method = "attribut SURFACE (km²)"
                area_note = "Superficie issue du rapport hiérarchie KMZ (pas PostGIS)."
                sources.append(area_source)
        if area_val is None:
            return {
                "status": ST_ANOMALY if entity.get("has_geometry") else ST_PENDING,
                "area_km2": indicator(
                    None,
                    ST_ANOMALY if entity.get("has_geometry") else ST_PENDING,
                    source="public.territoires / hierarchy",
                    note="Géométrie absente ou non calculable."
                    if not entity.get("has_geometry")
                    else "Anomalie — géométrie attendue mais superficie non calculée.",
                ),
                "density": indicator(None, ST_PENDING, note="Densité non calculable sans superficie."),
            }
        return {
            "status": area_status,
            "area_km2": indicator(
                area_val, area_status, source=area_source, method=area_method, note=area_note, unit="km²", confidence="high"
            ),
            "density": indicator(None, ST_PENDING, note="Densité renseignée après population."),
        }

    geography = _safe_block("geography", block_geo)
    section_status["geography"] = geography.get("status") or ST_ERROR

    # --- Population ---
    def block_population() -> dict[str, Any]:
        sites = _program_sites("sites_20476", name) or _program_sites("sites_300", name) or _program_sites("sites_40", name)
        pops = [int(s["population"]) for s in sites if s.get("population") not in (None, "")]
        # NCI coverage population if available
        nci_pop = None
        try:
            from api.services import coverage_intelligence_service as nci

            cov = nci.get_territory_coverage(name) or {}
            row = cov.get("territory") or {}
            covered = row.get("population_covered")
            uncovered = row.get("population_uncovered")
            if covered is not None or uncovered is not None:
                nci_pop = int(covered or 0) + int(uncovered or 0)
                sources.append("data/coverage/aggregates.json")
        except Exception:
            pass

        if nci_pop:
            val = nci_pop
            st = ST_PARTIAL
            src = "NCI aggregates (covered+uncovered)"
            note = "Population estimée NCI (couverte + non couverte) — pas un recensement officiel."
            conf = "medium"
        elif pops:
            val = sum(pops)
            st = ST_PARTIAL
            src = "programmes sites (somme)"
            note = "Somme des populations des sites programme — pas un recensement territorial officiel."
            conf = "low"
            sources.append("data/programs/sites_*")
        else:
            return {
                "status": ST_PENDING,
                "total": indicator(None, ST_PENDING, note="Population territoriale officielle absente."),
            }
        # density if area known
        dens = None
        dens_ind = geography.get("density")
        area_ind = geography.get("area_km2") or {}
        if area_ind.get("value") and val:
            dens = round(float(val) / float(area_ind["value"]), 2)
            geography["density"] = indicator(
                dens,
                ST_PARTIAL,
                source=f"{src} / {area_ind.get('source')}",
                method="population / area_km2",
                unit="hab/km²",
                confidence=conf,
                note="Densité estimée (population partielle).",
            )
        return {
            "status": st,
            "total": indicator(val, st, source=src, note=note, confidence=conf),
            "nci_total": nci_pop,
            "sites_sum": sum(pops) if pops else None,
        }

    population = _safe_block("population", block_population)
    section_status["population"] = population.get("status") or ST_ERROR

    # --- Health ---
    def block_health() -> dict[str, Any]:
        if DATA_MODE != "db":
            return {
                "status": ST_ANOMALY,
                "total": indicator(None, ST_ANOMALY, source="health.health_facilities", note="DATA_MODE≠db — référentiel Santé non interrogé."),
            }
        if not db_id:
            return {
                "status": ST_ANOMALY,
                "total": indicator(
                    None,
                    ST_ANOMALY,
                    source="health.health_facilities",
                    note="Anomalie — référentiel Santé présent mais territoire sans geom DB pour intersection spatiale.",
                ),
            }
        h = _db_health(int(db_id))
        total = int(h.get("total") or 0)
        sources.append("health.health_facilities")
        st = ST_OPERATIONAL if total >= 0 else ST_ERROR
        note = None
        if total == 0:
            note = "Recherche spatiale exécutée sur health.health_facilities : aucun établissement dans le polygone territorial."
            st = ST_OPERATIONAL  # vrai zéro
        elif int(h.get("hospitals") or 0) + int(h.get("health_centers") or 0) + int(h.get("health_posts") or 0) == 0:
            note = "Établissements trouvés — typologie métier (HGR/CS/PS) peu renseignée (codes OTHER)."
            st = ST_PARTIAL
        return {
            "status": st,
            "total": indicator(total, st, source="health.health_facilities", method=h.get("method"), confidence="high", note=note),
            "hospitals": indicator(int(h.get("hospitals") or 0), st, source="health.health_facilities"),
            "health_centers": indicator(int(h.get("health_centers") or 0), st, source="health.health_facilities"),
            "health_posts": indicator(int(h.get("health_posts") or 0), st, source="health.health_facilities"),
            "with_geometry": indicator(int(h.get("with_geom") or 0), ST_OPERATIONAL, source="health.health_facilities"),
            "by_type": h.get("by_type") or {},
        }

    health = _safe_block("health", block_health) if not light else {"status": ST_PENDING, "total": indicator(None, ST_PENDING)}
    if not light:
        section_status["health"] = health.get("status") or ST_ERROR

    # --- Telecom / Fiber ---
    def block_telecom() -> dict[str, Any]:
        if DATA_MODE != "db" or not db_id:
            return {
                "status": ST_ANOMALY if DATA_MODE == "db" else ST_ANOMALY,
                "infrastructures": indicator(None, ST_ANOMALY, source="telecom.infrastructure", note="Requête spatiale non exécutable."),
                "fiber_nodes": indicator(None, ST_ANOMALY, source="telecom.infrastructure"),
            }
        t = _db_telecom(int(db_id))
        sources.append("telecom.infrastructure")
        total = int(t.get("total") or 0)
        fiber = int(t.get("fiber_nodes") or 0)
        st = ST_OPERATIONAL if total >= 0 else ST_ERROR
        return {
            "status": st,
            "infrastructures": indicator(total, st, source="telecom.infrastructure", method=t.get("method"), confidence="high"),
            "operators": indicator(int(t.get("operators") or 0), ST_PARTIAL, source="telecom.infrastructure.operator_id", confidence="medium"),
            "radio_sites": indicator(int(t.get("radio_sites") or 0), st, source="telecom.infrastructure"),
            "fiber_nodes": indicator(
                fiber,
                ST_OPERATIONAL if fiber >= 0 else ST_ERROR,
                source="telecom.infrastructure (fttx/fibre)",
                note="Nœuds fibre / FTTX intersectant le territoire — pas de table fibre dédiée.",
                confidence="medium",
            ),
            "by_type": t.get("by_type") or {},
        }

    telecom = _safe_block("telecom", block_telecom) if not light else {"status": ST_PENDING}
    fiber = {
        "status": (telecom.get("status") if isinstance(telecom, dict) else ST_ERROR),
        "nodes": (telecom.get("fiber_nodes") if isinstance(telecom, dict) else indicator(None, ST_ERROR)),
        "length_km": indicator(
            None,
            ST_PENDING,
            source=None,
            note="En cours d’intégration — longueur de fibre territoriale absente (pas de référentiel linéaire fibre).",
        ),
        "note": "Fibre approximée via nœuds FTTX dans telecom.infrastructure.",
    }
    if not light:
        section_status["telecom"] = telecom.get("status") or ST_ERROR
        section_status["fiber"] = fiber.get("status") or ST_PENDING

    # --- Transport ---
    def block_transport() -> dict[str, Any]:
        if DATA_MODE != "db" or not db_id:
            return {
                "status": ST_ANOMALY,
                "routes": indicator(None, ST_ANOMALY, source="transport.routes"),
            }
        r = _db_routes(int(db_id))
        sources.append("transport.routes")
        st = ST_OPERATIONAL
        return {
            "status": st,
            "routes": indicator(r["routes_count"], st, source="transport.routes", method=r["method"], confidence="high"),
            "length_km": indicator(r["length_km"], st, source="transport.routes", unit="km", method=r["method"], confidence="high"),
        }

    transport = _safe_block("transport", block_transport) if not light else {"status": ST_PENDING}
    if not light:
        section_status["transport"] = transport.get("status") or ST_ERROR

    # --- Programs ---
    def block_programs() -> dict[str, Any]:
        s40 = _program_sites("sites_40", name)
        s300 = _program_sites("sites_300", name)
        s20476 = _program_sites("sites_20476", name)
        sources.append("data/programs/sites_*")
        scored = []
        if not light:
            try:
                from api.services import fdsu_site_priority_service

                for site in (s20476 or s300 or s40)[:200]:
                    try:
                        scored.append(fdsu_site_priority_service.compute_national_site_score(site))
                    except Exception:
                        continue
                scored.sort(key=lambda s: (-float(s.get("priority_score") or 0), str(s.get("site_name") or "")))
            except Exception:
                scored = []
        avg = round(sum(float(s["priority_score"]) for s in scored) / len(scored), 1) if scored else None
        top = scored[0].get("priority_level") if scored else None
        statuses = {}
        for label, rows in (("sites_40", s40), ("sites_300", s300), ("sites_20476", s20476)):
            # extract operational statuses if present
            st_vals = [str(s.get("status") or s.get("operational_status") or "").strip() for s in rows if s.get("status") or s.get("operational_status")]
            statuses[label] = {v: st_vals.count(v) for v in set(st_vals) if v}
        return {
            "status": ST_OPERATIONAL,
            "sites_40": indicator(len(s40), ST_OPERATIONAL, source="data/programs/sites_40", confidence="high", details={"statuses": statuses.get("sites_40")}),
            "sites_300": indicator(len(s300), ST_OPERATIONAL, source="data/programs/sites_300", confidence="high", details={"statuses": statuses.get("sites_300")}),
            "sites_20476": indicator(len(s20476), ST_OPERATIONAL, source="data/programs/sites_20476", confidence="high", details={"statuses": statuses.get("sites_20476")}),
            "priority_score": indicator(avg, ST_ESTIMATED if avg is not None else ST_PENDING, source="fdsu_site_priority_service", confidence="medium"),
            "priority_level": indicator(top, ST_ESTIMATED if top else ST_PENDING, source="top site scoré"),
            "scored_sample_size": len(scored),
        }

    programs = _safe_block("programs", block_programs)
    section_status["programs"] = programs.get("status") or ST_ERROR

    # --- CCN ---
    def block_ccn() -> dict[str, Any]:
        try:
            from api.services import ccn_operational_service

            listed = ccn_operational_service.list_ccn(territoire=name, province=province, limit=200)
            items = listed.get("ccn") or []
            if not items:
                listed = ccn_operational_service.list_ccn(territoire=name, limit=200)
                items = listed.get("ccn") or []
            data_class = (listed.get("_meta") or {}).get("data_class") or "DEMO"
            sources.append("data/programs/ccn/demo_ccn.json")
            if items:
                return {
                    "status": ST_DEMO,
                    "count": indicator(
                        len(items),
                        ST_DEMO,
                        source="/api/ccn (DEMO)",
                        note=f"Jeu CCN {data_class} — pas une base de production nationale.",
                        confidence="low",
                        details={"data_class": data_class},
                    ),
                    "data_class": data_class,
                }
            return {
                "status": ST_OPERATIONAL,
                "count": indicator(
                    0,
                    ST_OPERATIONAL,
                    source="/api/ccn (DEMO)",
                    note="Recherche exécutée sur le jeu CCN DEMO : aucun CCN pour ce territoire. Pas de référentiel CCN production.",
                    confidence="medium",
                    details={"data_class": data_class, "production_available": False},
                ),
                "data_class": data_class,
            }
        except Exception as exc:
            return {
                "status": ST_ERROR,
                "count": indicator(None, ST_ERROR, note=str(exc), source="/api/ccn"),
            }

    ccn = _safe_block("ccn", block_ccn) if not light else {"status": ST_PENDING}
    if not light:
        section_status["ccn"] = ccn.get("status") or ST_ERROR

    # --- Coverage / Needs ---
    def block_coverage() -> dict[str, Any]:
        try:
            from api.services import coverage_intelligence_service as nci

            payload = nci.get_territory_coverage(name)
            if not payload:
                return {
                    "status": ST_PENDING,
                    "note": "Territoire absent du Référentiel National des Besoins (NCI).",
                    "localities_uncovered": indicator(None, ST_PENDING, source="NCI"),
                }
            row = payload.get("territory") or {}
            sources.append("data/coverage/aggregates.json")
            return {
                "status": ST_OPERATIONAL,
                "localities_covered": indicator(row.get("localities_covered"), ST_OPERATIONAL, source="NCI"),
                "localities_uncovered": indicator(row.get("localities_uncovered"), ST_OPERATIONAL, source="NCI"),
                "population_covered": indicator(row.get("population_covered"), ST_OPERATIONAL, source="NCI"),
                "population_uncovered": indicator(row.get("population_uncovered"), ST_OPERATIONAL, source="NCI"),
                "ndci": indicator((row.get("ndci") or {}).get("index"), ST_OPERATIONAL, source="NCI"),
            }
        except Exception as exc:
            return {"status": ST_ERROR, "note": str(exc)}

    coverage = _safe_block("coverage", block_coverage)
    section_status["coverage"] = coverage.get("status") or ST_ERROR

    # Education etc. — réellement absents
    education = {
        "status": ST_PENDING,
        "schools": indicator(
            None,
            ST_PENDING,
            note="En cours d’intégration — amélioration future de l’analyse des bénéficiaires scolaires.",
        ),
    }
    section_status["education"] = ST_PENDING

    # Quality / confidence
    anomaly_count = sum(1 for s in section_status.values() if s == ST_ANOMALY)
    pending_count = sum(1 for s in section_status.values() if s == ST_PENDING)
    confidence = "high"
    if anomaly_count or pending_count >= 4:
        confidence = "low"
    elif pending_count or any(s == ST_PARTIAL for s in section_status.values()):
        confidence = "medium"

    return {
        "_meta": {
            "engine": ENGINE_VERSION,
            "generated_at": _now(),
            "data_mode": DATA_MODE,
            "principle": "Data First — aucune valeur inventée ; blocs indépendants et résilients",
        },
        "entity": entity,
        "administrative": administrative,
        "population": population,
        "geography": geography,
        "health": health,
        "telecom": telecom,
        "fiber": fiber,
        "transport": transport,
        "programs": programs,
        "ccn": ccn,
        "coverage": coverage,
        "needs": coverage,
        "education": education,
        "decision": {
            "priority_score": programs.get("priority_score") if isinstance(programs, dict) else None,
            "priority_level": programs.get("priority_level") if isinstance(programs, dict) else None,
        },
        "quality": {
            "confidence_level": confidence,
            "anomaly_count": anomaly_count,
            "pending_count": pending_count,
        },
        "sources": list(dict.fromkeys([s for s in sources if s])),
        "section_status": section_status,
    }


def to_territorial_intelligence_profile(composed: dict[str, Any]) -> dict[str, Any]:
    """Adapte le profil composé vers le contrat historique TI (sections.*)."""
    entity = composed.get("entity") or {}
    admin = composed.get("administrative") or {}
    pop = composed.get("population") or {}
    geo = composed.get("geography") or {}
    health = composed.get("health") or {}
    telecom = composed.get("telecom") or {}
    fiber = composed.get("fiber") or {}
    transport = composed.get("transport") or {}
    programs = composed.get("programs") or {}
    ccn = composed.get("ccn") or {}
    coverage = composed.get("coverage") or {}
    education = composed.get("education") or {}
    quality = composed.get("quality") or {}

    def as_field(ind: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(ind, dict):
            return indicator(None, ST_PENDING, note="Non calculé")
        # Prefer legacy_status for old UI badges, keep status as Data First
        return {
            "value": ind.get("value"),
            "status": ind.get("status") or ind.get("legacy_status") or ST_PENDING,
            "source": ind.get("source"),
            "note": ind.get("note"),
            "confidence": ind.get("confidence"),
            "method": ind.get("method"),
            "updated_at": ind.get("updated_at"),
            "available": ind.get("available"),
            "details": ind.get("details") or {},
            "unit": ind.get("unit"),
        }

    pop_total = as_field(pop.get("total"))
    area = as_field(geo.get("area_km2"))
    dens = as_field(geo.get("density"))
    locs = as_field(admin.get("localites"))
    grps = as_field(admin.get("groupements"))
    health_total = as_field(health.get("total"))
    tel = as_field(telecom.get("infrastructures"))
    fib = as_field(fiber.get("nodes") if isinstance(fiber.get("nodes"), dict) else fiber.get("nodes"))
    routes = as_field(transport.get("routes"))
    routes_km = as_field(transport.get("length_km"))

    gaps = []
    for key, ind in (
        ("population_officielle", pop_total),
        ("area_km2", area),
        ("education", as_field(education.get("schools"))),
    ):
        if ind.get("status") in {ST_PENDING, ST_ANOMALY, ST_ERROR}:
            gaps.append(key)

    hierarchy = entity.get("hierarchy") or {}
    profile = {
        "territory_id": entity.get("business_id") or entity.get("canonical_id"),
        "territory_name": entity.get("name"),
        "province": hierarchy.get("province"),
        "fdsu_zone": hierarchy.get("fdsu_zone"),
        "administrative_code": entity.get("official_code"),
        "province_code": hierarchy.get("province_code"),
        "population": pop_total,
        "area_km2": area,
        "density": dens,
        "localities_count": locs,
        "groupements_count": grps,
        "collectivites_count": as_field(admin.get("collectivites")),
        "data_quality": "partial" if gaps else "good",
        "confidence_level": quality.get("confidence_level") or "medium",
        "last_updated": _now(),
        "sources": composed.get("sources") or [],
        "is_demo_focus": _norm(entity.get("name")) == "dungu",
        "engine_version": ENGINE_VERSION,
        "section_status": composed.get("section_status") or {},
        "composed_engine": composed.get("_meta"),
    }

    sections = {
        "synthesis": {
            "province": indicator(hierarchy.get("province"), ST_OPERATIONAL, source="master_registry / public.provinces"),
            "fdsu_zone": indicator(hierarchy.get("fdsu_zone"), ST_OPERATIONAL if hierarchy.get("fdsu_zone") else ST_PARTIAL, source="nomenclature FDSU"),
            "population": pop_total,
            "area_km2": area,
            "density": dens,
            "localities": locs,
            "groupements": grps,
            "collectivites": as_field(admin.get("collectivites")),
            "chefferies": as_field(admin.get("chefferies")),
            "secteurs": as_field(admin.get("secteurs")),
            "administrative_code": indicator(entity.get("official_code"), ST_OPERATIONAL, source="public.territoires / registry"),
        },
        "digital": {
            "infrastructures_telecom": tel,
            "fibre": fib,
            "backbone": indicator(None, ST_PENDING, note="En cours d’intégration — backbone territorial non agrégé."),
            "operateurs_presents": as_field(telecom.get("operators")),
            "sites_fdsu_presents": {
                "sites_40": as_field(programs.get("sites_40")),
                "sites_300": as_field(programs.get("sites_300")),
                "sites_20476": as_field(programs.get("sites_20476")),
            },
            "ccn_presents_ou_proposes": as_field(ccn.get("count")),
            "couverture_disponible": as_field(coverage.get("ndci")),
        },
        "public_services": {
            "etablissements_sante": health_total,
            "sante_hopitaux": as_field(health.get("hospitals")),
            "sante_centres": as_field(health.get("health_centers")),
            "sante_postes": as_field(health.get("health_posts")),
            "sante_by_type": health.get("by_type") or {},
            "ecoles": as_field(education.get("schools")),
            "administrations": indicator(None, ST_PENDING, note="En cours d’intégration — référentiel administrations."),
            "marches": indicator(None, ST_PENDING, note="En cours d’intégration — référentiel marchés."),
        },
        "accessibility": {
            "routes": routes,
            "routes_length_km": routes_km,
            "aerodromes": indicator(None, ST_PENDING, note="En cours d’intégration — aérodromes."),
        },
        "economy": {
            "agriculture": indicator(None, ST_PENDING, note="En cours d’intégration — agriculture."),
        },
        "energy": {
            "disponibilite": indicator(None, ST_PENDING, note="En cours d’intégration — énergie."),
        },
        "programs": {
            "sites_40": as_field(programs.get("sites_40")),
            "sites_300": as_field(programs.get("sites_300")),
            "sites_20476": as_field(programs.get("sites_20476")),
            "ccn": as_field(ccn.get("count")),
            "autres": indicator(None, ST_PENDING, note="En cours d’intégration."),
        },
        "coverage": coverage,
        "priority": {
            "score": as_field(programs.get("priority_score")),
            "level": as_field(programs.get("priority_level")),
        },
        "opportunities": {"items": []},
        "risks": {"items": []},
    }

    return {
        "_meta": {
            "title": f"Profil Territorial FDSU — {entity.get('name')}",
            "engine_version": ENGINE_VERSION,
            "composed": True,
            "generated_at": _now(),
        },
        "profile": profile,
        "sections": sections,
        "data_gaps": gaps,
        "composed": composed,
        "spatial_matching": {"available": False},
    }
