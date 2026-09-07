const http = require('http');
const models = [
  'opencode-go/deepseek-v4-flash-low',
  'opencode-go/deepseek-v4-flash-none',
  'opencode-go/deepseek-v4-pro-none',
  'opencode-go/qwen3.7-max',
  'opencode-go/kimi-k2.6',
];
function probe(m) {
  return new Promise((res) => {
    const postData = JSON.stringify({ model: m, messages: [{ role: 'user', content: 'hi' }], max_tokens: 2 });
    const req = http.request(
      { hostname: 'localhost', port: 20128, path: '/v1/chat/completions', method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer sk-ae42a2661869ce17-4433c6-9b6f4115', 'Content-Length': Buffer.byteLength(postData) },
        timeout: 20000 },
      (r) => { let d = ''; r.on('data', (c) => (d += c)); r.on('end', () => res({ m, status: r.statusCode, body: d.slice(0, 130).replace(/\s+/g, ' ') })); }
    );
    req.on('error', (e) => res({ m, status: 'ERR', body: e.message.slice(0, 100) }));
    req.on('timeout', () => { req.destroy(); res({ m, status: 'TIMEOUT', body: '' }); });
    req.write(postData); req.end();
  });
}
(async () => {
  for (let round = 1; round <= 2; round++) {
    console.log('--- round ' + round + ' ---');
    for (const m of models) {
      const r = await probe(m);
      console.log(r.m, '=>', r.status, '|', r.body);
    }
  }
})();
