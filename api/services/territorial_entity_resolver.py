"""Resolver territorial canonique — province / territoire / collectivité / groupement / localité."""

from __future__ import annotations

from typing import Any

from psycopg2.extras import RealDictCursor

from api.config import DATA_MODE, connect_db


def _norm(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().lower().replace("-", " ").split())


def _names_match(a: str | None, b: str | None) -> bool:
    na, nb = _norm(a), _norm(b)
    return bool(na and nb and (na == nb or na in nb or nb in na))


def resolve_territory(ref: str | int, *, province: str | None = None) -> dict[str, Any] | None:
    """Résout un territoire depuis ID DB, code, business_id UI ou nom.

    Sortie canonique :
      canonical_id, official_code, name, level, parent, hierarchy, geometry centroid, sources
    """
    token = str(ref or "").strip()
    if not token:
        return None

    # 1) Master registry / nomenclature (codes UI type TERRITOIRE-05-002)
    try:
        from api.services import territorial_intelligence_service as ti

        reg = ti._resolve_territory_ref(token)
        if reg:
            db = _resolve_db_territory(reg.get("territory_name"), province or reg.get("province"))
            return _merge_registry_db(reg, db)
    except Exception:
        pass

    # 2) PostGIS admin
    db = _resolve_db_territory(token, province)
    if db:
        return db

    # 3) Numeric DB id
    if token.isdigit():
        db = _resolve_db_territory_by_id(int(token))
        if db:
            return db
    return None


def _merge_registry_db(reg: dict[str, Any], db: dict[str, Any] | None) -> dict[str, Any]:
    out = {
        "canonical_id": (db or {}).get("canonical_id") or reg.get("territory_id"),
        "official_code": (db or {}).get("official_code") or reg.get("administrative_code"),
        "business_id": reg.get("territory_id"),
        "name": reg.get("territory_name") or (db or {}).get("name"),
        "level": "territoire",
        "parent": {
            "level": "province",
            "name": reg.get("province") or (db or {}).get("province_name"),
            "code": reg.get("province_code"),
        },
        "hierarchy": {
            "province": reg.get("province") or (db or {}).get("province_name"),
            "province_code": reg.get("province_code"),
            "territoire": reg.get("territory_name"),
            "fdsu_zone": reg.get("fdsu_zone"),
        },
        "db_id": (db or {}).get("db_id"),
        "centroid": (db or {}).get("centroid"),
        "has_geometry": bool((db or {}).get("has_geometry")),
        "sources": list(
            dict.fromkeys(
                [reg.get("source") or "master_registry"]
                + ((db or {}).get("sources") or [])
            )
        ),
        "registry": reg,
        "db": db,
    }
    return out


def _resolve_db_territory(name_or_code: str | None, province: str | None = None) -> dict[str, Any] | None:
    if DATA_MODE != "db" or not name_or_code:
        return None
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT t.id, t.code, t.nom, t.parent_id,
                           p.nom AS province_name, p.code AS province_code,
                           t.geom IS NOT NULL AS has_geometry,
                           CASE WHEN t.geom IS NULL THEN NULL ELSE ST_Y(ST_Centroid(t.geom)) END AS lat,
                           CASE WHEN t.geom IS NULL THEN NULL ELSE ST_X(ST_Centroid(t.geom)) END AS lon
                    FROM public.territoires t
                    LEFT JOIN public.provinces p ON p.id = t.parent_id
                    WHERE t.nom ILIKE %s OR t.code ILIKE %s
                    ORDER BY (t.nom ILIKE %s) DESC, t.id
                    LIMIT 20
                    """,
                    (f"%{name_or_code}%", f"%{name_or_code}%", name_or_code),
                )
                rows = [dict(r) for r in cur.fetchall()]
        if not rows:
            return None
        chosen = rows[0]
        if province:
            for r in rows:
                if _names_match(r.get("province_name"), province):
                    chosen = r
                    break
        return {
            "canonical_id": chosen.get("code") or f"DB-TERR-{chosen['id']}",
            "official_code": chosen.get("code"),
            "db_id": chosen["id"],
            "name": chosen.get("nom"),
            "level": "territoire",
            "province_name": chosen.get("province_name"),
            "province_code": chosen.get("province_code"),
            "parent": {"level": "province", "name": chosen.get("province_name"), "code": chosen.get("province_code")},
            "hierarchy": {
                "province": chosen.get("province_name"),
                "province_code": chosen.get("province_code"),
                "territoire": chosen.get("nom"),
            },
            "centroid": {"latitude": chosen.get("lat"), "longitude": chosen.get("lon")}
            if chosen.get("lat") is not None
            else None,
            "has_geometry": bool(chosen.get("has_geometry")),
            "sources": ["public.territoires"],
        }
    except Exception:
        return None


def _resolve_db_territory_by_id(db_id: int) -> dict[str, Any] | None:
    if DATA_MODE != "db":
        return None
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT t.id, t.code, t.nom, p.nom AS province_name, p.code AS province_code,
                           t.geom IS NOT NULL AS has_geometry,
                           CASE WHEN t.geom IS NULL THEN NULL ELSE ST_Y(ST_Centroid(t.geom)) END AS lat,
                           CASE WHEN t.geom IS NULL THEN NULL ELSE ST_X(ST_Centroid(t.geom)) END AS lon
                    FROM public.territoires t
                    LEFT JOIN public.provinces p ON p.id = t.parent_id
                    WHERE t.id = %s
                    """,
                    (db_id,),
                )
                row = cur.fetchone()
        if not row:
            return None
        return _resolve_db_territory(row["nom"], row.get("province_name"))
    except Exception:
        return None
