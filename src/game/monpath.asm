; Percorsi dei mostri (17/11): parte di mon_path (game.asm) e mon_follow, nel secondo blocco di codice (CODE2, $9C00-$9FFF)
; per non consumare il margine del blocco principale. Copyright 2026 - Simone Caporale

; A = |pz_cx - pz_hx| + |pz_cy - pz_hy| (al massimo 255)
pz_h:   lda pz_cx
        sec
        sbc pz_hx
        bpl +
        eor #$ff
        clc
        adc #1
+       sta tmpv
        lda pz_cy
        sec
        sbc pz_hy
        bpl +
        eor #$ff
        clc
        adc #1
+       clc
        adc tmpv
        bcc +
        lda #255
+       rts

pz_ddx  .byte 1, $ff, 0, 0      ; direzioni: 0 +x, 1 -x, 2 +y, 3 -y
pz_ddy  .byte 0, 0, 1, $ff
pz_dc   .byte 1, $ff, BF_W, 256-BF_W

; ---- un passo lungo il percorso: la mossa corrente e' nei bit bassi di mslc. Prima si allinea l'altro asse al centro della
; casella (per passare dalle porte), poi ci si muove nella direzione della mossa; la mossa e' fatta quando si e' entrati nella
; casella nuova (bit 7) e se ne e' raggiunto il centro sull'asse del moto. Passo bloccato (un altro essere, un muro):
; percorso annullato, il mostro resta fermo e il chiamante lo fa aspettare.
mon_follow:
        lda mslc,x
        and #3
        sta mf_d
        cmp #2
        bcs _vy
        lda ent_y               ; moto in x: y allineata al centro (8) a meno di 1 px
        and #15
        cmp #7
        bcc _cp
        cmp #10
        bcs _cm
        jmp _main
_cp     lda #2                  ; y troppo in alto: +y
        bne _cross
_cm     lda #3
        bne _cross
_vy     lda ent_x               ; moto in y: x allineata
        and #15
        cmp #7
        bcc _cpx
        cmp #10
        bcs _cmx
        jmp _main
_cpx    lda #0
        beq _cross
_cmx    lda #1
_cross  jsr mon_try_d
        bcs +                  ; allineamento riuscito
        jmp _put
+
_main   lda mf_d
        jsr mon_try_d
        bcc +                  
        jmp _stop
+
        jsr ent_tile            ; casella cambiata sull'asse del moto: fase 2 (bit 7)
        lda mf_d
        cmp #2
        bcs _ty
        lda nt_x
        cmp ot_x
        jmp _ch
_ty     lda nt_y
        cmp ot_y
_ch     beq +
        lda mslide,x
        ora #$80
        sta mslide,x
+       lda mslide,x
        bpl _put
        ldy mf_d                ; fase 2: centro raggiunto? (+: scostamento >= 8; -: <= 8)
        lda pz_ax,y
        tay
        lda ent_x,y
        and #15
        sta tmpv
        lda mf_d
        and #1                  ; direzioni 1 e 3: verso -
        bne _neg
        lda tmpv
        cmp #8
        bcs _pop
        jmp _put
_neg    lda tmpv
        cmp #9
        bcs _put
_pop    lsr mslide,x            ; mossa successiva: registro a 10 bit (mslide bit 0-1 : mslc) a destra di 2, conteggio - 1
        ror mslc,x              ; (lo spostamento porta "esplora" dal bit 3 al bit 1 e il conteggio nei bit 2-4: si ricompone)
        lsr mslide,x
        ror mslc,x
        lda mslide,x
        and #$02                ; esplora -> bit 3
        asl
        asl
        sta tmpv
        lda mslide,x
        lsr
        lsr
        and #7                  ; conteggio
        sec
        sbc #1
        beq _clr
        asl
        asl
        asl
        asl
        ora tmpv
        sta mslide,x
        jmp _put
_clr    lda tmpv                ; fine del percorso: resta solo "esplora" (mon_step rifa' subito la ricerca)
        sta mslide,x
        lda #0
        sta mslc,x
        jmp _put
_stop   lda #0
        sta mslide,x
        sta mslc,x
        jsr mon_undo
_put    jmp mon_put

pz_ax   .byte 0, 0, ent_y-ent_x, ent_y-ent_x   ; asse della mossa: scarto da ent_x (0 = x, 2 = y)

; C=1 se la posizione proposta (ent_x, ent_y) non e' piu' vicina al PG di quella di partenza (m_adx + m_ady, a 9 bit)
no_progress:
        lda px
        sec
        sbc ent_x
        sta sp_a
        lda px+1
        sbc ent_x+1
        jsr dist8
        sta sp_n
        lda py
        sec
        sbc ent_y
        sta sp_a
        lda py+1
        sbc ent_y+1
        jsr dist8
        clc
        adc sp_n
        sta sp_n                ; nuova distanza (9 bit: sp_n + carry in sp_d)
        lda #0
        rol
        sta sp_d
        lda m_adx
        clc
        adc m_ady
        sta sp_a                ; vecchia distanza (9 bit: sp_a + carry in A)
        lda #0
        rol
        cmp sp_d                ; confronto a 9 bit: nuova >= vecchia -> C=1
        bne _r
        lda sp_n
        cmp sp_a
        rts
_r      lda sp_d
        cmp #1                  ; parti alte diverse: C=1 se la nuova ha la parte alta (e la vecchia no)
        rts

