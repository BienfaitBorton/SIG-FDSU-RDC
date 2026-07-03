const API_BASE = 'http://127.0.0.1:8000';

const navigationItems = document.querySelectorAll('.nav-item');
const panels = document.querySelectorAll('.module-panel');
const pageTitle = document.querySelector('.page-title');
const pageContext = document.querySelector('.page-context');

const dashboardState = {
  initialized: false,
  modules: {},
};

const referentielState = {
  initialized: false,
  provinces: [],
  search: '',
  sortKey: 'nom',
  sortOrder: 'asc',
  selectedProvinceId: null,
};

const moduleNames = {
  dashboard: 'Tableau de bord',
  cartographie: 'Cartographie',
  referentiel: 'Référentiel administratif',
  gestion_referentiels: 'Gestion des Référentiels',
  sites: 'Sites FDSU',
  import: 'Import',
  export: 'Export',
  statistiques: 'Statistiques',
  utilisateurs: 'Utilisateurs',
  parametres: 'Paramètres',
};

const referentielElements = {
  searchInput: null,
  tableBody: null,
  detailContainer: null,
  headers: null,
};

const cartographyState = {
  initialized: false,
  map: null,
  layers: {},
  layerControl: null,
  layerStatus: {
    zones: null,
    collectivites: null,
  },
  infoElement: null,
  zonesMessageElement: null,
  zonesLayer: null,
  collectivitesLayer: null,
  selectedLayer: null,
};

const GOVERNANCE_TAB_DEFINITIONS = {
  referentiels: {
    label: 'Référentiels',
    description: 'Cycle de vie des référentiels territoriaux et métier.',
    emptyMessage: 'Aucun référentiel connecté.',
    columns: [
      { key: 'nom', label: 'Nom' },
      { key: 'type', label: 'Type' },
      { key: 'nombre_objets', label: "Nombre d'objets" },
      { key: 'source_officielle', label: 'Source officielle' },
      { key: 'version', label: 'Version' },
      { key: 'date_mise_a_jour', label: 'Date de mise à jour' },
      { key: 'statut', label: 'Statut', badge: true },
      { key: 'qualite', label: 'Qualité (%)' },
    ],
    statusOptions: ['Importé', 'Analysé', 'Validé', 'Publié'],
  },
  sources: {
    label: 'Sources officielles',
    description: 'Catalogage et traçabilité des producteurs de données.',
    emptyMessage: 'Aucune source officielle connectée.',
    columns: [
      { key: 'nom', label: 'Nom' },
      { key: 'url_officielle', label: 'URL officielle' },
      { key: 'type_donnees', label: 'Type de données' },
      { key: 'version', label: 'Version' },
      { key: 'derniere_synchronisation', label: 'Dernière synchronisation' },
      { key: 'responsable', label: 'Responsable' },
      { key: 'documentation', label: 'Documentation' },
    ],
    statusOptions: [],
  },
  imports: {
    label: 'Historique des imports',
    description: 'Suivi des fichiers importés et rapports techniques.',
    emptyMessage: "Aucun import disponible dans l'historique.",
    columns: [
      { key: 'fichier', label: 'Fichier importé' },
      { key: 'type', label: 'Type' },
      { key: 'utilisateur', label: 'Utilisateur' },
      { key: 'date', label: 'Date' },
      { key: 'duree', label: 'Durée' },
      { key: 'nombre_objets', label: "Nombre d'objets" },
      { key: 'erreurs', label: 'Erreurs' },
      { key: 'rapport', label: 'Rapport' },
      { key: 'statut', label: 'Statut', badge: true },
    ],
    statusOptions: ['Importé', 'Analysé', 'Validé', 'Publié'],
  },
  validation: {
    label: 'Validation',
    description: 'Traitement des anomalies de qualité et conformité.',
    emptyMessage: 'Aucun objet en attente de validation.',
    columns: [
      { key: 'objet', label: 'Objet à vérifier' },
      { key: 'doublons', label: 'Doublons' },
      { key: 'geometries_invalides', label: 'Géométries invalides' },
      { key: 'sans_code', label: 'Objets sans code' },
      { key: 'sans_rattachement', label: 'Sans rattachement administratif' },
      { key: 'statut', label: 'Statut', badge: true },
    ],
    statusOptions: ['À vérifier', 'Validé', 'Corrigé', 'Rejeté'],
  },
  comparaison: {
    label: 'Comparaison',
    description: 'Différences entre versions de référentiels.',
    emptyMessage: 'Aucune comparaison disponible.',
    columns: [
      { key: 'version_source', label: 'Version source' },
      { key: 'version_cible', label: 'Version cible' },
      { key: 'objets_ajoutes', label: 'Objets ajoutés' },
      { key: 'objets_supprimes', label: 'Objets supprimés' },
      { key: 'objets_modifies', label: 'Objets modifiés' },
      { key: 'geometries_modifiees', label: 'Géométries modifiées' },
      { key: 'attributs_modifies', label: 'Attributs modifiés' },
    ],
    statusOptions: [],
  },
  publication: {
    label: 'Publication',
    description: 'Pilotage du workflow import-analyse-validation-publication.',
    emptyMessage: 'Aucun lot prêt à publier.',
    columns: [
      { key: 'lot', label: 'Lot' },
      { key: 'import', label: 'Import' },
      { key: 'analyse', label: 'Analyse' },
      { key: 'validation', label: 'Validation' },
      { key: 'publication', label: 'Publication' },
      { key: 'statut', label: 'Statut', badge: true },
    ],
    statusOptions: ['Importé', 'Analysé', 'Validé', 'Publié'],
  },
  qualite: {
    label: 'Qualité des données',
    description: 'Indicateurs de complétude, cohérence et fiabilité.',
    emptyMessage: 'Aucun indicateur qualité disponible.',
    columns: [
      { key: 'referentiel', label: 'Référentiel' },
      { key: 'completude', label: 'Complétude' },
      { key: 'coherence', label: 'Cohérence' },
      { key: 'geometries_valides', label: 'Géométries valides' },
      { key: 'doublons', label: 'Doublons' },
      { key: 'qualite_globale', label: 'Qualité globale', badge: true },
    ],
    statusOptions: [],
  },
  journal: {
    label: 'Journal des opérations',
    description: 'Traçabilité chronologique des opérations utilisateurs.',
    emptyMessage: 'Aucune opération enregistrée.',
    columns: [
      { key: 'date', label: 'Date' },
      { key: 'utilisateur', label: 'Utilisateur' },
      { key: 'action', label: 'Action' },
      { key: 'referentiel', label: 'Référentiel' },
      { key: 'resultat', label: 'Résultat', badge: true },
    ],
    statusOptions: [],
  },
  normalisation: {
    label: 'Normalisation',
    description: 'Préparation staging et restitution des résultats du moteur.',
    emptyMessage: 'Aucun résultat de normalisation disponible.',
    columns: [
      { key: 'source', label: 'Source' },
      { key: 'entites_analysees', label: 'Entités analysées' },
      { key: 'score_qualite', label: 'Score qualité' },
      { key: 'erreurs', label: 'Erreurs' },
      { key: 'doublons', label: 'Doublons' },
      { key: 'orphelines', label: 'Orphelines' },
      { key: 'rapport', label: 'Rapport', badge: true },
    ],
    statusOptions: [],
  },
};

