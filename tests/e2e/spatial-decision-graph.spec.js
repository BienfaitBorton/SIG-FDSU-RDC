// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Spatial Decision Graph v2.0 — Analyse d’Impact Territorial
 * Animation, légende, filtres, survol, explication, TDT, Workspace,
 * aucune erreur JS, une seule instance Leaflet.
 */

const SDG_URL = '/index.html#spatial-impact/site/7?program_code=sites_40';
const API = 'http://127.0.0.1:8001';

function attachDiag(page) {
  /** @type {string[]} */
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error' && /Leaflet.*already initialized|Map container is being reused/i.test(message.text())) {
      pageErrors.push(message.text());
    }
  });
  return { pageErrors };
}

test.describe('Spatial Decision Graph v2.0', () => {
  test('API graphe et présentation disponibles', async ({ request }) => {
    const meta = await request.get(`${API}/api/spatial-decision-graph/meta/categories`);
    expect(meta.ok()).toBeTruthy();
    const metaBody = await meta.json();
    expect(metaBody.ui_title).toMatch(/Analyse d’Impact Territorial|Analyse d'Impact Territorial/);
    expect(Array.isArray(metaBody.categories)).toBeTruthy();

    const graph = await request.get(`${API}/api/spatial-decision-graph/site/7?program_code=sites_40`);
    expect(graph.ok()).toBeTruthy();
    const body = await graph.json();
    expect(body._meta?.principle).toMatch(/NSME/);
    expect(body.center?.kind).toBe('site');
    expect(Array.isArray(body.edges)).toBeTruthy();
    expect(body.why_panel?.blocks?.length).toBeGreaterThan(0);
    // Aucune arête sans trace NSME
    for (const edge of body.edges || []) {
      expect(edge.nsme_trace?.relation_type).toBeTruthy();
    }

    const presentation = await request.get(`${API}/api/spatial-decision-graph/site/7/presentation?program_code=sites_40`);
    expect(presentation.ok()).toBeTruthy();
    const steps = (await presentation.json()).steps || [];
    expect(steps.length).toBeGreaterThanOrEqual(5);
  });

  test('vue Analyse d’Impact Territorial : shell, légende, filtres, panneau', async ({ page }) => {
    const diag = attachDiag(page);
    await page.goto(SDG_URL);

    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#dxl-title')).toContainText(/Analyse d’Impact Territorial|Analyse d'Impact Territorial/, {
      timeout: 45_000,
    });

    await expect(page.locator('#sdg-shell')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('#sdg-why-body')).toBeVisible();
    await expect(page.locator('#sdg-legend')).toBeVisible();
    await expect(page.locator('#sdg-filters')).toBeVisible();
    await expect(page.locator('#sdg-present-btn')).toBeVisible();

    // Une seule carte Leaflet sur #dxl-map
    const leafletCount = await page.evaluate(() => document.querySelectorAll('#dxl-map.leaflet-container').length);
    expect(leafletCount).toBeLessThanOrEqual(1);

    // Filtre : décocher une catégorie ne recrée pas Leaflet
    const filter = page.locator('#sdg-filters input[data-sdg-filter]').first();
    if (await filter.count()) {
      await filter.uncheck();
      const after = await page.evaluate(() => document.querySelectorAll('#dxl-map.leaflet-container').length);
      expect(after).toBe(leafletCount);
    }

    // Légende cliquable
    const legendBtn = page.locator('#sdg-legend [data-sdg-cat]').first();
    if (await legendBtn.count()) {
      await legendBtn.click();
      await expect(legendBtn).toHaveClass(/is-off|sdg-legend-btn/);
    }

    expect(diag.pageErrors.filter((e) => !/favicon|net::ERR/i.test(e))).toEqual([]);
  });

  test('animation présentation + interruption', async ({ page }) => {
    const diag = attachDiag(page);
    await page.goto(SDG_URL);
    await expect(page.locator('#sdg-present-btn')).toBeVisible({ timeout: 60_000 });

    await page.locator('#sdg-present-btn').click();
    await expect(page.locator('#sdg-stop-btn')).toBeVisible({ timeout: 5_000 });
    await expect(page.locator('#sdg-step-label')).not.toHaveText('', { timeout: 5_000 });

    await page.locator('#sdg-stop-btn').click();
    await expect(page.locator('#sdg-stop-btn')).toBeHidden({ timeout: 5_000 });
    await expect(page.locator('#sdg-step-label')).toContainText(/Raisonnement|Site|Population|Recommandation/i);

    expect(diag.pageErrors.filter((e) => !/favicon|net::ERR/i.test(e))).toEqual([]);
  });

  test('navigation Profil territorial / Analyser depuis actions graphe', async ({ page }) => {
    await page.goto(SDG_URL);
    await expect(page.locator('#sdg-shell')).toBeVisible({ timeout: 60_000 });

    // Injecte un popup de nœud central via API publique
    const opened = await page.evaluate(() => {
      const sdg = window.SpatialDecisionGraph;
      if (!sdg?.state?.nodeLayers) return false;
      const nodes = Object.values(sdg.state.nodeLayers);
      if (!nodes.length) return false;
      nodes[0].openPopup();
      return true;
    });
    test.skip(!opened, 'Aucun nœud SDG peinté (données / géométrie indisponibles)');

    const dossier = page.locator('.sdg-popup [data-sdg-nav*="decision-case"]');
    const analyze = page.locator('.sdg-popup [data-sdg-nav*="decision-detail"], .sdg-popup [data-sdg-nav*="decision-workspace"]');
    const twin = page.locator('.sdg-popup [data-sdg-nav*="territorial-twin"]');

    if (await dossier.count()) {
      await dossier.first().click();
      await expect.poll(() => page.url()).toMatch(/decision-case/);
    } else if (await analyze.count()) {
      await analyze.first().click();
      await expect.poll(() => page.url()).toMatch(/decision-detail|decision-workspace/);
    } else if (await twin.count()) {
      await twin.first().click();
      await expect.poll(() => page.url()).toMatch(/territorial-twin/);
    }
  });

  test('salle DG expose Présenter le raisonnement', async ({ page }) => {
    await page.goto('/index.html#salle-pilotage');
    const btn = page.locator('#edvs-sdg-present-btn');
    // Module peut charger async
    await expect(btn.or(page.locator('#edvs-cockpit-banner'))).toBeVisible({ timeout: 45_000 });
    if (await btn.count()) {
      await expect(btn).toContainText(/Présenter le raisonnement/i);
    }
  });
});
