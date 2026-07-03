from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .normalizer import SourceKind, StagingEntity


class BaseStagingAdapter(ABC):
    """Base contract for adapters that convert source data into staging entities."""

    source_kind: SourceKind = SourceKind.UNKNOWN

    @abstractmethod
    def load(self, source_path: str | Path) -> list[StagingEntity]:
        """Load source content into staging entities without mutating the source."""


class HdxStagingAdapter(BaseStagingAdapter):
    source_kind = SourceKind.HDX

    def load(self, source_path: str | Path) -> list[StagingEntity]:
        raise NotImplementedError("HDX staging adapter is implemented in adapters.py and consumes official COD boundary resources.")


class CeniStagingAdapter(BaseStagingAdapter):
    source_kind = SourceKind.CENI

    def load(self, source_path: str | Path) -> list[StagingEntity]:
        raise NotImplementedError("CENI staging adapter will be implemented when official machine-readable layers are connected.")


class CaidStagingAdapter(BaseStagingAdapter):
    source_kind = SourceKind.CAID

    def load(self, source_path: str | Path) -> list[StagingEntity]:
        raise NotImplementedError("CAID staging adapter will be implemented when statistical referential payloads are connected.")


class InsStagingAdapter(BaseStagingAdapter):
    source_kind = SourceKind.INS

    def load(self, source_path: str | Path) -> list[StagingEntity]:
        raise NotImplementedError("INS staging adapter will be implemented when official nomenclature payloads are connected.")