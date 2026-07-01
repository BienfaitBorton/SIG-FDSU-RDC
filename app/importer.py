from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import engine
from app.models import (
    Collectivite,
    CollectiviteType,
    Groupement,
    ImportHistory,
    Province,
    Territoire,
    Village,
)

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Parent lookup cache to optimize repeated lookups when importing large files
_PARENT_CACHE: dict[tuple[str, str, str], int | None] = {}

DEFAULT_ENTITY_ORDER = ["provinces", "territoires", "collectivites", "groupements", "villages"]

DEFAULT_FIELD_ALIASES = {
    "code": [
        "code",
        "code province",
        "code territoire",
        "code collectivite",
        "code collectivité",
        "code groupement",
        "code village",
        "code prov",
        "code terr",
        "code coll",
        "code grp",
        "code vil",
    ],
    "nom": [
        "nom",
        "nom province",
        "nom territoire",
        "nom collectivite",
        "nom collectivité",
        "nom groupement",
        "nom village",
    ],
    "zone": ["zone", "zone fdsu", "zone_fdsu", "region", "région"],
    "chef_lieu": [
        "chef_lieu",
        "chef-lieu",
        "chef lieu",
        "chef_lieu province",
        "chef lieu province",
        "chef-lieu province",
    ],
    "province_code": [
        "province_code",
        "code province",
        "province code",
        "code_prov",
        "prov code",
    ],
    "territoire_code": [
        "territoire_code",
        "code territoire",
        "territoire code",
        "code_terr",
        "terr code",
    ],
    "collectivite_code": [
        "collectivite_code",
        "code collectivite",
        "collectivite code",
        "code_coll",
        "coll code",
    ],
    "groupement_code": [
        "groupement_code",
        "code groupement",
        "groupement code",
        "code_grp",
        "grp code",
    ],
    "type_collectivite": [
        "type_collectivite",
        "type collectivite",
        "type",
    ],
    "population": ["population", "pop", "habitants"],
    "superficie": ["superficie", "surface", "surface_km2", "superficie_km2"],
}

ENTITY_CONFIGS = {
    "provinces": {
        "display_name": "Provinces",
        "sheet_names": ["provinces", "province"],
        "required_fields": ["code", "nom", "zone"],
        "optional_fields": ["chef_lieu", "population", "superficie"],
        "aliases": {
            "code": DEFAULT_FIELD_ALIASES["code"],
            "nom": DEFAULT_FIELD_ALIASES["nom"],
            "zone": DEFAULT_FIELD_ALIASES["zone"],
            "chef_lieu": DEFAULT_FIELD_ALIASES["chef_lieu"],
            "population": DEFAULT_FIELD_ALIASES["population"],
            "superficie": DEFAULT_FIELD_ALIASES["superficie"],
        },
    },
    "territoires": {
        "display_name": "Territoires",
        "sheet_names": ["territoires", "territoire"],
        "required_fields": ["code", "nom", "province_code"],
        "optional_fields": ["chef_lieu"],
        "aliases": {
            "code": DEFAULT_FIELD_ALIASES["code"],
            "nom": DEFAULT_FIELD_ALIASES["nom"],
            "province_code": DEFAULT_FIELD_ALIASES["province_code"],
            "chef_lieu": DEFAULT_FIELD_ALIASES["chef_lieu"],
        },
    },
    "collectivites": {
        "display_name": "Collectivites",
        "sheet_names": ["collectivites", "collectivite"],
        "required_fields": ["code", "nom", "type_collectivite", "territoire_code"],
        "optional_fields": ["chef_lieu"],
        "aliases": {
            "code": DEFAULT_FIELD_ALIASES["code"],
            "nom": DEFAULT_FIELD_ALIASES["nom"],
            "type_collectivite": DEFAULT_FIELD_ALIASES["type_collectivite"],
            "territoire_code": DEFAULT_FIELD_ALIASES["territoire_code"],
            "chef_lieu": DEFAULT_FIELD_ALIASES["chef_lieu"],
        },
    },
    "groupements": {
        "display_name": "Groupements",
        "sheet_names": ["groupements", "groupement"],
        "required_fields": ["code", "nom", "collectivite_code"],
        "optional_fields": ["chef_lieu"],
        "aliases": {
            "code": DEFAULT_FIELD_ALIASES["code"],
            "nom": DEFAULT_FIELD_ALIASES["nom"],
            "collectivite_code": DEFAULT_FIELD_ALIASES["collectivite_code"],
            "chef_lieu": DEFAULT_FIELD_ALIASES["chef_lieu"],
        },
    },
    "villages": {
        "display_name": "Villages",
        "sheet_names": ["villages", "village"],
        "required_fields": ["code", "nom", "groupement_code"],
        "optional_fields": ["chef_lieu"],
        "aliases": {
            "code": DEFAULT_FIELD_ALIASES["code"],
            "nom": DEFAULT_FIELD_ALIASES["nom"],
            "groupement_code": DEFAULT_FIELD_ALIASES["groupement_code"],
            "chef_lieu": DEFAULT_FIELD_ALIASES["chef_lieu"],
        },
    },
}


