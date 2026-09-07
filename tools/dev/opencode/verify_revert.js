const fs=require('fs');
const p='C:/Users/Ota/.config/opencode/opencode.jsonc';
const raw=fs.readFileSync(p,'utf8');
console.log('has omniroute-go-responses:', raw.includes('omniroute-go-responses'));
console.log('bytes:', raw.length);
try{
  const stripped=raw.replace(/\/\/.*$/gm,'').replace(/,\s*([}\]])/g,'$1');
  const cfg=JSON.parse(stripped);
  console.log('providers:', Object.keys(cfg.provider));
  console.log('omniroute-go models:', Object.keys(cfg.provider['omniroute-go'].models).length);
  console.log('JSON valid: yes');
}catch(e){ console.log('JSON valid: no', e.message.slice(0,200)); }
