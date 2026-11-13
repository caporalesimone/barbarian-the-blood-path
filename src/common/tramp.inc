; =============================================================================
; Trampoline: carica un altro programma del disco (PRG all'indirizzo del file, $0801) e lo avvia a $080D.
; Usato dal loader BARBARIAN (src/barbarian.asm: LORE, START) e da LORE (src/lore/scroll.asm: ritorno a BARBARIAN).
; Il codice si copia nel buffer della cassetta ($0334) perche' il programma nuovo si carica sopra quello che chiama.
; Rimette il sistema come all'accensione per il KERNAL: IOINIT (CIA, banco VIC 0, $01 = $37, SID muto) e RESTOR
; (vettori $0314-$0333). Lo schermo resta com'e': chi chiama decide se lasciarlo acceso (messaggio "loading").
; Ingresso: A = lunghezza del nome, X/Y = indirizzo del nome (PETSCII). Non ritorna.
; =============================================================================
TRAMP_AT = $0334
tramp_run:
        sei
        sta tr_n
        stx $fb
        sty $fc
        ldx #tramp_len - 1
_tc     lda tramp_img,x
        sta TRAMP_AT,x
        dex
        bpl _tc
        ldy tr_n
        sty tr_len
        dey
_tn     lda ($fb),y
        sta tr_name,y
        dey
        bpl _tn
        jmp TRAMP_AT
tr_n    .byte 0

tramp_img:
        .logical TRAMP_AT
        jsr $ff84               ; IOINIT
        jsr $ff8a               ; RESTOR
        lda #0
        sta $9d                 ; niente messaggi del KERNAL (SEARCHING, LOADING) sullo schermo
        cli
_ld     lda tr_len
        ldx #<tr_name
        ldy #>tr_name
        jsr $ffbd               ; SETNAM
        lda #1
        ldx #8
        ldy #1                  ; all'indirizzo del file
        jsr $ffba               ; SETLFS
        lda #0
        jsr $ffd5               ; LOAD
        bcs _err
        jmp $080d               ; dopo lo stub BASIC (SYS 2061)
_err    cmp #0                  ; (12/11) A = 0: RUN/STOP durante il LOAD del KERNAL ($F633): si torna al menu
        bne _red                ; (BARBARIAN), prima restava il bordo rosso fisso
        ldx #tr_bbn - 1
-       lda tr_bb,x
        sta tr_name,x
        dex
        bpl -
        lda #tr_bbn
        sta tr_len
        jmp _ld
_red    lda #2                  ; file mancante o errore di disco: bordo rosso fisso
        sta $d020
        jmp _red
tr_bb   .text "barbarian"
tr_bbn  = * - tr_bb
tr_len  .byte 0
tr_name .fill 16
        .endlogical
tramp_len = * - tramp_img
        .cerror TRAMP_AT + tramp_len > $03fc, "trampoline oltre il buffer della cassetta"
