"""Blocking indexe et top-k avant fusion de preuves."""

from __future__ import annotations

import json, math, time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import EntityReference

DEFAULT_RULES_PATH = Path(__file__).resolve().parents[3] / "data/business/nire_candidate_generation_rules_v1.json"

def valid_coordinates(e):
    try: p = float(e.attributes.get("latitude")), float(e.attributes.get("longitude"))
    except (TypeError, ValueError): return None
    return p if p != (0.0, 0.0) and -90 <= p[0] <= 90 and -180 <= p[1] <= 180 else None

def distance_km(a, b):
    x1,y1,x2,y2=map(math.radians,(*a,*b)); v=math.sin((x2-x1)/2)**2+math.cos(x1)*math.cos(x2)*math.sin((y2-y1)/2)**2
    return 12742.0176*math.asin(min(1,math.sqrt(v)))

class CandidateIndex(ABC):
    @abstractmethod
    def query(self, source: EntityReference, rules: dict) -> dict[str, set[int]]: ...

class MemoryCandidateIndex(CandidateIndex):
    def __init__(self, entities: Iterable[EntityReference], cell_degrees: float=.05):
        self.entities=tuple(entities); self.cell_degrees=cell_degrees; self.maps={k:{} for k in ("id","type","province","territory","operator","name","spatial")}
        for i,e in enumerate(self.entities):
            a=e.attributes
            values={"id":a.get("institutional_id"),"type":e.entity_type,"province":a.get("province"),"territory":a.get("territory"),"operator":a.get("operator"),"name":a.get("normalized_name")}
            for k,v in values.items():
                if v: self.maps[k].setdefault(v,set()).add(i)
            p=valid_coordinates(e)
            if p: self.maps["spatial"].setdefault((math.floor(p[0]/cell_degrees),math.floor(p[1]/cell_degrees)),set()).add(i)
    def query(self, s, rules):
        a=s.attributes; hits={}
        for k,v in (("exact_id",a.get("institutional_id")),("province",a.get("province")),("territory",a.get("territory")),("operator",a.get("operator")),("name",a.get("normalized_name"))):
            if v: hits[k]=set(self.maps["id" if k=="exact_id" else k].get(v,set()))
        p=valid_coordinates(s)
        if p:
            radius=float(rules.get("spatial_radius_km",5)); n=max(1,math.ceil(radius/(111*self.cell_degrees))); cell=(math.floor(p[0]/self.cell_degrees),math.floor(p[1]/self.cell_degrees)); ids=set()
            for x in range(cell[0]-n,cell[0]+n+1):
                for y in range(cell[1]-n,cell[1]+n+1): ids |= self.maps["spatial"].get((x,y),set())
            hits["spatial"]={i for i in ids if distance_km(p,valid_coordinates(self.entities[i]))<=radius}
        return hits

@dataclass(frozen=True)
class CandidateProposal:
    source: EntityReference; target: EntityReference; block_reasons: tuple[str,...]; priority: float

@dataclass(frozen=True)
class CandidateGenerationMetrics:
    source_entities:int; target_entities:int; theoretical_comparisons:int; actual_candidates:int; reduction_percent:float; average_candidates_per_entity:float; indexing_ms:float; generation_ms:float

class CandidateGenerationEngine:
    def __init__(self, rules_path: Path=DEFAULT_RULES_PATH): self.rules=json.loads(rules_path.read_text(encoding="utf-8"))
    def _compatible(self,a,b): return b in self.rules["type_compatibilities"].get(a,[a])
    def generate(self, sources: Iterable[EntityReference], targets: Iterable[EntityReference], *, index_factory=MemoryCandidateIndex):
        src, tgt=tuple(sources),tuple(targets); t=time.perf_counter(); index=index_factory(tgt); index_ms=(time.perf_counter()-t)*1000; t=time.perf_counter(); out=[]
        for s in src:
            cfg={**self.rules["defaults"],**self.rules.get("entity_types",{}).get(s.entity_type,{})}; hits=index.query(s,cfg); scores={}
            exact=hits.get("exact_id",set())
            selective=set().union(hits.get("spatial",set()),hits.get("name",set()))
            if not selective:
                broad=[ids for key,ids in hits.items() if key in {"territory","operator","province"} and ids]
                selective=set(min(broad,key=len)) if broad else set()
                selective=set(sorted(selective)[:int(cfg["top_k"])*20])
            pool=exact|selective
            for reason, ids in hits.items():
                ids=ids & pool
                for i in ids:
                    if self._compatible(s.entity_type,tgt[i].entity_type): scores.setdefault(i,set()).add(reason)
            ranked=[]
            for i,reasons in scores.items():
                # Province/territoire et operateur sont des conflits bloquants lorsqu'ils sont tous deux renseignes.
                a,b=s.attributes,tgt[i].attributes
                if a.get("province") and b.get("province") and a["province"]!=b["province"]: continue
                if a.get("territory") and b.get("territory") and a["territory"]!=b["territory"]: continue
                if cfg.get("operator_required") and a.get("operator") and b.get("operator") and a["operator"]!=b["operator"]: continue
                priority=sum(self.rules["priorities"].get(r,1) for r in reasons)
                ranked.append(CandidateProposal(s,tgt[i],tuple(sorted(reasons)),priority))
            out.extend(sorted(ranked,key=lambda x:(-x.priority,x.target.entity_id))[:int(cfg["top_k"])])
        gen_ms=(time.perf_counter()-t)*1000; theoretical=len(src)*len(tgt); actual=len(out)
        metrics=CandidateGenerationMetrics(len(src),len(tgt),theoretical,actual,round((1-actual/theoretical)*100,4) if theoretical else 100.0,round(actual/len(src),4) if src else 0.0,round(index_ms,3),round(gen_ms,3))
        return tuple(out),metrics
