/**
 * SigDecisionCartographyExperience — Phase 2.1
 * EXECUTIVE PRESENTATION MODE (Mode Présentation DG)
 * UX/UI uniquement — aucun moteur métier, aucun calcul.
 */
(function initSigDecisionCartographyExperience(global) {
  const POPUP_PAD = [96, 96];
  const VERSION = '2.1.0';

  const state = {
    attached: false,
    active: false,
    mode: 'free', // free | guided
    tourIndex: 0,
    tourPaused: false,
    attachToken: 0,
    lastSelectedKey: '',
    snapshot: null,
    selectionWatcher: null,
    fullscreenActive: false,
  };

  /** Scénario de présentation guidée — étapes vides sautées à l’exécution */
  const GUIDED_STEPS = [
    { id: 'site', title: 'Le site sélectionné', narrative: 'Point d’ancrage du dossier de décision.', categories: ['site'], zoom: 'site', required: true },
    { id: 'localities', title: 'Les localités concernées', narrative: 'Localités et besoins territoriaux liés au site.', categories: ['localities', 'needs'] },
    { id: 'population', title: 'La population concernée', narrative: 'Somme documentée des populations des localités analysées.', categories: ['localities'] },
    { id: 'health', title: 'Les établissements de santé', narrative: 'Structures sanitaires dans la zone d’influence.', categories: ['health'] },
    { id: 'telecom', title: 'Les télécommunications', narrative: 'Infrastructures et couverture télécom.', categories: ['telecom'] },
    { id: 'fibre', title: 'La fibre', narrative: 'Proximité fibre / backbone (sous-ensemble télécom).', categories: ['telecom'], fibreFocus: true },
    { id: 'roads', title: 'Les routes', narrative: 'Accessibilité et corridors routiers.', categories: ['roads'] },
    { id: 'fdsu_sites', title: 'Les autres Sites FDSU', narrative: 'Sites du programme national à proximité.', categories: ['fdsu_sites'] },
    { id: 'ccn', title: 'Les CCN', narrative: 'Ancrage des Centres Communautaires Numériques.', categories: ['ccn', 'admin'] },
    { id: 'indicators', title: 'Les indicateurs', narrative: 'Synthèse des indicateurs territoriaux clés.', focus: 'indicators', required: true },
    { id: 'recommendation', title: 'La recommandation finale', narrative: 'Synthèse décisionnelle et recommandation du dossier.', focus: 'recommendation', categories: ['*'], required: true },
  ];

  const KPI_DEFS = [
    { id: 'population', label: 'Population concernée', cat: 'localities', metric: 'population', icon: '👥' },
    { id: 'localities', label: 'Localités visibles', cat: 'localities', metric: 'visibleLocalities', icon: '◉' },
    { id: 'analyzed_localities', label: 'Localités analysées', cat: 'localities', metric: 'analyzedLocalities', icon: '◉' },
    { id: 'health', label: 'Santé', cat: 'health', icon: '✚' },
    { id: 'telecom', label: 'Télécom', cat: 'telecom', icon: '▲' },
    { id: 'roads', label: 'Routes', cat: 'roads', icon: '≡' },
    { id: 'fdsu_sites', label: 'Sites FDSU', cat: 'fdsu_sites', icon: '★' },
    { id: 'ccn', label: 'CCN', cat: 'ccn', icon: '✦' },
    { id: 'score', label: 'Score', cat: null, icon: '◈', fromSummary: 'score' },
    { id: 'priority', label: 'Priorité', cat: null, icon: '◆', fromSummary: 'priority' },
    { id: 'confidence', label: 'Confiance', cat: null, icon: '◇', fromSummary: 'confidence' },
  ];

  function sdg() {
    return global.SpatialDecisionGraph || null;
  }

  function map() {
    return sdg()?.state?.map || global.DxlCore?.state?.map || null;
  }

  function shell() {
    return document.querySelector('#sdg-shell');
  }

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function prefersReducedMotion() {
    return Boolean(global.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches);
  }

  function queueInvalidate() {
    global.requestAnimationFrame?.(() => {
      try { map()?.invalidateSize?.(true); } catch (_e) { /* */ }
    });
    global.setTimeout(() => {
      try { map()?.invalidateSize?.(true); } catch (_e) { /* */ }
    }, 80);
    global.setTimeout(() => {
      try { map()?.invalidateSize?.(true); } catch (_e) { /* */ }
    }, 280);
  }

  function categoryMeta(id) {
    return (sdg()?.state?.graph?.categories || []).find((c) => c.id === id) || {};
  }

  function categoryHasData(catId) {
    if (!catId || catId === 'site' || catId === '*') return true;
    return Number(categoryMeta(catId).count || 0) > 0;
  }

  function stepHasData(step) {
    if (!step) return false;
    if (step.required) return true;
    if (step.focus) return true;
    if (step.fibreFocus) {
      return hasFibreSignals();
    }
    return (step.categories || []).some((c) => categoryHasData(c));
  }

  function hasFibreSignals() {
    const graph = sdg()?.state?.graph;
    if (!graph) return false;
    if (!categoryHasData('telecom')) return false;
    const fibreRe = /fibr|fttx|backbone|mw/i;
    const inNodes = (graph.nodes || []).some((n) => n.category === 'telecom' && fibreRe.test(`${n.name || ''} ${n.role || ''} ${n.description || ''}`));
    const inEdges = (graph.edges || []).some((e) => e.category === 'telecom' && fibreRe.test(`${e.label || ''} ${e.relation_type || ''}`));
    return inNodes || inEdges || categoryHasData('telecom');
  }

  function usableGuidedSteps() {
    return GUIDED_STEPS.filter((s) => stepHasData(s));
  }

  function dossierMeta() {
    const payload = global.DxlCore?.state?.payload || {};
    const caseFile = payload.caseFile || payload.decisionCase || {};
    const asset = caseFile.asset || caseFile.site || {};
    const nsme = payload.nsmeImpact?.asset || {};
    const summary = sdg()?.state?.graph?.decision_summary || {};
    const graphCenter = sdg()?.state?.graph?.center || {};
    const titleEl = document.querySelector('#dxl-title');
    const name = asset.site_name || asset.name || nsme.site_name || nsme.name || graphCenter.name
      || (titleEl?.textContent || '').replace(/^Dossier de décision\s*[—–-]\s*/i, '').trim()
      || 'Site';
    const program = asset.program_code || nsme.program_code || global.DxlCore?.state?.programCode || '—';
    const priority = asset.priority_level_label || asset.priority_level || summary.priority || '—';
    const score = asset.priority_score ?? summary.score ?? '—';
    const confidence = summary.confidence || '—';
    return { name, program, priority, score, confidence };
  }

  function basemapLabel() {
    try {
      const mgr = map()?.__sigBasemapManager || global.DxlCore?.state?.map?.__sigBasemapManager;
      return mgr?.getActiveProviderLabel?.() || mgr?.getActiveProviderId?.() || 'Carte';
    } catch (_e) {
      return 'Carte';
    }
  }

  function setNarrative(text) {
    const el = document.querySelector('#epm-narrative');
    if (el) el.textContent = text || '';
  }

  function setTourCounter(index, total) {
    const el = document.querySelector('#epm-tour-counter');
    if (el) el.textContent = total ? `${index + 1}/${total}` : '';
  }

  /* ── Snapshot / restore ───────────────────────────────────────── */

  function captureSnapshot() {
    const m = map();
    const SDG = sdg();
    const center = m?.getCenter?.();
    return {
      zoom: m?.getZoom?.(),
      lat: center?.lat,
      lng: center?.lng,
      filters: SDG?.state?.filters ? { ...SDG.state.filters } : null,
      selected: SDG?.state?.selected || null,
      scrollY: global.scrollY || 0,
      panelsOpen: {
        relations: !document.querySelector('#sdg-filters-panel')?.classList.contains('epm-panel-hidden'),
        detail: !document.querySelector('#sdg-detail')?.classList.contains('epm-panel-hidden'),
      },
    };
  }

  function restoreSnapshot() {
    const snap = state.snapshot;
    if (!snap) return;
    const m = map();
    const SDG = sdg();
    if (m && snap.lat != null && snap.lng != null) {
      try {
        m.setView([snap.lat, snap.lng], snap.zoom ?? m.getZoom(), { animate: false });
      } catch (_e) { /* */ }
    }
    if (SDG?.state && snap.filters) {
      SDG.state.filters = { ...snap.filters };
      document.querySelectorAll('[data-sdg-filter]').forEach((input) => {
        const id = input.getAttribute('data-sdg-filter');
        if (!id || input.disabled) return;
        const checked = snap.filters[id] !== false;
        if (input.checked !== checked) {
          input.checked = checked;
          input.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });
    }
    if (typeof snap.scrollY === 'number') {
      global.scrollTo(0, snap.scrollY);
    }
    queueInvalidate();
  }

  /* ── Filters / zoom / highlight ───────────────────────────────── */

  function syncFilters(categories) {
    const SDG = sdg();
    if (!SDG?.state?.filters) return;
    const cats = categories || [];
    Object.keys(SDG.state.filters).forEach((key) => {
      if (key === 'site') {
        SDG.state.filters[key] = true;
        return;
      }
      if (cats.includes('*')) {
        SDG.state.filters[key] = categoryHasData(key);
        return;
      }
      SDG.state.filters[key] = cats.includes(key) && categoryHasData(key);
    });
    document.querySelectorAll('[data-sdg-filter]').forEach((input) => {
      const id = input.getAttribute('data-sdg-filter');
      if (!id || input.disabled) return;
      const checked = SDG.state.filters[id] !== false;
      if (input.checked !== checked) {
        input.checked = checked;
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
  }

  function zoomForStep(step) {
    const m = map();
    const SDG = sdg();
    if (!m || !SDG?.state?.nodeLayers || !global.L) return;
    const markers = [];
    if (step?.zoom === 'site' || step?.id === 'site') {
      const siteNode = (SDG.state.graph?.nodes || []).find((n) => n.kind === 'site' || n.category === 'site');
      if (siteNode && SDG.state.nodeLayers[siteNode.id]) markers.push(SDG.state.nodeLayers[siteNode.id]);
    } else if (step?.categories && !step.categories.includes('*')) {
      (SDG.state.graph?.nodes || []).forEach((node) => {
        if (step.categories.includes(node.category) && SDG.state.nodeLayers[node.id]) {
          markers.push(SDG.state.nodeLayers[node.id]);
        }
      });
      const siteNode = (SDG.state.graph?.nodes || []).find((n) => n.kind === 'site' || n.category === 'site');
      if (siteNode && SDG.state.nodeLayers[siteNode.id]) markers.push(SDG.state.nodeLayers[siteNode.id]);
    }
    if (!markers.length) {
      Object.values(SDG.state.nodeLayers).forEach((lyr) => markers.push(lyr));
    }
    if (!markers.length) return;
    try {
      const group = global.L.featureGroup(markers);
      m.fitBounds(group.getBounds().pad(0.28), {
        animate: !prefersReducedMotion(),
        duration: prefersReducedMotion() ? 0 : 0.75,
      });
    } catch (_e) { /* */ }
  }

  function highlightCategories(cats) {
    document.querySelectorAll('.sdg-marker').forEach((el) => {
      el.classList.remove('epm-spotlight', 'epm-dimmed');
    });
    document.querySelectorAll('.sdg-edge').forEach((el) => el.classList.remove('epm-edge-reveal'));
    if (!cats || cats.includes('*')) return;
    const SDG = sdg();
    if (!SDG?.state?.nodeLayers) return;
    (SDG.state.graph?.nodes || []).forEach((node) => {
      const lyr = SDG.state.nodeLayers[node.id];
      const el = lyr?.getElement?.();
      if (!el) return;
      const match = cats.includes(node.category) || (node.kind === 'site' && cats.includes('site'))
        || node.kind === 'site' || node.category === 'site';
      if (match && (cats.includes(node.category) || node.kind === 'site')) {
        el.classList.add('epm-spotlight');
      } else {
        el.classList.add('epm-dimmed');
      }
    });
    Object.values(SDG.state.edgeLayers || {}).forEach((line) => {
      const path = line?.getElement?.();
      if (path) path.classList.add('epm-edge-reveal');
    });
    global.setTimeout(() => {
      document.querySelectorAll('.sdg-marker').forEach((el) => {
        el.classList.remove('epm-spotlight', 'epm-dimmed');
      });
    }, 2400);
  }

  /* ── KPI strip ────────────────────────────────────────────────── */

  function kpiValue(def) {
    const graph = sdg()?.state?.graph;
    if (!graph) return '—';
    if (def.metric) {
      const summary = sdg()?.getPopulationSummary?.();
      if (!summary) return '—';
      if (def.metric === 'population') {
        return summary.totalPopulation == null
          ? 'Non disponible'
          : `${Math.round(Number(summary.totalPopulation)).toLocaleString('fr-FR')} hab.`;
      }
      return String(summary[def.metric] ?? 0);
    }
    if (def.fromSummary) {
      const s = graph.decision_summary || {};
      const v = s[def.fromSummary];
      return v == null || v === '' ? '—' : String(v);
    }
    const cat = categoryMeta(def.cat);
    if (cat.count != null) return String(cat.count);
    const kpi = (graph.kpis || []).find((k) => {
      const id = String(k.id || '').toLowerCase();
      const label = String(k.label || '').toLowerCase();
      return id.includes(def.cat) || label.includes(def.label.toLowerCase());
    });
    if (!kpi) return '—';
    if (kpi.status === 'unavailable') return '—';
    return kpi.display != null && kpi.display !== '' ? String(kpi.display) : (kpi.value != null ? String(kpi.value) : '—');
  }

  function renderKpiStrip() {
    const host = document.querySelector('#epm-kpi-strip');
    if (!host) return;
    host.innerHTML = KPI_DEFS.map((def) => {
      const value = kpiValue(def);
      const empty = value === '—' || value === '0';
      return `
        <button type="button" class="epm-kpi${empty ? ' is-empty' : ''}" data-epm-kpi="${escapeHtml(def.id)}"
          aria-label="${escapeHtml(def.label)} : ${escapeHtml(value)}" title="${escapeHtml(def.label)}">
          <span class="epm-kpi-icon" aria-hidden="true">${def.icon}</span>
          <span class="epm-kpi-meta">
            <span class="epm-kpi-label">${escapeHtml(def.label)}</span>
            <strong class="epm-kpi-value">${escapeHtml(value)}</strong>
          </span>
        </button>
      `;
    }).join('');

    host.querySelectorAll('[data-epm-kpi]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = btn.getAttribute('data-epm-kpi');
        const def = KPI_DEFS.find((d) => d.id === id);
        if (!def) return;
        if (def.cat) {
          syncFilters([def.cat]);
          zoomForStep({ categories: [def.cat] });
          highlightCategories([def.cat]);
          setNarrative(`${def.label} — isolation de la catégorie sur la carte.`);
          openPanel('relations');
        } else if (def.fromSummary) {
          openPanel('detail');
          setNarrative(`${def.label} : ${kpiValue(def)}.`);
          const summary = document.querySelector('#sdg-summary');
          if (summary) {
            document.querySelector('#epm-detail-body').innerHTML = summary.innerHTML;
          }
        }
        btn.classList.add('is-active');
        global.setTimeout(() => btn.classList.remove('is-active'), 1200);
      });
    });
  }

  function refreshTopbar() {
    const meta = dossierMeta();
    const nameEl = document.querySelector('#epm-site-name');
    const progEl = document.querySelector('#epm-program');
    const priEl = document.querySelector('#epm-priority');
    const scoreEl = document.querySelector('#epm-score');
    const baseEl = document.querySelector('#epm-basemap');
    if (nameEl) nameEl.textContent = meta.name;
    if (progEl) progEl.textContent = meta.program;
    if (priEl) priEl.textContent = meta.priority;
    if (scoreEl) scoreEl.textContent = String(meta.score);
    if (baseEl) baseEl.textContent = basemapLabel();
  }

  /* ── Panels ───────────────────────────────────────────────────── */

  function openPanel(which) {
    const relations = document.querySelector('#sdg-filters-panel');
    const detail = document.querySelector('#sdg-detail');
    if (which === 'relations' && relations) {
      relations.classList.remove('epm-panel-hidden');
      relations.classList.add('epm-panel-open');
      document.querySelector('#epm-btn-layers')?.classList.add('is-active');
      document.querySelector('#epm-btn-layers')?.setAttribute('aria-pressed', 'true');
    }
    if (which === 'detail' && detail) {
      detail.classList.remove('epm-panel-hidden');
      detail.classList.add('epm-panel-open');
      document.querySelector('#epm-btn-detail')?.classList.add('is-active');
      document.querySelector('#epm-btn-detail')?.setAttribute('aria-pressed', 'true');
    }
    queueInvalidate();
  }

  function closePanel(which) {
    if (which === 'relations' || which === 'all') {
      document.querySelector('#sdg-filters-panel')?.classList.add('epm-panel-hidden');
      document.querySelector('#sdg-filters-panel')?.classList.remove('epm-panel-open');
      document.querySelector('#epm-btn-layers')?.classList.remove('is-active');
      document.querySelector('#epm-btn-layers')?.setAttribute('aria-pressed', 'false');
    }
    if (which === 'detail' || which === 'all') {
      document.querySelector('#sdg-detail')?.classList.add('epm-panel-hidden');
      document.querySelector('#sdg-detail')?.classList.remove('epm-panel-open');
      document.querySelector('#epm-btn-detail')?.classList.remove('is-active');
      document.querySelector('#epm-btn-detail')?.setAttribute('aria-pressed', 'false');
    }
    queueInvalidate();
  }

  function togglePanel(which) {
    const el = which === 'relations'
      ? document.querySelector('#sdg-filters-panel')
      : document.querySelector('#sdg-detail');
    if (!el) return;
    if (el.classList.contains('epm-panel-hidden')) openPanel(which);
    else closePanel(which);
  }

  function hidePanelsForEntry() {
    closePanel('all');
    document.querySelector('#sdg-filters-panel')?.classList.add('epm-panel-hidden');
    document.querySelector('#sdg-detail')?.classList.add('epm-panel-hidden');
  }

  /* ── Popups & selection ───────────────────────────────────────── */

  function patchPopups() {
    const m = map();
    if (!m) return;
    if (!m.__epmPopupPatched) {
      m.__epmPopupPatched = true;
      m.on('popupopen', (event) => {
        const popup = event?.popup;
        const el = popup?.getElement?.();
        if (!el) return;
        el.classList.add('epm-popup-visible');
        const content = el.querySelector('.leaflet-popup-content');
        if (content) {
          content.style.maxHeight = 'min(42vh, 320px)';
          content.style.overflowY = 'auto';
        }
        ensurePopupInView(m, el);
      });
    }
    const SDG = sdg();
    Object.values(SDG?.state?.nodeLayers || {}).forEach((marker) => {
      const popup = marker.getPopup?.();
      if (popup) {
        popup.options.autoPan = true;
        popup.options.keepInView = true;
        popup.options.autoPanPadding = POPUP_PAD;
        popup.options.maxWidth = 280;
      }
    });
  }

  function ensurePopupInView(m, el) {
    const pad = 88;
    const rect = el.getBoundingClientRect();
    const container = m.getContainer().getBoundingClientRect();
    let dx = 0;
    let dy = 0;
    if (rect.right > container.right - pad) dx = container.right - pad - rect.right;
    if (rect.left < container.left + pad) dx = container.left + pad - rect.left;
    if (rect.bottom > container.bottom - pad) dy = container.bottom - pad - rect.bottom;
    if (rect.top < container.top + pad) dy = container.top + pad - rect.top;
    if (dx || dy) m.panBy([dx, dy], { animate: true, duration: 0.28 });
  }

  function panToSelection(forceOpen = false) {
    if (!state.active) return;
    const SDG = sdg();
    const m = map();
    if (!SDG?.state?.selected || !m) return;
    const { kind, payload } = SDG.state.selected;
    const key = `${kind}:${payload?.id || payload?.name || ''}`;
    // Même sélection : ne pas réouvrir automatiquement (l’utilisateur peut avoir fermé ✕)
    if (key === state.lastSelectedKey && !forceOpen) {
      return;
    }
    state.lastSelectedKey = key;
    openPanel('detail');
    let latlng = null;
    if (kind === 'node' && payload?.latitude != null && payload?.longitude != null) {
      latlng = global.L?.latLng(payload.latitude, payload.longitude);
    } else if (kind === 'edge' && payload?.geometry?.coordinates?.length) {
      const coords = payload.geometry.coordinates;
      const mid = coords[Math.floor(coords.length / 2)];
      if (mid) latlng = global.L?.latLng(mid[1], mid[0]);
    }
    if (!latlng) return;

    const pt = m.latLngToContainerPoint(latlng);
    const size = m.getSize();
    const detail = document.querySelector('#sdg-detail');
    let offsetX = 0;
    if (detail && !detail.classList.contains('epm-panel-hidden')) {
      offsetX = Math.min(detail.getBoundingClientRect().width * 0.2, 80);
    }
    const dx = size.x * 0.5 - offsetX - pt.x;
    const dy = size.y * 0.52 - pt.y;
    if (Math.abs(dx) > 10 || Math.abs(dy) > 10) {
      m.panBy([dx, dy], { animate: !prefersReducedMotion(), duration: 0.32 });
    }
    if (kind === 'node' && payload?.id && SDG.state.nodeLayers[payload.id]) {
      const el = SDG.state.nodeLayers[payload.id].getElement?.();
      el?.classList.add('epm-selected');
      global.setTimeout(() => el?.classList.remove('epm-selected'), 1600);
    }
  }

  /* ── Guided tour ──────────────────────────────────────────────── */

  function runGuidedStep(index) {
    const steps = usableGuidedSteps();
    if (!steps.length) return;
    const clamped = Math.max(0, Math.min(index, steps.length - 1));
    const step = steps[clamped];
    state.tourIndex = clamped;
    setTourCounter(clamped, steps.length);
    setNarrative(`${step.title} — ${step.narrative}`);
    updateGuidedControls();
    document.querySelectorAll('.epm-dock-btn[data-epm-cmd]').forEach((b) => b.classList.remove('is-active'));
    document.querySelector('#epm-btn-guided')?.classList.add('is-active');

    // Fermer le détail lors d’un changement d’étape — le contexte carte prévaut
    closePanel('detail');
    // Conserver la clé de sélection pour éviter une réouverture auto par le watcher
    const sel = sdg()?.state?.selected;
    if (sel) {
      state.lastSelectedKey = `${sel.kind}:${sel.payload?.id || sel.payload?.name || ''}`;
    }

    global.SpatialDecisionGraph?.stopPresentation?.(false);

    if (step.focus === 'indicators') {
      syncFilters(['site', 'localities', 'health', 'telecom', 'roads', 'fdsu_sites', 'ccn'].filter(categoryHasData));
      renderKpiStrip();
      document.querySelector('#epm-kpi-strip')?.classList.add('epm-kpi-pulse');
      global.setTimeout(() => document.querySelector('#epm-kpi-strip')?.classList.remove('epm-kpi-pulse'), 1800);
      zoomForStep({ zoom: 'site', categories: ['site'] });
      return;
    }
    if (step.focus === 'recommendation') {
      syncFilters(['*']);
      zoomForStep({ categories: ['*'] });
      const summary = sdg()?.state?.graph?.decision_summary;
      const meta = dossierMeta();
      const body = document.querySelector('#epm-reco-card');
      if (body) {
        body.hidden = false;
        body.innerHTML = `
          <p class="epm-reco-kicker">Recommandation</p>
          <p class="epm-reco-text">${escapeHtml(summary?.text || 'Synthèse décisionnelle disponible dans le dossier.')}</p>
          <div class="epm-reco-meta">
            <span>Priorité : ${escapeHtml(String(meta.priority))}</span>
            <span>Score : ${escapeHtml(String(meta.score))}</span>
            <span>Confiance : ${escapeHtml(String(meta.confidence))}</span>
          </div>
        `;
      }
      return;
    }

    document.querySelector('#epm-reco-card')?.setAttribute('hidden', '');
    syncFilters(step.categories || []);
    zoomForStep(step);
    highlightCategories(step.categories || []);
    patchPopups();
  }

  function updateGuidedControls() {
    const steps = usableGuidedSteps();
    const prev = document.querySelector('#epm-btn-prev');
    const next = document.querySelector('#epm-btn-next');
    if (prev) prev.disabled = state.tourIndex <= 0;
    if (next) next.disabled = state.tourIndex >= steps.length - 1;
    document.querySelector('#epm-guided-nav')?.classList.toggle('is-visible', state.mode === 'guided');
  }

  function tourNext() {
    if (state.tourPaused) return;
    runGuidedStep(state.tourIndex + 1);
  }

  function tourPrev() {
    if (state.tourPaused) return;
    runGuidedStep(state.tourIndex - 1);
  }

  function tourTogglePause() {
    state.tourPaused = !state.tourPaused;
    const btn = document.querySelector('#epm-btn-pause');
    if (btn) {
      btn.classList.toggle('is-active', state.tourPaused);
      btn.setAttribute('aria-pressed', String(state.tourPaused));
      btn.title = state.tourPaused ? 'Reprendre' : 'Pause';
      btn.setAttribute('aria-label', state.tourPaused ? 'Reprendre' : 'Pause');
    }
    setNarrative(state.tourPaused ? 'Présentation en pause.' : `Reprise — ${usableGuidedSteps()[state.tourIndex]?.title || ''}`);
  }

  function startGuided() {
    state.mode = 'guided';
    state.tourPaused = false;
    document.body.dataset.epmMode = 'guided';
    document.querySelector('#epm-btn-guided')?.classList.add('is-active');
    document.querySelector('#epm-btn-free')?.classList.remove('is-active');
    document.querySelector('#epm-reco-card')?.setAttribute('hidden', '');
    runGuidedStep(0);
  }

  function startFree() {
    state.mode = 'free';
    state.tourPaused = false;
    document.body.dataset.epmMode = 'free';
    document.querySelector('#epm-btn-free')?.classList.add('is-active');
    document.querySelector('#epm-btn-guided')?.classList.remove('is-active');
    document.querySelector('#epm-guided-nav')?.classList.remove('is-visible');
    document.querySelector('#epm-reco-card')?.setAttribute('hidden', '');
    setNarrative('Présentation libre — explorez la carte, isolez les couches, ouvrez les détails.');
    setTourCounter(0, 0);
    global.SpatialDecisionGraph?.stopPresentation?.(true);
    document.querySelector('[data-sdg-filter-action="show-all"]')?.click();
    queueInvalidate();
  }

  /* ── Fullscreen ───────────────────────────────────────────────── */

  function requestBrowserFullscreen() {
    const target = document.querySelector('#sdg-shell')
      || document.querySelector('#decision-experience-panel')
      || document.documentElement;
    const req = target.requestFullscreen || target.webkitRequestFullscreen || target.msRequestFullscreen;
    if (!req) return Promise.resolve(false);
    return Promise.resolve(req.call(target)).then(() => {
      state.fullscreenActive = true;
      return true;
    }).catch(() => false);
  }

  function exitBrowserFullscreen() {
    if (!document.fullscreenElement && !document.webkitFullscreenElement) {
      state.fullscreenActive = false;
      return Promise.resolve();
    }
    const exit = document.exitFullscreen || document.webkitExitFullscreen || document.msExitFullscreen;
    if (!exit) return Promise.resolve();
    return Promise.resolve(exit.call(document)).then(() => {
      state.fullscreenActive = false;
    }).catch(() => {});
  }

  /* ── Enter / Exit ─────────────────────────────────────────────── */

  function enterPresentation(mode = 'free') {
    if (!shell() || state.active) {
      if (state.active && mode === 'guided') startGuided();
      else if (state.active && mode === 'free') startFree();
      return;
    }

    state.snapshot = captureSnapshot();
    state.active = true;
    state.lastSelectedKey = '';
    document.body.classList.add('executive-presentation-mode');
    document.body.classList.remove('decision-demo-mode');

    document.querySelectorAll('.decision-experience-module > .dxl-topbar, .decision-experience-module > .dxl-section').forEach((el) => {
      if (el.id === 'sdg-shell' || el.id === 'dxl-section-territorial-impact' || el.querySelector?.('#sdg-shell') || el.querySelector?.('#dxl-map')) return;
      el.dataset.epmHidden = 'true';
    });

    ['.sdg-toolbar', '#sdg-summary', '#sdg-explainability', '#sdg-kpis', '#sdg-legend'].forEach((sel) => {
      document.querySelector(sel)?.setAttribute('data-epm-hidden', 'true');
    });

    hidePanelsForEntry();
    document.querySelector('#epm-root')?.removeAttribute('hidden');
    document.querySelector('#epm-enter-btn')?.setAttribute('hidden', '');

    refreshTopbar();
    renderKpiStrip();
    if (global.TerritorialImpactUI?.syncPresentationImpactKpis && global.__tieLastSiteProfile) {
      global.TerritorialImpactUI.syncPresentationImpactKpis(global.__tieLastSiteProfile);
    }
    patchPopups();

    // Fullscreen navigateur désactivé sous automation (Playwright) — fallback CSS viewport
    const skipFs = Boolean(global.navigator?.webdriver);
    const fsPromise = skipFs ? Promise.resolve(false) : requestBrowserFullscreen();
    fsPromise.finally(() => {
      queueInvalidate();
      if (mode === 'guided') startGuided();
      else startFree();
    });
  }

  function exitPresentation() {
    if (!state.active) return;
    exitBrowserFullscreen();
    state.active = false;
    state.tourPaused = false;
    document.body.classList.remove('executive-presentation-mode');
    delete document.body.dataset.epmMode;

    document.querySelectorAll('[data-epm-hidden]').forEach((el) => {
      delete el.dataset.epmHidden;
      el.removeAttribute('data-epm-hidden');
    });

    document.querySelector('#sdg-filters-panel')?.classList.remove('epm-panel-hidden', 'epm-panel-open');
    document.querySelector('#sdg-detail')?.classList.remove('epm-panel-hidden', 'epm-panel-open');
    document.querySelector('#epm-root')?.setAttribute('hidden', '');
    document.querySelector('#epm-enter-btn')?.removeAttribute('hidden');
    document.querySelector('#epm-reco-card')?.setAttribute('hidden', '');
    setNarrative('');

    global.SpatialDecisionGraph?.stopPresentation?.(true);
    restoreSnapshot();
    queueInvalidate();
  }

  function resetView() {
    document.querySelector('[data-sdg-filter-action="reset"]')?.click();
    document.querySelector('[data-sdg-filter-action="show-all"]')?.click();
    document.querySelector('#epm-reco-card')?.setAttribute('hidden', '');
    closePanel('all');
    if (state.mode === 'guided') runGuidedStep(0);
    else {
      setNarrative('Vue réinitialisée.');
      queueInvalidate();
    }
  }

  function printView() {
    document.body.classList.add('epm-print');
    global.print();
    global.setTimeout(() => document.body.classList.remove('epm-print'), 400);
  }

  function cycleBasemap() {
    const mgr = map()?.__sigBasemapManager;
    if (mgr?.applyProvider && global.SigBasemapManager?.getProviders) {
      const ids = Object.keys(global.SigBasemapManager.getProviders());
      const current = mgr.getActiveProviderId();
      const idx = Math.max(0, ids.indexOf(current));
      const next = ids[(idx + 1) % ids.length];
      mgr.applyProvider(next);
      refreshTopbar();
      setNarrative(`Fond de carte : ${basemapLabel()}`);
      return;
    }
    refreshTopbar();
    setNarrative(`Fond de carte actif : ${basemapLabel()}`);
  }

  function showHelp() {
    setNarrative('Échap : quitter · Guidé : scénario étape par étape · Libre : exploration · KPI : isoler une catégorie · Couches / Détail : panneaux contextuels.');
  }

  /* ── DOM injection ────────────────────────────────────────────── */

  function injectChrome() {
    const mapHost = document.querySelector('#sdg-map-host');
    if (!mapHost) return;

    if (!mapHost.querySelector('#epm-enter-btn')) {
      const enter = document.createElement('button');
      enter.type = 'button';
      enter.id = 'epm-enter-btn';
      enter.className = 'epm-enter-btn';
      enter.setAttribute('aria-label', 'Mode Présentation');
      enter.title = 'Mode Présentation — expérience immersive pour gouvernance / CA / bailleurs';
      enter.innerHTML = '<span aria-hidden="true">⛶</span> Mode Présentation';
      mapHost.appendChild(enter);
      enter.addEventListener('click', () => enterPresentation('free'));
    }

    if (document.querySelector('#epm-root')) return;

    const root = document.createElement('div');
    root.id = 'epm-root';
    root.className = 'epm-root';
    root.setAttribute('hidden', '');
    root.setAttribute('role', 'dialog');
    root.setAttribute('aria-modal', 'true');
    root.setAttribute('aria-label', 'Mode Présentation');
    root.innerHTML = `
      <header class="epm-topbar" role="banner">
        <div class="epm-brand">
          <span class="epm-brand-mark" aria-hidden="true">◆</span>
          <span class="epm-brand-text">SIG-FDSU RDC</span>
        </div>
        <div class="epm-meta">
          <strong id="epm-site-name">—</strong>
          <span class="epm-chip" id="epm-program">—</span>
          <span class="epm-chip epm-chip--prio" id="epm-priority">—</span>
          <span class="epm-chip" title="Score">Score <em id="epm-score">—</em></span>
          <span class="epm-chip epm-chip--mute" id="epm-basemap" title="Fond de carte">Carte</span>
        </div>
        <div class="epm-top-actions">
          <button type="button" class="epm-icon-btn" id="epm-btn-help" aria-label="Aide" title="Aide">?</button>
          <button type="button" class="epm-icon-btn epm-icon-btn--exit" id="epm-btn-exit-top" aria-label="Quitter" title="Quitter">✕</button>
        </div>
      </header>

      <div class="epm-kpi-strip" id="epm-kpi-strip" role="toolbar" aria-label="Indicateurs exécutifs"></div>

      <div class="epm-narrative-bar" aria-live="polite">
        <p id="epm-narrative"></p>
        <span id="epm-tour-counter" class="epm-tour-counter"></span>
      </div>

      <aside class="epm-reco-card" id="epm-reco-card" hidden aria-label="Recommandation"></aside>

      <div class="epm-command-dock" id="epm-command-dock" role="toolbar" aria-label="Commandes de présentation">
        <button type="button" class="epm-dock-btn" id="epm-btn-exit" data-epm-cmd="exit" aria-label="Quitter" title="Quitter"><span aria-hidden="true">✕</span></button>
        <button type="button" class="epm-dock-btn" id="epm-btn-fs" data-epm-cmd="fullscreen" aria-label="Plein écran" title="Plein écran"><span aria-hidden="true">⛶</span></button>
        <span class="epm-dock-sep" aria-hidden="true"></span>
        <button type="button" class="epm-dock-btn" id="epm-btn-guided" data-epm-cmd="guided" aria-label="Présentation guidée" title="Présentation guidée"><span aria-hidden="true">▶</span></button>
        <button type="button" class="epm-dock-btn" id="epm-btn-free" data-epm-cmd="free" aria-label="Présentation libre" title="Présentation libre"><span aria-hidden="true">◈</span></button>
        <span class="epm-guided-nav" id="epm-guided-nav">
          <button type="button" class="epm-dock-btn" id="epm-btn-prev" data-epm-cmd="prev" aria-label="Précédent" title="Précédent"><span aria-hidden="true">‹</span></button>
          <button type="button" class="epm-dock-btn" id="epm-btn-pause" data-epm-cmd="pause" aria-label="Pause" title="Pause" aria-pressed="false"><span aria-hidden="true">❚❚</span></button>
          <button type="button" class="epm-dock-btn" id="epm-btn-next" data-epm-cmd="next" aria-label="Suivant" title="Suivant"><span aria-hidden="true">›</span></button>
        </span>
        <span class="epm-dock-sep" aria-hidden="true"></span>
        <button type="button" class="epm-dock-btn" id="epm-btn-reset" data-epm-cmd="reset" aria-label="Réinitialiser" title="Réinitialiser"><span aria-hidden="true">↺</span></button>
        <button type="button" class="epm-dock-btn" id="epm-btn-basemap" data-epm-cmd="basemap" aria-label="Basemap" title="Basemap"><span aria-hidden="true">▣</span></button>
        <button type="button" class="epm-dock-btn" id="epm-btn-labels" data-epm-cmd="labels" aria-label="Masquer les labels permanents" title="Masquer les labels permanents" aria-pressed="true"><span aria-hidden="true">👁</span></button>
        <button type="button" class="epm-dock-btn" id="epm-btn-legend" data-epm-cmd="legend" aria-label="Légende" title="Légende" aria-pressed="false"><span aria-hidden="true">☰</span></button>
        <button type="button" class="epm-dock-btn" id="epm-btn-layers" data-epm-cmd="layers" aria-label="Couches" title="Couches / Relations" aria-pressed="false"><span aria-hidden="true">☷</span></button>
        <button type="button" class="epm-dock-btn" id="epm-btn-detail" data-epm-cmd="detail" aria-label="Détail" title="Panneau détail" aria-pressed="false"><span aria-hidden="true">ℹ</span></button>
        <span class="epm-dock-sep" aria-hidden="true"></span>
        <button type="button" class="epm-dock-btn" id="epm-btn-print" data-epm-cmd="print" aria-label="Imprimer" title="Imprimer"><span aria-hidden="true">⎙</span></button>
        <button type="button" class="epm-dock-btn is-coming" disabled aria-disabled="true" title="Export — À venir" aria-label="Export à venir"><span aria-hidden="true">↓</span></button>
      </div>
    `;

    // Place root as sibling overlay; map stays in sdg-shell under it via CSS
    shell().appendChild(root);

    // Wire dock commands
    const cmds = {
      exit: exitPresentation,
      fullscreen: () => {
        if (document.fullscreenElement) exitBrowserFullscreen();
        else requestBrowserFullscreen().then(queueInvalidate);
      },
      guided: startGuided,
      free: startFree,
      prev: tourPrev,
      next: tourNext,
      pause: tourTogglePause,
      reset: resetView,
      basemap: cycleBasemap,
      labels: () => sdg()?.toggleLabels?.(),
      legend: () => {
        const legend = document.querySelector('#sdg-legend');
        if (!legend) return;
        const show = legend.getAttribute('data-epm-hidden') === 'true' || legend.hasAttribute('data-epm-hidden');
        if (show) {
          legend.removeAttribute('data-epm-hidden');
          legend.classList.add('epm-legend-float');
          document.querySelector('#epm-btn-legend')?.classList.add('is-active');
        } else {
          legend.setAttribute('data-epm-hidden', 'true');
          legend.classList.remove('epm-legend-float');
          document.querySelector('#epm-btn-legend')?.classList.remove('is-active');
        }
      },
      layers: () => togglePanel('relations'),
      detail: () => togglePanel('detail'),
      print: printView,
    };

    root.querySelectorAll('[data-epm-cmd]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const cmd = btn.getAttribute('data-epm-cmd');
        cmds[cmd]?.();
      });
    });
    document.querySelector('#epm-btn-exit-top')?.addEventListener('click', exitPresentation);
    document.querySelector('#epm-btn-help')?.addEventListener('click', showHelp);
    sdg()?.refreshLabels?.();

    // Fermeture panneaux — délégation (survit aux re-renders SDG)
    if (document.body.dataset.epmPanelCloseBound !== 'true') {
      document.body.dataset.epmPanelCloseBound = 'true';
      document.addEventListener('click', (event) => {
        const btn = event.target?.closest?.('[data-epm-close-panel]');
        if (btn && state.active) {
          event.preventDefault();
          event.stopPropagation();
          const which = btn.getAttribute('data-epm-close-panel') || 'detail';
          closePanel(which === 'relations' ? 'relations' : 'detail');
          return;
        }
        // Sélection carte → ouvrir détail
        if (state.active && event.target?.closest?.('.sdg-marker, .leaflet-marker-icon, path.sdg-edge, .leaflet-interactive')) {
          global.setTimeout(() => {
            if (sdg()?.state?.selected) panToSelection(true);
          }, 40);
        }
      });
    }

    // Bouton ✕ permanent sur panneau Relations
    const filters = document.querySelector('#sdg-filters-panel');
    if (filters && !filters.querySelector('[data-epm-close-panel="relations"]')) {
      const close = document.createElement('button');
      close.type = 'button';
      close.className = 'epm-panel-close';
      close.setAttribute('data-epm-close-panel', 'relations');
      close.setAttribute('aria-label', 'Fermer le panneau relations');
      close.title = 'Fermer le panneau relations';
      close.textContent = '✕';
      filters.prepend(close);
    }
  }

  function bindGlobalKeys() {
    if (document.body.dataset.epmKeysBound === 'true') return;
    document.body.dataset.epmKeysBound = 'true';
    document.addEventListener('keydown', (event) => {
      if (!state.active) return;
      if (event.key === 'Escape') {
        event.preventDefault();
        event.stopPropagation();
        if (typeof event.stopImmediatePropagation === 'function') event.stopImmediatePropagation();
        const relationsOpen = document.querySelector('#sdg-filters-panel')
          && !document.querySelector('#sdg-filters-panel')?.classList.contains('epm-panel-hidden');
        const detailOpen = document.querySelector('#sdg-detail')
          && !document.querySelector('#sdg-detail')?.classList.contains('epm-panel-hidden');
        if (relationsOpen || detailOpen) {
          closePanel('all');
          return;
        }
        if (document.fullscreenElement || document.webkitFullscreenElement) {
          exitBrowserFullscreen();
          return;
        }
        exitPresentation();
        return;
      }
      if (state.mode === 'guided' && !state.tourPaused) {
        if (event.key === 'ArrowRight') {
          event.preventDefault();
          tourNext();
        } else if (event.key === 'ArrowLeft') {
          event.preventDefault();
          tourPrev();
        }
      }
    });
    document.addEventListener('fullscreenchange', () => {
      state.fullscreenActive = Boolean(document.fullscreenElement);
      queueInvalidate();
    });
  }

  function attach() {
    if (!shell()) return;
    const token = ++state.attachToken;
    global.setTimeout(() => {
      if (token !== state.attachToken) return;
      injectChrome();
      patchPopups();
      if (!state.selectionWatcher) {
        state.selectionWatcher = global.setInterval(() => {
          if (!shell()) return;
          panToSelection();
          if (state.active) patchPopups();
        }, 400);
      }
      state.attached = true;
    }, 60);
  }

  function setup() {
    bindGlobalKeys();
    const observer = new MutationObserver(() => {
      if (document.querySelector('#sdg-shell') && !document.querySelector('#epm-enter-btn')) {
        attach();
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
    if (shell()) attach();
  }

  global.SigDecisionCartographyExperience = {
    version: VERSION,
    setup,
    attach,
    enterDemoMode: enterPresentation,
    enterPresentation,
    exitDemoMode: exitPresentation,
    exitPresentation,
    isDemoActive: () => state.active,
    isActive: () => state.active,
    GUIDED_STEPS,
  };

  setup();
})(typeof window !== 'undefined' ? window : globalThis);
