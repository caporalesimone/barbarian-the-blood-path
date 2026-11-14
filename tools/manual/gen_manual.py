#!/usr/bin/env python3
"""Genera out/work/manual/manuale.html e out/work/manual/Barbarian_Blood_Path_Manuale.pdf (A5, WeasyPrint).

Gira nel container barbarian-manual (tools/manual, 13/11: WeasyPrint al posto di Chrome; stesse 19 pagine, l'ombra del
titolo in copertina non c'e' perche' WeasyPrint ignora text-shadow). Dall'host: ./build.sh --manual.

Sorgente editabile: docs/manual/manuale_src.html (+ stile.css). Questo script:
  1. ritaglia gli screenshot grezzi (docs/manual/shots/*.png) in out/work/manual/img/*.png (area utile 320x200 senza bordo);
  2. riempie i segnaposto con i dati di data/rules.yaml e data/balance.yaml:  {{MONSTER_ROWS}} {{STEP_HDR}} {{MIN_ROW}} {{MAX_ROW}};
  3. numera le pagine e scrive manuale.html;
  4. stampa il PDF con WeasyPrint.
Screenshot: tools/vice/shots_manual.sh (la schermata del nuovo barbaro: variante TESTUI 31); sprite mostri: docs/manual/mon.
Lingua (11/11): python3 tools/manual/gen_manual.py [--lang it|en]. it (default): manuale_src.html -> manuale.html +
Barbarian_Blood_Path_Manuale.pdf; en: manual_src_en.html -> manual_en.html + Barbarian_Blood_Path_Manual_EN.pdf (il
sorgente inglese non e' ancora scritto: TODO). Le parti generate (tabella dei mostri) hanno le parole nelle due lingue."""
import os, re, subprocess, sys, yaml
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
R = os.path.join(ROOT, "out", "work", "manual")          # (13/11) tutto cio' che genera: HTML, ritagli, PDF
M = os.path.join(ROOT, "docs", "manual")         # (11/11) sorgente del manuale in docs/manual/
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
import bestiary  # noqa: E402
Y = bestiary.load_balance()       # balance.yaml + mostri (data/monsters/bestiary.tsv, 11/11)
import items_db  # noqa: E402
RL = items_db.load_rules()        # rules.yaml + data/items/items.tsv (11/11)
LANG = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "it"
assert LANG in ("it", "en"), "--lang it|en"
SRC, OUT, PDF = {"it": ("manuale_src.html", "manuale.html", "Barbarian_Blood_Path_Manuale.pdf"),
                 "en": ("manual_src_en.html", "manual_en.html", "Barbarian_Blood_Path_Manual_EN.pdf")}[LANG]
if not os.path.exists(os.path.join(M, SRC)):
    sys.exit("manual source docs/manual/%s missing (the English manual is a TODO)" % SRC)
W = {"it": {"base": "base", "strong": "forte", "final": "boss finale", "dpf": "dadi/piano", 5: "lenta", 7: "media",
            8: "normale", 9: "veloce"},
     "en": {"base": "base", "strong": "strong", "final": "final boss", "dpf": "dice/level", 5: "slow", 7: "medium",
            8: "normal", 9: "fast"}}[LANG]

# ------------------------------------------------------------------ 1. ritaglio screenshot
os.makedirs(os.path.join(R, "img"), exist_ok=True)
for f in sorted(os.listdir(os.path.join(M, "shots"))):
    if not f.endswith(".png"):
        continue
    im = Image.open(os.path.join(M, "shots", f)).convert("RGB").crop((32, 36, 352, 236))
    if f == "chest.png":
        im = im.crop((0, 0, 320, 120))
    im.save(os.path.join(R, "img", f))

# ------------------------------------------------------------------ 2. dati dinamici
names = {"fallen": "Fallen", "skeleton": "Skeleton", "zombie": "Zombie", "demon": "Demon",
         "fallen_warchief": "Fallen Warchief", "skeleton_king": "Skeleton King", "lich": "Lich",
         "balrog": "Balrog", "lord_of_ruin": "Lord of Ruin"}
pngs = {"fallen": "fallen", "skeleton": "skeleton", "zombie": "zombie", "demon": "demon",
        "fallen_warchief": "warchief", "skeleton_king": "skeleton_king", "lich": "lich",
        "balrog": "balrog", "lord_of_ruin": "lord_of_ruin"}
spd = {k: W[k] for k in (5, 7, 8, 9)}
mons = Y["monsters"]
g = RL["growth"]
gv = "%g" % g["hp_dice_per_floor"]
grow = (f' <small>(+{gv.replace(".", ",") if LANG == "it" else gv} {W["dpf"]})</small>')

rows = ""
for key, m in mons.items():
    r = RL["monsters"][key]
    kind = W[m["tier"]]
    gr = "" if m["tier"] == "final" else grow
    rows += (f'<tr><td class="spr"><img src="mon/{pngs[key]}.png"></td>'
             f'<td><b>{names[key]}</b><br><small>{kind}</small></td><td>{r["floor"]}</td><td>{r["hp"]}{gr}</td>'
             f'<td>{r["dmg"]}</td><td>{r["ac"]}</td><td>{r["xp"]}</td><td>{spd.get(m["speed"], m["speed"])}</td></tr>')
