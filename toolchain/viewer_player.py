#!/usr/bin/env python3
"""Lettore del viewer (14/11): avvia VICE sullo schermo condiviso del viewer quando lo chiede la pagina indice.
Copyright (c) 2026 - Simone Caporale

Gira nel container c64-emu-player (immagine c64-emu-vice), avviato da toolchain/viewer.sh start se il progetto definisce
C64_VIEW_PLAYER in toolchain.env (il comando che avvia VICE su un .d64, es. tools/vice/play.sh). Il viewer NON ha il socket di
Docker (= root sull'host): parla con questo processo attraverso un socket Unix nel volume condiviso c64-x11.

Protocollo: una riga JSON per richiesta, una riga JSON di risposta.
  {"cmd": "status"}                                        -> {"ok": true, "running": bool, "disk": ..., "since": ...}
  {"cmd": "play", "disk": "releases/v1.244/x_1541.d64"}    -> avvia VICE su out/<disk> (chiude quello di prima)
  {"cmd": "basic"}                                         -> avvia il comando con --bare (VICE senza disco, per le prove a mano)
  {"cmd": "stop"}                                          -> chiude VICE
Il disco e' un percorso relativo a out/ che deve esistere, finire in .d64/.g64/.prg/.t64/.crt e restare dentro out/
(niente ../, niente link fuori)."""
import json, os, re, shlex, signal, socket, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.realpath(os.path.join(ROOT, "out"))
SOCK = os.environ.get("C64_PLAYER_SOCK", "/tmp/.X11-unix/c64-player.sock")
CMD = shlex.split(os.environ.get("C64_VIEW_PLAYER", ""))
DISK_RE = re.compile(r"^[A-Za-z0-9._/-]{1,200}\.(d64|g64|prg|t64|crt)$", re.I)
cur = {"p": None, "disk": None, "since": None}


def alive():
    return cur["p"] is not None and cur["p"].poll() is None


def stop():
    if alive():
        try:
            os.killpg(cur["p"].pid, signal.SIGTERM)
            cur["p"].wait(5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(cur["p"].pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    cur.update(p=None, disk=None, since=None)


def launch(args, label):
    stop()
    cur["p"] = subprocess.Popen(CMD + args, cwd=ROOT, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cur.update(disk=label, since=int(time.time()))
    time.sleep(0.5)                # un comando che esce subito (disco rifiutato, VICE che non parte) si vede gia' nello stato
    return status() if alive() else {"ok": False, "error": "il comando e' terminato subito (exit %s)" % cur["p"].returncode}


def play(disk):
    if not CMD:
        return {"ok": False, "error": "C64_VIEW_PLAYER non definito (toolchain.env)"}
    if disk is None:
        return launch(["--bare"], None)
    if not isinstance(disk, str) or not DISK_RE.match(disk) or ".." in disk.split("/"):
        return {"ok": False, "error": "disco non valido"}
    real = os.path.realpath(os.path.join(OUT, disk))
    if not real.startswith(OUT + os.sep) or not os.path.isfile(real):
        return {"ok": False, "error": "disco non trovato in out/"}
    return launch([os.path.relpath(real, ROOT)], disk)


def status():
    if not alive():
        cur.update(p=None, disk=None, since=None)
    return {"ok": True, "running": alive(), "disk": cur["disk"], "bare": alive() and cur["disk"] is None, "since": cur["since"]}


def handle(line):
    try:
        req = json.loads(line)
        c = req.get("cmd")
    except (ValueError, AttributeError):
        return {"ok": False, "error": "richiesta non valida"}
    if c == "status":
        return status()
    if c == "play":
        return play(req.get("disk") or "")
    if c == "basic":
        return play(None)
    if c == "stop":
        stop()
        return status()
    return {"ok": False, "error": "comando sconosciuto"}


def main():
    if os.path.exists(SOCK):
        os.remove(SOCK)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(SOCK)
    os.chmod(SOCK, 0o666)          # il server del viewer gira con un altro utente; il volume c64-x11 lo montano solo i nostri container
    s.listen(4)
    signal.signal(signal.SIGTERM, lambda *_: (stop(), sys.exit(0)))
    print("player pronto: %s (%s)" % (SOCK, " ".join(CMD) or "nessun comando"), flush=True)
    while True:
        c, _ = s.accept()
        with c:
            c.settimeout(5)
            try:
                data = b""
                while b"\n" not in data and len(data) < 4096:
                    b = c.recv(4096)
                    if not b:
                        break
                    data += b
                c.sendall((json.dumps(handle(data.decode("utf-8", "replace").strip())) + "\n").encode())
            except OSError:
                pass


if __name__ == "__main__":
    main()
