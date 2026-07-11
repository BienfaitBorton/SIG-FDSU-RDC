// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Tableau de Synthèse Territoriale (TST) v1.0
 */

test.describe('Tableau de Synthèse Territoriale', () => {
  test('API metrics + mount CD — provinces réelles', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(String(err)));

    await page.goto('/index.html#decision-view');
    await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#decision-center-tst-host .tst-metric-select, #decision-center-tst-host .tst-root, #decision-center-tst-host .leaflet-container').first()).toBeVisible({ timeout: 60_000 });

    await page.waitForFunction(
      () => document.querySelectorAll('#decision-center-tst-host .leaflet-interactive').length >= 20,
      null,
      { timeout: 60_000 },
    );

    await expect(page.locator('#decision-center-tst-host .tst-legend, #decision-center-tst-host .ux-map-legend').first()).toBeVisible();
    await expect(page.locator('#decision-center-tst-host .tst-breadcrumb')).toContainText('RDC');

    const dirty = await page.evaluate(() => {
      const text = document.querySelector('#decision-center-tst-host')?.innerText || '';
      return /\bundefined\b|\bnull\b|\bNaN\b/.test(text);
    });
    expect(dirty).toBeFalsy();
    expect(errors.filter((e) => !/favicon|net::/i.test(e))).toEqual([]);
  });

  test('tooltip + clic province + fil d’Ariane', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await expect(page.locator('#decision-center-tst-host .leaflet-interactive').first()).toBeVisible({ timeout: 60_000 });

    const poly = page.locator('#decision-center-tst-host .leaflet-interactive').first();
    await poly.hover({ force: true });
    await expect(page.locator('.leaflet-tooltip.sig-map-tooltip, .leaflet-tooltip').first()).toBeVisible({ timeout: 10_000 });

    await poly.click({ force: true });
    await expect(page.locator('#decision-center-tst-host .tst-breadcrumb')).toContainText(/.+/, { timeout: 20_000 });
    // Retour national
    await page.locator('#decision-center-tst-host [data-tst-crumb="0"]').click();
    await expect(page.locator('#decision-center-tst-host .tst-breadcrumb')).toContainText('RDC');
    await expect(page.locator('#decision-center-tst-host .leaflet-interactive').first()).toBeVisible({ timeout: 30_000 });
  });

  test('changement de métrique — données réelles', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await expect(page.locator('#decision-center-tst-host .tst-metric-select')).toBeVisible({ timeout: 45_000 });
    const select = page.locator('#decision-center-tst-host .tst-metric-select');
    await select.selectOption('sites_fdsu');
    await expect(page.locator('#decision-center-tst-host .tst-status')).toContainText(/provinces|données/i, { timeout: 30_000 });
  });

  test('pas de double instance Leaflet dans le host TST', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await expect(page.locator('#decision-center-tst-host .leaflet-container')).toHaveCount(1, { timeout: 45_000 });
  });

  test('conservation contexte TerritorialContext', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await expect(page.locator('#decision-center-tst-host .leaflet-interactive').first()).toBeVisible({ timeout: 60_000 });
    await page.locator('#decision-center-tst-host .leaflet-interactive').first().click({ force: true });
    await page.waitForTimeout(800);
    const ctx = await page.evaluate(() => window.TerritorialContext?.get?.());
    expect(ctx?.trail?.length).toBeGreaterThanOrEqual(1);
  });

  test('Salle de Pilotage DG — TST permanent', async ({ page }) => {
    await page.goto('/index.html#salle-pilotage');
    await expect(page.locator('#salle-pilotage-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#edvs-tst-host .tst-root, #edvs-tst-host .leaflet-container').first()).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('#edvs-cockpit-map')).toHaveCount(0);
  });
});
