// @ts-check
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
  timeout: 90_000,
  expect: { timeout: 15_000 },
  use: {
    baseURL: 'http://127.0.0.1:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'off',
    viewport: { width: 1440, height: 900 },
    locale: 'fr-FR',
  },
  projects: [
    {
      name: 'chromium-desktop',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: '.\\.venv\\Scripts\\python.exe -u dashboard\\serve_utf8.py --host 127.0.0.1 --port 8000',
      url: 'http://127.0.0.1:8000/healthz',
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command: '.\\.venv\\Scripts\\python.exe -u -m uvicorn api.main:app --host 127.0.0.1 --port 8001',
      url: 'http://127.0.0.1:8001/health',
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});
