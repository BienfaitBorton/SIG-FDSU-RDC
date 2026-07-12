/**
 * Spatial Decision Graph v2.1 — Analyse d’Impact Territorial
 * Seul renderer officiel. Réutilise l’instance Leaflet passée (pas de 2e L.map).
 * Données exclusivement depuis l’API — aucune invention.
 */
(function initSpatialDecisionGraph(global) {
  const API_BASE = `${global.location.protocol}//${global.location.hostname}:8001`;
  const VERSION = '2.1.0';

  const SYMBOL_GLYPH = {
    star: '★',
    place: '◉',
    people: '◎',
    health: '✚',
    cross: '✚',
    school: '▦',
    tower: '▲',
    road: '≡',
    bolt: '⚡',
    building: '▣',
    market: '◈',
    hub: '✦',
    alert: '!',
    site: '★',
  };

  const state = {
    graph: null,
    presentation: null,
    map: null,
    layer: null,
    edgeLayers: {},
    nodeLayers: {},
    filters: {},
    defaultFilters: {},
    selected: null,
    reveal: null,
    animTimer: null,
    animStep: -1,
    presenting: false,
    destroyed: false,
    chromeBound: false,
    navBound: false,
    mapOriginalParent: null,
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
      if (!r.ok) throw new Error(`${path} → ${r.status}`);
      return r.json();
    });
  }

  function categoryMeta(id) {
    return (state.graph?.categories || []).find((c) => c.id === id) || {};
  }

  function resolveSymbol(cat) {
    const raw = cat?.symbol || (cat?.id === 'health' ? 'cross' : cat?.id) || 'place';
    if (raw === 'health') return 'cross';
    return raw;
  }

  function symbolGlyph(symbol) {
    return SYMBOL_GLYPH[symbol] || SYMBOL_GLYPH.place;
  }

  function categoryEnabled(cat) {
    if (cat === 'site') return true;
    if (state.filters[cat] === false) return false;
    return true;
  }

  function formatDistance(m) {
    if (m == null || Number.isNaN(Number(m))) return null;
    const n = Number(m);
    if (n >= 1000) {
      const km = n / 1000;
      return `${km >= 10 ? Math.round(km) : Math.round(km * 10) / 10} km`.replace('.', ',');
    }
    return `${Math.round(n)} m`;
  }

  function contributionDisplay(contrib) {
    if (!contrib) return null;
    if (contrib.display) return contrib.display;
    if (contrib.status === 'unavailable' || contrib.status == null) return 'Contribution non calculée';
    return null;
  }

  function fieldRow(label, value) {
    if (value == null || value === '' || value === '—') return '';
    return `<p class="sdg-field"><span>${escapeHtml(label)}</span> ${escapeHtml(value)}</p>`;
  }

  /* ── Shell layout (wrap / move #dxl-map safely) ───────────────── */

  function ensureShell() {
    const mapEl = document.querySelector('#dxl-map');
    if (!mapEl) return null;

    document.querySelector('#ux-legend-dxl')?.remove();

    let shell = document.querySelector('#sdg-shell');
    if (shell) {
      const host = shell.querySelector('#sdg-map-host');
      if (host && mapEl.parentElement !== host) {
        host.appendChild(mapEl);
        queueInvalidate();
      }
      return shell;
    }

    if (!state.mapOriginalParent) {
      state.mapOriginalParent = mapEl.parentElement;
    }

    shell = document.createElement('div');
    shell.id = 'sdg-shell';
    shell.className = 'sdg-shell';
    shell.setAttribute('data-sdg-version', VERSION);
    shell.innerHTML = `
      <div class="sdg-toolbar" role="toolbar" aria-label="Analyse d’Impact Territorial">
        <div class="sdg-toolbar-title">
          <p class="sdg-kicker">Analyse d’Impact Territorial</p>
          <span class="sdg-tech-name" title="Nom technique">${escapeHtml('Spatial Decision Graph')}</span>
        </div>
        <div class="sdg-toolbar-actions">
          <button type="button" class="secondary-button" id="sdg-refresh-btn">Recalculer les relations spatiales</button>
          <button type="button" class="primary-button" id="sdg-present-btn">Présenter le raisonnement</button>
          <button type="button" class="secondary-button" id="sdg-stop-btn" hidden>Interrompre</button>
          <span class="sdg-step-label" id="sdg-step-label" aria-live="polite"></span>
        </div>
      </div>
      <div id="sdg-summary" class="sdg-summary" role="region" aria-label="Synthèse décisionnelle"></div>
      <div class="sdg-main-grid">
        <aside id="sdg-filters-panel" class="sdg-panel sdg-filters-panel" aria-label="Filtres de relations">
          <header class="sdg-panel-header">
            <h3>Relations</h3>
            <p class="sdg-panel-hint">Afficher, masquer ou isoler une catégorie</p>
          </header>
          <div class="sdg-filter-actions" role="group" aria-label="Actions de filtre">
            <button type="button" class="secondary-button sdg-btn-sm" id="sdg-show-all" data-sdg-filter-action="show-all">Tout afficher</button>
            <button type="button" class="secondary-button sdg-btn-sm" id="sdg-hide-all" data-sdg-filter-action="hide-all">Tout masquer</button>
            <button type="button" class="secondary-button sdg-btn-sm" id="sdg-reset-filters" data-sdg-filter-action="reset">Réinitialiser</button>
          </div>
          <div id="sdg-filters" class="sdg-filters-list" role="list"></div>
          <p class="sdg-relations-counter" id="sdg-relations-counter" aria-live="polite">Relations affichées —</p>
          <div id="sdg-why-body" class="sdg-why-body" aria-label="Pourquoi ce site ?"></div>
        </aside>
        <div class="sdg-map-column">
          <div id="sdg-map-host" class="sdg-map-host"></div>
          <div id="sdg-kpis" class="sdg-kpis" role="region" aria-label="Indicateurs territoriaux"></div>
          <div id="sdg-legend" class="sdg-legend" role="region" aria-label="Légende interactive"></div>
        </div>
        <aside id="sdg-detail" class="sdg-panel sdg-detail-panel" aria-label="Détail de relation" aria-live="polite">
          <div class="sdg-detail-empty">
            <p class="sdg-kicker">Détail</p>
            <p>Sélectionnez un nœud ou une relation sur la carte pour afficher les informations disponibles.</p>
          </div>
        </aside>
      </div>
    `;

    const section = mapEl.closest('.dxl-section') || mapEl.parentElement;
    const host = shell.querySelector('#sdg-map-host');
    host.appendChild(mapEl);
    section.appendChild(shell);
    queueInvalidate();
    return shell;
  }

  function queueInvalidate() {
    global.requestAnimationFrame?.(() => {
      try {
        state.map?.invalidateSize?.(true);
      } catch (_e) { /* */ }
    });
    global.setTimeout(() => {
      try {
        state.map?.invalidateSize?.(true);
      } catch (_e) { /* */ }
    }, 120);
  }

  function bindChrome() {
    if (state.chromeBound) return;
    state.chromeBound = true;
    document.addEventListener('click', (event) => {
      const actionBtn = event.target?.closest?.('[data-sdg-filter-action]');
      if (actionBtn && document.querySelector('#sdg-shell')) {
        const action = actionBtn.getAttribute('data-sdg-filter-action');
        if (action === 'show-all') setAllFilters(true);
        else if (action === 'hide-all') setAllFilters(false);
        else if (action === 'reset') resetFilters();
        return;
      }
      const present = event.target?.closest?.('#sdg-present-btn');
      if (present) {
        startPresentation();
        return;
      }
      const refresh = event.target?.closest?.('#sdg-refresh-btn');
      if (refresh) {
        refreshSpatialRelations(refresh);
        return;
      }
      const stop = event.target?.closest?.('#sdg-stop-btn');
      if (stop) {
        stopPresentation(true);
      }
    });
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

  /* ── Map layers ───────────────────────────────────────────────── */

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
    try { state.layer?.clearLayers(); } catch (_e) { /* */ }
  }

  function markerIconHtml(node, cat) {
    const symbol = resolveSymbol(cat);
    const isSite = node.kind === 'site' || node.category === 'site';
    const color = cat.color || (isSite ? '#f59e0b' : '#94a3b8');
    const sizeClass = isSite ? 'sdg-marker--site' : 'sdg-marker--node';
    return `
      <span class="sdg-marker ${sizeClass} sdg-symbol-${escapeHtml(symbol)}"
            style="--sdg-color:${escapeHtml(color)}"
            role="img" aria-label="${escapeHtml(node.name || cat.label || symbol)}">
        <span class="sdg-marker-glyph" aria-hidden="true">${symbolGlyph(symbol)}</span>
      </span>
    `;
  }

  function edgeTooltip(edge) {
    const contrib = edge.contribution || edge.score_contribution || {};
    const dist = formatDistance(edge.distance_m);
    const contribLabel = contributionDisplay(contrib);
    const origin = edge.origin_label || edge.source_entity?.name || state.graph?.center?.name;
    const dest = edge.target_label || edge.target_entity?.name;
    return `
      <div class="sdg-tip">
        <p class="sdg-kicker">Relation territoriale</p>
        <strong>${escapeHtml(edge.label || edge.relation_type || 'Relation')}</strong>
        ${origin ? fieldRow('Origine', origin) : ''}
        ${dest ? fieldRow('Destination', dest) : ''}
        ${fieldRow('Type', edge.label || edge.relation_type)}
        ${dist ? fieldRow('Distance', dist) : ''}
        ${contribLabel && contrib.status !== 'unavailable' ? fieldRow('Contribution', contribLabel) : ''}
        ${fieldRow('Confiance', edge.confidence)}
        ${(edge.why || edge.explanation) ? `<p class="sdg-why"><em>Pourquoi cette relation compte</em><br>${escapeHtml(edge.why || edge.explanation)}</p>` : ''}
      </div>
    `;
  }

  function nodePopup(node) {
    const actions = node.actions || state.graph?.actions || {};
    const contrib = node.contribution?.display;
    const dist = formatDistance(node.distance_m);
    return `
      <div class="sdg-popup">
        <p class="sdg-kicker">${escapeHtml(categoryMeta(node.category).label || node.category || '')}</p>
        <strong>${escapeHtml(node.name)}</strong>
        ${node.description || node.role ? `<p>${escapeHtml(node.description || node.role)}</p>` : ''}
        ${fieldRow('Rôle', node.role)}
        ${dist ? fieldRow('Distance', dist) : ''}
        ${fieldRow('État', node.state)}
        ${contrib ? fieldRow('Contribution', contrib) : ''}
        <div class="sdg-popup-actions">
          ${actions.open_twin ? `<button type="button" class="secondary-button" data-sdg-nav="${escapeHtml(actions.open_twin)}">Profil territorial</button>` : ''}
          ${actions.open_dossier ? `<button type="button" class="secondary-button" data-sdg-nav="${escapeHtml(actions.open_dossier)}">Ouvrir le dossier</button>` : ''}
          ${(actions.analyze || actions.open_workspace) ? `<button type="button" class="secondary-button" data-sdg-nav="${escapeHtml(actions.analyze || actions.open_workspace)}">Analyser</button>` : ''}
        </div>
      </div>
    `;
  }

  function nodeVisible(node) {
    const isSite = node.kind === 'site' || node.category === 'site';
    if (isSite) return true;
    if (!categoryEnabled(node.category)) return false;
    if (state.reveal?.nodes && !state.reveal.nodes.has(node.id)) return false;
    return true;
  }

  function edgeVisible(edge) {
    if (!categoryEnabled(edge.category)) return false;
    if (state.reveal?.edges && !state.reveal.edges.has(edge.id)) return false;
    return true;
  }

  function applyVisibility() {
    let visibleEdges = 0;
    const totalEdges = (state.graph?.edges || []).length;

    Object.entries(state.edgeLayers).forEach(([id, lyr]) => {
      const edge = (state.graph?.edges || []).find((e) => e.id === id);
      const show = edge && edgeVisible(edge);
      if (show) {
        visibleEdges += 1;
        if (state.layer && !state.layer.hasLayer(lyr)) lyr.addTo(state.layer);
      } else if (state.layer?.hasLayer(lyr)) {
        state.layer.removeLayer(lyr);
      }
    });

    Object.entries(state.nodeLayers).forEach(([id, lyr]) => {
      const node = (state.graph?.nodes || []).find((n) => n.id === id);
      const show = node && nodeVisible(node);
      if (show) {
        if (state.layer && !state.layer.hasLayer(lyr)) lyr.addTo(state.layer);
      } else if (state.layer?.hasLayer(lyr)) {
        state.layer.removeLayer(lyr);
      }
    });

    updateRelationsCounter(visibleEdges, totalEdges);
  }

  function updateRelationsCounter(visible, total) {
    const el = document.querySelector('#sdg-relations-counter');
    if (!el) return;
    const v = visible != null ? visible : countVisibleEdges();
    const t = total != null ? total : (state.graph?.edges || []).length;
    el.textContent = `Relations affichées ${v} / ${t}`;
  }

  function countVisibleEdges() {
    return (state.graph?.edges || []).filter((e) => edgeVisible(e)).length;
  }

  function selectEntity(kind, payload) {
    state.selected = { kind, payload };
    renderDetail();
  }

  function paintGraph(reveal) {
    if (!state.map || !state.layer || !state.graph || !global.L) return;
    state.reveal = reveal
      ? {
          nodes: reveal.nodes ? new Set(reveal.nodes) : null,
          edges: reveal.edges ? new Set(reveal.edges) : null,
        }
      : null;

    clearGraphLayers();

    (state.graph.edges || []).forEach((edge) => {
      if (!edge.geometry?.coordinates) return;
      const latlngs = edge.geometry.coordinates.map((c) => [c[1], c[0]]);
      const catClass = String(edge.category || 'default').replace(/[^a-z0-9_-]/gi, '');
      const line = global.L.polyline(latlngs, {
        color: edge.color || '#64748b',
        weight: edge.weight || 2,
        opacity: 0.92,
        dashArray: edge.dash || null,
        className: `sdg-edge sdg-edge--${catClass}`,
        interactive: true,
      });
      line.bindTooltip(edgeTooltip(edge), { sticky: true, className: 'sdg-tooltip', direction: 'top' });
      line.on('click', () => selectEntity('edge', edge));
      state.edgeLayers[edge.id] = line;
    });

    (state.graph.nodes || []).forEach((node) => {
      if (node.longitude == null || node.latitude == null) return;
      const cat = categoryMeta(node.category || (node.kind === 'site' ? 'site' : ''));
      const isSite = node.kind === 'site' || node.category === 'site';
      const size = isSite ? 36 : 28;
      const icon = global.L.divIcon({
        className: 'sdg-div-icon',
        html: markerIconHtml(node, { ...cat, id: node.category || cat.id, color: cat.color }),
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
        popupAnchor: [0, -size / 2],
      });
      const marker = global.L.marker([node.latitude, node.longitude], {
        icon,
        zIndexOffset: isSite ? 800 : 400,
        keyboard: true,
        title: node.name || '',
      });
      marker.bindPopup(nodePopup(node), { className: 'sdg-popup-wrap', maxWidth: 300 });
      marker.bindTooltip(
        `${node.name || ''}${node.role ? ` · ${node.role}` : ''}`,
        { direction: 'top', opacity: 0.95, className: 'sdg-tooltip', offset: [0, -8] },
      );
      marker.on('click', () => selectEntity('node', node));
      state.nodeLayers[node.id] = marker;
    });

    applyVisibility();

    try {
      const visibleMarkers = Object.entries(state.nodeLayers)
        .filter(([id]) => {
          const n = (state.graph.nodes || []).find((x) => x.id === id);
          return n && nodeVisible(n);
        })
        .map(([, lyr]) => lyr);
      if (visibleMarkers.length) {
        const group = global.L.featureGroup(visibleMarkers);
        state.map.fitBounds(group.getBounds().pad(0.28));
      }
    } catch (_e) { /* */ }

    queueInvalidate();
  }

  /* ── Filters / legend ─────────────────────────────────────────── */

  function initFiltersFromGraph() {
    const next = {};
    const defaults = {};
    (state.graph?.categories || []).forEach((c) => {
      if (c.id === 'site') {
        next[c.id] = true;
        defaults[c.id] = true;
        return;
      }
      const on = c.visible_default !== false && c.status === 'active';
      next[c.id] = on;
      defaults[c.id] = on;
    });
    state.filters = next;
    state.defaultFilters = { ...defaults };
  }

  function setAllFilters(visible) {
    Object.keys(state.filters).forEach((key) => {
      if (key === 'site') {
        state.filters[key] = true;
        return;
      }
      const meta = categoryMeta(key);
      if (meta.status === 'future' || meta.status === 'empty' || (meta.available === false && !meta.count)) {
        return;
      }
      state.filters[key] = visible;
    });
    renderFilters();
    renderLegend();
    applyVisibility();
  }

  function resetFilters() {
    state.filters = { ...state.defaultFilters };
    state.reveal = null;
    renderFilters();
    renderLegend();
    applyVisibility();
  }

  function toggleCategory(id, mode) {
    const meta = categoryMeta(id);
    if (meta.status === 'future' || (meta.available === false && !meta.count)) return;

    if (mode === 'isolate') {
      Object.keys(state.filters).forEach((key) => {
        state.filters[key] = key === id || key === 'site';
      });
      state.filters[id] = true;
    } else {
      state.filters[id] = state.filters[id] === false;
    }
    renderFilters();
    renderLegend();
    applyVisibility();
  }

  function renderFilters() {
    const host = document.querySelector('#sdg-filters');
    if (!host || !state.graph) return;

    const filters = state.graph.filters || (state.graph.categories || []).filter((c) => c.id !== 'site');

    host.innerHTML = filters.map((f) => {
      const status = f.status || (f.available === false ? 'future' : ((f.count || 0) > 0 ? 'active' : 'empty'));
      const disabled = status === 'future' || status === 'empty';
      const checked = !disabled && state.filters[f.id] !== false;
      const symbol = resolveSymbol(f);
      const note = f.note || (status === 'future'
        ? 'En cours d’intégration — référentiel non encore intégré'
        : status === 'empty'
          ? 'Aucune relation pour ce site'
          : '');
      const maturity = f.maturity || (status === 'future' ? 'integrating' : status === 'empty' ? 'partial' : 'operational');
      const maturityLabel = {
        operational: 'Opérationnel',
        partial: 'Partiellement intégré',
        integrating: 'En cours d’intégration',
        anomaly: 'Anomalie d’intégration',
      }[maturity] || maturity;
      return `
        <div class="sdg-filter-row${disabled ? ' is-disabled' : ''}${!checked && !disabled ? ' is-off' : ''}${maturity === 'anomaly' ? ' is-anomaly' : ''}"
             role="listitem" data-status="${escapeHtml(status)}" data-maturity="${escapeHtml(maturity)}">
          <label class="sdg-filter">
            <input type="checkbox"
              data-sdg-filter="${escapeHtml(f.id)}"
              ${checked ? 'checked' : ''}
              ${disabled ? 'disabled' : ''}
              aria-label="${escapeHtml(f.label)}" />
            <span class="sdg-swatch sdg-symbol-${escapeHtml(symbol)}"
                  style="--sdg-color:${escapeHtml(f.color || '#94a3b8')}"
                  aria-hidden="true">${symbolGlyph(symbol)}</span>
            <span class="sdg-filter-label">${escapeHtml(f.label)}</span>
            <span class="sdg-filter-color" style="background:${escapeHtml(f.color || '#94a3b8')}" title="${escapeHtml(f.color || '')}" aria-hidden="true"></span>
            <span class="sdg-filter-count" title="${escapeHtml(note || '')}">${Number(f.count || 0)}</span>
          </label>
          ${!disabled ? `<button type="button" class="secondary-button sdg-btn-sm sdg-isolate-btn" data-sdg-isolate="${escapeHtml(f.id)}" aria-label="Isoler ${escapeHtml(f.label)}">Isoler</button>` : ''}
          <p class="sdg-filter-note"><span class="sdg-maturity sdg-maturity--${escapeHtml(maturity)}">${escapeHtml(maturityLabel)}</span>${note ? ` — ${escapeHtml(note)}` : ''}</p>
        </div>
      `;
    }).join('');

    host.querySelectorAll('[data-sdg-filter]').forEach((input) => {
      input.addEventListener('change', () => {
        const id = input.getAttribute('data-sdg-filter');
        state.filters[id] = input.checked;
        renderLegend();
        applyVisibility();
        renderFilters();
      });
    });

    host.querySelectorAll('[data-sdg-isolate]').forEach((btn) => {
      btn.addEventListener('click', () => {
        toggleCategory(btn.getAttribute('data-sdg-isolate'), 'isolate');
      });
    });

    updateRelationsCounter();
  }

  function renderLegend() {
    const host = document.querySelector('#sdg-legend');
    if (!host || !state.graph) return;
    const cats = (state.graph.categories || []).filter((c) => c.id !== 'site');
    const visible = cats.filter((c) => categoryEnabled(c.id) && (c.count || 0) > 0).length;

    host.innerHTML = `
      <p class="sdg-kicker">Légende</p>
      <p class="sdg-legend-count">${visible} catégorie(s) visible(s)</p>
      <ul class="sdg-legend-list">
        ${cats.map((c) => {
          const symbol = resolveSymbol(c);
          const off = state.filters[c.id] === false;
          const future = c.status === 'future' || (c.available === false && !c.count);
          const empty = c.status === 'empty' && !future;
          const disabled = future || (empty && !c.count);
          return `
            <li>
              <button type="button"
                class="sdg-legend-btn${off ? ' is-off' : ''}${future ? ' is-future' : ''}${empty ? ' is-empty' : ''}"
                data-sdg-cat="${escapeHtml(c.id)}"
                ${disabled ? 'disabled' : ''}
                aria-pressed="${!off && !disabled}"
                title="${escapeHtml(c.note || `${c.label} — clic : activer/désactiver · double-clic : isoler`)}">
                <span class="sdg-swatch sdg-symbol-${escapeHtml(symbol)}"
                      style="--sdg-color:${escapeHtml(c.color)}"
                      aria-hidden="true">${symbolGlyph(symbol)}</span>
                <span class="sdg-legend-label">${escapeHtml(c.label)}</span>
                <em>${future && !c.count ? 'bientôt' : Number(c.count || 0)}</em>
              </button>
            </li>
          `;
        }).join('')}
      </ul>
      <p class="sdg-legend-hint">Clic : activer / désactiver · Double-clic : isoler</p>
    `;

    host.querySelectorAll('[data-sdg-cat]').forEach((btn) => {
      let clickTimer = null;
      btn.addEventListener('click', (event) => {
        if (event.detail === 2) return;
        const id = btn.getAttribute('data-sdg-cat');
        global.clearTimeout(clickTimer);
        clickTimer = global.setTimeout(() => toggleCategory(id, 'toggle'), 220);
      });
      btn.addEventListener('dblclick', (event) => {
        event.preventDefault();
        global.clearTimeout(clickTimer);
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

  /* ── Summary / KPIs / Why / Detail ────────────────────────────── */

  function renderSummary() {
    const host = document.querySelector('#sdg-summary');
    if (!host || !state.graph) return;
    const s = state.graph.decision_summary;
    if (!s) {
      host.innerHTML = `<p class="sdg-summary-empty">Synthèse décisionnelle non disponible pour cet actif.</p>`;
      host.dataset.status = 'unavailable';
      return;
    }
    host.dataset.status = s.status || 'success';
    const meta = [];
    if (s.priority != null && s.priority !== '') meta.push(`<span class="sdg-chip">Priorité : ${escapeHtml(s.priority)}</span>`);
    if (s.score != null && s.score !== '') meta.push(`<span class="sdg-chip">Score : ${escapeHtml(s.score)}</span>`);
    if (s.confidence != null && s.confidence !== '') meta.push(`<span class="sdg-chip">Confiance : ${escapeHtml(s.confidence)}</span>`);
    host.innerHTML = `
      <p class="sdg-kicker">Synthèse décisionnelle</p>
      <p class="sdg-summary-text">${escapeHtml(s.text || '')}</p>
      ${meta.length ? `<div class="sdg-summary-meta">${meta.join('')}</div>` : ''}
      ${(s.factors || []).length ? `
        <ul class="sdg-summary-factors">
          ${s.factors.map((f) => `<li>${escapeHtml(f)}</li>`).join('')}
        </ul>
      ` : ''}
    `;
  }

  function renderKpis() {
    const host = document.querySelector('#sdg-kpis');
    if (!host || !state.graph) return;
    const kpis = state.graph.kpis;
    if (!Array.isArray(kpis) || !kpis.length) {
      host.innerHTML = `<p class="sdg-kpi-empty">Indicateurs non disponibles.</p>`;
      return;
    }
    host.innerHTML = `
      <p class="sdg-kicker">Indicateurs</p>
      <div class="sdg-kpi-grid">
        ${kpis.map((k) => {
          const unavailable = k.status === 'unavailable'
            || (k.value == null && (k.display == null || k.display === '' || k.display === 'Non disponible'));
          const display = unavailable
            ? 'Non disponible'
            : (k.display != null && k.display !== '' ? k.display : String(k.value));
          return `
            <article class="sdg-kpi" data-status="${escapeHtml(unavailable ? 'unavailable' : (k.status || 'success'))}">
              <span class="sdg-kpi-label">${escapeHtml(k.label || k.id)}</span>
              <strong class="sdg-kpi-value">${escapeHtml(display)}</strong>
              ${k.note && unavailable ? `<small>${escapeHtml(k.note)}</small>` : ''}
            </article>
          `;
        }).join('')}
      </div>
    `;
  }

  function renderWhy() {
    const host = document.querySelector('#sdg-why-body');
    if (!host || !state.graph) return;
    const panel = state.graph.why_panel || {};
    host.innerHTML = `
      <p class="sdg-kicker">${escapeHtml(panel.title || 'Pourquoi ce site ?')}</p>
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
      `).join('') || '<p class="sdg-muted">Données insuffisantes pour expliquer ce site.</p>'}
    `;
  }

  function actionButtons(actions) {
    if (!actions) return '';
    const bits = [];
    if (actions.open_twin) {
      bits.push(`<button type="button" class="secondary-button" data-sdg-nav="${escapeHtml(actions.open_twin)}">Profil territorial</button>`);
    }
    if (actions.open_dossier) {
      bits.push(`<button type="button" class="secondary-button" data-sdg-nav="${escapeHtml(actions.open_dossier)}">Ouvrir le dossier</button>`);
    }
    if (actions.analyze || actions.open_workspace) {
      bits.push(`<button type="button" class="secondary-button" data-sdg-nav="${escapeHtml(actions.analyze || actions.open_workspace)}">Analyser</button>`);
    }
    return bits.length ? `<div class="sdg-detail-actions">${bits.join('')}</div>` : '';
  }

  function renderDetail() {
    const host = document.querySelector('#sdg-detail');
    if (!host) return;

    if (!state.selected) {
      host.innerHTML = `
        <div class="sdg-detail-empty">
          <p class="sdg-kicker">Détail</p>
          <p>Sélectionnez un nœud ou une relation sur la carte pour afficher les informations disponibles.</p>
        </div>
      `;
      return;
    }

    const { kind, payload } = state.selected;

    if (kind === 'node') {
      const node = payload;
      const cat = categoryMeta(node.category);
      const actions = node.actions || state.graph?.actions || {};
      const dist = formatDistance(node.distance_m);
      const contrib = node.contribution?.display || contributionDisplay(node.contribution);
      const coords = (node.latitude != null && node.longitude != null)
        ? `${Number(node.latitude).toFixed(5)}, ${Number(node.longitude).toFixed(5)}`
        : null;
      host.innerHTML = `
        <header class="sdg-panel-header">
          <p class="sdg-kicker">${escapeHtml(cat.label || node.category || 'Nœud')}</p>
          <h3>${escapeHtml(node.name || 'Sans nom')}</h3>
        </header>
        ${fieldRow('Type', node.type_label || node.role || cat.label)}
        ${fieldRow('Référentiel source', node.referential || node.source_label)}
        ${coords ? fieldRow('Coordonnées', coords) : ''}
        ${dist ? fieldRow('Distance', dist) : ''}
        ${node.population != null ? fieldRow('Population', node.population) : ''}
        ${fieldRow('Contribution au score', contrib || 'Contribution non calculée')}
        ${(node.why || node.description) ? `<p class="sdg-why"><em>Pourquoi cette relation existe</em><br>${escapeHtml(node.why || node.description)}</p>` : ''}
        ${fieldRow('Confiance', node.confidence || node.state)}
        ${fieldRow('Source des données', node.source_label)}
        ${fieldRow('Maturité', node.maturity === 'operational' ? 'Opérationnel' : (node.maturity || cat.maturity || '—'))}
        ${fieldRow('État', node.state)}
        ${actionButtons(actions)}
      `;
      return;
    }

    if (kind === 'edge') {
      const edge = payload;
      const detail = edge.detail || {};
      const contrib = edge.contribution || edge.score_contribution || {};
      const dist = formatDistance(edge.distance_m ?? detail.distance_m);
      const actions = state.graph?.actions || {};
      const origin = edge.origin_label || edge.source_entity?.name || state.graph?.center?.name;
      const dest = edge.target_label || edge.target_entity?.name || edge.target;
      const contribLabel = contributionDisplay(contrib);
      host.innerHTML = `
        <header class="sdg-panel-header">
          <p class="sdg-kicker">${escapeHtml(categoryMeta(edge.category).label || edge.category || 'Relation')}</p>
          <h3>${escapeHtml(edge.label || edge.relation_type || 'Relation')}</h3>
        </header>
        ${fieldRow('Origine', origin)}
        ${fieldRow('Destination', dest)}
        ${fieldRow('Type', edge.label || edge.relation_type)}
        ${fieldRow('Catégorie', categoryMeta(edge.category).label || edge.category)}
        ${fieldRow('Référentiel source', edge.source_label || detail.source)}
        ${dist ? fieldRow('Distance', dist) : ''}
        ${detail.population != null ? fieldRow('Population', detail.population) : ''}
        ${contribLabel ? fieldRow('Contribution au score', contribLabel) : fieldRow('Contribution au score', 'Contribution non calculée')}
        ${(edge.why || edge.explanation || detail.why) ? `<p class="sdg-why"><em>Pourquoi cette relation compte</em><br>${escapeHtml(edge.why || edge.explanation || detail.why)}</p>` : ''}
        ${fieldRow('Confiance', edge.confidence || detail.confidence)}
        ${fieldRow('Source des données', edge.source_label || detail.source)}
        ${detail.method ? fieldRow('Méthode', detail.method) : ''}
        ${fieldRow('Maturité', 'Opérationnel')}
        ${contrib.note ? fieldRow('Note contribution', contrib.note) : ''}
        ${actionButtons(actions)}
      `;
    }
  }

  /* ── Presentation ─────────────────────────────────────────────── */

  function categoryHasData(catId) {
    if (catId === 'site' || catId === '*') return true;
    const cat = categoryMeta(catId);
    return Number(cat.count || 0) > 0;
  }

  function usablePresentationSteps() {
    const steps = state.presentation?.steps || [];
    return steps.filter((step) => {
      const cats = step.categories || [];
      if (cats.includes('*')) return true;
      if (step.id === 'site' || step.id === 'recommendation') return true;
      const hasReveal = (step.reveal_edges || []).length > 0 || (step.reveal_nodes || []).some((id) => {
        const n = (state.graph?.nodes || []).find((x) => x.id === id);
        return n && n.kind !== 'site';
      });
      if (hasReveal) return true;
      return cats.some((c) => categoryHasData(c));
    });
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
    state.reveal = null;
    if (showAll) {
      applyVisibility();
      try {
        const layers = Object.values(state.nodeLayers);
        if (layers.length && state.map && global.L) {
          state.map.fitBounds(global.L.featureGroup(layers).getBounds().pad(0.25));
        }
      } catch (_e) { /* */ }
    }
  }

  function startPresentation() {
    if (!state.presentation?.steps?.length) {
      const assetId = state.graph?._meta?.asset_id;
      if (!assetId) {
        paintGraph();
        return;
      }
      const type = state.graph?._meta?.asset_type || 'site';
      const pc = state.graph?._meta?.program_code;
      const qs = pc ? `?program_code=${encodeURIComponent(pc)}` : '';
      fetchJson(`/api/spatial-decision-graph/${encodeURIComponent(type)}/${encodeURIComponent(assetId)}/presentation${qs}`)
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
    const steps = usablePresentationSteps();
    const preferReduced = global.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches;

    const next = () => {
      if (!state.presenting) return;
      state.animStep += 1;
      if (state.animStep >= steps.length) {
        stopPresentation(true);
        return;
      }
      const step = steps[state.animStep];
      const label = document.querySelector('#sdg-step-label');
      if (label) {
        label.textContent = `${step.label}${step.narrative ? ` — ${step.narrative}` : ''}`;
      }

      // Isoler les catégories de l’étape (uniquement celles qui ont des données)
      const cats = step.categories || [];
      if (!cats.includes('*')) {
        Object.keys(state.filters).forEach((key) => {
          if (key === 'site') {
            state.filters[key] = true;
            return;
          }
          state.filters[key] = cats.includes(key) && categoryHasData(key);
        });
        renderFilters();
        renderLegend();
      } else {
        resetFilters();
      }

      paintGraph({ nodes: step.reveal_nodes, edges: step.reveal_edges });
      const delay = preferReduced ? 400 : (step.duration_ms || 2200);
      state.animTimer = global.setTimeout(next, delay);
    };
    next();
  }

  function refreshSpatialRelations(btn) {
    const meta = state.graph?._meta || {};
    const assetId = meta.asset_id;
    if (!assetId || !state.map) {
      const label = document.querySelector('#sdg-step-label');
      if (label) label.textContent = 'Recalcul impossible — actif non identifié.';
      return;
    }
    if (btn?.disabled) return;
    if (btn) {
      btn.disabled = true;
      btn.setAttribute('aria-busy', 'true');
      btn.textContent = 'Recalcul en cours…';
    }
    const label = document.querySelector('#sdg-step-label');
    if (label) label.textContent = 'Recalcul des relations spatiales (NSME)…';

    const body = {
      asset_id: Number.isFinite(Number(assetId)) ? Number(assetId) : assetId,
      persist: true,
      include_ccn: true,
      program_code: meta.program_code || undefined,
    };

    fetch(`${API_BASE}/api/spatial-matching/refresh`, {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      cache: 'no-store',
      body: JSON.stringify(body),
    })
      .then(async (r) => {
        const data = await r.json().catch(() => ({}));
        if (!r.ok) {
          throw new Error(data.detail || `Recalcul impossible (${r.status})`);
        }
        return data;
      })
      .then((data) => {
        const written = data.matches_written ?? data.details?.matches_written ?? data._meta?.matches_written;
        const msg = written != null
          ? `Recalcul terminé — ${written} relation(s) créée(s) ou mise(s) à jour.`
          : (data.message || 'Recalcul terminé.');
        if (label) label.textContent = msg;
        const type = meta.asset_type || 'site';
        const pc = meta.program_code;
        return loadAndMount(state.map, type, assetId, pc).then(() => {
          if (label) label.textContent = msg;
        });
      })
      .catch((err) => {
        if (label) {
          label.textContent = `Recalcul impossible — ${err?.message || err}`;
        }
      })
      .finally(() => {
        if (btn) {
          btn.disabled = false;
          btn.removeAttribute('aria-busy');
          btn.textContent = 'Recalculer les relations spatiales';
        }
      });
  }

  /* ── Public API ───────────────────────────────────────────────── */

  function mount(map, graphPayload, presentationPayload) {
    state.destroyed = false;
    setMap(map);
    state.graph = graphPayload;
    state.presentation = presentationPayload || null;
    state.selected = null;
    state.reveal = null;

    document.querySelector('#ux-legend-dxl')?.remove();

    initFiltersFromGraph();
    ensureShell();
    bindChrome();
    bindNavDelegation();

    renderSummary();
    renderKpis();
    renderWhy();
    renderFilters();
    renderLegend();
    renderDetail();
    paintGraph();
  }

  function update(graphPayload) {
    state.graph = graphPayload;
    initFiltersFromGraph();
    renderSummary();
    renderKpis();
    renderWhy();
    renderFilters();
    renderLegend();
    if (!state.presenting) paintGraph();
  }

  function resize() {
    queueInvalidate();
  }

  function destroy() {
    stopPresentation(false);
    clearGraphLayers();
    state.destroyed = true;
    state.selected = null;
    // Leave #dxl-map in place (inside shell) — do not recreate L.map
  }

  function loadAndMount(map, assetType, assetId, programCode) {
    const qs = programCode ? `?program_code=${encodeURIComponent(programCode)}` : '';
    const type = assetType === 'fdsu_site' ? 'site' : assetType;
    return Promise.all([
      fetchJson(`/api/spatial-decision-graph/${encodeURIComponent(type)}/${encodeURIComponent(assetId)}${qs}`),
      fetchJson(`/api/spatial-decision-graph/${encodeURIComponent(type)}/${encodeURIComponent(assetId)}/presentation${qs}`).catch(() => null),
    ]).then(([graph, presentation]) => {
      if (programCode && graph?._meta) graph._meta.program_code = programCode;
      if (graph?._meta) {
        graph._meta.asset_id = graph._meta.asset_id || assetId;
        graph._meta.asset_type = graph._meta.asset_type || type;
      }
      mount(map, graph, presentation);
      return graph;
    });
  }

  global.SpatialDecisionGraph = {
    version: VERSION,
    uiTitle: 'Analyse d’Impact Territorial',
    technicalName: 'Spatial Decision Graph',
    mount,
    update,
    resize,
    destroy,
    loadAndMount,
    startPresentation,
    stopPresentation,
    refreshSpatialRelations,
    state,
  };
})(typeof window !== 'undefined' ? window : globalThis);
