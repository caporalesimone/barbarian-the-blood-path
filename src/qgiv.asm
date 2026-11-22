; ===================================================================
;  qgiv.asm - (22/11, decisioni D3, D13, D18 del committente, docs/wiki/quests.md) modulo del villaggio delle quest: file
;  "qstg", letto a CORE_AT ($E000: copre il segmento CORE, che main_loop rilegge dopo; per questo ui_begin0) da q_talk (src/game/qengine.asm) quando si preme Fire accanto a un NPC fisso (q_k = il suo
;  numero k di villages.FIXED), eseguito; finisce con ui_exit. Assemblato a parte con le etichette del gioco (game.lbl).
;  1. Consegna (q_tin, src/menu/q_who.asm): il premio (oro, unico, oggetto magico, pozioni, gettone, gradino del borsello), se c'e' posto (Q12:
;     altrimenti la quest resta da riscuotere); obiettivo G: "give N gold?" e l'oro addosso. Poi il testo "done" e il premio.
;  2. Offerta (q_offer): la quest e' presa subito (Q11) e si mostrano testo, obiettivo e premio.
;  3. Altrimenti "nothing for you now".
;  Testi: file QTXc del capitolo (tools/build/gen_qdata.py, a 5 bit) letto a QTX ($EC00, come CSHEET: cs_ok si azzera).
;  Premi: qg_rw (out/work/qgiv_rw.inc), 4 byte per quest.
;  Da fare: abilita' sbloccate dalla catena (Q15), borsello variabile (oggi solo il gradino in q_flag bit 4-7), cintura a 8
;  (TODO F1), oggetto magico "qualsiasi" ($ff, passo 11), sblocco del capitolo alla consegna dei passi 3, 6, 9.
; ===================================================================
        .include "../out/work/game.lbl"
        .include "macros.inc"
        * = CORE_AT
        .enc "screen"
        jmp qgiv
QG_LN    = 12                    ; righe di testo visibili (righe 5..16)
QG_Y    = 5
QG_RY   = 19                    ; righe del premio (19..21)
qg_id   .byte 0                 ; QID - 1
qg_sl   .byte 0                 ; posto in q_side ($ff = catena)
qg_mode .byte 0                 ; 0 offerta, 1 consegna
qg_top  .byte 0                 ; prima riga visibile
qg_nl   .byte 0                 ; righe del testo
qg_l0   .word 0                 ; prima riga del testo
qg_tt   .word 0                 ; titolo
qg_gl   .word 0                 ; obiettivo (giallo)
qg_cf   .byte 0                 ; 1 = obiettivo con il contatore
qg_r0   .word 0                 ; righe del premio
qg_rn   .byte 0
qg_rw   .byte 0, 0, 0, 0        ; premio della quest
qg_n    .byte 0                 ; posti che servono (zaino) / pozioni (cintura)
qg_rwt
        .include "../out/work/qgiv_rw.inc"

qgiv:   lda q_k
        jsr MENU_QTIN
        bcc _of
        sta qg_id
        stx qg_sl
        lda #1
        sta qg_mode
        jsr qg_give
        bcc qg_text
        jmp qg_out
_of     lda q_k
        jsr MENU_QOFFER
        bcs +
        jmp qg_none
+       sta qg_id
        lda #0
        sta qg_mode
        jsr qg_take

; ------------------------------------------------------------------ testo della quest qg_id (file QTXc a QTX)
qg_text:
        lda #$51                ; "QTX" + capitolo (PETSCII maiuscolo, come i nomi di nm_tab)
        sta cmdbuf+3
        lda #$54
        sta cmdbuf+4
        lda #$58
        sta cmdbuf+5
        lda c_chap
        ora #$30
        sta cmdbuf+6
        lda #0
        sta cmdbuf+7
        lda #4
        sta nlen
        lda #1
        sta io_dir
        sta io_quiet
        lsr cs_ok               ; QTX copre il modulo CSHEET
        lda #<QTX
        sta ptr0
        lda #>QTX
        sta ptr0+1
        jsr load_raw
        lda #0
        sta io_quiet
        bcc +
        jmp qg_out
