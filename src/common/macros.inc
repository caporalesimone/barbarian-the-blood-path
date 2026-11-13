; macro comuni (gioco e moduli su file)
at      .macro
        ldx #\1
        ldy #\2
        jsr ui_at
        .endm

msg     .macro
        jsr ui_pi
        .text \1
        .byte 0
        .endm

; riquadro dei menu (ui_box del gioco): x, y, larghezza, altezza (bordi compresi). 09/11: una sola copia qui
; (prima in ui.asm, lobby.asm (ex menu.asm) e ovlt.asm, assemblati a parte)
ubox    .macro
        lda #\1
        sta bx
        lda #\2
        sta by
        lda #\3
        sta bw
        lda #\4
        sta bh
        jsr ui_box
        .endm

tilep   .macro x, y, t
        lda #\x
        sta tx
        lda #\y
        sta ty
        lda #\t
        jsr set_tile
        .endm

; casa 7x4 con porta: bh_x, bh_y, bh_d (porta), bh_r (tetto), bh_s (insegna ai lati della porta)
