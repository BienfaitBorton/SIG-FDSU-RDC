"""Repositories NIRE. L'implementation memoire sert aux tests; PostgreSQL reste differe."""
from __future__ import annotations
from dataclasses import replace
from typing import Any
from psycopg2.extras import Json, RealDictCursor
from api.config import connect_db
from .operational import *

class InMemoryNireRepository:
    def __init__(self): self.runs={}; self.run_keys={}; self.candidates={}; self.evidences={}; self.decisions={}; self.reviews={}; self.actions=[]; self.history=[]
    def create_run(self,r):
        old=self.find_run_by_key(r.idempotency_key)
        if old:return old
        self.runs[r.run_id]=r; self.run_keys[r.idempotency_key]=r.run_id; return r
    def get_run(self,i): return self.runs.get(i)
    def find_run_by_key(self,k): return self.runs.get(self.run_keys.get(k))
    def save_candidate(self,c,e): self.candidates.setdefault(c.candidate_id,c); self.evidences.setdefault(c.candidate_id,tuple(e))
    def get_candidate(self,i): return self.candidates.get(i)
    def save_decision(self,d,h): self.decisions.setdefault(d.decision_id,d); self.history.append(h)
    def get_decision(self,i): return self.decisions.get(i)
    def enqueue(self,i): self.reviews.setdefault(i.review_id,i); return self.reviews[i.review_id]
    def get_review(self,i): return self.reviews.get(i)
    def save_review_action(self,i,a): self.reviews[i.review_id]=i; self.actions.append(a)
    def list_reviews(self,*,status=None,source_name=None,offset=0,limit=100):
        rows=list(self.reviews.values())
        if status: rows=[r for r in rows if r.status.value==status]
        if source_name: rows=[r for r in rows if self.candidates[r.candidate_id].source_name==source_name]
        return tuple(rows[offset:offset+limit])

class PostgresNireRepository:
    """Implementation SQL sans etat au demarrage; chaque operation ouvre sa transaction."""
    def _one(self,q,p=()):
        with connect_db() as c:
            with c.cursor(cursor_factory=RealDictCursor) as cur: cur.execute(q,p); row=cur.fetchone(); return dict(row) if row else None
    def create_run(self,r):
        row=self._one("""INSERT INTO nire.resolution_runs(run_id,idempotency_key,source_name,target_name,engine_version,rule_version,status,batch_size,max_candidates,timeout_seconds) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(idempotency_key) DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING *""",(r.run_id,r.idempotency_key,r.source_name,r.target_name,r.engine_version,r.rule_version,r.status,r.batch_size,r.max_candidates,r.timeout_seconds)); return StoredRun(**{k:row[k] for k in StoredRun.__dataclass_fields__ if k in row})
    def get_run(self,i):
        row=self._one("SELECT * FROM nire.resolution_runs WHERE run_id=%s",(i,)); return StoredRun(**{k:row[k] for k in StoredRun.__dataclass_fields__ if k in row}) if row else None
    def find_run_by_key(self,k):
        row=self._one("SELECT run_id FROM nire.resolution_runs WHERE idempotency_key=%s",(k,)); return self.get_run(row["run_id"]) if row else None
    def save_candidate(self,c,e):
        with connect_db() as db:
            with db.cursor() as cur:
                cur.execute("""INSERT INTO nire.resolution_candidates(candidate_id,run_id,source_name,source_entity_id,target_name,target_entity_id,score,confidence,status,explanation,requires_human_review,payload) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",(c.candidate_id,c.run_id,c.source_name,c.source_entity_id,c.target_name,c.target_entity_id,c.score,c.confidence,c.status,c.explanation,c.requires_human_review,Json(c.payload)))
                for x in e: cur.execute("""INSERT INTO nire.resolution_evidences(evidence_id,candidate_id,evidence_type,source_name,source_entity_id,value,weight,confidence,reliability,payload) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",(x.evidence_id,x.candidate_id,x.evidence_type,x.source_name,x.source_entity_id,Json(x.value),x.weight,x.confidence,x.reliability,Json(x.payload)))
    def get_candidate(self,i):
        row=self._one("SELECT * FROM nire.resolution_candidates WHERE candidate_id=%s",(i,)); return StoredCandidate(**{k:row[k] for k in StoredCandidate.__dataclass_fields__ if k in row}) if row else None
    def save_decision(self,d,h):
        with connect_db() as db:
            with db.cursor() as cur:
                cur.execute("""INSERT INTO nire.resolution_decisions(decision_id,candidate_id,decision,score,engine_version,rule_version,explanation,previous_decision_id,cancelled_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",(d.decision_id,d.candidate_id,d.decision,d.score,d.engine_version,d.rule_version,d.explanation,d.previous_decision_id,d.cancelled_at))
                cur.execute("""INSERT INTO nire.decision_history(history_id,decision_id,old_decision,new_decision,author,reason) VALUES(%s,%s,%s,%s,%s,%s)""",(h.history_id,h.decision_id,h.old_decision,h.new_decision,h.author,h.reason))
    def get_decision(self,i):
        row=self._one("SELECT * FROM nire.resolution_decisions WHERE decision_id=%s",(i,)); return StoredDecision(**{k:row[k] for k in StoredDecision.__dataclass_fields__ if k in row}) if row else None
    def enqueue(self,i):
        self._one("""INSERT INTO nire.review_queue(review_id,candidate_id,decision_id,status,priority,assigned_to) VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(review_id) DO UPDATE SET review_id=EXCLUDED.review_id RETURNING review_id""",(i.review_id,i.candidate_id,i.decision_id,i.status.value,i.priority,i.assigned_to)); return i
    def get_review(self,i):
        row=self._one("SELECT * FROM nire.review_queue WHERE review_id=%s",(i,)); return ReviewItem(**{**{k:row[k] for k in ReviewItem.__dataclass_fields__ if k in row},"status":ReviewStatus(row["status"])}) if row else None
    def save_review_action(self,i,a):
        with connect_db() as db:
            with db.cursor() as cur:
                cur.execute("UPDATE nire.review_queue SET status=%s,assigned_to=%s,updated_at=now() WHERE review_id=%s",(i.status.value,i.assigned_to,i.review_id)); cur.execute("""INSERT INTO nire.review_actions(action_id,review_id,action,author,role,justification,evidence_ids,previous_status,new_status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(a.action_id,a.review_id,a.action.value,a.author,a.role.value,a.justification,list(a.evidence_ids),a.previous_status.value,a.new_status.value))
    def list_reviews(self,*,status=None,source_name=None,offset=0,limit=100):
        filters=[]; params=[]
        if status: filters.append("q.status=%s"); params.append(status)
        if source_name: filters.append("c.source_name=%s"); params.append(source_name)
        where=" WHERE "+" AND ".join(filters) if filters else ""; params.extend([limit,offset])
        with connect_db() as db:
            with db.cursor(cursor_factory=RealDictCursor) as cur: cur.execute("SELECT q.* FROM nire.review_queue q JOIN nire.resolution_candidates c USING(candidate_id)"+where+" ORDER BY q.created_at LIMIT %s OFFSET %s",params); rows=cur.fetchall()
        return tuple(ReviewItem(**{**{k:r[k] for k in ReviewItem.__dataclass_fields__ if k in r},"status":ReviewStatus(r["status"])}) for r in rows)
