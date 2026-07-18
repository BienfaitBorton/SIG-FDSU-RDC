"""Contrats operationnels NIRE Phase 3: auditables, reversibles et sans fusion source."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Protocol

def now(): return datetime.now(timezone.utc).isoformat()
class ReviewStatus(StrEnum):
    PENDING="PENDING"; IN_REVIEW="IN_REVIEW"; VALIDATED="VALIDATED"; REJECTED="REJECTED"; CORRECTED="CORRECTED"; DEFERRED="DEFERRED"; CANCELLED="CANCELLED"
class ReviewActionType(StrEnum):
    VALIDATE="VALIDATE"; REJECT="REJECT"; CORRECT="CORRECT"; DEFER="DEFER"; CANCEL="CANCEL"
class NireRole(StrEnum): ANALYST="ANALYST"; REVIEWER="REVIEWER"; APPROVER="APPROVER"; ADMIN="ADMIN"

@dataclass(frozen=True)
class StoredRun:
    run_id:str; idempotency_key:str; source_name:str; target_name:str; engine_version:str; rule_version:str; status:str="STARTED"; batch_size:int=100; max_candidates:int=1000; timeout_seconds:int=300; created_at:str=field(default_factory=now)
@dataclass(frozen=True)
class StoredCandidate:
    candidate_id:str; run_id:str; source_name:str; source_entity_id:str; target_name:str; target_entity_id:str; score:float; confidence:float; status:str; explanation:str; requires_human_review:bool=True; payload:dict[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class StoredEvidence:
    evidence_id:str; candidate_id:str; evidence_type:str; source_name:str; source_entity_id:str; value:Any; weight:float; confidence:float; reliability:float; payload:dict[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class StoredDecision:
    decision_id:str; candidate_id:str; decision:str; score:float; engine_version:str; rule_version:str; explanation:str; previous_decision_id:str|None=None; cancelled_at:str|None=None; created_at:str=field(default_factory=now)
@dataclass(frozen=True)
class ReviewItem:
    review_id:str; candidate_id:str; decision_id:str; status:ReviewStatus=ReviewStatus.PENDING; priority:int=0; assigned_to:str|None=None; created_at:str=field(default_factory=now)
@dataclass(frozen=True)
class ReviewAction:
    action_id:str; review_id:str; action:ReviewActionType; author:str; role:NireRole; justification:str; evidence_ids:tuple[str,...]; previous_status:ReviewStatus; new_status:ReviewStatus; created_at:str=field(default_factory=now)
@dataclass(frozen=True)
class DecisionHistory:
    history_id:str; decision_id:str; old_decision:str|None; new_decision:str; author:str; reason:str; created_at:str=field(default_factory=now)

class NireRepository(Protocol):
    def create_run(self,run:StoredRun)->StoredRun: ...
    def get_run(self,run_id:str)->StoredRun|None: ...
    def find_run_by_key(self,key:str)->StoredRun|None: ...
    def save_candidate(self,candidate:StoredCandidate,evidences:tuple[StoredEvidence,...])->None: ...
    def get_candidate(self,candidate_id:str)->StoredCandidate|None: ...
    def save_decision(self,decision:StoredDecision,history:DecisionHistory)->None: ...
    def get_decision(self,decision_id:str)->StoredDecision|None: ...
    def enqueue(self,item:ReviewItem)->ReviewItem: ...
    def get_review(self,review_id:str)->ReviewItem|None: ...
    def save_review_action(self,item:ReviewItem,action:ReviewAction)->None: ...
    def list_reviews(self,*,status:str|None,source_name:str|None,offset:int,limit:int)->tuple[ReviewItem,...]: ...

ROLE_ACTIONS={NireRole.ANALYST:{ReviewActionType.DEFER},NireRole.REVIEWER:{ReviewActionType.VALIDATE,ReviewActionType.REJECT,ReviewActionType.DEFER},NireRole.APPROVER:set(ReviewActionType),NireRole.ADMIN:set(ReviewActionType)}
def require_action(role:NireRole,action:ReviewActionType):
    if action not in ROLE_ACTIONS[role]: raise PermissionError(f"Le role {role.value} ne peut pas executer {action.value}.")
