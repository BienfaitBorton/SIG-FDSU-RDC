(function initTerritorialIntelligenceModule(global) {
  const API_BASE = 'http://127.0.0.1:8001';

  const LAYER_STYLES = {
    territory_boundary: { color: '#38bdf8', weight: 2, fillOpacity: 0.06 },
    site_fdsu: { radius: 5, color: '#fbbf24', fillColor: '#f59e0b', fillOpacity: 0.9 },
    ccn: { radius: 7, color: '#a78bfa', fillColor: '#8b5cf6', fillOpacity: 0.9 },
    health: { radius: 5, color: '#34d399', fillColor: '#10b981', fillOpacity: 0.9 },
    telecom: { radius: 6, color: '#38bdf8', fillColor: '#0ea5e9', fillOpacity: 0.9 },
    fiber: { radius: 7, color: '#f472b6', fillColor: '#db2777', fillOpacity: 0.95 },
    fiber_line: { color: '#db2777', weight: 3, opacity: 0.85 },
    route: { color: '#94a3b8', weight: 3, opacity: 0.9 },
    groupement: { radius: 6, color: '#fcd34d', fillColor: '#eab308', fillOpacity: 0.85 },
    locality: { radius: 3, color: '#cbd5e1', fillColor: '#64748b', fillOpacity: 0.7 },
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
    admin: ['groupement', 'locality'],
  };

  const tiState = {
    initialized: false,
    territories: [],
    selectedId: null,
    profile: null,
    explainability: null,
    mapGeojson: null,
    map: null,
    layer: null,
    detailLayer: null,
    domainLayers: {},
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
      partial: 'Partiel', operational: 'Opérationnel',
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
      operational: 'opérationnel', confirmed: 'confirmé', estimated: 'estimé', partial: 'partiel',
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

  function addFeatureToMap(feature, targetGroup) {
    const kind = feature.properties?.kind;
    const geomType = feature.geometry?.type;
    const style = LAYER_STYLES[kind] || LAYER_STYLES.locality;
    const name = feature.properties?.name || feature.properties?.code || kind;

    if (kind === 'territory_boundary' || geomType === 'Polygon' || geomType === 'MultiPolygon') {
      const layer = global.L.geoJSON(feature, {
        style: LAYER_STYLES.territory_boundary,
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
          lyr.bindPopup(`${escapeHtml(kind === 'fiber_line' ? 'Fibre' : 'Route')}<br>${escapeHtml(name)}`);
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
    }).bindPopup(`<strong>${escapeHtml(kind)}</strong><br>${escapeHtml(name)}`);
    marker.addTo(targetGroup);
    return marker;
  }

  function renderMap(geojson) {
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
        tiState.domainLayers[kind] = global.L.layerGroup().addTo(tiState.layer);
      }
      addFeatureToMap(feature, tiState.domainLayers[kind]);
    });
    fitAllLayers();
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

  function renderSections(profilePayload, recommendations, explain) {
    const box = document.querySelector('#ti-sections');
    if (!box) return;
    const s = profilePayload?.sections || {};
    const p = profilePayload?.profile || {};
    const ex = profilePayload?.explainability || tiState.explainability || {};

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
      <section class="ti-section">
        <h3>A. Synthèse territoriale</h3>
        ${line('Province', s.synthesis?.province)}
        ${line('Zone FDSU', s.synthesis?.fdsu_zone)}
        ${line('Population', s.synthesis?.population)}
        ${line('Superficie', s.synthesis?.area_km2)}
        ${line('Densité', s.synthesis?.density)}
        ${line('Collectivités', s.synthesis?.collectivites, 'collectivites')}
        ${line('Groupements', s.synthesis?.groupements, 'groupements')}
        ${line('Localités', s.synthesis?.localities, 'localites')}
      </section>
      <section class="ti-section">
        <h3>B. Situation numérique</h3>
        ${line('Sites 20 476', s.digital?.sites_fdsu_presents?.sites_20476 || s.programs?.sites_20476, 'sites_20476')}
        ${line('Sites 300', s.digital?.sites_fdsu_presents?.sites_300 || s.programs?.sites_300, 'sites_300')}
        ${line('Sites 40', s.digital?.sites_fdsu_presents?.sites_40 || s.programs?.sites_40, 'sites_40')}
        ${line('CCN', s.digital?.ccn_presents_ou_proposes || s.programs?.ccn, 'ccn')}
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
        <h3>I. Recommandations DG</h3>
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

  function loadTerritory(territoryId) {
    if (!territoryId) return Promise.resolve();
    tiState.selectedId = territoryId;
    const banner = document.querySelector('#ti-banner');
    if (banner) banner.textContent = 'Chargement du profil territorial…';
    return Promise.all([
      fetchJson(`/api/territorial-intelligence/territories/${encodeURIComponent(territoryId)}`),
      fetchJson(`/api/territorial-intelligence/territories/${encodeURIComponent(territoryId)}/map`),
      fetchJson(`/api/territorial-intelligence/territories/${encodeURIComponent(territoryId)}/recommendations`),
      fetchJson(`/api/territorial-intelligence/territories/${encodeURIComponent(territoryId)}/explain`),
    ]).then(([profile, map, recs, explain]) => {
      tiState.profile = profile;
      tiState.explainability = profile.explainability || null;
      const p = profile.profile || {};
      const confFr = confidenceLabel(p.confidence_level);
      const title = document.querySelector('#ti-territory-title');
      if (title) title.textContent = `${p.territory_name || ''} — ${p.province || ''} · Zone ${p.fdsu_zone || ''}`;
      if (banner) {
        const layers = map?._meta?.layer_counts || {};
        const layerSummary = Object.entries(layers)
          .filter(([k]) => !k.startsWith('_'))
          .map(([k, v]) => `${k}:${v}`)
          .join(' · ');
        banner.textContent = p.is_demo_focus
          ? `Cas de démonstration : ${p.territory_name}. Confiance ${confFr}. Carte : ${map?._meta?.feature_count || 0} objets (${layerSummary}).`
          : `Profil consolidé. Confiance ${confFr}. Carte : ${map?._meta?.feature_count || 0} objets.`;
      }
      setKpi('#ti-kpi-pop', p.population);
      setKpi('#ti-kpi-sites', profile.sections?.programs?.sites_20476);
      setKpi('#ti-kpi-sites300', profile.sections?.programs?.sites_300);
      setKpi('#ti-kpi-ccn', profile.sections?.programs?.ccn);
      setKpi('#ti-kpi-health', profile.sections?.public_services?.etablissements_sante);
      setKpi('#ti-kpi-score', profile.sections?.priority?.score);
      setKpi('#ti-kpi-conf', { value: confFr, status: p.confidence_level === 'high' ? 'confirmed' : 'partial' });

      if (global.Edvs?.mountKpiStrip) {
        const host = document.querySelector('#ti-edvs-kpi-host');
        const legacy = document.querySelector('#ti-kpi-legacy');
        if (host) {
          host.hidden = false;
          if (legacy) legacy.hidden = true;
          const fieldVal = (f) => (f && typeof f === 'object' ? f.value : f);
          const fieldStatus = (f) => (f && typeof f === 'object' ? f.status : 'confirmed');
          const colorFor = (status) => (global.EdvsColors?.forStatus(status)?.token || 'blue');
          global.Edvs.mountKpiStrip('#ti-edvs-kpi-host', [
            { label: 'Population', value: fieldVal(p.population), icon: 'people', color: colorFor(fieldStatus(p.population)), confidence: confFr },
            { label: 'Sites 20 476', value: fieldVal(profile.sections?.programs?.sites_20476), icon: 'sites', color: 'blue', confidence: 'Élevée' },
            { label: 'Sites 300', value: fieldVal(profile.sections?.programs?.sites_300), icon: 'program', color: 'orange', confidence: 'Élevée' },
            { label: 'CCN', value: fieldVal(profile.sections?.programs?.ccn), icon: 'ccn', color: colorFor(fieldStatus(profile.sections?.programs?.ccn)), confidence: 'Moyenne' },
            { label: 'Santé', value: fieldVal(profile.sections?.public_services?.etablissements_sante), icon: 'data', color: 'green', confidence: 'Élevée' },
            { label: 'Score', value: fieldVal(profile.sections?.priority?.score), icon: 'decision', color: 'orange', confidence: confFr },
            { label: 'Confiance', valueDisplay: confFr, value: confFr, icon: 'gauge', color: 'blue', confidence: confFr },
          ]);
          if (global.UxPremium?.mountMapLegend) {
            global.UxPremium.mountMapLegend('#ti-map', {
              id: 'ux-legend-ti',
              title: 'Légende',
              items: [
                { className: 'is-poly', label: 'Territoire' },
                { className: 'is-site', label: 'Site FDSU' },
                { className: 'is-health', label: 'Santé' },
                { className: 'is-ccn', label: 'Télécom / Fibre / Routes' },
              ],
            });
          }
        }
      }
      renderMap(map.geojson);
      renderSections(profile, recs, explain);
    }).catch(() => {
      if (banner) banner.textContent = 'Profil territorial indisponible — vérifier l’API.';
    });
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
    const hashTerritory = hash.startsWith('territorial-intelligence/')
      ? decodeURIComponent(hash.split('/')[1] || '')
      : '';
    return loadTerritoryList().then(() => {
      tiState.initialized = true;
      if (hashTerritory) {
        const select = document.querySelector('#ti-territory-select');
        if (select) select.value = hashTerritory;
        return loadTerritory(hashTerritory);
      }
      global.setTimeout(() => tiState.map?.invalidateSize(), 120);
      return null;
    });
  }

  global.tiState = tiState;
  global.initializeTerritorialIntelligenceModule = initializeTerritorialIntelligenceModule;
})(window);
