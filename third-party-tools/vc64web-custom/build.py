#!/usr/bin/env python3
# Costruisce un unico HTML con vc64web + UI touch (pagina portable) e la pagina minima del demone (headless).
# Copyright (c) 2026 Simone Caporale.
#
# Cartelle (13/11): tutte parametri, con default relativi a questa cartella, cosi' il pacchetto e' autonomo (repository a se')
# e si puo' costruire anche da un progetto che lo contiene:
#   --vice-roms DIR   ROM Commodore (sottocartelle C64/ e DRIVES/, nomi di VICE)  default roms/vice-roms   (env C64_VICE_ROMS)
#   --open-roms DIR   ROM libere Open ROMs (ripiego)                              default roms/open-roms   (env C64_OPEN_ROMS)
#   --out DIR         uscita (pagine HTML)                                        default out              (env C64_OUT)
#   --tag NOME        nome dell'immagine Docker                                   default c64d             (env C64_IMAGE)
# Quali ROM servono e dove si trovano: roms/roms.md.
import base64, json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
R = ROOT / 'third-party' / 'vc64web'


def opt(name, env, default):
    """--name VALORE (o --name=VALORE), altrimenti la variabile d'ambiente, altrimenti il default; relativo alla cartella corrente"""
    for i, a in enumerate(sys.argv[1:], 1):
        if a == '--' + name and i + 1 < len(sys.argv): return Path(sys.argv[i + 1]).resolve()
        if a.startswith('--' + name + '='): return Path(a.split('=', 1)[1]).resolve()
    return Path(os.environ[env]).resolve() if os.environ.get(env) else default


VICE = opt('vice-roms', 'C64_VICE_ROMS', ROOT / 'roms' / 'vice-roms')
OPEN = opt('open-roms', 'C64_OPEN_ROMS', ROOT / 'roms' / 'open-roms')
OUTDIR = opt('out', 'C64_OUT', ROOT / 'out')
TAG = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv[:-1] else os.environ.get('C64_IMAGE', 'c64d')
ROMDIRS = [VICE / 'C64', VICE / 'DRIVES', VICE]
FLAGS = [a for a in sys.argv[1:] if a.startswith('--')]
BF = ROOT / 'BUILD'
N = (int(BF.read_text()) if BF.exists() else 0) + (1 if '--bump-version' in FLAGS else 0)
if '--bump-version' in FLAGS: BF.write_text(str(N))      # solo con --bump-version (release) si incrementa il contatore (file BUILD, nel repo)
VER = 'v%02d' % N
API = (ROOT / 'headless' / 'APIVER').read_text().strip()   # versione API: intero incrementale, da aggiornare a mano quando cambia l'API
import shutil
if OUTDIR.exists(): shutil.rmtree(OUTDIR)
OUTDIR.mkdir(parents=True)
OUT = OUTDIR / ('VirtualC64-%s.html' % VER)

def rd(p): return (R / p).read_text(encoding='utf8')
def esc_script(s): return s.replace('</script', '<\\/script').replace('<!--', '<\\!--')
def b64(p): return base64.b64encode(Path(p).read_bytes()).decode()

PIXEL = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'

import subprocess
subprocess.run([sys.executable, str(ROOT / 'portable' / 'asm' / 'mkblob.py'), str(OUTDIR / 'kt-blob.json')], check=True)
KTBLOB = (OUTDIR / 'kt-blob.json').read_text()
(OUTDIR / 'kt-blob.json').unlink()

h = rd('index.html')

# --- parti che non servono / richiedono rete -------------------------------
h = re.sub(r'<link[^>]*rel=(?:manifest|icon|apple-touch-icon)[^>]*>', '', h)
h = re.sub(r'<link[^>]*href=(?:img/favicon\.ico|manifest\.json|img/icon-96x96\.png)[^>]*>', '', h)
h = re.sub(r'<script src=https://cloud\.umami\.is[^>]*></script>', '', h)
h = re.sub(r'<script src=js/cm6/[^>]*></script>', '', h)           # editor script (non usato qui)
h = re.sub(r'<script src=js/vc64_updater\.js></script>', '', h)    # service worker / update

# --- CSS inline ------------------------------------------------------------
font = 'data:font/ttf;base64,' + b64(R / 'css/C64_Pro_Mono-STYLE.ttf')
def css_inline(m):
    css = rd('css/' + m.group(1))
    css = re.sub(r'/\*# sourceMappingURL=.*?\*/', '', css)
    css = css.replace('"C64_Pro_Mono-STYLE.ttf"', '"%s"' % font)
    return '<style>' + css + '</style>'
h = re.sub(r'<link href=css/([\w.-]+\.css) rel=stylesheet>', css_inline, h)

# --- JS inline -------------------------------------------------------------
def js_inline(m):
    name = m.group(1)
    js = rd(name)
    js = re.sub(r'//# sourceMappingURL=\S+', '', js)
    js = re.sub(r'window\.location\.href(?=[.)\s,;])', 'window.__HREF', js)
    return '<script>' + esc_script(js) + '</script>'
