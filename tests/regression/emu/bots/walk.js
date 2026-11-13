// Walk to tile (GX,GY) (constants prepended by the test after lib.js). Ends the loop when the hero is there.
const S = state; S.n = (S.n || 0) + 1;
if (S.n > 3000) { S.timeout = 1; return false; }
if (S.nopath) return false;
if (stepTo(S, GX, GY)) { joyOff(); S.arrived = S.n; return false; }
