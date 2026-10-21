const { defineConfig, devices } = require('@playwright/test');

const externalBaseURL = process.env.E2E_BASE_URL;

module.exports = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [
    ['line'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  outputDir: 'test-results',
  use: {
    baseURL: externalBaseURL || 'http://127.0.0.1:43117/',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'off',
  },
  webServer: externalBaseURL
    ? undefined
    : {
        command: 'python tests/e2e/server.py --port 43117',
        url: 'http://127.0.0.1:43117/',
        reuseExistingServer: false,
        timeout: 30_000,
      },
  projects: [
    {
      name: 'desktop Chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile Chromium',
      use: { ...devices['Pixel 7'] },
    },
  ],
});
