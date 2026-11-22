; ===================================================================
;  baule di casa: spostamenti, ordinamento, messaggi (08/11: dal modulo della locanda; la schermata e' in src/menu/inn.asm)
; ===================================================================
; il baule (st_id, st_b, st_du, st_m) sta nel blocco dell'eroe (CHRBLK, src/game/game.asm, 08/11 sera)

; messaggi: riga 23 in rosso chiaro
h_msg:  jsr h_msgclr
        #at 1,23
        lda #10
        sta ui_col
        rts
h_msgclr:
        ldy #23
        jmp clear_row


st_sort lda #<sd_st
        ldx #>sd_st
        jmp sort4
sd_st   .byte STASH_N
        .word st_id, st_b, st_du, st_m, st_sx

; ---- modulo MENU (11/11, TODO D6/D13): i menu del villaggio (locanda e negozi, src/menu.asm) in due zone di RAM,
;  compressi ZX0. Si carica all'ingresso nel villaggio (enter_gfx) se non c'e' (ovl_cur = 0: lo azzerano game_start, il
;  LOBBY, che copre la zona 1, e ogni ingresso nel villaggio, perche' il dungeon copre le zone 4 e 5).
;  (18/11, revisione R2) UN SOLO FILE "menu" (prima uno per zona, menu1..menu5: ogni file in piu' costava ~0,4 s a ogni
;  ingresso nel villaggio). tools/build/pack_menu.py lo scrive cosi': intestazione (numero di parti, poi per ogni parte
;  indirizzo dei dati compressi e destinazione, 4 B), poi le parti compresse, l'ultima e' la zona 2. Il file finisce
;  esattamente a MR2_END: Krill lo carica al suo indirizzo (C=0), cioe' nella RAM sotto il KERNAL fra $E000 (ML_LO: il
;  file del villaggio e' gia' installato, enter_gfx) e la fine della zona 2. Si decomprimono prima le parti che vanno altrove (zone 1,
;  3, 4, 5: i dati restano nell'area di appoggio) e per ultima la zona 2, sul posto: pack_menu.py verifica che la
;  scrittura non raggiunga i dati non ancora letti e che il file non tocchi la cache del villaggio.
MR1_AT  = $c900                 ; zona 1: $C900-$CFFF (la mappa finisce a $C8FF; il LOBBY arriva a $CBFF)
MR1_END = $d000
MR2_AT  = GFX_DUN_END           ; zona 2: dopo la cache del tema ($F4E0), sotto il KERNAL
        .cerror GFX_DUN_AT+4*GFX_DSTRIP+GFX_MONS+GFX_STRONG+GFX_INFO != GFX_DUN_END, "file del tema: lunghezza diversa da GFX_DUN_END-GFX_DUN_AT"
MR2_END = PF_END                ; ($FD00: FMAP)
MR3_AT  = $a700                 ; zona 3: slot sprite 28-31 del banco VIC 2, liberi nel gioco (mappa automatica: out/work/memory-map/program-game.html)
MR3_END = $a800                 ; (charset del gioco)
MR4_AT  = SPR_DATA+12*64        ; (17/11) zona 4: slot sprite 12-19 ($A300-$A4FF), mostri del tema nel dungeon (ricopiati da
MR4_END = SPR_DATA+20*64        ; gfx_install a ogni ingresso), liberi nel villaggio: gli sprite degli NPC (tools/build/npc_gfx.py)
MR5_AT  = $8c00                 ; (18/11) zona 5: sprite forti e boss del tema nel dungeon ($8C00-$8E7F, ricopiati da gfx_install a
MR5_END = $8e80                 ; ogni ingresso), liberi nel villaggio: lo sprite del "!" e il codice degli NPC (src/menu/npc.asm)
MR6_AT  = MRT                   ; (18/11) zona 6: tabelle dei mostri in gioco ($9600-$977F), inutili nel villaggio (lb_cnt = 0) e
MR6_END = MRT+MRT_N             ; riscritte a ogni ingresso nel dungeon: il passo degli NPC (src/menu/npc_tick.asm)
MPARTS  = 6
ML_LO   = core_end              ; (18/11) appoggio del file del modulo sotto il KERNAL; (21/11) dalla fine del segmento CORE in su
OVL_AT  = MR1_AT                ; tabella dei salti del modulo (src/menu.asm)
MENU_INN  = OVL_AT              ; locanda
MENU_SHOP = OVL_AT+3            ; negozio A (0 fabbro, 1 alchimista) (jsr mk_off + jmp enter_shop: 6 B)
MENU_NHERE = OVL_AT+9           ; (18/11) chi e' accanto al PG (src/menu/npc_here.asm)
MENU_QOFFER = OVL_AT+12         ; (22/11) quest da dare / da ritirare (src/menu/q_who.asm)
MENU_QTIN  = OVL_AT+15
MENU_QMARK = OVL_AT+18
MENU_QMMK  = OVL_AT+21         ; (22/11) mm_qmark: "!" delle quest sulla minimappa (src/menu/npc_fix.asm)
NPC_BANG  = MR5_AT              ; (18/11) sprite del "!" (puntatore $30), all'inizio della zona 5
NPC_JT    = MR5_AT+64           ; tabella dei salti degli NPC (zona 5): piazzamento, sprite, Fire
NPC_QMARK = MR5_END-64          ; (22/11) sprite del "?" (quest da ritirare), in fondo alla zona 5 ($8E40)
NPC_JINIT  = NPC_JT              ; piazzamento (ingresso nel villaggio)
NPC_JDRAW  = NPC_JT+3
NPC_JTALK  = NPC_JT+6
NPC_JPX    = NPC_JT+9            ; (21/11) npc_px: casella -> pixel (22/11: nessun chiamante in GAME, npc_fix sta nel MENU)
NPC_JLOOK  = NPC_JT+12           ; (21/11) npc_look: colore e disegno a caso dell'NPC X
;@map ML_LO..MR2_AT "Appoggio del file MENU all'ingresso nel villaggio (parti compresse prima della decompressione)" scenario=villaggio
ml_src  = $5c                   ; (pagina zero libera dopo ZX_ZP) inizio del file (intestazione)
ml_i    = ml_src+2              ; parti ancora da decomprimere
ml_try  = ml_i+1                ; (15/11) letture rimaste del file (ex TODO A2)
ml_k    = ml_try+1              ; posizione nell'intestazione

; carica il modulo se non c'e' (ovl_cur = 0). C=1 se non si puo' caricare (il chiamante non salta nel modulo)
ovl_town:
        lda ovl_cur
        beq ml_read
        clc
        rts
ml_read:                        ; (lettura del file MENU: la contano i test)
        lda #2                  ; schermata "loading..." generica
        sta io_what
        ldy #nm_menu-nm_tab
        jsr set_name4           ; "menu", 0 finale
        lda #3                  ; (15/11, ex TODO A2) fino a 3 letture
        sta ml_try
_t      jsr load_file           ; all'indirizzo del file (finisce a MR2_END)
        bcs _bad
        lda krill_endaddrlo     ; (15/11, ex TODO A2) il file deve finire esattamente alla fine della zona 2: una lettura piu'
        cmp ml_end              ; corta o piu' lunga (Krill non da' errore) si rifa'; dopo 3 volte C=1
        bne _bad
        lda krill_endaddrhi
        cmp ml_end+1
        beq _ok
