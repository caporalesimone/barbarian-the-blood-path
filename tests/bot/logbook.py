"""Bot: the log. One record per visit of a level (emulated time, real time, kills, potions, chests, deaths, hero level, life)
and a list of events (deaths, items worn, stat points, sales). Report: a table on the screen and a JSON file
(out/work/bot/<name>.json) with levels, chapters and the whole run."""
import csv, json, os, re, time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")


def _names():
    n = dict(items={}, prefix={}, suffix={}, uniques={})
    try:
        for m in re.finditer(r'^itnm_(\d+)\s+#t5 "([^"]*)"', open(os.path.join(ROOT, "out", "work", "db.asm")).read(), re.M):
            n["items"][int(m.group(1))] = m.group(2)
        nx = os.path.join(ROOT, "data", "items", "next")
        rd = lambda f: list(csv.DictReader(open(os.path.join(nx, f)), delimiter="\t"))
        n["prefix"] = {i + 1: r["name"] for i, r in enumerate(rd("prefixes.tsv"))}
        n["suffix"] = {i + 1: r["name"] for i, r in enumerate(rd("suffixes.tsv"))}
        n["uniques"] = {i: r["name"] for i, r in enumerate(rd("uniques.tsv"))}
        il = {r["name"]: int(r["ilvl"] or 0) for r in rd("bases.tsv")}
        n["ilvl"] = {i: il.get(nm, 0) for i, nm in n["items"].items()}
        be = list(csv.DictReader(open(os.path.join(ROOT, "data", "monsters", "bestiary.tsv")), delimiter="\t"))
        n["monsters"] = {}
        for c in range(1, 5):
            rows_c = [r for r in be if r["chapter"] == str(c)]
            order = [r for r in rows_c if r["tier"] == "base"] + [r for r in rows_c if r["tier"] == "strong"] + \
                    [r for r in rows_c if r["tier"] == "boss"]
            n["monsters"][c] = {k + 1: r["name"] for k, r in enumerate(order)}
    except OSError:
        pass
    return n


