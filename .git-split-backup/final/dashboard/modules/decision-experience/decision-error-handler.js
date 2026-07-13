/**
 * Decision Error Handler — Ownership Integrity Gate.
 * Messages métier DG : jamais d’exposition HTTP 400 brute.
 * Attaché à window.DecisionErrorHandler.
 */
(function initDecisionErrorHandler(global) {
  function escapeHtml(value) {
    if (typeof global.DxlCore?.escapeHtml === 'function') {
      return global.DxlCore.escapeHtml(value);
    }
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function humanizeFetchError(error, status) {
    const raw = String(error?.message || error || 'erreur inconnue');
    if (/failed to fetch|networkerror|load failed|network request failed/i.test(raw)) {
      return `Connexion impossible vers le service. Vérifiez que l’API est démarrée.`;
    }
    if (/abort/i.test(raw)) {
      return 'Délai dépassé — le service n’a pas répondu à temps.';
    }
    // Ne jamais exposer « HTTP 400 » / stacks au DG
    if (status === 404) return 'Dossier introuvable pour cet actif.';
    if (status === 400) return 'Données du dossier incohérentes ou incomplètes.';
    if (status && status >= 500) return 'Service décisionnel temporairement indisponible.';
    if (status) return 'Le service n’a pas pu fournir ce dossier.';
    if (/extra data|json|traceback|HTTP\s*\d{3}/i.test(raw)) {
      return 'Le dossier n’a pas pu être consolidé correctement.';
    }
    return raw;
  }

  function businessErrorHtml(title, message, options = {}) {
    const tech = options.technical ? `<details class="dxl-tech-details"><summary>Détail technique</summary><pre>${escapeHtml(options.technical)}</pre></details>` : '';
    const retry = options.retry
      ? `<button type="button" class="secondary-button" data-dxl-action="retry-case">Réessayer</button>`
      : '';
    return `
      <div class="dxl-panel-soft-error">
        <strong>${escapeHtml(title)}</strong>
        <p>${escapeHtml(message || '')}</p>
        ${options.hint ? `<p class="dxl-note">${escapeHtml(options.hint)}</p>` : ''}
        <div class="dxl-error-actions">${retry}</div>
        ${tech}
      </div>
    `;
  }

  global.DecisionErrorHandler = {
    humanizeFetchError,
    businessErrorHtml,
  };
})(typeof window !== 'undefined' ? window : globalThis);
