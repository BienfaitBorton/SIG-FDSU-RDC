from api.services.national_semantic_classification_engine import NationalSemanticClassificationEngine, normalize_name


def engine():
    return NationalSemanticClassificationEngine()


def test_normalization_handles_accents_punctuation_spaces_and_apostrophes():
    assert normalize_name("  É.P.   Jardin d’enfants ") == "EP JARDIN D ENFANTS"


def test_school_rules():
    cases = [("EP. LOSONDJU", "SCHOOL", .99), ("INST. ELONGA", "SCHOOL", .97), ("COMPLEXE SCOLAIRE KIMBA", "SCHOOL", .99)]
    for name, category, confidence in cases:
        result = engine().classify(name)
        assert result.normalized_category_code == category
        assert result.normalized_category_label_fr == "École"
        assert result.confidence == confidence
        assert result.matched_rule_id and result.justification_fr


def test_health_religious_administration_and_market_rules():
    cases = {
        "CENTRE DE SANTÉ KIMBA": "HEALTH_FACILITY",
        "HGR DE BUNIA": "HEALTH_FACILITY",
        "PAROISSE SAINT PAUL": "RELIGIOUS_BUILDING",
        "MAIRIE DE GOMA": "ADMINISTRATIVE_BUILDING",
        "MARCHÉ CENTRAL": "MARKET",
    }
    for name, category in cases.items():
        assert engine().classify(name).normalized_category_code == category


def test_ambiguous_cs_and_unknown_remain_unclassified():
    assert engine().classify("CS KIMBA").normalized_category_code == "UNCLASSIFIED"
    assert engine().classify("LOCAL LOSONDJU").normalized_category_code == "UNCLASSIFIED"
    assert engine().classify("CS SCOLAIRE KIMBA").normalized_category_code == "SCHOOL"
    assert engine().classify("CS SANTÉ KIMBA").normalized_category_code == "HEALTH_FACILITY"
    assert engine().classify("CS ECOLE HOPITAL KIMBA").normalized_category_code == "UNCLASSIFIED"


def test_source_is_preserved_result_is_explainable_stable_and_idempotent():
    source = "É.P.  LOSONDJU"
    raw = {"Name": source, "Latitude": "1"}
    first = engine().classify(source, raw_properties=raw)
    second = engine().classify(source, raw_properties=raw)
    assert first == second
    assert first.source_name == source and first.raw_properties == raw
    assert first.normalized_name != source
    assert first.matched_keyword == "ECOLE PRIMAIRE"
    assert first.confidence_label_fr == "Très élevée"
    assert first.engine_version == "fr-2.0.0-dnai"
    assert first.review_status == "Non revu"


def test_official_source_category_has_priority():
    result = engine().classify("PAROISSE", source_category="SCHOOL")
    assert result.normalized_category_code == "SCHOOL"
    assert result.matched_rule_id == "SOURCE_CATEGORY"
    assert result.confidence == 1.0


def test_short_tokens_never_match_inside_other_words():
    for name in ("INSTALLATION X", "INSTITUTION PUBLIQUE", "DEPARTEMENT X"):
        assert engine().classify(name).normalized_category_code == "UNCLASSIFIED"


def test_bare_abbreviation_empty_name_and_technical_identifier_are_unclassified():
    for name in ("", "EP", "INST", "CS", "CENI-EP-001"):
        result = engine().classify(name)
        assert result.normalized_category_code == "UNCLASSIFIED"
        assert result.matched_rule_id is None
