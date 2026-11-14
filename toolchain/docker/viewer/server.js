// Server di c64-emu-viewer (13/11). Copyright (c) 2026 - Simone Caporale
// UNA sola porta (6080, pubblicata solo su localhost):
//   /            pagina indice (www/index.html), /live.html schermo dal vivo con audio, /config.js disco proposto e nome del progetto
//   /vnc/        client web di KasmVNC (file del pacchetto ufficiale)
//   /websockify  WebSocket verso Xvnc (127.0.0.1:6901, non pubblicato): passaggio dei byte cosi' come sono
//   /audio       WebSocket con l'audio dello schermo: PulseAudio (monitor della scheda "c64"), PCM s16le stereo 44100 Hz
//   /input       WebSocket dei tasti degli overlay (tastiera C64, joystick) di live.html: testo "d <keysym>", "u <keysym>", "f"
//                (= puntatore al centro dello schermo: senza window manager i tasti vanno alla finestra sotto il puntatore)
//   /out/        cartella out/ del progetto, sola lettura (montata in /srv/out), con elenco delle cartelle
//   /control     (14/11) POST JSON {"cmd":"status"|"play"|"stop","disk":"releases/v<V>/<file>.d64"}: VICE sullo schermo dal vivo,
//                inoltrato al lettore (toolchain/viewer_player.py, container c64-emu-player) dal socket Unix nel volume c64-x11
// VIEW_PASSWORD (facoltativa, di default assente): autenticazione HTTP Basic su TUTTO (pagine, out/, schermo, audio).
// Protezioni (14/11): Host deve essere localhost/127.0.0.1/[::1] (o in VIEW_HOSTS, separati da virgole) contro il DNS rebinding;
// WebSocket e /control accettano solo richieste dalla stessa origine (un altro sito aperto nel browser non puo' comandare il viewer);
// /control vuole Content-Type application/json (un form di un altro sito non puo' mandarlo senza preflight, che qui non si concede).
'use strict';
const http = require('http'), fs = require('fs'), path = require('path'), net = require('net');
const { WebSocketServer, WebSocket } = require('ws');
const PulseAudio = require('pulseaudio2');

