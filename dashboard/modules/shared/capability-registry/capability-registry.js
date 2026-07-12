/**
 * Capability Registry — Zero Decorative Actions
 * Une capacité absente ⇒ bouton masqué ou disabled avec motif métier.
 */
(function initCapabilityRegistry(global) {
  const API_BASE = `${global.location.protocol}//${global.location.hostname}:8001`;

  const DEFAULTS = {
    export_excel: true,
    export_pdf: false,
    export_powerpoint: false,
    mission_planning: false,
    simulation: false,
    comparison: false,
    map_navigation: true,
  };

  const NOTES = {
    export_pdf: 'Export PDF non encore activé pour ce dossier',
    export_powerpoint: 'Export PowerPoint non encore activé pour ce dossier',
    mission_planning: 'Préparation de mission non encore disponible',
    simulation: 'Simulation non encore branchée',
    comparison: 'Comparaison non encore disponible',
  };

  const state = {
    loaded: false,
    capabilities: { ...DEFAULTS },
    notes: { ...NOTES },
  };

  function isEnabled(key) {
    return Boolean(state.capabilities[key]);
  }

  function reason(key) {
    return state.notes[key] || 'Fonctionnalité non disponible';
  }

  function applyButton(btn, capabilityKey, options = {}) {
    if (!btn) return;
    const enabled = isEnabled(capabilityKey);
    const hideWhenUnavailable = options.hideWhenUnavailable === true;
    if (!enabled && hideWhenUnavailable) {
      btn.hidden = true;
      btn.setAttribute('aria-hidden', 'true');
      return;
    }
    btn.hidden = false;
    btn.disabled = !enabled;
    btn.setAttribute('aria-disabled', enabled ? 'false' : 'true');
    if (!enabled) {
      const tip = reason(capabilityKey);
      btn.title = tip;
      btn.setAttribute('data-capability-reason', tip);
      btn.classList.add('is-capability-disabled');
    } else {
      btn.classList.remove('is-capability-disabled');
      btn.removeAttribute('data-capability-reason');
    }
  }

  function setBusy(btn, busy, loadingLabel) {
    if (!btn) return;
    if (busy) {
      btn.dataset.prevLabel = btn.textContent || '';
      btn.disabled = true;
      btn.classList.add('is-loading');
      if (loadingLabel) btn.textContent = loadingLabel;
    } else {
      btn.classList.remove('is-loading');
      if (btn.dataset.prevLabel) btn.textContent = btn.dataset.prevLabel;
      delete btn.dataset.prevLabel;
      const cap = btn.getAttribute('data-capability');
      if (cap && !isEnabled(cap)) btn.disabled = true;
      else btn.disabled = false;
    }
  }

  function load() {
    return fetch(`${API_BASE}/api/exports/capabilities`, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((payload) => {
        if (payload?.capabilities) {
          state.capabilities = { ...DEFAULTS, ...payload.capabilities };
        }
        if (payload?.notes) {
          state.notes = { ...NOTES, ...payload.notes };
        }
        state.loaded = true;
        return state;
      })
      .catch(() => {
        state.loaded = true;
        return state;
      });
  }

  global.CapabilityRegistry = {
    version: '1.0.0',
    state,
    load,
    isEnabled,
    reason,
    applyButton,
    setBusy,
    DEFAULTS,
  };
})(typeof window !== 'undefined' ? window : globalThis);
