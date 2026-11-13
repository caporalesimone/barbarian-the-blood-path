        .enc "screen"
        .cpu "6502"
        * = $0801
        .word (+), 2026
        .byte $9e, $32,$30,$36,$31, 0
+       .word 0
        * = 2061
        sei
        lda #8
        sta $ba
        lda #$36
        sta $01
        lda #$7f
        sta $dd0d
        jsr clr
        ldx #0
        stx pos
        jsr $1000               ; install
        sta r_inst
        lda #0
        rol
        sta r_c
        ldx #0
-       lda resid,x
        sta $0200,x
        lda resid+256,x
        sta $0300,x
        inx
        bne -
        lda #<s_i
        ldy #>s_i
        jsr pstr
        lda r_inst
        jsr phex
        lda r_c
        jsr phex
        ldx #<n_dat
        ldy #>n_dat
        jsr $0200
        sta r_a
        lda #<s_l
        ldy #>s_l
        jsr pstr
        lda r_a
        jsr phex
        lda $c900           ; primo byte letto
        jsr phex
        ldx #<n_sav
        ldy #>n_sav
        jsr $0200
        sta r_a
        lda #<s_p
        ldy #>s_p
        jsr pstr
        lda r_a
        jsr phex
        lda #$11
        sta $3000
        ldx #<sp1
        ldy #>sp1
        jsr $2000
        sta r_a
        lda #<s_s
        ldy #>s_s
        jsr pstr
        lda r_a
        jsr phex
        lda #0
        sta $3000
        ldx #<n_s1
        ldy #>n_s1
        jsr $0200
        sta r_a
        lda #<s_r
        ldy #>s_r
        jsr pstr
        lda r_a
        jsr phex
        lda $3000
        jsr phex
        lda #<s_ok
        ldy #>s_ok
        jsr pstr
        jmp *
clr     ldx #0
        lda #32
-       sta $0400,x
        sta $0500,x
        sta $0600,x
        sta $0700,x
        inx
        bne -
        rts
pstr    sta $fb
        sty $fc
        ldy #0
-       lda ($fb),y
        beq +
        jsr pch
        iny
        bne -
+       rts
pch     stx sx
        ldx pos
        sta $0400,x
        inc pos
        ldx sx
        rts
phex    pha
        lsr
        lsr
        lsr
        lsr
        jsr pn
        pla
        and #15
pn      cmp #10
        bcc +
        sbc #9
        jmp pch
+       adc #$30-0
        jmp pch
pos     .byte 0
sx      .byte 0
r_inst  .byte 0
r_c     .byte 0
r_a     .byte 0
s_i     .null "INST "
s_l     .null " LOAD "
s_p     .null " PLUG "
s_s     .null " SAVE "
s_r     .null " READ "
s_ok    .null " FINE"
n_dat   .text "data",0
n_sav   .text "save",0
n_s1    .text "s1",0
sp1     .word n_s1, $3000, 250, $3000, $8000
resid   .binary "loader-c64.prg",2
        * = $1000
        .binary "install-c64.prg",2
