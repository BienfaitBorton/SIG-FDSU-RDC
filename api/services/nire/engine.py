"""Fusion de preuves et résolution d'identité explicable de NIRE Phase 1."""

from __future__ import annotations

import hashlib
import math
from dataclasses import replace
from typing import Any, Iterable

from .models import (
    AmbiguityLevel,
    CandidateStatus,
    DecisionType,
    EntityReference,
    EvidenceStatus,
    NationalEvidence,
    ResolutionCandidate,
    ResolutionDecision,
)
from .rules import NationalRuleRegistry, default_rule_registry


def _stable_id(prefix: str, *values: Any) -> str:
    payload = "|".join(str(value) for value in values)
    return f"{prefix}-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:20].upper()}"


def _valid_coordinates(attributes: dict[str, Any]) -> tuple[float, float] | None:
    try:
        latitude, longitude = float(attributes.get("latitude")), float(attributes.get("longitude"))
    except (TypeError, ValueError):
        return None
    if (latitude, longitude) == (0.0, 0.0) or not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None
    return latitude, longitude


def _distance_km(left: tuple[float, float], right: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*left, *right))
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371.0088 * 2 * math.asin(min(1.0, math.sqrt(a)))


class EvidenceFusionEngine:
    def __init__(self, registry: NationalRuleRegistry | None = None) -> None:
        self.registry = registry or default_rule_registry()

    def fuse(self, evidences: Iterable[NationalEvidence]) -> dict[str, Any]:
        rows = tuple(evidences)
        positive = round(sum(row.contribution for row in rows if row.status == EvidenceStatus.SUPPORTING), 4)
        negative = round(sum(row.contribution for row in rows if row.status == EvidenceStatus.CONFLICTING), 4)
        blocking = tuple(dict.fromkeys(filter(None, (self.registry.blocking_rule(row.evidence_type) for row in rows if row.status == EvidenceStatus.CONFLICTING))))
        score = 0.0 if blocking else round(max(0.0, min(100.0, positive - negative)), 4)
        active = [row for row in rows if row.status != EvidenceStatus.NEUTRAL]
        reliability = sum(row.confidence * row.reliability for row in active) / len(active) if active else 0.0
        confidence = round(min(1.0, reliability * min(1.0, (positive + negative) / 70.0)), 4)
        return {"positive": positive, "negative": negative, "score": score, "confidence": confidence, "blocking_rules": blocking}


