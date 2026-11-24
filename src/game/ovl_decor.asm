; ===================================================================
;  ovl_decor.asm - (19/11) CODICE DEL PIANO dei piani generati del capitolo DK_CHAP (1-4): la passata degli ARREDI
;  (richiesta del committente: elementi decorativi a tema in tutti i dungeon; docs/wiki/dungeon.md "Arredi dei piani").
;  Assemblato una volta per capitolo (tools/build/asm.sh, -D DK_CHAP=c) -> out/work/ovl_decor{c}.bin, nella coda di GFX(2c-1)
;  (tools/build/bundle.py), copiato a OVP_AT da gfx_tail. Capitolo 4: anche la fine della generazione della cittadella
;  (gen_citadel.asm, OVJ_GEN). Regole e tabelle: tools/build/decor_gfx.py (out/work/decor.inc); decorate() la' e' la stessa
;  passata in Python.
;  OVJ_DECOR (load_location, subito dopo gen_dungeon, prima di mostri e bauli: floor_ok li tiene fuori dagli arredi): per ogni
;  casella di pavimento (FLOOR..FLOORC, y e x da 1 a 46) h = rand(); se h < DK_ANY: h < DK_W un arredo calpestabile
;  (dk_wt), altrimenti un solido se la casella e' "sicura": regola B, le 8 vicine sono pavimento (isolato, dk_bt); regola A, a
;  nord un muro (tile < FLOOR) e O, E, SO, S, SE pavimento (contro il muro, dk_at). Un solido cosi' non separa mai nulla:
;  i suoi vicini percorribili restano uniti girandogli attorno. Il generatore casuale si salva e si rimette com'era: mostri
;  e bauli usano la stessa sequenza di prima (cambia solo dove un arredo ha preso il loro pavimento).
; ===================================================================
        .include "../out/work/game.lbl"
        * = OVP_AT
        clc                     ; OVJ_INIT
        rts
        nop
.if DK_CHAP == 2
        jmp dw_tick             ; OVJ_TICK: (24/11) fango attorno agli annegati
.else
        clc                     ; OVJ_TICK
        rts
        nop
.endif
        clc                     ; OVJ_FIRE
        rts
        nop
        clc                     ; OVJ_DMG
        rts
        nop
        clc                     ; OVJ_KILL: bottino come sempre
        rts
        nop
        jmp dk_run              ; OVJ_DECOR
.if DK_CHAP == 4
        jmp cit_main            ; OVJ_GEN: cittadella (gen_citadel.asm)
.else
        clc                     ; OVJ_GEN
        rts
        nop
.endif
        .cerror * - OVP_AT != OVJ_N, "ovl_decor: tabella dei salti"
        .cerror T_FLOORC - T_FLOOR != 2, "ovl_decor: pavimenti FLOOR..FLOORC non contigui"
        .include "../out/work/decor.inc"

.if DK_CHAP == 2
; (24/11, IA del capitolo 2: scelta mia, il committente ha chiesto il capitolo 2 completo senza altre decisioni) FANGO: con un
; annegato (tipo DW_TYPE) vivo e sveglio a meno di DW_R pixel su entrambi gli assi il PG si muove a meta' velocita' (ovp_slow,
; update_player: fermo un fotogramma su due). Controllo ogni 4 fotogrammi.
DW_TYPE = 1
DW_R    = 24
dw_tick:
        lda frame
        and #3
        bne _r
        ldy #0
        ldx lb_cnt
_l      dex
        bmi _e
        lda mtype,x
        cmp #DW_TYPE
        bne _l
        lda malive,x
        beq _l
        lda mwake,x
        beq _l
        lda px
        sec
        sbc mxl,x
        sta tmp0
        lda px+1
        sbc mxh,x
        jsr _near
        bcc _l
        lda py
        sec
        sbc myl,x
        sta tmp0
        lda py+1
        sbc myh,x
        jsr _near
        bcc _l
        iny
_e      sty ovp_slow
_r      rts
; A = byte alto, tmp0 = basso di una differenza -> C=1 se |differenza| < DW_R
_near   beq _p
        cmp #$ff
        bne _no
        lda tmp0
        cmp #256-DW_R+1
        rts
_p      lda tmp0
        cmp #DW_R
        bcc _y
_no     clc
        rts
_y      sec
        rts
.endif

dk_x    .byte 0
dk_y    .byte 0
dk_xm   .byte 0                 ; x - 1
dk_h    .byte 0

dk_run:
        lda rnd                 ; il generatore casuale si rimette com'era alla fine
        pha
        lda rnd+1
        pha
        ora #$80                ; xorshift16 da 0 resta 0
        sta rnd+1
        lda #1
        sta dk_y
_row    ldx dk_y                ; ptr1 = riga y - 1 (le tre righe y-1, y, y+1 a +0, +MAPW, +2*MAPW)
        lda maprow_lo-1,x
        sta ptr1
        lda maprow_hi-1,x
        sta ptr1+1
        lda #1
        sta dk_x
_col    lda dk_x
        clc
        adc #MAPW
        tay
        lda (ptr1),y
        jsr dk_fl
        bcs _nx
        jsr rand
        cmp #DK_ANY
        bcs _nx
        sta dk_h
        jsr dk_try
.if DK_MIRROR
        lda dk_x                ; cittadella: la stessa h sulla casella specchiata
        pha
        eor #$ff
        sec
        adc #47
        sta dk_x
        jsr dk_try
        pla
        sta dk_x
.endif
_nx     inc dk_x
        lda dk_x
        cmp #DK_XEND
        bne _col
        inc dk_y
        lda dk_y
        cmp #47
        bne _row
        pla
        sta rnd+1
        pla
        sta rnd
        rts

; arredo sulla casella (dk_x, dk_y) se e' pavimento e sicura, con dk_h
dk_try:
        ldx dk_x
        dex
        stx dk_xm
        lda #MAPW+1             ; la casella
        jsr dk_get
        jsr dk_fl
        bcs _r
        lda dk_h
        cmp #DK_W
        bcs _sol
        and #1
        tax
        lda dk_wt,x
        jmp _put
_sol    ldx #4                  ; O, E, SO, S, SE: pavimento
_l5     lda dk_o5,x
        jsr dk_get
        jsr dk_fl
        bcs _r
        dex
        bpl _l5
        ldx #2                  ; NO, N, NE pavimento: isolato (regola B)
_l3     lda dk_o3,x
        jsr dk_get
        jsr dk_fl
        bcs _a
        dex
        bpl _l3
        lda dk_h
        and #1
        tax
        lda dk_bt,x
        jmp _put
_a      lda #1                  ; muro a nord: contro il muro (regola A)
        jsr dk_get
        cmp #T_FLOOR
        bcs _r
        lda dk_h
        and #1
        tax
        lda dk_at,x
_put    pha
        lda #MAPW+1
        clc
        adc dk_xm
        tay
        pla
        sta (ptr1),y
_r      rts

; A = scostamento nel quadrato 3x3 (0 = NO) -> A = tile. X conservato
dk_get  clc
        adc dk_xm
        tay
        lda (ptr1),y
        rts

; C=0 se il tile A e' un pavimento (FLOOR..FLOORC)
dk_fl   sec
        sbc #T_FLOOR
        cmp #3
        rts

dk_o5   .byte MAPW, MAPW+2, 2*MAPW, 2*MAPW+1, 2*MAPW+2
dk_o3   .byte 0, 1, 2

.if DK_CHAP == 4
        .include "gen_citadel.asm"
.endif
ovd_end
        .cerror ovd_end > OVP_END, "codice del piano dei piani oltre $CFFF"
