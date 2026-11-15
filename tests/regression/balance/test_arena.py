#!/usr/bin/env python3
"""Arena (ARENA build + tools/vice/arena.py): a short series must end, be repeatable and give sensible numbers (a
well-equipped level-5 hero against a level-1 monster: always wins)."""
import os, sys
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "tools", d) for d in ("build", "vice", "atlas", "simulators")]
import arena as AR

with AR.Arena() as a:
    sc = dict(lvl=1, plvl=5, weapon="sword", armor="leather_armor", shield="small_shield", ring="copper+3", potions={"red": 2}, pot=0.4, monsters=["skeleton", "fallen"], fights=4)
    r1, r2 = a.run(**sc), a.run(**sc)
k = ("win", "lose", "timeout", "frames", "dealt", "taken", "kills")
ok = (r1["status"] == 1 and r1["fights"] == 4 and r1["win"] == 4 and r1["kills"] == 8 and r1["dealt"] > 0
      and [r1[x] for x in k] == [r2[x] for x in k])
print("arena:", "ok" if ok else "ERRORE", {x: r1[x] for x in k})
sys.exit(0 if ok else 1)
