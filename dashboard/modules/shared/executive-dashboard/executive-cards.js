/**
 * EDVS — Cards / ranking / alertes / timeline
 */
(function (global) {
  function renderRanking(options) {
    const U = global.EdvsUtils;
    const C = global.EdvsColors;
    const opts = options || {};
    const items = opts.items || [];
    const cacheKey = ['rank', opts.title, items];

    return U.cached(cacheKey, () => {
      const max = Math.max(...items.map((i) => Number(i.value) || 0), 1);
      const rows = items.map((item, index) => {
        const color = C.resolve(item.color || opts.color || 'blue');
        const width = Math.max(4, ((Number(item.value) || 0) / max) * 100);
        return `
          <li class="edvs-rank-row">
            <span class="edvs-rank-pos">${index + 1}</span>
            <div class="edvs-rank-body">
              <div class="edvs-rank-head">
                <strong>${U.escapeHtml(item.label)}</strong>
                <span>${U.escapeHtml(item.valueDisplay != null ? item.valueDisplay : U.formatNumber(item.value))}</span>
              </div>
              <div class="edvs-rank-track"><span style="width:${width}%; background:${color.hex}"></span></div>
            </div>
          </li>
        `;
      }).join('');
      return `
        <section class="edvs-card edvs-ranking" data-edvs="ranking">
          <header class="edvs-card-header"><h3>${U.escapeHtml(opts.title || 'Classement')}</h3></header>
          <ol class="edvs-rank-list">${rows || '<li class="edvs-empty">Aucune donnée</li>'}</ol>
        </section>
      `;
    });
  }

  function renderAlertList(options) {
    const U = global.EdvsUtils;
    const C = global.EdvsColors;
    const I = global.EdvsIcons;
    const items = (options || {}).items || [];
    return `
      <section class="edvs-card edvs-alerts" data-edvs="alerts">
        <header class="edvs-card-header"><h3>${U.escapeHtml((options || {}).title || 'Alertes')}</h3></header>
        <ul class="edvs-alert-list">
          ${items.map((item) => {
            const color = C.forPriority(item.level || item.severity);
            return `<li style="--edvs-accent:${color.hex}">${I.icon('alert')} <div><strong>${U.escapeHtml(item.title)}</strong><p>${U.escapeHtml(item.message || '')}</p></div></li>`;
          }).join('') || '<li class="edvs-empty">Aucune alerte</li>'}
        </ul>
      </section>
    `;
  }

  function renderTimeline(options) {
    const U = global.EdvsUtils;
    const items = (options || {}).items || [];
    return `
      <section class="edvs-card edvs-timeline" data-edvs="timeline">
        <header class="edvs-card-header"><h3>${U.escapeHtml((options || {}).title || 'Historique')}</h3></header>
        <ol class="edvs-timeline-list">
          ${items.map((item) => `
            <li>
              <span class="edvs-timeline-dot"></span>
              <div>
                <strong>${U.escapeHtml(item.title)}</strong>
                <p>${U.escapeHtml(item.when || '')}</p>
                <p>${U.escapeHtml(item.detail || '')}</p>
              </div>
            </li>
          `).join('') || '<li class="edvs-empty">Aucun événement</li>'}
        </ol>
      </section>
    `;
  }

  function renderRecommendationCards(options) {
    const U = global.EdvsUtils;
    const C = global.EdvsColors;
    const items = (options || {}).items || [];
    return `
      <section class="edvs-card" data-edvs="recommendations">
        <header class="edvs-card-header"><h3>${U.escapeHtml((options || {}).title || 'Recommandations')}</h3></header>
        <div class="edvs-rec-grid">
          ${items.map((item) => {
            const color = C.forConfidence(item.confidence_level || item.confidence);
            return `
              <article class="edvs-rec-card" style="--edvs-accent:${color.hex}">
                <h4>${U.escapeHtml(item.action || item.title)}</h4>
                <p><strong>Pourquoi ?</strong> ${U.escapeHtml(item.why || '')}</p>
                <p class="edvs-muted">Doctrine : ${U.escapeHtml(item.doctrine?.id || item.doctrine || '—')}</p>
              </article>
            `;
          }).join('') || '<p class="edvs-empty">Aucune recommandation</p>'}
        </div>
      </section>
    `;
  }

  global.EdvsCards = {
    renderRanking,
    renderAlertList,
    renderTimeline,
    renderRecommendationCards,
  };
})(window);
