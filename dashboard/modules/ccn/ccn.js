(function initCcnModule(global) {
  const API_BASE = 'http://127.0.0.1:8001';

  const ccnState = {
    initialized: false,
    loading: false,
    items: [],
    allItems: [],
    map: null,
    layer: null,
    selectedId: null,
  };

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

  function currentFilters() {
    const params = new URLSearchParams();
    const mapping = [
      ['province', '#ccn-filter-province'],
      ['territoire', '#ccn-filter-territoire'],
      ['zone', '#ccn-filter-zone'],
      ['program_code', '#ccn-filter-program'],
      ['status', '#ccn-filter-status'],
      ['ccn_type', '#ccn-filter-type'],
    ];
    mapping.forEach(([key, selector]) => {
      const value = document.querySelector(selector)?.value;
      if (value) params.set(key, value);
    });
    return params;
  }

  function setKpi(id, value) {
    const node = document.querySelector(id);
    if (node) node.textContent = value == null ? '—' : Number(value).toLocaleString('fr-FR');
  }

  function renderKpis(stats) {
    const kpis = stats?.kpis || {};
    setKpi('#ccn-kpi-total', kpis.total);
    setKpi('#ccn-kpi-planned', kpis.planifies);
    setKpi('#ccn-kpi-prep', kpis.preparation);
    setKpi('#ccn-kpi-deploy', kpis.deploiement);
    setKpi('#ccn-kpi-ops', kpis.operationnels);
    setKpi('#ccn-kpi-pop', kpis.population_desservie);
    setKpi('#ccn-kpi-sites', kpis.sites_fdsu_associes);
    setKpi('#ccn-kpi-provinces', Object.keys(stats?.by_province || {}).length);

    if (global.Edvs?.mountKpiStrip) {
      const host = document.querySelector('#ccn-edvs-kpi-host');
      const legacy = document.querySelector('#ccn-kpi-grid');
      if (host) {
        host.hidden = false;
        if (legacy) legacy.hidden = true;
        global.Edvs.mountKpiStrip('#ccn-edvs-kpi-host', [
          { id: 'ccn-total', label: 'Total CCN', value: kpis.total, icon: 'ccn', color: 'blue', confidence: 'medium', note: 'DEMO' },
          { id: 'ccn-ops', label: 'Opérationnels', value: kpis.operationnels, icon: 'gauge', color: 'green', confidence: 'medium' },
          { id: 'ccn-deploy', label: 'Déploiement', value: kpis.deploiement, icon: 'program', color: 'orange', confidence: 'medium' },
          { id: 'ccn-pop', label: 'Population', value: kpis.population_desservie, icon: 'people', color: 'yellow', confidence: 'low', note: 'DEMO' },
          { id: 'ccn-sites', label: 'Sites associés', value: kpis.sites_fdsu_associes, icon: 'sites', color: 'blue', confidence: 'medium' },
          { id: 'ccn-prov', label: 'Provinces', value: Object.keys(stats?.by_province || {}).length, icon: 'map', color: 'blue', confidence: 'high' },
        ]);
      }
    }
  }

  function fillFilterOptions(items) {
    const provinceSelect = document.querySelector('#ccn-filter-province');
    const territoireSelect = document.querySelector('#ccn-filter-territoire');
    if (!provinceSelect || !territoireSelect) return;
    const provinces = [...new Set(items.map((item) => item.province).filter(Boolean))].sort();
    const territoires = [...new Set(items.map((item) => item.territoire).filter(Boolean))].sort();
    const currentProvince = provinceSelect.value;
    const currentTerritoire = territoireSelect.value;
    provinceSelect.innerHTML = `<option value="">Toutes</option>${provinces.map((p) => `<option value="${escapeHtml(p)}">${escapeHtml(p)}</option>`).join('')}`;
    territoireSelect.innerHTML = `<option value="">Tous</option>${territoires.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('')}`;
    provinceSelect.value = currentProvince;
    territoireSelect.value = currentTerritoire;
  }

  function renderTable(items) {
    const body = document.querySelector('#ccn-table-body');
    if (!body) return;
    if (!items.length) {
      body.innerHTML = '<tr><td colspan="10">Aucun CCN pour ces filtres.</td></tr>';
      return;
    }
    body.innerHTML = items.map((item) => `
      <tr data-ccn-id="${escapeHtml(item.id)}" class="${ccnState.selectedId === item.id ? 'is-selected' : ''}">
        <td title="${escapeHtml(item.business_id)}">${escapeHtml(item.business_id)}</td>
        <td>${escapeHtml(item.name)}</td>
        <td>${escapeHtml(item.province)}</td>
        <td>${escapeHtml(item.territoire)}</td>
        <td>${escapeHtml(item.program_code)}</td>
        <td>${escapeHtml(item.ccn_type)}</td>
        <td>${escapeHtml(item.status)}</td>
        <td>${Number(item.population_served || 0).toLocaleString('fr-FR')}</td>
        <td>${escapeHtml(item.manager)}</td>
        <td>${escapeHtml(item.site_fdsu_code || '—')}</td>
      </tr>
    `).join('');
    body.querySelectorAll('[data-ccn-id]').forEach((row) => {
      row.addEventListener('click', () => openDetail(row.getAttribute('data-ccn-id')));
    });
  }

  function ensureMap() {
    if (ccnState.map || typeof global.L === 'undefined') return;
    const el = document.querySelector('#ccn-map');
    if (!el) return;
    ccnState.map = global.L.map(el, { zoomControl: true }).setView([-2.8, 23.5], 5);
    global.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 18,
    }).addTo(ccnState.map);
    ccnState.layer = global.L.layerGroup().addTo(ccnState.map);
  }

  function renderMap(geojson) {
    ensureMap();
    if (!ccnState.map || !ccnState.layer) return;
    ccnState.layer.clearLayers();
    const features = geojson?.features || [];
    features.forEach((feature) => {
      const kind = feature.properties?.kind;
      if (kind === 'site_ccn_link') {
        global.L.geoJSON(feature, {
          style: { color: '#93c5fd', weight: 2, dashArray: '4 4', opacity: 0.8 },
        }).addTo(ccnState.layer);
        return;
      }
      const coords = feature.geometry?.coordinates;
      if (!coords) return;
      const latlng = [coords[1], coords[0]];
      if (kind === 'ccn') {
        const marker = global.L.circleMarker(latlng, {
          radius: 8,
          color: '#fbbf24',
          fillColor: '#f59e0b',
          fillOpacity: 0.9,
        }).bindPopup(`<strong>${escapeHtml(feature.properties.name)}</strong><br>${escapeHtml(feature.properties.business_id)}`);
        if (global.SigMapTooltips?.bindHoverTooltip) {
          global.SigMapTooltips.bindHoverTooltip(marker, 'ccn', feature.properties);
        }
        marker.on('click', () => openDetail(feature.properties.id));
        marker.addTo(ccnState.layer);
      } else if (kind === 'site_fdsu') {
        const siteMarker = global.L.marker(latlng).bindPopup(`Site FDSU<br>${escapeHtml(feature.properties.code)}`);
        if (global.SigMapTooltips?.bindHoverTooltip) {
          global.SigMapTooltips.bindHoverTooltip(siteMarker, 'site_fdsu', feature.properties);
        }
        siteMarker.addTo(ccnState.layer);
      }
    });
    global.setTimeout(() => ccnState.map.invalidateSize(), 80);
  }

  function renderDoctrine(payload) {
    const box = document.querySelector('#ccn-doctrine-summary');
    if (!box) return;
    const criteria = payload?.doctrine?.selection_criteria || [];
    const rules = payload?.doctrine?.opposability_rules || [];
    box.innerHTML = `
      <p><strong>${escapeHtml(payload?._meta?.title || 'Doctrine')}</strong> — v${escapeHtml(payload?._meta?.version)} — source ${escapeHtml(payload?._meta?.source_document || '')}</p>
      <p>Critères de sélection (pondérations versionnées) :</p>
      ${criteria.map((item) => `
        <div class="ccn-doctrine-row">
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(item.weight_percent)} %</strong>
        </div>
      `).join('')}
      <p style="margin-top:10px">Règles d'opposabilité :</p>
      <ul>${rules.map((rule) => `<li>${escapeHtml(rule.label)}</li>`).join('')}</ul>
    `;
  }

  function setCcnDetailTab(tabId) {
    const root = document.querySelector('#ccn-detail');
    if (!root) return;
    root.querySelectorAll('[data-ccn-tab]').forEach((btn) => {
      btn.classList.toggle('is-active', btn.getAttribute('data-ccn-tab') === tabId);
    });
    root.querySelectorAll('[data-ccn-tab-panel]').forEach((panel) => {
      const active = panel.getAttribute('data-ccn-tab-panel') === tabId;
      panel.hidden = !active;
      if (active) panel.removeAttribute('hidden');
      else panel.setAttribute('hidden', '');
    });
  }

  function renderJustification(payload) {
    const box = document.querySelector('#ccn-justification-body');
    if (!box) return;
    const items = payload?.justification || [];
    const doctrine = payload?.doctrine || {};
    box.innerHTML = `
      <p><strong>${escapeHtml(payload?.summary?.text || '')}</strong></p>
      <p>Doctrine : ${escapeHtml(doctrine.title)} v${escapeHtml(doctrine.version)} — ${escapeHtml(doctrine.date || '')}</p>
      <p>Confiance : ${escapeHtml(payload?.confidence?.label || '—')}</p>
      ${items.map((item) => `
        <article class="ccn-justify-item">
          <h5>${escapeHtml(item.label)} — ${escapeHtml(item.contribution_display || item.score_display)}</h5>
          <p><strong>Pourquoi ?</strong> ${escapeHtml(item.why)}</p>
        </article>
      `).join('') || '<p>Aucune justification disponible.</p>'}
    `;
  }

  function renderCaseFile(casePayload) {
    const box = document.querySelector('#ccn-case-body');
    if (!box) return;
    const c = casePayload || {};
    box.innerHTML = `
      <div class="ccn-case-grid">
        <p><strong>Dossier :</strong> ${escapeHtml(c.case_id)}</p>
        <p><strong>Score :</strong> ${escapeHtml(c.score?.global)} / 100 — ${escapeHtml(c.score?.priority_level)}</p>
        <p><strong>Confiance :</strong> ${escapeHtml(c.confidence?.label)}</p>
        <p><strong>Doctrine :</strong> ${escapeHtml(c.doctrine?.title)} v${escapeHtml(c.doctrine?.version)}</p>
        <p><strong>Matrice :</strong> ${escapeHtml(c.matrix?.id)}</p>
        <p><strong>Impact population :</strong> ${Number(c.impacts?.population_touchee || 0).toLocaleString('fr-FR')}</p>
        <p><strong>Services numériques :</strong> ${escapeHtml(c.impacts?.services_numeriques)}</p>
        <p><strong>Risques :</strong> ${(c.risks || []).map((r) => escapeHtml(r.label)).join(', ') || 'Aucun signalé'}</p>
        <p><strong>Hypothèses :</strong></p>
        <ul>${(c.assumptions || []).map((a) => `<li>${escapeHtml(a)}</li>`).join('')}</ul>
        <p><strong>Sources :</strong></p>
        <ul>${(c.sources || []).map((s) => `<li>${escapeHtml(s)}</li>`).join('')}</ul>
        <p><strong>Traçabilité :</strong> moteur ${escapeHtml(c.engine_version)} — ${escapeHtml(c.generated_at)} — utilisateur ${escapeHtml(c.traceability?.user?.label || 'system')}</p>
        <p><em>${escapeHtml(c.pdf_export?.note || '')}</em></p>
      </div>
    `;
  }

  function openDetail(ccnId) {
    ccnState.selectedId = ccnId;
    renderTable(ccnState.items);
    Promise.all([
      fetchJson(`/api/ccn/${encodeURIComponent(ccnId)}`),
      fetchJson(`/api/decision/explain/${encodeURIComponent(ccnId)}?asset_type=ccn`),
      fetchJson(`/api/decision/case/${encodeURIComponent(ccnId)}?asset_type=ccn`),
    ])
      .then(([payload, explain, caseFile]) => {
        const ccn = payload?.ccn || {};
        const panel = document.querySelector('#ccn-detail');
        const title = document.querySelector('#ccn-detail-title');
        const body = document.querySelector('#ccn-detail-body');
        if (!panel || !body) return;
        if (title) title.textContent = ccn.name || ccn.business_id || 'Fiche CCN';
        const sections = ccn.sections || {};
        const block = (label, content) => `
          <section class="ccn-detail-section">
            <h4>${escapeHtml(label)}</h4>
            ${content}
          </section>
        `;
        body.innerHTML = [
          block('Identification', `<p>Code : ${escapeHtml(ccn.business_id)}</p><p>Type : ${escapeHtml(ccn.ccn_type_label || ccn.ccn_type)}</p><p>Statut : ${escapeHtml(ccn.status)}</p><p>Score priorité : ${escapeHtml(ccn.priority_score)} (${escapeHtml(ccn.priority_level)})</p>`),
          block('Localisation', `<p>${escapeHtml(ccn.province)} / ${escapeHtml(ccn.territoire)} / Zone ${escapeHtml(ccn.zone)}</p><p>Hôte : ${escapeHtml(ccn.host_type)}</p>`),
          block('Connectivité', `<p>Site FDSU : ${escapeHtml(ccn.site_fdsu_code)}</p><p>${escapeHtml(ccn.site_fdsu_name)}</p>`),
          block('Équipements', `<ul>${(sections.equipements || []).map((x) => `<li>${escapeHtml(x)}</li>`).join('') || '<li>—</li>'}</ul>`),
          block('Services', `<ul>${(sections.services || []).map((x) => `<li>${escapeHtml(x)}</li>`).join('') || '<li>—</li>'}</ul>`),
          block('Exploitation', `<p>Gestionnaire : ${escapeHtml(ccn.manager)}</p>`),
          block('Maintenance', `<p>${escapeHtml(ccn.maintenance_status)}</p>`),
          block('Population', `<p>${Number(ccn.population_served || 0).toLocaleString('fr-FR')} habitants</p>`),
          block('Indicateurs', `<p>Flags : ${(ccn.measurement_flags || []).map(escapeHtml).join(', ') || '—'}</p>`),
          block('Impact', `<p>Services : ${(ccn.services || []).length}</p><p>Population : ${Number(ccn.population_served || 0).toLocaleString('fr-FR')}</p>`),
          block('Historique', `<ul>${(sections.historique || []).map((h) => `<li>${escapeHtml(h.note || h.event)}</li>`).join('')}</ul>`),
          block('Critères doctrine', `<ul>${(ccn.criteria_details || []).map((c) => `<li>${escapeHtml(c.label)} : ${escapeHtml(c.score)} × ${escapeHtml(c.weight_percent)}%</li>`).join('')}</ul>`),
        ].join('');
        renderJustification(explain);
        renderCaseFile(caseFile);
        setCcnDetailTab('fiche');
        panel.hidden = false;
        panel.removeAttribute('hidden');
      })
      .catch(() => {});
  }

  function loadModule() {
    if (ccnState.loading) return Promise.resolve();
    ccnState.loading = true;
    const query = currentFilters();
    const listPath = `/api/ccn?${query.toString()}`;
    const mapPath = `/api/ccn/map?${query.toString()}`;
    return Promise.all([
      fetchJson('/api/ccn/statistics'),
      fetchJson(listPath),
      fetchJson(mapPath),
      fetchJson('/api/ccn/doctrine'),
      fetchJson('/api/ccn?limit=500'),
    ])
      .then(([stats, list, map, doctrine, allList]) => {
        ccnState.items = list.ccn || [];
        ccnState.allItems = allList.ccn || ccnState.items;
        fillFilterOptions(ccnState.allItems);
        renderKpis(stats);
        renderTable(ccnState.items);
        renderMap(map.geojson);
        renderDoctrine(doctrine);
        ccnState.initialized = true;
      })
      .catch(() => {
        const body = document.querySelector('#ccn-table-body');
        if (body) body.innerHTML = '<tr><td colspan="10">Module CCN indisponible — vérifier l’API.</td></tr>';
      })
      .finally(() => {
        ccnState.loading = false;
      });
  }

  function bindFilters() {
    const root = document.querySelector('#ccn-panel');
    if (!root || root.dataset.bound === 'true') return;
    root.dataset.bound = 'true';
    root.querySelectorAll('select').forEach((select) => {
      select.addEventListener('change', () => loadModule());
    });
    document.querySelector('#ccn-filter-reset')?.addEventListener('click', () => {
      root.querySelectorAll('select').forEach((select) => { select.value = ''; });
      loadModule();
    });
    document.querySelector('#ccn-detail-close')?.addEventListener('click', () => {
      const panel = document.querySelector('#ccn-detail');
      if (panel) {
        panel.hidden = true;
        panel.setAttribute('hidden', '');
      }
    });
    document.querySelectorAll('#ccn-detail [data-ccn-tab]').forEach((btn) => {
      btn.addEventListener('click', () => setCcnDetailTab(btn.getAttribute('data-ccn-tab') || 'fiche'));
    });
  }

  function initializeCcnModule() {
    bindFilters();
    ensureMap();
    if (global.Edvs?.mountPresentationButton) {
      global.Edvs.mountPresentationButton('#ccn-edvs-presentation-slot');
    }
    return loadModule().then(() => {
      global.setTimeout(() => ccnState.map?.invalidateSize(), 120);
    });
  }

  global.ccnState = ccnState;
  global.initializeCcnModule = initializeCcnModule;
})(window);
