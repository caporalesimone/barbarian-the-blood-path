#!/usr/bin/env python3
"""Combat arena: the real game code (ARENA build) in VICE, driven from here (11/11, G3: on tests/lib/c64.py).

Command line (examples):
  tools/vice/arena.py --lvl 3 --plvl 3 --weapon sword+1 --armor chain_mail --shield small_shield --monster skeleton --fights 20
  tools/vice/arena.py --lvl 9 --plvl 9 --weapon viking_sword --ring silver+2 --monster demon --monster demon --potions red:2,yellow:2 --pot 0.4
  (ring: +1 STR, +2 DEX, +3 CON)
  tools/vice/arena.py --lvl 5 --plvl 5 --weapon sword --dur 40 --monster skeleton --fights 50   (weapon wear)
  tools/vice/arena.py ... --json          (results in JSON)      --csv results.csv  (one row appended)

From Python (several scenarios in the same VICE session, without restarting it):
  from arena import Arena
  with Arena() as a:
      r = a.run(lvl=3, plvl=3, weapon="sword", monsters=["skeleton"], fights=20)

Phase 1: hero and monsters next to each other (automatic positions), a still bot that turns and attacks (bot="stand").
bot="approach": walks to the nearest monster; bot="adds" (24/11): walks to the other monsters first and to the boss last
(summons, Mother Stitch's fetishes), going around what blocks it (src/test/arena.asm BOT 2).
(23/11) Levels with their own code (the boss levels of chapters 1-3, level 20): the same code as the game (out/work/arena_ovl_*.prg,
assembled with the labels of the ARENA build at OVP_AT = $F4E0) is loaded before every fight, so its state starts again each
time as when the hero enters the level; those series are played one fight at a time with seed + k (ovl=False: without it).
Needs the build: ./build.sh (or tools/build/asm.sh) makes out/work/arena_game.prg and out/work/arena.prg."""
import argparse, csv, json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "out", "work")
sys.path.insert(0, os.path.join(ROOT, "tests")); from lib import c64 as C64  # noqa: E402,E702


def labels(fn):
    d = {}
    for l in open(os.path.join(OUT, fn)):
        m = re.match(r"\s*(\w+)\s*=\s*\$([0-9a-fA-F]+)", l)
        if m:
            d[m.group(1)] = int(m.group(2), 16)
            continue
        m = re.match(r"\s*(\w+)\s*=\s*(\d+)\s*$", l)
        if m:
            d[m.group(1)] = int(m.group(2))
    return d


G = labels("arena_game.lbl")
A = labels("arena.lbl")
ITEMS = {k[2:].lower(): v for k, v in G.items() if k.startswith("I_") and k not in ("I_POTR", "I_POTY", "I_POTV", "I_SCROLL", "I_START")}
MONS = {k[2:].lower(): v for k, v in G.items() if k.startswith("M_")}
SKILLS = {"slash": 1, "whirlwind": 2, "battle_cry": 4, "smash": 8, "rage": 16, "frenzy": 32}
ALLSK = ("slash", "whirlwind", "battle_cry", "smash", "rage", "frenzy")
MAXLEVEL = G["MAXLEVEL"]
PAR, RES, LOG = A["PAR"], A["RES"], A["LOG"]


def theme(lvl):
    """level -> number of the GFXn file (like lvl_theme in the game)"""
    c = (lvl - 1) // 5 + 1                  # 2c-1 dungeon, 2c boss (ultimo piano del capitolo e piano finale)
    return 2 * G["CHAPTERS"] if lvl == MAXLEVEL else (2 * c if (lvl - 1) % 5 == 4 else 2 * c - 1)


def sadd(plvl):
    """stat points spent by the reference hero at level plvl (11/11: rules.yaml player.reference_alloc) -> [str, dex, con]"""
    sys.path.insert(0, os.path.join(ROOT, "tools", "simulators"))
    import rules as RU
    al = RU.R["player"]["reference_alloc"][:RU.pg_points(min(plvl, MAXLEVEL))]
    return [al.count(k) for k in ("str", "dex", "con")]


def item(spec):
    """'sword+2' -> (id, 2); '' -> (0, 0)"""
    if not spec:
        return 0, 0
    name, _, b = spec.partition("+")
    if name not in ITEMS:
        sys.exit("unknown item: %s (valid: %s)" % (name, ", ".join(sorted(ITEMS))))
    return ITEMS[name], int(b or 0)


