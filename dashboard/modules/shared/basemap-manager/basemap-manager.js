/**
 * SigBasemapManager — fond de carte résilient (multi-fournisseurs)
 * Ordre auto : OSM → CARTO Voyager → Esri Street → Esri Imagery
 */
(function initSigBasemapManager(global) {
  const STORAGE_KEY = 'sig.cartography.basemapPreference';
  const DEFAULT_TIMEOUT_MS = 3000;
  const DEFAULT_RETRIES = 1;
  const PROBE_Z = 5;
  const PROBE_X = 17;
  const PROBE_Y = 15;

  const PROVIDERS = {
    osm: {
      id: 'osm',
      label: 'OpenStreetMap',
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      options: {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
        subdomains: 'abc',
      },
      probeUrl: `https://a.tile.openstreetmap.org/${PROBE_Z}/${PROBE_X}/${PROBE_Y}.png`,
    },
    carto: {
      id: 'carto',
      label: 'CARTO Voyager',
      url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
      options: {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        maxZoom: 20,
        subdomains: 'abcd',
      },
      probeUrl: `https://a.basemaps.cartocdn.com/rastertiles/voyager/${PROBE_Z}/${PROBE_X}/${PROBE_Y}.png`,
    },
    esri_street: {
      id: 'esri_street',
      label: 'Esri Street',
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
      options: {
        attribution: 'Tiles &copy; Esri',
        maxZoom: 19,
      },
      probeUrl: `https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/${PROBE_Z}/${PROBE_Y}/${PROBE_X}`,
    },
    esri_imagery: {
      id: 'esri_imagery',
      label: 'Esri Satellite',
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      options: {
        attribution: 'Tiles &copy; Esri',
        maxZoom: 19,
      },
      probeUrl: `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${PROBE_Z}/${PROBE_Y}/${PROBE_X}`,
    },
  };

  const AUTO_ORDER = ['osm', 'carto', 'esri_street', 'esri_imagery'];
  const PREFERENCE_OPTIONS = [
    { id: 'auto', label: 'Automatique (défaut)' },
    { id: 'osm', label: 'OpenStreetMap' },
    { id: 'carto', label: 'CARTO Voyager' },
    { id: 'esri_street', label: 'Esri Street' },
    { id: 'esri_imagery', label: 'Esri Satellite' },
  ];

  function logBasemap(...parts) {
    console.info(['Basemap :', ...parts].join(' '));
  }

  function readPreference() {
    try {
      const raw = global.localStorage?.getItem(STORAGE_KEY);
      if (!raw) return 'auto';
      if (raw === 'auto' || PROVIDERS[raw]) return raw;
    } catch (_error) {
      /* ignore */
    }
    return 'auto';
  }

  function writePreference(value) {
    try {
      global.localStorage?.setItem(STORAGE_KEY, value);
    } catch (_error) {
      /* ignore */
    }
  }

  function probeImage(url, timeoutMs) {
    return new Promise((resolve) => {
      if (!url) {
        resolve(false);
        return;
      }
      const img = new Image();
      let settled = false;
      const finish = (ok) => {
        if (settled) return;
        settled = true;
        global.clearTimeout(timer);
        img.onload = null;
        img.onerror = null;
        resolve(ok);
      };
      const timer = global.setTimeout(() => finish(false), timeoutMs);
      img.onload = () => finish(true);
      img.onerror = () => finish(false);
      img.referrerPolicy = 'no-referrer';
      img.src = `${url}${url.includes('?') ? '&' : '?'}_bm=${Date.now()}`;
    });
  }

  class SigBasemapManager {
    constructor(options = {}) {
      this.timeoutMs = Number(options.timeoutMs) > 0 ? Number(options.timeoutMs) : DEFAULT_TIMEOUT_MS;
      this.retries = Number.isFinite(Number(options.retries))
        ? Math.max(0, Number(options.retries))
        : DEFAULT_RETRIES;
      this.preference = readPreference();
      this.map = null;
      this.activeLayer = null;
      this.activeProviderId = null;
      this.attaching = null;
      this.onChange = typeof options.onChange === 'function' ? options.onChange : null;
    }

    static getProviders() {
      return { ...PROVIDERS };
    }

    static getPreferenceOptions() {
      return PREFERENCE_OPTIONS.slice();
    }

    static getAutoOrder() {
      return AUTO_ORDER.slice();
    }

    getPreference() {
      return this.preference;
    }

    setPreference(preference) {
      const next = preference === 'auto' || PROVIDERS[preference] ? preference : 'auto';
      this.preference = next;
      writePreference(next);
      return next;
    }

    getActiveProviderId() {
      return this.activeProviderId;
    }

    getActiveProviderLabel() {
      return PROVIDERS[this.activeProviderId]?.label || null;
    }

    resolveOrder(preference = this.preference) {
      if (preference && preference !== 'auto' && PROVIDERS[preference]) {
        const rest = AUTO_ORDER.filter((id) => id !== preference);
        return [preference, ...rest];
      }
      return AUTO_ORDER.slice();
    }

    async probeProvider(providerId) {
      const provider = PROVIDERS[providerId];
      if (!provider) return false;
      const attempts = this.retries + 1;
      for (let attempt = 1; attempt <= attempts; attempt += 1) {
        const ok = await probeImage(provider.probeUrl, this.timeoutMs);
        if (ok) return true;
        if (attempt < attempts) {
          logBasemap(`${provider.label} — tentative ${attempt}/${attempts} échouée, nouvel essai…`);
        }
      }
      return false;
    }

    createTileLayer(providerId) {
      const provider = PROVIDERS[providerId];
      if (!provider || typeof global.L === 'undefined') return null;
      return global.L.tileLayer(provider.url, {
        ...provider.options,
        className: 'cartography-basemap-tiles',
        opacity: 1,
      });
    }

    clearActiveLayer() {
      if (this.activeLayer && this.map) {
        try {
          this.map.removeLayer(this.activeLayer);
        } catch (_error) {
          /* ignore */
        }
      }
      this.activeLayer = null;
      this.activeProviderId = null;
    }

    applyProvider(providerId) {
      if (!this.map || typeof global.L === 'undefined') return null;
      const layer = this.createTileLayer(providerId);
      if (!layer) return null;
      this.clearActiveLayer();
      layer.setZIndex(0);
      layer.addTo(this.map);
      // Remonter le basemap sous les overlays métier
      if (typeof layer.bringToBack === 'function') {
        layer.bringToBack();
      }
      this.activeLayer = layer;
      this.activeProviderId = providerId;
      if (typeof this.onChange === 'function') {
        this.onChange({
          preference: this.preference,
          providerId,
          label: PROVIDERS[providerId]?.label || providerId,
        });
      }
      return layer;
    }

    async attach(map, options = {}) {
      if (!map || typeof global.L === 'undefined') {
        return null;
      }
      this.map = map;
      if (options.preference) {
        this.setPreference(options.preference);
      }

      if (this.attaching) {
        await this.attaching;
      }

      this.attaching = this._attachInternal();
      try {
        return await this.attaching;
      } finally {
        this.attaching = null;
      }
    }

    async _attachInternal() {
      const order = this.resolveOrder();
      logBasemap(
        this.preference === 'auto'
          ? `mode Automatique — test dans l'ordre : ${order.map((id) => PROVIDERS[id].label).join(' → ')}`
          : `préférence ${PROVIDERS[this.preference]?.label || this.preference} (repli auto si indisponible)`,
      );

      for (let index = 0; index < order.length; index += 1) {
        const providerId = order[index];
        const provider = PROVIDERS[providerId];
        const available = await this.probeProvider(providerId);
        if (!available) {
          const next = order[index + 1];
          if (next) {
            logBasemap(`${provider.label} indisponible\n→ bascule ${PROVIDERS[next].label}`);
          } else {
            logBasemap(`${provider.label} indisponible — aucun fournisseur restant.`);
          }
          continue;
        }

        this.applyProvider(providerId);
        if (this.preference !== 'auto' && providerId !== this.preference) {
          logBasemap(
            `${PROVIDERS[this.preference]?.label || this.preference} indisponible\n→ bascule ${provider.label}`,
          );
        } else {
          logBasemap(`fournisseur actif : ${provider.label}`);
        }
        return providerId;
      }

      // Dernier recours : poser CARTO sans probe (Leaflet tentera quand même les tuiles)
      logBasemap('aucun probe réussi — application forcée de CARTO Voyager');
      this.applyProvider('carto');
      return 'carto';
    }

    async setPreferenceAndAttach(preference) {
      this.setPreference(preference);
      if (!this.map) return null;
      return this.attach(this.map);
    }
  }

  global.SigBasemapManager = SigBasemapManager;
  global.createBasemapManager = function createBasemapManager(options) {
    return new SigBasemapManager(options);
  };
})(typeof window !== 'undefined' ? window : globalThis);
