#!/usr/bin/env python3
"""Oro raccoglibile nel dungeon (data/balance.yaml: drops, chests, spawn) e oro dei bauli epici.

Per piano: mostri medi (fra minimo e massimo della tabella spawn) + boss; per mostro un tiro: gold_only
(drops.gold: min..max + per_dungeon_level x piano) o tesoro (chest_level -> T = CL/8, oro T x 3..7); bauli del
piano (stima: 2,5 per piano, T = piano + offset medio). Stampa il totale 1..19 e il 10% diviso sui 4 bauli
epici (chests.final_gold).

Tetto dell'oro addosso (08/11 sera, TODO 1.7): player.gold_max (10000) come nel gioco (add_gold16): l'oro raccolto
oltre il tetto si perde; nel baule di casa (c_sgold, in decine dal 10/11) fino a 655350, solo multipli di 10. Si simula un giocatore che porta l'oro a casa
ogni N piani (N = 1, 3, 5, mai): per ogni strategia oro addosso, nel baule e perso. Niente spese (negozi,
riparazioni): e' il caso peggiore per il tetto. Uso: python3 tools/simulators/sim_gold.py"""
import os, sys, yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build"))   # (13/11) generatori in tools/build/
import rules as RU

import bestiary
B = bestiary.load_balance()       # balance.yaml + mostri (data/monsters/bestiary.tsv, 11/11)
SP, DR, CH, CL = B["spawn"], B["drops"], B["chests"], B["chest_level"]
NF = B["constants"]["max_dungeon_level"]
steps = B["constants"]["difficulty_steps"]


def step(L):
    """come tools/build/gen_db.py: l'ultimo piano usa l'ultimo gradino, gli altri 1..steps-1"""
    return steps if L == NF else max(1, min(steps - 1, round(L * (steps - 1) / (NF - 1))))


GOLD_MAX = B["player"]["gold_max"]
START = B["player"].get("start_gold", 0)
STASH_MAX = 65535 * 10          # 10/11: il baule conta le decine (c_sgold), al massimo 655350 monete