+       ldy #1                  ; la voce della quest: n, n x (QID-1, indirizzo)
        ldx QTX
-       lda QTX,y
        cmp qg_id
        beq +
        iny
        iny
        iny
        dex
        bne -
        jmp qg_out
+       lda QTX+1,y
        sta ptr2
        lda QTX+2,y
        sta ptr2+1
        jsr qg_here             ; titolo
        sta qg_tt
        stx qg_tt+1
        jsr qg_skip
        jsr qg_here             ; obiettivo
        sta qg_gl
        stx qg_gl+1
        jsr qg_skip
        jsr qg_byte
        sta qg_cf
        jsr qg_byte             ; testo dell'offerta
        ldx qg_mode
        bne +
        jsr qg_set
+       jsr qg_lines
        jsr qg_byte             ; testo della consegna
        ldx qg_mode
        beq +
        jsr qg_set
+       jsr qg_lines
        jsr qg_byte             ; premio
        sta qg_rn
        jsr qg_here
        sta qg_r0
        stx qg_r0+1
        lda #0
        sta qg_top
_dr     jsr qg_draw
_in     jsr ui_input
        lda joynew
        lsr
        bcs _up
        lsr
        bcs _dn
        jsr ui_fire
        bne _x
        lda keynew+7            ; RUN/STOP chiude
        and #$80
        beq _in
_x      jsr read_input
        jmp qg_out
_up     lda qg_top
        beq _in
        dec qg_top
        jmp _dr
_dn     lda qg_top
        clc
        adc #QG_LN
        cmp qg_nl
        bcs _in
        inc qg_top
        jmp _dr

; A = righe del blocco da mostrare: qg_nl, qg_l0 = qui
qg_set: sta qg_nl
        jsr qg_here
        sta qg_l0
        stx qg_l0+1
        lda qg_nl
        rts
; salta A righe da ptr2
qg_lines:
        tax
        beq +
-       txa
        pha
        jsr qg_skip
        pla
        tax
        dex
        bne -
+       rts
; ptr2 -> dopo la stringa a 5 bit
qg_skip:
        lda #0
        sta d5_n
-       jsr d5_get
        bne -
        rts
; A = byte a ptr2, ptr2 + 1
qg_byte:
        ldy #0
        lda (ptr2),y
        inc ptr2
        bne +
        inc ptr2+1
+       rts
qg_here:
        lda ptr2
        ldx ptr2+1
        rts

qg_draw:
        jsr ui_begin0          ; (non ui_begin: rileggerebbe CORE sopra il modulo)
        #ubox 0,1,40,3          ; titolo sulla cornice, obiettivo
        #ubox 0,4,40,QG_LN+2     ; testo
        #ubox 0,QG_RY-1,40,5    ; premio
        jsr ui_labels
        .byte 1,24
        #t5 "w/s:scroll  fire:ok"
        .byte $ff
        #at 2,1
        lda #$20
        jsr ui_putc
        lda qg_tt
        ldx qg_tt+1
        jsr ui_puts5
        lda #$20
        jsr ui_putc
        #at 2,2                 ; obiettivo (giallo) e contatore
        lda #UC_VALUE
        sta ui_col
        lda qg_gl
        ldx qg_gl+1
        jsr ui_puts5
        lda qg_cf
        beq +
        ldy qg_id
        lda qg_mode             ; contatore: 0 all'offerta, la quantita' alla consegna
        beq _z
        lda qt_n,y
_z      ldx #0
        jsr ui_n5l
        lda #"/"
        jsr ui_putc
        ldy qg_id
        lda qt_n,y
        ldx #0
        jsr ui_n5l
