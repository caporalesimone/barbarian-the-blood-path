#!/usr/bin/env python3
"""Genera out/work/db.asm da data/rules.yaml (combattimento: PG, abilita', oggetti, schede e crescita dei mostri,
esperienza) e data/balance.yaml (mondo: generazione, bottino, bauli, negozi, nomi, colori).
uso: python3 tools/build/gen_db.py [--check]
Formule e significato delle tabelle: docs/wiki/combattimento.md, docs/wiki/mostri.md, docs/wiki/oggetti.md."""
import os, re, sys, math
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import items_db  # noqa: E402
import bestiary  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DST = os.path.join(ROOT, "out", "work", "db.asm")

CATS = ["weapon", "armor", "shield", "ring", "potion", "scroll"]          # id categoria = indice + 1
CAT_CONST = ["CAT_WEAPON", "CAT_ARMOR", "CAT_SHIELD", "CAT_RING", "CAT_POTION", "CAT_SCROLL"]
SECTION = {"weapon": "weapons", "armor": "armors", "shield": "shields", "ring": "rings", "potion": "potions",
           "scroll": "scrolls"}
# puntatori sprite: base a $A000 slot 12.. (128+12), forti e finale a $8C00 (48..)
PTR_BASE, PTR_STRONG = 140, 48
STATS = ("str", "dex", "con")


class Err(Exception):
    pass


def chk(cond, msg):
    if not cond:
        raise Err(msg)


def byte(v, what):
    chk(isinstance(v, int) and 0 <= v <= 255, f"{what}: {v} non e' un byte (0..255)")
    return v


def word(v, what):
    chk(isinstance(v, int) and 0 <= v <= 65535, f"{what}: {v} non e' una word")
    return v


def pct256(p, what):
    chk(0 <= p <= 100, f"{what}: percentuale {p} fuori da 0..100")
    return min(255, round(p * 256 / 100))


def mm(d, what):
    lo, hi = d["min"], d["max"]
    chk(isinstance(lo, int) and isinstance(hi, int) and lo <= hi, f"{what}: min/max non validi")
    return lo, hi


def asm_str(s, what):
    chk(all(c in "abcdefghijklmnopqrstuvwxyz0123456789 '-." for c in s),
        f"{what}: '{s}' usa caratteri non ammessi (solo minuscole, cifre, spazio)")
    return s


def dice(s):
    """'NdS+K' -> (N, S, K)"""
    s = str(s).replace(" ", "")
    m = re.fullmatch(r"(?:(\d+)d(\d+))?([+-]\d+)?|(\d+)", s)
    chk(m is not None, "dadi non validi: " + s)
    if m.group(4):
        return 0, 0, int(m.group(4))
    return int(m.group(1) or 0), int(m.group(2) or 0), int(m.group(3) or 0)


def mod(v):
    return (v - 10) // 2


class Out:
    def __init__(self):
        self.lines = []

    def __call__(self, s=""):
        self.lines.append(s)

    def bytes(self, label, vals, per=16):
        vals = list(vals)
        for i in range(0, max(1, len(vals)), per):
            head = f"{label:<12}" if i == 0 else " " * 12
            self(f"{head}.byte " + ", ".join(str(v) for v in vals[i:i + per]))

    def words(self, label, vals, per=10):
        vals = list(vals)
        for i in range(0, len(vals), per):
            head = f"{label:<12}" if i == 0 else " " * 12
            self(f"{head}.word " + ", ".join(str(v) for v in vals[i:i + per]))

    def strings(self, prefix, names, t5=False):
        self.bytes(prefix + "_lo", [f"<{prefix}_{i}" for i in range(len(names))])
        self.bytes(prefix + "_hi", [f">{prefix}_{i}" for i in range(len(names))])
        for i, n in enumerate(names):
            if t5:                       # (21/11 sera) testo a 5 bit (macro t5 di src/common/macros.inc): il testo resta leggibile
                self(f'{prefix}_{i:<8} #t5 "{n}"')
                continue
            self(f'{prefix}_{i:<8} .text "{n}"')
            self("            .byte 0")


def pl_points(P, L):
    """punti statistica guadagnati fino al livello L (11/11: stat_points)"""
    sp = P["stat_points"]
    return sum(sp["per_level"] for l in range(2, L + 1) if sp["first"] <= l <= sp["last"] and (l - sp["first"]) % sp["every"] == 0)


def pl_scores(P, L):
    """caratteristiche del PG di riferimento al livello L: base + punti spesi come reference_alloc"""
    sc = dict(P["scores"])
    for k in P["reference_alloc"][:pl_points(P, L)]:
        sc[k] += 1
    return sc


