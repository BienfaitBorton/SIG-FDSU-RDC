/**
 * Module Inventaire des Sites FDSU (#sites)
 * Réutilise /api/decision/sites/inventory — pas de référentiel concurrent.
 */
(function initSitesInventory(global) {
  const state = {
    initialized: false,
    loading: false,
    offset: 0,
    limit: 50,
    total: 0,
    sites: [],
    selected: null,
    filters: {
      program_code: '',
      status: '',
      province: '',
      territoire: '',
      priority: '',
      q: '',
    },
  };

  function shared() {
    return global.SigFdsuShared || {};
  }

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function displayName(site) {
    if (global.FdsuSiteDisplayName?.siteDisplayLabel) {
      return global.FdsuSiteDisplayName.siteDisplayLabel(site);
    }
    return site?.display_name || site?.name || site?.site_name || site?.site_code || 'Site FDSU';
  }

  function na(value) {
    if (value == null || value === '') return 'Non disponible';
    return String(value);
  }

  function formatNumber(value) {
    const n = Number(value);
    if (!Number.isFinite(n)) return '—';
    return n.toLocaleString('fr-FR');
  }

  function buildQuery() {
    const params = new URLSearchParams();
    Object.entries(state.filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    params.set('limit', String(state.limit));
    params.set('offset', String(state.offset));
    return params.toString();
  }

  function setStatus(message, isError) {
    const el = document.querySelector('#sites-inventory-status');
    if (!el) return;
    el.textContent = message || '';
    el.classList.toggle('is-error', Boolean(isError));
  }

  function renderKpis(payload) {
    const counts = payload?.counts || {};
    const meta = payload?._meta || {};
    const badge = document.querySelector('#sites-panel .panel-badge');
    if (badge) {
      badge.textContent = `${formatNumber(counts.primary || counts.sites_20476 || 0)} sites (national)`;
    }
    const host = document.querySelector('#sites-inventory-kpis');
    if (!host) return;
    const cards = [
      {
        label: 'Programme national',
        value: counts.sites_20476,
        hint: meta.primary_counter?.definition || 'Sites 20 476',
      },
      { label: 'Sites 40', value: counts.sites_40, hint: 'En exécution' },
      { label: 'Sites 300', value: counts.sites_300, hint: 'Planifié' },
      {
        label: 'Portefeuille 340',
        value: counts.portfolio_340,
        hint: 'Agrégat 40 + 300 (pas un programme)',
      },
    ];
    host.innerHTML = cards
      .map(
        (card) => `
      <article class="sites-inv-kpi" title="${escapeHtml(card.hint)}">
        <strong>${escapeHtml(formatNumber(card.value))}</strong>
        <span>${escapeHtml(card.label)}</span>
      </article>`,
      )
      .join('');

    const programsHost = document.querySelector('#sites-inventory-programs');
    if (programsHost) {
      const programs = payload?.programs || [];
      programsHost.innerHTML = programs
        .map(
          (p) => `
        <article class="sites-inv-program-card">
          <h4>${escapeHtml(p.label || p.program_code)}</h4>
          <p><strong>${escapeHtml(formatNumber(p.site_count))}</strong> sites · ${escapeHtml(p.status_label || p.phase || '')}</p>
          <p class="sites-inv-muted">${escapeHtml(p.description || '')}</p>
        </article>`,
        )
        .join('');
    }

    const note = document.querySelector('#sites-inventory-counter-note');
    if (note && meta.primary_counter) {
      note.textContent = meta.primary_counter.definition || '';
    }
  }

  function fillFacetSelect(selectId, values, current) {
    const select = document.querySelector(selectId);
    if (!select) return;
    const keep = current || '';
    const options = ['<option value="">Tous</option>']
      .concat(
        (values || []).map(
          (v) => `<option value="${escapeHtml(v)}"${v === keep ? ' selected' : ''}>${escapeHtml(v)}</option>`,
        ),
      );
    select.innerHTML = options.join('');
  }

  function renderTable(payload) {
    const tbody = document.querySelector('#sites-inventory-tbody');
    if (!tbody) return;
    const sites = payload?.sites || [];
    state.sites = sites;
    state.total = Number(payload?.total || 0);

    if (!sites.length) {
      tbody.innerHTML =
        '<tr><td colspan="10" class="sites-inv-empty">Aucun site pour ces filtres.</td></tr>';
      return;
    }

    tbody.innerHTML = sites
      .map((site) => {
        const name = displayName(site);
        const tech = site.technical_id || site.site_name || '';
        const score = site.priority_score != null ? Number(site.priority_score).toFixed(1) : '—';
        const geo = site.has_geometry || (site.latitude != null && site.longitude != null) ? 'Oui' : 'Non';
        return `
        <tr data-site-id="${escapeHtml(site.site_id)}" data-program="${escapeHtml(site.program_code || '')}">
          <td><code>${escapeHtml(na(site.site_code))}</code></td>
          <td title="${escapeHtml(tech)}">
            <strong>${escapeHtml(name)}</strong>
            ${tech && tech !== name ? `<small class="sites-inv-tech">${escapeHtml(tech)}</small>` : ''}
          </td>
          <td>${escapeHtml(na(site.program_label || site.programme || site.program_code))}</td>
          <td>${escapeHtml(na(site.province))}</td>
          <td>${escapeHtml(na(site.territoire))}</td>
          <td>${escapeHtml(na(site.status))}</td>
          <td>${escapeHtml(na(site.priority_level_label || site.priority_level || site.priority || site.priority_status))}</td>
          <td>${escapeHtml(score)}</td>
          <td>${escapeHtml(geo)}</td>
          <td class="sites-inv-actions">
            <button type="button" class="secondary-button sites-inv-detail-btn" title="Ouvrir la fiche">Fiche</button>
            <button type="button" class="secondary-button sites-inv-map-btn" title="Voir sur la carte">Carte</button>
          </td>
        </tr>`;
      })
      .join('');

    const pageInfo = document.querySelector('#sites-inventory-page-info');
    if (pageInfo) {
      const from = state.total ? state.offset + 1 : 0;
      const to = Math.min(state.offset + sites.length, state.total);
      pageInfo.textContent = `${formatNumber(from)}–${formatNumber(to)} / ${formatNumber(state.total)}`;
    }
  }

  function renderDetail(site) {
    const host = document.querySelector('#sites-inventory-detail');
    if (!host) return;
    if (!site) {
      host.innerHTML = '<p class="sites-inv-muted">Sélectionnez un site pour afficher la fiche métier.</p>';
      return;
    }
    const name = displayName(site);
    const tech = site.technical_id || (global.FdsuSiteDisplayName?.isTechnicalSiteIdentifier?.(site.site_name) ? site.site_name : null);
    const rows = [
      ['Code site', site.site_code],
      ['Nom métier', name],
      ['Identifiant technique', tech],
      ['Programme', site.program_label || site.programme || site.program_code],
      ['Statut', site.status],
      ['Province', site.province],
      ['Territoire', site.territoire],
      ['Zone', site.zone],
      ['Priorité', site.priority_level_label || site.priority_level || site.priority_status],
      ['Score', site.priority_score != null ? Number(site.priority_score).toFixed(1) : null],
      ['Population', site.population],
      ['Latitude', site.latitude],
      ['Longitude', site.longitude],
      ['Site opérateur proche', site.nearest_site],
      ['Distance', site.distance],
      ['Infrastructure de base (NCI)', site.infra_name],
      ['Provenance', site.source],
      ['Source libellé', site.display_name_source],
    ];

    host.innerHTML = `
      <header class="sites-inv-detail-head">
        <div>
          <p class="panel-label">Fiche site</p>
          <h3>${escapeHtml(name)}</h3>
          <p class="sites-inv-muted">${escapeHtml(site.program_label || '')} · ${escapeHtml(na(site.province))} / ${escapeHtml(na(site.territoire))}</p>
        </div>
        <div class="sites-inv-detail-actions">
          <button type="button" class="primary-button" id="sites-inv-open-map">Voir sur la carte</button>
          <button type="button" class="secondary-button" id="sites-inv-open-case">Dossier décisionnel</button>
          <button type="button" class="secondary-button" id="sites-inv-open-spatial">Impact spatial</button>
          <button type="button" class="secondary-button" id="sites-inv-open-ti">Intelligence territoriale</button>
        </div>
      </header>
      <dl class="sites-inv-detail-grid">
        ${rows
          .map(
            ([label, value]) => `
          <div>
            <dt>${escapeHtml(label)}</dt>
            <dd>${escapeHtml(na(value))}</dd>
          </div>`,
          )
          .join('')}
      </dl>
    `;

    document.querySelector('#sites-inv-open-map')?.addEventListener('click', () => openOnMap(site));
    document.querySelector('#sites-inv-open-case')?.addEventListener('click', () => {
      if (typeof global.openDecisionCase === 'function') {
        global.openDecisionCase('site', site.site_id, site.program_code);
      }
    });
    document.querySelector('#sites-inv-open-spatial')?.addEventListener('click', () => {
      if (typeof global.openSpatialImpact === 'function') {
        global.openSpatialImpact('site', site.site_id, site.program_code);
      } else if (typeof global.openDecisionCase === 'function') {
        global.openDecisionCase('site', site.site_id, site.program_code);
      }
    });
    document.querySelector('#sites-inv-open-ti')?.addEventListener('click', () => {
      if (site.territoire && global.TerritorialDigitalTwin?.open) {
        global.TerritorialDigitalTwin.open({
          entityType: 'territoire',
          entityId: site.territoire,
          returnHash: 'sites',
        });
      } else if (typeof global.navigateTo === 'function') {
        global.navigateTo('territorial-intelligence');
      } else {
        global.location.hash = 'territorial-intelligence';
      }
    });
  }

  function openOnMap(site) {
    const focus = {
      site_id: site.site_id,
      site_code: site.site_code,
      program_code: site.program_code,
      latitude: site.latitude,
      longitude: site.longitude,
      display_name: displayName(site),
    };
    if (typeof global.openDecisionSiteOnMap === 'function') {
      global.openDecisionSiteOnMap(focus);
      return;
    }
    try {
      global.sessionStorage?.setItem('fdsu.map.focusSite', JSON.stringify(focus));
    } catch (_e) {
      /* ignore */
    }
    global.location.hash = 'map';
  }

  async function loadInventory() {
    const fetchApiJson = shared().fetchApiJson;
    if (!fetchApiJson) {
      setStatus('API indisponible — module non initialisé.', true);
      return;
    }
    state.loading = true;
    setStatus('Chargement de l’inventaire…');
    const tbody = document.querySelector('#sites-inventory-tbody');
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="10" class="sites-inv-empty">Chargement…</td></tr>';
    }
    try {
      const payload = await fetchApiJson(`/api/decision/sites/inventory?${buildQuery()}`);
      renderKpis(payload);
      fillFacetSelect('#sites-filter-province', payload?.facets?.provinces, state.filters.province);
      fillFacetSelect('#sites-filter-territoire', payload?.facets?.territoires, state.filters.territoire);
      fillFacetSelect('#sites-filter-status', payload?.facets?.statuses, state.filters.status);
      renderTable(payload);
      setStatus(`${formatNumber(payload.total)} site(s) correspondant(s) aux filtres.`);
    } catch (error) {
      renderTable({ sites: [], total: 0 });
      setStatus(`Inventaire indisponible : ${error.message || error}`, true);
    } finally {
      state.loading = false;
    }
  }

  async function openDetail(siteId, programCode) {
    const fetchApiJson = shared().fetchApiJson;
    if (!fetchApiJson) return;
    try {
      const qs = programCode ? `?program_code=${encodeURIComponent(programCode)}` : '';
      const payload = await fetchApiJson(`/api/decision/sites/inventory/${encodeURIComponent(siteId)}${qs}`);
      state.selected = payload?.site || null;
      renderDetail(state.selected);
    } catch (error) {
      const fallback = state.sites.find((s) => String(s.site_id) === String(siteId));
      state.selected = fallback || null;
      renderDetail(state.selected);
      setStatus(`Fiche partielle : ${error.message || error}`, true);
    }
  }

  function readFiltersFromDom() {
    state.filters.program_code = document.querySelector('#sites-filter-program')?.value || '';
    state.filters.status = document.querySelector('#sites-filter-status')?.value || '';
    state.filters.province = document.querySelector('#sites-filter-province')?.value || '';
    state.filters.territoire = document.querySelector('#sites-filter-territoire')?.value || '';
    state.filters.priority = document.querySelector('#sites-filter-priority')?.value || '';
    state.filters.q = document.querySelector('#sites-filter-q')?.value?.trim() || '';
  }

  function bindEvents() {
    const panel = document.querySelector('#sites-panel');
    if (!panel || panel.dataset.sitesInvBound === 'true') return;
    panel.dataset.sitesInvBound = 'true';

    document.querySelector('#sites-filter-apply')?.addEventListener('click', () => {
      readFiltersFromDom();
      state.offset = 0;
      loadInventory();
    });
    document.querySelector('#sites-filter-q')?.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        readFiltersFromDom();
        state.offset = 0;
        loadInventory();
      }
    });
    ['#sites-filter-program', '#sites-filter-status', '#sites-filter-province', '#sites-filter-territoire', '#sites-filter-priority'].forEach(
      (sel) => {
        document.querySelector(sel)?.addEventListener('change', () => {
          readFiltersFromDom();
          state.offset = 0;
          loadInventory();
        });
      },
    );
    document.querySelector('#sites-inventory-prev')?.addEventListener('click', () => {
      state.offset = Math.max(0, state.offset - state.limit);
      loadInventory();
    });
    document.querySelector('#sites-inventory-next')?.addEventListener('click', () => {
      if (state.offset + state.limit < state.total) {
        state.offset += state.limit;
        loadInventory();
      }
    });

    panel.addEventListener('click', (event) => {
      const row = event.target?.closest?.('tr[data-site-id]');
      if (!row) return;
      const siteId = row.getAttribute('data-site-id');
      const program = row.getAttribute('data-program') || '';
      if (event.target?.closest?.('.sites-inv-map-btn')) {
        const site = state.sites.find((s) => String(s.site_id) === String(siteId));
        if (site) openOnMap(site);
        return;
      }
      openDetail(siteId, program);
    });
  }

  async function initialize() {
    bindEvents();
    renderDetail(null);
    readFiltersFromDom();
    await loadInventory();
    state.initialized = true;
  }

  global.SitesInventory = {
    initialize,
    reload: loadInventory,
    state,
  };
})(window);
