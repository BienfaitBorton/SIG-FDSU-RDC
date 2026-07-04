from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import Json

from app.fdsu_nomenclature import enrich_entity, find_province, find_territory, load_nomenclature


BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "data" / "reports"
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/sig_fdsu_rdc",
)

ZONE_LABELS = {zone["code"]: zone["nom"] for zone in load_nomenclature().get("zones", [])}


def load_report(relative_path: str) -> dict[str, Any]:
    path = REPORTS_DIR / relative_path
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def normalize_key(value: Any) -> str:
    return str(value or "").strip().lower()


def geometry_point(geometry: dict[str, Any] | None) -> tuple[float | None, float | None, float | None]:
    if not geometry or not isinstance(geometry.get("coordinates"), list):
        return None, None, None
    cursor = geometry["coordinates"]
    while isinstance(cursor, list) and cursor and isinstance(cursor[0], list):
        cursor = cursor[0]
    if not isinstance(cursor, list) or len(cursor) < 2:
        return None, None, None
    try:
        altitude = float(cursor[2]) if len(cursor) > 2 and cursor[2] is not None else None
        return float(cursor[1]), float(cursor[0]), altitude
    except (TypeError, ValueError):
        return None, None, None


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def force_2d_position(position: list[Any]) -> list[float]:
    longitude = to_float(position[0] if len(position) > 0 else None)
    latitude = to_float(position[1] if len(position) > 1 else None)
    if longitude is None or latitude is None:
        raise ValueError("Coordonnées longitude/latitude invalides")
    return [longitude, latitude]


def force_2d_coordinates(coordinates: Any) -> Any:
    if not isinstance(coordinates, list):
        raise ValueError("Coordonnées GeoJSON invalides")
    if coordinates and not isinstance(coordinates[0], list):
        return force_2d_position(coordinates)
    return [force_2d_coordinates(child) for child in coordinates]


def force_2d_geometry(geometry: dict[str, Any] | None) -> dict[str, Any] | None:
    if not geometry:
        return None
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if not geometry_type or coordinates is None:
        return None
    return {
        "type": geometry_type,
        "coordinates": force_2d_coordinates(coordinates),
    }


def entity_code(item: dict[str, Any], prefix: str, fallback_name: str) -> str:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    extended = metadata.get("extended_data") if isinstance(metadata.get("extended_data"), dict) else {}
    return str(
        item.get("canonical_id")
        or item.get("code_officiel")
        or item.get("code")
        or extended.get("PCODE")
        or extended.get("CODE_GRPT")
        or extended.get("CODE_INS")
        or f"{prefix}-{fallback_name}"
    )


def execute_insert(cur, table: str, row: dict[str, Any]) -> tuple[int | None, bool]:
    geometry = row.pop("geometry", None)
    geometry_2d = force_2d_geometry(geometry)
    geom_json = json.dumps(geometry_2d) if geometry_2d else None
    cur.execute("SAVEPOINT seed_entity")
    try:
        cur.execute(
            f"""
            INSERT INTO {table}
                (code, nom, type, parent_id, latitude, longitude, altitude, geom, source, quality_score, status, metadata)
            VALUES
                (%(code)s, %(nom)s, %(type)s, %(parent_id)s, %(latitude)s, %(longitude)s, %(altitude)s,
                 CASE WHEN %(geom)s IS NULL THEN NULL ELSE ST_SetSRID(ST_GeomFromGeoJSON(%(geom)s), 4326) END,
                 %(source)s, %(quality_score)s, %(status)s, %(metadata)s)
            ON CONFLICT (code) DO NOTHING
            RETURNING id
            """,
            {
                **row,
                "geom": geom_json,
                "metadata": Json(row.get("metadata") or {}),
            },
        )
        result = cur.fetchone()
        cur.execute("RELEASE SAVEPOINT seed_entity")
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT seed_entity")
        cur.execute("RELEASE SAVEPOINT seed_entity")
        raise
    if result:
        return int(result[0]), True

    cur.execute(f"SELECT id FROM {table} WHERE code = %s", (row["code"],))
    existing = cur.fetchone()
    return (int(existing[0]) if existing else None), False


def make_row(
    item: dict[str, Any],
    *,
    prefix: str,
    default_type: str,
    parent_id: int | None = None,
) -> dict[str, Any]:
    item = enrich_entity(item)
    geometry = item.get("geometry")
    latitude, longitude, altitude = geometry_point(geometry)
    name = item.get("nom") or item.get("name") or "Non renseigné"
    return {
        "code": entity_code(item, prefix, str(name).replace(" ", "_")),
        "nom": name,
        "type": item.get("type_localite") or item.get("type_collectivite") or item.get("niveau") or default_type,
        "parent_id": parent_id,
        "latitude": to_float(latitude),
        "longitude": to_float(longitude),
        "altitude": to_float(altitude),
        "geometry": geometry,
        "source": item.get("source") or item.get("source_file"),
        "quality_score": item.get("qualité") or item.get("qualite") or item.get("score_qualite"),
        "status": item.get("statut") or "official_candidate",
        "metadata": {
            **(item.get("metadata") or item.get("attributs") or {}),
            "code_province_fdsu": item.get("code_province_fdsu"),
            "code_territoire_fdsu": item.get("code_territoire_fdsu"),
            "fdsu_codification_format": item.get("fdsu_codification_format"),
        },
    }


