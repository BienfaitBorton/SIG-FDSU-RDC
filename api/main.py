import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
import psycopg2
from psycopg2.extras import RealDictCursor

from api.config import DATA_MODE, connect_db
from api.middlewares.exceptions import (
    sqlalchemy_integrity_error_handler,
    value_error_handler,
)
from api.routes import (
    provinces,
    territoires,
    collectivites,
    groupements,
    villages,
    sites,
    missions,
    documents,
    photos,
    imports,
    decision,
    territorial_enrichment,
    enrichment,
    knowledge,
)
from app.fdsu_nomenclature import enrich_entity, load_nomenclature

app = FastAPI(
    title="SIG-FDSU RDC - API SIG",
    description=(
        "API FastAPI de gestion du référentiel administratif et des sites du projet "
        "FDSU en République démocratique du Congo. Fournit des opérations CRUD "
        "pour les provinces, territoires, collectivités, groupements, villages, sites, missions, documents et photos."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(IntegrityError, sqlalchemy_integrity_error_handler)
app.add_exception_handler(ValueError, value_error_handler)


@app.middleware("http")
async def enforce_utf8_content_type(request, call_next):
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if content_type == "application/json":
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response


geodata_dir = Path(__file__).resolve().parent.parent / "data" / "generated"
app.mount("/geodata", StaticFiles(directory=geodata_dir), name="geodata")

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "data" / "reports"
DB_TABLES = {
    "zones": "zones",
    "provinces": "provinces",
    "territoires": "territoires",
    "territories": "territoires",
    "villes": "villes",
    "collectivites": "collectivites",
    "groupements": "groupements",
    "localites": "localites",
    "villages": "localites",
    "sites": "sites",
    "missions": "missions",
}


def use_database() -> bool:
    return DATA_MODE == "db"


def db_fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]


def db_fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = db_fetch_all(query, params)
    return rows[0] if rows else None


def db_entity_rows(table: str, skip: int = 0, limit: int = 500) -> list[dict[str, Any]]:
    parent_selects = {
        "zones": """
            SELECT z.id, z.code, z.nom, z.type, z.parent_id, z.latitude, z.longitude, z.source,
                   z.quality_score AS qualite, z.status AS statut, z.metadata,
                   z.code AS zone_fdsu,
                   CASE WHEN z.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(z.geom)::json END AS geometry
            FROM zones z
        """,
        "provinces": """
            SELECT p.id, p.code, p.nom, p.type, p.parent_id, p.latitude, p.longitude, p.source,
                   p.quality_score AS qualite, p.status AS statut, p.metadata,
                   z.code AS zone_fdsu,
                   CASE WHEN p.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(p.geom)::json END AS geometry
            FROM provinces p
            LEFT JOIN zones z ON z.id = p.parent_id
        """,
        "territoires": """
            SELECT t.id, t.code, t.nom, t.type, t.parent_id, t.latitude, t.longitude, t.source,
                   t.quality_score AS qualite, t.status AS statut, t.metadata,
                   p.nom AS province, z.code AS zone_fdsu,
                   CASE WHEN t.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(t.geom)::json END AS geometry
            FROM territoires t
            LEFT JOIN provinces p ON p.id = t.parent_id
            LEFT JOIN zones z ON z.id = p.parent_id
        """,
        "villes": """
            SELECT v.id, v.code, v.nom, v.type, v.parent_id, v.latitude, v.longitude, v.source,
                   v.quality_score AS qualite, v.status AS statut, v.metadata,
                   p.nom AS province, z.code AS zone_fdsu,
                   CASE WHEN v.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(v.geom)::json END AS geometry
            FROM villes v
            LEFT JOIN provinces p ON p.id = v.parent_id
            LEFT JOIN zones z ON z.id = p.parent_id
        """,
        "collectivites": """
            SELECT c.id, c.code, c.nom, c.type, c.parent_id, c.latitude, c.longitude, c.source,
                   c.quality_score AS qualite, c.status AS statut, c.metadata,
                   t.nom AS territoire, p.nom AS province, z.code AS zone_fdsu,
                   CASE WHEN c.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(c.geom)::json END AS geometry
            FROM collectivites c
            LEFT JOIN territoires t ON t.id = c.parent_id
            LEFT JOIN provinces p ON p.id = t.parent_id
            LEFT JOIN zones z ON z.id = p.parent_id
        """,
        "groupements": """
            SELECT g.id, g.code, g.nom, g.type, g.parent_id, g.latitude, g.longitude, g.source,
                   g.quality_score AS qualite, g.status AS statut, g.metadata,
                   c.nom AS collectivite, t.nom AS territoire, p.nom AS province, z.code AS zone_fdsu,
                   CASE WHEN g.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(g.geom)::json END AS geometry
            FROM groupements g
            LEFT JOIN collectivites c ON c.id = g.parent_id
            LEFT JOIN territoires t ON t.id = c.parent_id
            LEFT JOIN provinces p ON p.id = t.parent_id
            LEFT JOIN zones z ON z.id = p.parent_id
        """,
        "localites": """
            SELECT l.id, l.code, l.nom, l.type, l.parent_id, l.latitude, l.longitude, l.source,
                   l.quality_score AS qualite, l.status AS statut, l.metadata,
                   g.nom AS groupement, c.nom AS collectivite, t.nom AS territoire, p.nom AS province, z.code AS zone_fdsu,
                   CASE WHEN l.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(l.geom)::json END AS geometry
            FROM localites l
            LEFT JOIN groupements g ON g.id = l.parent_id
            LEFT JOIN collectivites c ON c.id = g.parent_id
            LEFT JOIN territoires t ON t.id = c.parent_id
            LEFT JOIN provinces p ON p.id = t.parent_id
            LEFT JOIN zones z ON z.id = p.parent_id
        """,
        "sites": """
            SELECT s.id, s.code, s.nom, s.type, s.parent_id, s.latitude, s.longitude, s.source,
                   s.quality_score AS qualite, s.status AS statut, s.metadata,
                   l.nom AS localite,
                   CASE WHEN s.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(s.geom)::json END AS geometry
            FROM sites s
            LEFT JOIN localites l ON l.id = s.parent_id
        """,
        "missions": """
            SELECT m.id, m.code, m.nom, m.type, m.parent_id, m.latitude, m.longitude, m.source,
                   m.quality_score AS qualite, m.status AS statut, m.metadata,
                   s.nom AS site,
                   CASE WHEN m.geom IS NULL THEN NULL ELSE ST_AsGeoJSON(m.geom)::json END AS geometry
            FROM missions m
            LEFT JOIN sites s ON s.id = m.parent_id
        """,
    }
    base_query = parent_selects.get(table)
    if base_query:
        return [enrich_entity(row) for row in db_fetch_all(f"{base_query} ORDER BY nom OFFSET %s LIMIT %s", (skip, limit))]

    return [enrich_entity(row) for row in db_fetch_all(
        f"""
        SELECT
            id, code, nom, type, parent_id, latitude, longitude, source,
            quality_score AS qualite, status AS statut, metadata,
            CASE WHEN geom IS NULL THEN NULL ELSE ST_AsGeoJSON(geom)::json END AS geometry
        FROM {table}
        ORDER BY nom
        OFFSET %s LIMIT %s
        """,
        (skip, limit),
    )]


def db_count(table: str) -> int:
    row = db_fetch_one(f"SELECT count(*)::int AS count FROM {table}")
    return int(row["count"]) if row else 0


def db_table_exists(table: str) -> bool:
    row = db_fetch_one("SELECT to_regclass(%s) IS NOT NULL AS exists", (f"public.{table}",))
    return bool(row and row.get("exists"))


def db_scalar_count(query: str, params: tuple[Any, ...]) -> int:
    row = db_fetch_one(query, params)
    return int(row["count"]) if row and row.get("count") is not None else 0


def db_relation_count(table: str, query: str, entity_id: int) -> int | None:
    if not db_table_exists(table):
        return None
    return db_scalar_count(query, (entity_id,))


def db_localite_services(localite_id: int) -> dict[str, Any] | None:
    if not db_table_exists("public_services"):
        return None
    row = db_fetch_one(
        """
        SELECT centre_sante, ecole_primaire, ecole_secondaire, marche, electricite, source, observation
        FROM public_services
        WHERE localite_id = %s
        ORDER BY updated_at DESC NULLS LAST, id DESC
        LIMIT 1
        """,
        (localite_id,),
    )
    return row or None


def db_localite_connectivity(localite_id: int) -> dict[str, Any] | None:
    if not db_table_exists("connectivity_profiles"):
        return None
    row = db_fetch_one(
        """
        SELECT couverture_2g, couverture_3g, couverture_4g, couverture_5g,
               score_connectivite, source, observation
        FROM connectivity_profiles
        WHERE localite_id = %s
        ORDER BY updated_at DESC NULLS LAST, id DESC
        LIMIT 1
        """,
        (localite_id,),
    )
    return row or None


def db_relation_stats(table: str, entity_id: int) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    relation_links: list[dict[str, str]] = []

    def set_count(key: str, source_table: str, query: str, target_layer: str | None = None) -> None:
        count = db_relation_count(source_table, query, entity_id)
        if count is None:
            return
        stats[key] = count
        if target_layer:
            relation_links.append({"key": key, "layer": target_layer})

    if table == "provinces":
        set_count("territoires", "territoires", "SELECT count(*)::int AS count FROM territoires WHERE parent_id = %s", "territoires")
        set_count("villes", "villes", "SELECT count(*)::int AS count FROM villes WHERE parent_id = %s")
        set_count("collectivites", "collectivites", """
            SELECT count(*)::int AS count
            FROM collectivites c
            JOIN territoires t ON t.id = c.parent_id
            WHERE t.parent_id = %s
        """, "collectivites")
        set_count("groupements", "groupements", """
            SELECT count(*)::int AS count
            FROM groupements g
            JOIN collectivites c ON c.id = g.parent_id
            JOIN territoires t ON t.id = c.parent_id
            WHERE t.parent_id = %s
        """, "groupements")
        set_count("localites", "localites", """
            SELECT count(*)::int AS count
            FROM localites l
            JOIN groupements g ON g.id = l.parent_id
            JOIN collectivites c ON c.id = g.parent_id
            JOIN territoires t ON t.id = c.parent_id
            WHERE t.parent_id = %s
        """, "localites")
        set_count("sites", "sites", """
            SELECT count(*)::int AS count
            FROM sites s
            JOIN localites l ON l.id = s.parent_id
            JOIN groupements g ON g.id = l.parent_id
            JOIN collectivites c ON c.id = g.parent_id
            JOIN territoires t ON t.id = c.parent_id
            WHERE t.parent_id = %s
        """)
        set_count("missions", "missions", """
            SELECT count(*)::int AS count
            FROM missions m
            JOIN sites s ON s.id = m.parent_id
            JOIN localites l ON l.id = s.parent_id
            JOIN groupements g ON g.id = l.parent_id
            JOIN collectivites c ON c.id = g.parent_id
            JOIN territoires t ON t.id = c.parent_id
            WHERE t.parent_id = %s
        """)
    elif table == "territoires":
        set_count("collectivites", "collectivites", "SELECT count(*)::int AS count FROM collectivites WHERE parent_id = %s", "collectivites")
        set_count("groupements", "groupements", """
            SELECT count(*)::int AS count
            FROM groupements g
            JOIN collectivites c ON c.id = g.parent_id
            WHERE c.parent_id = %s
        """, "groupements")
        set_count("localites", "localites", """
            SELECT count(*)::int AS count
            FROM localites l
            JOIN groupements g ON g.id = l.parent_id
            JOIN collectivites c ON c.id = g.parent_id
            WHERE c.parent_id = %s
        """, "localites")
        set_count("sites", "sites", """
            SELECT count(*)::int AS count
            FROM sites s
            JOIN localites l ON l.id = s.parent_id
            JOIN groupements g ON g.id = l.parent_id
            JOIN collectivites c ON c.id = g.parent_id
            WHERE c.parent_id = %s
        """)
        set_count("missions", "missions", """
            SELECT count(*)::int AS count
            FROM missions m
            JOIN sites s ON s.id = m.parent_id
            JOIN localites l ON l.id = s.parent_id
            JOIN groupements g ON g.id = l.parent_id
            JOIN collectivites c ON c.id = g.parent_id
            WHERE c.parent_id = %s
        """)
    elif table == "collectivites":
        set_count("groupements", "groupements", "SELECT count(*)::int AS count FROM groupements WHERE parent_id = %s", "groupements")
        set_count("localites", "localites", """
            SELECT count(*)::int AS count
            FROM localites l
            JOIN groupements g ON g.id = l.parent_id
            WHERE g.parent_id = %s
        """, "localites")
        set_count("sites", "sites", """
            SELECT count(*)::int AS count
            FROM sites s
            JOIN localites l ON l.id = s.parent_id
            JOIN groupements g ON g.id = l.parent_id
            WHERE g.parent_id = %s
        """)
        set_count("missions", "missions", """
            SELECT count(*)::int AS count
            FROM missions m
            JOIN sites s ON s.id = m.parent_id
            JOIN localites l ON l.id = s.parent_id
            JOIN groupements g ON g.id = l.parent_id
            WHERE g.parent_id = %s
        """)
    elif table == "groupements":
        set_count("localites", "localites", "SELECT count(*)::int AS count FROM localites WHERE parent_id = %s", "localites")
        set_count("sites", "sites", """
            SELECT count(*)::int AS count
            FROM sites s
            JOIN localites l ON l.id = s.parent_id
            WHERE l.parent_id = %s
        """)
        set_count("missions", "missions", """
            SELECT count(*)::int AS count
            FROM missions m
            JOIN sites s ON s.id = m.parent_id
            JOIN localites l ON l.id = s.parent_id
            WHERE l.parent_id = %s
        """)
    elif table == "localites":
        set_count("sites", "sites", "SELECT count(*)::int AS count FROM sites WHERE parent_id = %s")
        set_count("missions", "missions", """
            SELECT count(*)::int AS count
            FROM missions m
            JOIN sites s ON s.id = m.parent_id
            WHERE s.parent_id = %s
        """)
        services = db_localite_services(entity_id)
        connectivity = db_localite_connectivity(entity_id)
        if services is not None:
            stats["services_publics"] = services
        if connectivity is not None:
            stats["connectivite"] = connectivity

    if relation_links:
        stats["relation_links"] = relation_links
    return stats


def resolve_table(layer_name: str) -> str:
    table = DB_TABLES.get(layer_name)
    if not table:
        raise ValueError(f"Couche inconnue: {layer_name}")
    return table


def load_report(relative_path: str) -> dict[str, Any]:
    path = REPORTS_DIR / relative_path
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def paginate(items: list[dict[str, Any]], skip: int, limit: int) -> list[dict[str, Any]]:
    return items[skip : skip + limit]


def simplify_entity(item: dict[str, Any]) -> dict[str, Any]:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    attributes = item.get("attributs") if isinstance(item.get("attributs"), dict) else {}
    extended_data = metadata.get("extended_data", {}) or attributes.get("extended_data", {}) or {}
    return enrich_entity({
        "id": item.get("canonical_id") or item.get("id") or item.get("code_officiel") or item.get("nom"),
        "canonical_id": item.get("canonical_id"),
        "nom": item.get("nom") or item.get("name"),
        "niveau": item.get("niveau"),
        "type": item.get("type_localite") or item.get("type_collectivite") or item.get("niveau") or extended_data.get("TYPE"),
        "zone_fdsu": item.get("zone_fdsu"),
        "province": item.get("province"),
        "territoire": item.get("territoire"),
        "collectivite": item.get("collectivite") or item.get("collectivité") or item.get("collectivite_parent"),
        "groupement": item.get("groupement"),
        "source": item.get("source"),
        "statut": item.get("statut"),
        "qualite": item.get("qualite") or item.get("qualité"),
        "quality": item.get("quality"),
        "geometry": item.get("geometry"),
        "metadata": item.get("metadata"),
    })


def count_from_registry(key: str, fallback: int = 0) -> int:
    registry = load_report("national_counter_registry.json").get("registre_national_des_compteurs", {})
    entry = registry.get(key, {})
    if isinstance(entry, dict):
        return int(entry.get("trouve") or entry.get("nombre") or entry.get("attendu") or fallback)
    return fallback


def report_items(relative_path: str, list_key: str) -> list[dict[str, Any]]:
    return [simplify_entity(item) for item in as_list(load_report(relative_path).get(list_key))]


def territory_items() -> list[dict[str, Any]]:
    items = as_list(load_report("territory_hierarchy/territoires_hierarchie_kmz.report.json").get("territories"))
    territories = [
        item
        for item in items
        if str((item.get("attributs") or {}).get("extended_data", {}).get("TYPE", "")).lower() == "territoire"
    ]
    return [simplify_entity(item) for item in territories]


def entity_source_items(layer: str, skip: int = 0, limit: int = 500) -> list[dict[str, Any]]:
    if layer == "zones":
        return paginate(load_nomenclature().get("zones", []), skip, limit)
    if layer == "provinces":
        return read_provinces_json(skip=skip, limit=limit)
    if layer in ("territoires", "territories"):
        return read_territories_json(skip=skip, limit=limit)
    if layer == "collectivites":
        return read_collectivites_json(skip=skip, limit=limit)
    if layer == "groupements":
        return read_groupements_json(skip=skip, limit=limit)
    if layer in ("localites", "villages"):
        return read_localites_json(skip=skip, limit=limit)
    if layer == "sites":
        return read_sites_json(skip=skip, limit=limit)
    if layer == "missions":
        return read_missions_json(skip=skip, limit=limit)
    return []


def entity_search_text(item: dict[str, Any], layer: str) -> str:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    profile = item.get("future_profile") if isinstance(item.get("future_profile"), dict) else {}
    fields = [
        layer,
        item.get("id"),
        item.get("canonical_id"),
        item.get("code"),
        item.get("code_officiel"),
        item.get("nom"),
        item.get("name"),
        item.get("type"),
        item.get("niveau"),
        item.get("zone_fdsu"),
        item.get("province"),
        item.get("territoire"),
        item.get("collectivite"),
        item.get("groupement"),
        metadata.get("description"),
        profile.get("activite_principale"),
        profile.get("activite_secondaire"),
        profile.get("recommandations"),
    ]
    fields.extend(as_list(profile.get("activites_economiques")))
    fields.extend(as_list(profile.get("particularites")))
    fields.extend(str(item) for item in as_list(profile.get("defis")))
    fields.extend(str(item) for item in as_list(profile.get("services_publics")))
    return " ".join(str(value) for value in fields if value).lower()


@app.get("/health", tags=["v0.7.0"])
def health() -> dict[str, str]:
    if use_database():
        try:
            db_fetch_one("SELECT 1 AS ok")
            database_status = "Connectée"
            status = "ok"
        except Exception as error:
            database_status = f"Indisponible: {error}"
            status = "degraded"
        return {
            "status": status,
            "mode": "db",
            "database": database_status,
            "api": "FastAPI v0.8.0 PostGIS experimental",
            "loaded_at": datetime.now().isoformat(timespec="seconds"),
        }
    return {
        "status": "ok",
        "mode": "json-reports",
        "database": "Base non connectee",
        "api": "FastAPI v0.7.0 experimental",
        "loaded_at": datetime.now().isoformat(timespec="seconds"),
    }


@app.get("/dashboard/summary", tags=["v0.7.0"])
def dashboard_summary() -> dict[str, int]:
    if use_database():
        return {
            "zones": db_count("zones"),
            "provinces": db_count("provinces"),
            "territories": db_count("territoires"),
            "villes": db_count("villes"),
            "collectivites": db_count("collectivites"),
            "groupements": db_count("groupements"),
            "localites": db_count("localites"),
            "sites": db_count("sites"),
            "missions": db_count("missions"),
            "users": 0,
        }
    return {
        "zones": 5,
        "provinces": count_from_registry("provinces", 26),
        "territories": count_from_registry("territoires", 145),
        "villes": count_from_registry("villes", 11),
        "collectivites": count_from_registry("collectivites", 733),
        "groupements": count_from_registry("groupements", 1681),
        "localites": count_from_registry("localites", 26710),
        "sites": 0,
        "missions": 0,
        "users": 0,
    }


@app.get("/zones", tags=["v0.8.2"])
def read_zones_json() -> list[dict[str, Any]]:
    if use_database():
        return db_entity_rows("zones", 0, 50)
    return load_nomenclature().get("zones", [])


@app.get("/provinces", tags=["v0.7.0"])
def read_provinces_json(skip: int = Query(0, ge=0), limit: int = Query(500, gt=0)) -> list[dict[str, Any]]:
    if use_database():
        return db_entity_rows("provinces", skip, limit)
    return paginate(report_items("province_official/province_referential_official.json", "province_referential"), skip, limit)


@app.get("/territories", tags=["v0.7.0"])
def read_territories_json(skip: int = Query(0, ge=0), limit: int = Query(500, gt=0)) -> list[dict[str, Any]]:
    if use_database():
        return db_entity_rows("territoires", skip, limit)
    return paginate(territory_items(), skip, limit)


@app.get("/territoires", tags=["v0.7.0"])
def read_territoires_json(skip: int = Query(0, ge=0), limit: int = Query(500, gt=0)) -> list[dict[str, Any]]:
    return read_territories_json(skip=skip, limit=limit)


@app.get("/collectivites", tags=["v0.7.0"])
def read_collectivites_json(skip: int = Query(0, ge=0), limit: int = Query(1000, gt=0)) -> list[dict[str, Any]]:
    if use_database():
        return db_entity_rows("collectivites", skip, limit)
    return paginate(report_items("collectivity_official/collectivity_referential_official.json", "collectivity_referential"), skip, limit)


@app.get("/groupements", tags=["v0.7.0"])
def read_groupements_json(skip: int = Query(0, ge=0), limit: int = Query(2000, gt=0)) -> list[dict[str, Any]]:
    if use_database():
        return db_entity_rows("groupements", skip, limit)
    return paginate(report_items("groupement_official/groupement_referential_official.json", "groupement_referential"), skip, limit)


@app.get("/localites", tags=["v0.7.0"])
def read_localites_json(skip: int = Query(0, ge=0), limit: int = Query(1500, gt=0)) -> list[dict[str, Any]]:
    if use_database():
        return db_entity_rows("localites", skip, limit)
    return paginate(report_items("locality_official/locality_referential_official.json", "locality_referential"), skip, limit)


@app.get("/villages", tags=["v0.7.0"])
def read_villages_json(skip: int = Query(0, ge=0), limit: int = Query(1500, gt=0)) -> list[dict[str, Any]]:
    return read_localites_json(skip=skip, limit=limit)


@app.get("/sites", tags=["v0.7.0"])
def read_sites_json(skip: int = Query(0, ge=0), limit: int = Query(500, gt=0)) -> list[dict[str, Any]]:
    if use_database():
        return db_entity_rows("sites", skip, limit)
    return []


@app.get("/missions", tags=["v0.7.0"])
def read_missions_json(skip: int = Query(0, ge=0), limit: int = Query(500, gt=0)) -> list[dict[str, Any]]:
    if use_database():
        return db_entity_rows("missions", skip, limit)
    return []


@app.get("/map/layers/{layer_name}", tags=["v0.8.0"])
def read_map_layer(layer_name: str, skip: int = Query(0, ge=0), limit: int = Query(5000, gt=0)) -> dict[str, Any]:
    if use_database():
        table = resolve_table(layer_name)
        rows = db_entity_rows(table, skip, limit)
        features = [
            {
                "type": "Feature",
                "geometry": row.get("geometry"),
                "properties": {key: value for key, value in row.items() if key != "geometry"},
            }
            for row in rows
            if row.get("geometry")
        ]
        if layer_name == "zones" and not features:
            province_rows = db_entity_rows("provinces", skip, limit)
            features = [
                {
                    "type": "Feature",
                    "geometry": row.get("geometry"),
                    "properties": {
                        **row,
                        "layer": "zones",
                        "code": row.get("zone_fdsu"),
                        "nom": row.get("zone_nom") or "Zone FDSU",
                        "province": row.get("nom"),
                    },
                }
                for row in province_rows
                if row.get("geometry")
            ]
        return {"type": "FeatureCollection", "features": features}

    json_sources = {
        "zones": ("fdsu_nomenclature.json", "zones"),
        "provinces": ("province_official/province_referential_official.json", "province_referential"),
        "territoires": ("territory_hierarchy/territoires_hierarchie_kmz.report.json", "territories"),
        "collectivites": ("collectivity_official/collectivity_referential_official.json", "collectivity_referential"),
        "groupements": ("groupement_official/groupement_referential_official.json", "groupement_referential"),
        "localites": ("locality_official/locality_referential_official.json", "locality_referential"),
        "villages": ("locality_official/locality_referential_official.json", "locality_referential"),
        "sites": ("", ""),
        "missions": ("", ""),
    }
    source = json_sources.get(layer_name)
    if not source or not source[0]:
        return {"type": "FeatureCollection", "features": []}
    items = as_list(load_report(source[0]).get(source[1]))
    if layer_name == "zones":
        province_items = as_list(load_report("province_official/province_referential_official.json").get("province_referential"))
        features = []
        for province in province_items:
            enriched = enrich_entity(simplify_entity(province))
            geometry = province.get("geometry")
            if not geometry:
                continue
            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        **enriched,
                        "layer": "zones",
                        "code": enriched.get("zone_fdsu"),
                        "nom": next((zone.get("nom") for zone in items if zone.get("code") == enriched.get("zone_fdsu")), "Zone FDSU"),
                        "province": enriched.get("nom"),
                    },
                }
            )
        return {"type": "FeatureCollection", "features": features}
    if layer_name == "territoires":
        items = [
            item
            for item in items
            if str((item.get("attributs") or {}).get("extended_data", {}).get("TYPE", "")).lower() == "territoire"
        ]
    features = []
    for item in paginate(items, skip, limit):
        geometry = item.get("geometry")
        if geometry:
            features.append({"type": "Feature", "geometry": geometry, "properties": simplify_entity(item)})
    return {"type": "FeatureCollection", "features": features}


