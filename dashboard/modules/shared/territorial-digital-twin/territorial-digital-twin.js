/**
 * Territorial Digital Twin — mode du Decision Workspace.
 * Charge les sections en parallèle (résilient), réutilise TerritorialSummary pour la carte.
 */
(function initTerritorialDigitalTwin(global) {
  const API_BASE = `${global.location.protocol}//${global.location.hostname}:8001`;
  const SECTION_KEYS = [
    'summary',
    'connectivity',
    'public_services',
    'accessibility',
    'energy',
    'economy',
    'programs',
    'decision',
    'quality',
    'timeline',
  ];
  const SECTION_LABELS = {
    summary: 'Résumé exécutif',
    connectivity: 'Connectivité',
    public_services: 'Services publics',
    accessibility: 'Transport et accessibilité',
    energy: 'Énergie',
    economy: 'Économie',
    programs: 'Programmes FDSU',
    decision: 'Priorité et justification',
    quality: 'Qualité des données',
    timeline: 'Historique',
  };
  const ENDPOINT_MAP = {
    summary: 'summary',
    connectivity: 'connectivity',
    public_services: 'services',
    accessibility: 'accessibility',
    energy: null,
    economy: null,
    programs: 'programs',
    decision: 'decision',
    quality: 'quality',
    timeline: 'timeline',
  };

  const state = {
    active: false,
    entityType: null,
    entityId: null,
    abort: null,
    requestSeq: 0,
    twin: null,
    sections: {},
    sectionStatus: {},
    mapApi: null,
    returnHash: 'decision-view',
  };

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatValue(value) {
    if (value == null || value === '') return '—';
    if (typeof value === 'number' && Number.isFinite(value)) {
      return new Intl.NumberFormat('fr-FR').format(value);
    }
    if (typeof value === 'object') {
      if (value.display != null) return String(value.display);
      if (value.value != null) return formatValue(value.value);
      if (value.label != null) return String(value.label);
      return '—';
    }
    return String(value);
  }

  function parseHash() {
    const hash = (global.location.hash || '').replace(/^#/, '').split('?')[0];
    if (!hash.startsWith('territorial-twin/')) return null;
    const parts = hash.split('/').filter(Boolean);
    if (parts.length < 3) return null;
    return { entityType: parts[1], entityId: decodeURIComponent(parts.slice(2).join('/')) };
  }

  function fetchJson(path, signal) {
    return fetch(`${API_BASE}${path}`, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      signal,
    }).then((response) => {
      if (!response.ok) {
        const err = new Error(path);
        err.status = response.status;
        throw err;
      }
      return response.json();
    });
  }

  function ensureRoot() {
    const panel = document.querySelector('#decision-detail-panel');
    if (!panel) return null;
    let root = panel.querySelector('#tdt-root');
    if (!root) {
      root = document.createElement('div');
      root.id = 'tdt-root';
      root.className = 'tdt-root';
      root.setAttribute('data-tdt', '1.0');
      root.hidden = true;
      const topbar = panel.querySelector('.decision-detail-topbar');
      if (topbar && topbar.nextSibling) panel.insertBefore(root, topbar.nextSibling);
      else panel.prepend(root);
    }
    return root;
  }

  function setWorkspaceMode(active) {
    const panel = document.querySelector('#decision-detail-panel');
    if (!panel) return;
    panel.classList.toggle('is-territorial-twin', active);
    document.body.classList.toggle('territorial-twin-open', active);
    const root = ensureRoot();
    if (root) root.hidden = !active;
    panel.querySelectorAll(
      '.decision-detail-header-card, .decision-detail-secondary, .decision-detail-filters, .decision-detail-grid, .decision-detail-list-card, .decision-detail-explain-card, #decision-workspace-chrome'
    ).forEach((el) => {
      if (el) el.hidden = active;
    });
  }

  function statusBadge(status) {
    const s = status || 'unavailable';
    const labels = {
      success: 'Disponible',
      partial: 'Partiel',
      unavailable: 'Non disponible',
      error: 'Erreur',
      loading: 'Chargement…',
    };
    return `<span class="tdt-badge tdt-badge-${escapeHtml(s)}">${escapeHtml(labels[s] || s)}</span>`;
  }

  function renderShell() {
    const root = ensureRoot();
    if (!root) return;
    root.innerHTML = `
      <header class="tdt-header" aria-label="En-tête territorial">
        <div class="tdt-header-copy">
          <p class="tdt-kicker">Jumeau Numérique Territorial</p>
          <h2 id="tdt-title">Profil territorial</h2>
          <p id="tdt-subtitle" class="tdt-subtitle">Chargement de l’identité…</p>
        </div>
        <div class="tdt-header-actions">
          <button type="button" class="secondary-button" id="tdt-back-btn">← Retour</button>
          <button type="button" class="primary-button" id="tdt-open-full-btn" hidden>Analyse complète</button>
        </div>
      </header>
      <nav class="tdt-breadcrumb" id="tdt-breadcrumb" aria-label="Fil hiérarchique"></nav>
      <p class="tdt-status" id="tdt-status" aria-live="polite">Chargement progressif…</p>
      <div class="tdt-layout">
        <div class="tdt-main">
          <section class="tdt-section" data-tdt-section="summary">
            <div class="tdt-section-head"><h3>Résumé exécutif</h3><span data-tdt-status></span></div>
            <div class="tdt-section-body" data-tdt-body>Chargement…</div>
          </section>
          <section class="tdt-section" data-tdt-section="connectivity">
            <div class="tdt-section-head"><h3>Connectivité</h3><span data-tdt-status></span></div>
            <div class="tdt-section-body" data-tdt-body>Chargement…</div>
          </section>
          <section class="tdt-section" data-tdt-section="public_services">
            <div class="tdt-section-head"><h3>Services publics</h3><span data-tdt-status></span></div>
            <div class="tdt-section-body" data-tdt-body>Chargement…</div>
          </section>
          <section class="tdt-section" data-tdt-section="accessibility">
            <div class="tdt-section-head"><h3>Transport et accessibilité</h3><span data-tdt-status></span></div>
            <div class="tdt-section-body" data-tdt-body>Chargement…</div>
          </section>
          <section class="tdt-section" data-tdt-section="energy">
            <div class="tdt-section-head"><h3>Énergie</h3><span data-tdt-status></span></div>
            <div class="tdt-section-body" data-tdt-body>Chargement…</div>
          </section>
          <section class="tdt-section" data-tdt-section="economy">
            <div class="tdt-section-head"><h3>Économie</h3><span data-tdt-status></span></div>
            <div class="tdt-section-body" data-tdt-body>Chargement…</div>
          </section>
          <section class="tdt-section" data-tdt-section="programs">
            <div class="tdt-section-head"><h3>Programmes FDSU</h3><span data-tdt-status></span></div>
            <div class="tdt-section-body" data-tdt-body>Chargement…</div>
          </section>
          <section class="tdt-section" data-tdt-section="decision">
            <div class="tdt-section-head"><h3>Priorité et recommandations</h3><span data-tdt-status></span></div>
            <div class="tdt-section-body" data-tdt-body>Chargement…</div>
          </section>
          <section class="tdt-section" data-tdt-section="quality">
            <div class="tdt-section-head"><h3>Qualité des données</h3><span data-tdt-status></span></div>
            <div class="tdt-section-body" data-tdt-body>Chargement…</div>
          </section>
          <section class="tdt-section" data-tdt-section="timeline">
            <div class="tdt-section-head"><h3>Historique</h3><span data-tdt-status></span></div>
            <div class="tdt-section-body" data-tdt-body>Chargement…</div>
          </section>
          <section class="tdt-section" data-tdt-section="sources">
            <div class="tdt-section-head"><h3>Sources</h3></div>
            <div class="tdt-section-body" id="tdt-sources-body">—</div>
          </section>
        </div>
        <aside class="tdt-side">
          <div class="tdt-kpis" id="tdt-kpis" aria-label="KPI territoriaux"></div>
          <div class="tdt-map-host" id="tdt-map-host" aria-label="Carte territoriale"></div>
        </aside>
      </div>
    `;
    root.querySelector('#tdt-back-btn')?.addEventListener('click', () => {
      close();
      global.location.hash = state.returnHash || 'decision-view';
    });
    root.querySelector('#tdt-open-full-btn')?.addEventListener('click', () => {
      const entity = state.twin?.entity;
      if (entity?.entity_type === 'territoire' && entity?.entity_id) {
        global.location.hash = `territorial-intelligence/${encodeURIComponent(entity.entity_id)}`;
      }
    });
  }

  function renderBreadcrumb(hierarchy) {
    const host = document.querySelector('#tdt-breadcrumb');
    if (!host) return;
    const items = Array.isArray(hierarchy) ? hierarchy : [];
    host.innerHTML = items.map((step, index) => {
      const isLast = index === items.length - 1;
      const type = step.entity_type || 'rdc';
      const id = step.entity_id || step.nom || '';
      return `
        <button type="button" class="tdt-crumb${isLast ? ' is-current' : ''}"
          data-tdt-type="${escapeHtml(type)}" data-tdt-id="${escapeHtml(id)}"
          ${type === 'rdc' || isLast ? 'disabled' : ''}>
          ${escapeHtml(step.nom || step.niveau_administratif || type)}
        </button>
        ${isLast ? '' : '<span aria-hidden="true">›</span>'}
      `;
    }).join('');
    host.querySelectorAll('button[data-tdt-type]:not([disabled])').forEach((btn) => {
      btn.addEventListener('click', () => {
        open({
          entityType: btn.getAttribute('data-tdt-type'),
          entityId: btn.getAttribute('data-tdt-id'),
          returnHash: state.returnHash,
        });
      });
    });
  }

  function setSectionStatus(key, status) {
    state.sectionStatus[key] = status;
    const section = document.querySelector(`[data-tdt-section="${key}"]`);
    if (!section) return;
    const badge = section.querySelector('[data-tdt-status]');
    if (badge) badge.innerHTML = statusBadge(status);
    section.dataset.status = status;
  }

  function unavailableHtml(note) {
    return `
      <div class="tdt-empty">
        <strong>Données insuffisantes</strong>
        <p>${escapeHtml(note || 'Cette section n’est pas encore alimentée.')}</p>
      </div>
    `;
  }

  function metaLine(section) {
    const meta = section?._section || {};
    const parts = [
      meta.source ? `Source : ${meta.source}` : null,
      meta.updated_at ? `MAJ : ${String(meta.updated_at).slice(0, 19)}` : null,
      meta.status ? `Statut : ${meta.status}` : null,
    ].filter(Boolean);
    return parts.length ? `<p class="tdt-meta">${escapeHtml(parts.join(' · '))}</p>` : '';
  }

  function renderKpis(twin) {
    const host = document.querySelector('#tdt-kpis');
    if (!host) return;
    const summary = twin?.summary || {};
    const decision = twin?.decision || {};
    const access = twin?.accessibility || {};
    const cards = [
      { label: 'Population', value: formatValue(summary.population) },
      { label: 'Priorité', value: formatValue(decision.priority_metric || decision.priority || decision.value) },
      { label: 'Accessibilité', value: formatValue(access.avg_score) },
      { label: 'Statut global', value: twin?._meta?.overall_status || '—' },
    ];
    host.innerHTML = cards.map((c) => `
      <article class="tdt-kpi">
        <span>${escapeHtml(c.label)}</span>
        <strong>${escapeHtml(c.value)}</strong>
      </article>
    `).join('');
  }

  function renderSectionBody(key, payload) {
    const section = document.querySelector(`[data-tdt-section="${key}"]`);
    if (!section) return;
    const body = section.querySelector('[data-tdt-body]');
    if (!body) return;
    const data = payload?.[key] || payload;
    const status = data?._section?.status || state.sectionStatus[key] || 'unavailable';
    setSectionStatus(key, status);

    if (status === 'unavailable' || status === 'error') {
      body.innerHTML = unavailableHtml(data?._section?.note || data?.display) + metaLine(data);
      return;
    }

    if (key === 'summary') {
      const fields = Array.isArray(data.fields)
        ? data.fields.map((f) => `<li><span>${escapeHtml(f.label)}</span><strong>${escapeHtml(formatValue(f.value))}</strong></li>`).join('')
        : '';
      body.innerHTML = `
        <p class="tdt-lead">${escapeHtml(data.headline || 'Résumé territorial')}</p>
        ${fields ? `<ul class="tdt-kv">${fields}</ul>` : `
          <ul class="tdt-kv">
            <li><span>Population</span><strong>${escapeHtml(formatValue(data.population))}</strong></li>
            <li><span>Superficie</span><strong>${escapeHtml(formatValue(data.area_km2))}</strong></li>
            <li><span>Densité</span><strong>${escapeHtml(formatValue(data.density))}</strong></li>
            <li><span>Confiance</span><strong>${escapeHtml(formatValue(data.confidence_level))}</strong></li>
          </ul>`}
        ${data.note ? `<p class="tdt-note">${escapeHtml(data.note)}</p>` : ''}
        ${metaLine(data)}
      `;
      return;
    }

    if (key === 'connectivity') {
      const demo = data.demo ? '<p class="tdt-demo">⚠ Données DEMO signalées</p>' : '';
      body.innerHTML = `
        ${demo}
        <ul class="tdt-kv">
          <li><span>Population non couverte</span><strong>${escapeHtml(formatValue(data.population_uncovered))}</strong></li>
          <li><span>Population couverte</span><strong>${escapeHtml(formatValue(data.population_covered))}</strong></li>
          <li><span>Localités non couvertes</span><strong>${escapeHtml(formatValue(data.localities_uncovered))}</strong></li>
          <li><span>NDCI</span><strong>${escapeHtml(formatValue(data.ndci))}</strong></li>
        </ul>
        ${metaLine(data)}
      `;
      return;
    }

    if (key === 'public_services') {
      const health = data.health || {};
      body.innerHTML = `
        <ul class="tdt-kv">
          <li><span>Établissements de santé</span><strong>${escapeHtml(formatValue(health.count))}</strong></li>
          <li><span>Éducation</span><strong>${escapeHtml(formatValue(data.education))}</strong></li>
          <li><span>Administration</span><strong>${escapeHtml(formatValue(data.administration))}</strong></li>
          <li><span>Marchés</span><strong>${escapeHtml(formatValue(data.markets))}</strong></li>
        </ul>
        ${metaLine(data)}
      `;
      return;
    }

    if (key === 'accessibility') {
      body.innerHTML = `
        <ul class="tdt-kv">
          <li><span>Score moyen</span><strong>${escapeHtml(formatValue(data.avg_score))}</strong></li>
          <li><span>Sites scorés</span><strong>${escapeHtml(formatValue(data.sites_scored))}</strong></li>
          <li><span>Route proche (échantillon)</span><strong>${escapeHtml(formatValue(data.sample_nearest_road))}</strong></li>
        </ul>
        <p class="tdt-note">${escapeHtml(data.sample_justification || data._section?.note || '')}</p>
        ${metaLine(data)}
      `;
      return;
    }

    if (key === 'programs') {
      const sites = data.sites_sample || [];
      body.innerHTML = `
        <p class="tdt-note">${escapeHtml(data.note_ccn || 'Site FDSU ≠ CCN')}</p>
        <ul class="tdt-kv">
          <li><span>Sites échantillon</span><strong>${escapeHtml(String(sites.length))}</strong></li>
          <li><span>Sites FDSU</span><strong>${escapeHtml(formatValue(data.sites_fdsu))}</strong></li>
          <li><span>Sites prioritaires</span><strong>${escapeHtml(formatValue(data.sites_priority))}</strong></li>
          <li><span>CCN</span><strong>${escapeHtml(formatValue(data.ccn))}</strong></li>
        </ul>
        ${metaLine(data)}
      `;
      return;
    }

    if (key === 'decision') {
      const recs = data.recommendations;
      let recoHtml = '';
      if (recs && typeof recs === 'object') {
        const list = recs.recommendations || recs.items || [];
        if (Array.isArray(list) && list.length) {
          recoHtml = `<ul class="tdt-list">${list.slice(0, 6).map((r) => `<li>${escapeHtml(typeof r === 'string' ? r : (r.label || r.title || r.text || JSON.stringify(r)))}</li>`).join('')}</ul>`;
        } else {
          recoHtml = `<p class="tdt-note">${escapeHtml(formatValue(recs))}</p>`;
        }
      }
      body.innerHTML = `
        <ul class="tdt-kv">
          <li><span>Priorité</span><strong>${escapeHtml(formatValue(data.priority || data.priority_metric || data.class_label))}</strong></li>
          <li><span>Valeur</span><strong>${escapeHtml(formatValue(data.value))}</strong></li>
        </ul>
        <h4>Recommandations</h4>
        ${recoHtml || unavailableHtml('Recommandations non disponibles pour cette entité')}
        ${metaLine(data)}
      `;
      return;
    }

    if (key === 'quality') {
      const rows = data.ndf_registries || [];
      body.innerHTML = `
        <p class="tdt-note">${escapeHtml(data.rule || '')}</p>
        <ul class="tdt-list">${rows.slice(0, 10).map((r) => `
          <li><strong>${escapeHtml(r.registry_id)}</strong> — ${escapeHtml(r.status || '—')}
            (mesuré ${escapeHtml(formatValue(r.measured))} / insuffisant ${escapeHtml(formatValue(r.insufficient))})</li>
        `).join('')}</ul>
        ${metaLine(data)}
      `;
      return;
    }

    if (key === 'timeline') {
      const events = Array.isArray(payload?.timeline) ? payload.timeline
        : (Array.isArray(data?.events) ? data.events : (Array.isArray(data) ? data : []));
      if (!events.length) {
        body.innerHTML = unavailableHtml('Aucun événement timeline pour l’instant') + metaLine(data);
        return;
      }
      body.innerHTML = `
        <ol class="tdt-timeline">${events.map((e) => `
          <li>
            <time>${escapeHtml(String(e.at || '').slice(0, 19))}</time>
            <strong>${escapeHtml(e.label || e.kind || 'Événement')}</strong>
            <span>${escapeHtml(e.source || '')}</span>
          </li>
        `).join('')}</ol>
        ${metaLine(typeof data === 'object' && !Array.isArray(data) ? data : {})}
      `;
      return;
    }

    if (key === 'energy' || key === 'economy') {
      body.innerHTML = unavailableHtml(data?._section?.note || data?.display || 'Données non encore intégrées') + metaLine(data);
      return;
    }

    body.innerHTML = `<pre class="tdt-json">${escapeHtml(JSON.stringify(data, null, 2).slice(0, 1200))}</pre>${metaLine(data)}`;
  }

  function mountMap(entity, hierarchy) {
    const host = document.querySelector('#tdt-map-host');
    if (!host || !global.TerritorialSummary?.mount) {
      if (host) host.innerHTML = '<p class="tdt-empty">Carte indisponible</p>';
      return;
    }
    if (state.mapApi?.destroy) {
      try { state.mapApi.destroy(); } catch (_e) { /* */ }
      state.mapApi = null;
    }
    const level = entity?.entity_type === 'province' ? 'province'
      : entity?.entity_type === 'territoire' ? 'territoire'
        : 'province';
    const parentId = entity?.entity_type === 'territoire'
      ? (entity.province || hierarchy?.find((h) => h.entity_type === 'province')?.nom)
      : null;
    global.TerritorialSummary.mount(host, {
      metric: global.TerritorialContext?.get()?.metric || 'priority',
      level: entity?.entity_type === 'territoire' ? 'territoire' : 'province',
      parentId: parentId || null,
      preserveContext: true,
      showLegend: true,
      showKpis: false,
      allowDrilldown: true,
      onSelectionChange: (sel) => {
        if (!sel) return;
        const type = sel.level || sel.entity_type || level;
        const id = sel.id || sel.entity_id || sel.name;
        if (type && id) open({ entityType: type, entityId: id, returnHash: state.returnHash });
      },
    }).then((api) => {
      state.mapApi = api;
    }).catch(() => {
      host.innerHTML = '<p class="tdt-empty">Carte TST indisponible</p>';
    });
  }

  function updateStatusBar() {
    const el = document.querySelector('#tdt-status');
    if (!el) return;
    const statuses = Object.values(state.sectionStatus);
    const done = statuses.filter((s) => s && s !== 'loading').length;
    const partial = statuses.filter((s) => s === 'partial' || s === 'unavailable').length;
    el.textContent = `${done}/${SECTION_KEYS.length} sections · ${partial} partielles/indisponibles · ${state.twin?._meta?.overall_status || '…'}`;
  }

  function applyEntityHeader(entity) {
    const title = document.querySelector('#tdt-title');
    const subtitle = document.querySelector('#tdt-subtitle');
    if (title) title.textContent = entity?.nom || 'Profil territorial';
    if (subtitle) {
      subtitle.textContent = [
        entity?.niveau_administratif,
        entity?.code_officiel ? `Code ${entity.code_officiel}` : null,
        entity?.source_administrative ? `Source ${entity.source_administrative}` : null,
      ].filter(Boolean).join(' · ');
    }
    const fullBtn = document.querySelector('#tdt-open-full-btn');
    if (fullBtn) fullBtn.hidden = entity?.entity_type !== 'territoire';
  }

  function loadProgressive(entityType, entityId) {
    if (state.abort) state.abort.abort();
    state.abort = new AbortController();
    const signal = state.abort.signal;
    const seq = ++state.requestSeq;
    const base = `/api/territorial-digital-twin/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}`;

    SECTION_KEYS.forEach((key) => setSectionStatus(key, 'loading'));

    // Sections sans endpoint dédié : état transparent immédiat (pas d’écran « Chargement… » bloqué)
    renderSectionBody('energy', {
      display: 'Données insuffisantes',
      _section: {
        status: 'unavailable',
        note: 'Données non encore intégrées — référentiel Énergie (NDF planned)',
        source: 'ndf/energy',
      },
    });
    renderSectionBody('economy', {
      display: 'Données insuffisantes',
      _section: {
        status: 'unavailable',
        note: 'Données économiques non encore intégrées',
        source: 'ndf/economy',
      },
    });

    // Identité + résumé rapide via endpoint principal (composition résiliente)
    fetchJson(base, signal).then((twin) => {
      if (seq !== state.requestSeq) return;
      state.twin = twin;
      applyEntityHeader(twin.entity);
      renderBreadcrumb(twin.hierarchy);
      Object.entries(twin.section_status || {}).forEach(([k, v]) => setSectionStatus(k, v));
      SECTION_KEYS.forEach((key) => {
        if (key === 'timeline') {
          renderSectionBody(key, { timeline: twin.timeline, _section: { status: twin.section_status?.timeline } });
        } else {
          renderSectionBody(key, twin[key]);
        }
      });
      const sources = document.querySelector('#tdt-sources-body');
      if (sources) {
        sources.innerHTML = (twin.sources || []).length
          ? `<ul class="tdt-list">${twin.sources.map((s) => `<li>${escapeHtml(s)}</li>`).join('')}</ul>`
          : unavailableHtml('Sources non listées');
      }
      renderKpis(twin);
      mountMap(twin.entity, twin.hierarchy);
      updateStatusBar();
      if (global.TerritorialContext?.select && twin.entity) {
        global.TerritorialContext.select({
          level: twin.entity.entity_type,
          id: twin.entity.entity_id,
          name: twin.entity.nom,
          province: twin.entity.province,
        });
      }
    }).catch((err) => {
      if (signal.aborted || seq !== state.requestSeq) return;
      const status = document.querySelector('#tdt-status');
      if (status) status.textContent = err?.status === 404
        ? 'Entité territoriale introuvable.'
        : 'Impossible de charger le jumeau territorial.';
      SECTION_KEYS.forEach((key) => {
        setSectionStatus(key, 'error');
        renderSectionBody(key, { _section: { status: 'error', note: 'Erreur de chargement' } });
      });
    });

    // Rafraîchissement section-par-section (cache / annulation)
    SECTION_KEYS.forEach((key) => {
      const ep = ENDPOINT_MAP[key];
      if (!ep) return;
      fetchJson(`${base}/${ep}`, signal).then((payload) => {
        if (seq !== state.requestSeq) return;
        state.sections[key] = payload;
        const st = payload.section_status?.[key] || payload[key]?._section?.status || 'success';
        setSectionStatus(key, st);
        renderSectionBody(key, payload);
        updateStatusBar();
      }).catch(() => {
        /* composition principale déjà affichée */
      });
    });
  }

  function open(options = {}) {
    const fromHash = parseHash();
    const entityType = options.entityType || fromHash?.entityType;
    const entityId = options.entityId || fromHash?.entityId;
    if (!entityType || !entityId) return;

    state.returnHash = options.returnHash
      || (global.DecisionWorkspace?.state?.returnHash)
      || 'decision-view';
    state.entityType = entityType;
    state.entityId = entityId;
    state.active = true;

    if (global.DecisionWorkspace?.attach) {
      global.DecisionWorkspace.attach({
        returnHash: state.returnHash,
        trail: [{ level: 'rdc', id: 'rdc', label: 'RDC' }],
      });
    }

    const desired = `territorial-twin/${entityType}/${encodeURIComponent(entityId)}`;
    if ((global.location.hash || '').replace(/^#/, '') !== desired) {
      global.location.hash = desired;
    }

    setWorkspaceMode(true);
    renderShell();
    loadProgressive(entityType, entityId);
  }

  function close() {
    state.active = false;
    if (state.abort) state.abort.abort();
    if (state.mapApi?.destroy) {
      try { state.mapApi.destroy(); } catch (_e) { /* */ }
      state.mapApi = null;
    }
    setWorkspaceMode(false);
  }

  function syncFromHash() {
    const parsed = parseHash();
    if (!parsed) {
      if (state.active) close();
      return false;
    }
    open({ entityType: parsed.entityType, entityId: parsed.entityId, returnHash: state.returnHash });
    return true;
  }

  function initialize() {
    if (parseHash()) syncFromHash();
  }

  global.TerritorialDigitalTwin = {
    version: '1.0.0',
    open,
    close,
    syncFromHash,
    parseHash,
    initialize,
    state,
    SECTION_LABELS,
  };
})(typeof window !== 'undefined' ? window : globalThis);
