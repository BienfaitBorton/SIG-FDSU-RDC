// @ts-check
const { test, expect } = require('@playwright/test');

const DECISION_CENTER_URL = '/index.html#decision-view';
const LEGACY_DECISION_URL = '/index.html#decision';
const DASHBOARD_URL = '/index.html#dashboard';

async function openDecisionCenter(page) {
  await page.goto(DECISION_CENTER_URL);
  await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/);
  await expect(page.locator('.page-title')).toHaveText('Centre de Décision FDSU');
}

test.describe('SIG-FDSU RDC – Centre de Décision FDSU', () => {
  test('navigation et en-tête du module', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    await page.locator('[data-route="decision-view"]').click();
    await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/);
    await expect(page.locator('.decision-center-header h2')).toHaveText('Centre de Décision FDSU');
    await expect(page.locator('.decision-center-header-copy p').last()).toContainText("Plateforme nationale d'aide à la décision géospatiale");
    await expect(page.locator('.decision-center-action-slot')).toHaveCount(3);
  });

  test('onglets et vue nationale KPI réels', async ({ page }) => {
    await openDecisionCenter(page);

    await expect(page.locator('#decision-center-tabs .decision-center-tab')).toHaveCount(7);
    await expect(page.locator('[data-decision-tab-panel="vue-nationale"]')).toBeVisible();
    await expect(page.locator('#decision-center-kpi-grid .decision-center-kpi-card')).toHaveCount(6);

    // Anciens KPI fictifs absents
    await expect(page.locator('#decision-kpi-total-sites')).toHaveCount(0);
    await expect(page.locator('#decision-center-kpi-grid')).not.toContainText('1 248');
    await expect(page.locator('#decision-center-kpi-grid')).not.toContainText('12,4 M');
    await expect(page.locator('#decision-center-kpi-grid')).not.toContainText('3,8 M');
    await expect(page.locator('#decision-center-kpi-grid')).not.toContainText('28,6 M USD');
    await expect(page.locator('body')).not.toContainText('Nombre total de sites');

    await page.waitForFunction(
      () => {
        const value = document.querySelector('#decision-kpi-sites-fdsu')?.textContent?.trim();
        return Boolean(value && value !== '—' && !value.includes('intégration'));
      },
      null,
      { timeout: 30_000 },
    );

    // Synthèse nationale réelle
    await expect(page.locator('#decision-kpi-sites-fdsu')).toHaveText('340');
    await expect(page.locator('#decision-kpi-sites-priority')).not.toHaveText('—');
    await expect(page.locator('#decision-kpi-sites-critical')).not.toHaveText('—');
    await expect(page.locator('#decision-kpi-sites-high')).not.toHaveText('—');
    await expect(page.locator('#decision-kpi-referentials-active')).not.toHaveText('—');
    await expect(page.locator('#decision-kpi-referentials-planned')).not.toHaveText('—');

    // KPI opérationnels réels
    await expect(page.locator('#decision-kpi-sites-40')).toHaveText('40');
    await expect(page.locator('#decision-kpi-sites-300')).toHaveText('300');
    await expect(page.locator('#decision-kpi-sites-scored')).toHaveText('340');
    await expect(page.locator('#decision-kpi-referentials-in-progress')).toHaveText(/^\d+$/);
    await expect(page.locator('#decision-kpi-telecom-objects')).toHaveText(/14[\s\u00a0\u202f]?580/);
    await expect(page.locator('#decision-kpi-provinces')).toHaveText('26');
    await expect(page.locator('#decision-kpi-territoires')).toHaveText('145');
    await expect(page.locator('#decision-kpi-localites')).toHaveText(/26[\s\u00a0\u202f]?710/);

    // Indicateurs prospectifs non disponibles
    const pendingMessage = /Données en cours d['’]intégration/;
    await expect(page.locator('#decision-kpi-covered-population')).toHaveText(pendingMessage);
    await expect(page.locator('#decision-kpi-uncovered-population')).toHaveText(pendingMessage);
    await expect(page.locator('#decision-kpi-planned-ccn')).toHaveText(pendingMessage);
    await expect(page.locator('#decision-kpi-investment')).toHaveText(pendingMessage);

    await expect(page.locator('#decision-center-decision-sheet')).toContainText('Sélectionnez un site sur la carte');
  });

  test('onglets Priorisation et Référentiels sectoriels restent utilisables', async ({ page }) => {
    await openDecisionCenter(page);

    await page.locator('[data-decision-tab="priorisation"]').click();
    await expect(page.locator('[data-decision-tab-panel="priorisation"]')).toBeVisible();
    await expect(page.locator('[data-decision-tab-panel="priorisation"]')).toContainText('Moteur de décision FDSU');
    await expect(page.locator('#decision-engine-kpi-grid')).toBeVisible();

    await page.locator('[data-decision-tab="referentiels-sectoriels"]').click();
    await expect(page.locator('[data-decision-tab-panel="referentiels-sectoriels"]')).toBeVisible();
    await page.waitForFunction(
      () => document.querySelectorAll('#sectorial-catalog-grid .sectorial-catalog-card').length >= 1
        || (document.querySelector('#sectorial-catalog-grid')?.textContent || '').length > 20,
      null,
      { timeout: 30_000 },
    );
  });

  test('carte nationale réutilisée dans le centre de décision', async ({ page }) => {
    await openDecisionCenter(page);
    await page.waitForFunction(() => typeof window.L !== 'undefined', null, { timeout: 45_000 });
    await expect(page.locator('#decision-center-national-map.leaflet-container')).toBeVisible({ timeout: 30_000 });
    await page.waitForFunction(
      () => (window.decisionCenterState?.layers?.provinces?.getLayers?.().length ?? 0) > 0,
      null,
      { timeout: 60_000 },
    );
  });

  test('changement d’onglet sans logique métier', async ({ page }) => {
    await openDecisionCenter(page);

    await page.locator('[data-decision-tab="priorisation"]').click();
    await expect(page.locator('[data-decision-tab-panel="priorisation"]')).toBeVisible();
    await expect(page.locator('[data-decision-tab-panel="priorisation"]')).toContainText('Moteur de décision FDSU');

    await page.locator('[data-decision-tab="rapports"]').click();
    await expect(page.locator('[data-decision-tab-panel="rapports"]')).toBeVisible();
    await expect(page.locator('[data-decision-tab-panel="rapports"]')).toContainText('Espace Rapports');
  });

  test('architecture métier FDSU et programmes chargés', async ({ page }) => {
    await openDecisionCenter(page);

    const architecture = page.locator('#decision-center-business-architecture');
    await expect(architecture).toBeVisible();
    await expect(architecture.locator('h3')).toHaveText('Architecture métier FDSU');

    await page.waitForFunction(
      () => document.querySelectorAll('#decision-center-program-grid .decision-center-program-card').length >= 10,
      null,
      { timeout: 15_000 },
    );

    await expect(page.locator('#decision-center-program-grid .decision-center-program-card')).toHaveCount(10);
    await expect(page.locator('[data-program-id="sites_300"] .decision-center-program-card-title')).toHaveText('Sites 300');
    await expect(page.locator('[data-program-id="sites_300"] .decision-center-program-card-status')).toHaveText('Planifié');
    await expect(page.locator('[data-program-id="sites_40"] .decision-center-program-card-status')).toHaveText('En exécution');
    await expect(page.locator('[data-program-id="ccn"] .decision-center-program-card-title')).toHaveText('Centres Communautaires Numériques');

    await page.screenshot({ path: 'test-results/decision-center-business-architecture.png', fullPage: false });
  });

  test('programme Sites 40 intégré dans le centre de décision', async ({ page }) => {
    await openDecisionCenter(page);

    const panel = page.locator('#decision-center-sites-40-panel');
    await expect(panel).toBeVisible();
    await expect(panel.locator('h3')).toHaveText('Programme Sites 40');

    await page.waitForFunction(
      () => document.querySelector('#decision-center-sites-40-body .decision-center-sites-40-summary') !== null,
      null,
      { timeout: 15_000 },
    );

    await expect(panel.locator('.decision-center-sites-40-summary .summary-value').first()).toHaveText('40');
    await expect(panel).toContainText('Données KMZ intégrées');
    await expect(panel).toContainText('Répartition par zone FDSU');
    await expect(panel).toContainText('Centre');
    await expect(page.locator('#decision-center-sites-40-map-btn')).toBeVisible();

    await page.screenshot({ path: 'test-results/decision-center-sites-40.png', fullPage: false });
  });

  test('bouton Sites 40 ouvre la cartographie avec la couche activée', async ({ page }) => {
    await openDecisionCenter(page);
    await page.waitForFunction(
      () => document.querySelector('#decision-center-sites-40-body .decision-center-sites-40-summary') !== null,
      null,
      { timeout: 15_000 },
    );

    await page.locator('#decision-center-sites-40-map-btn').click();
    await expect(page.locator('#cartographie-panel')).not.toHaveClass(/hidden/);
    await page.waitForFunction(
      () => (window.cartographyState?.layers?.sites_40?.getLayers?.().length ?? 0) === 40,
      null,
      { timeout: 60_000 },
    );
    await expect(page.locator('input[data-layer="sites_40"]')).toBeChecked();
    await page.screenshot({ path: 'test-results/cartography-sites-40-layer.png', fullPage: false });
  });

  test('programme Sites 300 planifié intégré dans le centre de décision', async ({ page }) => {
    await openDecisionCenter(page);

    const panel = page.locator('#decision-center-sites-300-panel');
    await expect(panel).toBeVisible();
    await expect(panel.locator('h3')).toHaveText('Programme Sites 300');

    await page.waitForFunction(
      () => document.querySelector('#decision-center-sites-300-body .decision-center-sites-40-summary') !== null,
      null,
      { timeout: 15_000 },
    );

    await expect(panel).toContainText('🟡 Planifié');
    await expect(panel).toContainText('300');
    await expect(panel).toContainText('Non démarré');
    await expect(panel).toContainText('À calculer');
    await expect(page.locator('#decision-center-sites-300-map-btn')).toBeVisible();

    await page.screenshot({ path: 'test-results/decision-center-sites-300.png', fullPage: false });
  });

  test('référentiel télécom intégré dans le centre de décision', async ({ page }) => {
    await openDecisionCenter(page);

    const panel = page.locator('#decision-center-telecom-panel');
    await expect(panel).toBeVisible();
    await expect(panel.locator('h3')).toHaveText('Référentiel Télécom');

    await page.waitForFunction(
      () => {
        const body = document.querySelector('#decision-center-telecom-body');
        return body && !body.textContent.includes('Chargement du référentiel télécom');
      },
      null,
      { timeout: 15_000 },
    );

    await expect(panel.locator('#decision-center-telecom-body')).toContainText(/Données télécom disponibles en mode DB|Opérateurs|Sites radio/);
    await page.screenshot({ path: 'test-results/decision-center-telecom.png', fullPage: false });
  });

  test('analyse spatiale intégrée dans le centre de décision', async ({ page }) => {
    await openDecisionCenter(page);

    const panel = page.locator('#decision-center-spatial-panel');
    await expect(panel).toBeVisible();
    await expect(panel.locator('h3')).toHaveText('Analyse spatiale');
    await expect(page.locator('#decision-center-spatial-run-btn')).toHaveText('Analyser les programmes');

    await page.waitForFunction(
      () => {
        const body = document.querySelector('#decision-center-spatial-body');
        return body && !body.textContent.includes("Chargement de l'analyse spatiale");
      },
      null,
      { timeout: 15_000 },
    );

    await expect(panel.locator('#decision-center-spatial-body')).toContainText(/Analyses spatiales disponibles en mode DB|Sites analysés|Relations calculées/);
    await page.screenshot({ path: 'test-results/decision-center-spatial-analysis.png', fullPage: false });
  });

  test('moteur de décision FDSU — priorisation visible', async ({ page }) => {
    await openDecisionCenter(page);

    await page.locator('[data-decision-tab="priorisation"]').click();
    await expect(page.locator('[data-decision-tab-panel="priorisation"]')).toBeVisible();

    const panel = page.locator('#decision-engine-panel');
    await expect(panel).toBeVisible();
    await expect(panel.locator('h3')).toHaveText('Moteur de décision FDSU');
    await expect(page.locator('#decision-engine-recompute-btn')).toHaveText('Recalculer les scores');

    await page.waitForFunction(
      () => {
        const body = document.querySelector('#decision-engine-table-body');
        return body && !body.textContent.includes('Chargement des scores');
      },
      null,
      { timeout: 15_000 },
    );

    await expect(panel.locator('#decision-engine-kpi-grid')).toBeVisible();
    await expect(panel.locator('#decision-engine-kpi-total')).toBeVisible();
    await expect(panel.locator('#decision-engine-kpi-critical')).toBeVisible();
    await expect(panel.locator('#decision-engine-kpi-high')).toBeVisible();
    await expect(panel.locator('#decision-engine-kpi-medium')).toBeVisible();
    await expect(panel.locator('#decision-engine-kpi-low')).toBeVisible();
    await expect(panel.locator('#decision-engine-sectorial-note')).toContainText('Score partiel');
    await expect(panel.locator('#decision-engine-table')).toBeVisible();
    await expect(panel).toContainText(/Moteur de décision disponible en mode DB|Code|Score|Niveau/);

    await page.screenshot({ path: 'test-results/decision-center-decision-engine.png', fullPage: false });
  });

  test('moteur de décision FDSU — filtre par priorité', async ({ page }) => {
    await openDecisionCenter(page);
    await page.locator('[data-decision-tab="priorisation"]').click();

    await page.waitForFunction(
      () => {
        const body = document.querySelector('#decision-engine-table-body');
        return body && !body.textContent.includes('Chargement des scores');
      },
      null,
      { timeout: 15_000 },
    );

    await page.locator('[data-priority-filter="critical"]').click();
    await expect(page.locator('[data-priority-filter="critical"]')).toHaveClass(/is-active/);

    await page.waitForFunction(() => typeof window.L !== 'undefined', null, { timeout: 30_000 });
    await expect(page.locator('#decision-engine-map')).toBeVisible();
    await page.screenshot({ path: 'test-results/decision-center-decision-engine-filter.png', fullPage: false });
  });

  test('référentiels sectoriels — catalogue visible', async ({ page }) => {
    await openDecisionCenter(page);
    await page.locator('[data-decision-tab="referentiels-sectoriels"]').click();
    await expect(page.locator('[data-decision-tab-panel="referentiels-sectoriels"]')).toBeVisible();

    const panel = page.locator('#sectorial-referentials-panel');
    await expect(panel).toBeVisible();
    await expect(panel.locator('h3').first()).toHaveText('Référentiels sectoriels');

    await page.waitForFunction(
      () => {
        const grid = document.querySelector('#sectorial-catalog-grid');
        return grid && !grid.textContent.includes('Chargement du catalogue');
      },
      null,
      { timeout: 45_000 },
    );

    await expect(panel.locator('[data-reference-code="HEALTH"]')).toBeVisible();
    await expect(panel.locator('[data-reference-code="HEALTH"]')).toContainText(/Actif|En cours/);
    await expect(panel.locator('[data-reference-code="EDUCATION"]')).toContainText('Planifié');
    await expect(panel.locator('[data-reference-code="ENERGY"]')).toContainText('Planifié');
    await expect(panel.locator('[data-reference-code="ROADS"]')).toContainText('Planifié');
    await expect(panel.locator('[data-reference-code="POPULATION"]')).toContainText('Planifié');

    await page.screenshot({ path: 'test-results/decision-center-sectorial-catalog.png', fullPage: false });
  });

  test('référentiel Santé — KPI réels après import', async ({ page }) => {
    await openDecisionCenter(page);
    await page.locator('[data-decision-tab="referentiels-sectoriels"]').click();

    await page.waitForFunction(
      () => {
        const total = document.querySelector('#sectorial-health-kpi-total')?.textContent?.trim() || '0';
        return Number(total.replace(/\s|\u00a0|\u202f/g, '')) > 0;
      },
      null,
      { timeout: 45_000 },
    );

    const healthPanel = page.locator('#sectorial-health-panel');
    await expect(healthPanel).toBeVisible();
    await expect(healthPanel.locator('h3')).toHaveText('Santé');

    await expect(page.locator('#sectorial-health-kpi-total')).not.toHaveText('0');
    await expect(page.locator('#sectorial-health-kpi-hospitals')).not.toHaveText('0');
    await expect(page.locator('#sectorial-health-kpi-centers')).not.toHaveText('0');
    await expect(page.locator('#sectorial-health-kpi-posts')).not.toHaveText('0');
    await expect(page.locator('#sectorial-health-kpi-geo')).not.toHaveText('0');
    await expect(page.locator('#sectorial-health-kpi-quality')).not.toHaveText('—');

    await expect(page.locator('#sectorial-health-map-message')).toBeHidden();
    await expect(page.locator('#sectorial-health-table-body')).not.toContainText('Les données santé seront intégrées depuis une source officielle.');
    await expect(page.locator('#sectorial-health-table-body')).not.toContainText('aucune donnée santé');
    await expect(page.locator('#sectorial-health-table-body tr').first()).toBeVisible();
    await expect(page.locator('#sectorial-health-by-type li').first()).toBeVisible();
    await expect(page.locator('#sectorial-health-by-province li').first()).toBeVisible();
    await expect(page.locator('#sectorial-health-quality-list')).toContainText('Score qualité');
    await expect(page.locator('#sectorial-health-map')).toBeVisible();
    await expect(page.locator('#sectorial-health-import-btn')).toBeVisible();

    await page.screenshot({ path: 'test-results/decision-center-health-referential.png', fullPage: false });
  });

  test('module Aide à la décision existant inchangé', async ({ page }) => {
    await page.goto(LEGACY_DECISION_URL);
    await expect(page.locator('#decision-panel')).not.toHaveClass(/hidden/);
    await expect(page.locator('.page-title')).toHaveText('Aide à la décision');
    await expect(page.locator('#decision-run')).toBeVisible();
    await expect(page.locator('#decision-view-panel')).toHaveClass(/hidden/);
  });
});
