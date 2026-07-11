// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Decision Workspace v1.1 — socle partagé
 */

test.describe('Decision Workspace v1.1', () => {
  test('API DecisionWorkspace chargée', async ({ page }) => {
    await page.goto('/index.html#dashboard');
    await expect(page.locator('.page-title')).toBeVisible({ timeout: 30_000 });
    const ok = await page.evaluate(() => Boolean(
      window.DecisionWorkspace?.attach
      && window.DecisionWorkspace?.selectEntity
      && window.DecisionWorkspace?.LEVELS?.length >= 7
      && typeof window.openDecisionWorkspace === 'function',
    ));
    expect(ok).toBeTruthy();
  });

  test('ouverture via KPI — chrome + fil RDC + route decision-detail préservée', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });

    await page.waitForFunction(
      () => document.querySelector('[data-kpi-detail="sites_fdsu"], #decision-edvs-kpi-host .edvs-kpi-card[data-detail-key="sites_fdsu"]'),
      null,
      { timeout: 45_000 },
    );

    const edvs = page.locator('#decision-edvs-kpi-host .edvs-kpi-card[data-detail-key="sites_fdsu"]').first();
    if (await edvs.count()) {
      await edvs.click();
    } else {
      await page.locator('[data-kpi-detail="sites_fdsu"]').first().click();
    }

    await expect(page.locator('#decision-detail-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    expect(page.url()).toMatch(/#decision-detail\//);

    await expect(page.locator('#decision-workspace-chrome')).toBeVisible({ timeout: 15_000 });
    await expect(page.locator('#decision-workspace-trail')).toContainText('RDC');
    await expect(page.locator('#decision-workspace-summary')).toBeVisible();
    await expect(page.locator('#decision-workspace-compare')).toBeVisible();
    await expect(page.locator('#decision-workspace-compare')).toContainText(/Comparaison|socle/i);
  });

  test('alias #decision-workspace conserve le module analyse détaillée', async ({ page }) => {
    await page.goto('/index.html#decision-workspace/sites-total');
    await expect(page.locator('#decision-detail-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#decision-workspace-chrome, #decision-detail-title').first()).toBeVisible({ timeout: 20_000 });
  });

  test('synchronisation sélection ligne → fil + message sync', async ({ page }) => {
    await page.goto('/index.html#decision-detail/sites-total');
    await expect(page.locator('#decision-detail-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#decision-workspace-chrome')).toBeVisible({ timeout: 20_000 });

    await page.waitForFunction(
      () => document.querySelectorAll('#decision-detail-table-body tr [data-open-item]').length > 0
        || document.querySelector('#decision-detail-table-body .ux-state, #decision-detail-table-body .decision-detail-empty'),
      null,
      { timeout: 45_000 },
    );

    const rowBtn = page.locator('#decision-detail-table-body tr [data-open-item]').first();
    if (await rowBtn.count()) {
      // Clic sur la ligne (hors bouton Fiche) pour sélection sans ouvrir DXL
      await page.locator('#decision-detail-table-body tr').first().locator('td').first().click();
      await expect(page.locator('#decision-detail-table-body tr.is-selected, #decision-detail-table-body tr[data-dw-selected="true"]').first()).toBeVisible({ timeout: 10_000 });
      await expect(page.locator('#decision-workspace-sync')).toContainText(/Sélection synchronisée/i);
      await expect(page.locator('#decision-workspace-trail')).toContainText(/Site|RDC/i);
    }

    // Conservation contexte : retour CD puis réouverture
    await page.locator('#decision-detail-back-btn').click();
    await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 15_000 });
    await page.goto('/index.html#decision-detail/sites-total');
    await expect(page.locator('#decision-workspace-trail')).toContainText('RDC');
  });

  test('pas de régression — DXL priorisation intact', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await page.locator('[data-decision-tab="priorisation"]').click();
    await expect(page.locator('[data-decision-tab-panel="priorisation"]')).toBeVisible({ timeout: 15_000 });
    // Module DXL toujours disponible
    const hasDxl = await page.evaluate(() => typeof window.openDecisionCase === 'function');
    expect(hasDxl).toBeTruthy();
  });
});
