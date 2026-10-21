const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

function dashboardPath(testInfo) {
  return testInfo.project.name === 'mobile Chromium' ? './mobile.html' : './';
}

async function stubThirdParty(page) {
  await page.route('https://fonts.googleapis.com/**', (route) =>
    route.fulfill({ status: 200, contentType: 'text/css', body: '' }),
  );
  await page.route('https://fonts.gstatic.com/**', (route) => route.fulfill({ status: 204 }));
  await page.route('https://gc.zgo.at/**', (route) =>
    route.fulfill({ status: 200, contentType: 'application/javascript', body: '' }),
  );
}

test.beforeEach(async ({ page }) => {
  await stubThirdParty(page);
});

test('@smoke boots four KPIs and four charts without browser errors or overflow', async ({
  page,
}, testInfo) => {
  const browserErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') browserErrors.push(message.text());
  });
  page.on('pageerror', (error) => browserErrors.push(error.message));

  await page.goto(dashboardPath(testInfo));
  await expect(page.locator('.card')).toHaveCount(4);
  await expect(page.locator('.card strong')).toHaveCount(4);
  await expect(page.locator('.js-plotly-plot')).toHaveCount(4);
  await expect(page.locator('body')).not.toContainText(/R\$\s+(?:nan|inf)/i);

  const plotlySource = await page.locator('script[src$="plotly.min.js"]').getAttribute('src');
  expect(plotlySource).toBe('plotly.min.js');
  expect(new URL(plotlySource, page.url()).origin).toBe(new URL(page.url()).origin);

  const overflow = await page.evaluate(() =>
    Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
  );
  expect(overflow).toBeLessThanOrEqual(1);
  expect(browserErrors).toEqual([]);
});

test('reset acts only on the chart in its panel', async ({ page }, testInfo) => {
  await page.goto(dashboardPath(testInfo));
  await expect(page.locator('.js-plotly-plot')).toHaveCount(4);
  await page.evaluate(() => {
    window.__relayoutCalls = [];
    window.Plotly.relayout = (graph, update) => {
      window.__relayoutCalls.push({
        panel: [...document.querySelectorAll('.plotly-graph-div')].indexOf(graph),
        update,
      });
      return Promise.resolve();
    };
    window.Plotly.Plots.resize = () => {};
  });

  await page.locator('.panel').nth(1).getByRole('button', { name: 'Restablecer vista' }).click();

  await expect.poll(() => page.evaluate(() => window.__relayoutCalls)).toEqual([
    {
      panel: 1,
      update: { 'xaxis.autorange': true, 'yaxis.autorange': true },
    },
  ]);
});

test('reports a reset failure to the live status region', async ({ page }, testInfo) => {
  await page.goto(dashboardPath(testInfo));
  await expect(page.locator('.js-plotly-plot')).toHaveCount(4);
  await page.evaluate(() => {
    window.Plotly.relayout = () => Promise.reject(new Error('synthetic reset failure'));
  });

  await page.locator('.panel').first().getByRole('button', { name: 'Restablecer vista' }).click();

  await expect(page.locator('#dashboard-status')).toHaveText(
    'No se pudo restablecer la vista del gráfico.',
  );
  await expect(page.locator('#dashboard-status')).toHaveClass(/error/);
});

test('shows a useful fallback when the same-origin Plotly asset fails', async ({
  page,
}, testInfo) => {
  await page.route('**/plotly.min.js', (route) => route.abort('failed'));

  await page.goto(dashboardPath(testInfo));

  await expect(page.locator('#dashboard-status')).toHaveText(
    'No se pudieron cargar los gráficos. Recargá la página para volver a intentarlo.',
  );
  await expect(page.locator('#dashboard-status')).toHaveClass(/error/);
});

test('exposes the noscript fallback when JavaScript is disabled', async ({ browser }, testInfo) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();

  await page.goto(dashboardPath(testInfo));

  await expect(page.locator('noscript .dashboard-status')).toContainText(
    'Este tablero necesita JavaScript',
  );
  await context.close();
});

test('serves the checked-in 404 contract for an unknown route', async ({ page }) => {
  const response = await page.goto('./route-that-does-not-exist');

  expect(response.status()).toBe(404);
  await expect(page).toHaveTitle(/Página no encontrada/);
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex');
  await expect(page.getByRole('heading', { name: 'Página no encontrada.' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Volver al dashboard' })).toHaveAttribute(
    'href',
    'https://alexanderhuth98.github.io/analytics-clientes-ecommerce/',
  );
});

test('has no automatically detectable accessibility violations in the dashboard shell', async ({
  page,
}, testInfo) => {
  await page.goto(dashboardPath(testInfo));
  await expect(page.locator('.js-plotly-plot')).toHaveCount(4);

  const results = await new AxeBuilder({ page })
    .include('header')
    .include('.cards')
    .include('.panel-actions')
    .include('.note')
    .include('footer')
    .analyze();

  expect(results.violations).toEqual([]);
});
