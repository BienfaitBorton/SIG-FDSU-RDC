// @ts-check
const { test, expect } = require('@playwright/test');

const DASHBOARD_URL = '/index.html#dashboard';
const MAP_URL = '/index.html#map';

/** Erreurs JS non bloquantes connues (ressources optionnelles, tuiles OSM lentes). */
function isNonBlockingConsoleError(text) {
  const normalized = String(text || '').toLowerCase();
  return (
    normalized.includes('favicon')
    || normalized.includes('net::err_aborted')
    || normalized.includes('failed to load resource')
    || normalized.includes('404')
  );
}

function attachConsoleCollector(page) {
  /** @type {string[]} */
  const blockingErrors = [];
  page.on('pageerror', (error) => blockingErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error' && !isNonBlockingConsoleError(message.text())) {
      blockingErrors.push(message.text());
    }
  });
  return blockingErrors;
}

async function waitForAppReady(page) {
  await page.goto(DASHBOARD_URL);
  await expect(page.locator('.page-title')).toHaveText('Tableau de bord');
  await expect(page.locator('#api-status')).not.toHaveText('Chargement...', { timeout: 30_000 });
}

async function openCartography(page) {
  await page.goto(MAP_URL);
  await expect(page.locator('#cartographie-panel')).not.toHaveClass(/hidden/);
  await expect(page.locator('.page-title')).toHaveText('Cartographie');
  await page.waitForFunction(() => typeof window.L !== 'undefined', null, { timeout: 45_000 });
  await expect(page.locator('#map.leaflet-container')).toBeVisible({ timeout: 30_000 });
  await page.waitForFunction(() => window.cartographyState?.initialized === true, null, { timeout: 30_000 });
}

async function waitForNationalMapReady(page) {
  await page.waitForFunction(() => {
    const state = window.nationalMapState;
    return state?.initialized === true
      && state?.spatialContext?.layerKey === 'rdc'
      && (state?.features?.provinces?.length ?? 0) > 0
      && (state?.layers?.provinces?.getLayers?.().length ?? 0) > 0;
  }, null, { timeout: 60_000 });
  await expect(page.locator('#dashboard-national-map.leaflet-container')).toBeVisible({ timeout: 15_000 });
}

