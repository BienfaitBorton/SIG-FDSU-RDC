// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Zero Decorative Actions — dossier de décision + exports
 */

test.describe('Zero Decorative Actions — Decision Case', () => {
  test('dossier site : pas de boutons décoratifs actifs, rendu propre', async ({ page }) => {
    const pageErrors = [];
    page.on('pageerror', (err) => pageErrors.push(String(err)));

    await page.goto('/index.html#decision-case/site/7?program_code=sites_40');
    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#dxl-actions')).toBeVisible({ timeout: 60_000 });

    // Simulation / mission masqués
    await expect(page.locator('[data-dxl-action="simulate"]')).toHaveCount(0);
    await expect(page.locator('[data-dxl-action="mission"]')).toHaveCount(0);

    // PDF / PPT désactivés avec motif
    const pdf = page.locator('[data-dxl-action="pdf"]');
    const ppt = page.locator('[data-dxl-action="ppt"]');
    await expect(pdf).toBeDisabled();
    await expect(ppt).toBeDisabled();
    await expect(pdf).toHaveAttribute('title', /PDF/i);

    // Excel actif
    await expect(page.locator('[data-dxl-action="export"]')).toBeEnabled();

    // Rendu métier
    const bodyText = await page.locator('#decision-experience-panel').innerText();
    expect(bodyText).not.toMatch(/\[object Object\]/);
    expect(bodyText).not.toMatch(/\bundefined\b/);
    expect(bodyText).not.toMatch(/\bNaN\b/);
    expect(bodyText).not.toMatch(/data\/business\/priority_matrix\.json/);
    expect(bodyText).not.toMatch(/Lacunes\s*:\s*—/);

    // Date utilisateur si présente
    const generated = page.locator('#dxl-section-trace');
    if (await generated.count()) {
      const trace = await generated.innerText();
      expect(trace).not.toMatch(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+\+/);
    }

    expect(pageErrors.filter((e) => !/favicon|net::/i.test(e))).toEqual([]);
  });

  test('export Excel télécharge un .xlsx réel', async ({ page }) => {
    await page.goto('/index.html#decision-case/site/7?program_code=sites_40');
    await expect(page.locator('[data-dxl-action="export"]')).toBeEnabled({ timeout: 60_000 });

    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 60_000 }),
      page.locator('[data-dxl-action="export"]').click(),
    ]);
    const suggested = download.suggestedFilename();
    expect(suggested).toMatch(/\.xlsx$/i);
    expect(suggested).toMatch(/Dossier_decision/i);
    const path = await download.path();
    expect(path).toBeTruthy();
  });

  test('navigation Expliquer / Impact spatial / Retour', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await page.evaluate(() => {
      sessionStorage.setItem('fdsu.decisionCase.returnHash', 'decision-view');
    });
    await page.goto('/index.html#decision-case/site/7?program_code=sites_40');
    await expect(page.locator('#dxl-actions')).toBeVisible({ timeout: 60_000 });

    await page.locator('[data-dxl-action="explain"]').click();
    await expect(page.locator('#dxl-section-why')).toBeVisible();

    await page.locator('[data-dxl-action="spatial"]').click();
    await expect.poll(() => page.url()).toMatch(/spatial-impact\/site\/7/);

    await page.goto('/index.html#decision-case/site/7?program_code=sites_40');
    await expect(page.locator('[data-dxl-action="back"]')).toBeVisible({ timeout: 60_000 });
    await page.locator('[data-dxl-action="back"]').click();
    await expect.poll(() => page.url()).toMatch(/decision-view/);
  });
});
