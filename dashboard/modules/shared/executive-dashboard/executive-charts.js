/**
 * EDVS — Graphiques SVG (barres empilées, radar, gauge, waterfall, treemap, heatmap)
 * Pas de dépendance externe. Cache via EdvsUtils.
 */
(function (global) {
  function stackedBar(options) {
    const U = global.EdvsUtils;
    const C = global.EdvsColors;
    const opts = options || {};
    const series = opts.series || [];
    const categories = opts.categories || [];
    return U.cached(['stacked', opts.title, series, categories], () => {
      const totals = categories.map((_, i) => series.reduce((sum, s) => sum + (Number(s.values[i]) || 0), 0));
      const max = Math.max(...totals, 1);
      const bars = categories.map((cat, i) => {
        let left = 0;
        const segments = series.map((s) => {
          const val = Number(s.values[i]) || 0;
          const width = (val / max) * 100;
          const color = C.resolve(s.color || 'blue');
          const seg = `<span class="edvs-stack-seg" style="left:${left}%;width:${width}%;background:${color.hex}" title="${U.escapeHtml(s.label)}: ${U.formatNumber(val)}"></span>`;
          left += width;
          return seg;
        }).join('');
        return `<div class="edvs-stack-row"><span class="edvs-stack-label">${U.escapeHtml(cat)}</span><div class="edvs-stack-track">${segments}</div></div>`;
      }).join('');
      const legend = series.map((s) => {
        const color = C.resolve(s.color || 'blue');
        return `<span class="edvs-legend-item"><i style="background:${color.hex}"></i>${U.escapeHtml(s.label)}</span>`;
      }).join('');
      return `<section class="edvs-card edvs-chart" data-edvs="stacked-bar"><header class="edvs-card-header"><h3>${U.escapeHtml(opts.title || 'Comparaison')}</h3><div class="edvs-legend">${legend}</div></header><div class="edvs-stack-chart">${bars}</div></section>`;
    });
  }

  function radar(options) {
    const U = global.EdvsUtils;
    const C = global.EdvsColors;
    const opts = options || {};
    const axes = opts.axes || [];
    const color = C.resolve(opts.color || 'blue');
    const n = axes.length || 1;
    const cx = 110;
    const cy = 110;
    const r = 80;
    return U.cached(['radar', opts.title, axes], () => {
      const points = axes.map((axis, i) => {
        const angle = (-Math.PI / 2) + (i * 2 * Math.PI) / n;
        const value = Math.max(0, Math.min(100, Number(axis.value) || 0)) / 100;
        const x = cx + Math.cos(angle) * r * value;
        const y = cy + Math.sin(angle) * r * value;
        return `${x},${y}`;
      }).join(' ');
      const grid = [0.25, 0.5, 0.75, 1].map((scale) => {
        const ring = axes.map((_, i) => {
          const angle = (-Math.PI / 2) + (i * 2 * Math.PI) / n;
          return `${cx + Math.cos(angle) * r * scale},${cy + Math.sin(angle) * r * scale}`;
        }).join(' ');
        return `<polygon points="${ring}" fill="none" stroke="rgba(148,163,184,0.35)" stroke-width="1"/>`;
      }).join('');
      const labels = axes.map((axis, i) => {
        const angle = (-Math.PI / 2) + (i * 2 * Math.PI) / n;
        const x = cx + Math.cos(angle) * (r + 18);
        const y = cy + Math.sin(angle) * (r + 18);
        return `<text x="${x}" y="${y}" text-anchor="middle" class="edvs-radar-label">${U.escapeHtml(axis.label)}</text>`;
      }).join('');
      return `<section class="edvs-card edvs-chart" data-edvs="radar"><header class="edvs-card-header"><h3>${U.escapeHtml(opts.title || 'Radar')}</h3></header><svg class="edvs-radar" viewBox="0 0 220 220" role="img" aria-label="${U.escapeHtml(opts.title || 'Radar')}">${grid}<polygon points="${points}" fill="${color.soft}" stroke="${color.hex}" stroke-width="2"/>${labels}</svg></section>`;
    });
  }

  function gauge(options) {
    const U = global.EdvsUtils;
    const C = global.EdvsColors;
    const opts = options || {};
    const value = Math.max(0, Math.min(100, Number(opts.value) || 0));
    const color = C.resolve(opts.color || (value >= 70 ? 'green' : value >= 40 ? 'yellow' : 'orange'));
    const angle = -90 + (value / 100) * 180;
    return U.cached(['gauge', opts.title, value, opts.color], () => `
      <section class="edvs-card edvs-chart" data-edvs="gauge">
        <header class="edvs-card-header"><h3>${U.escapeHtml(opts.title || 'Jauge')}</h3></header>
        <div class="edvs-gauge">
          <svg viewBox="0 0 120 70" aria-label="${U.escapeHtml(opts.title || 'Jauge')}">
            <path d="M10 60 A50 50 0 0 1 110 60" fill="none" stroke="rgba(148,163,184,0.25)" stroke-width="10" stroke-linecap="round"/>
            <path d="M10 60 A50 50 0 0 1 110 60" fill="none" stroke="${color.hex}" stroke-width="10" stroke-linecap="round"
              stroke-dasharray="${(value / 100) * 157} 157"/>
            <line x1="60" y1="60" x2="60" y2="22" stroke="${color.hex}" stroke-width="2" transform="rotate(${angle} 60 60)"/>
            <circle cx="60" cy="60" r="4" fill="${color.hex}"/>
          </svg>
          <p class="edvs-gauge-value">${U.formatNumber(value)}%</p>
          <p class="edvs-muted">${U.escapeHtml(opts.subtitle || '')}</p>
        </div>
      </section>
    `);
  }

  function waterfall(options) {
    const U = global.EdvsUtils;
    const C = global.EdvsColors;
    const opts = options || {};
    const steps = opts.steps || [];
    let running = 0;
    const maxAbs = Math.max(...steps.map((s) => Math.abs(Number(s.value) || 0)), 1);
    const rows = steps.map((step) => {
      const val = Number(step.value) || 0;
      const color = C.resolve(step.color || (val >= 0 ? 'green' : 'red'));
      const width = Math.max(4, (Math.abs(val) / maxAbs) * 100);
      running += val;
      return `<div class="edvs-water-row"><span>${U.escapeHtml(step.label)}</span><div class="edvs-water-track"><span style="width:${width}%;background:${color.hex}"></span></div><strong>${U.formatNumber(val)}</strong></div>`;
    }).join('');
    return U.cached(['waterfall', opts.title, steps], () => `
      <section class="edvs-card edvs-chart" data-edvs="waterfall">
        <header class="edvs-card-header"><h3>${U.escapeHtml(opts.title || 'Contribution au score')}</h3><span class="edvs-muted">Total ${U.formatNumber(running)}</span></header>
        <div class="edvs-waterfall">${rows}</div>
      </section>
    `);
  }

  function treemap(options) {
    const U = global.EdvsUtils;
    const C = global.EdvsColors;
    const opts = options || {};
    const items = opts.items || [];
    const total = items.reduce((s, i) => s + (Number(i.value) || 0), 0) || 1;
    const cells = items.map((item) => {
      const color = C.resolve(item.color || 'blue');
      const flex = Math.max(1, Math.round(((Number(item.value) || 0) / total) * 100));
      return `<div class="edvs-tree-cell" style="flex:${flex};background:${color.soft};border-color:${color.hex}"><strong>${U.escapeHtml(item.label)}</strong><span>${U.formatNumber(item.value)}</span></div>`;
    }).join('');
    return U.cached(['treemap', opts.title, items], () => `
      <section class="edvs-card edvs-chart" data-edvs="treemap">
        <header class="edvs-card-header"><h3>${U.escapeHtml(opts.title || 'Répartition')}</h3></header>
        <div class="edvs-treemap">${cells || '<p class="edvs-empty">Aucune donnée</p>'}</div>
      </section>
    `);
  }

  function heatmap(options) {
    const U = global.EdvsUtils;
    const C = global.EdvsColors;
    const opts = options || {};
    const rows = opts.rows || [];
    const cols = opts.cols || [];
    const matrix = opts.matrix || [];
    const cells = rows.map((row, r) => `
      <div class="edvs-heat-row">
        <span class="edvs-heat-label">${U.escapeHtml(row)}</span>
        ${(cols.map((_, c) => {
          const raw = Number((matrix[r] || [])[c]) || 0;
          const level = raw >= 85 ? 'red' : raw >= 70 ? 'orange' : raw >= 50 ? 'yellow' : 'blue';
          const color = C.resolve(level);
          return `<span class="edvs-heat-cell" style="background:${color.soft};color:${color.hex}" title="${U.escapeHtml(row)} / ${U.escapeHtml(cols[c])}: ${raw}">${raw || '—'}</span>`;
        }).join(''))}
      </div>
    `).join('');
    return U.cached(['heatmap', opts.title, matrix], () => `
      <section class="edvs-card edvs-chart" data-edvs="heatmap">
        <header class="edvs-card-header"><h3>${U.escapeHtml(opts.title || 'Heatmap priorités')}</h3></header>
        <div class="edvs-heat-head"><span></span>${cols.map((c) => `<span>${U.escapeHtml(c)}</span>`).join('')}</div>
        ${cells}
      </section>
    `);
  }

  global.EdvsCharts = { stackedBar, radar, gauge, waterfall, treemap, heatmap };
})(window);
