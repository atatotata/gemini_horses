const http = require('http');
const ids = [
  'opencode/muse-spark-1.2-contributor-free',
  'opencode/muse-spark-1.3-contributor-free',
  'opencode-zen/muse-spark-1.3-contributor-free',
  'oc/muse-spark-1.2-contributor-free',
  'oc/muse-spark-1.3-contributor-free',
];
function probe(m) {
  return new Promise((res) => {
    const t0 = Date.now();
    const postData = JSON.stringify({ model: m, messages: [{ role: 'user', content: 'hi' }], max_tokens: 2 });
    const req = http.request(
      { hostname: 'localhost', port: 20128, path: '/v1/chat/completions', method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer sk-ae42a2661869ce17-4433c6-9b6f4115', 'Content-Length': Buffer.byteLength(postData) },
        timeout: 30000 },
      (r) => { let d = ''; r.on('data', (c) => (d += c)); r.on('end', () => res({ status: r.statusCode, ms: Date.now() - t0, body: d.slice(0, 160).replace(/\s+/g, ' ') })); }
    );
    req.on('error', (e) => res({ status: 'ERR', ms: Date.now() - t0, body: e.message.slice(0, 100) }));
    req.on('timeout', () => { req.destroy(); res({ status: 'TIMEOUT', ms: Date.now() - t0, body: '' }); });
    req.write(postData); req.end();
  });
}
(async () => {
  for (const id of ids) {
    const r = await probe(id);
    console.log(id, '=>', r.status, '(' + r.ms + 'ms) |', r.body);
  }
})();
