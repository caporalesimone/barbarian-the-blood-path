; =============================================================================
; BARBARIAN - il loader: primo file del disco (LOAD"BARBARIAN",8 + RUN). Avvia gli altri programmi con il
; trampoline (src/common/tramp.inc, nel buffer della cassetta).
; Release (MENU=1): menu con tre voci
;   hear the legend       -> LORE (titolo, musica, la storia a scorrimento; alla fine torna qui)
;   read the game manual  -> HELP (il manuale: tasti, schermate, HUD; alla fine torna qui)
;   walk the blood path   -> START (avvio del gioco: titolo, musica, PRESS SPACE, menu degli eroi)
;   Piccolo apposta: schermo a caratteri con il font del gioco (codici 0-63 di out/work/gfx/uifont.bin, copiati a $3800),
;   gira con l'IRQ del KERNAL e suona Demon's Eye (15/11, TODO E3/E4: stesso brano di START, LORE, LOBBY e HELP) con il player unico
;   (src/common/title_music.inc): clock = CIA1 timer A a 19656 cicli (50 Hz PAL), vettore $0314 proprio; prima di ogni LOAD del
;   KERNAL (il trampolino sovrascrive questo programma) si ferma tutto (tm_stop) e IRQ, CIA e SID tornano come prima. Tasti: joystick 2 su/giu' e fire, oppure 1 2 3,
;   W/S o joystick (09/11: niente tasti cursore), spazio/RETURN.
; (11/11) Un solo disco: con POKE 1020,1 prima del RUN (POKE_SKIP) niente menu, si carica subito START (sviluppo, test).
; =============================================================================
        .cpu "6502"
        .include "version.inc"
        .include "vic_init.inc" ; (11/11, O13) #vic_text_init
        .weak
MENU    = 1                     ; 1 = release (menu), 0 = debug (carica subito START)
        .endweak
SCR     = $0400
FONT    = $3800                 ; (12/11) sopra i programmi che il trampoline carica (LORE fino a $2B3D): durante
                                ; il caricamento lo schermo resta leggibile (a $2000 LORE e START lo coprivano)
GETIN   = $ffe4
;@map $0400..$07e8 "Schermo del menu"
.if MENU
SP_VARS = $c000                 ; variabili del player (RAM libera: BARBARIAN sta sotto $3800)
;@map SP_VARS..SP_VEND "Variabili del player SID (Demon's Eye, src/common/title_music.inc)"
.endif
;@map FONT+512 "Font del menu: codici 0-63 del font del gioco (uifont.bin), sopra i programmi che il trampoline carica"
NITEM   = 4                     ; (16/11) la quarta voce, exit game, torna al BASIC
ROW0    = 11                    ; riga della prima voce
LOGO_X  = (40 - LOGO_W) / 2     ; il logo della copertina (out/work/logo.inc, tools/build/gen_lore.py), righe 1..6
LOGO_Y  = 1
ICOL    = 9                     ; colonna delle voci
IW      = 23                    ; larghezza della voce colorata
TXT_ROW = 10                    ; riga della frase di attesa (come START, boot.asm)
COL_T   = 7                     ; giallo: titoli e voce scelta
COL_N   = 1                     ; bianco: voci (colori < 8: lo schermo e' multicolore per il logo)
COL_D   = 3                     ; ciano: righe di aiuto

        * = $0801
        .word _nl, 10
        .byte $9e
        .text "2061"
        .byte 0
_nl     .word 0
        ; $080D (anche il ritorno da LORE e HELP, tramp.inc)
        lda POKE_SKIP           ; (11/11) POKE 1020,1 prima del RUN: subito START, senza il menu (docs/wiki/cheats.md)
        beq +
        lda #nm_game_n          ; POKE 1020: subito START
        ldx #<nm_game
        ldy #>nm_game
        jmp tramp_run
+
.if MENU
        #vic_text_init          ; (src/common/vic_init.inc)
        lda #$1e                ; schermo $0400, charset $3800
        sta $d018
        lda #$18                ; multicolore (per il logo; il testo ha colori < 8: alta risoluzione), 40 colonne
        sta $d016
        lda #LOGO_MC1
        sta $d022
        lda #LOGO_MC2
        sta $d023
        ldx #0                  ; font (512 byte) -> FONT
_f      lda font_d,x
        sta FONT,x
        lda font_d+256,x
        sta FONT+256,x
        inx
        bne _f
        lda #<logo_cs           ; forme del logo -> codici 64.. (FONT + $200)
        sta $fb
        lda #>logo_cs
        sta $fc
        lda #<(FONT + 64 * 8)
        sta $fd
        lda #>(FONT + 64 * 8)
        sta $fe
        ldx #>(LOGO_N * 8 + 255)
        ldy #0
_lc     lda ($fb),y
        sta ($fd),y
        iny
        bne _lc
        inc $fc
        inc $fe
        dex
        bne _lc
        lda #0
        sta sel
        jsr draw_menu
        lda #$1b
        sta $d011
        jsr tm_start            ; Demon's Eye (clock a 50 Hz PAL, vettore IRQ proprio; torna con l'I flag acceso)
        cli

