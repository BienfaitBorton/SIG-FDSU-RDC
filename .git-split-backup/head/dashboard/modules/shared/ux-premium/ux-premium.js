/**
 * SIG-FDSU — UX Premium helpers (v1.0)
 * États métier, légendes carte, KPI interactifs — sans dépendance externe.
 */
(function initUxPremium(global) {
  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function stateHtml(kind, title, detail, hint) {
    const cls = kind === 'error' ? 'is-error' : kind === 'loading' ? 'is-loading' : 'is-empty';
    return `
      <div class="ux-state ${cls}" role="status">
        <strong>${escapeHtml(title)}</strong>
        ${detail ? `<span>${escapeHtml(detail)}</span>` : ''}
        ${hint ? `<span class="ux-state-hint">${escapeHtml(hint)}</span>` : ''}
      </div>
    `;
  }

  function tableEmptyRow(colspan, title, detail) {
    return `<tr class="ux-table-empty"><td colspan="${Number(colspan) || 1}">${stateHtml('empty', title, detail || 'Aucune donnée à afficher pour ce filtre.')}</td></tr>`;
  }

  /**
   * Injecte une légende compacte dans un conteneur carte (position relative).
   * items: [{ className: 'is-site', label: 'Site FDSU' }, ...]
   */
  function mountMapLegend(hostSelector, options = {}) {
    const host = typeof hostSelector === 'string'
      ? document.querySelector(hostSelector)
      : hostSelector;
    if (!host) return null;

    let shell = host.closest('.ux-map-shell, .decision-engine-map-shell, .decision-center-map-shell, .dashboard-national-map-shell, .cartography-map-stage');
    if (!shell) {
      shell = host.parentElement;
      if (shell) shell.classList.add('ux-map-shell');
    }
    if (!shell) return null;

    // Dashboard : coquille flex multi-blocs — ancrer la légende sur la carte elle-même
    const attachTo = shell.classList.contains('dashboard-national-map-shell') ? host : shell;
    if (attachTo === host) {
      host.classList.add('ux-map-host');
    }
    shell.classList.add('ux-map-shell-ready');

    const safeId = String(options.id || `ux-legend-${Math.random().toString(36).slice(2, 8)}`).replace(/[^a-zA-Z0-9_-]/g, '');
    let legend = document.getElementById(safeId);
    if (!legend) {
      legend = document.createElement('aside');
      legend.id = safeId;
      legend.className = 'ux-map-legend';
      legend.setAttribute('aria-label', options.title || 'Légende');
      attachTo.appendChild(legend);
    } else if (legend.parentElement !== attachTo) {
      attachTo.appendChild(legend);
    }

    const items = options.items || [
      { className: 'is-poly', label: 'Province / territoire' },
      { className: 'is-site', label: 'Site FDSU' },
    ];

    legend.innerHTML = `
      <button type="button" class="ux-map-legend-toggle" aria-expanded="true">${escapeHtml(options.title || 'Légende')}</button>
      <div class="ux-map-legend-body">
        ${options.sectionTitle ? `<p class="ux-map-legend-title">${escapeHtml(options.sectionTitle)}</p>` : ''}
        <ul class="ux-map-legend-list">
          ${items.map((item) => `
            <li><span class="ux-swatch ${escapeHtml(item.className || '')}"></span>${escapeHtml(item.label || '')}</li>
          `).join('')}
        </ul>
      </div>
    `;

    const toggle = legend.querySelector('.ux-map-legend-toggle');
    if (toggle && toggle.dataset.bound !== 'true') {
      toggle.dataset.bound = 'true';
      toggle.addEventListener('click', () => {
        const collapsed = legend.classList.toggle('is-collapsed');
        toggle.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
      });
    }
    return legend;
  }

  function bindInteractiveKpis(root = document) {
    // Cartes Centre de Décision : clic sur la carte (hors bouton déjà géré)
    root.querySelectorAll('.decision-center-kpi-card[data-kpi-key]').forEach((card) => {
      if (card.dataset.uxBound === 'true') return;
      card.dataset.uxBound = 'true';
      card.setAttribute('role', 'button');
      card.setAttribute('tabindex', '0');
      const open = () => {
        const key = card.getAttribute('data-kpi-key');
        const btn = card.querySelector(`[data-kpi-detail="${key}"]`) || card.querySelector('[data-kpi-detail]');
        if (btn) {
          btn.click();
          return;
        }
        if (key && typeof global.openDecisionWorkspace === 'function') {
          global.openDecisionWorkspace({ kpiKey: key, returnHash: 'decision-view' });
        } else if (key && typeof global.openDecisionDetail === 'function') {
          global.openDecisionDetail(key);
        } else if (key) {
          global.location.hash = `decision-detail/${encodeURIComponent(key.replace(/_/g, '-'))}`;
        }
      };
      card.addEventListener('click', (event) => {
        if (event.target?.closest?.('button, a, input, select')) return;
        open();
      });
      card.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          open();
        }
      });
    });
  }

  function bindEdvsKpiClicks(root = document) {
    root.querySelectorAll('.edvs-kpi-card[data-detail-key]').forEach((card) => {
      if (card.dataset.uxBound === 'true') return;
      card.dataset.uxBound = 'true';
      card.classList.add('is-interactive');
      card.setAttribute('role', 'button');
      card.setAttribute('tabindex', '0');
      const open = () => {
        const key = card.getAttribute('data-detail-key');
        const route = card.getAttribute('data-detail-route');
        if (route) {
          global.location.hash = String(route).replace(/^#/, '');
          return;
        }
        if (key && typeof global.openDecisionWorkspace === 'function') {
          global.openDecisionWorkspace({ kpiKey: key, returnHash: 'decision-view' });
          return;
        }
        if (typeof global.openDecisionDetail === 'function' && key) {
          global.openDecisionDetail(key);
          return;
        }
        if (key) global.location.hash = `decision-detail/${encodeURIComponent(key.replace(/_/g, '-'))}`;
      };
      card.addEventListener('click', open);
      card.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          open();
        }
      });
    });
  }

  function installDefaultLegends() {
    mountMapLegend('#decision-center-national-map', {
      id: 'ux-legend-decision-national',
      title: 'Légende',
      sectionTitle: 'Couches',
      items: [
        { className: 'is-poly', label: 'Province' },
        { className: 'is-site', label: 'Site FDSU (si affiché)' },
      ],
    });
    mountMapLegend('#dashboard-national-map', {
      id: 'ux-legend-dashboard-national',
      title: 'Légende',
      sectionTitle: 'Référentiel',
      items: [
        { className: 'is-poly', label: 'Province / territoire' },
        { className: 'is-site', label: 'Site FDSU' },
      ],
    });
    mountMapLegend('#ti-map', {
      id: 'ux-legend-ti',
      title: 'Légende',
      items: [
        { className: 'is-poly', label: 'Territoire' },
        { className: 'is-site', label: 'Site FDSU' },
        { className: 'is-ccn', label: 'CCN' },
        { className: 'is-health', label: 'Santé' },
        { className: 'is-uncovered', label: 'Localité non couverte' },
      ],
    });
    mountMapLegend('#ccn-map', {
      id: 'ux-legend-ccn',
      title: 'Légende',
      items: [
        { className: 'is-ccn', label: 'Centre communautaire' },
        { className: 'is-site', label: 'Site FDSU' },
      ],
    });
    mountMapLegend('#geocoding-map', {
      id: 'ux-legend-geocoding',
      title: 'Légende',
      items: [
        { className: 'is-ok', label: 'Géocodage validé' },
        { className: 'is-warn', label: 'À vérifier' },
        { className: 'is-fail', label: 'Échec / à corriger' },
      ],
    });
    mountMapLegend('#dxl-map', {
      id: 'ux-legend-dxl',
      title: 'Légende',
      items: [
        { className: 'is-site', label: 'Actif' },
        { className: 'is-uncovered', label: 'Besoin / localité' },
      ],
    });
    mountMapLegend('#decision-detail-map', {
      id: 'ux-legend-decision-detail',
      title: 'Légende',
      items: [
        { className: 'is-critical', label: 'Priorité critique' },
        { className: 'is-high', label: 'Priorité élevée' },
        { className: 'is-medium', label: 'Priorité moyenne' },
        { className: 'is-low', label: 'Priorité faible' },
      ],
    });
  }

  function boot() {
    bindInteractiveKpis(document);
    bindEdvsKpiClicks(document);
    installDefaultLegends();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  // Rebind après navigation modules (hash)
  global.addEventListener('hashchange', () => {
    global.setTimeout(() => {
      bindInteractiveKpis(document);
      bindEdvsKpiClicks(document);
      installDefaultLegends();
    }, 200);
  });

  global.UxPremium = {
    escapeHtml,
    stateHtml,
    tableEmptyRow,
    mountMapLegend,
    bindInteractiveKpis,
    bindEdvsKpiClicks,
    installDefaultLegends,
    version: '1.0.0',
  };
})(typeof window !== 'undefined' ? window : globalThis);
