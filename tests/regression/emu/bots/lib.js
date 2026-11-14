// Shared helpers for the bots that run INSIDE the emulator (c64.runLoop, vc64web). They read the game RAM through the
// labels of out/work/game.lbl and drive the hero through the joystick on port 2 only, like a player.
// The loop code is prepended with this file, so everything here is global for the bot that follows.
const W = 48, MP = c64.peek('MAP', 2304), SOL = c64.peek('solidtab', 48);
const solid = (x, y) => x < 0 || y < 0 || x >= W || y >= W || (SOL[MP[y * W + x]] & 1) === 1;
const PX = () => c64.peekWord('px'), PY = () => c64.peekWord('py');
const OFF = { up: false, down: false, left: false, right: false, fire: false };
const joyOff = () => c64.joy(2, OFF);
// breadth-first path over the walkable tiles (4 directions), from (sx,sy) to (gx,gy); null when unreachable
const bfs = (sx, sy, gx, gy) => {
  const q = [[sx, sy]], prev = new Map([[sy * W + sx, null]]);
  while (q.length) {
    const [x, y] = q.shift(); if (x === gx && y === gy) break;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const nx = x + dx, ny = y + dy, k = ny * W + nx;
      if (prev.has(k) || solid(nx, ny)) continue; prev.set(k, [x, y]); q.push([nx, ny]);
    }
  }
  if (!prev.has(gy * W + gx)) return null;
  const p = []; let c = [gx, gy]; while (c) { p.unshift(c); c = prev.get(c[1] * W + c[0]); } p.shift(); return p;
};
// one joystick step towards the centre of tile (gx,gy); true when the hero is there (+-7 px). S = the caller's memory.
// Tiles are 16 px; the hero box is about +-5 px, so a way point counts as reached at +-3 px.
const stepTo = (S, gx, gy) => {
  const px = PX(), py = PY();
  if (!S.path || S.goal !== gx + ',' + gy) { S.goal = gx + ',' + gy; S.path = bfs(px >> 4, py >> 4, gx, gy); S.stuck = 0; S.lp = px * 4096 + py; if (!S.path) { S.nopath = 1; return false; } }
  const w = S.path[0];
  if (!w) { joyOff(); return Math.abs(px - (gx * 16 + 8)) <= 7 && Math.abs(py - (gy * 16 + 8)) <= 7; }
  const wx = w[0] * 16 + 8, wy = w[1] * 16 + 8, dx = wx - px, dy = wy - py;
  if (Math.abs(dx) <= 3 && Math.abs(dy) <= 3) { S.path.shift(); return false; }
  const st = Object.assign({}, OFF);
  if (Math.abs(dx) >= Math.abs(dy)) { if (dx > 0) st.right = true; else st.left = true; } else { if (dy > 0) st.down = true; else st.up = true; }
  c64.joy(2, st);
  const cp = px * 4096 + py;
  if (cp === S.lp) { S.stuck++; if (S.stuck > 30) { S.path = null; S.stuck = 0; } } else { S.stuck = 0; S.lp = cp; }   // blocked: plan again
  return false;
};
