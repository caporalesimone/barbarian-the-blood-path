#!/usr/bin/env python3
"""Brani del gioco come file .sid (PSID), uno per brano (14/11, richiesta del committente): si ascoltano con il player della
pagina di controllo di Lab64 (sid.html, jsSID), con VICE vsid o con qualunque player SID.

Per ogni brano di tools/build/songs.py: un programma a $1000 con il player vero del gioco (src/common/sid_player.inc, assemblato
con 64tass come nel gioco) e i dati del brano (out/work/snd/<nome>.bin, da tools/build/gen_music.py): init a $1000 (azzera le
variabili del player in $C000 e avvia il brano), play a $1003 (sp_play, una volta per fotogramma). Intestazione PSID scritta da
../lab64/py/psid.py. Uscite: out/work/sid/<nome>.sid (i nomi di songs.py hanno gia' il numero: 00_tavern.sid, ...)."""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LAB64 = os.environ.get("LAB64") or os.path.normpath(os.path.join(ROOT, "..", "lab64"))
sys.path[:0] = [HERE, os.path.join(LAB64, "py")]
import songs  # noqa: E402
TITLES = songs.TITLES
from psid import write_psid  # noqa: E402

SND = os.path.join(ROOT, "out", "work", "snd")
OUT = os.path.join(ROOT, "out", "work", "sid")
TMP = os.path.join(ROOT, "out", "work", "sid_build")
WRAP = """; generato da tools/build/gen_sid.py: brano {name} come .sid
SP_VARS = $c000
SP_V0   = 7                     ; come nel gioco e nel jukebox: lead sulla voce 2, accordi sulla 1, basso sulla 3
SP_V1   = 0
SP_V2   = 14
        * = $1000
        jmp init
        jmp sp_play
init    lda #0                  ; variabili del player a zero (sp_mute, sp_once...), poi il brano
        ldx #0
-       sta SP_VARS,x
        inx
        cpx #<SP_VSIZE
        bne -
        lda #15
        sta $d418
        lda #<song
        sta sp_bl
        lda #>song
        sta sp_bh
        jmp sp_start
        .include "sid_player.inc"
song    .binary "{bin}"
"""


def main():
    os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".sid"):
            os.remove(os.path.join(OUT, f))
    ver = subprocess.run([sys.executable, os.path.join(HERE, "gen_version.py"), "--print", "version"], capture_output=True,
                         text=True, check=True).stdout.strip()
    n = 0
    for name in songs.SONGS:
        asm, prg = os.path.join(TMP, name + ".asm"), os.path.join(TMP, name + ".prg")
        open(asm, "w").write(WRAP.format(name=name, bin="../snd/%s.bin" % name))   # relativo al .asm (out/work/sid_build/)
        subprocess.run(["64tass", "-a", "-q", "-I", os.path.join(ROOT, "src", "common"), "-I", os.path.join(ROOT, "out", "work"),
                        asm, "-o", prg], check=True)
        title = TITLES.get(name, name)
        write_psid(os.path.join(OUT, name + ".sid"), open(prg, "rb").read(), 0x1000, 0x1003, name=title,
                   author="Barbarian: The Blood Path", released="2026 Simone Caporale (v%s)" % ver)
        n += 1
    print("gen_sid: %d brani in %s" % (n, os.path.relpath(OUT, ROOT)))


if __name__ == "__main__":
    main()
