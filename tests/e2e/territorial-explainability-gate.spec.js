// @ts-check
const { test, expect } = require('@playwright/test');

const TI_URL = '/index.html#territorial-intelligence/TERRITOIRE-05-002';
const API = 'http://127.0.0.1:8001';

test.describe('Sprint Gate — Territorial Explainability v1.1', () => {
  test('API carte : couches santé/télécom/fibre/routes présentes', async ({ request }) => {
    const res = await request.get(`${API}/api/territorial-intelligence/territories/TERRITOIRE-05-002/map`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const counts = body._meta.layer_counts || {};
    expect(body._meta.feature_count).toBeGreaterThan(50);
    expect(counts.health).toBe(121);
    expect((counts.telecom || 0) + (counts.fiber || 0)).toBe(22);
    expect(counts.route).toBe(19);
    expect(counts.fiber).toBeGreaterThanOrEqual(2);
    expect(counts.fiber_line).toBeGreaterThanOrEqual(1);
    expect(counts.groupement).toBe(5);
    expect(counts.locality).toBe(218);
  });

  test('UI : carte peuplée + cartes explicables + drawer sync', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(String(err)));

    await page.goto(TI_URL, { waitUntil: 'networkidle', timeout: 120000 });
    await page.waitForSelector('.ti-explain-card', { timeout: 90000 });
    await page.waitForTimeout(3000);

    const banner = await page.locator('#ti-banner').innerText();
    expect(banner).toMatch(/Carte\s*:\s*[1-9]\d+/);

    // Markers / paths on map
    const circleCount = await page.locator('#ti-map .leaflet-interactive, #ti-map path').count();
    expect(circleCount).toBeGreaterThan(20);

    const text = await page.locator('#ti-sections').innerText();
    expect(text).toMatch(/Télécommunications|Télécom/i);
    expect(text).toMatch(/22/);
    expect(text).toMatch(/Opérateur/i);
    expect(text).toMatch(/Santé/i);
    expect(text).toMatch(/Routes/i);
    expect(text).toMatch(/Fibre/i);
    expect(text).toMatch(/Pourquoi c’est important|Pourquoi c'est important/i);

    const detailsBtn = page.locator('.ti-explain-card[data-domain="telecom"] button', { hasText: /Voir/ }).first();
    await expect(detailsBtn).toBeVisible();
    await detailsBtn.click();
    await expect(page.locator('#ti-detail-drawer')).toBeVisible();
    await page.waitForSelector('#ti-detail-tbody tr.ti-detail-row', { timeout: 30000 });
    expect(await page.locator('#ti-detail-tbody tr.ti-detail-row').count()).toBeGreaterThan(0);

    await page.locator('#ti-detail-tbody tr.ti-detail-row').first().click();
    await page.waitForTimeout(500);
    expect(await page.locator('.leaflet-container').count()).toBeLessThanOrEqual(1);

    await page.screenshot({
      path: 'PROJECT_MANAGEMENT/ARCHITECTURE/captures/ti-gate-explainability-map-drawer.png',
      fullPage: true,
    });

    // Santé drawer + map focus
    await page.locator('#ti-detail-close').click();
    await page.locator('.ti-explain-card[data-domain="health"] button', { hasText: /Voir/ }).first().click();
    await expect(page.locator('#ti-detail-drawer')).toBeVisible();
    await page.waitForSelector('#ti-detail-tbody tr.ti-detail-row', { timeout: 30000 });

    await page.screenshot({
      path: 'PROJECT_MANAGEMENT/ARCHITECTURE/captures/ti-gate-health-drawer.png',
      fullPage: true,
    });

    expect(errors).toEqual([]);
  });
});
