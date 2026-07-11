/**
 * Decision Experience Layer (DXL)
 * Transforme les payloads API (Decision / NSME / TI) en dossiers métier dashboard.
 * Routes : #decision-case/<type>/<id> · #spatial-impact/<type>/<id>
 * Jamais d'ouverture /api/ pour l'utilisateur métier.
 */
(function initDecisionExperienceLayer(global) {
  const API_BASE = `${global.location.protocol}//${global.location.hostname}:8001`;

  const SERVICE_LABELS = {
    impact: 'Impact spatial',
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

  function humanizeFetchError(error, status) {
    const raw = String(error?.message || error || 'erreur inconnue');
    if (/failed to fetch|networkerror|load failed|network request failed/i.test(raw)) {
      return `Connexion impossible vers le service (${API_BASE}). Vérifiez que l’API est démarrée et accessible.`;
    }
    if (status) return `Réponse HTTP ${status}`;
    return raw;
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
        const error = humanizeFetchError(
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
        : humanizeFetchError(err);
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
    if (parts[0] === 'spatial-impact' && parts[1] && parts[2]) {
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

  function ensureMap() {
    const host = document.querySelector('#dxl-map');
    if (!host || !global.L) return null;
    if (state.map) {
      state.map.invalidateSize();
      return state.map;
    }
    state.map = global.L.map(host, { zoomControl: true }).setView([-2.8, 23.5], 5);
    global.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 18,
    }).addTo(state.map);
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
    const score = site.priority_score ?? caseFile?.score;
    const level = site.priority_level_label || site.priority_level || caseFile?.priority_level || '—';
    const confidence = caseFile?.confidence?.level || caseFile?.confidence_level || impact?.confidence_level || '—';
    const reco = caseFile?.recommendation_text || caseFile?.summary || caseFile?.recommendation?.text || 'Recommandation en cours de consolidation.';
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
      <p><strong>Lacunes :</strong> ${escapeHtml((missing || []).join(', ') || '—')}</p>
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
        <div><dt>Matrice</dt><dd>${escapeHtml(caseFile?.matrix?.ref || caseFile?.matrix || 'Matrice nationale de priorisation')}</dd></div>
        <div><dt>Moteur</dt><dd>Moteur de décision explicable FDSU</dd></div>
        <div><dt>Généré le</dt><dd>${escapeHtml(caseFile?.generated_at || caseFile?._meta?.generated_at || '—')}</dd></div>
      </dl>
    `;
  }

  function renderRecommendation(caseFile) {
    const host = document.querySelector('#dxl-section-reco');
    if (!host) return;
    host.innerHTML = `
      <p class="dxl-kicker">Recommandation rédigée</p>
      <p>${escapeHtml(caseFile?.recommendation_text || caseFile?.summary || 'Consolider la connaissance territoriale avant arbitrage final.')}</p>
      <p><strong>Suite recommandée :</strong> ${escapeHtml(caseFile?.next_action || 'Préparer une mission de terrain et comparer avec les besoins NCI associés.')}</p>
    `;
  }

  function renderActions() {
    const host = document.querySelector('#dxl-actions');
    if (!host) return;
    host.innerHTML = `
      <button type="button" class="secondary-button" data-dxl-action="back">← Retour</button>
      <button type="button" class="secondary-button" data-dxl-action="map">Voir sur la carte</button>
      <button type="button" class="secondary-button" data-dxl-action="ti">Intelligence territoriale</button>
      <button type="button" class="secondary-button" data-dxl-action="explain">Expliquer</button>
      <button type="button" class="secondary-button" data-dxl-action="spatial">Impact spatial</button>
      <button type="button" class="secondary-button" data-dxl-action="mission">Préparer une mission</button>
      <button type="button" class="secondary-button" data-dxl-action="export">Exporter Excel</button>
      <button type="button" class="secondary-button" data-dxl-action="pdf" title="Export PDF en préparation">Préparer PDF</button>
      <button type="button" class="secondary-button" data-dxl-action="ppt" title="Export PowerPoint en préparation">Préparer PowerPoint</button>
      <button type="button" class="secondary-button" data-dxl-action="simulate">Simulation future</button>
    `;
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

  /**
   * Charge l’impact spatial avec statut individuel par service.
   * Retourne { impact, needs, statistics, coverage, explain, map, decisionCase }.
   * Affichage progressif : les panneaux utiles s’affichent dès qu’un service répond.
   */
  async function loadSpatialImpactData(assetType, assetId) {
    const id = encodeURIComponent(assetId);
    const services = {
      impact: emptyService('impact'),
      needs: emptyService('needs'),
      explain: emptyService('explain'),
      coverage: emptyService('coverage'),
      decisionCase: emptyService('decisionCase'),
      statistics: emptyService('statistics'),
      map: emptyService('map'),
    };
    state.services = services;
    renderServicesPanel(services);

    const requests = [
      { key: 'needs', path: `/api/spatial-matching/assets/${id}/needs?limit=100` },
      { key: 'impact', path: `/api/spatial-matching/assets/${id}/impact` },
      { key: 'explain', path: `/api/spatial-matching/assets/${id}/explain`, timeoutMs: 12000 },
      { key: 'map', path: `/api/spatial-matching/map?asset_id=${id}` },
      { key: 'statistics', path: '/api/spatial-matching/statistics' },
      { key: 'decisionCase', path: `/api/decision/case/${id}?asset_type=${encodeURIComponent(assetType === 'site' ? 'site' : assetType)}` },
    ];

    const refreshCoverageDerived = () => {
      const impactData = services.impact.data;
      if (services.impact.status === 'loaded' && impactData?.coverage_gain) {
        services.coverage = {
          status: 'loaded',
          data: impactData.coverage_gain,
          error: null,
          ms: services.impact.ms,
          url: services.impact.url,
          httpStatus: services.impact.httpStatus,
          service: 'coverage',
          label: SERVICE_LABELS.coverage,
        };
      } else if (services.impact.status === 'error') {
        services.coverage = {
          status: 'error',
          data: null,
          error: 'Couverture indisponible faute d’impact spatial.',
          ms: null,
          url: null,
          httpStatus: null,
          service: 'coverage',
          label: SERVICE_LABELS.coverage,
        };
      } else if (services.impact.status === 'loaded') {
        services.coverage = {
          status: 'loaded',
          data: impactData?.impact || null,
          error: null,
          ms: services.impact.ms,
          url: services.impact.url,
          httpStatus: services.impact.httpStatus,
          service: 'coverage',
          label: SERVICE_LABELS.coverage,
        };
      }
    };

    const paint = () => {
      try {
        refreshCoverageDerived();
        renderServicesPanel(services);
        renderSpatialImpactWorkspace(services, assetId);
        const summary = summarizeServiceFailures(services);
        const stillLoading = Object.values(services).some((s) => s.status === 'loading');
        if (stillLoading) {
          setStatus(`Chargement… ${summary.text}`, summary.isError);
        } else {
          setStatus(summary.text, summary.isError);
        }
      } catch (paintErr) {
        console.error('[DXL] paint spatial-impact', paintErr);
        setStatus(`Affichage partiel — ${humanizeFetchError(paintErr)}`, true);
      }
    };

    await Promise.allSettled(
      requests.map(async ({ key, path, timeoutMs }) => {
        const result = await tracedFetch(path, key, timeoutMs ? { timeoutMs } : {});
        services[key] = {
          status: result.ok ? 'loaded' : 'error',
          data: result.data,
          error: result.error,
          ms: result.ms,
          url: result.url,
          httpStatus: result.httpStatus,
          service: key,
          label: SERVICE_LABELS[key] || key,
        };
        paint();
        return services[key];
      }),
    );

    refreshCoverageDerived();
    renderServicesPanel(services);
    return services;
  }

  function renderSpatialImpactWorkspace(services, assetId) {
    const needs = services.needs?.data;
    const impact = services.impact?.data;
    const explain = services.explain?.data;
    const mapPayload = services.map?.data;
    const decisionCase = services.decisionCase?.data;
    const statistics = services.statistics?.data;

    const title = document.querySelector('#dxl-title');
    if (title) {
      const name = needs?.asset?.site_name || decisionCase?.asset?.site_name || assetId;
      title.textContent = `Impact spatial — ${name}`;
    }

    // Résumé : ne dépend pas d’explain
    const summarySource = {
      asset: {
        site_code: assetId,
        site_name: needs?.asset?.site_name || decisionCase?.asset?.site_name || assetId,
        program_code: needs?.asset?.program_code || decisionCase?.asset?.program_code,
        priority_level_label: decisionCase?.asset?.priority_level_label || decisionCase?.priority_level,
        priority_score: decisionCase?.asset?.priority_score || decisionCase?.score,
      },
      summary: explain?.summary
        || (services.impact.status === 'loaded'
          ? 'Impact spatial calculé à partir des correspondances Actifs ↔ Besoins.'
          : 'Dossier d’impact spatial — certaines sources sont encore en cours de consolidation.'),
      confidence_level: explain?.confidence_level || impact?.impact?.confidence_level,
      recommendation_text: explain?.summary || decisionCase?.recommendation_text,
    };
    renderExecutiveSummary(summarySource, impact?.impact);

    // Impact / NDCI / population — indépendant
    const impactHost = document.querySelector('#dxl-section-impact');
    if (impactHost) {
      if (services.impact.status === 'loaded' && impact) {
        renderImpact({}, impact);
        const statsBits = [];
        if (services.coverage.status === 'loaded' && services.coverage.data) {
          const gain = services.coverage.data;
          statsBits.push(`<article><span>Couverture — gain NDCI</span><strong>${escapeHtml(gain.ndci_gain_estimated?.value ?? gain.value ?? '—')}</strong><small>${escapeHtml(gain.ndci_gain_estimated?.status || gain.status || 'estime')}</small></article>`);
        }
        if (services.statistics.status === 'loaded' && statistics) {
          statsBits.push(`<article><span>Statistiques nationales</span><strong>${escapeHtml(formatNumber(statistics.matches_total))}</strong><small>correspondances NSME</small></article>`);
        }
        if (statsBits.length) {
          impactHost.insertAdjacentHTML('beforeend', `<div class="dxl-kpi-strip" style="margin-top:0.75rem">${statsBits.join('')}</div>`);
        }
      } else if (services.impact.status === 'loading') {
        impactHost.innerHTML = softLoadingHtml('Chargement de l’impact spatial…');
      } else {
        impactHost.innerHTML = softErrorHtml(
          'Impact spatial indisponible',
          services.impact.error || 'Le service d’impact n’a pas répondu.',
          'Les autres volets (besoins, carte, explication) restent affichés s’ils sont disponibles.',
        );
      }
    }

    // Carte — message d’état sans dupliquer
    const mapSection = document.querySelector('#dxl-map')?.closest('.dxl-section');
    mapSection?.querySelectorAll(':scope > .dxl-panel-soft-error').forEach((el) => el.remove());
    try {
      if (services.map.status === 'loaded' && mapPayload) {
        renderMapFromNsme(mapPayload);
      } else {
        ensureMap();
        if (mapSection && services.map.status === 'error') {
          const note = document.createElement('p');
          note.className = 'dxl-panel-soft-error';
          note.innerHTML = `<strong>Carte indisponible</strong> — ${escapeHtml(services.map.error || 'Le service cartographique n’a pas répondu.')}`;
          document.querySelector('#dxl-map')?.before(note);
        }
      }
    } catch (mapErr) {
      console.warn('[DXL] rendu carte', mapErr);
      if (mapSection) {
        const note = document.createElement('p');
        note.className = 'dxl-panel-soft-error';
        note.innerHTML = '<strong>Carte indisponible</strong> — erreur de rendu cartographique.';
        document.querySelector('#dxl-map')?.before(note);
      }
    }

    // Explain — indépendant (ne masque jamais impact / carte / besoins)
    const why = document.querySelector('#dxl-section-why');
    if (why) {
      if (services.explain.status === 'loaded' && explain) {
        why.innerHTML = `
          <p class="dxl-kicker">Explication de la correspondance</p>
          <p>${escapeHtml(explain.summary || '—')}</p>
          <p>Distance : ${escapeHtml(explain.distance_m ?? '—')} m · Rayon : ${escapeHtml(explain.service_radius_m ?? '—')} m</p>
          <p>Règle spatiale : ${escapeHtml(explain.spatial_rule || '—')} · Méthode : ${escapeHtml(explain.calculation_method || '—')}</p>
        `;
      } else if (services.explain.status === 'loading') {
        why.innerHTML = softLoadingHtml('Chargement de l’analyse explicative…');
      } else {
        why.innerHTML = softErrorHtml(
          'Analyse explicative indisponible',
          'Le moteur d’explication n’a pas répondu.',
          'Les données d’impact restent consultables.',
        ) + (services.explain?.error ? `<p class="dxl-note">${escapeHtml(services.explain.error)}</p>` : '');
      }
    }

    // Needs / localités — indépendant
    const ctx = document.querySelector('#dxl-section-context');
    if (ctx) {
      if (services.needs.status === 'loaded' && needs) {
        const matches = (needs.matches || []).filter((m) => m.relation_type === 'SERVES_LOCALITY').slice(0, 12);
        ctx.innerHTML = `
          <p class="dxl-kicker">Besoins associés</p>
          <div class="dxl-kpi-strip">
            <article><span>Correspondances</span><strong>${escapeHtml(formatNumber(needs.match_count ?? matches.length))}</strong></article>
            <article><span>Population liée</span><strong>${escapeHtml(formatNumber(needs.population_impacted_sum ?? impact?.impact?.population_impacted))}</strong></article>
          </div>
          <ul>${matches.map((m) => `<li>${escapeHtml((m.properties || {}).locality_name || m.need_id)} — ${escapeHtml(m.distance_m != null ? `${Math.round(m.distance_m)} m` : '—')} — pop. ${escapeHtml(formatNumber(m.population_impacted))}</li>`).join('') || '<li>Aucun besoin apparié dans le rayon configurable.</li>'}</ul>
        `;
      } else if (services.needs.status === 'loading') {
        ctx.innerHTML = softLoadingHtml('Chargement des besoins associés…');
      } else {
        ctx.innerHTML = softErrorHtml(
          'Besoins associés indisponibles',
          services.needs.error || 'Le service Needs n’a pas répondu.',
          'La carte et l’impact restent consultables si disponibles.',
        );
      }
    }

    // Risques / reco / traçabilité — tolérants
    renderRisks({
      missing_data: explain?.missing_data || [],
      risks: services.explain.status === 'error'
        ? [{ label: 'Explication spatiale partiellement indisponible' }]
        : [],
    });
    renderTraceability({
      doctrine: { title: 'National Spatial Matching Engine', version: 'nsme-1.0.0' },
      generated_at: impact?._meta?.generated_at || statistics?._meta?.generated_at,
    });
    renderRecommendation({
      recommendation_text: explain?.summary
        || (services.impact.status === 'loaded'
          ? 'Prioriser les localités desservies à population impactée élevée.'
          : 'Consolider les correspondances spatiales avant arbitrage.'),
      next_action: 'Préparer une mission sur les localités à priorité élevée les plus proches.',
    });
    renderActions();
  }

  function summarizeServiceFailures(services) {
    const values = Object.values(services || {}).filter(Boolean);
    const failed = values.filter((s) => s.status === 'error');
    const loaded = values.filter((s) => s.status === 'loaded');
    const loading = values.filter((s) => s.status === 'loading');
    if (loading.length && !failed.length) {
      return { text: `${loaded.length} prêt(s) · ${loading.length} en cours`, isError: false };
    }
    if (!failed.length) {
      return { text: `${loaded.length} service(s) prêts`, isError: false };
    }
    if (!loaded.length && !loading.length) {
      const names = failed.map((s) => s.label).join(', ');
      return {
        text: `Aucun service joignable (${names}). ${failed[0]?.error || ''}`.trim(),
        isError: true,
      };
    }
    const names = failed.map((s) => s.label).join(', ');
    return {
      text: `Affichage partiel — indisponible : ${names}. Les autres données restent consultables.`,
      isError: true,
    };
  }

  async function loadSpatialImpact(assetType, assetId) {
    setLoading(true);
    setStatus('Chargement de l’impact spatial…');
    try {
      const services = await loadSpatialImpactData(assetType, assetId);
      state.payload = {
        services,
        needs: services.needs?.data,
        impact: services.impact?.data,
        explain: services.explain?.data,
        map: services.map?.data,
        statistics: services.statistics?.data,
        decisionCase: services.decisionCase?.data,
      };
      state.services = services;
      renderSpatialImpactWorkspace(services, assetId);
      const summary = summarizeServiceFailures(services);
      setStatus(summary.text, summary.isError);
      console.info('[DXL] loadSpatialImpact terminé', {
        assetType,
        assetId,
        statuses: Object.fromEntries(
          Object.entries(services).map(([k, v]) => [k, { status: v.status, ms: v.ms, error: v.error }]),
        ),
      });
      return services;
    } catch (err) {
      // Ne devrait quasiment jamais arriver (tracedFetch ne throw pas)
      console.error('[DXL] loadSpatialImpact erreur fatale', err);
      setStatus(`Impact spatial — erreur inattendue : ${humanizeFetchError(err)}`, true);
      const summary = document.querySelector('#dxl-section-summary');
      if (summary) {
        summary.innerHTML = softErrorHtml(
          'Espace d’impact spatial indisponible',
          humanizeFetchError(err),
          'Réessayez après vérification de l’API NSME.',
        );
      }
      renderActions();
      return state.services;
    } finally {
      setLoading(false);
    }
  }

  async function loadCoverageDetail(territoryId) {
    setLoading(true);
    setStatus('Chargement du détail de couverture…');
    try {
      const [profileRes, mapRes] = await Promise.all([
        tracedFetch(`/api/territorial-intelligence/territories/${encodeURIComponent(territoryId)}`, 'coverage'),
        tracedFetch(`/api/territorial-intelligence/territories/${encodeURIComponent(territoryId)}/map`, 'map'),
      ]);
      const profile = profileRes.ok ? profileRes.data : null;
      const mapPayload = mapRes.ok ? mapRes.data : null;
      const title = document.querySelector('#dxl-title');
      if (title) title.textContent = `Couverture territoriale — ${profile?.profile?.name || territoryId}`;
      renderExecutiveSummary({
        asset: {
          site_name: profile?.profile?.name || territoryId,
          site_code: territoryId,
          program_code: 'coverage',
          priority_level_label: profile?.sections?.coverage?.priority?.value || '—',
        },
        summary: 'Analyse de couverture et population restante pour le territoire sélectionné.',
        confidence_level: profile?.confidence_level || profile?._meta?.confidence_level,
      }, {});
      if (mapPayload?.features) {
        renderMapFromNsme({
          features: (mapPayload.features || []).map((f) => ({
            ...f,
            properties: { ...(f.properties || {}), kind: f.properties?.kind || 'linked_locality' },
          })),
        });
      } else {
        ensureMap();
      }
      renderContext({}, profile || {});
      renderWhy({ justification: [] });
      const why = document.querySelector('#dxl-section-why');
      if (why) {
        why.innerHTML = `
          <p class="dxl-kicker">Pourquoi cette lecture ?</p>
          <p>La couverture est dérivée du Référentiel National des Besoins et de l’Intelligence territoriale — aucune valeur inventée.</p>
        `;
      }
      renderImpact(profile?.sections?.coverage || {}, null);
      renderRisks({ missing_data: profile?.missing_data || [], risks: [] });
      renderTraceability({ doctrine: { title: 'National Coverage Intelligence', version: 'nci' }, generated_at: profile?._meta?.generated_at });
      renderRecommendation({
        recommendation_text: 'Prioriser les localités non couvertes à population restante élevée.',
        next_action: 'Ouvrir l’Intelligence territoriale pour le même territoire.',
      });
      renderActions();
      setStatus(profile ? 'Détail couverture prêt' : `Couverture partielle — ${profileRes.error || 'sources incomplètes'}`, !profile);
    } catch (err) {
      setStatus(`Couverture indisponible : ${humanizeFetchError(err)}`, true);
    } finally {
      setLoading(false);
    }
  }

  async function loadDecisionCase(assetType, assetId, programCode) {
    setLoading(true);
    setStatus('Chargement du dossier de décision…');
    const qs = programCode
      ? `?asset_type=${encodeURIComponent(assetType === 'site' ? 'site' : assetType)}&program_code=${encodeURIComponent(programCode)}`
      : `?asset_type=${encodeURIComponent(assetType === 'site' ? 'site' : assetType)}`;
    try {
      const [caseRes, impactRes, mapRes] = await Promise.all([
        tracedFetch(`/api/decision/case/${encodeURIComponent(assetId)}${qs}`, 'decisionCase'),
        tracedFetch(`/api/spatial-matching/assets/${encodeURIComponent(assetId)}/impact`, 'impact'),
        tracedFetch(`/api/spatial-matching/map?asset_id=${encodeURIComponent(assetId)}`, 'map'),
      ]);
      const caseFile = caseRes.ok ? caseRes.data : null;
      const nsmeImpact = impactRes.ok ? impactRes.data : null;
      const nsmeMap = mapRes.ok ? mapRes.data : null;
      let ti = null;
      const territoire = caseFile?.asset?.territoire || caseFile?.site?.territoire || caseFile?.asset?.territory_id;
      if (territoire) {
        const tiRes = await tracedFetch(`/api/territorial-intelligence/territories/${encodeURIComponent(territoire)}`, 'coverage');
        ti = tiRes.ok ? tiRes.data : null;
      }
      state.payload = { caseFile, nsmeImpact, nsmeMap, ti };
      const title = document.querySelector('#dxl-title');
      if (title) title.textContent = `Dossier de décision — ${caseFile?.asset?.site_name || caseFile?.asset?.name || assetId}`;
      renderExecutiveSummary(caseFile || {
        asset: { site_code: assetId },
        summary: caseRes.error ? 'Dossier partiel — le moteur de décision n’a pas entièrement répondu.' : 'Dossier en cours de consolidation.',
      }, nsmeImpact?.impact);
      if (nsmeMap) renderMapFromNsme(nsmeMap);
      else ensureMap();
      renderWhy(caseFile || {});
      renderContext(caseFile || {}, ti || {});
      if (nsmeImpact) renderImpact(caseFile?.impacts, nsmeImpact);
      else {
        const host = document.querySelector('#dxl-section-impact');
        if (host) {
          host.innerHTML = softErrorHtml(
            'Impact spatial indisponible',
            impactRes.error || 'Le service d’impact n’a pas répondu.',
            'Le reste du dossier reste consultable.',
          );
        }
      }
      renderRisks(caseFile || {});
      renderTraceability(caseFile || {});
      renderRecommendation(caseFile || {});
      renderActions();
      const failed = [caseRes, impactRes, mapRes].filter((r) => !r.ok).map((r) => r.label);
      setStatus(
        caseFile
          ? (failed.length ? `Dossier partiel — indisponible : ${failed.join(', ')}` : 'Dossier prêt')
          : `Dossier partiel — ${caseRes.error || 'sources indisponibles'}`,
        !caseFile || failed.length > 0,
      );
    } catch (err) {
      setStatus(`Impossible de charger le dossier : ${humanizeFetchError(err)}`, true);
      const summary = document.querySelector('#dxl-section-summary');
      if (summary) summary.innerHTML = softErrorHtml('Dossier indisponible', humanizeFetchError(err));
    } finally {
      setLoading(false);
    }
  }

  function goBack() {
    if (global.history.length > 1) {
      global.history.back();
      return;
    }
    global.location.hash = 'decision-view';
  }

  function bindEvents() {
    const root = document.querySelector('#decision-experience-panel');
    if (!root || root.dataset.bound === 'true') return;
    root.dataset.bound = 'true';

    document.querySelector('#dxl-back-btn')?.addEventListener('click', goBack);

    root.addEventListener('click', (event) => {
      const btn = event.target?.closest?.('[data-dxl-action]');
      if (!btn) return;
      const action = btn.getAttribute('data-dxl-action');
      if (action === 'back') goBack();
      if (action === 'map') {
        global.location.hash = 'map';
        global.setTimeout(() => {
          const checkbox = document.querySelector('input[data-layer="asset_need_matches"]');
          if (checkbox && !checkbox.checked) {
            checkbox.checked = true;
            checkbox.dispatchEvent(new Event('change', { bubbles: true }));
          }
        }, 300);
      }
      if (action === 'ti') {
        const tid = state.payload?.caseFile?.asset?.territoire
          || state.payload?.caseFile?.site?.territoire
          || state.payload?.ti?.profile?.id
          || state.payload?.ti?.territory_id
          || state.payload?.decisionCase?.asset?.territoire;
        global.location.hash = tid
          ? `territorial-intelligence/${encodeURIComponent(tid)}`
          : 'territorial-intelligence';
      }
      if (action === 'explain') document.querySelector('#dxl-section-why')?.scrollIntoView({ behavior: 'smooth' });
      if (action === 'spatial' && state.assetId) {
        global.location.hash = `spatial-impact/${state.assetType || 'site'}/${encodeURIComponent(state.assetId)}`;
      }
      if (action === 'mission') setStatus('Action : préparer une mission — contexte conservé dans le dossier');
      if (action === 'export') setStatus('Export Excel : utilisez l’export du Centre de Décision pour le programme concerné');
      if (action === 'pdf') setStatus('Préparation PDF : fonctionnalité en cours — dossier prêt à être exporté prochainement');
      if (action === 'ppt') setStatus('Préparation PowerPoint : fonctionnalité en cours — structure DXL prête');
      if (action === 'simulate') setStatus('Simulation future : bascule vers l’onglet Simulations du Centre de Décision');
      if (action === 'simulate') global.setTimeout(() => { global.location.hash = 'decision-view'; }, 600);
    });

    global.document.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape') return;
      const panel = document.querySelector('#decision-experience-panel');
      if (panel && !panel.classList.contains('hidden')) goBack();
    });
  }

  function openDecisionCase(assetType, assetId, programCode) {
    const qs = programCode ? `?program_code=${encodeURIComponent(programCode)}` : '';
    global.location.hash = `decision-case/${assetType}/${encodeURIComponent(assetId)}${qs}`;
  }

  function openSpatialImpact(assetType, assetId) {
    global.location.hash = `spatial-impact/${assetType}/${encodeURIComponent(assetId)}`;
  }

  function initializeDecisionExperienceModule() {
    bindEvents();
    state.initialized = true;
    const parsed = parseHash();
    if (!parsed) {
      setStatus('Aucun dossier sélectionné', true);
      setLoading(false);
      return;
    }
    state.mode = parsed.mode;
    state.assetType = parsed.assetType;
    state.assetId = parsed.assetId;
    state.programCode = parsed.programCode;
    const boot = parsed.mode === 'spatial-impact'
      ? loadSpatialImpact(parsed.assetType, parsed.assetId)
      : parsed.mode === 'coverage-detail'
        ? loadCoverageDetail(parsed.assetId)
        : loadDecisionCase(parsed.assetType, parsed.assetId, parsed.programCode);
    Promise.resolve(boot).catch((err) => {
      console.error('[DXL] initialisation module', err);
      setLoading(false);
      setStatus(`Chargement interrompu : ${humanizeFetchError(err)}`, true);
    });
  }

  global.openDecisionCase = openDecisionCase;
  global.openSpatialImpact = openSpatialImpact;
  global.loadSpatialImpact = loadSpatialImpact;
  global.initializeDecisionExperienceModule = initializeDecisionExperienceModule;
  global.decisionExperienceState = state;
})(typeof window !== 'undefined' ? window : globalThis);
