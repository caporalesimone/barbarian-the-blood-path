#!/bin/bash
# uso: tools/vice/shot.sh <png> [secondi] [live]  - carica out/game.prg via monitor (senza tastiera) e fa uno screenshot
#   live: in warp fino al primo giro di main_loop, poi i secondi indicati a velocita' reale (scene con mostri)
OUT=$1; SEC=${2:-4}
source "$(dirname "${BASH_SOURCE[0]}")/vice_env.sh"
cd "$ROOT"
tools/build/mkdisk.sh
($XRUN x64sc -silent -sounddev dummy $VROM -warp -8 out/disk.d64 -remotemonitor >/dev/null 2>&1 &)
sleep 8
python3 - "$OUT" "$SEC" "${3:-}" <<'PY'
import socket,time,sys
s=socket.create_connection(("127.0.0.1",6510)); s.settimeout(3)
def cmd(c,w=1.0):
    s.sendall((c+"\n").encode()); time.sleep(w)
    try: return s.recv(65536).decode(errors='ignore')
    except Exception as e: return str(e)
cmd("",0.5)
cmd('l "out/start.prg" 0',3)   # (11/11) START: installa Krill e carica GAME dal disco
if sys.argv[3] == "live":
    import re
    ml = re.search(r"^main_loop\s*=\s*\$([0-9a-f]+)", open("out/game.lbl").read(), re.M).group(1)
    cmd("break " + ml, 0.3)
    cmd("g 080d", 0.3)
    t = time.time(); buf = ""
    while time.time() - t < 30 and "Stop on" not in buf:
        try: buf += s.recv(65536).decode(errors="ignore")
        except Exception: pass
    cmd("del", 0.3); cmd("warp off", 0.3)
    s.sendall(b"x\n")
else:
    cmd("g 080d",0.3)
time.sleep(float(sys.argv[2]))
cmd("",0.5)
cmd('screenshot "%s" 2'%sys.argv[1],1.5)
PY
pkill x64sc
