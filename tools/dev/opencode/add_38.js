const fs = require('fs');
const http = require('http');
const path = 'C:/Users/Ota/.config/opencode/opencode.jsonc';
const cfg = JSON.parse(fs.readFileSync(path, 'utf8'));
const models = cfg.provider['omniroute-antigravity'].models;
console.log('3.8 already configured:', Object.keys(models).filter((k) => k.includes('3.8')));
console.log('tiered template:', JSON.stringify(models['antigravity/gemini-3.7-flash-tiered']));
function probe(m) {
  return new Promise((res) => {
    const postData = JSON.stringify({ model: m, messages: [{ role: 'user', content: 'hi' }], max_tokens: 2 });
    const req = http.request(
      { hostname: 'localhost', port: 20128, path: '/v1/chat/completions', method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer sk-ae42a2661869ce17-4433c6-9b6f4115', 'Content-Length': Buffer.byteLength(postData) },
        timeout: 20000 },
      (r) => { let d = ''; r.on('data', (c) => (d += c)); r.on('end', () => res({ status: r.statusCode, body: d.slice(0, 120).replace(/\s+/g, ' ') })); }
    );
    req.on('error', (e) => res({ status: 'ERR', body: e.message.slice(0, 80) }));
    req.on('timeout', () => { req.destroy(); res({ status: 'TIMEOUT', body: '' }); });
    req.write(postData); req.end();
  });
}
(async () => {
  const id = 'antigravity/gemini-3.8-flash-tiered';
  const r = await probe(id);
  console.log('probe', id, '=>', r.status, '|', r.body);
  if (r.status === 200 && !models[id]) {
    fs.writeFileSync(path + '.bak.20260903_38', fs.readFileSync(path, 'utf8'));
    models[id] = {
      name: 'Gemini 3.8 Flash Tiered',
      attachment: true,
      limit: { context: 1048576, output: 65536 },
      modalities: { input: ['text', 'image', 'audio', 'video', 'pdf'], output: ['text'] },
    };
    fs.writeFileSync(path, JSON.stringify(cfg, null, 2));
    JSON.parse(fs.readFileSync(path, 'utf8'));
    console.log('Added + JSON valid. antigravity total:', Object.keys(models).length);
  } else if (models[id]) {
    console.log('Already configured, no change.');
  } else {
    console.log('NOT adding: probe did not return 200.');
  }
})();
