/**
 * Tableau de Synthèse Territoriale (TST) v1.0
 * TerritorialSummary.mount / update / resize / destroy
 * Une seule instance Leaflet par conteneur — données réelles uniquement.
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
    return String(value || '').trim().toLowerCase().replace(/\s+/g, ' ');
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
      abort: null,
      geometryCache: null,
      layerPayload: null,
      metrics: [],
      trail: [{ level: 'rdc', id: 'rdc', label: 'RDC' }],
      selection: null,
      destroyed: false,
      unsubContext: null,
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
      };
    }

    function setStatus(text, kind) {
      const { status } = els();
      if (!status) return;
      status.textContent = text;
      status.className = `tst-status${kind ? ` is-${kind}` : ''}`;
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

    function renderKpis(features) {
      const { kpis } = els();
      if (!kpis || !state.opts.showKpis) return;
      const ok = (features || []).filter((f) => f.properties?.status === 'ok' || f.properties?.status === 'partial');
      const insufficient = (features || []).length - ok.length;
      const values = ok.map((f) => Number(f.properties.value)).filter((n) => Number.isFinite(n));
      const max = values.length ? Math.max(...values) : null;
      const items = [
        { label: 'Entités', value: (features || []).length },
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
        // Conteneur déjà initialisé ailleurs — refuse la double instance
        setStatus('Conteneur carte déjà initialisé — destroy() requis', 'error');
        return null;
      }
      state.map = global.L.map(mapHost, { zoomControl: true, attributionControl: true })
        .setView([-2.8, 23.5], 5);
      global.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap',
        maxZoom: 18,
      }).addTo(state.map);
      state.layer = global.L.geoJSON(null, {
        style: (feature) => styleFeature(feature),
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
        fillOpacity: feature?.properties?.status === 'insufficient' ? 0.25 : 0.65,
      };
    }

    function onEachFeature(feature, layer) {
      const p = feature.properties || {};
      const html = `
        <strong>${escapeHtml(p.name || '—')}</strong><br>
        ${escapeHtml(p.administrative_level || '')}<br>
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
        }, 'province', {
          interactive: true,
          direction: 'auto',
          onClick: () => handleSelect(p),
        });
      } else if (layer.bindTooltip) {
        layer.bindTooltip(html, { sticky: true, direction: 'auto', className: 'sig-map-tooltip' });
      }
      layer.on('click', () => handleSelect(p));
    }

    function handleSelect(props) {
      if (!props || !state.opts.allowDrilldown) return;
      const entity = {
        level: props.level || 'province',
        id: props.id,
        name: props.name,
        province: props.province || (props.level === 'province' ? props.name : undefined),
      };
      state.selection = entity;
      if (entity.level === 'province') {
        state.trail = [
          { level: 'rdc', id: 'rdc', label: 'RDC' },
          { level: 'province', id: String(entity.id), label: entity.name },
        ];
        state.opts.level = 'territoire';
        state.opts.parentId = entity.name;
      } else if (entity.level === 'territoire') {
        state.trail = [
          { level: 'rdc', id: 'rdc', label: 'RDC' },
          { level: 'province', id: String(props.province || state.opts.parentId), label: String(props.province || state.opts.parentId) },
          { level: 'territoire', id: String(entity.id), label: entity.name },
        ];
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
      if (entity.level === 'province') {
        loadLayer();
      } else {
        refreshLayerStyles();
      }
    }

    function refreshLayerStyles() {
      if (!state.layer) return;
      state.layer.eachLayer((layer) => {
        if (layer.feature) layer.setStyle(styleFeature(layer.feature));
      });
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

    function joinGeometry(layerPayload, geojson) {
      const byName = new Map();
      (layerPayload.features || []).forEach((f) => {
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
      });
      return { type: 'FeatureCollection', features };
    }

    function paint(geo) {
      ensureMap();
      if (!state.map || !state.layer) return;
      state.layer.clearLayers();
      if (geo?.features?.length) {
        state.layer.addData(geo);
        const bounds = state.layer.getBounds();
        if (bounds.isValid()) state.map.fitBounds(bounds, { padding: [16, 16] });
      }
      if (global.UxPremium?.mountMapLegend) {
        global.UxPremium.mountMapLegend(`#${id}`, {
          id: `ux-legend-${id}`,
          title: 'Légende TST',
          items: (state.layerPayload?.legend || []).map((item) => ({
            className: `is-${item.class_id}`,
            label: item.label,
          })),
        });
      }
    }

    function loadLayer() {
      if (state.destroyed) return;
      if (state.abort) state.abort.abort();
      state.abort = new global.AbortController();
      setStatus('Chargement…', 'loading');
      const metric = state.opts.metric || 'priority';
      const level = state.opts.level || 'province';
      const params = new URLSearchParams({ level, metric });
      if (level === 'territoire' && state.opts.parentId) params.set('parent_id', state.opts.parentId);

      const layerPromise = fetchJson(`/api/territorial-summary/layer?${params}`, state.abort.signal);
      const geoPromise = level === 'province'
        ? (state.geometryCache
          ? Promise.resolve(state.geometryCache)
          : fetchJson('/map/layers/provinces?limit=5000', state.abort.signal).then((g) => {
            state.geometryCache = g;
            return g;
          }))
        : Promise.resolve({ type: 'FeatureCollection', features: [] });

      Promise.all([layerPromise, geoPromise])
        .then(([layerPayload, geo]) => {
          if (state.destroyed) return;
          state.layerPayload = layerPayload;
          renderLegend(layerPayload.legend);
          renderKpis(layerPayload.features);
          if (level === 'province') {
            paint(joinGeometry(layerPayload, geo));
            setStatus(`${layerPayload.features?.length || 0} provinces — données réelles`, 'ok');
          } else {
            // Territoires : liste synthèse sans polygones si géométrie absente
            ensureMap();
            if (state.layer) state.layer.clearLayers();
            const { summary } = els();
            const list = (layerPayload.features || []).map((f) => {
              const p = f.properties || {};
              return `<button type="button" class="tst-territory-item" data-tst-territory='${escapeHtml(JSON.stringify({
                level: 'territoire',
                id: p.id,
                name: p.name,
                province: p.province || state.opts.parentId,
              }))}'>
                <strong>${escapeHtml(p.name)}</strong>
                <span>${escapeHtml(p.display)}</span>
              </button>`;
            }).join('');
            if (summary) {
              summary.innerHTML = `
                <h3>Territoires — ${escapeHtml(state.opts.parentId || '')}</h3>
                <div class="tst-territory-list">${list || (global.UxPremium?.stateHtml
                  ? global.UxPremium.stateHtml('empty', 'Données insuffisantes', 'Aucun territoire pour cette province.')
                  : '<p>Données insuffisantes</p>')}</div>
              `;
            }
            setStatus(`${layerPayload.features?.length || 0} territoires`, 'ok');
            if (state.selection) loadSummary(state.selection);
          }
        })
        .catch((err) => {
          if (err.name === 'AbortError') return;
          setStatus(`Erreur : ${err.message}`, 'error');
          const { summary } = els();
          if (summary && global.UxPremium?.stateHtml) {
            summary.innerHTML = global.UxPremium.stateHtml('error', 'Chargement impossible', err.message);
          }
        });
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
        const crumb = target.closest('[data-tst-crumb]');
        if (crumb) {
          const idx = Number(crumb.getAttribute('data-tst-crumb'));
          const next = state.trail.slice(0, idx + 1);
          state.trail = next;
          const last = next[next.length - 1];
          if (last.level === 'rdc') {
            state.opts.level = 'province';
            state.opts.parentId = null;
            state.selection = null;
            renderSummary(null);
          } else if (last.level === 'province') {
            state.opts.level = 'territoire';
            state.opts.parentId = last.label;
            state.selection = { level: 'province', id: last.id, name: last.label };
            loadSummary(state.selection);
          }
          renderBreadcrumb();
          if (state.opts.preserveContext && global.TerritorialContext) {
            global.TerritorialContext.setTrail(state.trail);
          }
          loadLayer();
          return;
        }
        const hashBtn = target.closest('[data-tst-hash]');
        if (hashBtn) {
          const hash = hashBtn.getAttribute('data-tst-hash');
          if (hash) global.location.hash = hash.replace(/^#/, '');
          return;
        }
        const terr = target.closest('[data-tst-territory]');
        if (terr) {
          try {
            handleSelect(JSON.parse(terr.getAttribute('data-tst-territory')));
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
      if (state.layer) {
        try { state.layer.clearLayers(); } catch (_e) { /* */ }
        state.layer = null;
      }
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

    const api = { mount, update, resize, destroy, getState: () => ({ ...state, map: Boolean(state.map) }) };
    instances.set(container, api);
    return api;
  }

  function mount(container, options) {
    const host = typeof container === 'string' ? document.querySelector(container) : container;
    if (!host) throw new Error('TST: conteneur introuvable');
    const existing = instances.get(host);
    if (existing) {
      existing.destroy();
    }
    const controller = createController(host, options || {});
    return controller.mount();
  }

  global.TerritorialSummary = {
    version: '1.0.0',
    mount,
    getInstance(container) {
      const host = typeof container === 'string' ? document.querySelector(container) : container;
      return host ? instances.get(host) : null;
    },
  };
})(typeof window !== 'undefined' ? window : globalThis);
