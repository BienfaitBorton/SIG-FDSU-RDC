from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import func, select
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


class ImportProcessError(Exception):
    """Erreur d'import de données administratives."""


@dataclass
class ImportReport:
    entity: str
    file_path: Path
    started_at: datetime = field(default_factory=datetime.now)
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def rows_processed(self) -> int:
        return self.inserted + self.updated + self.skipped + len(self.errors)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def format_lines(self) -> list[str]:
        lines = [
            f"Import de {self.entity} : {self.file_path}",
            f"Timestamp : {self.started_at.isoformat(sep=' ', timespec='seconds')}",
            f"Résultats : insertés={self.inserted}, mis à jour={self.updated}, ignorés={self.skipped}, erreurs={len(self.errors)}",
        ]
        if self.warnings:
            lines.append("WARNINGS :")
            lines.extend([f"  - {warning}" for warning in self.warnings])
        if self.errors:
            lines.append("ERREURS :")
            lines.extend([f"  - {error}" for error in self.errors])
        return lines

    def write_log(self, log_path: Path) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as handle:
            handle.write("\n".join(self.format_lines()))


def _normalize(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,20}$")


def _normalize_code(value: Any, entity: str) -> str:
    normalized = _normalize(value)
    if not normalized:
        raise ImportProcessError(f"Code manquant pour {entity}.")
    if not _CODE_PATTERN.match(normalized):
        raise ImportProcessError(
            f"Code invalide pour {entity} : '{value}'. Utiliser uniquement lettres, chiffres, tirets ou underscores."
        )
    return normalized.upper()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _save_import_history(report: ImportReport, file_path: Path, username: str) -> None:
    try:
        with Session(engine) as history_session:
            history_session.add(
                ImportHistory(
                    filename=file_path.name,
                    username=username,
                    imported_at=report.started_at,
                    entity=report.entity,
                    rows_total=report.rows_processed,
                    rows_inserted=report.inserted,
                    rows_updated=report.updated,
                    rows_rejected=report.skipped + len(report.errors),
                    duration_seconds=(datetime.now() - report.started_at).total_seconds(),
                    status="failed" if report.errors else "success",
                    summary="\n".join(report.format_lines()),
                    file_hash=_hash_file(file_path),
                )
            )
            history_session.commit()
    except Exception:
        pass


def _parse_int(value: Any, field_name: str) -> int | None:
    normalized = _normalize(value)
    if normalized == "":
        return None
    try:
        return int(float(normalized))
    except ValueError as exc:
        raise ImportProcessError(f"Valeur invalide pour {field_name} : {value}") from exc


def _parse_float(value: Any, field_name: str) -> float | None:
    normalized = _normalize(value)
    if normalized == "":
        return None
    try:
        return float(normalized)
    except ValueError as exc:
        raise ImportProcessError(f"Valeur invalide pour {field_name} : {value}") from exc


def _read_excel(file_path: Path) -> pd.DataFrame:
    df = pd.read_excel(file_path, dtype=object)
    df.columns = [str(col).strip().lower() for col in df.columns]
    df = df.replace({pd.NA: "", None: ""})
    return df


def _ensure_columns(df: pd.DataFrame, required_columns: set[str], entity: str) -> None:
    missing = required_columns.difference(df.columns)
    if missing:
        raise ImportProcessError(
            f"Le fichier {entity} doit contenir les colonnes : {', '.join(sorted(required_columns))}. Colonnes manquantes : {', '.join(sorted(missing))}."
        )


def _detect_duplicates(df: pd.DataFrame, subset: list[str], entity: str) -> None:
    duplicated = df[df.duplicated(subset=subset, keep=False)]
    if not duplicated.empty:
        rows = duplicated.to_dict(orient="records")
        details = "; ".join(
            [", ".join(f"{key}={row[key]}" for key in subset) for row in rows]
        )
        raise ImportProcessError(
            f"Doublons détectés dans le fichier {entity} pour les clés {subset} : {details}"
        )


