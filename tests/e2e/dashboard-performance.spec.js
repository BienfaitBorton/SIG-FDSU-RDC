const { test, expect } = require('@playwright/test');

test('le chargement initial diffère les couches cartographiques secondaires', async ({ page }) => {
  const apiRequests = [];
  page.on('request', (request) => {
    if (request.url().includes('127.0.0.1:8001')) apiRequests.push(request.url());
  });

  await page.goto('/');
  await page.waitForFunction(() => window.platformState && window.cartographyState, null, { timeout: 30_000 });
  await page.waitForTimeout(3_000);

  expect(apiRequests.some((url) => url.includes('/map/layers/provinces'))).toBeTruthy();
  for (const layer of ['territoires', 'collectivites', 'groupements', 'localites', 'sites', 'missions']) {
    expect(apiRequests.some((url) => url.includes(`/map/layers/${layer}`))).toBeFalsy();
  }
  expect(apiRequests.some((url) => url.includes('/api/ceni/sites'))).toBeFalsy();
  expect(apiRequests.some((url) => url.includes('/api/education/establishments'))).toBeFalsy();
  expect(apiRequests.some((url) => url.includes('/api/decision/'))).toBeFalsy();
});
