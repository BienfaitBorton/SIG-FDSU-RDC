// @ts-check
const { test, expect } = require('@playwright/test');

const MAP_URL = '/index.html#map';

function attachConsoleCollector(page) {
  /** @type {string[]} */
  const blockingErrors = [];
  page.on('pageerror', (error) => blockingErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error' && /Leaflet.*already initialized|Map container is being reused/i.test(message.text())) {
      blockingErrors.push(message.text());
    }
  });
  return blockingErrors;
}

test.describe('Cartography Experience Premium v0.9.1', () => {
  test('barre premium, basemap, pas de double Leaflet', async ({ page }) => {
    const errors = attachConsoleCollector(page);
    await page.goto(MAP_URL);
    await page.waitForFunction(() => window.cartographyState?.initialized === true, null, { timeout: 45000 });

    await expect(page.locator('.cartography-toolbar-premium')).toBeVisible();
    await expect(page.locator('#carto-demo-btn')).toBeVisible();
    await expect(page.locator('#carto-measure-btn')).toBeVisible();
    await expect(page.locator('#carto-basemap-btn')).toBeVisible();

    const leafletCount = await page.locator('#map.leaflet-container').count();
    expect(leafletCount).toBe(1);

    await page.locator('#carto-basemap-btn').click();
    await expect(page.locator('#carto-drawer-settings')).not.toHaveClass(/hidden/, { timeout: 10000 });

    expect(errors).toEqual([]);
  });

  test('mode Démonstration — plein écran applicatif et sortie', async ({ page }) => {
    const errors = attachConsoleCollector(page);
    await page.goto(MAP_URL);
    await page.waitForFunction(() => window.cartographyState?.initialized === true, null, { timeout: 45000 });

    await page.locator('#carto-demo-btn').click();
    await expect(page.locator('body')).toHaveClass(/cartography-demo-mode/);
    await expect(page.locator('#cartography-demo-bar')).toBeVisible();

    await page.locator('#carto-demo-exit').click();
    await expect(page.locator('body')).not.toHaveClass(/cartography-demo-mode/);

    expect(errors).toEqual([]);
  });

  test('légende catégorisée avec transparence', async ({ page }) => {
    await page.goto(MAP_URL);
    await page.waitForFunction(() => window.cartographyState?.initialized === true, null, { timeout: 45000 });

    await page.locator('[data-carto-drawer="legend"]').first().click();
    await expect(page.locator('.cartography-legend-category')).toHaveCount(6, { timeout: 10000 });
    await expect(page.locator('[data-legend-opacity="zones"]')).toBeVisible();
  });

  test('popup enrichi au clic — visible dans le viewport', async ({ page }) => {
    await page.goto(MAP_URL);
    await page.waitForFunction(() => window.cartographyState?.initialized === true, null, { timeout: 45000 });

    await page.evaluate(() => {
      const checkbox = document.querySelector('#layer-list input[data-layer="zones"]');
      if (checkbox && !checkbox.checked) {
        checkbox.checked = true;
        checkbox.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    await page.waitForTimeout(3000);

    const clicked = await page.evaluate(async () => {
      const map = window.cartographyState?.map;
      const layerGroup = window.cartographyState?.layers?.zones;
      if (!map || !layerGroup?.getLayers) return false;
      const layers = layerGroup.getLayers();
      if (!layers.length) return false;
      const layer = layers[0];
      const center = layer.getBounds?.()?.getCenter?.();
      if (!center) return false;
      map.setView(center, 7);
      await new Promise((r) => setTimeout(r, 800));
      layer.fire('click', { latlng: center });
      return true;
    });
    test.skip(!clicked, 'Couche zones indisponible pour le test popup');

    const popup = page.locator('.leaflet-popup.sig-map-popup');
    await expect(popup).toBeVisible({ timeout: 15000 });
    const box = await popup.boundingBox();
    const viewport = page.viewportSize();
    expect(box).toBeTruthy();
    if (box && viewport) {
      expect(box.x).toBeGreaterThanOrEqual(-4);
      expect(box.y).toBeGreaterThanOrEqual(-4);
      expect(box.x + box.width).toBeLessThanOrEqual(viewport.width + 4);
      expect(box.y + box.height).toBeLessThanOrEqual(viewport.height + 4);
    }
  });
});
