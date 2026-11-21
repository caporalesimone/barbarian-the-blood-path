; ===================================================================
;  charsheet.asm - schermata del personaggio (tasto C), 11/11; rifatta il 15/11 (TODO Z5, richiesta del committente)
;  Il passaggio di livello non alza piu' le caratteristiche: da' punti statistica (pl_pts, rules.yaml
;  player.stat_points) da spendere qui su FOR, DES, COS (+1 al valore per punto; c_sadd). Voci: le tre
;  caratteristiche (A/D o -/+ o Fire: un punto in meno / in piu', in attesa in cs_pend), confirm (domanda "spend N
;  points for good?": si' = i punti in attesa diventano spesi), undo (toglie tutti quelli in attesa), respec (solo con
;  gettoni c_resp: uno consumato, tutti i punti spesi tornano da spendere). I punti in attesa si spostano liberamente
;  fino alla conferma; RUN/STOP (o di nuovo C, 17/11) con punti in attesa chiede "spend N points before leaving?" (si' = spesi, no = si esce
;  e tornano da spendere). Nessun salvataggio (lo fa "save game"). Statistiche derivate (vita massima, ATT, CA, danno)
;  e caratteristiche: valore attuale e, se i punti in attesa lo cambiano, "-> nuovo" in verde. Senza gettoni respec
;  la schermata non dice nulla del respec.
; ===================================================================
        .enc "screen"
CS_N     = 6                    ; voci: 0..2 FOR DES COS, 3 confirm, 4 undo, 5 respec (solo con gettoni)
UC_PEND  = 5                    ; punti in attesa e valori nuovi: verdi
        .cerror s_dk - hpmax != 11 || s_str - hpmax != 2, "cs_nv: blocco hpmax..s_dk cambiato"

tt_cs   #t5 "character"
; (12/11, committente) senza punti da spendere niente voci: si legge e si esce con RUN/STOP ("no points to spend").
; Eccezione mia (da confermare): con un gettone respec resta la sola voce "respec" (cs_mode 1), altrimenti il respec
; non si potrebbe mai usare quando i punti sono tutti spesi. cs_mode: 0 tutte le voci, 1 solo respec, 2 nessuna.
ui_charsheet:
        jsr cs_zero
        sta cs_mode             ; (A = 0)
.if TESTUI == 39                ; (screenshot, TESTCL=9: 4 punti) nessun punto speso, 2 in attesa su FOR e 1 su COS,
        ldx #2                  ; 2 gettoni respec
-       sta c_sadd,x
        dex
        bpl -
        lda #2
        sta cs_pend
        sta c_resp
        inc cs_pend+2
.endif
.if TESTUI == 40                ; (screenshot, TESTCL=7: punti tutti spesi) nessun gettone respec
        sta c_resp
.endif
        ldx #CS_N-1             ; respec solo con gettoni
        lda c_resp
        beq +
        inx
+       stx ui_n
        jsr pts_avail
        bne _ni
        sta ui_n                ; (A = 0) nessuna voce...
        lda #2
        sta cs_mode
        lda c_resp              ; ...o solo respec
        beq _ni
        dec cs_mode
        inc ui_n
_ni     jsr nav_init
        jsr ui_begin
        lda #<tt_cs
        ldx #>tt_cs
        ldy #0
        jsr ui_title
        #ubox 0,1,40,7
        #ubox 0,8,40,8
        jsr ui_labels
        .byte 2,8
        #t5 " stats "
        .byte 2,2
        #t5 "lvl"
        .byte 2,3
        #t5 "hp"
        .byte 2,4
        #t5 "att"
        .byte 2,5
        #t5 "ac"
        .byte 2,6
        #t5 "dmg"
        .byte $ff
        #at 2,1                 ; nome sulla cornice (come l'inventario)
        lda #$20
        jsr ui_putc
        jsr ui_cname
        lda #$20
        jsr ui_putc
        #at 7,2
        lda c_lvl
        jsr ui_b3l
        lda c_resp              ; gettoni respec: solo se ce ne sono (Z5)
        beq _nr
        jsr ui_labels
        .byte 22,2
        #t5 "respec tokens"
        .byte $ff
        #at 36,2
        lda c_resp
        jsr ui_b3
