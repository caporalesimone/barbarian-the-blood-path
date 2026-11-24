#!/usr/bin/env python3
"""Genera out/work/manual/manuale.html e out/work/manual/Barbarian_Blood_Path_Manuale.pdf (A5, WeasyPrint).

Gira nel container lab64-pdf-gen di Lab64 (WeasyPrint; l'ombra del titolo in copertina non c'e' perche' WeasyPrint ignora
text-shadow). Dall'host: ./build.sh --manual (o lab64 manual, C64_MANUAL in lab64.env).

Sorgente editabile: manual/manuale_src.html. Stile (15/11): il tema base "c64" di Lab64 (containers/pdf-gen/themes/c64.css) +
manual/tema.css (solo le regole del gioco). Questo script fa le parti del gioco:
  1. ritaglia gli screenshot grezzi (manual/shots/*.png) in out/work/manual/img/*.png (area utile 320x200 senza bordo);
  1b. la mappa del mondo (fan art, tools/art/world_map.py, numpy + Pillow, deterministica; 19/11 la genera ./build.sh in
     lab64-tools prima del manuale): out/work/art/world_map_1x.png -> out/work/manual/img/world_map.png (960x600); non e' in git;
  2. prepara i dati di data/rules.yaml e data/balance.yaml per i segnaposto {{MONSTER_ROWS}} {{STEP_HDR}} {{MIN_ROW}} {{MAX_ROW}};
  3. il resto lo fa c64manual.build di Lab64: segnaposto, tema, tasti <kbd> disegnati, numeri di pagina, manuale.html, PDF
     (WeasyPrint) e avviso per le pagine che traboccano.
Screenshot: tools/vice/shots_manual.sh (la schermata del nuovo barbaro: variante TESTUI 31); sprite mostri: manual/mon.
Lingue (11/11; 15/11 tutte nella stessa build): senza --lang fa TUTTI i manuali che hanno il sorgente; --lang it|en uno solo.
it: manuale_src.html -> manuale.html + Barbarian_Blood_Path_Manuale.pdf; en: manual_src_en.html -> manual_en.html +
Barbarian_Blood_Path_Manual_EN.pdf (il sorgente inglese non e' ancora scritto: TODO E7). Le parti generate (tabella dei mostri)
hanno le parole nelle due lingue. Una lingua nuova: una voce in SOURCES e in W. --strict (release): una pagina che trabocca
o un segnaposto senza valore fermano la build."""
import os, re, subprocess, sys, yaml
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
R = os.path.join(ROOT, "out", "work", "manual")          # (13/11) tutto cio' che genera: HTML, ritagli, PDF
M = os.path.join(ROOT, "manual")         # (11/11) sorgente del manuale in manual/
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
import bestiary  # noqa: E402
Y = bestiary.load_balance()       # balance.yaml + mostri (data/monsters/bestiary.tsv, 11/11)
import items_db  # noqa: E402
RL = items_db.load_rules()        # rules.yaml + data/items/items.tsv (11/11)
SOURCES = {"it": ("manuale_src.html", "manuale.html", "Barbarian_Blood_Path_Manuale.pdf"),
           "en": ("manual_src_en.html", "manual_en.html", "Barbarian_Blood_Path_Manual_EN.pdf")}
if "--lang" not in sys.argv:                      # (15/11) tutti i manuali che hanno il sorgente, nella stessa build
    langs = [l for l, (src, _, _) in SOURCES.items() if os.path.exists(os.path.join(M, src))]
    sys.exit(max(subprocess.run([sys.executable, __file__, "--lang", l] + sys.argv[1:]).returncode for l in langs))
LANG = sys.argv[sys.argv.index("--lang") + 1]
assert LANG in ("it", "en"), "--lang it|en"
SRC, OUT, PDF = SOURCES[LANG]
if not os.path.exists(os.path.join(M, SRC)):
    sys.exit("manual source manual/%s missing (the English manual is a TODO)" % SRC)
