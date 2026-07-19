"""API NIRE interne v1. Non montee publiquement hors application controlee."""
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from api.services.nire import (
    groupement_controlled_integration,
    locality_controlled_integration,
    locality_coverage,
    locality_enrichment_audit,
    locality_preintegration_validation,
    mno_audit,
)
from api.services.nire.operational import NireRole, ReviewActionType
from api.services.nire.operational_service import NireOperationalService
from api.services.nire.persistence import PostgresNireRepository

router = APIRouter()


def get_nire_service():
    return NireOperationalService(PostgresNireRepository())


def role(x_nire_role: str = Header("ANALYST")):
    try:
        return NireRole(x_nire_role.upper())
    except ValueError:
        raise HTTPException(403, "Role NIRE invalide")


class GenerateRequest(BaseModel):
    idempotency_key: str
    source_name: str
    target_name: str
    batch_size: int = Field(100, gt=0, le=5000)
    max_candidates: int = Field(1000, gt=0, le=100000)
    timeout_seconds: int = Field(300, gt=0, le=3600)


class ReviewRequest(BaseModel):
    author: str
    justification: str = Field(min_length=3)
    evidence_ids: list[str] = []
    correction: str | None = None


class MnoAuditRunRequest(BaseModel):
    enqueue_reviews: bool = False
    max_review_items: int = Field(500, gt=0, le=5000)
    source_path: str | None = None


class LocalityCoverageRunRequest(BaseModel):
    max_rows: int | None = Field(None, gt=0, le=100000)
    write_cache: bool = False


class LocalityEnrichmentRunRequest(BaseModel):
    write_cache: bool = False
    run_coverage_if_needed: bool = True


class LocalityPreintegrationRunRequest(BaseModel):
    write_cache: bool = False
    run_upstream_if_needed: bool = True


class LocalityControlledIntegrationRunRequest(BaseModel):
    apply: bool = True
    write_cache: bool = True


class GroupementControlledIntegrationRunRequest(BaseModel):
    apply: bool = True
    write_cache: bool = True


@router.post("/candidates/generate")
def generate(p: GenerateRequest, s=Depends(get_nire_service)):
    return asdict(
        s.start_run(
            p.idempotency_key,
            p.source_name,
            p.target_name,
            batch_size=p.batch_size,
            max_candidates=p.max_candidates,
            timeout_seconds=p.timeout_seconds,
        )
    )


@router.post("/resolve")
def resolve_controlled():
    return {
        "status": "CONTROLLED_ONLY",
        "automatic_merge": False,
        "detail": "Utiliser le workflow interne avec donnees controlees.",
    }


@router.get("/workspace/summary")
def workspace_summary(s=Depends(get_nire_service)):
    return s.repository.workspace_summary()


@router.get("/runs")
def runs(
    status: str | None = None,
    source_name: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, gt=0, le=100),
    s=Depends(get_nire_service),
):
    return {
        "offset": offset,
        "limit": limit,
        "items": list(s.repository.list_runs(status=status, source_name=source_name, offset=offset, limit=limit)),
    }


@router.get("/candidates/{candidate_id}")
def candidate(candidate_id: str, s=Depends(get_nire_service)):
    row = s.repository.get_candidate(candidate_id)
    if not row:
        raise HTTPException(404, "Candidat introuvable")
    return asdict(row)


@router.get("/candidates/{candidate_id}/dossier")
def dossier(candidate_id: str, s=Depends(get_nire_service)):
    row = s.repository.get_dossier(candidate_id)
    if not row:
        raise HTTPException(404, "Dossier introuvable")
    return row


@router.get("/candidates/{candidate_id}/history")
def history(candidate_id: str, s=Depends(get_nire_service)):
    return {"items": list(s.repository.get_history(candidate_id))}


@router.get("/decisions/{decision_id}")
def decision(decision_id: str, s=Depends(get_nire_service)):
    row = s.repository.get_decision(decision_id)
    if not row:
        raise HTTPException(404, "Decision introuvable")
    return asdict(row)


@router.get("/runs/{run_id}")
def run(run_id: str, s=Depends(get_nire_service)):
    row = s.repository.get_run(run_id)
    if not row:
        raise HTTPException(404, "Run introuvable")
    return asdict(row)


