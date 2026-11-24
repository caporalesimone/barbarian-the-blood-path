#!/usr/bin/env python3
"""(24/11, TODO M9) Statistiche dei mostri per capitolo.

Il gioco ha 9 tipi di mostro (1..4 base, 5..8 forti, 9 boss finale) con le schede del capitolo 1 (righe implemented = yes del
bestiario, tools/build/gen_db.py) e la crescita per piano. Un capitolo con `own_stats: true` (data/chapters.yaml) da' ai suoi
tipi 1..8 statistiche proprie, ricavate dal suo bestiario SENZA cambiare la difficolta' media del piano:

- per ogni gruppo (4 base, 4 forti) si confrontano le righe del capitolo con la loro media: vita e danno medi diventano
  fattori k (media 1), CA, ATT, salvezza e velocita' scarti d (media 0);
- il tipo t del capitolo = il tipo t del capitolo 1 (stesso piano minimo, stessa crescita, stessi dadi) con vita x k_vita,
  danno x k_danno (sul bonus fisso del danno), CA/ATT/salvezza + d, velocita' = media del gruppo del capitolo 1 + d,
  esperienza x (k_vita + k_danno) / 2, bonus del livello del bottino del bestiario.

Le tabelle che cambiano (CH_FIELDS, 10 byte ciascuna: tipo 0..9) stanno contigue in GAME a `mt_ch` (gen_db.py); ogni file
del tema (GFXn, tools/build/gen_gfx.py) porta in coda i tipi 1..8 di FILE_FIELDS (64 B: i byte alti di vita ed esperienza
devono restare quelli del capitolo 1), che gfx_install copia nei loro posti di `mt_ch`. I capitoli senza
`own_stats` portano quelle del capitolo 1. Tipo 0 e tipo 9 (boss finale) restano sempre quelli del capitolo 1."""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bestiary      # noqa: E402

CH_FIELDS = ("hp_lo", "hp_hi", "ac", "att", "dk", "sv", "xp_lo", "xp_hi", "spd", "llb")
FILE_FIELDS = ("hp_lo", "ac", "att", "dk", "sv", "xp_lo", "spd", "llb")   # nel file del tema: tipi 1..8 (hp_hi, xp_hi uguali)


def dice(s):
    s = str(s).replace(" ", "")
    m = re.fullmatch(r"(?:(\d+)d(\d+))?([+-]\d+)?|(\d+)", s)
    if m is None:
        raise ValueError("dadi non validi: " + s)
    if m.group(4):
        return 0, 0, int(m.group(4))
    return int(m.group(1) or 0), int(m.group(2) or 0), int(m.group(3) or 0)


def avg(s):
    n, d, k = dice(s)
    return n * (d + 1) / 2 + k


def _b(v, what):
    v = int(v)
    if not 0 <= v <= 255:
        raise ValueError("%s: %d non e' un byte" % (what, v))
    return v


def ch1_tables(R, B):
    """tabelle CH_FIELDS del capitolo 1 (come gen_db.py: tipi 0..9, 0 = nessuno)"""
    t = {f: [0] for f in CH_FIELDS}
    t["dn"], t["ds"] = [0], [0]
    for (k, m), (_, b) in zip(R["monsters"].items(), B["monsters"].items()):
        havg = avg(m["hp"])
        if m.get("final"):
            havg *= R.get("final_boss_hp_mult", 1)
        h = int(round(havg))
        dn, ds, dk = dice(m["dmg"])
        t["hp_lo"].append(h & 255)
        t["hp_hi"].append(h >> 8)
        t["ac"].append(_b(m["ac"], k))
        t["att"].append(_b(m["att"], k))
        t["dn"].append(dn)
        t["ds"].append(ds)
        t["dk"].append(_b(dk, k))
        t["sv"].append(_b(m["save"], k))
        t["xp_lo"].append(m["xp"] & 255)
        t["xp_hi"].append(m["xp"] >> 8)
        t["spd"].append(_b(max(1, round(b["speed"] * B.get("monster_speed_percent", 100) / 100)), k))
        t["llb"].append(_b(b.get("loot_level_bonus", 0), k))
    return t


def own_chapters(root=os.path.join(HERE, "..", "..")):
    import yaml
    d = yaml.safe_load(open(os.path.join(root, "data", "chapters.yaml")))
    return {c["id"] for c in d["chapters"] if c.get("own_stats")}


