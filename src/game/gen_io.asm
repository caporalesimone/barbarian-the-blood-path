; ===================================================================
;  gen_io.asm - generatore dei piani nella RAM sotto l'I/O (GEN_AT). Nel PRG sta dopo la grafica fissa (dato
;  morto dopo l'avvio): `start` lo copia a GEN_AT con gen_install. Si chiama SOLO da gen_call (dungeon.asm), con
;  $01 = $34 e interrupt spenti: niente accessi a VIC, SID, CIA, RAM dei colori o KERNAL; le routine residenti
;  chiamate (rand, rndrange, set_tile, seed_level, clear_map, fin_doors) non ne fanno.
;  Attenzione: set_tile con tp_on = 1 ridisegna lo schermo (tile_patch, scrive anche i colori): durante la
;  generazione tp_on e' 0.
; ===================================================================
GEN_MAIN  = <GEN_AT             ; punti d'ingresso (byte basso, per gen_call)
GEN_WALLS = <GEN_AT + 3
gen_jtab:
        jmp gen_dmain
        jmp post_walls
gen_dmain:
        lda cur_level
        cmp #MAXLEVEL
        bne +
        jmp gen_final
+       lda lv_cboss            ; (12/11) piano del boss di un capitolo: mappa fissa gia' in MAP (bmap_load)
        beq +
        jmp gen_cboss
+       jsr seed_level
        ; stile del piano (dipende da seed e piano)
        jsr rand
        sta lv_style
        and #3
        tax
        lda minsz_tab,x
        sta lv_minw
        lda lv_style
        lsr
        lsr
        and #3
        tax
        lda minsz_tab,x
        sta lv_minh
        lda lv_style
        lsr
        lsr
        lsr
        lsr
        and #3
        sta lv_drop             ; probabilita' (n/8) che una stanza manchi
        lda lv_style
        .rept 6
        lsr
        .endrept
        clc
        adc #3
        sta lv_xl               ; 1 collegamento extra ogni 3..6
        jsr clear_map
        jsr gen_rooms
        jsr gen_links
        jsr carve_rooms
        jsr gen_stairs
        jsr post_walls
        rts

minsz_tab .byte 4, 5, 6, 4


gen_final:
        jsr seed_level          ; il generatore casuale resta deterministico (contenuto dei bauli)
        lda c_won               ; boss gia' sconfitto: stanze laterali aperte
        beq +
        jsr fin_doors
+       lda #FIN_SX             ; scale di arrivo (in basso)
        sta st_up_x
        lda #FIN_SY
        sta st_up_y
        lda #FIN_AX             ; la leva (stanza dei tesori, chiusa fino alla morte del boss)
        sta st_dn_x
        sta tx
        lda #FIN_AY
        sta st_dn_y
        sta ty
        lda c_lever
        beq +
        lda #T_PORTAL           ; leva tirata: portale per The Endless Abyss
        jsr set_tile
+       ldx #15                 ; stanze logiche: 0 = corridoio (arrivo), 1 = sala del trono (boss)
        lda #0
_v      sta vis,x
        dex
        bpl _v
        lda #1
        sta vis
        sta vis+1
        sta st_e
        lda #0
        sta st_s
        lda #FIN_SX
        sta rcx
        lda #FIN_SY
        sta rcy
        lda #FIN_CX
        sta rcx+1
        lda #FIN_CY
        sta rcy+1
        jmp post_walls          ; muri, pavimenti variati e figure (i marcatori)

; (12/11, TODO M1) piano del boss di un capitolo: la mappa di base (file BOSSCHc) e' in MAP; due stanze logiche come
; nella sala del trono: 0 = arrivo (scale), 1 = sala del boss (centro: il boss del piano, place_boss)
gen_cboss:
        jsr seed_level
        ldx #15
        lda #0
_v      sta vis,x
        dex
        bpl _v
        lda #1
        sta vis
        sta vis+1
        sta st_e
        lda #0
        sta st_s
        lda bm_sx
        sta st_up_x
        sta rcx
        lda bm_sy
        sta st_up_y
        sta rcy
        lda bm_bx
        sta st_dn_x
        sta rcx+1
        lda bm_by
        sta st_dn_y
        sta rcy+1
        jmp post_walls

