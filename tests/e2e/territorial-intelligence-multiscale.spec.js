/**
 * Territorial Intelligence multi-échelle — légende cohérente + drill-down.
 * Prérequis : .\start_sig.ps1 -Mode db (API :8001, dashboard :8000)
 */
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const BASE = process.env.SIG_BASE_URL || 'http://127.0.0.1:8000';
const API = process.env.SIG_API_URL || 'http://127.0.0.1:8001';
const DUNGU = 'TERRITOIRE-05-002';
const CAPTURE_DIR = path.join(
  __dirname,
  '..',
  '..',
  'PROJECT_MANAGEMENT',
  'ARCHITECTURE',
  'captures',
  'territorial-intelligence-multiscale'
);

function ensureDir() {
  fs.mkdirSync(CAPTURE_DIR, { recursive: true });
}

test.describe('TI multi-échelle', () => {
  test.setTimeout(300000);
  test.beforeAll(() => ensureDir());

  test('API légende : telecom / fibre / routes distincts et colorés', async ({ request }) => {
    const map = await request.get(`${API}/api/territorial-intelligence/territories/${DUNGU}/map`);
    expect(map.ok()).toBeTruthy();
    const body = await map.json();
    const legend = body.legend || [];
    const labels = legend.map((i) => i.label).join(' | ');
    expect(labels).not.toContain('Télécom / Fibre / Routes');
    const byKind = Object.fromEntries(legend.map((i) => [i.kind, i]));
    if (byKind.telecom && byKind.fiber) {
      expect(byKind.telecom.color).not.toBe(byKind.fiber.color);
    }
    if (byKind.telecom && byKind.route) {
      expect(byKind.telecom.color).not.toBe(byKind.route.color);
    }
    for (const item of legend) {
      expect(item.count).toBeGreaterThan(0);
      expect(item.color).toBeTruthy();
    }
  });

  test('ouverte Dungu + drill-down + fil d’Ariane + légende UI', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(String(err)));

    await page.goto(`${BASE}/#territorial-intelligence/${DUNGU}`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#territorial-intelligence-panel:not(.hidden)', { timeout: 30000 });
    await page.waitForFunction(() => {
      const t = document.querySelector('#ti-territory-title')?.textContent || '';
      return /Dungu|DUNGU/i.test(t);
    }, { timeout: 45000 });

    await page.screenshot({ path: path.join(CAPTURE_DIR, '01-territoire-dungu.png'), fullPage: true });

    const legend = page.locator('#ux-legend-ti');
    await expect(legend).toBeVisible({ timeout: 15000 });
    const legendText = await legend.innerText();
    expect(legendText).not.toContain('Télécom / Fibre / Routes');
    expect(legendText.toLowerCase()).toMatch(/télécom|telecom|santé|sante|route/i);

    await page.screenshot({ path: path.join(CAPTURE_DIR, '02-legende-corrigee.png'), fullPage: true });

    // Préférer Wando (chefferie avec groupements) si présente
    const wando = page.locator('#ti-children-list button', { hasText: /Wando/i }).first();
    const childBtn = (await wando.count()) ? wando : page.locator('#ti-children-list button').first();
    const childCount = await page.locator('#ti-children-list button').count();
    if (childCount > 0) {
      const childLabel = await childBtn.innerText();
      await childBtn.click();
      await page.waitForFunction(() => {
        const t = document.querySelector('#ti-territory-title')?.textContent || '';
        return /Chefferie|Collectivité|Wando|Malingindu|Ndolomo/i.test(t);
      }, { timeout: 60000 });

      await page.screenshot({ path: path.join(CAPTURE_DIR, '03-collectivite.png'), fullPage: true });

      const crumb = page.locator('#ti-breadcrumb');
      await expect(crumb).toContainText(/RDC|Haut/i);
      await expect(crumb).toContainText(/Dungu|DUNGU/i);

      const grp = page.locator('#ti-children-list button').first();
      if (await grp.count()) {
        await grp.click();
        await page.waitForTimeout(4000);
        await page.screenshot({ path: path.join(CAPTURE_DIR, '04-groupement.png'), fullPage: true });

        const loc = page.locator('#ti-children-list button').first();
        if (await loc.count()) {
          await loc.click();
          await page.waitForTimeout(4000);
          if (!page.isClosed()) {
            await page.screenshot({ path: path.join(CAPTURE_DIR, '05-localite.png'), fullPage: true });
          }
        }
      }

      // Retour territoire via fil d’Ariane
      const dunguCrumb = page.locator('#ti-breadcrumb a[data-ti-entity*="TERRITOIRE"], #ti-breadcrumb a[href*="TERRITOIRE"]').first();
      if (await dunguCrumb.count()) {
        await dunguCrumb.click();
        await page.waitForTimeout(2500);
      }

      expect(childLabel).toBeTruthy();
    }

    const covSection = page.locator('#ti-sections');
    await expect(covSection).toContainText(/Population couverte|Couverture/i);

    // Pas de double Leaflet container orphelin
    const leafletCount = await page.locator('#ti-map.leaflet-container').count();
    expect(leafletCount).toBeLessThanOrEqual(1);
    expect(errors.filter((e) => !/ResizeObserver|favicon/i.test(e))).toEqual([]);

    await page.screenshot({ path: path.join(CAPTURE_DIR, '06-breadcrumb-coverage.png'), fullPage: true });
  });
});
