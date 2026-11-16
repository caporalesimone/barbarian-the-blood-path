; =============================================================================
; LORE - la storia a scorrimento (incluso da src/start.asm con LORE=1, gira a $A000 dopo PRESS SPACE)
; -----------------------------------------------------------------------------
; Dati: out/work/lore.inc + LDAT decompresso a LD_DST ($2000) da tools/build/gen_lore.py (formato in docs/wiki/intro.md):
;   $2000 charset (font 0-63 + forme 64-254 caricate durante lo scorrimento), $2800 sprite, LR_ROWS righe.
; Video: banco VIC 0, modo testo multicolore a 24 righe, due schermi ($0400 / $0800) che si alternano.
;   - scroll fine con $D011 (s = 7..0, un pixel ogni LR_SPEED fotogrammi; fire e spazio non fanno nulla fino
;     alla fine della storia, 07/11; 15/11: con il FIRE DEL JOYSTICK 2 tenuto (non lo spazio) un pixel ogni LR_FAST
;     fotogrammi, cioe' velocita' doppia; al rilascio torna normale. Pausa iniziale e fine storia non cambiano);
;   - a ogni passo di 8 pixel (IRQ nel bordo basso): si mostra l'altro schermo, gia' preparato (righe 1-24 del
;     precedente + la riga nuova in fondo) e il ciclo principale sposta la RAM colore in "gara" con il pennello
;     (riga per riga dall'alto, parte nel bordo basso: arriva prima del pennello su ogni riga);
;   - i colori multicolore comuni ($D022/$D023) cambiano con un raster IRQ alla riga dove comincia
;     un'immagine (evento SPLIT); fra due immagini c'e' sempre almeno una riga di testo (alta risoluzione);
;   - sprite (mostri e barbaro) raddoppiati, salgono di un pixel per pixel di scorrimento, 2 fotogrammi.
; Uscita (RUN/STOP, o fire a fine storia): si ricarica BARBARIAN (il loader con il menu) con il trampoline di src/common/tramp.inc.
; =============================================================================
LSCR_A  = $0400                 ; schermo A (puntatori sprite a $07F8)
LSCR_B  = $0800                 ; schermo B ($0BF8)
ROWBUF  = $0c00                 ; riga decodificata: 40 caratteri + 40 colori (NEWCOL)
NEWCOL  = ROWBUF + 40
LR_SPEED = 6                    ; fotogrammi per pixel (07/11: era 2, troppo veloce): ~8 pixel, una riga al secondo
LR_FAST = 1                     ; (16/11, committente: "almeno il doppio di adesso", era 3) fotogrammi per pixel con il fire del joystick 2 tenuto: 6 volte la normale
IRQ_LB  = 251                   ; IRQ del bordo basso (sotto l'ultima riga: 24 righe, $D011 bit 3 = 0)
SPLIT_UP = 3                    ; il cambio dei colori comincia 3 righe raster prima dell'immagine
NSPL    = 4                     ; coda dei cambi di colore (la testa e' quello in vigore in alto)
lp      = $60                   ; (2) puntatore nel flusso delle righe
lq      = $62                   ; (2) puntatori di lavoro
lr      = $64                   ; (2)
ln      = $66                   ; (2) contatore 16 bit
        .cerror ZX_ZP + 15 > lp, "pagina zero: LORE sopra le variabili di ZX0"

; ------------------------------------------------------------------ partenza (dopo PRESS SPACE)
lore_start:
        sei
        lda #0
        sta $d01a
        sta $d015
        lda #$ff
        sta $d019
        lda #$0b                ; schermo spento durante il riempimento
        sta $d011
        lda #3                  ; banco VIC 0 ($0000-$3FFF). Krill installato (11/11): niente lettura di $DD00
        sta $dd00
        lda #$18                ; schermo $0400, charset $2000
        sta $d018
        lda #$18                ; multicolore, 40 colonne
        sta $d016
        lda #0
        sta $d020
        sta $d021
        sta $d01b               ; sprite davanti ai caratteri
        lda #9                  ; colori multicolore degli sprite come nel gioco
        sta $d025
        lda #15
        sta $d026
        lda #$ff
        sta $d01c
        sta $d017
        sta $d01d
        ldx #0                  ; schermi vuoti, RAM colore nera
        lda #32
_cl     sta LSCR_A,x
        sta LSCR_A+$100,x
        sta LSCR_A+$200,x
        sta LSCR_A+$2e8,x
        sta LSCR_B,x
        sta LSCR_B+$100,x
        sta LSCR_B+$200,x
        sta LSCR_B+$2e8,x
        inx
        bne _cl
        lda #0
_cc     sta $d800,x
        sta $d900,x
        sta $da00,x
        sta $dae8,x
        inx
        bne _cc
        ldx #lvar_n - 1         ; variabili a zero
_cv     sta lvar,x
        dex
        bpl _cv
        lda #7
        sta ls
        lda #$10                ; spazio ancora premuto da PRESS SPACE: serve una nuova pressione
        sta lfire               ; (e il fire del joystick: accelera solo dopo un primo rilascio, ljarm = 0)
        lda #<LR_ROWS
        sta lp
        lda #>LR_ROWS
        sta lp+1
        lda #25                 ; riempimento: 25 passi di una riga (8 pixel) a schermo spento
        sta lcnt
_pf     jsr prep
        lda #8
        jsr commit
        jsr colshift
        dec lcnt
        bne _pf
        jsr prep                ; la riga 26 pronta per il primo passo
        lda #1
        sta lready
        lda #<LR_HOLD           ; pausa sulla prima schermata (il logo)
        sta lhold
        lda #>LR_HOLD
        sta lhold+1
        lda #1                  ; stato: 1 pausa, 2 scorrimento, 3 fermo a fine storia
        sta lstate
        lda #<lirq
        sta $0314
        lda #>lirq
        sta $0315
        lda #IRQ_LB
        sta $d012
        lda #$17                ; schermo acceso, 24 righe, s = 7
        sta $d011
        lda #1
        sta $d01a
        cli

; ------------------------------------------------------------------ ciclo principale
lmain:
        lda lstop               ; RUN/STOP: uscita
        bne lore_exit
        lda lstep
        beq _ns
        lda #0
        sta lstep
        jsr colshift            ; in gara con il pennello: subito
        jsr prep                ; poi lo schermo nascosto per il passo seguente
        lda #1
        sta lready
_ns     lda lstate
        cmp #3
        bne lmain
        lda lfedge              ; fermo: fire (nuova pressione) per uscire
        beq lmain

lore_exit:
        sei
        lda #0
        sta $d01a
        sta $d015
        sta $d418
        lda #$ff
        sta $d019
        lda #<wm_msg            ; (16/11, committente) pagina di attesa "the legend falls silent / please wait" (waitmsg.inc)
        sta $fb
        lda #>wm_msg
        sta $fc
        lda #<lore_font
        sta $fd
        lda #>lore_font
        sta $fe
        jsr wm_show
        jsr krill_uninstall     ; (11/11) il drive torna alla sua ROM: BARBARIAN si carica con il KERNAL
        sei
        lda #0                  ; pagine 2-3 azzerate come all'accensione (il residente di Krill le ha sporcate:
        tax                     ; con le variabili RS-232 sporche il KERNAL si blocca in $F0A4, provato in VICE)
_z      sta $0200,x
        sta $0300,x
        inx
        bne _z
        lda #4                  ; pagina dello schermo del KERNAL
        sta $0288
        ldx #<nm_front
        ldy #>nm_front
        lda #nm_front_n
        jmp tramp_run

; ------------------------------------------------------------------ prepara lo schermo nascosto
; righe 1-24 dello schermo visibile -> righe 0-23 del nascosto; la riga nuova (flusso) nella riga 24 + NEWCOL
prep:
        lda lfront
        bne _fb
        lda #<(LSCR_A+40)       ; visibile A -> nascosto B
        sta lq
        lda #>(LSCR_A+40)
        sta lq+1
        lda #<LSCR_B
        sta lr
        lda #>LSCR_B
        sta lr+1
        jmp _cp
_fb     lda #<(LSCR_B+40)
        sta lq
        lda #>(LSCR_B+40)
        sta lq+1
        lda #<LSCR_A
        sta lr
        lda #>LSCR_A
        sta lr+1
_cp     ldx #4                  ; 960 byte = 4 x 240
_c4     ldy #239
_c1     lda (lq),y
        sta (lr),y
        dey
        cpy #$ff
        bne _c1
        lda lq
        clc
        adc #240
        sta lq
        bcc +
        inc lq+1
+       lda lr
        clc
        adc #240
        sta lr
        bcc +
        inc lr+1
+       dex
        bne _c4
        jsr decode              ; (decode usa lr per le forme: la riga 24 si scrive con l'indirizzo fisso)
        ldy #39
        lda lfront
        bne _r24a
_r24b   lda ROWBUF,y            ; visibile A -> nascosto B
        sta LSCR_B+24*40,y
        dey
        bpl _r24b
        rts
_r24a   lda ROWBUF,y
        sta LSCR_A+24*40,y
        dey
        bpl _r24a
        rts

; una riga del flusso -> ROWBUF (80 byte) + eventi
decode:
        ldy #0
        lda (lp),y
        cmp #$fe
        bne _ev
        ldx #39                 ; fine del flusso: riga vuota
_bl     lda #32
        sta ROWBUF,x
        lda #0
        sta NEWCOL,x
        dex
        bpl _bl
        rts
_ev     sta lnev
        jsr lp_inc
dec_evl lda lnev
        beq _rle
        dec lnev
        ldy #0
        lda (lp),y
        beq ev_shapes
        cmp #1
        bne +
        jmp ev_sprite
+       cmp #2
        bne +
        jmp ev_split
+       ; 3: STOP riga -> passi che mancano = 24 - riga
        iny
        lda #24
        sec
        sbc (lp),y
        sta lstopc
        lda #1
        sta lstopp
        lda #2
        jsr lp_add
        jmp dec_evl
_rle    ldx #0                  ; RLE: $FF n v = v ripetuto n volte
_rl     ldy #0
        lda (lp),y
        cmp #$ff
        beq _run
        sta ROWBUF,x
        inx
        jsr lp_inc
        cpx #80
        bne _rl
        rts
_run    iny
        lda (lp),y
        sta ln
        iny
        lda (lp),y
        ldy ln
_rr     sta ROWBUF,x
        inx
        dey
        bne _rr
        lda #3
        jsr lp_add
        cpx #80
        bne _rl
        rts

ev_shapes:                      ; 0 idx cnt lo hi: forme in $2000 + idx*8 (cnt*8 byte)
        iny
        lda (lp),y              ; idx -> lr = $2000 + idx*8
        sta lr
        lda #0
        sta lr+1
        asl lr
        rol lr+1
        asl lr
        rol lr+1
        asl lr
        rol lr+1
        lda lr+1
        clc
        adc #>LD_DST
        sta lr+1
        iny
        lda (lp),y              ; cnt -> ln = cnt*8
        sta ln
        lda #0
        sta ln+1
        asl ln
        rol ln+1
        asl ln
        rol ln+1
        asl ln
        rol ln+1
        iny
        lda (lp),y
        sta lq
        iny
        lda (lp),y
        sta lq+1
        ldy #0
_sc     lda (lq),y
        sta (lr),y
        inc lq
        bne +
        inc lq+1
+       inc lr
        bne +
        inc lr+1
+       lda ln
        bne +
        dec ln+1
+       dec ln
        lda ln
        ora ln+1
        bne _sc
        lda #5
        jsr lp_add
        jmp dec_evl

ev_sprite:                      ; 1 hw ptr xlo xhi col dy anim -> in attesa del passo
        ldx lpsn
        iny
        lda (lp),y
        sta lpsh,x
        iny
        lda (lp),y
        sta lpsp,x
        iny
        lda (lp),y
        sta lpsx,x
        iny
        lda (lp),y
        sta lpsxh,x
        iny
        lda (lp),y
        sta lpsc,x
        iny
        lda (lp),y
        sta lpsd,x
        inc lpsn
        lda #8
        jsr lp_add
        jmp dec_evl

ev_split:                       ; 2 mc1 mc2 -> in attesa del passo
        ldx lpcn
        iny
        lda (lp),y
        sta lpc1,x
        iny
        lda (lp),y
        sta lpc2,x
        inc lpcn
        lda #3
        jsr lp_add
        jmp dec_evl

lp_inc  lda #1
lp_add  clc
        adc lp
        sta lp
        bcc +
        inc lp+1
+       rts

; ------------------------------------------------------------------ passo di una riga (IRQ o riempimento)
; A = pixel di cui salgono gli sprite (1 nello scorrimento, 8 nel riempimento). Mostra lo schermo preparato,
; fa scorrere la coda dei colori, accende gli sprite in attesa. La RAM colore la sposta colshift.
commit:
        sta lpx
        lda lfront
        eor #1
        sta lfront
        tax
        lda d018_t,x
        sta $d018
        ldx #0                  ; cambi di colore: k - 1
_k      cpx lsn
        beq _kd
        dec lsk,x
        inx
        bne _k
_kd     lda lsn                 ; la testa si toglie quando il secondo e' arrivato in cima (k <= 0)
        cmp #2
        bcc _ka
        lda lsk+1
        beq _drop
        bpl _ka
_drop   ldx #0
_sh     lda lsk+1,x
        sta lsk,x
        lda ls1+1,x
        sta ls1,x
        lda ls2+1,x
        sta ls2,x
        inx
        cpx #NSPL-1
        bne _sh
        dec lsn
        jmp _kd
_ka     ldx #0                  ; i nuovi in coda con k = 24
_kn     cpx lpcn
        beq _kz
        ldy lsn
        cpy #NSPL
        bcs _kz
        lda #24
        sta lsk,y
        lda lpc1,x
        sta ls1,y
        lda lpc2,x
        sta ls2,y
        inc lsn
        inx
        bne _kn
_kz     lda #0
        sta lpcn
        lda lpx                 ; sprite: salgono
        jsr spr_up
        ldx #0                  ; sprite in attesa: accesi in fondo
_sn     cpx lpsn
        beq _sz
        ldy lpsh,x              ; Y = sprite hardware
        lda lpsp,x
        sta lsb,y
        sta LSCR_A+$3f8,y
        sta LSCR_B+$3f8,y
        lda lpsc,x
        sta $d027,y
        lda lpsd,x
        clc
        adc #247
        sta lsy,y
        tya
        asl
        tay
        lda lpsx,x
        sta $d000,y
        tya
        lsr
        tay
        lda bit_8,y
        ora lspr
        sta lspr
        lda lpsxh,x
        beq _xl
        lda bit_8,y
        ora $d010
        sta $d010
        jmp _xn
_xl     lda bit_8,y
        eor #$ff
        and $d010
        sta $d010
_xn     inx
        bne _sn
_sz     lda #0
        sta lpsn
        lda lstopp              ; fine della storia: si ferma dopo lstopc passi
        beq _st
        lda lstopc
        bne _sd
        lda #3
        sta lstate
        lda #0
        sta lstopp
        rts
_sd     dec lstopc
_st     rts

; sprite accesi: Y - A; spenti quando escono in alto (Y < A + 14)
spr_up:
        sta lpx
        ldy #7
_su     lda bit_8,y
        and lspr
        beq _sx
        lda lpx
        clc
        adc #14
        cmp lsy,y
        bcc _ok
        lda bit_8,y             ; uscito: spento
        eor #$ff
        and lspr
        sta lspr
        jmp _sx
_ok     lda lsy,y
        sec
        sbc lpx
        sta lsy,y
_sx     dey
        bpl _su
        rts

; RAM colore: righe 1-24 -> 0-23 (dall'alto, in gara con il pennello), poi NEWCOL nella riga 24
colshift:
.for r = 0, r < 24, r += 1
        ldx #39
-       lda $d800+(r+1)*40,x
        sta $d800+r*40,x
        dex
        bpl -
.next
        ldx #39
-       lda NEWCOL,x
        sta $d800+24*40,x
        dex
        bpl -
        rts

; ------------------------------------------------------------------ IRQ
lirq:
        lda #$ff
        sta $d019
        lda lirqk
        beq _bot
        jsr set_split           ; cambio dei colori a meta' schermo
        jmp $ea81
_bot    jsr sp_play             ; musica
        lda #$7f                ; tasti: colonna 7 (spazio bit 4, RUN/STOP bit 7); joystick 2 sul $DC00
        sta $dc00
        lda $dc01
        tax
        and #$80
        eor #$80
        sta lstop
        txa
        and $dc00
        and #$10
        eor #$10                ; fire o spazio (1 = premuto)
        tax
        eor lfire
        beq +
        txa
+       sta lfedge              ; nuova pressione
        stx lfire
        lda $dc00               ; (15/11) fire del joystick 2 da solo (bit 4 a 0 = premuto): velocita' doppia, non lo spazio.
        and #$10                ; Se era gia' premuto da PRESS SPACE non vale finche' non e' stato rilasciato (ljarm).
        bne _jr
        lda ljarm
        sta lfast
        jmp _jd
_jr     lda #1
        sta ljarm
        lda #0
        sta lfast
_jd     lda lstate
        cmp #1
        bne _run
        lda lhold               ; pausa: finisce solo con il tempo
        bne +
        dec lhold+1
        bmi _go
+       dec lhold
        jmp _vic
_go     lda #0
        sta lfedge
        lda #2
        sta lstate
_run    cmp #2
        bne _vic
        inc ltick
        lda ltick
        ldx lfast               ; 0 normale, 1 fire tenuto: soglia LR_SPEED o LR_FAST (ltick riparte da 0 a ogni pixel)
        cmp lspd,x
        bcc _vic
_mv     lda #0
        sta ltick
        lda ls
        beq _step
        dec ls
        lda #1
        jsr spr_up
        jmp _vic
_step   lda lready              ; passo di una riga (solo se il nascosto e' pronto: se no si aspetta)
        beq _vic
        lda #0
        sta lready
        lda #7
        sta ls
        lda #1
        jsr commit
        lda #1
        sta lstep
_vic    lda ls                  ; fotogramma seguente: scroll fine, sprite, animazione
        ora #$10
        sta $d011
        ldy #7
_sy     tya
        asl
        tax
        lda lsy,y
        sta $d001,x
        dey
        bpl _sy
        lda lspr
        sta $d015
        inc lanim
        lda lanim
        and #15
        bne _cs
        lda lanim               ; ogni 16 fotogrammi: l'altro fotogramma degli sprite
        lsr
        lsr
        lsr
        lsr
        and #1
        sta lq
        ldy #7
_an     lda lsb,y
        clc
        adc lq
        sta LSCR_A+$3f8,y
        sta LSCR_B+$3f8,y
        dey
        bpl _an
_cs     lda lsn                 ; colori in alto: la testa della coda; poi un IRQ per ogni immagine sotto
        beq _nc
        lda ls1
        sta $d022
        lda ls2
        sta $d023
_nc     lda #1
        sta lsi
        jsr next_split
        jmp $ea81

; prossimo cambio di colore (indice lsi, k >= 1) o IRQ del bordo basso
next_split:
        ldx lsi
        cpx lsn
        bcs _nb
        lda lsk,x
        beq _nx
        bmi _nx
        asl                     ; riga raster = 48 + s + 8k - SPLIT_UP
        asl
        asl
        clc
        adc ls
        adc #48 - SPLIT_UP
        sta $d012
        lda #1
        sta lirqk
        rts
_nx     inc lsi
        jmp next_split
_nb     lda #IRQ_LB
        sta $d012
        lda #0
        sta lirqk
        rts

set_split:
        ldx lsi
        lda ls1,x
        sta $d022
        lda ls2,x
        sta $d023
        inc lsi
        jmp next_split

lspd    .byte LR_SPEED, LR_FAST
d018_t  .byte $18, $28          ; schermo A ($0400) / B ($0800), charset $2000
bit_8   .byte 1, 2, 4, 8, 16, 32, 64, 128

        .enc "none"
nm_front .text "barbarian"
nm_front_n = * - nm_front

; ------------------------------------------------------------------ variabili (azzerate a lore_start)
lvar
lfront  .byte 0                 ; schermo visibile: 0 A, 1 B
ls      .byte 0                 ; scroll fine 7..0
lstate  .byte 0
lhold   .word 0
ltick   .byte 0
lready  .byte 0                 ; schermo nascosto pronto
lstep   .byte 0                 ; passo fatto: il ciclo principale sposta i colori e prepara
lstop   .byte 0                 ; RUN/STOP premuto
lfire   .byte 0                 ; fire / spazio tenuto ($10)
lfedge  .byte 0                 ; nuova pressione (fire o spazio: a fine storia esce)
lfast   .byte 0                 ; 1 = fire del joystick 2 tenuto (e rilasciato almeno una volta): velocita' doppia
ljarm   .byte 0                 ; 1 dopo il primo rilascio del fire del joystick
lanim   .byte 0
lcnt    .byte 0
lnev    .byte 0
lpx     .byte 0
lstopp  .byte 0
lstopc  .byte 0
lirqk   .byte 0                 ; 0 bordo basso, 1 cambio di colore
lsi     .byte 0
lsn     .byte 0                 ; coda dei colori: k (riga dello schermo), mc1, mc2
lsk     .fill NSPL
ls1     .fill NSPL
ls2     .fill NSPL
lpcn    .byte 0                 ; colori in attesa del passo
lpc1    .fill 2
lpc2    .fill 2
lspr    .byte 0                 ; sprite accesi (bit)
lsy     .fill 8                 ; Y degli sprite
lsb     .fill 8                 ; puntatore del primo fotogramma
lpsn    .byte 0                 ; sprite in attesa del passo
lpsh    .fill 8
lpsp    .fill 8
lpsx    .fill 8
lpsxh   .fill 8
lpsc    .fill 8
lpsd    .fill 8
lvar_n  = * - lvar
