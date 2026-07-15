/**
 * SIG-FDSU — Decision Scenarios Engine (v1.2)
 * UI d’orchestration : catalogue + exécution + rendu métier.
 * Réutilise Edvs / EdvsCharts / UxPremium / DecisionWorkspace / DXL.
 */
(function initDecisionScenarios(global) {
  const API_BASE = `${global.location.protocol}//${global.location.hostname}:8001`;
  const L = (text) => (global.FdsuLabels?.harmonize ? global.FdsuLabels.harmonize(text) : text);

  const state = {
    version: '1.2.0',
    catalog: [],
    activeId: null,
    lastResult: null,
    bound: false,
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

  function parseHash() {
    const hash = (global.location.hash || '').replace(/^#/, '');
    if (!hash.startsWith('decision-scenario')) return null;
    const parts = hash.split('/');
    return parts[1] || null;
  }

  function navigateHash(hash) {
    if (!hash) return;
    global.location.hash = String(hash).replace(/^#/, '');
  }

  function ensureHosts() {
    return {
      catalog: document.querySelector('#decision-scenarios-catalog'),
      result: document.querySelector('#decision-scenarios-result'),
      status: document.querySelector('#decision-scenarios-status'),
    };
  }

  function setStatus(text, isError) {
    const { status } = ensureHosts();
    if (!status) return;
    status.textContent = text;
    status.classList.toggle('is-error', Boolean(isError));
  }

  function renderCatalog(scenarios) {
    const { catalog } = ensureHosts();
    if (!catalog) return;
    state.catalog = scenarios || [];
    if (!state.catalog.length) {
      catalog.innerHTML = global.UxPremium?.stateHtml
        ? global.UxPremium.stateHtml('empty', 'Aucun scénario', 'Vérifier l’API /api/decision/scenarios.')
        : '<p>Aucun scénario.</p>';
      return;
    }
    catalog.innerHTML = state.catalog.map((scenario) => `
      <button type="button" class="ds-scenario-card${state.activeId === scenario.id ? ' is-active' : ''}"
        data-scenario-run="${escapeHtml(scenario.id)}">
        <span class="ds-scenario-code">${escapeHtml(scenario.code || '')}</span>
        <strong>${escapeHtml(L(scenario.title))}</strong>
        <span>${escapeHtml(scenario.question)}</span>
      </button>
    `).join('');
  }

  function renderCharts(charts) {
    if (!charts || !global.EdvsCharts) return '';
    const parts = [];
    if (charts.stacked) parts.push(global.EdvsCharts.stackedBar(charts.stacked));
    if (charts.gauge) parts.push(global.EdvsCharts.gauge(charts.gauge));
    if (charts.waterfall) parts.push(global.EdvsCharts.waterfall(charts.waterfall));
    if (charts.treemap) parts.push(global.EdvsCharts.treemap(charts.treemap));
    if (charts.radar) parts.push(global.EdvsCharts.radar(charts.radar));
    return parts.join('');
  }

  function renderResult(payload) {
    const { result } = ensureHosts();
    if (!result) return;
    state.lastResult = payload;
    if (!payload || payload.error) {
      result.innerHTML = global.UxPremium?.stateHtml
        ? global.UxPremium.stateHtml('error', 'Scénario indisponible', payload?.error || 'Erreur')
        : `<p>${escapeHtml(payload?.error || 'Erreur')}</p>`;
      return;
    }

    const kpis = payload.kpis || [];
    const recos = payload.recommendations || [];
    const links = payload.data_used || [];
    const actions = payload.actions || [];
    const just = payload.justification || {};
    const mapInfo = payload.map || {};

    result.innerHTML = `
      <header class="ds-result-header">
        <p class="panel-label">Scénario ${escapeHtml(payload.scenario?.code || '')}</p>
        <h3>${escapeHtml(L(payload.title || payload.scenario?.title || ''))}</h3>
        <p class="ds-question">${escapeHtml(payload.question || '')}</p>
      </header>

      <section class="ds-block" aria-label="Résumé exécutif">
        <h4>Résumé exécutif</h4>
        <p>${escapeHtml(payload.executive_summary || '')}</p>
      </section>

      <section class="ds-block" aria-label="Indicateurs">
        <h4>Indicateurs</h4>
        <div id="decision-scenarios-kpi-host" class="edvs-kpi-grid"></div>
      </section>

      <section class="ds-block ds-map-block" aria-label="Carte et contexte">
        <h4>Carte &amp; contexte</h4>
        <p>${escapeHtml(mapInfo.hint || mapInfo.label || 'Carte synchronisée via les modules métier.')}</p>
        ${mapInfo.hash ? `<button type="button" class="primary-button" data-ds-hash="${escapeHtml(mapInfo.hash)}" data-ds-tab="${escapeHtml(mapInfo.tab || '')}">Ouvrir la vue cartographique</button>` : ''}
      </section>

      <section class="ds-block" aria-label="Graphiques">
        <h4>Graphiques</h4>
        <div class="ds-charts ux-exec-charts">${renderCharts(payload.charts) || (global.UxPremium?.stateHtml ? global.UxPremium.stateHtml('empty', 'Pas de graphique pour ce contexte', 'Les indicateurs restent disponibles ci-dessus.') : '')}</div>
      </section>

      <section class="ds-block" aria-label="Recommandations">
        <h4>Recommandations</h4>
        <ul class="ds-reco-list">
          ${recos.map((reco) => `
            <li>
              <strong>${escapeHtml(reco.title || '')}</strong>
              <span>${escapeHtml(reco.detail || '')}</span>
              ${reco.hash ? `<button type="button" class="secondary-button" data-ds-hash="${escapeHtml(reco.hash)}">Ouvrir</button>` : ''}
            </li>
          `).join('') || '<li>Aucune recommandation pour ce contexte.</li>'}
        </ul>
      </section>

      <section class="ds-block" aria-label="Justification">
        <h4>Justification détaillée</h4>
        <p><strong>Pourquoi :</strong> ${escapeHtml(just.why || '—')}</p>
        <p><strong>Confiance :</strong> ${escapeHtml(just.confidence || '—')}</p>
        ${just.doctrine ? `<p><strong>Doctrine :</strong> ${escapeHtml(just.doctrine)}</p>` : ''}
        ${just.limitations ? `<p><strong>Limites :</strong> ${escapeHtml(just.limitations)}</p>` : ''}
      </section>

      <section class="ds-block" aria-label="Données utilisées">
        <h4>Données utilisées</h4>
        <ul class="ds-data-links">
          ${links.map((link) => `
            <li>
              <span>${escapeHtml(link.label || '')}</span>
              <code>${escapeHtml(link.href || '')}</code>
            </li>
          `).join('')}
        </ul>
      </section>

      <section class="ds-block ds-actions" aria-label="Actions">
        <h4>Actions possibles</h4>
        <div class="ds-action-row">
          ${actions.map((action) => `
            <button type="button" class="primary-button" data-ds-action="${escapeHtml(action.id || '')}" data-ds-hash="${escapeHtml(action.hash || '')}">
              ${escapeHtml(L(action.label || action.id || 'Action'))}
            </button>
          `).join('')}
        </div>
      </section>
    `;

    if (global.Edvs?.mountKpiStrip && kpis.length) {
      global.Edvs.mountKpiStrip('#decision-scenarios-kpi-host', kpis.map((kpi) => ({
        label: kpi.label,
        value: kpi.value,
        color: kpi.color || 'blue',
        note: kpi.note,
        confidence: 'medium',
        icon: 'decision',
      })));
      if (global.UxPremium?.bindEdvsKpiClicks) global.UxPremium.bindEdvsKpiClicks(result);
    }

    if (global.DecisionWorkspace?.attach && payload.scenario?.id) {
      global.DecisionWorkspace.attach({
        kpiCode: payload.scenario.id,
        returnHash: 'decision-view',
        syncMessage: `Scénario ${payload.scenario.code} — synchronisé`,
      });
    }
  }

  function runScenario(scenarioId, context = {}) {
    state.activeId = scenarioId;
    renderCatalog(state.catalog);
    setStatus('Exécution du scénario…');
    const params = new URLSearchParams();
    Object.entries(context).forEach(([key, value]) => {
      if (value != null && value !== '') params.set(key, value);
    });
    const qs = params.toString() ? `?${params}` : '';
    return fetchJson(`/api/decision/scenarios/${encodeURIComponent(scenarioId)}/run${qs}`)
      .then((payload) => {
        renderResult(payload);
        setStatus(`${payload.title || scenarioId} — prêt`);
        // Conserver le hash scénario sans casser les routes existantes
        const desired = `decision-scenario/${scenarioId}`;
        if ((global.location.hash || '').replace(/^#/, '').split('?')[0] !== desired) {
          global.history.replaceState(null, '', `#${desired}`);
        }
        return payload;
      })
      .catch((err) => {
        setStatus(`Erreur : ${err.message}`, true);
        renderResult({ error: err.message });
      });
  }

  function loadCatalog() {
    setStatus('Chargement des scénarios…');
    return fetchJson('/api/decision/scenarios')
      .then((payload) => {
        renderCatalog(payload.scenarios || []);
        setStatus(`${(payload.scenarios || []).length} scénarios disponibles`);
        const fromHash = parseHash();
        if (fromHash) runScenario(fromHash);
        return payload;
      })
      .catch((err) => {
        setStatus(`Catalogue indisponible : ${err.message}`, true);
        renderCatalog([]);
      });
  }

  function handleAction(hash, tab) {
    if (tab && typeof global.setDecisionCenterTab === 'function') {
      navigateHash('decision-view');
      global.setTimeout(() => global.setDecisionCenterTab(tab), 50);
      return;
    }
    if (!hash) return;
    if (hash.startsWith('decision-case/') && typeof global.openDecisionCase === 'function') {
      const parts = hash.split('?')[0].split('/');
      const program = new URLSearchParams(hash.split('?')[1] || '').get('program_code');
      global.openDecisionCase(parts[1] || 'site', parts[2], program || undefined);
      return;
    }
    navigateHash(hash);
  }

  function bindEvents() {
    if (state.bound) return;
    const root = document.querySelector('#decision-scenarios-root') || document.querySelector('[data-decision-tab-panel="simulations"]');
    if (!root) return;
    state.bound = true;
    root.addEventListener('click', (event) => {
      const target = event.target;
      if (!(target instanceof global.HTMLElement)) return;
      const runBtn = target.closest('[data-scenario-run]');
      if (runBtn) {
        runScenario(runBtn.getAttribute('data-scenario-run'));
        return;
      }
      const hashBtn = target.closest('[data-ds-hash]');
      if (hashBtn) {
        handleAction(hashBtn.getAttribute('data-ds-hash'), hashBtn.getAttribute('data-ds-tab'));
      }
    });
  }

  function openScenario(scenarioId, context) {
    if (typeof global.setDecisionCenterTab === 'function') {
      navigateHash('decision-view');
      global.setTimeout(() => {
        global.setDecisionCenterTab('simulations');
        runScenario(scenarioId, context || {});
      }, 80);
      return;
    }
    navigateHash(`decision-scenario/${scenarioId}`);
    runScenario(scenarioId, context || {});
  }

  function initializeDecisionScenariosModule() {
    bindEvents();
    loadCatalog();
  }

  global.DecisionScenarios = {
    version: state.version,
    state,
    loadCatalog,
    runScenario,
    openScenario,
    parseHash,
    initializeDecisionScenariosModule,
  };
  global.openDecisionScenario = openScenario;
  global.initializeDecisionScenariosModule = initializeDecisionScenariosModule;
})(typeof window !== 'undefined' ? window : globalThis);
