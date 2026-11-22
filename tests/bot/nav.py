"""Bot, layer 3: walking. Breadth-first paths on the tiles the bot has seen, and a pixel controller that follows them
(the hero is a 10 x 10 pixel box that moves 2 pixels a frame: it must be near the middle of a tile to enter a corridor)."""
import collections, random
from emu import UP, DOWN, LEFT, RIGHT

W = 48
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def bfs(world, start, goal_fn, passable=None, limit=4000):
    """shortest path of tiles from start to the first tile for which goal_fn is true (start excluded, goal included);
    only seen and walkable tiles (or passable(x, y)). None if there is none."""
    ok = passable or (lambda x, y: world.known(x, y) and world.walkable(x, y))
    prev = {start: None}
    q = collections.deque([start])
    while q and len(prev) < limit:
        cur = q.popleft()
        if cur != start and goal_fn(*cur):
            path = []
            while cur != start:
                path.append(cur); cur = prev[cur]
            return path[::-1]
        for dx, dy in N4:
            nb = (cur[0] + dx, cur[1] + dy)
            if nb not in prev and 0 <= nb[0] < W and 0 <= nb[1] < W and (ok(*nb) or goal_fn(*nb)):
                prev[nb] = cur; q.append(nb)
    return None


def frontier(world, x, y):
    """a seen walkable tile with a tile not seen yet next to it"""
    return world.known(x, y) and world.walkable(x, y) and any(not world.known(x + dx, y + dy) for dx, dy in N4)


class Walker:
    def __init__(self, world):
        self.w = world
        self.last = None
        self.still = 0
        self.run = 1

    def toward(self, px, py, slack=2):
        """joystick bits to move the hero toward the pixel (px, py)"""
        h = self.w.hero
        j = 0
        if px - h.px > slack: j |= RIGHT
        elif h.px - px > slack: j |= LEFT
        if py - h.py > slack: j |= DOWN
        elif h.py - py > slack: j |= UP
        return j

    def follow(self, path):
        """joystick bits for the next step of a path of tiles; first to the middle of the hero's own tile on the axis
        across the movement (so the box does not catch the corners), then to the middle of the next tile"""
        h = self.w.hero
        if not path:
            return 0
        nx, ny = path[0]
        cx, cy = h.tx * 16 + 8, h.ty * 16 + 8
        tx, ty = nx * 16 + 8, ny * 16 + 8
        if nx != h.tx and abs(h.py - cy) > 2:
            j = self.toward(h.px, cy)
        elif ny != h.ty and abs(h.px - cx) > 2:
            j = self.toward(cx, h.py)
        else:
            j = self.toward(tx, ty)
        # frames this joystick can be held before the next decision: 2 pixels a frame toward the target of this step
        d = max(abs(tx - h.px), abs(ty - h.py)) if j == self.toward(tx, ty) else max(abs(h.px - cx), abs(h.py - cy))
        self.run = max(1, min(6, d // 2))
        pos = (h.px, h.py)
        self.still = self.still + 1 if pos == self.last else 0
        self.last = pos
        if self.still > 6:                                 # stuck (a monster in the way, a corner): a random nudge
            self.still = 0
            j = random.choice((UP, DOWN, LEFT, RIGHT))
        return j
