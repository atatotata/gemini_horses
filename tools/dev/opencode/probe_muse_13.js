const http = require('http');

function probe(model) {
  return new Promise((resolve) => {
    const postData = JSON.stringify({
      model: model,
      messages: [{ role: 'user', content: 'Say hi in one word' }],
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
        timeout: 25000,
      },
      (res) => {
        let data = '';
        res.on('data', (chunk) => {
          data += chunk;
        });
        res.on('end', () => {
          resolve({
            model,
            status: res.statusCode,
            ms: Date.now() - t0,
            body: data.slice(0, 400).replace(/\s+/g, ' '),
          });
        });
      }
    );
    req.on('error', (err) => {
      resolve({ model, status: 'ERR', ms: Date.now() - t0, body: err.message });
    });
    req.timeout = 25000;
    req.on('timeout', () => {
      req.destroy();
      resolve({ model, status: 'TIMEOUT', ms: Date.now() - t0, body: 'Request timed out' });
    });
    req.write(postData);
    req.end();
  });
}

(async () => {
  const candidates = [
    'opencode-go/muse-spark-1.3-contributor',
    'opencode/muse-spark-1.3-contributor-free',
    'opencode-zen/muse-spark-1.3-contributor-free',
    'oc/muse-spark-1.3-contributor-free',
    // also probe 1.2 counterparts for baseline comparison
    'opencode-go/muse-spark-1.2-contributor',
    'opencode/muse-spark-1.2-contributor-free',
  ];

  console.log('Probing Muse models via OmniRoute:');
  for (const m of candidates) {
    const res = await probe(m);
    console.log(res.model + ' => ' + res.status + ' (' + res.ms + 'ms) | ' + res.body);
  }
})();
