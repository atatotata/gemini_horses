const http = require('http');

function probe(model) {
  return new Promise((resolve) => {
    const postData = JSON.stringify({
      model: model,
      messages: [{ role: 'user', content: 'Say hi' }],
      max_tokens: 5,
    });
    const t0 = Date.now();
    const req = http.request(
      {
        hostname: 'localhost',
        port: 20128,
        path: '/v1/chat/completions',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer sk-ae42a2661869ce17-4433c6-9b6f4115',
          'Content-Length': Buffer.byteLength(postData),
        },
        timeout: 20000,
      },
      (res) => {
        let d = '';
        res.on('data', (c) => (d += c));
        res.on('end', () =>
          resolve({
            m: model,
            s: res.statusCode,
            ms: Date.now() - t0,
            b: d.slice(0, 200).replace(/\s+/g, ' '),
          })
        );
      }
    );
    req.on('error', (e) => resolve({ m: model, s: 'ERR', ms: Date.now() - t0, b: e.message }));
    req.on('timeout', () => {
      req.destroy();
      resolve({ m: model, s: 'TIMEOUT', ms: Date.now() - t0, b: '' });
    });
    req.write(postData);
    req.end();
  });
}

(async () => {
  const models = [
    'opencode-go/muse-spark-1.3-contributor',
    'opencode/muse-spark-1.3-contributor-free',
    'opencode-zen/muse-spark-1.3-contributor-free',
    'oc/muse-spark-1.3-contributor-free',
    'opencode-go/muse-spark-1.2-contributor',
    'opencode-go/muse-spark-1.2-contributor-high',
    'opencode-go/muse-spark-1.2-contributor-low',
    'opencode-go/muse-spark-1.2-contributor-xhigh',
    'opencode/muse-spark-1.2-contributor-free',
    'oc/muse-spark-1.2-contributor-free',
  ];

  for (const m of models) {
    const r = await probe(m);
    console.log(`${r.m} => ${r.s} (${r.ms}ms) | ${r.b}`);
  }
})();
