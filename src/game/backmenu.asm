; =============================================================================
;  Codice per tornare al menu iniziale dalla lobby (16/11): il trampoline (src/common/tramp.inc) e la pagina di attesa
;  (src/common/waitmsg.inc), usati da bb_menu in src/lobby.asm. Stanno qui (GAME, residente) e non in LOBBY perche' LOBBY
;  non puo' superare $CBFF (copre lo schermo di attesa di START durante il caricamento). Attenzione: wm_show scrive
;  $0400-$07FF (schermo) e $3800-$39FF (font), cioe' sopra codice del gioco: dopo la chiamata il gioco non e' piu' utilizzabile
;  (si esce dal gioco), ne' queste routine ne' LOBBY ($C000) stanno in quelle zone.
; =============================================================================
        .include "tramp.inc"
        .include "waitmsg.inc"