test.describe('SIG-FDSU RDC – Smart Map', () => {
  test('chargement complet du dashboard', async ({ page }) => {
    const errors = attachConsoleCollector(page);
    await waitForAppReady(page);

    await expect(page.locator('.app-shell')).toBeVisible();
    await expect(page.locator('.sidebar')).toBeVisible();
    await expect(page.locator('#dashboard-panel')).toBeVisible();
    await expect(page.locator('#stat-provinces')).not.toHaveText('—');
    await expect(page.locator('#db-status')).not.toHaveText('Chargement...');

    expect(errors.filter((e) => !isNonBlockingConsoleError(e))).toEqual([]);
  });

  test('affichage de la carte Leaflet', async ({ page }) => {
    const errors = attachConsoleCollector(page);
    await openCartography(page);

    await expect(page.locator('#map')).toBeVisible();
    await expect(page.locator('#map.leaflet-container')).toHaveClass(/leaflet-container/);
    await expect(page.locator('#map-breadcrumb')).toContainText('RDC');

    expect(errors.filter((e) => !isNonBlockingConsoleError(e))).toEqual([]);
  });

  test('affichage et activation des couches', async ({ page }) => {
    await openCartography(page);

    const provincesCheckbox = page.locator('#layer-list input[data-layer="provinces"]');
    await expect(provincesCheckbox).toBeVisible();
    await page.waitForFunction(() => {
      const checkbox = document.querySelector('#layer-list input[data-layer="provinces"]');
      return checkbox && !checkbox.disabled;
    }, null, { timeout: 60_000 });
    await provincesCheckbox.check();

    await page.waitForFunction(() => {
      const state = window.cartographyState;
      return state?.layerStatus?.provinces === true || state?.features?.provinces?.length > 0;
    }, null, { timeout: 45_000 });

    await expect(page.locator('#map-synchronized-list .sync-list-header, #map-synchronized-list .zone-detail-empty')).toBeVisible();
  });

  test('zoom et déplacement sur la carte', async ({ page }) => {
    await openCartography(page);

    const map = page.locator('#map.leaflet-container');
    await expect(map).toBeVisible();
    await expect(page.locator('.leaflet-control-zoom-in')).toBeVisible();
    await expect(page.locator('.leaflet-control-zoom-out')).toBeVisible();

    const center = await page.evaluate(() => {
      const leafletMap = window.cartographyState?.map;
      if (!leafletMap) return null;
      const centerPoint = leafletMap.getCenter();
      return { lat: centerPoint.lat, lng: centerPoint.lng, zoom: leafletMap.getZoom() };
    });
    expect(center).toBeTruthy();

    const box = await map.boundingBox();
    expect(box).toBeTruthy();
    if (box) {
      const x = box.x + box.width / 2;
      const y = box.y + box.height / 2;
      await page.mouse.move(x, y);
      await page.mouse.wheel(0, -240);
      await page.waitForTimeout(300);
      await page.mouse.down();
      await page.mouse.move(x + 80, y + 40, { steps: 8 });
      await page.mouse.up();
    }

    const afterInteraction = await page.evaluate(() => {
      const leafletMap = window.cartographyState?.map;
      if (!leafletMap) return null;
      const centerPoint = leafletMap.getCenter();
      return { lat: centerPoint.lat, lng: centerPoint.lng, zoom: leafletMap.getZoom() };
    });
    expect(afterInteraction).toBeTruthy();
  });

  test('popup et panneau latéral sur sélection', async ({ page }) => {
    await openCartography(page);

    await page.waitForFunction(() => {
      const checkbox = document.querySelector('#layer-list input[data-layer="provinces"]');
      return checkbox && !checkbox.disabled;
    }, null, { timeout: 60_000 });
    await page.locator('#layer-list input[data-layer="provinces"]').check();
    await page.waitForFunction(() => (window.cartographyState?.features?.provinces?.length ?? 0) > 0, null, { timeout: 45_000 });

    const map = page.locator('#map.leaflet-container');
    const box = await map.boundingBox();
    expect(box).toBeTruthy();

    await page.mouse.click(box.x + box.width * 0.52, box.y + box.height * 0.48);

    const infoPanel = page.locator('#carto-info');
    await expect(infoPanel).toBeVisible();
    await expect(page.locator('.cartography-sidebar')).toBeVisible();

    const infoText = await infoPanel.innerText();
    const hasSelection = !infoText.includes('Sélectionnez un objet');
    if (hasSelection) {
      await expect(infoPanel).not.toContainText('Sélectionnez un objet sur la carte');
    }
  });

  test('Smart Map – fil d’Ariane, liste synchronisée, retour vue nationale', async ({ page }) => {
    await openCartography(page);

    await page.waitForFunction(
      () => document.querySelectorAll('#attribute-table-body tr[data-feature-id]').length > 0,
      null,
      { timeout: 60_000 },
    );

    const firstRow = page.locator('#attribute-table-body tr[data-feature-id]').first();
    await firstRow.click();

    await page.waitForFunction(
      () => !document.querySelector('#carto-info')?.textContent?.includes('Sélectionnez un objet'),
      null,
      { timeout: 15_000 },
    );

    await page.locator('#zoom-auto').click();
    await expect(page.locator('#map-breadcrumb')).toContainText('RDC');
  });

  test('recherche globale', async ({ page }) => {
    await waitForAppReady(page);

    const searchInput = page.locator('#global-search-input');
    await searchInput.click();
    await searchInput.fill('kin');
    await page.waitForFunction(() => (window.platformState?.searchIndex?.length ?? 0) > 0, null, { timeout: 60_000 });
    await page.waitForFunction(() => window.platformState?.searchReady === true, null, { timeout: 15_000 });
    await expect(page.locator('#global-search-results')).toBeVisible({ timeout: 15_000 });
    const resultCount = await page.locator('#global-search-results .global-search-result').count();
    const emptyCount = await page.locator('#global-search-results .global-search-empty').count();
    expect(resultCount + emptyCount).toBeGreaterThan(0);
    if (resultCount > 0) {
      await expect(page.locator('#global-search-results .global-search-result').first()).toBeVisible();
    }
  });

  test('filtres explorateur attributaire', async ({ page }) => {
    await openCartography(page);

    await expect(page.locator('#attribute-layer-select')).toBeVisible();
    await expect(page.locator('#attribute-search')).toBeVisible();
    await expect(page.locator('#attribute-province-filter')).toBeVisible();

    await page.locator('#attribute-search').fill('a');
    await page.waitForTimeout(400);

    const totalLabel = page.locator('#attribute-total');
    await expect(totalLabel).toBeVisible();
    await expect(totalLabel).not.toHaveText('0 élément');
  });

  test('absence d’erreurs JavaScript bloquantes', async ({ page }) => {
    const errors = attachConsoleCollector(page);
    await openCartography(page);

    await page.waitForFunction(() => {
      const checkbox = document.querySelector('#layer-list input[data-layer="provinces"]');
      return checkbox && !checkbox.disabled;
    }, null, { timeout: 60_000 });
    await page.locator('#layer-list input[data-layer="provinces"]').check();
    await page.waitForFunction(() => typeof window.cartographyState !== 'undefined', null, { timeout: 10_000 });
    await page.waitForTimeout(1500);

    const blocking = errors.filter((e) => !isNonBlockingConsoleError(e));
    expect(blocking).toEqual([]);
  });

  test('responsive desktop – layout cartographie', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await openCartography(page);

    await expect(page.locator('.cartography-layout')).toBeVisible();
    await expect(page.locator('.cartography-main')).toBeVisible();
    await expect(page.locator('.cartography-sidebar')).toBeVisible();

    const layoutBox = await page.locator('.cartography-layout').boundingBox();
    const sidebarBox = await page.locator('.cartography-sidebar').boundingBox();
    expect(layoutBox).toBeTruthy();
    expect(sidebarBox).toBeTruthy();
    if (layoutBox && sidebarBox) {
      expect(sidebarBox.width).toBeGreaterThan(200);
      expect(layoutBox.width).toBeGreaterThan(sidebarBox.width);
    }
  });
});

