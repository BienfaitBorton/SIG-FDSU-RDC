// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Spatial Decision Graph v2.1 — Analyse d’Impact Territorial
 * Mode DB réel : symbologie, filtres, légende, détail, présentation, navigation.
 * Aucune donnée inventée — uniquement le payload API.
 */

const API = 'http://127.0.0.1:8001';
const SITES = [
  { id: '7', program: 'sites_40' },
  { id: '29', program: 'sites_40' },
  { id: '30', program: 'sites_40' },
];

function sdgUrl(siteId, program = 'sites_40') {
  return `/index.html#spatial-impact/site/${siteId}?program_code=${program}`;
}

function attachDiag(page) {
  /** @type {string[]} */
  const pageErrors = [];
  /** @type {string[]} */
  const badText = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error' && /Leaflet.*already initialized|Map container is being reused/i.test(message.text())) {
      pageErrors.push(message.text());
    }
  });
  return { pageErrors, badText };
}

async function assertNoTechnicalLeak(page) {
  const body = await page.locator('#sdg-shell').innerText();
  expect(body).not.toMatch(/\[object Object\]/);
  expect(body).not.toMatch(/\bundefined\b/);
  expect(body).not.toMatch(/\bNaN\b/);
  expect(body).not.toMatch(/HTTP\s*400/i);
  expect(body).not.toMatch(/Actif\s*\/\s*Besoin/i);
}

