const http = require('http');
const fs = require('fs');
const cfg = JSON.parse(fs.readFileSync('C:/Users/Ota/.config/opencode/opencode.jsonc', 'utf8'));
const configured = Object.keys(cfg.provider['omniroute-go'].models).sort();
function probe(m) {
  return new Promise((res) => {
    const postData = JSON.stringify({ model: m, messages: [{ role: 'user', content: 'hi' }], max_tokens: 2 });
    const req = http.request(
      { hostname: 'localhost', port: 20128, path: '/v1/chat/completions', method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer sk-ae42a2661869ce17-4433c6-9b6f4115', 'Content-Length': Buffer.byteLength(postData) },
        timeout: 15000 },
      (r) => { let d = ''; r.on('data', (c) => (d += c)); r.on('end', () => res({ m, status: r.statusCode, body: d.slice(0, 130).replace(/\s+/g, ' ') })); }
    );
    req.on('error', (e) => res({ m, status: 'ERR', body: e.message.slice(0, 100) }));
    req.on('timeout', () => { req.destroy(); res({ m, status: 'TIMEOUT', body: '' }); });
    req.write(postData); req.end();
  });
}
(async () => {
  const results = [];
  for (const m of configured) {
    const r = await probe(m);
    results.push(r);
    console.log(r.m, '=>', r.status, '|', r.body);
  }
  fs.writeFileSync('C:\\TMP\\opencode\\go_configured_probe.json', JSON.stringify(results, null, 1));
  const ok = results.filter((r) => r.status === 200);
  console.log('\n200 OK: ' + ok.length + '/' + results.length);
  console.log(ok.map((r) => r.m).join('\n'));
})();
