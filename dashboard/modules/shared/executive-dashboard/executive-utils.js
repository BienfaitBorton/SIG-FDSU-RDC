/**
 * EDVS — Utilitaires (cache, format, accessibilité)
 */
(function (global) {
  const cache = new Map();
  const MAX_CACHE = 120;

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatNumber(value, locale) {
    if (value == null || Number.isNaN(Number(value))) return '—';
    return Number(value).toLocaleString(locale || 'fr-FR');
  }

  function hashKey(payload) {
    try {
      return JSON.stringify(payload);
    } catch (e) {
      return String(payload);
    }
  }

  function cached(key, builder) {
    const k = typeof key === 'string' ? key : hashKey(key);
    if (cache.has(k)) return cache.get(k);
    const value = builder();
    cache.set(k, value);
    if (cache.size > MAX_CACHE) {
      const first = cache.keys().next().value;
      cache.delete(first);
    }
    return value;
  }

  function clearCache() {
    cache.clear();
  }

  function confidenceLabel(level) {
    const map = { high: 'Confiance élevée', medium: 'Confiance moyenne', low: 'Confiance faible' };
    return map[String(level || '').toLowerCase()] || 'Confiance non renseignée';
  }

  function trendMeta(direction) {
    const d = String(direction || 'flat').toLowerCase();
    if (d === 'up' || d === 'hausse') return { dir: 'up', label: 'Hausse', color: 'green' };
    if (d === 'down' || d === 'baisse') return { dir: 'down', label: 'Baisse', color: 'red' };
    return { dir: 'flat', label: 'Stable', color: 'gray' };
  }

  global.EdvsUtils = {
    escapeHtml,
    formatNumber,
    hashKey,
    cached,
    clearCache,
    confidenceLabel,
    trendMeta,
  };
})(window);
