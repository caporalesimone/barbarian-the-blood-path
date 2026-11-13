// PROTOTIPO: tunnel guacamole-lite su 8080 (WebSocket) + pagina statica su 8081 con il token della connessione VNC
const GuacamoleLite = require('guacamole-lite'), http = require('http'), fs = require('fs'), crypto = require('crypto'), path = require('path');
const KEY = 'MySuperSecretKeyForParamsToken12';
new GuacamoleLite({ port: 8080 }, { host: process.env.GUACD || 'guacd', port: 4822 }, { crypt: { cypher: 'AES-256-CBC', key: KEY }, log: { level: 'ERRORS' } });
function token(obj) {
  const iv = crypto.randomBytes(16), c = crypto.createCipheriv('AES-256-CBC', KEY, iv);
  let v = c.update(JSON.stringify(obj), 'utf8', 'base64'); v += c.final('base64');
  return Buffer.from(JSON.stringify({ iv: iv.toString('base64'), value: v })).toString('base64');
}
const conn = { connection: { type: 'vnc', settings: { hostname: process.env.VNC_HOST || 'viewer', port: '5900', 'enable-audio': true,
  'audio-servername': process.env.PULSE_HOST || 'viewer', width: 1280, height: 1000, dpi: 96 } } };
const files = { '/': 'index.html', '/guac.js': 'node_modules/guacamole-common-js/dist/cjs/guacamole-common.js' };
http.createServer((q, r) => {
  const u = q.url.split('?')[0];
  if (u === '/token') { r.end(token(conn)); return; }
  const f = files[u]; if (!f) { r.statusCode = 404; r.end(); return; }
  r.setHeader('Content-Type', u.endsWith('.js') ? 'text/javascript' : 'text/html'); r.end(fs.readFileSync(path.join(__dirname, f)));
}).listen(8081);
console.log('guac proto: http://localhost:8081');
