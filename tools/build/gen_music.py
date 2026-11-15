#!/usr/bin/env python3
"""Compila i brani di tools/build/songs.py nel formato del player src/common/sid_player.inc (a pattern, rilocabile).

Formato di un brano (offset relativi all'inizio del brano, 16 bit little endian):
   0      speed (fotogrammi per tick)
   1..6   filtro: cutoff iniziale, minimo, massimo, passo dello sweep, $d417 (risonanza<<4 | voci), $d418 (modo<<4 | volume)
   7..57  strumenti delle 3 voci: 17 parametri x 3 (vedi INS_KEYS, un parametro per tutte le voci di fila)
  58..63  offset dell'ordine delle voci 0, 1, 2
  64      numero di pattern N, poi N byte bassi e N byte alti degli offset dei pattern
  ...     ordini e pattern
Ordine di una voce: $00-$7F pattern; $80-$BF trasposizione = byte - $A0 (semitoni, -32..+31);
                    $C0-$DF il pattern che segue si ripete (byte - $BF) volte; $FF = da capo (trasposizione 0).
Pattern: $E0-$EF nuova durata = DUR[byte & 15] tick; $FF fine; altro = nota (0 pausa, 1..95, bit 7 = seconda
         forma d'onda / secondo ADSR dello strumento). Ogni pattern comincia con una durata.

Uscite: out/work/snd/<nome>.bin (brano), out/work/snd/sndN.prg (file su disco SNDN), out/work/music_tab.inc (tabelle del gioco),
out/work/sid_freq.inc (frequenze),
out/work/sid_title.inc (brano del titolo per il loader), out/work/jukebox_songs.inc (tutti i brani per il jukebox)."""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "simulators")]
from vicemon import ROM_ARGS, XRUN  # noqa: E402  (Lab64: x64sc con -default + tutte le ROM di Lab64)
sys.path.insert(0, HERE)
import songs  # noqa: E402

OUT = os.path.join(ROOT, "out", "work", "snd")
DUR = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 14, 16, 24, 32, 48]
INS_KEYS = ["wave", "wave2", "ad", "sr", "ad2", "sr2", "pwlo", "pwhi", "pwd", "pwmin", "pwmax", "vd", "vw", "arp",
            "slo", "shi", "gcut"]
HDR = 64


def events(txt):
    d = songs.seq(txt)[:-1]
    return [(d[i], d[i + 1]) for i in range(0, len(d), 2)]


def split_rest(ev):
    """le pause di durata fuori tabella si spezzano; le note no (errore)"""
    out = []
    for n, d in ev:
        if d in DUR:
            out.append((n, d))
            continue
        assert n == 0, "durata %d non in tabella (nota %d)" % (d, n)
        while d:
            p = max(x for x in DUR if x <= d)
            out.append((0, p))
            d -= p
    return out


def chunks(ev, bar):
    """taglia la voce a fine battuta (solo dove nessuna nota scavalca il taglio)"""
    out, cur, t = [], [], 0
    for e in ev:
        cur.append(e)
        t += e[1]
        if t % bar == 0:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def key(ch):
    """forma del pattern indipendente dalla trasposizione: (prima nota, chiave)"""
    first = next((n & 0x7F for n, _ in ch if n), None)
    k = tuple(((n & 0x7F) - first if n else None, n & 0x80, d) for n, d in ch)
    return first, k


def pat_bytes(ch, tr):
    b, cur = [], None
    for n, d in ch:
        if d != cur:
            b.append(0xE0 | DUR.index(d))
            cur = d
        if n:
            base = (n & 0x7F) - tr
            assert 1 <= base <= 0x5F, base
            b.append(base | (n & 0x80))
        else:
            b.append(0)
    return b + [0xFF]


