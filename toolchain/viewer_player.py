#!/usr/bin/env python3
"""Viewer player (14/11): starts VICE on the shared viewer screen when the index page asks.
Copyright (c) 2026 - Simone Caporale

It runs in the c64-emu-player container (c64-emu-vice image), started by toolchain/viewer.sh start when the project defines
C64_VIEW_PLAYER in toolchain.env (the command that starts VICE on a .d64, e.g. tools/vice/play.sh). The viewer has NO Docker
socket (= root on the host): it talks to this process through a Unix socket in the shared c64-x11 volume.

Protocol: one JSON line per request, one JSON line per answer.
  {"cmd": "status"}                                        -> {"ok": true, "running": bool, "disk": ..., "since": ...}
  {"cmd": "play", "disk": "releases/v1.244/x_1541.d64"}    -> starts VICE on out/<disk> (closes the previous one)
  {"cmd": "basic"}                                         -> runs the command with --bare (VICE with no disk, for manual tries)
  {"cmd": "stop"}                                          -> closes VICE
The disk is a path relative to out/ that must exist, end in .d64/.g64/.prg/.t64/.crt and stay inside out/ (no ../, no links
pointing outside)."""
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
    time.sleep(0.5)                # a command that exits at once (disk refused, VICE not starting) already shows in the status
    return status() if alive() else {"ok": False, "error": "the command ended at once (exit %s)" % cur["p"].returncode}


def play(disk):
    if not CMD:
        return {"ok": False, "error": "C64_VIEW_PLAYER not defined (toolchain.env)"}
    if disk is None:
        return launch(["--bare"], None)
    if not isinstance(disk, str) or not DISK_RE.match(disk) or ".." in disk.split("/"):
        return {"ok": False, "error": "invalid disk"}
    real = os.path.realpath(os.path.join(OUT, disk))
    if not real.startswith(OUT + os.sep) or not os.path.isfile(real):
        return {"ok": False, "error": "disk not found in out/"}
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
        return {"ok": False, "error": "invalid request"}
    if c == "status":
        return status()
    if c == "play":
        return play(req.get("disk") or "")
    if c == "basic":
        return play(None)
    if c == "stop":
        stop()
        return status()
    return {"ok": False, "error": "unknown command"}


def main():
    if os.path.exists(SOCK):
        os.remove(SOCK)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(SOCK)
    os.chmod(SOCK, 0o666)          # the viewer server runs as another user; only our containers mount the c64-x11 volume
    s.listen(4)
    signal.signal(signal.SIGTERM, lambda *_: (stop(), sys.exit(0)))
    print("player ready: %s (%s)" % (SOCK, " ".join(CMD) or "no command"), flush=True)
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
