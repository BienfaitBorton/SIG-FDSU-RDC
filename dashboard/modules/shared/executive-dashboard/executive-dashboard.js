(function initExecutiveCockpit(global) {
  const state = { initialized: false, map: null, payload: null, tstInstance: null };

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

  /** @deprecated EDVS cockpit classique — remplacé par Executive Situation Room v1 */
  function renderCockpit(payload) {
    if (global.ExecutiveSituationRoom?.mount) {
      const root = document.querySelector('#edvs-cockpit-root');
      return global.ExecutiveSituationRoom.mount(root).then((esrPayload) => {
        state.payload = esrPayload;
      });
    }
    // Repli minimal si module ESR absent
    const root = document.querySelector('#edvs-cockpit-root');
    if (!root || !global.EdvsLayout) return;
    state.payload = payload;
    root.innerHTML = global.EdvsLayout.shell({
      eyebrow: 'Salle de Pilotage DG',
      title: 'Salle de Pilotage DG',
      subtitle: 'Executive Situation Room indisponible — mode cockpit réduit',
      actionsHtml: '<button type="button" class="secondary-button" data-route-jump="decision-view">Centre de Décision</button>',
      mapHtml: `<section class="edvs-card"><div id="edvs-tst-host" class="edvs-tst-host"></div></section>`,
      chartsHtml: '',
      kpiHtml: global.EdvsKpi?.renderKpiGrid?.(payload.kpis || []) || '',
      textHtml: global.EdvsCards?.renderAlertList?.({ title: 'Alertes', items: payload.alerts || [] }) || '',
    });
    root.querySelectorAll('[data-route-jump]').forEach((btn) => {
      btn.addEventListener('click', () => { global.location.hash = btn.getAttribute('data-route-jump'); });
    });
  }

  function initializeExecutiveCockpitModule() {
    const banner = document.querySelector('#edvs-cockpit-banner');
    if (banner) banner.textContent = 'Chargement de la Situation Room…';
    const root = document.querySelector('#edvs-cockpit-root');
    if (!root) return Promise.resolve();

    // Détruire l’ancienne carte Leaflet legacy si présente (éviter double instance)
    if (state.map) {
      try { state.map.remove(); } catch (_e) { /* */ }
      state.map = null;
    }

    if (global.ExecutiveSituationRoom?.mount) {
      return global.ExecutiveSituationRoom.mount(root)
        .then((payload) => {
          state.payload = payload;
          state.initialized = true;
          if (banner) {
            const ver = payload?._meta?.version || 'esr-1.0.0';
            banner.textContent = `Executive Situation Room · ${ver} · parcours Situation → Décision`;
          }
          global.EdvsLayout?.bindPresentationControls?.(document);
        })
        .catch(() => {
          if (banner) banner.textContent = 'Situation Room indisponible — vérifier /api/executive/situation-room';
        });
    }

    // Repli : ancien cockpit
    const API_BASE = `${global.location.protocol}//${global.location.hostname}:8001`;
    return fetch(`${API_BASE}/api/executive/cockpit`, { headers: { Accept: 'application/json' }, cache: 'no-store' })
      .then((r) => {
        if (!r.ok) throw new Error('cockpit');
        return r.json();
      })
      .then((payload) => {
        renderCockpit(payload);
        if (banner) banner.textContent = 'Salle de Pilotage DG (cockpit)';
        state.initialized = true;
      })
      .catch(() => {
        if (banner) banner.textContent = 'Salle de pilotage indisponible.';
      });
  }

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
    renderCockpit,
    ensureMap,
    state,
  };
  global.initializeExecutiveCockpitModule = initializeExecutiveCockpitModule;
})(window);
