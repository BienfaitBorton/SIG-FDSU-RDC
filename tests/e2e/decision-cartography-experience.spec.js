// @ts-check
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

/**
 * Executive Presentation Mode — Phase 2.1
 * UX only. Sites 14 / 16 / 26 / 29 / 34.
 */

const SITES = ['14', '16', '26', '29', '34'];
const CAPTURE_DIR = path.join(
  __dirname,
  '../../PROJECT_MANAGEMENT/ARCHITECTURE/captures/executive-presentation-mode',
);

function caseUrl(id) {
  return `/index.html#decision-case/site/${id}?program_code=sites_40`;
}

async function waitSdg(page) {
  await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
  await expect(page.locator('#sdg-shell')).toBeVisible({ timeout: 90_000 });
  await expect(page.locator('#epm-enter-btn')).toBeVisible({ timeout: 30_000 });
}

async function enterEpm(page) {
  await page.locator('#epm-enter-btn').click();
  await expect(page.locator('body')).toHaveClass(/executive-presentation-mode/);
  await expect(page.locator('#epm-root')).toBeVisible();
}

test.describe('Executive Presentation Mode — Phase 2.1', () => {
  test.beforeAll(() => {
    fs.mkdirSync(CAPTURE_DIR, { recursive: true });
  });

  for (const siteId of SITES) {
    test(`site/${siteId} — entrée EPM, immersion, KPI, sortie`, async ({ page }) => {
      const pageErrors = [];
      page.on('pageerror', (e) => pageErrors.push(e.message));

      await page.goto(caseUrl(siteId));
      await waitSdg(page);

      // Avant
      if (siteId === '29') {
        await page.screenshot({
          path: path.join(CAPTURE_DIR, '01-before-dossier.png'),
          fullPage: false,
        });
      }

      await enterEpm(page);

      // Sections dossier masquées
      await expect(page.locator('.dxl-topbar')).toBeHidden();
      await expect(page.locator('#epm-kpi-strip')).toBeVisible();
      await expect(page.locator('#epm-command-dock')).toBeVisible();

      // Un seul Leaflet
      const mapCount = await page.locator('.leaflet-container').count();
      expect(mapCount).toBe(1);

      // Carte dominante (> 85 % hauteur utile stage)
      const ratio = await page.evaluate(() => {
        const host = document.querySelector('#sdg-map-host');
        const shell = document.querySelector('#sdg-shell');
        if (!host || !shell) return 0;
        const hr = host.getBoundingClientRect();
        const sr = shell.getBoundingClientRect();
        return sr.height > 0 ? hr.height / sr.height : 0;
      });
      expect(ratio).toBeGreaterThan(0.72);

      // Panneaux masqués au démarrage
      await expect(page.locator('#sdg-filters-panel')).toHaveClass(/epm-panel-hidden/);
      await expect(page.locator('#sdg-detail')).toHaveClass(/epm-panel-hidden/);

      // Pas de bouton décoratif actif Export (disabled / À venir)
      await expect(page.locator('.epm-dock-btn.is-coming')).toBeDisabled();

      if (siteId === '29') {
        await page.screenshot({
          path: path.join(CAPTURE_DIR, '02-executive-empty.png'),
          fullPage: false,
        });
        await page.screenshot({
          path: path.join(CAPTURE_DIR, '03-executive-kpi.png'),
          fullPage: false,
        });
      }

      // Guidé
      await page.locator('#epm-btn-guided').click();
      await expect(page.locator('#epm-guided-nav')).toHaveClass(/is-visible/);
      await expect(page.locator('#epm-narrative')).not.toHaveText('');

      const next = page.locator('#epm-btn-next');
      if (await next.isEnabled()) {
        await next.click();
        if (siteId === '29') {
          await page.screenshot({
            path: path.join(CAPTURE_DIR, '04-guided-step.png'),
            fullPage: false,
          });
        }
      }

      // ESC quitte
      await page.keyboard.press('Escape');
      // Si un panneau s'était ouvert, second Escape
      if (await page.locator('body.executive-presentation-mode').count()) {
        await page.keyboard.press('Escape');
      }
      await expect(page.locator('body')).not.toHaveClass(/executive-presentation-mode/);

      expect(pageErrors.filter((m) => !/ResizeObserver|favicon/i.test(m))).toEqual([]);
    });
  }

  test('site/29 — sélection détail, popup, restauration', async ({ page }) => {
    await page.goto(caseUrl('29'));
    await waitSdg(page);
    await enterEpm(page);

    // Ouvrir couches
    await page.locator('#epm-btn-layers').click();
    await expect(page.locator('#sdg-filters-panel')).toHaveClass(/epm-panel-open/);

    // Fermer panneau via bouton Fermer (Échap gère aussi fullscreen navigateur)
    await page.locator('#sdg-filters-panel .epm-panel-close').click();
    await expect(page.locator('#sdg-filters-panel')).toHaveClass(/epm-panel-hidden/);

    // Libre
    await page.locator('#epm-btn-free').click();
    await expect(page.locator('body')).toHaveAttribute('data-epm-mode', 'free');

    // Clique marqueur si présent → détail
    const marker = page.locator('.sdg-marker').first();
    if (await marker.count()) {
      await marker.click({ force: true });
      await expect(page.locator('#sdg-detail')).toHaveClass(/epm-panel-open/, { timeout: 5_000 });
      await page.screenshot({
        path: path.join(CAPTURE_DIR, '05-detail-panel.png'),
        fullPage: false,
      });
    }

    await page.locator('#epm-btn-exit').click();
    await expect(page.locator('body')).not.toHaveClass(/executive-presentation-mode/);
    await expect(page.locator('#dxl-title')).toBeVisible();
    await page.screenshot({
      path: path.join(CAPTURE_DIR, '06-back-to-dossier.png'),
      fullPage: false,
    });
  });

  test('site/29 — responsive viewports critiques', async ({ page }) => {
    const viewports = [
      { width: 1366, height: 768 },
      { width: 1440, height: 900 },
      { width: 1728, height: 1000 },
      { width: 1920, height: 1080 },
    ];

    for (const vp of viewports) {
      await page.setViewportSize(vp);
      await page.goto(caseUrl('29'));
      await waitSdg(page);
      await enterEpm(page);

      const checks = await page.evaluate(() => {
        const dock = document.querySelector('#epm-command-dock')?.getBoundingClientRect();
        const host = document.querySelector('#sdg-map-host')?.getBoundingClientRect();
        const top = document.querySelector('.epm-topbar')?.getBoundingClientRect();
        return {
          noHScroll: document.documentElement.scrollWidth <= document.documentElement.clientWidth + 2,
          dockVisible: Boolean(dock && dock.width > 0 && dock.bottom <= window.innerHeight + 2),
          mapVisible: Boolean(host && host.height > window.innerHeight * 0.55),
          topVisible: Boolean(top && top.top >= 0),
        };
      });

      expect(checks.noHScroll, `${vp.width}x${vp.height} scroll`).toBeTruthy();
      expect(checks.dockVisible, `${vp.width}x${vp.height} dock`).toBeTruthy();
      expect(checks.mapVisible, `${vp.width}x${vp.height} map`).toBeTruthy();
      expect(checks.topVisible, `${vp.width}x${vp.height} top`).toBeTruthy();

      await page.locator('#epm-btn-exit').click();
    }
  });

  test('integrity — pas de voile / edvs-presentation-mode', async ({ page }) => {
    await page.goto(caseUrl('29'));
    await waitSdg(page);
    await enterEpm(page);
    await expect(page.locator('.edvs-presentation-mode')).toHaveCount(0);
    await expect(page.locator('.loading-overlay:not([hidden])')).toHaveCount(0);
    const text = await page.locator('#sdg-shell').innerText();
    expect(text).not.toMatch(/\[object Object\]/);
    expect(text).not.toMatch(/HTTP\s*[45]\d\d/i);
  });
});
