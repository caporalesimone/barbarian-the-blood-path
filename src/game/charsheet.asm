; ===================================================================
;  charsheet.asm - schermata del personaggio (tasto C), 11/11, branch feature/stat-points
;  Il passaggio di livello non alza piu' le caratteristiche: da' punti statistica (pl_pts, rules.yaml
;  player.stat_points) da spendere qui su FOR, DES, COS (+1 al valore per punto; c_sadd). Voci: le tre
;  caratteristiche (A/D o -/+ o Fire: un punto in meno / in piu', in attesa in cs_pend), confirm (i punti in
;  attesa diventano spesi), reset (azzera quelli in attesa), respec (consuma un gettone c_resp: tutti i punti
;  spesi tornano da spendere). All'uscita (RUN/STOP) i punti in attesa si confermano e, se e' cambiato qualcosa,
;  si salva (gm_save: piano + eroe). Statistiche derivate (vita, ATT, CA, danno) mostrate con i punti in attesa.
; ===================================================================
        .enc "screen"
CS_N     = 6                    ; voci: 0..2 FOR DES COS, 3 confirm, 4 reset, 5 respec
UC_PEND  = 5                    ; punti in attesa: verdi

tt_cs   .text "character", 0
; (12/11, committente) senza punti da spendere niente voci: si legge e si esce con RUN/STOP ("no points to spend").
; Eccezione mia (da confermare): con un gettone respec resta la sola voce "respec" (cs_mode 1), altrimenti il respec
; non si potrebbe mai usare quando i punti sono tutti spesi. cs_mode: 0 tutte le voci, 1 solo respec, 2 nessuna.
ui_charsheet:
        lda #0
        ldx #2
-       sta cs_pend,x
        dex
        bpl -
        sta cs_mode
        lda #CS_N
        sta ui_n
        jsr pts_avail
        bne _ni
        lda #0                  ; nessuna voce...
        sta ui_n
        lda #2
        sta cs_mode
        lda c_resp              ; ...o solo respec
        beq _ni
        lda #1
        sta cs_mode
        sta ui_n
_ni     jsr nav_init
_scr    jsr ui_begin
        lda #<tt_cs
        ldx #>tt_cs
        ldy #0
        jsr ui_title
        #ubox 0,1,40,6
        #ubox 0,7,40,8
        #ubox 0,15,40,6
        jsr ui_labels
        .byte 2,7
        .text " stats "
        .byte 0,2,15
        .text " actions "
        .byte 0,2,2
        .text "lvl"
        .byte 0,15,2
        .text "respec tokens"
        .byte 0,2,3
        .text "hp"
        .byte 0,15,3
        .text "att +"
        .byte 0,29,3
        .text "ac"
        .byte 0,2,4
        .text "dmg"
        .byte 0,4,12
        .text "points to spend"
        .byte 0,$ff
        lda cs_mode
        bne _lm
        jsr ui_labels
        .byte 4,16
        .text "confirm"
        .byte 0,4,17
        .text "reset"
        .byte 0,4,18
        .text "respec"
        .byte 0,1,24
        .text "a/d -/+:points fire:ok run/stop:back"
        .byte 0,$ff
        jmp _lx
_lm     jsr ui_labels
        .byte 4,18
        .text "no points to spend."
        .byte 0,$ff
        lda cs_mode
        cmp #1
        bne _lv
        jsr ui_labels
        .byte 4,16
        .text "respec"
        .byte 0,1,24
        .text "fire:ok run/stop:back"
        .byte 0,$ff
        jmp _lx
_lv     jsr ui_labels
        .byte 1,24
        .text "run/stop:back"
        .byte 0,$ff
_lx
        #at 2,1                 ; nome sulla cornice (come l'inventario)
        lda #$20
        jsr ui_putc
        jsr ui_cname
        lda #$20
        jsr ui_putc
.if TESTUI == 39                ; (screenshot) punti tutti da spendere, uno in attesa su FOR, 2 gettoni respec
        lda #0
        sta c_sadd
        sta c_sadd+1
        sta c_sadd+2
        inc cs_pend
        lda #2
        sta c_resp
.endif
_dr     jsr cs_draw
.if NOKEYS
_hg     jmp _hg
.endif
_in     jsr ui_nav
        cmp #NAV_MOVE
        beq _dr
        cmp #NAV_BACK
        bne +
        jmp _back
+       ldx cs_mode             ; (12/11) senza voci: solo RUN/STOP
        cpx #2
        beq _in
        cmp #NAV_FIRE
        beq _fire
        lda cs_mode             ; solo respec: niente punti da spostare
        bne _in
        lda ui_cur              ; sinistra / destra (A/D) e i tasti - e + sulle caratteristiche
        cmp #3
        bcs _in
        tax
        lda joynew
        and #8
        bne _plus
        lda keynew+5
        and #$01                ; '+'
        bne _plus
        lda joynew
        and #4
        bne _minus
        lda keynew+5
        and #$08                ; '-'
        beq _in
_minus  lda cs_pend,x
        beq _no
        dec cs_pend,x
        jmp _ok
_plus   stx tmp3
        jsr pts_avail
        beq _no
        ldx tmp3
        inc cs_pend,x
_ok     jsr msg23
        lda #SFX_PICK
        jsr sfx_play
        jmp _dr
_no     jsr msg23
        #at 1,23
        #msg "no points."
        jmp _in
_fire   lda cs_mode
        bne _rsp                ; (12/11) solo respec
        ldx ui_cur
        cpx #3
        bcc _plus
        bne +
        jmp _conf