const governanceState = {
  initialized: false,
  activeTab: 'referentiels',
  search: '',
  statusFilter: '',
  page: 1,
  pageSize: 10,
  viewState: 'empty',
  selectedRecord: null,
  dataByTab: {},
  normalization: {
    summary: null,
    byLevel: [],
    reportPreview: '',
  },
};

const governanceElements = {
  panel: null,
  kpis: null,
  tabs: null,
  searchInput: null,
  statusFilter: null,
  pageSize: null,
  actions: null,
  tableHead: null,
  tableBody: null,
  pageInfo: null,
  prevButton: null,
  nextButton: null,
  detailTitle: null,
  detailBody: null,
  flow: null,
  states: null,
  normalizationSummaryGrid: null,
  normalizationLevelStats: null,
  normalizationReportPreview: null,
};

function setActiveModule(moduleKey) {
  navigationItems.forEach((item) => {
    item.classList.toggle('active', item.dataset.module === moduleKey);
  });

  panels.forEach((panel) => {
    panel.classList.toggle('hidden', panel.dataset.module !== moduleKey);
  });

  pageTitle.textContent = moduleNames[moduleKey] || 'Tableau de bord';
  pageContext.textContent = `Module : ${moduleNames[moduleKey] || 'Tableau de bord'}`;
  window.location.hash = moduleKey;

  if (moduleKey === 'dashboard') {
    initializeDashboard();
  }

  if (moduleKey === 'referentiel') {
    initializeReferentielModule();
  }

  if (moduleKey === 'cartographie') {
    initializeCartographyModule();
    if (cartographyState.map) {
      window.setTimeout(() => cartographyState.map.invalidateSize(), 0);
    }
  }

  if (moduleKey === 'gestion_referentiels') {
    initializeGovernanceModule();
  }
}

function initializeDashboard() {
  if (dashboardState.initialized) {
    return;
  }

  getDashboardStats();
  getDatabaseStatus();
  getLastImports();
  getZones();
  dashboardState.initialized = true;
}

function initializeReferentielModule() {
  if (referentielState.initialized) {
    return;
  }

  referentielElements.searchInput = document.querySelector('#province-search');
  referentielElements.tableBody = document.querySelector('#province-table-body');
  referentielElements.detailContainer = document.querySelector('#province-detail');
  referentielElements.headers = document.querySelectorAll('.province-table th button');

  if (!referentielElements.searchInput || !referentielElements.tableBody || !referentielElements.detailContainer) {
    return;
  }

  referentielElements.searchInput.addEventListener('input', () => {
    referentielState.search = referentielElements.searchInput.value.trim().toLowerCase();
    renderProvinceTable();
  });

  referentielElements.headers.forEach((button) => {
    button.addEventListener('click', () => {
      const key = button.dataset.key;
      if (!key) return;

      if (referentielState.sortKey === key) {
        referentielState.sortOrder = referentielState.sortOrder === 'asc' ? 'desc' : 'asc';
      } else {
        referentielState.sortKey = key;
        referentielState.sortOrder = 'asc';
      }
      renderProvinceTable();
      updateSortIndicators();
    });
  });

  referentielElements.tableBody.addEventListener('click', (event) => {
    const row = event.target.closest('tr[data-id]');
    if (!row) return;
    const provinceId = Number(row.dataset.id);
    referentielState.selectedProvinceId = provinceId;
    renderProvinceTable();
    renderProvinceDetails();
  });

  fetchProvinces();
  referentielState.initialized = true;
}