@router.get("/review-queue")
def queue(
    status: str | None = None,
    source_name: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=500),
    s=Depends(get_nire_service),
):
    rows = s.repository.list_reviews(status=status, source_name=source_name, offset=offset, limit=limit)
    return {"offset": offset, "limit": limit, "items": [asdict(x) for x in rows]}


@router.get("/review-dossiers")
def review_dossiers(
    status: str | None = None,
    source_name: str | None = None,
    target_name: str | None = None,
    domain: str | None = None,
    ambiguity: str | None = None,
    engine_decision: str | None = None,
    priority: int | None = None,
    requires_human_review: bool | None = None,
    min_score: float | None = None,
    min_confidence: float | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, gt=0, le=100),
    s=Depends(get_nire_service),
):
    filters = {
        "status": status,
        "source_name": source_name,
        "target_name": target_name,
        "domain": domain,
        "ambiguity": ambiguity,
        "engine_decision": engine_decision,
        "priority": priority,
        "requires_human_review": requires_human_review,
        "min_score": min_score,
        "min_confidence": min_confidence,
    }
    return {
        "offset": offset,
        "limit": limit,
        "items": list(s.repository.list_review_dossiers(filters=filters, offset=offset, limit=limit)),
    }


@router.get("/roles")
def roles(r=Depends(role)):
    matrix = {
        "ANALYST": ["VIEW", "PREPARE", "DEFER"],
        "REVIEWER": ["VIEW", "REJECT", "DEFER", "VALIDATE"],
        "APPROVER": ["VIEW", "VALIDATE", "REJECT", "CORRECT", "DEFER", "CANCEL"],
        "ADMIN": ["VIEW", "VALIDATE", "REJECT", "CORRECT", "DEFER", "CANCEL"],
    }
    return {"role": r.value, "actions": matrix[r.value], "contract_version": "nire-role-contract-1.0"}


@router.get("/mno-audit/status")
def mno_audit_status():
    return mno_audit.status_payload()


@router.post("/mno-audit/run")
def mno_audit_run(p: MnoAuditRunRequest, r=Depends(role), s=Depends(get_nire_service)):
    if r not in {NireRole.APPROVER, NireRole.ADMIN, NireRole.REVIEWER}:
        raise HTTPException(403, "Role insuffisant pour declencher l'audit MNO")
    path = Path(p.source_path) if p.source_path else None
    if path is not None and not path.is_file():
        raise HTTPException(404, "Source MNO introuvable")
    try:
        state = mno_audit.run_mno_audit(
            path,
            enqueue_reviews=p.enqueue_reviews,
            review_service=s if p.enqueue_reviews else None,
            max_review_items=p.max_review_items,
        )
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {
        "executed": state.executed,
        "source_loaded": state.source_loaded,
        "message": state.message,
        "kpis": state.kpis,
        "operators": state.operators,
        "meta": state.meta,
        "performance": state.performance,
        "potential_kpi_estimate": state.potential_kpi_estimate,
        "coherence": state.coherence,
        "review_enqueued": state.review_enqueued,
        "automatic_replacement": False,
        "physical_deletion": False,
        "national_kpi_unchanged": True,
    }


@router.get("/mno-audit/rows")
def mno_audit_rows(
    operator: str | None = None,
    classification: str | None = None,
    status: str | None = None,
    quarantine: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, gt=0, le=200),
):
    if not mno_audit.get_state().executed:
        raise HTTPException(409, "Aucun audit MNO execute — lancez POST /api/nire/mno-audit/run")
    return mno_audit.list_rows(
        operator=operator,
        classification=classification,
        status=status,
        quarantine=quarantine,
        offset=offset,
        limit=limit,
    )


@router.get("/mno-audit/colocations")
def mno_audit_colocations(
    multi_operator_only: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, gt=0, le=200),
):
    if not mno_audit.get_state().executed:
        raise HTTPException(409, "Aucun audit MNO execute")
    return mno_audit.list_colocations(multi_operator_only=multi_operator_only, offset=offset, limit=limit)


