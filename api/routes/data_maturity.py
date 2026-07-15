"""API — National Data Maturity Dashboard."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from api.services import data_maturity_engine as ndm

router = APIRouter()


@router.get("", summary="Maturité nationale des données")
@router.get("/", summary="Maturité nationale des données")
def get_maturity() -> dict[str, Any]:
    return ndm.build_national_maturity()


@router.get("/details", summary="Détail par référentiel")
def get_details() -> dict[str, Any]:
    return ndm.build_details()


@router.get("/roadmap", summary="Feuille de route data + priorités")
def get_roadmap() -> dict[str, Any]:
    return ndm.build_roadmap_payload()


@router.get("/map", summary="GeoJSON maturité data (≠ couverture radio)")
def get_map() -> dict[str, Any]:
    return ndm.build_map_payload()


@router.get("/report", summary="Rapport Direction (JSON)")
def get_report() -> dict[str, Any]:
    return ndm.build_report_payload()


@router.get("/report.html", summary="Rapport imprimable (HTML → PDF navigateur)", response_class=HTMLResponse)
def get_report_html() -> HTMLResponse:
    report = ndm.build_report_payload()
    score = report.get("national_score")
    band = (report.get("national_band") or {}).get("label") or "—"
    rows = "".join(
        f"<tr><td>{d.get('label')}</td><td>{d.get('score') if d.get('score') is not None else '—'}%</td>"
        f"<td>{(d.get('band') or {}).get('label') or '—'}</td></tr>"
        for d in (report.get("dashboard") or [])
    )
    prios = "".join(
        f"<li>{'★' * int(p.get('stars') or 0)}{'☆' * (5 - int(p.get('stars') or 0))} "
        f"<strong>{p.get('label')}</strong> — {p.get('reason')}</li>"
        for p in (report.get("priorities") or [])
    )
    road = report.get("roadmap") or {}

    def road_block(title: str, items: list) -> str:
        lis = "".join(f"<li><strong>{i.get('action')}</strong> → {i.get('expected_gain')}</li>" for i in (items or []))
        return f"<h3>{title}</h3><ul>{lis or '<li>Aucun item</li>'}</ul>"

    html = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"/>
<title>Rapport National de Maturité des Données</title>
<style>
body{{font-family:Georgia,serif;margin:2rem;color:#0f172a}}
h1{{font-size:1.6rem}} table{{border-collapse:collapse;width:100%;margin:1rem 0}}
th,td{{border:1px solid #cbd5e1;padding:.4rem .6rem;text-align:left}}
th{{background:#f1f5f9}} .muted{{color:#64748b;font-size:.9rem}}
@media print{{button{{display:none}}}}
</style></head><body>
<button onclick="window.print()">Imprimer / PDF</button>
<h1>Rapport National de Maturité des Données</h1>
<p class="muted">SIG-FDSU RDC · Direction · {report.get('_meta', {}).get('generated_at', '')}</p>
<p><strong>Maturité nationale :</strong> {score if score is not None else '—'} % ({band})</p>
<p class="muted">Calcul : moyenne pondérée des scores domaines (dimensions null exclues). Data First.</p>
<h2>Tableau de bord</h2>
<table><thead><tr><th>Référentiel</th><th>Score</th><th>Bande</th></tr></thead>
<tbody>{rows}</tbody></table>
<h2>Données prioritaires à acquérir</h2>
<ul>{prios or '<li>Aucune priorité critique</li>'}</ul>
{road_block('Court terme', road.get('short_term'))}
{road_block('Moyen terme', road.get('medium_term'))}
{road_block('Long terme', road.get('long_term'))}
<p class="muted">{report.get('_meta', {}).get('note') or ''}</p>
</body></html>"""
    return HTMLResponse(content=html)