def compile_song(song):
    bar = song.get("bar", 16)
    pats, pkey = [], {}
    orders = []
    for v in ("v0", "v1", "v2"):
        refs = []
        for ch in chunks(split_rest(events(song[v])), bar):
            first, k = key(ch)
            if k in pkey:
                pi, pfirst = pkey[k]
                tr = 0 if first is None else first - pfirst
            else:
                pi = len(pats)
                pats.append(pat_bytes(ch, 0))
                pkey[k] = (pi, first)
                tr = 0
            refs.append((pi, tr))
        o, ctr, i = [], 0, 0
        while i < len(refs):
            pi, tr = refs[i]
            j = i
            while j + 1 < len(refs) and refs[j + 1] == refs[i] and j + 1 - i < 32:
                j += 1
            if tr != ctr:
                assert -32 <= tr <= 31
                o.append(0xA0 + tr)
                ctr = tr
            if j > i:
                o.append(0xBF + (j - i + 1))
            o.append(pi)
            i = j + 1
        orders.append(o + [0xFF])
    assert len(pats) < 128
    I = song["ins"]
    vals = dict(wave=[i["wave"] for i in I], wave2=[i["wave2"] for i in I], ad=[i["ad"] for i in I],
                sr=[i["sr"] for i in I], ad2=[i["ad2"] for i in I], sr2=[i["sr2"] for i in I],
                pwlo=[i["pw"] & 255 for i in I], pwhi=[i["pw"] >> 8 for i in I], pwd=[i["pwd"] & 255 for i in I],
                pwmin=[i["pwmin"] for i in I], pwmax=[i["pwmax"] for i in I], vd=[i["vd"] for i in I],
                vw=[i["vw"] for i in I], arp=[i["arp"] for i in I], slo=[i["slide"] & 255 for i in I],
                shi=[(i["slide"] >> 8) & 255 for i in I], gcut=[i["gcut"] for i in I])
    assert song["filt"][4] & 15 in (0, 15), "il filtro deve prendere tutte le voci o nessuna (le voci SID cambiano)"
    blob = [song["speed"]] + list(song["filt"])
    for k in INS_KEYS:
        blob += vals[k]
    assert len(blob) == 58
    npat = len(pats)
    ofs = HDR + 1 + 2 * npat
    oofs = []
    body = []
    for o in orders:
        oofs.append(ofs + len(body))
        body += o
    pofs = []
    for p in pats:
        pofs.append(ofs + len(body))
        body += p
    for x in oofs:
        blob += [x & 255, x >> 8]
    blob += [npat] + [x & 255 for x in pofs] + [x >> 8 for x in pofs] + body
    blob = [x & 255 for x in blob]
    assert len(blob) < 4096
    return bytes(blob)


def asm_bytes(label, data):
    o = [label]
    for i in range(0, len(data), 32):
        o.append("        .byte " + ", ".join("$%02x" % x for x in data[i:i + 32]))
    return o


