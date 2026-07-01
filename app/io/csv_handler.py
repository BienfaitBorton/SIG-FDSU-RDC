from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .base import Importer, Exporter
from .exceptions import ValidationError
from .utils import iter_with_progress, ensure_parent_dir


class CSVHandler(Importer, Exporter):
    """Importeur/Exporteur CSV basé sur pandas.

    - import_data: lit toutes les lignes et renvoie des dicts
    - export_data: écrit un CSV à partir d'un itérable de dicts
    """

    def import_data(self, path: Path, **kwargs) -> Iterable[dict]:
        df = pd.read_csv(path, dtype=object)
        df = df.where(pd.notna(df), None)
        for row in iter_with_progress(df.to_dict(orient="records"), desc=f"Import CSV {path.name}", disable=not self.progress):
            valid, errors = self.validate(row)
            if not valid:
                raise ValidationError(f"Ligne invalide: {errors}")
            yield row

    def export_data(self, path: Path, records: Iterable[dict], **kwargs) -> None:
        ensure_parent_dir(path)
        df = pd.DataFrame(list(records))
        df.to_csv(path, index=False)

    def validate(self, record: dict) -> tuple[bool, list[str]]:
        return True, []