function initializeCartographyModule() {
  if (cartographyState.initialized) {
    return;
  }

  if (typeof L === 'undefined') {
    showZonesMessage('Couche Zones FDSU non disponible.');
    return;
  }

  const mapElement = document.querySelector('#map');
  const layerList = document.querySelector('#layer-list');
  const zoomAutoButton = document.querySelector('#zoom-auto');
  cartographyState.infoElement = document.querySelector('#carto-info');
  cartographyState.zonesMessageElement = document.querySelector('#zones-message');

  if (!mapElement || !layerList || !zoomAutoButton || !cartographyState.infoElement || !cartographyState.zonesMessageElement) {
    return;
  }

  if (cartographyState.map) {
    cartographyState.map.invalidateSize();
    loadZonesFdsuLayer();
    return;
  }

  cartographyState.map = L.map(mapElement, {
    center: [0.0, 25.0],
    zoom: 5,
    minZoom: 3,
    maxZoom: 12,
  });

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(cartographyState.map);

  cartographyState.layers = {
    zones: L.geoJSON(null, {
      style: styleZoneFeature,
      onEachFeature: (feature, layer) => onGeoEachFeature(feature, layer, 'zones'),
    }),
    collectivites: L.geoJSON(null, {
      style: styleCollectivitesFeature,
      onEachFeature: (feature, layer) => onGeoEachFeature(feature, layer, 'collectivites'),
    }),
    provinces: L.geoJSON(null),
    territoires: L.geoJSON(null),
    villes: L.geoJSON(null),
    communes: L.geoJSON(null),
    secteurs: L.geoJSON(null),
    chefferies: L.geoJSON(null),
    groupements: L.geoJSON(null),
    villages: L.geoJSON(null),
    sites: L.geoJSON(null),
    missions: L.geoJSON(null),
  };

  cartographyState.layerControl = L.control.layers(
    {},
    {
      'Zones FDSU': cartographyState.layers.zones,
      'Collectivités': cartographyState.layers.collectivites,
    },
    { collapsed: false }
  ).addTo(cartographyState.map);

  setupLayerControls(layerList);
  setupMapInteractions();
  zoomAutoButton.addEventListener('click', fitMapToZonesOrRdc);
  fitMapToRdc();
  loadGeneratedLayer({
    layerKey: 'zones',
    filePath: '/geodata/zones_fdsu.geojson',
    emptyMessage: 'Couche non disponible.',
    fallbackMessage: 'Couche non disponible.',
    visibleByDefault: true,
  });
  loadGeneratedLayer({
    layerKey: 'collectivites',
    filePath: '/geodata/collectivites.geojson',
    emptyMessage: 'Couche non disponible.',
    fallbackMessage: 'Couche non disponible.',
    visibleByDefault: false,
  });
  cartographyState.initialized = true;
}

function loadGeneratedLayer({ layerKey, filePath, emptyMessage, fallbackMessage, visibleByDefault }) {
  if (!cartographyState.map || typeof L === 'undefined') {
    showZonesMessage(fallbackMessage);
    return;
  }

  fetchJson(filePath)
    .then((geojson) => {
      if (!geojson || !Array.isArray(geojson.features)) {
        cartographyState.layerStatus[layerKey] = false;
        updateLayerAvailabilityMessage(emptyMessage);
        return;
      }

      const geojsonLayer = cartographyState.layers[layerKey];
      if (!geojsonLayer) {
        showZonesMessage(emptyMessage);
        return;
      }

      geojsonLayer.clearLayers();
      geojsonLayer.addData(geojson);

      cartographyState[`${layerKey}Layer`] = geojsonLayer;
      cartographyState.layerStatus[layerKey] = true;

      if (document.querySelector(`input[data-layer="${layerKey}"]`)) {
        document.querySelector(`input[data-layer="${layerKey}"]`).checked = true;
      }

      if (visibleByDefault) {
        geojsonLayer.addTo(cartographyState.map);
      }

      const bounds = geojsonLayer.getBounds();
      const zonesLoaded = Boolean(cartographyState.zonesLayer && cartographyState.zonesLayer.getLayers().length > 0);
      if (bounds.isValid() && (layerKey === 'zones' || !zonesLoaded)) {
        cartographyState.map.fitBounds(bounds, { padding: [20, 20] });
      } else if (!zonesLoaded && layerKey === 'collectivites' && bounds.isValid()) {
        cartographyState.map.fitBounds(bounds, { padding: [20, 20] });
      } else if (layerKey === 'zones' && !bounds.isValid()) {
        fitMapToRdc();
      }

      updateLayerAvailabilityMessage(emptyMessage);
    })
    .catch(() => {
      cartographyState.layerStatus[layerKey] = false;
      updateLayerAvailabilityMessage(emptyMessage);
    });
}

function styleCollectivitesFeature() {
  const outlineColor = getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#94a3b8';
  return {
    color: outlineColor,
    weight: 1,
    opacity: 1,
    fillColor: outlineColor,
    fillOpacity: 0.08,
  };
}

function styleZoneFeature(feature) {
  const zoneCode = getZoneCode(feature);
  const zoneStyle = getZoneStyle(zoneCode);

  return {
    color: zoneStyle.color,
    weight: 2,
    opacity: 1,
    fillColor: zoneStyle.fillColor,
    fillOpacity: 0.28,
  };
}

function getZoneStyle(zoneCode) {
  const resolveColor = (variableName) => getComputedStyle(document.documentElement).getPropertyValue(variableName).trim() || '#94a3b8';

  const palette = {
    ND: { color: resolveColor('--zone-nd'), fillColor: resolveColor('--zone-nd') },
    OT: { color: resolveColor('--zone-ot'), fillColor: resolveColor('--zone-ot') },
    CE: { color: resolveColor('--zone-ce'), fillColor: resolveColor('--zone-ce') },
    SD: { color: resolveColor('--zone-sd'), fillColor: resolveColor('--zone-sd') },
    ET: { color: resolveColor('--zone-et'), fillColor: resolveColor('--zone-et') },
  };

  return palette[zoneCode] || { color: resolveColor('--text-muted'), fillColor: resolveColor('--text-muted') };
}

function getZoneCode(feature) {
  const properties = feature?.properties || {};
  const candidates = [
    properties.code,
    properties.zone,
    properties.zone_code,
    properties.zoneCode,
    properties.nom,
    properties.name,
    properties.libelle,
  ];

  for (const candidate of candidates) {
    const normalized = String(candidate || '').trim().toUpperCase();
    if (['ND', 'OT', 'CE', 'SD', 'ET'].includes(normalized)) {
      return normalized;
    }
  }

  return 'ND';
}

