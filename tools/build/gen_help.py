#!/usr/bin/env python3
"""HELP (il manuale nel menu del loader, solo release): pagine da data/help.txt + ritaglio dell'HUD.

  tools/build/gen_help.py          -> out/help.inc (charset: font della UI 0-63 + glifi dell'HUD da 64, pagine RLE)
                                 + anteprima out/atlas/help.png
  tools/build/gen_help.py --check  -> rifa la fotografia in out/ e la confronta con data/help_hud.json (test della release)
  tools/build/gen_help.py --snap   -> data/help_hud.json: fotografia dell'HUD vero (build di test TESTUI=28, VICE):
                                 righe 20-23 dello schermo HUD, colori, i glifi usati del charset del tema, $D022/$D023.
                                 Da rifare quando cambia la grafica dell'HUD (tests/test_help.py controlla che i glifi
                                 coincidano ancora con il charset del gioco). Poi ricompila la build normale.

Formato di data/help.txt: una pagina per sezione "=== titolo"; ogni riga di testo e' una riga dello schermo
(dalla riga 2; colonne 1..38). [testo] = giallo (tasti), {testo} = ciano (note). "@hud" = il ritaglio
dell'HUD (4 righe, colonne 1..38) a partire da quella riga. Righe 0 (titolo) e 24 (tasti dell'help): automatiche.
"""
import json, os, re, socket, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "memory-map", "simulators")]
from vice_rom import ROM_ARGS, XRUN  # noqa: E402  (x64sc: -default + tutte le ROM da roms/)
SNAP = os.path.join(ROOT, "data", "help_hud.json")
COL_TXT, COL_KEY, COL_NOTE, COL_TITLE = 1, 7, 3, 7       # colori < 8: caratteri in alta risoluzione (schermo multicolore)
HUD_X0, HUD_X1 = 1, 39                                     # colonne 1..38 (l'HUD del gioco e' a 38 colonne)
FOOT = "fire: next  left: back  run/stop: menu"


def lbl(path):
    return {m.group(1): int(m.group(2), 16) for m in re.finditer(r"^(\w+)\s*=\s*\$([0-9a-f]+)", open(path).read(), re.M)}


