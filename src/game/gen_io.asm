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
; GEN_MAIN: genera il piano cur_level in MAP (sala del trono e piani dei boss dei capitoli: mappe fisse); dopo
; stanze, corridoi e scale, i muri (post_walls)
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
        ldx cur_level           ; (18/11) stile della mappa del piano (data/chapters.yaml map.style, tabella lv_look)
        lda lv_look,x
        and #LK_CAVE|LK_SWAMP
        sta lv_cave             ; grotte e palude: macchie al posto dei rettangoli
        and #LK_SWAMP
        sta lv_swamp
        beq +
        lda #0                  ; palude: tutte le 16 isole (i cancelli vanno nelle colonne 0 e 3)
        sta lv_drop
+       jsr gen_rooms
        jsr gen_links
        jsr carve_rooms
        lda lv_cave
        beq +
        jsr cave_smooth
+       lda lv_swamp
        beq +
        jsr swamp_gates         ; palude: cancelli sui bordi ovest ed est al posto delle scale
        jmp post_walls
+       jsr gen_stairs
        jmp post_walls

minsz_tab .byte 4, 5, 6, 4

; ---------------------------------------------------------------------------------------------------------------------
; (18/11, TODO M11) GROTTE (capitolo 3, docs/wiki/dungeon.md): stesso contratto delle stanze (16 celle, vis, rx/ry/rw/rh
; come rettangolo della stanza per mostri e bauli, rcx/rcy pavimento, albero di gen_links), ma
;  - carve_blob: al posto del rettangolo pieno una macchia: passeggiata casuale di (rw+rh)*8 passi dal centro, pennello
;    2x2, sempre dentro il rettangolo della stanza;
;  - carve_worm: al posto del corridoio a L una galleria tortuosa larga 2 dal centro di cc_a a quello di cc_b (3 passi su
;    4 verso la meta, 1 di lato: arriva sempre, ogni passo la tocca);
;  - cave_smooth: un passo di automa cellulare sui muri (un muro con al massimo SM_MAX muri fra gli 8 vicini diventa
;    pavimento: niente spuntoni). Si segnano prima ($80, conta ancora come muro) e si cambiano dopo, cosi' il risultato
;    non dipende dall'ordine di visita.
; Il centro di ogni stanza resta pavimento (primo colpo di pennello) e ogni galleria passa per i due centri: la mappa e'
; collegata come quella delle stanze. Bordo della mappa sempre muro (pennello entro le colonne/righe 1..46).
; ---------------------------------------------------------------------------------------------------------------------
SM_MAX   = 2
WORM_LAT = 64                   ; rand < 64: passo di lato (1 su 4)
lv_cave .byte 0                 ; LK_CAVE se il piano e' a grotte
wx      .byte 0                 ; posizione del pennello (angolo in alto a sinistra del 2x2)
wy      .byte 0
wtx     .byte 0                 ; meta della galleria
wty     .byte 0
bl_x0   .byte 0                 ; limiti del pennello nella stanza
bl_x1   .byte 0
bl_y0   .byte 0
bl_y1   .byte 0
bl_n    .byte 0                 ; passi che restano
cv_k    .byte 0                 ; muri contati fra i vicini

; pavimento 2x2 con l'angolo in (wx, wy)
brush:
        ldy wy
        lda maprow_lo,y
        clc
        adc wx
        sta ptr0
        lda maprow_hi,y
        adc #0
        sta ptr0+1
        lda #T_FLOOR
        ldy #0
        sta (ptr0),y
        iny
        sta (ptr0),y
        ldy #MAPW
        sta (ptr0),y
        iny
        sta (ptr0),y
        rts

; macchia della stanza cur (vis = 1)
carve_blob:
        ldx cur
        lda rx,x
        sta bl_x0
        clc
        adc rw,x
        sbc #1                  ; (C = 0) rx + rw - 2
        sta bl_x1
        lda ry,x
        sta bl_y0
        clc
        adc rh,x
        sbc #1
        sta bl_y1
        lda rw,x
        clc
        adc rh,x
        asl
        asl
        asl
        sta bl_n
        lda rcx,x               ; rcx = rx + rw/2 <= rx + rw - 2 perche' rw >= 4
        sta wx
        lda rcy,x
        sta wy
_l      jsr brush
        dec bl_n
        beq _d
        jsr rand
        lsr                     ; C = verso, bit 0 di A = asse
        tay
        bcc _neg
        tya
        lsr
        bcs _yp
        lda wx
        cmp bl_x1
        bcs _l
        inc wx
        bne _l
_yp     lda wy
        cmp bl_y1
        bcs _l
        inc wy
        bne _l
_neg    tya
        lsr
        bcs _ym
        lda wx
        cmp bl_x0
        beq _l
        dec wx
        bne _l
_ym     lda wy
        cmp bl_y0
        beq _l
        dec wy
        bne _l
_d      rts

