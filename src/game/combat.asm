; ===================================================================
;  combat.asm - regole di combattimento d20 (docs/combattimento.md, numeri: data/rules.yaml)
;  statistiche del PG, mostri del piano, tiro per colpire, danni a 16 bit, abilita' a tempo,
;  pozioni con ricarica
; ===================================================================

; ---- variabili (non salvate; azzerate da game_start). $9318-$93FF: RAM libera verificata in VICE
        .virtual $9318
hpmax   .word ?                 ; vita massima (16 bit)
s_str   .byte ?                 ; FOR, DES, COS (valori, anello compreso): contigui (recalc_stats)
s_dex   .byte ?
s_con   .byte ?
s_mod   .byte ?                 ; modificatore dell'arma: FOR (pugnale: il migliore fra FOR e DES)
s_prof  .byte ?                 ; competenza
s_att   .byte ?                 ; tiro per colpire: competenza + mod + magia dell'arma
s_ac    .byte ?                 ; classe armatura
s_dn    .byte ?                 ; dadi dell'arma: numero, facce
s_ds    .byte ?
s_dk    .byte ?                 ; danno fisso: mod + magia dell'arma
s_rate  .byte ?                 ; cadenza dell'attacco base (fotogrammi)
s_pen   .byte ?                 ; penetrazione: - CA del bersaglio
s_crit  .byte ?                 ; critico da (20, o 19 dal livello CRIT_LVL)
s_dc    .byte ?                 ; CD del Battle Cry: 8 + competenza + mod FOR
sk_cdl  .fill SK_N              ; ricariche delle abilita' (16 bit)
sk_cdh  .fill SK_N
tmr     .fill 6                 ; durate (16 bit): 0 Rage, 2 Frenzy, 4 ricarica delle pozioni
fz_run  .byte ?                 ; Frenzy: corsa in piu' (%)
fz_acc  .byte ?
ft_dmul .byte ?                 ; mostri del piano: curva del danno (x/32)
ft_hpl  .fill N_MTYPES+1        ; vita media, CA, ATT, danno fisso, salvezza, esperienza per tipo (floor_types)
ft_hph  .fill N_MTYPES+1
ft_ac   .fill N_MTYPES+1
ft_att  .fill N_MTYPES+1
ft_dk   .fill N_MTYPES+1
ft_sv   .fill N_MTYPES+1
ft_xpl  .fill N_MTYPES+1
ft_xph  .fill N_MTYPES+1
cb_n    .byte ?                 ; dadi: numero, facce, risultato (16 bit)
cb_s    .byte ?
cb_dl   .byte ?
cb_dh   .byte ?
cb_r    .byte ?                 ; d20
cb_crit .byte ?
cb_t    .byte ?                 ; tipo del mostro
ho_i    .byte ?                 ; mostro colpito (hit_one) / che attacca (mon_attack)
ha_kind .byte ?                 ; 0 slash, 1 whirlwind, 2 battle cry, 3 smash
km_nl   .byte ?                 ; 1 = mostro troppo debole: niente esperienza ne' bottino
mw_l    .byte ?                 ; moltiplicazione 16 x 8 -> 24 bit (mu0..mu2)
mw_h    .byte ?
mw_k    .byte ?
mu0     .byte ?
mu1     .byte ?
mu2     .byte ?
wr_x    .byte ?                 ; wear: oggetto e Y salvato
wr_y    .byte ?
hud_nm  .byte ?                 ; nome mostrato nell'HUD per sk_t fotogrammi: 0..3 abilita', 4 oggetto rotto
cb_end
        .endv
        .cerror cb_end > $93a0, "variabili del combattimento oltre $939F (da $93A0: musica)"
        .cerror s_dex != s_str + 1 || s_con != s_str + 2, "s_str, s_dex, s_con devono essere contigui"
T_RAGE  = 0
T_FZ    = 2
T_POT   = 4