+       cpx #4
        bne _rsp
        jmp _reset
_rsp    lda c_resp              ; respec: un gettone, tutti i punti spesi tornano da spendere
        bne +
        jsr msg23
        #at 1,23
        #msg "no respec tokens."
        jmp _in
+       jsr msg23
        #at 1,23
        #msg "use a respec token?"
        jsr ui_yesno
        php
        jsr msg23
        plp
        bcs +
        jmp _dr
+       dec c_resp
        lda #0
        ldx #2
-       sta c_sadd,x
        sta cs_pend,x
        dex
        bpl -
        jsr cs_upd
        lda #SFX_PICK
        jsr sfx_play
        jmp ui_charsheet        ; (12/11) di nuovo da capo: ora ci sono punti, tutte le voci
_reset  lda #0
        ldx #2
-       sta cs_pend,x
        dex
        bpl -
        jmp _ok
_conf   jsr cs_apply
        jmp _ok
_back  jsr cs_apply            ; uscita: i punti in attesa si confermano (11/11 sera: niente salvataggio, lo fa "save game")
        jmp ui_exit

; punti in attesa -> spesi (c_sadd)
cs_apply:
        lda #0
        sta tmp4
        ldx #2
-       lda cs_pend,x
        beq +
        clc
        adc c_sadd,x
        sta c_sadd,x
        lda #0
        sta cs_pend,x
        inc tmp4
+       dex
        bpl -
        lda tmp4
        bne cs_upd
        rts
; statistiche ricalcolate, vita attuale al massimo nuovo se lo supera
cs_upd: jsr recalc_stats
        lda hpmax
        cmp c_hp
        lda hpmax+1
        sbc c_hp+1
        bcs +
        jmp hp_full
+       rts

; valori della schermata (con i punti in attesa: statistiche derivate calcolate come se fossero gia' spesi)
cs_draw:
        ldx #2
-       lda c_sadd,x            ; anteprima: c_sadd += cs_pend
        clc
        adc cs_pend,x
        sta c_sadd,x
        dex
        bpl -
        jsr recalc_stats
        ldx #2
-       lda c_sadd,x
        sec
        sbc cs_pend,x
        sta c_sadd,x
        dex
        bpl -
        #at 6,2
        lda c_lvl
        jsr ui_b3
        #at 29,2
        lda c_resp
        jsr ui_b3
        #at 5,3
        lda hpmax
        ldx hpmax+1
        jsr ui_n5l
        jsr cs_sp2
        #at 20,3
        lda s_att
        jsr ui_b3l
        lda #$20
        jsr ui_putc
        #at 32,3
        lda s_ac
        jsr ui_b3
        #at 6,4
        lda s_dn
        ldx s_ds
        ldy s_dk
        jsr ui_dice
        jsr cs_sp2
        ldx #0                  ; caratteristiche: righe 9..11
_s      stx tmp3
        txa
        clc
        adc #9
        tay
        ldx #2
        jsr ui_at
        lda #$20                ; (12/11) cursore sulle caratteristiche solo con tutte le voci
        ldx cs_mode
        bne +
        ldx tmp3
        jsr ui_mark
        jmp ++
+       jsr ui_putc
+       ldx tmp3
        lda cs_nm_lo,x          ; "str" / "dex" / "con"
        pha
        lda cs_nm_hi,x
        tax
        pla
        jsr ui_puts
        jsr cs_sp2
        ldx tmp3
        lda s_str,x             ; valore (anello compreso, punti in attesa compresi)
        jsr ui_b3
        jsr cs_sp2
        ldx tmp3
        lda cs_pend,x           ; punti in attesa: "+N" verde
        beq _np
        pha
        lda #$2b
        jsr ui_putc
        lda #UC_PEND
        sta ui_fc
        pla
        jsr ui_b3l
        lda #0
        sta ui_fc
_np     lda #$20                ; spazi fino alla colonna del modificatore (cidx 16 dalla colonna 2)
        jsr ui_putc
        lda cidx
        cmp #16
        bcc _np
_md     #msg "mod +"
        ldx tmp3
        lda s_str,x
        jsr modv
        jsr ui_b3l
        lda #$20
        jsr ui_putc
        ldx tmp3
        inx
        cpx #3
        beq +
        jmp _s
+       #at 20,12               ; punti da spendere
        jsr pts_avail
        jsr ui_b3
        lda cs_mode             ; (12/11) solo respec: cursore (voce 0) nella riga 16
        beq _a0
        cmp #1
        bne _ax
        #at 2,16
        ldx #0
        jsr ui_mark
_ax     jmp recalc_stats
_a0     ldx #3                  ; azioni: cursore nelle righe 16..18
_a      stx tmp3
        txa
        clc
        adc #13
        tay
        ldx #2
        jsr ui_at
        ldx tmp3
        jsr ui_mark
        ldx tmp3
        inx
        cpx #CS_N
        bne _a
        jmp recalc_stats        ; statistiche vere (senza i punti in attesa)

cs_mode .byte 0
cs_sp2  lda #$20                ; due spazi (ui_putc non conserva A)
        jsr ui_putc
        lda #$20
        jmp ui_putc

cs_nm_lo .byte <cs_str, <cs_dex, <cs_con
cs_nm_hi .byte >cs_str, >cs_dex, >cs_con
cs_str  .text "str", 0
cs_dex  .text "dex", 0
cs_con  .text "con", 0
        .enc "none"
