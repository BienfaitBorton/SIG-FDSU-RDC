/**
 * Moteur d’Impact Territorial — UI dossier de décision + graphiques.
 * Les totaux viennent exclusivement de l’API /api/territorial-impact.
 */
(function initTerritorialImpactUI(global) {
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

  function ensureSection() {
    let host = document.querySelector('#dxl-section-territorial-impact');
    if (host) return host;
    const reco = document.querySelector('#dxl-section-reco');
    host = document.createElement('section');
    host.id = 'dxl-section-territorial-impact';
    host.className = 'dxl-section';
    host.setAttribute('aria-label', 'Impact territorial et populationnel');
    if (reco && reco.parentNode) {
      reco.parentNode.insertBefore(host, reco);
    } else {
      document.querySelector('.decision-experience-module')?.appendChild(host);
    }
    return host;
  }

  function cumulativeSvg(points, mode) {
    const series = (points || []).filter((p) => p.cumulative_population_covered_gain != null);
    if (series.length < 2) {
      return '<p class="dxl-note">Courbe cumulative indisponible pour ce périmètre.</p>';
    }
    const w = 420;
    const h = 160;
    const pad = 28;
    const maxY = Math.max(...series.map((p) => Number(p.cumulative_population_covered_gain) || 0), 1);
    const coords = series.map((p, i) => {
      const x = pad + (i * (w - 2 * pad)) / (series.length - 1);
      const y = h - pad - ((Number(p.cumulative_population_covered_gain) || 0) / maxY) * (h - 2 * pad);
      return `${x},${y}`;
    });
    const dash = mode === 'simulation' ? '6 4' : (mode === 'real' ? '0' : '4 3');
    const stroke = mode === 'real' ? '#059669' : (mode === 'simulation' ? '#94a3b8' : '#0ea5e9');
    const kindLabel = mode === 'real' ? 'observée' : (mode === 'simulation' ? 'simulée' : 'projetée');
    return `
      <p class="dxl-note">Courbe ${escapeHtml(kindLabel)} (trait ${mode === 'real' ? 'plein' : 'pointillé'}).</p>
      <svg class="tie-chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="Progression cumulative ${kindLabel}">
        <polyline fill="none" stroke="${stroke}" stroke-width="2.5" stroke-dasharray="${dash}" points="${coords.join(' ')}" />
        ${series.map((p, i) => {
          const [x, y] = coords[i].split(',');
          return `<circle cx="${x}" cy="${y}" r="3.5" fill="${stroke}">
            <title>${escapeHtml(p.label || '')} — +${fmt(p.new_population_covered)} bénéficiaires · cumul ${fmt(p.cumulative_population_covered_gain)} · ${escapeHtml(p.badge || kindLabel)}</title>
          </circle>`;
        }).join('')}
      </svg>`;
  }

  function barsSvg(items) {
    const rows = (items || []).filter((b) => Number(b.value) > 0).slice(0, 12);
    if (!rows.length) return '<p class="dxl-note">Aucune contribution chiffrée.</p>';
    const maxV = Math.max(...rows.map((b) => Number(b.value) || 0), 1);
    return `<div class="tie-bars">${rows.map((b) => {
      const pct = Math.round((100 * (Number(b.value) || 0)) / maxV);
      const tone = b.nature === 'beneficiaires_potentiels_ccn' ? 'is-ccn' : 'is-site';
      return `<div class="tie-bar-row ${tone}" title="${escapeHtml(b.nature || '')}">
        <span class="tie-bar-label">${escapeHtml(b.label || b.id)}</span>
        <span class="tie-bar-track"><span class="tie-bar-fill" style="width:${pct}%"></span></span>
        <span class="tie-bar-val">+${fmt(b.value)}</span>
      </div>`;
    }).join('')}</div>`;
  }

  function composeBlocks(comp) {
    if (!comp) return '';
    const parts = [
      { label: 'Déjà couverte', value: comp.already_covered, cls: 'is-covered' },
      { label: 'Nouvellement couverte', value: comp.newly_covered_cumulative, cls: 'is-new' },
      { label: 'Restant non couverte', value: comp.remaining_uncovered, cls: 'is-remain' },
    ];
    if (comp.without_reliable_data != null) {
      parts.push({ label: 'Sans donnée fiable', value: comp.without_reliable_data, cls: 'is-unknown' });
    }
    return `<div class="tie-compose">${parts.map((p) => `
      <div class="tie-compose-seg ${p.cls}" style="flex:${Number(p.value) || 0.001}" title="${escapeHtml(p.label)}">
        <span>${escapeHtml(p.label)}</span><strong>${fmt(p.value)}</strong>
      </div>`).join('')}</div>
    <p class="dxl-note">${escapeHtml(comp.note || '')}</p>`;
  }

  function localitiesProgressionBlock(lp) {
    if (!lp) return '';
    return `
      <div class="dxl-kpi-strip tie-loc-prog">
        <article><span>Localités couvertes (baseline)</span><strong>${fmt(lp.localities_covered_baseline)}</strong></article>
        <article><span>Localités ajoutées (scénario)</span><strong>${fmt(lp.localities_added_in_scenario)}</strong></article>
        <article><span>Cumul après scénario</span><strong>${fmt(lp.localities_cumulative_covered_after_scenario)}</strong></article>
        <article><span>Restantes non couvertes</span><strong>${fmt(lp.localities_remaining_uncovered)}</strong></article>
      </div>
      <p class="dxl-note">${escapeHtml(lp.note || '')}</p>`;
  }

  function renderLocalitiesTable(localities, onFocus) {
    const rows = localities || [];
    if (!rows.length) return '<p class="dxl-note">Aucune localité NCI associée dans le rayon.</p>';
    return `
      <div class="tie-table-wrap">
        <table class="tie-table">
          <thead><tr>
            <th>Localité</th><th>Population</th><th>Avant</th><th>Après</th><th>Distance</th><th>Source</th><th>Confiance</th>
          </tr></thead>
          <tbody>
            ${rows.map((r, idx) => `
              <tr class="tie-loc-row" data-tie-loc="${idx}" tabindex="0">
                <td>${escapeHtml(r.name || r.need_id || '—')}</td>
                <td>${fmt(r.population)}</td>
                <td>${escapeHtml(r.before || '—')}</td>
                <td>${escapeHtml(r.after || r.state || '—')}</td>
                <td>${r.distance_m != null ? `${Math.round(r.distance_m)} m` : '—'}</td>
                <td>${escapeHtml((r.source || '').split('/').pop() || '—')}</td>
                <td>${escapeHtml(r.confidence || '—')}</td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
  }

  function renderSiteProfile(host, profile) {
    const impact = profile.impact || {};
    const baseline = profile.baseline || {};
    const dep = profile.deployment || {};
    const badges = profile.ui_badges || {};
    const newPop = impact.new_population_covered;
    const newLocs = impact.new_localities_covered;
    const impactSentence = (newPop != null && newLocs != null)
      ? `+${fmt(newPop)} bénéficiaires projetés dans ${fmt(newLocs)} localités après mise en service`
      : (impact.nature_label || '');
    host.innerHTML = `
      <p class="dxl-kicker">Impact territorial et populationnel</p>
      <div class="tie-head">
        <h3>${escapeHtml(profile.name || 'Site')}</h3>
      </div>
      <div class="tie-badge-row" aria-label="Statuts séparés">
        <span class="tie-badge is-data">${escapeHtml(badges.data || 'Données intégrées')}</span>
        <span class="tie-badge">${escapeHtml(badges.program || dep.badge || 'Programme')}</span>
        <span class="tie-badge is-soft">${escapeHtml(badges.asset || 'Statut individuel à confirmer')}</span>
        <span class="tie-badge is-impact">${escapeHtml(badges.impact || 'Impact estimé')}</span>
      </div>
      <div class="dxl-kpi-strip">
        <article><span>Localités concernées</span><strong>${fmt((profile.localities || []).length)}</strong></article>
        <article><span>Population totale (rayon)</span><strong>${fmt(baseline.population_total)}</strong></article>
        <article><span>Déjà couverte</span><strong>${fmt(impact.population_already_covered)}</strong></article>
        <article><span>Bénéficiaires projetés</span><strong>${fmt(newPop)}</strong></article>
        <article><span>Localités nouvellement concernées</span><strong>${fmt(newLocs)}</strong></article>
        <article><span>Couverture avant</span><strong>${impact.coverage_rate_before_pct != null ? `${fmt(impact.coverage_rate_before_pct)} %` : '—'}</strong></article>
        <article><span>Couverture après (estim.)</span><strong>${impact.coverage_rate_after_pct != null ? `${fmt(impact.coverage_rate_after_pct)} %` : '—'}</strong></article>
        <article><span>Confiance</span><strong>${escapeHtml(profile.confidence || '—')}</strong></article>
      </div>
      <p class="dxl-note">${escapeHtml(impactSentence)}</p>
      <p class="dxl-note">${escapeHtml(impact.note || '')}</p>
      <p class="dxl-note"><strong>Nature :</strong> ${escapeHtml(impact.nature_label || impact.nature || '')}</p>
      <details class="tie-details">
        <summary>Voir le détail du calcul</summary>
        <pre class="tie-pre">${escapeHtml(JSON.stringify({
          lifecycle: profile.lifecycle || null,
          calculation: profile.explainability?.calculation_detail || profile.dedup || {},
        }, null, 2))}</pre>
        <p>${escapeHtml(profile.explainability?.answer || '')}</p>
        <ul>${(profile.limits || []).map((l) => `<li>${escapeHtml(l)}</li>`).join('')}</ul>
        <p><strong>Sources :</strong> ${(profile.sources || []).map((s) => escapeHtml(s)).join(' · ')}</p>
      </details>
      <h4>Localités concernées</h4>
      ${renderLocalitiesTable(profile.localities)}
    `;
    host.querySelectorAll('.tie-loc-row').forEach((tr) => {
      tr.addEventListener('click', () => {
        const idx = Number(tr.getAttribute('data-tie-loc'));
        const loc = (profile.localities || [])[idx];
        if (!loc) return;
        focusLocalityOnMap(loc);
        tr.classList.add('is-active');
        host.querySelectorAll('.tie-loc-row').forEach((other) => {
          if (other !== tr) other.classList.remove('is-active');
        });
      });
    });
    syncPresentationImpactKpis(profile);
  }

  function syncPresentationImpactKpis(profile) {
    global.__tieLastSiteProfile = profile || null;
    const strip = document.querySelector('#epm-kpi-strip');
    if (!strip || !profile) return;
    let slot = strip.querySelector('[data-epm-kpi="tie-impact"]');
    if (!slot) {
      slot = document.createElement('button');
      slot.type = 'button';
      slot.className = 'epm-kpi';
      slot.setAttribute('data-epm-kpi', 'tie-impact');
      strip.appendChild(slot);
    }
    const impact = profile.impact || {};
    const gain = impact.new_population_covered;
    slot.setAttribute('aria-label', 'Nouveaux bénéficiaires estimés');
    slot.title = 'Impact territorial — ouvrir la section Impact';
    slot.innerHTML = `
      <span class="epm-kpi-icon" aria-hidden="true">◎</span>
      <span class="epm-kpi-meta">
        <span class="epm-kpi-label">Nouveaux bénéficiaires</span>
        <strong class="epm-kpi-value">${escapeHtml(fmt(gain))}</strong>
      </span>`;
    slot.onclick = () => {
      const section = document.querySelector('#dxl-section-territorial-impact');
      if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        section.classList.add('tie-pulse');
        global.setTimeout(() => section.classList.remove('tie-pulse'), 1600);
      }
      const narrative = document.querySelector('#epm-narrative');
      if (narrative) {
        narrative.textContent = [
          `Impact territorial — ${profile.name || 'site'}`,
          `Localités : ${(profile.localities || []).length}`,
          `Nouveaux bénéficiaires estimés : ${fmt(gain)}`,
          `Couverture avant : ${impact.coverage_rate_before_pct != null ? `${impact.coverage_rate_before_pct} %` : '—'}`,
          `Après (estim.) : ${impact.coverage_rate_after_pct != null ? `${impact.coverage_rate_after_pct} %` : '—'}`,
          impact.note || '',
        ].filter(Boolean).join(' · ');
      }
    };
  }

  function focusLocalityOnMap(loc) {
    const leafletMap = global.DxlCore?.state?.map;
    if (!leafletMap || loc.latitude == null || loc.longitude == null || !global.L) return;
    const latlng = [Number(loc.latitude), Number(loc.longitude)];
    leafletMap.setView(latlng, Math.max(leafletMap.getZoom(), 11));
    if (global.__tieFocusMarker) {
      try { leafletMap.removeLayer(global.__tieFocusMarker); } catch (_e) { /* */ }
    }
    global.__tieFocusMarker = global.L.circleMarker(latlng, {
      radius: 10,
      color: '#f59e0b',
      fillColor: '#fbbf24',
      fillOpacity: 0.9,
      weight: 2,
    }).bindPopup(`<strong>${escapeHtml(loc.name || '')}</strong><br/>Pop. ${fmt(loc.population)} · ${escapeHtml(loc.state || '')}`).addTo(leafletMap);
    global.__tieFocusMarker.openPopup();
  }

  function mountSiteImpact(assetId, programCode) {
    const host = ensureSection();
    host.innerHTML = '<p class="dxl-note">Chargement de l’impact territorial…</p>';
    const qs = programCode ? `?program_code=${encodeURIComponent(programCode)}` : '';
    return fetchJson(`/api/territorial-impact/sites/${encodeURIComponent(assetId)}${qs}`)
      .then((profile) => {
        renderSiteProfile(host, profile);
        return profile;
      })
      .catch(() => {
        host.innerHTML = '<p class="dxl-note">Impact territorial indisponible pour ce site (sources ou coordonnées manquantes).</p>';
        return null;
      });
  }

  function ensurePilotageSection() {
    let host = document.querySelector('#esr-coverage-progression');
    if (host) return host;
    const root = document.querySelector('.esr-root .esr-col-main') || document.querySelector('.esr-root');
    if (!root) return null;
    host = document.createElement('section');
    host.id = 'esr-coverage-progression';
    host.className = 'esr-card tie-pilotage';
    host.innerHTML = '<header class="esr-card-header"><h3>Progression de la couverture du Service Universel</h3></header><div id="esr-coverage-body" class="tie-pilotage-body">Chargement…</div>';
    const priorities = document.querySelector('#esr-priorities-host');
    if (priorities && priorities.parentNode) {
      priorities.parentNode.insertBefore(host, priorities.nextSibling);
    } else {
      root.appendChild(host);
    }
    return host;
  }

  function mountPilotageCoverage(options = {}) {
    const host = ensurePilotageSection();
    if (!host) return Promise.resolve(null);
    const body = host.querySelector('#esr-coverage-body') || host;
    const programs = options.programs || 'sites_40,sites_300';
    const mode = options.mode || 'planned';
    const limit = options.limit || 15;
    body.innerHTML = '<p class="esr-muted">Calcul de la progression…</p>';
    const params = new URLSearchParams({
      programs,
      mode,
      limit_per_program: String(limit),
      include_ccn: 'true',
    });
    if (options.province) params.set('province', options.province);
    if (options.territoire) params.set('territoire', options.territoire);
    return fetchJson(`/api/territorial-impact/scenario?${params}`)
      .then((payload) => {
        const charts = payload.charts || {};
        const summary = payload.summary || {};
        const baseline = payload.baseline || {};
        body.innerHTML = `
          <div class="tie-filters">
            <label>Mode
              <select id="tie-mode">
                <option value="planned"${mode === 'planned' ? ' selected' : ''}>Planifié</option>
                <option value="simulation"${mode === 'simulation' ? ' selected' : ''}>Simulation</option>
              </select>
            </label>
            <label>Programmes
              <select id="tie-programs">
                <option value="sites_40">Sites 40</option>
                <option value="sites_40,sites_300" selected>Sites 40 + 300</option>
                <option value="sites_40,sites_300,sites_20476">40 + 300 + 20 476</option>
              </select>
            </label>
            <button type="button" class="secondary-button" id="tie-refresh">Actualiser</button>
          </div>
          <div class="dxl-kpi-strip">
            <article><span>Pop. déjà couverte (baseline)</span><strong>${fmt(baseline.population_covered)}</strong></article>
            <article><span>Nouveaux bénéficiaires (cumul)</span><strong>${fmt(summary.cumulative_new_population)}</strong></article>
            <article><span>Localités ajoutées</span><strong>${fmt(summary.cumulative_new_localities)}</strong></article>
            <article><span>Restant à couvrir</span><strong>${fmt(summary.remaining_uncovered)}</strong></article>
            <article><span>Déploiements</span><strong>${fmt(summary.deployments_count)}</strong></article>
          </div>
          <h4>Courbe cumulative</h4>
          ${cumulativeSvg(charts.cumulative_curve, mode)}
          <p class="dxl-note">Cette courbe représente une couverture <strong>projetée</strong> (sites non mis en service) — pas une couverture réellement observée.</p>
          <h4>Contribution par déploiement</h4>
          <p class="dxl-note">Les barres CCN (violet) sont des bénéficiaires potentiels — non additionnées à la couverture radio.</p>
          ${barsSvg(charts.contribution_bars)}
          <h4>Composition couvert / nouveau / restant</h4>
          ${composeBlocks(charts.coverage_composition)}
          <h4>Évolution des localités (≠ population)</h4>
          ${localitiesProgressionBlock(charts.localities_progression)}
          <h4>Par programme</h4>
          <ul class="tie-prog-list">${(charts.by_program || []).map((p) => `
            <li><strong>${escapeHtml(p.phase || p.program)}</strong> —
              ${fmt(p.sites_or_ccn)} actifs ·
              +${fmt(p.new_population_covered)} hab. réseau ·
              ${p.beneficiaries_potential_ccn ? `CCN pot. ${fmt(p.beneficiaries_potential_ccn)} · ` : ''}
              ${fmt(p.new_localities_covered)} localités</li>`).join('')}</ul>
          <details class="tie-details">
            <summary>Qualité et limites</summary>
            <ul>${(payload.data_quality?.limits || []).map((l) => `<li>${escapeHtml(l)}</li>`).join('')}</ul>
            <p>Dernier calcul : ${escapeHtml(payload._meta?.last_calculation || '')}</p>
          </details>
        `;
        body.querySelector('#tie-refresh')?.addEventListener('click', () => {
          mountPilotageCoverage({
            mode: body.querySelector('#tie-mode')?.value || 'planned',
            programs: body.querySelector('#tie-programs')?.value || programs,
            limit,
            province: options.province,
            territoire: options.territoire,
          });
        });
        return payload;
      })
      .catch(() => {
        body.innerHTML = '<p class="esr-muted">Progression de couverture indisponible.</p>';
        return null;
      });
  }

  function mountProgramLifecycleBoard() {
    let host = document.querySelector('#esr-program-lifecycle');
    if (!host) {
      const root = document.querySelector('.esr-root .esr-col-main') || document.querySelector('.esr-root');
      if (!root) return Promise.resolve(null);
      host = document.createElement('section');
      host.id = 'esr-program-lifecycle';
      host.className = 'esr-card tie-pilotage';
      host.innerHTML = '<header class="esr-card-header"><h3>Suivi des programmes — cycle de vie</h3></header><div id="esr-program-lifecycle-body" class="tie-pilotage-body">Chargement…</div>';
      const coverage = document.querySelector('#esr-coverage-progression');
      if (coverage && coverage.parentNode) coverage.parentNode.insertBefore(host, coverage);
      else root.appendChild(host);
    }
    const body = host.querySelector('#esr-program-lifecycle-body') || host;
    return fetchJson('/api/program-lifecycle/programs')
      .then((payload) => {
        const rows = payload.programs || [];
        body.innerHTML = `
          <div class="tie-table-wrap">
            <table class="tie-table">
              <thead><tr>
                <th>Programme</th><th>Phase</th><th>Statut</th><th>Données</th>
                <th>Total</th><th>En cours</th><th>Installés</th><th>Mis en service</th><th>Opérationnels</th>
              </tr></thead>
              <tbody>
                ${rows.map((r) => `
                  <tr>
                    <td>${escapeHtml(r.program)}</td>
                    <td>${escapeHtml(r.phase || '—')}</td>
                    <td>${escapeHtml(r.status || '—')}</td>
                    <td>${escapeHtml(r.data_status || '—')}</td>
                    <td>${fmt(r.total)}</td>
                    <td>${escapeHtml(String(r.display?.in_progress ?? 'À consolider'))}</td>
                    <td>${escapeHtml(String(r.display?.installed ?? 'À consolider'))}</td>
                    <td>${escapeHtml(String(r.display?.commissioned ?? 'À consolider'))}</td>
                    <td>${escapeHtml(String(r.display?.operational ?? 'À consolider'))}</td>
                  </tr>`).join('')}
              </tbody>
            </table>
          </div>
          <p class="dxl-note">${escapeHtml((payload.limits || [])[0] || '')}</p>`;
        return payload;
      })
      .catch(() => {
        body.innerHTML = '<p class="esr-muted">Cycle de vie programmes indisponible.</p>';
        return null;
      });
  }

  function mountSdgMaturityCard() {
    let host = document.querySelector('#esr-sdg-maturity');
    if (!host) {
      const root = document.querySelector('.esr-root .esr-col-main') || document.querySelector('.esr-root');
      if (!root) return Promise.resolve(null);
      host = document.createElement('section');
      host.id = 'esr-sdg-maturity';
      host.className = 'esr-card tie-pilotage';
      host.innerHTML = '<header class="esr-card-header"><h3>Maturité analytique du SIG</h3></header><div id="esr-sdg-maturity-body" class="tie-pilotage-body">Chargement…</div>';
      const lifecycle = document.querySelector('#esr-program-lifecycle');
      if (lifecycle && lifecycle.parentNode) lifecycle.parentNode.insertBefore(host, lifecycle);
      else root.prepend(host);
    }
    const body = host.querySelector('#esr-sdg-maturity-body') || host;
    return fetchJson('/api/sdg/coverage?deep_sample=0&include_ccn=true')
      .then((payload) => {
        const matrix = payload.matrix || [];
        body.innerHTML = `
          <div class="dxl-kpi-strip">
            <article><span>SDG complet (NSME)</span><strong>${fmt(payload.complete)}</strong></article>
            <article><span>SDG partiel</span><strong>${fmt(payload.partial)}</strong></article>
            <article><span>À charger en NSME</span><strong>${fmt(payload.pending_nsme_load)}</strong></article>
            <article><span>Taux NSME natif</span><strong>${fmt(payload.nsme_native_rate)} %</strong></article>
          </div>
          <div class="tie-table-wrap">
            <table class="tie-table">
              <thead><tr><th>Programme</th><th>Total</th><th>Complet</th><th>Partiel</th><th>Impossible</th><th>%</th></tr></thead>
              <tbody>
                ${matrix.map((r) => `
                  <tr>
                    <td>${escapeHtml(r.program)}</td>
                    <td>${fmt(r.total)}</td>
                    <td>${fmt(r.complete)}</td>
                    <td>${fmt(r.partial)}</td>
                    <td>${fmt(r.impossible)}</td>
                    <td>${fmt(r.pct)}</td>
                  </tr>`).join('')}
              </tbody>
            </table>
          </div>
          <p class="dxl-note">${escapeHtml((payload.recommendations || [])[0] || '')}</p>
          <p class="dxl-note">Calcul : ${escapeHtml(payload._meta?.generated_at || '')}</p>`;
        return payload;
      })
      .catch(() => {
        body.innerHTML = '<p class="esr-muted">Maturité analytique indisponible.</p>';
        return null;
      });
  }

  global.TerritorialImpactUI = {
    mountSiteImpact,
    mountPilotageCoverage,
    mountProgramLifecycleBoard,
    mountSdgMaturityCard,
    ensureSection,
    syncPresentationImpactKpis,
  };
})(window);
