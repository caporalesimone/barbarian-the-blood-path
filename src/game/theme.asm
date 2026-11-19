; ===================================================================
;  theme.asm - tema grafico di un piano e bit di visita
;
;  (11/11, ramo fast-loader) Il precaricamento in sottofondo del tema (pf_*, ex prefetch.asm) e le cache della
;  grafica (gfx_town, gfx_theme, fin_ok), del modulo MENU e del brano sono stati tolti per provare il caricatore
;  veloce senza trucchi: ogni ingresso in un luogo rilegge i suoi file dal disco. Restano le due tabelle.
; ===================================================================
PF_END  = $fd00                 ; fine della zona del modulo MENU (MR2_END) e inizio di FMAP (FIN_AT)

; A = piano (1..) -> A = numero del file GFXn (12/11: un file per capitolo c = 1..CHAPTERS, tile + sprite dei mostri):
; GFX(2c-1) = piani del dungeon del capitolo, GFX(2c) = piano del boss (oggi solo il piano MAXLEVEL, sala del trono;
; i file del boss dei capitoli 1-3 sono segnaposto non ancora usati). Calcolo: lv_grp (rel.asm, A = capitolo 1..).
lvl_theme:
        cmp #MAXLEVEL
        bne +
        lda #2*CHAPTERS         ; boss dell'ultimo capitolo
        rts
+       jsr lv_grp
        asl                     ; 2c
        cpx #CH_LV-1            ; piano del boss del capitolo: GFX(2c), tile della sala del trono (12/11)
        beq +
        sec
        sbc #1                  ; 2c - 1
+       rts

; A = piano (1..16) -> X = byte di c_vis (0/1), A = bit del piano
vis_bit:
        sec
        sbc #1
        pha
        lsr
        lsr
        lsr
        tax
        pla
        and #7
        tay
        lda bitmask,y
        rts

; ---------------------------------------------------------------------------------------------------------------------
; (19/11) CODICE DEL PIANO (docs/wiki/dungeon.md "Codice del piano"): il codice che serve a un solo tipo di piano (sala del
; trono; piani del boss dei capitoli) non sta in GAME: sta nella coda del file del tema di quel piano (tools/build/bundle.py,
; src/game/ovl_*.asm) e gfx_tail (music.asm) lo copia a OVP_AT = $C900, la zona 1 del MENU, libera in tutti i piani del
; dungeon (il MENU si rilegge a ogni ingresso nel villaggio). ovp_ok = 1 se il tema del piano attuale ne aveva uno. Tabella
; dei salti all'inizio del codice: OVJ_INIT dopo il piazzamento dei mostri (load_location), OVJ_TICK a ogni giro, OVJ_FIRE
; con Fire su T_DHOME (la leva della sala del trono). Nelle build ARENA e TESTUI 36 il codice del piano 20 resta in GAME.
; ---------------------------------------------------------------------------------------------------------------------
OVP_AT   = $c900
OVP_END  = $d000
; (nessuna annotazione @map: la zona e' gia' quella del MENU, zona 1, con la sua coda @free; lab64 map le vedrebbe sovrapposte)
OVJ_INIT = 0
OVJ_TICK = 3
OVJ_FIRE = 6
OVJ_DMG  = 9                    ; (19/11) colpo del PG a un mostro: il danno si puo' cambiare (scudo di Varok, Mother Stitch)
OVJ_KILL = 12                   ; (19/11) mostro X ucciso: C=1 = niente bottino (piano 20, feticci di Mother Stitch)
OVJ_DECOR = 15                  ; (19/11) arredi del piano, subito dopo la generazione (ovl_decor.asm)
OVJ_GEN  = 18                   ; (19/11) fine della generazione sotto l'I/O (cittadella, gen_citadel.asm)
OVJ_N    = 21                   ; lunghezza della tabella dei salti
ovp_ok  .byte 0
ovp_tint .byte 0                ; (19/11) colore del boss del capitolo deciso dal codice del piano (0 = il suo), build_sprites
.if OVP_RES
ovp_init = final_init
ovp_tick = final_tick
;(nelle build ARENA e TESTUI 36 niente arredi: le mappe restano quelle del generatore)
ovp_decor
ovp_dmg rts
ovp_kill                        ; build ARENA / TESTUI 36: niente bottino nel piano 20 (come final.asm): C=1 solo li'
        lda cur_level
        cmp #MAXLEVEL
        beq +
        clc
+       rts
.if ARENA
ovp_fire rts
.else
ovp_fire = ui_lever
.endif
.else
ovp_decor:                      ; (19/11) arredi del piano, subito dopo gen_dungeon (ovl_decor.asm)
        lda #OVJ_DECOR
        .byte $2c               ; (bit $xxA9: salta il lda dopo)
ovp_kill:                       ; X = mostro ucciso -> C=1 niente bottino (senza codice del piano: C=0)
        lda #OVJ_KILL
        .byte $2c
ovp_tick:
        lda #OVJ_TICK
        .byte $2c
ovp_init:
        lda #OVJ_INIT
        .byte $2c
ovp_fire:
        lda #OVJ_FIRE
        .byte $2c
ovp_dmg:                        ; X = mostro colpito, cb_dl/cb_dh = danno (si puo' cambiare); X conservato
        lda #OVJ_DMG
        ldy ovp_ok
        clc
        beq +
        sta _j+1
_j      jmp OVP_AT
+       rts
.endif

