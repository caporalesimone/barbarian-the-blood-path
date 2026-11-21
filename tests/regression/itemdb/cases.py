"""Item database (11/11; sanity of the item database, moved to regression on 11/11): data/items/items.tsv is the source of truth of every item (tools/build/items_db.py), the game data
(out/work/db.asm, labels itcat/itfl/itprice) must match it, the table checker must refuse a wrong table, and the two-handed
rule (no shield with a two-handed weapon) must hold in the inn too (module OVL2, h_equip), not only in the inventory
(INV-2H-10/11). The first tests are pure Python; the inn tests share one VICE session in the village."""
import os, sys, tempfile
from c64test import test, check
from lib.play import new_game, INN_DOOR, list_to, key, K_E

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "simulators")]
import items_db as I  # noqa: E402

CATS = ["weapon", "armor", "shield", "ring", "potion", "scroll"]       # CAT_* = index + 1 (gen_db.py)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def game(ctx):
    if "g" not in ctx:
        from lib.c64 import Game
        g = ctx["g"] = Game()
        g.to_menu()
        new_game(g); g.frames(3)
    return ctx["g"]


@test("ITEMDB-10", "items.tsv: valid table, consumable = potion/scroll, equipment = weapon/armor/shield/ring, weapons 1 or 2 hands")
def db_valid(ctx):
    rows = I.load()
    check(rows, "empty table")
    for r in rows:
        want = "consumable" if r["type"] in ("potion", "scroll") else "equipment"
        check(r["category"] == want, "%s: category %s (expected %s)" % (r["id"], r["category"], want))
        if r["type"] == "weapon":
            check(r["hands"] in (1, 2), "%s: hands %s" % (r["id"], r.get("hands")))
        else:
            check("hands" not in r, "%s: hands on a %s" % (r["id"], r["type"]))
    check(any(r["type"] == "weapon" and r["hands"] == 2 and r["tier"] == "base" for r in rows), "no two-handed weapon in the game")


@test("ITEMDB-11", "the checker refuses a wrong table: shield with hands, duplicate id, missing price, unknown type")
def db_refuse(ctx):
    good = open(I.TSV).read().splitlines()
    head, rows = good[0], good[1:]
    col = I.COLUMNS.index

    shield = next(l for l in rows if l.split("\t")[col("type")] == "shield")
    sword = next(l for l in rows if l.split("\t")[col("type")] == "weapon")
    cases = []
    c = shield.split("\t"); c[col("hands")] = "2"; cases.append(("shield with hands", [head, "\t".join(c)]))
    cases.append(("duplicate id", [head, sword, sword]))
    c = shield.split("\t"); c[col("price")] = ""; cases.append(("missing price", [head, "\t".join(c)]))
    c = shield.split("\t"); c[col("type")] = "helmet"; cases.append(("unknown type", [head, "\t".join(c)]))
    c = sword.split("\t"); c[col("hands")] = "3"; cases.append(("three hands", [head, "\t".join(c)]))
    for what, lines in cases:
        with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, dir=os.path.join(ROOT, "out", "tmp")) as f:
            f.write("\n".join(lines) + "\n")
        try:
            I.load(f.name)
            check(False, "%s: accepted" % what)
        except ValueError:
            pass
        finally:
            os.unlink(f.name)


@test("ITEMDB-12", "game data = table: item ids in table order, category, price and the two-handed flag (itfl bit 0)")
def db_game(ctx):
    g = game(ctx)
    L = g.L
    rows = [r for r in I.load() if r["tier"] == "base"]
    order = sorted(rows, key=lambda r: CATS.index(r["type"]))          # gen_db: ids by category, table order inside
    check(L["N_ITEMS"] == len(rows) + 1, "N_ITEMS %d, table %d items" % (L["N_ITEMS"], len(rows)))
    cat, fl = g.mem(L["itcat"], len(rows) + 1), g.mem(L["itfl"], len(rows) + 1)
    for i, r in enumerate(order, 1):
        check(L["I_" + r["id"].upper()] == i, "%s: id %d (expected %d)" % (r["id"], L["I_" + r["id"].upper()], i))
        check(cat[i] == CATS.index(r["type"]) + 1, "%s: itcat %d" % (r["id"], cat[i]))
        check(g.w16(L["itprice"] + 2 * i) == r["price"], "%s: price %d (table %d)" % (r["id"], g.w16(L["itprice"] + 2 * i), r["price"]))
        if r["type"] == "weapon":
            check((fl[i] & 1) == (r["hands"] == 2), "%s: itfl %02x, hands %d" % (r["id"], fl[i], r["hands"]))


