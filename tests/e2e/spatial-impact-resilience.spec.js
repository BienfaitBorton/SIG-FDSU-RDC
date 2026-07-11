// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Spatial Impact Resilience
 * — Explain KO / lent ne doit jamais vider toute la vue
 * — panneau État des services visible
 * — aucun /api/ dans l'URL navigateur
 */

const SPATIAL_IMPACT_URL = '/index.html#spatial-impact/site/11';

function attachDiag(page) {
  /** @type {string[]} */
  const pageErrors = [];
  /** @type {string[]} */
  const rejections = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (message) => {
    const text = message.text();
    if (message.type() === 'error' && /unhandled|rejection/i.test(text)) {
      rejections.push(text);
    }
  });
  page.addInitScript(() => {
    window.addEventListener('unhandledrejection', (event) => {
      const reason = event.reason?.message || String(event.reason || 'unknown');
      console.error('UnhandledRejection:', reason);
      window.__dxlUnhandled = window.__dxlUnhandled || [];
      window.__dxlUnhandled.push(reason);
    });
  });
  return { pageErrors, rejections };
}

test.describe('Spatial Impact Resilience', () => {
  test('vue spatial-impact charge sans écran vide (asset 11)', async ({ page }) => {
    const diag = attachDiag(page);
    await page.goto(SPATIAL_IMPACT_URL);

    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#dxl-section-services')).toBeVisible({ timeout: 30_000 });
    await expect(page.locator('#dxl-services-list li')).not.toHaveCount(0);

    // Les panneaux métier restent présents (pas d'écran unique Failed to fetch)
    await expect(page.locator('#dxl-section-summary')).toBeVisible();
    await expect(page.locator('#dxl-map')).toBeVisible();
    await expect(page.locator('#dxl-section-impact')).toBeVisible();
    await expect(page.locator('#dxl-section-context')).toBeVisible();
    await expect(page.locator('#dxl-section-why')).toBeVisible();

    await expect(page.locator('#dxl-status')).not.toHaveText(/Impact spatial indisponible : Failed to fetch/i, {
      timeout: 45_000,
    });

    // Attendre stabilisation (explain peut timeout ~12s)
    await page.waitForFunction(
      () => {
        const items = [...document.querySelectorAll('#dxl-services-list li')];
        if (!items.length) return false;
        return items.every((li) => li.getAttribute('data-status') !== 'loading');
      },
      null,
      { timeout: 60_000 },
    );

    // Impact / Needs / Carte / Stats ne doivent pas tous être en erreur si API OK
    const statuses = await page.evaluate(() => {
      const out = {};
      document.querySelectorAll('#dxl-services-list li').forEach((li) => {
        out[li.getAttribute('data-service')] = li.getAttribute('data-status');
      });
      return out;
    });

    // Au moins un service critique chargé, ou message partiel métier (pas blank)
    const criticalOk = ['impact', 'needs', 'map', 'statistics'].filter((k) => statuses[k] === 'loaded');
    const bodyText = await page.locator('#decision-experience-panel').innerText();
    expect(bodyText).not.toMatch(/^Impact spatial indisponible : Failed to fetch$/);
    expect(criticalOk.length + (statuses.explain === 'error' || statuses.explain === 'loaded' ? 1 : 0)).toBeGreaterThan(0);

    // Spinner / loading class cleared
    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/is-loading/);

    const unhandled = await page.evaluate(() => window.__dxlUnhandled || []);
    expect(unhandled).toEqual([]);
    expect(diag.pageErrors.filter((e) => !/favicon|net::err/i.test(e))).toEqual([]);

    await page.screenshot({ path: 'test-results/spatial-impact-resilience-11.png', fullPage: true });
  });

  test('Explain KO simulé ne vide pas Impact / Needs / Carte', async ({ page }) => {
    const diag = attachDiag(page);

    await page.route('**/api/spatial-matching/assets/*/explain**', async (route) => {
      await new Promise((r) => setTimeout(r, 15_000));
      await route.abort('timedout');
    });

    await page.goto(SPATIAL_IMPACT_URL);
    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });

    // Dès qu'impact ou needs répond, les panneaux doivent se remplir (progressif)
    await page.waitForFunction(
      () => {
        const impact = document.querySelector('#dxl-services-list li[data-service="impact"]');
        const needs = document.querySelector('#dxl-services-list li[data-service="needs"]');
        return impact?.getAttribute('data-status') === 'loaded'
          || needs?.getAttribute('data-status') === 'loaded';
      },
      null,
      { timeout: 30_000 },
    );

    const impactText = await page.locator('#dxl-section-impact').innerText();
    expect(impactText).not.toMatch(/Failed to fetch/i);

    // Explain finira en erreur métier, sans écraser le reste
    await page.waitForFunction(
      () => document.querySelector('#dxl-services-list li[data-service="explain"]')?.getAttribute('data-status') === 'error',
      null,
      { timeout: 45_000 },
    );

    await expect(page.locator('#dxl-section-why')).toContainText(/Analyse explicative indisponible|données d’impact restent consultables/i);
    await expect(page.locator('#dxl-section-summary')).toBeVisible();
    await expect(page.locator('#dxl-map')).toBeVisible();
    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/is-loading/);

    const unhandled = await page.evaluate(() => window.__dxlUnhandled || []);
    expect(unhandled).toEqual([]);
    expect(diag.pageErrors.filter((e) => !/favicon|net::err|aborted/i.test(e))).toEqual([]);

    await page.screenshot({ path: 'test-results/spatial-impact-explain-ko.png', fullPage: true });
  });

  test('API totalement coupée : messages métier, pas Failed to fetch seul', async ({ page }) => {
    attachDiag(page);
    await page.route('**/api/spatial-matching/**', (route) => route.abort('failed'));
    await page.route('**/api/decision/**', (route) => route.abort('failed'));

    await page.goto(SPATIAL_IMPACT_URL);
    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });

    await page.waitForFunction(
      () => {
        const items = [...document.querySelectorAll('#dxl-services-list li')];
        return items.length > 0 && items.every((li) => li.getAttribute('data-status') !== 'loading');
      },
      null,
      { timeout: 45_000 },
    );

    const status = await page.locator('#dxl-status').innerText();
    expect(status).not.toBe('Impact spatial indisponible : Failed to fetch');
    expect(status.length).toBeGreaterThan(10);

    const panel = await page.locator('#decision-experience-panel').innerText();
    expect(panel).toMatch(/indisponible|Connexion impossible|n’a pas répondu|joignable/i);
    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/is-loading/);
    await expect(page.locator('#dxl-actions')).toBeVisible();
  });
});
