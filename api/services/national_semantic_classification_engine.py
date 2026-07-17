"""Moteur transversal, explicable et non destructif de classification française."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from api.services.dnai_service import default_dnai

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES_PATH = ROOT / "data" / "business" / "semantic_classification_rules_fr_v1.json"


def normalize_name(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char)).upper()
    text = text.replace("’", " ").replace("'", " ")
    text = re.sub(r"(?<=\b[A-Z])\.(?=[A-Z]\b|\s|$)", "", text)
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def confidence_label_fr(value: float) -> str:
    if value >= .95: return "Très élevée"
    if value >= .85: return "Élevée"
    if value >= .65: return "Moyenne"
    if value >= .40: return "Faible"
    return "Insuffisante"


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    source_name: str
    normalized_name: str
    source_category: str | None
    normalized_category_code: str
    normalized_category_label_fr: str
    classification_method: str
    matched_rule_id: str | None
    matched_keyword: str | None
    confidence: float
    confidence_label_fr: str
    justification_fr: str
    engine_version: str
    classification_date: str
    review_status: str
    raw_properties: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class NationalSemanticClassificationEngine:
    def __init__(self, rules_path: Path = DEFAULT_RULES_PATH) -> None:
        self.rules_path = Path(rules_path)
        self.registry = json.loads(self.rules_path.read_text(encoding="utf-8"))

    @staticmethod
    def _contains(text: str, keyword: str) -> bool:
        return re.search(rf"(?:^|\s){re.escape(keyword)}(?:\s|$)", text) is not None

    def classify(self, source_name: str, source_category: str | None = None, raw_properties: dict[str, Any] | None = None) -> ClassificationResult:
        referential = str((raw_properties or {}).get("referential") or ("CENI" if (raw_properties or {}).get("kml_name") is not None else "national"))
        dnai = default_dnai().normalize(source_name, referential=referential)
        normalized = normalize_name(dnai.normalized_text)
        categories = self.registry["categories_fr"]
        if source_category and source_category in categories and source_category != "UNCLASSIFIED":
            return self._result(source_name, normalized, source_category, source_category, "SOURCE_CATEGORY", source_category, 1.0, "La catégorie officielle fournie par la source est conservée.", raw_properties)

        if dnai.technical_identifier or normalized in {"EP", "INST", "CS"} or re.fullmatch(r"(?:CENI|ID|UID|CODE)(?:\s+[A-Z0-9]+)*\s+\d+", normalized):
            return self._result(source_name, normalized, source_category, "UNCLASSIFIED", None, None, 0.0, "Le nom est vide de contexte métier ou ressemble à un identifiant technique; aucune classification n’est proposée.", raw_properties)

        for rule in self.registry["rules"]:
            requires = rule.get("requires_any", [])
            excludes = rule.get("excludes_any", [])
            if requires and not any(self._contains(normalized, normalize_name(item)) for item in requires): continue
            if excludes and any(self._contains(normalized, normalize_name(item)) for item in excludes): continue
            matches = [item for item in rule.get("keywords", []) if self._contains(normalized, normalize_name(item))]
            matches += [item for item in rule.get("prefixes", []) if re.match(rf"^{re.escape(normalize_name(item))}(?:\s|$)", normalized)]
            if matches:
                keyword = matches[0]
                category = rule["category"]
                dnai_note = f" DNAI : {dnai.justification}" if dnai.rule_id else ""
                return self._result(source_name, normalized, source_category, category, rule["id"], keyword, float(rule["confidence"]), f"Le nom normalisé contient l’indice lexical français explicite « {keyword} », associé à la catégorie « {categories[category]} ».{dnai_note}", raw_properties)
        return self._result(source_name, normalized, source_category, "UNCLASSIFIED", None, None, 0.0, "Aucune règle lexicale française suffisamment fiable ne s’applique au nom source.", raw_properties)

    def _result(self, source_name: str, normalized: str, source_category: str | None, category: str, rule_id: str | None, keyword: str | None, confidence: float, justification: str, raw_properties: dict[str, Any] | None) -> ClassificationResult:
        return ClassificationResult(source_name=source_name, normalized_name=normalized, source_category=source_category, normalized_category_code=category, normalized_category_label_fr=self.registry["categories_fr"][category], classification_method=self.registry["classification_method"], matched_rule_id=rule_id, matched_keyword=keyword, confidence=confidence, confidence_label_fr=confidence_label_fr(confidence), justification_fr=justification, engine_version=self.registry["engine_version"], classification_date=date.today().isoformat(), review_status="À vérifier" if 0 < confidence < .85 else "Non revu", raw_properties=dict(raw_properties or {}))


@lru_cache(maxsize=1)
def default_engine() -> NationalSemanticClassificationEngine:
    return NationalSemanticClassificationEngine()
