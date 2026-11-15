; =============================================================================
; LORE - la storia (file LORE sul disco, solo release), caricato dal menu del loader BARBARIAN.
; Lo stesso avvio di START (src/common/boot.asm: titolo, musica, PRESS SPACE) che legge LDAT invece del gioco,
; poi lo scorrimento della storia (src/lore/scroll.asm). Dati: tools/build/gen_lore.py, data/lore.txt.
; =============================================================================
LORE    = 1
        .include "common/boot.asm"
;@map $cc00..$d000 "Colori del bitmap del titolo (banco VIC 3) e puntatori sprite"
;@map SPR_AT+384 "Sprite P R E S A C di PRESS SPACE (copiati da ld_spr)"
;@map TBUF "TBUF: il file TITLE letto qui, poi mostrato riga per riga nel bitmap a $E000"
;@map LD_DST "LDAT decompresso sul posto: il testo della storia"
