/**
 * SigCartographyExperience — Phase 1 Decision Experience Premium
 * UX cartographique uniquement (aucun moteur métier).
 */
(function initSigCartographyExperience(global) {
  const state = {
    demoActive: false,
    demoMode: 'free', // free | guided
    tourIndex: 0,
    tourPaused: false,
    tourTimer: null,
    measureActive: false,
    measurePoints: [],
    measureLayer: null,
    measureMarkers: [],
    legendOpacity: {},
  };

  const TOUR_STEPS = [
    {
      id: 'rdc',
      title: 'Vue nationale — RDC',
      narrative: 'Maîtrise territoriale à l’échelle du pays.',
      run(ctx) {
        ctx.zoomNational();
      },
    },
    {
      id: 'zone',
      title: 'Zones FDSU',
      narrative: 'Découpage stratégique national du programme.',
      run(ctx) {
        ctx.enableLayer('zones');
        ctx.zoomNational();
      },
    },
    {
      id: 'province',
      title: 'Provinces',
      narrative: 'Niveau administratif provincial.',
      run(ctx) {
        ctx.enableLayer('provinces');
      },
    },
    {
      id: 'territoire',
      title: 'Territoires',
      narrative: 'Maillage territorial opérationnel.',
      run(ctx) {
        ctx.enableLayer('territoires');
      },
    },
    {
      id: 'collectivite',
      title: 'Collectivités',
      narrative: 'Collectivités locales et chefferies.',
      run(ctx) {
        ctx.enableLayer('collectivites');
      },
    },
    {
      id: 'groupement',
      title: 'Groupements',
      narrative: 'Groupements et entités de proximité.',
      run(ctx) {
        ctx.enableLayer('groupements');
      },
    },
    {
      id: 'localite',
      title: 'Localités',
      narrative: 'Localités et population desservie.',
      run(ctx) {
        ctx.enableLayer('villages');
      },
    },
    {
      id: 'site',
      title: 'Sites FDSU',
      narrative: 'Sites du programme national de connectivité.',
      run(ctx) {
        ctx.enableLayer('sites_40');
      },
    },
    {
      id: 'relations',
      title: 'Relations spatiales',
      narrative: 'Liens actifs ↔ besoins et correspondances NSME.',
      run(ctx) {
        ctx.enableLayer('spatial_relations');
      },
    },
    {
      id: 'decision',
      title: 'Dossier de décision',
      narrative: 'Ouverture d’un dossier site pour recommandation.',
      run(ctx) {
        const siteId = ctx.pickSampleSiteId();
        if (siteId) {
          global.location.hash = `decision-case/site/${encodeURIComponent(siteId)}?program_code=sites_40`;
        }
      },
    },
    {
      id: 'recommendation',
      title: 'Recommandation',
      narrative: 'Synthèse exécutable pour pilotage institutionnel / bailleurs.',
      run(ctx) {
        ctx.showMessage('Parcours guidé : consultez le dossier de décision ouvert pour la recommandation.');
      },
    },
  ];

  function cs() {
    return global.cartographyState || null;
  }

  function map() {
    return cs()?.map || null;
  }

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function showMessage(text) {
    const el = document.querySelector('#zones-message');
    if (el) {
      el.textContent = text;
      el.hidden = !text;
    }
  }

  function getTourContext() {
    return {
      zoomNational() {
        document.querySelector('#zoom-auto')?.click();
      },
      enableLayer(key) {
        const checkbox = document.querySelector(`#layer-list input[data-layer="${key}"]`);
        if (checkbox && !checkbox.checked) {
          checkbox.checked = true;
          checkbox.dispatchEvent(new Event('change', { bubbles: true }));
        }
      },
      pickSampleSiteId() {
        const features = cs()?.features?.sites_40 || cs()?.data?.sites_40 || [];
        const first = Array.isArray(features) ? features[0] : null;
        const props = first?.properties || first || {};
        return props.site_id || props.id || props.code || '29';
      },
      showMessage,
    };
  }

  function updateDemoBar() {
    const bar = document.querySelector('#cartography-demo-bar');
    const title = document.querySelector('#carto-demo-step-title');
    const narrative = document.querySelector('#carto-demo-step-narrative');
    const progress = document.querySelector('#carto-demo-progress');
    if (!bar) return;

    if (!state.demoActive) {
      bar.hidden = true;
      bar.setAttribute('hidden', '');
      return;
    }

    bar.hidden = false;
    bar.removeAttribute('hidden');

    if (state.demoMode === 'guided') {
      const step = TOUR_STEPS[state.tourIndex];
      if (title) title.textContent = step?.title || 'Parcours guidé';
      if (narrative) narrative.textContent = step?.narrative || '';
      if (progress) progress.textContent = `${state.tourIndex + 1} / ${TOUR_STEPS.length}`;
    } else {
      if (title) title.textContent = 'Mode Démonstration — navigation libre';
      if (narrative) narrative.textContent = 'Interface épurée pour réunion institutionnelle, ministère ou bailleurs.';
      if (progress) progress.textContent = 'Libre';
    }
  }

  function runTourStep(index) {
    const step = TOUR_STEPS[index];
    if (!step) return;
    state.tourIndex = index;
    try {
      step.run(getTourContext());
    } catch (err) {
      console.warn('SigCartographyExperience tour step', step.id, err);
    }
    updateDemoBar();
    showMessage(`Démonstration : ${step.title}`);
  }

  function scheduleAutoAdvance() {
    if (state.tourTimer) global.clearTimeout(state.tourTimer);
    if (!state.demoActive || state.demoMode !== 'guided' || state.tourPaused) return;
    state.tourTimer = global.setTimeout(() => {
      if (state.tourIndex < TOUR_STEPS.length - 1) {
        runTourStep(state.tourIndex + 1);
        scheduleAutoAdvance();
      }
    }, 12000);
  }

  function enterDemoMode(mode = 'free') {
    if (state.demoActive) return;
    state.demoActive = true;
    state.demoMode = mode === 'guided' ? 'guided' : 'free';
    state.tourIndex = 0;
    state.tourPaused = false;

    document.body.classList.add('cartography-demo-mode');
    if (typeof global.setCartographyFocusMode === 'function') {
      global.setCartographyFocusMode(true);
    } else {
      document.body.classList.add('cartography-focus-mode');
    }

    document.querySelector('#cartography-explorer-drawer')?.classList.add('hidden');
    updateDemoBar();

    if (state.demoMode === 'guided') {
      runTourStep(0);
      scheduleAutoAdvance();
    } else {
      getTourContext().zoomNational();
      showMessage('Mode Démonstration — navigation libre.');
    }

    map()?.invalidateSize({ animate: false });
  }

  function exitDemoMode() {
    if (!state.demoActive) return;
    state.demoActive = false;
    state.tourPaused = false;
    if (state.tourTimer) global.clearTimeout(state.tourTimer);
    state.tourTimer = null;
    stopMeasure();

    document.body.classList.remove('cartography-demo-mode');
    if (typeof global.setCartographyFocusMode === 'function') {
      global.setCartographyFocusMode(false);
    } else {
      document.body.classList.remove('cartography-focus-mode');
    }

    updateDemoBar();
    showMessage('');
    map()?.invalidateSize({ animate: false });
  }

  function tourNext() {
    if (state.tourIndex < TOUR_STEPS.length - 1) {
      runTourStep(state.tourIndex + 1);
      scheduleAutoAdvance();
    }
  }

  function tourPrev() {
    if (state.tourIndex > 0) {
      runTourStep(state.tourIndex - 1);
      scheduleAutoAdvance();
    }
  }

  function tourTogglePause() {
    state.tourPaused = !state.tourPaused;
    const btn = document.querySelector('#carto-demo-pause');
    if (btn) {
      btn.textContent = state.tourPaused ? 'Reprendre' : 'Pause';
      btn.setAttribute('aria-pressed', String(state.tourPaused));
    }
    if (state.tourPaused && state.tourTimer) {
      global.clearTimeout(state.tourTimer);
      state.tourTimer = null;
    } else {
      scheduleAutoAdvance();
    }
  }

  function haversineM(a, b) {
    const R = 6371000;
    const toRad = (d) => (d * Math.PI) / 180;
    const dLat = toRad(b.lat - a.lat);
    const dLng = toRad(b.lng - a.lng);
    const lat1 = toRad(a.lat);
    const lat2 = toRad(b.lat);
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  }

  function formatDistance(m) {
    if (m >= 1000) return `${(m / 1000).toFixed(2).replace(/\.?0+$/, '')} km`;
    return `${Math.round(m)} m`;
  }

  function stopMeasure() {
    state.measureActive = false;
    state.measurePoints = [];
    const m = map();
    if (m && state.measureLayer) {
      m.removeLayer(state.measureLayer);
    }
    state.measureLayer = null;
    state.measureMarkers.forEach((mk) => m?.removeLayer(mk));
    state.measureMarkers = [];
    document.querySelector('#carto-measure-btn')?.classList.remove('is-active');
    document.querySelector('#carto-measure-btn')?.setAttribute('aria-pressed', 'false');
    showMessage('');
  }

  function toggleMeasure() {
    const m = map();
    if (!m || typeof global.L === 'undefined') return;

    if (state.measureActive) {
      stopMeasure();
      return;
    }

    stopMeasure();
    state.measureActive = true;
    state.measureLayer = global.L.layerGroup().addTo(m);
    document.querySelector('#carto-measure-btn')?.classList.add('is-active');
    document.querySelector('#carto-measure-btn')?.setAttribute('aria-pressed', 'true');
    showMessage('Mesure : cliquez deux points sur la carte. Échap pour annuler.');

    const onClick = (event) => {
      if (!state.measureActive) {
        m.off('click', onClick);
        return;
      }
      state.measurePoints.push(event.latlng);
      const marker = global.L.circleMarker(event.latlng, {
        radius: 5,
        color: '#38bdf8',
        fillColor: '#7dd3fc',
        fillOpacity: 0.9,
        weight: 2,
      }).addTo(state.measureLayer);
      state.measureMarkers.push(marker);

      if (state.measurePoints.length >= 2) {
        const [a, b] = state.measurePoints.slice(-2);
        global.L.polyline([a, b], { color: '#38bdf8', weight: 3, dashArray: '6 4' }).addTo(state.measureLayer);
        const dist = haversineM(a, b);
        showMessage(`Distance mesurée : ${formatDistance(dist)}`);
        state.measureActive = false;
        m.off('click', onClick);
        document.querySelector('#carto-measure-btn')?.classList.remove('is-active');
        document.querySelector('#carto-measure-btn')?.setAttribute('aria-pressed', 'false');
      }
    };

    m.on('click', onClick);
  }

  function applyLegendOpacity(layerKey, value) {
    const opacity = Math.max(0.05, Math.min(1, Number(value)));
    state.legendOpacity[layerKey] = opacity;
    const layerGroup = cs()?.layers?.[layerKey];
    if (!layerGroup) return;

    if (typeof layerGroup.setOpacity === 'function') {
      layerGroup.setOpacity(opacity);
    }
    if (typeof layerGroup.eachLayer === 'function') {
      layerGroup.eachLayer((layer) => {
        if (typeof layer.setStyle === 'function') {
          layer.setStyle({ fillOpacity: opacity * 0.45, opacity: Math.min(1, opacity + 0.2) });
        }
        if (typeof layer.setOpacity === 'function') layer.setOpacity(opacity);
      });
    }
  }

  function setupLegendControls() {
    document.querySelectorAll('[data-legend-opacity]').forEach((input) => {
      if (input.dataset.bound === 'true') return;
      input.dataset.bound = 'true';
      const layerKey = input.dataset.legendOpacity;
      input.addEventListener('input', () => applyLegendOpacity(layerKey, input.value));
    });

    document.querySelectorAll('[data-legend-toggle]').forEach((btn) => {
      if (btn.dataset.bound === 'true') return;
      btn.dataset.bound = 'true';
      btn.addEventListener('click', () => {
        const layerKey = btn.dataset.legendToggle;
        const checkbox = document.querySelector(`#layer-list input[data-layer="${layerKey}"]`);
        if (!checkbox) return;
        checkbox.checked = !checkbox.checked;
        checkbox.dispatchEvent(new Event('change', { bubbles: true }));
        btn.classList.toggle('is-off', !checkbox.checked);
        btn.setAttribute('aria-pressed', String(checkbox.checked));
      });
    });
  }

  function enhanceToolbarAccessibility() {
    document.querySelectorAll('.cartography-premium-btn').forEach((btn, index) => {
      if (!btn.id) btn.id = `carto-premium-btn-${index}`;
      if (!btn.getAttribute('tabindex')) btn.setAttribute('tabindex', '0');
    });
  }

  function setupPopupAutoPan() {
    const m = map();
    if (!m || m.__sigPopupAutoPan) return;
    m.__sigPopupAutoPan = true;
    m.on('popupopen', (event) => {
      const popup = event?.popup;
      const el = popup?.getElement?.();
      if (!el) return;
      el.classList.add('sig-map-popup-visible');
      const mapSize = m.getSize();
      const pad = 72;
      const rect = el.getBoundingClientRect();
      const container = m.getContainer().getBoundingClientRect();
      let dx = 0;
      let dy = 0;
      if (rect.right > container.right - pad) dx = container.right - pad - rect.right;
      if (rect.left < container.left + pad) dx = container.left + pad - rect.left;
      if (rect.bottom > container.bottom - pad) dy = container.bottom - pad - rect.bottom;
      if (rect.top < container.top + pad) dy = container.top + pad - rect.top;
      if (dx || dy) {
        m.panBy([dx, dy], { animate: true, duration: 0.25 });
      }
    });
  }

  function bindEvents() {
    if (document.body.dataset.sigCartographyExperienceBound === 'true') return;
    document.body.dataset.sigCartographyExperienceBound = 'true';

    document.querySelector('#carto-demo-btn')?.addEventListener('click', () => {
      if (state.demoActive) exitDemoMode();
      else enterDemoMode('free');
    });

    document.querySelector('#carto-demo-guided-btn')?.addEventListener('click', () => {
      exitDemoMode();
      enterDemoMode('guided');
    });

    document.querySelector('#carto-demo-exit')?.addEventListener('click', exitDemoMode);
    document.querySelector('#carto-demo-next')?.addEventListener('click', tourNext);
    document.querySelector('#carto-demo-prev')?.addEventListener('click', tourPrev);
    document.querySelector('#carto-demo-pause')?.addEventListener('click', tourTogglePause);

    document.querySelector('#carto-measure-btn')?.addEventListener('click', toggleMeasure);

    document.querySelector('#carto-analysis-btn')?.addEventListener('click', () => {
      if (typeof global.openCartographyDrawerPanel === 'function') {
        global.openCartographyDrawerPanel('classification');
      } else {
        document.querySelector('[data-carto-drawer="classification"]')?.click();
      }
    });

    document.querySelector('#carto-basemap-btn')?.addEventListener('click', () => {
      if (typeof global.openCartographyDrawerPanel === 'function') {
        global.openCartographyDrawerPanel('settings');
      } else {
        document.querySelector('[data-carto-drawer="settings"]')?.click();
      }
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        if (state.measureActive) {
          event.preventDefault();
          stopMeasure();
          return;
        }
        if (state.demoActive) {
          event.preventDefault();
          exitDemoMode();
        }
      }
    });

    enhanceToolbarAccessibility();
    setupLegendControls();
  }

  function setup() {
    bindEvents();
    const tryPopup = () => {
      if (map()) setupPopupAutoPan();
    };
    tryPopup();
    global.setInterval(tryPopup, 2000);
  }

  global.SigCartographyExperience = {
    setup,
    enterDemoMode,
    exitDemoMode,
    isDemoActive: () => state.demoActive,
    stopMeasure,
    applyLegendOpacity,
    TOUR_STEPS,
  };
})(typeof window !== 'undefined' ? window : globalThis);