def main():
    B = bestiary.load_balance(ROOT)           # balance.yaml + mostri (data/monsters/bestiary.tsv, 11/11)
    R = items_db.load_rules(ROOT)             # rules.yaml + data/items/items.tsv (11/11)
    o = Out()
    o("; ===================================================================")
    o(";  db.asm - GENERATO da tools/build/gen_db.py (data/rules.yaml, data/balance.yaml, data/items/items.tsv,")
    o(";  data/monsters/bestiary.tsv). Tabelle per piano: indice = piano 0..MAXLEVEL (0 = villaggio); per oggetto:")
    o(";  indice = id dell'oggetto (elenco sotto); per mostro: indice = tipo (elenco sotto).")
    o(";  NON MODIFICARE A MANO: modifica gli YAML e rigenera.")
    o("; ===================================================================")

    c = B["constants"]
    maxl = c["max_dungeon_level"]
    chk(maxl == R["dungeon"]["floors"], "balance.yaml max_dungeon_level != rules.yaml dungeon.floors")
    chk(2 <= maxl <= 24, "max_dungeon_level deve essere 2..24 (c_vis: 3 byte)")
    nst = c.get("difficulty_steps", maxl)

    def step(L):
        """piano L (1..maxl) -> gradino 1..nst delle tabelle spawn (l'ultimo piano = ultimo gradino)"""
        return nst if L == maxl else max(1, min(nst - 1, round(L * (nst - 1) / (maxl - 1))))

    # (18/11) aspetto dei piani generati (data/chapters.yaml, campo map): un byte per piano 0..MAXLEVEL, bit 0-3 palette
    # (0 = quella casuale di pal_for_level), bit 4-6 stile della mappa (nessuno = stanze, bit 4 grotte, 5 palude, 6 cittadella: gen_io.asm). Il piano del boss
    # del capitolo (l'ultimo) ha la sua mappa fissa: (19/11) solo la palette, da final.palette (capitoli 1-3; 0 = rossa).
    import chapters_db
    STYLES = {"rooms": 0, "caves": 1, "swamp": 2, "citadel": 4}     # un bit per stile (and #LK_x nel codice)
    look = [0] * (maxl + 1)
    for ch in chapters_db.load()["chapters"]:
        mp = ch.get("map") or {}
        st = STYLES.get(mp.get("style", "rooms"))
        chk(st is not None, f"chapters.yaml: capitolo {ch['id']}: map.style {mp.get('style')!r} sconosciuto")
        pals = mp.get("palettes") or []
        chk(len(pals) <= ch["n_levels"] - 1, f"chapters.yaml: capitolo {ch['id']}: piu' palette che piani generati")
        for loc in range(1, ch["n_levels"]):
            d = ch["first_depth"] + loc - 1
            if d >= maxl:
                break
            pl = pals[loc - 1] if loc <= len(pals) else 0
            chk(0 <= pl <= 15, f"chapters.yaml: capitolo {ch['id']}: palette {pl}")
            look[d] = pl | st << 4
        fp = (ch.get("final") or {}).get("palette", 0)
        d = ch["first_depth"] + ch["n_levels"] - 1                  # piano del boss del capitolo
        chk(0 <= fp <= 15, f"chapters.yaml: capitolo {ch['id']}: final.palette {fp}")
        if fp and d < maxl:
            look[d] = fp
    o("; ---- aspetto dei piani generati (data/chapters.yaml map): bit 0-3 palette (0 = casuale), bit 4-6 stile (bit 4 grotte, 5 palude, 6 cittadella)")
    o.bytes("lv_look", look)
    o("LK_CAVE     = $10")
    o("LK_SWAMP    = $20")
    o("LK_CIT      = $40")
    o("LK_STYLE    = $70")
    o()

    P = R["player"]
    plmax = P["max_level_before_boss"]
    chk(plmax == maxl, "player.max_level_before_boss deve essere = dungeon.floors (un livello per piano)")
    o(f"MAXLEVEL    = {maxl}            ; numero di piani (l'ultimo: sala del trono)")
    o(f"PL_MAXLVL   = {plmax}            ; tetto del PG prima dell'Abisso")
    o("dungeon_level = cur_level")
    o()

    # ------------------------------------------------------------ PG
    T = R["timing"]
    o("; ---- tempi (fotogrammi)")
    o(f"GCD_T       = {byte(T['gcd'], 'gcd')}")
    o(f"MON_ATK_T   = {byte(T['monster_attack'], 'monster_attack')}")
    o(f"STUN_HIT    = {byte(T['stun_on_hit'], 'stun_on_hit')}")
    o()
    o("; ---- PG: caratteristiche per livello (senza anello), competenza, vita massima (senza anello)")
    chk(P["hp_level1"] == "10+CON", "hp_level1: supportato solo '10+CON' (vedi recalc_stats)")
    L1 = int(P["hp_level1"].split("+")[0])
    o(f"PL_HP1      = {L1}")
    o(f"PL_HPL      = {byte(P['hp_per_level'], 'hp_per_level')}")
    o(f"PL_START_GOLD = {word(B['player']['start_gold'], 'start_gold')}")
    pu = B["player"]["purse"]                         # (22/11, committente) borsello a gradini (q_flag bit 4-7)
    chk(all(v % 10 == 0 for v in pu) and pu == sorted(pu) and 1 <= len(pu) <= 16, "player.purse: multipli di 10, crescenti")
    o(f"GOLD_MAX = {word(max(pu), 'purse')}       ; oro massimo addosso (l'ultimo gradino del borsello)")
    o(f"PURSE_N  = {len(pu)}          ; gradini del borsello")
    o.bytes("pc_lo", [v & 255 for v in pu])
    o.bytes("pc_hi", [v >> 8 for v in pu])
    # (11/11) punti statistica: caratteristiche di base + punti spesi (c_sadd), vita = 10 + COS + (L-1) x (6 + mod COS)
    chk(len(P["reference_alloc"]) >= pl_points(P, plmax) and all(k in STATS for k in P["reference_alloc"]),
        "player.reference_alloc: una caratteristica (str/dex/con) per ogni punto fino al livello massimo")
    for k in STATS:
        chk(P["scores"][k] >= 10, f"player.scores.{k} >= 10 (modv)")
        o(f"PL_{k.upper()}0     = {byte(P['scores'][k], k)}            ; valore di base (livello 1)")
    prof, pts = [], []
    for L in range(0, plmax + 1):
        Lx = max(1, L)
        prof.append(2 + (Lx - 1) // P["prof_every"])
        pts.append(byte(pl_points(P, Lx), "stat_points"))
    o.bytes("pl_prof", prof)
    o("; punti statistica guadagnati fino al livello (indice = livello)")
    o.bytes("pl_pts", pts)
    o(".if TESTCL > 1                 ; eroe di prova (TESTCL): punti spesi come il PG di riferimento")
    for k in STATS:
        o.bytes("pl_r" + k, [byte(pl_scores(P, max(1, L))[k] - P["scores"][k], k) for L in range(0, plmax + 1)])
    o(".endif")
    RS = P["respec"]
    chk(RS["final_boss"] >= 1, "respec.final_boss >= 1 (kill_monster: ciclo su X)")
    o(f"RESP_MAX    = {byte(RS['max'], 'respec.max')}           ; gettoni respec al massimo")
    o(f"RESP_FINAL  = {byte(RS['final_boss'], 'respec.final_boss')}             ; gettoni per il boss finale")
    o(f"RESP_DROP   = {byte(round(RS['abyss_chest_percent'] * 256 / 100), 'abyss_chest_percent')}             ; bauli dell'Abisso: gettone se rand < RESP_DROP (x/256)")
    AS = P["attack_speed"]                # (18/11) cadenza dell'attacco: arma + max(0, slow - per_dex x mod DES)
    o(f"ATK_SLOW    = {byte(AS['slow'], 'attack_speed.slow')}            ; rallentamento dell'attacco base (fotogrammi)")
    o(f"ATK_DEX     = {byte(AS['per_dex'], 'attack_speed.per_dex')}             ; ... meno questo per punto di mod DES")
    o(f"CRIT_LVL    = {byte(R['skills']['brutal_critical_level'], 'brutal_critical_level')}")
    dc = R["dex_cap"]
    o()

    # ------------------------------------------------------------ abilita'
    SK = R["skills"]
    order = ["slash", "whirlwind", "battle_cry", "smash", "rage", "frenzy"]
    o("; ---- abilita': 0 slash, 1 whirlwind, 2 battle cry, 3 smash (con Fire, tasti F1 F3 F5 F7), 4 rage (R), 5 frenzy (F)")
    o("SK_N        = 6")
    o.bytes("sk_req", [byte(SK[k]["level"], k) for k in order])
    cds = [0 if k == "slash" else word(SK[k]["cooldown"], k) for k in order]
    o.bytes("sk_cd_lo", [v & 255 for v in cds])
    o.bytes("sk_cd_hi", [v >> 8 for v in cds])
    o(f"BC_STUN     = {byte(SK['battle_cry']['stun'], 'battle_cry.stun')}")
    o(f"SM_STUN     = {byte(SK['smash']['stun'], 'smash.stun')}")
    o(f"RAGE_DUR    = {word(SK['rage']['duration'], 'rage.duration')}")
    chk(SK["rage"].get("damage", 0) == 0, "rage.damage: supportato solo 0 (Rage dimezza i danni subiti)")
    o(f"FZ_DUR      = {word(SK['frenzy']['duration'], 'frenzy.duration')}")
    chk(SK["frenzy"]["extra_hits"] == 1, "frenzy.extra_hits: supportato solo 1")
    o(f"FZ_RUN1     = {byte(SK['frenzy']['run_first'], 'run_first')}    ; % di corsa in piu' al primo colpo a segno")
    o(f"FZ_RUN2     = {byte(SK['frenzy']['run_step'], 'run_step')}    ; % in piu' a ogni colpo a segno dopo")
    o(f"FZ_RUNMAX   = {byte(SK['frenzy']['run_max'], 'run_max')}")
    o()

    # ------------------------------------------------------------ esperienza
    mons_r = list(R["monsters"].items())
    mons_b = list(B["monsters"].items())
    chk([k for k, _ in mons_r] == [k for k, _ in mons_b], "rules.yaml e balance.yaml: stessi mostri nello stesso ordine")
    base = [(k, m) for k, m in mons_b if m["tier"] == "base"]
    strong = [(k, m) for k, m in mons_b if m["tier"] == "strong"]
    final = [(k, m) for k, m in mons_b if m["tier"] == "final"]
    chk(mons_b == base + strong + final, "ordine mostri: prima i base, poi i forti, poi il finale")
    chk(len(final) == 1, "serve esattamente un mostro 'final'")
    chk([m["strong_of"] for _, m in strong] == [k for k, _ in base], "varianti forti nell'ordine dei base")
    nb = len(base)
    MR = R["monsters"]
    import mon_stats as MS      # (24/11, M9) statistiche dei mostri: formule del bestiario -> coefficienti del C64
    MCF = MS.coefs_by_id(R, B)

    def mxp(k, L):
        return MS.values(MCF[k], L, maxl)["xp"]

    sp = B["spawn"]

    def floor_xp(L):
        """esperienza attesa esplorando tutto il piano L (mostri comuni + boss con nome)"""
        if L == maxl:
            return mxp(final[0][0], L)
        n = (sp["max_monsters_per_level"][step(L) - 1] + sp["min_monsters_per_level"][step(L) - 1]) / 2
        bt = [k for k, _ in base if MR[k]["floor"] <= L] or [base[0][0]]
        avg = sum(mxp(k, L) for k in bt) / len(bt)
        st = [k for k, _ in strong if MR[k]["floor"] <= L] or [strong[0][0]]
        bxp = sum(mxp(k, L) for k in st) / len(st) * B["boss"]["xp_multiplier"]
        return n * avg + bxp

    lpf = 1.3                                                    # livelli per piano esplorato tutto
    E = [0.0]
    for L in range(1, maxl + 1):
        E.append(E[-1] + floor_xp(L))
    need = []
    for lv in range(2, plmax + 1):
        f = (lv - 1) / lpf                                       # piani esplorati per arrivare al livello lv
        i = int(f)
        xv = E[i] + (E[min(i + 1, maxl)] - E[i]) * (f - i)
        need.append(int(round(xv)))
    for i in range(1, len(need)):
        need[i] = max(need[i], need[i - 1] + 1)
    chk(need[-1] < 1 << 24, "xp oltre 24 bit")
    o("; ---- esperienza (24 bit) per passare al livello 2..PL_MAXLVL: ~1,3 livelli per piano esplorato tutto")
    o.bytes("xp_n0", [v & 255 for v in need])
    o.bytes("xp_n1", [(v >> 8) & 255 for v in need])
    o.bytes("xp_n2", [v >> 16 for v in need])
    o()

    # ------------------------------------------------------------ oggetti
    items = [("none", "none", {"name": "-", "price": 0, "ilvl": 0})]
    for cat in CATS:
        for k, it in R[SECTION[cat]].items():
            if not isinstance(it, dict) or "name" not in it:
                continue
            items.append((k, cat, it))
    chk(len(items) <= 64, "troppi oggetti (max 63)")
    # lunghezza del nome mostrato (08/11): le colonne dei menu (casa, inventario, negozi, riquadro dell'oggetto) hanno
    # 17 caratteri (ui_item riempie fino a 17): al massimo NAME_SHOW = 16, cosi' resta sempre uno spazio prima della
    # cornice o della colonna accanto. Arma/armatura/scudo: "+N " davanti; anello: " str"/" dex"/" con" dietro;
    # pergamena: "N " davanti (3 caratteri: la pila potrebbe arrivare a 10); pozione: il nome e basta. Documentato in docs/wiki/oggetti.md (Nomi).
    NAME_SHOW = 16
    for k, cat, it in items[1:]:
        extra = {"weapon": 3, "armor": 3, "shield": 3, "ring": 4, "scroll": 3}.get(cat, 0)
        chk(len(it["name"]) + extra <= NAME_SHOW,
            f"nome '{it['name']}' ({cat}): {len(it['name'])} caratteri + {extra} mostrati = {len(it['name']) + extra} > {NAME_SHOW} (docs/wiki/oggetti.md)")
    ids = {k: i for i, (k, _, _) in enumerate(items)}
    o("; ---- oggetti (id = ordine in data/items/items.tsv: armi, armature, scudi, anelli, pozioni, pergamene; 0 = vuoto)")
    o(";      id: " + ", ".join("%d %s" % (i, k) for i, (k, _, _) in enumerate(items)))
    for i, (k, _, _) in enumerate(items):
        if i:
            o(f"I_{k.upper():<14} = {i}")
    for i, cc in enumerate(CAT_CONST):
        o(f"{cc:<11}= {i + 1}")
    o(f"N_ITEMS     = {len(items)}")
    o(f"I_POTR      = {ids['red']}")
    o(f"I_POTY      = {ids['yellow']}")
    o(f"I_POTV      = {ids['violet']}")
    o(f"I_SCROLL    = {ids['portal_scroll']}")
    o(f"I_START     = {ids[R['start_weapon']]}")
    du = R["durability"]
    o("; ---- durabilita' (armi, armature, scudi indossati): generazione, usura 1/N, riparazione")
    o(f"DUR_MIN     = {byte(du['min'], 'durability.min')}")
    o(f"DUR_MAX     = {byte(du['max'], 'durability.max')}")
    o(f"DUR_WP      = {byte(du['ilvl_weight_percent'], 'ilvl_weight_percent')}      ; % dei casi in cui il livello oggetto pesa")
    o(f"DUR_PI      = {byte(du['floor_per_ilvl'], 'floor_per_ilvl')}       ; minimo = DUR_MIN + DUR_PI x ilvl (caso pesato)")
    o(f"WEAR_W      = {byte(du['wear']['weapon_per_hit'], 'wear')}")
    o(f"WEAR_A      = {byte(du['wear']['armor_per_hit'], 'wear')}")
    o(f"WEAR_S      = {byte(du['wear']['shield_per_hit'], 'wear')}")
    pc = byte(du['warn_percent'], 'durability.warn_percent')
    assert 0 < pc and 100 % pc == 0, "durability.warn_percent deve dividere 100"
    o(f"WARN_PC     = {pc}      ; avviso nell'HUD: durabilita' <= WARN_PC % del massimo")
    o(f"WARN_MUL    = {100 // pc}       ; (hud.asm: durabilita' x WARN_MUL <= massimo)")
    o(f"REPAIR_PC   = {byte(du['repair_cost_percent'], 'repair_cost_percent')}")
    chk(du["min"] + du["floor_per_ilvl"] * max(it.get("ilvl", 0) for _, ct, it in items if it.get("loot") is not False) < du["max"], "durability: minimo pesato oltre il massimo")
    cat, price, ilvl, dn, ds, val, rate, pen, fl, req = ([] for _ in range(10))
    pab = {}                                  # (15/11, TODO J4) cura nell'Abisso (livello PG > MAXLEVEL): colonna heal_abyss delle pozioni
    for k, ct, it in items:
        cat.append(0 if ct == "none" else CATS.index(ct) + 1)
        price.append(word(it.get("price", 0), f"{k}.price"))
        ilvl.append(255 if it.get("loot") is False else byte(it.get("ilvl", 0), f"{k}.ilvl"))   # 255 = mai nel bottino
        a = b_ = v = r = p = f = 0
        if ct == "weapon":
            n, s, kk = dice(it["dice"])
            chk(kk == 0 and n >= 1, f"{k}: dadi senza costante (NdS)")
            a, b_, r, p = n, s, it["rate"], it["pen"]
            f = (1 if it.get("two_handed") else 0) | (4 if it.get("nomod") else 0)
        elif ct == "armor":
            v = it["ac"]
            f = min(255, dc[it["type"]])
        elif ct == "shield":
            v = it["ac"]
        elif ct == "ring":
            v = it["bonus"]
        elif ct == "potion":
            m = re.fullmatch(r"(?:(\d+)\*L\+)?(\d+)", str(it["heal"]).replace(" ", ""))
            chk(m is not None, f"{k}.heal: formati ammessi 'B' o 'A*L+B'")
            a, v = int(m.group(1) or 0), int(m.group(2))
            ma = re.fullmatch(r"(?:(\d+)\*L\+)?(\d+)", str(it.get("heal_abyss", "")).replace(" ", ""))
            chk(ma is not None, f"{k}.heal_abyss: formati ammessi 'B' o 'A*L+B'")
            pab[k] = (byte(int(ma.group(1) or 0), f"{k}.heal_abyss A"), byte(int(ma.group(2)), f"{k}.heal_abyss B"))
            chk(it["cooldown"] % 2 == 0, f"{k}.cooldown: deve essere pari (si salva /2)")
            r = it["cooldown"] // 2
            f = it["color"]
        for nm, x in (("dn", a), ("ds", b_), ("val", v), ("rate", r), ("pen", p), ("fl", f)):
            byte(x, f"{k}.{nm}")
        dn.append(a); ds.append(b_); val.append(v); rate.append(r); pen.append(p); fl.append(f)
        # (21/11, O6) un solo requisito per oggetto: FOR (valore) o DES (valore | $80, min_dex); src/game/ui.asm req_chk
        ms, md = it.get("min_str", 0) or 0, it.get("min_dex", 0) or 0
        chk(not (ms and md), f"{k}: min_str e min_dex insieme (il gioco ne tiene uno solo)")
        chk(ms < 128 and md < 128, f"{k}: requisito oltre 127")
        req.append(ms or (md | 0x80 if md else 0))
    o.bytes("itcat", cat)
    o.words("itprice", price)
    o.bytes("itilvl", ilvl)
    # (21/11 sera) tabelle spostate nella RAM del font della UI dopo i glifi ($B800 + UI_N x 8: out/work/fonttab.asm, incluso in
    # src/game.asm dopo gd_font e copiato con il font da copy_gfx)
    global FT
    FT = Out()
    FT.bytes("itdn", dn)                 # arma: numero di dadi; pozione: cura per livello (A in A*L+B)
    FT.bytes("itds", ds)                 # arma: facce del dado
    o.bytes("itval", val)                # armatura/scudo: CA; anello: +N al modificatore; pozione: cura fissa (B)
    FT.bytes("itrate", rate)             # arma: cadenza (fotogrammi); pozione: ricarica / 2
    FT.bytes("itpen", pen)
    o.bytes("itfl", fl)                  # arma: bit0 due mani, bit2 senza modificatori; armatura: limite DES; pozione: colore
    o.bytes("itreq", req)                # (21/11, O6) FOR (valore) o DES (valore | $80) richiesta per indossarlo (anello compreso); 0 = nessuna
    # (15/11, TODO J4) cura delle pozioni nell'Abisso (livello del PG > MAXLEVEL), indice = id - I_POTR (rossa, gialla, viola):
    # cura = pab_val + pab_dn x livello, come itval / itdn nel dungeon (pot_heal, combat.asm)
    chk(ids["yellow"] == ids["red"] + 1 and ids["violet"] == ids["red"] + 2, "pozioni: rossa, gialla, viola devono essere consecutive nella tabella")
    o.bytes("pab_dn", [pab[k][0] for k in ("red", "yellow", "violet")])
    o.bytes("pab_val", [pab[k][1] for k in ("red", "yellow", "violet")])
    o("        .cerror I_POTY != I_POTR + 1 || I_POTV != I_POTR + 2, \"pab_dn / pab_val: pozioni consecutive (rossa, gialla, viola)\"")
    o()

    # ------------------------------------------------------------ bottino
    lo = B["loot"]
    maxll = byte(lo["max_loot_level"], "max_loot_level")
    w = lo["category_weights"]
    chk(sum(w[k] for k in CATS) == 100, "category_weights deve sommare a 100")
    cum, s = [], 0
    for k in CATS:
        s += w[k]
        cum.append(s)
    bon = lo["bonus"]
    o("; ---- bottino: categorie (soglie su 100), magia +N per livello bottino")
    o(f"MAXLL       = {maxll}")
    o.bytes("loot_cum", cum)
    # lt_scan prende il migliore oggetto con ilvl <= L: ogni categoria con peso deve avere un oggetto di ilvl 0
    for ct in ("weapon", "armor", "shield", "ring"):
        if w.get(ct) and not any(c == ct and it["ilvl"] == 0 for _, c, it in items):
            print(f"AVVISO: nessun oggetto di ilvl 0 nella categoria {ct}: a livello oggetto 0 la categoria resta vuota")
    # pozioni: colore secondo le zone (rules.yaml potions.zones / ramp)
    PZ = R["potions"]
    z = PZ["zones"]
    zb = [1, round(z[0] * maxl) + 1, round(z[1] * maxl) + 1]
    t1, t2 = [], []
    for f in range(0, maxl + 1):
        wt = []
        for kz in range(3):
            lo_, hi_ = zb[kz], (zb[kz + 1] - 1 if kz < 2 else 10 ** 6)
            d = max(0, lo_ - f, f - hi_)
            wt.append(1.0 if d == 0 else (PZ["ramp"][d - 1] if d <= len(PZ["ramp"]) else 0.0))
        tot = sum(wt) or 1
        t1.append(min(255, round(256 * wt[0] / tot)))
        t2.append(min(255, round(256 * (wt[0] + wt[1]) / tot)))
    o("; pozioni per piano: rnd < pot_t1 -> rossa, < pot_t2 -> gialla, altrimenti viola (oltre il dungeon: viola)")
    o.bytes("pot_t1", t1)
    o.bytes("pot_t2", t2)
    o()

    # ------------------------------------------------------------ mostri
    G = R["growth"]
    o("; ---- mostri (24/11): bestiario con formule (tools/build/mon_stats.py), valore = A + ((B x P + 8) >> 4), P = piano - fmin")
    o(f"N_BASE      = {nb}")
    o(";      tipo: " + ", ".join("%d %s" % (i + 1, k) for i, (k, _) in enumerate(mons_r)) + " (0 = nessuno; tabelle mon_* da 0)")
    o(f"N_MTYPES    = {len(mons_r)}")
    o(f"T_FINAL     = {len(mons_r)}")
    for i, (k, _) in enumerate(mons_r):
        o(f"M_{k.upper():<16} = {i + 1}")
    t = {f: [0] for f in ("imm", "col", "ptr")}
    for i, ((k, m), (_, b)) in enumerate(zip(mons_r, mons_b)):
        t["imm"].append(1 if m.get("stun_immune") else 0)
        t["col"].append(byte(b["color"], k))
        t["ptr"].append(PTR_BASE + 2 * i if i < nb else PTR_STRONG + 2 * (i - nb))
    tc = MS.ch1_tables(R, B)
    chk([r["id"] for r in MS.type_rows(1)] == [k for k, _ in mons_r], "mon_stats.type_rows(1) diverso dai tipi del gioco")
    pre = lambda f: ("mon_" if f in ("spd", "col", "llb", "ptr") else "mt_") + f
    for f, v in t.items():
        if f == "col":            # (15/11) colori e nomi dei tipi: dal file del tema (gen_gfx.py, blocco info a NM_AT)
            continue
        o.bytes(pre(f), v)
    o("; (24/11) tabelle dei tipi (tools/build/mon_stats.py): il file del tema porta i tipi 1..8 del suo capitolo, gfx_install le copia qui")
    o("mt_ch")
    for f in MS.CH_FIELDS:
        o.bytes(pre(f), tc[f])
    o(f"MT_CH_LEN   = {len(MS.CH_FIELDS) * len(tc['hp_lo'])}")
    sc = R.get("monster_scale", {"damage": 1})
    chk(set(sc) == {"damage"}, "monster_scale: solo damage (24/11: la vita e' nelle formule del bestiario)")
    chk(len(G["curve_dmg"]) == maxl + 1, "growth.curve_dmg: servono floors+1 valori")
    o.bytes("cv_dmg", [byte(round(v * sc["damage"] * 32), "curve_dmg") for v in G["curve_dmg"]])
    bo = R["boss"]
    chk(round(bo["hp_mult"] * 2) == bo["hp_mult"] * 2, "boss.hp_mult: multiplo di 0,5")
    o(f"BOSS_HPH    = {byte(int(bo['hp_mult'] * 2), 'boss.hp_mult')}            ; vita del boss con nome x BOSS_HPH / 2")
    o(f"BOSS_AC     = {byte(bo['ac_add'], 'boss.ac_add')}")
    mnames = list(B["monsters"])                    # (22/11, D8/D16) boss dei capitoli: tipo e vita fissi (codice del piano)
    for k, cb in (R.get("chapter_bosses") or {}).items():
        c = cb["floor"] // 5
        chk(cb["type"] in mnames, "chapter_bosses.%s.type" % k)
        chk(0 < cb["hp"] < 65536, "chapter_bosses.%s.hp" % k)
        o(f"CB{c}_TYPE   = {mnames.index(cb['type']) + 1}            ; (22/11) boss del capitolo {c} ({k}): tipo {cb['type']}")
        o(f"CB{c}_HP     = {cb['hp']}          ; vita fissa")
    o(f"BOSS_ATT    = {byte(bo['att_add'], 'boss.att_add')}")
    o(f"BOSS_LVL    = 3             ; livello del boss = piano + 3 (variante forte: + 2) per l'esperienza")
    bw = B["boss"]
    o(f"BOSS_XP_MUL = {byte(bw['xp_multiplier'], 'xp_multiplier')}")
    o(f"BOSS_LL_ADD = {byte(bw['loot_level_add'], 'loot_level_add')}      ; chestLevel del boss: + N")
    cl = B["chest_level"]
    o("; ---- chestLevel (1..255): per_floor x piano + bonus; livello oggetto T = CL / CL_PF, L = T x u^2")
    o(f"CL_PF       = {byte(cl['per_floor'], 'chest_level.per_floor')}")
    o(f"CL_LLB      = {byte(cl['llb_mult'], 'llb_mult')}")
    o(f"CL_STRONG   = {byte(cl['strong_bonus'], 'strong_bonus')}")
    o(f"CL_HP       = {byte(cl['hp_bonus'], 'hp_bonus')}")
    chk(cl["per_floor"] in (2, 4, 8, 16), "chest_level.per_floor: potenza di 2 (shift nel codice)")
    chk(cl["per_floor"] * maxl + 3 * cl["llb_mult"] + cl["strong_bonus"] + cl["hp_bonus"] + bw["loot_level_add"] <= 255,
        "chestLevel oltre 255 al piano massimo")
    chk(1 <= bw["loot_items"] <= 4, "boss.loot_items 1..4")
    o(f"BOSS_ITEMS  = {bw['loot_items']}")
    o(f"BOSS_KEY    = {1 if bw['key'] else 0}")
    chk(len(bw["first_names"]) == 8 and len(bw["epithets"]) == 8, "servono 8 nomi e 8 epiteti")
    fs = R["final_summons"]
    o(f"SUM_WAVE    = {byte(fs['per_wave'], 'per_wave')}")
    o(f"SUM_MAXALIVE = {byte(fs['max_alive'], 'max_alive')}")
    o(f"SUM_FLOOR   = {byte(fs['floor'], 'final_summons.floor')}")
    # (24/11) i tipi base presenti a un piano li conta base_n (combat.asm) da mt_fmin: in ordine di primo piano, il primo
    # presente dal primo piano del capitolo
    for c in range(1, maxl // MS.CPF + 1):
        fm = [r["floor"] for r in MS.type_rows(c)[:nb]]
        chk(fm == sorted(fm), "capitolo %d: tipi base non in ordine di primo piano %s (base_n)" % (c, fm))
        chk(fm[0] <= MS.CPF * c - 4, "capitolo %d: nessun tipo base al primo piano del capitolo (%s)" % (c, fm))
    sr = sp["strong_room_chance"]
    smf = byte(sp.get("strong_min_floor", 1), "strong_min_floor")
    o.bytes("strong_tab", [0] + [0 if L < smf else pct256(min(100, sr["percent"] + sr["per_dungeon_level"] * (step(L) - 1)), "strong")
                                 for L in range(1, maxl + 1)])
    o(f"STRONG_EARLY = {byte(sp.get('strong_early', 0), 'strong_early')}   ; variante forte solo se il suo piano minimo <= piano + N")
    a, b_ = mm(sp["monsters_per_room"], "monsters_per_room")
    o(f"SPAWN_MIN   = {a}")
    o(f"SPAWN_MAX   = {b_}")
    mx = sp["max_monsters_per_level"]
    mn = sp["min_monsters_per_level"]
    chk(len(mx) == nst and len(mn) == nst, f"spawn.*_monsters_per_level: servono {nst} valori")
    chk(mx[-1] == 0, "spawn.max_monsters_per_level: l'ultimo gradino deve avere 0 (solo il boss finale)")
    chk(all(0 <= a <= b <= 28 for a, b in zip(mn, mx)), "spawn: min <= max <= 28")
    o.bytes("maxmon_tab", [0] + [mx[step(L) - 1] for L in range(1, maxl + 1)])
    o.bytes("minmon_tab", [0] + [mn[step(L) - 1] for L in range(1, maxl + 1)])
    o()

    # ------------------------------------------------------------ drop
    d = B["drops"]
    o("; ---- bottino dei mostri (soglie su 256)")
    o(f"DROP_KEY    = {pct256(d['key']['chance'], 'key')}")
    oc = d["outcome"]
    chk(sum(oc.values()) == 100 and oc["gold_only"] > oc["chest"], "drops.outcome: somma 100, gold_only > chest")
    o(f"DROP_T_GOLD  = {pct256(oc['gold_only'], 'gold_only')}")
    o(f"DROP_T_CHEST = {pct256(oc['gold_only'] + oc['chest'], 'gold_only+chest')}")
    a, b_ = mm(d["gold"], "drops.gold")
    o(f"DROP_GOLD_MIN = {a}")
    o(f"DROP_GOLD_MAX = {b_}")
    o(f"DROP_GOLD_LVL = {byte(d['gold']['per_dungeon_level'], 'drops.gold.per_dungeon_level')}   ; oro in piu' per piano")
    a, b_ = mm(d["chest"]["items"], "drops.chest.items")
    chk(1 <= a and b_ <= 4, "drops.chest.items 1..4")
    o(f"DROP_IMIN   = {a}")
    o(f"DROP_IMAX   = {b_}")
    o()

    # ------------------------------------------------------------ bauli
    ch = B["chests"]
    o("; ---- bauli (indice: 0 normale, 1 chiave, 2 oro); ch_llmin/max: si sommano al piano")
    llmin, llmax, bias, imin, imax, keyr = [], [], [], [], [], []
    for n in ("normal", "key", "gold"):
        kd = ch[n]
        a, b_ = mm(kd["loot_level"], f"chests.{n}.loot_level")
        llmin.append(byte(a, n)); llmax.append(byte(b_, n))
        bias.append(1 if kd.get("bias_low") else 0)
        a, b_ = mm(kd["items"], f"chests.{n}.items")
        chk(1 <= a and b_ <= 4, f"chests.{n}.items 1..4")
        imin.append(a); imax.append(b_)
        keyr.append(1 if kd["key_required"] else 0)
    o.bytes("ch_llmin", llmin)
    o.bytes("ch_llmax", llmax)
    o.bytes("ch_bias", bias)
    o.bytes("ch_imin", imin)
    o.bytes("ch_imax", imax)
    o.bytes("ch_keyr", keyr)
    o(f"CH_N_ROOM   = {pct256(ch['normal']['room_chance'], 'normal')}")
    o(f"CH_N_MINLVL = {ch['normal']['min_dungeon_level']}")
    o(f"CH_K_ROOM   = {pct256(ch['key']['room_chance'], 'key')}")
    o(f"CH_K_MINLVL = {ch['key']['min_dungeon_level']}")
    o(f"CH_K_MAX    = {ch['key']['max_per_level']}")
    o(f"CH_G_CHANCE = {pct256(ch['gold']['chance'], 'gold')}")
    o(f"CH_G_MINLVL = {ch['gold']['min_dungeon_level']}")
    ga = ch["gold_amount"]
    chk(ga["max_per_loot_level"] * maxll <= 255, "chests.gold_amount: max_per_loot_level x max_loot_level <= 255")
    o(f"CH_GOLD_LLMIN = {ga['min_per_loot_level']}")
    o(f"CH_GOLD_LLMAX = {ga['max_per_loot_level']}")
    o(f"FIN_GOLD    = {word(ch['final_gold'], 'chests.final_gold')}       ; oro di ogni baule epico della sala del trono")
    o()

    # ------------------------------------------------------------ negozi
    sh = B["shops"]
    SHOP_POOL_MAX = 28                    # (21/11) armi nuove: il pool del fabbro passa 16; (21/11 sera) armature nuove: 28
    chk(list(sh) == ["blacksmith", "alchemist"], "shops: blacksmith, alchemist (09/11: niente armaiolo)")
    first, count, flat, stock, minl = [], [], [], [], []
    ahead = B["shop_rules"]["level_ahead"]
    itd = {k: (ct, it) for k, ct, it in items}
    for n, dd in sh.items():
        lst = dd["items"]
        chk(1 <= len(lst) <= SHOP_POOL_MAX, f"shop {n}: pool 1..{SHOP_POOL_MAX} (shp_stock in src/game/ui.asm)")
        first.append(len(flat)); count.append(len(lst))
        for k in lst:
            chk(k in ids, f"shop {n}: oggetto '{k}' sconosciuto")
            flat.append(ids[k])
            ct, it = itd[k]
            # livello minimo del PG per vederlo in vendita: pozioni e pergamene shop_level (rules.yaml),
            # equipaggiamento livello oggetto - level_ahead
            minl.append(byte(it["shop_level"], f"{k}.shop_level") if "shop_level" in it else max(0, it.get("ilvl", 0) - ahead))
    o("; ---- negozi (0 fabbro, 1 alchimista)")
    o(f"SHOP_POOL_MAX = {SHOP_POOL_MAX}     ; posti di shp_stock (src/game/ui.asm): pool filtrato di un negozio")
    o.bytes("shop_first", first)
    o.bytes("shop_cnt", count)
    wr = B["shop_rules"]["wares"]       # (21/11 sera, decisione del committente ex B1) merce casuale da min a max, con ripetizioni
    chk(1 <= wr["min"] <= wr["max"] <= 8, "shop_rules.wares: 1 <= min <= max <= 8 (riquadro merce da 8)")
    o(f"SHOP_KMIN   = {wr['min']}        ; oggetti in vendita: SHOP_KMIN + rndrange(SHOP_KN)")
    o(f"SHOP_KN     = {wr['max'] - wr['min'] + 1}")
    o.bytes("shop_items", flat)
    o.bytes("shop_minl", minl)            # livello minimo del PG (parallelo a shop_items)
    sdiv = B["shop_rules"]["sell_divisor"]
    chk(sdiv in (1, 2, 4, 8), "shop_rules.sell_divisor: 1, 2, 4 o 8 (potenza di 2: il gioco divide con gli shift)")
    o(f"SELL_SHIFT  = {sdiv.bit_length() - 1}        ; vendita = prezzo >> SELL_SHIFT (balance.yaml shop_rules.sell_divisor, 20/11)")
    o()

    # ------------------------------------------------------------ affissi (21/11 sera, fase 2b; data/items/next/)
    # Indice nella tabella: 0 = niente, 1..AF_NP prefissi (riga di prefixes.tsv), AF_SX0 + s = suffisso s (riga di suffixes.tsv).
    # Oggetto: byte "bonus" = id del prefisso (pergamene: quantita'), byte "suffisso" = id del suffisso. Valore dalla riga
    # (value1 = value2 fino al livello 20: decisione del committente del 21/11, oggetto a 5 byte).
    import csv as _csv
    nx = os.path.join(ROOT, "data", "items", "next")
    def rows(f):
        return list(_csv.DictReader(open(os.path.join(nx, f)), delimiter="\t"))
    PX, SX = rows("prefixes.tsv"), rows("suffixes.tsv")
    PW = ["ATT_DMG", "ATT", "DMG", "AC", "STR", "DEX", "CON", "ALL", "LIFE", "GETHIT", "PEN", "SPEED", "DUR",
          "INDESTRUCTIBLE", "LEECH", "THORNS"]           # codici 1.. (combat.asm af_one: fino a PW_ALL oggi, il resto con la fase 4)
    chk(len(PX) < 64 and len(SX) < 64, "affissi: al massimo 63 prefissi e 63 suffissi")
    o("; ---- affissi (data/items/next/prefixes.tsv, suffixes.tsv; indice 0 = niente, 1..AF_NP prefissi, AF_SX0+s suffissi)")
    for i, k in enumerate(PW):
        o(f"PW_{k:<15}= {i + 1}")
    o(f"AF_NP       = {len(PX)}")
    o(f"AF_NS       = {len(SX)}")
    o(f"AF_SX0      = {len(PX)}")
    pw, val, names = [0], [0], []
    for r in PX + SX:
        chk(r["power"] in PW, f"affisso {r['name']}: potere {r['power']} sconosciuto")
        v = int(r["value1"] or 0)
        chk(v == int(r["value2"] or 0), f"affisso {r['name']}: value1 != value2 (valore variabile: serve il byte del valore, Abisso)")
        chk(-128 <= v <= 127, f"affisso {r['name']}: valore {v} fuori da un byte con segno")
        # (22/11) il gioco regge un totale negativo solo per questi poteri (recalc_stats, af_dur): vita, danno subito,
        # penetrazione e cadenza non hanno il controllo
        chk(v >= 0 or r["power"] in ("DMG", "ATT_DMG", "AC", "STR", "DUR"), f"affisso {r['name']}: valore negativo non previsto per {r['power']}")
        pw.append(PW.index(r["power"]) + 1); val.append(v & 255)
    # (22/11, fase 6) unici (data/items/next/uniques.tsv): nell'oggetto suffisso = $80 + numero dell'unico, prefisso 0, id = la
    # base. I poteri (fino a 4, valori fissi) sono righe in coda ad af_pw / af_val: unico u -> righe UN0 + 4u .. UN0 + 4u + 3
    # (potere 0 = riga vuota). Righe nuove solo in fondo al .tsv: il numero dell'unico sta nei salvataggi (riordinare o togliere
    # righe chiede un SAVE_VER nuovo)
    UQ = rows("uniques.tsv")
    gname = {it["name"]: i for i, (k, cat, it) in enumerate(items)}
    bname = {r["id"]: r["name"] for r in rows("bases.tsv")}
    chk(1 <= len(UQ) <= 32, "unici: da 1 a 32")
    un0 = len(pw)
    chk(un0 + 4 * len(UQ) <= 128, "unici: righe dei poteri oltre 127 (af_pw)")
    unb, unbc, unpl, unph, unn = [], [], [], [], []
    maxu = yaml.safe_load(open(os.path.join(nx, "affix_rules.yaml")))["names"]["max_unique"]
    for u in UQ:
        nm = u["name"]
        chk(len(nm) <= maxu, f"unico {nm}: nome oltre {maxu} caratteri")
        chk(u["base"] in bname and bname[u["base"]] in gname, f"unico {nm}: base {u['base']} sconosciuta")
        b = gname[bname[u["base"]]]
        chk(items[b][1] in ("weapon", "armor", "shield", "ring"), f"unico {nm}: la base deve essere arma, armatura, scudo o anello")
        lo, hi = int(u["min_level"]), int(u["max_level"])
        chk(0 <= lo <= hi <= 127, f"unico {nm}: finestra {lo}..{hi}")
        bch = int(u.get("boss_chapter") or 0)          # (22/11, D9) 0 = solo da una quest
        chk(0 <= bch <= 4, f"unico {nm}: boss_chapter {bch}")
        n = 0
        for k in range(4):
            p = u.get(f"power{k}") or ""
            if not p:
                continue
            chk(p in PW, f"unico {nm}: potere {p} sconosciuto")
            va, vb = int(u.get(f"v{k}a") or 0), int(u.get(f"v{k}b") or 0)
            chk(va == vb, f"unico {nm}: {p} con valore variabile ({va}..{vb})")
            chk(-128 <= va <= 127, f"unico {nm}: {p} {va} fuori da un byte con segno")
            if p == "DUR":
                chk(va in (50, 100, -50), f"unico {nm}: DUR solo +50, +100, -50 (af_dur)")
            pw.append(PW.index(p) + 1); val.append(va & 255); n += 1
        pw += [0] * (4 - n); val += [0] * (4 - n)
        pr = int(u["price"])
        chk(0 < pr < 65536, f"unico {nm}: prezzo {pr}")
        unb.append(b); unbc.append(bch); unpl.append(pr & 255); unph.append(pr >> 8)
        unn.append(asm_str(nm, "unico"))
    o(f"UN_N        = {len(UQ)}        ; (fase 6) unici: quanti, prima riga dei poteri in af_pw / af_val (4 righe per unico)")
    o(f"UN0         = {un0}")
    o.bytes("af_pw", pw)                 # potere della riga (PW_*); (22/11) in GAME con i poteri degli unici (prima nel font)
    o.bytes("af_val", val)               # valore della riga (con segno)
    FT.bytes("un_pl", unpl)               # prezzo dell'unico (it_cost)
    FT.bytes("un_ph", unph)
    # unici: base e capitolo del boss (22/11, D9: solo dai bauli dei boss, bu_roll; prima af_gen0 nella finestra dei livelli). Nella RAM del font (FT):
    # sotto l'I/O dopo gli slot dei piani non c'e' posto
    FT.bytes("un_base", unb)
    # (22/11, D9) capitolo del boss che puo' lasciare l'unico (0 = solo da una quest): bu_roll (combat.asm)
    FT.bytes("un_bch", unbc)
    # (21/11 sera, fase 3) generazione: livello minimo (bit 7 = maledetto: valore negativo), tipi di oggetto (bit 0 arma, 1 armatura,
    # 2 scudo, 3 anello: cat_bit >> 1), peso; prezzo aggiunto (con segno, 16 bit: E5, prezzi dei .tsv da tarare)
    TYB = {"weapon": 1, "armor": 2, "shield": 4, "ring": 8}
    amin, aty, ach, apl, aph = [0], [0], [0], [0], [0]
    for r in PX + SX:
        ml = int(r["min_level"])
        chk(0 <= ml <= 127, f"affisso {r['name']}: min_level {ml}")
        cur = int(r["value1"] or 0) < 0
        amin.append(ml | (0x80 if cur else 0))
        aty.append(sum(TYB[t] for t in r["item_types"].split(",")))
        # (fase 4) furto di vita e spine: dopo la 2.0 (decisione O5): righe con peso 0, non escono finche' il gioco non le fa
        ach.append(0 if r["power"] in ("LEECH", "THORNS") else byte(int(r["chance"]), f"{r['name']}.chance"))
        if r["power"] == "DUR":
            chk(int(r["value1"]) in (50, 100, -50), f"affisso {r['name']}: DUR solo +50, +100, -50 (af_dur)")
        pa = int(r["price_add"]) & 0xffff
        apl.append(pa & 255); aph.append(pa >> 8)
    chk(sum(ach[1:len(PX) + 1]) < 256 and sum(ach[len(PX) + 1:]) < 256, "affissi: la somma dei pesi deve stare in un byte (af_pick)")
    # (21/11 sera, spazio di GAME) le tabelle che servono solo a generare stanno sotto l'I/O con il generatore (out/work/afgen.asm,
    # incluso in fondo a src/game/gen_io.asm): af_gen le legge con $01 = $34 e interrupt spenti
    ag = Out()
    ag.bytes("af_min", amin)
    ag.bytes("af_ty", aty)
    ag.bytes("af_ch", ach)
    FT.bytes("af_pl", apl)
    FT.bytes("af_ph", aph)
    if "--check" not in sys.argv:
        open(os.path.join(os.path.dirname(DST), "fonttab.asm"), "w").write("; (gen_db.py) tabelle nella RAM del font della UI dopo i glifi (src/game.asm gd_font)\n" + "\n".join(FT.lines) + "\n")
    AR = yaml.safe_load(open(os.path.join(nx, "affix_rules.yaml")))
    q = AR["quality"]
    # magico con probabilita' base + per_t x T (T = chestLevel / 8), al massimo max: soglie su 256 per T = 0..31
    ag.bytes("mag_t", [pct256(min(q["magic"]["max"], q["magic"]["base"] + q["magic"]["per_t"] * t), "magic") for t in range(32)])
    a = q["affixes"]
    o(f"AFQ_P       = {pct256(a['prefix'], 'affixes.prefix')}       ; fra i magici: solo prefisso sotto AFQ_P, solo suffisso sotto AFQ_S, poi entrambi (su 256)")
    o(f"AFQ_S       = {pct256(a['prefix'] + a['suffix'], 'affixes.suffix')}")
    ac = AR["affix_choice"]
    chk(ac["low_fraction"] == 0.5 and ac.get("cursed_any_level"), "affix_choice: il gioco fa la finestra con 2 x min_level >= livello (low_fraction 0.5) e i maledetti fuori finestra")
    o(f"AF_TOP      = {byte(ac['top_level'], 'top_level')}       ; finestra: livello al massimo AF_TOP")
    o("RATE_MIN    = 6        ; (fase 4) cadenza minima dell'attacco base con gli affissi (fotogrammi)")
    o(f"CURSE_T     = {pct256(ac['cursed_share'], 'cursed_share')}       ; affisso maledetto con probabilita' CURSE_T / 256")
    chk(AR["rings"] == {"copper": 1, "silver": 2, "gold": 2}, "rings: il gioco fa rame 1, argento e oro 2 (oro: prefisso del livello piu' alto)")
    sm = AR["shops"]["magic"]
    bu = q["boss_unique"]
    o(f"UNB_C       = {pct256(bu['chapter_boss'], 'boss_unique.chapter_boss')}       ; (22/11, D9) unico dal baule del boss del capitolo: UNB_C / 256")
    o(f"UNB_N       = {pct256(bu['named_boss'], 'boss_unique.named_boss')}       ; ... dal baule del boss con nome degli altri piani: UNB_N / 256")
    ag.bytes("shm_t", [pct256(min(sm["max"], sm["base"] + sm["per_level"] * l), "shops.magic") for l in range(21)])   # negozi: merce magica per livello del PG
    if "--check" not in sys.argv:
        open(os.path.join(os.path.dirname(DST), "afgen.asm"), "w").write("; (gen_db.py) tabelle di generazione degli affissi, sotto l'I/O\n" + "\n".join(ag.lines) + "\n")
    def find(rs, power, v, typ):
        for i, r in enumerate(rs, 1):
            if r["power"] == power and int(r["value1"] or 0) == v and typ in r["item_types"].split(","):
                return i
        raise Err(f"affissi: nessuna riga {power} {v} per {typ}")
    # magia +N di oggi -> prefisso (armi ATT_DMG, armature e scudi AC): indice categoria x 4 + N (gen_item)
    mag = []
    for typ, pwn in (("weapon", "ATT_DMG"), ("armor", "AC"), ("shield", "AC")):
        mag += [0] + [find(PX, pwn, n, typ) for n in (1, 2, 3)]
    chk(len(mag) == 12, "mag_px")         # (fase 3: non piu' una tabella del gioco, solo le costanti MAG_*)
    chk(mag[4:8] == mag[8:12], "affissi: armature e scudi devono avere gli stessi prefissi di CA +1..+3 (MAG_A)")
    for n in (1, 2, 3):                  # costanti per le varianti di prova e l'arena (levels.asm, src/test/arena.asm, tools/vice/arena.py)
        o(f"MAG_W{n}      = {mag[n]}        ; prefisso della magia +{n} di un'arma")
        o(f"MAG_A{n}      = {mag[4 + n]}        ; ... di armatura e scudo")
    # anello: caratteristica (FOR, DES, COS) x 3 + metallo (itval 1..3) - 1 -> suffisso (gen_item, negozio)
    rsx = [find(SX, st, n, "ring") for st in ("STR", "DEX", "CON") for n in (1, 2, 3)]
    for i, v in enumerate(rsx):
        o(f"RSX_{i // 3 + 1}{i % 3 + 1}      = {v}        ; suffisso di un anello: caratteristica {i // 3 + 1} (FOR, DES, COS), metallo {i % 3 + 1}")
    # nomi in CORE (out/work/afnames.asm): prefissi e suffissi senza "of " (lo stampa af_name), 0 finale
    for r in PX:
        names.append(asm_str(r["name"], "prefisso"))
    for r in SX:
        chk(r["name"].startswith("of "), f"suffisso {r['name']}: deve cominciare con 'of '")
        names.append(asm_str(r["name"][3:], "suffisso"))
    # (senza .enc: si include in src/game/inv.asm, gia' in codifica "screen" come tutto CORE; un .enc "none" qui cambiava il resto)
    an = ["af_names                        ; (gen_db.py) nomi degli affissi a 5 bit (#t5, leggibili qui): prefissi, suffissi senza \"of \""]
    for n in names:
        an.append(f'        #t5 "{n}"')
    if "--check" not in sys.argv:
        open(os.path.join(os.path.dirname(DST), "afnames.asm"), "w").write("\n".join(an) + "\n")
    o()

    # ------------------------------------------------------------ nomi (codici schermo)
    o('        .enc "screen"')
    o.strings("itnm", [asm_str(it["name"], f"nome {k}") for k, _, it in items], t5=True)   # (21/11 sera) a 5 bit: ui_item / ip_puts
    o("un_names                        ; (fase 6) nomi degli unici a 5 bit (#t5, leggibili qui), uno dopo l'altro (it_nm)")
    for n in unn:
        o(f'        #t5 "{n}"')
    # (15/11) niente piu' tn_*: i nomi dei tipi stanno nel file del tema del capitolo (tools/build/gen_gfx.py, NM_AT)
    o.strings("fn", [asm_str(n, "boss") for n in bw["first_names"]])
    o.strings("ep", [asm_str(n, "boss") for n in bw["epithets"]])
    o('        .enc "none"')
    if "--check" not in sys.argv:
        open(DST, "w").write("\n".join(o.lines) + "\n")
    print(f"ok: {DST} ({len(items)-1} oggetti, {len(mons_r)} mostri, {maxl} piani, xp al livello {plmax}: {need[-1]})")


if __name__ == "__main__":
    try:
        main()
    except Err as e:
        print("ERRORE dati:", e)
        sys.exit(1)