_nr     lda cs_mode
        cmp #2
        beq _nb
        #ubox 0,16,40,5
        jsr ui_labels
        .byte 2,16
        #t5 " actions "
        .byte $ff
        lda c_resp
        beq _nb
        ldy #19                 ; "respec": terza azione, o la sola (riga 17) senza punti
        lda cs_mode
        beq +
        ldy #17
+       ldx #4
        jsr ui_at
        #msg "respec"
_nb     lda cs_mode
        bne _lm
        jsr ui_labels
        .byte 4,17
        #t5 "confirm"
        .byte 4,18
        #t5 "undo"
        .byte 3,13
        #t5 "points to spend"
        .byte $ff
        #at 1,24
        #msg "a/d -/+:points "
        jmp _kf
_lm     jsr ui_labels
        .byte 3,13
        #t5 "no points to spend."
        .byte $ff
        ldx c_lvl               ; prossimo punto: primo livello con pl_pts piu' alto (niente oltre PL_MAXLVL)
        cpx #PL_MAXLVL
        bcs _kk
        lda pl_pts,x
-       inx
        cmp pl_pts,x
        bne +
        cpx #PL_MAXLVL
        bcc -
        bcs _kk
+       stx tmp3
        #at 3,14
        #msg "next point at level "
        lda tmp3
        jsr ui_b3l
_kk     #at 1,24
        lda cs_mode
        cmp #2
        beq _kb
_kf     #msg "fire:ok "
_kb     #msg "run/stop:back"
_dr     jsr cs_draw
.if NOKEYS
_hg     jmp _hg
.endif
_in     jsr ui_nav
        pha                     ; (17/11, committente) C chiude come RUN/STOP (in basso resta scritto solo run/stop)
        lda keynew+2
        and #$10
        beq +
        pla
        jmp _back
+       pla
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
_minus  lda cs_pend,x           ; si toglie solo un punto in attesa: quelli spesi restano (si cambiano col respec)
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
_no     jsr msg23           ; (msg23 lascia la scrittura in riga 23, colonna 1)
        #msg "no points."
        jmp _in
_fire   lda cs_mode
        bne _rsp                ; (12/11) solo respec
        ldx ui_cur
        cpx #3
        bcc _plus
        beq _conf
        cpx #4
        bne _rsp
        jsr cs_zero             ; undo: tutti i punti in attesa tornano da spendere
        jmp _ok
_rsp    jsr msg23               ; respec (voce presente solo con gettoni): uno consumato, tutti i punti spesi tornano
        #msg "use a respec token?"
        jsr ui_yesno
        php
        jsr msg23
        plp
        bcs +
_jdr    jmp _dr
+       dec c_resp
        lda #0
        ldx #2
-       sta c_sadd,x
        dex
        bpl -
        jsr recalc_stats        ; (la vita attuale resta entro il massimo: hp_cap)
        jmp _done               ; di nuovo da capo: ora ci sono punti, tutte le voci
_conf   jsr cs_psum             ; (15/11, Z5) confirm: domanda, no = si continua a cambiare
        beq _no
        clc
        jsr cs_ask
        bcc _jdr
        jsr cs_apply
_done   lda #SFX_PICK
        jsr sfx_play
        jmp ui_charsheet        ; da capo: senza punti la schermata passa a "no points to spend"
_back   jsr cs_psum             ; (15/11, Z5) uscita con punti in attesa: si' = spesi, no = tornano da spendere
        beq +
        sec
        jsr cs_ask
        bcc +
        jsr cs_apply
+       jsr cs_zero             ; fuori dalla schermata cs_pend = 0 (pts_avail, HUD)
        jmp ui_exit

