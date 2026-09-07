const http = require('http');

(async () => {
  const live = await new Promise((resolve) => {
    const req = http.request(
      {
        hostname: 'localhost',
        port: 20128,
        path: '/v1/models',
        method: 'GET',
        headers: { Authorization: 'Bearer sk-ae42a2661869ce17-4433c6-9b6f4115' },
      },
      (res) => {
        let d = '';
        res.on('data', (c) => (d += c));
        res.on('end', () => resolve(JSON.parse(d)));
      }
    );
    req.end();
  });

  const m13 = live.data
    .filter((m) => m.id.includes('1.3') || (m.id.includes('muse') && m.id.includes('1.')))
    .map((m) => m.id)
    .sort();
  console.log('All live 1.3 / muse models in catalog (' + m13.length + '):');
  m13.forEach((id) => console.log('  ' + id));
})();
