; ===================================================================
;  ovl_boss1.asm - (19/11) CODICE DEL PIANO 5: The Hollow Abbot (capitolo 1, docs/wiki/bestiario.md "Meccaniche dei boss di
;  capitolo"). A OVP_AT, nella coda di GFX2 (tools/build/bundle.py), copiato da gfx_tail entrando nel piano.
;  EVOCA I MORTI: quando la vita scende sotto 2/3 e sotto 1/3 si ferma 1 s lampeggiando di verde (bordo verde) e fa alzare
;  2 scheletri (tipo 2) accanto a se'; finche' uno scheletro evocato e' vivo si rigenera di 1 punto vita ogni mezzo secondo.
;  Al rientro nel piano le soglie gia' superate non si ripetono (ab_init).
; ===================================================================
        .include "../out/work/game.lbl"
        * = OVP_AT
        jmp ab_init             ; OVJ_INIT
        jmp ab_tick             ; OVJ_TICK
        rts                     ; OVJ_FIRE
        nop
        nop
        rts                     ; OVJ_DMG
        nop
        nop
        clc                     ; OVJ_KILL: bottino come sempre
        rts
        nop
        clc                     ; OVJ_DECOR (piani del boss: arredi gia' nella mappa)
        rts
        nop
        clc                     ; OVJ_GEN
        rts
        nop

AB_SKEL  = 2                    ; tipo evocato: Skeleton
AB_STOP  = 50                   ; fotogrammi fermo prima dell'evocazione (1 s)
AB_REGEN = 25                   ; un punto vita ogni AB_REGEN fotogrammi (mezzo secondo)
AB_GREEN = 5

ab_wave .byte 0                 ; soglie gia' superate (0..2)
ab_t    .byte 0                 ; fotogrammi fermo rimasti (evocazione in corso)
ab_rc   .byte 0                 ; contatore della rigenerazione

; ingresso nel piano: soglie gia' superate (vita gia' sotto) contate
ab_init:
        lda #0
        sta ab_wave
        jsr ob_alive
        bcc _r
_l      jsr ab_th
        bcc _r
        inc ab_wave
        lda ab_wave
        cmp #2
        bcc _l
_r      rts

; C=1 se la vita del boss X e' sotto la soglia dell'ondata ab_wave (2/3, poi 1/3). X conservato
ab_th:
        lda #2
        sec
        sbc ab_wave
        jsr ob_frac3
        jmp ob_below

ab_tick:
        jsr ob_alive
        bcc _r
        lda ab_t                ; evocazione in corso: fermo, lampeggia verde
        beq _nw
        jsr ob_freeze
        lda #AB_GREEN
        jsr ob_blink
        dec ab_t
        bne _r
        lda #0
        sta ovp_tint
        lda #AB_SKEL
        jmp ob_summon
_nw     lda ab_wave
        cmp #2
        bcs _rg
        jsr ab_th
        bcc _rg
        inc ab_wave
        lda #AB_STOP
        sta ab_t
        lda #AB_GREEN           ; bordo verde per tutta la pausa
        ldx #AB_STOP
        jsr set_flash
        lda #SFX_PORTAL
        jmp sfx_play
_rg     jsr ob_sum_alive        ; scheletri evocati vivi: si rigenera (verde fisso a tratti)
        bcc _nr
        lda frame
        and #16
        beq +
        lda #AB_GREEN
+       sta ovp_tint
        inc ab_rc
        lda ab_rc
        cmp #AB_REGEN
        bcc _r
        lda #0
        sta ab_rc
        ldx ob_b
        lda mhp,x               ; +1, mai oltre il massimo
        cmp mhm,x
        lda mhph,x
        sbc mhmh,x
        bcs _r
        inc mhp,x
        bne _r
        inc mhph,x
_r      rts
_nr     lda #0
        sta ovp_tint
        rts

        .include "ovl_boss.inc"
ovb_end
        .cerror ovb_end > OVP_END, "codice del piano 5 oltre $CFFF"
