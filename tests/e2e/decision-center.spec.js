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

  test('onglets et vue nationale placeholder', async ({ page }) => {
    await openDecisionCenter(page);

    await expect(page.locator('#decision-center-tabs .decision-center-tab')).toHaveCount(6);
    await expect(page.locator('[data-decision-tab-panel="vue-nationale"]')).toBeVisible();
    await expect(page.locator('#decision-center-kpi-grid .decision-center-kpi-card')).toHaveCount(6);
    await expect(page.locator('#decision-kpi-total-sites')).toHaveText('1 248');
    await expect(page.locator('#decision-center-decision-sheet')).toContainText('Sélectionnez un site sur la carte');
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
    await expect(page.locator('[data-decision-tab-panel="priorisation"]')).toContainText('Espace Priorisation');

    await page.locator('[data-decision-tab="rapports"]').click();
    await expect(page.locator('[data-decision-tab-panel="rapports"]')).toBeVisible();
    await expect(page.locator('[data-decision-tab-panel="rapports"]')).toContainText('Espace Rapports');
  });

  test('module Aide à la décision existant inchangé', async ({ page }) => {
    await page.goto(LEGACY_DECISION_URL);
    await expect(page.locator('#decision-panel')).not.toHaveClass(/hidden/);
    await expect(page.locator('.page-title')).toHaveText('Aide à la décision');
    await expect(page.locator('#decision-run')).toBeVisible();
    await expect(page.locator('#decision-view-panel')).toHaveClass(/hidden/);
  });
});
