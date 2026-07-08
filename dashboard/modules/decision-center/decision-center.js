(function initDecisionCenterModule(global) {
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
  };

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

    if (!decisionCenterState.initialized) {
      setDecisionCenterTab('vue-nationale');
      decisionCenterState.initialized = true;
      return;
    }

    if (decisionCenterState.activeTab === 'vue-nationale') {
      initializeDecisionCenterNationalMap();
    }
  }

  global.decisionCenterState = decisionCenterState;
  global.initializeDecisionCenterModule = initializeDecisionCenterModule;
})(window);
