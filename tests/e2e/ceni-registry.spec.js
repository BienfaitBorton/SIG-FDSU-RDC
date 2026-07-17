// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Référentiel National CENI v1.0', () => {
  test('dashboard affiche provenance, filtres, carte, tableau et fiche sans confusion FDSU', async ({ page }) => {
    await page.goto('/index.html#ceni-registry');
    await expect(page.locator('#ceni-registry-panel')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('#ceni-provenance')).toContainText('C3762911DF483D0B291145AF31CF612A30332039BB3D7BFD86FA894C650ABE9D', { timeout: 60_000 });
    await expect(page.locator('#ceni-kpis .ceni-kpi')).toHaveCount(6);
    await expect(page.locator('#ceni-kpis .ceni-kpi-icon')).toHaveCount(6);
    await expect(page.locator('#ceni-map')).toBeVisible();
    await expect(page.locator('[data-ceni-map]')).toHaveCount(5);
    await expect(page.locator('#ceni-map-legend')).toContainText('Légende');
    await expect(page.locator('#ceni-visible-count')).not.toHaveText('');
    await expect(page.locator('#ceni-sites-body tr').first()).toBeVisible({ timeout: 60_000 });
    await page.locator('#ceni-sites-body tr').first().click();
    await expect(page.locator('#ceni-detail')).toContainText('Fiche institutionnelle');
    await expect(page.locator('#ceni-detail')).toContainText('CENI');
    await expect(page.locator('#ceni-detail')).toContainText('Provenance et historique');
    await expect(page.locator('#ceni-detail')).toContainText('Classification sémantique française');
    await expect(page.locator('#ceni-detail')).toContainText('Catégorie déduite');
    await expect(page.locator('#ceni-detail')).toContainText('Mot-clé détecté');
    await expect(page.locator('#ceni-detail')).not.toContainText(/Domaine\s*FDSU/i);
  });

  test('interface premium reste lisible, pilotable et bornée', async ({ page }) => {
    await page.goto('/index.html#ceni-registry');
    const panel = page.locator('#ceni-registry-panel');
    await expect(panel).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('#ceni-sites-body tr').first()).toBeVisible({ timeout: 60_000 });
    await expect(panel).toHaveCSS('color', 'rgb(232, 240, 250)');
    await expect(page.locator('#ceni-sites-body tr')).toHaveCount(50);

    await page.locator('#ceni-table-search').fill('CENI');
    await expect(page.locator('#ceni-status')).toContainText('objet');
    await page.locator('#ceni-table-search').fill('');
    await page.locator('#ceni-table th[data-sort="name"]').click();
    await expect(page.locator('#ceni-table th[data-sort="name"]')).toHaveAttribute('data-direction', /^(asc|desc)$/);

    await page.locator('.ceni-columns summary').click();
    await page.locator('#ceni-column-picker input[value="territory"]').uncheck();
    await expect(page.locator('[data-ceni-column="territory"]').first()).toBeHidden();

    await page.locator('[data-ceni-map="fullscreen"]').click();
    await expect(page.locator('#ceni-map-stage')).toHaveClass(/is-fullscreen/);
    await page.locator('[data-ceni-map="fullscreen"]').click();

    await page.locator('#ceni-category').selectOption({ index: 1 });
    await page.locator('#ceni-reset').click();
    await expect(page.locator('#ceni-category')).toHaveValue('');
  });

  test('recherche et filtres rechargent uniquement les données API', async ({ page }) => {
    await page.goto('/index.html#ceni-registry');
    await expect(page.locator('#ceni-sites-body tr').first()).toBeVisible({ timeout: 60_000 });
    await page.locator('#ceni-category').selectOption('UNCLASSIFIED');
    await page.locator('#ceni-apply').click();
    await expect(page.locator('#ceni-sites-body tr').first()).toContainText('Non classifié');
    await page.locator('#ceni-quality').selectOption('outside_country');
    await page.locator('#ceni-apply').click();
    await expect(page.locator('#ceni-sites-body tr').first()).toContainText('Hors du pays');
  });

  test('classification française masque les codes techniques et actualise les statistiques', async ({ page }) => {
    await page.goto('/index.html#ceni-registry');
    await expect(page.locator('#ceni-classification-progress')).toContainText('Non classifiés avant', { timeout: 60_000 });
    await expect(page.locator('#ceni-confidence-bars')).toContainText('Très élevée');
    await expect(page.locator('#ceni-review-count')).toContainText('validation humaine');
    await page.locator('#ceni-search').fill('EP. LOSONDJU');
    await page.locator('#ceni-apply').click();
    await expect(page.locator('#ceni-sites-body')).toContainText('École', { timeout: 60_000 });
    await expect(page.locator('#ceni-registry-panel')).not.toContainText(/\b(?:UNCLASSIFIED|SCHOOL|HEALTH_FACILITY|PUBLIC_BUILDING)\b/);
  });
});