h = re.sub(r'<script src=([\w/.-]+\.js)(?: async| defer)?></script>', js_inline, h)

# --- sprite SVG inline -----------------------------------------------------
sprites = rd('img/sprites.svg')
sprites = re.sub(r'<svg ', '<svg style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true" ', sprites, count=1)
h = re.sub(r'(<body[^>]*>)', lambda m: m.group(1) + sprites, h, count=1)
h = h.replace('/img/sprites.svg#', '#').replace('img/sprites.svg#', '#')

# --- immagini: pixel trasparente (servono solo in dialoghi nascosti) --------
h = re.sub(r'img/[\w.-]+\.(?:png|ico)', PIXEL, h)

# --- config e URL letti dal documento: niente location.href (srcdoc non ha hash) -
h = re.sub(r'window\.location\.href(?=[.)\s,;])', 'window.__HREF', h)
ui_js_patch = lambda js: re.sub(r'window\.location\.href(?=[.)\s,;])', 'window.__HREF', js)

# --- pre-script: risorse e config dal genitore (fetch / audio worklet) -------
pre = r"""<script>
(function(){
  var E = window.parent.__EMU, cache = {};
  window.__HREF = E.href;
  function key(u){ u=String((u&&u.url)||u).split('#')[0].split('?')[0]; for(var k in E.assets){ if(u.length>=k.length && u.slice(-k.length)===k) return k; } return null; }
  function bytes(k){ if(!cache[k]){ var s=atob(E.assets[k].b), a=new Uint8Array(s.length); for(var i=0;i<s.length;i++) a[i]=s.charCodeAt(i); cache[k]=a; } return cache[k]; }
  var of=window.fetch.bind(window);
  window.fetch=function(u,o){
    var k=key(u); if(k===null) return of(u,o);
    var r=new Response(bytes(k),{status:200,headers:{'Content-Type':E.assets[k].t}});
    try{ Object.defineProperty(r,'url',{value:String((u&&u.url)||u)}); }catch(e){}
    return Promise.resolve(r);
  };
  if(window.AudioWorklet){
    var am=AudioWorklet.prototype.addModule;
    AudioWorklet.prototype.addModule=function(u,o){ var k=key(u); return am.call(this,k?('data:text/javascript;base64,'+E.assets[k].b):u,o); };
  }
})();
</script>"""
h = re.sub(r'(<head>)', lambda mm: mm.group(1) + pre + '<style>#button_show_menu{display:none!important}</style>', h, count=1)
h = h.replace('<title>vc64web C64 emulator iPad iPhone</title>', '<title>vc64web</title>')

# --- risorse binarie/testuali caricate a runtime ----------------------------
assets = {}
def add(name, path, mime):
    assets[name] = {'t': mime, 'b': b64(path)}
add('vc64.wasm', R / 'vc64.wasm', 'application/wasm')
for n in ['insert', 'eject', 'step', 'key_standard', 'key_backspace', 'key_space']:
    add('sounds/%s.mp3' % n, R / ('sounds/%s.mp3' % n), 'audio/mpeg')
add('js/vc64_audioprocessor.js', R / 'js/vc64_audioprocessor.js', 'text/javascript')
add('js/vc64_audioprocessor_stereo.js', R / 'js/vc64_audioprocessor_stereo.js', 'text/javascript')
for n in ['basic_generic.rom', 'kernal_generic.rom', 'chargen_pxlfont_2.3.rom']:
    add(n, OPEN / n, 'application/octet-stream')       # Open ROMs: solo se mancano le ROM Commodore

# ROM Commodore (VICE). Portable: tutte le varianti compatibili, selezionabili; headless: solo le predefinite (+ le due 1541)
DEF_K, DEF_C = '901227-03', '901225-01'
KERNALS = ['901227-03', '901227-02', '901227-01', '251104-04', '390852-01', '901246-01', '906145-02']
CHARGENS = ['901225-01', '906143-02']
DRIVES = {'rom_floppy': 'dos1541ii-251968-03.bin', 'rom_floppy_1541': 'dos1541-325302-01+901229-05.bin'}
def find_rom(fname):
    for d in ROMDIRS:
        if (d / fname).is_file(): return d / fname
    return None
def rom(path): return {'t': 'application/octet-stream', 'b': b64(path)}
rom_full, rom_hl, missing = {}, {}, []
# (chiave, nome file, obbligatoria): le predefinite servono alla pagina headless e al test del gioco; le varianti sono facoltative
# e, se mancano, non entrano nel menu della pagina portable (il menu elenca solo quelle incorporate)
WANT = [('rom_kernal_' + k, 'kernal-%s.bin' % k, k == DEF_K) for k in KERNALS] \
     + [('rom_chargen_' + c, 'chargen-%s.bin' % c, c == DEF_C) for c in CHARGENS] \
     + [('rom_basic', 'basic-901226-01.bin', True)] + [(key, f, True) for key, f in DRIVES.items()]
for key, fname, required in WANT:
    p = find_rom(fname)
    if p: rom_full[key] = rom(p)
    else: missing.append((fname, required))
