#!/bin/bash
# uso: tools/vice/prof.sh funz1 funz2 ... : cicli medi/max per chiamata (stopwatch VICE), build gia' fatta in out/
source "$(dirname "${BASH_SOURCE[0]}")/vice_env.sh"
cd "$ROOT"
tools/build/mkdisk.sh
($XRUN x64sc -silent -sounddev dummy $VROM -warp -8 out/disk.d64 -remotemonitor >/dev/null 2>&1 &)
sleep 8
python3 - "$@" <<'PY'
import socket,time,re,sys
lbl={}
for l in open('out/game.lbl'):
    m=re.match(r'(\w+)\s*=\s*\$([0-9a-f]+)',l)
    if m: lbl[m.group(1)]=m.group(2)
s=socket.create_connection(("127.0.0.1",6510)); s.settimeout(4)
def cmd(c,w=0.2):
    s.sendall((c+"\n").encode()); time.sleep(w)
    try: return s.recv(65536).decode(errors='ignore')
    except Exception as e: return ""
cmd("",0.5)
cmd('l "out/start.prg" 0',3)   # (11/11) START: installa Krill e carica GAME dal disco
cmd("g 080d",0.3)
time.sleep(2.5)
for f in sys.argv[1:]:
    cmd("",0.3)
    cmd("del",0.2)
    cmd("break %s"%lbl[f],0.2)
    v=[]
    for i in range(int(__import__("os").environ.get("N","25"))):
        o=cmd("x",0.25)
        cmd("sw reset",0.1)
        cmd("ret",0.25)
        o=cmd("sw",0.15)
        m=re.search(r"Stopwatch:\s+(\d+)",o)
        if m: v.append(int(m.group(1)))
    cmd("del",0.2)
    if v: print(f"{f:16s} n={len(v)} media={sum(v)//len(v)} max={max(v)} min={min(v)}")
    cmd("x",0.2)
PY
pkill x64sc
