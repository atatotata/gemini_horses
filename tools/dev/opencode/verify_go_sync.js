const fs = require('fs');
const http = require('http');
const cfg = JSON.parse(fs.readFileSync('C:/Users/Ota/.config/opencode/opencode.jsonc', 'utf8'));
const goKeys = Object.keys(cfg.provider['omniroute-go'].models).sort();
console.log('Configured omniroute-go: ' + goKeys.length);
console.log('Default model: ' + cfg.model + ' | Small model: ' + cfg.small_model);
console.log('Default in config: ' + (goKeys.includes(cfg.model) ? 'YES' : 'NO'));
(async () => {
const live = await new Promise((r) => {
  const req = http.request(
    { hostname: 'localhost', port: 20128, path: '/v1/models', method: 'GET', headers: { Authorization: 'Bearer sk-ae42a2661869ce17-4433c6-9b6f4115' } },
    (res) => { let d = ''; res.on('data', (c) => (d += c)); res.on('end', () => r(JSON.parse(d))); }
  );
  req.end();
});
const liveGo = new Set(live.data.filter((m) => m.id.startsWith('opencode-go/')).map((m) => m.id));
const missing = goKeys.filter((k) => !liveGo.has(k));
const unconfigured = [...liveGo].filter((k) => !goKeys.includes(k));
console.log('Live opencode-go: ' + liveGo.size);
console.log('Configured-not-live (stale): ' + JSON.stringify(missing));
console.log('Live-not-configured: ' + JSON.stringify(unconfigured));
console.log('SYNC: ' + (missing.length === 0 && unconfigured.length === 0 ? 'COMPLETE' : 'INCOMPLETE'));
})();
