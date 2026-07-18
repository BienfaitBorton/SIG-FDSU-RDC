from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.routes import nire as route
from api.services.nire import EntityReference
from api.services.nire.operational import *
from api.services.nire.operational_service import NireOperationalService
from api.services.nire.persistence import InMemoryNireRepository

def setup_service():
    repo=InMemoryNireRepository(); service=NireOperationalService(repo); run=service.start_run("key","CENI","EDUCATION")
    candidate=StoredCandidate("CAN-1",run.run_id,"CENI","C1","EDUCATION","E1",55,.8,"AMBIGUOUS","Test",True)
    evidence=(StoredEvidence("E1","CAN-1","NAME","CENI","C1","EP A",25,.9,.9),)
    decision=StoredDecision("DEC-1","CAN-1","AMBIGUOUS",55,run.engine_version,run.rule_version,"Revue requise")
    review=service.persist_resolution(run,candidate,decision,evidence)
    return repo,service,run,candidate,evidence,decision,review

def test_resolution_run_created(): assert setup_service()[2].status=="STARTED"
def test_resolution_run_idempotent():
    r,s,run,*_=setup_service(); assert s.start_run("key","X","Y")==run and len(r.runs)==1
def test_candidate_persisted():
    r,_,_,c,*_=setup_service(); assert r.get_candidate(c.candidate_id)==c
def test_evidences_persisted():
    r,_,_,c,e,*_=setup_service(); assert r.evidences[c.candidate_id]==e
def test_decision_recorded(): assert setup_service()[0].get_decision("DEC-1").decision=="AMBIGUOUS"
def test_audit_trail_created(): assert len(setup_service()[0].history)==1
def test_review_queue_fed(): assert setup_service()[-1].status==ReviewStatus.PENDING

@pytest.mark.parametrize("action,status,role",[(ReviewActionType.VALIDATE,ReviewStatus.VALIDATED,NireRole.REVIEWER),(ReviewActionType.REJECT,ReviewStatus.REJECTED,NireRole.REVIEWER),(ReviewActionType.DEFER,ReviewStatus.DEFERRED,NireRole.ANALYST),(ReviewActionType.CORRECT,ReviewStatus.CORRECTED,NireRole.APPROVER)])
def test_human_actions(action,status,role):
    r,s,*rest=setup_service(); item=rest[-1]; updated=s.review(item.review_id,action,"user",role,"justification",("E1",),"POSSIBLE_MATCH" if action==ReviewActionType.CORRECT else None)
    assert updated.status==status and r.actions[-1].evidence_ids==("E1",)

def test_correction_preserves_old_decision():
    r,s,*rest=setup_service(); s.review(rest[-1].review_id,ReviewActionType.CORRECT,"a",NireRole.APPROVER,"correction",correction="POSSIBLE_MATCH")
    assert r.get_decision("DEC-1").decision=="AMBIGUOUS" and any(x.previous_decision_id=="DEC-1" for x in r.decisions.values())
def test_cancellation_preserves_history():
    r,s,*_=setup_service(); new=s.cancel_decision("DEC-1","a",NireRole.ADMIN,"erreur")
    assert new.previous_decision_id=="DEC-1" and r.get_decision("DEC-1").cancelled_at is None and len(r.history)==2
def test_permissions_contract():
    _,s,*rest=setup_service()
    with pytest.raises(PermissionError): s.review(rest[-1].review_id,ReviewActionType.VALIDATE,"a",NireRole.ANALYST,"non")
def test_source_never_modified():
    _,s,*_=setup_service(); attrs={"normalized_name":"EP A","institutional_id":"C1"}; a=EntityReference("C1","CENI","SCHOOL",attrs.copy()); b=EntityReference("E1","EDUCATION","SCHOOL",attrs.copy()); before=(a.as_dict(),b.as_dict()); s.run_controlled_workflow("wf",a,b); assert (a.as_dict(),b.as_dict())==before
