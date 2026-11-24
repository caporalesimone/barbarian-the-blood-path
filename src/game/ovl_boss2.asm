; ===================================================================
;  ovl_boss2.asm - (19/11) CODICE DEL PIANO 10: Mother Stitch, the Dollmaker (capitolo 2, docs/wiki/bestiario.md "Meccaniche
;  dei boss di capitolo"). A OVP_AT, nella coda di GFX4 (tools/build/bundle.py), copiato da gfx_tail entrando nel piano.
;  I FETICCI: tre RITI (appena sveglia, sotto 2/3 e sotto 1/3 della vita): si ferma 1 s lampeggiando di bianco (bordo
;  bianco), poi pianta 2 feticci (tipo 8 del file GFX4: fermi, non attaccano, vita = la sua massima / 16) sulle caselle
;  accanto. PROTETTA finche' un feticcio e' in piedi: i colpi del PG valgono la meta' e si rigenera di 1 punto vita ogni
;  mezzo secondo (gialla). Caduto l'ultimo feticcio resta SCOPERTA 2 s (ferma, lampeggia azzurro: danno doppio).
;  I feticci danno esperienza ma niente bottino (OVJ_KILL; committente, 19/11). Niente verde: si confonde con la palude.
;  Al rientro nel piano i riti gia' fatti non si ripetono (dm_init). I feticci si riconoscono dal TIPO, non dall'indice:
;  quelli rimessi dalla STASH (ritorno dal portale) restano fermi anche se il codice del piano e' ripartito da capo.
;  (24/11, proposta del 20/11 messa nel codice: il committente ha chiesto il capitolo 2 completo senza altre decisioni)
;  TIPO E VITA FISSI (rules.yaml chapter_bosses: CB2_TYPE, CB2_HP, tarati con sim_builds.py --fit-chapter stitch); feticci
;  piu' robusti (vita / 8) e scoperta piu' breve (1,5 s); MALEDIZIONE: ogni DM_HEX x 4 fotogrammi (sveglia, non durante riti
;  e scoperta) lampeggia di rosso chiaro DM_HW fotogrammi (avviso), poi se il PG e' a meno di DM_HR pixel su entrambi gli assi
;  la cadenza dello Slash x1,625 per DM_HT fotogrammi (ovp_rate, game.asm perform_skill1); FETICCIO MARCIO: i feticci ancora
;  in piedi DM_ROT x 4 fotogrammi dopo il rito diventano annegati (tipo 1, svegli; niente scoperta).
;  Modello: tools/simulators/boss_scripts.py Stitch (data/rules_next.yaml bosses.stitch.game).
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
        jmp dm_init             ; OVJ_INIT
        jmp dm_tick2            ; OVJ_TICK
        clc                     ; OVJ_FIRE
        rts
        nop
        jmp dm_dmg              ; OVJ_DMG
        jmp dm_kill             ; OVJ_KILL
        clc                     ; OVJ_DECOR (piani del boss: arredi gia' nella mappa)
        rts
        nop
        clc                     ; OVJ_GEN
        rts
        nop

DM_TYPE   = 8                    ; tipo del feticcio (nel file GFX4 il posto 8 e' il feticcio: tools/build/monsters.py)
DM_STOP  = 50                   ; rito: 1 s fermo
DM_TOPN  = 75                   ; scoperta: 1,5 s (24/11; 2 s fino al 23/11)
DM_REGEN = 25                   ; protetta: +1 vita ogni mezzo secondo
DM_WHITE = 1
DM_YEL   = 7
DM_CYAN  = 3
DM_HEX   = 400 / 4              ; (24/11) maledizione ogni 400 fotogrammi (contatore ogni 4 fotogrammi)
DM_HW    = 40                   ;   avviso: 0,8 s
DM_HT    = 150                  ;   durata: 3 s
DM_HR    = 40                   ;   raggio: 40 pixel su entrambi gli assi (come la nube dell'abate)
DM_HCOL  = 10                   ;   rosso chiaro
DM_ROT   = 500 / 4              ; (24/11) feticcio marcio: 10 s dopo il rito
DM_ROTT  = 1                    ;   diventa un annegato (tipo 1 del capitolo 2)

dm_wave .byte 0                 ; riti fatti (0..3)
dm_t    .byte 0                 ; rito in corso: fotogrammi rimasti
dm_open .byte 0                 ; scoperta: fotogrammi rimasti
dm_sh   .byte 0                 ; 1 = protetta (c'erano feticci vivi)
dm_rc   .byte 0
dmh_cd  .byte DM_HEX            ; (24/11) fotogrammi / 4 alla prossima maledizione
dmh_w   .byte 0                 ; avviso in corso (fotogrammi rimasti)
dmh_t   .byte 0                 ; maledizione in corso (fotogrammi rimasti)
dmr_c   .byte 0                 ; fotogrammi / 4 al marcire dei feticci (0 = niente)

; ingresso nel piano: riti gia' fatti (vita non piena = il primo, poi le soglie gia' superate)
dm_init:
        lda #0
        sta dm_wave
        sta dmh_w
        sta dmh_t
        sta dmr_c
        sta ovp_rate
        lda #DM_HEX
        sta dmh_cd
        jsr ob_alive
        bcc _r
        lda #CB2_TYPE           ; (24/11, D8) tipo e vita fissi, come l'abate: la vita si mette solo la prima volta
        sta mtype,x
        lda mhm,x
        cmp #<CB2_HP
        bne +
        lda mhmh,x
        cmp #>CB2_HP
        beq ++
+       lda #<CB2_HP
        sta mhm,x
        sta mhp,x
        lda #>CB2_HP
        sta mhmh,x
        sta mhph,x
+       lda mhp,x
        cmp mhm,x
        lda mhph,x
        sbc mhmh,x
        bcs _r                  ; vita piena: nessun rito ancora
_l      inc dm_wave
        lda dm_wave
        cmp #3
        bcs _r
        jsr dm_th
        bcs _l
_r      rts

; C=1 se la vita del boss X e' sotto la soglia del rito dm_wave (1 -> 2/3, 2 -> 1/3). X conservato
dm_th:
        lda #3
        sec
        sbc dm_wave
        jsr ob_frac3
        jmp ob_below

dm_tick:
        jsr ob_alive
        bcc _r
        lda dm_t                ; rito in corso: ferma, lampeggia bianco
        beq _nr
        jsr ob_freeze
        lda #DM_WHITE
        jsr ob_blink
        dec dm_t
        bne _r
        lda #0
        sta ovp_tint
        lda #DM_ROT             ; (24/11) i feticci marciscono fra 10 s
        sta dmr_c
        lda #DM_TYPE
        jsr ob_summon
        jmp dm_fhp
_nr     lda dm_open             ; scoperta: ferma, lampeggia azzurro
        beq _no
        jsr ob_freeze
        lda #DM_CYAN
        jsr ob_blink
        dec dm_open
        bne _r
        lda #0
        sta ovp_tint
_r      rts
_no     jsr dm_fet              ; feticci vivi fermi; C=1 se ce n'e' almeno uno
        bcs _prot
        lda dm_sh
        beq _th
        lda #0                  ; l'ultimo e' caduto adesso: scoperta
        sta dm_sh
        lda #DM_TOPN
        sta dm_open
        lda #DM_CYAN
        ldx #6
        jsr set_flash
        lda #SFX_HIT
        jmp sfx_play
_prot   lda #1
        sta dm_sh
        lda #DM_YEL
        sta ovp_tint
        inc dm_rc               ; rigenerazione (come l'abate)
        lda dm_rc
        cmp #DM_REGEN
        bcc _r
        lda #0
        sta dm_rc
        ldx ob_b
        lda mhp,x               ; +1, mai oltre il massimo
        cmp mhm,x
        lda mhph,x
        sbc mhmh,x
        bcs _r
        inc mhp,x
        bne _r
        inc mhph,x
        rts
_th     lda #0
        sta ovp_tint
        lda dm_wave
        cmp #3
        bcs _r
        ldx ob_b
        cmp #0
        bne _t1
        lda mwake,x             ; primo rito: appena sveglia
        beq _r
        bne _go
_t1     jsr dm_th
        bcc _r
_go     inc dm_wave
        lda #DM_STOP
        sta dm_t
        lda #DM_WHITE
        ldx #DM_STOP
        jsr set_flash
        lda #SFX_PORTAL
        jmp sfx_play

; ferma ogni feticcio vivo del piano (per tipo); C=1 se ce n'e' almeno uno. X = boss all'uscita
dm_fet:
        lda #0
        sta ob_k
        ldx lb_cnt
_l      dex
        bmi _e
        lda malive,x
        beq _l
        lda mtype,x
        cmp #DM_TYPE
        bne _l
        lda #4
        sta mstun,x
        inc ob_k
        bne _l
_e      ldx ob_b
        lda ob_k
        cmp #1
        rts

; vita dei feticci appena evocati (ob_s0, ob_s1) = vita massima del boss / 8, almeno 1
dm_fhp:
        ldx ob_b
        lda mhm,x
        sta tmp0
        lda mhmh,x
        sta tmp1
        ldy #3                  ; (24/11) / 8 (fino al 23/11 / 16)
-       lsr tmp1
        ror tmp0
        dey
        bne -
        lda tmp0
        ora tmp1
        bne +
        inc tmp0
+       ldx ob_s0
        jsr _set
        ldx ob_s1
_set    bmi _r
        lda tmp0
        sta mhp,x
        sta mhm,x
        lda tmp1
        sta mhph,x
        sta mhmh,x
_r      rts

; colpo del PG al mostro X: sul boss scoperta x2, protetta /2 (almeno 1). X conservato
dm_dmg:
        cpx ob_b
        bne _r
        lda lb_boss
        beq _r
        lda dm_open
        beq _h
        asl cb_dl
        rol cb_dh
        rts
_h      lda dm_sh
        beq _r
        lsr cb_dh
        ror cb_dl
        lda cb_dl
        ora cb_dh
        bne _r
        inc cb_dl
_r      rts

; (24/11) maledizione e feticci marci, con il boss sveglio
dm_tick2:
        jsr dm_tick
        jsr ob_alive
        bcc _x
        lda mwake,x
        bne +
_x      rts
+       lda dmh_t               ; maledizione in corso: alla fine la cadenza torna quella di prima
        beq +
        dec dmh_t
        bne +
        lda #0
        sta ovp_rate
+       lda frame
        and #3
        bne _f
        lda dmr_c               ; feticci marci
        beq +
        dec dmr_c
        bne +
        jsr dm_marc
+       lda dmh_w               ; prossima maledizione: niente conto durante avviso, maledizione, rito e scoperta
        ora dmh_t
        ora dm_t
        ora dm_open
        bne _f
        dec dmh_cd
        bne _f
        lda #DM_HEX
        sta dmh_cd
        lda #DM_HW
        sta dmh_w
        lda #DM_HCOL
        ldx #DM_HW
        jsr set_flash
_f      lda dmh_w               ; avviso: lampeggia di rosso chiaro
        beq _r
        ldx ob_b
        lda #DM_HCOL
        jsr ob_blink
        dec dmh_w
        bne _r
        lda #0
        sta ovp_tint
        ldx ob_b
        jsr ob_dist
        lda ob_adx
        cmp #DM_HR
        bcs _r
        lda ob_ady
        cmp #DM_HR
        bcs _r
        lda s_rate              ; colpito: ovp_rate = 5/8 della cadenza (cadenza x1,625)
        lsr
        sta tmp0
        lsr
        lsr
        clc
        adc tmp0
        sta ovp_rate
        lda #DM_HT
        sta dmh_t
        lda #DM_HCOL
        ldx #8
        jsr set_flash
        lda #SFX_HURT
        jmp sfx_play
_r      rts

; (24/11) i feticci ancora in piedi diventano annegati (tipo DM_ROTT: vita del tipo al piano, svegli); niente scoperta
dm_marc:
        ldx lb_cnt
_l      dex
        bmi _e
        lda malive,x
        beq _l
        lda mtype,x
        cmp #DM_TYPE
        bne _l
        lda #DM_ROTT
        sta mtype,x
        stx rt_i
        jsr mon_hp_init
        ldx rt_i
        lda #1
        sta mwake,x
        lda #0
        sta mstun,x
        beq _l
_e      lda #0
        sta dm_sh
        rts

; mostro X ucciso: C=1 = niente bottino (i feticci). X conservato
dm_kill:
        lda mtype,x
        cmp #DM_TYPE
        beq +
        clc
        rts
+       sec
        rts

        .include "ovl_boss.inc"
ovb_end
        .cerror ovb_end > OVP_END, "codice del piano 10 oltre $CFFF"
        .cerror CB2_TYPE != M_LICH, "CB2_TYPE: controllare il tipo del boss (rules.yaml)"
