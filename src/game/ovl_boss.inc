; ===================================================================
;  ovl_boss.inc - (19/11) parti comuni del CODICE DEL PIANO dei boss dei capitoli 1-3 (src/game/ovl_boss1..3.asm, a OVP_AT,
;  nella coda dei file GFX2, GFX4, GFX6; docs/wiki/dungeon.md "Codice del piano", meccaniche: docs/wiki/bestiario.md
;  "Meccaniche dei boss di capitolo"). Ogni file include questo dopo la sua tabella dei salti e i suoi dati.
;  Variabili nell'area del codice (copiata a ogni lettura del tema: ripartono da capo a ogni ingresso nel piano).
; ===================================================================
ob_b    .byte 0                 ; indice del boss
ob_adx  .byte 0                 ; |PG - boss| in pixel (255 se oltre)
ob_ady  .byte 0
ob_sx   .byte 0                 ; segno di PG - boss: 0 PG a destra / sotto, 1 a sinistra / sopra
ob_sy   .byte 0
ob_th   .word 0                 ; soglia di vita (calcolata da ob_frac)
ob_s0   .byte $ff               ; mostri evocati (indici, $ff = nessuno)
ob_s1   .byte $ff
ob_tx   .byte 0                 ; casella del boss
ob_ty   .byte 0
ob_k    .byte 0
ob_i    .byte 0
ob_d8x  .byte 1, $ff, 0, 0, 1, $ff, 1, $ff      ; 8 direzioni (prima le 4 dritte)
ob_d8y  .byte 0, 0, 1, $ff, 1, 1, $ff, $ff

; C=1 se c'e' un boss vivo (X = ob_b = indice)
ob_alive:
        ldx lb_boss
        beq _n
        dex
        stx ob_b
        lda malive,x
        beq _n
        sec
        rts
_n      lda #0                  ; boss morto: niente colore proprio
        sta ovp_tint
        clc
        rts

; distanze fra PG e boss X (ob_adx/ob_ady, segni ob_sx/ob_sy). X conservato
ob_dist:
        lda #0
        sta ob_sx
        sta ob_sy
        lda px
        sec
        sbc mxl,x
        sta tmp0
        lda px+1
        sbc mxh,x
        jsr _abs
        sta ob_adx
        rol ob_sx
        lda py
        sec
        sbc myl,x
        sta tmp0
        lda py+1
        sbc myh,x
        jsr _abs
        sta ob_ady
        rol ob_sy
        rts
_abs    bpl _p                  ; A = byte alto, tmp0 = basso -> A = |valore| (255 se oltre), C = segno (1 negativo)
        eor #$ff
        tay
        lda tmp0
        eor #$ff
        clc
        adc #1
        sta tmp0
        tya
        adc #0
        bne _big1
        lda tmp0
        sec
        rts
_big1   lda #255
        sec
        rts
_p      bne _big0
        lda tmp0
        clc
        rts
_big0   lda #255
        clc
        rts

; boss X fermo (niente IA e niente attacchi: update_monsters salta i mostri storditi)
ob_freeze:
        lda #4
        sta mstun,x
        rts

; boss lampeggiante: colore A un fotogramma su due a gruppi di 8, il suo colore negli altri
ob_blink:
        tay
        lda frame
        and #8
        beq +
        tya
        .byte $2c
+       lda #0
        sta ovp_tint
        rts

; C=1 se la vita del boss X e' <= ob_th. X conservato
ob_below:
        lda ob_th
        cmp mhp,x
        lda ob_th+1
        sbc mhph,x
        rts

; ob_th = vita massima del boss X * A / 3 (A = 1 o 2). X conservato
ob_frac3:
        sta ob_k
        lda mhm,x               ; 16 bit / 3 (divisione lunga, quoziente in tmp0/tmp1)
        sta tmp0
        lda mhmh,x
        sta tmp1
        lda #0
        ldy #16
_d      asl tmp0
        rol tmp1
        rol
        cmp #3
        bcc +
        sbc #3
        inc tmp0
+       dey
        bne _d
        lda tmp0
        sta ob_th
        lda tmp1
        sta ob_th+1
        lda ob_k
        cmp #2
        bne +
        asl ob_th
        rol ob_th+1
+       rts

; ob_th = vita massima del boss X / 2
ob_half:
        lda mhmh,x
        lsr
        sta ob_th+1
        lda mhm,x
        ror
        sta ob_th
        rts

; evoca 2 mostri del tipo A sulle caselle di pavimento accanto al boss (ob_b), svegli -> ob_s0, ob_s1
ob_summon:
        sta ob_k
        lda #$ff
        sta ob_s0
        sta ob_s1
        ldx ob_b
        jsr mon_tx
        sta ob_tx
        ldx ob_b
        jsr mon_ty
        sta ob_ty
        ldx #0
_l      stx ob_i
        ldy lb_cnt
        cpy #32
        bcs _r
        lda ob_tx
        clc
        adc ob_d8x,x
        sta tx
        lda ob_ty
        clc
        adc ob_d8y,x
        sta ty
        jsr floor_ok
        bcs _nx
        ldy lb_cnt
        lda ob_k
        sta mtype,y
        lda tx
        sta mix,y
        lda ty
        sta miy,y
        lda #1
        sta malive,y
        lda #0
        sta mfar,y
        inc lb_cnt
        tya
        tax
        jsr init_rt_from
        ldx lb_cnt
        dex
        lda #1
        sta mwake,x
        lda ob_s0
        bpl +
        stx ob_s0
        bmi _nx
+       stx ob_s1
        rts
_nx     ldx ob_i
        inx
        cpx #8
        bne _l
_r      rts

; C=1 se e' vivo almeno uno dei mostri evocati
ob_sum_alive:
        ldx ob_s0
        bmi +
        lda malive,x
        bne _y
+       ldx ob_s1
        bmi _n
        lda malive,x
        bne _y
_n      clc
        rts
_y      sec
        rts
