/**
 * Tableau de Synthèse Territoriale (TST) v1.1
 * TerritorialSummary.mount / update / resize / destroy
 * Drill-down cartographique continu — une seule instance Leaflet par conteneur.
 */
(function initTerritorialSummary(global) {
  const API_BASE = `${global.location.protocol}//${global.location.hostname}:8001`;
  const COLOR_MAP = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#ca8a04',
    low: '#4ade80',
    none: '#94a3b8',
    insufficient: '#64748b',
    partial: '#38bdf8',
  };

  const instances = new WeakMap();
  let instanceSeq = 0;

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function fetchJson(path, signal) {
    return fetch(`${API_BASE}${path}`, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      signal,
    }).then((response) => {
      if (!response.ok) throw new Error(path);
      return response.json();
    });
  }

  function norm(value) {
    return String(value || '').trim().toLowerCase().replace(/[-_]+/g, ' ').replace(/\s+/g, ' ');
  }

  function featureList(payload) {
    const raw = payload?.features;
    if (Array.isArray(raw)) return raw;
    if (raw && Array.isArray(raw.features)) return raw.features;
    return [];
  }

  function createController(container, options) {
    const opts = {
      metric: 'priority',
      level: 'province',
      parentId: null,
      context: null,
      onSelectionChange: null,
      preserveContext: true,
      showLegend: true,
      showKpis: true,
      allowDrilldown: true,
      ...options,
    };

    const id = `tst-map-${++instanceSeq}`;
    const state = {
      id,
      opts,
      container,
      map: null,
      layer: null,
      parentLayer: null,
      abort: null,
      requestSeq: 0,
      geometryCache: { provinces: null, territoires: null },
      layerPayload: null,
      metrics: [],
      trail: [{ level: 'rdc', id: 'rdc', label: 'RDC' }],
      selection: null,
      destroyed: false,
      unsubContext: null,
      provinceContext: null,
      territoryContext: null,
    };

    container.classList.add('tst-root');
    container.dataset.tstInstance = id;
    container.innerHTML = `
      <div class="tst-toolbar">
        <label class="tst-metric-label">Métrique
          <select class="tst-metric-select" aria-label="Métrique territoriale"></select>
        </label>
        <nav class="tst-breadcrumb" aria-label="Fil d’Ariane territorial"></nav>
        <span class="tst-status" aria-live="polite">Chargement…</span>
      </div>
      <div class="tst-layout">
        <div class="tst-map-shell ux-map-shell">
          <div id="${id}" class="tst-map" role="region" aria-label="Carte de synthèse territoriale"></div>
          <div class="tst-map-banner hidden" role="status"></div>
          <aside class="tst-legend" aria-label="Légende"></aside>
        </div>
        <aside class="tst-panel" aria-label="Synthèse territoriale">
          <div class="tst-kpis"></div>
          <div class="tst-summary"></div>
        </aside>
      </div>
    `;

    function els() {
      return {
        select: container.querySelector('.tst-metric-select'),
        breadcrumb: container.querySelector('.tst-breadcrumb'),
        status: container.querySelector('.tst-status'),
        legend: container.querySelector('.tst-legend'),
        kpis: container.querySelector('.tst-kpis'),
        summary: container.querySelector('.tst-summary'),
        mapHost: container.querySelector(`#${id}`),
        banner: container.querySelector('.tst-map-banner'),
      };
    }

    function setStatus(text, kind) {
      const { status } = els();
      if (!status) return;
      status.textContent = text;
      status.className = `tst-status${kind ? ` is-${kind}` : ''}`;
    }

    function setBanner(html, visible) {
      const { banner } = els();
      if (!banner) return;
      banner.innerHTML = html || '';
      banner.classList.toggle('hidden', !visible);
    }

    function renderBreadcrumb() {
      const { breadcrumb } = els();
      if (!breadcrumb) return;
      breadcrumb.innerHTML = state.trail.map((step, index) => {
        const last = index === state.trail.length - 1;
        return `
          <button type="button" class="tst-crumb${last ? ' is-current' : ''}" data-tst-crumb="${index}">
            ${escapeHtml(step.label)}
          </button>
          ${last ? '' : '<span class="tst-crumb-sep" aria-hidden="true">›</span>'}
        `;
      }).join('');
    }

    function renderLegend(legend) {
      const { legend: host } = els();
      if (!host || !state.opts.showLegend) return;
      host.innerHTML = `
        <p class="tst-legend-title">Légende</p>
        <ul>
          ${(legend || []).map((item) => `
            <li><span class="tst-swatch" style="background:${escapeHtml(item.color || COLOR_MAP[item.class_id] || '#64748b')}"></span>${escapeHtml(item.label)}</li>
          `).join('')}
        </ul>
      `;
    }

    function renderKpis(features, meta) {
      const { kpis } = els();
      if (!kpis || !state.opts.showKpis) return;
      const list = features || [];
      const ok = list.filter((f) => f.properties?.status === 'ok' || f.properties?.status === 'partial');
      const insufficient = list.length - ok.length;
      const values = ok.map((f) => Number(f.properties.value)).filter((n) => Number.isFinite(n));
      const max = values.length ? Math.max(...values) : null;
      const withGeom = meta?.geometry_count != null
        ? meta.geometry_count
        : list.filter((f) => f.geometry).length;
      const items = [
        { label: 'Entités', value: meta?.expected_count != null ? meta.expected_count : list.length },
        { label: 'Avec géométrie', value: withGeom },
        { label: 'Avec données', value: ok.length },
        { label: 'Insuffisantes', value: insufficient },
        { label: 'Max métrique', value: max == null ? 'Données insuffisantes' : max },
      ];
      if (global.Edvs?.mountKpiStrip) {
        const hostId = `${state.id}-kpi`;
        kpis.innerHTML = `<div id="${hostId}" class="edvs-kpi-grid tst-kpi-host"></div>`;
        global.Edvs.mountKpiStrip(`#${hostId}`, items.map((item) => ({
          label: item.label,
          value: item.value,
          color: 'blue',
          confidence: 'medium',
          icon: 'map',
        })));
      } else {
        kpis.innerHTML = items.map((item) => `
          <article class="tst-kpi-card"><p>${escapeHtml(item.label)}</p><strong>${escapeHtml(item.value)}</strong></article>
        `).join('');
      }
    }

    function renderEntityList(features, title, message) {
      const { summary } = els();
      if (!summary) return;
      const list = (features || []).map((f) => {
        const p = f.properties || {};
        return `<button type="button" class="tst-territory-item" data-tst-entity='${escapeHtml(JSON.stringify({
          level: p.level,
          id: p.id,
          name: p.name,
          province: p.province || state.provinceContext,
          territoire: p.territoire || state.territoryContext,
        }))}'>
          <strong>${escapeHtml(p.name)}</strong>
          <span>${escapeHtml(p.administrative_level || '')} — ${escapeHtml(p.display || 'Données insuffisantes')}</span>
        </button>`;
      }).join('');
      summary.innerHTML = `
        <h3>${escapeHtml(title || 'Entités')}</h3>
        ${message ? `<p class="tst-fallback-msg">${escapeHtml(message)}</p>` : ''}
        <div class="tst-territory-list">${list || '<p>Données insuffisantes</p>'}</div>
        <button type="button" class="secondary-button" data-tst-back>Revenir au niveau précédent</button>
      `;
    }

    function renderSummary(summary) {
      const { summary: host } = els();
      if (!host) return;
      if (!summary) {
        host.innerHTML = global.UxPremium?.stateHtml
          ? global.UxPremium.stateHtml('empty', 'Sélectionnez un territoire', 'Cliquez une province sur la carte pour afficher la synthèse.')
          : '<p>Sélectionnez un territoire.</p>';
        return;
      }
      const entity = summary.entity || {};
      const fields = summary.fields || [];
      host.innerHTML = `
        <header class="tst-summary-head">
          <p class="panel-label">${escapeHtml(entity.administrative_level || entity.level || '')}</p>
          <h3>${escapeHtml(entity.name || '')}</h3>
        </header>
        <dl class="tst-summary-fields">
          ${fields.map((field) => `
            <div><dt>${escapeHtml(field.label)}</dt><dd>${escapeHtml(field.display)}</dd></div>
          `).join('')}
        </dl>
        <p class="tst-source"><strong>Source :</strong> ${escapeHtml(summary.source || '—')}</p>
        <p class="tst-source"><strong>Mise à jour :</strong> ${escapeHtml(String(summary.updated_at || '').slice(0, 19).replace('T', ' '))}</p>
        <div class="tst-actions">
          ${(summary.actions || []).map((action) => `
            <button type="button" class="secondary-button" data-tst-hash="${escapeHtml(action.hash || '')}">${escapeHtml(action.label)}</button>
          `).join('')}
        </div>
      `;
    }

    function ensureMap() {
      if (state.destroyed) return null;
      if (typeof global.L === 'undefined') {
        setStatus('Leaflet indisponible', 'error');
        return null;
      }
      const { mapHost } = els();
      if (!mapHost) return null;
      if (state.map) {
        state.map.invalidateSize();
        return state.map;
      }
      if (mapHost._leaflet_id) {
        setStatus('Conteneur carte déjà initialisé — destroy() requis', 'error');
        return null;
      }
      state.map = global.L.map(mapHost, { zoomControl: true, attributionControl: true })
        .setView([-2.8, 23.5], 5);
      global.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap',
        maxZoom: 18,
      }).addTo(state.map);
      state.parentLayer = global.L.geoJSON(null, {
        style: () => ({
          color: '#38bdf8',
          weight: 3,
          fillColor: '#0ea5e9',
          fillOpacity: 0.06,
          opacity: 0.95,
          interactive: false,
        }),
      }).addTo(state.map);
      state.layer = global.L.geoJSON(null, {
        style: (feature) => styleFeature(feature),
        pointToLayer: (feature, latlng) => global.L.circleMarker(latlng, {
          radius: 6,
          color: '#0f172a',
          weight: 1,
          fillColor: COLOR_MAP[feature?.properties?.class_id] || COLOR_MAP.insufficient,
          fillOpacity: 0.85,
        }),
        onEachFeature: onEachFeature,
      }).addTo(state.map);
      return state.map;
    }

    function styleFeature(feature) {
      const classId = feature?.properties?.class_id || 'insufficient';
      const selected = state.selection && String(state.selection.id) === String(feature?.properties?.id);
      return {
        color: selected ? '#38bdf8' : '#0f172a',
        weight: selected ? 2.5 : 1,
        fillColor: COLOR_MAP[classId] || COLOR_MAP.insufficient,
        fillOpacity: feature?.properties?.status === 'insufficient' ? 0.28 : 0.65,
      };
    }

    function onEachFeature(feature, layer) {
      const p = feature.properties || {};
      const html = `
        <strong>${escapeHtml(p.name || '—')}</strong><br>
        ${escapeHtml(p.administrative_level || p.administrative_type || '')}<br>
        Valeur : ${escapeHtml(p.display || 'Données insuffisantes')}<br>
        Classe : ${escapeHtml(p.class_label || '—')}<br>
        Objets : ${escapeHtml(p.objects_count ?? '—')}<br>
        Source : ${escapeHtml(p.source || '—')}<br>
        <em>Cliquer pour explorer</em>
      `;
      if (global.SigMapTooltips?.bind) {
        global.SigMapTooltips.bind(layer, {
          ...p,
          nom: p.name,
          name: p.name,
          tooltip_html: html,
        }, p.level || 'province', {
          interactive: true,
          direction: 'auto',
          onClick: () => handleSelect(p),
        });
      } else if (layer.bindTooltip) {
        layer.bindTooltip(html, { sticky: true, direction: 'auto', className: 'sig-map-tooltip' });
      }
      layer.on('click', () => handleSelect(p));
    }

    function fitSafe(layerOrBounds) {
      if (!state.map) return;
      try {
        const bounds = layerOrBounds.getBounds ? layerOrBounds.getBounds() : layerOrBounds;
        if (bounds && bounds.isValid && bounds.isValid()) {
          state.map.fitBounds(bounds, { padding: [28, 28], maxZoom: 11 });
        }
      } catch (_e) { /* ignore */ }
    }

    function paintChildren(geo, parentFeature) {
      ensureMap();
      if (!state.map || !state.layer) return false;
      const features = (geo?.features || []).filter((f) => f && f.geometry);
      // 1) Parent outline d'abord (contour renforcé)
      if (state.parentLayer) {
        state.parentLayer.clearLayers();
        if (parentFeature?.geometry) {
          state.parentLayer.addData({
            type: 'FeatureCollection',
            features: [parentFeature],
          });
        }
      }
      // 2) Ajouter enfants, puis retirer l'ancienne couche enfants
      if (!features.length) {
        // Ne pas vider si aucun enfant : conserver parent (ou couche courante)
        if (parentFeature?.geometry) {
          fitSafe(state.parentLayer);
          return false;
        }
        return false;
      }
      const next = global.L.geoJSON(
        { type: 'FeatureCollection', features },
        {
          style: (feature) => styleFeature(feature),
          pointToLayer: (feature, latlng) => global.L.circleMarker(latlng, {
            radius: 6,
            color: '#0f172a',
            weight: 1,
            fillColor: COLOR_MAP[feature?.properties?.class_id] || COLOR_MAP.insufficient,
            fillOpacity: 0.85,
          }),
          onEachFeature: onEachFeature,
        },
      );
      next.addTo(state.map);
      fitSafe(next);
      // 3) Retirer l'ancienne couche enfants seulement après ajout
      if (state.layer) {
        try {
          state.map.removeLayer(state.layer);
          state.layer.clearLayers();
        } catch (_e) { /* */ }
      }
      state.layer = next;
      return true;
    }

    function handleSelect(props) {
      if (!props || !state.opts.allowDrilldown) return;
      const level = props.level || 'province';
      const entity = {
        level,
        id: props.id,
        name: props.name,
        province: props.province || (level === 'province' ? props.name : state.provinceContext),
        territoire: props.territoire || (level === 'territoire' ? props.name : state.territoryContext),
      };
      state.selection = entity;

      if (level === 'province') {
        state.provinceContext = entity.name;
        state.territoryContext = null;
        state.trail = [
          { level: 'rdc', id: 'rdc', label: 'RDC' },
          { level: 'province', id: String(entity.id), label: entity.name },
        ];
        state.opts.level = 'territoire';
        state.opts.parentId = entity.name;
      } else if (level === 'territoire') {
        state.provinceContext = entity.province || state.provinceContext;
        state.territoryContext = entity.name;
        state.trail = [
          { level: 'rdc', id: 'rdc', label: 'RDC' },
          { level: 'province', id: String(state.provinceContext), label: String(state.provinceContext) },
          { level: 'territoire', id: String(entity.id), label: entity.name },
        ];
        state.opts.level = 'collectivite';
        state.opts.parentId = entity.name;
      } else if (level === 'collectivite') {
        state.trail = [
          { level: 'rdc', id: 'rdc', label: 'RDC' },
          { level: 'province', id: String(state.provinceContext), label: String(state.provinceContext) },
          { level: 'territoire', id: String(state.territoryContext), label: String(state.territoryContext) },
          { level: 'collectivite', id: String(entity.id), label: entity.name },
        ];
        state.opts.level = 'groupement';
        state.opts.parentId = entity.name;
      } else if (level === 'groupement') {
        state.trail = state.trail.slice(0, 4).concat([
          { level: 'groupement', id: String(entity.id), label: entity.name },
        ]);
        state.opts.level = 'localite';
        state.opts.parentId = entity.name;
      } else if (level === 'localite') {
        state.trail = state.trail.slice(0, 5).concat([
          { level: 'localite', id: String(entity.id), label: entity.name },
        ]);
        // Sites : panneau uniquement (pas de couche TST dédiée encore)
        state.opts.level = 'site';
        state.opts.parentId = entity.name;
      }

      renderBreadcrumb();
      if (state.opts.preserveContext && global.TerritorialContext) {
        global.TerritorialContext.select(entity);
        global.TerritorialContext.setTrail(state.trail);
      }
      if (typeof state.opts.onSelectionChange === 'function') {
        state.opts.onSelectionChange(entity, state.trail.slice());
      }
      loadSummary(entity);
      if (level === 'localite' || level === 'site') {
        setBanner('Niveau site : ouvrez « Voir les sites » dans le panneau. Aucune géométrie fictive.', true);
        setStatus('Niveau localité / site — liste métier', 'ok');
        return;
      }
      loadLayer();
    }

    function loadSummary(entity) {
      if (!entity) {
        renderSummary(null);
        return;
      }
      const params = new URLSearchParams({
        level: entity.level,
        id: entity.id,
        name: entity.name || '',
      });
      fetchJson(`/api/territorial-summary/entity?${params}`, state.abort?.signal)
        .then(renderSummary)
        .catch(() => {
          renderSummary({
            entity,
            fields: [{ label: 'État', display: 'Données insuffisantes', source: 'TST' }],
            actions: [],
            source: 'TST',
            updated_at: new Date().toISOString(),
          });
        });
    }

    function joinProvinceGeometry(layerPayload, geojson) {
      const byName = new Map();
      featureList(layerPayload).forEach((f) => {
        byName.set(norm(f.properties?.name), f.properties);
        byName.set(norm(f.properties?.id), f.properties);
      });
      const features = (geojson.features || []).map((feature) => {
        const props = feature.properties || {};
        const name = props.nom || props.name || props.province || props.NAME_1;
        const matched = byName.get(norm(name)) || byName.get(norm(props.code));
        return {
          type: 'Feature',
          properties: matched
            ? { ...matched, name: matched.name || name }
            : {
              id: norm(name),
              name,
              level: 'province',
              administrative_level: 'Province',
              display: 'Données insuffisantes',
              class_id: 'insufficient',
              class_label: 'Données insuffisantes',
              objects_count: 0,
              status: 'insufficient',
              source: 'Géométrie seule — métrique absente',
              hint: 'Cliquer pour explorer',
            },
          geometry: feature.geometry,
        };
      }).filter((f) => f.geometry);
      return { type: 'FeatureCollection', features };
    }

    function applyLayerPayload(level, layerPayload, provinceGeo) {
      const features = featureList(layerPayload);
      const geometryStatus = layerPayload.geometry_status
        || (level === 'province' ? 'complete' : null);
      const geometryCount = layerPayload.geometry_count != null
        ? layerPayload.geometry_count
        : features.filter((f) => f.geometry).length;
      const expected = layerPayload.expected_count != null ? layerPayload.expected_count : features.length;
      const parent = layerPayload.parent || null;
      const meta = {
        geometry_status: geometryStatus,
        geometry_count: geometryCount,
        expected_count: expected,
      };

      renderLegend(layerPayload.legend);
      renderKpis(features, meta);

      if (level === 'province') {
        setBanner('', false);
        if (state.parentLayer) state.parentLayer.clearLayers();
        const joined = joinProvinceGeometry(layerPayload, provinceGeo || { features: [] });
        paintChildren(joined, null);
        setStatus(`${joined.features.length} provinces — données réelles`, 'ok');
        return;
      }

      const withGeom = {
        type: 'FeatureCollection',
        features: features.filter((f) => f.geometry),
      };
      const painted = paintChildren(withGeom, parent);

      if (!painted || geometryStatus === 'unavailable') {
        const msg = layerPayload.message
          || 'Les limites détaillées de ce niveau ne sont pas encore disponibles.';
        setBanner(`${escapeHtml(msg)} <button type="button" class="tst-banner-back" data-tst-back>Revenir au niveau précédent</button>`, true);
        // Conserver le parent visible : déjà peint dans paintChildren
        if (parent?.geometry && state.parentLayer) {
          fitSafe(state.parentLayer);
        }
        renderEntityList(
          features,
          `${expected} entité(s) — ${state.opts.parentId || ''}`,
          msg,
        );
        setStatus(`${expected} entités · géométries indisponibles`, 'partial');
        return;
      }

      if (geometryStatus === 'partial') {
        setBanner(
          `Géométries partielles : ${geometryCount}/${expected}. Les entités sans limites restent listées.`,
          true,
        );
        renderEntityList(
          features.filter((f) => !f.geometry),
          `Sans géométrie (${expected - geometryCount})`,
          null,
        );
      } else {
        setBanner('', false);
        if (state.selection) loadSummary(state.selection);
      }
      setStatus(`${geometryCount}/${expected} géométries · ${level}`, 'ok');
    }

    function loadLayer() {
      if (state.destroyed) return;
      if (state.abort) state.abort.abort();
      state.abort = new global.AbortController();
      const seq = ++state.requestSeq;
      setStatus('Chargement…', 'loading');
      // Ne PAS clearLayers ici — conserver la couche parente pendant le fetch

      const metric = state.opts.metric || 'priority';
      const level = state.opts.level || 'province';
      const params = new URLSearchParams({ level, metric });
      if (level !== 'province' && state.opts.parentId) params.set('parent_id', state.opts.parentId);
      if (state.provinceContext) params.set('province', state.provinceContext);
      if (state.territoryContext) params.set('territory', state.territoryContext);

      const layerPromise = fetchJson(`/api/territorial-summary/layer?${params}`, state.abort.signal);
      const geoPromise = level === 'province'
        ? (state.geometryCache.provinces
          ? Promise.resolve(state.geometryCache.provinces)
          : fetchJson('/map/layers/provinces?limit=5000', state.abort.signal).then((g) => {
            state.geometryCache.provinces = g;
            return g;
          }))
        : Promise.resolve(null);

      Promise.all([layerPromise, geoPromise])
        .then(([layerPayload, provinceGeo]) => {
          if (state.destroyed || seq !== state.requestSeq) return;
          state.layerPayload = layerPayload;
          applyLayerPayload(level, layerPayload, provinceGeo);
        })
        .catch((err) => {
          if (err.name === 'AbortError') return;
          if (seq !== state.requestSeq) return;
          setStatus(`Erreur : ${err.message}`, 'error');
          setBanner(
            'Chargement impossible. La couche précédente est conservée. <button type="button" class="tst-banner-back" data-tst-back>Revenir au niveau précédent</button>',
            true,
          );
        });
    }

    function goBackOneLevel() {
      if (state.trail.length <= 1) {
        state.opts.level = 'province';
        state.opts.parentId = null;
        state.selection = null;
        state.provinceContext = null;
        state.territoryContext = null;
        renderSummary(null);
        renderBreadcrumb();
        loadLayer();
        return;
      }
      const idx = state.trail.length - 2;
      navigateToTrailIndex(idx);
    }

    function navigateToTrailIndex(idx) {
      const next = state.trail.slice(0, idx + 1);
      state.trail = next;
      const last = next[next.length - 1];
      if (last.level === 'rdc') {
        state.opts.level = 'province';
        state.opts.parentId = null;
        state.selection = null;
        state.provinceContext = null;
        state.territoryContext = null;
        renderSummary(null);
      } else if (last.level === 'province') {
        state.provinceContext = last.label;
        state.territoryContext = null;
        state.opts.level = 'territoire';
        state.opts.parentId = last.label;
        state.selection = { level: 'province', id: last.id, name: last.label };
        loadSummary(state.selection);
      } else if (last.level === 'territoire') {
        state.territoryContext = last.label;
        state.opts.level = 'collectivite';
        state.opts.parentId = last.label;
        state.selection = {
          level: 'territoire',
          id: last.id,
          name: last.label,
          province: state.provinceContext,
        };
        loadSummary(state.selection);
      } else if (last.level === 'collectivite') {
        state.opts.level = 'groupement';
        state.opts.parentId = last.label;
        state.selection = { level: 'collectivite', id: last.id, name: last.label };
        loadSummary(state.selection);
      } else if (last.level === 'groupement') {
        state.opts.level = 'localite';
        state.opts.parentId = last.label;
        state.selection = { level: 'groupement', id: last.id, name: last.label };
        loadSummary(state.selection);
      }
      renderBreadcrumb();
      if (state.opts.preserveContext && global.TerritorialContext) {
        global.TerritorialContext.setTrail(state.trail);
        if (state.selection) global.TerritorialContext.select(state.selection);
      }
      loadLayer();
    }

    function loadMetrics() {
      return fetchJson('/api/territorial-summary/metrics')
        .then((payload) => {
          state.metrics = payload.metrics || [];
          const { select } = els();
          if (!select) return;
          select.innerHTML = state.metrics.map((metric) => `
            <option value="${escapeHtml(metric.id)}" title="${escapeHtml(metric.source || '')}">${escapeHtml(metric.label)}</option>
          `).join('');
          select.value = state.opts.metric || payload.default_metric || 'priority';
        })
        .catch(() => {
          const { select } = els();
          if (select) {
            select.innerHTML = '<option value="priority">Niveau de priorité territoriale</option>';
          }
        });
    }

    function bindUi() {
      container.addEventListener('click', (event) => {
        const target = event.target;
        if (!(target instanceof global.HTMLElement)) return;
        if (target.closest('[data-tst-back]')) {
          goBackOneLevel();
          return;
        }
        const crumb = target.closest('[data-tst-crumb]');
        if (crumb) {
          navigateToTrailIndex(Number(crumb.getAttribute('data-tst-crumb')));
          return;
        }
        const hashBtn = target.closest('[data-tst-hash]');
        if (hashBtn) {
          const hash = hashBtn.getAttribute('data-tst-hash');
          if (hash) global.location.hash = hash.replace(/^#/, '');
          return;
        }
        const entityBtn = target.closest('[data-tst-entity], [data-tst-territory]');
        if (entityBtn) {
          try {
            const raw = entityBtn.getAttribute('data-tst-entity') || entityBtn.getAttribute('data-tst-territory');
            handleSelect(JSON.parse(raw));
          } catch (_e) { /* ignore */ }
        }
      });
      const { select } = els();
      select?.addEventListener('change', () => {
        state.opts.metric = select.value;
        if (state.opts.preserveContext && global.TerritorialContext) {
          global.TerritorialContext.setMetric(select.value);
        }
        loadLayer();
      });
    }

    function mount() {
      bindUi();
      renderBreadcrumb();
      if (opts.preserveContext && global.TerritorialContext) {
        const snap = global.TerritorialContext.get();
        if (snap.metric) state.opts.metric = snap.metric;
        if (snap.trail?.length) state.trail = snap.trail;
        if (snap.selection) {
          state.selection = snap.selection;
          if (snap.selection.level === 'province') {
            state.opts.level = 'territoire';
            state.opts.parentId = snap.selection.name;
            state.provinceContext = snap.selection.name;
          } else if (snap.selection.level === 'territoire') {
            state.opts.level = 'collectivite';
            state.opts.parentId = snap.selection.name;
            state.provinceContext = snap.selection.province;
            state.territoryContext = snap.selection.name;
          }
        }
        state.unsubContext = global.TerritorialContext.onChange(() => {});
      }
      return loadMetrics().then(() => {
        ensureMap();
        loadLayer();
        if (state.selection) loadSummary(state.selection);
        return api;
      });
    }

    function update(nextOptions = {}) {
      Object.assign(state.opts, nextOptions);
      if (nextOptions.metric) {
        const { select } = els();
        if (select) select.value = nextOptions.metric;
      }
      loadLayer();
    }

    function resize() {
      if (state.map) state.map.invalidateSize();
    }

    function destroy() {
      state.destroyed = true;
      if (state.abort) state.abort.abort();
      if (state.unsubContext) state.unsubContext();
      [state.layer, state.parentLayer].forEach((layer) => {
        if (!layer) return;
        try { layer.clearLayers(); } catch (_e) { /* */ }
      });
      state.layer = null;
      state.parentLayer = null;
      if (state.map) {
        try {
          state.map.off();
          state.map.remove();
        } catch (_e) { /* */ }
        state.map = null;
      }
      const { mapHost } = els();
      if (mapHost) {
        mapHost.innerHTML = '';
        delete mapHost._leaflet_id;
      }
      container.innerHTML = '';
      container.classList.remove('tst-root');
      instances.delete(container);
    }

    const api = {
      mount,
      update,
      resize,
      destroy,
      getState: () => ({ ...state, map: Boolean(state.map) }),
    };
    instances.set(container, api);
    return api;
  }

  function mount(container, options) {
    const host = typeof container === 'string' ? document.querySelector(container) : container;
    if (!host) throw new Error('TST: conteneur introuvable');
    const existing = instances.get(host);
    if (existing) existing.destroy();
    const controller = createController(host, options || {});
    return controller.mount();
  }

  global.TerritorialSummary = {
    version: '1.1.0',
    mount,
    getInstance(container) {
      const host = typeof container === 'string' ? document.querySelector(container) : container;
      return host ? instances.get(host) : null;
    },
  };
})(typeof window !== 'undefined' ? window : globalThis);
