#!/usr/bin/env python3
"""Brani SID del gioco (dati): li compila tools/build/gen_music.py nel formato a pattern di src/common/sid_player.inc.

Formato delle voci: "NOTA:durata" in tick (un tick = `speed` fotogrammi), "-" = pausa, "*NOTA" = seconda forma
d'onda e secondo ADSR dello strumento (rullante sulla voce basso+batteria, eco morbida sul lead).
Voce 0 melodia, 1 accordi (arpeggio), 2 basso + batteria. Nel gioco la voce 1 del SID e' condivisa con gli effetti
sonori: mentre suona un effetto la voce 1 del brano tace (il brano continua sulle altre due).
Elenchi del gioco (PLAYLIST in fondo): titolo, villaggio, livelli, boss finale, combattimento."""

NOTES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def n(s):
    if s == "-":
        return 0
    w2 = s.startswith("*")
    s = s.lstrip("*")
    return (NOTES[s[:-1]] + 12 * int(s[-1]) + 1) | (0x80 if w2 else 0)


def seq(txt):
    out = []
    for tok in txt.split():
        name, ln = tok.split(":")
        out += [n(name), int(ln)]
    return out + [0xFF]


def freq_table():                   # indice 0 = pausa, 1 = C0 (come n()); fino a B7 + 12 (arpeggi)
    return [0] + [min(65535, int(round(440.0 * 2 ** ((i - 57) / 12.0) * 16777216 / 985248))) for i in range(107)]


def bars(*parts):
    return " ".join(parts)


def rep(s, k):
    return " ".join([s] * k)


# ------------------------------------------------------------------ strumenti
# wave, wave2, ad, sr, pw, pwd (delta per fotogramma, con segno), pwmin, pwmax (byte alto), vd, vw, arp, slide, gcut
def ins(wave, ad, sr, pw=0x800, pwd=0, pwmin=1, pwmax=14, vd=0, vw=0, arp=0, slide=0, gcut=1, wave2=None, ad2=None, sr2=None):
    return dict(wave=wave, wave2=wave2 if wave2 is not None else wave, ad=ad, sr=sr, pw=pw, pwd=pwd, pwmin=pwmin,
                pwmax=pwmax, vd=vd, vw=vw, arp=arp, slide=slide, gcut=gcut,
                ad2=ad2 if ad2 is not None else ad, sr2=sr2 if sr2 is not None else sr)


LEAD = ins(0x41, 0x08, 0x9A, pw=0x600, pwd=12, pwmin=3, pwmax=12, vd=9, vw=9, gcut=2)
LEAD_SAW = ins(0x21, 0x06, 0xA9, vd=7, vw=10, gcut=2)
LEAD_TRI = ins(0x11, 0x0A, 0xAB, vd=12, vw=8, gcut=3)
CHORD = ins(0x41, 0x00, 0x68, pw=0x300, pwd=4, pwmin=2, pwmax=6, arp=1, gcut=2)
CHORD_TRI = ins(0x11, 0x02, 0x7A, arp=2, gcut=2)
BASSDRUM = ins(0x21, 0x00, 0xA8, wave2=0x81, gcut=2)          # dente di sega; *nota = rumore (rullante / charleston)
BASS_PULSE = ins(0x41, 0x00, 0xB8, pw=0x200, pwd=2, pwmin=1, pwmax=4, wave2=0x81, gcut=2)
ARPS = [[0, 0, 0, 0], [0, 7, 12, 7], [0, 3, 7, 12], [0, 4, 7, 12]]   # 0 nessuno, 1 quinta, 2 minore, 3 maggiore

# ------------------------------------------------------------------ brani (Re minore, 16-32 battute)
def bass_line(roots, pat="R2:2 *R2:2 R2:2 R3:2 *R2:2 R2:2 R3:2 *R2:2"):
    """basso + batteria: R = fondamentale; *R = colpo di rumore al posto della nota"""
    out = []
    for r in roots:
        out.append(pat.replace("R2", r + "2").replace("R3", r + "3"))
    return " ".join(out)


SONGS = {}

