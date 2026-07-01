from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine, tables_exist
from app.models import Province, Territoire, ImportHistory
from app.fdsu_importer import ImportReport


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
        return (
            "=========================================\n"
            "IMPORT FDSU TERMINÉ\n"
            "=========================================\n"
            f"Fichier : {self.filename}\n"
            f"Provinces créées : {self.provinces_created}\n"
            f"Provinces mises à jour : {self.provinces_updated}\n"
            f"Territoires créés : {self.territories_created}\n"
            f"Territoires mis à jour : {self.territories_updated}\n"
            f"Lignes ignorées : {self.rows_ignored}\n"
            f"Erreurs : {len(self.errors)}\n"
            f"Durée : {self.duration_seconds:.2f} secondes\n"
            "========================================="
        )


class FDSUStructureImporter:
    """Importer for 'FDSU Structure code Territoire zones.xlsx' official file.

    Reads sheets: ND, SD, CE, OT, ET and imports provinces and territoires.
    """

    SHEETS = ["ND", "SD", "CE", "OT", "ET"]

    # candidate headers for detection
    HEADER_CANDIDATES = {
        "zone": ["zone", "zone_fdsu", "zone fdsu"],
        "province_name": ["province", "province_name", "nom_province", "nom province"],
        "province_code": ["code_province", "prov_code", "code province", "code"],
        "territoire_name": ["territoire", "territoire_name", "nom_territoire"],
        "territoire_code": ["code_territoire", "terr_code", "code territoire"],
        "sites_gsm": ["sites_gsm", "nb_sites_gsm", "nombre_sites_gsm", "sites gsm", "gsm_sites"],
    }

    def __init__(self, username: str = "system") -> None:
        self.username = username

    @staticmethod
    def _norm(s: Optional[str]) -> str:
        if s is None:
            return ""
        return str(s).strip().lower().replace("\n", " ").replace("\r", " ")

    def _detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        cols = list(df.columns)
        norm = {self._norm(c): c for c in cols}
        mapping: Dict[str, str] = {}
        for key, candidates in self.HEADER_CANDIDATES.items():
            for cand in candidates:
                n = cand.replace(" ", "").lower()
                for nc, original in norm.items():
                    if n in nc.replace(" ", "") or nc.replace(" ", "") in n:
                        mapping[key] = original
                        break
                if key in mapping:
                    break
        return mapping

    def import_file(self, path: Path) -> StructureReport:
        start = time.time()
        report = StructureReport(filename=path.name)

        if not path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {path}")

        ext = path.suffix.lower()
        if ext not in {".xlsx", ".xls"}:
            raise ValueError(
                "Format de fichier invalide. Le fichier doit être un .xlsx ou .xls officiel "
                f"(fichier fourni : {path.name})."
            )

        file_hash = self._hash_file(path)

        try:
            if ext == ".xlsx":
                xls = pd.read_excel(path, sheet_name=None, engine="openpyxl")
            else:
                raise ValueError(
                    "Le format .xls n'est pas supporté par cet importeur officiel. "
                    "Veuillez convertir le fichier en .xlsx et réessayer."
                )
        except ImportError as exc:
            if "openpyxl" in str(exc).lower():
                raise ImportError(
                    "Le moteur openpyxl est requis pour lire les fichiers .xlsx. "
                    "Installez-le avec `pip install openpyxl`."
                ) from exc
            raise

        sheets = [s for s in self.SHEETS if s in xls]
        report.sheets_processed = sheets

        seen = set()  # to ignore duplicates in file based on province_code+territoire_code

        with Session(engine) as session:
            # Ensure required tables are present before attempting import.
            missing = [t for t, ok in tables_exist(["provinces", "territoires"]).items() if not ok]
            if missing:
                raise RuntimeError(
                    f"Required database tables are missing: {missing}.\n"
                    "Initialize the database schema before running the importer.\n"
                    "Options: run alembic migrations, or run scripts/init_db.py to create tables for development."
                )
            with session.begin():
                for sheet in sheets:
                    df = xls[sheet]
                    mapping = self._detect_columns(df)
                    for idx, row in df.iterrows():
                        report.rows_total += 1
                        try:
                            province_name = row.get(mapping.get("province_name"))
                            province_code = row.get(mapping.get("province_code"))
                            zone = row.get(mapping.get("zone"))
                            territoire_name = row.get(mapping.get("territoire_name"))
                            territoire_code = row.get(mapping.get("territoire_code"))
                            sites_gsm = row.get(mapping.get("sites_gsm"))

                            if pd.isna(province_code) and pd.isna(province_name):
                                report.rows_ignored += 1
                                continue

                            prov_code = str(province_code).strip().upper() if not pd.isna(province_code) else None
                            terr_code = str(territoire_code).strip().upper() if not pd.isna(territoire_code) else None

                            key = (prov_code or "") + "|" + (terr_code or "")
                            if key in seen:
                                report.rows_ignored += 1
                                continue
                            seen.add(key)

                            # provinces
                            if prov_code:
                                existing_prov = session.scalar(select(Province).where(Province.code == prov_code))
                            else:
                                existing_prov = None

                            if existing_prov:
                                # update
                                updated = False
                                if province_name and existing_prov.nom != province_name:
                                    existing_prov.nom = province_name
                                    updated = True
                                if zone and existing_prov.zone != zone:
                                    existing_prov.zone = str(zone)
                                    updated = True
                                if updated:
                                    session.add(existing_prov)
                                    report.provinces_updated += 1
                                prov_id = existing_prov.id
                            else:
                                # create
                                new_code = prov_code or (province_name and province_name[:5].upper().replace(' ', '_'))
                                prov = Province(code=str(new_code), nom=str(province_name) if province_name else str(new_code), zone=str(zone) if zone else "")
                                session.add(prov)
                                session.flush()
                                report.provinces_created += 1
                                prov_id = prov.id

                            # territoires
                            if terr_code:
                                existing_terr = session.scalar(select(Territoire).where(Territoire.code == terr_code, Territoire.province_id == prov_id))
                            else:
                                existing_terr = None

                            if existing_terr:
                                updated = False
                                if territoire_name and existing_terr.nom != territoire_name:
                                    existing_terr.nom = territoire_name
                                    updated = True
                                # accumulate sites_gsm
                                try:
                                    nb = int(sites_gsm) if not pd.isna(sites_gsm) else 0
                                except Exception:
                                    nb = 0
                                # update stored value
                                existing_nb = int(existing_terr.nb_sites_reference or 0)
                                existing_terr.nb_sites_reference = existing_nb + nb
                                updated = True
                                if updated:
                                    session.add(existing_terr)
                                    report.territories_updated += 1
                            else:
                                # create territory
                                terr = Territoire(code=str(terr_code) if terr_code else str(int(time.time())), nom=str(territoire_name) if territoire_name else (terr_code or ""), province_id=prov_id, nb_sites_reference=(int(sites_gsm) if not pd.isna(sites_gsm) else 0))
                                session.add(terr)
                                session.flush()
                                report.territories_created += 1
                            # record sites_gsm for report (also used by API)
                            if terr_code:
                                try:
                                    nb = int(sites_gsm) if not pd.isna(sites_gsm) else 0
                                except Exception:
                                    nb = 0
                                report.territory_sites[f"{prov_code}|{terr_code}"] = report.territory_sites.get(f"{prov_code}|{terr_code}", 0) + nb
                        except Exception as exc:
                            report.errors.append({"row": int(idx) + 1, "error": str(exc)})

        report.duration_seconds = time.time() - start

        # persist import history using the readable summary text
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
        import hashlib

        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
