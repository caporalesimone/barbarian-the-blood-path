#!/usr/bin/env python3
"""Concept delle mappe dei villaggi dei capitoli 2-5 (15/11, TODO Z2): scrive data/town_map2.txt ... town_map5.txt.
Ogni villaggio ha una struttura sua (non lo stesso villaggio con altri colori): palafitte su un lago, un campo a terrazze
sulla montagna, una citta' in rovina attorno a un cratere, isole sospese nel vuoto. Come per il villaggio 1, lo script da'
la prima stesura: poi la fonte e' il testo in data/ (rilanciarlo riscrive il file). La build NON usa questo script.
Uso: python3 lab/villaggi/concept_maps.py [capitolo ...]"""
import sys
from mapkit import Map, write, W, H


# ------------------------------------------------------------------------------------------------ 2: Blackwater Mill
def blackwater():
    m = Map(2, "%")
    # la riva di fango a sud (costa ondulata), il resto e' lago
    for x in range(W):
        top = 41 + (1 if x % 11 < 4 else 0) - (1 if 14 <= x < 22 else 0) + (2 if x > 26 else 0) + (3 if x > 36 else 0)
        m.fill(x, top, x, 45, ".")
    m.fill(0, 46, 47, 47, "B"); m.fill(0, 0, 47, 1, "%")

    def platform(x0, y0, x1, y1, rail=True):
        m.fill(x0, y0, x1, y1, "+")
        m.fill(x0, y1 + 1, x1, y1 + 1, "A")                 # i pali sotto il bordo sud
        if rail:
            m.fill(x0, y0 - 1, x1, y0 - 1, "|", only="%")

    def hut(x, y, w, door="D", sign=None, chim=True, roof="R"):
        """capanna larga w: colmo, gronda, parete con la porta al centro; ritorna la porta"""
        mid = x + w // 2
        m.fill(x, y, x + w - 1, y, "r" if roof == "R" else roof)
        m.fill(x, y + 1, x + w - 1, y + 1, roof)
        if chim:
            m.put(x + 1, y, "c")
        m.fill(x, y + 2, x + w - 1, y + 2, "W")
        m.put(mid, y + 2, door)
        if sign:
            m.put(mid - 1, y + 2, sign)
        for xx in (x + 1, x + w - 2):
            if abs(xx - mid) > 1 or (not sign and xx != mid):
                m.put(xx, y + 2, "o")
        return mid, y + 2

    # la campana degli annegati, al centro
    platform(17, 16, 25, 22)
    m.rows(20, 17, "12", "34", "~~")
    m.rows(17, 16, "i"); m.rows(25, 16, "i"); m.rows(18, 16, "w"); m.rows(25, 21, "s")
    # fabbro (nord-ovest)
    hut(6, 7, 7, "S", "5"); platform(5, 10, 13, 12, rail=False); m.put(5, 10, "w"); m.put(13, 10, "i"); m.put(12, 12, "s")
    # alchimista (ovest), piccola e isolata
    hut(3, 24, 5, "L", "7"); platform(3, 27, 8, 28, rail=False); m.put(8, 27, "i")
    # locanda (sud-est), la capanna piu' grande
    hut(29, 29, 9, "H"); platform(28, 32, 38, 34, rail=False); m.put(28, 32, "w"); m.put(38, 32, "i"); m.put(37, 34, "s"); m.put(29, 34, "i")
    # capanne dei pescatori
    hut(26, 7, 5); platform(26, 10, 31, 11, rail=False); m.put(31, 10, "s")
    hut(14, 33, 5, chim=False); platform(14, 36, 19, 37, rail=False); m.put(19, 36, "w")
    # il mulino (nord-est) su un isolotto di fango, con la ruota nell'acqua: la botola della cantina e' l'ingresso
    m.blob(40, 13, 5.2, 3.2, ".", jag=0.15); m.fill(36, 11, 44, 12, ".")
    m.fill(36, 5, 44, 7, "l"); m.put(38, 5, "c"); m.fill(36, 8, 44, 10, "W")
    m.rows(36, 8, "WoWoWoWoW", "WWWWWWWWW", "WoWW>WWoW")
    m.rows(34, 8, "[]", "/\\")
    # piattaforma del portale (sud-est) e pontile dell'uscita (est) con il traghetto
    platform(39, 37, 44, 40); m.put(42, 38, "P"); m.put(39, 37, "i"); m.put(44, 40, "w")
    # passerelle: ":" est-ovest, "d" nord-sud
    w = "%()*T@tY"
    R = lambda pts: m.road(pts, ":", cv="d", only=w + ".,`A|")
    m.put(6, 45, "E"); m.road([(7, 44), (12, 44)], ":", only="."); m.put(6, 44, ":")
    R([(12, 43), (12, 23)]); R([(9, 28), (11, 28)]); R([(12, 22), (16, 22)])
    R([(16, 18), (14, 18)]); R([(13, 18), (13, 13)])
    R([(26, 17), (30, 17)]); R([(30, 16), (30, 12)]); R([(32, 11), (35, 11)])
    R([(22, 23), (22, 27)]); R([(22, 28), (27, 28)]); R([(28, 28), (28, 31)])
    R([(39, 33), (41, 33)]); R([(41, 34), (41, 36)])
    R([(42, 16), (42, 19)]); m.road([(42, 20), (46, 20)], ":", w=2, only=w); m.put(46, 20, "="); m.put(46, 21, "=")
    R([(43, 22), (43, 36)])
    R([(16, 38), (16, 40)])
    # barche, pali d'ormeggio, ninfee, canne, schiuma, mangrovie
    for x, y in ((8, 31), (19, 26), (33, 23), (44, 23), (24, 12), (9, 16), (33, 38)):
        if m.get(x, y) == "%" and m.get(x + 1, y) == "%":
            m.rows(x, y, "tY")
    m.scatter("@", 22, "%", near=":d+", far="tY")
    m.scatter("T", 46, "%", x0=0, x1=47, far=":d+=EPSLH>~")
    for x in range(W):
        for y in (0, 1):
            if m.r.random() < 0.55:
                m.put(x, y, "T")
    for y in range(2, 41):
        for x in (0, 1, 46, 47):
            if m.r.random() < 0.5 and m.get(x, y) == "%":
                m.put(x, y, "T")
    m.scatter(")", 70, "%", near=".T", dist=1); m.scatter(")", 12, "%")
    m.scatter("*", 40, "%", far=":d"); m.scatter("(", 70, "%")
    m.scatter("B", 26, ".", far=":dE"); m.scatter(",", 50, "."); m.scatter("`", 22, ".")
    return m.finish(lambda c: "B", keep=":d+")


