/**
 * SigMapTooltips — factory centralisée d'infobulles cartographiques FDSU
 * Survol = comprendre rapidement · Clic = ouvrir une analyse métier (jamais /api/...)
 */
(function initSigMapTooltips(global) {
  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function isPresentable(value) {
    if (value === null || value === undefined) return false;
    const text = String(value).trim();
    if (!text) return false;
    const lower = text.toLowerCase();
    if (['null', 'undefined', 'nan', 'feature', 'point', '—', '-', '0'].includes(lower)) return false;
    return true;
  }

  function pick(props, keys) {
    const source = props || {};
    for (const key of keys) {
      if (Object.prototype.hasOwnProperty.call(source, key) && isPresentable(source[key])) {
        return source[key];
      }
    }
    return null;
  }

  function formatPopulation(value) {
    if (value == null || value === '') return null;
    const num = Number(String(value).replace(/\s/g, '').replace(',', '.'));
    if (!Number.isFinite(num) || num <= 0) return null;
    return Math.round(num).toLocaleString('fr-FR');
  }

  function formatDistance(value) {
    if (value == null || value === '') return null;
    const num = Number(value);
    if (!Number.isFinite(num) || num < 0) return null;
    if (num >= 1000) return `${(num / 1000).toFixed(1).replace('.0', '')} km`;
    return `${Math.round(num)} m`;
  }

  function formatScore(value) {
    if (value == null || value === '') return null;
    const num = Number(value);
    if (!Number.isFinite(num)) return String(value);
    return `${Math.round(num * 10) / 10}`;
  }

  const KIND_META = {
    site: { label: 'Site FDSU', icon: '📡' },
    site_fdsu: { label: 'Site FDSU', icon: '📡' },
    sites: { label: 'Site FDSU', icon: '📡' },
    sites_40: { label: 'Site 40 FDSU', icon: '🟣' },
    sites_300: { label: 'Site 300 FDSU', icon: '🔵' },
    sites_all: { label: 'Site FDSU', icon: '📡' },
    ccn: { label: 'Centre communautaire', icon: '🏛️' },
    uncovered_locality: { label: 'Localité non couverte', icon: '⚠️' },
    covered_locality: { label: 'Localité couverte', icon: '✅' },
    village: { label: 'Localité', icon: '📍' },
    villages: { label: 'Localité', icon: '📍' },
    territory: { label: 'Territoire', icon: '📍' },
    territoire: { label: 'Territoire', icon: '📍' },
    territoires: { label: 'Territoire', icon: '📍' },
    province: { label: 'Province', icon: '📍' },
    provinces: { label: 'Province', icon: '📍' },
    collectivite: { label: 'Collectivité', icon: '📍' },
    collectivites: { label: 'Collectivité', icon: '📍' },
    groupement: { label: 'Groupement', icon: '📍' },
    groupements: { label: 'Groupement', icon: '📍' },
    zone: { label: 'Zone FDSU', icon: '🗺️' },
    zones: { label: 'Zone FDSU', icon: '🗺️' },
    health: { label: 'Établissement de santé', icon: '🏥' },
    school: { label: 'École', icon: '🏫' },
    market: { label: 'Marché', icon: '🛒' },
    administration: { label: 'Administration', icon: '🏛️' },
    telecom: { label: 'Infrastructure télécom', icon: '📶' },
    telecom_vodacom: { label: 'Couverture Vodacom', icon: '📶' },
    telecom_orange: { label: 'Couverture Orange', icon: '📶' },
    telecom_fiber_mw: { label: 'Lien micro-ondes / fibre', icon: '📡' },
    telecom_fiberco: { label: 'Backbone fibre', icon: '🧵' },
    telecom_fttx: { label: 'Accès fibre (FTTx)', icon: '🧵' },
    fiber: { label: 'Fibre optique', icon: '🧵' },
    fibre: { label: 'Fibre optique', icon: '🧵' },
    backbone: { label: 'Backbone', icon: '🧵' },
    road: { label: 'Route', icon: '🛣️' },
    cluster: { label: 'Regroupement', icon: '⬤' },
    spatial_match: { label: 'Correspondance spatiale', icon: '🔗' },
    link: { label: 'Liaison actif–besoin', icon: '🔗' },
    mission_candidate: { label: 'Candidat mission', icon: '🎯' },
    mission: { label: 'Mission', icon: '🎯' },
    missions: { label: 'Mission', icon: '🎯' },
  };

  const LAYER_TO_KIND = {
    sites_40: 'sites_40',
    sites_300: 'sites_300',
    sites_all: 'site',
    sites: 'site',
    villages: 'village',
    territoires: 'territory',
    provinces: 'province',
    collectivites: 'collectivite',
    groupements: 'groupement',
    zones: 'zone',
    missions: 'mission',
    telecom_vodacom: 'telecom_vodacom',
    telecom_orange: 'telecom_orange',
    telecom_fiber_mw: 'fiber',
    telecom_fiberco: 'backbone',
    telecom_fttx: 'fiber',
    asset_need_matches: 'spatial_match',
    spatial_relations: 'spatial_match',
  };

  function normalizeProps(featureOrData) {
    if (!featureOrData) return {};
    if (featureOrData.properties && typeof featureOrData.properties === 'object') {
      return { ...featureOrData.properties };
    }
    if (typeof featureOrData === 'object') return { ...featureOrData };
    return {};
  }

  function resolveKind(entityType, props) {
    if (entityType && KIND_META[entityType]) return entityType;
    if (entityType && LAYER_TO_KIND[entityType]) return LAYER_TO_KIND[entityType];
    const inferred = pick(props, ['kind', 'entity_type', 'feature_kind', 'layer_key']);
    if (inferred && KIND_META[inferred]) return inferred;
    if (inferred && LAYER_TO_KIND[inferred]) return LAYER_TO_KIND[inferred];
    if (pick(props, ['coverage_status']) === 'uncovered' || props.is_uncovered) return 'uncovered_locality';
    if (String(pick(props, ['relation_type']) || '').includes('SERVES') || props.kind === 'link') return 'spatial_match';
    return entityType || 'village';
  }

  function pushLine(lines, label, value) {
    if (!isPresentable(value)) return;
    lines.push(`${label} : ${value}`);
  }

  function buildLines(kind, props) {
    const p = props || {};
    const lines = [];
    const resolved = resolveKind(kind, p);

    if (['site', 'site_fdsu', 'sites', 'sites_40', 'sites_300', 'sites_all'].includes(resolved)) {
      pushLine(lines, 'Code', pick(p, ['site_code', 'code', 'official_code', 'business_id']));
      pushLine(lines, 'Localité', pick(p, ['localite', 'locality', 'village', 'name', 'nom', 'site_name']));
      pushLine(lines, 'Programme', pick(p, ['programme', 'program_code', 'program']) || (resolved === 'sites_300' ? 'Sites 300' : resolved === 'sites_40' ? 'Sites 40' : null));
      const score = formatScore(pick(p, ['priority_score', 'score']));
      if (score) pushLine(lines, 'Score', score);
      pushLine(lines, 'Priorité', pick(p, ['priority_level_label', 'priority_level', 'priorite', 'priority_status']));
      pushLine(lines, 'Facteur principal', pick(p, ['top_factor', 'main_factor', 'primary_factor']));
      const pop = formatPopulation(pick(p, ['population_cible', 'population', 'pop_cible', 'target_population', 'impact_total_population']));
      if (pop) pushLine(lines, 'Population cible / impact', pop);
      pushLine(lines, 'Province', pick(p, ['province', 'province_name']));
      pushLine(lines, 'Territoire', pick(p, ['territoire', 'territory', 'territoire_name']));
      pushLine(lines, 'Statut de donnée', pick(p, ['data_status', 'data_quality', 'quality_label', 'statut_donnee', 'status', 'operational_status']));
      return lines.slice(0, 7);
    }

    if (resolved === 'uncovered_locality') {
      pushLine(lines, 'Nom', pick(p, ['nom', 'name', 'localite', 'locality_name']));
      pushLine(lines, 'Province', pick(p, ['province', 'province_name']));
      pushLine(lines, 'Territoire', pick(p, ['territoire', 'territory', 'territoire_name']));
      const pop = formatPopulation(pick(p, ['population', 'pop', 'population_estimee']));
      if (pop) pushLine(lines, 'Population', pop);
      pushLine(lines, 'Priorité', pick(p, ['priority_level_label', 'priority_level', 'priorite', 'priority']));
      pushLine(lines, 'Catégorie', pick(p, ['category', 'categorie', 'need_category', 'coverage_category']));
      const distRaw = pick(p, ['distance_utile_m', 'distance_m', 'distance_to_site_m', 'nearest_site_distance_m']);
      const distKm = pick(p, ['distance_km']);
      if (distRaw != null) pushLine(lines, 'Distance utile', formatDistance(distRaw));
      else if (distKm != null) pushLine(lines, 'Distance utile', `${distKm} km`);
      pushLine(lines, 'Statut de donnée', pick(p, ['data_quality', 'quality_label', 'data_status']) || 'Référentiel des besoins');
      return lines;
    }

    if (resolved === 'covered_locality' || resolved === 'village' || resolved === 'villages') {
      pushLine(lines, 'Groupement', pick(p, ['groupement']));
      pushLine(lines, 'Territoire', pick(p, ['territoire', 'territory']));
      const pop = formatPopulation(pick(p, ['population', 'pop']));
      if (pop) pushLine(lines, 'Population', pop);
      pushLine(lines, 'Couverture', pick(p, ['coverage_status', 'couverture', 'status']));
      return lines;
    }

    if (resolved === 'ccn') {
      pushLine(lines, 'Code', pick(p, ['business_id', 'code', 'ccn_code', 'official_code']));
      pushLine(lines, 'Nom', pick(p, ['name', 'nom']));
      pushLine(lines, 'Type', pick(p, ['ccn_type', 'type', 'category', 'type_label']));
      pushLine(lines, 'Statut', pick(p, ['status', 'statut', 'operational_status']));
      const pop = formatPopulation(pick(p, ['population_desservie', 'population_served', 'population']));
      if (pop) pushLine(lines, 'Population desservie', pop);
      pushLine(lines, 'Site associé', pick(p, ['site_code', 'associated_site', 'site_fdsu', 'linked_site']));
      pushLine(lines, 'Territoire', pick(p, ['territoire', 'territory']));
      return lines;
    }

    if (resolved === 'territory' || resolved === 'territoire' || resolved === 'territoires') {
      pushLine(lines, 'Province', pick(p, ['province', 'province_name']));
      pushLine(lines, 'Zone FDSU', pick(p, ['fdsu_zone', 'zone', 'zone_fdsu']));
      if (p.fdsu_sites_count != null) pushLine(lines, 'Sites FDSU', p.fdsu_sites_count);
      if (p.uncovered_localities_count != null) pushLine(lines, 'Localités non couvertes', p.uncovered_localities_count);
      const popRest = formatPopulation(pick(p, ['population_uncovered', 'population_restante', 'population_remaining', 'population']));
      if (popRest) pushLine(lines, 'Population restante', popRest);
      pushLine(lines, 'NDCI', pick(p, ['ndci', 'ndci_score', 'coverage_index']));
      pushLine(lines, 'Qualité des données', pick(p, ['data_quality', 'quality_label', 'cdqs', 'quality_score']));
      return lines;
    }

    if (resolved === 'province' || resolved === 'provinces') {
      pushLine(lines, 'Code', pick(p, ['code_province_fdsu', 'code']));
      pushLine(lines, 'Zone FDSU', pick(p, ['fdsu_zone', 'zone']));
      if (p.fdsu_sites_count != null) pushLine(lines, 'Sites FDSU', p.fdsu_sites_count);
      if (p.uncovered_localities_count != null) pushLine(lines, 'Localités non couvertes', p.uncovered_localities_count);
      pushLine(lines, 'NDCI', pick(p, ['ndci', 'ndci_score']));
      const pop = formatPopulation(pick(p, ['population', 'pop']));
      if (pop) pushLine(lines, 'Population', pop);
      return lines;
    }

    if (resolved === 'health') {
      pushLine(lines, 'Type', pick(p, ['facility_type_name', 'facility_type_code', 'type']));
      pushLine(lines, 'Territoire', pick(p, ['territoire', 'territory', 'province_name', 'province']));
      pushLine(lines, 'Source', pick(p, ['data_source', 'source_label', 'source']) || 'Référentiel Santé');
      const dist = formatDistance(pick(p, ['distance_m', 'distance_to_selected_site_m']));
      if (dist) pushLine(lines, 'Distance', dist);
      pushLine(lines, 'Qualité des données', pick(p, ['data_quality', 'quality_score', 'quality_label']));
      return lines;
    }

    if (resolved === 'school') {
      pushLine(lines, 'Type', pick(p, ['type', 'school_type']));
      pushLine(lines, 'Territoire', pick(p, ['territoire', 'territory']));
      const dist = formatDistance(pick(p, ['distance_m']));
      if (dist) pushLine(lines, 'Distance', dist);
      return lines;
    }

    if (resolved === 'market' || resolved === 'administration') {
      pushLine(lines, 'Type', pick(p, ['type', 'category']));
      pushLine(lines, 'Territoire', pick(p, ['territoire', 'territory']));
      const dist = formatDistance(pick(p, ['distance_m']));
      if (dist) pushLine(lines, 'Distance', dist);
      return lines;
    }

    if (String(resolved).startsWith('telecom') || resolved === 'fiber' || resolved === 'fibre' || resolved === 'backbone' || resolved === 'telecom') {
      pushLine(lines, 'Opérateur', pick(p, ['operator_name', 'operator_code', 'operateur', 'owner']));
      pushLine(lines, 'Type', pick(p, ['infra_type', 'line_type', 'polygon_type', 'infra_category', 'type']));
      pushLine(lines, 'Technologie', pick(p, ['technology', 'technologie']));
      pushLine(lines, 'Statut', pick(p, ['status', 'statut', 'operational_status']));
      const dist = formatDistance(pick(p, ['distance_to_selected_site_m', 'distance_m']));
      if (dist) pushLine(lines, 'Distance utile', dist);
      pushLine(lines, 'Qualité de la donnée', pick(p, ['data_quality', 'quality_label']) || 'Référentiel télécom');
      return lines;
    }

    if (resolved === 'road') {
      pushLine(lines, 'Type', pick(p, ['road_type', 'type', 'classe']));
      pushLine(lines, 'État', pick(p, ['status', 'etat', 'condition']));
      pushLine(lines, 'Province', pick(p, ['province']));
      return lines;
    }

    if (resolved === 'spatial_match' || resolved === 'link') {
      pushLine(lines, 'Actif', pick(p, ['asset_business_id', 'code', 'site_code', 'name', 'asset_name']));
      pushLine(lines, 'Besoin', pick(p, ['locality_name', 'need_name', 'need_id', 'name']));
      pushLine(lines, 'Relation', pick(p, ['relation_type', 'relation']));
      const dist = formatDistance(pick(p, ['distance_m']));
      if (dist) pushLine(lines, 'Distance', dist);
      const pop = formatPopulation(pick(p, ['population', 'population_impacted', 'impact_total_population']));
      if (pop) pushLine(lines, 'Population impactée', pop);
      pushLine(lines, 'Confiance', pick(p, ['confidence_level', 'confidence']));
      return lines;
    }

    if (resolved === 'mission_candidate' || resolved === 'mission' || resolved === 'missions') {
      pushLine(lines, 'Statut', pick(p, ['statut', 'status', 'etat']));
      pushLine(lines, 'Priorité', pick(p, ['priority_level', 'priorite']));
      pushLine(lines, 'Date', pick(p, ['date', 'date_mission', 'started_at']));
      return lines;
    }

    if (resolved === 'cluster') {
      pushLine(lines, 'Objets', pick(p, ['count', 'childCount', 'n']));
      pushLine(lines, 'Type dominant', pick(p, ['dominant_type', 'type']));
      return lines;
    }

    [
      ['Code', pick(p, ['code', 'business_id', 'official_code'])],
      ['Province', pick(p, ['province', 'province_name'])],
      ['Territoire', pick(p, ['territoire', 'territory'])],
      ['Statut', pick(p, ['status', 'statut', 'operational_status'])],
    ].forEach(([label, value]) => pushLine(lines, label, value));
    if (!lines.length) lines.push('Données contextuelles à compléter');
    return lines;
  }

  function buildTitle(kind, props) {
    const resolved = resolveKind(kind, props);
    return pick(props, ['nom', 'name', 'libelle', 'infra_name', 'line_name', 'polygon_name', 'site_name', 'localite', 'code'])
      || KIND_META[resolved]?.label
      || 'Entité';
  }

  function buildHtml(kind, props, options = {}) {
    const resolved = resolveKind(kind, props);
    const meta = KIND_META[resolved] || { label: 'Entité', icon: '📍' };
    const title = buildTitle(kind, props);
    const lines = buildLines(kind, props);
    const hint = options.hint === false
      ? ''
      : `<span class="map-smart-tooltip-hint">${escapeHtml(options.hint || 'Cliquer pour analyser en détail')}</span>`;
    return `
      <div class="map-smart-tooltip">
        <div class="map-smart-tooltip-title">
          <span class="map-smart-tooltip-icon">${meta.icon}</span>
          <span>${escapeHtml(title)}</span>
        </div>
        <span class="map-smart-tooltip-type">${escapeHtml(meta.label)}</span>
        ${lines.map((line) => `<span class="map-smart-tooltip-line">${escapeHtml(line)}</span>`).join('')}
        ${hint}
      </div>
    `;
  }

  function resolveClickRoute(kind, props, options = {}) {
    if (options.clickRoute) return options.clickRoute;
    const p = props || {};
    const resolved = resolveKind(kind, p);
    if (options.onNavigate) return null;

    if (['site', 'site_fdsu', 'sites', 'sites_40', 'sites_300', 'sites_all'].includes(resolved)) {
      const id = pick(p, ['site_id', 'id', 'asset_id']) || pick(p, ['site_code', 'code', 'business_id']);
      const program = pick(p, ['program_code', 'programme']) || '';
      if (id) return `decision-case/site/${encodeURIComponent(id)}${program ? `?program_code=${encodeURIComponent(program)}` : ''}`;
    }
    if (resolved === 'ccn') {
      const id = pick(p, ['id', 'business_id', 'code']);
      if (id) return `decision-case/ccn/${encodeURIComponent(id)}`;
    }
    if (resolved === 'uncovered_locality') {
      return 'decision-detail/population-non-couverte';
    }
    if (resolved === 'territory' || resolved === 'territoire' || resolved === 'territoires') {
      const id = pick(p, ['territory_id', 'id', 'code', 'nom', 'name']);
      if (id) return `territorial-intelligence/${encodeURIComponent(id)}`;
    }
    if (resolved === 'spatial_match' || resolved === 'link') {
      const id = pick(p, ['asset_id', 'asset_business_id', 'code', 'site_code']);
      if (id) return `spatial-impact/site/${encodeURIComponent(id)}`;
    }
    if (resolved === 'health') {
      return 'decision-detail/sante';
    }
    return null;
  }

  function bindHoverTooltip(layer, kind, props, options = {}) {
    return bind(layer, props, kind, options);
  }

  /**
   * API cible : SigMapTooltips.bind(layer, featureOrData, entityType, options)
   */
  function bind(layer, featureOrData, entityType, options = {}) {
    if (!layer || typeof layer.bindTooltip !== 'function') return false;
    const props = normalizeProps(featureOrData);
    const kind = resolveKind(entityType, props);
    const html = buildHtml(kind, props, options);

    layer.bindTooltip(html, {
      sticky: false,
      direction: options.direction || 'auto',
      opacity: 1,
      className: 'sig-map-tooltip',
      permanent: false,
      pane: options.pane || 'tooltipPane',
    });

    if (options.interactive !== false && typeof layer.on === 'function') {
      layer.off('click.sigMapTooltips');
      layer.on('click.sigMapTooltips', (event) => {
        if (event?.originalEvent && global.L?.DomEvent?.stopPropagation) {
          global.L.DomEvent.stopPropagation(event.originalEvent);
        }
        if (typeof options.onClick === 'function') {
          options.onClick(props, kind, event);
          return;
        }
        const route = resolveClickRoute(kind, props, options);
        if (route) {
          // Jamais d'ouverture /api/ — uniquement hash métier dashboard
          if (String(route).includes('/api/')) return;
          global.location.hash = String(route).replace(/^#/, '');
        }
      });
    }

    // Surbrillance discrète polygones / lignes
    if (typeof layer.setStyle === 'function' && options.hoverStyle !== false) {
      layer.off('mouseover.sigMapTooltips mouseout.sigMapTooltips');
      const base = options.baseStyle || null;
      layer.on('mouseover.sigMapTooltips', function onHover() {
        try {
          layer.setStyle({ weight: (base?.weight || 2) + 1, opacity: 1 });
          if (layer.bringToFront) layer.bringToFront();
        } catch (_e) { /* ignore */ }
      });
      layer.on('mouseout.sigMapTooltips', function onOut() {
        try {
          if (base) layer.setStyle(base);
          else if (layer.options) layer.setStyle({ weight: layer.options.weight || 2, opacity: layer.options.opacity || 0.85 });
        } catch (_e) { /* ignore */ }
      });
    }

    return true;
  }

  function rebindLayerGroup(layerGroup, entityType, options = {}) {
    if (!layerGroup?.eachLayer) return 0;
    let count = 0;
    layerGroup.eachLayer((layer) => {
      const feature = layer.feature || layer.options?.feature;
      if (bind(layer, feature || layer.options || {}, entityType, options)) count += 1;
    });
    return count;
  }

  global.SigMapTooltips = {
    escapeHtml,
    isPresentable,
    pick,
    formatPopulation,
    formatDistance,
    formatScore,
    normalizeProps,
    resolveKind,
    buildLines,
    buildHtml,
    buildTitle,
    bind,
    bindHoverTooltip,
    rebindLayerGroup,
    resolveClickRoute,
    KIND_META,
    LAYER_TO_KIND,
  };
})(typeof window !== 'undefined' ? window : globalThis);
