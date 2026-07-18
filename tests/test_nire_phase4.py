from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.routes import nire as route
from api.services.nire.operational import *
from api.services.nire.operational_service import NireOperationalService
from api.services.nire.persistence import InMemoryNireRepository

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"dashboard/index.html").read_text(encoding="utf-8")
APP=(ROOT/"dashboard/app.js").read_text(encoding="utf-8")
JS=(ROOT/"dashboard/modules/nire-workspace/nire-workspace.js").read_text(encoding="utf-8")
CSS=(ROOT/"dashboard/modules/nire-workspace/nire-workspace.css").read_text(encoding="utf-8")

def seeded():
    repo=InMemoryNireRepository(); service=NireOperationalService(repo); run=service.start_run("synthetic-phase4","CENI_SYNTHETIC","EDUCATION_SYNTHETIC")
    payload={"ambiguity":"HIGH","domain":"EDUCATION","blocking_conflicts":["IDENTIFIER_CONFLICT"],"source_entity":{"entity_type":"SCHOOL","attributes":{"name":"EP TEST","normalized_name":"EP TEST","latitude":-4.3,"longitude":15.3,"province":"KINSHASA","territory":"TSHANGU","quality_status":"SYNTHETIC","provenance":"TEST_SYNTHETIC"}},"target_entity":{"entity_type":"SCHOOL","attributes":{"name":"EP TEST B","normalized_name":"EP TEST","latitude":-4.31,"longitude":15.31,"province":"KINSHASA","territory":"TSHANGU","quality_status":"SYNTHETIC","provenance":"TEST_SYNTHETIC"}}}
    c=StoredCandidate("CAN-SYNTHETIC",run.run_id,"CENI_SYNTHETIC","SRC-1","EDUCATION_SYNTHETIC","TGT-1",62,.74,"AMBIGUOUS","Explication synthétique persistée.",True,payload)
    ev=(StoredEvidence("E-POS",c.candidate_id,"NORMALIZED_NAME","CENI_SYNTHETIC","SRC-1",["EP TEST","EP TEST"],25,.9,.9,{"status":"SUPPORTING","method":"synthetic","extractor_version":"test"}),StoredEvidence("E-NEG",c.candidate_id,"OPERATOR_CONFLICT","CENI_SYNTHETIC","SRC-1",["A","B"],-30,.9,.9,{"status":"CONFLICTING","method":"synthetic","extractor_version":"test"}))
    d=StoredDecision("DEC-SYNTHETIC",c.candidate_id,"AMBIGUOUS",62,run.engine_version,run.rule_version,"Explication synthétique persistée."); review=service.persist_resolution(run,c,d,ev)
    return repo,service,run,c,d,review

@pytest.fixture
def client():
    repo,service,*_=seeded(); app=FastAPI();app.include_router(route.router,prefix="/api/nire");app.dependency_overrides[route.get_nire_service]=lambda:service
    return TestClient(app),repo,service

def test_workspace_route_and_navigation_exist(): assert 'data-route="nire-workspace"' in HTML and 'Résolution d’identité' in HTML
def test_workspace_javascript_is_lazy_loaded(): assert 'modules/nire-workspace/nire-workspace.js' not in HTML and "document.createElement('script')" in APP
def test_dashboard_initial_has_no_nire_fetch():
    before=APP.split('function loadNireWorkspaceOnDemand')[0]; assert '/api/nire' not in before
def test_workspace_css_is_lazy_loaded(): assert 'nire-workspace.css' not in HTML and "document.createElement('link')" in APP
def test_kpi_aggregates(client):
    c,_,_=client;x=c.get('/api/nire/workspace/summary');assert x.status_code==200 and x.json()['pending']==1 and x.json()['ambiguous']==1
def test_runs_pagination(client):
    c,_,_=client;x=c.get('/api/nire/runs?offset=0&limit=1');assert x.status_code==200 and len(x.json()['items'])==1
def test_review_pagination(client):
    c,_,_=client;x=c.get('/api/nire/review-dossiers?offset=0&limit=1');assert x.status_code==200 and len(x.json()['items'])==1
