; ===================================================================
;  ui.asm - schermate di testo (font ROM), inventario, negozi, minimappa
; ===================================================================
        .enc "screen"

        .virtual $9460
mm_tx    .byte ?
mm_ty    .byte ?
mm_bits  .byte ?
mm_st    .byte ?
mm_wat   .byte ?              ; villaggio: bit 0 = acqua nel quadrante, bit 1 = strada (cella blu se solo acqua)
mmx      .byte ?
mmy      .byte ?
st_i     .byte ?                ; indice salvato (baule di casa, cintura nell'inventario)
it_i     .byte ?                ; oggetto in transito: id, bonus, durabilita', massimo (eq_get, pk_put...)
it_b     .byte ?
it_d     .byte ?
it_m     .byte ?
ui_dur   .byte ?                ; ibox_show: durabilita' dell'oggetto mostrato (0 = non mostrata)
ui_durm  .byte ?
st_top   .byte ?                ; baule di casa: primo oggetto della pagina mostrata (locanda)
st_col   .byte ?                ; baule di casa: colonna selezionata (0 zaino, 1 baule) (locanda)
        .endv
        .cerror st_col >= $9480, "variabili UI oltre $947F"

        .virtual $93e0          ; motore dei menu (ui_nav, 07/11 sera: docs/refactor-tasti.md)
tb_n     .byte ?                ; contatore di ui_boxes (11/11: le linguette non ci sono piu')
tb_i     .byte ?
ui_bc    .byte ?                ; colore delle cornici di ui_box (ui_begin: UC_BOX; la casa colora equipped in scelta)
s4_n     .byte ?                ; sort4: numero di posti, categoria della passata, appoggio
s4_c     .byte ?
s4_t     .byte ?
hg_x     .byte ?                ; h_get / h_put (casa): posto e indice della tabella
hg_k     .byte ?
eq_y     .byte ?                ; eq_draw: prima riga, voce del cursore del primo posto, posto fisso ($FF nessuno)
eq_u0    .byte ?
eq_fix   .byte ?
eq_k     .byte ?
nav_end
        .endv
        .cerror nav_end > $9400, "variabili di ui_nav oltre $93FF"

        .virtual $942b          ; (08/11) liste comuni dei menu: lista da 8, righe dei riquadri
l8_id   .fill 8                 ; list8: oggetti dei posti (0 = '-', $FF = oro del baule: ch_gold)
l8_b    .fill 8                 ; ... e loro bonus
l8_y    .byte ?                 ; prima riga della lista da 8
de_y    .byte ?                 ; prima riga dello zaino (draw_entries)
pu_y    .byte ?                 ; prima riga del purse (purse_draw)
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
ib_y    .byte ?                 ; riquadro oggetto: prima riga di testo e riga finale+1
ib_ye   .byte ?
ui_fc   .byte ?                 ; <>0: colore forzato per valori e oggetti (schermate eroe)
        .endv

        .virtual $9400
shp_stock .fill 16              ; oggetti in vendita (estratti a caso a ogni ingresso)
sh_mask   .byte ?               ; negozio: categorie comprate (bit 1<<CAT_*), 0 = fuori dal negozio (pk_name)
sh_lc     .byte ?               ; voce con il '>' nella merce e nel purse (ui_lc o il posto scelto)
        .endv
        .cerror sh_lc >= $9420, "variabili del negozio oltre $941F"

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
        jsr irq_off
        lda #0
        sta SPR_EN
        sta BORDER
        sta BGCOL
        sta inv
        sta sh_mask
        sta tp_on               ; in UI lo schermo A e' testo: set_tile non deve toccarlo
        lda #UC_BOX
        sta ui_bc
        lda #2                  ; righe dei riquadri comuni (inventario, negozi); il baule le cambia
        sta l8_y
        lda #8
        sta eq_y
        lda #12
        sta de_y
        lda #18
        sta pu_y
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
UC_CURSOR = 13
UC_MAGIC = 14
UC_EMPTY = 11
UC_BOX   = 11                   ; cornici grigio scuro (08/11, prima 15)
UC_BTTL  = 15                   ; titoli sulle cornici: grigio chiaro (ui_at li riconosce: iniziano sopra BOX_H)
BOX_H    = 28
BOX_V    = 30
BOX_TL   = 31
BOX_TR   = 59
BOX_BL   = 60
BOX_BR   = 0
CH_KEY   = 91
CH_COIN  = 92                   ; una moneta (08/11: prima un mucchio di 2 caratteri, 92-93)
CH_POT   = 94
CH_SCR   = 95
CH_ANVIL = 34
CH_SHLD  = 35
CH_FLASK = 36
CH_SWORD = 97                   ; icone dell'equipaggiamento (08/11, font UI: blocco "inverso" non usato dalla UI)
CH_ARMOR = 98                   ; (lo scudo e' CH_SHLD)
CH_RING  = 99
CH_SKULL = 100                  ; teschio (09/11: titolo della schermata di morte)
CH_INN   = 101                  ; boccale (09/11: titolo della locanda)
CH_ARROW = 93                   ; freccia a destra (15/11: schermata C, "valore -> nuovo" dei punti in attesa)

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

ui_putc:
        ora inv
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

; stringa in linea dopo la JSR
ui_pi:
        pla
        sta ptr2
        pla
        sta ptr2+1
_l      inc ptr2
        bne _a
        inc ptr2+1
_a      ldy #0
        lda (ptr2),y
        beq _d
        jsr ui_putc
        jmp _l
_d      lda ptr2+1
        pha
        lda ptr2
        pha
        rts

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
        lda tmp0
        clc
        adc c_gold
        sta tmp0
        lda tmp1
        adc c_gold+1
        sta tmp1
        bcc +
        inc tmp2
+       rts

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
        lda ui_col
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

; A = id oggetto, ui_ib = bonus: [+N ]nome riempito a 17 caratteri
ui_item:
        tax
        lda ui_col
        pha
        lda #UC_ITEM
        cpx #0
        bne +
        lda #UC_EMPTY
+       ldy ui_ib
        beq +
        cpx #I_SCROLL           ; pila di pergamene: il bonus e' la quantita', non magia
        beq +
        lda #UC_MAGIC
+       ldy ui_fc
        beq _nfi
        lda ui_fc
_nfi    sta ui_col
        lda cidx
        pha
        lda ui_ib
        beq _nb
        ldy itcat,x             ; anello: il bonus e' la caratteristica (nome + " str"/" dex"/" con")
        cpy #CAT_RING
        beq _nb
        cpx #I_SCROLL
        bne _bo
        cmp #10                 ; "3 portal scroll", "10 portal scroll" (08/11: senza la x, fino a 10)
        bcc +
        sbc #10
        pha
        lda #$31
        jsr ui_putc
        pla
+       ora #$30
        jsr ui_putc
        jmp _bs
_bo     lda #$2b
        jsr ui_putc
        lda ui_ib
        clc
        adc #$30
        jsr ui_putc
_bs     lda #$20
        jsr ui_putc
_nb     txa
        pha
        lda itnm_lo,x
        pha
        lda itnm_hi,x
        tax
        pla
        jsr ui_puts
        pla
        tax
        lda itcat,x
        cmp #CAT_RING
        bne +
        jsr ring_stat
+       lda #0
        sta ui_ib
        pla
        clc
        adc #16                 ; 16 colonne (08/11: la colonna prima del nome e' l'icona della categoria, ui_cic)
        sta tmp6
_p      lda cidx
        cmp tmp6
        bcs _d
        lda #$20
        jsr ui_putc
        jmp _p
_d      pla
        sta ui_col
        rts

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
        pla
        sta ptr2
        pla
        sta ptr2+1
_n      jsr _g
        cmp #$ff
        beq _e
        tax
        jsr _g
        tay
        jsr ui_at
_c      jsr _g
        beq _n
        jsr ui_putc
        jmp _c
_e      lda ptr2+1
        pha
        lda ptr2
        pha
        rts
_g      inc ptr2
        bne +
        inc ptr2+1
+       ldy #0
        lda (ptr2),y
        rts

; riga 24: i tasti, uguali in tutte le schermate
nav_help:
        #at 1,24
        #msg "fire:select  run/stop:back"
        rts

; ------------------------------------------------------------------ voci (zaino+equip)
draw_entries:
        ldx #0
_l      stx tmp3
        txa
        and #3
        clc
        adc de_y
        tay
        lda ue_x,x
        tax
        jsr ui_at
        ldx tmp3
        cpx ui_lc
        bne _nm
        lda #$3e
        bne _pm
_nm     lda #$20
_pm     jsr ui_putc
        ldx tmp3
        lda c_pack,x            ; icona della categoria al posto dello spazio (08/11)
        jsr ui_cic
        jsr pk_name
        ldx tmp3
        inx
        cpx #PACK_N             ; solo lo zaino (l'equipaggiamento con eq_draw)
        bne _l
        rts

; nome dell'oggetto X delle tabelle dello zaino (PACK_N.. = equipaggiamento) alla posizione corrente: magia, rotto in rosso
pk_name:
        lda c_packb,x
        sta ui_ib
        lda #0                  ; oggetto rotto (durabilita' 0 su un massimo > 0: le armi, 07/11): in rosso
        ldy c_packm,x
        beq +
        ldy c_packd,x
        bne +
        lda #2
+       sta ui_fc
        lda sh_mask             ; negozio (08/11): gli oggetti dello zaino che non compra sono grigi
        beq _n
        cpx #PACK_N
        bcs _n
        ldy c_pack,x
        lda itcat,y
        tay
        lda cat_bit,y
        and sh_mask
        bne _n
        lda #12
        sta ui_fc
_n      lda c_pack,x
        jsr ui_item
        lda #0
        sta ui_fc
        rts

; equipaggiamento su 2 colonne con le icone (08/11, casa e inventario): arma (1,eq_y), armatura (1,eq_y+1),
; scudo (20,eq_y), anello (20,eq_y+1). Cursore '>' se eq_u0 + posto = ui_lc, oppure fisso sul posto eq_fix
eq_draw:
        ldx #0
_l      stx eq_k
        lda eq_x,x
        tax
        lda eq_k
        and #1
        clc
        adc eq_y
        tay
        jsr ui_at
        lda eq_k
        cmp eq_fix
        beq _gt
        clc
        adc eq_u0
        cmp ui_lc
        bne _sp
_gt     lda #$3e
        .byte $2c
_sp     lda #$20
        jsr ui_putc
        ldy eq_k
        lda eq_icc,y
        tax
        lda eq_ic,y
        jsr ui_icon
        lda eq_k
        clc
        adc #PACK_N
        tax
        jsr pk_name
        ldx eq_k
        inx
        cpx #4
        bne _l
        rts
; equipaggiamento in righe 8-9 con il cursore della lista (inventario, negozi)
eq_std: lda #PACK_N              ; (riga: eq_y, 8 di base da ui_begin)
        sta eq_u0
        lda #$ff
        sta eq_fix
        jmp eq_draw
eq_x    .byte 1, 1, 20, 20
eq_ic   .byte CH_SWORD, CH_ARMOR, CH_SHLD, CH_RING
eq_icc  .byte 1, 15, 9, 7       ; bianco, grigio chiaro, marrone, giallo

; ------------------------------------------------------------------ inventario
; inventario (08/11: niente linguette): fire = usa (indossa, togli, bevi, pergamena), DEL = elimina (con conferma),
; RUN/STOP o I = chiude. Lista: zaino (8, due colonne da 4) poi equipaggiamento (4)
ui_inventory:
        jsr sort_pack           ; (08/11) zaino sempre ordinato anche se il salvataggio e' di prima dell'ordinamento
        lda #PACK_N+4
        sta ui_n
        jsr nav_init
        jsr ui_begin
        lda #19
        jsr ib_set
        lda #<tt_bp
        ldx #>tt_bp
        ldy #0
        jsr ui_title
        jsr inv_frames
        jsr ui_labels
        .byte 1,24
        .text "fire:use  del:drop  run/stop:back"
        .byte 0,$ff
_dyn    jsr inv_dynamic
        jsr ibox_draw
_in     jsr ui_nav
        cmp #NAV_MOVE
        beq _dyn
        cmp #NAV_BACK
        beq _exit
        cmp #NAV_FIRE
        beq _f
        lda keynew              ; DEL (INST/DEL, riga 0 bit 0): elimina
        and #$01
        bne _drop
        lda keynew+4            ; I: chiude anche (lo stesso tasto che l'ha aperto)
        and #$02
        beq _in
_exit   jmp ui_exit
_f      jsr inv_act
        jmp _dyn
_drop   jsr inv_delete
        jmp _dyn

tt_bp   .text "backpack", 0

; riquadro: bx,by,bw,bh (bordo grigio, interno non toccato)
ui_box:
        ldx bx
        ldy by
        jsr ui_at
        lda ui_bc
        sta ui_col
        lda #BOX_TL
        jsr ui_putc
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
        jsr ui_at
        lda ui_bc
        sta ui_col
        lda #BOX_V
        jsr ui_putc
        lda bx
        clc
        adc bw
        tax
        dex
        ldy br
        jsr ui_at
        lda ui_bc
        sta ui_col
        lda #BOX_V
        jsr ui_putc
        jmp _side
_bot    ldx bx
        ldy bend
        jsr ui_at
        lda ui_bc
        sta ui_col
        lda #BOX_BL
        jsr ui_putc
        ldx bw
        dex
        dex
_b2     lda #BOX_H
        jsr ui_putc
        dex
        bne _b2
        lda #BOX_BR
        jmp ui_putc


; cornici e etichette fisse dell'inventario
; inventario (08/11, concept con il committente): statistiche (titolo = nome), equipped con le icone, zaino,
; cintura, oggetto selezionato; riga 23 per la domanda, 24 i tasti
inv_frames:
        jsr sec_frames
        jsr ui_labels
        .byte 2,17
        .text " belt "
        .byte 0,2,1,$20,0,$ff
        jsr ui_cname
        lda #$20
        jmp ui_putc

; i 5 riquadri comuni a inventario e negozi: in alto (statistiche / merce), equipped, pack, in basso a sinistra
; (belt / purse), selected item (riquadro standard dell'oggetto)
sec_frames:
        lda #<sf_box
        ldx #>sf_box
        ldy #20
        jsr ui_boxes
        jsr ui_labels
        .byte 2,7
        .text " equipped "
        .byte 0,2,11
        .text " pack "
        .byte 0,22,17
        .text " selected item "
        .byte 0,$ff
        rts
sf_box  .byte 0,1,40,6, 0,7,40,4, 0,11,40,6, 0,17,20,5, 20,17,20,5

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

; lista da 8 (08/11, componente comune: merce dei negozi, contenuto dei bauli): 2 colonne da 4 dalla riga l8_y,
; voci 12..19 (cursore '>' su sh_lc), l8_id/l8_b = oggetti; 0 = '-', $FF = oro del baule ("64o")
list8:
        ldx #0
_w      stx tmp3
        txa
        and #3
        clc
        adc l8_y
        tay
        ldx #1
        lda tmp3
        cmp #4
        bcc +
        ldx #20
+       jsr ui_at
        lda tmp3
        clc
        adc #12
        jsr sh_cur1
        ldx tmp3
        lda l8_id,x             ; icona della categoria (spazio per '-' e per l'oro del baule)
        jsr ui_cic
        ldx tmp3
        lda l8_id,x
        cmp #$ff
        bne _it
        lda ch_gold
        ldx ch_gold+1
        jsr ui_n5l
        jsr ui_coin
        jmp _nx
_it     ldy l8_b,x
        sty ui_ib
        jsr ui_item
_nx     ldx tmp3
        inx
        cpx #8
        bcc _w
        rts

; purse (08/11, componente comune: negozi, bauli) dalla riga pu_y: oro (moneta a x 2, sopra la prima pozione) e
; chiavi (x 11); riga pu_y+1 cintura (posti a x 2, 5, 8, 11; '>' su sh_lc = 20..23) e pergamene (x 14, voce 24);
; riga pu_y+2 libera: seconda fila della cintura a 8 posti (4 slot da 2, quest; TODO)
purse_draw:
        ldx #2
        ldy pu_y
        jsr ui_at
        jsr shop_gold
        ldx #0
_bl     stx st_i
        txa
        asl
        adc st_i
        adc #1
        tax
        ldy pu_y
        iny
        jsr ui_at
        lda st_i
        clc
        adc #20
        jsr sh_cur1
        ldx st_i
        jsr belt_slot
        ldx st_i
        inx
        cpx #4
        bne _bl
        ldx #13
        ldy pu_y
        iny
        jsr ui_at
        lda #24
        jsr sh_cur1
        jsr scr_find
        bcs _ns
        lda c_packb,y
        pha
        lda #CH_SCR
        ldx #15
        jsr ui_icon
        lda #$20
        jsr ui_putc
        pla
        jsr ui_b3l
        lda #$20
        jsr ui_putc
        jmp _k
_ns     #msg "-   "
_k      ldx #11                 ; chiavi accanto all'oro (x 11, sopra il 4o posto della cintura): icona + "n/10"
        ldy pu_y                ; (la riga pu_y+2 resta per la 2a fila della cintura a 8 posti, quest: TODO)
        jsr ui_at
        jsr keys_n
        lda #$20                ; (le cifre possono calare: pulisce la colonna dopo)
        jmp ui_putc

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


; statistiche dell'oggetto selezionato: riquadro in basso a destra (x=21..38, righe 21-22)
ibox_draw:
        ldx ui_cur
        jsr ibox_ld
ibox_show:                      ; ui_sel / tmp5 gia' impostati
        jsr ibox_top
        beq +
        jsr ib_at1              ; riga 2: valore (vendita)
        jmp it_val
+       rts

; oggetto X delle tabelle dello zaino (PACK_N.. = equipaggiamento) -> ui_sel, tmp5, ui_dur, ui_durm
ibox_ld:
        lda c_pack,x
        sta ui_sel
        lda c_packb,x
        sta tmp5
        lda c_packd,x
        sta ui_dur
        lda c_packm,x
        sta ui_durm
        rts

; pulisce le 2 righe del riquadro oggetto e scrive caratteristica principale + secondaria. Z=1 se nessun oggetto
ibox_top:
        ldy ib_y
_cl     tya
        pha
        ldx #21
        jsr ui_at
        lda #$20
        ldy #17
_c2     sta (cp),y
        dey
        bpl _c2
        pla
        tay
        iny
        cpy ib_ye
        bne _cl
        ldx ui_sel
        bne _ok
        rts
_ok     jsr ib_at0              ; riga 1: caratteristica principale + secondaria
        jsr it_prim
        lda #$20
        jsr ui_putc
        jsr it_sec
        lda ui_sel
        rts

; posizionamento nel riquadro oggetto
ib_at0: ldx #21
        ldy ib_y
        jmp ui_at
ib_at1: ldx #21
        ldy ib_y
        iny
        jmp ui_at

; A = riga di testo del riquadro oggetto
ib_set: sta ib_y
        clc
        adc #2
        sta ib_ye
        rts

; posto X (0..3) della cintura: icona della pozione (nel suo colore) o '-', poi 2 spazi
belt_slot:
        ldy c_beltt,x
        beq _nt
        ldx itfl,y              ; colore della pozione (rossa, gialla, viola)
        lda #CH_POT
        jsr ui_icon
        jmp _sp
_nt     lda #$2d
        jsr ui_putc
_sp     lda #$20
        jsr ui_putc
        lda #$20
        jmp ui_putc

inv_act:
        ldx ui_cur
        cpx #PACK_N
        bcc _pk
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
_sw     lda itcat,y             ; scambio zaino <-> equipaggiamento (posto = categoria - 1)
        sec
        sbc #1
        tay
        jsr eq_get              ; vecchio equipaggiamento -> it_*
        ldx ui_cur
        jsr pk_swap             ; it_* <-> posto dello zaino
        ldy tmp6
        jsr eq_put              ; nuovo equipaggiamento
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
; Y = posto dell'equipaggiamento (0..3, o PACK_N..PACK_N+3: PACK_N multiplo di 4) -> it_*
eq_get: tya
        and #3
        tay
        sty tmp6
        lda c_eq,y
        sta it_i
        lda c_eqb,y
        sta it_b
        lda c_eqd,y
        sta it_d
        lda c_eqm,y
        sta it_m
        rts
eq_put: lda it_i
        sta c_eq,y
        lda it_b
        sta c_eqb,y
        lda it_d
        sta c_eqd,y
        lda it_m
        sta c_eqm,y
        rts
eq_zero: tya
        and #3
        tay
        lda #0
        sta c_eq,y
        sta c_eqb,y
        sta c_eqd,y
        sta c_eqm,y
        rts
; X = posto dello zaino
pk_put: lda it_i
        sta c_pack,x
        lda it_b
        sta c_packb,x
        lda it_d
        sta c_packd,x
        lda it_m
        sta c_packm,x
        rts
pk_zero: lda #0
        sta c_pack,x
        sta c_packb,x
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
        ldy #24
        jsr clear_row
        #at 1,24
        #msg "y:yes  n:no"
.if TESTUI == 33
        jmp *                   ; screenshot della domanda "quit game?"
.endif
yn_wait jsr ui_input            ; (etichetta globale: la usa tests/test_saves.py)
        jsr ui_fire             ; fire = si' (07/11 sera, docs/refactor-tasti.md)
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
        .word c_pack, c_packb, c_packd, c_packm

; ordinamento stabile per categoria (armi, armature, scudi, anelli, pozioni, pergamene; i posti vuoti in fondo) di
; 4 tabelle parallele: id, bonus, durabilita', massimo (08/11: zaino e baule di casa sempre ordinati).
; A/X = descrittore: numero di posti (<= 32), poi i 4 indirizzi. Usa $FB-$FE, S4_ORD e S4_BUF (dopo LVLBLK).
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
        cmp #9
        bne _tb
        rts

; valore di vendita: "val 1200o d135/178" (08/11: numero e poi la moneta)
it_val  #msg "val "             ; valore di vendita: meta' del prezzo
it_half lda ui_sel
        asl
        tay
        lda itprice+1,y
        lsr
        sta tmp1
        lda itprice,y
        ror
        ldx tmp1
        jsr ui_n5l              ; (08/11) allineato a sinistra
        jsr ui_coin
it_dur  lda ui_durm             ; durabilita' " d120/200" (solo oggetti che si usurano), se sta nel riquadro da 18
        beq _x                  ; (cidx = caratteri gia' scritti dalla riga: " d135/178" sono 9)
        lda cidx
        cmp #10
        bcs _x
        #msg " d"
        lda ui_dur
        jsr ui_b3l
        lda #$2f
        jsr ui_putc
        lda ui_durm
        jmp ui_b3l
_x      rts

; caratteristica principale dell'oggetto ui_sel (bonus tmp5), al massimo 9 caratteri:
; "dmg 2d6+3", "ac +5", "+2 str", "heal 60", "portal"
it_prim:
        ldx ui_sel
        lda itcat,x
        cmp #CAT_WEAPON
        beq _w
        cmp #CAT_RING
        beq _rg
        cmp #CAT_POTION
        beq _po
        cmp #CAT_SCROLL
        beq _scr
        #msg "ac +"             ; armatura / scudo: CA (magia compresa)
        ldx ui_sel
        lda itval,x
        clc
        adc tmp5
        jmp ui_b3l
_rg     lda tmp5                ; anello: +N al modificatore della caratteristica (tmp5 prima di ui_b3l, che lo usa)
        sta ui_ib
        #msg "+"
        ldx ui_sel
        lda itval,x
        jsr ui_b3l
        jsr ring_stat
        lda #0
        sta ui_ib
        rts
_po     #msg "heal "            ; pozione: cura al livello attuale
        ldy ui_sel
        jsr pot_heal
        ldx mu1
        jmp ui_n5l
_scr    #msg "portal"
        rts
_w      lda tmp5                ; arma: dadi + magia (08/11: tmp5 salvato, ui_b3l lo usa: prima usciva un numero a caso)
        pha
        #msg "dmg "
        pla
        tay
        ldx ui_sel
        lda itdn,x
        pha
        lda itds,x
        tax
        pla
; dadi "NdS+K" tutti nel colore dei valori (08/11): A = N, X = S, Y = K (0 = senza "+K")
ui_dice:
        stx tmp6
        sty tmp7
        tay
        lda ui_col
        pha
        lda ui_fc               ; (15/11) colore forzato (schermata C: valore nuovo in verde) anche per 'd' e '+'
        bne +
        lda #UC_VALUE
+       sta ui_col
        tya
        jsr ui_b3l
        lda #4                  ; 'd'
        jsr ui_putc
        lda tmp6
        jsr ui_b3l
        lda tmp7
        beq +
        lda #$2b
        jsr ui_putc
        lda tmp7
        jsr ui_b3l
+       pla
        sta ui_col
        rts

; caratteristica secondaria (al massimo 9 caratteri): "2h pen 1", "dex max 2" o niente
it_sec:
        ldx ui_sel
        lda itcat,x
        cmp #CAT_ARMOR
        beq _ar
        cmp #CAT_WEAPON
        bne _r
        lda itfl,x
        and #1
        beq _pn
        #msg "2h "
_pn     ldx ui_sel
        lda itpen,x
        beq _r
        #msg "pen "
        ldx ui_sel
        lda itpen,x
        jmp ui_b3l
_ar     lda itfl,x              ; armatura: limite al modificatore di DES
        cmp #99
        bcs _r
        #msg "dex max "
        ldx ui_sel
        lda itfl,x
        jmp ui_b3l
_r      rts

; anello: " str" / " dex" / " con" secondo ui_ib (1..3)
ring_stat:
        lda ui_ib
        beq _r
        cmp #4
        bcs _r
        sec
        sbc #1
        sta tmp7
        asl
        adc tmp7                ; x 3
        tax
        adc #3
        sta tmp7                ; fine (ui_putc usa Y: il contatore e' X)
        lda #$20
        jsr ui_putc
_c      lda rs_txt,x
        jsr ui_putc
        inx
        cpx tmp7
        bne _c
_r      rts
rs_txt  .text "strdexcon"


; icona: A = codice, X = colore (ui_col preservato)
ui_icon:
        ldy ui_col
        sty tmp6
        stx ui_col
        jsr ui_putc
        lda tmp6
        sta ui_col
        rts

; A = id oggetto -> icona della categoria (08/11, TODO 1.3) nel suo colore; spazio se 0 o $FF (oro del baule).
; Pozioni nel loro colore (itfl). X conservato.
ui_cic:
        tay
        beq _sp
        iny
        beq _sp
        dey
        txa
        pha
        lda itcat,y
        cmp #CAT_POTION
        bne +
        ldx itfl,y
        bne _c
+       tay
        ldx cat_icc,y
_c      lda cat_ic,y
        cpy #CAT_POTION         ; (pozione: Y = id, l'icona e' fissa)
        bcc +
        lda #CH_POT
        cpy #CAT_SCROLL
        bne +
        lda #CH_SCR
+       jsr ui_icon
        pla
        tax
        rts
_sp     lda #$20
        jmp ui_putc
cat_ic  .byte $20, CH_SWORD, CH_ARMOR, CH_SHLD, CH_RING
cat_icc .byte 0, 1, 15, 9, 7, 0, 15

; tabella statistiche (righe 1-3), colonne a x = 1, 12, 24, 31
inv_dynamic:
        ldy #2                  ; righe 2-5 pulite (i valori cambiano lunghezza)
_c      tya
        pha
        ldx #1
        jsr ui_at
        ldx #38
-       lda #$20
        jsr ui_putc
        dex
        bne -
        pla
        tay
        iny
        cpy #6
        bne _c
        jsr ui_labels           ; 3 colonne: x 2, 15, 29
        .byte 2,2
        .text "lvl"
        .byte 0,15,2
        .text "xp"
        .byte 0,2,3
        .text "hp"
        .byte 0,15,3
        .text "att +"
        .byte 0,29,3
        .text "ac"
        .byte 0,2,4
        .text "str"
        .byte 0,15,4
        .text "dex"
        .byte 0,29,4
        .text "con"
        .byte 0,2,5
        .text "dmg"
        .byte 0,$ff
        #at 7,2
        lda c_lvl
        jsr ui_b3l
        #at 19,2                ; xp come nell'HUD (08/11): "9999/27k", da 10000 in migliaia (16 bit bassi)
        lda c_xp
        ldx c_xp+1
        jsr ui_n5k
        ldx c_lvl
        cpx #PL_MAXLVL
        bcs _xm                 ; livello massimo: niente soglia
        lda #$2f
        jsr ui_putc
        lda xp_n1-1,x
        pha
        lda xp_n0-1,x
        tay
        pla
        tax
        tya
        jsr ui_n5k
_xm
        #at 29,2
        jsr ui_gold
        #at 33,2                ; cifre nella colonna dei valori (ac, con)
        lda c_gold
        ldx c_gold+1
        jsr ui_n5l
        #at 7,3
        lda c_hp
        ldx c_hp+1
        jsr ui_n5l
        lda #$2f
        jsr ui_putc
        lda hpmax
        ldx hpmax+1
        jsr ui_n5l
        #at 20,3
        lda s_att
        jsr ui_b3l
        #at 33,3
        lda s_ac
        jsr ui_b3l
        #at 7,4
        lda s_str
        jsr ui_b3l
        #at 19,4
        lda s_dex
        jsr ui_b3l
        #at 33,4
        lda s_con
        jsr ui_b3l
        #at 7,5
        lda s_dn
        ldx s_ds
        ldy s_dk
        jsr ui_dice
        #at 15,5                ; chiavi
        jsr keys_n
        jsr eq_std              ; equipaggiamento: voci PACK_N.. della lista, righe 8-9
        jsr draw_entries
        #at 21,18               ; nome dell'oggetto selezionato, con l'icona della categoria
        ldx ui_cur
        lda c_pack,x
        jsr ui_cic
        jsr pk_name
        ; cintura (riquadro in basso a sinistra): 4 pozioni + pergamena, '-' = posto vuoto
        #at 2,18
        ldx #0
_bs     stx st_i
        jsr belt_slot
        ldx st_i
        inx
        cpx #4
        bne _bs
        jsr scr_find
        bcs _ns
        lda #CH_SCR
        ldx #15
        jmp ui_icon
_ns     lda #$2d
        jmp ui_putc

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

; '>' sulla voce A se e' quella del cursore (sh_lc), altrimenti spazio
sh_cur1:
        cmp sh_lc
        bne +
        lda #$3e
        .byte $2c
+       lda #$20
        jmp ui_putc

; titolo di ogni schermata (08/11, routine unica): riga ti_row, centrato, giallo; A/X = testo, Y = icona ai due lati
; (gialla; 0 = nessuna): "^ blacksmith ^", "o golden chest o", "backpack"
ui_title:
        sta ptr2
        stx ptr2+1
        sty tmp7
        ldy #0
-       lda (ptr2),y
        beq +
        iny
        bne -
+       tya                     ; lunghezza (+4 con le icone e gli spazi)
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
+       lda ptr2
        ldx ptr2+1
        jsr ui_puts
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
        lda ui_col
        pha
        lda #UC_VALUE
        sta ui_col
        lda #'k'
        jsr ui_putc
        pla
        sta ui_col
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

; riga dei messaggi pulita, cursore all'inizio: msg23 = riga 23 (negozi), shop_msg_clear = riga 22 (baule del piano)
msg23:  ldy #23
        .byte $2c
shop_msg_clear:
        ldy #22
        ldx #1
        jsr ui_at
        lda #$20
        ldy #37
_c      sta (cp),y
        dey
        bpl _c
        rts

; riquadro dell'oggetto selezionato del baule di un dungeon (voce ui_lc 12..19 della lista da 8; 11/11: la versione
; dei negozi, sh_item, e' nel modulo MENU): nome, caratteristiche, valore; riga 24 i tasti
ch_item:
        ldx #21                 ; nome nella riga prima di ib_y
        ldy ib_y
        dey
        jsr ui_at
        ldx ui_lc
        lda l8_id-12,x
        sta ui_sel
        lda l8_b-12,x
        sta ui_ib
        lda ui_sel
        jsr ui_cic
        lda ui_sel
        jsr ui_item
        ldx ui_lc               ; dopo ui_item (ui_puts usa tmp5)
        lda l8_b-12,x
        sta tmp5
        lda #0
        sta ui_dur
        sta ui_durm
        jsr ibox_top
        beq +
        jsr ib_at1
        jsr it_val
+       ldy #24
        jsr clear_row
        #at 1,24
        #msg "fire:take  run/stop:back"
        rts

; ------------------------------------------------------------------ minimappa
; (mm_tx,mm_ty) -> A: 0 nulla, 1 pavimento, 2 scale giu', 3 scale su
mm_tile:
        lda cur_level
        bne _dun
        jmp mm_town             ; citta': tutta visibile, solo strade e piazza
_dun    ldx mm_ty
        lda exprow_lo,x
        sta ptr2
        lda exprow_hi,x
        sta ptr2+1
        lda mm_tx
        lsr
        lsr
        lsr
        tay
        lda mm_tx
        and #7
        tax
        lda (ptr2),y
        and bitmask,x
        beq _no
        lda mm_tx
        sta tx
        lda mm_ty
        sta ty
        jsr get_tile
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
_su     lda #3
        rts
_no     lda #0
        rts

; citta': 1 = strada/piazza/porte, 2 = scale per il dungeon, 0 = resto (erba, case, alberi)
mm_town:
        lda mm_tx
        sta tx
        lda mm_ty
        sta ty
        jsr get_tile
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
        lda mm_wat
        ora #1
        sta mm_wat
        lda #1
        rts
_0      lda #0
        rts
_y      lda mm_wat
        ora #2
        sta mm_wat
        lda #1
        rts
_sd     lda #2
        rts

mm_acc:                         ; A = risultato, X = maschera
        cmp #1
        bne _s
        txa
        ora mm_bits
        sta mm_bits
        rts
_s      cmp #2
        bcc _r
        sta mm_st
_r      rts

mm_quad .macro dx, dy, mask
        lda mm_tx
        clc
        adc #\dx
        pha
        lda mm_ty
        clc
        adc #\dy
        sta mm_ty
        pla
        sta mm_tx
        jsr mm_tile
        ldx #\mask
        jsr mm_acc
        lda mm_tx
        sec
        sbc #\dx
        sta mm_tx
        lda mm_ty
        sec
        sbc #\dy
        sta mm_ty
        .endm

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
        lda #0
        sta mmy
_row    lda #0
        sta mmx
_col    lda mmx
        asl
        sta mm_tx
        lda mmy
        asl
        sta mm_ty
        lda #0
        sta mm_bits
        sta mm_st
        sta mm_wat
        #mm_quad 0,0,1
        #mm_quad 1,0,2
        #mm_quad 0,1,4
        #mm_quad 1,1,8
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
        cmp #1
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
        lda SPR_MSB
        and #$80
        sta SPR_MSB
        lda #(1 << MI_N) - 1    ; icone a doppia grandezza (16 px)
        sta SPR_XEXP
        sta SPR_YEXP
        lda #$80 | ((1 << MI_N) - 1)
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
        sta ptr0
        lda #0
        sta ptr0+1
        asl ptr0
        rol ptr0+1
        asl ptr0
        rol ptr0+1
        asl ptr0
        rol ptr0+1
        lda ptr0+1
        clc
        adc #$b8
        sta ptr0+1              ; ptr0 = $B800 + codice x 8
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
        lda #<mm_ttown
        ldx #>mm_ttown
        jsr bn_put
        jmp _sd
_fl     lda #<mm_chap               ; (12/11, committente) "chapter 3 level 4" per intero (17 caratteri); seed e
        ldx #>mm_chap               ; coordinate del PG (debug) restano solo nella mappa del villaggio
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
        jmp _bld                    ; (seed e coordinate non ci stanno: si vedono 21 caratteri, lo sprite 7 e' il marcatore)
_sd     lda #9                  ; villaggio: "town anoano 18,33": seed, coordinate del PG (debug, 06/11)
        sta bn_i
        lda #<nb_chr
        ldx #>nb_chr
        jsr seed_out            ; (11/11, O10)
        lda #16
        sta bn_i
        lda ptx
        jsr loc_num
        lda #$3a                ; ":" (separatore delle coordinate)
        jsr nb_chr
        lda pty
        jsr loc_num
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
mm_ttown .text "town", 0
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

tt_died .text "you have died", 0
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


; ------------------------------------------------------------------ la leva della sala del trono
ui_lever:
        lda #2
        sta ui_n
        jsr nav_init
_dr     jsr ui_begin
        #at 12,3
        #msg "congratulations,"
        #at 14,4
        jsr ui_cname
        #at 5,7
        #msg "slaying the demon lord is only"
        #at 13,8
        #msg "the beginning."
        #at 6,10
        #msg "this lever opens the gate to"
        #at 11,11
        #msg "the endless abyss."
        #at 13,14
        #msg "are you sure?"
        #at 14,17
        #msg "give up"
        #at 14,19
        #msg "pull the lever"
_mk     #at 12,17
        ldx #0
        jsr ui_mark
        #at 12,19
        ldx #1
        jsr ui_mark
        #at 1,24
        #msg "fire:select"
_in     jsr ui_nav
        cmp #NAV_MOVE
        beq _mk
        cmp #NAV_FIRE
        bne _in
        lda ui_cur
        beq _x                  ; give up
        lda #1                  ; pull the lever: al posto della leva il portale nero
        sta c_lever
        lda #FIN_AX
        sta tx
        lda #FIN_AY
        sta ty
        lda #T_BPORTAL
        jsr set_tile
        lda #SFX_PORTAL
        jsr sfx_play
_x      jmp ui_exit

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
        jsr ui_begin
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
        jmp _pw
_lv     cmp #2
        beq _pw                 ; "loading" e basta (modulo MENU)
        #msg "level "
        lda io_lvl              ; (12/11, committente) il piano del capitolo: "loading level 3"
        jsr lv_grp
        inx
        txa
        jsr ui_n2
_pw     jmp ui_pwait

; "please wait" centrato in riga 15 (09/11): sotto il titolo di io_screen e nelle attese ("deleting ...")
ui_pwait:
        #at 14,15
        #msg "please wait"
        rts

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
gm0     .text "resume", 0
gm1     .text "save game", 0
gm2     .text "quit game", 0
.if CHEATS
gm3     .text "cheats", 0
.endif


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
        jsr ui_puts
        ldx tmp3
        inx
.if CHEATS
        cpx #4
.else
        cpx #3
.endif
        bne _l
        rts

tt_gm   .text "game menu", 0
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
        #at VER_X,19            ; centrata (09/11)
        jsr ui_pi
        .text "version ", VERSION
        .byte 0
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
_quit   ldx #$ff                ; uscita senza salvare: vale l'ultimo "save game"
        txs
        jmp game_start


; salvataggio completo (menu RUN/STOP "save game"): piano attuale (o lasciato in memoria) nel suo slot, poi eroe + piani
; del capitolo sul disco con una sola riscrittura (sv_all, rel.asm)
gm_save:
        lda cur_level
        beq _tw
        jsr save_level
        jmp _sc
_tw     lda pend_lvl            ; nel villaggio: il piano lasciato per portale resta anche in memoria
        beq _sc
        jsr pend_save
        jsr clear_lvlblk        ; (il baule di casa e' nel blocco dell'eroe: clear_lvlblk non lo tocca)
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
_show   jsr sec_frames
        jsr ui_labels
        .byte 2,1
        .text " contents "
        .byte 0,2,17
        .text " purse "
        .byte 0,$ff
        lda #19
        jsr ib_set
        jsr sort_pack
        jsr ch_fill
        jsr nav_init
.if NOKEYS
        jsr ch_fill
        jsr ch_draw
_hg     jmp _hg                 ; screenshot: la schermata resta com'e'
.endif
_rd     jsr ch_fill
        jsr ch_draw
_in     jsr ui_nav
        cmp #NAV_MOVE
        beq _rd
        cmp #NAV_BACK
        beq _x
        cmp #NAV_FIRE
        bne _in
        lda ui_n
        beq _in
        jsr msg23
        jsr chest_take1
        bcc _ok
        jsr give_msg            ; "the belt is full." / "pack is full." / "max 10 scrolls.": resta nel baule
        jmp _rd
_ok     jsr chest_empty
        bcc _rd
        jmp ui_exit
_x      jsr chest_empty         ; un baule vuoto sparisce anche uscendo
        jmp ui_exit

; tipo del baule: ch_t & 3 = 0/1 normale, 2 con chiave, 3 d'oro; $40 epico
ch_nm_lo .byte <cn_0, <cn_1, <cn_2, <cn_3
ch_nm_hi .byte >cn_0, >cn_1, >cn_2, >cn_3
cn_0    .text "chest", 0
cn_1    .text "key chest", 0
cn_2    .text "golden chest", 0
cn_3    .text "epic chest", 0

; lista da 8 dal baule: oro preso (se c'e') + oggetti, poi '-'; ui_n = oggetti; ui_lc / sh_lc = voce del cursore
ch_fill:
        ldy #0
        lda ch_gold
        ora ch_gold+1
        beq +
        lda #$ff
        sta l8_id
        iny
+       sty tmp7                ; 1 = c'e' la riga dell'oro
        lda ch_cur
        asl
        asl
        tax
        lda #4
        sta tmp6
_c      lda ch_i,x
        beq +
        sta l8_id,y
        lda ch_b,x
        sta l8_b,y
        iny
+       inx
        dec tmp6
        bne _c
        tya
        sec
        sbc tmp7
        sta ui_n
        lda #0
_z      cpy #8
        bcs +
        sta l8_id,y
        iny
        bne _z
+       ldx #$ff
        lda ui_n
        beq +
        lda ui_cur
        clc
        adc tmp7
        adc #12
        tax
+       stx sh_lc
        txa
        bpl +
        lda #12                 ; nessun oggetto: riquadro dell'oggetto vuoto (voce '-' o l'oro)
        adc tmp7
+       sta ui_lc
        rts

ch_draw:
        jsr list8
        jsr eq_std
        jsr draw_entries
        jsr purse_draw
        jmp ch_item

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
        iny
        inc tmp3
        jmp _sh
_last   lda #0
        sta ch_i,y
        sta ch_b,y
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
        lda #0
        sta ch_t,x
        lda cx_x,x
        sta tx
        lda cx_y,x
        sta ty
        lda #T_FLOOR
        jsr set_tile
        sec
        rts

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
