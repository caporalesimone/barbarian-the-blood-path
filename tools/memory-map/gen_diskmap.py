#!/usr/bin/env python3
"""Mappa del disco di Barbarian: The Blood Path -> out/memory-map/mappa_disco.html
Legge il d64 (default out/disk.d64, release; ./build.sh gli passa il disco della build: di debug o di release), le etichette (out/game.lbl), src/game/game.asm (blocco eroe)
e out/gfx_consts.inc. Uso: python3 tools/memory-map/gen_diskmap.py [disco.d64] [out.html]"""
import html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D64 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out", "disk.d64")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "out", "memory-map", "mappa_disco.html")
img = open(D64, "rb").read()


def spt(t):
    return 21 if t <= 17 else 19 if t <= 24 else 18 if t <= 30 else 17


OFF = {}
o = 0
for t in range(1, 36):
    for s in range(spt(t)):
        OFF[(t, s)] = o
        o += 256


def blk(t, s):
    return img[OFF[(t, s)]:OFF[(t, s)] + 256]


def chain(t, s):
    out = []
    while t:
        out.append((t, s))
        b = blk(t, s)
        t, s = b[0], b[1]
    return out


def data(ch):
    d = b""
    for i, (t, s) in enumerate(ch):
        b = blk(t, s)
        d += b[2:] if b[0] else b[2:b[1] + 1]
    return d


def petscii(b):
    return "".join(chr(c) if 32 <= c < 96 else "?" for c in b.rstrip(b"\xa0")).lower()


# ------------------------------------------------------------------ directory
TYPES = {1: "seq", 2: "prg", 3: "usr", 4: "rel"}
bam = blk(18, 0)
disk_name = petscii(bam[0x90:0xA0])
disk_id = petscii(bam[0xA2:0xA4])
files = []
for (t, s) in chain(18, 1):
    b = blk(t, s)
    for e in range(8):
        x = b[e * 32:(e + 1) * 32]
        if x[2] & 7 == 0:
            continue
        f = dict(name=petscii(x[5:21]), type=TYPES.get(x[2] & 7, "?"), t=x[3], s=x[4], blocks=x[30] + 256 * x[31])
        f["chain"] = chain(f["t"], f["s"])
        f["data"] = data(f["chain"])
        if f["type"] == "rel":
            f["reclen"] = x[23]
            f["ss"] = chain(x[21], x[22])
        files.append(f)
owner = {}
for i, f in enumerate(files):
    for ts in f["chain"]:
        owner[ts] = (i, "d")
    for ts in f.get("ss", []):
        owner[ts] = (i, "s")
dirblk = chain(18, 1)
free_blocks = sum(bam[4 + 4 * (t - 1)] for t in range(1, 36) if t != 18)

# ------------------------------------------------------------------ etichette e costanti
L = {}
for l in open(os.path.join(ROOT, "out", "game.lbl")):
    m = re.match(r"\s*(\S+)\s*=\s*\$([0-9a-f]+)", l)
    if m:
        L[m.group(1)] = int(m.group(2), 16)
    m = re.match(r"\s*(\S+)\s*=\s*(\d+)\s*$", l)
    if m:
        L[m.group(1)] = int(m.group(2))
TILES = {}
for l in open(os.path.join(ROOT, "out", "gfx_consts.inc")):
    m = re.match(r"(T_\w+)\s*=\s*(\d+)", l)
    if m:
        TILES[int(m.group(2))] = m.group(1)
TSTRIP, DSTRIP, MONS, STRONG, NT = L["GFX_TSTRIP"], L["GFX_DSTRIP"], L["GFX_MONS"], L["GFX_STRONG"], L["GFX_NT"]
FSTRIP = 160
SAVE_VER = int(re.search(r"SAVE_VER = \$([0-9a-f]+)", open(os.path.join(ROOT, "out", "version.inc")).read()).group(1), 16)
VERSION = open(os.path.join(ROOT, "out", "version.inc")).read().split('"')[1]

