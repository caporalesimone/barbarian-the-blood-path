; ===================================================================
;  levels.asm - citta', cambio livello, nuovo personaggio, avvio
; ===================================================================
; (15/11, TODO Z2) Ogni villaggio ha le SUE posizioni, i SUOI colori, il nome del SUO luogo di cura e i SUOI tile solidi:
; stanno nell'intestazione del file TWNc (dopo i tile, prima della mappa RLE; tools/build/gen_maps.py) e gfx_install le
; copia qui (town_k, TK_LEN byte) e in solidtab a ogni caricamento del villaggio.
        .include "town_places.inc"      ; TK_LEN, TK_SOLID, TX_EXIT_N, NVIL
town_k
tk_px   .byte 0                 ; portale del villaggio (casella P della mappa); l'arrivo e' la casella sotto
tk_py   .byte 0
tk_stx  .byte 0                 ; arrivo dal primo piano: sull'ingresso del sotterraneo (casella >)
tk_sty  .byte 0
tk_nx   .byte 0                 ; ingresso del villaggio (casella E): partita nuova, arrivo dal capitolo prima
tk_ny   .byte 0
tk_pal  .fill 4                 ; colori: sfondo, multicolor 1, multicolor 2, color RAM (8 + accento)
tp_smith .fill 6                ; porte per le icone della minimappa: fabbro, alchimista, locanda (colonna, riga)
tx_exit_x .fill TX_EXIT_N       ; uscita del capitolo (caselle =)
tx_exit_y .fill TX_EXIT_N
ls_fount .fill TK_NAME          ; nome del luogo di cura (etichetta della barra in alto, con lo 0 finale)
        .cerror * - town_k != TK_LEN, "town_k: lunghezza diversa da TK_LEN (tools/build/gen_maps.py)"

; set di tile (palette) 1..8 per piano: dipende da seed e piano
pal_for_level:
        lda cur_level
        beq _t
        cmp #MAXLEVEL           ; ultimo piano: palette rossa fissa (contrasto del pentacolo)
        beq _red
        lda lv_cboss            ; (12/11) piano del boss di un capitolo: anche lui rosso (tile della sala del trono)
        beq +
_red    lda #4
        rts
+       lda cur_level
        asl
        clc
        adc cur_level
        clc
        adc c_seedt
        clc
        adc c_seedt+3
        and #7
        clc
        adc #1
        rts
_t      lda #0
        rts

new_character:
        lda #<CHRBLK
        sta ptr0
        lda #>CHRBLK
        sta ptr0+1
        lda rnd
        pha
        lda rnd+1
        pha
        ldy #0
        lda #0
_c      sta (ptr0),y
        iny
        cpy #(CHREND-CHRBLK)
        bne _c
        pla
        sta c_seed+1
        pla
        sta c_seed
        ora c_seed+1
        bne _s
        inc c_seed
_s      lda #SAVE_VER
        sta c_magic
        lda #GVER
        sta c_gver
        ldx #5
_sd     lda seedbuf,x           ; seed scelto/mostrato nella schermata di creazione
        sta c_seedt,x
        dex
        bpl _sd
        ldx #NAME_LEN-1
_nm     lda namebuf,x
        sta c_name,x
        dex
        bpl _nm
        lda #1
        sta c_lvl
        sta c_chap              ; (12/11) capitolo 1, nessun altro sbloccato
        sta c_unl
        lda #<PL_START_GOLD
        sta c_gold
        lda #>PL_START_GOLD
        sta c_gold+1
        lda $dc04           ; rnd e' 0 dopo game_start (xorshift fermo: durabilita' sempre DUR_MIN): un seme dal timer
        eor $d012
        sta rnd
        lda $dc05
        ora #1
        sta rnd+1
        lda #I_START
        sta c_eq            ; arma iniziale (db) con la sua durabilita'
        jsr dur_roll
        lda ap_d
        sta c_eqd
        lda ap_m
        sta c_eqm
        jsr ap_clr          ; (dur_roll lascia ap_d/ap_m: il prossimo give_item li copierebbe)
        inc c_game          ; partita 1 (il numero cresce a ogni avvio: game_start)
        jsr recalc_stats
        lda hpmax
        sta c_hp
        rts


