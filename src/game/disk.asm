; ===================================================================
;  disk.asm - caricamento dei file con Krill's Loader r194 (11/11, ramo fast-loader; docs/wiki/FastLoader.md)
;  Il residente (krill_loadraw, $0200) lo installa START: da li' il drive non risponde piu' al KERNAL.
;  I salvataggi sono in src/game/rel.asm (file save-0N e hl, plugin di save residente in GAME).
; ===================================================================
        .enc "none"              ; nomi file in PETSCII ('none': maiuscolo = $41..)

        .virtual $9450
cmdbuf  .fill 12                ; nome del file in cmdbuf+3.. (al massimo 8 caratteri + 0 finale)
nlen    .byte ?
cur_slot .byte ?
sv_old  .byte ?                 ; 1 = trovati salvataggi di un'altra versione
ovl_cur .byte ?                 ; 1 = modulo MENU (menu del villaggio) in memoria (azzerato da game_start e load_menu)
        .endv
        .virtual hw_low+1               ; (11/11, Krill) byte liberi dopo HUD e IRQ (src/game/hud.asm), fino a $97FF
sv_par  .fill 10                ; parametri del plugin di save: nome, da, lunghezza, indirizzo nel file, buffer
sv_nm   .fill 8                 ; "save-0N" + 0
dsk_end
        .endv
        .cerror dsk_end > $9800, "variabili del disco oltre $97FF (LVLBLK)"

