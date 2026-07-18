"""API NIRE interne v1. Non montee publiquement hors application controlee."""
from dataclasses import asdict
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from api.services.nire.operational import NireRole, ReviewActionType
from api.services.nire.operational_service import NireOperationalService
from api.services.nire.persistence import PostgresNireRepository
router=APIRouter()
def get_nire_service(): return NireOperationalService(PostgresNireRepository())
def role(x_nire_role:str=Header("ANALYST")):
    try:return NireRole(x_nire_role.upper())
    except ValueError:raise HTTPException(403,"Role NIRE invalide")
class GenerateRequest(BaseModel):
    idempotency_key:str; source_name:str; target_name:str; batch_size:int=Field(100,gt=0,le=5000); max_candidates:int=Field(1000,gt=0,le=100000); timeout_seconds:int=Field(300,gt=0,le=3600)
class ReviewRequest(BaseModel): author:str; justification:str=Field(min_length=3); evidence_ids:list[str]=[]; correction:str|None=None
@router.post("/candidates/generate")
def generate(p:GenerateRequest,s=Depends(get_nire_service)):
    return asdict(s.start_run(p.idempotency_key,p.source_name,p.target_name,batch_size=p.batch_size,max_candidates=p.max_candidates,timeout_seconds=p.timeout_seconds))
@router.post("/resolve")
def resolve_controlled(): return {"status":"CONTROLLED_ONLY","automatic_merge":False,"detail":"Utiliser le workflow interne avec donnees controlees."}
@router.get("/workspace/summary")
def workspace_summary(s=Depends(get_nire_service)): return s.repository.workspace_summary()
@router.get("/runs")
def runs(status:str|None=None,source_name:str|None=None,offset:int=Query(0,ge=0),limit:int=Query(25,gt=0,le=100),s=Depends(get_nire_service)):
    return {"offset":offset,"limit":limit,"items":list(s.repository.list_runs(status=status,source_name=source_name,offset=offset,limit=limit))}
@router.get("/candidates/{candidate_id}")
def candidate(candidate_id:str,s=Depends(get_nire_service)):
    row=s.repository.get_candidate(candidate_id)
    if not row:raise HTTPException(404,"Candidat introuvable")
    return asdict(row)
@router.get("/candidates/{candidate_id}/dossier")
def dossier(candidate_id:str,s=Depends(get_nire_service)):
    row=s.repository.get_dossier(candidate_id)
    if not row:raise HTTPException(404,"Dossier introuvable")
    return row
@router.get("/candidates/{candidate_id}/history")
def history(candidate_id:str,s=Depends(get_nire_service)): return {"items":list(s.repository.get_history(candidate_id))}
@router.get("/decisions/{decision_id}")
def decision(decision_id:str,s=Depends(get_nire_service)):
    row=s.repository.get_decision(decision_id)
    if not row:raise HTTPException(404,"Decision introuvable")
    return asdict(row)
@router.get("/runs/{run_id}")
def run(run_id:str,s=Depends(get_nire_service)):
    row=s.repository.get_run(run_id)
    if not row:raise HTTPException(404,"Run introuvable")
    return asdict(row)
@router.get("/review-queue")
def queue(status:str|None=None,source_name:str|None=None,offset:int=Query(0,ge=0),limit:int=Query(100,gt=0,le=500),s=Depends(get_nire_service)):
    rows=s.repository.list_reviews(status=status,source_name=source_name,offset=offset,limit=limit); return {"offset":offset,"limit":limit,"items":[asdict(x) for x in rows]}
@router.get("/review-dossiers")
def review_dossiers(status:str|None=None,source_name:str|None=None,target_name:str|None=None,domain:str|None=None,ambiguity:str|None=None,engine_decision:str|None=None,priority:int|None=None,requires_human_review:bool|None=None,min_score:float|None=None,min_confidence:float|None=None,offset:int=Query(0,ge=0),limit:int=Query(25,gt=0,le=100),s=Depends(get_nire_service)):
    filters={"status":status,"source_name":source_name,"target_name":target_name,"domain":domain,"ambiguity":ambiguity,"engine_decision":engine_decision,"priority":priority,"requires_human_review":requires_human_review,"min_score":min_score,"min_confidence":min_confidence}
    return {"offset":offset,"limit":limit,"items":list(s.repository.list_review_dossiers(filters=filters,offset=offset,limit=limit))}
@router.get("/roles")
def roles(r=Depends(role)):
    matrix={"ANALYST":["VIEW","PREPARE","DEFER"],"REVIEWER":["VIEW","REJECT","DEFER","VALIDATE"],"APPROVER":["VIEW","VALIDATE","REJECT","CORRECT","DEFER","CANCEL"],"ADMIN":["VIEW","VALIDATE","REJECT","CORRECT","DEFER","CANCEL"]}
    return {"role":r.value,"actions":matrix[r.value],"contract_version":"nire-role-contract-1.0"}
@router.get("/mno-audit/status")
def mno_audit_status(): return {"executed":False,"source_loaded":False,"operators":[],"message":"Aucun audit MNO n’a encore été exécuté. Chargez une source MNO validée pour démarrer une analyse.","automatic_replacement":False,"physical_deletion":False}
def apply(review_id,p,action,r,s):
    try:return asdict(s.review(review_id,action,p.author,r,p.justification,p.evidence_ids,p.correction))
    except PermissionError as e:raise HTTPException(403,str(e))
    except KeyError:raise HTTPException(404,"Revue introuvable")
@router.post("/review/{review_id}/validate")
def validate(review_id:str,p:ReviewRequest,r=Depends(role),s=Depends(get_nire_service)):return apply(review_id,p,ReviewActionType.VALIDATE,r,s)
@router.post("/review/{review_id}/reject")
def reject(review_id:str,p:ReviewRequest,r=Depends(role),s=Depends(get_nire_service)):return apply(review_id,p,ReviewActionType.REJECT,r,s)
@router.post("/review/{review_id}/correct")
def correct(review_id:str,p:ReviewRequest,r=Depends(role),s=Depends(get_nire_service)):return apply(review_id,p,ReviewActionType.CORRECT,r,s)
@router.post("/review/{review_id}/defer")
def defer(review_id:str,p:ReviewRequest,r=Depends(role),s=Depends(get_nire_service)):return apply(review_id,p,ReviewActionType.DEFER,r,s)
@router.post("/decisions/{decision_id}/cancel")
def cancel(decision_id:str,p:ReviewRequest,r=Depends(role),s=Depends(get_nire_service)):
    try:return asdict(s.cancel_decision(decision_id,p.author,r,p.justification))
    except PermissionError as e:raise HTTPException(403,str(e))
    except KeyError:raise HTTPException(404,"Decision introuvable")
