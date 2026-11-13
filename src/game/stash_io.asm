; ===================================================================
;  baule di casa: disco e oro (08/11: spostati dal modulo della locanda nella coda di CODE2)
;  Il baule sta nel blocco dell'eroe (CHRBLK) dall'08/11 sera: niente record a parte.
; ===================================================================
; tutto l'oro addosso nel baule (quello che non ci sta resta addosso, con un messaggio). 10/11: c_sgold conta le DECINE
; di monete (tetto 65535 decine = 655350 monete): si spostano solo multipli di 10, il resto (0..9) resta sempre addosso.
; 10/11 (decisione del committente): niente prelievo. I negozi spendono l'oro totale (gold_pay) e nel dungeon l'oro
; addosso non serve (a vita 0 se ne perde meta'): toglierlo dal baule non ha senso.
st_gold:
        jsr h_msgclr
        jsr g_div10             ; tmp0:1 = c_gold / 10, tmp6 = resto
        lda c_sgold             ; zaino -> baule (decine)
        sta tmp2
        lda c_sgold+1
        sta tmp3
        lda #$ff                ; baule: fino a 65535 decine
        sta tmp4
        sta tmp5
        jsr gd_add
        bcs _r
        lda tmp2
        sta c_sgold
        lda tmp3
        sta c_sgold+1
        jsr gd_rest             ; Z=1: e' entrato tutto
        php
        jsr g_mul10             ; c_gold = decine rimaste x 10 + resto
        plp
        beq _ok
        jsr h_msg
        #msg "the chest is full"
_ok     lda #SFX_PICK
        jmp sfx_play
_r      rts
.cerror GOLD_MAX % 10 != 0, "GOLD_MAX deve essere un multiplo di 10 (baule a decine)"
; tmp0:1 = c_gold / 10, tmp6 = c_gold mod 10
g_div10 lda c_gold
        sta tmp0
        lda c_gold+1
        sta tmp1
        jsr div10t
        sta tmp6
        rts
; tmp0:1 = tmp0:1 / 10, A = resto (usata anche dai negozi: gold_need)
div10t  lda #0
        ldx #16
-       asl tmp0
        rol tmp1
        rol a
        cmp #10
        bcc +
        sbc #10
        inc tmp0
+       dex
        bne -
        rts
; c_gold = tmp0:1 x 10 + tmp6 (al massimo GOLD_MAX)
g_mul10 asl tmp0
        rol tmp1
        lda tmp0
        sta c_gold
        lda tmp1
        sta c_gold+1
        asl tmp0
        rol tmp1
        asl tmp0
        rol tmp1
        lda tmp0
        clc
        adc c_gold
        sta tmp0
        lda tmp1
        adc c_gold+1
        sta tmp1
        lda tmp0
        clc
        adc tmp6
        sta c_gold
        lda tmp1
        adc #0
        sta c_gold+1
        rts
gd_rest lda tmp0
        ora tmp1
        rts
; tmp2:3 += tmp0:1 fino al tetto tmp4:5; tmp0:1 = quello che non ci sta. C=1 se tmp0:1 era 0 (niente da spostare)
gd_add: lda tmp0
        ora tmp1
        sec
        beq _x
        clc
        lda tmp2
        adc tmp0
        sta tmp2
        lda tmp3
        adc tmp1
        sta tmp3
        lda #0
        rol a                   ; 17esimo bit della somma
        sta tmp0
        sec                     ; somma - tetto (17 bit): C=0 -> ci sta tutta
        lda tmp2
        sbc tmp4
        tax
        lda tmp3
        sbc tmp5
        tay
        lda tmp0
        sbc #0
        bcc _fit
        stx tmp0                ; oltre il tetto: resto = somma - tetto, destinazione = tetto
        sty tmp1
        lda tmp4
        sta tmp2
        lda tmp5
        sta tmp3
        clc
        rts
_fit    lda #0
        sta tmp0
        sta tmp1
        clc
_x      rts

; (08/11 sera) il baule si legge e si scrive con l'eroe: save_char / load_char (src/game/rel.asm)