def per_floor(lo=1, hi=None, abyss=False):
    """oro medio raccolto in ogni piano lo..hi (default 1..NF-1: mostri + boss + bauli del piano).
    abyss=True (10/11, ipotesi): per i piani 21+ si usa il gradino dell'ultimo piano casuale (22 mostri al massimo, 11 al
    minimo) e chestLevel = 8 x piano (T = piano), come nei piani normali; da verificare con TODO 5.2."""
    g = CH["gold_amount"]
    out = []
    for L in range(lo, (hi or NF - 1) + 1):
        s = (steps - 1 if abyss else step(L)) - 1
        n = (SP["max_monsters_per_level"][s] + SP["min_monsters_per_level"][s]) / 2 + 1
        gold_only = DR["outcome"]["gold_only"] / 100 * ((DR["gold"]["min"] + DR["gold"]["max"]) / 2 + DR["gold"]["per_dungeon_level"] * L)
        t = (CL["per_floor"] * L + 2) // CL["per_floor"]
        chest = DR["outcome"]["chest"] / 100 * t * (g["min_per_loot_level"] + g["max_per_loot_level"]) / 2
        boss_chest = (t + B["boss"]["loot_level_add"] // CL["per_floor"]) * (g["min_per_loot_level"] + g["max_per_loot_level"]) / 2
        out.append(n * min(255, gold_only + chest) + boss_chest + 2.5 * (L + 2) * (g["min_per_loot_level"] + g["max_per_loot_level"]) / 2)
    return out


def cap_table():
    """strategie di deposito: oro addosso, nel baule e perso alla fine dei piani 1..NF-1"""
    pf = per_floor()
    print("\ntetto addosso %d (player.gold_max), baule %d: oro perso per strategia di deposito (senza spese)" % (GOLD_MAX, STASH_MAX))
    print("%-16s %9s %9s %9s %12s" % ("deposito", "addosso", "baule", "perso", "primo piano"))
    for every in (1, 3, 5, 0):
        carried, stash, lost, first = float(START), 0.0, 0.0, None
        for L, g in enumerate(pf, 1):
            room = GOLD_MAX - carried
            take = min(g, room)
            if g > room and first is None:
                first = L
            lost += g - take
            carried += take
            if every and L % every == 0:              # ritorno a casa: nel baule solo multipli di 10 (st_gold, 10/11)
                mv = min(int(carried) // 10 * 10, STASH_MAX - stash)
                stash += mv
                carried -= mv
        name = "ogni %d piani" % every if every else "mai"
        print("%-16s %9.0f %9.0f %9.0f %12s" % (name, carried, stash, lost, first if first else "-"))


def abyss_table(n=10):
    """oro dei primi n piani dell'Abisso (21..20+n) e fino a che piano basta ogni tetto dell'oro addosso"""
    pf = per_floor(NF + 1, NF + n, abyss=True)
    print("\nAbisso, primi %d piani (ipotesi: stessa scheda di spawn del piano 19, chestLevel = 8 x piano, tutto raccolto)" % n)
    print("%5s %9s %10s" % ("piano", "oro/piano", "cumulato"))
    c = 0.0
    for i, g in enumerate(pf):
        c += g
        print("%5d %9.0f %10.0f" % (NF + 1 + i, g, c))
    print("\noro per piano nei piani normali: 1 -> %.0f, 10 -> %.0f, 19 -> %.0f; Abisso 21 -> %.0f, %d -> %.0f" % (
        per_floor(1, 1)[0], per_floor(10, 10)[0], per_floor(19, 19)[0], pf[0], NF + n, pf[-1]))


def floor_gold(L):
    """oro medio raccolto al piano L (1..19 normali, 20 sala del trono, 21+ Abisso), stessa stima di per_floor ma con i
    tetti del gioco (ipotesi per l'Abisso, vedi abyss_table): oro del mostro min(255, 12..40 + 6 x piano) prima del peso,
    chestLevel = min(255, 8 x piano), T = CL/8; piano 20: solo i 4 bauli epici (final_gold ciascuno)."""
    g = CH["gold_amount"]
    avg_g = (g["min_per_loot_level"] + g["max_per_loot_level"]) / 2
    if L == NF:
        return 4 * CH["final_gold"]
    s = (steps - 1 if L > NF else step(L)) - 1
    n = (SP["max_monsters_per_level"][s] + SP["min_monsters_per_level"][s]) / 2 + 1
    t = min(255, CL["per_floor"] * L + 2) // CL["per_floor"]
    gold_only = DR["outcome"]["gold_only"] / 100 * min(255, (DR["gold"]["min"] + DR["gold"]["max"]) / 2 + DR["gold"]["per_dungeon_level"] * L)
    chest = DR["outcome"]["chest"] / 100 * t * avg_g
    boss_t = min(255, CL["per_floor"] * L + B["boss"]["loot_level_add"]) // CL["per_floor"]
    return n * (gold_only + chest) + boss_t * avg_g + 2.5 * min(t + 2, 255 // CL["per_floor"]) * avg_g


def table_floors(n=100, csv=None):
    """tabella piano per piano 1..n: oro del piano e cumulato (tutto raccolto, nessuna spesa)"""
    rows, c = [], 0.0
    for L in range(1, n + 1):
        g = floor_gold(L)
        c += g
        rows.append((L, g, c))
    if csv:
        with open(csv, "w") as f:
            f.write("piano;oro_del_piano;oro_cumulato\n")
            for L, g, c in rows:
                f.write("%d;%.0f;%.0f\n" % (L, g, c))
    else:
        print("%5s %10s %10s" % ("piano", "oro piano", "cumulato"))
        for L, g, c in rows:
            print("%5d %10.0f %10.0f" % (L, g, c))
    return rows


def main():
    tot = 0.0
    g = CH["gold_amount"]
    print("%5s %7s %8s %8s %8s" % ("piano", "mostri", "oro mob", "oro ch", "totale"))
    for L in range(1, NF):
        s = step(L) - 1
        n = (SP["max_monsters_per_level"][s] + SP["min_monsters_per_level"][s]) / 2 + 1   # + boss
        gold_only = DR["outcome"]["gold_only"] / 100 * ((DR["gold"]["min"] + DR["gold"]["max"]) / 2 + DR["gold"]["per_dungeon_level"] * L)
        t = (CL["per_floor"] * L + 2) // CL["per_floor"]
        chest = DR["outcome"]["chest"] / 100 * t * (g["min_per_loot_level"] + g["max_per_loot_level"]) / 2
        boss_chest = (t + B["boss"]["loot_level_add"] // CL["per_floor"]) * (g["min_per_loot_level"] + g["max_per_loot_level"]) / 2
        mob = n * min(255, gold_only + chest) + boss_chest
        floor_chests = 2.5 * (L + 2) * (g["min_per_loot_level"] + g["max_per_loot_level"]) / 2
        tot += mob + floor_chests
        print("%5d %7.1f %8.0f %8.0f %8.0f" % (L, n, mob, floor_chests, tot))
    print("\ntotale piani 1..%d: %.0f oro; 10%% = %.0f -> %d per baule epico (4 bauli); balance.yaml final_gold = %d" %
          (NF - 1, tot, tot / 10, round(tot / 40), CH["final_gold"]))
    cap_table()
    abyss_table()


if __name__ == "__main__":
    if "--floors" in sys.argv:       # python3 tools/simulators/sim_gold.py --floors 100 [file.csv]
        i = sys.argv.index("--floors")
        table_floors(int(sys.argv[i + 1]), sys.argv[i + 2] if len(sys.argv) > i + 2 else None)
    else:
        main()
