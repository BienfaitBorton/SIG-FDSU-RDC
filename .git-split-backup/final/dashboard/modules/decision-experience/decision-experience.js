/**
 * Decision Experience Layer (DXL) — orchestrateur mince.
 * Routes : #decision-case/<type>/<id> · #spatial-impact/<type>/<id>
 * Délègue : DxlCore · DecisionCaseController (IG) · SpatialImpactController (SDG).
 */
(function initDecisionExperienceLayer(global) {
  const Dxl = () => global.DxlCore;
  const state = () => Dxl()?.state;

  function bindEvents() {
    const core = Dxl();
    if (!core) return;
    const { goBack, notify, openMapForCurrentSite, exportCaseExcel } = core;
    const st = core.state;

    const root = document.querySelector('#decision-experience-panel');
    if (!root || root.dataset.bound === 'true') return;
    root.dataset.bound = 'true';

    document.querySelector('#dxl-back-btn')?.addEventListener('click', goBack);

    root.addEventListener('click', (event) => {
      const btn = event.target?.closest?.('[data-dxl-action]');
      if (!btn || btn.disabled) return;
      const action = btn.getAttribute('data-dxl-action');
      if (action === 'back') {
        goBack();
        return;
      }
      if (action === 'retry-case') {
        if (st.mode === 'decision-case' && st.assetId) {
          global.DecisionCaseController?.load(st.assetType || 'site', st.assetId, st.programCode);
        } else if (st.mode === 'spatial-impact' && st.assetId) {
          global.SpatialImpactController?.load(st.assetType || 'site', st.assetId);
        }
        return;
      }
      if (action === 'map') {
        openMapForCurrentSite();
        return;
      }
      if (action === 'ti') {
        const tid = st.payload?.caseFile?.asset?.territoire
          || st.payload?.caseFile?.site?.territoire
          || st.payload?.ti?.profile?.id
          || st.payload?.ti?.territory_id
          || st.payload?.decisionCase?.asset?.territoire;
        if (!tid) {
          notify('Rattachement territorial absent — impossible d’ouvrir l’analyse territoriale pour ce site.', true);
          return;
        }
        global.location.hash = `territorial-intelligence/${encodeURIComponent(tid)}`;
        return;
      }
      if (action === 'explain') {
        const why = document.querySelector('#dxl-section-why');
        if (!why) {
          notify('Section d’explication indisponible.', true);
          return;
        }
        why.scrollIntoView({ behavior: 'smooth', block: 'start' });
        if (!why.textContent?.trim() || /non encore disponible/i.test(why.textContent)) {
          notify('Justification en cours de chargement ou encore partielle.');
        }
        return;
      }
      if (action === 'spatial') {
        if (!st.assetId) {
          notify('Identifiant d’actif manquant pour l’impact spatial.', true);
          return;
        }
        global.location.hash = `spatial-impact/${st.assetType || 'site'}/${encodeURIComponent(st.assetId)}`;
        return;
      }
      if (action === 'export') {
        exportCaseExcel(btn);
        return;
      }
      if (action === 'pdf') {
        notify(global.CapabilityRegistry?.reason?.('export_pdf') || 'Export PDF non encore activé pour ce dossier');
        return;
      }
      if (action === 'ppt') {
        notify(global.CapabilityRegistry?.reason?.('export_powerpoint') || 'Export PowerPoint non encore activé pour ce dossier');
      }
    });

    global.document.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape') return;
      const panel = document.querySelector('#decision-experience-panel');
      if (panel && !panel.classList.contains('hidden')) goBack();
    });
  }

  function openDecisionCase(assetType, assetId, programCode) {
    try {
      const current = (global.location.hash || '').replace(/^#/, '');
      if (current && !current.startsWith('decision-case')) {
        global.sessionStorage?.setItem('fdsu.decisionCase.returnHash', current);
      }
    } catch (_err) { /* */ }
    const qs = programCode ? `?program_code=${encodeURIComponent(programCode)}` : '';
    global.location.hash = `decision-case/${assetType}/${encodeURIComponent(assetId)}${qs}`;
  }

  function openSpatialImpact(assetType, assetId) {
    global.location.hash = `spatial-impact/${assetType}/${encodeURIComponent(assetId)}`;
  }

  function loadSpatialImpact(assetType, assetId) {
    return global.SpatialImpactController?.load(assetType, assetId);
  }

  function initializeDecisionExperienceModule() {
    const core = Dxl();
    if (!core) {
      console.error('[DXL] DxlCore manquant — scripts non chargés dans le bon ordre');
      return;
    }
    const { parseHash, setStatus, setLoading } = core;
    const st = core.state;

    bindEvents();
    st.initialized = true;

    function bootParsed() {
      const parsed = parseHash();
      if (!parsed) {
        setStatus('Aucun dossier sélectionné', true);
        setLoading(false);
        return;
      }
      st.mode = parsed.mode;
      st.assetType = parsed.assetType;
      st.assetId = parsed.assetId;
      st.programCode = parsed.programCode;
      const boot = parsed.mode === 'spatial-impact'
        ? global.SpatialImpactController?.load(parsed.assetType, parsed.assetId)
        : parsed.mode === 'coverage-detail'
          ? global.SpatialImpactController?.loadCoverageDetail(parsed.assetId)
          : global.DecisionCaseController?.load(parsed.assetType, parsed.assetId, parsed.programCode);
      Promise.resolve(boot).catch((err) => {
        console.error('[DXL] initialisation module', err);
        setLoading(false);
        const msg = global.DecisionErrorHandler?.humanizeFetchError?.(err)
          || String(err?.message || err || 'erreur inconnue');
        setStatus(`Chargement interrompu : ${msg}`, true);
      });
    }

    if (global.CapabilityRegistry?.load) {
      global.CapabilityRegistry.load().finally(() => bootParsed());
    } else {
      bootParsed();
    }
  }

  global.openDecisionCase = openDecisionCase;
  global.openSpatialImpact = openSpatialImpact;
  global.loadSpatialImpact = loadSpatialImpact;
  global.initializeDecisionExperienceModule = initializeDecisionExperienceModule;
  Object.defineProperty(global, 'decisionExperienceState', {
    get() {
      return Dxl()?.state;
    },
    configurable: true,
  });
})(typeof window !== 'undefined' ? window : globalThis);
