#!/bin/sh
# Debug: registri, disassembla, singola istruzione, call, breakpoint, trace, snapshot della RAM.
set -e; . "$(dirname "$0")/common.sh"
fresh
$C64 --compact regs
$C64 --compact disasm 0xFFFC 3       # il disassembler del core
$C64 --compact step 3                # 3 istruzioni
$C64 --compact trace '{"max":5,"last":3}'    # METTI SEMPRE max (default 20000 istruzioni = minuti)
$C64 ramSnap prima
$C64 poke 0xC000 7
$C64 --compact ramDiff prima null    # -> un indirizzo cambiato
$C64 --compact call 0xFFD2 '{"a":65}'        # JSR CHROUT con A=65: stampa 'A'
$C64 breakpoint 0xFFD2; $C64 breakpoints; $C64 clearBreakpoints
