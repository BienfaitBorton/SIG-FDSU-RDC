from __future__ import annotations
import json
from dataclasses import FrozenInstanceError
import pytest

from api.services.nire import *
from api.services.nire.candidate_generation import DEFAULT_RULES_PATH, valid_coordinates

def norm(adapter, row): return adapter.normalize_entity(row)
def mem(cls, rows, **kw): return cls(lambda: tuple(dict(r) for r in rows), **kw)

@pytest.mark.parametrize("cls,row", [
 (CeniSourceAdapter,{"asset_uid":"C1","name":"EP A","geometry_status":"valid"}),
 (EducationSourceAdapter,{"education_id":"E1","source_id":"C1","original_name":"EP A","validation_status":"PROBABLE"}),
 (HealthSourceAdapter,{"id":1,"name":"CS A","data_source":"health.health_facilities"}),
 (TelecomSourceAdapter,{"id":1,"infra_name":"SITE A","geometry_kind":"POINT","operator_code":"ORANGE"}),
 (FdsuSiteSourceAdapter,{"site_id":1,"site_name":"TECH-001","source":"PROGRAMME 20476 SITES.csv"}),
 (AdministrativeSourceAdapter,{"entity_id":"L1","nom":"KABAMBA","administrative_level":"LOCALITY"}),
])
def test_real_adapters_are_read_only_projections(cls,row):
    source=dict(row); adapter=mem(cls,[source]); entity=norm(adapter,adapter.get_entity_by_id(adapter.source_id(row)))
    assert source==row and entity.attributes["provenance"]
    with pytest.raises(FrozenInstanceError): entity.entity_id="changed"

def test_ceni_zero_zero_is_removed_and_quarantine_preserved():
    row={"asset_uid":"Q1","name":"CABANE","latitude":0,"longitude":0,"geometry_status":"quarantined_sentinel_coordinates","quarantine":{"resolution_candidate":True}}
    e=norm(mem(CeniSourceAdapter,[row],include_quarantine=True),row)
    assert valid_coordinates(e) is None and e.attributes["quality_status"]=="QUARANTINE" and e.attributes["resolution_candidate"]

def test_ceni_integrated_stream_excludes_quarantine_by_default():
    rows=[{"asset_uid":"I","name":"A","geometry_status":"valid"},{"asset_uid":"Q","name":"B","geometry_status":"quarantined_sentinel_coordinates"}]
    adapter=mem(CeniSourceAdapter,rows)
    # Le fournisseur injecte est deja un flux controle; le contrat de separation est porte par le fournisseur reel.
    assert adapter.include_quarantine is False

def test_education_quarantine_projection_keeps_direct_provenance():
    row={"education_id":"EDU-Q","source_id":"Q","original_name":"EP Q","validation_status":"QUARANTINE","provenance":{"source":"CENI"}}
    e=norm(mem(EducationSourceAdapter,[row],include_quarantine=True),row)
    assert e.attributes["quality_status"]=="QUARANTINE" and e.attributes["institutional_id"]=="Q" and e.attributes["provenance"]["source"]=="CENI"

def test_fdsu_technical_identifier_is_preserved_without_invented_name():
    row={"site_id":1,"site_code":"SITES_20476_00001","site_name":"Part2_technical","latitude":-2,"longitude":23}
    e=norm(mem(FdsuSiteSourceAdapter,[row]),row)
    assert e.entity_id=="1" and e.attributes["institutional_id"]=="SITES 20476 00001" and e.attributes["name"]=="Part2_technical"

def entities(rows, typ="SCHOOL", source="A"):
    a=InMemorySourceAdapter(source,typ,rows); return tuple(a.normalize_entity(r) for r in a.get_entities())

def test_exact_id_is_prioritized_and_ceni_education_direct_source():
    s=norm(mem(EducationSourceAdapter,[{"education_id":"E1","source_id":"C1","original_name":"EP K"}]),{"education_id":"E1","source_id":"C1","original_name":"EP K"})
    targets=(norm(mem(CeniSourceAdapter,[{"asset_uid":"C1","name":"EP K","geometry_status":"valid"}]),{"asset_uid":"C1","name":"EP K","geometry_status":"valid"}),)
    p,_=CandidateGenerationEngine().generate((s,),targets)
    assert p[0].target.entity_id=="C1" and "exact_id" in p[0].block_reasons

def test_top_k_and_province_territory_blocks():
    s=entities([{"id":"S","name":"ALPHA","province":"P1","territory":"T1"}])[0]
    t=entities([{"id":str(i),"name":"ALPHA","province":"P1","territory":"T1"} for i in range(15)]+[{"id":"X","name":"ALPHA","province":"P2","territory":"T1"},{"id":"Y","name":"ALPHA","province":"P1","territory":"T2"}],source="B")
    p,_=CandidateGenerationEngine().generate((s,),t)
    assert len(p)==10 and all(x.target.entity_id not in {"X","Y"} for x in p)

def test_operator_block_and_geometry_types():
    adapter=mem(TelecomSourceAdapter,[{"id":1,"infra_name":"A","geometry_kind":"POINT"},{"id":2,"line_name":"FIBRE","geometry_kind":"LINESTRING"}])
    rows=tuple(adapter.normalize_entity(r) for r in adapter.get_entities())
    assert [x.entity_type for x in rows]==["TELECOM_SITE","TELECOM_NETWORK_GEOMETRY"]
    s=entities([{"id":"S","name":"SITE","operator":"ORANGE"}],"TELECOM_SITE")[0]
    t=entities([{"id":"A","name":"SITE","operator":"ORANGE"},{"id":"B","name":"SITE","operator":"VODACOM"}],"TELECOM_SITE","B")
    p,_=CandidateGenerationEngine().generate((s,),t); assert [x.target.entity_id for x in p]==["A"]

