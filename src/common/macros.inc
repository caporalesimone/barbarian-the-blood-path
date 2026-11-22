; macro comuni (gioco e moduli su file)
at      .macro
        ldx #\1
        ldy #\2
        jsr ui_at
        .endm

; (21/11 sera, richiesta del committente) TESTO A 5 BIT (docs/wiki/tecnica.md, "Testo a 5 bit"): ogni carattere e' un simbolo di
; 5 bit, 3 simboli per parola di 16 bit (byte alto prima; il bit 15 non si usa). Simboli: 0 = fine, 1..26 = lettere (codice
; schermo = simbolo), 27 spazio, 28 ':', 29 '.', 30 '/', 31 = cambio: il simbolo dopo e' l'indice nella tabella T5X (cifre e
; segni rari). Regola del committente: il testo a 5 bit nel codice si scrive SEMPRE leggibile, come argomento delle macro
; (#msg "testo", #t5 "testo"); la macro lo codifica. Decodificatore: d5_get in src/game/ui.asm (ui_pi, ui_puts5).
t5      .macro
T5X     := "0123456789?-+!,'()>%$" ; ('$' = moneta CH_COIN, 22/11) (dentro la macro: macros.inc si include anche nei moduli assemblati con game.lbl)
_s      := \1
_y      := []
        .for _i = 0, _i < len(_s), _i += 1
_c      := _s[_i] + 0
        .if _c >= 1 && _c <= 26
_y      := _y .. [_c]
        .elsif _c == $20
_y      := _y .. [27]
        .elsif _c == ":" + 0
_y      := _y .. [28]
        .elsif _c == "." + 0
_y      := _y .. [29]
        .elsif _c == "/" + 0
_y      := _y .. [30]
        .else
_k      := -1
        .for _j = 0, _j < len(T5X), _j += 1
        .if T5X[_j] + 0 == _c
_k      := _j
        .endif
        .next
        .cerror _k < 0, "testo a 5 bit: carattere non previsto in ", \1, " (aggiungerlo a T5X in macros.inc e a d5_t2)"
_y      := _y .. [31, _k]
        .endif
        .next
_y      := _y .. [0]
        .while len(_y) % 3 != 0
_y      := _y .. [0]
        .endwhile
        .for _i = 0, _i < len(_y), _i += 3
_w      := _y[_i] * 1024 + _y[_i + 1] * 32 + _y[_i + 2]
        .byte >_w, <_w
        .next
        .endm

; stringa in linea dopo la JSR (21/11 sera: a 5 bit; l'argomento e' il testo leggibile)
msg     .macro
        jsr ui_pi
        #t5 \1
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
