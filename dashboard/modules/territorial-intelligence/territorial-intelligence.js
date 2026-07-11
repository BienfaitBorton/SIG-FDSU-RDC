(function initTerritorialIntelligenceModule(global) {
  const API_BASE = 'http://127.0.0.1:8001';

  const tiState = {
    initialized: false,
    loading: false,
    territories: [],
    selectedId: null,
    profile: null,
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
    const value = typeof field.value === 'number' ? Number(field.value).toLocaleString('fr-FR') : field.value;
    return { text: String(value), status: field.status || 'confirmed', note: field.note };
  }

  function statusLabel(status) {
    const map = {
      confirmed: 'confirmé',
      estimated: 'estimé',
      partial: 'partiel',
      unavailable: 'indisponible',
      not_sourced: 'non sourcé',
      demonstration: 'démonstration',
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
  }

  function renderMap(geojson) {
    ensureMap();
    if (!tiState.map || !tiState.layer) return;
    tiState.layer.clearLayers();
    const features = geojson?.features || [];
    const bounds = [];
    features.forEach((feature) => {
      const kind = feature.properties?.kind;
      // Aussi binder le polygone territoire
      if (kind === 'territory_boundary') {
        const layer = global.L.geoJSON(feature, {
          style: { color: '#38bdf8', weight: 2, fillOpacity: 0.08 },
          onEachFeature: (feat, pathLayer) => {
            if (global.SigMapTooltips?.bindHoverTooltip) {
              global.SigMapTooltips.bindHoverTooltip(pathLayer, 'territoire', feat.properties || feature.properties || {});
            }
          },
        });
        layer.addTo(tiState.layer);
        try { bounds.push(layer.getBounds()); } catch (e) { /* ignore */ }
        return;
      }
      const coords = feature.geometry?.coordinates;
      if (!coords || feature.geometry?.type !== 'Point') return;
      const latlng = [coords[1], coords[0]];
      bounds.push(global.L.latLng(latlng));
      if (kind === 'site_fdsu') {
        const marker = global.L.circleMarker(latlng, { radius: 5, color: '#fbbf24', fillColor: '#f59e0b', fillOpacity: 0.9 })
          .bindPopup(`Site FDSU<br>${escapeHtml(feature.properties.name || feature.properties.code)}`);
        if (global.SigMapTooltips?.bindHoverTooltip) {
          global.SigMapTooltips.bindHoverTooltip(marker, 'site_fdsu', feature.properties);
        }
        marker.addTo(tiState.layer);
      } else if (kind === 'ccn') {
        const marker = global.L.circleMarker(latlng, { radius: 7, color: '#a78bfa', fillColor: '#8b5cf6', fillOpacity: 0.9 })
          .bindPopup(`CCN<br>${escapeHtml(feature.properties.name)}`);
        if (global.SigMapTooltips?.bindHoverTooltip) {
          global.SigMapTooltips.bindHoverTooltip(marker, 'ccn', feature.properties);
        }
        marker.addTo(tiState.layer);
      } else if (kind === 'health') {
        const marker = global.L.circleMarker(latlng, { radius: 5, color: '#34d399', fillColor: '#10b981', fillOpacity: 0.9 })
          .bindPopup(`Santé<br>${escapeHtml(feature.properties.name)}`);
        if (global.SigMapTooltips?.bindHoverTooltip) {
          global.SigMapTooltips.bindHoverTooltip(marker, 'health', feature.properties);
        }
        marker.addTo(tiState.layer);
      } else if (kind === 'uncovered_locality' || feature.properties?.coverage_status === 'uncovered') {
        const marker = global.L.circleMarker(latlng, { radius: 4, color: '#f87171', fillColor: '#ef4444', fillOpacity: 0.85 })
          .bindPopup(`Localité non couverte<br>${escapeHtml(feature.properties.name || feature.properties.nom || '')}`);
        if (global.SigMapTooltips?.bindHoverTooltip) {
          global.SigMapTooltips.bindHoverTooltip(marker, 'uncovered_locality', feature.properties);
        }
        marker.addTo(tiState.layer);
      }
    });
    if (bounds.length) {
      try {
        const group = global.L.featureGroup(bounds.filter((b) => b && b.getNorthEast ? [b] : []).flat());
        // fallback fit
        const latLngs = bounds.filter((b) => b.lat !== undefined);
        if (latLngs.length) tiState.map.fitBounds(global.L.latLngBounds(latLngs), { padding: [24, 24] });
      } catch (e) {
        const latLngs = bounds.filter((b) => b.lat !== undefined);
        if (latLngs.length) tiState.map.fitBounds(global.L.latLngBounds(latLngs), { padding: [24, 24] });
      }
    }
    global.setTimeout(() => tiState.map.invalidateSize(), 80);
  }

  function renderSections(profilePayload, recommendations, explain) {
    const box = document.querySelector('#ti-sections');
    if (!box) return;
    const s = profilePayload?.sections || {};
    const p = profilePayload?.profile || {};
    const line = (label, fieldObj) => {
      const f = formatField(fieldObj);
      return `<p><strong>${escapeHtml(label)} :</strong> ${escapeHtml(f.text)} <span class="ti-status is-${f.status}">${escapeHtml(statusLabel(f.status))}</span></p>`;
    };

    const recHtml = (recommendations?.recommendations || []).map((rec) => `
      <article class="ti-rec">
        <h4>${escapeHtml(rec.action)}</h4>
        <p><strong>Pourquoi ?</strong> ${escapeHtml(rec.why)}</p>
        <p>Doctrine : ${escapeHtml(rec.doctrine?.id || '—')} v${escapeHtml(rec.doctrine?.version || '—')}</p>
        <p>Confiance : ${escapeHtml(rec.confidence_level)} — Données manquantes : ${escapeHtml((rec.missing_data || []).join(', ') || '—')}</p>
      </article>
    `).join('') || '<p>Aucune recommandation.</p>';

    box.innerHTML = `
      <section class="ti-section">
        <h3>A. Synthèse territoriale</h3>
        ${line('Province', s.synthesis?.province)}
        ${line('Zone FDSU', s.synthesis?.fdsu_zone)}
        ${line('Population', s.synthesis?.population)}
        ${line('Superficie', s.synthesis?.area_km2)}
        ${line('Densité', s.synthesis?.density)}
        ${line('Localités', s.synthesis?.localities)}
        ${line('Groupements', s.synthesis?.groupements)}
      </section>
      <section class="ti-section">
        <h3>B. Situation numérique</h3>
        ${line('Sites 20 476', s.digital?.sites_fdsu_presents?.sites_20476)}
        ${line('Sites 300', s.digital?.sites_fdsu_presents?.sites_300)}
        ${line('Sites 40', s.digital?.sites_fdsu_presents?.sites_40)}
        ${line('CCN', s.digital?.ccn_presents_ou_proposes)}
        ${line('Distance moyenne sites', s.digital?.distance_moyenne_sites)}
        ${line('Télécom', s.digital?.infrastructures_telecom)}
        ${line('Fibre', s.digital?.fibre)}
      </section>
      <section class="ti-section">
        <h3>C. Services publics</h3>
        ${line('Santé', s.public_services?.etablissements_sante)}
        ${line('Écoles', s.public_services?.ecoles)}
        ${line('Administrations', s.public_services?.administrations)}
        ${line('Marchés', s.public_services?.marches)}
      </section>
      <section class="ti-section">
        <h3>D–F. Économie / Accessibilité / Énergie</h3>
        ${line('Agriculture', s.economy?.agriculture)}
        ${line('Routes', s.accessibility?.routes)}
        ${line('Aérodromes (signal)', s.accessibility?.aerodromes)}
        ${line('Énergie', s.energy?.disponibilite)}
      </section>
      <section class="ti-section">
        <h3>G–H. Programmes & Priorité FDSU</h3>
        ${line('Score territorial', s.priority?.score)}
        ${line('Niveau', s.priority?.level)}
        <p>Confiance profil : <strong>${escapeHtml(p.confidence_level)}</strong></p>
        <p>Gaps : ${escapeHtml((profilePayload?.data_gaps || []).join(', ') || '—')}</p>
      </section>
      <section class="ti-section">
        <h3>I. Recommandations</h3>
        <div class="ti-recs">${recHtml}</div>
      </section>
      <section class="ti-section">
        <h3>J–K. Opportunités & Risques</h3>
        <ul>${(s.opportunities?.items || []).map((i) => `<li>${escapeHtml(i.label)} <span class="ti-status is-${i.status || 'confirmed'}">${escapeHtml(statusLabel(i.status || 'confirmed'))}</span></li>`).join('')}</ul>
        <ul>${(s.risks?.items || []).map((i) => `<li>${escapeHtml(i.label)}${i.note ? ` — ${escapeHtml(i.note)}` : ''}</li>`).join('')}</ul>
      </section>
      <section class="ti-section">
        <h3>L. Justification</h3>
        <p>Doctrine : ${escapeHtml(explain?.doctrine?.title || explain?.doctrine?.id)} v${escapeHtml(explain?.doctrine?.version)}</p>
        <p>Matrice : ${escapeHtml(explain?.matrix)}</p>
        <p>Hypothèses :</p>
        <ul>${(explain?.assumptions || []).map((a) => `<li>${escapeHtml(a)}</li>`).join('')}</ul>
        <p>Sources :</p>
        <ul>${(explain?.sources || []).map((a) => `<li>${escapeHtml(a)}</li>`).join('')}</ul>
      </section>
    `;
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
      const p = profile.profile || {};
      const title = document.querySelector('#ti-territory-title');
      if (title) title.textContent = `${p.territory_name || ''} — ${p.province || ''} · Zone ${p.fdsu_zone || ''}`;
      if (banner) {
        banner.textContent = p.is_demo_focus
          ? `Cas de démonstration : ${p.territory_name}. Qualité ${p.data_quality} — confiance ${p.confidence_level}. Aucune valeur inventée.`
          : `Profil consolidé. Qualité ${p.data_quality} — confiance ${p.confidence_level}.`;
      }
      setKpi('#ti-kpi-pop', p.population);
      setKpi('#ti-kpi-sites', profile.sections?.programs?.sites_20476);
      setKpi('#ti-kpi-sites300', profile.sections?.programs?.sites_300);
      setKpi('#ti-kpi-ccn', profile.sections?.programs?.ccn);
      setKpi('#ti-kpi-health', profile.sections?.public_services?.etablissements_sante);
      setKpi('#ti-kpi-score', profile.sections?.priority?.score);
      setKpi('#ti-kpi-conf', { value: p.confidence_level, status: p.confidence_level === 'high' ? 'confirmed' : 'partial' });

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
            { label: 'Population', value: fieldVal(p.population), icon: 'people', color: colorFor(fieldStatus(p.population)), confidence: p.confidence_level, note: p.population?.note },
            { label: 'Sites 20 476', value: fieldVal(profile.sections?.programs?.sites_20476), icon: 'sites', color: 'blue', confidence: 'high' },
            { label: 'Sites 300', value: fieldVal(profile.sections?.programs?.sites_300), icon: 'program', color: 'orange', confidence: 'high' },
            { label: 'CCN', value: fieldVal(profile.sections?.programs?.ccn), icon: 'ccn', color: colorFor(fieldStatus(profile.sections?.programs?.ccn)), confidence: 'medium' },
            { label: 'Santé', value: fieldVal(profile.sections?.public_services?.etablissements_sante), icon: 'data', color: colorFor(fieldStatus(profile.sections?.public_services?.etablissements_sante)), confidence: 'medium' },
            { label: 'Score', value: fieldVal(profile.sections?.priority?.score), icon: 'decision', color: 'orange', confidence: p.confidence_level, note: 'Estimé' },
            { label: 'Confiance', valueDisplay: p.confidence_level, value: p.confidence_level, icon: 'gauge', color: colorFor(p.confidence_level === 'high' ? 'confirmed' : 'partial'), confidence: p.confidence_level },
          ]);
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
  }

  function initializeTerritorialIntelligenceModule() {
    bindUi();
    ensureMap();
    if (global.Edvs?.mountPresentationButton) {
      global.Edvs.mountPresentationButton('#ti-edvs-presentation-slot');
    }
    return loadTerritoryList().then(() => {
      tiState.initialized = true;
      global.setTimeout(() => tiState.map?.invalidateSize(), 120);
    });
  }

  global.tiState = tiState;
  global.initializeTerritorialIntelligenceModule = initializeTerritorialIntelligenceModule;
})(window);