# 1. "Demon's Eye": lento e pesante, melodia che scende, accordi di quinta
SONGS["01_demons_eye"] = dict(
    speed=8, filt=(0x50, 0x30, 0x90, 1, 0x7F, 0x1F), ins=[LEAD, CHORD, BASSDRUM],
    v0=bars("D4:8 F4:4 E4:4   D4:6 C4:2 D4:8   A#3:8 D4:4 F4:4   E4:12 -:4",
            "D4:8 F4:4 A4:4   G4:6 F4:2 E4:8   F4:4 E4:4 D4:4 C4:4   D4:12 -:4",
            "A4:6 A#4:2 A4:4 G4:4   F4:8 E4:8   D4:6 E4:2 F4:4 G4:4   A4:12 -:4",
            "A#4:6 A4:2 G4:8   F4:6 E4:2 D4:8   C#4:8 E4:8   D4:16"),
    v1=bars(rep("D3:4 -:4 D3:4 -:4", 2), rep("A#2:4 -:4 A#2:4 -:4", 2), rep("D3:4 -:4 D3:4 -:4", 2), rep("A2:4 -:4 A2:4 -:4", 2),
            rep("D3:4 -:4 D3:4 -:4", 2), rep("F3:4 -:4 F3:4 -:4", 2), rep("G2:4 -:4 G2:4 -:4", 2), rep("A2:4 -:4 A2:4 -:4", 2)),
    v2=bass_line(["D", "D", "A#", "A#", "D", "D", "A", "A", "D", "D", "F", "F", "G", "G", "A", "A"]))

# 2. "Blood Path": marcia veloce, basso a ottave, melodia a salti
SONGS["02_blood_path"] = dict(
    speed=6, filt=(0x40, 0x28, 0xA0, 2, 0x8F, 0x1F), ins=[LEAD_SAW, CHORD, BASS_PULSE],
    v0=bars("D4:2 -:2 D4:2 F4:2 A4:4 G4:2 F4:2   E4:4 D4:2 E4:2 F4:8",
            "D4:2 -:2 D4:2 F4:2 A4:4 A#4:2 A4:2   G4:4 F4:2 E4:2 D4:8",
            "C4:2 -:2 C4:2 E4:2 G4:4 F4:2 E4:2   D4:4 C4:2 D4:2 E4:8",
            "A3:2 -:2 A3:2 C#4:2 E4:4 D4:2 C#4:2   A3:4 C#4:2 E4:2 A4:8",
            "D5:4 C5:2 A4:2 D5:4 C5:2 A4:2   A#4:4 A4:2 G4:2 F4:8",
            "G4:4 F4:2 D4:2 G4:4 F4:2 D4:2   E4:4 F4:2 G4:2 A4:8",
            "A#4:2 A4:2 G4:2 F4:2 E4:2 D4:2 C4:2 A#3:2   A3:4 C#4:4 E4:8",
            "D4:16 -:16"),
    v1=bars(rep("D3:2 -:2", 8), rep("A#2:2 -:2", 8), rep("C3:2 -:2", 8), rep("A2:2 -:2", 8),
            rep("D3:2 -:2", 8), rep("G2:2 -:2", 8), rep("A#2:2 -:2 A2:2 -:2", 4), rep("D3:2 -:2", 8)),
    v2=bass_line(["D", "D", "A#", "A#", "C", "C", "A", "A", "D", "D", "G", "G", "A#", "A", "D", "D"],
                 pat="R2:2 R3:2 *R2:2 R2:2 R3:2 R2:2 *R2:2 R3:2"))

