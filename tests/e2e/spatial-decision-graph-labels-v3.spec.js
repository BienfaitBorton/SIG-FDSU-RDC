// @ts-check
const { test, expect } = require('@playwright/test');

const URL = '/index.html#spatial-impact/site/30?program_code=sites_40';

test.describe('Spatial Decision Graph v3.1 — labels premium', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => { window.__SDG_API_BASE__ = 'http://127.0.0.1:8011'; });
    await page.goto(URL);
    await expect(page.locator('#sdg-shell[data-sdg-version="3.1.0"]')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('.sdg-marker--site')).toHaveCount(1, { timeout: 60_000 });
    await expect.poll(() => page.evaluate(() => window.SpatialDecisionGraph?.labelMetrics?.eligible || 0), { timeout: 30_000 }).toBeGreaterThan(0);
  });

  test('activation et désactivation restaurent vue riche et vue épurée', async ({ page }) => {
    const toggle = page.locator('#sdg-label-toggle');
    await expect(toggle).toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('.sdg-map-label:not(.is-collision-hidden)').first()).toBeVisible();
    const markersBefore = await page.locator('.sdg-marker').count();
    const edgesBefore = await page.locator('path.sdg-edge').count();
    await toggle.click();
    await expect(toggle).toHaveAttribute('aria-pressed', 'false');
    await expect(toggle).toContainText('Afficher les labels');
    await expect(page.locator('.sdg-map-label')).toHaveCount(0);
    await expect(page.locator('.sdg-marker')).toHaveCount(markersBefore);
    await expect(page.locator('path.sdg-edge')).toHaveCount(edgesBefore);
    await toggle.click();
    await expect(toggle).toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('.sdg-map-label:not(.is-collision-hidden)').first()).toBeVisible();
  });

  test('état masqué persiste après zoom, filtre et changement de site', async ({ page }) => {
    await page.locator('#sdg-label-toggle').click();
    await expect(page.locator('#sdg-label-toggle')).toHaveAttribute('aria-pressed', 'false');
    await page.evaluate(() => window.SpatialDecisionGraph.state.map.zoomIn());
    const filter = page.locator('[data-sdg-filter]:not([disabled])').first();
    if (await filter.count()) await filter.uncheck();
    await expect(page.locator('.sdg-map-label')).toHaveCount(0);
    expect(await page.evaluate(() => window.__SDG_LABELS_VISIBLE__)).toBe(false);
    await page.goto('/index.html#spatial-impact/site/29?program_code=sites_40');
    await expect(page.locator('#sdg-shell[data-sdg-version="3.1.0"]')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('.sdg-marker--site')).toHaveCount(1, { timeout: 60_000 });
    await expect(page.locator('#sdg-label-toggle')).toHaveAttribute('aria-pressed', 'false');
    await expect(page.locator('.sdg-map-label')).toHaveCount(0);
  });

  test('contrôle synchronisé disponible en Mode Présentation sans erreur JavaScript', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await expect(page.locator('#epm-enter-btn')).toBeVisible({ timeout: 30_000 });
    await page.locator('#epm-enter-btn').click();
    const dock = page.locator('#epm-btn-labels');
    await expect(dock).toBeVisible();
    await expect(dock).toHaveAttribute('aria-label', /Masquer les labels permanents/);
    await dock.click();
    await expect(dock).toHaveAttribute('aria-pressed', 'false');
    await expect(page.locator('.sdg-map-label')).toHaveCount(0);
    await page.keyboard.press('l');
    await expect(dock).toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('.sdg-map-label:not(.is-collision-hidden)').first()).toBeVisible();
    expect(errors).toEqual([]);
  });

  test('populations affichées correspondent uniquement aux nœuds documentés', async ({ page }) => {
    const audit = await page.evaluate(() => {
      const graph = window.SpatialDecisionGraph.state.graph;
      return Array.from(document.querySelectorAll('[data-sdg-label-id]')).map((label) => {
        const id = label.getAttribute('data-sdg-label-id');
        const node = graph.nodes.find((item) => item.id === id);
        return { id, hasPopulationText: /hab\./i.test(label.textContent || ''), population: node?.population };
      });
    });
    expect(audit.some((row) => row.hasPopulationText)).toBeTruthy();
    expect(audit.filter((row) => row.hasPopulationText).every((row) => row.population != null)).toBeTruthy();
    expect(audit.filter((row) => row.population == null).every((row) => !row.hasPopulationText)).toBeTruthy();
  });

  test('anti-collision empêche le chevauchement des labels visibles', async ({ page }) => {
    const result = await page.evaluate(() => {
      window.SpatialDecisionGraph.layoutMapLabels();
      const labels = Array.from(document.querySelectorAll('.sdg-map-label:not(.is-collision-hidden)'));
      const boxes = labels.map((label) => label.getBoundingClientRect());
      const overlaps = [];
      for (let i = 0; i < boxes.length; i += 1) {
        for (let j = i + 1; j < boxes.length; j += 1) {
          const a = boxes[i]; const b = boxes[j];
          if (!(a.right + 2 < b.left || a.left > b.right + 2 || a.bottom + 2 < b.top || a.top > b.bottom + 2)) overlaps.push([i, j]);
        }
      }
      return { count: labels.length, overlaps, metrics: window.SpatialDecisionGraph.labelMetrics };
    });
    expect(result.count).toBeGreaterThan(0);
    expect(result.overlaps).toEqual([]);
    expect(result.metrics.hidden).toBeGreaterThanOrEqual(0);
  });

  test('zoom progressif et recalcul restent fluides', async ({ page }) => {
    const result = await page.evaluate(() => {
      const sdg = window.SpatialDecisionGraph;
      const beforeZoom = sdg.state.map.getZoom();
      sdg.state.map.setZoom(Math.min(16, beforeZoom + 2));
      const started = performance.now();
      for (let i = 0; i < 20; i += 1) sdg.layoutMapLabels();
      return { beforeZoom, afterZoom: sdg.state.map.getZoom(), elapsed: performance.now() - started, metrics: sdg.labelMetrics };
    });
    expect(result.afterZoom).toBeGreaterThanOrEqual(result.beforeZoom);
    expect(result.elapsed).toBeLessThan(1000);
    expect(result.metrics.duration_ms).toBeLessThan(100);
  });

  test('responsive mobile conserve contrôles, carte et KPI', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(page.locator('#sdg-label-toggle')).toBeVisible();
    await expect(page.locator('#sdg-map-host')).toBeVisible();
    await expect(page.locator('#sdg-kpis .sdg-kpi')).toHaveCount(7);
    const columns = await page.locator('.sdg-main-grid').evaluate((element) => getComputedStyle(element).gridTemplateColumns.split(' ').length);
    expect(columns).toBe(1);
    await expect(page.locator('#sdg-detail')).toBeVisible();
  });
});
