/**
 * Decision Case Controller — Ownership Integrity Gate.
 * Charge le dossier décisionnel ; délègue la carte SDG à SpatialImpactController.
 * Attaché à window.DecisionCaseController.
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
      const territoire = caseFile?.asset?.territoire || caseFile?.site?.territoire || caseFile?.asset?.territory_id
        || nsmeImpact?.asset?.territoire;
      if (territoire) {
        const tiRes = await tracedFetch(`/api/territorial-intelligence/territories/${encodeURIComponent(territoire)}`, 'coverage');
        ti = tiRes.ok ? tiRes.data : null;
      }
      state.payload = { caseFile, nsmeImpact, nsmeMap, ti };

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

      // Carte dossier : déléguée au SpatialImpactController (SDG) — pas d’appel direct SDG
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
        ensureMap(); // graceful without SDG
      }

      renderWhy(caseFile || {});
      renderContext(caseFile || {}, ti || {});
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
      if (global.TerritorialImpactUI?.mountSiteImpact) {
        global.TerritorialImpactUI.mountSiteImpact(assetId, programCode);
      }
      renderRisks(caseFile || {});
      renderTraceability(caseFile || {});
      renderRecommendation(caseFile || {});
      renderActions();

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