@app.get("/entities/search", tags=["v0.8.0"])
def search_entities(
    q: str = Query("", description="Texte recherche: nom, code FDSU, activite, defi, service ou document"),
    layer: str | None = Query(None, description="Filtre optionnel: zone, provinces, territoires, collectivites, groupements, localites, sites, missions"),
    skip: int = Query(0, ge=0),
    limit: int = Query(25, gt=0, le=200),
) -> dict[str, Any]:
    query_value = q if isinstance(q, str) else ""
    layer_value = layer if isinstance(layer, str) and layer else None
    skip_value = skip if isinstance(skip, int) else 0
    limit_value = limit if isinstance(limit, int) else 25
    requested_layers = [layer_value] if layer_value else [
        "zones",
        "provinces",
        "territoires",
        "collectivites",
        "groupements",
        "localites",
        "sites",
        "missions",
    ]
    normalized_query = query_value.strip().lower()
    matches: list[dict[str, Any]] = []
    for layer_name in requested_layers:
        canonical_layer = "localites" if layer_name == "villages" else layer_name
        items = entity_source_items(canonical_layer, 0, 5000)
        for item in items:
            simplified = simplify_entity(item) if canonical_layer != "zones" else enrich_entity(item)
            if normalized_query and normalized_query not in entity_search_text(simplified, canonical_layer):
                continue
            matches.append({
                "layer": canonical_layer,
                "id": simplified.get("id") or simplified.get("canonical_id") or simplified.get("code") or simplified.get("nom"),
                "nom": simplified.get("nom") or simplified.get("name"),
                "type": simplified.get("type") or simplified.get("niveau") or canonical_layer,
                "zone_fdsu": simplified.get("zone_fdsu") or simplified.get("code") if canonical_layer == "zones" else simplified.get("zone_fdsu"),
                "province": simplified.get("province"),
                "territoire": simplified.get("territoire"),
                "collectivite": simplified.get("collectivite"),
                "groupement": simplified.get("groupement"),
                "source": simplified.get("source"),
            })
    total = len(matches)
    return {
        "query": query_value,
        "total": total,
        "skip": skip_value,
        "limit": limit_value,
        "items": matches[skip_value : skip_value + limit_value],
    }


