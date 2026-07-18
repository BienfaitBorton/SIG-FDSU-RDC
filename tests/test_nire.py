from __future__ import annotations

import json

from api.services.nire import (
    AmbiguityLevel,
    CandidateStatus,
    DecisionType,
    IdentityResolutionEngine,
    InMemorySourceAdapter,
    NationalRuleRegistry,
)
from api.services.nire.rules import DEFAULT_RULES_PATH


def entity(source: str, entity_id: str, name: str, entity_type: str = "SCHOOL", **attributes):
    adapter = InMemorySourceAdapter(source, entity_type, [{"id": entity_id, "name": name, **attributes}])
    return adapter.normalize_entity(adapter.get_entity_by_id(entity_id))


def test_identical_name_alone_never_validates_or_merges():
    candidate, decision = IdentityResolutionEngine().resolve(entity("CENI", "A", "E.P KABAMBA"), entity("EDUCATION", "B", "EP KABAMBA"))
    assert candidate.status == CandidateStatus.AMBIGUOUS
    assert candidate.ambiguity_level == AmbiguityLevel.HIGH
    assert decision.decision == DecisionType.INSUFFICIENT_EVIDENCE
    assert decision.requires_human_review is True
    assert candidate.status != CandidateStatus.VALIDATED_MATCH


def test_identical_name_and_territory_is_probable():
    source = entity("CENI", "A", "EP KABAMBA", territory="LUPATAPATA")
    target = entity("EDUCATION", "B", "E.P KABAMBA", territory="LUPATAPATA")
    candidate, decision = IdentityResolutionEngine().resolve(source, target)
    assert candidate.status == CandidateStatus.PROBABLE_MATCH
    assert decision.decision == DecisionType.POSSIBLE_MATCH


def test_name_territory_and_near_coordinates_is_strong_but_not_validated():
    source = entity("CENI", "A", "EP KABAMBA", territory="LUPATAPATA", latitude=-6.1, longitude=23.4)
    target = entity("EDUCATION", "B", "E.P KABAMBA", territory="LUPATAPATA", latitude=-6.1004, longitude=23.4003)
    candidate, decision = IdentityResolutionEngine().resolve(source, target)
    assert candidate.status == CandidateStatus.STRONG_MATCH
    assert decision.decision == DecisionType.MATCH_RECOMMENDED
    assert decision.requires_human_review is True


def test_different_provinces_create_blocking_conflict():
    source = entity("CENI", "A", "EP KABAMBA", province="LOMAMI")
    target = entity("EDUCATION", "B", "EP KABAMBA", province="KINSHASA")
    candidate, decision = IdentityResolutionEngine().resolve(source, target)
    assert candidate.status == CandidateStatus.CONFLICT
    assert decision.decision == DecisionType.NO_MATCH
    assert "BLOCK_ADMINISTRATIVE_CONFLICT" in decision.blocking_rules


def test_identical_institutional_identifier_is_strong_evidence():
    source = entity("SOURCE_A", "A", "SITE ALPHA", institutional_id="OFF-001")
    target = entity("SOURCE_B", "B", "SITE ALPHA", institutional_id="OFF-001")
    candidate, decision = IdentityResolutionEngine().resolve(source, target)
    assert "EXACT_IDENTIFIER" in {row.evidence_type for row in candidate.evidences}
    assert candidate.status == CandidateStatus.STRONG_MATCH
    assert decision.decision == DecisionType.MATCH_RECOMMENDED


def test_incompatible_identifiers_override_positive_score():
    source = entity("SOURCE_A", "A", "SITE ALPHA", institutional_id="OFF-001")
    target = entity("SOURCE_B", "B", "SITE ALPHA", institutional_id="OFF-002")
    candidate, decision = IdentityResolutionEngine().resolve(source, target)
    assert candidate.resolution_score == 0
    assert decision.decision == DecisionType.NO_MATCH
    assert "BLOCK_IDENTIFIER_CONFLICT" in decision.blocking_rules


def test_telecom_operator_conflict_is_blocking():
    source = entity("MNO", "V1", "SITE GOMA", "TELECOM", operator="VODACOM")
    target = entity("TELECOM_SIG", "O1", "SITE GOMA", "TELECOM", operator="ORANGE")
    candidate, decision = IdentityResolutionEngine().resolve(source, target)
    assert candidate.status == CandidateStatus.CONFLICT
    assert "BLOCK_OPERATOR_CONFLICT" in decision.blocking_rules


