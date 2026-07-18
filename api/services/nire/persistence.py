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
    def workspace_summary(self):
        statuses=[r.status.value for r in self.reviews.values()]; candidates=list(self.candidates.values())
        return {"recent_runs":len(self.runs),"pending":statuses.count("PENDING"),"ambiguous":sum(c.status=="AMBIGUOUS" for c in candidates),"conflicts":sum(c.status=="CONFLICT" for c in candidates),"to_validate":sum(x in {"PENDING","IN_REVIEW"} for x in statuses),"validated":statuses.count("VALIDATED"),"rejected":statuses.count("REJECTED"),"deferred":statuses.count("DEFERRED")}
    def list_runs(self,*,status=None,source_name=None,offset=0,limit=50):
        rows=list(self.runs.values())
        if status: rows=[r for r in rows if r.status==status]
        if source_name: rows=[r for r in rows if r.source_name==source_name]
        rows.sort(key=lambda r:r.created_at,reverse=True)
        return tuple({**asdict(r),"completed_at":None,"duration_ms":None,"source_count":None,"candidate_count":sum(c.run_id==r.run_id for c in self.candidates.values()),"ambiguous_count":sum(c.run_id==r.run_id and c.status=="AMBIGUOUS" for c in self.candidates.values()),"conflict_count":sum(c.run_id==r.run_id and c.status=="CONFLICT" for c in self.candidates.values()),"insufficient_count":sum(c.run_id==r.run_id and c.status=="INSUFFICIENT_EVIDENCE" for c in self.candidates.values()),"metrics":{}} for r in rows[offset:offset+limit])
    def get_dossier(self,candidate_id):
        c=self.candidates.get(candidate_id)
        if not c:return None
        decisions=[d for d in self.decisions.values() if d.candidate_id==candidate_id]; decision=decisions[-1] if decisions else None; review=next((r for r in self.reviews.values() if r.candidate_id==candidate_id),None)
        return {"candidate":asdict(c),"source_entity":c.payload.get("source_entity",{}),"target_entity":c.payload.get("target_entity",{}),"evidences":[asdict(e) for e in self.evidences.get(candidate_id,())],"decision":asdict(decision) if decision else None,"review":asdict(review) if review else None,"blocking_conflicts":c.payload.get("blocking_conflicts",[]),"ambiguity":c.payload.get("ambiguity","NONE")}
    def get_history(self,candidate_id):
        decision_ids={d.decision_id for d in self.decisions.values() if d.candidate_id==candidate_id}; review_ids={r.review_id for r in self.reviews.values() if r.candidate_id==candidate_id}
        rows=[{"kind":"DECISION","author":h.author,"date":h.created_at,"action":h.new_decision,"old_value":h.old_decision,"new_value":h.new_decision,"justification":h.reason} for h in self.history if h.decision_id in decision_ids]
        rows += [{"kind":"REVIEW","author":a.author,"date":a.created_at,"action":a.action.value,"old_value":a.previous_status.value,"new_value":a.new_status.value,"justification":a.justification} for a in self.actions if a.review_id in review_ids]
        return tuple(sorted(rows,key=lambda x:x["date"]))
    def list_review_dossiers(self,*,filters,offset=0,limit=50):
        rows=[]
        for review in self.reviews.values():
            c=self.candidates[review.candidate_id]; d=self.decisions.get(review.decision_id)
            row={**asdict(review),"source_name":c.source_name,"source_entity_id":c.source_entity_id,"target_name":c.target_name,"target_entity_id":c.target_entity_id,"score":c.score,"confidence":c.confidence,"ambiguity":c.payload.get("ambiguity","NONE"),"engine_decision":d.decision if d else c.status,"requires_human_review":c.requires_human_review,"domain":c.payload.get("domain")}
            exact={k:v for k,v in filters.items() if k not in {"min_score","min_confidence"}}
            if all(v in (None,"") or str(row.get(k,"")).upper()==str(v).upper() for k,v in exact.items()) and (filters.get("min_score") in (None,"") or c.score>=float(filters["min_score"])) and (filters.get("min_confidence") in (None,"") or c.confidence>=float(filters["min_confidence"])):rows.append(row)
        rows.sort(key=lambda x:(-x["priority"],x["created_at"]));return tuple(rows[offset:offset+limit])

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
    def workspace_summary(self):
        return self._one("""SELECT (SELECT count(*) FROM nire.resolution_runs WHERE created_at >= now()-interval '30 days') recent_runs,count(*) FILTER(WHERE q.status='PENDING') pending,count(*) FILTER(WHERE c.status='AMBIGUOUS') ambiguous,count(*) FILTER(WHERE c.status='CONFLICT') conflicts,count(*) FILTER(WHERE q.status IN ('PENDING','IN_REVIEW')) to_validate,count(*) FILTER(WHERE q.status='VALIDATED') validated,count(*) FILTER(WHERE q.status='REJECTED') rejected,count(*) FILTER(WHERE q.status='DEFERRED') deferred FROM nire.review_queue q JOIN nire.resolution_candidates c USING(candidate_id)""")
    def list_runs(self,*,status=None,source_name=None,offset=0,limit=50):
        filters=[]; params=[]
        if status:filters.append("r.status=%s");params.append(status)
        if source_name:filters.append("r.source_name=%s");params.append(source_name)
        where=" WHERE "+" AND ".join(filters) if filters else "";params.extend([limit,offset])
        query="""SELECT r.*,NULL::timestamptz completed_at,NULL::float duration_ms,NULL::int source_count,count(c.candidate_id)::int candidate_count,count(c.candidate_id) FILTER(WHERE c.status='AMBIGUOUS')::int ambiguous_count,count(c.candidate_id) FILTER(WHERE c.status='CONFLICT')::int conflict_count,count(c.candidate_id) FILTER(WHERE c.status='INSUFFICIENT_EVIDENCE')::int insufficient_count,'{}'::jsonb metrics FROM nire.resolution_runs r LEFT JOIN nire.resolution_candidates c USING(run_id)"""+where+" GROUP BY r.run_id ORDER BY r.created_at DESC LIMIT %s OFFSET %s"
        with connect_db() as db:
            with db.cursor(cursor_factory=RealDictCursor) as cur:cur.execute(query,params);return tuple(dict(x) for x in cur.fetchall())
    def get_dossier(self,candidate_id):
        candidate=self._one("SELECT * FROM nire.resolution_candidates WHERE candidate_id=%s",(candidate_id,))
        if not candidate:return None
        decision=self._one("SELECT * FROM nire.resolution_decisions WHERE candidate_id=%s ORDER BY created_at DESC LIMIT 1",(candidate_id,)); review=self._one("SELECT * FROM nire.review_queue WHERE candidate_id=%s ORDER BY created_at DESC LIMIT 1",(candidate_id,))
        with connect_db() as db:
            with db.cursor(cursor_factory=RealDictCursor) as cur:cur.execute("SELECT * FROM nire.resolution_evidences WHERE candidate_id=%s ORDER BY evidence_type",(candidate_id,));evidences=[dict(x) for x in cur.fetchall()]
        payload=candidate.get("payload") or {}
        return {"candidate":candidate,"source_entity":payload.get("source_entity",{}),"target_entity":payload.get("target_entity",{}),"evidences":evidences,"decision":decision,"review":review,"blocking_conflicts":payload.get("blocking_conflicts",[]),"ambiguity":payload.get("ambiguity","NONE")}
    def get_history(self,candidate_id):
        query="""SELECT 'DECISION' kind,h.author,h.created_at date,h.new_decision action,h.old_decision old_value,h.new_decision new_value,h.reason justification FROM nire.decision_history h JOIN nire.resolution_decisions d USING(decision_id) WHERE d.candidate_id=%s UNION ALL SELECT 'REVIEW',a.author,a.created_at,a.action,a.previous_status,a.new_status,a.justification FROM nire.review_actions a JOIN nire.review_queue q USING(review_id) WHERE q.candidate_id=%s ORDER BY date"""
        with connect_db() as db:
            with db.cursor(cursor_factory=RealDictCursor) as cur:cur.execute(query,(candidate_id,candidate_id));return tuple(dict(x) for x in cur.fetchall())
    def list_review_dossiers(self,*,filters,offset=0,limit=50):
        columns={"status":"q.status","source_name":"c.source_name","target_name":"c.target_name","ambiguity":"c.payload->>'ambiguity'","engine_decision":"d.decision","requires_human_review":"c.requires_human_review","domain":"c.payload->>'domain'","priority":"q.priority"}; where=[];params=[]
        for key,value in filters.items():
            if value not in (None,"") and key in columns:where.append(f"{columns[key]}=%s");params.append(value)
        if filters.get("min_score") not in (None,""):where.append("c.score >= %s");params.append(filters["min_score"])
        if filters.get("min_confidence") not in (None,""):where.append("c.confidence >= %s");params.append(filters["min_confidence"])
        clause=" WHERE "+" AND ".join(where) if where else "";params.extend([limit,offset])
        query="""SELECT q.*,c.source_name,c.source_entity_id,c.target_name,c.target_entity_id,c.score,c.confidence,COALESCE(c.payload->>'ambiguity','NONE') ambiguity,d.decision engine_decision,c.requires_human_review,c.payload->>'domain' domain FROM nire.review_queue q JOIN nire.resolution_candidates c USING(candidate_id) LEFT JOIN nire.resolution_decisions d ON d.decision_id=q.decision_id"""+clause+" ORDER BY q.priority DESC,q.created_at LIMIT %s OFFSET %s"
        with connect_db() as db:
            with db.cursor(cursor_factory=RealDictCursor) as cur:cur.execute(query,params);return tuple(dict(x) for x in cur.fetchall())
