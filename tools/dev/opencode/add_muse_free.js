const fs = require('fs');
const path = 'C:/Users/Ota/.config/opencode/opencode.jsonc';
const raw = fs.readFileSync(path, 'utf8');
fs.writeFileSync(path + '.bak.20260903_muse_free', raw);
console.log('Backup created');
const cfg = JSON.parse(raw);
const models = cfg.provider['omniroute-go'].models;
const template = () => ({
  attachment: true,
  limit: { context: 1048576, output: 65536 },
  modalities: { input: ['text', 'image'], output: ['text'] },
});
const toAdd = {
  'opencode/muse-spark-1.2-contributor-free': 'Muse Spark 1.2 Contributor Free',
  'opencode/muse-spark-1.3-contributor-free': 'Muse Spark 1.3 Contributor Free',
  'opencode-zen/muse-spark-1.3-contributor-free': 'Muse Spark 1.3 Contributor Free (Zen)',
  'oc/muse-spark-1.2-contributor-free': 'Muse Spark 1.2 Contributor Free (OC)',
  'oc/muse-spark-1.3-contributor-free': 'Muse Spark 1.3 Contributor Free (OC)',
};
let added = 0;
for (const [id, name] of Object.entries(toAdd)) {
  if (!models[id]) {
    models[id] = { name, ...template() };
    added++;
    console.log('Added:', id, '->', name);
  } else {
    console.log('Already present:', id);
  }
}
fs.writeFileSync(path, JSON.stringify(cfg, null, 2));
JSON.parse(fs.readFileSync(path, 'utf8'));
console.log('Added ' + added + '. omniroute-go total:', Object.keys(models).length, '| JSON valid');
