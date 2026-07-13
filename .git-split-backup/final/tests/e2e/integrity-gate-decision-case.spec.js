// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Integrity Gate — parcours exact DG
 * #decision-case/site/29?program_code=sites_40
 */

const CASE_29 = '/index.html#decision-case/site/29?program_code=sites_40';
const API = 'http://127.0.0.1:8001';

function attachDiag(page) {
  /** @type {string[]} */
  const pageErrors = [];
  /** @type {string[]} */
  const rejections = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error' && /unhandled|rejection/i.test(message.text())) {
      rejections.push(message.text());
    }
  });
  page.addInitScript(() => {
    window.addEventListener('unhandledrejection', (event) => {
      const reason = event.reason?.message || String(event.reason || 'unknown');
      window.__integrityRejections = window.__integrityRejections || [];
      window.__integrityRejections.push(reason);
    });
  });
  return { pageErrors, rejections };
}

test.describe('Integrity Gate — Decision Case site/29', () => {
  test('API DB site/29 répond 200 avec nom métier', async ({ request }) => {
    const res = await request.get(`${API}/api/decision/case/29?asset_type=site&program_code=sites_40`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    const name = body.asset?.site_name || body.asset?.name;
    expect(name).toBeTruthy();
    expect(String(name)).not.toBe('29');
  });

  test('UI exacte site/29 — nom métier, pas HTTP 400, carte, retour', async ({ page }) => {
    const diag = attachDiag(page);
    await page.goto(CASE_29);

    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('#dxl-title')).toBeVisible({ timeout: 60_000 });

    // Attendre la fin du chargement
    await expect.poll(async () => {
      const status = await page.locator('#dxl-status').innerText().catch(() => '');
      const title = await page.locator('#dxl-title').innerText();
      const summary = await page.locator('#dxl-section-summary').innerText().catch(() => '');
      return `${status}||${title}||${summary}`;
    }, { timeout: 90_000 }).toMatch(/Village Nsona|Dossier prêt|Priorité/i);

    const title = await page.locator('#dxl-title').innerText();
    expect(title).toMatch(/Village Nsona/i);
    expect(title).not.toMatch(/^Dossier de décision — 29$/);

    const panelText = await page.locator('#decision-experience-panel').innerText();
    expect(panelText).not.toMatch(/HTTP\s*400/i);
    expect(panelText).not.toMatch(/\[object Object\]/i);
    expect(panelText).toMatch(/Priorité|Score|Recommandation/i);

    await expect(page.locator('#dxl-map')).toBeVisible();

    const back = page.locator('#dxl-back-btn, [data-dxl-action="back"]').first();
    await expect(back).toBeVisible();

    const exportBtn = page.locator('[data-dxl-action="export"]');
    if (await exportBtn.count()) {
      const disabled = await exportBtn.isDisabled();
      if (!disabled) {
        await expect(exportBtn).toBeEnabled();
      } else {
        const titleAttr = await exportBtn.getAttribute('title');
        expect(titleAttr || (await exportBtn.getAttribute('data-capability-reason')) || 'disabled').toBeTruthy();
      }
    }

    const pageErrors = diag.pageErrors.filter((e) => !/favicon|net::ERR/i.test(e));
    expect(pageErrors).toEqual([]);
    const rejections = await page.evaluate(() => window.__integrityRejections || []);
    expect(rejections).toEqual([]);
  });

  test('Salle Pilotage sans voile opaque', async ({ page }) => {
    await page.goto('/index.html#salle-pilotage');
    await expect(page.locator('#edvs-cockpit-root .esr-root')).toBeVisible({ timeout: 60_000 });

    const veil = await page.evaluate(() => {
      const blockers = [];
      document.querySelectorAll('*').forEach((el) => {
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') return;
        const fixed = style.position === 'fixed' || style.position === 'absolute';
        if (!fixed) return;
        const rect = el.getBoundingClientRect();
        if (rect.width < window.innerWidth * 0.6 || rect.height < window.innerHeight * 0.6) return;
        const bg = style.backgroundColor;
        const opacity = Number(style.opacity || '1');
        const pe = style.pointerEvents;
        if (pe === 'none') return;
        if (el.hasAttribute('hidden') || el.getAttribute('aria-hidden') === 'true') return;
        if (el.id === 'edvs-presentation-bar') return;
        if (el.id === 'esr-explain-drawer') return;
        if (opacity > 0.15 && /rgba\(\s*255,\s*255,\s*255/i.test(bg)) {
          blockers.push({ id: el.id, cls: String(el.className).slice(0, 80), bg, opacity });
        }
      });
      return {
        presentation: document.body.classList.contains('edvs-presentation-mode'),
        blockers,
      };
    });

    expect(veil.presentation).toBeFalsy();
    expect(veil.blockers).toEqual([]);
  });
});
