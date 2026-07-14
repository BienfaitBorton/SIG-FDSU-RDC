/**
 * Analyse détaillée — vue dédiée #decision-detail/<kpi_code>
 */
(function initDecisionDetailWorkspace(global) {
  const API_BASE = `${global.location.protocol}//${global.location.hostname}:8001`;
  const PAGE_SIZE = 50;

  const SLUG_ALIASES = {
    'sites-total': 'sites_fdsu',
    'sites-fdsu': 'sites_fdsu',
    'sites-prioritaires': 'sites_priority',
    'sites-priority': 'sites_priority',
    'sites-critiques': 'sites_critical',
    'sites-critical': 'sites_critical',
    'sites-priorite-elevee': 'sites_high',
    'sites-high': 'sites_high',
    'referentiels-actifs': 'referentials_active',
    'referentiels-planifies': 'referentials_planned',
    'sites-40': 'sites_40',
    'sites-300': 'sites_300',
    'sites-scores': 'sites_scored',
    'sante': 'health_facilities',
    'telecom': 'telecom_objects',
    'provinces': 'provinces',
    'territoires': 'territoires',
    'population-couverte': 'population_covered',
    'population-non-couverte': 'population_uncovered',
    'ccn-planifies': 'planned_ccn',
    'investissement-estime': 'estimated_investment',
    'referentiels-en-cours': 'referentials_in_progress',
  };

  const ROUTE_SLUGS = {
    sites_fdsu: 'sites-total',
    sites_priority: 'sites-prioritaires',
    sites_critical: 'sites-critiques',
    sites_high: 'sites-priorite-elevee',
    referentials_active: 'referentiels-actifs',
    referentials_planned: 'referentiels-planifies',
    sites_40: 'sites-40',
    sites_300: 'sites-300',
    sites_scored: 'sites-scores',
    health_facilities: 'sante',
    telecom_objects: 'telecom',
    provinces: 'provinces',
    territoires: 'territoires',
    population_covered: 'population-couverte',
    population_uncovered: 'population-non-couverte',
    planned_ccn: 'ccn-planifies',
    estimated_investment: 'investissement-estime',
    referentials_in_progress: 'referentiels-en-cours',
  };

  const state = {
    initialized: false,
    kpiCode: null,
    payload: null,
    offset: 0,
    map: null,
    layer: null,
    loading: false,
  };

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatNumber(value) {
    if (value == null || value === '') return '—';
    const n = Number(value);
    if (Number.isNaN(n)) return String(value);
    return new Intl.NumberFormat('fr-FR').format(n);
  }

  function resolveKpiCode(raw) {
    if (!raw) return null;
    const key = String(raw).trim();
    if (SLUG_ALIASES[key]) return SLUG_ALIASES[key];
    if (key.includes('_')) return key;
    return SLUG_ALIASES[key.replace(/_/g, '-')] || key.replace(/-/g, '_');
  }

  function getKpiFromHash() {
    const hash = (global.location.hash || '').replace(/^#/, '').split('?')[0];
    // Alias Decision Workspace v1.1 — même contrat que decision-detail
    if (!hash.startsWith('decision-detail') && !hash.startsWith('decision-workspace')) return null;
    const parts = hash.split('/');
    return resolveKpiCode(parts[1] || '');
  }

  function setStatus(text, isError) {
    const el = document.querySelector('#decision-detail-status');
    if (!el) return;
    el.textContent = text;
    el.classList.toggle('is-error', Boolean(isError));
  }

  function buildQuery() {
    const params = new URLSearchParams();
    const q = document.querySelector('#decision-detail-q')?.value?.trim();
    const province = document.querySelector('#decision-detail-province')?.value?.trim();
    const territoire = document.querySelector('#decision-detail-territoire')?.value?.trim();
    const programme = document.querySelector('#decision-detail-programme')?.value?.trim();
    const priority = document.querySelector('#decision-detail-priority')?.value?.trim();
    if (q) params.set('q', q);
    if (province) params.set('province', province);
    if (territoire) params.set('territoire', territoire);
    if (programme) params.set('programme', programme);
    if (priority) params.set('priority_level', priority);
    params.set('limit', String(PAGE_SIZE));
    params.set('offset', String(state.offset));
    return params;
  }

  async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || `HTTP ${response.status}`);
    }
    return response.json();
  }

  function renderHeader(header) {
    const host = document.querySelector('#decision-detail-header');
    const title = document.querySelector('#decision-detail-title');
    if (title) title.textContent = header?.title || 'Détail indicateur';
    if (!host || !header) return;
    if (header.pending) {
      host.innerHTML = `
        <div class="decision-detail-header-main">
          <p class="summary-label">${escapeHtml(header.title)}</p>
          <p class="summary-value is-pending-value">Donnée non encore calculée</p>
          <p>${escapeHtml(header.definition || '')}</p>
        </div>
        <dl class="decision-detail-meta">
          <div><dt>Source</dt><dd>${escapeHtml(header.source || '—')}</dd></div>
          <div><dt>Confiance</dt><dd>${escapeHtml(header.confidence || 'low')}</dd></div>
          <div><dt>Objectif</dt><dd>${escapeHtml(header.objective || '—')}</dd></div>
        </dl>
      `;
      return;
    }
    host.innerHTML = `
      <div class="decision-detail-header-main">
        <p class="summary-label">${escapeHtml(header.title)}</p>
        <p class="summary-value">${escapeHtml(formatNumber(header.value))}</p>
        <p>${escapeHtml(header.definition || header.description || '')}</p>
      </div>
      <dl class="decision-detail-meta">
        <div><dt>Source</dt><dd>${escapeHtml(header.source || '—')}</dd></div>
        <div><dt>Mise à jour</dt><dd>${escapeHtml(String(header.last_updated || '').slice(0, 19).replace('T', ' '))}</dd></div>
        <div><dt>Confiance</dt><dd>${escapeHtml(header.confidence || '—')}</dd></div>
        <div><dt>Tendance</dt><dd>${escapeHtml(header.trend || 'stable')}</dd></div>
        <div><dt>Objectif</dt><dd>${escapeHtml(header.objective || '—')}</dd></div>
      </dl>
    `;
  }

  function renderSecondary(items) {
    const host = document.querySelector('#decision-detail-secondary');
    if (!host) return;
    if (!items?.length) {
      host.innerHTML = '';
      return;
    }
    host.innerHTML = items.map((kpi) => `
      <article class="decision-detail-secondary-card">
        <p class="summary-label">${escapeHtml(kpi.label)}</p>
        <p class="summary-value">${escapeHtml(formatNumber(kpi.value))}</p>
      </article>
    `).join('');
  }

  function renderCharts(charts) {
    const host = document.querySelector('#decision-detail-charts-body');
    if (!host) return;
    const blocks = Object.entries(charts || {});
    if (!blocks.length) {
      host.innerHTML = '<p class="decision-detail-empty">Aucun graphique pour ce KPI.</p>';
      return;
    }
    host.innerHTML = blocks.map(([key, chart]) => {
      const rows = (chart.items || []).slice(0, 8);
      const max = Math.max(...rows.map((r) => Number(r.value) || 0), 1);
      return `
        <div class="decision-detail-chart" data-chart="${escapeHtml(key)}">
          <h4>${escapeHtml(chart.title || key)}</h4>
          <ul class="decision-detail-barlist">
            ${rows.map((row) => `
              <li>
                <span>${escapeHtml(row.label)}</span>
                <div class="decision-detail-bartrack">
                  <div class="decision-detail-barfill" style="width:${Math.round((Number(row.value) || 0) / max * 100)}%;background:var(--edvs-${row.color || 'blue'}, #2563eb)"></div>
                </div>
                <strong>${escapeHtml(formatNumber(row.value))}</strong>
              </li>
            `).join('')}
          </ul>
        </div>
      `;
    }).join('');
  }

  function renderExplain(explain) {
    const host = document.querySelector('#decision-detail-explain-body');
    if (!host) return;
    if (!explain) {
      host.innerHTML = '<p>Justification indisponible.</p>';
      return;
    }
    const criteria = (explain.criteria || []).map((c) => `
      <li>${escapeHtml(c.label || c.id)} — ${escapeHtml(c.weight_percent != null ? `${c.weight_percent}%` : '')}</li>
    `).join('');
    host.innerHTML = `
      <p><strong>Pourquoi :</strong> ${escapeHtml(explain.why || '—')}</p>
      <p><strong>Doctrine :</strong> ${escapeHtml(explain.doctrine?.id || '—')} v${escapeHtml(explain.doctrine?.version || '—')}</p>
      <p><strong>Matrice :</strong> ${escapeHtml(explain.matrix?.ref || '—')}</p>
      <p><strong>Confiance :</strong> ${escapeHtml(explain.confidence || '—')}</p>
      <p><strong>Action recommandée :</strong> ${escapeHtml(explain.recommended_action || '—')}</p>
      ${criteria ? `<ul>${criteria}</ul>` : ''}
      ${(explain.missing_data || []).length ? `<p><strong>Données manquantes :</strong> ${escapeHtml(explain.missing_data.join(', '))}</p>` : ''}
    `;
  }

  function renderActions(actions) {
    const host = document.querySelector('#decision-detail-actions');
    if (!host) return;
    const caps = global.CapabilityRegistry;
    const filtered = (actions || []).filter((action) => {
      if (action.id === 'prepare_mission') return caps?.isEnabled?.('mission_planning');
      if (action.id === 'simulate_investment') return caps?.isEnabled?.('simulation');
      return true;
    });
    if (!filtered.length) {
      host.innerHTML = '';
      return;
    }
    host.innerHTML = filtered.map((action) => `
      <button type="button" class="secondary-button" data-detail-action="${escapeHtml(action.id)}">${escapeHtml(action.label)}</button>
    `).join('');
  }

  function renderTable(payload) {
    const head = document.querySelector('#decision-detail-table-head');
    const body = document.querySelector('#decision-detail-table-body');
    const count = document.querySelector('#decision-detail-list-count');
    const pageLabel = document.querySelector('#decision-detail-page-label');
    const columns = payload?.config?.list_columns || [];
    const items = payload?.items || {};
    const rows = items.rows || [];
    if (count) count.textContent = `${formatNumber(items.total || 0)} élément(s)`;
    if (pageLabel) {
      const page = Math.floor((items.offset || 0) / PAGE_SIZE) + 1;
      pageLabel.textContent = `Page ${page}`;
    }
    if (!head || !body) return;
    if (!columns.length) {
      head.innerHTML = '';
      body.innerHTML = global.UxPremium?.tableEmptyRow
        ? global.UxPremium.tableEmptyRow(1, 'Aucune colonne configurée', 'Ce KPI n’a pas encore de colonnes de liste.')
        : '<tr><td class="decision-detail-empty">Aucune colonne configurée pour ce KPI.</td></tr>';
      return;
    }
    head.innerHTML = `<tr>${columns.map((c) => `<th>${escapeHtml(c)}</th>`).join('')}<th></th></tr>`;
    if (!rows.length) {
      body.innerHTML = global.UxPremium?.tableEmptyRow
        ? global.UxPremium.tableEmptyRow(columns.length + 1, 'Aucun élément pour ce filtre', 'Élargissez la province, le territoire ou la priorité.')
        : `<tr><td colspan="${columns.length + 1}" class="decision-detail-empty">Aucun élément pour ce filtre.</td></tr>`;
      return;
    }
    body.innerHTML = rows.map((row) => {
      const cells = columns.map((c) => `<td>${escapeHtml(row[c] ?? '—')}</td>`).join('');
      const id = row.site_id || row.id || row.code || '';
      return `<tr>${cells}<td><button type="button" class="table-action-button" data-open-item="${escapeHtml(id)}" data-program="${escapeHtml(row.program_code || '')}">Fiche</button></td></tr>`;
    }).join('');
  }

  function attachResilientBasemap(map) {
    if (!map || !global.L) return null;
    if (typeof global.SigBasemapManager === 'function') {
      const manager = new global.SigBasemapManager({ timeoutMs: 3000, retries: 1 });
      manager.attach(map);
      return manager;
    }
    return global.L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      maxZoom: 20,
      subdomains: 'abcd',
    }).addTo(map);
  }

  function ensureMap() {
    const host = document.querySelector('#decision-detail-map');
    if (!host || !global.L) return null;
    if (state.map) {
      state.map.invalidateSize();
      return state.map;
    }
    state.map = global.L.map(host, { zoomControl: true }).setView([-2.8, 23.5], 5);
    attachResilientBasemap(state.map);
    state.layer = global.L.layerGroup().addTo(state.map);
    return state.map;
  }

  async function renderMap(kpiCode) {
    const map = ensureMap();
    if (!map || !state.layer) return;
    state.layer.clearLayers();
    const params = buildQuery();
    params.delete('limit');
    params.delete('offset');
    try {
      const geo = await fetchJson(`${API_BASE}/api/decision/details/${encodeURIComponent(kpiCode)}/map?${params}`);
      const legend = document.querySelector('#decision-detail-legend');
      if (legend) {
        legend.textContent = `${geo.features?.length || 0} objet(s) cartographiés — recentrage national disponible`;
      }
      const colorFor = (level) => ({
        critical: '#dc2626',
        high: '#ea580c',
        medium: '#ca8a04',
        low: '#16a34a',
      }[level] || '#2563eb');
      (geo.features || []).forEach((feature) => {
        const [lon, lat] = feature.geometry.coordinates;
        const props = feature.properties || {};
        const marker = global.L.circleMarker([lat, lon], {
          radius: 5,
          color: colorFor(props.priority_level),
          fillColor: colorFor(props.priority_level),
          fillOpacity: 0.75,
          weight: 1,
        });
        const kind = props.kind === 'ccn'
          ? 'ccn'
          : (props.kind === 'uncovered_locality' || props.coverage_status === 'uncovered')
            ? 'uncovered_locality'
            : (props.kind === 'health' ? 'health' : 'site_fdsu');
        if (global.SigMapTooltips?.bind) {
          global.SigMapTooltips.bind(marker, props, kind, {
            onClick: () => {
              if (global.DecisionWorkspace?.bindMapFeatureSelection) {
                global.DecisionWorkspace.bindMapFeatureSelection(props);
              }
              const id = props.id || props.site_id || props.code;
              if (id && typeof global.openDecisionCase === 'function') {
                global.openDecisionCase('site', id, props.program_code);
              } else if (id) {
                global.location.hash = `decision-case/site/${encodeURIComponent(id)}`;
              }
            },
          });
        } else {
          marker.bindTooltip(
            `<strong>${escapeHtml(props.name || '—')}</strong><br>${escapeHtml(props.province || '')} / ${escapeHtml(props.territoire || '')}`,
            { direction: 'top', opacity: 1, className: 'sig-map-tooltip' },
          );
        }
        marker.bindPopup(`<strong>${escapeHtml(props.name || '—')}</strong><br>${escapeHtml(props.province || '')} / ${escapeHtml(props.territoire || '')}<br>${escapeHtml(props.priority_level || '')}`);
        state.layer.addLayer(marker);
      });
      if (state.layer.getLayers().length) {
        map.fitBounds(state.layer.getBounds().pad(0.15));
      } else {
        map.setView([-2.8, 23.5], 5);
      }
    } catch (err) {
      const legend = document.querySelector('#decision-detail-legend');
      if (legend) legend.textContent = `Carte indisponible : ${err.message}`;
    }
  }

  function setLoading(isLoading) {
    const root = document.querySelector('#decision-detail-panel');
    const overlay = document.querySelector('#decision-detail-loading-overlay');
    state.loading = Boolean(isLoading);
    if (root) {
      root.classList.toggle('is-loading', state.loading);
      root.style.opacity = '1';
      root.style.filter = 'none';
      root.style.pointerEvents = 'auto';
      root.style.background = 'transparent';
    }
    // Overlay conservé dans le DOM pour compatibilité tests, jamais affiché
    if (overlay) {
      overlay.setAttribute('aria-hidden', 'true');
      overlay.hidden = true;
      overlay.style.display = 'none';
      overlay.style.pointerEvents = 'none';
      overlay.style.opacity = '0';
      overlay.style.background = 'transparent';
    }
  }

  function clearResidualOverlays() {
    // Fermer drawer KPI legacy s'il était ouvert
    const drawer = document.querySelector('#decision-kpi-detail-drawer');
    if (drawer) {
      drawer.hidden = true;
      drawer.setAttribute('hidden', '');
      drawer.style.display = 'none';
    }
    document.querySelectorAll('.kpi-detail-btn.is-loading').forEach((btn) => {
      btn.classList.remove('is-loading');
    });
    // Sortir du mode présentation EDVS s'il masque l'UI
    if (document.body.classList.contains('edvs-presentation-mode')) {
      document.body.classList.remove('edvs-presentation-mode');
      const bar = document.querySelector('#edvs-presentation-bar');
      if (bar) {
        bar.hidden = true;
        bar.setAttribute('hidden', '');
      }
    }
    document.body.classList.add('decision-detail-open');
    document.body.style.filter = 'none';
    document.body.style.opacity = '1';
    const root = document.querySelector('#decision-detail-panel');
    if (root) {
      root.style.opacity = '1';
      root.style.filter = 'none';
      root.style.pointerEvents = 'auto';
      root.style.background = 'transparent';
      root.classList.remove('is-loading');
    }
    const overlay = document.querySelector('#decision-detail-loading-overlay');
    if (overlay) {
      overlay.setAttribute('aria-hidden', 'true');
      overlay.hidden = true;
      overlay.style.display = 'none';
      overlay.style.opacity = '0';
      overlay.style.pointerEvents = 'none';
      overlay.style.background = 'transparent';
    }
  }

  function leaveDetailWorkspace() {
    document.body.classList.remove('decision-detail-open');
    if (global.DecisionWorkspace?.detach) global.DecisionWorkspace.detach();
    setLoading(false);
  }

  async function loadDetail(kpiCode) {
    state.kpiCode = kpiCode;
    clearResidualOverlays();
    setLoading(true);
    setStatus('Chargement…');
    const header = document.querySelector('#decision-detail-header');
    if (header) header.innerHTML = '<p class="decision-center-program-loading">Chargement du détail…</p>';
    try {
      const params = buildQuery();
      const payload = await fetchJson(`${API_BASE}/api/decision/details/${encodeURIComponent(kpiCode)}?${params}`);
      state.payload = payload;
      renderHeader(payload.header);
      renderSecondary(payload.secondary_kpis);
      renderCharts(payload.charts);
      renderTable(payload);
      renderExplain(payload.explain);
      renderActions(payload.actions);
      await renderMap(kpiCode);
      if (global.DecisionWorkspace?.syncFromDetailPayload) {
        global.DecisionWorkspace.syncFromDetailPayload(payload, kpiCode);
      }
      setStatus(`${payload.header?.title || kpiCode} — prêt`);
    } catch (err) {
      setStatus(`Erreur : ${err.message}`, true);
      if (header) {
        header.innerHTML = `<p class="decision-detail-empty is-error">Impossible de charger le détail : ${escapeHtml(err.message)}</p>`;
      }
    } finally {
      setLoading(false);
      global.requestAnimationFrame(() => {
        state.map?.invalidateSize();
        clearResidualOverlays();
        setLoading(false);
      });
    }
  }

  async function runAction(actionId) {
    const kpi = state.kpiCode;
    if (!kpi) return;
    if (actionId === 'export_excel' || actionId === 'export_geojson') {
      const format = actionId === 'export_geojson' ? 'geojson' : 'csv';
      const params = buildQuery();
      params.set('format', format);
      params.delete('limit');
      params.delete('offset');
      const data = await fetchJson(`${API_BASE}/api/decision/details/${encodeURIComponent(kpi)}/export?${params}`);
      if (format === 'geojson') {
        const blob = new Blob([JSON.stringify(data.payload, null, 2)], { type: 'application/geo+json' });
        downloadBlob(blob, data.filename || `${kpi}.geojson`);
      } else {
        const blob = new Blob([data.content || ''], { type: 'text/csv;charset=utf-8' });
        downloadBlob(blob, data.filename || `${kpi}.csv`);
      }
      return;
    }
    if (actionId === 'open_cartography') {
      global.location.hash = 'map';
      return;
    }
    if (actionId === 'open_nsme_map' || actionId === 'view_matched_needs') {
      global.location.hash = 'map';
      global.setTimeout(() => {
        const checkbox = document.querySelector('input[data-layer="asset_need_matches"]');
        if (checkbox && !checkbox.checked) {
          checkbox.checked = true;
          checkbox.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }, 400);
      return;
    }
    if (actionId === 'explain_match') {
      const firstId = state.payload?.items?.rows?.[0]?.id || state.payload?.items?.rows?.[0]?.site_id;
      if (!firstId) {
        setStatus('Aucun actif disponible pour l’explication spatiale');
        return;
      }
      fetchJson(`${API_BASE}/api/spatial-matching/assets/${encodeURIComponent(firstId)}/explain`)
        .then((payload) => {
          const host = document.querySelector('#decision-detail-explain-body');
          if (host) {
            host.innerHTML = `
              <p><strong>Correspondance spatiale</strong></p>
              <p>${escapeHtml(payload.summary || '—')}</p>
              <p>Distance : ${escapeHtml(payload.distance_m ?? '—')} m · Rayon : ${escapeHtml(payload.service_radius_m ?? '—')} m</p>
              <p>Règle : ${escapeHtml(payload.spatial_rule || '—')} · Confiance : ${escapeHtml(payload.confidence_level || '—')}</p>
            `;
          }
          document.querySelector('#decision-detail-explain')?.scrollIntoView({ behavior: 'smooth' });
          setStatus('Explication NSME chargée');
        })
        .catch((err) => setStatus(`Explication NSME indisponible : ${err.message}`, true));
      return;
    }
    if (actionId === 'view_population_impact') {
      const firstId = state.payload?.items?.rows?.[0]?.id || state.payload?.items?.rows?.[0]?.site_id;
      if (!firstId) {
        setStatus('Aucun actif pour l’impact populationnel');
        return;
      }
      fetchJson(`${API_BASE}/api/spatial-matching/assets/${encodeURIComponent(firstId)}/impact`)
        .then((payload) => {
          const impact = payload.impact || {};
          setStatus(
            `Impact : ${impact.localities_impacted ?? 0} localités · population ${impact.population_impacted ?? 'n/d'} (${impact.population_status || ''})`,
          );
        })
        .catch((err) => setStatus(`Impact NSME indisponible : ${err.message}`, true));
      return;
    }
    if (actionId === 'open_ti') {
      const sel = state.payload?.items?.rows?.find((row) => String(row.site_id || row.id) === String(state.selectionId))
        || state.payload?.items?.rows?.[0];
      const tid = sel?.territoire || sel?.territory_id || sel?.territory_name;
      if (!tid) {
        setStatus('Rattachement territorial absent pour l’analyse territoriale.');
        return;
      }
      global.location.hash = `territorial-intelligence/${encodeURIComponent(tid)}`;
      return;
    }
    if (actionId === 'explain') {
      document.querySelector('#decision-detail-explain')?.scrollIntoView({ behavior: 'smooth' });
      return;
    }
    if (actionId === 'prepare_mission') {
      // Capacité absente — ne doit plus apparaître actif
      setStatus(global.CapabilityRegistry?.reason?.('mission_planning') || 'Préparation de mission non encore disponible');
      return;
    }
    if (actionId === 'simulate_investment') {
      setStatus(global.CapabilityRegistry?.reason?.('simulation') || 'Simulation non encore branchée');
    }
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  function bindEvents() {
    const root = document.querySelector('#decision-detail-panel');
    if (!root || root.dataset.bound === 'true') return;
    root.dataset.bound = 'true';

    document.querySelector('#decision-detail-back-btn')?.addEventListener('click', () => {
      leaveDetailWorkspace();
      global.location.hash = 'decision-view';
    });

    document.querySelector('#decision-detail-apply-filters')?.addEventListener('click', () => {
      state.offset = 0;
      if (state.kpiCode) loadDetail(state.kpiCode);
    });

    document.querySelector('#decision-detail-prev')?.addEventListener('click', () => {
      state.offset = Math.max(0, state.offset - PAGE_SIZE);
      if (state.kpiCode) loadDetail(state.kpiCode);
    });

    document.querySelector('#decision-detail-next')?.addEventListener('click', () => {
      const total = state.payload?.items?.total || 0;
      if (state.offset + PAGE_SIZE < total) {
        state.offset += PAGE_SIZE;
        if (state.kpiCode) loadDetail(state.kpiCode);
      }
    });

    document.querySelector('#decision-detail-map-reset')?.addEventListener('click', () => {
      state.map?.setView([-2.8, 23.5], 5);
    });

    root.addEventListener('click', (event) => {
      const target = event.target;
      if (!(target instanceof global.HTMLElement)) return;
      const actionBtn = target.closest('[data-detail-action]');
      if (actionBtn) {
        runAction(actionBtn.getAttribute('data-detail-action'));
        return;
      }
      const openBtn = target.closest('[data-open-item]');
      if (openBtn) {
        const id = openBtn.getAttribute('data-open-item');
        const program = openBtn.getAttribute('data-program');
        if (id) {
          if (global.DecisionWorkspace?.selectEntity) {
            global.DecisionWorkspace.selectEntity({
              id,
              site_id: id,
              name: openBtn.closest('tr')?.querySelector('td')?.textContent?.trim() || `Site ${id}`,
              program_code: program || undefined,
            }, { applyFilters: false });
          }
          const programQs = program ? `?program_code=${encodeURIComponent(program)}` : '';
          if (typeof global.openDecisionCase === 'function') {
            global.openDecisionCase('site', id, program || undefined);
          } else {
            global.location.hash = `decision-case/site/${encodeURIComponent(id)}${programQs}`;
          }
        }
      }
    });

    global.document.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape') return;
      const panel = document.querySelector('#decision-detail-panel');
      if (panel && !panel.classList.contains('hidden')) {
        leaveDetailWorkspace();
        global.location.hash = 'decision-view';
      }
    });
  }

  function openDecisionDetail(kpiKey) {
    clearResidualOverlays();
    const code = resolveKpiCode(kpiKey);
    const slug = ROUTE_SLUGS[code] || String(kpiKey).replace(/_/g, '-');
    if (global.DecisionWorkspace?.attach) {
      global.DecisionWorkspace.attach({ kpiCode: code, returnHash: 'decision-view' });
    }
    global.location.hash = `decision-detail/${slug}`;
  }

  function initializeDecisionDetailModule() {
    bindEvents();
    state.initialized = true;
    clearResidualOverlays();
    if (global.DecisionWorkspace?.attach) {
      const ctx = global.DecisionWorkspace.restoreContextFromStorage?.();
      global.DecisionWorkspace.attach({
        kpiCode: getKpiFromHash() || ctx?.kpiKey,
        returnHash: ctx?.returnHash || 'decision-view',
        trail: ctx?.trail,
      });
      if (ctx?.selection) global.DecisionWorkspace.selectEntity(ctx.selection, { applyFilters: false });
    }
    const kpi = getKpiFromHash();
    if (kpi) {
      state.offset = 0;
      loadDetail(kpi);
    } else {
      setLoading(false);
      setStatus('Aucun KPI sélectionné', true);
    }
  }

  global.openDecisionDetail = openDecisionDetail;
  global.openDecisionWorkspace = function openDecisionWorkspace(context) {
    if (global.DecisionWorkspace?.open) {
      global.DecisionWorkspace.open(context || {});
      return;
    }
    if (context?.kpiKey || context?.kpiCode) openDecisionDetail(context.kpiKey || context.kpiCode);
  };
  global.initializeDecisionDetailModule = initializeDecisionDetailModule;
  global.decisionDetailState = state;
  global.resolveDecisionDetailKpi = resolveKpiCode;
})(window);