@app.get("/entities/{layer}/{entity_id}", tags=["v0.8.0"])
def read_entity(layer: str, entity_id: int | str) -> dict[str, Any]:
    if use_database():
        table = resolve_table(layer)
        row = db_fetch_one(
            f"""
            SELECT
                id, code, nom, type, parent_id, latitude, longitude, source,
                quality_score AS qualite, status AS statut, metadata,
                CASE WHEN geom IS NULL THEN NULL ELSE ST_AsGeoJSON(geom)::json END AS geometry
            FROM {table}
            WHERE id::text = %s OR code = %s
            LIMIT 1
            """,
            (str(entity_id), str(entity_id)),
        )
        if not row:
            return {}
        row.update(db_relation_stats(table, int(row["id"])))
        return enrich_entity(row)

    layer_sources = {
        "provinces": ("province_official/province_referential_official.json", "province_referential"),
        "territoires": ("territory_hierarchy/territoires_hierarchie_kmz.report.json", "territories"),
        "collectivites": ("collectivity_official/collectivity_referential_official.json", "collectivity_referential"),
        "groupements": ("groupement_official/groupement_referential_official.json", "groupement_referential"),
        "localites": ("locality_official/locality_referential_official.json", "locality_referential"),
        "villages": ("locality_official/locality_referential_official.json", "locality_referential"),
    }
    source = layer_sources.get(layer)
    if not source:
        return {}
    for item in as_list(load_report(source[0]).get(source[1])):
        simplified = simplify_entity(item)
        candidates = [
            simplified.get("id"),
            simplified.get("canonical_id"),
            simplified.get("code"),
            simplified.get("code_officiel"),
            simplified.get("nom"),
            simplified.get("name"),
        ]
        if any(str(candidate).lower() == str(entity_id).lower() for candidate in candidates if candidate):
            return simplified
    return {}


