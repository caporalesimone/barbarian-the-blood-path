; =============================================================================
; START - avvio del gioco (file START sul disco), caricato dal loader BARBARIAN (src/barbarian.asm).
; Release (INTRO=1): titolo riga per riga con la musica, PRESS SPACE; debug (INTRO=0): solo i file.
; Carica GAME (ZX0, decompresso sul posto), LOBBY, GFX0 e l'elenco eroi, poi salta al gioco.
; Il codice e' in src/common/boot.asm (lo stesso di LORE, src/lore.asm).
; =============================================================================
        .include "common/boot.asm"