+       lda qg_r0               ; premio
        sta ptr2
        lda qg_r0+1
        sta ptr2+1
        lda #QG_RY
        sta tmp3
        ldx qg_rn
        jsr qg_show
        lda qg_top              ; testo dalla riga qg_top
        beq +
        #at 33,4
        #msg " up "
+       lda qg_top
        clc
        adc #QG_LN
        cmp qg_nl
        bcs +
        #at 32,QG_Y+QG_LN
        #msg " more "
+       lda qg_l0
        sta ptr2
        lda qg_l0+1
        sta ptr2+1
        lda qg_top
        jsr qg_lines
        lda #QG_Y
        sta tmp3
        lda qg_nl
        sec
        sbc qg_top
        cmp #QG_LN
        bcc +
        lda #QG_LN
+       tax
; X righe da ptr2 alle righe tmp3.. (colore: premio giallo, testo bianco)
qg_show:
        txa
        beq _r
-       stx tmp4
        ldx #2
        ldy tmp3
        jsr ui_at
        lda #UC_ITEM
        ldy tmp3
        cpy #QG_RY
        bcc +
        lda #UC_VALUE
+       sta ui_col
        jsr ui_p5
        inc tmp3
        ldx tmp4
        dex
        bne -
_r      rts

; ------------------------------------------------------------------ niente da dare o da ritirare
qg_none:
        jsr ui_begin0          ; (non ui_begin: rileggerebbe CORE sopra il modulo)
        #ubox 0,9,40,5
        #at 4,11
        #msg "nothing for you now."
        jsr ui_wait_fire
        jmp qg_out

; messaggio A/X (codici schermo, 0 finale) in un riquadro, poi Fire
qg_say: pha
        txa
        pha
        jsr ui_begin0          ; (non ui_begin: rileggerebbe CORE sopra il modulo)
        #ubox 0,9,40,5
        #at 4,11
        pla
        tax
        pla
        jsr ui_puts
        jmp ui_wait_fire

; di nuovo nel gioco: la barra in alto si ricostruisce (come la pagina Q, src/qpage.asm)
qg_out: jsr MENU_QMARK          ; (D12) segni di nuovo
        lda #0
        sta bt_who
        sta bar_lab
        sta bar_on
        lda #$ff
        sta lc_x
        jmp ui_exit

; ------------------------------------------------------------------ presa (Q11)
qg_take:
        ldy qg_id
        cpy #QT_CHAIN
        bcs _sd
        lda q_flag              ; catena: preso, contatore a 0 (il gradino del borsello resta)
        and #$f0
        ora #1
        sta q_flag
        lda #0
        sta q_cnt
        rts
_sd     ldx #0                  ; accessoria: il primo posto libero di q_side (q_offer: c'e')
-       lda q_side,x
        beq +
        inx
        inx
        cpx #8
        bne -
        rts
+       tya
        sec
        sbc #QT_CHAIN-1
        sta q_side,x
        lda #0
        sta q_side+1,x
        rts

; ------------------------------------------------------------------ consegna: C = 1 se non si e' consegnato
qg_give:
        lda qg_id               ; premio della quest: 4 byte
        asl
        asl
        tay
        ldx #0
-       lda qg_rwt,y
        sta qg_rw,x
        iny
        inx
        cpx #4
        bne -
        ldy qg_id               ; obiettivo G non ancora pagato: "give N gold?"
        lda qt_ty,y
        and #$0f
        cmp #QG_G
        bne _sp
        ldx qg_sl
        lda q_side,x
        bmi _sp
        jsr ui_begin0          ; (non ui_begin: rileggerebbe CORE sopra il modulo)
        #ubox 0,9,40,5
        #at 4,11
        #msg "give "
        ldy qg_id
        lda qt_p1,y
        ldx qt_p2,y
        jsr ui_n5l
        #msg " gold?"
        jsr ui_yesno
        bcs +
        rts                     ; (C = 1: no)
