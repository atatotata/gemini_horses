const fs = require('fs');
const raw = fs.readFileSync('C:/Users/Ota/.config/opencode/opencode.jsonc', 'utf8');
const idx = raw.indexOf('"omniroute-go"');
console.log(raw.slice(Math.max(0, idx - 1200), idx + 3500));
