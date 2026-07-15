/**
 * SDG Coverage Audit — explicabilité + maturité Pilotage.
 */
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const BASE = process.env.SIG_BASE_URL || 'http://127.0.0.1:8000';
const API = process.env.SIG_API_URL || 'http://127.0.0.1:8001';
const CAPTURE_DIR = path.join(
  __dirname,
  '..',
  '..',
  'PROJECT_MANAGEMENT',
  'ARCHITECTURE',
  'captures',
  'sdg-coverage'
);

test.describe('SDG Coverage Audit', () => {
  test.setTimeout(180000);
  test.beforeAll(() => fs.mkdirSync(CAPTURE_DIR, { recursive: true }));

  test('API /api/sdg/coverage', async ({ request }) => {
    const res = await request.get(`${API}/api/sdg/coverage?deep_sample=0`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.matrix?.length).toBeGreaterThan(2);
    expect(body.coverage_rate).toBeGreaterThanOrEqual(0);
  });

  test('dossier site 29 — pas de message générique unique', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`${BASE}/#decision-case/site/29?program_code=sites_40`, {
      waitUntil: 'domcontentloaded',
    });
    await page.waitForSelector('#sdg-shell, #sdg-explainability, #dxl-map', { timeout: 90000 });
    await page.waitForTimeout(4000);
    const bodyText = await page.locator('body').innerText();
    expect(bodyText).not.toMatch(/Analyse d’Impact Territorial indisponible\s*—\s*aucun rendu générique/i);
    await page.screenshot({
      path: path.join(CAPTURE_DIR, '01-decision-case-explainability.png'),
      fullPage: true,
    });
    expect(errors.filter((e) => !/favicon|ResizeObserver/i.test(e))).toEqual([]);
  });

  test('salle de pilotage — maturité analytique', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`${BASE}/#salle-pilotage`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#salle-pilotage-panel:not(.hidden)', { timeout: 45000 });
    await page.waitForSelector('#esr-sdg-maturity', { timeout: 120000 });
    await page.waitForFunction(() => {
      const t = document.querySelector('#esr-sdg-maturity-body')?.textContent || '';
      return /SDG complet|Sites 40|couverture|indisponible/i.test(t);
    }, { timeout: 120000 });
    await page.screenshot({
      path: path.join(CAPTURE_DIR, '02-pilotage-maturite-analytique.png'),
      fullPage: true,
    });
    expect(errors.filter((e) => !/favicon|ResizeObserver/i.test(e))).toEqual([]);
  });
});