# ------------------------------------------------------------------ grafica
def glyphs(d, strips, n):
    g = [d[q * n * 8 + i * 8:q * n * 8 + i * 8 + 8] for q in range(strips) for i in range(n)]
    return len(g), sum(1 for x in g if any(x)), len({x for x in g if any(x)})


def sprites(d):
    sp = [d[i:i + 64] for i in range(0, len(d), 64)]
    return len(sp), sum(1 for x in sp if any(x[:63]))


GFX = []
for f in files:
    if re.fullmatch(r"gfx\d|twn1", f["name"]):              # (12/11) villaggio: TWN1 (TWN2..4 sono copie)
        n = 0 if f["name"] == "twn1" else int(f["name"][3])
        d = f["data"][2:]
        if n == 0:
            tot, used, uniq = glyphs(d, 4, NT)
            GFX.append(dict(f=f, n=n, kind="Villaggio", load=0xE000, size=len(d), tiles=NT, chars=tot, used=used, uniq=uniq,
                            parts=[("Tile: 4 strisce x %d B (%d tile)" % (TSTRIP, NT), 4 * TSTRIP), ("Mappa del villaggio (RLE)", len(d) - 4 * TSTRIP)],
                            spr=None))
        else:
            tot, used, uniq = glyphs(d, 4, DSTRIP // 8)
            m1 = sprites(d[4 * DSTRIP:4 * DSTRIP + MONS])
            m2 = sprites(d[4 * DSTRIP + MONS:4 * DSTRIP + MONS + STRONG])
            ML, ch = L["MAXLEVEL"], (n + 1) // 2
            if n % 2:
                kind = "Capitolo %d: dungeon (piani %d-%d)" % (ch, 5 * ch - 4, 5 * ch)
            else:
                kind = "Capitolo %d: boss, tile della sala del trono (piano %d)" % (ch, 5 * ch)
            GFX.append(dict(f=f, n=n, kind=kind, load=0xED00, size=len(d),
                            tiles=DSTRIP // 8, chars=tot, used=used, uniq=uniq,
                            parts=[("Tile: 4 strisce x %d B (%d tile)" % (DSTRIP, DSTRIP // 8), 4 * DSTRIP),
                                   ("Sprite mostri base (8)", MONS), ("Sprite forti + boss (10)", STRONG)],
                            spr=(m1, m2)))

# ------------------------------------------------------------------ blocco eroe (da src/game/game.asm)
src = open(os.path.join(ROOT, "src", "game", "game.asm")).read()
blkt = src[src.index("CHRBLK\n"):src.index("CHREND")]
fields = re.findall(r"^((?:c|st)_\w+)\s+\.(byte|word|fill)\s*([^;\n]*?)\s*(?:;\s*(.*))?$", blkt, re.M)
DESC = {
    "c_magic": "versione del formato = save_version di version.yaml (oggi $%02X): se diversa l'eroe e' scartato" % SAVE_VER,
    "c_seed": "seed numerico del mondo (dai 6 caratteri di c_seedt)", "c_loc": "luogo attuale: 0 villaggio, 1..20 piano",
    "c_lvl": "livello dell'eroe", "c_xp": "esperienza (24 bit)", "c_gold": "oro (16 bit)", "c_hp": "vita attuale (16 bit)",
    "c_vis": "1 bit per piano 1..24: il piano ha uno stato salvato (record dei piani)",
    "c_retlvl": "piano a cui riporta il portale", "c_retx": "X di ritorno del portale (pixel)", "c_rety": "Y di ritorno del portale (pixel)",
    "c_portal": "1 = portale aperto nel villaggio", "c_beltt": "cintura: 4 posti, una pozione ciascuno (id, 0 = vuoto)",
    "c_skill": "abilita' selezionata", "c_kills": "mostri uccisi (16 bit)",
    "c_won": "1 = boss finale sconfitto", "c_lever": "1 = leva tirata: portale per The Endless Abyss nella sala del trono",
    "c_maxd": "piano piu' profondo raggiunto", "c_name": "nome (12 codici schermo)", "c_px": "X dell'eroe (pixel)", "c_py": "Y dell'eroe (pixel)",
    "c_pack": "zaino: id oggetto (0 = vuoto), 8 posti", "c_eq": "equipaggiamento: arma, armatura, scudo, cintura",
    "c_seedt": "seed: 6 caratteri in base 36 (0-9, A-Z)", "c_gver": "versione del generatore dei dungeon",
    "c_packb": "bonus +N degli oggetti nello zaino", "c_eqb": "bonus +N degli oggetti equipaggiati", "c_keys": "chiavi possedute",
    "c_packd": "durabilita' attuale degli oggetti nello zaino (armi, armature, scudi; 0 = non si usura)",
    "c_eqd": "durabilita' attuale dell'equipaggiamento (segue lo zaino: indice 8..11)",
    "c_packm": "durabilita' massima (zaino)", "c_eqm": "durabilita' massima (equipaggiamento)",
    "c_game": "bit 0..8: numero della partita (1..511, +1 a ogni 'continua'); bit 9..23: minuti giocati",
    "c_deaths": "morti (16 bit)",
    "c_sgold": "oro nel baule della locanda in decine (16 bit, fino a 655350 monete): la morte non lo tocca; oro totale = c_gold + 10 x c_sgold",
    "st_id": "baule della locanda: id dei 24 oggetti (0 = vuoto)", "st_b": "baule della locanda: bonus", "st_du": "baule della locanda: durabilita' attuale", "st_m": "baule della locanda: durabilita' massima",
}
HERO = []
for name, kind, arg, com in fields:
    a = L[name] - L["CHRBLK"]
    HERO.append([a, name, kind, com])
CHRLEN = L["CHREND"] - L["CHRBLK"]
for i, x in enumerate(HERO):
    x.append((HERO[i + 1][0] if i + 1 < len(HERO) else CHRLEN) - x[0])

# ------------------------------------------------------------------ HTML
def h(x):
    return html.escape(str(x))


P = ["""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mappa del disco</title><style>
:root{--bg:#f6f5f1;--fg:#1d1d1b;--mut:#6b6a64;--line:#d9d6cc;--card:#fff;--free:#eef3e8;--sys:#3a3a38;--ss:#1d1d1b}
@media (prefers-color-scheme:dark){:root{--bg:#17181a;--fg:#e9e7e1;--mut:#9b998f;--line:#34352f;--card:#202124;--free:#26301f;--sys:#9a988f;--ss:#fff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 80px}h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:40px 0 8px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:14px;margin:22px 0 6px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em}p{margin:6px 0;max-width:82ch}.mut{color:var(--mut)}
code,.mono,td.n{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
table{border-collapse:collapse;width:100%;margin-top:8px}td,th{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;font-size:13px;vertical-align:top}
td.n,th.n{text-align:right;white-space:nowrap}.wrap{overflow-x:auto}
.sw{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-1px;margin-right:6px;background:var(--c)}
.grid{display:grid;grid-template-columns:34px repeat(21,1fr);gap:2px;font:10px ui-monospace,Menlo,monospace;min-width:640px}
.grid div{height:16px;border-radius:2px;background:var(--free)}.grid .tn{background:none;color:var(--mut);text-align:right;padding-right:4px;line-height:16px}
.grid .na{background:none}.grid .ss{outline:2px solid var(--ss);outline-offset:-2px}
.bar{display:flex;height:26px;border-radius:5px;overflow:hidden;border:1px solid var(--line);margin:4px 0 2px}.bar div{background:var(--c);color:#fff;font-size:11px;padding:4px 6px;white-space:nowrap;overflow:hidden}
.bar .fr{background:var(--free);color:var(--mut)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:10px}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.card b.t{font-size:15px}.recs{display:grid;grid-template-columns:repeat(30,1fr);gap:2px;min-width:620px}.recs div{height:22px;border-radius:2px;background:var(--c);font:9px ui-monospace,Menlo,monospace;color:#fff;text-align:center;line-height:22px}
.leg span{margin-right:14px;font-size:13px;white-space:nowrap}
</style></head><body><main>"""]
P.append("<h1>Barbarian: The Blood Path &middot; mappa del disco</h1>")
P.append('<p class="mut">Disco <code>%s</code> (nome "%s", ID "%s"), build v%s, save_version $%02X. Generata da <code>tools/memory-map/gen_diskmap.py</code> leggendo il d64 blocco per blocco.</p>'
         % (h(os.path.relpath(D64, ROOT)), h(disk_name), h(disk_id), h(VERSION), SAVE_VER))

COL = ["#d4622a", "#8e6cc9", "#3b7fc4", "#2f9e8f", "#d9a23a", "#c2477e", "#7a9a3a", "#5a7fa8", "#b5653f", "#4f9a77", "#9c6fb8",
       "#c58b2e", "#3f8fb0", "#a8547a", "#6a8f3c", "#7b6c58"]
for i, f in enumerate(files):
    f["col"] = COL[i % len(COL)]

# --- 1. file
P.append("<h2>1. File sul disco</h2><div class='wrap'><table><tr><th>#</th><th>Nome</th><th>Tipo</th><th class='n'>Blocchi</th><th class='n'>Byte</th><th>Primo blocco</th><th>Contenuto</th></tr>")
WHAT = {"barbarian": "Loader (LOAD\"*\",8, src/barbarian.asm): release = menu (la storia LORE, il manuale, il gioco START); debug = carica subito START",
        "start": "Avvio del gioco (src/start.asm): release = titolo, musica, PRESS SPACE; debug = solo i file. Carica GAME, LOBBY e l'elenco eroi",
        "lore": "LORE: START con LORE=1 (titolo + LDAT, PRESS SPACE) e la storia a scorrimento (src/lore/scroll.asm)",
        "help": "HELP, il manuale (src/help.asm, compresso ZX0 con il decompressore in testa: src/help/zx0sfx.asm): 5 pagine RLE da data/help.txt, ritaglio dell'HUD (tools/build/gen_help.py, docs/help.md); solo release",
        "ldat": "Dati della storia, compressi ZX0: charset, sprite, forme delle immagini, righe (tools/build/gen_lore.py, docs/intro.md)", "hl": "Elenco eroi (salvataggi, Krill)", "save-01": "Salvataggio dell'eroe 1", "save-02": "Salvataggio dell'eroe 2", "save-03": "Salvataggio dell'eroe 3", "save-04": "Salvataggio dell'eroe 4", "save-05": "Salvataggio dell'eroe 5", "menu1": "Modulo MENU, zona 1 (ZX0)", "menu2": "Modulo MENU, zona 2 (ZX0)", "menu3": "Modulo MENU, zona 3 (ZX0)",
        "game": "Il gioco compresso ZX0 (decompresso in $0400-$%04X)" % (L["code2_end"] - 1), "lobby": "Menu iniziale LOBBY ($C000)", "title": "Schermata del titolo (bitmap multicolor)",
        "twn1": "Villaggio del capitolo 1: tile e mappa (12/11: TWNc, oggi i 4 villaggi sono copie di out/gfx0.prg)", "twn2": "Villaggio del capitolo 2 (segnaposto: copia del villaggio 1)", "twn3": "Villaggio del capitolo 3 (segnaposto)", "twn4": "Villaggio del capitolo 4 (segnaposto)",
        "bossch1": "Mappa del piano del boss del capitolo 1, piano 5 (segnaposto, tools/build/gen_bossmap.py)", "bossch2": "Mappa del piano del boss del capitolo 2, piano 10 (segnaposto)", "bossch3": "Mappa del piano del boss del capitolo 3, piano 15 (segnaposto)", "menu": "Menu del villaggio (11/11, oggi la locanda): OVL2 + OVLT compressi ZX0 (tools/build/pack_menu.py). Prima apertura della locanda: tutto (OVLT a $C900, OVL2 a $F500); se manca solo OVL2 (il precaricamento l'ha sovrascritto) si legge solo la prima parte",
        "fmap": "Mappa della sala del trono, piano 20 (RLE, tools/build/gen_final.py): letta una volta nella cache sotto il KERNAL, dopo la mappa del villaggio",
        "jukebox": "Prova di brani ed effetti (solo disco di sviluppo, docs/musica.md)"}
SNDC = re.search(r"^; (0=.*)$", open(os.path.join(ROOT, "out", "music_tab.inc")).read(), re.M)
SNDN = dict(x.split("=", 1) for x in SNDC.group(1).split(", ")) if SNDC else {}
for i, f in enumerate(files):
    w = WHAT.get(f["name"], ("Grafica dei temi di dungeon (file %s)" % f["name"][3]) if f["name"].startswith("gfx") else "")
    if re.fullmatch(r"snd\w", f["name"]):
        w = "Brano %s (tools/build/songs.py, docs/musica.md)" % SNDN.get(f["name"][3].upper(), "?")
    by = len(f["data"]) if f["type"] != "rel" else len(f["chain"]) * 254
    extra = ""
    if f["type"] == "rel":
        extra = " &middot; record da %d B, %d blocchi dati + %d side sector" % (f["reclen"], len(f["chain"]), len(f["ss"]))
    P.append("<tr><td>%d</td><td><span class='sw' style='--c:%s'></span><code>%s</code></td><td>%s</td><td class='n'>%d</td><td class='n'>%d</td><td class='mono'>%d/%d</td><td>%s%s</td></tr>"
             % (i + 1, f["col"], h(f["name"]), f["type"], f["blocks"], by, f["t"], f["s"], h(w), extra))
used = sum(f["blocks"] for f in files)
P.append("<tr><th></th><th>Totale</th><th></th><th class='n'>%d</th><th></th><th></th><th>%d blocchi liberi su 664 (traccia 18 esclusa: directory e BAM)</th></tr></table></div>" % (used, free_blocks))

# --- 2. griglia tracce/settori
P.append("<h2>2. Tracce e settori</h2><p>Ogni quadrato e' un blocco da 256 B (254 di dati). Le tracce esterne (1-17) hanno 21 settori, le interne 17. "
         "Il DOS alloca partendo dalla traccia 18 verso l'esterno: i file vicini alla 18 si raggiungono con meno spostamenti della testina. "
         "Bordo scuro = side sector del file REL. Passa sopra un blocco per vedere file e posizione.</p><div class='wrap'><div class='grid'>")
P.append("<div class='tn'></div>" + "".join("<div class='tn' style='text-align:center'>%d</div>" % s for s in range(21)))
for t in range(1, 36):
    P.append("<div class='tn'>%d</div>" % t)
    for s in range(21):
        if s >= spt(t):
            P.append("<div class='na'></div>")
            continue
        if t == 18:
            what = "BAM" if s == 0 else ("directory" if (t, s) in dirblk else "")
            P.append("<div style='background:var(--sys)' title='18/%d %s'></div>" % (s, what) if what else "<div title='18/%d libero (riservato)'></div>" % s)
            continue
        if (t, s) in owner:
            i, k = owner[(t, s)]
            f = files[i]
            pos = (f["chain"].index((t, s)) + 1) if k == "d" else None
            tip = "%d/%d %s %s" % (t, s, f["name"], ("blocco %d/%d" % (pos, len(f["chain"]))) if pos else "side sector")
            if f["type"] == "rel" and pos:
                tip += " = record %d" % pos
            P.append("<div class='%s' style='background:%s' title='%s'></div>" % ("ss" if k == "s" else "", f["col"], h(tip)))
        else:
            P.append("<div title='%d/%d libero'></div>" % (t, s))
P.append("</div></div><p class='leg'>" + "".join("<span><span class='sw' style='--c:%s'></span>%s</span>" % (f["col"], h(f["name"])) for f in files)
         + "<span><span class='sw' style='--c:var(--sys)'></span>BAM / directory</span><span><span class='sw' style='--c:var(--free)'></span>libero</span></p>")

# --- 3. grafica
P.append("<h2>3. File di grafica</h2><p>Il charset del gioco ($A800) e' diviso in 4 quarti da 64 caratteri: ogni tile 16x16 usa un carattere per quarto "
         "(alto-sx, alto-dx, basso-sx, basso-dx). Per quarto: %d caratteri di tile al massimo + %d caratteri fissi (HUD, minimappa) = 64.</p>" % (NT, FSTRIP // 8))
fixed = 4 * FSTRIP // 8


def cbar(tilechars):
    free = 256 - fixed - tilechars
    return ("<div class='bar'><div style='--c:#3b7fc4;width:%.1f%%'>tile %d</div><div style='--c:#8a8a86;width:%.1f%%'>fissi %d</div>%s</div>"
            % (tilechars / 2.56, tilechars, fixed / 2.56, fixed, ("<div class='fr' style='width:%.1f%%'>liberi %d</div>" % (free / 2.56, free)) if free else ""))


tw = next(g for g in GFX if g["n"] == 0)
td = next(g for g in GFX if g["n"] == 1)
P.append("<div class='cards'><div class='card'><b class='t'>Villaggio (GFX0)</b><br>Caratteri del charset: <b>%d di 256</b>%s"
         "<span class='mut'>%d tile x 4 quarti + %d fissi: charset pieno.</span></div>"
         "<div class='card'><b class='t'>Dungeon (GFX1..GFXn)</b><br>Caratteri del charset: <b>%d di 256</b>%s"
         "<span class='mut'>%d tile x 4 + %d fissi. I %d liberi conservano i tile del villaggio (non usati nel dungeon): nel charset ci sarebbe posto per %d tile in piu' per tema (ma il file crescerebbe di 32 B a tile e i posti della cache, oggi 2016 B, andrebbero allargati).</span></div></div>"
         % (tw["chars"] + fixed, cbar(tw["chars"]), tw["tiles"], fixed, td["chars"] + fixed, cbar(td["chars"]), td["tiles"], fixed,
            256 - fixed - td["chars"], (256 - fixed - td["chars"]) // 4))
P.append("<div class='wrap'><table><tr><th>File</th><th>Uso</th><th class='n'>Byte</th><th class='n'>Blocchi</th><th>Contenuto (byte)</th><th class='n'>Caratteri tile</th><th class='n'>Glifi diversi</th><th class='n'>Sprite usati</th></tr>")
for g in GFX:
    parts = "<br>".join("%s: %d" % (h(a), b) for a, b in g["parts"])
    spr = "-" if not g["spr"] else "%d/%d + %d/%d" % (g["spr"][0][1], g["spr"][0][0], g["spr"][1][1], g["spr"][1][0])
    P.append("<tr><td><code>%s</code></td><td>%s</td><td class='n'>%d</td><td class='n'>%d</td><td>%s</td><td class='n'>%d/%d</td><td class='n'>%d</td><td class='n'>%s</td></tr>"
             % (g["f"]["name"].upper(), h(g["kind"]), g["size"], g["f"]["blocks"], parts, g["used"], g["chars"], g["uniq"], spr))
P.append("</table></div><p class='mut'>Caratteri tile = disegnati / posti nel file. Glifi diversi = caratteri distinti tra quelli disegnati (gli uguali si potrebbero condividere). "
         "Sprite usati = mostri base (4 mostri x 2 fotogrammi) + forti e boss finale (4 x 2 + 2). Lo sprite del boss finale e' in ogni tema, ma serve solo nel tema 8 (vedi TODO).</p>")
dun_t = ", ".join("%d %s" % (i, TILES.get(i, "?")[2:].lower()) for i in range(DSTRIP // 8))
P.append("<p class='mut'>Tile dei temi dungeon (0-%d): %s. Nel tema 8 (sala del trono) gli slot 12-13 sono stella e cerchio del pentacolo e lo slot 7 la leva. Temi con la stessa grafica condividono un file (oggi i temi 1-7).</p>" % (DSTRIP // 8 - 1, h(dun_t)))
P.append("<p class='mut'>Tile del villaggio (0-%d): %s.</p>" % (NT - 1, h(", ".join("%d %s" % (i, TILES.get(i, "?")[2:].lower()) for i in range(NT)))))

# --- 4. salvataggi (11/11, ramo fast-loader: plugin di save di Krill, un file per eroe + elenco)
lbl = {m.group(1): m.group(2) for m in re.finditer(r"^(\w+)\s*=\s*(\$?[0-9a-f]+)", open(os.path.join(ROOT, "out", "game.lbl")).read(), re.M)}
num = lambda v: int(v[1:], 16) if v.startswith("$") else int(v)
NFL = num(lbl["MAXLEVEL"]); STN = num(lbl["STASH_N"]); SVL = num(lbl["SV_LEN"]); HEL = num(lbl["HERO_LEN"]); LVS = num(lbl["LV_SLOT"])
svf = [f for f in files if f["name"].startswith("save-")]
hlf = next((f for f in files if f["name"] == "hl"), None)
P.append("<h2>4. Salvataggi: file HL e SAVE-01..05 (Krill)</h2>")
P.append("<p>Dal ramo <code>fast-loader</code> (11/11) i salvataggi usano il plugin di save di Krill's Loader: riscrive <b>solo file gia' presenti</b> "
         "e con lo <b>stesso numero di blocchi</b>, quindi la build li crea vuoti con la lunghezza giusta (<code>tools/build/mkdisk.sh</code>) e la directory non cambia mai. "
         "Ogni scrittura riscrive il file intero: il gioco legge il file, cambia la parte (eroe o un piano) e lo riscrive.</p>")
P.append("<table><tr><th>File</th><th class='n'>Byte</th><th class='n'>Blocchi</th><th>Contenuto</th></tr>"
         "<tr><td class='mono'>HL</td><td class='n'>%d</td><td class='n'>%s</td><td>Elenco eroi: versione, 5 byte \"eroe presente\", 5 nomi</td></tr>"
         "<tr><td class='mono'>SAVE-01..05</td><td class='n'>%d</td><td class='n'>%s</td><td>Un eroe: blocco dell'eroe (%d B) + %d piani da %d B</td></tr></table>"
         % (1 + 5 + 5 * 12, hlf["blocks"] if hlf else "?", SVL, svf[0]["blocks"] if svf else "?", HEL, NFL, LVS))
P.append("""<table><tr><th>Parte</th><th>Quando si scrive</th><th>Quando si legge</th></tr>
<tr><td class='mono'>save-0N: piano (offset %d + (piano&minus;1)&times;%d)</td><td>Lasciando il piano per le scale; dal menu RUN/STOP; prima di entrare in un altro piano se uno e' in memoria</td><td>Entrando in un piano con il suo bit in <code>c_vis</code></td></tr>
<tr><td class='mono'>save-0N: eroe (offset 0)</td><td>Menu RUN/STOP (salva o esci), creazione dell'eroe, locanda</td><td>"Continua" dal menu</td></tr>
<tr><td class='mono'>hl</td><td>Creazione o cancellazione di un eroe</td><td>START (prima del menu), ritorno al menu</td></tr></table>""" % (HEL, LVS))
P.append("<h3>File HL &middot; elenco eroi</h3><table><tr><th class='n'>Offset</th><th class='n'>Byte</th><th>Campo</th><th>Significato</th></tr>"
         "<tr><td class='n'>0</td><td class='n'>1</td><td><code>versione</code></td><td>save_version ($%02X): se diversa i salvataggi non sono compatibili</td></tr>"
         "<tr><td class='n'>1</td><td class='n'>5</td><td><code>slot_valid</code></td><td>1 byte per eroe 0..4: 1 = presente, 0 = posto libero</td></tr>"
         "<tr><td class='n'>6</td><td class='n'>60</td><td><code>nomi</code></td><td>5 nomi da 12 codici schermo (in memoria: <code>slot_name</code>, passo 16)</td></tr>"
         "</table>" % (SAVE_VER,))

P.append("<h3>SAVE-0N offset 0 &middot; blocco dell'eroe (copia esatta di CHRBLK a $9500)</h3><div class='wrap'><table><tr><th class='n'>Offset</th><th class='n'>Byte</th><th>Campo</th><th>Significato</th></tr>")
for a, name, kind, com, n in HERO:
    P.append("<tr><td class='n'>%d</td><td class='n'>%d</td><td><code>%s</code></td><td>%s</td></tr>" % (a, n, name, h(DESC.get(name, com))))
P.append("<tr><th></th><th class='n'>%d</th><th colspan='2'>byte (%d nel file: HERO_LEN). Oggetti: 12 posti (zaino 8, equipaggiamento 4), ognuno id + bonus + durabilita' + massimo (anelli: bonus = caratteristica; pila di pergamene: bonus = quantita', max 10); cintura: 4 pozioni; poi il baule della locanda (4 &times; %d byte).</th></tr></table></div>" % (CHRLEN, HEL, STN))

P.append("""<h3>Record dei piani &middot; formato compatto (lv_put / lv_get)</h3>
<p>Il piano <b>non</b> e' salvato per intero: entrando si rigenera tutto dal seed (mappa, mostri, bauli del piano) e poi si applicano queste differenze, in ordine.
Un posto fisso per piano nel file dell'eroe (11/11).</p>
<div class='wrap'><table><tr><th>Campo</th><th class='n'>Byte</th><th>Formato</th></tr>
<tr><td>Piano</td><td class='n'>1</td><td>numero del piano: controllo, se non coincide lo stato e' ignorato</td></tr>
<tr><td>Partita</td><td class='n'>2</td><td>numero della partita (9 bit di <code>c_game</code>) in cui il piano e' stato salvato: se e' un'altra, i mostri tornano tutti vivi e i bauli del piano chiusi (si tengono la nebbia; il baule del boss si scarta)</td></tr>
<tr><td>Numero di mostri</td><td class='n'>1</td><td><code>lb_cnt</code> al salvataggio (informativo: si tengono i mostri rigenerati, le evocazioni del boss finale no)</td></tr>
<tr><td>Mostri vivi</td><td class='n'>4</td><td>1 bit per mostro (bit 7 del primo byte = mostro 0); morto = 0. <b>Le posizioni non si salvano</b>: i vivi ripartono dalla casella di partenza</td></tr>
<tr><td>Bauli del piano tolti</td><td class='n'>1</td><td>bit <i>i</i> = 1 se il baule del piano nel posto <i>i</i> (0..3, <code>ch_t</code> bit 4) non c'e' piu' (aperto)</td></tr>
<tr><td>Baule del boss</td><td class='n'>1 o 12</td><td>0 = nessuno (boss vivo o baule aperto); 1 + X, Y, <code>ch_t</code>, 4 &times; oggetto, 4 &times; bonus. Finche' non e' aperto (<code>ch_t</code> bit 3): primo oggetto = numero di oggetti, primo bonus = chestLevel; oro e oggetti si generano alla prima apertura</td></tr>
<tr><td>Nebbia</td><td class='n'>72</td><td>settori 2&times;2 caselle: 24 righe &times; 3 byte (bit 7 del primo byte = settore 0); settore esplorato se lo e' almeno una delle sue 4 caselle</td></tr>
<tr><th>Totale</th><th class='n'>82 / 93</th><th>nel suo posto di LV_SLOT byte</th></tr></table></div>
<p class='mut'>Non salvati: posizione, vita, armatura, danno dei mostri (ricalcolati da <code>init_monsters_rt</code>); bauli aperti e tesori lasciati dai mostri (spariscono cambiando piano).
In memoria lo stato completo e' LVLBLK ($9800); con un portale o alla morte resta in STASH ($D000) con le posizioni dei mostri e va su disco solo entrando in un altro piano o dal menu RUN/STOP.</p>""")

P.append("<p class='mut'>Tempi dei salvataggi con Krill: <a href='../docs/prestazioni.md'>docs/prestazioni.md</a>.</p>")
P.append("</main></body></html>")
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
open(OUT, "w").write("\n".join(P))
print("scritto", OUT)
