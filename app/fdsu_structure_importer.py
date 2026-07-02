from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine, tables_exist
from app.models import ImportHistory, Province, Territoire


@dataclass
class StructureReport:
    filename: str
    sheets_processed: List[str] = field(default_factory=list)
    provinces_created: int = 0
    provinces_updated: int = 0
    territories_created: int = 0
    territories_updated: int = 0
    rows_total: int = 0
    rows_ignored: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    territory_sites: Dict[str, int] = field(default_factory=dict)
    duration_seconds: float = 0.0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "sheets_processed": self.sheets_processed,
            "provinces_created": self.provinces_created,
            "provinces_updated": self.provinces_updated,
            "territories_created": self.territories_created,
            "territories_updated": self.territories_updated,
            "rows_total": self.rows_total,
            "rows_ignored": self.rows_ignored,
            "errors": self.errors,
            "territory_sites": self.territory_sites,
            "duration_seconds": self.duration_seconds,
        }

    def summary_text(self) -> str:
        errors = "\n".join(
            f"- Feuille {err.get('sheet', '-')}, ligne {err.get('row', '-')}: {err.get('error')}"
            for err in self.errors
        )
        return (
            "=========================================\n"
            "IMPORT FDSU TERMINE\n"
            "=========================================\n"
            f"Fichier : {self.filename}\n"
            f"Feuilles importees : {', '.join(self.sheets_processed) if self.sheets_processed else 'aucune'}\n"
            f"Lignes lues : {self.rows_total}\n"
            f"Provinces creees : {self.provinces_created}\n"
            f"Provinces mises a jour : {self.provinces_updated}\n"
            f"Territoires crees : {self.territories_created}\n"
            f"Territoires mis a jour : {self.territories_updated}\n"
            f"Lignes ignorees : {self.rows_ignored}\n"
            f"Erreurs : {len(self.errors)}\n"
            f"{errors + chr(10) if errors else ''}"
            f"Duree : {self.duration_seconds:.2f} secondes\n"
            "========================================="
        )