; schermata di attesa (solo se non in modalita' silenziosa): titolo + "please wait"
io_begin:
        lda io_quiet
        bne _q
        lda io_what             ; 0 eroe, 2 "loading..." generico, altro: piano
        beq _h
        cmp #2
        beq _h
        lda #1
_h      sta io_what
        jsr io_screen
_q      rts

; (11/11, O3) nome di un file: Y = offset in nm_tab -> cmdbuf+3.., set_name4 = 4 caratteri, set_name con A = lunghezza
; (LOBBY: 5); nlen = lunghezza, io_dir = 1, 0 finale (Krill).
; Esce con A = 1 (i chiamanti lo scrivono anche in io_what / io_quiet); X conservato.
set_name4:
        lda #4
set_name:                               ; A = lunghezza (LOBBY: 5)
        sta nlen
        txa
        pha
        ldx #0
-       lda nm_tab,y
        sta cmdbuf+3,x
        iny
        inx
        cpx nlen
        bne -
        lda #0
        sta cmdbuf+3,x
        pla
        tax
        lda #1
        sta io_dir
        rts
nm_tab                                  ; minuscolo in "none" = PETSCII maiuscolo
nm_gfx  .byte $47,$46,$58,$30           ; "GFX" (+ cifra in cmdbuf+6 dal chiamante)
nm_fmap .text "fmap"
nm_lobby .text "lobby"
nm_menu .text "menu"                   ; menu del villaggio (locanda), stash.asm
nm_twn  .text "twn"                    ; (12/11) villaggio del capitolo: "TWN" + cifra (c_chap)
nm_bch  .text "bossch"                 ; (12/11) mappa del boss del capitolo: "BOSSCH" + cifra
nm_qst  .text "qst"                    ; (17/11) testo della quest: "QST" + cifra (quest.asm)
.if CHEATS
nm_cht  .text "cheats"                 ; (17/11) menu dei trucchi (solo debug e test, src/cheats.asm)
.endif

; A = 0 villaggio, 1..8 tema -> carica "GFXn" nella cache sotto il KERNAL. C=1 errore
load_gfx:
        tax
        ldy #nm_gfx-nm_tab      ; "GFX" + cifra
        jsr set_name4
        txa
        bne +
        ldy #nm_twn-nm_tab      ; (12/11) villaggio: "TWN" + capitolo
        jsr set_name4
        lda c_chap
+       clc
        adc #$30
        sta cmdbuf+6
        lda #1
        sta io_what
        lda cur_level
        sta io_lvl
        lda #<GFX_TOWN_AT
        sta ptr0
        lda #>GFX_TOWN_AT
        sta ptr0+1
        lda #<(GFX_TOWN_AT+4*GFX_TSTRIP+TOWN_MAX)
        sta ptr1
        lda #>(GFX_TOWN_AT+4*GFX_TSTRIP+TOWN_MAX)
        sta ptr1+1
        txa
        bne +
        jmp load_raw
+
        lda #<GFX_DUN_AT
        sta ptr0
        lda #>GFX_DUN_AT
        sta ptr0+1
        lda #<GFX_DUN_END
        sta ptr1
        lda #>GFX_DUN_END
        sta ptr1+1
        jmp load_raw

; (15/11, TODO D12) legge il file di nome gia' impostato in FIN_AT..FIN_END (FMAP e BOSSCHc)
fin_rd:
        lda #<FIN_AT
        sta ptr0
        lda #>FIN_AT
        sta ptr0+1
        lda #<FIN_END
        sta ptr1
        lda #>FIN_END
        sta ptr1+1
        jmp load_raw

; mappa di base della sala del trono (piano 20, file FMAP: tools/build/gen_final.py) -> MAP. Il file (RLE, ~400 B) si
; rilegge a ogni ingresso nel piano (11/11: niente cache) in FIN_AT ($FD00, sotto il KERNAL, fino ai vettori $FFFA)
; e si scompatta da li'.
fin_load:
        ldy #nm_fmap-nm_tab
        jsr set_name4
        sta io_what
        lda cur_level
        sta io_lvl
        jsr fin_rd
        lda #<FIN_AT
        ldx #>FIN_AT
fin_unp sta ptr0                ; ptr0 = flusso RLE -> MAP
        stx ptr0+1
        lda #<MAP
        sta ptr1
        lda #>MAP
        sta ptr1+1
        sei
        lda #$35                ; KERNAL spento: si legge la RAM sottostante
        sta $01
        jsr rle_unpack
        lda #$36
        sta $01
        cli
        rts

; (12/11, TODO M1) mappa del piano del boss del capitolo (file BOSSCHc, tools/build/gen_bossmap.py) -> MAP: stesso buffer
; di FMAP (FIN_AT); i primi 4 byte sono scale di arrivo (x, y) e posto del boss (x, y) -> bm_hdr, poi l'RLE
bmap_load:
        ldy #nm_bch-nm_tab
        lda #6
        jsr set_name
        sta io_what
        lda cur_level
        sta io_lvl
        jsr lv_grp              ; capitolo
        ora #$30
        sta cmdbuf+9
        lda #0
        sta cmdbuf+10
        lda #7
        sta nlen
        jsr fin_rd
        sei
        lda #$35
        sta $01
        ldx #3
-       lda FIN_AT,x
        sta bm_hdr,x
        dex
        bpl -
        lda #$36
        sta $01
        cli
        lda #<(FIN_AT+4)
        ldx #>(FIN_AT+4)
        jmp fin_unp

; modulo LOBBY (menu iniziale) -> $C000 ed esecuzione (il menu restituisce A come ui_menu)
menu_run:
        lda LDFLAGS             ; gia' caricato dal loader (solo la prima volta)
        beq _ld
        lda #0
        sta LDFLAGS
        jmp LOBBY_AT
_ld
        jsr load_menu
        jmp LOBBY_AT
; menu iniziale: il modulo LOBBY dal disco a LOBBY_AT ($C000, sopra la mappa; copre la zona 1 del MENU: ovl_cur = 0)
load_menu:
        lda #0
        sta ovl_cur             ; il LOBBY ($C000-$CBFF) copre la zona 1 del modulo MENU
        ldy #nm_lobby-nm_tab
        lda #5
        jsr set_name
        sta io_quiet
        lda #<LOBBY_AT
        sta ptr0
        lda #>LOBBY_AT
        sta ptr0+1
        lda #<(LOBBY_AT+$1000)
        sta ptr1
        lda #>(LOBBY_AT+$1000)
        sta ptr1+1
        jsr load_raw
        lda #0
        sta io_quiet
        rts

; modulo MENU (menu del villaggio, compresso): ovl_town in src/game/stash.asm (11/11)

; carica il file (nome in cmdbuf+3, 0 finale) a ptr0 (l'indirizzo nel file si ignora; ptr1 non serve piu').
; C=1 errore (A = stato di Krill). Musica zittita, schermata di attesa se non io_quiet.
load_raw:
        lda ptr0
        sta krill_loadaddrlo
        lda ptr0+1
        sta krill_loadaddrhi
        sec                     ; LOAD_TO: destinazione data qui
        .byte $24               ; (bit zp: salta il clc)
; carica il file all'indirizzo scritto nel file (C=0)
load_file:
        clc
        php
        jsr snd_io              ; SID zittito durante il disco (music.asm)
        jsr io_begin
        plp
        ldx #<(cmdbuf+3)
        ldy #>(cmdbuf+3)
        jmp krill_loadraw

; salvataggi: src/game/rel.asm (file REL SAVES)
save_level:
        jsr flush_drops         ; i bauli in attesa compaiono prima di salvare
        jsr sync_monsters
        lda cur_level
        jmp save_lvlblk
