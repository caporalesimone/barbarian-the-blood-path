#!/usr/bin/env python3
"""The bot that plays the game by itself in VICE (22/11, owner's request): see README.md in this folder.
Usage (in the lab64-tools container, from the project folder):
    lab64 run python3 tests/bot/run.py [--max-level N] [--minutes M] [--seed abc123] [--name run1]
--max-level: stop when the hero enters a level deeper than N (default 19); --minutes: real-time limit (default 20);
--max-deaths N: stop at the N-th death; --cheat potions gold: see README.md (the cheats are written in the report)."""
import argparse, os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu                                         # noqa: E402
from brain import Bot                                       # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-level", type=int, default=19)
    ap.add_argument("--minutes", type=float, default=20)
    ap.add_argument("--seed", default="abc123")
    ap.add_argument("--name", default="run")
    ap.add_argument("--max-deaths", type=int, default=0, help="stop after this many deaths (0 = no limit)")
    ap.add_argument("--cheat", nargs="*", default=[], choices=["potions", "gold"],
                    help="potions: a red potion appears in the belt when it is empty; gold: 10000 gold in the inn chest at the start")
    a = ap.parse_args()
    seed = [(ord(c) - 48) if c.isdigit() else (ord(c.lower()) - 87) for c in a.seed][:6]
    print("seed", a.seed, "cheats", a.cheat or "-", flush=True)
    emu = Emu(seed=seed)
    bot = None
    try:
        emu.start()
        bot = Bot(emu, max_level=a.max_level, max_seconds=a.minutes * 60, cheats=set(a.cheat), max_deaths=a.max_deaths)
        bot.run()
    except Exception:
        traceback.print_exc()
        try:                                               # where is the machine? (a loop that never reads the input)
            emu.g.running = True
            print("registers:", emu.g.cmd("r").strip().splitlines()[-1])
            print("stack:", " ".join("%02x" % b for b in emu.g.mem(0x01e0, 32)))
            print("hook vars:", emu.g.mem(0x03f0, 6), "hp", emu.g.w16(emu.L["c_hp"]), "level", emu.g.b(emu.L["cur_level"]))
        except Exception as x:
            print("no registers:", x)
        if bot:
            bot.log.close("error")
    finally:
        if bot:
            bot.log.events.insert(0, dict(kind="run", at=0, seed=a.seed, cheats=" ".join(a.cheat) or "-", max_level=a.max_level, max_deaths=a.max_deaths))
        print("report:", bot.log.write(a.name))
        emu.close()


if __name__ == "__main__":
    main()
