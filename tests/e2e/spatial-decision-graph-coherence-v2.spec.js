// @ts-check
const { test, expect } = require('@playwright/test');

const URL = '/index.html#spatial-impact/site/30?program_code=sites_40';

test.describe('Spatial Decision Graph v2.0 — cohérence carte et couches', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => { window.__SDG_API_BASE__ = 'http://127.0.0.1:8011'; });
    await page.goto(URL);
    await expect(page.locator('#sdg-shell')).toBeVisible({ timeout: 60_000 });
    await expect.poll(() => page.evaluate(() => Object.keys(window.SpatialDecisionGraph?.visibleObjectsRegistry || {}).length), {
      timeout: 60_000,
    }).toBeGreaterThan(0);
  });

  test('couche visible = compteur identique au nombre réellement dessiné', async ({ page }) => {
    const result = await page.evaluate(() => window.SpatialDecisionGraph.validateSpatialLayers());
    expect(result.valid).toBeTruthy();
    for (const row of Object.values(result.registry)) {
      const legend = page.locator(`[data-sdg-cat="${row.id}"]`);
      if (row.available === 0) {
        await expect(legend).toHaveCount(0);
      } else if (row.visible > 0) {
        await expect(legend.locator('em')).toHaveText(String(row.visible));
      }
    }
  });

  test('couche masquée = compteur et statistiques recalculés', async ({ page }) => {
    const id = await page.evaluate(() => Object.values(window.SpatialDecisionGraph.visibleObjectsRegistry)
      .find((row) => row.visible > 0)?.id || null);
    test.skip(!id, 'Aucune couche métier visible pour ce site');
    await page.locator(`[data-sdg-filter="${id}"]`).uncheck();
    await expect.poll(() => page.evaluate((layerId) => window.SpatialDecisionGraph.visibleObjectsRegistry[layerId]?.visible, id)).toBe(0);
    await expect(page.locator(`[data-sdg-layer-stat="${id}"]`)).toContainText('0 visible(s)');
    expect((await page.evaluate(() => window.SpatialDecisionGraph.validateSpatialLayers())).valid).toBeTruthy();
  });

  test('besoin prioritaire visible ou absent de la légende sans compteur fantôme', async ({ page }) => {
    const needs = await page.evaluate(() => window.SpatialDecisionGraph.visibleObjectsRegistry.needs || null);
    if (!needs || needs.available === 0) {
      await expect(page.locator('[data-sdg-cat="needs"]')).toHaveCount(0);
      return;
    }
    await expect(page.locator('.sdg-marker--priority-need')).toHaveCount(needs.visible);
    await expect(page.locator('[data-sdg-cat="needs"] em')).toHaveText(String(needs.visible));
  });

  test('route absente toujours expliquée', async ({ page }) => {
    const diagnostic = page.locator('.sdg-availability-diagnostic');
    await expect(diagnostic).toBeVisible();
    await expect(diagnostic).toContainText(/Routes/);
    await expect(diagnostic).toContainText(/référentiel absent|aucune route dans le rayon|route\(s\) analysée\(s\)/i);
    await expect(diagnostic).not.toContainText(/Routes manquantes/i);
  });

  test('aucune incohérence carte/légende', async ({ page }) => {
    const audit = await page.evaluate(() => window.SpatialDecisionGraph.validateSpatialLayers());
    expect(audit.issues).toEqual([]);
    await expect(page.locator('.sdg-consistency-alert')).toHaveCount(0);
  });

  test('validation visuelle des sites 14, 16, 26 et 29', async ({ page }) => {
    for (const siteId of ['14', '16', '26', '29']) {
      await page.goto(`/index.html#spatial-impact/site/${siteId}?program_code=sites_40`);
      await expect(page.locator('#sdg-shell')).toBeVisible({ timeout: 60_000 });
      await expect(page.locator('#sdg-legend')).toBeVisible();
      await expect(page.locator('#sdg-layer-statistics')).toBeVisible();
      expect((await page.evaluate(() => window.SpatialDecisionGraph.validateSpatialLayers())).valid).toBeTruthy();
      await page.screenshot({ path: `test-results/sdg-coherence-site-${siteId}.png`, fullPage: true });
    }
  });
});