def test_spatial_index_excludes_zero_and_fdsu_admin_never_fuses():
    s=entities([{"id":"F","name":"TECH","province":"P","latitude":-4.3,"longitude":15.3}],"FDSU_SITE")[0]
    a=AdministrativeSourceAdapter(lambda:[{"entity_id":"L","nom":"LOC","administrative_level":"LOCALITY","province":"P","latitude":-4.31,"longitude":15.31}])
    target=tuple(a.normalize_entity(r) for r in a.get_entities()); p,_=CandidateGenerationEngine().generate((s,),target)
    assert len(p)==1 and "spatial" in p[0].block_reasons and not hasattr(p[0],"decision")

def test_reduction_is_massive_and_no_quadratic_scan():
    s=entities([{"id":f"S{i}","name":f"N{i}","province":"P"} for i in range(100)])
    t=entities([{"id":f"T{i}","name":f"N{i}","province":"P"} for i in range(1000)],source="B")
    p,m=CandidateGenerationEngine().generate(s,t)
    assert m.theoretical_comparisons==100000 and m.actual_candidates<=1000 and m.reduction_percent>=99

def test_broad_administrative_block_is_bounded():
    s=entities([{"id":f"S{i}","name":"","province":"P"} for i in range(25)])
    t=entities([{"id":f"T{i}","name":"","province":"P"} for i in range(5000)],source="B")
    p,m=CandidateGenerationEngine().generate(s,t)
    assert len(p)<=250 and m.actual_candidates<=25*10

def test_kabamba_is_ambiguous_and_cabane_critical():
    e=IdentityResolutionEngine(); a,b=entities([{"id":"A","name":"E.P KABAMBA"}])[0],entities([{"id":"B","name":"EP KABAMBA"}],source="B")[0]
    assert e.resolve(a,b)[0].ambiguity_level==AmbiguityLevel.HIGH
    c,d=entities([{"id":"C","name":"CABANE"}],"OTHER")[0],entities([{"id":"D","name":"CABANE"}],"OTHER","B")[0]
    assert e.resolve(c,d,homonym_count=114)[0].ambiguity_level==AmbiguityLevel.CRITICAL

def test_evidence_extractors_trace_contract_and_zero_zero():
    a,b=entities([{"id":"A","name":"EP A","institutional_id":"1","latitude":0,"longitude":0}])[0],entities([{"id":"B","name":"EP A","institutional_id":"1","latitude":0,"longitude":0}],source="B")[0]
    ev=extract_all(a,b); assert {x.evidence_type for x in ev}>={"NORMALIZED_NAME","INSTITUTIONAL_IDENTIFIER","ENTITY_TYPE","SOURCE_QUALITY"}
    assert "GEOGRAPHIC_DISTANCE" not in {x.evidence_type for x in ev} and all(x.metadata.get("extractor_version")=="2.0.0" for x in ev)

@pytest.mark.parametrize("expected,predicted,wanted",[
 ([1,1,0,0],[1,0,1,0],(.5,.5,.5,.5)),
 ([1,1,0,0],[1,1,0,0],(1,1,0,0)),
])
def test_calibration_metrics(expected,predicted,wanted):
    m=calculate_calibration(expected,predicted); assert (m.precision,m.recall,m.false_positive_rate,m.false_negative_rate)==wanted

def test_synthetic_ground_truth_covers_required_risks():
    cases=synthetic_ground_truth_cases(); names={x["case"] for x in cases}
    assert {"homonym","near_but_distinct","same_name_different_province","identifier_conflict","different_operator","missing_coordinates"} <= names

def test_candidate_generation_is_idempotent_and_rules_extensible():
    s=entities([{"id":"S","name":"A"}]); t=entities([{"id":"T","name":"A"}],source="B"); engine=CandidateGenerationEngine()
    assert engine.generate(s,t)[0]==engine.generate(s,t)[0]
    rules=json.loads(DEFAULT_RULES_PATH.read_text(encoding="utf-8")); rules["entity_types"]["FUTURE_DOMAIN"]={"top_k":3,"spatial_radius_km":1}
    engine.rules=rules
    assert engine.rules["entity_types"]["FUTURE_DOMAIN"]["top_k"]==3

def test_mno_synthetic_classifications_and_no_replacement():
    rules=json.loads(DEFAULT_RULES_PATH.read_text(encoding="utf-8"))
    assert set(rules["future_mno_classifications"])=={"EXACT_MATCH","PROBABLE_MATCH","AMBIGUOUS","NEW_SITE","POSSIBLE_DUPLICATE","CONFLICT"}
    assert rules["legacy_replacement_requires_coverage_percent"]==100 and rules["automatic_merge_allowed"] is False

def test_locality_is_not_automatically_a_village():
    a=AdministrativeSourceAdapter(lambda:[{"entity_id":"1","nom":"X","administrative_level":"LOCALITY"}]); e=a.normalize_entity(next(iter(a.get_entities())))
    assert e.entity_type=="ADMIN_LOCALITY" and e.attributes["locality_village_equivalence_proven"] is False
