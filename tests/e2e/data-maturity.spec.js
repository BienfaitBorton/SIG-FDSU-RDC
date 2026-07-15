/**
 * National Data Maturity Dashboard — Salle de Pilotage.
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
  'data-maturity'
);

test.describe('National Data Maturity', () => {
  test.setTimeout(180000);
  test.beforeAll(() => fs.mkdirSync(CAPTURE_DIR, { recursive: true }));

  test('API maturité nationale', async ({ request }) => {
    const res = await request.get(`${API}/api/data-maturity`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.national_score).toBeGreaterThanOrEqual(0);
    expect(body.dashboard?.length).toBeGreaterThan(5);
    expect(body.priorities).toBeTruthy();
  });

  test('salle de pilotage — carte maturité données', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`${BASE}/#salle-pilotage`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#salle-pilotage-panel:not(.hidden)', { timeout: 45000 });
    await page.waitForSelector('#esr-data-maturity', { timeout: 120000 });
    await page.waitForFunction(() => {
      const t = document.querySelector('#esr-data-maturity-body')?.textContent || '';
      return /Données prioritaires|Feuille de route|Administration|Sites 40|indisponible/i.test(t)
        && !/Calcul de la maturité nationale/i.test(t);
    }, { timeout: 180000 });
    const text = await page.locator('#esr-data-maturity').innerText();
    expect(text).toMatch(/Maturité/i);
    expect(text).toMatch(/Données prioritaires|Feuille de route|Court terme|indisponible/i);
    await page.screenshot({
      path: path.join(CAPTURE_DIR, '01-pilotage-data-maturity.png'),
      fullPage: true,
    });
    // Ouvrir détail d'une tuile
    const tile = page.locator('#esr-data-maturity [data-ndm-code]').first();
    if (await tile.count()) {
      await tile.click();
      await page.waitForTimeout(400);
      await page.screenshot({
        path: path.join(CAPTURE_DIR, '02-domain-detail.png'),
        fullPage: true,
      });
    }
    expect(errors.filter((e) => !/favicon|ResizeObserver/i.test(e))).toEqual([]);
  });
});
