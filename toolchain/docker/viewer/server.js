// Server di c64-emu-viewer (13/11). Copyright (c) 2026 - Simone Caporale
// UNA sola porta (6080, pubblicata solo su localhost):
//   /            pagina indice (www/index.html), /live.html schermo dal vivo con audio, /config.js disco proposto
//   /vnc/        client web di KasmVNC (file del pacchetto ufficiale)
//   /websockify  WebSocket verso Xvnc (127.0.0.1:6901, non pubblicato): passaggio dei byte cosi' come sono
//   /audio       WebSocket con l'audio dello schermo: PulseAudio (monitor della scheda "c64"), PCM s16le stereo 44100 Hz
//   /out/        cartella out/ del progetto, sola lettura (montata in /srv/out), con elenco delle cartelle
// VIEW_PASSWORD (facoltativa, di default assente): autenticazione HTTP Basic su TUTTO (pagine, out/, schermo, audio).
'use strict';
const http = require('http'), fs = require('fs'), path = require('path'), net = require('net');
const { WebSocketServer } = require('ws');
const PulseAudio = require('pulseaudio2');

const PORT = 6080, VNC_PORT = 6901, PASS = process.env.VIEW_PASSWORD || '';
const DISK = (process.env.VIEW_DISK || '').replace(/["\\]/g, '');
const ROOTS = [['/out/', '/srv/out', true], ['/vnc/', '/usr/share/kasmvnc/www', false], ['/', path.join(__dirname, 'www'), false]];
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.txt': 'text/plain; charset=utf-8',
  '.wasm': 'application/wasm', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.md': 'text/plain; charset=utf-8' };

function authorized(req) {
  if (!PASS) return true;
  const h = req.headers.authorization || '';
  if (!h.startsWith('Basic ')) return false;
  const s = Buffer.from(h.slice(6), 'base64').toString(), i = s.indexOf(':');
  return i >= 0 && s.slice(i + 1) === PASS;                       // utente qualsiasi, conta la password
}
const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function serveFile(req, res, file, st) {
  const lm = st.mtime.toUTCString();
  res.setHeader('Last-Modified', lm);
  res.setHeader('Cache-Control', 'no-cache');                    // il browser chiede sempre se il file e' cambiato (304)
  const ims = req.headers['if-modified-since'];
  if (ims && Math.floor(st.mtimeMs / 1000) <= Math.floor(Date.parse(ims) / 1000)) { res.statusCode = 304; return res.end(); }
  res.setHeader('Content-Type', MIME[path.extname(file).toLowerCase()] || 'application/octet-stream');
  res.setHeader('Content-Length', st.size);
  if (req.method === 'HEAD') return res.end();
  fs.createReadStream(file).pipe(res);
}

function listing(res, dir, urlPath) {                           // elenco HTML (lo legge la pagina indice)
  const items = fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))
    .map(d => d.name + (d.isDirectory() ? '/' : ''));
  res.setHeader('Content-Type', 'text/html; charset=utf-8'); res.setHeader('Cache-Control', 'no-cache');
  res.end(`<!doctype html><meta charset="utf-8"><title>${esc(urlPath)}</title><h1>${esc(urlPath)}</h1><ul>` +
    items.map(n => `<li><a href="${encodeURIComponent(n.replace(/\/$/, '')) + (n.endsWith('/') ? '/' : '')}">${esc(n)}</a></li>`).join('') + '</ul>');
}

const server = http.createServer((req, res) => {
  if (!authorized(req)) { res.statusCode = 401; res.setHeader('WWW-Authenticate', 'Basic realm="c64 viewer"'); return res.end(); }
  let urlPath;
  try { urlPath = decodeURIComponent(new URL(req.url, 'http://x').pathname); } catch (e) { res.statusCode = 400; return res.end(); }
  if (urlPath === '/config.js') {
    res.setHeader('Content-Type', 'text/javascript'); res.setHeader('Cache-Control', 'no-cache');
    return res.end(`window.VIEW_DISK = "${DISK}";\n`);
  }
  if (urlPath === '/out') { res.statusCode = 301; res.setHeader('Location', '/out/'); return res.end(); }
  const [prefix, root, list] = ROOTS.find(([p]) => urlPath.startsWith(p));
  const file = path.normalize(path.join(root, urlPath.slice(prefix.length)));
  if (file !== root && !file.startsWith(root + path.sep)) { res.statusCode = 403; return res.end(); }   // niente ../
  fs.stat(file, (err, st) => {
    if (err) { res.statusCode = 404; return res.end('non trovato'); }
    if (st.isDirectory()) {
      const idx = path.join(file, 'index.html');
      if (fs.existsSync(idx)) return serveFile(req, res, idx, fs.statSync(idx));
      if (list) return listing(res, file, urlPath);
      res.statusCode = 404; return res.end();
    }
    serveFile(req, res, file, st);
  });
});

// --- audio: un solo flusso di registrazione da PulseAudio, aperto finche' c'e' almeno un ascoltatore
const wss = new WebSocketServer({ noServer: true });
const pulse = new PulseAudio();
let pulseOk = true, rec = null;
pulse.on('error', e => { pulseOk = false; console.log('audio non disponibile:', e && e.message); });
function startRec() {
  if (rec || !pulseOk) return;
  rec = pulse.createRecordStream({ device: 'c64.monitor', channels: 2, rate: 44100, format: 'S16LE' });
  rec.on('connection', () => rec.on('data', chunk => { for (const c of wss.clients) if (c.readyState === 1) c.send(chunk); }));
}
function stopRec() { if (rec && wss.clients.size === 0) { try { rec.end(); } catch (e) { /* gia' chiuso */ } rec = null; } }
wss.on('connection', ws => { startRec(); ws.on('close', () => setTimeout(stopRec, 100)); });

// --- WebSocket: /audio qui, tutto il resto (client di KasmVNC) passa a Xvnc cosi' com'e'
server.on('upgrade', (req, sock, head) => {
  if (!authorized(req)) { sock.end('HTTP/1.1 401 Unauthorized\r\n\r\n'); return; }
  if (req.url.startsWith('/audio')) { wss.handleUpgrade(req, sock, head, ws => wss.emit('connection', ws, req)); return; }
  const up = net.connect(VNC_PORT, '127.0.0.1', () => {
    let h = `${req.method} ${req.url} HTTP/${req.httpVersion}\r\n`;
    for (let i = 0; i < req.rawHeaders.length; i += 2) {
      if (req.rawHeaders[i].toLowerCase() === 'authorization') continue;      // Xvnc non usa l'autenticazione: resta al viewer
      h += `${req.rawHeaders[i]}: ${req.rawHeaders[i + 1]}\r\n`;
    }
    up.write(h + '\r\n'); if (head && head.length) up.write(head);
    sock.pipe(up).pipe(sock);
  });
  up.on('error', () => sock.destroy()); sock.on('error', () => up.destroy());
});

server.listen(PORT, () => console.log(`viewer pronto: http://localhost:${PORT}` + (PASS ? ' (password)' : '')));
