"""NTIL v1.0 — gouvernance nationale de la terminologie."""

from __future__ import annotations

import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from api.services.dnai_service import default_dnai

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "data" / "business" / "national_terminology_registry.json"
VALIDATED_STATES = {"VALIDÉ", "PUBLIÉ"}
PENDING_STATES = {"DÉCOUVERT", "EN ANALYSE", "EN VALIDATION"}


def _pct(numerator: float, denominator: float) -> float:
    return round(100 * numerator / denominator, 2) if denominator else 0.0


class NTILService:
    def __init__(self, registry_path: Path = REGISTRY_PATH) -> None:
        self.registry_path = Path(registry_path)
        self.registry = json.loads(self.registry_path.read_text(encoding="utf-8"))

    @property
    def terms(self) -> list[dict[str, Any]]:
        return self.registry["terms"]

    def list_terms(self, *, query: str = "", status: str | None = None, family: str | None = None, referential: str | None = None, skip: int = 0, limit: int = 100) -> dict[str, Any]:
        needle = query.casefold().strip()
        rows = [term for term in self.terms if (not needle or needle in json.dumps(term, ensure_ascii=False).casefold()) and (not status or term["status"] == status) and (not family or term.get("family") == family) and (not referential or referential in term.get("referentials", []))]
        rows.sort(key=lambda item: (item["term"], item["id"]))
        return {"total": len(rows), "skip": skip, "limit": limit, "terms": rows[skip:skip + limit]}

    def term(self, term_id: str) -> dict[str, Any] | None:
        return next((term for term in self.terms if term["id"] == term_id), None)

    def discoveries(self) -> dict[str, Any]:
        rows = [term for term in self.terms if term["status"] in PENDING_STATES]
        return {"count": len(rows), "items": rows, "publication_automatic": False, "workflow": self.registry["workflow_states"]}

    def compare_discoveries(self, labels: list[str], referential: str) -> dict[str, Any]:
        """Compare un import au NTR et ne retourne que des propositions non publiées."""
        scan = default_dnai().discover(labels, referential)
        known = {term["term"] for term in self.terms}
        proposals = []
        for item in scan.get("discoveries", []):
            proposal = dict(item)
            proposal["registry_match"] = item["abbreviation"] in known
            proposal["proposed_state"] = "EN ANALYSE" if proposal["registry_match"] else "DÉCOUVERT"
            proposal["publication_automatic"] = False
            proposals.append(proposal)
        return {"referential": referential, "count": len(proposals), "proposals": proposals, "registry_version": self.registry["_meta"]["version"]}

    def histories(self, term_id: str | None = None) -> dict[str, Any]:
        global_history = list(self.registry.get("history", []))
        term = self.term(term_id) if term_id else None
        if term_id and not term: return {"count": 0, "items": []}
        if term:
            global_history.append({"version": term["version"], "date": term["first_seen"], "author": "SIG-FDSU RDC", "origin": term["source"], "justification": term["justification"], "change": f"Création de {term['id']} au statut {term['status']}."})
        return {"count": len(global_history), "items": global_history}

    def families(self) -> dict[str, Any]:
        counts = Counter(term.get("family") or "Non déterminée" for term in self.terms)
        synonyms = Counter(group["family"] for group in self.registry.get("synonym_groups", []))
        return {"count": len(counts), "families": [{"name": name, "terms": count, "synonym_groups": synonyms[name]} for name, count in sorted(counts.items())]}

    def quality(self) -> dict[str, Any]:
        snapshots = self.registry.get("referential_snapshots", {})
        validated = sum(term["status"] in VALIDATED_STATES for term in self.terms)
        ambiguous = [term for term in self.terms if "ambigu" in term["type"]]
        resolved = sum(term["status"] in VALIDATED_STATES for term in ambiguous)
        avg_conf = sum(float(term.get("confidence") or 0) for term in self.terms) / len(self.terms) if self.terms else 0
        total_objects = sum(int(snapshot.get("objects", 0)) for snapshot in snapshots.values())
        normalized = sum(int(snapshot.get("normalized_objects", 0)) for snapshot in snapshots.values())
        recognized = sum(int(snapshot.get("recognized_objects", 0)) for snapshot in snapshots.values())
        unknown = sum(int(snapshot.get("unknown_occurrences", 0)) for snapshot in snapshots.values())
        metrics = {
            "normalization_rate": _pct(normalized, total_objects),
            "recognition_rate": _pct(recognized, total_objects),
            "ambiguity_resolution_rate": _pct(resolved, len(ambiguous)),
            "unknown_term_rate": _pct(unknown, total_objects),
            "validation_rate": _pct(validated, len(self.terms)),
            "average_confidence": round(avg_conf, 4),
        }
        components = [metrics["normalization_rate"], metrics["recognition_rate"], metrics["ambiguity_resolution_rate"], 100 - metrics["unknown_term_rate"], metrics["validation_rate"], metrics["average_confidence"] * 100]
        per_ref = []
        for name, snapshot in snapshots.items():
            score = round((2 * _pct(snapshot["normalized_objects"], snapshot["objects"]) + 2 * _pct(snapshot["recognized_objects"], snapshot["objects"]) + (100 - _pct(snapshot["unknown_occurrences"], snapshot["objects"]))) / 5, 2)
            per_ref.append({"referential": name, "score": score, "normalization_rate": _pct(snapshot["normalized_objects"], snapshot["objects"]), "recognition_rate": _pct(snapshot["recognized_objects"], snapshot["objects"]), "unknown_term_rate": _pct(snapshot["unknown_occurrences"], snapshot["objects"]), "objects": snapshot["objects"], "source_sha256": snapshot.get("source_sha256")})
        return {"terminology_quality_score": round(sum(components) / len(components), 2), "metrics": metrics, "quality_by_referential": per_ref, "formula": "Moyenne de normalisation, reconnaissance, ambiguïtés résolues, absence d’inconnus, validation et confiance."}

    def statistics(self) -> dict[str, Any]:
        statuses = Counter(term["status"] for term in self.terms)
        occurrences = sorted(((term["term"], sum(term.get("occurrences", {}).values())) for term in self.terms), key=lambda row: (-row[1], row[0]))
        return {"version": self.registry["_meta"]["version"], "total_terms": len(self.terms), "validated_terms": sum(statuses[state] for state in VALIDATED_STATES), "pending_terms": sum(statuses[state] for state in PENDING_STATES), "unknown_terms": sum(term.get("expansion") is None for term in self.terms), "ambiguities": sum("ambigu" in term["type"] for term in self.terms), "synonym_groups": len(self.registry.get("synonym_groups", [])), "synonyms": sum(len(group["terms"]) for group in self.registry.get("synonym_groups", [])), "families": self.families()["count"], "statuses": dict(statuses), "top_terms": [{"term": term, "occurrences": count} for term, count in occurrences[:50]], "dnai": default_dnai().statistics(), "quality": self.quality()}

    def dashboard(self) -> dict[str, Any]:
        return {"statistics": self.statistics(), "quality": self.quality(), "discoveries": self.discoveries(), "families": self.families(), "history": self.histories(), "coverage": self.registry.get("referential_snapshots", {}), "synonym_groups": self.registry.get("synonym_groups", [])}


@lru_cache(maxsize=1)
def default_ntil() -> NTILService:
    return NTILService()