@router.get("/mno-audit/layers/{operator}")
def mno_audit_layer(
    operator: str,
    limit: int = Query(2000, gt=0, le=5000),
    include_planned: bool = True,
):
    if not mno_audit.get_state().executed:
        raise HTTPException(409, "Aucun audit MNO execute")
    return mno_audit.layer_geojson(operator, limit=limit, include_planned=include_planned)


@router.get("/mno-audit/source")
def mno_audit_source():
    state = mno_audit.get_state()
    if not state.executed or not state.meta:
        return {
            "source_loaded": False,
            "message": "Source MNO non chargee dans cet audit.",
            "default_path": str(mno_audit.DEFAULT_SOURCE),
        }
    return {"source_loaded": True, "meta": state.meta, "immutable": True}


@router.get("/locality-coverage/status")
def locality_coverage_status():
    return locality_coverage.status_payload()


@router.post("/locality-coverage/run")
def locality_coverage_run(p: LocalityCoverageRunRequest, r=Depends(role)):
    if r not in {NireRole.APPROVER, NireRole.ADMIN, NireRole.REVIEWER}:
        raise HTTPException(403, "Role insuffisant pour declencher le rapprochement localites")
    state = locality_coverage.run_locality_coverage(max_rows=p.max_rows, write_cache=p.write_cache)
    return {
        "executed": state.executed,
        "message": state.message,
        "kpis": state.kpis,
        "meta": state.meta,
        "performance": state.performance,
        "universes_not_forced_equal": True,
        "sources_immutable": True,
    }


@router.get("/locality-coverage/summary")
def locality_coverage_summary():
    if not locality_coverage.get_state().executed:
        raise HTTPException(409, "Aucun rapprochement localites — lancez POST /api/nire/locality-coverage/run")
    return locality_coverage.summary_payload()


@router.get("/locality-coverage/rows")
def locality_coverage_rows(
    classification: str | None = None,
    coverage_status: str | None = None,
    province: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, gt=0, le=200),
):
    if not locality_coverage.get_state().executed:
        raise HTTPException(409, "Aucun rapprochement localites — lancez POST /api/nire/locality-coverage/run")
    return locality_coverage.list_rows(
        classification=classification,
        coverage_status=coverage_status,
        province=province,
        offset=offset,
        limit=limit,
    )


@router.get("/locality-enrichment/status")
def locality_enrichment_status():
    return locality_enrichment_audit.status_payload()


@router.post("/locality-enrichment/run")
def locality_enrichment_run(p: LocalityEnrichmentRunRequest, r=Depends(role)):
    if r not in {NireRole.APPROVER, NireRole.ADMIN, NireRole.REVIEWER}:
        raise HTTPException(403, "Role insuffisant pour declencher l'audit enrichissement")
    state = locality_enrichment_audit.run_enrichment_audit(
        write_cache=p.write_cache,
        run_coverage_if_needed=p.run_coverage_if_needed,
    )
    return {
        "executed": state.executed,
        "message": state.message,
        "kpis": state.kpis,
        "funnel": state.funnel,
        "meta": state.meta,
        "performance": state.performance,
        "referential_not_modified": True,
        "auto_creation_disabled": True,
        "sources_immutable": True,
    }


@router.get("/locality-enrichment/summary")
def locality_enrichment_summary():
    if not locality_enrichment_audit.get_state().executed:
        raise HTTPException(409, "Aucun audit enrichissement — lancez POST /api/nire/locality-enrichment/run")
    return locality_enrichment_audit.summary_payload()


@router.get("/locality-enrichment/rows")
def locality_enrichment_rows(
    enrichment_class: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, gt=0, le=200),
):
    if not locality_enrichment_audit.get_state().executed:
        raise HTTPException(409, "Aucun audit enrichissement — lancez POST /api/nire/locality-enrichment/run")
    return locality_enrichment_audit.list_rows(
        enrichment_class=enrichment_class,
        offset=offset,
        limit=limit,
    )


@router.get("/locality-preintegration/status")
def locality_preintegration_status():
    return locality_preintegration_validation.status_payload()