function onGeoEachFeature(feature, layer, layerKey) {
  if (!layer) return;

  layer.on('click', () => {
    if (cartographyState.selectedLayer && cartographyState.selectedLayer.setStyle) {
      cartographyState.selectedLayer.setStyle({
        weight: 2,
        opacity: 1,
        fillOpacity: 0.28,
      });
    }

    cartographyState.selectedLayer = layer;
    layer.setStyle({
      weight: 3,
      opacity: 1,
      fillOpacity: 0.4,
    });

    if (layer.bringToFront) {
      layer.bringToFront();
    }

    renderFeatureDetails(feature, layerKey);
  });
}

function renderFeatureDetails(feature, layerKey) {
  if (!cartographyState.infoElement) return;

  const properties = feature?.properties || {};
  const code = getFeatureProperty(properties, ['code', 'zone', 'zone_code', 'zoneCode']);
  const name = getFeatureProperty(properties, ['nom', 'name', 'libelle']);
  const provinceCount = getFeatureProperty(properties, ['nb_provinces', 'nombre_provinces', 'province_count']);
  const description = getFeatureProperty(properties, ['description', 'desc', 'commentaire']);

  const attributes = Object.entries(properties)
    .filter(([, value]) => value !== null && value !== undefined && String(value).trim() !== '')
    .map(([key, value]) => `<div class="detail-row"><span>${escapeHtml(key)}</span><strong>${escapeHtml(formatAttributeValue(value))}</strong></div>`)
    .join('');

  cartographyState.infoElement.innerHTML = `
    <p class="zone-detail-label">Type de couche</p>
    <p class="zone-detail-value">${escapeHtml(layerKey === 'zones' ? 'Zones FDSU' : 'Collectivités')}</p>
    <p class="zone-detail-label">Code</p>
    <p class="zone-detail-value">${escapeHtml(code)}</p>
    <p class="zone-detail-label">Nom</p>
    <p class="zone-detail-value">${escapeHtml(name)}</p>
    <p class="zone-detail-label">Nombre de provinces</p>
    <p class="zone-detail-value">${escapeHtml(provinceCount)}</p>
    <p class="zone-detail-label">Description</p>
    <p class="zone-detail-value">${escapeHtml(description)}</p>
    <div class="detail-attributes">
      <p class="zone-detail-label">Attributs extraits</p>
      ${attributes || '<p class="zone-detail-empty">Non disponible</p>'}
    </div>
  `;
}

function getFeatureProperty(properties, keys) {
  for (const key of keys) {
    const value = properties?.[key];
    if (value !== null && value !== undefined && String(value).trim() !== '') {
      return String(value);
    }
  }

  return 'Non disponible';
}

function showZonesMessage(message) {
  if (!cartographyState.zonesMessageElement) return;
  cartographyState.zonesMessageElement.textContent = message || '';
}

function updateLayerAvailabilityMessage(fallbackMessage) {
  const zonesAvailable = cartographyState.layerStatus.zones;
  const collectivitesAvailable = cartographyState.layerStatus.collectivites;

  if (zonesAvailable === false || collectivitesAvailable === false) {
    showZonesMessage(fallbackMessage);
    return;
  }

  if (zonesAvailable === true && collectivitesAvailable === true) {
    showZonesMessage('');
    return;
  }

  showZonesMessage('');
}

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function formatAttributeValue(value) {
  if (value === null || value === undefined) {
    return 'Non disponible';
  }

  if (typeof value === 'string') {
    return value;
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function setupLayerControls(layerList) {
  layerList.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
    checkbox.addEventListener('change', () => {
      const layerKey = checkbox.dataset.layer;
      const layer = cartographyState.layers[layerKey];
      if (!layer || !cartographyState.map) return;

      if ((layerKey === 'zones' || layerKey === 'collectivites') && layer.getLayers().length === 0) {
        checkbox.checked = false;
        showZonesMessage('Couche non disponible.');
        return;
      }

      if (checkbox.checked) {
        layer.addTo(cartographyState.map);
      } else {
        cartographyState.map.removeLayer(layer);
      }
    });
  });
}

function setupMapInteractions() {
  if (!cartographyState.map) return;
  cartographyState.map.on('click', () => {
    if (cartographyState.infoElement) {
      cartographyState.infoElement.innerHTML = '<p class="zone-detail-empty">Sélectionnez un objet pour afficher ses informations.</p>';
    }
  });
}

function fitMapToZonesOrRdc() {
  if (!cartographyState.map) return;

  if (cartographyState.zonesLayer) {
    const bounds = cartographyState.zonesLayer.getBounds();
    if (bounds.isValid()) {
      cartographyState.map.fitBounds(bounds, { padding: [20, 20] });
      return;
    }
  }

  fitMapToRdc();
}

function fitMapToRdc() {
  if (!cartographyState.map) return;
  const bounds = L.latLngBounds([[-13.45, 12.2], [5.4, 31.3]]);
  cartographyState.map.fitBounds(bounds, { padding: [20, 20] });
}

function initializeGovernanceModule() {
  if (!governanceState.initialized) {
    governanceElements.panel = document.querySelector('#gestion-referentiels-panel');
    governanceElements.kpis = document.querySelector('#governance-kpis');
    governanceElements.tabs = document.querySelector('#governance-tabs');
    governanceElements.searchInput = document.querySelector('#governance-search');
    governanceElements.statusFilter = document.querySelector('#governance-status-filter');
    governanceElements.pageSize = document.querySelector('#governance-page-size');
    governanceElements.actions = document.querySelector('#governance-actions');
    governanceElements.tableHead = document.querySelector('#governance-table-head');
    governanceElements.tableBody = document.querySelector('#governance-table-body');
    governanceElements.pageInfo = document.querySelector('#governance-page-info');
    governanceElements.prevButton = document.querySelector('#governance-prev');
    governanceElements.nextButton = document.querySelector('#governance-next');
    governanceElements.detailTitle = document.querySelector('#governance-detail-title');
    governanceElements.detailBody = document.querySelector('#governance-detail-body');
    governanceElements.flow = document.querySelector('#publication-flow');
    governanceElements.states = document.querySelectorAll('.governance-state');
    governanceElements.normalizationSummaryGrid = document.querySelector('#normalization-summary-grid');
    governanceElements.normalizationLevelStats = document.querySelector('#normalization-level-stats');
    governanceElements.normalizationReportPreview = document.querySelector('#normalization-report-preview');

    if (!governanceElements.panel || !governanceElements.tabs || !governanceElements.tableHead || !governanceElements.tableBody) {
      return;
    }

    seedGovernanceModuleData();
    bindGovernanceEvents();
    renderGovernanceKpis();
    renderGovernanceActions();
    renderPublicationFlow();
    renderNormalizationHub();
    governanceState.initialized = true;
  }

  renderGovernanceTabs();
  updateGovernanceStatusFilter();
  renderGovernanceTable();
  renderGovernanceDetailPanel();
  setGovernanceViewState('empty');
}