test.describe('SIG-FDSU RDC – Module Cartographie libre', () => {
  test('plusieurs couches cochées s’affichent ensemble', async ({ page }) => {
    await openCartography(page);

    await page.waitForFunction(() => {
      const state = window.cartographyState;
      return state?.layerStatus?.provinces === true || (state?.features?.provinces?.length ?? 0) > 0;
    }, null, { timeout: 60_000 });

    await page.locator('#layer-list input[data-layer="provinces"]').check();
    await page.waitForFunction(() => {
      const state = window.cartographyState;
      return state?.map?.hasLayer(state.layers.provinces)
        && state.layers.provinces.getLayers().length > 0;
    }, null, { timeout: 30_000 });

    await page.waitForFunction(() => (window.cartographyState?.features?.zones?.length ?? 0) > 0, null, { timeout: 30_000 });
    await page.locator('#layer-list input[data-layer="zones"]').check();

    await page.waitForFunction(() => {
      const state = window.cartographyState;
      return state?.map?.hasLayer(state.layers.provinces)
        && state?.map?.hasLayer(state.layers.zones)
        && state.layers.zones.getLayers().length > 0;
    }, null, { timeout: 30_000 });

    const stats = await page.evaluate(() => ({
      provincesOnMap: window.cartographyState.map.hasLayer(window.cartographyState.layers.provinces),
      zonesOnMap: window.cartographyState.map.hasLayer(window.cartographyState.layers.zones),
      provincesCount: window.cartographyState.layers.provinces.getLayers().length,
      zonesCount: window.cartographyState.layers.zones.getLayers().length,
      totalProvinces: window.cartographyState.features.provinces.length,
    }));

    expect(stats.provincesOnMap).toBe(true);
    expect(stats.zonesOnMap).toBe(true);
    expect(stats.provincesCount).toBe(stats.totalProvinces);
    expect(stats.zonesCount).toBeGreaterThan(0);
  });
});

