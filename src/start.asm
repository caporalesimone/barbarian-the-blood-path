; =============================================================================
; START - avvio del gioco (file START sul disco), caricato dal loader BARBARIAN (src/barbarian.asm).
; Release (INTRO=1): titolo riga per riga con la musica, PRESS SPACE; debug (INTRO=0): solo i file.
; Carica GAME (ZX0, decompresso sul posto), LOBBY, GFX0 e l'elenco eroi, poi salta al gioco.
; Il codice e' in src/common/boot.asm (lo stesso di LORE, src/lore.asm).
; =============================================================================
        .include "common/boot.asm"
;@map $cc00..$d000 "Schermo della schermata di attesa (banco VIC 3) e puntatori sprite"
;@map $e000+512 "Font della schermata di attesa (txt_init: codici 0-63 del font del gioco)"
;@map SPR_AT+384 "Sprite P R E S A C (copiati da ld_spr all'avvio)"
;@map CHRTMP+67 "CHRTMP: stato + file hl (elenco eroi), poi copiato in CHRBUF ($D000)"
