/**
 * Impact territorial — profil site + progression couverture.
 * Prérequis : API :8001 en mode DB.
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
  'territorial-impact'
);

test.describe('Impact territorial', () => {
  test.setTimeout(180000);
  test.beforeAll(() => fs.mkdirSync(CAPTURE_DIR, { recursive: true }));

  test('API profil site + courbe scénario', async ({ request }) => {
    const site = await request.get(`${API}/api/territorial-impact/sites/1?program_code=sites_40`);
    expect(site.ok()).toBeTruthy();
    const body = await site.json();
    expect(body.localities).toBeTruthy();
    expect(body.deployment_date).toBeNull();
    expect(body.impact).toBeTruthy();

    const scen = await request.get(
      `${API}/api/territorial-impact/scenario?programs=sites_40&limit_per_program=6&include_ccn=true`
    );
    expect(scen.ok()).toBeTruthy();
    const data = await scen.json();
    expect(data.charts.cumulative_curve.length).toBeGreaterThan(1);
    const siteCumul = data.deployments
      .filter((d) => d.asset_type === 'FDSU_SITE')
      .map((d) => d.cumulative_population_covered);
    for (let i = 1; i < siteCumul.length; i += 1) {
      expect(siteCumul[i]).toBeGreaterThanOrEqual(siteCumul[i - 1]);
    }
  });

  test('dossier décision — section impact + localités', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`${BASE}/#decision-case/site/1?program_code=sites_40`, {
      waitUntil: 'domcontentloaded',
    });
    await page.waitForSelector('#dxl-section-territorial-impact', { timeout: 60000 });
    await page.waitForFunction(() => {
      const t = document.querySelector('#dxl-section-territorial-impact')?.textContent || '';
      return /Impact territorial|Localités|Nouvellement|indisponible/i.test(t)
        && !/Chargement de l/i.test(t);
    }, { timeout: 90000 });
    const section = page.locator('#dxl-section-territorial-impact');
    await section.scrollIntoViewIfNeeded();
    await page.screenshot({
      path: path.join(CAPTURE_DIR, '01-site-impact-profile.png'),
      fullPage: true,
    });
    const detail = page.locator('#dxl-section-territorial-impact summary').first();
    if (await detail.count()) {
      await detail.click();
      await page.waitForTimeout(400);
      await page.screenshot({
        path: path.join(CAPTURE_DIR, '02-calcul-detail.png'),
        fullPage: true,
      });
    }
    const loc = page.locator('#dxl-section-territorial-impact .tie-loc-row').first();
    await expect(loc).toBeVisible({ timeout: 15000 });
    await loc.click();
    await page.waitForTimeout(800);
    await page.screenshot({
      path: path.join(CAPTURE_DIR, '03-localite-focus.png'),
      fullPage: true,
    });
    expect(errors.filter((e) => !/favicon|ResizeObserver/i.test(e))).toEqual([]);
  });

  test('salle de pilotage — progression couverture', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`${BASE}/#salle-pilotage`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#salle-pilotage-panel:not(.hidden)', { timeout: 45000 });
    await page.waitForSelector('#esr-coverage-progression', { timeout: 120000 });
    await page.waitForFunction(() => {
      const t = document.querySelector('#esr-coverage-body')?.textContent || '';
      return /Courbe cumulative|Composition|indisponible|Nouveaux bénéficiaires|par programme/i.test(t);
    }, { timeout: 120000 }).catch(() => null);
    await page.screenshot({
      path: path.join(CAPTURE_DIR, '04-pilotage-progression.png'),
      fullPage: true,
    });
    const body = page.locator('#esr-coverage-body');
    await expect(body).toBeVisible();
    const text = await body.innerText();
    expect(text.length).toBeGreaterThan(20);
    expect(errors.filter((e) => !/favicon|ResizeObserver/i.test(e))).toEqual([]);
  });
});
