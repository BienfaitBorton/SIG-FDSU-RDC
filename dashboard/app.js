const DATA_MODE = 'auto'; // 'auto' detecte FastAPI/PostgreSQL, 'api' force l'API, 'json' force le fallback local.
const API_BASE_URL = window.__API_BASE_URL__ || 'http://127.0.0.1:8001';
const DEMO_ENRICHMENT_MODE = true;
const REPORTS_BASE = '../data/reports';
let LOCAL_JSON_MODE = DATA_MODE === 'json';
let API_HEALTH = null;
const FDSU_CODE_FORMAT = 'FDSU_<CODE_ZONE>_<CODE_PROVINCE>_<CODE_TERRITOIRE>_<CODE_SITE>';
const FDSU_ZONE_DEFINITIONS = {
  ND: { nom: 'Zone Nord', colorVar: '--zone-nd' },
  SD: { nom: 'Zone Sud', colorVar: '--zone-sd' },
  CE: { nom: 'Zone Centre', colorVar: '--zone-ce' },
  OT: { nom: 'Zone Ouest', colorVar: '--zone-ot' },
  ET: { nom: 'Zone Est', colorVar: '--zone-et' },
};
const FDSU_ZONE_CODES = ['ND', 'OT', 'CE', 'SD', 'ET'];
const FDSU_LAYER_STACK_ORDER = ['rdcBoundary', 'zones', 'provinces', 'territoires', 'collectivites', 'groupements', 'villages', 'sites', 'sites_all', 'sites_40', 'sites_300', 'telecom_vodacom', 'telecom_orange', 'telecom_fiber_mw', 'telecom_fiberco', 'telecom_fttx', 'routes_principales', 'spatial_relations', 'asset_need_matches', 'missions'];
const FDSU_SITES_PROGRAM_LAYERS = {
  sites_all: {
    label: 'Tous les sites',
    virtual: true,
    programKeys: ['sites_40', 'sites_300'],
  },
  sites_40: {
    label: 'Programme Sites 40',
    filePath: '/programs/sites_40/sites_40.geojson',
    apiPath: '/api/programs/sites40',
    panelApiPath: '/api/programs/sites40?format=panel',
  },
  sites_300: {
    label: 'Programme Sites 300',
    filePath: '/programs/sites_300/sites_300.geojson',
    apiPath: '/api/programs/sites300',
    panelApiPath: '/api/programs/sites300?format=panel',
  },
};
const TELECOM_LAYERS = {
  telecom_vodacom: {
    label: 'Sites Vodacom',
    apiPath: '/api/telecom/layers/telecom_vodacom',
    pendingMessage: 'Données télécom disponibles en mode DB',
    color: '#e11d48',
    fillColor: '#fb7185',
  },
  telecom_orange: {
    label: 'Infrastructures Orange',
    apiPath: '/api/telecom/layers/telecom_orange',
    pendingMessage: 'Données télécom disponibles en mode DB',
    color: '#ea580c',
    fillColor: '#fb923c',
  },
  telecom_fiber_mw: {
    label: 'Fibre / MW',
    apiPath: '/api/telecom/layers/telecom_fiber_mw',
    pendingMessage: 'Données télécom disponibles en mode DB',
    color: '#2563eb',
    fillColor: '#60a5fa',
  },
  telecom_fiberco: {
    label: 'Fiberco',
    apiPath: '/api/telecom/layers/telecom_fiberco',
    pendingMessage: 'Données télécom disponibles en mode DB',
    color: '#0891b2',
    fillColor: '#22d3ee',
  },
  telecom_fttx: {
    label: 'FTTX',
    apiPath: '/api/telecom/layers/telecom_fttx',
    pendingMessage: 'Données télécom disponibles en mode DB',
    color: '#7c3aed',
    fillColor: '#a78bfa',
  },
};
const TRANSPORT_LAYERS = {
  routes_principales: {
    label: 'Routes principales',
    apiPath: '/api/transport/layers/routes_principales',
    pendingMessage: 'Routes disponibles en mode DB après import pipeline',
    color: '#b45309',
    fillColor: '#f59e0b',
  },
};
const SPATIAL_ANALYSIS_LAYERS = {
  spatial_relations: {
    label: 'Relations spatiales',
    apiPath: '/api/analysis/layers/spatial-relations',
    pendingMessage: 'Relations spatiales disponibles en mode DB après analyse',
    color: '#0d9488',
    fillColor: '#2dd4bf',
  },
  asset_need_matches: {
    label: 'Correspondance Actifs ↔ Besoins',
    apiPath: '/api/spatial-matching/map',
    pendingMessage: 'Correspondances NSME disponibles après refresh',
    color: '#f59e0b',
    fillColor: '#fbbf24',
  },
};
const FDSU_SMART_MAP_MODES = {
  administrative: 'Mode administratif',
  connectivity: 'Mode connectivité',
  economic: 'Mode potentiel économique',
  ccnPriority: 'Mode priorité CCN',
  dataQuality: 'Mode qualité des données',
  decision: 'Mode aide à la décision',
};
const RDC_MAP_BOUNDS = [[-13.45, 12.2], [5.4, 31.3]];
const FDSU_PROVINCE_REFERENCE = {
  'BAS-UELE': { code: '01', zone_fdsu: 'ND', zone_nom: 'Zone Nord' },
  EQUATEUR: { code: '02', zone_fdsu: 'ND', zone_nom: 'Zone Nord' },
  'HAUT-UELE': { code: '05', zone_fdsu: 'ND', zone_nom: 'Zone Nord' },
  MONGALA: { code: '18', zone_fdsu: 'ND', zone_nom: 'Zone Nord' },
  'NORD-UBANGI': { code: '20', zone_fdsu: 'ND', zone_nom: 'Zone Nord' },
  'SUD-UBANGI': { code: '23', zone_fdsu: 'ND', zone_nom: 'Zone Nord' },
  TSHOPO: { code: '25', zone_fdsu: 'ND', zone_nom: 'Zone Nord' },
  TSHUAPA: { code: '26', zone_fdsu: 'ND', zone_nom: 'Zone Nord' },
  TANGANYIKA: { code: '24', zone_fdsu: 'SD', zone_nom: 'Zone Sud' },
  'HAUT-KATANGA': { code: '03', zone_fdsu: 'SD', zone_nom: 'Zone Sud' },
  LUALABA: { code: '15', zone_fdsu: 'SD', zone_nom: 'Zone Sud' },
  'HAUT-LOMAMI': { code: '04', zone_fdsu: 'SD', zone_nom: 'Zone Sud' },
  KASAI: { code: '07', zone_fdsu: 'CE', zone_nom: 'Zone Centre' },
  'KASAI CENTRAL': { code: '08', zone_fdsu: 'CE', zone_nom: 'Zone Centre' },
  'KASAI-ORIENTAL': { code: '09', zone_fdsu: 'CE', zone_nom: 'Zone Centre' },
  LOMAMI: { code: '14', zone_fdsu: 'CE', zone_nom: 'Zone Centre' },
  SANKURU: { code: '21', zone_fdsu: 'CE', zone_nom: 'Zone Centre' },
  KINSHASA: { code: '10', zone_fdsu: 'OT', zone_nom: 'Zone Ouest' },
  'KONGO CENTRAL': { code: '11', zone_fdsu: 'OT', zone_nom: 'Zone Ouest' },
  KWANGO: { code: '12', zone_fdsu: 'OT', zone_nom: 'Zone Ouest' },
  KWILU: { code: '13', zone_fdsu: 'OT', zone_nom: 'Zone Ouest' },
  'MAI-NDOMBE': { code: '16', zone_fdsu: 'OT', zone_nom: 'Zone Ouest' },
  ITURI: { code: '06', zone_fdsu: 'ET', zone_nom: 'Zone Est' },
  'NORD-KIVU': { code: '19', zone_fdsu: 'ET', zone_nom: 'Zone Est' },
  'SUD-KIVU': { code: '22', zone_fdsu: 'ET', zone_nom: 'Zone Est' },
  MANIEMA: { code: '17', zone_fdsu: 'ET', zone_nom: 'Zone Est' },
};

const navigationItems = document.querySelectorAll('.nav-item');
const panels = document.querySelectorAll('#dashboard-panel, .module-panel');
const pageTitle = document.querySelector('.page-title');
const pageContext = document.querySelector('.page-context');
const ROUTE_TO_MODULE = {
  dashboard: 'dashboard',
  map: 'cartographie',
  cartographie: 'cartographie',
  referentiel: 'referentiel',
  registry: 'gestion_referentiels',
  'national-asset-registry': 'national_asset_registry',
  national_asset_registry: 'national_asset_registry',
  'ceni-registry': 'ceni_registry',
  ceni_registry: 'ceni_registry',
  dnai: 'dnai',
  ntil: 'ntil',
  'national-territorial-intelligence': 'national_territorial_intelligence',
  national_territorial_intelligence: 'national_territorial_intelligence',
  gestion_referentiels: 'gestion_referentiels',
  sources: 'explorateur_sources',
  explorateur_sources: 'explorateur_sources',
  sites: 'sites',
  decision: 'decision',
  'decision-view': 'centre_decision',
  decision_view: 'centre_decision',
  centre_decision: 'centre_decision',
  knowledge: 'connaissances',
  connaissances: 'connaissances',
  enrichment: 'enrichissement',
  enrichissement: 'enrichissement',
  geocoding: 'geocodage',
  ccn: 'ccn',
  'territorial-intelligence': 'territorial_intelligence',
  territorial_intelligence: 'territorial_intelligence',
  'salle-pilotage': 'salle_pilotage',
  salle_pilotage: 'salle_pilotage',
  'decision-detail': 'decision_detail',
  'decision-workspace': 'decision_detail',
  'territorial-twin': 'decision_detail',
  territorial_twin: 'decision_detail',
  decision_detail: 'decision_detail',
  decision_workspace: 'decision_detail',
  'decision-case': 'decision_experience',
  'spatial-impact': 'decision_experience',
  'analyse-impact-territorial': 'decision_experience',
  'coverage-detail': 'decision_experience',
  'ccn-detail': 'decision_experience',
  decision_experience: 'decision_experience',
  geocodage: 'geocodage',
  import: 'import',
  export: 'export',
  statistiques: 'statistiques',
  utilisateurs: 'utilisateurs',
  parametres: 'parametres',
};
const MODULE_TO_ROUTE = {
  dashboard: 'dashboard',
  cartographie: 'map',
  referentiel: 'referentiel',
  gestion_referentiels: 'registry',
  national_asset_registry: 'national-asset-registry',
  ceni_registry: 'ceni-registry',
  dnai: 'dnai',
  ntil: 'ntil',
  national_territorial_intelligence: 'national-territorial-intelligence',
  explorateur_sources: 'sources',
  sites: 'sites',
  decision: 'decision',
  centre_decision: 'decision-view',
  connaissances: 'knowledge',
  enrichissement: 'enrichment',
  geocodage: 'geocoding',
  ccn: 'ccn',
  territorial_intelligence: 'territorial-intelligence',
  salle_pilotage: 'salle-pilotage',
  decision_detail: 'decision-detail',
  decision_experience: 'decision-case',
  import: 'import',
  export: 'export',
  statistiques: 'statistiques',
  utilisateurs: 'utilisateurs',
  parametres: 'parametres',
};

const dashboardState = {
  initialized: false,
  modules: {},
  localDataPromise: null,
};

const DASHBOARD_DETAIL_PAGE_CONFIG = {
  zones: { title: 'Zones FDSU', layerKey: null, mode: 'zones' },
  provinces: { title: 'Provinces', layerKey: 'provinces' },
  territories: { title: 'Territoires', layerKey: 'territoires', showProvinceFilter: true },
  collectivities: { title: 'Collectivités', layerKey: 'collectivites', showProvinceFilter: true, showTerritoryFilter: true },
  groupements: { title: 'Groupements', layerKey: 'groupements', showProvinceFilter: true, showTerritoryFilter: true },
  localities: { title: 'Localités', layerKey: 'villages', showProvinceFilter: true, showTerritoryFilter: true },
  sites: { title: 'Sites FDSU', layerKey: 'sites', showProvinceFilter: true, showTerritoryFilter: true },
  missions: { title: 'Missions', layerKey: 'missions', showProvinceFilter: true },
};

const dashboardViewState = {
  page: 'main',
  detailType: '',
  selectedEntityId: null,
  selectedZoneCode: null,
  filters: { search: '', province: '', territory: '' },
  rows: [],
  features: [],
  map: null,
  layer: null,
  featureLayers: {},
  mapInitialized: false,
};

const referentielState = {
  initialized: false,
  provinces: [],
  search: '',
  sortKey: 'nom',
  sortOrder: 'asc',
  selectedProvinceId: null,
};

const enrichmentFields = [
  'subdivision_administrative_reelle',
  'activites_economiques_principales',
  'activites_economiques_secondaires',
  'particularites',
  'defis',
  'potentiel_agricole',
  'potentiel_minier',
  'potentiel_commercial',
  'potentiel_numerique',
  'services_publics',
  'couverture_reseau',
];

const enrichmentState = {
  initialized: false,
  suggestions: [],
  selectedId: null,
};

const knowledgeSections = [
  ['presentation', 'Présentation'],
  ['administration', 'Administration'],
  ['geographie', 'Géographie'],
  ['subdivision', 'Subdivision'],
  ['population', 'Population'],
  ['activites_economiques_principales', 'Activités économiques principales'],
  ['activites_economiques_secondaires', 'Activités économiques secondaires'],
  ['particularites', 'Particularités'],
  ['defis', 'Défis'],
  ['potentiel_agricole', 'Potentiel agricole'],
  ['potentiel_minier', 'Potentiel minier'],
  ['potentiel_forestier', 'Potentiel forestier'],
  ['potentiel_touristique', 'Potentiel touristique'],
  ['potentiel_numerique', 'Potentiel numérique'],
  ['services_publics', 'Services publics'],
  ['connectivite', 'Connectivité'],
  ['infrastructures', 'Infrastructures'],
  ['documents', 'Documents'],
  ['photos', 'Photos'],
  ['rapports', 'Rapports'],
  ['historique', 'Historique'],
  ['sources', 'Sources'],
  ['analyse_fdsu', 'Analyse FDSU'],
];

const knowledgeState = {
  initialized: false,
  summary: null,
  priorities: [],
  profile: null,
  origins: null,
  selectedTab: 'presentation',
};

const localKnowledgeSummary = {
  complete_profiles: 0,
  incomplete_profiles: 2,
  profiles_without_photo: 2,
  profiles_without_activities: 2,
  profiles_without_challenges: 2,
  profiles_without_public_services: 2,
  profiles_without_connectivity: 2,
  profiles_without_documents: 2,
};

const localKnowledgePriorities = [
  { province: 'Kinshasa', territoire: 'Ville-Province', completeness: 25, missing_fields_count: 18, priority: 'haute', last_updated_at: '2026-07-04' },
  { province: 'À qualifier', territoire: 'Territoire exemple', completeness: 12, missing_fields_count: 22, priority: 'critique', last_updated_at: '2026-07-04' },
];

const localKnowledgeOrigins = {
  automatic_web_collection_enabled: false,
  official_publication_enabled: false,
  validation_required: true,
  origins: [
    { origin: 'PostgreSQL / PostGIS', status: 'prioritaire', confidence: 45, source_count: 'tables relationnelles', validation_status: 'interne', last_update: '2026-07-05' },
    { origin: 'Documents internes', status: 'indexé', confidence: 30, source_count: 0, validation_status: 'proposition uniquement', last_update: '2026-07-05' },
    { origin: 'CAID', status: 'connecteur prêt', confidence: 40, source_count: 1, validation_status: 'désactivé sans validation humaine', last_update: '2026-07-05' },
    { origin: 'INS', status: 'connecteur prêt', confidence: 40, source_count: 2, validation_status: 'désactivé sans validation humaine', last_update: '2026-07-05' },
  ],
};

const localEnrichmentSuggestions = [
  {
    id: 1,
    entity_type: 'province',
    entity_id: null,
    entity_name: 'Kinshasa',
    field_name: 'subdivision_administrative_reelle',
    proposed_value: 'Ville-Province avec quatre districts administratifs usuels : Funa, Lukunga, Mont-Amba et Tshangu.',
    source_name: 'Ministère de l\'Intérieur RDC',
    source_url: 'https://example.local/source-a-verifier',
    consulted_at: new Date().toISOString(),
    confidence_level: 'à vérifier',
    status: 'proposé',
    review_note: '',
  },
  {
    id: 2,
    entity_type: 'territoire',
    entity_id: null,
    entity_name: 'Exemple à qualifier',
    field_name: 'potentiel_numerique',
    proposed_value: 'Potentiel numérique à documenter depuis une source institutionnelle avant validation.',
    source_name: 'ARPTC',
    source_url: 'https://example.local/source-a-verifier',
    consulted_at: new Date().toISOString(),
    confidence_level: 'faible',
    status: 'proposé',
    review_note: '',
  },
];

const moduleNames = {
  dashboard: 'Tableau de bord',
  cartographie: 'Cartographie',
  referentiel: 'Référentiel administratif',
  gestion_referentiels: 'Gestion des Référentiels',
  national_asset_registry: 'National FDSU Asset Registry',
  national_territorial_intelligence: 'National Territorial Intelligence',
  explorateur_sources: 'Explorateur de Sources',
  sites: 'Sites FDSU',
  decision: 'Aide à la décision',
  centre_decision: 'Centre de Décision FDSU',
  connaissances: 'Base nationale de connaissances',
  enrichissement: 'Enrichissement territorial',
  geocodage: 'Géocodage FDSU',
  ccn: 'Centres Communautaires',
  territorial_intelligence: 'Intelligence territoriale',
  salle_pilotage: 'Salle de Pilotage',
  decision_detail: 'Analyse détaillée',
  decision_experience: 'Dossier de décision',
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
  layerLoadPromises: {},
  activeDrawer: null,
  openDrawers: [],
  freeMode: false,
  mapSearchTerm: '',
  layerStatus: {
    zones: null,
    collectivites: null,
    provinces: null,
    territoires: null,
    groupements: null,
    villages: null,
    sites: null,
    missions: null,
  },
  infoElement: null,
  zonesMessageElement: null,
  breadcrumbElement: null,
  synchronizedListElement: null,
  zonesLayer: null,
  collectivitesLayer: null,
  selectedLayer: null,
  selectedFeature: null,
  hoveredFeatureId: null,
  spatialContext: null,
  spatialContextTrail: [],
  data: {},
  features: {},
  featureLayers: {},
  activeAttributeLayer: 'provinces',
  attributePage: 1,
  attributePageSize: 25,
  attributeSortKey: 'nom',
  attributeSortOrder: 'asc',
  selectedFeatureId: null,
  thematicMode: '',
  basemapManager: null,
};

const nationalMapState = {
  initialized: false,
  map: null,
  layers: {},
  layerStatus: {},
  breadcrumbElement: null,
  synchronizedListElement: null,
  messageElement: null,
  spatialContext: null,
  spatialContextTrail: [],
  data: {},
  features: {},
  featureLayers: {},
};

const platformState = {
  dataPromises: {},
  searchIndex: [],
  searchReady: false,
  selectedEntity: null,
  demoEnrichment: null,
  demoEnrichmentPromise: null,
  workbenchLayer: '',
  workbenchRows: [],
  workbenchPage: 1,
  workbenchPageSize: 25,
  workbenchSortKey: 'nom',
  workbenchSortOrder: 'asc',
  workbenchSelectedFeatureId: null,
  interactionsBound: false,
};

const importState = {
  file: null,
  extension: '',
  workbook: null,
  sheets: {},
  activeSheet: '',
  preview: null,
  anomalies: [],
};

const decisionState = {
  initialized: false,
  rows: [],
  selectedIndex: null,
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
    statusOptions: ['Validé', 'Validé provisoirement', 'Partiel', 'Non publié', 'À valider manuellement'],
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
    statusOptions: ['Validé', 'Validé provisoirement', 'Partiel', 'Non publié', 'À valider manuellement'],
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
  jsonSources: {},
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
  const normalizedModule = ROUTE_TO_MODULE[moduleKey] || moduleKey || 'dashboard';
  initializePlatformInteractions();
  navigationItems.forEach((item) => {
    item.classList.toggle('active', item.dataset.module === normalizedModule);
  });

  panels.forEach((panel) => {
    panel.classList.toggle('hidden', panel.dataset.module !== normalizedModule);
  });

  pageTitle.textContent = moduleNames[normalizedModule] || 'Tableau de bord';
  pageContext.textContent = `Module : ${moduleNames[normalizedModule] || 'Tableau de bord'}`;
  document.querySelector('.main-content')?.scrollTo({ top: 0, behavior: 'auto' });
  window.scrollTo({ top: 0, behavior: 'auto' });
  const activePanel = document.querySelector(`.content-area [data-module="${normalizedModule}"]`);
  if (activePanel) {
    activePanel.setAttribute('tabindex', '-1');
    window.requestAnimationFrame(() => activePanel.focus({ preventScroll: true }));
  }

  if (normalizedModule === 'dashboard') {
    initializeDashboard();
    if (nationalMapState.map) {
      window.setTimeout(() => nationalMapState.map.invalidateSize(), 0);
    }
  }

  if (normalizedModule === 'referentiel') {
    initializeReferentielModule();
  }

  if (normalizedModule === 'cartographie') {
    initializeCartographyModule();
    if (cartographyState.map) {
      window.setTimeout(() => cartographyState.map.invalidateSize(), 0);
    }
  } else if (typeof isCartographyFocusMode === 'function' && isCartographyFocusMode()) {
    setCartographyFocusMode(false);
  }

  if (normalizedModule === 'explorateur_sources') {
    initializeSourceExplorerModule();
  }

  if (normalizedModule === 'gestion_referentiels') {
    initializeGovernanceModule();
  }

  if (normalizedModule === 'national_asset_registry') {
    initializeNationalAssetRegistry();
  }

  if (normalizedModule === 'ceni_registry') {
    initializeCeniRegistry();
  }

  if (normalizedModule === 'dnai') {
    initializeDnaiModule();
  }

  if (normalizedModule === 'ntil') {
    initializeNtilModule();
  }

  if (normalizedModule === 'national_territorial_intelligence') {
    initializeNationalTerritorialIntelligence();
  }

  if (normalizedModule === 'sites') {
    initializeSitesModule();
  }

  if (normalizedModule === 'centre_decision') {
    if (typeof window.initializeDecisionCenterModule === 'function') {
      window.initializeDecisionCenterModule();
    } else {
      // Module chargé après app.js : réessayer dès que decision-center.js est prêt.
      window.setTimeout(() => {
        if (typeof window.initializeDecisionCenterModule === 'function') {
          window.initializeDecisionCenterModule();
        }
      }, 0);
    }
    if (window.decisionCenterState?.map) {
      window.setTimeout(() => window.decisionCenterState.map.invalidateSize(), 0);
    }
    const route = getRouteFromHash();
    if (route.startsWith('decision-scenario/') && typeof window.openDecisionScenario === 'function') {
      const scenarioId = route.split('/')[1];
      window.setTimeout(() => window.openDecisionScenario(scenarioId), 120);
    }
  }

  if (normalizedModule === 'decision') {
    initializeDecisionModule();
  }

  if (normalizedModule === 'connaissances') {
    initializeKnowledgeModule();
  }

  if (normalizedModule === 'enrichissement') {
    initializeEnrichmentModule();
  }

  if (normalizedModule === 'geocodage') {
    if (typeof window.initializeGeocodingModule === 'function') {
      window.initializeGeocodingModule();
    }
    if (window.geocodingState?.map) {
      window.setTimeout(() => window.geocodingState.map.invalidateSize(), 0);
    }
  }

  if (normalizedModule === 'ccn') {
    if (typeof window.initializeCcnModule === 'function') {
      window.initializeCcnModule();
    }
    if (window.ccnState?.map) {
      window.setTimeout(() => window.ccnState.map.invalidateSize(), 0);
    }
  }

  if (normalizedModule === 'territorial_intelligence') {
    if (typeof window.initializeTerritorialIntelligenceModule === 'function') {
      window.initializeTerritorialIntelligenceModule();
    }
    if (window.tiState?.map) {
      window.setTimeout(() => window.tiState.map.invalidateSize(), 0);
    }
  }

  if (normalizedModule === 'salle_pilotage') {
    if (typeof window.initializeExecutiveCockpitModule === 'function') {
      window.initializeExecutiveCockpitModule();
    }
    if (window.Edvs?.state?.map) {
      window.setTimeout(() => window.Edvs.state.map.invalidateSize(), 0);
    }
  }

  if (normalizedModule === 'decision_detail') {
    const twinHash = (window.location.hash || '').replace(/^#/, '').startsWith('territorial-twin');
    if (twinHash && typeof window.TerritorialDigitalTwin?.syncFromHash === 'function') {
      window.TerritorialDigitalTwin.syncFromHash();
    } else {
      if (typeof window.TerritorialDigitalTwin?.close === 'function') {
        window.TerritorialDigitalTwin.close();
      }
      if (typeof window.initializeDecisionDetailModule === 'function') {
        window.initializeDecisionDetailModule();
      } else {
        window.setTimeout(() => {
          if (typeof window.initializeDecisionDetailModule === 'function') {
            window.initializeDecisionDetailModule();
          }
        }, 0);
      }
      if (window.decisionDetailState?.map) {
        window.setTimeout(() => window.decisionDetailState.map.invalidateSize(), 0);
      }
    }
  } else if (normalizedModule === 'decision_experience') {
    if (typeof window.initializeDecisionExperienceModule === 'function') {
      window.initializeDecisionExperienceModule();
    }
    if (window.decisionExperienceState?.map) {
      window.setTimeout(() => window.decisionExperienceState.map.invalidateSize(), 0);
    }
  } else {
    document.body.classList.remove('decision-detail-open');
    document.body.classList.remove('territorial-twin-open');
    // Integrity Gate : aucun voile / mode présentation fantôme entre modules
    document.body.classList.remove('edvs-presentation-mode');
    const presentationBar = document.querySelector('#edvs-presentation-bar');
    if (presentationBar) {
      presentationBar.hidden = true;
      presentationBar.setAttribute('aria-hidden', 'true');
    }
    const esrDrawer = document.querySelector('#esr-explain-drawer');
    if (esrDrawer) {
      esrDrawer.hidden = true;
      esrDrawer.setAttribute('aria-hidden', 'true');
    }
    if (typeof window.ExecutiveSituationRoom?.stopPresentation === 'function') {
      window.ExecutiveSituationRoom.stopPresentation();
    }
    if (typeof window.EdvsLayout?.setPresentationMode === 'function') {
      window.EdvsLayout.setPresentationMode(false);
    }
    if (typeof window.TerritorialDigitalTwin?.close === 'function') {
      window.TerritorialDigitalTwin.close();
    }
    if (typeof window.DecisionWorkspace?.detach === 'function') {
      window.DecisionWorkspace.detach();
    }
    const detailPanel = document.querySelector('#decision-detail-panel');
    if (detailPanel) {
      detailPanel.classList.remove('is-loading');
      detailPanel.classList.remove('is-territorial-twin');
      detailPanel.style.opacity = '';
      detailPanel.style.filter = '';
      detailPanel.style.pointerEvents = '';
    }
    const loadingOverlay = document.querySelector('#decision-detail-loading-overlay');
    if (loadingOverlay) {
      loadingOverlay.hidden = true;
      loadingOverlay.setAttribute('aria-hidden', 'true');
      loadingOverlay.style.display = 'none';
      loadingOverlay.style.pointerEvents = 'none';
      loadingOverlay.style.opacity = '0';
    }
  }

  if (normalizedModule === 'import') {
    initializeImportModule();
  }

  if (normalizedModule === 'export') {
    initializeExportModule();
  }
}

function fetchApiJson(endpoint) {
  const url = new URL(endpoint, API_BASE_URL).toString();
  return fetch(url, {
    headers: { Accept: 'application/json' },
    cache: 'no-store',
  }).then((response) => {
    if (!response.ok) {
      throw new Error(`Route API indisponible: ${endpoint}`);
    }
    return response.json();
  });
}

function detectDataMode() {
  if (DATA_MODE === 'json') {
    LOCAL_JSON_MODE = true;
    API_HEALTH = null;
    return Promise.resolve(null);
  }

  return fetchApiJson('/health')
    .then((health) => {
      API_HEALTH = health;
      const databaseConnected = health?.mode === 'db' && health?.status === 'ok';
      LOCAL_JSON_MODE = DATA_MODE === 'api' ? false : !databaseConnected;
      return health;
    })
    .catch(() => {
      API_HEALTH = null;
      LOCAL_JSON_MODE = DATA_MODE === 'api' ? false : true;
      return null;
    });
}

function initializeApplication() {
  detectDataMode().finally(() => {
    loadDemoEnrichmentData().finally(() => {
      if (!window.location.hash) {
        window.location.hash = 'dashboard';
      }
      renderRouteFromHash();
    });
  });
}

function loadDemoEnrichmentData() {
  if (!DEMO_ENRICHMENT_MODE) {
    platformState.demoEnrichment = null;
    return Promise.resolve(null);
  }
  if (platformState.demoEnrichmentPromise) {
    return platformState.demoEnrichmentPromise;
  }
  platformState.demoEnrichmentPromise = fetchApiJson('/knowledge/demo-enrichment')
    .then((payload) => {
      platformState.demoEnrichment = payload?.demo_enrichment_mode ? payload : null;
      return platformState.demoEnrichment;
    })
    .catch(() => {
      platformState.demoEnrichment = null;
      return null;
    });
  return platformState.demoEnrichmentPromise;
}

function initializeDashboard() {
  if (dashboardState.initialized) {
    return;
  }

  initializePlatformInteractions();
  getDashboardStats();
  getDatabaseStatus();
  getLastImports();
  getZones();
  preloadPlatformData().then(() => renderDashboardZonesSidebar());
  initializeNationalMapModule();
  setupDashboardDetailPages();
  dashboardState.initialized = true;
}

function initializeDecisionModule() {
  if (decisionState.initialized) {
    renderDecisionRows();
    return;
  }
  [
    '#decision-use-case',
    '#decision-zone',
    '#decision-province',
    '#decision-territoire',
    '#decision-population',
    '#decision-network',
    '#decision-health',
    '#decision-school',
    '#decision-activity',
    '#decision-potential',
    '#decision-connectivity-score',
    '#decision-priority-score',
    '#decision-search',
  ].forEach((selector) => {
    const element = document.querySelector(selector);
    if (!element || element.dataset.bound === 'true') return;
    element.dataset.bound = 'true';
    element.addEventListener('change', loadDecisionRows);
    element.addEventListener('input', debounceDecisionLoad);
  });
  document.querySelector('#decision-run')?.addEventListener('click', loadDecisionRows);
  document.querySelector('#decision-export-csv')?.addEventListener('click', () => {
    downloadTextFile(`sig_fdsu_decision_${getExportDateStamp()}.csv`, toCsv(decisionState.rows), 'text/csv;charset=utf-8');
  });
  document.querySelector('#decision-export-json')?.addEventListener('click', () => {
    downloadTextFile(`sig_fdsu_decision_${getExportDateStamp()}.json`, JSON.stringify(decisionState.rows, null, 2), 'application/json');
  });
  decisionState.initialized = true;
  loadDecisionRows();
}

let decisionLoadTimer = null;
function debounceDecisionLoad() {
  window.clearTimeout(decisionLoadTimer);
  decisionLoadTimer = window.setTimeout(loadDecisionRows, 350);
}

function decisionValue(selector) {
  return String(document.querySelector(selector)?.value || '').trim();
}

function appendDecisionParam(params, key, value) {
  if (value !== '' && value !== null && value !== undefined) {
    params.set(key, value);
  }
}

function buildDecisionEndpoint() {
  const useCase = decisionValue('#decision-use-case') || 'localites';
  const params = new URLSearchParams();
  appendDecisionParam(params, 'zone', decisionValue('#decision-zone'));
  appendDecisionParam(params, 'province', decisionValue('#decision-province'));
  appendDecisionParam(params, 'territoire', decisionValue('#decision-territoire'));
  appendDecisionParam(params, 'couverture_reseau', decisionValue('#decision-network'));
  appendDecisionParam(params, 'centre_sante', decisionValue('#decision-health'));
  appendDecisionParam(params, 'ecole_secondaire', decisionValue('#decision-school'));
  appendDecisionParam(params, 'activite_economique', decisionValue('#decision-activity'));
  appendDecisionParam(params, 'potentiel', decisionValue('#decision-potential'));
  appendDecisionParam(params, 'niveau_connectivite', decisionValue('#decision-connectivity-score'));
  appendDecisionParam(params, 'score_priorite_min', decisionValue('#decision-priority-score'));
  appendDecisionParam(params, 'q', decisionValue('#decision-search'));
  appendDecisionParam(params, 'population_min', decisionValue('#decision-population'));
  params.set('limit', '250');

  if (useCase === 'territoires') return `/decision/territoires-prioritaires?${params.toString()}`;
  if (useCase === 'search') return `/decision/search?${params.toString()}`;
  return `/decision/localites-prioritaires?${params.toString()}`;
}

function fetchDecisionJson(endpoint) {
  const url = new URL(endpoint, API_BASE_URL).toString();
  return fetch(url)
    .then((response) => (response.ok ? response.json() : null))
    .catch(() => null);
}

function loadDecisionRows() {
  const body = document.querySelector('#decision-results-body');
  if (body) body.innerHTML = '<tr><td colspan="9" class="empty-state">Chargement...</td></tr>';
  fetchDecisionJson(buildDecisionEndpoint()).then((payload) => {
    const rows = Array.isArray(payload) ? payload : asArray(payload?.items);
    decisionState.rows = rows;
    decisionState.selectedIndex = rows.length ? 0 : null;
    renderDecisionRows();
  });
}

function formatDecisionValue(value) {
  if (value === null || value === undefined || value === '') return 'donnée à compléter';
  if (typeof value === 'boolean') return value ? 'Oui' : 'Non';
  if (typeof value === 'number') return value.toLocaleString('fr-FR');
  return String(value);
}

function renderDecisionRows() {
  const body = document.querySelector('#decision-results-body');
  const count = document.querySelector('#decision-count');
  const rows = asArray(decisionState.rows);
  if (count) count.textContent = `${rows.length.toLocaleString('fr-FR')} résultat${rows.length > 1 ? 's' : ''}`;
  if (!body) return;
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="9" class="empty-state">Aucun résultat connu. Les données métier restent à compléter.</td></tr>';
    renderDecisionDetail(null);
    return;
  }
  body.innerHTML = rows.map((row, index) => `
    <tr data-index="${index}" class="${index === decisionState.selectedIndex ? 'selected' : ''}">
      <td>${escapeHtml(formatDecisionValue(row.score_priorite_fdsu))}</td>
      <td>${escapeHtml(row.nom || 'donnée à compléter')}</td>
      <td>${escapeHtml(formatDecisionValue(row.zone))}</td>
      <td>${escapeHtml(formatDecisionValue(row.province))}</td>
      <td>${escapeHtml(formatDecisionValue(row.population))}</td>
      <td>${escapeHtml(formatDecisionValue(row.couverture_4g))}</td>
      <td>${escapeHtml([formatDecisionValue(row.centre_sante), formatDecisionValue(row.ecole_secondaire)].join(' / '))}</td>
      <td>${escapeHtml(formatDecisionValue(row.potentiel_agricole || row.potentiel_minier || row.potentiel_commercial || row.potentiel_numerique))}</td>
      <td>${escapeHtml(formatDecisionValue(row.recommandation))}</td>
    </tr>
  `).join('');
  body.querySelectorAll('tr[data-index]').forEach((row) => {
    row.addEventListener('click', () => {
      decisionState.selectedIndex = Number(row.dataset.index);
      renderDecisionRows();
    });
  });
  renderDecisionDetail(rows[decisionState.selectedIndex ?? 0]);
}

function renderDecisionDetail(row) {
  const detail = document.querySelector('#decision-detail');
  const map = document.querySelector('#decision-map');
  if (!detail) return;
  if (!row) {
    detail.innerHTML = `
      <p class="panel-label">Fiche</p>
      <h3>Aucun élément sélectionné</h3>
      <p class="status-card-text">Les champs non renseignés apparaîtront comme donnée à compléter.</p>
    `;
    if (map) map.textContent = 'Carte décisionnelle';
    return;
  }
  if (map) {
    map.innerHTML = `
      <strong>${escapeHtml(row.nom || 'Entité')}</strong>
      <span>${escapeHtml(row.province || 'Province à compléter')} · ${escapeHtml(row.territoire || 'Territoire à compléter')}</span>
    `;
  }
  const fields = [
    ['Niveau', row.niveau],
    ['Code', row.code],
    ['Zone', row.zone],
    ['Population', row.population],
    ['Couverture 2G', row.couverture_2g],
    ['Couverture 3G', row.couverture_3g],
    ['Couverture 4G', row.couverture_4g],
    ['Couverture 5G', row.couverture_5g],
    ['Centre de santé', row.centre_sante],
    ['École primaire', row.ecole_primaire],
    ['École secondaire', row.ecole_secondaire],
    ['Marché', row.marche],
    ['Électricité', row.electricite],
    ['Activité principale', row.activite_principale],
    ['Activité secondaire', row.activite_secondaire],
    ['Potentiel agricole', row.potentiel_agricole],
    ['Potentiel minier', row.potentiel_minier],
    ['Potentiel commercial', row.potentiel_commercial],
    ['Potentiel numérique', row.potentiel_numerique],
    ['Niveau enclavement', row.niveau_enclavement],
    ['Score connectivité', row.score_connectivite],
    ['Score potentiel', row.score_potentiel],
    ['Score priorité FDSU', row.score_priorite_fdsu],
  ];
  detail.innerHTML = `
    <p class="panel-label">Fiche</p>
    <h3>${escapeHtml(row.nom || 'donnée à compléter')}</h3>
    <dl class="decision-detail-list">
      ${fields.map(([label, value]) => `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(formatDecisionValue(value))}</dd></div>`).join('')}
    </dl>
    <div class="decision-recommendation">
      <strong>Recommandation FDSU</strong>
      <p>${escapeHtml(formatDecisionValue(row.recommandation))}</p>
    </div>
    <p class="decision-missing">${escapeHtml(asArray(row.champs_a_completer).length ? `À compléter : ${row.champs_a_completer.join(', ')}` : 'Dossier complet pour les champs minimum.')}</p>
  `;
}

function initializeKnowledgeModule() {
  if (knowledgeState.initialized) {
    renderKnowledgeModule();
    return;
  }

  knowledgeState.initialized = true;
  document.querySelector('#knowledge-search')?.addEventListener('input', debounceKnowledgeSearch);
  document.querySelector('#knowledge-priority-filter')?.addEventListener('change', renderKnowledgePriorityTable);
  document.querySelector('#knowledge-sort')?.addEventListener('change', renderKnowledgePriorityTable);

  Promise.all([
    LOCAL_JSON_MODE ? Promise.resolve(localKnowledgeSummary) : fetchJson('/knowledge'),
    LOCAL_JSON_MODE ? Promise.resolve(localKnowledgePriorities) : fetchJson('/knowledge/completeness'),
    LOCAL_JSON_MODE ? Promise.resolve(buildLocalKnowledgeProfile()) : fetchJson('/knowledge/kinshasa'),
    LOCAL_JSON_MODE ? Promise.resolve(localKnowledgeOrigins) : fetchJson('/knowledge/documentary/origins').catch(() => localKnowledgeOrigins),
  ]).then(([summary, priorities, profile, origins]) => {
    knowledgeState.summary = summary || localKnowledgeSummary;
    knowledgeState.priorities = asArray(priorities).length ? priorities : localKnowledgePriorities;
    knowledgeState.profile = profile || buildLocalKnowledgeProfile();
    knowledgeState.origins = origins || localKnowledgeOrigins;
    renderKnowledgeModule();
  });
}

let knowledgeSearchTimer = null;

function debounceKnowledgeSearch() {
  window.clearTimeout(knowledgeSearchTimer);
  knowledgeSearchTimer = window.setTimeout(runKnowledgeSearch, 180);
}

function renderKnowledgeModule() {
  renderKnowledgeKpis();
  renderKnowledgeOrigins();
  renderKnowledgePriorityTable();
  renderKnowledgeProfile();
}

function renderKnowledgeOrigins() {
  const container = document.querySelector('#knowledge-data-origins');
  if (!container) return;
  const payload = knowledgeState.origins || localKnowledgeOrigins;
  const rows = asArray(payload.origins).slice(0, 8);
  const rules = [
    payload.automatic_web_collection_enabled ? 'Collecte web active' : 'Collecte web automatique désactivée',
    payload.official_publication_enabled ? 'Publication directe active' : 'Aucune publication directe',
    payload.validation_required ? 'Validation humaine obligatoire' : 'Validation non configurée',
  ];
  container.innerHTML = `
    <div class="knowledge-origin-header">
      <div>
        <p class="panel-label">Origine des données</p>
        <h3>Traçabilité CNCT</h3>
      </div>
      <span class="panel-badge">${escapeHtml(rules[2])}</span>
    </div>
    <div class="knowledge-origin-rules">
      ${rules.map((rule) => `<span>${escapeHtml(rule)}</span>`).join('')}
    </div>
    <div class="knowledge-origin-grid">
      ${rows.map((row) => `
        <article class="knowledge-origin-item">
          <strong>${escapeHtml(row.origin || 'Source')}</strong>
          <span>${escapeHtml(row.status || 'à vérifier')}</span>
          <small>${escapeHtml(`Confiance ${row.confidence ?? 0}% · Sources ${row.source_count ?? 0}`)}</small>
          <small>${escapeHtml(row.validation_status || 'proposition uniquement')}</small>
        </article>
      `).join('')}
    </div>
  `;
}

function renderKnowledgeKpis() {
  const summary = knowledgeState.summary || localKnowledgeSummary;
  const bindings = {
    'knowledge-complete': summary.complete_profiles,
    'knowledge-incomplete': summary.incomplete_profiles,
    'knowledge-no-photo': summary.profiles_without_photo,
    'knowledge-no-activities': summary.profiles_without_activities,
    'knowledge-no-challenges': summary.profiles_without_challenges,
    'knowledge-no-services': summary.profiles_without_public_services,
    'knowledge-no-connectivity': summary.profiles_without_connectivity,
    'knowledge-no-documents': summary.profiles_without_documents,
  };
  Object.entries(bindings).forEach(([id, value]) => {
    const element = document.querySelector(`#${id}`);
    if (element) element.textContent = String(value ?? 0);
  });
}

function renderKnowledgePriorityTable() {
  const body = document.querySelector('#knowledge-priority-body');
  if (!body) return;
  const priorityFilter = document.querySelector('#knowledge-priority-filter')?.value || '';
  const sortKey = document.querySelector('#knowledge-sort')?.value || 'priority';
  const priorityRank = { critique: 0, haute: 1, normale: 2 };
  const rows = (knowledgeState.priorities || [])
    .filter((row) => !priorityFilter || row.priority === priorityFilter)
    .slice()
    .sort((a, b) => {
      if (sortKey === 'completeness') return Number(a.completeness) - Number(b.completeness);
      if (sortKey === 'missing') return Number(b.missing_fields_count) - Number(a.missing_fields_count);
      if (sortKey === 'updated') return String(b.last_updated_at).localeCompare(String(a.last_updated_at));
      return (priorityRank[a.priority] ?? 9) - (priorityRank[b.priority] ?? 9);
    });

  if (rows.length === 0) {
    body.innerHTML = '<tr><td colspan="6" class="empty-state">Aucune priorité trouvée.</td></tr>';
    return;
  }
  body.innerHTML = rows.map((row) => `
    <tr>
      <td>${escapeHtml(row.province)}</td>
      <td>${escapeHtml(row.territoire)}</td>
      <td>${renderKnowledgeProgress(row.completeness)}</td>
      <td>${escapeHtml(String(row.missing_fields_count))}</td>
      <td><span class="status-badge">${escapeHtml(row.priority)}</span></td>
      <td>${escapeHtml(row.last_updated_at)}</td>
    </tr>
  `).join('');
}

function renderKnowledgeProfile() {
  const profile = knowledgeState.profile || buildLocalKnowledgeProfile();
  const title = document.querySelector('#knowledge-profile-title');
  const bars = document.querySelector('#knowledge-completeness-bars');
  const tabs = document.querySelector('#knowledge-tabs');
  const content = document.querySelector('#knowledge-tab-content');
  if (title) title.textContent = `${profile.title || 'Fiche'} · ${profile.entity_type || 'CNCT'}`;
  if (bars) {
    const completeness = profile.completeness || {};
    bars.innerHTML = Object.entries(completeness).map(([label, value]) => `
      <div class="knowledge-completeness-row">
        <span>${escapeHtml(label)}</span>
        ${renderKnowledgeProgress(value)}
      </div>
    `).join('') || '<p>Donnée non encore renseignée</p>';
  }
  if (tabs) {
    tabs.innerHTML = knowledgeSections.map(([key, label]) => `
      <button type="button" class="${knowledgeState.selectedTab === key ? 'active' : ''}" data-knowledge-tab="${escapeHtml(key)}">${escapeHtml(label)}</button>
    `).join('');
    tabs.querySelectorAll('[data-knowledge-tab]').forEach((button) => {
      button.addEventListener('click', () => {
        knowledgeState.selectedTab = button.dataset.knowledgeTab;
        renderKnowledgeProfile();
      });
    });
  }
  if (content) {
    const section = asArray(profile.sections).find((item) => item.key === knowledgeState.selectedTab);
    const sourceRows = asArray(section?.sources).length
      ? asArray(section.sources).map((source) => `
        <div class="detail-row"><span>${escapeHtml(source.source || 'Source')}</span><strong>${escapeHtml([source.author, source.date, source.confidence_level, source.status].filter(Boolean).join(' · '))}</strong></div>
        <div class="detail-row"><span>URL</span><strong>${escapeHtml(source.url || 'Donnée non encore renseignée')}</strong></div>
      `).join('')
      : '<div class="detail-row"><span>Source</span><strong>Aucune information sans source</strong></div>';
    content.innerHTML = `
      <h4>${escapeHtml(section?.label || 'Rubrique')}</h4>
      <p>${escapeHtml(formatKnowledgeValue(section?.value))}</p>
      <div class="knowledge-section-source">${sourceRows}</div>
    `;
  }
}

function renderKnowledgeProgress(value) {
  const normalized = Math.max(0, Math.min(100, Number(value) || 0));
  return `<div class="knowledge-progress" aria-label="${normalized}%"><span style="width: ${normalized}%"></span><strong>${normalized}%</strong></div>`;
}

function formatKnowledgeValue(value) {
  if (value === null || value === undefined || value === '') return 'Donnée non encore renseignée';
  if (Array.isArray(value)) return value.length ? value.join(', ') : 'Donnée non encore renseignée';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function buildLocalKnowledgeProfile() {
  const source = {
    source: 'Référentiel FDSU interne',
    author: 'SIG-FDSU RDC',
    date: '2026-07-04',
    url: '',
    confidence_level: 'interne',
    status: 'validé',
  };
  return {
    entity: 'kinshasa',
    entity_type: 'Ville-Province',
    title: 'Kinshasa',
    completeness: {
      Référentiel: 100,
      Subdivision: 100,
      Activités: 0,
      Défis: 0,
      'Services publics': 0,
      Connectivité: 0,
      Photos: 0,
      Documents: 0,
    },
    sections: knowledgeSections.map(([key, label]) => {
      const values = {
        presentation: 'Ville-Province de la RDC.',
        administration: 'Statut Ville-Province.',
        subdivision: 'Districts : Funa, Lukunga, Mont-Amba, Tshangu.',
        sources: 'Sources internes et propositions contrôlées uniquement.',
      };
      const value = values[key] || 'Donnée non encore renseignée';
      return {
        key,
        label,
        value,
        completeness: value === 'Donnée non encore renseignée' ? 0 : 100,
        sources: value === 'Donnée non encore renseignée' ? [] : [source],
      };
    }),
  };
}

function runKnowledgeSearch() {
  const query = document.querySelector('#knowledge-search')?.value.trim() || '';
  const container = document.querySelector('#knowledge-search-results');
  if (!container) return;
  if (!query) {
    container.innerHTML = '';
    return;
  }
  const source = LOCAL_JSON_MODE ? Promise.resolve(searchLocalKnowledge(query)) : fetchJson(`/knowledge/search?q=${encodeURIComponent(query)}`);
  source.then((results) => {
    const rows = asArray(results);
    container.innerHTML = rows.length
      ? rows.map((item) => `<button type="button" class="global-search-result"><strong>${escapeHtml(item.entity)}</strong><span>${escapeHtml(item.entity_type)} · ${escapeHtml(asArray(item.matched_fields).join(', ') || 'CNCT')}</span></button>`).join('')
      : '<p class="empty-state">Aucun résultat CNCT.</p>';
  });
}

function searchLocalKnowledge(query) {
  const text = query.toLowerCase();
  const profile = buildLocalKnowledgeProfile();
  return profile.sections
    .filter((section) => `${section.label} ${section.value}`.toLowerCase().includes(text))
    .map((section) => ({
      entity: profile.title,
      entity_type: profile.entity_type,
      matched_fields: [section.label],
      excerpt: formatKnowledgeValue(section.value),
      completeness: section.completeness,
    }));
}

function initializeEnrichmentModule() {
  if (enrichmentState.initialized) {
    loadEnrichmentSuggestions();
    return;
  }

  enrichmentState.initialized = true;
  const fieldFilter = document.querySelector('#enrichment-field-filter');
  const statusFilter = document.querySelector('#enrichment-status-filter');
  const refreshButton = document.querySelector('#enrichment-refresh');

  if (fieldFilter) {
    fieldFilter.innerHTML = '<option value="">Tous les champs</option>' + enrichmentFields
      .map((field) => `<option value="${escapeHtml(field)}">${escapeHtml(formatDetailLabel(field))}</option>`)
      .join('');
    fieldFilter.addEventListener('change', loadEnrichmentSuggestions);
  }
  statusFilter?.addEventListener('change', loadEnrichmentSuggestions);
  refreshButton?.addEventListener('click', loadEnrichmentSuggestions);
  loadEnrichmentSuggestions();
}

function loadEnrichmentSuggestions() {
  const status = document.querySelector('#enrichment-status-filter')?.value || '';
  const field = document.querySelector('#enrichment-field-filter')?.value || '';
  const tableBody = document.querySelector('#enrichment-suggestions-body');
  if (tableBody) {
    tableBody.innerHTML = '<tr><td colspan="6" class="empty-state">Chargement des propositions...</td></tr>';
  }

  const source = LOCAL_JSON_MODE
    ? Promise.resolve(localEnrichmentSuggestions)
    : fetchJson(`/territorial-enrichment/suggestions?limit=200${status ? `&status=${encodeURIComponent(status)}` : ''}${field ? `&field_name=${encodeURIComponent(field)}` : ''}`);

  source.then((suggestions) => {
    enrichmentState.suggestions = asArray(suggestions)
      .filter((item) => !status || item.status === status)
      .filter((item) => !field || item.field_name === field);
    if (!enrichmentState.selectedId && enrichmentState.suggestions.length > 0) {
      enrichmentState.selectedId = enrichmentState.suggestions[0].id;
    }
    renderEnrichmentSuggestions();
    renderEnrichmentDetail();
  }).catch(() => {
    if (tableBody) {
      tableBody.innerHTML = '<tr><td colspan="6" class="empty-state">Impossible de charger les propositions.</td></tr>';
    }
  });
}

function renderEnrichmentSuggestions() {
  const tableBody = document.querySelector('#enrichment-suggestions-body');
  if (!tableBody) return;
  if (enrichmentState.suggestions.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="6" class="empty-state">Aucune proposition disponible.</td></tr>';
    return;
  }

  tableBody.innerHTML = enrichmentState.suggestions.map((item) => `
    <tr data-enrichment-id="${escapeHtml(String(item.id))}" class="${item.id === enrichmentState.selectedId ? 'selected' : ''}">
      <td>${escapeHtml(item.entity_name || item.entity_type || 'Entité à qualifier')}</td>
      <td>${escapeHtml(formatDetailLabel(item.field_name))}</td>
      <td>${escapeHtml(item.source_name)}</td>
      <td>${escapeHtml(item.confidence_level)}</td>
      <td><span class="status-badge">${escapeHtml(item.status || 'proposé')}</span></td>
      <td><button type="button" class="table-action-button" data-select-enrichment="${escapeHtml(String(item.id))}">Revoir</button></td>
    </tr>
  `).join('');

  tableBody.querySelectorAll('[data-select-enrichment]').forEach((button) => {
    button.addEventListener('click', () => {
      enrichmentState.selectedId = Number(button.dataset.selectEnrichment);
      renderEnrichmentSuggestions();
      renderEnrichmentDetail();
    });
  });
}

function renderEnrichmentDetail() {
  const title = document.querySelector('#enrichment-detail-title');
  const body = document.querySelector('#enrichment-detail-body');
  if (!title || !body) return;
  const suggestion = enrichmentState.suggestions.find((item) => Number(item.id) === Number(enrichmentState.selectedId));
  if (!suggestion) {
    title.textContent = 'Aucune proposition sélectionnée';
    body.innerHTML = '<div class="empty-detail">Sélectionnez une proposition pour consulter la source, modifier la valeur, puis accepter ou rejeter.</div>';
    return;
  }

  title.textContent = suggestion.entity_name || suggestion.entity_type || 'Proposition';
  body.innerHTML = `
    <div class="detail-row"><span>Champ</span><strong>${escapeHtml(formatDetailLabel(suggestion.field_name))}</strong></div>
    <div class="detail-row"><span>Source</span><strong>${escapeHtml(suggestion.source_name)}</strong></div>
    <div class="detail-row"><span>URL</span><strong><a href="${escapeHtml(suggestion.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(suggestion.source_url)}</a></strong></div>
    <div class="detail-row"><span>Consultation</span><strong>${escapeHtml(formatAttributeValue(suggestion.consulted_at))}</strong></div>
    <div class="detail-row"><span>Confiance</span><strong>${escapeHtml(suggestion.confidence_level)}</strong></div>
    <label class="enrichment-editor-label" for="enrichment-proposed-value">Valeur proposée</label>
    <textarea id="enrichment-proposed-value" class="enrichment-editor" rows="7">${escapeHtml(suggestion.proposed_value || '')}</textarea>
    <label class="enrichment-editor-label" for="enrichment-review-note">Note de revue</label>
    <textarea id="enrichment-review-note" class="enrichment-editor" rows="3">${escapeHtml(suggestion.review_note || '')}</textarea>
    <div class="profile-actions">
      <button type="button" class="primary-button" data-enrichment-action="validé">Accepter</button>
      <button type="button" class="table-action-button" data-enrichment-action="rejeté">Rejeter</button>
      <button type="button" class="table-action-button" data-enrichment-action="proposé">Enregistrer modification</button>
    </div>
  `;

  body.querySelectorAll('[data-enrichment-action]').forEach((button) => {
    button.addEventListener('click', () => updateEnrichmentSuggestion(suggestion.id, button.dataset.enrichmentAction));
  });
}

function updateEnrichmentSuggestion(suggestionId, status) {
  const proposedValue = document.querySelector('#enrichment-proposed-value')?.value || '';
  const reviewNote = document.querySelector('#enrichment-review-note')?.value || '';
  const payload = {
    proposed_value: proposedValue,
    review_note: reviewNote,
    status,
    validated_by: 'Administrateur',
  };

  if (LOCAL_JSON_MODE) {
    enrichmentState.suggestions = enrichmentState.suggestions.map((item) => (
      Number(item.id) === Number(suggestionId)
        ? { ...item, ...payload, validated_at: status === 'validé' ? new Date().toISOString() : item.validated_at }
        : item
    ));
    const index = localEnrichmentSuggestions.findIndex((item) => Number(item.id) === Number(suggestionId));
    if (index >= 0) localEnrichmentSuggestions[index] = { ...localEnrichmentSuggestions[index], ...payload };
    renderEnrichmentSuggestions();
    renderEnrichmentDetail();
    return;
  }

  const endpoint = status === 'validé'
    ? `/territorial-enrichment/suggestions/${suggestionId}/accept`
    : status === 'rejeté'
      ? `/territorial-enrichment/suggestions/${suggestionId}/reject`
      : `/territorial-enrichment/suggestions/${suggestionId}`;
  const method = status === 'proposé' ? 'PATCH' : 'POST';
  fetch(new URL(endpoint, API_BASE_URL).toString(), {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
    .then((response) => {
      if (!response.ok) throw new Error('Mise à jour impossible');
      return response.json();
    })
    .then((updated) => {
      enrichmentState.suggestions = enrichmentState.suggestions.map((item) => (
        Number(item.id) === Number(updated.id) ? updated : item
      ));
      renderEnrichmentSuggestions();
      renderEnrichmentDetail();
    });
}

function initializeSitesModule() {
  const panel = document.querySelector('#sites-panel');
  if (!panel) return;
  const badge = panel.querySelector('.panel-badge');
  const message = panel.querySelector('#sites-module-message');
  if (badge) badge.textContent = '0 site';
  if (message) message.textContent = 'Module Sites FDSU à construire en v0.7.0.';
}

function initializeImportModule() {
  const input = document.querySelector('#import-file-input');
  const resetButton = document.querySelector('#import-reset');
  const reportButton = document.querySelector('#import-anomaly-report');
  const sheetSelect = document.querySelector('#import-sheet-select');

  if (input && input.dataset.bound !== 'true') {
    input.dataset.bound = 'true';
    input.addEventListener('change', () => previewImportFile(input.files?.[0]));
  }
  if (resetButton && resetButton.dataset.bound !== 'true') {
    resetButton.dataset.bound = 'true';
    resetButton.addEventListener('click', resetImportModule);
  }
  if (reportButton && reportButton.dataset.bound !== 'true') {
    reportButton.dataset.bound = 'true';
    reportButton.addEventListener('click', downloadImportAnomalyReport);
  }
  if (sheetSelect && sheetSelect.dataset.bound !== 'true') {
    sheetSelect.dataset.bound = 'true';
    sheetSelect.addEventListener('change', () => renderExcelSheetPreview(sheetSelect.value));
  }
}

function previewImportFile(file) {
  const fileNameElement = document.querySelector('#import-file-name');
  const previewElement = document.querySelector('#import-preview');
  const reportButton = document.querySelector('#import-anomaly-report');
  if (!previewElement) return;
  if (!file) {
    resetImportModule();
    return;
  }

  const extension = file.name.split('.').pop().toLowerCase();
  importState.file = file;
  importState.extension = extension;
  importState.workbook = null;
  importState.sheets = {};
  importState.activeSheet = '';
  importState.preview = null;
  importState.anomalies = [];
  if (fileNameElement) fileNameElement.textContent = `${file.name} - ${formatFileSize(file.size)} - .${extension}`;
  if (reportButton) reportButton.disabled = true;

  if (['kml', 'kmz', 'zip'].includes(extension)) {
    renderImportAdvancedGeoMessage(file, extension);
    return;
  }

  if (['xlsx', 'xls'].includes(extension)) {
    previewExcelFile(file);
    return;
  }

  const reader = new FileReader();
  reader.onload = () => {
    try {
      if (extension === 'csv') {
        renderImportPreview(parseCsvPreview(String(reader.result || ''), file, extension));
      } else if (['json', 'geojson'].includes(extension)) {
        renderImportPreview(parseJsonPreview(String(reader.result || ''), file, extension));
      } else {
        previewElement.innerHTML = '<p>Format reconnu mais non prévisualisable dans cette version.</p>';
      }
    } catch (error) {
      previewElement.innerHTML = `<p>Prévisualisation impossible : ${escapeHtml(error.message)}</p>`;
    }
  };
  reader.readAsText(file, 'utf-8');
}

function resetImportModule() {
  importState.file = null;
  importState.extension = '';
  importState.workbook = null;
  importState.sheets = {};
  importState.activeSheet = '';
  importState.preview = null;
  importState.anomalies = [];
  const input = document.querySelector('#import-file-input');
  const fileNameElement = document.querySelector('#import-file-name');
  const previewElement = document.querySelector('#import-preview');
  const reportButton = document.querySelector('#import-anomaly-report');
  const sheetSelect = document.querySelector('#import-sheet-select');
  if (input) input.value = '';
  if (fileNameElement) fileNameElement.textContent = 'Aucun fichier sélectionné.';
  if (previewElement) previewElement.textContent = 'Sélectionnez un fichier Excel, CSV, JSON ou GeoJSON.';
  if (reportButton) reportButton.disabled = true;
  if (sheetSelect) {
    sheetSelect.classList.add('hidden');
    sheetSelect.innerHTML = '';
  }
}

function renderImportAdvancedGeoMessage(file, extension) {
  const previewElement = document.querySelector('#import-preview');
  if (!previewElement) return;
  importState.preview = {
    fileName: file.name,
    extension,
    fileType: extension.toUpperCase(),
    totalRows: 0,
    columns: [],
    rows: [],
    detected: {},
    anomalies: [],
  };
  previewElement.innerHTML = `
    <div class="import-summary">
      <div class="detail-row"><span>Fichier</span><strong>${escapeHtml(file.name)}</strong></div>
      <div class="detail-row"><span>Taille</span><strong>${escapeHtml(formatFileSize(file.size))}</strong></div>
      <div class="detail-row"><span>Extension</span><strong>.${escapeHtml(extension)}</strong></div>
    </div>
    <p>Analyse géographique avancée prévue en backend v0.8.0.</p>
  `;
}

function previewExcelFile(file) {
  const previewElement = document.querySelector('#import-preview');
  if (!previewElement) return;
  if (typeof XLSX === 'undefined') {
    previewElement.innerHTML = '<p>SheetJS n’est pas disponible. Vérifier la connexion au CDN ou ajouter une version locale.</p>';
    return;
  }

  const reader = new FileReader();
  reader.onload = () => {
    try {
      const workbook = XLSX.read(reader.result, { type: 'array' });
      importState.workbook = workbook;
      importState.sheets = {};
      workbook.SheetNames.forEach((sheetName) => {
        importState.sheets[sheetName] = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName], { header: 1, defval: '' });
      });
      renderExcelSheetSelector(workbook.SheetNames);
      renderExcelSheetPreview(workbook.SheetNames[0]);
    } catch (error) {
      previewElement.innerHTML = `<p>Lecture Excel impossible : ${escapeHtml(error.message)}</p>`;
    }
  };
  reader.readAsArrayBuffer(file);
}

function renderExcelSheetSelector(sheetNames) {
  const sheetSelect = document.querySelector('#import-sheet-select');
  if (!sheetSelect) return;
  sheetSelect.classList.remove('hidden');
  sheetSelect.innerHTML = sheetNames.map((sheetName) => `<option value="${escapeHtml(sheetName)}">${escapeHtml(sheetName)}</option>`).join('');
}

function renderExcelSheetPreview(sheetName) {
  const rows = importState.sheets[sheetName] || [];
  importState.activeSheet = sheetName;
  const parsed = parseTableRowsPreview(rows, importState.file, importState.extension, sheetName);
  renderImportPreview(parsed);
}

function parseCsvPreview(text, file, extension) {
  const lines = text.split(/\r?\n/).filter((line) => line.trim() !== '');
  const separator = lines[0]?.includes(';') ? ';' : ',';
  const tableRows = lines.map((line) => splitCsvLine(line, separator));
  return parseTableRowsPreview(tableRows, file, extension);
}

function splitCsvLine(line, separator) {
  const values = [];
  let current = '';
  let quoted = false;
  for (const char of line) {
    if (char === '"') {
      quoted = !quoted;
    } else if (char === separator && !quoted) {
      values.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  values.push(current.trim());
  return values;
}

function parseJsonPreview(text, file, extension) {
  const parsed = JSON.parse(text);
  const rows = Array.isArray(parsed)
    ? parsed
    : Array.isArray(parsed.features)
      ? parsed.features.map((feature) => ({
        ...feature.properties,
        geometry: feature.geometry?.type,
        longitude: extractGeometryCoordinate(feature.geometry)?.lng ?? feature.properties?.longitude,
        latitude: extractGeometryCoordinate(feature.geometry)?.lat ?? feature.properties?.latitude,
      }))
      : Object.values(parsed).find(Array.isArray) || [parsed];
  const objects = asArray(rows).filter((row) => row && typeof row === 'object');
  const columns = [...new Set(objects.flatMap((row) => Object.keys(row)))];
  const matrixRows = objects.map((row) => columns.map((column) => row[column]));
  return buildImportPreview({ columns, rows: matrixRows, totalRows: objects.length, file, extension });
}

function parseTableRowsPreview(tableRows, file, extension, sheetName = '') {
  const header = asArray(tableRows[0]).map((value, index) => String(value || `colonne_${index + 1}`).trim());
  const rows = tableRows.slice(1).filter((row) => asArray(row).some((value) => String(value || '').trim() !== ''));
  return buildImportPreview({ columns: header, rows, totalRows: rows.length, file, extension, sheetName });
}

function buildImportPreview({ columns, rows, totalRows, file, extension, sheetName = '' }) {
  const detected = detectImportColumns(columns);
  const anomalies = detectImportAnomalies({ columns, rows, detected });
  const preview = {
    fileName: file?.name || importState.file?.name || '',
    extension,
    fileType: extension?.toUpperCase() || '',
    sheetName,
    totalRows,
    columns,
    rows: rows.slice(0, 50),
    detected,
    anomalies,
  };
  importState.preview = preview;
  importState.anomalies = anomalies;
  return preview;
}

function renderImportPreview({ columns, rows, totalRows, fileType, sheetName, detected, anomalies }) {
  const previewElement = document.querySelector('#import-preview');
  const reportButton = document.querySelector('#import-anomaly-report');
  if (!previewElement) return;
  const detectedRows = Object.entries(detected || {})
    .filter(([, value]) => value)
    .map(([key, value]) => `<div class="detail-row"><span>${escapeHtml(getImportFieldLabel(key))}</span><strong>${escapeHtml(value)}</strong></div>`)
    .join('');
  const anomalyItems = asArray(anomalies).slice(0, 30).map((anomaly) => `<li>${escapeHtml(anomaly.message)}</li>`).join('');
  if (reportButton) reportButton.disabled = asArray(anomalies).length === 0;
  previewElement.innerHTML = `
    <div class="import-summary">
      <div class="detail-row"><span>Type fichier</span><strong>${escapeHtml(fileType || importState.extension.toUpperCase())}</strong></div>
      <div class="detail-row"><span>Feuille</span><strong>${escapeHtml(sheetName || 'Non applicable')}</strong></div>
      <div class="detail-row"><span>Lignes</span><strong>${totalRows.toLocaleString('fr-FR')}</strong></div>
      <div class="detail-row"><span>Colonnes</span><strong>${columns.length.toLocaleString('fr-FR')}</strong></div>
    </div>
    <div class="import-columns">${columns.map((column) => `<span>${escapeHtml(column)}</span>`).join('')}</div>
    <div class="detail-card">
      <div class="detail-card-header"><div><p class="panel-label">Détection automatique</p><h3>Champs reconnus</h3></div></div>
      ${detectedRows || '<p>Aucun champ standard reconnu.</p>'}
    </div>
    <div class="detail-card">
      <div class="detail-card-header"><div><p class="panel-label">Contrôle qualité</p><h3>Anomalies</h3></div></div>
      ${anomalyItems ? `<ul>${anomalyItems}</ul>` : '<p>Aucune anomalie détectée dans la prévisualisation.</p>'}
    </div>
    <div class="table-frame">
      <table class="governance-table">
        <thead><tr>${columns.slice(0, 12).map((column) => `<th>${escapeHtml(column)}</th>`).join('')}</tr></thead>
        <tbody>
          ${rows.map((row) => `<tr>${columns.slice(0, 12).map((_column, index) => `<td>${escapeHtml(formatAttributeValue(Array.isArray(row) ? row[index] : row?.[index]))}</td>`).join('')}</tr>`).join('')}
        </tbody>
      </table>
    </div>
  `;
}

function detectImportColumns(columns) {
  const rules = {
    nom: ['nom', 'name', 'libelle', 'localite', 'localité', 'nom1', 'nom_bd', 'nom_rgc'],
    type: ['type', 'genre', 'niveau', 'type_localite', 'type_collectivite'],
    province: ['province', 'prov'],
    territoire: ['territoire', 'territory'],
    collectivite: ['collectivite', 'collectivité', 'secteur', 'chefferie'],
    groupement: ['groupement', 'grpt', 'code_grpt'],
    localite: ['localite', 'localité', 'village'],
    latitude: ['lat', 'latitude', 'y'],
    longitude: ['lon', 'lng', 'long', 'longitude', 'x'],
  };
  return Object.fromEntries(Object.entries(rules).map(([key, aliases]) => [
    key,
    columns.find((column) => aliases.some((alias) => normalizeColumnName(column).includes(normalizeColumnName(alias)))) || '',
  ]));
}

function normalizeColumnName(value) {
  return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]/g, '');
}

function getImportFieldLabel(key) {
  return {
    nom: 'Nom',
    type: 'Type',
    province: 'Province',
    territoire: 'Territoire',
    collectivite: 'Collectivité',
    groupement: 'Groupement',
    localite: 'Localité',
    latitude: 'Latitude',
    longitude: 'Longitude',
  }[key] || key;
}

function detectImportAnomalies({ columns, rows, detected }) {
  const anomalies = [];
  ['nom', 'province', 'territoire'].forEach((field) => {
    if (!detected[field]) {
      anomalies.push({ type: 'colonnes_manquantes', message: `Colonne manquante probable : ${getImportFieldLabel(field)}.` });
    }
  });
  if (!detected.latitude || !detected.longitude) {
    anomalies.push({ type: 'colonnes_manquantes', message: 'Colonnes latitude/longitude non détectées.' });
  }

  const seen = new Map();
  const indexes = Object.fromEntries(columns.map((column, index) => [column, index]));
  rows.forEach((row, index) => {
    const nom = getImportCell(row, indexes[detected.nom]);
    const province = getImportCell(row, indexes[detected.province]);
    const territoire = getImportCell(row, indexes[detected.territoire]);
    const lat = getImportCell(row, indexes[detected.latitude]);
    const lng = getImportCell(row, indexes[detected.longitude]);
    const key = [nom, province, territoire].map((value) => String(value || '').trim().toLowerCase()).join('|');
    if (key.replaceAll('|', '') === '') return;
    if (seen.has(key)) {
      anomalies.push({ type: 'doublons_probables', row: index + 2, message: `Doublon probable ligne ${index + 2} avec ligne ${seen.get(key)} : ${nom}.` });
    } else {
      seen.set(key, index + 2);
    }
    if ((lat || lng) && !isValidLatLng(lat, lng)) {
      anomalies.push({ type: 'coordonnees_invalides', row: index + 2, message: `Coordonnées invalides ligne ${index + 2}.` });
    }
    if (!province && !territoire && !getImportCell(row, indexes[detected.collectivite]) && !getImportCell(row, indexes[detected.groupement])) {
      anomalies.push({ type: 'sans_rattachement', row: index + 2, message: `Entité sans rattachement ligne ${index + 2}.` });
    }
  });
  return anomalies;
}

function getImportCell(row, index) {
  if (index === undefined || index === null || index < 0) return '';
  return Array.isArray(row) ? row[index] : '';
}

function isValidLatLng(lat, lng) {
  const latitude = Number(String(lat).replace(',', '.'));
  const longitude = Number(String(lng).replace(',', '.'));
  return Number.isFinite(latitude) && Number.isFinite(longitude) && latitude >= -90 && latitude <= 90 && longitude >= -180 && longitude <= 180;
}

function downloadImportAnomalyReport() {
  const report = {
    generated_at: new Date().toISOString(),
    file: importState.file?.name || '',
    extension: importState.extension,
    sheet: importState.activeSheet,
    summary: {
      rows: importState.preview?.totalRows || 0,
      columns: importState.preview?.columns || [],
      detected: importState.preview?.detected || {},
    },
    anomalies: importState.anomalies,
  };
  downloadTextFile(`sig_fdsu_import_anomalies_${getExportDateStamp()}.json`, JSON.stringify(report, null, 2), 'application/json');
}

function initializeExportModule() {
  const button = document.querySelector('#export-run');
  const layerSelect = document.querySelector('#export-layer-select');
  const filterElements = [
    layerSelect,
    document.querySelector('#export-province-filter'),
    document.querySelector('#export-territory-filter'),
    document.querySelector('#export-type-filter'),
  ];
  if (button && button.dataset.bound !== 'true') {
    button.dataset.bound = 'true';
    button.addEventListener('click', runPrototypeExport);
  }
  filterElements.forEach((element) => {
    if (!element || element.dataset.bound === 'true') return;
    element.dataset.bound = 'true';
    element.addEventListener('change', refreshExportFilters);
  });
  refreshExportFilters();
}

function runPrototypeExport() {
  const layerKey = document.querySelector('#export-layer-select')?.value || 'provinces';
  const format = document.querySelector('#export-format-select')?.value || 'csv';
  const status = document.querySelector('#export-status');

  if (format === 'kml') {
    if (status) status.textContent = 'KML/KMZ à préparer en backend v0.8.0.';
    return;
  }

  getLayerItemsForExport(layerKey).then((items) => {
    const rows = filterExportRows(asArray(items).map((item) => normalizeAttributeRow(item, layerKey).properties));
    if (rows.length === 0) {
      if (status) status.textContent = 'Aucune donnée disponible pour cette couche.';
      return;
    }

    const filenameBase = `sig_fdsu_${layerKey}_${getExportDateStamp()}`;
    if (format === 'json') {
      downloadTextFile(`${filenameBase}.json`, JSON.stringify(rows, null, 2), 'application/json');
    } else if (format === 'geojson') {
      const exportItems = asArray(items).filter((item) => {
        const props = normalizeAttributeRow(item, layerKey).properties;
        return filterExportRows([props]).length > 0;
      });
      downloadTextFile(`${filenameBase}.geojson`, JSON.stringify(buildFeatureCollection(exportItems, layerKey), null, 2), 'application/geo+json');
    } else {
      downloadTextFile(`${filenameBase}.csv`, toCsv(rows), 'text/csv;charset=utf-8');
    }
    if (status) status.textContent = `${rows.length.toLocaleString('fr-FR')} éléments exportés (${format === 'excel' ? 'CSV compatible Excel' : format.toUpperCase()}).`;
  });
}

function refreshExportFilters() {
  const layerKey = document.querySelector('#export-layer-select')?.value || 'provinces';
  getLayerItemsForExport(layerKey).then((items) => {
    const rows = asArray(items).map((item) => normalizeAttributeRow(item, layerKey).properties);
    updateSelectOptions(document.querySelector('#export-province-filter'), rows.map((row) => row.province).filter(Boolean), 'Toutes les provinces');
    updateSelectOptions(document.querySelector('#export-territory-filter'), rows.map((row) => row.territoire).filter(Boolean), 'Tous les territoires');
    updateSelectOptions(document.querySelector('#export-type-filter'), rows.map((row) => row.type).filter(Boolean), 'Tous les types');
    updateExportCount(rows);
  });
}

function filterExportRows(rows) {
  const province = document.querySelector('#export-province-filter')?.value || '';
  const territory = document.querySelector('#export-territory-filter')?.value || '';
  const type = document.querySelector('#export-type-filter')?.value || '';
  return rows.filter((row) => (!province || row.province === province)
    && (!territory || row.territoire === territory)
    && (!type || row.type === type));
}

function updateExportCount(rows) {
  const countElement = document.querySelector('#export-count');
  if (!countElement) return;
  countElement.textContent = `${filterExportRows(rows).length.toLocaleString('fr-FR')} élément(s) prêt(s) à exporter.`;
}

function getLayerItemsForExport(layerKey) {
  if (asArray(cartographyState.data[layerKey]).length > 0) {
    return Promise.resolve(cartographyState.data[layerKey]);
  }
  return fetchPlatformLayerData(layerKey);
}

function toCsv(rows) {
  const columns = [...new Set(rows.flatMap((row) => Object.keys(row)))];
  const escapeCsv = (value) => `"${String(value ?? '').replaceAll('"', '""')}"`;
  return [
    columns.map(escapeCsv).join(';'),
    ...rows.map((row) => columns.map((column) => escapeCsv(row[column])).join(';')),
  ].join('\n');
}

function downloadTextFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function getExportDateStamp() {
  return new Date().toISOString().slice(0, 10).replaceAll('-', '');
}

function buildHtmlTableDocument(properties) {
  const rows = Object.entries(properties || {})
    .filter(([, value]) => typeof value !== 'object')
    .map(([key, value]) => `<tr><th>${escapeHtml(formatDetailLabel(key))}</th><td>${escapeHtml(formatAttributeValue(value || missingDataText()))}</td></tr>`)
    .join('');
  return `<html><head><meta charset="utf-8"></head><body><table>${rows}</table></body></html>`;
}

function buildHtmlProfileDocument(properties) {
  const title = escapeHtml(properties.nom || properties.name || 'Fiche SIG-FDSU');
  const rows = Object.entries(properties || {})
    .filter(([, value]) => typeof value !== 'object')
    .map(([key, value]) => `<p><strong>${escapeHtml(formatDetailLabel(key))}</strong>: ${escapeHtml(formatAttributeValue(value || missingDataText()))}</p>`)
    .join('');
  return `<html><head><meta charset="utf-8"><title>${title}</title></head><body><h1>${title}</h1>${rows}</body></html>`;
}

function buildKmlFeature(properties, geometry) {
  const coordinates = extractGeometryCoordinate(geometry);
  const point = coordinates ? `${coordinates.lng},${coordinates.lat},0` : '';
  return `<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>${escapeXml(properties.nom || properties.name || 'SIG-FDSU')}</name>
      <description>${escapeXml(formatHierarchy(properties))}</description>
      ${point ? `<Point><coordinates>${point}</coordinates></Point>` : ''}
    </Placemark>
  </Document>
</kml>`;
}

function escapeXml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
}

function formatFileSize(size) {
  if (!Number.isFinite(size)) return 'Taille inconnue';
  if (size < 1024) return `${size} o`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} Ko`;
  return `${(size / (1024 * 1024)).toFixed(1)} Mo`;
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

  if (LOCAL_JSON_MODE) {
    referentielElements.searchInput.addEventListener('input', () => {
      referentielState.search = referentielElements.searchInput.value.trim().toLowerCase();
      renderAdministrativeHierarchyModule();
    });
    renderAdministrativeHierarchyModule();
    referentielState.initialized = true;
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
  if (typeof L === 'undefined') {
    showZonesMessage('Couche Zones FDSU non disponible.');
    return;
  }

  setupCartographyDrawers();
  setupCartographyMapInfo();
  setupCartographyFullscreen();
  setupCartographyPrint();
  setupCartographyFreeMode();
  setupCartographySearch();
  setupCartographyExplorerDrawer();
  setupCartographyBasemapSettings();

  if (typeof window.SigCartographyExperience?.setup === 'function') {
    window.SigCartographyExperience.setup();
  }

  const mapElement = document.querySelector('#map');
  const layerList = document.querySelector('#layer-list');
  const zoomAutoButton = document.querySelector('#zoom-auto');
  cartographyState.infoElement = document.querySelector('#carto-info');
  cartographyState.zonesMessageElement = document.querySelector('#zones-message');
  cartographyState.breadcrumbElement = document.querySelector('#map-breadcrumb');
  cartographyState.synchronizedListElement = document.querySelector('#map-synchronized-list');

  if (!mapElement || !layerList || !zoomAutoButton || !cartographyState.infoElement || !cartographyState.zonesMessageElement) {
    return;
  }

  if (cartographyState.initialized && cartographyState.map) {
    setupCartographyResizeObserver(mapElement);
    window.setTimeout(() => cartographyState.map.invalidateSize(), 0);
    preloadCartographyLayers();
    return;
  }

  if (cartographyState.map) {
    cartographyState.map.invalidateSize();
    return;
  }

  cartographyState.map = L.map(mapElement, {
    center: [0.0, 25.0],
    zoom: 5,
    minZoom: 3,
    maxZoom: 12,
    maxBounds: RDC_MAP_BOUNDS,
    maxBoundsViscosity: 0.65,
  });

  attachCartographyBasemap(cartographyState.map);

  cartographyState.layers = {
    rdcBoundary: L.geoJSON(null, {
      style: styleRdcBoundaryFeature,
    }),
    zones: L.geoJSON(null, {
      style: styleZoneFeature,
      onEachFeature: (feature, layer) => onGeoEachFeature(feature, layer, 'zones'),
    }),
    collectivites: L.geoJSON(null, {
      style: styleCollectivitesFeature,
      onEachFeature: (feature, layer) => onGeoEachFeature(feature, layer, 'collectivites'),
    }),
    provinces: L.geoJSON(null, {
      style: styleProvinceFeature,
      onEachFeature: (feature, layer) => onGeoEachFeature(feature, layer, 'provinces'),
    }),
    territoires: L.geoJSON(null, {
      style: styleTerritoryFeature,
      onEachFeature: (feature, layer) => onGeoEachFeature(feature, layer, 'territoires'),
    }),
    villes: L.geoJSON(null),
    communes: L.geoJSON(null),
    secteurs: L.geoJSON(null),
    chefferies: L.geoJSON(null),
    groupements: L.geoJSON(null, {
      pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#7c3aed', '#a78bfa'),
      onEachFeature: (feature, layer) => onGeoEachFeature(feature, layer, 'groupements'),
    }),
    villages: L.geoJSON(null, {
      pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#0f766e', '#14b8a6'),
      onEachFeature: (feature, layer) => onGeoEachFeature(feature, layer, 'villages'),
    }),
    sites: L.geoJSON(null, {
      pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#b45309', '#f59e0b'),
      onEachFeature: (feature, layer) => onGeoEachFeature(feature, layer, 'sites'),
    }),
    sites_all: L.geoJSON(null, {
      pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#b45309', '#f59e0b', 9),
      onEachFeature: (feature, layer) => onFdsuProgramSiteEachFeature(feature, layer, 'sites_all'),
    }),
    sites_40: L.geoJSON(null, {
      pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#7e22ce', '#c084fc', 10),
      onEachFeature: (feature, layer) => onFdsuProgramSiteEachFeature(feature, layer, 'sites_40'),
    }),
    sites_300: L.geoJSON(null, {
      pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#0369a1', '#38bdf8', 9),
      onEachFeature: (feature, layer) => onFdsuProgramSiteEachFeature(feature, layer, 'sites_300'),
    }),
    telecom_vodacom: L.geoJSON(null, {
      pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#e11d48', '#fb7185', 8),
      onEachFeature: (feature, layer) => onTelecomEachFeature(feature, layer, 'telecom_vodacom'),
    }),
    telecom_orange: L.geoJSON(null, {
      pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#ea580c', '#fb923c', 8),
      onEachFeature: (feature, layer) => onTelecomEachFeature(feature, layer, 'telecom_orange'),
    }),
    telecom_fiber_mw: L.geoJSON(null, {
      style: (feature) => styleTelecomFeature(feature, 'telecom_fiber_mw'),
      pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#2563eb', '#60a5fa', 7),
      onEachFeature: (feature, layer) => onTelecomEachFeature(feature, layer, 'telecom_fiber_mw'),
    }),
    telecom_fiberco: L.geoJSON(null, {
      style: (feature) => styleTelecomFeature(feature, 'telecom_fiberco'),
      pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#0891b2', '#22d3ee', 7),
      onEachFeature: (feature, layer) => onTelecomEachFeature(feature, layer, 'telecom_fiberco'),
    }),
    telecom_fttx: L.geoJSON(null, {
      style: (feature) => styleTelecomFeature(feature, 'telecom_fttx'),
      pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#7c3aed', '#a78bfa', 7),
      onEachFeature: (feature, layer) => onTelecomEachFeature(feature, layer, 'telecom_fttx'),
    }),
    routes_principales: L.geoJSON(null, {
      style: () => ({ color: '#b45309', weight: 2.5, opacity: 0.85 }),
      onEachFeature: (feature, layer) => {
        const p = feature?.properties || {};
        const html = `<strong>${p.nom || 'Sans nom'}</strong><br>Type : ${p.type || '—'}<br>Longueur : ${p.longueur_km != null ? `${p.longueur_km} km` : '—'}<br>Source : ${p.source || '—'}<br>État : ${p.etat || 'Non renseigné'}`;
        if (window.SigMapTooltips?.bind) {
          window.SigMapTooltips.bind(layer, { ...p, nom: p.nom, tooltip_html: html }, 'transport_route', { sticky: true });
        } else if (layer.bindTooltip) {
          layer.bindTooltip(html, { sticky: true, className: 'sig-map-tooltip' });
        }
      },
    }),
    spatial_relations: L.geoJSON(null, {
      style: () => ({ color: '#0d9488', weight: 2, opacity: 0.75, dashArray: '4 6' }),
      onEachFeature: (feature, layer) => onSpatialRelationEachFeature(feature, layer),
    }),
    asset_need_matches: L.geoJSON(null, {
      style: (feature) => {
        const kind = feature?.properties?.kind;
        if (kind === 'link') return { color: '#f59e0b', weight: 2, opacity: 0.8, dashArray: '3 5' };
        return { color: '#f59e0b', weight: 1 };
      },
      pointToLayer: (feature, latlng) => {
        const kind = feature?.properties?.kind;
        if (kind === 'asset') return makePointMarker(latlng, '#b45309', '#fbbf24', 9);
        return makePointMarker(latlng, '#dc2626', '#fca5a5', 6);
      },
      onEachFeature: (feature, layer) => onAssetNeedMatchEachFeature(feature, layer),
    }),
    missions: L.geoJSON(null, {
      pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#be123c', '#fb7185'),
      onEachFeature: (feature, layer) => onGeoEachFeature(feature, layer, 'missions'),
    }),
  };

  setupLayerControls(layerList);
  setupMapInteractions();
  renderMapBreadcrumb();
  renderSynchronizedLayerList();
  setupThematicControls();
  setupCartographyResizeObserver(mapElement);
  zoomAutoButton.addEventListener('click', resetMapToNationalView);
  fitMapToRdc();
  loadGeneratedLayer({
    layerKey: 'rdcBoundary',
    filePath: '/geodata/rdc_boundary.geojson',
    emptyMessage: 'Contour RDC non disponible.',
    fallbackMessage: 'Contour RDC non disponible.',
    visibleByDefault: true,
  });
  loadWebSigLayers();
  setupAttributeExplorer();
  cartographyState.initialized = true;
  if (typeof cartographyState.bindMapInfoEvents === 'function') {
    cartographyState.bindMapInfoEvents();
  }
}

const CARTOGRAPHY_PANEL_KEYS = ['layers', 'legend', 'entities', 'info', 'classification'];

function getCartographyDrawerElement(drawerKey) {
  return document.querySelector(`#carto-drawer-${drawerKey}`);
}

function getCartographyDrawerButton(drawerKey) {
  return document.querySelector(`[data-carto-drawer="${drawerKey}"]`);
}

function updateCartographySidebarVisibility() {
  const mainRow = document.querySelector('#cartography-main-row');
  const sidebar = document.querySelector('#cartography-sidebar');
  const activeDrawer = cartographyState.activeDrawer;
  const drawer = activeDrawer ? getCartographyDrawerElement(activeDrawer) : null;
  const hasOpenPanel = Boolean(drawer && !drawer.classList.contains('hidden'));
  mainRow?.classList.toggle('has-sidebar-panel', hasOpenPanel);
  sidebar?.classList.toggle('hidden', !hasOpenPanel);
  window.setTimeout(() => cartographyState.map?.invalidateSize(), 0);
}

function closeAllCartographyPanels(exceptKey = null) {
  CARTOGRAPHY_PANEL_KEYS.forEach((drawerKey) => {
    if (drawerKey === exceptKey) return;
    const drawer = getCartographyDrawerElement(drawerKey);
    if (!drawer) return;
    drawer.classList.add('hidden');
    drawer.setAttribute('aria-hidden', 'true');
    const button = getCartographyDrawerButton(drawerKey);
    if (button) {
      button.classList.remove('is-active');
      button.setAttribute('aria-expanded', 'false');
    }
  });
  if (!exceptKey) {
    cartographyState.activeDrawer = null;
    cartographyState.openDrawers = [];
    updateCartographySidebarVisibility();
  }
}

function closeCartographyDrawer(drawerEl) {
  if (!drawerEl) return;
  const drawerKey = drawerEl.dataset.drawer;
  drawerEl.classList.add('hidden');
  drawerEl.setAttribute('aria-hidden', 'true');
  const button = getCartographyDrawerButton(drawerKey);
  if (button) {
    button.classList.remove('is-active');
    button.setAttribute('aria-expanded', 'false');
  }
  cartographyState.openDrawers = asArray(cartographyState.openDrawers).filter((key) => key !== drawerKey);
  if (cartographyState.activeDrawer === drawerKey) {
    cartographyState.activeDrawer = null;
  }
  updateCartographySidebarVisibility();
}

function openCartographyDrawerPanel(drawerKey) {
  const drawer = getCartographyDrawerElement(drawerKey);
  if (!drawer) return;
  closeAllCartographyPanels(drawerKey);
  drawer.classList.remove('hidden');
  drawer.setAttribute('aria-hidden', 'false');
  const button = getCartographyDrawerButton(drawerKey);
  if (button) {
    button.classList.add('is-active');
    button.setAttribute('aria-expanded', 'true');
  }
  cartographyState.activeDrawer = drawerKey;
  cartographyState.openDrawers = [drawerKey];
  updateCartographySidebarVisibility();
}

function toggleCartographyDrawer(drawerKey) {
  const drawer = getCartographyDrawerElement(drawerKey);
  if (!drawer) return;
  if (!drawer.classList.contains('hidden') && cartographyState.activeDrawer === drawerKey) {
    closeCartographyDrawer(drawer);
    return;
  }
  openCartographyDrawerPanel(drawerKey);
}

function setupCartographyDrawers() {
  if (document.body.dataset.cartographyDrawersBound === 'true') return;
  document.body.dataset.cartographyDrawersBound = 'true';

  document.querySelectorAll('[data-carto-drawer]').forEach((button) => {
    button.addEventListener('click', () => {
      toggleCartographyDrawer(button.dataset.cartoDrawer);
    });
  });

  document.querySelectorAll('[data-carto-drawer-close]').forEach((button) => {
    button.addEventListener('click', () => {
      closeCartographyDrawer(button.closest('.cartography-drawer'));
    });
  });
}

function setupCartographyFreeMode() {
  if (document.body.dataset.cartographyFreeModeBound === 'true') return;
  document.body.dataset.cartographyFreeModeBound = 'true';

  const button = document.querySelector('#carto-free-mode');
  button?.addEventListener('click', () => {
    cartographyState.freeMode = !cartographyState.freeMode;
    button.classList.toggle('is-active', cartographyState.freeMode);
    button.setAttribute('aria-pressed', String(cartographyState.freeMode));
    showZonesMessage(cartographyState.freeMode
      ? 'Cartographie libre : navigation sans contrainte hiérarchique.'
      : 'Mode hiérarchique restauré.');
    renderSynchronizedLayerList();
  });
}

function setupCartographySearch() {
  if (document.body.dataset.cartographySearchBound === 'true') return;
  document.body.dataset.cartographySearchBound = 'true';

  const input = document.querySelector('#carto-map-search');
  input?.addEventListener('input', () => {
    cartographyState.mapSearchTerm = String(input.value || '').trim();
    renderSynchronizedLayerList();
    if (cartographyState.mapSearchTerm) {
      openCartographyDrawerPanel('entities');
    }
  });
}

function openCartographyExplorerDrawer() {
  const drawer = document.querySelector('#cartography-explorer-drawer');
  if (!drawer) return;
  drawer.classList.remove('hidden');
  drawer.setAttribute('aria-hidden', 'false');
  renderAttributeExplorer();
}

function closeCartographyExplorerDrawer() {
  const drawer = document.querySelector('#cartography-explorer-drawer');
  if (!drawer) return;
  drawer.classList.add('hidden');
  drawer.setAttribute('aria-hidden', 'true');
}

function setupCartographyExplorerDrawer() {
  if (document.body.dataset.cartographyExplorerBound === 'true') return;
  document.body.dataset.cartographyExplorerBound = 'true';

  document.querySelectorAll('[data-carto-explorer-open]').forEach((button) => {
    button.addEventListener('click', openCartographyExplorerDrawer);
  });
  document.querySelectorAll('[data-carto-explorer-close]').forEach((button) => {
    button.addEventListener('click', closeCartographyExplorerDrawer);
  });
}

function updateCartographyBasemapStatus(detail = {}) {
  const status = document.querySelector('#carto-basemap-status');
  if (!status) return;
  const preference = detail.preference || cartographyState.basemapManager?.getPreference?.() || 'auto';
  const label = detail.label || cartographyState.basemapManager?.getActiveProviderLabel?.();
  if (!label) {
    status.textContent = preference === 'auto'
      ? 'Mode automatique — recherche d’un fournisseur disponible…'
      : 'Application du fond de carte…';
    return;
  }
  const modeLabel = preference === 'auto' ? 'Automatique' : 'Manuel';
  status.textContent = `Actif : ${label} (${modeLabel})`;
}

function syncCartographyBasemapRadios(preference) {
  const value = preference || cartographyState.basemapManager?.getPreference?.() || 'auto';
  document.querySelectorAll('input[name="carto-basemap"]').forEach((input) => {
    input.checked = input.value === value;
  });
}

function ensureCartographyBasemapManager() {
  if (cartographyState.basemapManager) return cartographyState.basemapManager;
  if (typeof window.SigBasemapManager !== 'function') return null;
  cartographyState.basemapManager = new window.SigBasemapManager({
    timeoutMs: 3000,
    retries: 1,
    onChange: (detail) => {
      updateCartographyBasemapStatus(detail);
      syncCartographyBasemapRadios(detail.preference);
    },
  });
  return cartographyState.basemapManager;
}

function attachCartographyBasemap(map) {
  const manager = ensureCartographyBasemapManager();
  if (!manager || !map) {
    if (typeof L !== 'undefined' && map) {
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        maxZoom: 20,
        subdomains: 'abcd',
        className: 'cartography-basemap-tiles',
      }).addTo(map);
    }
    return Promise.resolve(null);
  }
  syncCartographyBasemapRadios(manager.getPreference());
  updateCartographyBasemapStatus({ preference: manager.getPreference() });
  showZonesMessage('Fond de carte : recherche d’un fournisseur disponible…');
  return manager.attach(map).then((providerId) => {
    const label = manager.getActiveProviderLabel() || providerId;
    if (label) {
      showZonesMessage(`Fond de carte : ${label}`);
    }
    updateCartographyBasemapStatus({
      preference: manager.getPreference(),
      label,
      providerId,
    });
    return providerId;
  });
}

function setupCartographyBasemapSettings() {
  if (document.body.dataset.cartographyBasemapSettingsBound === 'true') return;
  document.body.dataset.cartographyBasemapSettingsBound = 'true';

  const manager = ensureCartographyBasemapManager();
  if (manager) {
    syncCartographyBasemapRadios(manager.getPreference());
    updateCartographyBasemapStatus({ preference: manager.getPreference() });
  }

  document.querySelectorAll('input[name="carto-basemap"]').forEach((input) => {
    input.addEventListener('change', () => {
      if (!input.checked) return;
      const preference = input.value;
      const activeManager = ensureCartographyBasemapManager();
      if (!activeManager) return;
      updateCartographyBasemapStatus({ preference });
      showZonesMessage('Fond de carte : bascule en cours…');
      activeManager.setPreferenceAndAttach(preference).then((providerId) => {
        const label = activeManager.getActiveProviderLabel() || providerId;
        if (label) showZonesMessage(`Fond de carte : ${label}`);
      });
    });
  });
}

function setupCartographyMapInfo() {
  if (cartographyState.mapInfoBound) return;
  cartographyState.mapInfoBound = true;

  const panel = document.querySelector('#carto-map-info-panel');
  const scaleElement = document.querySelector('#carto-map-scale');
  const positionElement = document.querySelector('#carto-map-position');
  const zoomElement = document.querySelector('#carto-map-zoom');

  document.querySelector('[data-carto-map-info-close]')?.addEventListener('click', () => {
    panel?.classList.add('hidden');
  });

  const updateMapInfo = (latlng) => {
    if (!cartographyState.map) return;
    const zoom = cartographyState.map.getZoom();
    const center = latlng || cartographyState.map.getCenter();
    if (zoomElement) zoomElement.textContent = String(zoom);
    if (positionElement && center) {
      positionElement.textContent = `${center.lat.toFixed(4)}°, ${center.lng.toFixed(4)}°`;
    }
    if (scaleElement && center) {
      const metersPerPixel = (156543.03392 * Math.cos((center.lat * Math.PI) / 180)) / (2 ** zoom);
      const scale = Math.round((metersPerPixel * 100 * 39.37) / 0.0254);
      scaleElement.textContent = scale > 0 ? `1:${scale.toLocaleString('fr-FR')}` : '—';
    }
  };

  cartographyState.bindMapInfoEvents = () => {
    if (!cartographyState.map || cartographyState.mapInfoEventsBound) return;
    cartographyState.mapInfoEventsBound = true;
    cartographyState.map.on('mousemove', (event) => updateMapInfo(event.latlng));
    cartographyState.map.on('zoomend moveend', () => updateMapInfo(cartographyState.map.getCenter()));
    updateMapInfo(cartographyState.map.getCenter());
  };
}

function setupCartographyFullscreen() {
  // Conservé comme alias historique — le Mode Focus remplace le plein écran.
  setupCartographyFocusMode();
}

function isCartographyFocusMode() {
  return document.body.classList.contains('cartography-focus-mode');
}

function setCartographyFocusMode(enabled) {
  const focusBtn = document.querySelector('#carto-focus-btn');
  const focusBar = document.querySelector('#cartography-focus-bar');
  const stage = document.querySelector('#cartography-map-stage');
  const entering = Boolean(enabled);

  // Interdit : fullscreen natif navigateur (impasse UX sans contrôle visible).
  if (document.fullscreenElement && document.exitFullscreen) {
    document.exitFullscreen().catch(() => {});
  }

  document.body.classList.toggle('cartography-focus-mode', entering);

  if (focusBar) {
    focusBar.hidden = !entering;
    if (entering) focusBar.removeAttribute('hidden');
    else focusBar.setAttribute('hidden', '');
  }

  if (focusBtn) {
    focusBtn.classList.toggle('is-active', entering);
    const focusLabel = focusBtn.querySelector('.cartography-premium-btn__label');
    if (focusLabel) focusLabel.textContent = entering ? 'Plein écran actif' : 'Plein écran';
    focusBtn.setAttribute('aria-pressed', entering ? 'true' : 'false');
    focusBtn.title = entering
      ? 'Plein écran actif — Quitter ou Échap'
      : 'Plein écran applicatif — agrandir la carte';
  }

  if (entering) {
    // Masquer les tiroirs latéraux carto pour maximiser la carte
    document.querySelectorAll('#cartographie-panel .cartography-drawer:not(.hidden)').forEach((drawer) => {
      drawer.classList.add('hidden');
    });
    document.querySelectorAll('#cartographie-panel [data-carto-drawer][aria-expanded="true"]').forEach((btn) => {
      btn.setAttribute('aria-expanded', 'false');
    });
    document.querySelector('#cartography-main-row')?.classList.remove('has-sidebar-panel');
  }

  // Conserver zoom/centre : on ne recrée pas la carte, on recalcule seulement la taille.
  window.setTimeout(() => {
    cartographyState.map?.invalidateSize({ animate: false });
  }, 0);
  window.setTimeout(() => {
    cartographyState.map?.invalidateSize({ animate: false });
  }, 120);

  if (stage) {
    stage.classList.remove('is-fullscreen');
  }
}

function setupCartographyFocusMode() {
  if (document.body.dataset.cartographyFocusBound === 'true') return;
  document.body.dataset.cartographyFocusBound = 'true';

  const enterOrToggle = () => {
    setCartographyFocusMode(!isCartographyFocusMode());
  };
  const exitFocus = () => {
    if (isCartographyFocusMode()) setCartographyFocusMode(false);
  };

  document.querySelector('#carto-focus-btn')?.addEventListener('click', enterOrToggle);
  document.querySelector('#carto-focus-exit')?.addEventListener('click', exitFocus);
  document.querySelector('#carto-focus-back')?.addEventListener('click', exitFocus);

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && isCartographyFocusMode()) {
      event.preventDefault();
      exitFocus();
    }
  });

  // Si l'utilisateur quitte le module cartographie, sortir du Mode Focus.
  document.querySelectorAll('.nav-item[data-module]').forEach((item) => {
    item.addEventListener('click', () => {
      if (item.getAttribute('data-module') !== 'cartographie') exitFocus();
    });
  });
}

function setupCartographyPrint() {
  if (document.body.dataset.cartographyPrintBound === 'true') return;
  document.body.dataset.cartographyPrintBound = 'true';
  document.querySelector('#carto-print-btn')?.addEventListener('click', () => {
    window.print();
  });
}

function setupCartographyResizeObserver(mapElement) {
  if (!mapElement || cartographyState.resizeObserver) return;
  const invalidate = () => {
    if (cartographyState.map) {
      window.requestAnimationFrame(() => cartographyState.map.invalidateSize());
    }
  };
  if (typeof ResizeObserver !== 'undefined') {
    cartographyState.resizeObserver = new ResizeObserver(invalidate);
    cartographyState.resizeObserver.observe(mapElement);
    const mainRow = document.querySelector('#cartography-main-row');
    if (mainRow) cartographyState.resizeObserver.observe(mainRow);
  }
  if (cartographyState.windowResizeBound !== true) {
    cartographyState.windowResizeBound = true;
    window.addEventListener('resize', invalidate);
  }
}

function isFdsuSitesProgramLayer(layerKey) {
  return Boolean(FDSU_SITES_PROGRAM_LAYERS[layerKey]);
}

function getCartographyLayerLabel(layerKey) {
  if (FDSU_SITES_PROGRAM_LAYERS[layerKey]) return FDSU_SITES_PROGRAM_LAYERS[layerKey].label;
  if (TELECOM_LAYERS[layerKey]) return TELECOM_LAYERS[layerKey].label;
  if (TRANSPORT_LAYERS[layerKey]) return TRANSPORT_LAYERS[layerKey].label;
  if (SPATIAL_ANALYSIS_LAYERS[layerKey]) return SPATIAL_ANALYSIS_LAYERS[layerKey].label;
  return WEB_SIG_LAYER_DEFINITIONS[layerKey]?.label || layerKey;
}

function rebuildSitesAllLayer() {
  const layer = cartographyState.layers.sites_all;
  if (!layer) return;

  const features = [];
  asArray(FDSU_SITES_PROGRAM_LAYERS.sites_all.programKeys).forEach((programKey) => {
    asArray(cartographyState.features[programKey]).forEach((feature) => {
      features.push(feature);
    });
  });

  layer.clearLayers();
  cartographyState.featureLayers.sites_all = {};

  if (features.length > 0) {
    layer.addData({ type: 'FeatureCollection', features });
    cartographyState.features.sites_all = features;
    cartographyState.layerStatus.sites_all = true;
    return;
  }

  cartographyState.features.sites_all = [];
  cartographyState.layerStatus.sites_all = false;
}

function canUseProgramDbData() {
  return !LOCAL_JSON_MODE && API_HEALTH?.mode === 'db' && API_HEALTH?.status === 'ok';
}

function isSpatialAnalysisLayer(layerKey) {
  return Boolean(SPATIAL_ANALYSIS_LAYERS[layerKey]);
}

function resolveSpatialAnalysisDataPath(definition) {
  if (!definition) return null;
  if (canUseProgramDbData() && definition.apiPath) return definition.apiPath;
  return null;
}

function onSpatialRelationEachFeature(feature, layer) {
  if (!layer) return;
  const properties = feature?.properties || {};
  const distance = properties.distance_m != null ? `${Math.round(properties.distance_m)} m` : '';
  const lines = [
    ['strong', properties.infra_name || properties.line_name || 'Relation spatiale'],
    ['label', 'Type', properties.relation_type],
    ['label', 'Distance', distance],
    ['label', 'Opérateur', properties.operator_name || properties.operator_code],
  ];
  layer.bindPopup(
    `<div class="telecom-popup">${lines.map((entry) => {
      if (entry[0] === 'strong') return entry[1] ? `<strong>${escapeHtml(entry[1])}</strong>` : '';
      const value = String(entry[2] ?? '').trim();
      return value ? `${escapeHtml(entry[1])} : ${escapeHtml(value)}` : '';
    }).filter(Boolean).join('<br>')}</div>`,
    { maxWidth: 280, className: 'telecom-popup-wrapper' },
  );
  if (typeof window !== 'undefined' && window.SigMapTooltips?.bind) {
    window.SigMapTooltips.bind(layer, {
      ...properties,
      relation_type: properties.relation_type,
      distance_m: properties.distance_m,
      name: properties.infra_name || properties.line_name || 'Correspondance spatiale',
    }, 'spatial_match', { interactive: false, hint: false });
  }
}

function onAssetNeedMatchEachFeature(feature, layer) {
  if (!layer) return;
  const p = feature?.properties || {};
  const kind = p.kind || 'linked_locality';
  if (kind === 'link') {
    if (window.SigMapTooltips?.bind) {
      window.SigMapTooltips.bind(layer, p, 'spatial_match', { hint: false });
    }
    return;
  }
  if (kind === 'asset') {
    if (window.SigMapTooltips?.bind) {
      window.SigMapTooltips.bind(layer, {
        ...p,
        site_code: p.code,
        program_code: p.programme,
        population: p.impact_total_population,
      }, 'site', {
        onClick: () => {
          const id = p.code || p.id;
          if (id && typeof window.openDecisionCase === 'function') window.openDecisionCase('site', id, p.programme);
          else if (id) window.location.hash = `decision-case/site/${encodeURIComponent(id)}`;
        },
      });
    }
    return;
  }
  if (window.SigMapTooltips?.bind) {
    window.SigMapTooltips.bind(layer, p, 'uncovered_locality', {
      onClick: () => {
        const assetId = p.asset_business_id;
        if (assetId && typeof window.openSpatialImpact === 'function') window.openSpatialImpact('site', assetId);
        else window.location.hash = 'decision-detail/population-non-couverte';
      },
    });
  }
}

function ensureSpatialAnalysisLayerLoaded(layerKey) {
  const definition = SPATIAL_ANALYSIS_LAYERS[layerKey];
  if (!definition) return Promise.resolve([]);

  if (cartographyState.layerLoadPromises[layerKey]) {
    return cartographyState.layerLoadPromises[layerKey];
  }

  const layer = cartographyState.layers[layerKey];
  if ((layer?.getLayers?.().length ?? 0) > 0) {
    return Promise.resolve(layer.getLayers());
  }

  const sourcePath = resolveSpatialAnalysisDataPath(definition);
  if (!sourcePath) {
    cartographyState.layerStatus[layerKey] = false;
    cartographyState.features[layerKey] = [];
    return Promise.resolve([]);
  }

  cartographyState.layerLoadPromises[layerKey] = fetchJson(sourcePath)
    .then((geojson) => {
      if (!layer) return [];
      if (!geojson || !Array.isArray(geojson.features)) {
        cartographyState.layerStatus[layerKey] = false;
        cartographyState.features[layerKey] = [];
        return [];
      }
      layer.clearLayers();
      cartographyState.featureLayers[layerKey] = {};
      if (geojson.features.length > 0) {
        layer.addData(geojson);
        cartographyState.features[layerKey] = geojson.features;
        cartographyState.layerStatus[layerKey] = true;
      } else {
        cartographyState.features[layerKey] = [];
        cartographyState.layerStatus[layerKey] = false;
      }
      return layer.getLayers();
    })
    .catch(() => {
      cartographyState.layerStatus[layerKey] = false;
      cartographyState.features[layerKey] = [];
      return [];
    })
    .finally(() => {
      cartographyState.layerLoadPromises[layerKey] = null;
    });

  return cartographyState.layerLoadPromises[layerKey];
}

function isTelecomLayer(layerKey) {
  return Boolean(TELECOM_LAYERS[layerKey]);
}

function isTransportLayer(layerKey) {
  return Boolean(TRANSPORT_LAYERS[layerKey]);
}

function resolveTelecomDataPath(definition) {
  if (!definition) return null;
  if (canUseProgramDbData() && definition.apiPath) return definition.apiPath;
  return null;
}

function styleTelecomFeature(feature, layerKey) {
  const definition = TELECOM_LAYERS[layerKey] || {};
  const geometryType = feature?.geometry?.type || 'LineString';
  if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
    return {
      color: definition.color || '#64748b',
      weight: 1,
      opacity: 0.85,
      fillColor: definition.fillColor || definition.color || '#64748b',
      fillOpacity: 0.18,
    };
  }
  return {
    color: definition.color || '#64748b',
    weight: 2,
    opacity: 0.85,
  };
}

function buildTelecomPopupHtml(properties) {
  const name = properties.infra_name || properties.line_name || properties.polygon_name || properties.name || 'Infrastructure';
  const infraType = properties.infra_type || properties.line_type || properties.polygon_type || properties.infra_category || 'Non renseigné';
  const distance = properties.distance_to_selected_site_m != null
    ? `${Math.round(properties.distance_to_selected_site_m)} m`
    : (properties.distance_m != null ? `${Math.round(properties.distance_m)} m` : '');
  const lines = [
    ['strong', name],
    ['label', 'Type', infraType],
    ['label', 'Opérateur', properties.operator_name || properties.operator_code],
    ['label', 'Technologie', properties.technology],
    ['label', 'Distance au site sélectionné', distance],
    ['label', 'Source', properties.source_label || properties.data_source || 'Référentiel télécom'],
  ];
  // Ne jamais exposer de nom de fichier technique au DG
  if (properties.province) lines.push(['text', properties.province]);
  if (properties.territoire) lines.push(['text', properties.territoire]);

  return `
    <div class="telecom-popup decision-map-popup">
      ${lines.map((entry) => {
        if (entry[0] === 'strong') {
          const value = String(entry[1] || '').trim();
          return value ? `<strong>${escapeHtml(value)}</strong>` : '';
        }
        if (entry[0] === 'label') {
          const value = String(entry[2] ?? '').trim();
          if (!value) return '';
          return `${escapeHtml(entry[1])} : ${escapeHtml(value)}`;
        }
        const value = String(entry[1] || '').trim();
        return value ? escapeHtml(value) : '';
      }).filter(Boolean).join('<br>')}
    </div>
  `;
}

function onTelecomEachFeature(feature, layer, layerKey) {
  if (!layer) return;
  const properties = feature?.properties || {};
  const featureId = getFeatureId(properties, layerKey);
  if (!cartographyState.featureLayers[layerKey]) cartographyState.featureLayers[layerKey] = {};
  cartographyState.featureLayers[layerKey][featureId] = layer;
  layer.bindPopup(buildTelecomPopupHtml(properties), { maxWidth: 280, className: 'telecom-popup-wrapper' });
  renderSmartTooltip(feature, layer, layerKey);
}

function ensureTelecomLayerLoaded(layerKey) {
  const definition = TELECOM_LAYERS[layerKey];
  if (!definition) return Promise.resolve([]);

  if (cartographyState.layerLoadPromises[layerKey]) {
    return cartographyState.layerLoadPromises[layerKey];
  }

  const layer = cartographyState.layers[layerKey];
  if ((layer?.getLayers?.().length ?? 0) > 0) {
    return Promise.resolve(layer.getLayers());
  }

  const sourcePath = resolveTelecomDataPath(definition);
  if (!sourcePath) {
    cartographyState.layerStatus[layerKey] = false;
    cartographyState.features[layerKey] = [];
    return Promise.resolve([]);
  }

  cartographyState.layerLoadPromises[layerKey] = fetchJson(sourcePath)
    .then((geojson) => {
      if (!layer) return [];
      if (!geojson || !Array.isArray(geojson.features) || geojson.features.length === 0) {
        cartographyState.layerStatus[layerKey] = false;
        cartographyState.features[layerKey] = [];
        return [];
      }
      layer.clearLayers();
      cartographyState.featureLayers[layerKey] = {};
      layer.addData(geojson);
      cartographyState.features[layerKey] = geojson.features;
      cartographyState.layerStatus[layerKey] = true;
      return layer.getLayers();
    })
    .catch(() => {
      cartographyState.layerStatus[layerKey] = false;
      cartographyState.features[layerKey] = [];
      return [];
    })
    .finally(() => {
      cartographyState.layerLoadPromises[layerKey] = null;
    });

  return cartographyState.layerLoadPromises[layerKey];
}

function ensureTransportLayerLoaded(layerKey) {
  const definition = TRANSPORT_LAYERS[layerKey];
  if (!definition) return Promise.resolve([]);
  if (cartographyState.layerLoadPromises[layerKey]) {
    return cartographyState.layerLoadPromises[layerKey];
  }
  const layer = cartographyState.layers[layerKey];
  if ((layer?.getLayers?.().length ?? 0) > 0) {
    return Promise.resolve(layer.getLayers());
  }
  const sourcePath = definition.apiPath;
  cartographyState.layerLoadPromises[layerKey] = fetchJson(sourcePath)
    .then((geojson) => {
      if (!layer) return [];
      if (!geojson || !Array.isArray(geojson.features) || geojson.features.length === 0) {
        cartographyState.layerStatus[layerKey] = false;
        cartographyState.features[layerKey] = [];
        return [];
      }
      layer.clearLayers();
      cartographyState.featureLayers[layerKey] = {};
      layer.addData(geojson);
      cartographyState.features[layerKey] = geojson.features;
      cartographyState.layerStatus[layerKey] = true;
      return layer.getLayers();
    })
    .catch(() => {
      cartographyState.layerStatus[layerKey] = false;
      cartographyState.features[layerKey] = [];
      return [];
    })
    .finally(() => {
      cartographyState.layerLoadPromises[layerKey] = null;
    });
  return cartographyState.layerLoadPromises[layerKey];
}

function resolveFdsuProgramDataPath(definition, panelFormat) {
  if (!definition) return null;
  if (canUseProgramDbData()) {
    if (panelFormat && definition.panelApiPath) return definition.panelApiPath;
    if (definition.apiPath) return definition.apiPath;
  }
  return definition.filePath || null;
}

function ensureFdsuSitesProgramLayerLoaded(layerKey) {
  const definition = FDSU_SITES_PROGRAM_LAYERS[layerKey];
  if (!definition) return Promise.resolve([]);

  if (definition.virtual) {
    const programKeys = asArray(definition.programKeys).filter((programKey) => {
      const programDefinition = FDSU_SITES_PROGRAM_LAYERS[programKey];
      return resolveFdsuProgramDataPath(programDefinition, false);
    });
    if (!programKeys.length) {
      rebuildSitesAllLayer();
      return Promise.resolve(cartographyState.layers.sites_all?.getLayers?.() || []);
    }
    return Promise.all(programKeys.map((programKey) => ensureFdsuSitesProgramLayerLoaded(programKey)))
      .then(() => {
        rebuildSitesAllLayer();
        return cartographyState.layers.sites_all?.getLayers?.() || [];
      });
  }

  if (cartographyState.layerLoadPromises[layerKey]) {
    return cartographyState.layerLoadPromises[layerKey];
  }

  const layer = cartographyState.layers[layerKey];
  if ((layer?.getLayers?.().length ?? 0) > 0) {
    return Promise.resolve(layer.getLayers());
  }

  const sourcePath = resolveFdsuProgramDataPath(definition, false);
  if (!sourcePath) {
    return Promise.resolve([]);
  }

  cartographyState.layerLoadPromises[layerKey] = fetchJson(sourcePath)
    .then((geojson) => {
      if (!layer) return [];
      if (!geojson || !Array.isArray(geojson.features) || geojson.features.length === 0) {
        cartographyState.layerStatus[layerKey] = false;
        cartographyState.features[layerKey] = [];
        return [];
      }

      layer.clearLayers();
      cartographyState.featureLayers[layerKey] = {};
      layer.addData(geojson);
      cartographyState.features[layerKey] = geojson.features;
      cartographyState.layerStatus[layerKey] = true;

      if (cartographyState.map?.hasLayer(cartographyState.layers.sites_all)) {
        rebuildSitesAllLayer();
      }

      return layer.getLayers();
    })
    .catch(() => {
      cartographyState.layerStatus[layerKey] = false;
      cartographyState.features[layerKey] = [];
      return [];
    })
    .finally(() => {
      cartographyState.layerLoadPromises[layerKey] = null;
    });

  return cartographyState.layerLoadPromises[layerKey];
}

function isManagedCartographyLayer(layerKey) {
  return Boolean(WEB_SIG_LAYER_DEFINITIONS[layerKey]) || layerKey === 'zones' || isFdsuSitesProgramLayer(layerKey) || isTelecomLayer(layerKey) || isTransportLayer(layerKey) || isSpatialAnalysisLayer(layerKey);
}

function ensureCartographyLayerLoaded(layerKey) {
  if (layerKey === 'rdcBoundary') {
    const layer = cartographyState.layers[layerKey];
    return Promise.resolve(layer?.getLayers?.() || []);
  }
  if (isSpatialAnalysisLayer(layerKey)) {
    return ensureSpatialAnalysisLayerLoaded(layerKey);
  }
  if (isTelecomLayer(layerKey)) {
    return ensureTelecomLayerLoaded(layerKey);
  }
  if (isTransportLayer(layerKey)) {
    return ensureTransportLayerLoaded(layerKey);
  }
  if (isFdsuSitesProgramLayer(layerKey)) {
    return ensureFdsuSitesProgramLayerLoaded(layerKey);
  }
  if (layerKey === 'zones') {
    return ensureCartographyLayerLoaded('provinces').then(() => {
      if (asArray(cartographyState.features.zones).length === 0) {
        buildZoneLayerFromProvinces(asArray(cartographyState.data.provinces));
      }
      return asArray(cartographyState.features.zones);
    });
  }
  const definition = WEB_SIG_LAYER_DEFINITIONS[layerKey];
  if (!definition) return Promise.resolve([]);
  const layer = cartographyState.layers[layerKey];
  const hasLayerGraphics = (layer?.getLayers?.().length ?? 0) > 0;
  if (asArray(cartographyState.features[layerKey]).length > 0 && hasLayerGraphics) {
    return Promise.resolve(cartographyState.features[layerKey]);
  }
  if (asArray(cartographyState.data[layerKey]).length > 0) {
    hydrateCartographyLayerFromCache(layerKey);
    if ((layer?.getLayers?.().length ?? 0) > 0) {
      return Promise.resolve(cartographyState.features[layerKey]);
    }
  }
  if (!cartographyState.layerLoadPromises[layerKey]) {
    cartographyState.layerLoadPromises[layerKey] = loadWebSigLayer(layerKey, definition)
      .finally(() => {
        cartographyState.layerLoadPromises[layerKey] = null;
      });
  }
  return cartographyState.layerLoadPromises[layerKey];
}

function hydrateCartographyLayerFromCache(layerKey) {
  const definition = WEB_SIG_LAYER_DEFINITIONS[layerKey];
  const layer = cartographyState.layers[layerKey];
  if (!definition || !layer) return false;
  const filteredItems = asArray(cartographyState.data[layerKey])
    .filter((item) => !definition.filter || definition.filter(item));
  const featureCollection = buildFeatureCollection(filteredItems, layerKey);
  cartographyState.features[layerKey] = featureCollection.features;
  cartographyState.featureLayers[layerKey] = {};
  layer.clearLayers();
  if (featureCollection.features.length > 0) {
    layer.addData(featureCollection);
    cartographyState.layerStatus[layerKey] = true;
    return true;
  }
  cartographyState.layerStatus[layerKey] = filteredItems.length > 0 ? 'attributes-only' : false;
  return false;
}

function openCartographyDrawer(drawerKey) {
  openCartographyDrawerPanel(drawerKey);
}

function setCartographyLayerVisible(layerKey, visible, checkbox) {
  const layer = cartographyState.layers[layerKey];
  if (!layer || !cartographyState.map) return Promise.resolve(false);

  if (!visible) {
    cartographyState.map.removeLayer(layer);
    if (checkbox) checkbox.checked = false;
    refreshCartographicLayerPresentation();
    renderSynchronizedLayerList();
    updateLayerAvailabilityMessage();
    return Promise.resolve(true);
  }

  return ensureCartographyLayerLoaded(layerKey).then(() => {
    refreshVisibleCartographyLayer(layerKey);
    const featureCount = layer.getLayers().length;
    const hasAttributes = asArray(cartographyState.data[layerKey]).length > 0;

    if (featureCount === 0) {
      if (checkbox) checkbox.checked = false;
      const programDefinition = FDSU_SITES_PROGRAM_LAYERS[layerKey];
      const telecomDefinition = TELECOM_LAYERS[layerKey];
      const spatialDefinition = SPATIAL_ANALYSIS_LAYERS[layerKey];
      if (programDefinition?.pendingMessage) {
        showZonesMessage(programDefinition.pendingMessage);
        return false;
      }
      if (telecomDefinition?.pendingMessage) {
        showZonesMessage(telecomDefinition.pendingMessage);
        return false;
      }
      if (spatialDefinition?.pendingMessage) {
        showZonesMessage(spatialDefinition.pendingMessage);
        return false;
      }
      showZonesMessage(hasAttributes
        ? `${getCartographyLayerLabel(layerKey)} : données attributaires disponibles, géométrie absente.`
        : `Aucune donnée disponible pour ${getCartographyLayerLabel(layerKey)}.`);
      return false;
    }

    layer.addTo(cartographyState.map);
    if (checkbox) checkbox.checked = true;
    refreshCartographicLayerPresentation();
    renderSynchronizedLayerList(layerKey);
    fitLayerBounds(layer);
    updateLayerAvailabilityMessage();
    return true;
  });
}

function preloadCartographyLayers() {
  const managedKeys = Object.keys(WEB_SIG_LAYER_DEFINITIONS);
  return Promise.all(managedKeys.map((layerKey) => ensureCartographyLayerLoaded(layerKey).catch(() => [])))
    .then(() => {
      updateLayerAvailabilityMessage();
      renderAttributeExplorer();
      refreshGlobalSearchIndex();
    });
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
        document.querySelector(`input[data-layer="${layerKey}"]`).checked = Boolean(visibleByDefault);
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

      // Succès : effacer le message d'indisponibilité (emptyMessage ne doit s'afficher qu'en échec).
      updateLayerAvailabilityMessage('');
    })
    .catch(() => {
      cartographyState.layerStatus[layerKey] = false;
      updateLayerAvailabilityMessage(emptyMessage);
    });
}

function loadReferentialGeoLayer({ layerKey, reportPath, listKey, visibleByDefault, emptyMessage }) {
  if (!cartographyState.map || typeof L === 'undefined') return;

  const source = LOCAL_JSON_MODE
    ? fetchReportJson(reportPath).then((result) => result.data?.[listKey])
    : fetchJson(`/${layerKey}?limit=1000`);

  source
    .then((items) => {
      const featureCollection = buildFeatureCollection(asArray(items), layerKey);
      const geojsonLayer = cartographyState.layers[layerKey];

      if (!geojsonLayer || featureCollection.features.length === 0) {
        cartographyState.layerStatus[layerKey] = false;
        updateLayerAvailabilityMessage(emptyMessage);
        return;
      }

      geojsonLayer.clearLayers();
      geojsonLayer.addData(featureCollection);
      cartographyState[`${layerKey}Layer`] = geojsonLayer;
      cartographyState.layerStatus[layerKey] = true;

      const checkbox = document.querySelector(`input[data-layer="${layerKey}"]`);
      if (checkbox) checkbox.checked = Boolean(visibleByDefault);
      if (visibleByDefault) geojsonLayer.addTo(cartographyState.map);

      const bounds = geojsonLayer.getBounds();
      if (bounds.isValid()) {
        cartographyState.map.fitBounds(bounds, { padding: [20, 20] });
      }
      updateLayerAvailabilityMessage('');
    })
    .catch(() => {
      cartographyState.layerStatus[layerKey] = false;
      updateLayerAvailabilityMessage(emptyMessage);
    });
}

function loadLocalityPointLayer() {
  if (!cartographyState.map || typeof L === 'undefined') return;

  const source = LOCAL_JSON_MODE
    ? fetchReportJson('locality_official/locality_referential_official.json').then((result) => result.data?.locality_referential)
    : fetchJson('/localites?limit=1500');

  source
    .then((items) => {
      const featureCollection = buildFeatureCollection(asArray(items), 'villages');
      const localitiesLayer = cartographyState.layers.villages;

      if (!localitiesLayer || featureCollection.features.length === 0) {
        cartographyState.layerStatus.villages = false;
        updateLayerAvailabilityMessage('Points des localités non disponibles.');
        return;
      }

      localitiesLayer.clearLayers();
      localitiesLayer.addData(featureCollection);
      cartographyState.villagesLayer = localitiesLayer;
      cartographyState.layerStatus.villages = true;

      const checkbox = document.querySelector('input[data-layer="villages"]');
      if (checkbox) checkbox.checked = !cartographyState.layerStatus.provinces;
      if (!cartographyState.layerStatus.provinces) {
        localitiesLayer.addTo(cartographyState.map);
        const bounds = localitiesLayer.getBounds();
        if (bounds.isValid()) cartographyState.map.fitBounds(bounds, { padding: [20, 20] });
      }
      updateLayerAvailabilityMessage('');
    })
    .catch(() => {
      cartographyState.layerStatus.villages = false;
      updateLayerAvailabilityMessage('Points des localités non disponibles.');
    });
}

const WEB_SIG_LAYER_DEFINITIONS = {
  provinces: {
    label: 'Provinces',
    reportPath: 'province_official/province_referential_official.json',
    listKey: 'province_referential',
    endpoint: '/geo/provinces?limit=500',
    visibleByDefault: false,
  },
  territoires: {
    label: 'Territoires',
    reportPath: 'territory_hierarchy/territoires_hierarchie_kmz.report.json',
    listKey: 'territories',
    endpoint: '/territories?limit=500',
    visibleByDefault: false,
    filter: (item) => String(item?.attributs?.extended_data?.TYPE || item?.type || '').toLowerCase() === 'territoire',
  },
  collectivites: {
    label: 'Collectivités',
    reportPath: 'collectivity_official/collectivity_referential_official.json',
    listKey: 'collectivity_referential',
    endpoint: '/geo/collectivites?limit=1000',
    visibleByDefault: false,
  },
  groupements: {
    label: 'Groupements',
    reportPath: 'groupement_official/groupement_referential_official.json',
    listKey: 'groupement_referential',
    endpoint: '/geo/groupements?limit=2000',
    visibleByDefault: false,
  },
  villages: {
    label: 'Localités',
    reportPath: 'locality_official/locality_referential_official.json',
    listKey: 'locality_referential',
    endpoint: '/localites?limit=5000',
    visibleByDefault: false,
  },
  sites: {
    label: 'Sites FDSU',
    endpoint: '/geo/sites',
    visibleByDefault: false,
    fallbackItems: [],
  },
  missions: {
    label: 'Missions',
    endpoint: '/geo/missions?limit=500',
    visibleByDefault: false,
    fallbackItems: [],
  },
};

function loadWebSigLayers() {
  preloadCartographyLayers();
}

function loadWebSigLayer(layerKey, definition) {
  const source = fetchPlatformLayerData(layerKey);

  return source
    .then((items) => {
      const filteredItems = asArray(items).filter((item) => !definition.filter || definition.filter(item));
      const featureCollection = buildFeatureCollection(filteredItems, layerKey);
      const layer = cartographyState.layers[layerKey];

      cartographyState.data[layerKey] = filteredItems;
      cartographyState.features[layerKey] = featureCollection.features;
      cartographyState.featureLayers[layerKey] = {};

      if (!layer) return filteredItems;
      layer.clearLayers();
      if (featureCollection.features.length > 0) {
        layer.addData(featureCollection);
        cartographyState.layerStatus[layerKey] = true;
        if (cartographyState.map?.hasLayer(layer)) {
          refreshVisibleCartographyLayer(layerKey);
        }
      } else {
        cartographyState.layerStatus[layerKey] = filteredItems.length > 0 ? 'attributes-only' : false;
      }

      const checkbox = document.querySelector(`input[data-layer="${layerKey}"]`);
      if (checkbox) {
        checkbox.disabled = filteredItems.length === 0;
      }

      if (layerKey === 'provinces') {
        buildZoneLayerFromProvinces(filteredItems);
      }

      renderAttributeExplorer();
      refreshGlobalSearchIndex();
      updateLayerAvailabilityMessage();
      return filteredItems;
    })
    .catch((error) => {
      console.error(`Erreur chargement couche ${layerKey}`, error);
      cartographyState.data[layerKey] = [];
      cartographyState.features[layerKey] = [];
      cartographyState.layerStatus[layerKey] = false;
      updateLayerAvailabilityMessage();
      renderAttributeExplorer();
      return [];
    });
}

function buildZoneLayerFromProvinces(provinces) {
  if (!cartographyState.layers.zones || cartographyState.layers.zones.getLayers().length > 0) return;
  const zones = new Map();
  asArray(provinces)
    .filter((province) => province.geometry)
    .forEach((province) => {
      const officialProvince = enrichFdsuNomenclature(province);
      const zoneCode = officialProvince.zone_fdsu;
      if (!FDSU_ZONE_DEFINITIONS[zoneCode]) return;
      if (!zones.has(zoneCode)) zones.set(zoneCode, { code: zoneCode, polygons: [], provinceNames: [] });
      const zone = zones.get(zoneCode);
      appendGeometryPolygons(zone.polygons, province.geometry);
      if (province.nom || province.name) zone.provinceNames.push(province.nom || province.name);
    });

  const features = FDSU_ZONE_CODES
    .map((zoneCode) => zones.get(zoneCode))
    .filter((zone) => zone && zone.polygons.length > 0)
    .map((zone) => {
      const zoneCode = zone.code;
      const zoneName = getZoneName(zoneCode);
      const zoneStats = computeZoneStats(zoneCode);
      const provinceNames = zoneStats.provinces.length > 0 ? zoneStats.provinces : zone.provinceNames;
      return {
        type: 'Feature',
        geometry: {
          type: 'MultiPolygon',
          coordinates: zone.polygons,
        },
        properties: {
          layer: 'zones',
          code: zoneCode,
          zone_fdsu: zoneCode,
          nom: zoneName,
          type: 'Zone FDSU',
          fdsu_codification_format: FDSU_CODE_FORMAT,
          provinces_rattachees: provinceNames.join(', '),
          nb_provinces: provinceNames.length,
          territoires: zoneStats.territoires,
          collectivites: zoneStats.collectivites,
          groupements: zoneStats.groupements,
          localites: zoneStats.localites,
          sites: zoneStats.sites,
          source: 'Couche de synthese par zones FDSU, construite depuis les provinces',
          statut: 'fallback_cartographique_synthese',
          synthetic_zone_layer: true,
        },
      };
    });
  if (features.length === 0) return;
  const zonesLayer = cartographyState.layers.zones;
  zonesLayer.clearLayers();
  zonesLayer.addData({ type: 'FeatureCollection', features });
  cartographyState.features.zones = features;
  cartographyState.layerStatus.zones = true;
  cartographyState.zonesLayer = zonesLayer;
  const checkbox = document.querySelector('input[data-layer="zones"]');
  if (checkbox) {
    checkbox.disabled = false;
  }
  if (checkbox?.checked) {
    zonesLayer.addTo(cartographyState.map);
    fitLayerBounds(zonesLayer);
  }
  refreshCartographicLayerPresentation();
  updateLayerAvailabilityMessage('');
}

function appendGeometryPolygons(targetPolygons, geometry) {
  if (!geometry || !Array.isArray(targetPolygons)) return;
  if (geometry.type === 'Polygon' && Array.isArray(geometry.coordinates)) {
    targetPolygons.push(geometry.coordinates);
  } else if (geometry.type === 'MultiPolygon' && Array.isArray(geometry.coordinates)) {
    geometry.coordinates.forEach((polygon) => {
      if (Array.isArray(polygon)) targetPolygons.push(polygon);
    });
  }
}

function getZoneName(zoneCode) {
  const code = String(zoneCode || '').toUpperCase();
  return FDSU_ZONE_DEFINITIONS[code]?.nom || 'Zone FDSU';
}

function normalizeFdsuName(value) {
  return String(value || '')
    .trim()
    .toUpperCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^A-Z0-9]/g, '');
}

function getFdsuProvinceReference(value) {
  const target = normalizeFdsuName(value);
  if (!target) return null;
  return Object.entries(FDSU_PROVINCE_REFERENCE)
    .find(([name, reference]) => normalizeFdsuName(name) === target || normalizeFdsuName(reference.code) === target)?.[1] || null;
}

function getFdsuZoneCodeForItem(item = {}) {
  const provinceReference = getFdsuProvinceReference(item.province || item.nom || item.name || item.code_province_fdsu);
  if (provinceReference) return provinceReference.zone_fdsu;
  const zone = String(item.zone_fdsu || item.zone || item.metadata?.zone_fdsu || '').trim().toUpperCase();
  return FDSU_ZONE_DEFINITIONS[zone] ? zone : '';
}

function enrichFdsuNomenclature(item = {}) {
  const provinceReference = getFdsuProvinceReference(item.province || item.nom || item.name || item.code_province_fdsu);
  const zoneCode = getFdsuZoneCodeForItem(item);
  return {
    ...item,
    zone_fdsu: zoneCode || item.zone_fdsu || item.zone || '',
    zone_nom: zoneCode ? getZoneName(zoneCode) : item.zone_nom || '',
    code_province_fdsu: provinceReference?.code || item.code_province_fdsu || '',
    fdsu_codification_format: FDSU_CODE_FORMAT,
  };
}

function computeZoneStats(zoneCode) {
  const code = String(zoneCode || '').toUpperCase();
  const matchesZone = (item) => getFdsuZoneCodeForItem(item) === code;
  const provinces = asArray(cartographyState.data.provinces)
    .filter(matchesZone)
    .map((item) => item.nom || item.name)
    .filter(Boolean);
  return {
    provinces,
    territoires: asArray(cartographyState.data.territoires).filter(matchesZone).length,
    collectivites: asArray(cartographyState.data.collectivites).filter(matchesZone).length,
    groupements: asArray(cartographyState.data.groupements).filter(matchesZone).length,
    localites: asArray(cartographyState.data.villages).filter(matchesZone).length,
    sites: asArray(cartographyState.data.sites).filter(matchesZone).length,
  };
}

function computeZoneProfileProperties(properties) {
  const zoneCode = properties.zone_fdsu || properties.code;
  const stats = computeZoneStats(zoneCode);
  return {
    nom: properties.nom || getZoneName(zoneCode),
    type: 'Zone FDSU',
    code: zoneCode,
    zone_fdsu: zoneCode,
    zone_nom: getZoneName(zoneCode),
    fdsu_codification_format: FDSU_CODE_FORMAT,
    provinces_rattachees: stats.provinces.join(', '),
    nb_provinces: stats.provinces.length,
    territoires: stats.territoires,
    collectivites: stats.collectivites,
    groupements: stats.groupements,
    localites: stats.localites,
    sites: stats.sites,
  };
}

function canUseApiLayerData() {
  if (DATA_MODE === 'json') return false;
  if (DATA_MODE === 'api') return true;
  return API_HEALTH?.status === 'ok';
}

function fetchPlatformLayerData(layerKey) {
  if (platformState.dataPromises[layerKey]) return platformState.dataPromises[layerKey];
  const definition = WEB_SIG_LAYER_DEFINITIONS[layerKey];
  if (!definition) return Promise.resolve([]);
  platformState.dataPromises[layerKey] = (canUseApiLayerData()
    ? fetchApiJson(`/map/layers/${getApiLayerName(layerKey)}?limit=5000`).then((payload) => geoJsonToItems(payload) || definition.fallbackItems || []).catch(() => definition.fallbackItems || [])
    : loadLayerItemsFromReports(definition)
  ).then((items) => {
    const filteredItems = asArray(items)
      .map((item) => enrichFdsuNomenclature(item))
      .filter((item) => !definition.filter || definition.filter(item));
    cartographyState.data[layerKey] = filteredItems;
    return filteredItems;
  });
  return platformState.dataPromises[layerKey];
}

function preloadPlatformData() {
  return Promise.all(Object.keys(WEB_SIG_LAYER_DEFINITIONS).map((layerKey) => fetchPlatformLayerData(layerKey))).then(() => {
    refreshGlobalSearchIndex();
    return platformState.searchIndex;
  });
}

function getApiLayerName(layerKey) {
  return layerKey === 'villages' ? 'localites' : layerKey;
}

function geoJsonToItems(payload) {
  if (Array.isArray(payload)) return payload;
  if (!payload || !Array.isArray(payload.features)) return [];
  return payload.features.map((feature) => ({
    ...(feature.properties || {}),
    geometry: feature.geometry,
  }));
}

function loadLayerItemsFromReports(definition) {
  if (!definition.reportPath) return Promise.resolve(definition.fallbackItems || []);
  return fetchReportJson(definition.reportPath).then((result) => result.data?.[definition.listKey] || []);
}

function initializePlatformInteractions() {
  const globalSearchInput = document.querySelector('#global-search-input');
  const globalSearchResults = document.querySelector('#global-search-results');
  if (globalSearchInput && globalSearchInput.dataset.bound !== 'true') {
    globalSearchInput.dataset.bound = 'true';
    globalSearchInput.addEventListener('input', () => renderGlobalSearchResults(globalSearchInput.value));
    globalSearchInput.addEventListener('focus', () => {
      preloadPlatformData();
      renderGlobalSearchResults(globalSearchInput.value);
    });
  }
  if (!platformState.interactionsBound) {
    platformState.interactionsBound = true;
    document.addEventListener('click', (event) => {
      if (!event.target.closest('.global-search-field')) {
        document.querySelector('#global-search-results')?.classList.add('hidden');
      }
    });
  }

  document.querySelectorAll('.clickable-summary').forEach((card) => {
    if (card.dataset.bound === 'true') return;
    card.dataset.bound = 'true';
    const openLayer = () => {
      if (card.dataset.detailPage) {
        openDashboardDetailPage(card.dataset.detailPage);
      } else if (card.dataset.layer) {
        openDashboardLayerList(card.dataset.layer);
      } else if (card.dataset.route) {
        navigateTo(card.dataset.route);
      }
    };
    card.addEventListener('click', openLayer);
    card.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') openLayer();
    });
  });

  const closeButton = document.querySelector('#entity-profile-close');
  if (closeButton && closeButton.dataset.bound !== 'true') {
    closeButton.dataset.bound = 'true';
    closeButton.addEventListener('click', closeEntityProfile);
  }
  setupDashboardWorkbench();
  setupDashboardZoneShortcuts();
}

function setupDashboardZoneShortcuts() {
  document.querySelectorAll('.zone-item[data-zone], .legend-list [data-zone]').forEach((item) => {
    if (item.dataset.bound === 'true') return;
    item.dataset.bound = 'true';
    const openZone = () => openDashboardDetailPage('zones', { zoneCode: item.dataset.zone });
    item.addEventListener('click', openZone);
    item.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') openZone();
    });
  });
}

function refreshGlobalSearchIndex() {
  const index = [];
  Object.keys(WEB_SIG_LAYER_DEFINITIONS).forEach((layerKey) => {
    const rows = asArray(cartographyState.data[layerKey]);
    rows.forEach((item) => {
      const row = normalizeAttributeRow(item, layerKey);
      index.push({
        layerKey,
        featureId: row.featureId,
        label: row.nom,
        type: row.type,
        province: row.province,
        territoire: row.territoire,
        properties: row.properties,
        searchable: buildSearchText(row.properties),
      });
    });
  });
  platformState.searchIndex = index;
  platformState.searchReady = true;
  return index;
}

function buildSearchText(properties) {
  const profile = getFutureProfile(properties);
  return [
    properties.code,
    properties.canonical_id,
    properties.nom,
    properties.type,
    properties.province,
    properties.territoire,
    properties.collectivite,
    properties.groupement,
    properties.localite,
    properties.source,
    properties.observations,
    properties.anomalies,
    ...asArray(profile.activites_economiques),
    ...asArray(profile.particularites),
    ...asArray(profile.defis).map((defi) => typeof defi === 'string' ? defi : `${defi.nom || ''} ${defi.niveau || ''}`),
    ...Object.keys(profile.potentiels || {}),
    ...asArray(profile.operateurs),
    ...asArray(profile.infrastructures),
  ].join(' ').toLowerCase();
}

function renderGlobalSearchResults(query) {
  const resultsElement = document.querySelector('#global-search-results');
  if (!resultsElement) return;
  const searchTerm = String(query || '').trim().toLowerCase();
  if (!platformState.searchReady) {
    preloadPlatformData().then(() => renderGlobalSearchResults(query));
  }
  if (searchTerm.length < 2) {
    resultsElement.classList.add('hidden');
    resultsElement.innerHTML = '';
    return;
  }
  const results = platformState.searchIndex
    .filter((entry) => entry.searchable.includes(searchTerm))
    .slice(0, 12);
  resultsElement.classList.remove('hidden');
  resultsElement.innerHTML = results.length
    ? results.map((entry) => `
      <button type="button" class="global-search-result" data-layer="${escapeHtml(entry.layerKey)}" data-feature-id="${escapeHtml(entry.featureId)}">
        <strong>${escapeHtml(entry.label)}</strong>
        <span>${escapeHtml(entry.type)}${entry.province ? ` • ${escapeHtml(entry.province)}` : ''}${entry.territoire ? ` • ${escapeHtml(entry.territoire)}` : ''}</span>
      </button>
    `).join('')
    : '<p class="global-search-empty">Aucun résultat.</p>';
  resultsElement.querySelectorAll('[data-feature-id]').forEach((button) => {
    button.addEventListener('click', () => {
      resultsElement.classList.add('hidden');
      openDashboardSearchList(searchTerm, button.dataset.layer, button.dataset.featureId);
    });
  });
}

function openDashboardSearchList(searchTerm, preferredLayer = '', preferredFeatureId = '') {
  const matchingRows = platformState.searchIndex
    .filter((entry) => entry.searchable.includes(searchTerm))
    .map((entry) => ({
      ...normalizeAttributeRow(entry.properties, entry.layerKey),
      layerKey: entry.layerKey,
    }));
  const selectedRow = matchingRows.find((row) => row.layerKey === preferredLayer && row.featureId === preferredFeatureId);
  if (selectedRow) {
    platformState.workbenchSelectedFeatureId = selectedRow.featureId;
  }
  openDashboardLayerList('mixed', matchingRows, `Recherche: ${searchTerm}`);
}

function openLayerWorkbench(layerKey, featureId = null) {
  navigateTo('map');
  window.setTimeout(() => {
    const layerSelect = document.querySelector('#attribute-layer-select');
    if (layerSelect) {
      layerSelect.value = layerKey;
      cartographyState.activeAttributeLayer = layerKey;
    }
    fetchPlatformLayerData(layerKey).then((items) => {
      if (!cartographyState.data[layerKey]?.length) {
        cartographyState.data[layerKey] = items;
      }
      renderAttributeExplorer();
      if (featureId) focusAttributeFeature(layerKey, featureId);
    });
  }, 80);
}

function openRelationCounterList(relationKey, properties) {
  const targetLayer = getRelationLayerForCounter(properties, relationKey);
  if (!targetLayer) return;
  fetchPlatformLayerData(targetLayer).then((items) => {
    const parentFilter = getRelationParentFilter(properties);
    const rows = asArray(items)
      .map((item) => normalizeAttributeRow(item, targetLayer))
      .filter((row) => !parentFilter.field || normalizeDashboardText(row.properties[parentFilter.field]) === parentFilter.value)
      .map((row) => ({ ...row, layerKey: targetLayer }));
    openDashboardLayerList(targetLayer, rows, `${getLayerDisplayLabel(targetLayer)} - ${properties.nom || properties.name || ''}`);
  });
}

function getRelationLayerForCounter(properties, relationKey) {
  const links = asArray(properties.relation_links);
  const match = links.find((item) => item.key === relationKey);
  if (match?.layer) return match.layer === 'localites' ? 'villages' : match.layer;
  return {
    territoires: 'territoires',
    collectivites: 'collectivites',
    groupements: 'groupements',
    localites: 'villages',
  }[relationKey] || '';
}

function getRelationParentFilter(properties) {
  const layer = getApiLayerName(properties.layer || '');
  const parentName = normalizeDashboardText(properties.nom || properties.name);
  if (layer === 'provinces') return { field: 'province', value: parentName };
  if (layer === 'territoires') return { field: 'territoire', value: parentName };
  if (layer === 'collectivites') return { field: 'collectivite', value: parentName };
  if (layer === 'groupements') return { field: 'groupement', value: parentName };
  return { field: '', value: '' };
}

function openZoneProvinceList(zoneCode) {
  openDashboardDetailPage('zones', { zoneCode: String(zoneCode || '').toUpperCase() });
}

function setupDashboardDetailPages() {
  document.querySelector('#dashboard-detail-back')?.addEventListener('click', backToDashboard);
  ['#dashboard-detail-search', '#dashboard-detail-province-filter', '#dashboard-detail-territory-filter'].forEach((selector) => {
    const element = document.querySelector(selector);
    if (!element || element.dataset.bound === 'true') return;
    element.dataset.bound = 'true';
    element.addEventListener('input', () => {
      dashboardViewState.filters.search = document.querySelector('#dashboard-detail-search')?.value || '';
      dashboardViewState.filters.province = document.querySelector('#dashboard-detail-province-filter')?.value || '';
      dashboardViewState.filters.territory = document.querySelector('#dashboard-detail-territory-filter')?.value || '';
      dashboardViewState.selectedEntityId = null;
      renderDashboardDetailPage();
    });
    element.addEventListener('change', () => {
      dashboardViewState.filters.search = document.querySelector('#dashboard-detail-search')?.value || '';
      dashboardViewState.filters.province = document.querySelector('#dashboard-detail-province-filter')?.value || '';
      dashboardViewState.filters.territory = document.querySelector('#dashboard-detail-territory-filter')?.value || '';
      dashboardViewState.selectedEntityId = null;
      renderDashboardDetailPage();
    });
  });
}

function backToDashboard() {
  dashboardViewState.page = 'main';
  dashboardViewState.detailType = '';
  dashboardViewState.selectedEntityId = null;
  dashboardViewState.selectedZoneCode = null;
  dashboardViewState.filters = { search: '', province: '', territory: '' };
  renderDashboardMain();
  document.querySelector('#dashboard-panel')?.scrollIntoView({ block: 'start', behavior: 'smooth' });
}

function renderDashboardMain() {
  document.querySelector('#dashboard-main-view')?.classList.remove('hidden');
  document.querySelector('#dashboard-detail-view')?.classList.add('hidden');
  document.querySelector('#dashboard-detail-view')?.setAttribute('aria-hidden', 'true');
  document.querySelector('#dashboard-workbench')?.classList.add('hidden');
  closeEntityProfile();
  if (nationalMapState.map) {
    window.setTimeout(() => nationalMapState.map.invalidateSize(), 0);
  }
}

function openDashboardDetailPage(detailType, options = {}) {
  if (!DASHBOARD_DETAIL_PAGE_CONFIG[detailType]) return;
  navigateTo('dashboard');
  dashboardViewState.page = 'detail';
  dashboardViewState.detailType = detailType;
  dashboardViewState.selectedEntityId = options.featureId || null;
  dashboardViewState.selectedZoneCode = options.zoneCode || null;
  dashboardViewState.filters = {
    search: '',
    province: options.provinceFilter || '',
    territory: options.territoryFilter || '',
  };
  document.querySelector('#dashboard-main-view')?.classList.add('hidden');
  document.querySelector('#dashboard-detail-view')?.classList.remove('hidden');
  document.querySelector('#dashboard-detail-view')?.setAttribute('aria-hidden', 'false');
  document.querySelector('#dashboard-workbench')?.classList.add('hidden');
  closeEntityProfile();
  const searchInput = document.querySelector('#dashboard-detail-search');
  const provinceFilter = document.querySelector('#dashboard-detail-province-filter');
  const territoryFilter = document.querySelector('#dashboard-detail-territory-filter');
  if (searchInput) searchInput.value = dashboardViewState.filters.search;
  if (provinceFilter) provinceFilter.value = dashboardViewState.filters.province;
  if (territoryFilter) territoryFilter.value = dashboardViewState.filters.territory;
  loadDashboardDetailData(detailType, options).then(() => renderDashboardDetailPage());
}

function loadDashboardDetailData(detailType, options = {}) {
  const config = DASHBOARD_DETAIL_PAGE_CONFIG[detailType];
  if (config.mode === 'zones') {
    return Promise.all([
      fetchPlatformLayerData('provinces'),
      fetchPlatformLayerData('territoires'),
      fetchPlatformLayerData('collectivites'),
      fetchPlatformLayerData('groupements'),
      fetchPlatformLayerData('villages'),
      fetchPlatformLayerData('sites'),
    ]).then(() => {
      dashboardViewState.rows = FDSU_ZONE_CODES.map((zoneCode) => {
        const stats = computeZoneStats(zoneCode);
        return {
          featureId: zoneCode,
          layerKey: 'zones',
          nom: getZoneName(zoneCode),
          type: 'Zone FDSU',
          zone_fdsu: zoneCode,
          nb_provinces: stats.provinces.length,
          territoires: stats.territoires,
          collectivites: stats.collectivites,
          groupements: stats.groupements,
          localites: stats.localites,
          sites: stats.sites,
          properties: computeZoneProfileProperties({ code: zoneCode, zone_fdsu: zoneCode, nom: getZoneName(zoneCode) }),
        };
      });
      dashboardViewState.features = buildDashboardZoneFeatures();
      if (options.presetRows) dashboardViewState.rows = options.presetRows;
    });
  }
  const layerKey = config.layerKey;
  const dataPromise = options.presetRows
    ? Promise.resolve(options.presetRows.map((row) => row.properties || row))
    : fetchPlatformLayerData(layerKey);
  return dataPromise.then((items) => {
    const rows = (options.presetRows || asArray(items)).map((item) => (
      item?.featureId ? item : normalizeAttributeRow(item, layerKey)
    ));
    dashboardViewState.rows = rows;
    dashboardViewState.features = buildFeatureCollection(rows.map((row) => row.properties), layerKey).features;
  });
}

function buildDashboardZoneFeatures() {
  const provinces = asArray(cartographyState.data.provinces).length
    ? cartographyState.data.provinces
    : asArray(dashboardViewState.rows);
  const zones = new Map();
  asArray(cartographyState.data.provinces)
    .filter((province) => province.geometry)
    .forEach((province) => {
      const officialProvince = enrichFdsuNomenclature(province);
      const zoneCode = officialProvince.zone_fdsu;
      if (!FDSU_ZONE_DEFINITIONS[zoneCode]) return;
      if (!zones.has(zoneCode)) zones.set(zoneCode, { code: zoneCode, polygons: [] });
      appendGeometryPolygons(zones.get(zoneCode).polygons, province.geometry);
    });
  return FDSU_ZONE_CODES
    .map((zoneCode) => zones.get(zoneCode))
    .filter((zone) => zone && zone.polygons.length > 0)
    .map((zone) => ({
      type: 'Feature',
      geometry: { type: 'MultiPolygon', coordinates: zone.polygons },
      properties: {
        layer: 'zones',
        code: zone.code,
        zone_fdsu: zone.code,
        nom: getZoneName(zone.code),
        type: 'Zone FDSU',
        ...computeZoneProfileProperties({ code: zone.code, zone_fdsu: zone.code, nom: getZoneName(zone.code) }),
      },
    }));
}

function renderDashboardDetailPage() {
  const config = DASHBOARD_DETAIL_PAGE_CONFIG[dashboardViewState.detailType];
  if (!config) return;
  document.querySelector('#dashboard-detail-title').textContent = config.title;
  document.querySelector('#dashboard-detail-label').textContent = 'Page analytique';
  const provinceFilter = document.querySelector('#dashboard-detail-province-filter');
  const territoryFilter = document.querySelector('#dashboard-detail-territory-filter');
  if (provinceFilter) {
    provinceFilter.classList.toggle('hidden', !config.showProvinceFilter);
    updateSelectOptions(provinceFilter, dashboardViewState.rows.map((row) => row.province).filter(Boolean), 'Toutes les provinces');
    provinceFilter.value = dashboardViewState.filters.province;
  }
  if (territoryFilter) {
    territoryFilter.classList.toggle('hidden', !config.showTerritoryFilter);
    updateSelectOptions(territoryFilter, dashboardViewState.rows.map((row) => row.territoire).filter(Boolean), 'Tous les territoires');
    territoryFilter.value = dashboardViewState.filters.territory;
  }
  const filteredRows = getFilteredDashboardDetailRows();
  document.querySelector('#dashboard-detail-count').textContent = `${filteredRows.length.toLocaleString('fr-FR')} élément(s)`;
  renderDashboardDetailMap(filteredRows, config);
  renderDashboardDetailList(filteredRows, config);
  renderDashboardDetailStats(filteredRows, config);
  window.setTimeout(() => dashboardViewState.map?.invalidateSize(), 0);
}

function getFilteredDashboardDetailRows() {
  const search = String(dashboardViewState.filters.search || '').trim().toLowerCase();
  const province = dashboardViewState.filters.province || '';
  const territory = dashboardViewState.filters.territory || '';
  let rows = asArray(dashboardViewState.rows);
  if (dashboardViewState.detailType === 'zones' && dashboardViewState.selectedZoneCode) {
    rows = rows.filter((row) => String(row.zone_fdsu || row.featureId || '').toUpperCase() === dashboardViewState.selectedZoneCode);
  }
  return rows.filter((row) => {
    const haystack = [row.nom, row.type, row.province, row.territoire, row.collectivite, row.groupement, row.zone_fdsu]
      .join(' ').toLowerCase();
    return (!search || haystack.includes(search))
      && (!province || row.province === province)
      && (!territory || row.territoire === territory);
  });
}

function ensureDashboardDetailMap() {
  if (typeof L === 'undefined') return null;
  const mapElement = document.querySelector('#dashboard-detail-map');
  if (!mapElement) return null;
  if (!dashboardViewState.map) {
    dashboardViewState.map = L.map(mapElement, { zoomControl: true, minZoom: 4, maxZoom: 14 }).setView([-2.8, 23.5], 5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(dashboardViewState.map);
    dashboardViewState.layer = L.geoJSON(null);
    dashboardViewState.mapInitialized = true;
  }
  return dashboardViewState.map;
}

function renderDashboardDetailMap(filteredRows, config) {
  const map = ensureDashboardDetailMap();
  if (!map || !dashboardViewState.layer) return;
  if (dashboardViewState.layer && map.hasLayer(dashboardViewState.layer)) {
    map.removeLayer(dashboardViewState.layer);
  }
  dashboardViewState.featureLayers = {};
  let features = [];
  if (config.mode === 'zones') {
    features = dashboardViewState.selectedZoneCode
      ? buildFeatureCollection(
        asArray(cartographyState.data.provinces).filter((item) => getFdsuZoneCodeForItem(item) === dashboardViewState.selectedZoneCode),
        'provinces',
      ).features
      : asArray(dashboardViewState.features);
    dashboardViewState.layer = L.geoJSON(null, {
      style: (feature) => styleZoneFeature(feature),
      onEachFeature: (feature, layer) => bindDashboardDetailFeature(feature, layer, 'zones'),
    });
  } else {
    const layerKey = config.layerKey;
    features = filteredRows
      .map((row) => buildFeature(row.properties, layerKey))
      .filter(Boolean);
    const isPointLayer = ['groupements', 'villages', 'sites', 'missions'].includes(layerKey);
    dashboardViewState.layer = L.geoJSON(null, {
      style: isPointLayer ? undefined : (feature) => getDashboardDetailStyle(feature, layerKey),
      pointToLayer: isPointLayer ? (_feature, latlng) => makePointMarker(latlng, '#38bdf8', '#7dd3fc') : undefined,
      onEachFeature: (feature, layer) => bindDashboardDetailFeature(feature, layer, layerKey),
    });
  }
  dashboardViewState.layer.addData({ type: 'FeatureCollection', features });
  dashboardViewState.layer.addTo(map);
  const bounds = dashboardViewState.layer.getBounds();
  if (bounds.isValid()) map.fitBounds(bounds, { padding: [20, 20] });
  else if (typeof L !== 'undefined') map.fitBounds(L.latLngBounds(RDC_MAP_BOUNDS), { padding: [20, 20] });
  if (dashboardViewState.selectedEntityId) {
    highlightDashboardDetailSelection(dashboardViewState.selectedEntityId);
  }
}

function getDashboardDetailStyle(feature, layerKey) {
  if (layerKey === 'provinces') return styleProvinceFeature(feature);
  if (layerKey === 'territoires') return styleTerritoryFeature(feature);
  if (layerKey === 'collectivites') return styleCollectivitesFeature(feature);
  return { color: '#38bdf8', weight: 2, opacity: 1, fillColor: '#38bdf8', fillOpacity: 0.28 };
}

function bindDashboardDetailFeature(feature, layer, layerKey) {
  const properties = feature?.properties || {};
  const featureId = getFeatureId(properties, layerKey);
  if (!dashboardViewState.featureLayers[layerKey]) dashboardViewState.featureLayers[layerKey] = {};
  dashboardViewState.featureLayers[layerKey][featureId] = layer;
  if (layer.bindPopup) {
    layer.bindPopup(`<strong>${escapeHtml(getFeatureProperty(properties, ['nom', 'name']))}</strong>`);
  }
  if (typeof window !== 'undefined' && window.SigMapTooltips?.bind) {
    window.SigMapTooltips.bind(layer, feature || properties, layerKey, { interactive: false });
  }
  layer.on('click', () => selectDashboardDetailEntity(featureId, layerKey, properties));
}

function selectDashboardDetailEntity(featureId, layerKey, properties = {}) {
  dashboardViewState.selectedEntityId = featureId;
  if (dashboardViewState.detailType === 'zones' && layerKey === 'zones') {
    dashboardViewState.selectedZoneCode = String(properties.zone_fdsu || properties.code || featureId).toUpperCase();
    const provinceRows = asArray(cartographyState.data.provinces)
      .filter((item) => getFdsuZoneCodeForItem(item) === dashboardViewState.selectedZoneCode)
      .map((item) => normalizeAttributeRow(item, 'provinces'));
    dashboardViewState.rows = provinceRows.length ? provinceRows : dashboardViewState.rows;
  }
  highlightDashboardDetailSelection(featureId, layerKey);
  renderDashboardDetailList(getFilteredDashboardDetailRows(), DASHBOARD_DETAIL_PAGE_CONFIG[dashboardViewState.detailType]);
  renderDashboardDetailStats(getFilteredDashboardDetailRows(), DASHBOARD_DETAIL_PAGE_CONFIG[dashboardViewState.detailType], properties);
}

function highlightDashboardDetailSelection(featureId, layerKey = dashboardViewState.detailType === 'zones' ? 'zones' : DASHBOARD_DETAIL_PAGE_CONFIG[dashboardViewState.detailType]?.layerKey) {
  Object.values(dashboardViewState.featureLayers).forEach((group) => {
    Object.entries(group).forEach(([id, layer]) => {
      if (layer?.setStyle) layer.setStyle(getDashboardDetailStyle(layer.feature, layerKey));
    });
  });
  const selectedLayer = dashboardViewState.featureLayers[layerKey]?.[featureId];
  if (selectedLayer?.setStyle) {
    selectedLayer.setStyle({ color: '#fbbf24', weight: 3, fillColor: '#fde68a', fillOpacity: 0.45 });
    if (selectedLayer.getBounds) {
      dashboardViewState.map?.fitBounds(selectedLayer.getBounds(), { padding: [28, 28], maxZoom: 10 });
    } else if (selectedLayer.getLatLng) {
      dashboardViewState.map?.setView(selectedLayer.getLatLng(), Math.max(dashboardViewState.map.getZoom(), 9));
    }
  }
}

function renderDashboardDetailList(filteredRows, config) {
  const listElement = document.querySelector('#dashboard-detail-list');
  if (!listElement) return;
  if (config.mode === 'zones' && !dashboardViewState.selectedZoneCode) {
    listElement.innerHTML = dashboardViewState.rows.map((row) => `
      <button type="button" class="dashboard-detail-list-item zone-item zone-${String(row.zone_fdsu || row.featureId).toLowerCase()}" data-feature-id="${escapeHtml(row.featureId)}">
        <span>${escapeHtml(row.nom)}</span>
        <small>${row.nb_provinces ?? 0} provinces · ${row.territoires ?? 0} territoires · ${row.localites ?? 0} localités</small>
      </button>
    `).join('');
  } else if (filteredRows.length === 0) {
    listElement.innerHTML = '<p class="zone-detail-empty">Aucun élément ne correspond aux filtres.</p>';
  } else {
    listElement.innerHTML = filteredRows.slice(0, 300).map((row) => `
      <button type="button" class="dashboard-detail-list-item ${row.featureId === dashboardViewState.selectedEntityId ? 'is-selected' : ''}" data-feature-id="${escapeHtml(row.featureId)}" data-layer="${escapeHtml(row.layerKey || config.layerKey || 'zones')}">
        <span>${escapeHtml(row.nom)}</span>
        <small>${escapeHtml([row.type, row.province, row.territoire].filter(Boolean).join(' · '))}</small>
      </button>
    `).join('');
  }
  listElement.querySelectorAll('.dashboard-detail-list-item').forEach((button) => {
    button.addEventListener('click', () => {
      const row = filteredRows.find((candidate) => candidate.featureId === button.dataset.featureId)
        || dashboardViewState.rows.find((candidate) => candidate.featureId === button.dataset.featureId);
      selectDashboardDetailEntity(button.dataset.featureId, button.dataset.layer || config.layerKey || 'zones', row?.properties || row || {});
    });
  });
}

function renderDashboardDetailStats(filteredRows, config, selectedProperties = null) {
  const statsElement = document.querySelector('#dashboard-detail-stats');
  if (!statsElement) return;
  const selectedRow = filteredRows.find((row) => row.featureId === dashboardViewState.selectedEntityId)
    || dashboardViewState.rows.find((row) => row.featureId === dashboardViewState.selectedEntityId);
  const properties = selectedProperties || selectedRow?.properties || {};
  if (config.mode === 'zones' && dashboardViewState.selectedZoneCode && !selectedRow) {
    const zoneStats = computeZoneStats(dashboardViewState.selectedZoneCode);
    statsElement.innerHTML = `
      <h3>Zone ${escapeHtml(dashboardViewState.selectedZoneCode)}</h3>
      <ul class="dashboard-detail-stats-list">
        <li><span>Provinces</span><strong>${zoneStats.provinces.length}</strong></li>
        <li><span>Territoires</span><strong>${zoneStats.territoires}</strong></li>
        <li><span>Collectivités</span><strong>${zoneStats.collectivites}</strong></li>
        <li><span>Groupements</span><strong>${zoneStats.groupements}</strong></li>
        <li><span>Localités</span><strong>${zoneStats.localites}</strong></li>
        <li><span>Sites</span><strong>${zoneStats.sites}</strong></li>
      </ul>
      <p class="cartography-note">Cliquez une province pour la localiser sur la carte.</p>
    `;
    return;
  }
  if (!selectedRow) {
    statsElement.innerHTML = `
      <h3>${escapeHtml(config.title)}</h3>
      <p class="cartography-note">${filteredRows.length.toLocaleString('fr-FR')} élément(s) affichés. Sélectionnez une entité dans la liste ou sur la carte.</p>
    `;
    return;
  }
  const contextStats = computeSpatialContextStats(selectedRow.layerKey || config.layerKey, properties);
  statsElement.innerHTML = `
    <h3>${escapeHtml(selectedRow.nom)}</h3>
    <p class="cartography-note">${escapeHtml(selectedRow.type || config.title)}</p>
    ${renderContextStatsHtml(contextStats)}
    <div class="detail-attributes">
      ${[
        ['Province', selectedRow.province],
        ['Territoire', selectedRow.territoire],
        ['Collectivité', selectedRow.collectivite],
        ['Zone FDSU', selectedRow.zone_fdsu],
        ['Qualité', selectedRow.qualite],
      ].filter(([, value]) => value).map(([label, value]) => `<div class="detail-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(formatAttributeValue(value))}</strong></div>`).join('')}
    </div>
  `;
}

function openDashboardLayerList(layerKey, presetRows = null, title = '') {
  const pageMap = {
    provinces: 'provinces',
    territoires: 'territories',
    collectivites: 'collectivities',
    groupements: 'groupements',
    villages: 'localities',
    sites: 'sites',
    missions: 'missions',
    zones: 'zones',
  };
  const detailType = pageMap[layerKey];
  if (detailType) {
    openDashboardDetailPage(detailType, { presetRows, title });
    return;
  }
  if (presetRows?.length) {
    const firstLayer = presetRows.find((row) => row.layerKey)?.layerKey || 'provinces';
    openDashboardDetailPage(pageMap[firstLayer] || 'provinces', { presetRows, title });
    return;
  }
  navigateTo('dashboard');
  platformState.workbenchLayer = layerKey;
  platformState.workbenchPage = 1;
  document.querySelector('#dashboard-workbench')?.classList.add('hidden');
}

function setupDashboardWorkbench() {
  const search = document.querySelector('#dashboard-workbench-search');
  const province = document.querySelector('#dashboard-workbench-province');
  const territory = document.querySelector('#dashboard-workbench-territory');
  const sort = document.querySelector('#dashboard-workbench-sort');
  const pageSize = document.querySelector('#dashboard-workbench-page-size');
  const prev = document.querySelector('#dashboard-workbench-prev');
  const next = document.querySelector('#dashboard-workbench-next');
  const backButton = document.querySelector('#dashboard-workbench-back');
  const mapButton = document.querySelector('#dashboard-workbench-map');
  const exportButton = document.querySelector('#dashboard-workbench-export');
  const printButton = document.querySelector('#dashboard-workbench-print');
  const referentielButton = document.querySelector('#dashboard-workbench-referentiel');
  [search, province, territory, sort, pageSize].forEach((element) => {
    if (!element || element.dataset.bound === 'true') return;
    element.dataset.bound = 'true';
    element.addEventListener('input', () => {
      platformState.workbenchPage = 1;
      renderDashboardWorkbench();
    });
    element.addEventListener('change', () => {
      if (element === sort) {
        const [key, order] = String(sort.value || 'nom:asc').split(':');
        platformState.workbenchSortKey = key || 'nom';
        platformState.workbenchSortOrder = order === 'desc' ? 'desc' : 'asc';
      }
      if (element === pageSize) {
        platformState.workbenchPageSize = Number(pageSize.value) || 25;
      }
      platformState.workbenchPage = 1;
      renderDashboardWorkbench();
    });
  });
  if (prev && prev.dataset.bound !== 'true') {
    prev.dataset.bound = 'true';
    prev.addEventListener('click', () => {
      platformState.workbenchPage = Math.max(1, platformState.workbenchPage - 1);
      renderDashboardWorkbench();
    });
  }
  if (next && next.dataset.bound !== 'true') {
    next.dataset.bound = 'true';
    next.addEventListener('click', () => {
      platformState.workbenchPage += 1;
      renderDashboardWorkbench();
    });
  }
  if (backButton && backButton.dataset.bound !== 'true') {
    backButton.dataset.bound = 'true';
    backButton.addEventListener('click', backToDashboard);
  }
  if (mapButton && mapButton.dataset.bound !== 'true') {
    mapButton.dataset.bound = 'true';
    mapButton.addEventListener('click', () => {
      const selectedRow = getWorkbenchSelectedRow();
      const firstLayer = selectedRow?.layerKey || asArray(platformState.workbenchRows).find((row) => row.layerKey)?.layerKey;
      const targetLayer = platformState.workbenchLayer === 'mixed' ? firstLayer : platformState.workbenchLayer;
      if (targetLayer) openLayerWorkbench(targetLayer, selectedRow?.featureId || null);
    });
  }
  if (exportButton && exportButton.dataset.bound !== 'true') {
    exportButton.dataset.bound = 'true';
    exportButton.addEventListener('click', () => exportDashboardWorkbench());
  }
  if (printButton && printButton.dataset.bound !== 'true') {
    printButton.dataset.bound = 'true';
    printButton.addEventListener('click', () => window.print());
  }
  if (referentielButton && referentielButton.dataset.bound !== 'true') {
    referentielButton.dataset.bound = 'true';
    referentielButton.addEventListener('click', () => navigateTo('referentiel'));
  }
}

function refreshWorkbenchFilters(rows) {
  updateSelectOptions(document.querySelector('#dashboard-workbench-province'), rows.map((row) => row.province).filter(Boolean), 'Toutes les provinces');
  updateSelectOptions(document.querySelector('#dashboard-workbench-territory'), rows.map((row) => row.territoire).filter(Boolean), 'Tous les territoires');
}

function renderDashboardWorkbench() {
  const body = document.querySelector('#dashboard-workbench-body');
  if (!body) return;
  const search = String(document.querySelector('#dashboard-workbench-search')?.value || '').trim().toLowerCase();
  const province = document.querySelector('#dashboard-workbench-province')?.value || '';
  const territory = document.querySelector('#dashboard-workbench-territory')?.value || '';
  const rows = asArray(platformState.workbenchRows).filter((row) => {
    const haystack = [row.nom, row.type, row.province, row.territoire, row.collectivite, row.groupement].join(' ').toLowerCase();
    return (!search || haystack.includes(search))
      && (!province || row.province === province)
      && (!territory || row.territoire === territory);
  }).sort((left, right) => compareWorkbenchRows(left, right));
  const pageSize = platformState.workbenchPageSize;
  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
  platformState.workbenchPage = Math.min(platformState.workbenchPage, totalPages);
  const pageRows = rows.slice((platformState.workbenchPage - 1) * pageSize, platformState.workbenchPage * pageSize);
  const pageInfo = document.querySelector('#dashboard-workbench-page');
  const prev = document.querySelector('#dashboard-workbench-prev');
  const next = document.querySelector('#dashboard-workbench-next');
  if (pageInfo) pageInfo.textContent = `Page ${platformState.workbenchPage} / ${totalPages} - ${rows.length.toLocaleString('fr-FR')} element(s)`;
  if (prev) prev.disabled = platformState.workbenchPage <= 1;
  if (next) next.disabled = platformState.workbenchPage >= totalPages;
  if (pageRows.length === 0) {
    body.innerHTML = '<tr><td colspan="6" class="empty-state">Aucun élément dans cette liste.</td></tr>';
    return;
  }
  const columns = getWorkbenchColumns(platformState.workbenchLayer, pageRows);
  const headerRow = body.closest('table')?.querySelector('thead tr');
  if (headerRow) {
    headerRow.innerHTML = `${columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join('')}<th>Action</th>`;
  }
  body.innerHTML = pageRows.map((row) => `
    <tr class="${row.featureId === platformState.workbenchSelectedFeatureId ? 'selected' : ''}" data-layer="${escapeHtml(row.layerKey || platformState.workbenchLayer)}" data-feature-id="${escapeHtml(row.featureId)}">
      ${columns.map((column) => `<td>${escapeHtml(formatAttributeValue(getWorkbenchCellValue(row, column.key)))}</td>`).join('')}
      <td>
        <button type="button" class="table-action-button" data-row-action="open">Ouvrir fiche</button>
        <button type="button" class="table-action-button" data-row-action="map">Voir carte</button>
      </td>
    </tr>
  `).join('');
  body.querySelectorAll('tr[data-feature-id]').forEach((tr) => {
    tr.addEventListener('click', () => {
      platformState.workbenchSelectedFeatureId = tr.dataset.featureId;
      renderDashboardWorkbench();
    });
    tr.addEventListener('dblclick', () => {
      openEntityFromLayer(tr.dataset.layer, tr.dataset.featureId, { navigateMap: false });
    });
    tr.querySelector('[data-row-action="open"]')?.addEventListener('click', (event) => {
      event.stopPropagation();
      platformState.workbenchSelectedFeatureId = tr.dataset.featureId;
      openEntityFromLayer(tr.dataset.layer, tr.dataset.featureId, { navigateMap: false });
    });
    tr.querySelector('[data-row-action="map"]')?.addEventListener('click', (event) => {
      event.stopPropagation();
      platformState.workbenchSelectedFeatureId = tr.dataset.featureId;
      openLayerWorkbench(tr.dataset.layer, tr.dataset.featureId);
    });
  });
}

function compareWorkbenchRows(left, right) {
  const key = platformState.workbenchSortKey || 'nom';
  const order = platformState.workbenchSortOrder === 'desc' ? -1 : 1;
  return String(left[key] || '').localeCompare(String(right[key] || ''), 'fr') * order;
}

function getWorkbenchColumns(layerKey, rows) {
  const effectiveLayer = layerKey === 'mixed'
    ? rows.find((row) => row.layerKey)?.layerKey || 'provinces'
    : layerKey;
  const definitions = {
    provinces: [
      { key: 'nom', label: 'Nom' },
      { key: 'code_province_fdsu', label: 'Code FDSU' },
      { key: 'zone_fdsu', label: 'Zone FDSU' },
      { key: 'territoires', label: 'Territoires' },
      { key: 'collectivites', label: 'Collectivités' },
      { key: 'groupements', label: 'Groupements' },
      { key: 'localites', label: 'Localités' },
      { key: 'qualite', label: 'Score qualité' },
      { key: 'score_priorite_fdsu', label: 'Score FDSU' },
    ],
    territoires: [
      { key: 'nom', label: 'Nom' },
      { key: 'province', label: 'Province' },
      { key: 'zone_fdsu', label: 'Zone' },
      { key: 'collectivites', label: 'Collectivités' },
      { key: 'groupements', label: 'Groupements' },
      { key: 'localites', label: 'Localités' },
      { key: 'score_priorite_fdsu', label: 'Score FDSU' },
    ],
    groupements: [
      { key: 'nom', label: 'Nom' },
      { key: 'collectivite', label: 'Collectivité' },
      { key: 'territoire', label: 'Territoire' },
      { key: 'province', label: 'Province' },
      { key: 'localites', label: 'Localités' },
    ],
    villages: [
      { key: 'nom', label: 'Nom' },
      { key: 'groupement', label: 'Groupement' },
      { key: 'territoire', label: 'Territoire' },
      { key: 'province', label: 'Province' },
      { key: 'coordinates', label: 'Coordonnées' },
      { key: 'population', label: 'Population' },
      { key: 'couverture_numerique', label: 'Couverture 4G' },
      { key: 'score_priorite_fdsu', label: 'Score FDSU' },
    ],
  };
  return definitions[effectiveLayer] || [
    { key: 'nom', label: 'Nom' },
    { key: 'type', label: 'Type' },
    { key: 'province', label: 'Province' },
    { key: 'territoire', label: 'Territoire' },
    { key: 'qualite', label: 'Qualité' },
  ];
}

function getWorkbenchCellValue(row, key) {
  const properties = row.properties || {};
  const profile = getFutureProfile(properties);
  if (key === 'coordinates') return formatGpsCoordinates(properties);
  if (key === 'score_priorite_fdsu') return profile.score_priorite_fdsu || properties.score_priorite_fdsu;
  if (key === 'couverture_numerique') return profile.couverture_numerique || properties.couverture_numerique;
  if (key in row) return row[key];
  return properties[key] ?? profile[key] ?? '';
}

function getFilteredWorkbenchRows() {
  const search = String(document.querySelector('#dashboard-workbench-search')?.value || '').trim().toLowerCase();
  const province = document.querySelector('#dashboard-workbench-province')?.value || '';
  const territory = document.querySelector('#dashboard-workbench-territory')?.value || '';
  return asArray(platformState.workbenchRows).filter((row) => {
    const haystack = [row.nom, row.type, row.province, row.territoire, row.collectivite, row.groupement].join(' ').toLowerCase();
    return (!search || haystack.includes(search))
      && (!province || row.province === province)
      && (!territory || row.territoire === territory);
  }).sort((left, right) => compareWorkbenchRows(left, right));
}

function getWorkbenchSelectedRow() {
  return asArray(platformState.workbenchRows).find((row) => row.featureId === platformState.workbenchSelectedFeatureId) || null;
}

function exportDashboardWorkbench() {
  const rows = getFilteredWorkbenchRows().map((row) => ({
    niveau: row.layerKey || platformState.workbenchLayer,
    nom: row.nom,
    type: row.type,
    province: row.province,
    territoire: row.territoire,
    collectivite: row.collectivite,
    groupement: row.groupement,
    qualite: row.qualite,
  }));
  downloadTextFile(`sig_fdsu_liste_${platformState.workbenchLayer || 'recherche'}_${getExportDateStamp()}.csv`, toCsv(rows), 'text/csv;charset=utf-8');
}

function openEntityFromLayer(layerKey, featureId, options = {}) {
  const row = asArray(cartographyState.data[layerKey])
    .map((item) => normalizeAttributeRow(item, layerKey))
    .find((item) => item.featureId === featureId);
  if (!row) return;
  openEntityProfile(layerKey, row.properties);
  renderChildrenForEntity(layerKey, row.properties);
  if (options.navigateMap) {
    openLayerWorkbench(layerKey, featureId);
  }
}

function renderChildrenForEntity(layerKey, properties) {
  const childLayers = getChildLayers(layerKey);
  if (childLayers.length === 0) return;
  Promise.all(childLayers.map((childLayer) => fetchPlatformLayerData(childLayer))).then((itemsByLayer) => {
    const rows = childLayers.flatMap((childLayer, index) => asArray(itemsByLayer[index])
      .map((item) => ({ ...normalizeAttributeRow(item, childLayer), layerKey: childLayer }))
      .filter((row) => isChildOfEntity(layerKey, properties, row.properties)));
    if (rows.length > 0) {
      const uniqueLayers = [...new Set(rows.map((row) => row.layerKey))];
      const listLayer = uniqueLayers.length === 1 ? uniqueLayers[0] : 'mixed';
      const title = uniqueLayers.length === 1
        ? `${getLayerDisplayLabel(uniqueLayers[0])} rattaches a ${properties.nom}`
        : `Elements rattaches a ${properties.nom}`;
      openDashboardLayerList(listLayer, rows, title);
    }
  });
}

function getChildLayers(layerKey) {
  return {
    rdc: ['provinces'],
    zones: ['provinces'],
    provinces: ['territoires'],
    territoires: ['collectivites', 'groupements', 'villages'],
    collectivites: ['groupements', 'villages'],
    groupements: ['villages'],
    villages: ['sites'],
    sites: ['missions'],
  }[layerKey] || [];
}

function getMapEntityName(properties = {}, layerKey = '') {
  if (layerKey === 'villages') {
    return String(properties.nom || properties.name || properties.localite || '').trim();
  }
  return String(properties.nom || properties.name || properties.libelle || properties.localite || '').trim();
}

function isNationalMapContext(context = nationalMapState.spatialContext) {
  return !context?.layerKey || context.layerKey === 'rdc';
}

function isSameMapEntity(layerKey, properties = {}, contextProperties = {}, contextFeatureId = '') {
  const featureId = getFeatureId(properties, layerKey);
  if (contextFeatureId && featureId === contextFeatureId) return true;
  const contextName = getMapEntityName(contextProperties, layerKey);
  const entityName = getMapEntityName(properties, layerKey);
  return Boolean(contextName && entityName && contextName === entityName);
}

function getHierarchyVisibleLayers(context = nationalMapState.spatialContext) {
  if (isNationalMapContext(context)) return ['provinces'];
  return [context.layerKey, ...getChildLayers(context.layerKey)];
}

function getHierarchyListLayers(context = nationalMapState.spatialContext) {
  if (isNationalMapContext(context)) return ['provinces'];
  return getChildLayers(context.layerKey);
}

function ensureNationalHierarchyLayersLoaded(layerKeys = []) {
  const uniqueKeys = [...new Set(asArray(layerKeys).filter(Boolean))];
  return Promise.all(uniqueKeys.map((layerKey) => loadNationalMapLayer(layerKey)));
}

function applyDashboardNationalHierarchyView() {
  nationalMapState.spatialContext = {
    level: 'national',
    layerKey: 'rdc',
    featureId: 'rdc',
    properties: {},
    feature: null,
  };
  nationalMapState.spatialContextTrail = [{ layerKey: 'rdc', label: 'RDC', properties: {} }];
  renderNationalContextMap();
  renderNationalMapBreadcrumb();
}

function renderNationalContextMap() {
  if (!nationalMapState.map) return;
  const visibleLayers = getHierarchyVisibleLayers();

  Object.keys(nationalMapState.layers).forEach((layerKey) => {
    if (layerKey === 'rdcBoundary') {
      const boundary = nationalMapState.layers.rdcBoundary;
      if (boundary && boundary.getLayers().length > 0 && !nationalMapState.map.hasLayer(boundary)) {
        boundary.addTo(nationalMapState.map);
      }
      return;
    }

    refreshNationalMapLayer(layerKey);
    const layer = nationalMapState.layers[layerKey];
    if (!layer) return;
    const shouldDisplay = visibleLayers.includes(layerKey) && layer.getLayers().length > 0;

    if (shouldDisplay) {
      if (!nationalMapState.map.hasLayer(layer)) layer.addTo(nationalMapState.map);
    } else if (nationalMapState.map.hasLayer(layer)) {
      nationalMapState.map.removeLayer(layer);
    }
  });

  refreshNationalMapLayerPresentation();
  renderNationalSynchronizedList();
  updateNationalHierarchyMessage();
  updateNationalMapBackButton();
  fitNationalMapToContext();
}

function showNationalMapMessage(message = '') {
  if (!nationalMapState.messageElement) return;
  nationalMapState.messageElement.textContent = message;
  nationalMapState.messageElement.hidden = !message;
}

function updateNationalHierarchyMessage() {
  const context = nationalMapState.spatialContext;
  if (isNationalMapContext(context)) {
    showNationalMapMessage('');
    return;
  }
  const childLayers = getChildLayers(context.layerKey);
  const hasChildren = childLayers.some((layerKey) => asArray(nationalMapState.features[layerKey])
    .some((feature) => isWithinHierarchyContext(layerKey, feature.properties || {})));
  showNationalMapMessage(hasChildren ? '' : 'Aucune subdivision disponible pour ce niveau.');
}

function updateNationalMapBackButton() {
  const backButton = document.querySelector('#dashboard-map-context-back');
  if (!backButton) return;
  backButton.disabled = (nationalMapState.spatialContextTrail?.length ?? 0) <= 1;
}

function fitNationalMapToContext() {
  if (!nationalMapState.map) return;
  const context = nationalMapState.spatialContext;
  if (isNationalMapContext(context)) {
    const provincesLayer = nationalMapState.layers.provinces;
    if (provincesLayer?.getBounds) {
      const bounds = provincesLayer.getBounds();
      if (bounds.isValid()) {
        nationalMapState.map.fitBounds(bounds, { padding: [16, 16] });
        return;
      }
    }
    fitNationalMapToRdc();
    return;
  }

  const parentLayer = nationalMapState.featureLayers[context.layerKey]?.[context.featureId];
  if (parentLayer) {
    fitNationalMapToFeatureLayer(parentLayer);
    return;
  }

  const visibleLayer = getHierarchyVisibleLayers(context).find((layerKey) => {
    const layer = nationalMapState.layers[layerKey];
    return layer?.getBounds && layer.getBounds().isValid();
  });
  if (visibleLayer) fitNationalMapBounds(nationalMapState.layers[visibleLayer]);
}

function goBackNationalContext() {
  const trail = nationalMapState.spatialContextTrail || [];
  if (trail.length <= 1) {
    resetDashboardNationalView();
    return;
  }
  navigateNationalMapBreadcrumb(trail.length - 2);
}

function setNationalMapContext(layerKey, properties = {}, feature = null) {
  activateNationalSpatialContext(layerKey, properties, feature);
}
function isChildOfEntity(parentLayer, parentProperties, childProperties) {
  const name = parentProperties.nom;
  if (!name) return false;
  if (parentLayer === 'zones') return childProperties.zone_fdsu === parentProperties.zone_fdsu || childProperties.zone_fdsu === parentProperties.code;
  if (parentLayer === 'provinces') return childProperties.province === name;
  if (parentLayer === 'territoires') return childProperties.territoire === name;
  if (parentLayer === 'collectivites') return childProperties.collectivite === name;
  if (parentLayer === 'groupements') return childProperties.groupement === name;
  if (parentLayer === 'villages') return childProperties.localite === name;
  return false;
}

function isWithinHierarchyContext(layerKey, properties, context = nationalMapState.spatialContext) {
  if (layerKey === 'rdcBoundary') return true;
  if (isNationalMapContext(context)) return layerKey === 'provinces';

  const contextLayer = context.layerKey;
  const contextProperties = context.properties || {};

  if (layerKey === contextLayer) {
    return isSameMapEntity(layerKey, properties, contextProperties, context.featureId);
  }

  if (getChildLayers(contextLayer).includes(layerKey)) {
    return isChildOfEntity(contextLayer, contextProperties, properties);
  }

  return false;
}

function refreshVisibleCartographyLayers() {
  Object.keys(cartographyState.layers).forEach((layerKey) => {
    if (layerKey === 'rdcBoundary') return;
    refreshVisibleCartographyLayer(layerKey);
  });
  refreshCartographicLayerPresentation();
  renderSynchronizedLayerList();
}

function refreshVisibleCartographyLayer(layerKey) {
  const layer = cartographyState.layers[layerKey];
  if (!layer || !layer.clearLayers || !layer.addData) return;
  const features = asArray(cartographyState.features[layerKey]);
  layer.clearLayers();
  cartographyState.featureLayers[layerKey] = {};
  if (features.length > 0) {
    layer.addData({ type: 'FeatureCollection', features });
  }
}

function refreshNationalMapLayer(layerKey) {
  const layer = nationalMapState.layers[layerKey];
  if (!layer || !layer.clearLayers || !layer.addData) return;
  const features = asArray(nationalMapState.features[layerKey])
    .filter((feature) => isWithinHierarchyContext(layerKey, feature.properties || {}));
  layer.clearLayers();
  nationalMapState.featureLayers[layerKey] = {};
  if (features.length > 0) {
    layer.addData({ type: 'FeatureCollection', features });
  }
}

function buildFeatureCollection(items, layerKey) {
  return {
    type: 'FeatureCollection',
    features: items
      .map((item) => buildFeature(item, layerKey))
      .filter(Boolean),
  };
}

function buildFeature(item, layerKey) {
  item = enrichFdsuNomenclature(item);
  const geometry = item?.geometry;
  if (!geometry || !geometry.type || !Array.isArray(geometry.coordinates)) return null;
  const metadata = item?.metadata || {};
  const attributes = item?.attributs || {};
  const extendedData = metadata.extended_data || attributes.extended_data || {};
  const coordinates = extractGeometryCoordinate(geometry);

  return {
    type: 'Feature',
    geometry,
    properties: {
      layer: layerKey,
      canonical_id: item.canonical_id || item.id || '',
      code: item.code || item.code_officiel || item.canonical_id || item.id || '',
      nom: item.nom || item.name || 'Non renseigné',
      type: item.type_localite || item.type_collectivite || item.niveau || extendedData.TYPE || layerKey,
      province: item.province || '',
      territoire: item.territoire || '',
      collectivite: item.collectivité || item.collectivite || item.collectivite_parent || '',
      groupement: item.groupement || '',
      localite: layerKey === 'villages' ? item.nom || item.name || '' : '',
      zone_fdsu: item.zone_fdsu || item.zone || '',
      zone_nom: item.zone_nom || getZoneName(item.zone_fdsu),
      code_province_fdsu: item.code_province_fdsu || '',
      code_territoire_fdsu: item.code_territoire_fdsu || '',
      fdsu_codification_format: item.fdsu_codification_format || FDSU_CODE_FORMAT,
      source: item.source || item.source_file || '',
      qualite: item.qualité ?? item.qualite ?? item.quality ?? '',
      statut: item.statut || '',
      latitude: coordinates?.lat ?? '',
      longitude: coordinates?.lng ?? '',
      observations: metadata.description || attributes.description || '',
      anomalies: asArray(item.incoherences || item.anomalies).join(', '),
      metadata,
      future_profile: item.future_profile || metadata.future_profile || {},
      geometry,
    },
  };
}

function extractGeometryCoordinate(geometry) {
  const coordinates = geometry?.coordinates;
  if (!Array.isArray(coordinates)) return null;
  let cursor = coordinates;
  while (Array.isArray(cursor?.[0])) {
    cursor = cursor[0];
  }
  if (typeof cursor?.[0] !== 'number' || typeof cursor?.[1] !== 'number') return null;
  return { lng: cursor[0], lat: cursor[1] };
}

function makePointMarker(latlng, color, fillColor, radius = 4) {
  return L.circleMarker(latlng, {
    radius,
    weight: 1,
    color,
    fillColor,
    fillOpacity: 0.72,
  });
}

function styleRdcBoundaryFeature() {
  return {
    color: '#e2e8f0',
    weight: 2.5,
    opacity: 0.95,
    fillColor: '#020617',
    fillOpacity: 0.06,
  };
}

function styleProvinceFeature() {
  return {
    color: '#2563eb',
    weight: 1.5,
    opacity: 0.95,
    fillColor: '#60a5fa',
    fillOpacity: 0.12,
  };
}

function styleTerritoryFeature() {
  return {
    color: '#0891b2',
    weight: 1,
    opacity: 0.95,
    fillColor: '#22d3ee',
    fillOpacity: 0.08,
  };
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
  const isSyntheticZone = Boolean(feature?.properties?.synthetic_zone_layer);

  return {
    color: isSyntheticZone ? zoneStyle.fillColor : zoneStyle.color,
    weight: isSyntheticZone ? 1 : 2,
    opacity: 1,
    fillColor: zoneStyle.fillColor,
    fillOpacity: isSyntheticZone ? 0.58 : 0.28,
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
    properties.zone_fdsu,
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

function buildFdsuProgramPopupHtml(properties, layerKey) {
  const programmeLabel = properties.programme || getCartographyLayerLabel(layerKey);
  const lines = [
    ['strong', properties.name || properties.site_name || 'Site FDSU'],
    ['label', 'Code', properties.site_code || properties.code || properties.official_code],
    ['label', 'Localité', properties.localite || properties.locality_name || properties.name],
    ['text', properties.province],
    ['text', properties.territoire],
    ['text', properties.zone],
    ['label', 'Programme', programmeLabel],
            ['label', 'Statut source (brut)', properties.status || properties.operational_status || 'À renseigner'],
            ['label', 'Statut de donnée', properties.data_status || properties.data_quality || properties.quality_label || 'À renseigner'],
    ['label', 'Score de priorité', properties.priority_score ?? properties.fdsu_score ?? properties.priority_status ?? 'À calculer'],
    ['label', 'Niveau de priorité', properties.priority_level_label || properties.priority_level || properties.priority_status],
    ['label', 'Critères principaux', Array.isArray(properties.top_criteria) ? properties.top_criteria.join(', ') : properties.top_criteria],
    ['label', 'Distance HGR', properties.distance_hgr_m != null ? `${Math.round(properties.distance_hgr_m)} m` : properties.nearest_hgr],
    ['label', 'Distance Centre de Santé', properties.distance_health_center_m != null ? `${Math.round(properties.distance_health_center_m)} m` : properties.nearest_health_center],
  ];

  return `
    <div class="sites-40-popup decision-map-popup">
      ${lines.map((entry) => {
        if (entry[0] === 'strong') {
          const value = String(entry[1] || '').trim();
          return value ? `<strong>${escapeHtml(value)}</strong>` : '';
        }
        if (entry[0] === 'label') {
          const value = String(entry[2] ?? '').trim();
          if (!value) return '';
          return `${escapeHtml(entry[1])} : ${escapeHtml(value)}`;
        }
        const value = String(entry[1] || '').trim();
        return value ? escapeHtml(value) : '';
      }).filter(Boolean).join('<br>')}
      <br><span class="map-popup-action">Voir fiche site</span>
    </div>
  `;
}

function onFdsuProgramSiteEachFeature(feature, layer, layerKey) {
  if (!layer) return;
  const properties = feature?.properties || {};
  const featureId = getFeatureId(properties, layerKey);
  if (!cartographyState.featureLayers[layerKey]) cartographyState.featureLayers[layerKey] = {};
  cartographyState.featureLayers[layerKey][featureId] = layer;

  const popupHtml = layerKey === 'sites_300'
    ? buildFdsuProgramPopupHtml(properties, layerKey)
    : `
    <div class="sites-40-popup">
      <strong>${escapeHtml(properties.name || 'Site')}</strong><br>
      ${escapeHtml(properties.province || '')}<br>
      ${escapeHtml(properties.territoire || '')}<br>
      ${escapeHtml(properties.zone || '')}<br>
      Programme : ${escapeHtml(properties.programme || getCartographyLayerLabel(layerKey))}
    </div>
  `;

  if (layer.bindPopup) {
    layer.bindPopup(popupHtml, { maxWidth: 240, className: 'sites-40-leaflet-popup' });
  }

  renderSmartTooltip(feature, layer, layerKey);

  layer.on('mouseover', () => {
    highlightMapFeature(layerKey, feature, layer);
  });

  layer.on('mouseout', () => {
    if (cartographyState.selectedLayer !== layer) resetHoverMapFeature(layerKey, feature, layer);
  });

  layer.on('click', (event) => {
    if (event?.originalEvent && typeof L !== 'undefined') {
      L.DomEvent.stopPropagation(event.originalEvent);
    }
    selectMapFeature(layerKey, feature, layer, { zoom: true });
    if (cartographyState.map?.closePopup) cartographyState.map.closePopup();
    const siteId = properties.business_id || properties.site_code || properties.code || properties.id;
    const program = properties.programme || properties.program_code
      || (layerKey === 'sites_300' ? 'sites_300' : (layerKey === 'sites_40' ? 'sites_40' : null));
    if (siteId && typeof window.openDecisionCase === 'function') {
      window.openDecisionCase('site', siteId, program);
    } else if (siteId) {
      const qs = program ? `?program_code=${encodeURIComponent(program)}` : '';
      window.location.hash = `decision-case/site/${encodeURIComponent(siteId)}${qs}`;
    }
  });
}

function onGeoEachFeature(feature, layer, layerKey) {
  if (!layer) return;
  const properties = feature?.properties || {};
  const featureId = getFeatureId(properties, layerKey);
  if (!cartographyState.featureLayers[layerKey]) cartographyState.featureLayers[layerKey] = {};
  cartographyState.featureLayers[layerKey][featureId] = layer;

  if (layer.bindPopup) {
    if (typeof window !== 'undefined' && window.SigMapTooltips?.bindRichPopup) {
      window.SigMapTooltips.bindRichPopup(layer, feature, layerKey, { onNavigate: true });
    } else {
      layer.bindPopup(`
        <div class="decision-map-popup">
          <strong>${escapeHtml(getFeatureProperty(properties, ['nom', 'name', 'libelle']))}</strong><br>
          Niveau : ${escapeHtml(getFeatureProperty(properties, ['type', 'niveau']) || getCartographyLayerLabel(layerKey))}<br>
          Parent : ${escapeHtml(getFeatureProperty(properties, ['parent_name', 'province', 'territoire', 'parent']) || '—')}<br>
          Sites FDSU : ${escapeHtml(properties.fdsu_sites_count ?? properties.sites_count ?? '—')}<br>
          Établissements santé : ${escapeHtml(properties.health_facilities_count ?? '—')}<br>
          Indicateurs : ${escapeHtml(properties.available_indicators || 'Référentiel administratif')}<br>
          <span class="map-popup-action">Voir fiche territoriale</span>
        </div>
      `, { maxWidth: 280, className: 'decision-map-popup-wrapper sig-map-popup', autoPan: true, keepInView: true });
    }
  }

  renderSmartTooltip(feature, layer, layerKey);

  layer.on('mouseover', () => {
    highlightMapFeature(layerKey, feature, layer);
  });

  layer.on('mouseout', () => {
    if (cartographyState.selectedLayer !== layer) resetHoverMapFeature(layerKey, feature, layer);
  });

  layer.on('click', (event) => {
    if (event?.originalEvent && typeof L !== 'undefined') {
      L.DomEvent.stopPropagation(event.originalEvent);
    }
    selectMapFeature(layerKey, feature, layer, { zoom: true });
    renderFeatureDetails(feature, layerKey);
    if (layer.openPopup && event?.latlng) {
      layer.openPopup(event.latlng);
    }
    openEntityProfile(layerKey, properties, feature);
    enrichFeatureDetailsFromApi(feature, layerKey);
  });

  layer.on('dblclick', (event) => {
    if (event?.originalEvent && typeof L !== 'undefined') {
      L.DomEvent.stopPropagation(event.originalEvent);
    }
    openEntityProfile(layerKey, properties, feature);
    if (layerKey === 'territoires' || layerKey === 'territory') {
      const tid = properties.territoire_id || properties.id || properties.code || properties.nom;
      if (tid) window.location.hash = `territorial-intelligence/${encodeURIComponent(tid)}`;
    }
  });
}

function renderDashboardZonesSidebar() {
  const list = document.querySelector('.dashboard-zones-list');
  if (!list) return;

  list.innerHTML = FDSU_ZONE_CODES.map((zoneCode) => {
    const zoneClass = `zone-${zoneCode.toLowerCase()}`;
    const zoneName = getZoneName(zoneCode);
    const stats = computeZoneStats(zoneCode);
    const metaParts = [];
    if (stats.provinces.length > 0) metaParts.push(`${stats.provinces.length} provinces`);
    if (stats.territoires > 0) metaParts.push(`${stats.territoires.toLocaleString('fr-FR')} territoires`);
    const localitesLine = stats.localites > 0
      ? `${stats.localites.toLocaleString('fr-FR')} localités`
      : '';

    return `
      <li class="zone-item sig-zone-card ${zoneClass}" data-zone="${zoneCode}" tabindex="0">
        <div class="sig-zone-card-body">
          <strong class="sig-zone-card-title">${escapeHtml(zoneName)}</strong>
          ${metaParts.length ? `<p class="sig-zone-card-meta">${escapeHtml(metaParts.join(' · '))}</p>` : ''}
          ${localitesLine ? `<p class="sig-zone-card-count">${escapeHtml(localitesLine)}</p>` : ''}
        </div>
      </li>
    `;
  }).join('');

  setupDashboardZoneShortcuts();
}

function isPresentableTooltipValue(value) {
  if (value === null || value === undefined) return false;
  const text = String(value).trim();
  if (!text || text === '0' || text === '—') return false;
  const lowered = text.toLowerCase();
  return !['non disponible', 'inconnue', 'inconnu', 'n/a', 'na', 'null', 'undefined'].includes(lowered);
}

function formatTooltipPopulation(value) {
  if (!isPresentableTooltipValue(value)) return '';
  const num = Number(String(value).replace(/\s/g, '').replace(',', '.'));
  if (Number.isFinite(num) && num >= 1000000) {
    return `${(num / 1000000).toFixed(1).replace('.', ',')} M`;
  }
  if (Number.isFinite(num) && num >= 1000) {
    return `${Math.round(num).toLocaleString('fr-FR')}`;
  }
  return formatAttributeValue(value);
}

function getTooltipLayerLabel(layerKey) {
  const labels = {
    zones: 'Zone FDSU',
    provinces: 'Province',
    territoires: 'Territoire',
    collectivites: 'Collectivité',
    groupements: 'Groupement',
    villages: 'Localité',
    sites: 'Site FDSU',
    sites_all: 'Tous les sites FDSU',
    sites_40: 'Site 40 FDSU',
    sites_300: 'Site 300 FDSU',
    missions: 'Mission',
    telecom_vodacom: 'Couverture Vodacom',
    telecom_orange: 'Couverture Orange',
    telecom_fiber_mw: 'Lien micro-ondes / fibre',
    telecom_fiberco: 'Backbone fibre',
    telecom_fttx: 'Accès fibre (FTTx)',
    health: 'Établissement de santé',
    ccn: 'Centre communautaire',
    uncovered_locality: 'Localité non couverte',
  };
  return labels[layerKey] || 'Entité';
}

function getTooltipLayerIcon(layerKey) {
  const icons = {
    zones: '🗺️',
    provinces: '📍',
    territoires: '📍',
    collectivites: '📍',
    groupements: '📍',
    villages: '📍',
    sites: '📡',
    sites_all: '📡',
    sites_40: '🟣',
    sites_300: '🔵',
    missions: '🎯',
    telecom_vodacom: '📶',
    telecom_orange: '📶',
    telecom_fiber_mw: '📡',
    telecom_fiberco: '🧵',
    telecom_fttx: '🧵',
    health: '🏥',
    ccn: '🏛️',
    uncovered_locality: '⚠️',
  };
  return icons[layerKey] || '📍';
}

function buildCompactTooltipLines(layerKey, properties, stats) {
  // Télécom / fibre / backbone : composant partagé (contenu métier unifié)
  if (typeof window !== 'undefined' && window.SigMapTooltips?.buildLines && isTelecomLayer(layerKey)) {
    const shared = window.SigMapTooltips.buildLines(layerKey, properties);
    if (shared?.length) return shared;
  }

  const lines = [];

  if (layerKey === 'provinces') {
    const code = getFeatureProperty(properties, ['code_province_fdsu', 'code']);
    if (isPresentableTooltipValue(code)) lines.push(`Code : ${code}`);
    if (stats.territoires > 0) lines.push(`${stats.territoires.toLocaleString('fr-FR')} territoires`);
    const population = formatTooltipPopulation(stats.population);
    if (population) lines.push(`Population : ${population}`);
    if (properties.fdsu_sites_count != null) lines.push(`Sites FDSU : ${properties.fdsu_sites_count}`);
    if (properties.health_facilities_count != null) lines.push(`Établissements santé : ${properties.health_facilities_count}`);
    if (properties.uncovered_localities_count != null) lines.push(`Localités non couvertes : ${properties.uncovered_localities_count}`);
    if (isPresentableTooltipValue(properties.ndci)) lines.push(`NDCI : ${properties.ndci}`);
    if (isPresentableTooltipValue(properties.data_quality || properties.quality_label)) {
      lines.push(`Qualité des données : ${properties.data_quality || properties.quality_label}`);
    }
    return lines;
  }

  if (layerKey === 'territoires') {
    const province = getFeatureProperty(properties, ['province']);
    if (isPresentableTooltipValue(province)) lines.push(`Province : ${province}`);
    if (stats.collectivites > 0) lines.push(`${stats.collectivites.toLocaleString('fr-FR')} collectivités`);
    if (stats.groupements > 0) lines.push(`${stats.groupements.toLocaleString('fr-FR')} groupements`);
    if (stats.localites > 0) lines.push(`${stats.localites.toLocaleString('fr-FR')} localités`);
    const population = formatTooltipPopulation(stats.population);
    if (population) lines.push(`Population : ${population}`);
    if (properties.fdsu_sites_count != null) lines.push(`Sites FDSU : ${properties.fdsu_sites_count}`);
    if (properties.uncovered_localities_count != null) lines.push(`Localités non couvertes : ${properties.uncovered_localities_count}`);
    if (isPresentableTooltipValue(properties.ndci || properties.ndci_score)) {
      lines.push(`NDCI : ${properties.ndci || properties.ndci_score}`);
    }
    if (isPresentableTooltipValue(properties.data_quality || properties.quality_label || properties.cdqs)) {
      lines.push(`Qualité des données : ${properties.data_quality || properties.quality_label || properties.cdqs}`);
    }
    if (properties.health_facilities_count != null) lines.push(`Établissements santé : ${properties.health_facilities_count}`);
    return lines;
  }

  if (layerKey === 'collectivites') {
    const territoire = getFeatureProperty(properties, ['territoire']);
    if (isPresentableTooltipValue(territoire)) lines.push(`Territoire : ${territoire}`);
    if (stats.groupements > 0) lines.push(`${stats.groupements.toLocaleString('fr-FR')} groupements`);
    return lines;
  }

  if (layerKey === 'groupements') {
    const collectivite = getFeatureProperty(properties, ['collectivite']);
    if (isPresentableTooltipValue(collectivite)) lines.push(`Collectivité : ${collectivite}`);
    if (stats.localites > 0) lines.push(`${stats.localites.toLocaleString('fr-FR')} localités`);
    const population = formatTooltipPopulation(stats.population);
    if (population) lines.push(`Population : ${population}`);
    return lines;
  }

  if (layerKey === 'villages') {
    const groupement = getFeatureProperty(properties, ['groupement']);
    if (isPresentableTooltipValue(groupement)) lines.push(`Groupement : ${groupement}`);
    const territoire = getFeatureProperty(properties, ['territoire', 'territory']);
    if (isPresentableTooltipValue(territoire)) lines.push(`Territoire : ${territoire}`);
    const population = formatTooltipPopulation(stats.population || properties.population);
    if (population) lines.push(`Population : ${population}`);
    if (properties.coverage_status === 'uncovered' || properties.is_uncovered) {
      if (isPresentableTooltipValue(properties.priority_level || properties.priorite)) {
        lines.push(`Priorité : ${properties.priority_level || properties.priorite}`);
      }
      if (isPresentableTooltipValue(properties.category || properties.categorie)) {
        lines.push(`Catégorie : ${properties.category || properties.categorie}`);
      }
    }
    return lines;
  }

  if (layerKey === 'sites_40' || layerKey === 'sites_all' || layerKey === 'sites_300') {
    const programme = properties.programme
      || (layerKey === 'sites_300' ? 'Sites 300' : 'Sites 40');
    [
      ['Code', properties.site_code || properties.code || properties.official_code],
      ['Localité', properties.localite || properties.locality || properties.village || properties.name],
      ['Programme', programme],
      ['Priorité', properties.priority_level_label || properties.priority_level || properties.priority_status],
      ['Population cible', formatTooltipPopulation(properties.population_cible || properties.population || properties.target_population)],
      ['Statut de donnée', properties.data_status || properties.data_quality || properties.quality_label || properties.status || properties.operational_status || 'À renseigner'],
      ['Province', properties.province],
      ['Territoire', properties.territoire],
    ].forEach(([label, value]) => {
      if (isPresentableTooltipValue(value)) lines.push(`${label} : ${value}`);
    });
    return lines;
  }

  if (layerKey === 'sites') {
    [
      ['Code', getFeatureProperty(properties, ['site_code', 'code', 'official_code'])],
      ['Localité', getFeatureProperty(properties, ['localite', 'locality', 'nom', 'name'])],
      ['État', getFeatureProperty(properties, ['etat', 'status', 'statut'])],
      ['Technologie', getFeatureProperty(properties, ['technologie', 'technology', 'technologies'])],
      ['Opérateur', getFeatureProperty(properties, ['operateur', 'operator', 'operateurs'])],
      ['Priorité', getFeatureProperty(properties, ['priorite', 'score_priorite_fdsu', 'priority'])],
      ['Statut de donnée', getFeatureProperty(properties, ['data_quality', 'data_status', 'quality_label']) || 'À renseigner'],
    ].forEach(([label, value]) => {
      if (isPresentableTooltipValue(value)) lines.push(`${label} : ${value}`);
    });
    return lines;
  }

  if (layerKey === 'missions') {
    [
      ['Statut', getFeatureProperty(properties, ['statut', 'status', 'etat'])],
      ['Date', getFeatureProperty(properties, ['date', 'date_mission', 'started_at'])],
    ].forEach(([label, value]) => {
      if (isPresentableTooltipValue(value)) lines.push(`${label} : ${value}`);
    });
    return lines;
  }

  if (layerKey === 'zones') {
    if (stats.territoires > 0) lines.push(`${stats.territoires.toLocaleString('fr-FR')} territoires`);
    if (stats.localites > 0) lines.push(`${stats.localites.toLocaleString('fr-FR')} localités`);
  }

  if (isTelecomLayer(layerKey)) {
    [
      ['Type', properties.infra_type || properties.line_type || properties.polygon_type || properties.infra_category || properties.technology],
      ['Opérateur', properties.operator_name || properties.operator_code],
      ['Technologie', properties.technology],
      ['Province', properties.province],
      ['Territoire', properties.territoire],
    ].forEach(([label, value]) => {
      if (isPresentableTooltipValue(value)) lines.push(`${label} : ${value}`);
    });
    const dist = properties.distance_to_selected_site_m != null
      ? `${Math.round(properties.distance_to_selected_site_m)} m`
      : (properties.distance_m != null ? `${Math.round(properties.distance_m)} m` : null);
    if (isPresentableTooltipValue(dist)) lines.push(`Distance au site : ${dist}`);
    if (!lines.length) lines.push('Infrastructure télécom');
    return lines;
  }

  return lines;
}

function buildCompactTooltipHtml(feature, layerKey) {
  const properties = feature?.properties || {};
  const stats = computeSpatialContextStats(layerKey, properties);
  const name = getFeatureProperty(properties, ['nom', 'name', 'libelle', 'infra_name', 'line_name', 'polygon_name', 'site_name'])
    || getTooltipLayerLabel(layerKey);
  const lines = buildCompactTooltipLines(layerKey, properties, stats);

  return `
    <div class="map-smart-tooltip">
      <div class="map-smart-tooltip-title">
        <span class="map-smart-tooltip-icon">${getTooltipLayerIcon(layerKey)}</span>
        <span>${escapeHtml(name)}</span>
      </div>
      <span class="map-smart-tooltip-type">${escapeHtml(getTooltipLayerLabel(layerKey))}</span>
      ${lines.map((line) => `<span class="map-smart-tooltip-line">${escapeHtml(line)}</span>`).join('')}
      <span class="map-smart-tooltip-hint">Cliquer pour analyser en détail</span>
    </div>
  `;
}

function renderSmartTooltip(feature, layer, layerKey) {
  if (!layer?.bindTooltip) return;
  if (typeof window !== 'undefined' && window.SigMapTooltips?.bind) {
    // Tooltip only — le clic métier reste géré par onEachFeature (fiche / sélection)
    window.SigMapTooltips.bind(layer, feature, layerKey, { interactive: false });
    return;
  }
  layer.bindTooltip(buildCompactTooltipHtml(feature, layerKey), {
    sticky: false,
    direction: 'top',
    opacity: 1,
    className: 'sig-map-tooltip',
  });
}

function selectMapFeature(layerKey, feature, layer, options = {}) {
  resetSelectedMapFeatureStyle();
  const featureId = getFeatureId(feature?.properties || {}, layerKey);
  const activeLayer = cartographyState.featureLayers[layerKey]?.[featureId] || layer;
  cartographyState.selectedLayer = activeLayer;
  cartographyState.selectedFeature = feature;
  applySelectedMapFeatureStyle(activeLayer, feature);
  if (options.zoom) fitMapToFeatureLayer(activeLayer);
  if (activeLayer?.bringToFront) activeLayer.bringToFront();
  refreshCartographicLayerPresentation();
  renderSynchronizedLayerList();
}

function highlightMapFeature(layerKey, feature, layer) {
  cartographyState.hoveredFeatureId = getFeatureId(feature?.properties || {}, layerKey);
  if (layer?.setStyle && layer !== cartographyState.selectedLayer) {
    const baseStyle = getDefaultFeatureStyle(feature, layerKey);
    layer.setStyle({ ...baseStyle, weight: Math.max(Number(baseStyle.weight) || 1, 2.5), fillOpacity: Math.max(Number(baseStyle.fillOpacity) || 0.18, 0.32) });
  }
  highlightSynchronizedListRow(layerKey, cartographyState.hoveredFeatureId);
}

function resetHoverMapFeature(layerKey, feature, layer) {
  if (layer?.setStyle && layer !== cartographyState.selectedLayer) {
    layer.setStyle(getDefaultFeatureStyle(feature, layerKey));
  }
  cartographyState.hoveredFeatureId = null;
  highlightSynchronizedListRow('', '');
}

function resetSelectedMapFeatureStyle() {
  const layer = cartographyState.selectedLayer;
  const feature = cartographyState.selectedFeature || layer?.feature;
  if (!layer?.setStyle) return;
  layer.setStyle(getDefaultFeatureStyle(feature, feature?.properties?.layer || ''));
  layer.getElement?.()?.classList.remove('map-feature-selected');
}

function applySelectedMapFeatureStyle(layer, feature) {
  if (!layer?.setStyle) return;
  const baseStyle = getDefaultFeatureStyle(feature, feature?.properties?.layer || '');
  layer.setStyle({
    ...baseStyle,
    weight: Math.max(Number(baseStyle.weight) || 1, 3),
    opacity: 1,
    fillOpacity: Math.max(Number(baseStyle.fillOpacity) || 0.25, 0.42),
  });
  layer.getElement?.()?.classList.add('map-feature-selected');
}

function getDefaultFeatureStyle(feature, layerKey) {
  if (feature?.properties?.synthetic_zone_layer || layerKey === 'zones') return styleZoneFeature(feature);
  if (layerKey === 'provinces') return styleProvinceFeature(feature);
  if (layerKey === 'territoires') return styleTerritoryFeature(feature);
  if (layerKey === 'collectivites') return styleCollectivitesFeature(feature);
  return { color: '#38bdf8', weight: 2, opacity: 1, fillColor: '#38bdf8', fillOpacity: 0.28 };
}

function activateNationalSpatialContext(layerKey, properties = {}, feature = null) {
  if (layerKey === 'rdcBoundary') {
    resetDashboardNationalView();
    return;
  }

  const layersToLoad = [layerKey, ...getChildLayers(layerKey)];
  ensureNationalHierarchyLayersLoaded(layersToLoad).then(() => {
    nationalMapState.spatialContext = {
      level: layerKey,
      layerKey,
      featureId: getFeatureId(properties, layerKey),
      properties,
      feature,
    };
    nationalMapState.spatialContextTrail = buildSpatialContextTrail(layerKey, properties);
    renderNationalContextMap();
    renderNationalMapBreadcrumb();
  });
}

function resetMapToNationalView() {
  resetSelectedMapFeatureStyle();
  cartographyState.selectedLayer = null;
  cartographyState.selectedFeature = null;
  cartographyState.spatialContext = null;
  cartographyState.spatialContextTrail = [{ layerKey: 'rdc', label: 'RDC', properties: {} }];
  renderMapBreadcrumb();
  fitMapToRdc();
  showZonesMessage('');
}

function resetDashboardNationalView() {
  nationalMapState.spatialContext = null;
  applyDashboardNationalHierarchyView();
}

function buildSpatialContextTrail(layerKey, properties = {}) {
  const trail = [{ layerKey: 'rdc', label: 'RDC', properties: {} }];
  const province = layerKey === 'provinces' ? getMapEntityName(properties, 'provinces') : properties.province;
  const territoire = layerKey === 'territoires' ? getMapEntityName(properties, 'territoires') : properties.territoire;
  const collectivite = layerKey === 'collectivites' ? getMapEntityName(properties, 'collectivites') : properties.collectivite;
  const groupement = layerKey === 'groupements' ? getMapEntityName(properties, 'groupements') : properties.groupement;
  const localite = layerKey === 'villages' ? getMapEntityName(properties, 'villages') : properties.localite;

  if (province) {
    trail.push({
      layerKey: 'provinces',
      label: province,
      properties: { ...properties, nom: province, province },
    });
  }
  if (territoire && ['territoires', 'collectivites', 'groupements', 'villages', 'sites', 'missions'].includes(layerKey)) {
    trail.push({
      layerKey: 'territoires',
      label: territoire,
      properties: { ...properties, nom: territoire, territoire, province },
    });
  }
  if (collectivite && ['collectivites', 'groupements', 'villages', 'sites', 'missions'].includes(layerKey)) {
    trail.push({
      layerKey: 'collectivites',
      label: collectivite,
      properties: { ...properties, nom: collectivite, collectivite, territoire, province },
    });
  }
  if (groupement && ['groupements', 'villages', 'sites', 'missions'].includes(layerKey)) {
    trail.push({
      layerKey: 'groupements',
      label: groupement,
      properties: { ...properties, nom: groupement, groupement, collectivite, territoire, province },
    });
  }
  if (localite && ['villages', 'sites', 'missions'].includes(layerKey)) {
    trail.push({
      layerKey: 'villages',
      label: localite,
      properties: { ...properties, nom: localite, localite, groupement, collectivite, territoire, province },
    });
  }
  if (layerKey === 'sites') {
    trail.push({
      layerKey: 'sites',
      label: getMapEntityName(properties, 'sites'),
      properties,
    });
  }
  return trail;
}

function renderMapBreadcrumb() {
  const element = cartographyState.breadcrumbElement;
  if (!element) return;
  const trail = cartographyState.spatialContextTrail?.length > 0
    ? cartographyState.spatialContextTrail
    : [{ layerKey: 'rdc', label: 'RDC', properties: {} }];
  element.innerHTML = trail.map((item, index) => `
    <button type="button" data-breadcrumb-index="${index}" ${index === trail.length - 1 ? 'aria-current="location"' : ''}>${escapeHtml(item.label)}</button>
  `).join('<span>&gt;</span>');
  element.querySelectorAll('button[data-breadcrumb-index]').forEach((button) => {
    button.addEventListener('click', () => {
      const index = Number(button.dataset.breadcrumbIndex);
      if (index === 0) resetMapToNationalView();
    });
  });
}

function renderNationalMapBreadcrumb() {
  const element = nationalMapState.breadcrumbElement;
  if (!element) return;
  const trail = nationalMapState.spatialContextTrail.length > 0
    ? nationalMapState.spatialContextTrail
    : [{ layerKey: 'rdc', label: 'RDC', properties: {} }];
  element.innerHTML = trail.map((item, index) => `
    <button type="button" data-national-breadcrumb-index="${index}" ${index === trail.length - 1 ? 'aria-current="location"' : ''}>${escapeHtml(item.label)}</button>
  `).join('<span>&gt;</span>');
  element.querySelectorAll('button[data-national-breadcrumb-index]').forEach((button) => {
    button.addEventListener('click', () => navigateNationalMapBreadcrumb(Number(button.dataset.nationalBreadcrumbIndex)));
  });
}

function navigateNationalMapBreadcrumb(index) {
  const item = nationalMapState.spatialContextTrail[index];
  if (!item || item.layerKey === 'rdc') {
    resetDashboardNationalView();
    return;
  }
  nationalMapState.spatialContext = {
    level: item.layerKey,
    layerKey: item.layerKey,
    featureId: getFeatureId(item.properties, item.layerKey),
    properties: item.properties,
    feature: null,
  };
  nationalMapState.spatialContextTrail = nationalMapState.spatialContextTrail.slice(0, index + 1);
  renderNationalContextMap();
  renderNationalMapBreadcrumb();
}

function getPrimaryVisibleBusinessLayer(preferredLayer = '') {
  if (preferredLayer && cartographyState.map?.hasLayer(cartographyState.layers[preferredLayer])) return preferredLayer;
  return FDSU_LAYER_STACK_ORDER.find((layerKey) => layerKey !== 'rdcBoundary' && cartographyState.map?.hasLayer(cartographyState.layers[layerKey])) || '';
}

function renderSynchronizedLayerList(preferredLayer = '') {
  const element = cartographyState.synchronizedListElement;
  if (!element) return;

  const visibleLayers = preferredLayer
    ? [preferredLayer]
    : FDSU_LAYER_STACK_ORDER.filter((layerKey) => {
      if (layerKey === 'rdcBoundary') return false;
      return cartographyState.map?.hasLayer(cartographyState.layers[layerKey]);
    });

  if (visibleLayers.length === 0) {
    element.innerHTML = '<p class="zone-detail-empty">Activez une couche pour afficher la liste synchronisée.</p>';
    return;
  }

  const rows = [];
  const searchTerm = String(cartographyState.mapSearchTerm || '').trim().toLowerCase();
  visibleLayers.forEach((layerKey) => {
    asArray(cartographyState.features[layerKey]).forEach((feature) => {
      const properties = feature.properties || {};
      const label = getFeatureProperty(properties, ['nom', 'name', 'libelle']);
      const type = getFeatureProperty(properties, ['type', 'niveau', 'type_localite']);
      const haystack = `${label} ${type}`.toLowerCase();
      if (searchTerm && !haystack.includes(searchTerm)) return;
      rows.push({
        layerKey,
        feature,
        featureId: getFeatureId(properties, layerKey),
        label,
        type,
      });
    });
  });

  if (rows.length === 0) {
    element.innerHTML = searchTerm
      ? '<p class="zone-detail-empty">Aucune entité ne correspond à la recherche.</p>'
      : '<p class="zone-detail-empty">Aucune entité disponible pour les couches actives.</p>';
    return;
  }

  const headerLabel = visibleLayers.length === 1
    ? getLayerDisplayLabel(visibleLayers[0])
    : 'Couches actives';

  element.innerHTML = `
    <div class="sync-list-header">
      <span>${escapeHtml(headerLabel)}</span>
      <strong>${rows.length}</strong>
    </div>
    <div class="sync-list-body">
      ${rows.slice(0, 200).map((row) => `
        <button type="button" class="sync-list-item" data-layer="${escapeHtml(row.layerKey)}" data-feature-id="${escapeHtml(row.featureId)}">
          <span>${escapeHtml(row.label)}</span>
          <small>${escapeHtml(row.type)}</small>
        </button>
      `).join('')}
    </div>
  `;
  element.querySelectorAll('.sync-list-item').forEach((button) => {
    button.addEventListener('mouseenter', () => highlightFeatureFromList(button.dataset.layer, button.dataset.featureId));
    button.addEventListener('mouseleave', () => clearFeatureHighlightFromList(button.dataset.layer, button.dataset.featureId));
    button.addEventListener('click', () => focusAttributeFeature(button.dataset.layer, button.dataset.featureId));
    button.addEventListener('dblclick', () => {
      const feature = cartographyState.features[button.dataset.layer]?.find((candidate) => getFeatureId(candidate.properties, button.dataset.layer) === button.dataset.featureId);
      openEntityProfile(button.dataset.layer, feature?.properties || {}, feature);
    });
  });
}

function renderNationalSynchronizedList(preferredLayer = '') {
  const element = nationalMapState.synchronizedListElement;
  if (!element) return;

  const context = nationalMapState.spatialContext;
  const listLayers = preferredLayer && getHierarchyListLayers(context).includes(preferredLayer)
    ? [preferredLayer]
    : getHierarchyListLayers(context);

  const rows = [];
  listLayers.forEach((layerKey) => {
    asArray(nationalMapState.features[layerKey]).forEach((feature) => {
      const properties = feature.properties || {};
      if (!isWithinHierarchyContext(layerKey, properties)) return;
      rows.push({
        layerKey,
        feature,
        featureId: getFeatureId(properties, layerKey),
        label: getFeatureProperty(properties, ['nom', 'name', 'libelle']),
        type: getFeatureProperty(properties, ['type', 'niveau', 'type_localite']),
      });
    });
  });

  if (rows.length === 0) {
    element.innerHTML = '<p class="zone-detail-empty">Aucune subdivision disponible pour ce niveau.</p>';
    return;
  }

  const headerLabel = listLayers.length === 1
    ? getLayerDisplayLabel(listLayers[0])
    : 'Subdivisions';

  element.innerHTML = `
    <div class="sync-list-header">
      <span>${escapeHtml(headerLabel)}</span>
      <strong>${rows.length}</strong>
    </div>
    <div class="sync-list-body">
      ${rows.slice(0, 200).map((row) => `
        <button type="button" class="sync-list-item" data-layer="${escapeHtml(row.layerKey)}" data-feature-id="${escapeHtml(row.featureId)}">
          <span>${escapeHtml(row.label)}</span>
          <small>${escapeHtml(row.type)}</small>
        </button>
      `).join('')}
    </div>
  `;
  element.querySelectorAll('.sync-list-item').forEach((button) => {
    button.addEventListener('click', () => focusNationalMapFeature(button.dataset.layer, button.dataset.featureId));
  });
}

function highlightFeatureFromList(layerKey, featureId) {
  const layer = cartographyState.featureLayers[layerKey]?.[featureId];
  const feature = cartographyState.features[layerKey]?.find((candidate) => getFeatureId(candidate.properties, layerKey) === featureId);
  if (layer && feature) highlightMapFeature(layerKey, feature, layer);
}

function clearFeatureHighlightFromList(layerKey, featureId) {
  const layer = cartographyState.featureLayers[layerKey]?.[featureId];
  const feature = cartographyState.features[layerKey]?.find((candidate) => getFeatureId(candidate.properties, layerKey) === featureId);
  if (layer && feature && cartographyState.selectedLayer !== layer) resetHoverMapFeature(layerKey, feature, layer);
}

function highlightSynchronizedListRow(layerKey, featureId) {
  if (!cartographyState.synchronizedListElement) return;
  cartographyState.synchronizedListElement.querySelectorAll('.sync-list-item').forEach((item) => {
    item.classList.toggle('is-hovered', item.dataset.layer === layerKey && item.dataset.featureId === featureId);
  });
}

function fitMapToFeatureLayer(layer) {
  if (!cartographyState.map || !layer) return;
  if (layer.getBounds) {
    const bounds = layer.getBounds();
    if (bounds.isValid()) {
      cartographyState.map.fitBounds(bounds, { padding: [36, 36] });
      return;
    }
  }
  if (layer.getLatLng) {
    cartographyState.map.setView(layer.getLatLng(), Math.max(cartographyState.map.getZoom(), 10));
  }
}

function enrichFeatureDetailsFromApi(feature, layerKey) {
  if (LOCAL_JSON_MODE) return;
  const properties = feature?.properties || {};
  const entityId = properties.id || properties.canonical_id || properties.code;
  if (!entityId) return;
  fetchJson(`/entities/${getApiLayerName(layerKey)}/${entityId}`).then((entity) => {
    if (!entity || Object.keys(entity).length === 0) return;
    renderTerritorialFeatureDetails({ ...properties, ...entity }, layerKey);
  });
}

function renderFeatureDetails(feature, layerKey) {
  if (!cartographyState.infoElement) return;
  openCartographyDrawer('info');

  const properties = feature?.properties || {};
  if (['provinces', 'villages', 'collectivites', 'groupements', 'territoires', 'sites', 'missions'].includes(layerKey)) {
    renderTerritorialFeatureDetails(properties, layerKey);
    return;
  }

  const code = getFeatureProperty(properties, ['code', 'zone', 'zone_code', 'zoneCode']);
  const name = getFeatureProperty(properties, ['nom', 'name', 'libelle']);
  const provinceCount = getFeatureProperty(properties, ['nb_provinces', 'nombre_provinces', 'province_count']);
  const description = getFeatureProperty(properties, ['description', 'desc', 'commentaire']);

  const attributes = Object.entries(properties)
    .filter(([, value]) => value !== null && value !== undefined && String(value).trim() !== '')
    .map(([key, value]) => `<div class="detail-row"><span>${escapeHtml(key)}</span><strong>${escapeHtml(formatAttributeValue(value))}</strong></div>`)
    .join('');
  const contextStats = computeSpatialContextStats(layerKey, properties);

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
    ${renderContextStatsHtml(contextStats)}
    ${renderSmartDecisionPanel(properties)}
    <button type="button" class="map-profile-button" data-profile-layer="${escapeHtml(layerKey)}" data-profile-id="${escapeHtml(getFeatureId(properties, layerKey))}">Ouvrir la fiche complète</button>
    <div class="detail-attributes">
      <p class="zone-detail-label">Attributs extraits</p>
      ${attributes || '<p class="zone-detail-empty">Non disponible</p>'}
    </div>
  `;
  bindCartographyProfileButtons();
}

function renderTerritorialFeatureDetails(properties, layerKey) {
  const layerLabels = {
    provinces: 'Province',
    collectivites: 'Collectivité',
    groupements: 'Groupement',
    territoires: 'Territoire',
    villages: 'Localité',
    sites: 'Site FDSU',
    missions: 'Mission',
  };

  const rows = [
    ['Nom', getFeatureProperty(properties, ['nom', 'name', 'libelle'])],
    ['Type administratif', getFeatureProperty(properties, ['type', 'type_localite', 'niveau'])],
    ['Zone FDSU', getFeatureProperty(properties, ['zone_fdsu', 'zone'])],
    ['Province', getFeatureProperty(properties, ['province'])],
    ['Territoire', getFeatureProperty(properties, ['territoire'])],
    ['Collectivité', getFeatureProperty(properties, ['collectivite', 'collectivité'])],
    ['Groupement', getFeatureProperty(properties, ['groupement'])],
    ['Localité', getFeatureProperty(properties, ['localite'])],
    ['Source', getFeatureProperty(properties, ['source'])],
    ['Score qualité', getFeatureProperty(properties, ['qualite', 'qualité', 'quality'])],
    ['Statut', getFeatureProperty(properties, ['statut'])],
    ['Coordonnées GPS', formatGpsCoordinates(properties)],
    ['Observations', getFeatureProperty(properties, ['observations', 'description'])],
    ['Anomalies éventuelles', getFeatureProperty(properties, ['anomalies'])],
  ];

  const contextStats = computeSpatialContextStats(layerKey, properties);

  cartographyState.infoElement.innerHTML = `
    <p class="zone-detail-label">Type de couche</p>
    <p class="zone-detail-value">${escapeHtml(layerLabels[layerKey] || layerKey)}</p>
    ${renderContextStatsHtml(contextStats)}
    ${renderSmartDecisionPanel(properties)}
    <button type="button" class="map-profile-button" data-profile-layer="${escapeHtml(layerKey)}" data-profile-id="${escapeHtml(getFeatureId(properties, layerKey))}">Ouvrir la fiche complète</button>
    <div class="detail-attributes">
      ${rows.map(([label, value]) => `<div class="detail-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(formatAttributeValue(value))}</strong></div>`).join('')}
    </div>
  `;
  bindCartographyProfileButtons();
}

function computeSpatialContextStats(layerKey, properties = {}) {
  const context = {
    layerKey,
    featureId: getFeatureId(properties, layerKey),
    properties,
  };
  const countLayer = (targetLayer) => asArray(cartographyState.features[targetLayer])
    .filter((feature) => isWithinHierarchyContext(targetLayer, feature.properties || {}, context)).length;
  const subdivisions = getChildLayers(layerKey).reduce((total, childLayer) => total + countLayer(childLayer), 0);
  return {
    subdivisions,
    territoires: countLayer('territoires'),
    collectivites: countLayer('collectivites'),
    groupements: countLayer('groupements'),
    localites: countLayer('villages'),
    sites: countLayer('sites'),
    missions: countLayer('missions'),
    population: getFeatureProperty(properties, ['population', 'population_totale', 'pop']),
    superficie: getFeatureProperty(properties, ['superficie', 'area_sqkm', 'surface', 'surface_km2']),
    chefLieu: getFeatureProperty(properties, ['chef_lieu', 'cheflieu', 'chefLieu']),
    zoneFdsu: getFeatureProperty(properties, ['zone_nom', 'zone_fdsu', 'zone']),
  };
}

function renderContextStatsHtml(stats) {
  const rows = [
    ['Subdivisions', stats.subdivisions],
    ['Territoires', stats.territoires],
    ['Collectivités', stats.collectivites],
    ['Groupements', stats.groupements],
    ['Localités', stats.localites],
    ['Sites FDSU', stats.sites],
    ['Missions', stats.missions],
    ['Population', stats.population],
    ['Superficie', stats.superficie],
    ['Chef-lieu', stats.chefLieu],
    ['Zone FDSU', stats.zoneFdsu],
  ];
  return `
    <div class="context-stats">
      ${rows.map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(formatAttributeValue(value))}</strong></div>`).join('')}
    </div>
  `;
}

function renderSmartDecisionPanel(properties = {}) {
  const rows = [
    ['Activités économiques', getFeatureProperty(properties, ['activites_economiques', 'economic_activities'])],
    ['Défis', getFeatureProperty(properties, ['defis', 'challenges'])],
    ['Potentiel', getFeatureProperty(properties, ['potentiel', 'potential', 'potentiel_fdsu'])],
    ['Sources', getFeatureProperty(properties, ['source'])],
    ['Documents', getFeatureProperty(properties, ['documents'])],
  ];
  return `
    <div class="smart-side-panel">
      ${rows.map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(formatAttributeValue(value))}</strong></div>`).join('')}
    </div>
  `;
}

function bindCartographyProfileButtons() {
  cartographyState.infoElement?.querySelectorAll('.map-profile-button').forEach((button) => {
    button.addEventListener('click', () => {
      const layerKey = button.dataset.profileLayer;
      const featureId = button.dataset.profileId;
      const feature = cartographyState.features[layerKey]?.find((candidate) => getFeatureId(candidate.properties, layerKey) === featureId);
      openEntityProfile(layerKey, feature?.properties || {}, feature);
    });
  });
}

function getFeatureId(properties, layerKey) {
  return String(properties?.canonical_id || properties?.id || properties?.code || `${layerKey}-${properties?.nom || properties?.name || 'sans_nom'}-${properties?.province || ''}-${properties?.territoire || ''}`);
}

function formatGpsCoordinates(properties) {
  const latitude = properties?.latitude;
  const longitude = properties?.longitude;
  if (latitude === '' || longitude === '' || latitude === undefined || longitude === undefined) {
    return 'Non disponible';
  }
  return `${Number(latitude).toFixed(6)}, ${Number(longitude).toFixed(6)}`;
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

function updateLayerAvailabilityMessage(fallbackMessage = '') {
  const attributeOnlyLayers = Object.entries(cartographyState.layerStatus)
    .filter(([, status]) => status === 'attributes-only')
    .map(([layerKey]) => WEB_SIG_LAYER_DEFINITIONS[layerKey]?.label || layerKey);

  if (attributeOnlyLayers.length > 0) {
    showZonesMessage(`Couche disponible en attributaire uniquement, géométrie manquante : ${attributeOnlyLayers.join(', ')}.`);
    return;
  }

  showZonesMessage(fallbackMessage || '');
}

function escapeHtml(value) {
  return String(value ?? '')
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
  if (layerList.dataset.bound === 'true') return;
  layerList.dataset.bound = 'true';

  layerList.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
    checkbox.addEventListener('change', () => {
      const layerKey = checkbox.dataset.layer;
      if (!isManagedCartographyLayer(layerKey)) {
        checkbox.checked = false;
        return;
      }
      setCartographyLayerVisible(layerKey, checkbox.checked, checkbox);
    });
  });
}

function setupLeafletLayerControlSync() {
  if (!cartographyState.map) return;
  cartographyState.map.on('overlayadd overlayremove', (event) => {
    const layerKey = getLayerKeyFromLeafletLayer(event.layer);
    if (!layerKey || layerKey === 'rdcBoundary') return;
    const checkbox = document.querySelector(`input[data-layer="${layerKey}"]`);
    if (checkbox) checkbox.checked = event.type === 'overlayadd';
    refreshCartographicLayerPresentation();
    renderSynchronizedLayerList(layerKey);
  });
}

function getLayerKeyFromLeafletLayer(targetLayer) {
  return Object.entries(cartographyState.layers).find(([, layer]) => layer === targetLayer)?.[0] || '';
}

function refreshCartographicLayerPresentation() {
  if (!cartographyState.map) return;
  const zonesLayer = cartographyState.layers.zones;
  if (zonesLayer?.setStyle) zonesLayer.setStyle(styleZoneFeature);
  FDSU_LAYER_STACK_ORDER.forEach((layerKey) => {
    const layer = cartographyState.layers[layerKey];
    if (layer && cartographyState.map.hasLayer(layer) && layer.bringToFront) {
      layer.bringToFront();
    }
  });
  if (cartographyState.selectedLayer?.bringToFront) cartographyState.selectedLayer.bringToFront();
}

function fitLayerBounds(layer) {
  if (!cartographyState.map || !layer?.getBounds) return;
  const bounds = layer.getBounds();
  if (bounds.isValid()) {
    cartographyState.map.fitBounds(bounds, { padding: [20, 20] });
  }
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

  for (const layerKey of FDSU_LAYER_STACK_ORDER) {
    if (cartographyState.spatialContext && layerKey === 'rdcBoundary') continue;
    const layer = cartographyState.layers[layerKey];
    if (layer && cartographyState.map.hasLayer(layer) && layer.getBounds) {
      const bounds = layer.getBounds();
      if (bounds.isValid()) {
        cartographyState.map.fitBounds(bounds, { padding: [20, 20] });
        return;
      }
    }
  }

  fitMapToRdc();
}

function fitMapToRdc() {
  if (!cartographyState.map) return;
  const bounds = L.latLngBounds(RDC_MAP_BOUNDS);
  cartographyState.map.fitBounds(bounds, { padding: [20, 20] });
}

function fitNationalMapBounds(layer) {
  if (!nationalMapState.map || !layer?.getBounds) return;
  const bounds = layer.getBounds();
  if (bounds.isValid()) {
    nationalMapState.map.fitBounds(bounds, { padding: [16, 16] });
  }
}

function fitNationalMapToRdc() {
  if (!nationalMapState.map || typeof L === 'undefined') return;
  nationalMapState.map.fitBounds(L.latLngBounds(RDC_MAP_BOUNDS), { padding: [16, 16] });
}

function fitNationalMapToFeatureLayer(layer) {
  if (!nationalMapState.map || !layer) return;
  if (layer.getBounds) {
    const bounds = layer.getBounds();
    if (bounds.isValid()) {
      nationalMapState.map.fitBounds(bounds, { padding: [20, 20] });
      return;
    }
  }
  if (layer.getLatLng) {
    nationalMapState.map.setView(layer.getLatLng(), Math.max(nationalMapState.map.getZoom(), 8));
  }
}

function refreshNationalMapLayerPresentation() {
  if (!nationalMapState.map) return;
  FDSU_LAYER_STACK_ORDER.forEach((layerKey) => {
    const layer = nationalMapState.layers[layerKey];
    if (layer && nationalMapState.map.hasLayer(layer) && layer.bringToFront) {
      layer.bringToFront();
    }
  });
}

function onNationalGeoEachFeature(feature, layer, layerKey) {
  if (!layer) return;
  const properties = feature?.properties || {};
  const featureId = getFeatureId(properties, layerKey);
  if (!nationalMapState.featureLayers[layerKey]) nationalMapState.featureLayers[layerKey] = {};
  nationalMapState.featureLayers[layerKey][featureId] = layer;

  if (layer.bindPopup) {
    layer.bindPopup(`
      <strong>${escapeHtml(getFeatureProperty(properties, ['nom', 'name', 'libelle']))}</strong><br>
      ${escapeHtml(getFeatureProperty(properties, ['type', 'niveau']))}
    `);
  }

  renderSmartTooltip(feature, layer, layerKey);

  layer.on('click', (event) => {
    if (event?.originalEvent && typeof L !== 'undefined') {
      L.DomEvent.stopPropagation(event.originalEvent);
    }
    activateNationalSpatialContext(layerKey, properties, feature);
    if (layer.openPopup) layer.openPopup();
  });
}

function loadNationalMapLayer(layerKey) {
  if (!WEB_SIG_LAYER_DEFINITIONS[layerKey]) return Promise.resolve([]);
  const definition = WEB_SIG_LAYER_DEFINITIONS[layerKey];
  return fetchPlatformLayerData(layerKey)
    .then((items) => {
      const filteredItems = asArray(items).filter((item) => !definition.filter || definition.filter(item));
      const featureCollection = buildFeatureCollection(filteredItems, layerKey);
      const layer = nationalMapState.layers[layerKey];
      nationalMapState.data[layerKey] = filteredItems;
      nationalMapState.features[layerKey] = featureCollection.features;
      nationalMapState.featureLayers[layerKey] = {};
      if (layer && featureCollection.features.length > 0) {
        nationalMapState.layerStatus[layerKey] = true;
      } else {
        nationalMapState.layerStatus[layerKey] = filteredItems.length > 0 ? 'attributes-only' : false;
      }
      return filteredItems;
    })
    .catch(() => {
      nationalMapState.data[layerKey] = [];
      nationalMapState.features[layerKey] = [];
      nationalMapState.layerStatus[layerKey] = false;
      return [];
    });
}

function loadNationalMapBoundary() {
  if (!nationalMapState.map || typeof L === 'undefined') return Promise.resolve();
  return fetchJson('/geodata/rdc_boundary.geojson')
    .then((geojson) => {
      const boundary = nationalMapState.layers.rdcBoundary;
      if (!boundary || !geojson?.features?.length) return;
      boundary.clearLayers();
      boundary.addData(geojson);
      boundary.addTo(nationalMapState.map);
      nationalMapState.layerStatus.rdcBoundary = true;
    })
    .catch(() => {
      nationalMapState.layerStatus.rdcBoundary = false;
    });
}

function focusNationalMapFeature(layerKey, featureId) {
  const featureLayer = nationalMapState.featureLayers[layerKey]?.[featureId];
  const feature = nationalMapState.features[layerKey]?.find((candidate) => getFeatureId(candidate.properties, layerKey) === featureId);
  if (!featureLayer || !feature) return;
  activateNationalSpatialContext(layerKey, feature.properties || {}, feature);
  fitNationalMapToFeatureLayer(featureLayer);
}

function initializeNationalMapModule() {
  if (typeof L === 'undefined') return;
  const mapElement = document.querySelector('#dashboard-national-map');
  if (!mapElement) return;

  nationalMapState.breadcrumbElement = document.querySelector('#dashboard-map-breadcrumb');
  nationalMapState.synchronizedListElement = document.querySelector('#dashboard-map-synchronized-list');
  nationalMapState.messageElement = document.querySelector('#dashboard-map-message');
  setupNationalMapResizeObserver(mapElement);

  if (!nationalMapState.map) {
    nationalMapState.map = L.map(mapElement, {
      zoomControl: true,
      attributionControl: true,
      minZoom: 4,
      maxZoom: 14,
    }).setView([-2.8, 23.5], 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(nationalMapState.map);

    nationalMapState.layers = {
      rdcBoundary: L.geoJSON(null, { style: styleRdcBoundaryFeature }),
      provinces: L.geoJSON(null, { style: styleProvinceFeature, onEachFeature: (feature, layer) => onNationalGeoEachFeature(feature, layer, 'provinces') }),
      territoires: L.geoJSON(null, { style: styleTerritoryFeature, onEachFeature: (feature, layer) => onNationalGeoEachFeature(feature, layer, 'territoires') }),
      collectivites: L.geoJSON(null, { style: styleCollectivitesFeature, onEachFeature: (feature, layer) => onNationalGeoEachFeature(feature, layer, 'collectivites') }),
      groupements: L.geoJSON(null, {
        pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#7c3aed', '#a78bfa'),
        onEachFeature: (feature, layer) => onNationalGeoEachFeature(feature, layer, 'groupements'),
      }),
      villages: L.geoJSON(null, {
        pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#0f766e', '#14b8a6'),
        onEachFeature: (feature, layer) => onNationalGeoEachFeature(feature, layer, 'villages'),
      }),
      sites: L.geoJSON(null, {
        pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#b45309', '#f59e0b'),
        onEachFeature: (feature, layer) => onNationalGeoEachFeature(feature, layer, 'sites'),
      }),
      missions: L.geoJSON(null, {
        pointToLayer: (_feature, latlng) => makePointMarker(latlng, '#be123c', '#fb7185'),
        onEachFeature: (feature, layer) => onNationalGeoEachFeature(feature, layer, 'missions'),
      }),
    };

    document.querySelector('#dashboard-map-context-back')?.addEventListener('click', goBackNationalContext);
    document.querySelector('#dashboard-map-reset-national')?.addEventListener('click', resetDashboardNationalView);
  }

  const bootstrap = () => {
    loadNationalMapBoundary().finally(() => {
      loadNationalMapLayer('provinces').finally(() => {
        applyDashboardNationalHierarchyView();
        window.setTimeout(() => nationalMapState.map?.invalidateSize(), 0);
      });
    });
  };

  if (nationalMapState.initialized) {
    window.setTimeout(() => nationalMapState.map?.invalidateSize(), 0);
    return;
  }

  nationalMapState.initialized = true;
  bootstrap();
}

function setupNationalMapResizeObserver(mapElement) {
  if (!mapElement || nationalMapState.resizeObserver) return;

  const invalidate = () => {
    if (nationalMapState.map) {
      window.requestAnimationFrame(() => nationalMapState.map.invalidateSize());
    }
  };

  if (typeof ResizeObserver !== 'undefined') {
    nationalMapState.resizeObserver = new ResizeObserver(invalidate);
    nationalMapState.resizeObserver.observe(mapElement);
  }

  if (nationalMapState.windowResizeBound !== true) {
    nationalMapState.windowResizeBound = true;
    window.addEventListener('resize', invalidate);
  }
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

  const registry = governanceState.report?.registryCounters || {};
  const groupements = registry.groupements || {};
  const localites = registry.localites || {};
  const kpis = [
    { label: 'Provinces', value: formatGovernanceMetric(registry.provinces?.nombre ?? 26) },
    { label: 'Collectivités', value: formatGovernanceMetric(registry.collectivites?.nombre ?? 733) },
    { label: 'Groupements', value: `${formatGovernanceMetric(groupements.trouve ?? groupements.nombre ?? 1681)} / ${formatGovernanceMetric(groupements.attendu_officiel ?? 6053)}` },
    { label: 'Localités', value: formatGovernanceMetric(localites.nombre) },
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
    .map((action) => `<button type="button" class="governance-action-button" data-governance-action="${escapeHtml(action.toLowerCase())}">${escapeHtml(action)}</button>`)
    .join('');
  governanceElements.actions.querySelectorAll('[data-governance-action]').forEach((button) => {
    button.addEventListener('click', () => handleGovernanceAction(button.dataset.governanceAction));
  });
}

function handleGovernanceAction(action) {
  if (action === 'importer') {
    navigateTo('import');
    window.setTimeout(() => {
      document.querySelector('#import-entity')?.focus();
      showZonesMessage('Import ouvert avec contexte: référentiel administratif.');
    }, 80);
    return;
  }
  if (action === 'comparer') {
    showGovernanceActionPanel('Comparaison référentiel', 'Aucun fichier importé pour comparaison dans cette session.');
    return;
  }
  if (action === 'valider') {
    governanceState.activeTab = 'validation';
    governanceState.page = 1;
    renderGovernanceTabs();
    updateGovernanceStatusFilter();
    renderGovernanceTable();
    renderGovernanceDetailPanel();
    showGovernanceActionPanel('Validation des anomalies', 'Panneau de validation ouvert. Sélectionnez une anomalie pour consulter sa fiche.');
    return;
  }
  if (action === 'publier') {
    showGovernanceActionPanel('Publication', 'Publication disponible après validation des anomalies.');
    return;
  }
  if (action === 'exporter') {
    const format = window.prompt('Format export référentiel: CSV, Excel, JSON, GeoJSON, KML ou KMZ', 'CSV');
    exportGovernanceRows(format);
  }
}

function exportGovernanceRows(format = 'CSV') {
  const rows = getGovernanceFilteredRows();
  const normalizedFormat = String(format || 'CSV').trim().toLowerCase();
  const baseName = `sig_fdsu_referentiel_${governanceState.activeTab}_${getExportDateStamp()}`;
  if (normalizedFormat === 'json') {
    downloadTextFile(`${baseName}.json`, JSON.stringify(rows, null, 2), 'application/json');
  } else if (normalizedFormat === 'excel' || normalizedFormat === 'xlsx') {
    downloadTextFile(`${baseName}.xls`, buildHtmlRowsDocument(rows), 'application/vnd.ms-excel;charset=utf-8');
  } else if (normalizedFormat === 'geojson') {
    downloadTextFile(`${baseName}.geojson`, JSON.stringify({ type: 'FeatureCollection', features: [] }, null, 2), 'application/geo+json');
  } else if (normalizedFormat === 'kml' || normalizedFormat === 'kmz') {
    downloadTextFile(`${baseName}.kml`, buildKmlRows(rows), 'application/vnd.google-earth.kml+xml');
  } else {
    downloadTextFile(`${baseName}.csv`, toCsv(rows), 'text/csv;charset=utf-8');
  }
  showGovernanceActionPanel('Export référentiel', `Export ${normalizedFormat.toUpperCase()} généré pour le filtre actif.`);
}

function buildHtmlRowsDocument(rows) {
  const columns = [...new Set(asArray(rows).flatMap((row) => Object.keys(row || {})))];
  const header = columns.map((column) => `<th>${escapeHtml(formatDetailLabel(column))}</th>`).join('');
  const body = asArray(rows).map((row) => `<tr>${columns.map((column) => `<td>${escapeHtml(formatAttributeValue(row[column]))}</td>`).join('')}</tr>`).join('');
  return `<html><head><meta charset="utf-8"></head><body><table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table></body></html>`;
}

function buildKmlRows(rows) {
  const placemarks = rows.map((row) => `
    <Placemark>
      <name>${escapeXml(row.nom || row.objet || row.referentiel || row.source || 'Référentiel')}</name>
      <description>${escapeXml(JSON.stringify(row))}</description>
    </Placemark>
  `).join('');
  return `<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>${placemarks}</Document></kml>`;
}

function showGovernanceActionPanel(title, message) {
  if (!governanceElements.detailTitle || !governanceElements.detailBody) return;
  governanceElements.detailTitle.textContent = title;
  governanceElements.detailBody.innerHTML = `<div class="empty-detail">${escapeHtml(message)}</div>`;
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
  loadNationalReferentialJsonData()
    .then((payload) => {
      const report = buildNationalReferentialReportFromJson(payload);

      governanceState.report = report;
      governanceState.jsonSources = payload.sources;
      governanceState.normalization = report.normalization;
      governanceState.dataByTab.referentiels = report.referentielRows;
      governanceState.dataByTab.sources = report.sourceRows;
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
      setGovernanceViewState('success');
      renderGovernanceTable();
      renderGovernanceDetailPanel();
    })
    .catch(() => {
      governanceState.report = null;
      setGovernanceViewState('error');
    });
}

const NATIONAL_REFERENTIAL_JSON_FILES = {
  registry: 'national_counter_registry.json',
  provinceReferential: 'province_official/province_referential_official.json',
  provinceFactSheets: 'province_official/province_fact_sheets.json',
  provinceQuality: 'province_official/province_quality_report.json',
  territoryHierarchy: 'territory_hierarchy/territoires_hierarchie_kmz.report.json',
  cityReferential: 'city_official/city_referential_official.json',
  cityFactSheets: 'city_official/city_fact_sheets.json',
  cityQuality: 'city_official/city_quality_report.json',
  collectivityReferential: 'collectivity_official/collectivity_referential_official.json',
  collectivityFactSheets: 'collectivity_official/collectivity_fact_sheets.json',
  collectivityQuality: 'collectivity_official/collectivity_quality_report.json',
  territoryCollectivityIndex: 'collectivity_official/territory_collectivity_index.json',
  provinceCollectivityIndex: 'collectivity_official/province_collectivity_index.json',
  groupementReferential: 'groupement_official/groupement_referential_official.json',
  groupementQuality: 'groupement_official/groupement_quality_report.json',
  groupementCoverageAudit: 'groupement_official/groupement_coverage_audit.json',
  collectivityGroupementIndex: 'groupement_official/collectivity_groupement_index.json',
  territoryGroupementIndex: 'groupement_official/territory_groupement_index.json',
  provinceGroupementIndex: 'groupement_official/province_groupement_index.json',
  localityReferential: 'locality_official/locality_referential_official.json',
  localityFactSheets: 'locality_official/locality_fact_sheets.json',
  localityQuality: 'locality_official/locality_quality_report.json',
  provinceLocalityIndex: 'locality_official/province_locality_index.json',
  territoryLocalityIndex: 'locality_official/territory_locality_index.json',
  collectivityLocalityIndex: 'locality_official/collectivity_locality_index.json',
  groupementLocalityIndex: 'locality_official/groupement_locality_index.json',
};

function loadNationalReferentialJsonData() {
  const entries = Object.entries(NATIONAL_REFERENTIAL_JSON_FILES);
  return Promise.all(entries.map(([key, path]) => fetchReportJson(path).then((result) => [key, result]))).then((results) => {
    const payload = {};
    const sources = {};
    results.forEach(([key, result]) => {
      payload[key] = result.data;
      sources[key] = {
        path: result.path,
        available: result.available,
        label: result.available ? 'Chargé' : 'Donnée non disponible',
      };
    });
    payload.sources = sources;
    return payload;
  });
}

function setupThematicControls() {
  const select = document.querySelector('#thematic-layer-select');
  if (!select || select.dataset.bound === 'true') return;
  select.dataset.bound = 'true';
  select.addEventListener('change', () => {
    cartographyState.thematicMode = select.value;
    applyThematicStyles();
    showZonesMessage(select.value ? `Carte thématique active : ${select.options[select.selectedIndex].textContent}.` : '');
  });
}

function applyThematicStyles() {
  Object.entries(cartographyState.layers).forEach(([layerKey, layer]) => {
    if (!layer?.eachLayer) return;
    layer.eachLayer((leafletLayer) => {
      const properties = leafletLayer.feature?.properties || {};
      const style = getThematicStyle(properties, layerKey);
      if (leafletLayer.setStyle) leafletLayer.setStyle(style);
    });
  });
}

function getThematicStyle(properties, layerKey) {
  if (!cartographyState.thematicMode || cartographyState.thematicMode === 'administrative') {
    if (layerKey === 'provinces') return styleProvinceFeature();
    if (layerKey === 'territoires') return styleTerritoryFeature();
    if (layerKey === 'collectivites') return styleCollectivitesFeature();
    if (layerKey === 'zones') return styleZoneFeature({ properties });
    return { color: '#0f766e', fillColor: '#14b8a6', fillOpacity: 0.72, weight: 1 };
  }
  const text = buildSearchText(properties);
  const thematicColors = {
    economic: text.includes('commerce') ? '#f97316' : '#16a34a',
    connectivity: text.includes('faible') || text.includes('absence') ? '#dc2626' : '#2563eb',
    ccnPriority: text.includes('priorit') ? '#7c3aed' : '#0f766e',
    dataQuality: text.includes('anomal') || text.includes('incomplet') ? '#f59e0b' : '#16a34a',
    decision: text.includes('urgent') || text.includes('priorit') ? '#be123c' : '#0891b2',
    agriculture: text.includes('agriculture') ? '#22c55e' : '#84cc16',
    mining: text.includes('mine') || text.includes('minier') ? '#a855f7' : '#64748b',
    network: text.includes('faible') || text.includes('absence') ? '#dc2626' : '#2563eb',
    challenges: text.includes('critique') || text.includes('insécurité') || text.includes('insecurite') ? '#b91c1c' : '#f59e0b',
    infrastructure: text.includes('route') || text.includes('port') || text.includes('aéroport') ? '#0891b2' : '#64748b',
    fdsu: text.includes('priorité') || text.includes('priorite') ? '#7c3aed' : '#0f766e',
  };
  const color = thematicColors[cartographyState.thematicMode] || '#0f766e';
  return { color, fillColor: color, fillOpacity: 0.32, weight: 2 };
}

function setupAttributeExplorer() {
  const layerSelect = document.querySelector('#attribute-layer-select');
  const searchInput = document.querySelector('#attribute-search');
  const provinceFilter = document.querySelector('#attribute-province-filter');
  const territoryFilter = document.querySelector('#attribute-territory-filter');
  const prevButton = document.querySelector('#attribute-prev');
  const nextButton = document.querySelector('#attribute-next');

  [layerSelect, searchInput, provinceFilter, territoryFilter].forEach((element) => {
    if (!element || element.dataset.bound === 'true') return;
    element.dataset.bound = 'true';
    element.addEventListener('input', () => {
      if (layerSelect) cartographyState.activeAttributeLayer = layerSelect.value;
      cartographyState.attributePage = 1;
      renderAttributeExplorer();
    });
    element.addEventListener('change', () => {
      if (layerSelect) cartographyState.activeAttributeLayer = layerSelect.value;
      cartographyState.attributePage = 1;
      renderAttributeExplorer();
    });
  });
  if (prevButton && prevButton.dataset.bound !== 'true') {
    prevButton.dataset.bound = 'true';
    prevButton.addEventListener('click', () => {
      cartographyState.attributePage = Math.max(1, cartographyState.attributePage - 1);
      renderAttributeExplorer();
    });
  }
  if (nextButton && nextButton.dataset.bound !== 'true') {
    nextButton.dataset.bound = 'true';
    nextButton.addEventListener('click', () => {
      cartographyState.attributePage += 1;
      renderAttributeExplorer();
    });
  }
}

function renderAttributeExplorer() {
  const tableBody = document.querySelector('#attribute-table-body');
  const totalElement = document.querySelector('#attribute-total');
  const pageInfo = document.querySelector('#attribute-page-info');
  const prevButton = document.querySelector('#attribute-prev');
  const nextButton = document.querySelector('#attribute-next');
  const layerSelect = document.querySelector('#attribute-layer-select');
  const provinceFilter = document.querySelector('#attribute-province-filter');
  const territoryFilter = document.querySelector('#attribute-territory-filter');
  const searchInput = document.querySelector('#attribute-search');
  if (!tableBody) return;

  const layerKey = layerSelect?.value || cartographyState.activeAttributeLayer || 'provinces';
  const rows = asArray(cartographyState.data[layerKey]).map((item) => normalizeAttributeRow(item, layerKey));
  refreshAttributeFilters(rows, provinceFilter, territoryFilter);

  const searchTerm = String(searchInput?.value || '').trim().toLowerCase();
  const provinceValue = provinceFilter?.value || '';
  const territoryValue = territoryFilter?.value || '';
  const filteredRows = rows.filter((row) => {
    const haystack = [row.nom, row.type, row.province, row.territoire, row.collectivite, row.groupement].join(' ').toLowerCase();
    return (!searchTerm || haystack.includes(searchTerm))
      && (!provinceValue || row.province === provinceValue)
      && (!territoryValue || row.territoire === territoryValue);
  }).sort((a, b) => String(a[cartographyState.attributeSortKey] || '').localeCompare(String(b[cartographyState.attributeSortKey] || ''), 'fr'));

  if (totalElement) totalElement.textContent = `${filteredRows.length.toLocaleString('fr-FR')} / ${rows.length.toLocaleString('fr-FR')} éléments`;
  const pageSize = cartographyState.attributePageSize;
  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  cartographyState.attributePage = Math.min(cartographyState.attributePage, totalPages);
  const offset = (cartographyState.attributePage - 1) * pageSize;
  const pageRows = filteredRows.slice(offset, offset + pageSize);
  if (pageInfo) pageInfo.textContent = `Page ${cartographyState.attributePage} / ${totalPages}`;
  if (prevButton) prevButton.disabled = cartographyState.attributePage <= 1;
  if (nextButton) nextButton.disabled = cartographyState.attributePage >= totalPages;
  if (filteredRows.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="6" class="empty-state">Donnée non disponible.</td></tr>';
    return;
  }

  tableBody.innerHTML = pageRows.map((row) => `
    <tr data-layer="${escapeHtml(layerKey)}" data-feature-id="${escapeHtml(row.featureId)}" class="${row.featureId === cartographyState.selectedFeatureId ? 'selected' : ''}">
      <td>${escapeHtml(row.nom)}</td>
      <td>${escapeHtml(row.type)}</td>
      <td>${escapeHtml(row.province || '—')}</td>
      <td>${escapeHtml(row.territoire || '—')}</td>
      <td>${escapeHtml(formatAttributeValue(row.qualite || '—'))}</td>
      <td><button type="button" class="table-action-button" data-action="view-feature">Voir fiche</button></td>
    </tr>
  `).join('');

  tableBody.querySelectorAll('tr[data-feature-id]').forEach((row) => {
    row.addEventListener('click', () => {
      cartographyState.selectedFeatureId = row.dataset.featureId;
      focusAttributeFeature(row.dataset.layer, row.dataset.featureId);
      renderAttributeExplorer();
    });
  });
}

function refreshAttributeFilters(rows, provinceFilter, territoryFilter) {
  updateSelectOptions(provinceFilter, rows.map((row) => row.province).filter(Boolean), 'Toutes les provinces');
  updateSelectOptions(territoryFilter, rows.map((row) => row.territoire).filter(Boolean), 'Tous les territoires');
}

function updateSelectOptions(select, values, emptyLabel) {
  if (!select) return;
  const currentValue = select.value;
  const uniqueValues = [...new Set(values)].sort((a, b) => a.localeCompare(b, 'fr'));
  select.innerHTML = `<option value="">${escapeHtml(emptyLabel)}</option>${uniqueValues.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join('')}`;
  if (uniqueValues.includes(currentValue)) select.value = currentValue;
}

function normalizeAttributeRow(item, layerKey) {
  const feature = buildFeature(item, layerKey);
  const properties = feature?.properties || buildPropertiesFromItem(item, layerKey);
  return {
    featureId: getFeatureId(properties, layerKey),
    properties,
    nom: properties.nom || 'Non renseigné',
    type: properties.type || layerKey,
    province: properties.province || '',
    territoire: properties.territoire || '',
    collectivite: properties.collectivite || '',
    groupement: properties.groupement || '',
    qualite: properties.qualite || '',
  };
}

function buildPropertiesFromItem(item, layerKey) {
  item = enrichFdsuNomenclature(item);
  const metadata = item?.metadata || {};
  const attributes = item?.attributs || {};
  const extendedData = metadata.extended_data || attributes.extended_data || {};
  return {
    layer: layerKey,
    canonical_id: item?.canonical_id || item?.id || item?.code_officiel || '',
    code: item?.code || item?.code_officiel || item?.canonical_id || item?.id || '',
    nom: item?.nom || item?.name || 'Non renseigné',
    type: item?.type_localite || item?.type_collectivite || item?.niveau || extendedData.TYPE || layerKey,
    province: item?.province || '',
    territoire: item?.territoire || '',
    collectivite: item?.collectivité || item?.collectivite || item?.collectivite_parent || '',
    groupement: item?.groupement || '',
    localite: layerKey === 'villages' ? item?.nom || item?.name || '' : '',
    zone_fdsu: item?.zone_fdsu || item?.zone || '',
    zone_nom: item?.zone_nom || getZoneName(item?.zone_fdsu),
    code_province_fdsu: item?.code_province_fdsu || '',
    code_territoire_fdsu: item?.code_territoire_fdsu || '',
    fdsu_codification_format: item?.fdsu_codification_format || FDSU_CODE_FORMAT,
    source: item?.source || item?.source_file || '',
    qualite: item?.qualité ?? item?.qualite ?? item?.quality ?? '',
    statut: item?.statut || '',
    observations: metadata.description || attributes.description || '',
    anomalies: asArray(item?.incoherences || item?.anomalies).join(', '),
    metadata,
    future_profile: item?.future_profile || metadata.future_profile || {},
    geometry: item?.geometry || null,
  };
}

function focusAttributeFeature(layerKey, featureId) {
  const featureLayer = cartographyState.featureLayers[layerKey]?.[featureId];
  const feature = cartographyState.features[layerKey]?.find((candidate) => getFeatureId(candidate.properties, layerKey) === featureId);
  const row = asArray(cartographyState.data[layerKey])
    .map((item) => normalizeAttributeRow(item, layerKey))
    .find((item) => item.featureId === featureId);

  if (featureLayer && cartographyState.map) {
    const layer = cartographyState.layers[layerKey];
    if (layer && !cartographyState.map.hasLayer(layer)) {
      layer.addTo(cartographyState.map);
      const checkbox = document.querySelector(`input[data-layer="${layerKey}"]`);
      if (checkbox) checkbox.checked = true;
      refreshCartographicLayerPresentation();
    }
    if (featureLayer.getBounds) {
      fitLayerBounds(featureLayer);
    } else if (featureLayer.getLatLng) {
      cartographyState.map.setView(featureLayer.getLatLng(), Math.max(cartographyState.map.getZoom(), 9));
    }
    selectMapFeature(layerKey, feature || { properties: row?.properties || {} }, featureLayer, { zoom: false });
    renderFeatureDetails(feature || { properties: row?.properties || {} }, layerKey);
    if (featureLayer.openPopup) featureLayer.openPopup();
    return;
  }

  renderTerritorialFeatureDetails(row?.properties || {}, layerKey);
  openEntityProfile(layerKey, row?.properties || {});
  showZonesMessage('Fiche attributaire ouverte, géométrie manquante.');
}

function openEntityProfile(layerKey, properties = {}, feature = null) {
  const drawer = document.querySelector('#entity-profile-drawer');
  const title = document.querySelector('#entity-profile-title');
  const layerLabel = document.querySelector('#entity-profile-layer');
  const body = document.querySelector('#entity-profile-body');
  if (!drawer || !title || !layerLabel || !body) return;
  const normalized = layerKey === 'zones'
    ? { ...properties, ...computeZoneProfileProperties(properties), layer: layerKey }
    : { ...properties, layer: layerKey };
  const demoEnriched = applyDemoEnrichmentToProperties(normalized);
  platformState.selectedEntity = { layerKey, properties: demoEnriched, feature };
  title.textContent = demoEnriched.nom || demoEnriched.name || 'Entité sans nom';
  layerLabel.textContent = getLayerDisplayLabel(layerKey);
  body.innerHTML = buildEntityProfileMarkup(layerKey, demoEnriched);
  drawer.classList.remove('hidden');
  document.body.classList.add('entity-profile-open');
  bindEntityProfileActions(body, layerKey, demoEnriched, feature);
  hydrateEntityProfileFromApi(layerKey, demoEnriched, feature);
}

function bindEntityProfileActions(body, layerKey, properties, feature = null) {
  body.querySelector('[data-profile-action="toggle-export"]')?.addEventListener('click', () => {
    body.querySelector('.profile-export-menu')?.classList.toggle('hidden');
  });
  body.querySelector('[data-profile-action="save"]')?.addEventListener('click', () => exportEntityProfile(layerKey, properties, feature));
  body.querySelector('[data-profile-action="print"]')?.addEventListener('click', () => window.print());
  body.querySelectorAll('[data-open-related-layer]').forEach((button) => {
    button.addEventListener('click', () => openLayerWorkbench(button.dataset.openRelatedLayer));
  });
  body.querySelectorAll('[data-open-relation-list]').forEach((button) => {
    button.addEventListener('click', () => openRelationCounterList(button.dataset.openRelationList, properties));
  });
}

function hydrateEntityProfileFromApi(layerKey, properties, feature = null) {
  if (LOCAL_JSON_MODE || properties.relation_links) return;
  const entityId = properties.id || properties.canonical_id || properties.code;
  if (!entityId) return;
  fetchJson(`/entities/${getApiLayerName(layerKey)}/${entityId}`).then((entity) => {
    if (!entity || Object.keys(entity).length === 0) return;
    const drawer = document.querySelector('#entity-profile-drawer');
    const title = document.querySelector('#entity-profile-title');
    const body = document.querySelector('#entity-profile-body');
    if (!drawer || drawer.classList.contains('hidden') || !body) return;
    const enriched = applyDemoEnrichmentToProperties({ ...properties, ...entity, layer: layerKey });
    platformState.selectedEntity = { layerKey, properties: enriched, feature };
    if (title) title.textContent = enriched.nom || enriched.name || 'Entité sans nom';
    body.innerHTML = buildEntityProfileMarkup(layerKey, enriched);
    bindEntityProfileActions(body, layerKey, enriched, feature);
  });
}

function applyDemoEnrichmentToProperties(properties) {
  if (!DEMO_ENRICHMENT_MODE || !platformState.demoEnrichment?.entities) return properties;
  const match = findDemoEnrichmentForEntity(properties);
  if (!match?.fields) return properties;
  const enriched = { ...properties };
  const futureProfile = {
    ...(properties.future_profile && typeof properties.future_profile === 'object' ? properties.future_profile : {}),
  };
  const applied = [];
  const identityFields = new Set(['description', 'chef_lieu', 'superficie', 'population', 'subdivision', 'geographie', 'climat']);
  Object.entries(match.fields).forEach(([field, value]) => {
    if (value === null || value === undefined || value === '') return;
    const target = identityFields.has(field) ? enriched : futureProfile;
    if (isDemoMissingValue(target[field])) {
      target[field] = value;
      if (field.startsWith('potentiel_')) {
        const potentialKey = field.replace('potentiel_', '').replace('numerique', 'numerique');
        futureProfile.potentiels = {
          ...(futureProfile.potentiels && typeof futureProfile.potentiels === 'object' ? futureProfile.potentiels : {}),
          [potentialKey]: value,
        };
      }
      applied.push({
        field,
        value,
        source_name: match.source_name || 'CNCT démo',
        source_url: match.source_url || '',
        consulted_at: match.consulted_at || '',
        confidence_level: match.confidence_level || 'à vérifier',
        status: match.status || 'proposition à valider',
      });
    }
  });
  if (applied.length) {
    enriched.future_profile = futureProfile;
    enriched.demo_enrichment = {
      entity_name: match.entity_name,
      source_name: match.source_name,
      source_url: match.source_url,
      consulted_at: match.consulted_at,
      confidence_level: match.confidence_level,
      status: match.status || 'proposition à valider',
      applied,
    };
  }
  return enriched;
}

function findDemoEnrichmentForEntity(properties) {
  const names = [
    properties.nom,
    properties.name,
    properties.entity_name,
    properties.code,
    properties.canonical_id,
  ].filter(Boolean).map(normalizeDemoEntityName);
  return asArray(platformState.demoEnrichment?.entities).find((item) => {
    const candidates = [item.entity_name, ...(Array.isArray(item.aliases) ? item.aliases : [])]
      .filter(Boolean)
      .map(normalizeDemoEntityName);
    return candidates.some((candidate) => names.includes(candidate));
  });
}

function normalizeDemoEntityName(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/gi, ' ')
    .trim()
    .toLowerCase();
}

function isDemoMissingValue(value) {
  if (value === null || value === undefined || value === '') return true;
  const text = normalizeDemoEntityName(value);
  return [
    'donnee non encore renseignee',
    'non renseignee',
    'non renseigne',
    'non disponible',
    'a completer',
  ].includes(text);
}

function closeEntityProfile() {
  document.querySelector('#entity-profile-drawer')?.classList.add('hidden');
  document.body.classList.remove('entity-profile-open');
}

function exportEntityProfile(layerKey, properties, feature = null) {
  const format = document.querySelector('#entity-profile-export-format')?.value || 'json';
  const baseName = getProfileExportBaseName(layerKey, properties);
  if (format === 'json') {
    downloadTextFile(`${baseName}.json`, JSON.stringify(properties, null, 2), 'application/json');
    return;
  }
  if (format === 'csv') {
    downloadTextFile(`${baseName}.csv`, toCsv([properties]), 'text/csv;charset=utf-8');
    return;
  }
  if (format === 'excel') {
    downloadTextFile(`${baseName}.xls`, buildHtmlTableDocument(properties), 'application/vnd.ms-excel;charset=utf-8');
    return;
  }
  if (format === 'word') {
    downloadTextFile(`${baseName}.doc`, buildHtmlProfileDocument(properties), 'application/msword;charset=utf-8');
    return;
  }
  if (format === 'pdf') {
    alert('Export PDF direct prévu avec génération PDF dédiée. Utilisez temporairement PDF / Impression navigateur.');
    return;
  }
  if (format === 'print_pdf') {
    window.print();
    return;
  }
  if (format === 'geojson') {
    const geometry = feature?.geometry || properties.geometry;
    if (!geometry) {
      alert('GeoJSON non disponible : cette fiche ne contient pas de géométrie.');
      return;
    }
    downloadTextFile(`${baseName}.geojson`, JSON.stringify({ type: 'Feature', geometry, properties }, null, 2), 'application/geo+json');
    return;
  }
  if (format === 'kml' || format === 'kmz') {
    const geometry = feature?.geometry || properties.geometry;
    if (!geometry) {
      alert(`${format.toUpperCase()} non disponible : cette fiche ne contient pas de géométrie.`);
      return;
    }
    downloadTextFile(`${baseName}.kml`, buildKmlFeature(properties, geometry), 'application/vnd.google-earth.kml+xml');
    return;
  }
}

function getProfileExportBaseName(layerKey, properties) {
  const type = sanitizeExportSegment(getApiLayerName(layerKey));
  const name = sanitizeExportSegment(properties.nom || properties.name || properties.code || properties.canonical_id || 'fiche');
  return `sig_fdsu_${type}_${name}_${getExportDateStamp()}`;
}

function sanitizeExportSegment(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toLowerCase() || 'fiche';
}

function buildEntityProfileMarkup(layerKey, properties) {
  const profile = getFutureProfile(properties);
  const relations = getEntityRelations(layerKey, properties);
  return `
    <section class="profile-actions">
      <button type="button" class="primary-button" data-profile-action="toggle-export">Exporter</button>
      <button type="button" class="table-action-button" data-profile-action="print">Imprimer</button>
    </section>
    <section class="profile-actions profile-export-menu hidden">
      <select id="entity-profile-export-format" aria-label="Format export fiche">
        <option value="pdf">PDF</option>
        <option value="print_pdf">PDF / Impression navigateur</option>
        <option value="word">Word / DOCX</option>
        <option value="excel">Excel / XLSX</option>
        <option value="csv">CSV</option>
        <option value="json">JSON</option>
        <option value="geojson">GeoJSON</option>
        <option value="kml">KML</option>
        <option value="kmz">KMZ</option>
      </select>
      <button type="button" class="primary-button" data-profile-action="save">Enregistrer la fiche</button>
    </section>
    ${renderDemoEnrichmentBanner(properties)}
    ${buildTypedIdentitySection(layerKey, properties, profile)}
    <section class="profile-section">
      <h3>Carte</h3>
      <p>${properties.latitude && properties.longitude ? `Objet géolocalisé : ${formatGpsCoordinates(properties)}.` : 'Géométrie ou coordonnées non disponibles pour cet objet.'}</p>
    </section>
    <section class="profile-section">
      <h3>Activités économiques</h3>
      ${renderEconomicActivities(profile)}
    </section>
    <section class="profile-section">
      <h3>Particularités</h3>
      <div class="rich-text-preview">${renderListOrPlaceholder(profile.particularites, 'Aucune particularité renseignée.')}</div>
    </section>
    <section class="profile-section">
      <h3>Défis</h3>
      ${renderChallenges(profile)}
    </section>
    <section class="profile-section">
      <h3>Potentiel de développement</h3>
      ${renderPotentials(profile)}
    </section>
    <section class="profile-section">
      <h3>Services publics</h3>
      ${renderServiceGrid(profile)}
    </section>
    <section class="profile-section">
      <h3>Analyse FDSU</h3>
      ${buildProfileSection(null, [
        ['Couverture numérique', profile.couverture_numerique],
        ['Opérateurs présents', asArray(profile.operateurs).join(', ')],
        ['Technologies', asArray(profile.technologies).join(', ')],
        ['Qualité de service', profile.qualite_service],
        ['Sites existants', profile.sites_existants],
        ['Sites candidats', profile.sites_candidats],
        ['Missions réalisées', profile.missions_realisees],
        ['Besoins prioritaires', asArray(profile.besoins_prioritaires).join(', ')],
        ['Score priorité FDSU', profile.score_priorite_fdsu],
        ['Recommandations', profile.recommandations],
      ], true)}
    </section>
    <section class="profile-section">
      <h3>Relations hiérarchiques</h3>
      <div class="profile-relations">${relations.map((relation) => `<button type="button" class="table-action-button" data-open-related-layer="${escapeHtml(relation.layer)}">${escapeHtml(relation.label)}</button>`).join('') || '<p>Aucune relation disponible.</p>'}</div>
    </section>
    ${buildProfileSection('Qualité des données', [
      ['Score qualité', properties.qualite || properties.quality],
      ['Statut', properties.statut],
      ['Source', properties.source],
      ['Anomalies', properties.anomalies],
    ])}
    <section class="profile-section">
      <h3>Documents et photos</h3>
      <p>Aucun document ou photo lié dans cette version.</p>
    </section>
    ${buildKnowledgeBaseSection(profile)}
    <section class="profile-section">
      <h3>Historique</h3>
      <ol class="profile-history">
        <li>Source importée : ${escapeHtml(properties.source || 'Non renseignée')}</li>
        <li>Statut courant : ${escapeHtml(properties.statut || 'Non renseigné')}</li>
        <li>Consultation fiche : ${escapeHtml(new Date().toLocaleString('fr-FR'))}</li>
      </ol>
    </section>
  `;
}

function buildTypedIdentitySection(layerKey, properties, profile) {
  const type = getEntityProfileType(layerKey, properties);
  const fieldSets = {
    zone: [
      ['Code zone FDSU', properties.zone_fdsu || properties.code],
      ['Nom', properties.nom],
      ['Provinces rattachées', properties.provinces_rattachees],
      ['Nombre de provinces', properties.nb_provinces],
      ['Sites FDSU', properties.sites],
      ['Missions', properties.missions],
    ],
    province: [
      ['Zone FDSU', properties.zone_fdsu],
      ['Code province', properties.code_province_fdsu || properties.code || properties.canonical_id],
      ['Nom', properties.nom],
      ['Chef-lieu', properties.chef_lieu],
      ['Territoires', properties.territoires, 'territoires'],
      ['Villes', properties.villes],
      ['Collectivités', properties.collectivites, 'collectivites'],
      ['Groupements', properties.groupements, 'groupements'],
      ['Localités', properties.localites, 'localites'],
      ['Sites FDSU', properties.sites],
      ['Missions', properties.missions],
    ],
    ville_province: [
      ['Type', 'Ville-Province'],
      ['Zone FDSU', properties.zone_fdsu],
      ['Code province', properties.code_province_fdsu || properties.code || properties.canonical_id],
      ['Nom', properties.nom],
      ['Districts', properties.districts || 'Funa, Lukunga, Mont-Amba, Tshangu'],
      ['Communes', properties.communes],
      ['Quartiers', properties.quartiers],
      ['Population', properties.population || profile.population],
      ['Superficie', properties.superficie],
      ['Sites FDSU', properties.sites],
      ['Connectivité', profile.couverture_numerique],
    ],
    territoire: [
      ['Province', properties.province],
      ['Zone FDSU', properties.zone_fdsu],
      ['Code territoire', properties.code_territoire_fdsu || properties.code || properties.canonical_id],
      ['Secteurs', properties.secteurs],
      ['Chefferies', properties.chefferies],
      ['Collectivités', properties.collectivites, 'collectivites'],
      ['Groupements', properties.groupements, 'groupements'],
      ['Localités', properties.localites, 'localites'],
      ['Villages', properties.villages],
      ['Sites FDSU', properties.sites],
      ['Missions', properties.missions],
    ],
    collectivite: [
      ['Territoire', properties.territoire],
      ['Province', properties.province],
      ['Zone FDSU', properties.zone_fdsu],
      ['Code collectivité', properties.code || properties.canonical_id],
      ['Type', properties.type],
      ['Groupements', properties.groupements, 'groupements'],
      ['Localités', properties.localites, 'localites'],
      ['Sites FDSU', properties.sites],
      ['Missions', properties.missions],
    ],
    groupement: [
      ['Collectivité', properties.collectivite],
      ['Territoire', properties.territoire],
      ['Province', properties.province],
      ['Localités', properties.localites, 'localites'],
      ['Villages', properties.villages],
      ['Sites FDSU', properties.sites],
      ['Missions', properties.missions],
    ],
    localite: [
      ['Groupement', properties.groupement],
      ['Collectivité', properties.collectivite],
      ['Territoire', properties.territoire],
      ['Province', properties.province],
      ['Coordonnées', formatGpsCoordinates(properties)],
      ['Population', properties.population || profile.population],
      ['Sites FDSU liés', properties.sites],
      ['Missions liées', properties.missions],
      ['Services publics', formatPublicServices(properties.services_publics)],
      ['Connectivité', formatConnectivity(properties.connectivite)],
      ['Couverture réseau', profile.couverture_numerique],
      ['Potentiel CCN', profile.potentiel_numerique],
      ['Score FDSU', profile.score_priorite_fdsu],
    ],
    default: [
      ['Code officiel', properties.code || properties.canonical_id],
      ['Nom', properties.nom],
      ['Type administratif', properties.type],
      ['Hiérarchie administrative', formatHierarchy(properties)],
      ['Coordonnées', formatGpsCoordinates(properties)],
      ['Source', properties.source],
    ],
  };
  return buildProfileSection(getProfileTypeLabel(type), fieldSets[type] || fieldSets.default);
}

function getEntityProfileType(layerKey, properties) {
  const name = normalizeDashboardText(properties.nom || properties.name);
  const type = normalizeDashboardText(properties.type || '');
  if (layerKey === 'zones') return 'zone';
  if (layerKey === 'provinces' && name === 'kinshasa') return 'ville_province';
  if (layerKey === 'provinces') return 'province';
  if (layerKey === 'territoires') return type.includes('ville') ? 'ville' : 'territoire';
  if (layerKey === 'collectivites') return 'collectivite';
  if (layerKey === 'groupements') return 'groupement';
  if (layerKey === 'villages' || layerKey === 'localites') return 'localite';
  return 'default';
}

function getProfileTypeLabel(type) {
  return {
    zone: 'Fiche Zone FDSU',
    province: 'Fiche Province',
    ville_province: 'Fiche Ville-Province',
    territoire: 'Fiche Territoire',
    ville: 'Fiche Ville',
    collectivite: 'Fiche Collectivité',
    groupement: 'Fiche Groupement',
    localite: 'Fiche Localité',
    default: 'Fiche métier',
  }[type] || 'Fiche métier';
}

function buildProfileSection(title, rows, embedded = false) {
  const content = `<div class="detail-attributes">${rows.map((row) => buildProfileDetailRow(row)).join('')}</div>`;
  if (embedded) return content;
  return `<section class="profile-section">${title ? `<h3>${escapeHtml(title)}</h3>` : ''}${content}</section>`;
}

function buildProfileDetailRow(row) {
  const [label, value, relationKey] = row;
  const hasValue = value !== null && value !== undefined && value !== '';
  const formatted = hasValue ? formatAttributeValue(value) : missingDataText();
  const relationButton = relationKey && hasValue
    ? `<button type="button" class="table-action-button relation-list-button" data-open-relation-list="${escapeHtml(relationKey)}">Voir la liste</button>`
    : '';
  return `
    <div class="detail-row relation-detail-row">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(formatted)}</strong>
      ${relationButton}
    </div>
  `;
}

function missingDataText() {
  return 'À compléter';
}

function renderDemoEnrichmentBanner(properties) {
  const demo = properties.demo_enrichment;
  const applied = asArray(demo?.applied);
  if (!demo || applied.length === 0) return '';
  return `
    <section class="profile-section demo-enrichment-section">
      <div class="demo-enrichment-header">
        <div>
          <h3>Enrichissement CNCT démo</h3>
          <p>Les informations ci-dessous complètent l'affichage sans modifier le référentiel officiel.</p>
        </div>
        <span class="demo-enrichment-badge">Proposition à valider</span>
      </div>
      <div class="demo-enrichment-meta">
        <span>Donnée affichée en mode démo</span>
        <span>Confiance : ${escapeHtml(demo.confidence_level || 'à vérifier')}</span>
        <span>Consultation : ${escapeHtml(demo.consulted_at || 'à compléter')}</span>
      </div>
      <div class="demo-enrichment-source">
        <strong>Source</strong>
        <span>${escapeHtml(demo.source_name || 'Source à vérifier')}</span>
        <small>${escapeHtml(demo.source_url || 'URL non disponible')}</small>
      </div>
      <div class="demo-enrichment-fields">
        ${applied.slice(0, 8).map((item) => `<span>${escapeHtml(formatDetailLabel(item.field))}</span>`).join('')}
      </div>
    </section>
  `;
}

function formatPublicServices(services) {
  if (!services || typeof services !== 'object') return '';
  const labels = [
    ['centre_sante', 'Centre de santé'],
    ['ecole_primaire', 'École primaire'],
    ['ecole_secondaire', 'École secondaire'],
    ['marche', 'Marché'],
    ['electricite', 'Électricité'],
  ];
  const available = labels
    .filter(([key]) => services[key] === true)
    .map(([, label]) => label);
  return available.length ? available.join(', ') : '0 service public renseigné';
}

function formatConnectivity(connectivity) {
  if (!connectivity || typeof connectivity !== 'object') return '';
  const networks = [
    ['couverture_2g', '2G'],
    ['couverture_3g', '3G'],
    ['couverture_4g', '4G'],
    ['couverture_5g', '5G'],
  ]
    .filter(([key]) => connectivity[key] === true)
    .map(([, label]) => label);
  const score = connectivity.score_connectivite !== null && connectivity.score_connectivite !== undefined
    ? `Score ${Number(connectivity.score_connectivite).toLocaleString('fr-FR')}`
    : '';
  return [networks.join(', '), score].filter(Boolean).join(' - ') || '0 couverture renseignée';
}

function buildKnowledgeBaseSection(profile) {
  const fields = [
    ['Historique', profile.historique],
    ['Description', profile.description],
    ['Géographie', profile.geographie],
    ['Climat', profile.climat],
    ['Subdivision', profile.subdivision],
    ['Population', profile.population],
    ['Potentiel agricole', profile.potentiel_agricole],
    ['Potentiel minier', profile.potentiel_minier],
    ['Potentiel touristique', profile.potentiel_touristique],
    ['Potentiel numérique', profile.potentiel_numerique],
    ['Rapports', asArray(profile.rapports).join(', ')],
  ];
  return buildProfileSection('Base de connaissances territoriale', fields);
}

function getFutureProfile(properties) {
  const metadata = properties.metadata && typeof properties.metadata === 'object' ? properties.metadata : {};
  const profile = properties.future_profile && typeof properties.future_profile === 'object' ? properties.future_profile : {};
  return {
    activites_economiques: profile.activites_economiques || metadata.activites_economiques || [],
    activite_principale: profile.activite_principale || metadata.activite_principale || '',
    activite_secondaire: profile.activite_secondaire || metadata.activite_secondaire || '',
    particularites: profile.particularites || metadata.particularites || [],
    defis: profile.defis || metadata.defis || [],
    potentiels: profile.potentiels || metadata.potentiels || {},
    services_publics: profile.services_publics || metadata.services_publics || {},
    couverture_numerique: profile.couverture_numerique || '',
    operateurs: profile.operateurs || [],
    technologies: profile.technologies || [],
    qualite_service: profile.qualite_service || '',
    sites_existants: profile.sites_existants || '',
    sites_candidats: profile.sites_candidats || '',
    missions_realisees: profile.missions_realisees || '',
    besoins_prioritaires: profile.besoins_prioritaires || [],
    score_priorite_fdsu: profile.score_priorite_fdsu || '',
    recommandations: profile.recommandations || '',
    infrastructures: profile.infrastructures || [],
    historique: profile.historique || metadata.historique || properties.historique || '',
    description: profile.description || metadata.description || properties.description || '',
    geographie: profile.geographie || metadata.geographie || properties.geographie || '',
    climat: profile.climat || metadata.climat || properties.climat || '',
    subdivision: profile.subdivision || metadata.subdivision || properties.subdivision || '',
    population: profile.population || metadata.population || properties.population || '',
    potentiel_agricole: profile.potentiel_agricole || metadata.potentiel_agricole || profile.potentiels?.agricole || '',
    potentiel_minier: profile.potentiel_minier || metadata.potentiel_minier || profile.potentiels?.minier || '',
    potentiel_touristique: profile.potentiel_touristique || metadata.potentiel_touristique || profile.potentiels?.touristique || '',
    potentiel_numerique: profile.potentiel_numerique || metadata.potentiel_numerique || profile.potentiels?.numerique || '',
    rapports: profile.rapports || metadata.rapports || [],
  };
}

function renderEconomicActivities(profile) {
  const activities = [
    profile.activite_principale ? { nom: profile.activite_principale, role: 'Principale' } : null,
    profile.activite_secondaire ? { nom: profile.activite_secondaire, role: 'Secondaire' } : null,
    ...asArray(profile.activites_economiques).map((activity) => typeof activity === 'string' ? { nom: activity } : activity),
  ].filter(Boolean);
  if (activities.length === 0) return '<p>À compléter</p>';
  return `<div class="activity-chip-list">${activities.map((activity) => `<span class="activity-chip"><strong>${escapeHtml(activity.nom || activity.label || 'Activité')}</strong><small>${escapeHtml(activity.role || activity.priorite || 'À qualifier')}</small></span>`).join('')}</div>`;
}

function renderChallenges(profile) {
  const challenges = asArray(profile.defis);
  if (challenges.length === 0) return '<p>À compléter</p>';
  return `<div class="challenge-list">${challenges.map((challenge) => {
    const label = typeof challenge === 'string' ? challenge : challenge.nom || challenge.label || 'Défi';
    const level = typeof challenge === 'string' ? 'À qualifier' : challenge.niveau || 'À qualifier';
    return `<div class="challenge-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(level)}</strong></div>`;
  }).join('')}</div>`;
}

function renderPotentials(profile) {
  const potentials = profile.potentiels || {};
  const keys = ['agricole', 'pastoral', 'halieutique', 'minier', 'forestier', 'touristique', 'commercial', 'numerique', 'energetique'];
  return `<div class="potential-grid">${keys.map((key) => {
    const value = potentials[key];
    const formatted = typeof value === 'number' ? `${value}/5` : formatAttributeValue(value || 'À compléter');
    return `<div><span>${escapeHtml(key)}</span><strong>${escapeHtml(formatted)}</strong></div>`;
  }).join('')}</div>`;
}

function renderServiceGrid(profile) {
  const services = profile.services_publics || {};
  const keys = ['ecoles', 'centres_sante', 'batiments_administratifs', 'marches', 'eglises', 'points_eau', 'reseau_electrique', 'couverture_telephonique', 'internet', 'ccn', 'sites_fdsu'];
  return `<div class="service-grid">${keys.map((key) => `<div><span>${escapeHtml(key.replaceAll('_', ' '))}</span><strong>${escapeHtml(formatAttributeValue(services[key] || 'À compléter'))}</strong></div>`).join('')}</div>`;
}

function renderListOrPlaceholder(items, placeholder) {
  const values = asArray(items);
  if (values.length === 0) return `<p>${escapeHtml(placeholder)}</p>`;
  return `<ul>${values.map((item) => `<li>${escapeHtml(typeof item === 'string' ? item : JSON.stringify(item))}</li>`).join('')}</ul>`;
}

function formatHierarchy(properties) {
  return [
    properties.zone_fdsu,
    properties.province,
    properties.territoire,
    properties.collectivite,
    properties.groupement,
    properties.localite,
  ].filter(Boolean).join(' > ') || 'Non disponible';
}

function getEntityRelations(layerKey) {
  const order = ['provinces', 'territoires', 'collectivites', 'groupements', 'villages', 'sites', 'missions'];
  const index = order.indexOf(layerKey);
  if (index < 0) return [];
  return order.slice(Math.max(0, index - 1), index + 2)
    .filter((candidate) => candidate !== layerKey)
    .map((candidate) => ({ layer: candidate, label: WEB_SIG_LAYER_DEFINITIONS[candidate]?.label || candidate }));
}

function getLayerDisplayLabel(layerKey) {
  if (layerKey === 'zones') return 'Zones FDSU';
  return WEB_SIG_LAYER_DEFINITIONS[layerKey]?.label || 'Fiche territoriale';
}

function fetchReportJson(path) {
  const url = `${REPORTS_BASE}/${path}`;
  return fetch(url)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`JSON absent: ${path}`);
      }
      return response.json();
    })
    .then((data) => ({ path: url, data, available: true }))
    .catch(() => ({ path: url, data: null, available: false }));
}

function buildNationalReferentialReportFromJson(payload) {
  const registryCounters = payload.registry?.registre_national_des_compteurs || {};
  const provinces = asArray(payload.provinceReferential?.province_referential);
  const territories = asArray(payload.territoryHierarchy?.territories).filter((item) => normalizeDashboardText(item?.attributs?.extended_data?.TYPE) === 'territoire');
  const cities = asArray(payload.cityReferential?.city_referential);
  const collectivities = asArray(payload.collectivityReferential?.collectivity_referential);
  const groupements = asArray(payload.groupementReferential?.groupement_referential);
  const localities = asArray(payload.localityReferential?.locality_referential);
  const groupementAudit = payload.groupementCoverageAudit || {};
  const groupementQuality = payload.groupementQuality || {};
  const collectivityQuality = payload.collectivityQuality || {};
  const localityQuality = payload.localityQuality || {};
  const provinceQuality = payload.provinceQuality || {};
  const cityQuality = payload.cityQuality || {};
  const expectedGroupements = registryCounters.groupements?.attendu_officiel ?? groupementAudit.national_reference?.expected_groupements;
  const foundGroupements = registryCounters.groupements?.trouve ?? registryCounters.groupements?.nombre ?? groupements.length;
  const groupementCoverage = registryCounters.groupements?.couverture ?? (groupementAudit.national_reference?.coverage_percent ? `${groupementAudit.national_reference.coverage_percent}%` : 'Donnée non disponible');

  const tree = buildOfficialHierarchyTree({ provinces, territories, cities, collectivities, groupements, localities });
  const anomalyRows = buildOfficialAnomalyRows({ groupementAudit, groupementQuality, collectivityQuality, localityQuality });
  const qualityScore = computeDashboardQualityScore([provinceQuality.global_score, cityQuality.global_score, collectivityQuality.global_score, groupementQuality.global_score, localityQuality.global_score]);
  const byLevel = {
    rdc: 1,
    zone_fdsu: tree.children.length,
    province: registryCounters.provinces?.nombre ?? provinces.length,
    territoire: registryCounters.territoires?.nombre ?? territories.length,
    ville: registryCounters.villes?.nombre ?? cities.length,
    secteur: registryCounters.secteurs?.nombre ?? collectivities.filter((item) => item.type_collectivite === 'Secteur').length,
    chefferie: registryCounters.chefferies?.nombre ?? collectivities.filter((item) => item.type_collectivite === 'Chefferie').length,
    groupement: foundGroupements,
    localite: registryCounters.localites?.nombre ?? localityQuality.locality_count ?? localities.length,
  };
  const totalEntities = Object.values(byLevel).reduce((total, value) => total + (Number(value) || 0), 0);
  const missingFiles = Object.values(payload.sources || {}).filter((source) => !source.available).length;
  const duplicateCount = (groupementQuality.duplicate_count || 0) + (collectivityQuality.duplicate_count || 0) + (provinceQuality.duplicates || 0) + (localityQuality.duplicate_count || 0);
  const orphanCount = (groupementQuality.orphan_count || 0) + (collectivityQuality.missing_territory_count || 0) + (localityQuality.orphan_count || 0);
  const referentielRows = [
    buildRegistryRow('zones', 'Zones FDSU', 'Zone FDSU', 5, tree.children.length, '100%', 'Validé', 'Non publié', qualityScore, 'Référentiel national consolidé'),
    buildRegistryRow('provinces', 'Provinces', 'Province', 26, byLevel.province, '100%', registryCounters.provinces?.statut || 'Validé', 'Non publié', provinceQuality.global_score, 'Province26.kmz'),
    buildRegistryRow('territoires', 'Territoires', 'Territoire', 145, byLevel.territoire, '100%', registryCounters.territoires?.statut || 'Validé', 'Non publié', payload.territoryHierarchy ? 100 : null, 'territoires_hierarchie_kmz.report.json'),
    buildRegistryRow('villes', 'Villes', 'Ville', 11, byLevel.ville, '100%', registryCounters.villes?.statut || 'Validé', 'Non publié', cityQuality.global_score, 'zones_fdsu.kmz'),
    buildRegistryRow('collectivites', 'Collectivités', 'Secteur / Chefferie', 733, registryCounters.collectivites?.nombre ?? collectivities.length, '100%', registryCounters.collectivites?.statut || 'Validé provisoirement', 'Non publié', collectivityQuality.global_score, 'collectivites.kmz'),
    buildRegistryRow('groupements', 'Groupements', 'Groupement', expectedGroupements, foundGroupements, groupementCoverage, registryCounters.groupements?.statut || 'Partiel', registryCounters.groupements?.validation || 'Non publié', groupementQuality.global_score, 'Groupements.kmz'),
    buildRegistryRow('localites', 'Localités', 'Localité', registryCounters.localites?.reference_nationale, byLevel.localite, registryCounters.localites?.comparaison_reference || 'Référence nationale non disponible', registryCounters.localites?.statut || 'Partiel', registryCounters.localites?.validation || 'Non publié', localityQuality.global_score, 'Localités.kmz'),
  ];

  return {
    tree,
    registryCounters,
    referentielRows,
    sourceRows: buildOfficialSourceRows(payload.sources),
    validationRows: anomalyRows,
    qualityRows: buildOfficialQualityRows({ provinceQuality, cityQuality, collectivityQuality, groupementQuality, localityQuality, groupementAudit, missingFiles }),
    normalizationRow: {
      id: 'national-referential-json',
      source: 'Référentiels JSON officiels',
      entites_analysees: totalEntities,
      score_qualite: qualityScore,
      erreurs: anomalyRows.length,
      doublons: duplicateCount,
      orphelines: orphanCount,
      rapport: missingFiles ? 'Donnée non disponible' : 'Chargé',
    },
    normalization: {
      summary: {
        analyzedEntities: totalEntities,
        qualityScore,
        errors: anomalyRows.length,
        duplicates: duplicateCount,
        orphans: orphanCount,
        reportStatus: missingFiles ? `${missingFiles} fichier(s) absent(s)` : 'Référentiels JSON chargés',
      },
      byLevel: Object.entries(byLevel).map(([level, value]) => ({ level, value })),
      reportPreview: buildOfficialMarkdownPreview({ byLevel, referentielRows, anomalyRows, missingFiles, groupementCoverage }),
    },
    statistics: {
      entityCount: totalEntities,
      byLevel,
      orphanCount,
      duplicateCount,
      qualityScore,
    },
    anomalies: anomalyRows.map((row) => ({
      level: row.level || 'referentiel',
      entity: row.objet,
      message: row.probleme || row.sans_rattachement || 'Anomalie connue',
      severity: row.statut === 'À valider manuellement' ? 'error' : 'warning',
      code: row.id,
    })),
    quality: { qualityScore },
  };
}

function buildOfficialHierarchyTree({ provinces, territories, cities, collectivities, groupements, localities = [] }) {
  const root = {
    level: 'rdc',
    label: 'RDC',
    count: 1,
    status: 'Validé provisoirement',
    source: 'Référentiel national des compteurs',
    quality: null,
    children: [],
    childStats: {},
  };
  const zoneNodes = new Map();
  const provinceNodes = new Map();
  const territoryNodes = new Map();
  const collectivityNodes = new Map();
  const groupementNodes = new Map();

  provinces.slice().sort(sortByName).forEach((province) => {
    const zoneCode = province.zone_fdsu || 'INCONNU';
    const zoneLabel = zoneLabelFromCode(zoneCode);
    const zoneNode = getOrCreateNode(zoneNodes, zoneCode, {
      level: 'zone_fdsu',
      label: zoneLabel,
      code: zoneCode,
      count: 0,
      status: 'Validé',
      source: province.source || 'province_referential_official.json',
      quality: province.qualite,
      children: [],
      childStats: { provinces: 0 },
    });
    if (!root.children.includes(zoneNode)) root.children.push(zoneNode);
    zoneNode.count += 1;
    zoneNode.childStats.provinces += 1;

    const provinceNode = {
      level: 'province',
      label: province.nom,
      code: province.code_officiel,
      count: 1,
      status: normalizeDashboardStatus(province.statut || 'Validé'),
      source: province.source || 'province_referential_official.json',
      quality: province.qualite,
      children: [],
      raw: province,
      childStats: { territoires: 0, collectivites: 0, groupements: 0, localites: 0 },
    };
    zoneNode.children.push(provinceNode);
    provinceNodes.set(normalizeDashboardText(province.nom), provinceNode);
  });

  territories.slice().sort(sortByName).forEach((territory) => {
    const provinceNode = provinceNodes.get(normalizeDashboardText(territory.province));
    if (!provinceNode) return;
    const territoryNode = {
      level: 'territoire',
      label: territory.nom,
      code: territory.attributs?.extended_data?.CODE_INS || territory.attributs?.extended_data?.CODE,
      count: 1,
      status: territory.incoherences?.length ? 'À valider manuellement' : 'Validé',
      source: 'territoires_hierarchie_kmz.report.json',
      quality: territory.score_qualite,
      children: [],
      raw: territory,
      anomalies: asArray(territory.incoherences).map((item) => String(item)),
      childStats: { collectivites: 0, groupements: 0, localites: 0 },
    };
    provinceNode.children.push(territoryNode);
    provinceNode.childStats.territoires += 1;
    territoryNodes.set(hierarchyKey(territory.province, territory.nom), territoryNode);
  });

  cities.slice().sort(sortByName).forEach((city) => {
    const provinceNode = provinceNodes.get(normalizeDashboardText(city.province));
    if (!provinceNode) return;
    provinceNode.children.push({
      level: 'ville',
      label: city.nom,
      code: city.canonical_id,
      count: 1,
      status: normalizeDashboardStatus(city.statut || 'Validé provisoirement'),
      source: city.source || 'city_referential_official.json',
      quality: city.qualite,
      children: [],
      raw: city,
      childStats: {},
    });
  });

  collectivities.slice().sort(sortByName).forEach((collectivity) => {
    const territoryNode = territoryNodes.get(hierarchyKey(collectivity.province, collectivity.territoire));
    if (!territoryNode) return;
    const level = normalizeDashboardText(collectivity.type_collectivite) === 'chefferie' ? 'chefferie' : 'secteur';
    const collectivityNode = {
      level,
      label: collectivity.nom,
      code: collectivity.code_officiel,
      count: 1,
      status: normalizeDashboardStatus(collectivity.statut || 'Validé provisoirement'),
      source: collectivity.source || 'collectivity_referential_official.json',
      quality: collectivity.qualite,
      children: [],
      raw: collectivity,
      childStats: { groupements: 0, localites: 0 },
    };
    territoryNode.children.push(collectivityNode);
    territoryNode.childStats.collectivites += 1;
    const provinceNode = provinceNodes.get(normalizeDashboardText(collectivity.province));
    if (provinceNode) provinceNode.childStats.collectivites += 1;
    collectivityNodes.set(hierarchyKey(collectivity.province, collectivity.territoire, collectivity.nom), collectivityNode);
  });

  groupements.slice().sort(sortByName).forEach((groupement) => {
    const collectivityNode = collectivityNodes.get(hierarchyKey(groupement.province, groupement.territoire, groupement.collectivite_parent));
    if (!collectivityNode) return;
    const groupementNode = {
      level: 'groupement',
      label: groupement.nom,
      code: groupement.code_officiel,
      count: 1,
      status: normalizeDashboardStatus(groupement.statut || 'Partiel'),
      source: groupement.source || 'groupement_referential_official.json',
      quality: groupement.qualite,
      children: [],
      raw: groupement,
      anomalies: asArray(groupement.metadata?.inconsistencies),
      childStats: { localites: 0 },
    };
    collectivityNode.children.push(groupementNode);
    groupementNodes.set(hierarchyKey(groupement.province, groupement.territoire, groupement.collectivite_parent, groupement.nom), groupementNode);
    collectivityNode.childStats.groupements += 1;
    const territoryNode = territoryNodes.get(hierarchyKey(groupement.province, groupement.territoire));
    if (territoryNode) territoryNode.childStats.groupements += 1;
    const provinceNode = provinceNodes.get(normalizeDashboardText(groupement.province));
    if (provinceNode) provinceNode.childStats.groupements += 1;
  });

  localities.slice().sort(sortByName).forEach((locality) => {
    const groupementNode = locality.groupement
      ? groupementNodes.get(hierarchyKey(locality.province, locality.territoire, locality.collectivité, locality.groupement))
      : null;
    const collectivityNode = !groupementNode && locality.collectivité
      ? collectivityNodes.get(hierarchyKey(locality.province, locality.territoire, locality.collectivité))
      : null;
    const territoryNode = !groupementNode && !collectivityNode
      ? territoryNodes.get(hierarchyKey(locality.province, locality.territoire))
      : null;
    const parentNode = groupementNode || collectivityNode || territoryNode;
    if (!parentNode) return;

    parentNode.children.push({
      level: 'localite',
      label: locality.nom,
      code: locality.canonical_id,
      count: 1,
      status: normalizeDashboardStatus(locality.statut || 'Partiel'),
      source: locality.source || 'locality_referential_official.json',
      quality: locality.qualité,
      children: [],
      raw: locality,
      anomalies: asArray(locality.metadata?.inconsistencies),
      childStats: {},
    });
    parentNode.childStats.localites = (parentNode.childStats.localites || 0) + 1;
    const localityTerritoryNode = territoryNodes.get(hierarchyKey(locality.province, locality.territoire));
    if (localityTerritoryNode) localityTerritoryNode.childStats.localites = (localityTerritoryNode.childStats.localites || 0) + 1;
    const provinceNode = provinceNodes.get(normalizeDashboardText(locality.province));
    if (provinceNode) provinceNode.childStats.localites = (provinceNode.childStats.localites || 0) + 1;
  });

  root.children.sort(sortTreeNodes);
  root.children.forEach((zone) => {
    zone.children.sort(sortTreeNodes);
    zone.children.forEach((province) => province.children.sort(sortTreeNodes));
  });
  root.childStats = {
    zones: root.children.length,
    provinces: provinces.length,
    territoires: territories.length,
    villes: cities.length,
    collectivites: collectivities.length,
    groupements: groupements.length,
    localites: localities.length,
  };
  return root;
}

function buildOfficialAnomalyRows({ groupementAudit, groupementQuality, collectivityQuality, localityQuality }) {
  const rows = [];
  asArray(groupementQuality.anomalies).slice(0, 120).forEach((anomaly, index) => {
    rows.push({
      id: `groupement-anomaly-${index + 1}`,
      level: 'groupement',
      objet: anomaly.entite || 'Groupement',
      doublons: anomaly.probleme === 'doublon referentiel' ? 'Oui' : '—',
      geometries_invalides: anomaly.probleme === 'geometrie invalide' ? 'Oui' : '—',
      sans_code: anomaly.probleme === 'code officiel manquant' ? 'Oui' : '—',
      sans_rattachement: anomaly.probleme || anomaly.cause || 'Anomalie groupement',
      probleme: anomaly.cause || anomaly.probleme || 'Anomalie groupement',
      statut: anomaly.entite === 'Bena muhona' ? 'À valider manuellement' : 'Partiel',
    });
  });
  asArray(collectivityQuality.anomalies).slice(0, 40).forEach((anomaly, index) => {
    rows.push({
      id: `collectivity-anomaly-${index + 1}`,
      level: 'collectivite',
      objet: anomaly.entite || 'Collectivité',
      doublons: anomaly.probleme === 'doublon referentiel' ? 'Oui' : '—',
      geometries_invalides: anomaly.probleme === 'geometrie invalide' ? 'Oui' : '—',
      sans_code: '—',
      sans_rattachement: anomaly.probleme || 'Anomalie collectivité',
      probleme: anomaly.cause || anomaly.probleme || 'Anomalie collectivité',
      statut: anomaly.entite === 'Bahema' ? 'À valider manuellement' : 'Validé provisoirement',
    });
  });
  asArray(groupementAudit.territories_without_groupement).forEach((item, index) => {
    rows.push({
      id: `territory-without-groupement-${index + 1}`,
      level: 'territoire',
      objet: item.territoire || item.nom || String(item),
      doublons: '—',
      geometries_invalides: '—',
      sans_code: '—',
      sans_rattachement: 'Territoire sans groupement dans la source partielle',
      probleme: 'territoires sans groupement',
      statut: 'Partiel',
    });
  });
  asArray(groupementAudit.collectivities_without_groupement).forEach((item, index) => {
    rows.push({
      id: `collectivity-without-groupement-${index + 1}`,
      level: 'collectivite',
      objet: item.collectivite_parent || item.collectivite || item.nom || String(item),
      doublons: '—',
      geometries_invalides: '—',
      sans_code: '—',
      sans_rattachement: 'Collectivité sans groupement dans la source partielle',
      probleme: 'collectivités sans groupement',
      statut: item.collectivite_parent === 'Bahema' || item.nom === 'Bahema' ? 'À valider manuellement' : 'Partiel',
    });
  });
  if (!rows.some((row) => normalizeDashboardText(row.objet).includes('bahema'))) {
    rows.push({
      id: 'known-bahema',
      level: 'collectivite',
      objet: 'Bahema',
      doublons: '—',
      geometries_invalides: '—',
      sans_code: '—',
      sans_rattachement: 'Anomalie connue à vérifier dans les rapports collectivités/groupements',
      probleme: 'Bahema',
      statut: 'À valider manuellement',
    });
  }
  if (!rows.some((row) => normalizeDashboardText(row.objet).includes('bena muhona'))) {
    rows.push({
      id: 'known-bena-muhona',
      level: 'groupement',
      objet: 'Bena muhona',
      doublons: '—',
      geometries_invalides: '—',
      sans_code: '—',
      sans_rattachement: 'Groupement orphelin connu dans le rapport officiel',
      probleme: 'Bena muhona',
      statut: 'À valider manuellement',
    });
  }
  asArray(localityQuality.anomalies).slice(0, 80).forEach((anomaly, index) => {
    rows.push({
      id: `locality-anomaly-${index + 1}`,
      level: 'localite',
      objet: anomaly.entite || 'Localité',
      doublons: anomaly.probleme === 'doublon referentiel' ? 'Oui' : '—',
      geometries_invalides: anomaly.probleme === 'geometrie_invalide' ? 'Oui' : '—',
      sans_code: '—',
      sans_rattachement: anomaly.probleme || anomaly.sans_rattachement || 'Anomalie localité',
      probleme: anomaly.suggestion || anomaly.probleme || 'Anomalie localité',
      statut: anomaly.probleme === 'type_inconnu' ? 'À valider manuellement' : 'Partiel',
    });
  });
  return rows;
}

function buildOfficialQualityRows({ provinceQuality, cityQuality, collectivityQuality, groupementQuality, localityQuality, groupementAudit, missingFiles }) {
  return [
    {
      id: 'province-quality',
      referentiel: 'Provinces',
      completude: `${formatGovernanceMetric(provinceQuality.global_score)} %`,
      coherence: `${formatGovernanceMetric(provinceQuality.global_score)} %`,
      geometries_valides: `${formatGovernanceMetric(26 - (provinceQuality.provinces_without_geometry || 0))} / 26`,
      doublons: provinceQuality.duplicates || 0,
      qualite_globale: provinceQuality.global_score ?? 'Donnée non disponible',
    },
    {
      id: 'city-quality',
      referentiel: 'Villes',
      completude: `${formatGovernanceMetric(cityQuality.global_score)} %`,
      coherence: `${formatGovernanceMetric(cityQuality.global_score)} %`,
      geometries_valides: `${formatGovernanceMetric(cityQuality.city_count ?? 11)}`,
      doublons: cityQuality.duplicate_count || 0,
      qualite_globale: cityQuality.global_score ?? 'Donnée non disponible',
    },
    {
      id: 'collectivity-quality',
      referentiel: 'Collectivités',
      completude: `${formatGovernanceMetric(collectivityQuality.global_score)} %`,
      coherence: `${formatGovernanceMetric(collectivityQuality.global_score)} %`,
      geometries_valides: `${formatGovernanceMetric((collectivityQuality.collectivity_count || 0) - (collectivityQuality.invalid_geometry_count || 0))}`,
      doublons: collectivityQuality.duplicate_count || 0,
      qualite_globale: collectivityQuality.global_score ?? 'Donnée non disponible',
    },
    {
      id: 'groupement-quality',
      referentiel: 'Groupements',
      completude: groupementAudit.national_reference?.coverage_percent ? `${groupementAudit.national_reference.coverage_percent} %` : 'Donnée non disponible',
      coherence: `${formatGovernanceMetric(groupementQuality.global_score)} %`,
      geometries_valides: `${formatGovernanceMetric((groupementQuality.groupement_count || 0) - (groupementQuality.invalid_geometry_count || 0))}`,
      doublons: groupementQuality.duplicate_count || 0,
      qualite_globale: groupementQuality.global_score ?? 'Donnée non disponible',
    },
    {
      id: 'locality-quality',
      referentiel: 'Localités',
      completude: `${formatGovernanceMetric(localityQuality.global_score)} %`,
      coherence: `${formatGovernanceMetric(localityQuality.global_score)} %`,
      geometries_valides: `${formatGovernanceMetric((localityQuality.locality_count || 0) - (localityQuality.invalid_geometry_count || 0))}`,
      doublons: localityQuality.duplicate_count || 0,
      qualite_globale: localityQuality.global_score ?? 'Donnée non disponible',
    },
    {
      id: 'json-availability',
      referentiel: 'Disponibilité JSON',
      completude: missingFiles ? 'Partielle' : 'Complète',
      coherence: missingFiles ? `${missingFiles} absent(s)` : 'OK',
      geometries_valides: '—',
      doublons: '—',
      qualite_globale: missingFiles ? 'Donnée non disponible' : 'Validé provisoirement',
    },
  ];
}

function buildOfficialSourceRows(sources) {
  return Object.entries(sources || {}).map(([key, source]) => ({
    id: `source-${key}`,
    nom: key,
    url_officielle: source.path,
    type_donnees: 'JSON référentiel',
    version: source.available ? 'Généré' : 'Donnée non disponible',
    derniere_synchronisation: source.available ? 'Chargé au runtime' : 'Donnée non disponible',
    responsable: 'Dashboard statique',
    documentation: source.label,
  }));
}

function buildRegistryRow(id, nom, type, expected, found, coverage, status, validation, quality, source) {
  return {
    id,
    nom,
    type,
    nombre_objets: `${formatGovernanceMetric(found)}${expected ? ` / ${formatGovernanceMetric(expected)}` : ''}`,
    source_officielle: source,
    version: coverage || 'Donnée non disponible',
    date_mise_a_jour: validation || 'Non publié',
    statut: normalizeDashboardStatus(status),
    qualite: quality ?? 'Donnée non disponible',
  };
}

function buildOfficialMarkdownPreview({ byLevel, referentielRows, anomalyRows, missingFiles, groupementCoverage }) {
  return [
    '# Référentiel National FDSU',
    '',
    `- Zones FDSU: ${byLevel.zone_fdsu}`,
    `- Provinces: ${byLevel.province}`,
    `- Territoires: ${byLevel.territoire}`,
    `- Villes: ${byLevel.ville}`,
    `- Collectivités: ${(byLevel.secteur || 0) + (byLevel.chefferie || 0)}`,
    `- Groupements: ${byLevel.groupement}`,
    `- Localités: ${byLevel.localite || 0}`,
    `- Couverture groupements: ${groupementCoverage}`,
    `- Fichiers absents: ${missingFiles}`,
    '',
    '## Statuts',
    ...referentielRows.map((row) => `- ${row.nom}: ${row.statut}`),
    '',
    '## Anomalies visibles',
    ...anomalyRows.slice(0, 20).map((row) => `- ${row.objet}: ${row.probleme || row.sans_rattachement}`),
  ].join('\n');
}

function computeDashboardQualityScore(scores) {
  const valid = scores.map(Number).filter((value) => Number.isFinite(value));
  if (!valid.length) return null;
  return Number((valid.reduce((total, value) => total + value, 0) / valid.length).toFixed(2));
}

function getOrCreateNode(map, key, template) {
  if (!map.has(key)) {
    map.set(key, template);
  }
  return map.get(key);
}

function hierarchyKey(...parts) {
  return parts.map((part) => normalizeDashboardText(part)).join('|');
}

function normalizeDashboardText(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase();
}

function normalizeDashboardStatus(value) {
  const text = normalizeDashboardText(value);
  if (text.includes('partiel')) return 'Partiel';
  if (text.includes('non publ')) return 'Non publié';
  if (text.includes('manuel') || text.includes('verifier') || text.includes('valider')) return 'À valider manuellement';
  if (text.includes('provis')) return 'Validé provisoirement';
  if (text.includes('valid')) return 'Validé';
  if (text.includes('official_candidate')) return 'Validé provisoirement';
  return value || 'Donnée non disponible';
}

function zoneLabelFromCode(code) {
  const labels = {
    ND: 'Zone Nord',
    SD: 'Zone Sud',
    CE: 'Zone Centre',
    OT: 'Zone Ouest',
    ET: 'Zone Est',
  };
  return labels[String(code || '').toUpperCase()] || `Zone FDSU ${code || 'INCONNU'}`;
}

function sortByName(left, right) {
  return String(left?.nom || left?.label || '').localeCompare(String(right?.nom || right?.label || ''), 'fr');
}

function sortTreeNodes(left, right) {
  return String(left.label || '').localeCompare(String(right.label || ''), 'fr');
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
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
  const id = node.id || buildExplorerNodeId(parent, level, label, node.code);
  const decoratedChildren = children.map((child) => decorateExplorerNode(child, { id }, { ...context, path }));
  const qualityScore = typeof node.quality === 'number' ? node.quality : getExplorerQualityScore(level, context.quality, context.anomalies);
  const status = node.status || getExplorerStatus(level, context.anomalies);

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
    qualityBadge: formatExplorerQualityBadge(qualityScore),
    qualityClass: getExplorerQualityClassFromScore(qualityScore),
    status,
    source: node.source || (level === 'rdc' ? 'Référentiel national consolidé' : 'Référentiel JSON officiel'),
    informationAvailable: getExplorerInformationAvailable(level),
    hierarchyPath: path,
    hierarchyLabel: path.join(' > '),
    statistics: buildExplorerNodeStatistics(level, context.statistics, context.byLevel, decoratedChildren.length, node.count),
    raw: node.raw || null,
    anomalies: Array.isArray(node.anomalies) ? node.anomalies : [],
    childStats: node.childStats || {},
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
  return getExplorerQualityClassFromScore(score);
}

function formatExplorerQualityBadge(score) {
  if (score === null || score === undefined || Number.isNaN(Number(score))) return 'Donnée non disponible';
  const normalizedScore = Math.max(0, Math.min(100, Math.round(Number(score))));
  if (normalizedScore >= 85) return `Excellent · ${normalizedScore}%`;
  if (normalizedScore >= 70) return `Bon · ${normalizedScore}%`;
  if (normalizedScore >= 50) return `À surveiller · ${normalizedScore}%`;
  return `Critique · ${normalizedScore}%`;
}

function getExplorerQualityClassFromScore(score) {
  if (score === null || score === undefined || Number.isNaN(Number(score))) return 'quality-warning';
  const normalizedScore = Math.max(0, Math.min(100, Math.round(Number(score))));
  if (normalizedScore >= 85) return 'quality-high';
  if (normalizedScore >= 70) return 'quality-medium';
  if (normalizedScore >= 50) return 'quality-warning';
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
    localite: '•',
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
    localite: 'Localité',
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
    localite: 'Niveau 5',
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
    localite: ['nom', 'type', 'niveau administratif', 'hiérarchie', 'statistiques', 'qualité', 'statut', 'source'],
  };

  return availability[String(level || '').toLowerCase()] || ['nom', 'type', 'hiérarchie'];
}

function getExplorerSearchTerm() {
  return governanceState.search.trim().toLowerCase();
}

function isExplorerNodeVisible(node, searchTerm) {
  const statusFilter = governanceState.statusFilter;
  const statusMatch = statusFilter ? String(node.status || '').toLowerCase() === statusFilter.toLowerCase() : true;
  if (!searchTerm) {
    return statusMatch || node.children.some((child) => isExplorerNodeVisible(child, searchTerm));
  }
  const haystack = [node.label, node.code, node.level, node.typeLabel, node.adminLevel, node.hierarchyLabel].join(' ').toLowerCase();
  if (haystack.includes(searchTerm) && statusMatch) {
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
    governanceElements.detailBody.querySelector('[data-open-node-profile]')?.addEventListener('click', () => {
      openEntityProfile(getLayerFromExplorerNode(selectedNode), propertiesFromExplorerNode(selectedNode));
    });
    return;
  }

  if (!governanceState.selectedRecord) {
    governanceElements.detailTitle.textContent = 'Aucun élément sélectionné';
    governanceElements.detailBody.innerHTML = '<div class="empty-detail">Sélectionnez une ligne pour afficher la fiche détaillée.</div>';
    return;
  }

governanceElements.detailTitle.textContent = `Élément ${governanceState.selectedRecord}`;
  const selectedRow = getGovernanceRowsForActiveTab().find((row) => String(row.id) === String(governanceState.selectedRecord));
  if (selectedRow) {
    governanceElements.detailTitle.textContent = selectedRow.nom || selectedRow.objet || selectedRow.referentiel || selectedRow.source || `Élément ${governanceState.selectedRecord}`;
    governanceElements.detailBody.innerHTML = Object.entries(selectedRow)
      .filter(([key]) => !['id', 'level'].includes(key))
      .map(([key, value]) => `<div class="detail-row"><span>${escapeHtml(formatDetailLabel(key))}</span><strong>${escapeHtml(formatGovernanceValue(value))}</strong></div>`)
      .join('');
    return;
  }

  governanceElements.detailBody.innerHTML = `
    <div class="detail-row"><span>Identifiant</span><strong>${escapeHtml(String(governanceState.selectedRecord))}</strong></div>
    <div class="detail-row"><span>État de connexion</span><strong>Donnée non disponible</strong></div>
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
    { label: 'Localité', value: getHierarchyValue(node, 'localite', 'village') },
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

  const anomalyInfo = [
    { label: 'Anomalies', value: node.anomalies?.length ? node.anomalies.join(' | ') : 'Aucune anomalie attachée au nœud' },
    { label: 'Statut qualité', value: node.status },
    { label: 'Contrôle manuel', value: node.status === 'À valider manuellement' ? 'Requis' : 'Non requis' },
  ];

  const childStatsInfo = Object.entries(node.childStats || {}).map(([key, value]) => ({
    label: formatDetailLabel(key),
    value,
  }));

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
          <button type="button" class="mode-chip" data-open-node-profile>Ouvrir fiche métier</button>
          <button type="button" class="mode-chip active" aria-pressed="true">${escapeHtml(modeLabel)}</button>
          <button type="button" class="mode-chip" disabled aria-disabled="true">Mode édition futur</button>
        </div>
      </div>

      <p class="territorial-file-intro">${escapeHtml(modeDescription)}</p>

      ${renderTerritorialSection('Informations générales', generalInfo, true)}
      ${renderTerritorialSection('Organisation administrative', administrativeInfo)}
      ${renderTerritorialSection('Géographie', geographicInfo)}
      ${renderTerritorialSection('Statistiques enfants', childStatsInfo.length ? childStatsInfo : [{ label: 'Enfants', value: node.statistics.children }])}
      ${renderTerritorialSection('Anomalies', anomalyInfo)}
      ${renderTerritorialSection('Développement', developmentInfo)}
      ${renderTerritorialSection('Télécommunications', telecomInfo)}
      ${renderTerritorialSection('Documentation', documentationInfo)}
      ${renderTerritorialSection('Historique', historicalInfo)}
      ${renderTerritorialSection('Sources', sourceInfo, false, true)}
    </div>
  `;
}

function getLayerFromExplorerNode(node) {
  return {
    zone_fdsu: 'zones',
    province: 'provinces',
    territoire: 'territoires',
    secteur: 'collectivites',
    chefferie: 'collectivites',
    cite: 'collectivites',
    groupement: 'groupements',
    village: 'villages',
    localite: 'villages',
  }[node.level] || 'provinces';
}

function propertiesFromExplorerNode(node) {
  return {
    nom: node.label,
    type: node.typeLabel || node.level,
    code: node.code,
    zone_fdsu: getHierarchyValue(node, 'zone_fdsu') || (node.level === 'zone_fdsu' ? node.code : ''),
    province: getHierarchyValue(node, 'province'),
    territoire: getHierarchyValue(node, 'territoire'),
    collectivite: getHierarchyValue(node, 'secteur', 'chefferie', 'cite'),
    groupement: getHierarchyValue(node, 'groupement'),
    localite: getHierarchyValue(node, 'localite', 'village'),
    qualite: node.qualityBadge,
    statut: node.status,
    source: node.source,
  };
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

function formatDetailLabel(key) {
  return String(key || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getHierarchyValue(node, ...levels) {
  const path = node.hierarchyPath || [];
  const indexes = {
    zone_fdsu: 1,
    province: 2,
    territoire: 3,
    secteur: 4,
    chefferie: 4,
    groupement: 5,
    village: 6,
    localite: 6,
  };
  for (const level of levels) {
    const index = indexes[String(level).toLowerCase()];
    if (path[index]) return path[index];
  }
  return 'Non renseigné';
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
    return 'Donnée non disponible';
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
    if (LOCAL_JSON_MODE) {
      renderSourceExplorerLocalSources();
    } else {
      renderSourceExplorerEmpty('Chargez un rapport JSON généré par scripts/explore_source.py pour explorer la source.');
    }
  }
}

function renderSourceExplorerLocalSources() {
  if (sourceExplorerElements.sourcePath) sourceExplorerElements.sourcePath.textContent = 'data/reports';
  if (sourceExplorerElements.sourceFormat) sourceExplorerElements.sourceFormat.textContent = 'JSON local';
  if (sourceExplorerElements.objectCount) sourceExplorerElements.objectCount.textContent = String(Object.keys(NATIONAL_REFERENTIAL_JSON_FILES).length);
  if (sourceExplorerElements.fieldCount) sourceExplorerElements.fieldCount.textContent = '—';
  if (sourceExplorerElements.folderCount) sourceExplorerElements.folderCount.textContent = '5';

  loadNationalReferentialJsonData().then((payload) => {
    const rows = Object.entries(payload.sources || {});
    if (sourceExplorerElements.catalogBody) {
      sourceExplorerElements.catalogBody.innerHTML = rows.map(([key, source]) => `
        <tr>
          <td>${escapeHtml(key)}</td>
          <td>JSON référentiel</td>
          <td>${escapeHtml(source.available ? '1' : '0')}</td>
          <td>—</td>
          <td>—</td>
          <td><span class="status-badge">${escapeHtml(source.label)}</span></td>
          <td>Dashboard JSON local</td>
          <td>${escapeHtml(source.path)}</td>
        </tr>
      `).join('');
    }
    if (sourceExplorerElements.dictionaryBody) {
      sourceExplorerElements.dictionaryBody.innerHTML = rows.map(([key, source]) => `
        <tr>
          <td>${escapeHtml(key)}</td>
          <td>${escapeHtml(source.available ? 'disponible' : 'absent')}</td>
          <td>${escapeHtml(source.available ? '1' : '0')}</td>
          <td>${escapeHtml(source.available ? '1' : '0')}</td>
          <td>${escapeHtml(source.available ? '0' : '1')}</td>
          <td>${escapeHtml(source.path)}</td>
        </tr>
      `).join('');
    }
    if (sourceExplorerElements.tagsContainer) {
      sourceExplorerElements.tagsContainer.innerHTML = '<span class="source-tag">Mode JSON local</span><span class="source-tag">Sans API</span><span class="source-tag">Sans BD</span>';
    }
  });
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

function renderAdministrativeHierarchyModule() {
  if (!referentielElements.tableBody) return;
  referentielElements.tableBody.innerHTML = '<tr><td colspan="7" class="empty-state">Chargement de l’arborescence JSON locale...</td></tr>';

  loadNationalReferentialJsonData()
    .then((payload) => {
      const report = decorateExplorerReport(buildNationalReferentialReportFromJson(payload));
      const rows = [];
      const searchTerm = referentielState.search || '';

      function visit(node, depth = 0) {
        const haystack = [node.label, node.code, node.level, node.typeLabel, node.hierarchyLabel].join(' ').toLowerCase();
        const childMatches = [];
        node.children.forEach((child) => {
          const before = rows.length;
          visit(child, depth + 1);
          if (rows.length > before) childMatches.push(child.id);
        });
        const selfMatches = !searchTerm || haystack.includes(searchTerm);
        if (!selfMatches && childMatches.length === 0) return;
        rows.splice(rows.length - childMatches.length, 0, { node, depth });
      }

      report.root.children.forEach((child) => visit(child, 0));

      const table = referentielElements.tableBody.closest('table');
      const thead = table?.querySelector('thead');
      if (thead) {
        thead.innerHTML = `
          <tr>
            <th>Hiérarchie</th>
            <th>Type</th>
            <th>Code</th>
            <th>Zone</th>
            <th>Parent</th>
            <th>Statut</th>
            <th>Qualité</th>
          </tr>
        `;
      }

      if (rows.length === 0) {
        referentielElements.tableBody.innerHTML = '<tr><td colspan="7" class="empty-state">Aucun élément trouvé.</td></tr>';
        return;
      }

      referentielElements.tableBody.innerHTML = rows
        .slice(0, 600)
        .map(({ node, depth }) => {
          const parent = node.parentId ? report.nodesById[node.parentId]?.label || '—' : 'RDC';
          const zone = node.hierarchyPath?.[1] || '—';
          return `
            <tr data-node-id="${escapeHtml(node.id)}">
              <td>${'&nbsp;'.repeat(depth * 4)}${escapeHtml(node.label)}</td>
              <td>${escapeHtml(node.typeLabel)}</td>
              <td>${escapeHtml(node.code || '—')}</td>
              <td>${escapeHtml(zone)}</td>
              <td>${escapeHtml(parent)}</td>
              <td><span class="status-badge">${escapeHtml(node.status)}</span></td>
              <td>${escapeHtml(node.qualityBadge)}</td>
            </tr>
          `;
        })
        .join('');

      referentielElements.tableBody.querySelectorAll('tr[data-node-id]').forEach((row) => {
        row.addEventListener('click', () => {
          const node = report.nodesById[row.dataset.nodeId];
          if (!node || !referentielElements.detailContainer) return;
          referentielElements.tableBody.querySelectorAll('tr').forEach((item) => item.classList.remove('selected'));
          row.classList.add('selected');
          referentielElements.detailContainer.innerHTML = buildTerritorialFileMarkup(node);
        });
      });

      const firstNode = rows[0]?.node;
      if (firstNode && referentielElements.detailContainer) {
        referentielElements.detailContainer.innerHTML = buildTerritorialFileMarkup(firstNode);
      }
    })
    .catch(() => {
      referentielElements.tableBody.innerHTML = '<tr><td colspan="7" class="empty-state">Donnée non disponible.</td></tr>';
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
  if (!LOCAL_JSON_MODE) {
    fetchJson('/dashboard/summary').then((summary) => {
      const data = summary || {};
      updateSummaryCard('stat-provinces')(Number(data.provinces) || 0);
      updateSummaryCard('stat-territoires')(Number(data.territories ?? data.territoires) || 0);
      updateSummaryCard('stat-collectivites')(Number(data.collectivites) || 0);
      updateSummaryCard('stat-groupements')(Number(data.groupements) || 0);
      updateSummaryCard('stat-villages')(Number(data.localites ?? data.villages) || 0);
      updateSummaryCard('stat-sites')(Number(data.sites) || 0);
      updateSummaryCard('stat-missions')(Number(data.missions) || 0);
      updateSummaryCard('stat-utilisateurs')(Number(data.users) || 0);
    });
    return;
  }

  getCount('/geo/provinces?limit=500').then(updateSummaryCard('stat-provinces'));
  getCount('/geo/territoires?limit=500').then(updateSummaryCard('stat-territoires'));
  getCount('/geo/collectivites?limit=500').then(updateSummaryCard('stat-collectivites'));
  getCount('/geo/groupements?limit=500').then(updateSummaryCard('stat-groupements'));
  getCount('/geo/villages?limit=500').then(updateSummaryCard('stat-villages'));
  updateSummaryCard('stat-sites')(0);
  updateSummaryCard('stat-missions')(0);
  updateSummaryCard('stat-utilisateurs')(0);
}

function getDatabaseStatus() {
  const apiStatusEl = document.querySelector('#api-status');
  const dbStatusEl = document.querySelector('#db-status');
  const dbSyncEl = document.querySelector('#db-sync');

  if (!apiStatusEl || !dbStatusEl || !dbSyncEl) return;
  apiStatusEl.textContent = LOCAL_JSON_MODE ? 'Mode JSON local' : 'Mode DB';
  dbStatusEl.textContent = LOCAL_JSON_MODE ? 'Non connectée' : 'Vérification...';

  if (!LOCAL_JSON_MODE) {
    Promise.resolve(API_HEALTH || fetchApiJson('/health'))
      .then((health) => {
        API_HEALTH = health;
        const databaseConnected = health?.mode === 'db' && health?.status === 'ok';
        apiStatusEl.textContent = databaseConnected ? 'Mode DB' : 'API FastAPI indisponible';
        dbStatusEl.textContent = databaseConnected ? 'Connectée' : (health?.database || 'Base non connectée');
        dbSyncEl.textContent = health?.loaded_at || new Date().toLocaleString('fr-FR');
      })
      .catch(() => {
        apiStatusEl.textContent = 'API FastAPI indisponible';
        dbStatusEl.textContent = 'Base non connectée';
        dbSyncEl.textContent = new Date().toLocaleString('fr-FR');
      });
    return;
  }

  loadLocalDashboardData()
    .then((data) => {
      dbSyncEl.textContent = data.loadedAt;
    })
    .catch(() => {
      dbSyncEl.textContent = new Date().toLocaleString('fr-FR');
    });
}

function getLastImports() {
  const lastImportEl = document.querySelector('#last-import');
  if (!lastImportEl) return;
  lastImportEl.textContent = 'Non disponible';
}

function getZones() {
  const source = LOCAL_JSON_MODE
    ? loadLocalDashboardData().then((data) => data.provinces)
    : fetchJson('/geo/provinces?limit=500').then((provinces) => asArray(provinces));

  source.then((provinces) => {
    if (!asArray(cartographyState.data.provinces).length) {
      cartographyState.data.provinces = asArray(provinces).map((item) => enrichFdsuNomenclature(item));
    }
    renderDashboardZonesSidebar();
  });
}

function getProvinces() {
  if (LOCAL_JSON_MODE) {
    return loadLocalDashboardData().then((data) => data.provinces);
  }
  return fetchJson('/geo/provinces?limit=500');
}

function getTerritoires() {
  if (LOCAL_JSON_MODE) {
    return loadLocalDashboardData().then((data) => makePlaceholderRows(data.counts.territoires, 'territoire'));
  }
  return fetchJson('/territories?limit=500');
}

function getCollectivites() {
  if (LOCAL_JSON_MODE) {
    return loadLocalDashboardData().then((data) => makePlaceholderRows(data.counts.collectivites, 'collectivite'));
  }
  return fetchJson('/geo/collectivites?limit=500');
}

function getGroupements() {
  if (LOCAL_JSON_MODE) {
    return loadLocalDashboardData().then((data) => makePlaceholderRows(data.counts.groupements, 'groupement'));
  }
  return fetchJson('/geo/groupements?limit=500');
}

function getVillages() {
  if (LOCAL_JSON_MODE) {
    return loadLocalDashboardData().then((data) => makePlaceholderRows(data.counts.localites, 'localite'));
  }
  return fetchJson('/localites?limit=500');
}

function getCount(endpoint) {
  if (LOCAL_JSON_MODE) {
    return loadLocalDashboardData().then((data) => {
      const key = getLocalCountKey(endpoint);
      return key ? data.counts[key] : 0;
    });
  }
  return fetchJson(endpoint).then((data) => {
    if (Array.isArray(data)) {
      return data.length;
    }
    return 0;
    });
}

function loadLocalDashboardData() {
  if (!dashboardState.localDataPromise) {
    dashboardState.localDataPromise = Promise.all([
      fetchReportJson('national_counter_registry.json'),
      fetchReportJson('province_official/province_referential_official.json'),
      fetchReportJson('locality_official/locality_quality_report.json'),
    ]).then(([registryResult, provinceResult, localityQualityResult]) => {
      const counters = registryResult.data?.registre_national_des_compteurs || {};
      const localityQuality = localityQualityResult.data || {};
      const provincesRaw = asArray(provinceResult.data?.province_referential);
      const provinces = provincesRaw.map((province, index) => ({
        id: index + 1,
        nom: province.nom || 'Non renseigné',
        code: province.code_officiel || province.canonical_id || '',
        zone: province.zone_fdsu || '',
        chef_lieu: province.chef_lieu || '',
        population: null,
        superficie: null,
        source: province.source || 'province_referential_official.json',
        statut: normalizeDashboardStatus(province.statut || 'Validé'),
        qualite: province.qualite,
      }));
      const zoneCounts = provinces.reduce((acc, province) => {
        const zone = String(province.zone || '').toUpperCase();
        if (acc[zone] !== undefined) acc[zone] += 1;
        return acc;
      }, { ND: 0, SD: 0, CE: 0, OT: 0, ET: 0 });

      return {
        loadedAt: new Date().toLocaleString('fr-FR'),
        counters,
        provinces,
        zoneCounts,
        counts: {
          zones: 5,
          provinces: counters.provinces?.nombre ?? provinces.length ?? 26,
          territoires: counters.territoires?.nombre ?? 145,
          villes: counters.villes?.nombre ?? 11,
          collectivites: counters.collectivites?.nombre ?? 733,
          groupements: counters.groupements?.trouve ?? counters.groupements?.nombre ?? 1681,
          localites: counters.localites?.nombre ?? localityQuality.locality_count ?? 26710,
          sites: 0,
          missions: 0,
          users: 0,
        },
      };
    });
  }
  return dashboardState.localDataPromise;
}

function getLocalCountKey(endpoint) {
  const text = String(endpoint || '').toLowerCase();
  if (text.includes('provinces')) return 'provinces';
  if (text.includes('territoires') || text.includes('territories')) return 'territoires';
  if (text.includes('collectivites')) return 'collectivites';
  if (text.includes('groupements')) return 'groupements';
  if (text.includes('villages') || text.includes('localites') || text.includes('localités')) return 'localites';
  if (text.includes('sites')) return 'sites';
  if (text.includes('missions')) return 'missions';
  if (text.includes('users') || text.includes('utilisateurs')) return 'users';
  return null;
}

function makePlaceholderRows(count, prefix) {
  return Array.from({ length: Number(count) || 0 }, (_, index) => ({ id: index + 1, nom: `${prefix}-${index + 1}` }));
}

function fetchJson(endpoint) {
  const localPath = String(endpoint || '');
  // Le contour RDC et les geodata generes sont servis par FastAPI (/geodata), pas par le serveur statique du dashboard.
  if (localPath.startsWith('/geodata/')) {
    return fetchApiJson(localPath).catch(() => null);
  }
  if (localPath.startsWith('/api/programs/')) {
    return fetchApiJson(localPath).catch(() => null);
  }
  if (localPath.startsWith('/api/telecom/')) {
    return fetchApiJson(localPath).catch(() => null);
  }
  if (localPath.startsWith('/api/analysis/')) {
    return fetchApiJson(localPath).catch(() => null);
  }
  if (localPath.startsWith('/api/decision/')) {
    return fetchApiJson(localPath).catch(() => null);
  }
  if (localPath.startsWith('/api/health/')) {
    return fetchApiJson(localPath).catch(() => null);
  }
  if (localPath.startsWith('/api/reference/')) {
    return fetchApiJson(localPath).catch(() => null);
  }
  if (localPath.startsWith('/programs/') || localPath.startsWith('/business/')) {
    if (canUseProgramDbData()) {
      if (localPath.endsWith('sites_40/sites_40.geojson')) {
        return fetchApiJson('/api/programs/sites40').catch(() => null);
      }
      if (localPath.endsWith('sites_300/sites_300.geojson')) {
        return fetchApiJson('/api/programs/sites300').catch(() => null);
      }
      if (localPath.endsWith('sites_40/sites_40.json')) {
        return fetchApiJson('/api/programs/sites40?format=panel').catch(() => null);
      }
      if (localPath.endsWith('sites_300/sites_300.json')) {
        return fetchApiJson('/api/programs/sites300?format=panel').catch(() => null);
      }
    }
    return fetch(localPath).then((response) => (response.ok ? response.json() : null)).catch(() => null);
  }
  if (LOCAL_JSON_MODE) {
    if (localPath.endsWith('.json') || localPath.endsWith('.geojson')) {
      return fetch(localPath).then((response) => (response.ok ? response.json() : null)).catch(() => null);
    }
    return Promise.resolve(null);
  }
  return fetchApiJson(endpoint).catch(() => null);
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

function getRouteFromHash() {
  return window.location.hash.replace('#', '').trim() || 'dashboard';
}

const nationalAssetRegistryState = { initialized: false, statistics: null };

function renderNationalAssetRegistryStatistics(stats) {
  const kpis = document.querySelector('#nfar-kpis');
  if (kpis) {
    const cards = [
      ['Actifs réels', stats.total_assets],
      ['Géolocalisés', stats.data_quality?.geolocated],
      ['Qualité géométrique', stats.data_quality?.geolocation_rate == null ? 'Non disponible' : `${stats.data_quality.geolocation_rate}%`],
      ['Population documentée', stats.population?.assets_documented],
      ['Population restante', stats.population?.assets_remaining],
      ['Couverture nationale', stats.population?.coverage_national ?? 'Non calculée'],
    ];
    kpis.innerHTML = cards.map(([label, value]) => `<article class="nfar-kpi"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value ?? 'Non disponible')}</strong></article>`).join('');
  }
  const programs = document.querySelector('#nfar-programs');
  if (programs) programs.innerHTML = Object.entries(stats.by_program || {}).map(([key, value]) => `<p><span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong></p>`).join('');
  const types = document.querySelector('#nfar-types');
  if (types) types.innerHTML = (stats.asset_types || []).map((row) => `<p data-status="${escapeHtml(row.status)}"><span>${escapeHtml(row.label)}</span><strong>${row.count == null ? escapeHtml(row.status) : escapeHtml(row.count)}</strong></p>`).join('');
}

function loadNationalAssetRegistryAssets() {
  const program = document.querySelector('#nfar-program-filter')?.value || '';
  const params = new URLSearchParams({ limit: '50' });
  if (program) params.set('program', program);
  const status = document.querySelector('#nfar-status');
  if (status) status.textContent = 'Chargement des actifs documentés…';
  return fetch(`${API_BASE_URL}/registry/assets?${params.toString()}`, { headers: { Accept: 'application/json' } })
    .then((response) => {
      if (!response.ok) throw new Error(`Registry API ${response.status}`);
      return response.json();
    })
    .then((payload) => {
      const body = document.querySelector('#nfar-assets-body');
      if (body) body.innerHTML = (payload.assets || []).map((asset) => `<tr data-asset-uuid="${escapeHtml(asset.uuid)}">
        <td><code>${escapeHtml(asset.business_code)}</code></td><td>${escapeHtml(asset.name)}</td>
        <td>${escapeHtml(asset.program)}</td><td>${escapeHtml(asset.territory?.territoire || asset.territory?.province || 'Non renseigné')}</td>
        <td>${escapeHtml(asset.data_status)}</td><td>${escapeHtml(asset.source?.path || 'Source référencée')}</td></tr>`).join('');
      if (status) status.textContent = `${payload._meta?.total ?? 0} actif(s) — 50 maximum affichés.`;
    })
    .catch((error) => { if (status) status.textContent = `Registry indisponible : ${error.message}`; });
}

function initializeNationalAssetRegistry() {
  if (!nationalAssetRegistryState.initialized) {
    nationalAssetRegistryState.initialized = true;
    document.querySelector('#nfar-program-filter')?.addEventListener('change', loadNationalAssetRegistryAssets);
  }
  Promise.all([
    fetch(`${API_BASE_URL}/registry/statistics`, { headers: { Accept: 'application/json' } }).then((r) => {
      if (!r.ok) throw new Error(`Registry API ${r.status}`);
      return r.json();
    }),
    loadNationalAssetRegistryAssets(),
  ]).then(([stats]) => {
    nationalAssetRegistryState.statistics = stats;
    renderNationalAssetRegistryStatistics(stats);
    const version = document.querySelector('#nfar-version');
    if (version) version.textContent = stats._meta?.registry || 'nfar-1.0.0';
  }).catch((error) => {
    const status = document.querySelector('#nfar-status');
    if (status) status.textContent = `Registry indisponible : ${error.message}`;
  });
}

const CENI_CATEGORY_STYLE = {
  UNCLASSIFIED: { color: '#94a3b8', icon: '❓', label: 'Non classifié' },
  PUBLIC_BUILDING: { color: '#8b5cf6', icon: '🏢', label: 'Bâtiment public' },
  SCHOOL: { color: '#3b82f6', icon: '🏫', label: 'École' },
  HEALTH_FACILITY: { color: '#10b981', icon: '🏥', label: 'Santé' },
  ADMINISTRATIVE_BUILDING: { color: '#f59e0b', icon: '🏛', label: 'Administration' },
  RELIGIOUS_BUILDING: { color: '#ec4899', icon: '◆', label: 'Religieux' },
  MARKET: { color: '#f97316', icon: '◫', label: 'Marché' },
  ENERGY: { color: '#eab308', icon: '⚡', label: 'Infrastructure énergétique' },
  TELECOM: { color: '#6366f1', icon: '⌁', label: 'Infrastructure de télécommunications' },
  ROAD: { color: '#78716c', icon: '↔', label: 'Infrastructure routière ou de transport' },
  CENI_SITE: { color: '#06b6d4', icon: '🗳', label: 'Site CENI' },
  VOTING_CENTER: { color: '#0ea5e9', icon: '🗳', label: 'Centre de vote' },
  REGISTRATION_CENTER: { color: '#14b8a6', icon: '✍', label: 'Enrôlement' },
  OTHER: { color: '#64748b', icon: '●', label: 'Autre' },
};
const ceniRegistryState = { initialized: false, map: null, layer: null, tile: null, sites: [], tableRows: [], total: 0, page: 1, pageSize: 50, sortKey: 'name', sortDirection: 1, hiddenColumns: new Set(), stats: null, loadToken: 0, defaultView: [[-13.6, 12.0], [5.5, 31.5]] };

function ceniFormat(value) { return value == null ? 'Non disponible' : Number(value).toLocaleString('fr-FR'); }
function ceniPercent(value, total) { return total ? `${(Number(value || 0) * 100 / total).toLocaleString('fr-FR', { maximumFractionDigits: 2 })} %` : 'Non disponible'; }
function ceniStyle(category) { return CENI_CATEGORY_STYLE[category] || CENI_CATEGORY_STYLE.OTHER; }
function ceniLabelFr(value, type) {
  if (type === 'category') return ceniStyle(value).label;
  const labels = { valid: 'Valide', suspect: 'À vérifier', invalid: 'Invalide', outside_country: 'Hors du pays', missing: 'Géométrie manquante', resolved: 'Résolu', partial: 'Partiel', unresolved: 'Non résolu' };
  return labels[value] || value || 'Non disponible';
}
function ceniRuleLabelFr(ruleId) {
  const labels = { SOURCE_CATEGORY: 'Catégorie officielle source', HEALTH_EXPLICIT: 'Santé explicite', HEALTH_ABBREVIATION: 'Abréviation sanitaire', SCHOOL_EXPLICIT: 'École explicite', SCHOOL_NAME: 'Nom d’établissement scolaire', SCHOOL_EP: 'Préfixe EP', SCHOOL_INST: 'Préfixe INST', ADMINISTRATION_EXPLICIT: 'Administration explicite', ADMINISTRATION_CONTEXT: 'Administration avec contexte', RELIGIOUS_EXPLICIT: 'Édifice religieux explicite', MARKET_EXPLICIT: 'Marché explicite', TELECOM_EXPLICIT: 'Télécommunications explicites', TELECOM_OPERATOR_INFRA: 'Opérateur avec indice d’infrastructure', ENERGY_EXPLICIT: 'Énergie explicite', TRANSPORT_EXPLICIT: 'Transport explicite', ROAD_CONTEXT: 'Route avec contexte', PUBLIC_BUILDING_EXPLICIT: 'Bâtiment public explicite', CENI_EXPLICIT: 'Site CENI explicite', VOTING_EXPLICIT: 'Centre de vote explicite', REGISTRATION_EXPLICIT: 'Centre d’enrôlement explicite', CS_CONTEXT_SCOLAIRE: 'CS avec contexte scolaire', CS_CONTEXT_SANTÉ: 'CS avec contexte sanitaire' };
  return labels[ruleId] || 'Aucune règle applicable';
}
function ceniBadge(value, type) { return `<span class="ceni-badge ceni-badge--${escapeHtml(type)}" data-value="${escapeHtml(value)}">${escapeHtml(ceniLabelFr(value, type))}</span>`; }

function renderCeniDetail(site) {
  const drawer = document.querySelector('#ceni-detail'); const host = document.querySelector('#ceni-detail-body');
  if (!drawer || !host || !site) return;
  const admin = site.administrative_attachment || {}; const source = site.source || {}; const raw = site.raw_properties || {};
  host.innerHTML = `<header class="ceni-detail-head"><span class="ceni-detail-icon" style="--ceni-category:${ceniStyle(site.normalized_category).color}">${ceniStyle(site.normalized_category).icon}</span><div><p class="panel-label">Fiche institutionnelle CENI</p><h3>${escapeHtml(site.name || 'Sans nom')}</h3><p>${ceniBadge(site.normalized_category, 'category')} ${ceniBadge(site.geometry_status, 'quality')}</p></div></header>
    <section><h4>Classification sémantique française</h4><dl><dt>Nom source</dt><dd>${escapeHtml(site.name || 'Non fourni')}</dd><dt>Nom normalisé</dt><dd>${escapeHtml(site.normalized_name || 'Non disponible')}</dd><dt>Catégorie source</dt><dd>${escapeHtml(site.source_category || 'Non fournie')}</dd><dt>Catégorie déduite</dt><dd>${escapeHtml(site.normalized_category_label_fr || ceniStyle(site.normalized_category).label)}</dd><dt>Méthode</dt><dd>${escapeHtml(site.classification_method || 'Classification lexicale en français')}</dd><dt>Mot-clé détecté</dt><dd>${escapeHtml(site.matched_keyword || 'Aucun')}</dd><dt>Confiance</dt><dd>${Math.round(Number(site.classification_confidence || 0) * 100)} % · ${escapeHtml(site.confidence_label_fr || 'Insuffisante')}</dd><dt>Justification</dt><dd>${escapeHtml(site.classification_justification)}</dd><dt>Règle</dt><dd>${escapeHtml(ceniRuleLabelFr(site.matched_rule_id))}</dd><dt>Statut de revue</dt><dd>${escapeHtml(site.review_status || 'Non revu')}</dd><dt>Version du moteur</dt><dd>${escapeHtml(site.engine_version || 'Non disponible')}</dd></dl></section>
    <section><h4>Rattachement territorial</h4><dl><dt>Province</dt><dd>${escapeHtml(admin.province || 'Non résolue')}</dd><dt>Territoire</dt><dd>${escapeHtml(admin.territory || 'Non résolu')}</dd><dt>Collectivité</dt><dd>${escapeHtml(admin.collectivity || 'Non résolue')}</dd><dt>Groupement</dt><dd>${escapeHtml(admin.groupement || 'Non résolu')}</dd><dt>Localité</dt><dd>${escapeHtml(admin.locality || 'Non résolue')}</dd><dt>Méthode</dt><dd>${escapeHtml(admin.method || 'Non disponible')}</dd></dl></section>
    <section><h4>Géométrie et qualité</h4><dl><dt>Coordonnées</dt><dd>${site.latitude == null ? 'Non disponibles' : `${Number(site.latitude).toFixed(6)}, ${Number(site.longitude).toFixed(6)}`}</dd><dt>Qualité</dt><dd>${escapeHtml(site.geometry_status)}</dd><dt>Doublon</dt><dd>${escapeHtml(site.duplicate?.status || 'none')} · ${site.duplicate?.group_size || 1} occurrence(s)</dd></dl></section>
    <section><h4>Provenance et historique</h4><dl><dt>Source</dt><dd>${escapeHtml(source.file || '')}</dd><dt>Hash SHA-256</dt><dd><code>${escapeHtml(source.sha256 || '')}</code></dd><dt>Membre KML</dt><dd>${escapeHtml(source.kml_member || '')}</dd><dt>Historique</dt><dd>Import déterministe v1.0 · source conservée · aucune fusion automatique</dd></dl></section>
    <details><summary>Toutes les propriétés source</summary><pre>${escapeHtml(JSON.stringify(raw, null, 2))}</pre></details>`;
  drawer.classList.add('is-open'); drawer.setAttribute('aria-hidden', 'false');
}

function closeCeniDetail() { const drawer = document.querySelector('#ceni-detail'); drawer?.classList.remove('is-open'); drawer?.setAttribute('aria-hidden', 'true'); }

function ceniMapIcon(site, count = 1) {
  if (count > 1) return window.L.divIcon({ className: 'ceni-map-div-icon', html: `<span class="ceni-cluster">${ceniFormat(count)}</span>`, iconSize: [38, 38], iconAnchor: [19, 19] });
  const style = ceniStyle(site.normalized_category);
  return window.L.divIcon({ className: 'ceni-map-div-icon', html: `<span class="ceni-symbol" style="--ceni-category:${style.color}" title="${escapeHtml(style.label)}">${style.icon}</span>`, iconSize: [30, 30], iconAnchor: [15, 15] });
}

function renderCeniViewport() {
  const state = ceniRegistryState; if (!state.map || !state.layer) return;
  const bounds = state.map.getBounds(); const zoom = state.map.getZoom();
  const visible = state.sites.filter((site) => site.latitude != null && site.longitude != null && bounds.contains([site.latitude, site.longitude]));
  const counter = document.querySelector('#ceni-visible-count'); if (counter) counter.textContent = ceniFormat(visible.length);
  state.layer.clearLayers();
  if (zoom < 9) {
    const cell = zoom <= 5 ? 1.2 : zoom === 6 ? 0.65 : zoom === 7 ? 0.32 : 0.16; const groups = new Map();
    visible.forEach((site) => { const key = `${Math.round(site.latitude / cell)}:${Math.round(site.longitude / cell)}`; const group = groups.get(key) || []; group.push(site); groups.set(key, group); });
    Array.from(groups.values()).slice(0, 4000).forEach((group) => {
      const lat = group.reduce((sum, site) => sum + Number(site.latitude), 0) / group.length; const lon = group.reduce((sum, site) => sum + Number(site.longitude), 0) / group.length;
      const marker = window.L.marker([lat, lon], { icon: ceniMapIcon(group[0], group.length), keyboard: true }).addTo(state.layer);
      if (group.length === 1) marker.bindTooltip(escapeHtml(group[0].name || group[0].asset_uid)).on('click', () => renderCeniDetail(group[0]));
      else marker.bindTooltip(`${ceniFormat(group.length)} objets`).on('click', () => state.map.setView([lat, lon], Math.min(12, zoom + 2)));
    });
  } else {
    visible.slice(0, 4000).forEach((site) => window.L.marker([site.latitude, site.longitude], { icon: ceniMapIcon(site), keyboard: true }).bindTooltip(escapeHtml(site.name || site.asset_uid)).on('click', () => renderCeniDetail(site)).addTo(state.layer));
  }
}

function ensureCeniMap() {
  const host = document.querySelector('#ceni-map'); if (!host || !window.L || ceniRegistryState.map) return;
  const map = window.L.map(host, { zoomControl: true, preferCanvas: true }).fitBounds(ceniRegistryState.defaultView);
  ceniRegistryState.map = map; ceniRegistryState.tile = window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap', maxZoom: 18, crossOrigin: true }).addTo(map);
  ceniRegistryState.layer = window.L.layerGroup().addTo(map); map.on('moveend zoomend', renderCeniViewport);
}

function renderCeniLegend() {
  const host = document.querySelector('#ceni-map-legend'); if (!host || !ceniRegistryState.stats) return;
  const counts = ceniRegistryState.stats.categories || {};
  host.innerHTML = `<strong>Légende</strong>${Object.entries(CENI_CATEGORY_STYLE).filter(([id]) => counts[id]).map(([id, style]) => `<span><i style="--ceni-category:${style.color}">${style.icon}</i>${escapeHtml(style.label)} <em>${ceniFormat(counts[id])}</em></span>`).join('')}`;
}

function ceniBarRows(entries, total, limit = 6) { return entries.sort((a, b) => Number(b[1]) - Number(a[1])).slice(0, limit).map(([label, value]) => `<div class="ceni-bar-row"><p><span>${escapeHtml(label)}</span><strong>${ceniFormat(value)}</strong></p><i><b style="width:${Math.max(2, Number(value) * 100 / (total || 1))}%"></b></i></div>`).join(''); }

function renderCeniAnalytics(stats) {
  const total = Number(stats.total_raw || 0); const valid = Number(stats.geometry_quality?.valid || 0); const suspect = Number(stats.suspect || 0); const rejected = Number(stats.rejected || 0);
  const validPct = total ? valid * 100 / total : 0; const suspectPct = total ? suspect * 100 / total : 0;
  const donut = document.querySelector('#ceni-quality-donut'); if (donut) { donut.style.setProperty('--valid', `${validPct}%`); donut.style.setProperty('--suspect', `${validPct + suspectPct}%`); donut.querySelector('span').innerHTML = `<strong>${validPct.toLocaleString('fr-FR', { maximumFractionDigits: 1 })}%</strong><small>valides</small>`; }
  const qualityLegend = document.querySelector('#ceni-quality-legend'); if (qualityLegend) qualityLegend.innerHTML = `<p><i class="is-valid"></i>Valides <strong>${ceniFormat(valid)}</strong></p><p><i class="is-suspect"></i>Suspects <strong>${ceniFormat(suspect)}</strong></p><p><i class="is-rejected"></i>Rejetés <strong>${ceniFormat(rejected)}</strong></p>`;
  const attachments = Object.entries(stats.administrative_attachments || {}); const attachmentHost = document.querySelector('#ceni-attachment-bars'); if (attachmentHost) attachmentHost.innerHTML = ceniBarRows(attachments, total, 4);
  const categoryHost = document.querySelector('#ceni-category-bars'); if (categoryHost) categoryHost.innerHTML = ceniBarRows(Object.entries(stats.categories || {}).map(([key, value]) => [ceniStyle(key).label, value]), total, 8);
  const classification = stats.classification || {}; const before = Number(classification.unclassified_before || total); const after = Number(classification.unclassified_after || 0);
  const progress = document.querySelector('#ceni-classification-progress'); if (progress) progress.innerHTML = ceniBarRows([['Non classifiés avant', before], ['Non classifiés après', after], ['Objets classifiés', Number(classification.reduction_count || 0)]], before, 3) + `<p class="ceni-classification-rate"><strong>${ceniPercent(classification.reduction_count, before)}</strong> de réduction</p>`;
  const confidence = document.querySelector('#ceni-confidence-bars'); if (confidence) confidence.innerHTML = ceniBarRows(Object.entries(classification.confidence || {}), total, 5);
  const rules = document.querySelector('#ceni-rule-bars'); if (rules) rules.innerHTML = ceniBarRows(Object.entries(classification.top_rules || {}).map(([key, value]) => [key === 'Aucune règle' ? 'Aucune règle applicable' : ceniRuleLabelFr(key), value]), total, 5);
  const review = document.querySelector('#ceni-review-count'); if (review) review.innerHTML = `<strong>${ceniFormat(classification.review_status?.['À vérifier'] || 0)}</strong><span> classifications prudentes à soumettre à validation humaine</span>`;
  [['#ceni-top-provinces', stats.provinces], ['#ceni-top-territories', stats.territories]].forEach(([selector, data]) => { const host = document.querySelector(selector); if (host) host.innerHTML = Object.entries(data || {}).filter(([name]) => name !== 'unresolved').sort((a, b) => Number(b[1]) - Number(a[1])).slice(0, 5).map(([name, value]) => `<li><span>${escapeHtml(name)}</span><strong>${ceniFormat(value)}</strong></li>`).join(''); });
}

function ceniTableValue(site, key) { const admin = site.administrative_attachment || {}; return key === 'province' ? admin.province || '' : key === 'territory' ? admin.territory || '' : site[key] ?? ''; }

function renderCeniTable() {
  const state = ceniRegistryState; const needle = document.querySelector('#ceni-table-search')?.value?.trim().toLocaleLowerCase('fr') || '';
  let rows = needle ? state.sites.filter((site) => `${site.asset_uid} ${site.name} ${site.normalized_category} ${site.administrative_attachment?.province || ''} ${site.administrative_attachment?.territory || ''}`.toLocaleLowerCase('fr').includes(needle)) : [...state.sites];
  rows.sort((a, b) => String(ceniTableValue(a, state.sortKey)).localeCompare(String(ceniTableValue(b, state.sortKey)), 'fr', { numeric: true }) * state.sortDirection); state.tableRows = rows;
  const pages = Math.max(1, Math.ceil(rows.length / state.pageSize)); state.page = Math.min(state.page, pages); const start = (state.page - 1) * state.pageSize; const pageRows = rows.slice(start, start + state.pageSize);
  const body = document.querySelector('#ceni-sites-body'); if (body) body.innerHTML = pageRows.map((site) => { const admin = site.administrative_attachment || {}; return `<tr data-ceni-uid="${escapeHtml(site.asset_uid)}" tabindex="0"><td data-ceni-column="asset_uid"><code>${escapeHtml(site.asset_uid)}</code></td><td data-ceni-column="name"><strong>${escapeHtml(site.name || 'Sans nom')}</strong></td><td data-ceni-column="normalized_category">${ceniBadge(site.normalized_category, 'category')}</td><td data-ceni-column="province">${ceniBadge(admin.province || 'Non résolue', 'province')}</td><td data-ceni-column="territory">${escapeHtml(admin.territory || 'Non résolu')}</td><td data-ceni-column="geometry_status">${ceniBadge(site.geometry_status, 'quality')}</td><td data-ceni-column="classification_confidence">${ceniBadge(`${Math.round(Number(site.classification_confidence || 0) * 100)} %`, 'confidence')}</td></tr>`; }).join('');
  body?.querySelectorAll('[data-ceni-uid]').forEach((row) => { const open = () => renderCeniDetail(pageRows.find((site) => site.asset_uid === row.dataset.ceniUid)); row.addEventListener('click', open); row.addEventListener('keydown', (event) => { if (event.key === 'Enter') open(); }); });
  state.hiddenColumns.forEach((key) => document.querySelectorAll(`[data-ceni-column="${key}"]`).forEach((cell) => cell.setAttribute('hidden', '')));
  const label = document.querySelector('#ceni-page-label'); if (label) label.textContent = `Page ${state.page} / ${pages}`; const prev = document.querySelector('#ceni-prev'); const next = document.querySelector('#ceni-next'); if (prev) prev.disabled = state.page <= 1; if (next) next.disabled = state.page >= pages;
  const status = document.querySelector('#ceni-status'); if (status) status.textContent = `${ceniFormat(rows.length)} objet(s) · lignes ${rows.length ? start + 1 : 0}–${Math.min(start + state.pageSize, rows.length)}`;
}

function renderCeniKpis(stats) {
  const total = Number(stats.total_raw || 0); const cards = [
    { label: 'Total brut', value: total, note: 'Placemark', icon: '◉', tone: 'cyan' },
    { label: 'Intégrés', value: stats.integrated, note: ceniPercent(stats.integrated, total), icon: '✓', tone: 'green' },
    { label: 'Rejetés', value: stats.rejected, note: 'Hors emprise', icon: '!', tone: 'red' },
    { label: 'Suspects', value: stats.suspect, note: 'Géométries', icon: '△', tone: 'amber' },
    { label: 'Doublons', value: stats.duplicates?.exact, note: 'Conservés', icon: '⧉', tone: 'violet' },
    { label: 'Rattachements', value: stats.administrative_attachments?.resolved, note: 'Collectivité / Territoire', icon: '⌖', tone: 'blue' },
  ]; const host = document.querySelector('#ceni-kpis'); if (host) host.innerHTML = cards.map((card) => `<article class="ceni-kpi ceni-kpi--${card.tone}"><span class="ceni-kpi-icon">${card.icon}</span><div><span>${escapeHtml(card.label)}</span><strong>${ceniFormat(card.value)}</strong><small>${escapeHtml(card.note)}</small></div></article>`).join('');
}

function renderCeniMap() { ensureCeniMap(); renderCeniLegend(); renderCeniViewport(); }

async function loadCeniSites() {
  const token = ++ceniRegistryState.loadToken; const base = new URLSearchParams(); [['q', '#ceni-search'], ['category', '#ceni-category'], ['province', '#ceni-province'], ['quality', '#ceni-quality']].forEach(([key, selector]) => { const value = document.querySelector(selector)?.value?.trim(); if (value) base.set(key, value); });
  ceniRegistryState.sites = []; ceniRegistryState.page = 1; const status = document.querySelector('#ceni-status'); if (status) status.textContent = 'Chargement progressif du référentiel CENI…';
  let offset = 0; let total = 0; const limit = 5000;
  try {
    do { const params = new URLSearchParams(base); params.set('limit', String(limit)); params.set('offset', String(offset)); const response = await fetch(`${API_BASE_URL}/api/ceni/sites?${params}`, { headers: { Accept: 'application/json' } }); if (!response.ok) throw new Error(`CENI API ${response.status}`); const payload = await response.json(); if (token !== ceniRegistryState.loadToken) return; total = Number(payload.total || 0); ceniRegistryState.sites.push(...(payload.sites || [])); offset += payload.sites?.length || 0; ceniRegistryState.total = total; renderCeniTable(); renderCeniMap(); await new Promise((resolve) => window.requestAnimationFrame(resolve)); } while (offset < total && offset > 0);
  } catch (error) { if (status) status.textContent = `Référentiel CENI indisponible : ${error.message}`; }
}

function resetCeniFilters() { ['#ceni-search', '#ceni-category', '#ceni-province', '#ceni-quality', '#ceni-table-search'].forEach((selector) => { const element = document.querySelector(selector); if (element) element.value = ''; }); loadCeniSites(); }

function exportCeniMapImage() {
  const map = ceniRegistryState.map; if (!map) return; const size = map.getSize(); const canvas = document.createElement('canvas'); canvas.width = size.x; canvas.height = size.y; const ctx = canvas.getContext('2d'); ctx.fillStyle = '#0b1220'; ctx.fillRect(0, 0, size.x, size.y); const bounds = map.getBounds();
  ceniRegistryState.sites.filter((site) => site.latitude != null && bounds.contains([site.latitude, site.longitude])).slice(0, 12000).forEach((site) => { const point = map.latLngToContainerPoint([site.latitude, site.longitude]); ctx.fillStyle = ceniStyle(site.normalized_category).color; ctx.beginPath(); ctx.arc(point.x, point.y, 2.2, 0, Math.PI * 2); ctx.fill(); });
  ctx.fillStyle = '#e2e8f0'; ctx.font = 'bold 18px sans-serif'; ctx.fillText('Référentiel National CENI', 18, 28); ctx.font = '12px sans-serif'; ctx.fillText(`${document.querySelector('#ceni-visible-count')?.textContent || 0} objets visibles · export SIG-FDSU RDC`, 18, 48); const link = document.createElement('a'); link.download = 'referentiel-national-ceni.png'; link.href = canvas.toDataURL('image/png'); link.click();
}

function handleCeniMapAction(action) { const map = ceniRegistryState.map; if (!map) return; if (action === 'fullscreen') { document.querySelector('#ceni-map-stage')?.classList.toggle('is-fullscreen'); window.setTimeout(() => map.invalidateSize(), 100); } else if (action === 'reset') map.fitBounds(ceniRegistryState.defaultView); else if (action === 'basemap') document.querySelector('#ceni-map-stage')?.classList.toggle('is-light'); else if (action === 'export') exportCeniMapImage(); else if (action === 'locate' && navigator.geolocation) navigator.geolocation.getCurrentPosition((position) => map.setView([position.coords.latitude, position.coords.longitude], 12)); }

function initializeCeniTableControls() {
  const columns = [{ id: 'asset_uid', label: 'Identifiant' }, { id: 'name', label: 'Nom source' }, { id: 'normalized_category', label: 'Catégorie' }, { id: 'province', label: 'Province' }, { id: 'territory', label: 'Territoire' }, { id: 'geometry_status', label: 'Qualité' }, { id: 'classification_confidence', label: 'Confiance' }];
  const picker = document.querySelector('#ceni-column-picker'); if (picker) picker.innerHTML = columns.map((column) => `<label><input type="checkbox" value="${column.id}" checked>${column.label}</label>`).join('');
  picker?.querySelectorAll('input').forEach((input) => input.addEventListener('change', () => { if (input.checked) ceniRegistryState.hiddenColumns.delete(input.value); else ceniRegistryState.hiddenColumns.add(input.value); renderCeniTable(); }));
  document.querySelectorAll('#ceni-table th[data-sort]').forEach((header) => header.addEventListener('click', () => { const key = header.dataset.sort; if (ceniRegistryState.sortKey === key) ceniRegistryState.sortDirection *= -1; else { ceniRegistryState.sortKey = key; ceniRegistryState.sortDirection = 1; } document.querySelectorAll('#ceni-table th').forEach((item) => item.removeAttribute('data-direction')); header.dataset.direction = ceniRegistryState.sortDirection > 0 ? 'asc' : 'desc'; renderCeniTable(); }));
}

function initializeCeniRegistry() {
  if (!ceniRegistryState.initialized) {
    ceniRegistryState.initialized = true; document.querySelector('#ceni-apply')?.addEventListener('click', loadCeniSites); document.querySelector('#ceni-reset')?.addEventListener('click', resetCeniFilters); document.querySelector('#ceni-search')?.addEventListener('keydown', (event) => { if (event.key === 'Enter') loadCeniSites(); });
    let searchTimer; document.querySelector('#ceni-table-search')?.addEventListener('input', () => { window.clearTimeout(searchTimer); searchTimer = window.setTimeout(() => { ceniRegistryState.page = 1; renderCeniTable(); }, 120); });
    document.querySelector('#ceni-prev')?.addEventListener('click', () => { ceniRegistryState.page -= 1; renderCeniTable(); }); document.querySelector('#ceni-next')?.addEventListener('click', () => { ceniRegistryState.page += 1; renderCeniTable(); }); document.querySelector('#ceni-page-size')?.addEventListener('change', (event) => { ceniRegistryState.pageSize = Number(event.target.value); ceniRegistryState.page = 1; renderCeniTable(); }); document.querySelector('#ceni-detail-close')?.addEventListener('click', closeCeniDetail); document.querySelectorAll('[data-ceni-map]').forEach((button) => button.addEventListener('click', () => handleCeniMapAction(button.dataset.ceniMap))); initializeCeniTableControls();
  }
  Promise.all([fetch(`${API_BASE_URL}/api/ceni/statistics`).then((response) => response.json()), fetch(`${API_BASE_URL}/api/ceni/categories`).then((response) => response.json())]).then(([stats, categoryPayload]) => {
    ceniRegistryState.stats = stats; renderCeniKpis(stats); renderCeniAnalytics(stats); const category = document.querySelector('#ceni-category'); if (category && category.options.length === 1) category.insertAdjacentHTML('beforeend', (categoryPayload.categories || []).map((row) => `<option value="${escapeHtml(row.id)}">${escapeHtml(ceniStyle(row.id).label)} (${ceniFormat(row.count)})</option>`).join('')); const province = document.querySelector('#ceni-province'); if (province && province.options.length === 1) province.insertAdjacentHTML('beforeend', Object.keys(stats.provinces || {}).filter((name) => name !== 'unresolved').sort().map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)} (${ceniFormat(stats.provinces[name])})</option>`).join('')); const provenance = document.querySelector('#ceni-provenance'); if (provenance) provenance.innerHTML = `<strong>Source officielle</strong> · KMZ File Sites CENI.kmz · <span>SHA-256 ${escapeHtml(stats._meta?.source_sha256 || 'Non disponible')}</span> · Institution CENI · Domaine INSTITUTIONAL`; const version = document.querySelector('#ceni-version'); if (version) version.textContent = stats._meta?.version || 'v1.0.0'; renderCeniLegend();
  });
  loadCeniSites(); window.setTimeout(() => ceniRegistryState.map?.invalidateSize(), 0);
}

const nationalTerritorialIntelligenceState = { initialized: false, profile: null };

function ntieValue(profile, id) {
  return profile?.indicator_index?.[id]?.value;
}

function renderNationalTerritorialIntelligence(profile) {
  const entity = profile.entity || {};
  const kpiIds = ['population', 'mobile_coverage', 'population_uncovered', 'localities', 'fdsu_sites', 'ccn'];
  const kpis = document.querySelector('#ntie-kpis');
  if (kpis) kpis.innerHTML = kpiIds.map((id) => {
    const indicator = profile.indicator_index?.[id] || {};
    const value = indicator.value == null ? 'Non disponible' : `${Number(indicator.value).toLocaleString('fr-FR')} ${indicator.unit || ''}`;
    return `<article class="ntie-kpi"><span>${escapeHtml(indicator.label || id)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(indicator.source || 'Source non disponible')}</small></article>`;
  }).join('');
  const score = document.querySelector('#ntie-score');
  if (score) score.innerHTML = `<p><strong>${escapeHtml(profile.score?.label || 'Score')}</strong> : ${profile.score?.value == null ? 'Non calcule' : escapeHtml(profile.score.value)}</p><p>${escapeHtml(profile.score?.explanation || '')}</p>`;
  const quality = document.querySelector('#ntie-quality');
  if (quality) quality.innerHTML = `<p><strong>${profile.data_quality?.available || 0}</strong> indicateurs disponibles sur ${profile.data_quality?.total || 0}</p><p>${escapeHtml(profile.data_quality?.rule || '')}</p>`;
  const evolution = document.querySelector('#ntie-evolution');
  if (evolution) evolution.innerHTML = `<div class="table-wrapper"><table class="data-table"><thead><tr><th>Scenario</th><th>Actifs documentes</th><th>Couverture</th><th>Methode</th></tr></thead><tbody>${(profile.evolution || []).map((row) => `<tr><td>${escapeHtml(row.label)}</td><td>${row.documented_assets ?? '—'}</td><td>${row.coverage_rate_pct == null ? 'Non projetee' : `${row.coverage_rate_pct} %`}</td><td>${escapeHtml(row.method)}</td></tr>`).join('')}</tbody></table></div>`;
  const map = document.querySelector('#ntie-map');
  if (map) map.innerHTML = `<p><strong>${escapeHtml(entity.admin_type || entity.type || '')} — ${escapeHtml(entity.name || '')}</strong></p><p>${entity.has_geometry ? 'Geometrie territoriale disponible.' : 'Geometrie non disponible.'}</p><p>La carte detaillee reutilise le rendu multi-echelle existant.</p>`;
  const explainability = document.querySelector('#ntie-explainability');
  if (explainability) explainability.innerHTML = `<p>Moteurs federes : ${escapeHtml((profile.explainability?.dependencies || []).join(', '))}</p><p>${escapeHtml(profile.explainability?.limits || 'Valeurs absentes conservees a null.')}</p>`;
  const version = document.querySelector('#ntie-version');
  if (version) version.textContent = profile._meta?.engine || 'ntie-1.0.0';
}

function loadNationalTerritorialIntelligence() {
  const input = document.querySelector('#ntie-profile-id');
  const status = document.querySelector('#ntie-status');
  const entityId = String(input?.value || 'TERRITOIRE-05-002').trim();
  if (status) status.textContent = 'Chargement du profil territorial…';
  return fetch(`${API_BASE_URL}/territorial-profile/${encodeURIComponent(entityId)}`, { headers: { Accept: 'application/json' } })
    .then((response) => {
      if (!response.ok) throw new Error(`NTIE API ${response.status}`);
      return response.json();
    })
    .then((profile) => {
      nationalTerritorialIntelligenceState.profile = profile;
      renderNationalTerritorialIntelligence(profile);
      if (status) status.textContent = `${profile.entity?.admin_type || profile.entity?.type} — ${profile.entity?.name}`;
      return profile;
    })
    .catch((error) => {
      if (status) status.textContent = `Profil indisponible : ${error.message}`;
      throw error;
    });
}

function initializeNationalTerritorialIntelligence() {
  if (!nationalTerritorialIntelligenceState.initialized) {
    nationalTerritorialIntelligenceState.initialized = true;
    document.querySelector('#ntie-load')?.addEventListener('click', () => loadNationalTerritorialIntelligence().catch(() => {}));
  }
  return loadNationalTerritorialIntelligence().catch(() => null);
}

function getModuleFromRoute(route) {
  const raw = String(route || '').trim();
  if (raw.startsWith('decision-detail') || raw.startsWith('decision-workspace') || raw.startsWith('territorial-twin')) {
    return 'decision_detail';
  }
  if (raw.startsWith('decision-scenario')) return 'centre_decision';
  if (raw.startsWith('decision-case') || raw.startsWith('spatial-impact') || raw.startsWith('analyse-impact-territorial') || raw.startsWith('coverage-detail') || raw.startsWith('ccn-detail')) {
    return 'decision_experience';
  }
  if (raw.startsWith('territorial-intelligence/')) return 'territorial_intelligence';
  if (raw.startsWith('national-territorial-intelligence')) return 'national_territorial_intelligence';
  const base = raw.split('?')[0].split('/')[0];
  return ROUTE_TO_MODULE[raw] || ROUTE_TO_MODULE[base] || 'dashboard';
}

function navigateTo(moduleOrRoute) {
  const raw = String(moduleOrRoute || '').trim();
  if (
    raw.startsWith('decision-detail/')
    || raw.startsWith('decision-workspace/')
    || raw.startsWith('territorial-twin/')
    || raw.startsWith('decision-scenario/')
    || raw.startsWith('decision-case/')
    || raw.startsWith('spatial-impact/')
    || raw.startsWith('analyse-impact-territorial/')
    || raw.startsWith('coverage-detail/')
    || raw.startsWith('ccn-detail/')
    || raw.startsWith('territorial-intelligence/')
    || raw.includes('/')
  ) {
    if (getRouteFromHash() === raw) {
      setActiveModule(getModuleFromRoute(raw));
      return;
    }
    window.location.hash = raw;
    return;
  }
  const moduleKey = getModuleFromRoute(raw);
  const route = MODULE_TO_ROUTE[moduleKey] || 'dashboard';
  if (getRouteFromHash() === route) {
    setActiveModule(moduleKey);
    return;
  }
  window.location.hash = route;
}

function renderRouteFromHash() {
  setActiveModule(getModuleFromRoute(getRouteFromHash()));
}

navigationItems.forEach((item) => {
  item.addEventListener('click', () => {
    navigateTo(item.dataset.route || item.dataset.module);
  });
});

const quickActions = document.querySelectorAll('.quick-actions button');
quickActions.forEach((button) => {
  button.addEventListener('click', () => {
    navigateTo(button.dataset.route || button.dataset.module);
  });
});

window.addEventListener('hashchange', renderRouteFromHash);

// Exposition minimale pour les tests E2E Playwright (lecture seule).
window.cartographyState = cartographyState;
window.setCartographyFocusMode = setCartographyFocusMode;
window.openCartographyDrawerPanel = openCartographyDrawerPanel;
window.nationalMapState = nationalMapState;
window.dashboardViewState = dashboardViewState;
window.openDashboardDetailPage = openDashboardDetailPage;
function openSites300ProgramOnMap() {
  navigateTo('map');
  const activate = () => {
    if (!cartographyState.initialized || !cartographyState.map || !cartographyState.layers.sites_300) {
      window.setTimeout(activate, 120);
      return;
    }
    ensureFdsuSitesProgramLayerLoaded('sites_300').then(() => {
      const layer = cartographyState.layers.sites_300;
      if ((layer?.getLayers?.().length ?? 0) === 0) {
        window.setTimeout(activate, 120);
        return;
      }
      const checkbox = document.querySelector('input[data-layer="sites_300"]');
      setCartographyLayerVisible('sites_300', true, checkbox).finally(() => {
        if (checkbox && !checkbox.checked) checkbox.checked = true;
        if (!cartographyState.map.hasLayer(layer)) layer.addTo(cartographyState.map);
        refreshCartographicLayerPresentation();
        openCartographyDrawerPanel('layers');
        fitLayerBounds(layer);
      });
    });
  };
  activate();
}

function openSites40ProgramOnMap() {
  navigateTo('map');
  const activate = () => {
    if (!cartographyState.initialized || !cartographyState.map || !cartographyState.layers.sites_40) {
      window.setTimeout(activate, 120);
      return;
    }
    ensureFdsuSitesProgramLayerLoaded('sites_40').then(() => {
      const layer = cartographyState.layers.sites_40;
      if ((layer?.getLayers?.().length ?? 0) === 0) {
        window.setTimeout(activate, 120);
        return;
      }
      const checkbox = document.querySelector('input[data-layer="sites_40"]');
      setCartographyLayerVisible('sites_40', true, checkbox).finally(() => {
        if (checkbox && !checkbox.checked) checkbox.checked = true;
        if (!cartographyState.map.hasLayer(layer)) layer.addTo(cartographyState.map);
        refreshCartographicLayerPresentation();
        openCartographyDrawerPanel('layers');
        fitLayerBounds(layer);
      });
    });
  };
  activate();
}

function openDecisionSiteOnMap(focus = {}) {
  const siteId = focus.site_id || focus.id;
  const program = String(focus.program_code || '').toLowerCase();
  const layerKey = program.includes('300') ? 'sites_300' : (program.includes('40') ? 'sites_40' : 'sites_40');
  navigateTo('map');
  const activate = () => {
    if (!cartographyState.initialized || !cartographyState.map) {
      window.setTimeout(activate, 120);
      return;
    }
    const ensure = layerKey === 'sites_300'
      ? ensureFdsuSitesProgramLayerLoaded('sites_300')
      : ensureFdsuSitesProgramLayerLoaded('sites_40');
    ensure.then(() => {
      const layer = cartographyState.layers[layerKey];
      if (!layer) {
        window.setTimeout(activate, 120);
        return;
      }
      const checkbox = document.querySelector(`input[data-layer="${layerKey}"]`);
      setCartographyLayerVisible(layerKey, true, checkbox).finally(() => {
        if (checkbox && !checkbox.checked) checkbox.checked = true;
        if (!cartographyState.map.hasLayer(layer)) layer.addTo(cartographyState.map);
        refreshCartographicLayerPresentation();
        openCartographyDrawerPanel('layers');

        let matched = null;
        layer.eachLayer((lyr) => {
          if (matched) return;
          const props = lyr.feature?.properties || {};
          const candidates = [props.site_id, props.id, props.site_code, props.code, props.business_id]
            .map((v) => String(v ?? ''));
          if (siteId && candidates.includes(String(siteId))) matched = lyr;
          if (focus.site_code && candidates.includes(String(focus.site_code))) matched = lyr;
        });

        if (matched) {
          try {
            if (matched.getLatLng) {
              cartographyState.map.setView(matched.getLatLng(), Math.max(cartographyState.map.getZoom(), 10));
            } else if (matched.getBounds) {
              cartographyState.map.fitBounds(matched.getBounds().pad(0.3));
            }
            if (typeof matched.openPopup === 'function') matched.openPopup();
            if (typeof matched.fire === 'function') matched.fire('click');
          } catch (_e) { /* */ }
          return;
        }

        const lat = Number(focus.latitude);
        const lon = Number(focus.longitude);
        if (Number.isFinite(lat) && Number.isFinite(lon)) {
          cartographyState.map.setView([lat, lon], Math.max(cartographyState.map.getZoom(), 10));
          return;
        }
        fitLayerBounds(layer);
      });
    });
  };
  activate();
}

const ntilState = { initialized: false };

async function loadNtilRegistry() {
  const q = document.querySelector('#ntil-search')?.value?.trim() || '';
  const status = document.querySelector('#ntil-status')?.value || '';
  const message = document.querySelector('#ntil-status-message');
  try {
    const payload = await fetchApiJson(`/api/ntil/registry?q=${encodeURIComponent(q)}&status=${encodeURIComponent(status)}&limit=100`);
    const body = document.querySelector('#ntil-registry-body');
    if (body) body.innerHTML = (payload.terms || []).map((term) => `<tr data-ntil-term="${escapeDnai(term.id)}"><td><strong>${escapeDnai(term.term)}</strong></td><td>${escapeDnai(term.expansion || 'À valider')}</td><td>${escapeDnai(term.family || 'Non déterminée')}</td><td><span class="panel-badge">${escapeDnai(term.status)}</span></td><td>${Math.round(Number(term.confidence || 0) * 100)} %</td><td>${escapeDnai((term.referentials || []).join(', '))}</td></tr>`).join('');
    if (message) message.textContent = `${payload.total || 0} terme(s) trouvé(s).`;
  } catch (error) { if (message) message.textContent = `Registre NTIL indisponible : ${error.message}`; }
}

async function initializeNtilModule() {
  if (!ntilState.initialized) {
    ntilState.initialized = true;
    document.querySelector('#ntil-search-button')?.addEventListener('click', loadNtilRegistry);
    document.querySelector('#ntil-search')?.addEventListener('keydown', (event) => { if (event.key === 'Enter') loadNtilRegistry(); });
    document.querySelector('#ntil-status')?.addEventListener('change', loadNtilRegistry);
  }
  try {
    const payload = await fetchApiJson('/api/ntil/dashboard');
    const stats = payload.statistics || {}; const quality = payload.quality || {};
    const score = document.querySelector('#ntil-score'); if (score) score.textContent = `${Number(quality.terminology_quality_score || 0).toFixed(1)}/100`;
    const kpis = [['Termes',stats.total_terms],['Validés',stats.validated_terms],['En attente',stats.pending_terms],['Inconnus',stats.unknown_terms],['Synonymes',stats.synonyms],['Familles',stats.families]];
    const host = document.querySelector('#ntil-kpis'); if (host) host.innerHTML = kpis.map(([label,value]) => `<article class="ntil-kpi"><strong>${escapeDnai(value)}</strong><span>${escapeDnai(label)}</span></article>`).join('');
    const bars = document.querySelector('#ntil-quality-bars'); if (bars) bars.innerHTML = (quality.quality_by_referential || []).map((row) => `<div class="ntil-bar-row"><span>${escapeDnai(row.referential)}</span><div class="ntil-bar"><i style="width:${Math.max(0,Math.min(100,Number(row.score || 0)))}%"></i></div><strong>${Number(row.score || 0).toFixed(1)}</strong></div>`).join('');
    const families = document.querySelector('#ntil-family-chart'); if (families) families.innerHTML = ((payload.families || {}).families || []).map((row) => `<div class="ntil-family"><span>${escapeDnai(row.name)}</span><strong>${escapeDnai(row.terms)}</strong></div>`).join('');
    const discoveries = document.querySelector('#ntil-discoveries'); if (discoveries) discoveries.innerHTML = ((payload.discoveries || {}).items || []).map((row) => `<div class="ntil-discovery"><strong>${escapeDnai(row.term)}</strong><br><small>${escapeDnai(row.status)} · ${escapeDnai(row.justification)}</small></div>`).join('');
    const history = document.querySelector('#ntil-history'); if (history) history.innerHTML = ((payload.history || {}).items || []).map((row) => `<div class="ntil-history-item"><strong>v${escapeDnai(row.version)}</strong> · ${escapeDnai(row.date)}<br><small>${escapeDnai(row.change)}</small></div>`).join('');
  } catch (error) { const message=document.querySelector('#ntil-status-message'); if(message) message.textContent=`Dashboard NTIL indisponible : ${error.message}`; }
  await loadNtilRegistry();
}

const dnaiState = { initialized: false };

function escapeDnai(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
}

async function loadDnaiEntries() {
  const query = document.querySelector('#dnai-search')?.value?.trim() || '';
  const status = document.querySelector('#dnai-status');
  if (status) status.textContent = 'Chargement du dictionnaire…';
  try {
    const payload = await fetchApiJson(`/api/dnai/search?q=${encodeURIComponent(query)}`);
    const body = document.querySelector('#dnai-results');
    if (body) body.innerHTML = (payload.entries || []).map((entry) => `<tr><td><strong>${escapeDnai(entry.abbreviation)}</strong></td><td>${escapeDnai(entry.official_expansion)}</td><td>${escapeDnai(entry.family)}</td><td>${escapeDnai([...(entry.variants || []), ...(entry.synonyms || [])].join(', ') || '—')}</td><td>${Math.round(Number(entry.confidence || 0) * 100)} %</td><td>${escapeDnai(entry.source)}</td></tr>`).join('');
    if (status) status.textContent = `${payload.count || 0} entrée(s) affichée(s).`;
  } catch (error) { if (status) status.textContent = `DNAI indisponible : ${error.message}`; }
}

async function initializeDnaiModule() {
  if (!dnaiState.initialized) {
    dnaiState.initialized = true;
    document.querySelector('#dnai-search-button')?.addEventListener('click', loadDnaiEntries);
    document.querySelector('#dnai-search')?.addEventListener('keydown', (event) => { if (event.key === 'Enter') loadDnaiEntries(); });
  }
  try {
    const [stats, pending] = await Promise.all([fetchApiJson('/api/dnai/statistics'), fetchApiJson('/api/dnai/pending-validations')]);
    const kpis = [
      ['Abréviations publiées', stats.abbreviations], ['Variantes reconnues', stats.recognized_variants],
      ['Familles', Object.keys(stats.families || {}).length], ['À valider', stats.ambiguities],
    ];
    const host = document.querySelector('#dnai-kpis');
    if (host) host.innerHTML = kpis.map(([label, value]) => `<article class="dnai-kpi"><strong>${escapeDnai(value)}</strong><span>${escapeDnai(label)}</span></article>`).join('');
    const pendingHost = document.querySelector('#dnai-pending-list');
    if (pendingHost) pendingHost.innerHTML = (pending.items || []).map((item) => `<p class="dnai-pending-item"><strong>${escapeDnai(item.abbreviation)}</strong> — ${escapeDnai(item.reason)}</p>`).join('');
  } catch (_error) { /* le message détaillé est rendu par loadDnaiEntries */ }
  await loadDnaiEntries();
}

window.openDecisionSiteOnMap = openDecisionSiteOnMap;
window.openSites40ProgramOnMap = openSites40ProgramOnMap;
window.openSites300ProgramOnMap = openSites300ProgramOnMap;
window.backToDashboard = backToDashboard;
window.platformState = platformState;
window.goBackContext = goBackNationalContext;
window.goBackNationalContext = goBackNationalContext;
window.resetDashboardNationalView = resetDashboardNationalView;
window.renderNationalContextMap = renderNationalContextMap;

window.SigFdsuShared = {
  API_BASE_URL,
  fetchApiJson,
  fetchJson,
  canUseProgramDbData,
  canUseTelecomDbData: canUseProgramDbData,
  styleRdcBoundaryFeature,
  styleProvinceFeature,
  styleTerritoryFeature,
  styleCollectivitesFeature,
  makePointMarker,
  openSites40ProgramOnMap,
  openSites300ProgramOnMap,
};

function bootSigFdsuApplication() {
  initializeApplication();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootSigFdsuApplication);
} else {
  bootSigFdsuApplication();
}