class FDSUStructureImporter:
    """Importer for the official FDSU structure Excel file."""

    SHEETS = ["ZONE ND", "ZONE SD", "ZONE CE", "ZONE OT", "ZONE ET"]
    SHEET_ZONES = {
        "ZONE ND": "ND",
        "ZONE SD": "SD",
        "ZONE CE": "CE",
        "ZONE OT": "OT",
        "ZONE ET": "ET",
    }
    REQUIRED_COLUMNS = {
        "province_code",
        "province_name",
        "territoire_code",
        "territoire_name",
        "nb_sites_reference",
    }
    COLUMN_MAPPING = {
        "N°": "province_code",
        "NO": "province_code",
        "N": "province_code",
        "PROVINCE": "province_name",
        "CODE": "territoire_code",
        "TOWN/TERRITORY": "territoire_name",
        "NOMBRE DES SITES GSM": "nb_sites_reference",
    }

    def __init__(self, username: str = "system") -> None:
        self.username = username

    @staticmethod
    def _normalize_spaces(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _normalize_sheet_name(cls, value: Any) -> str:
        return cls._normalize_spaces(str(value)).upper()

    @classmethod
    def _normalize_header(cls, value: Any) -> str:
        return cls._normalize_spaces(str(value)).upper()

    @staticmethod
    def _is_blank(value: Any) -> bool:
        return value is None or pd.isna(value) or str(value).strip() == ""

    @classmethod
    def _text(cls, value: Any) -> str | None:
        if cls._is_blank(value):
            return None
        return cls._normalize_spaces(str(value))

    @classmethod
    def _code(cls, value: Any, width: int) -> str | None:
        text = cls._text(value)
        if text is None:
            return None
        if text.endswith(".0"):
            text = text[:-2]
        return text.upper().zfill(width)

    @staticmethod
    def _int_value(value: Any) -> int:
        if value is None or pd.isna(value):
            return 0
        try:
            return int(value)
        except Exception:
            try:
                return int(float(str(value).strip()))
            except Exception:
                return 0

    def _sheet_map(self, xls: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        normalized = {self._normalize_sheet_name(name): name for name in xls}
        return {sheet: normalized[sheet] for sheet in self.SHEETS if sheet in normalized}

    def _detect_header(self, raw: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, int], List[str]]:
        mapping: Dict[str, int] = {}
        header_row_index = None

        for idx, row in raw.iterrows():
            row_mapping: Dict[str, int] = {}
            for col_idx, value in row.items():
                target = self.COLUMN_MAPPING.get(self._normalize_header(value))
                if target is not None:
                    row_mapping[target] = int(col_idx)
            if {"province_name", "territoire_name", "territoire_code"}.issubset(row_mapping):
                mapping = row_mapping
                header_row_index = int(idx)
                break

        if header_row_index is None:
            return pd.DataFrame(), {}, sorted(self.REQUIRED_COLUMNS)

        missing = sorted(self.REQUIRED_COLUMNS.difference(mapping))
        data = raw.iloc[header_row_index + 1 :].reset_index(drop=True)
        return data, mapping, missing

    def import_file(self, path: Path) -> StructureReport:
        start = time.time()
        report = StructureReport(filename=path.name)

        if not path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {path}")

        ext = path.suffix.lower()
        if ext not in {".xlsx", ".xls"}:
            raise ValueError(
                "Format de fichier invalide. Le fichier doit etre un .xlsx ou .xls officiel "
                f"(fichier fourni : {path.name})."
            )

        file_hash = self._hash_file(path)

        try:
            if ext == ".xlsx":
                xls = pd.read_excel(path, sheet_name=None, engine="openpyxl", header=None, dtype=object)
            else:
                raise ValueError(
                    "Le format .xls n'est pas supporte par cet importeur officiel. "
                    "Veuillez convertir le fichier en .xlsx et reessayer."
                )
        except ImportError as exc:
            if "openpyxl" in str(exc).lower():
                raise ImportError(
                    "Le moteur openpyxl est requis pour lire les fichiers .xlsx. "
                    "Installez-le avec `pip install openpyxl`."
                ) from exc
            raise

        sheets = self._sheet_map(xls)
        report.sheets_processed = list(sheets.values())

        for expected in self.SHEETS:
            if expected not in sheets:
                report.errors.append(
                    {
                        "sheet": expected,
                        "row": None,
                        "error": f"Feuille obligatoire manquante : {expected}",
                    }
                )

        seen = set()

        with Session(engine) as session:
            missing = [t for t, ok in tables_exist(["provinces", "territoires"]).items() if not ok]
            if missing:
                raise RuntimeError(
                    f"Required database tables are missing: {missing}.\n"
                    "Initialize the database schema before running the importer.\n"
                    "Options: run alembic migrations, or run scripts/init_db.py to create tables for development."
                )
            with session.begin():
                for normalized_sheet, sheet in sheets.items():
                    zone = self.SHEET_ZONES[normalized_sheet]
                    df, mapping, missing_columns = self._detect_header(xls[sheet])
                    if missing_columns:
                        for missing_column in missing_columns:
                            report.errors.append(
                                {
                                    "sheet": sheet,
                                    "row": None,
                                    "error": f"Colonne obligatoire manquante : {missing_column}",
                                }
                            )
                        continue

                    current_prov_id = None
                    current_prov_code = None

                    for idx, row in df.iterrows():
                        report.rows_total += 1
                        try:
                            province_name = self._text(row.get(mapping["province_name"]))
                            province_code = self._code(row.get(mapping["province_code"]), 2)
                            territoire_name = self._text(row.get(mapping["territoire_name"]))
                            territoire_code = self._code(row.get(mapping["territoire_code"]), 3)
                            nb_sites_reference = self._int_value(row.get(mapping["nb_sites_reference"]))

                            if not province_code and not province_name and not territoire_code and not territoire_name:
                                report.rows_ignored += 1
                                continue

                            if province_code in self.SHEET_ZONES and not province_name and not territoire_code and not territoire_name:
                                report.rows_ignored += 1
                                continue

                            is_province_row = bool(province_code and province_name)
                            prov_code = province_code if is_province_row else current_prov_code
                            terr_code = territoire_code

                            if not prov_code:
                                report.rows_ignored += 1
                                report.errors.append(
                                    {
                                        "sheet": sheet,
                                        "row": int(idx) + 1,
                                        "error": "Province introuvable pour cette ligne",
                                    }
                                )
                                continue

                            key = f"{prov_code}|{terr_code or ''}|{province_name or ''}"
                            if key in seen:
                                report.rows_ignored += 1
                                continue
                            seen.add(key)

                            existing_prov = session.scalar(select(Province).where(Province.code == prov_code))
                            if existing_prov:
                                updated = False
                                if is_province_row and province_name and existing_prov.nom != province_name:
                                    existing_prov.nom = province_name
                                    updated = True
                                if existing_prov.zone != zone:
                                    existing_prov.zone = zone
                                    updated = True
                                if updated:
                                    session.add(existing_prov)
                                    report.provinces_updated += 1
                                prov_id = existing_prov.id
                            elif is_province_row:
                                prov = Province(code=prov_code, nom=province_name or prov_code, zone=zone)
                                session.add(prov)
                                session.flush()
                                report.provinces_created += 1
                                prov_id = prov.id
                            else:
                                prov_id = current_prov_id

                            current_prov_id = prov_id
                            current_prov_code = prov_code

                            if not terr_code or not territoire_name:
                                if not is_province_row:
                                    report.rows_ignored += 1
                                continue

                            existing_terr = session.scalar(
                                select(Territoire).where(
                                    Territoire.code == terr_code,
                                    Territoire.province_id == prov_id,
                                )
                            )
                            if existing_terr:
                                updated = False
                                if existing_terr.nom != territoire_name:
                                    existing_terr.nom = territoire_name
                                    updated = True
                                if int(existing_terr.nb_sites_reference or 0) != nb_sites_reference:
                                    existing_terr.nb_sites_reference = nb_sites_reference
                                    updated = True
                                if updated:
                                    session.add(existing_terr)
                                    report.territories_updated += 1
                            else:
                                terr = Territoire(
                                    code=terr_code,
                                    nom=territoire_name,
                                    province_id=prov_id,
                                    nb_sites_reference=nb_sites_reference,
                                )
                                session.add(terr)
                                session.flush()
                                report.territories_created += 1

                            report.territory_sites[f"{prov_code}|{terr_code}"] = nb_sites_reference
                        except Exception as exc:
                            report.errors.append({"sheet": sheet, "row": int(idx) + 1, "error": str(exc)})

        report.duration_seconds = time.time() - start

        readable_summary = report.summary_text()
        with Session(engine) as history_session:
            history = ImportHistory(
                filename=path.name,
                username=self.username,
                imported_at=datetime.utcnow(),
                entity="fdsu_structure",
                rows_total=report.rows_total,
                rows_inserted=report.provinces_created + report.territories_created,
                rows_updated=report.provinces_updated + report.territories_updated,
                rows_rejected=len(report.errors),
                duration_seconds=report.duration_seconds,
                status="completed" if not report.errors else "partial",
                summary=readable_summary,
                file_hash=file_hash,
            )
            history_session.add(history)
            history_session.commit()

        return report

    @staticmethod
    def _hash_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
