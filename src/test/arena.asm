; =============================================================================
;  arena.asm - modulo ARENA (out/work/arena.prg, a AR_BASE = $C900) per i test di combattimento
;
;  Si usa SOLO con la build arena del gioco (out/work/arena_game.prg, ARENA=1): stessa logica di
;  combattimento del gioco vero, ma niente loader, menu, villaggio, disco, zaino, drop.
;  Comandato da tools/vice/arena.py attraverso il monitor di VICE:
;    1. carica arena_game.prg, arena.prg e il tema GFXn a GFX_DUN_AT (RAM sotto il KERNAL, indirizzo del file)
;    2. scrive il blocco parametri (PAR) e fa partire game_start
;    3. il modulo esegue PAR_FIGHTS combattimenti uno dopo l'altro e si ferma su ar_halt
;    4. lo script legge il blocco risultati (RES) e il registro dei combattimenti (LOG)
;  Stanza unica 44x44 al centro della mappa; nessun seed: il generatore casuale parte da un
;  valore fisso, quindi gli stessi parametri danno sempre gli stessi risultati.
;
;  Fase 1 (05/11): PG e mostri adiacenti; il bot non si sposta (BOT 0): si gira verso il mostro
;  piu' vicino e attacca. BOT 1: si avvicina al mostro piu' vicino (per le fasi successive).
; =============================================================================
        .include "../../out/work/arena_game.lbl"
        .enc "none"

