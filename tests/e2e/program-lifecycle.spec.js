/**
 * Program Lifecycle — badges séparés, pas de faux « Opérationnel ».
 * Prérequis : API :8001 mode DB.
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
  'program-lifecycle'
);

test.describe('Program Lifecycle Engine', () => {
  test.setTimeout(180000);
  test.beforeAll(() => fs.mkdirSync(CAPTURE_DIR, { recursive: true }));

  test('API programmes — Sites 40 en cours de déploiement', async ({ request }) => {
    const res = await request.get(`${API}/api/program-lifecycle/programs`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const s40 = body.programs.find((p) => p.program_code === 'sites_40');
    const s300 = body.programs.find((p) => p.program_code === 'sites_300');
    const s20476 = body.programs.find((p) => p.program_code === 'sites_20476');
    const ccn = body.programs.find((p) => p.program_code === 'ccn');
    expect(s40.status_code).toBe('deployment_in_progress');
    expect(s300.status_code).toBe('planned');
    expect(s20476.status_code).toBe('strategic_planning');
    expect(ccn.status_code).toBe('preparation');
    expect(s40.operational).toBeNull();
  });

  test('dossier décision — badges data/programme/site/impact séparés', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`${BASE}/#decision-case/site/29?program_code=sites_40`, {
      waitUntil: 'domcontentloaded',
    });
    await page.waitForSelector('#dxl-section-territorial-impact', { timeout: 90000 });
    await page.waitForFunction(() => {
      const t = document.querySelector('#dxl-section-territorial-impact')?.textContent || '';
      return /Impact territorial|bénéficiaires|Statut individuel|Données/i.test(t)
        && !/Chargement de l/i.test(t);
    }, { timeout: 90000 });
    const text = await page.locator('#dxl-section-territorial-impact').innerText();
    expect(text).not.toMatch(/nouvelles localités\s*\(/i);
    // Pas de badge unique « Opérationnel » saturant la section
    const badges = await page.locator('#dxl-section-territorial-impact .tie-badge').allTextContents();
    const joined = badges.join(' | ');
    expect(joined.toLowerCase()).not.toBe('opérationnel');
    await page.screenshot({
      path: path.join(CAPTURE_DIR, '01-decision-case-lifecycle-badges.png'),
      fullPage: true,
    });
    expect(errors.filter((e) => !/favicon|ResizeObserver/i.test(e))).toEqual([]);
  });

  test('salle de pilotage — tableau cycle de vie', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`${BASE}/#salle-pilotage`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#salle-pilotage-panel:not(.hidden)', { timeout: 45000 });
    await page.waitForSelector('#esr-program-lifecycle', { timeout: 120000 });
    await page.waitForFunction(() => {
      const t = document.querySelector('#esr-program-lifecycle-body')?.textContent || '';
      return /Sites 40|En cours de déploiement|À consolider/i.test(t);
    }, { timeout: 90000 });
    const text = await page.locator('#esr-program-lifecycle').innerText();
    expect(text).toMatch(/En cours de déploiement/i);
    expect(text).toMatch(/À consolider/i);
    await page.screenshot({
      path: path.join(CAPTURE_DIR, '02-pilotage-program-lifecycle.png'),
      fullPage: true,
    });
    expect(errors.filter((e) => !/favicon|ResizeObserver/i.test(e))).toEqual([]);
  });
});
