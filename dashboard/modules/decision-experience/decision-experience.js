/**
 * Decision Experience Layer (DXL)
 * Transforme les payloads API (Decision / NSME / TI) en dossiers métier dashboard.
 * Routes : #decision-case/<type>/<id> · #spatial-impact/<type>/<id>
 * Jamais d'ouverture /api/ pour l'utilisateur métier.
 */
(function initDecisionExperienceLayer(global) {
  const API_BASE = `${global.location.protocol}//${global.location.hostname}:8001`;

  const state = {
    initialized: false,
    mode: null, // decision-case | spatial-impact
    assetType: null,
    assetId: null,
    programCode: null,
    payload: null,
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

  async function fetchJson(path) {
    const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
    const response = await fetch(url, { headers: { Accept: 'application/json' }, cache: 'no-store' });
    if (!response.ok) throw new Error(`Données indisponibles (${response.status})`);
    return response.json();
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
              // rester dans le dossier
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

  async function loadCoverageDetail(territoryId) {
    setLoading(true);
    setStatus('Chargement du détail de couverture…');
    try {
      const [profile, mapPayload] = await Promise.all([
        fetchJson(`/api/territorial-intelligence/territories/${encodeURIComponent(territoryId)}`).catch(() => null),
        fetchJson(`/api/territorial-intelligence/territories/${encodeURIComponent(territoryId)}/map`).catch(() => null),
      ]);
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
      // carte TI via features NSME-like si disponibles
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
      setStatus(profile ? 'Détail couverture prêt' : 'Données de couverture partielles', !profile);
    } catch (err) {
      setStatus(`Couverture indisponible : ${err.message}`, true);
    } finally {
      setLoading(false);
    }
  }

  async function loadDecisionCase(assetType, assetId, programCode) {
    setLoading(true);
    setStatus('Chargement du dossier de décision…');
    const qs = programCode ? `?asset_type=${encodeURIComponent(assetType === 'site' ? 'site' : assetType)}&program_code=${encodeURIComponent(programCode)}` : `?asset_type=${encodeURIComponent(assetType === 'site' ? 'site' : assetType)}`;
    try {
      const [caseFile, nsmeImpact, nsmeMap] = await Promise.all([
        fetchJson(`/api/decision/case/${encodeURIComponent(assetId)}${qs}`).catch(() => null),
        fetchJson(`/api/spatial-matching/assets/${encodeURIComponent(assetId)}/impact`).catch(() => null),
        fetchJson(`/api/spatial-matching/map?asset_id=${encodeURIComponent(assetId)}`).catch(() => null),
      ]);
      let ti = null;
      const territoire = caseFile?.asset?.territoire || caseFile?.site?.territoire || caseFile?.asset?.territory_id;
      if (territoire) {
        ti = await fetchJson(`/api/territorial-intelligence/territories/${encodeURIComponent(territoire)}`).catch(() => null);
      }
      state.payload = { caseFile, nsmeImpact, nsmeMap, ti };
      const title = document.querySelector('#dxl-title');
      if (title) title.textContent = `Dossier de décision — ${caseFile?.asset?.site_name || caseFile?.asset?.name || assetId}`;
      renderExecutiveSummary(caseFile || {}, nsmeImpact?.impact);
      renderMapFromNsme(nsmeMap);
      renderWhy(caseFile || {});
      renderContext(caseFile || {}, ti || {});
      renderImpact(caseFile?.impacts, nsmeImpact);
      renderRisks(caseFile || {});
      renderTraceability(caseFile || {});
      renderRecommendation(caseFile || {});
      renderActions();
      setStatus(caseFile ? 'Dossier prêt' : 'Dossier partiel — certaines sources indisponibles', !caseFile);
    } catch (err) {
      setStatus(`Impossible de charger le dossier : ${err.message}`, true);
      const summary = document.querySelector('#dxl-section-summary');
      if (summary) summary.innerHTML = `<p class="dxl-empty is-error">${escapeHtml(err.message)}</p>`;
    } finally {
      setLoading(false);
    }
  }

  async function loadSpatialImpact(assetType, assetId) {
    setLoading(true);
    setStatus('Chargement de l’impact spatial…');
    try {
      const [needs, impact, explain, mapPayload] = await Promise.all([
        fetchJson(`/api/spatial-matching/assets/${encodeURIComponent(assetId)}/needs?limit=100`),
        fetchJson(`/api/spatial-matching/assets/${encodeURIComponent(assetId)}/impact`),
        fetchJson(`/api/spatial-matching/assets/${encodeURIComponent(assetId)}/explain`),
        fetchJson(`/api/spatial-matching/map?asset_id=${encodeURIComponent(assetId)}`),
      ]);
      const title = document.querySelector('#dxl-title');
      if (title) title.textContent = `Impact spatial — actif ${assetId}`;
      renderExecutiveSummary({
        asset: { site_code: assetId, site_name: needs?.asset?.site_name || assetId, program_code: needs?.asset?.program_code },
        summary: explain?.summary,
        confidence_level: explain?.confidence_level,
      }, impact?.impact);
      renderMapFromNsme(mapPayload);
      const why = document.querySelector('#dxl-section-why');
      if (why) {
        why.innerHTML = `
          <p class="dxl-kicker">Explication de la correspondance</p>
          <p>${escapeHtml(explain?.summary || '—')}</p>
          <p>Distance : ${escapeHtml(explain?.distance_m ?? '—')} m · Rayon : ${escapeHtml(explain?.service_radius_m ?? '—')} m</p>
          <p>Règle spatiale : ${escapeHtml(explain?.spatial_rule || '—')} · Méthode : ${escapeHtml(explain?.calculation_method || '—')}</p>
        `;
      }
      renderImpact({}, impact);
      renderRisks({ missing_data: explain?.missing_data || [], risks: [] });
      renderTraceability({
        doctrine: { title: 'National Spatial Matching Engine', version: 'nsme-1.0.0' },
        generated_at: impact?._meta?.generated_at,
      });
      renderRecommendation({
        recommendation_text: explain?.summary,
        next_action: 'Préparer une mission sur les localités à priorité élevée les plus proches.',
      });
      renderActions();
      const ctx = document.querySelector('#dxl-section-context');
      if (ctx) {
        const matches = (needs?.matches || []).filter((m) => m.relation_type === 'SERVES_LOCALITY').slice(0, 8);
        ctx.innerHTML = `
          <p class="dxl-kicker">Besoins associés</p>
          <ul>${matches.map((m) => `<li>${escapeHtml((m.properties || {}).locality_name || m.need_id)} — ${escapeHtml(m.distance_m != null ? `${Math.round(m.distance_m)} m` : '—')} — pop. ${escapeHtml(formatNumber(m.population_impacted))}</li>`).join('') || '<li>Aucun besoin apparié dans le rayon configurable.</li>'}</ul>
        `;
      }
      setStatus(`${needs?.match_count || 0} correspondance(s) — prêt`);
    } catch (err) {
      setStatus(`Impact spatial indisponible : ${err.message}`, true);
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
          || state.payload?.ti?.territory_id;
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
      return;
    }
    state.mode = parsed.mode;
    state.assetType = parsed.assetType;
    state.assetId = parsed.assetId;
    state.programCode = parsed.programCode;
    if (parsed.mode === 'spatial-impact') {
      loadSpatialImpact(parsed.assetType, parsed.assetId);
    } else if (parsed.mode === 'coverage-detail') {
      loadCoverageDetail(parsed.assetId);
    } else {
      loadDecisionCase(parsed.assetType, parsed.assetId, parsed.programCode);
    }
  }

  global.openDecisionCase = openDecisionCase;
  global.openSpatialImpact = openSpatialImpact;
  global.initializeDecisionExperienceModule = initializeDecisionExperienceModule;
  global.decisionExperienceState = state;
})(typeof window !== 'undefined' ? window : globalThis);
