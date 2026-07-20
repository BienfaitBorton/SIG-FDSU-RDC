/**
 * @fileoverview Compteurs SDG : objets métier = nœuds uniques (jamais nœuds + arêtes).
 * Exécution : via Playwright (page SpatialDecisionGraph) ou smoke Python miroir.
 */
// @ts-check
const { test, expect } = require('@playwright/test');

const BAKI = '/index.html#spatial-impact/site/30?program_code=sites_40';

test.describe('SDG — registre objets vs relations (nodes ≠ edges)', () => {
  test.setTimeout(180_000);

  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => { window.__SDG_API_BASE__ = 'http://127.0.0.1:8001'; });
  });

  test('BAKI : 13 localités visibles UI, 13 relations, pop 13829, données complètes', async ({ page }) => {
    await page.goto(BAKI);
    await expect(page.locator('#sdg-shell[data-sdg-version="3.1.0"]')).toBeVisible({ timeout: 60_000 });
    await expect.poll(() => page.evaluate(() => String(window.SpatialDecisionGraph?.state?.graph?._meta?.asset_id || '')), {
      timeout: 90_000,
    }).toBe('30');
    await expect.poll(() => page.evaluate(() => {
      const reg = window.SpatialDecisionGraph?.visibleObjectsRegistry?.localities;
      return reg && typeof reg.visible === 'number' ? reg.visible : -1;
    }), { timeout: 60_000 }).toBeGreaterThan(0);

    const result = await page.evaluate(() => {
      const sdg = window.SpatialDecisionGraph;
      const graph = sdg.state.graph;
      const locNodes = (graph.nodes || []).filter((n) => n.category === 'localities');
      const locEdges = (graph.edges || []).filter((e) => e.category === 'localities');
      const reg = sdg.visibleObjectsRegistry.localities || {};
      const summary = sdg.getPopulationSummary();
      const uniqueIds = new Set(locNodes.map((n) => sdg.businessObjectId(n)));
      return {
        nodeCount: locNodes.length,
        edgeCount: locEdges.length,
        uniqueIds: uniqueIds.size,
        uiVisible: reg.visible,
        uiRelations: reg.visibleRelations,
        forbiddenInflated: (reg.visibleNodeCount || 0) + (reg.visibleEdgeCount || 0),
        summary,
      };
    });

    expect(result.nodeCount).toBe(13);
    expect(result.edgeCount).toBe(13);
    expect(result.uniqueIds).toBe(13);
    expect(result.uiVisible).toBe(13);
    expect(result.uiRelations).toBe(13);
    expect(result.uiVisible).not.toBe(result.forbiddenInflated);
    expect(result.uiVisible).not.toBe(result.nodeCount + result.edgeCount);
    expect(result.summary.visibleLocalities).toBe(13);
    expect(result.summary.analyzedLocalities).toBe(13);
    expect(result.summary.totalPopulation).toBe(13829);
    expect(result.summary.dataStatus).toBe('documented');

    const panel = page.locator('#sdg-filters-panel');
    await expect(panel.locator('[data-sdg-relation-metric="visible-localities"] em')).toHaveText('13');
    await expect(panel.locator('[data-sdg-relation-metric="analyzed-localities"] em')).toHaveText('13');
    await expect(panel.locator('[data-sdg-relation-population]')).toContainText(/Données complètes/i);
    await expect(panel.locator('[data-sdg-relation-metric="analyzed-localities"]')).toContainText(/population renseignée/i);
  });

  test('une relation ne doit jamais augmenter le compteur d’objets de sa catégorie', async ({ page }) => {
    await page.goto(BAKI);
    await expect.poll(() => page.evaluate(() => window.SpatialDecisionGraph?.state?.graph?.nodes?.length || 0), {
      timeout: 90_000,
    }).toBeGreaterThan(0);

    const audit = await page.evaluate(() => {
      const sdg = window.SpatialDecisionGraph;
      const reg = sdg.visibleObjectsRegistry || {};
      return Object.values(reg).map((row) => ({
        id: row.id,
        visible: row.visible,
        visibleRelations: row.visibleRelations,
        visibleNodeCount: row.visibleNodeCount,
        visibleEdgeCount: row.visibleEdgeCount,
        inflated: (row.visibleNodeCount || 0) + (row.visibleEdgeCount || 0),
      }));
    });

    for (const row of audit) {
      if ((row.visibleEdgeCount || 0) > 0 && (row.visibleNodeCount || 0) > 0) {
        expect(row.visible, `${row.id} must not equal nodes+edges`).not.toBe(row.inflated);
        expect(row.visible, `${row.id} object count`).toBeLessThanOrEqual(row.visibleNodeCount);
      }
      // Compteur objets = nœuds uniques (≤ nœuds bruts)
      expect(row.visible).toBeLessThanOrEqual(row.visibleNodeCount || row.visible);
    }
  });

  test('homonymes distincts (même nom, ids différents) ne sont pas fusionnés', async ({ page }) => {
    await page.goto(BAKI);
    await expect.poll(() => page.evaluate(() => !!window.SpatialDecisionGraph?.uniqueBusinessNodes), {
      timeout: 60_000,
    }).toBeTruthy();

    const result = await page.evaluate(() => {
      const sdg = window.SpatialDecisionGraph;
      const nodes = [
        { id: 'n1', need_id: 'A-1', name: 'Kamba', category: 'localities', population: 100, source_label: 'NCI' },
        { id: 'n2', need_id: 'A-2', name: 'Kamba', category: 'localities', population: 200, source_label: 'NCI' },
      ];
      const unique = sdg.uniqueBusinessNodes(nodes);
      const summary = sdg.computePopulationSummary({}, nodes);
      return {
        uniqueCount: unique.length,
        ids: unique.map((n) => n.need_id),
        totalLocalities: summary.totalLocalities,
        documented: summary.documentedLocalities,
        population: summary.totalPopulation,
      };
    });

    expect(result.uniqueCount).toBe(2);
    expect(result.ids.sort()).toEqual(['A-1', 'A-2']);
    expect(result.totalLocalities).toBe(2);
    expect(result.documented).toBe(2);
    expect(result.population).toBe(300);
  });

  test('déduplication canonique : même need_id → un seul objet', async ({ page }) => {
    await page.goto(BAKI);
    await expect.poll(() => page.evaluate(() => !!window.SpatialDecisionGraph?.uniqueBusinessNodes), {
      timeout: 60_000,
    }).toBeTruthy();

    const result = await page.evaluate(() => {
      const sdg = window.SpatialDecisionGraph;
      const nodes = [
        { id: 'n1', need_id: 'SAME', name: 'Alpha', category: 'localities', population: 10, source_label: 'NCI' },
        { id: 'n2', need_id: 'SAME', name: 'Alpha', category: 'localities', population: 10, source_label: 'NCI' },
      ];
      return {
        unique: sdg.uniqueBusinessNodes(nodes).length,
        summary: sdg.computePopulationSummary({}, nodes),
      };
    });

    expect(result.unique).toBe(1);
    expect(result.summary.totalLocalities).toBe(1);
    expect(result.summary.totalPopulation).toBe(10);
  });
});
