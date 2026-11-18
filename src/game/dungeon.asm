; ===================================================================
;  generazione dungeon da seed: parte residente (il generatore vero e' in gen_io.asm, nella RAM sotto l'I/O)
; ===================================================================

tile_to_pix:                ; A = coordinata tile -> tmp0/tmp1 = A*16+8
        sta tmp0
        lda #0
        sta tmp1
        .rept 4
        asl tmp0
        rol tmp1
        .endrept
        lda tmp0
        clc
        adc #8
        sta tmp0
        lda tmp1
        adc #0
        sta tmp1
        rts

; MAP piena di muro (T_WALL, 9 pagine), prima della generazione
clear_map:
        lda #<MAP
        sta ptr0
        lda #>MAP
        sta ptr0+1
        lda #T_WALL
        ldx #9
                                ; (prosegue in fill_pages)
; (11/11, O4) X pagine da ptr0 riempite con A; esce con Y = 0, ptr0 dopo l'ultima pagina. Usata anche sotto l'I/O
; (clear_map dal generatore) e da clear_lvlblk, game_start
fill_pages:
        ldy #0
-       sta (ptr0),y
        iny
        bne -
        inc ptr0+1
        dex
        bne -
        rts

; stato del PRNG per (seed, piano): mescola le 6 cifre del seed e il numero del piano
seed_level:
        lda cur_level
; (19/11) A = numero (piano; confine della palude | $c0, gate_hash) -> rnd: stesso mescolamento per tutti
seed_mix:
        sta sd_n
        lda #$a5
        sta rnd
        lda #$3c
        sta rnd+1
        ldx #0
_h      lda rnd
        clc
        adc c_seedt,x
        sta rnd
        lda rnd+1
        adc #$9d
        sta rnd+1
        jsr rand
        jsr rand
        inx
        cpx #6
        bne _h
        lda rnd
        clc
        adc sd_n
        sta rnd
        lda rnd+1
        adc #$47
        sta rnd+1
        jsr rand
        jsr rand
        jsr rand
        lda rnd
        ora rnd+1
        bne _ok
        lda #1
        sta rnd
_ok     rts

; genera il piano cur_level in MAP. Il generatore gira nella RAM sotto l'I/O (gen_io.asm, GEN_AT): qui solo cio'
; che tocca il disco (mappa della sala del trono, fin_load in CODE2) e il cambio di banco.
gen_dungeon:
        lda cur_level
        cmp #MAXLEVEL
        bne +
        jsr fin_load            ; MAP = mappa di base (dalla cache FIN_AT; dal disco la prima volta)
+       lda lv_cboss            ; (12/11) piano del boss di un capitolo: mappa fissa BOSSCHc (19/11: cripta, isola, grotta)
        beq +
        jsr bmap_load
+       lda #GEN_MAIN
; chiama il codice sotto l'I/O: A = punto d'ingresso (GEN_MAIN, GEN_WALLS). I/O e KERNAL spenti ($01 = $34) e
; interrupt spenti per tutta la chiamata: quel codice non deve toccare VIC, SID, CIA, colori, KERNAL.
gen_call:
        sta _j+1
        php
        sei
        lda #$34
        sta $01
_j      jsr GEN_AT
        lda #$36
        sta $01
        plp
        rts

; ------------------------------------------------------------------ ultimo piano: mappa fissa
; La mappa di base (rettangoli, porte chiuse, scale, leva, figure come marcatori $80|tile) e' il file FMAP del
; disco (tools/build/gen_final.py), messo in MAP da fin_load (disk.asm, CODE2). gen_final (gen_io.asm) fa solo cio' che
; dipende dalla partita; fin_doors e fin_chests restano qui (servono anche in gioco).
        .include "final_map.inc"
T_FSTAR = T_GRASSA              ; linee della stella (nel tema 8 lo slot contiene la grafica della stella)
T_FCIRC = T_GRASSB              ; cerchio
; apre le stanze laterali (muri -> pavimento; ridisegna se lo schermo e' attivo)
T_BPORTAL = T_FREE8              ; (15/11, C2) sala del trono: portale NERO della leva (posto libero 8 del file del tema 8, calpestabile)
T_LEVER = T_DHOME                ; nella sala del trono lo slot della porta di casa e' la leva (file del tema 8)
; sala del trono con il boss gia' sconfitto: le porte delle stanze laterali (fin_door) diventano pavimento
fin_doors:
        ldx #0
_d      lda fin_door,x
        sta tx
        lda fin_door+1,x
        sta ty
        lda #T_FLOOR
        jsr set_tile
        inx
        inx
        cpx #FIN_DOOR_N*2
        bne _d
        rts

; baule epico (si apre senza chiave; livello bottino massimo, EPIC_ITEMS oggetti)
fin_chests:
        ldx #0
        ldy #0
_c      lda fin_chest,y
        sta cx_x,x
        lda fin_chest+1,y
        sta cx_y,x
        lda #$53                ; tipo 3 (grafica del baule d'oro) + bit 6 = epico + bit 4 = del piano
        sta ch_t,x
        iny
        iny
        inx
        cpx #FIN_CHEST_N
        bne _c
        rts

