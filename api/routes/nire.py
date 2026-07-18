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
@router.get("/candidates/{candidate_id}")
def candidate(candidate_id:str,s=Depends(get_nire_service)):
    row=s.repository.get_candidate(candidate_id)
    if not row:raise HTTPException(404,"Candidat introuvable")
    return asdict(row)
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