# 3. "The Watcher": ritmo sincopato, tema ipnotico, accordi minori arpeggiati
SONGS["03_the_watcher"] = dict(
    speed=7, filt=(0x60, 0x38, 0x80, 1, 0x4F, 0x1F), ins=[LEAD, CHORD_TRI, BASSDRUM],
    v0=bars("-:16", "-:16",
            "D4:3 F4:3 A4:2 D4:3 F4:3 A4:2   G4:3 F4:3 E4:2 D4:8",
            "D4:3 F4:3 A4:2 D5:3 C5:3 A4:2   A#4:3 A4:3 G4:2 F4:8",
            "E4:3 G4:3 C5:2 E4:3 G4:3 C5:2   A#4:3 A4:3 G4:2 E4:8",
            "C#4:3 E4:3 A4:2 C#4:3 E4:3 A4:2   G4:3 F4:3 E4:2 A4:8",
            "D5:6 C5:2 A4:8   F5:6 E5:2 D5:8",
            "D5:6 A#4:2 F4:8   G4:4 A4:4 A#4:4 C5:4",
            "D5:3 C5:3 A#4:2 A4:3 G4:3 F4:2   E4:3 F4:3 E4:2 D4:8",
            "C#4:8 E4:8   A3:16"),
    v1=bars(rep("D3:16", 2), rep("A#2:16", 2), rep("C3:16", 2), rep("A2:16", 2), rep("D3:16", 2), rep("A#2:16", 2),
            rep("G2:16", 2), rep("A2:16", 2), rep("D3:16", 2)),
    v2=bass_line(["D", "D", "A#", "A#", "C", "C", "A", "A", "D", "D", "A#", "A#", "G", "G", "A", "A", "D", "D"],
                 pat="R2:3 *R2:1 R2:2 R2:2 *R2:2 R2:2 R3:2 *R2:2"))

# 4. "Iron Crown": tema eroico in minore, terzine di accordi, basso che cammina
SONGS["04_iron_crown"] = dict(
    speed=6, filt=(0x70, 0x40, 0xB0, 1, 0x6F, 0x1F), ins=[LEAD_TRI, CHORD, BASS_PULSE],
    v0=bars("D4:4 A4:4 F4:4 D4:4   E4:4 F4:4 G4:4 E4:4",
            "F4:4 C5:4 A4:4 F4:4   G4:4 A4:4 A#4:4 G4:4",
            "A4:4 D5:4 C5:4 A4:4   A#4:4 A4:4 G4:4 F4:4",
            "E4:4 G4:4 F4:4 E4:4   D4:8 -:8",
            "D5:6 D5:2 C5:4 A4:4   A#4:6 A#4:2 A4:4 G4:4",
            "F4:6 F4:2 G4:4 A4:4   A#4:4 C5:4 D5:8",
            "C5:4 A#4:4 A4:4 G4:4   F4:4 E4:4 D4:4 C#4:4",
            "D4:16 -:16"),
    v1=bars(rep("D3:4 -:2 D3:2 -:8", 2), rep("F3:4 -:2 F3:2 -:8", 2), rep("D3:4 -:2 D3:2 -:8", 2), rep("A2:4 -:2 A2:2 -:8", 2),
            rep("G2:4 -:2 G2:2 -:8", 2), rep("A#2:4 -:2 A#2:2 -:8", 2), rep("F3:4 -:2 F3:2 -:8", 1), rep("A2:4 -:2 A2:2 -:8", 1), rep("D3:4 -:2 D3:2 -:8", 2)),
    v2=bass_line(["D", "D", "F", "F", "D", "D", "A", "A", "G", "G", "A#", "A#", "F", "A", "D", "D"],
                 pat="R2:4 *R2:2 R2:2 R3:2 R2:2 *R2:2 R3:2"))

# 5. "Abyss Gate": molto lento e minaccioso, lead ampio con vibrato, basso pulsante, accordi lunghi
SONGS["05_abyss_gate"] = dict(
    speed=9, filt=(0x30, 0x20, 0x70, 1, 0x9F, 0x1F), ins=[LEAD, CHORD_TRI, BASSDRUM],
    v0=bars("-:16", "-:16", "D4:12 E4:4   F4:8 E4:8", "D4:12 C4:4   A#3:16",
            "A3:12 A#3:4   C4:8 D4:8", "E4:16   -:16",
            "F4:8 G4:8   A4:12 G4:4", "F4:8 E4:8   D4:12 -:4",
            "C#4:8 E4:8   A3:12 -:4", "D4:16 -:16"),
    v1=bars(rep("D3:16", 2), rep("D3:16", 2), rep("A#2:16", 2), rep("G2:16", 2), rep("A2:16", 2), rep("D3:16", 2), rep("A#2:16", 2),
            rep("A2:16", 2), rep("D3:16", 2)),
    v2=bass_line(["D", "D", "D", "D", "A#", "A#", "G", "G", "A", "A", "D", "D", "A#", "A#", "A", "A", "D", "D"],
                 pat="R2:4 *R2:4 R2:4 *R2:2 R2:2"))