class IdentityResolutionEngine:
    def __init__(self, registry: NationalRuleRegistry | None = None) -> None:
        self.registry = registry or default_rule_registry()
        self.fusion = EvidenceFusionEngine(self.registry)

    def _evidence(self, kind: str, source: EntityReference, target: EntityReference, value: Any, normalized: Any, *, confidence: float = 1.0, reliability: float = 1.0, metadata: dict[str, Any] | None = None) -> NationalEvidence:
        status = EvidenceStatus.CONFLICTING if self.registry.is_negative(kind) else EvidenceStatus.SUPPORTING
        return NationalEvidence(evidence_id=_stable_id("EVI", kind, source.source_name, source.entity_id, target.source_name, target.entity_id, normalized), evidence_type=kind, source_name=source.source_name, source_entity_id=source.entity_id, target_entity_id=target.entity_id, value=value, normalized_value=normalized, weight=self.registry.weight(kind), confidence=confidence, reliability=reliability, status=status, metadata=dict(metadata or {}))

    def extract_evidence(self, source: EntityReference, target: EntityReference) -> tuple[NationalEvidence, ...]:
        left, right, rows = source.attributes, target.attributes, []
        left_id, right_id = left.get("institutional_id"), right.get("institutional_id")
        if left_id and right_id:
            kind = "EXACT_IDENTIFIER" if left_id == right_id else "IDENTIFIER_CONFLICT"
            rows.append(self._evidence(kind, source, target, [left_id, right_id], left_id if left_id == right_id else f"{left_id}!={right_id}"))
        if left.get("normalized_name") and left.get("normalized_name") == right.get("normalized_name"):
            rows.append(self._evidence("NORMALIZED_NAME", source, target, [left.get("name"), right.get("name")], left["normalized_name"], confidence=.95, reliability=.9))
        if source.entity_type and target.entity_type:
            kind = "ENTITY_TYPE_MATCH" if source.entity_type == target.entity_type else "ENTITY_TYPE_CONFLICT"
            rows.append(self._evidence(kind, source, target, [source.entity_type, target.entity_type], source.entity_type if kind.endswith("MATCH") else f"{source.entity_type}!={target.entity_type}"))
        for key, match_kind in (("province", "PROVINCE_MATCH"), ("territory", "TERRITORY_MATCH"), ("locality", "LOCALITY_MATCH")):
            if left.get(key) and right.get(key):
                if left[key] == right[key]:
                    rows.append(self._evidence(match_kind, source, target, [left[key], right[key]], left[key], reliability=.95))
                elif key == "province":
                    rows.append(self._evidence("ADMINISTRATIVE_CONFLICT", source, target, [left[key], right[key]], f"{left[key]}!={right[key]}", reliability=.95, metadata={"level": key}))
        if left.get("operator") and right.get("operator"):
            kind = "OPERATOR_MATCH" if left["operator"] == right["operator"] else "OPERATOR_CONFLICT"
            rows.append(self._evidence(kind, source, target, [left["operator"], right["operator"]], left["operator"] if kind.endswith("MATCH") else f"{left['operator']}!={right['operator']}"))
        for key, kind in (("phone", "PHONE_MATCH"), ("email", "EMAIL_MATCH")):
            if left.get(key) and left.get(key) == right.get(key):
                rows.append(self._evidence(kind, source, target, left[key], str(left[key]).strip().lower()))
        left_coord, right_coord = _valid_coordinates(left), _valid_coordinates(right)
        if left_coord and right_coord:
            distance = _distance_km(left_coord, right_coord)
            if distance <= .01:
                rows.append(self._evidence("SAME_COORDINATES", source, target, [left_coord, right_coord], round(distance * 1000, 2), reliability=.98, metadata={"distance_m": round(distance * 1000, 2)}))
            elif distance <= 1.0:
                rows.append(self._evidence("GEOGRAPHIC_DISTANCE", source, target, [left_coord, right_coord], round(distance * 1000, 2), confidence=max(.7, 1.0 - distance / 2), reliability=.95, metadata={"distance_m": round(distance * 1000, 2)}))
            elif distance >= 100.0:
                rows.append(self._evidence("GEOGRAPHIC_CONFLICT", source, target, [left_coord, right_coord], round(distance, 2), reliability=.95, metadata={"distance_km": round(distance, 2)}))
        return tuple(rows)

    def resolve(self, source: EntityReference, target: EntityReference, *, homonym_count: int = 1, competing_scores: Iterable[float] = ()) -> tuple[ResolutionCandidate, ResolutionDecision]:
        evidences = self.extract_evidence(source, target)
        fusion = self.fusion.fuse(evidences)
        ambiguity = self._ambiguity(evidences, fusion["score"], homonym_count, tuple(competing_scores))
        status = self._candidate_status(fusion, ambiguity)
        explanation = self._explain(evidences, fusion["blocking_rules"], ambiguity)
        candidate_id = _stable_id("CAN", source.source_name, source.entity_id, target.source_name, target.entity_id)
        candidate = ResolutionCandidate(candidate_id=candidate_id, source_entity=source, target_entity=target, evidences=evidences, positive_evidence_score=fusion["positive"], negative_evidence_score=fusion["negative"], resolution_score=fusion["score"], confidence=fusion["confidence"], status=status, ambiguity_level=ambiguity, explanation=explanation)
        decision = self._decision(candidate, fusion["blocking_rules"])
        return candidate, decision

    def resolve_many(self, source: EntityReference, targets: Iterable[EntityReference]) -> tuple[tuple[ResolutionCandidate, ResolutionDecision], ...]:
        initial = [self.resolve(source, target) for target in targets]
        scores = [candidate.resolution_score for candidate, _ in initial]
        results = []
        for candidate, _ in initial:
            competitors = tuple(score for score in scores if score != candidate.resolution_score or scores.count(score) > 1)
            ambiguity = self._ambiguity(candidate.evidences, candidate.resolution_score, len(initial), competitors)
            updated = replace(candidate, ambiguity_level=ambiguity, status=self._candidate_status({"score": candidate.resolution_score, "blocking_rules": tuple(self.registry.blocking_rule(row.evidence_type) for row in candidate.evidences if row.status == EvidenceStatus.CONFLICTING and self.registry.blocking_rule(row.evidence_type))}, ambiguity), explanation=self._explain(candidate.evidences, tuple(), ambiguity))
            results.append((updated, self._decision(updated, tuple(self.registry.blocking_rule(row.evidence_type) for row in updated.evidences if row.status == EvidenceStatus.CONFLICTING and self.registry.blocking_rule(row.evidence_type)))))
        return tuple(results)

    def _candidate_status(self, fusion: dict[str, Any], ambiguity: AmbiguityLevel) -> CandidateStatus:
        if fusion.get("blocking_rules"):
            return CandidateStatus.CONFLICT
        score = float(fusion["score"])
        if ambiguity in {AmbiguityLevel.HIGH, AmbiguityLevel.CRITICAL} and score < self.registry.document["thresholds"]["match_recommended"]:
            return CandidateStatus.AMBIGUOUS
        if score >= self.registry.document["thresholds"]["strong_match"]:
            return CandidateStatus.STRONG_MATCH
        if score >= self.registry.document["thresholds"]["possible_match"]:
            return CandidateStatus.PROBABLE_MATCH
        return CandidateStatus.AMBIGUOUS if ambiguity in {AmbiguityLevel.HIGH, AmbiguityLevel.CRITICAL} else CandidateStatus.PENDING

    def _ambiguity(self, evidences: tuple[NationalEvidence, ...], score: float, homonym_count: int, competing_scores: tuple[float, ...]) -> AmbiguityLevel:
        if homonym_count >= 100:
            return AmbiguityLevel.CRITICAL
        if homonym_count > 1 and any(abs(score - other) <= 5 for other in competing_scores):
            return AmbiguityLevel.HIGH
        types = {row.evidence_type for row in evidences}
        geographic = types & {"SAME_COORDINATES", "GEOGRAPHIC_DISTANCE"}
        context = types & {"EXACT_IDENTIFIER", "TERRITORY_MATCH", "LOCALITY_MATCH", "PROVINCE_MATCH"}
        if types == {"NORMALIZED_NAME", "ENTITY_TYPE_MATCH"} or ("NORMALIZED_NAME" in types and not geographic and not context):
            return AmbiguityLevel.HIGH
        if homonym_count > 1:
            return AmbiguityLevel.MEDIUM
        return AmbiguityLevel.LOW if score >= self.registry.document["thresholds"]["match_recommended"] else AmbiguityLevel.MEDIUM

    def _decision(self, candidate: ResolutionCandidate, blocking: tuple[str, ...]) -> ResolutionDecision:
        thresholds = self.registry.document["thresholds"]
        if blocking:
            decision = DecisionType.NO_MATCH
        elif candidate.ambiguity_level in {AmbiguityLevel.HIGH, AmbiguityLevel.CRITICAL}:
            decision = DecisionType.AMBIGUOUS if candidate.resolution_score >= thresholds["possible_match"] else DecisionType.INSUFFICIENT_EVIDENCE
        elif candidate.resolution_score >= thresholds["match_recommended"]:
            decision = DecisionType.MATCH_RECOMMENDED
        elif candidate.resolution_score >= thresholds["possible_match"]:
            decision = DecisionType.POSSIBLE_MATCH
        else:
            decision = DecisionType.INSUFFICIENT_EVIDENCE
        warnings = ["Aucune fusion automatique n'est autorisée en Phase 1."]
        if not any(row.evidence_type in {"SAME_COORDINATES", "GEOGRAPHIC_DISTANCE"} for row in candidate.evidences):
            warnings.append("Aucune preuve géographique exploitable n'est disponible.")
        return ResolutionDecision(decision_id=_stable_id("DEC", candidate.candidate_id, decision.value), candidate_id=candidate.candidate_id, decision=decision, score=candidate.resolution_score, confidence=candidate.confidence, evidences_used=tuple(row.evidence_id for row in candidate.evidences), positive_evidences=tuple(row.evidence_id for row in candidate.evidences if row.status == EvidenceStatus.SUPPORTING), negative_evidences=tuple(row.evidence_id for row in candidate.evidences if row.status == EvidenceStatus.CONFLICTING), blocking_rules=tuple(dict.fromkeys(blocking)), warnings=tuple(warnings), explanation=candidate.explanation, requires_human_review=True, engine_version=self.registry.engine_version)

    @staticmethod
    def _explain(evidences: tuple[NationalEvidence, ...], blocking: tuple[str, ...], ambiguity: AmbiguityLevel) -> str:
        phrases = []
        for row in evidences:
            if row.evidence_type == "NORMALIZED_NAME": phrases.append("les deux entités partagent le même nom normalisé")
            elif row.evidence_type == "TERRITORY_MATCH": phrases.append("elles sont rattachées au même territoire")
            elif row.evidence_type == "PROVINCE_MATCH": phrases.append("elles sont rattachées à la même province")
            elif row.evidence_type == "SAME_COORDINATES": phrases.append(f"leurs coordonnées coïncident à {row.metadata.get('distance_m', 0)} mètre(s) près")
            elif row.evidence_type == "GEOGRAPHIC_DISTANCE": phrases.append(f"la distance géographique est de {row.metadata.get('distance_m')} mètres")
            elif row.evidence_type == "EXACT_IDENTIFIER": phrases.append("elles partagent le même identifiant institutionnel")
            elif row.evidence_type.endswith("CONFLICT"): phrases.append(f"une preuve contradictoire {row.evidence_type} est constatée")
        if blocking:
            prefix = "Correspondance non recommandée"
        elif phrases:
            prefix = "Analyse de correspondance"
        else:
            prefix = "Preuves insuffisantes"
        detail = "; ".join(phrases) if phrases else "aucune preuve d'identité exploitable n'a été extraite"
        review = " Une validation humaine est requise." if ambiguity != AmbiguityLevel.NONE else ""
        return f"{prefix} : {detail}.{review}"