W = {"it": {"base": "base", "strong": "forte", "final": "boss finale", "dpf": "per piano", 5: "lenta", 7: "media",
            8: "normale", 9: "veloce"},
     "en": {"base": "base", "strong": "strong", "final": "final boss", "dpf": "per level", 5: "slow", 7: "medium",
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

# (16/11) mappa del mondo, mai salvata in git. (19/11) la v3 usa numpy, che lab64-pdf-gen non ha: la genera ./build.sh nel
# container lab64-tools prima del manuale (lab64 run python3 tools/art/world_map.py); qui si genera solo se numpy c'e'
WM = os.path.join(ROOT, "out", "work", "art", "world_map_1x.png")
try:
    import numpy  # noqa: F401
    import runpy
    runpy.run_path(os.path.join(ROOT, "tools", "art", "world_map.py"), run_name="world_map")
except ImportError:
    if not os.path.exists(WM):
        sys.exit("manuale: manca out/work/art/world_map_1x.png: lab64 run python3 tools/art/world_map.py (o ./build.sh --manual)")
Image.open(os.path.join(ROOT, "out", "work", "art", "world_map_1x.png")).convert("RGB").save(os.path.join(R, "img", "world_map.png"))

# ------------------------------------------------------------------ 2. dati dinamici
names = {"fallen": "Fallen", "skeleton": "Skeleton", "zombie": "Zombie", "demon": "Demon",
         "fallen_warchief": "Fallen Warchief", "skeleton_king": "Skeleton King", "lich": "Lich",
         "balrog": "Balrog", "lord_of_ruin": "Lord of Ruin"}
pngs = {"fallen": "fallen", "skeleton": "skeleton", "zombie": "zombie", "demon": "demon",
        "fallen_warchief": "warchief", "skeleton_king": "skeleton_king", "lich": "lich",
        "balrog": "balrog", "lord_of_ruin": "lord_of_ruin"}
spd = {k: W[k] for k in (5, 7, 8, 9)}
mons = Y["monsters"]
import mon_stats as MS        # noqa: E402  (24/11) valori dalle formule del bestiario, come il C64
MCF = MS.coefs_by_id(RL, Y)
fmt = lambda v: ("%g" % v).replace(".", ",") if LANG == "it" else "%g" % v

rows = ""
for key, m in mons.items():
    r = RL["monsters"][key]
    cf = MCF[key]
    v = MS.values(cf, r["floor"])
    kind = W[m["tier"]]
    gr = "" if m["tier"] == "final" or not cf["hp"][1] else f' <small>(+{fmt(cf["hp"][1] / 16)} {W["dpf"]})</small>'
    dmg = ("%dd%d+%d" % (v["dn"], v["ds"], v["dk"])) if v["dn"] else str(v["dk"])
    rows += (f'<tr><td class="spr"><img src="mon/{pngs[key]}.png"></td>'
             f'<td><b>{names[key]}</b><br><small>{kind}</small></td><td>{r["floor"]}</td><td>{v["hp"]}{gr}</td>'
             f'<td>{dmg}</td><td>{v["ac"]}</td><td>{v["xp"]}</td><td>{spd.get(m["speed"], m["speed"])}</td></tr>')
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

# ------------------------------------------------------------------ 3. manuale (Lab64: tema, tasti, numeri di pagina, PDF)
from c64manual import build  # noqa: E402  (Lab64, container lab64-pdf-gen; tema base "c64" + manual/tema.css)
hp, pdf, n = build(os.path.join(M, SRC), out_dir=R, pdf_name=PDF, html_name=OUT, theme=os.path.join(M, "tema.css"),
                   values={"MONSTER_ROWS": rows, "STEP_HDR": hdr, "MIN_ROW": cells(mn), "MAX_ROW": cells(mx)},
                   html_only="--html" in sys.argv, strict="--strict" in sys.argv)
print(pdf or hp, n, "pagine numerate")
