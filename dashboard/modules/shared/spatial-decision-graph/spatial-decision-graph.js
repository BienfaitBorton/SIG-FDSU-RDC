/**
 * Spatial Decision Graph v2.0 — Analyse d’Impact Territorial
 * Réutilise la carte DXL (#dxl-map) — une instance Leaflet, mount/update/resize.
 */
(function initSpatialDecisionGraph(global) {
  const API_BASE = `${global.location.protocol}//${global.location.hostname}:8001`;

  const state = {
    graph: null,
    presentation: null,
    map: null,
    layer: null,
    edgeLayers: {},
    nodeLayers: {},
    filters: {},
    animTimer: null,
    animStep: -1,
    presenting: false,
    destroyed: false,
    chromeBound: false,
    navBound: false,
  };

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function fetchJson(path, signal) {
    return fetch(`${API_BASE}${path}`, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      signal,
    }).then((r) => {
      if (!r.ok) throw new Error(path);
      return r.json();
    });
  }

  function ensureShell() {
    const mapHost = document.querySelector('#dxl-map');
    if (!mapHost) return null;
    let shell = document.querySelector('#sdg-shell');
    if (!shell) {
      shell = document.createElement('div');
      shell.id = 'sdg-shell';
      shell.className = 'sdg-shell';
      shell.innerHTML = `
        <div class="sdg-toolbar" role="toolbar" aria-label="Analyse d’Impact Territorial">
          <button type="button" class="primary-button" id="sdg-present-btn">Présenter le raisonnement</button>
          <button type="button" class="secondary-button" id="sdg-stop-btn" hidden>Interrompre</button>
          <span class="sdg-step-label" id="sdg-step-label" aria-live="polite"></span>
        </div>
        <div class="sdg-layout">
          <aside class="sdg-side" aria-label="Pourquoi ce site ?">
            <h3>Pourquoi ce site ?</h3>
            <div id="sdg-why-body" class="sdg-why-body">Chargement…</div>
          </aside>
          <div class="sdg-map-wrap">
            <div id="sdg-legend" class="sdg-legend" aria-label="Légende intelligente"></div>
            <div id="sdg-filters" class="sdg-filters" aria-label="Filtres de relations"></div>
          </div>
        </div>
      `;
      const section = mapHost.closest('.dxl-section') || mapHost.parentElement;
      section?.appendChild(shell);
    }
    return shell;
  }

  function bindChrome() {
    if (state.chromeBound) return;
    state.chromeBound = true;
    document.querySelector('#sdg-present-btn')?.addEventListener('click', () => startPresentation());
    document.querySelector('#sdg-stop-btn')?.addEventListener('click', () => stopPresentation(true));
  }

  function bindNavDelegation() {
    if (state.navBound) return;
    state.navBound = true;
    document.addEventListener('click', (event) => {
      const btn = event.target?.closest?.('[data-sdg-nav]');
      if (!btn || !document.querySelector('#sdg-shell')) return;
      const hash = btn.getAttribute('data-sdg-nav');
      if (hash) global.location.hash = hash.replace(/^#/, '');
    });
  }

  function setMap(map) {
    state.map = map;
    if (!state.layer && map && global.L) {
      state.layer = global.L.layerGroup().addTo(map);
    }
  }

  function clearGraphLayers() {
    Object.values(state.edgeLayers).forEach((lyr) => {
      try { state.layer?.removeLayer(lyr); } catch (_e) { /* */ }
    });
    Object.values(state.nodeLayers).forEach((lyr) => {
      try { state.layer?.removeLayer(lyr); } catch (_e) { /* */ }
    });
    state.edgeLayers = {};
    state.nodeLayers = {};
    state.layer?.clearLayers();
  }

  function categoryEnabled(cat) {
    if (cat === 'site') return true;
    if (state.filters[cat] === false) return false;
    return true;
  }

  function edgeTooltip(edge) {
    const contrib = edge.contribution || {};
    return `
      <div class="sdg-tip">
        <strong>${escapeHtml(edge.label || edge.relation_type)}</strong>
        <p><span>Origine</span> Site étudié</p>
        <p><span>Destination</span> ${escapeHtml(edge.target)}</p>
        <p><span>Distance</span> ${edge.distance_m != null ? `${Math.round(edge.distance_m)} m` : '—'}</p>
        <p><span>Contribution</span> ${escapeHtml(contrib.display || 'Non chiffrée')}</p>
        <p><span>Source</span> ${escapeHtml(edge.source_label || 'NSME')}</p>
        <p><span>Confiance</span> ${escapeHtml(edge.confidence || '—')}</p>
        <p class="sdg-why">${escapeHtml(edge.why || '')}</p>
      </div>
    `;
  }

  function nodePopup(node) {
    const actions = node.actions || {};
    const contrib = node.contribution?.display || '—';
    return `
      <div class="sdg-popup">
        <p class="sdg-kicker">${escapeHtml(node.category || '')}</p>
        <strong>${escapeHtml(node.name)}</strong>
        <p>${escapeHtml(node.description || node.role || '')}</p>
        <p>Rôle : ${escapeHtml(node.role || '—')}</p>
        <p>Distance : ${node.distance_m != null ? `${Math.round(node.distance_m)} m` : '—'} · État : ${escapeHtml(node.state || '—')}</p>
        <p>Contribution : ${escapeHtml(contrib)}</p>
        <div class="sdg-popup-actions">
          ${actions.open_twin ? `<button type="button" class="secondary-button" data-sdg-nav="${escapeHtml(actions.open_twin)}">Profil territorial</button>` : ''}
          ${actions.open_dossier ? `<button type="button" class="secondary-button" data-sdg-nav="${escapeHtml(actions.open_dossier)}">Ouvrir le dossier</button>` : ''}
          ${actions.analyze || actions.open_workspace ? `<button type="button" class="secondary-button" data-sdg-nav="${escapeHtml(actions.analyze || actions.open_workspace)}">Analyser</button>` : ''}
        </div>
      </div>
    `;
  }

  function paintGraph(reveal) {
    if (!state.map || !state.layer || !state.graph || !global.L) return;
    const revealNodes = reveal?.nodes ? new Set(reveal.nodes) : null;
    const revealEdges = reveal?.edges ? new Set(reveal.edges) : null;

    clearGraphLayers();

    (state.graph.edges || []).forEach((edge) => {
      if (!categoryEnabled(edge.category)) return;
      if (revealEdges && !revealEdges.has(edge.id)) return;
      if (!edge.geometry?.coordinates) return;
      const latlngs = edge.geometry.coordinates.map((c) => [c[1], c[0]]);
      const line = global.L.polyline(latlngs, {
        color: edge.color || '#64748b',
        weight: edge.weight || 2,
        opacity: 0.9,
        dashArray: edge.dash || null,
        className: 'sdg-edge',
        interactive: true,
      });
      line.bindTooltip(edgeTooltip(edge), { sticky: true, className: 'sdg-tooltip', direction: 'top' });
      line.addTo(state.layer);
      state.edgeLayers[edge.id] = line;
    });

    (state.graph.nodes || []).forEach((node) => {
      if (!categoryEnabled(node.category) && node.kind !== 'site') return;
      if (revealNodes && !revealNodes.has(node.id) && node.kind !== 'site') return;
      if (node.longitude == null || node.latitude == null) return;
      const cat = (state.graph.categories || []).find((c) => c.id === node.category) || {};
      const isSite = node.kind === 'site';
      const marker = global.L.circleMarker([node.latitude, node.longitude], {
        radius: isSite ? 11 : 7,
        color: '#0f172a',
        weight: isSite ? 2 : 1,
        fillColor: cat.color || (isSite ? '#f59e0b' : '#94a3b8'),
        fillOpacity: 0.92,
        className: isSite ? 'sdg-node-site' : 'sdg-node',
      });
      marker.bindPopup(nodePopup(node), { className: 'sdg-popup-wrap', maxWidth: 280 });
      marker.bindTooltip(`${node.name} · ${node.role || node.category || ''}`, {
        direction: 'top',
        opacity: 0.95,
        className: 'sdg-tooltip',
      });
      marker.addTo(state.layer);
      state.nodeLayers[node.id] = marker;
    });

    try {
      const layers = Object.values(state.nodeLayers);
      if (layers.length) {
        const group = global.L.featureGroup(layers);
        state.map.fitBounds(group.getBounds().pad(0.25));
      }
    } catch (_e) { /* */ }
  }

  function toggleCategory(id, mode) {
    if (mode === 'isolate') {
      Object.keys(state.filters).forEach((key) => {
        state.filters[key] = key === id;
      });
      state.filters[id] = true;
    } else {
      state.filters[id] = state.filters[id] === false;
    }
    renderLegend();
    renderFilters();
    paintGraph();
  }

  function renderLegend() {
    const host = document.querySelector('#sdg-legend');
    if (!host || !state.graph) return;
    const cats = (state.graph.categories || []).filter((c) => c.id !== 'site');
    const visible = cats.filter((c) => categoryEnabled(c.id) && (c.count || 0) > 0).length;
    host.innerHTML = `
      <p class="sdg-kicker">Légende</p>
      <p class="sdg-legend-count">${visible} catégorie(s) visible(s)</p>
      <ul>
        ${cats.map((c) => `
          <li>
            <button type="button" class="sdg-legend-btn${state.filters[c.id] === false ? ' is-off' : ''}${!c.available ? ' is-future' : ''}"
              data-sdg-cat="${escapeHtml(c.id)}" ${!c.available && !c.count ? 'disabled' : ''}
              title="${escapeHtml(c.note || `${c.label} — clic : activer/désactiver · double-clic : isoler`)}"
              aria-pressed="${state.filters[c.id] !== false}">
              <span class="sdg-swatch" style="background:${escapeHtml(c.color)}" aria-hidden="true"></span>
              ${escapeHtml(c.label)}
              <em>${c.available === false && !c.count ? 'bientôt' : Number(c.count || 0)}</em>
            </button>
          </li>
        `).join('')}
      </ul>
      <p class="sdg-legend-hint">Clic : activer / désactiver · Double-clic : isoler</p>
    `;
    host.querySelectorAll('[data-sdg-cat]').forEach((btn) => {
      btn.addEventListener('click', (event) => {
        if (event.detail === 2) return;
        toggleCategory(btn.getAttribute('data-sdg-cat'), 'toggle');
      });
      btn.addEventListener('dblclick', (event) => {
        event.preventDefault();
        toggleCategory(btn.getAttribute('data-sdg-cat'), 'isolate');
      });
      btn.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          toggleCategory(btn.getAttribute('data-sdg-cat'), event.shiftKey ? 'isolate' : 'toggle');
        }
      });
    });
  }

  function renderFilters() {
    const host = document.querySelector('#sdg-filters');
    if (!host || !state.graph) return;
    const filterIds = ['population', 'localities', 'health', 'telecom', 'roads', 'ccn', 'admin', 'needs', 'fdsu_sites'];
    const filters = (state.graph.filters || []).filter((f) => filterIds.includes(f.id) || (f.count || 0) > 0 || f.available);
    host.innerHTML = `
      <p class="sdg-kicker">Filtres</p>
      <div class="sdg-filter-row">
        ${filters.map((f) => `
          <label class="sdg-filter${state.filters[f.id] === false ? ' is-off' : ''}">
            <input type="checkbox" data-sdg-filter="${escapeHtml(f.id)}" ${state.filters[f.id] === false ? '' : 'checked'} ${f.available === false && !f.count ? 'disabled' : ''} />
            <span style="border-color:${escapeHtml(f.color)}">${escapeHtml(f.label)} (${Number(f.count || 0)})</span>
          </label>
        `).join('')}
      </div>
    `;
    host.querySelectorAll('[data-sdg-filter]').forEach((input) => {
      input.addEventListener('change', () => {
        const id = input.getAttribute('data-sdg-filter');
        state.filters[id] = input.checked;
        renderLegend();
        paintGraph();
      });
    });
  }

  function renderWhy() {
    const host = document.querySelector('#sdg-why-body');
    if (!host || !state.graph) return;
    const panel = state.graph.why_panel || {};
    host.innerHTML = `
      <p class="sdg-subtitle">${escapeHtml(panel.subtitle || '')}</p>
      ${(panel.blocks || []).map((b) => `
        <article class="sdg-why-block" data-status="${escapeHtml(b.status || '')}">
          <header>
            <strong>${escapeHtml(b.title)}</strong>
            <span>${escapeHtml(b.score)}</span>
          </header>
          <p>${escapeHtml(b.justification)}</p>
          <small>Source : ${escapeHtml(b.source)}</small>
        </article>
      `).join('') || '<p>Données insuffisantes pour expliquer ce site.</p>'}
    `;
  }

  function stopPresentation(showAll) {
    state.presenting = false;
    if (state.animTimer) {
      global.clearTimeout(state.animTimer);
      state.animTimer = null;
    }
    const stopBtn = document.querySelector('#sdg-stop-btn');
    if (stopBtn) stopBtn.hidden = true;
    const label = document.querySelector('#sdg-step-label');
    if (label) label.textContent = showAll ? 'Raisonnement affiché' : '';
    if (showAll) paintGraph();
  }

  function startPresentation() {
    if (!state.presentation?.steps?.length) {
      const assetId = state.graph?._meta?.asset_id;
      if (!assetId) {
        paintGraph();
        return;
      }
      const type = state.graph?._meta?.asset_type || 'site';
      fetchJson(`/api/spatial-decision-graph/${encodeURIComponent(type)}/${encodeURIComponent(assetId)}/presentation`)
        .then((payload) => {
          state.presentation = payload;
          runPresentation();
        })
        .catch(() => paintGraph());
      return;
    }
    runPresentation();
  }

  function runPresentation() {
    stopPresentation(false);
    state.presenting = true;
    const stopBtn = document.querySelector('#sdg-stop-btn');
    if (stopBtn) stopBtn.hidden = false;
    state.animStep = -1;
    const preferReduced = global.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches;
    const next = () => {
      if (!state.presenting) return;
      state.animStep += 1;
      const steps = state.presentation.steps || [];
      if (state.animStep >= steps.length) {
        stopPresentation(true);
        return;
      }
      const step = steps[state.animStep];
      const label = document.querySelector('#sdg-step-label');
      if (label) label.textContent = `${step.label} — ${step.narrative || ''}`;
      paintGraph({ nodes: step.reveal_nodes, edges: step.reveal_edges });
      const delay = preferReduced ? 400 : (step.duration_ms || 2200);
      state.animTimer = global.setTimeout(next, delay);
    };
    next();
  }

  function mount(map, graphPayload, presentationPayload) {
    state.destroyed = false;
    setMap(map);
    state.graph = graphPayload;
    state.presentation = presentationPayload || null;
    (graphPayload.categories || []).forEach((c) => {
      if (state.filters[c.id] == null) state.filters[c.id] = true;
    });
    ensureShell();
    bindChrome();
    bindNavDelegation();
    renderWhy();
    renderLegend();
    renderFilters();
    paintGraph();
  }

  function update(graphPayload) {
    state.graph = graphPayload;
    renderWhy();
    renderLegend();
    renderFilters();
    if (!state.presenting) paintGraph();
  }

  function resize() {
    state.map?.invalidateSize?.();
  }

  function destroy() {
    stopPresentation(false);
    clearGraphLayers();
    state.destroyed = true;
  }

  function loadAndMount(map, assetType, assetId, programCode) {
    const qs = programCode ? `?program_code=${encodeURIComponent(programCode)}` : '';
    const type = assetType === 'fdsu_site' ? 'site' : assetType;
    return Promise.all([
      fetchJson(`/api/spatial-decision-graph/${encodeURIComponent(type)}/${encodeURIComponent(assetId)}${qs}`),
      fetchJson(`/api/spatial-decision-graph/${encodeURIComponent(type)}/${encodeURIComponent(assetId)}/presentation${qs}`).catch(() => null),
    ]).then(([graph, presentation]) => {
      mount(map, graph, presentation);
      return graph;
    });
  }

  global.SpatialDecisionGraph = {
    version: '2.0.0',
    uiTitle: 'Analyse d’Impact Territorial',
    technicalName: 'Spatial Decision Graph',
    mount,
    update,
    resize,
    destroy,
    loadAndMount,
    startPresentation,
    stopPresentation,
    state,
  };
})(typeof window !== 'undefined' ? window : globalThis);
