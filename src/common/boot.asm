; =============================================================================
; Avvio con musica: il codice comune di START (src/start.asm) e LORE (src/lore.asm, LORE=1), file START e LORE.
; (11/11 sera) Entrambi installano Krill's Loader e leggono i file con loadraw (docs/FastLoader.md).
; -----------------------------------------------------------------------------
; 1. lo stub BASIC copia il corpo a $A000 (RAM sotto la ROM del BASIC) e lo esegue: install di Krill (KERNAL acceso),
;    residente a $0200, poi la musica (IRQ raster).
; 2. START: schermata di attesa a caratteri (txt_init), GAME (ZX0, decompresso sul posto in $0400),
;    LOBBY ($C000), elenco eroi (hl), segnali in LDFLAGS / CHRPRE e salto al gioco ($0400, GAME_ENTRY).
;    LORE: TITLE in un buffer e LDAT, il titolo compare riga per riga dal buffer, poi PRESS / SPACE (sprite, 2 righe
;    con multiplexing) e la storia (src/lore/scroll.asm).
; Memoria: il VIC lavora nel banco 3 (schermo $CC00, bitmap o font a $E000); sprite delle lettere a $DD00-$DE7F (RAM
; sotto l'I/O); LOBBY fino a $CBFF.
; =============================================================================
        .cpu "6502"
        .weak
INTRO   = 1                     ; 1 = release (titolo, musica, PRESS SPACE); 0 = sviluppo (solo i file)
LORE    = 0                     ; 1 = programma LORE: titolo + LDAT, poi la storia a scorrimento (src/lore.asm)
TITLE   = 1                     ; con INTRO: 1 = titolo e PRESS SPACE; 0 = schermata di attesa e poi subito il gioco
                                ; (START di release dal 07/11: "walk the blood path" va dritto al menu del gioco)
        .endweak
        .cerror LORE && !TITLE, "LORE richiede il titolo"
TXT     = INTRO && !TITLE       ; START: schermata di attesa a caratteri (banco 3: schermo $CC00, font $E000)
TXT_ROW = 10                    ; riga del testo; "please wait" 3 righe sotto
        .cerror LORE && !INTRO, "LORE richiede INTRO"

SETNAM  = $ffbd
SETLFS  = $ffba
OPEN    = $ffc0
CLOSE   = $ffc3
CHKIN   = $ffc6
CLRCHN  = $ffcc
CHRIN   = $ffcf
CHKOUT  = $ffc9
CHROUT  = $ffd2
ST      = $90

LDFLAGS = $8e                   ; 1 = LOBBY gia' a $C000 (11/11: pagina zero, il residente di Krill occupa $0200-$0312)
CHRPRE  = $8f                   ; 1 = elenco eroi (file hl) gia' letto, in CHRBUF (lobby.asm)
POKE_GOD = $03fd                ; (11/11) POKE 1021,1 prima del RUN = god mode (docs/cheats.md); letto prima dell'install
        .include "krill.inc"    ; out/work/krill.inc (tools/build/krill_syms.py): START e LORE installano Krill's Loader r194
CHRTMP  = TXT ? $b800 : $b000                 ; durante il caricamento: stato (1 = letto) + file hl (elenco eroi)
CHRBUF  = $d000                 ; dopo SPAZIO (RAM sotto l'I/O, liberata dal villaggio)
HDR_N   = 1 + 5 + 5*12          ; versione + eroi presenti + 5 nomi da 12
SPR_AT  = $dd00                 ; 6 sprite (P R E S A C) nella RAM sotto l'I/O: $C000-$CBFF resta
                                ; al LOBBY. Puntatore VIC = ($DD00-$C000)/64
SPRP    = (SPR_AT - $c000) / 64
TITLE_U = 250                   ; blocchi da 40 byte del titolo (25 righe x (schermo, colore, 8 righe))

PS_X    = 114                   ; PRESS / SPACE: 5 lettere ogni 28 pixel
ROW1_Y  = 172                   ; PRESS (centro dell'onda; era 188)
ROW2_Y  = 220                   ; SPACE (era 224)
SIN_A   = 7                     ; ampiezza dell'onda (ld_sin: -7..+7, tools/build/gen_start.py SIN_A)
IRQ_BOT = 250                   ; IRQ nel bordo basso: musica (e prima riga di PRESS / SPACE)
IRQ_MID = ROW1_Y + SIN_A + 22   ; IRQ fra le due righe (solo PRESS / SPACE): sotto l'ultima riga di PRESS
        ; l'IRQ di meta' riscrive le 5 Y di SPACE in ~3 righe raster (piu' la latenza): almeno 8 righe di margine
        ; sopra il punto piu' alto di SPACE, altrimenti una lettera gia' iniziata si "ripete" (la linea vista sulla A)
        .cerror ROW2_Y - SIN_A - IRQ_MID < 8, "PRESS e SPACE troppo vicine per il multiplexing"
        .cerror ROW2_Y + SIN_A + 21 > IRQ_BOT - 2, "SPACE troppo vicina all'IRQ del bordo basso"
; LDCOL (riga di comando, tools/build/asm.sh): tavolozza di PRESS SPACE (0 sangue, 1 oro antico, 2 acciaio: tools/build/gen_start.py)

zp0     = $fb                   ; puntatori del programma principale
zp1     = $fd

        * = $0801
        .word _nl, 10
        .byte $9e
        .text "2061"
        .byte 0
_nl     .word 0
        sei                     ; $080D
        lda #$36                ; ROM del BASIC esclusa: il corpo gira a $A000
        sta $01
        lda #<body
        sta zp0
        lda #>body
        sta zp0+1
        lda #<main
        sta zp1
        lda #>main
        sta zp1+1
        ldx #>(body_end - main + 255)
        ldy #0
_cp     lda (zp0),y
        sta (zp1),y
        iny
        bne _cp
        inc zp0+1
        inc zp1+1
        dex
        bne _cp
        jmp main
; codice di installazione di Krill (eseguito una volta da main, poi la RAM torna libera: GAME / LDAT la sovrascrivono)
        .cerror * > krill_install, "stub di START oltre l'indirizzo dell'install di Krill (tools/build/krill_build.sh)"
        * = krill_install
        .binary "krill/install.prg", 2

body
        .logical $a000
main:
        sei
        ldx #$ff
        txs
        lda #$7f                ; niente IRQ dei CIA: solo il raster
        sta $dc0d
        sta $dd0d
        lda $dc0d
        lda $dd0d
        lda #<nmi               ; vettori nella RAM sotto il KERNAL (servono con $01=$34)
        sta $fffa
        lda #>nmi
        sta $fffb
.if !LORE
        lda POKE_GOD            ; prima dell'install: Krill usa $0200-$03FF
        sta gm_poke
.endif
        jsr kr_install          ; (11/11: anche LORE)
.if INTRO == 0
        ; sviluppo: niente titolo/musica/sprite; GAME, LOBBY e GFX0 uno dopo l'altro, poi si parte
        jsr load_all
        jmp start_game
.endif
        lda #$0b                ; schermo spento durante la preparazione
        sta $d011
        lda #0
        sta $d020
        sta $d021
        sta $d015
        sta zp0                 ; bitmap vuota $E000-$FFFF (tutto sfondo nero)
        tay
        ldx #$e0
_cl     stx zp0+1
_cb     sta (zp0),y
        iny
        bne _cb
        inx
        bne _cl
        lda #$34                ; sprite delle lettere (384 byte) nella RAM sotto l'I/O
        sta $01
        ldx #0
_sp     lda ld_spr,x
        sta SPR_AT,x
        cpx #128
        bcs +
        lda ld_spr+256,x
        sta SPR_AT+256,x
+       inx
        bne _sp
        lda #$36
        sta $01
        lda $dd02
        ora #3
        sta $dd02
        lda #0                  ; banco VIC 3. Krill installato: i 6 bit alti di $DD00 sempre a 0 (niente lettura)
        sta $dd00
        lda #$38                ; schermo $CC00, bitmap $E000 (TXT: charset $E000)
        sta $d018
.if TXT
        jsr txt_init
        lda #$08                ; caratteri in alta risoluzione
.else
        lda #$18                ; multicolor
.endif
        sta $d016
        lda #0
        sta $d010
        sta $d017
        sta $d01d
        sta $d01c
        sta $d01b
        sta phase
        sta irqn
        jsr lm_init
        lda #<irq
        sta $0314
        lda #>irq
        sta $0315
        lda #IRQ_BOT
        sta $d012
.if TXT
        lda #$1b                ; testo acceso (bit 7 = 0: riga raster < 256)
.else
        lda #$3b                ; bitmap acceso (bit 7 = 0: riga raster < 256)
.endif
        sta $d011
        lda #1
        sta $d01a
        lda #$ff
        sta $d019
        cli

        jsr load_all
.if TXT
        lda okf                 ; senza il gioco non si parte: bordo rosso
        lsr
        bcs +
        lda #2
        sta $d020
-       jmp -
+       jmp start_game          ; niente PRESS SPACE: subito il menu del gioco
.endif

.if !TXT                        ; (15/11, TODO D12) START con la schermata di attesa non ha PRESS SPACE: va dritto a start_game
        sei                     ; PRESS / SPACE
        ldx #4
_ps     lda press,x
        sta $cff8,x
        dex
        bpl _ps
        lda #PS_X
        jsr set_x
        lda #ROW1_Y
        jsr set_y
        lda #$1f
        sta $d015
        lda #1
        sta phase
        lda #0
        sta irqn
        lda #IRQ_BOT
        sta $d012
        cli
        lda okf                 ; senza il gioco non si parte: bordo rosso, resta la musica
        lsr
        bcs _wait
        lda #2
        sta $d020
_halt   jmp _halt
_wait   lda #$7f                ; SPACE: colonna 7, riga 4
        sta $dc00
        lda $dc01
.if LORE
        bpl _rs                 ; RUN/STOP (colonna 7, bit 7): di nuovo il menu del loader
        and #$10
        bne _wait
        jmp lore_start          ; la storia (src/lore/scroll.asm)
_rs     jmp lore_exit
.else
        and #$10
        bne _wait
.endif
.endif                          ; !TXT

.if !LORE                       ; (15/11, TODO D12) LORE non parte mai direttamente col gioco: ha lore_start / lore_exit
start_game
        sei                     ; partenza del gioco
        lda #0
        sta $d01a
        sta $d015
        sta $d404
        sta $d40b
        sta $d412
        sta $d418
        lda #$ff
        sta $d019
        sta $dc00
        lda #$0b
        sta $d011
        lda #0
        sta LDFLAGS
        lda okf
        and #2
        beq _go
        lda #1
        sta LDFLAGS             ; LOBBY a $C000
_go     lda #$34                ; salvataggi letti: CHRTMP -> CHRBUF (sotto l'I/O; $B000 sara' del gioco)
        sta $01
        ldx #0
_cb     lda CHRTMP,x
        sta CHRBUF,x
        lda CHRTMP+256,x
        sta CHRBUF+256,x
        lda CHRTMP+512,x
        sta CHRBUF+512,x
        inx
        bne _cb
        lda #$36
        sta $01
        lda #1
        sta CHRPRE
.if !LORE
        lda gm_poke             ; POKE 1021,N: god mode nel byte di GAME (non azzerato da game_start)
        sta GODMODE
.endif
        lda #$08
        sta $d016
.if INTRO == 0
        lda okf                 ; sviluppo: senza GAME bordo rosso e stop
        lsr
        bcs +
        lda #2
        sta $d020
-       jmp -
+
.endif
        jmp $0400               ; GAME_ENTRY (src/main.asm)
.endif                          ; !LORE

nmi     rti

.if !TXT                        ; (15/11, D12) solo PRESS SPACE (START con la schermata di attesa non lo usa)
; A = X del primo sprite; poi +28 per ogni sprite (0-4)
set_x   ldx #0
_x      sta $d000,x
        clc
        adc #28
        inx
        inx
        cpx #10
        bne _x
        rts
set_y   ldx #8
_y      sta $d001,x
        dex
        dex
        bpl _y
        rts
.endif

; ------------------------------------------------------------------ caricamento
; (11/11, ramo fast-loader) Krill's Loader: install (KERNAL acceso), residente a $0200, poi i file con loadraw;
; la musica continua in IRQ durante i caricamenti (schermata di attesa, txt_init).
kr_install:
        lda #$36
        sta $01
        jsr krill_install       ; (fa sei/cli; dopo, il drive non risponde piu' al KERNAL)
        bcc +
        jmp kr_fail             ; (12/11, TODO M7 KRILL-14) drive non supportato: messaggio e ritorno a BARBARIAN
+       sei
        ldx #0                  ; residente -> $0200 (2 pagine: KRILL_LOADER_LEN byte)
_r      lda kr_res,x
        sta krill_loadraw,x
        lda kr_res+256,x
        sta krill_loadraw+256,x
        inx
        bne _r
        rts
        .cerror KRILL_LOADER_LEN > 512, "residente di Krill oltre 2 pagine"

; (12/11, TODO M7) install di Krill fallita (drive non supportato, o emulatore senza drive vero): sistema come
; all'accensione per il KERNAL (pagine 2-3 azzerate come fa LORE, CIA2, RESTOR, CINT, IRQ della tastiera), messaggio, un tasto o fire,
; poi BARBARIAN di nuovo con il KERNAL (trampoline). Prima: bordo rosso fisso.
kr_fail:
        sei
        lda #$36
        sta $01
        lda #0
        tax
_z      sta $0200,x
        sta $0300,x
        inx
        bne _z
        lda #4                  ; pagina dello schermo del KERNAL
        sta $0288
        lda #$3f                ; (niente IOINIT: rimette $01 = $37 e il BASIC coprirebbe questo codice a $A000)
        sta $dd02
        lda #$03                ; banco VIC 0, linee seriali rilasciate (Krill non e' installato)
        sta $dd00
        jsr $ff8a               ; RESTOR
        jsr $ff81               ; CINT: schermo di testo pulito
        lda #$81                ; IRQ del timer A del CIA1: la tastiera del KERNAL (GETIN)
        sta $dc0d
        lda #2
        sta $d020
        lda #0
        sta $d021
        ldx #0
_m      lda kf_txt,x
        sta $0400+40*10,x
        lda #1
        sta $d800+40*10,x
        inx
        cpx #kf_n
        bne _m
        cli
_w      jsr $ffe4               ; GETIN
        bne _go
        lda $dc00
        and #$10                ; fire (porta 2)
        bne _w
_go     ldx #<nm_barb
        ldy #>nm_barb
        lda #nm_barb_n
        jmp tramp_run
        .enc "screen"
kf_txt  .text "  this drive is not supported by the    "
        .text "  fast loader (1541 / 1541-ii only).    "
        .text "                                        "
        .text "  press a key to go back to the menu    "
kf_n    = * - kf_txt
        .cerror kf_n > 255, "messaggio troppo lungo"
        .enc "none"
nm_barb .text "barbarian"
nm_barb_n = * - nm_barb
.if !LORE
        .include "tramp.inc"
.endif

.if !LORE
load_all:
        lda #0
        sta CHRTMP              ; elenco eroi non ancora letto
        sta okf
        clc                     ; GAME (ZX0) all'indirizzo del file, poi decompresso sul posto
        ldx #<nm_game
        ldy #>nm_game
        jsr krill_loadraw
        bcs _nl
        lda #<UNP_AT
        sta zx_src
        lda #>UNP_AT
        sta zx_src+1
        lda #<UNP_DST
        sta zx_dst
        lda #>UNP_DST
        sta zx_dst+1
        jsr zx0_unpack          ; (la musica continua: niente sei)
        lda #1
        sta okf
_nl     clc                     ; LOBBY a $C000 (indirizzo del file)
        ldx #<nm_lobby
        ldy #>nm_lobby
        jsr krill_loadraw
        bcs _nh
        lda okf
        ora #2
        sta okf
_nh     lda #<(CHRTMP+1)        ; elenco eroi (file hl) -> CHRTMP+1, CHRTMP = 1 se letto
        sta krill_loadaddrlo
        lda #>(CHRTMP+1)
        sta krill_loadaddrhi
        sec
        ldx #<nm_hl
        ldy #>nm_hl
        jsr krill_loadraw
        bcs _x
        lda #1
        sta CHRTMP
_x      rts
.else
; (11/11) LORE con Krill: TITLE (10000 B) in un buffer, LDAT al suo indirizzo e decompresso, poi il titolo compare
; riga per riga dal buffer (un blocco di 40 byte per fotogramma: ~5 s), con la musica. RUN/STOP: di nuovo BARBARIAN.
TBUF    = $6000                 ; TITLE (dopo LDAT decompresso, $2000-$57E2; sotto il corpo a $A000). 15/11: era $5600, ma con l'interlinea
                                ; della storia (292 righe) LDAT decompresso arriva a $57E3; $6000 lascia ~2 KB alla storia (TITLE finisce a $8710)
TBUF_end = TBUF + TITLE_U * 40  ; (15/11) coppie di etichette per la mappa automatica (src/lore.asm)
LD_DST_end = LD_DST + LD_RAW
        .cerror TBUF < LD_DST + LD_RAW || TBUF < LD_AT + LD_LEN, "buffer del titolo sopra LDAT"
        .cerror TBUF + TITLE_U * 40 > $a000, "buffer del titolo sopra il corpo di LORE"
load_all:
        lda #0
        sta ld_stop             ; RUN/STOP non ancora premuto
        sta okf
        lda #<TBUF
        sta krill_loadaddrlo
        lda #>TBUF
        sta krill_loadaddrhi
        sec
        ldx #<nm_title
        ldy #>nm_title
        jsr krill_loadraw
        lda #0                  ; titolo mancante: niente titolo (resta lo sfondo nero)
        bcs +
        lda #TITLE_U
+       sta tleft
        clc                     ; LDAT all'indirizzo del file (LD_AT), decompresso sul posto (LD_DST)
        ldx #<nm_ldat
        ldy #>nm_ldat
        jsr krill_loadraw
        bcs _t
        lda #<UNP_AT
        sta zx_src
        lda #>UNP_AT
        sta zx_src+1
        lda #<UNP_DST
        sta zx_dst
        lda #>UNP_DST
        sta zx_dst+1
        jsr zx0_unpack          ; (la musica continua)
        lda #1
        sta okf
_t      lda #<TBUF              ; il titolo dal buffer
        sta rdp
        lda #>TBUF
        sta rdp+1
        lda #0
        sta tu
        sta tsc
        sta tco
        sta trow
        sta tlin
        lda #$cc
        sta tsc+1
        lda #$d8
        sta tco+1
        lda #$e0
        sta trow+1
        sta tlin+1
_l      lda ld_stop             ; RUN/STOP: di nuovo il menu del loader
        beq +
        jmp lore_exit
+       lda tleft
        beq _e
        lda frm                 ; un blocco per fotogramma (frm: IRQ)
-       cmp frm
        beq -
        jsr title_unit
        jmp _l
_e      rts

; byte seguente del titolo dal buffer (X e Y conservati)
rd      sty rsy
        ldy #0
        lda (rdp),y
        inc rdp
        bne +
        inc rdp+1
+       ldy rsy
        rts
rdp     = zp1                   ; (title_unit usa zp0)

; un blocco di 40 byte del titolo
title_unit:
        lda tu
        cmp #2
        bcs _px
        asl                     ; 0 schermo, 1 colore: 40 byte consecutivi (tsc / tco)
        tax
        lda tsc,x
        sta zp0
        lda tsc+1,x
        sta zp0+1
        ldy #0
_s      jsr rd
        sta (zp0),y
        iny
        cpy #40
        bne _s
        lda tsc,x
        clc
        adc #40
        sta tsc,x
        bcc _nx
        inc tsc+1,x
        jmp _nx
_px     lda tlin                ; una riga di pixel: la cella successiva e' 8 byte piu' avanti
        sta zp0
        lda tlin+1
        sta zp0+1
        ldx #40
_p      jsr rd
        ldy #0
        sta (zp0),y
        lda zp0
        clc
        adc #8
        sta zp0
        bcc +
        inc zp0+1
+       dex
        bne _p
        inc tlin
_nx     inc tu
        lda tu
        cmp #10
        bne _r
        lda #0                  ; riga di caratteri successiva: bitmap +320
        sta tu
        lda trow
        clc
        adc #<320
        sta trow
        sta tlin
        lda trow+1
        adc #>320
        sta trow+1
        sta tlin+1
_r      dec tleft
        rts

.endif


.if TXT
; ------------------------------------------------------------------ schermata di attesa (START)
; Schermo $CC00 (banco 3), font della UI del gioco a $E000 (codici 0-63): titolo e "please wait".
txt_init:
        ldx #0
_f      lda txt_font,x
        sta $e000,x
        lda txt_font+256,x
        sta $e100,x
        lda #32
        sta $cc00,x
        sta $cd00,x
        sta $ce00,x
        sta $cee8,x
        lda #7
        sta $d800,x
        sta $d900,x
        sta $da00,x
        sta $dae8,x
        inx
        bne _f
        ldx #txt_t_n-1
_t      lda txt_t,x
        sta $cc00+TXT_ROW*40+(40-txt_t_n)/2,x
        dex
        bpl _t
        ldx #txt_w_n-1
_w      lda txt_w,x
        sta $cc00+(TXT_ROW+3)*40+(40-txt_w_n)/2,x
        lda #1
        sta $d800+(TXT_ROW+3)*40+(40-txt_w_n)/2,x
        dex
        bpl _w
        rts
        .enc "screen"
txt_t   .text "the crypt door creaks open"
txt_t_n = * - txt_t
txt_w   .text "please wait"
txt_w_n = * - txt_w
        .enc "none"
txt_font .binary "../../out/work/gfx/uifont.bin", 0, 512
.endif

; ------------------------------------------------------------------ IRQ: musica e sprite
irq:
        lda #$ff
        sta $d019
        inc frm                 ; (LORE: passo del titolo)
.if LORE
        lda #$7f                ; RUN/STOP durante il caricamento e la comparsa del titolo
        sta $dc00
        lda $dc01
        bmi +
        lda #1
        sta ld_stop
+
.endif
        lda phase
        bne _p1
        jsr lm_play            ; caricamento: solo musica
        jmp $ea81
_p1     lda irqn                ; PRESS / SPACE: 2 IRQ per fotogramma
        bne _mid
        inc sph                 ; onda: fase +1 per fotogramma
        lda #ROW1_Y             ; bordo basso: prima riga (PRESS) per il fotogramma seguente
        ldy #0
        jsr sin_y
        ldx #4
_r1     lda press,x
        sta $cff8,x
        dex
        bpl _r1
        jsr lm_play
        inc cph
        ldx #4
_c1     jsr colour
        dex
        bpl _c1
        lda #IRQ_MID
        sta $d012
        lda #1
        sta irqn
        jmp $ea81
_mid    lda #ROW2_Y             ; dopo PRESS: stessi sprite piu' in basso (SPACE), onda in controfase
        ldy #32
        jsr sin_y
        ldx #4
_r2     lda space,x
        sta $cff8,x
        dex
        bpl _r2
        lda #IRQ_BOT
        sta $d012
        lda #0
        sta irqn
        jmp $ea81
; Y degli sprite 0-4 sull'onda: A = Y di base, Y = sfasamento (0 PRESS, 32 SPACE); lettera X: fase sph + 6X
sin_y   sta sy_b              ; (dalla lettera 0: la prima di SPACE va scritta prima che il raster la raggiunga)
        sty sy_o
        ldx #0
_l      lda sx_off,x
        clc
        adc sph
        clc
        adc sy_o
        and #63
        tay
        lda ld_sin,y
        clc
        adc sy_b
        pha
        txa
        asl
        tay
        pla
        sta $d001,y
        inx
        cpx #5
        bne _l
        rts
sx_off  .byte 0, 6, 12, 18, 24
colour  txa                     ; colore dello sprite X: tabella sfumata, sfasata per lettera
        clc
        adc cph
        lsr
        and #31
        tay
        lda LD_COL,y
        sta $d027,x
        rts

; ------------------------------------------------------------------ decompressore ZX0 (GAME)
ZX_ZP   = $50                   ; 15 byte della pagina zero del BASIC (il BASIC non gira; il KERNAL non li usa)
        .include "zx0.inc"
.if LORE
        .include "lore.inc"         ; out/work/lore.inc: LD_AT, LD_DST, LR_ROWS... (tools/build/gen_lore.py)
UNP_AT  = LD_AT
UNP_DST = LD_DST
        .include "lore/scroll.asm"
        .include "tramp.inc"
.else
        .include "pack.inc"         ; out/work/pack.inc: GAME_ZX_AT, GAME_ZX_DST (tools/build/pack.py)
UNP_AT  = GAME_ZX_AT
UNP_DST = GAME_ZX_DST
.endif

; ------------------------------------------------------------------ musica: brano del titolo (tools/build/songs.py)
SP_VARS = $be00                 ; variabili del player (RAM sotto il BASIC, dopo il corpo)
SP_V0   = 0
SP_V1   = 7
SP_V2   = 14
SP_RESUME = 0                   ; (15/11, TODO D12) START e LORE non riprendono ne' rilasciano il brano: fuori sp_resume e sp_release
        .include "sid_player.inc"
        .include "sid_title.inc"        ; out/work/sid_title.inc (tools/build/gen_music.py)
        .cerror SP_VARS + SP_VSIZE > $c000, "variabili del player oltre $BFFF"
lm_init:
        ldx #$18
        lda #0
_c      sta $d400,x
        dex
        bpl _c
        sta sp_mute
        sta sp_mute+1
        sta sp_mute+2
        sta sp_once
        lda #<sid_title
        sta sp_bl
        lda #>sid_title
        sta sp_bh
        jmp sp_start
lm_play = sp_play

        .enc "none"
nm_title .text "title"          ; minuscolo in "none" = PETSCII maiuscolo; 0 finale per Krill
        .byte 0
nm_game  .text "game"
        .byte 0
nm_lobby .text "lobby"
        .byte 0
nm_hl    .text "hl"
        .byte 0
nm_ldat  .text "ldat"
        .byte 0
; sprite: P R E S A C = 0..5
press   .byte SPRP+0, SPRP+1, SPRP+2, SPRP+3, SPRP+3
space   .byte SPRP+3, SPRP+0, SPRP+4, SPRP+5, SPRP+2

        .include "start_data.inc"
LD_COL  = (ld_col0, ld_col1, ld_col2)[LDCOL]

; variabili (dopo il codice, azzerate da chi le usa)
phase   .byte 0
irqn    .byte 0
cph     .byte 0
sph     .byte 0                 ; fase dell'onda di PRESS / SPACE
sy_b    .byte 0
sy_o    .byte 0
okf     .byte 0
ld_stop .byte 0                 ; LORE: RUN/STOP premuto durante il caricamento
tleft   .byte 0
tu      .byte 0
tsc     .word 0                 ; puntatore schermo (tu = 0) - adiacente a tco
tco     .word 0                 ; puntatore colore (tu = 1)
trow    .word 0
tlin    .word 0
rsx     .byte 0
rsy     .byte 0
frm     .byte 0                 ; fotogrammi (IRQ)
gm_poke .byte 0                 ; POKE 1021 letto all'avvio (god mode)
kr_res  .binary "krill/loader.prg", 2   ; residente di Krill, copiato a $0200 da kr_install
        .fill 512 - KRILL_LOADER_LEN    ; (la copia ne legge 2 pagine)
body_end
.if LORE
        .cerror body_end > SP_VARS, "LORE oltre le variabili del player ($BE00)"
.else
        .cerror body_end > CHRTMP, "START oltre CHRTMP"
.endif
        .endlogical