def main():
    os.makedirs(OUT, exist_ok=True)
    f = songs.freq_table()
    open(os.path.join(ROOT, "out", "work", "sid_freq.inc"), "w").write(
        "; generato da tools/build/gen_music.py - frequenze SID (PAL), indice 0 = pausa, 1 = C0\n"
        "sp_flo  .byte " + ", ".join("$%02x" % (x & 255) for x in f) + "\n"
        "sp_fhi  .byte " + ", ".join("$%02x" % (x >> 8) for x in f) + "\n")
    P = songs.PLAYLIST
    blobs = {}
    for name in songs.SONGS:
        blobs[name] = compile_song(songs.SONGS[name])
        open(os.path.join(OUT, name + ".bin"), "wb").write(blobs[name])
    # file su disco: SND0..SNDn nell'ordine villaggio, livelli, boss, combattimento
    game = songs.game_files(P)              # (12/11) un file per brano: i temi ripetuti fra capitoli non si duplicano
    for f in os.listdir(OUT):
        if f.startswith("snd") and f.endswith(".prg"):
            os.remove(os.path.join(OUT, f))
    assert len(game) <= 36, "troppi brani (nomi SND0-SNDZ)"
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for i, name in enumerate(game):
        open(os.path.join(OUT, "snd%s.prg" % digits[i].lower()), "wb").write(b"\x00\x00" + blobs[name])
    assert [game.index(n) for n in P["fight"]] == list(range(game.index(P["fight"][0]), game.index(P["fight"][0]) + len(P["fight"]))), \
        "i motivetti di combattimento devono essere file consecutivi (SND_FIG0..)"
    smax = max(len(blobs[n]) for n in P["town"] + P["level"] + P["boss"])
    fmax = max(len(blobs[n]) for n in P["fight"])
    o = ["; generato da tools/build/gen_music.py (brani in tools/build/songs.py) - non modificare",
         "; (12/11, TODO M2) un brano per villaggio e uno per capitolo (snd_town_c, snd_lvl_c: capitolo 1..), boss finale",
         "snd_town_c .byte " + ", ".join(str(game.index(n)) for n in P["town"]),
         "snd_lvl_c  .byte " + ", ".join(str(game.index(n)) for n in P["level"]),
         "SND_NCHAP  = %d" % len(P["level"]),
         "SND_BOSS   = %d" % game.index(P["boss"][0]),
         "SND_FIG0   = %d" % game.index(P["fight"][0]), "SND_NFIG   = %d" % len(P["fight"]),
         "SND_N      = %d" % len(game),
         "SND_SMAX   = %d          ; brano piu' lungo (villaggio/livello/boss)" % smax,
         "SND_FMAX   = %d          ; motivetto di combattimento piu' lungo" % fmax,
         "snd_digit  .text \"%s\"" % digits[:len(game)].upper(),
         "snd_llo    .byte " + ", ".join("<%d" % len(blobs[n]) for n in game),
         "snd_lhi    .byte " + ", ".join(">%d" % len(blobs[n]) for n in game),
         "; " + ", ".join("%s=%s(%d B)" % (digits[i], n, len(blobs[n])) for i, n in enumerate(game))]
    open(os.path.join(ROOT, "out", "work", "music_tab.inc"), "w").write("\n".join(o) + "\n")
    t = P["title"]
    open(os.path.join(ROOT, "out", "work", "sid_title.inc"), "w").write(
        "\n".join(["; brano del titolo: %s (tools/build/songs.py)" % t] + asm_bytes("sid_title", blobs[t])) + "\n")
    # jukebox: tutti i brani del gioco (titolo compreso) con nome
    jl = [t] + game
    o = ["; generato da tools/build/gen_music.py - brani per tools/jukebox.asm", "JB_NSONG = %d" % len(jl)]
    o.append("jb_slo .byte " + ", ".join("<jbs_%d" % i for i in range(len(jl))))
    o.append("jb_shi .byte " + ", ".join(">jbs_%d" % i for i in range(len(jl))))
    for i, n in enumerate(jl):
        role = "title" if i == 0 else ("town" if n in P["town"] else "level" if n in P["level"] else
                                       "boss" if n in P["boss"] else "fight")
        o.append("jbn_%d .text \"%-14s %-5s\"" % (i, songs.TITLES.get(n, n)[:14].lower(), role))
    o.append("jb_nlo .byte " + ", ".join("<jbn_%d" % i for i in range(len(jl))))
    o.append("jb_nhi .byte " + ", ".join(">jbn_%d" % i for i in range(len(jl))))
    for i, n in enumerate(jl):
        o += asm_bytes("jbs_%d" % i, blobs[n])
    open(os.path.join(ROOT, "out", "work", "jukebox_songs.inc"), "w").write("\n".join(o) + "\n")
    if "-v" in sys.argv:
        for n, b in blobs.items():
            print("%-18s %4d B" % (n, len(b)))
    tot = sum(len(blobs[n]) for n in game)
    print("brani del gioco: %d, %d B (max brano %d, max combattimento %d); titolo %d B" % (
        len(game), tot, smax, fmax, len(blobs[t])))


if __name__ == "__main__" and "--render" not in sys.argv:
    main()


def render(idx, name, seconds):
    """jukebox con AUTOPLAY=idx -> VICE (reSID) -> WAV -> MP3 in out/work/music/"""
    import subprocess
    od = os.path.join(ROOT, "out", "work", "music")         # MP3 di ascolto (13/11: in out/, generati)
    os.makedirs(od, exist_ok=True)
    prg = os.path.join(od, name + ".prg")
    subprocess.run(["64tass", "-a", "-q", "-I", os.path.join(ROOT, "src"), "-I", os.path.join(ROOT, "src", "common"),
                    "-I", os.path.join(ROOT, "src", "game"), "-I", os.path.join(ROOT, "out", "work"),
                    "-D", "AUTOPLAY=%d" % idx, os.path.join(ROOT, "src", "jukebox.asm"), "-o", prg], check=True)
    wav = os.path.join(od, name + ".wav")
    subprocess.run(XRUN + ["x64sc", "-silent"] + ROM_ARGS + ["-sounddev", "wav",
                    "-soundarg", wav, "-sidenginemodel", "256", "-limitcycles", str(int(985248 * (seconds * 1.8 + 8))),
                    "-autostart", prg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=seconds * 3 + 120)
    mp3 = os.path.join(od, name + ".mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "2.5", "-i", wav, "-t", str(seconds), "-af",
                    "afade=t=out:st=%d:d=2" % (seconds - 2), "-b:a", "128k", mp3], check=True)
    os.remove(wav)
    os.remove(prg)
    return mp3


if __name__ == "__main__" and "--render" in sys.argv:
    main()
    P = songs.PLAYLIST
    jl = [P["title"]] + songs.game_files(P)
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    for i, n in enumerate(jl):
        if not only or n in only:
            print(render(i, n, 16 if n.startswith("3") else 40))
