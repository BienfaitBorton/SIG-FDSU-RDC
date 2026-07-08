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

async function openCartographyDrawerPanel(page, drawerKey) {
  await page.evaluate((key) => {
    const panelKeys = ['layers', 'legend', 'entities', 'info', 'classification'];
    panelKeys.forEach((panelKey) => {
      if (panelKey === key) return;
      const panel = document.querySelector(`#carto-drawer-${panelKey}`);
      panel?.classList.add('hidden');
      panel?.setAttribute('aria-hidden', 'true');
      const button = document.querySelector(`[data-carto-drawer="${panelKey}"]`);
      button?.classList.remove('is-active');
      button?.setAttribute('aria-expanded', 'false');
    });
    const drawer = document.querySelector(`#carto-drawer-${key}`);
    const button = document.querySelector(`[data-carto-drawer="${key}"]`);
    drawer?.classList.remove('hidden');
    drawer?.setAttribute('aria-hidden', 'false');
    button?.classList.add('is-active');
    button?.setAttribute('aria-expanded', 'true');
    document.querySelector('#cartography-sidebar')?.classList.remove('hidden');
    document.querySelector('#cartography-main-row')?.classList.add('has-sidebar-panel');
    if (window.cartographyState) {
      window.cartographyState.activeDrawer = key;
      window.cartographyState.openDrawers = [key];
    }
    window.cartographyState?.map?.invalidateSize();
  }, drawerKey);
  await expect(page.locator(`#carto-drawer-${drawerKey}`)).not.toHaveClass(/hidden/);
}

async function openAttributeExplorer(page) {
  await page.locator('[data-carto-explorer-open]').click();
  await expect(page.locator('#cartography-explorer-drawer')).not.toHaveClass(/hidden/);
}

async function checkCartographyLayer(page, layerKey) {
  await page.evaluate((key) => {
    const checkbox = document.querySelector(`#layer-list input[data-layer="${key}"]`);
    if (!checkbox || checkbox.disabled) return;
    checkbox.checked = true;
    checkbox.dispatchEvent(new Event('change', { bubbles: true }));
  }, layerKey);
}

