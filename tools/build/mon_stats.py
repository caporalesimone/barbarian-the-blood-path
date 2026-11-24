#!/usr/bin/env python3
"""(24/11, TODO M9) Statistiche dei mostri: dalle formule del bestiario ai coefficienti del C64 (docs/wiki/bestiario.md).

`data/monsters/bestiary.tsv` e' il database dei mostri: le colonne `hp`, `ac`, `att`, `save`, `xp` e il bonus di `dmg`
sono formule (`9 + 2.56*P`), la colonna `floor` e' il primo piano in cui il mostro compare (FIRST). Variabili:

    L      piano (profondita' globale, 1..)          P      piani dopo il primo: L - FIRST (mai sotto 0)
    FIRST  la colonna floor della riga               C      capitolo del piano L (5 piani per capitolo)
    F      piano nel capitolo (1..5)

Operazioni: + - * / e parentesi, min, max, round, numeri e le costanti con nome di data/monsters/constants.yaml (anche
formule). Dentro i piani in cui la riga si usa la formula deve essere LINEARE in L (la build si ferma dicendo mostro e
colonna): il C64 non valuta formule, entrando in un piano calcola per ogni tipo e statistica

    valore = A + ((B x P + 8) >> 4)        A = formula al piano FIRST (arrotondata), B = crescita per piano x 16

(floor_types in src/game/combat.asm; P = 0 per il boss finale). Questo modulo fa le stesse operazioni intere: gen_db.py
(tabelle in GAME), gen_gfx.py (coda del file del tema), simulatori (tools/simulators/rules.py) e test leggono di qui.

Tipi del gioco: 1..4 base, 5..8 forti, 9 boss finale. Un capitolo con `own_stats: true` (data/chapters.yaml) usa come tipi
1..8 le sue righe base e forti (nell'ordine del file); gli altri capitoli quelle del capitolo 1. Le tabelle FIELDS (10 byte
ciascuna: tipo 0..9) stanno contigue in GAME a `mt_ch` (+ `mt_z`, 10 zeri: parte alta delle statistiche a 8 bit); ogni file
del tema porta in coda i tipi 1..8 di FIELDS (160 B), che gfx_install copia nei loro posti."""
import ast, operator, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
import bestiary      # noqa: E402
import yaml          # noqa: E402

FIELDS = ("fmin", "hp_lo", "hp_hi", "hp_b", "ac", "ac_b", "att", "att_b", "dn", "ds", "dk", "dk_b", "sv", "sv_b",
          "xp_lo", "xp_hi", "xp_bl", "xp_bh", "spd", "llb")
CH_FIELDS = FIELDS + ("z",)          # in GAME: + mt_z (zeri)
FILE_FIELDS = FIELDS                 # in coda al file del tema: tipi 1..8
# statistica: colonna del bestiario, valore massimo, B a 16 bit
STATS = (("hp", "hp", 65535, False), ("ac", "ac", 255, False), ("att", "att", 255, False), ("dk", "dmg", 255, False),
         ("sv", "save", 255, False), ("xp", "xp", 65535, True))
CPF = 5                              # piani per capitolo (data/chapters.yaml)
CONSTANTS = os.path.join(ROOT, "data", "monsters", "constants.yaml")

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
_FUN = {"min": min, "max": max, "round": round}
_CONST = None


def constants():
    global _CONST
    if _CONST is None:
        d = yaml.safe_load(open(CONSTANTS)) if os.path.exists(CONSTANTS) else None
        _CONST = (d or {}).get("constants") or {}
    return _CONST


