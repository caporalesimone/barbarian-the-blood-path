; ===================================================================
;  slist.asm - liste a scorrimento della UI (21/11): inventario, negozi, locanda (routine unica, chiamata anche dal MENU)
;
;  Fino a 2 liste per schermata (L = 0/1, sl_l = quella con il cursore; A/D passano all'altra). Una lista e' una finestra
;  di sl_h righe dalla riga sl_y, dentro un riquadro largo 40 (cornice destra = colonna 39: barra di scorrimento) e con la
;  posizione "n/N" nel titolo (riga sl_y-1). Le voci vengono da al massimo SG_MAX segmenti (tabella comune sg_*, la lista
;  usa quelli da sl_s0 per sl_sn): un segmento = tipo (SK_*; bit 7 = riga separatrice prima, se il segmento non e' vuoto),
;  primo posto e numero di posti della tabella di quel tipo. Una voce e' un oggetto (o un posto vuoto, '-') oppure la riga
;  separatrice, che il cursore salta. Riga di una voce: colonna 1 cursore, 2 segno della provenienza (spunta / cintura /
;  zaino), 4 icona, 5.. nome; a destra, se sl_rv <> 0, il valore (routine sl_rv, nel MENU: prezzi).
;  sl_get risolve una voce: ui_sel/tmp5/ui_dur/ui_durm come ibox_ld, sl_sl = codice del posto per le azioni (zaino e
;  equipaggiamento: indice delle tabelle c_pack..; cintura $20+n; baule $40+n; merce $60+n).
; ===================================================================
SG_MAX  = 6
SK_EQ   = 0                     ; equipaggiamento: c_pack.. dall'indice PACK_N+primo
SK_PACK = 1                     ; zaino: c_pack..
SK_BELT = 2                     ; cintura: c_beltt (solo id)
SK_CHEST = 3                    ; baule della locanda: st_id.. (passo STASH_N)
SK_WARE = 4                     ; merce del negozio: l8_id / l8_b
SK_SEP  = $80                   ; riga separatrice prima del segmento
SL_ESEP = $ff                   ; sl_sl della riga separatrice

        .virtual $9480          ; (21/11) sovrapposte alle variabili dei salvataggi (slot_*: usate solo dal LOBBY e alla
sl_l    .byte ?                 ; creazione dell'eroe, mai mentre una lista e' sullo schermo)
sl_nl   .byte ?                 ; liste nella schermata (1 o 2)
sl_y    .fill 2                 ; prima riga delle voci
sl_h    .fill 2                 ; righe
sl_top  .fill 2                 ; prima voce mostrata
sl_cur  .fill 2                 ; voce del cursore
sl_n    .fill 2                 ; voci (righe separatrici comprese)
sl_s0   .fill 2                 ; primo segmento
sl_sn   .fill 2                 ; segmenti
sl_nsp  .fill 2                 ; righe separatrici
sg_k    .fill SG_MAX            ; segmenti: tipo (| SK_SEP), primo posto, posti
sg_a    .fill SG_MAX
sg_c    .fill SG_MAX
sl_rv   .word ?                 ; routine del valore a destra (0 = nessuno): A = sl_sl, ui_sel... impostati
sl_sl   .byte ?                 ; sl_get: codice del posto
sl_ns   .byte ?                 ; sl_get: righe separatrici prima della voce
sl_mk   .byte ?                 ; sl_get: segno (glifo, 0 = nessuno)
sl_e    .byte ?                 ; appoggi
sl_r    .byte ?                 ; lista che si disegna
sl_t    .byte ?
sl_w    .byte ?                 ; riga della finestra (sl_draw)
sl_bs   .byte ?                 ; barra di scorrimento: prima riga del cursore e riga dopo l'ultima
sl_be   .byte ?
sl_q    .byte ?
iv_l3   .word ?                 ; (21/11) riga 3 del riquadro dell'oggetto (iv_sel): routine della schermata
iv_mode .byte ?                 ; 0 = riga 2 con valore e durabilita' (inventario, locanda, baule), 1 = solo durabilita' (negozi)
l8_s    .fill 8                 ; (21/11 sera) suffisso della merce o del contenuto del baule del piano (accanto a l8_id / l8_b)
sl_end
        .endv
        .cerror sl_end > $94f7, "variabili delle liste oltre le variabili dei salvataggi"

; ------------------------------------------------------------------ dati di una lista
; L = X: conta le voci (sl_n) e le righe separatrici (sl_nsp) dai segmenti; cursore e finestra sulla prima voce (il
; primo segmento non ha mai la riga separatrice: la prima voce e' un oggetto o un posto)
sl_init:
        lda #0
        sta sl_top,x
        sta sl_cur,x
        sta sl_nsp,x
        sta sl_t
        ldy sl_s0,x
        lda sl_sn,x
        sta sl_r
_s      lda sg_c,y
        beq _n
        clc
        adc sl_t
        sta sl_t
        lda sg_k,y
        bpl _n
        tya                     ; (riga separatrice prima del primo segmento: mai)
        cmp sl_s0,x
        beq _n
        inc sl_t
        inc sl_nsp,x
_n      iny
        dec sl_r
        bne _s
        lda sl_t
        sta sl_n,x
        rts


; L = X: come sl_init, ma dopo un cambiamento delle voci (comprato, venduto, spostato) tiene cursore e finestra: il cursore
; resta entro le voci e mai sulla riga separatrice (sale di una)
sl_reinit:
        lda sl_cur,x
        pha
        lda sl_top,x
        pha
        jsr sl_init
        pla
        sta sl_top,x
        pla
        ldy sl_n,x
        beq _z
        cmp sl_n,x
        bcc +
        tya                     ; oltre l'ultima: l'ultima
        sbc #1
+       sta sl_cur,x
_s      lda sl_cur,x
        jsr sl_get
        bcc sl_win
        dec sl_cur,x
        bpl _s
_z      lda #0
        sta sl_cur,x
        sta sl_top,x
        rts

; L = X: finestra con il cursore dentro, senza spazio vuoto in fondo se le voci sono piu' delle righe
sl_win:
        lda sl_cur,x
        cmp sl_top,x
        bcs +
        sta sl_top,x
+       sec
        sbc sl_h,x
        bcc +
        adc #0                  ; (C = 1) cur - h + 1
        cmp sl_top,x
        bcc +
        sta sl_top,x
+       lda sl_n,x
        sec
        sbc sl_h,x
        bcs +
        lda #0
+       cmp sl_top,x
        bcs +
        sta sl_top,x
+       rts

; A/X = tabella (numero di segmenti, poi tipo, primo posto, posti per ognuno), Y = primo segmento: copiata in sg_*
sl_segs:
        sta ptr2
        stx ptr2+1
        sty sl_t
        ldy #0
        lda (ptr2),y
        sta sl_e
_l      ldx sl_t
        iny
        lda (ptr2),y
        sta sg_k,x
        iny
        lda (ptr2),y
        sta sg_a,x
        iny
        lda (ptr2),y
        sta sg_c,x
        inc sl_t
        dec sl_e
        bne _l
        rts

; ------------------------------------------------------------------ voce
; voce A della lista X -> C = 1 riga separatrice; altrimenti ui_sel, tmp5, ui_dur, ui_durm, sl_sl, sl_mk. sl_ns = righe
; separatrici prima della voce. X conservato.
sl_get:
        sta sl_e
        lda #0
        sta sl_ns
        ldy sl_s0,x
_s      lda sg_c,y
        beq _nx
        lda sg_k,y
        bpl _in
        tya
        cmp sl_s0,x
        beq _in
        lda sl_e                ; la riga separatrice prima del segmento
        bne +
        lda #SL_ESEP
        sta sl_sl
        sec
        rts
+       dec sl_e
        inc sl_ns
_in     lda sl_e
        cmp sg_c,y
        bcc _it
        sbc sg_c,y
        sta sl_e
_nx     iny
        bne _s                  ; (sempre: la voce esiste)
_it     adc sg_a,y              ; (C = 0) posto nella tabella del tipo
        sta sl_t
        lda sg_k,y
        and #$7f
        tay
        lda sk_mk,y
        sta sl_mk
        lda #0
        sta ui_dur
        sta ui_durm
        sta tmp5
        stx sl_r
        cpy #SK_BELT
        bcs _ob
        lda sl_t                ; zaino ed equipaggiamento: indice delle tabelle c_pack..
        cpy #SK_EQ
        bne +
        clc
        adc #PACK_N
+       sta sl_sl
        tax
        jsr ibox_ld
        ldx sl_r
        clc
        rts
_ob     lda sk_sl-SK_BELT,y
        ora sl_t
        sta sl_sl
        ldx sl_t
        cpy #SK_BELT
        bne +
        lda c_beltt,x
        sta ui_sel
        ldx sl_r
        clc
        rts
+       cpy #SK_CHEST
        bne _wa
        lda st_id,x
        sta ui_sel
        lda st_b,x
        sta tmp5
        lda st_du,x
        sta ui_dur
        lda st_m,x
        sta ui_durm
        ldx sl_r
        clc
        rts
_wa     lda l8_id,x
        sta ui_sel
        lda l8_b,x
        sta tmp5
        ldx sl_r
        clc
        rts
sk_mk   .byte CH_EQ, CH_PACK, CH_BELT, 0, 0
sk_sl   .byte $20, $40, $60

; voce del cursore della lista attiva -> come sl_get
sl_sel:
        ldx sl_l
        lda sl_cur,x
        jmp sl_get

; ------------------------------------------------------------------ disegno
ICOL_EQ = 7                     ; colori dei segni: spunta gialla, cintura azzurra (UC_LABEL), zaino grigio chiaro (UC_BTTL)

; tutta la lista X (righe, barra di scorrimento, posizione nel titolo). X conservato.
sl_draw:
        stx sl_r
        lda #0
        sta sl_w
_r      ldx sl_r
        lda sl_w
        clc
        adc sl_top,x
        jsr sl_row
        inc sl_w
        ldx sl_r
        lda sl_w
        cmp sl_h,x
        bne _r
        lda #$ff                ; barra: solo se le voci non stanno nella finestra
        sta sl_bs
        sta sl_be
        lda sl_h,x
        cmp sl_n,x
        bcs _bd
        tay                     ; lunghezza = h*h/n (almeno 1), posizione = top*(h-lunghezza)/(n-h)
        jsr sl_mul
        ldy sl_n,x
        jsr sl_div
        bne +
        lda #1
+       sta sl_q
        lda sl_h,x
        sec
        sbc sl_q
        tay
        lda sl_top,x
        jsr sl_mul
        pha
        lda sl_n,x
        sec
        sbc sl_h,x
        tay
        pla
        jsr sl_div
        sta sl_bs
        clc
        adc sl_q
        sta sl_be
_bd     lda #0
        sta sl_w
_bl     ldx sl_r
        lda sl_w
        clc
        adc sl_y,x
        tay
        ldx #39
        jsr ui_at
        lda #BOX_V
        ldx ui_bc
        ldy sl_w
        cpy sl_bs
        bcc +
        cpy sl_be
        bcs +
        lda #CH_THUMB
        ldx #UC_BTTL
+       jsr ui_icon
        inc sl_w
        ldx sl_r
        lda sl_w
        cmp sl_h,x
        bne _bl
        ldy sl_y,x              ; posizione nel titolo: cornice sulle colonne 30..38, poi " n/N " allineato a destra
        dey
        sty sl_w
        ldx #30
        jsr ui_at
        lda ui_bc
        sta ui_col
        ldx #9
-       lda #BOX_H
        jsr ui_putc
        dex
        bne -
        ldx sl_r
        lda sl_bs
        bmi _x
        lda sl_cur,x            ; n = voce + 1 - righe separatrici prima, N = voci - righe separatrici
        jsr sl_get
        lda sl_cur,x
        sec
        sbc sl_ns
        sta sl_t                ; n - 1
        lda sl_n,x
        sec
        sbc sl_nsp,x
        sta sl_e                ; N
        lda #5                  ; lunghezza " n/N ": 5 con una cifra per numero
        ldy sl_t
        cpy #9
        bcc +
        adc #0                  ; (C = 1: +1)
+       ldy sl_e
        cpy #10
        bcc +
        adc #0
+       eor #$ff                ; colonna = 39 - lunghezza
        sec
        adc #39
        tax
        ldy sl_w
        jsr ui_at
        lda #UC_BTTL
        sta ui_col
        lda #$20
        jsr ui_putc
        ldx sl_t
        inx
        txa
        jsr ui_b3l
        lda #$2f
        jsr ui_putc
        lda sl_e
        jsr ui_b3l
        lda #$20
        jsr ui_putc
_x      ldx sl_r
        rts

; A * Y -> A (saturato a 255)
sl_mul:
        sta sl_t
        lda #0
        cpy #0
        beq _r
_l      clc
        adc sl_t
        bcs _c
        dey
        bne _l
_r      rts
_c      lda #255
        rts

; A / Y -> A (per difetto; Y > 0). Z = 1 se il quoziente e' 0
sl_div:
        sty sl_t
        ldy #0
_l      cmp sl_t
        bcc _d
        sbc sl_t
        iny
        bne _l
_d      tya
        rts

; voce A della lista sl_r alla riga sl_w della finestra: cursore, segno, icona, nome, valore. Oltre l'ultima: riga vuota
sl_row:
        pha
        lda sl_w
        clc
        adc sl_y,x
        tay
        ldx #1
        jsr ui_at
        ldy #37                 ; pulisce le colonne 1..38
        lda #$20
-       sta (cp),y
        dey
        bpl -
        ldx sl_r
        pla
        cmp sl_n,x
        bcc +
        rts
+       pha
        jsr sl_get
        pla
        bcs _sep
        ldy sl_l                ; '>' solo nella lista attiva
        cpy sl_r
        bne +
        cmp sl_cur,x
        bne +
        lda #$3e
        jsr ui_putc
+       lda #1                  ; colonna 2: segno nel suo colore
        sta cidx
        lda sl_mk
        beq +
        ldx #ICOL_EQ
        cmp #CH_EQ
        beq _mc
        ldx #UC_LABEL
        cmp #CH_BELT
        beq _mc
        ldx #UC_BTTL
_mc     jsr ui_icon
+       lda #3                  ; colonna 4: icona, 5: nome (o '-')
        sta cidx
        lda ui_sel
        bne _it
        inc cidx
        lda #UC_EMPTY
        sta ui_col
        lda #$2d
        jsr ui_putc
        jmp _v
_it     jsr ui_cic
        lda tmp5
        sta ui_ib
        lda #0                  ; rotto (durabilita' 0 su un massimo > 0): in rosso
        ldy ui_durm
        beq +
        ldy ui_dur
        bne +
        lda #2
+       sta ui_fc
        lda ui_sel
        jsr ui_item
        lda #0
        sta ui_fc
_v      ldx sl_r
        lda sl_rv+1             ; valore a destra (routine del MENU: A = sl_sl)
        beq _x
        lda sl_sl
        jmp (sl_rv)
_sep    lda #9                  ; riga separatrice sottile, colonne 10..29
        sta cidx
        lda ui_bc
        sta ui_col
        ldx #20
-       lda #CH_SEP
        jsr ui_putc
        dex
        bne -
_x      ldx sl_r
        rts

; ------------------------------------------------------------------ cursore
; un fotogramma: A = NAV_BACK (RUN/STOP), NAV_MOVE (cursore o lista cambiati, gia' ridisegnati), NAV_FIRE, NAV_NONE
sl_nav:
        jsr ui_input
.if NOKEYS
        lda #NAV_NONE
        rts
.endif
        lda keynew+7
        and #$80
        beq +
        lda #NAV_BACK
        rts
+       ldx sl_l
        lda joynew
        lsr
        bcs _up
        lsr
        bcs _dn
        and #3                  ; sinistra / destra (A / D): l'altra lista
        beq _f
        lda sl_nl
        cmp #2
        bcc _no
        txa
        eor #1
        sta sl_l
        jsr sl_draw             ; (X = la lista lasciata: senza cursore)
        ldx sl_l
        jmp _mv
_f      jsr ui_fire
        beq _no
        lda #NAV_FIRE
        rts
_no     lda #NAV_NONE
        rts
_up     lda sl_n,x
        beq _no
_u1     ldy sl_cur,x
        bne +
        ldy sl_n,x              ; dalla prima voce: l'ultima
+       dey
        tya
        sta sl_cur,x
        jsr sl_get
        bcs _u1                 ; (la riga separatrice si salta)
        bcc _mv
_dn     lda sl_n,x
        beq _no
_d1     ldy sl_cur,x
        iny
        tya
        cmp sl_n,x
        bcc +
        lda #0
+       sta sl_cur,x
        jsr sl_get
        bcs _d1
_mv     jsr sl_win              ; finestra: il cursore dentro
        jsr sl_draw
        lda #NAV_MOVE
        rts
