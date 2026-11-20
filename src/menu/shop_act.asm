; ===================================================================
;  menu/shop_act.asm - negozi: comprare, vendere, riparare (parte del modulo MENU, zona 1; il resto dei negozi e' in
;  menu/shop.asm, zona 2: la divisione segue solo lo spazio delle due zone)
; ===================================================================
; ------------------------------------------------------------------ negozi: azioni
; compra la merce ui_lc. Pozione: '>' sul primo posto libero della cintura, W/S lo spostano, fire paga e la mette,
; RUN/STOP annulla senza pagare (08/11). Altro: conferma (shop_ask) e give_item.
shop_buy:
        jsr sh_selid
        sta shp_item
        asl
        tay
        lda itprice,y
        sta shp_price
        lda itprice+1,y
        sta shp_price+1
        jsr gold_need           ; 10/11: si paga con l'oro addosso e poi con il baule della locanda
        bcs _ng
        ldx shp_item
        lda itcat,x
        cmp #CAT_POTION
        beq _pot
        lda #0
        jsr shop_ask
        bcc _r
        lda #0
        sta ap_b
        lda shp_item
        jsr give_item
        bcs _full
        jsr sort_pack
_pay    jsr gold_pay
        jsr msg23
        #msg "bought."
        lda #SFX_PICK
        jmp sfx_play
_ng     jmp no_gold
_r      rts
_pot    ldx #0                  ; primo posto libero della cintura
_f      lda c_beltt,x
        beq _sel
        inx
        cpx #4
        bne _f
        lda #1
        sta gv_why
_full   jsr msg23
        jmp give_msg
_sel    stx sh_slot
        jsr msg23
_dr     jsr sh_draw
_l      jsr ui_input
        lda keynew+7            ; RUN/STOP: annulla
        and #$80
        bne _cn
        jsr ui_fire
        bne _put
        lda joynew              ; su/giu': posto libero precedente/seguente
        and #3
        beq _l
        lsr
        lda #$ff
        bcs +
        lda #1
+       sta sh_dir
_nx     lda sh_slot
        clc
        adc sh_dir
        and #3
        sta sh_slot
        tax
        lda c_beltt,x
        bne _nx
        beq _dr
_put    ldx sh_slot
        lda shp_item
        sta c_beltt,x
        jsr _cn
        jmp _pay
_cn     lda #$ff
        sta sh_slot
        rts

; vende la voce ui_lc (zaino, posto della cintura o una pergamena), se il negozio la compra
shop_sell:
        jsr sh_selid
        beq _r
        sta ui_sel
        jsr sh_buys
        bcc _ok
        jsr msg23
        #msg "i don't buy that."
_r      rts
_ok     lda ui_sel              ; prezzo >> SELL_SHIFT (20/11: un quarto, balance.yaml shop_rules.sell_divisor)
        asl
        tay
        lda itprice+1,y
        sta tmp3
        lda itprice,y
        .rept SELL_SHIFT
        lsr tmp3
        ror a
        .endrept
        sta tmp2
        sta shp_price
        lda tmp3
        sta shp_price+1
        jsr purse_room          ; tetto GOLD_MAX addosso: oltre non si vende (07/11 sera)
        bcs _r
        lda #1
        jsr shop_ask
        bcc _r
        ldx ui_lc
        cpx #20
        bcc _pk
        cpx #24
        bne _bt
        jsr scr_find            ; pergamene: una della pila dello zaino
        tya
        tax
_pk     lda c_pack,x
        cmp #I_SCROLL
        bne _z
        dec c_packb,x           ; una pergamena della pila; la pila vuota libera il posto
        bne _gd
_z      jsr pk_zero
        jsr sort_pack
        jmp _gd
_bt     lda #0
        sta c_beltt-20,x
_gd     lda shp_price           ; (18/11, R9) l'oro con add_gold16 di GAME (il tetto lo ha gia' controllato purse_room)
        ldx shp_price+1
        jsr add_gold16
        jsr recalc_stats
        jsr msg23
        #msg "sold."
        lda #SFX_PICK
        jmp sfx_play

