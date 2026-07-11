// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * UX Premium v1.0 — KPI interactifs, légendes, design system
 */

test.describe('UX Premium v1.0', () => {
  test('design system UxPremium chargé', async ({ page }) => {
    await page.goto('/index.html#dashboard');
    await expect(page.locator('.page-title')).toBeVisible({ timeout: 30_000 });
    const ok = await page.evaluate(() => Boolean(window.UxPremium?.mountMapLegend && window.UxPremium?.bindInteractiveKpis));
    expect(ok).toBeTruthy();
  });

  test('Centre de Décision — KPI carte cliquable + strip EDVS interactif', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });

    await page.waitForFunction(
      () => document.querySelectorAll('#decision-edvs-kpi-host .edvs-kpi-card[data-detail-key]').length > 0
        || document.querySelector('.decision-center-kpi-card[data-kpi-key]'),
      null,
      { timeout: 45_000 },
    );

    const edvsCard = page.locator('#decision-edvs-kpi-host .edvs-kpi-card[data-detail-key]').first();
    if (await edvsCard.count()) {
      await expect(edvsCard).toContainText(/Voir l’analyse|Sites/i);
      await edvsCard.click();
      await expect(page.locator('#decision-detail-panel, #decision-experience-panel').first()).toBeVisible({ timeout: 30_000 });
      expect(page.url()).toMatch(/#decision-detail\/|#decision-case\//);
    } else {
      const card = page.locator('.decision-center-kpi-card[data-kpi-key="sites_fdsu"], .decision-center-kpi-card[data-kpi-key]').first();
      await card.click({ position: { x: 24, y: 24 } });
      await expect(page.locator('#decision-detail-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    }
  });

  test('légendes carte injectées sur vues nationales', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#decision-view-panel .tst-legend, #decision-view-panel .ux-map-legend').first()).toBeVisible({ timeout: 30_000 });

    await page.goto('/index.html#dashboard');
    await expect(page.locator('#dashboard-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#dashboard-panel #ux-legend-dashboard-national')).toBeVisible({ timeout: 15_000 });
  });

  test('vocabulaire métier — pas Decision Detail Workspace', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await expect(page.locator('body')).not.toContainText('Decision Detail Workspace');
    await expect(page.locator('body')).not.toContainText('Knowledge Hub');
  });
});