def ev(expr, env, _seen=()):
    """valore della formula `expr` (str o numero) con le variabili `env`"""
    if isinstance(expr, (int, float)):
        return expr
    def walk(n):
        if isinstance(n, ast.Expression):
            return walk(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _BIN:
            return _BIN[type(n.op)](walk(n.left), walk(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            v = walk(n.operand)
            return -v if isinstance(n.op, ast.USub) else v
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _FUN and not n.keywords:
            return _FUN[n.func.id](*[walk(a) for a in n.args])
        if isinstance(n, ast.Name):
            if n.id in env:
                return env[n.id]
            c = constants()
            if n.id in c:
                if n.id in _seen:
                    raise ValueError("costante %s definita con se stessa" % n.id)
                return ev(c[n.id], env, _seen + (n.id,))
            raise ValueError("nome sconosciuto %s (variabili L, P, FIRST, C, F; costanti: %s)" % (n.id, CONSTANTS))
        raise ValueError("formula non ammessa: %s" % ast.dump(n))
    try:
        tree = ast.parse(str(expr).strip(), mode="eval")
    except SyntaxError:
        raise ValueError("formula non valida: %r" % expr)
    return walk(tree)


def dice(s):
    s = str(s).replace(" ", "")
    m = re.fullmatch(r"(?:(\d+)d(\d+))?([+-]\d+)?|(\d+)", s)
    if m is None:
        raise ValueError("dadi non validi: " + s)
    if m.group(4):
        return 0, 0, int(m.group(4))
    return int(m.group(1) or 0), int(m.group(2) or 0), int(m.group(3) or 0)


def split_dmg(s):
    """'1d4 + 1 + P' -> (1, 4, '1 + P'); formula senza dadi -> (0, 0, formula)"""
    m = re.fullmatch(r"\s*(\d+)d(\d+)\s*(?:([+-])(.*))?", str(s))
    if m:
        return int(m.group(1)), int(m.group(2)), (m.group(3) + m.group(4)) if m.group(3) else "0"
    return 0, 0, str(s)


def env(r, L):
    c = (L - 1) // CPF + 1
    return {"L": L, "P": max(0, L - r["floor"]), "FIRST": r["floor"], "C": c, "F": L - CPF * (c - 1)}


def floors(r, nf=20):
    """piani in cui la riga si usa (crescita controllata li'): capitolo 1 = tipi del gioco anche nei capitoli senza
    own_stats, fino al piano nf; gli altri il loro capitolo; il boss finale il suo piano (P = 0)"""
    if "final" in r["flags"]:
        return [r["floor"]]
    last = nf if r["chapter"] == 1 else max(r["floor"], CPF * r["chapter"])
    return list(range(r["floor"], last + 1))


def coef(r, nf=20, speed_pct=100):
    """coefficienti del C64 della riga (dict: fmin, dn, ds, spd, llb, e per ogni statistica (A, B)), con i controlli"""
    who = r["id"]
    dn, ds, dkf = split_dmg(r["dmg"])
    fl = floors(r, nf)
    out = {"fmin": r["floor"], "dn": dn, "ds": ds, "final": "final" in r["flags"],
           "spd": max(1, round(r["speed"] * speed_pct / 100)), "llb": r["loot_level_bonus"]}
    for st, col, mx, wide in STATS:
        expr = dkf if st == "dk" else r[col]
        try:
            v = {L: ev(expr, env(r, L)) for L in fl}
        except (ValueError, ZeroDivisionError, TypeError) as e:
            raise ValueError("%s.%s: %s" % (who, col, e))
        a = v[fl[0]]
        s = v[fl[1]] - a if len(fl) > 1 else 0
        for L in fl:
            if abs(v[L] - (a + s * (L - fl[0]))) > 1e-6:
                raise ValueError("%s.%s: formula %r non lineare nei piani %d-%d (al piano %d vale %g, la retta %g)"
                                 % (who, col, expr, fl[0], fl[-1], L, v[L], a + s * (L - fl[0])))
        A, B = int(round(a)), int(round(s * 16))
        if B < 0:
            raise ValueError("%s.%s: crescita negativa (%g per piano)" % (who, col, s))
        if B > (65535 if wide else 255):
            raise ValueError("%s.%s: crescita %g per piano oltre il limite (%g)" % (who, col, s, (65535 if wide else 255) / 16))
        if not 0 <= A <= mx:
            raise ValueError("%s.%s: %d al piano %d fuori da 0..%d" % (who, col, A, fl[0], mx))
        top = c64(A, B, fl[-1] - fl[0])
        if top > mx:
            raise ValueError("%s.%s: %d al piano %d oltre %d" % (who, col, top, fl[-1], mx))
        out[st] = (A, B)
    for k, v in (("dn", dn), ("ds", ds), ("spd", out["spd"]), ("llb", out["llb"]), ("fmin", out["fmin"])):
        if not 0 <= v <= 255:
            raise ValueError("%s: %s %d non e' un byte" % (who, k, v))
    return out


def c64(A, B, P):
    """una statistica come floor_types: A + ((B x P + 8) >> 4), 16 bit"""
    return (A + ((B * P + 8) >> 4)) & 0xFFFF


def values(cf, L, nf=20):
    """statistiche di un tipo (coefficienti `cf`) al piano L, come il C64 (piano oltre nf: quello di nf)"""
    L = min(L, nf)
    P = 0 if cf["final"] else max(0, L - cf["fmin"])
    out = {st: c64(*cf[st], P) for st, _, _, _ in STATS}
    out.update(dn=cf["dn"], ds=cf["ds"], P=P)
    return out


def own_chapters(root=ROOT):
    d = yaml.safe_load(open(os.path.join(root, "data", "chapters.yaml")))
    return {c["id"] for c in d["chapters"] if c.get("own_stats")}


def type_rows(c, rows=None):
    """le 9 righe dei tipi 1..9 nel capitolo c"""
    rows = rows or bestiary.load()
    g1 = bestiary.game_rows(rows)
    t = [r for r in g1 if r["tier"] in ("base", "strong")]
    if c in own_chapters():
        t = [r for r in rows if r["chapter"] == c and r["tier"] == "base"] + \
            [r for r in rows if r["chapter"] == c and r["tier"] == "strong"]
        if len(t) != 8:
            raise ValueError("capitolo %d: servono 4 mostri base e 4 forti, ci sono %d righe" % (c, len(t)))
    return t + [g1[-1]]


def chapter_tables(R, B, c, rows=None):
    """tabelle CH_FIELDS del capitolo c (dict campo -> 10 valori, tipo 0 = nessuno)"""
    nf = R["dungeon"]["floors"]
    pct = B.get("monster_speed_percent", 100)
    t = {f: [0] for f in CH_FIELDS}
    for r in type_rows(c, rows):
        cf = coef(r, nf, pct)
        hp, ac, att, dk, sv, xp = (cf[s] for s, _, _, _ in STATS)
        for f, v in (("fmin", cf["fmin"]), ("hp_lo", hp[0] & 255), ("hp_hi", hp[0] >> 8), ("hp_b", hp[1]),
                     ("ac", ac[0]), ("ac_b", ac[1]), ("att", att[0]), ("att_b", att[1]), ("dn", cf["dn"]),
                     ("ds", cf["ds"]), ("dk", dk[0]), ("dk_b", dk[1]), ("sv", sv[0]), ("sv_b", sv[1]),
                     ("xp_lo", xp[0] & 255), ("xp_hi", xp[0] >> 8), ("xp_bl", xp[1] & 255), ("xp_bh", xp[1] >> 8),
                     ("spd", cf["spd"]), ("llb", cf["llb"]), ("z", 0)):
            t[f].append(v)
    return t


def ch1_tables(R, B, rows=None):
    return chapter_tables(R, B, 1, rows)


def block(R, B, c, rows=None):
    """byte del blocco `mt_ch` in GAME per il capitolo c (CH_FIELDS in fila, tipi 0..9)"""
    t = chapter_tables(R, B, c, rows)
    return bytes(v for f in CH_FIELDS for v in t[f])


def file_block(R, B, c, rows=None):
    """byte in coda al file del tema (FILE_FIELDS, tipi 1..8: 160 B); gfx_install li copia nei posti 1..8 di mt_ch"""
    t = chapter_tables(R, B, c, rows)
    return bytes(v for f in FILE_FIELDS for v in t[f][1:9])


def coefs_by_id(R, B, rows=None):
    """coefficienti di ogni riga del bestiario (anche concept), per id"""
    nf, pct = R["dungeon"]["floors"], B.get("monster_speed_percent", 100)
    return {r["id"]: coef(r, nf, pct) for r in rows or bestiary.load()}


def load():
    import items_db
    return items_db.load_rules(ROOT), bestiary.load_balance(ROOT)


def report(R, B, rows=None):
    """tabella dei valori per piano (vita, CA, ATT, danno, salvezza, esperienza) dei tipi di ogni capitolo"""
    rows = rows or bestiary.load()
    nf = R["dungeon"]["floors"]
    out = []
    for c in range(1, nf // CPF + 1):
        own = c == 1 or c in own_chapters()
        out.append("== capitolo %d (piani %d-%d)%s" % (c, CPF * c - 4, CPF * c, "" if own else ": tipi del capitolo 1"))
        for x, r in enumerate(type_rows(c, rows), 1):
            cf = coef(r, nf, B.get("monster_speed_percent", 100))
            cells = []
            for L in range(CPF * c - 4, CPF * c + 1):
                v = values(cf, L, nf)
                cells.append("%3d/%2d/%2d/%dd%d+%-2d" % (v["hp"], v["ac"], v["att"], v["dn"], v["ds"], v["dk"]))
            out.append("  %d %-16s fmin %2d  %s" % (x, r["id"], cf["fmin"], "  ".join(cells)))
    return "\n".join(out)


if __name__ == "__main__":
    R, B = load()
    print("vita/CA/ATT/danno per piano (valori del C64, src/game/combat.asm floor_types)")
    print(report(R, B))