PAR      = $cf00                ; parametri (scritti da tools/vice/arena.py)
PAR_LVL    = PAR+0              ; piano 1..MAXLEVEL (statistiche dei mostri, tema grafico)
PAR_PLVL   = PAR+1              ; livello del PG 1..20
PAR_EQ     = PAR+2              ; 4 id: arma, armatura, scudo, anello (0 = niente; l'arma c'e' sempre)
PAR_EQB    = PAR+6              ; 4 affissi (21/11 sera): prefisso di arma, armatura, scudo (MAG_W/MAG_A); anello: suffisso (RSX_)
PAR_BELTT  = PAR+10             ; cintura: 4 posti, una pozione ciascuno (id, 0 = vuoto)
PAR_DUR    = PAR+14             ; durabilita' dell'arma all'inizio della serie (= massimo); 0 = non si usura
PAR_SADD   = PAR+15             ; (11/11) punti statistica spesi in FOR, DES, COS (c_sadd: PG di riferimento)
PAR_NMON   = PAR+18             ; mostri 1..8
PAR_BOSS   = PAR+19             ; 0 = nessun boss, n = il mostro n-1 e' un boss con nome
PAR_MTYPE  = PAR+20             ; 8 tipi (M_*)
PAR_MX     = PAR+28             ; 8 caselle X (0 = automatica, attorno al PG)
PAR_MY     = PAR+36             ; 8 caselle Y
PAR_PX     = PAR+44             ; casella del PG (0 = 24)
PAR_PY     = PAR+45
PAR_FIGHTS = PAR+46             ; combattimenti da eseguire (1..255)
PAR_MAXF   = PAR+47             ; limite in fotogrammi per combattimento (16 bit)
PAR_FAST   = PAR+49             ; 1 = senza attesa del raster (piu' veloce, stessa logica)
PAR_SKILLS = PAR+50             ; abilita' permesse: bit 0 slash, 1 whirlwind, 2 battle cry, 3 smash, 4 rage, 5 frenzy
PAR_POT    = PAR+51             ; beve sotto vita * PAR_POT / 256 (0 = mai)
PAR_WAKE   = PAR+52             ; 1 = mostri gia' svegli
PAR_BOT    = PAR+53             ; 0 = fermo, si gira e attacca; 1 = si avvicina
PAR_SEED   = PAR+54             ; (23/11) seme del generatore casuale (16 bit; arena.py: $1234 di solito, un altro a ogni
                                ; combattimento dei piani con il codice del piano, che si rilegge a ogni combattimento)
PAR_LEN    = 56

RES      = $cf40                ; risultati (azzerati all'avvio)
RES_DONE   = RES+0              ; combattimenti finiti
RES_WIN    = RES+1
RES_LOSE   = RES+2
RES_TIME   = RES+3
RES_FRAMES = RES+4              ; 24 bit: somma dei fotogrammi
RES_HPEND  = RES+7              ; 16 bit: somma della vita rimasta al PG (saturata)
RES_XP     = RES+9              ; 24 bit
RES_KILLS  = RES+12             ; 16 bit
RES_DEALT  = RES+14             ; 24 bit: danno inflitto (vita tolta ai mostri, senza eccesso)
RES_TAKEN  = RES+17             ; 24 bit: danno subito
RES_HEALED = RES+20             ; 16 bit: vita recuperata con le pozioni
RES_POTS   = RES+22             ; 16 bit: pozioni bevute
RES_HPMAX  = RES+24             ; statistiche del PG (ultimo combattimento): vita massima (16 bit), ATT, CA,
RES_ATT    = RES+26             ; dadi (numero, facce), danno fisso, cadenza
RES_AC     = RES+27
RES_DN     = RES+28
RES_DS     = RES+29
RES_DK     = RES+30
RES_RATE   = RES+31
RES_M0HP   = RES+32             ; mostro 0 all'inizio dell'ultimo combattimento: vita (16 bit), CA, ATT del tipo
RES_M0AC   = RES+34
RES_M0ATT  = RES+35
RES_STATUS = RES+36             ; 1 = serie finita
RES_WDUR   = RES+37             ; durabilita' dell'arma a fine serie (0 = rotta, se PAR_DUR > 0)
RES_WEQ    = RES+38             ; arma a fine serie (rotta: la stessa, con durabilita' 0)
RES_LEN    = 39
LOG      = $cf80                ; 32 combattimenti x 4 byte: esito (1 vinto, 2 perso, 3 tempo), fotogrammi (16 bit), vita finale (byte basso)
LOG_N    = 32

        * = AR_BASE
        jmp arena_main
        jmp arena_input
        jmp arena_kill
        jmp arena_dead
        jmp arena_wait

; ---------------------------------------------------------------- avvio (da game_start)
arena_main:
        ldx #RES_LEN-1
        lda #0
_z      sta RES,x
        dex
        bpl _z
        lda PAR_SEED            ; generatore casuale: valore dato (prove ripetibili; arena.py: $1234)
        sta rnd
        lda PAR_SEED+1
        sta rnd+1
        lda PAR_LVL
        sta cur_level
        sta c_loc
        jsr floor_types         ; statistiche dei mostri del piano
        jsr irq_off
        lda cur_level           ; tema gia' a GFX_DUN_AT (caricato da tools/vice/arena.py)
        jsr lvl_theme
        lda #1
        jsr gfx_install
        jsr clear_map           ; stanza 44x44: muri attorno, pavimento dentro
        ldx #2
_ry     lda maprow_lo,x
        sta ptr0
        lda maprow_hi,x
        sta ptr0+1
        ldy #2
        lda #T_FLOOR
_rx     sta (ptr0),y
        iny
        cpy #MAPW-2
        bne _rx
        inx
        cpx #MAPH-2
        bne _ry
        lda #GEN_WALLS          ; post_walls e' sotto l'I/O (gen_io.asm)
        jsr gen_call
        lda #$0f                ; volume per gli effetti sonori (nessuna musica)
        sta $d418
        lda PAR_DUR             ; durabilita' dell'arma per tutta la serie (0 = non si usura: serie ripetibili)
        sta c_eqd
        sta c_eqm

; ---------------------------------------------------------------- un combattimento
ar_fight:
        ldx #$ff
        txs
        jsr irq_off
        jsr clear_lvlblk
        lda cur_level
        sta lb_lvl
        ; PG
        lda PAR_PLVL
        sta c_lvl
        lda #QT_CHAIN           ; (23/11, Q15) catena finita: le abilita' le decide solo il livello, come nel simulatore
        sta q_step
        ldx #2
-       lda PAR_SADD,x
        sta c_sadd,x
        dex
        bpl -
        ldx #3
_e      lda PAR_EQ,x
        sta c_eq,x
        lda PAR_EQB,x
        cpx #3                  ; (21/11 sera) anello: il byte e' il suffisso
        bne +
        sta c_eqs+3
        lda #0
+       sta c_eqb,x
        lda PAR_BELTT,x
        sta c_beltt,x
        dex
        bpl _e
        ldx #SK_N-1             ; (arma rotta in un combattimento precedente: c_eqd resta 0, danno 0; 07/11)             ; ricariche, Rage, Frenzy, pozioni
        lda #0
_k      sta sk_cdl,x
        sta sk_cdh,x
        dex
        bpl _k
        ldx #5
_tm     sta tmr,x
        dex
        bpl _tm
        sta fz_run
        sta c_skill
        sta gcd
        sta bar_m
        sta bar_t
        jsr recalc_stats
        jsr hp_full
        lda c_hp
        sta ar_hp
        lda c_hp+1
        sta ar_hp+1
        lda PAR_PX
        bne +
        lda #24
+       sta ar_px
        lda PAR_PY
        bne +
        lda #24
+       sta ar_py
        lda ar_px
        jsr tile_to_pix
        lda tmp0
        sta px
        lda tmp1
        sta px+1
        lda ar_py
        jsr tile_to_pix
        lda tmp0
        sta py
        lda tmp1
        sta py+1
        lda #$ff
        sta lptx
        sta lpty
        lda #0
        sta pdx
        sta pdy
        sta fx_timer
        lda #3                  ; rivolto a destra (verso il primo mostro automatico)
        sta pdir
        ; mostri
        lda PAR_NMON
        sta lb_cnt
        lda PAR_BOSS
        sta lb_boss
        ldx #0
_m      lda PAR_MTYPE,x
        sta mtype,x
        lda #1
        sta malive,x
        lda PAR_MX,x
        bne _mx
        lda ar_px
        clc
        adc ar_ofx,x
_mx     sta mix,x
        lda PAR_MY,x
        bne _my
        lda ar_py
        clc
        adc ar_ofy,x
_my     sta miy,x
        inx
        cpx lb_cnt
        bne _m
        ldx #31                 ; stato di movimento rimasto dal combattimento precedente
        lda #0
_mf     sta mfar,x
        dex
        bpl _mf
        jsr init_monsters_rt
        jsr ovp_init            ; (23/11) codice del piano (boss dei capitoli, piano 20), se arena.py lo ha caricato (ovp_ok)
        ldx lb_cnt
        dex
_w      lda PAR_WAKE
        sta mwake,x
        dex
        bpl _w
        lda #0
        sta ar_f
        sta ar_f+1
        sta ar_pots
        lda mhp                 ; mostro 0 all'inizio
        sta RES_M0HP
        lda mhph
        sta RES_M0HP+1
        ldy mtype
        lda ft_ac,y
        sta RES_M0AC
        lda ft_att,y
        sta RES_M0ATT
        lda hpmax               ; statistiche del PG
        sta RES_HPMAX
        lda hpmax+1
        sta RES_HPMAX+1
        ldx #5
_st     lda s_att,x
        sta RES_ATT,x
        dex
        bpl _st
        jsr ui_exit             ; disegno completo, HUD, IRQ di nuovo attivi
        jmp main_loop

; caselle automatiche dei mostri attorno al PG: destra, sinistra, sopra, sotto, diagonali
ar_ofx  .char 1, -1, 0, 0, 1, -1, 1, -1
ar_ofy  .char 0, 0, -1, 1, -1, -1, 1, 1

arena_wait:
        lda PAR_FAST
        bne _x
        jmp wait_vblank
_x      rts

; ---------------------------------------------------------------- ogni fotogramma
arena_input:
        inc ar_f                ; tempo del combattimento
        bne +
        inc ar_f+1
+       lda ar_hp               ; danno subito / vita recuperata dall'ultimo fotogramma (16 bit)
        sec
        sbc c_hp
        sta tmp0
        lda ar_hp+1
        sbc c_hp+1
        sta tmp1
        ora tmp0
        beq _hs
        bcc _heal               ; vita aumentata
        lda tmp0
        clc
        adc RES_TAKEN
        sta RES_TAKEN
        lda tmp1
        adc RES_TAKEN+1
        sta RES_TAKEN+1
        bcc _h1
        inc RES_TAKEN+2
        jmp _h1
_heal   lda #0
        sec
        sbc tmp0
        clc
        adc RES_HEALED
        sta RES_HEALED
        lda #0
        sbc tmp1
        adc RES_HEALED+1
        sta RES_HEALED+1
_h1     lda c_hp
        sta ar_hp
        lda c_hp+1
        sta ar_hp+1
_hs     lda ar_f+1              ; tempo scaduto?
        cmp PAR_MAXF+1
        bcc _t
        bne _to
        lda ar_f
        cmp PAR_MAXF
        bcc _t
_to     lda #3
        jmp ar_end
_t      jsr ar_target           ; mostro piu' vicino (nessuno vivo: vinto)
        bcc _bot
        lda #1
        jmp ar_end
_bot    lda #0
        sta joy
        jsr ar_potion
        jsr ar_skill
        ; direzione verso il bersaglio: asse con distanza maggiore
        lda ar_ady
        cmp ar_adx
        bcs _vy
        lda ar_dxs              ; orizzontale
        bmi _lf
        lda #$08
        bne _dir
_lf     lda #$04
        bne _dir
_vy     lda ar_dys
        bmi _up
        lda #$02
        bne _dir
_up     lda #$01
_dir    sta ar_j
        lda ar_adx              ; a contatto? (asse maggiore <= 24 px, minore <= 14 px)
        cmp ar_ady
        bcs +
        lda ar_ady
+       cmp #25
        bcs _far
        lda ar_adx
        cmp ar_ady
        bcc +
        lda ar_ady
+       cmp #15
        bcs _far
        lda ar_j                ; si gira (la casella del mostro e' occupata: non si muove) e colpisce
        ora #$10
        sta joy
        rts
_far    lda PAR_BOT             ; lontano: fermo (BOT 0) o si avvicina (BOT 1)
        beq _x
        lda ar_j
        sta joy
_x      rts

; mostro vivo piu' vicino -> ar_t, distanze ar_adx/ar_ady (0..255, saturate), segni ar_dxs/ar_dys.
; Conta anche i mostri entro 40 px (ar_near). C=1 se nessuno e' vivo.
ar_target:
        lda #$ff
        sta ar_best
        sta ar_t
        lda #0
        sta ar_near
        ldx #0
_l      cpx lb_cnt
        bcs _e
        lda malive,x
        beq _n
        lda mxl,x
        sec
        sbc px
        sta tmp0
        lda mxh,x
        sbc px+1
        sta tmp1
        jsr ar_abs              ; A = |dx| saturato, tmp2 = segno
        sta tmp3
        lda tmp2
        sta tmp4
        lda myl,x
        sec
        sbc py
        sta tmp0
        lda myh,x
        sbc py+1
        sta tmp1
        jsr ar_abs
        sta tmp5
        cmp #40                 ; vicino (entro 40 px su entrambi gli assi)
        bcs +
        lda tmp3
        cmp #40
        bcs +
        inc ar_near
+       lda tmp3                ; distanza = |dx| + |dy| / 2 (saturata)
        lsr
        sta tmp6
        lda tmp5
        lsr
        clc
        adc tmp6
        cmp ar_best
        bcs _n
        sta ar_best
        stx ar_t
        lda tmp3
        sta ar_adx
        lda tmp4
        sta ar_dxs
        lda tmp5
        sta ar_ady
        lda tmp2
        sta ar_dys
_n      inx
        bne _l
_e      lda ar_t
        cmp #$ff
        beq _none
        clc
        rts
_none   sec
        rts

; tmp0/tmp1 (16 bit con segno) -> A = valore assoluto saturato a 255, tmp2 = $00 positivo / $ff negativo
ar_abs:
        lda tmp1
        sta tmp2
        bpl _p
        lda #0
        sec
        sbc tmp0
        sta tmp0
        lda #0
        sbc tmp1
        sta tmp1
_p      lda tmp1
        beq _s
        lda #255
        rts
_s      lda tmp0
        rts

; abilita': Rage e Frenzy appena pronte (se permesse); poi la migliore pronta e permessa (smash, whirlwind se
; >= 2 vicini, battle cry se >= 2 vicini), poi slash
ar_skill:
        ldx #4
_b      lda ar_skb,x
        and PAR_SKILLS
        beq _bn
        txa
        pha
        jsr buff_act            ; (niente se livello o ricarica non lo permettono)
        pla
        tax
_bn     inx
        cpx #6
        bne _b
        ldx #3
_l      lda ar_skb,x
        and PAR_SKILLS
        beq _n
        jsr sk_ok
        bcc _n
        lda sk_cdl,x
        ora sk_cdh,x
        bne _n
        cpx #1                  ; whirlwind e battle cry: solo con almeno 2 mostri vicini
        beq _two
        cpx #2
        bne _ok
_two    lda ar_near
        cmp #2
        bcc _n
_ok     stx c_skill
        rts
_n      dex
        bne _l
        stx c_skill             ; slash
        rts
ar_skb  .byte 1, 2, 4, 8, 16, 32

; pozione: sotto la soglia beve dalla prima colonna della cintura che ne ha
ar_potion:
        lda PAR_POT
        beq _x
        sta mw_k                ; soglia = vita massima x PAR_POT / 256
        lda hpmax
        sta mw_l
        lda hpmax+1
        sta mw_h
        jsr mul16x8
        lda c_hp
        cmp mu1
        lda c_hp+1
        sbc mu2
        bcs _x
        ldx #0
_f      lda c_beltt,x
        bne _use
        inx
        cpx #4
        bne _f
_x      rts
_use    stx tmp7
        jsr use_potion
        ldx tmp7
        lda c_beltt,x
        bne _x
        inc RES_POTS
        bne _x
        inc RES_POTS+1
        rts

; ---------------------------------------------------------------- eventi dal gioco
arena_kill:                        ; tmp0/tmp1 = esperienza del mostro ucciso
        clc
        lda RES_XP
        adc tmp0
        sta RES_XP
        lda RES_XP+1
        adc tmp1
        sta RES_XP+1
        bcc +
        inc RES_XP+2
+       inc RES_KILLS
        bne +
        inc RES_KILLS+1
+       rts

arena_dead:
        lda #2
        ; (prosegue in ar_end)

; ---------------------------------------------------------------- fine combattimento: A = esito
ar_end:
        sta ar_res
        ldx #$ff
        txs
        jsr irq_off
        ldx ar_res              ; conteggi per esito
        inc RES_DONE,x
        lda RES_FRAMES          ; tempo
        clc
        adc ar_f
        sta RES_FRAMES
        lda RES_FRAMES+1
        adc ar_f+1
        sta RES_FRAMES+1
        bcc +
        inc RES_FRAMES+2
+       lda RES_HPEND           ; vita rimasta (16 bit, saturata)
        clc
        adc c_hp
        sta RES_HPEND
        lda RES_HPEND+1
        adc c_hp+1
        bcc +
        lda #$ff
        sta RES_HPEND
+       sta RES_HPEND+1
+       ldx #0                  ; danno inflitto: vita massima dei morti + vita tolta ai vivi
_d      cpx lb_cnt
        bcs _dd
        lda mhm,x               ; vita massima - vita attuale (morti: vita attuale 0)
        sec
        sbc mhp,x
        sta tmp0
        lda mhmh,x
        sbc mhph,x
        sta tmp1
        lda malive,x
        bne _add
        lda mhm,x
        sta tmp0
        lda mhmh,x
        sta tmp1
_add    lda tmp0
        clc
        adc RES_DEALT
        sta RES_DEALT
        lda tmp1
        adc RES_DEALT+1
        sta RES_DEALT+1
        bcc _dn
        inc RES_DEALT+2
_dn     inx
        bne _d
_dd     lda RES_DONE            ; registro (primi LOG_N combattimenti)
        cmp #LOG_N
        bcs _nl
        asl
        asl
        tax
        lda ar_res
        sta LOG,x
        lda ar_f
        sta LOG+1,x
        lda ar_f+1
        sta LOG+2,x
        lda c_hp
        sta LOG+3,x
_nl     inc RES_DONE
        lda RES_DONE
        cmp PAR_FIGHTS
        bcs _fin
        jmp ar_fight
_fin    lda #1
        sta RES_STATUS
        lda c_eqd
        sta RES_WDUR
        lda c_eq
        sta RES_WEQ
        jsr irq_on
ar_halt:
        jmp ar_halt             ; tools/vice/arena.py si ferma qui (breakpoint)

; ---------------------------------------------------------------- variabili
ar_f     .word 0
ar_hp    .word 0
ar_px    .byte 0
ar_py    .byte 0
ar_res   .byte 0
ar_pots  .byte 0
ar_t     .byte 0
ar_best  .byte 0
ar_near  .byte 0
ar_adx   .byte 0
ar_ady   .byte 0
ar_dxs   .byte 0
ar_dys   .byte 0
ar_j     .byte 0
ar_end_  = *
        .cerror ar_end_ > PAR, "modulo arena oltre $CEFF (blocco parametri)"
