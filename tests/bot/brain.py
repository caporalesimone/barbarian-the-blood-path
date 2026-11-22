"""Bot, layer 5: the brain. Reads the state, asks the capabilities in order of priority, lets the first one that is ready
act for one decision. Keeps the log of every level (logbook.py)."""
import time
import nav, skills
from state import World
from logbook import Log


class Bot:
    def __init__(self, emu, max_level=19, max_seconds=None, cheats=(), max_deaths=0):
        self.emu = emu
        self.world = World(emu)
        self.walker = nav.Walker(self.world)
        self.log = Log(self)
        self.max_level, self.max_seconds = max_level, max_seconds
        self.cheats, self.max_deaths, self.deaths = set(cheats), max_deaths, 0
        self.cheat_gold_done = False
        self.ascend = skills.Ascend()
        self.gear = skills.Gear()
        self.caps = [skills.Screens(), skills.Drink(), skills.Flee(), skills.Fight(), skills.Stats(), self.gear, skills.Town(),
                     skills.Loot(), self.ascend, skills.Descend(), skills.Explore()]
        self.heal_tries = 0
        self.death_key = None; self.death_loop = 0
        self.inv = None; self.inv_check = True; self.last_lvl = 0; self.last_gold = None
        self.ignored = set(); self.fight_t = [None, 0, 0]
        self.met = set(); self.last_hp = None
        self.avoided = set(); self.town_reread = False; self.loot_wait = 0; self.opened = set()
        self.dead = False; self.stop = None
        self.pot_wait = 0; self.skill_sel = 0
        self.done_chests = set()
        self.gear_check = True; self.stat_lvl = 0; self.town_done = False
        self.explored_all = False; self.explore_more = False; self.going_up = False
        self.mon_n = 0; self.map_age = 0
        self._tables = None
        self.belt_n = 0
        self.last_cap = None

    # ---- data of the game read once
    def tables(self):
        if self._tables is None:
            e, L = self.emu, self.emu.L
            n = L["N_ITEMS"]
            na = L["UN0"] + 4 * L["UN_N"]
            pr = e.mem(L["itprice"], 2 * n)
            self._tables = dict(cat=e.mem(L["itcat"], n), val=e.mem(L["itval"], n), dn=e.mem(L["itdn"], n), ds=e.mem(L["itds"], n),
                                rate=e.mem(L["itrate"], n), fl=e.mem(L["itfl"], n), req=e.mem(L["itreq"], n),
                                price=[pr[2 * i] + 256 * pr[2 * i + 1] for i in range(n)],
                                pw=e.mem(L["af_pw"], na))
            self._tables["val_af"] = e.mem(L["af_val"], na)
        return self._tables

    def monster_name(self, m):
        """name of a monster of the current chapter (bestiary.tsv order = the game's types 1..9); the named boss of a level:
        'named <name>'"""
        c = (self.world.level - 1) // 5 + 1 if self.world.level else 1
        nm = self.log.names.get("monsters", {}).get(min(c, 4), {}).get(m["type"], "type %d" % m["type"])
        if m["type"] == 9 and self.world.level % 5:
            nm = "Lord of Ruin"
        if m["boss"] and self.world.level and self.world.level % 5 == 0:
            # (22/11) the boss level of a chapter: its boss is a strong monster of a random family (place_boss) shown with
            # the chapter boss's sprite and name (build_sprites, lv_cboss): the name is the chapter boss, the stats that type's
            return "%s (stats of %s)" % (self.log.names.get("monsters", {}).get(min((self.world.level - 1) // 5 + 1, 4), {}).get(9, "chapter boss"), nm)
        return ("named " + nm) if m["boss"] and m["type"] != 9 else nm

    def loot_info(self, i, b, s):
        """an item for the loot statistics: [category, item level of the base (bases.tsv), quality, name]"""
        T, L = self.tables(), self.emu.L
        cat = {1: "weapon", 2: "armor", 3: "shield", 4: "ring", 5: "potion", 6: "scroll"}.get(T["cat"][i], "other")
        q = "unique" if s >= 0x80 else "normal" if not (b or s) or cat == "scroll" else "magic"
        return [cat, self.log.names.get("ilvl", {}).get(i, 0), q, self.item_name(i, b, s)]

    def item_name(self, i, b, s):
        names = self.log.names
        base = names["items"].get(i, "item %d" % i)
        if i == self.emu.L["I_SCROLL"]:
            return "%d %s" % (b, base) if b else base          # (the prefix byte of a scroll is the quantity)
        if s >= 0x80: return names["uniques"].get(s & 0x7f, "unique %d" % (s & 0x7f))
        return " ".join(x for x in (names["prefix"].get(b, ""), base, names["suffix"].get(s, "")) if x)

    def level_done(self):
        """enough of this level: no chest to try and every reachable frontier seen, or the stairs known for a while"""
        if self.explored_all:
            return True
        return self.log.cur and self.emu.frames - self.log.cur["f0"] > 50 * 240     # 4 emulated minutes on a level: go on

    # ---- the loop
    def run(self):
        w = self.world
        while not self.stop:
            h = w.read()
            if w.level != self.log.level:
                self.log.enter(w.level, h)
                self.town_reread = False
                self.done_chests = {c for c in self.done_chests if c[0] != w.level or c in self.opened}
                self.explored_all = False
                self.skill_sel = 0
                self.mon_n = len(w.monsters)
            if self.pot_wait: self.pot_wait -= 1
            self.cheat(h)
            # the map changes while playing (a dead monster leaves a chest): read it again after a kill and now and then
            self.map_age += 1
            if w.level and (len(w.monsters) < self.mon_n or self.map_age > 60):
                if len(w.monsters) < self.mon_n: self.log.count("kills", self.mon_n - len(w.monsters))
                n0 = w.map.count(self.emu.L["T_CHEST"])
                w.read_map(); self.map_age = 0
                if w.map.count(self.emu.L["T_CHEST"]) > n0: self.explored_all = False
            self.mon_n = len(w.monsters)
            nb = sum(1 for t in h.belt if t)
            if w.level and nb < self.belt_n:
                self.log.count("potions", self.belt_n - nb)
            self.belt_n = nb
            if w.level:
                for m in w.visible_monsters():
                    k = (w.level, self.log.visit_n, m["i"])
                    if k not in self.met:
                        self.met.add(k)
                        self.log.event("meet", level=w.level, monster=self.monster_name(m), monster_hp=m["hp"],
                                       pos="%d,%d" % (m["tx"], m["ty"]), hero_hp="%d/%d" % (h.hp, h.hpmax), awake=bool(m["awake"]))
            if self.last_hp is not None and 0 < h.hp < self.last_hp and w.level:
                near = min(w.monsters, key=lambda m: abs(m["x"] - h.px) + abs(m["y"] - h.py), default=None)
                self.log.event("hurt", level=w.level, hp="%d -> %d/%d" % (self.last_hp, h.hp, h.hpmax),
                               by=self.monster_name(near) if near else "?", monster_hp=near["hp"] if near else "-")
            self.last_hp = h.hp
            if self.last_lvl and h.lvl > self.last_lvl:
                self.log.event("level_up", hero_level=h.lvl, level=w.level, hpmax=h.hpmax)
            self.last_lvl = h.lvl
            if self.last_gold is not None and h.gold > self.last_gold and w.level:
                self.log.count("gold_found", h.gold - self.last_gold)
            self.last_gold = h.gold
            if self.inv_check and h.in_game:
                self.inv_check = False
                self.inventory_diff()
            if w.level > self.max_level:
                self.stop = "reached level %d" % w.level; break
            if self.max_seconds and time.time() - self.emu.t0 > self.max_seconds:
                self.stop = "time limit"; break
            for c in self.caps:
                if c.ready(self):
                    if c.name != self.last_cap:
                        self.last_cap = c.name
                    c.act(self)
                    self.log.tick(c.name)
                    break
        self.log.hero = self.snapshot()
        self.log.close(self.stop)
        return self.log

    def cheat(self, h):
        """--cheat: potions = a red potion in the first belt slot when the belt is empty in a dungeon; gold = 10000 gold in
        the inn chest at the start (the bot takes it from there in the village). Every use is an event of the log."""
        e, L = self.emu, self.emu.L
        if "gold" in self.cheats and not self.cheat_gold_done and h.in_game:
            self.cheat_gold_done = True
            e.poke(L["c_sgold"], 1000 & 255, 1000 >> 8)     # the chest counts tens of gold
            self.log.event("cheat", what="gold", chest_gold=10000)
        if "potions" in self.cheats and self.world.level > 0 and h.in_game and not any(h.belt):
            e.poke(L["c_beltt"], L["I_POTR"]); e.poke(L["hud_dirty"], 1)
            h.belt = [L["I_POTR"], 0, 0, 0]; self.belt_n = 1
            self.log.event("cheat", what="potion", level=self.world.level, hp="%d/%d" % (h.hp, h.hpmax))
            self.log.count("cheat_potions")

    def inventory(self):
        """pack, worn items and belt as lists of (id, prefix, suffix, durability, maximum)"""
        e, L = self.emu, self.emu.L
        n = L["PACK_N"] + L["EQ_N"]
        f = [e.mem(L[a], n) for a in ("c_pack", "c_packb", "c_packs", "c_packd", "c_packm")]
        return [tuple(col[k] for col in f) for k in range(n)]

    def describe(self, it):
        """an item for the log: name, quality, durability and the numbers the choice of the gear looks at"""
        i, b, s, d, m = it
        T, L = self.tables(), self.emu.L
        cat = T["cat"][i]
        q = "unique" if s >= 0x80 else "normal" if not (b or s) else "magic"
        if q == "magic" and any(skills.sgn(T["val_af"][k]) < 0 for k in skills.rows(L, b, s)): q = "cursed"
        out = dict(item=self.item_name(i, b, s), what={1: "weapon", 2: "armor", 3: "shield", 4: "ring"}.get(cat, "other"), quality=q)
        if m: out["durability"] = "%d/%d" % (d, m)
        if cat == 1:
            out["dice"] = "%dd%d" % (T["dn"][i], T["ds"][i]); out["rate"] = T["rate"][i]
            out["two_handed"] = bool(T["fl"][i] & 1)
        elif cat in (2, 3):
            out["ac"] = T["val"][i]
        r = T["req"][i]
        if r & 0x7f: out["needs"] = "%s %d" % ("dex" if r & 0x80 else "str", r & 0x7f)
        sc = self.gear.score(self, T, i, b, s, d, m)
        if sc >= 0: out["score"] = round(sc, 1)
        return out

    def inventory_diff(self):
        """what entered or left the pack since the last look: events `found` (with the reason it was not worn, if any)
        and `lost` (dropped, sold or broken items are logged by who did it)"""
        new = self.inventory()
        P = self.emu.L["PACK_N"]
        if self.inv is not None:
            old = list(self.inv[:P]) + list(self.inv[P:])
            for it in new[:P]:
                if not it[0]:
                    continue
                if it in old:
                    old.remove(it); continue
                d = self.describe(it)
                why = self.gear.why_not(self, it)
                if why: d["not_worn"] = why
                self.log.event("found", level=self.world.level, **d)
                self.log.count("items_found")
        self.inv = new

    def snapshot(self):
        """the hero at the end: level, life, gold, stats, what he wears and carries (names)"""
        e, L, h = self.emu, self.emu.L, self.world.hero
        P, E = L["PACK_N"], L["EQ_N"]
        f = {k: e.mem(L[a], P + E) for k, a in (("id", "c_pack"), ("b", "c_packb"), ("s", "c_packs"))}
        nm = lambda k: self.item_name(f["id"][k], f["b"][k], f["s"][k]) if f["id"][k] else "-"
        return dict(level=h.lvl, hp=h.hp, hpmax=h.hpmax, gold=h.gold, xp=h.xp,
                    str=e.b(L["s_str"]), dex=e.b(L["s_dex"]), con=e.b(L["s_con"]), att=e.b(L["s_att"]), ac=e.b(L["s_ac"]),
                    worn=[nm(P + k) for k in range(E)], pack=[nm(k) for k in range(P)], deaths=e.w(L["c_deaths"]))
