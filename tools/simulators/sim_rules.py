#!/usr/bin/env python3
"""Simulatore delle regole NUOVE (docs/wiki/SISTEMA_COMBATTIMENTO.md, parametri data/rules.yaml) + report HTML.

Combattimento a eventi in fotogrammi PAL, come il gioco: il PG agisce dopo la ricarica globale (10) quando
un'abilita' e' pronta; ogni mostro attacca al contatto e poi ogni 45 fotogrammi; lo stordimento ferma la
ricarica del mostro. Il bot fa le stesse scelte del bot dell'arena (tools/vice/arena.py, fase 1): fermo davanti ai
mostri, abilita' migliore pronta (Rage/Frenzy appena pronte, Smash, Whirlwind e Battle Cry con >= 2 mostri),
pozione sotto il 35% della vita (con ricarica). Boss finale: evocazioni al 75/50/25% della vita.

Uso:
  python3 tools/simulators/sim_rules.py                      # tutte le prove + report out/work/simulators/simulazione_regole.html
  python3 tools/simulators/sim_rules.py --fights 100 --out x.html
  python3 tools/simulators/sim_rules.py --fight 5 9 skeleton skeleton fallen   # un gruppo: piano 5, PG livello 9

Da Python: from sim_rules import fight, series"""
import argparse, base64, io, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules as RU
from rules import R, NF, VMAX, Dice, Hero, monster, hit_chance

T = R["timing"]
SK = R["skills"]