; ------------------------------------------------------------------ aritmetica
; A = 1..20
d20:    lda #20
        jsr rndrange
        clc
        adc #1
        rts

; cb_n dadi da cb_s facce + A -> cb_dl/cb_dh. Preserva Y.
roll_dice:
        sta cb_dl
        lda #0
        sta cb_dh
        ldx cb_n
        beq _r
_l      lda cb_s
        jsr rndrange            ; 0..facce-1 (preserva X)
        sec                     ; +1
        adc cb_dl
        sta cb_dl
        bcc +
        inc cb_dh
+       dex
        bne _l
_r      rts

; mw_l/mw_h x mw_k -> mu0..mu2 (24 bit). Usa X, preserva Y.
mul16x8:
        lda #0
        sta mu0
        sta mu1
        sta mu2
        ldx #8
_l      asl mu0
        rol mu1
        rol mu2
        asl mw_k
        bcc _n
        clc
        lda mu0
        adc mw_l
        sta mu0
        lda mu1
        adc mw_h
        sta mu1
        bcc _n
        inc mu2
_n      dex
        bne _l
        rts

; mu0..mu2 >> X
mu_shr: lsr mu2
        ror mu1
        ror mu0
        dex
        bne mu_shr
        rts

; A = valore della caratteristica (>= 10) -> modificatore (valore - 10) / 2
modv:   sec
        sbc #10
        lsr
        rts

pl_base .byte PL_STR0, PL_DEX0, PL_CON0

; (11/11) punti statistica da spendere: pl_pts[livello] - punti spesi (c_sadd) - in attesa (cs_pend, schermata C) -> A
pts_avail:
        ldx c_lvl
        cpx #PL_MAXLVL+1
        bcc +
        ldx #PL_MAXLVL
+       lda pl_pts,x
        ldx #2
-       sec
        sbc c_sadd,x
        sec
        sbc cs_pend,x
        dex
        bpl -
        tax                     ; Z = nessun punto (X = A)
        rts

; un gettone respec in piu' (al massimo RESP_MAX)
resp_add:
        lda c_resp
        cmp #RESP_MAX
        bcs +
        inc c_resp
+       rts

; X = mostro: C=1 se e' il boss con nome del piano (non il boss finale). Preserva X, Y.
mon_named:
        txa
        sec
        adc #0                  ; indice + 1
        cmp lb_boss
        bne _no
        lda mtype,x
        cmp #T_FINAL
        beq _no
        sec
        rts
_no     clc
        rts

; ------------------------------------------------------------------ PG
; caratteristiche, competenza, vita massima, attacco, danno, CA: dal livello e dall'equipaggiamento
recalc_stats:
        ldx c_lvl
        cpx #PL_MAXLVL+1
        bcc +
        ldx #PL_MAXLVL
+       stx tmp4
        lda pl_prof,x
        sta s_prof
        ldx #2                  ; (11/11) caratteristiche = base + punti spesi (c_sadd, schermata C)
-       lda pl_base,x
        clc
        adc c_sadd,x
        sta s_str,x
        dex
        bpl -
        lda s_con               ; vita = PL_HP1 + COS + (livello - 1) x (PL_HPL + mod COS)
        jsr modv
        clc
        adc #PL_HPL
        sta tmp5
        lda s_con
        clc
        adc #PL_HP1
        sta hpmax
        lda #0
        sta hpmax+1
        ldy tmp4
        beq _hd
-       dey
        beq _hd
        lda hpmax
        clc
        adc tmp5
        sta hpmax
        bcc -
        inc hpmax+1
        bne -
_hd
        ; anello: +N al modificatore della caratteristica (bonus 1 FOR, 2 DES, 3 COS) = +2N al valore
        ldx c_eq+3
        beq _nr
        ldy c_eqb+3
        beq _nr
        lda itval,x
        sta tmp5
        asl
        clc
        adc s_str-1,y
        sta s_str-1,y
        cpy #3
        bne _nr
        ldx tmp4                ; COS: vita + N x (livello + 1)
        inx
        lda #0
