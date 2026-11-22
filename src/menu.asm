; ===================================================================
;  menu.asm - modulo MENU (file su disco, 11/11): i menu del villaggio, locanda e negozi, uno per tutti i villaggi.
;  Assemblato con le etichette del gioco (out/work/game.lbl) in DUE zone di RAM (immagine piatta $A700-$FCFF, i buchi li
;  scarta tools/build/pack_menu.py, che comprime le zone una per una nel file MENU):
;    zona 1  MR1_AT $C900 - $CFFF   RAM normale (dopo la mappa; il LOBBY la copre: ovl_cur = 0)
;    zona 2  MR2_AT $F4E0 - $FCFF   RAM sotto il KERNAL (dopo la cache del tema; fino all'11/11 posto del precaricamento)
;    zona 3  MR3_AT $A700 - $A7FF   RAM del banco VIC 2: slot sprite 28-31, liberi nel gioco
;    zona 4  MR4_AT $A300 - $A4FF   (17/11) slot sprite 12-19 (mostri nel dungeon): gli sprite degli NPC del villaggio
;    zona 5  MR5_AT $8C00 - $8E7F   (18/11) sprite forti e boss del tema (dungeon): il "!" e il codice degli NPC (menu/npc.asm)
;    zona 6  MR6_AT $9600 - $977F   (18/11) tabelle dei mostri in gioco (MRT, dungeon): il passo degli NPC (menu/npc_tick.asm)
;  Il gioco lo carica all'ingresso nel villaggio (ovl_town, src/game/stash.asm) se non c'e' e poi resta in memoria.
;  Tutti i menu girano con le interruzioni spente (mk_off) e, come tutto il gioco dal 21/11, con $01 = MEMCFG = $35
;  (KERNAL escluso: il codice della zona 2 si esegue). Escono con ui_exit (che riaccende l'IRQ).
;  Tabella dei salti fissa all'inizio della zona 1 (MENU_INN, MENU_SHOP in stash.asm).
; ===================================================================
        .include "../out/work/game.lbl"
        .include "macros.inc"
        .enc "screen"

        * = MR1_AT
        jmp ov_stash            ; MENU_INN: locanda
        jsr mk_off              ; MENU_SHOP: negozio A (0 fabbro, 1 alchimista); enter_shop e' nella zona 2: prima
        jmp enter_shop          ; (interrupt spenti: mk_off)
        jmp npc_here1           ; MENU_NHERE (18/11): chi e' accanto al PG (menu/npc_here.asm)
        jmp q_offer             ; MENU_QOFFER (22/11): quest da dare (menu/q_who.asm)
        jmp q_tin               ; MENU_QTIN (22/11): quest da ritirare
        jmp q_marks             ; MENU_QMARK (22/11, D12): segni degli NPC fissi
        jmp mm_qmark            ; MENU_QMMK (22/11): "!" delle quest sulla minimappa (menu/npc_fix.asm)

; interrupt spenti per tutto il menu (dal 21/11 il KERNAL e' sempre escluso, $01 = MEMCFG: la zona 2 si esegue sempre).
; Preserva A, X, Y.
mk_off: sei
        rts

; uscita da un menu
mk_exit = ui_exit

        .include "menu/inn.asm"
        .include "menu/shop_act.asm"
        .include "menu/npc_here.asm"
        .include "menu/q_who.asm"       ; (22/11) quest: chi da' e chi ritira
        .include "menu/npc_fix.asm"     ; (22/11) NPC fissi, colore del vestito, "!" sulla minimappa (da GAME)
mz1_top
        .cerror mz1_top > MR1_END, "modulo MENU: zona 1 oltre $CFFF di ", mz1_top - MR1_END, " B"
;@free mz1_top..MR1_END "Coda della zona 1 del MENU: codice o dati del modulo MENU (la build stampa lo spazio libero delle zone)" use=code
;@free mz2_top..MR2_END "Coda della zona 2 del MENU (sotto il KERNAL, gira con $01=$35): codice del modulo MENU o dati" use=code
; (zona 5: la coda libera non ha un @free, perche' per la mappa e' gia' la zona degli sprite forti del tema, @map in game.asm)
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

        * = MR5_AT              ; (18/11) zona 5: sprite del "!" e codice degli NPC del villaggio (menu/npc.asm)
        .include "menu/npc.asm"
mz5_top
        .cerror mz5_top > MR5_END, "modulo MENU: zona 5 oltre $8E7F di ", mz5_top - MR5_END, " B"

        * = MR6_AT              ; (18/11, R11) zona 6: il passo degli NPC (menu/npc_tick.asm), all'inizio della zona (salto di npc_tick)
        .include "menu/npc_tick.asm"
mz6_top
        .cerror mz6_top > MR6_END, "modulo MENU: zona 6 oltre $977F di ", mz6_top - MR6_END, " B"
