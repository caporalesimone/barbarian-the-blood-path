; ===================================================================
;  cheats/menu.asm - menu dei trucchi per i test (15/11, richiesta del committente): voce "cheats" del menu di gioco
;  (RUN/STOP). (17/11) Modulo su file: CHEATS sul disco (src/cheats.asm), caricato a CHT_AT (= SCR_B) da cheat_menu di GAME
;  quando si apre ed eseguito; finisce sempre con un salto nel gioco. Solo con CHEATS = 1 (debug e test): la release non ha
;  ne' il file ne' la voce del menu ne' cheat_menu (src/game/ui.asm, game.asm; test CHEAT-22).
;  Voci: god mode (on/off, byte godmode), level up (esperienza alla soglia del livello dopo, poi add_xp: il passaggio
;  di livello normale), respec token (resp_add), next level (come le scale; piano del boss: boss ucciso e ritorno al
;  villaggio; villaggio: primo piano come la cripta), next chapter (capitolo dopo sbloccato e chap_travel, che salva).
;  (18/11, committente) gold +1000: a ogni Fire 1000 monete addosso (add_gold16: al massimo GOLD_MAX, il resto nel baule
;  della locanda lo si porta a mano).
;  Fire = fai, RUN/STOP = menu di gioco, W/S o joystick = scegli; la riga 23 conferma.
; ===================================================================
        .enc "screen"
CT_N    = 6

ct_menu:
        lda #CT_N
        sta ui_n
        jsr nav_init
        jsr ui_begin
        lda #4
        sta ti_row
        lda #<gm3               ; titolo = testo della voce del menu di gioco ("cheats")
        ldx #>gm3
        ldy #0
        jsr ui_title
        jsr nav_help
        jsr ui_labels           ; voci a x = 15, righe 8, 10, ..., 16 (come il menu di gioco)
        .byte 15,8
        #t5 "god mode:"
        .byte 15,10
        #t5 "level up"
        .byte 15,12
        #t5 "respec token"
        .byte 15,14
        #t5 "next level"
        .byte 15,16
        #t5 "next chapter"
        .byte 15,18
        #t5 "gold +1000"
        .byte $ff
_dr     ldx #CT_N-1             ; '>' sulla voce del cursore
_l      stx tmp3
        txa
        asl
        adc #8
        tay
        ldx #13
        jsr ui_at
        ldx tmp3
        jsr ui_mark
        dex
        bpl _l
        #at 25,8                ; stato del god mode dopo "god mode:"
        lda godmode
        beq +
        #msg "on "
        jmp _in
+       #msg "off"
_in     jsr ui_nav
        cmp #NAV_MOVE
        beq _dr
        cmp #NAV_BACK
        bne +
        jmp ui_gamemenu
+       cmp #NAV_FIRE
        bne _in
        jsr msg23               ; riga dei messaggi pulita, cursore a (1,23)
        lda ui_cur
        bne _c1
        lda godmode             ; 0 god mode: acceso / spento
        eor #1
        sta godmode
        jmp _dr                 ; (lo stato acceso / spento si legge sulla voce)
_c1     cmp #1
        bne _c2
        lda c_lvl               ; 1 level up: esperienza = soglia del livello dopo, poi il passaggio normale (add_xp:
        cmp #PL_MAXLVL          ; livello, statistiche, vita piena, lampo, suono; punti statistica da pl_pts)
        bcs _max
        tax
        dex
        lda xp_n0,x
        sta c_xp
        lda xp_n1,x
        sta c_xp+1
        lda xp_n2,x
        sta c_xp+2
        lda #0
        sta tmp0
        sta tmp1
        jsr add_xp
        #msg "level "
        lda c_lvl
_num    jsr ui_b3l
        jmp _dr
_max    #msg "limit reached"     ; livello massimo, villaggio 5 senza sotterraneo, ultimo villaggio
        jmp _dr
_c2     cmp #2
        bne _c3
        jsr resp_add            ; 2 respec token: +1 (al massimo RESP_MAX)
        #msg "tokens "
        lda c_resp
        jmp _num
_c3     cmp #3
        bne _c4
        lda cur_level           ; 3 next level
        bne _dun
        lda c_chap              ; villaggio: il primo piano del capitolo, come la cripta (go_tdown)
        cmp #CHAPTERS+1
        bcs _max
        jmp go_tdown
_dun    cmp #MAXLEVEL
        beq _fin
        jsr is_cboss
        bcs _boss
        jmp go_down             ; piano normale: le scale in giu'
_fin    lda #1                  ; sala del trono: come la morte del boss finale (kill_monster)
        sta c_won
        lda #CHAPTERS+1
        sta c_unl
        .rept RESP_FINAL
        jsr resp_add
        .endrept
        jmp _home
_boss   jsr chap_won            ; piano del boss del capitolo: come la sua morte (capitolo dopo sbloccato)
_home   lda #0                  ; al villaggio del capitolo, alla cripta (come le scale in su dal primo piano)
        tax
        jmp change_level
_c4     cmp #4
        bne _gold
_ch     lda c_chap              ; 4 next chapter
        cmp #CHAPTERS+1
        bcs _max
        cmp c_unl               ; capitolo dopo sbloccato (c_unl almeno c_chap + 1)
        bcc +
        adc #0                  ; (C = 1)
        sta c_unl
+       lda cur_level
        beq _tv
        jsr save_level          ; da un piano: il piano nel suo slot (come le scale), poi si parte come dal villaggio:
        lda #0                  ; niente STASH/portale verso il capitolo lasciato, eroe salvato nel villaggio nuovo
        sta cur_level
        sta c_loc
_tv     jmp chap_travel
_gold   lda #<1000              ; 5 gold +1000 (18/11)
        ldx #>1000
        jsr add_gold16
        #msg "gold "
        lda c_gold
        sta tmp0
        lda c_gold+1
        sta tmp1
        lda #1
        sta ui_nl
        jsr ui_num5
        lda #0
        sta ui_nl
        jmp _dr

        .enc "none"