def seed() -> dict[str, Any]:
    report = {"inserted": {}, "ignored": {}, "errors": []}
    inserted_total = 0
    ignored_total = 0

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO import_batches(source, status) VALUES (%s, %s) RETURNING id",
                ("data/reports JSON", "running"),
            )
            batch_id = int(cur.fetchone()[0])

            def add_count(table: str, inserted: bool) -> None:
                nonlocal inserted_total, ignored_total
                key = "inserted" if inserted else "ignored"
                report[key][table] = report[key].get(table, 0) + 1
                if inserted:
                    inserted_total += 1
                else:
                    ignored_total += 1

            def record_error(table: str, item: dict[str, Any], error: Exception) -> None:
                entry = {
                    "table": table,
                    "code": item.get("canonical_id") or item.get("code_officiel"),
                    "name": item.get("nom"),
                    "error": str(error),
                }
                report["errors"].append(entry)
                cur.execute(
                    """
                    INSERT INTO import_errors(batch_id, table_name, entity_code, entity_name, error_message, raw_entity)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (batch_id, table, entry["code"], entry["name"], entry["error"], Json(item)),
                )

            zone_ids: dict[str, int] = {}
            for code, name in ZONE_LABELS.items():
                row = {
                    "code": code,
                    "nom": name,
                    "type": "Zone FDSU",
                    "parent_id": None,
                    "latitude": None,
                    "longitude": None,
                    "altitude": None,
                    "geometry": None,
                    "source": "national_counter_registry.json",
                    "quality_score": 100,
                    "status": "official_candidate",
                    "metadata": {"zone_fdsu": code},
                }
                entity_id, inserted = execute_insert(cur, "zones", row)
                if entity_id:
                    zone_ids[code] = entity_id
                add_count("zones", inserted)

            province_ids: dict[str, int] = {}
            provinces = as_list(load_report("province_official/province_referential_official.json").get("province_referential"))
            for item in provinces:
                try:
                    enriched = enrich_entity(item)
                    row = make_row(enriched, prefix="PROV", default_type="Province", parent_id=zone_ids.get(enriched.get("zone_fdsu")))
                    official_province = find_province(enriched.get("nom"))
                    if official_province:
                        row["code"] = official_province["code"]
                    entity_id, inserted = execute_insert(cur, "provinces", row)
                    if entity_id:
                        province_ids[normalize_key(item.get("nom"))] = entity_id
                    add_count("provinces", inserted)
                except Exception as error:
                    record_error("provinces", item, error)

            territory_ids: dict[str, int] = {}
            city_items: list[dict[str, Any]] = []
            territories = as_list(load_report("territory_hierarchy/territoires_hierarchie_kmz.report.json").get("territories"))
            for item in territories:
                extended = item.get("attributs", {}).get("extended_data", {})
                target_table = "territoires" if str(extended.get("TYPE", "")).lower() == "territoire" else "villes"
                try:
                    enriched = enrich_entity(item)
                    row = make_row(
                        enriched,
                        prefix="TERR" if target_table == "territoires" else "VILLE",
                        default_type=extended.get("TYPE") or ("Territoire" if target_table == "territoires" else "Ville"),
                        parent_id=province_ids.get(normalize_key(item.get("province"))),
                    )
                    official_territory = find_territory(enriched.get("nom"), enriched.get("province"), enriched.get("code_province_fdsu"))
                    if official_territory:
                        row["code"] = f"{official_territory['province_code']}{official_territory['code']}"
                    entity_id, inserted = execute_insert(cur, target_table, row)
                    if target_table == "territoires" and entity_id:
                        territory_ids[normalize_key(item.get("nom"))] = entity_id
                    elif target_table == "villes":
                        city_items.append(item)
                    add_count(target_table, inserted)
                except Exception as error:
                    record_error(target_table, item, error)

            collectivity_ids: dict[str, int] = {}
            collectivities = as_list(load_report("collectivity_official/collectivity_referential_official.json").get("collectivity_referential"))
            for item in collectivities:
                try:
                    row = make_row(item, prefix="COLL", default_type="Collectivité", parent_id=territory_ids.get(normalize_key(item.get("territoire"))))
                    entity_id, inserted = execute_insert(cur, "collectivites", row)
                    if entity_id:
                        collectivity_ids[normalize_key(item.get("nom"))] = entity_id
                    add_count("collectivites", inserted)
                except Exception as error:
                    record_error("collectivites", item, error)

            groupement_ids: dict[str, int] = {}
            groupements = as_list(load_report("groupement_official/groupement_referential_official.json").get("groupement_referential"))
            for item in groupements:
                try:
                    row = make_row(item, prefix="GRPT", default_type="Groupement", parent_id=collectivity_ids.get(normalize_key(item.get("collectivite_parent"))))
                    entity_id, inserted = execute_insert(cur, "groupements", row)
                    if entity_id:
                        groupement_ids[normalize_key(item.get("nom"))] = entity_id
                    add_count("groupements", inserted)
                except Exception as error:
                    record_error("groupements", item, error)

            localities = as_list(load_report("locality_official/locality_referential_official.json").get("locality_referential"))
            for item in localities:
                try:
                    row = make_row(item, prefix="LOC", default_type="Localité", parent_id=groupement_ids.get(normalize_key(item.get("groupement"))))
                    _entity_id, inserted = execute_insert(cur, "localites", row)
                    add_count("localites", inserted)
                except Exception as error:
                    record_error("localites", item, error)

            report["totals"] = {
                "inserted": inserted_total,
                "ignored": ignored_total,
                "errors": len(report["errors"]),
            }
            cur.execute(
                """
                UPDATE import_batches
                SET status = %s, inserted_count = %s, ignored_count = %s, error_count = %s, report = %s
                WHERE id = %s
                """,
                ("completed", inserted_total, ignored_total, len(report["errors"]), Json(report), batch_id),
            )

    return report


if __name__ == "__main__":
    print(json.dumps(seed(), ensure_ascii=False, indent=2))
