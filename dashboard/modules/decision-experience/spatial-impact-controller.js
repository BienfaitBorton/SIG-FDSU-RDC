/**
 * Spatial Impact Controller — Ownership Spatial Decision Graph (SDG).
 * Analyse d’Impact Territorial, montée SDG sur carte dossier, coverage-detail.
 * Attaché à window.SpatialImpactController.
 */
(function initSpatialImpactController(global) {
  /** Génération de load() — invalide les paint/SDG d’un chargement précédent. */
  let activeLoadGeneration = 0;
  /** Génération pour laquelle loadAndMount a déjà été demandé (au plus une fois). */
  let sdgMountClaimedForGeneration = -1;

  function getCore() {
    return global.DxlCore;
  }

  function startLoadGeneration() {
    activeLoadGeneration += 1;
    return activeLoadGeneration;
  }

  /**
   * Réserve un unique mount SDG pour la génération courante.
   * @returns {boolean} true si l’appelant doit déclencher loadAndMount
   */
  function claimSdgMount(generation) {
    if (generation == null || generation !== activeLoadGeneration) return false;
    if (sdgMountClaimedForGeneration === generation) return false;
    sdgMountClaimedForGeneration = generation;
    return true;
  }

  function isActiveLoadGeneration(generation) {
    return generation != null && generation === activeLoadGeneration;
  }

  function humanize(err, status) {
    if (typeof global.DecisionErrorHandler?.humanizeFetchError === 'function') {
      return global.DecisionErrorHandler.humanizeFetchError(err, status);
    }
    return String(err?.message || err || 'erreur inconnue');
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

  /**
   * Monte Spatial Decision Graph sur la carte du dossier de décision.
   * Pas de fallback NSME générique. Retire ux-legend-dxl.
   */
  function mountOnCaseMap(opts = {}) {
    const Dxl = getCore();
    if (!Dxl) return;
    const { assetType, assetId, programCode, caseFile, nsmeImpact } = opts;
    const map = opts.map || Dxl.ensureMap();
    const layer = opts.layer !== undefined ? opts.layer : Dxl.state.layer;

    document.querySelector('#ux-legend-dxl')?.remove();
    try {
      if (map && layer) layer.clearLayers();
      if (map && global.SpatialDecisionGraph?.loadAndMount) {
        global.SpatialDecisionGraph.loadAndMount(
          map,
          assetType === 'site' ? 'site' : assetType,
          assetId,
          programCode || caseFile?.asset?.program_code || nsmeImpact?.asset?.program_code,
        ).then(() => {
          document.querySelector('#ux-legend-dxl')?.remove();
          global.SigDecisionCartographyExperience?.attach?.();
        }).catch((err) => {
          console.warn('[DXL] SDG dossier', err);
          const mapHost = document.querySelector('#dxl-map');
          if (mapHost) {
            const note = document.createElement('div');
            note.className = 'dxl-panel-soft-error sdg-explain-fallback';
            note.id = 'sdg-load-explain';
            const sid = assetId;
            const pc = programCode || caseFile?.asset?.program_code || nsmeImpact?.asset?.program_code || '';
            note.innerHTML = '<strong>Analyse spatiale en diagnostic…</strong>';
            mapHost.before(note);
            const qs = pc ? `?program_code=${encodeURIComponent(pc)}` : '';
            fetch(`${location.protocol}//${location.hostname}:8001/api/sdg/assets/${encodeURIComponent(sid)}/explainability${qs}`)
              .then((r) => (r.ok ? r.json() : null))
              .then((payload) => {
                const card = payload?.explainability;
                if (!card) {
                  note.innerHTML = `<strong>Analyse spatiale indisponible</strong> — échec de chargement du graphe.`;
                  return;
                }
                note.innerHTML = `
                  <strong>${card.title || 'Analyse spatiale indisponible'}</strong>
                  <p>${card.message || ''}</p>
                  <p><em>Données disponibles :</em> ${(card.available || []).join(', ') || '—'}</p>
                  <p><em>Données manquantes :</em> ${(card.missing || []).join(', ') || '—'}</p>
                  <p class="dxl-note">${card.hint || ''}</p>`;
              })
              .catch(() => {
                note.innerHTML = '<strong>Analyse spatiale indisponible</strong> — diagnostic détaillé non joignable.';
              });
          }
        });
      }
    } catch (mapErr) {
      console.warn('[DXL] carte dossier', mapErr);
    }
  }

  /**
   * Charge l’impact spatial avec statut individuel par service.
   * Retourne { impact, needs, statistics, coverage, explain, decisionCase }.
   * Pas de fetch /spatial-matching/map : le rendu carte est assuré par SpatialDecisionGraph.
   */
  async function loadData(assetType, assetId, generation) {
    const Dxl = getCore();
    if (!Dxl) return null;

    const gen = generation != null ? generation : startLoadGeneration();

    const {
      state,
      SERVICE_LABELS,
      emptyService,
      tracedFetch,
      renderServicesPanel,
      setStatus,
    } = Dxl;

    const id = encodeURIComponent(assetId);
    const programCode = state.programCode
      ? String(state.programCode).trim()
      : '';
    const withProgramCode = (path) => {
      if (!programCode) return path;
      const sep = path.includes('?') ? '&' : '?';
      return `${path}${sep}program_code=${encodeURIComponent(programCode)}`;
    };
    const services = {
      impact: emptyService('impact'),
      needs: emptyService('needs'),
      explain: emptyService('explain'),
      coverage: emptyService('coverage'),
      decisionCase: emptyService('decisionCase'),
      statistics: emptyService('statistics'),
    };
    state.services = services;
    renderServicesPanel(services);

    const requests = [
      { key: 'needs', path: withProgramCode(`/api/spatial-matching/assets/${id}/needs?limit=100`) },
      { key: 'impact', path: withProgramCode(`/api/spatial-matching/assets/${id}/impact`) },
      { key: 'explain', path: withProgramCode(`/api/spatial-matching/assets/${id}/explain`), timeoutMs: 12000 },
      { key: 'statistics', path: '/api/spatial-matching/statistics' },
      {
        key: 'decisionCase',
        // Noyau léger au premier affichage — preuves spatiales via Needs / Impact / SDG
        // program_code requis pour éviter collision d’identité site_id multi-programmes
        path: withProgramCode(
          `/api/decision/case/${id}?asset_type=${encodeURIComponent(assetType === 'site' ? 'site' : assetType)}&include_spatial_evidence=false`,
        ),
      },
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
      if (!isActiveLoadGeneration(gen)) return;
      try {
        refreshCoverageDerived();
        renderServicesPanel(services);
        renderWorkspace(services, assetId, gen);
        const summary = summarizeServiceFailures(services);
        const stillLoading = Object.values(services).some((s) => s.status === 'loading');
        if (stillLoading) {
          setStatus(`Chargement… ${summary.text}`, summary.isError);
        } else {
          setStatus(summary.text, summary.isError);
        }
      } catch (paintErr) {
        console.error('[DXL] paint spatial-impact', paintErr);
        setStatus(`Affichage partiel — ${humanize(paintErr)}`, true);
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

  function renderWorkspace(services, assetId, generation) {
    const Dxl = getCore();
    if (!Dxl) return;

    const gen = generation != null ? generation : activeLoadGeneration;

    const {
      state,
      escapeHtml,
      formatNumber,
      ensureMap,
      softErrorHtml,
      softLoadingHtml,
      renderExecutiveSummary,
      renderImpact,
      renderRisks,
      renderTraceability,
      renderRecommendation,
      renderActions,
    } = Dxl;

    const needs = services.needs?.data;
    const impact = services.impact?.data;
    const explain = services.explain?.data;
    const decisionCase = services.decisionCase?.data;
    const statistics = services.statistics?.data;

    const title = document.querySelector('#dxl-title');
    if (title) {
      const name = decisionCase?.asset?.site_name
        || decisionCase?.asset?.name
        || needs?.asset?.site_name
        || assetId;
      title.textContent = `Analyse d’Impact Territorial — ${name}`;
    }

    // Résumé : ne dépend pas d’explain
    const summarySource = {
      asset: {
        site_code: decisionCase?.asset?.site_code || assetId,
        site_name: decisionCase?.asset?.site_name || decisionCase?.asset?.name || needs?.asset?.site_name || assetId,
        program_code: decisionCase?.asset?.program_code || needs?.asset?.program_code,
        priority_level_label: decisionCase?.asset?.priority_level_label || decisionCase?.priority_level,
        priority_score: decisionCase?.asset?.priority_score || decisionCase?.score,
      },
      summary: explain?.summary
        || (services.impact.status === 'loaded'
          ? 'Analyse d’Impact Territorial construite à partir des correspondances NSME.'
          : 'Dossier d’impact territorial — certaines sources sont encore en cours de consolidation.'),
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
        impactHost.innerHTML = softLoadingHtml('Chargement de l’analyse d’impact territorial…');
      } else {
        impactHost.innerHTML = softErrorHtml(
          'Analyse d’impact (NSME) indisponible',
          services.impact.error || 'Le service d’impact n’a pas répondu.',
          'Le Spatial Decision Graph et l’explicabilité restent consultables s’ils sont disponibles.',
        );
      }
    }

    // Carte — Spatial Decision Graph v2.1 (seul renderer officiel Analyse d’Impact Territorial)
    // Au plus un loadAndMount par génération de load() ; les paint() suivants mettent à jour l’UI sans remonter.
    const mapSection = document.querySelector('#dxl-map')?.closest('.dxl-section');
    mapSection?.querySelectorAll(':scope > .dxl-panel-soft-error').forEach((el) => el.remove());
    document.querySelector('#ux-legend-dxl')?.remove();
    try {
      const map = ensureMap();
      const programCode = needs?.asset?.program_code
        || decisionCase?.asset?.program_code
        || state.programCode;
      if (map && global.SpatialDecisionGraph?.loadAndMount) {
        if (claimSdgMount(gen)) {
          if (state.layer) state.layer.clearLayers();
          global.SpatialDecisionGraph.loadAndMount(
            map,
            'site',
            assetId,
            programCode,
          ).then(() => {
            if (!isActiveLoadGeneration(gen)) return;
            document.querySelector('#ux-legend-dxl')?.remove();
            global.SigDecisionCartographyExperience?.attach?.();
            if (global.sessionStorage?.getItem('fdsu.sdg.autoPresent') === '1') {
              global.sessionStorage.removeItem('fdsu.sdg.autoPresent');
              global.setTimeout(() => {
                if (!isActiveLoadGeneration(gen)) return;
                global.SpatialDecisionGraph?.startPresentation?.();
              }, 400);
            }
          }).catch((err) => {
            if (!isActiveLoadGeneration(gen)) return;
            console.warn('[DXL] Spatial Decision Graph', err);
            if (mapSection) {
              const note = document.createElement('div');
              note.className = 'dxl-panel-soft-error sdg-explain-fallback';
              note.innerHTML = '<strong>Analyse spatiale en diagnostic…</strong>';
              document.querySelector('#dxl-map')?.before(note);
              const pc = programCode || '';
              const qs = pc ? `?program_code=${encodeURIComponent(pc)}` : '';
              fetch(`${location.protocol}//${location.hostname}:8001/api/sdg/assets/${encodeURIComponent(assetId)}/explainability${qs}`)
                .then((r) => (r.ok ? r.json() : null))
                .then((payload) => {
                  if (!isActiveLoadGeneration(gen)) return;
                  const card = payload?.explainability;
                  if (!card) {
                    note.innerHTML = '<strong>Analyse spatiale indisponible</strong> — le graphe n’a pas pu être chargé.';
                    return;
                  }
                  note.innerHTML = `
                  <strong>${card.title || 'Analyse spatiale indisponible'}</strong>
                  <p>${card.message || ''}</p>
                  <p><em>Disponibles :</em> ${(card.available || []).join(', ') || '—'}</p>
                  <p><em>Manquantes :</em> ${(card.missing || []).join(', ') || '—'}</p>
                  <p class="dxl-note">${card.hint || ''}</p>`;
                })
                .catch(() => {
                  if (!isActiveLoadGeneration(gen)) return;
                  note.innerHTML = '<strong>Analyse spatiale indisponible</strong> — diagnostic non joignable.';
                });
            }
          });
        }
      } else if (!global.SpatialDecisionGraph?.loadAndMount && mapSection && claimSdgMount(gen)) {
        // Une seule note « module manquant » par génération
        const note = document.createElement('p');
        note.className = 'dxl-panel-soft-error';
        note.innerHTML = '<strong>Module Spatial Decision Graph non chargé</strong> — vérifiez spatial-decision-graph.js.';
        document.querySelector('#dxl-map')?.before(note);
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

  async function load(assetType, assetId) {
    const Dxl = getCore();
    if (!Dxl) return null;

    const {
      state,
      setLoading,
      setStatus,
      softErrorHtml,
      renderActions,
    } = Dxl;

    const gen = startLoadGeneration();
    setLoading(true);
    setStatus('Chargement de l’analyse d’impact territorial…');
    try {
      const services = await loadData(assetType, assetId, gen);
      if (!isActiveLoadGeneration(gen)) return services;
      state.payload = {
        services,
        needs: services.needs?.data,
        impact: services.impact?.data,
        explain: services.explain?.data,
        map: null,
        statistics: services.statistics?.data,
        decisionCase: services.decisionCase?.data,
      };
      state.services = services;
      renderWorkspace(services, assetId, gen);
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
      if (!isActiveLoadGeneration(gen)) return state.services;
      setStatus(`Analyse d’Impact Territorial — erreur inattendue : ${humanize(err)}`, true);
      const summary = document.querySelector('#dxl-section-summary');
      if (summary) {
        summary.innerHTML = softErrorHtml(
          'Analyse spatiale — erreur inattendue',
          humanize(err),
          'Consultez la fiche d’explicabilité si le diagnostic SDG est disponible.',
        );
      }
      renderActions();
      return state.services;
    } finally {
      if (isActiveLoadGeneration(gen)) setLoading(false);
    }
  }

  async function loadCoverageDetail(territoryId) {
    const Dxl = getCore();
    if (!Dxl) return;

    const {
      tracedFetch,
      setLoading,
      setStatus,
      ensureMap,
      renderMapFromNsme,
      renderExecutiveSummary,
      renderContext,
      renderWhy,
      renderImpact,
      renderRisks,
      renderTraceability,
      renderRecommendation,
      renderActions,
    } = Dxl;

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
      setStatus(`Couverture indisponible : ${humanize(err)}`, true);
    } finally {
      setLoading(false);
    }
  }

  global.SpatialImpactController = {
    load,
    loadData,
    renderWorkspace,
    mountOnCaseMap,
    loadCoverageDetail,
    summarizeServiceFailures,
    /** Hooks de test / diagnostic — garde mount SDG (génération). */
    _sdgMountGuard: {
      startLoadGeneration,
      claimSdgMount,
      isActiveLoadGeneration,
      getActiveLoadGeneration: () => activeLoadGeneration,
      getClaimedGeneration: () => sdgMountClaimedForGeneration,
    },
  };
})(typeof window !== 'undefined' ? window : globalThis);
