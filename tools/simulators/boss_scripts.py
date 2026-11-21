#!/usr/bin/env python3
"""Chapter boss mechanics for the fight simulator (20/11). Numbers: data/rules_next.yaml "bosses".

Each script plugs into sim_rules.fight(script=...): tick() runs at every event (spawns, regeneration, timed attacks; returns
damage to the hero), pg_dmg/m_dmg change the damage of a hit, m_rate the time between two monster attacks, pg_rate the hero's
attack cadence (curse), target() picks the hero's target (the bot kills summons first, as a good player does).

Mechanics: "game" = what the code does since 19/11 (docs/wiki/bestiario.md "Meccaniche dei boss di capitolo"; the Lord of
Ruin only summons, through final_boss in fight); "new" = additions proposed on 20/11. The simulator does not move: an
announced attack (warning on screen) is dodged with probability `skill` (a stand-in for the player's movement)."""
import sim_rules as S

FAR = 10 ** 9


class Base:
    def __init__(self, cfg, mon, floor, new, skill, rng):
        self.c, self.mon, self.floor, self.new, self.skill = cfg, mon, floor, new, skill
        self.timers = {}            # name -> next time
        self.hurt = []              # (time, damage to the hero)
        self.adds = []
        self.b = None
        self.rng = rng
        self.g = dict(cfg["game"])                  # numbers of the game; the proposal may change some ("new.changes")
        if new:
            self.g.update(cfg["new"].get("changes") or {})

    # --- helpers
    def bind(self, ms):
        if self.b is None:
            self.b = ms[0]
            self.start(ms)

    def start(self, ms):
        pass

    def frac(self):
        return self.b.hp / self.b.hpmax

    def spawn(self, pend, at, kind):
        m = S.Mon(self.mon(kind, self.floor, False), self.rng)
        m.add = True
        pend.append((at, m))
        self.adds.append(m)
        return m

    def adds_alive(self):
        return [m for m in self.adds if m.alive]

    def boss_hit(self):
        return self.b.st["dmg"].avg * self.b.st["dmg_mult"]

    def dodge(self):
        return self.rng.random() < self.skill

    def zone(self, t, p):
        """announced area attack: warning, then `ticks` hits of dmg x the boss hit, unless dodged"""
        if not self.dodge():
            for k in range(p["ticks"]):
                self.hurt.append((t + p["warn"] + k * p["tick_every"], p["dmg"] * self.boss_hit()))

    # --- hooks for fight
    def wake(self, t):
        ts = [v for v in self.timers.values() if v > t] + [h[0] for h in self.hurt if h[0] > t]
        return min(ts) if ts else FAR

    def tick(self, t, ms, pend, rng, hero):
        self.bind(ms)
        self.hero = hero
        self.step(t, ms, pend)
        d = sum(x for when, x in self.hurt if when <= t)
        self.hurt = [h for h in self.hurt if h[0] > t]
        return int(d)

    def step(self, t, ms, pend):
        pass

    def pg_dmg(self, m, d, t):
        return d

    def m_dmg(self, m, d, t):
        return d

    def m_rate(self, m, t):
        return S.T["monster_attack"]

    def pg_rate(self, t):
        return 1.0

    def target(self, alive):
        a = [m for m in alive if getattr(m, "add", False)]
        return min(a, key=lambda m: m.hp) if a else alive[0]

    def regen(self, t, cond, every):
        last = self.timers.get("_regen", t)
        if cond and self.b.alive:
            n = (t - last) // every
            if n > 0:
                self.b.hp = min(self.b.hpmax, self.b.hp + n)
                self.timers["_regen"] = last + n * every
        else:
            self.timers["_regen"] = t