def _build_log_path(entity: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOG_DIR / f"{timestamp}_{entity}_import.log"


def import_provinces(file_path: str) -> ImportReport:
    file_path = Path(file_path)
    report = ImportReport(entity="Provinces", file_path=file_path)
    df = _read_excel(file_path)
    required = {"code", "nom", "zone"}
    _ensure_columns(df, required, report.entity)
    _detect_duplicates(df, ["code"], report.entity)
    _detect_duplicates(df, ["nom"], report.entity)

    with Session(engine) as session:
        with session.begin():
            for raw in df.to_dict(orient="records"):
                try:
                    code = _normalize_code(raw.get("code"), "province")
                except ImportProcessError as exc:
                    report.add_error(str(exc))
                    continue
                nom = _normalize(raw.get("nom"))
                zone = _normalize(raw.get("zone"))
                chef_lieu = _normalize(raw.get("chef_lieu"))
                population = _parse_int(raw.get("population"), "population")
                superficie = _parse_float(raw.get("superficie"), "superficie")

                if not code or not nom or not zone:
                    raise ImportProcessError(
                        f"Ligne incomplète : code, nom et zone sont requis. Valeurs : code={code}, nom={nom}, zone={zone}"
                    )

                province = session.scalar(select(Province).where(Province.code == code))
                if province is not None:
                    if province.nom != nom:
                        same_nom = session.scalar(select(Province).where(Province.nom == nom, Province.code != code))
                        if same_nom is not None:
                            raise ImportProcessError(
                                f"Incohérence : un autre province utilise déjà le nom '{nom}' avec le code '{same_nom.code}'"
                            )
                    province.nom = nom
                    province.zone = zone
                    province.chef_lieu = chef_lieu or None
                    province.population = population
                    province.superficie = superficie
                    report.updated += 1
                else:
                    if session.scalar(select(Province).where(Province.nom == nom)) is not None:
                        raise ImportProcessError(
                            f"Incohérence : le nom de province '{nom}' existe déjà avec un autre code"
                        )
                    province = Province(
                        code=code,
                        nom=nom,
                        zone=zone,
                        chef_lieu=chef_lieu or None,
                        population=population,
                        superficie=superficie,
                    )
                    session.add(province)
                    report.inserted += 1

    report.write_log(_build_log_path("provinces"))
    _save_import_history(report, file_path, username="system")
    return report


def import_territoires(file_path: str) -> ImportReport:
    file_path = Path(file_path)
    report = ImportReport(entity="Territoires", file_path=file_path)
    df = _read_excel(file_path)
    required = {"code", "nom", "province_code"}
    _ensure_columns(df, required, report.entity)
    _detect_duplicates(df, ["code", "province_code"], report.entity)

    with Session(engine) as session:
        with session.begin():
            for raw in df.to_dict(orient="records"):
                try:
                    code = _normalize_code(raw.get("code"), "territoire")
                except ImportProcessError as exc:
                    report.add_error(str(exc))
                    continue
                nom = _normalize(raw.get("nom"))
                chef_lieu = _normalize(raw.get("chef_lieu"))
                province_code = _normalize(raw.get("province_code"))

                if not code or not nom or not province_code:
                    raise ImportProcessError(
                        f"Ligne incomplète : code, nom et province_code sont requis. Valeurs : code={code}, nom={nom}, province_code={province_code}"
                    )

                province = session.scalar(select(Province).where(Province.code == province_code))
                if province is None:
                    raise ImportProcessError(
                        f"Incohérence hiérarchique : la province '{province_code}' est introuvable pour le territoire '{code}'"
                    )

                territoire = session.scalar(
                    select(Territoire).where(
                        Territoire.code == code,
                        Territoire.province_id == province.id,
                    )
                )
                if territoire is not None:
                    territoire.nom = nom
                    territoire.chef_lieu = chef_lieu or None
                    report.updated += 1
                else:
                    if session.scalar(
                        select(Territoire).where(
                            Territoire.nom == nom,
                            Territoire.province_id == province.id,
                        )
                    ) is not None:
                        raise ImportProcessError(
                            f"Incohérence : le nom de territoire '{nom}' existe déjà pour la province '{province_code}'"
                        )
                    territoire = Territoire(
                        code=code,
                        nom=nom,
                        chef_lieu=chef_lieu or None,
                        province_id=province.id,
                    )
                    session.add(territoire)
                    report.inserted += 1

    report.write_log(_build_log_path("territoires"))
    _save_import_history(report, file_path, username="system")
    return report


def import_collectivites(file_path: str) -> ImportReport:
    file_path = Path(file_path)
    report = ImportReport(entity="Collectivites", file_path=file_path)
    df = _read_excel(file_path)
    required = {"code", "nom", "type_collectivite", "territoire_code"}
    _ensure_columns(df, required, report.entity)
    _detect_duplicates(df, ["code", "territoire_code"], report.entity)

    with Session(engine) as session:
        with session.begin():
            for raw in df.to_dict(orient="records"):
                try:
                    code = _normalize_code(raw.get("code"), "collectivite")
                except ImportProcessError as exc:
                    report.add_error(str(exc))
                    continue
                nom = _normalize(raw.get("nom"))
                type_value = _normalize(raw.get("type_collectivite"))
                territoire_code = _normalize(raw.get("territoire_code"))
                chef_lieu = _normalize(raw.get("chef_lieu"))

                if not code or not nom or not type_value or not territoire_code:
                    raise ImportProcessError(
                        f"Ligne incomplète : code, nom, type_collectivite et territoire_code sont requis."
                    )

                try:
                    type_collectivite = CollectiviteType(type_value)
                except ValueError as exc:
                    raise ImportProcessError(
                        f"Type de collectivité invalide : {type_value}. Valeurs acceptées : {', '.join([item.value for item in CollectiviteType])}"
                    ) from exc

                territoire = session.scalar(select(Territoire).where(Territoire.code == territoire_code))
                if territoire is None:
                    raise ImportProcessError(
                        f"Incohérence hiérarchique : le territoire '{territoire_code}' est introuvable pour la collectivité '{code}'"
                    )

                collectivite = session.scalar(
                    select(Collectivite).where(
                        Collectivite.code == code,
                        Collectivite.territoire_id == territoire.id,
                    )
                )
                if collectivite is not None:
                    collectivite.nom = nom
                    collectivite.type_collectivite = type_collectivite
                    collectivite.chef_lieu = chef_lieu or None
                    report.updated += 1
                else:
                    collectivite = Collectivite(
                        code=code,
                        nom=nom,
                        type_collectivite=type_collectivite,
                        chef_lieu=chef_lieu or None,
                        territoire_id=territoire.id,
                    )
                    session.add(collectivite)
                    report.inserted += 1

    report.write_log(_build_log_path("collectivites"))
    _save_import_history(report, file_path, username="system")
    return report


def import_groupements(file_path: str) -> ImportReport:
    file_path = Path(file_path)
    report = ImportReport(entity="Groupements", file_path=file_path)
    df = _read_excel(file_path)
    required = {"code", "nom", "collectivite_code"}
    _ensure_columns(df, required, report.entity)
    _detect_duplicates(df, ["code", "collectivite_code"], report.entity)

    with Session(engine) as session:
        with session.begin():
            for raw in df.to_dict(orient="records"):
                try:
                    code = _normalize_code(raw.get("code"), "groupement")
                except ImportProcessError as exc:
                    report.add_error(str(exc))
                    continue
                nom = _normalize(raw.get("nom"))
                collectivite_code = _normalize(raw.get("collectivite_code"))
                chef_lieu = _normalize(raw.get("chef_lieu"))

                if not code or not nom or not collectivite_code:
                    raise ImportProcessError(
                        f"Ligne incomplète : code, nom et collectivite_code sont requis."
                    )

                collectivite = session.scalar(select(Collectivite).where(Collectivite.code == collectivite_code))
                if collectivite is None:
                    raise ImportProcessError(
                        f"Incohérence hiérarchique : la collectivité '{collectivite_code}' est introuvable pour le groupement '{code}'"
                    )

                groupement = session.scalar(
                    select(Groupement).where(
                        Groupement.code == code,
                        Groupement.collectivite_id == collectivite.id,
                    )
                )
                if groupement is not None:
                    groupement.nom = nom
                    groupement.chef_lieu = chef_lieu or None
                    report.updated += 1
                else:
                    groupement = Groupement(
                        code=code,
                        nom=nom,
                        chef_lieu=chef_lieu or None,
                        collectivite_id=collectivite.id,
                    )
                    session.add(groupement)
                    report.inserted += 1

    report.write_log(_build_log_path("groupements"))
    _save_import_history(report, file_path, username="system")
    return report


def import_villages(file_path: str) -> ImportReport:
    file_path = Path(file_path)
    report = ImportReport(entity="Villages", file_path=file_path)
    df = _read_excel(file_path)
    required = {"code", "nom", "groupement_code"}
    _ensure_columns(df, required, report.entity)
    _detect_duplicates(df, ["code", "groupement_code"], report.entity)

    with Session(engine) as session:
        with session.begin():
            for raw in df.to_dict(orient="records"):
                try:
                    code = _normalize_code(raw.get("code"), "village")
                except ImportProcessError as exc:
                    report.add_error(str(exc))
                    continue
                nom = _normalize(raw.get("nom"))
                groupement_code = _normalize(raw.get("groupement_code"))
                chef_lieu = _normalize(raw.get("chef_lieu"))

                if not code or not nom or not groupement_code:
                    raise ImportProcessError(
                        f"Ligne incomplète : code, nom et groupement_code sont requis."
                    )

                groupement = session.scalar(select(Groupement).where(Groupement.code == groupement_code))
                if groupement is None:
                    raise ImportProcessError(
                        f"Incohérence hiérarchique : le groupement '{groupement_code}' est introuvable pour le village '{code}'"
                    )

                village = session.scalar(
                    select(Village).where(
                        Village.code == code,
                        Village.groupement_id == groupement.id,
                    )
                )
                if village is not None:
                    village.nom = nom
                    village.chef_lieu = chef_lieu or None
                    report.updated += 1
                else:
                    village = Village(
                        code=code,
                        nom=nom,
                        chef_lieu=chef_lieu or None,
                        groupement_id=groupement.id,
                    )
                    session.add(village)
                    report.inserted += 1

    report.write_log(_build_log_path("villages"))
    _save_import_history(report, file_path, username="system")
    return report
