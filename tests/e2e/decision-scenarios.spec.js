// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Decision Scenarios v1.2 — moteur de scénarios métier
 */

test.describe('Decision Scenarios v1.2', () => {
  test('API DecisionScenarios + catalogue UI', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });

    const apiOk = await page.evaluate(async () => {
      const res = await fetch('http://127.0.0.1:8001/api/decision/scenarios');
      if (!res.ok) return false;
      const json = await res.json();
      return Array.isArray(json.scenarios) && json.scenarios.length >= 5;
    });
    expect(apiOk).toBeTruthy();

    await page.locator('[data-decision-tab="simulations"]').click();
    await expect(page.locator('#decision-scenarios-root')).toBeVisible({ timeout: 15_000 });
    await expect(page.locator('#decision-scenarios-catalog .ds-scenario-card')).toHaveCount(5, { timeout: 30_000 });
  });

  test('ouverture scénario A — investir en priorité', async ({ page }) => {
    await page.goto('/index.html#decision-scenario/invest_priority');
    await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('[data-decision-tab-panel="simulations"]')).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('#decision-scenarios-result')).toContainText(/investir|priorit/i, { timeout: 45_000 });
    await expect(page.locator('#decision-scenarios-result')).toContainText(/Résumé exécutif|Indicateurs|Justification|Données utilisées/i);
    await expect(page.locator('#decision-scenarios-kpi-host .edvs-kpi-card, #decision-scenarios-result .edvs-kpi-card').first()).toBeVisible({ timeout: 20_000 });
  });

  test('recommandations et actions cliquables', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await page.locator('[data-decision-tab="simulations"]').click();
    await page.locator('[data-scenario-run="dg_dossier"]').click();
    await expect(page.locator('#decision-scenarios-result')).toContainText(/dossier|DG|décision/i, { timeout: 45_000 });
    await expect(page.locator('#decision-scenarios-result .ds-reco-list, #decision-scenarios-result .ds-actions').first()).toBeVisible();
    const action = page.locator('#decision-scenarios-result [data-ds-hash]').first();
    await expect(action).toBeVisible();
  });

  test('cohérence hash scénario conservée', async ({ page }) => {
    await page.goto('/index.html#decision-scenario/ccn_implantation');
    await expect(page.locator('#decision-scenarios-result')).toContainText(/CCN|Communautaire/i, { timeout: 45_000 });
    expect(page.url()).toMatch(/decision-scenario\/ccn_implantation/);
  });

  test('pas de régression — Centre de Décision + Workspace', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('[data-decision-tab="vue-nationale"]')).toBeVisible();
    const hasWorkspace = await page.evaluate(() => Boolean(window.DecisionWorkspace?.attach && window.DecisionScenarios?.runScenario));
    expect(hasWorkspace).toBeTruthy();
  });
});
