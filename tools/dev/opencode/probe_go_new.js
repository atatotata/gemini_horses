const http = require('http');
const added = [
  'opencode-go/deepseek-v4-flash-low',
  'opencode-go/deepseek-v4-flash-none',
  'opencode-go/deepseek-v4-pro-none',
  'opencode-go/gpt-5.6-luna',
  'opencode-go/gpt-5.6-luna-max',
  'opencode-go/grok-4.6',
  'opencode-go/hy3-none',
  'opencode-go/hy4-preview',
  'opencode-go/kimi-k3',
  'opencode-go/kimi-k3-max',
  'opencode-go/mimo-v2.5-max',
  'opencode-go/minimax-m2.7',
  'opencode-go/muse-spark-1.2',
  'opencode-go/muse-spark-1.2-contributor',
  'opencode-go/muse-spark-1.2-contributor-high',
  'opencode-go/muse-spark-1.2-contributor-low',
  'opencode-go/muse-spark-1.2-contributor-medium',
  'opencode-go/muse-spark-1.2-contributor-minimal',
  'opencode-go/muse-spark-1.2-contributor-xhigh',
  'opencode-go/muse-spark-1.3-contributor',
  'opencode-go/ox-alpha-free',
  'opencode-go/ox-alpha-free-high',
  'opencode-go/ox-alpha-free-low',
  'opencode-go/ox-alpha-free-max',
];
function probe(m) {
  return new Promise((res) => {
    const postData = JSON.stringify({ model: m, messages: [{ role: 'user', content: 'hi' }], max_tokens: 2 });
    const req = http.request(
      { hostname: 'localhost', port: 20128, path: '/v1/chat/completions', method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer sk-ae42a2661869ce17-4433c6-9b6f4115', 'Content-Length': Buffer.byteLength(postData) },
        timeout: 15000 },
      (r) => { let d = ''; r.on('data', (c) => (d += c)); r.on('end', () => res({ m, status: r.statusCode, body: d.slice(0, 150).replace(/\s+/g, ' ') })); }
    );
    req.on('error', (e) => res({ m, status: 'ERR', body: e.message.slice(0, 100) }));
    req.on('timeout', () => { req.destroy(); res({ m, status: 'TIMEOUT', body: '' }); });
    req.write(postData); req.end();
  });
}
(async () => {
  // also probe 2 already-configured controls
  for (const m of ['opencode-go/qwen3.7-max', ...added]) {
    const r = await probe(m);
    console.log(r.m, '=>', r.status, '|', r.body);
  }
})();
