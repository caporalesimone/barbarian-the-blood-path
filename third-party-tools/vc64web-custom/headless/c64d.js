#!/usr/bin/env node
// c64d: demone che tiene aperto l'emulatore (pagina minima c64-headless.html, solo emulatore) in Chromium headless
// e ne espone window.c64 via HTTP su 127.0.0.1. Uso:
//   node c64d.js [--page c64-headless.html] [--api c64-api.js] [--port 7064]    (serve il modulo npm 'playwright': npm install in questa cartella, oppure globale con NODE_PATH=$(npm root -g))
// Richiesta: POST /call  {"method":"peek","args":["0x0400",16]}  ->  {"ok":true,"value":[...]}  |  {"ok":false,"error":"...","code":"..."}
//            GET /ping    POST /quit
// Copyright (c) 2026 Simone Caporale
const http = require('http'), path = require('path'), fs = require('fs'), os = require('os'), { spawn } = require('child_process');
const { chromium } = require('playwright');
const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
const pageDefault = [path.join(__dirname, 'c64-headless.html'), path.join(__dirname, '..', 'out', 'c64-headless.html')].find(f => fs.existsSync(f)) || path.join(__dirname, '..', 'out', 'c64-headless.html');
const PAGE = path.resolve(arg('page', pageDefault));   // default: pagina minima (solo emulatore) generata da build.py in out/
const PORT = +arg('port', 7064), HOST = arg('host', process.env.C64_HOST || '127.0.0.1');   // in Docker: 0.0.0.0 (pubblicare la porta solo su 127.0.0.1 dell'host: il demone non ha autenticazione e c64.eval esegue JS)
if (!fs.existsSync(PAGE)) { console.error('pagina non trovata: ' + PAGE + '\nla pagina headless si genera con: python3 build.py (crea out/c64-headless.html). uso: c64d.js [--page FILE] [--api c64-api.js] [--port 7064]'); process.exit(2); }