; villaggio: dopo la mappa dal file, il portale (se aperto) e il caso fisso del villaggio
town_post:
        lda #$5a
        sta rnd
        lda #$a5
        sta rnd+1
        lda c_portal
        beq _np
        lda tk_px
        sta tx
        lda tk_py
        sta ty
        lda #T_PORTAL
        jmp set_tile
_np     rts

; ---- caricamento / generazione di un luogo (cur_level)
; grafica del luogo: si rilegge sempre dal disco (nessuna cache dal 11/11, ramo fast-loader), poi la si installa.
; town_at = 1 mentre il villaggio e' a $E000: un salvataggio usa quella RAM e lo rilegge (rel.asm, sv_end)
enter_gfx:
        lda #0
        sta town_at
        lda cur_level
        bne _dun
        jsr load_gfx
        inc town_at
        lda #0
        sta ovl_cur             ; il modulo MENU si rilegge a ogni ingresso nel villaggio
        jsr ovl_town            ; modulo MENU (negozi e locanda)
        lda #0
        jmp gfx_install
_dun    jsr lvl_theme           ; file del tema del piano
        jsr load_gfx
        lda #1
        jmp gfx_install

load_location:
        jsr chap_enter          ; (12/11) lv_cboss: piano del boss di un capitolo?
        jsr enter_gfx
        lda #0
        sta bar_lab
        sta bt_ph
        sta bt_who
        lda #$ff
        sta lc_x                ; forza il ricalcolo dell'etichetta
        jsr pal_for_level
        jsr set_palette
        lda cur_level           ; tile solidi del luogo: il villaggio ha i suoi (gia' copiati da gfx_install, 15/11)
        beq _st
        ldy #47
_sd     lda solid_dun,y
        sta solidtab,y
        dey
        bpl _sd
        bmi _dun
_st     jsr town_post           ; la mappa del villaggio e' gia' in MAP (file GFX0, data/town_map.txt)
        jsr clear_lvlblk
        jmp music_town
_dun    ldx #63                 ; mostri: nessuno scorrimento lungo i muri in corso (mslide, mslc)
        lda #0
-       sta mslide,x
        dex
        bpl -
        jsr music_dungeon
        jsr floor_types         ; statistiche dei tipi di mostro per questo piano (combat.asm)
        jsr gen_dungeon
        jsr chap_ensure         ; (11/11 sera) piani del capitolo negli slot in RAM (letti dal file se si cambia capitolo)
        jsr pend_enter          ; stato lasciato in memoria (portale/morte)? mostri come li si era lasciati
        bcs _mem
        jsr clear_lvlblk        ; piano rigenerato dal seed (sempre)...
        lda cur_level
        sta lb_lvl
        jsr spawn_monsters
        lda cur_level
        cmp #MAXLEVEL
        bne _pc
        jsr fin_chests
        jmp _pb
_pc     jsr place_chests
_pb     jsr place_boss
        lda cur_level           ; ...e se visitato, le differenze salvate sopra
        jsr vis_bit
        and c_vis,x
        beq _ok
        jsr load_level
_ok     jsr init_monsters_rt        ; scale: mostri rimasti ricalcolati (vita piena)
_mem
        jsr final_init
        jsr apply_chests
        jsr place_portal_tile
.if TESTBUILD == 0
        lda $d012               ; dopo la generazione deterministica, il caso torna libero
        eor frame
        eor rnd
        sta rnd
        lda rnd+1
        eor $dc04
        ora #1
        sta rnd+1
.endif
        rts

; ---- posiziona il giocatore secondo spawn_mode
; 0 = scale su (arrivo da sopra), 1 = scale giu' (arrivo da sotto),
; 2 = portale (citta': accanto al portale; dungeon: posizione salvata), 3 = respawn citta'
place_player:
        lda cur_level
        bne _dun
        lda spawn_mode
        beq _ts
        cmp #4
        bne _tp
        lda tk_nx
        ldx tk_ny
        jmp _put
_tp     lda tk_px               ; accanto al portale: la casella sotto
        ldx tk_py
        inx
        jmp _put
_ts     lda tk_stx
        ldx tk_sty
        jmp _put
_dun    lda spawn_mode
        cmp #2
        beq _ret
        cmp #1
        beq _dn
        lda st_up_x
        clc
        adc #1
        ldx st_up_y
        jmp _put
_dn     lda st_dn_x
        clc
        adc #1
        ldx st_dn_y
        jmp _put
_ret    lda c_retx
        ldx c_rety
_put    jsr put_hero            ; (11/11, O12)
_fin    lda #$ff
        sta lptx
        sta lpty
        sta st_hold
        lda #0
        sta fx_timer
        sta pdx
        sta pdy
        sta panim
        lda #1
        sta hud_dirty
        sta force_redraw
        rts

; A = nuovo livello, X = modalita'
; Salvataggi: il personaggio solo dal menu RUN/STOP (e alla creazione). Lo stato del piano si
; salva lasciandolo per le scale; per portale o morte resta in memoria (STASH) e si salva quando
; si entra in un altro piano o dal menu RUN/STOP.
change_level:
        sta new_lvl
        stx spawn_mode
        jsr snd_fade            ; audio: dissolvenza del volume a zero, prima di tutto
        jsr irq_off             ; schermo nero: niente glitch mentre si riscrivono caratteri e mappa
        lda #0
        sta SPR_EN
        sta BORDER
        lda #$0b
        sta VIC_CTRL1
        jsr music_fadeout       ; (in silenzio: salva la posizione del brano)
        jsr snd_mute
        lda cur_level
        beq _ns
        lda spawn_mode
        cmp #2
        bcs _st                 ; portale (2) o morte (3)
        jsr save_level
        jmp _ns
_st     jsr stash_level
_ns     lda new_lvl         ; (11/11 sera) piano di un altro capitolo: eroe + piani del capitolo sul disco, prima di
        beq _nc                 ; cambiare luogo (l'eroe resta registrato dove era: c_loc e posizione di adesso)
        jsr lv_grp
        cmp cur_chap
        beq _nc
        jsr chap_save
_nc     lda new_lvl
        cmp c_maxd
        bcc _nmx
        sta c_maxd
_nmx    lda new_lvl
        sta cur_level
        sta c_loc
        jsr load_location
        jsr place_player
        lda mus_flt             ; volume di nuovo pieno (i brani ripartono con la loro dissolvenza)
        ora #$0f
        sta $d418
        jmp ui_exit

; dissolvenza del volume generale a zero (15 fotogrammi), poi tutte le voci spente
snd_fade:
        ldx #15
_l      txa
        ora mus_flt
        sta $d418
        jsr wait_vblank
        dex
        bpl _l
snd_mute:
        lda #0
        sta $d404
        sta $d40b
        sta $d412
        lda mus_flt
        sta $d418               ; volume 0
        rts

; ---- stato del piano in memoria (STASH: RAM sotto l'I/O)
; Uscendo per portale o morte si conservano LVLBLK e lo stato dei mostri in gioco (MRT: posizione
; fine, vita attuale e massima a 16 bit, ricariche... 384 B): tornando, i mostri sono esattamente come li si era lasciati.
; Cambiando piano per le scale invece si salva solo lo stato compatto e i mostri rimasti si ricalcolano.
STASH  = $d000                  ; libera dopo il primo menu (salvataggi letti dal loader)
MRT    = $9600                  ; mxl .. mdmg (game.asm): 12 tabelle x 32 mostri
MRT_N  = 12*32
STASHM = STASH + $300           ; copia di MRT
        .cerror mxl != MRT || mhmh + 32 != MRT + MRT_N, "tabelle dei mostri in gioco non contigue a $9600"
        .cerror STASHM < STASH + (LVLEND-LVLBLK), "STASHM sovrapposto a LVLBLK in STASH"

; piano attuale -> STASH (uscita per portale o morte)
stash_level:
        jsr flush_drops
        jsr sync_monsters
        lda cur_level
        sta lb_lvl
        sta pend_lvl
        lda #0                  ; LVLBLK -> STASH, MRT -> STASHM
        beq stash_both
; STASH -> LVLBLK, STASHM -> MRT
stash_get:
        lda #1
stash_both:
        sta tmp5
        ldx #1
_b      stx tmp4
        lda sb_lo,x             ; blocco x: 0 = LVLBLK, 1 = MRT
        sta ptr0
        sta ptr1
        lda sb_hi,x
        sta ptr0+1
        sta ptr1+1
        lda sb_slo,x
        ldy tmp5
        bne _g
        sta ptr1                ; salva: memoria -> STASH
        lda sb_shi,x
        sta ptr1+1
        jmp _n
_g      sta ptr0                ; riprende: STASH -> memoria
        lda sb_shi,x
        sta ptr0+1
_n      lda sb_nlo,x
        sta tmp6
        lda sb_nhi,x
        sta tmp7
        sei
        lda #$34
        sta $01
        jsr cp_n
        lda #$36
        sta $01
        cli
        ldx tmp4
        dex
        bpl _b
        rts
sb_lo   .byte <LVLBLK, <MRT
sb_hi   .byte >LVLBLK, >MRT
sb_slo  .byte <STASH, <STASHM
sb_shi  .byte >STASH, >STASHM
sb_nlo  .byte <(LVLEND-LVLBLK), <MRT_N
sb_nhi  .byte >(LVLEND-LVLBLK), >MRT_N

; entrando in un piano: C=1 se il suo stato e' in STASH (ripreso). Se STASH contiene un altro
; piano, prima lo si salva su disco.
pend_enter:
        lda pend_lvl
        beq _no
        cmp cur_level
        bne _fl
        jsr stash_get
        lda #0
        sta pend_lvl
        sec
        rts
_fl     jsr pend_save
        lda #0
        sta pend_lvl
_no     clc
        rts

; STASH -> slot del piano in RAM (LVLBLK viene sovrascritto: il chiamante lo ricostruisce)
pend_save:
        jsr stash_get
        lda pend_lvl
        jmp save_lvlblk

; ---- avvio
; (11/11, O12) il PG sulla casella A (x), X (y): px/py in pixel (portale, scale, morte, varianti di prova)
put_hero:
        stx tmp5
        jsr tile_to_pix
        lda tmp0
        sta px
        lda tmp1
        sta px+1
        lda tmp5
        jsr tile_to_pix
        lda tmp0
        sta py
        lda tmp1
        sta py+1
        rts

game_start:
        lda #$90                ; azzera tutte le variabili $9000-$9BFF (incluso LVLBLK)
        sta ptr0+1
        lda #0
        sta ptr0
        ldx #12
        jsr fill_pages          ; (esce con A = 0, Y = 0)
.if ARENA
        jmp AR_MAIN
.endif
.if TESTBUILD
        lda #<testscript
        sta scr_ptr
        lda #>testscript
        sta scr_ptr+1
.endif
.if TESTBUILD == 1
.if TMDBG
        lda #$ff
        sta $dd04
        sta $dd05
        lda #0
        sta TM_IDX
        lda #$91                ; (bit 7: TOD a 50 Hz)
        sta $dd0e
.endif
        lda #$34
        sta rnd
        lda #$12
        sta rnd+1
        jsr seed_roll
        jsr new_character
        jsr tod_start
        lda #TESTCL
        sta c_lvl
.if TESTCL > 1                  ; (11/11) punti statistica spesi come il PG di riferimento
        lda pl_rstr+TESTCL
        sta c_sadd
        lda pl_rdex+TESTCL
        sta c_sadd+1
        lda pl_rcon+TESTCL
        sta c_sadd+2
.endif
        jsr recalc_stats
        jsr hp_full
.if TESTGOD
        lda #1                  ; cheat: il PG non perde vita (TESTGOD=1 tools/build/asm.sh test; docs/cheats.md)
        sta godmode
.endif
.if TESTFZ == 1
        lda #TESTFZR            ; test: Frenzy infinita alla corsa TESTFZR (0..100 = +0..100%)
        sta fz_run
        lda #$ff
        sta tmr+T_FZ
        sta tmr+T_FZ+1
.endif
.if TESTUI
        jsr test_ui_fill
.endif
        lda #TESTLVL
        sta cur_level
        sta c_loc
        jsr load_location
        lda #0
        sta spawn_mode
        jsr place_player
.if TESTUI == 2
        jsr load_menu
        jsr LOBBY_AT+3           ; scheda eroe salvato
.endif
.if (TESTUI == 21) || (TESTUI == 29)       ; 29: casa nella scelta dell'anello (screenshot)
        jsr ovl_town
        ldx #STASH_N-1          ; baule di casa pieno (24 oggetti, regola del committente 08/11): tutti i tipi di oggetto
_st     txa                     ; tranne le pergamene, a giro
-       cmp #I_SCROLL-1
        bcc +
        sbc #I_SCROLL-1
        bcs -
+       adc #1
        sta st_id,x
        lda #0
        sta st_b,x
        sta st_du,x
        sta st_m,x
        dex
        bpl _st
        jsr MENU_INN
.endif
.if TESTUI == 20
        lda #2
        ldx #0
        jsr change_level
.endif
.if TESTUI == 5
        jsr player_tile
        lda ptx
        sta loot_x
        lda pty
        sta loot_y
        lda #3
        jsr chest_add
        lda #0
        sta ch_msg
        jsr chest_gen_seed
        jsr ui_chest
.endif
.if TESTUI == 4
        jsr ui_inventory
.endif
.if (TESTUI == 15) || (TESTUI == 17)        ; 15 fabbro, 17 alchimista (16 era l'armaiolo, tolto il 09/11)
        lda #<5000
        sta c_gold
        lda #>5000
        sta c_gold+1
        jsr ovl_town            ; (gia' caricato entrando nel villaggio)
        lda #(TESTUI - 15) / 2
        jsr MENU_SHOP
.endif
.if TESTUI == 14
        jsr player_tile
        jsr mark_explored
        jsr ui_minimap
.endif
.if TESTUI == 22
        lda #3
        sta $03e1
_t22y   lda #4
        sta $03e0
_t22x   lda $03e0
        sta ptx
        lda $03e1
        sta pty
        lda $03e0
        cmp #36
        bcc _t22d
        lda $03e1
        cmp #27
        bcs _t22s
_t22d   jsr mark_explored
_t22s   lda $03e0
        clc
        adc #8
        sta $03e0
        cmp #48
        bcc _t22x
        lda $03e1
        clc
        adc #6
        sta $03e1
        cmp #48
        bcc _t22y
        jsr player_tile
        jsr mark_explored
        jsr ui_minimap
.endif
.if TESTUI == 23
        jsr player_tile
        lda ptx
        sta $03e2
        lda pty
        sta $03e3
        lda #14
        sta $03e0
_t23    lda ptx
        sta loot_x
        lda pty
        sta loot_y
        lda #3
        lda #24                 ; chestLevel 24 (piano 3)
        sta gi_ll
        lda #0
        sta dc_b
        ldx #1
        lda #1
        jsr drop_chest
        dec $03e0
        bne _t23
.endif
.if TESTUI == 25
        jsr ui_gamemenu
.endif
.if (TESTUI == 40) && CHEATS     ; (15/11) screenshot: menu dei trucchi (tools/vice/shots_menus.sh "trucchi")
        jsr cheat_menu
.endif
.if TESTUI == 39                ; (11/11) screenshot: schermata C (personaggio) con un punto in attesa su FOR
        jsr ui_charsheet
.endif
.if (TESTUI == 30) || (TESTUI == 31)    ; (09/11) screenshot: menu iniziale con 2 barbari / nuovo barbaro
        jsr load_menu
        sei                     ; elenco dei barbari "gia' letto dal loader" (CHRPRE/CHRBUF di src/lobby.asm)
        lda #$34
        sta $01
        ldx #HDR_LEN
        lda #$20
_h30    sta $d000,x
        dex
        bpl _h30
        lda #1
        sta $d000
        sta $d002
        sta $d003
        lda #SAVE_VER
        sta $d001
        ldx #NAME_LEN-1
_n30    lda tu_name,x
        sta $d007,x
        lda tu_nm2,x
        sta $d007+NAME_LEN,x
        dex
        bpl _n30
        lda #0
        sta $d004
        sta $d005
        sta $d006
        lda #$36
        sta $01
        lda #1
        sta $02b1
        jmp LOBBY_AT
tu_nm2  .byte 7,18,5,25,32,23,15,12,6,32,32,32   ; "grey wolf"
.endif
.if TESTUI == 32
        jsr ui_died
.endif
.if TESTUI == 33
        jsr ui_gamemenu         ; (ui.asm: con TESTUI=33 salta subito alla domanda "quit game?")
.endif
.if TESTUI == 34
        lda #SAVE_VER-1         ; salvataggi di un'altra versione
        sta hdrbuf
        jsr ui_badsave
.endif
.if (TESTUI == 37) || (TESTUI == 38)   ; io_screen: "loading" generico (modulo MENU) / "loading level 5..."
        lda #1
        sta io_dir
        lda #TESTUI-35          ; 37 -> 2 (generico), 38 -> 3 (piano)
        sta io_what
        lda #5
        sta io_lvl
        jsr io_screen
        jmp *
.endif
.if TESTUI == 35
        lda #0                  ; "saving barbarian"
        sta io_dir
        sta io_what
        jsr io_screen
        jmp *
.endif
.if TESTUI == 36
        jsr ui_lever
.endif
.if TESTUI == 28                ; HUD per il ritaglio dell'help (tools/build/gen_help.py --snap): arma quasi rotta, 2 chiavi
        lda #9
        sta c_eqd
        lda #120
        sta c_eqm
        lda #2
        sta c_keys
        lda hpmax               ; vita a meno di 40 dal massimo (barra rossa non piena, sopra la soglia di avviso)
        sec
        sbc #40
        sta c_hp
        lda hpmax+1
        sbc #0
        sta c_hp+1
        ldx c_lvl               ; esperienza a meta' del livello: (soglia precedente + soglia successiva) / 2
        dex
        lda xp_n0-1,x
        clc
        adc xp_n0,x
        sta c_xp
        lda xp_n1-1,x
        adc xp_n1,x
        ror
        sta c_xp+1
        ror c_xp
.endif
.if TESTUI == 27                ; avvisi dell'HUD (screenshot del manuale): vita bassa e arma quasi rotta
        lda #6
        sta c_hp
        lda #0
        sta c_hp+1
        lda #9
        sta c_eqd
        lda #120
        sta c_eqm
.endif
.if TESTUI == 3
        lda #0
        sta cur_slot
        jsr save_char
        lda #0
        sta c_gold
        sta c_gold+1
        jsr load_char
        lda #0
        rol
        sta $03f0
        lda c_gold
        sta $03f1
        lda c_gold+1
        sta $03f2
        lda c_seedt+3
        sta $03f3
        lda lb_cnt
        sta $03f4
        lda mtype
        sta $03f5
        jsr save_level
        jsr clear_lvlblk
        lda cur_level
        jsr load_level
        lda #0
        rol
        sta $03f6
        lda lb_cnt
        sta $03f7
        lda mtype
        sta $03f8
        lda lb_lvl
        sta $03f9
        lda c_seedt+3
        sta $03fa
.endif

.if (TESTUI == 6) || (TESTUI == 7)
        ldx #0
_fc     lda ch_t,x
        bne _gc
        inx
        cpx #CH_MAX
        bne _fc
        beq _nc
_gc     lda cx_x,x
        sta loot_x
        lda cx_y,x
        sta loot_y
.if TESTUI == 6
        jsr adj_floor
.endif
        lda loot_x
        ldx loot_y
        jsr put_hero
_nc
.endif
.if TESTUI == 8
        jsr player_tile
        lda ptx
        sta loot_x
        lda pty
        sta loot_y
        jsr adj_floor
        lda loot_x
        sta tx
        lda loot_y
        sta ty
        lda #0
        sta km_i
        lda #10
        sta tmp7
_rl     jsr roll_loot
        lda tx
        sta loot_x
        lda ty
        sta loot_y
        dec tmp7
        bne _rl
        jsr flush_drops
.endif
.if TESTUI == 9
        ldx lb_boss
        beq _nb9
        dex
        jsr bar_target
        lda #$ff
        sta bar_t
        lda mhp,x
        lsr
        sta mhp,x
_nb9
.endif
.if TESTUI == 10
        lda cur_level
        pha
        lda #1
        sta cur_level
_u10    ldx cur_level         ; nomi dei boss per piano ($0350/$0360,x)
        jsr boss_name_idx
        lda lb_bn1
        sta $0350,x
        lda lb_bn2
        sta $0360,x
        inc cur_level
        lda cur_level
        cmp #MAXLEVEL
        bne _u10
        pla
        sta cur_level
.endif
.if TESTUI == 11
        lda mxl
        sta ha_x
        lda mxh
        sta ha_x+1
        lda myl
        sta ha_y
        lda myh
        sta ha_y+1
        lda #40
        sta ha_hw
        sta ha_hh
        lda #0                  ; un colpo di slash
        sta ha_kind
        jsr hit_area
.endif
.if (TESTUI == 12) || (TESTUI == 13)
        jsr player_tile
        jsr use_scroll
.endif
.if TESTUI == 13
        lda c_retx
        ldx c_rety
        jsr put_hero
.endif
.if TESTSP
        jsr test_spawn
.endif
.if TESTX
        lda #TESTX
        ldx #TESTY
        jsr put_hero
.endif
        jsr ui_exit
        jmp main_loop

test_ui_fill:
        ldx #4
_e      lda tu_eq-1,x
        sta c_eq-1,x
        dex
        bne _e
        ldx #3
_e2     lda tu_eqb,x
        sta c_eqb,x
        dex
        bpl _e2
        ldx #PACK_N-1
_p      lda tu_pack,x
        sta c_pack,x
        lda tu_packb,x
        sta c_packb,x
        dex
        bpl _p
        ldx #PACK_N+3           ; durabilita' di prova per tutto (zaino + equipaggiamento)
_du     lda c_pack,x
        jsr dur_roll
        lda ap_d
        sta c_packd,x
        lda ap_m
        sta c_packm,x
        dex
        bpl _du
        jsr ap_clr
        lda #I_POTR
        sta c_beltt
        sta c_beltt+1
        lda #I_POTY
        sta c_beltt+3
        lda #I_POTV             ; cintura piena (08/11, CLAUDE.md: l'eroe di prova ha sempre il massimo di pozioni)
        sta c_beltt+2
        lda #<340
        sta c_xp
        lda #>340
        sta c_xp+1
        lda #<137
        sta c_kills
        lda #0
        sta c_kills+1
        lda #<2350
        sta c_gold
        lda #>2350
        sta c_gold+1
        lda #<TU_SGOLD          ; oro nel baule di casa (la scheda mostra il totale)
        sta c_sgold
        lda #>TU_SGOLD
        sta c_sgold+1
        lda #5
        sta c_maxd
        ldx #NAME_LEN-1
_n      lda tu_name,x
        sta c_name,x
        dex
        bpl _n
        jmp recalc_stats
TU_SGOLD = 65535                ; baule di casa pieno al limite (65535 decine = 655350 monete, 10/11) + 2350 addosso = 657700:
                                ; la scheda passa per il totale a 6 cifre (regola del committente, 08/11: si prova sempre questo caso)
tu_eq   .byte I_SWORD, I_PLATE_MAIL, I_MEDIUM_SHIELD, I_SILVER
tu_eqb  .byte 1, 3, 2, 2
tu_pack .byte I_VIKING_SWORD, I_DAGGER, I_CHAIN_MAIL, I_TOWER_SHIELD, I_SCROLL, I_GOLD, I_LEATHER_ARMOR, I_COPPER
tu_packb .byte 2, 0, 1, 0, 3, 3, 0, 1
        .cerror * - tu_packb != PACK_N, "tu_packb: un byte per posto dello zaino"
tu_name .byte 2,12,1,3,11,32,20,8,15,18,14,5     ; "black thorne": 12 caratteri con uno spazio (08/11, regola del committente per le prove)
        .cerror * - tu_name != NAME_LEN, "tu_name: NAME_LEN caratteri"
        .fill 11, 32

test_spawn:
.if TESTLVL == 0
        rts
.endif
.if TESTSP == 2
        jmp test_spawn2
.endif
        jsr player_tile
        ldx lb_cnt
        lda #1
        sta mtype,x
        sta malive,x
        lda ptx
        sta mix,x
        lda pty
        clc
        adc #2
        sta miy,x
        inx
        lda #4
        sta mtype-0,x
        sta malive,x
        lda ptx
        clc
        adc #1
        sta mix,x
        lda pty
        clc
        adc #3
        sta miy,x
        inx
        stx lb_cnt
        jmp init_monsters_rt
.else
        jsr menu_run            ; A = 0 continua, 1 nuova partita
        pha
        cmp #1
        bne _cont
        jsr new_character
        lda #0
        sta cur_level
        sta c_loc
        jsr load_location
        lda #4                  ; nuova partita: ingresso sud del villaggio
        sta spawn_mode
        jsr place_player
        lda #1                  ; eroe + elenco eroi con una sola apertura del file
        sta rel_hold
        jsr save_char
        ldx cur_slot            ; elenco eroi (record 156 di SAVES): solo alla creazione
        lda #1
        sta slot_valid,x
        txa
        asl
        asl
        asl
        asl
        tax
        ldy #0
_hn     lda c_name,y
        sta slot_name,x
        inx
        iny
        cpy #NAME_LEN
        bne _hn
        jsr hdr_write
        jsr rel_done
        jmp _go
_cont   inc c_game              ; nuova partita con un eroe salvato: numero di partita + 1 (9 bit, 1..511)
        bne +
        inc c_game+1
+       lda c_game+1
        and #1
        ora c_game
        bne +
        inc c_game              ; 512 -> 1
+       lda c_loc
        sta cur_level
        jsr load_location
        lda c_px
        sta px
        lda c_px+1
        sta px+1
        lda c_py
        sta py
        lda c_py+1
        sta py+1
        lda #$ff
        sta lptx
        sta lpty
        lda #1
        sta hud_dirty
        sta force_redraw
_go     jsr tod_start           ; tempo giocato: l'orologio parte da 0 a ogni partita
        pla
        jsr recalc_stats
        jsr ui_exit
        jmp main_loop
.endif

; ---- vecchi salvataggi: ricava il seed (4 cifre base 36) dal vecchio seed a 16 bit
migrate_char:
        lda c_gver
        cmp #GVER
        beq _ok
        lda c_seed
        sta tmp0
        lda c_seed+1
        sta tmp1
        ldy #5
_d      lda #0
        ldx #16
_b      asl tmp0
        rol tmp1
        rol
        cmp #36
        bcc _n
        sbc #36
        inc tmp0
_n      dex
        bne _b
        sta c_seedt,y
        dey
        cpy #1
        bne _d
        lda #0
        sta c_seedt
        sta c_seedt+1
        sta c_vis               ; i piani vengono rigenerati col nuovo generatore
        sta c_vis+1
        sta c_vis+2
        lda #GVER
        sta c_gver
_ok     rts

.if TESTSP == 2
; scena pulita per gli screenshot: mostri distanziati attorno al PG, solo su pavimento libero
test_spawn2:
        jsr player_tile
        ldy #0
_o      sty $03e0
        lda ptx
        clc
        adc t2_dx,y
        sta tx
        lda pty
        clc
        adc t2_dy,y
        sta ty
        jsr floor_ok
        bcs _n
        ldy $03e0
        ldx lb_cnt
        lda t2_ty,y
        sta mtype,x
        lda #1
        sta malive,x
        lda tx
        sta mix,x
        lda ty
        sta miy,x
        inc lb_cnt
_n      ldy $03e0
        iny
        cpy #6
        bne _o
        jsr init_monsters_rt
        ldx #N_MTYPES           ; mostri quasi innocui (solo per lo screenshot): ATT -128, danno minimo (1)
_z      lda #$80
        sta ft_att,x
        dex
        bpl _z
        lda #0
        sta ft_dmul
        rts
t2_dx   .byte 3, $fd, 0, 4, $fc, 0
t2_dy   .byte 0, 1, 3, $fe, $fe, $fd
t2_ty   .byte 1, 2, 3, 5, 2, 1
.endif
