// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('National FDSU Asset Registry v1', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => { window.__API_BASE_URL__ = 'http://127.0.0.1:8011'; });
  });

  test('API couvre 40, 300, 20 476, CCN et explicabilité', async ({ request }) => {
    const stats = await request.get('http://127.0.0.1:8011/registry/statistics');
    expect(stats.ok()).toBeTruthy();
    const body = await stats.json();
    expect(body.by_program.sites_40).toBe(40);
    expect(body.by_program.sites_300).toBe(300);
    expect(body.by_program.sites_20476).toBe(20476);
    expect(body.by_program.ccn).toBeGreaterThan(0);
    expect(body.population.coverage_national).toBeNull();

    const assets = await request.get('http://127.0.0.1:8011/registry/assets?program=sites_20476&limit=1');
    const asset = (await assets.json()).assets[0];
    for (const suffix of ['relationships', 'population', 'lifecycle', 'explainability']) {
      const response = await request.get(`http://127.0.0.1:8011/registry/assets/${asset.uuid}/${suffix}`);
      expect(response.ok(), suffix).toBeTruthy();
    }
  });

  test('dashboard affiche les actifs réels, leur maturité et leur provenance', async ({ page }) => {
    await page.goto('/index.html#national-asset-registry');
    await expect(page.locator('#national-asset-registry-panel')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('#nfar-kpis .nfar-kpi')).toHaveCount(6, { timeout: 60_000 });
    await expect(page.locator('#nfar-programs')).toContainText('sites_20476');
    await expect(page.locator('#nfar-types')).toContainText(/Éducation|Énergie/);
    await expect(page.locator('#nfar-assets-body tr').first()).toBeVisible();
    await expect(page.locator('#nfar-status')).toContainText(/actif/i);
    const text = await page.locator('#national-asset-registry-panel').innerText();
    expect(text).not.toMatch(/undefined|NaN|\[object Object\]/);
  });

  test('filtre programme recalcule la liste sans valeur inventée', async ({ page }) => {
    await page.goto('/index.html#national-asset-registry');
    await expect(page.locator('#nfar-assets-body tr').first()).toBeVisible({ timeout: 60_000 });
    await page.locator('#nfar-program-filter').selectOption('sites_40');
    await expect(page.locator('#nfar-status')).toContainText('40 actif(s)');
    await expect(page.locator('#nfar-assets-body tr')).toHaveCount(40);
  });
});