function bindGovernanceEvents() {
  governanceElements.searchInput?.addEventListener('input', () => {
    governanceState.search = governanceElements.searchInput.value.trim().toLowerCase();
    governanceState.page = 1;
    renderGovernanceTable();
  });

  governanceElements.statusFilter?.addEventListener('change', () => {
    governanceState.statusFilter = governanceElements.statusFilter.value;
    governanceState.page = 1;
    renderGovernanceTable();
  });

  governanceElements.pageSize?.addEventListener('change', () => {
    governanceState.pageSize = Number(governanceElements.pageSize.value) || 10;
    governanceState.page = 1;
    renderGovernanceTable();
  });

  governanceElements.prevButton?.addEventListener('click', () => {
    if (governanceState.page <= 1) return;
    governanceState.page -= 1;
    renderGovernanceTable();
  });

  governanceElements.nextButton?.addEventListener('click', () => {
    const totalPages = getGovernanceTotalPages();
    if (governanceState.page >= totalPages) return;
    governanceState.page += 1;
    renderGovernanceTable();
  });
}

function renderGovernanceKpis() {
  if (!governanceElements.kpis) return;

  const kpis = [
    { label: 'Référentiels suivis', value: 'Staging prêt' },
    { label: 'Sources officielles', value: 'Adaptateurs prêts' },
    { label: 'Objets à valider', value: formatGovernanceMetric(governanceState.normalization.summary?.orphans) },
    { label: 'Qualité globale', value: formatGovernanceMetric(governanceState.normalization.summary?.qualityScore) },
  ];

  governanceElements.kpis.innerHTML = kpis
    .map((kpi) => `
      <article class="governance-kpi-card">
        <p class="summary-label">${escapeHtml(kpi.label)}</p>
        <p class="summary-value">${escapeHtml(kpi.value)}</p>
      </article>
    `)
    .join('');
}

function renderGovernanceTabs() {
  if (!governanceElements.tabs) return;

  governanceElements.tabs.innerHTML = Object.entries(GOVERNANCE_TAB_DEFINITIONS)
    .map(([key, definition]) => {
      const active = governanceState.activeTab === key;
      return `
        <button
          type="button"
          class="governance-tab ${active ? 'active' : ''}"
          role="tab"
          aria-selected="${active ? 'true' : 'false'}"
          data-tab="${key}"
        >
          <span class="governance-tab-label">${escapeHtml(definition.label)}</span>
          <span class="governance-tab-description">${escapeHtml(definition.description)}</span>
        </button>
      `;
    })
    .join('');

  governanceElements.tabs.querySelectorAll('[data-tab]').forEach((button) => {
    button.addEventListener('click', () => {
      const tab = button.dataset.tab;
      if (!tab || tab === governanceState.activeTab) return;

      governanceState.activeTab = tab;
      governanceState.page = 1;
      governanceState.search = '';
      governanceState.statusFilter = '';
      governanceState.selectedRecord = null;

      if (governanceElements.searchInput) {
        governanceElements.searchInput.value = '';
      }

      renderGovernanceTabs();
      updateGovernanceStatusFilter();
      renderGovernanceTable();
      renderGovernanceDetailPanel();
      setGovernanceViewState('empty');
    });
  });
}

function updateGovernanceStatusFilter() {
  if (!governanceElements.statusFilter) return;

  const definition = GOVERNANCE_TAB_DEFINITIONS[governanceState.activeTab];
  const options = Array.isArray(definition?.statusOptions) ? definition.statusOptions : [];

  governanceElements.statusFilter.innerHTML = ['<option value="">Tous les statuts</option>']
    .concat(options.map((status) => `<option value="${escapeHtml(status)}">${escapeHtml(status)}</option>`))
    .join('');

  governanceElements.statusFilter.disabled = options.length === 0;
  governanceElements.statusFilter.value = governanceState.statusFilter;
}

function renderGovernanceActions() {
  if (!governanceElements.actions) return;

  const actions = ['Importer', 'Comparer', 'Valider', 'Publier', 'Exporter'];
  governanceElements.actions.innerHTML = actions
    .map((action) => `<button type="button" class="governance-action-button" disabled>${escapeHtml(action)}</button>`)
    .join('');
}

