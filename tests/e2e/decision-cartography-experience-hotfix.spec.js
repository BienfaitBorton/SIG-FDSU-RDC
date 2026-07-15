// @ts-check
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

/**
 * Hotfix UX — panneau détail fermable + contribution explicable
 * Sites 14 / 16 / 26 / 29 / 34
 */

const SITES = ['14', '16', '26', '29', '34'];
const API = 'http://127.0.0.1:8001';
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
}

async function openDetailWithContent(page) {
  // Prefer site marker, then any marker
  const siteMarker = page.locator('.sdg-marker--site').first();
  if (await siteMarker.count()) {
    await siteMarker.click({ force: true });
  } else {
    await page.locator('.leaflet-marker-icon').first().click({ force: true });
  }
  await page.waitForTimeout(250);
  if (!(await page.locator('#sdg-detail.epm-panel-open').count())) {
    await page.locator('#epm-btn-detail').click();
  }
  await expect(page.locator('#sdg-detail')).toHaveClass(/epm-panel-open/, { timeout: 10_000 });
  // Si empty state, forcer un nœud via API UI publique (repaint not needed)
  const text = await page.locator('#sdg-detail').innerText();
  if (/Sélectionnez un nœud/i.test(text)) {
    await page.evaluate(() => {
      const SDG = window.SpatialDecisionGraph;
      const node = (SDG?.state?.graph?.nodes || []).find((n) => n.kind === 'site')
        || (SDG?.state?.graph?.nodes || [])[0];
      const edge = (SDG?.state?.graph?.edges || [])[0];
      if (node && SDG?.state?.nodeLayers?.[node.id]) {
        SDG.state.nodeLayers[node.id].fire('click');
      } else if (edge && SDG?.state?.edgeLayers?.[edge.id]) {
        SDG.state.edgeLayers[edge.id].fire('click');
      }
    });
    await page.waitForTimeout(200);
    if (!(await page.locator('#sdg-detail.epm-panel-open').count())) {
      await page.locator('#epm-btn-detail').click();
    }
  }
  await expect(page.locator('#sdg-detail [data-epm-close-panel="detail"]')).toBeVisible();
}

