; ===================================================================
;  menu/inn.asm - la locanda, parte del modulo MENU (src/menu.asm; fino all'11/11 il modulo OVLT): schermata e
;  baule (nel blocco dell'eroe, CHRBLK). La scelta dell'equipaggiamento e' in menu/inn_eq.asm (ex OVL2).
;
;  Baule di casa: STASH_N oggetti x 4 byte (id, bonus, durabilita', massimo) nel blocco dell'eroe (08/11 sera):
;  sempre in RAM, letto e scritto con l'eroe. Uscendo non si salva (11/11 sera, decisione del committente): il baule va
;  sul disco con "save game" o al cambio di capitolo, insieme all'eroe (spegnendo prima si torna all'ultimo salvataggio
;  per eroe e baule insieme: niente duplicati).
; ===================================================================
PAGE    = 8                     ; oggetti del baule per pagina (STASH_N = 24: 3 pagine, 08/11)
        .cerror STASH_N % PAGE != 0, "STASH_N non multiplo di PAGE"
        .cerror PACK_N > PAGE, "zaino piu' lungo della pagina del baule"

; ------------------------------------------------------------------ baule di casa (08/11: schermata nuova)
; Righe: 0 titolo; 1-6 riquadri del PG (nome, statistiche) e dell'oggetto selezionato; 7-10 equipped su 2 colonne
; (icone); 11-22 zaino (oro + 8) e baule (oro + 8 della pagina, numero di pagina come pulsante); 23 messaggi; 24 tasti.
; Zaino e baule sempre ordinati per categoria (sort4). Voci del cursore (ui_nav, una sola lista):
;   normale: 0-3 equipped (arma, armatura, scudo, anello), 4 oro zaino, 5-12 zaino, 13 pagina, 14 oro baule,
;            15-22 baule (pagina st_top). Destra: dallo zaino al baule sulla stessa riga.
;   scelta (h_sel = categoria): [remove] (non per l'arma), oggetti della categoria nello zaino, pagina, quelli del
;            baule (pagina h_fp della lista filtrata). Fire indossa; RUN/STOP annulla.
H_EQY   = 8                     ; prima riga di equipped
H_LY    = 12                    ; riga dell'oro di zaino e baule (gli oggetti da H_LY+2)
K_EQ    = 0                     ; tipi di voce (h_ref)
K_GP    = 1
K_PI    = 2
K_PG    = 3
K_GC    = 4
K_CI    = 5
K_RM    = 6
ov_stash:
        lda #0
        sta h_jf
        sta h_fl
        jsr mk_off              ; tutta la schermata con il KERNAL escluso ($01 = $35): niente KERNAL qui dentro
        jsr recalc_stats
        jsr st_sort
        jsr sort_pack
        lda #0
        sta h_sel
        sta st_top
        jsr h_setn
        jsr nav_init
        lda #5                  ; cursore sul primo posto dello zaino
        sta ui_cur
        jsr nav_sync
.if TESTUI == 29
        lda #3                  ; (screenshot) scelta dell'anello
        jsr h_enter
.endif
_scr    jsr h_screen
_dr     jsr h_draw
.if NOKEYS                      ; (da out/work/game.lbl: build di test per gli screenshot)
_hg     jmp _hg
.endif
_in     jsr h_flash
        jsr ui_nav
        cmp #NAV_MOVE
        bne +
        jsr h_msgclr
        jmp _dr
+       cmp #NAV_BACK
        beq _back
        cmp #NAV_FIRE
        bne _key
        jsr h_msgclr
        jsr h_fire
        bcs _scr                ; cambio di modalita': schermata da ridisegnare
        jmp _dr
_key    lda h_sel
        bne _in
        lda keynew+4
        and #$02                ; I: esce (solo fuori dalla scelta)
        bne _x
        lda joynew
        and #$08                ; destra: dallo zaino al baule, stessa riga
        beq _in
        lda ui_cur
        cmp #4
        bcc _in
        cmp #13
        bcs _in
        adc #10
        sta ui_cur
        jsr nav_sync
        jmp _dr
_back   lda h_sel
        beq _x
        jsr h_back              ; RUN/STOP nella scelta: annulla
        jmp _scr
_x      jmp ui_exit             ; (11/11 sera: niente salvataggio uscendo, lo fa "save game": il baule e' nel blocco dell'eroe)

; numero di voci (ui_n) per la modalita' attuale
h_setn: lda h_sel
        bne +
        lda #23
        sta ui_n
        rts
+       lda h_rm
        clc
        adc h_np
        adc #1
        adc h_ncp
        sta ui_n
        rts

; uscita dalla scelta: cursore sul posto di equipped
h_back: ldx h_sel
        dex
        stx ui_cur
        lda #0
        sta h_sel
        jsr h_setn
        jmp nav_sync

; schermata fissa: riquadri (equipped colorato nella scelta), titoli, riga dei tasti
h_screen:
        jsr ui_begin
        lda #3
        jsr ib_set
        lda #<h_box             ; (09/11) riquadri con la routine comune ui_boxes: i primi 4, poi equipped
        ldx #>h_box             ; (rosso nella scelta dell'anello o dell'arma)
        ldy #16
        jsr ui_boxes
        lda h_sel
        beq +
        lda #10
        sta ui_bc
+       lda #<h_box+16
        ldx #>h_box+16
        ldy #4
        jsr ui_boxes
        lda #<h_tt              ; titolo (routine unica ui_title) con il boccale ai lati (09/11)
        ldx #>h_tt
        ldy #CH_INN
        jsr ui_title
        jsr ui_labels
        .byte 22,1
        .text " selected item "
        .byte 0,2,7
        .text " equipped "
        .byte 0,2,11
        .text " pack "
        .byte 0,22,11
        .text " chest "
        .byte 0,2,1,$20,0,$ff
        jsr ui_cname
        lda #$20
        jsr ui_putc
        lda h_sel
        bne +
        jmp nav_help
+       jsr ui_labels
        .byte 1,24
        .text "fire:equip  run/stop:cancel"
        .byte 0,$ff
        rts
h_tt    .text "inn", 0
h_box   .byte 0,1,20,6, 20,1,20,6, 0,11,20,12, 20,11,20,12, 0,7,40,4

; ---- disegno di tutte le parti variabili
h_draw: jsr h_stats
        lda #H_EQY              ; equipped: routine comune del gioco (eq_draw); nella scelta '>' fisso sul posto
        sta eq_y
        ldx h_sel
        dex                     ; $FF fuori dalla scelta
        stx eq_fix
        lda #0
        ldy h_sel
        beq +
        lda #$80                ; nella scelta il cursore della lista non va su equipped
+       sta eq_u0
        jsr eq_draw
        ldx #1                  ; oro: zaino (1,H_LY), baule (21,H_LY); cursore solo fuori dalla scelta
        ldy #H_LY
        jsr ui_at
        lda #4
        jsr h_cursn
        ldx #0
        jsr h_gold
        ldx #21
        ldy #H_LY
        jsr ui_at
        lda #14
        jsr h_cursn
        ldx #1
        jsr h_gold
        lda h_sel
        bne _sel
        lda #0                  ; ---- normale: zaino e baule
        sta hl_s
        sta hl_i
        lda #5
        ldx #1
        ldy #PACK_N
        jsr h_list
        inc hl_s
        lda st_top
        sta hl_i
        lda #15
        ldx #21
        ldy #PAGE
        jsr h_list
        lda #13                 ; pagina: voce 13, st_top / PAGE + 1 di STASH_N / PAGE
        sta tmp4
        lda st_top
        ldx #STASH_N/PAGE
        jmp _pg
_sel    ldx #1                  ; ---- scelta: righe pulite, [remove], blocco della categoria in zaino e baule
_cl     txa
        clc
        adc #H_LY
        tay
        txa
        pha
        ldx #1
        jsr ui_at
        jsr h_blank
        ldx #21
        jsr ui_at
        jsr h_blank
        pla
        tax
        inx
        cpx #PAGE+2
        bne _cl
        lda h_rm
        beq +
        #at 1,H_LY+1
        lda #0
        jsr h_curs
        #msg " - remove"
+       lda #0
        sta hl_s
        lda h_p0
        sta hl_i
        lda h_rm
        ldx #1
        ldy h_np
        jsr h_list
        inc hl_s
        lda h_c0
        clc
        adc h_fp
        sta hl_i
        lda h_rm
        clc
        adc h_np
        sta tmp4                ; voce della pagina
        adc #1
        ldx #21
        ldy h_ncp
        jsr h_list
        lda h_nc                ; pagine della lista filtrata: (h_nc - 1) / PAGE + 1 (almeno 1)
        beq +
        sec
        sbc #1
+       lsr a
        lsr a
        lsr a
        tax
        inx
        lda h_fp
_pg     stx tmp5                ; A = primo posto della pagina, X = pagine, tmp4 = voce della pagina
        lsr a
        lsr a
        lsr a
        pha
        ldx #33
        ldy #11
        jsr ui_at
        lda tmp4
        jsr h_curs
        pla
        clc
        adc #$31
        jsr ui_putc
        lda #$2f
        jsr ui_putc
        lda tmp5
        ora #$30
        jsr ui_putc
        lda #$20
        jsr ui_putc
        jmp h_item              ; riquadro dell'oggetto sotto il cursore

        .cerror PAGE != 8, "pagine da 8 (divisione con 3 lsr)"

; come h_curs, ma senza cursore nella scelta (oro)
h_cursn ldx h_sel
        bne +
        jmp h_curs
+       lda #$20
        jmp ui_putc
; lista: Y voci da (X, H_LY+2), voce del cursore da A, oggetti (hl_s, hl_i...); Y = 0: niente
h_list: sta hl_u
        stx hl_x
        sty hl_n
        cpy #0
        beq _r
        ldx #0
_l      stx hl_j
        txa
        clc
        adc #H_LY+2
        tay
        ldx hl_x
        jsr ui_at
        lda hl_u
        clc
        adc hl_j
        jsr h_curs
        lda hl_i
        clc
        adc hl_j
        tax
        lda hl_s
        jsr h_name
        ldx hl_j
        inx
        cpx hl_n
        bne _l
_r      rts

; riquadro del PG: hp (massimo), ac, att, str, dmg, dex, con (colonne fisse: valori fino a 3 cifre, hp fino a 5)
h_stats:
        ldy #2
_c      tya
        pha
        ldx #1
        jsr ui_at
        jsr h_blank
        pla
        tay
        iny
        cpy #6
        bne _c
        jsr ui_labels
        .byte 1,2               ; a sinistra il combattimento, a destra le caratteristiche, il danno da solo in fondo
        .text "hp"
        .byte 0,1,3
        .text "ac"
        .byte 0,1,4
        .text "att +"
        .byte 0,1,5
        .text "dmg"
        .byte 0,11,2
        .text "str"
        .byte 0,11,3
        .text "dex"
        .byte 0,11,4
        .text "con"
        .byte 0,$ff
        #at 5,2
        lda hpmax
        ldx hpmax+1
        jsr ui_n5l
        ldx #0
_v      stx h_k
        lda h_sv+1,x
        tay
        lda h_sv,x
        tax
        jsr ui_at
        ldx h_k
        ldy h_sv+2,x
        lda $9300,y
        jsr ui_b3l
        ldx h_k
        inx
        inx
        inx
        cpx #15
        bne _v
        #at 5,5                 ; danno: dadi + fisso, tutto nel colore dei valori
        lda s_dn
        ldx s_ds
        ldy s_dk
        jmp ui_dice
h_sv    .byte 5,3,<s_ac, 6,4,<s_att, 15,2,<s_str, 15,3,<s_dex, 15,4,<s_con
        .cerror >s_ac != $93 || >s_att != $93 || >s_str != $93 || >s_dex != $93 || >s_con != $93, "h_sv: statistiche fuori da $93xx"

; riquadro dell'oggetto sotto il cursore: nome (riga 2), caratteristiche e valore (righe 3-4)
h_item: lda ui_cur
        jsr h_ref
        ldx #21
        ldy #2
        jsr ui_at
        lda h_kind
        cmp #K_RM
        bne +
        #msg "- remove        "
        lda #0
        beq _sh
+       lda h_src
        bpl +
        jsr h_blank             ; oro, pagina: riquadro vuoto
        lda #0
        beq _sh
+       ldx h_idx
        jsr h_name
        lda it_b
        sta tmp5
        lda it_d
        sta ui_dur
        lda it_m
        sta ui_durm
        lda it_i
_sh     sta ui_sel
        jmp ibox_show

; voce A -> h_kind, h_src ($FF = nessun oggetto), h_idx
h_ref:  ldx #$ff
        stx h_src
        ldx h_sel
        bne _sel
        cmp #4
        bcs +
        adc #PACK_N             ; equipped: posti PACK_N.. delle tabelle dello zaino
        ldx #K_EQ
        bpl _p0
+       ldx #K_GP
        cmp #4
        beq _k
        cmp #13
        bcs +
        sbc #4                  ; (C=0: -5)
        ldx #K_PI
        bpl _p0
+       ldx #K_PG
        cmp #13
        beq _k
        ldx #K_GC
        cmp #14
        beq _k
        sbc #15
        clc
        adc st_top
        ldx #K_CI
        bpl _p1
_sel    ldx h_rm
        beq +
        ldx #K_RM
        cmp #0
        beq _k
        sec
        sbc #1
+       cmp h_np
        bcs +
        adc h_p0
        ldx #K_PI
        bpl _p0
+       sbc h_np
        ldx #K_PG
        cmp #0
        beq _k
        sbc #1
        clc
        adc h_c0
        adc h_fp
        ldx #K_CI
        bpl _p1
_p0     ldy #0
        .byte $2c
_p1     ldy #1
        sty h_src
        sta h_idx
_k      stx h_kind
        rts

; ---- fire. C=1: la schermata cambia modalita' (da ridisegnare tutta)
h_fire: lda ui_cur
        jsr h_ref
        lda #0
        sta h_jf
        lda h_kind
        cmp #K_PG
        bne _np
        lda h_sel
        bne _fpg
        lda st_top              ; pagina del baule: 1 -> 2 -> 3 -> 1
        clc
        adc #PAGE
        cmp #STASH_N
        bcc +
        lda #0
+       sta st_top
        clc
        rts
_fpg    lda h_fp                ; pagina della lista filtrata
        clc
        adc #PAGE
        cmp h_nc
        bcc +
        lda #0
+       sta h_fp
        jsr h_fpn
        clc
        rts
_np     ldx h_sel
        beq _norm
        jmp h_equip
_norm   cmp #K_EQ
        bne +
        lda ui_cur              ; posto di equipped: entra nella scelta (modulo OVL2)
        jmp h_enter
+       cmp #K_GC               ; oro del baule: niente (10/11: il prelievo non c'e' piu')
        beq _gc
        cmp #K_GP
        bne +
        jsr st_gold             ; oro addosso: tutto nel baule
_gc     clc
        rts
+       cmp #K_PI
        bne +
        lda #0                  ; zaino -> baule: poi la pagina dove e' finito
        ldx h_idx
        jsr h_get
        lda it_i
        beq _r
        jsr h_keep
        lda #0
        beq _mv
+       lda #1                  ; baule -> zaino
_mv     sta st_col
        ldx h_idx
        jsr st_move
        jsr h_jump
_r      clc
        rts

; voci del baule nella pagina filtrata (h_ncp), poi ui_n
h_fpn:  lda h_nc
        sec
        sbc h_fp
        cmp #PAGE
        bcc +
        lda #PAGE
+       sta h_ncp
        jsr h_setn
        jmp nav_sync

; ricorda it_* (entra nel baule): dopo l'ordinamento la pagina mostrata sara' la sua (h_jump)
h_keep: pha
        txa
        pha
        ldx #3
-       lda it_i,x
        sta kp_i,x
        dex
        bpl -
        lda #1
        sta h_jf
        pla
        tax
        pla
        rts

; baule ordinato; se un oggetto e' entrato, st_top = la sua pagina
h_jump: jsr st_sort
        lda h_jf
        beq _r
        ldx #STASH_N-1
_f      ldy #3
-       lda st_id,x             ; (st_b, st_du, st_m seguono a passo STASH_N: confronto dei 4 byte)
        cmp kp_i
        bne _n
        lda st_b,x
        cmp kp_i+1
        bne _n
        lda st_du,x
        cmp kp_i+2
        bne _n
        lda st_m,x
        cmp kp_i+3
        beq _y
_n      dex
        bpl _f
_r      rts
_y      txa
        and #$100-PAGE
        sta st_top
        rts

; lampo rosso del bordo: si spegne da solo
h_flash lda h_fl
        beq +
        dec h_fl
        bne +
        lda #0
        sta BORDER
+       rts


; variabili della schermata (nel modulo: RAM normale)
; (11/11) variabili della locanda in pagina zero ($65-$81, libera nel gioco: docs/wiki/tecnica.md): niente byte nel file e
; istruzioni piu' corte
h_sel   = $65                 ; 0 normale, 1..4 = scelta della categoria (arma, armatura, scudo, anello)
h_rm    = $66                 ; 1 = voce remove (non per l'arma)
h_p0    = $67                 ; zaino: primo posto della categoria e quanti
h_np    = $68
h_c0    = $69                 ; baule: primo posto della categoria e quanti
h_nc    = $6a
h_fp    = $6b                 ; pagina della lista filtrata (primo posto relativo)
h_ncp   = $6c                 ; voci del baule nella pagina filtrata
h_kind  = $6d                 ; h_ref: tipo di voce, tabelle (0 zaino/equip, 1 baule, $FF niente), posto
h_src   = $6e
h_idx   = $6f
h_k     = $70
h_eqi   = $71
h_jf    = $72                 ; 1 = un oggetto e' entrato nel baule (kp_i): mostrarne la pagina
h_fl    = $73                 ; lampo rosso del bordo: fotogrammi
hl_x    = $74                 ; h_list
hl_u    = $75
hl_s    = $76
hl_i    = $77
hl_n    = $78
hl_j    = $79
nw_i    = $7a                 ; oggetto nuovo da indossare (id, bonus, durabilita', massimo)
kp_i    = $7e                 ; oggetto entrato nel baule
        .cerror kp_i+4 > $82, "variabili della locanda oltre $81"
        .cerror it_b != it_i+1 || it_d != it_i+2 || it_m != it_i+3, "it_i..it_m non contigui"