@pytest.mark.parametrize('query',["status=PENDING","source_name=CENI_SYNTHETIC","target_name=EDUCATION_SYNTHETIC","ambiguity=HIGH","min_score=60","min_confidence=0.7"])
def test_review_filters(client,query):
    c,_,_=client;assert len(c.get('/api/nire/review-dossiers?'+query).json()['items'])==1
def test_open_resolution_dossier(client):
    c,_,_=client;x=c.get('/api/nire/candidates/CAN-SYNTHETIC/dossier');assert x.status_code==200 and x.json()['source_entity']['attributes']['name']=='EP TEST'
def test_side_by_side_comparison_contract(): assert 'Comparaison champ par champ' in JS and 'Entité source' in JS and 'Candidat cible' in JS
def test_map_two_geometries_supported(): assert "points.length===2" in JS and 'fitBounds' in JS
def test_map_one_geometry_supported(): assert "else state.map.setView(points[0].p,12)" in JS
def test_no_map_without_geometry(): assert 'Aucune donnée géographique exploitable pour cette comparaison.' in JS
def test_zero_zero_rejected(): assert 'lat===0&&lon===0' in JS
def test_evidence_groups_present():
    for label in ('Preuves positives','Preuves négatives','Conflits bloquants','Informations complémentaires'): assert label in JS
def test_persisted_engine_explanation_only(): assert "x.explanation||c.explanation" in JS and 'Explication synthétique persistée.' == seeded()[4].explanation
@pytest.mark.parametrize('action,path,role',[('validate','validate','REVIEWER'),('reject','reject','REVIEWER'),('correct','correct','APPROVER'),('defer','defer','ANALYST')])
def test_review_actions_require_justification(client,action,path,role):
    c,_,_=client;review=seeded()[-1]; assert c.post(f'/api/nire/review/{review.review_id}/{path}',headers={'X-NIRE-Role':role},json={'author':'test','justification':'raison synthétique','correction':'POSSIBLE_MATCH' if action=='correct' else None}).status_code==200
def test_cancel_decision_and_preserve_old(client):
    c,repo,_=client;x=c.post('/api/nire/decisions/DEC-SYNTHETIC/cancel',headers={'X-NIRE-Role':'ADMIN'},json={'author':'test','justification':'annulation synthétique'});assert x.status_code==200 and repo.get_decision('DEC-SYNTHETIC').decision=='AMBIGUOUS'
def test_history_endpoint(client):
    c,_,_=client;assert len(c.get('/api/nire/candidates/CAN-SYNTHETIC/history').json()['items'])>=1
def test_role_contract_controls(client):
    c,_,_=client;assert c.get('/api/nire/roles',headers={'X-NIRE-Role':'ANALYST'}).json()['role']=='ANALYST' and c.get('/api/nire/roles',headers={'X-NIRE-Role':'INVALID'}).status_code==403
def test_mno_empty_state_has_no_numbers(client):
    c,_,_=client;x=c.get('/api/nire/mno-audit/status').json();assert x['executed'] is False and x['operators']==[] and x['source_loaded'] is False
def test_mno_ui_is_explicitly_not_calculated(): assert 'Non calculé — aucune source MNO validée' in JS and all(x in JS for x in ['Orange','Vodacom','Airtel','Africell'])
def test_orange_vodacom_rule_documented(): assert '100 %' in JS and 'Aucune suppression physique' in JS and 'Aucun remplacement automatique' in JS
def test_payloads_are_bounded(): assert 'le=100' in (ROOT/'api/routes/nire.py').read_text(encoding='utf-8') and 'pageSize:25' in JS
def test_client_performance_instrumented(): assert JS.count('performance.now()')>=4 and all(x in JS for x in ['kpi_ms','queue_ms','dossier_ms'])
def test_workspace_professional_error_hides_failed_fetch(): assert 'Failed to fetch' not in JS and 'momentanément indisponible' in JS
def test_no_real_mno_or_protected_source_access(): assert 'data/raw/ceni' not in JS and 'MNO_FICTIF' not in JS and '/upload' not in JS
def test_workspace_documentation_exists(): assert (ROOT/'PROJECT_MANAGEMENT/ARCHITECTURE/NIRE_PHASE_4.md').exists()
