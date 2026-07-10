/**
 * EDVS — Layout (ratio 30/30/20/20) + Mode Présentation
 */
(function (global) {
  const PRESENTATION_CLASS = 'edvs-presentation-mode';

  function shell(options) {
    const U = global.EdvsUtils;
    const opts = options || {};
    return `
      <div class="edvs-shell ${opts.className || ''}" data-edvs="shell" data-ratio="30-30-20-20">
        <header class="edvs-shell-header">
          <div>
            <p class="edvs-eyebrow">${U.escapeHtml(opts.eyebrow || 'Executive Data Visualization System')}</p>
            <h2>${U.escapeHtml(opts.title || 'Pilotage')}</h2>
            <p class="edvs-muted">${U.escapeHtml(opts.subtitle || '')}</p>
          </div>
          <div class="edvs-shell-actions">
            ${opts.actionsHtml || ''}
            <button type="button" class="edvs-presentation-btn" data-edvs-presentation-toggle aria-pressed="false">Mode Présentation</button>
          </div>
        </header>
        <div class="edvs-ratio-grid">
          <section class="edvs-zone edvs-zone-map" data-zone="map">${opts.mapHtml || ''}</section>
          <section class="edvs-zone edvs-zone-charts" data-zone="charts">${opts.chartsHtml || ''}</section>
          <section class="edvs-zone edvs-zone-kpi" data-zone="kpi">${opts.kpiHtml || ''}</section>
          <section class="edvs-zone edvs-zone-text" data-zone="text">${opts.textHtml || ''}</section>
        </div>
      </div>
    `;
  }

  function isPresentationMode() {
    return document.body.classList.contains(PRESENTATION_CLASS);
  }

  function setPresentationMode(enabled) {
    const on = Boolean(enabled);
    document.body.classList.toggle(PRESENTATION_CLASS, on);
    document.querySelectorAll('[data-edvs-presentation-toggle]').forEach((btn) => {
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
      btn.textContent = on ? 'Quitter Présentation' : 'Mode Présentation';
    });
    // Règle UX : barre de sortie toujours visible en mode présentation
    let bar = document.querySelector('#edvs-presentation-bar');
    if (on) {
      if (!bar) {
        bar = document.createElement('div');
        bar.id = 'edvs-presentation-bar';
        bar.className = 'edvs-presentation-bar';
        bar.innerHTML = `
          <button type="button" class="edvs-presentation-back" data-edvs-presentation-exit>← Retour</button>
          <p>SIG-FDSU RDC — Mode Présentation DG</p>
          <button type="button" class="primary-button" data-edvs-presentation-exit>Quitter le Mode Présentation</button>
        `;
        document.body.appendChild(bar);
      }
      bar.hidden = false;
    } else if (bar) {
      bar.hidden = true;
    }
    global.dispatchEvent(new CustomEvent('edvs:presentation', { detail: { enabled: on } }));
  }

  function bindPresentationControls(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-edvs-presentation-toggle]').forEach((btn) => {
      if (btn.dataset.edvsBound === 'true') return;
      btn.dataset.edvsBound = 'true';
      btn.addEventListener('click', () => setPresentationMode(!isPresentationMode()));
    });
    if (document.body.dataset.edvsPresentationEsc !== 'true') {
      document.body.dataset.edvsPresentationEsc = 'true';
      document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && isPresentationMode()) {
          event.preventDefault();
          setPresentationMode(false);
        }
      });
      document.addEventListener('click', (event) => {
        const exit = event.target?.closest?.('[data-edvs-presentation-exit]');
        if (exit) setPresentationMode(false);
      });
    }
  }

  global.EdvsLayout = {
    shell,
    isPresentationMode,
    setPresentationMode,
    bindPresentationControls,
    PRESENTATION_CLASS,
  };
})(window);