# ================================================================== musiche del gioco: 2 VOCI
# Nel gioco la voce 1 del SID e' degli effetti sonori (src/game/music.asm): i brani del dungeon, del boss finale e del
# combattimento usano solo lead (voce 0 qui) e basso + batteria (voce 2); la voce 1 resta muta.
# Eco: su un solo canale, ogni nota lunga e' seguita da una ripetizione piu' morbida (bit 7: ADSR2 con sustain
# basso), come fa gia' src/game/music.asm ("nota eco").
def echo(txt, d=2):
    """ogni nota di durata L > d diventa nota:d + *nota:(L-d) (ripetizione morbida); pause e note corte restano"""
    out = []
    for tok in txt.split():
        name, ln = tok.split(":")
        ln = int(ln)
        if name == "-" or name.startswith("*") or ln <= d:
            out.append(tok)
        else:
            out.append("%s:%d *%s:%d" % (name, d, name, ln - d))
    return " ".join(out)


SILENT = ins(0x00, 0x00, 0x00)
LEAD_ECHO = ins(0x41, 0x06, 0x8A, pw=0x500, pwd=10, pwmin=3, pwmax=11, vd=6, vw=9, gcut=2, wave2=0x41, ad2=0x00, sr2=0x39)
LEAD_DARK = ins(0x21, 0x09, 0x9B, vd=5, vw=12, gcut=3, wave2=0x21, ad2=0x00, sr2=0x48)
LEAD_FAST = ins(0x41, 0x02, 0x7A, pw=0x400, pwd=20, pwmin=2, pwmax=13, vd=4, vw=5, gcut=1)
BASS_D = ins(0x21, 0x00, 0x99, wave2=0x81, ad2=0x00, sr2=0x95, gcut=2)         # saw + rumore (ADSR del rullante a parte)
BASS_P = ins(0x41, 0x00, 0xA9, pw=0x300, pwd=3, pwmin=1, pwmax=5, wave2=0x81, ad2=0x00, sr2=0x94, gcut=2)
BASS_KICK = ins(0x41, 0x00, 0xA9, pw=0x300, wave2=0x11, ad2=0x00, sr2=0x86, gcut=2, slide=-0x280)   # *nota con triangolo e glissato in giu' = cassa

REST16 = "-:16"


def two(v0, v2):
    return dict(v0=v0, v1=rep(REST16, 1), v2=v2)


