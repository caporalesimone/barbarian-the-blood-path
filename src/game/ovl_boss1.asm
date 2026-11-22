; ===================================================================
;  ovl_boss1.asm - (19/11) CODICE DEL PIANO 5: The Hollow Abbot (capitolo 1, docs/wiki/bestiario.md "Meccaniche dei boss di
;  capitolo"). A OVP_AT, nella coda di GFX2 (tools/build/bundle.py), copiato da gfx_tail entrando nel piano.
;  EVOCA I MORTI: quando la vita scende sotto 2/3 e sotto 1/3 si ferma 1 s lampeggiando di verde (bordo verde) e fa alzare
;  uno scheletro (tipo 2; 2 fino al 22/11) accanto a se'; finche' uno scheletro evocato e' vivo si rigenera di 1 punto vita ogni mezzo secondo.
;  Al rientro nel piano le soglie gia' superate non si ripetono (ab_init).
;  (21/11, committente) RABBIA sotto il 30% della vita (bordo rosso): attacca piu' spesso (ricarica dell'attacco al massimo
;  AB_RCD fotogrammi invece di 45) e ogni AB_CD fotogrammi agita il TURIBOLO: lampeggia di bianco per AB_WARN fotogrammi (avviso),
;  poi la nube d'incenso (bordo grigio) toglie 1/8 della vita massima al PG se e' a meno di AB_R pixel su entrambi gli assi.
;  (22/11, D8/D16, proposta del 20/11 approvata) TIPO E VITA FISSI (rules.yaml chapter_bosses: CB1_TYPE, CB1_HP, tarati con
;  tools/simulators/sim_builds.py --fit-chapter); rigenerazione ogni AB_REGEN = 50 fotogrammi; SCHELETRI DALLA CRIPTA: ogni
;  AB_RISE fotogrammi uno scheletro si alza su una casella di pavimento a 3-9 caselle dal PG (al massimo AB_RMAX vivi), sveglio;
;  NUBE D'INCENSO per tutto il combattimento: ogni AB_NC fotogrammi l'abate lampeggia d'argento AB_NW fotogrammi (avviso),
;  poi per AB_NT colpi, uno ogni AB_NE fotogrammi, toglie AB_ND punti vita al PG entro AB_R pixel (meta' del colpo del boss).
;  Modello: tools/simulators/boss_scripts.py Abbot (data/rules_next.yaml bosses.abbot.game).
; ===================================================================
        .include "../out/work/game.lbl"
        * = OVP_AT
        jmp ab_init             ; OVJ_INIT
        jmp ab_tick2            ; OVJ_TICK
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
AB_REGEN = 50                   ; un punto vita ogni AB_REGEN fotogrammi (1 s; 25 fino al 22/11)
AB_GREEN = 5

AB_RCD   = 28                   ; (21/11) rabbia: ricarica dell'attacco al massimo 28 fotogrammi (di solito MON_ATK_T = 45)
AB_CD    = 150                  ; (21/11) turibolo ogni 2 x 150 = 300 fotogrammi (6 s; il contatore scende a fotogrammi alterni)
AB_CD0   = 50                   ; (21/11) il primo 2 s dopo l'inizio della rabbia
AB_WARN  = 50                   ; (21/11) avviso: 1 s di lampeggio bianco
AB_R     = 40                   ; (21/11) raggio della nube: 40 pixel (2,5 caselle) su entrambi gli assi
AB_RISE  = 600 / 4              ; (22/11) scheletri dalla cripta: ogni 600 fotogrammi (contatore ogni 4 fotogrammi)
AB_RMAX  = 3                    ;   al massimo 3 vivi
AB_NC    = 400 / 4              ; (22/11) nube d'incenso: ogni 400 fotogrammi (contatore ogni 4 fotogrammi)
AB_NW    = 50                   ;   avviso: 1 s
AB_NT    = 3                    ;   colpi
AB_NE    = 50                   ;   uno ogni secondo
AB_ND    = 4                    ;   punti vita a colpo: meta' del colpo medio del boss (Skeleton King al piano 5: ~8,6)
AB_SILV  = 15                   ; avviso della nube: grigio chiaro (il turibolo della rabbia: bianco)
AB_WHITE = 1
AB_RED   = 2
AB_GREY  = 12

ab_wave .byte 0                 ; soglie gia' superate (0..2)
abx_rage .byte 0                 ; (21/11) 1 = in rabbia (vita sotto il 30%)
abx_cd   .byte 0                 ; (21/11) fotogrammi / 2 al prossimo turibolo
abx_w    .byte 0                 ; (21/11) fotogrammi di avviso rimasti (0 = nessun turibolo in arrivo)
ab_t    .byte 0                 ; fotogrammi fermo rimasti (evocazione in corso)
ab_rc   .byte 0                 ; contatore della rigenerazione
abr_cd  .byte AB_RISE           ; (22/11) fotogrammi / 4 al prossimo scheletro della cripta
abr_s   .byte $ff, $ff, $ff     ; (22/11) scheletri della cripta (indici, $ff = nessuno)
abn_cd  .byte AB_NC             ; (22/11) fotogrammi / 4 alla prossima nube
abn_w   .byte 0                 ; avviso in corso (fotogrammi rimasti)
abn_t   .byte 0                 ; colpi della nube rimasti
abn_e   .byte 0                 ; fotogrammi al prossimo colpo

; ingresso nel piano: soglie gia' superate (vita gia' sotto) contate
ab_init:
        lda #0
        sta ab_wave
        jsr ob_alive
        bcc _r
        lda #CB1_TYPE           ; (22/11, D8) tipo e vita fissi; la vita si mette solo la prima volta (vita massima diversa:
        sta mtype,x             ; appena creato), al ritorno dal portale (STASH) resta quella lasciata
        lda mhm,x
        cmp #<CB1_HP
        bne +
        lda mhmh,x
        cmp #>CB1_HP
        beq _l
