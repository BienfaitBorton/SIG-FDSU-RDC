"""Chargement et validation du registre national de règles NIRE."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RULES_PATH = ROOT / "data" / "business" / "nire_resolution_rules_v1.json"


class NationalRuleRegistry:
    def __init__(self, path: Path = DEFAULT_RULES_PATH) -> None:
        self.path = Path(path)
        self.document: dict[str, Any] = json.loads(self.path.read_text(encoding="utf-8"))
        self.validate()

    @property
    def version(self) -> str:
        return str(self.document["version"])

    @property
    def engine_version(self) -> str:
        return str(self.document["engine_version"])

    def weight(self, evidence_type: str) -> float:
        return float(self.document["evidence_types"].get(evidence_type, {}).get("weight", 0.0))

    def is_negative(self, evidence_type: str) -> bool:
        return str(self.document["evidence_types"].get(evidence_type, {}).get("polarity", "positive")) == "negative"

    def blocking_rule(self, evidence_type: str) -> str | None:
        return next((row["id"] for row in self.document["blocking_rules"] if evidence_type in row["evidence_types"]), None)

    def validate(self) -> None:
        required = {"version", "engine_version", "evidence_types", "thresholds", "blocking_rules", "confidence_levels", "ambiguity_levels"}
        missing = required - self.document.keys()
        if missing:
            raise ValueError(f"Registre NIRE incomplet: {sorted(missing)}")
        thresholds = self.document["thresholds"]
        if not (0 <= thresholds["possible_match"] < thresholds["match_recommended"] < thresholds["strong_match"] <= 100):
            raise ValueError("Seuils NIRE incohérents")


@lru_cache(maxsize=1)
def default_rule_registry() -> NationalRuleRegistry:
    return NationalRuleRegistry()
