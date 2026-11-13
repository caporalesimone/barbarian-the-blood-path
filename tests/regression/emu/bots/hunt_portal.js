// In the crypt: hunt the nearest monster, kill it with the basic attack (fire), read the portal scroll (key 5), walk to
// the portal that appears at (c_retx, c_rety) and step on it with fire. Ends when the hero is back in the village.
// state.log: what happened, in order; state.end: 'dead' | 'timeout' | 'village' | 'no effect'.
const S = state; S.n = (S.n || 0) + 1; S.ph = S.ph || 'hunt'; S.log = S.log || [];
const mon = k => ({ x: c64.peek('mxl', 32)[k] | (c64.peek('mxh', 32)[k] << 8), y: c64.peek('myl', 32)[k] | (c64.peek('myh', 32)[k] << 8), hp: c64.peek('mhp', 32)[k] | (c64.peek('mhph', 32)[k] << 8) });
const px = PX(), py = PY(), hp = c64.peekWord('c_hp');
if (S.n > 5000) { S.log.push('timeout ' + S.ph); S.end = 'timeout'; return false; }
if (hp === 0) { S.log.push('hero dead'); S.end = 'dead'; return false; }
if (S.ph === 'hunt') {
  if (S.t === undefined || mon(S.t).hp === 0) {
    if (S.t !== undefined) { S.ph = 'after'; S.a0 = S.n; S.log.push('killed ' + S.t); joyOff(); return; }
    let best = 1e9;
    for (let k = 0; k < 32; k++) { const m = mon(k); if (m.hp > 0 && (m.x || m.y)) { const d = Math.hypot(m.x - px, m.y - py); if (d < best) { best = d; S.t = k; } } }
    if (S.t === undefined) { S.log.push('no monster'); S.end = 'no monster'; return false; }
    S.log.push('target ' + S.t + ' hp ' + mon(S.t).hp); S.hp0 = mon(S.t).hp;
  }
  const m = mon(S.t), dx = m.x - px, dy = m.y - py, ad = Math.hypot(dx, dy);
  if (ad <= 34) {                                   // in reach: face it and attack (fire pressed every other pair of frames)
    const st = Object.assign({}, OFF);
    if (Math.abs(dy) >= Math.abs(dx)) { if (dy < 0) st.up = true; else st.down = true; } else { if (dx < 0) st.left = true; else st.right = true; }
    if (S.n % 4 < 2) st.fire = true;
    c64.joy(2, st);
  } else { S.sub = S.sub || {}; stepTo(S.sub, m.x >> 4, m.y >> 4); }
  return;
}
if (S.ph === 'after') {                             // read the scroll: key 5 (belt/pack slot of the scroll)
  joyOff();
  if (S.n - S.a0 === 30) c64.keyDown('5');
  if (S.n - S.a0 === 33) c64.keyUp('5');
  if (S.n - S.a0 === 60) { S.rx = c64.peek('c_retx', 1)[0]; S.ry = c64.peek('c_rety', 1)[0]; S.portal = c64.peek('c_portal', 1)[0]; S.log.push('portal at ' + S.rx + ',' + S.ry + ' flag ' + S.portal); S.ph = 'toportal'; S.sub = {}; }
  return;
}
if (S.ph === 'toportal') { if (stepTo(S.sub, S.rx, S.ry)) { joyOff(); S.ph = 'fire'; S.f0 = S.n; } return; }
if (S.ph === 'fire') {
  const st = Object.assign({}, OFF); if (S.n - S.f0 < 2) st.fire = true; c64.joy(2, st);
  if (c64.peek('cur_level', 1)[0] === 0) { S.ph = 'village'; S.v0 = S.n; S.log.push('village'); }
  if (S.n - S.f0 > 60) { S.log.push('fire without effect'); S.end = 'no effect'; return false; }
  return;
}
if (S.ph === 'village') { joyOff(); if (S.n - S.v0 > 100) { S.end = 'village'; return false; } }