; galleria tortuosa larga 2 dal centro della stanza cc_a a quello di cc_b
carve_worm:
        ldx cc_a
        lda rcx,x
        sta wx
        lda rcy,x
        sta wy
        ldx cc_b
        lda rcx,x
        sta wtx
        lda rcy,x
        sta wty
_l      jsr brush
        lda wx
        cmp wtx
        bne _go
        lda wy
        cmp wty
        beq _d
_go     jsr rand
        cmp #WORM_LAT
        bcc _lat
        tay                     ; verso la meta: su x o su y (bit 0 a caso se mancano tutti e due)
        lda wx
        cmp wtx
        beq _ty
        lda wy
        cmp wty
        beq _tx
        tya
        lsr
        bcc _tx
_ty     lda wy
        cmp wty
        bcc _yi
        dec wy
        bpl _l
_yi     inc wy
        bpl _l
_tx     lda wx
        cmp wtx
        bcc _xi
        dec wx
        bpl _l
_xi     inc wx
        bpl _l
_lj     jmp _l
_lat    lsr                     ; di lato: bit 0 asse, bit 1 verso; mai fuori dalle colonne/righe 1..MAPW-3
        bcs _sy
        lsr
        bcs _sxp
        lda wx
        cmp #2
        bcc _lj
        dec wx
        bpl _lj
_sxp    lda wx
        cmp #MAPW-3
        bcs _lj
        inc wx
        bpl _lj
_sy     lsr
        bcs _syp
        lda wy
        cmp #2
        bcc _lj
        dec wy
        bpl _lj
_syp    lda wy
        cmp #MAPH-3
        bcs _lj
        inc wy
        bpl _lj
_d      rts

; un muro vicino (A = tile) conta se e' muro (0) o muro segnato ($80)
cnt     .macro
        lda (\1),y
        and #$7f
        bne +
        inc cv_k
+
        .endm

; un passo di automa cellulare sui muri interni (righe e colonne 1..46): segna, poi cambia
cave_smooth:
        ldx #1
_ry     lda maprow_lo-1,x
        sta ptr0
        lda maprow_hi-1,x
        sta ptr0+1
        lda maprow_lo,x
        sta ptr1
        lda maprow_hi,x
        sta ptr1+1
        lda maprow_lo+1,x
        sta ptr2
        lda maprow_hi+1,x
        sta ptr2+1
        ldy #1
_rx     lda (ptr1),y
        bne _nx
        lda #0
        sta cv_k
        dey
        #cnt ptr0
        #cnt ptr1
        #cnt ptr2
        iny
        #cnt ptr0
        #cnt ptr2
        iny
        #cnt ptr0
        #cnt ptr1
        #cnt ptr2
        dey
        lda cv_k
        cmp #SM_MAX+1
        bcs _nx
        lda #$80
        sta (ptr1),y
_nx     iny
        cpy #MAPW-1
        bne _rx
        inx
        cpx #MAPH-1
        beq +
        jmp _ry
+       lda #<MAP               ; i segnati diventano pavimento
        sta ptr0
        lda #>MAP
        sta ptr0+1
        ldy #0
        ldx #9                  ; 9 pagine: 2304 = 48 x 48
_cv     lda (ptr0),y
        cmp #$80
        bne +
        lda #T_FLOOR
        sta (ptr0),y
+       iny
        bne _cv
        inc ptr0+1
        dex
        bne _cv
        rts


; sala del trono (piano MAXLEVEL): mappa fissa (FMAP), scale e posizioni del boss; stanze laterali aperte se c_won
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
        lda #T_BPORTAL          ; leva tirata: portale per The Endless Abyss
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

; una stanza per cella della griglia 4x4: larghezza e altezza a caso (lv_minw..11), posizione a caso nella cella
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
        lda lv_cave             ; (18/11) grotte: macchia al posto del rettangolo
        beq +
        jsr carve_blob
        jmp _skipr
+       lda rx,x
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

; collegamenti fra le celle: albero casuale dalla cella di partenza (vis), poi qualche anello in piu'; carve_corr
; per ogni coppia
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

; corridoio largo 2 fra le stanze cc_a e cc_b: un tratto orizzontale e uno verticale (carve_h, carve_v)
carve_corr:
        lda lv_swamp            ; (18/11) palude: passerella di assi
        beq +
        jmp carve_plank
+       lda lv_cave             ; (18/11) grotte: galleria tortuosa
        beq +
        jmp carve_worm
+       ldx cc_a
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

; tratto orizzontale largo 2 (righe ch_y, ch_y+1) da ch_x0 a ch_x1
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

; tratto verticale largo 2 (colonne ch_y, ch_y+1) da ch_x0 a ch_x1 (stesse variabili di carve_h, assi scambiati)
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

; scale: quelle in su in una stanza abitabile a caso (st_s), quelle in giu' in un'altra stanza abitabile (st_e) il cui numero
; di cella dista da 5 a 11 (modulo 16) da st_s; dopo 60 tentativi va bene qualunque stanza diversa da st_s
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

