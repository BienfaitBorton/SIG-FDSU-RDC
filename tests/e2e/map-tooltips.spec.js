// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Infobulles cartographiques + Decision Experience Layer
 * — aucun utilisateur métier ne doit atterrir sur /api/...
 */

const MAP_URL = '/index.html#map';
const DXL_SAMPLE = '/index.html#decision-case/site/30?program_code=sites_40';

test.describe('Map tooltips & DXL', () => {
  test('factory SigMapTooltips est chargée', async ({ page }) => {
    await page.goto(MAP_URL);
    await expect(page.locator('#map-panel, #cartography-panel, [data-module="map"]').first()).toBeVisible({ timeout: 30_000 });
    const hasFactory = await page.evaluate(() => Boolean(window.SigMapTooltips?.bind && window.SigMapTooltips?.buildHtml));
    expect(hasFactory).toBeTruthy();
  });

  test('dossier de décision s’ouvre sans navigation /api/', async ({ page }) => {
    const apiNavigations = [];
    page.on('framenavigated', (frame) => {
      if (frame === page.mainFrame()) {
        const url = frame.url();
        if (url.includes('/api/')) apiNavigations.push(url);
      }
    });

    await page.goto(DXL_SAMPLE);
    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#dxl-title')).toContainText(/Dossier de décision/i);
    await expect(page.locator('#dxl-section-summary')).toBeVisible();
    await expect(page.locator('#dxl-map')).toBeVisible();
    await expect(page.locator('#dxl-actions')).toBeVisible();

    // Retour métier
    await page.locator('#dxl-back-btn').click();
    await page.waitForTimeout(400);
    expect(apiNavigations).toEqual([]);
    expect(page.url()).not.toMatch(/\/api\//);
  });

  test('hash spatial-impact reste dans le dashboard', async ({ page }) => {
    await page.goto('/index.html#spatial-impact/site/demo');
    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    expect(page.url()).toContain('#spatial-impact/');
    expect(page.url()).not.toMatch(/:8001\/api\//);
  });

  test('aucun lien visible vers /api/decision/case dans le Centre de Décision', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    const badHrefs = await page.locator('a[href*="/api/decision"], a[href*="/api/spatial-matching"]').count();
    expect(badHrefs).toBe(0);
  });
});