+       lda #<CB1_HP
        sta mhm,x
        sta mhp,x
        lda #>CB1_HP
        sta mhmh,x
        sta mhph,x
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
        lda #AB_SKEL            ; (22/11, committente) uno scheletro per evocazione (prima 2: troppo duro per il PG di oggi)
        jmp ob_summon1
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

; (21/11) un giro con la rabbia: prima le evocazioni e la rigenerazione (ab_tick), poi la rabbia (il suo colore ha la precedenza)
; (22/11) e dopo la cripta e la nube d'incenso (ab_tick3: il suo lampeggio ha la precedenza)
ab_tick2:
        jsr ab_tick
        jsr ab_rg
        jmp ab_tick3
ab_rg:  jsr ob_alive
        bcc _r
        lda abx_rage
        bne _on
        jsr ab_th30
        bcc _r
        lda #1                  ; entra in rabbia: bordo rosso, suono, primo turibolo fra 2 s
        sta abx_rage
        lda #AB_CD0
        sta abx_cd
        lda #AB_RED
        ldx #25
        jsr set_flash
        lda #SFX_PORTAL
        jsr sfx_play
        ldx ob_b
_on     lda mcd,x               ; attacca piu' spesso
        cmp #AB_RCD
        bcc +
        lda #AB_RCD
        sta mcd,x
+       lda abx_w
        bne _warn
        lda frame
        and #1
        bne _r
        dec abx_cd
        bne _r
        lda #AB_WARN            ; turibolo: comincia l'avviso
        sta abx_w
_r      rts
_warn   lda #AB_WHITE
        jsr ob_blink
        dec abx_w
        bne _r
        lda #AB_CD
        sta abx_cd
        lda #0
        sta ovp_tint
        lda #AB_GREY            ; la nube
        ldx #8
        jsr set_flash
        ldx ob_b
        jsr ob_dist
        lda ob_adx
        cmp #AB_R
        bcs _r
        lda ob_ady
        cmp #AB_R
        bcs _r
        lda hpmax+1             ; danno = vita massima / 8
        lsr
        sta cb_dh
        lda hpmax
        ror
        lsr cb_dh
        ror
        lsr cb_dh
        ror
        sta cb_dl
        ora cb_dh
        bne +
        inc cb_dl               ; almeno 1
+       jmp hurt_player

; (22/11, D16) scheletri dalla cripta e nube d'incenso, solo con il boss sveglio (mwake: lo ha visto)
ab_tick3:
        jsr ob_alive
        bcc _x
        lda mwake,x
        bne +
