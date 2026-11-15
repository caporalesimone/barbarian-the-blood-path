; ===================================================================
;  jukebox.asm - prova di tutti i suoni del gioco (brani + effetti) con il player del gioco.
;  Una sola schermata: elenco con nome e ruolo, cursore, stato. Brani e player come nel gioco (voce 1 del SID
;  condivisa con gli effetti); i brani sono quelli di tools/build/songs.py (out/work/jukebox_songs.inc, tools/build/gen_music.py).
;  Tasti: su/giu' (cursore o W/S) scelta, RETURN/fire suona, SPAZIO pausa, R ripetizione/singolo, X stop.
;  Uscita: out/work/jukebox.prg (sul disco di sviluppo come JUKEBOX).
; ===================================================================
        .cpu "6502"
SP_VARS = $c000
SP_V0   = 7                     ; come nel gioco: lead sulla voce 2, accordi sulla 1 (con gli effetti), basso sulla 3
SP_V1   = 0
SP_V2   = 14
SCR     = $0400
COL     = $d800
ROW0    = 3                     ; prima riga dell'elenco
; AUTOPLAY (sempre da riga di comando): -1 jukebox normale, n = suona la voce n (rendering degli MP3)
GETIN   = $ffe4
;@map $0400..$07e8 "Schermo del jukebox"

        * = $0801
        .word _nl, 2026
        .byte $9e
        .text "2061"
        .byte 0
_nl     .word 0
        jmp main

        .virtual $c100
cur     .byte ?                 ; voce selezionata
playing .byte ?                 ; voce in riproduzione ($ff nessuna)
paused  .byte ?
rpt     .byte ?                 ; 1 = ripetizione
sfx_t   .byte ?
sfx_w   .byte ?
sfx_sx  .byte ?
sfx_sy  .byte ?
sfx_f   .byte ?
sfx_d   .byte ?
sfx_own .byte ?
tmp     .byte ?
        .endv
NITEM   = JB_NSONG + SFX_N

main:
        sei
        lda #<irq
        sta $0314
        lda #>irq
        sta $0315
        lda #$7f                ; solo l'IRQ raster (50 Hz): la tastiera la legge comunque $ea31
        sta $dc0d
        lda $dc0d
        lda #$1b
        sta $d011
        lda #250
        sta $d012
        lda #1
        sta $d01a
        lda #0
        sta cur
        sta paused
        sta sp_on
        sta sp_mute
        sta sp_mute+1
        sta sp_mute+2
        sta sfx_own
        sta sfx_t
        lda #1
        sta rpt
        lda #$ff
        sta playing
        jsr sid_clear
        cli
        lda #0
        sta $d020
        sta $d021
        lda #$17                ; minuscolo
        sta $d018
        jsr draw
.if AUTOPLAY >= 0                ; (tools/build/gen_music.py --render: suona la voce AUTOPLAY e basta)
        lda #AUTOPLAY
        sta cur
        lda #$0d
        jmp kgot
.endif
loop    jsr GETIN
        bne kgot
        lda playing             ; brano finito da solo (singolo)
        cmp #$fe
        bne loop
        lda #$ff
        sta playing
        jsr draw
        jmp loop
kgot    ldx #0
_f      cmp keys,x
        beq _go
        inx
        cpx #len(keys)
        bne _f
        beq loop
_go     txa
        asl
        tax
        lda kact+1,x
        pha
        lda kact,x
        pha
        rts
keys    .byte $91, $11, $57, $53, $0d, $20, $52, $58
kact    .word k_up-1, k_dn-1, k_up-1, k_dn-1, k_play-1, k_pause-1, k_rep-1, k_stop-1

k_up    lda cur
        beq +
        dec cur
+       jmp redraw
k_dn    lda cur
        cmp #NITEM-1
        beq +
        inc cur
+       jmp redraw
k_play  lda #0
        sta paused
        lda cur
        cmp #JB_NSONG
        bcs _sfx
        sei
        sta playing
        tax
        lda jb_slo,x
        sta sp_bl
        lda jb_shi,x
        sta sp_bh
        lda rpt
        eor #1
        sta sp_once
        jsr sid_clear
        jsr sp_start
        cli
        jmp redraw
_sfx    sbc #JB_NSONG
        sei
        jsr sfx_play
        cli
        jmp redraw
k_pause lda playing
        bmi +
        lda paused
        eor #1
        sta paused
        sei
        lda #$00                ; pausa: volume a zero (il brano resta fermo dov'e')
        ldx paused
        bne _v
        lda sp_fmode
_v      sta $d418
        cli
+       jmp redraw
k_rep   lda rpt
        eor #1
        sta rpt
        eor #1
        sta sp_once
        jmp redraw
k_stop  sei
        jsr sp_stop
        lda #$ff
        sta playing
        lda #0
        sta paused
        jsr sid_clear
        cli
redraw  jsr draw
        jmp loop

