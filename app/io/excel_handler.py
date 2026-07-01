from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .base import Importer, Exporter
from .exceptions import ValidationError
from .utils import iter_with_progress, ensure_parent_dir


class ExcelHandler(Importer, Exporter):
    """Importeur/Exporteur Excel (.xlsx) basé sur pandas/openpyxl.

    - import_data: renvoie des dicts par ligne
    - export_data: prend un itérable de dicts et écrit une feuille
    """

    def import_data(self, path: Path, sheet_name: str | None = None, **kwargs) -> Iterable[dict]:
        df = pd.read_excel(path, sheet_name=sheet_name, dtype=object)
        df = df.where(pd.notna(df), None)
        for row in iter_with_progress(df.to_dict(orient="records"), desc=f"Import Excel {path.name}", disable=not self.progress):
            valid, errors = self.validate(row)
            if not valid:
                raise ValidationError(f"Ligne invalide: {errors}")
            yield row

    def export_data(self, path: Path, records: Iterable[dict], sheet_name: str = "data", **kwargs) -> None:
        ensure_parent_dir(path)
        df = pd.DataFrame(list(records))
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    def validate(self, record: dict) -> tuple[bool, list[str]]:
        # Par défaut, aucune validation métier stricte. Retourne toujours vrai.
        return True, []
