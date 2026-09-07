const fs = require('fs');
const path = 'C:/Users/Ota/.config/opencode/opencode.jsonc';
const raw = fs.readFileSync(path, 'utf8');
fs.writeFileSync(path + '.bak.20260903_go-sync', raw);
console.log('Backup created');
const cfg = JSON.parse(raw);
const models = cfg.provider['omniroute-go'].models;

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
const toAdd = [
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
let added = 0;
for (const id of toAdd) {
  if (!models[id]) {
    models[id] = { name: titleize(id), ...template() };
    added++;
    console.log('Added', id, 'as', models[id].name);
  } else {
    console.log('Already present', id);
  }
}
fs.writeFileSync(path, JSON.stringify(cfg, null, 2));
console.log('Added ' + added + ' models. Total omniroute-go: ' + Object.keys(models).length);
JSON.parse(fs.readFileSync(path, 'utf8'));
console.log('JSON valid');
