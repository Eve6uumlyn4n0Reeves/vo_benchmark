import { test, expect } from '@playwright/test';

const FRONTEND = process.env.FRONTEND_URL || 'http://127.0.0.1:3000';
const BACKEND = `http://${process.env.VITE_BACKEND_HOST || '127.0.0.1'}:${process.env.VITE_BACKEND_PORT || '5000'}`;

// Minimal smoke covering connectivity, health, SSE, and manifest/arrow path

test.describe('Connectivity and health', () => {
  test('health page renders and backend health is OK', async ({ page }) => {
    await page.goto(FRONTEND + '/health');
    const res = await page.request.get(BACKEND + '/api/v1/health-doc/');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(['healthy','degraded']).toContain(body.status);
  });
});

test.describe('SSE events', () => {
  test('SSE can connect and receive at least one message or heartbeat', async ({ page }) => {
    await page.goto(FRONTEND + '/tasks');
    // Hook into EventSource by evaluating in the page context
    const got = await page.evaluate(async () => {
      return await new Promise<boolean>((resolve) => {
        const es = new EventSource('/api/v1/events/');
        let done = false;
        const finish = (ok: boolean) => { if (!done) { done = true; es.close(); resolve(ok); } };
        es.onmessage = () => finish(true);
        es.addEventListener('heartbeat', () => finish(true));
        es.onerror = () => finish(false);
        // Heartbeat interval is ~15s server-side; wait 20s to allow one beat
        setTimeout(() => finish(false), 20000);
      });
    });
    expect(got).toBeTruthy();
  });
});

test.describe('Arrow worker parsing', () => {
  test('PR curve load falls back or loads via Arrow without external CDN', async ({ page }) => {
    // Navigate to results page; the app may attempt to load results
    await page.goto(FRONTEND + '/results');
    // Ensure the arrow worker file is in the build (dev will lazy compile)
    // We just assert no console error about Arrow CDN
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });
    await page.waitForTimeout(500);
    expect(errors.join('\n')).not.toMatch(/apache-arrow@|cdn\.skypack|unpkg\.com/i);
  });
});

