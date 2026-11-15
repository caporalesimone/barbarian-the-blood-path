; =============================================================================
; Pagina di attesa prima di ricaricare BARBARIAN (16/11, richiesta del committente): LORE, HELP e LOBBY ("back to main menu")
; mostrano una frase e "please wait" mentre il trampoline (tramp.inc) ricarica il menu iniziale; prima lo schermo restava nero
; (LORE e HELP) o mostrava la pagina del gioco, che con il banco VIC 2 sparisce con IOINIT (LOBBY).
; Pagina sempre in banco VIC 0, schermo $0400, charset $3800 (copiato qui, 512 byte del font della UI): sopravvive a IOINIT
; e a RESTOR del trampoline, e BARBARIAN la sovrascrive appena parte.
; Ingresso: ($fb) = tabella dei messaggi (indirizzo sullo schermo lo/hi, colore, testo in codici schermo, 0; fine con un indirizzo di pagina 0: due byte a 0), ($fd) = font (512 byte,
; codici 0-63 di out/work/gfx/uifont.bin). Interrupt e raster IRQ spenti, sprite spenti. Distrugge A, X, Y, $fb-$fe.
; =============================================================================
wm_show:
        sei
        lda #0
        sta $d01a               ; niente raster IRQ
        sta $d015               ; niente sprite
        sta $d011               ; schermo spento mentre si prepara
        sta $d020
        sta $d021
        lda #3
        sta $dd00               ; banco VIC 0 (con Krill i 6 bit alti di $DD00 stanno a 0)
        ldy #0
_f1     lda ($fd),y             ; font -> $3800
        sta $3800,y
        iny
        bne _f1
        inc $fe
_f2     lda ($fd),y
        sta $3900,y
        iny
        bne _f2
        ldx #0
_fl     lda #$20                ; schermo vuoto, colore bianco
        sta $0400,x
        sta $0500,x
        sta $0600,x
        sta $06e8,x
        lda #1
        sta $d800,x
        sta $d900,x
        sta $da00,x
        sta $dae8,x
        inx
        bne _fl
_pl     ldy #0
        lda ($fb),y             ; indirizzo sullo schermo (lo, hi); fine tabella: hi = 0
        sta $fd
        iny
        lda ($fb),y
        beq _done
        sta $fe
        iny
        lda ($fb),y             ; colore
        sta wm_c
        lda $fb                 ; al testo
        clc
        adc #3
        sta $fb
        bcc +
        inc $fc
+       ldy #0
_ch     lda ($fb),y
        beq _en
        sta ($fd),y
        lda $fe                 ; colore nella stessa posizione di $D800 (+ $D4 sulla pagina alta)
        clc
        adc #$d4
        sta $fe
        lda wm_c
        sta ($fd),y
        lda $fe
        sec
        sbc #$d4
        sta $fe
        iny
        bne _ch
_en     iny                     ; oltre lo 0 finale
        tya
        clc
        adc $fb
        sta $fb
        bcc _pl
        inc $fc
        bne _pl
_done   lda #$1e                ; schermo $0400, charset $3800
        sta $d018
        lda #$08                ; testo normale (niente multicolore)
        sta $d016
        lda #$1b
        sta $d011
        rts
wm_c    .byte 0
