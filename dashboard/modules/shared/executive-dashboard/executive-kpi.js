/**
 * EDVS — Executive KPI Card + sparkline
 */
(function (global) {
  function sparkline(points, colorHex) {
    const values = (points || []).map(Number).filter((n) => !Number.isNaN(n));
    if (values.length < 2) {
      return '<svg class="edvs-sparkline" viewBox="0 0 80 24" aria-hidden="true"></svg>';
    }
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const coords = values.map((v, i) => {
      const x = (i / (values.length - 1)) * 80;
      const y = 22 - ((v - min) / span) * 18;
      return `${x},${y}`;
    });
    return `<svg class="edvs-sparkline" viewBox="0 0 80 24" aria-hidden="true"><polyline fill="none" stroke="${colorHex}" stroke-width="2" points="${coords.join(' ')}"/></svg>`;
  }

  function renderKpiCard(options) {
    const U = global.EdvsUtils;
    const C = global.EdvsColors;
    const I = global.EdvsIcons;
    const opts = options || {};
    const color = C.resolve(opts.color || 'blue');
    const conf = C.forConfidence(opts.confidence);
    const trend = U.trendMeta(opts.trend);
    const trendColor = C.resolve(trend.color);
    const cacheKey = ['kpi', opts.id || opts.label, opts.value, opts.trend, opts.confidence, opts.sparkline];

    return U.cached(cacheKey, () => {
      const evolution = opts.evolution == null ? '' : `<span class="edvs-kpi-evo">${U.escapeHtml(opts.evolution)}</span>`;
      const confHtml = opts.confidence
        ? `<span class="edvs-chip" style="--edvs-chip:${conf.hex}">${U.escapeHtml(U.confidenceLabel(opts.confidence))}</span>`
        : '';
      return `
        <article class="edvs-kpi-card${opts.detailKey || opts.onClick || opts.detailRoute ? ' is-interactive' : ''}" data-edvs="kpi"${opts.detailKey ? ` data-detail-key="${U.escapeHtml(opts.detailKey)}"` : ''}${opts.detailRoute ? ` data-detail-route="${U.escapeHtml(opts.detailRoute)}"` : ''} style="--edvs-accent:${color.hex}; --edvs-soft:${color.soft}">
          <div class="edvs-kpi-top">
            ${I.icon(opts.icon || 'data', 'edvs-kpi-icon')}
            <p class="edvs-kpi-label">${U.escapeHtml(opts.label || '')}</p>
          </div>
          <p class="edvs-kpi-value">${U.escapeHtml(opts.valueDisplay != null ? opts.valueDisplay : U.formatNumber(opts.value))}</p>
          <div class="edvs-kpi-meta">
            <span class="edvs-kpi-trend" style="color:${trendColor.hex}">
              ${trend.dir === 'up' ? I.icon('trendUp') : trend.dir === 'down' ? I.icon('trendDown') : ''}
              ${U.escapeHtml(trend.label)}${evolution}
            </span>
            ${confHtml}
          </div>
          ${sparkline(opts.sparkline, color.hex)}
          ${opts.note ? `<p class="edvs-kpi-note">${U.escapeHtml(opts.note)}</p>` : ''}
          ${opts.detailKey || opts.detailRoute ? '<p class="ux-kpi-cta">Voir l’analyse →</p>' : ''}
        </article>
      `;
    });
  }

  function renderKpiGrid(items, className) {
    const cards = (items || []).map((item) => renderKpiCard(item)).join('');
    return `<div class="edvs-kpi-grid ${className || ''}" data-edvs="kpi-grid">${cards}</div>`;
  }

  global.EdvsKpi = { renderKpiCard, renderKpiGrid, sparkline };
})(window);
