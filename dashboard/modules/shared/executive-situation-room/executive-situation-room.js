/**
 * Executive Situation Room v1.0 — Salle de Pilotage DG
 * Parcours : Situation → Pourquoi → Où → Que faire → Impact → Décider
 * Réutilise EDVS widgets + TST — une carte Leaflet (TST), chargement progressif.
 */
(function initExecutiveSituationRoom(global) {
  const API_BASE = `${global.location.protocol}//${global.location.hostname}:8001`;

  const state = {
    payload: null,
    panels: {},
    tstInstance: null,
    presentTimer: null,
    presentStep: -1,
    presenting: false,
  };

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function fetchJson(path, timeoutMs = 20000) {
    const ctrl = new AbortController();
    const timer = global.setTimeout(() => ctrl.abort(), timeoutMs);
    return fetch(`${API_BASE}${path}`, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      signal: ctrl.signal,
    })
      .then((r) => {
        if (!r.ok) throw new Error(path);
        return r.json();
      })
      .finally(() => global.clearTimeout(timer));
  }

  function softError(title, detail, anchorId) {
    const idAttr = anchorId ? ` id="${escapeHtml(anchorId)}"` : '';
    return `<div class="esr-soft-error" ${idAttr}><strong>${escapeHtml(title)}</strong><p>${escapeHtml(detail || '')}</p></div>`;
  }

  function softLoading(label, anchorId) {
    const idAttr = anchorId ? ` id="${escapeHtml(anchorId)}"` : '';
    return `<div class="esr-loading" ${idAttr} aria-busy="true">${escapeHtml(label || 'Chargement…')}</div>`;
  }

  function navigate(hash) {
    if (!hash) return;
    global.location.hash = String(hash).replace(/^#/, '');
  }

  function openExplain(title, body, source) {
    let drawer = document.querySelector('#esr-explain-drawer');
    if (!drawer) {
      drawer = document.createElement('aside');
      drawer.id = 'esr-explain-drawer';
      drawer.className = 'esr-explain-drawer';
      drawer.setAttribute('role', 'dialog');
      drawer.setAttribute('aria-label', 'Explication');
      document.body.appendChild(drawer);
    }
    drawer.innerHTML = `
      <header>
        <h3>Pourquoi ?</h3>
        <button type="button" class="secondary-button" data-esr-close-explain aria-label="Fermer">Fermer</button>
      </header>
      <strong>${escapeHtml(title || '')}</strong>
      <p>${escapeHtml(body || 'Explication indisponible pour cet élément.')}</p>
      ${source ? `<small>Source : ${escapeHtml(source)}</small>` : ''}
    `;
    drawer.hidden = false;
    drawer.querySelector('[data-esr-close-explain]')?.addEventListener('click', () => {
      drawer.hidden = true;
    });
  }

  function renderBriefing(briefing) {
    if (!briefing) return softError('Briefing indisponible', 'Le service de briefing n’a pas répondu.');
    const factors = (briefing.factors || []).map((f) => `<li>${escapeHtml(f.text || f)}</li>`).join('');
    const updates = (briefing.since_last_update || []).map((u) => `<li>${escapeHtml(u.text || u)}</li>`).join('');
    return `
      <section class="esr-card esr-briefing" id="esr-briefing" data-esr-step="briefing">
        <header class="esr-card-header">
          <div>
            <p class="esr-kicker">Executive Briefing</p>
            <h2>${escapeHtml(briefing.title || 'Executive Briefing')}</h2>
          </div>
          <button type="button" class="secondary-button esr-why-btn" data-esr-why
            data-why-title="Executive Briefing"
            data-why-body="${escapeHtml(briefing.narrative || '')}"
            data-why-source="Cockpit EDVS · NCI · NSME · Decision Engine">Pourquoi ?</button>
        </header>
        <p class="esr-headline">${escapeHtml(briefing.headline || '')}</p>
        ${(briefing.paragraphs || []).slice(1).map((p) => `<p>${escapeHtml(p)}</p>`).join('')}
        ${factors ? `<div class="esr-bullets"><p class="esr-kicker">Facteurs</p><ul>${factors}</ul></div>` : ''}
        ${updates ? `<div class="esr-bullets"><p class="esr-kicker">Depuis la dernière consolidation</p><ul>${updates}</ul></div>` : ''}
        <p class="esr-anomaly">${escapeHtml(briefing.anomaly_line || '')}</p>
      </section>
    `;
  }

  function renderNational(national) {
    if (!national) return softError('Situation nationale indisponible', '');
    const cards = (national.cards || []).map((c) => `
      <article class="esr-nation-card" data-status="${escapeHtml(c.status || '')}" data-esr-nav="${escapeHtml(c.hash || '')}" tabindex="0" role="button">
        <header>
          <span>${escapeHtml(c.label)}</span>
          <button type="button" class="esr-why-btn" data-esr-why
            data-why-title="${escapeHtml(c.label)}"
            data-why-body="${escapeHtml(c.explain || '')}"
            data-why-source="${escapeHtml(c.source || '')}">Pourquoi ?</button>
        </header>
        <strong>${escapeHtml(c.value_display != null ? c.value_display : '—')}</strong>
        ${c.note ? `<small>${escapeHtml(c.note)}</small>` : ''}
        <p class="esr-card-cta">Ouvrir l’analyse →</p>
      </article>
    `).join('');
    return `
      <section class="esr-card" id="esr-national" data-esr-step="situation">
        <header class="esr-card-header">
          <h3>${escapeHtml(national.title || 'Situation nationale')}</h3>
        </header>
        <div class="esr-nation-grid">${cards || '<p class="esr-empty">Aucun indicateur</p>'}</div>
      </section>
    `;
  }

  function renderAlerts(alerts) {
    if (!alerts) return softError('Alertes indisponibles', '');
    const cats = (alerts.categories || []).map((c) => `
      <span class="esr-alert-pill" data-sev="${escapeHtml(c.id)}">${escapeHtml(c.label)} · ${Number(c.count || 0)}</span>
    `).join('');
    const items = (alerts.items || []).map((a) => `
      <li class="esr-alert-item" data-severity="${escapeHtml(a.severity || 'info')}">
        <div>
          <strong>${escapeHtml(a.title)}</strong>
          <p>${escapeHtml(a.message || '')}</p>
        </div>
        <div class="esr-alert-actions">
          <button type="button" class="secondary-button esr-why-btn" data-esr-why
            data-why-title="${escapeHtml(a.title)}"
            data-why-body="${escapeHtml(a.why || '')}"
            data-why-source="Alertes ESR">Pourquoi ?</button>
          <button type="button" class="primary-button" data-esr-nav="${escapeHtml(a.hash || 'decision-view')}">Analyser</button>
        </div>
      </li>
    `).join('');
    return `
      <section class="esr-card" id="esr-alerts" data-esr-step="alerts">
        <header class="esr-card-header">
          <h3>${escapeHtml(alerts.title || 'Alertes nationales')}</h3>
          <div class="esr-alert-pills">${cats}</div>
        </header>
        <ul class="esr-alert-list">${items || '<li class="esr-empty">Aucune alerte</li>'}</ul>
      </section>
    `;
  }

  function renderQuestions(questions) {
    if (!questions) return softError('Questions indisponibles', '');
    const list = (questions.questions || []).map((q) => `
      <button type="button" class="esr-question" data-esr-nav="${escapeHtml(q.hash || '')}">
        <strong>${escapeHtml(q.question || q.title)}</strong>
        <span>${escapeHtml(q.answer_hint || 'Ouvre l’analyse correspondante')}</span>
      </button>
    `).join('');
    return `
      <section class="esr-card" id="esr-questions" data-esr-step="why">
        <header class="esr-card-header">
          <h3>${escapeHtml(questions.title || 'Posez votre question')}</h3>
          <small class="esr-muted">${escapeHtml(questions.placeholder || '')}</small>
        </header>
        <div class="esr-questions">${list || '<p class="esr-empty">Aucune question</p>'}</div>
      </section>
    `;
  }

  function renderScenarios(scenarios) {
    if (!scenarios) return softError('Scénarios indisponibles', '');
    const cards = (scenarios.scenarios || []).map((s) => `
      <article class="esr-scenario-card">
        <header>
          <span class="esr-code">${escapeHtml(s.code || '')}</span>
          <h4>${escapeHtml(s.title)}</h4>
        </header>
        <p>${escapeHtml(s.question || '')}</p>
        <dl class="esr-scenario-meta">
          <div><dt>Coût</dt><dd>${escapeHtml(s.cost_display || '—')}</dd></div>
          <div><dt>Impact</dt><dd>${escapeHtml(s.impact_display || '—')}</dd></div>
          <div><dt>Bénéficiaires</dt><dd>${escapeHtml(s.beneficiaries_display || '—')}</dd></div>
        </dl>
        ${s.recommendation ? `<p class="esr-rec"><strong>Recommandation</strong> ${escapeHtml(s.recommendation)}</p>` : ''}
        <div class="esr-scenario-actions">
          <button type="button" class="esr-why-btn secondary-button" data-esr-why
            data-why-title="${escapeHtml(s.title)}"
            data-why-body="${escapeHtml(s.recommendation || s.question || '')}"
            data-why-source="Decision Scenarios">Pourquoi ?</button>
          <button type="button" class="primary-button" data-esr-nav="${escapeHtml(s.hash || '')}">Lancer</button>
        </div>
      </article>
    `).join('');
    return `
      <section class="esr-card" id="esr-scenarios" data-esr-step="decisions">
        <header class="esr-card-header">
          <h3>${escapeHtml(scenarios.title || 'Simulations stratégiques')}</h3>
        </header>
        <div class="esr-scenario-grid">${cards || '<p class="esr-empty">Aucun scénario</p>'}</div>
      </section>
    `;
  }

  function renderActions(actions) {
    const items = (actions?.actions || []).map((a) => {
      const attrs = [
        `type="button"`,
        `class="esr-action-btn ${a.action === 'start_presentation' ? 'primary-button' : 'secondary-button'}"`,
        a.hash ? `data-esr-nav="${escapeHtml(a.hash)}"` : '',
        a.action ? `data-esr-action="${escapeHtml(a.action)}"` : '',
        a.capability ? `data-capability="${escapeHtml(a.capability)}"` : '',
        a.hide_when_unavailable ? `data-hide-unavailable="1"` : '',
        `title="${escapeHtml(a.why || '')}"`,
      ].filter(Boolean).join(' ');
      return `<button ${attrs}>${escapeHtml(a.label)}</button>`;
    }).join('');
    return `
      <section class="esr-actions-bar" id="esr-actions" aria-label="Actions exécutives">
        ${items}
      </section>
    `;
  }

  function renderPriorities(priorities, cockpit) {
    const ranking = global.EdvsCards?.renderRanking?.({
      title: 'Priorités sites',
      items: priorities?.sites || [],
      color: 'orange',
    }) || '';
    const recs = global.EdvsCards?.renderRecommendationCards?.({
      title: 'Décisions proposées',
      items: priorities?.recommendations || [],
    }) || '';
    const charts = cockpit ? [
      global.EdvsCharts?.stackedBar?.({ title: 'Programmes FDSU', ...(cockpit.stacked || {}) }) || '',
      global.EdvsCharts?.gauge?.(cockpit.gauges?.[0] || { title: 'Maturité', value: 0 }) || '',
      global.EdvsCharts?.waterfall?.(cockpit.waterfall || { title: 'Doctrine', steps: [] }) || '',
    ].join('') : '';
    return `
      <section class="esr-card" id="esr-priorities" data-esr-step="priorities">
        <header class="esr-card-header"><h3>Priorités & décisions</h3></header>
        <div class="esr-priorities-grid">
          ${ranking}
          ${recs}
        </div>
        <div class="esr-mini-charts">${charts}</div>
      </section>
    `;
  }

  function renderShell(partial) {
    const journey = `
      <nav class="esr-journey" aria-label="Parcours décisionnel">
        <span>Situation nationale</span><span aria-hidden="true">↓</span>
        <span>Pourquoi ?</span><span aria-hidden="true">↓</span>
        <span>Où ?</span><span aria-hidden="true">↓</span>
        <span>Que faut-il faire ?</span><span aria-hidden="true">↓</span>
        <span>Quel impact ?</span><span aria-hidden="true">↓</span>
        <span>Décider</span>
      </nav>
    `;
    return `
      <div class="esr-root" data-esr="situation-room">
        <header class="esr-top">
          <div>
            <p class="esr-kicker">Executive Situation Room</p>
            <h1>Salle de Pilotage DG</h1>
            <p class="esr-muted">État numérique du territoire — de la situation nationale à la décision</p>
          </div>
          <div class="esr-top-actions">
            <button type="button" class="primary-button" data-esr-action="start_presentation">Présenter au DG</button>
            <button type="button" class="secondary-button" data-esr-action="stop_presentation" hidden id="esr-stop-present">Interrompre</button>
            <button type="button" class="edvs-presentation-btn" data-edvs-presentation-toggle>Mode Présentation</button>
          </div>
        </header>
        ${journey}
        <div id="esr-actions-host">${partial.actionsHtml || softLoading('Actions…', 'esr-actions')}</div>
        <div id="esr-briefing-host">${partial.briefingHtml || softLoading('Briefing…', 'esr-briefing')}</div>
        <div class="esr-main-grid">
          <div class="esr-col-main">
            <div id="esr-national-host">${partial.nationalHtml || softLoading('Situation…', 'esr-national')}</div>
            <section class="esr-card esr-map-card" id="esr-map" data-esr-step="map">
              <header class="esr-card-header">
                <h3>Carte nationale — Tableau de Synthèse Territoriale</h3>
                <button type="button" class="esr-why-btn secondary-button" data-esr-why
                  data-why-title="Carte nationale"
                  data-why-body="Le TST permet de descendre Province → Territoire → … → Site. La sélection met à jour le contexte territorial sans recharger la page."
                  data-why-source="Territorial Summary · Territorial Context">Pourquoi ?</button>
              </header>
              <div id="edvs-tst-host" class="edvs-tst-host esr-tst-host" aria-label="Synthèse territoriale DG"></div>
              <p class="esr-map-hint" id="esr-context-hint">Sélectionnez une province pour commencer le parcours territorial.</p>
            </section>
            <div id="esr-priorities-host">${partial.prioritiesHtml || softLoading('Priorités…', 'esr-priorities')}</div>
          </div>
          <div class="esr-col-side">
            <div id="esr-alerts-host">${partial.alertsHtml || softLoading('Alertes…', 'esr-alerts')}</div>
            <div id="esr-questions-host">${partial.questionsHtml || softLoading('Questions…', 'esr-questions')}</div>
            <div id="esr-scenarios-host">${partial.scenariosHtml || softLoading('Scénarios…', 'esr-scenarios')}</div>
          </div>
        </div>
        <p class="esr-step-label" id="esr-step-label" aria-live="polite"></p>
      </div>
    `;
  }

  function bindInteractions(root) {
    root.addEventListener('click', (event) => {
      const why = event.target?.closest?.('[data-esr-why]');
      if (why) {
        event.preventDefault();
        openExplain(
          why.getAttribute('data-why-title'),
          why.getAttribute('data-why-body'),
          why.getAttribute('data-why-source'),
        );
        return;
      }
      const nav = event.target?.closest?.('[data-esr-nav]');
      if (nav && !event.target.closest('[data-esr-why]')) {
        let hash = nav.getAttribute('data-esr-nav');
        // Contexte TST : Twin / Impact selon sélection
        if (hash && hash.startsWith('territorial-twin/')) {
          const sel = global.TerritorialContext?.get()?.selection;
          const level = sel?.level || sel?.entity_type;
          const id = sel?.id || sel?.entity_id || sel?.name;
          if ((level === 'province' || level === 'territoire') && id) {
            hash = `territorial-twin/${level}/${encodeURIComponent(id)}`;
          }
        }
        if (hash && hash.startsWith('spatial-impact/')) {
          const sel = global.TerritorialContext?.get()?.selection;
          const siteId = sel?.site_id || (sel?.level === 'site' ? sel?.id : null);
          if (siteId) hash = `spatial-impact/site/${encodeURIComponent(siteId)}`;
        }
        if (hash) navigate(hash);
        return;
      }
      const action = event.target?.closest?.('[data-esr-action]');
      if (action) {
        const name = action.getAttribute('data-esr-action');
        if (name === 'start_presentation') startPresentation();
        if (name === 'stop_presentation') stopPresentation();
      }
    });
    root.querySelectorAll('.esr-nation-card[data-esr-nav]').forEach((card) => {
      card.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          navigate(card.getAttribute('data-esr-nav'));
        }
      });
    });
  }

  function applyCapabilities(root) {
    const reg = global.CapabilityRegistry;
    if (!reg) return;
    const run = () => {
      root.querySelectorAll('[data-capability]').forEach((btn) => {
        const key = btn.getAttribute('data-capability');
        const hide = btn.getAttribute('data-hide-unavailable') === '1';
        reg.applyButton(btn, key, { hideWhenUnavailable: hide });
      });
    };
    if (reg.state.loaded) run();
    else reg.load().then(run);
  }

  function mountTst() {
    const tstHost = document.querySelector('#edvs-tst-host');
    if (!tstHost || !global.TerritorialSummary?.mount) return;
    if (state.tstInstance?.destroy) {
      try { state.tstInstance.destroy(); } catch (_e) { /* */ }
    }
    global.TerritorialSummary.mount(tstHost, {
      metric: global.TerritorialContext?.get()?.metric || 'priority',
      preserveContext: true,
      showLegend: true,
      showKpis: true,
      allowDrilldown: true,
      onSelectionChange: (entity) => {
        if (global.TerritorialContext) global.TerritorialContext.select(entity);
        const hint = document.querySelector('#esr-context-hint');
        if (hint && entity) {
          const level = entity.level || entity.entity_type || 'entité';
          const name = entity.name || entity.id || entity.entity_id || '';
          hint.textContent = `Contexte actif : ${level} — ${name}. Les analyses s’ouvrent dans ce cadre.`;
        }
        if (!entity || !global.TerritorialDigitalTwin?.open) return;
        const level = entity.level || entity.entity_type;
        const id = entity.id || entity.entity_id || entity.name;
        if ((level === 'province' || level === 'territoire') && id) {
          // Ne pas quitter la salle automatiquement : le DG ouvre le Twin via action dédiée
          // Sauf double intention déjà habituelle — ouvrir Twin en overlay workspace
          global.TerritorialDigitalTwin.open({
            entityType: level,
            entityId: id,
            returnHash: 'salle-pilotage',
          });
        }
      },
    }).then((api) => { state.tstInstance = api; });
  }

  function stopPresentation() {
    state.presenting = false;
    if (state.presentTimer) {
      global.clearTimeout(state.presentTimer);
      state.presentTimer = null;
    }
    document.querySelectorAll('.esr-card.is-presenting').forEach((el) => el.classList.remove('is-presenting'));
    const stopBtn = document.querySelector('#esr-stop-present');
    if (stopBtn) stopBtn.hidden = true;
    const label = document.querySelector('#esr-step-label');
    if (label) label.textContent = '';
  }

  function startPresentation() {
    const steps = state.payload?.presentation?.steps
      || [
        { id: 'briefing', label: 'Executive Briefing', selector: '#esr-briefing', duration_ms: 3200 },
        { id: 'situation', label: 'Situation nationale', selector: '#esr-national', duration_ms: 3000 },
        { id: 'map', label: 'Carte', selector: '#esr-map', duration_ms: 3200 },
        { id: 'alerts', label: 'Alertes', selector: '#esr-alerts', duration_ms: 2800 },
        { id: 'priorities', label: 'Priorités', selector: '#esr-priorities', duration_ms: 3000 },
        { id: 'decisions', label: 'Décisions proposées', selector: '#esr-scenarios', duration_ms: 3000 },
      ];
    stopPresentation();
    state.presenting = true;
    state.presentStep = -1;
    const stopBtn = document.querySelector('#esr-stop-present');
    if (stopBtn) stopBtn.hidden = false;
    if (global.EdvsLayout?.setPresentationMode) global.EdvsLayout.setPresentationMode(true);

    const preferReduced = global.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches;
    const next = () => {
      if (!state.presenting) return;
      document.querySelectorAll('.esr-card.is-presenting').forEach((el) => el.classList.remove('is-presenting'));
      state.presentStep += 1;
      if (state.presentStep >= steps.length) {
        stopPresentation();
        return;
      }
      const step = steps[state.presentStep];
      const node = document.querySelector(step.selector);
      if (node) {
        node.classList.add('is-presenting');
        node.scrollIntoView({ behavior: preferReduced ? 'auto' : 'smooth', block: 'center' });
      }
      const label = document.querySelector('#esr-step-label');
      if (label) label.textContent = `${state.presentStep + 1}/${steps.length} — ${step.label}`;
      state.presentTimer = global.setTimeout(next, preferReduced ? 500 : (step.duration_ms || 3000));
    };
    next();
  }

  function paintPartial(slotId, html) {
    const host = document.querySelector(slotId);
    if (host) host.innerHTML = html;
  }

  function settle(promise, key) {
    return promise
      .then((data) => ({ key, ok: true, data }))
      .catch((err) => ({ key, ok: false, error: err }));
  }

  function mount(root) {
    if (!root) return Promise.resolve(null);
    root.innerHTML = renderShell({});
    bindInteractions(root);
    global.EdvsLayout?.bindPresentationControls?.(root);

    // Chargement progressif — allSettled, timeouts, résultats partiels
    const tasks = [
      settle(fetchJson('/api/executive/situation-room/briefing', 60000), 'briefing'),
      settle(fetchJson('/api/executive/situation-room/national', 60000), 'national'),
      settle(fetchJson('/api/executive/situation-room/alerts', 60000), 'alerts'),
      settle(fetchJson('/api/executive/situation-room/questions', 30000), 'questions'),
      settle(fetchJson('/api/executive/situation-room/actions', 20000), 'actions'),
      settle(fetchJson('/api/executive/situation-room', 90000), 'full'),
      settle(fetchJson('/api/executive/situation-room/scenarios', 45000), 'scenarios'),
    ];

    // Afficher dès que possible
    tasks[0].then((r) => paintPartial('#esr-briefing-host', r.ok ? renderBriefing(r.data) : softError('Briefing', 'Indisponible', 'esr-briefing')));
    tasks[1].then((r) => paintPartial('#esr-national-host', r.ok ? renderNational(r.data) : softError('Situation', 'Indisponible', 'esr-national')));
    tasks[2].then((r) => paintPartial('#esr-alerts-host', r.ok ? renderAlerts(r.data) : softError('Alertes', 'Indisponible', 'esr-alerts')));
    tasks[3].then((r) => paintPartial('#esr-questions-host', r.ok ? renderQuestions(r.data) : softError('Questions', 'Indisponible', 'esr-questions')));
    tasks[4].then((r) => {
      paintPartial('#esr-actions-host', r.ok ? renderActions(r.data) : softError('Actions', 'Indisponible', 'esr-actions'));
      applyCapabilities(root);
    });
    tasks[6].then((r) => paintPartial('#esr-scenarios-host', r.ok ? renderScenarios(r.data) : softError('Scénarios', 'Indisponible', 'esr-scenarios')));

    mountTst();

    return Promise.all(tasks).then((results) => {
      const byKey = Object.fromEntries(results.map((r) => [r.key, r]));
      const full = byKey.full?.ok ? byKey.full.data : null;
      state.payload = full || {
        briefing: byKey.briefing?.data,
        national_situation: byKey.national?.data,
        alerts: byKey.alerts?.data,
        questions: byKey.questions?.data,
        scenarios: byKey.scenarios?.data,
        actions: byKey.actions?.data,
      };
      if (full?.priorities || full?.cockpit) {
        paintPartial(
          '#esr-priorities-host',
          renderPriorities(full.priorities, full.cockpit),
        );
        if (global.UxPremium?.bindEdvsKpiClicks) {
          // KPIs nationaux déjà cliquables via cartes ESR
        }
      }
      // Scénarios : si full arrive avant le panel dédié, compléter
      if (full?.scenarios && !byKey.scenarios?.ok) {
        paintPartial('#esr-scenarios-host', renderScenarios(full.scenarios));
      }
      applyCapabilities(root);
      return state.payload;
    });
  }

  function destroy() {
    stopPresentation();
    if (state.tstInstance?.destroy) {
      try { state.tstInstance.destroy(); } catch (_e) { /* */ }
    }
    state.tstInstance = null;
  }

  global.ExecutiveSituationRoom = {
    version: '1.0.0',
    mount,
    destroy,
    startPresentation,
    stopPresentation,
    state,
  };
})(typeof window !== 'undefined' ? window : globalThis);
