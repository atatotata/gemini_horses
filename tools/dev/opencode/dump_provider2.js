const fs=require('fs');
const raw=fs.readFileSync('C:/Users/Ota/.config/opencode/opencode.jsonc','utf8');
const cfg=JSON.parse(raw);
for(const k of Object.keys(cfg.provider)){
  const v=cfg.provider[k];
  const shallow={};
  for(const kk of Object.keys(v)){
    if(kk==='models') shallow.models_count=Object.keys(v.models).length;
    else shallow[kk]=v[kk];
  }
  console.log(k+':');
  console.log(JSON.stringify(shallow, null, 2));
  console.log('---');
}
