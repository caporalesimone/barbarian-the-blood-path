"""Bot, layer 2: what the bot knows. Read from the game's memory with as few monitor commands as possible.
The hero and the monsters are read every decision; the map only when the level changes (and again after a chest is opened).
In a dungeon the bot does NOT use the whole map: `seen` holds the tiles that were on the screen (20 x 10 tiles around the
hero) and every decision is taken on those (World.known). In the village the whole map is known (owner's request)."""

W = 48
VIEW_X, VIEW_Y = 9, 5                                       # half size of the screen in tiles (40 x 20 characters)


class Hero:
    pass


class World:
    def __init__(self, emu):
        self.e = emu; self.L = emu.L
        self.level = -1
        self.map = []
        self.seen = set()
        self.solid = []
        self.cache = {}                                    # level -> seen tiles (the bot remembers the levels it walked)
        self.hero = Hero()
        self.hero.hpmax = 1
        self.monsters = []
        self.tick = 0; self.hp_lvl = -1; self.mon_lvl = -1

    # ---- reading
    def read(self):
        e, L, h = self.e, self.L, self.hero
        zp = e.mem(0x10, 0x10)
        h.px, h.py = zp[4] + 256 * zp[5], zp[6] + 256 * zp[7]
        h.tx, h.ty = h.px >> 4, h.py >> 4
        blk = e.mem(L["c_lvl"], L["c_beltt"] + 4 - L["c_lvl"])
        o = lambda n: L[n] - L["c_lvl"]
        h.lvl = blk[0]
        h.xp = blk[o("c_xp")] | blk[o("c_xp") + 1] << 8 | blk[o("c_xp") + 2] << 16
        h.gold = blk[o("c_gold")] | blk[o("c_gold") + 1] << 8
        h.hp = blk[o("c_hp")] | blk[o("c_hp") + 1] << 8
        h.belt = blk[o("c_beltt"):o("c_beltt") + 4]
        h.in_game = e.b(0x03f5) == 1
        lv = e.b(L["cur_level"])
        if lv != self.level:
            self.enter(lv)
        self.tick += 1
        if h.lvl != self.hp_lvl or self.tick % 16 == 0:     # the maximum life changes with the level and the gear
            self.hp_lvl = h.lvl
            h.hpmax = e.w(L["hpmax"])
        near = any(abs(m["tx"] - h.tx) <= VIEW_X + 2 and abs(m["ty"] - h.ty) <= VIEW_Y + 2 for m in self.monsters)
        if near or self.tick % 4 == 0 or lv != self.mon_lvl:  # monsters: every decision when one is close, else one in 4
            self.mon_lvl = lv
            self.read_monsters()
        if self.level:
            for y in range(max(0, h.ty - VIEW_Y), min(W, h.ty + VIEW_Y + 1)):
                for x in range(max(0, h.tx - VIEW_X), min(W, h.tx + VIEW_X + 1)):
                    self.seen.add((x, y))
        return h

    def enter(self, lv):
        if self.level >= 0:
            self.cache[self.level] = self.seen
        self.level = lv
        self.read_map()
        self.seen = self.cache.get(lv, set()) if lv else {(x, y) for x in range(W) for y in range(W)}

    def read_map(self):
        e, L = self.e, self.L
        m = []
        for a in range(0, W * W, 256):
            m += e.mem(L["MAP"] + a, 256)
        self.map = m[:W * W]
        self.solid = e.mem(L["solidtab"], 48)

    def read_monsters(self):
        e, L = self.e, self.L
        self.monsters = []
        if not self.level:
            return
        hd = e.mem(L["lb_cnt"], L["malive"] + 32 - L["lb_cnt"])     # lb_cnt, lb_boss, mtype, malive (LVLBLK)
        n, boss = hd[0], hd[L["lb_boss"] - L["lb_cnt"]]
        if not n:
            return
        types = hd[L["mtype"] - L["lb_cnt"]:]; alive = hd[L["malive"] - L["lb_cnt"]:]
        rt = e.mem(L["mxl"], 0x140)                         # mxl, mxh, myl, myh, mhp, ..., mwake, mhph: 32 bytes each
        o = lambda name: L[name] - L["mxl"]
        for i in range(n):
            if not alive[i]:
                continue
            x = rt[o("mxl") + i] + 256 * rt[o("mxh") + i]; y = rt[o("myl") + i] + 256 * rt[o("myh") + i]
            self.monsters.append(dict(i=i, x=x, y=y, tx=x >> 4, ty=y >> 4, type=types[i],
                                      hp=rt[o("mhp") + i] + 256 * rt[o("mhph") + i], awake=rt[o("mwake") + i], boss=(i + 1 == boss)))

    # ---- questions
    def tile(self, x, y):
        return self.map[y * W + x] if 0 <= x < W and 0 <= y < W else 0

    def walkable(self, x, y):
        t = self.tile(x, y)
        return t < 48 and not self.solid[t] & 1

    def known(self, x, y):
        return (x, y) in self.seen

    def find_seen(self, *tiles):
        return [(x, y) for (x, y) in self.seen if self.tile(x, y) in tiles]

    def visible_monsters(self):
        h = self.hero
        return [m for m in self.monsters if abs(m["tx"] - h.tx) <= VIEW_X and abs(m["ty"] - h.ty) <= VIEW_Y]
