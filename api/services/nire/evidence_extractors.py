"""Extracteurs de preuves Phase 2 independants des adaptateurs et de la fusion."""
from __future__ import annotations
import hashlib
from abc import ABC, abstractmethod
from .candidate_generation import distance_km, valid_coordinates
from .models import EntityReference, EvidenceStatus, NationalEvidence

class EvidenceExtractor(ABC):
    evidence_type="GENERIC"; weight=10.0
    @abstractmethod
    def compare(self,a,b): ...
    def extract(self,s:EntityReference,t:EntityReference):
        result=self.compare(s,t)
        if result is None:return ()
        value,normalized,status,confidence,reliability,method=result
        raw=f"{self.evidence_type}|{s.source_name}|{s.entity_id}|{t.source_name}|{t.entity_id}|{normalized}"
        return (NationalEvidence("EVI-"+hashlib.sha256(raw.encode()).hexdigest()[:20].upper(),self.evidence_type,s.source_name,s.entity_id,t.entity_id,value,normalized,self.weight,confidence,reliability,status,{"method":method,"extractor_version":"2.0.0","target_source":t.source_name}),)

class _Equal(EvidenceExtractor):
    key=""
    def compare(self,a,b):
        x,y=a.attributes.get(self.key),b.attributes.get(self.key)
        if not x or not y:return None
        return ([x,y],x if x==y else f"{x}!={y}",EvidenceStatus.SUPPORTING if x==y else EvidenceStatus.CONFLICTING,1,.95,f"normalized_{self.key}_comparison")
class LexicalEvidenceExtractor(_Equal): evidence_type="NORMALIZED_NAME"; key="normalized_name"; weight=25
class AdministrativeEvidenceExtractor(_Equal): evidence_type="ADMINISTRATIVE_CONTEXT"; key="territory"; weight=20
class InstitutionalEvidenceExtractor(_Equal): evidence_type="INSTITUTIONAL_IDENTIFIER"; key="institutional_id"; weight=70
class OperatorEvidenceExtractor(_Equal): evidence_type="OPERATOR_CONTEXT"; key="operator"; weight=20
class EntityTypeEvidenceExtractor(EvidenceExtractor):
    evidence_type="ENTITY_TYPE"; weight=25
    def compare(self,a,b): return ([a.entity_type,b.entity_type],a.entity_type if a.entity_type==b.entity_type else f"{a.entity_type}!={b.entity_type}",EvidenceStatus.SUPPORTING if a.entity_type==b.entity_type else EvidenceStatus.CONFLICTING,1,1,"type_contract")
class GeographicEvidenceExtractor(EvidenceExtractor):
    evidence_type="GEOGRAPHIC_DISTANCE"; weight=35
    def compare(self,a,b):
        x,y=valid_coordinates(a),valid_coordinates(b)
        if not x or not y:return None
        d=distance_km(x,y); return ([x,y],round(d*1000,2),EvidenceStatus.SUPPORTING if d<=5 else EvidenceStatus.CONFLICTING,max(.5,1-d/10),.95,"haversine")
class SourceQualityEvidenceExtractor(EvidenceExtractor):
    evidence_type="SOURCE_QUALITY"; weight=5
    def compare(self,a,b):
        values=[a.attributes.get("quality_status"),b.attributes.get("quality_status")]
        confidence=.4 if any(str(v).upper() in {"QUARANTINE","CRITICAL","A_VERIFIER"} for v in values) else .9
        return (values,values,EvidenceStatus.NEUTRAL,confidence,.8,"source_quality_metadata")

DEFAULT_EXTRACTORS=(InstitutionalEvidenceExtractor(),EntityTypeEvidenceExtractor(),AdministrativeEvidenceExtractor(),GeographicEvidenceExtractor(),OperatorEvidenceExtractor(),LexicalEvidenceExtractor(),SourceQualityEvidenceExtractor())
def extract_all(source,target,extractors=DEFAULT_EXTRACTORS): return tuple(e for x in extractors for e in x.extract(source,target))