class MappingError(Exception):
    pass


class ImporterError(Exception):
    pass


@dataclass
class EntityResult:
    entity: str
    sheet_name: str
    mapped_columns: dict[str, str]
    rows_total: int = 0
    inserted: int = 0
    updated: int = 0
    rejected: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        self.errors.append(message)


@dataclass
class ImportReport:
    filename: Path
    username: str
    entity: str
    started_at: datetime = field(default_factory=datetime.now)
    duration_seconds: float | None = None
    rows_total: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_rejected: int = 0
    status: str = "pending"
    summary: list[str] = field(default_factory=list)
    entity_results: list[EntityResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_entity_result(self, result: EntityResult) -> None:
        self.entity_results.append(result)
        self.rows_total += result.rows_total
        self.rows_inserted += result.inserted
        self.rows_updated += result.updated
        self.rows_rejected += result.rejected
        if result.errors:
            self.errors.extend(result.errors)

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def build_summary(self) -> None:
        lines = [
            f"Import FDSU officiel : {self.filename}",
            f"Utilisateur : {self.username}",
            f"Démarré à : {self.started_at.isoformat(sep=' ', timespec='seconds')}",
            f"Statut : {self.status}",
            f"Durée : {self.duration_seconds:.3f}s" if self.duration_seconds is not None else "Durée : N/A",
            f"Lignes totales : {self.rows_total}",
            f"Insérées : {self.rows_inserted}",
            f"Mises à jour : {self.rows_updated}",
            f"Rejetées : {self.rows_rejected}",
        ]
        for entity_result in self.entity_results:
            lines.append(
                f"  - {entity_result.entity} ({entity_result.sheet_name}) : totale={entity_result.rows_total}, insérées={entity_result.inserted}, mises à jour={entity_result.updated}, rejetées={entity_result.rejected}"
            )
            if entity_result.warnings:
                lines.append("    warnings:")
                lines.extend(f"      - {warning}" for warning in entity_result.warnings)
            if entity_result.errors:
                lines.append("    erreurs:")
                lines.extend(f"      - {error}" for error in entity_result.errors)
        if self.errors:
            lines.append("Erreurs globales :")
            lines.extend(f"  - {error}" for error in self.errors)
        self.summary = lines

    def format_summary(self) -> str:
        if not self.summary:
            self.build_summary()
        return "\n".join(self.summary)

    def write_log(self, log_path: Path) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as handle:
            handle.write(self.format_summary())


def _normalize_header(value: Any) -> str:
    if value is None:
        return ""
    header = str(value).strip().lower()
    header = re.sub(r"[\s\-_]+", " ", header)
    header = re.sub(r"[^a-z0-9 ]", "", header)
    return header


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _load_mapping_config(mapping_path: Path) -> dict[str, Any]:
    with mapping_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise MappingError("Le fichier de configuration de mapping doit contenir un objet JSON.")
    return data


def _resolve_entity_config(entity: str, custom_config: dict[str, Any] | None = None) -> dict[str, Any]:
    if entity not in ENTITY_CONFIGS:
        raise MappingError(f"Entité inconnue : {entity}")

    config = {**ENTITY_CONFIGS[entity]}
    config["aliases"] = {**config["aliases"]}

    if custom_config is None:
        return config

    entity_config = custom_config.get(entity, {})
    if not isinstance(entity_config, dict):
        raise MappingError(f"Configuration invalide pour l'entité {entity}.")

    if sheet_name := entity_config.get("sheet_name"):
        config["sheet_names"] = [sheet_name]

    override_map = entity_config.get("column_map")
    if override_map is not None:
        if not isinstance(override_map, dict):
            raise MappingError("`column_map` doit être un objet JSON.")
        for field, target in override_map.items():
            if field not in config["aliases"]:
                raise MappingError(f"Champ inconnu dans le mapping pour {entity} : {field}")
            if isinstance(target, str):
                config["aliases"][field] = [target, *config["aliases"][field]]
            elif isinstance(target, list):
                config["aliases"][field] = [*target, *config["aliases"][field]]
            else:
                raise MappingError(
                    f"La valeur de mapping pour le champ {field} doit être une chaîne ou une liste de chaînes."
                )

    return config


def _detect_sheet_name(available: list[str], config: dict[str, Any]) -> str:
    normalized_available = {normalize_header(name): name for name in available}
    for candidate in config["sheet_names"]:
        candidate_norm = normalize_header(candidate)
        if candidate_norm in normalized_available:
            return normalized_available[candidate_norm]
    for candidate in config["sheet_names"]:
        candidate_norm = normalize_header(candidate)
        for normalized_name, actual_name in normalized_available.items():
            if candidate_norm in normalized_name or normalized_name in candidate_norm:
                return actual_name
    if len(available) == 1:
        return available[0]
    raise MappingError(
        f"Impossible de trouver la feuille Excel pour l'entité {config['display_name']} dans {available}."
    )


def _load_entity_dataframe(
    file_path: Path,
    entity: str,
    custom_config: dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], str]:
    config = _resolve_entity_config(entity, custom_config)
    extension = file_path.suffix.lower()
    if extension in {".xlsx", ".xls"}:
        xls = pd.ExcelFile(file_path, engine="openpyxl")
        sheet_name = _detect_sheet_name(xls.sheet_names, config)
        df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=object)
    elif extension == ".csv":
        sheet_name = file_path.name
        df = pd.read_csv(file_path, dtype=object)
    else:
        raise MappingError(f"Format de fichier non supporté : {extension}")

    df.columns = [str(col).strip() for col in df.columns]
    return df, config, sheet_name


