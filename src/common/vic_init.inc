; (11/11, O13) avvio comune dei programmi a schermo di testo (loader BARBARIAN, manuale HELP): niente cursore del
; KERNAL, BASIC escluso, colori neri, sprite spenti, schermo spento durante la preparazione, banco VIC 0.
; Lascia gli interrupt disattivati (sei). Dopo: $d018/$d016 e i colori propri del programma.
vic_text_init .macro
        sei
        lda #1                  ; niente cursore lampeggiante del KERNAL
        sta $cc
        lda #$36                ; BASIC escluso, KERNAL e I/O
        sta $01
        lda #0
        sta $d020
        sta $d021
        sta $d015
        lda #$0b                ; schermo spento mentre si prepara
        sta $d011
        lda $dd02               ; banco VIC 0
        ora #3
        sta $dd02
        lda $dd00
        ora #3
        sta $dd00
.endm
