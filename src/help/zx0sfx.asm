; =============================================================================
; HELP compresso (12/11, TODO M5b): il file HELP sul disco e' questo programma, lungo meno della meta' di out/help.prg.
; BARBARIAN lo carica con il KERNAL (tramp.inc) a $0801 e salta a $080D: qui il decompressore si copia a SFX_AT
; insieme ai dati ZX0 (out/help.zx0, tools/build/pack.py --help), decomprime HELP a $0801 e salta al suo $080D.
; Il KERNAL legge ~14 blocchi invece di 32: l'attesa del manuale si accorcia (la decompressione costa una frazione).
; =============================================================================
        .cpu "6502"
ZX_ZP   = $02                   ; 12 byte di pagina zero: HELP non e' ancora partito, BASIC non serve
SFX_AT  = $8000                 ; RAM libera per HELP (codice $0801-$27xx, charset $3000, schermo $0400)

        * = $0801
        .word _nl, 10
        .byte $9e
        .text "2061"
        .byte 0
_nl     .word 0
        ; $080D: copia il blocco alto (decompressore + dati) a SFX_AT, poi lo esegue
        sei
        lda #<hi_img
        sta $fb
        lda #>hi_img
        sta $fc
        lda #<SFX_AT
        sta $fd
        lda #>SFX_AT
        sta $fe
        ldx #>(hi_len + 255)
        ldy #0
_c      lda ($fb),y
        sta ($fd),y
        iny
        bne _c
        inc $fc
        inc $fe
        dex
        bne _c
        jmp SFX_AT

hi_img:
        .logical SFX_AT
        lda #<zdata
        sta zx_src
        lda #>zdata
        sta zx_src+1
        lda #<$0801
        sta zx_dst
        lda #>$0801
        sta zx_dst+1
        jsr zx0_unpack
        cli
        jmp $080d               ; HELP (dopo il suo stub BASIC)
        .include "zx0.inc"
zdata   .binary "help.zx0"
        .endlogical
hi_len = * - hi_img
        .cerror SFX_AT + hi_len > $a000, "HELP compresso oltre $A000"
        .cerror hi_img + hi_len > SFX_AT, "il blocco alto si sovrappone a SFX_AT: la copia in avanti lo rovinerebbe"
