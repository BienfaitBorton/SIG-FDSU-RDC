/**
 * Contexte territorial partagé — conservation entre modules.
 */
(function initTerritorialContext(global) {
  const STORAGE_KEY = 'fdsu.territorialContext.v1';

  const state = {
    trail: [{ level: 'rdc', id: 'rdc', label: 'RDC' }],
    selection: null,
    metric: 'priority',
    listeners: [],
  };

  function persist() {
    try {
      global.sessionStorage?.setItem(STORAGE_KEY, JSON.stringify({
        trail: state.trail,
        selection: state.selection,
        metric: state.metric,
      }));
    } catch (_err) { /* private mode */ }
  }

  function restore() {
    try {
      const raw = global.sessionStorage?.getItem(STORAGE_KEY);
      if (!raw) return;
      const data = JSON.parse(raw);
      if (Array.isArray(data.trail) && data.trail.length) state.trail = data.trail;
      if (data.selection) state.selection = data.selection;
      if (data.metric) state.metric = data.metric;
    } catch (_err) { /* ignore */ }
  }

  function emit() {
    state.listeners.forEach((fn) => {
      try { fn(getSnapshot()); } catch (_e) { /* isolé */ }
    });
    if (global.DecisionWorkspace?.setTrail) {
      global.DecisionWorkspace.setTrail(state.trail, { applyFilters: false });
    }
  }

  function getSnapshot() {
    return {
      trail: state.trail.slice(),
      selection: state.selection ? { ...state.selection } : null,
      metric: state.metric,
    };
  }

  function setMetric(metricId) {
    state.metric = metricId || 'priority';
    persist();
    emit();
  }

  function setTrail(trail) {
    state.trail = Array.isArray(trail) && trail.length
      ? trail.map((s) => ({ level: s.level, id: String(s.id), label: s.label || String(s.id) }))
      : [{ level: 'rdc', id: 'rdc', label: 'RDC' }];
    const last = state.trail[state.trail.length - 1];
    state.selection = last.level === 'rdc' ? null : {
      level: last.level,
      id: last.id,
      name: last.label,
      province: state.trail.find((s) => s.level === 'province')?.label,
    };
    persist();
    emit();
  }

  function select(entity) {
    if (!entity) {
      setTrail([{ level: 'rdc', id: 'rdc', label: 'RDC' }]);
      return;
    }
    const trail = [{ level: 'rdc', id: 'rdc', label: 'RDC' }];
    if (entity.province || entity.level === 'province') {
      const pid = entity.province_id || (entity.level === 'province' ? entity.id : entity.province);
      const plabel = entity.province_name || (entity.level === 'province' ? entity.name : entity.province);
      if (pid || plabel) trail.push({ level: 'province', id: String(pid || plabel), label: String(plabel || pid) });
    }
    if (entity.level === 'territoire' || entity.territoire_id || entity.territoire) {
      trail.push({
        level: 'territoire',
        id: String(entity.territoire_id || entity.id || entity.territoire),
        label: String(entity.name || entity.territoire_name || entity.territoire || entity.id),
      });
    }
    state.selection = {
      level: entity.level || trail[trail.length - 1].level,
      id: String(entity.id || trail[trail.length - 1].id),
      name: entity.name || trail[trail.length - 1].label,
      province: trail.find((s) => s.level === 'province')?.label,
    };
    state.trail = trail;
    persist();
    emit();
  }

  function onChange(fn) {
    state.listeners.push(fn);
    return () => {
      state.listeners = state.listeners.filter((x) => x !== fn);
    };
  }

  restore();

  global.TerritorialContext = {
    get: getSnapshot,
    setMetric,
    setTrail,
    select,
    onChange,
    restore,
    persist,
  };
})(typeof window !== 'undefined' ? window : globalThis);
