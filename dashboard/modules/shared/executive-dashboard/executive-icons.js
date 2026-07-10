/**
 * EDVS — Icônes SVG minimalistes (pilotage stratégique)
 */
(function (global) {
  const ICONS = {
    map: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M9 4l6 2 6-2v16l-6 2-6-2-6 2V6l6-2zm0 2.2V18l6 2V8.2l-6-2z"/></svg>',
    sites: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a7 7 0 017 7c0 5.25-7 13-7 13S5 14.25 5 9a7 7 0 017-7zm0 9.5A2.5 2.5 0 1012 6a2.5 2.5 0 000 5.5z"/></svg>',
    ccn: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4 5h16v4H4V5zm0 5h10v9H4v-9zm12 0h4v9h-4v-9z"/></svg>',
    alert: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 3l10 18H2L12 3zm0 5l-6.5 11h13L12 8zm-1 3h2v4h-2v-4zm0 5h2v2h-2v-2z"/></svg>',
    decision: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7l3-7z"/></svg>',
    program: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4 4h16v4H4V4zm0 6h10v10H4V10zm12 0h4v10h-4V10z"/></svg>',
    people: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M9 11a3 3 0 110-6 3 3 0 010 6zm6 0a3 3 0 110-6 3 3 0 010 6zM3 20a6 6 0 0112 0H3zm10 0a5.9 5.9 0 013-4.9A6 6 0 0121 20h-8z"/></svg>',
    trendUp: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4 18l6-6 4 4 6-8v6h2V4h-10v2h6l-6 8-4-4-6 6 2 2z"/></svg>',
    trendDown: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4 6l6 6 4-4 6 8v-6h2v10H12v-2h6l-6-8-4 4-6-6 2-2z"/></svg>',
    gauge: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 3a9 9 0 019 9h-2a7 7 0 10-7 7v2a9 9 0 010-18zm1 9.4l3.5-3.5-1.4-1.4L11 10.6V16h2v-3.6z"/></svg>',
    data: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4 4h16v4H4V4zm0 6h16v4H4v-4zm0 6h16v4H4v-4z"/></svg>',
  };

  function icon(name, className) {
    const svg = ICONS[name] || ICONS.data;
    return `<span class="edvs-icon ${className || ''}" data-icon="${name}">${svg}</span>`;
  }

  global.EdvsIcons = { icon, ICONS };
})(window);