def chapter_tables(R, B, c, rows=None):
    """tabelle CH_FIELDS del capitolo c (dict campo -> 10 valori)"""
    rows = rows or bestiary.load()
    t1 = ch1_tables(R, B)
    if c == 1 or c not in own_chapters():
        return {f: list(t1[f]) for f in CH_FIELDS}
    g1 = bestiary.game_rows(rows)
    out = {f: list(t1[f]) for f in CH_FIELDS}
    sp = B.get("monster_speed_percent", 100) / 100
    for tier, off in (("base", 0), ("strong", 4)):
        cr = [r for r in rows if r["chapter"] == c and r["tier"] == tier]
        r1 = [r for r in g1 if r["tier"] == tier]
        if len(cr) != 4 or len(r1) != 4:
            raise ValueError("capitolo %d: servono 4 mostri %s (e 4 nel capitolo 1)" % (c, tier))
        mh = sum(avg(r["hp"]) for r in cr) / 4
        md = sum(avg(r["dmg"]) for r in cr) / 4
        mean = lambda f, rs: sum(r[f] for r in rs) / 4
        for i, r in enumerate(cr):
            x = off + i + 1                      # tipo 1..8
            kh, kd = avg(r["hp"]) / mh, avg(r["dmg"]) / md
            h = max(1, int(round((t1["hp_lo"][x] + 256 * t1["hp_hi"][x]) * kh)))
            out["hp_lo"][x], out["hp_hi"][x] = h & 255, h >> 8
            d1 = t1["dn"][x] * (t1["ds"][x] + 1) / 2 + t1["dk"][x]
            out["dk"][x] = _b(max(0, round(d1 * kd - t1["dn"][x] * (t1["ds"][x] + 1) / 2)), r["id"] + ".dk")
            for f, col in (("ac", "ac"), ("att", "att"), ("sv", "save")):
                out[f][x] = _b(max(0, t1[f][x] + round(r[col] - mean(col, cr))), "%s.%s" % (r["id"], f))
            s = mean("speed", r1) + (r["speed"] - mean("speed", cr))
            out["spd"][x] = _b(max(1, round(s * sp)), r["id"] + ".spd")
            xp = int(round((t1["xp_lo"][x] + 256 * t1["xp_hi"][x]) * (kh + kd) / 2))
            out["xp_lo"][x], out["xp_hi"][x] = xp & 255, xp >> 8
            out["llb"][x] = _b(r["loot_level_bonus"], r["id"] + ".llb")
    return out


def block(R, B, c, rows=None):
    """byte del blocco `mt_ch` in GAME per il capitolo c (CH_FIELDS in fila, tipi 0..9)"""
    t = chapter_tables(R, B, c, rows)
    return bytes(v for f in CH_FIELDS for v in t[f])


def file_block(R, B, c, rows=None):
    """byte in coda al file del tema (FILE_FIELDS, tipi 1..8: 64 B; i byte alti, tipo 0 e tipo 9 restano quelli del
    capitolo 1). gfx_install li copia nei posti 1..8 delle tabelle di mt_ch"""
    t, t1 = chapter_tables(R, B, c, rows), ch1_tables(R, B)
    for f in ("hp_hi", "xp_hi"):
        if t[f] != t1[f]:
            raise ValueError("capitolo %d: %s %s diverso dal capitolo 1 %s (non e' nel file del tema)" % (c, f, t[f], t1[f]))
    return bytes(v for f in FILE_FIELDS for v in t[f][1:9])


def load():
    import items_db
    return items_db.load_rules(os.path.join(HERE, "..", "..")), bestiary.load_balance(os.path.join(HERE, "..", ".."))


if __name__ == "__main__":
    R, B = load()
    rows = bestiary.load()
    for c in range(1, 5):
        t = chapter_tables(R, B, c, rows)
        print("== capitolo %d%s" % (c, "" if c == 1 or c in own_chapters() else " (come il capitolo 1)"))
        for x in range(1, 9):
            print("  tipo %d  vita %4d  CA %2d  ATT %2d  danno +%-2d  salv %d  vel %2d  xp %4d  llb %d" % (
                x, t["hp_lo"][x] + 256 * t["hp_hi"][x], t["ac"][x], t["att"][x], t["dk"][x], t["sv"][x], t["spd"][x],
                t["xp_lo"][x] + 256 * t["xp_hi"][x], t["llb"][x]))
