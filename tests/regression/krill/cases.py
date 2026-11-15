"""Krill's Loader r194 (11/11, fast-loader branch, docs/FastLoader.md): START installs the loader, the resident sits at
$0200, the disk has the pre-allocated save files with the right number of blocks, a hero saved with the plugin comes
back the same from disk, the hero list (file hl) is rewritten by the plugin. One VICE session."""
import os, re
from c64test import test, check
from lib.c64 import OUT, Game
from lib.play import new_game

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def blocks(path):
    """file name -> blocks of a d64 directory"""
    d = open(path, "rb").read()
    spt = [21] * 17 + [19] * 7 + [18] * 6 + [17] * 5
    off = lambda t, s: (sum(spt[:t - 1]) + s) * 256
    out, t, s = {}, 18, 1
    while t:
        b = d[off(t, s):off(t, s) + 256]
        for i in range(8):
            e = b[i * 32:(i + 1) * 32]
            if e[2] & 7:
                out[e[5:21].split(b"\xa0")[0].decode("latin1").lower()] = e[30] | e[31] << 8
        t, s = b[0], b[1]
    return out


@test("KRILL-10", "START installs Krill: resident code at $0200 as out/work/krill/loader.prg (but its variables), LDFLAGS used")
def krill_resident(ctx):
    g = ctx["g"]
    res = open(os.path.join(OUT, "krill", "loader.prg"), "rb").read()[2:]
    cur = g.mem(0x0200, len(res))
    diff = [0x200 + i for i, (a, b) in enumerate(zip(cur, res)) if a != b]
    check(len(diff) <= 8 and cur[:32] == list(res[:32]), "resident differs at %s" % [hex(a) for a in diff[:10]])
    check(g.b(0x8e) == 0, "LDFLAGS $8E = %d after the menu (expected 0: consumed)" % g.b(0x8e))


@test("KRILL-11", "disk: hl (1 block), ksave, save-01..05 with SV_LEN + 2 bytes (9 blocks), barbarian first")
def krill_disk(ctx):
    L = ctx["g"].L
    b = blocks(os.path.join(OUT, "disk.d64"))
    names = list(b)
    want = -(-(L["SV_LEN"] + 2) // 254)
    check(names[0] == "barbarian", "first file %s" % names[0])
    check(b.get("hl") == 1 and "ksave" in b, "hl %s, ksave %s" % (b.get("hl"), b.get("ksave")))
    for s in range(1, 6):
        check(b.get("save-0%d" % s) == want, "save-0%d: %s blocks (expected %d)" % (s, b.get("save-0%d" % s), want))


@test("KRILL-12", "new hero: hl rewritten by the plugin (version, present, name); hero file: save_char then load_char gives the same hero")
def krill_save(ctx):
    g = ctx["g"]; L = g.L
    new_game(g); g.frames(3)
    g.call_keep(L["hdr_read"], tmax=60)
    h = g.mem(L["hdrbuf"], 18)
    check(h[0] == L["SAVE_VER"] and h[1] == 1 and h[6:18] == g.mem(L["c_name"], 12), "hl %s" % h)
    g.poke16(L["c_gold"], 4321)
    s0 = g.mem(L["CHRBLK"], L["HERO_LEN"])
    g.call_keep(L["save_char"], tmax=90)
    g.fill(L["CHRBLK"], L["CHRBLK"] + L["HERO_LEN"] - 1, 0)
    g.call_keep(L["load_char"], tmax=90)
    s1 = g.mem(L["CHRBLK"], L["HERO_LEN"])
    check(s1 == s0, "hero from disk differs at %s" % [i for i, (a, b) in enumerate(zip(s0, s1)) if a != b][:8])
    check(g.w16(L["c_gold"]) == 4321, "gold %d" % g.w16(L["c_gold"]))


@test("KRILL-13", "no KERNAL disk call left in GAME, LOBBY, MENU and START (listing scan: after the install the drive does not answer the KERNAL)")
def krill_no_kernal(ctx):
    vec = ("ffba", "ffbd", "ffc0", "ffc3", "ffc6", "ffc9", "ffcc", "ffcf", "ffd2", "ffd5", "ffd8", "ffb1", "ff93",
           "ffa8", "ffae", "ffb7", "ffe4")
    pat = re.compile(r"^\.\w+\s+(?:\w+\s+)?(?:20|4c) (\w\w) ff\s", re.M)
    for f in ("game", "lobby", "menu", "start"):
        lst = open(os.path.join(OUT, f + ".lst")).read()
        if f == "start":        # (12/11) kr_fail and the trampoline: only when the install failed (KRILL-14), KERNAL allowed
            i = lst.find("kr_fail:"); j = lst.find("load_all:", i)
            lst = lst[:i] + lst[j:] if i >= 0 and j > i else lst
            k = lst.find("tramp_run:")
            lst = lst[:k] if k >= 0 else lst
        if f == "game":         # (16/11) the trampoline of "back to main menu" (backmenu.asm): runs only after krill_uninstall, KERNAL allowed
            i = lst.find("tramp_run:"); j = lst.find("tramp_len = * - tramp_img", i)
            lst = lst[:i] + lst[j:] if i >= 0 and j > i else lst
        bad = sorted({"$ff" + m.group(1) for m in pat.finditer(lst) if "ff" + m.group(1) in vec})
        check(not bad, "%s.lst calls %s" % (f, bad))
