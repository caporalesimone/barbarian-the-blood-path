#!/bin/bash
# esegue out/game.prg (build TMDBG) e stampa i record di temporizzazione
source "$(dirname "${BASH_SOURCE[0]}")/vice_env.sh"
cd "$ROOT"
tools/build/mkdisk.sh
($XRUN x64sc -silent -sounddev dummy $VROM -warp -8 out/disk.d64 -remotemonitor >/dev/null 2>&1 &)
sleep 8
python3 - <<'PY'
import socket,time,re
s=socket.create_connection(("127.0.0.1",6510)); s.settimeout(4)
def cmd(c,w=0.5):
    s.sendall((c+"\n").encode()); time.sleep(w)
    try: return s.recv(65536).decode(errors='ignore')
    except Exception as e: return str(e)
cmd("",0.5)
cmd('l "out/start.prg" 0',3)   # (11/11) START: installa Krill e carica GAME dal disco
cmd("g 080d",0.3)
time.sleep(8)
cmd("",0.3)
o=cmd("m 0340 03f2",0.8)
b=[]
for l in o.split("\n"):
    m=re.match(r">C:([0-9a-f]{4})\s+((?:[0-9a-f]{2}\s+)+)",l)
    if m: b+= [int(x,16) for x in m.group(2).split()]
recs=[b[i:i+5] for i in range(0,175,5)]
tot=[r[0]+256*r[1] for r in recs]; work=[r[3]+256*r[4] for r in recs]
print("loop:",tot); print("work:",work); print("path:",[r[2] for r in recs])
print("over (loop>19656+300):",sum(1 for t in tot if t>19956), "max work", max(work))
PY
pkill x64sc
