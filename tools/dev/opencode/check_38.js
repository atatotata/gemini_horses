const http = require('http');
(async () => {
  const live = await new Promise((r) => {
    const req = http.request(
      { hostname: 'localhost', port: 20128, path: '/v1/models', method: 'GET', headers: { Authorization: 'Bearer sk-ae42a2661869ce17-4433c6-9b6f4115' } },
      (res) => { let d = ''; res.on('data', (c) => (d += c)); res.on('end', () => r(JSON.parse(d))); }
    );
    req.end();
  });
  const gem38 = live.data.map((m) => m.id).filter((id) => id.includes('3.8')).sort();
  console.log('Live *3.8* models (' + gem38.length + '):');
  gem38.forEach((id) => console.log(' ' + id));
  const ant = live.data.map((m) => m.id).filter((id) => id.startsWith('antigravity/')).sort();
  console.log('\nAll live antigravity (' + ant.length + '):');
  ant.forEach((id) => console.log(' ' + id));
})();
