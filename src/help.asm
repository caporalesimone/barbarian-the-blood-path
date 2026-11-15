; =============================================================================
; HELP - il manuale del gioco (file HELP sul disco, solo release): voce "read the game manual" del loader BARBARIAN.
; Programma a se': non tocca il gioco (ne' RAM ne' tempo di CPU di GAME). Alla fine torna a BARBARIAN (trampoline).
; Pagine a tutto schermo generate da tools/build/gen_help.py (data/help.txt) in out/work/help.inc: schermo e colori in RLE,
; charset = font della UI (codici 0-63, out/work/gfx/uifont.bin) + i glifi dell'HUD fotografato dal gioco (codici 64..,
; data/help_hud.json) per il ritaglio dell'HUD. Schermo multicolore: il testo ha colori < 8 (alta risoluzione), il
; ritaglio dell'HUD i suoi colori, con $D022/$D023 del tema fotografato.
; Tasti (09/11: ci si muove solo con joystick o WASD, niente tasti cursore): fire / spazio / RETURN / destra / D =
; pagina seguente (dall'ultima: la prima, 16/11; prima si usciva); sinistra / A / DEL = pagina precedente; RUN/STOP o freccia a sinistra = di nuovo il loader.
; Gira con l'IRQ del KERNAL (tastiera con GETIN) e suona Demon's Eye (15/11, TODO E4: stesso brano del titolo e del menu) con il
; player unico (src/common/title_music.inc, variabili a SP_VARS): clock = CIA1 timer A a 19656 cicli (50 Hz PAL esatti), non il
; passo del KERNAL; il vettore IRQ torna com'era (tm_stop) prima di tornare al loader.
; =============================================================================
        .cpu "6502"
SCR     = $0400
CHARS   = $3000                 ; charset (font 512 B + glifi dell'HUD): $D018 = $1C
GETIN   = $ffe4
;@map $0400..$07e8 "Schermo del manuale"
;@map CHARS..$3800 "Charset del manuale: font della UI (512 B) + glifi dell'HUD ($D018 = $1C)"
pg      = $02                   ; pagina attuale
jprev   = $03                   ; joystick al fotogramma precedente
src     = $fb                   ; (2) flusso RLE
dst     = $fd                   ; (2) destinazione
SP_VARS = $c000                 ; variabili del player (RAM libera: l'help non usa altro sopra $3800)
;@map SP_VARS..SP_VEND "Variabili del player SID (Demon's Eye, src/common/title_music.inc)"

        .include "vic_init.inc" ; (11/11, O13) #vic_text_init (solo una macro: nessun byte)
        * = $0801
        .word _nl, 10
        .byte $9e
        .text "2061"
        .byte 0
_nl     .word 0
        ; $080D
        #vic_text_init          ; (src/common/vic_init.inc)
        lda #0
        sta pg
        lda #$1c                ; schermo $0400, charset $3000
        sta $d018
        lda #$18                ; multicolore (per il ritaglio dell'HUD), 40 colonne
        sta $d016
        lda #HELP_D022
        sta $d022
        lda #HELP_D023
        sta $d023
        ldx #0                  ; font della UI (512 B) -> $3000
_f      lda font_d,x
        sta CHARS,x
        lda font_d+256,x
        sta CHARS+256,x
        inx
        bne _f
        ldx #0                  ; glifi dell'HUD -> codici 64..
_g      lda help_glyphs,x
        sta CHARS+64*8,x
        inx
        cpx #<(HELP_NG*8)
        bne _g
        .cerror HELP_NG*8 > 256, "glifi dell'HUD oltre 256 byte: allargare la copia"
        lda $dc00
        eor #$ff
        and #$1c
        sta jprev               ; fire gia' premuto nel loader: non conta
        jsr tm_start            ; Demon's Eye (clock a 50 Hz PAL, vettore IRQ proprio)
        cli
show    jsr draw_page

loop    jsr wait_frame
        jsr GETIN
        beq _joy
        cmp #$03                ; RUN/STOP
        beq quit
        cmp #$5f                ; freccia a sinistra
        beq quit
        cmp #$0d                ; RETURN
        beq next
        cmp #" "
        beq next
        cmp #"D"
        beq next
        cmp #"A"
        beq prev
        cmp #$14                ; DEL
        beq prev
_joy    lda $dc00               ; joystick 2: sinistra (bit 2), destra (bit 3), fire (bit 4); attivo basso
        eor #$ff
        and #$1c
        tax
        eor jprev               ; solo le nuove pressioni
        stx jprev
        and jprev
        beq loop
        and #$04
        bne prev
        beq next

next    ldx pg
        inx
        cpx #HELP_NP
        bcc +
        ldx #0                  ; (16/11, committente) dall'ultima pagina si torna alla prima; si esce solo con RUN/STOP
+       stx pg
        jmp show
prev    ldx pg
        beq loop
        dex
        stx pg
        jmp show

quit    jsr tm_stop             ; sei, silenzio, IRQ e CIA come prima: prima del LOAD del KERNAL
        lda #$0b
        sta $d011
        lda #nm_front_n
        ldx #<nm_front
        ldy #>nm_front
        jmp tramp_run

; pagina pg: schermo spento, RLE dello schermo ($0400) e dei colori ($D800), schermo acceso
draw_page:
        lda #$0b
        sta $d011
        ldx pg
        lda help_plo,x
        sta src
        lda help_phi,x
        sta src+1
        lda #>SCR
        jsr unrle
        lda #$d8
        jsr unrle
        jsr wait_frame
        lda #$1b
        sta $d011
        rts

; RLE: coppie (conteggio, valore) fino al conteggio 0; A = pagina alta della destinazione
unrle   sta dst+1
        lda #0
        sta dst
_r      ldy #0
        lda (src),y
        beq _end
        tax
        iny
        lda (src),y
        ldy #0
_w      sta (dst),y
        iny
        dex
        bne _w
        tya                     ; dst += conteggio
        clc
        adc dst
        sta dst
        bcc +
        inc dst+1
+       lda src
        clc
        adc #2
        sta src
        bcc _r
        inc src+1
        bne _r
_end    inc src                 ; salta lo 0 finale
        bne +
        inc src+1
+       rts

wait_frame
_w1     lda $d011               ; attende la riga 255 (uno per fotogramma)
        bpl _w1
_w2     lda $d011
        bmi _w2
        rts

        .enc "none"
nm_front .text "barbarian"
nm_front_n = * - nm_front

        .include "tramp.inc"
        .include "title_music.inc"      ; Demon's Eye con il player unico

font_d  .binary "../out/work/gfx/uifont.bin", 0, 512
        .include "help.inc"     ; out/work/help.inc (tools/build/gen_help.py): glifi dell'HUD e pagine
help_end
        .cerror help_end > CHARS, "HELP oltre $3000 (charset)"