; un fotogramma del menu del loader: tasti 1-3 (scelta diretta), W/S o joystick (voce), Fire/RETURN/spazio (scegli)
loop:
        jsr wait_frame
        jsr GETIN               ; tastiera (IRQ del KERNAL)
        beq _joy
        cmp #"1"
        bcc _k
        cmp #"1" + NITEM
        bcs _k
        sec
        sbc #"1"
        sta sel
        jsr draw_sel
        jmp choose
_k      cmp #$0d                ; RETURN
        beq choose
        cmp #" "
        beq choose
        cmp #"W"
        beq up
        cmp #"S"
        beq down
_joy    lda $dc00               ; joystick 2: su (bit 0), giu' (bit 1), fire (bit 4); attivo basso
        eor #$ff
        and #$13
        tax
        eor jprev               ; solo i cambi (nuova pressione)
        stx jprev
        and jprev
        beq loop
        lsr
        bcs up
        lsr
        bcs down
        jmp choose
; voce sopra / sotto (senza giro)
up      lda sel
        beq loop
        dec sel
        jsr draw_sel
        jmp loop
down    lda sel
        cmp #NITEM - 1
        bcs loop
        inc sel
        jsr draw_sel
        jmp loop

choose:                         ; (15/11, committente) qualunque voce: SUBITO lo schermo nero (prima solo la storia;
        jsr tm_stop             ; (15/11, TODO E3/E4) silenzio e IRQ/CIA/SID come prima: il LOAD del KERNAL sovrascrive questo programma
        ldx sel                 ; (16/11, committente) 4 exit game: si torna al BASIC (il "commodore")
        cpx #3
        bne _go
        sei                     ; stato della macchina come all'accensione (CIA, vettori, schermo), poi avvio a caldo del BASIC
        jsr $ff84               ; IOINIT
        jsr $ff8a               ; RESTOR
        jsr $ff81               ; CINT (VIC, schermo, colori)
        cli
        jmp ($a002)             ; vettore di avvio a caldo del BASIC: "READY."
_go
        ldx #0                  ;  manuale e gioco scrivevano la frase sul menu e il nero arrivava dopo, col programma)
        lda #$20
_cl     sta SCR,x
        sta SCR+$100,x
        sta SCR+$200,x
        sta SCR+$2e8,x
        inx
        bne _cl
_m      ldx sel                 ; la frase resta sullo schermo durante il caricamento
        lda msg_lo,x
        sta $fb
        lda msg_hi,x
        sta $fc
        jsr print_all
        ldx sel
        lda nm_n,x
        pha
        lda nm_lo,x
        ldy nm_hi,x
        tax
        pla
        jmp tramp_run

; schermo del menu: logo, testi, voci
draw_menu:
        jsr cls
        ldx #0                  ; logo: LOGO_H righe da LOGO_W
_lr     stx pr_x
        lda row_lo+LOGO_Y,x
        clc
        adc #LOGO_X
        sta $fd
        lda row_hi+LOGO_Y,x
        adc #0
        sta $fe
        ldy #LOGO_W - 1
_lw     lda (lg_p),y
        sta ($fd),y
        dey
        bpl _lw
        lda $fe
        clc
        adc #>($d800 - SCR)
        sta $fe
        ldy #LOGO_W - 1
_lk     lda (lg_q),y
        sta ($fd),y
        dey
        bpl _lk
        lda lg_p
        clc
        adc #LOGO_W
        sta lg_p
        bcc +
        inc lg_p+1
+       lda lg_q
        clc
        adc #LOGO_W
        sta lg_q
        bcc +
        inc lg_q+1
+       ldx pr_x
        inx
        cpx #LOGO_H
        bne _lr
        lda #<texts             ; testi fissi: x, y, colore, testo, 0 ... $ff
        sta $fb
        lda #>texts
        sta $fc
        jsr print_all
        jmp draw_sel

; schermo vuoto, colori a 0; puntatori del logo all'inizio
cls     ldx #0
_c      lda #32
        sta SCR,x
        sta SCR+$100,x
        sta SCR+$200,x
        sta SCR+$2e8,x
        lda #0
        sta $d800,x
        sta $d900,x
        sta $da00,x
        sta $dae8,x
        inx
        bne _c
        lda #<logo_ch
        sta lg_p
        lda #>logo_ch
        sta lg_p+1
        lda #<logo_co
        sta lg_q
        lda #>logo_co
        sta lg_q+1
        rts
lg_p    = $02                   ; (2) puntatore alle celle del logo (pagina zero libera: il BASIC non gira)
lg_q    = $04                   ; (2) puntatore ai colori del logo

wait_frame:
-       lda $d011               ; attende la riga 250 (una volta per fotogramma)
        bmi -
-       lda $d012
        cmp #250
        bne -
        rts

; voci: la scelta in giallo con la freccia, le altre in grigio
draw_sel:
        ldx #0
_d      txa
        asl
        clc
        adc #ROW0
        tay                     ; riga = ROW0 + 2*voce
        lda row_lo,y
        sta $fb
        lda row_hi,y
        sta $fc
        lda row_hi,y            ; colore: stessa riga in $D800
        clc
        adc #>($d800 - SCR)
        sta $fe
        lda $fb
        sta $fd
        lda #COL_N
        sta _col
        lda #32
        sta _arw
        cpx sel
        bne +
        lda #COL_T
        sta _col
        lda #62                 ; ">"
        sta _arw
+       ldy #ICOL - 2           ; freccia due colonne prima della voce, poi la voce (IW colonne)
        lda _arw
        sta ($fb),y
        lda #COL_T
        sta ($fd),y
        ldy #ICOL
        lda _col
-       sta ($fd),y
        iny
        cpy #ICOL + IW
        bne -
        inx
        cpx #NITEM
        bne _d
        rts
_col    .byte 0
_arw    .byte 0

; testi: x, y, colore, caratteri (codici schermo), 0; fine con $ff
print_all:
        ldy #0
        lda ($fb),y
        cmp #$ff
        bne +
        rts
+       sta pr_x
        iny
        lda ($fb),y
        tax
        iny
        lda ($fb),y
        sta pr_c
        lda row_lo,x
        clc
        adc pr_x
        sta $fd
        lda row_hi,x
        adc #0
        sta $fe
        lda #3
        jsr adv
        ldy #0
-       lda ($fb),y
        beq _e
        sta ($fd),y
        lda $fe                 ; colore nella stessa posizione di $D800
        pha
        clc
        adc #>($d800 - SCR)
        sta $fe
        lda pr_c
        sta ($fd),y
        pla
        sta $fe
        iny
        bne -
_e      iny
        tya
        jsr adv
        jmp print_all
; A = byte da saltare: ($FB) += A
adv     clc
        adc $fb
        sta $fb
        bcc +
        inc $fc
+       rts
pr_x      .byte 0
pr_c     .byte 0

row_lo  .for r = 0, r < 25, r += 1
        .byte <(SCR + r * 40)
        .next
row_hi  .for r = 0, r < 25, r += 1
        .byte >(SCR + r * 40)
        .next

sel     .byte 0
jprev   .byte 0

        .enc "screen"
texts   .byte 6, 8, COL_D
        .text "---------------------------", 0       ; (16/11) 27 trattini: la larghezza del logo (LOGO_W)
        .byte ICOL, ROW0, COL_N
        .text "1  hear the legend", 0
        .byte ICOL, ROW0 + 2, COL_N
        .text "2  read the game manual", 0
        .byte ICOL, ROW0 + 4, COL_N
        .text "3  walk the blood path", 0
        .byte ICOL, ROW0 + 6, COL_N
        .text "4  exit game", 0
        .byte 13, 19, COL_D
        .text "fire to choose", 0         ; (12/11, committente: solo questo)
        .byte VER_LX, 22 - 1, COL_D
        .text "version ", VERSION, " - loader by krill ", KRILL_VER, 0
        .byte 4, 23, COL_D
        .text "copyright 2026 - simone caporale", 0
        .byte $ff
; frasi a schermo nero (16/11, committente): identiche alla schermata di attesa di START (txt_init in boot.asm: frase centrata
; in riga 10, gialla; "please wait" in riga 13, bianco), cosi' il passaggio da BARBARIAN a START non cambia lo schermo.
; Anche per storia e manuale. Colonna = (40 - lunghezza) / 2.
msg_lore .byte 6, TXT_ROW, COL_T
        .text "the old ones begin to speak", 0
        .byte 14, TXT_ROW + 3, COL_N
        .text "please wait", 0
        .byte $ff
msg_man .byte 9, TXT_ROW, COL_T
        .text "the old scroll unrolls", 0
        .byte 14, TXT_ROW + 3, COL_N
        .text "please wait", 0
        .byte $ff
msg_game .byte 7, TXT_ROW, COL_T
        .text "the crypt door creaks open", 0
        .byte 14, TXT_ROW + 3, COL_N
        .text "please wait", 0
        .byte $ff
msg_lo  .byte <msg_lore, <msg_man, <msg_game
msg_hi  .byte >msg_lore, >msg_man, >msg_game

.endif
        .enc "none"
nm_lore .text "lore"
nm_lore_n = * - nm_lore
nm_game .text "start"
nm_game_n = * - nm_game
.if MENU
nm_help .text "help"
nm_help_n = * - nm_help
nm_n    .byte nm_lore_n, nm_help_n, nm_game_n
nm_lo   .byte <nm_lore, <nm_help, <nm_game
nm_hi   .byte >nm_lore, >nm_help, >nm_game
.endif

        .include "tramp.inc"
POKE_SKIP = $03fc               ; byte libero dopo il buffer della cassetta (trampoline < $03FC), 0 all'accensione

.if MENU
        .include "title_music.inc"      ; Demon's Eye con il player unico (tm_start / tm_stop)
font_d  .binary "../out/work/gfx/uifont.bin", 0, 512
        .include "logo.inc"     ; out/work/logo.inc (tools/build/gen_lore.py): forme, celle e colori del logo
.endif
.if MENU
bar_end
        .cerror bar_end > FONT, "BARBARIAN oltre il font ($3800)"
.endif