test.describe('Hotfix EPM — panneau détail + contribution', () => {
  test.beforeAll(() => {
    fs.mkdirSync(CAPTURE_DIR, { recursive: true });
  });

  test('contrat API — contribution_type explicite, jamais « non calculée »', async ({ request }) => {
    test.setTimeout(180_000);
    for (const id of SITES) {
      const res = await request.get(`${API}/api/spatial-decision-graph/site/${id}?program_code=sites_40`, {
        timeout: 60_000,
      });
      expect(res.ok(), `site ${id}`).toBeTruthy();
      const body = await res.json();
      for (const edge of body.edges || []) {
        const contrib = edge.score_contribution || edge.contribution || {};
        expect(contrib.contribution_type).toMatch(/direct|indirect|contextual_evidence|not_applicable|pending_rule/);
        expect(String(contrib.role_label || '')).toBeTruthy();
        expect(JSON.stringify(contrib).toLowerCase()).not.toContain('non calculée');
        if (contrib.contribution_type === 'direct') {
          expect(contrib.criterion || contrib.display).toBeTruthy();
        }
        if (contrib.status === 'unavailable') {
          expect(String(contrib.display || '')).not.toMatch(/^\+\d/);
        }
      }
    }
  });

  test('site/29 — fermeture ✕, ESC interne, réouverture dock, un Leaflet', async ({ page }) => {
    test.setTimeout(120_000);
    const pageErrors = [];
    page.on('pageerror', (e) => pageErrors.push(e.message));

    await page.goto(caseUrl('29'));
    await waitSdg(page);
    await enterEpm(page);
    await openDetailWithContent(page);

    await page.screenshot({ path: path.join(CAPTURE_DIR, 'hotfix-detail-open.png'), fullPage: false });

    const detailText = await page.locator('#sdg-detail').innerText();
    expect(detailText).toMatch(/Rôle dans la décision/i);
    expect(detailText.toLowerCase()).not.toContain('non calculée');
    expect(detailText).toMatch(/Contribution directe|Contribution indirecte|Preuve contextuelle|Non applicable|En attente/i);

    await page.screenshot({ path: path.join(CAPTURE_DIR, 'hotfix-contribution-role.png'), fullPage: false });

    // Fermer via ✕
    await page.locator('#sdg-detail [data-epm-close-panel="detail"]').click();
    await expect(page.locator('#sdg-detail')).toHaveClass(/epm-panel-hidden/);
    await page.screenshot({ path: path.join(CAPTURE_DIR, 'hotfix-detail-closed.png'), fullPage: false });

    // Rouvrir via dock
    await page.locator('#epm-btn-detail').click();
    await expect(page.locator('#sdg-detail')).toHaveClass(/epm-panel-open/);
    await page.screenshot({ path: path.join(CAPTURE_DIR, 'hotfix-detail-reopen.png'), fullPage: false });

    // ESC applicatif : ferme le panneau, reste en EPM (assertion atomique)
    const escResult = await page.evaluate(() => {
      const detail = document.querySelector('#sdg-detail');
      if (!detail) return { exists: false };
      detail.classList.remove('epm-panel-hidden');
      detail.classList.add('epm-panel-open');
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
      return {
        exists: Boolean(document.querySelector('#sdg-detail')),
        hidden: detail.classList.contains('epm-panel-hidden'),
        epm: document.body.classList.contains('executive-presentation-mode'),
        maps: document.querySelectorAll('.leaflet-container').length,
      };
    });
    expect(escResult.exists).toBeTruthy();
    expect(escResult.hidden).toBeTruthy();
    expect(escResult.epm).toBeTruthy();
    expect(escResult.maps).toBe(1);

    await page.evaluate(() => window.SigDecisionCartographyExperience?.exitPresentation?.());
    await expect(page.locator('body')).not.toHaveClass(/executive-presentation-mode/);

    expect(pageErrors.filter((m) => !/ResizeObserver|favicon/i.test(m))).toEqual([]);
  });

  for (const siteId of ['14', '16', '26', '34']) {
    test(`site/${siteId} — détail fermable + rôle décision`, async ({ page }) => {
      await page.goto(caseUrl(siteId));
      await waitSdg(page);
      await enterEpm(page);
      await openDetailWithContent(page);

      const text = await page.locator('#sdg-detail').innerText();
      expect(text.toLowerCase()).not.toContain('non calculée');
      expect(text).toMatch(/Rôle dans la décision/i);

      await page.locator('#sdg-detail [data-epm-close-panel="detail"]').click();
      await expect(page.locator('#sdg-detail')).toHaveClass(/epm-panel-hidden/);
      expect(await page.locator('.leaflet-container').count()).toBe(1);

      await page.locator('#epm-btn-guided').click();
      await page.waitForTimeout(300);
      await expect(page.locator('#sdg-detail')).toHaveClass(/epm-panel-hidden/);
      await page.locator('#epm-btn-exit').click();
    });
  }

  test('site/29 — détail calcul repliable si présent', async ({ page }) => {
    await page.goto(caseUrl('29'));
    await waitSdg(page);
    await enterEpm(page);
    await openDetailWithContent(page);

    const calc = page.locator('#sdg-detail .sdg-contrib-calc');
    if (await calc.count()) {
      await page.screenshot({ path: path.join(CAPTURE_DIR, 'hotfix-calc-collapsed.png'), fullPage: false });
      await calc.locator('summary').click();
      await expect(calc).toHaveAttribute('open', '');
      await page.screenshot({ path: path.join(CAPTURE_DIR, 'hotfix-calc-expanded.png'), fullPage: false });
    }
  });
});
