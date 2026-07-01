from __future__ import annotations

import io
import json
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.fdsu_importer import FDSUExcelImporter, ImportReport
from app.models import Province, Territoire, Collectivite, Groupement, Village, Site

router = APIRouter()

# Simple in-memory job store: job_id -> {status, report, error}
JOBS: Dict[str, Dict[str, Any]] = {}


@router.get("/ui")
def ui_page():
    html = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Import Référentiel FDSU</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 20px; }
      .panel { border: 1px solid #ddd; padding: 12px; margin-bottom: 12px; }
      #progress { width: 100%; height: 20px; background: #eee; border-radius: 4px; overflow: hidden; }
      #bar { height: 100%; width: 0%; background: #4caf50; transition: width 0.3s; }
    </style>
  </head>
  <body>
    <h2>Import Référentiel FDSU</h2>
    <div class="panel">
      <input id="file" type="file" accept=".xlsx" />
      <select id="entity">
        <option value="provinces">Provinces</option>
        <option value="territoires">Territoires</option>
        <option value="collectivites">Collectivités</option>
        <option value="groupements">Groupements</option>
        <option value="villages">Villages</option>
        <option value="sites">Sites</option>
      </select>
      <label><input type="checkbox" id="create_parents" /> Créer parents manquants</label>
      <br/><br/>
      <button id="preview">Prévisualiser</button>
      <button id="import">Importer</button>
    </div>

    <div id="previewPanel" class="panel" style="display:none">
      <h3>Prévisualisation</h3>
      <div id="previewContent"></div>
    </div>

    <div id="importPanel" class="panel" style="display:none">
      <h3>Import en cours</h3>
      <div id="progress"><div id="bar"></div></div>
      <pre id="importLog"></pre>
    </div>

    <script>
      const fileInput = document.getElementById('file');
      const entitySelect = document.getElementById('entity');
      const previewBtn = document.getElementById('preview');
      const importBtn = document.getElementById('import');
      const previewPanel = document.getElementById('previewPanel');
      const previewContent = document.getElementById('previewContent');
      const importPanel = document.getElementById('importPanel');
      const bar = document.getElementById('bar');
      const importLog = document.getElementById('importLog');

      previewBtn.addEventListener('click', async () => {
        if (!fileInput.files.length) { alert('Choisissez un fichier'); return; }
        const fd = new FormData();
        fd.append('file', fileInput.files[0]);
        fd.append('entity', entitySelect.value);
        fd.append('create_parents', document.getElementById('create_parents').checked ? '1' : '0');
        previewContent.innerText = 'Analyse en cours...';
        previewPanel.style.display = 'block';
        const res = await fetch('/imports/preview', { method: 'POST', body: fd });
        if (!res.ok) { previewContent.innerText = 'Erreur: ' + await res.text(); return; }
        const data = await res.json();
        previewContent.innerText = JSON.stringify(data, null, 2);
      });

      importBtn.addEventListener('click', async () => {
        if (!fileInput.files.length) { alert('Choisissez un fichier'); return; }
        const fd = new FormData();
        fd.append('file', fileInput.files[0]);
        fd.append('entity', entitySelect.value);
        fd.append('create_parents', document.getElementById('create_parents').checked ? '1' : '0');
        importPanel.style.display = 'block';
        bar.style.width = '0%';
        importLog.innerText = 'Démarrage...';
        const res = await fetch('/imports/start', { method: 'POST', body: fd });
        if (!res.ok) { importLog.innerText = 'Erreur démarrage: ' + await res.text(); return; }
        const { job_id } = await res.json();
        // poll status
        const poll = setInterval(async () => {
          const s = await fetch('/imports/status/' + job_id);
          if (!s.ok) { importLog.innerText = 'Erreur status'; clearInterval(poll); return; }
          const j = await s.json();
          if (j.status === 'running') {
            bar.style.width = '40%';
            importLog.innerText = 'Import en cours...';
          } else if (j.status === 'finished') {
            bar.style.width = '100%';
            importLog.innerText = JSON.stringify(j.report, null, 2);
            clearInterval(poll);
          } else if (j.status === 'failed') {
            bar.style.width = '100%';
            importLog.innerText = 'Échec: ' + j.error;
            clearInterval(poll);
          }
        }, 1000);
      });
    </script>
  </body>
</html>
"""
    return html


@router.post("/preview")
async def preview(file: UploadFile = File(...), entity: str = Form(...), create_parents: str = Form('0')):
    content = await file.read()
    try:
        df = pd.read_excel(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Fichier Excel invalide: {exc}")

    importer = FDSUExcelImporter(username="web")
    mapping = importer.detect_columns(df)

    # determine code field and model
    ent = entity.lower()
    model = None
    parent_checks = []
    code_field = None
    if ent in ("province", "provinces"):
        model = Province
        code_field = mapping.get('province_code')
    elif ent in ("territoire", "territoires"):
        model = Territoire
        code_field = mapping.get('territoire_code')
        parent_checks = [('province_code', Province)]
    elif ent in ("collectivite", "collectivites"):
        model = Collectivite
        code_field = mapping.get('collectivite_code')
        parent_checks = [('territoire_code', Territoire)]
    elif ent in ("groupement", "groupements"):
        model = Groupement
        code_field = mapping.get('groupement_code')
        parent_checks = [('collectivite_code', Collectivite)]
    elif ent in ("village", "villages"):
        model = Village
        code_field = mapping.get('village_code')
        parent_checks = [('groupement_code', Groupement)]
    elif ent in ("site", "sites"):
        model = Site
        code_field = mapping.get('site_code')
        parent_checks = [('village_code', Village)]
    else:
        raise HTTPException(status_code=400, detail="Entité inconnue")

    rows_total = len(df)
    duplicates = []
    errors = []
    to_create = 0
    to_update = 0

    seen = set()
    with Session(engine) as session:
        for idx, row in df.iterrows():
            rnum = int(idx) + 1
            row_dict = {c: (None if pd.isna(v) else v) for c, v in row.items()}
            code_val = row_dict.get(code_field) if code_field else None
            code_key = str(code_val).strip() if code_val is not None else None
            if code_key:
                if code_key in seen:
                    duplicates.append({"row": rnum, "code": code_key})
                    continue
                seen.add(code_key)

            # parent checks
            parent_missing = False
            for field_name, parent_model in parent_checks:
                parent_code = row_dict.get(mapping.get(field_name))
                if not parent_code:
                    parent_missing = True
                    errors.append({"row": rnum, "error": f"Parent {field_name} manquant"})
                    break
                parent_id = importer._find_parent_id(session, parent_model, parent_code)
                if parent_id is None and not bool(int(create_parents)):
                    parent_missing = True
                    errors.append({"row": rnum, "error": f"Parent {field_name} introuvable: {parent_code}"})
                    break

            if parent_missing:
                continue

            # determine if exists
            exists = False
            if ent in ("province", "provinces") and code_key:
                exists = session.scalar(select(Province).where(Province.code == code_key)) is not None
            elif ent in ("territoire", "territoires") and code_key:
                prov_code = row_dict.get(mapping.get('province_code'))
                prov_id = importer._find_parent_id(session, Province, prov_code)
                exists = session.scalar(select(Territoire).where(Territoire.code == code_key, Territoire.province_id == prov_id)) is not None
            elif ent in ("collectivite", "collectivites") and code_key:
                territoire_code = row_dict.get(mapping.get('territoire_code'))
                territoire_id = importer._find_parent_id(session, Territoire, territoire_code)
                exists = session.scalar(select(Collectivite).where(Collectivite.code == code_key, Collectivite.territoire_id == territoire_id)) is not None
            elif ent in ("groupement", "groupements") and code_key:
                collectivite_code = row_dict.get(mapping.get('collectivite_code'))
                collectivite_id = importer._find_parent_id(session, Collectivite, collectivite_code)
                exists = session.scalar(select(Groupement).where(Groupement.code == code_key, Groupement.collectivite_id == collectivite_id)) is not None
            elif ent in ("village", "villages") and code_key:
                groupement_code = row_dict.get(mapping.get('groupement_code'))
                groupement_id = importer._find_parent_id(session, Groupement, groupement_code)
                exists = session.scalar(select(Village).where(Village.code == code_key, Village.groupement_id == groupement_id)) is not None
            elif ent in ("site", "sites") and code_key:
                exists = session.scalar(select(Site).where(Site.code_site == code_key)) is not None

            if exists:
                to_update += 1
            else:
                to_create += 1

    return {
        "rows_total": rows_total,
        "duplicates": duplicates,
        "errors": errors[:50],
        "to_create": to_create,
        "to_update": to_update,
        "mapping": mapping,
    }


@router.post('/start')
async def start_import(file: UploadFile = File(...), entity: str = Form(...), create_parents: str = Form('0')):
    content = await file.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    tmp.write(content)
    tmp.flush()
    tmp.close()

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "running", "report": None, "error": None}

    def _run():
        try:
            imp = FDSUExcelImporter(username='web')
            report: ImportReport = imp.import_file(Path(tmp.name), entity=entity, create_parents=bool(int(create_parents)))
            JOBS[job_id]["status"] = "finished"
            JOBS[job_id]["report"] = report.as_dict()
        except Exception as e:
            JOBS[job_id]["status"] = "failed"
            JOBS[job_id]["error"] = str(e)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return {"job_id": job_id}


@router.get('/status/{job_id}')
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")
    return job