+       ldy qg_id
        lda c_gold
        sec
        sbc qt_p1,y
        tax
        lda c_gold+1
        sbc qt_p2,y
        bcs +
        lda #<ms_gold
        ldx #>ms_gold
        jsr qg_say
        sec
        rts
+       sta c_gold+1
        stx c_gold
        lda #1
        sta hud_dirty
_sp     lda #0                  ; posto: zaino per unico e oggetto, cintura per le pozioni (Q12)
        sta qg_n
        lda qg_rw+1
        beq +
        inc qg_n
+       lda qg_rw+2
        beq +
        inc qg_n
+       ldx #PACK_N-1
-       lda c_pack,x
        bne +
        dec qg_n
+       dex
        bpl -
        lda qg_n
        bmi +
        bne _full
+       lda qg_rw+3             ; pozioni: posti liberi della cintura
        lsr
        lsr
        and #7
        sta qg_n
        ldx #3
-       lda c_beltt,x
        bne +
        dec qg_n
+       dex
        bpl -
        lda qg_n
        bmi _ok
        beq _ok
_full   lda #<ms_room
        ldx #>ms_room
        jsr qg_say
        sec
        rts
_ok     lda qg_rw               ; oro / 10 -> x 10
        sta tmp0
        lda #0
        sta tmp1
        asl tmp0
        rol tmp1
        lda tmp0
        ldx tmp1                ; 2g
        asl tmp0
        rol tmp1
        asl tmp0
        rol tmp1                ; 8g
        clc
        adc tmp0
        pha
        txa
        adc tmp1
        tax
        pla
        jsr add_gold16
        lda qg_rw+1             ; unico
        beq +
        sta ap_s
        and #$7f
        tax
        lda un_base,x
        jsr qg_item
+       lda qg_rw+2             ; oggetto magico della base (livello: boss del capitolo)
        beq _pt
        cmp #$ff
        beq _pt                 ; (da fare: "qualsiasi", passo 11)
        tay
        lda c_chap
        asl
        asl
        adc c_chap
        sta af_l
        sta af_tt
        lda #1
        sta af_m
        jsr af_gen
        lda af_id
        jsr qg_item0
_pt     lda qg_rw+3             ; pozioni
        and #3
        beq _rs
        clc
        adc #I_POTR-1
        sta tmp5
        lda qg_rw+3
        lsr
        lsr
        and #7
        sta qg_n
-       lda #0
        sta ap_b
        lda tmp5
        jsr give_item
        dec qg_n
        bne -
_rs     lda qg_rw+3
        and #$20
        beq +
        jsr resp_add
+       lda qg_rw+3             ; gradino del borsello (q_flag bit 4-7)
        and #$40
        beq +
        lda q_flag
        clc
        adc #$10
        sta q_flag
+       ldy qg_id               ; stato
        cpy #QT_CHAIN
        bcs _sd
        inc q_step
        lda q_flag
        and #$f0
        sta q_flag
        lda #0
        sta q_cnt
        beq _ex
_sd     tya                     ; accessoria: bit id-1 in q_sdone, posto libero
        sec
        sbc #QT_CHAIN
        tax
        and #7
        tay
        lda bitmask,y
        cpx #8
        bcs +
        ora q_sdone
        sta q_sdone
        bcc ++
+       ora q_sdone+1
        sta q_sdone+1
+       ldx qg_sl
        lda #0
        sta q_side,x
        sta q_side+1,x
_ex     lda #SFX_LEVEL
        jsr sfx_play
        lda #1
        sta hud_dirty
        clc
        rts

; A = id dell'oggetto, ap_s gia' messo: prefisso 0, durabilita' da generare
qg_item:
        ldx #0
        stx ap_b
qg_item0:
        ldx #0
        stx ap_d
        stx ap_m
        jmp give_item

ms_gold .text "you do not have enough gold.", 0
ms_room .text "no room in your pack or belt.", 0

qg_end
        .cerror qg_end > QTX, "modulo QGIV sopra i testi del capitolo (QTX)"
