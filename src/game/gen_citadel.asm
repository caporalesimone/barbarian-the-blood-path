; ===================================================================
;  gen_citadel.asm - (19/11, TODO M11) passo della CITTADELLA del generatore (capitolo 4; descrizione in gen_io.asm e in
;  docs/wiki/dungeon.md "Cittadella"). Non sta nel PRG GAME (il programma e il generatore sotto l'I/O sono pieni): dal 19/11
;  e' parte del CODICE DEL PIANO del capitolo 4 (src/game/ovl_decor.asm con DK_CHAP = 4, coda di GFX7, copiato a OVP_AT da
;  gfx_tail prima di gen_dungeon). Gira con $01 = $34 come il generatore (gen_call): $C900 e' RAM anche li'. Si chiama da
;  gen_dmain (gen_io.asm: jsr cit_finish = OVP_AT + OVJ_GEN). Prima del 19/11 era assemblato da solo per GFX_DUN_END.
; ===================================================================
cit_main:
        ldx #44                 ; colonne
_pr     stx cit_py
        lda maprow_lo-1,x       ; riga y - 1
        sta ptr1
        lda maprow_hi-1,x
        sta ptr1+1
        lda #1                  ; x - 1
_pc     sta cit_px
        ldx #8
_p9     lda cit_9,x
        clc
        adc cit_px
        tay
        lda (ptr1),y
        cmp #T_FLOOR
        bne _pn
        dex
        bpl _p9
        lda cit_px
        clc
        adc #MAPW+1             ; centro del quadrato
        tay
        lda #T_WALL
        sta (ptr1),y
_pn     lda cit_px
        clc
        adc #3
        cmp #21
        bcc _pc
        lda cit_py
        sec
        sbc #3
        tax
        cpx #2
        bcs _pr
        ; passaggi sull'asse: ogni riga con probabilita' 1/2, l'ultima se non ce n'e' ancora nessuno
        lda #0
        sta cit_na
        ldx #1
_ax     stx cur
        cpx #13
        bne +
        lda cit_na
        beq _do
+       lda #2
        jsr rndrange
        beq _na
_do     ldx cur
        lda rcx,x
        sta ch_x0
        lda #24
        sta ch_x1
        lda rcy,x
        sta ch_y
        jsr carve_h
        inc cit_na
_na     lda cur
        clc
        adc #4
        tax
        cpx #17
        bcc _ax
        ldx #MAPW-1             ; specchio della mappa: colonne 47..24 = 0..23
_mr     lda maprow_lo,x
        sta ptr0
        lda maprow_hi,x
        sta ptr0+1
        ldy #0
_mc     sty cit_px
        lda (ptr0),y
        pha
        tya
        eor #$ff
        clc
        adc #48                 ; ~y + 48 = 47 - y (mod 256)
        tay
        pla
        sta (ptr0),y
        ldy cit_px
        iny
        cpy #24
        bcc _mc
        dex
        bpl _mr
        ldx #13                 ; celle 2-3 = specchio delle celle 1-0 (X = cella sinistra, Y = gemella)
_mm     txa
        and #2
        bne _mn
        txa
        ora #3
        sta cit_py
        txa
        and #1
        eor cit_py               ; riga*4 + 3 - colonna
        tay
        lda vis,x
        sta vis,y
        lda rw,x
        sta rw,y
        lda rh,x
        sta rh,y
        lda ry,x
        sta ry,y
        lda rcy,x
        sta rcy,y
        lda #48
        sec
        sbc rx,x
        sbc rw,x                ; (C = 1: 48 - rx >= rw)
        sta rx,y
        lda #46
        sbc rcx,x
        sta rcx,y
_mn     dex
        bpl _mm
        rts

cit_9    .byte 0, 1, 2, MAPW, MAPW+1, MAPW+2, 2*MAPW, 2*MAPW+1, 2*MAPW+2    ; quadrato 3x3 dall'angolo in alto a sinistra
