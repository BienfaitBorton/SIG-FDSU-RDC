const { test, expect } = require('@playwright/test');

test.describe('DNAI v2.0', () => {
  test('API normalise les exemples et protège les identifiants', async ({ request }) => {
    const ep = await request.post('http://127.0.0.1:8011/api/dnai/normalize', { data: { text: 'EP1 MFUAMBA', referential: 'CENI' } });
    expect(ep.ok()).toBeTruthy();
    expect((await ep.json()).normalized_text).toBe('ÉCOLE PRIMAIRE 1 MFUAMBA');
    const technical = await request.post('http://127.0.0.1:8011/api/dnai/normalize', { data: { text: 'CENI-EP-001', referential: 'CENI' } });
    expect((await technical.json()).technical_identifier).toBeTruthy();
  });

  test('module Référentiels DNAI affiche statistiques, recherche et validations', async ({ page }) => {
    await page.goto('/index.html#dnai');
    await expect(page.locator('#dnai-panel')).toBeVisible();
    await expect(page.locator('#dnai-kpis .dnai-kpi')).toHaveCount(4);
    await page.locator('#dnai-search').fill('ISP');
    await page.locator('#dnai-search-button').click();
    await expect(page.locator('#dnai-results')).toContainText('INSTITUT SUPÉRIEUR PÉDAGOGIQUE');
    await expect(page.locator('#dnai-pending-list')).toContainText('EDAC');
  });
});