mx = Y["spawn"]["max_monsters_per_level"]
mn = Y["spawn"]["min_monsters_per_level"]
cells = lambda a: "".join(f"<td>{v if v else '—'}</td>" for v in a)
# piani di ogni gradino delle tabelle spawn (stessa regola di tools/build/gen_db.py step())
NF = RL["dungeon"]["floors"]
nst = len(mx)
step = lambda L: nst if L == NF else max(1, min(nst - 1, round(L * (nst - 1) / (NF - 1))))
hdr = ""
for g in range(1, nst + 1):
    fl = [L for L in range(1, NF + 1) if step(L) == g]
    hdr += f"<th>{fl[0]}–{fl[-1]}</th>" if len(fl) > 1 else f"<th>{fl[0]}</th>"

# ------------------------------------------------------------------ 3. composizione
html = open(os.path.join(M, SRC), encoding="utf-8").read()
for ph, val in (("{{MONSTER_ROWS}}", rows), ("{{STEP_HDR}}", hdr), ("{{MIN_ROW}}", cells(mn)), ("{{MAX_ROW}}", cells(mx))):
    assert ph in html, "segnaposto mancante nel sorgente: " + ph
    html = html.replace(ph, val)
# tasti (09/11): ogni <kbd>X</kbd> diventa un piccolo SVG disegnato in unita' del font (DejaVu Sans Mono, 2048/em,
# avanzamento 1233, altezza delle maiuscole 1493). Il testo e' centrato geometricamente nel riquadro: nell'HTML Chrome
# aggancia la linea di base al pixel intero e lo scarto cambiava da tasto a tasto (W A S D piu' bassi di ~1 px);
# dentro l'SVG la posizione e' esatta e uguale per tutti i tasti.
import html as _h
U, ADV, CAP = 2048, 1233, 1493
KH, PADX, BRD, RAD, SH = 2908, 941, 196, 785, 314      # 1,42 em; 1,2 mm; 0,25 mm; 1 mm; ombra 0,4 mm (a 7,4 pt)
def kbd(m):
    t = _h.unescape(m.group(1))
    w = max(KH, len(t) * ADV + 2 * PADX)
    th = KH + SH
    base = KH / 2 + CAP / 2                              # maiuscole e cifre centrate in verticale
    return (f'<svg class="key" viewBox="0 0 {w} {th}" style="width:{w / U:.4f}em;height:{th / U:.4f}em;'
            f'vertical-align:-{(th - base) / U:.4f}em">'
            f'<rect x="{BRD / 2}" y="{BRD / 2 + SH}" width="{w - BRD}" height="{KH - BRD}" rx="{RAD}" fill="#2a2118"/>'
            f'<rect x="{BRD / 2}" y="{BRD / 2}" width="{w - BRD}" height="{KH - BRD}" rx="{RAD}" fill="#fffaf0" '
            f'stroke="#2a2118" stroke-width="{BRD}"/>'
            f'<text x="{w / 2}" y="{base:.0f}" text-anchor="middle" font-family="DejaVu Sans Mono" font-size="{U}" '
            f'fill="#2a2118">{_h.escape(t)}</text></svg>')
html = re.sub(r"<kbd>(.*?)</kbd>", kbd, html)

n = [0]
def number(m):
    n[0] += 1
    return m.group(0) if n[0] == 1 else f'<div data-n="— {n[0]-1} —" class="page'
html = re.sub(r'<div class="page', number, html)
# l'HTML sta in out/work/manual/: foglio di stile e sprite dei mostri restano nel sorgente (docs/manual/)
html = html.replace('href="stile.css"', 'href="../../docs/manual/stile.css"').replace('src="mon/', 'src="../../docs/manual/mon/')
open(os.path.join(R, OUT), "w", encoding="utf-8").write(html)

# ------------------------------------------------------------------ 4. PDF
pdf = os.path.join(R, PDF)
if "--html" in sys.argv:                         # solo l'HTML (senza WeasyPrint)
    print(os.path.join(R, OUT), n[0], "pagine"); sys.exit(0)
import logging                                   # noqa: E402
logging.getLogger("weasyprint").setLevel(logging.ERROR)   # avvisi noti: text-shadow, print-color-adjust
import weasyprint                                # noqa: E402  (container barbarian-manual)
weasyprint.HTML(os.path.join(R, OUT)).write_pdf(pdf)
print(pdf, n[0], "pagine")

# ------------------------------------------------------------------ 5. controllo: pagine che traboccano (testo tagliato)
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        pg.goto("file://" + os.path.abspath(os.path.join(R, OUT)))
        pg.emulate_media(media="print")
        over = pg.evaluate("""() => [...document.querySelectorAll('.page')].map((p, i) => {
            const r = p.getBoundingClientRect(); let m = 0;
            for (const e of p.querySelectorAll('*')) m = Math.max(m, e.getBoundingClientRect().bottom - r.top);
            return [i, Math.round(m - p.clientHeight + 38)]; }).filter(x => x[1] > 0)""")
        b.close()
    for i, px in over:
        print(f"ATTENZIONE: pagina {i} trabocca di ~{px} px (testo tagliato)")
except ImportError:
    pass
