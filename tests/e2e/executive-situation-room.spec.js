// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Executive Situation Room v1.0
 * Briefing, alertes, questions, carte, scénarios, actions, présentation,
 * aucune erreur JS, une seule instance Leaflet (TST).
 */

const ESR_URL = '/index.html#salle-pilotage';
const API = 'http://127.0.0.1:8001';

function attachDiag(page) {
  /** @type {string[]} */
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error' && /Map container is being reused|already initialized/i.test(message.text())) {
      pageErrors.push(message.text());
    }
  });
  return { pageErrors };
}

test.describe('Executive Situation Room v1.0', () => {
  test('API situation-room disponible', async ({ request }) => {
    const briefing = await request.get(`${API}/api/executive/situation-room/briefing`);
    expect(briefing.ok()).toBeTruthy();
    const body = await briefing.json();
    expect(body.headline || body.narrative).toBeTruthy();

    const room = await request.get(`${API}/api/executive/situation-room`);
    expect(room.ok()).toBeTruthy();
    const full = await room.json();
    expect(full.briefing).toBeTruthy();
    expect(full.alerts).toBeTruthy();
    expect(full.questions?.questions?.length).toBeGreaterThan(0);
    expect(full.presentation?.steps?.length).toBeGreaterThan(0);
  });

  test('salle DG : briefing, situation, alertes, questions, actions', async ({ page }) => {
    const diag = attachDiag(page);
    await page.goto(ESR_URL);

    await expect(page.locator('#salle-pilotage-panel')).not.toHaveClass(/hidden/, { timeout: 30_000 });
    await expect(page.locator('.esr-root')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('#esr-briefing-host')).toBeVisible({ timeout: 30_000 });
    // Attendre le contenu réel du briefing (section ou erreur soft avec ancre)
    await expect(page.locator('#esr-briefing')).toBeVisible({ timeout: 90_000 });
    await expect(page.locator('#esr-briefing-host')).toContainText(/Briefing|recommande|Situation|Facteurs|Indisponible|population|territoire/i, {
      timeout: 90_000,
    });
    await expect(page.locator('#esr-national')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('#esr-alerts')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('#esr-questions')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('#esr-actions')).toBeVisible({ timeout: 60_000 });

    // Carte TST centrale
    await expect(page.locator('#edvs-tst-host')).toBeVisible({ timeout: 60_000 });
    // Pas de double Leaflet legacy
    expect(await page.locator('#edvs-cockpit-map').count()).toBe(0);
    const leafletMaps = await page.locator('#salle-pilotage-panel .leaflet-container').count();
    expect(leafletMaps).toBeLessThanOrEqual(1);

    // Explicabilité — bouton Pourquoi du briefing (si section complète)
    const whyBtn = page.locator('#esr-briefing [data-esr-why], #esr-briefing-host [data-esr-why]').first();
    if (await whyBtn.count()) {
      await whyBtn.click();
      await expect(page.locator('#esr-explain-drawer')).toBeVisible();
      await page.locator('#esr-explain-drawer [data-esr-close-explain]').click();
    }

    expect(diag.pageErrors.filter((e) => !/favicon|net::ERR/i.test(e))).toEqual([]);
  });

  test('scénarios et questions naviguent', async ({ page }) => {
    await page.goto(ESR_URL);
    await expect(page.locator('#esr-questions')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('#esr-scenarios')).toBeVisible({ timeout: 90_000 });

    const question = page.locator('#esr-questions .esr-question').first();
    if (await question.count()) {
      await question.click();
      await expect.poll(() => page.url()).toMatch(/decision-scenario|decision-view|salle-pilotage/);
    }
  });

  test('mode Présenter au DG + interruption', async ({ page }) => {
    const diag = attachDiag(page);
    await page.goto(ESR_URL);
    await expect(page.locator('[data-esr-action="start_presentation"]')).toBeVisible({ timeout: 60_000 });

    await page.locator('[data-esr-action="start_presentation"]').first().click();
    await expect(page.locator('#esr-stop-present')).toBeVisible({ timeout: 5_000 });
    await expect(page.locator('#esr-step-label')).not.toHaveText('', { timeout: 5_000 });

    await page.locator('#esr-stop-present').click();
    await expect(page.locator('#esr-stop-present')).toBeHidden({ timeout: 5_000 });

    expect(diag.pageErrors.filter((e) => !/favicon|net::ERR/i.test(e))).toEqual([]);
  });

  test('mission masquée si capacité absente', async ({ page }) => {
    await page.goto(ESR_URL);
    await expect(page.locator('#esr-actions')).toBeVisible({ timeout: 60_000 });
    const mission = page.locator('#esr-actions [data-capability="mission_planning"]');
    if (await mission.count()) {
      await expect(mission).toBeHidden();
    }
  });
});
