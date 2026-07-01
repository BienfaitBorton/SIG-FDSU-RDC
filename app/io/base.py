from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable


class IOHandler(ABC):
    """Base abstraite pour les handlers d'import/export.

    Les sous-classes doivent implémenter :
    - import_data(path) -> iterable of records (dict)
    - export_data(path, records) -> None
    - validate(record) -> tuple[bool, list[str]]
    """

    def __init__(self, *, progress: bool = True, logger: Any | None = None):
        self.progress = progress
        self.logger = logger

    @abstractmethod
    def import_data(self, path: Path, **kwargs) -> Iterable[dict]:
        raise NotImplementedError()

    @abstractmethod
    def export_data(self, path: Path, records: Iterable[dict], **kwargs) -> None:
        raise NotImplementedError()

    @abstractmethod
    def validate(self, record: dict) -> tuple[bool, list[str]]:
        raise NotImplementedError()


class Importer(IOHandler):
    pass


class Exporter(IOHandler):
    pass
