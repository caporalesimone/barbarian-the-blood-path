; ===================================================================
;  ovl_boss2.asm - (19/11) CODICE DEL PIANO 10: The Miller of Bad Water (capitolo 2, docs/wiki/bestiario.md "Meccaniche dei
;  boss di capitolo"). A OVP_AT, nella coda di GFX4 (tools/build/bundle.py), copiato da gfx_tail entrando nel piano.
;  IL GIRO DELLA MACINA: sveglio, ogni 4 s carica il colpo (1 s fermo, lampeggia bianco), poi colpisce tutto attorno a se'
;  entro 2 caselle (due attacchi, lampo bianco del bordo) e resta SCOPERTO 1,5 s (fermo, lampeggia azzurro: subisce danno
;  doppio). Sotto meta' vita chiama 2 Drowned (tipo 1), una volta.
; ===================================================================
        .include "../out/work/game.lbl"
        * = OVP_AT
        jmp mi_init             ; OVJ_INIT
        jmp mi_tick             ; OVJ_TICK
        rts                     ; OVJ_FIRE
        nop
        nop
        jmp mi_dmg              ; OVJ_DMG

MI_DROWN = 1                    ; tipo chiamato: Drowned
MI_IDLE  = 200                  ; 4 s fra un giro e l'altro
MI_CHG   = 50                   ; carica: 1 s
MI_OPEN  = 75                   ; scoperto: 1,5 s
MI_R     = 36                   ; raggio del colpo (pixel fra i centri: 2 caselle + mezzo corpo)
MI_WHITE = 1
MI_CYAN  = 3

mi_s    .byte 0                 ; 0 attesa, 1 carica, 2 scoperto
mi_t    .byte MI_IDLE
mi_half .byte 0                 ; Drowned gia' chiamati

mi_init:
        lda #0
        sta mi_half
        jsr ob_alive
        bcc _r
        jsr ob_half
        jsr ob_below
        rol mi_half             ; gia' sotto meta' vita: niente chiamata al rientro
_r      rts

mi_tick:
        jsr ob_alive
        bcc _r
        lda mi_half             ; sotto meta' vita: 2 Drowned, una volta
        bne _w
        jsr ob_half
        jsr ob_below
        bcc _w
        inc mi_half
        lda #MI_DROWN
        jsr ob_summon
        ldx ob_b
_w      lda mwake,x             ; il giro della macina solo da sveglio
        beq _r
        lda mi_s
        beq _idle
        jsr ob_freeze           ; carica e scoperto: fermo
        lda mi_s
        cmp #1
        bne _open
        lda #MI_WHITE
        jsr ob_blink
        dec mi_t
        bne _r
        jsr ob_dist             ; il colpo: tutto attorno entro 2 caselle
        lda ob_adx
        cmp #MI_R+1
        bcs _miss
        lda ob_ady
        cmp #MI_R+1
        bcs _miss
        ldx ob_b
        jsr mon_attack
        jsr mon_attack
_miss   lda #MI_WHITE
        ldx #6
        jsr set_flash
        lda #SFX_HIT
        jsr sfx_play
        lda #2
        sta mi_s
        lda #MI_OPEN
        sta mi_t
_r      rts
_open   lda #MI_CYAN
        jsr ob_blink
        dec mi_t
        bne _r
        lda #0
        sta mi_s
        sta ovp_tint
        lda #MI_IDLE
        sta mi_t
        rts
_idle   dec mi_t
        bne _r
        lda #1
        sta mi_s
        lda #MI_CHG
        sta mi_t
        rts

; colpo del PG al mostro X: sul mugnaio scoperto danno doppio. X conservato
mi_dmg:
        lda mi_s
        cmp #2
        bne _r
        cpx ob_b
        bne _r
        lda lb_boss
        beq _r
        asl cb_dl
        rol cb_dh
_r      rts

        .include "ovl_boss.inc"
ovb_end
        .cerror ovb_end > OVP_END, "codice del piano 10 oltre $CFFF"
