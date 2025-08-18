/* Extended connectivity check: health, config, CORS, SSE (20s heartbeat), docs */
const http = require('http');

const host = process.env.VITE_BACKEND_HOST || '127.0.0.1';
const port = parseInt(process.env.VITE_BACKEND_PORT || '5000', 10);
const base = `http://${host}:${port}`;

function request(path, headers = {}) {
  return new Promise((resolve, reject) => {
    const req = http.request(`${base}${path}`, { method: 'GET', timeout: 20000, headers }, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: data }));
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(new Error('timeout')); });
    req.end();
  });
}

async function checkCors() {
  const origin = 'http://127.0.0.1:3000';
  const res = await request('/api/v1/health-doc/', { Origin: origin });
  const allow = res.headers['access-control-allow-origin'] || '';
  return { status: res.status, allow_origin: allow };
}

async function checkSSE20s() {
  return new Promise((resolve, reject) => {
    const req = http.request(`${base}/api/v1/events/`, {
      headers: { Accept: 'text/event-stream' },
      timeout: 25000,
      method: 'GET',
    }, (res) => {
      let gotAny = false;
      let gotHeartbeat = false;
      let buffer = '';
      res.setEncoding('utf8');
      res.on('data', (chunk) => {
        gotAny = true;
        buffer += chunk;
        if (buffer.includes('event: heartbeat')) gotHeartbeat = true;
      });
      setTimeout(() => {
        resolve({ status: res.statusCode, gotAny, gotHeartbeat });
        try { req.destroy(); } catch (_) {}
      }, 20000);
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(new Error('timeout')); });
    req.end();
  });
}

(async function main(){
  try {
    const health = await request('/api/v1/health-doc/');
    const detailed = await request('/api/v1/health-doc/detailed');
    const config = await request('/api/v1/config/client');
    const docs = await request('/api/v1/docs/');
    const cors = await checkCors();
    const sse = await checkSSE20s();

    const result = {
      backend: `${host}:${port}`,
      health_basic: health.status,
      health_detailed: detailed.status,
      config_client: config.status,
      docs_status: docs.status,
      cors_allow_origin: cors.allow_origin || null,
      sse_status: sse.status,
      sse_any_data_within_20s: sse.gotAny,
      sse_heartbeat_within_20s: sse.gotHeartbeat,
      success: [health.status, detailed.status, config.status, docs.status, sse.status].every(s => s === 200)
    };
    console.log(JSON.stringify(result, null, 2));
    process.exit(result.success ? 0 : 1);
  } catch (e) {
    console.error('extended connectivity check failed:', e.message);
    process.exit(1);
  }
})();

