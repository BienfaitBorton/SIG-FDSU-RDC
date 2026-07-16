// @ts-check
const { test, expect } = require('@playwright/test');

// Site 18 = Kimba (Sites 40), cas métier de référence de ce correctif.
const URL = '/index.html#spatial-impact/site/18?program_code=sites_40';

test.describe('Spatial Decision Graph v3.1 — compteur métier population', () => {
  test.setTimeout(180_000);

  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => { window.__SDG_API_BASE__ = 'http://127.0.0.1:8011'; });
    await page.goto(URL);
    await expect(page.locator('#sdg-shell[data-sdg-version="3.1.0"]')).toBeVisible({ timeout: 60_000 });
    await expect.poll(() => page.evaluate(() => window.SpatialDecisionGraph?.state?.graph?.nodes?.length || 0), {
      timeout: 60_000,
    }).toBeGreaterThan(0);
  });

  test('somme les populations sourcées des localités visibles', async ({ page }) => {
    const result = await page.evaluate(() => {
      const sdg = window.SpatialDecisionGraph;
      const visible = sdg.state.graph.nodes.filter((node) => node.kind !== 'site' && sdg.state.filters[node.category] !== false);
      const summary = sdg.computePopulationSummary(sdg.state.graph, visible);
      const expected = new Map();
      visible.filter((node) => node.category === 'localities').forEach((node) => {
        const id = node.need_id || node.locality_id || node.locality_code || node.official_code || node.id;
        const value = Number(node.population);
        if (id && Number.isFinite(value) && value > 0 && (node.source_label || node.referential || node.source || node.source_document)) {
          if (!expected.has(String(id))) expected.set(String(id), value);
        }
      });
      return { summary, expected: Array.from(expected.values()).reduce((sum, value) => sum + value, 0) };
    });
    expect(result.summary.totalPopulation).toBe(result.expected || null);
    if (result.expected > 0) {
      await expect(page.locator('[data-sdg-kpi="population"]')).not.toContainText(/^0$/);
      await expect(page.locator('[data-sdg-kpi="population"] .sdg-kpi-value')).toContainText('hab.');
    }
  });

  test('panneau Relations supprime le compteur technique et reprend la synthèse centrale', async ({ page }) => {
    await page.goto('/index.html#spatial-impact/site/30?program_code=sites_40');
    await expect.poll(() => page.evaluate(() => String(window.SpatialDecisionGraph?.state?.graph?._meta?.asset_id || '')), {
      timeout: 60_000,
    }).toBe('30');
    const summary = await page.evaluate(() => window.SpatialDecisionGraph.getPopulationSummary());
    const panel = page.locator('#sdg-filters-panel');
    await expect(panel).not.toContainText(/Population\s*\/\s*localit/i);
    await expect(panel.locator('[data-sdg-relation-metric="population"] em')).toHaveText(
      summary.totalPopulation == null ? 'Non disponible' : `${Math.round(summary.totalPopulation).toLocaleString('fr-FR')} hab.`,
    );
    await expect(panel.locator('[data-sdg-relation-metric="visible-localities"] em')).toHaveText(String(summary.visibleLocalities));
    await expect(panel.locator('[data-sdg-relation-metric="analyzed-localities"] em')).toHaveText(String(summary.analyzedLocalities));
    if (summary.totalPopulation > 0) await expect(panel.locator('[data-sdg-relation-metric="population"] em')).not.toHaveText('0');
    if (summary.visibleLocalities !== summary.analyzedLocalities) {
      expect(summary.visibleLocalities).not.toBe(summary.analyzedLocalities);
    }
  });

  test('masquer les labels ne modifie aucune métrique Population', async ({ page }) => {
    const before = await page.locator('[data-sdg-relation-population]').innerText();
    await page.locator('#sdg-label-toggle').click();
    await expect(page.locator('.sdg-map-label')).toHaveCount(0);
    await expect(page.locator('[data-sdg-relation-population]')).toHaveText(before);
  });

  test('aucune population disponible affiche Non disponible, jamais zéro', async ({ page }) => {
    const summary = await page.evaluate(() => window.SpatialDecisionGraph.computePopulationSummary({}, [
      { id: 'loc-1', category: 'localities', population: null, source_label: 'Référentiel A' },
      { id: 'loc-2', category: 'localities', population: '', source_label: 'Référentiel A' },
      { id: 'loc-3', category: 'localities', population: 'inconnue', source_label: 'Référentiel A' },
    ]));
    expect(summary).toMatchObject({ totalPopulation: null, documentedLocalities: 0, totalLocalities: 3, dataStatus: 'unavailable' });
  });

  test('population partielle expose la couverture démographique', async ({ page }) => {
    const summary = await page.evaluate(() => window.SpatialDecisionGraph.computePopulationSummary({}, [
      { id: 'loc-1', category: 'localities', population: 4348, source_label: 'Référentiel A' },
      { id: 'loc-2', category: 'localities', population: null, source_label: 'Référentiel A' },
    ]));
    expect(summary).toMatchObject({ totalPopulation: 4348, documentedLocalities: 1, totalLocalities: 2, missingPopulationCount: 1, dataStatus: 'partial', confidence: 0.5 });
  });

  test('déduplique une même localité par identifiant stable', async ({ page }) => {
    const summary = await page.evaluate(() => window.SpatialDecisionGraph.computePopulationSummary({}, [
      { id: 'node-a', need_id: 'LOC-1', category: 'localities', population: 1951, source_label: 'Référentiel A' },
      { id: 'node-b', need_id: 'LOC-1', category: 'localities', population: 1951, source_label: 'Référentiel A' },
      { id: 'node-c', need_id: 'LOC-2', category: 'localities', population: 747, source_label: 'Référentiel A' },
    ]));
    expect(summary).toMatchObject({ totalPopulation: 2698, documentedLocalities: 2, totalLocalities: 2, dataStatus: 'documented' });
  });

  test('ignore les valeurs non positives et non sourcées', async ({ page }) => {
    const summary = await page.evaluate(() => window.SpatialDecisionGraph.computePopulationSummary({}, [
      { id: 'loc-1', category: 'localities', population: 0, source_label: 'Référentiel A' },
      { id: 'loc-2', category: 'localities', population: -10, source_label: 'Référentiel A' },
      { id: 'loc-3', category: 'localities', population: 900 },
      { id: 'loc-4', category: 'localities', population: 747, source_label: 'Référentiel A' },
    ]));
    expect(summary).toMatchObject({ totalPopulation: 747, documentedLocalities: 1, totalLocalities: 4, dataStatus: 'partial' });
  });

  test('isoler la couche localités recalcule Population et Localités', async ({ page }) => {
    const filter = page.locator('[data-sdg-filter="localities"]');
    test.skip(await filter.count() === 0 || await filter.isDisabled(), 'Couche localités absente pour ce site');
    await filter.uncheck();
    await expect(page.locator('[data-sdg-kpi="population"] .sdg-kpi-value')).toHaveText('Non disponible');
    await expect(page.locator('[data-sdg-kpi="localities"] .sdg-kpi-value')).toHaveText('0');
    await expect(page.locator('[data-sdg-population-summary]').first()).toContainText('Référentiel démographique non disponible pour ce périmètre.');
  });

  test('vue normale et Mode Présentation conservent la même valeur', async ({ page }) => {
    const before = await page.locator('[data-sdg-kpi="population"] .sdg-kpi-value').innerText();
    await expect(page.locator('#epm-enter-btn')).toBeVisible({ timeout: 30_000 });
    await page.locator('#epm-enter-btn').click();
    await expect(page.locator('body')).toHaveClass(/executive-presentation-mode/);
    await expect(page.locator('[data-sdg-kpi="population"] .sdg-kpi-value')).toHaveText(before);
    await expect(page.locator('[data-sdg-population-summary]').first()).toContainText(before);
  });

  test('zéro est interdit dès qu’une population valide existe', async ({ page }) => {
    const summary = await page.evaluate(() => window.SpatialDecisionGraph.computePopulationSummary({}, [
      { id: 'loc-1', category: 'localities', population: 4348, source_label: 'Référentiel A' },
      { id: 'loc-2', category: 'localities', population: null, source_label: 'Référentiel A' },
    ]));
    expect(summary.totalPopulation).toBe(4348);
    expect(summary.totalPopulation).not.toBe(0);
  });

  test('validation visuelle BAKI, Kimba, Bena-Mulumba et site 29', async ({ page }) => {
    test.setTimeout(360_000);
    const sites = [
      ['30', 'baki'],
      ['18', 'kimba'],
      ['16', 'bena-mulumba'],
      ['29', 'site-29'],
    ];
    for (const [siteId, slug] of sites) {
      await page.goto(`/index.html#spatial-impact/site/${siteId}?program_code=sites_40`);
      await expect.poll(() => page.evaluate(() => String(window.SpatialDecisionGraph?.state?.graph?._meta?.asset_id || '')), {
        timeout: 60_000,
      }).toBe(siteId);
      const population = page.locator('[data-sdg-relation-metric="population"] em');
      await expect(population).not.toHaveText('0');
      await expect(page.locator('#sdg-filters-panel')).not.toContainText(/Population\s*\/\s*localit/i);
      await page.screenshot({ path: `test-results/sdg-population-${slug}-normal.png`, fullPage: true });

      await page.locator('#sdg-label-toggle').click();
      await expect(page.locator('.sdg-map-label')).toHaveCount(0);
      await page.screenshot({ path: `test-results/sdg-population-${slug}-labels-hidden.png`, fullPage: true });
      await page.locator('#sdg-label-toggle').click();

      await page.locator('#epm-enter-btn').click();
      await expect(page.locator('body')).toHaveClass(/executive-presentation-mode/);
      await expect(page.locator('[data-sdg-relation-metric="population"] em')).toHaveText(await population.innerText());
      await page.screenshot({ path: `test-results/sdg-population-${slug}-presentation.png`, fullPage: true });
      await page.locator('#epm-btn-exit').click();
      await expect(page.locator('body')).not.toHaveClass(/executive-presentation-mode/);
    }
  });
});
