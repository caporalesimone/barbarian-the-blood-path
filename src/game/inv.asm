; ===================================================================
;  inv.asm - (21/11, TODO D15) parte del segmento CORE (src/game/core.asm, RAM sotto il KERNAL da $E000): schermata
;  dell'inventario e descrizione degli oggetti (nome, icona, statistiche, valore). Spostate da ui.asm senza cambiarle.
;  Si chiamano solo dalle schermate (dopo ui_begin, che si assicura che CORE sia in memoria: core_need).
; ===================================================================
; A = id oggetto, ui_ib = prefisso (pergamene: quantita'), ui_is = suffisso: "[prefisso ]nome[ of suffisso]" tagliato e riempito
; a ui_w colonne (22/11: impostate dal chiamante, prima 16 fisse; 21/11 sera, fase 2b degli affissi). Azzera ui_ib, ui_is, ui_sk
ui_item:
        tax
        lda ui_col
        pha
        lda #UC_ITEM
        cpx #0
        bne +
        lda #UC_EMPTY
+       cpx #I_SCROLL           ; pila di pergamene: il bonus e' la quantita', non un affisso
        beq +
        ldy ui_ib
        bne _mg
        ldy ui_is
        beq +
_mg     jsr it_qcol             ; (fase 5) magico azzurro, maledetto grigio
+       ldy ui_fc
        beq _nfi
        lda ui_fc
_nfi    sta ui_col
        lda #0
        sta ui_nlen
        lda cidx                ; (22/11) colonne del nome in ui_w, sempre dal chiamante: liste sl_wd, riquadro 34, messaggio 16
        pha
        clc
        adc ui_w                ; 16 colonne (08/11: la colonna prima del nome e' l'icona della categoria, ui_cic)
        sta ui_lim
        cpx #I_SCROLL
        bne _px
        lda ui_ib
        beq _px
        cmp #10                 ; "3 portal scroll", "10 portal scroll" (08/11: senza la x, fino a 10)
        bcc +
        sbc #10
        pha
        lda #$31
        jsr ui_putc
        pla
+       ora #$30
        jsr ui_putc
        lda #$20
        jsr ui_putc
        lda #0                  ; (la quantita' non e' un prefisso)
        sta ui_ib
_px     jsr it_nm               ; (22/11, fase 6: in GAME per lo spazio di CORE) "[prefisso ]nome[ of suffisso]" o nome dell'unico
        lda #0
        sta ui_ib
        sta ui_is
        sta ui_sk
        pla
        clc
        adc ui_w
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

        .include "../out/work/afnames.asm"


iv_main:                        ; (21/11) ingresso da ui_inventory (ui.asm), che prima si assicura che CORE ci sia
        jsr sort_pack           ; (08/11) zaino sempre ordinato anche se il salvataggio e' di prima dell'ordinamento
        jsr ui_begin
        lda #<tt_bp
        ldx #>tt_bp
        ldy #0
        jsr ui_title
        lda #<iv_box
        ldx #>iv_box
        ldy #12
        jsr ui_boxes
        jsr ui_labels
        .byte 2,6
        #t5 " items "
        .byte 1,24
        #t5 "fire:use  del:drop  run/stop:back"
        .byte 2,1
        #t5 " "
        .byte $ff
        jsr ui_cname
        lda #$20
        jsr ui_putc
        lda #<iv_sg             ; lista: segmenti e righe
        ldx #>iv_sg
        ldy #0
        jsr sl_segs
        lda #IV_LY
        sta sl_y
        lda #IV_LH
        sta sl_h
        lda #0
        sta sl_s0
        sta sl_l
        sta sl_rv+1
        sta iv_mode
        jsr iv_std              ; riga 3 del riquadro: provenienza o confronto
        lda #3
        sta sl_sn
        lda #1
        sta sl_nl
        tax                     ; (X = 0 dopo il dex sotto)
        dex
        jsr sl_init
        lda #EQ_N+6             ; cursore sul primo posto dello zaino (indossati + riga + cintura 4 + riga)
        sta sl_cur
        lda #1
        sta sl_top
        jsr nav_init
        jsr iv_cur
_dyn    jsr inv_dynamic
_in     jsr sl_nav
        cmp #NAV_MOVE
        bne +
        jsr iv_cur
        jsr iv_sel
        jmp _in
+       cmp #NAV_BACK
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
; posto della voce del cursore -> ui_cur (la riga separatrice non e' mai sotto il cursore)
iv_cur  jsr sl_sel
        lda sl_sl
        sta ui_cur
        rts
; segmenti: indossati (EQ_N), cintura (4), zaino (8)
iv_sg   .byte 3, SK_EQ,0,EQ_N, SK_BELT|SK_SEP,0,4, SK_PACK|SK_SEP,0,PACK_N
iv_box  .byte 0,1,40,5, 0,6,40,12, 0,IV_SY,40,5
tt_bp   #t5 "backpack"


; valore di vendita: "val 1200o d135/178" (08/11: numero e poi la moneta)
it_val  #msg "val "             ; valore di vendita dell'oggetto ui_sel: prezzo >> SELL_SHIFT (20/11: un quarto,
        lda ui_sel              ; balance.yaml shop_rules.sell_divisor), allineato a sinistra, moneta; (fase 3) con gli affissi
        ldx ui_px
        ldy ui_sx
        jsr it_cost
        lda tmp0
        .rept SELL_SHIFT
        lsr tmp1
        ror a
        .endrept
        ldx tmp1
        jsr ui_n5l
        jmp ui_coin

; caratteristica principale dell'oggetto ui_sel (affissi ui_px, ui_sx), al massimo 9 caratteri:
; "dmg 2d6+3", "ac +5", "+2 str", "heal 50", "portal"
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
        jsr it_af               ; (21/11 sera) armatura / scudo: CA + affissi
        #msg "ac +"
        ldx ui_sel
        lda itval,x
        clc
        adc af_ac
        jmp ui_b3l
_rg     jsr it_af               ; anello: la prima caratteristica dei suoi affissi, "+N str"
        ldx #0
-       lda af_st,x
        bne +
        inx
        cpx #3
        bne -
        rts
+       stx tmp7
        pha
        #msg "+"
        pla
        jsr ui_b3l
        ldx tmp7
        inx
        stx ui_ib
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
_w      jsr it_af               ; arma: dadi + danno degli affissi (21/11 sera; prima la magia)
        lda af_dmg
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
        ldy ui_sel
        jsr req_chk             ; (21/11, O6) FOR o DES richiesta e non raggiunta: "str N" / "dex N" al posto del resto
        bcc _s0
        lda itreq,y
        bmi _dx
        #msg "str "
        jmp _rv
_dx     #msg "dex "
_rv     ldy ui_sel
        lda itreq,y
        and #$7f
        jmp ui_b3l
_s0     ldx ui_sel
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

; (21/11 sera) totali degli affissi dell'oggetto mostrato (prefisso tmp5, suffisso ui_sx) in af_att, af_dmg, af_ac, af_st
it_af:  jsr af_clr
        lda ui_px
        ldy ui_sx
        jmp af_pair

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


; statistiche (righe 2-4), lista, riquadro dell'oggetto
inv_dynamic:
        lda #2                  ; righe 2-4 pulite (i valori cambiano lunghezza)
        sta iv_r
_c      ldx #1
        ldy iv_r
        jsr ui_at
        lda #$20
        ldy #37
-       sta (cp),y
        dey
        bpl -
        inc iv_r
        lda iv_r
        cmp #5
        bne _c
        jsr ui_labels
        .byte 2,2
        #t5 "lvl"
        .byte 9,2
        #t5 "xp"
        .byte 2,3
        #t5 "hp"
        .byte 13,3
        #t5 "att +"
        .byte 21,3
        #t5 "ac"
        .byte 28,3
        #t5 "dmg"
        .byte 2,4
        #t5 "str"
        .byte 9,4
        #t5 "dex"
        .byte 16,4
        #t5 "con"
        .byte $ff
        #at 6,2
        lda c_lvl
        jsr ui_b3l
        #at 12,2                ; xp come nell'HUD (08/11): "9999/27k", da 10000 in migliaia (16 bit bassi)
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
        #at 26,2
        jsr ui_gold
        lda c_gold
        ldx c_gold+1
        jsr ui_n5l
        #at 33,2                ; chiavi
        jsr keys_n
        #at 5,3
        lda c_hp
        ldx c_hp+1
        jsr ui_n5l
        lda #$2f
        jsr ui_putc
        lda hpmax
        ldx hpmax+1
        jsr ui_n5l
        #at 18,3
        lda s_att
        jsr ui_b3l
        #at 24,3
        lda s_ac
        jsr ui_b3l
        #at 32,3
        lda s_dn
        ldx s_ds
        ldy s_dk
        jsr ui_dice
        #at 6,4
        lda s_str
        jsr ui_b3l
        #at 13,4
        lda s_dex
        jsr ui_b3l
        #at 20,4
        lda s_con
        jsr ui_b3l
        ldx #0
        jsr sl_draw
; riquadro dell'oggetto sotto il cursore (titolo = icona e nome; caratteristiche, valore e durabilita', confronto con
; l'indossato della stessa categoria o la provenienza)
iv_sel:
        ldx #1                  ; titolo: cornice pulita, poi " icona nome "
        ldy #IV_SY
        jsr ui_at
        lda ui_bc
        sta ui_col
        ldx #38
-       lda #BOX_H
        jsr ui_putc
        dex
        bne -
        lda #IV_SY+1            ; righe 19-21 pulite
        sta iv_r
_cl     ldx #1
        ldy iv_r
        jsr ui_at
        lda #$20
        ldy #37
-       sta (cp),y
        dey
        bpl -
        inc iv_r
        lda iv_r
        cmp #IV_SY+4
        bne _cl
        jsr sl_sel
        #at 2,IV_SY
        lda #$20
        jsr ui_putc
        lda ui_sel
        bne +
        rts
+       jsr ui_cic
        lda ui_px
        sta ui_ib
        lda ui_sx
        sta ui_is
        lda #34                 ; (fase 5, O8) nel titolo del riquadro il nome completo (fino a 34 colonne)
        sta ui_w
        lda ui_sel
        jsr ui_item
        jsr iv_trim             ; (ui_item riempie le colonne del nome: la cornice riprende dopo il nome)
        #at 2,IV_SY+1           ; caratteristiche
        jsr it_prim
        lda #$20
        jsr ui_putc
        jsr it_sec
        jsr it_pw               ; (fase 5) i poteri degli affissi che non stanno nei numeri
        #at 2,IV_SY+2           ; valore e durabilita' (negozi: solo la durabilita', il prezzo e' nella riga 3)
        lda iv_mode
        bne +
        jsr it_val
        inc cidx                ; due spazi
        inc cidx
+       lda ui_durm
        beq +
        #msg "dur "
        lda ui_dur
        jsr ui_b3l
        lda #$2f
        jsr ui_putc
        lda ui_durm
        jsr ui_b3l
+       #at 2,IV_SY+3           ; riga 3: routine della schermata (iv_std: provenienza o confronto; negozi: prezzi)
        jmp (iv_l3)
; riga 3 standard: indossato / in cintura, altrimenti (zaino, baule, merce) il confronto con l'indossato
iv_l3s  lda sl_mk
        beq _cmp
        cmp #CH_PACK
        beq _cmp
        tay
        ldx #ICOL_EQ
        lda #<tx_eqd
        cpy #CH_EQ
        beq +
        ldx #UC_LABEL
        lda #<tx_inb
+       pha
        tya
        jsr ui_icon
        pla
        ldx #>tx_eqd
        jmp ui_puts5            ; (21/11 sera) testi a 5 bit
_cmp    ldx ui_sel              ; zaino: "you: " + caratteristica principale dell'indossato della stessa categoria
        lda itcat,x
        cmp #CAT_RING+1
        bcs _x
        tax
        lda c_eq-1,x
        beq _x
        sta ui_sel
        lda c_eqb-1,x
        sta ui_px
        lda c_eqs-1,x
        sta ui_sx
        lda #UC_LABEL
        sta ui_col
        #msg "you: "
        jmp it_prim
_x      rts
; iv_l3 = iv_l3s (riga 3 standard)
iv_std  lda #<iv_l3s
        sta iv_l3
        lda #>iv_l3s
        sta iv_l3+1
        rts

; ---- schermate con due liste (21/11: negozi, locanda, baule del piano): riquadri, righe, disegno
; riquadri: lista 0 (righe 2-7), lista 1 (righe 10-16), oggetto (righe 18-22)
ls2_frame:
        lda #<ls2_box
        ldx #>ls2_box
        ldy #12
        jmp ui_boxes
ls2_box .byte 0,1,40,8, 0,9,40,9, 0,IV_SY,40,5
; segmenti gia' in sg_*, sl_s0/sl_sn impostati: righe delle due liste, cursore sulla prima voce della lista 0
ls2_init:
        ldx #3
-       lda ls2_yh,x
        sta sl_y,x
        dex
        bpl -
        lda #2
        sta sl_nl
        lda #0
        sta sl_l
        ldx #1
        jsr sl_init
        dex
        jmp sl_init
ls2_yh  .byte 2, 10, 6, 7               ; sl_y (2 liste), poi sl_h
        .cerror sl_h != sl_y+2, "sl_y e sl_h contigui"
; le due liste e il riquadro dell'oggetto sotto il cursore
ls2_draw:
        ldx #0
        jsr sl_draw
        inx
        jsr sl_draw
        jmp iv_sel

; la cornice del titolo riprende dopo il nome (gli spazi di riempimento di ui_item tornano BOX_H)
iv_trim:
        ldy cidx
_t      dey
        lda (cp),y
        cmp #$20
        bne _e
        lda #BOX_H
        sta (cp),y
        lda ui_bc
        sta (ccp),y
        bne _t
_e      iny
        lda #$20
        sta (cp),y
        rts
tx_eqd  #t5 " equipped"
tx_inb  #t5 " in belt"
        .cerror (>tx_eqd) != (>tx_inb), "tx_eqd e tx_inb nella stessa pagina"

