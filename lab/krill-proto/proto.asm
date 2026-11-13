        .enc "none"
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
        lda #$ff                ; CIA2: TA 16 bit free-running, TB counts TA underflows
        sta $dd04
        sta $dd05
        sta $dd06
        sta $dd07
        lda #$41
        sta $dd0f
        lda #$01
        sta $dd0e
        jsr snap                ; 0: start
        jsr $1000               ; install
        sta $c000
        lda #0
        rol
        sta $c001
        jsr snap                ; 1: after install
        ldx #0
-       lda resid,x
        sta $0200,x
        lda resid+256,x
        sta $0300,x
        inx
        bne -
        ldx #<n_dat
        ldy #>n_dat
        jsr $0200               ; load "data" 1622 B -> $c900
        sta $c002
        jsr snap                ; 2
        ldx #<n_hi
        ldy #>n_hi
        jsr $0200               ; load "hi" 2018 B -> $ed00
        sta $c003
        jsr snap                ; 3
        ldx #<n_sav
        ldy #>n_sav
        jsr $0200               ; load "save" plugin -> $2000
        sta $c004
        jsr snap                ; 4
        ldx #<n_s1
        ldy #>n_s1
        jsr $0200
        sta $c030
        ldx #<n_s8
        ldy #>n_s8
        jsr $0200
        sta $c031
        ldx #<sp1
        ldy #>sp1
        jsr $2000               ; save 1 block
        sta $c005
        lda #0
        rol
        sta $c015
        jsr snap                ; 5
        ldx #<sp8
        ldy #>sp8
        jsr $2000               ; save 8 blocks
        sta $c006
        lda #0
        rol
        sta $c016
        jsr snap                ; 6
        ldx #<sp1
        ldy #>sp1
        jsr $2000               ; save 1 block again
        jsr snap                ; 7
        ldx #<n_s1
        ldy #>n_s1
        jsr $0200               ; read back s1
        sta $c007
        jsr snap                ; 8
        ldx #<n_s8
        ldy #>n_s8
        jsr $0200               ; read back s8
        sta $c008
        jsr snap                ; 9
        lda #$55
        sta $c0ff
done    jmp done
snap:   ldy snp
        lda $dd04
        sta $c020,y
        lda $dd05
        sta $c021,y
        lda $dd06
        sta $c022,y
        lda $dd07
        sta $c023,y
        iny
        iny
        iny
        iny
        sty snp
        rts
snp     .byte 0
n_dat   .text "data",0
n_hi    .text "hi",0
n_sav   .text "save",0
n_s1    .text "s1",0
n_s8    .text "s8",0
sp1     .word n_s1, $3000, 250, $3000, $8000
sp8     .word n_s8, $3000, 2000, $3000, $8000
resid   .binary "loader-c64.prg",2
resid_end
        * = $1000
        .binary "install-c64.prg",2
