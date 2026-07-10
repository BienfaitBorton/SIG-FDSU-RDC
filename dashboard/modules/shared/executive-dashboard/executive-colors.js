/**
 * EDVS — Charte graphique officielle SIG-FDSU RDC
 * Interdiction des couleurs aléatoires.
 */
(function (global) {
  const EdvsColors = Object.freeze({
    green: { token: 'green', hex: '#16a34a', soft: 'rgba(22, 163, 74, 0.14)', meaning: 'Positif / opérationnel / confiance élevée' },
    orange: { token: 'orange', hex: '#ea580c', soft: 'rgba(234, 88, 12, 0.14)', meaning: 'Attention / priorité élevée' },
    red: { token: 'red', hex: '#dc2626', soft: 'rgba(220, 38, 38, 0.14)', meaning: 'Critique / alerte / risque' },
    blue: { token: 'blue', hex: '#2563eb', soft: 'rgba(37, 99, 235, 0.14)', meaning: 'Information / contexte stratégique' },
    gray: { token: 'gray', hex: '#64748b', soft: 'rgba(100, 116, 139, 0.14)', meaning: 'Indisponible / non sourcé / neutre technique' },
    yellow: { token: 'yellow', hex: '#ca8a04', soft: 'rgba(202, 138, 4, 0.16)', meaning: 'Partiel / estimé / démonstration' },
  });

  const PRIORITY_COLOR = Object.freeze({
    critical: 'red',
    high: 'orange',
    medium: 'yellow',
    low: 'blue',
    operational: 'green',
    unavailable: 'gray',
  });

  function resolve(token) {
    return EdvsColors[token] || EdvsColors.gray;
  }

  function forPriority(level) {
    return resolve(PRIORITY_COLOR[String(level || '').toLowerCase()] || 'gray');
  }

  function forConfidence(level) {
    const map = { high: 'green', medium: 'yellow', low: 'orange', unavailable: 'gray' };
    return resolve(map[String(level || '').toLowerCase()] || 'gray');
  }

  function forStatus(status) {
    const map = {
      confirmed: 'green',
      estimated: 'yellow',
      partial: 'yellow',
      demonstration: 'blue',
      unavailable: 'gray',
      not_sourced: 'gray',
    };
    return resolve(map[String(status || '').toLowerCase()] || 'gray');
  }

  global.EdvsColors = { palette: EdvsColors, resolve, forPriority, forConfidence, forStatus, PRIORITY_COLOR };
})(window);