(async () => {
  // modalita' con finestra visibile (--headed o C64_HEADED=1): stesso demone e stessa CLI, ma Chromium mostra la finestra con l'emulatore (serve un display)
  const HEADED = process.argv.includes('--headed') || /^(1|true|yes)$/i.test(process.env.C64_HEADED || '');
  if (HEADED && process.platform === 'linux' && !process.env.DISPLAY && !process.env.WAYLAND_DISPLAY) { console.error('--headed: nessun display (DISPLAY non impostato). Su un server usare xvfb-run, oppure lanciare da una sessione grafica.'); process.exit(2); }
  const browser = await chromium.launch({ headless: !HEADED, args: ['--autoplay-policy=no-user-gesture-required'].concat(process.env.C64_NO_SANDBOX ? ['--no-sandbox'] : []).concat(HEADED ? ['--window-size=1000,860'] : []) });
  const page = await (await browser.newContext({ viewport: HEADED ? null : { width: 1000, height: 800 } })).newPage();   // headed: viewport libero (la finestra si ridimensiona a mano)
  if (HEADED) { const bye = why => { console.error('c64d: ' + why + ': demone terminato'); process.exit(0); }; page.on('close', () => bye('finestra chiusa')); browser.on('disconnected', () => bye('browser chiuso')); }
  console.error('c64d: Chromium ' + (HEADED ? 'con finestra (headed)' : 'headless'));
  page.on('pageerror', e => console.error('pageerror', String(e).slice(0, 200)));
  await page.goto('file://' + PAGE);
  const apiVer = (() => { try { return fs.readFileSync(path.join(__dirname, 'APIVER'), 'utf8').trim(); } catch (e) { return '0'; } })();   // la versione API e' nel file APIVER (accanto a c64-api.js)
  await page.addScriptTag({ content: fs.readFileSync(path.resolve(arg('api', path.join(__dirname, 'c64-api.js'))), 'utf8').replace('/*__API__*/', apiVer) });   // l'HTML non contiene l'API: la si inietta
  await page.waitForFunction(() => window.c64 && typeof window.c64.apiVersion === 'number');
  const call = (method, args) => page.evaluate(async ([m, a]) => {
    try {
      const f = window.c64[m]; if (typeof f !== 'function') return { ok: false, error: 'metodo sconosciuto: ' + m, code: 'BAD_METHOD' };
      let v = await f.apply(window.c64, a);
      if (v instanceof Uint8Array) { let s = ''; for (let i = 0; i < v.length; i += 0x8000) s += String.fromCharCode.apply(null, v.subarray(i, i + 0x8000)); v = { mime: 'application/octet-stream', data: btoa(s) }; }
      return { ok: true, value: v === undefined ? null : v };
    } catch (e) { return { ok: false, error: String(e.message || e), code: e.code || 'ERROR', outputs: e.outputs, log: e.log }; }
  }, [method, args]);
  // video deterministico: gli screenshot si catturano DENTRO la pagina ogni 'every' fotogrammi emulati mentre gira uno script di input
  // (o un ciclo JS, o N fotogrammi) e si codificano con ffmpeg (necessario nel PATH). Opzioni: {script|loop|frames, every:2, fps:25, scale:3 (1-4), crf:20, loopOpts}
  const video = async o => {
    o = o || {}; const every = o.every || 2, fps = o.fps || Math.round(50 / every), scale = Math.min(4, Math.max(1, o.scale || 3)), crf = o.crf === undefined ? 20 : o.crf;
    const kind = o.script !== undefined ? 'script' : o.loop !== undefined ? 'loop' : o.frames !== undefined ? 'frames' : null;
    if (!kind) return { ok: false, error: 'video: serve script, loop o frames', code: 'BAD_ARG' };
    const arg = kind === 'script' ? o.script : kind === 'loop' ? { code: o.loop, opts: o.loopOpts || {} } : o.frames;
    const out = path.join(os.tmpdir(), 'c64video-' + process.pid + '-' + Date.now() + '.mp4');
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-', '-vf', 'scale=iw*' + scale + ':ih*' + scale + ':flags=neighbor,format=yuv420p', '-c:v', 'libx264', '-preset', o.preset || 'medium', '-crf', String(crf), '-movflags', '+faststart', out], { stdio: ['pipe', 'ignore', 'pipe'] });
    let ferr = '', failed = null; ff.stderr.on('data', d => { ferr += d; }); ff.on('error', e => { failed = e; ff.stdin.destroy(); });
    const closed = new Promise(r => ff.on('close', r));
    let r = await call('capStart', [{ every }]); if (!r.ok) { ff.stdin.destroy(); return r; }
    try {
      r = await call('capRun', [kind, arg]); if (!r.ok) return r;
      let n = 0, res = null, err = null;
      for (;;) {
        const t = await call('capTake', [40]); if (!t.ok) return t;
        for (const b64 of t.value.frames) { if (failed) break; if (!ff.stdin.write(Buffer.from(b64, 'base64'))) await new Promise(r => ff.stdin.once('drain', r)); n++; }
        if (failed) return { ok: false, error: 'ffmpeg non disponibile: ' + failed.message, code: 'NO_FFMPEG' };
        if (t.value.done) { res = t.value.result; err = t.value.error; break; }
        if (!t.value.frames.length) await new Promise(r => setTimeout(r, 15));
      }
      ff.stdin.end(); const code = await closed;
      if (err) return { ok: false, error: 'video: ' + err.message, code: err.code };
      if (code !== 0 || !fs.existsSync(out)) return { ok: false, error: 'ffmpeg ha fallito: ' + ferr.slice(-300), code: 'FFMPEG' };
      const buf = fs.readFileSync(out); return { ok: true, value: { mime: 'video/mp4', data: buf.toString('base64'), bytes: buf.length, frames: n, fps, scale, result: res } };
    } finally { await call('capStop', []); try { fs.unlinkSync(out); } catch (e) { } }
  };
  // ---- video dentro uno script (API 15): «video start [NOME] [keep] ... / video stop» ----
  // la pagina mette in coda fotogrammi (stringhe base64 PNG) e marcatori {ctl:'start'|'stop'}; il demone li passa a un ffmpeg per clip. «keep»: la clip resta aperta dopo lo script
  // e un pump in background continua a svuotare la coda mentre arrivano altre chiamate; si chiude con il metodo videoStop.
  const vs = { enc: null, done: [], chain: Promise.resolve(), pump: false, err: null };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const mkEnc = c => {
    const out = path.join(os.tmpdir(), 'c64clip-' + process.pid + '-' + Date.now() + '-' + c.id + '.mp4'), fps = c.fps || Math.round(50 / (c.every || 2));
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-', '-vf', 'scale=iw*' + c.scale + ':ih*' + c.scale + ':flags=neighbor,format=yuv420p', '-c:v', 'libx264', '-preset', 'medium', '-crf', String(c.crf), '-movflags', '+faststart', out], { stdio: ['pipe', 'ignore', 'pipe'] });
    const e = { c, out, ff, fps, n: 0, ferr: '', failed: null }; ff.stderr.on('data', d => { e.ferr += d; }); ff.on('error', x => { e.failed = x; ff.stdin.destroy(); });
    e.closed = new Promise(r => ff.on('close', r)); return e;
  };
  const finishEnc = async () => {
    const e = vs.enc; if (!e) return; vs.enc = null; if (!e.failed) e.ff.stdin.end(); const code = await e.closed;
    if (e.failed) { vs.err = { code: 'NO_FFMPEG', message: 'ffmpeg non disponibile: ' + e.failed.message }; return; }
    if (code !== 0 || !fs.existsSync(e.out)) { vs.err = { code: 'FFMPEG', message: 'ffmpeg ha fallito: ' + e.ferr.slice(-300) }; return; }
    const buf = fs.readFileSync(e.out); try { fs.unlinkSync(e.out); } catch (x) { }
    vs.done.push({ type: 'video', name: e.c.name, mime: 'video/mp4', bytes: buf.length, frames: e.n, fps: e.fps, scale: e.c.scale, data: buf.toString('base64') });
  };
  const handle = async items => {
    for (const it of items) {
      if (typeof it === 'string') { const e = vs.enc; if (e && !e.failed) { if (!e.ff.stdin.write(Buffer.from(it, 'base64'))) await new Promise(r => e.ff.stdin.once('drain', r)); e.n++; } }
      else if (it.ctl === 'start') { await finishEnc(); vs.enc = mkEnc(it); }
      else if (it.ctl === 'stop') await finishEnc();
    }
  };
  const drain = () => (vs.chain = vs.chain.then(async () => { const t = await call('capTake', [40]); if (t.ok) await handle(t.value.frames); return t; }));
  const startPump = () => { if (vs.pump) return; vs.pump = true; (async () => { try { while (vs.enc) { const t = await drain(); if (!t.ok) break; if (!t.value.frames.length) await sleep(15); } } finally { vs.pump = false; } })(); };
  const scriptVideo = async args => {
    vs.done = []; vs.err = null; let r;
    if (!vs.enc) { await call('capStop', []); r = await call('capArm', []); if (!r.ok) return r; }   // con un video «keep» ancora aperto la cattura esiste gia
    r = await call('capRun', ['script', args[0]]); if (!r.ok) { await call('capStop', []); return r; }
    let res = null, err = null;
    for (;;) { const t = await drain(); if (!t.ok) return t; if (t.value.done) { res = t.value.result; err = t.value.error; break; } if (!t.value.frames.length) await sleep(15); }
    const open = !!vs.enc; if (open) startPump(); else await call('capStop', []);
    const outs = (err ? (err.outputs || []) : (res && res.outputs) || []).concat(vs.done); vs.done = [];
    if (vs.err) return { ok: false, error: 'video: ' + vs.err.message, code: vs.err.code, outputs: outs };
    if (err) return { ok: false, error: err.message, code: err.code, outputs: outs, log: err.log };
    res = res || {}; if (outs.length) res.outputs = outs; else delete res.outputs; if (open) res.videoOpen = vs.enc.c.name; return { ok: true, value: res };
  };
  const videoStop = async () => {
    if (!vs.enc) return { ok: false, error: 'nessun video attivo', code: 'NO_VIDEO' };
    let r = await call('capClipStop', []); if (!r.ok) return r;
    while (vs.enc) { const t = await drain(); if (!t.ok) return t; }
    await call('capStop', []); if (vs.err) { const e = vs.err; vs.err = null; return { ok: false, error: 'video: ' + e.message, code: e.code }; }
    const v = vs.done.pop(); vs.done = []; return { ok: true, value: v };
  };
  let queue = Promise.resolve(), cancelCur = false, running = 0, jobSeq = 0, pending = 0, curMethod = null, curT0 = 0;      // le chiamate sono serializzate: l'emulatore e' deterministico solo se una alla volta
  const server = http.createServer((req, res) => {
    const send = (c, o) => { let body; try { body = JSON.stringify(o, (k, v) => typeof v === 'bigint' ? (v >= -9007199254740991n && v <= 9007199254740991n ? Number(v) : v.toString()) : v); } catch (e) { body = JSON.stringify({ ok: false, error: 'risposta non serializzabile: ' + e.message, code: 'DAEMON' }); } res.writeHead(c, { 'content-type': 'application/json' }); res.end(body); };   // BigInt (es. wasm wasm_get_cpu_cycles) -> numero (stringa se oltre 2^53); prima il demone andava in crash
    if (req.method === 'GET' && req.url === '/ping') return send(200, { ok: true, value: { api: 'c64d', port: PORT, page: path.basename(PAGE) } });
    if (req.method === 'POST' && req.url === '/quit') { send(200, { ok: true }); setTimeout(async () => { await browser.close(); server.close(); process.exit(0); }, 50); return; }
    if (req.method === 'GET' && req.url === '/status') {   // API 18: stato del job in corso (non passa dalla coda)
      call('progress', []).then(r => send(200, { ok: true, value: { busy: running !== 0, method: curMethod, elapsedMs: running ? Date.now() - curT0 : 0, queued: pending, progress: r.ok ? r.value : null } }), e => send(200, { ok: false, error: String(e.message || e), code: 'DAEMON' })); return; }
    if (req.method === 'POST' && req.url === '/abort') {   // API 18: interrompe il job in corso (non passa dalla coda); i job in attesa restano
      cancelCur = true; call('abort', []).then(r => send(200, r), e => send(200, { ok: false, error: String(e.message || e), code: 'DAEMON' })); return; }
    if (req.method === 'POST' && req.url === '/call') {
      const chunks = []; req.on('data', c => chunks.push(c));
      req.on('end', () => {
        let b; try { b = JSON.parse(Buffer.concat(chunks).toString()); } catch (e) { return send(400, { ok: false, error: 'JSON non valido', code: 'BAD_JSON' }); }
        let gone = false; res.on('close', () => { if (!res.writableFinished) { gone = true; if (running === job) call('abort', []).catch(() => { }); } });   // client chiuso/ucciso: il job si interrompe (o viene saltato se e' ancora in coda)
        const job = ++jobSeq; pending++;
        queue = queue.then(() => { if (gone) { pending--; return { ok: false, error: 'client disconnesso prima dell\'esecuzione', code: 'CLIENT_GONE' }; } pending--; running = job; curMethod = b.method; curT0 = Date.now(); return b.method === 'video' ? video((b.args || [])[0]) : b.method === 'videoStop' ? videoStop() : (b.method === 'runScript' && typeof (b.args || [])[0] === 'string' && /^\s*(\+?\d+\s+)?video\s+(start|stop)\b/im.test(b.args[0])) ? scriptVideo(b.args) : call(b.method, b.args || []); }).then(r => { if (running === job) running = 0; send(200, r); }, e => { if (running === job) running = 0; send(200, { ok: false, error: String(e.message || e), code: 'DAEMON' }); });
      }); return;
    }
    send(404, { ok: false, error: 'not found' });
  });
  server.listen(PORT, HOST, () => console.log('c64d pronto su ' + HOST + ':' + PORT + ' (' + path.basename(PAGE) + ')'));
})();
