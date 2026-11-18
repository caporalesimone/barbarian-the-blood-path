#!/usr/bin/env python3
"""(18/11, revisione dei file del disco, docs/wiki/FastLoader.md 7.3) Code dei file TWNc e GFXn: ogni file che il gioco legge
cambiando luogo porta in fondo i dati che servono subito dopo, cosi' il gioco non cerca un altro file nella directory (una
ricerca costa 0,1-1,4 s, leggere un blocco ~65 ms). L'ultimo byte del file e' il segno (src/game/disk.asm gfx_tail):
  0..SND_N-1  il brano (dati del file SNDn senza indirizzo, snd_llo/hi byte) sta subito prima del segno;
  $80         la mappa del piano del boss (file BOSSCHc senza indirizzo) comincia a GFX_DUN_END, subito dopo il tema.
Code: TWNc = brano del villaggio (snd_town_c), GFX(2c-1) = brano dei piani del capitolo (snd_lvl_c), GFX(2c) per c = 1-3 = mappa
del boss, GFX(2*CHAPTERS) = brano del boss finale (SND_BOSS). Scrive out/work/bundle/twnC.prg e gfxN.prg (quelli che vanno sul
disco, tools/build/mkdisk.sh); i file di partenza in out/work e out/work/gfx restano come sono (atlante, strumenti).
I file SNDn restano sul disco (JUKEBOX, LOBBY e riserva); i BOSSCHc no (tools/build/mkdisk.sh)."""
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

    gfx_end = int(re.search(r"^GFX_DUN_END\s*=\s*\$([0-9a-f]+)", open(os.path.join(W, "game.lbl")).read(), re.M | re.I).group(1), 16)
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
        if n % 2:
            d += song(lvl[n // 2]); rep.append("gfx%d+snd%d" % (n, lvl[n // 2]))
        elif n < ngfx:
            m = rd("bossch%d.prg" % (n // 2))[2:]
            assert len(m) <= 0xFD00 - gfx_end - 1, "bossch%d troppo lunga per la coda" % (n // 2)
            d += m + b"\x80"; rep.append("gfx%d+bossch%d" % (n, n // 2))
        else:
            d += song(boss); rep.append("gfx%d+snd%d" % (n, boss))
        assert a + len(d) - 2 <= 0xFD00, "gfx%d: la coda arriva oltre $FD00 (FMAP)" % n
        open(os.path.join(OUT, "gfx%d.prg" % n), "wb").write(d)
    print("bundle: " + " ".join(rep))


if __name__ == "__main__":
    main()