# ------------------------------------------------------------------ fotografia dell'HUD (VICE)
def snap(path=SNAP):
    env = dict(os.environ, NOKEYS="1", TESTUI="28", TESTCL="15", TESTLVL="2", TESTSP="1")
    subprocess.run(["tools/build/asm.sh", "test"], cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["tools/build/mkdisk.sh"], cwd=ROOT, check=True)
    L = lbl(os.path.join(ROOT, "out", "game.lbl"))
    vice = subprocess.Popen(XRUN + ["x64sc", "-silent", "-sounddev", "dummy"] + ROM_ARGS + ["-warp", "-8",
                             os.path.join(ROOT, "out", "disk.d64"), "-remotemonitor"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        s = None
        for _ in range(40):
            try:
                s = socket.create_connection(("127.0.0.1", 6510)); break
            except OSError:
                time.sleep(0.25)
        s.settimeout(1)
        time.sleep(3)

        def cmd(c, w=0.4):
            s.sendall((c + "\n").encode()); time.sleep(w); out = ""
            try:
                while True:
                    d = s.recv(65536).decode(errors="ignore")
                    if not d: break
                    out += d
                    if len(d) < 65536: break
            except Exception:
                pass
            return out

        def mem(a, n):
            out = []
            for ln in cmd("m %04x %04x" % (a, a + n - 1), 0.6).splitlines():
                m = re.match(r">C:([0-9a-f]{4})\s+((?:[0-9a-f]{2}\s+)+)", ln)
                if m: out += [int(x, 16) for x in m.group(2).split()]
            return out[:n]

        cmd("", 0.3)
        cmd('l "%s" 0' % os.path.join(ROOT, "out", "start.prg"), 3)    # (11/11) START: installa Krill, GAME dal disco
        cmd("break %04x" % L["main_loop"], 0.2)
        s.sendall(b"g 080d\n"); t0 = time.time(); buf = ""
        while time.time() - t0 < 60 and "Stop on" not in buf:
            try: buf += s.recv(65536).decode(errors="ignore")
            except Exception: pass
        for _ in range(39):                 # 40 giri del ciclo principale (uno per fotogramma): HUD disegnato,
            s.sendall(b"x\n"); t0 = time.time(); buf = ""      # un pannello per fotogramma; sempre lo stesso
            while time.time() - t0 < 10 and "Stop on" not in buf:   # istante (fotografia ripetibile)
                try: buf += s.recv(65536).decode(errors="ignore")
                except Exception: pass
        cmd("del", 0.2)
        scr = mem(L["SCR_H"] + 800, 160)
        col = [c & 15 for c in mem(0xd800 + 800, 160)]
        vic = mem(0xd022, 2)
        cs = mem(0xa800, 2048)
    finally:
        vice.terminate()
        subprocess.run(["pkill", "x64sc"], stderr=subprocess.DEVNULL)
    for x in range(29, 32):             # icone degli oggetti consumati: lampeggiano rosso/giallo, nel ritaglio rosse
        if col[40 + x] == 7:
            col[40 + x] = 2
    used = sorted(set(scr))
    data = {"note": "HUD del gioco (TESTUI=28, livello 15, piano 2): righe 20-23 dello schermo HUD; tools/build/gen_help.py --snap",
            "d022": vic[0] & 15, "d023": vic[1] & 15, "screen": scr, "color": col,
            "glyphs": {str(c): cs[c * 8:c * 8 + 8] for c in used}}
    json.dump(data, open(path, "w"), indent=0)
    subprocess.run(["tools/build/asm.sh"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)     # di nuovo la build normale
    subprocess.run(["tools/build/mkdisk.sh"], cwd=ROOT, check=True)
    print("%s: %d glifi, $D022=%d $D023=%d" % (os.path.relpath(path, ROOT), len(used), data["d022"], data["d023"]))


# ------------------------------------------------------------------ pagine
# icone della UI in piu' (08/11 sera, regola della moneta e glifi dell'equipaggiamento): in data/help.txt si
# scrivono con questi caratteri; vanno nel charset dopo i glifi dell'HUD (codice 64 + glifi HUD + posizione).
# Lo scudo e' gia' nel font a 64 caratteri (codice 35 = '#'). Colore fisso (hires, < 8).
EXTRA = [("\u00a4", 92, 7), ("\u2020", 97, 1), ("\u2021", 98, 1), ("\u00b0", 99, 7)]   # moneta, spada, armatura, anello
EXTRA_CODE = {}


def scode(ch):
    if ch in EXTRA_CODE: return EXTRA_CODE[ch]
    if "a" <= ch <= "z": return ord(ch) - 96
    if ch == "@": return 0
    o = ord(ch)
    if 32 <= o < 64: return o
    raise SystemExit("help.txt: carattere non stampabile %r" % ch)


def parse_pages():
    pages = []
    for ln in open(os.path.join(ROOT, "data", "help.txt")).read().split("\n"):
        if ln.startswith("#"):
            continue
        if ln.startswith("=== "):
            pages.append({"title": ln[4:].strip(), "lines": []}); continue
        if pages:
            pages[-1]["lines"].append(ln.rstrip())
    for p in pages:
        while p["lines"] and not p["lines"][-1]:
            p["lines"].pop()
    return pages


def build():
    hud = json.load(open(SNAP))
    glyph_codes = sorted(int(k) for k in hud["glyphs"])
    remap = {c: 64 + i for i, c in enumerate(glyph_codes)}
    for k, (ch, code, colr) in enumerate(EXTRA):
        EXTRA_CODE[ch] = 64 + len(glyph_codes) + k
    if 64 + len(glyph_codes) + len(EXTRA) > 256:
        raise SystemExit("troppi glifi dell'HUD")
    pages = parse_pages()
    screens = []
    for n, p in enumerate(pages):
        scr = [32] * 1000; col = [COL_TXT] * 1000

        def put(x, y, text, c):
            for i, ch in enumerate(text):
                if 0 <= x + i < 40:
                    scr[y * 40 + x + i] = scode(ch); col[y * 40 + x + i] = c

        title = p["title"]
        put((40 - len(title)) // 2, 0, title, COL_TITLE)
        tag = "%d/%d" % (n + 1, len(pages))
        put(39 - len(tag), 0, tag, COL_NOTE)
        put(1, 24, FOOT, COL_NOTE)
        y = 1
        for ln in p["lines"]:
            y += 1
            if ln.strip() == "@hud":
                for r in range(4):
                    for x in range(HUD_X0, HUD_X1):
                        scr[(y + r) * 40 + x] = remap[hud["screen"][r * 40 + x]]
                        col[(y + r) * 40 + x] = hud["color"][r * 40 + x]
                y += 3
                continue
            if y > 23:
                raise SystemExit("help.txt: pagina '%s' troppo lunga" % title)
            x = 1; c = COL_TXT
            for ch in ln:
                if ch == "[": c = COL_KEY; continue
                if ch == "{": c = COL_NOTE; continue
                if ch in "]}": c = COL_TXT; continue
                if x > 38 and ch != " ":
                    raise SystemExit("help.txt: riga oltre la colonna 38: %r" % ln)
                if x < 40:
                    put(x, y, ch, next((e[2] for e in EXTRA if e[0] == ch), c))
                x += 1
        screens.append((scr, col))
    return hud, glyph_codes, pages, screens


def rle(seq):                         # coppie (conteggio 1..255, valore); conteggio 0 = fine
    out = []; i = 0
    while i < len(seq):
        j = i
        while j < len(seq) and seq[j] == seq[i] and j - i < 255:
            j += 1
        out += [j - i, seq[i]]; i = j
    return out + [0]


def preview(hud, glyph_codes, screens):
    try:
        from PIL import Image
    except ImportError:
        return
    full = open(os.path.join(ROOT, "out", "gfx", "uifont.bin"), "rb").read()
    cs = bytearray(2048); cs[:512] = full[:512]
    for i, c in enumerate(glyph_codes):
        cs[(64 + i) * 8:(64 + i) * 8 + 8] = bytes(hud["glyphs"][str(c)])
    for k, (ch, code, colr) in enumerate(EXTRA):
        a = (64 + len(glyph_codes) + k) * 8
        cs[a:a + 8] = full[code * 8:code * 8 + 8]
    pal = [(0, 0, 0), (255, 255, 255), (136, 57, 50), (103, 182, 189), (139, 63, 150), (85, 160, 73), (64, 49, 141),
           (191, 206, 114), (139, 84, 41), (87, 66, 0), (184, 105, 98), (80, 80, 80), (120, 120, 120), (148, 224, 137),
           (120, 105, 196), (159, 159, 159)]
    im = Image.new("RGB", (320 * len(screens) + 8 * (len(screens) - 1), 200), (40, 40, 40))
    for n, (scr, col) in enumerate(screens):
        ox = n * 328
        for p in range(1000):
            x0, y0 = (p % 40) * 8, (p // 40) * 8; c = col[p]
            for r in range(8):
                b = cs[scr[p] * 8 + r]
                if c < 8:
                    for k in range(8):
                        im.putpixel((ox + x0 + k, y0 + r), pal[c] if b & (128 >> k) else pal[0])
                else:
                    m = [pal[0], pal[hud["d022"]], pal[hud["d023"]], pal[c & 7]]
                    for k in range(4):
                        v = m[(b >> (6 - 2 * k)) & 3]
                        im.putpixel((ox + x0 + 2 * k, y0 + r), v); im.putpixel((ox + x0 + 2 * k + 1, y0 + r), v)
    os.makedirs(os.path.join(ROOT, "out", "atlas"), exist_ok=True)
    im.save(os.path.join(ROOT, "out", "atlas", "help.png"))


def main():
    if "--snap" in sys.argv:
        snap(); return
    if "--check" in sys.argv:           # test della release: la fotografia e' ancora uguale all'HUD del gioco?
        tmp = os.path.join(ROOT, "out", "help_hud_now.json")
        snap(tmp)
        a, b = json.load(open(SNAP)), json.load(open(tmp))
        keys = ("d022", "d023", "screen", "color", "glyphs")
        bad = [k for k in keys if a[k] != b[k]]
        print("HUD dell'help: " + ("uguale al gioco" if not bad else "DIVERSO (%s): rifare tools/build/gen_help.py --snap" % ", ".join(bad)))
        sys.exit(1 if bad else 0)
    hud, glyph_codes, pages, screens = build()
    o = ["; generato da tools/build/gen_help.py (data/help.txt, data/help_hud.json): non modificare",
         "HELP_NP = %d" % len(pages), "HELP_D022 = %d" % hud["d022"], "HELP_D023 = %d" % hud["d023"],
         "HELP_NG = %d" % (len(glyph_codes) + len(EXTRA)), "help_glyphs"]
    for c in glyph_codes:
        o.append("        .byte " + ",".join("$%02x" % b for b in hud["glyphs"][str(c)]))
    full = open(os.path.join(ROOT, "out", "gfx", "uifont.bin"), "rb").read()
    for ch, code, colr in EXTRA:                    # icone della UI (moneta, spada, armatura, anello)
        o.append("        .byte " + ",".join("$%02x" % b for b in full[code * 8:code * 8 + 8]))
    tot = 0
    for n, (scr, col) in enumerate(screens):
        d = rle(scr) + rle(col); tot += len(d)
        o.append("help_p%d" % n)
        for i in range(0, len(d), 24):
            o.append("        .byte " + ",".join(str(b) for b in d[i:i + 24]))
    o.append("help_plo .byte " + ",".join("<help_p%d" % n for n in range(len(pages))))
    o.append("help_phi .byte " + ",".join(">help_p%d" % n for n in range(len(pages))))
    open(os.path.join(ROOT, "out", "help.inc"), "w").write("\n".join(o) + "\n")
    preview(hud, glyph_codes, screens)
    print("help: %d pagine, %d B di pagine (RLE), %d glifi dell'HUD" % (len(pages), tot, len(glyph_codes)))


if __name__ == "__main__":
    main()