-       clc
        adc tmp5
        dex
        bne -
        clc
        adc hpmax
        sta hpmax
        bcc _nr
        inc hpmax+1
_nr     lda s_str
        jsr modv
        sta s_mod
        clc
        adc s_prof
        adc #8
        sta s_dc
        ldx c_eq                ; arma (08/11: tolto il pugnale "d'ufficio" se c_eq = 0; il caso senza arma non deve
                                ; esistere. Con c_eq = 0 le tabelle dell'oggetto 0 danno 0: nessun danno). Mod = FOR sempre
        lda s_mod
        clc
        adc c_eqb
        sta s_dk
        clc
        adc s_prof
        sta s_att
        lda itdn,x
        sta s_dn
        lda itds,x
        sta s_ds
        lda c_eqm               ; arma rotta (durabilita' 0, 07/11): resta in mano ma non fa danni
        beq +
        lda c_eqd
        bne +
        sta s_dn                ; (A = 0) nessun dado, nessun danno fisso
        sta s_dk
+
        lda itrate,x
        sta s_rate
        lda itpen,x
        sta s_pen
        ; CA = 10 + min(mod DES, limite dell'armatura) + armatura + scudo (magia compresa)
        lda #10
        sta tmp6
        lda #255
        sta tmp7
        ldx c_eq+1
        beq _na
        lda c_eqm+1             ; armatura rotta (durabilita' 0, 07/11): resta indossata ma non conta (ne' CA ne' limite)
        beq +
        lda c_eqd+1
        beq _na
+       lda itfl,x
        sta tmp7
        lda itval,x
        clc
        adc c_eqb+1
        adc tmp6
        sta tmp6
_na     ldx c_eq+2
        beq _ns
        lda c_eqm+2             ; scudo rotto: non conta
        beq +
        lda c_eqd+2
        beq _ns
+       ldy c_eq
        lda itfl,y
        and #1                  ; arma a due mani: lo scudo non conta
        bne _ns
        lda itval,x
        clc
        adc c_eqb+2
        adc tmp6
        sta tmp6
_ns     lda s_dex
        jsr modv
        cmp tmp7
        bcc +
        lda tmp7
+       clc
        adc tmp6
        sta s_ac
        lda #20
        ldx tmp4
        cpx #CRIT_LVL
        bcc +
        lda #19
+       sta s_crit
        jsr hp_cap
        lda #1
        sta hud_dirty
        rts

; vita attuale al massimo hpmax
hp_cap:
        lda c_hp
        cmp hpmax
        lda c_hp+1
        sbc hpmax+1
        bcs hp_full
        rts
hp_full:
        lda hpmax
        sta c_hp
        lda hpmax+1
        sta c_hp+1
        rts

; danno al PG: cb_dl/cb_dh (16 bit). godmode diverso da 0: nessun danno (cheat, docs/cheats.md)
hurt_player:
        lda godmode
        bne _s
        lda c_hp
        sec
        sbc cb_dl
        sta c_hp
        lda c_hp+1
        sbc cb_dh
        sta c_hp+1
        bcs _s
        lda #0
        sta c_hp
        sta c_hp+1
_s      lda hud_pend            ; (11/11, prestazioni) colpo subito: solo il pannello della vita (riga 21), non tutto l'HUD
        ora #1
        sta hud_pend
        lda #2
        ldx #4
        jsr set_flash
        lda #SFX_HURT
        jmp sfx_play

; tmp0/tmp1 = esperienza guadagnata (esperienza a 24 bit; un livello alla volta)
add_xp:
        lda hud_pend            ; (11/11) esperienza: solo il pannello XP (riga 22); il passaggio di livello ridisegna tutto
        ora #2
        sta hud_pend
        clc
        lda c_xp
        adc tmp0
        sta c_xp
        lda c_xp+1
        adc tmp1
        sta c_xp+1
        bcc _chk
        inc c_xp+2
_chk    lda c_lvl
        cmp #PL_MAXLVL
        bcs _done
        tax
        dex                     ; xp_n*[livello - 1] = esperienza per il livello successivo
        lda c_xp+2
        cmp xp_n2,x
        bcc _done
        bne _up
        lda c_xp+1
        cmp xp_n1,x
        bcc _done
        bne _up
        lda c_xp
        cmp xp_n0,x
        bcc _done
_up     inc c_lvl
        lda #1
        sta hud_dirty
        jsr recalc_stats
        jsr hp_full
        lda #7
        ldx #12
        jsr set_flash
        lda #SFX_LEVEL
        jsr sfx_play
        jmp _chk
_done   rts

; ------------------------------------------------------------------ mostri del piano
; statistiche per tipo al piano attuale (P = piano - piano minimo del tipo): vita media (x curva), CA, ATT,
; danno fisso, salvezza, esperienza. Da chiamare entrando in un piano (prima di init_monsters_rt).
floor_types:
        ldy cur_level
        cpy #MAXLEVEL+1
        bcc +
        ldy #MAXLEVEL
+       sty tmp4
        lda cv_dmg,y
        sta ft_dmul
        ldx #N_MTYPES
_t      stx cb_t
        lda #0
        cpx #T_FINAL
        beq _p
        lda tmp4
        sec
        sbc mt_fmin,x
        bcs +
        lda #0
+       cmp #MAXLEVEL
        bcc _p
        lda #MAXLEVEL-1
_p      tay
        sty tmp5
        lda mt_ac,x
        clc
        adc gr_ac,y
        sta ft_ac,x
        lda mt_att,x
        clc
        adc gr_att,y
        sta ft_att,x
        lda mt_dk,x
        clc
        adc gr_dmg,y
        sta ft_dk,x
        lda gr_att,y
        lsr
        clc
        adc mt_sv,x
        sta ft_sv,x
        ; esperienza = base x (4 + P x XP_PFQ) / 4
        tya
        .rept XP_PFQ-1
        clc
        adc tmp5
        .endrept
        clc
        adc #4
        sta mw_k
        lda mt_xp_lo,x
        sta mw_l
        lda mt_xp_hi,x
        sta mw_h
        jsr mul16x8
        ldx #2
        jsr mu_shr
        ldx cb_t
        lda mu0
        sta ft_xpl,x
        lda mu1
        sta ft_xph,x
        ; vita = (media + dadi in piu' x media del dado) x curva del piano / 32
        ldy tmp5
        lda gr_hpd,y
        sta mw_k
        lda mt_hpd2,x
        sta mw_l
        lda #0
        sta mw_h
        jsr mul16x8             ; dadi x (facce + 1) = 2 x media
        ldx cb_t
        lda mu0
        lsr
        clc
        adc mt_hp_lo,x
        sta mw_l
        lda mt_hp_hi,x
        adc #0
        sta mw_h
        ldy tmp4
        lda cv_hp,y
        sta mw_k
        jsr mul16x8
        ldx #5
        jsr mu_shr
        ldx cb_t
        lda mu0
        sta ft_hpl,x
        lda mu1
        sta ft_hph,x
        dex
        beq +
        jmp _t
+       rts
        .cerror XP_PFQ < 1, "xp_per_floor: almeno 0,25"

; vita del mostro rt_i alla nascita: media del tipo x (96..160)/128 (+-25%); boss con nome x BOSS_HPH/2
mon_hp_init:
        ldx rt_i
        ldy mtype,x
        lda ft_hpl,y
        sta mw_l
        lda ft_hph,y
        sta mw_h
        lda #65
        jsr rndrange
        clc
        adc #96
        sta mw_k
        jsr mul16x8
        ldx #7
        jsr mu_shr
        ldx rt_i
        jsr mon_named
        bcc _nb
        lda mu0
        sta mw_l
        lda mu1
        sta mw_h
        lda #BOSS_HPH
        sta mw_k
        jsr mul16x8
        ldx #1
        jsr mu_shr
_nb     ldx rt_i
        lda mu0
        ora mu1
        bne +
        inc mu0                 ; almeno 1
+       lda mu0
        sta mhp,x
        sta mhm,x
        lda mu1
        sta mhph,x
        sta mhmh,x
        rts

; X = mostro a contatto: un attacco (d20 + ATT contro la CA del PG; 1 manca, 20 critico: dadi x 2).
; Danno x curva del piano / 32, dimezzato da Rage, almeno 1. Preserva X.
mon_attack:
        lda bar_t               ; nessun bersaglio nella barra: mostra chi attacca
        bne +
        jsr bar_target
+       stx ho_i
        ldy mtype,x
        sty cb_t
        jsr mon_named           ; (C) - lda non tocca C
        lda ft_att,y
        bcc +
        adc #BOSS_ATT-1         ; (C=1)
+       sta tmp7
        jsr d20
        cmp #1
        beq _r0
        ldy #0
        sty cb_crit
        cmp #20
        beq _cr
        clc
        adc tmp7
        cmp s_ac
        bcs _hit
_r0     jmp _r
_cr     inc cb_crit
_hit    ldy cb_t
        lda mt_dn,y
        ldx cb_crit
        beq +
        asl
+       sta cb_n
        lda mt_ds,y
        sta cb_s
        lda ft_dk,y
        jsr roll_dice
        lda cb_dl
        sta mw_l
        lda cb_dh
        sta mw_h
        lda ft_dmul
        sta mw_k
        jsr mul16x8
        ldx #5
        jsr mu_shr
        lda tmr+T_RAGE          ; Rage: danni subiti dimezzati
        ora tmr+T_RAGE+1
        beq +
        lsr mu1
        ror mu0
+       lda mu0
        ora mu1
        bne +
        inc mu0
+       lda mu0
        sta cb_dl
        lda mu1
        sta cb_dh
        jsr hurt_player
        lda #WEAR_A             ; usura dell'armatura e dello scudo (colpo subito)
        ldx #1
        jsr wear
        ldx c_eq
        lda itfl,x
        and #1                  ; con un'arma a due mani lo scudo non conta e non si usura
        bne _r
        lda #WEAR_S
        ldx #2
        jsr wear
_r      ldx ho_i
        rts

; usura: oggetto indossato X (0 arma, 1 armatura, 2 scudo) perde 1 punto con probabilita' 1/A; a 0 si rompe:
; resta equipaggiato ma perde ogni effetto (07/11: arma danno 0, armatura e scudo niente CA; recalc_stats), nome in
; rosso, icona fissa nell'HUD; lampo rosso, avviso "broken". Massimo 0 = non si usura. X e Y conservati.
wear:
        stx wr_x
        sty wr_y
        ldy c_eqm,x
        beq _r
        lda c_eqd,x             ; gia' rotto: niente (resta a 0)
        beq _r
        jsr rndrange
        bne _r
        ldx wr_x
        dec c_eqd,x
        bne _r
        jsr recalc_stats
        lda #4
        sta hud_nm              ; "broken"
        lda #SK_SHOW
        sta sk_t
        lda #1
        sta hud_dirty
        lda #SFX_DIE
        jsr sfx_play
        lda #2
        ldx #10
        jsr set_flash
_r      ldx wr_x
        ldy wr_y
        rts

; ------------------------------------------------------------------ attacco del PG
; X = mostro nell'area, ha_kind = abilita'. Preserva X.
;   slash / whirlwind: d20 + ATT >= CA - penetrazione (1 manca, >= s_crit critico: dadi x 2), blocco da colpo
;   (non ai boss); smash: vantaggio (2 d20), dadi x 2, stordimento SM_STUN anche ai boss;
;   battle cry: d20 + salvezza >= CD resiste, altrimenti fermo BC_STUN fotogrammi
hit_one:
        stx ho_i
        lda #1
        sta mwake,x
        ldy mtype,x
        sty cb_t
        lda ha_kind
        cmp #2
        bne _att
        jsr d20
        clc
        adc ft_sv,y
        cmp s_dc
        bcs _x
        lda #BC_STUN
        sta mstun,x
_x      rts
_att    jsr mon_named
        lda ft_ac,y
        bcc +
        adc #BOSS_AC-1          ; (C=1)
+       sec
        sbc s_pen
        bcs +
        lda #0
+       sta tmp7
        jsr d20
        sta cb_r
        lda ha_kind
        cmp #3
        bne _nv
        jsr d20                 ; Smash: vantaggio
        cmp cb_r
        bcc _nv
        sta cb_r
_nv     lda #0
        sta cb_crit
        lda cb_r
        cmp #1
        beq _x
        cmp s_crit
        bcs _crit
        clc
        adc s_att
        cmp tmp7
        bcs _hit
        rts
_crit   inc cb_crit
_hit    lda s_dn                ; arma rotta: il colpo arriva ma non fa nulla (niente danno, stordimento, usura)
        ora s_dk
        bne +
        jmp _sx
+       lda s_dn                ; dadi: x 2 critico, x 2 Smash
        ldy cb_crit
        beq +
        asl
+       ldy ha_kind
        cpy #3
        bne +
        asl
+       sta cb_n
        lda s_ds
        sta cb_s
        lda s_dk
        jsr roll_dice
        jsr fz_hit
        lda #WEAR_W             ; usura dell'arma (colpo a segno)
        ldx #0
        jsr wear
        ldx ho_i
        lda mhp,x
        sec
        sbc cb_dl
        sta mhp,x
        lda mhph,x
        sbc cb_dh
        sta mhph,x
        bcc _kill
        ora mhp,x
        beq _kill
        jsr bar_target
        lda ha_kind
        cmp #3
        bne _bl
        lda #SM_STUN
        bne _st
_bl     txa                     ; blocco da colpo: non al boss del piano ne' al boss finale
        clc
        adc #1
        cmp lb_boss
        beq _sx
        lda #STUN_HIT
_st     cmp mstun,x
        bcc _sx
        sta mstun,x
_sx     lda #SFX_HIT
        jmp sfx_play
_kill   lda #0
        sta mhp,x
        sta mhph,x
        jmp kill_monster

; colpo a segno durante Frenzy: corsa +FZ_RUN1% al primo, +FZ_RUN2% ai successivi (max FZ_RUNMAX)
fz_hit:
        lda tmr+T_FZ
        ora tmr+T_FZ+1
        beq _r
        lda fz_run
        beq _f
        clc
        adc #FZ_RUN2
        bne _s
_f      lda #FZ_RUN1
_s      cmp #FZ_RUNMAX+1
        bcc +
        lda #FZ_RUNMAX
+       sta fz_run
_r      rts

; ------------------------------------------------------------------ abilita' e tempi
; ogni fotogramma: ricariche delle abilita', durate di Rage / Frenzy, ricarica delle pozioni
tick_timers:
        ldx #SK_N-1
_cd     lda sk_cdl,x
        ora sk_cdh,x
        beq _z
        lda sk_cdl,x
        bne +
        dec sk_cdh,x
+       dec sk_cdl,x
        lda sk_cdl,x
        ora sk_cdh,x
        bne _z
        lda hud_pend            ; abilita' di nuovo pronta: solo la riga 23 (11/11)
        ora #4
        sta hud_pend
_z      dex
        bpl _cd
        ldx #4
_tm     lda tmr,x
        ora tmr+1,x
        beq _tz
        lda tmr,x
        bne +
        dec tmr+1,x
+       dec tmr,x
        lda tmr,x
        ora tmr+1,x
        bne _tz
        lda hud_pend            ; fine di Rage / Frenzy / ricarica delle pozioni: riga 23 e cintura (11/11)
        ora #$0c
        sta hud_pend
        cpx #T_FZ               ; fine di Frenzy: corsa normale
        bne _tz
        lda #0
        sta fz_run
_tz     dex
        dex
        bpl _tm
        rts

; X = 4 Rage (tasto R) / 5 Frenzy (tasto F): attivazione immediata se il livello basta e la ricarica e' finita
buff_act:
        lda c_lvl
        cmp sk_req,x
        bcc _r
        lda sk_cdl,x
        ora sk_cdh,x
        bne _r
        lda sk_cd_lo,x
        sta sk_cdl,x
        lda sk_cd_hi,x
        sta sk_cdh,x
        cpx #4
        bne _fz
        lda #<RAGE_DUR
        sta tmr+T_RAGE
        lda #>RAGE_DUR
        sta tmr+T_RAGE+1
        lda #2
        bne _s
_fz     lda #<FZ_DUR
        sta tmr+T_FZ
        lda #>FZ_DUR
        sta tmr+T_FZ+1
        lda #0
        sta fz_run
        sta fz_acc
        lda #7
_s      ldx #10
        jsr set_flash
        lda #1
        sta hud_dirty
        lda #SFX_PORTAL
        jmp sfx_play
_r      rts

; Frenzy: passi in piu' (pdx/pdy) secondo fz_run: +2 px x fz_run / 100 a fotogramma in media
fz_move:
        lda fz_run
        beq _r
        lda pdx
        ora pdy
        beq _r
        lda fz_acc              ; accumulatore in 1/50 di pixel: ogni 50 un pixel in piu' per asse
        clc                     ; (fz_run 100 = +2 px a fotogramma = +100% sul passo base di 2 px)
        adc fz_run
_px     cmp #50
        bcc _s
        sbc #50
        ldx #0                  ; 1 px in piu' su ogni asse in movimento
_a      ldy pdx,x
        beq _n
        bmi _m
        inc pdx,x
        bne _n
_m      dec pdx,x
_n      inx
        cpx #2
        bne _a
        jmp _px
_s      sta fz_acc
_r      rts
        .cerror pdy != pdx + 1, "pdx e pdy devono essere contigui (fz_move)"

; ------------------------------------------------------------------ pozioni
; X = posto della cintura (0..3): beve la pozione (se la ricarica e' finita e la vita non e' piena)
; (11/11, O5) cura di una pozione al livello del PG: Y = oggetto -> mu0/mu1 = itval + itdn x c_lvl, A = mu0
; (Y conservato: mul16x8 non lo tocca). Usata da drink e dalla scheda dell'oggetto (ui.asm)
pot_heal:
        lda itdn,y
        sta mw_l
        lda #0
        sta mw_h
        lda c_lvl
        sta mw_k
        jsr mul16x8
        lda itval,y
        clc
        adc mu0
        sta mu0
        bcc +
        inc mu1
+       rts

use_potion:
        ldy c_beltt,x
        beq _no
        jsr drink
        bcs _no
        lda #0
        sta c_beltt,x
_no     rts

; Y = pozione: cura itval + itdn x livello (16 bit, fino alla vita massima), poi blocco di tutte le pozioni
; per itrate x 2 fotogrammi. C=1 (niente fatto) se in ricarica o con la vita piena. Preserva X, Y.
drink:
        lda tmr+T_POT
        ora tmr+T_POT+1
        bne _no
        lda c_hp
        cmp hpmax
        lda c_hp+1
        sbc hpmax+1
        bcs _no
        txa
        pha
        jsr pot_heal            ; A = mu0
        clc
        adc c_hp
        sta c_hp
        lda mu1
        adc c_hp+1
        sta c_hp+1
        jsr hp_cap
        lda itrate,y
        asl
        sta tmr+T_POT
        lda #0
        rol
        sta tmr+T_POT+1
        lda hud_pend            ; pozione bevuta: vita e cintura (11/11)
        ora #$09
        sta hud_pend
        lda #SFX_PICK
        jsr sfx_play
        pla
        tax
        clc
        rts
_no     sec
        rts
