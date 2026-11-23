#!/usr/bin/env python3
"""(23/11) Arena with the code of the level (tools/vice/arena.py, out/work/arena_ovl_boss1.prg at OVP_AT = $F4E0 in the ARENA
build): the Hollow Abbot on level 5 gets his fixed type and life (CB1_TYPE, CB1_HP), summons skeletons below 2/3 and 1/3 of his
life and rages under 30%; the series is repeatable (seed + k per fight)."""
import os, sys
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "tools", d) for d in ("build", "vice", "atlas", "simulators")]
import arena as AR

O = AR.labels("arena_ovl_boss1.lbl")
G = AR.G
sc = dict(lvl=5, plvl=7, weapon="sword+1", armor="chain_mail+1", shield="medium_shield+1", potions={"red": 4}, pot=0.35,
          monsters=["skeleton_king"], boss=1, fights=3)
with AR.Arena() as a:
    r1 = a.run(**sc)
    a.v.cmd("bank ram")
    wave, rage = a.v.mem(O["ab_wave"], 1)[0], a.v.mem(O["abx_rage"], 1)[0]
    a.v.cmd("bank cpu")
    types = a.v.mem(G["mtype"], 4)
    r2 = a.run(**sc)
k = ("win", "lose", "timeout", "frames", "dealt", "taken", "kills")
bad = []
if r1["m0"]["hp"] != G["CB1_HP"]: bad.append("boss life %d, expected CB1_HP %d" % (r1["m0"]["hp"], G["CB1_HP"]))
if r1["fights"] != 3 or r1["win"] + r1["lose"] + r1["timeout"] != 3: bad.append("fights %s" % r1["fights"])
if r1["win"] and (wave != 2 or rage != 1): bad.append("last fight won but ab_wave %d abx_rage %d" % (wave, rage))
if r1["win"] and r1["kills"] <= r1["win"]: bad.append("no summoned skeleton killed (kills %d)" % r1["kills"])
if types[0] != G["CB1_TYPE"]: bad.append("boss type %d, expected %d" % (types[0], G["CB1_TYPE"]))
if [r1[x] for x in k] != [r2[x] for x in k]: bad.append("not repeatable: %s / %s" % ([r1[x] for x in k], [r2[x] for x in k]))
print("arena boss:", "ok" if not bad else "ERRORE " + "; ".join(bad), {x: r1[x] for x in k})
sys.exit(1 if bad else 0)
