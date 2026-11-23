; ===================================================================
;  final.asm - (19/11) codice del PIANO 20 (sala del trono): evocazioni del boss finale (final_tick, fb_th, final_init)
;  e la leva (ui_lever). Fino al 19/11 stava in GAME (src/game/game.asm, src/game/ui.asm); ora e' CODICE DEL PIANO: assemblato
;  a OVP_AT ($C900) da src/game/ovl_final.asm, sta nella coda del file del tema GFX8 (tools/build/bundle.py) e gfx_tail lo
;  copia a OVP_AT entrando nel piano 20 (docs/wiki/dungeon.md "Codice del piano"). Nella build TESTUI = 36 (screenshot
;  della leva) resta in GAME (OVP_RES); (23/11) l'arena ne usa una versione sua (out/work/arena_ovl_final.prg, a $F4E0).
; ===================================================================
; a ogni giro nella sala del trono: quando la vita del boss finale scende sotto la soglia dell'ondata (fb_th) evoca
; un'ondata di mostri, se i vivi sono pochi (final_summons in data/rules.yaml)
final_tick:
        lda cur_level
        cmp #MAXLEVEL
        beq _go
_q      rts
_go     ldx lb_boss
        beq _q
        dex
        lda malive,x
        beq _q
        lda fb_wave
        cmp #3
        bcs _q
        jsr fb_th               ; vita <= soglia dell'ondata corrente?
        bcc _q
        inc fb_wave
        ldy #0                  ; mostri vivi oltre al boss
        ldx #0
_c      cpx lb_cnt
        bcs _cd
        lda malive,x
        beq +
        iny
+       inx
        bne _c
_cd     cpy #SUM_MAXALIVE+1     ; (boss compreso)
        bcs _r
        lda #SUM_WAVE
        sta gf_n
        lda #5
        jsr rndrange
        sta gf_t                ; prima punta della stella
_s      ldy lb_cnt
        cpy #32
        bcs _r
        ldx #SUM_FLOOR          ; tipi comuni del piano SUM_FLOOR (statistiche del piano del boss)
        lda maxtype_tab,x
        jsr rndrange
        clc
        adc #1
        sta mtype,y
        lda gf_t
        asl
        tax
        lda fin_tip,x
        sta mix,y
        lda fin_tip+1,x
        sta miy,y
        lda #1
        sta malive,y
        lda #0
        sta mfar,y
        inc lb_cnt
        tya
        tax
        jsr init_rt_from
        ldx lb_cnt
        dex
        lda #1
        sta mwake,x
        lda gf_t                ; punta successiva (due oltre: mai vicine)
        clc
        adc #2
        cmp #5
        bcc +
        sbc #5
+       sta gf_t
        dec gf_n
        bne _s
_r      rts

; X = boss: C=1 se la vita e' sotto la soglia dell'ondata fb_wave (max x (3 - fb_wave) / 4). Preserva X.
fb_th:
        lda mhm,x               ; tmp0/tmp1 = max / 4
        sta tmp0
        lda mhmh,x
        lsr
        ror tmp0
        lsr
        ror tmp0
        sta tmp1
        lda #0
        sta tmp2
        sta tmp3
        lda #3
        sec
        sbc fb_wave
        tay
_t      dey
        bmi _e
        clc
        lda tmp2
        adc tmp0
        sta tmp2
        lda tmp3
        adc tmp1
        sta tmp3
        jmp _t
_e      lda tmp2                ; C = (soglia >= vita) e vita != soglia
        cmp mhp,x
        lda tmp3
        sbc mhph,x
        bcc _no
        lda tmp2
        cmp mhp,x
        bne _y
        lda tmp3
        cmp mhph,x
        beq _no
_y      sec
        rts
_no     clc
        rts

; all'ingresso nell'ultimo piano: le ondate gia' superate (vita del boss sotto la soglia) non si ripetono
final_init:
        lda #0
        sta fb_wave
        lda cur_level
        cmp #MAXLEVEL
        bne _r
        ldx lb_boss
        beq _r
        dex
_l      lda fb_wave
        cmp #3
        bcs _r
        jsr fb_th
        bcc _r
        inc fb_wave
        bne _l
_r      rts


.if ARENA == 0                  ; l'arena non ha la leva (e nella build di test non ci starebbe: gen_img_end oltre $9C00)
        .enc "screen"
; ------------------------------------------------------------------ la leva della sala del trono
ui_lever:
        lda #2
        sta ui_n
        jsr nav_init
_dr     jsr ui_begin
        #at 12,3
        #msg "congratulations,"
        #at 14,4
        jsr ui_cname
        #at 5,7
        #msg "slaying the demon lord is only"
        #at 13,8
        #msg "the beginning."
        #at 6,10
        #msg "this lever opens the gate to"
        #at 11,11
        #msg "the endless abyss."
        #at 13,14
        #msg "are you sure?"
        #at 14,17
        #msg "give up"
        #at 14,19
        #msg "pull the lever"
_mk     #at 12,17
        ldx #0
        jsr ui_mark
        #at 12,19
        ldx #1
        jsr ui_mark
        #at 1,24
        #msg "fire:select"
_in     jsr ui_nav
        cmp #NAV_MOVE
        beq _mk
        cmp #NAV_FIRE
        bne _in
        lda ui_cur
        beq _x                  ; give up
        lda #1                  ; pull the lever: al posto della leva il portale nero
        sta c_lever
        lda #FIN_AX
        sta tx
        lda #FIN_AY
        sta ty
        lda #T_BPORTAL
        jsr set_tile
        lda #SFX_PORTAL
        jsr sfx_play
_x      jmp ui_exit
        .enc "none"
.endif