class Abbot(Base):
    """The Hollow Abbot (chapter 1): game = 2 skeletons at 2/3 and 1/3 (pause 1 s), +1 life every 25 frames while one is
    alive. New: skeletons rise from the crypt at random places every 8 s (they walk to the hero); censer cloud every 6 s"""
    def start(self, ms):
        self.th = list(self.g["summon_at"])
        self.summoned = []
        if self.new:
            n = self.c["new"]
            self.timers["rise"] = n["crypt_rise"]["every"]
            self.timers["censer"] = n["censer"]["every"]

    def step(self, t, ms, pend):
        g = self.g
        if g.get("rage_at") and self.b.alive and not getattr(self, "rage", False) and self.frac() <= g["rage_at"]:
            self.rage = True                                  # (21/11, game) rage: faster attacks, the censer
            self.timers["censer_g"] = t + g["censer_first"]
        if getattr(self, "rage", False) and self.b.alive and t >= self.timers.get("censer_g", FAR):
            self.timers["censer_g"] = t + g["censer_every"]
            if not self.dodge():
                self.hurt.append((t + g["censer_warn"], self.hero.hpmax // g["censer_hp_div"]))
        while self.th and self.b.alive and self.frac() <= self.th[0]:
            self.th.pop(0)
            self.b.next = max(self.b.next, t + g["pause"])
            for _ in range(g["summon_n"]):
                self.summoned.append(self.spawn(pend, t + g["pause"], g["summon_type"]))
        self.regen(t, any(m.alive for m in self.summoned) or any(p[1] in self.summoned for p in pend), g["regen_every"])
        if not self.new or not self.b.alive:
            return
        n = self.c["new"]
        if t >= self.timers["rise"]:
            r = n["crypt_rise"]
            self.timers["rise"] = t + r["every"]
            if len(self.adds_alive()) + sum(1 for p in pend if getattr(p[1], "add", False)) < r["max_alive"]:
                self.spawn(pend, t + self.rng.randint(*r["travel"]), r["type"])     # no regeneration from these
        if t >= self.timers["censer"]:
            self.timers["censer"] = t + n["censer"]["every"]
            self.zone(t, n["censer"])

    def m_rate(self, m, t):
        if m is self.b and getattr(self, "rage", False):
            return min(S.T["monster_attack"], self.g["rage_rate"])
        return S.T["monster_attack"]


class Stitch(Base):
    """Mother Stitch (chapter 2): game = rites at waking, 2/3, 1/3: 2 still fetishes (life = boss max / 16); while one stands
    the hero's hits are halved and she regenerates; the last one down leaves her exposed 2 s (still, hits x2). New: a hex every
    8 s (attack cadence x1.6 for 3 s, unless dodged); a fetish left standing 10 s rots into a Drowned"""
    def start(self, ms):
        self.th = list(self.g["rites_at"])
        self.fet = []
        self.exposed = 0
        self.slow = 0
        if self.new:
            self.timers["hex"] = self.c["new"]["hex"]["every"]

    def step(self, t, ms, pend):
        g = self.g
        while self.th and self.b.alive and self.frac() <= self.th[0]:
            self.th.pop(0)
            self.b.next = max(self.b.next, t + 50)
            for _ in range(g["fetish_n"]):
                f = self.spawn(pend, t + 50, "skeleton")
                f.hpmax = f.hp = max(1, self.b.hpmax // g["fetish_hp_div"])
                f.next = FAR
                f.fetish, f.born = True, t + 50
                self.fet.append(f)
        standing = [f for f in self.fet if f.alive or any(p[1] is f for p in pend)]
        if self.fet and not standing and self.exposed == 0:
            self.exposed = t + g["exposed"]
            self.b.stun_for(t, g["exposed"])
            self.fet = []
        if self.exposed and t >= self.exposed:
            self.exposed = 0
        self.timers["_exp"] = self.exposed or FAR
        self.regen(t, bool(standing), g["regen_every"])
        if not self.new or not self.b.alive:
            return
        n = self.c["new"]
        if t >= self.timers["hex"]:
            h = n["hex"]
            self.timers["hex"] = t + h["every"]
            if not self.dodge():
                self.slow = t + h["warn"] + h["duration"]
        for f in list(self.fet):
            if f.alive and t >= f.born + n["fetish_rot"]["after"]:
                f.alive = False
                self.fet.remove(f)
                self.spawn(pend, t, n["fetish_rot"]["type"])

    def protected(self):
        return any(f.alive for f in self.fet)

    def pg_dmg(self, m, d, t):
        if m is not self.b:
            return d
        if self.exposed and t < self.exposed:
            return d * self.g["exposed_mult"]
        return max(1, d // self.g["protect_div"]) if self.protected() else d

    def pg_rate(self, t):
        return self.c["new"]["hex"]["slow"] if self.new and t < self.slow else 1.0


class Varok(Base):
    """Varok the Oathbreaker (chapter 3): game = a charge every ~6 s (warning 0.5 s): dodged -> he hits the wall, stunned 2 s
    (shield down); not dodged -> 2 attacks; the shield halves the hero's hits. New: at half life 2 Ash Ghouls, and he throws
    the shield away (no halving) and attacks and charges faster"""
    def start(self, ms):
        self.timers["charge"] = self.g["charge_every"]
        self.broken = False

    def step(self, t, ms, pend):
        g = self.g
        if self.new and not self.broken and self.frac() <= self.c["new"]["oathbreak"]["at"]:
            self.broken = True
            for _ in range(self.c["new"]["ghouls"]["n"]):
                self.spawn(pend, t, self.c["new"]["ghouls"]["type"])
        if self.b.alive and t >= self.timers["charge"]:
            every = self.c["new"]["oathbreak"]["charge_every"] if self.broken else g["charge_every"]
            self.timers["charge"] = t + every
            if self.b.stun > t:
                return
            if self.dodge():
                self.b.stun_for(t + 25, g["wall_stun"])
            else:
                for _ in range(g["charge_hits"]):
                    r = S.attack_roll(self.rng, self.b.att, self.hero.ac)
                    if r:
                        self.hurt.append((t + 25, self.b.st["dmg"].roll(self.rng, times=r) * self.b.st["dmg_mult"]))

    def pg_dmg(self, m, d, t):
        if m is self.b and not self.broken and self.b.stun <= t:
            return max(1, d // self.g["shield_div"])
        return d

    def m_rate(self, m, t):
        r = S.T["monster_attack"]
        return int(r * self.c["new"]["oathbreak"]["rate_mult"]) if m is self.b and self.broken else r


class Lord(Base):
    """Lord of Ruin (chapter 4, final): game = the summons of fight (final_boss). New: the pentacle burns at 3/4, 1/2, 1/4
    (dodge = stand off the lines), faster in the last quarter, the tithe every 10 s (drains life from the hero, heals him)"""
    def start(self, ms):
        self.th = list(self.c["new"]["pentacle"]["at"]) if self.new else []
        if self.new:
            self.timers["tithe"] = self.c["new"]["tithe"]["every"]

    def step(self, t, ms, pend):
        if not self.new or not self.b.alive:
            return
        n = self.c["new"]
        while self.th and self.frac() <= self.th[0]:
            self.th.pop(0)
            self.zone(t, n["pentacle"])
        if t >= self.timers["tithe"]:
            p = n["tithe"]
            self.timers["tithe"] = t + p["every"]
            if not self.dodge():
                d = self.hero.hpmax * p["drain_pct"] // 100
                self.hurt.append((t + p["warn"], d))
                self.b.hp = min(self.b.hpmax, self.b.hp + d * p["heal_mult"])

    def m_rate(self, m, t):
        r = S.T["monster_attack"]
        if self.new and m is self.b and self.frac() <= self.c["new"]["fury"]["at"]:
            return int(r * self.c["new"]["fury"]["rate_mult"])
        return r


SCRIPTS = {"abbot": Abbot, "stitch": Stitch, "varok": Varok, "lord": Lord}