@router.post("/locality-preintegration/run")
def locality_preintegration_run(p: LocalityPreintegrationRunRequest, r=Depends(role)):
    if r not in {NireRole.APPROVER, NireRole.ADMIN, NireRole.REVIEWER}:
        raise HTTPException(403, "Role insuffisant pour la validation pre-integration")
    state = locality_preintegration_validation.run_preintegration_validation(
        write_cache=p.write_cache,
        run_upstream_if_needed=p.run_upstream_if_needed,
    )
    return {
        "executed": state.executed,
        "message": state.message,
        "kpis": state.kpis,
        "simulation": state.simulation,
        "meta": state.meta,
        "performance": state.performance,
        "referential_not_modified": True,
        "auto_creation_disabled": True,
        "sources_immutable": True,
    }


@router.get("/locality-preintegration/summary")
def locality_preintegration_summary():
    if not locality_preintegration_validation.get_state().executed:
        raise HTTPException(
            409,
            "Aucune validation pre-integration — lancez POST /api/nire/locality-preintegration/run",
        )
    return locality_preintegration_validation.summary_payload()


@router.get("/locality-controlled-integration/status")
def locality_controlled_integration_status():
    return locality_controlled_integration.status_payload()


@router.post("/locality-controlled-integration/run")
def locality_controlled_integration_run(p: LocalityControlledIntegrationRunRequest, r=Depends(role)):
    if r not in {NireRole.APPROVER, NireRole.ADMIN}:
        raise HTTPException(403, "Role insuffisant pour l'integration controlee")
    state = locality_controlled_integration.run_controlled_integration(
        apply=p.apply,
        write_cache=p.write_cache,
    )
    return {
        "executed": state.executed,
        "message": state.message,
        "kpis": state.kpis,
        "meta": state.meta,
        "performance": state.performance,
        "base_untouched": True,
        "sources_immutable": True,
    }


@router.get("/groupement-controlled-integration/status")
def groupement_controlled_integration_status():
    return groupement_controlled_integration.status_payload()


@router.post("/groupement-controlled-integration/run")
def groupement_controlled_integration_run(p: GroupementControlledIntegrationRunRequest, r=Depends(role)):
    if r not in {NireRole.APPROVER, NireRole.ADMIN}:
        raise HTTPException(403, "Role insuffisant pour l'integration controlee")
    state = groupement_controlled_integration.run_controlled_integration(
        apply=p.apply,
        write_cache=p.write_cache,
    )
    return {
        "executed": state.executed,
        "message": state.message,
        "kpis": state.kpis,
        "meta": state.meta,
        "idempotence": state.idempotence,
        "candidates": state.candidates,
        "performance": state.performance,
        "base_untouched": True,
        "sources_immutable": True,
        "locality_candidates_not_integrated": True,
    }


def apply(review_id, p, action, r, s):
    try:
        return asdict(s.review(review_id, action, p.author, r, p.justification, p.evidence_ids, p.correction))
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except KeyError:
        raise HTTPException(404, "Revue introuvable")


@router.post("/review/{review_id}/validate")
def validate(review_id: str, p: ReviewRequest, r=Depends(role), s=Depends(get_nire_service)):
    return apply(review_id, p, ReviewActionType.VALIDATE, r, s)


@router.post("/review/{review_id}/reject")
def reject(review_id: str, p: ReviewRequest, r=Depends(role), s=Depends(get_nire_service)):
    return apply(review_id, p, ReviewActionType.REJECT, r, s)


@router.post("/review/{review_id}/correct")
def correct(review_id: str, p: ReviewRequest, r=Depends(role), s=Depends(get_nire_service)):
    return apply(review_id, p, ReviewActionType.CORRECT, r, s)


@router.post("/review/{review_id}/defer")
def defer(review_id: str, p: ReviewRequest, r=Depends(role), s=Depends(get_nire_service)):
    return apply(review_id, p, ReviewActionType.DEFER, r, s)


@router.post("/decisions/{decision_id}/cancel")
def cancel(decision_id: str, p: ReviewRequest, r=Depends(role), s=Depends(get_nire_service)):
    try:
        return asdict(s.cancel_decision(decision_id, p.author, r, p.justification))
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except KeyError:
        raise HTTPException(404, "Decision introuvable")