_bad    dec ml_try
        bne _t
        sec
        rts
_ok     lda krill_loadaddrlo
        sta ml_src
        lda krill_loadaddrhi
        sta ml_src+1
        php                     ; (il file e la zona 2 sono nella RAM sotto il KERNAL, sempre escluso: MEMCFG)
        sei
        ldy #0
        lda (ml_src),y          ; numero di parti
        sta ml_i
        iny
_u      lda (ml_src),y          ; dati compressi, destinazione
        sta zx_src
        iny
        lda (ml_src),y
        sta zx_src+1
        iny
        lda (ml_src),y
        sta zx_dst
        iny
        lda (ml_src),y
        sta zx_dst+1
        iny
        sty ml_k
        jsr zx0_unpack
        ldy ml_k
        dec ml_i
        bne _u
        plp
        inc ovl_cur
        clc
        rts
ml_end  .word MR2_END           ; fine attesa del file (una variabile: KRILL-22 la cambia per provare le riletture)

; (21/11, TODO D15) segmento CORE (src/game/core.asm) in memoria: se manca (core_ok = 0) si legge dal disco a CORE_AT, senza
; schermata (io_quiet), fino a 3 volte. Preserva X e Y? no: A, X, Y, ptr0 e i registri del disco cambiano.
core_need:
        lda core_ok
        bne _r
.if !ARENA                              ; (l'arena parte senza Krill e non apre schermate)
        lda io_quiet
        pha
        lda #1
        sta io_quiet
        lda #3
        sta ml_try
_t      ldy #nm_core-nm_tab
        jsr set_name4
        lda #<CORE_AT
        sta ptr0
        lda #>CORE_AT
        sta ptr0+1
        jsr load_raw
        bcs _bad
        lda krill_endaddrlo     ; letto tutto: il file finisce a core_end
        cmp #<core_end
        bne _bad
        lda krill_endaddrhi
        cmp #>core_end
        beq _ok
_bad    dec ml_try
        bne _t
        beq _x
_ok     inc core_ok
_x      pla
        sta io_quiet
.endif
_r      rts

; (21/11 sera, TODO A1 e D15) schermata del personaggio (tasto C): modulo CSHEET a CS_AT, letto se non c'e' (cs_ok = 0: lo
; azzerano ogni caricamento, load_file / load_raw, e il salvataggio, che possono coprire $EC00-), poi eseguito
CS_AT   = $ec00
;@map CS_AT..MR2_AT "CSHEET (schermata del personaggio) mentre e' aperta; prima il file del villaggio o del tema, l'appoggio del MENU o l'immagine SV_ALT" scenario=villaggio,dungeon
ui_charsheet:
        jsr cs_load
        bcs +
        jmp CS_AT
+       rts
; cs_load: il modulo in memoria (C = 0) o non leggibile (C = 1: la schermata non si apre). Lettura silenziosa come core_need
; (fino a 3 tentativi); il file e' intero se finisce dove dice la sua parola CS_AT+3. Misurata da PERF-DISK (csheet, cs1..cs4)
cs_load:
        lda cs_ok
        bne _ok0
.if !ARENA
        lda io_quiet
        pha
        lda #1
        sta io_quiet
        lda #3
        sta ml_try
_t      ldy #nm_csh-nm_tab
        lda #6
        jsr set_name
        lda #<CS_AT
        sta ptr0
        lda #>CS_AT
        sta ptr0+1
        jsr load_raw            ; (azzera cs_ok)
        bcs _bad
        lda krill_endaddrlo
        cmp CS_AT+3
        bne _bad
        lda krill_endaddrhi
        cmp CS_AT+4
        beq _ok
_bad    dec ml_try
        bne _t
        beq _x
_ok     inc cs_ok
_x      pla
        sta io_quiet
        lda cs_ok
        bne _ok0
.endif
        sec
        rts
_ok0    clc
        rts

ZX_ZP   = $50                   ; 12 byte della pagina zero del BASIC, liberi nel gioco (come in START, boot.asm)
        .include "zx0.inc"
