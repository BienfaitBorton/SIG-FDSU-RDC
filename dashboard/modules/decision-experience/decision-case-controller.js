/**
 * Decision Case Controller — Ownership Integrity Gate.
 * Phase 2 : premier contenu utile (core) puis preuves spatiales en parallèle.
 */
(function initDecisionCaseController(global) {
  async function load(assetType, assetId, programCode) {
    const Dxl = global.DxlCore;
    const Err = global.DecisionErrorHandler;
    if (!Dxl) {
      console.error('[DXL] DecisionCaseController : DxlCore manquant');
      return;
    }

    const {
      state,
      tracedFetch,
      setLoading,
      setStatus,
      ensureMap,
      softErrorHtml,
      renderExecutiveSummary,
      renderWhy,
      renderContext,
      renderImpact,
      renderRisks,
      renderTraceability,
      renderRecommendation,
      renderActions,
    } = Dxl;

    const businessErrorHtml = Err?.businessErrorHtml
      || ((title, message, options = {}) => {
        const esc = Dxl.escapeHtml;
        const tech = options.technical ? `<details class="dxl-tech-details"><summary>Détail technique</summary><pre>${esc(options.technical)}</pre></details>` : '';
        const retry = options.retry
          ? `<button type="button" class="secondary-button" data-dxl-action="retry-case">Réessayer</button>`
          : '';
        return `
          <div class="dxl-panel-soft-error">
            <strong>${esc(title)}</strong>
            <p>${esc(message || '')}</p>
            ${options.hint ? `<p class="dxl-note">${esc(options.hint)}</p>` : ''}
            <div class="dxl-error-actions">${retry}</div>
            ${tech}
          </div>
        `;
      });
    const humanizeFetchError = Err?.humanizeFetchError
      || ((error) => String(error?.message || error || 'erreur inconnue'));

    setLoading(true);
    setStatus('Chargement du dossier de décision…');
    const baseQs = programCode
      ? `asset_type=${encodeURIComponent(assetType === 'site' ? 'site' : assetType)}&program_code=${encodeURIComponent(programCode)}`
      : `asset_type=${encodeURIComponent(assetType === 'site' ? 'site' : assetType)}`;
    const coreQs = `?${baseQs}&include_spatial_evidence=false`;
    const fullQs = `?${baseQs}`;
    try {
      // 1) Core + impact + map en parallèle — core sans preuves spatiales lourdes
      const [caseRes, impactRes, mapRes] = await Promise.all([
        tracedFetch(`/api/decision/case/${encodeURIComponent(assetId)}${coreQs}`, 'decisionCase'),
        tracedFetch(`/api/spatial-matching/assets/${encodeURIComponent(assetId)}/impact`, 'impact'),
        tracedFetch(`/api/spatial-matching/map?asset_id=${encodeURIComponent(assetId)}`, 'map'),
      ]);
      let caseFile = caseRes.ok ? caseRes.data : null;
      const nsmeImpact = impactRes.ok ? impactRes.data : null;
      const nsmeMap = mapRes.ok ? mapRes.data : null;
      state.payload = { caseFile, nsmeImpact, nsmeMap, ti: null };

      const assetForLabel = caseFile?.asset || nsmeImpact?.asset || {};
      const displayName = (global.FdsuSiteDisplayName?.siteDisplayLabel?.(assetForLabel))
        || assetForLabel.display_name
        || assetForLabel.site_name
        || assetForLabel.name
        || null;
      const title = document.querySelector('#dxl-title');
      if (title) {
        title.textContent = displayName
          ? `Dossier de décision — ${displayName}`
          : `Dossier de décision — site ${assetId}`;
      }

      if (caseFile) {
        renderExecutiveSummary(caseFile, nsmeImpact?.impact);
      } else {
        renderExecutiveSummary({
          asset: {
            site_code: nsmeImpact?.asset?.site_code || assetId,
            site_name: displayName || `Site ${assetId}`,
            name: displayName || `Site ${assetId}`,
            program_code: programCode || nsmeImpact?.asset?.program_code,
            priority_level_label: 'Priorité non consolidée',
            priority_score: '—',
          },
          summary: {
            text: 'Le dossier décisionnel n’a pas pu être consolidé. Les autres volets (carte, impact) restent consultables s’ils sont disponibles.',
            recommendation: 'Réessayer le chargement ou ouvrir l’Analyse d’Impact Territorial.',
          },
          score: { global: '—', priority_label: 'Non consolidé' },
        }, nsmeImpact?.impact);
        const summaryHost = document.querySelector('#dxl-section-summary');
        if (summaryHost) {
          summaryHost.insertAdjacentHTML(
            'beforeend',
            businessErrorHtml(
              'Section dossier décisionnel indisponible',
              'Le moteur de décision n’a pas renvoyé un dossier complet pour ce site.',
              {
                hint: 'Les autres sections restent affichées. Utilisez Réessayer.',
                technical: `${caseRes.error || ''} [${caseRes.httpStatus || 'n/a'}] ${caseRes.url || ''}`.trim(),
                retry: true,
              },
            ),
          );
        }
      }

      renderWhy(caseFile || {});
      renderContext(caseFile || {}, {});
      if (nsmeImpact) renderImpact(caseFile?.impacts, nsmeImpact);
      else {
        const host = document.querySelector('#dxl-section-impact');
        if (host) {
          host.innerHTML = softErrorHtml(
            'Impact NSME indisponible',
            impactRes.error || 'Le service d’impact n’a pas répondu.',
            'Le reste du dossier reste consultable. Ouvrez l’Analyse d’Impact Territorial pour le graphe décisionnel.',
          );
        }
      }
      renderRisks(caseFile || {});
      renderTraceability(caseFile || {});
      renderRecommendation(caseFile || {});
      renderActions();

      // TIME_TO_FIRST_USEFUL_CONTENT
      setLoading(false);
      setStatus('Dossier partiel — enrichissement spatial en cours…', false);

      const territoire = caseFile?.asset?.territoire || caseFile?.site?.territoire || caseFile?.asset?.territory_id
        || nsmeImpact?.asset?.territoire;

      const evidencePromise = tracedFetch(
        `/api/decision/case/${encodeURIComponent(assetId)}/spatial-evidence${fullQs}`,
        'spatialEvidence',
      ).then((evRes) => (evRes.ok ? evRes.data : null)).catch(() => null);

      const tiPromise = territoire
        ? tracedFetch(`/api/territorial-intelligence/territories/${encodeURIComponent(territoire)}`, 'coverage')
          .then((tiRes) => (tiRes.ok ? tiRes.data : null))
          .catch(() => null)
        : Promise.resolve(null);

      const sdgPromise = Promise.resolve().then(() => {
        if (global.SpatialImpactController?.mountOnCaseMap) {
          global.SpatialImpactController.mountOnCaseMap({
            assetType,
            assetId,
            programCode,
            caseFile,
            nsmeImpact,
            map: ensureMap(),
            layer: state.layer,
          });
        } else {
          ensureMap();
        }
      });

      const tiePromise = Promise.resolve().then(() => {
        if (global.TerritorialImpactUI?.mountSiteImpact) {
          global.TerritorialImpactUI.mountSiteImpact(assetId, programCode);
        }
      });

      const [evidence, ti] = await Promise.all([evidencePromise, tiPromise, sdgPromise, tiePromise]);
      if (evidence) {
        caseFile = evidence;
        state.payload.caseFile = evidence;
        // Re-render sections that depend on spatial proofs
        renderExecutiveSummary(evidence, nsmeImpact?.impact);
        renderWhy(evidence);
        renderContext(evidence, ti || {});
        renderRisks(evidence);
        renderTraceability(evidence);
        renderRecommendation(evidence);
      } else if (ti) {
        state.payload.ti = ti;
        renderContext(caseFile || {}, ti);
      }
      if (ti) state.payload.ti = ti;

      const failedLabels = [];
      if (!caseRes.ok) failedLabels.push('dossier décisionnel');
      if (!impactRes.ok) failedLabels.push('impact');
      if (!mapRes.ok) failedLabels.push('carte');
      if (caseFile && !failedLabels.length) {
        setStatus('Dossier prêt', false);
      } else if (caseFile) {
        setStatus(`Dossier partiel — sections indisponibles : ${failedLabels.join(', ')}`, true);
      } else {
        setStatus(
          displayName
            ? `Dossier incomplet pour ${displayName} — décisionnel indisponible`
            : 'Dossier incomplet — le moteur de décision n’a pas répondu',
          true,
        );
      }
    } catch (err) {
      setStatus('Impossible de charger le dossier de décision', true);
      const summary = document.querySelector('#dxl-section-summary');
      if (summary) {
        summary.innerHTML = businessErrorHtml(
          'Dossier indisponible',
          'Une erreur inattendue a interrompu le chargement.',
          { technical: humanizeFetchError(err), retry: true },
        );
      }
    } finally {
      setLoading(false);
    }
  }

  global.DecisionCaseController = { load };
})(typeof window !== 'undefined' ? window : globalThis);