_x      rts
+       lda frame
        and #3
        bne _n
        dec abr_cd              ; cripta
        bne +
        lda #AB_RISE
        sta abr_cd
        jsr ab_crypt
+       lda abn_w               ; nube: niente conto alla rovescia durante avviso e colpi
        ora abn_t
        bne _n
        dec abn_cd
        bne _n
        lda #AB_NC
        sta abn_cd
        lda #AB_NW
        sta abn_w
_n      ldx ob_b
        lda abn_w               ; avviso: lampeggia d'argento
        beq _h
        lda #AB_SILV
        jsr ob_blink
        dec abn_w
        bne _r
        lda #0
        sta ovp_tint
        lda #AB_NT
        sta abn_t
        lda #1
        sta abn_e
_h      lda abn_t               ; colpi della nube
        beq _r
        dec abn_e
        bne _r
        lda #AB_NE
        sta abn_e
        dec abn_t
        lda #AB_GREY            ; bordo grigio: la nube
        ldx #8
        jsr set_flash
        ldx ob_b
        jsr ob_dist
        lda ob_adx
        cmp #AB_R
        bcs _r
        lda ob_ady
        cmp #AB_R
        bcs _r
        lda #AB_ND
        sta cb_dl
        lda #0
        sta cb_dh
        jmp hurt_player
_r      rts

; (ab_crypt) uno scheletro dalla cripta: se ne sono vivi meno di AB_RMAX, su una casella di pavimento a 3..9 caselle dal PG (per asse,
; segno a caso; 8 tentativi), sveglio
ab_crypt:
        ldy #AB_RMAX-1          ; un posto libero (mai usato o scheletro morto)
-       ldx abr_s,y
        bmi _f
        lda malive,x
        beq _f
        dey
        bpl -
        rts
_f      sty ob_k
        ldy lb_cnt
        cpy #31
        bcs _x
        jsr player_tile
        lda #8
        sta ob_i
_t      jsr _off
        clc
        adc ptx
        sta tx
        jsr _off
        clc
        adc pty
        sta ty
        cmp #48                 ; dentro la mappa (48 x 48)
        bcs _nt
        lda tx
        cmp #48
        bcs _nt
        jsr floor_ok
        bcc _ok
_nt     dec ob_i
        bne _t
_x      rts
_ok     ldy lb_cnt
        lda #AB_SKEL
        sta mtype,y
        lda tx
        sta mix,y
        lda ty
        sta miy,y
        lda #1
        sta malive,y
        lda #0
        sta mfar,y
        inc lb_cnt
        tya
        tax
        ldy ob_k
        sta abr_s,y
        jsr init_rt_from
        ldx lb_cnt
        dex
        lda #1
        sta mwake,x
        lda #SFX_PORTAL
        jmp sfx_play
; A = scarto a caso: 3..9 con segno a caso (complemento a 2)
_off    jsr rand
        and #7
        cmp #7
        bcc +
        lda #0
+       clc
        adc #3                  ; 3..9
        pha
        jsr rand
        lsr
        pla
        bcc +
        eor #$ff
        adc #0                  ; (C = 1) -A
+       rts

; C=1 se la vita del boss X e' sotto il 30% della massima (1/4 + 1/32 + 1/64 = 29,7%). X conservato
ab_th30:
        lda mhm,x
        sta tmp0
        lda mhmh,x
        sta tmp1
        lsr tmp1                ; /4
        ror tmp0
        lsr tmp1
        ror tmp0
        lda tmp0
        sta ob_th
        lda tmp1
        sta ob_th+1
        ldy #3                  ; /32 (3 passi in piu')
-       lsr tmp1
        ror tmp0
        dey
        bne -
        jsr _add
        lsr tmp1                ; /64
        ror tmp0
        jsr _add
        jmp ob_below
_add    lda ob_th
        clc
        adc tmp0
        sta ob_th
        lda ob_th+1
        adc tmp1
        sta ob_th+1
        rts

        .cerror CB1_TYPE != M_SKELETON_KING && CB1_TYPE != M_FALLEN_WARCHIEF, "CB1_TYPE: controllare il tipo del boss (rules.yaml)"
        .include "ovl_boss.inc"
ovb_end
        .cerror ovb_end > OVP_END, "codice del piano 5 oltre $CFFF"
