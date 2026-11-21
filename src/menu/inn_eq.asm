; ===================================================================
;  menu/inn_eq.asm - locanda: oro del baule e spostamenti fra zaino e baule (parte del modulo MENU, zona 2). (21/11) La
;  scelta dell'equipaggiamento (h_enter, h_equip della modalita' h_sel) non c'e' piu': si indossa con E (menu/inn.asm).
; ===================================================================
; oro alla posizione corrente: X = 0 zaino (c_gold), 1 baule (c_sgold)
h_gold: txa
        pha
        jsr ui_gold
        pla
        bne +
        lda c_gold
        ldx c_gold+1
        sta tmp0
        stx tmp1
        jmp ui_num5
+       lda c_sgold             ; baule: decine (10/11), si mostra il totale in monete (6 cifre)
        ldx c_sgold+1
        jsr ui_x10
        jmp ui_num6



; st_col = 0 zaino -> baule (X = posto dello zaino), 1 baule -> zaino (X = posto del baule)
st_move:
        stx st_i
        jsr h_msgclr
        lda st_col
        bne _take
        ldx st_i
        lda c_pack,x            ; zaino -> baule (primo posto libero)
        beq _r
        cmp #I_SCROLL           ; pergamene: se nel baule c'e' gia' la pila, si accumulano fino a SCR_MAX (08/11)
        bne _nf
        ldy #STASH_N-1
-       lda st_id,y
        cmp #I_SCROLL
        beq _msj
        dey
        bpl -
_nf     ldy #0
_f      lda st_id,y
        beq _put
        iny
        cpy #STASH_N
        bne _f
_cf     jsr h_msg
        #msg "the chest is full"
_r      rts
_msj    jmp _ms
_put    lda c_pack,x
        sta st_id,y
        lda c_packb,x
        sta st_b,y
        lda c_packd,x
        sta st_du,y
        lda c_packm,x
        sta st_m,y
        lda c_packs,x
        sta st_sx,y
        jsr pk_zero
        jsr sort_pack
_ok     lda #SFX_PICK
        jmp sfx_play
_take   ldx st_i                ; baule -> zaino / cintura
        lda st_id,x
        beq _r
        cmp #I_SCROLL           ; pergamene con la pila gia' nello zaino: si accumulano fino a SCR_MAX
        bne _tk
        jsr scr_find
        bcs _tk
        lda #SCR_MAX
        sec
        sbc c_packb,y
        beq _sfl
        cmp st_b,x
        bcc +
        lda st_b,x
+       sta tmp0
        clc
        adc c_packb,y
        sta c_packb,y
        lda st_b,x
        sec
        sbc tmp0
        sta st_b,x
        beq _put2               ; la pila del baule e' finita: si toglie
        jmp _ok
_sfl    lda #2                  ; "max 10 scrolls."
        sta gv_why
        jsr h_msg
        jmp give_msg
_ms     lda #SCR_MAX            ; zaino -> pila del baule
        sec
        sbc st_b,y
        bne +
        jmp _cf
+       cmp c_packb,x
        bcc +
        lda c_packb,x
+       sta tmp0
        clc
        adc st_b,y
        sta st_b,y
        lda c_packb,x
        sec
        sbc tmp0
        sta c_packb,x
        bne _ok
        jsr pk_zero
        jsr sort_pack
        jmp _ok
_tk     stx st_i
        lda st_b,x
        sta ap_b
        lda st_du,x
        sta ap_d
        lda st_m,x
        sta ap_m
        lda st_sx,x
        sta ap_s
        lda st_id,x
        jsr give_item
        ldx st_i
        bcc _put2
        jsr h_msg
        jmp give_msg
_put2   cpx #STASH_N-1          ; compatta il baule
        beq _sz
_sh     lda st_id+1,x
        sta st_id,x
        lda st_b+1,x
        sta st_b,x
        lda st_du+1,x
        sta st_du,x
        lda st_m+1,x
        sta st_m,x
        lda st_sx+1,x
        sta st_sx,x
        inx
        cpx #STASH_N-1
        bne _sh
_sz     lda #0
        sta st_id+STASH_N-1
        sta st_b+STASH_N-1
        sta st_du+STASH_N-1
        sta st_m+STASH_N-1
        sta st_sx+STASH_N-1
        jsr sort_pack
        jmp _ok
