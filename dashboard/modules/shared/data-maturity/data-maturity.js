/**
 * National Data Maturity Dashboard — Salle de Pilotage.
 * Totaux exclusivement depuis /api/data-maturity (Data First).
 */
(function initDataMaturityDashboard(global) {
  const API_BASE = `${global.location.protocol}//${global.location.hostname}:8001`;

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function fmt(value) {
    if (value == null || value === '') return '—';
    if (typeof value === 'number') return value.toLocaleString('fr-FR');
    return String(value);
  }

  function fetchJson(path) {
    return fetch(`${API_BASE}${path}`, { headers: { Accept: 'application/json' }, cache: 'no-store' })
      .then((r) => {
        if (!r.ok) throw new Error(path);
        return r.json();
      });
  }

  function bandClass(band) {
    const code = (band && band.code) || 'unknown';
    return `ndm-band ndm-band--${escapeHtml(code)}`;
  }

  function stars(n) {
    const s = Math.max(0, Math.min(5, Number(n) || 0));
    return `${'★'.repeat(s)}${'☆'.repeat(5 - s)}`;
  }

  function ensureHost() {
    let host = document.querySelector('#esr-data-maturity');
    if (host) return host;
    const root = document.querySelector('.esr-root .esr-col-main') || document.querySelector('.esr-root');
    if (!root) return null;
    host = document.createElement('section');
    host.id = 'esr-data-maturity';
    host.className = 'esr-card ndm-card';
    host.innerHTML = `
      <header class="esr-card-header">
        <h3>Maturité des Données Nationales</h3>
        <div class="ndm-header-actions">
          <button type="button" class="secondary-button" id="ndm-btn-report">Rapport Direction</button>
          <button type="button" class="secondary-button" id="ndm-btn-refresh">Actualiser</button>
        </div>
      </header>
      <div id="esr-data-maturity-body" class="ndm-body">Chargement…</div>`;
    const maturitySdg = document.querySelector('#esr-sdg-maturity');
    if (maturitySdg && maturitySdg.parentNode) {
      maturitySdg.parentNode.insertBefore(host, maturitySdg);
    } else {
      root.prepend(host);
    }
    return host;
  }

  function renderDetail(domain) {
    if (!domain) return '';
    const dims = Object.values(domain.dimensions || {});
    return `
      <article class="ndm-detail" data-code="${escapeHtml(domain.code)}">
        <header>
          <h4>${escapeHtml(domain.label)} — ${domain.score != null ? `${fmt(domain.score)} %` : '—'}</h4>
          <span class="${bandClass(domain.band)}">${escapeHtml(domain.band?.label || '')}</span>
        </header>
        <p class="ndm-meta">Source : ${escapeHtml(domain.source || '—')} · As-of : ${escapeHtml(domain.as_of || '—')} · Version : ${escapeHtml(domain.version || '—')}</p>
        <p class="ndm-meta">Objets : ${fmt(domain.object_count)} · Relations : ${escapeHtml(domain.relations || '—')}</p>
        <div class="ndm-dims">${dims.map((d) => `
          <span title="${escapeHtml(d.label)}">${escapeHtml(d.label)} <strong>${d.score != null ? fmt(d.score) : '—'}</strong></span>
        `).join('')}</div>
        ${(domain.strengths || []).length ? `<p><em>Forces :</em> ${domain.strengths.map(escapeHtml).join(' · ')}</p>` : ''}
        ${(domain.weaknesses || []).length ? `<p><em>Faiblesses :</em> ${domain.weaknesses.map(escapeHtml).join(' · ')}</p>` : ''}
        ${(domain.anomalies || []).length ? `<p><em>Anomalies :</em> ${domain.anomalies.map(escapeHtml).join(' · ')}</p>` : ''}
        ${(domain.recommendations || []).length ? `<p><em>Recommandations :</em> ${domain.recommendations.map(escapeHtml).join(' · ')}</p>` : ''}
      </article>`;
  }

  function mountDataMaturityDashboard() {
    const host = ensureHost();
    if (!host) return Promise.resolve(null);
    const body = host.querySelector('#esr-data-maturity-body') || host;
    body.innerHTML = '<p class="esr-muted">Calcul de la maturité nationale…</p>';

    return fetchJson('/api/data-maturity')
      .then((payload) => {
        const dash = payload.dashboard || [];
        const priorities = payload.priorities || [];
        const roadmap = payload.roadmap || {};
        body.innerHTML = `
          <div class="ndm-national">
            <div>
              <span class="ndm-national-label">Maturité nationale</span>
              <strong class="ndm-national-score">${payload.national_score != null ? `${fmt(payload.national_score)} %` : '—'}</strong>
              <span class="${bandClass(payload.national_band)}">${escapeHtml(payload.national_band?.label || '')}</span>
            </div>
            <p class="dxl-note">Moyenne pondérée des référentiels scorés — dimensions absentes exclues (Data First).</p>
          </div>
          <div class="ndm-grid">
            ${dash.map((d) => `
              <button type="button" class="ndm-tile ${bandClass(d.band)}" data-ndm-code="${escapeHtml(d.code)}" title="${escapeHtml(d.label)}">
                <span>${escapeHtml(d.label)}</span>
                <strong>${d.score != null ? `${fmt(d.score)} %` : '—'}</strong>
              </button>`).join('')}
          </div>
          <div id="ndm-detail-host" class="ndm-detail-host"></div>
          <h4>Données prioritaires à acquérir</h4>
          <ul class="ndm-priorities">${priorities.map((p) => `
            <li><span class="ndm-stars" aria-label="${p.stars} étoiles">${stars(p.stars)}</span>
              <strong>${escapeHtml(p.label)}</strong> — ${escapeHtml(p.reason || '')}</li>`).join('') || '<li>Aucune priorité critique</li>'}
          </ul>
          <h4>Feuille de route data</h4>
          <div class="ndm-roadmap">
            <div><h5>Court terme</h5><ul>${(roadmap.short_term || []).map((i) => `<li>${escapeHtml(i.action)} <em>(${escapeHtml(i.expected_gain)})</em></li>`).join('') || '<li>—</li>'}</ul></div>
            <div><h5>Moyen terme</h5><ul>${(roadmap.medium_term || []).map((i) => `<li>${escapeHtml(i.action)} <em>(${escapeHtml(i.expected_gain)})</em></li>`).join('') || '<li>—</li>'}</ul></div>
            <div><h5>Long terme</h5><ul>${(roadmap.long_term || []).map((i) => `<li>${escapeHtml(i.action)} <em>(${escapeHtml(i.expected_gain)})</em></li>`).join('') || '<li>—</li>'}</ul></div>
          </div>
          <p class="dxl-note">Calcul : ${escapeHtml(payload._meta?.generated_at || '')}</p>`;

        const detailHost = body.querySelector('#ndm-detail-host');
        const byCode = Object.fromEntries((payload.domains || []).map((d) => [d.code, d]));
        body.querySelectorAll('[data-ndm-code]').forEach((btn) => {
          btn.addEventListener('click', () => {
            const code = btn.getAttribute('data-ndm-code');
            if (detailHost) detailHost.innerHTML = renderDetail(byCode[code]);
          });
        });

        host.querySelector('#ndm-btn-refresh')?.addEventListener('click', () => mountDataMaturityDashboard());
        host.querySelector('#ndm-btn-report')?.addEventListener('click', () => {
          global.open(`${API_BASE}/api/data-maturity/report.html`, '_blank', 'noopener');
        });
        return payload;
      })
      .catch(() => {
        body.innerHTML = '<p class="esr-muted">Maturité des données nationales indisponible.</p>';
        return null;
      });
  }

  global.DataMaturityDashboard = { mountDataMaturityDashboard };
  // Compat ESR : aussi exposé via TerritorialImpactUI si déjà présent
  global.TerritorialImpactUI = global.TerritorialImpactUI || {};
  global.TerritorialImpactUI.mountDataMaturityDashboard = mountDataMaturityDashboard;
})(window);
