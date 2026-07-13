// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Cohérence des statuts SDG — Data First + No Black Box
 * Focus site 14 + contrôles multi-sites.
 */

const API = 'http://127.0.0.1:8001';

function caseUrl(siteId, program = 'sites_40') {
  return `/index.html#decision-case/site/${siteId}?program_code=${program}`;
}

test.describe('SDG domain status coherence', () => {
  test('API site 14 : plus d’anomalie FDSU, rayon affiché, messages métier', async ({ request }) => {
    const res = await request.get(`${API}/api/spatial-decision-graph/site/14?program_code=sites_40`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body._meta?.version).toMatch(/^sdg-2\.2/);

    const by = Object.fromEntries((body.categories || []).map((c) => [c.id, c]));
    expect(by.fdsu_sites?.maturity).not.toBe('anomaly');
    expect(String(by.fdsu_sites?.note || '')).not.toMatch(/Anomalie d[’']intégration/i);

    expect(by.telecom?.maturity).not.toBe('anomaly');
    if (Number(by.telecom?.count || 0) === 0) {
      expect(String(by.telecom?.note || '').length).toBeGreaterThan(10);
    }

    expect(by.roads?.maturity).not.toBe('anomaly');
    if (Number(by.roads?.count || 0) === 0) {
      expect(String(by.roads?.note || '').length).toBeGreaterThan(10);
    }

    const radius = (body.kpis || []).find((k) => k.id === 'radius');
    expect(radius?.value).not.toBeNull();
    expect(radius?.status).not.toBe('unavailable');
    expect(String(radius?.note || '')).toMatch(/Rayon|km/i);

    const shellText = JSON.stringify(body.categories);
    expect(shellText).not.toMatch(/\bNSME\b/);
    expect(shellText).not.toMatch(/ST_Within/);
    expect(shellText).not.toMatch(/integration anomaly/i);
    expect(Array.isArray(body.domain_statuses)).toBeTruthy();
  });

  test('UI dossier site 14 : filtres cohérents, pas de code interne', async ({ page }) => {
    /** @type {string[]} */
    const pageErrors = [];
    page.on('pageerror', (error) => pageErrors.push(error.message));
    page.on('console', (message) => {
      if (message.type() === 'error' && /Leaflet.*already initialized|Map container is being reused/i.test(message.text())) {
        pageErrors.push(message.text());
      }
    });

    await page.goto(caseUrl('14'));
    await expect(page.locator('#decision-experience-panel')).not.toHaveClass(/hidden/, { timeout: 45_000 });
    await expect(page.locator('#sdg-shell')).toBeVisible({ timeout: 60_000 });

    const filters = page.locator('#sdg-filters');
    await expect(filters).toBeVisible();
    const filterText = await filters.innerText();
    expect(filterText).not.toMatch(/Anomalie d[’']intégration/i);
    expect(filterText).not.toMatch(/\bNSME\b/);
    expect(filterText).not.toMatch(/\bST_Within\b/);
    expect(filterText).not.toMatch(/\bFK\b/);
    expect(filterText).toMatch(/Sites FDSU|Télécommunications|Routes|CCN/i);

    const kpis = page.locator('#sdg-kpis');
    await expect(kpis).toBeVisible();
    const kpiText = await kpis.innerText();
    expect(kpiText).toMatch(/Rayon|influence|15|km|m/i);
    // Un 0 télécom / routes doit être accompagné d'une note dans le panneau filtres
    expect(filterText.length).toBeGreaterThan(40);

    expect(pageErrors).toEqual([]);
  });
});