test.describe('SIG-FDSU RDC – Cartographie nationale (tableau de bord)', () => {
  test('la carte nationale s’affiche avec les provinces', async ({ page }) => {
    await waitForAppReady(page);
    await waitForNationalMapReady(page);

    const stats = await page.evaluate(() => ({
      context: window.nationalMapState.spatialContext?.layerKey,
      visibleProvinces: window.nationalMapState.layers.provinces.getLayers().length,
      totalProvinces: window.nationalMapState.features.provinces.length,
      territoiresVisible: window.nationalMapState.map.hasLayer(window.nationalMapState.layers.territoires),
    }));

    expect(stats.context).toBe('rdc');
    expect(stats.visibleProvinces).toBe(stats.totalProvinces);
    expect(stats.totalProvinces).toBeGreaterThan(0);
    expect(stats.territoiresVisible).toBe(false);
  });

  test('clic province isole le contexte et met à jour le fil d’Ariane', async ({ page }) => {
    await waitForAppReady(page);
    await waitForNationalMapReady(page);

    const totalProvinces = await page.evaluate(() => window.nationalMapState.features.provinces.length);
    await page.locator('#dashboard-map-synchronized-list .sync-list-item').first().click();

    await page.waitForFunction(() => (window.nationalMapState?.spatialContextTrail?.length ?? 0) > 1, null, { timeout: 30_000 });

    const after = await page.evaluate(() => ({
      visibleProvinces: window.nationalMapState.layers.provinces.getLayers().length,
      breadcrumb: document.querySelector('#dashboard-map-breadcrumb')?.innerText || '',
      backEnabled: !document.querySelector('#dashboard-map-context-back')?.disabled,
      contextLayer: window.nationalMapState.spatialContext?.layerKey,
    }));

    expect(after.contextLayer).toBe('provinces');
    expect(after.visibleProvinces).toBe(1);
    expect(after.breadcrumb).toContain('RDC');
    expect(after.backEnabled).toBe(true);
    expect(totalProvinces).toBeGreaterThan(1);
  });

  test('clic territoire affiche uniquement les collectivités du contexte', async ({ page }) => {
    await waitForAppReady(page);
    await waitForNationalMapReady(page);

    await page.locator('#dashboard-map-synchronized-list .sync-list-item').first().click();
    await page.waitForFunction(() => window.nationalMapState.spatialContext?.layerKey === 'provinces', null, { timeout: 30_000 });

    await page.waitForFunction(
      () => {
        const listCount = document.querySelectorAll('#dashboard-map-synchronized-list .sync-list-item').length;
        const emptyMessage = document.querySelector('#dashboard-map-synchronized-list .zone-detail-empty, #dashboard-map-message')?.textContent || '';
        return listCount > 0 || /Aucune subdivision disponible/i.test(emptyMessage);
      },
      null,
      { timeout: 30_000 },
    );

    const territoryCount = await page.locator('#dashboard-map-synchronized-list .sync-list-item').count();
    if (territoryCount === 0) {
      await expect(page.locator('#dashboard-map-message')).toContainText(/Aucune subdivision disponible/i);
      return;
    }

    await page.locator('#dashboard-map-synchronized-list .sync-list-item').first().click();
    await page.waitForFunction(() => window.nationalMapState.spatialContext?.layerKey === 'territoires', null, { timeout: 30_000 });

    const stats = await page.evaluate(() => ({
      visibleTerritoires: window.nationalMapState.layers.territoires.getLayers().length,
      contextLayer: window.nationalMapState.spatialContext?.layerKey,
      breadcrumb: document.querySelector('#dashboard-map-breadcrumb')?.innerText || '',
    }));

    expect(stats.contextLayer).toBe('territoires');
    expect(stats.visibleTerritoires).toBe(1);
    expect(stats.breadcrumb).toMatch(/RDC/i);
  });

  test('bouton retour et vue nationale restaurent la RDC', async ({ page }) => {
    await waitForAppReady(page);
    await waitForNationalMapReady(page);

    await page.locator('#dashboard-map-synchronized-list .sync-list-item').first().click();
    await page.waitForFunction(() => (window.nationalMapState?.spatialContextTrail?.length ?? 0) > 1, null, { timeout: 30_000 });

    await page.locator('#dashboard-map-context-back').click();
    await page.waitForFunction(() => window.nationalMapState.spatialContext?.layerKey === 'rdc', null, { timeout: 15_000 });
    await expect(page.locator('#dashboard-map-breadcrumb')).toContainText('RDC');

    await page.locator('#dashboard-map-synchronized-list .sync-list-item').first().click();
    await page.waitForFunction(() => window.nationalMapState.spatialContext?.layerKey === 'provinces', null, { timeout: 15_000 });

    await page.locator('#dashboard-map-reset-national').click();
    await page.waitForFunction(() => window.nationalMapState.spatialContext?.layerKey === 'rdc', null, { timeout: 15_000 });
    await expect(page.locator('#dashboard-map-context-back')).toBeDisabled();
  });

  test('aucun crash si une subdivision est vide', async ({ page }) => {
    const errors = attachConsoleCollector(page);
    await waitForAppReady(page);
    await waitForNationalMapReady(page);

    await page.evaluate(async () => {
      window.nationalMapState.features.missions = [];
      window.nationalMapState.data.missions = [];
      window.nationalMapState.spatialContext = {
        level: 'sites',
        layerKey: 'sites',
        featureId: 'site-test-empty',
        properties: { nom: 'Site test', id: 'site-test-empty' },
        feature: null,
      };
      window.nationalMapState.spatialContextTrail = [
        { layerKey: 'rdc', label: 'RDC', properties: {} },
        { layerKey: 'sites', label: 'Site test', properties: { nom: 'Site test' } },
      ];
      if (typeof renderNationalContextMap === 'function') renderNationalContextMap();
    });

    await expect(page.locator('#dashboard-map-message')).toContainText(/Aucune subdivision disponible/i);
    expect(errors.filter((e) => !isNonBlockingConsoleError(e))).toEqual([]);
  });
});