def _map_columns(df: pd.DataFrame, config: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    normalized_columns = {normalize_header(col): col for col in df.columns}
    mapping: dict[str, str] = {}
    missing: list[str] = []

    for field, aliases in config["aliases"].items():
        found_column = None
        for alias in aliases:
            normalized_alias = normalize_header(alias)
            if normalized_alias in normalized_columns:
                found_column = normalized_columns[normalized_alias]
                break
        if found_column:
            mapping[field] = found_column
        elif field in config["required_fields"]:
            missing.append(field)

    return mapping, missing


def _normalize_value(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _parse_int(value: Any) -> int | None:
    normalized = _normalize_value(value)
    if normalized == "":
        return None
    try:
        return int(float(normalized))
    except ValueError as exc:
        raise ImporterError(f"Valeur entière invalide : {value}") from exc


def _parse_float(value: Any) -> float | None:
    normalized = _normalize_value(value)
    if normalized == "":
        return None
    try:
        return float(normalized)
    except ValueError as exc:
        raise ImporterError(f"Valeur décimale invalide : {value}") from exc


def _parse_collectivite_type(value: Any) -> CollectiviteType:
    normalized = _normalize_value(value).lower()
    if normalized in {"secteur", "secteur "}:
        return CollectiviteType.Secteur
    if normalized in {"chefferie", "chefferie "}:
        return CollectiviteType.Chefferie
    if normalized in {"cite", "cité", "cite "}:
        return CollectiviteType.Cite
    raise ImporterError(
        f"Type de collectivité invalide : {value}. Valeurs acceptées : Secteur, Chefferie, Cité"
    )


def _load_custom_config(mapping_path: Path | None) -> dict[str, Any] | None:
    if mapping_path is None:
        return None
    return _load_mapping_config(mapping_path)


def _build_log_path(filename: str, entity: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", filename)
    return LOG_DIR / f"{timestamp}_{safe_name}_{entity}.log"


def _find_parent_id(session: Session, parent_model: Any, parent_code: str, parent_field_name: str) -> int | None:
    # simple in-memory cache to avoid repeated DB lookups for the same parent code
    key = (parent_model.__tablename__, parent_field_name, parent_code)
    if key in _PARENT_CACHE:
        return _PARENT_CACHE[key]
    parent = session.scalar(select(parent_model).where(getattr(parent_model, parent_field_name) == parent_code))
    parent_id = parent.id if parent is not None else None
    _PARENT_CACHE[key] = parent_id
    return parent_id


def _process_province_row(row: dict[str, Any], mapping: dict[str, str], result: EntityResult, session: Session) -> None:
    code = _normalize_value(row[mapping["code"]])
    nom = _normalize_value(row[mapping["nom"]])
    zone = _normalize_value(row[mapping["zone"]])
    if not code or not nom or not zone:
        result.rejected += 1
        result.add_error("Ligne ignorée : code, nom et zone sont requis.")
        return
    chef_lieu = _normalize_value(row.get(mapping.get("chef_lieu"))) or None
    population = _parse_int(row.get(mapping.get("population")))
    superficie = _parse_float(row.get(mapping.get("superficie")))

    province = session.scalar(select(Province).where(Province.code == code))
    if province is not None:
        province.nom = nom
        province.zone = zone
        province.chef_lieu = chef_lieu
        province.population = population
        province.superficie = superficie
        result.updated += 1
        return

    province = Province(
        code=code,
        nom=nom,
        zone=zone,
        chef_lieu=chef_lieu,
        population=population,
        superficie=superficie,
    )
    session.add(province)
    result.inserted += 1


def _process_territoire_row(row: dict[str, Any], mapping: dict[str, str], result: EntityResult, session: Session) -> None:
    code = _normalize_value(row[mapping["code"]])
    nom = _normalize_value(row[mapping["nom"]])
    province_code = _normalize_value(row[mapping["province_code"]])
    if not code or not nom or not province_code:
        result.rejected += 1
        result.add_error("Ligne ignorée : code, nom et province_code sont requis.")
        return
    province_id = _find_parent_id(session, Province, province_code, "code")
    if province_id is None:
        result.rejected += 1
        result.add_error(f"Territoire {code} ignoré : province {province_code} introuvable.")
        return

    chef_lieu = _normalize_value(row.get(mapping.get("chef_lieu"))) or None
    territoire = session.scalar(
        select(Territoire).where(Territoire.code == code, Territoire.province_id == province_id)
    )
    if territoire is not None:
        territoire.nom = nom
        territoire.chef_lieu = chef_lieu
        result.updated += 1
        return

    territoire = Territoire(
        code=code,
        nom=nom,
        chef_lieu=chef_lieu,
        province_id=province_id,
    )
    session.add(territoire)
    result.inserted += 1


def _process_collectivite_row(row: dict[str, Any], mapping: dict[str, str], result: EntityResult, session: Session) -> None:
    code = _normalize_value(row[mapping["code"]])
    nom = _normalize_value(row[mapping["nom"]])
    territoire_code = _normalize_value(row[mapping["territoire_code"]])
    type_value = _normalize_value(row[mapping["type_collectivite"]])
    if not code or not nom or not territoire_code or not type_value:
        result.rejected += 1
        result.add_error("Ligne ignorée : code, nom, type_collectivite et territoire_code sont requis.")
        return
    territoire_id = _find_parent_id(session, Territoire, territoire_code, "code")
    if territoire_id is None:
        result.rejected += 1
        result.add_error(f"Collectivite {code} ignorée : territoire {territoire_code} introuvable.")
        return

    try:
        type_collectivite = _parse_collectivite_type(type_value)
    except ImporterError as exc:
        result.rejected += 1
        result.add_error(str(exc))
        return

    chef_lieu = _normalize_value(row.get(mapping.get("chef_lieu"))) or None
    collectivite = session.scalar(
        select(Collectivite).where(
            Collectivite.code == code,
            Collectivite.territoire_id == territoire_id,
        )
    )
    if collectivite is not None:
        collectivite.nom = nom
        collectivite.type_collectivite = type_collectivite
        collectivite.chef_lieu = chef_lieu
        result.updated += 1
        return

    collectivite = Collectivite(
        code=code,
        nom=nom,
        type_collectivite=type_collectivite,
        chef_lieu=chef_lieu,
        territoire_id=territoire_id,
    )
    session.add(collectivite)
    result.inserted += 1


def _process_groupement_row(row: dict[str, Any], mapping: dict[str, str], result: EntityResult, session: Session) -> None:
    code = _normalize_value(row[mapping["code"]])
    nom = _normalize_value(row[mapping["nom"]])
    collectivite_code = _normalize_value(row[mapping["collectivite_code"]])
    if not code or not nom or not collectivite_code:
        result.rejected += 1
        result.add_error("Ligne ignorée : code, nom et collectivite_code sont requis.")
        return

    collectivite_id = _find_parent_id(session, Collectivite, collectivite_code, "code")
    if collectivite_id is None:
        result.rejected += 1
        result.add_error(f"Groupement {code} ignoré : collectivite {collectivite_code} introuvable.")
        return

    chef_lieu = _normalize_value(row.get(mapping.get("chef_lieu"))) or None
    groupement = session.scalar(
        select(Groupement).where(
            Groupement.code == code,
            Groupement.collectivite_id == collectivite_id,
        )
    )
    if groupement is not None:
        groupement.nom = nom
        groupement.chef_lieu = chef_lieu
        result.updated += 1
        return

    groupement = Groupement(
        code=code,
        nom=nom,
        chef_lieu=chef_lieu,
        collectivite_id=collectivite_id,
    )
    session.add(groupement)
    result.inserted += 1


def _process_village_row(row: dict[str, Any], mapping: dict[str, str], result: EntityResult, session: Session) -> None:
    code = _normalize_value(row[mapping["code"]])
    nom = _normalize_value(row[mapping["nom"]])
    groupement_code = _normalize_value(row[mapping["groupement_code"]])
    if not code or not nom or not groupement_code:
        result.rejected += 1
        result.add_error("Ligne ignorée : code, nom et groupement_code sont requis.")
        return

    groupement_id = _find_parent_id(session, Groupement, groupement_code, "code")
    if groupement_id is None:
        result.rejected += 1
        result.add_error(f"Village {code} ignoré : groupement {groupement_code} introuvable.")
        return

    chef_lieu = _normalize_value(row.get(mapping.get("chef_lieu"))) or None
    village = session.scalar(
        select(Village).where(
            Village.code == code,
            Village.groupement_id == groupement_id,
        )
    )
    if village is not None:
        village.nom = nom
        village.chef_lieu = chef_lieu
        result.updated += 1
        return

    village = Village(
        code=code,
        nom=nom,
        chef_lieu=chef_lieu,
        groupement_id=groupement_id,
    )
    session.add(village)
    result.inserted += 1


_PROCESSORS = {
    "provinces": _process_province_row,
    "territoires": _process_territoire_row,
    "collectivites": _process_collectivite_row,
    "groupements": _process_groupement_row,
    "villages": _process_village_row,
}


def _build_preview(file_path: Path, entity: str, custom_config: dict[str, Any] | None = None) -> EntityResult:
    df, config, sheet_name = _load_entity_dataframe(file_path, entity, custom_config)
    mapping, missing = _map_columns(df, config)
    result = EntityResult(entity=config["display_name"], sheet_name=sheet_name, mapped_columns=mapping)
    result.rows_total = len(df)
    if missing:
        result.add_error(
            f"Colonnes requises manquantes pour {config['display_name']} : {', '.join(missing)}"
        )
    return result


def preview_import(
    file_path: str,
    entity: str | None = None,
    mapping_path: str | None = None,
    sample_rows: int = 5,
) -> dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    custom_config = _load_custom_config(Path(mapping_path)) if mapping_path else None
    selected_entities = [entity] if entity else DEFAULT_ENTITY_ORDER
    previews: dict[str, Any] = {}

    for current_entity in selected_entities:
        result = _build_preview(path, current_entity, custom_config)
        sample = []
        if result.mapped_columns:
            df, _, _ = _load_entity_dataframe(path, current_entity, custom_config)
            try:
                sample_df = df[list(result.mapped_columns.values())].head(sample_rows)
                sample = sample_df.where(pd.notna(sample_df), "").to_dict(orient="records")
            except Exception:
                sample = []
        previews[current_entity] = {
            "sheet_name": result.sheet_name,
            "mapped_columns": result.mapped_columns,
            "missing_fields": [field for field in ENTITY_CONFIGS[current_entity]["required_fields"] if field not in result.mapped_columns],
            "sample": sample,
            "errors": result.errors,
        }

    return previews


def _import_entity(
    file_path: Path,
    entity: str,
    session: Session,
    custom_config: dict[str, Any] | None = None,
) -> EntityResult:
    df, config, sheet_name = _load_entity_dataframe(file_path, entity, custom_config)
    mapping, missing = _map_columns(df, config)
    result = EntityResult(entity=config["display_name"], sheet_name=sheet_name, mapped_columns=mapping)
    result.rows_total = len(df)
    if missing:
        raise ImporterError(
            f"Colonnes requises manquantes pour {config['display_name']} : {', '.join(missing)}"
        )
    processor = _PROCESSORS[entity]
    # clear parent cache for this entity import to avoid stale values between entities
    _PARENT_CACHE.clear()
    for raw in df.to_dict(orient="records"):
        try:
            processor(raw, mapping, result, session)
        except ImporterError as exc:
            result.rejected += 1
            result.add_error(str(exc))
    return result


def import_fdsu(
    file_path: str,
    username: str | None = None,
    entity: str | None = None,
    mapping_path: str | None = None,
    dry_run: bool = False,
    preview: bool = False,
) -> ImportReport:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    now = datetime.now()
    username = username or os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
    selected_entities = [entity] if entity else DEFAULT_ENTITY_ORDER
    custom_config = _load_custom_config(Path(mapping_path)) if mapping_path else None
    report = ImportReport(filename=path, username=username, entity=entity or "all")
    file_hash = _hash_file(path)
    start_time = time.perf_counter()

    if preview:
        previews = preview_import(file_path, entity=entity, mapping_path=mapping_path)
        report.status = "preview"
        report.duration_seconds = time.perf_counter() - start_time
        report.summary = [f"Aperçu pour {path}"]
        for current_entity, preview_result in previews.items():
            report.summary.append(
                f"- {current_entity} : feuille={preview_result['sheet_name']}, colonnes={preview_result['mapped_columns']}"
            )
            if preview_result["errors"]:
                report.summary.extend(f"  - ERREUR: {error}" for error in preview_result["errors"])
        return report

    try:
        with Session(engine) as session:
            with session.begin():
                for current_entity in selected_entities:
                    entity_result = _import_entity(path, current_entity, session, custom_config)
                    report.add_entity_result(entity_result)
            if dry_run:
                raise ImporterError("Mode dry-run : annulation volontaire de l'import après validation")
        report.status = "success"
    except ImporterError as exc:
        if str(exc) == "Mode dry-run : annulation volontaire de l'import après validation":
            report.status = "dry-run"
        else:
            report.status = "failed"
            report.add_error(str(exc))
    except SQLAlchemyError as exc:
        report.status = "failed"
        report.add_error(f"Erreur SQLAlchemy : {exc}")
    except Exception as exc:
        report.status = "failed"
        report.add_error(f"Erreur inattendue : {exc}")

    report.duration_seconds = time.perf_counter() - start_time
    report.build_summary()
    log_path = _build_log_path(path.stem, report.entity)
    report.write_log(log_path)

    try:
        with Session(engine) as history_session:
            with history_session.begin():
                history_session.add(
                    ImportHistory(
                        filename=path.name,
                        username=username,
                        imported_at=report.started_at,
                        entity=report.entity,
                        rows_total=report.rows_total,
                        rows_inserted=report.rows_inserted,
                        rows_updated=report.rows_updated,
                        rows_rejected=report.rows_rejected,
                        duration_seconds=report.duration_seconds,
                        status=report.status,
                        summary=report.format_summary(),
                        file_hash=file_hash,
                    )
                )
    except Exception:
        pass

    return report