class Mon:
    def __init__(self, st, rng):
        self.st = st
        # come mon_hp_init (src/game/combat.asm): vita MEDIA del tipo x (96 + rnd 0..64) / 128 (= +-25%), non i dadi
        self.hpmax = max(1, int(int(st["hp"].avg * st["hp_mult"]) * (96 + rng.randrange(65)) // 128))
        self.hp = self.hpmax
        self.ac, self.att, self.save = st["ac"], st["att"], st["save"]
        self.next = 1                       # primo colpo appena a contatto
        self.stun = 0
        self.alive = True

    def stun_for(self, t, s):
        until = t + s
        if until > self.stun:
            extra = until - max(self.stun, t)
            self.stun = until
            self.next += extra              # la ricarica del mostro si ferma


def attack_roll(rng, att, ac, crit=20, adv=False):
    d = rng.randint(1, 20)
    if adv:
        d = max(d, rng.randint(1, 20))
    if d == 1:
        return 0
    if d >= crit:
        return 2
    return 1 if d == 20 or d + att >= ac else 0


def potion_heal(p, hero):
    """cura di una pozione: 'heal' = formula con L (livello) e HP (vita massima), es. "20", "4*L+40", "HP//2";
    altrimenti heal_percent della vita massima. (15/11, TODO J4) Livello del PG > NF (Abisso): 'heal_abyss' (come il codice:
    pot_heal usa pab_val + pab_dn x livello oltre MAXLEVEL)"""
    if hero.level > NF and "heal_abyss" in p:
        return int(eval(str(p["heal_abyss"]), {}, {"L": hero.level, "HP": hero.hpmax}))
    if "heal" in p:
        return int(eval(str(p["heal"]), {}, {"L": hero.level, "HP": hero.hpmax}))
    return hero.hpmax * p["heal_percent"] // 100


def fight(hero, mons, rng, potions=None, final_boss=None, stats=None, pot_cfg=None, hp0=None, left=None):
    """hero: rules.Hero; mons: elenco di statistiche (rules.monster); final_boss: indice del boss finale (evocazioni).
    hp0: vita all'inizio (default piena); left: lista che riceve le pozioni rimaste (20/11, sim_floor.py).
    Ritorna (esito 'win'/'lose'/'time', fotogrammi, vita finale)."""
    pc = pot_cfg or R["potions"]
    hp = hero.hpmax if hp0 is None else hp0
    ms = [Mon(m, rng) for m in mons]
    pend = []                               # evocazioni in arrivo: (tempo, Mon)
    wave = 0
    pots = list(potions if potions is not None else hero.potions)
    pot_ready = 0
    cd = {k: 0 for k in SK if isinstance(SK[k], dict)}
    avail = hero.skills()
    rage_until = frenzy_until = 0
    t = 0
    nxt = 0
    st = stats if stats is not None else {}
    for k in ("pg_swings", "pg_hits", "m_swings", "m_hits", "dealt", "taken", "healed", "pots", "run_bonus", "frenzy_t"):
        st.setdefault(k, 0)
    run = 0                                 # Frenzy: bonus di corsa in % (statistica)

    def hit(m, times=1, adv=False, dice_x=1):
        nonlocal t, run
        for _ in range(times):
            if not m.alive:
                return
            st["pg_swings"] += 1
            r = attack_roll(rng, hero.att, m.ac - hero.pen, hero.crit, adv)
            if not r:
                continue
            st["pg_hits"] += 1
            if t < frenzy_until:
                fz = SK["frenzy"]
                run = min(fz["run_max"], run + (fz["run_step"] if run else fz["run_first"]))
            dmg = hero.dice.roll(rng, times=dice_x * (2 if r == 2 else 1)) + hero.dmg_k
            if t < rage_until:
                dmg += hero.rage_bonus()
            dmg = max(1, dmg)
            d = min(dmg, m.hp)
            m.hp -= dmg
            st["dealt"] += d
            if not m.st.get("stun_immune") and not m.st.get("boss"):   # boss con nome e finale: niente blocco da colpo
                m.stun_for(t, T["stun_on_hit"])
            if m.hp <= 0:
                m.alive = False

    while t < T["max_frames"]:
        alive = [m for m in ms if m.alive]
        if not alive and not pend:
            if left is not None:
                left[:] = pots
            return "win", t, hp
        # prossimo evento
        times = [nxt] + [max(m.next, m.stun) for m in alive] + [p[0] for p in pend]
        t = max(t, min(times))
        if t >= T["max_frames"]:
            break
        for p in [p for p in pend if p[0] <= t]:
            pend.remove(p)
            ms.append(p[1])
        alive = [m for m in ms if m.alive]
        # mostri
        for m in alive:
            if max(m.next, m.stun) <= t:
                st["m_swings"] += 1
                r = attack_roll(rng, m.att, hero.ac)
                if r:
                    st["m_hits"] += 1
                    d = int(m.st["dmg"].roll(rng, times=2 if r == 2 else 1) * m.st["dmg_mult"])
                    if t < rage_until:
                        d //= 2
                    d = max(1, d)
                    hp -= d
                    st["taken"] += d
                    if hp <= 0:
                        if left is not None:
                            left[:] = pots
                        return "lose", t, 0
                m.next = t + T["monster_attack"]
        # PG
        if nxt <= t and alive:
            if pots and hp < pc["drink_below"] * hero.hpmax and t >= pot_ready:
                kind = pots.pop(0)
                h = min(hero.hpmax - hp, potion_heal(pc[kind], hero))
                hp += h
                st["healed"] += h
                st["pots"] += 1
                pot_ready = t + pc[kind]["cooldown"]
            ready = lambda k: k in avail and cd[k] <= t
            tgt = alive[0]
            if ready("rage") and t >= rage_until:
                rage_until = t + SK["rage"]["duration"]
                cd["rage"] = t + SK["rage"]["cooldown"]
            elif ready("frenzy") and t >= frenzy_until:
                frenzy_until = t + SK["frenzy"]["duration"]
                run = 0
                st["frenzy_t"] += 1
                cd["frenzy"] = t + SK["frenzy"]["cooldown"]
            else:
                n = hero.speed + (SK["frenzy"]["extra_hits"] if t < frenzy_until else 0)
                if ready("smash"):
                    hit(tgt, n, adv=True, dice_x=2)
                    tgt.stun_for(t, SK["smash"]["stun"])
                    cd["smash"] = t + SK["smash"]["cooldown"]
                elif ready("whirlwind") and len(alive) >= 2:
                    for m in alive:
                        hit(m, n)
                    cd["whirlwind"] = t + SK["whirlwind"]["cooldown"]
                elif ready("battle_cry") and len(alive) >= 2:
                    for m in alive:
                        if rng.randint(1, 20) + m.save < hero.dc:
                            m.stun_for(t, SK["battle_cry"]["stun"])
                    cd["battle_cry"] = t + SK["battle_cry"]["cooldown"]
                elif ready("slash"):
                    st["run_bonus"] = max(st["run_bonus"], run) if t < frenzy_until else st["run_bonus"]
                    for _ in range(n):              # i colpi in piu' vanno al mostro dopo, se il primo muore
                        a = [m for m in ms if m.alive]
                        if not a:
                            break
                        hit(a[0], 1)
                    cd["slash"] = t + hero.rate
            # evocazioni del boss finale
            if final_boss is not None and wave < R["final_summons"]["waves"]:
                b = ms[final_boss]
                fs = R["final_summons"]
                while wave < fs["waves"] and (not b.alive or b.hp * 4 <= b.hpmax * (3 - wave)):
                    wave += 1
                    if not b.alive:
                        break
                    # come final_tick (src/game/game.asm): ondata solo se i vivi (boss compreso) sono <= max_alive,
                    # sempre per_wave mostri, subito, con le statistiche del PIANO ATTUALE (floor_types del piano 20)
                    others = sum(1 for m in ms if m.alive) + len(pend)
                    if others <= fs["max_alive"]:
                        for _ in range(fs["per_wave"]):
                            pend.append((t, Mon(monster(rng.choice(fs["types"]), NF), rng)))   # statistiche del piano 20
            ready_times = [cd[k] for k in avail if k in ("slash", "smash", "whirlwind", "battle_cry")]
            nxt = max(t + T["gcd"], min(ready_times))
        elif nxt <= t:
            nxt = t + 1
    if left is not None:
        left[:] = pots
    return "time", T["max_frames"], hp


def series(hero, group, floor, n=200, seed=1, boss_idx=None, final=False, potions=None, pot_cfg=None, scale=None):
    """n combattimenti di `hero` contro il gruppo (nomi dei mostri) al piano `floor`."""
    rng = random.Random(seed)
    mons = [monster(g, floor, boss=(i == boss_idx), scale=scale) for i, g in enumerate(group)]
    res = dict(win=0, lose=0, time=0, frames=0, hp_end=0)
    st = {}
    for _ in range(n):
        r, f, h = fight(hero, mons, rng, potions=potions, final_boss=(0 if final else None), stats=st, pot_cfg=pot_cfg)
        res[r] += 1
        res["frames"] += f
        res["hp_end"] += h
    res.update({k: v / n for k, v in st.items()})
    res["n"] = n
    res["winp"] = 100 * res["win"] / n
    res["sec"] = res["frames"] / n / 50
    res["hp_end"] /= n
    res["hp_endp"] = 100 * res["hp_end"] / hero.hpmax
    res["pg_hitp"] = 100 * res["pg_hits"] / max(1, res["pg_swings"])
    res["m_hitp"] = 100 * res["m_hits"] / max(1, res["m_swings"])
    return res


void_hero = RU.void_hero


def ref_hero(floor, level=None, potions=(), hp_level1=None):
    r = R["reference"][floor]
    return Hero(level or r.get("level", floor), r["weapon"], r["armor"], r["shield"], r["magic"], ring=r.get("ring", ""),
                potions=potions, hp_level1=hp_level1)


# ------------------------------------------------------------------ report
def png(fig):
    import matplotlib.pyplot as plt
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return '<img src="data:image/png;base64,%s">' % base64.b64encode(b.getvalue()).decode()


def table(head, rows):
    h = "<table><tr>" + "".join("<th>%s</th>" % x for x in head) + "</tr>"
    for r in rows:
        h += "<tr>" + "".join("<td>%s</td>" % x for x in r) + "</tr>"
    return h + "</table>"


def md_to_html(md):
    """tabelle e titoli Markdown (tools/simulators/cmp_rules.py) -> HTML"""
    out, rows = [], []
    def flush():
        if rows:
            out.append("<table>" + "".join("<tr>" + "".join(("<th>%s</th>" if i == 0 else "<td>%s</td>") % c for c in r) + "</tr>" for i, r in enumerate(rows)) + "</table>")
            rows.clear()
    for line in md.splitlines():
        if line.startswith("|---"):
            continue
        if line.startswith("|"):
            rows.append([c.strip() for c in line.strip("|").split("|")])
        else:
            flush()
            if line.startswith("## "):
                out.append("<h3>%s</h3>" % line[3:])
            elif line.strip():
                out.append("<p>%s</p>" % line)
    flush()
    return "\n".join(out)


def groups(floor):
    """gruppi tipici del piano (per la matrice): 1 base, 3 base, 1 forte, boss con nome (forte)"""
    base = RU.floor_types(floor)
    strong = RU.floor_types(floor, strong=True)
    hard = base[-1]
    return {"1 base": [hard], "3 base": [base[-1], base[0], base[min(1, len(base) - 1)]],
            "1 forte": [strong[-1]], "boss del piano": [strong[-1]]}


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    ap = argparse.ArgumentParser()
    ap.add_argument("--fights", type=int, default=150)
    ap.add_argument("--out", default=os.path.join(RU.ROOT, "out", "work", "simulators", "simulazione_regole.html"))
    ap.add_argument("--fight", nargs="+", help="piano livello mostro [mostro...]")
    a = ap.parse_args()
    N = a.fights
    if a.fight:
        fl, lv, g = int(a.fight[0]), int(a.fight[1]), a.fight[2:]
        h = ref_hero(fl, lv, potions=["red", "red", "yellow", "violet"])
        r = series(h, g, fl, n=N)
        print("PG liv %d (%s, CA %d, ATT +%d, vita %d) vs %s piano %d: vinti %.0f%%, %.1f s, vita finale %.0f%%, "
              "colpi PG %.0f%%, colpi mostri %.0f%%" % (lv, h.weapon, h.ac, h.att, h.hpmax, g, fl, r["winp"], r["sec"],
                                                      r["hp_endp"], r["pg_hitp"], r["m_hitp"]))
        return
    t0 = time.time()
    H = ["""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Simulazione regole</title><style>
:root{--bg:#f6f5f1;--fg:#1d1d1b;--mut:#6b6a64;--line:#d9d6cc;--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#17181a;--fg:#e9e7e1;--mut:#9b998f;--line:#34352f;--card:#202124}}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif}main{max-width:1100px;margin:0 auto;padding:24px 16px 60px}
h1{font-size:24px}h2{font-size:18px;margin-top:36px;border-top:1px solid var(--line);padding-top:10px}p{max-width:85ch}.mut{color:var(--mut)}
table{border-collapse:collapse;margin:8px 0}td,th{border-bottom:1px solid var(--line);padding:4px 8px;font-size:13px;text-align:right}th:first-child,td:first-child{text-align:left}
img{max-width:100%;background:#fff;border-radius:6px}</style></head><body><main>
<h1>Simulazione delle regole nuove</h1>"""]
    H.append("<p class='mut'>Parametri: <code>data/rules.yaml</code> (bilanciamento del 05/11, docs/wiki/BILANCIAMENTO.md). %d combattimenti per caso. "
             "Bot fermo come nell'arena (fase 1). Equipaggiamento di riferimento per piano (sezione 1).</p>" % N)
    # 1. riferimento
    rows = []
    for f in range(1, NF + 1):
        h = ref_hero(f)
        r = R["reference"][f]
        rows.append([f, h.level, "%s +%d" % (r["weapon"], r["magic"]), r["armor"], r["shield"] or "-", r.get("ring") or "-", h.hpmax, h.ac,
                     "+%d" % h.att, "%d-%d" % h.dmg_range()])
    H.append("<h2>1. PG di riferimento per piano</h2>" + table(["piano", "livello", "arma", "armatura", "scudo", "anello", "vita", "CA", "ATT", "danno"], rows))
    rows = []
    for f in range(1, NF + 1):
        for k in RU.floor_types(f) + RU.floor_types(f, True):
            m = monster(k, f)
            h = ref_hero(f)
            rows.append([f, k, "%d-%d" % (m["hp"].min, m["hp"].max), m["ac"], "+%d" % m["att"], "%d-%d" % (m["dmg"].min, m["dmg"].max),
                         "%.0f%%" % (100 * hit_chance(h.att, m["ac"] - h.pen)), "%.0f%%" % (100 * hit_chance(m["att"], h.ac))])
    m = monster("lord_of_ruin", NF)
    h = ref_hero(NF)
    rows.append([NF, "lord_of_ruin", "%d-%d" % (m["hp"].min, m["hp"].max), m["ac"], "+%d" % m["att"], "%d-%d" % (m["dmg"].min, m["dmg"].max),
                 "%.0f%%" % (100 * hit_chance(h.att, m["ac"] - h.pen)), "%.0f%%" % (100 * hit_chance(m["att"], h.ac))])
    H.append("<h2>2. Mostri per piano</h2><p>Colpisce: probabilita' del PG di riferimento di colpire il mostro, e del mostro di colpire il PG.</p>"
             + table(["piano", "mostro", "vita", "CA", "ATT", "danno", "PG colpisce", "mostro colpisce"], rows))
    # 3. matrice piano x livello
    H.append("<h2>3. Vittorie per piano e livello del PG</h2><p>Equipaggiamento di riferimento del piano, livello del PG variabile, "
             "con 4 pozioni (rossa, rossa, gialla, viola). Il bordo segna il livello di riferimento.</p>")
    G = ["1 base", "3 base", "1 forte", "boss del piano"]
    fig, axs = plt.subplots(1, 4, figsize=(16, 4.2))
    for gi, gname in enumerate(G):
        M = np.zeros((NF, NF))
        for f in range(1, NF + 1):
            grp = groups(f)[gname]
            for lv in range(1, NF + 1):
                h = ref_hero(f, lv, potions=["red", "red", "yellow", "violet"])
                r = series(h, grp, f, n=max(30, N // 3), seed=f * 100 + lv, boss_idx=(0 if gname == "boss del piano" else None))
                M[f - 1, lv - 1] = r["winp"]
        ax = axs[gi]
        im = ax.imshow(M, origin="lower", cmap="RdYlGn", vmin=0, vmax=100, aspect="auto", extent=(0.5, NF + 0.5, 0.5, NF + 0.5))
        for f in range(1, NF + 1):
            lv = R["reference"][f].get("level", f)
            ax.add_patch(plt.Rectangle((lv - 0.5, f - 0.5), 1, 1, fill=False, lw=1.5, ec="k"))
        ax.set_title(gname)
        ax.set_xlabel("livello PG")
        if gi == 0:
            ax.set_ylabel("piano")
    fig.colorbar(im, ax=axs, shrink=0.8, label="% vittorie")
    H.append(png(fig))
    # 4. al livello di riferimento: durata, vita, colpi
    rows = []
    for f in range(1, NF + 1):
        for gname in G:
            h = ref_hero(f, potions=["red", "red", "yellow", "violet"])
            r = series(h, groups(f)[gname], f, n=N, seed=f, boss_idx=(0 if gname == "boss del piano" else None))
            rows.append([f, gname, ", ".join(groups(f)[gname]), "%.0f%%" % r["winp"], "%.1f" % r["sec"], "%.0f%%" % r["hp_endp"],
                         "%.1f" % r["pots"], "%.0f%%" % r["pg_hitp"], "%.0f%%" % r["m_hitp"]])
    H.append("<h2>4. Al livello di riferimento</h2>" + table(["piano", "gruppo", "mostri", "vinti", "durata s", "vita finale", "pozioni", "PG colpisce", "mostri colpiscono"], rows))
    # 5. boss finale
    H.append("<h2>5. Boss finale (piano %d) al livello %d</h2><p>Riferimento dell'ultimo piano." % (NF, NF) + "<p> Vita del boss = scheda x final_boss_hp_mult "
             "(data/rules.yaml, tarato da tools/simulators/fit_rules.py per ~65%% di vittorie con 4 pozioni; oggi x%g). Le evocazioni arrivano al 75/50/25%% della vita.</p>" % R["final_boss_hp_mult"])
    rows = []
    base_mult = R["final_boss_hp_mult"]
    for mult in (0.5, 0.75, 1, 1.25, 1.5, 2):
        row = ["x%g" % (base_mult * mult)]
        for pots in ([], ["red", "red", "yellow", "violet"]):
            h = ref_hero(NF, NF, potions=pots)
            rng = random.Random(3)
            st0 = monster("lord_of_ruin", NF)
            st0 = dict(st0, hp_mult=st0["hp_mult"] * mult)
            res = {"win": 0, "lose": 0, "time": 0}
            secs = 0
            for _ in range(N):
                o, f, _h = fight(h, [st0], rng, potions=pots, final_boss=0)
                res[o] += 1
                secs += f
            row += ["%.0f%%" % (100 * res["win"] / N), "%.1f s" % (secs / N / 50)]
        rows.append(row)
    H.append(table(["vita boss", "vinti senza pozioni", "durata", "vinti con 4 pozioni", "durata"], rows))
    # 6. Abisso: livelli 20..255
    H.append("<h2>6. Abisso: PG dal livello %d al 255</h2><p>Livello = piano: un piano dell'Abisso per livello. "
             "Mostri: scheda del piano %d + tabella dell'Abisso (data/rules.yaml, void.table: CA, ATT, vita, danno per piano, tarata da "
             "tools/simulators/fit_rules.py perche' il boss con nome cali dal 70%% al 45%% di vittorie). PG: spada vichinga dell'Abisso, piastre, "
             "magia da +3 a +8, anello d'oro di forza, 4 pozioni nelle proporzioni dei pesi del piano (potions.abyss_drop: rosse fino al 40, gialle fino al 70, poi solo viola; cura heal_abyss).</p>" % (NF, NF))
    LV = sorted(set([NF, NF + 5, NF + 10, NF + 20, 50, 60, 75, 100, 125, 150, 175, 200, 225, 255]))
    VG = {"1 base": ["demon"], "3 base": ["demon", "skeleton", "zombie"], "1 forte": ["balrog"], "boss": ["balrog"]}
    rows, curves, lim = [], {g: [] for g in VG}, []
    hitc = {"PG": [], "mostri": []}
    for lv in LV:
        fl = lv
        h = void_hero(lv, potions=RU.abyss_belt(fl))     # (15/11, J4) cintura attesa all'Abisso (potions.abyss_drop)
        row = [lv, fl, h.hpmax, "+%d" % h.att, h.ac, "%d-%d" % h.dmg_range()]
        for g, grp in VG.items():
            r = series(h, grp, fl, n=max(40, N // 3), seed=lv, boss_idx=(0 if g == "boss" else None))
            curves[g].append(r["winp"])
            row.append("%.0f%% %.0fs" % (r["winp"], r["sec"]))
        d = monster("demon", fl)
        b = monster("balrog", fl, boss=True)
        hitc["PG"].append(100 * hit_chance(h.att, d["ac"] - h.pen))
        hitc["mostri"].append(100 * hit_chance(d["att"], h.ac))
        rows.append(row)
        mdmg = int(b["dmg"].max * b["dmg_mult"] * 2)            # critico
        mhp = int(b["hp"].max * b["hp_mult"])
        pdmg = (h.dice.max * 2 + h.dmg_k + h.rage_bonus()) * 2   # smash + critico
        lim.append([lv, fl, h.att, h.ac, pdmg, b["att"], b["ac"], mdmg, h.hpmax, mhp])
    H.append(table(["livello", "piano", "vita PG", "ATT", "CA", "danno", "1 base", "3 base", "1 forte", "boss"], rows))
    fig, axs = plt.subplots(1, 2, figsize=(13, 3.8))
    for g, c in curves.items():
        axs[0].plot(LV, c, marker="o", label=g)
    axs[0].set_xlabel("livello PG (= piano)")
    axs[0].set_ylabel("% vittorie")
    axs[0].set_ylim(-5, 105)
    axs[0].legend()
    axs[0].grid(alpha=.3)
    for k, c in hitc.items():
        axs[1].plot(LV, c, marker="o", label=k + " colpisce")
    axs[1].set_xlabel("livello PG")
    axs[1].set_ylabel("% colpi a segno (contro demon)")
    axs[1].set_ylim(0, 100)
    axs[1].legend()
    axs[1].grid(alpha=.3)
    H.append(png(fig))
    H.append("<h3>PG piu' forte o piu' debole del previsto</h3><p>Vittorie contro 3 mostri base (demon, skeleton, zombie) "
             "e contro il boss con nome, per livello del PG e piano. Diagonale = livello previsto (piano = livello). "
             "Sopra la diagonale il PG e' piu' alto del piano: deve vincere facilmente.</p>")
    PL = [NF, 40, 60, 80, 100, 125, 150, 175, 200, 225, 255]
    FL = [NF, 40, 60, 80, 100, 125, 150, 175, 200, 225, 255]
    fig, axs = plt.subplots(1, 2, figsize=(14, 4.6))
    for k, (gname, grp, bi) in enumerate((("3 base", ["demon", "skeleton", "zombie"], None), ("boss", ["balrog"], 0))):
        M = np.zeros((len(FL), len(PL)))
        for j, lv in enumerate(PL):
            h = void_hero(lv)
            for i, fl in enumerate(FL):
                M[i, j] = series(h, grp, fl, n=max(30, N // 6), seed=lv + fl, boss_idx=bi, potions=RU.abyss_belt(fl))["winp"]
        ax = axs[k]
        im = ax.imshow(M, origin="lower", cmap="RdYlGn", vmin=0, vmax=100, aspect="auto")
        ax.set_xticks(range(len(PL)))
        ax.set_xticklabels(PL)
        ax.set_yticks(range(len(FL)))
        ax.set_yticklabels(FL)
        ax.set_xlabel("livello PG")
        ax.set_ylabel("piano")
        ax.set_title(gname)
        for i in range(len(FL)):
            for j in range(len(PL)):
                ax.text(j, i, "%.0f" % M[i, j], ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=axs, shrink=0.8, label="% vittorie")
    H.append(png(fig))
    L8, L16 = R["void"]["limits"]["byte"], R["void"]["limits"]["word"]
    fmt = lambda v, lim_: ("<b style='color:#c0392b'>%d</b>" % v) if v > lim_ else str(v)
    H.append("<h3>Limiti a 8 e 16 bit</h3><p>In rosso i valori che superano il limite del C64 (8 bit: 255 per ATT e CA; "
             "16 bit: 65535 per vita e danno di un colpo). Danno massimo di un colpo: PG = Smash critico; mostro = critico.</p>")
    H.append(table(["livello", "piano", "ATT PG", "CA PG", "danno max PG", "ATT boss", "CA boss", "danno max boss", "vita PG", "vita max boss"],
                   [[a_, b_, fmt(c, L8), fmt(d, L8), fmt(e, L16), fmt(f, L8), fmt(g, L8), fmt(h_, L16), fmt(i, L16), fmt(j, L16)]
                    for a_, b_, c, d, e, f, g, h_, i, j in lim]))
    rows = []
    for lv in PL:
        h = void_hero(lv)
        mn, mx = h.dmg_range()
        rows.append([lv, h.weapon, h.dice.text, "+%d" % h.dmg_k, "%d-%d" % (mn, mx), "%.0f%%" % (100 * h.dice.avg / (h.dice.avg + h.dmg_k))])
    H.append("<h3>Armi dell'Abisso: peso dei dadi nel danno</h3>" + table(["livello", "arma", "dadi", "fisso", "danno", "quota dei dadi"], rows))
    # 7. confronti: oggetti, abilita', pozioni (tools/simulators/cmp_rules.py)
    import cmp_rules, io as _io, contextlib
    buf = _io.StringIO()
    with contextlib.redirect_stdout(buf):
        sys.argv = [sys.argv[0], "--fights", str(max(50, N))]
        cmp_rules.main()
    H.append("<h2>7. Confronti: oggetti, abilita', pozioni</h2><p>Da <code>tools/simulators/cmp_rules.py</code>: vittorie (vita finale, durata).</p>" + md_to_html(buf.getvalue()))
    # 7. bottino
    H.append("<h2>8. Bottino: probabilita' per piano (formula stile Diablo)</h2><p>Peso = rarita' x g(livello area - livello oggetto); "
             "livello area = 2 x piano (oltre: Abisso). Probabilita' dentro la categoria (armi).</p>")
    items = RU.loot_items()
    W = [k for k, v in items.items() if v["cat"] == "weapons"]
    areas = [2 * f for f in range(1, NF + 1, 2)] + [2 * NF + 20, 2 * NF + 40]
    M = np.array([[RU.loot_probs(al, items, "weapons").get(w, 0) * 100 for al in areas] for w in W])
    fig, ax = plt.subplots(figsize=(10, 4))
    im = ax.imshow(M, cmap="Blues", aspect="auto")
    ax.set_yticks(range(len(W)))
    ax.set_yticklabels(["%s (LO %d)" % (w, items[w]["ilvl"]) for w in W])
    ax.set_xticks(range(len(areas)))
    ax.set_xticklabels(["p%d" % (al // 2) if al <= 2 * NF else "LA %d" % al for al in areas])
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if M[i, j] >= 0.5:
                ax.text(j, i, "%.0f" % M[i, j], ha="center", va="center", fontsize=7, color="k" if M[i, j] < 40 else "w")
    fig.colorbar(im, label="%")
    H.append(png(fig))
    H.append("<p class='mut'>Generato in %.0f s da <code>tools/simulators/sim_rules.py</code>.</p></main></body></html>" % (time.time() - t0))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w").write("\n".join(H))
    print("scritto", a.out, "in %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
