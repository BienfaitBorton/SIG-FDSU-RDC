/**
 * Infobulles cartographiques partagées SIG-FDSU
 * Survol = comprendre rapidement · Clic = analyser en détail
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
    if (!text || text === '0' || text === '—' || text.toLowerCase() === 'null') return false;
    return true;
  }

  function pick(props, keys) {
    const source = props || {};
    for (const key of keys) {
      if (isPresentable(source[key])) return source[key];
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

  const KIND_META = {
    site_fdsu: { label: 'Site FDSU', icon: '📡' },
    sites_40: { label: 'Site 40 FDSU', icon: '🟣' },
    sites_300: { label: 'Site 300 FDSU', icon: '🔵' },
    sites_all: { label: 'Site FDSU', icon: '📡' },
    ccn: { label: 'Centre communautaire', icon: '🏛️' },
    uncovered_locality: { label: 'Localité non couverte', icon: '⚠️' },
    covered_locality: { label: 'Localité couverte', icon: '✅' },
    village: { label: 'Localité', icon: '📍' },
    villages: { label: 'Localité', icon: '📍' },
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
    telecom: { label: 'Infrastructure télécom', icon: '📶' },
    telecom_vodacom: { label: 'Couverture Vodacom', icon: '📶' },
    telecom_orange: { label: 'Couverture Orange', icon: '📶' },
    telecom_fiber_mw: { label: 'Lien micro-ondes / fibre', icon: '📡' },
    telecom_fiberco: { label: 'Backbone fibre', icon: '🧵' },
    telecom_fttx: { label: 'Accès fibre (FTTx)', icon: '🧵' },
    fibre: { label: 'Fibre optique', icon: '🧵' },
    backbone: { label: 'Backbone', icon: '🧵' },
    route: { label: 'Route', icon: '🛣️' },
    mission: { label: 'Mission', icon: '🎯' },
    missions: { label: 'Mission', icon: '🎯' },
  };

  function resolveKind(kind, props) {
    const p = props || {};
    if (kind && KIND_META[kind]) return kind;
    const inferred = pick(p, ['kind', 'layer_key', 'feature_kind']);
    if (inferred && KIND_META[inferred]) return inferred;
    if (pick(p, ['coverage_status']) === 'uncovered' || pick(p, ['is_uncovered']) === true) {
      return 'uncovered_locality';
    }
    return kind || 'village';
  }

  function pushLine(lines, label, value) {
    if (!isPresentable(value)) return;
    lines.push(`${label} : ${value}`);
  }

  function buildLines(kind, props) {
    const p = props || {};
    const lines = [];
    const resolved = resolveKind(kind, p);

    if (resolved === 'site_fdsu' || resolved === 'sites_40' || resolved === 'sites_300' || resolved === 'sites_all' || resolved === 'sites') {
      pushLine(lines, 'Code', pick(p, ['site_code', 'code', 'official_code', 'business_id']));
      pushLine(lines, 'Localité', pick(p, ['localite', 'locality', 'village', 'name', 'nom']));
      pushLine(lines, 'Programme', pick(p, ['programme', 'program_code', 'program']) || (resolved === 'sites_300' ? 'Sites 300' : resolved === 'sites_40' ? 'Sites 40' : null));
      pushLine(lines, 'Priorité', pick(p, ['priority_level_label', 'priority_level', 'priorite', 'priority_status']));
      const pop = formatPopulation(pick(p, ['population_cible', 'population', 'pop_cible', 'target_population']));
      if (pop) pushLine(lines, 'Population cible', pop);
      pushLine(lines, 'Statut de donnée', pick(p, ['data_status', 'data_quality', 'quality_label', 'statut_donnee', 'status', 'operational_status']) || 'À renseigner');
      pushLine(lines, 'Province', pick(p, ['province', 'province_name']));
      pushLine(lines, 'Territoire', pick(p, ['territoire', 'territory', 'territoire_name']));
      return lines.slice(0, 7);
    }

    if (resolved === 'uncovered_locality') {
      pushLine(lines, 'Nom', pick(p, ['nom', 'name', 'localite', 'locality_name']));
      pushLine(lines, 'Territoire', pick(p, ['territoire', 'territory', 'territoire_name']));
      const pop = formatPopulation(pick(p, ['population', 'pop', 'population_estimee']));
      if (pop) pushLine(lines, 'Population', pop);
      pushLine(lines, 'Priorité', pick(p, ['priority_level_label', 'priority_level', 'priorite', 'priority']));
      pushLine(lines, 'Catégorie', pick(p, ['category', 'categorie', 'need_category', 'coverage_category']));
      const dist = formatDistance(pick(p, ['distance_utile_m', 'distance_m', 'distance_to_site_m', 'nearest_site_distance_m']));
      if (dist) pushLine(lines, 'Distance utile', dist);
      return lines;
    }

    if (resolved === 'ccn') {
      pushLine(lines, 'Code', pick(p, ['business_id', 'code', 'ccn_code', 'official_code']));
      pushLine(lines, 'Type', pick(p, ['ccn_type', 'type', 'category']));
      pushLine(lines, 'Statut', pick(p, ['status', 'statut', 'operational_status']));
      const pop = formatPopulation(pick(p, ['population_desservie', 'population_served', 'population']));
      if (pop) pushLine(lines, 'Population desservie', pop);
      pushLine(lines, 'Site associé', pick(p, ['site_code', 'associated_site', 'site_fdsu', 'linked_site']));
      pushLine(lines, 'Territoire', pick(p, ['territoire', 'territory']));
      return lines;
    }

    if (resolved === 'territoire' || resolved === 'territoires') {
      pushLine(lines, 'Province', pick(p, ['province', 'province_name']));
      if (p.fdsu_sites_count != null) pushLine(lines, 'Sites FDSU', p.fdsu_sites_count);
      if (p.uncovered_localities_count != null) pushLine(lines, 'Localités non couvertes', p.uncovered_localities_count);
      pushLine(lines, 'NDCI', pick(p, ['ndci', 'ndci_score', 'coverage_index']));
      pushLine(lines, 'Qualité des données', pick(p, ['data_quality', 'quality_label', 'cdqs', 'quality_score']));
      const pop = formatPopulation(pick(p, ['population', 'pop']));
      if (pop) pushLine(lines, 'Population', pop);
      return lines;
    }

    if (resolved === 'province' || resolved === 'provinces') {
      pushLine(lines, 'Code', pick(p, ['code_province_fdsu', 'code']));
      if (p.fdsu_sites_count != null) pushLine(lines, 'Sites FDSU', p.fdsu_sites_count);
      if (p.uncovered_localities_count != null) pushLine(lines, 'Localités non couvertes', p.uncovered_localities_count);
      pushLine(lines, 'NDCI', pick(p, ['ndci', 'ndci_score']));
      const pop = formatPopulation(pick(p, ['population', 'pop']));
      if (pop) pushLine(lines, 'Population', pop);
      return lines;
    }

    if (resolved === 'health') {
      pushLine(lines, 'Type', pick(p, ['facility_type_name', 'facility_type_code', 'type']));
      pushLine(lines, 'Province', pick(p, ['province_name', 'province']));
      pushLine(lines, 'Zone de santé', pick(p, ['zonesante', 'zone_sante']));
      pushLine(lines, 'Localité', pick(p, ['locality_name', 'localite', 'village']));
      pushLine(lines, 'Qualité des données', pick(p, ['data_quality', 'quality_score', 'quality_label']));
      return lines;
    }

    if (String(resolved).startsWith('telecom') || resolved === 'fibre' || resolved === 'backbone' || resolved === 'telecom') {
      pushLine(lines, 'Type', pick(p, ['infra_type', 'line_type', 'polygon_type', 'infra_category', 'technology']));
      pushLine(lines, 'Opérateur', pick(p, ['operator_name', 'operator_code', 'operateur']));
      pushLine(lines, 'Technologie', pick(p, ['technology', 'technologie']));
      const dist = formatDistance(pick(p, ['distance_to_selected_site_m', 'distance_m']));
      if (dist) pushLine(lines, 'Distance au site', dist);
      pushLine(lines, 'Province', pick(p, ['province']));
      pushLine(lines, 'Territoire', pick(p, ['territoire']));
      return lines;
    }

    if (resolved === 'route') {
      pushLine(lines, 'Type', pick(p, ['road_type', 'type', 'classe']));
      pushLine(lines, 'État', pick(p, ['status', 'etat', 'condition']));
      pushLine(lines, 'Province', pick(p, ['province']));
      return lines;
    }

    if (resolved === 'village' || resolved === 'villages' || resolved === 'covered_locality') {
      pushLine(lines, 'Groupement', pick(p, ['groupement']));
      pushLine(lines, 'Territoire', pick(p, ['territoire', 'territory']));
      const pop = formatPopulation(pick(p, ['population', 'pop']));
      if (pop) pushLine(lines, 'Population', pop);
      pushLine(lines, 'Couverture', pick(p, ['coverage_status', 'couverture', 'status']));
      return lines;
    }

    if (resolved === 'missions' || resolved === 'mission') {
      pushLine(lines, 'Statut', pick(p, ['statut', 'status', 'etat']));
      pushLine(lines, 'Date', pick(p, ['date', 'date_mission', 'started_at']));
      return lines;
    }

    // Fallback métier : au moins 1–3 attributs utiles, jamais vide
    [
      ['Code', pick(p, ['code', 'business_id', 'official_code', 'id'])],
      ['Province', pick(p, ['province', 'province_name'])],
      ['Territoire', pick(p, ['territoire', 'territory'])],
      ['Statut', pick(p, ['status', 'statut', 'operational_status'])],
    ].forEach(([label, value]) => pushLine(lines, label, value));
    if (!lines.length) lines.push('Données contextuelles à compléter');
    return lines;
  }

  function buildTitle(kind, props) {
    const p = props || {};
    const resolved = resolveKind(kind, p);
    return pick(p, ['nom', 'name', 'libelle', 'infra_name', 'line_name', 'polygon_name', 'site_name', 'localite'])
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

  function bindHoverTooltip(layer, kind, props, options = {}) {
    if (!layer || typeof layer.bindTooltip !== 'function') return false;
    layer.bindTooltip(buildHtml(kind, props, options), {
      sticky: false,
      direction: options.direction || 'top',
      opacity: 1,
      className: 'sig-map-tooltip',
    });
    return true;
  }

  global.SigMapTooltips = {
    escapeHtml,
    isPresentable,
    buildLines,
    buildHtml,
    bindHoverTooltip,
    resolveKind,
    KIND_META,
  };
})(typeof window !== 'undefined' ? window : globalThis);