function seedGovernanceModuleData() {
  governanceState.normalization = {
    summary: {
      analyzedEntities: null,
      qualityScore: null,
      errors: null,
      duplicates: null,
      orphans: null,
      reportStatus: 'En attente de source',
    },
    byLevel: [],
    reportPreview: [
      '# Normalization Report',
      '',
      '- Source: En attente',
      '- Mode: staging only',
      '- Entités analysées: —',
      '- Score qualité: —',
    ].join('\n'),
  };

  governanceState.dataByTab.normalisation = [
    {
      id: 'normalization-engine',
      source: 'StagingEntity',
      entites_analysees: '—',
      score_qualite: '—',
      erreurs: '—',
      doublons: '—',
      orphelines: '—',
      rapport: 'Prêt',
    },
  ];

  governanceState.dataByTab.sources = [
    {
      id: 'source-excel-fdsu',
      nom: 'Excel FDSU',
      url_officielle: 'Fichier local de staging',
      type_donnees: 'Workbook',
      version: 'Contrat prêt',
      derniere_synchronisation: 'Non exécutée',
      responsable: 'Adaptateur ExcelFDSUAdapter',
      documentation: 'StagingEntity',
    },
    {
      id: 'source-kmz',
      nom: 'KMZ',
      url_officielle: 'Fichier local de staging',
      type_donnees: 'Placemark géospatial',
      version: 'Contrat prêt',
      derniere_synchronisation: 'Non exécutée',
      responsable: 'Adaptateur KMZAdapter',
      documentation: 'StagingEntity',
    },
    {
      id: 'source-ceni',
      nom: 'CENI',
      url_officielle: 'Métadonnées publiques CENI',
      type_donnees: 'Interface préparée',
      version: 'Interface',
      derniere_synchronisation: 'Non exécutée',
      responsable: 'CeniStagingAdapter',
      documentation: 'Interface sans implémentation complète',
    },
    {
      id: 'source-caid',
      nom: 'CAID',
      url_officielle: 'Source future',
      type_donnees: 'Interface préparée',
      version: 'Interface',
      derniere_synchronisation: 'Non exécutée',
      responsable: 'CaidStagingAdapter',
      documentation: 'Interface sans implémentation complète',
    },
    {
      id: 'source-ins',
      nom: 'INS',
      url_officielle: 'Source future',
      type_donnees: 'Interface préparée',
      version: 'Interface',
      derniere_synchronisation: 'Non exécutée',
      responsable: 'InsStagingAdapter',
      documentation: 'Interface sans implémentation complète',
    },
  ];
}

function renderNormalizationHub() {
  renderNormalizationSummary();
  renderNormalizationLevelStats();
  renderNormalizationReportPreview();
}

function renderNormalizationSummary() {
  if (!governanceElements.normalizationSummaryGrid) return;

  const summary = governanceState.normalization.summary || {};
  const cards = [
    { label: 'Entités analysées', value: formatGovernanceMetric(summary.analyzedEntities) },
    { label: 'Score de qualité', value: formatGovernanceMetric(summary.qualityScore) },
    { label: 'Erreurs', value: formatGovernanceMetric(summary.errors) },
    { label: 'Doublons', value: formatGovernanceMetric(summary.duplicates) },
    { label: 'Orphelines', value: formatGovernanceMetric(summary.orphans) },
    { label: 'Rapport', value: formatGovernanceMetric(summary.reportStatus) },
  ];

  governanceElements.normalizationSummaryGrid.innerHTML = cards
    .map((card) => `
      <article class="normalization-summary-card">
        <p class="summary-label">${escapeHtml(card.label)}</p>
        <p class="summary-value">${escapeHtml(card.value)}</p>
      </article>
    `)
    .join('');
}

function renderNormalizationLevelStats() {
  if (!governanceElements.normalizationLevelStats) return;

  const stats = governanceState.normalization.byLevel || [];
  if (stats.length === 0) {
    governanceElements.normalizationLevelStats.innerHTML = '<p class="normalization-empty">Aucune statistique de normalisation n\'a encore été calculée.</p>';
    return;
  }

  governanceElements.normalizationLevelStats.innerHTML = stats
    .map((entry) => `
      <div class="normalization-level-row">
        <span>${escapeHtml(entry.level)}</span>
        <strong>${escapeHtml(String(entry.value))}</strong>
      </div>
    `)
    .join('');
}

function renderNormalizationReportPreview() {
  if (!governanceElements.normalizationReportPreview) return;
  governanceElements.normalizationReportPreview.textContent = governanceState.normalization.reportPreview || 'Aucun rapport disponible.';
}

function renderPublicationFlow() {
  if (!governanceElements.flow) return;

  const flowSteps = ['Import', 'Analyse', 'Validation', 'Publication'];
  governanceElements.flow.innerHTML = flowSteps
    .map((step, index) => {
      const connector = index < flowSteps.length - 1 ? '<span class="flow-connector">↓</span>' : '';
      return `<div class="flow-step"><span>${escapeHtml(step)}</span>${connector}</div>`;
    })
    .join('');
}

function renderGovernanceTable() {
  const definition = GOVERNANCE_TAB_DEFINITIONS[governanceState.activeTab];
  if (!definition || !governanceElements.tableHead || !governanceElements.tableBody) return;

  governanceElements.tableHead.innerHTML = `
    <tr>
      ${definition.columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join('')}
    </tr>
  `;

  const rows = getGovernanceVisibleRows();
  if (rows.length === 0) {
    governanceElements.tableBody.innerHTML = `
      <tr>
        <td colspan="${definition.columns.length}" class="empty-state">${escapeHtml(definition.emptyMessage)}</td>
      </tr>
    `;
    updateGovernancePagination(0);
    return;
  }

  governanceElements.tableBody.innerHTML = rows
    .map((record, rowIndex) => {
      const id = record.id || `row-${rowIndex}`;
      const selected = governanceState.selectedRecord === String(id);
      const cells = definition.columns
        .map((column) => {
          const value = record?.[column.key];
          if (column.badge) {
            return `<td><span class="status-badge">${escapeHtml(formatGovernanceValue(value))}</span></td>`;
          }
          return `<td>${escapeHtml(formatGovernanceValue(value))}</td>`;
        })
        .join('');

      return `<tr data-record-id="${escapeHtml(String(id))}" class="${selected ? 'selected' : ''}">${cells}</tr>`;
    })
    .join('');

  governanceElements.tableBody.querySelectorAll('tr[data-record-id]').forEach((row) => {
    row.addEventListener('click', () => {
      governanceState.selectedRecord = row.dataset.recordId;
      renderGovernanceDetailPanel();
      governanceElements.tableBody.querySelectorAll('tr').forEach((item) => item.classList.remove('selected'));
      row.classList.add('selected');
      setGovernanceViewState('success');
    });
  });

  updateGovernancePagination(getGovernanceFilteredRows().length);
}