@app.get("/provinces/{entity_id}", tags=["v0.8.0"])
def read_province_detail(entity_id: int | str) -> dict[str, Any]:
    return read_entity("provinces", entity_id)


@app.get("/territoires/{entity_id}", tags=["v0.8.0"])
def read_territoire_detail(entity_id: int | str) -> dict[str, Any]:
    return read_entity("territoires", entity_id)


@app.get("/collectivites/{entity_id}", tags=["v0.8.0"])
def read_collectivite_detail(entity_id: int | str) -> dict[str, Any]:
    return read_entity("collectivites", entity_id)


@app.get("/groupements/{entity_id}", tags=["v0.8.0"])
def read_groupement_detail(entity_id: int | str) -> dict[str, Any]:
    return read_entity("groupements", entity_id)


@app.get("/localites/{entity_id}", tags=["v0.8.0"])
def read_localite_detail(entity_id: int | str) -> dict[str, Any]:
    return read_entity("localites", entity_id)


app.include_router(provinces.router, prefix="/provinces", tags=["Provinces"])
app.include_router(territoires.router, prefix="/territoires", tags=["Territoires"])
app.include_router(collectivites.router, prefix="/collectivites", tags=["Collectivites"])
app.include_router(groupements.router, prefix="/groupements", tags=["Groupements"])
app.include_router(villages.router, prefix="/villages", tags=["Villages"])
app.include_router(sites.router, prefix="/sites", tags=["Sites"])
app.include_router(missions.router, prefix="/missions", tags=["Missions"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(photos.router, prefix="/photos", tags=["Photos"])
app.include_router(imports.router, prefix="/imports", tags=["Imports"])
app.include_router(decision.router, prefix="/decision", tags=["Aide a la decision"])
app.include_router(territorial_enrichment.router, prefix="/territorial-enrichment", tags=["Enrichissement territorial"])
app.include_router(enrichment.router, prefix="/enrichment", tags=["Assistant d'enrichissement"])
app.include_router(knowledge.router, prefix="/knowledge", tags=["Centre de connaissances"])

@app.get("/", tags=["Root"])
def read_root() -> dict[str, str]:
    return {"message": "SIG-FDSU RDC API est en cours d'exécution."}
