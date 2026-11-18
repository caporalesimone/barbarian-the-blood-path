; ===================================================================
;  menu/shop.asm - i negozi (fabbro, alchimista), parte del modulo MENU (src/menu.asm; fino all'11/11 in ui.asm).
;  Si entra da enter_shop (tabella dei salti del modulo, MENU_SHOP) con A = negozio; gira con $01 = $35 (KERNAL
;  escluso: parte del codice sta nella zona 2, sotto il KERNAL), come la locanda.
; ===================================================================
; ------------------------------------------------------------------ negozi
; negozi (08/11, concept con il committente): una schermata a riquadri uguale per tutti, senza linguette.
; Voci (codici in ui_lc): 0..7 zaino, 8..11 equipaggiamento, 12..19 merce, 20..23 cintura, 24 pergamene.
; ui_cur = posizione nell'ordine del cursore (sh_nav): merce, equipaggiamento (solo fabbro), zaino, cintura e
; pergamene (solo alchimista). Fire: merce = compra, zaino/cintura = vende, equipaggiamento = ripara;
; R (fabbro) ripara zaino ed equipaggiamento. L'equipaggiamento non si vende mai. Ogni negozio compra solo le
; categorie di cio' che vende (sh_cats); gli altri oggetti dello zaino sono grigi (pk_name).
SH_N = 25
; (11/11) variabili dei negozi in pagina zero ($82-$8C, libera nel gioco: docs/wiki/tecnica.md); shp_stock, sh_mask, sh_lc
; restano a $9400 (src/game/ui.asm: le usano anche inventario e baule)
shop_id   = $82
shp_first = $83
shp_cnt   = $84
shp_k     = $85                 ; quanti oggetti mostrati
shp_i     = $86
shp_item  = $87
shp_price = $88                 ; (2 B)
sh_slot   = $8a                 ; posto della cintura scelto per la pozione comprata ($FF = nessuna scelta)
sh_old    = $8b                 ; ui_cur prima di ui_nav (direzione del movimento)
sh_dir    = $8c                 ; +1 / -1: passo di sh_fix
sh_nav  .byte 12,13,14,15,16,17,18,19, 8,9,10,11, 0,1,2,3,4,5,6,7, 20,21,22,23,24
sh_cats .byte 1<<CAT_WEAPON | 1<<CAT_ARMOR | 1<<CAT_SHIELD          ; 0 fabbro, 1 alchimista (09/11: niente armaiolo)
        .byte 1<<CAT_RING | 1<<CAT_POTION | 1<<CAT_SCROLL

enter_shop:                     ; (KERNAL gia' escluso: tabella dei salti di src/menu.asm)
        sta shop_id
        tax
        lda shop_first,x
        sta shp_first
        lda shop_cnt,x
        sta shp_cnt             ; dimensione del pool
        lda shop_stock,x
        sta shp_k
        lda frame               ; un po' di entropia in piu': ogni visita estrae un assortimento nuovo
        eor rnd
        sta rnd
        jsr shop_roll
        jsr sort_pack
        lda shp_k
        sta shp_cnt             ; da qui shp_cnt = oggetti in vendita
        ldx #7                  ; lista da 8: la merce, poi '-'
_cp     lda #0
        sta l8_b,x
        cpx shp_cnt
        bcs +
        lda shp_stock,x
+       sta l8_id,x
        dex
        bpl _cp
        jsr ui_begin
        ldx shop_id
        lda sh_cats,x
        sta sh_mask
        lda #$ff
        sta sh_slot
        lda #SH_N
        sta ui_n
        jsr nav_init
        jsr shop_title
        jsr sec_frames
        jsr ui_labels
        .byte 2,1
        .text " wares "
        .byte 0,2,17
        .text " purse "
        .byte 0,$ff
        lda #19
        jsr ib_set
        lda #1
        bne _fx
_in     lda ui_cur
        sta sh_old
        jsr ui_nav
        cmp #NAV_BACK
        beq _exit
        cmp #NAV_MOVE
        bne _nm
        lda ui_cur              ; direzione: avanti se ui_cur = sh_old + 1 (o giro dall'ultima alla prima)
        sec
        sbc sh_old
        cmp #1
        beq _f1
        cmp #$100-(SH_N-1)
        beq _f1
        lda #$ff
        .byte $2c
_f1     lda #1
_fx     sta sh_dir
        jsr sh_fix
_rd     jsr sh_draw
        jmp _in
_nm     cmp #NAV_FIRE
        bne _k
        jsr sh_fire
        jmp _ref
_k      lda keynew+2            ; R: ripara (solo il fabbro; zaino ed equipaggiamento)
        and #$02
        beq _in
        lda shop_id
        bne _in
        ldx ui_lc
        cpx #12
        bcs _in
        jsr shop_repair
_ref    lda #1                  ; la voce puo' essere sparita (pozione, pergamene vendute)
        sta sh_dir
        jsr sh_fix
        jmp _rd
_exit   lda #0
        sta sh_mask
        jmp mk_exit

; cursore su una voce valida (passo sh_dir, con giro); ui_lc = codice della voce
sh_fix:
_l      ldx ui_cur
        lda sh_nav,x
        sta ui_lc
        jsr sh_valid
        bcc _r
        lda ui_cur
        clc
        adc sh_dir
        bpl +
        lda #SH_N-1
+       cmp #SH_N
        bcc +
        lda #0
+       sta ui_cur
        jmp _l
_r      rts

; A = codice: C=0 se la voce esiste in questo negozio
sh_valid:
        cmp #8
        bcc _y                  ; zaino: sempre (anche i posti vuoti, come nell'inventario)
        cmp #12
        bcs _w
        ldx shop_id             ; equipaggiamento: solo dal fabbro (riparazione)
        bne _n
        beq _y
_w      cmp #20
        bcs _b
        sbc #11                 ; (C=0) merce: indice < shp_cnt
        cmp shp_cnt
        rts
_b      ldx shop_id             ; cintura e pergamene: solo dall'alchimista
        cpx #1
        bne _n
        cmp #24
        beq _s
        tax
        lda c_beltt-20,x
        beq _n
_y      clc
        rts
_s      jmp scr_find
_n      sec
        rts

; A = id dell'oggetto della voce ui_lc (0 = niente)
sh_selid:
        ldx ui_lc
        cpx #12
        bcc _p
        cpx #20
        bcc _w
        cpx #24
        beq _s
        lda c_beltt-20,x
        rts
_s      lda #I_SCROLL
        rts
_w      lda l8_id-12,x
        rts

_p      lda c_pack,x            ; zaino e (subito dopo) equipaggiamento
        rts

; bonus della voce ui_lc (lista da 8: l8_b; altre: 0) -> A
l8_bonus:
        ldx ui_lc
        lda #0
        cpx #12
        bcc +
        cpx #20
        bcs +
        lda l8_b-12,x
+       rts

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

; negozio: merce, zaino ed equipaggiamento con il '>' sulla voce del cursore (sul posto della cintura nella scelta
; del posto della pozione, sh_slot), poi il riquadro dell'oggetto scelto
sh_draw:
        lda ui_lc               ; nella scelta del posto della pozione il '>' e' sul posto (sh_slot)
        ldx sh_slot
        bmi +
        txa
        clc
        adc #20
+       sta sh_lc
        jsr list8               ; merce
        jsr eq_std
        jsr draw_entries
        jsr purse_draw
; riquadro dell'oggetto selezionato (standard, 20,17): nome, caratteristiche, riga 3 secondo la voce
sh_item:
        ldx #21                 ; nome nella riga prima di ib_y
        ldy ib_y
        dey
        jsr ui_at
        lda ui_lc
        cmp #12
        bcs _o
        tax                     ; zaino / equipaggiamento
        lda c_pack,x
        jsr ui_cic
        jsr pk_name
        ldx ui_lc
        jsr ibox_ld
        jmp _t
_o      jsr sh_selid
        sta ui_sel
        jsr l8_bonus
        sta ui_ib
        lda ui_sel
        jsr ui_cic
        lda ui_sel
        jsr ui_item
        jsr l8_bonus            ; dopo ui_item (ui_puts usa tmp5)
        sta tmp5
        lda #0
        sta ui_dur
        sta ui_durm
_t      jsr ibox_top
        bne +
        jmp sh_help
+       jsr ib_at1
        ldx ui_lc
        cpx #8
        bcc _pk
        cpx #12
        bcc _eq
        cpx #20
        bcs _sl
        lda sh_mask
        bne +
        jmp _vl                 ; baule: valore
+       #msg "buy "             ; merce: prezzo pieno
        lda ui_sel
        asl
        tay
        lda itprice,y
        ldx itprice+1,y
        jsr ui_n5l
        jsr ui_coin
        jmp _have
_eq     jsr rep_cost            ; equipaggiamento: costo della riparazione se serve
        bcs _vl
        #msg "fix "
        lda shp_price
        ldx shp_price+1
        jsr ui_n5l
        jsr ui_coin
        jsr it_dur
        jmp sh_help
_pk     jsr sh_buys             ; zaino: offerta se il negozio lo compra
        bcs _vl
_sl     #msg "sell "
        jsr it_half
_have   ldx ui_sel              ; pozioni e pergamene: quante se ne hanno
        lda itcat,x
        cmp #CAT_SCROLL
        beq _hs
        cmp #CAT_POTION
        bne sh_help
        ldy #0
        ldx #3
_hc     lda c_beltt,x
        cmp ui_sel
        bne +
        iny
+       dex
        bpl _hc
        tya
        jmp _hp
_hs     jsr scr_find
        lda #0
        bcs _hp
        lda c_packb,y
_hp     pha
        #msg " have "
        pla
        jsr ui_b3l
        jmp sh_help
_vl     jsr it_val
; riga 24: i tasti secondo la voce
sh_help:
        ldy #24
        jsr clear_row
        #at 1,24
        lda sh_mask
        bne +
        #msg "fire:take  run/stop:back"
        rts
+       #msg "fire:"
        lda ui_lc
        cmp #8
        bcc _sl
        cmp #12
        bcc _rp
        cmp #20
        bcs _sl
        #msg "buy"
        jmp _bk
_rp     #msg "repair"
        jmp _bk
_sl     #msg "sell"
        lda ui_lc
        cmp #8
        bcs _bk
        lda shop_id
        bne _bk
        #msg "  r:repair"
_bk     #msg "  run/stop:"
        lda sh_slot
        bmi _b
        #msg "cancel"
        rts
_b      #msg "back"
        rts

; Fire nel negozio sulla voce ui_lc: merce = compra, zaino = vende, equipaggiamento (posti 8-11) = ripara
sh_fire:
        lda ui_lc
        cmp #8
        bcc _s
        cmp #12
        bcs +
        tax
        jmp shop_repair
+       cmp #20
        bcc _b
_s      jmp shop_sell
_b      jmp shop_buy


; copia il pool in shp_stock e ne estrae shp_k a caso (Fisher-Yates parziale)
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
        cpx shp_k
        bcs +
        stx shp_k               ; meno oggetti di stock: tutti quelli che ci sono
+       lda shp_k
        bne +
        rts
+       lda #0
        sta shp_i
_i      lda shp_cnt
        sec
        sbc shp_i
        jsr rndrange
        clc
        adc shp_i
        tay                     ; j in [i, cnt)
        ldx shp_i
        lda shp_stock,x
        pha
        lda shp_stock,y
        sta shp_stock,x
        pla
        sta shp_stock,y
        inc shp_i
        lda shp_i
        cmp shp_k
        bcc _i
        rts

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
sn_smith .text "blacksmith", 0
sn_alch  .text "alchemist", 0

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

