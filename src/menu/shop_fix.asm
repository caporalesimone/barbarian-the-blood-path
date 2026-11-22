; ===================================================================
;  menu/shop_fix.asm - negozi: riparazione e tetto dell'oro (parte del modulo MENU, zona 3: $A700-$A7FF, slot sprite
;  28-31 liberi nel gioco)
; ===================================================================
; X = voce 0..11 (zaino o equipaggiamento): costo della riparazione in shp_price, prezzo x REPAIR_PC / 100.
; C=1 se non c'e' niente da riparare (gia' intero o non si usura)
rep_cost:
        lda c_packm,x
        beq _no
        cmp c_packd,x
        beq _no
        stx shp_i               ; (fase 3, O11) prezzo con gli affissi: it_cost
        ldy c_packs,x
        lda c_pack,x
        pha
        lda c_packb,x
        tax
        pla
        jsr it_cost
        ldx shp_i
        lda tmp0
        sta mw_l
        lda tmp1
        sta mw_h
        lda #REPAIR_PC
        sta mw_k
        jsr mul16x8             ; prezzo x REPAIR_PC -> mu0..mu2
        lda #0                  ; / 100 (senza divisione: sottrazioni ripetute, al massimo 655 giri)
        sta shp_price
        sta shp_price+1
_dv     lda mu0
        sec
        sbc #100
        tay
        lda mu1
        sbc #0
        tax
        lda mu2
        sbc #0
        bcc _dd
        sta mu2
        stx mu1
        sty mu0
        inc shp_price
        bne _dv
        inc shp_price+1
        bne _dv
_dd     clc
        rts
_no     sec
        rts

; riparazione (fabbro) della voce X (0..11): torna alla durabilita' massima, che cala di 1
shop_repair:
        jsr rep_cost
        bcs _r
        jsr gold_need
        bcs _ng
        lda #2
        jsr shop_ask
        bcc _r
        jsr gold_pay
        ldx ui_lc
        dec c_packm,x
        lda c_packm,x
        sta c_packd,x
        jsr recalc_stats
        jsr msg23
        #msg "repaired."
        lda #SFX_PICK
        jmp sfx_play
_ng     jmp no_gold
_r      rts


; C=0 se c_gold + tmp2:3 <= tetto del borsello (gold_cap, 22/11: a gradini); altrimenti C=1, senza messaggio (10/11: la
; vendita oltre il tetto non fa nulla)
purse_room:
        clc
        lda c_gold
        adc tmp2
        sta pr_l
        lda c_gold+1
        adc tmp3
        sta pr_h
        bcs _pf
        jsr gold_cap            ; A/X = tetto: tetto >= somma?
        cmp pr_l
        txa
        sbc pr_h
        bcc _pf
        clc
        rts
_pf     sec
        rts
pr_l    .byte 0
pr_h    .byte 0

