"""Orchestration NIRE Phase 3, explicitement declenchee et toujours reversible."""
from __future__ import annotations
import hashlib
from dataclasses import replace
from .operational import *

def sid(prefix,*parts): return prefix+"-"+hashlib.sha256("|".join(map(str,parts)).encode()).hexdigest()[:20].upper()
class NireOperationalService:
    def __init__(self,repository): self.repository=repository
    def start_run(self,key,source,target,*,batch_size=100,max_candidates=1000,timeout_seconds=300):
        old=self.repository.find_run_by_key(key)
        if old:return old
        return self.repository.create_run(StoredRun(sid("RUN",key),key,source,target,"nire-engine-2.0.0","nire-rules-1.0.0",batch_size=batch_size,max_candidates=max_candidates,timeout_seconds=timeout_seconds))
    def persist_resolution(self,run,candidate,decision,evidences=()):
        self.repository.save_candidate(candidate,tuple(evidences)); history=DecisionHistory(sid("HIS",decision.decision_id,decision.created_at),decision.decision_id,None,decision.decision,"SYSTEM","Resolution controlee")
        self.repository.save_decision(decision,history)
        return self.repository.enqueue(ReviewItem(sid("REV",candidate.candidate_id),candidate.candidate_id,decision.decision_id)) if candidate.requires_human_review else None
    def review(self,review_id,action,author,role,justification,evidence_ids=(),correction=None):
        require_action(role,action); item=self.repository.get_review(review_id)
        if not item: raise KeyError(review_id)
        statuses={ReviewActionType.VALIDATE:ReviewStatus.VALIDATED,ReviewActionType.REJECT:ReviewStatus.REJECTED,ReviewActionType.CORRECT:ReviewStatus.CORRECTED,ReviewActionType.DEFER:ReviewStatus.DEFERRED,ReviewActionType.CANCEL:ReviewStatus.CANCELLED}
        updated=replace(item,status=statuses[action],assigned_to=author); audit=ReviewAction(sid("ACT",review_id,action.value,len(getattr(self.repository,"actions",()))),review_id,action,author,role,justification,tuple(evidence_ids),item.status,updated.status)
        self.repository.save_review_action(updated,audit)
        if correction:
            old=self.repository.get_decision(item.decision_id); new=StoredDecision(sid("DEC",old.decision_id,correction),old.candidate_id,correction,old.score,old.engine_version,old.rule_version,justification,old.decision_id)
            self.repository.save_decision(new,DecisionHistory(sid("HIS",new.decision_id),new.decision_id,old.decision,correction,author,justification))
        return updated
    def cancel_decision(self,decision_id,author,role,reason):
        require_action(role,ReviewActionType.CANCEL); old=self.repository.get_decision(decision_id)
        if not old: raise KeyError(decision_id)
        new=StoredDecision(sid("DEC",decision_id,"CANCELLED"),old.candidate_id,"CANCELLED",old.score,old.engine_version,old.rule_version,reason,old.decision_id,now())
        self.repository.save_decision(new,DecisionHistory(sid("HIS",new.decision_id),new.decision_id,old.decision,"CANCELLED",author,reason)); return new
    def enqueue_ceni_quarantine(self,candidates):
        out=[]
        for c,d,e in candidates:
            if c.source_name!="CENI_QUARANTINE" or c.status not in {"AMBIGUOUS","INSUFFICIENT_EVIDENCE"}: raise ValueError("Un candidat CENI quarantaine ne peut pas etre auto-valide.")
            out.append(self.persist_resolution(self.repository.get_run(c.run_id),c,d,e))
        return tuple(out)
    def run_controlled_workflow(self,key,source,target):
        """Workflow demonstratif complet; ne modifie et ne fusionne aucune source."""
        from .candidate_generation import CandidateGenerationEngine
        from .evidence_extractors import extract_all
        from .engine import EvidenceFusionEngine
        run=self.start_run(key,source.source_name,target.source_name,max_candidates=10)
        proposals,_=CandidateGenerationEngine().generate((source,),(target,))
        if not proposals:return run,None
        evidence=extract_all(source,target); fusion=EvidenceFusionEngine().fuse(evidence); cid=sid("CAN",run.run_id,source.entity_id,target.entity_id)
        status="AMBIGUOUS" if fusion["score"]<70 or fusion["blocking_rules"] else "PROBABLE_MATCH"
        candidate=StoredCandidate(cid,run.run_id,source.source_name,source.entity_id,target.source_name,target.entity_id,fusion["score"],fusion["confidence"],status,"Workflow controle: aucune fusion automatique.",True)
        stored=tuple(StoredEvidence(x.evidence_id,cid,x.evidence_type,x.source_name,x.source_entity_id,x.value,x.weight,x.confidence,x.reliability,x.as_dict()) for x in evidence)
        decision=StoredDecision(sid("DEC",cid,status),cid,status,fusion["score"],run.engine_version,run.rule_version,"Decision explicable soumise a revue humaine.")
        return run,self.persist_resolution(run,candidate,decision,stored)
