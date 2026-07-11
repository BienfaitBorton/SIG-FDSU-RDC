// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Centre de Décision — tooltips carte + tableau analytique lisible
 */

const DECISION_URL = '/index.html#decision-view';

async function openPriorisation(page) {
  await page.goto(DECISION_URL);
  await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
  await page.locator('[data-decision-tab="priorisation"]').click();
  await expect(page.locator('[data-decision-tab-panel="priorisation"]')).toBeVisible();
  await page.waitForFunction(
    () => document.querySelectorAll('#decision-engine-map .leaflet-interactive').length > 0
      || document.querySelector('#decision-engine-table-body tr[data-site-id]'),
    null,
    { timeout: 45_000 },
  );
}

test.describe('Decision Center map & table UX', () => {
  test('légende visible et tableau avec colonnes métier', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));

    await openPriorisation(page);

    await expect(page.locator('#decision-engine-map-legend')).toBeVisible();
    await expect(page.locator('#decision-engine-legend-body')).toContainText(/Critique|Élevée/i);

    const headers = await page.locator('#decision-engine-table thead th').allTextContents();
    expect(headers.map((h) => h.trim())).toEqual([
      'Site',
      'Localisation',
      'Score',
      'Priorité',
      'Facteur principal',
      'Action',
    ]);

    await expect(page.locator('#decision-engine-table-expand-btn')).toBeVisible();
    await expect(page.locator('#decision-engine-table-body tr[data-site-id]').first()).toBeVisible({ timeout: 45_000 });
    await expect(page.locator('.decision-engine-detail-btn').first()).toBeVisible();

    // Pas de débordement horizontal majeur du panneau
    const overflow = await page.evaluate(() => {
      const panel = document.querySelector('#decision-engine-panel');
      if (!panel) return true;
      return panel.scrollWidth > panel.clientWidth + 24;
    });
    expect(overflow).toBeFalsy();

    expect(errors.filter((e) => !/favicon|net::err/i.test(e))).toEqual([]);
  });

  test('tooltip au survol d’un marqueur Priorisation', async ({ page }) => {
    await openPriorisation(page);

    const marker = page.locator('#decision-engine-map .leaflet-interactive').first();
    await expect(marker).toBeVisible({ timeout: 45_000 });
    await marker.hover({ force: true });

    const tooltip = page.locator('.leaflet-tooltip.sig-map-tooltip').first();
    await expect(tooltip).toBeVisible({ timeout: 8_000 });
    const text = await tooltip.innerText();
    expect(text).not.toMatch(/\bundefined\b/i);
    expect(text).not.toMatch(/\bnull\b/i);
    expect(text).not.toMatch(/\bNaN\b/i);
    expect(text.length).toBeGreaterThan(3);
  });

  test('tooltip au survol d’un polygone (vue nationale)', async ({ page }) => {
    await page.goto(DECISION_URL);
    await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await page.locator('[data-decision-tab="vue-nationale"]').click();

    await page.waitForFunction(
      () => document.querySelectorAll('#decision-center-national-map .leaflet-interactive').length > 0,
      null,
      { timeout: 45_000 },
    );

    const poly = page.locator('#decision-center-national-map .leaflet-interactive').first();
    await poly.hover({ force: true });
    const tooltip = page.locator('.leaflet-tooltip.sig-map-tooltip').first();
    await expect(tooltip).toBeVisible({ timeout: 8_000 });
    const text = await tooltip.innerText();
    expect(text).not.toMatch(/\bundefined\b|\bnull\b|\bNaN\b/i);
  });

  test('clic ligne → sélection + Voir le détail ouvre dossier', async ({ page }) => {
    await openPriorisation(page);

    const row = page.locator('#decision-engine-table-body tr[data-site-id]').first();
    await expect(row).toBeVisible({ timeout: 45_000 });
    await row.click();
    await expect(row).toHaveClass(/is-selected/);

    await page.locator('.decision-engine-detail-btn').first().click();
    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    expect(page.url()).toMatch(/#decision-case\//);
    expect(page.url()).not.toMatch(/\/api\//);
  });

  test('agrandir le tableau bascule le layout', async ({ page }) => {
    await openPriorisation(page);
    const body = page.locator('#decision-engine-body');
    await page.locator('#decision-engine-table-expand-btn').click();
    await expect(body).toHaveClass(/is-table-expanded/);
    await expect(page.locator('#decision-engine-table-expand-btn')).toHaveText(/Réduire/);
    await page.locator('#decision-engine-table-expand-btn').click();
    await expect(body).not.toHaveClass(/is-table-expanded/);
  });
});
