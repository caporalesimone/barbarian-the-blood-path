; ===================================================================
;  menu/npc_tick.asm - (18/11, revisione R11) il passo degli NPC del villaggio, nel modulo MENU: zona 6 = MRT ($9600, le
;  tabelle dei mostri in gioco, che nel villaggio non servono: lb_cnt = 0, e che ogni ingresso nel dungeon riscrive:
;  init_monsters_rt, oppure STASHM per il ritorno dal portale). Spostato da GAME (src/game/quest.asm, che chiama MR6_AT ogni
;  giro nel villaggio con il modulo in memoria). Al primo giro piazza gli NPC (npc_init, zona 5).
; ===================================================================
NPC_R    = 10                   ; i vaganti si muovono solo con il PG a meno di 10 caselle (su entrambi gli assi)
NPC_STOP = 2                    ; (18/11) ... e stanno fermi con il PG a 2 caselle o meno

npc_tick6:
        lda npc_pend
        beq +
        lda #0
        sta npc_pend
        jsr player_tile         ; (ptx, pty dell'ingresso: al primo giro non sono ancora aggiornati)
        jsr npc_init            ; (src/menu/npc.asm)
+       lda frame
        and #15
        bne +
        lda #$ff                ; (18/11) ogni 16 fotogrammi l'etichetta del luogo si ricalcola (bar.asm, loc_check): un NPC
        sta lc_x                ; arrivato accanto al PG fermo, o la quest appena presa
+       lda frame
        and #1
        beq +
        rts
+       ldx #NPC_N-1
_l      lda npc_xh,x
        cmp #$ff
        bne +
        jmp _n
+       lda npc_mv,x
        bne _mv
        cpx #0                  ; chi da' la quest resta fermo
        bne +
        jmp _n
+       jsr npc_tile
        lda tx
        sec
        sbc ptx
        clc
        adc #NPC_R
        cmp #2*NPC_R+1
        bcc +
        jmp _n
+       sec
        sbc #NPC_R-NPC_STOP     ; dx + NPC_STOP (0..2 x NPC_STOP = vicino)
        sta tmp6
        lda ty
        sec
        sbc pty
        clc
        adc #NPC_R
        cmp #2*NPC_R+1
        bcc +
        jmp _n
+       sec
        sbc #NPC_R-NPC_STOP     ; dy + NPC_STOP
        cmp #2*NPC_STOP+1
        bcs _go
        lda tmp6
        cmp #2*NPC_STOP+1
        bcs _go
        jmp _n                  ; PG a NPC_STOP caselle o meno su entrambi gli assi: fermo
_go     jsr rand                ; (17/11) parte 1 volta su 16 (era 64: sembravano tutti fermi)
        and #15
        beq +
        jmp _n
+       jsr rand
        and #3
        sta npc_d,x
        jsr npc_in              ; la casella dopo il passo e' fuori dal settore: resta fermo
        bcc +
        jmp _n
+       lda #8                  ; 8 passi da 2 px = una casella
        sta npc_mv,x
_mv     lda npc_xl,x
        sta ent_x
        lda npc_xh,x
        sta ent_x+1
        lda npc_yl,x
        sta ent_y
        lda npc_yh,x
        sta ent_y+1
        stx npc_k
        lda #0
        sta st_nz
        ldy npc_d,x
        lda npc_st,y
        cpy #2
        bcs _y
        jsr try_step_x
        jmp _c
_y      jsr try_step_y
_c      ldx npc_k
        bcs _stop
        lda ent_x               ; non sulla casella del PG
        ldy ent_x+1
        jsr pix_t
        cmp ptx
        bne _ok
        lda ent_y
        ldy ent_y+1
        jsr pix_t
        cmp pty
        beq _stop
_ok     lda ent_x
        sta npc_xl,x
        lda ent_x+1
        sta npc_xh,x
        lda ent_y
        sta npc_yl,x
        lda ent_y+1
        sta npc_yh,x
        dec npc_mv,x
        jmp _n
_stop   lda #0
        sta npc_mv,x
_n      dex
        bmi +
        jmp _l
+       rts
npc_st  .byte 2, $fe, 2, $fe

; X = NPC (1..), (tx, ty) = la sua casella: C=1 se il prossimo passo (npc_d) esce dal suo settore (tk_sec, voce X-1). Cambia tx, ty
npc_in:
        ldy npc_d,x
        lda tx
        clc
        adc npc_dx,y
        sta tx
        lda ty
        clc
        adc npc_dy,y
        sta ty
        txa
        asl
        asl
        tay
        lda tx
        sec
        sbc tk_sec-4,y          ; x - x0
        cmp tk_sec-2,y          ; >= larghezza (anche se negativo: grande)
        bcs +
        lda ty
        sec
        sbc tk_sec-3,y
        cmp tk_sec-1,y
+       rts
npc_dx  .byte 1, $ff, 0, 0
npc_dy  .byte 0, 0, 1, $ff

; X = NPC -> (tx, ty) = la sua casella. X conservato
npc_tile:
        lda npc_xl,x
        ldy npc_xh,x
        jsr pix_t
        sta tx
        lda npc_yl,x
        ldy npc_yh,x
        jsr pix_t
        sta ty
        rts
pix_t   sty tmp7                ; A/Y = pixel -> A = casella
        lsr tmp7
        ror
        lsr tmp7
        ror
        lsr tmp7
        ror
        lsr tmp7
        ror
        rts

