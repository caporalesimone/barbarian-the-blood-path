; ===================================================================
;  ovl_boss3.asm - (19/11) CODICE DEL PIANO 15: Varok the Oathbreaker (capitolo 3, docs/wiki/bestiario.md "Meccaniche dei
;  boss di capitolo"). A OVP_AT, nella coda di GFX6 (tools/build/bundle.py), copiato da gfx_tail entrando nel piano.
;  LA CARICA: sveglio, quando e' allineato con il PG (stessa riga o colonna, da 2 a 9 caselle) si ferma mezzo secondo
;  lampeggiando di giallo, poi parte in linea retta a 4 px per fotogramma (il doppio del passo dei mostri) finche' non urta:
;  contro un muro resta STORDITO 2 s (grigio, scudo giu'); se raggiunge il PG lo colpisce due volte e si ferma. Fuori dallo
;  stordimento lo SCUDO dimezza i danni dei colpi del PG. Dopo ogni carica una pausa di 1,5 s.
; ===================================================================
        .weak
ARENA_OVL = 0                   ; (23/11) 1 = versione per l'arena (tools/build/asm.sh: etichette di arena_game, OVP_AT = $F4E0)
        .endweak
.if ARENA_OVL
        .include "../out/work/arena_game.lbl"
.else
        .include "../out/work/game.lbl"
.endif
        * = OVP_AT
        rts                     ; OVJ_INIT
        nop
        nop
        jmp va_tick             ; OVJ_TICK
        rts                     ; OVJ_FIRE
        nop
        nop
        jmp va_dmg              ; OVJ_DMG
        clc                     ; OVJ_KILL: bottino come sempre
        rts
        nop
        clc                     ; OVJ_DECOR (piani del boss: arredi gia' nella mappa)
        rts
        nop
        clc                     ; OVJ_GEN
        rts
        nop

VA_WARN  = 25                   ; avviso: mezzo secondo fermo
VA_STUN  = 100                  ; stordito: 2 s
VA_PAUSE = 75                   ; pausa dopo una carica: 1,5 s
VA_MAX   = 60                   ; durata massima di una carica (fotogrammi)
VA_AL    = 8                    ; "allineato": scarto in pixel fra i centri
VA_MIN   = 32                   ; distanza minima per partire (2 caselle)
VA_MAX_D = 144                  ; distanza massima (9 caselle)
VA_YEL   = 7
VA_GREY  = 12

va_s    .byte 0                 ; 0 libero, 1 avviso, 2 carica, 3 stordito
va_t    .byte 0
va_dir  .byte 0                 ; passo della carica con segno (2 o $fe)
va_ax   .byte 0                 ; 1 = carica orizzontale, 0 = verticale

va_tick:
        jsr ob_alive
        bcc _r
        lda mwake,x
        beq _r
        lda va_s
        bne _st
        lda va_t                ; libero: pausa dopo la carica
        beq +
        dec va_t
_r      rts
+       jsr ob_dist             ; allineato con il PG?
        lda ob_ady
        cmp #VA_AL
        bcs _col
        lda ob_adx              ; stessa riga: carica orizzontale
        ldy ob_sx
        ldx #1
        bne _chk
_col    lda ob_adx
        cmp #VA_AL
        bcs _r
        lda ob_ady              ; stessa colonna: carica verticale
        ldy ob_sy
        ldx #0
_chk    cmp #VA_MIN
        bcc _r
        cmp #VA_MAX_D
        bcs _r
        stx va_ax
        lda #2
        cpy #0
        beq +
        lda #$fe
+       sta va_dir
        lda #1
        sta va_s
        lda #VA_WARN
        sta va_t
        rts
_st     ldx ob_b
        jsr ob_freeze           ; avviso, carica, stordito: l'IA dei mostri non lo muove
        lda va_s
        cmp #2
        beq _chg
        bcs _stun
        lda #VA_YEL             ; avviso
        jsr ob_blink
        dec va_t
        bne _r2
        lda #2
        sta va_s
        lda #VA_MAX
        sta va_t
_r2     rts
_stun   lda #VA_GREY
        sta ovp_tint
        dec va_t
        bne _r2
_free   lda #0
        sta va_s
        sta ovp_tint
        lda #VA_PAUSE
        sta va_t
        rts
_chg    lda #VA_YEL
        sta ovp_tint
        dec va_t
        beq _free               ; carica troppo lunga (non dovrebbe succedere): finita
        jsr va_step
        bcs _wall
        jsr va_step
        bcs _wall
        ldx ob_b                ; raggiunto il PG: due colpi e fine della carica
        jsr ob_dist
        lda ob_adx
        cmp #14
        bcs _r2
        lda ob_ady
        cmp #14
        bcs _r2
        ldx ob_b
        jsr mon_attack
        jsr mon_attack
        jmp _free
_wall   lda #3                  ; contro un muro: stordito
        sta va_s
        lda #VA_STUN
        sta va_t
        lda #VA_GREY
        ldx #6
        jsr set_flash
        lda #SFX_HIT
        jmp sfx_play

; un passo della carica (2 px nella direzione va_dir): C=1 se un muro lo ferma
va_step:
        ldx ob_b
        lda mxl,x
        sta ent_x
        lda mxh,x
        sta ent_x+1
        lda myl,x
        sta ent_y
        lda myh,x
        sta ent_y+1
        lda #0
        sta st_nz               ; niente scivolamento sugli spigoli: un urto e' un urto
        inc st_nz
        lda va_dir
        ldy va_ax
        beq +
        jsr try_step_x
        jmp _p
+       jsr try_step_y
_p      php
        lda #0
        sta st_nz
        ldx ob_b
        jsr mon_put
        plp
        rts

; colpo del PG al mostro X: lo scudo di Varok dimezza il danno (non da stordito). X conservato
va_dmg:
        cpx ob_b
        bne _r
        lda lb_boss
        beq _r
        lda va_s
        cmp #3
        beq _r
        lsr cb_dh
        ror cb_dl
        lda cb_dl
        ora cb_dh
        bne _r
        inc cb_dl               ; almeno 1
_r      rts

        .include "ovl_boss.inc"
ovb_end
        .cerror ovb_end > OVP_END, "codice del piano 15 oltre $CFFF"
