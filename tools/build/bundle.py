#!/usr/bin/env python3
"""(18/11, revisione dei file del disco, docs/wiki/FastLoader.md 7.3) Code dei file TWNc e GFXn: ogni file che il gioco legge
cambiando luogo porta in fondo i dati che servono subito dopo, cosi' il gioco non cerca un altro file nella directory (una
ricerca costa 0,1-1,4 s, leggere un blocco ~65 ms). L'ultimo byte del file e' il segno (src/game/disk.asm gfx_tail):
  0..SND_N-1  il brano (dati del file SNDn senza indirizzo, snd_llo/hi byte) sta subito prima del segno;
  $80         la mappa del piano del boss (file BOSSCHc senza indirizzo) comincia a GFX_DUN_END, subito dopo il tema.
(19/11) Nel file del tema dei piani di un capitolo a cittadella (data/chapters.yaml map.style citadel, oggi GFX7) fra il tema e
il brano c'e' il codice della cittadella (out/work/gen_cit.bin, src/game/gen_citadel.asm), assemblato per GFX_DUN_END: il brano
si trova contando dal segno all'indietro, quindi i byte in mezzo non lo spostano.
Code: TWNc = brano del villaggio (snd_town_c), GFX(2c-1) = brano dei piani del capitolo (snd_lvl_c), GFX(2c) per c = 1-3 = mappa
del boss, GFX(2*CHAPTERS) = brano del boss finale (SND_BOSS). Scrive out/work/bundle/twnC.prg e gfxN.prg (quelli che vanno sul
disco, tools/build/mkdisk.sh); i file di partenza in out/work e out/work/gfx restano come sono (atlante, strumenti).
I file SNDn restano sul disco (JUKEBOX, LOBBY e riserva); i BOSSCHc no (tools/build/mkdisk.sh).
(19/11) CODICE DEL PIANO (src/game/theme.asm, src/game/ovl_*.asm, assemblato a OVP_AT = $C900): nei file di OVL subito dopo il
tema, a GFX_DUN_END, 2 byte di lunghezza e il codice; il resto della coda (mappa del boss, brano) dopo; segno | $40. gfx_tail
lo copia a OVP_AT. Mai nei file con il codice della cittadella (assemblato proprio a GFX_DUN_END)."""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W = os.path.join(ROOT, "out", "work")
OUT = os.path.join(W, "bundle")


def rd(p):
    return open(os.path.join(W, p), "rb").read()


def main():
    os.makedirs(OUT, exist_ok=True)
    tab = open(os.path.join(W, "music_tab.inc")).read()
    arr = lambda n: [int(v) for v in re.search(r"^%s\s+\.byte\s+([\d, ]+)" % n, tab, re.M).group(1).split(",")]
    num = lambda n: int(re.search(r"^%s\s*=\s*(\d+)" % n, tab, re.M).group(1))
    town, lvl, boss, nsnd = arr("snd_town_c"), arr("snd_lvl_c"), num("SND_BOSS"), num("SND_N")
    hi = [int(v) for v in re.search(r"^snd_lhi\s+\.byte\s+(.+)$", tab, re.M).group(1).replace(">", "").split(",")]
    lo = [int(v) for v in re.search(r"^snd_llo\s+\.byte\s+(.+)$", tab, re.M).group(1).replace("<", "").split(",")]
    assert lo == hi and len(lo) == nsnd, "music_tab.inc: snd_llo/snd_lhi"

    def song(k):
        d = rd("snd/snd%d.prg" % k)[2:]
        assert len(d) == lo[k], "snd%d: %d B, snd_llo %d" % (k, len(d), lo[k])
        return d + bytes([k])

    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
    import chapters_db
    cit = {2 * ch["id"] - 1 for ch in chapters_db.load()["chapters"] if (ch.get("map") or {}).get("style") == "citadel"}
    citcode = rd("gen_cit.bin")
    gfx_end = int(re.search(r"^GFX_DUN_END\s*=\s*\$([0-9a-f]+)", open(os.path.join(W, "game.lbl")).read(), re.M | re.I).group(1), 16)
    ovl = {2 * len(lvl): "ovl_final.bin"}             # (19/11) GFX8: sala del trono
    for c in range(1, len(lvl)):                      # GFX2, GFX4, GFX6: meccaniche dei boss dei capitoli 1-3 (ovl_bossC)
        if os.path.exists(os.path.join(W, "ovl_boss%d.bin" % c)):
            ovl[2 * c] = "ovl_boss%d.bin" % c
    assert not set(ovl) & cit, "codice del piano e cittadella nello stesso file"
    rep = []
    for c, k in enumerate(town, 1):
        f = "twn%d.prg" % c
        d = rd(f) + song(k)
        open(os.path.join(OUT, f), "wb").write(d)
        rep.append("%s+snd%d" % (f[:-4], k))
    ngfx = 2 * len(lvl)
    for n in range(1, ngfx + 1):
        d = rd("gfx/gfx%d.prg" % n)
        a = d[0] | d[1] << 8
        assert a + len(d) - 2 == gfx_end, "gfx%d: non finisce a GFX_DUN_END" % n
        flag = 0
        if n in ovl:
            oc = rd(ovl[n])
            d += bytes([len(oc) & 255, len(oc) >> 8]) + oc; flag = 0x40
            rep.append("gfx%d+%s(%d B)" % (n, ovl[n][:-4], len(oc)))
        if n % 2:
            if n in cit:
                d += citcode; rep.append("gfx%d+citadel(%d B)" % (n, len(citcode)))
            d += song(lvl[n // 2]); rep.append("gfx%d+snd%d" % (n, lvl[n // 2]))
        elif n < ngfx:
            m = rd("bossch%d.prg" % (n // 2))[2:]
            assert len(m) <= 0xFD00 - gfx_end - 1, "bossch%d troppo lunga per la coda" % (n // 2)
            d += m + b"\x80"; rep.append("gfx%d+bossch%d" % (n, n // 2))
        else:
            d += song(boss); rep.append("gfx%d+snd%d" % (n, boss))
        if flag:
            d = d[:-1] + bytes([d[-1] | flag])
        assert a + len(d) - 2 <= 0xFD00, "gfx%d: la coda arriva oltre $FD00 (FMAP)" % n
        open(os.path.join(OUT, "gfx%d.prg" % n), "wb").write(d)
    print("bundle: " + " ".join(rep))


if __name__ == "__main__":
    main()