; C = 0: "spend N point(s) for good?", C = 1: "... before leaving?" (riga 23); risposta in C (ui_yesno)
cs_ask:
        php
        jsr msg23
        #msg "spend "
        jsr cs_psum
        pha
        jsr ui_b3l
        #msg " point"
        pla
        cmp #2
        bcc +
        lda #'s'
        jsr ui_putc
+       plp
        bcs +
        #msg " for good?"
        jmp ++
+       #msg " before leaving?"
+       jsr ui_yesno
        php
        jsr msg23
        plp
        rts

; somma dei punti in attesa -> A (Z = nessuno)
cs_psum:
        lda #0
        clc
        adc cs_pend
        adc cs_pend+1
        adc cs_pend+2
        rts

; nessun punto in attesa (A = 0 all'uscita)
cs_zero:
        lda #0
        ldx #2
-       sta cs_pend,x
        dex
        bpl -
        rts

; punti in attesa -> spesi (c_sadd)
cs_apply:
        ldx #2
-       lda cs_pend,x
        clc
        adc c_sadd,x
        sta c_sadd,x
        dex
        bpl -
        jsr cs_zero
        jmp recalc_stats        ; statistiche ricalcolate (hp_cap: vita attuale entro il nuovo massimo)


; valori della schermata: prima le statistiche come se i punti in attesa fossero spesi (copia di hpmax..s_dk in
; cs_nv), poi quelle vere; ogni valore e' "attuale" e, se i punti in attesa lo cambiano, "-> nuovo" in verde
cs_draw:
        ldx #2
-       lda c_sadd,x            ; anteprima: c_sadd += cs_pend
        clc
        adc cs_pend,x
        sta c_sadd,x
        dex
        bpl -
        jsr recalc_stats
        ldx #11
-       lda hpmax,x
        sta cs_nv,x
        dex
        bpl -
        ldx #2
-       lda c_sadd,x
        sec
        sbc cs_pend,x
        sta c_sadd,x
        dex
        bpl -
        jsr recalc_stats        ; statistiche vere (senza i punti in attesa)
        #at 7,3                 ; vita massima (16 bit)
        lda hpmax
        ldx hpmax+1
        jsr ui_n5l
        lda hpmax
        cmp cs_nv
        bne +
        lda hpmax+1
        cmp cs_nv+1
        beq ++
+       jsr cs_arw
        lda cs_nv
        ldx cs_nv+1
        jsr ui_n5l
+       jsr cs_eol
        #at 7,4                 ; ATT (con '+')
        lda s_att
        ldy cs_nv+s_att-hpmax
        sec
        jsr cs_pv
        jsr cs_eol
        #at 7,5                 ; CA
        lda s_ac
        ldy cs_nv+s_ac-hpmax
        clc
        jsr cs_pv
        jsr cs_eol
        #at 7,6                 ; danno: i punti cambiano solo il fisso (s_dk)
        lda s_dn
        ldx s_ds
        ldy s_dk
        jsr ui_dice
        lda s_dk
        cmp cs_nv+s_dk-hpmax
        beq +
        jsr cs_arw
        lda s_dn
        ldx s_ds
        ldy cs_nv+s_dk-hpmax
        jsr ui_dice
+       jsr cs_eol
        ldx #0                  ; caratteristiche: righe 9..11
_s      stx tmp3
        txa
        clc
        adc #9
        tay
        ldx #2
        jsr ui_at
        ldx tmp3                ; (12/11) cursore sulle caratteristiche solo con tutte le voci
        lda cs_mode
        beq +
        ldx #$ff                ; (nessuna voce $ff: spazio)
+       jsr ui_mark
        ldx tmp3
        jsr cs_text             ; "str" / "dex" / "con"
        lda #5                  ; valore dalla colonna 7
        jsr cs_pad
        ldx tmp3
        lda s_str,x             ; valore (anello compreso) -> con i punti in attesa
        ldy cs_nv+s_str-hpmax,x
        clc
        jsr cs_pv
        lda #16                 ; modificatore dalla colonna 18
        jsr cs_pad
        #msg "mod "
        ldx tmp3
        lda cs_nv+s_str-hpmax,x
        jsr modv
        tay
        lda s_str,x
        jsr modv
        sec
        jsr cs_pv
        lda #36
        jsr cs_pad
        ldx tmp3
        inx
        cpx #3
        bne _s
        lda cs_mode             ; (12/11) solo respec: cursore (voce 0) nella riga 17
        beq _a0
        cmp #1
        bne _ax
        #at 2,17
        ldx #0
        jmp ui_mark
_ax     rts
_a0     #at 19,13               ; punti da spendere e, se ce ne sono, quelli in attesa (numero verde)
        jsr pts_avail
        jsr ui_b3l
        lda #4
        jsr cs_pad
        jsr cs_psum
        beq +
        pha
        #msg "pending "
        pla
        ldy #UC_PEND
        sty ui_fc
        jsr ui_b3l
        jsr cs_col
+       lda #19
        jsr cs_pad
        #at 3,14                ; a che cosa serve la caratteristica sotto il cursore (recalc_stats)
        ldx ui_cur
        cpx #3
        bcs +
        lda #UC_HELP
        sta ui_col
        inx
        inx
        inx
        jsr cs_text
        jsr cs_col
+       lda #35
        jsr cs_pad
        ldx #3                  ; azioni: cursore nelle righe 17..19
_a      stx tmp3
        txa
        clc
        adc #14
        tay
        ldx #2
        jsr ui_at
        ldx tmp3
        jsr ui_mark
        ldx tmp3
        inx
        cpx ui_n
        bne _a
        rts

; A = valore attuale, Y = nuovo, C = 1: con '+' davanti. "attuale" e, se diverso, " -> nuovo" in verde
cs_pv:  ror cs_sg
        sty cs_nw
        sta cs_cu
        jsr cs_p1
        lda cs_cu
        cmp cs_nw
        beq cs_col
        jsr cs_arw
        lda cs_nw
        jsr cs_p1
cs_col: lda #0                  ; colori normali
        sta ui_fc
        lda #UC_LABEL
        sta ui_col
        rts
cs_p1   pha
        bit cs_sg
        bpl +
        lda #$2b
        jsr ui_putc
+       pla
        jmp ui_b3l

; " -> ", poi valori in verde
cs_arw: lda #$20
        jsr ui_putc
        lda #CH_ARROW
        jsr ui_putc
        lda #$20
        jsr ui_putc
        lda #UC_PEND
        sta ui_fc
        sta ui_col
        rts

; fine di una riga delle statistiche derivate (dalla colonna 7): colori normali, spazi fino alla colonna 38
cs_eol: jsr cs_col
        lda #31
; spazi fino a cidx = A (cancella cio' che restava del disegno precedente)
cs_pad: sta cs_k
-       lda cidx
        cmp cs_k
        bcs +
        lda #$20
        jsr ui_putc
        jmp -
+       rts

; testo X della tabella: 0..2 nomi delle caratteristiche, 3..5 a che cosa servono (combattimento.md, recalc_stats)
cs_text:
        lda cs_tl,x
        pha
        lda cs_th,x
        tax
        pla
        jmp ui_puts5            ; (21/11 sera) testi a 5 bit

cs_tl   .byte <cs_str, <cs_dex, <cs_con, <cs_hs, <cs_hd, <cs_hc
cs_th   .byte >cs_str, >cs_dex, >cs_con, >cs_hs, >cs_hd, >cs_hc
cs_str  #t5 "str"
cs_dex  #t5 "dex"
cs_con  #t5 "con"
cs_hs   #t5 "attack, damage, battle cry"
cs_hd   #t5 "armor class (armor may cap it)"
cs_hc   #t5 "hit points, for every level"
        .enc "none"
