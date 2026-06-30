from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import Province


def load_province_file(file_path: Path) -> pd.DataFrame:
    supported_extensions = {".xlsx", ".xls", ".csv"}
    extension = file_path.suffix.lower()
    if extension not in supported_extensions:
        raise ValueError(
            f"Type de fichier non supporté : {extension}. Utilisez xlsx, xls ou csv."
        )

    if extension in {".xlsx", ".xls"}:
        return pd.read_excel(file_path, engine="openpyxl")

    return pd.read_csv(file_path)


def import_provinces(file_path: Path) -> int:
    dataframe = load_province_file(file_path)
    expected_columns = {"nom", "code", "zone"}
    missing_columns = expected_columns - set(map(str.lower, dataframe.columns))
    if missing_columns:
        raise ValueError(
            "Le fichier doit contenir les colonnes : nom, code, zone. "
            f"Colonnes manquantes : {', '.join(sorted(missing_columns))}."
        )

    inserted = 0
    with Session(engine) as session:
        for _, row in dataframe.iterrows():
            nom = str(row.get("nom") or row.get("Nom") or "").strip()
            code = str(row.get("code") or row.get("Code") or "").strip()
            zone = str(row.get("zone") or row.get("Zone") or "").strip()
            if not nom or not code or not zone:
                continue

            statement = select(Province).where(Province.code == code)
            existing = session.execute(statement).scalar_one_or_none()
            if existing:
                existing.nom = nom
                existing.zone = zone
            else:
                session.add(Province(nom=nom, code=code, zone=zone))
            inserted += 1

        session.commit()

    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importer la liste des provinces RDC dans la base SIG-FDSU."
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Chemin vers le fichier de provinces (xlsx, xls ou csv).",
    )
    args = parser.parse_args()

    file_path = args.file
    if not file_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")

    count = import_provinces(file_path)
    print(f"Import terminé. {count} provinces traitées.")


if __name__ == "__main__":
    main()
