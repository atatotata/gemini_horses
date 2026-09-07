const http=require('http');
function post(path, body){
  return new Promise(res=>{
    const b=JSON.stringify(body);
    const req=http.request({hostname:'localhost',port:20128,path,method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer sk-ae42a2661869ce17-4433c6-9b6f4115','Content-Length':Buffer.byteLength(b)},timeout:20000},r=>{
      let d='';r.on('data',c=>d+=c);r.on('end',()=>res({status:r.statusCode,body:d.slice(0,1200)}));
    });
    req.on('error',e=>res({status:'ERR',body:e.message}));
    req.on('timeout',()=>{req.destroy();res({status:'TIMEOUT',body:''})});
    req.write(b);req.end();
  });
}
(async()=>{
  const tests=[
    {path:'/v1/responses', body:{model:'opencode-go/muse-spark-1.3-contributor',input:'Say hi in one word'}},
    {path:'/v1/responses', body:{model:'muse-spark-1.3-contributor',input:'Say hi in one word'}},
    {path:'/v1/chat/completions', body:{model:'opencode-go/muse-spark-1.3-contributor',messages:[{role:'user',content:'Say hi in one word'}],max_tokens:5}},
  ];
  for(const t of tests){
    const r=await post(t.path,t.body);
    console.log(`POST ${t.path} model=${t.body.model} => ${r.status}`);
    console.log(r.body.slice(0,900).replace(/\n/g,' '));
    console.log('---');
  }
})();