class Arena:
    def __init__(self, warp=True, show=False):
        self.warp, self.show = warp, show

    def __enter__(self):
        subprocess.run(["pkill", "x64sc"], stderr=subprocess.DEVNULL)
        self.v = C64.Vice(warp=self.warp, show=self.show)          # (11/11, G3: the shared VICE client)
        self.v.load(os.path.join(OUT, "arena_game.prg"))
        self.v.load(os.path.join(OUT, "arena.prg"))
        self.theme = None
        self.ran = False
        self.v.brk(A["ar_halt"])
        return self

    def __exit__(self, *a):
        self.v.close()

    def cmd(self, c, w=None):
        """a monitor command, answer up to the prompt (w: ignored, kept for the old scripts)"""
        return self.v.cmd(c)

    def mem(self, a, n):
        return self.v.mem(a, n)

    def go(self, lim=30):
        """continue to the next stop; False if none in lim seconds"""
        try:
            self.v.go(lim); return True
        except C64.MonitorError:
            return False

    def load_theme(self, t):
        if self.theme != t:
            self.v.cmd("bank ram")
            self.v.load(os.path.join(ROOT, "out", "work", "gfx", "gfx%d.prg" % t))
            self.v.cmd("bank cpu")
            self.theme = t

    def run(self, lvl=1, plvl=1, weapon="dagger", armor="", shield="", ring="", potions=None, monsters=("fallen",),
            boss=0, pos=None, ppos=(0, 0), fights=10, maxsec=120, fast=True, skills=ALLSK,
            pot=0.0, wake=True, bot="stand", timeout=None, dur=0, seed=0x1234, ovl=True):
        assert 1 <= lvl <= MAXLEVEL and 1 <= plvl <= 20 and 1 <= len(monsters) <= 8 and 1 <= fights <= 255
        assert weapon, "the hero always has a weapon"
        eq = [item(weapon), item(armor), item(shield), item(ring)]
        # (21/11 evening, affixes) magic +N -> prefix id (MAG_W / MAG_A), ring stat (1 STR, 2 DEX, 3 CON) -> suffix id (RSX_)
        metal = {"copper": 1, "silver": 2, "gold": 3}
        rname = ring.partition("+")[0]
        eq = [(i, G["MAG_%s%d" % ("W" if k == 0 else "A", b)] if b and k < 3 else
               (G["RSX_%d%d" % (b, metal[rname])] if b and k == 3 else 0)) for k, (i, b) in enumerate(eq)]
        bt, bn = [], [0] * 4                # belt: 4 slots, one potion each
        for name, n in (potions or {}).items():
            bt += [item(name)[0]] * n
        assert len(bt) <= 4, "4 potions at most in the belt"
        bt += [0] * (4 - len(bt))
        mt = []
        for m in monsters:
            if m not in MONS:
                sys.exit("unknown monster: %s (valid: %s)" % (m, ", ".join(sorted(MONS))))
            mt.append(MONS[m])
        mx = [p[0] for p in (pos or [])] + [0] * 8
        my = [p[1] for p in (pos or [])] + [0] * 8
        maxf = min(65535, int(maxsec * 50))
        sk = sum(SKILLS[s] for s in skills)
        assert 0 <= dur <= 255
        bn = [dur] + sadd(plvl)             # PAR+14 = PAR_DUR (weapon durability), PAR+15..17 = PAR_SADD (stat points)
        p = ([lvl, plvl] + [e[0] for e in eq] + [e[1] for e in eq] + bt + bn + [len(mt), boss] + (mt + [0] * 8)[:8]
             + mx[:8] + my[:8] + [ppos[0], ppos[1], fights, maxf & 255, maxf >> 8, 1 if fast else 0, sk,
                                 min(255, int(pot * 256)), 1 if wake else 0, {"stand": 0, "approach": 1, "adds": 2}[bot]])
        p += [seed & 255, seed >> 8]
        assert len(p) == A["PAR_LEN"], len(p)
        ov = self.overlay(lvl) if ovl else None
        if ov and fights > 1:               # (23/11) the level code keeps its state in its own bytes: one fight at a time
            args = dict(lvl=lvl, plvl=plvl, weapon=weapon, armor=armor, shield=shield, ring=ring, potions=potions, monsters=monsters,
                        boss=boss, pos=pos, ppos=ppos, maxsec=maxsec, fast=fast, skills=skills, pot=pot, wake=wake, bot=bot,
                        timeout=timeout, dur=dur, ovl=ovl)
            rs = [self.run(fights=1, seed=(seed + 7919 * k) & 0xffff or 1, **args) for k in range(fights)]
            return merge(rs, fights)
        if self.ran:                        # the tail of the PRG (fixed graphics, generator copied under the I/O) is
            self.v.load(os.path.join(OUT, "arena_game.prg"))      # dead data after `start`: load it again
        self.ran = True
        self.load_theme(theme(lvl))
        if ov:                              # after the theme: the code goes where the tail of the theme was
            self.v.cmd("bank ram")          # under the KERNAL, like the theme
            self.v.load(ov)
            self.v.cmd("bank cpu")
            self.v.poke(G["ovp_ok"], 1)
        self.v.poke(PAR, *p)
        t0 = time.time()
        lim = timeout or (60 + fights * maxsec * (0.25 if fast else 1.2))
        self.v.pc(G["start"])
        if not self.go(lim):
            raise RuntimeError("arena: time out (%d real s)" % lim)
        wall = time.time() - t0
        r = self.mem(RES, A["RES_LEN"])
        lg = self.mem(LOG, 4 * min(fights, A["LOG_N"]))
        w24 = lambda o: r[o] | r[o + 1] << 8 | r[o + 2] << 16
        w16 = lambda o: r[o] | r[o + 1] << 8
        n = r[0]
        res = dict(fights=n, win=r[1], lose=r[2], timeout=r[3], frames=w24(4), hp_end=w16(7), xp=w24(9), kills=w16(12),
                   dealt=w24(14), taken=w24(17), healed=w16(20), potions=w16(22),
                   pg=dict(hpmax=w16(24), att=r[26], ac=r[27], dice="%dd%d+%d" % (r[28], r[29], r[30]), rate=r[31]),
                   m0=dict(hp=w16(32), ac=r[34], att=r[35]), status=r[36], weapon_dur=r[37], weapon_end=r[38], wall_s=round(wall, 1),
                   log=[dict(result={1: "win", 2: "lose", 3: "timeout"}.get(lg[i], "?"), frames=lg[i + 1] | lg[i + 2] << 8,
                             hp_end=lg[i + 3]) for i in range(0, len(lg), 4)])
        res["avg_sec"] = round(res["frames"] / max(1, n) / 50, 2)
        res["params"] = dict(lvl=lvl, plvl=plvl, weapon=weapon, armor=armor, shield=shield, ring=ring, potions=potions or {},
                             monsters=list(monsters), boss=boss, fights=fights, maxsec=maxsec, skills=list(skills), pot=pot,
                             wake=wake, bot=bot, fast=fast, dur=dur)
        return res

    @staticmethod
    def overlay(lvl):
        """(23/11) the code of the level for the arena (theme.asm OVP_AT): boss level of chapter c = 1..3 (5c), level 20; else None"""
        if lvl == MAXLEVEL:
            f = "arena_ovl_final.prg"
        elif lvl % 5 == 0:
            f = "arena_ovl_boss%d.prg" % (lvl // 5)
        else:
            return None
        f = os.path.join(OUT, f)
        return f if os.path.exists(f) else None


def merge(rs, fights):
    """(23/11) results of single-fight runs -> one series (sums; hero and monster 0 from the last one)"""
    r = dict(rs[-1])
    for k in ("fights", "win", "lose", "timeout", "frames", "hp_end", "xp", "kills", "dealt", "taken", "healed", "potions"):
        r[k] = sum(x[k] for x in rs)
    r["wall_s"] = round(sum(x["wall_s"] for x in rs), 1)
    r["log"] = [x["log"][0] for x in rs][:A["LOG_N"]]
    r["avg_sec"] = round(r["frames"] / max(1, r["fights"]) / 50, 2)
    r["params"] = dict(rs[0]["params"], fights=fights)
    return r


def summary(r):
    p = r["params"]
    n = max(1, r["fights"])
    s = ["Arena: level %d, hero level %d, %s%s%s against %s (%d fights, %.1f real s)" % (
        p["lvl"], p["plvl"], p["weapon"], (" + " + p["armor"]) if p["armor"] else "", (" + " + p["shield"]) if p["shield"] else "",
        ", ".join(p["monsters"]), r["fights"], r["wall_s"]),
        "  hero: hp %d, ATT +%d, AC %d, damage %s, rate %d frames" % tuple(r["pg"][k] for k in ("hpmax", "att", "ac", "dice", "rate")),
        "  monster 1: hp %d, AC %d, ATT +%d" % (r["m0"]["hp"], r["m0"]["ac"], r["m0"]["att"]),
        "  result: won %d (%.0f%%), lost %d, timed out %d" % (r["win"], 100 * r["win"] / n, r["lose"], r["timeout"]),
        "  average length %.1f s of game; average hp left %.1f; damage dealt %.1f / taken %.1f per fight" % (
            r["avg_sec"], r["hp_end"] / n, r["dealt"] / n, r["taken"] / n),
        "  potions %d (hp healed %d); experience %d; monsters killed %d" % (r["potions"], r["healed"], r["xp"], r["kills"])]
    if p.get("dur"):
        s.append("  weapon: durability %d -> %d%s" % (p["dur"], r["weapon_dur"], " (BROKEN: no damage)" if r["weapon_dur"] == 0 else ""))
    return "\n".join(s)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lvl", type=int, default=1, help="level 1..%d (monster difficulty)" % MAXLEVEL)
    ap.add_argument("--plvl", type=int, default=1, help="hero level 1..20")
    ap.add_argument("--weapon", default="dagger", help="weapon[+magic], e.g. sword+2. Valid: " + ", ".join(sorted(ITEMS)))
    ap.add_argument("--armor", default="")
    ap.add_argument("--shield", default="")
    ap.add_argument("--ring", default="", help="ring+stat (1 STR, 2 DEX, 3 CON), e.g. gold+3")
    ap.add_argument("--potions", default="", help="belt (4 potions at most): name:count, e.g. red:3,violet:1")
    ap.add_argument("--pot", type=float, default=0.35, help="drinks below this fraction of hp (0 = never)")
    ap.add_argument("--monster", action="append", help="monster (repeatable, max 8). Valid: " + ", ".join(sorted(MONS)))
    ap.add_argument("--boss", type=int, default=0, help="n = monster n is a named boss (1..8)")
    ap.add_argument("--fights", type=int, default=10)
    ap.add_argument("--dur", type=int, default=0, help="starting weapon durability (= max, 1..255): the weapon wears "
                    "and can break during the series; 0 = no wear (default, repeatable series)")
    ap.add_argument("--maxsec", type=float, default=120, help="game time limit per fight (seconds)")
    ap.add_argument("--skills", default=",".join(ALLSK))
    ap.add_argument("--sleep", action="store_true", help="monsters asleep at the start")
    ap.add_argument("--bot", default="stand", choices=["stand", "approach", "adds"])
    ap.add_argument("--slow", action="store_true", help="waits for the raster (real game speed)")
    ap.add_argument("--show", action="store_true", help="visible VICE window (with --slow and without warp: --nowarp)")
    ap.add_argument("--nowarp", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--csv", help="appends a row to this CSV file")
    a = ap.parse_args()
    pots = {}
    for x in filter(None, a.potions.split(",")):
        k, _, v = x.partition(":")
        pots[k] = int(v or 1)
    with Arena(warp=not a.nowarp, show=a.show) as ar:
        r = ar.run(lvl=a.lvl, plvl=a.plvl, weapon=a.weapon, armor=a.armor, shield=a.shield, ring=a.ring, potions=pots,
                   monsters=a.monster or ["fallen"], boss=a.boss, fights=a.fights, maxsec=a.maxsec, fast=not a.slow,
                   skills=[s for s in a.skills.split(",") if s], pot=a.pot, wake=not a.sleep, bot=a.bot, dur=a.dur)
    if a.json:
        print(json.dumps(r, indent=1))
    else:
        print(summary(r))
    if a.csv:
        new = not os.path.exists(a.csv)
        row = {"p_" + k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in r["params"].items()}
        row.update({k: r[k] for k in ("fights", "win", "lose", "timeout", "avg_sec", "frames", "hp_end", "dealt", "taken",
                                      "healed", "potions", "xp", "kills", "wall_s", "weapon_dur", "weapon_end")})
        row.update({"pg_" + k: v for k, v in r["pg"].items()})
        row.update({"m0_" + k: v for k, v in r["m0"].items()})
        with open(a.csv, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            if new:
                w.writeheader()
            w.writerow(row)


if __name__ == "__main__":
    main()