function getGovernanceRowsForActiveTab() {
  return Array.isArray(governanceState.dataByTab[governanceState.activeTab])
    ? governanceState.dataByTab[governanceState.activeTab]
    : [];
}

function getGovernanceFilteredRows() {
  const rows = getGovernanceRowsForActiveTab();

  return rows.filter((record) => {
    const textMatch = governanceState.search
      ? Object.values(record || {}).some((value) => String(value ?? '').toLowerCase().includes(governanceState.search))
      : true;

    if (!textMatch) {
      return false;
    }

    if (!governanceState.statusFilter) {
      return true;
    }

    return String(record?.statut ?? '').toLowerCase() === governanceState.statusFilter.toLowerCase();
  });
}

function getGovernanceVisibleRows() {
  const filtered = getGovernanceFilteredRows();
  const start = (governanceState.page - 1) * governanceState.pageSize;
  return filtered.slice(start, start + governanceState.pageSize);
}

function getGovernanceTotalPages() {
  const total = getGovernanceFilteredRows().length;
  return Math.max(1, Math.ceil(total / governanceState.pageSize));
}

function updateGovernancePagination(totalRows) {
  const totalPages = Math.max(1, Math.ceil(totalRows / governanceState.pageSize));
  governanceState.page = Math.min(governanceState.page, totalPages);

  if (governanceElements.pageInfo) {
    governanceElements.pageInfo.textContent = `Page ${governanceState.page} / ${totalPages}`;
  }

  if (governanceElements.prevButton) {
    governanceElements.prevButton.disabled = governanceState.page <= 1;
  }

  if (governanceElements.nextButton) {
    governanceElements.nextButton.disabled = governanceState.page >= totalPages;
  }
}

function renderGovernanceDetailPanel() {
  if (!governanceElements.detailTitle || !governanceElements.detailBody) return;

  if (!governanceState.selectedRecord) {
    governanceElements.detailTitle.textContent = 'Aucun élément sélectionné';
    governanceElements.detailBody.innerHTML = '<div class="empty-detail">Sélectionnez une ligne pour afficher la fiche détaillée.</div>';
    return;
  }

  governanceElements.detailTitle.textContent = `Élément ${governanceState.selectedRecord}`;
  governanceElements.detailBody.innerHTML = `
    <div class="detail-row"><span>Identifiant</span><strong>${escapeHtml(String(governanceState.selectedRecord))}</strong></div>
    <div class="detail-row"><span>État de connexion</span><strong>En attente de liaison API</strong></div>
    <div class="detail-row"><span>Détail</span><strong>Données non chargées</strong></div>
  `;
}

function setGovernanceViewState(stateKey) {
  governanceState.viewState = stateKey;
  governanceElements.states?.forEach((stateElement) => {
    stateElement.classList.toggle('hidden', stateElement.dataset.state !== stateKey);
  });
}

function formatGovernanceValue(value) {
  if (value === null || value === undefined || String(value).trim() === '') {
    return '—';
  }

  return String(value);
}

function formatGovernanceMetric(value) {
  if (value === null || value === undefined || String(value).trim() === '') {
    return 'En attente';
  }
  return String(value);
}

function fetchProvinces() {
  if (!referentielElements.tableBody) return;
  referentielElements.tableBody.innerHTML = '<tr><td colspan="7" class="empty-state">Chargement des provinces...</td></tr>';

  getProvinces()
    .then((provinces) => {
      referentielState.provinces = Array.isArray(provinces) ? provinces : [];
      referentielState.selectedProvinceId = referentielState.provinces.length > 0 ? referentielState.provinces[0].id : null;
      renderProvinceTable();
      renderProvinceDetails();
      updateSortIndicators();
    })
    .catch(() => {
      referentielElements.tableBody.innerHTML = '<tr><td colspan="7" class="empty-state">Impossible de charger les provinces. Vérifiez le serveur API.</td></tr>';
    });
}