gen_rooms:
        ldx #0
_cell   stx cur
        lda #11
        sec
        sbc lv_minw
        jsr rndrange
        clc
        adc lv_minw
        sta rw,x
        lda #11
        sec
        sbc lv_minh
        jsr rndrange
        clc
        adc lv_minh
        sta rh,x
        txa
        and #3
        tay
        lda mul12,y
        sta tmp0
        txa
        lsr
        lsr
        tay
        lda mul12,y
        sta tmp1
        lda #11
        sec
        sbc rw,x
        jsr rndrange
        clc
        adc tmp0
        adc #1
        sta rx,x
        lda #11
        sec
        sbc rh,x
        jsr rndrange
        clc
        adc tmp1
        adc #1
        sta ry,x
        lda rw,x
        lsr
        clc
        adc rx,x
        sta rcx,x
        lda rh,x
        lsr
        clc
        adc ry,x
        sta rcy,x
        ldx cur
        inx
        cpx #16
        beq +
        jmp _cell
+       rts

; scava le stanze raggiungibili (vis=1)
carve_rooms:
        ldx #0
_cell   stx cur
        lda vis,x
        cmp #1
        bne _skipr
        lda rx,x
        sta tmp2
        lda ry,x
        sta tmp3
        lda rh,x
        sta tmp4
        lda rw,x
        sta tmp5
_row    ldy tmp3
        lda maprow_lo,y
        clc
        adc tmp2
        sta ptr0
        lda maprow_hi,y
        adc #0
        sta ptr0+1
        ldy #0
        lda #T_FLOOR
_col    sta (ptr0),y
        iny
        cpy tmp5
        bne _col
        inc tmp3
        dec tmp4
        bne _row
_skipr  ldx cur
        inx
        cpx #16
        bne _cell
        rts

try_cand:                   ; A = cella vicina; aggiunge se non visitata
        tax
        lda vis,x
        bne _no
        ldy ncand
        txa
        sta cand,y
        inc ncand
_no     rts

gen_links:
        ldx #15
        lda #0
_v      sta vis,x
        dex
        bpl _v
        lda #16
        jsr rndrange
        sta stk
        sta gl_start
        lda lv_drop
        beq _nd0
        ldx #15
_dl     cpx gl_start
        beq _dn
        lda #8
        jsr rndrange
        cmp lv_drop
        bcs _dn
        lda #2                  ; stanza assente
        sta vis,x
_dn     dex
        bpl _dl
_nd0    ldx stk
        lda #1
        sta vis,x
        lda #1
        sta sp_
_loop   ldx sp_
        beq _dfsdone
        lda stk-1,x
        sta cur
        lda #0
        sta ncand
        lda cur
        and #3
        beq _nl
        lda cur
        sec
        sbc #1
        jsr try_cand
_nl     lda cur
        and #3
        cmp #3
        beq _nr
        lda cur
        clc
        adc #1
        jsr try_cand
_nr     lda cur
        cmp #4
        bcc _nu
        sec
        sbc #4
        jsr try_cand
_nu     lda cur
        cmp #12
        bcs _nd
        clc
        adc #4
        jsr try_cand
_nd     lda ncand
        bne _pick
        dec sp_
        jmp _loop
_pick   jsr rndrange
        tax
        lda cand,x
        sta cc_b
        lda cur
        sta cc_a
        jsr carve_corr
        ldx cc_b
        lda #1
        sta vis,x
        ldy sp_
        txa
        sta stk,y
        inc sp_
        jmp _loop
_dfsdone
        ; se sono rimaste troppe poche stanze, rigenera senza stanze assenti
        ldx #15
        ldy #0
_cnt    lda vis,x
        cmp #1
        bne _cn
        iny
_cn     dex
        bpl _cnt
        cpy #7
        bcs _okc
        lda lv_drop
        beq _okc
        lda #0
        sta lv_drop
        jmp gen_links
_okc    ldx #0
_ex     stx cur
        lda vis,x
        cmp #1
        bne _nex2
        txa
        and #3
        cmp #3
        beq _nex
        lda vis+1,x
        cmp #1
        bne _nex
        lda lv_xl
        jsr rndrange
        bne _nex
        ldx cur
        stx cc_a
        inx
        stx cc_b
        jsr carve_corr