; GEN_WALLS: rifinitura dei muri (tile di muro secondo i vicini) su tutta la mappa; la stessa logica e' in
; tools/atlas/gen_atlas.py (src/CLAUDE.md)
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

; ---------------------------------------------------------------------------------------------------------------------
; (18/11, TODO M11) PALUDE (capitolo 2, docs/wiki/dungeon.md "Palude"): i piani 6-9 sono AFFIANCATI da ovest a est in
; un'unica palude. Le isole sono le macchie delle grotte (carve_blob + cave_smooth), l'acqua e' il muro (tile 0, solido),
; le stanze sono collegate da passerelle di assi larghe 1 (carve_plank: a L, solo sull'acqua). Al posto delle scale due
; CANCELLI (swamp_gates): quello delle scale su sul bordo ovest (x = 1, verso il piano prima o il villaggio), quello delle
; scale giu' sul bordo est (x = MAPW-2, verso il piano dopo). La riga di un cancello dipende solo dal seed del capitolo e
; dal confine (gate_row): il cancello est del piano L e quello ovest del piano L+1 stanno sulla stessa riga, quindi
; passando si arriva allo stesso punto del bordo.
; ---------------------------------------------------------------------------------------------------------------------
T_PLANK = T_PATH                ; passerella: posto 14, calpestabile, mai usato nei dungeon (tools/build/swamp_gfx.py)
lv_swamp .byte 0                ; LK_SWAMP se il piano e' di palude
pk_e    .byte 0                 ; fine del tratto di passerella
gr_b    .byte 0                 ; confine (piano a ovest) per gate_row

; passerella sulla casella (tx, ty) se e' acqua
plank_at:
        ldy ty
        lda maprow_lo,y
        sta ptr0
        lda maprow_hi,y
        sta ptr0+1
        ldy tx
        lda (ptr0),y
        bne +
        lda #T_PLANK
        sta (ptr0),y
+       rts

; tratto orizzontale da tx a pk_e (compresi) alla riga ty
pk_h:
_l      jsr plank_at
        lda tx
        cmp pk_e
        beq _d
        bcc _i
        dec tx
        bpl _l
_i      inc tx
        bpl _l
_d      rts

; tratto verticale da ty a pk_e (compresi) alla colonna tx
pk_v:
_l      jsr plank_at
        lda ty
        cmp pk_e
        beq _d
        bcc _i
        dec ty
        bpl _l
_i      inc ty
        bpl _l
_d      rts

; passerella fra i centri delle stanze cc_a e cc_b: orizzontale alla riga di cc_a, poi verticale alla colonna di cc_b
carve_plank:
        ldx cc_a
        ldy cc_b
        lda rcy,x
        sta ty
        lda rcx,x
        sta tx
        lda rcx,y
        sta pk_e
        jsr pk_h
        ldy cc_b
        lda rcy,y
        sta pk_e
        jmp pk_v

; A mod 36
mod36:
-       cmp #36
        bcc +
        sbc #36
        bcs -
+       rts

; A = confine (numero del piano a ovest) -> A = riga del cancello 6..41: (somma delle 6 cifre del seed + gr_tab[confine
; mod 8]) mod 36 + 6 (tabella irregolare: i cancelli non scendono a scala da un piano all'altro)
gate_row:
        and #7
        tax
        lda gr_tab,x
        sta gr_b
        ldx #5
        lda #0
-       clc
        adc c_seedt,x
        dex
        bpl -
        jsr mod36
        clc
        adc gr_b
        jsr mod36
        clc
        adc #6
        rts

gr_tab  .byte 0, 17, 5, 29, 11, 23, 2, 31

; A = riga -> X = cella della colonna 0 nella fascia di quella riga ((riga / 12) * 4)
row_cell:
        ldx #0
-       cmp #12
        bcc +
        sbc #12
        inx
        inx
        inx
        inx
        bne -
+       rts

; cancelli ovest ed est con la passerella fino al centro della stanza della loro fascia (colonna 0 e colonna 3)
swamp_gates:
        lda cur_level           ; ovest: confine con il piano prima
        sec
        sbc #1
        jsr gate_row
        sta ty
        sta st_up_y
        jsr row_cell
        stx st_s
        lda #1
        sta tx
        sta st_up_x
        lda rcx,x
        sta pk_e
        jsr pk_h
        ldx st_s
        lda rcy,x
        sta pk_e
        jsr pk_v
        lda st_up_x
        sta tx
        lda st_up_y
        sta ty
        lda #T_STAIRSU
        jsr set_tile
        lda cur_level           ; est: confine con il piano dopo
        jsr gate_row
        sta ty
        sta st_dn_y
        jsr row_cell
        inx
        inx
        inx
        stx st_e
        lda #MAPW-2
        sta tx
        sta st_dn_x
        lda rcx,x
        sta pk_e
        jsr pk_h
        ldx st_e
        lda rcy,x
        sta pk_e
        jsr pk_v
        lda st_dn_x
        sta tx
        lda st_dn_y
        sta ty
        lda #T_STAIRSD
        jmp set_tile
