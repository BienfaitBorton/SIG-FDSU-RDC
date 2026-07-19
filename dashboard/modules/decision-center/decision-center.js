(function initDecisionCenterModule(global) {
  const BUSINESS_DATA_BASE = '/business/';
  const PROGRAMS_DATA_BASE = '/programs/';
  const FDSU_PROGRAMS_PATH = `${BUSINESS_DATA_BASE}fdsu_programs.json`;
  const SITES_40_DATA_PATH = `${PROGRAMS_DATA_BASE}sites_40/sites_40.json`;

  const DECISION_CENTER_TABS = [
    { id: 'vue-nationale', label: 'Vue nationale' },
    { id: 'priorisation', label: 'Priorisation' },
    { id: 'referentiels-sectoriels', label: 'Référentiels sectoriels' },
    { id: 'analyse-multicritere', label: 'Analyse multicritère' },
    { id: 'simulations', label: 'Simulations' },
    { id: 'tableaux-de-bord', label: 'Tableaux de bord' },
    { id: 'rapports', label: 'Rapports' },
  ];

  const NATIONAL_PANEL_PENDING_MESSAGE = "Données en cours d'intégration";

  const NATIONAL_SYNTHESIS_KPI_BINDINGS = [
    { key: 'sites_fdsu', elementId: 'decision-kpi-sites-fdsu', synthesisKey: 'sites_fdsu' },
    { key: 'sites_priority', elementId: 'decision-kpi-sites-priority', synthesisKey: 'sites_priority' },
    { key: 'sites_critical', elementId: 'decision-kpi-sites-critical', synthesisKey: 'sites_critical' },
    { key: 'sites_high', elementId: 'decision-kpi-sites-high', synthesisKey: 'sites_high' },
    { key: 'referentials_active', elementId: 'decision-kpi-referentials-active', synthesisKey: 'referentials_active' },
    { key: 'referentials_planned', elementId: 'decision-kpi-referentials-planned', synthesisKey: 'referentials_planned' },
  ];

  const NATIONAL_OPERATIONAL_KPI_BINDINGS = [
    { key: 'sites_40', elementId: 'decision-kpi-sites-40' },
    { key: 'sites_300', elementId: 'decision-kpi-sites-300' },
    { key: 'sites_scored', elementId: 'decision-kpi-sites-scored' },
    { key: 'health_facilities', elementId: 'decision-kpi-health-facilities' },
    { key: 'referentials_in_progress', elementId: 'decision-kpi-referentials-in-progress' },
    { key: 'telecom_objects', elementId: 'decision-kpi-telecom-objects' },
    { key: 'provinces', elementId: 'decision-kpi-provinces' },
    { key: 'territoires', elementId: 'decision-kpi-territoires' },
  ];

  const NATIONAL_PENDING_KPI_BINDINGS = [
    { key: 'population_covered', elementId: 'decision-kpi-covered-population' },
    { key: 'population_uncovered', elementId: 'decision-kpi-uncovered-population' },
    { key: 'planned_ccn', elementId: 'decision-kpi-planned-ccn' },
    { key: 'estimated_investment', elementId: 'decision-kpi-investment' },
  ];

  const NOT_CALCULATED_MESSAGE = 'Donnée non encore calculée — nécessite référentiel Population / CCN / Budget.';
  const STATUS_TO_FILL_MESSAGE = 'Statuts opérationnels à renseigner';

  const decisionCenterState = {
    initialized: false,
    activeTab: 'vue-nationale',
    map: null,
    layers: {},
    mapInitialized: false,
    resizeObserver: null,
    nationalPanelLoaded: false,
    nationalPanelLoading: false,
    explainKpis: {},
    intentsLoaded: false,
    followupLoaded: false,
    demoScenarios: [],
    demoActiveScenarioId: null,
    demoVisible: false,
    businessPanelsLoading: false,
    businessPanelsPromise: null,
    programsLoaded: false,
    programsLoading: false,
    sites40Loaded: false,
    sites40Loading: false,
    sites300Loaded: false,
    sites300Loading: false,
    telecomLoaded: false,
    telecomLoading: false,
    telecomLoadingPromise: null,
    spatialLoaded: false,
    spatialLoading: false,
    spatialLoadingPromise: null,
    decisionEngineLoaded: false,
    decisionEngineLoading: false,
    decisionEngineFilter: '',
    decisionEngineProgram: 'sites_20476',
    decisionEngineSites: [],
    decisionEngineMap: null,
    decisionEngineMarkers: null,
    decisionEngineSelectedSiteId: null,
    masterRegistryLoaded: false,
    masterRegistryLoading: false,
    ccnExtensionsLoaded: false,
    sectorialLoaded: false,
    sectorialLoading: false,
    healthMap: null,
    healthFacilitiesLayer: null,
    healthGeojson: null,
    programStatusCatalog: null,
    priorityMatrixLoader: null,
  };

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatNationalKpiNumber(value) {
    if (value == null || Number.isNaN(Number(value))) {
      return NATIONAL_PANEL_PENDING_MESSAGE;
    }
    return Number(value).toLocaleString('fr-FR');
  }

  function setNationalKpiElement(elementId, displayValue, isPending) {
    const element = document.getElementById(elementId);
    if (!element) return;
    element.textContent = displayValue;
    element.classList.toggle('is-pending-value', Boolean(isPending));
    const card = element.closest('.decision-center-kpi-card');
    if (card) {
      card.classList.toggle('is-pending', Boolean(isPending));
    }
  }

  function resolveKpiDisplay(kpi) {
    if (!kpi || kpi.available === false || kpi.value == null) {
      return {
        text: kpi?.display || kpi?.limitations || NOT_CALCULATED_MESSAGE || NATIONAL_PANEL_PENDING_MESSAGE,
        pending: true,
      };
    }
    return {
      text: formatNationalKpiNumber(kpi.value),
      pending: false,
    };
  }

  function applyExplainableKpiCard(key, kpi) {
    const card = document.querySelector(`.decision-explainable-kpi[data-kpi-key="${key}"]`);
    if (!card || !kpi) return;
    const definition = card.querySelector('[data-kpi-field="definition"]');
    const source = card.querySelector('[data-kpi-field="source"]');
    const calculation = card.querySelector('[data-kpi-field="calculation"]');
    const updated = card.querySelector('[data-kpi-field="updated"]');
    const confidence = card.querySelector('[data-kpi-field="confidence"]');
    if (definition && kpi.definition) definition.textContent = kpi.definition;
    // Affichage exécutif : source métier lisible (pas de table SQL)
    if (source) source.textContent = kpi.source_label || kpi.source_readable || source.textContent || 'Source FDSU';
    if (calculation && kpi.calculation_method) {
      calculation.textContent = kpi.calculation_method;
      const tech = card.querySelector('[data-kpi-tech="true"]');
      if (tech) tech.hidden = true; // technique masquée par défaut pour le DG
    }
    if (confidence) {
      confidence.textContent = `Confiance : ${kpi.confidence || 'moyenne'}`;
    }
    if (updated) {
      const stamp = kpi.last_updated ? String(kpi.last_updated).slice(0, 19).replace('T', ' ') : '—';
      updated.textContent = `Mise à jour : ${stamp}`;
    }
    card.classList.toggle('is-pending', kpi.available === false);
  }

  function renderNationalPanelKpis(payload, explainPayload) {
    const kpis = payload?.kpis || {};
    const synthesis = payload?.synthesis || {};
    const explained = explainPayload?.kpis || decisionCenterState.explainKpis || {};
    decisionCenterState.explainKpis = explained;

    NATIONAL_SYNTHESIS_KPI_BINDINGS.forEach((binding) => {
      const explainedKpi = explained[binding.key];
      if (explainedKpi) {
        const resolved = resolveKpiDisplay(explainedKpi);
        setNationalKpiElement(binding.elementId, resolved.text, resolved.pending);
        applyExplainableKpiCard(binding.key, explainedKpi);
        return;
      }
      const fromSynthesis = synthesis[binding.synthesisKey];
      if (fromSynthesis != null) {
        setNationalKpiElement(binding.elementId, formatNationalKpiNumber(fromSynthesis), false);
        return;
      }
      const resolved = resolveKpiDisplay(kpis[binding.key]);
      setNationalKpiElement(binding.elementId, resolved.text, resolved.pending);
    });

    NATIONAL_OPERATIONAL_KPI_BINDINGS.forEach((binding) => {
      const explainedKpi = explained[binding.key] || kpis[binding.key];
      const resolved = resolveKpiDisplay(explainedKpi);
      setNationalKpiElement(binding.elementId, resolved.text, resolved.pending);
      if (explained[binding.key]) applyExplainableKpiCard(binding.key, explained[binding.key]);
    });

    NATIONAL_PENDING_KPI_BINDINGS.forEach((binding) => {
      const explainedKpi = explained[binding.key] || kpis[binding.key];
      const resolved = resolveKpiDisplay(explainedKpi);
      setNationalKpiElement(binding.elementId, resolved.text || NOT_CALCULATED_MESSAGE, true);
      if (explained[binding.key]) applyExplainableKpiCard(binding.key, explained[binding.key]);
    });

    if (global.Edvs?.mountKpiStrip) {
      const pick = (key) => {
        const item = explained[key] || kpis[key];
        if (item && typeof item === 'object' && 'value' in item) return item.value;
        if (typeof item === 'number') return item;
        return synthesis[key] ?? null;
      };
      global.Edvs.mountKpiStrip('#decision-edvs-kpi-host', [
        { label: 'Sites FDSU', value: pick('sites_fdsu_total') ?? synthesis.sites_fdsu, icon: 'sites', color: 'blue', confidence: 'high', detailKey: 'sites_fdsu' },
        { label: 'Sites prioritaires', value: pick('sites_priority') ?? synthesis.sites_priority, icon: 'decision', color: 'orange', confidence: 'medium', detailKey: 'sites_priority' },
        { label: 'Sites critiques', value: pick('sites_critical') ?? synthesis.sites_critical, icon: 'alert', color: 'red', confidence: 'medium', detailKey: 'sites_critical' },
        { label: 'Référentiels actifs', value: pick('referentials_active') ?? synthesis.referentials_active, icon: 'data', color: 'green', confidence: 'high', detailKey: 'referentials_active' },
      ]);
      if (global.UxPremium?.bindInteractiveKpis) global.UxPremium.bindInteractiveKpis(document);
      if (global.UxPremium?.bindEdvsKpiClicks) global.UxPremium.bindEdvsKpiClicks(document);
    }

    renderNationalExecutiveCharts(payload, explainPayload);
  }

  function renderNationalExecutiveCharts(payload) {
    const host = document.querySelector('#decision-edvs-charts-host');
    if (!host || !global.EdvsCharts) return;
    const synthesis = payload?.synthesis || {};
    const total = Number(synthesis.sites_fdsu) || 0;
    const priority = Number(synthesis.sites_priority) || 0;
    const critical = Number(synthesis.sites_critical) || 0;
    const high = Number(synthesis.sites_high) || 0;
    const other = Math.max(0, total - priority - critical - high);
    if (!total && !priority && !critical) {
      host.innerHTML = global.UxPremium?.stateHtml
        ? global.UxPremium.stateHtml('empty', 'Graphiques en attente', 'Les indicateurs nationaux se chargeront dès que la synthèse sera disponible.')
        : '';
      return;
    }
    const share = total ? Math.round((priority / total) * 100) : 0;
    host.innerHTML = [
      global.EdvsCharts.treemap({
        title: 'Portefeuille sites FDSU',
        items: [
          { label: 'Prioritaires', value: priority, color: 'orange' },
          { label: 'Critiques', value: critical, color: 'red' },
          { label: 'Élevés', value: high, color: 'yellow' },
          { label: 'Autres', value: other, color: 'blue' },
        ].filter((item) => Number(item.value) > 0),
      }),
      global.EdvsCharts.gauge({
        title: 'Part prioritaire',
        value: share,
        subtitle: 'Sites prioritaires / total FDSU',
        color: share >= 40 ? 'orange' : 'blue',
      }),
    ].join('');
  }

  function renderNationalPanelUnavailable(message) {
    const pendingMessage = message || NATIONAL_PANEL_PENDING_MESSAGE;
    [...NATIONAL_SYNTHESIS_KPI_BINDINGS, ...NATIONAL_OPERATIONAL_KPI_BINDINGS].forEach((binding) => {
      setNationalKpiElement(binding.elementId, pendingMessage, true);
    });
    NATIONAL_PENDING_KPI_BINDINGS.forEach((binding) => {
      setNationalKpiElement(binding.elementId, NOT_CALCULATED_MESSAGE, true);
    });
  }

  function openKpiDetail(kpiKey) {
    // Feedback immédiat + navigation vers Analyse détaillée
    const btn = document.querySelector(`[data-kpi-detail="${kpiKey}"]`);
    if (btn) {
      btn.classList.add('is-loading');
      window.setTimeout(() => btn.classList.remove('is-loading'), 400);
    }
    // Fermer immédiatement le drawer legacy pour éviter tout voile résiduel
    closeKpiDetail();
    // KPI territoriaux : ouvrir le jumeau si une sélection TST existe
    const territorialKpis = new Set(['provinces', 'territoires', 'population_covered', 'population_uncovered']);
    if (territorialKpis.has(kpiKey) && global.TerritorialDigitalTwin?.open) {
      const sel = global.TerritorialContext?.get()?.selection;
      const level = sel?.level || sel?.entity_type;
      const id = sel?.id || sel?.entity_id || sel?.name;
      if ((level === 'province' || level === 'territoire') && id) {
        global.TerritorialDigitalTwin.open({
          entityType: level,
          entityId: id,
          returnHash: 'decision-view',
        });
        return;
      }
    }
    // Santé : ouvrir l'analyse détaillée (carte + liste + graphiques)
    if (typeof global.openDecisionDetail === 'function') {
      global.openDecisionDetail(kpiKey);
      return;
    }
    // Fallback drawer si le module détail n'est pas chargé
    const drawer = document.querySelector('#decision-kpi-detail-drawer');
    const title = document.querySelector('#decision-kpi-detail-title');
    const body = document.querySelector('#decision-kpi-detail-body');
    const kpi = decisionCenterState.explainKpis?.[kpiKey];
    if (!drawer || !body) return;
    if (!kpi) {
      body.innerHTML = `<p>${escapeHtml(NATIONAL_PANEL_PENDING_MESSAGE)}</p>`;
    } else {
      if (title) title.textContent = kpi.label || kpiKey;
      body.innerHTML = `
        <p><strong>Valeur :</strong> ${escapeHtml(kpi.available === false ? (kpi.display || NOT_CALCULATED_MESSAGE) : formatNationalKpiNumber(kpi.value))}</p>
        <p><strong>Définition :</strong> ${escapeHtml(kpi.definition || '—')}</p>
        <p><strong>Source :</strong> ${escapeHtml(kpi.source_label || kpi.source_table || '—')}</p>
        <p><strong>Mise à jour :</strong> ${escapeHtml(kpi.last_updated || '—')}</p>
        <p><strong>Confiance :</strong> ${escapeHtml(kpi.confidence || '—')}</p>
        <p><strong>Action recommandée :</strong> ${escapeHtml(kpi.recommended_action || '—')}</p>
        <p class="kpi-meta-tech"><strong>Technique :</strong> ${escapeHtml(kpi.calculation_method || '—')}</p>
      `;
    }
    drawer.hidden = false;
    drawer.removeAttribute('hidden');
  }

  function closeKpiDetail() {
    const drawer = document.querySelector('#decision-kpi-detail-drawer');
    if (!drawer) return;
    drawer.hidden = true;
    drawer.setAttribute('hidden', '');
  }

  function renderDecisionIntents(payload) {
    const grid = document.querySelector('#decision-intent-grid');
    if (!grid) return;
    const intents = asArray(payload?.intents);
    if (!intents.length) {
      grid.innerHTML = '<p class="decision-center-program-note">Questions métier indisponibles.</p>';
      return;
    }
    grid.innerHTML = intents.map((intent) => `
      <button type="button" class="decision-intent-card" data-intent-id="${escapeHtml(intent.id)}" data-target-tab="${escapeHtml(intent.target_tab || 'vue-nationale')}" data-scenario-id="${escapeHtml(intent.scenario_id || '')}">
        <h4>${escapeHtml(intent.title)}</h4>
        <p>${escapeHtml(intent.explanation || '')}</p>
        <p class="intent-data">Données : ${escapeHtml(asArray(intent.data_used).slice(0, 2).join(' · ') || '—')}</p>
        <span class="intent-action">${escapeHtml(intent.primary_action || 'Analyser')}</span>
      </button>
    `).join('');
  }

  function renderFollowupCard(containerId, programPayload, metricOrder) {
    const card = document.querySelector(containerId);
    if (!card) return;
    const metrics = programPayload?.metrics || {};
    const rows = metricOrder.map(([key, label]) => {
      const value = metrics[key];
      const display = value == null
        ? (programPayload?.metrics_status || programPayload?.display || STATUS_TO_FILL_MESSAGE)
        : formatNationalKpiNumber(value);
      return `<li><span>${escapeHtml(label)}</span><strong>${escapeHtml(display)}</strong></li>`;
    }).join('');
    const note = programPayload?.status_message || programPayload?.metrics_status || programPayload?.display;
    card.innerHTML = `
      <h4>${escapeHtml(programPayload?.program_name || programPayload?.label || 'Programme')}</h4>
      <ul class="decision-followup-metrics">${rows}</ul>
      ${note ? `<p class="decision-followup-note">${escapeHtml(note)}</p>` : ''}
    `;
  }

  function renderProgramFollowup(payload) {
    renderFollowupCard('#decision-followup-sites-40', payload?.sites_40, [
      ['total_sites', 'Total sites'],
      ['installes', 'Installés'],
      ['en_cours_installation', "En cours d'installation"],
      ['operationnels', 'Opérationnels'],
      ['non_demarres', 'Non démarrés'],
      ['bloques', 'Bloqués'],
      ['taux_avancement', "Taux d'avancement"],
    ]);
    renderFollowupCard('#decision-followup-sites-300', payload?.sites_300, [
      ['total', 'Total'],
      ['planifies', 'Planifiés'],
      ['priorises', 'Priorisés'],
      ['en_etude', 'En étude'],
      ['prets_a_deployer', 'Prêts à déployer'],
      ['bloques', 'Bloqués'],
      ['taux_preparation', 'Taux de préparation'],
    ]);
    renderFollowupCard('#decision-followup-ccn', {
      ...(payload?.ccn || {}),
      program_name: 'CCN',
      metrics: {
        ccn_planifies: null,
        ccn_installes: null,
        ccn_operationnels: null,
      },
      metrics_status: payload?.ccn?.display || NOT_CALCULATED_MESSAGE,
    }, [
      ['ccn_planifies', 'CCN planifiés'],
      ['ccn_installes', 'CCN installés'],
      ['ccn_operationnels', 'CCN opérationnels'],
    ]);
  }

  function renderDemoScenario(scenario) {
    const body = document.querySelector('#decision-demo-scenario-body');
    if (!body || !scenario) return;
    const actions = asArray(scenario.actions).map((action) => `
      <button type="button" class="secondary-button decision-demo-action" data-target-tab="${escapeHtml(action.target_tab || '')}" data-demo-action="${escapeHtml(action.action || '')}">
        ${escapeHtml(action.label || 'Action')}
      </button>
    `).join('');
    const kpiEntries = Object.entries(scenario.kpis || {}).slice(0, 4);
    let tableRows = kpiEntries.map(([key, kpi]) => {
      const value = kpi?.available === false
        ? (kpi.display || NOT_CALCULATED_MESSAGE)
        : formatNationalKpiNumber(kpi?.value);
      return `<tr><td>${escapeHtml(kpi?.label || key)}</td><td>${escapeHtml(value)}</td><td>${escapeHtml(kpi?.source_table || '—')}</td></tr>`;
    }).join('');
    if (!tableRows && scenario.followup) {
      const followupRows = [
        ['Sites 40 — total', scenario.followup?.sites_40?.metrics?.total_sites, scenario.followup?.sites_40?.source_table],
        ['Sites 40 — statuts', scenario.followup?.sites_40?.status_message || STATUS_TO_FILL_MESSAGE, scenario.followup?.sites_40?.source_table],
        ['Sites 300 — total', scenario.followup?.sites_300?.metrics?.total, scenario.followup?.sites_300?.source_table],
        ['CCN', scenario.followup?.ccn?.display || NOT_CALCULATED_MESSAGE, scenario.followup?.ccn?.source_table],
      ];
      tableRows = followupRows.map(([label, value, source]) => `
        <tr><td>${escapeHtml(label)}</td><td>${escapeHtml(value == null ? STATUS_TO_FILL_MESSAGE : String(value))}</td><td>${escapeHtml(source || '—')}</td></tr>
      `).join('');
    }
    const mapLabel = scenario.map_focus === 'priorisation'
      ? 'Carte priorisation (sites critiques / élevés)'
      : scenario.map_focus === 'referentiels-sectoriels'
        ? 'Carte Santé + sites FDSU'
        : 'Carte nationale / suivi programmes';
    body.innerHTML = `
      <h4>${escapeHtml(scenario.title)}</h4>
      <p><strong>Question métier :</strong> ${escapeHtml(scenario.business_question || '')}</p>
      <p><strong>Réponse synthétique :</strong> ${escapeHtml(scenario.synthetic_answer || '')}</p>
      <p><strong>Données utilisées :</strong> ${escapeHtml(asArray(scenario.data_used).join(' · '))}</p>
      <p><strong>Carte :</strong> ${escapeHtml(mapLabel)}</p>
      <div class="decision-demo-table-wrap">
        <table class="decision-demo-table">
          <thead><tr><th>Indicateur</th><th>Valeur</th><th>Source</th></tr></thead>
          <tbody>${tableRows || '<tr><td colspan="3">Tableau de suivi programmes (voir section opérationnelle)</td></tr>'}</tbody>
        </table>
      </div>
      <p><strong>Recommandation :</strong> ${escapeHtml(scenario.recommendation || '')}</p>
      <p><strong>Limites :</strong> ${escapeHtml(scenario.limitations || 'Aucune')}</p>
      <div class="decision-demo-actions">${actions}</div>
    `;
  }

  function renderDemoScenarios(payload) {
    const nav = document.querySelector('#decision-demo-scenario-nav');
    const scenarios = asArray(payload?.scenarios);
    decisionCenterState.demoScenarios = scenarios;
    if (!nav) return;
    if (!scenarios.length) {
      nav.innerHTML = '';
      document.querySelector('#decision-demo-scenario-body').innerHTML = '<p>Aucun scénario disponible.</p>';
      return;
    }
    nav.innerHTML = scenarios.map((scenario, index) => `
      <button type="button" class="decision-demo-scenario-btn ${index === 0 ? 'is-active' : ''}" data-scenario-id="${escapeHtml(scenario.id)}">
        ${escapeHtml(scenario.title)}
      </button>
    `).join('');
    decisionCenterState.demoActiveScenarioId = scenarios[0].id;
    renderDemoScenario(scenarios[0]);
  }

  function setDemoModeVisible(visible) {
    const panel = document.querySelector('#decision-demo-panel');
    if (!panel) return;
    decisionCenterState.demoVisible = Boolean(visible);
    panel.hidden = !visible;
    if (visible) panel.removeAttribute('hidden');
    else panel.setAttribute('hidden', '');
  }

  function loadDecisionBusinessPanels(forceReload) {
    const shared = getShared();
    const canUseDb = typeof shared.canUseProgramDbData === 'function' && shared.canUseProgramDbData();
    if (!canUseDb) {
      renderDecisionIntents({ intents: [] });
      return Promise.resolve();
    }
    if (decisionCenterState.businessPanelsLoading) {
      return decisionCenterState.businessPanelsPromise || Promise.resolve();
    }
    if (decisionCenterState.intentsLoaded && decisionCenterState.demoScenarios.length && decisionCenterState.followupLoaded && !forceReload) {
      return Promise.resolve();
    }

    const fetchJson = shared.fetchJson.bind(shared);
    decisionCenterState.businessPanelsLoading = true;

    // Chargement progressif : intents (léger) d'abord, puis followup / demos / health
    decisionCenterState.businessPanelsPromise = fetchJson('/api/decision/decision-intents')
      .then((intents) => {
        if (intents) {
          renderDecisionIntents(intents);
          decisionCenterState.intentsLoaded = true;
        }
        return Promise.all([
          fetchJson('/api/programs/sites-followup'),
          fetchJson('/api/decision/demo-scenarios'),
          fetchJson('/api/health/decision-summary'),
          decisionCenterState.explainKpis && Object.keys(decisionCenterState.explainKpis).length
            ? Promise.resolve({ kpis: decisionCenterState.explainKpis })
            : fetchJson('/api/decision/explain-kpi'),
        ]);
      })
      .then(([followup, demos, healthSummary, explain]) => {
        if (explain?.kpis) decisionCenterState.explainKpis = explain.kpis;
        if (followup) {
          renderProgramFollowup(followup);
          decisionCenterState.followupLoaded = true;
        }
        if (demos) renderDemoScenarios(demos);
        if (healthSummary?.value != null) {
          setNationalKpiElement('decision-kpi-health-facilities', formatNationalKpiNumber(healthSummary.value), false);
          applyExplainableKpiCard('health_facilities', {
            definition: healthSummary.definition,
            source_table: healthSummary.source_table,
            calculation_method: healthSummary.calculation_method,
            last_updated: healthSummary.last_updated,
            available: true,
          });
        }
      })
      .catch(() => {
        const body = document.querySelector('#decision-demo-scenario-body');
        if (body && !decisionCenterState.demoScenarios.length) {
          body.innerHTML = '<p class="decision-center-program-note">Scénarios temporairement indisponibles — réessayez Mode démonstration.</p>';
        }
      })
      .finally(() => {
        decisionCenterState.businessPanelsLoading = false;
      });

    return decisionCenterState.businessPanelsPromise;
  }

  function loadNationalPanel(forceReload) {
    if (decisionCenterState.nationalPanelLoading) return;
    if (decisionCenterState.nationalPanelLoaded && !forceReload) return;

    const shared = getShared();
    const canUseDb = typeof shared.canUseProgramDbData === 'function' && shared.canUseProgramDbData();
    if (!canUseDb) {
      renderNationalPanelUnavailable(NATIONAL_PANEL_PENDING_MESSAGE);
      decisionCenterState.nationalPanelLoaded = true;
      return;
    }

    decisionCenterState.nationalPanelLoading = true;
    const fetchPanel = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/decision/national-panel')
      : global.fetch('/api/decision/national-panel').then((response) => (response.ok ? response.json() : null));
    const fetchExplain = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/decision/explain-kpi')
      : Promise.resolve(null);

    Promise.all([Promise.resolve(fetchPanel), Promise.resolve(fetchExplain)])
      .then(([payload, explainPayload]) => {
        if (!payload || !payload.kpis) {
          renderNationalPanelUnavailable(NATIONAL_PANEL_PENDING_MESSAGE);
          return;
        }
        renderNationalPanelKpis(payload, explainPayload);
        decisionCenterState.nationalPanelLoaded = true;
        loadDecisionBusinessPanels(forceReload);
      })
      .catch(() => {
        renderNationalPanelUnavailable(NATIONAL_PANEL_PENDING_MESSAGE);
      })
      .finally(() => {
        decisionCenterState.nationalPanelLoading = false;
      });
  }

  function bindDecisionBusinessInteractions() {
    const root = document.querySelector('#decision-view-panel');
    if (!root || root.dataset.businessBound === 'true') return;
    root.dataset.businessBound = 'true';

    root.addEventListener('click', (event) => {
      const target = event.target;
      if (!(target instanceof global.HTMLElement)) return;

      const intentCard = target.closest('[data-intent-id]');
      if (intentCard) {
        const tab = intentCard.getAttribute('data-target-tab');
        const scenarioId = intentCard.getAttribute('data-scenario-id');
        const V12 = new Set(['invest_priority', 'ccn_implantation', 'territory_priority', 'investment_impact', 'dg_dossier']);
        if (scenarioId && V12.has(scenarioId) && typeof global.openDecisionScenario === 'function') {
          global.openDecisionScenario(scenarioId);
          return;
        }
        if (scenarioId) {
          setDemoModeVisible(true);
          const scenario = decisionCenterState.demoScenarios.find((item) => item.id === scenarioId);
          if (scenario) {
            decisionCenterState.demoActiveScenarioId = scenarioId;
            document.querySelectorAll('.decision-demo-scenario-btn').forEach((btn) => {
              btn.classList.toggle('is-active', btn.getAttribute('data-scenario-id') === scenarioId);
            });
            renderDemoScenario(scenario);
          }
        }
        if (tab) setDecisionCenterTab(tab);
        return;
      }

      const detailBtn = target.closest('[data-kpi-detail]');
      if (detailBtn) {
        openKpiDetail(detailBtn.getAttribute('data-kpi-detail'));
        return;
      }

      const kpiCard = target.closest('.decision-center-kpi-card[data-kpi-key]');
      if (kpiCard && !target.closest('button, a, input, select')) {
        openKpiDetail(kpiCard.getAttribute('data-kpi-key'));
        return;
      }

      if (target.id === 'decision-kpi-detail-close') {
        closeKpiDetail();
        return;
      }

      if (target.id === 'decision-open-edvs-btn') {
        global.location.hash = 'salle-pilotage';
        return;
      }

      if (target.id === 'decision-open-ti-btn') {
        global.location.hash = 'territorial-intelligence';
        return;
      }

      if (target.id === 'decision-open-nsme-map-btn') {
        global.location.hash = 'map';
        global.setTimeout(() => {
          const checkbox = document.querySelector('input[data-layer="asset_need_matches"]');
          if (checkbox && !checkbox.checked) {
            checkbox.checked = true;
            checkbox.dispatchEvent(new Event('change', { bubbles: true }));
          }
        }, 400);
        return;
      }

      if (target.id === 'decision-center-demo-mode-btn') {
        setDemoModeVisible(true);
        loadDecisionBusinessPanels(!decisionCenterState.demoScenarios.length);
        return;
      }

      if (target.id === 'decision-demo-close-btn') {
        setDemoModeVisible(false);
        return;
      }

      const scenarioBtn = target.closest('[data-scenario-id].decision-demo-scenario-btn');
      if (scenarioBtn) {
        const scenarioId = scenarioBtn.getAttribute('data-scenario-id');
        const scenario = decisionCenterState.demoScenarios.find((item) => item.id === scenarioId);
        document.querySelectorAll('.decision-demo-scenario-btn').forEach((btn) => {
          btn.classList.toggle('is-active', btn === scenarioBtn);
        });
        decisionCenterState.demoActiveScenarioId = scenarioId;
        renderDemoScenario(scenario);
        return;
      }

      const demoAction = target.closest('.decision-demo-action');
      if (demoAction) {
        const tab = demoAction.getAttribute('data-target-tab');
        if (tab) setDecisionCenterTab(tab);
      }
    });
  }

  function fetchProgramJson(relativePath) {
    const shared = getShared();
    if (typeof shared?.fetchJson === 'function' && typeof shared?.canUseProgramDbData === 'function' && shared.canUseProgramDbData()) {
      const apiPathMap = {
        'sites_40/sites_40.json': '/api/programs/sites40?format=panel',
        'sites_300/sites_300.json': '/api/programs/sites300?format=panel',
      };
      const apiPath = apiPathMap[relativePath];
      if (apiPath) {
        return shared.fetchJson(apiPath).then((payload) => {
          if (!payload) {
            throw new Error(`Impossible de charger ${apiPath}`);
          }
          return payload;
        });
      }
    }
    const path = `${PROGRAMS_DATA_BASE}${relativePath}`;
    return global.fetch(path).then((response) => {
      if (!response.ok) {
        throw new Error(`Impossible de charger ${path}`);
      }
      return response.json();
    });
  }

  function countByField(items, fieldName) {
    return asArray(items).reduce((acc, item) => {
      const key = String(item?.[fieldName] || 'Non renseigné').trim() || 'Non renseigné';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
  }

  function renderDistributionList(title, counts) {
    const entries = Object.entries(counts).sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0], 'fr'));
    if (!entries.length) {
      return `<div class="decision-center-sites-40-block"><h4>${escapeHtml(title)}</h4><p class="decision-center-program-loading">Aucune donnée.</p></div>`;
    }
    return `
      <div class="decision-center-sites-40-block">
        <h4>${escapeHtml(title)}</h4>
        <ul class="decision-center-sites-40-distribution">
          ${entries.map(([label, count]) => `<li><span>${escapeHtml(label)}</span><strong>${count.toLocaleString('fr-FR')}</strong></li>`).join('')}
        </ul>
      </div>
    `;
  }

  function renderSites40ProgramPanel(payload) {
    const container = document.querySelector('#decision-center-sites-40-body');
    if (!container) return;

    const sites = asArray(payload?.sites);
    const total = payload?._meta?.count || sites.length;
    const byZone = countByField(sites, 'zone');
    const byProvince = countByField(sites, 'province');

    container.innerHTML = `
      <div class="decision-center-sites-40-summary">
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Total sites</p>
          <p class="summary-value">${Number(total).toLocaleString('fr-FR')}</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Statut</p>
          <p class="summary-value is-status">Données KMZ intégrées</p>
        </article>
      </div>
      <div class="decision-center-sites-40-distributions">
        ${renderDistributionList('Répartition par zone FDSU', byZone)}
        ${renderDistributionList('Répartition par province', byProvince)}
      </div>
    `;
    decisionCenterState.sites40Loaded = true;
  }

  function bindSites40MapButton() {
    const button = document.querySelector('#decision-center-sites-40-map-btn');
    if (!button || button.dataset.bound === 'true') return;
    button.dataset.bound = 'true';
    button.addEventListener('click', () => {
      const shared = getShared();
      if (typeof shared.openSites40ProgramOnMap === 'function') {
        shared.openSites40ProgramOnMap();
        return;
      }
      if (typeof global.openSites40ProgramOnMap === 'function') {
        global.openSites40ProgramOnMap();
      }
    });
  }

  function loadSites40ProgramPanel(forceReload) {
    if (decisionCenterState.sites40Loading) return Promise.resolve();
    if (decisionCenterState.sites40Loaded && !forceReload) return Promise.resolve();

    const container = document.querySelector('#decision-center-sites-40-body');
    if (!container) return Promise.resolve();

    bindSites40MapButton();
    decisionCenterState.sites40Loading = true;
    container.innerHTML = '<p class="decision-center-program-loading">Chargement du programme Sites 40…</p>';

    return fetchProgramJson('sites_40/sites_40.json')
      .then((payload) => {
        renderSites40ProgramPanel(payload);
      })
      .catch(() => {
        container.innerHTML = '<p class="decision-center-program-error">Programme Sites 40 indisponible (<code>data/programs/sites_40/sites_40.json</code>).</p>';
      })
      .finally(() => {
        decisionCenterState.sites40Loading = false;
      });
  }

  function fetchBusinessJson(filename) {
    const path = `${BUSINESS_DATA_BASE}${filename}`;
    return global.fetch(path).then((response) => {
      if (!response.ok) {
        throw new Error(`Impossible de charger ${path}`);
      }
      return response.json();
    });
  }

  function resolveProgramStatusLabel(program, legacyStatusCatalog, lifecycleCatalog) {
    const lifecycle = asArray(lifecycleCatalog).find((entry) => entry.code === program?.program_status);
    if (lifecycle?.label) return lifecycle.label;
    const match = asArray(legacyStatusCatalog).find((entry) => entry.id === program?.status);
    return match?.label || program?.status || 'Non défini';
  }

  function resolveProgramStatusClass(program, lifecycleCatalog) {
    const lifecycle = asArray(lifecycleCatalog).find((entry) => entry.code === program?.program_status);
    if (lifecycle?.code === 'PLANIFIE') return 'is-planned';
    if (lifecycle?.code === 'EN_EXECUTION') return 'is-active';
    if (lifecycle?.code === 'EN_PREPARATION') return 'is-preparation';
    if (lifecycle?.code === 'EN_SUIVI') return 'is-followup';
    if (lifecycle?.code === 'TERMINE') return 'is-completed';
    if (program?.status === 'active') return 'is-active';
    if (program?.status === 'planned') return 'is-planned';
    return 'is-defined';
  }

  function renderProgramCard(program, legacyStatusCatalog, lifecycleCatalog) {
    const title = escapeHtml(program?.name || program?.short_label || 'Programme');
    const tagline = escapeHtml(program?.tagline || program?.description || '');
    const statusLabel = escapeHtml(resolveProgramStatusLabel(program, legacyStatusCatalog, lifecycleCatalog));
    const statusClass = resolveProgramStatusClass(program, lifecycleCatalog);

    return `
      <article class="decision-center-program-card" data-program-id="${escapeHtml(program?.id || '')}">
        <div class="decision-center-program-card-head">
          <span class="decision-center-program-card-marker" aria-hidden="true">■</span>
          <h4 class="decision-center-program-card-title">${title}</h4>
        </div>
        ${tagline ? `<p class="decision-center-program-card-tagline">${tagline}</p>` : ''}
        <p class="decision-center-program-card-status ${statusClass}">${statusLabel}</p>
      </article>
    `;
  }

  function renderBusinessArchitecturePanel(payload, lifecycleCatalog) {
    const container = document.querySelector('#decision-center-program-grid');
    if (!container) return;

    const programs = asArray(payload?.programs);
    const legacyStatusCatalog = asArray(payload?.statuses);

    if (!programs.length) {
      container.innerHTML = '<p class="decision-center-program-error">Aucun programme FDSU disponible.</p>';
      return;
    }

    container.innerHTML = programs.map((program) => renderProgramCard(program, legacyStatusCatalog, lifecycleCatalog)).join('');
    decisionCenterState.programsLoaded = true;
  }

  function loadPriorityMatrix() {
    if (decisionCenterState.priorityMatrixLoader) {
      return Promise.resolve(decisionCenterState.priorityMatrixLoader);
    }
    return fetchBusinessJson('priority_matrix_loader.json')
      .then((payload) => {
        decisionCenterState.priorityMatrixLoader = payload;
        return payload;
      })
      .catch(() => null);
  }

  function renderSites300ProgramPanel(payload, matrixLoader, scoresPayload) {
    const container = document.querySelector('#decision-center-sites-300-body');
    if (!container) return;

    const sites = asArray(payload?.sites);
    const total = payload?._meta?.count || sites.length;
    const scoredTotal = Number(
      scoresPayload?._meta?.total_filtered
      ?? scoresPayload?.sites?.length
      ?? 0,
    );
    const scoreReady = scoredTotal > 0;
    const scoreDisplay = scoreReady
      ? `${Number(scoredTotal).toLocaleString('fr-FR')} scorés`
      : 'En attente moteur';
    const matrixStatus = scoreReady
      ? (matrixLoader?.status?.message || 'Matrice disponible — scores moteur de décision FDSU actifs.')
      : (matrixLoader?.status?.message || 'Matrice disponible — scoring FDSU en attente.');

    container.innerHTML = `
      <div class="decision-center-sites-40-summary">
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Statut programme</p>
          <p class="summary-value is-planned-status">🟡 Planifié</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Sites</p>
          <p class="summary-value">${Number(total).toLocaleString('fr-FR')}</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Matrice</p>
          <p class="summary-value is-status">Disponible</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Score FDSU</p>
          <p class="summary-value">${escapeHtml(scoreDisplay)}</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Déploiement</p>
          <p class="summary-value">Non démarré</p>
        </article>
      </div>
      <p class="decision-center-program-note">${escapeHtml(matrixStatus)}</p>
      <div class="decision-center-sites-300-actions">
        <button type="button" class="primary-button" id="decision-center-sites-300-map-btn">Consulter les sites</button>
        <button type="button" class="secondary-button" id="decision-center-sites-300-matrix-btn">Voir la matrice</button>
        <button type="button" class="secondary-button" id="decision-center-sites-300-analysis-btn">Préparer l'analyse</button>
      </div>
      <div class="decision-center-program-info hidden" id="decision-center-sites-300-info" aria-live="polite"></div>
    `;
    bindSites300ActionButtons();
    decisionCenterState.sites300Loaded = true;
  }

  function showSites300Info(message) {
    const panel = document.querySelector('#decision-center-sites-300-info');
    if (!panel) return;
    panel.classList.remove('hidden');
    panel.innerHTML = `<p>${escapeHtml(message)}</p>`;
  }

  function bindSites300ActionButtons() {
    const mapButton = document.querySelector('#decision-center-sites-300-map-btn');
    if (mapButton && mapButton.dataset.bound !== 'true') {
      mapButton.dataset.bound = 'true';
      mapButton.addEventListener('click', () => {
        const shared = getShared();
        if (typeof shared.openSites300ProgramOnMap === 'function') {
          shared.openSites300ProgramOnMap();
          return;
        }
        if (typeof global.openSites300ProgramOnMap === 'function') {
          global.openSites300ProgramOnMap();
        }
      });
    }

    const matrixButton = document.querySelector('#decision-center-sites-300-matrix-btn');
    if (matrixButton && matrixButton.dataset.bound !== 'true') {
      matrixButton.dataset.bound = 'true';
      matrixButton.addEventListener('click', () => {
        loadPriorityMatrix().then((loader) => {
          const source = loader?.source?.strategic_copy || 'data/programs/sites_300/matrice_priorisation_300_sites.xlsx';
          showSites300Info(`Matrice officielle référencée : ${source}. Les scores de priorité Sites 300 sont produits par le moteur de décision FDSU (decision.fdsu_site_scores).`);
        });
      });
    }

    const analysisButton = document.querySelector('#decision-center-sites-300-analysis-btn');
    if (analysisButton && analysisButton.dataset.bound !== 'true') {
      analysisButton.dataset.bound = 'true';
      analysisButton.addEventListener('click', () => {
        loadPriorityMatrix().then((loader) => {
          const steps = asArray(loader?.pipeline).map((step) => step.description).join(' ');
          showSites300Info(`Analyse préparée via data/business/priority_matrix_loader.json. Étapes prévues : ${steps || 'normalisation et scoring à venir.'}`);
        });
      });
    }
  }

  function loadSites300ProgramPanel(forceReload) {
    if (decisionCenterState.sites300Loading) return Promise.resolve();
    if (decisionCenterState.sites300Loaded && !forceReload) return Promise.resolve();

    const container = document.querySelector('#decision-center-sites-300-body');
    if (!container) return Promise.resolve();

    decisionCenterState.sites300Loading = true;
    container.innerHTML = '<p class="decision-center-program-loading">Chargement du programme Sites 300…</p>';

    return Promise.all([
      fetchProgramJson('sites_300/sites_300.json'),
      loadPriorityMatrix(),
      fetch('/api/decision/site-scores?program_code=PROG_SITES_300&limit=1')
        .then((response) => (response.ok ? response.json() : null))
        .catch(() => null),
    ])
      .then(([payload, matrixLoader, scoresPayload]) => {
        renderSites300ProgramPanel(payload, matrixLoader, scoresPayload);
      })
      .catch(() => {
        container.innerHTML = '<p class="decision-center-program-error">Programme Sites 300 indisponible (<code>data/programs/sites_300/sites_300.json</code>).</p>';
      })
      .finally(() => {
        decisionCenterState.sites300Loading = false;
      });
  }

  function loadTelecomReferentialPanel(forceReload) {
    if (decisionCenterState.telecomLoaded && !forceReload) return Promise.resolve();

    const container = document.querySelector('#decision-center-telecom-body');
    if (!container) return Promise.resolve();
    if (decisionCenterState.telecomLoading && !forceReload) {
      return decisionCenterState.telecomLoadingPromise || Promise.resolve();
    }

    const shared = getShared();
    decisionCenterState.telecomLoading = true;
    container.innerHTML = '<p class="decision-center-program-loading">Chargement du référentiel télécom…</p>';

    const canUseDb = typeof shared.canUseTelecomDbData === 'function' && shared.canUseTelecomDbData();
    if (!canUseDb) {
      container.innerHTML = `
        <div class="decision-center-sites-40-summary">
          <article class="decision-center-sites-40-stat">
            <p class="summary-label">Mode</p>
            <p class="summary-value is-status">JSON</p>
          </article>
        </div>
        <p class="decision-center-program-note">Données télécom disponibles en mode DB.</p>
      `;
      decisionCenterState.telecomLoaded = true;
      decisionCenterState.telecomLoading = false;
      decisionCenterState.telecomLoadingPromise = null;
      return Promise.resolve();
    }

    const fetchPanel = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/telecom/panel')
      : global.fetch('http://127.0.0.1:8001/api/telecom/panel').then((response) => (response.ok ? response.json() : null));

    decisionCenterState.telecomLoadingPromise = Promise.race([
      fetchPanel,
      new Promise((resolve) => {
        global.setTimeout(() => resolve(null), 8000);
      }),
    ])
      .then((payload) => {
        if (!payload?.statistics) {
          throw new Error('Referentiel telecom indisponible');
        }
        const stats = payload.statistics;
        const operators = asArray(payload.operators);
        const sources = asArray(stats.by_source_file);
        container.innerHTML = `
          <div class="decision-center-sites-40-summary">
            <article class="decision-center-sites-40-stat">
              <p class="summary-label">Opérateurs</p>
              <p class="summary-value">${Number(stats.operator_count || operators.length).toLocaleString('fr-FR')}</p>
            </article>
            <article class="decision-center-sites-40-stat">
              <p class="summary-label">Sites radio</p>
              <p class="summary-value">${Number(stats.infrastructure_count || 0).toLocaleString('fr-FR')}</p>
            </article>
            <article class="decision-center-sites-40-stat">
              <p class="summary-label">Lignes réseau</p>
              <p class="summary-value">${Number(stats.network_line_count || 0).toLocaleString('fr-FR')}</p>
            </article>
            <article class="decision-center-sites-40-stat">
              <p class="summary-label">Polygones réseau</p>
              <p class="summary-value">${Number(stats.coverage_polygon_count || 0).toLocaleString('fr-FR')}</p>
            </article>
          </div>
          <div class="decision-center-sites-40-distributions">
            ${renderDistributionList('Opérateurs importés', operators.reduce((acc, item) => {
              acc[item.operator_name || item.operator_code] = 1;
              return acc;
            }, {}))}
            ${renderDistributionList('Sources KMZ intégrées', sources.reduce((acc, item) => {
              acc[item.source_file] = Number(item.points || 0) + Number(item.lines || 0) + Number(item.polygons || 0);
              return acc;
            }, {}))}
          </div>
          <p class="decision-center-program-note">Référentiel télécom disponible pour les futures analyses de couverture et de proximité FDSU.</p>
        `;
        decisionCenterState.telecomLoaded = true;
      })
      .catch(() => {
        container.innerHTML = `
          <div class="decision-center-sites-40-summary">
            <article class="decision-center-sites-40-stat">
              <p class="summary-label">Mode</p>
              <p class="summary-value is-status">Indisponible</p>
            </article>
          </div>
          <p class="decision-center-program-note">Données télécom disponibles en mode DB.</p>
        `;
        decisionCenterState.telecomLoaded = true;
      })
      .finally(() => {
        decisionCenterState.telecomLoading = false;
        decisionCenterState.telecomLoadingPromise = null;
      });

    return decisionCenterState.telecomLoadingPromise;
  }

  function loadSpatialAnalysisPanel(forceReload) {
    if (decisionCenterState.spatialLoaded && !forceReload) return Promise.resolve();

    const container = document.querySelector('#decision-center-spatial-body');
    if (!container) return Promise.resolve();
    if (decisionCenterState.spatialLoading && !forceReload) {
      return decisionCenterState.spatialLoadingPromise || Promise.resolve();
    }

    const shared = getShared();
    decisionCenterState.spatialLoading = true;
    container.innerHTML = '<p class="decision-center-program-loading">Chargement de l\'analyse spatiale…</p>';

    const canUseDb = typeof shared.canUseTelecomDbData === 'function' && shared.canUseTelecomDbData();
    if (!canUseDb) {
      container.innerHTML = `
        <div class="decision-center-sites-40-summary">
          <article class="decision-center-sites-40-stat">
            <p class="summary-label">Mode</p>
            <p class="summary-value is-status">JSON</p>
          </article>
        </div>
        <p class="decision-center-program-note">Analyses spatiales disponibles en mode DB.</p>
      `;
      decisionCenterState.spatialLoaded = true;
      decisionCenterState.spatialLoading = false;
      return Promise.resolve();
    }

    const fetchPanel = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/analysis/panel')
      : Promise.resolve(null);

    decisionCenterState.spatialLoadingPromise = Promise.race([
      fetchPanel,
      new Promise((resolve) => { global.setTimeout(() => resolve(null), 8000); }),
    ])
      .then((payload) => {
        if (!payload?.statistics) {
          throw new Error('Analyse indisponible');
        }
        renderSpatialAnalysisPanel(payload.statistics);
        decisionCenterState.spatialLoaded = true;
      })
      .catch(() => {
        container.innerHTML = `
          <div class="decision-center-sites-40-summary">
            <article class="decision-center-sites-40-stat">
              <p class="summary-label">Mode</p>
              <p class="summary-value is-status">Indisponible</p>
            </article>
          </div>
          <p class="decision-center-program-note">Analyses spatiales disponibles en mode DB.</p>
        `;
        decisionCenterState.spatialLoaded = true;
      })
      .finally(() => {
        decisionCenterState.spatialLoading = false;
        decisionCenterState.spatialLoadingPromise = null;
      });

    return decisionCenterState.spatialLoadingPromise;
  }

  function renderSpatialAnalysisPanel(stats) {
    const container = document.querySelector('#decision-center-spatial-body');
    if (!container) return;
    const lastAnalysis = stats.last_analysis
      ? new Date(stats.last_analysis).toLocaleString('fr-FR')
      : 'Aucune analyse';
    container.innerHTML = `
      <div class="decision-center-sites-40-summary">
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Sites analysés</p>
          <p class="summary-value">${Number(stats.sites_analyzed || 0).toLocaleString('fr-FR')}</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Infrastructures</p>
          <p class="summary-value">${Number(stats.infrastructure_analyzed || 0).toLocaleString('fr-FR')}</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Relations calculées</p>
          <p class="summary-value">${Number(stats.relations_computed || 0).toLocaleString('fr-FR')}</p>
        </article>
        <article class="decision-center-sites-40-stat">
          <p class="summary-label">Dernière analyse</p>
          <p class="summary-value is-status">${escapeHtml(lastAnalysis)}</p>
        </article>
      </div>
      <p class="decision-center-program-note">Moteur d'analyse spatiale générique — prêt pour Santé, Éducation, Énergie et futurs référentiels.</p>
    `;
  }

  function bindSpatialAnalysisRunButton() {
    const button = document.querySelector('#decision-center-spatial-run-btn');
    if (!button || button.dataset.bound === 'true') return;
    button.dataset.bound = 'true';
    button.addEventListener('click', () => {
      const shared = getShared();
      const container = document.querySelector('#decision-center-spatial-body');
      if (!container) return;
      if (typeof shared.canUseTelecomDbData === 'function' && !shared.canUseTelecomDbData()) {
        container.innerHTML = '<p class="decision-center-program-note">Analyses spatiales disponibles en mode DB.</p>';
        return;
      }
      container.innerHTML = '<p class="decision-center-program-loading">Analyse des programmes Sites 40 et Sites 300 en cours…</p>';
      const run = typeof shared.fetchApiJson === 'function'
        ? shared.fetchApiJson('/api/analysis/run/programs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
        : Promise.reject(new Error('API indisponible'));
      run
        .then(() => loadSpatialAnalysisPanel(true))
        .catch(() => {
          container.innerHTML = '<p class="decision-center-program-error">Analyse impossible. Vérifiez PostgreSQL et le mode DB.</p>';
        });
    });
  }

  const DECISION_ENGINE_PRIORITY_CLASS = {
    critical: 'is-critical',
    high: 'is-high',
    medium: 'is-medium',
    low: 'is-low',
  };

  const DECISION_ENGINE_MARKER_COLORS = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#ca8a04',
    low: '#4ade80',
  };

  function humanizeCriteriaLabel(label) {
    if (!label) return '';
    let text = String(label);
    text = text.replace(/Programme Sites 40 — déploiement en exécution/i, 'Programme Sites 40 — en cours');
    text = text.replace(/Programme Sites 300 — planifié/i, 'Programme Sites 300 — planifié');
    text = text.replace(/Distance opérateur ([\d.,]+) km — déficit majeur/i, 'Réseau éloigné ($1 km) — besoin urgent');
    text = text.replace(/Distance opérateur ([\d.,]+) km — déficit élevé/i, 'Réseau éloigné ($1 km) — couverture faible');
    text = text.replace(/Distance opérateur ([\d.,]+) km — déficit modéré/i, 'Réseau à $1 km — déficit modéré');
    text = text.replace(/Proximité infrastructure \(([\d.,]+) km\) — déficit faible/i, 'Réseau proche ($1 km)');
    text = text.replace(/Contexte admin validé PostGIS — /i, 'Zone : ');
    text = text.replace(/Province et territoire renseignés — /i, 'Zone : ');
    text = text.replace(/Contexte administratif partiel — /i, 'Zone partielle : ');
    text = text.replace(/Contexte administratif incomplet/i, 'Localisation à compléter');
    text = text.replace(/\d+ relations spatiales calculées/i, 'Analyse spatiale complète');
    text = text.replace(/\d+ relation\(s\) spatiale\(s\) — analyse partielle/i, 'Analyse spatiale partielle');
    text = text.replace(/Aucune relation spatiale — exécuter l'analyse spatiale/i, 'Lancer l\'analyse spatiale');
    text = text.replace(/Distance télécom non calculée — lancer l'analyse spatiale/i, 'Couverture réseau à analyser');
    text = text.replace(/Site en exécution/i, 'Déploiement en cours');
    text = text.replace(/Site du programme en cours de déploiement/i, 'Site en déploiement actif');
    if (text.length > 64) return `${text.slice(0, 61)}…`;
    return text;
  }

  function formatProgramLabel(site) {
    const code = String(site?.program_code || '').toUpperCase();
    if (code.includes('SITES_40') || code === 'SITES_40') return 'Sites 40';
    if (code.includes('SITES_300') || code === 'SITES_300') return 'Sites 300';
    if (code.includes('20476') || code.includes('SITES_20476')) return 'National 20 476';
    const name = site?.program_name || site?.program_code || '—';
    return name.length > 18 ? `${name.slice(0, 16)}…` : name;
  }

  function getDecisionEngineMarkerColor(site) {
    return DECISION_ENGINE_MARKER_COLORS[site?.priority_level] || DECISION_ENGINE_MARKER_COLORS.low;
  }

  function renderDecisionEngineKpis(summary) {
    const total = summary?.total ?? 0;
    const set = (id, value) => {
      const node = document.querySelector(id);
      if (node) node.textContent = Number(value || 0).toLocaleString('fr-FR');
    };
    set('#decision-engine-kpi-total', total);
    set('#decision-engine-kpi-critical', summary?.critical);
    set('#decision-engine-kpi-high', summary?.high);
    set('#decision-engine-kpi-medium', summary?.medium);
    set('#decision-engine-kpi-low', summary?.low);
  }

  function formatDecisionCriteria(topCriteria) {
    const items = asArray(topCriteria);
    if (!items.length) return 'Non renseigné';
    return items.slice(0, 2).map((item) => escapeHtml(humanizeCriteriaLabel(item?.label || ''))).join(' · ');
  }

  function formatPrimaryFactor(site) {
    const items = asArray(site?.top_criteria || site?.criteria_details?.top_factors || []);
    if (!items.length) return 'Non renseigné';
    const label = humanizeCriteriaLabel(items[0]?.label || items[0]?.criterion_id || '');
    return label || 'Non renseigné';
  }

  function truncateText(value, maxLen) {
    const text = String(value ?? '').trim();
    if (!text) return 'Non renseigné';
    if (text.length <= maxLen) return text;
    return `${text.slice(0, Math.max(0, maxLen - 1)).trim()}…`;
  }

  function renderDecisionEngineTable(sites) {
    const tbody = document.querySelector('#decision-engine-table-body');
    if (!tbody) return;
    const filtered = decisionCenterState.decisionEngineFilter
      ? sites.filter((site) => site.priority_level === decisionCenterState.decisionEngineFilter)
      : sites;

    if (!filtered.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="decision-center-program-loading">Aucun site pour ce filtre.</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map((site) => {
      const levelClass = DECISION_ENGINE_PRIORITY_CLASS[site.priority_level] || 'is-low';
      const selected = decisionCenterState.decisionEngineSelectedSiteId === site.site_id ? ' is-selected' : '';
      const territory = [site.territoire, site.province].filter(Boolean).join(' · ') || 'Non renseigné';
      const siteName = (global.FdsuSiteDisplayName?.siteDisplayLabel?.(site))
        || site.display_name || site.site_name || site.site_code || 'Site FDSU';
      const techId = site.technical_id || site.site_name || site.site_code;
      const siteTitle = [siteName, techId !== siteName ? techId : null, formatProgramLabel(site)].filter(Boolean).join(' — ');
      const factor = formatPrimaryFactor(site);
      const score = Number(site.priority_score || 0).toFixed(1);
      const priorityLabel = site.priority_level_label || site.priority_level || '—';
      return `
        <tr data-site-id="${escapeHtml(site.site_id)}" class="${selected.trim()}">
          <td class="col-site" title="${escapeHtml(siteTitle)}">
            <strong>${escapeHtml(truncateText(siteName, 42))}</strong>
            <small>${escapeHtml(formatProgramLabel(site))}</small>
          </td>
          <td class="col-location is-ellipsis" title="${escapeHtml(territory)}">${escapeHtml(truncateText(territory, 48))}</td>
          <td class="col-score">${score}</td>
          <td class="col-priority"><span class="decision-engine-priority-badge ${levelClass}">${escapeHtml(priorityLabel)}</span></td>
          <td class="col-factor is-ellipsis" title="${escapeHtml(factor)}">${escapeHtml(truncateText(factor, 40))}</td>
          <td class="col-action">
            <button type="button" class="secondary-button decision-engine-detail-btn" data-site-id="${escapeHtml(site.site_id)}" data-program-code="${escapeHtml(site.program_code || decisionCenterState.decisionEngineProgram || '')}">
              Voir le détail
            </button>
            ${site.territoire ? `<button type="button" class="secondary-button decision-engine-tdt-btn" data-territory="${escapeHtml(site.territoire)}" data-province="${escapeHtml(site.province || '')}">Profil territorial</button>` : ''}
          </td>
        </tr>
      `;
    }).join('');

    tbody.querySelectorAll('tr[data-site-id]').forEach((row) => {
      row.addEventListener('click', (event) => {
        if (event.target?.closest?.('.decision-engine-detail-btn') || event.target?.closest?.('.decision-engine-tdt-btn')) return;
        selectDecisionEngineSite(Number(row.dataset.siteId) || row.dataset.siteId);
      });
    });
    tbody.querySelectorAll('.decision-engine-tdt-btn').forEach((btn) => {
      btn.addEventListener('click', (event) => {
        event.stopPropagation();
        const territory = btn.getAttribute('data-territory');
        if (territory && global.TerritorialDigitalTwin?.open) {
          global.TerritorialDigitalTwin.open({
            entityType: 'territoire',
            entityId: territory,
            returnHash: 'decision-view',
          });
        }
      });
    });
  }

  function initializeDecisionEngineMap() {
    const shared = getShared();
    if (typeof global.L === 'undefined') return;

    const mapElement = document.querySelector('#decision-engine-map');
    if (!mapElement) return;

    if (decisionCenterState.decisionEngineMap) {
      global.setTimeout(() => decisionCenterState.decisionEngineMap.invalidateSize(), 0);
      return;
    }

    decisionCenterState.decisionEngineMap = global.L.map(mapElement, {
      zoomControl: true,
      attributionControl: true,
      minZoom: 4,
      maxZoom: 14,
    }).setView([-2.8, 23.5], 5);

    // Remonter le pane tooltip au-dessus des contrôles (évite tooltips « muets » / masqués)
    const tooltipPane = decisionCenterState.decisionEngineMap.getPane('tooltipPane');
    if (tooltipPane) tooltipPane.style.zIndex = 700;

    global.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(decisionCenterState.decisionEngineMap);

    decisionCenterState.decisionEngineMarkers = global.L.layerGroup().addTo(decisionCenterState.decisionEngineMap);

    if (shared.fetchApiJson) {
      shared.fetchApiJson('/map/layers/provinces?limit=5000')
        .then((payload) => {
          const features = asArray(payload?.features);
          if (!features.length) return;
          global.L.geoJSON({ type: 'FeatureCollection', features }, {
            style: shared.styleProvinceFeature,
            onEachFeature: (feature, layer) => {
              if (global.SigMapTooltips?.bind) {
                global.SigMapTooltips.bind(layer, feature, 'province', {
                  interactive: false,
                  direction: 'auto',
                });
              } else if (layer.bindTooltip) {
                const name = feature?.properties?.nom || feature?.properties?.name || 'Province';
                layer.bindTooltip(String(name), {
                  sticky: false,
                  direction: 'auto',
                  className: 'sig-map-tooltip',
                });
              }
            },
          }).addTo(decisionCenterState.decisionEngineMap);
        })
        .catch(() => {});
    }

    global.setTimeout(() => decisionCenterState.decisionEngineMap?.invalidateSize(), 0);
  }

  function updateDecisionEngineMapMarkers(sites) {
    if (!decisionCenterState.decisionEngineMap || !decisionCenterState.decisionEngineMarkers) return;

    const filtered = decisionCenterState.decisionEngineFilter
      ? sites.filter((site) => site.priority_level === decisionCenterState.decisionEngineFilter)
      : sites;

    decisionCenterState.decisionEngineMarkers.clearLayers();
    const bounds = [];

    filtered.forEach((site) => {
      const lat = Number(site.latitude);
      const lng = Number(site.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
      const color = getDecisionEngineMarkerColor(site);
      const selected = decisionCenterState.decisionEngineSelectedSiteId === site.site_id;
      const marker = global.L.circleMarker([lat, lng], {
        radius: selected ? 10 : 7,
        color,
        fillColor: color,
        fillOpacity: 0.9,
        weight: selected ? 3 : 2,
        bubblingMouseEvents: false,
      });
      marker.bindPopup(`
        <strong>${escapeHtml((global.FdsuSiteDisplayName?.siteDisplayLabel?.(site)) || site.display_name || site.site_name || site.site_code || 'Site FDSU')}</strong><br/>
        Score : ${Number(site.priority_score || 0).toFixed(1)}<br/>
        ${escapeHtml(site.priority_level_label || site.priority_level || '')}<br/>
        <span class="map-popup-action">Cliquer pour le dossier de décision</span>
      `, { maxWidth: 260, className: 'decision-map-popup-wrapper' });

      const label = (global.FdsuSiteDisplayName?.siteDisplayLabel?.(site))
        || site.display_name || site.site_name || site.site_code || 'Site';
      const tipProps = {
        ...site,
        name: label,
        site_name: label,
        display_name: label,
        technical_id: site.technical_id || site.site_name,
        site_code: site.site_code,
        program_code: site.program_code,
        programme: site.program_name || site.program_code,
        province: site.province,
        territoire: site.territoire,
        priority_score: site.priority_score,
        priority_level: site.priority_level_label || site.priority_level,
        priority_level_label: site.priority_level_label || site.priority_level,
        top_factor: formatPrimaryFactor(site),
      };

      if (global.SigMapTooltips?.bind) {
        global.SigMapTooltips.bind(marker, tipProps, 'site', {
          direction: 'auto',
          onClick: () => {
            selectDecisionEngineSite(site.site_id);
          },
        });
      } else {
        marker.bindTooltip(
          `<strong>${escapeHtml(label)}</strong><br>Score ${Number(site.priority_score || 0).toFixed(1)}`,
          { direction: 'auto', opacity: 1, className: 'sig-map-tooltip' },
        );
        marker.on('click', () => selectDecisionEngineSite(site.site_id));
      }
      marker.addTo(decisionCenterState.decisionEngineMarkers);
      bounds.push([lat, lng]);
    });

    if (bounds.length > 1) {
      decisionCenterState.decisionEngineMap.fitBounds(bounds, { padding: [28, 28], maxZoom: 8 });
    } else if (bounds.length === 1) {
      decisionCenterState.decisionEngineMap.setView(bounds[0], 8);
    }
  }

  function selectDecisionEngineSite(siteId) {
    decisionCenterState.decisionEngineSelectedSiteId = siteId;
    renderDecisionEngineTable(decisionCenterState.decisionEngineSites);
    updateDecisionEngineMapMarkers(decisionCenterState.decisionEngineSites);

    const site = decisionCenterState.decisionEngineSites.find((item) => String(item.site_id) === String(siteId));
    if (site && decisionCenterState.decisionEngineMap) {
      const lat = Number(site.latitude);
      const lng = Number(site.longitude);
      if (Number.isFinite(lat) && Number.isFinite(lng)) {
        decisionCenterState.decisionEngineMap.setView([lat, lng], 10);
      }
    }
  }

  function bindDecisionEngineTableExpand() {
    const btn = document.querySelector('#decision-engine-table-expand-btn');
    const body = document.querySelector('#decision-engine-body');
    if (!btn || !body || btn.dataset.bound === 'true') return;
    btn.dataset.bound = 'true';
    btn.addEventListener('click', () => {
      const expanded = body.classList.toggle('is-table-expanded');
      btn.setAttribute('aria-pressed', expanded ? 'true' : 'false');
      btn.textContent = expanded ? 'Réduire le tableau' : 'Agrandir le tableau';
      global.setTimeout(() => decisionCenterState.decisionEngineMap?.invalidateSize(), 80);
    });
  }

  function bindDecisionEngineLegend() {
    const toggle = document.querySelector('#decision-engine-legend-toggle');
    const legend = document.querySelector('#decision-engine-map-legend');
    if (!toggle || !legend || toggle.dataset.bound === 'true') return;
    toggle.dataset.bound = 'true';
    toggle.addEventListener('click', () => {
      const collapsed = legend.classList.toggle('is-collapsed');
      toggle.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
    });
  }

  function bindDecisionEngineFilters() {
    const container = document.querySelector('#decision-engine-filters');
    if (!container || container.dataset.bound === 'true') return;
    container.dataset.bound = 'true';

    container.querySelectorAll('[data-priority-filter]').forEach((button) => {
      button.addEventListener('click', () => {
        decisionCenterState.decisionEngineFilter = button.dataset.priorityFilter || '';
        container.querySelectorAll('[data-priority-filter]').forEach((item) => {
          item.classList.toggle('is-active', item === button);
        });
        renderDecisionEngineTable(decisionCenterState.decisionEngineSites);
        updateDecisionEngineMapMarkers(decisionCenterState.decisionEngineSites);
      });
    });
  }

  function bindDecisionEngineRecomputeButton() {
    const button = document.querySelector('#decision-engine-recompute-btn');
    if (!button || button.dataset.bound === 'true') return;
    button.dataset.bound = 'true';

    button.addEventListener('click', () => {
      const shared = getShared();
      const tbody = document.querySelector('#decision-engine-table-body');
      if (typeof shared.canUseTelecomDbData === 'function' && !shared.canUseTelecomDbData()) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="decision-center-program-note">Scores disponibles en mode DB.</td></tr>';
        return;
      }
      if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="decision-center-program-loading">Recalcul des scores en cours…</td></tr>';
      const run = typeof shared.fetchApiJson === 'function'
        ? shared.fetchApiJson('/api/decision/recompute-site-scores', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
        : Promise.reject(new Error('API indisponible'));
      run
        .then(() => loadDecisionEnginePanel(true))
        .catch(() => {
          if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="decision-center-program-error">Recalcul impossible.</td></tr>';
        });
    });
  }

  function renderDecisionEngineTopList(sites) {
    const list = document.querySelector('#decision-engine-top-list');
    if (!list) return;
    const top = asArray(sites).slice(0, 10);
    if (!top.length) {
      list.innerHTML = '<li>Aucune priorité disponible pour ce programme.</li>';
      return;
    }
    list.innerHTML = top.map((site, index) => {
      const label = (global.FdsuSiteDisplayName?.siteDisplayLabel?.(site))
        || site.display_name || site.site_name || site.site_code || 'Site';
      return `
      <li>
        <strong>#${index + 1}</strong>
        ${escapeHtml(label)}
        — score ${escapeHtml(site.priority_score)}
        (${escapeHtml(site.priority_level_label || site.priority_level)})
        <button type="button" class="secondary-button decision-engine-explain-btn" data-site-id="${escapeHtml(site.site_id)}" data-program-code="${escapeHtml(site.program_code || decisionCenterState.decisionEngineProgram)}">Expliquer</button>
      </li>
    `;
    }).join('');
  }

  function openDecisionEngineExplain(payload) {
    const panel = document.querySelector('#decision-engine-explain');
    const title = document.querySelector('#decision-engine-explain-title');
    const body = document.querySelector('#decision-engine-explain-body');
    const caseBody = document.querySelector('#decision-engine-case-body');
    const sheetBody = document.querySelector('#decision-center-decision-sheet-body');
    if (!panel || !body) return;
    const site = payload?.site || payload?.asset || {};
    const explanation = payload?.explanation || {};
    const justification = payload?.justification || [];
    const doctrine = payload?.doctrine || {};
    if (title) {
      title.textContent = (global.FdsuSiteDisplayName?.siteDisplayLabel?.(site))
        || site.display_name || site.name || site.site_name || `Site ${site.id || site.site_id}`;
    }

    const justifyHtml = justification.length
      ? justification.map((item) => `
          <article class="decision-justify-item">
            <h5>${escapeHtml(item.label)} — ${escapeHtml(item.contribution_display || item.score_display)}</h5>
            <p><strong>Pourquoi ?</strong> ${escapeHtml(item.why)}</p>
          </article>
        `).join('')
      : `<ul>${Object.values(explanation.criteria || {}).map((item) => `
          <li><strong>${escapeHtml(item.score)}</strong> × ${escapeHtml(item.weight)} — ${escapeHtml(item.label)}</li>
        `).join('')}</ul>`;

    body.innerHTML = `
      <p><strong>Réponse :</strong> ${escapeHtml(payload?.summary?.text || explanation.answer || '')}</p>
      <p><strong>Doctrine :</strong> ${escapeHtml(doctrine.title || '—')} v${escapeHtml(doctrine.version || '—')}</p>
      <p><strong>Confiance :</strong> ${escapeHtml(payload?.confidence?.label || '—')}</p>
      <p><strong>Calibration :</strong> ${escapeHtml(explanation.calibration_note || (site.criteria_details?.calibration?.note) || 'Matrice 300')}</p>
      ${justifyHtml}
    `;

    const casePayload = payload?.case_file || null;
    if (caseBody) {
      if (casePayload) {
        caseBody.innerHTML = renderDecisionCaseHtml(casePayload);
      } else {
        caseBody.innerHTML = '<p>Chargement du dossier…</p>';
      }
    }
    if (sheetBody) {
      sheetBody.innerHTML = body.innerHTML;
    }

    panel.querySelectorAll('[data-decision-case-tab]').forEach((btn) => {
      btn.classList.toggle('is-active', btn.getAttribute('data-decision-case-tab') === 'justification');
    });
    body.hidden = false;
    body.removeAttribute('hidden');
    if (caseBody) {
      caseBody.hidden = true;
      caseBody.setAttribute('hidden', '');
    }

    panel.hidden = false;
    panel.removeAttribute('hidden');
  }

  function renderDecisionCaseHtml(c) {
    return `
      <div class="decision-case-block">
        <h5>Dossier ${escapeHtml(c.case_id)}</h5>
        <p><strong>Score :</strong> ${escapeHtml(c.score?.global)} — ${escapeHtml(c.score?.priority_label || c.score?.priority_level)}</p>
        <p><strong>Doctrine :</strong> ${escapeHtml(c.doctrine?.title)} v${escapeHtml(c.doctrine?.version)}</p>
        <p><strong>Matrice :</strong> ${escapeHtml(c.matrix?.id)}</p>
        <p><strong>Impact population :</strong> ${escapeHtml(c.impacts?.population_touchee)}</p>
        <p><strong>Risques :</strong> ${(c.risks || []).map((r) => escapeHtml(r.label)).join(', ') || 'Aucun'}</p>
        <p><strong>Sources :</strong></p>
        <ul>${(c.sources || []).map((s) => `<li>${escapeHtml(s)}</li>`).join('')}</ul>
        <p><strong>Traçabilité :</strong> ${escapeHtml(c.engine_version)} — ${escapeHtml(c.generated_at)}</p>
        <p><em>${escapeHtml(c.pdf_export?.note || '')}</em></p>
      </div>
    `;
  }

  function bindDecisionEngineProgramFilters() {
    const container = document.querySelector('#decision-engine-program-filters');
    if (!container || container.dataset.bound === 'true') return;
    container.dataset.bound = 'true';
    container.querySelectorAll('[data-program-filter]').forEach((button) => {
      button.addEventListener('click', () => {
        container.querySelectorAll('[data-program-filter]').forEach((item) => item.classList.remove('is-active'));
        button.classList.add('is-active');
        decisionCenterState.decisionEngineProgram = button.getAttribute('data-program-filter') || 'sites_20476';
        decisionCenterState.decisionEngineLoaded = false;
        loadDecisionEnginePanel(true);
      });
    });
  }

  function bindDecisionEngineExplainActions() {
    const root = document.querySelector('#decision-engine-panel');
    if (!root || root.dataset.explainBound === 'true') return;
    root.dataset.explainBound = 'true';
    root.addEventListener('click', (event) => {
      const target = event.target;
      if (!(target instanceof global.HTMLElement)) return;
      if (target.id === 'decision-engine-explain-close') {
        const panel = document.querySelector('#decision-engine-explain');
        if (panel) {
          panel.hidden = true;
          panel.setAttribute('hidden', '');
        }
        return;
      }
      if (target.id === 'decision-engine-export-btn') {
        const program = decisionCenterState.decisionEngineProgram || 'sites_20476';
        const shared = getShared();
        shared.fetchJson(`/api/decision/sites/export?program_code=${encodeURIComponent(program)}`)
          .then((payload) => {
            if (payload?.absolute_path || payload?.export_path) {
              global.alert(`Export généré : ${payload.filename || payload.export_path}`);
            }
          })
          .catch(() => global.alert('Export indisponible.'));
        return;
      }
      const explainBtn = target.closest('.decision-engine-explain-btn');
      if (explainBtn) {
        const siteId = explainBtn.getAttribute('data-site-id');
        const program = explainBtn.getAttribute('data-program-code') || decisionCenterState.decisionEngineProgram;
        if (typeof global.openDecisionCase === 'function') {
          global.openDecisionCase('site', siteId, program);
          return;
        }
        global.location.hash = `decision-case/site/${encodeURIComponent(siteId)}?program_code=${encodeURIComponent(program || '')}`;
        return;
      }
      const detailBtn = target.closest('.decision-engine-detail-btn');
      if (detailBtn) {
        event.preventDefault();
        event.stopPropagation();
        const siteId = detailBtn.getAttribute('data-site-id');
        const program = detailBtn.getAttribute('data-program-code') || decisionCenterState.decisionEngineProgram;
        selectDecisionEngineSite(Number(siteId) || siteId);
        if (typeof global.openDecisionCase === 'function') {
          global.openDecisionCase('site', siteId, program);
        } else {
          global.location.hash = `decision-case/site/${encodeURIComponent(siteId)}?program_code=${encodeURIComponent(program || '')}`;
        }
      }
    });

    const explainPanel = document.querySelector('#decision-engine-explain');
    if (explainPanel && explainPanel.dataset.caseTabsBound !== 'true') {
      explainPanel.dataset.caseTabsBound = 'true';
      explainPanel.addEventListener('click', (event) => {
        const tab = event.target?.closest?.('[data-decision-case-tab]');
        if (!tab) return;
        const tabId = tab.getAttribute('data-decision-case-tab');
        explainPanel.querySelectorAll('[data-decision-case-tab]').forEach((btn) => {
          btn.classList.toggle('is-active', btn.getAttribute('data-decision-case-tab') === tabId);
        });
        explainPanel.querySelectorAll('[data-decision-case-panel]').forEach((panelNode) => {
          const active = panelNode.getAttribute('data-decision-case-panel') === tabId;
          panelNode.hidden = !active;
          if (active) panelNode.removeAttribute('hidden');
          else panelNode.setAttribute('hidden', '');
        });
      });
    }
  }

  function loadDecisionEnginePanel(forceReload) {
    if (decisionCenterState.decisionEngineLoaded && !forceReload) {
      initializeDecisionEngineMap();
      updateDecisionEngineMapMarkers(decisionCenterState.decisionEngineSites);
      global.setTimeout(() => decisionCenterState.decisionEngineMap?.invalidateSize(), 0);
      return Promise.resolve();
    }
    if (decisionCenterState.decisionEngineLoading && !forceReload) return Promise.resolve();

    const tbody = document.querySelector('#decision-engine-table-body');
    const shared = getShared();
    bindDecisionEngineFilters();
    bindDecisionEngineProgramFilters();
    bindDecisionEngineRecomputeButton();
    bindDecisionEngineExplainActions();
    bindDecisionEngineTableExpand();
    bindDecisionEngineLegend();

    decisionCenterState.decisionEngineLoading = true;
    if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="decision-center-program-loading">Chargement des scores…</td></tr>';

    const program = decisionCenterState.decisionEngineProgram || 'sites_20476';
    const priority = decisionCenterState.decisionEngineFilter || '';
    const query = new URLSearchParams({
      program_code: program,
      limit: program === 'sites_20476' ? '300' : '500',
    });
    if (priority) query.set('priority_level', priority);

    const fetchScores = typeof shared.fetchJson === 'function'
      ? shared.fetchJson(`/api/decision/sites/priorities?${query.toString()}`)
      : Promise.reject(new Error('API indisponible'));

    return fetchScores
      .then((payload) => {
        if (!payload?.sites) throw new Error('Scores indisponibles');
        decisionCenterState.decisionEngineSites = asArray(payload?.sites);
        renderDecisionEngineKpis(payload?.summary);
        renderDecisionEngineTable(decisionCenterState.decisionEngineSites);
        renderDecisionEngineTopList(decisionCenterState.decisionEngineSites);
        initializeDecisionEngineMap();
        updateDecisionEngineMapMarkers(decisionCenterState.decisionEngineSites);
        decisionCenterState.decisionEngineLoaded = true;
      })
      .catch(() => {
        // Fallback historique DB pour 40/300 si endpoint national indisponible
        if (program === 'sites_20476') {
          renderDecisionEngineKpis({ total: 0, critical: 0, high: 0, medium: 0, low: 0 });
          if (tbody) {
            tbody.innerHTML = '<tr><td colspan="7" class="decision-center-program-note">Priorisation nationale indisponible — vérifier l’import 20 476.</td></tr>';
          }
          renderDecisionEngineTopList([]);
          initializeDecisionEngineMap();
          decisionCenterState.decisionEngineLoaded = true;
          return null;
        }
        return shared.fetchJson(`/api/decision/site-scores?limit=500${priority ? `&priority_level=${encodeURIComponent(priority)}` : ''}`)
          .then((payload) => {
            decisionCenterState.decisionEngineSites = asArray(payload?.sites);
            renderDecisionEngineKpis(payload?.summary);
            renderDecisionEngineTable(decisionCenterState.decisionEngineSites);
            renderDecisionEngineTopList(decisionCenterState.decisionEngineSites);
            initializeDecisionEngineMap();
            updateDecisionEngineMapMarkers(decisionCenterState.decisionEngineSites);
            decisionCenterState.decisionEngineLoaded = true;
          });
      })
      .finally(() => {
        decisionCenterState.decisionEngineLoading = false;
        global.setTimeout(() => decisionCenterState.decisionEngineMap?.invalidateSize(), 0);
      });
  }

  function renderMasterBreakdown(targetId, mapping) {
    const node = document.querySelector(targetId);
    if (!node) return;
    const entries = Object.entries(mapping || {}).sort((a, b) => Number(b[1]) - Number(a[1]));
    if (!entries.length) {
      node.textContent = 'Aucune donnée.';
      return;
    }
    node.innerHTML = entries.map(([key, value]) => `
      <div class="master-type-row">
        <span>${escapeHtml(key)}</span>
        <strong>${Number(value).toLocaleString('fr-FR')}</strong>
      </div>
    `).join('');
  }

  function loadCcnDecisionExtensions(forceReload) {
    if (decisionCenterState.ccnExtensionsLoaded && !forceReload) return Promise.resolve();
    const list = document.querySelector('#decision-ccn-extensions-list');
    const shared = getShared();
    if (typeof shared.fetchJson !== 'function') return Promise.resolve();

    return shared.fetchJson('/api/ccn/decision-extensions')
      .then((payload) => {
        const extensions = asArray(payload?.extensions);
        if (list && extensions.length) {
          list.innerHTML = extensions.map((ext) => `
            <li>
              <strong>${escapeHtml(ext.label || ext.code)}</strong>
              — ${escapeHtml(ext.description || 'Extension préparée')}
              <span class="decision-center-program-note">(${ext.ui_ready ? 'UI prête' : 'UI non branchée'})</span>
            </li>
          `).join('');
        }
        decisionCenterState.ccnExtensionsLoaded = true;
      })
      .catch(() => {
        /* Fondations uniquement : silence si API indisponible */
      });
  }

  function getCcnDecisionExtensions() {
    return loadCcnDecisionExtensions(true);
  }

  function loadMasterRegistryPanel(forceReload) {
    if (decisionCenterState.masterRegistryLoaded && !forceReload) return Promise.resolve();
    if (decisionCenterState.masterRegistryLoading && !forceReload) return Promise.resolve();

    const shared = getShared();
    decisionCenterState.masterRegistryLoading = true;
    const fetchPanel = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/master/panel')
      : Promise.reject(new Error('API indisponible'));

    return fetchPanel
      .then((payload) => {
        const stats = payload?.statistics || {};
        const totals = stats.totals || {};
        const set = (id, value) => {
          const node = document.querySelector(id);
          if (node) node.textContent = value == null ? '—' : Number(value).toLocaleString('fr-FR');
        };
        set('#master-kpi-entities', totals.entities);
        set('#master-kpi-duplicates', totals.duplicate_groups);
        set('#master-kpi-valid', totals.fdsu_codes_valid);
        set('#master-kpi-invalid', totals.fdsu_codes_invalid);
        set('#master-kpi-sources', totals.sources);
        set('#master-kpi-versions', totals.versions_events);
        const quality = document.querySelector('#master-kpi-quality');
        if (quality) quality.textContent = `${stats.quality_score ?? '—'} %`;

        const note = document.querySelector('#master-nomenclature-note');
        const nomen = payload?.nomenclature || {};
        if (note) {
          note.textContent = `${nomen.format || ''} — exemple ${nomen.example || ''} — ${nomen.note || nomen.source || ''}`;
        }
        const zones = document.querySelector('#master-nomenclature-zones');
        if (zones) {
          zones.innerHTML = (nomen.zones || []).map((zone) => `<li>${escapeHtml(zone)}</li>`).join('');
        }
        renderMasterBreakdown('#master-type-breakdown', stats.by_type);
        renderMasterBreakdown('#master-sources-breakdown', stats.sources);
        renderMasterBreakdown('#master-quality-breakdown', {
          ...(stats.validation_status || {}),
          ...(stats.confidence_level || {}),
        });
        decisionCenterState.masterRegistryLoaded = true;
      })
      .catch(() => {
        const note = document.querySelector('#master-nomenclature-note');
        if (note) note.textContent = 'Référentiel national indisponible.';
      })
      .finally(() => {
        decisionCenterState.masterRegistryLoading = false;
      });
  }

  const SECTORIAL_CARD_CODES = ['HEALTH', 'EDUCATION', 'ENERGY', 'ROADS', 'POPULATION'];
  const REFERENTIAL_STATUS_LABELS = {
    active: 'Actif',
    in_progress: 'En cours',
    planned: 'Planifié',
  };
  const REFERENTIAL_STATUS_CLASS = {
    active: 'is-active',
    in_progress: 'is-progress',
    planned: 'is-planned',
  };

  function renderSectorialCatalogCards(catalog) {
    const container = document.querySelector('#sectorial-catalog-grid');
    if (!container) return;
    const items = asArray(catalog).filter((item) => SECTORIAL_CARD_CODES.includes(item.code));
    if (!items.length) {
      container.innerHTML = '<p class="decision-center-program-note">Catalogue sectoriel indisponible.</p>';
      return;
    }
    container.innerHTML = items.map((item) => {
      const status = item.status || 'planned';
      const statusClass = REFERENTIAL_STATUS_CLASS[status] || 'is-planned';
      const statusLabel = REFERENTIAL_STATUS_LABELS[status] || status;
      return `
        <article class="sectorial-catalog-card ${statusClass}" data-reference-code="${escapeHtml(item.code)}">
          <p class="summary-label">${escapeHtml(item.code)}</p>
          <h4>${escapeHtml(item.name || item.code)}</h4>
          <p class="sectorial-catalog-status">${escapeHtml(statusLabel)}</p>
        </article>
      `;
    }).join('');
  }

  function renderSectorialHealthKpis(stats, quality) {
    const set = (id, value) => {
      const node = document.querySelector(id);
      if (node) node.textContent = Number(value || 0).toLocaleString('fr-FR');
    };
    set('#sectorial-health-kpi-total', stats?.total_facilities);
    set('#sectorial-health-kpi-hospitals', stats?.hospitals);
    set('#sectorial-health-kpi-centers', stats?.health_centers);
    set('#sectorial-health-kpi-posts', stats?.health_posts);
    set('#sectorial-health-kpi-geo', stats?.facilities_with_geometry);
    const qualityNode = document.querySelector('#sectorial-health-kpi-quality');
    if (qualityNode) {
      const score = quality?.quality_score ?? stats?.details?.quality_score;
      qualityNode.textContent = score == null ? '—' : `${Number(score).toLocaleString('fr-FR')} %`;
    }
  }

  function renderSectorialHealthTable(facilities, emptyMessage) {
    const tbody = document.querySelector('#sectorial-health-table-body');
    if (!tbody) return;
    const rows = asArray(facilities);
    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="decision-center-program-note">${escapeHtml(emptyMessage || 'Les données santé seront intégrées depuis une source officielle.')}</td></tr>`;
      return;
    }
    tbody.innerHTML = rows.map((item) => `
      <tr>
        <td>${escapeHtml(item.official_code || '—')}</td>
        <td>${escapeHtml(item.name || '—')}</td>
        <td>${escapeHtml(item.facility_type_name || item.facility_type_code || '—')}</td>
        <td>${escapeHtml(item.province_name || '—')}</td>
      </tr>
    `).join('');
  }

  function renderHealthDistributionList(containerId, distribution, emptyLabel) {
    const container = document.querySelector(containerId);
    if (!container) return;
    const entries = Object.entries(distribution || {}).sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0], 'fr'));
    if (!entries.length) {
      container.innerHTML = `<li>${escapeHtml(emptyLabel || 'Aucune donnée.')}</li>`;
      return;
    }
    container.innerHTML = entries.slice(0, 12).map(([label, count]) => `
      <li><span>${escapeHtml(label)}</span><strong>${Number(count).toLocaleString('fr-FR')}</strong></li>
    `).join('');
  }

  function renderSectorialHealthQuality(payload) {
    const list = document.querySelector('#sectorial-health-quality-list');
    const stats = payload?.statistics || {};
    const quality = payload?.quality || {};
    const details = stats.details || quality.details || {};
    if (list) {
      const items = [
        ['Score qualité', `${Number(quality.quality_score ?? details.quality_score ?? 0).toLocaleString('fr-FR')} %`],
        ['Géolocalisées', Number(stats.facilities_with_geometry || 0).toLocaleString('fr-FR')],
        ['Non géolocalisées', Number(stats.facilities_without_geometry || 0).toLocaleString('fr-FR')],
        ['Noms manquants', Number(details.missing_names || quality.missing_names || 0).toLocaleString('fr-FR')],
        ['Types manquants', Number(details.missing_types || quality.missing_types || 0).toLocaleString('fr-FR')],
        ['Doublons potentiels', Number(details.potential_duplicates || quality.potential_duplicates || 0).toLocaleString('fr-FR')],
      ];
      list.innerHTML = items.map(([label, value]) => `<li><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></li>`).join('');
    }
    renderHealthDistributionList('#sectorial-health-by-type', payload?.by_type || details.by_type || {}, 'Aucune répartition type.');
    renderHealthDistributionList('#sectorial-health-by-province', payload?.by_province || details.by_province || {}, 'Aucune répartition province.');
  }

  function setSectorialHealthMapMessage(message, visible) {
    const node = document.querySelector('#sectorial-health-map-message');
    if (!node) return;
    node.hidden = !visible;
    node.textContent = message || '';
  }

  function initializeSectorialHealthMap(geojsonPayload) {
    const shared = getShared();
    if (typeof global.L === 'undefined') return;
    const mapElement = document.querySelector('#sectorial-health-map');
    if (!mapElement) return;

    if (!decisionCenterState.healthMap) {
      decisionCenterState.healthMap = global.L.map(mapElement, {
        zoomControl: true,
        attributionControl: true,
        minZoom: 4,
        maxZoom: 14,
      }).setView([-2.8, 23.5], 5);

      global.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(decisionCenterState.healthMap);

      if (shared.fetchApiJson) {
        shared.fetchApiJson('/map/layers/provinces?limit=5000')
          .then((payload) => {
            const features = asArray(payload?.features);
            if (!features.length) return;
            global.L.geoJSON({ type: 'FeatureCollection', features }, {
              style: shared.styleProvinceFeature,
            }).addTo(decisionCenterState.healthMap);
          })
          .catch(() => {});
      }
    }

    if (decisionCenterState.healthFacilitiesLayer) {
      decisionCenterState.healthMap.removeLayer(decisionCenterState.healthFacilitiesLayer);
      decisionCenterState.healthFacilitiesLayer = null;
    }

    const features = asArray(geojsonPayload?.features);
    if (!features.length) {
      setSectorialHealthMapMessage(geojsonPayload?._meta?.message || 'Aucune donnée santé géolocalisée disponible', true);
      global.setTimeout(() => decisionCenterState.healthMap?.invalidateSize(), 0);
      return;
    }

    setSectorialHealthMapMessage('', false);
    const layer = global.L.geoJSON({ type: 'FeatureCollection', features }, {
      pointToLayer: (feature, latlng) => global.L.circleMarker(latlng, {
        radius: 3,
        color: '#b91c1c',
        weight: 1,
        fillColor: '#ef4444',
        fillOpacity: 0.75,
      }),
      onEachFeature: (feature, featureLayer) => {
        const props = feature?.properties || {};
        const quality = props.quality_score != null ? `${props.quality_score} %` : (props.data_quality || 'Import KMZ');
        featureLayer.bindPopup(`
          <div class="decision-map-popup">
            <strong>${escapeHtml(props.name || 'Structure sanitaire')}</strong><br>
            Type : ${escapeHtml(props.facility_type_name || props.facility_type_code || '')}<br>
            Province : ${escapeHtml(props.province_name || '')}<br>
            Zone de santé : ${escapeHtml(props.properties?.zonesante || props.zonesante || '')}<br>
            Aire de santé : ${escapeHtml(props.properties?.airesante || props.airesante || '')}<br>
            Localité : ${escapeHtml(props.locality_name || '')}<br>
            Source : ${escapeHtml(props.data_source || 'Référentiel Santé')}<br>
            Qualité donnée : ${escapeHtml(quality)}<br>
            <span class="map-popup-action">Voir fiche établissement</span>
          </div>
        `, { maxWidth: 280 });
        if (global.SigMapTooltips?.bind) {
          global.SigMapTooltips.bind(featureLayer, props, 'health', {
            onClick: () => { global.location.hash = 'decision-detail/sante'; },
          });
        } else {
          featureLayer.bindTooltip(
            `<strong>${escapeHtml(props.name || 'Structure')}</strong><br>${escapeHtml(props.facility_type_name || props.facility_type_code || '')}`,
            { sticky: false, direction: 'top', opacity: 1, className: 'sig-map-tooltip' },
          );
        }
      },
    }).addTo(decisionCenterState.healthMap);
    decisionCenterState.healthFacilitiesLayer = layer;
    try {
      const bounds = layer.getBounds();
      if (bounds?.isValid()) {
        decisionCenterState.healthMap.fitBounds(bounds, { padding: [16, 16], maxZoom: 7 });
      }
    } catch (_error) {
      // ignore invalid bounds
    }
    global.setTimeout(() => decisionCenterState.healthMap?.invalidateSize(), 0);
  }

  function loadSectorialReferentialsPanel(forceReload) {
    if (decisionCenterState.sectorialLoaded && !forceReload) {
      initializeSectorialHealthMap(decisionCenterState.healthGeojson || null);
      global.setTimeout(() => decisionCenterState.healthMap?.invalidateSize(), 0);
      return Promise.resolve();
    }
    if (decisionCenterState.sectorialLoading && !forceReload) return Promise.resolve();

    decisionCenterState.sectorialLoading = true;
    const catalogContainer = document.querySelector('#sectorial-catalog-grid');
    const shared = getShared();
    const canUseDb = typeof shared.canUseTelecomDbData === 'function' && shared.canUseTelecomDbData();

    if (catalogContainer) {
      catalogContainer.innerHTML = '<p class="decision-center-program-loading">Chargement du catalogue…</p>';
    }

    if (!canUseDb) {
      renderSectorialCatalogCards([
        { code: 'HEALTH', name: 'Référentiel Santé', status: 'in_progress' },
        { code: 'EDUCATION', name: 'Référentiel Éducation', status: 'partial' },
        { code: 'ENERGY', name: 'Référentiel Énergie', status: 'planned' },
        { code: 'ROADS', name: 'Référentiel Routes', status: 'planned' },
        { code: 'POPULATION', name: 'Référentiel Population', status: 'planned' },
      ]);
      renderSectorialHealthKpis({}, {});
      renderSectorialHealthTable([], 'Les données santé seront intégrées depuis une source officielle.');
      renderSectorialHealthQuality({});
      initializeSectorialHealthMap(null);
      decisionCenterState.sectorialLoaded = true;
      decisionCenterState.sectorialLoading = false;
      return Promise.resolve();
    }

    const fetchReference = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/reference/panel')
      : Promise.resolve(null);
    const fetchHealth = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/health/panel')
      : Promise.resolve(null);
    const fetchHealthLayer = typeof shared.fetchJson === 'function'
      ? shared.fetchJson('/api/health/layers/facilities?limit=2500')
      : Promise.resolve(null);

    return Promise.allSettled([fetchReference, fetchHealth, fetchHealthLayer])
      .then(([referenceResult, healthResult, layerResult]) => {
        const referencePayload = referenceResult.status === 'fulfilled' ? referenceResult.value : null;
        const healthPayload = healthResult.status === 'fulfilled' ? healthResult.value : null;
        const healthLayer = layerResult.status === 'fulfilled' ? layerResult.value : null;

        if (referencePayload?.sectorial_referentials || referencePayload?.catalog) {
          renderSectorialCatalogCards(referencePayload.sectorial_referentials || referencePayload.catalog || []);
        } else {
          renderSectorialCatalogCards([
            { code: 'HEALTH', name: 'Référentiel Santé', status: healthPayload?.statistics?.data_available ? 'active' : 'in_progress' },
            { code: 'EDUCATION', name: 'Référentiel Éducation', status: 'partial' },
            { code: 'ENERGY', name: 'Référentiel Énergie', status: 'planned' },
            { code: 'ROADS', name: 'Référentiel Routes', status: 'planned' },
            { code: 'POPULATION', name: 'Référentiel Population', status: 'planned' },
          ]);
        }

        renderSectorialHealthKpis(healthPayload?.statistics || {}, healthPayload?.quality || {});
        renderSectorialHealthTable(
          healthPayload?.facilities || [],
          healthPayload?.table_empty_message || (healthPayload?.statistics?.data_available ? null : 'Les données santé seront intégrées depuis une source officielle.'),
        );
        renderSectorialHealthQuality(healthPayload || {});
        decisionCenterState.healthGeojson = healthLayer;
        initializeSectorialHealthMap(healthLayer);
        decisionCenterState.sectorialLoaded = true;
      })
      .finally(() => {
        decisionCenterState.sectorialLoading = false;
        global.setTimeout(() => decisionCenterState.healthMap?.invalidateSize(), 0);
      });
  }

  function loadBusinessArchitecturePanel(forceReload) {
    if (decisionCenterState.programsLoading) return Promise.resolve();
    if (decisionCenterState.programsLoaded && !forceReload) return Promise.resolve();

    const container = document.querySelector('#decision-center-program-grid');
    if (!container) return Promise.resolve();

    decisionCenterState.programsLoading = true;
    container.innerHTML = '<p class="decision-center-program-loading">Chargement des programmes FDSU…</p>';

    return Promise.all([
      fetchBusinessJson('fdsu_programs.json'),
      fetchBusinessJson('program_status_catalog.json').catch(() => ({ statuses: [] })),
    ])
      .then(([payload, lifecyclePayload]) => {
        decisionCenterState.programStatusCatalog = lifecyclePayload;
        renderBusinessArchitecturePanel(payload, lifecyclePayload?.statuses);
      })
      .catch(() => {
        container.innerHTML = '<p class="decision-center-program-error">Référentiel métier indisponible (<code>data/business/fdsu_programs.json</code>).</p>';
      })
      .finally(() => {
        decisionCenterState.programsLoading = false;
      });
  }

  function asArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function getShared() {
    return global.SigFdsuShared || {};
  }

  function bindDecisionCenterTabs() {
    const tabList = document.querySelector('#decision-center-tabs');
    if (!tabList || tabList.dataset.bound === 'true') return;
    tabList.dataset.bound = 'true';

    tabList.querySelectorAll('[data-decision-tab]').forEach((button) => {
      button.addEventListener('click', () => {
        setDecisionCenterTab(button.dataset.decisionTab);
      });
    });
  }

  function setDecisionCenterTab(tabId) {
    if (!tabId) return;
    decisionCenterState.activeTab = tabId;

    document.querySelectorAll('[data-decision-tab]').forEach((button) => {
      const isActive = button.dataset.decisionTab === tabId;
      button.classList.toggle('is-active', isActive);
      button.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    document.querySelectorAll('[data-decision-tab-panel]').forEach((panel) => {
      const isActive = panel.dataset.decisionTabPanel === tabId;
      panel.classList.toggle('is-active', isActive);
      if (isActive) {
        panel.hidden = false;
        panel.removeAttribute('hidden');
      } else {
        panel.hidden = true;
        panel.setAttribute('hidden', '');
      }
    });

    if (tabId === 'vue-nationale') {
      loadNationalPanel(false);
      initializeDecisionCenterNationalMap();
      mountDecisionCenterTst();
      loadBusinessArchitecturePanel(false);
      loadSites40ProgramPanel(false);
      loadSites300ProgramPanel(false);
      loadTelecomReferentialPanel(false);
      loadSpatialAnalysisPanel(false);
      loadCcnDecisionExtensions(false);
    }

    if (tabId === 'simulations' && typeof global.initializeDecisionScenariosModule === 'function') {
      global.initializeDecisionScenariosModule();
    }

    if (tabId === 'priorisation') {
      loadDecisionEnginePanel(false);
      global.setTimeout(() => {
        decisionCenterState.decisionEngineMap?.invalidateSize();
      }, 120);
    }

    if (tabId === 'referentiel-national') {
      loadMasterRegistryPanel(false);
    }

    if (tabId === 'referentiels-sectoriels') {
      loadSectorialReferentialsPanel(false);
      global.setTimeout(() => {
        decisionCenterState.healthMap?.invalidateSize();
      }, 120);
    }
  }

  function setupDecisionCenterResizeObserver(mapElement) {
    if (!mapElement || decisionCenterState.resizeObserver) return;
    const invalidate = () => {
      if (decisionCenterState.map) {
        global.requestAnimationFrame(() => decisionCenterState.map.invalidateSize());
      }
    };

    if (typeof global.ResizeObserver !== 'undefined') {
      decisionCenterState.resizeObserver = new global.ResizeObserver(invalidate);
      decisionCenterState.resizeObserver.observe(mapElement);
    }

    if (decisionCenterState.windowResizeBound !== true) {
      decisionCenterState.windowResizeBound = true;
      global.addEventListener('resize', invalidate);
    }
  }

  function mountDecisionCenterTst() {
    const host = document.querySelector('#decision-center-tst-host');
    if (!host || !global.TerritorialSummary?.mount) return;
    if (decisionCenterState.tstInstance?.resize) {
      decisionCenterState.tstInstance.resize();
      return;
    }
    const run = () => global.TerritorialSummary.mount(host, {
      metric: global.TerritorialContext?.get()?.metric || 'priority',
      level: 'province',
      preserveContext: true,
      showLegend: true,
      showKpis: true,
      allowDrilldown: true,
      onSelectionChange: (entity) => {
        if (global.TerritorialContext) global.TerritorialContext.select(entity);
      },
    }).then((api) => {
      decisionCenterState.tstInstance = api;
    }).catch(() => {
      decisionCenterState.tstInstance = null;
      host.classList.add('tst-root');
      host.innerHTML = global.UxPremium?.stateHtml
        ? global.UxPremium.stateHtml('error', 'TST indisponible', 'Vérifier l’API /api/territorial-summary.')
        : '<p class="tst-status is-error">TST indisponible</p>';
      // Une nouvelle tentative après chargement API
      global.setTimeout(() => {
        if (!decisionCenterState.tstInstance) run();
      }, 1500);
    });
    run();
  }

  function initializeDecisionCenterNationalMap() {
    // Conservé pour compatibilité Priorisation / appels legacy — vue nationale utilise le TST.
    const shared = getShared();
    if (typeof global.L === 'undefined' || !shared.fetchApiJson) return;
    const mapElement = document.querySelector('#decision-center-national-map');
    if (!mapElement) return;

    setupDecisionCenterResizeObserver(mapElement);

    if (decisionCenterState.map) {
      global.setTimeout(() => decisionCenterState.map.invalidateSize(), 0);
      return;
    }

    decisionCenterState.map = global.L.map(mapElement, {
      zoomControl: true,
      attributionControl: true,
      minZoom: 4,
      maxZoom: 14,
    }).setView([-2.8, 23.5], 5);

    global.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(decisionCenterState.map);

    decisionCenterState.layers = {
      rdcBoundary: global.L.geoJSON(null, { style: shared.styleRdcBoundaryFeature }),
      provinces: global.L.geoJSON(null, {
        style: shared.styleProvinceFeature,
        onEachFeature: (feature, layer) => {
          if (global.SigMapTooltips?.bind) {
            global.SigMapTooltips.bind(layer, feature, 'province', {
              interactive: false,
              direction: 'auto',
            });
          } else if (layer.bindTooltip) {
            const name = feature?.properties?.nom || feature?.properties?.name || 'Province';
            layer.bindTooltip(String(name), { sticky: false, direction: 'auto', className: 'sig-map-tooltip' });
          }
        },
      }),
    };

    const boundaryPromise = shared.fetchApiJson
      ? shared.fetchJson('/geodata/rdc_boundary.geojson').catch(() => null)
      : Promise.resolve(null);

    boundaryPromise.then((geojson) => {
      if (geojson?.features?.length) {
        decisionCenterState.layers.rdcBoundary.clearLayers();
        decisionCenterState.layers.rdcBoundary.addData(geojson);
        decisionCenterState.layers.rdcBoundary.addTo(decisionCenterState.map);
      }
    });

    shared.fetchApiJson('/map/layers/provinces?limit=5000')
      .then((payload) => {
        const features = asArray(payload?.features);
        if (!features.length) return;
        decisionCenterState.layers.provinces.clearLayers();
        decisionCenterState.layers.provinces.addData({ type: 'FeatureCollection', features });
        decisionCenterState.layers.provinces.addTo(decisionCenterState.map);
        const bounds = decisionCenterState.layers.provinces.getBounds();
        if (bounds.isValid()) {
          decisionCenterState.map.fitBounds(bounds, { padding: [16, 16] });
        }
      })
      .catch(() => {})
      .finally(() => {
        decisionCenterState.mapInitialized = true;
        if (global.UxPremium?.mountMapLegend) {
          global.UxPremium.mountMapLegend('#decision-center-national-map', {
            id: 'ux-legend-decision-national',
            title: 'Légende',
            sectionTitle: 'Couches',
            items: [
              { className: 'is-poly', label: 'Province' },
              { className: 'is-site', label: 'Site FDSU (si affiché)' },
            ],
          });
        }
        global.setTimeout(() => decisionCenterState.map?.invalidateSize(), 0);
      });
  }

  function initializeDecisionCenterModule() {
    const panel = document.querySelector('#decision-view-panel');
    if (!panel) return;

    bindDecisionCenterTabs();
    bindDecisionBusinessInteractions();
    bindSites40MapButton();
    bindSpatialAnalysisRunButton();
    bindDecisionEngineFilters();
    bindDecisionEngineRecomputeButton();
    if (global.Edvs?.mountPresentationButton) {
      global.Edvs.mountPresentationButton('#decision-edvs-presentation-slot');
    }

    if (!decisionCenterState.initialized) {
      setDecisionCenterTab('vue-nationale');
      decisionCenterState.initialized = true;
      return;
    }

    if (decisionCenterState.activeTab === 'vue-nationale') {
      loadNationalPanel(false);
      mountDecisionCenterTst();
      loadBusinessArchitecturePanel(false);
      loadSites40ProgramPanel(false);
      loadSites300ProgramPanel(false);
      loadTelecomReferentialPanel(false);
      loadSpatialAnalysisPanel(false);
    }
  }

  global.decisionCenterState = decisionCenterState;
  global.initializeDecisionCenterModule = initializeDecisionCenterModule;
  global.setDecisionCenterTab = setDecisionCenterTab;
  global.loadNationalPanel = loadNationalPanel;
  global.loadFdsuBusinessArchitecture = loadBusinessArchitecturePanel;
  global.loadFdsuSites40Program = loadSites40ProgramPanel;
  global.loadFdsuSites300Program = loadSites300ProgramPanel;
  global.loadTelecomReferentialPanel = loadTelecomReferentialPanel;
  global.loadSpatialAnalysisPanel = loadSpatialAnalysisPanel;
  global.loadDecisionEnginePanel = loadDecisionEnginePanel;
  global.loadSectorialReferentialsPanel = loadSectorialReferentialsPanel;
  global.loadPriorityMatrix = loadPriorityMatrix;
  global.getCcnDecisionExtensions = getCcnDecisionExtensions;
  global.FDSU_BUSINESS_DATA_BASE = BUSINESS_DATA_BASE;
  global.FDSU_PROGRAMS_DATA_BASE = PROGRAMS_DATA_BASE;
  global.FDSU_PROGRAMS_PATH = FDSU_PROGRAMS_PATH;
  global.FDSU_SITES_40_DATA_PATH = SITES_40_DATA_PATH;

  // Secours : si le Centre de Décision est déjà affiché (hash #decision-view) avant le boot app.js,
  // lier immédiatement les onglets pour que « Référentiels sectoriels » / Santé restent accessibles.
  function ensureDecisionCenterReady() {
    const panel = document.querySelector('#decision-view-panel');
    if (!panel || panel.classList.contains('hidden')) return;
    if (decisionCenterState.initialized) return;
    initializeDecisionCenterModule();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensureDecisionCenterReady);
  } else {
    ensureDecisionCenterReady();
  }
})(window);
