; ===================================================================
;  menu.asm - modulo MENU (file su disco, 11/11): i menu del villaggio, locanda e negozi, uno per tutti i villaggi.
;  Assemblato con le etichette del gioco (out/work/game.lbl) in DUE zone di RAM (immagine piatta $A700-$FCFF, i buchi li
;  scarta tools/build/pack_menu.py, che comprime le zone una per una nel file MENU):
;    zona 1  MR1_AT $C900 - $CFFF   RAM normale (dopo la mappa; il LOBBY la copre: ovl_cur = 0)
;    zona 2  MR2_AT $F4E0 - $FCFF   RAM sotto il KERNAL (dopo la cache del tema; fino all'11/11 posto del precaricamento)
;    zona 3  MR3_AT $A700 - $A7FF   RAM del banco VIC 2: slot sprite 28-31, liberi nel gioco
;    zona 4  MR4_AT $A300 - $A4FF   (17/11) slot sprite 12-19 (mostri nel dungeon): gli sprite degli NPC del villaggio
;  Il gioco lo carica all'ingresso nel villaggio (ovl_town, src/game/stash.asm) se non c'e' e poi resta in memoria.
;  Tutti i menu girano con $01 = $35 (KERNAL escluso, interruzioni spente, NMI su nmi_stub): il codice della zona 2
;  si esegue solo cosi'. Escono con $01 = $36 prima di ui_exit (che riaccende l'IRQ).
;  Tabella dei salti fissa all'inizio della zona 1 (MENU_INN, MENU_SHOP in stash.asm).
; ===================================================================
        .include "../out/work/game.lbl"
        .include "macros.inc"
        .enc "screen"

        * = MR1_AT
        jmp ov_stash            ; MENU_INN: locanda
        jsr mk_off              ; MENU_SHOP: negozio A (0 fabbro, 1 alchimista); enter_shop e' nella zona 2: prima
        jmp enter_shop          ; il KERNAL va escluso (con $01 = $36 a $F4E0- si eseguirebbe la ROM)
        jmp npc_init            ; MENU_NPC (17/11): NPC del villaggio (menu/npc.asm)

; KERNAL escluso per tutto il menu (sei, NMI in RAM, $01 = $35). Preserva A, X, Y. Da chiamare SOLO dalla zona 1.
mk_off: sei
        pha
        lda #<nmi_stub          ; (RESTORE: vettore NMI nella RAM sotto il KERNAL)
        sta $fffa
        lda #>nmi_stub
        sta $fffb
        lda #$35
        sta $01
        pla
        rts

; uscita da un menu: di nuovo il KERNAL ($01 = $36), poi ui_exit
mk_exit:
        lda #$36
        sta $01
        jmp ui_exit

        .include "menu/inn.asm"
        .include "menu/shop_act.asm"
        .include "menu/npc.asm"
mz1_top
        .cerror mz1_top > MR1_END, "modulo MENU: zona 1 oltre $CFFF di ", mz1_top - MR1_END, " B"
;@free mz1_top..MR1_END "Coda della zona 1 del MENU: codice o dati del modulo MENU (la build stampa lo spazio libero delle zone)" use=code
;@free mz2_top..MR2_END "Coda della zona 2 del MENU (sotto il KERNAL, gira con $01=$35): codice del modulo MENU o dati" use=code
;@free mz3_top..MR3_END "Coda della zona 3 del MENU (banco VIC, slot sprite 28-31): codice del modulo MENU o dati" use=code

        * = MR2_AT
        .include "menu/inn_eq.asm"
        .include "menu/shop.asm"
mz2_top
        .cerror mz2_top > MR2_END, "modulo MENU: zona 2 oltre $FCFF di ", mz2_top - MR2_END, " B"

        * = MR3_AT
        .include "menu/shop_fix.asm"
        .include "menu/npc_look.asm"
mz3_top
        .cerror mz3_top > MR3_END, "modulo MENU: zona 3 oltre $A7FF di ", mz3_top - MR3_END, " B"

        * = MR4_AT              ; (17/11) zona 4: sprite degli NPC (slot 12-19, tools/build/npc_gfx.py), solo dati
        .binary "../out/work/gfx/npc_spr.bin"
mz4_top
        .cerror mz4_top != SPR_DATA+20*64, "modulo MENU: zona 4 = 8 sprite degli NPC"
