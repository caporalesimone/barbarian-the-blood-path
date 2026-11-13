; =============================================================================
; LORE - la storia (file LORE sul disco, solo release), caricato dal menu del loader BARBARIAN.
; Lo stesso avvio di START (src/common/boot.asm: titolo, musica, PRESS SPACE) che legge LDAT invece del gioco,
; poi lo scorrimento della storia (src/lore/scroll.asm). Dati: tools/build/gen_lore.py, data/lore.txt.
; =============================================================================
LORE    = 1
        .include "common/boot.asm"
