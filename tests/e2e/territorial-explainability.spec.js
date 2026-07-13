// @ts-check
const { test, expect } = require('@playwright/test');

const TI_URL = '/index.html#territorial-intelligence/TERRITOIRE-05-002';
const API = 'http://127.0.0.1:8001';

test.describe('Territorial Explainability — TERRITOIRE-05-002', () => {
  test('API explainability : télécom 22, opérateurs, santé, routes, fibre', async ({ request }) => {
    const res = await request.get(`${API}/api/territorial-intelligence/territories/TERRITOIRE-05-002/explainability`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.telecom.summary.count).toBe(22);
    expect((body.telecom.operators || []).length).toBeGreaterThan(0);
    expect((body.telecom.breakdown || []).length).toBeGreaterThan(0);
    expect(body.health.summary.count).toBe(121);
    expect(body.routes.summary.count).toBe(19);
    expect(body.fiber.summary.count).toBeGreaterThanOrEqual(0);
    expect(body.sites_20476.summary.count).toBe(88);
  });

  test('UI cartes explicables + drawer détail télécom', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(String(err)));

    await page.goto(TI_URL, { waitUntil: 'networkidle', timeout: 90000 });
    await page.waitForSelector('.ti-explain-card', { timeout: 60000 });
    await page.waitForTimeout(2500);

    const sections = page.locator('#ti-sections');
    const text = await sections.innerText();
    expect(text).toMatch(/Télécom/i);
    expect(text).toMatch(/22/);
    expect(text).toMatch(/Opérateur/i);
    expect(text).toMatch(/Santé/i);
    expect(text).toMatch(/Routes/i);
    expect(text).toMatch(/Fibre/i);
    // Pas de codes internes métier dans les cartes décideur / synthèse prioritaire
    const explainText = await page.locator('.ti-explain-grid').innerText();
    expect(explainText).not.toMatch(/\bunmatched_needs\b/);
    expect(explainText).not.toMatch(/\bhigh\b/);
    expect(explainText).not.toMatch(/\bmedium\b/);
    expect(explainText).not.toMatch(/\btrue\b/);
    expect(explainText).not.toMatch(/\bfalse\b/);
    expect(text).not.toMatch(/\bunmatched_needs\b/);
    expect(text).not.toMatch(/Aérodromes \(signal\)\s*:\s*true/i);
    expect(text).not.toMatch(/Niveau\s*:\s*high\b/i);

    const detailsBtn = page.locator('.ti-explain-card[data-domain="telecom"] button', {
      hasText: /Voir les/,
    }).first();
    await expect(detailsBtn).toBeVisible();
    await detailsBtn.click();
    await expect(page.locator('#ti-detail-drawer')).toBeVisible();
    await page.waitForSelector('#ti-detail-tbody tr', { timeout: 30000 });
    const rows = page.locator('#ti-detail-tbody tr.ti-detail-row');
    await expect(rows.first()).toBeVisible();
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);

    await rows.first().click();
    await page.waitForTimeout(800);
    const leafletCount = await page.locator('.leaflet-container').count();
    expect(leafletCount).toBeLessThanOrEqual(1);

    await page.screenshot({
      path: 'PROJECT_MANAGEMENT/ARCHITECTURE/captures/ti-explainability-telecom-drawer.png',
      fullPage: true,
    });

    expect(errors).toEqual([]);
  });
});
