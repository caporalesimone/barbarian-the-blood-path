; ===================================================================
;  cheats.asm - (17/11) modulo CHEATS sul disco: il menu dei trucchi (src/cheats/menu.asm), assemblato a parte con le
;  etichette del gioco (out/work/game.lbl, come il LOBBY e la pagina delle quest) solo con CHEATS = 1 (tools/build/asm.sh).
;  Caricato a CHT_AT (= SCR_B, lo schermo B del gioco: libero mentre c'e' una pagina della UI, ridisegnato all'uscita) da
;  cheat_menu (src/game.asm) ed eseguito dall'inizio. Fino a 1000 B (lo schermo; dopo ci sono i puntatori degli sprite).
; ===================================================================
        .include "../out/work/game.lbl"
        .include "macros.inc"
        * = CHT_AT
        jmp ct_menu
        .include "cheats/menu.asm"
ct_end
        .cerror ct_end > CHT_AT+1000, "CHEATS: modulo oltre i 1000 B dello schermo B (", ct_end-CHT_AT, " B)"
