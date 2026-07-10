(function initGeocodingModule(global) {
  const API_BASE = 'http://127.0.0.1:8001';

  const geocodingState = {
    initialized: false,
    file: null,
    analyzeJob: null,
    geocodeJob: null,
    map: null,
    layer: null,
  };

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function setKpi(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value == null || value === '' ? '—' : String(value);
  }

  function renderAnomalies(anomalies) {
    const list = document.getElementById('geocoding-anomalies-list');
    if (!list) return;
    const entries = Object.entries(anomalies || {});
    if (!entries.length) {
      list.innerHTML = '<li>Aucune anomalie détectée.</li>';
      return;
    }
    const labels = {
      empty: 'Coordonnées vides',
      null_island: 'Coordonnées (0,0)',
      malformed: 'Format incorrect',
      out_of_rdc: 'Hors RDC',
      swapped: 'Lat/Lon inversées',
      repeated: 'Coordonnées répétées suspectes',
    };
    list.innerHTML = entries
      .map(([code, count]) => `<li><strong>${escapeHtml(labels[code] || code)}</strong> : ${escapeHtml(count)}</li>`)
      .join('');
  }

  function renderResults(rows) {
    const body = document.getElementById('geocoding-results-body');
    if (!body) return;
    const items = Array.isArray(rows) ? rows : [];
    if (!items.length) {
      body.innerHTML = '<tr><td colspan="7">Aucune ligne suspecte.</td></tr>';
      return;
    }
    body.innerHTML = items.slice(0, 200).map((row) => `
      <tr>
        <td>${escapeHtml(row.row_number)}</td>
        <td>${escapeHtml(row.site_label)}</td>
        <td>${escapeHtml(row.old_latitude)} / ${escapeHtml(row.old_longitude)}</td>
        <td>${escapeHtml(row.new_latitude)} / ${escapeHtml(row.new_longitude)}</td>
        <td>${escapeHtml(row.status)}</td>
        <td>${escapeHtml(row.source || '—')}</td>
        <td>${escapeHtml(row.comment || '')}</td>
      </tr>
    `).join('');
  }

  function applyJobSummary(job) {
    if (!job) return;
    setKpi('geocoding-kpi-analyzed', job.rows_analyzed);
    setKpi('geocoding-kpi-kept', job.valid_kept);
    setKpi('geocoding-kpi-corrected', job.corrected);
    setKpi('geocoding-kpi-approx', job.approximate);
    setKpi('geocoding-kpi-failed', job.failed);
    setKpi('geocoding-kpi-job', job.job_id);
    renderAnomalies(job.anomalies);
    renderResults(job.results_preview);
    const exportBtn = document.getElementById('geocoding-export-btn');
    if (exportBtn) exportBtn.disabled = !(job.export_path || job.export_filename);
    renderMap(job.geojson);
  }

  function ensureMap() {
    if (geocodingState.map || typeof global.L === 'undefined') return geocodingState.map;
    const container = document.getElementById('geocoding-map');
    if (!container) return null;
    geocodingState.map = global.L.map(container, { zoomControl: true }).setView([-2.5, 23.5], 5);
    global.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 18,
    }).addTo(geocodingState.map);
    return geocodingState.map;
  }

  function renderMap(geojson) {
    const map = ensureMap();
    const message = document.getElementById('geocoding-map-message');
    if (!map) return;
    if (geocodingState.layer) {
      map.removeLayer(geocodingState.layer);
      geocodingState.layer = null;
    }
    const features = geojson?.features || [];
    if (!features.length) {
      if (message) message.textContent = 'Aucun point cartographiable pour ce job.';
      return;
    }
    geocodingState.layer = global.L.geoJSON(geojson, {
      pointToLayer: (feature, latlng) => global.L.circleMarker(latlng, {
        radius: 4,
        color: feature.properties?.modified ? '#0ea5e9' : '#22c55e',
        weight: 1,
        fillOpacity: 0.8,
      }),
      onEachFeature: (feature, layer) => {
        const p = feature.properties || {};
        layer.bindPopup(`<strong>${escapeHtml(p.site || 'Site')}</strong><br>Statut : ${escapeHtml(p.status)}<br>Source : ${escapeHtml(p.source || '—')}`);
      },
    }).addTo(map);
    try {
      map.fitBounds(geocodingState.layer.getBounds(), { padding: [20, 20] });
    } catch (_err) {
      /* ignore empty bounds */
    }
    if (message) message.textContent = `${features.length} points affichés (vert = conservé, bleu = modifié).`;
    window.setTimeout(() => map.invalidateSize(), 50);
  }

  async function postExcel(endpoint, extraFields) {
    if (!geocodingState.file) throw new Error('Sélectionnez un fichier Excel.');
    const form = new FormData();
    form.append('file', geocodingState.file);
    Object.entries(extraFields || {}).forEach(([key, value]) => form.append(key, value));
    const response = await fetch(`${API_BASE}${endpoint}`, { method: 'POST', body: form });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Erreur API ${response.status}`);
    }
    return payload;
  }

  function bindEvents() {
    const root = document.getElementById('geocodage-panel');
    if (!root || root.dataset.bound === 'true') return;
    root.dataset.bound = 'true';

    document.getElementById('geocoding-file-input')?.addEventListener('change', (event) => {
      const input = event.target;
      geocodingState.file = input.files?.[0] || null;
      const runBtn = document.getElementById('geocoding-run-btn');
      if (runBtn) runBtn.disabled = !geocodingState.file;
      document.getElementById('geocoding-export-btn').disabled = true;
    });

    document.getElementById('geocoding-analyze-btn')?.addEventListener('click', async () => {
      try {
        setKpi('geocoding-kpi-job', '…');
        const job = await postExcel('/api/geocoding/analyze-excel');
        geocodingState.analyzeJob = job;
        applyJobSummary(job);
        document.getElementById('geocoding-run-btn').disabled = false;
      } catch (error) {
        setKpi('geocoding-kpi-job', 'Erreur');
        document.getElementById('geocoding-results-body').innerHTML =
          `<tr><td colspan="7">${escapeHtml(error.message)}</td></tr>`;
      }
    });

    document.getElementById('geocoding-run-btn')?.addEventListener('click', async () => {
      try {
        setKpi('geocoding-kpi-job', '…');
        const offline = document.getElementById('geocoding-offline')?.checked !== false;
        const nominatim = Boolean(document.getElementById('geocoding-nominatim')?.checked);
        const job = await postExcel('/api/geocoding/geocode-excel', {
          enable_offline: offline ? 'true' : 'false',
          enable_nominatim: nominatim ? 'true' : 'false',
          max_external_calls: '30',
        });
        geocodingState.geocodeJob = job;
        applyJobSummary(job);
      } catch (error) {
        setKpi('geocoding-kpi-job', 'Erreur');
        document.getElementById('geocoding-results-body').innerHTML =
          `<tr><td colspan="7">${escapeHtml(error.message)}</td></tr>`;
      }
    });

    document.getElementById('geocoding-export-btn')?.addEventListener('click', () => {
      const job = geocodingState.geocodeJob || geocodingState.analyzeJob;
      if (!job?.job_id || !job.export_path && !job.export_filename) return;
      global.open(`${API_BASE}/api/geocoding/export/${job.job_id}`, '_blank');
    });
  }

  function initializeGeocodingModule() {
    const panel = document.getElementById('geocodage-panel');
    if (!panel) return;
    bindEvents();
    ensureMap();
    geocodingState.initialized = true;
    window.setTimeout(() => geocodingState.map?.invalidateSize(), 80);
  }

  global.initializeGeocodingModule = initializeGeocodingModule;
  global.geocodingState = geocodingState;
})(window);
