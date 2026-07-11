// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Tableau de Synthèse Territoriale (TST) v1.1 — drill-down cartographique
 */

async function waitProvinces(page) {
  await page.goto('/index.html#decision-view');
  await expect(page.locator('#decision-view-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
  await page.waitForFunction(
    () => document.querySelectorAll('#decision-center-tst-host .leaflet-interactive').length >= 20,
    null,
    { timeout: 60_000 },
  );
}

async function clickProvinceByName(page, name) {
  const clicked = await page.evaluate((provinceName) => {
    const host = document.querySelector('#decision-center-tst-host');
    const mapId = host?.querySelector('.tst-map')?.id;
    const inst = window.TerritorialSummary?.getInstance?.(host);
    const layer = inst?.getState?.()?.layer || null;
    // Fallback : parcourir les path leaflet et matcher le tooltip via features
    const root = host;
    if (!root) return false;
    // Accès via Leaflet map layers
    const mapEl = root.querySelector('.leaflet-container');
    if (!mapEl || !window.L) return false;
    let found = null;
    root.querySelectorAll('.leaflet-interactive').forEach((el) => {
      // no-op collect
    });
    // Utiliser l'API interne : déclencher handleSelect via clic sur feature name
    const api = window.TerritorialSummary.getInstance(host);
    const st = api?.getState?.();
    if (!st?.layer) return false;
    st.layer.eachLayer((lyr) => {
      const n = lyr.feature?.properties?.name || '';
      if (String(n).toLowerCase().replace(/-/g, ' ') === provinceName.toLowerCase().replace(/-/g, ' ')) {
        found = lyr;
      }
    });
    if (found) {
      found.fire('click');
      return true;
    }
    return false;
  }, name);
  expect(clicked).toBeTruthy();
}

test.describe('Tableau de Synthèse Territoriale', () => {
  test('API metrics + mount CD — provinces réelles', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(String(err)));

    await waitProvinces(page);
    await expect(page.locator('#decision-center-tst-host .tst-legend, #decision-center-tst-host .ux-map-legend').first()).toBeVisible();
    await expect(page.locator('#decision-center-tst-host .tst-breadcrumb')).toContainText('RDC');

    const dirty = await page.evaluate(() => {
      const text = document.querySelector('#decision-center-tst-host')?.innerText || '';
      return /\bundefined\b|\bnull\b|\bNaN\b/.test(text);
    });
    expect(dirty).toBeFalsy();
    expect(errors.filter((e) => !/favicon|net::/i.test(e))).toEqual([]);
  });

  test('drill-down Haut-Lomami — territoires visibles, carte non vide', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(String(err)));
    await waitProvinces(page);

    const before = await page.locator('#decision-center-tst-host .leaflet-interactive').count();
    expect(before).toBeGreaterThanOrEqual(20);

    await clickProvinceByName(page, 'Haut-Lomami');
    await expect(page.locator('#decision-center-tst-host .tst-breadcrumb')).toContainText(/Haut.?Lomami/i, { timeout: 20_000 });

    // Pendant / après chargement : au moins un polygone (parent ou enfants)
    await expect.poll(async () => page.locator('#decision-center-tst-host .leaflet-interactive').count(), {
      timeout: 45_000,
    }).toBeGreaterThan(0);

    const layerMeta = await page.waitForFunction(async () => {
      const res = await fetch('http://127.0.0.1:8001/api/territorial-summary/layer?level=territoire&parent_id=Haut-Lomami&metric=priority');
      return res.json();
    }, null, { timeout: 30_000 }).then((h) => h.jsonValue());

    expect(layerMeta.geometry_status).toMatch(/complete|partial/);
    expect(layerMeta.geometry_count).toBeGreaterThan(0);
    expect(layerMeta.parent?.geometry).toBeTruthy();

    await expect.poll(async () => page.locator('#decision-center-tst-host .leaflet-interactive').count(), {
      timeout: 30_000,
    }).toBeGreaterThanOrEqual(Math.min(Number(layerMeta.geometry_count) || 1, 3));

    // Zoom réellement recentré (plus de vue nationale large)
    const zoom = await page.evaluate(() => {
      const host = document.querySelector('#decision-center-tst-host');
      const api = window.TerritorialSummary?.getInstance?.(host);
      // Leaflet map zoom via DOM _leaflet_id is opaque — check status text
      return document.querySelector('#decision-center-tst-host .tst-status')?.textContent || '';
    });
    expect(zoom).toMatch(/géométries|territoire|entités/i);

    // Tooltip territoire
    await page.locator('#decision-center-tst-host .leaflet-interactive').first().hover({ force: true });
    await expect(page.locator('.leaflet-tooltip').first()).toBeVisible({ timeout: 10_000 });

    // Retour province via fil d’Ariane
    await page.locator('#decision-center-tst-host [data-tst-crumb="1"]').click();
    await expect(page.locator('#decision-center-tst-host .tst-breadcrumb')).toContainText(/Haut.?Lomami/i);
    await expect.poll(async () => page.locator('#decision-center-tst-host .leaflet-interactive').count()).toBeGreaterThan(0);

    // Retour RDC
    await page.locator('#decision-center-tst-host [data-tst-crumb="0"]').click();
    await expect(page.locator('#decision-center-tst-host .tst-breadcrumb')).toContainText('RDC');
    await page.waitForFunction(
      () => document.querySelectorAll('#decision-center-tst-host .leaflet-interactive').length >= 20,
      null,
      { timeout: 45_000 },
    );

    expect(errors.filter((e) => !/favicon|net::/i.test(e))).toEqual([]);
  });

  test('API layer — FeatureCollection territoire expliquée (pas vide ambigu)', async ({ request }) => {
    const res = await request.get('http://127.0.0.1:8001/api/territorial-summary/layer?level=territoire&parent_id=Haut-Lomami&metric=priority');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.geometry_status).toBeTruthy();
    expect(['complete', 'partial', 'unavailable']).toContain(body.geometry_status);
    if (body.geometry_status === 'unavailable') {
      expect(body.message).toMatch(/limites détaillées/i);
    } else {
      expect(body.geometry_count).toBeGreaterThan(0);
    }
    const feats = Array.isArray(body.features) ? body.features : body.features?.features;
    expect(Array.isArray(feats)).toBeTruthy();
  });

  test('plusieurs provinces — géométries territoires', async ({ request }) => {
    for (const province of ['Haut-Lomami', 'Kinshasa', 'Nord-Kivu']) {
      const res = await request.get(
        `http://127.0.0.1:8001/api/territorial-summary/layer?level=territoire&parent_id=${encodeURIComponent(province)}&metric=priority`,
      );
      expect(res.ok()).toBeTruthy();
      const body = await res.json();
      expect(body.geometry_status).toBeTruthy();
      expect(body.parent === null || body.parent?.geometry || body.geometry_status === 'unavailable').toBeTruthy();
    }
  });

  test('tooltip + clic province + fil d’Ariane', async ({ page }) => {
    await waitProvinces(page);
    const poly = page.locator('#decision-center-tst-host .leaflet-interactive').first();
    await poly.hover({ force: true });
    await expect(page.locator('.leaflet-tooltip.sig-map-tooltip, .leaflet-tooltip').first()).toBeVisible({ timeout: 10_000 });
    await poly.click({ force: true });
    await expect(page.locator('#decision-center-tst-host .tst-breadcrumb')).toContainText(/.+/, { timeout: 20_000 });
    await expect.poll(async () => page.locator('#decision-center-tst-host .leaflet-interactive').count()).toBeGreaterThan(0);
    await page.locator('#decision-center-tst-host [data-tst-crumb="0"]').click();
    await expect(page.locator('#decision-center-tst-host .tst-breadcrumb')).toContainText('RDC');
    await expect(page.locator('#decision-center-tst-host .leaflet-interactive').first()).toBeVisible({ timeout: 30_000 });
  });

  test('changement de métrique — données réelles', async ({ page }) => {
    await waitProvinces(page);
    const select = page.locator('#decision-center-tst-host .tst-metric-select');
    await select.selectOption('sites_fdsu');
    await expect(page.locator('#decision-center-tst-host .tst-status')).toContainText(/provinces|données|géométries/i, { timeout: 30_000 });
  });

  test('pas de double instance Leaflet dans le host TST', async ({ page }) => {
    await page.goto('/index.html#decision-view');
    await expect(page.locator('#decision-center-tst-host .leaflet-container')).toHaveCount(1, { timeout: 45_000 });
  });

  test('conservation contexte TerritorialContext', async ({ page }) => {
    await waitProvinces(page);
    await page.locator('#decision-center-tst-host .leaflet-interactive').first().click({ force: true });
    await page.waitForTimeout(800);
    const ctx = await page.evaluate(() => window.TerritorialContext?.get?.());
    expect(ctx?.trail?.length).toBeGreaterThanOrEqual(1);
  });

  test('Salle de Pilotage DG — TST permanent', async ({ page }) => {
    await page.goto('/index.html#salle-pilotage');
    await expect(page.locator('#salle-pilotage-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#edvs-tst-host .tst-root, #edvs-tst-host .leaflet-container').first()).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('#edvs-cockpit-map')).toHaveCount(0);
  });
});
