#!/usr/bin/env python3
"""(24/11) Arena with the code of level 10 (out/work/arena_ovl_boss2.prg at OVP_AT = $F4E0 in the ARENA build): Mother Stitch
gets her fixed type and life (CB2_TYPE, CB2_HP), holds at least one rite; the bot "adds" (src/test/arena.asm BOT 2: the other
monsters first, then the boss, around obstacles) kills fetishes; the series is repeatable (seed + k per fight)."""
import os, sys
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "tools", d) for d in ("build", "vice", "atlas", "simulators")]
import arena as AR

O = AR.labels("arena_ovl_boss2.lbl")
G = AR.G
sc = dict(lvl=10, plvl=11, weapon="sword+1", armor="chain_mail+1", shield="tower_shield+1", potions={"yellow": 4}, pot=0.35,
          monsters=["lich"], boss=1, fights=3, bot="adds")
with AR.Arena() as a:
    r1 = a.run(**sc)
    a.v.cmd("bank ram")
    wave = a.v.mem(O["dm_wave"], 1)[0]
    a.v.cmd("bank cpu")
    types = a.v.mem(G["mtype"], 1)
    r2 = a.run(**sc)
k = ("win", "lose", "timeout", "frames", "dealt", "taken", "kills")
bad = []
if r1["m0"]["hp"] != G["CB2_HP"]: bad.append("boss life %d, expected CB2_HP %d" % (r1["m0"]["hp"], G["CB2_HP"]))
if r1["fights"] != 3 or r1["win"] + r1["lose"] + r1["timeout"] != 3: bad.append("fights %s" % r1["fights"])
if wave < 1: bad.append("no rite (dm_wave %d)" % wave)
if r1["kills"] < 3: bad.append("fetishes not killed (kills %d in 3 fights)" % r1["kills"])
if types[0] != G["CB2_TYPE"]: bad.append("boss type %d, expected %d" % (types[0], G["CB2_TYPE"]))
if [r1[x] for x in k] != [r2[x] for x in k]: bad.append("not repeatable: %s / %s" % ([r1[x] for x in k], [r2[x] for x in k]))
print("arena stitch:", "ok" if not bad else "ERRORE " + "; ".join(bad), {x: r1[x] for x in k})
sys.exit(1 if bad else 0)