sid_clear:
        ldx #$18
        lda #0
_c      sta $d400,x
        dex
        bpl _c
        lda #$0f
        sta $d418
        rts

irq     lda #$ff
        sta $d019
        lda paused
        bne +
        jsr sp_play
        lda sp_on               ; brano finito (modo singolo)
        bne +
        lda playing
        bmi +
        cmp #JB_NSONG
        bcs +
        lda #$fe                ; segnala la fine al disegno
        sta playing
+       jsr sfx_step
        jmp $ea31

; ---------------------------------------------------------------- schermata
draw:
        ldx #0
_cl     lda #32
        sta SCR,x
        sta SCR+$100,x
        sta SCR+$200,x
        sta SCR+$2e8,x
        lda #11
        sta COL,x
        sta COL+$100,x
        sta COL+$200,x
        sta COL+$2e8,x
        inx
        bne _cl
        ldx #0
_t      lda title,x
        beq +
        sta SCR+40*0+1,x
        lda #7
        sta COL+40*0+1,x
        inx
        bne _t
+       ldx #0
_t2     lda hdr,x
        beq +
        sta SCR+40*2+1,x
        inx
        bne _t2
+       lda #0
        sta tmp
_row    lda tmp                 ; riga = ROW0 + i
        clc
        adc #ROW0
        tay
        lda rowlo,y
        sta _p+1
        sta _c+1
        lda rowhi,y
        sta _p+2
        clc
        adc #>(COL-SCR)
        sta _c+2
        lda tmp
        cmp #JB_NSONG
        bcs _isfx
        tax
        lda jb_nlo,x
        sta _s+1
        lda jb_nhi,x
        sta _s+2
        jmp _pr
_isfx   sec
        sbc #JB_NSONG
        tax
        lda sfx_nlo,x
        sta _s+1
        lda sfx_nhi,x
        sta _s+2
_pr     ldx #0                  ; colore: 1 selezionata, 5 in riproduzione, 15 altre
        ldy #15
        lda tmp
        cmp playing
        bne +
        ldy #5
+       cmp cur
        bne +
        ldy #1
+       sty _col+1
        ldy #0
_s      lda $ffff,y
        ldx tmp
        cpx cur
        bne +
        ora #$80                ; selezione in negativo
+       ldx #0
_p      sta $ffff,y
_col    lda #15
_c      sta $ffff,y
        iny
        cpy #20
        bne _s
        inc tmp
        lda tmp
        cmp #NITEM
        beq +
        jmp _row
+
        ; stato
        ldx #0
_h      lda help1,x
        beq +
        sta SCR+40*22+1,x
        lda #12
        sta COL+40*22+1,x
        inx
        bne _h
+       ldx #0
_h2     lda help2,x
        beq +
        sta SCR+40*23+1,x
        lda #12
        sta COL+40*23+1,x
        inx
        bne _h2
+       ldy #<st_stop           ; riga di stato
        lda playing
        bmi _st
        ldy #<st_play
        lda paused
        beq _st
        ldy #<st_pause
_st     ldx #0
_s2     lda stx_base,y
        sta SCR+40*24+1,x
        lda #7
        sta COL+40*24+1,x
        iny
        inx
        cpx #9
        bne _s2
        ldy #<st_single
        lda rpt
        beq +
        ldy #<st_repeat
+       ldx #0
_s3     lda stx_base,y
        sta SCR+40*24+12,x
        lda #7
        sta COL+40*24+12,x
        iny
        inx
        cpx #9
        bne _s3
        rts

rowlo   .byte <(SCR+range(25)*40+3)
rowhi   .byte >(SCR+range(25)*40+3)

        .enc "screen"
title   .text "barbarian: the blood path - sound test", 0
hdr     .text "   name           role", 0
help1   .text "up/down choose  return play  x stop", 0
help2   .text "space pause     r repeat / single", 0
        .align 256
stx_base
st_stop   = * - stx_base
        .text "stopped  "
st_play   = * - stx_base
        .text "playing  "
st_pause  = * - stx_base
        .text "paused   "
st_single = * - stx_base
        .text "single   "
st_repeat = * - stx_base
        .text "repeat   "
sfx_n0  .text "sfx swing      sfx  "
sfx_n1  .text "sfx hit        sfx  "
sfx_n2  .text "sfx hurt       sfx  "
sfx_n3  .text "sfx pick up    sfx  "
sfx_n4  .text "sfx level up   sfx  "
sfx_n5  .text "sfx death      sfx  "
sfx_n6  .text "sfx portal     sfx  "
sfx_n7  .text "sfx low hp     sfx  "
sfx_nlo .byte <(sfx_n0+range(8)*20)
sfx_nhi .byte >(sfx_n0+range(8)*20)
        .include "jukebox_songs.inc"
        .enc "none"
        .include "sid_player.inc"
        .include "sfx.inc"
