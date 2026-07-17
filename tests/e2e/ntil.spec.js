const { test, expect } = require('@playwright/test');

test.describe('NTIL v1.0', () => {
  test('API expose registre, qualité et gouvernance', async ({ request }) => {
    const api = 'http://127.0.0.1:8011/api/ntil';
    const stats = await request.get(`${api}/statistics`);
    expect(stats.ok()).toBeTruthy();
    expect((await stats.json()).total_terms).toBeGreaterThan(0);
    const quality = await request.get(`${api}/quality`);
    expect((await quality.json()).terminology_quality_score).toBeGreaterThan(0);
    const edac = await request.get(`${api}/term/NTR-EDAC`);
    expect((await edac.json()).term.expansion).toBeNull();
  });

  test('dashboard Terminologie Nationale affiche KPI, graphiques et recherche', async ({ page }) => {
    await page.goto('/index.html#ntil');
    await expect(page.locator('#ntil-panel')).toBeVisible();
    await expect(page.locator('#ntil-kpis .ntil-kpi')).toHaveCount(6);
    await expect(page.locator('#ntil-score')).toContainText('/100');
    await expect(page.locator('#ntil-quality-bars .ntil-bar-row')).toHaveCount(1);
    await page.locator('#ntil-search').fill('EDAC');
    await page.locator('#ntil-search-button').click();
    await expect(page.locator('#ntil-registry-body')).toContainText('À valider');
    await expect(page.locator('#ntil-discoveries')).toContainText('ISGEA');
  });
});
