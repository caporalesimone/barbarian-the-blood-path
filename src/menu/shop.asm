; ===================================================================
;  menu/shop.asm - i negozi (fabbro, alchimista), parte del modulo MENU (src/menu.asm; fino all'11/11 in ui.asm).
;  Si entra da enter_shop (tabella dei salti del modulo, MENU_SHOP) con A = negozio; gira con $01 = $35 (KERNAL
;  escluso: parte del codice sta nella zona 2, sotto il KERNAL), come la locanda.
; ===================================================================
; ------------------------------------------------------------------ negozi
; (21/11, branch liste-menu, prototipi approvati dal committente) due liste a scorrimento (src/game/slist.asm, segmento CORE):
;   lista 0 "wares": la merce (prezzo pieno a destra);
;   lista 1 "gear" (fabbro: arma, armatura e scudo indossati, poi armi/armature/scudi dello zaino e i posti liberi) o "yours"
;   (alchimista: anello indossato, cintura, anelli e pergamene dello zaino e i posti liberi), con il prezzo di vendita a destra.
; Le azioni lavorano sui codici di prima in ui_lc (sh_cur): 0..7 zaino, 8..12 equipaggiamento, LC_W.. merce, LC_B.. cintura (21/11 sera: prima merce 12 = secondo anello).
; Fire: merce = compra, zaino e cintura = vende (l'indossato no: "unequip to sell"); R (fabbro): ripara zaino e indossato.
; Oro (addosso + baule della locanda) nel titolo della lista 1.
; (11/11) variabili dei negozi in pagina zero ($82-$8C, libera nel gioco: docs/wiki/tecnica.md); shp_stock, sh_mask, sh_lc
; restano a $9400 (src/game/ui.asm)
shop_id   = $82
shp_first = $83
shp_cnt   = $84
shp_k     = $85                 ; quanti oggetti mostrati
shp_i     = $86
shp_item  = $87
shp_price = $88                 ; (2 B)
sh_slot   = $8a                 ; posto della cintura scelto per la pozione comprata ($FF = nessuna scelta)
sh_dir    = $8c                 ; +1 / -1: passo nella scelta del posto della cintura
sh_cats .byte 1<<CAT_WEAPON | 1<<CAT_ARMOR | 1<<CAT_SHIELD          ; 0 fabbro, 1 alchimista (09/11: niente armaiolo)
        .byte 1<<CAT_RING | 1<<CAT_POTION | 1<<CAT_SCROLL

enter_shop:                     ; (interrupt spenti: tabella dei salti di src/menu.asm)
        sta shop_id
        tax
        lda shop_first,x
        sta shp_first
        lda shop_cnt,x
        sta shp_cnt             ; dimensione del pool
        lda #SHOP_KN            ; (21/11 sera, committente) da SHOP_KMIN a SHOP_KMIN + SHOP_KN - 1 oggetti, con ripetizioni
        jsr rndrange
        clc
        adc #SHOP_KMIN
        sta shp_k
        lda frame               ; un po' di entropia in piu': ogni visita estrae un assortimento nuovo
        eor rnd
        sta rnd
        jsr shop_roll
        jsr sort_pack
        ldx #7
_cp     stx shp_i
        lda #0
        sta l8_b,x
        sta l8_s,x
        sta l8_id,x
        cpx shp_k
        bcs _cz
        lda shp_cnt             ; (21/11 sera) un oggetto a caso del pool filtrato (ripetizioni ammesse)
        jsr rndrange
        tay
        lda shp_stock,y
        sta l8_id,x
        tay
        lda c_lvl               ; affissi (af_gen): livello = livello del PG; magico con probabilita' shm_t[livello]
        cmp #MAXLEVEL
        bcc _cl
        lda #MAXLEVEL
_cl     sta af_l
        lda #2                  ; negozio: af_gen decide se e' magico con shm_t[livello] (tabella sotto l'I/O)
        sta af_m
        lda #31
        sta af_tt
        jsr af_gen
        ldx shp_i
        lda ap_b
        sta l8_b,x
        lda ap_s
        sta l8_s,x
        lda #0
        sta ap_b
        sta ap_s
_cz     ldx shp_i
        dex
        bpl _cp
        lda shp_k
        sta shp_cnt             ; da qui shp_cnt = oggetti in vendita
        jsr ui_begin
        ldx shop_id
        lda sh_cats,x
        sta sh_mask
        lda #$ff
        sta sh_slot
        jsr shop_title
        jsr ls2_frame
        jsr ui_labels
        .byte 2,1
        #t5 " wares "
        .byte $ff
        lda shop_id
        bne +
        jsr ui_labels
        .byte 2,9
        #t5 " gear "
        .byte $ff
        jmp ++
+       jsr ui_labels
        .byte 2,9
        #t5 " yours "
        .byte $ff
+       lda #1
        sta iv_mode
        lda #<sh_l3
        sta iv_l3
        lda #>sh_l3
        sta iv_l3+1
        lda #<sh_price
        sta sl_rv
        lda #>sh_price
        sta sl_rv+1
        jsr sh_segs
        jsr ls2_init
        jmp _dr
_rb     jsr sh_segs             ; le voci possono essere cambiate (comprato, venduto)
        ldx #1
        jsr sl_reinit
        dex
        jsr sl_reinit
_dr     jsr sh_draw
_in     jsr sl_nav
        cmp #NAV_BACK
        beq _exit
        cmp #NAV_MOVE
        bne +
        jsr sh_cur
        jsr iv_sel
        jsr sh_keys
        jmp _in
+       cmp #NAV_FIRE
        bne _k
        jsr sh_cur
        jsr sh_fire
        jmp _rb
_k      lda keynew+2            ; R: ripara (solo il fabbro; zaino ed equipaggiamento)
        and #$02
        beq _in
        lda shop_id
        bne _in
        jsr sh_cur
        ldx ui_lc
        cpx #LC_W
        bcs _in
        jsr shop_repair
        jmp _rb
_exit   lda #0
        sta sh_mask
        sta sl_rv+1
        jmp mk_exit

; segmenti delle due liste (sg_*, sl_s0, sl_sn): merce; equipaggiamento (e cintura), blocco delle categorie del negozio nello
; zaino (ordinato: un blocco solo), posti liberi dello zaino
sh_segs:
        lda #SK_WARE
        sta sg_k
        lda #0
        sta sg_a
        sta sl_s0
        lda shp_cnt
        sta sg_c
        ldy #1
        sty sl_sn
        sty sl_s0+1
        lda #SK_EQ
        sta sg_k,y
        ldx shop_id
        lda sh_eq0,x            ; fabbro: arma, armatura, scudo; alchimista: l'anello
        sta sg_a,y
        lda sh_eqn,x
        sta sg_c,y
        iny
        txa
        beq +
        lda #SK_BELT|SK_SEP     ; alchimista: la cintura
        sta sg_k,y
        lda #0
        sta sg_a,y
        lda #4
        sta sg_c,y
        iny
+       ldx #0                  ; zaino: tmp6 = primo della categoria, tmp7 = quanti, tmp4 = posti usati
        stx tmp7
_l      lda c_pack,x
        beq _e
        sty tmp3
        tay
        lda itcat,y
        tay
        lda cat_bit,y
        ldy tmp3
        and sh_mask
        beq _n
        lda tmp7
        bne +
        stx tmp6
+       inc tmp7
_n      inx
        cpx #PACK_N
        bne _l
_e      stx tmp4
        lda #SK_PACK|SK_SEP
        sta sg_k,y
        lda tmp6
        sta sg_a,y
        lda tmp7
        sta sg_c,y
        iny
        lda tmp7                ; posti liberi: la riga separatrice solo se il blocco prima e' vuoto
        cmp #1
        lda #SK_PACK|SK_SEP
        bcc +
        lda #SK_PACK
+       sta sg_k,y
        lda tmp4
        sta sg_a,y
        lda #PACK_N
        sec
        sbc tmp4
        sta sg_c,y
        dey                     ; segmenti della lista 1 = Y (l'ultimo) - 1 + 1
        sty sl_sn+1
        rts
sh_eq0  .byte 0, 3
sh_eqn  .byte 3, 2              ; (21/11) alchimista: i due anelli

; voce del cursore -> ui_lc (codici di prima: 0..7 zaino, 8..12 equipaggiamento, LC_W.. merce, LC_B.. cintura (21/11 sera: prima merce 12 = secondo anello))
sh_cur: jsr sl_sel
        lda sl_sl
        cmp #$20
        bcc _s
        cmp #$60
        and #$1f
        bcs _w
        adc #LC_B
        bne _s
_w      clc
        adc #LC_W
_s      sta ui_lc
        rts

; tutta la schermata variabile: oro nel titolo della lista 1, liste, oggetto, tasti. Nella scelta del posto della pozione
; (sh_slot) il cursore sta sul posto della cintura (lista 1: anello, riga separatrice, poi la cintura)
sh_draw:
        lda sh_slot
        bmi +
        clc
        adc #2
        sta sl_cur+1
        lda #1
        sta sl_l
        tax
        jsr sl_win
        jmp ++                  ; (ui_lc resta la merce che si compra)
+       jsr sh_cur
+       ldx #21
        ldy #9
        jsr ui_at
        jsr shop_gold
        jsr ls2_draw
; riga 24: i tasti secondo la voce
sh_keys:
        jsr row24
        lda sh_slot
        bmi +
        #msg "fire:buy  run/stop:cancel"
        rts
+       lda ui_lc
        cmp #8
        bcc _sl
        cmp #LC_W
        bcc _rp
        cmp #LC_B
        bcs _sl
        #msg "fire:buy"
        jmp _bk
_sl     #msg "fire:sell"
        lda ui_lc
        cmp #8
        bcs _bk
        lda shop_id
        bne _bk
        #msg "  "
_rp     lda shop_id
        bne _b2
        #msg "r:repair"
_bk     #msg "  "
_b2     #msg "run/stop:back"
        rts

; prezzo a destra della voce (sl_rv, da sl_row: A = sl_sl, ui_sel): merce prezzo pieno, il resto prezzo di vendita
sh_price:
        ldx ui_sel
        beq sh_rts
        cmp #$60
        jsr sh_pr
        lda #32                 ; colonne 33-37 (riga da ui_at 1), moneta in 38
        sta cidx
sh_num  jsr ui_num5
        jmp ui_coin
sh_rts  rts
; C = 1 prezzo pieno di ui_sel, C = 0 prezzo di vendita (>> SELL_SHIFT) -> tmp0/tmp1
sh_pr:  php
        lda ui_sel              ; (fase 3) con gli affissi della voce (sl_get: ui_px, ui_sx)
        ldx ui_px
        ldy ui_sx
        jsr it_cost
        plp
        bcs +
        .rept SELL_SHIFT
        lsr tmp1
        ror tmp0
        .endrept
+       rts

; riga 3 del riquadro dell'oggetto (iv_l3): indossato "unequip to sell" e, dal fabbro, il costo della riparazione; merce
; "buy"; zaino e cintura "sell"; a destra come nelle liste
sh_l3:  ldx ui_sel
        beq _r
        ldx ui_lc
        cpx #8
        bcc _sl
        cpx #LC_W
        bcc _eq
        cpx #LC_B
        bcs _sl
        ldx #29
        jsr _at
        #msg "buy "
        sec
        bcs _pr
_sl     ldx #28
        jsr _at
        #msg "sell "
        clc
_pr     jsr sh_pr
        jmp sh_num
_eq     lda #CH_EQ
        ldx #ICOL_EQ
        jsr ui_icon
        lda #UC_EMPTY
        sta ui_col
        #msg " unequip to sell"
        lda shop_id
        bne _r
        ldx ui_lc
        jsr rep_cost
        bcs _r
        ldx #26
        jsr _at
        #msg "repair "
        lda shp_price
        sta tmp0
        lda shp_price+1
        sta tmp1
        jmp sh_num
_r      rts
_at     ldy #IV_SY+3            ; colonna X della riga 3, colore dei valori
        jsr ui_at
        lda #UC_VALUE
        sta ui_col
        rts

; Fire sulla voce ui_lc: merce = compra, zaino e cintura = vende, indossato = niente (si vende solo dallo zaino)
sh_fire:
        lda ui_lc
        cmp #8
        bcc _s
        cmp #LC_W
        bcc _r
        cmp #LC_B
        bcc _b
_s      jmp shop_sell
_b      jmp shop_buy
_r      rts

; A = id dell'oggetto della voce ui_lc (0 = niente)
; (fase 3) prezzo pieno della voce ui_lc con i suoi affissi -> tmp0/tmp1 (it_cost)
sh_cost:
        ldx ui_lc
        cpx #LC_W
        bcc _p
        ldy #0
        cpx #LC_B
        bcc _w
        lda c_beltt-LC_B,x
        ldx #0
        jmp it_cost
_w      ldy l8_s-LC_W,x
        lda l8_id-LC_W,x
        pha
        lda l8_b-LC_W,x
        jmp +
_p      ldy c_packs,x
        lda c_pack,x
        pha
        lda c_packb,x
+       tax
        pla
        jmp it_cost

sh_selid:
        ldx ui_lc
        cpx #LC_W
        bcc _p
        cpx #LC_B
        bcc _w
        lda c_beltt-LC_B,x
        rts
_w      lda l8_id-LC_W,x
        rts
_p      lda c_pack,x            ; zaino e (subito dopo) equipaggiamento
        rts

; C=0 se il negozio compra la categoria di ui_sel
sh_buys:
        ldx ui_sel
        ldy itcat,x
        lda cat_bit,y
        and sh_mask
        clc
        bne +
        sec
+       rts


; copia in shp_stock il pool filtrato per il livello del PG (shp_cnt = quanti); (21/11 sera) la merce si estrae con
; ripetizioni in enter_shop (prima: Fisher-Yates parziale, senza ripetizioni); pool vuoto: niente merce (shp_k = 0)
shop_roll:
        ldx #0                  ; solo gli oggetti per il livello del PG (shop_minl <= c_lvl)
        ldy shp_first
_c      lda shop_minl,y
        cmp c_lvl
        beq +
        bcs _nx
+       lda shop_items,y
        sta shp_stock,x
        inx
_nx     iny
        dec shp_cnt
        bne _c
        stx shp_cnt             ; pool filtrato
        bne +
        stx shp_k
+       rts

; chiede conferma: shp_price = prezzo, A = 0 acquisto / 1 vendita. C=1 se Y, C=0 se N
; chiede conferma: shp_price = prezzo, A = 0 acquisto / 1 vendita. C=1 se Y, C=0 se N
shop_ask:
        pha
        jsr msg23
        pla
        bne _s
        #msg "buy for "
        jmp _p
_s      cmp #2
        bne _s1
        #msg "repair for "
        jmp _p
_s1     #msg "sell for "
_p      lda shp_price
        ldx shp_price+1
        jsr ui_n5l
        jsr ui_coin
        lda #"?"
        jsr ui_putc
        jsr ui_yesno
        bcc _no
        jsr msg23
        sec
        rts
_no     jsr msg23
        #msg "cancelled."
        clc
        rts

; ------------------------------------------------------------------ schermate negozio
shop_ic  .byte CH_ANVIL, CH_FLASK
shop_nm_lo .byte <sn_smith, <sn_alch
shop_nm_hi .byte >sn_smith, >sn_alch
sn_smith #t5 "blacksmith"
sn_alch  #t5 "alchemist"

; titolo (riga 0): icona + nome + icona
shop_title:
        ldx shop_id
        ldy shop_ic,x
        lda shop_nm_lo,x
        pha
        lda shop_nm_hi,x
        tax
        pla
        jmp ui_title
; "not enough o." nel riquadro dei messaggi
;; (10/11) pagamento nei negozi: prima l'oro addosso, poi il baule della locanda (c_sgold, in decine).
; gold_need: C=1 se c_gold + 10 x c_sgold < shp_price; altrimenti C=0, tmp0:1 = decine da prendere dal baule (0 = basta
; l'oro addosso), tmp6 = resto che torna addosso (0..9). gold_pay: paga (rifa' il conto: chiamarla dopo gold_need con C=0)
gold_need:
        lda c_gold
        sec
        sbc shp_price
        sta tmp0
        lda c_gold+1
        sbc shp_price+1
        sta tmp1
        bcc _ch
        lda #0                  ; basta l'oro addosso
        sta tmp0
        sta tmp1
        clc
        rts
_ch     jsr neg16               ; manca = prezzo - addosso
        jsr div10t              ; tmp0:1 = decine, A = unita'
        sta tmp6
        cmp #0                  ; (sta non tocca i flag: Z veniva dal dex di div10t)
        beq +
        lda #10                 ; una decina in piu', il resto torna addosso
        sec
        sbc tmp6
        sta tmp6
        inc tmp0
        bne +
        inc tmp1
+       lda c_sgold             ; C=1 se c_sgold >= decine
        cmp tmp0
        lda c_sgold+1
        sbc tmp1
        rol a                   ; C invertito: 0 = ci sono
        eor #1
        lsr a
        rts
gold_pay:
        jsr gold_need
        lda tmp0
        ora tmp1
        bne _sb
        lda c_gold
        sec
        sbc shp_price
        sta c_gold
        lda c_gold+1
        sbc shp_price+1
        sta c_gold+1
        rts
_sb     lda c_sgold
        sec
        sbc tmp0
        sta c_sgold
        lda c_sgold+1
        sbc tmp1
        sta c_sgold+1
        lda tmp6
        sta c_gold
        lda #0
        sta c_gold+1
        rts

; messaggio "not enough" + moneta in riga 23
no_gold:
        jsr msg23
        #msg "not enough "
        jsr ui_coin
        lda #$2e
        jmp ui_putc