def test_controlled_workflow_queues_review():
    s=NireOperationalService(InMemoryNireRepository()); attrs={"normalized_name":"EP A","institutional_id":"C1"}; _,item=s.run_controlled_workflow("wf",EntityReference("C1","CENI","SCHOOL",attrs),EntityReference("E1","EDUCATION","SCHOOL",attrs)); assert item.status==ReviewStatus.PENDING
def test_38_ceni_candidates_not_auto_validated():
    s=NireOperationalService(InMemoryNireRepository()); run=s.start_run("q","CENI_QUARANTINE","CENI"); rows=[]
    for i in range(38):
        c=StoredCandidate(f"C{i}",run.run_id,"CENI_QUARANTINE",str(i),"CENI",str(i),10,.2,"AMBIGUOUS","q",True); d=StoredDecision(f"D{i}",c.candidate_id,"INSUFFICIENT_EVIDENCE",10,run.engine_version,run.rule_version,"q"); rows.append((c,d,()))
    assert len(s.enqueue_ceni_quarantine(rows))==38 and not any(x.status==ReviewStatus.VALIDATED for x in s.repository.reviews.values())
def test_ceni_auto_validation_rejected():
    s=NireOperationalService(InMemoryNireRepository()); run=s.start_run("q","CENI_QUARANTINE","CENI"); c=StoredCandidate("C",run.run_id,"CENI_QUARANTINE","Q","CENI","T",99,1,"VALIDATED","q",False); d=StoredDecision("D","C","VALIDATED",99,run.engine_version,run.rule_version,"q")
    with pytest.raises(ValueError): s.enqueue_ceni_quarantine([(c,d,())])

@pytest.fixture
def client():
    service=NireOperationalService(InMemoryNireRepository()); app=FastAPI(); app.include_router(route.router,prefix="/api/nire"); app.dependency_overrides[route.get_nire_service]=lambda:service
    return TestClient(app),service
def test_api_limits(client):
    c,_=client; x=c.post("/api/nire/candidates/generate",json={"idempotency_key":"a","source_name":"A","target_name":"B","batch_size":25,"max_candidates":50,"timeout_seconds":10}); assert x.status_code==200 and x.json()["batch_size"]==25
def test_api_pagination_and_filter(client):
    c,s=client
    for i in range(3):
        run=s.start_run(str(i),"CENI" if i<2 else "FDSU","X"); can=StoredCandidate(f"C{i}",run.run_id,run.source_name,str(i),"X",str(i),1,.1,"AMBIGUOUS","x"); dec=StoredDecision(f"D{i}",can.candidate_id,"AMBIGUOUS",1,run.engine_version,run.rule_version,"x"); s.persist_resolution(run,can,dec)
    assert len(c.get("/api/nire/review-queue?source_name=CENI&offset=1&limit=1").json()["items"])==1
def test_api_permission_and_validation(client):
    c,s=client; r,_,run,can,ev,dec,item=setup_service(); s.repository=r
    body={"author":"a","justification":"raison"}; assert c.post(f"/api/nire/review/{item.review_id}/validate",headers={"X-NIRE-Role":"ANALYST"},json=body).status_code==403
    assert c.post(f"/api/nire/review/{item.review_id}/validate",headers={"X-NIRE-Role":"REVIEWER"},json=body).status_code==200
def test_migration_reversible():
    text=Path("alembic/versions/0006_nire_operational.py").read_text(encoding="utf-8"); assert "CREATE SCHEMA IF NOT EXISTS" in text and "def downgrade" in text and "DROP SCHEMA IF EXISTS" in text
def test_review_statuses_complete(): assert len(ReviewStatus)==7
def test_api_main_mount_is_hidden():
    text=Path("api/main.py").read_text(encoding="utf-8"); assert 'prefix="/api/nire"' in text and "include_in_schema=False" in text
