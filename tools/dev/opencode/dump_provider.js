const fs=require('fs');
const raw=fs.readFileSync('C:/Users/Ota/.config/opencode/opencode.jsonc','utf8');
const cfg=JSON.parse(raw);
console.log(JSON.stringify(cfg.provider['omniroute-go'], null, 2).slice(0,12000));
console.log('---ALL PROVIDER KEYS---');
console.log(Object.keys(cfg.provider));
for(const k of Object.keys(cfg.provider)){
  const v=cfg.provider[k];
  console.log(k, '->', JSON.stringify({baseURL: v.baseURL, base_url: v.base_url, api: v.api, provider: v.provider, type: v.type, options: v.options}, null, 2).slice(0,800));
}
