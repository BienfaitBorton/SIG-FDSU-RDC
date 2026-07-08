(function initDecisionCenterModule(global) {
  const BUSINESS_DATA_BASE = '/business/';
  const PROGRAMS_DATA_BASE = '/programs/';
  const FDSU_PROGRAMS_PATH = `${BUSINESS_DATA_BASE}fdsu_programs.json`;
  const SITES_40_DATA_PATH = `${PROGRAMS_DATA_BASE}sites_40/sites_40.json`;

  const DECISION_CENTER_TABS = [
    { id: 'vue-nationale', label: 'Vue nationale' },
    { id: 'priorisation', label: 'Priorisation' },
    { id: 'analyse-multicritere', label: 'Analyse multicritère' },
    { id: 'simulations', label: 'Simulations' },
    { id: 'tableaux-de-bord', label: 'Tableaux de bord' },
    { id: 'rapports', label: 'Rapports' },
  ];

  const DECISION_CENTER_KPIS = [
    { id: 'total-sites', label: 'Nombre total de sites', value: '1 248' },
    { id: 'priority-sites', label: 'Sites prioritaires', value: '186' },
    { id: 'covered-population', label: 'Population couverte', value: '12,4 M' },
    { id: 'uncovered-population', label: 'Population non couverte', value: '3,8 M' },
    { id: 'planned-ccn', label: 'CCN planifiés', value: '42' },
    { id: 'investment', label: 'Investissement estimé', value: '28,6 M USD' },
  ];

  const decisionCenterState = {
    initialized: false,
    activeTab: 'vue-nationale',
    map: null,
    layers: {},
    mapInitialized: false,
    resizeObserver: null,
    programsLoaded: false,
    programsLoading: false,
    sites40Loaded: false,
    sites40Loading: false,
  };

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function fetchProgramJson(relativePath) {
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

  function resolveProgramStatusLabel(program, statusCatalog) {
    const match = asArray(statusCatalog).find((entry) => entry.id === program?.status);
    return match?.label || program?.status || 'Non défini';
  }

  function resolveProgramStatusClass(status) {
    if (status === 'active') return 'is-active';
    if (status === 'planned') return 'is-planned';
    return 'is-defined';
  }

  function renderProgramCard(program, statusCatalog) {
    const title = escapeHtml(program?.name || program?.short_label || 'Programme');
    const tagline = escapeHtml(program?.tagline || program?.description || '');
    const statusLabel = escapeHtml(resolveProgramStatusLabel(program, statusCatalog));
    const statusClass = resolveProgramStatusClass(program?.status);

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

  function renderBusinessArchitecturePanel(payload) {
    const container = document.querySelector('#decision-center-program-grid');
    if (!container) return;

    const programs = asArray(payload?.programs);
    const statusCatalog = asArray(payload?.statuses);

    if (!programs.length) {
      container.innerHTML = '<p class="decision-center-program-error">Aucun programme FDSU disponible.</p>';
      return;
    }

    container.innerHTML = programs.map((program) => renderProgramCard(program, statusCatalog)).join('');
    decisionCenterState.programsLoaded = true;
  }

  function loadBusinessArchitecturePanel(forceReload) {
    if (decisionCenterState.programsLoading) return Promise.resolve();
    if (decisionCenterState.programsLoaded && !forceReload) return Promise.resolve();

    const container = document.querySelector('#decision-center-program-grid');
    if (!container) return Promise.resolve();

    decisionCenterState.programsLoading = true;
    container.innerHTML = '<p class="decision-center-program-loading">Chargement des programmes FDSU…</p>';

    return fetchBusinessJson('fdsu_programs.json')
      .then((payload) => {
        renderBusinessArchitecturePanel(payload);
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
      initializeDecisionCenterNationalMap();
      loadBusinessArchitecturePanel(false);
      loadSites40ProgramPanel(false);
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

    if (!decisionCenterState.initialized) {
      setDecisionCenterTab('vue-nationale');
      decisionCenterState.initialized = true;
      return;
    }

    if (decisionCenterState.activeTab === 'vue-nationale') {
      initializeDecisionCenterNationalMap();
      loadBusinessArchitecturePanel(false);
      loadSites40ProgramPanel(false);
    }
  }

  global.decisionCenterState = decisionCenterState;
  global.initializeDecisionCenterModule = initializeDecisionCenterModule;
  global.loadFdsuBusinessArchitecture = loadBusinessArchitecturePanel;
  global.loadFdsuSites40Program = loadSites40ProgramPanel;
  global.FDSU_BUSINESS_DATA_BASE = BUSINESS_DATA_BASE;
  global.FDSU_PROGRAMS_DATA_BASE = PROGRAMS_DATA_BASE;
  global.FDSU_PROGRAMS_PATH = FDSU_PROGRAMS_PATH;
  global.FDSU_SITES_40_DATA_PATH = SITES_40_DATA_PATH;
})(window);
