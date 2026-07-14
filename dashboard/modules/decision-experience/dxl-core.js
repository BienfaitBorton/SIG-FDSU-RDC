/**
 * DXL Core — shell partagé (utils, fetch, map coverage, section renderers).
 * Attaché à window.DxlCore. Ne possède ni Integrity Gate ni Spatial Decision Graph.
 */
(function initDxlCore(global) {
  const API_BASE = `${global.location.protocol}//${global.location.hostname}:8001`;

  const SERVICE_LABELS = {
    impact: 'Analyse d’Impact Territorial',
    needs: 'Needs',
    explain: 'Explain',
    coverage: 'Coverage',
    decisionCase: 'Decision Engine',
    statistics: 'Statistics',
    map: 'Carte NSME',
  };

  const state = {
    initialized: false,
    mode: null, // decision-case | spatial-impact
    assetType: null,
    assetId: null,
    programCode: null,
    payload: null,
    services: null,
    map: null,
    layer: null,
    loading: false,
  };

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatNumber(value) {
    if (value == null || value === '') return '—';
    const n = Number(value);
    if (Number.isNaN(n)) return String(value);
    return new Intl.NumberFormat('fr-FR').format(n);
  }

  function formatUserDate(value) {
    if (value == null || value === '' || value === '—') return '—';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    return new Intl.DateTimeFormat('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(d);
  }

  function humanText(value, fallback = '') {
    if (value == null || value === '') return fallback;
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      return String(value);
    }
    if (Array.isArray(value)) {
      return value.map((item) => humanText(item)).filter(Boolean).join(' · ') || fallback;
    }
    if (typeof value === 'object') {
      for (const key of ['text', 'recommendation', 'label', 'title', 'detail', 'display', 'value', 'message']) {
        if (value[key] != null && value[key] !== '') return humanText(value[key], fallback);
      }
      return fallback;
    }
    return fallback;
  }

  function matrixLabel(matrix) {
    if (!matrix) return 'Matrice de priorisation des sites FDSU';
    if (typeof matrix === 'string') {
      if (matrix.includes('priority_matrix') || matrix.includes('/')) {
        return 'Matrice de priorisation des sites FDSU';
      }
      return matrix;
    }
    return humanText(matrix.label || matrix.id || matrix.title, 'Matrice de priorisation des sites FDSU');
  }

  function summarizePayload(payload) {
    if (payload == null) return null;
    if (typeof payload !== 'object') return { type: typeof payload };
    if (Array.isArray(payload)) return { type: 'array', length: payload.length };
    const keys = Object.keys(payload).slice(0, 12);
    return {
      type: 'object',
      keys,
      featureCount: Array.isArray(payload.features) ? payload.features.length : undefined,
      matchCount: payload.match_count ?? (Array.isArray(payload.matches) ? payload.matches.length : undefined),
    };
  }

  function humanizeFetchErrorFallback(error, status) {
    const raw = String(error?.message || error || 'erreur inconnue');
    if (/failed to fetch|networkerror|load failed|network request failed/i.test(raw)) {
      return `Connexion impossible vers le service. Vérifiez que l’API est démarrée.`;
    }
    if (/abort/i.test(raw)) {
      return 'Délai dépassé — le service n’a pas répondu à temps.';
    }
    if (status === 404) return 'Dossier introuvable pour cet actif.';
    if (status === 400) return 'Données du dossier incohérentes ou incomplètes.';
    if (status && status >= 500) return 'Service décisionnel temporairement indisponible.';
    if (status) return 'Le service n’a pas pu fournir ce dossier.';
    if (/extra data|json|traceback|HTTP\s*\d{3}/i.test(raw)) {
      return 'Le dossier n’a pas pu être consolidé correctement.';
    }
    return raw;
  }

  function resolveHumanizeFetchError(error, status) {
    if (typeof global.DecisionErrorHandler?.humanizeFetchError === 'function') {
      return global.DecisionErrorHandler.humanizeFetchError(error, status);
    }
    return humanizeFetchErrorFallback(error, status);
  }

  /**
   * Fetch tracé : URL, status, payload, erreur, durée (ms).
   * Timeout par service pour ne jamais bloquer toute la vue (ex. /explain lent).
   * Ne lance jamais d’exception — retourne { ok, status, data, error, ms, url, service }.
   */
  async function tracedFetch(path, serviceKey, options = {}) {
    const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
    const started = global.performance?.now?.() ?? Date.now();
    const label = SERVICE_LABELS[serviceKey] || serviceKey || 'Service';
    const logBase = { service: serviceKey, label, url };
    const timeoutMs = Number(options.timeoutMs) > 0
      ? Number(options.timeoutMs)
      : (serviceKey === 'explain' ? 12000 : 20000);
    const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
    const timer = controller
      ? global.setTimeout(() => controller.abort(), timeoutMs)
      : null;

    console.info('[DXL fetch] →', { ...logBase, phase: 'start', timeoutMs });

    try {
      const response = await fetch(url, {
        headers: { Accept: 'application/json' },
        cache: 'no-store',
        signal: controller?.signal,
      });
      const ms = Math.round((global.performance?.now?.() ?? Date.now()) - started);
      const contentType = response.headers.get('content-type') || '';
      let data = null;
      let parseError = null;
      try {
        if (contentType.includes('application/json')) {
          data = await response.json();
        } else {
          const text = await response.text();
          data = text ? { _non_json: true, preview: text.slice(0, 200) } : null;
        }
      } catch (err) {
        parseError = err;
      }

      if (!response.ok) {
        const error = resolveHumanizeFetchError(
          parseError || new Error(`HTTP ${response.status}`),
          response.status,
        );
        console.warn('[DXL fetch] ✗', {
          ...logBase,
          status: response.status,
          ms,
          payload: summarizePayload(data),
          error,
        });
        return {
          ok: false,
          status: 'error',
          httpStatus: response.status,
          data: null,
          error,
          ms,
          url,
          service: serviceKey,
          label,
        };
      }

      if (parseError) {
        const error = `Réponse illisible : ${parseError.message}`;
        console.warn('[DXL fetch] ✗', { ...logBase, status: response.status, ms, error });
        return {
          ok: false,
          status: 'error',
          httpStatus: response.status,
          data: null,
          error,
          ms,
          url,
          service: serviceKey,
          label,
        };
      }

      console.info('[DXL fetch] ✓', {
        ...logBase,
        status: response.status,
        ms,
        payload: summarizePayload(data),
        error: null,
      });
      return {
        ok: true,
        status: 'loaded',
        httpStatus: response.status,
        data,
        error: null,
        ms,
        url,
        service: serviceKey,
        label,
      };
    } catch (err) {
      const ms = Math.round((global.performance?.now?.() ?? Date.now()) - started);
      const aborted = err?.name === 'AbortError';
      const error = aborted
        ? `Délai dépassé (${timeoutMs} ms) — le service ${label} n’a pas répondu à temps.`
        : resolveHumanizeFetchError(err);
      console.error('[DXL fetch] ✗', {
        ...logBase,
        status: null,
        ms,
        payload: null,
        error,
        raw: String(err?.message || err),
        aborted,
      });
      return {
        ok: false,
        status: 'error',
        httpStatus: null,
        data: null,
        error,
        ms,
        url,
        service: serviceKey,
        label,
      };
    } finally {
      if (timer) global.clearTimeout(timer);
    }
  }

  async function fetchJson(path) {
    const result = await tracedFetch(path, 'generic');
    if (!result.ok) throw new Error(result.error || 'Données indisponibles');
    return result.data;
  }

  function parseHash() {
    const hash = (global.location.hash || '').replace(/^#/, '');
    const [pathPart, queryPart] = hash.split('?');
    const params = new URLSearchParams(queryPart || '');
    const parts = pathPart.split('/').filter(Boolean);
    if (parts[0] === 'decision-case' && parts[1] && parts[2]) {
      return {
        mode: 'decision-case',
        assetType: parts[1],
        assetId: decodeURIComponent(parts[2]),
        programCode: params.get('program_code'),
      };
    }
    if (
      (parts[0] === 'spatial-impact' || parts[0] === 'analyse-impact-territorial')
      && parts[1] && parts[2]
    ) {
      return {
        mode: 'spatial-impact',
        assetType: parts[1],
        assetId: decodeURIComponent(parts[2]),
        programCode: params.get('program_code'),
      };
    }
    if (parts[0] === 'coverage-detail' && parts[1]) {
      return { mode: 'coverage-detail', assetType: 'territory', assetId: decodeURIComponent(parts[1]) };
    }
    if (parts[0] === 'ccn-detail' && parts[1]) {
      return { mode: 'decision-case', assetType: 'ccn', assetId: decodeURIComponent(parts[1]) };
    }
    return null;
  }

  function setStatus(text, isError) {
    const el = document.querySelector('#dxl-status');
    if (!el) return;
    el.textContent = text;
    el.classList.toggle('is-error', Boolean(isError));
  }

  function setLoading(isLoading) {
    state.loading = Boolean(isLoading);
    const root = document.querySelector('#decision-experience-panel');
    if (!root) return;
    root.classList.toggle('is-loading', state.loading);
    root.style.opacity = '1';
    root.style.filter = 'none';
    root.style.pointerEvents = 'auto';
  }

  function serviceIcon(status) {
    if (status === 'loaded') return '🟢';
    if (status === 'loading') return '🟡';
    if (status === 'error') return '🔴';
    return '🟡';
  }

  function renderServicesPanel(services) {
    const host = document.querySelector('#dxl-section-services');
    const list = document.querySelector('#dxl-services-list');
    if (!host || !list) return;
    const order = ['impact', 'needs', 'explain', 'coverage', 'decisionCase', 'statistics', 'map'];
    const entries = order
      .filter((key) => services[key])
      .map((key) => {
        const svc = services[key];
        const detail = svc.status === 'loaded'
          ? `OK${svc.ms != null ? ` · ${svc.ms} ms` : ''}`
          : (svc.error || 'En attente');
        return `
          <li data-service="${escapeHtml(key)}" data-status="${escapeHtml(svc.status)}">
            <span class="dxl-svc-icon" aria-hidden="true">${serviceIcon(svc.status)}</span>
            <span class="dxl-svc-meta">
              <span class="dxl-svc-name">${escapeHtml(svc.label || SERVICE_LABELS[key] || key)}</span>
              <span class="dxl-svc-detail">${escapeHtml(detail)}</span>
            </span>
          </li>
        `;
      });
    list.innerHTML = entries.join('');
    host.hidden = entries.length === 0;
  }

  function softErrorHtml(title, detail, hint) {
    return `
      <p class="dxl-panel-soft-error">
        <strong>${escapeHtml(title)}</strong><br>
        ${escapeHtml(detail || '')}
        ${hint ? `<br>${escapeHtml(hint)}` : ''}
      </p>
    `;
  }

  function softLoadingHtml(title) {
    return `<p class="dxl-empty">${escapeHtml(title)}</p>`;
  }

  function attachResilientBasemap(map) {
    if (!map || !global.L) return null;
    if (typeof global.SigBasemapManager === 'function') {
      const manager = new global.SigBasemapManager({ timeoutMs: 3000, retries: 1 });
      manager.attach(map);
      return manager;
    }
    return global.L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      maxZoom: 20,
      subdomains: 'abcd',
    }).addTo(map);
  }

  function ensureMap() {
    const host = document.querySelector('#dxl-map');
    if (!host || !global.L) return null;
    if (state.map) {
      state.map.invalidateSize();
      return state.map;
    }
    state.map = global.L.map(host, { zoomControl: true }).setView([-2.8, 23.5], 5);
    attachResilientBasemap(state.map);
    state.layer = global.L.layerGroup().addTo(state.map);
    return state.map;
  }

  function renderMapFromNsme(nsmeMap) {
    const map = ensureMap();
    if (!map || !state.layer) return;
    state.layer.clearLayers();
    const features = nsmeMap?.features || [];
    features.forEach((feature) => {
      const kind = feature.properties?.kind;
      const props = feature.properties || {};
      if (feature.geometry?.type === 'Point') {
        const [lon, lat] = feature.geometry.coordinates;
        const marker = global.L.circleMarker([lat, lon], {
          radius: kind === 'asset' ? 8 : 5,
          color: kind === 'asset' ? '#b45309' : '#dc2626',
          fillColor: kind === 'asset' ? '#fbbf24' : '#fca5a5',
          fillOpacity: 0.85,
          weight: 1,
        });
        const tipKind = kind === 'asset' ? 'site' : (kind === 'linked_locality' ? 'uncovered_locality' : 'spatial_match');
        if (global.SigMapTooltips?.bind) {
          global.SigMapTooltips.bind(marker, props, tipKind, {
            onClick: () => {
              if (kind === 'linked_locality') return;
            },
          });
        }
        state.layer.addLayer(marker);
      } else if (feature.geometry?.type === 'LineString') {
        const line = global.L.geoJSON(feature, {
          style: { color: '#f59e0b', weight: 2, dashArray: '4 4', opacity: 0.85 },
        });
        if (global.SigMapTooltips?.bind) {
          line.eachLayer((lyr) => {
            global.SigMapTooltips.bind(lyr, props, 'spatial_match', { hint: false });
          });
        }
        state.layer.addLayer(line);
      }
    });
    try {
      if (state.layer.getLayers().length) {
        map.fitBounds(global.L.featureGroup(state.layer.getLayers()).getBounds().pad(0.2));
      }
    } catch (_e) { /* ignore */ }
    global.setTimeout(() => map.invalidateSize(), 80);
  }

  function renderExecutiveSummary(caseFile, impact) {
    const host = document.querySelector('#dxl-section-summary');
    if (!host) return;
    const site = caseFile?.asset || caseFile?.site || {};
    const scoreObj = caseFile?.score;
    const scoreRaw = site.priority_score
      ?? (scoreObj && typeof scoreObj === 'object' ? scoreObj.global : scoreObj)
      ?? caseFile?.summary?.score;
    const score = humanText(scoreRaw, '—');
    const level = humanText(
      site.priority_level_label
        || site.priority_level
        || (scoreObj && typeof scoreObj === 'object' ? (scoreObj.priority_label || scoreObj.priority_level) : null)
        || caseFile?.priority_level
        || caseFile?.summary?.priority_label,
      '—',
    );
    const confidence = humanText(
      caseFile?.confidence?.level || caseFile?.confidence_level || impact?.confidence_level,
      '—',
    );
    const reco = humanText(
      caseFile?.recommendation_text
        || caseFile?.summary?.recommendation
        || caseFile?.summary?.text
        || caseFile?.recommendation?.text
        || caseFile?.summary,
      'Recommandation en cours de consolidation.',
    );
    host.innerHTML = `
      <div class="dxl-summary-grid">
        <div>
          <p class="dxl-kicker">Résumé exécutif</p>
          <h3>${escapeHtml(site.site_name || site.name || site.site_code || state.assetId)}</h3>
          <p>Code : <strong>${escapeHtml(site.site_code || site.business_id || state.assetId)}</strong>
             · Programme : <strong>${escapeHtml(site.program_code || state.programCode || '—')}</strong></p>
          <p>Statut / priorité : <strong>${escapeHtml(level)}</strong>
             · Score : <strong>${escapeHtml(score ?? '—')}</strong>
             · Confiance : <strong>${escapeHtml(confidence)}</strong></p>
        </div>
        <aside class="dxl-reco-card">
          <p class="dxl-kicker">Recommandation principale</p>
          <p>${escapeHtml(reco)}</p>
        </aside>
      </div>
    `;
  }

  function renderWhy(caseFile) {
    const host = document.querySelector('#dxl-section-why');
    if (!host) return;
    const criteria = caseFile?.justification || caseFile?.criteria || caseFile?.explanation?.criteria || [];
    const list = Array.isArray(criteria) ? criteria : Object.values(criteria || {});
    if (!list.length) {
      host.innerHTML = '<p class="dxl-empty">Justification détaillée non encore disponible pour cet actif.</p>';
      return;
    }
    const max = Math.max(...list.map((c) => Number(c.contribution || c.weight_percent || 1)), 1);
    host.innerHTML = `
      <p class="dxl-kicker">Pourquoi ?</p>
      <ul class="dxl-waterfall">
        ${list.map((c) => `
          <li>
            <div class="dxl-waterfall-head">
              <strong>${escapeHtml(c.label || c.criterion_id || 'Critère')}</strong>
              <span>${escapeHtml(c.contribution_display || c.score_display || c.contribution || '—')}</span>
            </div>
            <div class="dxl-bartrack"><div class="dxl-barfill" style="width:${Math.round(Number(c.contribution || c.weight_percent || 0) / max * 100)}%"></div></div>
            <p>${escapeHtml(c.why || c.description || '')}</p>
          </li>
        `).join('')}
      </ul>
    `;
  }

  function renderContext(caseFile, ti) {
    const host = document.querySelector('#dxl-section-context');
    if (!host) return;
    const cov = ti?.needs?.coverage || ti?.sections?.coverage || {};
    const getVal = (field) => {
      if (!field) return '—';
      if (typeof field === 'object' && 'value' in field) return field.value ?? '—';
      return field;
    };
    host.innerHTML = `
      <p class="dxl-kicker">Contexte territorial</p>
      <div class="dxl-kpi-strip">
        <article><span>Population restante</span><strong>${escapeHtml(formatNumber(getVal(cov.population_uncovered) || ti?.spatial_matching?.population_remaining))}</strong></article>
        <article><span>Localités non couvertes</span><strong>${escapeHtml(formatNumber(getVal(cov.localities_uncovered)))}</strong></article>
        <article><span>NDCI</span><strong>${escapeHtml(getVal(cov.ndci) ?? '—')}</strong></article>
        <article><span>Santé (échantillon)</span><strong>${escapeHtml(formatNumber((ti?.assets?.health_sample || []).length))}</strong></article>
      </div>
      <p class="dxl-note">Sources : Intelligence territoriale · Référentiel National des Besoins · pas de valeur inventée.</p>
    `;
  }

  function renderImpact(impact, nsmeImpact) {
    const host = document.querySelector('#dxl-section-impact');
    if (!host) return;
    const data = nsmeImpact?.impact || impact || {};
    const gain = data.ndci_gain_estimated || nsmeImpact?.coverage_gain?.ndci_gain_estimated || {};
    host.innerHTML = `
      <p class="dxl-kicker">Impacts attendus</p>
      <div class="dxl-kpi-strip">
        <article><span>Population impactée</span><strong>${escapeHtml(formatNumber(data.population_impacted))}</strong><small>${escapeHtml(data.population_status || 'non_disponible')}</small></article>
        <article><span>Localités desservies</span><strong>${escapeHtml(formatNumber(data.localities_impacted))}</strong></article>
        <article><span>Infrastructures touchées</span><strong>${escapeHtml(formatNumber(data.essential_infrastructures))}</strong></article>
        <article><span>Distance moyenne</span><strong>${escapeHtml(data.avg_distance_m != null ? `${Math.round(data.avg_distance_m)} m` : '—')}</strong></article>
        <article><span>Gain NDCI estimé</span><strong>${escapeHtml(gain.value ?? '—')}</strong><small>${escapeHtml(gain.status || 'estime')}</small></article>
        <article><span>Confiance</span><strong>${escapeHtml(data.confidence_level || '—')}</strong></article>
      </div>
    `;
  }

  function renderRisks(caseFile) {
    const host = document.querySelector('#dxl-section-risks');
    if (!host) return;
    const risks = caseFile?.risks || [];
    const missing = caseFile?.missing_data || caseFile?.confidence?.missing || [];
    host.innerHTML = `
      <p class="dxl-kicker">Risques et données manquantes</p>
      <ul>${(risks.length ? risks : [{ label: 'Aucun risque critique signalé' }]).map((r) => `<li>${escapeHtml(r.label || r.type || r)}</li>`).join('')}</ul>
      <p><strong>Lacunes :</strong> ${escapeHtml(
        (missing && missing.length)
          ? missing.map((m) => humanText(m)).filter(Boolean).join(', ')
          : 'Aucune lacune identifiée'
      )}</p>
    `;
  }

  function renderTraceability(caseFile) {
    const host = document.querySelector('#dxl-section-trace');
    if (!host) return;
    const doctrine = caseFile?.doctrine || {};
    const meta = doctrine._meta || doctrine.meta || {};
    host.innerHTML = `
      <p class="dxl-kicker">Doctrine et traçabilité</p>
      <dl class="dxl-meta">
        <div><dt>Doctrine</dt><dd>${escapeHtml(meta.title || doctrine.title || doctrine.id || '—')}</dd></div>
        <div><dt>Version</dt><dd>${escapeHtml(meta.version || doctrine.version || '—')}</dd></div>
        <div><dt>Matrice</dt><dd>${escapeHtml(matrixLabel(caseFile?.matrix))}</dd></div>
        <div><dt>Moteur</dt><dd>Moteur de décision explicable FDSU</dd></div>
        <div><dt>Généré le</dt><dd>${escapeHtml(formatUserDate(caseFile?.generated_at || caseFile?._meta?.generated_at))}</dd></div>
        <details class="dxl-tech-trace">
          <summary>Détail technique (traçabilité)</summary>
          <p>Réf. matrice : <code>${escapeHtml(caseFile?.matrix?.ref || '—')}</code></p>
          <p>Horodatage ISO : <code>${escapeHtml(caseFile?.generated_at || caseFile?._meta?.generated_at || '—')}</code></p>
        </details>
      </dl>
    `;
  }

  function renderRecommendation(caseFile) {
    const host = document.querySelector('#dxl-section-reco');
    if (!host) return;
    const reco = humanText(
      caseFile?.recommendation_text
        || caseFile?.summary?.recommendation
        || caseFile?.summary?.text
        || caseFile?.summary,
      'Consolider la connaissance territoriale avant arbitrage final.',
    );
    const next = humanText(caseFile?.next_action, 'Comparer avec les besoins NCI associés et préparer l’arbitrage.');
    host.innerHTML = `
      <p class="dxl-kicker">Recommandation rédigée</p>
      <p>${escapeHtml(reco)}</p>
      <p><strong>Suite recommandée :</strong> ${escapeHtml(next)}</p>
    `;
  }

  function renderActions() {
    const host = document.querySelector('#dxl-actions');
    if (!host) return;
    const caps = global.CapabilityRegistry;
    const missionOk = caps?.isEnabled?.('mission_planning');
    const simOk = caps?.isEnabled?.('simulation');
    const pdfOk = caps?.isEnabled?.('export_pdf');
    const pptOk = caps?.isEnabled?.('export_powerpoint');
    const excelOk = caps?.isEnabled?.('export_excel') !== false;

    host.innerHTML = `
      <button type="button" class="secondary-button" data-dxl-action="back">← Retour</button>
      <button type="button" class="secondary-button" data-dxl-action="map">Voir sur la carte</button>
      <button type="button" class="secondary-button" data-dxl-action="ti">Intelligence territoriale</button>
      <button type="button" class="secondary-button" data-dxl-action="explain">Expliquer</button>
      <button type="button" class="secondary-button" data-dxl-action="spatial">Analyse d’Impact Territorial</button>
      ${missionOk ? '<button type="button" class="secondary-button" data-dxl-action="mission">Préparer une mission</button>' : ''}
      <button type="button" class="secondary-button" data-dxl-action="export" data-capability="export_excel" ${excelOk ? '' : 'disabled'}>Exporter Excel</button>
      <button type="button" class="secondary-button" data-dxl-action="pdf" data-capability="export_pdf" ${pdfOk ? '' : 'disabled'} title="${escapeHtml(caps?.reason?.('export_pdf') || 'Export PDF non encore activé pour ce dossier')}">Préparer PDF</button>
      <button type="button" class="secondary-button" data-dxl-action="ppt" data-capability="export_powerpoint" ${pptOk ? '' : 'disabled'} title="${escapeHtml(caps?.reason?.('export_powerpoint') || 'Export PowerPoint non encore activé pour ce dossier')}">Préparer PowerPoint</button>
      ${simOk ? '<button type="button" class="secondary-button" data-dxl-action="simulate">Simulation</button>' : ''}
    `;
    if (caps?.applyButton) {
      caps.applyButton(host.querySelector('[data-dxl-action="pdf"]'), 'export_pdf');
      caps.applyButton(host.querySelector('[data-dxl-action="ppt"]'), 'export_powerpoint');
      caps.applyButton(host.querySelector('[data-dxl-action="export"]'), 'export_excel');
    }
  }

  function emptyService(key) {
    return {
      status: 'loading',
      data: null,
      error: null,
      ms: null,
      url: null,
      httpStatus: null,
      service: key,
      label: SERVICE_LABELS[key] || key,
    };
  }

  function goBack() {
    try {
      const raw = global.sessionStorage?.getItem('fdsu.decisionCase.returnHash');
      if (raw) {
        global.sessionStorage.removeItem('fdsu.decisionCase.returnHash');
        global.location.hash = raw.replace(/^#/, '');
        return;
      }
    } catch (_err) { /* private mode */ }
    if (global.history.length > 1) {
      global.history.back();
      return;
    }
    global.location.hash = 'decision-view';
  }

  function notify(message, isError) {
    if (typeof global.UxPremium?.notify === 'function') {
      global.UxPremium.notify(message, isError ? 'error' : 'info');
      return;
    }
    setStatus(message, Boolean(isError));
  }

  function openMapForCurrentSite() {
    const caseFile = state.payload?.caseFile || state.payload?.decisionCase || {};
    const site = caseFile.asset || caseFile.site || {};
    const program = site.program_code || state.programCode || '';
    const focus = {
      site_id: state.assetId || site.site_id || site.id,
      site_code: site.site_code || site.business_id,
      program_code: program,
      latitude: site.latitude ?? site.lat,
      longitude: site.longitude ?? site.lon ?? site.lng,
    };
    try {
      global.sessionStorage?.setItem('fdsu.map.focusSite', JSON.stringify(focus));
    } catch (_err) { /* */ }
    if (typeof global.openDecisionSiteOnMap === 'function') {
      global.openDecisionSiteOnMap(focus);
      return;
    }
    global.location.hash = 'map';
  }

  async function exportCaseExcel(btn) {
    if (!state.assetId) {
      notify('Aucun dossier à exporter.', true);
      return;
    }
    const caps = global.CapabilityRegistry;
    if (caps && caps.isEnabled('export_excel') === false) {
      notify(caps.reason('export_excel'), true);
      return;
    }
    caps?.setBusy?.(btn, true, 'Export Excel…');
    const type = state.assetType || 'site';
    const qs = state.programCode ? `?program_code=${encodeURIComponent(state.programCode)}` : '';
    const url = `${API_BASE}/api/exports/decision-case/${encodeURIComponent(type)}/${encodeURIComponent(state.assetId)}/excel${qs}`;
    try {
      const response = await fetch(url, { headers: { Accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }, cache: 'no-store' });
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail.detail || `Export impossible (${response.status})`);
      }
      const blob = await response.blob();
      if (!blob || blob.size < 32) throw new Error('Fichier Excel vide');
      const disposition = response.headers.get('Content-Disposition') || '';
      const match = /filename="?([^"]+)"?/i.exec(disposition);
      const filename = match?.[1] || response.headers.get('X-FDSU-Export-Filename') || `Dossier_decision_${state.assetId}.xlsx`;
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(objectUrl);
      notify(`Export Excel téléchargé : ${filename}`);
    } catch (err) {
      console.error('[DXL] export excel', err);
      notify(err.message || 'Export Excel impossible.', true);
    } finally {
      caps?.setBusy?.(btn, false);
    }
  }

  global.DxlCore = {
    API_BASE,
    SERVICE_LABELS,
    state,
    escapeHtml,
    formatNumber,
    formatUserDate,
    humanText,
    matrixLabel,
    summarizePayload,
    tracedFetch,
    fetchJson,
    parseHash,
    setStatus,
    setLoading,
    serviceIcon,
    renderServicesPanel,
    softErrorHtml,
    softLoadingHtml,
    ensureMap,
    renderMapFromNsme,
    renderExecutiveSummary,
    renderWhy,
    renderContext,
    renderImpact,
    renderRisks,
    renderTraceability,
    renderRecommendation,
    renderActions,
    emptyService,
    goBack,
    notify,
    openMapForCurrentSite,
    exportCaseExcel,
  };
})(typeof window !== 'undefined' ? window : globalThis);
