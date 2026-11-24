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
        jsr sh_cost             ; (fase 3) prezzo con gli affissi
        lda tmp0
        sta shp_price
        lda tmp1
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
        ldx ui_lc               ; (21/11) bonus della merce (anelli: la caratteristica tirata all'ingresso)
        lda l8_b-LC_W,x
        sta ap_b
        lda l8_s-LC_W,x
        sta ap_s
        lda shp_item
        jsr give_item
        bcs _full
        jsr sort_pack
_pay    jsr gold_pay
        jsr sh_take             ; (22/11, committente) l'oggetto comprato sparisce dalla merce
        jsr msg23
        #msg "bought."
        lda #SFX_PICK
        jmp sfx_play
_ng     jmp no_gold
_r      rts
_pot    jsr belt_cap            ; primo posto libero della cintura (24/11, F1: 4 o 8 posti)
        sta tmp0
        ldx #0
_f      lda c_beltt,x
        beq _sel
        inx
        cpx tmp0
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
_nx     jsr belt_cap            ; (24/11, F1) giro sui posti che ci sono (4 o 8: maschera posti - 1)
        sec
        sbc #1
        sta tmp0
        lda sh_slot
        clc
        adc sh_dir
        and tmp0
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
        lda #0                  ; (21/11) il cursore torna nella lista della merce
        sta sl_l
        rts

; (22/11, committente) toglie dalla merce la voce comprata (ui_lc - LC_W): le seguenti salgono di un posto, shp_cnt - 1.
; La lista si rifa' in enter_shop (_rb: sh_segs + sl_reinit, che riporta il cursore sull'ultima voce se serve)
sh_take:
        lda shp_cnt             ; (nessuna merce: niente da togliere; i test chiamano shop_buy senza enter_shop)
        beq _r
        lda ui_lc
        sec
        sbc #LC_W
        tax
_l      inx
        cpx shp_cnt
        bcs _e
        lda l8_id,x
        sta l8_id-1,x
        lda l8_b,x
        sta l8_b-1,x
        lda l8_s,x
        sta l8_s-1,x
        bcc _l                  ; (C = 0 da cpx)
_e      dec shp_cnt
        ldx shp_cnt
        lda #0
        sta l8_id,x
        sta l8_b,x
        sta l8_s,x
_r      rts

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
_ok     jsr sh_cost             ; prezzo con gli affissi (fase 3) >> SELL_SHIFT (20/11: un quarto, balance.yaml shop_rules.sell_divisor)
        lda tmp1
        sta tmp3
        lda tmp0
        .rept SELL_SHIFT
        lsr tmp3
        ror a
        .endrept
        sta tmp2
        sta shp_price
        lda tmp3
        sta shp_price+1
        jsr purse_room          ; tetto del borsello addosso: oltre non si vende (07/11 sera)
        bcc +
        jsr msg23               ; (23/11, committente) con il messaggio: dal 10/11 il rifiuto era muto e sembrava un difetto
        #msg "your purse is full."
        rts
+
        lda #1
        jsr shop_ask
        bcc _r
        ldx ui_lc               ; (21/11) zaino 0..7 o cintura LC_B.. (le pergamene sono nello zaino, in pila)
        cpx #LC_B
        bcs _bt
        lda c_pack,x
        cmp #I_SCROLL
        bne _z
        dec c_packb,x           ; una pergamena della pila; la pila vuota libera il posto
        bne _gd
_z      jsr pk_zero
        jsr sort_pack
        jmp _gd
_bt     lda #0
        sta c_beltt-LC_B,x
_gd     lda shp_price           ; (18/11, R9) l'oro con add_gold16 di GAME (il tetto lo ha gia' controllato purse_room)
        ldx shp_price+1
        jsr add_gold16
        jsr recalc_stats
        jsr msg23
        #msg "sold."
        lda #SFX_PICK
        jmp sfx_play