async function openCartography(page) {
  await page.goto(MAP_URL);
  await expect(page.locator('#cartographie-panel')).not.toHaveClass(/hidden/);
  await expect(page.locator('.page-title')).toHaveText('Cartographie');
  await page.waitForFunction(() => typeof window.L !== 'undefined', null, { timeout: 45_000 });
  await expect(page.locator('#map.leaflet-container')).toBeVisible({ timeout: 30_000 });
  await page.waitForFunction(() => window.cartographyState?.initialized === true, null, { timeout: 30_000 });
  await openCartographyDrawerPanel(page, 'layers');
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
    await checkCartographyLayer(page, 'provinces');

    await page.waitForFunction(() => {
      const state = window.cartographyState;
      return state?.layerStatus?.provinces === true || state?.features?.provinces?.length > 0;
    }, null, { timeout: 45_000 });

    await openCartographyDrawerPanel(page, 'entities');
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
    await checkCartographyLayer(page, 'provinces');
    await page.waitForFunction(() => (window.cartographyState?.features?.provinces?.length ?? 0) > 0, null, { timeout: 45_000 });

    const map = page.locator('#map.leaflet-container');
    const box = await map.boundingBox();
    expect(box).toBeTruthy();

    await page.evaluate(() => {
      const state = window.cartographyState;
      const features = state?.features?.provinces || [];
      const feature = features[0];
      if (!feature) return;
      const layerKey = 'provinces';
      const featureId = feature.properties?.id || feature.properties?.canonical_id || feature.properties?.code;
      const layer = state.featureLayers?.[layerKey]?.[featureId] || state.layers?.provinces?.getLayers?.()?.[0];
      if (layer?.fire) {
        layer.fire('click', { originalEvent: new MouseEvent('click') });
      }
    });

    const infoPanel = page.locator('#cartography-sidebar #carto-info');
    await expect(page.locator('#cartography-sidebar')).not.toHaveClass(/hidden/, { timeout: 15_000 });
    await expect(page.locator('#carto-drawer-info')).not.toHaveClass(/hidden/, { timeout: 15_000 });
    await expect(infoPanel).toContainText(/.+/);

    const infoText = await infoPanel.innerText();
    const hasSelection = !infoText.includes('Sélectionnez un objet');
    if (hasSelection) {
      await expect(infoPanel).not.toContainText('Sélectionnez un objet sur la carte');
    }
  });

  test('Smart Map – fil d’Ariane, liste synchronisée, retour vue nationale', async ({ page }) => {
    await openCartography(page);

    await openAttributeExplorer(page);
    await page.waitForFunction(
      () => document.querySelectorAll('#attribute-table-body tr[data-feature-id]').length > 0,
      null,
      { timeout: 60_000 },
    );

    await page.evaluate(() => {
      document.querySelectorAll('.cartography-drawer').forEach((panel) => {
        panel.classList.add('hidden');
        panel.setAttribute('aria-hidden', 'true');
      });
      document.querySelector('#cartography-sidebar')?.classList.add('hidden');
      document.querySelector('#cartography-main-row')?.classList.remove('has-sidebar-panel');
      document.querySelector('#attribute-table-body tr[data-feature-id]')?.click();
    });

    await page.waitForFunction(
      () => !document.querySelector('#carto-info')?.textContent?.includes('Sélectionnez un objet'),
      null,
      { timeout: 15_000 },
    );

    await page.locator('#zoom-auto').click({ force: true });
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
    await openAttributeExplorer(page);

    await expect(page.locator('#attribute-layer-select')).toBeVisible();
    await expect(page.locator('#attribute-search')).toBeVisible();
    await expect(page.locator('#attribute-province-filter')).toBeVisible();

    await page.locator('#attribute-search').fill('a');
    await page.waitForTimeout(400);

    const totalLabel = page.locator('#cartography-explorer-drawer #attribute-total');
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
    await checkCartographyLayer(page, 'provinces');
    await page.waitForFunction(() => typeof window.cartographyState !== 'undefined', null, { timeout: 10_000 });
    await page.waitForTimeout(1500);

    const blocking = errors.filter((e) => !isNonBlockingConsoleError(e));
    expect(blocking).toEqual([]);
  });

  test('responsive desktop – layout cartographie', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await openCartography(page);

    await expect(page.locator('.cartography-workspace')).toBeVisible();
    await expect(page.locator('.cartography-map-stage')).toBeVisible();
    await expect(page.locator('.cartography-toolbar-row')).toBeVisible();
    await expect(page.locator('.cartography-tool-btn[data-carto-drawer="layers"]')).toBeVisible();
    await expect(page.locator('#cartography-explorer-drawer')).toHaveClass(/hidden/);

    await page.evaluate(() => {
      document.querySelector('#carto-drawer-layers')?.classList.add('hidden');
      document.querySelector('#cartography-sidebar')?.classList.add('hidden');
      document.querySelector('#cartography-main-row')?.classList.remove('has-sidebar-panel');
      window.cartographyState?.map?.invalidateSize();
    });
    await page.waitForTimeout(200);

    const stageBox = await page.locator('.cartography-map-stage').boundingBox();
    const mapBox = await page.locator('#map.leaflet-container').boundingBox();
    const mainRowBox = await page.locator('.cartography-main-row').boundingBox();
    expect(stageBox).toBeTruthy();
    expect(mapBox).toBeTruthy();
    expect(mainRowBox).toBeTruthy();
    if (stageBox && mapBox && mainRowBox) {
      expect(mapBox.width).toBeGreaterThan(700);
      expect(mapBox.height).toBeGreaterThan(400);
      expect(stageBox.width / mainRowBox.width).toBeGreaterThan(0.9);
    }

    await openCartographyDrawerPanel(page, 'layers');
    const sidebarBox = await page.locator('.cartography-sidebar').boundingBox();
    const mapWithSidebar = await page.locator('#map.leaflet-container').boundingBox();
    if (sidebarBox && mapWithSidebar && mainRowBox) {
      expect(sidebarBox.width).toBeLessThanOrEqual(320);
      expect(mapWithSidebar.width / (mapWithSidebar.width + sidebarBox.width)).toBeGreaterThan(0.55);
    }
  });

  test('validation SIG – carte principale et captures', async ({ page }) => {
    await page.goto(MAP_URL);
    await expect(page.locator('#cartographie-panel')).not.toHaveClass(/hidden/);
    await page.waitForFunction(() => window.cartographyState?.initialized === true, null, { timeout: 30_000 });
    await expect(page.locator('#map.leaflet-container')).toBeVisible();
    await expect(page.locator('#cartography-explorer-drawer')).toHaveClass(/hidden/);
    await expect(page.locator('.sig-map-info-compact')).toBeVisible();

    await page.screenshot({ path: 'test-results/cartography-map-main.png', fullPage: false });
    await openCartographyDrawerPanel(page, 'layers');
    await page.waitForTimeout(300);
    await page.screenshot({ path: 'test-results/cartography-layers-sidebar.png', fullPage: false });
    await openAttributeExplorer(page);
    await page.waitForTimeout(300);
    await page.screenshot({ path: 'test-results/cartography-explorer-drawer.png', fullPage: false });
  });

  test('validation UI – panneaux compacts tableau de bord', async ({ page }) => {
    await waitForAppReady(page);
    await page.waitForFunction(() => document.querySelectorAll('.dashboard-zones-list .sig-zone-card').length === 5, null, { timeout: 60_000 });

    const cards = page.locator('.dashboard-zones-list .sig-zone-card');
    await expect(cards).toHaveCount(5);

    const firstCard = cards.first();
    const box = await firstCard.boundingBox();
    expect(box).toBeTruthy();
    if (box) {
      expect(box.height).toBeGreaterThanOrEqual(85);
      expect(box.height).toBeLessThanOrEqual(115);
    }

    await page.screenshot({ path: 'test-results/dashboard-zones-compact.png', fullPage: false });
  });
});

