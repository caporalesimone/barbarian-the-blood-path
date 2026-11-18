; ===================================================================
;  menu/npc_here.asm - (18/11, revisione R3) chi e' accanto al PG nel villaggio, nel modulo MENU (zona 1): spostato da GAME
;  (src/game/quest.asm) per il margine di GAME. Lo chiamano l'etichetta del luogo (loc_id, bar.asm) e il Fire (act_tick)
;  attraverso npc_here di GAME (che controlla prima npc_ok: villaggio, modulo in memoria, NPC piazzati) e MENU_NHERE.
;  npc_offer serve anche al "!" (npc_bmark, zona 5).
; ===================================================================
; C=1 se il PG e' accanto (a una casella, anche in diagonale) a Hilde o a un NPC con una quest da dare: X = NPC, Y = etichetta
; del luogo (QL_ID Hilde, QL_GV "quest giver"). tx, ty conservati (loc_id, bar.asm)
npc_here1:
        lda tx
        pha
        lda ty
        pha
        ldx #0
_l      lda npc_xh,x
        cmp #$ff
        beq _n
        txa
        beq _t                  ; Hilde: sempre (anche con la quest gia' presa: la si rilegge)
        tay
        jsr npc_offer
        bcc _n
_t      jsr npc_tile
        lda tx
        sec
        sbc ptx
        clc
        adc #1
        cmp #3
        bcs _n
        lda ty
        sec
        sbc pty
        clc
        adc #1
        cmp #3
        bcs _n
        ldy #QL_GV
        txa
        bne +
        ldy #QL_ID
+       sec
        bcs _x
_n      inx
        cpx #NPC_N
        bne _l
        clc
_x      pla
        sta ty
        pla
        sta tx
        rts

; Y = NPC: C=1 se ha una quest da dare (A = quest). Cambia Y
npc_offer:
        lda npc_q,y
        beq _no
        tay
        lda bitmask-1,y
        and c_qst
        bne _no
        tya
        sec
        rts
_no     clc
        rts