function renderProvinceTable() {
  if (!referentielElements.tableBody) return;

  const filterValue = referentielState.search;
  const filtered = referentielState.provinces.filter((province) => {
    const text = `${province.nom} ${province.code} ${province.zone} ${province.chef_lieu || ''}`.toLowerCase();
    return text.includes(filterValue);
  });

  const sorted = filtered.slice().sort((a, b) => {
    const key = referentielState.sortKey;
    const valueA = normalizeValue(a[key]);
    const valueB = normalizeValue(b[key]);

    if (valueA < valueB) return referentielState.sortOrder === 'asc' ? -1 : 1;
    if (valueA > valueB) return referentielState.sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  if (sorted.length === 0) {
    referentielElements.tableBody.innerHTML = '<tr><td colspan="7" class="empty-state">Aucune province trouvée.</td></tr>';
    return;
  }

  referentielElements.tableBody.innerHTML = sorted
    .map((province) => {
      const isSelected = province.id === referentielState.selectedProvinceId;
      return `
        <tr data-id="${province.id}" class="${isSelected ? 'selected' : ''}">
          <td>${province.id}</td>
          <td>${province.nom || '—'}</td>
          <td>${province.code || '—'}</td>
          <td>${province.zone || '—'}</td>
          <td>${province.chef_lieu || '—'}</td>
          <td>${typeof province.population === 'number' ? province.population.toLocaleString('fr-FR') : '—'}</td>
          <td>${typeof province.superficie === 'number' ? province.superficie.toFixed(1) : '—'}</td>
        </tr>
      `;
    })
    .join('');
}

function normalizeValue(value) {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value.toLowerCase();
  return value;
}

function renderProvinceDetails() {
  if (!referentielElements.detailContainer) return;

  const province = referentielState.provinces.find((item) => item.id === referentielState.selectedProvinceId);
  if (!province) {
    referentielElements.detailContainer.innerHTML = '<div class="empty-detail">Sélectionnez une province pour afficher les détails.</div>';
    return;
  }

  referentielElements.detailContainer.innerHTML = `
    <div class="detail-row"><span>ID</span><strong>${province.id}</strong></div>
    <div class="detail-row"><span>Nom</span><strong>${province.nom || '—'}</strong></div>
    <div class="detail-row"><span>Code</span><strong>${province.code || '—'}</strong></div>
    <div class="detail-row"><span>Zone</span><strong>${province.zone || '—'}</strong></div>
    <div class="detail-row"><span>Chef-lieu</span><strong>${province.chef_lieu || '—'}</strong></div>
    <div class="detail-row"><span>Population</span><strong>${typeof province.population === 'number' ? province.population.toLocaleString('fr-FR') : '—'}</strong></div>
    <div class="detail-row"><span>Superficie</span><strong>${typeof province.superficie === 'number' ? province.superficie.toFixed(1) + ' km²' : '—'}</strong></div>
  `;
}

function getDashboardStats() {
  getCount('/provinces?limit=500').then(updateSummaryCard('stat-provinces'));
  getCount('/territoires?limit=500').then(updateSummaryCard('stat-territoires'));
  getCount('/collectivites?limit=500').then(updateSummaryCard('stat-collectivites'));
  getCount('/groupements?limit=500').then(updateSummaryCard('stat-groupements'));
  getCount('/villages?limit=500').then(updateSummaryCard('stat-villages'));
  getCount('/sites?limit=500').then(updateSummaryCard('stat-sites'));
  getCount('/missions?limit=500').then(updateSummaryCard('stat-missions'));
  getCount('/users?limit=500').then(updateSummaryCard('stat-utilisateurs'));
}

function getDatabaseStatus() {
  const apiStatusEl = document.querySelector('#api-status');
  const dbStatusEl = document.querySelector('#db-status');
  const dbSyncEl = document.querySelector('#db-sync');

  getProvinces()
    .then((data) => {
      if (Array.isArray(data)) {
        apiStatusEl.textContent = 'Disponible';
        dbStatusEl.textContent = 'Disponible';
        dbSyncEl.textContent = 'Non disponible';
      } else {
        apiStatusEl.textContent = 'Non disponible';
        dbStatusEl.textContent = 'Non disponible';
        dbSyncEl.textContent = 'Non disponible';
      }
    })
    .catch(() => {
      apiStatusEl.textContent = 'Non disponible';
      dbStatusEl.textContent = 'Non disponible';
      dbSyncEl.textContent = 'Non disponible';
    });
}

function getLastImports() {
  const lastImportEl = document.querySelector('#last-import');
  if (!lastImportEl) return;
  lastImportEl.textContent = 'Non disponible';
}

function getZones() {
  getProvinces()
    .then((provinces) => {
      const counts = { ND: 0, SD: 0, CE: 0, OT: 0, ET: 0 };
      if (Array.isArray(provinces)) {
        provinces.forEach((province) => {
          const zone = String(province.zone || '').toUpperCase();
          if (counts[zone] !== undefined) {
            counts[zone] += 1;
          }
        });
      }
      updateZoneCount('ND', counts.ND);
      updateZoneCount('SD', counts.SD);
      updateZoneCount('CE', counts.CE);
      updateZoneCount('OT', counts.OT);
      updateZoneCount('ET', counts.ET);
    })
    .catch(() => {
      updateZoneCount('ND', 0);
      updateZoneCount('SD', 0);
      updateZoneCount('CE', 0);
      updateZoneCount('OT', 0);
      updateZoneCount('ET', 0);
    });
}

function getProvinces() {
  return fetchJson('/provinces?limit=500');
}

function getCount(endpoint) {
  return fetchJson(endpoint).then((data) => {
    if (Array.isArray(data)) {
      return data.length;
    }
    return 0;
  });
}

function fetchJson(endpoint) {
  const url = new URL(endpoint, API_BASE).toString();

  return fetch(url)
    .then((response) => {
      if (!response.ok) {
        return Promise.reject(new Error('Route non disponible'));
      }
      return response.json();
    })
    .catch(() => {
      return Promise.resolve(null);
    });
}

function updateSummaryCard(id) {
  return (value) => {
    const el = document.querySelector(`#${id}`);
    if (!el) return;
    if (typeof value === 'number' && value >= 0) {
      el.textContent = value.toLocaleString('fr-FR');
    } else {
      el.textContent = 'Non disponible';
    }
  };
}

function updateZoneCount(zone, value) {
  const element = document.querySelector(`#zone-${zone}`);
  if (!element) return;
  element.textContent = typeof value === 'number' ? value.toString() : '0';
}

function updateSortIndicators() {
  referentielElements.headers?.forEach((button) => {
    const key = button.dataset.key;
    if (!key) return;

    const indicator = button.querySelector('.sort-indicator');
    if (indicator) {
      indicator.remove();
    }

    if (key === referentielState.sortKey) {
      const arrow = document.createElement('span');
      arrow.className = 'sort-indicator';
      arrow.textContent = referentielState.sortOrder === 'asc' ? '▲' : '▼';
      button.appendChild(arrow);
    }
  });
}

navigationItems.forEach((item) => {
  item.addEventListener('click', () => {
    setActiveModule(item.dataset.module);
  });
});

const quickActions = document.querySelectorAll('.quick-actions button');
quickActions.forEach((button) => {
  button.addEventListener('click', () => {
    setActiveModule(button.dataset.module);
  });
});

const defaultModule = window.location.hash.replace('#', '') || 'dashboard';
setActiveModule(defaultModule);

window.addEventListener('load', () => {
  if (window.location.hash.replace('#', '') === 'cartographie') {
    initializeCartographyModule();
  }
});
