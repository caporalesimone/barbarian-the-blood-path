; ===================================================================
;  qpage.asm - (17/11, concept; 18/11 elenco e dettaglio, richiesta del committente) pagina delle quest: modulo su file, in
;  testa al file QST0 (tools/build/gen_quests.py: codice + indice), caricato a QBUF (= SCR_B) da ui_quest (src/game/quest.asm)
;  ed eseguito; finisce con ui_exit. Assemblato a parte con le etichette del gioco (out/work/game.lbl), come il LOBBY.
;  Elenco: le quest prese (bit di c_qst), titolo e capitolo; Fire = dettaglio. Dettaglio: titolo (sulla cornice), capitolo,
;  stato (SEGNAPOSTO giallo, in testa al testo: cosa mostrera' lo decide il quest system, TODO H1), testo, premio; il testo
;  (file QSTn, letto a QTXT senza schermata di attesa) scorre con W/S o il joystick se non sta nel riquadro.
;  q_open <> 0 (Fire accanto a chi da' una quest): si apre subito il dettaglio di quella quest; si torna all'elenco.
;  Indice (dopo il codice, qp_index): per ogni quest 1..Q_N capitolo (1 B) e titolo (0 finale).
;  File QSTn: premio 0, righe dello stato (1 B), righe (ciascuna 0 finale) dello stato e del testo, $FF.
; ===================================================================
        .include "../out/work/game.lbl"
        .include "macros.inc"
        * = QBUF
        .enc "screen"
        jmp qpage
QV_N    = 14                    ; righe di testo visibili nel riquadro del dettaglio (righe 5..18)
QV_Y    = 5
QL_Y    = 5                     ; prima riga dell'elenco (una voce ogni 2 righe)
tt_q    #t5 "quests"
qp_lst  .fill 8                 ; quest dell'elenco (numeri)
qp_sel  .byte 0                 ; voce dell'elenco scelta (si ritrova tornando dal dettaglio)
qd_id   .byte 0                 ; quest del dettaglio
qd_ns   .byte 0                 ; righe dello stato (gialle)
qd_nl   .byte 0                 ; righe in tutto (stato + testo)
qd_top  .byte 0                 ; prima riga visibile
qd_l0   .word 0                 ; prima riga (stato) nel file QSTn

qpage:  lda q_open
        beq ql_list
        jsr qd_show             ; Fire accanto a chi da' la quest: subito il dettaglio, poi l'elenco
; ------------------------------------------------------------------ elenco delle quest prese
ql_list:
        ldx #0
        ldy #1
-       lda bitmask-1,y
        and c_qst
        beq +
        tya
        sta qp_lst,x
        inx
+       iny
        cpy #Q_N+1
        bne -
        stx ui_n
        jsr nav_init
        lda qp_sel
        cmp ui_n
        bcc +
        lda #0
+       sta ui_cur
        jsr nav_sync
        jsr ui_begin
        lda #<tt_q
        ldx #>tt_q
        ldy #0
        jsr ui_title
        jsr nav_help
        lda ui_n
        bne _full
        #ubox 0,8,40,5
        #at 4,10
        #msg "talk to the villagers"
        jmp _in
_full   #ubox 0,3,40,18
        ldx #0
_ln     stx tmp3                ; voce X: titolo e capitolo
        ldx #5
        jsr ql_at
        lda qp_lst,x
        jsr qi_find             ; ptr1 = capitolo, titolo
        lda #UC_ITEM
        sta ui_col
        jsr qi_title
        ldx #31
        jsr ql_at
        #msg "ch. "
        ldy #0
        jsr qi_chap
        ldx tmp3
        inx
        cpx ui_n
        bne _ln
_dr     ldx ui_n                ; '>' sulla voce del cursore
        dex
_mk     stx tmp3
        ldx #3
        jsr ql_at
        jsr ui_mark
        dex
        bpl _mk
_in     jsr ui_nav
        cmp #NAV_MOVE
        beq _dr
        cmp #NAV_BACK
        beq qp_out
        cmp #NAV_FIRE
        bne +
        ldx ui_cur
        stx qp_sel
        lda qp_lst,x
        jsr qd_show
        jmp ql_list
+       lda keynew+7            ; Q chiude come RUN/STOP
        and #$40
        beq _in
; di nuovo nel gioco: la barra in alto si ricostruisce (il testo della quest ha coperto il suo set B, QTXT), come la minimappa
qp_out  lda #0
        sta bt_who
        sta bar_lab
        sta bar_on
        lda #$ff
        sta lc_x
        jmp ui_exit

; posizione (X, riga della voce tmp3 dell'elenco); X = tmp3 all'uscita
ql_at   lda tmp3
        asl
        adc #QL_Y
        tay
        jsr ui_at
        ldx tmp3
        rts

; A = quest -> ptr1 = la sua voce nell'indice (capitolo, titolo)
qi_find:
        tax
        lda #<qp_index
        sta ptr1
        lda #>qp_index
        sta ptr1+1
-       dex
        beq _r
        ldy #1                  ; dopo il capitolo, il titolo fino allo 0
-       lda (ptr1),y
        iny
        cmp #0
        bne -
        tya
        clc
        adc ptr1
        sta ptr1
        bcc --
        inc ptr1+1
        bne --
_r      rts

; titolo della voce ptr1 alla posizione corrente
qi_title:
        lda ptr1
        clc
        adc #1
        pha
        lda ptr1+1
        adc #0
        tax
        pla
        jmp ui_puts

; capitolo della voce ptr1 (Y = 0), in giallo
qi_chap lda #UC_VALUE
        sta ui_col
        lda (ptr1),y
        ora #$30
        jmp ui_putc

; ------------------------------------------------------------------ dettaglio della quest A
qd_show:
        sta qd_id
        ldy #nm_qst-nm_tab      ; "QST" + cifra: il testo a QTXT, senza schermata di attesa
        jsr set_name4
        lda qd_id
        ora #$30
        sta cmdbuf+6
        lda #1
        sta io_quiet
        lda #<QTXT
        sta ptr0
        lda #>QTXT
        sta ptr0+1
        jsr load_raw
        lda #0
        sta io_quiet
        bcc +
        rts                     ; file non letto: si resta nell'elenco
+       lda #<QTXT              ; premio, poi le righe
        sta ptr1
        lda #>QTXT
        sta ptr1+1
        jsr qd_skip
        ldy #0
        lda (ptr1),y
        sta qd_ns
        inc ptr1
        bne +
        inc ptr1+1
+       lda ptr1
        sta qd_l0
        lda ptr1+1
        sta qd_l0+1
        ldx #0                  ; righe in tutto
-       ldy #0
        lda (ptr1),y
        cmp #$ff
        beq +
        jsr qd_skip
        inx
        bne -
+       stx qd_nl
        lda #0
        sta qd_top
_dr     jsr qd_draw
_in     jsr ui_input
        lda joynew
        lsr
        bcs _up
        lsr
        bcs _dn
        jsr ui_fire
        bne _x
        lda keynew+7            ; RUN/STOP o Q: all'elenco
        and #$c0
        beq _in
_x      jsr read_input          ; il tasto che chiude non vale anche nell'elenco
        rts
_up     lda qd_top
        beq _in
        dec qd_top
        jmp _dr
_dn     lda qd_top
        clc
        adc #QV_N
        cmp qd_nl
        bcs _in
        inc qd_top
        jmp _dr

; ptr1 -> dopo la stringa (0 finale)
qd_skip:
        ldy #0
-       lda (ptr1),y
        iny
        cmp #0
        bne -
        tya
        clc
        adc ptr1
        sta ptr1
        bcc +
        inc ptr1+1
+       rts

qd_draw:
        jsr ui_begin
        #ubox 0,1,40,3          ; titolo sulla cornice, capitolo
        #ubox 0,4,40,QV_N+2     ; stato e testo
        #ubox 0,QV_Y+QV_N+1,40,3    ; premio
        jsr ui_labels
        .byte 2,QV_Y+QV_N+1
        #t5 " reward "
        .byte 2,2
        #t5 "chapter "
        .byte 1,24
        #t5 "w/s:scroll  run/stop:back"
        .byte $ff
        lda qd_id               ; capitolo e titolo dall'indice
        jsr qi_find
        #at 10,2
        ldy #0
        jsr qi_chap
        #at 2,1
        lda #$20
        jsr ui_putc
        jsr qi_title
        lda #$20
        jsr ui_putc
        #at 3,QV_Y+QV_N+2       ; premio (la prima stringa del file)
        lda #UC_VALUE
        sta ui_col
        lda #<QTXT
        ldx #>QTXT
        jsr ui_puts
        lda qd_top              ; righe qd_top.. : la prima visibile
        beq +
        #at 33,4
        #msg " up "
+       lda qd_top
        clc
        adc #QV_N
        cmp qd_nl
        bcs +
        #at 32,QV_Y+QV_N
        #msg " more "
+       lda qd_l0
        sta ptr1
        lda qd_l0+1
        sta ptr1+1
        ldx #0                  ; X = riga del file
-       cpx qd_top
        beq _v
        jsr qd_skip
        inx
        bne -
_v      lda #QV_Y
        sta tmp3
_l      ldy #0
        lda (ptr1),y
        cmp #$ff
        beq _r
        stx tmp4
        ldx #2
        ldy tmp3
        jsr ui_at
        lda #UC_ITEM            ; righe dello stato: gialle (segnaposto)
        ldx tmp4
        cpx qd_ns
        bcs +
        lda #UC_VALUE
+       sta ui_col
        lda ptr1
        ldx ptr1+1
        jsr ui_puts
        jsr qd_skip
        ldx tmp4
        inx
        inc tmp3
        lda tmp3
        cmp #QV_Y+QV_N
        bne _l
_r      rts

qp_index                        ; indice delle quest (gen_quests.py)