const PORT = 6080, VNC_PORT = 6901, PASS = process.env.VIEW_PASSWORD || '';
const DISK = (process.env.VIEW_DISK || '').replace(/["\\]/g, '');
const PLAYER = JSON.stringify((process.env.VIEW_PLAYER || '').slice(0, 200)).replace(/</g, '\\u003c');   // comando del lettore (per la pagina)
const TITLE = JSON.stringify((process.env.VIEW_TITLE || '').slice(0, 80)).replace(/</g, '\\u003c');   // nome del progetto nella pagina
const PLAYER_SOCK = '/tmp/.X11-unix/c64-player.sock';
const HOSTS = new Set(['localhost', '127.0.0.1', '[::1]', ...(process.env.VIEW_HOSTS || '').split(',').map(s => s.trim().toLowerCase()).filter(Boolean)]);
function hostOk(req) {                                          // nome dell'Host senza porta
  const h = String(req.headers.host || '').toLowerCase().replace(/:\d+$/, '');
  return HOSTS.has(h);
}
function sameOrigin(req) {                                      // Origin assente (curl, script locali) o uguale all'Host
  const o = req.headers.origin;
  if (!o) return true;
  try { return new URL(o).host === req.headers.host; } catch (e) { return false; }
}
function control(req, res) {
  const fail = (code, msg) => { res.statusCode = code; res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify({ ok: false, error: msg })); };
  if (req.method !== 'POST') return fail(405, 'solo POST');
  if (!sameOrigin(req)) return fail(403, 'origine diversa');
  if (!String(req.headers['content-type'] || '').startsWith('application/json')) return fail(415, 'serve application/json');
  let body = '';
  req.on('data', d => { body += d; if (body.length > 2048) req.destroy(); });
  req.on('end', () => {
    let q;
    try { q = JSON.parse(body); } catch (e) { return fail(400, 'JSON non valido'); }
    const line = JSON.stringify({ cmd: String(q.cmd || ''), disk: q.disk === undefined ? undefined : String(q.disk) }) + '\n';
    const c = net.connect(PLAYER_SOCK);
    let out = '', done = false;
    const finish = (code, txt) => { if (done) return; done = true; res.statusCode = code; res.setHeader('Content-Type', 'application/json'); res.setHeader('Cache-Control', 'no-store'); res.end(txt); };
    c.setTimeout(8000, () => { c.destroy(); finish(504, JSON.stringify({ ok: false, error: 'il lettore non risponde' })); });
    c.on('connect', () => c.write(line));
    c.on('data', d => { out += d; });
    c.on('end', () => finish(200, out.trim() || JSON.stringify({ ok: false, error: 'risposta vuota' })));
    c.on('error', () => finish(503, JSON.stringify({ ok: false, error: 'lettore non attivo (C64_VIEW_PLAYER in toolchain.env, poi toolchain/viewer.sh stop e start)' })));
  });
}
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
  if (!hostOk(req)) { res.statusCode = 421; return res.end('Host non ammesso (VIEW_HOSTS)'); }
  if (!authorized(req)) { res.statusCode = 401; res.setHeader('WWW-Authenticate', 'Basic realm="c64 viewer"'); return res.end(); }
  let urlPath;
  try { urlPath = decodeURIComponent(new URL(req.url, 'http://x').pathname); } catch (e) { res.statusCode = 400; return res.end(); }
  if (urlPath === '/config.js') {
    res.setHeader('Content-Type', 'text/javascript'); res.setHeader('Cache-Control', 'no-cache');
    return res.end(`window.VIEW_DISK = "${DISK}";\nwindow.VIEW_TITLE = ${TITLE};\nwindow.VIEW_PLAYER = ${PLAYER};\n`);
  }
  if (urlPath === '/control') return control(req, res);
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

// --- /input: tasti iniettati in Xvnc come secondo client RFB (solo KeyEvent e PointerEvent; non si chiede mai l'immagine).
// Ogni connessione /input apre il suo client RFB (cosi' la dimensione dello schermo e' quella di adesso) e al termine rilascia i tasti rimasti premuti.
const inWss = new WebSocketServer({ noServer: true });
inWss.on('connection', ws => {
  const down = new Set(), pending = [];
  let st = 0, buf = Buffer.alloc(0), w = 1280, h = 1000, ready = false;
  const up = new WebSocket(`ws://127.0.0.1:${VNC_PORT}/websockify`, ['binary'], { headers: { Origin: `http://127.0.0.1:${VNC_PORT}` } });   // senza Origin Xvnc risponde 404
  const key = (sym, d) => { const m = Buffer.alloc(8); m[0] = 4; m[1] = d; m.writeUInt32BE(sym >>> 0, 4); up.send(m); };
  const ptr = (x, y) => { const m = Buffer.alloc(11); m[0] = 5; m.writeUInt16BE(x, 3); m.writeUInt16BE(y, 5); up.send(m); };   // KasmVNC: 5, maschera u16, x, y, scorrimento x e y (s16): 11 byte, non 6 come nell'RFB standard
  const run = c => {
    const [op, a] = c.split(' '), sym = parseInt(a, 10);
    if (op === 'f') ptr(w >> 1, h >> 1);
    else if ((op === 'd' || op === 'u') && Number.isInteger(sym)) {
      if (op === 'd') down.add(sym); else down.delete(sym);
      key(sym, op === 'd' ? 1 : 0);
    }
  };
  function step() {                                            // handshake RFB 3.8 senza sicurezza
    for (;;) {
      if (st === 0) { if (buf.length < 12) return; buf = buf.subarray(12); up.send(Buffer.from('RFB 003.008\n')); st = 1; }
      else if (st === 1) {
        if (!buf.length || buf.length < 1 + buf[0]) return;
        const types = [...buf.subarray(1, 1 + buf[0])]; buf = buf.subarray(1 + buf[0]);
        if (!types.includes(1)) { up.close(); return; }
        up.send(Buffer.from([1])); st = 2;
      } else if (st === 2) { if (buf.length < 4) return; if (buf.readUInt32BE(0) !== 0) { up.close(); return; } buf = buf.subarray(4); up.send(Buffer.from([1])); st = 3; }
      else if (st === 3) {
        if (buf.length < 24 || buf.length < 24 + buf.readUInt32BE(20)) return;
        w = buf.readUInt16BE(0); h = buf.readUInt16BE(2); buf = Buffer.alloc(0); st = 4;
        ready = true; for (const c of pending.splice(0)) run(c);
      } else { buf = Buffer.alloc(0); return; }
    }
  }
  up.on('message', d => { if (st < 4) { buf = Buffer.concat([buf, d]); step(); } });
  up.on('error', () => ws.close()); up.on('close', () => ws.close());
  ws.on('message', m => { const c = String(m).slice(0, 40); if (ready) run(c); else if (pending.length < 100) pending.push(c); });
  ws.on('close', () => { if (ready && up.readyState === 1) for (const s of down) key(s, 0); up.close(); });
  ws.on('error', () => ws.close());
});

// --- WebSocket: /audio e /input qui, tutto il resto (client di KasmVNC) passa a Xvnc cosi' com'e'
server.on('upgrade', (req, sock, head) => {
  if (!hostOk(req) || !sameOrigin(req)) { sock.end('HTTP/1.1 403 Forbidden\r\n\r\n'); return; }
  if (!authorized(req)) { sock.end('HTTP/1.1 401 Unauthorized\r\n\r\n'); return; }
  if (req.url.startsWith('/input')) { inWss.handleUpgrade(req, sock, head, ws => inWss.emit('connection', ws, req)); return; }
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