def pack(g, *ids):
    L = g.L
    ids = list(ids) + [0] * (8 - len(ids))
    g.poke(L["c_pack"], *ids)
    g.poke(L["c_packd"], *[30 if i else 0 for i in ids]); g.poke(L["c_packm"], *[40 if i else 0 for i in ids])
    g.poke(L["c_packb"], *[0] * 8)


def equip(g, slot, item):
    L = g.L
    g.poke(L["c_eq"] + slot, item); g.poke(L["c_eqd"] + slot, 30 if item else 0); g.poke(L["c_eqm"] + slot, 40 if item else 0)
    g.poke(L["c_eqb"] + slot, 0)


def inn_open(g):
    g.teleport(*INN_DOOR); g.frames(3); g.press_fire(); g.frames(5, tmax=60)
    check(not g.in_game(), "the inn did not open")


def inn_close(g):
    g.run_stop(); g.frames(3)
    check(g.in_game(), "RUN/STOP does not close the inn")


@test("INN-2H-10", "inn: shield with a two-handed weapon on: refused (the shield stays in the pack)")
def inn_shield(ctx):
    g = game(ctx); L = g.L
    equip(g, 0, L["I_VIKING_SWORD"]); equip(g, 2, 0); pack(g, L["I_SMALL_SHIELD"])
    inn_open(g)
    check(list_to(g, 0, "ui_cur", 0), "cursor not on the pack shield")   # (21/11) list yours, pack slot 0
    key(g, K_E, 2)                                        # E: wear
    check(g.b(L["c_eq"] + 2) == 0, "the shield was equipped with a two-handed weapon")
    check(L["I_SMALL_SHIELD"] in g.mem(L["c_pack"], 8), "the shield left the pack: %s" % g.mem(L["c_pack"], 8))
    inn_close(g)


@test("INN-2H-11", "inn: two-handed weapon with a shield on: equipped, the shield and the old weapon go to the pack")
def inn_two(ctx):
    g = game(ctx); L = g.L
    equip(g, 0, L["I_SWORD"]); equip(g, 2, L["I_SMALL_SHIELD"]); pack(g, L["I_VIKING_SWORD"])
    inn_open(g)
    check(list_to(g, 0, "ui_cur", 0), "cursor not on the pack weapon")   # (21/11) list yours, pack slot 0
    key(g, K_E, 2)                                        # E: wear
    check(g.b(L["c_eq"]) == L["I_VIKING_SWORD"], "weapon %d (expected the viking sword)" % g.b(L["c_eq"]))
    check(g.b(L["c_eq"] + 2) == 0, "shield %d still on with a two-handed weapon" % g.b(L["c_eq"] + 2))
    pk = g.mem(L["c_pack"], 8)
    check(L["I_SMALL_SHIELD"] in pk and L["I_SWORD"] in pk, "pack %s (expected the shield and the sword)" % pk)
    inn_close(g)


@test("ITEMDB-NEXT-10", "next item database (data/items/next, proposal of 20/11): full names <= 37, unique names <= 16, affix values fit a byte, ids fit the record")
def next_db(ctx):
    import items_model as M
    bad = M.check()
    check(not bad, "; ".join(bad[:4]) + (" (+%d)" % (len(bad) - 4) if len(bad) > 4 else ""))
    check(len(M.BASES) == 31, "%d bases (expected 31, decision O1)" % len(M.BASES))
