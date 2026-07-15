/**
 * Harmonisation terminologique institutionnelle — libellés UI uniquement.
 * Les identifiants techniques (routes, modules, scénarios) ne changent pas.
 */
(function initInstitutionalLabels(global) {
  const EXACT = {
    'Salle de Pilotage DG': 'Salle de Pilotage',
    'Présenter au DG': 'Présentation guidée',
    'Préparer un dossier DG': 'Préparer un dossier de décision',
    'Préparer un dossier de décision pour le DG': 'Préparer un dossier de décision',
    'Ouvrir le dossier DG': 'Ouvrir le dossier de décision',
    'Executive Briefing': 'Synthèse Exécutive',
    'Executive Situation Room': 'Centre National de Pilotage',
    'Decision Workspace': 'Espace de Décision',
    'Territorial Digital Twin': 'Jumeau Numérique Territorial',
    'Mode Présentation DG': 'Mode Présentation',
    'Recommandations DG': 'Recommandations de pilotage',
  };

  function harmonize(value) {
    const raw = String(value ?? '').trim();
    if (!raw) return value;
    return EXACT[raw] || raw;
  }

  global.FdsuLabels = { harmonize, EXACT };
})(window);
