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
  explorateur_sources: 'Explorateur de Sources',
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

const sourceExplorerState = {
  initialized: false,
  report: null,
};

const sourceExplorerElements = {
  panel: null,
  fileInput: null,
  sourcePath: null,
  sourceFormat: null,
  objectCount: null,
  fieldCount: null,
  folderCount: null,
  extractButton: null,
  catalogBody: null,
  dictionaryBody: null,
  tagsContainer: null,
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
  detailMode: 'consultation',
  selectedRecord: null,
  selectedExplorerNodeId: null,
  expandedExplorerNodeIds: new Set(),
  dataByTab: {},
  report: null,
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

  if (moduleKey === 'explorateur_sources') {
    initializeSourceExplorerModule();
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
    loadNationalAdministrativeReport();
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
      governanceState.selectedExplorerNodeId = governanceState.report?.root?.children[0]?.id || governanceState.report?.root?.id || null;

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

function loadNationalAdministrativeReport() {
  Promise.all([getProvinces(), getTerritoires(), getCollectivites(), getGroupements(), getVillages()])
    .then(([provinces, territoires, collectivites, groupements, villages]) => {
      const report = buildNationalAdministrativeReport({
        provinces: Array.isArray(provinces) ? provinces : [],
        territoires: Array.isArray(territoires) ? territoires : [],
        collectivites: Array.isArray(collectivites) ? collectivites : [],
        groupements: Array.isArray(groupements) ? groupements : [],
        villages: Array.isArray(villages) ? villages : [],
      });

      governanceState.report = report;
      governanceState.normalization = report.normalization;
      governanceState.dataByTab.referentiels = report.referentielRows;
      governanceState.dataByTab.validation = report.validationRows;
      governanceState.dataByTab.qualite = report.qualityRows;
      governanceState.dataByTab.normalisation = [report.normalizationRow];
      governanceState.report = decorateExplorerReport(report);
      governanceState.expandedExplorerNodeIds = new Set([governanceState.report.root.id]);
      governanceState.report.root.children.forEach((child) => governanceState.expandedExplorerNodeIds.add(child.id));
      governanceState.selectedExplorerNodeId = governanceState.report.root.children[0]?.id || governanceState.report.root.id;

      renderGovernanceKpis();
      renderNormalizationHub();
      renderGovernanceTabs();
      updateGovernanceStatusFilter();
      governanceState.page = 1;
      governanceState.selectedRecord = null;
      renderGovernanceTable();
      renderGovernanceDetailPanel();
    })
    .catch(() => {
      governanceState.report = null;
    });
}

function decorateExplorerReport(report) {
  const statistics = report.statistics || {};
  const byLevel = statistics.byLevel || {};
  const quality = report.quality || {};
  const anomalies = Array.isArray(report.anomalies) ? report.anomalies : [];
  const root = decorateExplorerNode(report.tree, null, {
    statistics,
    byLevel,
    quality,
    anomalies,
    path: [],
  });
  const nodesById = {};
  indexExplorerNodes(root, nodesById);

  return {
    ...report,
    root,
    nodesById,
  };
}

function decorateExplorerNode(node, parent, context) {
  const level = String(node.level || 'unknown');
  const label = String(node.label || '—');
  const path = [...context.path, label];
  const children = Array.isArray(node.children) ? node.children : [];
  const decoratedChildren = children.map((child) => decorateExplorerNode(child, { id: node.id || buildExplorerNodeId(parent, level, label, node.code) }, { ...context, path }));
  const id = node.id || buildExplorerNodeId(parent, level, label, node.code);

  return {
    id,
    parentId: parent ? parent.id : null,
    level,
    label,
    code: node.code || null,
    count: node.count || 0,
    icon: getExplorerIcon(level),
    typeLabel: getExplorerTypeLabel(level),
    adminLevel: getExplorerAdminLevel(level),
    qualityBadge: getExplorerQualityBadge(level, context.quality, context.anomalies),
    qualityClass: getExplorerQualityClass(level, context.quality, context.anomalies),
    status: getExplorerStatus(level, context.anomalies),
    source: level === 'rdc' ? 'Référentiel national consolidé' : 'API locale consolidée',
    informationAvailable: getExplorerInformationAvailable(level),
    hierarchyPath: path,
    hierarchyLabel: path.join(' > '),
    statistics: buildExplorerNodeStatistics(level, context.statistics, context.byLevel, decoratedChildren.length, node.count),
    children: decoratedChildren,
  };
}

function indexExplorerNodes(node, nodesById) {
  nodesById[node.id] = node;
  node.children.forEach((child) => indexExplorerNodes(child, nodesById));
}

function buildExplorerNodeId(parent, level, label, code) {
  const suffix = String(code || label || 'node').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'node';
  return parent ? `${parent.id}--${level}--${suffix}` : `${level}--${suffix}`;
}

function buildExplorerNodeStatistics(level, statistics, byLevel, childCount, nodeCount) {
  const count = typeof nodeCount === 'number' && nodeCount > 0
    ? nodeCount
    : level === 'rdc'
      ? statistics.entityCount || 0
      : byLevel[level] || childCount || 0;

  return {
    count,
    children: childCount,
    total: statistics.entityCount || 0,
    orphans: statistics.orphanCount || 0,
    qualityScore: statistics.qualityScore || 0,
  };
}

function getExplorerQualityBadge(level, quality, anomalies) {
  const score = getExplorerQualityScore(level, quality, anomalies);
  if (score >= 85) return `Excellent · ${score}%`;
  if (score >= 70) return `Bon · ${score}%`;
  if (score >= 50) return `À surveiller · ${score}%`;
  return `Critique · ${score}%`;
}

function getExplorerQualityClass(level, quality, anomalies) {
  const score = getExplorerQualityScore(level, quality, anomalies);
  if (score >= 85) return 'quality-high';
  if (score >= 70) return 'quality-medium';
  if (score >= 50) return 'quality-warning';
  return 'quality-low';
}

function getExplorerQualityScore(level, quality, anomalies) {
  const base = typeof quality.qualityScore === 'number' ? quality.qualityScore : 0;
  const errors = anomalies.filter((anomaly) => String(anomaly.level || '').toLowerCase() === String(level || '').toLowerCase() && anomaly.severity === 'error').length;
  return Math.max(0, Math.min(100, Math.round(base - (errors * 2))));
}

function getExplorerStatus(level, anomalies) {
  const hasError = anomalies.some((anomaly) => String(anomaly.level || '').toLowerCase() === String(level || '').toLowerCase() && anomaly.severity === 'error');
  return hasError ? 'À vérifier' : 'Publié';
}

function getExplorerIcon(level) {
  const icons = {
    rdc: '🇨🇩',
    zone_fdsu: '🟩',
    province: '🟦',
    territoire: '🟨',
    ville: '🏙',
    commune: '🏛',
    commune_urbaine: '🏛',
    commune_rurale: '🏛',
    secteur: '🌿',
    chefferie: '👑',
    groupement: '📍',
    village: '🏘',
  };

  return icons[String(level || '').toLowerCase()] || '•';
}

function getExplorerTypeLabel(level) {
  const labels = {
    rdc: 'État',
    zone_fdsu: 'Zone',
    province: 'Province',
    territoire: 'Territoire',
    ville: 'Ville',
    commune: 'Commune',
    commune_urbaine: 'Commune urbaine',
    commune_rurale: 'Commune rurale',
    secteur: 'Secteur',
    chefferie: 'Chefferie',
    groupement: 'Groupement',
    village: 'Village',
  };

  return labels[String(level || '').toLowerCase()] || 'Niveau';
}

function getExplorerAdminLevel(level) {
  const levels = {
    rdc: 'National',
    zone_fdsu: 'Zone FDSU',
    province: 'Niveau 1',
    territoire: 'Niveau 2',
    ville: 'Niveau 2',
    commune: 'Niveau 3',
    commune_urbaine: 'Niveau 3',
    commune_rurale: 'Niveau 3',
    secteur: 'Niveau 3',
    chefferie: 'Niveau 3',
    groupement: 'Niveau 4',
    village: 'Niveau 5',
  };

  return levels[String(level || '').toLowerCase()] || 'Niveau inconnu';
}

function getExplorerInformationAvailable(level) {
  const availability = {
    rdc: ['hiérarchie', 'statistiques', 'qualité', 'statut', 'source'],
    zone_fdsu: ['nom', 'type', 'niveau administratif', 'hiérarchie', 'statistiques', 'qualité', 'statut', 'source'],
    province: ['nom', 'type', 'niveau administratif', 'hiérarchie', 'statistiques', 'qualité', 'statut', 'source'],
    territoire: ['nom', 'type', 'niveau administratif', 'hiérarchie', 'statistiques', 'qualité', 'statut', 'source'],
    ville: ['nom', 'type', 'niveau administratif', 'hiérarchie', 'statistiques', 'qualité', 'statut', 'source'],
    commune: ['nom', 'type', 'niveau administratif', 'hiérarchie', 'statistiques', 'qualité', 'statut', 'source'],
    secteur: ['nom', 'type', 'niveau administratif', 'hiérarchie', 'statistiques', 'qualité', 'statut', 'source'],
    chefferie: ['nom', 'type', 'niveau administratif', 'hiérarchie', 'statistiques', 'qualité', 'statut', 'source'],
    groupement: ['nom', 'type', 'niveau administratif', 'hiérarchie', 'statistiques', 'qualité', 'statut', 'source'],
    village: ['nom', 'type', 'niveau administratif', 'hiérarchie', 'statistiques', 'qualité', 'statut', 'source'],
  };

  return availability[String(level || '').toLowerCase()] || ['nom', 'type', 'hiérarchie'];
}

function getExplorerSearchTerm() {
  return governanceState.search.trim().toLowerCase();
}

function isExplorerNodeVisible(node, searchTerm) {
  if (!searchTerm) return true;
  const haystack = [node.label, node.code, node.level, node.typeLabel, node.adminLevel, node.hierarchyLabel].join(' ').toLowerCase();
  if (haystack.includes(searchTerm)) {
    return true;
  }
  return node.children.some((child) => isExplorerNodeVisible(child, searchTerm));
}

function getExplorerVisibleNodes() {
  const report = governanceState.report;
  if (!report?.root) return [];

  const searchTerm = getExplorerSearchTerm();
  const rows = [];

  function visit(node, depth = 0) {
    if (!isExplorerNodeVisible(node, searchTerm)) {
      return;
    }

    rows.push({ node, depth });
    const shouldShowChildren = !searchTerm || governanceState.expandedExplorerNodeIds.has(node.id) || node.id === report.root.id || node.children.some((child) => isExplorerNodeVisible(child, searchTerm));
    if (shouldShowChildren) {
      node.children.forEach((child) => visit(child, depth + 1));
    }
  }

  visit(report.root);
  return rows;
}

function getExplorerNodeById(nodeId) {
  return governanceState.report?.nodesById?.[nodeId] || null;
}

function isExplorerExpanded(nodeId) {
  return governanceState.expandedExplorerNodeIds.has(nodeId);
}

function setExplorerExpanded(nodeId, expanded) {
  const next = new Set(governanceState.expandedExplorerNodeIds);
  if (expanded) {
    next.add(nodeId);
  } else {
    next.delete(nodeId);
  }
  governanceState.expandedExplorerNodeIds = next;
}

function toggleExplorerNode(nodeId) {
  setExplorerExpanded(nodeId, !isExplorerExpanded(nodeId));
  renderGovernanceTable();
}

function selectExplorerNode(nodeId) {
  governanceState.selectedExplorerNodeId = nodeId;
  governanceState.selectedRecord = nodeId;
  setGovernanceViewState('success');
  renderGovernanceDetailPanel();
  renderGovernanceTable();
}

function selectExplorerPath(nodeId) {
  const node = getExplorerNodeById(nodeId);
  if (!node) return;

  let current = node;
  while (current) {
    setExplorerExpanded(current.id, true);
    current = current.parentId ? getExplorerNodeById(current.parentId) : null;
  }

  selectExplorerNode(nodeId);
}

function renderExplorerTable() {
  if (!governanceElements.tableHead || !governanceElements.tableBody) return;

  governanceElements.tableHead.innerHTML = `
    <tr>
      <th>Explorateur administratif</th>
      <th>Type</th>
      <th>Niveau</th>
      <th>Statut</th>
      <th>Qualité</th>
      <th>Source</th>
      <th>Infos</th>
    </tr>
  `;

  const rows = getExplorerVisibleNodes();
  if (rows.length === 0) {
    governanceElements.tableBody.innerHTML = '<tr><td colspan="7" class="empty-state">Aucun nœud correspondant à la recherche.</td></tr>';
    if (governanceElements.pageInfo) {
      governanceElements.pageInfo.textContent = 'Explorateur';
    }
    if (governanceElements.prevButton) governanceElements.prevButton.disabled = true;
    if (governanceElements.nextButton) governanceElements.nextButton.disabled = true;
    return;
  }

  governanceElements.tableBody.innerHTML = rows
    .map(({ node, depth }) => {
      const selected = governanceState.selectedExplorerNodeId === node.id;
      const expanded = isExplorerExpanded(node.id);
      const hasChildren = node.children.length > 0;
      const padding = depth * 22;

      return `
        <tr data-node-id="${escapeHtml(node.id)}" class="explorer-row ${selected ? 'selected' : ''}">
          <td>
            <div class="explorer-node" style="padding-left:${padding}px;">
              <button type="button" class="explorer-toggle ${hasChildren ? '' : 'leaf'}" data-toggle-node="${escapeHtml(node.id)}" aria-label="${expanded ? 'Réduire' : 'Déployer'} ${escapeHtml(node.label)}" ${hasChildren ? '' : 'disabled'}>${hasChildren ? (expanded ? '−' : '+') : '•'}</button>
              <span class="explorer-icon" aria-hidden="true">${escapeHtml(node.icon)}</span>
              <span class="explorer-label">
                <strong>${escapeHtml(node.label)}</strong>
                <span>${escapeHtml(node.code || '—')}</span>
              </span>
            </div>
          </td>
          <td>${escapeHtml(node.typeLabel)}</td>
          <td>${escapeHtml(node.adminLevel)}</td>
          <td><span class="status-badge explorer-status">${escapeHtml(node.status)}</span></td>
          <td><span class="quality-badge ${escapeHtml(node.qualityClass)}">${escapeHtml(node.qualityBadge)}</span></td>
          <td>${escapeHtml(node.source)}</td>
          <td>${escapeHtml(String(node.informationAvailable.length))}</td>
        </tr>
      `;
    })
    .join('');

  governanceElements.tableBody.querySelectorAll('tr[data-node-id]').forEach((row) => {
    row.addEventListener('click', (event) => {
      const toggleButton = event.target.closest('[data-toggle-node]');
      if (toggleButton) {
        event.stopPropagation();
        toggleExplorerNode(toggleButton.dataset.toggleNode);
        return;
      }

      const nodeId = row.dataset.nodeId;
      if (!nodeId) return;
      selectExplorerNode(nodeId);
    });
  });

  if (governanceElements.pageInfo) {
    governanceElements.pageInfo.textContent = `Explorateur · ${rows.length} nœud${rows.length > 1 ? 's' : ''}`;
  }

  if (governanceElements.prevButton) governanceElements.prevButton.disabled = true;
  if (governanceElements.nextButton) governanceElements.nextButton.disabled = true;
}

function buildNationalAdministrativeReport({ provinces, territoires, collectivites, groupements, villages }) {
  const duplicateDetails = [];
  const anomalies = [];
  const byLevel = {
    rdc: 1,
    zone_fdsu: 0,
    province: provinces.length,
    territoire: territoires.length,
    secteur: 0,
    chefferie: 0,
    cite: 0,
    groupement: groupements.length,
    village: villages.length,
  };

  const root = { level: 'rdc', label: 'RDC', count: 1, children: [] };
  const zoneNodes = new Map();
  const provinceNodes = new Map();
  const territoireNodes = new Map();

  const sortedProvinces = provinces.slice().sort((left, right) => String(left.nom || '').localeCompare(String(right.nom || ''), 'fr'));
  sortedProvinces.forEach((province) => {
    const zoneCode = String(province.zone || 'INCONNU').toUpperCase();
    let zoneNode = zoneNodes.get(zoneCode);
    if (!zoneNode) {
      zoneNode = { level: 'zone_fdsu', label: `Zone FDSU ${zoneCode}`, code: zoneCode, count: 0, children: [] };
      zoneNodes.set(zoneCode, zoneNode);
      root.children.push(zoneNode);
    }
    zoneNode.count += 1;

    if (!province.zone) {
      anomalies.push({ level: 'province', entity: province.nom, message: 'Province sans zone FDSU renseignée.', severity: 'error', code: province.code });
    }

    const provinceNode = { level: 'province', label: province.nom, code: province.code, count: 1, children: [] };
    zoneNode.children.push(provinceNode);
    provinceNodes.set(province.id, provinceNode);
  });

  territoires.slice().sort((left, right) => String(left.nom || '').localeCompare(String(right.nom || ''), 'fr')).forEach((territoire) => {
    const provinceNode = provinceNodes.get(territoire.province_id);
    if (!provinceNode) {
      anomalies.push({ level: 'territoire', entity: territoire.nom, message: 'Territoire sans province parente exploitable.', severity: 'error', code: territoire.code });
      return;
    }

    const territoireNode = { level: 'territoire', label: territoire.nom, code: territoire.code, count: 1, children: [] };
    provinceNode.children.push(territoireNode);
    territoireNodes.set(territoire.id, territoireNode);
  });

  collectivites.slice().sort((left, right) => String(left.nom || '').localeCompare(String(right.nom || ''), 'fr')).forEach((collectivite) => {
    const territoireNode = territoireNodes.get(collectivite.territoire_id);
    if (!territoireNode) {
      anomalies.push({ level: 'collectivite', entity: collectivite.nom, message: 'Collectivité sans territoire parent exploitable.', severity: 'error', code: collectivite.code });
      return;
    }

    const collectiviteType = String(collectivite.type_collectivite || '').toLowerCase();
    const nodeLevel = collectiviteType === 'secteur' || collectiviteType === 'chefferie' ? collectiviteType : 'cite';
    byLevel[nodeLevel] = (byLevel[nodeLevel] || 0) + 1;

    const collectiviteNode = { level: nodeLevel, label: collectivite.nom, code: collectivite.code, count: 1, children: [] };
    territoireNode.children.push(collectiviteNode);

    groupements
      .filter((groupement) => groupement.collectivite_id === collectivite.id)
      .slice()
      .sort((left, right) => String(left.nom || '').localeCompare(String(right.nom || ''), 'fr'))
      .forEach((groupement) => {
        const groupementNode = { level: 'groupement', label: groupement.nom, code: groupement.code, count: 1, children: [] };
        collectiviteNode.children.push(groupementNode);

        villages
          .filter((village) => village.groupement_id === groupement.id)
          .slice()
          .sort((left, right) => String(left.nom || '').localeCompare(String(right.nom || ''), 'fr'))
          .forEach((village) => {
            groupementNode.children.push({ level: 'village', label: village.nom, code: village.code, count: 1, children: [] });
          });
      });
  });

  byLevel.zone_fdsu = zoneNodes.size;

  const duplicateCount = [provinces, territoires, collectivites, groupements, villages].reduce((total, items) => total + countDuplicateEntries(items), 0);
  duplicateDetails.push(...collectDuplicateAnomalies(provinces, 'province'));
  duplicateDetails.push(...collectDuplicateAnomalies(territoires, 'territoire'));
  duplicateDetails.push(...collectDuplicateAnomalies(collectivites, 'collectivite'));
  duplicateDetails.push(...collectDuplicateAnomalies(groupements, 'groupement'));
  duplicateDetails.push(...collectDuplicateAnomalies(villages, 'village'));
  anomalies.push(...duplicateDetails);

  const totalEntities = 1 + provinces.length + territoires.length + collectivites.length + groupements.length + villages.length;
  const orphanCount = anomalies.filter((item) => item.severity === 'error').length;
  const consistency = totalEntities > 0 ? Math.max(0, 100 - ((anomalies.length / totalEntities) * 100)) : 0;
  const completeness = totalEntities > 0 ? Math.max(0, 100 - ((orphanCount / totalEntities) * 100)) : 0;
  const qualityScore = Number(((completeness * 0.35) + (consistency * 0.65)).toFixed(2));

  const flattenedRows = flattenAdministrativeTree(root, qualityScore, duplicateCount);
  const qualityRows = [{
    id: 'national',
    referentiel: 'Référentiel administratif national',
    completude: `${completeness.toFixed(1)} %`,
    coherence: `${consistency.toFixed(1)} %`,
    geometries_valides: '100 %',
    doublons: duplicateCount,
    qualite_globale: qualityScore,
  }];

  const validationRows = anomalies.length > 0
    ? anomalies.map((anomaly, index) => ({
        id: `anomaly-${index + 1}`,
        objet: anomaly.entity,
        doublons: anomaly.code && anomaly.message.toLowerCase().includes('dupliqué') ? anomaly.code : '—',
        geometries_invalides: '—',
        sans_code: anomaly.code ? '—' : 'Oui',
        sans_rattachement: anomaly.message.toLowerCase().includes('sans') ? 'Oui' : '—',
        statut: anomaly.severity === 'error' ? 'À vérifier' : 'À surveiller',
      }))
    : [{
        id: 'validation-empty',
        objet: 'Référentiel national',
        doublons: '0',
        geometries_invalides: '0',
        sans_code: '0',
        sans_rattachement: '0',
        statut: 'Validé',
      }];

  const markdownPreview = buildAdministrativeMarkdown(root, { totalEntities, orphanCount, duplicateCount, qualityScore, completeness, consistency }, anomalies);

  return {
    tree: root,
    referentielRows: flattenedRows,
    validationRows,
    qualityRows,
    normalizationRow: {
      id: 'national-referential',
      source: 'API locale',
      entites_analysees: totalEntities,
      score_qualite: qualityScore,
      erreurs: anomalies.length,
      doublons: duplicateCount,
      orphelines: orphanCount,
      rapport: 'Publié',
    },
    normalization: {
      summary: {
        analyzedEntities: totalEntities,
        qualityScore,
        errors: anomalies.length,
        duplicates: duplicateCount,
        orphans: orphanCount,
        reportStatus: anomalies.length === 0 ? 'Publié' : 'À vérifier',
      },
      byLevel: Object.entries(byLevel).map(([level, value]) => ({ level, value })),
      reportPreview: markdownPreview,
    },
    statistics: {
      entityCount: totalEntities,
      byLevel,
      orphanCount,
      duplicateCount,
      qualityScore,
    },
    anomalies,
    quality: { qualityScore, completeness, consistency },
  };
}

function collectDuplicateAnomalies(items, level) {
  const codeCounts = new Map();
  const nameCounts = new Map();

  items.forEach((item) => {
    const code = String(item.code || '').trim();
    const name = String(item.nom || '').trim().toUpperCase();
    if (code) {
      codeCounts.set(code, (codeCounts.get(code) || 0) + 1);
    }
    if (name) {
      nameCounts.set(name, (nameCounts.get(name) || 0) + 1);
    }
  });

  const anomalies = [];
  items.forEach((item) => {
    const code = String(item.code || '').trim();
    const name = String(item.nom || '').trim();
    if (code && codeCounts.get(code) > 1) {
      anomalies.push({ level, entity: name || code, message: 'Code dupliqué dans le référentiel.', severity: 'error', code });
    }
    if (name && nameCounts.get(name.toUpperCase()) > 1) {
      anomalies.push({ level, entity: name, message: 'Nom dupliqué dans le référentiel.', severity: 'warning', code: code || null });
    }
  });

  return anomalies;
}

function countDuplicateEntries(items) {
  const codes = new Map();
  items.forEach((item) => {
    const code = String(item.code || '').trim();
    if (!code) return;
    codes.set(code, (codes.get(code) || 0) + 1);
  });
  let duplicates = 0;
  codes.forEach((value) => {
    if (value > 1) duplicates += value - 1;
  });
  return duplicates;
}

function flattenAdministrativeTree(root, qualityScore, duplicateCount) {
  const rows = [];

  function visit(node, depth = 0, parentLabel = '—') {
    rows.push({
      id: `${node.level}-${rows.length + 1}`,
      nom: `${'  '.repeat(depth)}${node.label}`,
      type: node.level,
      nombre_objets: node.count,
      source_officielle: depth === 0 ? 'RDC' : 'API locale',
      version: 'Calculé',
      date_mise_a_jour: new Date().toLocaleDateString('fr-FR'),
      statut: node.level === 'rdc' ? 'Publié' : 'Publié',
      qualite: qualityScore.toFixed(1),
      parent: parentLabel,
    });

    node.children.forEach((child) => visit(child, depth + 1, node.label));
  }

  visit(root);

  if (rows.length > 0) {
    rows[0].doublons = duplicateCount;
  }

  return rows;
}

function buildAdministrativeMarkdown(root, summary, anomalies) {
  const lines = [
    '# Référentiel administratif national',
    '',
    `- Entités: ${summary.totalEntities}`,
    `- Orphelins: ${summary.orphanCount}`,
    `- Doublons: ${summary.duplicateCount}`,
    `- Score qualité: ${summary.qualityScore}`,
    `- Complétude: ${summary.completeness.toFixed(1)} %`,
    `- Cohérence: ${summary.consistency.toFixed(1)} %`,
    '',
    '## Arborescence',
    '',
  ];

  function renderNode(node, depth = 0) {
    const codeSuffix = node.code ? ` (${node.code})` : '';
    lines.push(`${'  '.repeat(depth)}- ${node.label}${codeSuffix} [${node.count}]`);
    node.children.forEach((child) => renderNode(child, depth + 1));
  }

  renderNode(root);
  lines.push('', '## Anomalies', '');
  if (anomalies.length === 0) {
    lines.push('- aucune anomalie détectée');
  } else {
    anomalies.forEach((anomaly) => {
      lines.push(`- ${anomaly.severity}/${anomaly.level}: ${anomaly.message}`);
    });
  }

  return lines.join('\n');
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

  if (governanceState.activeTab === 'referentiels') {
    renderExplorerTable();
    return;
  }

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

  if (governanceState.activeTab === 'referentiels') {
    const selectedNode = getExplorerNodeById(governanceState.selectedExplorerNodeId);
    if (!selectedNode) {
      governanceElements.detailTitle.textContent = 'Aucun nœud sélectionné';
      governanceElements.detailBody.innerHTML = '<div class="empty-detail">Sélectionnez un nœud de l’arborescence pour afficher ses informations.</div>';
      return;
    }

    governanceElements.detailTitle.textContent = selectedNode.label;
    governanceElements.detailBody.innerHTML = buildTerritorialFileMarkup(selectedNode);
    return;
  }

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

function buildTerritorialFileMarkup(node) {
  const consultationMode = governanceState.detailMode || 'consultation';
  const modeLabel = consultationMode === 'consultation' ? 'Consultation' : 'Édition future';
  const modeDescription = consultationMode === 'consultation'
    ? 'Mode consultation actif. Les données sont présentées en lecture seule.'
    : 'Mode édition réservé pour un enrichissement futur.';
  const futureSources = ['CAID', 'CENI', 'HDX', 'FDSU', 'KMZ'];

  const generalInfo = [
    { label: 'Nom', value: node.label },
    { label: 'Type', value: node.typeLabel },
    { label: 'Niveau administratif', value: node.adminLevel },
    { label: 'Statut', value: node.status },
    { label: 'Source', value: node.source },
    { label: 'Qualité', value: node.qualityBadge },
  ];

  const administrativeInfo = [
    { label: 'Hiérarchie complète', value: node.hierarchyLabel },
    { label: 'Parent direct', value: node.parentId ? (getExplorerNodeById(node.parentId)?.label || 'Non renseigné') : 'Non renseigné' },
    { label: 'Enfants directs', value: String(node.statistics.children ?? 0) },
    { label: 'Total de nœuds', value: String(node.statistics.total ?? 0) },
    { label: 'Orphelins détectés', value: String(node.statistics.orphans ?? 0) },
    { label: 'Code', value: node.code || 'Non renseigné' },
  ];

  const geographicInfo = [
    { label: 'Zone FDSU', value: node.level === 'zone_fdsu' || node.level === 'province' || node.level === 'territoire' ? node.hierarchyPath?.[1] : 'Non renseigné' },
    { label: 'Province', value: getHierarchyValue(node, 'province') },
    { label: 'Territoire', value: getHierarchyValue(node, 'territoire') },
    { label: 'Secteur / Chefferie', value: getHierarchyValue(node, 'secteur', 'chefferie') },
    { label: 'Groupement', value: getHierarchyValue(node, 'groupement') },
    { label: 'Village', value: getHierarchyValue(node, 'village') },
  ];

  const developmentInfo = [
    { label: 'Population', value: 'Non renseigné' },
    { label: 'Superficie', value: 'Non renseigné' },
    { label: 'Densité', value: 'Non renseigné' },
    { label: 'Chef-lieu', value: 'Non renseigné' },
  ];

  const telecomInfo = [
    { label: 'Couverture', value: 'Non renseigné' },
    { label: 'Sites FDSU', value: 'Non renseigné' },
    { label: 'Backbone', value: 'Non renseigné' },
    { label: 'Technologies', value: 'Non renseigné' },
  ];

  const documentationInfo = [
    { label: 'Fiche source', value: 'Non renseigné' },
    { label: 'Version', value: 'Non renseigné' },
    { label: 'Dernière mise à jour', value: 'Non renseigné' },
    { label: 'Références disponibles', value: futureSources.join(', ') },
  ];

  const historicalInfo = [
    { label: 'Créé le', value: 'Non renseigné' },
    { label: 'Mis à jour le', value: 'Non renseigné' },
    { label: 'Validé le', value: 'Non renseigné' },
    { label: 'Événements', value: 'Non renseigné' },
  ];

  const sourceInfo = futureSources.map((source) => ({
    label: source,
    value: source === 'FDSU' ? 'Référentiel consolidé' : 'Prévu pour enrichissement futur',
  }));

  return `
    <div class="territorial-file">
      <div class="territorial-file-header">
        <div>
          <p class="panel-label">Fiche territoriale intelligente</p>
          <h4>${escapeHtml(node.label)}</h4>
          <p class="territorial-file-subtitle">${escapeHtml(node.hierarchyLabel || 'Non renseigné')}</p>
        </div>
        <div class="territorial-file-modes">
          <button type="button" class="mode-chip active" aria-pressed="true">${escapeHtml(modeLabel)}</button>
          <button type="button" class="mode-chip" disabled aria-disabled="true">Mode édition futur</button>
        </div>
      </div>

      <p class="territorial-file-intro">${escapeHtml(modeDescription)}</p>

      ${renderTerritorialSection('Informations générales', generalInfo, true)}
      ${renderTerritorialSection('Organisation administrative', administrativeInfo)}
      ${renderTerritorialSection('Géographie', geographicInfo)}
      ${renderTerritorialSection('Développement', developmentInfo)}
      ${renderTerritorialSection('Télécommunications', telecomInfo)}
      ${renderTerritorialSection('Documentation', documentationInfo)}
      ${renderTerritorialSection('Historique', historicalInfo)}
      ${renderTerritorialSection('Sources', sourceInfo, false, true)}
    </div>
  `;
}

function renderTerritorialSection(title, fields, open = false, isSources = false) {
  const items = fields
    .map((field) => `
      <div class="territorial-field">
        <span>${escapeHtml(field.label)}</span>
        <strong>${escapeHtml(formatTerritorialValue(field.value))}</strong>
      </div>
    `)
    .join('');

  const sourceBadges = isSources
    ? `
      <div class="territorial-source-badges">
        ${fields
          .map((field) => `<span class="territorial-source-badge">${escapeHtml(field.label)}</span>`)
          .join('')}
      </div>
    `
    : '';

  return `
    <details class="territorial-section" ${open ? 'open' : ''}>
      <summary>
        <span>${escapeHtml(title)}</span>
        <span class="territorial-section-toggle">${open ? '−' : '+'}</span>
      </summary>
      <div class="territorial-section-body">
        ${items}
        ${sourceBadges}
      </div>
    </details>
  `;
}

function formatTerritorialValue(value) {
  if (value === null || value === undefined || String(value).trim() === '') {
    return 'Non renseigné';
  }
  return String(value);
}

function getHierarchyValue(node, ...levels) {
  const normalizedLevels = levels.map((level) => String(level).toLowerCase());
  const match = [...(node.hierarchyPath || [])].reverse().find((item) => normalizedLevels.includes(String(item).toLowerCase()));
  return match || 'Non renseigné';
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

function initializeSourceExplorerModule() {
  if (!sourceExplorerState.initialized) {
    sourceExplorerElements.panel = document.querySelector('#explorateur-sources-panel');
    sourceExplorerElements.fileInput = document.querySelector('#source-explorer-report-input');
    sourceExplorerElements.sourcePath = document.querySelector('#source-explorer-source-path');
    sourceExplorerElements.sourceFormat = document.querySelector('#source-explorer-source-format');
    sourceExplorerElements.objectCount = document.querySelector('#source-explorer-object-count');
    sourceExplorerElements.fieldCount = document.querySelector('#source-explorer-field-count');
    sourceExplorerElements.folderCount = document.querySelector('#source-explorer-folder-count');
    sourceExplorerElements.extractButton = document.querySelector('#source-explorer-extract');
    sourceExplorerElements.catalogBody = document.querySelector('#source-explorer-catalog-body');
    sourceExplorerElements.dictionaryBody = document.querySelector('#source-explorer-dictionary-body');
    sourceExplorerElements.tagsContainer = document.querySelector('#source-explorer-tags');

    if (!sourceExplorerElements.panel) {
      return;
    }

    sourceExplorerElements.fileInput?.addEventListener('change', async (event) => {
      const input = event.target;
      if (!input || !input.files || input.files.length === 0) {
        return;
      }

      const file = input.files[0];
      try {
        const text = await file.text();
        const payload = JSON.parse(text);
        sourceExplorerState.report = payload;
        renderSourceExplorerReport();
      } catch {
        sourceExplorerState.report = null;
        renderSourceExplorerEmpty('Impossible de lire le rapport JSON sélectionné.');
      }
    });

    sourceExplorerElements.extractButton?.addEventListener('click', () => {
      // Sprint scope: extraction workflow is intentionally staged for later.
    });

    sourceExplorerState.initialized = true;
    renderSourceExplorerEmpty('Chargez un rapport JSON généré par scripts/explore_source.py pour explorer la source.');
  }
}

function renderSourceExplorerEmpty(message) {
  if (sourceExplorerElements.sourcePath) sourceExplorerElements.sourcePath.textContent = 'Non renseigné';
  if (sourceExplorerElements.sourceFormat) sourceExplorerElements.sourceFormat.textContent = 'Non renseigné';
  if (sourceExplorerElements.objectCount) sourceExplorerElements.objectCount.textContent = '0';
  if (sourceExplorerElements.fieldCount) sourceExplorerElements.fieldCount.textContent = '0';
  if (sourceExplorerElements.folderCount) sourceExplorerElements.folderCount.textContent = '0';

  if (sourceExplorerElements.catalogBody) {
    sourceExplorerElements.catalogBody.innerHTML = `<tr><td colspan="8" class="empty-state">${escapeHtml(message)}</td></tr>`;
  }
  if (sourceExplorerElements.dictionaryBody) {
    sourceExplorerElements.dictionaryBody.innerHTML = '<tr><td colspan="6" class="empty-state">Aucun dictionnaire disponible.</td></tr>';
  }
  if (sourceExplorerElements.tagsContainer) {
    sourceExplorerElements.tagsContainer.innerHTML = '<span class="source-tag">Aucun tag</span>';
  }
}

function renderSourceExplorerReport() {
  const report = sourceExplorerState.report;
  if (!report) {
    renderSourceExplorerEmpty('Aucun rapport chargé.');
    return;
  }

  const folders = Array.isArray(report.folders) ? report.folders : [];
  const dictionary = Array.isArray(report.data_dictionary) ? report.data_dictionary : [];

  if (sourceExplorerElements.sourcePath) sourceExplorerElements.sourcePath.textContent = report.source_file || 'Non renseigné';
  if (sourceExplorerElements.sourceFormat) sourceExplorerElements.sourceFormat.textContent = report.source_format || 'Non renseigné';
  if (sourceExplorerElements.objectCount) sourceExplorerElements.objectCount.textContent = String(report.object_count || 0);
  if (sourceExplorerElements.fieldCount) sourceExplorerElements.fieldCount.textContent = String(report.field_count || 0);
  if (sourceExplorerElements.folderCount) sourceExplorerElements.folderCount.textContent = String(folders.length);

  if (sourceExplorerElements.catalogBody) {
    if (folders.length === 0) {
      sourceExplorerElements.catalogBody.innerHTML = '<tr><td colspan="8" class="empty-state">Aucun dossier détecté.</td></tr>';
    } else {
      sourceExplorerElements.catalogBody.innerHTML = folders
        .map((folder, index) => {
          const geometry = Array.isArray(folder.geometry_types) && folder.geometry_types.length > 0
            ? folder.geometry_types.join(', ')
            : 'Non renseigné';
          const attributes = Array.isArray(folder.attributes) && folder.attributes.length > 0
            ? folder.attributes.join(', ')
            : 'Non renseigné';
          return `
            <tr data-folder-index="${index}">
              <td>${escapeHtml(String(folder.folder_name || 'Non renseigné'))}</td>
              <td>${escapeHtml(String(folder.type || folder.dataset_type || 'Autres'))}</td>
              <td>${escapeHtml(String(folder.object_count || 0))}</td>
              <td>${escapeHtml(String(folder.field_count || 0))}</td>
              <td>${escapeHtml(geometry)}</td>
              <td>${escapeHtml(String(folder.quality ?? 'Non renseigné'))}</td>
              <td>${escapeHtml(String(folder.module_sig_conseille || 'Dashboard'))}</td>
              <td>${escapeHtml(attributes)}</td>
            </tr>
          `;
        })
        .join('');
    }
  }

  if (sourceExplorerElements.dictionaryBody) {
    if (dictionary.length === 0) {
      sourceExplorerElements.dictionaryBody.innerHTML = '<tr><td colspan="6" class="empty-state">Aucun champ détecté.</td></tr>';
    } else {
      sourceExplorerElements.dictionaryBody.innerHTML = dictionary
        .map((entry) => `
          <tr>
            <td>${escapeHtml(String(entry.name || 'Non renseigné'))}</td>
            <td>${escapeHtml(String(entry.type || entry.value_type || 'inconnu'))}</td>
            <td>${escapeHtml(String(entry.value_count ?? 0))}</td>
            <td>${escapeHtml(String(entry.unique_count ?? 0))}</td>
            <td>${escapeHtml(String(entry.null_count ?? 0))}</td>
            <td>${escapeHtml(String(entry.example || 'Non renseigné'))}</td>
          </tr>
        `)
        .join('');
    }
  }

  if (sourceExplorerElements.tagsContainer) {
    const tags = new Set();
    folders.forEach((folder) => {
      (Array.isArray(folder.tags) ? folder.tags : []).forEach((tag) => tags.add(String(tag)));
    });
    sourceExplorerElements.tagsContainer.innerHTML = tags.size > 0
      ? Array.from(tags).sort().map((tag) => `<span class="source-tag">${escapeHtml(tag)}</span>`).join('')
      : '<span class="source-tag">Aucun tag</span>';
  }
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

function getTerritoires() {
  return fetchJson('/territoires?limit=500');
}

function getCollectivites() {
  return fetchJson('/collectivites?limit=500');
}

function getGroupements() {
  return fetchJson('/groupements?limit=500');
}

function getVillages() {
  return fetchJson('/villages?limit=500');
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
