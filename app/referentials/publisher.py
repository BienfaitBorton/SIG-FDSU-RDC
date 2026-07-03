from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PublicationStage(str, Enum):
    IMPORT = "import"
    ANALYZE = "analyze"
    VALIDATE = "validate"
    PUBLISH = "publish"


@dataclass(slots=True)
class PublicationWorkflow:
    """Lifecycle state holder for referential publication."""

    source_name: str
    stage: PublicationStage = PublicationStage.IMPORT

    def move_to(self, next_stage: PublicationStage) -> None:
        """Transition placeholder for future policy checks."""

        self.stage = next_stage

    def is_published(self) -> bool:
        """Published data is the only data to be consumed by SIG."""

        return self.stage == PublicationStage.PUBLISH
