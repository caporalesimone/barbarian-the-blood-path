; ===================================================================
;  csheet.asm - (21/11 sera, TODO A1 e D15, soglia del committente 2 s) modulo CSHEET sul disco: la schermata del personaggio
;  (tasto C, src/csheet/charsheet.asm), assemblata a parte con le etichette del gioco (out/work/game.lbl), come il LOBBY e il menu
;  dei trucchi. Caricata a CS_AT ($EC00, RAM sotto il KERNAL: buffer del file del villaggio o del tema, gia' installato quando
;  si apre la schermata) da ui_charsheet (src/game/stash.asm) ed eseguita dall'inizio; resta valida finche' un caricamento o un
;  salvataggio non la copre (cs_ok). Prima stava in GAME (~1,5 KB).
; ===================================================================
        .include "../out/work/game.lbl"
        .include "macros.inc"
        * = CS_AT
        jmp cs_main
        .word csh_end           ; letta da cs_load: il file e' intero se finisce qui
        .include "csheet/charsheet.asm"
csh_end
        .cerror csh_end > MR2_AT, "CSHEET: modulo oltre l'inizio della zona 2 del MENU (", csh_end-MR2_AT, " B)"
