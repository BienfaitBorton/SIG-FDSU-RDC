// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Territorial Digital Twin Foundation v1.0
 */

async function openCentreDecision(page) {
  await page.goto('/index.html#decision-view');
  await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
}

test.describe('Territorial Digital Twin', () => {
  test('hash territorial-twin ouvre le dossier sans erreur JS', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(String(err)));

    await page.goto('/index.html#territorial-twin/province/Haut-Lomami');
    await expect(page.locator('#decision-detail-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#tdt-root')).toBeVisible({ timeout: 30_000 });
    await expect(page.locator('#tdt-title')).not.toHaveText(/Chargement/i, { timeout: 60_000 });
    await expect(page.locator('#tdt-breadcrumb')).not.toBeEmpty();
    await expect(page.locator('[data-tdt-section="summary"] [data-tdt-body]')).not.toHaveText(/^\s*$/);
    await expect(page.locator('#tdt-map-host')).toBeVisible();

    // Aucun écran vide : sections affichent un état (success/partial/unavailable)
    const sectionCount = await page.locator('.tdt-section[data-tdt-section]').count();
    expect(sectionCount).toBeGreaterThanOrEqual(8);

    await expect(page.locator('[data-tdt-section="energy"]')).toContainText(/insuffisant|non encore|Données/i);
    await expect(page.locator('#tdt-sources-body')).toBeVisible();

    expect(errors).toEqual([]);
  });

  test('ouverture depuis le TST conserve le contexte et permet le retour', async ({ page }) => {
    const errors = [];
    const rejections = [];
    page.on('pageerror', (err) => errors.push(String(err)));
    page.on('console', (msg) => {
      if (msg.type() === 'error' && /unhandledrejection/i.test(msg.text())) rejections.push(msg.text());
    });
    page.on('pageerror', () => {});
    await page.addInitScript(() => {
      window.addEventListener('unhandledrejection', (ev) => {
        window.__tdtUnhandled = window.__tdtUnhandled || [];
        window.__tdtUnhandled.push(String(ev.reason || 'unhandledrejection'));
      });
    });

    await openCentreDecision(page);
    await page.waitForFunction(
      () => document.querySelectorAll('#decision-center-tst-host .leaflet-interactive').length >= 10,
      null,
      { timeout: 60_000 },
    );

    const selected = await page.evaluate(() => {
      const host = document.querySelector('#decision-center-tst-host');
      const api = window.TerritorialSummary?.getInstance?.(host);
      const st = api?.getState?.();
      if (!st?.layer) return null;
      let found = null;
      st.layer.eachLayer((lyr) => {
        const n = lyr.feature?.properties?.name || '';
        if (!found && n) found = lyr;
      });
      if (!found) return null;
      found.fire('click');
      return found.feature?.properties?.name || null;
    });
    expect(selected).toBeTruthy();

    const openBtn = page.locator('#decision-center-tst-host [data-tst-hash*="territorial-twin"]').first();
    await expect(openBtn).toBeVisible({ timeout: 45_000 });
    await openBtn.click();

    await expect(page.locator('#tdt-root')).toBeVisible({ timeout: 30_000 });
    await expect(page.locator('#tdt-breadcrumb')).toContainText(/RDC|Province/i);
    if (selected) {
      await expect(page.locator('#tdt-title')).toContainText(new RegExp(selected.split(/[-\s]/)[0], 'i'), { timeout: 60_000 });
    }

    const leafletCount = await page.locator('#tdt-map-host .leaflet-container').count();
    expect(leafletCount).toBeLessThanOrEqual(1);
    await expect(page.locator('[data-tdt-section="summary"] [data-tdt-body]')).not.toHaveText(/^\s*$/);
    await expect(page.locator('[data-tdt-section="energy"]')).toContainText(/insuffisant|non encore|Données/i);

    await page.locator('#tdt-back-btn').click();
    await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 15_000 });

    const unhandled = await page.evaluate(() => window.__tdtUnhandled || []);
    expect(errors.filter((e) => !/favicon|net::/i.test(e))).toEqual([]);
    expect(unhandled).toEqual([]);
    expect(rejections).toEqual([]);
  });

  test('chargement progressif et priorités/recommandations', async ({ page }) => {
    await page.goto('/index.html#territorial-twin/province/Haut-Lomami');
    await expect(page.locator('#tdt-status')).toBeVisible({ timeout: 30_000 });
    await expect(page.locator('#tdt-status')).toContainText(/sections/i, { timeout: 60_000 });
    await expect(page.locator('[data-tdt-section="decision"]')).toBeVisible();
    await expect(page.locator('[data-tdt-section="quality"]')).toContainText(/Source|NDF|qualité|mesuré|référentiel/i);
    await expect(page.locator('#tdt-kpis .tdt-kpi')).toHaveCount(4, { timeout: 60_000 });
  });
});
