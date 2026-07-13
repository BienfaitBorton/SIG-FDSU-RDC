// @ts-check
const { test, expect } = require('@playwright/test');

const TI_URL = '/index.html#territorial-intelligence/TERRITOIRE-05-002';

test.describe('Territorial Data First — TERRITOIRE-05-002', () => {
  test('API profil : groupements, localités, santé, superficie branchés', async ({ request }) => {
    const res = await request.get('http://127.0.0.1:8001/api/territorial-intelligence/territories/TERRITOIRE-05-002');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const s = body.sections.synthesis;
    expect(Number(s.groupements.value)).toBeGreaterThan(0);
    expect(Number(s.localities.value)).toBeGreaterThan(0);
    expect(Number(s.area_km2.value)).toBeGreaterThan(0);
    expect(Number(body.sections.public_services.etablissements_sante.value)).toBeGreaterThan(0);
    expect(['operational', 'partial', 'confirmed']).toContain(s.groupements.status);
    expect(s.groupements.status).not.toBe('unavailable');
    expect(s.localities.status).not.toBe('unavailable');
  });

  test('UI synthèse : plus de faux indisponible / faux 0 santé', async ({ page }) => {
    await page.goto(TI_URL, { waitUntil: 'networkidle', timeout: 90000 });
    await page.waitForSelector('#ti-sections', { timeout: 60000 });
    await page.waitForTimeout(4000);
    const text = await page.locator('#ti-sections').innerText();
    expect(text).toMatch(/Groupements/i);
    expect(text).toMatch(/Localités/i);
    expect(text).toMatch(/Santé/i);
    expect(text).toMatch(/Superficie/i);
    // Must not show bare unavailable for groupements/localities in synthesis
    const synth = text.split('Situation numérique')[0] || text;
    expect(synth).not.toMatch(/Groupements\s*:\s*—\s*indisponible/i);
    expect(synth).not.toMatch(/Localités\s*:\s*—\s*indisponible/i);
    await page.screenshot({
      path: 'PROJECT_MANAGEMENT/ARCHITECTURE/captures/ti-territoire-05-002-after.png',
      fullPage: true,
    });
  });
});
