; ===================================================================
;  menu/inn.asm - la locanda, parte del modulo MENU (src/menu.asm; fino all'11/11 il modulo OVLT): schermata e
;  baule (nel blocco dell'eroe, CHRBLK). Spostamenti fra zaino e baule in menu/inn_eq.asm (st_move).
;
;  Baule di casa: STASH_N oggetti x 4 byte (id, bonus, durabilita', massimo) nel blocco dell'eroe (08/11 sera):
;  sempre in RAM, letto e scritto con l'eroe. Uscendo non si salva (11/11 sera, decisione del committente): il baule va
;  sul disco con "save game" o al cambio di capitolo, insieme all'eroe (spegnendo prima si torna all'ultimo salvataggio
;  per eroe e baule insieme: niente duplicati).
; ===================================================================
; (21/11, branch liste-menu, prototipi approvati dal committente) due liste a scorrimento (src/game/slist.asm, segmento CORE):
;   lista 0 "yours": i 5 posti indossati (due anelli), riga sottile, lo zaino (8 posti; niente cintura: le pozioni non vanno nel baule);
;   lista 1 "chest": i 24 posti del baule.
; Fire: zaino -> baule, baule -> zaino, indossato -> zaino (l'arma no: si sostituisce). E: indossa (dallo zaino, o dal baule
; passando dallo zaino). Oro addosso e del baule nei titoli: entrando, l'oro addosso va nel baule (decine, st_gold).
; Niente piu' riquadro delle statistiche e modalita' di scelta dell'equipaggiamento (h_sel): il confronto "you: ..." e' nel
; riquadro dell'oggetto.
ov_stash:
        jsr mk_off              ; interrupt spenti per tutta la schermata
        jsr recalc_stats
        lda c_gold+1            ; (21/11) l'oro addosso nel baule, se fa almeno una decina
        bne +
        lda c_gold
        cmp #10
        bcc ++
+       jsr st_gold
+       jsr st_sort
        jsr sort_pack
        jsr ui_begin
        lda #<h_tt              ; titolo (routine unica ui_title) con il boccale ai lati (09/11)
        ldx #>h_tt
        ldy #CH_INN
        jsr ui_title
        jsr ls2_frame
        jsr ui_labels
        .byte 2,1
        .text " yours "
        .byte 0,2,9
        .text " chest "
        .byte 0,$ff
        lda #0
        sta iv_mode
        sta sl_rv+1
        sta sl_s0
        jsr iv_std
        lda #<h_sg
        ldx #>h_sg
        ldy #0
        jsr sl_segs
        lda #2
        sta sl_sn
        sta sl_s0+1
        lda #1
        sta sl_sn+1
        jsr ls2_init
        lda #EQ_N+1             ; cursore sul primo posto dello zaino (indossati + riga)
        sta sl_cur
_dr     jsr h_draw
.if NOKEYS                      ; (da out/work/game.lbl: build di test per gli screenshot)
_hg     jmp _hg
.endif
_in     jsr sl_nav
        cmp #NAV_BACK
        beq _x
        cmp #NAV_MOVE
        bne +
        jsr h_sel1
        jmp _in
+       cmp #NAV_FIRE
        bne _key
        jsr iv_cur
        jsr h_fire
        jmp _rb
_key    lda keynew+4
        and #$02                ; I: esce
        bne _x
        lda keynew+1            ; E: indossa
        and #$40
        beq _in
        jsr iv_cur
        jsr h_equip
_rb     jsr st_sort             ; le voci possono essere cambiate
        jsr sort_pack
        ldx #1
        jsr sl_reinit
        dex
        jsr sl_reinit
        jmp _dr
_x      jmp ui_exit             ; (11/11 sera: niente salvataggio uscendo, lo fa "save game": il baule e' nel blocco dell'eroe)

h_tt    .text "inn", 0
h_sg    .byte 3, SK_EQ,0,EQ_N, SK_PACK|SK_SEP,0,PACK_N, SK_CHEST,0,STASH_N

; oro nei titoli (addosso, baule), liste, oggetto, tasti
h_draw: ldx #21
        ldy #1
        jsr ui_at
        jsr shop_gold           ; (sh_mask = 0: l'oro addosso)
        ldx #21
        ldy #9
        jsr ui_at
        ldx #1
        jsr h_gold
        jsr iv_cur
        jsr ls2_draw
        jmp h_keys
; cursore spostato: oggetto e tasti
h_sel1: jsr iv_cur
        jsr iv_sel
; riga 24: i tasti secondo la voce (ui_cur = posto)
h_keys: jsr row24
        lda ui_cur
        cmp #PACK_N
        bcc _pk
        cmp #$40
        bcs _ch
        cmp #PACK_N             ; l'arma non si toglie
        beq _bk
        #msg "fire:unequip"
        jmp _sp
_ch     #msg "fire:to pack"
        jmp _eq
_pk     #msg "fire:to chest"
_eq     #msg "  e:equip"
_sp     #msg "  "
_bk     #msg "run/stop:back"
        rts

; fire sul posto ui_cur: zaino -> baule, baule -> zaino, indossato -> zaino (inv_act)
h_fire: ldx ui_cur
        cpx #PACK_N
        bcc _pk
        cpx #$40
        bcc _eq
        txa
        and #$1f
        tax
        lda #1
        .byte $2c
_pk     lda #0
        sta st_col
        jmp st_move
_eq     jmp inv_act

; E sul posto ui_cur: indossa un'arma, un'armatura, uno scudo o un anello dello zaino (inv_act) o del baule (prima nello
; zaino con st_move, poi ritrovato dopo l'ordinamento: kp_i)
h_equip:
        ldx ui_cur
        cpx #PACK_N
        bcc _pk
        cpx #$40
        bcc _r
        txa
        and #$1f
        tax
        stx st_i
        lda st_id,x
        jsr h_wear
        bcs _r
        ldy #3                  ; l'oggetto (st_id, st_b, st_du, st_m: passo STASH_N)
-       lda st_id,x
        sta kp_i,y
        txa
        clc
        adc #STASH_N
        tax
        dey
        bpl -
        ldx st_i
        lda #1
        sta st_col
        jsr st_move
        ldx #PACK_N-1           ; dov'e' finito nello zaino
_f      lda c_pack,x
        cmp kp_i+3
        bne _n
        lda c_packb,x
        cmp kp_i+2
        bne _n
        lda c_packd,x
        cmp kp_i+1
        bne _n
        lda c_packm,x
        cmp kp_i
        beq _go
_n      dex
        bpl _f
_r      rts
_go     stx ui_cur
        jmp inv_act
_pk     lda c_pack,x
        jsr h_wear
        bcc _go
        rts
; C = 0 se l'oggetto A si indossa (arma, armatura, scudo, anello)
h_wear: tay
        beq _n
        lda itcat,y
        cmp #CAT_RING+1
        rts
_n      sec
        rts

; (11/11) variabili della locanda in pagina zero ($65-$81, libera nel gioco: docs/wiki/tecnica.md)
kp_i    = $7e                   ; oggetto preso dal baule per indossarlo (al contrario: massimo, durabilita', bonus, id)
        .cerror kp_i+4 > $82, "variabili della locanda oltre $81"
        .cerror st_b != st_id+STASH_N || st_du != st_b+STASH_N || st_m != st_du+STASH_N, "st_id..st_m a passo STASH_N"
