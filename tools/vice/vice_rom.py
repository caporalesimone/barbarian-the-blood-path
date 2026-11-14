"""Opzioni di x64sc comuni (13/11, regola del committente: niente percorsi del sistema, tutto relativo al progetto).
ROM_ARGS: impostazioni di fabbrica (-default: non conta la configurazione dell'utente) e TUTTE le ROM da <progetto>/toolchain/roms/vice-roms
(Kernal, Basic, chargen e quelle dei drive 1541, 1541-II, 1570, 1571): VICE non cerca nulla nella sua cartella dati ne' in
/usr/share/vice. VICE (x64sc) e' quello del container c64-emu-vice (/opt/vice/bin, nel PATH). Lo usano tests/lib/c64.py, tools/build/gen_help.py, tools/build/gen_music.py; la copia per gli script shell e'
tools/vice/vice_env.sh (tenerle uguali)."""
import os, re, socket, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # ricavata dalla posizione del file
ROMS = os.path.join(ROOT, "toolchain", "roms", "vice-roms")          # (13/11) sottocartelle come VICE: C64/ e DRIVES/ (toolchain/roms/roms.md)
ROMS_C64 = os.path.join(ROMS, "C64")
ROMS_DRIVES = os.path.join(ROMS, "DRIVES")
ROM_ARGS = ["-default",
            "-kernal", ROMS_C64 + "/kernal-901227-03.bin", "-basic", ROMS_C64 + "/basic-901226-01.bin",
            "-chargen", ROMS_C64 + "/chargen-901225-01.bin",
            "-dos1541", ROMS_DRIVES + "/dos1541-325302-01+901229-05.bin", "-dos1541II", ROMS_DRIVES + "/dos1541ii-251968-03.bin",
            "-dos1570", ROMS_DRIVES + "/dos1570-315090-01.bin", "-dos1571", ROMS_DRIVES + "/dos1571-310654-05.bin"]

# Display (13/11): di norma ogni VICE ha il suo display virtuale (xvfb-run); con C64_VIEW=1 (./build.sh --view, container
# c64-emu-viewer) VICE si apre sullo schermo condiviso DISPLAY, che il viewer mostra nel browser (KasmVNC).
XRUN = [] if os.environ.get("C64_VIEW") == "1" and os.environ.get("DISPLAY") else ["xvfb-run", "-a"]


# Attesa del boot (14/11, TODO I11). VICE apre la porta del monitor remoto (6510) PRIMA di aver finito di avviare il C64: a freddo
# (disco lento dopo il riavvio della macchina) passano ~7 s tra l'una e l'altra. Un programma lanciato prima che il KERNAL abbia
# inizializzato i vettori IRQ ($0314/5) fa girare il C64 a vuoto e il breakpoint non arriva mai. Non si aspetta un tempo fisso:
# si guarda il C64. Pronto = vettori IRQ al valore standard ($EA31) E "READY." sullo schermo (riga 5, $04C8).
_PROMPT = re.compile(r"\(C:\$[0-9a-f]{4}\) $")
_READY = [0x12, 0x05, 0x01, 0x04, 0x19, 0x2E]                  # codici schermo di "READY."


def _mem(s, a, n, tmax=5):
    """n byte da a, dal monitor remoto (la macchina si ferma nel monitor); None se la risposta non arriva in tmax secondi"""
    s.settimeout(0.05)
    try:                                                          # avanzi di risposte precedenti
        while s.recv(65536): pass
    except OSError:
        pass
    s.sendall(("m %04x %04x\n" % (a, a + n - 1)).encode())
    buf, t0 = "", time.time()
    while time.time() - t0 < tmax:
        try:
            d = s.recv(65536)
            if d: buf += d.decode(errors="ignore")
        except socket.timeout:
            pass
        if _PROMPT.search(buf):
            m = re.search(r">C:%04x\s+((?:[0-9a-f]{2}\s+){%d})" % (a, n), buf)
            if m: return [int(x, 16) for x in m.group(1).split()]
    return None


def wait_boot(s, tmax=30):
    """aspetta che il C64 collegato al monitor remoto (socket s) sia pronto (vedi sopra); alla fine lo lascia in marcia.
    Solleva RuntimeError dopo tmax secondi."""
    t0 = time.time()
    while True:
        vec, scr = _mem(s, 0x0314, 2), _mem(s, 0x04C8, len(_READY))
        if vec == [0x31, 0xEA] and scr == _READY:
            s.sendall(b"x\n")                                     # riprende (la prima mem lo aveva fermato nel monitor)
            return
        if time.time() - t0 > tmax:
            raise RuntimeError("VICE: il C64 non e' pronto dopo %d s (vettori IRQ %s, schermo %s)" % (tmax, vec, scr))
        s.sendall(b"x\n")                                         # ancora in avvio: lascia correre e riprova
        time.sleep(0.15)
