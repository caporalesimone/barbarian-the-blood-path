"""Bot, layer 4: the capabilities. Each one is a small class with `ready(bot)` (does it want the turn?) and `act(bot)`
(one decision: usually the joystick for the next frame). The brain (brain.py) asks them in order of priority.
To add a capability (a shop, a quest, a new skill rule): write a class here and put it in the list of brain.py.

What goes through the game's own input: walking, fighting, skills, potions, chests, stairs, the death screen.
What is a SHORTCUT (the bot writes the result in memory and calls the game's own routine, same outcome as the menu, no menu
navigation yet): wearing an item (Gear), spending the stat points (Stats), selling and buying in the village (Town)."""
import nav
from emu import UP, DOWN, LEFT, RIGHT, FIRE

SKILL_KEYS = ("slash", "whirlwind", "battle_cry", "smash", "rage", "frenzy")       # index = sk_req / sk_cd index


def dist(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


class Capability:
    name = "?"
    def ready(self, bot): return False
    def act(self, bot): raise NotImplementedError


class Screens(Capability):
    """a screen is open and nobody asked for it (death, a message): fire, then RUN/STOP"""
    name = "screens"
    def ready(self, bot):
        return not bot.world.hero.in_game
    def act(self, bot):
        h = bot.world.hero
        if h.hp == 0 and not bot.dead:
            bot.dead = True
            bot.log.event("death", level=bot.world.level, hero_level=h.lvl)
            key = (bot.world.level, h.lvl, h.xp)
            bot.death_loop = bot.death_loop + 1 if key == bot.death_key else 1
            bot.death_key = key
            bot.deaths += 1
            if bot.max_deaths and bot.deaths >= bot.max_deaths:
                bot.stop = "%d deaths (--max-deaths)" % bot.deaths
            if bot.death_loop >= 4:                        # 4 deaths in a row on the same level with no experience gained
                bot.stop = "death loop on level %d (hero level %d): 4 deaths in a row with no progress" % (bot.world.level, h.lvl)
        bot.emu.tap_fire(3)
        if not bot.emu.in_game():
            bot.emu.step(key="runstop"); bot.emu.step(n=2)


class Drink(Capability):
    """a potion when the life is under 45% (the game refuses if the potions are still recharging)"""
    name = "drink"
    def ready(self, bot):
        h = bot.world.hero
        return bot.world.level > 0 and 0 < h.hp * 100 < h.hpmax * 45 and any(h.belt) and not bot.pot_wait
    def act(self, bot):
        h = bot.world.hero
        slot = next(i for i, t in enumerate(h.belt) if t)
        bot.log.event("drink", level=bot.world.level, hp_before="%d/%d" % (h.hp, h.hpmax), slot=slot + 1)
        bot.emu.step(key="potion%d" % (slot + 1))
        bot.pot_wait = 12                                  # (drunk potions are counted by the brain: the belt gets emptier)


class Flee(Capability):
    """life under 30% and no potion left: back to the village by the stairs (to heal at the fountain and buy potions).
    Not on a boss level (the boss heals while the hero is away)."""
    name = "flee"
    def ready(self, bot):
        h, w = bot.world.hero, bot.world
        if w.level > 0 and w.level % 5 and 0 < h.hp * 100 < h.hpmax * 30 and not any(h.belt) and not bot.going_up:
            bot.going_up = True
            bot.log.count("retreats")
            bot.log.event("retreat", level=w.level, hp="%d/%d" % (h.hp, h.hpmax))
        return w.level > 0 and bot.going_up and w.level % 5 != 0
    def act(self, bot):
        bot.ascend.act(bot)


class Fight(Capability):
    """the nearest monster on the screen: walk next to it, face it, hold fire. Skills (learned from the level, sk_req):
    whirlwind with 2 or more monsters around, battle cry with 3 or more, smash on a boss, rage under half life with
    2 or more around, frenzy on a boss; only when the recharge (sk_cd) is over."""
    name = "fight"
    REACH = 20                                              # pixels between the centres: a blow lands
    def target(self, bot):
        h = bot.world.hero
        ms = [m for m in bot.world.visible_monsters() if (m["awake"] or dist((m["tx"], m["ty"]), (h.tx, h.ty)) <= 4)
              and (bot.world.level, m["i"]) not in bot.ignored and not self.too_strong(bot, m)]
        # the nearest one; on a boss level the others first (the abbot heals while his risen skeletons stand), unless the boss
        # is already next to the hero
        key = lambda m: (bool(m["boss"]) and abs(m["x"] - h.px) + abs(m["y"] - h.py) > 24, abs(m["x"] - h.px) + abs(m["y"] - h.py))
        return min(ms, key=key) if ms else None

    def too_strong(self, bot, m):
        """(22/11) the named boss of a normal level when it has more than 10 blows of the hero's mean damage: leave it (it
        may chase the hero: Flee takes over under 30%). Not on the boss level of a chapter (that one is the goal). Logged once."""
        w = bot.world
        if not m["boss"] or not w.level or w.level % 5 == 0:
            return False
        e, L = bot.emu, bot.emu.L
        dmg = e.b(L["s_dn"]) * (e.b(L["s_ds"]) + 1) / 2 + e.b(L["s_dk"])
        strong = m["hp"] > 10 * max(1, dmg)
        k = (w.level, bot.log.visit_n, m["i"])
        if strong and k not in bot.avoided:
            bot.avoided.add(k)
            bot.log.event("avoid", level=w.level, monster=bot.monster_name(m), monster_hp=m["hp"], hero_damage=round(dmg, 1),
                          hero_level=w.hero.lvl)
        return strong

    def ready(self, bot):
        return bot.world.level > 0 and self.target(bot) is not None

    def skill(self, bot, near, boss):
        e, L, h = bot.emu, bot.emu.L, bot.world.hero
        req = e.mem(L["sk_req"], 6)
        cdl, cdh = e.mem(L["sk_cdl"], 6), e.mem(L["sk_cdh"], 6)
        can = lambda i: h.lvl >= req[i] and not (cdl[i] | cdh[i])
        if boss and can(5): return "frenzy"
        if near >= 2 and h.hp * 2 < h.hpmax and can(4): return "rage"
        want = 0
        if boss and can(3): want = 3
        elif near >= 3 and can(2): want = 2
        elif near >= 2 and can(1): want = 1
        if want != bot.skill_sel:
            bot.skill_sel = want
            return SKILL_KEYS[want]
        return None

    def act(self, bot):
        w, h = bot.world, bot.world.hero
        m = self.target(bot)
        k = (w.level, m["i"])
        if bot.fight_t[0] != k or bot.fight_t[2] != m["hp"]:
            bot.fight_t = [k, 0, m["hp"]]
        bot.fight_t[1] += 1
        if bot.fight_t[1] > 120:                           # 120 decisions and the monster has not lost a point: unreachable
            bot.ignored.add(k)
            bot.log.event("give_up", level=w.level, monster=m["type"], boss=bool(m["boss"]), pos="%d,%d" % (m["tx"], m["ty"]),
                          hero="%d,%d" % (h.tx, h.ty), hp=m["hp"])
            bot.emu.step()
            return
        dx, dy = m["x"] - h.px, m["y"] - h.py
        near = sum(1 for o in w.monsters if abs(o["x"] - h.px) <= 28 and abs(o["y"] - h.py) <= 28)
        if abs(dx) <= self.REACH and abs(dy) <= self.REACH and min(abs(dx), abs(dy)) > 8:
            # (22/11) diagonal: the blow lands only in front of the hero (4 directions); step to line up on the shorter axis
            j = (DOWN if dy > 0 else UP) if abs(dy) < abs(dx) else (RIGHT if dx > 0 else LEFT)
            bot.emu.step(joy=j, n=2)
            return
        if abs(dx) <= self.REACH and abs(dy) <= self.REACH:
            key = self.skill(bot, near, m["boss"])
            bot.log.event("attack", level=w.level, monster=bot.monster_name(m), monster_hp=m["hp"],
                          hero_hp="%d/%d" % (h.hp, h.hpmax), skill=SKILL_KEYS[bot.skill_sel] if not key else key)
            if key:
                bot.log.count("skill_" + key)
                bot.log.event("skill", level=w.level, skill=key, monsters_near=near, boss=bool(m["boss"]), hp="%d/%d" % (h.hp, h.hpmax))
            face = (RIGHT if dx > 0 else LEFT) if abs(dx) >= abs(dy) else (DOWN if dy > 0 else UP)
            bot.emu.step(joy=face | FIRE, key=key, n=4)
            return
        path = nav.bfs(w, (h.tx, h.ty), lambda x, y: (x, y) == (m["tx"], m["ty"]))
        if path and len(path) > 1:
            bot.emu.step(joy=bot.walker.follow(path), n=2)
        else:
            bot.emu.step(joy=bot.walker.toward(m["x"], m["y"], slack=4), n=2)


class Loot(Capability):
    """a chest the bot has seen and not tried yet: next to it, fire, then fire on every item (the chest screen)"""
    name = "loot"
    def chests(self, bot):
        return [c for c in bot.world.find_seen(bot.emu.L["T_CHEST"]) if (bot.world.level, c) not in bot.done_chests]
    def ready(self, bot):
        return bot.world.level > 0 and bool(self.chests(bot))
    def act(self, bot):
        # (22/11) a chest opens with fire while the hero STANDS ON it (act_tick: pl_tile = T_CHEST -> chest_fire) and no
        # monster is within 3 tiles (chest_blocked); before, the bot stood next to it and never opened one
        w, h = bot.world, bot.world.hero
        cs = set(self.chests(bot))
        if (h.tx, h.ty) in cs:
            chest = (h.tx, h.ty)
        else:
            path = nav.bfs(w, (h.tx, h.ty), lambda x, y: (x, y) in cs,
                           passable=lambda x, y: w.known(x, y) and (w.walkable(x, y) or (x, y) in cs))
            if path is None:
                for c in cs: bot.done_chests.add((w.level, c))      # not reachable from here
                return
            bot.emu.step(joy=bot.walker.follow(path), n=bot.walker.run)
            return
        if any(max(abs(m["tx"] - h.tx), abs(m["ty"] - h.ty)) < 3 for m in w.monsters):
            # a monster too close (chest_blocked): Fight takes the turn, unless the bot gave up on it or avoids it; then leave
            # the chest for now (it is tried again on the next visit of the level)
            bot.loot_wait += 1
            if bot.loot_wait > 20:
                bot.loot_wait = 0
                bot.done_chests.add((w.level, chest))
                bot.log.event("chest_skipped", level=w.level, pos="%d,%d" % chest, why="a monster within 3 tiles")
            bot.emu.step(n=2)
            return
        bot.loot_wait = 0
        bot.emu.step(n=1)
        bot.emu.tap_fire(3)
        bot.opened.add((w.level, chest))
        bot.done_chests.add((w.level, chest))
        e, L = bot.emu, bot.emu.L
        def content(raw=False):
            ids, bs, ss = e.mem(L["l8_id"], 8), e.mem(L["l8_b"], 8), e.mem(L["l8_s"], 8)
            if raw:
                return [bot.loot_info(i, b, s) for i, b, s in zip(ids, bs, ss) if i]
            return [bot.item_name(i, b, s) for i, b, s in zip(ids, bs, ss) if i]
        opened = not bot.emu.in_game()
        locked = opened and e.b(L["ch_msg"]) == 1
        inside = content() if opened and not locked else []
        items = content(True) if opened and not locked else []
        gold = e.w(L["ch_gold"]) if opened and not locked else 0
        n = 0
        while not bot.emu.in_game() and n < 8:             # the chest screen: fire takes the item under the cursor
            bot.emu.tap_fire(2); n += 1
        left = content() if not bot.emu.in_game() else []
        if not bot.emu.in_game():
            bot.emu.step(key="runstop"); bot.emu.step(n=2)
        bot.log.count("chests")
        bot.log.event("chest", level=w.level, pos="%d,%d" % chest, opened=opened, locked=locked, gold=gold,
                      contents=", ".join(inside) or "-", left_inside=", ".join(left) or "-", items=items)
        w.read_map()
        bot.gear_check = True
        bot.inv_check = True


class Gear(Capability):
    """wear the best item of every slot (SHORTCUT: swaps the item fields in memory and calls recalc_stats, as the inventory
    does). Score: weapon = mean damage a frame, armor and shield = AC, with the item's affixes; requirements respected."""
    name = "gear"
    def ready(self, bot):
        return bot.gear_check and bot.world.hero.in_game

    def items(self, bot):
        e, L = bot.emu, bot.emu.L
        n = L["PACK_N"] + L["EQ_N"]
        f = {k: e.mem(L[a], n) for k, a in (("id", "c_pack"), ("b", "c_packb"), ("s", "c_packs"), ("d", "c_packd"), ("m", "c_packm"))}
        return f, n

    def score(self, bot, T, i, b, s, d, m):
        L = bot.emu.L
        if not i or (m and not d):
            return -1
        cat = T["cat"][i]
        af = lambda pw: sum(sgn(T["val_af"][k]) for k in rows(L, b, s) if T["pw"][k] == L["PW_" + pw])
        if cat == 1:                                       # weapon: (dice mean + fixed damage) / rate
            dmg = T["dn"][i] * (T["ds"][i] + 1) / 2 + af("ATT_DMG") + af("DMG") + 0.5 * af("ATT")
            return 100 * dmg / max(6, T["rate"][i] - af("SPEED"))
        if cat in (2, 3):
            return T["val"][i] + af("AC") + 0.1 * af("LIFE")
        return -1

    def why_not(self, bot, it):
        """why an item of the pack is not the one worn: '' if it is not gear, else the reason"""
        e, L = bot.emu, bot.emu.L
        T = bot.tables()
        i, b, s, d, m = it
        cat = T["cat"][i]
        if cat not in (1, 2, 3):
            return ""
        r = T["req"][i]
        have = e.b(L["s_dex"] if r & 0x80 else L["s_str"])
        if (r & 0x7f) > have:
            return "needs %s %d (has %d)" % ("dex" if r & 0x80 else "str", r & 0x7f, have)
        inv = bot.inventory()
        P = L["PACK_N"]
        if cat == 1 and T["fl"][i] & 1 and inv[P + 2][0]:
            return "two-handed and a shield is worn"
        if cat == 3 and T["fl"][inv[P][0]] & 1:
            return "a two-handed weapon is worn"
        cur = self.score(bot, T, *inv[P + cat - 1])
        sc = self.score(bot, T, i, b, s, d, m)
        if sc < 0:
            return "broken"
        if sc <= cur + 0.01:
            return "score %.1f, worn %.1f" % (sc, cur)
        return "better (score %.1f, worn %.1f): will be worn" % (sc, cur)

    FIELDS = (("id", "c_pack"), ("b", "c_packb"), ("s", "c_packs"), ("d", "c_packd"), ("m", "c_packm"))

    def swap(self, bot, f, p, q):
        """swap the items of the positions p and q (pack 0.., worn PACK_N..) in memory and in f"""
        e, L = bot.emu, bot.emu.L
        for k, a in self.FIELDS:
            x, y = f[k][p], f[k][q]
            e.poke(L[a] + p, y); e.poke(L[a] + q, x)
            f[k][p], f[k][q] = y, x

    def act(self, bot):
        e, L = bot.emu, bot.emu.L
        bot.gear_check = False
        bot.inv_check = True
        T = bot.tables()
        f, n = self.items(bot)
        P = L["PACK_N"]
        st, dx = e.b(L["s_str"]), e.b(L["s_dex"])
        it = lambda k: [f[x][k] for x in ("id", "b", "s", "d", "m")]
        name = lambda k: bot.item_name(f["id"][k], f["b"][k], f["s"][k]) if f["id"][k] else "-"
        changed = False
        for slot, cat in ((0, 1), (1, 2), (2, 3)):
            cur = self.score(bot, T, *it(P + slot))
            best, bi = cur, None
            for p in range(P):
                i = f["id"][p]
                if not i or T["cat"][i] != cat:
                    continue
                r = T["req"][i]
                if (r & 0x7f) > (dx if r & 0x80 else st):
                    continue
                if cat == 3 and T["fl"][f["id"][P]] & 1:   # no shield with a two-handed weapon
                    continue
                sc = self.score(bot, T, *it(p))
                if cat == 1 and T["fl"][i] & 1 and f["id"][P + 2]:
                    # (22/11) a two-handed weapon while a shield is worn: only if it is clearly better (30%) and the pack has
                    # a free place for the shield
                    if sc < 1.3 * max(cur, 0.1) or 0 not in f["id"][:P]:
                        continue
                if sc > best + 0.01:
                    best, bi = sc, p
            if bi is not None:
                old = name(P + slot)
                self.swap(bot, f, bi, P + slot)
                changed = True
                bot.log.event("wear", level=bot.world.level, slot=("weapon", "armor", "shield")[slot], item=name(P + slot),
                              score=round(best, 1), took_off=old, old_score=round(cur, 1))
                bot.log.count("worn")
                if slot == 0 and T["fl"][f["id"][P]] & 1 and f["id"][P + 2]:
                    free = f["id"][:P].index(0)
                    bot.log.event("take_off", level=bot.world.level, slot="shield", item=name(P + 2), why="two-handed weapon")
                    self.swap(bot, f, free, P + 2)
        for p in range(P):                                 # rings: a free ring slot takes any ring that is not cursed
            i = f["id"][p]
            if i and T["cat"][i] == 4 and not any(sgn(T["val_af"][k]) < 0 for k in rows(L, f["b"][p], f["s"][p])):
                slot = next((k for k in (3, 4) if not f["id"][P + k]), None)
                if slot is not None:
                    self.swap(bot, f, p, P + slot)
                    changed = True
                    bot.log.event("wear", level=bot.world.level, slot="ring", item=name(P + slot), score="-", took_off="-", old_score="-")
                    bot.log.count("worn")
        if changed:
            e.call("recalc_stats")


def sgn(b):
    return b - 256 if b > 127 else b


def rows(L, b, s):
    """rows of af_pw / af_val of an item with prefix b and suffix s (a unique: its 4 rows)"""
    out = [b] if b else []
    if s >= 0x80:
        out += [L["UN0"] + 4 * (s & 0x7f) + k for k in range(4)]
    elif s:
        out.append(L["AF_SX0"] + s)
    return out


class Stats(Capability):
    """spend the stat points (SHORTCUT: c_sadd + recalc_stats, as the C screen): strength up to what the best weapon seen
    asks, then dexterity up to 18 (attack speed), then constitution"""
    name = "stats"
    def ready(self, bot):
        return bot.world.hero.in_game and bot.world.hero.lvl != bot.stat_lvl
    def act(self, bot):
        e, L = bot.emu, bot.emu.L
        bot.stat_lvl = bot.world.hero.lvl
        while e.call("pts_avail")["a"]:
            st, dx = e.b(L["s_str"]), e.b(L["s_dex"])
            k = 0 if st < 18 else 1 if dx < 18 else 2
            e.poke(L["c_sadd"] + k, e.b(L["c_sadd"] + k) + 1)
            e.call("recalc_stats")
            bot.log.event("stat", stat="str dex con".split()[k], hero_level=bot.stat_lvl)
        bot.gear_check = True


class Descend(Capability):
    """the stairs down are on the screen memory and the level is done (no chest left, enough of it explored): go and fire"""
    name = "descend"
    def stairs(self, bot):
        return bot.world.find_seen(bot.emu.L["T_STAIRSD"])
    def ready(self, bot):
        return bot.world.level > 0 and bool(self.stairs(bot)) and bot.level_done()
    def act(self, bot):
        w, h = bot.world, bot.world.hero
        st = set(self.stairs(bot))
        if (h.tx, h.ty) in st:
            bot.emu.tap_fire(3); return
        path = nav.bfs(w, (h.tx, h.ty), lambda x, y: (x, y) in st)
        if path:
            bot.emu.step(joy=bot.walker.follow(path), n=bot.walker.run)
        else:
            bot.explore_more = True


class Ascend(Capability):
    """a boss level (5, 10, 15) with the boss dead, or the bot wants the village: up the stairs, level after level
    (the stairs up are where the hero arrived: always seen)"""
    name = "ascend"
    def ready(self, bot):
        w = bot.world
        if w.level > 0 and w.level % 5 == 0 and not w.monsters and bot.explored_all:
            bot.going_up = True
        return w.level > 0 and bot.going_up
    def act(self, bot):
        w, h = bot.world, bot.world.hero
        st = set(w.find_seen(bot.emu.L["T_STAIRSU"]))
        if (h.tx, h.ty) in st:
            bot.emu.tap_fire(3); return
        path = nav.bfs(w, (h.tx, h.ty), lambda x, y: (x, y) in st)
        if path:
            bot.emu.step(joy=bot.walker.follow(path), n=bot.walker.run)
        else:
            bot.log.event("stuck", where="level %d: no path to the stairs up" % w.level)
            bot.going_up = False


class Explore(Capability):
    """walk to the nearest seen tile that has an unseen tile next to it"""
    name = "explore"
    def ready(self, bot):
        return bot.world.level > 0
    def act(self, bot):
        w, h = bot.world, bot.world.hero
        path = nav.bfs(w, (h.tx, h.ty), lambda x, y: nav.frontier(w, x, y))
        if path:
            bot.emu.step(joy=bot.walker.follow(path), n=bot.walker.run)
        else:
            bot.explored_all = True
            bot.emu.step()


class Town(Capability):
    """in the village (the whole map is known): sell what is not worn, fill the belt with potions (SHORTCUT: prices from the
    game's it_cost, no shop menu yet), then walk to the entrance of the dungeon and fire"""
    name = "town"
    def ready(self, bot):
        return bot.world.level == 0
    def act(self, bot):
        e, L, w, h = bot.emu, bot.emu.L, bot.world, bot.world.hero
        if bot.dead:
            bot.dead = False
        if not bot.town_done:
            bot.town_done = True
            self.trade(bot)
        bot.going_up = False
        if h.hp < h.hpmax:                                 # the healing place of the village: walking on it heals
            heal = set(w.find_seen(L["T_FOUNTAIN"]))
            path = nav.bfs(w, (h.tx, h.ty), lambda x, y: (x, y) in heal, passable=lambda x, y: w.walkable(x, y) or (x, y) in heal) if heal else None
            if path:
                bot.emu.step(joy=bot.walker.follow(path), n=bot.walker.run)
                bot.heal_tries += 1
                if bot.heal_tries < 400:
                    return
        bot.heal_tries = 0
        chap, unl = e.b(L["c_chap"]), e.b(L["c_unl"])
        if unl > chap:                                     # the chapter boss is dead: the exit of the village is open
            goal = {(e.b(L["tx_exit_x"] + k), e.b(L["tx_exit_y"] + k)) for k in range(L["TX_EXIT_N"])}
            what = "exit"
        else:                                              # the entrance of the dungeon (tk_stx, tk_sty: header of the village)
            goal = {(e.b(L["tk_stx"]), e.b(L["tk_sty"]))}
            what = "entrance"
        if (h.tx, h.ty) in goal:
            if what == "exit":
                bot.log.event("chapter", done=chap)
                if bot.max_level <= 5 * chap:
                    bot.stop = "chapter %d done" % chap
                    return
                w.cache.clear(); w.level = -1              # another village, other levels
            bot.emu.tap_fire(3)
            bot.town_done = False
            return
        path = nav.bfs(w, (h.tx, h.ty), lambda x, y: (x, y) in goal)
        if path:
            bot.emu.step(joy=bot.walker.follow(path), n=bot.walker.run)
        elif not bot.town_reread:
            bot.town_reread = True                          # (the map may still be the one of the place before)
            w.read_map(); bot.emu.step(n=10)
        else:
            bot.log.event("stuck", where="village: no path to the %s %s from %d,%d" % (what, sorted(goal), h.tx, h.ty))
            bot.stop = "no path to the %s in the village" % what

    def trade(self, bot):
        """SHORTCUTS, with the game's prices (it_cost, itprice) and rules: take the gold of the inn chest, wear the best, sell
        the rest, buy from the smith the best weapon, armor and shield the hero's level and gold allow (the base items the
        smith can sell at that level: shop_items / shop_minl; no magic wares), then potions"""
        e, L = bot.emu, bot.emu.L
        T = bot.tables()
        P = L["PACK_N"]
        gold = e.w(L["c_gold"])
        chest = e.w(L["c_sgold"])
        take = min(chest, (L["GOLD_MAX"] - gold) // 10)
        if take > 0:
            gold += take * 10
            e.poke(L["c_sgold"], (chest - take) & 255, (chest - take) >> 8)
            e.poke(L["c_gold"], gold & 255, gold >> 8)
            bot.log.event("withdraw", gold=take * 10, chest_left=(chest - take) * 10)
        bot.gear.act(bot)
        gold = self.sell(bot, gold)
        gold = self.smith(bot, gold)
        bot.gear.act(bot)
        gold = self.sell(bot, gold)
        belt = e.mem(L["c_beltt"], 4)
        pot = L["I_POTR"]
        price = T["price"][pot]
        bought = 0
        for s in range(4):
            if not belt[s] and gold >= price:
                e.poke(L["c_beltt"] + s, pot); gold -= price; bought += 1
                bot.log.count("potions_bought")
        if bought:
            bot.log.event("buy", item="red potion", count=bought, gold=bought * price, gold_left=gold)
        elif not all(belt):
            bot.log.event("no_gold", wanted="red potion", price=price, gold=gold)
        e.poke(L["c_gold"], gold & 255, gold >> 8)
        e.poke(L["hud_dirty"], 1)
        bot.inv_check = True
        bot.inv = None                                     # (bought and sold items are not "found")

    def sell(self, bot, gold):
        e, L = bot.emu, bot.emu.L
        T = bot.tables()
        P = L["PACK_N"]
        ids = e.mem(L["c_pack"], P); bs = e.mem(L["c_packb"], P); ss = e.mem(L["c_packs"], P)
        for p in range(P):                                 # the gear left in the pack (Gear already wore the best)
            i = ids[p]
            if i and T["cat"][i] in (1, 2, 3, 4):
                e.call("it_cost", regs="a=%02x,x=%02x,y=%02x" % (i, bs[p], ss[p]))
                v = (e.b(L["tmp0"]) + 256 * e.b(L["tmp1"])) >> L["SELL_SHIFT"]
                gold = min(L["GOLD_MAX"], gold + v)
                for a in ("c_pack", "c_packb", "c_packs", "c_packd", "c_packm"): e.poke(L[a] + p, 0)
                bot.log.event("sell", item=bot.item_name(i, bs[p], ss[p]), gold=v, gold_now=gold)
                bot.log.count("sold")
        e.poke(L["c_gold"], gold & 255, gold >> 8)
        return gold

    def smith(self, bot, gold):
        e, L, h = bot.emu, bot.emu.L, bot.world.hero
        T = bot.tables()
        P = L["PACK_N"]
        n = L["N_ITEMS"]
        items = e.mem(L["shop_items"], 33); minl = e.mem(L["shop_minl"], 33)
        st, dx = e.b(L["s_str"]), e.b(L["s_dex"])
        # the wares the bot can choose from at this visit (the shortcut's list: the base items of the smith for this hero
        # level, not the random wares of the real shop screen), with price, score and what the hero cannot use
        wares = []
        for i, ml in zip(items, minl):
            if i < n and T["cat"][i] in (1, 2, 3) and ml <= h.lvl:
                r = T["req"][i]
                no = (r & 0x7f) > (dx if r & 0x80 else st)
                wares.append("%s %d (score %.1f%s)" % (bot.item_name(i, 0, 0), T["price"][i], bot.gear.score(bot, T, i, 0, 0, 1, 1),
                                                       ", needs %s %d" % ("dex" if r & 0x80 else "str", r & 0x7f) if no else ""))
        bot.log.event("shop", shop="smith", hero_level=h.lvl, gold=gold, wares="; ".join(wares))
        for slot, cat in ((0, 1), (1, 2), (2, 3)):
            inv = bot.inventory()
            cur = bot.gear.score(bot, T, *inv[P + slot])
            two = T["fl"][inv[P][0]] & 1
            best, bi = cur, None
            for i, ml in zip(items, minl):
                if i >= n or T["cat"][i] != cat or ml > h.lvl or T["price"][i] > gold:
                    continue
                r = T["req"][i]
                if (r & 0x7f) > (dx if r & 0x80 else st):
                    continue
                if cat == 1 and T["fl"][i] & 1:            # v1: the bot buys one-handed weapons (it keeps the shield)
                    continue
                if cat == 3 and two:
                    continue
                sc = bot.gear.score(bot, T, i, 0, 0, 1, 1)
                if sc > best + 0.01:
                    best, bi = sc, i
            if bi is None or 0 not in [x[0] for x in inv[:P]]:
                continue
            gold -= T["price"][bi]
            e.poke(L["c_gold"], gold & 255, gold >> 8)
            e.poke(L["ap_b"], 0); e.poke(L["ap_s"], 0); e.poke(L["ap_m"], 0)
            e.call("add_to_pack", regs="a=%02x" % bi)       # the game rolls the durability, as for a bought item
            bot.log.event("buy", item=bot.item_name(bi, 0, 0), slot=("weapon", "armor", "shield")[slot], gold=T["price"][bi],
                          gold_left=gold, score=round(best, 1), old_score=round(cur, 1), hero_level=h.lvl)
            bot.log.count("bought")
        return gold
