(function initDecisionCenterModule(global) {
  const BUSINESS_DATA_BASE = '/business/';
  const PROGRAMS_DATA_BASE = '/programs/';
  const FDSU_PROGRAMS_PATH = `${BUSINESS_DATA_BASE}fdsu_programs.json`;
  const SITES_40_DATA_PATH = `${PROGRAMS_DATA_BASE}sites_40/sites_40.json`;

  const DECISION_CENTER_TABS = [
    { id: 'vue-nationale', label: 'Vue nationale' },
    { id: 'priorisation', label: 'Priorisation' },
    { id: 'referentiels-sectoriels', label: 'Référentiels sectoriels' },
    { id: 'analyse-multicritere', label: 'Analyse multicritère' },
    { id: 'simulations', label: 'Simulations' },
    { id: 'tableaux-de-bord', label: 'Tableaux de bord' },
    { id: 'rapports', label: 'Rapports' },
  ];

  const NATIONAL_PANEL_PENDING_MESSAGE = "Données en cours d'intégration";

  const NATIONAL_SYNTHESIS_KPI_BINDINGS = [
    { key: 'sites_fdsu', elementId: 'decision-kpi-sites-fdsu', synthesisKey: 'sites_fdsu' },
    { key: 'sites_priority', elementId: 'decision-kpi-sites-priority', synthesisKey: 'sites_priority' },
    { key: 'sites_critical', elementId: 'decision-kpi-sites-critical', synthesisKey: 'sites_critical' },
    { key: 'sites_high', elementId: 'decision-kpi-sites-high', synthesisKey: 'sites_high' },
    { key: 'referentials_active', elementId: 'decision-kpi-referentials-active', synthesisKey: 'referentials_active' },
    { key: 'referentials_planned', elementId: 'decision-kpi-referentials-planned', synthesisKey: 'referentials_planned' },
  ];

  const NATIONAL_OPERATIONAL_KPI_BINDINGS = [
    { key: 'sites_40', elementId: 'decision-kpi-sites-40' },
    { key: 'sites_300', elementId: 'decision-kpi-sites-300' },
    { key: 'sites_scored', elementId: 'decision-kpi-sites-scored' },
    { key: 'referentials_in_progress', elementId: 'decision-kpi-referentials-in-progress' },
    { key: 'telecom_objects', elementId: 'decision-kpi-telecom-objects' },
    { key: 'provinces', elementId: 'decision-kpi-provinces' },
    { key: 'territoires', elementId: 'decision-kpi-territoires' },
    { key: 'localites', elementId: 'decision-kpi-localites' },
  ];

  const NATIONAL_PENDING_KPI_BINDINGS = [
    { key: 'population_covered', elementId: 'decision-kpi-covered-population' },
    { key: 'population_uncovered', elementId: 'decision-kpi-uncovered-population' },
    { key: 'planned_ccn', elementId: 'decision-kpi-planned-ccn' },
    { key: 'estimated_investment', elementId: 'decision-kpi-investment' },
  ];

  const decisionCenterState = {
    initialized: false,
    activeTab: 'vue-nationale',
    map: null,
    layers: {},
    mapInitialized: false,
    resizeObserver: null,
    nationalPanelLoaded: false,
    nationalPanelLoading: false,
    programsLoaded: false,
    programsLoading: false,
    sites40Loaded: false,
    sites40Loading: false,
    sites300Loaded: false,
    sites300Loading: false,
    telecomLoaded: false,
    telecomLoading: false,
    telecomLoadingPromise: null,
    spatialLoaded: false,
    spatialLoading: false,
    spatialLoadingPromise: null,
    decisionEngineLoaded: false,
    decisionEngineLoading: false,
    decisionEngineFilter: '',
    decisionEngineSites: [],
    decisionEngineMap: null,
    decisionEngineMarkers: null,
    decisionEngineSelectedSiteId: null,
    sectorialLoaded: false,
    sectorialLoading: false,
    healthMap: null,
    programStatusCatalog: null,
    priorityMatrixLoader: null,
  };

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatNationalKpiNumber(value) {
    if (value == null || Number.isNaN(Number(value))) {
      return NATIONAL_PANEL_PENDING_MESSAGE;
    }
    return Number(value).toLocaleString('fr-FR');
  }

  function setNationalKpiElement(elementId, displayValue, isPending) {
    const element = document.getElementById(elementId);
    if (!element) return;
    element.textContent = displayValue;
    element.classList.toggle('is-pending-value', Boolean(isPending));
    const card = element.closest('.decision-center-kpi-card');
    if (card) {
      card.classList.toggle('is-pending', Boolean(isPending));
    }
  }

  function resolveKpiDisplay(kpi) {
    if (!kpi || kpi.available === false || kpi.value == null) {
      return {
        text: kpi?.display || NATIONAL_PANEL_PENDING_MESSAGE,
        pending: true,
      };
    }
    return {
      text: formatNationalKpiNumber(kpi.value),
      pending: false,
    };
  }

  function renderNationalPanelKpis(payload) {
    const kpis = payload?.kpis || {};
    const synthesis = payload?.synthesis || {};

    NATIONAL_SYNTHESIS_KPI_BINDINGS.forEach((binding) => {
      const fromSynthesis = synthesis[binding.synthesisKey];
      if (fromSynthesis != null) {
        setNationalKpiElement(binding.elementId, formatNationalKpiNumber(fromSynthesis), false);
        return;
      }
      const resolved = resolveKpiDisplay(kpis[binding.key]);
      setNationalKpiElement(binding.elementId, resolved.text, resolved.pending);
    });

    NATIONAL_OPERATIONAL_KPI_BINDINGS.forEach((binding) => {
      const resolved = resolveKpiDisplay(kpis[binding.key]);
      setNationalKpiElement(binding.elementId, resolved.text, resolved.pending);
    });

    NATIONAL_PENDING_KPI_BINDINGS.forEach((binding) => {
      const resolved = resolveKpiDisplay(kpis[binding.key]);
      setNationalKpiElement(binding.elementId, resolved.text || NATIONAL_PANEL_PENDING_MESSAGE, true);
    });
  }

  function renderNationalPanelUnavailable(message) {
    const pendingMessage = message || NATIONAL_PANEL_PENDING_MESSAGE;
    [...NATIONAL_SYNTHESIS_KPI_BINDINGS, ...NATIONAL_OPERATIONAL_KPI_BINDINGS].forEach((binding) => {
      setNationalKpiElement(binding.elementId, pendingMessage, true);
    });
    NATIONAL_PENDING_KPI_BINDINGS.forEach((binding) => {
      setNationalKpiElement(binding.elementId, NATIONAL_PANEL_PENDING_MESSAGE, true);
    });
  }

  function loadNationalPanel(forceReload) {
    if (decisionCenterState.nationalPanelLoading) return;
    if (decisionCenterState.nationalPanelLoaded && !forceReload) return;

    const shared = getShared();
    const canUseDb = typeof shared.canUseProgramDbData === 'function' && shared.canUseProgramDbData();
    if (!canUseDb) {
      renderNationalPanelUnavailable(NATIONAL_PANEL_PENDING_MESSAGE);
      decisionCenterState.nationalPanelLoaded = true;
      return;
    }

    decisionCenterState.nationalPanelLoading = true;
    const fetchPanel = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/decision/national-panel')
      : global.fetch('/api/decision/national-panel').then((response) => (response.ok ? response.json() : null));

    Promise.resolve(fetchPanel)
      .then((payload) => {
        if (!payload || !payload.kpis) {
          renderNationalPanelUnavailable(NATIONAL_PANEL_PENDING_MESSAGE);
          return;
        }
        renderNationalPanelKpis(payload);
        decisionCenterState.nationalPanelLoaded = true;
      })
      .catch(() => {
        renderNationalPanelUnavailable(NATIONAL_PANEL_PENDING_MESSAGE);
      })
      .finally(() => {
        decisionCenterState.nationalPanelLoading = false;
      });
  }

  function fetchProgramJson(relativePath) {
    const shared = getShared();
    if (typeof shared?.fetchJson === 'function' && typeof shared?.canUseProgramDbData === 'function' && shared.canUseProgramDbData()) {
      const apiPathMap = {
        'sites_40/sites_40.json': '/api/programs/sites40?format=panel',
        'sites_300/sites_300.json': '/api/programs/sites300?format=panel',
      };
      const apiPath = apiPathMap[relativePath];
      if (apiPath) {
        return shared.fetchJson(apiPath).then((payload) => {
          if (!payload) {
            throw new Error(`Impossible de charger ${apiPath}`);
          }
          return payload;
        });
      }
    }
    const path = `${PROGRAMS_DATA_BASE}${relativePath}`;
    return global.fetch(path).then((response) => {
      if (!response.ok) {
        throw new Error(`Impossible de charger ${path}`);
      }
      return response.json();
    });
  }

  function countByField(items, fieldName) {
    return asArray(items).reduce((acc, item) => {
      const key = String(item?.[fieldName] || 'Non renseigné').trim() || 'Non renseigné';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
  }

  function renderDistributionList(title, counts) {
    const entries = Object.entries(counts).sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0], 'fr'));
    if (!entries.length) {
      return `<div class="decision-center-sites-40-block"><h4>${escapeHtml(title)}</h4><p class="decision-center-program-loading">Aucune donnée.</p></div>`;
    }
    return `
      <div class="decision-center-sites-40-block">
        <h4>${escapeHtml(title)}</h4>
        <ul class="decision-center-sites-40-distribution">
          ${entries.map(([label, count]) => `<li><span>${escapeHtml(label)}</span><strong>${count.toLocaleString('fr-FR')}</strong></li>`).join('')}
        </ul>
      </div>
    `;
  }

  function renderSites40ProgramPanel(payload) {
    const container = document.querySelector('#decision-center-sites-40-body');
    if (!container) return;

    const sites = asArray(payload?.sites);
    const total = payload?._meta?.count || sites.length;
    const byZone = countByField(sites, 'zone');
    const byProvince = countByField(sites, 'province');

    container.innerHTML = `
      <div class="decision-center-sites-40-summary">
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Total sites</p>
          <p class="summary-value">${Number(total).toLocaleString('fr-FR')}</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Statut</p>
          <p class="summary-value is-status">Données KMZ intégrées</p>
        </article>
      </div>
      <div class="decision-center-sites-40-distributions">
        ${renderDistributionList('Répartition par zone FDSU', byZone)}
        ${renderDistributionList('Répartition par province', byProvince)}
      </div>
    `;
    decisionCenterState.sites40Loaded = true;
  }

  function bindSites40MapButton() {
    const button = document.querySelector('#decision-center-sites-40-map-btn');
    if (!button || button.dataset.bound === 'true') return;
    button.dataset.bound = 'true';
    button.addEventListener('click', () => {
      const shared = getShared();
      if (typeof shared.openSites40ProgramOnMap === 'function') {
        shared.openSites40ProgramOnMap();
        return;
      }
      if (typeof global.openSites40ProgramOnMap === 'function') {
        global.openSites40ProgramOnMap();
      }
    });
  }

  function loadSites40ProgramPanel(forceReload) {
    if (decisionCenterState.sites40Loading) return Promise.resolve();
    if (decisionCenterState.sites40Loaded && !forceReload) return Promise.resolve();

    const container = document.querySelector('#decision-center-sites-40-body');
    if (!container) return Promise.resolve();

    bindSites40MapButton();
    decisionCenterState.sites40Loading = true;
    container.innerHTML = '<p class="decision-center-program-loading">Chargement du programme Sites 40…</p>';

    return fetchProgramJson('sites_40/sites_40.json')
      .then((payload) => {
        renderSites40ProgramPanel(payload);
      })
      .catch(() => {
        container.innerHTML = '<p class="decision-center-program-error">Programme Sites 40 indisponible (<code>data/programs/sites_40/sites_40.json</code>).</p>';
      })
      .finally(() => {
        decisionCenterState.sites40Loading = false;
      });
  }

  function fetchBusinessJson(filename) {
    const path = `${BUSINESS_DATA_BASE}${filename}`;
    return global.fetch(path).then((response) => {
      if (!response.ok) {
        throw new Error(`Impossible de charger ${path}`);
      }
      return response.json();
    });
  }

  function resolveProgramStatusLabel(program, legacyStatusCatalog, lifecycleCatalog) {
    const lifecycle = asArray(lifecycleCatalog).find((entry) => entry.code === program?.program_status);
    if (lifecycle?.label) return lifecycle.label;
    const match = asArray(legacyStatusCatalog).find((entry) => entry.id === program?.status);
    return match?.label || program?.status || 'Non défini';
  }

  function resolveProgramStatusClass(program, lifecycleCatalog) {
    const lifecycle = asArray(lifecycleCatalog).find((entry) => entry.code === program?.program_status);
    if (lifecycle?.code === 'PLANIFIE') return 'is-planned';
    if (lifecycle?.code === 'EN_EXECUTION') return 'is-active';
    if (lifecycle?.code === 'EN_PREPARATION') return 'is-preparation';
    if (lifecycle?.code === 'EN_SUIVI') return 'is-followup';
    if (lifecycle?.code === 'TERMINE') return 'is-completed';
    if (program?.status === 'active') return 'is-active';
    if (program?.status === 'planned') return 'is-planned';
    return 'is-defined';
  }

  function renderProgramCard(program, legacyStatusCatalog, lifecycleCatalog) {
    const title = escapeHtml(program?.name || program?.short_label || 'Programme');
    const tagline = escapeHtml(program?.tagline || program?.description || '');
    const statusLabel = escapeHtml(resolveProgramStatusLabel(program, legacyStatusCatalog, lifecycleCatalog));
    const statusClass = resolveProgramStatusClass(program, lifecycleCatalog);

    return `
      <article class="decision-center-program-card" data-program-id="${escapeHtml(program?.id || '')}">
        <div class="decision-center-program-card-head">
          <span class="decision-center-program-card-marker" aria-hidden="true">■</span>
          <h4 class="decision-center-program-card-title">${title}</h4>
        </div>
        ${tagline ? `<p class="decision-center-program-card-tagline">${tagline}</p>` : ''}
        <p class="decision-center-program-card-status ${statusClass}">${statusLabel}</p>
      </article>
    `;
  }

  function renderBusinessArchitecturePanel(payload, lifecycleCatalog) {
    const container = document.querySelector('#decision-center-program-grid');
    if (!container) return;

    const programs = asArray(payload?.programs);
    const legacyStatusCatalog = asArray(payload?.statuses);

    if (!programs.length) {
      container.innerHTML = '<p class="decision-center-program-error">Aucun programme FDSU disponible.</p>';
      return;
    }

    container.innerHTML = programs.map((program) => renderProgramCard(program, legacyStatusCatalog, lifecycleCatalog)).join('');
    decisionCenterState.programsLoaded = true;
  }

  function loadPriorityMatrix() {
    if (decisionCenterState.priorityMatrixLoader) {
      return Promise.resolve(decisionCenterState.priorityMatrixLoader);
    }
    return fetchBusinessJson('priority_matrix_loader.json')
      .then((payload) => {
        decisionCenterState.priorityMatrixLoader = payload;
        return payload;
      })
      .catch(() => null);
  }

  function renderSites300ProgramPanel(payload, matrixLoader) {
    const container = document.querySelector('#decision-center-sites-300-body');
    if (!container) return;

    const sites = asArray(payload?.sites);
    const total = payload?._meta?.count || sites.length;
    const matrixStatus = matrixLoader?.status?.message || 'Matrice disponible — scoring FDSU à calculer.';

    container.innerHTML = `
      <div class="decision-center-sites-40-summary">
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Statut programme</p>
          <p class="summary-value is-planned-status">🟡 Planifié</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Sites</p>
          <p class="summary-value">${Number(total).toLocaleString('fr-FR')}</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Matrice</p>
          <p class="summary-value is-status">Disponible</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Score FDSU</p>
          <p class="summary-value">À calculer</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Déploiement</p>
          <p class="summary-value">Non démarré</p>
        </article>
      </div>
      <p class="decision-center-program-note">${escapeHtml(matrixStatus)}</p>
      <div class="decision-center-sites-300-actions">
        <button type="button" class="primary-button" id="decision-center-sites-300-map-btn">Consulter les sites</button>
        <button type="button" class="secondary-button" id="decision-center-sites-300-matrix-btn">Voir la matrice</button>
        <button type="button" class="secondary-button" id="decision-center-sites-300-analysis-btn">Préparer l'analyse</button>
      </div>
      <div class="decision-center-program-info hidden" id="decision-center-sites-300-info" aria-live="polite"></div>
    `;
    bindSites300ActionButtons();
    decisionCenterState.sites300Loaded = true;
  }

  function showSites300Info(message) {
    const panel = document.querySelector('#decision-center-sites-300-info');
    if (!panel) return;
    panel.classList.remove('hidden');
    panel.innerHTML = `<p>${escapeHtml(message)}</p>`;
  }

  function bindSites300ActionButtons() {
    const mapButton = document.querySelector('#decision-center-sites-300-map-btn');
    if (mapButton && mapButton.dataset.bound !== 'true') {
      mapButton.dataset.bound = 'true';
      mapButton.addEventListener('click', () => {
        const shared = getShared();
        if (typeof shared.openSites300ProgramOnMap === 'function') {
          shared.openSites300ProgramOnMap();
          return;
        }
        if (typeof global.openSites300ProgramOnMap === 'function') {
          global.openSites300ProgramOnMap();
        }
      });
    }

    const matrixButton = document.querySelector('#decision-center-sites-300-matrix-btn');
    if (matrixButton && matrixButton.dataset.bound !== 'true') {
      matrixButton.dataset.bound = 'true';
      matrixButton.addEventListener('click', () => {
        loadPriorityMatrix().then((loader) => {
          const source = loader?.source?.strategic_copy || 'data/programs/sites_300/matrice_priorisation_300_sites.xlsx';
          showSites300Info(`Matrice officielle référencée : ${source}. Le pipeline de normalisation et de scoring est préparé ; le calcul FDSU n'est pas encore activé.`);
        });
      });
    }

    const analysisButton = document.querySelector('#decision-center-sites-300-analysis-btn');
    if (analysisButton && analysisButton.dataset.bound !== 'true') {
      analysisButton.dataset.bound = 'true';
      analysisButton.addEventListener('click', () => {
        loadPriorityMatrix().then((loader) => {
          const steps = asArray(loader?.pipeline).map((step) => step.description).join(' ');
          showSites300Info(`Analyse préparée via data/business/priority_matrix_loader.json. Étapes prévues : ${steps || 'normalisation et scoring à venir.'}`);
        });
      });
    }
  }

  function loadSites300ProgramPanel(forceReload) {
    if (decisionCenterState.sites300Loading) return Promise.resolve();
    if (decisionCenterState.sites300Loaded && !forceReload) return Promise.resolve();

    const container = document.querySelector('#decision-center-sites-300-body');
    if (!container) return Promise.resolve();

    decisionCenterState.sites300Loading = true;
    container.innerHTML = '<p class="decision-center-program-loading">Chargement du programme Sites 300…</p>';

    return Promise.all([
      fetchProgramJson('sites_300/sites_300.json'),
      loadPriorityMatrix(),
    ])
      .then(([payload, matrixLoader]) => {
        renderSites300ProgramPanel(payload, matrixLoader);
      })
      .catch(() => {
        container.innerHTML = '<p class="decision-center-program-error">Programme Sites 300 indisponible (<code>data/programs/sites_300/sites_300.json</code>).</p>';
      })
      .finally(() => {
        decisionCenterState.sites300Loading = false;
      });
  }

  function loadTelecomReferentialPanel(forceReload) {
    if (decisionCenterState.telecomLoaded && !forceReload) return Promise.resolve();

    const container = document.querySelector('#decision-center-telecom-body');
    if (!container) return Promise.resolve();
    if (decisionCenterState.telecomLoading && !forceReload) {
      return decisionCenterState.telecomLoadingPromise || Promise.resolve();
    }

    const shared = getShared();
    decisionCenterState.telecomLoading = true;
    container.innerHTML = '<p class="decision-center-program-loading">Chargement du référentiel télécom…</p>';

    const canUseDb = typeof shared.canUseTelecomDbData === 'function' && shared.canUseTelecomDbData();
    if (!canUseDb) {
      container.innerHTML = `
        <div class="decision-center-sites-40-summary">
          <article class="decision-center-sites-40-stat">
            <p class="summary-label">Mode</p>
            <p class="summary-value is-status">JSON</p>
          </article>
        </div>
        <p class="decision-center-program-note">Données télécom disponibles en mode DB.</p>
      `;
      decisionCenterState.telecomLoaded = true;
      decisionCenterState.telecomLoading = false;
      decisionCenterState.telecomLoadingPromise = null;
      return Promise.resolve();
    }

    const fetchPanel = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/telecom/panel')
      : global.fetch('http://127.0.0.1:8001/api/telecom/panel').then((response) => (response.ok ? response.json() : null));

    decisionCenterState.telecomLoadingPromise = Promise.race([
      fetchPanel,
      new Promise((resolve) => {
        global.setTimeout(() => resolve(null), 8000);
      }),
    ])
      .then((payload) => {
        if (!payload?.statistics) {
          throw new Error('Referentiel telecom indisponible');
        }
        const stats = payload.statistics;
        const operators = asArray(payload.operators);
        const sources = asArray(stats.by_source_file);
        container.innerHTML = `
          <div class="decision-center-sites-40-summary">
            <article class="decision-center-sites-40-stat">
              <p class="summary-label">Opérateurs</p>
              <p class="summary-value">${Number(stats.operator_count || operators.length).toLocaleString('fr-FR')}</p>
            </article>
            <article class="decision-center-sites-40-stat">
              <p class="summary-label">Sites radio</p>
              <p class="summary-value">${Number(stats.infrastructure_count || 0).toLocaleString('fr-FR')}</p>
            </article>
            <article class="decision-center-sites-40-stat">
              <p class="summary-label">Lignes réseau</p>
              <p class="summary-value">${Number(stats.network_line_count || 0).toLocaleString('fr-FR')}</p>
            </article>
            <article class="decision-center-sites-40-stat">
              <p class="summary-label">Polygones réseau</p>
              <p class="summary-value">${Number(stats.coverage_polygon_count || 0).toLocaleString('fr-FR')}</p>
            </article>
          </div>
          <div class="decision-center-sites-40-distributions">
            ${renderDistributionList('Opérateurs importés', operators.reduce((acc, item) => {
              acc[item.operator_name || item.operator_code] = 1;
              return acc;
            }, {}))}
            ${renderDistributionList('Sources KMZ intégrées', sources.reduce((acc, item) => {
              acc[item.source_file] = Number(item.points || 0) + Number(item.lines || 0) + Number(item.polygons || 0);
              return acc;
            }, {}))}
          </div>
          <p class="decision-center-program-note">Référentiel télécom disponible pour les futures analyses de couverture et de proximité FDSU.</p>
        `;
        decisionCenterState.telecomLoaded = true;
      })
      .catch(() => {
        container.innerHTML = `
          <div class="decision-center-sites-40-summary">
            <article class="decision-center-sites-40-stat">
              <p class="summary-label">Mode</p>
              <p class="summary-value is-status">Indisponible</p>
            </article>
          </div>
          <p class="decision-center-program-note">Données télécom disponibles en mode DB.</p>
        `;
        decisionCenterState.telecomLoaded = true;
      })
      .finally(() => {
        decisionCenterState.telecomLoading = false;
        decisionCenterState.telecomLoadingPromise = null;
      });

    return decisionCenterState.telecomLoadingPromise;
  }

  function loadSpatialAnalysisPanel(forceReload) {
    if (decisionCenterState.spatialLoaded && !forceReload) return Promise.resolve();

    const container = document.querySelector('#decision-center-spatial-body');
    if (!container) return Promise.resolve();
    if (decisionCenterState.spatialLoading && !forceReload) {
      return decisionCenterState.spatialLoadingPromise || Promise.resolve();
    }

    const shared = getShared();
    decisionCenterState.spatialLoading = true;
    container.innerHTML = '<p class="decision-center-program-loading">Chargement de l\'analyse spatiale…</p>';

    const canUseDb = typeof shared.canUseTelecomDbData === 'function' && shared.canUseTelecomDbData();
    if (!canUseDb) {
      container.innerHTML = `
        <div class="decision-center-sites-40-summary">
          <article class="decision-center-sites-40-stat">
            <p class="summary-label">Mode</p>
            <p class="summary-value is-status">JSON</p>
          </article>
        </div>
        <p class="decision-center-program-note">Analyses spatiales disponibles en mode DB.</p>
      `;
      decisionCenterState.spatialLoaded = true;
      decisionCenterState.spatialLoading = false;
      return Promise.resolve();
    }

    const fetchPanel = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/analysis/panel')
      : Promise.resolve(null);

    decisionCenterState.spatialLoadingPromise = Promise.race([
      fetchPanel,
      new Promise((resolve) => { global.setTimeout(() => resolve(null), 8000); }),
    ])
      .then((payload) => {
        if (!payload?.statistics) {
          throw new Error('Analyse indisponible');
        }
        renderSpatialAnalysisPanel(payload.statistics);
        decisionCenterState.spatialLoaded = true;
      })
      .catch(() => {
        container.innerHTML = `
          <div class="decision-center-sites-40-summary">
            <article class="decision-center-sites-40-stat">
              <p class="summary-label">Mode</p>
              <p class="summary-value is-status">Indisponible</p>
            </article>
          </div>
          <p class="decision-center-program-note">Analyses spatiales disponibles en mode DB.</p>
        `;
        decisionCenterState.spatialLoaded = true;
      })
      .finally(() => {
        decisionCenterState.spatialLoading = false;
        decisionCenterState.spatialLoadingPromise = null;
      });

    return decisionCenterState.spatialLoadingPromise;
  }

  function renderSpatialAnalysisPanel(stats) {
    const container = document.querySelector('#decision-center-spatial-body');
    if (!container) return;
    const lastAnalysis = stats.last_analysis
      ? new Date(stats.last_analysis).toLocaleString('fr-FR')
      : 'Aucune analyse';
    container.innerHTML = `
      <div class="decision-center-sites-40-summary">
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Sites analysés</p>
          <p class="summary-value">${Number(stats.sites_analyzed || 0).toLocaleString('fr-FR')}</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Infrastructures</p>
          <p class="summary-value">${Number(stats.infrastructure_analyzed || 0).toLocaleString('fr-FR')}</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Relations calculées</p>
          <p class="summary-value">${Number(stats.relations_computed || 0).toLocaleString('fr-FR')}</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Dernière analyse</p>
          <p class="summary-value is-status">${escapeHtml(lastAnalysis)}</p>
        </article>
      </div>
      <p class="decision-center-program-note">Moteur d'analyse spatiale générique — prêt pour Santé, Éducation, Énergie et futurs référentiels.</p>
    `;
  }

  function bindSpatialAnalysisRunButton() {
    const button = document.querySelector('#decision-center-spatial-run-btn');
    if (!button || button.dataset.bound === 'true') return;
    button.dataset.bound = 'true';
    button.addEventListener('click', () => {
      const shared = getShared();
      const container = document.querySelector('#decision-center-spatial-body');
      if (!container) return;
      if (typeof shared.canUseTelecomDbData === 'function' && !shared.canUseTelecomDbData()) {
        container.innerHTML = '<p class="decision-center-program-note">Analyses spatiales disponibles en mode DB.</p>';
        return;
      }
      container.innerHTML = '<p class="decision-center-program-loading">Analyse des programmes Sites 40 et Sites 300 en cours…</p>';
      const run = typeof shared.fetchApiJson === 'function'
        ? shared.fetchApiJson('/api/analysis/run/programs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
        : Promise.reject(new Error('API indisponible'));
      run
        .then(() => loadSpatialAnalysisPanel(true))
        .catch(() => {
          container.innerHTML = '<p class="decision-center-program-error">Analyse impossible. Vérifiez PostgreSQL et le mode DB.</p>';
        });
    });
  }

  const DECISION_ENGINE_PRIORITY_CLASS = {
    critical: 'is-critical',
    high: 'is-high',
    medium: 'is-medium',
    low: 'is-low',
  };

  const DECISION_ENGINE_MARKER_COLORS = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#ca8a04',
    low: '#4ade80',
  };

  function humanizeCriteriaLabel(label) {
    if (!label) return '';
    let text = String(label);
    text = text.replace(/Programme Sites 40 — déploiement en exécution/i, 'Programme Sites 40 — en cours');
    text = text.replace(/Programme Sites 300 — planifié/i, 'Programme Sites 300 — planifié');
    text = text.replace(/Distance opérateur ([\d.,]+) km — déficit majeur/i, 'Réseau éloigné ($1 km) — besoin urgent');
    text = text.replace(/Distance opérateur ([\d.,]+) km — déficit élevé/i, 'Réseau éloigné ($1 km) — couverture faible');
    text = text.replace(/Distance opérateur ([\d.,]+) km — déficit modéré/i, 'Réseau à $1 km — déficit modéré');
    text = text.replace(/Proximité infrastructure \(([\d.,]+) km\) — déficit faible/i, 'Réseau proche ($1 km)');
    text = text.replace(/Contexte admin validé PostGIS — /i, 'Zone : ');
    text = text.replace(/Province et territoire renseignés — /i, 'Zone : ');
    text = text.replace(/Contexte administratif partiel — /i, 'Zone partielle : ');
    text = text.replace(/Contexte administratif incomplet/i, 'Localisation à compléter');
    text = text.replace(/\d+ relations spatiales calculées/i, 'Analyse spatiale complète');
    text = text.replace(/\d+ relation\(s\) spatiale\(s\) — analyse partielle/i, 'Analyse spatiale partielle');
    text = text.replace(/Aucune relation spatiale — exécuter l'analyse spatiale/i, 'Lancer l\'analyse spatiale');
    text = text.replace(/Distance télécom non calculée — lancer l'analyse spatiale/i, 'Couverture réseau à analyser');
    text = text.replace(/Site en exécution/i, 'Déploiement en cours');
    text = text.replace(/Site du programme en cours de déploiement/i, 'Site en déploiement actif');
    if (text.length > 64) return `${text.slice(0, 61)}…`;
    return text;
  }

  function formatProgramLabel(site) {
    const code = String(site?.program_code || '').toUpperCase();
    if (code.includes('SITES_40')) return 'Sites 40';
    if (code.includes('SITES_300')) return 'Sites 300';
    const name = site?.program_name || site?.program_code || '—';
    return name.length > 14 ? `${name.slice(0, 12)}…` : name;
  }

  function getDecisionEngineMarkerColor(site) {
    return DECISION_ENGINE_MARKER_COLORS[site?.priority_level] || DECISION_ENGINE_MARKER_COLORS.low;
  }

  function renderDecisionEngineKpis(summary) {
    const total = summary?.total ?? 0;
    const set = (id, value) => {
      const node = document.querySelector(id);
      if (node) node.textContent = Number(value || 0).toLocaleString('fr-FR');
    };
    set('#decision-engine-kpi-total', total);
    set('#decision-engine-kpi-critical', summary?.critical);
    set('#decision-engine-kpi-high', summary?.high);
    set('#decision-engine-kpi-medium', summary?.medium);
    set('#decision-engine-kpi-low', summary?.low);
  }

  function formatDecisionCriteria(topCriteria) {
    const items = asArray(topCriteria);
    if (!items.length) return '—';
    return items.slice(0, 2).map((item) => escapeHtml(humanizeCriteriaLabel(item?.label || ''))).join(' · ');
  }

  function renderDecisionEngineTable(sites) {
    const tbody = document.querySelector('#decision-engine-table-body');
    if (!tbody) return;
    const filtered = decisionCenterState.decisionEngineFilter
      ? sites.filter((site) => site.priority_level === decisionCenterState.decisionEngineFilter)
      : sites;

    if (!filtered.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="decision-center-program-loading">Aucun site pour ce filtre.</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map((site) => {
      const levelClass = DECISION_ENGINE_PRIORITY_CLASS[site.priority_level] || 'is-low';
      const selected = decisionCenterState.decisionEngineSelectedSiteId === site.site_id ? ' is-selected' : '';
      const territory = [site.territoire, site.province].filter(Boolean).join(' / ') || '—';
      const siteName = site.site_name || '—';
      const criteriaText = formatDecisionCriteria(site.top_criteria);
      return `
        <tr data-site-id="${site.site_id}" class="${selected.trim()}">
          <td title="${escapeHtml(site.site_code || '—')}">${escapeHtml(site.site_code || '—')}</td>
          <td title="${escapeHtml(siteName)}">${escapeHtml(siteName)}</td>
          <td title="${escapeHtml(site.program_name || site.program_code || '—')}">${escapeHtml(formatProgramLabel(site))}</td>
          <td title="${escapeHtml(territory)}">${escapeHtml(territory)}</td>
          <td>${Number(site.priority_score || 0).toFixed(1)}</td>
          <td><span class="decision-engine-priority-badge ${levelClass}">${escapeHtml(site.priority_level_label || site.priority_level)}</span></td>
          <td><span class="decision-engine-criteria" title="${criteriaText}">${criteriaText}</span></td>
        </tr>
      `;
    }).join('');

    tbody.querySelectorAll('[data-site-id]').forEach((row) => {
      row.addEventListener('click', () => {
        selectDecisionEngineSite(Number(row.dataset.siteId));
      });
    });
  }

  function initializeDecisionEngineMap() {
    const shared = getShared();
    if (typeof global.L === 'undefined') return;

    const mapElement = document.querySelector('#decision-engine-map');
    if (!mapElement) return;

    if (decisionCenterState.decisionEngineMap) {
      global.setTimeout(() => decisionCenterState.decisionEngineMap.invalidateSize(), 0);
      return;
    }

    decisionCenterState.decisionEngineMap = global.L.map(mapElement, {
      zoomControl: true,
      attributionControl: true,
      minZoom: 4,
      maxZoom: 14,
    }).setView([-2.8, 23.5], 5);

    global.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(decisionCenterState.decisionEngineMap);

    decisionCenterState.decisionEngineMarkers = global.L.layerGroup().addTo(decisionCenterState.decisionEngineMap);

    if (shared.fetchApiJson) {
      shared.fetchApiJson('/map/layers/provinces?limit=5000')
        .then((payload) => {
          const features = asArray(payload?.features);
          if (!features.length) return;
          global.L.geoJSON({ type: 'FeatureCollection', features }, {
            style: shared.styleProvinceFeature,
          }).addTo(decisionCenterState.decisionEngineMap);
        })
        .catch(() => {});
    }

    global.setTimeout(() => decisionCenterState.decisionEngineMap?.invalidateSize(), 0);
  }

  function updateDecisionEngineMapMarkers(sites) {
    if (!decisionCenterState.decisionEngineMap || !decisionCenterState.decisionEngineMarkers) return;

    const filtered = decisionCenterState.decisionEngineFilter
      ? sites.filter((site) => site.priority_level === decisionCenterState.decisionEngineFilter)
      : sites;

    decisionCenterState.decisionEngineMarkers.clearLayers();
    const bounds = [];

    filtered.forEach((site) => {
      const lat = Number(site.latitude);
      const lng = Number(site.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
      const color = getDecisionEngineMarkerColor(site);
      const marker = global.L.circleMarker([lat, lng], {
        radius: decisionCenterState.decisionEngineSelectedSiteId === site.site_id ? 9 : 6,
        color,
        fillColor: color,
        fillOpacity: 0.85,
        weight: decisionCenterState.decisionEngineSelectedSiteId === site.site_id ? 3 : 1,
      });
      marker.bindPopup(`
        <strong>${escapeHtml(site.site_name || '')}</strong><br/>
        Score : ${Number(site.priority_score || 0).toFixed(1)}<br/>
        ${escapeHtml(site.priority_level_label || '')}
      `);
      marker.on('click', () => selectDecisionEngineSite(site.site_id));
      marker.addTo(decisionCenterState.decisionEngineMarkers);
      bounds.push([lat, lng]);
    });

    if (bounds.length > 1) {
      decisionCenterState.decisionEngineMap.fitBounds(bounds, { padding: [24, 24], maxZoom: 8 });
    } else if (bounds.length === 1) {
      decisionCenterState.decisionEngineMap.setView(bounds[0], 8);
    }
  }

  function selectDecisionEngineSite(siteId) {
    decisionCenterState.decisionEngineSelectedSiteId = siteId;
    renderDecisionEngineTable(decisionCenterState.decisionEngineSites);
    updateDecisionEngineMapMarkers(decisionCenterState.decisionEngineSites);

    const site = decisionCenterState.decisionEngineSites.find((item) => item.site_id === siteId);
    if (site && decisionCenterState.decisionEngineMap) {
      const lat = Number(site.latitude);
      const lng = Number(site.longitude);
      if (Number.isFinite(lat) && Number.isFinite(lng)) {
        decisionCenterState.decisionEngineMap.setView([lat, lng], 10);
      }
    }
  }

  function bindDecisionEngineFilters() {
    const container = document.querySelector('#decision-engine-filters');
    if (!container || container.dataset.bound === 'true') return;
    container.dataset.bound = 'true';

    container.querySelectorAll('[data-priority-filter]').forEach((button) => {
      button.addEventListener('click', () => {
        decisionCenterState.decisionEngineFilter = button.dataset.priorityFilter || '';
        container.querySelectorAll('[data-priority-filter]').forEach((item) => {
          item.classList.toggle('is-active', item === button);
        });
        renderDecisionEngineTable(decisionCenterState.decisionEngineSites);
        updateDecisionEngineMapMarkers(decisionCenterState.decisionEngineSites);
      });
    });
  }

  function bindDecisionEngineRecomputeButton() {
    const button = document.querySelector('#decision-engine-recompute-btn');
    if (!button || button.dataset.bound === 'true') return;
    button.dataset.bound = 'true';

    button.addEventListener('click', () => {
      const shared = getShared();
      const tbody = document.querySelector('#decision-engine-table-body');
      if (typeof shared.canUseTelecomDbData === 'function' && !shared.canUseTelecomDbData()) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="decision-center-program-note">Scores disponibles en mode DB.</td></tr>';
        return;
      }
      if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="decision-center-program-loading">Recalcul des scores en cours…</td></tr>';
      const run = typeof shared.fetchApiJson === 'function'
        ? shared.fetchApiJson('/api/decision/recompute-site-scores', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
        : Promise.reject(new Error('API indisponible'));
      run
        .then(() => loadDecisionEnginePanel(true))
        .catch(() => {
          if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="decision-center-program-error">Recalcul impossible.</td></tr>';
        });
    });
  }

  function loadDecisionEnginePanel(forceReload) {
    if (decisionCenterState.decisionEngineLoaded && !forceReload) {
      initializeDecisionEngineMap();
      updateDecisionEngineMapMarkers(decisionCenterState.decisionEngineSites);
      global.setTimeout(() => decisionCenterState.decisionEngineMap?.invalidateSize(), 0);
      return Promise.resolve();
    }
    if (decisionCenterState.decisionEngineLoading && !forceReload) return Promise.resolve();

    const tbody = document.querySelector('#decision-engine-table-body');
    const shared = getShared();
    bindDecisionEngineFilters();
    bindDecisionEngineRecomputeButton();

    decisionCenterState.decisionEngineLoading = true;
    if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="decision-center-program-loading">Chargement des scores…</td></tr>';

    const canUseDb = typeof shared.canUseTelecomDbData === 'function' && shared.canUseTelecomDbData();
    if (!canUseDb) {
      renderDecisionEngineKpis({ total: 0, critical: 0, high: 0, medium: 0, low: 0 });
      if (tbody) {
        tbody.innerHTML = '<tr><td colspan="7" class="decision-center-program-note">Moteur de décision disponible en mode DB (DATA_MODE=db).</td></tr>';
      }
      decisionCenterState.decisionEngineLoaded = true;
      decisionCenterState.decisionEngineLoading = false;
      initializeDecisionEngineMap();
      return Promise.resolve();
    }

    const fetchScores = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/decision/site-scores?limit=500')
      : Promise.reject(new Error('API indisponible'));

    return fetchScores
      .then((payload) => {
        if (!payload?.sites) throw new Error('Scores indisponibles');
        if (payload.summary?.total === 0) {
          return shared.fetchApiJson('/api/decision/recompute-site-scores', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
          }).then(() => shared.fetchJson('/api/decision/site-scores?limit=500'));
        }
        return payload;
      })
      .then((payload) => {
        decisionCenterState.decisionEngineSites = asArray(payload?.sites);
        renderDecisionEngineKpis(payload?.summary);
        renderDecisionEngineTable(decisionCenterState.decisionEngineSites);
        initializeDecisionEngineMap();
        updateDecisionEngineMapMarkers(decisionCenterState.decisionEngineSites);
        decisionCenterState.decisionEngineLoaded = true;
      })
      .catch(() => {
        renderDecisionEngineKpis({ total: 0, critical: 0, high: 0, medium: 0, low: 0 });
        if (tbody) {
          tbody.innerHTML = '<tr><td colspan="7" class="decision-center-program-note">Scores disponibles en mode DB après recalcul.</td></tr>';
        }
        initializeDecisionEngineMap();
        decisionCenterState.decisionEngineLoaded = true;
      })
      .finally(() => {
        decisionCenterState.decisionEngineLoading = false;
        global.setTimeout(() => decisionCenterState.decisionEngineMap?.invalidateSize(), 0);
      });
  }

  const SECTORIAL_CARD_CODES = ['HEALTH', 'EDUCATION', 'ENERGY', 'ROADS', 'POPULATION'];
  const REFERENTIAL_STATUS_LABELS = {
    active: 'Actif',
    in_progress: 'En cours',
    planned: 'Planifié',
  };
  const REFERENTIAL_STATUS_CLASS = {
    active: 'is-active',
    in_progress: 'is-progress',
    planned: 'is-planned',
  };

  function renderSectorialCatalogCards(catalog) {
    const container = document.querySelector('#sectorial-catalog-grid');
    if (!container) return;
    const items = asArray(catalog).filter((item) => SECTORIAL_CARD_CODES.includes(item.code));
    if (!items.length) {
      container.innerHTML = '<p class="decision-center-program-note">Catalogue sectoriel indisponible.</p>';
      return;
    }
    container.innerHTML = items.map((item) => {
      const status = item.status || 'planned';
      const statusClass = REFERENTIAL_STATUS_CLASS[status] || 'is-planned';
      const statusLabel = REFERENTIAL_STATUS_LABELS[status] || status;
      return `
        <article class="sectorial-catalog-card ${statusClass}" data-reference-code="${escapeHtml(item.code)}">
          <p class="summary-label">${escapeHtml(item.code)}</p>
          <h4>${escapeHtml(item.name || item.code)}</h4>
          <p class="sectorial-catalog-status">${escapeHtml(statusLabel)}</p>
        </article>
      `;
    }).join('');
  }

  function renderSectorialHealthKpis(stats) {
    const set = (id, value) => {
      const node = document.querySelector(id);
      if (node) node.textContent = Number(value || 0).toLocaleString('fr-FR');
    };
    set('#sectorial-health-kpi-total', stats?.total_facilities);
    set('#sectorial-health-kpi-hospitals', stats?.hospitals);
    set('#sectorial-health-kpi-centers', stats?.health_centers);
    set('#sectorial-health-kpi-posts', stats?.health_posts);
    set('#sectorial-health-kpi-geo', stats?.facilities_with_geometry);
  }

  function renderSectorialHealthTable(facilities, emptyMessage) {
    const tbody = document.querySelector('#sectorial-health-table-body');
    if (!tbody) return;
    const rows = asArray(facilities);
    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="decision-center-program-note">${escapeHtml(emptyMessage || 'Les données santé seront intégrées depuis une source officielle.')}</td></tr>`;
      return;
    }
    tbody.innerHTML = rows.map((item) => `
      <tr>
        <td>${escapeHtml(item.official_code || '—')}</td>
        <td>${escapeHtml(item.name || '—')}</td>
        <td>${escapeHtml(item.facility_type_name || item.facility_type_code || '—')}</td>
        <td>${escapeHtml(item.province_name || '—')}</td>
      </tr>
    `).join('');
  }

  function initializeSectorialHealthMap() {
    const shared = getShared();
    if (typeof global.L === 'undefined') return;
    const mapElement = document.querySelector('#sectorial-health-map');
    if (!mapElement) return;

    if (decisionCenterState.healthMap) {
      global.setTimeout(() => decisionCenterState.healthMap.invalidateSize(), 0);
      return;
    }

    decisionCenterState.healthMap = global.L.map(mapElement, {
      zoomControl: true,
      attributionControl: true,
      minZoom: 4,
      maxZoom: 14,
    }).setView([-2.8, 23.5], 5);

    global.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(decisionCenterState.healthMap);

    if (shared.fetchApiJson) {
      shared.fetchApiJson('/map/layers/provinces?limit=5000')
        .then((payload) => {
          const features = asArray(payload?.features);
          if (!features.length) return;
          global.L.geoJSON({ type: 'FeatureCollection', features }, {
            style: shared.styleProvinceFeature,
          }).addTo(decisionCenterState.healthMap);
        })
        .catch(() => {});
    }

    global.setTimeout(() => decisionCenterState.healthMap?.invalidateSize(), 0);
  }

  function loadSectorialReferentialsPanel(forceReload) {
    if (decisionCenterState.sectorialLoaded && !forceReload) {
      initializeSectorialHealthMap();
      global.setTimeout(() => decisionCenterState.healthMap?.invalidateSize(), 0);
      return Promise.resolve();
    }
    if (decisionCenterState.sectorialLoading && !forceReload) return Promise.resolve();

    decisionCenterState.sectorialLoading = true;
    const catalogContainer = document.querySelector('#sectorial-catalog-grid');
    const shared = getShared();
    const canUseDb = typeof shared.canUseTelecomDbData === 'function' && shared.canUseTelecomDbData();

    if (catalogContainer) {
      catalogContainer.innerHTML = '<p class="decision-center-program-loading">Chargement du catalogue…</p>';
    }

    if (!canUseDb) {
      renderSectorialCatalogCards([
        { code: 'HEALTH', name: 'Référentiel Santé', status: 'in_progress' },
        { code: 'EDUCATION', name: 'Référentiel Éducation', status: 'planned' },
        { code: 'ENERGY', name: 'Référentiel Énergie', status: 'planned' },
        { code: 'ROADS', name: 'Référentiel Routes', status: 'planned' },
        { code: 'POPULATION', name: 'Référentiel Population', status: 'planned' },
      ]);
      renderSectorialHealthKpis({});
      renderSectorialHealthTable([], 'Les données santé seront intégrées depuis une source officielle.');
      initializeSectorialHealthMap();
      decisionCenterState.sectorialLoaded = true;
      decisionCenterState.sectorialLoading = false;
      return Promise.resolve();
    }

    const fetchReference = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/reference/panel')
      : Promise.reject(new Error('API indisponible'));
    const fetchHealth = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/health/panel')
      : Promise.reject(new Error('API indisponible'));

    const timeout = new Promise((_, reject) => {
      global.setTimeout(() => reject(new Error('Timeout')), 8000);
    });

    return Promise.race([Promise.all([fetchReference, fetchHealth]), timeout])
      .then(([referencePayload, healthPayload]) => {
        renderSectorialCatalogCards(referencePayload?.sectorial_referentials || referencePayload?.catalog || []);
        renderSectorialHealthKpis(healthPayload?.statistics || {});
        renderSectorialHealthTable(
          healthPayload?.facilities || [],
          healthPayload?.table_empty_message,
        );
        initializeSectorialHealthMap();
        decisionCenterState.sectorialLoaded = true;
      })
      .catch(() => {
        renderSectorialCatalogCards([
          { code: 'HEALTH', name: 'Référentiel Santé', status: 'in_progress' },
          { code: 'EDUCATION', name: 'Référentiel Éducation', status: 'planned' },
          { code: 'ENERGY', name: 'Référentiel Énergie', status: 'planned' },
          { code: 'ROADS', name: 'Référentiel Routes', status: 'planned' },
          { code: 'POPULATION', name: 'Référentiel Population', status: 'planned' },
        ]);
        renderSectorialHealthKpis({});
        renderSectorialHealthTable([], 'Les données santé seront intégrées depuis une source officielle.');
        initializeSectorialHealthMap();
        decisionCenterState.sectorialLoaded = true;
      })
      .finally(() => {
        decisionCenterState.sectorialLoading = false;
        global.setTimeout(() => decisionCenterState.healthMap?.invalidateSize(), 0);
      });
  }

  function loadBusinessArchitecturePanel(forceReload) {
    if (decisionCenterState.programsLoading) return Promise.resolve();
    if (decisionCenterState.programsLoaded && !forceReload) return Promise.resolve();

    const container = document.querySelector('#decision-center-program-grid');
    if (!container) return Promise.resolve();

    decisionCenterState.programsLoading = true;
    container.innerHTML = '<p class="decision-center-program-loading">Chargement des programmes FDSU…</p>';

    return Promise.all([
      fetchBusinessJson('fdsu_programs.json'),
      fetchBusinessJson('program_status_catalog.json').catch(() => ({ statuses: [] })),
    ])
      .then(([payload, lifecyclePayload]) => {
        decisionCenterState.programStatusCatalog = lifecyclePayload;
        renderBusinessArchitecturePanel(payload, lifecyclePayload?.statuses);
      })
      .catch(() => {
        container.innerHTML = '<p class="decision-center-program-error">Référentiel métier indisponible (<code>data/business/fdsu_programs.json</code>).</p>';
      })
      .finally(() => {
        decisionCenterState.programsLoading = false;
      });
  }

  function asArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function getShared() {
    return global.SigFdsuShared || {};
  }

  function bindDecisionCenterTabs() {
    const tabList = document.querySelector('#decision-center-tabs');
    if (!tabList || tabList.dataset.bound === 'true') return;
    tabList.dataset.bound = 'true';

    tabList.querySelectorAll('[data-decision-tab]').forEach((button) => {
      button.addEventListener('click', () => {
        setDecisionCenterTab(button.dataset.decisionTab);
      });
    });
  }

  function setDecisionCenterTab(tabId) {
    if (!tabId) return;
    decisionCenterState.activeTab = tabId;

    document.querySelectorAll('[data-decision-tab]').forEach((button) => {
      const isActive = button.dataset.decisionTab === tabId;
      button.classList.toggle('is-active', isActive);
      button.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    document.querySelectorAll('[data-decision-tab-panel]').forEach((panel) => {
      const isActive = panel.dataset.decisionTabPanel === tabId;
      panel.classList.toggle('is-active', isActive);
      panel.hidden = !isActive;
    });

    if (tabId === 'vue-nationale') {
      loadNationalPanel(false);
      initializeDecisionCenterNationalMap();
      loadBusinessArchitecturePanel(false);
      loadSites40ProgramPanel(false);
      loadSites300ProgramPanel(false);
      loadTelecomReferentialPanel(false);
      loadSpatialAnalysisPanel(false);
    }

    if (tabId === 'priorisation') {
      loadDecisionEnginePanel(false);
      global.setTimeout(() => {
        decisionCenterState.decisionEngineMap?.invalidateSize();
      }, 120);
    }

    if (tabId === 'referentiels-sectoriels') {
      loadSectorialReferentialsPanel(false);
      global.setTimeout(() => {
        decisionCenterState.healthMap?.invalidateSize();
      }, 120);
    }
  }

  function setupDecisionCenterResizeObserver(mapElement) {
    if (!mapElement || decisionCenterState.resizeObserver) return;
    const invalidate = () => {
      if (decisionCenterState.map) {
        global.requestAnimationFrame(() => decisionCenterState.map.invalidateSize());
      }
    };

    if (typeof global.ResizeObserver !== 'undefined') {
      decisionCenterState.resizeObserver = new global.ResizeObserver(invalidate);
      decisionCenterState.resizeObserver.observe(mapElement);
    }

    if (decisionCenterState.windowResizeBound !== true) {
      decisionCenterState.windowResizeBound = true;
      global.addEventListener('resize', invalidate);
    }
  }

  function initializeDecisionCenterNationalMap() {
    const shared = getShared();
    if (typeof global.L === 'undefined' || !shared.fetchApiJson) return;

    const mapElement = document.querySelector('#decision-center-national-map');
    if (!mapElement) return;

    setupDecisionCenterResizeObserver(mapElement);

    if (decisionCenterState.map) {
      global.setTimeout(() => decisionCenterState.map.invalidateSize(), 0);
      return;
    }

    decisionCenterState.map = global.L.map(mapElement, {
      zoomControl: true,
      attributionControl: true,
      minZoom: 4,
      maxZoom: 14,
    }).setView([-2.8, 23.5], 5);

    global.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(decisionCenterState.map);

    decisionCenterState.layers = {
      rdcBoundary: global.L.geoJSON(null, { style: shared.styleRdcBoundaryFeature }),
      provinces: global.L.geoJSON(null, { style: shared.styleProvinceFeature }),
    };

    const boundaryPromise = shared.fetchApiJson
      ? shared.fetchJson('/geodata/rdc_boundary.geojson').catch(() => null)
      : Promise.resolve(null);

    boundaryPromise.then((geojson) => {
      if (geojson?.features?.length) {
        decisionCenterState.layers.rdcBoundary.clearLayers();
        decisionCenterState.layers.rdcBoundary.addData(geojson);
        decisionCenterState.layers.rdcBoundary.addTo(decisionCenterState.map);
      }
    });

    shared.fetchApiJson('/map/layers/provinces?limit=5000')
      .then((payload) => {
        const features = asArray(payload?.features);
        if (!features.length) return;
        decisionCenterState.layers.provinces.clearLayers();
        decisionCenterState.layers.provinces.addData({ type: 'FeatureCollection', features });
        decisionCenterState.layers.provinces.addTo(decisionCenterState.map);
        const bounds = decisionCenterState.layers.provinces.getBounds();
        if (bounds.isValid()) {
          decisionCenterState.map.fitBounds(bounds, { padding: [16, 16] });
        }
      })
      .catch(() => {})
      .finally(() => {
        decisionCenterState.mapInitialized = true;
        global.setTimeout(() => decisionCenterState.map?.invalidateSize(), 0);
      });
  }

  function initializeDecisionCenterModule() {
    const panel = document.querySelector('#decision-view-panel');
    if (!panel) return;

    bindDecisionCenterTabs();
    bindSites40MapButton();
    bindSpatialAnalysisRunButton();
    bindDecisionEngineFilters();
    bindDecisionEngineRecomputeButton();

    if (!decisionCenterState.initialized) {
      setDecisionCenterTab('vue-nationale');
      decisionCenterState.initialized = true;
      return;
    }

    if (decisionCenterState.activeTab === 'vue-nationale') {
      loadNationalPanel(false);
      initializeDecisionCenterNationalMap();
      loadBusinessArchitecturePanel(false);
      loadSites40ProgramPanel(false);
      loadSites300ProgramPanel(false);
      loadTelecomReferentialPanel(false);
      loadSpatialAnalysisPanel(false);
    }
  }

  global.decisionCenterState = decisionCenterState;
  global.initializeDecisionCenterModule = initializeDecisionCenterModule;
  global.loadNationalPanel = loadNationalPanel;
  global.loadFdsuBusinessArchitecture = loadBusinessArchitecturePanel;
  global.loadFdsuSites40Program = loadSites40ProgramPanel;
  global.loadFdsuSites300Program = loadSites300ProgramPanel;
  global.loadTelecomReferentialPanel = loadTelecomReferentialPanel;
  global.loadSpatialAnalysisPanel = loadSpatialAnalysisPanel;
  global.loadDecisionEnginePanel = loadDecisionEnginePanel;
  global.loadSectorialReferentialsPanel = loadSectorialReferentialsPanel;
  global.loadPriorityMatrix = loadPriorityMatrix;
  global.FDSU_BUSINESS_DATA_BASE = BUSINESS_DATA_BASE;
  global.FDSU_PROGRAMS_DATA_BASE = PROGRAMS_DATA_BASE;
  global.FDSU_PROGRAMS_PATH = FDSU_PROGRAMS_PATH;
  global.FDSU_SITES_40_DATA_PATH = SITES_40_DATA_PATH;
})(window);