if any(r for _, r in missing):
    sys.exit('ROM obbligatorie mancanti: %s\ncercate in: %s\n(quali file e dove trovarli: roms/roms.md; cartella: --vice-roms DIR)' % (
        ', '.join(f for f, r in missing if r), ', '.join(str(d) for d in ROMDIRS)))
if missing: print('ROM facoltative non trovate (non sono nel menu della pagina portable):', ', '.join(f for f, _ in missing))
print('ROM da:', ', '.join(sorted({str(find_rom(f).parent) for k, f, _ in WANT if find_rom(f)})))
for key in ['rom_kernal_' + DEF_K, 'rom_chargen_' + DEF_C, 'rom_basic'] + list(DRIVES): rom_hl[key] = rom_full[key]
assets_hl = dict(assets, **rom_hl)
assets = dict(assets, **rom_full)

def js_str(s):
    return json.dumps(s, ensure_ascii=False).replace('</', '<\\/').replace('<!--', '<\\!--').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')

shell = (ROOT / 'portable' / 'shell.html').read_text(encoding='utf8')
shell = shell.replace('/*__INNER__*/null', js_str(h))
shell = shell.replace('/*__ASSETS__*/{}', json.dumps(assets).replace('</', '<\\/'))
shell = shell.replace('/*__VER__*/', VER).replace('/*__KTBLOB__*/null', KTBLOB)
OUT.write_text(shell, encoding='utf8')

# --- pagina headless: solo emulatore + minimo per avviarlo (per il demone) -----------------------------
src = (ROOT / 'portable' / 'shell.html').read_text(encoding='utf8')
KT = src[src.index('/*KT<<*/') + 8: src.index('/*>>KT*/')]
AI = src[src.index('function afterInsert(){'):]; AI = AI[:AI.index('\n}\n') + 3]
hl = (ROOT / 'headless' / 'headless.template.html').read_text(encoding='utf8')
hl = hl.replace('/*__AFTERINSERT__*/', AI).replace('/*__KT__*/', KT)
hl = hl.replace('/*__INNER__*/null', js_str(h)).replace('/*__ASSETS__*/{}', json.dumps(assets_hl).replace('</', '<\\/'))
hl = hl.replace('/*__VER__*/', VER).replace('/*__KTBLOB__*/null', KTBLOB)
print('scritto', OUT, round(OUT.stat().st_size / 1e6, 2), 'MB; inner', round(len(h) / 1e3), 'KB')

(OUTDIR / 'c64-headless.html').write_text(hl, encoding='utf8')
print('scritto', OUTDIR / 'c64-headless.html', round((OUTDIR / 'c64-headless.html').stat().st_size / 1e6, 2), 'MB')

# --- container Docker (se docker e' disponibile): contesto = tutto il repo, compreso out/ ---------------
import shutil as _sh
if '--no-docker' in FLAGS: print('docker: saltato (--no-docker)')
elif not _sh.which('docker'): print('docker: NON disponibile in questo ambiente, immagine non costruita (esegui di nuovo build.py dove c\'e\' docker)')
else:
    tag = TAG + ':' + VER
    # contesto = questa cartella (allowlist .dockerignore); le pagine arrivano dal contesto con nome "pages" (--out)
    cmd = ['docker', 'build', '-t', tag, '-t', TAG + ':latest', '--build-context', 'pages=' + str(OUTDIR)]
    ca = os.environ.get('C64_CA_BUNDLE')      # facoltativo: CA di un proxy che intercetta TLS (solo per npm durante la build)
    if ca: cmd += ['--secret', 'id=ca,src=' + ca]
    subprocess.run(cmd + [str(ROOT)], check=True, env=dict(os.environ, DOCKER_BUILDKIT='1')); print('immagine', tag)
    if '--save' in FLAGS: subprocess.run('docker save %s:latest | gzip > %s' % (TAG, OUTDIR / ('%s-%s.tar.gz' % (TAG, VER))), shell=True, check=True)
print('build', VER, 'api', API, '->', OUTDIR)

# --- controllo ffmpeg (non bloccante): serve solo per i video deterministici -----------------------------
def _ffmpeg_check():
    ff = _sh.which('ffmpeg')
    if not ff: return 'ffmpeg NON trovato nel PATH'
    try:
        enc = subprocess.run([ff, '-hide_banner', '-encoders'], capture_output=True, text=True, timeout=20).stdout
    except Exception as e: return 'ffmpeg trovato (%s) ma non eseguibile: %s' % (ff, e)
    if 'libx264' not in enc: return 'ffmpeg trovato (%s) ma senza encoder libx264' % ff
    return None
_w = None if '--no-ffmpeg-check' in FLAGS else _ffmpeg_check()   # (il controllo serve dove gira il demone)
if _w: print('\nWARNING: %s. Il build e\' completo, ma i video deterministici (c64 video, "video start" negli script) non funzioneranno finche\' non lo installi. Vedi README.md, sezione "ffmpeg".' % _w)
else: print('ffmpeg: ok')