test.describe('Spatial Decision Graph v2.1', () => {
  test('API graphe sites 7/29/30 : catégories typées + résumé', async ({ request }) => {
    for (const site of SITES) {
      const graph = await request.get(
        `${API}/api/spatial-decision-graph/site/${site.id}?program_code=${site.program}`,
      );
      expect(graph.ok(), `site ${site.id}`).toBeTruthy();
      const body = await graph.json();
      expect(body._meta?.version).toMatch(/^sdg-2\.1/);
      expect(body._meta?.title_ui).toMatch(/Analyse d’Impact Territorial|Analyse d'Impact Territorial/);
      expect(body.center?.kind).toBe('site');
      expect(body.center?.name).toBeTruthy();
      expect(body.decision_summary?.text).toBeTruthy();
      expect(Array.isArray(body.kpis)).toBeTruthy();
      expect(Array.isArray(body.categories)).toBeTruthy();

      const edu = (body.categories || []).find((c) => c.id === 'education');
      expect(edu?.status).toBe('future');

      for (const edge of body.edges || []) {
        expect(edge.nsme_trace?.relation_type).toBeTruthy();
        expect(edge.target_label || edge.target_entity?.name).toBeTruthy();
        const contrib = edge.score_contribution || edge.contribution || {};
        expect(['mapped', 'proxy', 'unavailable']).toContain(contrib.status);
      }
    }
  });

  test('Route site 30 : shell, symboles, légende, filtres', async ({ page }) => {
    const diag = attachDiag(page);
    await page.goto(sdgUrl('30'));

    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#dxl-title')).toContainText(/Analyse d’Impact Territorial|Analyse d'Impact Territorial/, {
      timeout: 45_000,
    });

    await expect(page.locator('#sdg-shell')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('#sdg-summary')).toBeVisible();
    await expect(page.locator('#sdg-filters')).toBeVisible();
    await expect(page.locator('#sdg-legend')).toBeVisible();
    await expect(page.locator('#sdg-detail')).toBeVisible();
    await expect(page.locator('#sdg-kpis')).toBeVisible();
    await expect(page.locator('#sdg-present-btn')).toBeVisible();
    await expect(page.locator('#sdg-relations-counter')).toContainText(/Relations affichées/);

    // Ancienne légende générique absente
    await expect(page.locator('#ux-legend-dxl')).toHaveCount(0);

    const leafletCount = await page.evaluate(() => document.querySelectorAll('#dxl-map.leaflet-container').length);
    expect(leafletCount).toBe(1);

    const markerCount = await page.locator('.sdg-marker').count();
    expect(markerCount).toBeGreaterThan(0);

    // Au moins le site central (symbole star)
    await expect(page.locator('.sdg-marker--site')).toHaveCount(1);

    // Filtre : décocher sans recréer Leaflet
    const filter = page.locator('#sdg-filters input[data-sdg-filter]:not([disabled])').first();
    if (await filter.count()) {
      await filter.uncheck();
      await expect(page.locator('#sdg-relations-counter')).toContainText(/Relations affichées/);
      const after = await page.evaluate(() => document.querySelectorAll('#dxl-map.leaflet-container').length);
      expect(after).toBe(1);
    }

    await assertNoTechnicalLeak(page);
    expect(diag.pageErrors.filter((e) => !/favicon|net::ERR/i.test(e))).toEqual([]);
  });

  test('Sites 7 et 29 : shell SDG monté', async ({ page }) => {
    for (const site of [{ id: '7' }, { id: '29' }]) {
      await page.goto(sdgUrl(site.id));
      await expect(page.locator('#sdg-shell')).toBeVisible({ timeout: 60_000 });
      await expect(page.locator('#sdg-summary')).toBeVisible();
      await expect(page.locator('.sdg-marker--site')).toHaveCount(1);
      await assertNoTechnicalLeak(page);
    }
  });

  test('Clic relation → panneau détail métier', async ({ page }) => {
    await page.goto(sdgUrl('30'));
    await expect(page.locator('#sdg-shell')).toBeVisible({ timeout: 60_000 });

    const clicked = await page.evaluate(() => {
      const sdg = window.SpatialDecisionGraph;
      const edges = Object.values(sdg?.state?.edgeLayers || {});
      if (!edges.length) return false;
      edges[0].fire('click');
      return true;
    });
    test.skip(!clicked, 'Aucune arête peinte (géométrie indisponible)');

    const detail = page.locator('#sdg-detail');
    await expect(detail).toContainText(/Origine|Destination|Type|Relation/i);
    const text = await detail.innerText();
    expect(text).not.toMatch(/\[object Object\]|undefined|NaN/);
  });

  test('Présentation : démarrage, pause, fin', async ({ page }) => {
    const diag = attachDiag(page);
    await page.goto(sdgUrl('30'));
    await expect(page.locator('#sdg-present-btn')).toBeVisible({ timeout: 60_000 });

    await page.locator('#sdg-present-btn').click();
    await expect(page.locator('#sdg-stop-btn')).toBeVisible({ timeout: 5_000 });
    await expect(page.locator('#sdg-step-label')).not.toHaveText('', { timeout: 5_000 });

    await page.locator('#sdg-stop-btn').click();
    await expect(page.locator('#sdg-stop-btn')).toBeHidden({ timeout: 5_000 });

    expect(diag.pageErrors.filter((e) => !/favicon|net::ERR/i.test(e))).toEqual([]);
  });

  test('Navigation dossier → impact sans double Leaflet', async ({ page }) => {
    test.setTimeout(120_000);
    const diag = attachDiag(page);
    await page.goto(`/index.html#decision-case/site/30?program_code=sites_40`);
    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/hidden/, { timeout: 45_000 });
    await expect(page.locator('#sdg-shell')).toBeVisible({ timeout: 60_000 });
    expect(await page.evaluate(() => document.querySelectorAll('#dxl-map.leaflet-container').length)).toBe(1);

    await page.goto(`/index.html#spatial-impact/site/30?program_code=sites_40`);
    await expect(page.locator('#sdg-shell')).toBeVisible({ timeout: 60_000 });
    expect(await page.evaluate(() => document.querySelectorAll('#dxl-map.leaflet-container').length)).toBe(1);
    await expect(page.locator('#ux-legend-dxl')).toHaveCount(0);

    const leafletErrors = diag.pageErrors.filter((e) => /Leaflet.*already initialized|Map container is being reused/i.test(e));
    expect(leafletErrors).toEqual([]);
  });
});
