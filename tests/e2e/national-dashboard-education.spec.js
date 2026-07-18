const { test, expect } = require('@playwright/test');

test('la synthèse nationale reste légère et ouvre le Référentiel Éducation à la demande', async ({ page }) => {
  const apiRequests = [];
  page.on('request', (request) => {
    if (request.url().includes('127.0.0.1:8001')) apiRequests.push(request.url());
  });

  await page.goto('/');
  await expect(page.locator('#national-kpi-fdsu')).toHaveText('20 476', { timeout: 30_000 });
  await expect(page.locator('#national-kpi-ceni')).toHaveText('31 956');
  await expect(page.locator('#national-kpi-education')).toHaveText('23 604');
  await expect(page.locator('#national-kpi-health')).toHaveText('37 562');
  await expect(page.locator('#national-kpi-telecom')).toHaveText('14 580');
  await expect(page.locator('#national-kpi-telecom-note')).toContainText('31 401 éléments géospatiaux');
  await expect(page.locator('#national-kpi-admin')).toHaveText('Par niveau');
  await expect(page.locator('#administrative-coverage-body tr')).toHaveCount(7);
  await expect(page.locator('#administrative-coverage-body')).toContainText('Anomalie à auditer');
  await expect(page.locator('#administrative-coverage-body')).toContainText('indicative');
  expect(apiRequests.some((url) => url.includes('/api/education/establishments'))).toBeFalsy();
  expect(apiRequests.some((url) => url.includes('/api/ceni/sites'))).toBeFalsy();

  await page.locator('[data-national-route="education-referential"]').click();
  await expect(page.locator('#education-referential-panel')).toBeVisible();
  await expect(page.locator('#education-kpis')).toContainText('23 604', { timeout: 30_000 });
  await expect(page.locator('#education-table-body tr')).toHaveCount(100, { timeout: 30_000 });
  expect(apiRequests.some((url) => url.includes('/api/education/establishments'))).toBeTruthy();
  await expect(page.locator('body')).not.toContainText('Objets CENI');
});
