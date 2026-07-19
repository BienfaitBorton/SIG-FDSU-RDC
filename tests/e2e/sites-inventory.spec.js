/**
 * E2E Inventaire Sites FDSU (#sites)
 * Prérequis : plateforme démarrée (ex. .\start_sig.ps1 -Mode db)
 */
const { test, expect } = require('@playwright/test');

const BASE = process.env.SIG_BASE_URL || 'http://127.0.0.1:8000';

test.describe('Inventaire Sites FDSU', () => {
  test('#sites n’affiche plus le placeholder et charge des données', async ({ page }) => {
    await page.goto(`${BASE}/#sites`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await expect(page.locator('#sites-panel')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('#sites-panel')).not.toContainText('Module Sites FDSU à construire en v0.7.0');
    await expect(page.locator('#sites-inventory-tbody')).toBeVisible({ timeout: 60000 });
    await expect(page.locator('#sites-inventory-tbody tr[data-site-id]').first()).toBeVisible({ timeout: 90000 });
    const badge = page.locator('#sites-panel .panel-badge');
    await expect(badge).not.toHaveText('0 site');
    await expect(page.locator('#sites-inventory-programs')).toContainText('Sites 40');
    await expect(page.locator('#sites-inventory-programs')).toContainText('Sites 300');
    await expect(page.locator('#sites-inventory-programs')).toContainText('20 476');
  });

  test('recherche et fiche site', async ({ page }) => {
    await page.goto(`${BASE}/#sites`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await expect(page.locator('#sites-inventory-tbody tr[data-site-id]').first()).toBeVisible({ timeout: 90000 });
    await page.fill('#sites-filter-q', 'Yengembana');
    await page.selectOption('#sites-filter-program', 'sites_40');
    await page.click('#sites-filter-apply');
    await expect(page.locator('#sites-inventory-tbody tr[data-site-id]').first()).toBeVisible({ timeout: 60000 });
    await page.locator('#sites-inventory-tbody .sites-inv-detail-btn').first().click();
    await expect(page.locator('#sites-inventory-detail h3')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('#sites-inv-open-map')).toBeVisible();
  });

  test('état API cassée ne casse pas le panneau', async ({ page }) => {
    await page.route('**/api/decision/sites/inventory**', (route) => route.abort());
    await page.goto(`${BASE}/#sites`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await expect(page.locator('#sites-panel')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('#sites-inventory-status')).toContainText(/indisponible|Inventaire/i, { timeout: 30000 });
    await expect(page.locator('#sites-panel')).not.toContainText('[object Object]');
  });
});
