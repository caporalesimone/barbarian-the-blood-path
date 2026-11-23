; ===================================================================
;  ui.asm - schermate di testo (font ROM), ingresso dell'inventario, baule del piano, minimappa, menu di gioco
; ===================================================================
        .enc "screen"

        .virtual $9460
mm_bits  .byte ?
mm_st    .byte ?
mm_wat   .byte ?              ; villaggio: bit 0 = acqua nel quadrante, bit 1 = strada (cella blu se solo acqua)
mmx      .byte ?
mmy      .byte ?
st_i     .byte ?                ; indice salvato (baule di casa, cintura nell'inventario)
it_i     .byte ?                ; oggetto in transito: id, bonus, durabilita', massimo (eq_get, pk_put...)
it_b     .byte ?
it_s     .byte ?                ; (21/11 sera) suffisso
it_d     .byte ?
it_m     .byte ?
ui_dur   .byte ?                ; durabilita' dell'oggetto mostrato (0 = non mostrata): ibox_ld, sl_get
ui_durm  .byte ?
st_col   .byte ?                ; baule di casa: colonna selezionata (0 zaino, 1 baule) (locanda)
iv_r     .byte ?                ; (21/11) inventario: riga che si pulisce
iv_rr    .byte ?                ; (21/11) inv_act: 1 = un anello sostituito (messaggio)
        .endv
        .cerror iv_rr >= $9480, "variabili UI oltre $947F"

        .virtual $93e0          ; motore dei menu (ui_nav, 07/11 sera: docs/wiki/refactor-tasti.md)
tb_n     .byte ?                ; contatore di ui_boxes (11/11: le linguette non ci sono piu')
tb_i     .byte ?
ui_bc    .byte ?                ; colore delle cornici di ui_box (ui_begin: UC_BOX; la casa colora equipped in scelta)
s4_n     .byte ?                ; sort4: numero di posti, categoria della passata, appoggio
s4_c     .byte ?
s4_t     .byte ?
nav_end
        .endv
        .cerror nav_end > $9400, "variabili di ui_nav oltre $93FF"

        .virtual $942b          ; (08/11) liste comuni dei menu: lista da 8, righe dei riquadri
l8_id   .fill 8                 ; merce del negozio o contenuto del baule del piano (segmento SK_WARE delle liste)
l8_b    .fill 8                 ; ... e loro bonus
ti_row  .byte ?                 ; riga del titolo (ui_title; 0 di base da ui_begin)
ti_col  .byte ?                 ; colore del titolo e delle sue icone (ui_title; UC_TITLE di base da ui_begin)
l8_end
        .endv
        .cerror l8_end > $9440, "variabili delle liste oltre $943F"

        .virtual $9440
bx      .byte ?                 ; riquadro: x, y, larghezza, altezza
by      .byte ?
bw      .byte ?
bh      .byte ?
br      .byte ?
bend    .byte ?
ui_nl   .byte ?                 ; 1 = numeri senza spazi iniziali
ui_fc   .byte ?                 ; <>0: colore forzato per valori e oggetti (schermate eroe)
        .endv

        .virtual $9400
shp_stock .fill SHOP_POOL_MAX    ; oggetti in vendita (estratti a caso a ogni ingresso; 21/11: 24, armi nuove; 28, armature nuove)
sh_mask   .byte ?               ; negozio: categorie comprate (bit 1<<CAT_*), 0 = fuori dal negozio (shop_gold)
        .endv
        .cerror sh_mask >= $9420, "variabili del negozio oltre $941F"

        .include "macros.inc"

scrrow_lo
        .for i = 0, i < 25, i = i + 1
        .byte <(SCR_A + i*40)
        .next
scrrow_hi
        .for i = 0, i < 25, i = i + 1
        .byte >(SCR_A + i*40)
        .next

; voci dello zaino (PACK_N = 8: due colonne da 4, dalla riga de_y)
ue_x    .byte 1,1,1,1, 20,20,20,20
        .cerror PACK_N != 8, "tabella ue_x: 2 colonne da 4"


; ------------------------------------------------------------------ primitive
ui_begin:
        jsr core_need           ; (21/11, TODO D15) le schermate usano il segmento CORE: se manca si rilegge
ui_begin0:                      ; (io_screen: senza, perche' durante un salvataggio CORE e' coperto dall'immagine)
        jsr irq_off
        lda #0
        sta SPR_EN
        sta BORDER
        sta BGCOL
        sta sh_mask
        sta tp_on               ; in UI lo schermo A e' testo: set_tile non deve toccarlo
        lda #UC_BOX
        sta ui_bc
        lda #0
        sta ti_row
        lda #UC_TITLE
        sta ti_col
        lda #$de                ; schermo $B400, charset UI a $B800
        sta VIC_MEM
        lda #$08
        sta VIC_CTRL2
        lda #$1b
        sta VIC_CTRL1
        ldy #0
_c      lda #$20
        sta SCR_A,y
        sta SCR_A+$100,y
        sta SCR_A+$200,y
        sta SCR_A+$300,y
        lda #1
        sta COLRAM,y
        sta COLRAM+$100,y
        sta COLRAM+$200,y
        sta COLRAM+$300,y
        iny
        bne _c
        rts

; X = colonna, Y = riga
; colori dei testi: riga 0 = titolo, righe 23-24 = aiuto, resto = etichette
UC_TITLE = 7
UC_HELP  = 12
UC_LABEL = 3
UC_VALUE = 7                    ; numeri (statistiche, quantita', prezzi): gialli (08/11, prima bianchi)
UC_ITEM  = 1                    ; nome di un oggetto normale (bianco)
UC_CURSED = 12                  ; (fase 5, O7) nome di un oggetto con un affisso maledetto (grigio; 11 e' "posto vuoto")
UC_CURSOR = 13
UC_MAGIC = 14
UC_UNIQUE = 7                   ; (22/11, fase 6, O7) nome di un unico (giallo)
; (21/11 sera) codici ui_lc dei negozi (src/menu/shop.asm sh_cur): 0..7 zaino, 8..12 equipaggiamento (PACK_N + posto), LC_W + n merce,
; LC_B + n cintura. Prima la merce partiva da 12, che e' anche il secondo anello indossato (EQ_N = 5 dal 21/11): Fire sul secondo
; anello dall'alchimista comprava la prima merce
LC_W     = 16
LC_B     = 24
        .cerror LC_W < PACK_N + EQ_N || LC_B < LC_W + 8, "codici ui_lc dei negozi sovrapposti"
UC_EMPTY = 11
UC_BOX   = 11                   ; cornici grigio scuro (08/11, prima 15)
UC_BTTL  = 15                   ; titoli sulle cornici: grigio chiaro (ui_at li riconosce: iniziano sopra BOX_H)
BOX_H    = 28
BOX_V    = 30
BOX_TL   = 31
BOX_TR   = 59
BOX_BL   = 60
BOX_BR   = 0
CH_CURS  = 64                   ; (21/11 sera) icone di seguito da 64 (tools/build/gen_font.py): spazio invertito, cursore dei campi
UIF_N     = 80                   ; glifi del font della UI; da $B800 + UIF_N x 8 a $BBFF RAM libera (gd_font)
CH_KEY   = 65
CH_COIN  = 66                   ; una moneta (08/11: prima un mucchio di 2 caratteri, 92-93)
CH_POT   = 68
CH_SCR   = 69
CH_ANVIL = 34
CH_SHLD  = 35
CH_FLASK = 36
CH_SWORD = 70                   ; icone dell'equipaggiamento
CH_ARMOR = 71                   ; (lo scudo e' CH_SHLD)
CH_RING  = 72
CH_SKULL = 73                  ; teschio (09/11: titolo della schermata di morte)
CH_INN   = 74                  ; boccale (09/11: titolo della locanda)
CH_ARROW = 67                   ; freccia a destra (15/11: schermata C, "valore -> nuovo" dei punti in attesa)
CH_EQ    = 75                  ; (21/11, liste a scorrimento) spunta: oggetto indossato
CH_BELT  = 76                  ; posto della cintura
CH_SEP   = 77                  ; separatore sottile fra i blocchi di una lista
CH_THUMB = 78                  ; cursore della barra di scorrimento
CH_PACK  = 79                  ; zaino: oggetto nello zaino

ui_at:
        lda #UC_LABEL
        cpy #0
        bne +
        lda #UC_TITLE
+       cpy #23
        bcc +
        lda #UC_HELP
+       sta ui_col
        lda scrrow_lo,y
        sta cp
        lda scrrow_hi,y
        sta cp+1
        txa
        clc
        adc cp
        sta cp
        bcc _n
        inc cp+1
_n      lda cp
        sta ccp
        lda cp+1
        clc
        adc #>(COLRAM-SCR_A)
        sta ccp+1
        tya                     ; (Y e X restano quelli del chiamante)
        pha
        ldy #0
        lda (cp),y              ; testo che parte sopra una cornice: e' il titolo del riquadro
        cmp #BOX_H
        bne +
        lda #UC_BTTL
        sta ui_col
+       pla
        tay
        lda #0
        sta cidx
        rts

; A = carattere: alla posizione corrente (cp/ccp + cidx) con il colore ui_col (il cursore '>' nel suo colore), avanza
ui_putc:
        ldy cidx
        sta (cp),y
        cmp #$3e                ; cursore '>'
        bne _c
        lda #UC_CURSOR
        bne _s
_c      lda ui_col
_s      sta (ccp),y
        inc cidx
        rts

; A/X = puntatore a stringa terminata da 0
ui_puts:
        sta ptr2
        stx ptr2+1
        lda #0
        sta tmp5
_l      ldy tmp5
        lda (ptr2),y
        beq _d
        jsr ui_putc
        inc tmp5
        jmp _l
_d      rts

; stringa a 5 bit in linea dopo la JSR (#msg; 21/11 sera, prima testo normale con lo 0 finale)
ui_pi:
        pla
        sta ptr2
        pla
        sta ptr2+1
        inc ptr2                ; (l'indirizzo sulla pila e' quello dell'ultimo byte della JSR)
        bne +
        inc ptr2+1
+       jsr ui_p5
        lda ptr2                ; ptr2 = dopo il testo: si torna a ptr2 (rts aggiunge 1)
        bne +
        dec ptr2+1
+       dec ptr2
        lda ptr2+1
        pha
        lda ptr2
        pha
        rts
; A/X = stringa a 5 bit (#t5): stampa con ui_putc
ui_puts5:
        sta ptr2
        stx ptr2+1
ui_p5:  lda #0
        sta d5_n
-       jsr d5_get
        beq +
        jsr ui_putc
        jmp -
+       rts

; ---- (21/11 sera) decodificatore del testo a 5 bit (macro t5 in src/common/macros.inc): ptr2 = testo, d5_n = 0 all'inizio di
; una stringa. A = carattere (codice schermo), 0 = fine (flag Z). Dopo la fine ptr2 punta al byte dopo la stringa. Usa X
d5_get: jsr d5_sym
        beq _r                  ; fine
        cmp #27
        bcc _r                  ; lettere: codice schermo = simbolo
        cmp #31
        beq _x
        tax
        lda d5_t1-27,x          ; spazio : . /
        rts
_x      jsr d5_sym
        tax
        lda d5_t2,x             ; cambio: cifre e segni rari (T5X)
_r      rts
d5_sym: lda d5_n                ; prossimo simbolo di 5 bit
        bne _hv
        ldy #0                  ; parola nuova (byte alto prima): via il bit 15, 3 simboli
        lda (ptr2),y
        sta d5_h
        iny
        lda (ptr2),y
        sta d5_l
        lda ptr2
        clc
        adc #2
        sta ptr2
        bcc +
        inc ptr2+1
+       asl d5_l
        rol d5_h
        lda #3
        sta d5_n
_hv     dec d5_n
        lda #0
        ldx #5
-       asl d5_l
        rol d5_h
        rol a
        dex
        bne -
        cmp #0
        rts
d5_t1   .text " :./"
d5_t2   .text "0123456789?-+!,'()>%"   ; = T5X di src/common/macros.inc (stesso ordine)
        .byte CH_COIN           ; (22/11) '$' nel testo a 5 bit: la moneta (premio del borsello, "purse: upgrade $1000")

;; (10/11) oro del baule a decine: tmp0..2 = A/X x 10 (24 bit; usa tmp3..5)
ui_x10: sta tmp0
        stx tmp1
        lda #0
        sta tmp2
        asl tmp0                ; x2
        rol tmp1
        rol tmp2
        lda tmp0
        sta tmp3
        lda tmp1
        sta tmp4
        lda tmp2
        sta tmp5
        ldx #2                  ; x8
-       asl tmp0
        rol tmp1
        rol tmp2
        dex
        bne -
        lda tmp0                ; x8 + x2 = x10
        clc
        adc tmp3
        sta tmp0
        lda tmp1
        adc tmp4
        sta tmp1
        lda tmp2
        adc tmp5
        sta tmp2
        rts

; (11/11, O2) oro totale = addosso + baule della locanda (c_gold + 10 x c_sgold) -> tmp0..2 (negozi, scheda del barbaro)
gold_total:
        lda c_sgold
        ldx c_sgold+1
        jsr ui_x10
        jsr t01_addg
        bcc +
        inc tmp2
+       rts

; (15/11, TODO D12) tmp0:1 += c_gold (C = riporto); anche g_mul10 (stash_io.asm)
t01_addg:
        lda tmp0
        clc
        adc c_gold
        sta tmp0
        lda tmp1
        adc c_gold+1
        sta tmp1
        rts

; (10/11) numero a 24 bit tmp0..2 (al massimo 999999) in 6 caratteri allineati a destra, colori come ui_num5
ui_num6:
        lda ui_col
        pha
        lda #UC_VALUE
        ldy ui_fc
        beq +
        lda ui_fc
+       sta ui_col
        lda #0
        sta tmp4                ; 1 = gia' stampata una cifra
        tax
_dg     lda #0
        sta tmp5
_sub    lda tmp0
        sec
        sbc p6l,x
        pha
        lda tmp1
        sbc p6m,x
        tay
        lda tmp2
        sbc p6h,x
        bcc _no
        sta tmp2
        sty tmp1
        pla
        sta tmp0
        inc tmp5
        bne _sub
_no     pla
        lda tmp5
        ora tmp4
        bne _show
        cpx #5
        beq _show
        lda ui_nl               ; allineato a sinistra: niente spazi iniziali
        bne _nx
        lda #$20
        bne _out
_show   lda #1
        sta tmp4
        lda tmp5
        ora #$30
_out    jsr ui_putc
_nx     inx
        cpx #6
        bne _dg
        pla
        sta ui_col
        rts
p6l     .byte 100000 & 255, 10000 & 255, 1000 & 255, 100, 10, 1
p6m     .byte (100000 >> 8) & 255, 10000 >> 8, 1000 >> 8, 0, 0, 0
p6h     .byte 100000 >> 16, 0, 0, 0, 0, 0

; tmp0/tmp1 = numero a 16 bit: ui_num5 in 5 cifre, ui_num3 in 3 (destra, spazi davanti; ui_nl = 1: a sinistra);
; colore UC_VALUE, o ui_fc se impostato
ui_num5:
        ldx #0
        beq ui_numx
ui_num3:
        ldx #2
ui_numx:
        lda ui_col
        pha
        lda #UC_VALUE
        ldy ui_fc
        beq _nfc
        lda ui_fc
_nfc    sta ui_col
        lda #0
        sta tmp4
_dg     lda #0
        sta tmp5
_sub    lda tmp0
        sec
        sbc p10l,x
        tay
        lda tmp1
        sbc p10h,x
        bcc _done
        sta tmp1
        sty tmp0
        inc tmp5
        jmp _sub
_done   lda tmp5
        bne _show
        lda tmp4
        bne _show
        cpx #4
        beq _show
        lda ui_nl
        bne _nx
        lda #$20
        bne _out
_show   lda #1
        sta tmp4
        lda tmp5
        clc
        adc #$30
_out    jsr ui_putc
_nx      inx
        cpx #5
        bne _dg
        pla
        sta ui_col
        rts

; stampa A senza spazi iniziali
ui_b3l:
        ldx #1
        stx ui_nl
        jsr ui_b3
        ldx #0
        stx ui_nl
        rts

; A = byte basso, X = byte alto: numero a 16 bit allineato a sinistra
ui_n5l:
        sta tmp0
        stx tmp1
        ldx #1
        stx ui_nl
        jsr ui_num5
        ldx #0
        stx ui_nl
        rts

; A/X = numero a 16 bit allineato a sinistra; da 10000 in su in migliaia senza decimali con "k" (come hput_k dell'HUD)
ui_n5k:
        cpx #>10000
        bcc ui_n5l
        bne _k
        cmp #<10000
        bcc ui_n5l
_k      sta tmp0
        stx tmp1
        ldy #0
_l      lda tmp0
        sec
        sbc #<1000
        sta tmp0
        lda tmp1
        sbc #>1000
        sta tmp1
        bcc _d
        iny
        bne _l
_d      tya
        jsr ui_b3l
ui_k:   lda ui_col              ; (15/11, D12) 'k' nel colore dei valori, ui_col conservato
        pha
        lda #UC_VALUE
        sta ui_col
        lda #'k'
        jsr ui_putc
        pla
        sta ui_col
        rts

; stampa A (0..255) su 3 cifre
ui_b3:
        sta tmp0
        lda #0
        sta tmp1
        jmp ui_num3

; (21/11, TODO D15) qui c'era codice ora nel segmento CORE (src/game/inv.asm)
; un fotogramma di una schermata della UI: attesa del vblank, contatore, effetti sonori, lettura di joystick e tastiera
ui_input:
        jsr wait_vblank
        inc frame
        jsr sfx_update
        jmp read_input

; A<>0 se fuoco/Return appena premuto
ui_fire:
        lda joynew
        and #$10
        bne _y
        lda keynew
        and #$02
        bne _y
        lda #0
        rts
_y      lda #1
        rts

; chiusura della minimappa: fire/spazio/RETURN, RUN/STOP o M (A<>0)
mm_close:
        jsr ui_fire
        bne _r
        lda keynew+7
        and #$80
        bne _r
        lda keynew+4
        and #$10
_r      rts

clear_row:                      ; Y = riga
        ldx #0
        jsr ui_at
        lda #$20
        ldy #0
_c      sta (cp),y
        iny
        cpy #40
        bne _c
        rts

; uscita da una schermata della UI: palette, camera e finestra di gioco ridisegnate, HUD e sprite, i tasti che hanno
; chiuso la schermata non valgono nel gioco, IRQ riacceso
ui_exit:
        jsr pal_for_level
        jsr set_palette
        lda #0
        sta BORDER
        jsr update_camera
        lda #1
        sta force_redraw
        sta tp_on               ; di nuovo in gioco: set_tile aggiorna lo schermo
        jsr maybe_redraw
        jsr hud_full
        jsr build_sprites
        jsr apply_frame
        lda #0                  ; (11/11) il tasto o il Fire che ha chiuso la schermata non vale anche nel gioco:
        sta joynew              ; act_tick e handle_keys dello stesso giro leggevano ancora joynew/keynew del menu
        ldx #7                  ; (bug: "resume" del menu di gioco davanti a una porta riapriva il negozio; UI-MENU-10)
-       sta keynew,x
        dex
        bpl -
        jmp irq_on

; cursore su/giu' (wrap su ui_n)
cur_up:
        ldx ui_cur
        dex
        bpl _s
        ldx ui_n
        dex
_s      stx ui_cur
        rts

; cursore giu' (con giro su ui_n)
cur_dn:
        ldx ui_cur
        inx
        cpx ui_n
        bcc _s
        ldx #0
_s      stx ui_cur
        rts

; ------------------------------------------------------------------ motore dei menu (07/11 sera)
; Ogni schermata e' una lista di voci: tb_n linguette (in fila, riga tb_y) e ui_n voci di lista (ui_cur).
; Ordine del cursore: linguette da sinistra a destra, poi la lista dall'alto in basso, con giro.
; Su/giu' = joystick o W/S (read_input), fire/spazio/RETURN = conferma, RUN/STOP = indietro.
; Sinistra/destra (e A/D) non fanno nulla. ui_nav: un fotogramma; A = NAV_*.
NAV_NONE = 0
NAV_MOVE = 1
NAV_FIRE = 2                    ; fire su una voce della lista (ui_cur)
NAV_TAB  = 3                    ; fire con la lista vuota (11/11: niente piu' linguette)
NAV_BACK = $ff                  ; RUN/STOP

; inizio di una schermata: cursore sulla voce 0 della lista. (11/11, O1: le linguette non le usava nessuna schermata:
; tolte; con la lista vuota ui_lc = $FF e Fire da' NAV_TAB come prima, che le schermate senza voci ignorano)
nav_init:
        jsr read_input          ; tasti gia' premuti all'apertura (fire, I, RUN/STOP...) non contano come nuovi
        lda #0
        sta ui_cur
nav_sync:
        lda ui_cur
        ldx ui_n
        bne +
        lda #$ff                ; lista vuota: nessuna voce sotto il cursore
+       sta ui_lc
        rts

; un fotogramma del motore dei menu: A = NAV_BACK (RUN/STOP), NAV_MOVE (su/giu': ui_cur cambiato), NAV_FIRE (Fire su
; una voce), NAV_TAB (Fire con la lista vuota), NAV_NONE
ui_nav:
        jsr ui_input
.if NOKEYS                      ; build degli screenshot: la schermata resta com'e' (in VICE, prima del ciclo di
        lda #NAV_NONE           ; gioco, compare un RUN/STOP fantasma: visto il 07/11 sera, causa non trovata)
        rts
.endif
        lda keynew+7
        and #$80
        beq _nb
        lda #NAV_BACK
        rts
_nb     lda joynew
        lsr
        bcs _up
        lsr
        bcs _dn
        jsr ui_fire
        beq _r
        lda ui_n
        beq _tb
        lda #NAV_FIRE
_r      rts
_tb     ldx #0
        lda #NAV_TAB
        rts
_up     ldx ui_cur
        dex
        bpl _sc
        ldx ui_n                ; dalla prima voce: l'ultima (giro)
        dex
        bpl _sc
_no     lda #NAV_NONE           ; lista vuota: niente da muovere
        rts
_dn     ldx ui_n
        beq _no
        ldx ui_cur
        inx
        cpx ui_n
        bcc _sc
        ldx #0                  ; dopo l'ultima voce: la prima (giro)
_sc     stx ui_cur
        jsr nav_sync
        lda #NAV_MOVE
        rts

; testi in linea dopo la JSR: x, y, testo, 0, ... $ff (08/11: dal modulo LOBBY, usata anche dalla casa)
ui_labels:
        pla                     ; (21/11 sera) dopo la JSR: x, y, testo a 5 bit (#t5), ...; x = $ff fine
        sta ptr2
        pla
        sta ptr2+1
        inc ptr2
        bne _n
        inc ptr2+1
_n      ldy #0
        lda (ptr2),y
        cmp #$ff
        beq _e
        tax
        iny
        lda (ptr2),y
        tay
        jsr ui_at
        lda ptr2
        clc
        adc #2
        sta ptr2
        bcc +
        inc ptr2+1
+       jsr ui_p5
        jmp _n
_e      lda ptr2+1              ; ptr2 sul $ff: si torna li' (rts aggiunge 1)
        pha
        lda ptr2
        pha
        rts

; riga 24: i tasti, uguali in tutte le schermate
nav_help:
        #at 1,24
        #msg "fire:select  run/stop:back"
        rts

; (21/11) tolte draw_entries, eq_draw, sec_frames, list8, purse_draw, ibox_show/ibox_top, sh_cur1 e ch_item: la vecchia
; interfaccia comune di inventario, negozi, locanda e baule (ora le liste a scorrimento, src/game/slist.asm)
; (21/11, TODO D15) qui c'era codice ora nel segmento CORE (src/game/inv.asm)

; ------------------------------------------------------------------ inventario
; inventario (21/11, liste a scorrimento: slist.asm): statistiche (titolo = nome) in 3 righe, lista "items" da 10 righe
; (indossati con la spunta, riga sottile, cintura, riga sottile, zaino con i posti liberi '-'), riquadro dell'oggetto
; (titolo = icona e nome). Riga 23 domande e messaggi, 24 tasti. fire = usa (indossa, togli, bevi, pergamena), DEL =
; elimina (con conferma), RUN/STOP o I = chiude. ui_cur = posto dell'oggetto sotto il cursore (0..PACK_N-1 zaino,
; PACK_N.. equipaggiamento, $20+n cintura: per ora solo da guardare) per inv_act e inv_delete.
IV_LY   = 7                     ; prima riga della lista
IV_LH   = 10                    ; righe della lista
IV_SY   = 18                    ; riquadro dell'oggetto (riga del titolo)
; (21/11, TODO D15) qui c'era codice ora nel segmento CORE (src/game/inv.asm)
; schermata dell'inventario (tasto I): e' nel segmento CORE, che va prima assicurato (chi la apre non e' una schermata)
ui_inventory:
        jsr core_need
        jmp iv_main
; (15/11, TODO D12) glifo A del riquadro in (X,Y) nel colore delle cornici (ui_bc)
bx_g:   pha
        jsr ui_at
        lda ui_bc
        sta ui_col
        pla
        jmp ui_putc

; riquadro: bx,by,bw,bh (bordo grigio, interno non toccato)
ui_box:
        ldx bx
        ldy by
        lda #BOX_TL
        jsr bx_g
        ldx bw
        dex
        dex
_t      lda #BOX_H
        jsr ui_putc
        dex
        bne _t
        lda #BOX_TR
        jsr ui_putc
        lda by
        clc
        adc bh
        tax
        dex
        stx bend
        lda by
        sta br
_side   inc br
        lda br
        cmp bend
        beq _bot
        ldx bx
        ldy br
        lda #BOX_V
        jsr bx_g
        lda bx
        clc
        adc bw
        tax
        dex
        ldy br
        lda #BOX_V
        jsr bx_g
        jmp _side
_bot    ldx bx
        ldy bend
        lda #BOX_BL
        jsr bx_g
        ldx bw
        dex
        dex
_b2     lda #BOX_H
        jsr ui_putc
        dex
        bne _b2
        lda #BOX_BR
        jmp ui_putc


; riquadri da una tabella (x, y, larghezza, altezza): A/X = tabella, Y = 4 x numero di riquadri
ui_boxes:
        sta ptr2
        stx ptr2+1
        sty tb_n                ; (contatore dei riquadri: 11/11 tb_n serve solo qui)
        ldy #0
_b      sty tb_i
        lda (ptr2),y
        sta bx
        iny
        lda (ptr2),y
        sta by
        iny
        lda (ptr2),y
        sta bw
        iny
        lda (ptr2),y
        sta bh
        jsr ui_box
        lda tb_i
        clc
        adc #4
        tay
        cpy tb_n
        bne _b
        rts

; (11/11, O9) chiavi alla posizione corrente: icona, spazio, "n/10" (purse e inventario)
keys_n:
        lda #CH_KEY
        ldx #15
        jsr ui_icon
        lda #$20
        jsr ui_putc
        lda c_keys
        jsr ui_b3l
        #msg "/10"
        rts


; oggetto X delle tabelle dello zaino (PACK_N.. = equipaggiamento) -> ui_sel, tmp5, ui_dur, ui_durm
ibox_ld:
        lda c_pack,x
        sta ui_sel
        lda c_packb,x
        sta ui_px
        lda c_packs,x
        sta ui_sx
        lda c_packd,x
        sta ui_dur
        lda c_packm,x
        sta ui_durm
        rts



; Fire nell'inventario sul posto ui_cur (anche dalla locanda): zaino = usa o indossa, indossato = toglie (non l'arma)
inv_act:
        ldx ui_cur
        cpx #PACK_N
        bcc _pk
        cpx #PACK_N+EQ_N        ; (21/11) cintura ($20+n): per ora solo da guardare
        bcs _r1
        jmp _unequip
_no1    jmp _no
_dr     jmp _drink
_r1     rts
_pk     lda c_pack,x
        beq _r1
        tay
        lda itcat,y
        cmp #CAT_POTION
        beq _dr
        cmp #CAT_SCROLL
        beq _r1
        jsr req_chk             ; (21/11, O6) FOR o DES richiesta: con meno non si indossa
        bcs _no1
        lda itcat,y
        cmp #CAT_SHIELD         ; scudo con un'arma a due mani: no
        bne _ns
        ldx c_eq
        lda itfl,x
        and #1
        bne _no1
_ns     lda itcat,y
        cmp #CAT_WEAPON         ; arma a due mani con uno scudo: lo scudo torna nello zaino
        bne _sw
        lda itfl,y
        and #1
        beq _sw
        lda c_eq+2
        beq _sw
        ldx #PACK_N             ; posto libero per lo scudo (oltre a quello dell'arma)
        jsr inv_free
        bcs _no1
        ldy #2
        jsr eq_get
        jsr pk_put
        ldy #2
        jsr eq_zero
        ldx ui_cur
        ldy c_pack,x
_sw     lda #0
        sta iv_rr
        lda itcat,y             ; scambio zaino <-> equipaggiamento (posto = categoria - 1)
        sec
        sbc #1
        cmp #EQ_RING            ; (21/11) anelli: il primo posto libero; con due anelli si sostituisce quello di valore minore
        bne _ty
        ldx c_eq+EQ_RING
        beq _ty
        lda #EQ_RING+1
        ldy c_eq+EQ_RING+1
        beq _ty
        inc iv_rr
        lda itval,x
        cmp itval,y
        lda #EQ_RING+1
        bcs _ty
        lda #EQ_RING
_ty     tay
        jsr eq_get              ; vecchio equipaggiamento -> it_*
        ldx ui_cur
        jsr pk_swap             ; it_* <-> posto dello zaino
        ldy tmp6
        jsr eq_put              ; nuovo equipaggiamento
        lda iv_rr
        beq _after
        jsr msg23               ; "replaced silver ring dex" (l'anello tolto e' finito nello zaino al posto del nuovo)
        #msg "replaced "
        ldx ui_cur
        lda c_packb,x
        sta ui_ib
        lda c_packs,x
        sta ui_is
        lda #16                 ; (22/11) colonne del nome (ui_item)
        sta ui_w
        lda c_pack,x
        jsr ui_item
        jmp _after
_drink  jsr drink               ; Y = pozione (ricarica, vita piena: niente)
        bcs _r
        ldx ui_cur
        jsr pk_zero
        jmp _after
_unequip cpx #PACK_N            ; l'arma non si toglie (il PG ha sempre un'arma): si sostituisce
        beq _no
        lda c_pack,x
        beq _r
        ldx #PACK_N
        jsr inv_free
        bcs _r
        ldy ui_cur              ; posto dell'equipaggiamento (PACK_N + categoria - 1)
        jsr eq_get
        jsr pk_put
        ldy ui_cur
        jsr eq_zero
_after  jsr recalc_stats
        jmp sort_pack
_no     lda #2                  ; rifiutato: lampo rosso
        ldx #6
        jmp set_flash
_r      rts

; ---- oggetti: 4 tabelle parallele (id, bonus, durabilita', massimo). it_* = oggetto in transito
; Y = posto dell'equipaggiamento (0..EQ_N-1, o PACK_N..PACK_N+EQ_N-1) -> it_*
eq_get: jsr eq_y
        lda c_eq,y
        sta it_i
        lda c_eqb,y
        sta it_b
        lda c_eqs,y
        sta it_s
        lda c_eqd,y
        sta it_d
        lda c_eqm,y
        sta it_m
        rts
; Y = PACK_N.. -> 0.. (posto dell'equipaggiamento); tmp6 = Y
eq_y:   cpy #PACK_N
        bcc +
        tya
        sbc #PACK_N
        tay
+       sty tmp6
        rts
; it_* -> posto Y dell'equipaggiamento
eq_put: lda it_i
        sta c_eq,y
        lda it_b
        sta c_eqb,y
        lda it_s
        sta c_eqs,y
        lda it_d
        sta c_eqd,y
        lda it_m
        sta c_eqm,y
        rts
; posto Y (0..EQ_N-1, o PACK_N..) dell'equipaggiamento vuoto
eq_zero: jsr eq_y
        lda #0
        sta c_eq,y
        sta c_eqb,y
        sta c_eqs,y
        sta c_eqd,y
        sta c_eqm,y
        rts
; X = posto dello zaino
pk_put: lda it_i
        sta c_pack,x
        lda it_b
        sta c_packb,x
        lda it_s
        sta c_packs,x
        lda it_d
        sta c_packd,x
        lda it_m
        sta c_packm,x
        rts
; posto X dello zaino vuoto
pk_zero: lda #0
        sta c_pack,x
        sta c_packb,x
        sta c_packs,x
        sta c_packd,x
        sta c_packm,x
        rts
pk_swap: lda c_pack,x           ; it_* <-> posto X dello zaino
        pha
        lda it_i
        sta c_pack,x
        pla
        sta it_i
        lda c_packb,x
        pha
        lda it_b
        sta c_packb,x
        pla
        sta it_b
        lda c_packs,x
        pha
        lda it_s
        sta c_packs,x
        pla
        sta it_s
        lda c_packd,x
        pha
        lda it_d
        sta c_packd,x
        pla
        sta it_d
        lda c_packm,x
        pha
        lda it_m
        sta c_packm,x
        pla
        sta it_m
        rts

; (21/11 sera, in GAME per lo spazio di CORE; af_names sta in CORE: solo dalle schermate) A = indice dell'affisso (1..AF_NP prefisso, AF_SX0 + s suffisso): il suo nome (af_names, CORE) fino a ui_lim
af_name:
        tax
        lda #<af_names
        sta ptr2
        lda #>af_names
        sta ptr2+1
; X-esima stringa (da 1) della lista a 5 bit in ptr2
af_nth:
_w      dex                     ; (21/11 sera) nomi a 5 bit: si salta una stringa decodificandola
        beq ip_p5
        stx af_t
        lda #0
        sta d5_n
-       jsr d5_get
        bne -
        ldx af_t
        jmp _w
; A/X = stringa a 5 bit (#t5) stampata fino alla colonna ui_lim esclusa (i nomi lunghi si tagliano)
ip_puts:
        sta ptr2
        stx ptr2+1
ip_p5:  lda #0
        sta d5_n
-       jsr d5_get
        beq +
        jsr ip_putc
        jmp -
+       rts
ip_putc:
        inc ui_nlen             ; (fase 5) lunghezza del nome completo e caratteri saltati del nome scorrevole
        ldy ui_sk
        beq +
        dec ui_sk
        rts
+       ldy cidx
        cpy ui_lim
        bcs +
        jmp ui_putc
+       rts
af_of   #t5 " of "
; (22/11, da ui_item in CORE) X = id: "[prefisso ]nome[ of suffisso]" (ui_ib, ui_is) fino a ui_lim; (fase 6) unico (ui_is =
; $80 + u): il suo nome (un_names, db.asm)
it_nm:  lda ui_is
        bpl _px
        and #$7f
        tax
        inx
        lda #<un_names
        sta ptr2
        lda #>un_names
        sta ptr2+1
        jmp af_nth
_px     lda ui_ib               ; prefisso
        beq _nb
        stx af_k
        jsr af_name
        lda #$20
        jsr ip_putc
        ldx af_k
_nb     lda itnm_lo,x
        pha
        lda itnm_hi,x
        tax
        pla
        jsr ip_puts
        lda ui_is               ; suffisso
        beq _r
        lda #<af_of
        ldx #>af_of
        jsr ip_puts
        lda ui_is
        clc
        adc #AF_SX0
        jmp af_name
_r      rts
; (fase 5, O8) poteri degli affissi dell'oggetto mostrato (ui_px, ui_sx) che non stanno gia' nei numeri della riga: "hp+12",
; "hit-1" (danno subito in meno), "spd+2", "pen+1", "str+1" (non per gli anelli: la prima caratteristica e' gia' nella riga),
; "ind" (indistruttibile), fino alla colonna 34
it_pw:  lda ui_px
        jsr _one
        lda ui_sx
        bne +
        rts
+       bpl +
        ldx #<_one              ; (fase 6) unico: le sue 4 righe
        ldy #>_one
        jmp af_rowv
+       clc
        adc #AF_SX0
_one    tay
        beq _r
        lda cidx
        cmp #34
        bcs _r
        ldx af_pw,y
        beq _r                  ; (riga vuota di un unico)
        lda pw_tx-1,x           ; 0 = gia' nei numeri (o nella durabilita')
        beq _r
        cpx #PW_ALL+1           ; caratteristiche: non per gli anelli
        bcs +
        cpx #PW_STR
        bcc +
        ldx ui_sel
        lda itcat,x
        cmp #CAT_RING
        beq _r
        ldx af_pw,y
+       sty af_t
        inc cidx
        txa                     ; 3 caratteri: pw_t1/2/3
        tax
        lda pw_tx-1,x
        jsr ui_putc
        lda pw_t2-1,x
        jsr ui_putc
        lda pw_t3-1,x
        cmp #$20
        beq +
        jsr ui_putc
+       cpx #PW_INDESTRUCTIBLE
        beq _r
        ldy af_t
        lda af_val,y
        cpx #PW_GETHIT
        beq _m
        tax
        bmi _n
        lda #$2b                ; '+'
        jsr ui_putc
        txa
        jmp ui_b3l
_n      lda #$2d
        jsr ui_putc
        txa
        eor #$ff
        clc
        adc #1
        jmp ui_b3l
_m      pha
        lda #$2d                ; danno subito: "-N"
        jsr ui_putc
        pla
        jmp ui_b3l
_r      rts
; 3 caratteri per potere (PW_ATT_DMG .. PW_THORNS); 0 = non mostrato qui
pw_tx   .byte 0, 0, 0, 0        ; att/dmg, att, dmg, ac: gia' nei numeri; poi str dex con all  hp hit pen spd (dur: 0) ind lch thn
        .text "sdca hps"
        .byte 0
        .text "ilt"
pw_t2   .byte 0, 0, 0, 0
        .text "teolhiep"
        .byte 0
        .text "nch"
pw_t3   .byte 0, 0, 0, 0
        .text "rxnlptnd"
        .byte 0
        .text "dhn"
        .cerror PW_THORNS != 16 || PW_STR != 5, "pw_tx: tabella dei poteri"
        .cerror pw_t2 - pw_tx != 16, "pw_tx: 16 poteri"

; (fase 5, O7) colore di un oggetto con affissi (ui_ib prefisso, ui_is suffisso): grigio se uno dei due e' maledetto (valore
; negativo), altrimenti azzurro; (fase 6) unico giallo. A = colore; X conservato
it_qcol:
        lda ui_is
        bmi _u
        ldy ui_ib
        lda af_val,y
        bmi _c
        lda ui_is
        beq _m
        clc
        adc #AF_SX0
        tay
        lda af_val,y
        bmi _c
_m      lda #UC_MAGIC
        rts
_c      lda #UC_CURSED
        rts
_u      lda #UC_UNIQUE
        rts

; (21/11, O6) requisito dell'oggetto Y (itreq: bit 7 = DES, s_dex; altrimenti FOR, s_str; valore nei bit 0-6, 0 = nessuno):
; C = 1 se non raggiunto. X e Y conservati
req_chk:
        lda itreq,y
        bmi _d
        cmp s_str
        beq _ok
        rts                     ; C = 1 se richiesto > FOR
_d      and #$7f
        cmp s_dex
        beq _ok
        rts
_ok     clc
        rts

; X = posti dello zaino da cercare (PACK_N): X = primo posto libero. C=1 se lo zaino e' pieno
inv_free:
        stx tmp6
        ldx #0
_f      lda c_pack,x
        beq _y
        inx
        cpx tmp6
        bne _f
        sec
        rts
_y      clc
        rts

; elimina la voce selezionata (solo zaino), dopo la conferma (Y / N sulla riga dei tasti)
inv_delete:
        ldx ui_cur
        cpx #PACK_N
        bcs _r
        lda c_pack,x
        beq _r                  ; posto vuoto: niente da chiedere
        #at 1,23
        #msg "drop this item?"
        jsr ui_yesno
        php
        ldy #23
        jsr clear_row
        plp
        bcc _r
        ldx ui_cur
        jsr pk_zero
        jmp sort_pack
_r      rts

; attende si' (fire, spazio, RETURN o Y: C = 1) o no (RUN/STOP o N: C = 0). 09/11: riga dei tasti unica per tutte
; le domande, scritta qui in riga 24 ("y:yes  n:no"; fire e RUN/STOP restano sinonimi non scritti); la riga 24 di
; prima (i tasti della schermata) si salva in YN_SAV e si rimette alla risposta. La domanda la scrive il chiamante.
YN_SAV  = $0340                 ; 40 B nel buffer della cassetta (11/11: $0200-$0312 e' il residente di Krill)
ui_yesno:
        ldx #39
_sv     lda SCR_A+24*40,x
        sta YN_SAV,x
        dex
        bpl _sv
        jsr row24
        #msg "y:yes  n:no"
.if TESTUI == 33
        jmp *                   ; screenshot della domanda "quit game?"
.endif
yn_wait jsr ui_input            ; (etichetta globale: la usa tests/test_saves.py)
        jsr ui_fire             ; fire = si' (07/11 sera, docs/wiki/refactor-tasti.md)
        bne _y
        lda keynew+3
        and #$02                ; Y
        bne _y
        lda keynew+4
        and #$80                ; N
        bne _n
        lda keynew+7
        and #$80                ; RUN/STOP = N (annulla, 07/11 sera)
        beq yn_wait
_n      clc
        .byte $24               ; (bit zp: salta il sec)
_y      sec
        php
        ldx #39
_rs     lda YN_SAV,x
        sta SCR_A+24*40,x
        dex
        bpl _rs
        plp
        rts

; zaino: compatto (i vuoti in fondo) e ordinato per categoria, stabile (08/11; prima solo compattato)
sort_pack:
        lda #<sd_pack
        ldx #>sd_pack
        jmp sort4
sd_pack .byte PACK_N
        .word c_pack, c_packb, c_packd, c_packm, c_packs

; ordinamento stabile per categoria (armi, armature, scudi, anelli, pozioni, pergamene; i posti vuoti in fondo) di
; 4 tabelle parallele: id, bonus, durabilita', massimo (08/11: zaino e baule di casa sempre ordinati).
; A/X = descrittore: numero di posti (<= 32), poi i 5 indirizzi (21/11 sera: + il suffisso). Usa $FB-$FE, S4_ORD e S4_BUF (dopo LVLBLK).
S4_ORD = $9a60
S4_BUF = $9a80
sort4:  sta $fd
        stx $fe
        ldy #0
        lda ($fd),y
        sta s4_n
        iny
        lda ($fd),y
        sta $fb
        iny
        lda ($fd),y
        sta $fc
        ldx #0                  ; X = posti gia' messi in ordine (S4_ORD)
        lda #1
        sta s4_c
_cl     ldy #0                  ; una passata per categoria: i posti di quella categoria, nell'ordine di prima
_il     lda ($fb),y
        beq _e
        sty s4_t
        tay
        lda itcat,y
        ldy s4_t
        .byte $2c               ; (bit: salta l'istruzione seguente)
_e      lda #CAT_SCROLL+1       ; posto vuoto: dopo tutte le categorie
        cmp s4_c
        bne _nx
        tya
        sta S4_ORD,x
        inx
_nx     iny
        cpy s4_n
        bne _il
        inc s4_c
        lda s4_c
        cmp #CAT_SCROLL+2
        bne _cl
        lda #1                  ; le 4 tabelle, una alla volta, nell'ordine di S4_ORD
        sta s4_t
_tb     ldy s4_t
        lda ($fd),y
        sta $fb
        iny
        lda ($fd),y
        sta $fc
        iny
        sty s4_t
        ldx #0
_p1     ldy S4_ORD,x
        lda ($fb),y
        sta S4_BUF,x
        inx
        cpx s4_n
        bne _p1
        ldy #0
_p2     lda S4_BUF,y
        sta ($fb),y
        iny
        cpy s4_n
        bne _p2
        lda s4_t
        cmp #11                 ; (21/11 sera) 5 tabelle: id, bonus (prefisso), durabilita', massimo, suffisso
        bne _tb
        rts

; (21/11, TODO D15) qui c'era codice ora nel segmento CORE (src/game/inv.asm)
; (21/11, TODO D15) qui c'era codice ora nel segmento CORE (src/game/inv.asm)
; ------------------------------------------------------------------ salvataggi di un'altra versione
; Y = cancella tutto e prosegue (C=1), N = esce dal gioco (reset)
ui_badsave:
        jsr ui_begin
        #at 9,5                 ; vecchio stile (09/11, concept del committente): versioni trovata e attesa in decimale
        #msg "bad save file version"
        #at 13,8
        #msg "found    : "
        lda hdrbuf
        jsr ui_b3l
        #at 13,9
        #msg "expected : "
        lda #SAVE_VER
        jsr ui_b3l
        #at 11,12
        #msg "  destroy all data"
        #at 11,14
        #msg "  quit"
.if AUTOY
        jmp _y                  ; solo test automatici
.endif
        lda #2                  ; lista di 2 voci, cursore su "quit": fire per abitudine non cancella nulla
        sta ui_n
        jsr nav_init
        inc ui_cur
_mk     ldx #11
        ldy #12
        jsr ui_at
        ldx #0
        jsr ui_mark
        ldx #11
        ldy #14
        jsr ui_at
        ldx #1
        jsr ui_mark
_k      jsr ui_nav
        cmp #NAV_MOVE
        beq _mk
        cmp #NAV_FIRE
        bne _k
        lda ui_cur
        beq _y
        jmp LOBBY_AT+9           ; quit the game come nel menu (bb_quit: reset, BASIC)
_y      jsr ui_begin
        #at 10,9
        #msg "deleting saved games"
        jsr ui_pwait
        jsr scratch_all
        sec
        rts

; ------------------------------------------------------------------ casa: baule
; baule di casa: modulo MENU (src/menu/inn.asm, MENU_INN)

; ------------------------------------------------------------------ negozi
; (11/11) i negozi stanno nel modulo MENU (src/menu/shop.asm, caricato nel villaggio): qui restano le routine che usano
; anche inventario, baule dei dungeon e locanda (titolo, oro, '>' delle voci, riga dei messaggi, riquadro dell'oggetto
; del baule).
cat_bit .byte 0, 1<<1, 1<<2, 1<<3, 1<<4, 1<<5, 1<<6

; (11/11, O8) '>' se X = ui_cur, altrimenti spazio (domanda sì/no, leva, menu di gioco, menu dei barbari)
ui_mark:
        cpx ui_cur
        bne +
        lda #$3e
        .byte $2c
+       lda #$20
        jmp ui_putc

; titolo di ogni schermata (08/11, routine unica): riga ti_row, centrato, giallo; A/X = testo a 5 bit (#t5), Y = icona ai due lati
; (gialla; 0 = nessuna): "^ blacksmith ^", "o golden chest o", "backpack"
ui_title:
        sta ti_p                ; (21/11 sera) testo a 5 bit (#t5): la lunghezza si conta decodificando
        stx ti_p+1
        sta ptr2
        stx ptr2+1
        sty tmp7
        lda #0
        sta d5_n
        sta tmp6
-       jsr d5_get
        beq +
        inc tmp6
        bne -
+       lda tmp6                ; lunghezza (+4 con le icone e gli spazi)
        ldx tmp7
        beq +
        clc
        adc #4
+       sta tmp6
        lda #40
        sec
        sbc tmp6
        lsr
        tax
        ldy ti_row
        jsr ui_at
        lda ti_col
        sta ui_col
        lda tmp7
        beq +
        ldx ti_col
        jsr ui_icon
        lda #$20
        jsr ui_putc
+       lda ti_p
        ldx ti_p+1
        jsr ui_puts5
        lda tmp7
        beq +
        lda #$20
        jsr ui_putc
        lda tmp7
        ldx ti_col
        jmp ui_icon
+       rts

; oro (moneta + cifre a sinistra + 2 spazi: le cifre possono calare) alla posizione corrente. 10/11: nei negozi
; (sh_mask <> 0) l'oro TOTALE = addosso + baule della locanda (c_gold + 10 x c_sgold), da 100000 in migliaia con "k"
shop_gold:
        jsr ui_gold
        lda sh_mask
        bne _tot
        lda c_gold
        ldx c_gold+1
        jsr ui_n5l
        jmp _sp
_tot    jsr gold_total
        lda tmp0                ; >= 100000 ($0186A0)?
        cmp #<100000
        lda tmp1
        sbc #>(100000 & $ffff)
        lda tmp2
        sbc #100000 >> 16
        bcs _k
        lda #1
        sta ui_nl
        jsr ui_num6             ; fino a 99999: tutte le cifre, a sinistra
        lda #0
        sta ui_nl
        jmp _sp
_k      lda #0                  ; migliaia: sottrazioni di 1000 (al massimo 665)
        sta tmp6
        sta tmp7
-       lda tmp0
        sec
        sbc #<1000
        tay
        lda tmp1
        sbc #>1000
        tax
        lda tmp2
        sbc #0
        bcc +
        sta tmp2
        stx tmp1
        sty tmp0
        inc tmp6
        bne -
        inc tmp7
        bne -
+       lda tmp6
        ldx tmp7
        jsr ui_n5l
        jsr ui_k
_sp     lda #$20
        jsr ui_putc
        lda #$20
        jmp ui_putc

; moneta gialla + spazio alla posizione corrente (08/11: un glifo, in tutto il gioco): possesso "o 2350"
ui_gold:
        jsr ui_coin
        lda #$20
        jmp ui_putc
; moneta gialla (prezzi e valori: "600o")
ui_coin:
        lda #CH_COIN
        ldx #7
        jmp ui_icon

; (15/11, TODO D12) riga 24 pulita, cursore a colonna 1 (riga dei tasti): poi #msg
row24:  ldy #24
        jsr clear_row
        ldx #1
        ldy #24
        jmp ui_at

; riga dei messaggi (23) pulita, cursore all'inizio (22/11: tolto l'ingresso shop_msg_clear per la riga 22, mai usato)
msg23:  ldy #23
        ldx #1
        jsr ui_at
        lda #$20
        ldy #37
_c      sta (cp),y
        dey
        bpl _c
        rts

; ------------------------------------------------------------------ minimappa
; (15/11, TODO D2) 0,64 s -> piu' veloce: prima ogni cella 24x24 chiamava 4 volte mm_tile (get_tile + catena di confronti).
; Ora all'ingresso si costruisce UNA volta la tabella mm_cls (48 byte, un byte per codice di tile) e poi ogni cella legge
; i 4 tile della mappa con due puntatori di riga (MAP + 2 mmy * 48, +48), i bit "esplorato" (dungeon) con uno scorrimento.
; Classe di un tile (mm_cls): bit 0 pavimento/strada (quadrante disegnato), bit 1 scale giu', bit 2 scale su,
; bit 3 acqua, bit 4 strada (villaggio: cella blu se nel quadrante c'e' solo acqua). Risultato identico a prima.
; Zona di lavoro: coda dello slot sprite 27 ($A6C0..$A6FB: byte senza uso, annotazione @map in game.asm).
mm_cls  = $a6c0                 ; 48 byte
mm_ex   = $a6f0                 ; 12 byte: bit "esplorato" delle due righe di tile della riga di celle (villaggio: $FF)

; A = codice del tile -> A = classe (dungeon: esplorato o no lo decide il chiamante; solido = nulla)
mm_cdun:
        cmp #T_STAIRSD
        beq _sd
        cmp #T_TSTAIRS
        beq _sd
        cmp #T_STAIRSU
        beq _su
        tay
        lda solidtab,y
        lsr
        bcs _no
        lda #1
        rts
_sd     lda #2
        rts
_su     lda #4
        rts
_no     lda #0
        rts

; citta': 1 = strada/piazza/porte, 2 = scale per il dungeon, 0 = resto (erba, case, alberi)
mm_ctown:
        cmp #T_TSTAIRS
        beq _sd
        cmp #T_PATH
        beq _y
        cmp #T_DIRT
        beq _y
        cmp #T_BRIDGE
        beq _y
        cmp #T_COBBLE
        beq _y
        cmp #T_FOUNTAIN
        beq _y
        cmp #T_PORTAL
        beq _y
        cmp #T_DHOME
        beq _y
        cmp #T_DSMITH
        bcc _n
        cmp #T_DALCH+1
        bcc _y
_n      cmp #T_WATER            ; fiume (acqua e sponde): nella minimappa in blu
        bcc _0
        cmp #T_WATERR+1
        bcs _0
        lda #1+8
        rts
_0      lda #0
        rts
_y      lda #1+16
        rts
_sd     lda #2
        rts

; tabella mm_cls dei codici 0..47 del luogo attuale (village: costanti T_* come prima; dungeon: solidtab)
mm_build:
        ldx #47
_t      txa
        ldy cur_level
        bne _d
        jsr mm_ctown
        jmp _s
_d      jsr mm_cdun
_s      sta mm_cls,x
        dex
        bpl _t
        lda cur_level
        bne _r
        lda #$ff                ; citta': tutta visibile
        ldx #11
_f      sta mm_ex,x
        dex
        bpl _f
_r      rts

; un quadrante: classe del tile (\ptr),y se esplorato (bit basso di \ev, che scorre), poi accumula in
; mm_wat (OR delle classi), mm_st (ultime scale: 2 giu', 4 su; l'ultimo quadrante vince come prima) e mm_bits (bit 0 -> ror)
mm_q    .macro ptr, ev
        lda #0
        lsr \ev
        bcc +
        lda (\ptr),y
        tax
        lda mm_cls,x
+       tax
        ora mm_wat
        sta mm_wat
        txa
        and #6
        beq +
        sta mm_st
+       txa
        lsr
        ror mm_bits
        .endm

; minimappa (M): la mappa del luogo a celle 2x2, le caselle viste, il marcatore del PG; nel villaggio i nomi
; dei luoghi e le icone delle porte. Si chiude con Fire, M o RUN/STOP
ui_minimap:
        jsr irq_off             ; niente split raster HUD sopra la mappa
        jsr player_tile         ; ptx/pty aggiornati (coordinate nel testo in basso)
        lda #0
        sta SPR_EN
        sta BORDER
        sta BGCOL
        lda #12                 ; %01 = grigio (muri/bordi glifo)
        sta BGCOL1
        lda #2                  ; %10 = rosso (scale)
        sta BGCOL2
        lda #11                 ; colore RAM: bit3 = multicolore, %11 = ciano
        jsr col_fill
        lda #$da
        sta VIC_MEM
        lda #$18
        sta VIC_CTRL2
        lda #$1b
        sta VIC_CTRL1
        ldy #0
_c      lda #63
        sta SCR_A,y
        sta SCR_A+$100,y
        sta SCR_A+$200,y
        sta SCR_A+$300,y
        iny
        bne _c
        jsr mm_build
        lda #0
        sta mmy
_row    lda mmy                 ; puntatori delle due righe di tile (MAP + 2 mmy * 48 e la successiva)
        asl
        tax
        lda maprow_lo,x
        sta ptr0
        lda maprow_hi,x
        sta ptr0+1
        lda maprow_lo+1,x
        sta ptr1
        lda maprow_hi+1,x
        sta ptr1+1
        lda cur_level
        beq _nex                ; citta': mm_ex gia' a $FF
        lda exprow_lo,x         ; dungeon: 12 byte "esplorato" delle due righe (contigue, 6 byte ciascuna)
        sta ptr2
        lda exprow_hi,x
        sta ptr2+1
        ldy #11
_ec     lda (ptr2),y
        sta mm_ex,y
        dey
        bpl _ec
_nex    lda #0
        sta mmx
_col    lda mmx
        and #3
        bne _ne                 ; ogni 4 celle (8 tile) i prossimi byte "esplorato" delle due righe
        lda mmx
        lsr
        lsr
        tax
        lda mm_ex,x
        sta tmp0
        lda mm_ex+6,x
        sta tmp1
_ne     lda mmx
        asl
        tay                     ; Y = colonna di tile
        lda #0
        sta mm_st
        sta mm_wat
        #mm_q ptr0, tmp0        ; in alto a sinistra  (maschera 1)
        iny
        #mm_q ptr0, tmp0        ; in alto a destra    (2)
        dey
        #mm_q ptr1, tmp1        ; in basso a sinistra (4)
        iny
        #mm_q ptr1, tmp1        ; in basso a destra   (8)
        lda mm_bits
        lsr
        lsr
        lsr
        lsr
        sta mm_bits
        lda mm_st
        beq _nst
        cmp #2
        bne _up
        lda #176
        bne _w
_up     lda #177
        bne _w
_nst    lda mm_bits
        bne _gl
        lda #63
        bne _w
_gl     clc
        adc #240
_w      pha
        ldy mmy
        lda scrrow_lo,y
        clc
        adc #8
        sta ptr3
        lda scrrow_hi,y
        adc #0
        sta ptr3+1
        ldy mmx
        pla
        sta (ptr3),y
        lda mm_wat              ; solo acqua nel quadrante: cella blu (color RAM = schermo + $2400)
        and #8+16               ; (OR delle classi: bit 3 acqua, bit 4 strada)
        cmp #8
        bne _nw
        lda ptr3+1
        clc
        adc #>(COLRAM - SCR_A)
        sta ptr3+1
        lda #8+6
        sta (ptr3),y
_nw     inc mmx
        lda mmx
        cmp #24
        beq _cd
        jmp _col
_cd
        inc mmy
        lda mmy
        cmp #24
        beq _rd
        jmp _row
_rd     jsr mm_sprites
        lda cur_level
        bne _lp
        jsr mm_names            ; citta': nomi delle case negli sprite (blocchi $B000)
_lp     jsr ui_input            ; attende la riga $fc
        lda frame               ; marcatore del PG: sempre visibile, giallo/rosso
        and #8
        beq _y
        lda #2
        bne _mc
_y      lda #7
_mc     sta SPR_COL+7
        lda cur_level
        bne _k
        jsr mm_icons            ; citta': 4 icone dei luoghi (sprite 0-3), poi il testo in fondo
        lda #228
        jsr mm_wait
        ldx #2
        jsr mm_setgrp
        lda #0
        sta SPR_XEXP
        sta SPR_YEXP
_k
.if NOKEYS
        jmp _lp
.else
        jsr mm_close
        beq _lp
.endif
        lda #0
        sta SPR_EN
        jmp ui_exit

; attende la riga raster A (<256) del frame successivo al vblank
mm_wait:
        sta tmp4
_w0     lda $d012               ; ancora nelle righe 250-255 del vblank
        cmp #250
        bcs _w0
_w1     lda $d011               ; righe 256-311
        bmi _w1
_w2     lda $d012
        cmp tmp4
        bcc _w2
        rts

; registri degli sprite 0..6 per il gruppo X (0 = nomi in alto, 1 = nomi in basso, 2 = testo in fondo)
mm_setgrp:
        lda mg_off,x
        sta tmp6
        lda mg_y,x
        sta tmp4
        lda mg_en,x
        sta tmp5
        ldy #0
_l      ldx tmp6
        tya
        asl
        tax
        stx tmp3
        ldx tmp6
        lda mg_x,x
        ldx tmp3
        sta SPR_X,x
        lda tmp4
        sta SPR_X+1,x
        ldx tmp6
        lda mg_p,x
        sta SCR_A+$3f8,y
        lda mg_c,x
        sta SPR_COL,y
        inc tmp6
        iny
        cpy #7
        bne _l
        lda SPR_MSB
        and #$80
        sta SPR_MSB
        lda tmp5
        ora #$80
        sta SPR_EN
        rts

MG_B = ($b000 - $8000) / 64     ; primo blocco libero a $B000
mg_off  .byte 0, 7, 14
mg_y    .byte 98, 162, 243
mg_en   .byte $7f, $1f, $7f
mg_x    .byte 94, 118, 142, 166, 204, 228, 252
        .byte 118, 142, 196, 220, 244, 0, 0
        .byte 100, 124, 148, 172, 196, 220, 244
mg_p    .byte MG_B, MG_B+1, MG_B+2, MG_B+3, MG_B+4, MG_B+5, MG_B+6
        .byte MG_B+7, MG_B+8, MG_B+9, MG_B+10, MG_B+11, MG_B+11, MG_B+11
        .byte BARPTR, BARPTR+1, BARPTR+2, BARPTR+3, BARPTR+4, BARPTR+5, BARPTR+6
mg_c    .byte 1, 1, 1, 1, 7, 7, 7
        .byte 13, 13, 14, 14, 14, 14, 14
        .byte 15, 15, 15, 15, 15, 15, 15

; icone dei luoghi del villaggio: sprite 0..2 sopra la porta (src/game/town_places.inc), sprite 3..6 spenti
MI_N    = 3                     ; fabbro, alchimista, locanda (09/11: niente armaiolo)
mi_ic   .byte CH_ANVIL, CH_FLASK, CH_INN       ; locanda: il boccale (09/11, prima la casetta CH_HOME)
mi_c    .byte 1, 7, 13
; minimappa del villaggio: le icone di fabbro, alchimista e locanda (sprite 0-2) sulle loro porte
mm_icons:
        ldx #0
_l      txa
        asl
        tay
        lda tp_smith,y          ; colonna della porta -> x = 88 + 4 col - 6 (icona larga 16 px al centro)
        asl
        asl
        clc
        adc #82
        sta SPR_X,y
        lda tp_smith+1,y        ; riga della porta -> y = 50 + 4 riga - 20: sopra il tetto
        asl
        asl
        clc
        adc #30
        sta SPR_X+1,y
        txa
        clc
        adc #MG_B
        sta SCR_A+$3f8,x
        lda mi_c,x
        sta SPR_COL,x
        inx
        cpx #MI_N
        bne _l
        lda #0                  ; (22/11) "!" delle quest sugli NPC fissi: mm_qmark nel modulo MENU (src/menu/npc_fix.asm);
        sta tmp1                ; tmp1 = sprite dei segni, tmp2 = loro bit MSB
        sta tmp2
        lda ovl_cur
        beq +
        jsr MENU_QMMK
+
        lda SPR_MSB
        and #$80
        ora tmp2
        sta SPR_MSB
        lda #(1 << (MI_N + NFIX)) - 1   ; icone e segni a doppia grandezza (16 px)
        sta SPR_XEXP
        sta SPR_YEXP
        lda #$80 | ((1 << MI_N) - 1)
        ora tmp1
        sta SPR_EN
        rts

; blocchi MG_B..MG_B+MI_N-1: un glifo del font della UI ($B800) per icona, in alto a sinistra dello sprite
mm_names:
        lda #0
        tay
_z      sta $b000,y
        iny
        bne _z
        ldx #MI_N-1
_i      lda mi_ic,x
        ldy #$b8                ; ptr0 = $B800 + codice x 8
        jsr x8p
        txa
        lsr
        ror
        ror
        sta ptr1                ; ptr1 = $B000 + icona x 64
        lda #$b0
        sta ptr1+1
        stx tmp1
        ldy #7
_g      lda (ptr0),y
        sty tmp0
        ldx tmp0
        ldy mul3,x
        sta (ptr1),y
        ldy tmp0
        dey
        bpl _g
        ldx tmp1
        dex
        bpl _i
        rts

; ------------------------------------------------------------------ liste: voci da saltare (22/11, committente)
; Il cursore delle liste (src/game/slist.asm, segmento CORE: qui perche' CORE e' pieno) salta le righe separatrici e i posti
; vuoti ('-'). SL_NTRY tentativi per ricerca: in una lista (o due) senza oggetti il cursore si ferma su un posto vuoto.
SL_NTRY  = 64
; voce A della lista X: C = 1 se il cursore la salta (riga separatrice sempre; posto vuoto finche' ci sono tentativi:
; esauriti, si accetta). Ogni voce accettata rimette i tentativi. Come sl_get (ui_sel, sl_sl, ...). X conservato
sl_ok:  jsr sl_get
        bcs _r
        lda ui_sel
        beq _e
_y      lda #SL_NTRY
        sta sl_try
        clc
_r      rts
_e      dec sl_try
        beq _y
        sec
        rts
sl_try  .byte SL_NTRY
; lista X: dal cursore in giu' la prima voce con un oggetto (nessuna: la voce 0), poi la finestra (sl_win)
sl_fwd:
_l      lda sl_cur,x
        cmp sl_n,x
        bcs _z
        jsr sl_ok
        bcc +
        inc sl_cur,x
        bne _l
_z      lda #0
        sta sl_cur,x
+       jmp sl_win

; ---- minimappa: testo (piano, seed, coordinate x,y del PG) in 7 sprite sulla riga 24, marcatore del PG nello sprite 7
MM_MARK = $8a00                 ; blocco sprite libero (40)
mm_sprites:
        ldx #23
        lda #$20
_f      sta nbuf,x
        dex
        bpl _f
        lda #0
        sta bn_i
        lda cur_level
        bne _fl
        ldx c_chap              ; (23/11, committente) nome del villaggio del capitolo (vil_lo/vil_hi, town_places.inc)
        dex
        lda vil_lo,x
        pha
        lda vil_hi,x
        tax
        pla
        jsr bn_put
        jmp _bld
_fl     lda #<mm_chap               ; (12/11, committente) "chapter 3 level 4" per intero (17 caratteri)
        ldx #>mm_chap
        jsr bn_put
        lda cur_level
        jsr lv_grp
        inx
        stx tmp3
        jsr loc_num
        lda #<mm_lev
        ldx #>mm_lev
        jsr bn_put
        lda tmp3
        jsr loc_num
        ; (23/11, committente) niente seed e coordinate del PG nella minimappa: le coordinate sono nel menu dei trucchi,
        ; il seed nel menu di gioco (RUN/STOP)
_bld    ; costruzione sincrona negli sprite della barra (poi la barra di gioco va ricostruita)
        lda #0
        sta bt_cel
        lda #$28                ; cosi' si costruisce nel set $8800 (puntatori BARPTR della tabella mg_p)
        sta bar_fr
        lda #1
        sta bt_ph
_bs     jsr bt_step
        lda bt_ph
        bne _bs
        sei
        lda #0
        sta bt_who
        sta bar_lab
        sta bar_on
        lda #$ff
        sta lc_x
        ; marcatore: anello 7x7
        ldy #63
        lda #0
_z      sta MM_MARK,y
        dey
        bpl _z
        ldx #6
_m      lda mm_ring,x
        ldy mul3,x
        sta MM_MARK,y
        dex
        bpl _m
        ; registri
        ldx #6
_t      txa
        asl
        tay
        lda mm_sx,x
        sta SPR_X,y
        lda #243
        sta SPR_X+1,y
        lda #15
        sta SPR_COL,x
        txa
        clc
        adc #BARPTR
        sta SCR_A+$3f8,x
        dex
        bpl _t
        lda #(MM_MARK - $8000) / 64
        sta SCR_A+$3ff
        lda #7
        sta SPR_COL+7
        lda #0
        sta SPR_MC
        sta SPR_XEXP
        sta SPR_YEXP
        sta SPR_PRIO
        ; X = 85 + px/4, Y = 48 + py/4
        lda px+1
        sta tmp1
        lda px
        lsr tmp1
        ror
        lsr tmp1
        ror
        clc
        adc #85
        sta SPR_X+14
        lda #0
        adc tmp1
        beq _nx
        lda #$80
_nx     sta SPR_MSB
        lda py+1
        sta tmp1
        lda py
        lsr tmp1
        ror
        lsr tmp1
        ror
        clc
        adc #48
        sta SPR_X+15
        lda cur_level           ; dungeon: testo + marcatore sempre accesi (in citta' ci pensa mm_setgrp)
        beq _tw
        lda #$ff
        sta SPR_EN
_tw     cli
        rts
mm_sx   .byte 100, 124, 148, 172, 196, 220, 244
mm_ring .byte $38, $44, $82, $92, $82, $44, $38
mm_chap  .text "chapter ", 0             ; (12/11) "chapter 3 level 4"
mm_lev   .text " level ", 0


; ------------------------------------------------------------------ schermate varie
; ------------------------------------------------------------------ menu salvataggi
        .virtual $9480
slot_valid .fill 5
slot_idx   .fill 6
nvalid     .byte ?
nlen2      .byte ?
slot_name  .fill 80
namebuf    .fill 16
seedbuf    .fill 6
slen       .byte ?
nfield     .byte ?
sfresh     .byte ?
fcur       .byte ?
        .endv

keymap  .byte 0,0,0,0,0,0,0,0
        .byte $33,23,1,$34,26,19,5,0
        .byte $35,18,4,$36,3,6,20,24
        .byte $37,25,7,$38,2,8,21,22
        .byte $39,9,10,$30,13,11,15,14
        .byte 0,16,12,$2d,$2e,0,0,0
        .byte 0,0,0,0,0,0,0,0
        .byte $31,0,0,$32,$20,0,17,0

; A = slot dell'eroe (0..): stampa i NAME_LEN caratteri del suo nome (slot_name)
ui_name:
        asl
        asl
        asl
        asl
        tax
        ldy #0
_l      sty tmp4
        lda slot_name,x
        stx tmp5
        jsr ui_putc
        ldx tmp5
        inx
        ldy tmp4
        iny
        cpy #NAME_LEN
        bne _l
        rts

; nome del PG senza gli spazi in fondo (08/11: nei titoli dei riquadri la cornice continua subito dopo)
ui_cname:
        ldx #NAME_LEN
_t      dex
        bmi _r                  ; nome vuoto
        lda c_name,x
        cmp #$20
        beq _t
        inx
        stx tmp5                ; caratteri da stampare (gli spazi in mezzo restano)
        ldx #0
_l      stx tmp4
        lda c_name,x
        jsr ui_putc
        ldx tmp4
        inx
        cpx tmp5
        bne _l
_r      rts

seed_roll:                      ; nuovo seed casuale: 6 caratteri, valori 1..35 (0 escluso)
        ldx #5
_s      lda #35
        jsr rndrange
        clc
        adc #1
        sta seedbuf,x
        dex
        bpl _s
        lda #6
        sta slen
        lda #1
        sta sfresh
        rts


; fire o RUN/STOP (morte, baule chiuso a chiave)
ui_wait_fire:
_w      jsr ui_input
        jsr ui_fire
        bne _r
        lda keynew+7
        and #$80
        beq _w
_r      rts

tt_died #t5 "you have died"
; schermata della morte: titolo rosso con il teschio, oro perso, Fire o RUN/STOP per continuare
ui_died:
        jsr ui_begin
        lda #3                  ; (09/11, concept del committente) titolo rosso con teschio, riquadro, tasto in riga 24
        sta ti_row
        lda #10
        sta ti_col
        lda #<tt_died
        ldx #>tt_died
        ldy #CH_SKULL
        jsr ui_title
        #ubox 2,6,36,9
        #at 4,8                 ; regola della moneta (08/11): il glifo al posto della parola gold
        #msg "you lose half of the "
        jsr ui_coin
        #msg " you carry."
        #at 4,10
        #msg "the "
        jsr ui_coin
        #msg " in your inn chest is safe."
        #at 4,13
        lda #1
        sta ui_col
        #msg "you wake up in town."
        #at 1,24
        #msg "fire:continue"
.if TESTUI == 32
        jmp *                   ; screenshot
.endif
        jmp ui_wait_fire


; (19/11) la leva della sala del trono (ui_lever): src/game/final.asm (codice del piano 20)

; ------------------------------------------------------------------ conferma scale
ui_n2:                          ; A -> 1..2 cifre senza riempimento
        ldx #$30
_t      cmp #10
        bcc _u
        sbc #10
        inx
        bne _t
_u      pha
        cpx #$30
        beq _nl
        txa
        jsr ui_putc
_nl     pla
        clc
        adc #$30
        jmp ui_putc

; ------------------------------------------------------------------ schermata disco
; io_dir: 0 salva / 1 carica ; io_what: 0 eroe / 2 generico ("loading") / altro piano (io_lvl)
io_screen:
        jsr ui_begin0
        ldx #12                 ; titolo centrato (09/11): "saving/loading barbarian" e "loading level 3" da x=12
        lda io_what
        cmp #2
        bne _tc
        ldx #16                 ; "loading" (7 colonne)
_tc     ldy #9
        jsr ui_at
        lda io_dir
        bne _ld
        #msg "saving "
        jmp _w
_ld     #msg "loading "
_w      lda io_what
        bne _lv
        #msg "barbarian"
        jmp ui_pwait
_lv     cmp #2
        beq ui_pwait            ; "loading" e basta (modulo MENU)
        #msg "level "
        lda io_lvl              ; (12/11, committente) il piano del capitolo: "loading level 3"
        jsr lv_grp
        inx
        txa
        jsr ui_n2               ; (18/11) e prosegue in ui_pwait (prima un jmp alla riga dopo)

; "please wait" centrato in riga 15 (09/11): sotto il titolo di io_screen e nelle attese ("deleting ...")
ui_pwait:
        #at 14,15
        #msg "please wait"
        rts

; attesa "reading barbarians" (lettura dell'elenco degli eroi)
io_screen_scan:
        jsr ui_begin
        #at 11,9
        #msg "reading barbarians"
        jmp ui_pwait


ui_seed:                        ; stampa le 6 cifre del seed (0-9, A-Z)
        lda #<ui_putc
        ldx #>ui_putc
; (11/11, O10) le 6 cifre del seed con la routine di uscita A/X (ui_putc a schermo, nb_chr negli sprite della minimappa)
seed_out:
        sta _p+1
        stx _p+2
        ldx #0
_l      stx tmp4
        lda c_seedt,x
        cmp #10
        bcs _a
        adc #$30
        bne _p
_a      sbc #9
_p      jsr ui_putc             ; (destinazione scritta da seed_out)
        ldx tmp4
        inx
        cpx #6
        bne _l
        rts


; ------------------------------------------------------------------ menu di gioco (RUN/STOP)
gm_lo   .byte <gm0, <gm1, <gm2
.if CHEATS
        .byte <gm3
.endif
gm_hi   .byte >gm0, >gm1, >gm2
.if CHEATS
        .byte >gm3
.endif
; (15/11) build con CHEATS = 1: quarta voce "cheats" (src/game/cheats.asm). Le voci si contano con .if e non con un
; simbolo: con CHEATS = 0 il listato della release resta identico a quello di prima dei trucchi
gm0     #t5 "resume"
gm1     #t5 "save game"
gm2     #t5 "quit game"
.if CHEATS
gm3     #t5 "cheats"
.endif


; menu di gioco: le voci (gm_lo/gm_hi) con il '>' sulla voce del cursore
gm_draw:
        ldx #0
_l      stx tmp3
        txa
        asl
        clc
        adc #8
        tay
        ldx #13                 ; (09/11) testo a x=15 come il titolo "game menu" (9 car., centrato): voci centrate
        jsr ui_at
        ldx tmp3
        jsr ui_mark
        lda #$20
        jsr ui_putc
        ldx tmp3
        lda gm_lo,x
        pha
        lda gm_hi,x
        tax
        pla
        jsr ui_puts5            ; (21/11 sera) voci a 5 bit
        ldx tmp3
        inx
.if CHEATS
        cpx #4
.else
        cpx #3
.endif
        bne _l
        rts

tt_gm   #t5 "game menu"
; (23/11, committente) riga 6 del menu di gioco: nel villaggio il suo nome (vil_nm), nel sotterraneo "chapter 3 level 4"
; (centrati): capitolo e piano non sono piu' nell'HUD
gm_place:
        lda cur_level
        bne _d
        ldx c_chap
        dex
        lda vil_lo,x
        sta ptr0
        lda vil_hi,x
        sta ptr0+1
        ldy #0                  ; lunghezza -> colonna (40 - n) / 2
-       lda (ptr0),y
        beq +
        iny
        bne -
+       sty tmp3
        lda #40
        sec
        sbc tmp3
        lsr
        tax
        ldy #6
        jsr ui_at
        lda ptr0
        ldx ptr0+1
        jmp ui_puts
_d      jsr lv_grp              ; A = capitolo, X = indice del piano nel capitolo
        inx
        stx tmp4
        pha
        #at 11,6                ; "chapter N level M" = 17 caratteri
        #msg "chapter "
        pla
        clc
        adc #$30
        jsr ui_putc
        #msg " level "
        lda tmp4
        clc
        adc #$30
        jmp ui_putc
; menu di gioco (RUN/STOP): resume, save game, quit game (e cheats con CHEATS = 1)
ui_gamemenu:
.if CHEATS
        lda #4
.else
        lda #3
.endif
        sta ui_n
        jsr nav_init
        jsr ui_begin
        lda #4
        sta ti_row
        lda #<tt_gm
        ldx #>tt_gm
        ldy #0
        jsr ui_title
        jsr gm_place            ; (23/11) dove si e': riga 6 (il capitolo e il piano non sono piu' nell'HUD)
        #at VER_X+1,18          ; (23/11, committente) seed della partita sopra la versione, centrato, staccato dalle voci,
        #msg "seed "            ; una riga vuota fra seed e versione
        jsr ui_seed
        #at VER_X,20            ; centrata (09/11)
        #msg "version " .. VERSION
        jsr nav_help
.if TESTUI == 33
        jmp _qask               ; screenshot della domanda "quit game?"
.endif
        jmp _dr
_back   jmp ui_exit
_dr     jsr gm_draw
.if NOKEYS
_hg     jmp _hg
.endif
_in     jsr ui_nav
        cmp #NAV_MOVE
        beq _dr
        cmp #NAV_BACK
        beq _back
        cmp #NAV_FIRE
        bne _in
        lda ui_cur
        beq _back
.if CHEATS
        cmp #3
        bne +
        jmp cheat_menu          ; 3 cheats (solo con CHEATS = 1)
+
.endif
        cmp #1
        bne _qask               ; 0 resume, 1 save game, 2 quit to main menu
_save   jsr gm_save             ; (08/11: niente schermata "game saved": basta la schermata di io_screen; si torna al gioco)
        jmp ui_exit
_qask   ; esci al menu principale (11/11 sera: senza salvare, decisione del committente)
        jsr ui_begin
        #at 15,9
        #msg "quit game?"
        #at 5,11
        #msg "unsaved progress will be lost"
        jsr ui_yesno            ; (09/11) "y:yes  n:no" in riga 24 come tutte le domande
        bcs _quit
        jmp ui_gamemenu
_quit   jsr music_fadeout       ; (15/11, TODO E3) la musica del gioco si dissolve: game_start azzera le variabili del player
        ldx #$ff                ; uscita senza salvare: vale l'ultimo "save game"
        txs
        jmp game_start


; salvataggio completo (menu RUN/STOP "save game"): piano attuale (o lasciato in memoria) nel suo slot, poi eroe + piani
; del capitolo sul disco con una sola riscrittura (sv_all, rel.asm)
gm_save:
        lda cur_level
        beq _tw
        jsr save_level
_tw                             ; (19/11) nel villaggio il piano lasciato per portale e' gia' nel suo slot (change_level)
_sc     jsr tod_tick            ; minuti giocati aggiornati
        jmp sv_all

; ------------------------------------------------------------------ baule
; baule del dungeon (08/11, concept con il committente): la schermata dei negozi. Titolo "o golden chest o",
; contents (lista da 8: prima voce l'oro preso aprendolo, non selezionabile; riaprendolo non c'e' piu'), equipped,
; pack, purse, selected item; riga 23 i messaggi, 24 i tasti. Fire prende l'oggetto (pozione: primo posto libero
; della cintura); il baule vuoto sparisce. Niente "take all".
ui_chest:
        jsr ui_begin
        ldx ch_cur              ; titolo: tipo del baule fra due monete
        lda ch_t,x
        and #$40
        beq +
        ldx #3
        bne ++
+       lda ch_t,x
        and #3
        tax
        dex
        bpl +
        ldx #0
+       lda ch_nm_lo,x
        pha
        lda ch_nm_hi,x
        tax
        pla
        ldy #CH_COIN
        jsr ui_title
        lda ch_msg
        cmp #2                  ; (11/11) gettone respec trovato (Abisso): riga 23
        bne +
        #at 1,23
        #msg "respec token found!"
+       lda ch_msg
        cmp #1
        bne _show
        #at 1,3
        #msg "it is locked. you need a key."
        #at 1,24
        #msg "fire or run/stop: close"
        jsr ui_wait_fire
        jmp ui_exit
_show   jsr ls2_frame           ; (21/11, liste a scorrimento) contenuto del baule e quello che si ha addosso
        jsr ui_labels
        .byte 2,1
        #t5 " contents "
        .byte 2,9
        #t5 " yours "
        .byte $ff
        lda ch_gold             ; oro trovato aprendolo: nel titolo del contenuto
        ora ch_gold+1
        beq +
        ldx #21
        ldy #1
        jsr ui_at
        jsr ui_gold
        lda ch_gold
        ldx ch_gold+1
        jsr ui_n5l
+       lda #0
        sta iv_mode
        sta sl_rv+1
        jsr iv_std
        jsr sort_pack
        lda #<iv_sg             ; lista 1 = le voci dell'inventario (segmenti 1-3), lista 0 = il contenuto (segmento 0)
        ldx #>iv_sg
        ldy #1
        jsr sl_segs
        lda #1
        sta sl_s0+1
        sta sl_sn
        lda #3
        sta sl_sn+1
        lda #0
        sta sl_s0
        jsr ch_fill
        jsr ls2_init
.if NOKEYS
        jsr ls2_draw
_hg     jmp _hg                 ; screenshot: la schermata resta com'e'
.endif
_rd     jsr ls2_draw
        jsr ch_keys
_in     jsr sl_nav
        cmp #NAV_MOVE
        bne +
        jsr iv_sel
        jsr ch_keys
        jmp _in
+       cmp #NAV_BACK
        beq _x
        cmp #NAV_FIRE
        bne _in
        lda sl_l                ; si prende solo dal contenuto
        bne _in
        jsr sl_sel
        lda ui_sel
        beq _in
        lda ch_cur              ; voce n del contenuto -> posto del baule (n-esimo oggetto dei 4 posti)
        asl
        asl
        tay
        ldx sl_cur
        lda #$ff
        sta ui_cur
-       inc ui_cur
        lda ch_i,y
        iny
        cmp #0
        beq -
        dex
        bpl -
        jsr msg23
        jsr chest_take1
        bcc _ok
        jsr give_msg            ; "the belt is full." / "pack is full." / "max 10 scrolls.": resta nel baule
        jmp _rd
_ok     jsr chest_empty
        bcs _e
        jsr ch_fill
        ldx #1
        jsr sl_reinit
        dex
        jsr sl_reinit
        jmp _rd
_x      jsr chest_empty         ; un baule vuoto sparisce anche uscendo
_e      jmp ui_exit

; riga 24: i tasti (nel contenuto si prende, nell'altra lista si guarda)
ch_keys:
        jsr row24
        lda sl_l
        bne +
        #msg "fire:take  "
+       #msg "run/stop:back"
        rts

; tipo del baule: ch_t & 3 = 0/1 normale, 2 con chiave, 3 d'oro; $40 epico
ch_nm_lo .byte <cn_0, <cn_1, <cn_2, <cn_3
ch_nm_hi .byte >cn_0, >cn_1, >cn_2, >cn_3
cn_0    #t5 "chest"
cn_1    #t5 "key chest"
cn_2    #t5 "golden chest"
cn_3    #t5 "epic chest"

; (21/11) oggetti del baule ch_cur -> l8_id / l8_b e segmento 0 (merce: SK_WARE) con quanti sono
ch_fill:
        lda ch_cur
        asl
        asl
        tax
        lda #4
        sta tmp6
        ldy #0
_c      lda ch_i,x
        beq +
        sta l8_id,y
        lda ch_b,x
        sta l8_b,y
        lda ch_s,x
        sta l8_s,y
        iny
+       inx
        dec tmp6
        bne _c
        sty sg_c
        lda #SK_WARE
        sta sg_k
        lda #0
        sta sg_a
        rts

; Y = posto nel contenuto del baule ch_cur (4 posti per baule) della voce ui_cur
chest_idx:
        lda ch_cur
        asl
        asl
        clc
        adc ui_cur
        tay
        rts

; prende la voce ui_cur. C=1 se zaino pieno
chest_take1:
        jsr chest_idx
        lda ch_i,y
        beq _ok
        lda ch_b,y
        sta ap_b
        lda ch_s,y
        sta ap_s
        lda ch_i,y
        jsr give_item
        bcs _full
        jsr chest_idx           ; gli oggetti successivi risalgono nello slot liberato
        lda ui_cur
        sta tmp3
_sh     lda tmp3
        cmp #3
        beq _last
        lda ch_i+1,y
        sta ch_i,y
        lda ch_b+1,y
        sta ch_b,y
        lda ch_s+1,y
        sta ch_s,y
        iny
        inc tmp3
        jmp _sh
_last   lda #0
        sta ch_i,y
        sta ch_b,y
        sta ch_s,y
        jsr chest_idx           ; cursore: resta sullo stesso slot (ora l'oggetto dopo);
        lda ch_i,y              ; se e' vuoto torna sull'ultimo oggetto rimasto
        bne _rf
        lda ui_cur
        beq _rf
        dec ui_cur
        jmp _last2
_rf     jsr sort_pack
_ok     clc
        rts
_last2  jsr chest_idx
        lda ch_i,y
        bne _rf
        lda ui_cur
        beq _rf
        dec ui_cur
        jmp _last2
_full   sec
        rts

; C=1 se il baule e' vuoto (lo rimuove)
chest_empty:
        lda ch_cur
        asl
        asl
        tay
        lda ch_i,y
        ora ch_i+1,y
        ora ch_i+2,y
        ora ch_i+3,y
        beq _e
        clc
        rts
_e      ldx ch_cur
        jsr ch_floor
        sec
        rts

; (15/11, TODO D12) baule X tolto: ch_t = 0 e la sua casella torna pavimento (X non preservato; anche rel.asm)
ch_floor:
        lda #0
        sta ch_t,x
        lda cx_x,x
        sta tx
        lda cx_y,x
        sta ty
        lda #T_FLOOR
        jmp set_tile

; messaggio di give_item fallito (gv_why), alla posizione corrente
give_msg:
        lda gv_why
        beq _p
        cmp #1
        beq _b
        #msg "max 10 scrolls."
        rts
_b      #msg "the belt is full."
        rts
_p      #msg "pack is full."
        rts



        .enc "none"