def test_two_close_candidates_raise_high_ambiguity():
    engine = IdentityResolutionEngine()
    source = entity("MNO", "A", "SITE RADIO", "TELECOM", operator="AIRTEL")
    targets = [entity("SIG", "B", "SITE RADIO", "TELECOM", operator="AIRTEL"), entity("SIG", "C", "SITE RADIO", "TELECOM", operator="AIRTEL")]
    results = engine.resolve_many(source, targets)
    assert {candidate.ambiguity_level for candidate, _ in results} == {AmbiguityLevel.HIGH}
    assert all(decision.requires_human_review for _, decision in results)


def test_cabane_homonyms_are_critical_and_never_merged():
    candidate, decision = IdentityResolutionEngine().resolve(entity("CENI_QUARANTINE", "A", "CABANE", "OTHER"), entity("CENI", "B", "CABANE", "OTHER"), homonym_count=114)
    assert candidate.ambiguity_level == AmbiguityLevel.CRITICAL
    assert candidate.status == CandidateStatus.AMBIGUOUS
    assert decision.decision == DecisionType.INSUFFICIENT_EVIDENCE


def test_missing_coordinates_keep_engine_functional_and_cautious():
    candidate, decision = IdentityResolutionEngine().resolve(entity("CENI", "A", "EP KABAMBA"), entity("EDU", "B", "EP KABAMBA", territory="LUPATAPATA"))
    assert not {"SAME_COORDINATES", "GEOGRAPHIC_DISTANCE"} & {row.evidence_type for row in candidate.evidences}
    assert any("géographique" in warning for warning in decision.warnings)


def test_zero_zero_is_never_geographic_evidence():
    source = entity("CENI", "A", "EP KABAMBA", latitude=0, longitude=0)
    target = entity("EDU", "B", "EP KABAMBA", latitude=0, longitude=0)
    candidate, _ = IdentityResolutionEngine().resolve(source, target)
    assert not {"SAME_COORDINATES", "GEOGRAPHIC_DISTANCE", "GEOGRAPHIC_CONFLICT"} & {row.evidence_type for row in candidate.evidences}


def test_no_sufficient_evidence_returns_insufficient():
    candidate, decision = IdentityResolutionEngine().resolve(entity("A", "1", "ALPHA"), entity("B", "2", "BETA"))
    assert candidate.resolution_score < 40
    assert decision.decision == DecisionType.INSUFFICIENT_EVIDENCE


def test_explanation_is_french_and_traceable_to_evidence():
    source = entity("CENI", "A", "EP KABAMBA", territory="LUPATAPATA", latitude=-6.1, longitude=23.4)
    target = entity("EDU", "B", "EP KABAMBA", territory="LUPATAPATA", latitude=-6.1004, longitude=23.4003)
    candidate, decision = IdentityResolutionEngine().resolve(source, target)
    assert "même nom normalisé" in decision.explanation
    assert "même territoire" in decision.explanation
    assert "distance géographique" in decision.explanation
    assert set(decision.evidences_used) == {row.evidence_id for row in candidate.evidences}


def test_engine_is_idempotent_for_same_inputs():
    engine = IdentityResolutionEngine()
    source, target = entity("MNO", "A", "SITE KIN", "TELECOM", operator="AFRICELL"), entity("SIG", "B", "SITE KIN", "TELECOM", operator="AFRICELL")
    first = engine.resolve(source, target)
    second = engine.resolve(source, target)
    assert first[0].candidate_id == second[0].candidate_id
    assert first[0].resolution_score == second[0].resolution_score
    assert first[1].decision_id == second[1].decision_id


def test_rule_registry_is_versioned_valid_and_extensible():
    registry = NationalRuleRegistry()
    document = json.loads(DEFAULT_RULES_PATH.read_text(encoding="utf-8"))
    assert registry.version == "nire-rules-1.0.0"
    assert document["automatic_merge_allowed"] is False
    assert {"NORMALIZED_NAME", "MANUAL_VALIDATION", "IDENTIFIER_CONFLICT", "GEOGRAPHIC_CONFLICT"} <= document["evidence_types"].keys()


def test_fictitious_mno_same_operator_and_coordinates_is_recommended():
    engine = IdentityResolutionEngine()
    for operator in ("VODACOM", "ORANGE", "AIRTEL", "AFRICELL"):
        source = entity("MNO_FICTIF", f"{operator}-A", f"SITE {operator} TEST", "TELECOM", operator=operator, latitude=-4.3, longitude=15.3)
        target = entity("SIG_FICTIF", f"{operator}-B", f"SITE {operator} TEST", "TELECOM", operator=operator, latitude=-4.3, longitude=15.3)
        candidate, decision = engine.resolve(source, target)
        assert candidate.status == CandidateStatus.STRONG_MATCH
        assert decision.decision == DecisionType.MATCH_RECOMMENDED
        assert candidate.status != CandidateStatus.VALIDATED_MATCH
