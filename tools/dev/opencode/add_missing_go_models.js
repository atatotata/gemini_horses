const fs = require('fs');
const http = require('http');
const path = 'C:/Users/Ota/.config/opencode/opencode.jsonc';
const raw = fs.readFileSync(path, 'utf8');

// Backup
fs.writeFileSync(path + '.bak.20260903_go_full_sync', raw);
console.log('Backup created at', path + '.bak.20260903_go_full_sync');

const cfg = JSON.parse(raw);
const goModels = cfg.provider['omniroute-go'].models;

function titleize(id) {
  return id
    .replace(/^opencode-go\//, '')
    .split('-')
    .map((t) => (t.length ? t[0].toUpperCase() + t.slice(1) : t))
    .join(' ');
}

const template = () => ({
  attachment: true,
  limit: { context: 1048576, output: 65536 },
  modalities: { input: ['text', 'image'], output: ['text'] },
});

(async () => {
  const live = await new Promise((r) => {
    const req = http.request(
      { hostname: 'localhost', port: 20128, path: '/v1/models', method: 'GET', headers: { Authorization: 'Bearer sk-ae42a2661869ce17-4433c6-9b6f4115' } },
      (res) => { let d = ''; res.on('data', (c) => (d += c)); res.on('end', () => r(JSON.parse(d))); }
    );
    req.end();
  });

  const liveGo = live.data.filter((m) => m.id.startsWith('opencode-go/')).map((m) => m.id).sort();
  console.log('Live opencode-go total:', liveGo.length);

  let added = 0;
  for (const id of liveGo) {
    if (!goModels[id]) {
      goModels[id] = { name: titleize(id), ...template() };
      added++;
      console.log('Added:', id, '->', goModels[id].name);
    }
  }

  // Write updated file
  fs.writeFileSync(path, JSON.stringify(cfg, null, 2));
  console.log('\nAdded', added, 'models. Total omniroute-go models now:', Object.keys(goModels).length);

  // Validate parse
  JSON.parse(fs.readFileSync(path, 'utf8'));
  console.log('opencode.jsonc parsed successfully!');
})();
