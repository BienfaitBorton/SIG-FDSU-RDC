/**
 * Spatial Decision Graph v3.1 — Analyse d’Impact Territorial
 * Seul renderer officiel. Réutilise l’instance Leaflet passée (pas de 2e L.map).
 * Données exclusivement depuis l’API — aucune invention.
 */
(function initSpatialDecisionGraph(global) {
  const API_BASE = global.__SDG_API_BASE__ || `${global.location.protocol}//${global.location.hostname}:8001`;
  const VERSION = '3.1.0';
  let INITIAL_LABELS_VISIBLE = typeof global.__SDG_LABELS_VISIBLE__ === 'boolean'
    ? global.__SDG_LABELS_VISIBLE__
    : true;
  try {
    const stored = global.sessionStorage?.getItem('sdg.labels.visible');
    if (stored === 'true' || stored === 'false') INITIAL_LABELS_VISIBLE = stored === 'true';
  } catch (_error) { /* sessionStorage peut être indisponible en contexte restreint */ }

  const SYMBOL_GLYPH = {
    star: '★',
    place: '◉',
    people: '👥',
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
    visibleObjectsRegistry: {},
    consistencyIssues: [],
    labelsEnabled: INITIAL_LABELS_VISIBLE,
    labelLayoutFrame: null,
    labelMapBound: null,
    labelMetrics: { eligible: 0, shown: 0, hidden: 0, duration_ms: 0 },
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

  function normalizeContribution(raw, category) {
    const contrib = raw && typeof raw === 'object' ? { ...raw } : {};
    const cat = category || '';
    let type = contrib.contribution_type;
    if (!type) {
      if (contrib.status === 'mapped' && contrib.criterion) {
        const disp = String(contrib.display || '');
        type = (/\d/.test(disp) || disp.includes('/')) ? 'direct' : 'indirect';
      } else if (contrib.status === 'proxy' || ['population', 'localities', 'needs'].includes(cat)) {
        type = 'indirect';
      } else if (cat === 'ccn') {
        type = 'pending_rule';
      } else if (['fdsu_sites', 'admin'].includes(cat)) {
        type = 'contextual_evidence';
      } else {
        type = 'contextual_evidence';
      }
    }
    const roleLabels = {
      direct: 'Contribution directe',
      indirect: 'Contribution indirecte',
      contextual_evidence: 'Preuve contextuelle',
      not_applicable: 'Non applicable',
      pending_rule: 'En attente de règle officielle',
    };
    const explanations = {
      direct: contrib.criterion
        ? `Cette relation attribue des points au critère « ${contrib.criterion} » selon la règle officielle appliquée.`
        : 'Points attribués selon une règle officielle sourcée.',
      indirect: ['population', 'localities', 'needs'].includes(cat)
        ? 'Cette localité ou population alimente indirectement les critères démographie et couverture.'
        : 'Cette relation alimente des critères agrégés du score, sans points isolés propres.',
      contextual_evidence: cat === 'health'
        ? 'Cet établissement confirme la présence d’un service public essentiel (preuve contextuelle).'
        : cat === 'fdsu_sites'
          ? 'Site FDSU voisin — preuve de coordination / contexte programme, sans points attribués.'
          : 'Cette relation aide à comprendre la décision sans être pondérée directement dans le score.',
      not_applicable: 'Cette relation n’entre pas dans le scoring ; elle est affichée à titre de contexte territorial.',
      pending_rule: 'Moteur CCN / DEMO — aucune pondération inventée ; en attente de règle officielle sourcée.',
    };
    return {
      ...contrib,
      contribution_type: type,
      role_label: contrib.role_label || roleLabels[type] || 'Preuve contextuelle',
      explanation: contrib.explanation || explanations[type] || explanations.contextual_evidence,
    };
  }

  function renderContributionBlock(raw, category) {
    const contrib = normalizeContribution(raw, category);
    const type = contrib.contribution_type;
    const fed = Array.isArray(contrib.fed_criteria) ? contrib.fed_criteria.filter(Boolean) : [];
    const hasCalc = type === 'direct' && (
      contrib.points != null
      || contrib.maximum != null
      || contrib.criterion
      || (contrib.display && /\d/.test(String(contrib.display)))
    );
    const calcRows = [];
    if (contrib.criterion) calcRows.push(`<p class="sdg-field"><span>Critère</span> ${escapeHtml(contrib.criterion)}</p>`);
    if (contrib.points != null || contrib.maximum != null) {
      calcRows.push(`<p class="sdg-field"><span>Points</span> ${escapeHtml(contrib.points ?? '—')} / ${escapeHtml(contrib.maximum ?? '—')}</p>`);
    } else if (contrib.display && type === 'direct') {
      calcRows.push(`<p class="sdg-field"><span>Valeur</span> ${escapeHtml(contrib.display)}</p>`);
    }
    if (contrib.weight != null && contrib.weight !== '') {
      calcRows.push(`<p class="sdg-field"><span>Pondération</span> ${escapeHtml(contrib.weight)}</p>`);
    }
    if (contrib.rule) calcRows.push(`<p class="sdg-field"><span>Règle</span> ${escapeHtml(contrib.rule)}</p>`);
    if (contrib.matrix_version) {
      calcRows.push(`<p class="sdg-field"><span>Version matrice</span> ${escapeHtml(contrib.matrix_version)}</p>`);
    }
    if (contrib.source_document) {
      calcRows.push(`<p class="sdg-field"><span>Document source</span> ${escapeHtml(contrib.source_document)}</p>`);
    }
    if (contrib.note) calcRows.push(`<p class="sdg-field"><span>Note</span> ${escapeHtml(contrib.note)}</p>`);

    return `
      <div class="sdg-contrib" data-contrib-type="${escapeHtml(type)}">
        <p class="sdg-field sdg-contrib-role"><span>Rôle dans la décision</span>
          <strong>${escapeHtml(contrib.role_label)}</strong>
        </p>
        <p class="sdg-contrib-explain">${escapeHtml(contrib.explanation)}</p>
        ${fed.length ? `<p class="sdg-field"><span>Critères alimentés</span> ${escapeHtml(fed.join(', '))}</p>` : ''}
        ${hasCalc || calcRows.length ? `
          <details class="sdg-contrib-calc">
            <summary>Voir le détail du calcul</summary>
            ${calcRows.join('') || '<p class="sdg-muted">Aucun détail chiffré supplémentaire disponible (aucune valeur inventée).</p>'}
          </details>
        ` : ''}
      </div>
    `;
  }

  function fieldRow(label, value) {
    if (value == null || value === '' || value === '—') return '';
    return `<p class="sdg-field"><span>${escapeHtml(label)}</span> ${escapeHtml(value)}</p>`;
  }

  function detailCloseButton() {
    return `
      <button type="button"
        class="epm-panel-close sdg-detail-close"
        data-epm-close-panel="detail"
        aria-label="Fermer le panneau de détail"
        title="Fermer le panneau de détail">✕</button>
    `;
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
      if (!shell.querySelector('#sdg-explainability')) {
        const summary = shell.querySelector('#sdg-summary');
        const slot = document.createElement('div');
        slot.id = 'sdg-explainability';
        slot.className = 'sdg-explainability';
        slot.setAttribute('role', 'region');
        slot.setAttribute('aria-label', 'Explicabilité de l’analyse spatiale');
        if (summary) summary.after(slot);
        else shell.prepend(slot);
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
          <button type="button" class="secondary-button sdg-label-toggle" id="sdg-label-toggle"
            aria-label="Masquer les labels permanents" title="Masquer les labels permanents (L)"
            aria-pressed="${String(state.labelsEnabled)}"><span class="sdg-label-toggle-icon" aria-hidden="true">👁</span><span>Masquer les labels</span></button>
          <button type="button" class="secondary-button" id="sdg-refresh-btn">Recalculer les relations spatiales</button>
          <button type="button" class="primary-button" id="sdg-present-btn">Présenter le raisonnement</button>
          <button type="button" class="secondary-button" id="sdg-stop-btn" hidden>Interrompre</button>
          <span class="sdg-step-label" id="sdg-step-label" aria-live="polite"></span>
        </div>
      </div>
      <div id="sdg-summary" class="sdg-summary" role="region" aria-label="Synthèse décisionnelle"></div>
      <div id="sdg-explainability" class="sdg-explainability" role="region" aria-label="Explicabilité de l’analyse spatiale"></div>
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
          <div id="sdg-layer-statistics" class="sdg-layer-statistics" aria-live="polite"></div>
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
      const labels = event.target?.closest?.('#sdg-label-toggle');
      if (labels) {
        setLabelsEnabled(!state.labelsEnabled);
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
    document.addEventListener('keydown', (event) => {
      if (event.key?.toLowerCase() !== 'l' || event.altKey || event.ctrlKey || event.metaKey) return;
      if (event.target?.matches?.('input, textarea, select, [contenteditable="true"]')) return;
      if (!document.querySelector('#sdg-shell')) return;
      event.preventDefault();
      toggleLabels();
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
    if (map && state.labelMapBound !== map) {
      state.labelMapBound = map;
      map.on?.('zoomend moveend resize', scheduleLabelLayout);
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
    state.visibleObjectsRegistry = {};
    state.consistencyIssues = [];
    try { state.layer?.clearLayers(); } catch (_e) { /* */ }
  }

  function markerIconHtml(node, cat) {
    const symbol = resolveSymbol(cat);
    const isSite = node.kind === 'site' || node.category === 'site';
    const isPriorityNeed = node.category === 'needs';
    const color = isPriorityNeed ? '#dc2626' : (cat.color || (isSite ? '#f59e0b' : '#94a3b8'));
    const sizeClass = isSite ? 'sdg-marker--site' : 'sdg-marker--node';
    return `
      <span class="sdg-marker ${sizeClass}${isPriorityNeed ? ' sdg-marker--priority-need' : ''} sdg-symbol-${escapeHtml(symbol)}"
            style="--sdg-color:${escapeHtml(color)}"
            role="img" aria-label="${escapeHtml(node.name || cat.label || symbol)}">
        <span class="sdg-marker-glyph" aria-hidden="true">${symbolGlyph(symbol)}</span>
      </span>
    `;
  }

  function formatPopulation(value) {
    if (value == null || value === '' || Number.isNaN(Number(value))) return null;
    return `${Math.round(Number(value)).toLocaleString('fr-FR')} hab.`;
  }

  function localityStableId(node) {
    return node?.need_id || node?.locality_id || node?.locality_code || node?.official_code || node?.id || null;
  }

  function localityHasSource(node) {
    return Boolean(node?.source_label || node?.referential || node?.source || node?.source_document);
  }

  function localityHasValidPopulation(node) {
    if (!localityHasSource(node) || node?.population == null || node.population === '') return false;
    const population = Number(node.population);
    return Number.isFinite(population) && population > 0;
  }

  function computePopulationSummary(graph, visibleNodes) {
    const nodes = Array.isArray(visibleNodes)
      ? visibleNodes
      : (graph?.nodes || []).filter((node) => nodeVisible(node));
    const localities = new Map();
    nodes.filter((node) => node?.category === 'localities').forEach((node) => {
      const stableId = localityStableId(node);
      if (stableId == null || stableId === '') return;
      const key = String(stableId);
      const current = localities.get(key);
      if (!current || (!localityHasValidPopulation(current) && localityHasValidPopulation(node))) {
        localities.set(key, node);
      }
    });
    const documented = Array.from(localities.values()).filter(localityHasValidPopulation);
    const totalPopulation = documented.length
      ? documented.reduce((total, node) => total + Number(node.population), 0)
      : null;
    const totalLocalities = localities.size;
    const documentedLocalities = documented.length;
    const missingPopulationCount = Math.max(0, totalLocalities - documentedLocalities);
    const dataStatus = documentedLocalities === 0
      ? 'unavailable'
      : (missingPopulationCount > 0 ? 'partial' : 'documented');
    return {
      totalPopulation,
      documentedLocalities,
      totalLocalities,
      visibleLocalities: totalLocalities,
      analyzedLocalities: documentedLocalities,
      missingPopulationCount,
      dataStatus,
      confidence: totalLocalities ? documentedLocalities / totalLocalities : 0,
    };
  }

  function currentPopulationSummary() {
    const visibleNodes = (state.graph?.nodes || []).filter((node) => node.kind !== 'site' && nodeVisible(node));
    const summary = computePopulationSummary(state.graph, visibleNodes);
    const visibleLocalities = state.visibleObjectsRegistry.localities?.visible ?? summary.visibleLocalities;
    const missingPopulationCount = Math.max(0, visibleLocalities - summary.documentedLocalities);
    return {
      ...summary,
      totalLocalities: visibleLocalities,
      visibleLocalities,
      analyzedLocalities: summary.documentedLocalities,
      missingPopulationCount,
      dataStatus: summary.documentedLocalities === 0
        ? 'unavailable'
        : (missingPopulationCount > 0 ? 'partial' : 'documented'),
      confidence: visibleLocalities ? summary.documentedLocalities / visibleLocalities : 0,
    };
  }

  function populationSummaryHtml(summary, compact = false) {
    const populationLabel = summary.dataStatus === 'partial' ? 'Population documentée' : 'Population concernée';
    const populationDisplay = formatPopulation(summary.totalPopulation) || 'Non disponible';
    const coverage = `${summary.documentedLocalities} / ${summary.totalLocalities} localités renseignées`;
    const note = summary.dataStatus === 'unavailable'
      ? 'Référentiel démographique non disponible pour ce périmètre.'
      : (summary.dataStatus === 'partial' ? 'Données partielles' : 'Données documentées');
    return `<section class="sdg-population-summary${compact ? ' is-compact' : ''}" data-sdg-population-summary data-status="${summary.dataStatus}">
      ${fieldRow(populationLabel, populationDisplay)}
      ${fieldRow('Localités visibles', summary.visibleLocalities)}
      ${fieldRow('Localités analysées', summary.analyzedLocalities)}
      ${summary.dataStatus === 'partial' ? fieldRow('Couverture démographique', coverage) : ''}
      <p class="sdg-population-summary-note">${escapeHtml(note)}</p>
    </section>`;
  }

  function populationRelationsMetricsHtml(summary) {
    const populationDisplay = formatPopulation(summary.totalPopulation) || 'Non disponible';
    const partial = summary.dataStatus === 'partial'
      ? `Données partielles — ${summary.documentedLocalities}/${summary.visibleLocalities} localités renseignées`
      : (summary.dataStatus === 'unavailable' ? 'Référentiel démographique non disponible pour ce périmètre.' : 'Données documentées');
    return `<section class="sdg-relation-business-metrics" data-sdg-relation-population data-status="${summary.dataStatus}" aria-label="Population et localités analysées">
      <div class="sdg-relation-business-row" data-sdg-relation-metric="population">
        <span class="sdg-swatch sdg-symbol-people" aria-hidden="true">${symbolGlyph('people')}</span>
        <span><strong>Population concernée</strong><small>${escapeHtml(partial)}</small></span>
        <em>${escapeHtml(populationDisplay)}</em>
      </div>
      <div class="sdg-relation-business-row" data-sdg-relation-metric="visible-localities">
        <span class="sdg-swatch sdg-symbol-place" aria-hidden="true">${symbolGlyph('place')}</span>
        <span><strong>Localités visibles</strong><small>Objets localité actuellement pris en compte sur la carte.</small></span>
        <em>${summary.visibleLocalities}</em>
      </div>
      <div class="sdg-relation-business-row" data-sdg-relation-metric="analyzed-localities">
        <span class="sdg-swatch sdg-symbol-place" aria-hidden="true">${symbolGlyph('place')}</span>
        <span><strong>Localités analysées</strong><small>Localités disposant d’une population valide et sourcée.</small></span>
        <em>${summary.analyzedLocalities}</em>
      </div>
    </section>`;
  }

  function labelPriority(node) {
    if (node.kind === 'site' || node.category === 'site') return 100;
    return ({ population: 95, localities: 90, needs: 88, health: 76, ccn: 74, telecom: 70, admin: 64, education: 62, markets: 60, roads: 58, fdsu_sites: 56 }[node.category] || 50);
  }

  function nodeLabelHtml(node) {
    const dist = formatDistance(node.distance_m);
    const localityPopulation = ['localities', 'population'].includes(node.category)
      ? formatPopulation(node.population)
      : null;
    const served = node.population_served ?? node.population_concerned ?? node.population_potentially_covered;
    const servedPopulation = !['localities', 'population'].includes(node.category) ? formatPopulation(served) : null;
    return `<span class="sdg-map-label-content" data-sdg-label-id="${escapeHtml(node.id)}" data-sdg-label-priority="${labelPriority(node)}">
      <strong>${escapeHtml(node.name || categoryMeta(node.category).label || 'Objet territorial')}</strong>
      ${localityPopulation ? `<small>${escapeHtml(localityPopulation)}</small>` : ''}
      ${servedPopulation ? `<small>Population desservie : ${escapeHtml(servedPopulation)}</small>` : ''}
      ${!localityPopulation && dist ? `<small>${escapeHtml(dist)}</small>` : ''}
    </span>`;
  }

  function scheduleLabelLayout() {
    if (state.labelLayoutFrame) global.cancelAnimationFrame?.(state.labelLayoutFrame);
    state.labelLayoutFrame = global.requestAnimationFrame?.(() => {
      state.labelLayoutFrame = null;
      layoutMapLabels();
    }) || global.setTimeout(layoutMapLabels, 0);
  }

  function rectanglesOverlap(a, b, padding = 6) {
    return !(a.right + padding < b.left || a.left > b.right + padding || a.bottom + padding < b.top || a.top > b.bottom + padding);
  }

  function layoutMapLabels() {
    const started = global.performance?.now?.() || Date.now();
    const zoom = state.map?.getZoom?.() ?? 12;
    const maxLabels = zoom <= 7 ? 10 : zoom <= 9 ? 20 : zoom <= 11 ? 42 : 90;
    const candidates = Object.entries(state.nodeLayers).map(([id, marker]) => {
      const node = (state.graph?.nodes || []).find((item) => item.id === id);
      const element = marker.getTooltip?.()?.getElement?.();
      return node && element && nodeVisible(node) ? { node, marker, element, priority: labelPriority(node) } : null;
    }).filter(Boolean).sort((a, b) => b.priority - a.priority || Number(a.node.distance_m || 0) - Number(b.node.distance_m || 0));

    const accepted = [];
    let shown = 0;
    candidates.forEach((item) => {
      item.element.classList.remove('is-collision-hidden');
      item.element.removeAttribute('aria-hidden');
      if (!state.labelsEnabled) return;
      const isSite = item.node.kind === 'site' || item.node.category === 'site';
      const progressiveVisible = isSite || shown < maxLabels;
      const rect = item.element.getBoundingClientRect();
      const collides = !isSite && accepted.some((other) => rectanglesOverlap(rect, other));
      const visible = progressiveVisible && !collides;
      item.element.classList.toggle('is-collision-hidden', !visible);
      if (!visible) item.element.setAttribute('aria-hidden', 'true');
      if (visible) {
        accepted.push(rect);
        shown += 1;
      }
    });
    const ended = global.performance?.now?.() || Date.now();
    state.labelMetrics = { eligible: candidates.length, shown, hidden: Math.max(0, candidates.length - shown), duration_ms: Math.round((ended - started) * 10) / 10 };
    document.querySelector('#sdg-shell')?.setAttribute('data-label-layout-ms', String(state.labelMetrics.duration_ms));
  }

  function setLabelsEnabled(enabled) {
    state.labelsEnabled = Boolean(enabled);
    global.__SDG_LABELS_VISIBLE__ = state.labelsEnabled;
    try { global.sessionStorage?.setItem('sdg.labels.visible', String(state.labelsEnabled)); } catch (_error) { /* */ }
    Object.values(state.nodeLayers).forEach((marker) => {
      const tooltip = marker.getTooltip?.();
      if (!tooltip) return;
      tooltip.options.permanent = state.labelsEnabled;
      if (state.labelsEnabled && state.layer?.hasLayer(marker)) marker.openTooltip?.();
      else marker.closeTooltip?.();
    });
    const button = document.querySelector('#sdg-label-toggle');
    if (button) {
      button.setAttribute('aria-pressed', String(state.labelsEnabled));
      const action = state.labelsEnabled ? 'Masquer' : 'Afficher';
      button.setAttribute('aria-label', `${action} les labels permanents`);
      button.title = `${action} les labels permanents (L)`;
      button.innerHTML = `<span class="sdg-label-toggle-icon" aria-hidden="true">${state.labelsEnabled ? '👁' : '⊘'}</span><span>${action} les labels</span>`;
    }
    const dockButton = document.querySelector('#epm-btn-labels');
    if (dockButton) {
      const action = state.labelsEnabled ? 'Masquer' : 'Afficher';
      dockButton.setAttribute('aria-pressed', String(state.labelsEnabled));
      dockButton.setAttribute('aria-label', `${action} les labels permanents`);
      dockButton.title = `${action} les labels permanents`;
      dockButton.classList.toggle('is-active', state.labelsEnabled);
      const icon = dockButton.querySelector('[aria-hidden="true"]');
      if (icon) icon.textContent = state.labelsEnabled ? '👁' : '⊘';
    }
    document.querySelector('#sdg-shell')?.classList.toggle('sdg-labels-off', !state.labelsEnabled);
    scheduleLabelLayout();
  }

  function setLabelsVisible(visible) {
    setLabelsEnabled(visible);
  }

  function toggleLabels() {
    setLabelsEnabled(!state.labelsEnabled);
    return state.labelsEnabled;
  }

  function refreshLabels() {
    setLabelsEnabled(state.labelsEnabled);
    return state.labelMetrics;
  }

  function edgeTooltip(edge) {
    const contrib = edge.contribution || edge.score_contribution || {};
    const dist = formatDistance(edge.distance_m);
    const role = normalizeContribution(contrib, edge.category).role_label;
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
        ${fieldRow('Rôle dans la décision', role)}
        ${fieldRow('Confiance', edge.confidence)}
        ${(edge.why || edge.explanation) ? `<p class="sdg-why"><em>Pourquoi cette relation compte</em><br>${escapeHtml(edge.why || edge.explanation)}</p>` : ''}
      </div>
    `;
  }

  function nodePopup(node) {
    const actions = node.actions || state.graph?.actions || {};
    const role = normalizeContribution(node.contribution || node.score_contribution, node.category).role_label;
    const dist = formatDistance(node.distance_m);
    return `
      <div class="sdg-popup">
        <p class="sdg-kicker">${escapeHtml(categoryMeta(node.category).label || node.category || '')}</p>
        <strong>${escapeHtml(node.name)}</strong>
        ${node.description || node.role ? `<p>${escapeHtml(node.description || node.role)}</p>` : ''}
        ${fieldRow('Rôle', node.role)}
        ${dist ? fieldRow('Distance', dist) : ''}
        ${fieldRow('État', node.state)}
        ${fieldRow('Rôle dans la décision', role)}
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

  function rebuildVisibleObjectsRegistry() {
    const registry = {};
    (state.graph?.categories || []).forEach((category) => {
      if (category.id === 'site') return;
      const nodes = (state.graph?.nodes || []).filter((node) => node.category === category.id);
      const edges = (state.graph?.edges || []).filter((edge) => edge.category === category.id);
      const drawableNodes = nodes.filter((node) => Boolean(state.nodeLayers[node.id]));
      const drawableEdges = edges.filter((edge) => Boolean(state.edgeLayers[edge.id]));
      const visibleNodes = drawableNodes.filter((node) => nodeVisible(node)
        && Boolean(state.layer?.hasLayer(state.nodeLayers[node.id])));
      const visibleEdges = drawableEdges.filter((edge) => edgeVisible(edge)
        && Boolean(state.layer?.hasLayer(state.edgeLayers[edge.id])));
      const available = drawableNodes.length + drawableEdges.length;
      const visible = visibleNodes.length + visibleEdges.length;
      const declared = Number(category.count || 0);
      registry[category.id] = {
        id: category.id,
        label: category.label || category.id,
        declared,
        available,
        visible,
        hidden: Math.max(0, available - visible),
        outside: Math.max(0, declared - available),
        state: available === 0 ? 'unavailable' : (visible > 0 ? 'visible' : 'hidden'),
        nodeIds: drawableNodes.map((node) => node.id),
        edgeIds: drawableEdges.map((edge) => edge.id),
      };
    });
    state.visibleObjectsRegistry = registry;
    return registry;
  }

  function validateSpatialLayers() {
    const registry = rebuildVisibleObjectsRegistry();
    const issues = Object.values(registry).filter((entry) => {
      const announced = entry.state === 'visible' ? entry.visible : 0;
      const drawn = entry.nodeIds.filter((id) => state.layer?.hasLayer(state.nodeLayers[id])).length
        + entry.edgeIds.filter((id) => state.layer?.hasLayer(state.edgeLayers[id])).length;
      return announced !== drawn;
    });
    state.consistencyIssues = issues;
    if (issues.length) console.warn('[SpatialDecisionGraph] Incohérence détectée', issues);
    renderLayerStatistics();
    return { valid: issues.length === 0, issues, registry };
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

    rebuildVisibleObjectsRegistry();
    updateRelationsCounter(visibleEdges, totalEdges);
    renderSummary();
    renderKpis();
    renderDetail();
    renderLegend();
    renderFilters();
    validateSpatialLayers();
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
        zIndexOffset: isSite ? 800 : (node.category === 'needs' ? 700 : 400),
        keyboard: true,
        title: node.name || '',
      });
      marker.bindPopup(nodePopup(node), {
        className: 'sdg-popup-wrap',
        maxWidth: 300,
        autoPan: true,
        keepInView: true,
        autoPanPadding: [80, 80],
      });
      marker.bindTooltip(nodeLabelHtml(node), {
        permanent: state.labelsEnabled,
        interactive: false,
        direction: 'right',
        opacity: 1,
        className: `sdg-map-label sdg-map-label--${String(node.category || 'site').replace(/[^a-z0-9_-]/gi, '')}`,
        offset: [Math.round(size / 2) + 6, 0],
      });
      marker.on('mouseover', () => { if (!state.labelsEnabled) marker.openTooltip?.(); });
      marker.on('mouseout', () => { if (!state.labelsEnabled) marker.closeTooltip?.(); });
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
    scheduleLabelLayout();
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

    const filters = (state.graph.filters || (state.graph.categories || []).filter((c) => c.id !== 'site'))
      .filter((filter) => filter.id !== 'population');

    const registry = state.visibleObjectsRegistry;
    host.innerHTML = populationRelationsMetricsHtml(currentPopulationSummary()) + filters.map((f) => {
      const stats = registry[f.id] || { available: 0, visible: 0, hidden: 0, outside: Number(f.count || 0), state: 'unavailable' };
      const status = f.status || (f.available === false ? 'future' : ((f.count || 0) > 0 ? 'active' : 'empty'));
      const disabled = status === 'future' || status === 'empty';
      const checked = !disabled && state.filters[f.id] !== false;
      const symbol = resolveSymbol(f);
      const note = f.note || (status === 'future'
        ? 'En cours d’intégration — référentiel non encore intégré'
        : status === 'empty'
          ? 'Aucune relation pour ce site'
          : '');
      const maturity = f.maturity || (status === 'future' ? 'integrating' : status === 'empty' ? 'empty' : 'operational');
      const maturityLabel = {
        operational: 'Référentiel intégré',
        empty: 'Aucun objet trouvé',
        partial: 'Données partielles',
        integrating: 'En cours d’intégration',
        error: 'Erreur d’intégration',
        demonstration: 'Démonstration / partiel',
        anomaly: 'Anomalie d’intégration',
      }[maturity] || maturity;
      const nearest = f.nearest_context;
      const nearestLine = nearest
        ? ` Plus proche : ${nearest.name || 'objet'}${nearest.operator ? ` (${nearest.operator})` : ''}${nearest.distance_km != null ? ` — ${nearest.distance_km} km` : ''}.`
        : '';
      const impactLine = f.business_impact ? ` Impact : ${f.business_impact}` : '';
      const fullNote = `${note || ''}${nearestLine}${impactLine}`.trim();
      return `
        <div class="sdg-filter-row${disabled ? ' is-disabled' : ''}${!checked && !disabled ? ' is-off' : ''}${maturity === 'error' || maturity === 'anomaly' ? ' is-anomaly' : ''}"
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
            <span class="sdg-filter-count" title="${escapeHtml(fullNote || '')}">${stats.visible}</span>
          </label>
          ${!disabled ? `<button type="button" class="secondary-button sdg-btn-sm sdg-isolate-btn" data-sdg-isolate="${escapeHtml(f.id)}" aria-label="Isoler ${escapeHtml(f.label)}">Isoler</button>` : ''}
          <p class="sdg-filter-note"><span class="sdg-maturity sdg-maturity--${escapeHtml(maturity)}">${escapeHtml(maturityLabel)}</span>${fullNote ? ` — ${escapeHtml(fullNote)}` : ''}</p>
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
    const registry = state.visibleObjectsRegistry;
    const cats = (state.graph.categories || []).filter((c) => c.id !== 'site' && (registry[c.id]?.available || 0) > 0);
    const visible = cats.filter((c) => registry[c.id]?.visible > 0).length;

    host.innerHTML = `
      <p class="sdg-kicker">Légende</p>
      <p class="sdg-legend-count">${visible} catégorie(s) visible(s)</p>
      <ul class="sdg-legend-list">
        ${cats.map((c) => {
          const symbol = resolveSymbol(c);
          const stats = registry[c.id];
          const off = stats.state !== 'visible';
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
                <em>${stats.visible}</em>
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

  function routeAvailabilityDiagnostic() {
    const domain = (state.graph?.domain_statuses || []).find((item) => item.domain === 'roads');
    const stats = state.visibleObjectsRegistry.roads || { available: 0 };
    if (domain?.reference_available === false) {
      return '⚠ référentiel absent — Routes non disponibles dans le référentiel';
    }
    if (stats.available === 0) {
      return '✓ aucune route dans le rayon — Aucune route détectée dans le périmètre analysé';
    }
    return `✓ ${stats.available} route(s) analysée(s)`;
  }

  function renderLayerStatistics() {
    const host = document.querySelector('#sdg-layer-statistics');
    if (!host) return;
    const rows = Object.values(state.visibleObjectsRegistry).filter((row) => row.id !== 'population');
    const issues = state.consistencyIssues || [];
    host.innerHTML = `
      <p class="sdg-kicker">Statistiques des couches</p>
      ${issues.length ? `<div class="sdg-consistency-alert" role="alert">⚠ Incohérence détectée
        <button type="button" class="secondary-button sdg-btn-sm" id="sdg-recalculate-layer">Recalculer la couche</button></div>` : ''}
      <div class="sdg-layer-stats-list">
        ${rows.map((row) => `<article class="sdg-layer-stat" data-sdg-layer-stat="${escapeHtml(row.id)}" data-state="${row.state}">
          <strong>${escapeHtml(row.label)}</strong>
          <span>${row.available} disponible(s)</span><span>${row.visible} visible(s)</span>
          <span>${row.hidden} masqué(s)</span><span>${row.outside} hors périmètre</span>
        </article>`).join('')}
      </div>
      <div class="sdg-availability-diagnostic">
        <p class="sdg-kicker">Diagnostic de disponibilité</p>
        ${rows.map((row) => `<p><strong>${escapeHtml(row.label)}</strong> ${row.id === 'roads'
          ? escapeHtml(routeAvailabilityDiagnostic())
          : (row.available ? `✓ ${row.available} objet(s) analysé(s)` : '⚠ aucun objet géolocalisé dans le périmètre')}</p>`).join('')}
      </div>`;
    host.querySelector('#sdg-recalculate-layer')?.addEventListener('click', (event) => {
      refreshSpatialRelations(event.currentTarget);
    });
  }

  /* ── Summary / KPIs / Why / Detail ────────────────────────────── */

  function renderExplainability() {
    const host = document.querySelector('#sdg-explainability');
    if (!host || !state.graph) return;
    const card = state.graph.explainability;
    const cls = card?.classification || state.graph._meta?.classification || state.graph._meta?.status;
    if (!card) {
      host.innerHTML = '';
      host.hidden = true;
      return;
    }
    host.hidden = false;
    host.dataset.classification = cls || '';
    const avail = (card.available || []).map((i) => `<li class="is-ok">✓ ${escapeHtml(i)}</li>`).join('');
    const miss = (card.missing || []).map((i) => `<li class="is-miss">⚠ ${escapeHtml(i)}</li>`).join('');
    host.innerHTML = `
      <div class="sdg-explain-card" data-classification="${escapeHtml(cls || '')}">
        <div class="sdg-explain-head">
          <p class="sdg-kicker">Couverture analytique</p>
          <span class="sdg-explain-badge">${escapeHtml(card.badge || card.title || '')}</span>
        </div>
        <h3>${escapeHtml(card.title || 'Analyse spatiale')}</h3>
        <p>${escapeHtml(card.message || '')}</p>
        <div class="sdg-explain-cols">
          <div>
            <p class="sdg-explain-col-title">Données disponibles</p>
            <ul>${avail || '<li>—</li>'}</ul>
          </div>
          <div>
            <p class="sdg-explain-col-title">Données manquantes</p>
            <ul>${miss || '<li>Aucune bloquante identifiée</li>'}</ul>
          </div>
        </div>
        ${(card.causes || []).length ? `<p class="sdg-muted">Causes : ${(card.causes || []).map((c) => escapeHtml(c)).join(' · ')}</p>` : ''}
        <p class="sdg-muted">${escapeHtml(card.hint || '')}</p>
      </div>
    `;
  }

  function renderSummary() {
    const host = document.querySelector('#sdg-summary');
    if (!host || !state.graph) return;
    const s = state.graph.decision_summary;
    const populationSummary = currentPopulationSummary();
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
      <p class="sdg-summary-text">${escapeHtml(s.text || s.message || '')}</p>
      ${populationSummaryHtml(populationSummary, true)}
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
    const sourceKpis = Array.isArray(state.graph.kpis) ? state.graph.kpis : [];
    if (!sourceKpis.length) {
      host.innerHTML = `<p class="sdg-kpi-empty">Indicateurs non disponibles.</p>`;
      return;
    }
    const source = Object.fromEntries(sourceKpis.map((item) => [item.id, item]));
    const visibleNodes = (state.graph.nodes || []).filter((node) => node.kind !== 'site' && nodeVisible(node));
    const populationSummary = currentPopulationSummary();
    const distances = visibleNodes.map((node) => Number(node.distance_m)).filter((value) => Number.isFinite(value));
    const averageDistance = distances.length ? distances.reduce((sum, value) => sum + value, 0) / distances.length : null;
    const operatorNames = new Set();
    visibleNodes.filter((node) => node.category === 'telecom').forEach((node) => {
      const text = `${node.operator || ''} ${node.state || ''}`;
      const match = text.match(/\b(Airtel|Africell|Orange|Vodacom)\b/i);
      if (match) operatorNames.add(match[1].toLowerCase());
    });
    const active = (id) => categoryEnabled(id);
    const kpis = [
      { ...source.population, id: 'population', label: populationSummary.dataStatus === 'partial' ? 'Population documentée' : 'Population concernée', value: populationSummary.totalPopulation, display: formatPopulation(populationSummary.totalPopulation) || 'Non disponible', status: populationSummary.dataStatus === 'unavailable' ? 'unavailable' : populationSummary.dataStatus, note: populationSummary.dataStatus === 'unavailable' ? 'Référentiel démographique non disponible pour ce périmètre.' : (populationSummary.dataStatus === 'partial' ? `${populationSummary.documentedLocalities} / ${populationSummary.totalLocalities} localités renseignées · Données partielles` : 'Population totale documentée des localités visibles.') },
      { ...source.localities, id: 'localities', label: 'Localités visibles', value: populationSummary.visibleLocalities, display: String(populationSummary.visibleLocalities), status: 'success', note: `${populationSummary.analyzedLocalities} localité(s) analysée(s) dans le calcul de Population concernée.` },
      { id: 'average_distance', label: 'Distance moyenne', value: averageDistance, display: averageDistance == null ? 'Non disponible' : formatDistance(averageDistance), status: averageDistance == null ? 'unavailable' : 'success', note: 'Moyenne des distances réellement calculées pour les objets visibles.' },
      { ...source.health, id: 'health', label: 'Services de santé', value: active('health') ? source.health?.value : 0, display: active('health') ? source.health?.display : '0' },
      { ...source.education, id: 'education', label: 'Écoles' },
      { id: 'mobile_operators', label: 'Opérateurs mobiles', value: operatorNames.size || null, display: operatorNames.size ? String(operatorNames.size) : 'Non disponible', status: operatorNames.size ? 'success' : 'unavailable', note: operatorNames.size ? Array.from(operatorNames).map((name) => name[0].toUpperCase() + name.slice(1)).join(', ') : 'Aucun opérateur identifiable dans les objets télécom visibles.' },
      { ...source.ccn, id: 'ccn', label: 'CCN', value: active('ccn') ? source.ccn?.value : 0, display: active('ccn') ? source.ccn?.display : '0' },
    ];
    host.innerHTML = `
      <p class="sdg-kicker">Résumé d’impact</p>
      <div class="sdg-kpi-grid">
        ${kpis.map((k) => {
          const unavailable = k.status === 'unavailable'
            || (k.value == null && (k.display == null || k.display === '' || k.display === 'Non disponible'));
          const display = unavailable
            ? 'Non disponible'
            : (k.display != null && k.display !== '' ? k.display : String(k.value));
          const note = k.note || '';
          const nearest = k.detail && k.detail.nearest_context;
          const nearestTxt = nearest
            ? `Plus proche : ${nearest.name || ''}${nearest.distance_km != null ? ` — ${nearest.distance_km} km` : ''}`
            : '';
          return `
            <article class="sdg-kpi" data-sdg-kpi="${escapeHtml(k.id)}" data-status="${escapeHtml(unavailable ? 'unavailable' : (k.status || 'success'))}">
              <span class="sdg-kpi-label">${escapeHtml(k.label || k.id)}</span>
              <strong class="sdg-kpi-value">${escapeHtml(display)}</strong>
              ${note ? `<small>${escapeHtml(note)}</small>` : ''}
              ${nearestTxt ? `<small>${escapeHtml(nearestTxt)}</small>` : ''}
            </article>
          `;
        }).join('')}
      </div>
    `;
  }

  function populationImpactBlock(payload, kind) {
    const detail = payload?.detail || {};
    const contribution = normalizeContribution(payload?.contribution || payload?.score_contribution, payload?.category);
    const population = payload?.population_served
      ?? payload?.population_concerned
      ?? payload?.population_potentially_covered
      ?? payload?.population
      ?? detail.population
      ?? contribution.proxy_population;
    const contributionValue = contribution.points != null
      ? `${contribution.points}${contribution.maximum != null ? ` / ${contribution.maximum}` : ''}`
      : contribution.display;
    const weight = contribution.weight;
    const socialImpact = contribution.explanation || payload?.why || payload?.description || detail.why;
    const hasData = population != null || contributionValue || weight != null || socialImpact;
    return `<section class="sdg-population-impact" data-sdg-population-status="${hasData ? 'documented' : 'unavailable'}">
      <p class="sdg-kicker">Impact populationnel</p>
      ${population != null ? fieldRow(kind === 'node' && payload.category === 'localities' ? 'Population concernée' : 'Population potentiellement couverte', formatPopulation(population)) : ''}
      ${contributionValue ? fieldRow('Contribution dans le score', contributionValue) : ''}
      ${weight != null ? fieldRow('Poids de la relation', weight) : ''}
      ${socialImpact ? fieldRow('Impact social', socialImpact) : ''}
      ${!hasData ? '<p class="sdg-muted">Aucune donnée populationnelle calculée pour cet objet.</p>' : ''}
    </section>`;
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
      const populationSummary = currentPopulationSummary();
      host.innerHTML = `
        <div class="sdg-detail-empty">
          <header class="sdg-panel-header sdg-panel-header--with-close">
            ${detailCloseButton()}
            <p class="sdg-kicker">Détail</p>
          </header>
          <p>Sélectionnez un nœud ou une relation sur la carte pour afficher les informations disponibles.</p>
        </div>
        ${populationSummaryHtml(populationSummary)}
      `;
      return;
    }

    const { kind, payload } = state.selected;

    if (kind === 'node') {
      const node = payload;
      const cat = categoryMeta(node.category);
      const actions = node.actions || state.graph?.actions || {};
      const dist = formatDistance(node.distance_m);
      const coords = (node.latitude != null && node.longitude != null)
        ? `${Number(node.latitude).toFixed(5)}, ${Number(node.longitude).toFixed(5)}`
        : null;
      host.innerHTML = `
        <header class="sdg-panel-header sdg-panel-header--with-close">
          ${detailCloseButton()}
          <p class="sdg-kicker">${escapeHtml(cat.label || node.category || 'Nœud')}</p>
          <h3>${escapeHtml(node.name || 'Sans nom')}</h3>
        </header>
        ${fieldRow('Type', node.type_label || node.role || cat.label)}
        ${fieldRow('Référentiel source', node.referential || node.source_label)}
        ${coords ? fieldRow('Coordonnées', coords) : ''}
        ${dist ? fieldRow('Distance', dist) : ''}
        ${node.population != null ? fieldRow('Population', node.population) : ''}
        ${populationImpactBlock(node, 'node')}
        ${renderContributionBlock(node.contribution || node.score_contribution, node.category)}
        ${(node.why || node.description) ? `<p class="sdg-why"><em>Pourquoi cette relation existe</em><br>${escapeHtml(node.why || node.description)}</p>` : ''}
        ${fieldRow('Confiance', node.confidence || node.state)}
        ${fieldRow('Source des données', node.source_label)}
        ${fieldRow('Maturité d’analyse', node.maturity === 'operational' ? 'Référentiel intégré' : (node.maturity || cat.maturity || '—'))}
        ${fieldRow('État', node.state)}
        ${actionButtons(actions)}
        ${populationSummaryHtml(currentPopulationSummary(), true)}
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
      host.innerHTML = `
        <header class="sdg-panel-header sdg-panel-header--with-close">
          ${detailCloseButton()}
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
        ${populationImpactBlock(edge, 'edge')}
        ${renderContributionBlock(contrib, edge.category)}
        ${(edge.why || edge.explanation || detail.why) ? `<p class="sdg-why"><em>Pourquoi cette relation compte</em><br>${escapeHtml(edge.why || edge.explanation || detail.why)}</p>` : ''}
        ${fieldRow('Confiance', edge.confidence || detail.confidence)}
        ${fieldRow('Source des données', edge.source_label || detail.source)}
        ${detail.method ? fieldRow('Méthode', detail.method) : ''}
        ${fieldRow('Maturité d’analyse', 'Référentiel intégré')}
        ${actionButtons(actions)}
        ${populationSummaryHtml(currentPopulationSummary(), true)}
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
        state.presenting = true;
        const stopBtn = document.querySelector('#sdg-stop-btn');
        if (stopBtn) stopBtn.hidden = false;
        const label = document.querySelector('#sdg-step-label');
        if (label) label.textContent = 'Préparation du raisonnement…';
        return;
      }
      const type = state.graph?._meta?.asset_type || 'site';
      const pc = state.graph?._meta?.program_code;
      const qs = pc ? `?program_code=${encodeURIComponent(pc)}` : '';
      state.presenting = true;
      const stopBtn = document.querySelector('#sdg-stop-btn');
      if (stopBtn) stopBtn.hidden = false;
      const label = document.querySelector('#sdg-step-label');
      if (label) label.textContent = 'Préparation du raisonnement…';
      fetchJson(`/api/spatial-decision-graph/${encodeURIComponent(type)}/${encodeURIComponent(assetId)}/presentation${qs}`)
        .then((payload) => {
          state.presentation = payload;
          if (state.presenting) runPresentation();
        })
        .catch(() => stopPresentation(true));
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

  function repaint(revealPayload) {
    paintGraph(revealPayload || null);
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
    renderExplainability();
    renderKpis();
    renderWhy();
    renderFilters();
    renderLegend();
    renderDetail();
    paintGraph();
    setLabelsEnabled(state.labelsEnabled);
  }

  function update(graphPayload) {
    state.graph = graphPayload;
    initFiltersFromGraph();
    renderSummary();
    renderExplainability();
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
    // Shell visible immédiatement (évite timeout E2E pendant le fetch graphe).
    setMap(map);
    ensureShell();
    bindChrome();
    bindNavDelegation();
    const summary = document.querySelector('#sdg-summary');
    if (summary && !state.graph) {
      summary.innerHTML = '<p class="sdg-kicker">Analyse d’Impact Territorial</p><p>Chargement des relations spatiales…</p>';
    }
    return fetchJson(`/api/spatial-decision-graph/${encodeURIComponent(type)}/${encodeURIComponent(assetId)}${qs}`).then((graph) => {
      if (programCode && graph?._meta) graph._meta.program_code = programCode;
      if (graph?._meta) {
        graph._meta.asset_id = graph._meta.asset_id || assetId;
        graph._meta.asset_type = graph._meta.asset_type || type;
      }
      mount(map, graph, null);
      fetchJson(
        `/api/spatial-decision-graph/${encodeURIComponent(type)}/${encodeURIComponent(assetId)}/presentation${qs}`,
      ).then((presentation) => {
        if (state.graph !== graph || !presentation) return;
        state.presentation = presentation;
        if (state.presenting) runPresentation();
      }).catch(() => {
        if (state.graph === graph && state.presenting) stopPresentation(true);
      });
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
    validateSpatialLayers,
    repaint,
    setLabelsEnabled,
    setLabelsVisible,
    toggleLabels,
    refreshLabels,
    layoutMapLabels,
    computePopulationSummary,
    getPopulationSummary: currentPopulationSummary,
    state,
    get visibleObjectsRegistry() { return state.visibleObjectsRegistry; },
    get labelMetrics() { return state.labelMetrics; },
  };
})(typeof window !== 'undefined' ? window : globalThis);
