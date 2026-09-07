const http = require('http');
function get(path) {
  return new Promise((r) => {
    const req = http.request(
      { hostname: 'localhost', port: 20128, path, method: 'GET', headers: { Authorization: 'Bearer sk-ae42a2661869ce17-4433c6-9b6f4115' } },
      (res) => { let d = ''; res.on('data', (c) => (d += c)); res.on('end', () => r({ status: res.statusCode, body: d })); }
    );
    req.on('error', (e) => r({ status: 'ERR', body: e.message }));
    req.end();
  });
}
function probe(m) {
  return new Promise((res) => {
    const postData = JSON.stringify({ model: m, messages: [{ role: 'user', content: 'hi' }], max_tokens: 2 });
    const req = http.request(
      { hostname: 'localhost', port: 20128, path: '/v1/chat/completions', method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer sk-ae42a2661869ce17-4433c6-9b6f4115', 'Content-Length': Buffer.byteLength(postData) },
        timeout: 25000 },
      (r) => { let d = ''; r.on('data', (c) => (d += c)); r.on('end', () => res({ status: r.statusCode, body: d.slice(0, 300).replace(/\s+/g, ' ') })); }
    );
    req.on('error', (e) => res({ status: 'ERR', body: e.message.slice(0, 120) }));
    req.on('timeout', () => { req.destroy(); res({ status: 'TIMEOUT', body: '' }); });
    req.write(postData); req.end();
  });
}
(async () => {
  const models = await get('/v1/models');
  console.log('GET /v1/models =>', models.status, 'bytes:', models.body.length);
  try {
    const j = JSON.parse(models.body);
    for (const m of j.data) {
      if (m.id === 'antigravity/gemini-3-flash' || m.id === 'antigravity/antigravity/gemini-3.7-flash-tiered') {
        console.log('--- ' + m.id + ' ---');
        console.log(JSON.stringify(m, null, 1));
      }
    }
  } catch (e) { console.log('models parse fail:', e.message, models.body.slice(0, 200)); }

  for (const id of ['antigravity/gemini-3-flash', 'antigravity/antigravity/gemini-3.7-flash-tiered', 'antigravity/gemini-3.7-flash-tiered']) {
    const r = await probe(id);
    console.log('probe', id, '=>', r.status, '|', r.body);
  }
})();