test.describe('SIG-FDSU RDC – Module Cartographie libre', () => {
  test('plusieurs couches cochées s’affichent ensemble', async ({ page }) => {
    await openCartography(page);

    await page.waitForFunction(() => {
      const state = window.cartographyState;
      return state?.layerStatus?.provinces === true || (state?.features?.provinces?.length ?? 0) > 0;
    }, null, { timeout: 60_000 });

    await checkCartographyLayer(page, 'provinces');
    await page.waitForFunction(() => {
      const state = window.cartographyState;
      return state?.map?.hasLayer(state.layers.provinces)
        && state.layers.provinces.getLayers().length > 0;
    }, null, { timeout: 30_000 });

    await page.waitForFunction(() => (window.cartographyState?.features?.zones?.length ?? 0) > 0, null, { timeout: 30_000 });
    await checkCartographyLayer(page, 'zones');

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

  test('couches administratives inférieures se chargent et s’affichent', async ({ page }) => {
    await openCartography(page);

    for (const layerKey of ['territoires', 'collectivites', 'groupements', 'villages']) {
      await page.waitForFunction((key) => {
        const checkbox = document.querySelector(`#layer-list input[data-layer="${key}"]`);
        return checkbox && !checkbox.disabled;
      }, layerKey, { timeout: 60_000 });

      await checkCartographyLayer(page, layerKey);
      await page.waitForFunction((key) => {
        const state = window.cartographyState;
        return state?.map?.hasLayer(state.layers[key])
          && (state.layers[key].getLayers().length ?? 0) > 0
          && (state.features?.[key]?.length ?? 0) > 0;
      }, layerKey, { timeout: 45_000 });
    }
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

test.describe('SIG-FDSU RDC – Pages analytiques dashboard', () => {
  test('clic Zones FDSU ouvre une page dédiée sans superposition', async ({ page }) => {
    await waitForAppReady(page);
    await page.locator('.summary-card-zones').click();

    await expect(page.locator('#dashboard-detail-view')).toBeVisible();
    await expect(page.locator('#dashboard-detail-title')).toHaveText('Zones FDSU');
    await expect(page.locator('#dashboard-main-view')).toHaveClass(/hidden/);
    await expect(page.locator('#dashboard-workbench')).toHaveClass(/hidden/);
    await expect(page.locator('#entity-profile-drawer')).not.toHaveClass(/is-open/);
    await expect(page.locator('#dashboard-detail-map.leaflet-container')).toBeVisible({ timeout: 15_000 });
  });

  test('clic Provinces ouvre une page dédiée avec carte et liste', async ({ page }) => {
    await waitForAppReady(page);
    await page.locator('[data-detail-page="provinces"]').click();

    await expect(page.locator('#dashboard-detail-view')).toBeVisible();
    await expect(page.locator('#dashboard-detail-title')).toHaveText('Provinces');
    await page.waitForFunction(() => (window.dashboardViewState?.rows?.length ?? 0) > 0, null, { timeout: 60_000 });
    await expect(page.locator('#dashboard-detail-map.leaflet-container')).toBeVisible({ timeout: 15_000 });
    await expect(page.locator('#dashboard-detail-list .dashboard-detail-list-item').first()).toBeVisible({ timeout: 15_000 });
  });

  test('clic Territoires ouvre une page dédiée avec carte et liste', async ({ page }) => {
    await waitForAppReady(page);
    await page.locator('[data-detail-page="territories"]').click();

    await expect(page.locator('#dashboard-detail-view')).toBeVisible();
    await expect(page.locator('#dashboard-detail-title')).toHaveText('Territoires');
    await page.waitForFunction(() => window.dashboardViewState?.detailType === 'territories', null, { timeout: 15_000 });
    await expect(page.locator('#dashboard-detail-map')).toBeVisible();
    await expect(page.locator('#dashboard-detail-province-filter')).toBeVisible();
  });

  test('bouton Retour au tableau de bord fonctionne', async ({ page }) => {
    await waitForAppReady(page);
    await page.locator('[data-detail-page="provinces"]').click();
    await expect(page.locator('#dashboard-detail-view')).toBeVisible();

    await page.locator('#dashboard-detail-back').click();
    await expect(page.locator('#dashboard-main-view')).toBeVisible();
    await expect(page.locator('#dashboard-detail-view')).toHaveClass(/hidden/);
    await expect(page.locator('.summary-grid')).toBeVisible();
  });

  test('aucun panneau workbench ne masque le tableau de bord après clic KPI', async ({ page }) => {
    await waitForAppReady(page);
    await page.locator('[data-detail-page="collectivities"]').click();
    await expect(page.locator('#dashboard-workbench')).toHaveClass(/hidden/);
    await expect(page.locator('#dashboard-detail-view')).toBeVisible();
    await expect(page.locator('#dashboard-national-map')).toBeHidden();
  });
});
