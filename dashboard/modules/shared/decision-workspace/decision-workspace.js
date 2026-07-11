/**
 * SIG-FDSU — Decision Workspace (v1.1)
 * Socle partagé d’analyse unifiée. N’écrase pas les modules existants :
 * s’attache à #decision-detail-panel et synchronise sélection / fil / cartes.
 *
 * Domaines futurs (économie, énergie, routes, santé, télécoms, éducation, marchés)
 * via registerDomainAdapter(domainId, adapter).
 */
(function initDecisionWorkspace(global) {
  const LEVELS = [
    { id: 'rdc', label: 'RDC' },
    { id: 'province', label: 'Province' },
    { id: 'territoire', label: 'Territoire' },
    { id: 'collectivite', label: 'Collectivité' },
    { id: 'groupement', label: 'Groupement' },
    { id: 'localite', label: 'Localité' },
    { id: 'site', label: 'Site' },
  ];

  const DOMAIN_REGISTRY = Object.create(null);

  const state = {
    version: '1.1.0',
    attached: false,
    kpiCode: null,
    kpiSlug: null,
    returnHash: 'decision-view',
    trail: [{ level: 'rdc', id: 'rdc', label: 'RDC' }],
    selection: null,
    listeners: Object.create(null),
    lastPayload: null,
    syncToken: 0,
  };

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function on(event, handler) {
    if (!state.listeners[event]) state.listeners[event] = [];
    state.listeners[event].push(handler);
    return () => {
      state.listeners[event] = (state.listeners[event] || []).filter((fn) => fn !== handler);
    };
  }

  function emit(event, detail) {
    (state.listeners[event] || []).forEach((fn) => {
      try { fn(detail); } catch (_err) { /* isolé */ }
    });
  }

  function registerDomainAdapter(domainId, adapter) {
    if (!domainId || !adapter) return;
    DOMAIN_REGISTRY[String(domainId)] = adapter;
  }

  function getDomainAdapter(domainId) {
    return DOMAIN_REGISTRY[String(domainId)] || null;
  }

  function defaultTrail() {
    return [{ level: 'rdc', id: 'rdc', label: 'RDC' }];
  }

  function normalizeTrail(trail) {
    if (!Array.isArray(trail) || !trail.length) return defaultTrail();
    return trail.map((step) => ({
      level: step.level || 'rdc',
      id: step.id != null ? String(step.id) : step.level,
      label: step.label || LEVELS.find((l) => l.id === step.level)?.label || String(step.id || ''),
    }));
  }

  function trailFromEntity(entity) {
    const trail = defaultTrail();
    if (!entity) return trail;
    const push = (level, id, label) => {
      if (id == null || id === '') return;
      trail.push({ level, id: String(id), label: label || String(id) });
    };
    push('province', entity.province_id || entity.province, entity.province_name || entity.province);
    push('territoire', entity.territoire_id || entity.territoire, entity.territoire_name || entity.territoire);
    push('collectivite', entity.collectivite_id || entity.collectivite, entity.collectivite_name || entity.collectivite);
    push('groupement', entity.groupement_id || entity.groupement, entity.groupement_name || entity.groupement);
    push('localite', entity.localite_id || entity.localite || entity.village, entity.localite_name || entity.localite || entity.village);
    if (entity.site_id || entity.id || entity.code) {
      const siteId = entity.site_id || entity.id || entity.code;
      push('site', siteId, entity.name || entity.site_name || `Site ${siteId}`);
    }
    return trail;
  }

  function ensureShell() {
    const panel = document.querySelector('#decision-detail-panel');
    if (!panel) return null;

    let chrome = panel.querySelector('#decision-workspace-chrome');
    if (!chrome) {
      chrome = document.createElement('div');
      chrome.id = 'decision-workspace-chrome';
      chrome.className = 'dw-chrome';
      chrome.setAttribute('data-decision-workspace', '1.1');
      chrome.innerHTML = `
        <nav class="dw-trail" id="decision-workspace-trail" aria-label="Fil d’analyse"></nav>
        <p class="dw-sync" id="decision-workspace-sync" aria-live="polite">Espace d’analyse — sélection synchronisée</p>
        <div class="dw-sections" id="decision-workspace-sections">
          <section class="dw-section" id="decision-workspace-summary" data-dw-section="summary" hidden>
            <h3>Résumé exécutif</h3>
            <div class="dw-section-body" id="decision-workspace-summary-body"></div>
          </section>
          <section class="dw-section" id="decision-workspace-reco" data-dw-section="recommendations" hidden>
            <h3>Recommandations</h3>
            <div class="dw-section-body" id="decision-workspace-reco-body"></div>
          </section>
          <section class="dw-section" id="decision-workspace-history" data-dw-section="history" hidden>
            <h3>Historique</h3>
            <div class="dw-section-body" id="decision-workspace-history-body"></div>
          </section>
          <section class="dw-section dw-section-scaffold" id="decision-workspace-compare" data-dw-section="comparison" hidden>
            <h3>Comparaison</h3>
            <div class="dw-section-body" id="decision-workspace-compare-body"></div>
          </section>
        </div>
      `;
      const topbar = panel.querySelector('.decision-detail-topbar');
      if (topbar && topbar.nextSibling) {
        panel.insertBefore(chrome, topbar.nextSibling);
      } else {
        panel.prepend(chrome);
      }
    }

    panel.classList.add('is-decision-workspace');
    document.body.classList.add('decision-workspace-open');
    state.attached = true;
    return chrome;
  }

  function renderTrail() {
    const host = document.querySelector('#decision-workspace-trail');
    if (!host) return;
    const trail = normalizeTrail(state.trail);
    host.innerHTML = trail.map((step, index) => {
      const isLast = index === trail.length - 1;
      return `
        <button type="button"
          class="dw-trail-step${isLast ? ' is-current' : ''}"
          data-dw-trail-index="${index}"
          data-dw-level="${escapeHtml(step.level)}"
          data-dw-id="${escapeHtml(step.id)}"
          aria-current="${isLast ? 'step' : 'false'}">
          <span class="dw-trail-level">${escapeHtml(LEVELS.find((l) => l.id === step.level)?.label || step.level)}</span>
          <strong>${escapeHtml(step.label)}</strong>
        </button>
        ${isLast ? '' : '<span class="dw-trail-sep" aria-hidden="true">→</span>'}
      `;
    }).join('');
  }

  function setSyncMessage(text) {
    const el = document.querySelector('#decision-workspace-sync');
    if (el) el.textContent = text;
  }

  function applyFiltersFromTrail() {
    const provinceInput = document.querySelector('#decision-detail-province');
    const territoireInput = document.querySelector('#decision-detail-territoire');
    const provinceStep = state.trail.find((s) => s.level === 'province');
    const territoireStep = state.trail.find((s) => s.level === 'territoire');
    if (provinceInput) {
      provinceInput.value = provinceStep && provinceStep.id !== 'rdc' ? (provinceStep.label || provinceStep.id) : '';
    }
    if (territoireInput) {
      territoireInput.value = territoireStep ? (territoireStep.label || territoireStep.id) : '';
    }
  }

  function highlightTableSelection() {
    const body = document.querySelector('#decision-detail-table-body');
    if (!body) return;
    const selectedId = state.selection?.site_id || state.selection?.id || state.selection?.code;
    body.querySelectorAll('tr').forEach((row) => {
      const btn = row.querySelector('[data-open-item]');
      const id = btn?.getAttribute('data-open-item');
      const match = selectedId != null && id != null && String(id) === String(selectedId);
      row.classList.toggle('is-selected', Boolean(match));
      if (match) row.setAttribute('data-dw-selected', 'true');
      else row.removeAttribute('data-dw-selected');
    });
  }

  function renderContextPanels(payload) {
    const summaryBody = document.querySelector('#decision-workspace-summary-body');
    const summarySection = document.querySelector('#decision-workspace-summary');
    const recoBody = document.querySelector('#decision-workspace-reco-body');
    const recoSection = document.querySelector('#decision-workspace-reco');
    const historyBody = document.querySelector('#decision-workspace-history-body');
    const historySection = document.querySelector('#decision-workspace-history');
    const compareBody = document.querySelector('#decision-workspace-compare-body');
    const compareSection = document.querySelector('#decision-workspace-compare');

    const header = payload?.header || {};
    const explain = payload?.explain || {};
    const selection = state.selection;

    if (summarySection && summaryBody) {
      summarySection.hidden = false;
      const selLine = selection
        ? `${selection.name || selection.site_name || selection.id || 'Entité'} — ${selection.province || '—'} / ${selection.territoire || '—'}`
        : 'Aucune entité sélectionnée — cliquez une ligne ou un marqueur.';
      summaryBody.innerHTML = `
        <div class="dw-summary-grid">
          <article class="dw-summary-card">
            <p class="dw-kicker">Indicateur</p>
            <strong>${escapeHtml(header.title || state.kpiCode || 'Analyse')}</strong>
            <span>${escapeHtml(header.subtitle || header.definition || '')}</span>
          </article>
          <article class="dw-summary-card">
            <p class="dw-kicker">Sélection</p>
            <strong>${escapeHtml(selLine)}</strong>
            <span>Synchronisé avec carte, liste et filtres</span>
          </article>
          <article class="dw-summary-card">
            <p class="dw-kicker">Confiance</p>
            <strong>${escapeHtml(explain.confidence || header.confidence || '—')}</strong>
            <span>${escapeHtml(explain.recommended_action || 'Action recommandée dès qu’une entité est choisie')}</span>
          </article>
        </div>
      `;
    }

    if (recoSection && recoBody) {
      recoSection.hidden = false;
      const action = explain.recommended_action;
      const why = explain.why;
      if (action || why) {
        recoBody.innerHTML = `
          ${why ? `<p><strong>Pourquoi :</strong> ${escapeHtml(why)}</p>` : ''}
          ${action ? `<p><strong>Recommandation :</strong> ${escapeHtml(action)}</p>` : ''}
          <p class="dw-hint">Les actions opérationnelles restent disponibles dans la barre d’actions de l’analyse détaillée et le dossier de décision (DXL).</p>
        `;
      } else if (global.UxPremium?.stateHtml) {
        recoBody.innerHTML = global.UxPremium.stateHtml(
          'empty',
          'Recommandations en contexte',
          'Sélectionnez un site ou une localité pour affiner la recommandation.',
        );
      } else {
        recoBody.innerHTML = '<p>Sélectionnez une entité pour afficher une recommandation.</p>';
      }
    }

    if (historySection && historyBody) {
      historySection.hidden = false;
      const stamp = new Date().toLocaleString('fr-FR');
      historyBody.innerHTML = `
        <ul class="dw-history-list">
          <li><time>${escapeHtml(stamp)}</time> Ouverture analyse — ${escapeHtml(state.kpiCode || 'KPI')}</li>
          ${state.selection ? `<li><time>${escapeHtml(stamp)}</time> Sélection — ${escapeHtml(state.selection.name || state.selection.id || '')}</li>` : ''}
        </ul>
        <p class="dw-hint">Historique session (socle v1.1) — persistance Master Registry / connaissances prévue ultérieurement.</p>
      `;
    }

    if (compareSection && compareBody) {
      compareSection.hidden = false;
      compareBody.innerHTML = global.UxPremium?.stateHtml
        ? global.UxPremium.stateHtml(
          'empty',
          'Comparaison — socle prêt',
          'Ce panneau accueillera la comparaison multi-entités / multi-domaines (économie, énergie, routes, santé, télécoms, éducation, marchés).',
          'Aucun scénario inventé.',
        )
        : '<p>Comparaison — socle v1.1 (à brancher).</p>';
    }
  }

  function selectEntity(entity, options = {}) {
    state.selection = entity || null;
    state.syncToken += 1;
    if (entity && options.updateTrail !== false) {
      state.trail = trailFromEntity(entity);
    }
    renderTrail();
    highlightTableSelection();
    if (options.applyFilters !== false) applyFiltersFromTrail();
    renderContextPanels(state.lastPayload);
    const label = entity?.name || entity?.site_name || entity?.id || 'aucune';
    setSyncMessage(`Sélection synchronisée · ${label} · jeton ${state.syncToken}`);
    emit('selection:change', { selection: state.selection, trail: state.trail, syncToken: state.syncToken });
  }

  function setTrail(trail, options = {}) {
    state.trail = normalizeTrail(trail);
    renderTrail();
    if (options.applyFilters !== false) applyFiltersFromTrail();
    setSyncMessage(`Fil d’analyse · ${state.trail.map((s) => s.label).join(' → ')}`);
    emit('trail:change', { trail: state.trail });
  }

  function drillToTrailIndex(index) {
    const next = normalizeTrail(state.trail).slice(0, Math.max(1, index + 1));
    state.trail = next;
    const last = next[next.length - 1];
    if (last?.level === 'rdc') {
      state.selection = null;
    } else if (last && (!state.selection || String(state.selection.id) !== String(last.id))) {
      state.selection = {
        id: last.id,
        name: last.label,
        province: next.find((s) => s.level === 'province')?.label,
        territoire: next.find((s) => s.level === 'territoire')?.label,
        [last.level]: last.label,
        [`${last.level}_id`]: last.id,
      };
    }
    renderTrail();
    applyFiltersFromTrail();
    highlightTableSelection();
    renderContextPanels(state.lastPayload);
    setSyncMessage(`Fil recentré · ${next.map((s) => s.label).join(' → ')}`);
    emit('trail:navigate', { trail: state.trail, index });

    // Recharger le détail avec filtres spatiaux (contrat API inchangé)
    if (typeof global.decisionDetailState !== 'undefined' && state.kpiCode) {
      const applyBtn = document.querySelector('#decision-detail-apply-filters');
      if (applyBtn) applyBtn.click();
      else if (typeof global.initializeDecisionDetailModule === 'function') {
        // fallback : le module détail écoute déjà les filtres
      }
    }
  }

  function bindChromeEvents() {
    const panel = document.querySelector('#decision-detail-panel');
    if (!panel || panel.dataset.dwBound === 'true') return;
    panel.dataset.dwBound = 'true';

    panel.addEventListener('click', (event) => {
      const target = event.target;
      if (!(target instanceof global.HTMLElement)) return;

      const trailBtn = target.closest('[data-dw-trail-index]');
      if (trailBtn) {
        const idx = Number(trailBtn.getAttribute('data-dw-trail-index'));
        if (!Number.isNaN(idx)) drillToTrailIndex(idx);
        return;
      }

      const row = target.closest('#decision-detail-table-body tr');
      if (row && !target.closest('[data-open-item], [data-detail-action]')) {
        const btn = row.querySelector('[data-open-item]');
        if (!btn) return;
        const id = btn.getAttribute('data-open-item');
        const program = btn.getAttribute('data-program');
        const cells = [...row.querySelectorAll('td')].map((td) => td.textContent?.trim() || '');
        selectEntity({
          id,
          site_id: id,
          name: cells[0] || `Site ${id}`,
          program_code: program || undefined,
          province: document.querySelector('#decision-detail-province')?.value || undefined,
          territoire: document.querySelector('#decision-detail-territoire')?.value || undefined,
        });
      }
    });
  }

  function attach(options = {}) {
    ensureShell();
    bindChromeEvents();
    if (options.kpiCode) state.kpiCode = options.kpiCode;
    if (options.returnHash) state.returnHash = options.returnHash;
    if (options.trail) state.trail = normalizeTrail(options.trail);
    else if (!state.trail?.length) state.trail = defaultTrail();
    renderTrail();
    setSyncMessage(options.syncMessage || 'Espace d’analyse prêt — carte, liste et KPI synchronisables');
    if (global.UxPremium?.mountMapLegend) {
      global.UxPremium.mountMapLegend('#decision-detail-map', {
        id: 'ux-legend-decision-detail',
        title: 'Légende',
        items: [
          { className: 'is-critical', label: 'Priorité critique' },
          { className: 'is-high', label: 'Priorité élevée' },
          { className: 'is-medium', label: 'Priorité moyenne' },
          { className: 'is-low', label: 'Priorité faible' },
        ],
      });
    }
    emit('attach', { kpiCode: state.kpiCode });
    return state;
  }

  function syncFromDetailPayload(payload, kpiCode) {
    state.lastPayload = payload || null;
    state.kpiCode = kpiCode || state.kpiCode || payload?.header?.kpi_code || null;
    attach({ kpiCode: state.kpiCode });
    renderContextPanels(payload);

    // KPI secondaires → strip interactif si EDVS dispo
    const secondary = payload?.secondary_kpis;
    if (Array.isArray(secondary) && secondary.length && global.Edvs?.mountKpiStrip) {
      const host = document.querySelector('#decision-detail-secondary');
      if (host && !host.dataset.dwKpiMounted) {
        // ne remplace pas le rendu existant ; marqueur pour futurs adapters
        host.dataset.dwReady = 'true';
      }
    }

    // Charts déjà rendus par decision-detail ; enrichir via EdvsCharts si payload.charts structuré
    emit('payload:sync', { payload, kpiCode: state.kpiCode });
    highlightTableSelection();
  }

  function detach() {
    document.body.classList.remove('decision-workspace-open');
    const panel = document.querySelector('#decision-detail-panel');
    if (panel) panel.classList.remove('is-decision-workspace');
    state.attached = false;
    emit('detach', {});
  }

  /**
   * Point d’entrée unifié — conserve #decision-detail/<slug> (ou alias #decision-workspace/).
   */
  function open(context = {}) {
    const kpiKey = context.kpiKey || context.kpiCode || context.kpi;
    state.returnHash = context.returnHash || 'decision-view';
    state.trail = normalizeTrail(context.trail || defaultTrail());
    state.selection = context.entity || context.selection || null;
    if (state.selection) state.trail = trailFromEntity(state.selection);

    try {
      global.sessionStorage?.setItem('fdsu.decisionWorkspace.context', JSON.stringify({
        kpiKey,
        returnHash: state.returnHash,
        trail: state.trail,
        selection: state.selection,
      }));
    } catch (_err) { /* private mode */ }

    attach({ kpiCode: kpiKey, returnHash: state.returnHash, trail: state.trail });

    if (kpiKey && typeof global.openDecisionDetail === 'function') {
      global.openDecisionDetail(kpiKey);
    } else if (kpiKey) {
      const slug = String(kpiKey).replace(/_/g, '-');
      const useAlias = context.useWorkspaceHash === true;
      global.location.hash = useAlias ? `decision-workspace/${slug}` : `decision-detail/${slug}`;
    }
  }

  function restoreContextFromStorage() {
    try {
      const raw = global.sessionStorage?.getItem('fdsu.decisionWorkspace.context');
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (_err) {
      return null;
    }
  }

  function bindMapFeatureSelection(props) {
    if (!props) return;
    selectEntity({
      id: props.id || props.site_id || props.code,
      site_id: props.id || props.site_id || props.code,
      name: props.name || props.site_name,
      province: props.province,
      territoire: props.territoire,
      program_code: props.program_code,
      priority_level: props.priority_level,
      kind: props.kind,
    }, { applyFilters: false });
  }

  global.DecisionWorkspace = {
    version: state.version,
    LEVELS,
    state,
    on,
    emit,
    attach,
    detach,
    open,
    selectEntity,
    setTrail,
    drillToTrailIndex,
    syncFromDetailPayload,
    bindMapFeatureSelection,
    trailFromEntity,
    restoreContextFromStorage,
    registerDomainAdapter,
    getDomainAdapter,
    ensureShell,
  };
})(typeof window !== 'undefined' ? window : globalThis);