class Log:
    def __init__(self, bot):
        self.bot = bot
        self.level = -1
        self.visits, self.events = [], []
        self.cur = None
        self.names = _names()
        self.t0 = time.time()
        self.hero = {}

    def enter(self, level, h):
        self._end(h)
        self.level = level
        self.visit_n = getattr(self, "visit_n", 0) + 1
        e = self.bot.emu
        self.cur = dict(level=level, chapter=(level - 1) // 5 + 1 if level else e.b(e.L["c_chap"]), f0=e.frames, t0=time.time(),
                        hero_level_in=h.lvl, hp_in=h.hp, gold_in=h.gold, xp_in=h.xp, counts={}, caps={},
                        monsters=len(self.bot.world.monsters))
        print("[bot] %7.1f s  level %2d  hero level %2d  hp %d/%d  gold %d" % (e.seconds(), level, h.lvl, h.hp, h.hpmax, h.gold), flush=True)

    def _end(self, h):
        c, e = self.cur, self.bot.emu
        if not c:
            return
        c.update(seconds=round((e.frames - c["f0"]) / 50.0, 1), real_seconds=round(time.time() - c["t0"], 1),
                 hero_level_out=h.lvl, hp_out=h.hp, hpmax=h.hpmax, gold_out=h.gold, xp_out=h.xp,
                 monsters_left=len(self.bot.world.monsters), seen=len(self.bot.world.seen) if c["level"] else 0)
        del c["f0"], c["t0"]
        self.visits.append(c)
        self.cur = None

    def tick(self, cap):
        if self.cur: self.cur["caps"][cap] = self.cur["caps"].get(cap, 0) + 1

    def count(self, what, n=1):
        if self.cur: self.cur["counts"][what] = self.cur["counts"].get(what, 0) + n

    def event(self, kind, **kw):
        e = dict(kind=kind, at=round(self.bot.emu.seconds(), 1), **kw)
        self.events.append(e)
        if kind == "death": self.count("deaths")
        print("[bot] %7.1f s  %s %s" % (e["at"], kind, " ".join("%s=%s" % kv for kv in kw.items())), flush=True)

    def close(self, why):
        self._end(self.bot.world.hero)
        self.why = why

    # ---- report
    def summary(self):
        lv = {}
        for v in self.visits:
            if not v["level"]:
                continue
            d = lv.setdefault(v["level"], dict(level=v["level"], chapter=v["chapter"], visits=0, seconds=0, deaths=0, potions=0,
                                               chests=0, kills=0, items_found=0, gold_found=0, worn=0, retreats=0,
                                               hero_level_in=v["hero_level_in"], hero_level_out=0))
            d["visits"] += 1; d["seconds"] = round(d["seconds"] + v["seconds"], 1)
            for k in ("deaths", "potions", "chests", "kills", "items_found", "gold_found", "worn", "retreats"): d[k] += v["counts"].get(k, 0)
            d["hero_level_out"] = v["hero_level_out"]
        ch = {}
        for v in self.visits:
            d = ch.setdefault(v["chapter"], dict(chapter=v["chapter"], seconds=0, village_seconds=0, deaths=0))
            d["seconds"] = round(d["seconds"] + v["seconds"], 1)
            if not v["level"]: d["village_seconds"] = round(d["village_seconds"] + v["seconds"], 1)
            d["deaths"] += v["counts"].get("deaths", 0)
        e = self.bot.emu
        return dict(stop=self.why, emulated_seconds=round(e.seconds(), 1), real_seconds=round(time.time() - self.t0, 1),
                    frames=e.frames, speed="%.1fx" % (e.seconds() / max(1e-6, time.time() - self.t0)),
                    deepest_level=max([v["level"] for v in self.visits] or [0]),
                    levels=[lv[k] for k in sorted(lv)], chapters=[ch[k] for k in sorted(ch)])

    def write(self, name):
        out = os.path.join(ROOT, "out", "work", "bot")
        os.makedirs(out, exist_ok=True)
        s = self.summary()
        json.dump(dict(summary=s, hero=self.hero, visits=self.visits, events=self.events), open(os.path.join(out, name + ".json"), "w"), indent=1)
        print("\nstop: %s   emulated %.0f s, real %.0f s (%s), deepest level %d" % (s["stop"], s["emulated_seconds"], s["real_seconds"],
                                                                                  s["speed"], s["deepest_level"]))
        print("level chap visits seconds deaths potions chests kills items  gold hero level")
        for d in s["levels"]:
            print("%5d %4d %6d %7.1f %6d %7d %6d %5d %5d %5d   %d -> %d" % (d["level"], d["chapter"], d["visits"], d["seconds"], d["deaths"],
                  d["potions"], d["chests"], d["kills"], d["items_found"], d["gold_found"], d["hero_level_in"], d["hero_level_out"]))
        found = [e for e in self.events if e["kind"] == "found"]
        if found:
            print("items found (%d):" % len(found))
            for e in found:
                print("  level %2d  %-34s %-7s %-7s %s%s" % (e["level"], e["item"], e.get("what", ""), e["quality"],
                      ("score %s" % e["score"]) if "score" in e else "", ("  not worn: " + e["not_worn"]) if e.get("not_worn") else ""))
        worn = [e for e in self.events if e["kind"] == "wear"]
        for e in worn:
            print("worn on level %d: %s (%s, score %s) in place of %s (%s)" % (e["level"], e["item"], e["slot"], e["score"], e["took_off"], e["old_score"]))
        txt = os.path.join(out, name + ".log")              # every event, one line each
        with open(txt, "w") as f:
            for e in self.events:
                f.write("%8.1f s  %-9s %s\n" % (e["at"], e["kind"], "  ".join("%s=%s" % (k, v) for k, v in e.items() if k not in ("kind", "at"))))
        for d in s["chapters"]:
            print("chapter %d: %.1f s (village %.1f s), deaths %d" % (d["chapter"], d["seconds"], d["village_seconds"], d["deaths"]))
        if self.hero:
            hh = self.hero
            print("hero: level %(level)d, hp %(hp)d/%(hpmax)d, str %(str)d dex %(dex)d con %(con)d, att %(att)d ac %(ac)d, gold %(gold)d, deaths %(deaths)d" % hh)
            print("worn: %s\npack: %s" % (", ".join(hh["worn"]), ", ".join(hh["pack"])))
        return os.path.join(out, name + ".json")
