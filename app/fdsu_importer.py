from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import (
    Province,
    Territoire,
    Collectivite,
    Groupement,
    Village,
    Site,
    ImportHistory,
)


@dataclass
class ImportReport:
    filename: str
    entity: str
    rows_total: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_rejected: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "entity": self.entity,
            "rows_total": self.rows_total,
            "rows_inserted": self.rows_inserted,
            "rows_updated": self.rows_updated,
            "rows_rejected": self.rows_rejected,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds,
        }


class FDSUExcelImporter:
    """Moteur d'import spécifique aux fichiers Excel officiels FDSU.

    Usage:
        importer = FDSUExcelImporter(username="admin")
        report = importer.import_file(Path("/tmp/fdsu_provinces.xlsx"), entity="province", mapping_json=Path("mapping.json"))
    """

    # canonical fields we support for automatic detection / mapping
    CANONICAL_FIELDS = {
        "province_code": ["province_code", "code_province", "prov_code", "code"],
        "province_name": ["province", "province_name", "nom_province", "nom"],
        "province_zone": ["zone", "zone_fdsu"],

        "territoire_code": ["territoire_code", "code_territoire"],
        "territoire_name": ["territoire", "territoire_name", "nom_territoire"],

        "collectivite_code": ["collectivite_code", "code_collectivite", "collectivite_code"],
        "collectivite_name": ["collectivite", "collectivite_name", "nom_collectivite"],
        "collectivite_type": ["type_collectivite", "collectivite_type"],

        "groupement_code": ["groupement_code", "code_groupement"],
        "groupement_name": ["groupement", "groupement_name", "nom_groupement"],

        "village_code": ["village_code", "code_village"],
        "village_name": ["village", "village_name", "nom_village"],

        # site specific
        "site_name": ["site", "site_name", "nom_site"],
        "site_code": ["code_site", "site_code"],
        "latitude": ["lat", "latitude"],
        "longitude": ["lon", "longitude", "long"],
        "statut": ["statut", "status"],
        "type_site": ["type", "type_site"],
    }

    def __init__(self, username: str = "system") -> None:
        self.username = username

    @staticmethod
    def _normalize(text: Optional[str]) -> str:
        if text is None:
            return ""
        txt = str(text).strip().lower()
        txt = unicodedata.normalize("NFKD", txt)
        txt = re.sub(r"[^a-z0-9]+", "", txt)
        return txt

    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Attempt to detect columns mapping from DataFrame headers to canonical fields.

        Returns mapping canonical_field -> df_column_name
        """
        cols = list(df.columns)
        norm_cols = {self._normalize(c): c for c in cols}
        mapping: Dict[str, str] = {}
        for canon, candidates in self.CANONICAL_FIELDS.items():
            found = None
            for cand in candidates:
                n = self._normalize(cand)
                # exact match
                if n in norm_cols:
                    found = norm_cols[n]
                    break
            if found is None:
                # try partial token matching
                for ncol, original in norm_cols.items():
                    for cand in candidates:
                        if cand.replace("_", "") in ncol or ncol in cand:
                            found = original
                            break
                    if found:
                        break
            if found:
                mapping[canon] = found
        return mapping

    def load_mapping(self, mapping_json: Path) -> Dict[str, str]:
        with open(mapping_json, "r", encoding="utf-8") as fh:
            return json.load(fh)

    @staticmethod
    def _hash_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _validate_required(self, row: Dict[str, Any], required: List[str]) -> List[str]:
        errs: List[str] = []
        for field in required:
            if not row.get(field) and row.get(field) != 0:
                errs.append(f"Champ requis manquant: {field}")
        return errs

    def import_file(self, path: Path, entity: str, mapping_json: Optional[Path] = None, create_parents: bool = False) -> ImportReport:
        """Import a FDSU Excel file for a given entity (province|territoire|collectivite|groupement|village|site).

        mapping_json: optional Path to a JSON mapping file where keys are canonical fields and values are column names.
        """
        start = time.time()
        df = pd.read_excel(path)
        report = ImportReport(filename=path.name, entity=entity)
        report.rows_total = len(df)

        # determine mapping
        if mapping_json and mapping_json.exists():
            mapping = self.load_mapping(mapping_json)
        else:
            mapping = self.detect_columns(df)

        file_hash = self._hash_file(path)

        # set behavior for parent creation during this import
        self._create_parents = bool(create_parents)

        # basic duplicate check inside file (by code if available)
        code_field = None
        if entity == "province":
            code_field = mapping.get("province_code")
        elif entity == "territoire":
            code_field = mapping.get("territoire_code")
        elif entity == "collectivite":
            code_field = mapping.get("collectivite_code")
        elif entity == "groupement":
            code_field = mapping.get("groupement_code")
        elif entity == "village":
            code_field = mapping.get("village_code")
        elif entity == "site":
            code_field = mapping.get("site_code")

        seen_codes = set()

        with Session(engine) as session:
            with session.begin():
                for idx, row in df.iterrows():
                    rnum = int(idx) + 1
                    row_dict = {c: (None if pd.isna(v) else v) for c, v in row.items()}

                    # duplicate in file
                    code_val = row_dict.get(code_field) if code_field else None
                    if code_val is not None:
                        code_key = str(code_val).strip()
                        if code_key in seen_codes:
                            report.rows_rejected += 1
                            report.errors.append({"row": rnum, "error": "Doublon dans le fichier (même code)"})
                            continue
                        seen_codes.add(code_key)

                    try:
                        if entity == "province":
                            self._process_province_row(row_dict, mapping, report, session)
                        elif entity == "territoire":
                            self._process_territoire_row(row_dict, mapping, report, session)
                        elif entity == "collectivite":
                            self._process_collectivite_row(row_dict, mapping, report, session)
                        elif entity == "groupement":
                            self._process_groupement_row(row_dict, mapping, report, session)
                        elif entity == "village":
                            self._process_village_row(row_dict, mapping, report, session)
                        elif entity == "site":
                            self._process_site_row(row_dict, mapping, report, session)
                        else:
                            raise ValueError(f"Entity non supportée: {entity}")
                    except Exception as exc:
                        report.rows_rejected += 1
                        report.errors.append({"row": rnum, "error": str(exc)})

        report.duration_seconds = time.time() - start
        # save import history
        status = "completed" if report.rows_rejected == 0 else "partial"
        summary = json.dumps(report.as_dict(), ensure_ascii=False)
        with Session(engine) as history_session:
            history = ImportHistory(
                filename=path.name,
                username=self.username,
                imported_at=datetime.utcnow(),
                entity=entity,
                rows_total=report.rows_total,
                rows_inserted=report.rows_inserted,
                rows_updated=report.rows_updated,
                rows_rejected=report.rows_rejected,
                duration_seconds=report.duration_seconds,
                status=status,
                summary=summary,
                file_hash=file_hash,
            )
            history_session.add(history)
            history_session.commit()

        return report

    # --- processors for each entity ---
    def _process_province_row(self, row: Dict[str, Any], mapping: Dict[str, str], report: ImportReport, session: Session) -> None:
        code = str(row.get(mapping.get("province_code"), "")).strip().upper()
        nom = row.get(mapping.get("province_name"))
        zone = row.get(mapping.get("province_zone")) or ""
        if not code or not nom:
            raise ValueError("Province: code ou nom manquant")

        existing = session.scalar(select(Province).where(Province.code == code))
        if existing:
            existing.nom = nom
            existing.zone = zone
            session.add(existing)
            report.rows_updated += 1
            return

        # ensure no same name with different code
        if session.scalar(select(Province).where(Province.nom == nom)) is not None:
            raise ValueError("Province: même nom existe avec un code différent")

        prov = Province(code=code, nom=nom, zone=zone)
        session.add(prov)
        report.rows_inserted += 1

    def _find_parent_id(self, session: Session, model, code_value: Optional[str], code_field_name: str = "code") -> Optional[int]:
        if not code_value:
            return None
        code_value = str(code_value).strip().upper()
        parent = session.scalar(select(model).where(getattr(model, code_field_name) == code_value))
        return parent.id if parent is not None else None

    def _create_province(self, session: Session, code: str, name: Optional[str] = None, zone: Optional[str] = None) -> int:
        prov = Province(code=str(code).strip().upper(), nom=name or str(code), zone=zone or "")
        session.add(prov)
        session.flush()
        return prov.id

    def _create_territoire(self, session: Session, code: str, name: Optional[str], province_code: str) -> int:
        prov_id = self._find_parent_id(session, Province, province_code)
        if prov_id is None:
            # try to create province if allowed
            if getattr(self, "_create_parents", False):
                prov_name = None
                session.flush()
                prov_id = self._create_province(session, province_code, prov_name)
            else:
                raise ValueError("Cannot create Territoire: parent Province missing")
        territoire = Territoire(code=str(code).strip().upper(), nom=name or str(code), province_id=prov_id)
        session.add(territoire)
        session.flush()
        return territoire.id

    def _process_territoire_row(self, row: Dict[str, Any], mapping: Dict[str, str], report: ImportReport, session: Session) -> None:
        code = str(row.get(mapping.get("territoire_code"), "")).strip().upper()
        nom = row.get(mapping.get("territoire_name"))
        prov_code = row.get(mapping.get("province_code"))
        if not code or not nom or not prov_code:
            raise ValueError("Territoire: code, nom ou code province manquant")
        province_id = self._find_parent_id(session, Province, prov_code)
        if province_id is None:
            if getattr(self, "_create_parents", False):
                prov_name = row.get(mapping.get("province_name"))
                province_id = self._create_province(session, prov_code, prov_name)
            else:
                raise ValueError("Territoire: province parente introuvable")

        existing = session.scalar(select(Territoire).where(Territoire.code == code, Territoire.province_id == province_id))
        if existing:
            existing.nom = nom
            session.add(existing)
            report.rows_updated += 1
            return

        territoire = Territoire(code=code, nom=nom, province_id=province_id)
        session.add(territoire)
        report.rows_inserted += 1

    def _process_collectivite_row(self, row: Dict[str, Any], mapping: Dict[str, str], report: ImportReport, session: Session) -> None:
        code = str(row.get(mapping.get("collectivite_code"), "")).strip().upper()
        nom = row.get(mapping.get("collectivite_name"))
        type_col = row.get(mapping.get("collectivite_type"))
        territoire_code = row.get(mapping.get("territoire_code"))
        if not code or not nom or not territoire_code:
            raise ValueError("Collectivite: code, nom ou territoire parent manquant")
        territoire_id = self._find_parent_id(session, Territoire, territoire_code)
        if territoire_id is None:
            if getattr(self, "_create_parents", False):
                # try to create territoire (and province if needed)
                prov_code = row.get(mapping.get("province_code"))
                territoire_name = row.get(mapping.get("territoire_name"))
                territoire_id = self._create_territoire(session, territoire_code, territoire_name, prov_code or "")
            else:
                raise ValueError("Collectivite: territoire parente introuvable")

        existing = session.scalar(select(Collectivite).where(Collectivite.code == code, Collectivite.territoire_id == territoire_id))
        if existing:
            existing.nom = nom
            if type_col:
                existing.type_collectivite = type_col
            session.add(existing)
            report.rows_updated += 1
            return

        collectivite = Collectivite(code=code, nom=nom, territoire_id=territoire_id, type_collectivite=type_col or "Secteur")
        session.add(collectivite)
        report.rows_inserted += 1

    def _process_groupement_row(self, row: Dict[str, Any], mapping: Dict[str, str], report: ImportReport, session: Session) -> None:
        code = str(row.get(mapping.get("groupement_code"), "")).strip().upper()
        nom = row.get(mapping.get("groupement_name"))
        collectivite_code = row.get(mapping.get("collectivite_code"))
        if not code or not nom or not collectivite_code:
            raise ValueError("Groupement: code, nom ou collectivite parent manquant")
        collectivite_id = self._find_parent_id(session, Collectivite, collectivite_code)
        if collectivite_id is None:
            if getattr(self, "_create_parents", False):
                # try to create collectivite (requires territoire)
                territoire_code = row.get(mapping.get("territoire_code"))
                collectivite_name = row.get(mapping.get("collectivite_name"))
                # create territoire if needed
                territoire_id = self._find_parent_id(session, Territoire, territoire_code) if territoire_code else None
                if territoire_id is None:
                    if territoire_code and getattr(self, "_create_parents", False):
                        prov_code = row.get(mapping.get("province_code"))
                        territoire_id = self._create_territoire(session, territoire_code, row.get(mapping.get("territoire_name")), prov_code or "")
                    else:
                        raise ValueError("Groupement: territoire parent introuvable pour créer la collectivite")
                collectivite = Collectivite(code=str(collectivite_code).strip().upper(), nom=collectivite_name or str(collectivite_code), territoire_id=territoire_id, type_collectivite=row.get(mapping.get("collectivite_type")) or "Secteur")
                session.add(collectivite)
                session.flush()
                collectivite_id = collectivite.id
            else:
                raise ValueError("Groupement: collectivite parente introuvable")

        existing = session.scalar(select(Groupement).where(Groupement.code == code, Groupement.collectivite_id == collectivite_id))
        if existing:
            existing.nom = nom
            session.add(existing)
            report.rows_updated += 1
            return

        groupement = Groupement(code=code, nom=nom, collectivite_id=collectivite_id)
        session.add(groupement)
        report.rows_inserted += 1

    def _process_village_row(self, row: Dict[str, Any], mapping: Dict[str, str], report: ImportReport, session: Session) -> None:
        code = str(row.get(mapping.get("village_code"), "")).strip().upper()
        nom = row.get(mapping.get("village_name"))
        groupement_code = row.get(mapping.get("groupement_code"))
        if not code or not nom or not groupement_code:
            raise ValueError("Village: code, nom ou groupement parent manquant")
        groupement_id = self._find_parent_id(session, Groupement, groupement_code)
        if groupement_id is None:
            if getattr(self, "_create_parents", False):
                # try to create groupement (requires collectivite)
                collectivite_code = row.get(mapping.get("collectivite_code"))
                collectivite_id = self._find_parent_id(session, Collectivite, collectivite_code) if collectivite_code else None
                if collectivite_id is None:
                    if collectivite_code and getattr(self, "_create_parents", False):
                        # create collectivite (and its territoire/province as needed)
                        territoire_code = row.get(mapping.get("territoire_code"))
                        territoire_name = row.get(mapping.get("territoire_name"))
                        collectivite_id = self._create_territoire(session, territoire_code or "", territoire_name, row.get(mapping.get("province_code")) or "")
                        collectivite = Collectivite(code=str(collectivite_code).strip().upper(), nom=row.get(mapping.get("collectivite_name")) or str(collectivite_code), territoire_id=collectivite_id, type_collectivite=row.get(mapping.get("collectivite_type")) or "Secteur")
                        session.add(collectivite)
                        session.flush()
                        collectivite_id = collectivite.id
                    else:
                        raise ValueError("Village: collectivite parente introuvable pour créer le groupement")
                groupement = Groupement(code=str(groupement_code).strip().upper(), nom=nom or str(groupement_code), collectivite_id=collectivite_id)
                session.add(groupement)
                session.flush()
                groupement_id = groupement.id
            else:
                raise ValueError("Village: groupement parent introuvable")

        existing = session.scalar(select(Village).where(Village.code == code, Village.groupement_id == groupement_id))
        if existing:
            existing.nom = nom
            session.add(existing)
            report.rows_updated += 1
            return

        village = Village(code=code, nom=nom, groupement_id=groupement_id)
        session.add(village)
        report.rows_inserted += 1

    def _process_site_row(self, row: Dict[str, Any], mapping: Dict[str, str], report: ImportReport, session: Session) -> None:
        # Sites require village to exist (by code or by hierarchy fields)
        village_code = row.get(mapping.get("village_code"))
        if not village_code:
            raise ValueError("Site: code village manquant")

        village = session.scalar(select(Village).where(Village.code == str(village_code).strip().upper()))
        if village is None:
            if getattr(self, "_create_parents", False):
                # attempt to create village and its parents
                groupement_code = row.get(mapping.get("groupement_code"))
                collectivite_code = row.get(mapping.get("collectivite_code"))
                territoire_code = row.get(mapping.get("territoire_code"))
                province_code = row.get(mapping.get("province_code"))

                # ensure groupement exists
                groupement = None
                if groupement_code:
                    groupement = session.scalar(select(Groupement).where(Groupement.code == str(groupement_code).strip().upper()))
                if groupement is None:
                    # create collectivite if needed
                    collectivite = None
                    if collectivite_code:
                        collectivite = session.scalar(select(Collectivite).where(Collectivite.code == str(collectivite_code).strip().upper()))
                    if collectivite is None:
                        # create territoire (and province) if needed
                        if not territoire_code:
                            territoire_code = ""
                        territoire_id = self._find_parent_id(session, Territoire, territoire_code)
                        if territoire_id is None:
                            territoire_id = self._create_territoire(session, territoire_code or "", row.get(mapping.get("territoire_name")), province_code or "")
                        collectivite = Collectivite(code=str(collectivite_code).strip().upper() if collectivite_code else "AUTO_COL_" + str(int(time.time())), nom=row.get(mapping.get("collectivite_name")) or (collectivite_code or "auto"), territoire_id=territoire_id, type_collectivite=row.get(mapping.get("collectivite_type")) or "Secteur")
                        session.add(collectivite)
                        session.flush()
                    # create groupement
                    groupement = Groupement(code=str(groupement_code).strip().upper() if groupement_code else "AUTO_GRP_" + str(int(time.time())), nom=row.get(mapping.get("groupement_name")) or (groupement_code or "auto"), collectivite_id=collectivite.id)
                    session.add(groupement)
                    session.flush()

                # now create village
                village = Village(code=str(village_code).strip().upper(), nom=row.get(mapping.get("village_name")) or str(village_code), groupement_id=groupement.id)
                session.add(village)
                session.flush()
            else:
                raise ValueError("Site: village introuvable pour lier le site")

        nom = row.get(mapping.get("site_name")) or ""
        code_site = row.get(mapping.get("site_code"))
        latitude = row.get(mapping.get("latitude"))
        longitude = row.get(mapping.get("longitude"))

        # check existing by code_site or by generated fdsu components
        if code_site:
            existing = session.scalar(select(Site).where(Site.code_site == code_site))
        else:
            existing = None

        if existing:
            existing.nom = nom or existing.nom
            existing.latitude = latitude or existing.latitude
            existing.longitude = longitude or existing.longitude
            existing.village_id = village.id
            session.add(existing)
            report.rows_updated += 1
            return

        site = Site(
            nom=nom,
            code_site=code_site or None,
            code_fdsu=code_site or None,
            latitude=latitude,
            longitude=longitude,
            statut=row.get(mapping.get("statut")) or "Prévu",
            type_site=row.get(mapping.get("type_site")) or "Autre",
            village_id=village.id,
        )
        session.add(site)
        report.rows_inserted += 1
