(function initTerritorialIntelligenceModule(global) {
  const API_BASE = 'http://127.0.0.1:8001';

  /** Fallback aligné sur data/cartography/symbology_registry_v1.json — remplacé par /symbology si disponible. */
  let LAYER_STYLES = {
    territory_boundary: { color: '#38bdf8', weight: 2, fillOpacity: 0.06 },
    collectivite: { color: '#67e8f9', weight: 1.5, fillColor: 'rgba(103,232,249,0.12)', fillOpacity: 0.12 },
    site_fdsu: { radius: 5, color: '#fbbf24', fillColor: '#f59e0b', fillOpacity: 0.9 },
    ccn: { radius: 7, color: '#a78bfa', fillColor: '#8b5cf6', fillOpacity: 0.9 },
    health: { radius: 5, color: '#34d399', fillColor: '#10b981', fillOpacity: 0.9 },
    telecom: { radius: 6, color: '#38bdf8', fillColor: '#0ea5e9', fillOpacity: 0.9 },
    fiber: { radius: 7, color: '#f472b6', fillColor: '#db2777', fillOpacity: 0.95 },
    fiber_line: { color: '#db2777', weight: 3, opacity: 0.85 },
    route: { color: '#94a3b8', weight: 3, opacity: 0.9 },
    groupement: { radius: 6, color: '#fcd34d', fillColor: '#eab308', fillOpacity: 0.85 },
    locality: { radius: 3, color: '#cbd5e1', fillColor: '#64748b', fillOpacity: 0.7 },
    locality_covered: { radius: 4, color: '#86efac', fillColor: '#22c55e', fillOpacity: 0.85 },
    locality_uncovered: { radius: 4, color: '#fca5a5', fillColor: '#ef4444', fillOpacity: 0.85 },
  };

  const KIND_LABELS = {
    territory_boundary: 'Limite',
    collectivite: 'Collectivité',
    site_fdsu: 'Site FDSU',
    ccn: 'CCN',
    health: 'Santé',
    telecom: 'Télécommunications',
    fiber: 'Nœud fibre',
    fiber_line: 'Tronçon fibre',
    route: 'Route',
    groupement: 'Groupement',
    locality: 'Localité',
    locality_covered: 'Localité couverte',
    locality_uncovered: 'Localité non couverte',
  };

  const DOMAIN_LAYER_KINDS = {
    telecom: ['telecom'],
    fiber: ['fiber', 'fiber_line'],
    health: ['health'],
    routes: ['route'],
    sites_20476: ['site_fdsu'],
    sites_300: ['site_fdsu'],
    sites_40: ['site_fdsu'],
    ccn: ['ccn'],
    groupements: ['groupement'],
    localites: ['locality'],
    admin: ['groupement', 'locality', 'collectivite'],
  };

  const DRILL_KINDS = new Set(['collectivite', 'groupement', 'locality', 'territory_boundary']);

  const tiState = {
    initialized: false,
    territories: [],
    selectedId: null,
    entity: null,
    profile: null,
    explainability: null,
    mapGeojson: null,
    mapLegend: [],
    map: null,
    layer: null,
    detailLayer: null,
    domainLayers: {},
    layerVisibility: {},
    detail: {
      domain: null,
      page: 1,
      pageSize: 25,
      payload: null,
      filter: '',
      search: '',
      showTech: false,
    },
  };

  function applySymbologyRegistry(payload) {
    const domains = payload?.domains || [];
    if (!domains.length) return;
    const next = { ...LAYER_STYLES };
    domains.forEach((d) => {
      const key = d.domain;
      if (!key) return;
      next[key] = {
        color: d.color,
        fillColor: d.fillColor || d.fill_color || d.color,
        fillOpacity: d.fillOpacity ?? d.fill_opacity ?? 0.8,
        radius: d.radius ?? 5,
        weight: d.weight ?? 2,
        opacity: d.opacity ?? 0.9,
      };
    });
    LAYER_STYLES = next;
  }

  function setHashEntity(entityId) {
    if (!entityId) return;
    const next = `territorial-intelligence/${encodeURIComponent(entityId)}`;
    if ((global.location.hash || '').replace(/^#/, '') !== next) {
      global.location.hash = next;
    }
  }

  function confidenceLabel(value) {
    const map = { high: 'Élevée', medium: 'Moyenne', low: 'Faible' };
    return map[String(value || '').toLowerCase()] || String(value || '—');
  }

  function humanizeToken(value) {
    const raw = String(value ?? '');
    const map = {
      high: 'Élevée', medium: 'Moyenne', low: 'Faible',
      true: 'Oui / Présence détectée', false: 'Non',
      unmatched_needs: 'Besoins sans actif correspondant',
      partial: 'Données partielles', operational: 'Données intégrées',
      confirmed: 'Confirmé', demonstration: 'Démonstration',
      integration_pending: 'En cours d’intégration',
      integration_anomaly: 'Anomalie d’intégration',
    };
    return map[raw] || map[raw.toLowerCase()] || raw;
  }

  function humanizeBusinessText(text) {
    return String(text ?? '')
      .replace(/\bnot_sourced\b/gi, 'non sourcé')
      .replace(/\bunavailable\b/gi, 'indisponible')
      .replace(/\bunmatched_needs\b/gi, 'besoins sans actif correspondant')
      .replace(/\bintegration_pending\b/gi, 'en cours d’intégration')
      .replace(/\bhigh\b/gi, 'élevée')
      .replace(/\bmedium\b/gi, 'moyenne')
      .replace(/\blow\b/gi, 'faible')
      .replace(/\btrue\b/gi, 'oui')
      .replace(/\bfalse\b/gi, 'non');
  }

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function fetchJson(path) {
    return fetch(`${API_BASE}${path}`, { headers: { Accept: 'application/json' }, cache: 'no-store' })
      .then((response) => {
        if (!response.ok) throw new Error(path);
        return response.json();
      });
  }

  function formatField(field) {
    if (!field || typeof field !== 'object') return { text: '—', status: 'unavailable' };
    if (field.value === null || field.value === undefined) {
      return { text: '—', status: field.status || 'unavailable', note: field.note };
    }
    let value = field.value;
    if (typeof value === 'boolean') value = value ? 'Oui / Présence détectée' : 'Non';
    else if (typeof value === 'number') value = Number(value).toLocaleString('fr-FR');
    else value = humanizeToken(value);
    return { text: String(value), status: field.status || 'confirmed', note: field.note };
  }

  function statusLabel(status) {
    const map = {
      operational: 'données intégrées', confirmed: 'confirmé', estimated: 'estimé', partial: 'données partielles',
      integration_pending: 'en cours d’intégration', integration_anomaly: 'anomalie d’intégration',
      not_applicable: 'non applicable', error: 'erreur', unavailable: 'indisponible',
      not_sourced: 'non sourcé', demonstration: 'démonstration',
    };
    return map[status] || status || '';
  }

  function setKpi(id, fieldOrValue) {
    const node = document.querySelector(id);
    const statusNode = document.querySelector(`${id}-status`);
    if (!node) return;
    if (fieldOrValue && typeof fieldOrValue === 'object' && 'status' in fieldOrValue) {
      const formatted = formatField(fieldOrValue);
      node.textContent = formatted.text;
      if (statusNode) {
        statusNode.textContent = statusLabel(formatted.status);
        statusNode.className = `ti-status is-${formatted.status}`;
        statusNode.title = formatted.note || '';
      }
      return;
    }
    node.textContent = fieldOrValue == null ? '—' : Number(fieldOrValue).toLocaleString('fr-FR');
  }

  function ensureMap() {
    if (tiState.map || typeof global.L === 'undefined') return;
    const el = document.querySelector('#ti-map');
    if (!el) return;
    tiState.map = global.L.map(el, { zoomControl: true }).setView([-2.8, 23.5], 5);
    global.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 18,
    }).addTo(tiState.map);
    tiState.layer = global.L.layerGroup().addTo(tiState.map);
    tiState.detailLayer = global.L.layerGroup().addTo(tiState.map);
  }

  function fitAllLayers() {
    if (!tiState.map || !tiState.layer) return;
    const layers = tiState.layer.getLayers();
    if (!layers.length) return;
    try {
      const group = global.L.featureGroup(layers);
      const b = group.getBounds();
      if (b && b.isValid && b.isValid()) {
        tiState.map.fitBounds(b, { padding: [28, 28], maxZoom: 11 });
      }
    } catch (_e) { /* ignore */ }
    global.setTimeout(() => tiState.map.invalidateSize(), 80);
  }

  function popupLabel(kind, name) {
    return `<strong>${escapeHtml(KIND_LABELS[kind] || kind)}</strong><br>${escapeHtml(name || '')}`;
  }

  function bindDrill(layer, feature) {
    const props = feature.properties || {};
    const kind = props.kind;
    const drillId = props.drill_id || props.id;
    if (!drillId || !DRILL_KINDS.has(kind)) return;
    if (kind === 'territory_boundary' && !String(drillId).toUpperCase().startsWith('TERRITOIRE')) return;
    const navigateId = (() => {
      const raw = String(drillId);
      if (/^(PROVINCE|TERRITOIRE|COLLECTIVITE|GROUPEMENT|LOCALITE)-/i.test(raw)) return raw;
      if (kind === 'collectivite') return `COLLECTIVITE-${raw}`;
      if (kind === 'groupement') return `GROUPEMENT-${raw}`;
      if (kind === 'locality') return `LOCALITE-${raw}`;
      return raw;
    })();
    layer.on('click', () => {
      loadEntity(navigateId, { pushHash: true });
    });
  }

  function tipKindForFeature(kind) {
    if (kind === 'locality_uncovered' || kind === 'uncovered_locality') return 'uncovered_locality';
    if (kind === 'locality_covered' || kind === 'locality') return 'uncovered_locality';
    if (kind === 'territory_boundary' || kind === 'territoire') return 'territoire';
    if (kind === 'province') return 'province';
    if (kind === 'ccn') return 'ccn';
    if (kind === 'route' || kind === 'fiber_line') return 'route';
    if (String(kind || '').startsWith('site')) return 'site_fdsu';
    if (kind === 'health') return 'health';
    if (kind === 'telecom') return 'telecom';
    return kind || 'territoire';
  }

  function bindSharedTooltip(layer, featureOrProps, kind) {
    if (!layer || !global.SigMapTooltips?.bind) return;
    const props = featureOrProps?.properties || featureOrProps || {};
    global.SigMapTooltips.bind(layer, props, tipKindForFeature(kind || props.kind), {
      sticky: true,
      hint: false,
    });
  }

  function addFeatureToMap(feature, targetGroup) {
    const kind = feature.properties?.kind;
    const geomType = feature.geometry?.type;
    const style = LAYER_STYLES[kind] || LAYER_STYLES.locality;
    const name = feature.properties?.name || feature.properties?.code || kind;
    const polyStyle = kind === 'collectivite' ? (LAYER_STYLES.collectivite || LAYER_STYLES.territory_boundary) : LAYER_STYLES.territory_boundary;

    if (kind === 'territory_boundary' || kind === 'collectivite' || geomType === 'Polygon' || geomType === 'MultiPolygon') {
      const layer = global.L.geoJSON(feature, {
        style: {
          color: polyStyle.color,
          weight: polyStyle.weight || 2,
          fillColor: polyStyle.fillColor || polyStyle.color,
          fillOpacity: polyStyle.fillOpacity ?? 0.06,
        },
        onEachFeature: (feat, lyr) => {
          lyr.bindPopup(popupLabel(kind || 'territory_boundary', name));
          bindSharedTooltip(lyr, feat, kind || 'territoire');
          bindDrill(lyr, feature);
        },
      });
      layer.addTo(targetGroup);
      return layer;
    }

    if (geomType === 'LineString' || geomType === 'MultiLineString' || kind === 'route' || kind === 'fiber_line') {
      const layer = global.L.geoJSON(feature, {
        style: {
          color: style.color || '#94a3b8',
          weight: style.weight || 3,
          opacity: style.opacity || 0.9,
        },
        onEachFeature: (feat, lyr) => {
          lyr.bindPopup(popupLabel(kind, name));
          bindSharedTooltip(lyr, feat, kind);
        },
      });
      layer.addTo(targetGroup);
      return layer;
    }

    const coords = feature.geometry?.coordinates;
    if (!coords || geomType !== 'Point') return null;
    const latlng = [coords[1], coords[0]];
    const marker = global.L.circleMarker(latlng, {
      radius: style.radius || 5,
      color: style.color || '#64748b',
      fillColor: style.fillColor || '#94a3b8',
      fillOpacity: style.fillOpacity || 0.8,
      weight: 2,
    }).bindPopup(popupLabel(kind, name));
    bindSharedTooltip(marker, feature, kind);
    bindDrill(marker, feature);
    marker.addTo(targetGroup);
    return marker;
  }

  function setLayerVisibility(kind, visible) {
    tiState.layerVisibility[kind] = visible;
    const group = tiState.domainLayers[kind];
    if (!group || !tiState.map) return;
    if (visible) {
      if (!tiState.layer.hasLayer(group)) tiState.layer.addLayer(group);
    } else if (tiState.layer.hasLayer(group)) {
      tiState.layer.removeLayer(group);
    }
  }

  function mountTiLegend(legendItems) {
    const items = (legendItems || []).filter((i) => i.visible !== false && (i.count == null || i.count > 0));
    tiState.mapLegend = items;
    if (!global.UxPremium?.mountMapLegend) return;
    global.UxPremium.mountMapLegend('#ti-map', {
      id: 'ux-legend-ti',
      title: 'Légende',
      interactive: true,
      items: items.map((item) => ({
        kind: item.kind || item.domain,
        label: item.label,
        count: item.count,
        color: item.color || item.fill_color,
        className: item.legend_class || item.className || '',
        visible: tiState.layerVisibility[item.kind || item.domain] !== false,
      })),
      onToggle: (kind, visible) => setLayerVisibility(kind, visible),
    });
  }

  function renderMap(geojson, legendItems) {
    ensureMap();
    if (!tiState.map || !tiState.layer) return;
    tiState.mapGeojson = geojson;
    tiState.layer.clearLayers();
    tiState.detailLayer?.clearLayers();
    tiState.domainLayers = {};

    const features = geojson?.features || [];
    features.forEach((feature) => {
      const kind = feature.properties?.kind || 'other';
      if (!tiState.domainLayers[kind]) {
        tiState.domainLayers[kind] = global.L.layerGroup();
        if (tiState.layerVisibility[kind] !== false) {
          tiState.domainLayers[kind].addTo(tiState.layer);
        }
      }
      addFeatureToMap(feature, tiState.domainLayers[kind]);
    });
    mountTiLegend(legendItems || tiState.mapLegend);
    fitAllLayers();
  }

  function renderBreadcrumb(crumbs) {
    const nav = document.querySelector('#ti-breadcrumb');
    const list = nav?.querySelector('.ti-breadcrumb-list') || nav;
    if (!list) return;
    const items = crumbs && crumbs.length ? crumbs : [{ type: 'rdc', id: 'RDC', name: 'RDC' }];
    list.innerHTML = items.map((c, idx) => {
      const isLast = idx === items.length - 1;
      const label = escapeHtml(c.label || c.name || c.id);
      if (isLast || c.type === 'rdc') {
        return `<li class="${isLast ? 'is-current' : ''}">${c.type === 'rdc' && !isLast ? `<a href="#decision-view">${label}</a>` : label}</li>`;
      }
      return `<li><a href="#territorial-intelligence/${encodeURIComponent(c.id)}" data-ti-entity="${escapeHtml(c.id)}">${label}</a></li>`;
    }).join('');
    list.querySelectorAll('[data-ti-entity]').forEach((a) => {
      a.addEventListener('click', (event) => {
        event.preventDefault();
        loadEntity(a.getAttribute('data-ti-entity'), { pushHash: true });
      });
    });
  }

  function renderChildren(children, childrenLevel) {
    const host = document.querySelector('#ti-children');
    const list = document.querySelector('#ti-children-list');
    const title = document.querySelector('.ti-children-title');
    if (!host || !list) return;
    if (!children || !children.length) {
      host.hidden = true;
      list.innerHTML = '';
      return;
    }
    host.hidden = false;
    if (title) {
      const labels = {
        collectivite: 'Collectivités / secteurs / chefferies',
        groupement: 'Groupements',
        localite: 'Localités',
        territoire: 'Territoires',
      };
      title.textContent = labels[childrenLevel] || 'Niveau inférieur';
    }
    list.innerHTML = children.map((c) => `
      <li><button type="button" data-ti-entity="${escapeHtml(c.id)}">${escapeHtml(c.name || c.id)}${c.admin_type ? ` <small>(${escapeHtml(c.admin_type)})</small>` : ''}</button></li>
    `).join('');
    list.querySelectorAll('[data-ti-entity]').forEach((btn) => {
      btn.addEventListener('click', () => loadEntity(btn.getAttribute('data-ti-entity'), { pushHash: true }));
    });
  }

  function focusDomainOnMap(domain) {
    ensureMap();
    if (!tiState.map || !tiState.mapGeojson) return;
    const kinds = DOMAIN_LAYER_KINDS[domain] || [domain];
    tiState.detailLayer?.clearLayers();

    // Remettre toutes les couches visibles, mettre en avant le domaine
    Object.keys(tiState.domainLayers).forEach((kind) => {
      const group = tiState.domainLayers[kind];
      if (!group) return;
      group.eachLayer((lyr) => {
        if (lyr.setStyle && (kind === 'route' || kind === 'fiber_line' || kind === 'territory_boundary')) {
          const base = LAYER_STYLES[kind] || {};
          lyr.setStyle({
            opacity: kinds.includes(kind) ? 1 : 0.25,
            weight: kinds.includes(kind) ? (base.weight || 3) + 1 : (base.weight || 2),
            color: base.color,
          });
        } else if (lyr.setStyle) {
          lyr.setStyle({
            fillOpacity: kinds.includes(kind) ? 0.95 : 0.2,
            opacity: kinds.includes(kind) ? 1 : 0.25,
          });
        }
      });
    });

    const focusFeatures = (tiState.mapGeojson.features || []).filter((f) => kinds.includes(f.properties?.kind));
    const temp = global.L.featureGroup();
    focusFeatures.forEach((f) => addFeatureToMap(f, tiState.detailLayer));
    tiState.detailLayer.eachLayer((lyr) => temp.addLayer(lyr));
    try {
      if (temp.getLayers().length) {
        const b = temp.getBounds();
        if (b && b.isValid()) tiState.map.fitBounds(b, { padding: [36, 36], maxZoom: 12 });
      }
    } catch (_e) { /* ignore */ }
    global.setTimeout(() => tiState.map.invalidateSize(), 80);
  }

  function focusItemsOnMap(items, color) {
    ensureMap();
    if (!tiState.map || !tiState.detailLayer) return;
    tiState.detailLayer.clearLayers();
    const latLngs = [];
    (items || []).forEach((item) => {
      const c = item.coordinates || {};
      const lat = c.latitude;
      const lon = c.longitude;
      if (lat == null || lon == null) return;
      const marker = global.L.circleMarker([lat, lon], {
        radius: 8,
        color: color || '#f59e0b',
        fillColor: color || '#fbbf24',
        fillOpacity: 0.95,
        weight: 2,
      });
      marker.bindPopup(`<strong>${escapeHtml(item.name || item.id)}</strong><br/>${escapeHtml(item.type || '')}`);
      if (global.SigMapTooltips?.bind) {
        global.SigMapTooltips.bind(marker, item, tipKindForFeature(item.type || item.kind || 'uncovered_locality'), {
          sticky: true,
          hint: false,
        });
      }
      marker.addTo(tiState.detailLayer);
      latLngs.push([lat, lon]);
    });
    if (latLngs.length) {
      tiState.map.fitBounds(global.L.latLngBounds(latLngs), { padding: [28, 28], maxZoom: 12 });
    }
    global.setTimeout(() => tiState.map.invalidateSize(), 80);
  }

  function openDetailDrawer(domain, opts = {}) {
    const drawer = document.querySelector('#ti-detail-drawer');
    if (!drawer || !tiState.selectedId) return;
    tiState.detail.domain = domain;
    tiState.detail.page = opts.page || 1;
    tiState.detail.search = '';
    tiState.detail.filter = '';
    tiState.detail.showTech = false;
    const search = document.querySelector('#ti-detail-search');
    const filter = document.querySelector('#ti-detail-filter');
    if (search) search.value = '';
    if (filter) filter.innerHTML = '<option value="">Tous les types</option>';
    drawer.hidden = false;
    drawer.removeAttribute('hidden');
    focusDomainOnMap(domain);
    loadDetailPage();
  }

  function closeDetailDrawer() {
    const drawer = document.querySelector('#ti-detail-drawer');
    if (!drawer) return;
    drawer.hidden = true;
    drawer.setAttribute('hidden', '');
    tiState.detailLayer?.clearLayers();
    // restore opacity
    Object.keys(tiState.domainLayers).forEach((kind) => {
      const group = tiState.domainLayers[kind];
      const base = LAYER_STYLES[kind] || {};
      group?.eachLayer((lyr) => {
        if (lyr.setStyle) {
          lyr.setStyle({
            opacity: base.opacity || 0.9,
            fillOpacity: base.fillOpacity || 0.8,
            weight: base.weight || 2,
            color: base.color,
          });
        }
      });
    });
    fitAllLayers();
  }

  function detailColumns(domain) {
    if (domain === 'telecom') return [['operator', 'Opérateur'], ['name', 'Nom'], ['type', 'Type'], ['technology', 'Technologie'], ['locality', 'Localité'], ['status', 'Statut']];
    if (domain === 'health') return [['name', 'Nom'], ['type', 'Type'], ['locality', 'Localité'], ['source', 'Source']];
    if (domain === 'routes') return [['name', 'Nom'], ['category', 'Catégorie'], ['length_km', 'Longueur (km)'], ['condition', 'État'], ['surface', 'Revêtement']];
    if (domain === 'fiber') return [['name', 'Nom'], ['kind', 'Nature'], ['type', 'Type'], ['operator', 'Opérateur'], ['length_km', 'Longueur (km)'], ['locality', 'Localité']];
    if (String(domain).startsWith('sites') || domain === 'ccn') return [['name', 'Nom'], ['program', 'Programme'], ['status', 'Statut'], ['priority', 'Priorité'], ['score', 'Score'], ['locality', 'Localité']];
    return [['name', 'Nom'], ['type', 'Type'], ['parent', 'Parent'], ['code', 'Code']];
  }

  function loadDetailPage() {
    const domain = tiState.detail.domain;
    if (!domain || !tiState.selectedId) return;
    const params = new URLSearchParams({
      page: String(tiState.detail.page),
      page_size: String(tiState.detail.pageSize),
    });
    if (String(domain).startsWith('sites_') || domain === 'ccn') params.set('program', domain);
    if (['localites', 'groupements', 'collectivites'].includes(domain)) params.set('level', domain);
    const title = document.querySelector('#ti-detail-title');
    const meta = document.querySelector('#ti-detail-meta');
    if (title) title.textContent = 'Chargement…';
    fetchJson(`/api/territorial-intelligence/territories/${encodeURIComponent(tiState.selectedId)}/details/${encodeURIComponent(domain)}?${params}`)
      .then((payload) => {
        tiState.detail.payload = payload;
        renderDetailTable(payload);
        if (meta) {
          meta.textContent = `${payload.summary?.headline || ''} · Confiance ${confidenceLabel(payload.summary?.confidence)} · Source ${payload.summary?.source || ''}`;
        }
        if (title) title.textContent = payload.domain_label || domain;
        const impact = document.querySelector('#ti-detail-impact');
        if (impact) {
          impact.innerHTML = `
            <p><strong>Pourquoi c’est important :</strong> ${escapeHtml(payload.summary?.business_impact || 'Impact non encore calculé')}</p>
            <p><strong>Action recommandée :</strong> ${escapeHtml(payload.summary?.recommendation || '')}</p>
          `;
        }
        const tech = document.querySelector('#ti-detail-tech');
        if (tech) {
          tech.textContent = JSON.stringify(payload.technical || {}, null, 2);
          tech.hidden = !tiState.detail.showTech;
        }
        const filter = document.querySelector('#ti-detail-filter');
        if (filter && filter.options.length <= 1) {
          const types = [...new Set((payload.top_items || []).map((i) => i.type_group || i.type || i.category || i.kind).filter(Boolean))];
          types.forEach((t) => {
            const opt = document.createElement('option');
            opt.value = t;
            opt.textContent = t;
            filter.appendChild(opt);
          });
        }
      })
      .catch(() => {
        if (title) title.textContent = 'Détail indisponible';
      });
  }

  function renderDetailTable(payload) {
    const thead = document.querySelector('#ti-detail-thead');
    const tbody = document.querySelector('#ti-detail-tbody');
    const pageLabel = document.querySelector('#ti-detail-page');
    if (!thead || !tbody) return;
    const cols = detailColumns(payload.domain || tiState.detail.domain);
    thead.innerHTML = `<tr>${cols.map(([, label]) => `<th>${escapeHtml(label)}</th>`).join('')}</tr>`;
    let rows = payload.top_items || [];
    const q = (tiState.detail.search || '').toLowerCase();
    const f = tiState.detail.filter || '';
    if (q) rows = rows.filter((r) => JSON.stringify(r).toLowerCase().includes(q));
    if (f) rows = rows.filter((r) => [r.type_group, r.type, r.category, r.kind].includes(f));
    tbody.innerHTML = rows.map((row) => `
      <tr data-id="${escapeHtml(row.id)}" class="ti-detail-row">
        ${cols.map(([key]) => {
          let val = row[key];
          if (key === 'kind') val = row.kind === 'network_line' ? 'Tronçon' : (row.kind === 'fttx_node' ? 'Nœud FTTX' : val);
          if (typeof val === 'number') val = Number(val).toLocaleString('fr-FR');
          return `<td>${escapeHtml(humanizeToken(val ?? '—'))}</td>`;
        }).join('')}
      </tr>
    `).join('') || '<tr><td colspan="8">Aucun objet pour ce filtre.</td></tr>';
    const pag = payload.pagination || {};
    if (pageLabel) pageLabel.textContent = `Page ${pag.page || 1} / ${pag.pages || 1} · ${pag.total ?? rows.length} objets`;
    tbody.querySelectorAll('.ti-detail-row').forEach((tr) => {
      tr.addEventListener('click', () => {
        const id = tr.getAttribute('data-id');
        const item = (payload.top_items || []).find((x) => String(x.id) === String(id));
        if (item) focusItemsOnMap([item], '#f59e0b');
      });
    });
  }

  function explainCard(domainKey, payload) {
    if (!payload || !payload.summary) {
      return `<article class="ti-explain-card is-pending" data-domain="${escapeHtml(domainKey)}"><h4>${escapeHtml(domainKey)}</h4><p>En cours d’intégration</p></article>`;
    }
    const s = payload.summary;
    const breakdown = (payload.breakdown || []).slice(0, 8)
      .map((b) => `<li>${escapeHtml(b.label)} : <strong>${escapeHtml(b.display != null ? b.display : b.count)}</strong>${b.note ? ` <em>${escapeHtml(b.note)}</em>` : ''}</li>`)
      .join('');
    const ops = (payload.operators || []).slice(0, 8)
      .map((o) => `<li>${escapeHtml(o.label)} : <strong>${escapeHtml(o.count)}</strong></li>`)
      .join('');
    const techs = (payload.technologies || []).slice(0, 8)
      .map((o) => `<li>${escapeHtml(o.label)} : <strong>${escapeHtml(o.count)}</strong></li>`)
      .join('');
    const typology = (payload.typology || [])
      .map((t) => `<li>${escapeHtml(t.label)} : <strong>${escapeHtml(t.display != null ? t.display : t.count)}</strong>${t.note ? ` — ${escapeHtml(t.note)}` : ''}</li>`)
      .join('');
    const named = (payload.named_axes || []).map((n) => `<li>${escapeHtml(n)}</li>`).join('');
    const actions = (payload.actions || [
      { id: 'details', label: 'Voir les détails' },
      { id: 'map', label: 'Afficher sur la carte' },
    ]).map((a) => `
      <button type="button" class="secondary-button ti-explain-action" data-domain="${escapeHtml(payload.domain || domainKey)}" data-action="${escapeHtml(a.id)}">${escapeHtml(a.label)}</button>
    `).join('');
    return `
      <article class="ti-explain-card" data-domain="${escapeHtml(payload.domain || domainKey)}">
        <header>
          <h4>${escapeHtml(payload.domain_label || domainKey)}</h4>
          <span class="ti-status is-${escapeHtml(s.status)}">${escapeHtml(statusLabel(s.status))}</span>
        </header>
        <p class="ti-explain-headline">${escapeHtml(s.headline || '')}</p>
        ${breakdown ? `<div><p class="ti-explain-label">Répartition</p><ul>${breakdown}</ul></div>` : ''}
        ${ops ? `<div><p class="ti-explain-label">Opérateurs</p><ul>${ops}</ul></div>` : ''}
        ${techs ? `<div><p class="ti-explain-label">Technologies</p><ul>${techs}</ul></div>` : ''}
        ${typology ? `<div><p class="ti-explain-label">Typologie</p><ul>${typology}</ul></div>` : ''}
        ${named ? `<div><p class="ti-explain-label">Axes identifiés</p><ul>${named}</ul></div>` : ''}
        ${payload.accessibility_label ? `<p>Accessibilité : <strong>${escapeHtml(payload.accessibility_label)}</strong></p>` : ''}
        ${payload.limit_note || payload.quality?.limit_note ? `<p class="ti-field-note">Limite : ${escapeHtml(payload.limit_note || payload.quality.limit_note)}</p>` : ''}
        <p><strong>Confiance :</strong> ${escapeHtml(confidenceLabel(s.confidence))}</p>
        <p><strong>Pourquoi c’est important :</strong> ${escapeHtml(s.business_impact || 'Impact non encore calculé')}</p>
        <p><strong>Action :</strong> ${escapeHtml(s.recommendation || '')}</p>
        <div class="ti-explain-actions">${actions}</div>
      </article>
    `;
  }

  function renderSections(profilePayload, recommendations, explain, coverageOverride) {
    const box = document.querySelector('#ti-sections');
    if (!box) return;
    const s = profilePayload?.sections || {};
    const p = profilePayload?.profile || {};
    const ex = profilePayload?.explainability || tiState.explainability || {};
    const cov = coverageOverride || profilePayload?.coverage || s.coverage || {};
    const entityType = profilePayload?.entity?.type || p.entity_type || 'territoire';

    const line = (label, fieldObj, domain) => {
      const f = formatField(fieldObj);
      const src = fieldObj && fieldObj.source ? ` · Source : ${escapeHtml(fieldObj.source)}` : '';
      const conf = fieldObj && fieldObj.confidence ? ` · Confiance : ${escapeHtml(confidenceLabel(fieldObj.confidence))}` : '';
      const note = f.note ? `<br/><span class="ti-field-note">${escapeHtml(f.note)}</span>` : '';
      const click = domain
        ? ` class="ti-kpi-line is-clickable" data-domain="${escapeHtml(domain)}" role="button" tabindex="0" title="Voir les détails"`
        : '';
      return `<p${click}><strong>${escapeHtml(label)} :</strong> ${escapeHtml(f.text)} <span class="ti-status is-${escapeHtml(f.status)}">${escapeHtml(statusLabel(f.status))}</span>${src}${conf}${note}</p>`;
    };

    const recHtml = (recommendations?.recommendations || []).map((rec) => `
      <article class="ti-rec ti-rec--dg">
        <h4>Décision recommandée</h4>
        <p class="ti-rec-action">${escapeHtml(humanizeBusinessText(rec.action))}</p>
        <p><strong>Pourquoi ?</strong> ${escapeHtml(humanizeBusinessText(rec.why))}</p>
        <p><strong>Impact attendu :</strong> ${escapeHtml(humanizeBusinessText(rec.expected_impact || rec.impact || 'Impact non encore calculé'))}</p>
        <p><strong>Niveau de priorité :</strong> ${escapeHtml(humanizeToken(rec.priority_label || rec.priority || rec.confidence_level))}
          · Confiance ${escapeHtml(confidenceLabel(rec.confidence_level))}</p>
      </article>
    `).join('') || '<p>Aucune recommandation.</p>';

    const coverageHtml = `
      <section class="ti-section">
        <h3>Couverture numérique (NCI)</h3>
        ${line('Population estimée', profilePayload?.population || s.synthesis?.population || cov.population)}
        ${line('Population couverte', cov.population_covered)}
        ${line('Population non couverte', cov.population_uncovered)}
        ${line('Localités couvertes', cov.localities_covered)}
        ${line('Localités non couvertes', cov.localities_uncovered)}
        ${line('Taux estimé de couverture', cov.coverage_rate_pct)}
        ${cov.note || cov.double_counting_guard ? `<p class="ti-field-note">${escapeHtml(cov.note || '')}${cov.double_counting_guard ? ` · Garde : ${escapeHtml(cov.double_counting_guard)}` : ''}</p>` : ''}
      </section>`;

    const hideLocalityCount = entityType === 'localite';
    box.innerHTML = `
      <section class="ti-section">
        <h3>Lecture décideur — domaines explicables</h3>
        <div class="ti-explain-grid">
          ${explainCard('telecom', ex.telecom)}
          ${explainCard('fiber', ex.fiber)}
          ${explainCard('health', ex.health)}
          ${explainCard('routes', ex.routes)}
          ${explainCard('sites_20476', ex.sites_20476)}
          ${explainCard('sites_300', ex.sites_300)}
          ${explainCard('groupements', ex.groupements)}
          ${explainCard('localites', ex.localites)}
          ${explainCard('ccn', ex.ccn)}
        </div>
      </section>
      ${coverageHtml}
      <section class="ti-section">
        <h3>A. Synthèse ${escapeHtml(entityType === 'territoire' ? 'territoriale' : 'administrative')}</h3>
        ${line('Type', { value: profilePayload?.entity?.admin_type || entityType, status: 'confirmed' })}
        ${line('Province', s.synthesis?.province || { value: profilePayload?.entity?.hierarchy?.province, status: profilePayload?.entity?.hierarchy?.province ? 'confirmed' : 'unavailable' })}
        ${line('Zone FDSU', s.synthesis?.fdsu_zone || { value: profilePayload?.entity?.fdsu_zone, status: profilePayload?.entity?.fdsu_zone ? 'confirmed' : 'partial' })}
        ${line('Population', s.synthesis?.population || profilePayload?.population)}
        ${line('Superficie', s.synthesis?.area_km2)}
        ${line('Densité', s.synthesis?.density)}
        ${entityType === 'territoire' || entityType === 'province' ? line('Collectivités', s.synthesis?.collectivites, 'collectivites') : ''}
        ${entityType !== 'localite' && entityType !== 'groupement' ? line('Groupements', s.synthesis?.groupements, 'groupements') : ''}
        ${hideLocalityCount ? '' : line('Localités', s.synthesis?.localities, 'localites')}
        ${entityType === 'localite' ? line('Rattachement parent', { value: profilePayload?.entity?.parent?.name, status: profilePayload?.entity?.parent ? 'confirmed' : 'partial' }) : ''}
      </section>
      <section class="ti-section">
        <h3>B. Situation numérique</h3>
        ${line('Sites 20 476', s.digital?.sites_fdsu_presents?.sites_20476 || s.programs?.sites_20476, 'sites_20476')}
        <p class="ti-note">Programme : Planification stratégique · Statuts individuels : en cours de consolidation · Données partielles</p>
        ${line('Sites 300', s.digital?.sites_fdsu_presents?.sites_300 || s.programs?.sites_300, 'sites_300')}
        <p class="ti-note">Programme : Planifié · Statuts individuels : en cours de consolidation · Données intégrées</p>
        ${line('Sites 40', s.digital?.sites_fdsu_presents?.sites_40 || s.programs?.sites_40, 'sites_40')}
        <p class="ti-note">Programme : En cours de déploiement · Statuts individuels : en cours de consolidation · Données intégrées</p>
        ${line('CCN', s.digital?.ccn_presents_ou_proposes || s.programs?.ccn, 'ccn')}
        <p class="ti-note">Programme : En préparation · Inventaire DEMO · ≠ opérationnel production</p>
        ${line('Télécom', s.digital?.infrastructures_telecom, 'telecom')}
        ${line('Opérateurs', s.digital?.operateurs_presents, 'telecom')}
        ${line('Fibre (nœuds FTTX)', s.digital?.fibre, 'fiber')}
      </section>
      <section class="ti-section">
        <h3>C. Services publics</h3>
        ${line('Santé', s.public_services?.etablissements_sante, 'health')}
        ${line('Écoles', s.public_services?.ecoles)}
        ${line('Administrations', s.public_services?.administrations)}
        ${line('Marchés', s.public_services?.marches)}
      </section>
      <section class="ti-section">
        <h3>D–F. Accessibilité</h3>
        ${line('Routes', s.accessibility?.routes, 'routes')}
        ${line('Longueur routes (km)', s.accessibility?.routes_length_km, 'routes')}
        ${line('Aérodromes (signal)', s.accessibility?.aerodromes)}
        ${line('Énergie', s.energy?.disponibilite)}
      </section>
      <section class="ti-section">
        <h3>I. Recommandations de pilotage</h3>
        <div class="ti-recs">${recHtml}</div>
      </section>
      <section class="ti-section">
        <h3>L. Justification</h3>
        <p>Doctrine : ${escapeHtml(explain?.doctrine?.title || explain?.doctrine?.id)} v${escapeHtml(explain?.doctrine?.version)}</p>
        <ul>${(explain?.assumptions || []).map((a) => `<li>${escapeHtml(humanizeBusinessText(a))}</li>`).join('')}</ul>
      </section>
    `;

    box.querySelectorAll('.ti-explain-action').forEach((btn) => {
      btn.addEventListener('click', () => {
        const domain = btn.getAttribute('data-domain');
        const action = btn.getAttribute('data-action');
        if (!domain) return;
        if (action === 'map' || action === 'details' || action === 'impact') {
          openDetailDrawer(domain);
        }
      });
    });
    box.querySelectorAll('.ti-kpi-line.is-clickable').forEach((el) => {
      const open = () => openDetailDrawer(el.getAttribute('data-domain'));
      el.addEventListener('click', open);
      el.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); open(); }
      });
    });
  }

  function fillTerritorySelect(items) {
    const select = document.querySelector('#ti-territory-select');
    if (!select) return;
    const current = select.value || tiState.selectedId || '';
    select.innerHTML = `<option value="">Sélectionner un territoire…</option>${items.map((t) => `
      <option value="${escapeHtml(t.territory_id)}">${escapeHtml(t.territory_name)} — ${escapeHtml(t.province)} (${escapeHtml(t.fdsu_zone)})${t.is_demo_focus ? ' ★' : ''}</option>
    `).join('')}`;
    if (current) select.value = current;
  }

  function fieldVal(f) {
    return f && typeof f === 'object' ? f.value : f;
  }

  function fieldStatus(f) {
    return f && typeof f === 'object' ? f.status : 'confirmed';
  }

  function loadEntity(entityId, opts = {}) {
    if (!entityId) return Promise.resolve();
    const pushHash = opts.pushHash !== false;
    tiState.selectedId = entityId;
    if (pushHash) setHashEntity(entityId);
    const banner = document.querySelector('#ti-banner');
    if (banner) banner.textContent = 'Chargement de la synthèse multi-échelle…';

    const isTerritory = String(entityId).toUpperCase().startsWith('TERRITOIRE');
    const entityPromise = fetchJson(`/api/territorial-intelligence/entities/${encodeURIComponent(entityId)}`)
      .catch(() => fetchJson(`/api/territorial-intelligence/territories/${encodeURIComponent(entityId)}`));

    return entityPromise.then((bundle) => {
      const mapPromise = bundle.map_payload
        ? Promise.resolve(bundle.map_payload)
        : fetchJson(`/api/territorial-intelligence/entities/${encodeURIComponent(entityId)}/map`)
          .catch(() => fetchJson(`/api/territorial-intelligence/territories/${encodeURIComponent(entityId)}/map`));

      const extras = isTerritory
        ? Promise.all([
          fetchJson(`/api/territorial-intelligence/territories/${encodeURIComponent(entityId)}/recommendations`).catch(() => null),
          fetchJson(`/api/territorial-intelligence/territories/${encodeURIComponent(entityId)}/explain`).catch(() => null),
        ])
        : Promise.resolve([null, null]);

      return Promise.all([Promise.resolve(bundle), mapPromise, extras]).then(([profile, mapPayload, pair]) => {
        const recs = pair && pair[0];
        const explain = pair && pair[1];
        if (mapPayload && mapPayload.symbology) applySymbologyRegistry(mapPayload.symbology);
        tiState.profile = profile;
        tiState.entity = profile.entity || null;
        tiState.explainability = profile.explainability || null;
        const p = profile.profile || {};
        const entity = profile.entity || {};
        const confFr = confidenceLabel(p.confidence_level || profile.confidence);
        const title = document.querySelector('#ti-territory-title');
        const adminLabel = entity.admin_type || entity.type || 'Territoire';
        const displayName = entity.name || p.territory_name || entityId;
        const province = (entity.hierarchy && entity.hierarchy.province) || p.province || '';
        const zone = entity.fdsu_zone || p.fdsu_zone || '';
        if (title) {
          title.textContent = zone
            ? (displayName + ' — ' + adminLabel + (province ? ' · ' + province : '') + ' · Zone ' + zone)
            : (displayName + ' — ' + adminLabel + (province ? ' · ' + province : ''));
        }
        renderBreadcrumb(profile.breadcrumb);
        renderChildren(
          profile.children || (profile.administrative && profile.administrative.children) || [],
          profile.administrative && profile.administrative.children_level
        );

        if (banner) {
          const layers = (mapPayload && mapPayload._meta && mapPayload._meta.layer_counts)
            || (profile.map && profile.map.layer_counts)
            || {};
          const layerSummary = Object.entries(layers)
            .filter(([k]) => !String(k).startsWith('_'))
            .map(([k, v]) => (KIND_LABELS[k] || k) + ':' + v)
            .join(' · ');
          const featCount = (mapPayload && mapPayload._meta && mapPayload._meta.feature_count)
            || (profile.map && profile.map.feature_count)
            || 0;
          banner.textContent = adminLabel + ' ' + displayName + '. Confiance ' + confFr + '. Carte : ' + featCount + ' objets (' + layerSummary + ').';
        }

        const popField = profile.population || p.population;
        const healthField = profile.health || (profile.sections && profile.sections.public_services && profile.sections.public_services.etablissements_sante);
        const sitesField = profile.sections && profile.sections.programs && profile.sections.programs.sites_20476;
        const sites300Field = profile.sections && profile.sections.programs && profile.sections.programs.sites_300;
        const ccnField = profile.ccn || (profile.sections && profile.sections.programs && profile.sections.programs.ccn);
        const scoreField = profile.score || (profile.sections && profile.sections.priority && profile.sections.priority.score);

        setKpi('#ti-kpi-pop', popField);
        setKpi('#ti-kpi-sites', sitesField);
        setKpi('#ti-kpi-sites300', sites300Field);
        setKpi('#ti-kpi-ccn', ccnField);
        setKpi('#ti-kpi-health', healthField);
        setKpi('#ti-kpi-score', scoreField);
        setKpi('#ti-kpi-conf', { value: confFr, status: (p.confidence_level || profile.confidence) === 'high' ? 'confirmed' : 'partial' });

        if (global.Edvs && global.Edvs.mountKpiStrip) {
          const host = document.querySelector('#ti-edvs-kpi-host');
          const legacy = document.querySelector('#ti-kpi-legacy');
          if (host) {
            host.hidden = false;
            if (legacy) legacy.hidden = true;
            const colorFor = (status) => (global.EdvsColors && global.EdvsColors.forStatus(status) && global.EdvsColors.forStatus(status).token) || 'blue';
            const cov = profile.coverage || {};
            const rateVal = fieldVal(cov.coverage_rate_pct);
            global.Edvs.mountKpiStrip('#ti-edvs-kpi-host', [
              { label: 'Population', value: fieldVal(popField), icon: 'people', color: colorFor(fieldStatus(popField)), confidence: confFr },
              { label: 'Pop. couverte', value: fieldVal(cov.population_covered), icon: 'people', color: 'green', confidence: confidenceLabel(cov.population_covered && cov.population_covered.confidence) },
              { label: 'Pop. non couverte', value: fieldVal(cov.population_uncovered), icon: 'people', color: 'orange', confidence: confidenceLabel(cov.population_uncovered && cov.population_uncovered.confidence) },
              { label: 'Taux couverture', value: rateVal != null ? (String(rateVal) + ' %') : '—', icon: 'gauge', color: 'blue', confidence: confidenceLabel(cov.coverage_rate_pct && cov.coverage_rate_pct.confidence) },
              { label: 'Santé', value: fieldVal(healthField), icon: 'data', color: 'green', confidence: 'Élevée' },
              { label: 'Sites 20 476', value: fieldVal(sitesField), icon: 'sites', color: 'blue', confidence: 'Élevée' },
              { label: 'Confiance', valueDisplay: confFr, value: confFr, icon: 'gauge', color: 'blue', confidence: confFr },
            ]);
          }
        }

        const legend = (mapPayload && mapPayload.legend) || (profile.map && profile.map.legend) || [];
        mountTiLegend(legend);
        renderMap((mapPayload && mapPayload.geojson) || { type: 'FeatureCollection', features: [] }, legend);
        renderSections(profile, recs, explain, profile.coverage);
      });
    }).catch(() => {
      if (banner) banner.textContent = 'Synthèse territoriale indisponible — vérifier l’API.';
    });
  }

  function loadTerritory(territoryId) {
    return loadEntity(territoryId, { pushHash: true });
  }

  function loadTerritoryList() {
    const q = document.querySelector('#ti-search')?.value || '';
    const province = document.querySelector('#ti-filter-province')?.value || '';
    const zone = document.querySelector('#ti-filter-zone')?.value || '';
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (province) params.set('province', province);
    if (zone) params.set('zone', zone);
    params.set('limit', '500');
    return fetchJson(`/api/territorial-intelligence/territories?${params.toString()}`)
      .then((payload) => {
        tiState.territories = payload.territories || [];
        fillTerritorySelect(tiState.territories);
        const dungu = tiState.territories.find((t) => t.is_demo_focus) || tiState.territories[0];
        if (dungu && !tiState.selectedId) {
          const select = document.querySelector('#ti-territory-select');
          if (select) select.value = dungu.territory_id;
          return loadTerritory(dungu.territory_id);
        }
        if (tiState.selectedId) return loadTerritory(tiState.selectedId);
        return null;
      });
  }

  function bindUi() {
    const root = document.querySelector('#territorial-intelligence-panel');
    if (!root || root.dataset.bound === 'true') return;
    root.dataset.bound = 'true';
    document.querySelector('#ti-territory-select')?.addEventListener('change', (event) => {
      loadTerritory(event.target.value);
    });
    document.querySelector('#ti-search-btn')?.addEventListener('click', () => loadTerritoryList());
    document.querySelector('#ti-search')?.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') loadTerritoryList();
    });
    document.querySelector('#ti-filter-zone')?.addEventListener('change', () => loadTerritoryList());
    document.querySelector('#ti-filter-province')?.addEventListener('change', () => loadTerritoryList());
    document.querySelector('#ti-back-national')?.addEventListener('click', () => {
      global.location.hash = 'decision-view';
    });
    document.querySelector('#ti-open-ccn')?.addEventListener('click', () => {
      global.location.hash = 'ccn';
    });
    document.querySelector('#ti-detail-close')?.addEventListener('click', () => closeDetailDrawer());
    document.querySelector('#ti-detail-prev')?.addEventListener('click', () => {
      if (tiState.detail.page > 1) {
        tiState.detail.page -= 1;
        loadDetailPage();
      }
    });
    document.querySelector('#ti-detail-next')?.addEventListener('click', () => {
      const pages = tiState.detail.payload?.pagination?.pages || 1;
      if (tiState.detail.page < pages) {
        tiState.detail.page += 1;
        loadDetailPage();
      }
    });
    document.querySelector('#ti-detail-search')?.addEventListener('input', (event) => {
      tiState.detail.search = event.target.value || '';
      if (tiState.detail.payload) renderDetailTable(tiState.detail.payload);
    });
    document.querySelector('#ti-detail-filter')?.addEventListener('change', (event) => {
      tiState.detail.filter = event.target.value || '';
      if (tiState.detail.payload) renderDetailTable(tiState.detail.payload);
    });
    document.querySelector('#ti-detail-tech-toggle')?.addEventListener('click', () => {
      tiState.detail.showTech = !tiState.detail.showTech;
      const tech = document.querySelector('#ti-detail-tech');
      if (tech) tech.hidden = !tiState.detail.showTech;
    });
    document.querySelector('#ti-toggle-tst')?.addEventListener('click', () => {
      const drawer = document.querySelector('#ti-tst-drawer');
      const mapSection = document.querySelector('#ti-map')?.closest('section');
      const btn = document.querySelector('#ti-toggle-tst');
      if (!drawer) return;
      const open = drawer.hasAttribute('hidden');
      if (open) {
        drawer.hidden = false;
        drawer.removeAttribute('hidden');
        if (mapSection) mapSection.hidden = true;
        if (btn) btn.textContent = 'Masquer la synthèse territoriale';
        if (tiState.map) {
          try { tiState.map.remove(); } catch (_e) { /* */ }
          tiState.map = null;
          tiState.layer = null;
          tiState.detailLayer = null;
          const el = document.querySelector('#ti-map');
          if (el) { el.innerHTML = ''; delete el._leaflet_id; }
        }
        if (global.TerritorialSummary?.mount) {
          if (tiState.tstInstance?.destroy) tiState.tstInstance.destroy();
          global.TerritorialSummary.mount('#ti-tst-host', {
            metric: global.TerritorialContext?.get()?.metric || 'priority',
            preserveContext: true,
          }).then((api) => { tiState.tstInstance = api; });
        }
      } else {
        drawer.hidden = true;
        drawer.setAttribute('hidden', '');
        if (mapSection) mapSection.hidden = false;
        if (btn) btn.textContent = 'Afficher la synthèse territoriale';
        if (tiState.tstInstance?.destroy) {
          tiState.tstInstance.destroy();
          tiState.tstInstance = null;
        }
        ensureMap();
        if (tiState.mapGeojson) renderMap(tiState.mapGeojson);
        global.setTimeout(() => tiState.map?.invalidateSize(), 80);
      }
    });
  }

  function initializeTerritorialIntelligenceModule() {
    bindUi();
    ensureMap();
    if (global.Edvs?.mountPresentationButton) {
      global.Edvs.mountPresentationButton('#ti-edvs-presentation-slot');
    }
    const hash = (global.location.hash || '').replace(/^#/, '');
    const hashEntity = hash.startsWith('territorial-intelligence/')
      ? decodeURIComponent(hash.split('/')[1] || '')
      : '';
    return fetchJson('/api/territorial-intelligence/symbology')
      .then(applySymbologyRegistry)
      .catch(() => null)
      .then(() => {
        if (hashEntity && !String(hashEntity).toUpperCase().startsWith('TERRITOIRE')) {
          tiState.selectedId = hashEntity;
          return loadTerritoryList().then(() => {
            tiState.initialized = true;
            return loadEntity(hashEntity, { pushHash: false });
          });
        }
        return loadTerritoryList().then(() => {
          tiState.initialized = true;
          if (hashEntity) {
            const select = document.querySelector('#ti-territory-select');
            if (select) select.value = hashEntity;
            return loadEntity(hashEntity, { pushHash: false });
          }
          global.setTimeout(() => tiState.map?.invalidateSize(), 120);
          return null;
        });
      });
  }

  global.tiState = tiState;
  global.loadEntity = loadEntity;
  global.initializeTerritorialIntelligenceModule = initializeTerritorialIntelligenceModule;
})(window);