# -------------------------------------------------------------------------------------------------- 3: The Last Camp
def lastcamp():
    m = Map(3, "l")
    # tre terrazze nella montagna (l = roccia): alta y 4-14, media y 19-30, bassa y 35-44; fra una e l'altra una parete
    # (R orlo innevato, W roccia, r piede) dal profilo a gradini
    m.fill(3, 4, 44, 44, ".")
    off1 = lambda x: (0, 1, 1, 0, 0, -1, 0, 1)[(x // 6) % 8]
    off2 = lambda x: (0, 0, 1, 1, 0, -1, -1, 0)[((x + 3) // 6) % 8]
    for x in range(3, 45):
        for base, off in ((15, off1), (31, off2)):
            y = base + off(x)
            m.put(x, y, "R"); m.put(x, y + 1, "W"); m.put(x, y + 2, "W"); m.put(x, y + 3, "r")
        m.put(x, 3, "W"); m.put(x, 4, "r")                       # la parete nord
    for y in range(4, 45):                                       # fianchi irregolari della montagna
        for x in (3, 4, 43, 44):
            if m.r.random() < (0.75 if x in (3, 44) else 0.3) and m.get(x, y) == ".":
                m.put(x, y, "T" if m.r.random() < 0.6 else "B")
    m.fill(3, 45, 44, 45, "T"); m.scatter("B", 12, "T", y0=45)

    def tent(x, y, door="D"):
        m.rows(x, y, "[@]", "/" + door + "\\")
        return x + 1, y + 1

    S = lambda pts, w=1: m.road(pts, ":", w=w, only=".,`*TB")
    # ---- terrazza bassa: cancello nella palizzata a ovest, locanda (tenda della mensa), slitte e provviste
    m.fill(7, 35, 7, 44, "v", only=".TB"); m.put(7, 39, "("); m.put(7, 40, "."); m.put(7, 41, ")")
    m.rows(8, 37, "Y", "t"); m.rows(8, 42, "Y", "t")
    m.put(2, 40, "E"); m.fill(0, 40, 1, 40, "l"); S([(3, 40), (37, 40)])
    hx, hy = tent(14, 36, "H"); S([(hx, hy + 1), (hx, 39)])
    tent(22, 36); tent(27, 42 - 6)
    m.rows(18, 42, "cc w"); m.rows(11, 43, "ww"); m.rows(31, 42, "s s"); m.put(13, 38, "i"); m.put(17, 38, "i")
    m.rows(39, 37, "wws", "c  "); m.put(41, 42, "i")
    m.fill(36, 30, 37, 39, "d", only="RWr.:")                   # scale verso la terrazza media
    # ---- terrazza media: il falo', fabbro, alchimista, tende, il tavolato del portale fra le pietre
    m.blob(22.5, 24.5, 4.6, 3.4, ":", only=".")
    m.rows(22, 24, "12", "34"); m.rows(21, 24, "~", "~"); m.rows(24, 24, "~", "~"); m.rows(22, 26, "~~")
    sx, sy = tent(30, 21, "S"); m.put(33, 22, "5"); S([(sx, sy + 1), (sx, 24), (27, 24)])
    ax, ay = tent(12, 21, "L"); m.put(11, 22, "7"); S([(ax, ay + 1), (ax, 24), (18, 24)])
    tent(17, 27); tent(27, 27)
    m.put(19, 22, "i"); m.put(26, 22, "i"); m.rows(15, 25, "s"); m.rows(35, 24, "ww")
    m.fill(40, 23, 42, 26, "+"); m.put(41, 24, "P")
    for x, y in ((39, 22), (43, 22), (39, 27), (43, 27)):
        m.put(x, y, "B")
    S([(36, 29), (25, 29), (25, 28)][:2]); S([(25, 29), (25, 27)][:0] or [(23, 29), (23, 28)])
    S([(37, 29), (41, 29), (41, 27)]); S([(18, 25), (9, 25), (9, 22)])
    m.fill(8, 14, 9, 21, "d", only="RWr.:")                     # scale verso la terrazza alta
    m.rows(6, 20, "Y", "t"); m.rows(11, 19, "A")
    # ---- terrazza alta: tende del comando con gli stendardi, tumuli, la grotta nella parete nord, il passo a nord-ovest
    S([(8, 13), (8, 11), (33, 11), (33, 5)]); m.put(33, 3, ">"); m.put(33, 4, ":")
    tent(15, 7); tent(19, 7); m.rows(14, 8, "A"); m.rows(22, 8, "A"); S([(16, 9), (16, 10)]); S([(20, 9), (20, 10)])
    m.rows(31, 5, "i"); m.rows(35, 5, "i")
    for x in (37, 39, 41):
        for y in (7, 9, 12):
            m.put(x, y, "o")
    m.rows(26, 6, "Y", "t")
    S([(8, 11), (5, 11), (5, 5)], w=1); m.fill(5, 0, 6, 10, ":"); m.put(5, 0, "="); m.put(6, 0, "="); m.fill(4, 5, 4, 9, "B"); m.fill(7, 5, 7, 9, "T")
    m.put(4, 4, "l"); m.put(7, 4, "r"); m.put(4, 3, "l"); m.put(7, 3, "W")
    # ---- alberi, massi, cumuli di neve, orme
    m.scatter("T", 34, ".", far=":d~SLH>EP=+", dist=1); m.scatter("B", 22, ".", far=":d~SLH>EP=+")
    m.scatter("*", 60, "."); m.scatter(",", 70, ".", near=":"); m.scatter("`", 40, ".")
    m.scatter("T", 60, "l", far=".:d=", dist=1)
    return m.finish(lambda c: "B", keep=":d+")


# ---------------------------------------------------------------------------------------------------- 4: Ruin's Gate
def ruinsgate():
    m = Map(4, ".")
    C = 23.5
    dist = lambda x, y: ((x - C) ** 2 + (y - C) ** 2) ** 0.5
    # fuori dalle mura: alberi bruciati e macerie (solidi)
    for y in range(H):
        for x in range(W):
            if x < 2 or x > 45 or y < 2 or y > 45:
                m.put(x, y, "T" if m.r.random() < 0.7 else "B")
    # il cratere al centro (orlo irregolare), l'anello di strada attorno, i quattro raggi
    pit = {(x, y) for y in range(H) for x in range(W) if dist(x, y) <= 6.2 + m.r.uniform(-0.5, 0.5)}
    pit = {p for p in pit if sum(((p[0] + dx, p[1] + dy) in pit) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 2}
    for (x, y) in pit:
        c = "%"
        if (x - 1, y) not in pit: c = "("
        elif (x + 1, y) not in pit: c = ")"
        elif (x, y - 1) not in pit: c = "t"
        elif (x, y + 1) not in pit: c = "Y"
        m.put(x, y, c)
    for y in range(H):
        for x in range(W):
            if 8.7 <= dist(x, y) <= 10.6:
                m.put(x, y, ":")
    m.fill(23, 34, 24, 45, ":"); m.put(23, 45, "E"); m.put(24, 45, "T"); m.fill(23, 46, 24, 47, "T")
    m.fill(23, 6, 23, 13, ":"); m.fill(24, 9, 24, 13, ":"); m.fill(22, 9, 22, 13, ":")
    m.fill(4, 23, 13, 24, ":"); m.fill(34, 23, 43, 24, ":")
    # la discesa nel cratere (uscita del capitolo): una scala di tavole dall'anello all'orlo sud
    ys = max(y for (x, y) in pit if x in (23, 24))
    m.fill(23, ys + 1, 24, 32, "x"); m.put(23, ys, "="); m.put(24, ys, "=")
    # il corpo di guardia a nord: mura, due torri, la saracinesca delle segrete
    m.fill(3, 3, 44, 3, "R"); m.fill(3, 4, 44, 5, "W")
    for x0 in (20, 24):
        m.fill(x0, 1, x0 + 2, 1, "A"); m.fill(x0, 2, x0 + 2, 5, "W"); m.put(x0 + 1, 3, "o")
    m.put(23, 5, ">"); m.put(23, 4, "W"); m.put(23, 3, "R"); m.put(23, 2, "W")
    for x0, x1 in ((8, 10), (15, 16), (33, 36), (41, 42)):                     # brecce
        m.fill(x0, 3, x1, 5, "."); m.put(x0 - 1, 4, "]"); m.put(x1 + 1, 4, "["); m.put(x0 - 1, 5, "]"); m.put(x1 + 1, 5, "[")
        m.put(x0 - 1, 3, "."); m.put(x1 + 1, 3, ".")
    # resti delle mura sugli altri lati
    for (x0, y0, x1, y1) in ((3, 8, 3, 14), (3, 30, 3, 38), (44, 9, 44, 17), (44, 28, 44, 33), (6, 44, 14, 44), (30, 44, 40, 44)):
        m.fill(x0, y0, x1, y1, "W")
        if y0 == y1:
            m.fill(x0, y0 - 1, x1, y0 - 1, "R"); m.put(x0, y0, "["); m.put(x1, y0, "]")

    def ruin(x, y, w, door="D", sign=None):
        """casa sventrata larga w: resti del tetto, parete con finestre vuote, parete con la porta al centro"""
        mid = x + w // 2
        for i in range(w):
            m.put(x + i, y, m.r.choice("rrl."))
            m.put(x + i, y + 1, "o" if i in (1, w - 2) else "W")
            m.put(x + i, y + 2, "W")
        m.put(x, y + 1, "["); m.put(x + w - 1, y + 1, "]")
        m.put(mid, y + 2, door)
        if sign:
            m.put(mid - 1, y + 2, sign)
        return mid, y + 2

    S = lambda pts: m.road(pts, ":", only=".,`*TB")
    # nord-ovest: la fucina
    sx, sy = ruin(8, 9, 7, "S", "5"); S([(sx, sy + 1), (sx, 16), (16, 16)]); m.put(7, 12, "i"); m.put(15, 12, "i")
    ruin(5, 16, 5); m.put(13, 14, "s")
    # nord-est: la torre spezzata dell'alchimista e il colonnato
    m.rows(35, 8, "AAA", "WoW", "WWW", "WLW"); m.put(34, 11, "7"); S([(36, 12), (36, 16), (31, 16)])
    for x in (29, 32, 39, 42):
        m.rows(x, 13, "/", "\\")
    m.rows(39, 17, "@"); m.rows(30, 9, "@"); ruin(38, 18, 5)
    # sud-ovest: la taverna (locanda nella cantina), la forca, il carro
    hx, hy = ruin(6, 30, 9, "H"); S([(hx, hy + 1), (hx, 35), (17, 35), (17, 32)])
    m.put(5, 33, "i"); m.put(15, 33, "i"); m.rows(8, 38, "w"); m.rows(14, 38, "s"); ruin(5, 39, 5)
    # sud-est: l'angelo che piange dentro la cancellata, il pavimento della cappella con il portale
    m.fill(32, 31, 37, 31, "|"); m.fill(32, 32, 32, 36, "v"); m.fill(37, 32, 37, 36, "v"); m.fill(32, 37, 33, 37, "|"); m.fill(36, 37, 37, 37, "|")
    m.fill(33, 32, 36, 36, "+"); m.rows(34, 32, "12", "34", "~~")
    S([(34, 37), (34, 38)]); m.fill(34, 37, 35, 38, ":"); S([(33, 39), (31, 39), (31, 31)][:2]); S([(31, 39), (31, 33)])
    m.fill(37, 39, 42, 42, "+"); m.put(39, 40, "P"); S([(36, 39), (35, 39)]); m.put(36, 40, ":")
    for x, y in ((37, 38), (42, 38)):
        m.rows(x, y - 1, "/", "\\")
    m.rows(40, 43, "@"); m.rows(28, 41, "@")
    # macerie, alberi bruciati, ossa, braci
    keep = ":x=EPSLH>~+"
    m.scatter("T", 46, ".", far=keep); m.scatter("B", 60, ".", far=keep); m.scatter("@", 8, ".", far=keep)
    m.scatter("*", 40, "."); m.scatter(",", 90, "."); m.scatter("`", 80, ".")
    m.scatter("i", 6, ".", near=":", far="SLH")
    return m.finish(lambda c: "B", keep=":x+")


# ------------------------------------------------------------------------------------------ 5: The City of the Abyss
def abysscity():
    m = Map(5, "%")
    isl = [(24, 41, 5.2, 3.2), (24, 25, 6.6, 5.2), (9, 25, 5.6, 4.6), (9, 10, 5.6, 4.6), (25, 8, 7.4, 4.4),
           (39, 24, 5.6, 4.6), (39, 39, 5.4, 3.8), (40, 9, 4.6, 3.6)]
    for cx, cy, rx, ry in isl:
        m.blob(cx, cy, rx, ry, ".", jag=0.12)
    # gli orli delle isole: sotto la roccia che pende, ai lati la parete, sopra il bordo
    floor = {(x, y) for y in range(H) for x in range(W) if m.g[y][x] == "."}
    for y in range(H):
        for x in range(W):
            if m.g[y][x] != "%":
                continue
            if (x, y - 1) in floor: m.put(x, y, "t" if (x * 7 + y) % 3 else "Y")
            elif (x + 1, y) in floor: m.put(x, y, "[")
            elif (x - 1, y) in floor: m.put(x, y, "]")
            elif (x, y + 1) in floor: m.put(x, y, "|")
    for cx, cy, rx, ry in isl:                                  # catene che pendono sotto le isole
        for dx in (-2, 1):
            x, y = int(cx) + dx, int(cy + ry) + 2
            if m.get(x, y) == "%" and m.get(x, y - 1) in "tY":
                m.put(x, y, "v")

    # ponti di luce (: est-ovest, d nord-sud) fra le isole, da centro a centro: coprono solo vuoto e orli; un disco di
    # pietra a meta' dei ponti lunghi
    B = lambda pts: m.road(pts, ":", cv="d", only="%|[]tYv")
    B([(24, 41), (24, 25)]); B([(9, 25), (24, 25)]); B([(24, 25), (39, 25)]); B([(9, 10), (9, 25)]); m.put(9, 17, "x")
    B([(9, 10), (25, 10)]); B([(24, 8), (24, 25)]); m.put(24, 16, "x"); B([(39, 24), (39, 39)]); m.put(39, 32, "x")
    B([(25, 8), (40, 8)]); B([(40, 9), (40, 24)]); m.put(40, 16, "x")
    m.put(16, 41, "E"); B([(17, 41), (24, 41)]); B([(40, 9), (44, 9)]); m.put(45, 9, "="); m.put(46, 9, "="); m.put(47, 9, "%")

    def dome(x, y, door="D"):
        m.rows(x, y, "/@\\", "W" + door + "R")
        return x + 1, y + 1

    # centro: il cuore dell'Abisso sul mosaico
    m.fill(21, 22, 26, 27, "+"); m.rows(23, 24, "12", "34"); m.rows(23, 23, "~~"); m.rows(23, 26, "~~")
    for x, y in ((20, 22), (27, 22), (20, 27), (27, 27)):
        m.put(x, y, "i")
    # ovest: il fabbro; nord-ovest: la locanda; est: l'alchimista
    dome(8, 23, "S"); m.put(11, 24, "5"); m.put(6, 26, "w"); m.put(12, 27, "T")
    dome(8, 8, "H"); m.put(6, 10, "i"); m.put(12, 10, "i"); dome(4, 10)
    dome(38, 22, "L"); m.put(37, 23, "7"); m.put(42, 25, "s"); m.put(36, 26, "T")
    # nord: la Bocca fra gli obelischi; nord-est: l'isola dell'uscita (sigillata); sud-est: il portale
    m.rows(24, 5, "r>l"); m.rows(22, 5, "A", "o"); m.rows(28, 5, "A", "o"); m.rows(20, 7, "A", "o"); m.rows(30, 7, "A", "o")
    m.put(25, 10, "s"); m.put(21, 10, "w"); m.put(29, 10, "w")
    m.rows(38, 7, "A", "o"); m.rows(42, 7, "A", "o"); m.put(40, 11, "s")
    m.fill(38, 38, 40, 40, "+"); m.put(39, 38, "P"); m.put(36, 39, "i"); m.put(42, 39, "i"); m.put(37, 41, "T")
    # sud: l'isola dell'arrivo
    m.put(21, 42, "w"); m.put(27, 42, "w"); m.put(24, 43, "T")
    # pezzi di citta' alla deriva
    for x, y in ((16, 33), (32, 16), (5, 38), (45, 31), (16, 3), (31, 44)):
        m.rows(x, y, "cc", "c")
    keep = ":dx=EPSLH>~+"
    m.scatter("T", 14, ".", far=keep + "/@\\WR"); m.scatter("B", 22, ".", far=keep)
    m.scatter("*", 26, "."); m.scatter(",", 34, "."); m.scatter("`", 26, ".")
    m.scatter("(", 150, "%"); m.scatter(")", 16, "%", far=".:d|[]tY"); m.scatter("c", 26, "%", far=":d")
    return m.finish(lambda c: "B", keep=":dx+")


VILLAGES = {
    2: ("Blackwater Mill, palafitte su un lago nero", [
        "Niente piazza e niente fiume: il villaggio sta SULL'ACQUA. Piattaforme di assi su pali (i pali si vedono sotto il",
        "bordo sud) unite da passerelle (: est-ovest, d nord-sud). Centro: la campana degli annegati (cura: i moccoli ~).",
        "Nord-ovest il fabbro, ovest l'alchimista, sud-est la locanda, due capanne di pescatori. Nord-est, su un isolotto di",
        "fango, il mulino con la ruota: la botola della sua cantina allagata (>) e' l'ingresso del sotterraneo. Ingresso del",
        "villaggio dalla riva a sud-ovest; uscita in fondo al pontile est (il traghetto); portale sulla piattaforma a sud-est."], blackwater),
    3: ("The Last Camp, un campo di guerra su tre terrazze nella neve", [
        "Niente acqua e niente case: tre terrazze nella montagna, separate da pareti di roccia (R orlo, W parete, r piede) e",
        "unite da scale di legno (d). Bassa (sud): cancello nella palizzata a ovest con le torri (Y sopra t), la tenda della",
        "mensa (locanda), slitte e provviste; scale a est. Media: il grande falo' (cura: i tronchi ~ attorno), fabbro e",
        "alchimista (tende 3x2: [@] sopra, / porta \\ sotto), tavolato del portale fra quattro massi; scale a ovest. Alta: tende",
        "del comando con gli stendardi (A), tumuli dei caduti (o), la bocca della grotta (>) nella parete nord: l'ingresso del",
        "sotterraneo. Ingresso del villaggio a ovest (terrazza bassa); uscita dal passo a nord-ovest (terrazza alta)."], lastcamp),
    4: ("Ruin's Gate, la citta' in rovina attorno al cratere", [
        "Niente fiume e niente fontana: al centro un cratere (% buio con le vene di brace, orli ( ) t Y), attorno la strada ad",
        "anello e quattro raggi. Nord: il corpo di guardia con le due torri e la saracinesca delle segrete (>): l'ingresso del",
        "sotterraneo; mura con le brecce. Nord-ovest la fucina, nord-est la torre spezzata dell'alchimista e il colonnato",
        "(/ sopra \\, @ colonna caduta), sud-ovest la taverna (locanda), la forca (w) e il carro. Sud-est l'angelo che piange",
        "dentro la cancellata (cura: le candele ~) e il pavimento della cappella con il portale. Ingresso del villaggio a sud;",
        "l'uscita del capitolo e' la scala di tavole (x) che scende nel cratere dal lato sud."], ruinsgate),
    5: ("The City of the Abyss, isole sospese nel vuoto (prototipo)", [
        "Niente terreno continuo: isole di pietra nel vuoto (% ( ) = vuoto, stelle, nebulose), con gli orli (| sopra, [ ] ai",
        "lati, t Y sotto) e unite da ponti di luce (: est-ovest, d nord-sud, x disco di pietra). Sud: l'isola dell'arrivo (si",
        "arriva da un ponte che viene dal nulla). Centro: il cuore dell'Abisso sul mosaico (cura: le rune ~). Ovest il fabbro,",
        "nord-ovest la locanda, est l'alchimista (case a cupola 3x2: /@\\ sopra, W porta R sotto). Nord: la Bocca (r > l) fra",
        "gli obelischi (A sopra o): l'ingresso del sotterraneo. Sud-est il portale. Nord-est l'isola dell'uscita: le due",
        "caselle = ci sono (formato del file) ma non si aprono mai. Nel vuoto, pezzi di citta' alla deriva (c)."], abysscity),
}

if __name__ == "__main__":
    for n in [int(a) for a in sys.argv[1:]] or sorted(VILLAGES):
        t, notes, fn = VILLAGES[n]
        write(n, t, notes, fn())
