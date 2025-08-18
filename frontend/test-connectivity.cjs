/* Simple connectivity check for VO-Benchmark frontend-backend stack
 * Usage: node ./test-connectivity.cjs
 * Honors env: VITE_BACKEND_HOST, VITE_BACKEND_PORT
 */

const http = require('http');

function getEnv(name, def) { return process.env[name] || def; }
const host = getEnv('VITE_BACKEND_HOST', '127.0.0.1');
const port = parseInt(getEnv('VITE_BACKEND_PORT', '5000'), 10);
const base = `http://${host}:${port}/api/v1`;

function request(path) {
  return new Promise((resolve, reject) => {
    const req = http.request(`${base}${path}`, { method: 'GET', timeout: 15000 }, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: data }));
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(new Error('timeout')); });
    req.end();
  });
}

async function checkHealth() {
  const basic = await request('/health-doc/');
  const detailed = await request('/health-doc/detailed');
  return { basic, detailed };
}

async function checkConfig() {
  const res = await request('/config/client');
  return res;
}

async function checkSSE() {
  return new Promise((resolve, reject) => {
    const req = http.request(`${base}/events/`, {
      headers: { Accept: 'text/event-stream' },
      timeout: 20000,
    }, (res) => {
      let gotData = false;
      res.on('data', () => { gotData = true; });
      setTimeout(() => {
        resolve({ status: res.statusCode, gotData });
        req.destroy();
      }, 3000);
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(new Error('timeout')); });
    req.end();
  });
}

(async function main() {
  try {
    const health = await checkHealth();
    const config = await checkConfig();
    const sse = await checkSSE();
    const ok = (health.basic.status === 200) && (health.detailed.status === 200) && (config.status === 200) && (sse.status === 200);

    const result = {
      backend: `${host}:${port}`,
      health_basic: health.basic.status,
      health_detailed: health.detailed.status,
      config_client: config.status,
      sse_status: sse.status,
      sse_received_any_data_within_3s: sse.gotData,
      success: ok,
    };
    console.log(JSON.stringify(result, null, 2));
    process.exit(ok ? 0 : 1);
  } catch (e) {
    console.error('connectivity check failed:', e.message);
    process.exit(1);
  }
})();