_nex    ldx cur
        cpx #12
        bcs _nex2
        lda vis+4,x
        cmp #1
        bne _nex2
        lda lv_xl
        jsr rndrange
        bne _nex2
        ldx cur
        stx cc_a
        txa
        clc
        adc #4
        sta cc_b
        jsr carve_corr
_nex2   ldx cur
        inx
        cpx #16
        bne _ex
        rts

carve_corr:
        ldx cc_a
        ldy cc_b
        lda rcx,x
        cmp rcx,y
        bcc _o1
        lda rcx,y
        sta ch_x0
        lda rcx,x
        sta ch_x1
        jmp _h
_o1     lda rcx,x
        sta ch_x0
        lda rcx,y
        sta ch_x1
_h      lda rcy,x
        sta ch_y
        jsr carve_h
        ldx cc_a
        ldy cc_b
        lda rcy,x
        cmp rcy,y
        bcc _o2
        lda rcy,y
        sta ch_x0
        lda rcy,x
        sta ch_x1
        jmp _v
_o2     lda rcy,x
        sta ch_x0
        lda rcy,y
        sta ch_x1
_v      lda rcx,y
        sta ch_y
        jsr carve_v
        rts

carve_h:
        lda ch_x0
        sta tx
_l      lda ch_y
        sta ty
        lda #T_FLOOR
        jsr set_tile
        inc ty
        lda #T_FLOOR
        jsr set_tile
        lda tx
        cmp ch_x1
        beq _d
        inc tx
        bne _l
_d      rts

carve_v:
        lda ch_x0
        sta ty
_l      lda ch_y
        sta tx
        lda #T_FLOOR
        jsr set_tile
        inc tx
        lda #T_FLOOR
        jsr set_tile
        lda ty
        cmp ch_x1
        beq _d
        inc ty
        bne _l
_d      rts

gen_stairs:
_p1     lda #16
        jsr rndrange
        tax
        lda vis,x
        cmp #1
        bne _p1
        stx st_s
        lda #60
        sta gs_try
_p2     lda #16
        jsr rndrange
        tax
        lda vis,x
        cmp #1
        bne _p2
        cpx st_s
        beq _p2
        dec gs_try
        beq _got                ; troppi tentativi: accetta
        txa
        sec
        sbc st_s
        and #15
        cmp #5
        bcc _p2
        cmp #12
        bcs _p2
_got    stx st_e
        ldx st_s
        lda rcx,x
        sta st_up_x
        sta tx
        lda rcy,x
        sta st_up_y
        sta ty
        lda #T_STAIRSU
        jsr set_tile
        ldx st_e
        lda rcx,x
        sta st_dn_x
        sta tx
        lda rcy,x
        sta st_dn_y
        sta ty
        lda cur_level
        cmp #MAXLEVEL
        bcs _nodn
        lda #T_STAIRSD
        jsr set_tile
_nodn   rts

post_walls:
        ldx #0
_ry     lda maprow_lo,x
        sta ptr0
        lda maprow_hi,x
        sta ptr0+1
        lda maprow_lo+1,x
        sta ptr1
        lda maprow_hi+1,x
        sta ptr1+1
        ldy #0
_rx     lda (ptr0),y
        bne _nx
        lda (ptr1),y
        cmp #2
        bcc _nx
        lda #T_WALLFACE
        sta (ptr0),y
_nx     iny
        cpy #MAPW
        bne _rx
        inx
        cpx #MAPH-1
        bne _ry
        lda #<MAP
        sta ptr0
        lda #>MAP
        sta ptr0+1
        ldy #0
        ldx #9
_pv     lda (ptr0),y
        cmp #T_FLOOR
        beq _pf
        cmp #$80
        bcc _pn
        and #$7f                ; marcatore ($80|tile, solo sala del trono): figura su un pavimento. Il caso si
        sta (ptr0),y            ; consuma come per il pavimento (stessa sequenza di quando le figure si disegnavano dopo)
        jsr rand
        jmp _pn
_pf     jsr rand
        and #7
        cmp #2
        bcs _pn
        clc
        adc #T_FLOORB
        sta (ptr0),y
_pn     iny
        bne _pv
        inc ptr0+1
        dex
        bne _pv
        rts

