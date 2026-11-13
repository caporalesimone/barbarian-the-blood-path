; ===================================================================
;  menu/inn_eq.asm - locanda, scelta dell'equipaggiamento (08/11; fino all'11/11 il modulo OVL2), parte del modulo
;  MENU (src/menu.asm). Gira con $01 = $35 (KERNAL escluso, I/O presente: lo imposta ov_stash).
; ===================================================================
; entra nella scelta per il posto A (0 arma .. 3 anello): blocchi della categoria in zaino e baule
h_enter:
        tax
        inx
        stx h_sel
        ldy #0                  ; remove: non per l'arma
        cpx #1
        beq +
        iny
+       sty h_rm
        ldx #PACK_N-1           ; zaino: primo posto e quanti (ordinato: un blocco solo)
        ldy #0
        sty h_np
_pk     lda c_pack,x
        jsr h_iscat
        bne +
        stx h_p0
        inc h_np
+       dex
        bpl _pk
        ldx #STASH_N-1
        ldy #0
        sty h_nc
_ck     lda st_id,x
        jsr h_iscat
        bne +
        stx h_c0
        inc h_nc
+       dex
        bpl _ck
        lda #0
        sta h_fp
        sta ui_cur
        jsr h_fpn
        sec
        rts

; Z=1 se l'oggetto A e' della categoria h_sel
h_iscat tay
        beq _n
        lda itcat,y
        cmp h_sel
        rts
_n      lda #1
        rts

; ---- scelta: fire su remove, su un oggetto o niente
h_equip:
        lda h_sel
        sec
        sbc #1
        clc
        adc #PACK_N
        sta h_eqi               ; posto dell'equipaggiamento nelle tabelle dello zaino
        lda h_kind
        cmp #K_RM
        bne _ob
        lda #0                  ; remove: nello zaino, se pieno nel baule
        ldx h_eqi
        jsr h_get
        lda it_i
        beq _d1
        jsr h_free
        bcs _n1
        jsr h_put
        jsr h_zeq
_d1     jmp _done
_n1     jmp _no
_n2     jmp _no2
_ob     lda h_sel               ; scudo con un'arma a due mani: no
        cmp #CAT_SHIELD
        bne +
        ldx c_eq
        lda itfl,x
        and #1
        bne _n2
+       lda h_src               ; nuovo oggetto -> nw_*
        ldx h_idx
        jsr h_get
        ldx #3
-       lda it_i,x
        sta nw_i,x
        dex
        bpl -
        lda h_sel               ; arma a due mani con lo scudo: posto per lo scudo (zaino, poi baule)
        cmp #CAT_WEAPON
        bne _sw
        ldx nw_i
        lda itfl,x
        and #1
        beq _sw
        lda c_eq+2
        beq _sw
        lda #0
        ldx #PACK_N+2
        jsr h_get
        jsr h_free
        bcs _no
        jsr h_put
        lda #0
        ldx #PACK_N+2
        jsr h_zeq2
_sw     lda #0                  ; scambio: il vecchio va al posto del nuovo
        ldx h_eqi
        jsr h_get
        lda h_src
        beq +
        lda it_i
        beq +
        jsr h_keep              ; il vecchio entra nel baule: poi la sua pagina
+       lda h_src
        ldx h_idx
        jsr h_put
        ldx #3
-       lda nw_i,x
        sta it_i,x
        dex
        bpl -
        lda #0
        ldx h_eqi
        jsr h_put
_done   jsr recalc_stats
        jsr sort_pack
        jsr h_jump
        lda #SFX_PICK
        jsr sfx_play
        jsr h_back
        sec
        rts
_no2    jsr h_msg
        #msg "two-handed weapon."
        jmp _nof
_no     jsr h_msg
        #msg "no room."
_nof    lda #2                  ; rifiutato: bordo rosso per un attimo
        sta BORDER
        lda #20
        sta h_fl
        lda #SFX_HURT
        jsr sfx_play
        clc
        rts

; posto libero per it_*: zaino (A = 0), altrimenti baule (A = 1, h_keep); X = posto. C=1 se tutto pieno
h_free: ldx #PACK_N
        jsr inv_free
        lda #0
        bcc _r
        ldx #0
-       lda st_id,x
        beq +
        inx
        cpx #STASH_N
        bne -
        sec
        rts
+       jsr h_keep
        lda #1
        clc
_r      rts

; posto dell'equipaggiamento h_eqi (o X con h_zeq2) vuoto
h_zeq:  ldx h_eqi
h_zeq2: lda #0
        sta c_pack,x
        sta c_packb,x
        sta c_packd,x
        sta c_packm,x
        rts


; ---- aiuti della schermata della casa (08/11: nel gioco per far stare il modulo OVLT in 1792 B)
; '>' se A = ui_lc, altrimenti spazio
h_curs: cmp ui_lc
        bne +
        lda #$3e
        .byte $2c
+       lda #$20
        jmp ui_putc
; 18 spazi
h_blank ldx #18
-       lda #$20
        jsr ui_putc
        dex
        bne -
        rts

; nome dell'oggetto (A = 0 zaino/equipaggiamento, 1 baule; X = posto) alla posizione corrente (rotto: rosso)
h_name: jsr h_get
        lda it_b
        sta ui_ib
        lda #0
        ldy it_m
        beq +
        ldy it_d
        bne +
        lda #2
+       sta ui_fc
        lda it_i                ; icona della categoria (08/11) e nome in 16 colonne
        jsr ui_cic
        lda it_i
        jsr ui_item
        lda #0
        sta ui_fc
        rts

; oggetto (A = 0 zaino/equipaggiamento PACK_N.., 1 baule; X = posto): h_get -> it_i..it_m, h_put it_i..it_m ->
h_get:  sec
        .byte $24               ; (bit zp: salta clc)
h_put:  clc
        php
        stx hg_x
        asl a
        asl a
        asl a
        tax
        ldy #0
_l      sty hg_k
        lda h_at,x
        sta $fb
        lda h_at+1,x
        sta $fc
        ldy hg_x
        plp
        php
        bcc _p
        lda ($fb),y
        ldy hg_k
        sta it_i,y
        bcs _n
_p      ldy hg_k
        lda it_i,y
        ldy hg_x
        sta ($fb),y
_n      inx
        inx
        ldy hg_k
        iny
        cpy #4
        bne _l
        plp
        ldx hg_x
        rts
h_at    .word c_pack, c_packb, c_packd, c_packm, st_id, st_b, st_du, st_m

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
        inx
        cpx #STASH_N-1
        bne _sh
_sz     lda #0
        sta st_id+STASH_N-1
        sta st_b+STASH_N-1
        sta st_du+STASH_N-1
        sta st_m+STASH_N-1
        jsr sort_pack
        jmp _ok
