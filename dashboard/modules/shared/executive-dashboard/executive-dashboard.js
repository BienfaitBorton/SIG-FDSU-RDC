(function initExecutiveCockpit(global) {
  const API_BASE = 'http://127.0.0.1:8001';
  const state = { initialized: false, map: null, payload: null };

  function fetchJson(path) {
    return fetch(`${API_BASE}${path}`, { headers: { Accept: 'application/json' }, cache: 'no-store' })
      .then((r) => {
        if (!r.ok) throw new Error(path);
        return r.json();
      });
  }

  function ensureMap(center, zoom) {
    if (typeof global.L === 'undefined') return;
    const el = document.querySelector('#edvs-cockpit-map');
    if (!el) return;
    if (!state.map) {
      state.map = global.L.map(el, { zoomControl: true }).setView(center || [-2.8, 23.5], zoom || 5);
      global.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap',
        maxZoom: 18,
      }).addTo(state.map);
    } else {
      state.map.setView(center || [-2.8, 23.5], zoom || state.map.getZoom(), { animate: false });
    }
    global.setTimeout(() => state.map.invalidateSize(), 80);
  }

  function renderCockpit(payload) {
    const root = document.querySelector('#edvs-cockpit-root');
    if (!root || !global.EdvsLayout) return;
    state.payload = payload;
    const kpiHtml = global.EdvsKpi.renderKpiGrid(payload.kpis || []);
    const chartsHtml = [
      global.EdvsCharts.stackedBar({ title: 'Programmes FDSU', ...(payload.stacked || {}) }),
      global.EdvsCharts.radar({ title: 'Portrait connaissance', ...(payload.radar || {}) }),
      global.EdvsCharts.gauge(payload.gauges?.[0] || { title: 'Maturité', value: 0 }),
      global.EdvsCharts.waterfall(payload.waterfall || { title: 'Doctrine', steps: [] }),
      global.EdvsCharts.treemap(payload.treemap || { title: 'Répartition', items: [] }),
      global.EdvsCharts.heatmap(payload.heatmap || { title: 'Heatmap', rows: [], cols: [], matrix: [] }),
    ].join('');
    const mapHtml = `
      <section class="edvs-card">
        <header class="edvs-card-header"><h3>Carte nationale</h3></header>
        <div id="edvs-cockpit-map" class="edvs-cockpit-map" aria-label="Carte nationale de pilotage"></div>
        <p class="edvs-muted">${global.EdvsUtils.escapeHtml(payload.map?.note || '')}</p>
      </section>
      ${global.EdvsCards.renderRanking({ title: 'Top priorités sites', items: payload.rankings?.sites_priority || [], color: 'orange' })}
    `;
    const textHtml = [
      global.EdvsCards.renderAlertList({ title: 'Alertes', items: payload.alerts || [] }),
      global.EdvsCards.renderRecommendationCards({ title: 'Recommandations explicables', items: payload.recommendations || [] }),
      global.EdvsCards.renderTimeline({ title: 'Historique décisions / jalons', items: payload.timeline || [] }),
      global.EdvsCards.renderRanking({ title: 'Top provinces CCN (DEMO)', items: payload.rankings?.provinces_ccn || [] }),
    ].join('');

    root.innerHTML = global.EdvsLayout.shell({
      eyebrow: 'Salle de Pilotage DG',
      title: 'Salle de Pilotage DG',
      subtitle: 'Histoire visuelle nationale — Base nationale de connaissances · Centre de Décision · Intelligence territoriale · CCN',
      actionsHtml: `
        <button type="button" class="secondary-button" data-route-jump="decision-view">Centre de Décision</button>
        <button type="button" class="secondary-button" data-route-jump="territorial-intelligence">Intelligence territoriale</button>
      `,
      mapHtml,
      chartsHtml,
      kpiHtml,
      textHtml,
    });

    global.EdvsLayout.bindPresentationControls(root);
    root.querySelectorAll('[data-route-jump]').forEach((btn) => {
      btn.addEventListener('click', () => {
        global.location.hash = btn.getAttribute('data-route-jump');
      });
    });
    ensureMap(payload.map?.center, payload.map?.zoom);
  }

  function initializeExecutiveCockpitModule() {
    const banner = document.querySelector('#edvs-cockpit-banner');
    if (banner) banner.textContent = 'Chargement de la salle de pilotage…';
    return fetchJson('/api/executive/cockpit')
      .then((payload) => {
        renderCockpit(payload);
        if (banner) {
          banner.textContent = `Sources consolidées · doctrine métier ${payload.doctrine?.id || '—'} v${payload.doctrine?.version || '—'}`;
        }
        state.initialized = true;
        global.EdvsLayout.bindPresentationControls(document);
      })
      .catch(() => {
        if (banner) banner.textContent = 'Salle de pilotage indisponible — vérifier le service de pilotage.';
      });
  }

  /** Helpers d’intégration pour les modules existants */
  function mountKpiStrip(selector, items) {
    const node = document.querySelector(selector);
    if (!node || !global.EdvsKpi) return;
    node.innerHTML = global.EdvsKpi.renderKpiGrid(items || []);
    if (global.UxPremium?.bindEdvsKpiClicks) {
      global.UxPremium.bindEdvsKpiClicks(node);
    }
  }

  function mountPresentationButton(selector) {
    const node = document.querySelector(selector);
    if (!node || node.dataset.edvsPresentationMounted === 'true') return;
    node.dataset.edvsPresentationMounted = 'true';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'edvs-presentation-btn';
    btn.setAttribute('data-edvs-presentation-toggle', '');
    btn.textContent = 'Mode Présentation';
    node.appendChild(btn);
    global.EdvsLayout.bindPresentationControls(node);
  }

  global.Edvs = {
    initializeExecutiveCockpitModule,
    mountKpiStrip,
    mountPresentationButton,
    state,
  };
  global.initializeExecutiveCockpitModule = initializeExecutiveCockpitModule;
})(window);