def song2(speed, filt, lead, bass, v0, v2):
    d = dict(speed=speed, filt=filt, ins=[lead, SILENT, bass], v0=v0, v2=v2)
    L0 = sum(seq(v0)[1:-1:2]); L2 = sum(seq(v2)[1:-1:2])
    if L0 != L2:                     # la voce piu' corta si chiude con una pausa (da sistemare a mano nel brano scelto)
        if L0 < L2:
            v0 += " -:%d" % (L2 - L0)
        else:
            v2 += " -:%d" % (L0 - L2)
        L0 = max(L0, L2)
    d["v0"], d["v2"] = v0, v2
    d["v1"] = " ".join(["-:16"] * (L0 // 16)) if L0 % 16 == 0 else "-:%d" % L0
    return d


# ---- dungeon (5): cripte, paura, battaglie
SONGS["11_crypt_steps"] = song2(7, (0x48, 0x30, 0x78, 1, 0x4F, 0x1F), LEAD_ECHO, BASS_D,
    echo(bars("D4:4 -:4 F4:4 -:4   E4:4 -:4 D4:4 -:4", "A3:4 -:4 C4:4 -:4   A#3:8 A3:8",
              "D4:4 -:4 F4:4 -:4   G4:4 -:4 A4:4 -:4", "G4:4 F4:4 E4:4 C#4:4   D4:16",
              "F4:4 -:4 A4:4 -:4   G4:4 -:4 F4:4 -:4", "E4:4 -:4 G4:4 -:4   F4:8 E4:8",
              "D4:4 F4:4 A4:4 D5:4   C5:4 A#4:4 A4:4 G4:4", "F4:4 E4:4 D4:4 C#4:4   D4:16"), 3),
    bass_line(["D", "D", "A", "A", "D", "D", "A", "D", "F", "F", "C", "C", "D", "G", "A", "D"],
              pat="R2:4 *R2:4 R2:2 R2:2 *R2:4"))

SONGS["12_bone_halls"] = song2(6, (0x58, 0x38, 0x98, 2, 0x8F, 0x1F), LEAD_DARK, BASS_P,
    bars("D3:2 D4:2 D3:2 F4:2 D3:2 E4:2 D3:2 D4:2   C3:2 C4:2 C3:2 E4:2 C3:2 D4:2 C3:2 C4:2",
         "A#2:2 A#3:2 A#2:2 D4:2 A#2:2 C4:2 A#2:2 A#3:2   A2:2 A3:2 A2:2 C#4:2 A2:2 E4:2 A2:2 A3:2",
         "D4:6 F4:2 A4:8   G4:4 F4:4 E4:4 D4:4", "C4:6 E4:2 G4:8   F4:4 E4:4 D4:4 C4:4",
         "A#3:6 D4:2 F4:8   E4:4 D4:4 C4:4 A#3:4", "A3:4 C#4:4 E4:4 A4:4   G4:4 F4:4 E4:4 C#4:4",
         "D4:16 -:16"),
    bass_line(["D", "D", "C", "C", "A#", "A#", "A", "A", "D", "D", "C", "C", "A#", "A#", "A", "A", "D", "D"][:14],
              pat="R2:2 R2:2 *R2:2 R2:2 R3:2 R2:2 *R2:2 R2:2"))

SONGS["13_fear_below"] = song2(9, (0x30, 0x20, 0x60, 1, 0x7F, 0x1F), LEAD_ECHO, BASS_D,
    echo(bars("-:16", "D4:12 -:4   D#4:12 -:4", "D4:8 C4:8   A#3:12 -:4", "A3:8 A#3:8   A3:12 -:4",
              "F4:12 -:4   E4:12 -:4", "D4:8 F4:8   G4:4 F4:4 E4:4 D4:4", "C#4:12 E4:4   A3:16", "D4:16 -:16"), 4),
    bass_line(["D", "D", "D", "D", "D", "A#", "A", "A", "F", "F", "D", "G", "A", "A", "D", "D"],
              pat="R2:8 *R2:2 R2:2 *R2:4"))

SONGS["14_war_drums"] = song2(5, (0x60, 0x40, 0xB0, 3, 0x6F, 0x1F), LEAD_FAST, BASS_KICK,
    bars("D4:2 D4:2 -:2 D4:2 F4:2 -:2 D4:2 -:2   A3:2 A3:2 -:2 A3:2 C4:2 -:2 A3:2 -:2",
         "A#3:2 A#3:2 -:2 A#3:2 D4:2 -:2 A#3:2 -:2   A3:2 A3:2 -:2 C#4:2 E4:2 -:2 A3:2 -:2",
         "D4:4 F4:4 A4:4 D5:4   C5:4 A4:4 F4:4 D4:4", "A#3:4 D4:4 F4:4 A#4:4   A4:4 G4:4 F4:4 E4:4",
         "D4:2 D4:2 F4:2 D4:2 A4:2 D4:2 F4:2 D4:2   C4:2 C4:2 E4:2 C4:2 G4:2 C4:2 E4:2 C4:2",
         "A#3:2 A#3:2 D4:2 A#3:2 F4:2 A#3:2 D4:2 A#3:2   A3:2 C#4:2 E4:2 A4:2 E4:2 C#4:2 A3:2 -:2",
         "D4:16 -:16"),
    bass_line(["D", "D", "A", "A", "A#", "A#", "A", "A", "D", "D", "A#", "A#", "D", "D", "C", "C", "A#", "A#", "A", "A", "D", "D"][:14],
              pat="*R2:2 R2:2 R2:2 *R2:2 R2:2 *R2:2 R2:2 R2:2"))

SONGS["15_black_chant"] = song2(8, (0x40, 0x28, 0x70, 1, 0x4F, 0x1F), LEAD_DARK, BASS_D,
    echo(bars("D4:3 D4:3 D4:2 F4:3 E4:3 D4:2   C4:3 C4:3 C4:2 D4:3 C4:3 A#3:2",
              "A3:3 A3:3 A3:2 C4:3 A#3:3 A3:2   G3:3 G3:3 G3:2 A3:3 A#3:3 A3:2",
              "D4:3 D4:3 D4:2 F4:3 G4:3 A4:2   A#4:3 A4:3 G4:2 F4:3 E4:3 D4:2",
              "C#4:3 C#4:3 C#4:2 E4:3 D4:3 C#4:2   D4:8 -:8"), 2),
    bass_line(["D", "D", "C", "C", "A", "A", "G", "G", "D", "D", "A#", "A#", "A", "A", "D", "D"][:8],
              pat="R2:3 *R2:3 R2:2 R3:3 *R2:3 R2:2"))

# ---- boss finale (3): piu' cupo, rapido, ossessivo
SONGS["21_lord_of_ruin"] = song2(5, (0x50, 0x30, 0xA0, 2, 0x8F, 0x1F), LEAD_FAST, BASS_KICK,
    bars("D4:2 D#4:2 D4:2 C4:2 D4:2 D#4:2 D4:2 C4:2   A#3:2 B3:2 A#3:2 A3:2 A#3:2 B3:2 A#3:2 A3:2",
         "D4:2 D#4:2 D4:2 C4:2 D4:2 F4:2 D4:2 C4:2   G#3:2 A3:2 G#3:2 G3:2 A3:4 -:4",
         "D5:4 C#5:2 D5:2 A#4:4 A4:4   G4:4 F#4:2 G4:2 D#4:4 D4:4",
         "C#4:2 D4:2 D#4:2 E4:2 F4:2 F#4:2 G4:2 G#4:2   A4:8 -:8",
         "D4:16 -:16"),
    bass_line(["D", "D", "A#", "A#", "D", "D", "G#", "A", "D", "D", "G", "G", "C#", "A", "D", "D"][:10],
              pat="R2:2 *R2:2 R2:2 R2:2 *R2:2 R2:2 R2:2 *R2:2"))

SONGS["22_throne_of_ash"] = song2(6, (0x40, 0x28, 0x90, 2, 0x8F, 0x1F), LEAD_DARK, BASS_P,
    bars("D4:6 F4:2 D#4:8   C4:6 D#4:2 C4:8", "A#3:6 D4:2 A#3:8   A3:6 C#4:2 A3:8",
         "D4:4 F4:4 G#4:4 A4:4   A#4:4 A4:4 G4:4 F4:4", "E4:4 G4:4 A#4:4 C#5:4   D5:8 -:8",
         "D5:3 D5:3 D5:2 C5:3 A#4:3 A4:2   G#4:3 G#4:3 G#4:2 A4:3 A#4:3 A4:2",
         "G4:3 G4:3 G4:2 F4:3 E4:3 D4:2   C#4:8 D4:8",
         "D4:16 -:16"),
    bass_line(["D", "D", "C", "C", "A#", "A#", "A", "A", "D", "D", "A#", "A", "D", "D", "G#", "G#", "G", "C#", "D", "D"][:14],
              pat="R2:2 R2:2 *R2:2 R2:2 R3:2 R2:2 *R2:2 R3:2"))

SONGS["23_demon_awakes"] = song2(4, (0x60, 0x40, 0xB0, 4, 0x6F, 0x1F), LEAD_FAST, BASS_KICK,
    bars("D4:1 D4:1 D4:2 F4:1 F4:1 F4:2 D4:1 D4:1 D4:2 C4:2 D4:2   A#3:1 A#3:1 A#3:2 D4:1 D4:1 D4:2 A#3:1 A#3:1 A#3:2 A3:2 A#3:2",
         "A3:1 A3:1 A3:2 C#4:1 C#4:1 C#4:2 E4:1 E4:1 E4:2 A4:2 G4:2   F4:2 E4:2 D4:2 C#4:2 D4:8",
         "D5:4 D#5:4 D5:4 C5:4   A#4:4 A4:4 G#4:4 A4:4", "F4:4 F#4:4 G4:4 G#4:4   A4:8 A#4:8",
         "D4:16 -:16"),
    bass_line(["D", "D", "A#", "A#", "A", "A", "D", "D", "D", "D", "A#", "A", "F", "G", "A", "A", "D", "D"][:10],
              pat="R2:1 R2:1 *R2:2 R2:2 *R2:2 R2:1 R2:1 *R2:2 R2:2 *R2:2"))

# ---- combattimento (3): motivetti brevi (<= 10 s), bpm alto, ansia
SONGS["31_fight_1"] = song2(3, (0x60, 0x40, 0xA0, 4, 0x6F, 0x1F), LEAD_FAST, BASS_KICK,
    rep(bars("D4:2 D4:2 F4:2 D4:2 D#4:2 D4:2 C4:2 D4:2   D4:2 D4:2 F4:2 D4:2 A#3:2 A3:2 A#3:2 C4:2",
         "D4:2 D4:2 F4:2 D4:2 D#4:2 D4:2 C4:2 D4:2   G4:2 F4:2 E4:2 D4:2 C#4:2 D4:2 E4:2 C#4:2"), 2),
    bass_line(["D", "D", "D", "A#", "D", "D", "C", "A"], pat="R2:2 *R2:2 R2:2 *R2:2 R2:2 *R2:2 R2:2 *R2:2"))

SONGS["32_fight_2"] = song2(3, (0x50, 0x30, 0x90, 3, 0x8F, 0x1F), LEAD_DARK, BASS_P,
    rep(bars("D4:1 -:1 D4:1 -:1 D4:2 F4:2 D4:1 -:1 D4:1 -:1 E4:2 D4:2   C4:1 -:1 C4:1 -:1 C4:2 D#4:2 C4:1 -:1 C4:1 -:1 D4:2 C4:2",
         "A#3:1 -:1 A#3:1 -:1 A#3:2 D4:2 A#3:1 -:1 A#3:1 -:1 C4:2 A#3:2   A3:1 -:1 A3:1 -:1 A3:2 C#4:2 E4:2 D4:2 C#4:2 A3:2"), 2),
    bass_line(["D", "D", "C", "C", "A#", "A#", "A", "A"], pat="R2:2 *R2:2 R3:2 R2:2 *R2:2 R2:2 R3:2 *R2:2"))

SONGS["33_fight_3"] = song2(3, (0x70, 0x48, 0xB0, 5, 0x6F, 0x1F), LEAD_FAST, BASS_KICK,
    rep(bars("D5:1 D5:1 D5:2 A#4:1 A#4:1 A#4:2 A4:1 A4:1 A4:2 G4:2 F4:2   E4:1 E4:1 E4:2 F4:1 F4:1 F4:2 G4:2 A4:2 A#4:2 A4:2",
         "D5:1 D5:1 D5:2 A#4:1 A#4:1 A#4:2 A4:1 A4:1 A4:2 G4:2 F4:2   G4:2 A4:2 A#4:2 C5:2 C#5:4 D5:4"), 2),
    bass_line(["D", "D", "A#", "A", "D", "D", "A#", "A"], pat="*R2:1 R2:1 R2:2 *R2:2 R2:2 *R2:1 R2:1 R2:2 *R2:2 R2:2"))



# ---- villaggio: "Taverna dell'Alba" (A dorico, 6/8: un tick = un ottavo da 8 fotogrammi; dal vecchio gen_music.py)
LEAD_TAV = ins(0x11, 0x34, 0xC5, vd=8, vw=8, gcut=0x82)      # gcut | $80 = hard restart (06/11: glitch nel villaggio)
BASS_TAV = ins(0x41, 0x08, 0x04, pw=0x600, gcut=0x82)
SONGS["00_tavern"] = song2(8, (0x00, 0x00, 0x00, 0, 0x00, 0x0F), LEAD_TAV, BASS_TAV,
    "A4:3 C5:1 D5:1 E5:1 E5:2 D5:1 C5:2 D5:1 A4:3 C5:1 D5:1 E5:1 G5:3 E5:2 D5:1 A4:3 C5:1 D5:1 E5:1 "
    "E5:2 F#5:1 E5:2 D5:1 G5:2 F#5:1 E5:2 D5:1 C5:2 B4:1 A4:3 E5:3 G5:1 A5:1 G5:1 E5:2 D5:1 C5:2 D5:1 "
    "E5:3 G5:1 A5:1 B5:1 A5:3 G5:2 E5:1 D5:3 F#5:1 G5:1 F#5:1 E5:2 D5:1 C5:2 B4:1 C5:1 D5:1 E5:1 D5:1 "
    "C5:1 B4:1 A4:5 -:1",
    "A2:3 E3:3 A2:3 E3:3 A2:3 E3:3 G2:3 D3:3 A2:3 E3:3 D3:3 A3:3 G2:3 D3:3 A2:3 E3:3 A2:3 E3:3 A2:3 E3:3 "
    "C3:3 G3:3 A2:3 E3:3 D3:3 A3:3 E2:3 B2:3 A2:3 E3:3 A2:5 -:1")
SONGS["00_tavern"]["bar"] = 6

# ================================================================== elenchi del gioco (scelte del committente, 06/11)
# Per aggiungere un brano: definirlo in SONGS e aggiungerne il nome all'elenco giusto; tools/build/gen_music.py crea il
# file su disco e le tabelle del gioco. Ogni elenco puo' crescere (il gioco sceglie a caso).
# (12/11, decisione del committente, TODO M2) un tema per villaggio e uno per capitolo (uguale per i suoi 5 piani, anche il
# piano del boss del capitolo); il piano finale ha il suo tema. town e level: un brano per capitolo 1..4, nell'ordine.
PLAYLIST = dict(
    title="01_demons_eye",                                              # nel loader (non e' un file a parte)
    town=["00_tavern", "00_tavern", "00_tavern", "00_tavern", "00_tavern"],   # villaggi dei capitoli 1..5 (temi: tbd; 5 = citta' dell'Abisso)
    level=["04_iron_crown", "02_blood_path", "13_fear_below", "15_black_chant"],   # piani dei capitoli 1..4
    boss=["05_abyss_gate"],                                             # piano finale (MAXLEVEL)
    fight=["31_fight_1"],                                               # uno a caso per piano, scelto al caricamento
)


def game_files(P=None):
    """brani del gioco, uno per file SNDn: villaggi, livelli, boss, combattimento, senza ripetizioni (ordine di comparsa)"""
    P = P or PLAYLIST
    out = []
    for n in P["town"] + P["level"] + P["boss"] + P["fight"]:
        if n not in out: out.append(n)
    if P["title"] not in out:           # (15/11, TODO E3) Demon's Eye anche come file, ultimo (SND_MENU): musica del menu LOBBY
        out.append(P["title"])
    return out


def jukebox_files(P=None):
    """brani del jukebox: il titolo per primo, poi i file del gioco senza ripeterlo"""
    P = P or PLAYLIST
    return [P["title"]] + [n for n in game_files(P) if n != P["title"]]
TITLES = {"00_tavern": "Tavern of Dawn", "01_demons_eye": "Demon's Eye", "02_blood_path": "Blood Path",
          "03_the_watcher": "The Watcher", "04_iron_crown": "Iron Crown", "05_abyss_gate": "Abyss Gate",
          "11_crypt_steps": "Crypt Steps", "12_bone_halls": "Bone Halls", "13_fear_below": "Fear Below",
          "14_war_drums": "War Drums", "15_black_chant": "Black Chant", "21_lord_of_ruin": "Lord of Ruin",
          "22_throne_of_ash": "Throne of Ash", "23_demon_awakes": "Demon Awakes", "31_fight_1": "Fight 1",
          "32_fight_2": "Fight 2", "33_fight_3": "Fight 3"}
