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
        lda npc_d,x             ; (21/11) NPC fisso (bit 7): sempre, con il suo nome (anche con la quest gia' presa)
        bmi _t
        txa
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
        lda npc_d,x
        bpl +
        lsr                     ; (21/11) nome k = bit 4-5: fix_nm[tk_fnb + k] nell'etichetta QL_ID
        lsr
        lsr
        lsr
        and #3
        clc
        adc tk_fnb
        tay
        lda fix_lo,y
        sta loc_lo+QL_ID
        lda fix_hi,y
        sta loc_hi+QL_ID
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

; Y = NPC: C=1 se ha una quest da dare o da ritirare, A = colore del segno (D12: giallo da dare, verde da ritirare). Cambia Y.
; (22/11) NPC fisso: npc_q = $80 + colore (q_marks, q_who.asm); vagante (concept): numero della quest, giallo se non presa
npc_offer:
        lda npc_q,y
        beq _no
        bmi _fx
        tay
        lda bitmask-1,y
        and c_qst
        bne _no
        lda #7
        sec
        rts
_fx     and #$0f
        sec
        rts
_no     clc
        rts
