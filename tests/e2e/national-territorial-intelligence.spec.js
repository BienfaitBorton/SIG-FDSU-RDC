// @ts-check
const { test, expect } = require('@playwright/test');

const API = 'http://127.0.0.1:8011';

test.describe('National Territorial Intelligence Engine v1', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => { window.__API_BASE_URL__ = 'http://127.0.0.1:8011'; });
  });

  test('API valide tous les niveaux administratifs reels', async ({ request }) => {
    const refs = ['PROVINCE-9', 'TERRITOIRE-05-002', 'SECTEUR-3', 'CHEFFERIE-1', 'COLLECTIVITE-326', 'GROUPEMENT-1', 'LOCALITE-64'];
    for (const ref of refs) {
      const response = await request.get(`${API}/territorial-profile/${ref}`);
      expect(response.ok(), ref).toBeTruthy();
      const profile = await response.json();
      expect(profile._meta.data_first).toBe(true);
      expect(profile.indicators).toHaveLength(23);
      expect(profile.indicators.every((item) => Object.hasOwn(item, 'source') && Object.hasOwn(item, 'method'))).toBe(true);
    }
  });

  test('API expose score, population, couverture et explicabilite', async ({ request }) => {
    for (const suffix of ['score', 'population', 'coverage', 'explainability', 'evolution']) {
      const response = await request.get(`${API}/territorial-profile/TERRITOIRE-05-002/${suffix}`);
      expect(response.ok(), suffix).toBeTruthy();
    }
    const score = await (await request.get(`${API}/territorial-profile/TERRITOIRE-05-002/score`)).json();
    expect(score.score.label).toBe('Score indicatif');
    expect(score.score.value).toBeNull();
    expect(score.score.confidence_limited).toBe(true);
  });

  test('dashboard affiche profil, evolution, qualite, carte et explicabilite', async ({ page }) => {
    await page.goto('/index.html#national-territorial-intelligence');
    await expect(page.locator('#national-territorial-intelligence-panel')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('#ntie-kpis .ntie-kpi')).toHaveCount(6, { timeout: 60_000 });
    await expect(page.locator('#ntie-status')).toContainText(/Territoire.*DUNGU/i);
    await expect(page.locator('#ntie-score')).toContainText('Score indicatif');
    await expect(page.locator('#ntie-evolution')).toContainText('Apres 20 476 sites');
    await expect(page.locator('#ntie-quality')).toContainText('indicateurs disponibles');
    await expect(page.locator('#ntie-map')).toContainText('Geometrie territoriale disponible');
    await expect(page.locator('#ntie-explainability')).toContainText('National Asset Registry');
    const text = await page.locator('#national-territorial-intelligence-panel').innerText();
    expect(text).not.toMatch(/undefined|NaN|\[object Object\]/);
  });
});
