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
GEN_STOUT = <GEN_AT + 6         ; (19/11) portale o morte: boss, mostri caldi e bauli lasciati -> STASH
GEN_STIN  = <GEN_AT + 9         ; (19/11) rientro nello stesso piano: STASH -> mostri e bauli
gen_jtab:
        jmp gen_dmain
        jmp post_walls
        jmp st_out
        jmp st_in
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
        ldx cur_level           ; (18/11) stile della mappa del piano (data/chapters.yaml map.style, tabella lv_look):
        lda lv_look,x           ; bit 4-6: grotte, palude, cittadella (19/11); nessuno = stanze
        and #LK_STYLE
        ldx #0
        stx lv_cave
        stx lv_swamp
        stx lv_cit
        cmp #LK_CIT
        bne +
        sta lv_cit              ; cittadella: sale grandi (7..10), tutte presenti
        lda #7
        sta lv_minw
        sta lv_minh
        stx lv_drop
        jmp _gr
+       cmp #LK_SWAMP
        bne +
        sta lv_swamp
        stx lv_drop             ; palude: tutte le 16 isole (i cancelli vanno nelle colonne 0 e 3)
+       and #LK_CAVE|LK_SWAMP
        sta lv_cave             ; grotte e palude: macchie al posto dei rettangoli
_gr     jsr gen_rooms
        jsr gen_links
        jsr carve_rooms
        lda lv_cit
        beq +
        jsr cit_finish          ; cittadella: colonne, passaggi sull'asse, specchio della meta' sinistra
+       lda lv_cave
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
        .virtual $87e8          ; (19/11) variabili di grotte e cittadella fuori dalla RAM sotto l'I/O (fra schermo HUD e puntatori sprite)
wx      .byte ?                 ; posizione del pennello (angolo in alto a sinistra del 2x2)
wy      .byte ?
wtx     .byte ?                 ; meta della galleria
wty     .byte ?
bl_x0   .byte ?                 ; limiti del pennello nella stanza
bl_x1   .byte ?
bl_y0   .byte ?
bl_y1   .byte ?
bl_n    .byte ?                 ; passi che restano
cv_k    .byte ?                 ; muri contati fra i vicini
cit_px   .byte ?
cit_py   .byte ?
cit_na    .byte ?                 ; passaggi sull'asse fatti
cv_vend
        .endv
        .cerror cv_vend > $87f8, "variabili di grotte e cittadella oltre $87F7"

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
        ldx lv_cit              ; (19/11) cittadella: l'albero solo nella meta' sinistra (colonne 0-1), la destra la copia
        beq _gs
        and #$fd                ; colonna 2 -> 0, 3 -> 1
_gs     sta stk
        sta gl_start
        txa
        beq _gh
        ldx #15
_gc     txa
        and #2
        beq _gn
        lda #2
        sta vis,x               ; colonne 2-3: assenti per l'albero (try_cand le salta)
_gn     dex
        bpl _gc
_gh
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
; (18/11, TODO M11) PALUDE (capitolo 2, docs/wiki/dungeon.md "Palude"): i piani generati del capitolo (6-9) sono pezzi
; AFFIANCATI di un'unica palude, in un percorso a caso dal seed del capitolo: dal piano L al piano L+1 si va nella direzione
; d(L) (nord, est, sud, ovest), mai indietro (d(L+1) != opposto di d(L): in 3 passi il percorso non torna su se stesso).
; Le isole sono le macchie delle grotte (carve_blob + cave_smooth), l'acqua e' il muro (tile 0, solido), le passerelle di
; assi larghe 1 uniscono le isole (carve_plank, solo sull'acqua). Al posto delle scale due CANCELLI sul bordo
; (swamp_gates): quello d'ingresso (scale su: verso il piano prima o il villaggio) sul lato opposto a d(L-1), quello
; d'uscita (scale giu': verso il piano dopo o il boss) sul lato d(L). Il primo piano ha l'ingresso su un lato a caso diverso
; dall'uscita, l'ultimo l'uscita su un lato a caso diverso dall'ingresso. Il punto del cancello sul lato (6..41) dipende dal
; seed e dal confine (gate_row), quindi i due piani vicini lo trovano nello stesso punto e si arriva dove si era usciti.
; ---------------------------------------------------------------------------------------------------------------------
T_PLANK = T_PATH                ; passerella: posto 14, calpestabile, mai usato nei dungeon (tools/build/swamp_gfx.py)
lv_swamp .byte 0                ; LK_SWAMP se il piano e' di palude

; ---------------------------------------------------------------------------------------------------------------------
; (19/11, TODO M11) CITTADELLA (capitolo 4, prototipo; docs/wiki/dungeon.md "Cittadella"): stesso contratto delle stanze
; (16 celle, vis, rx/ry/rw/rh, rcx/rcy, albero), ma si genera solo la meta' sinistra (colonne 0-1 della griglia):
;  - sale grandi 7..10 x 7..10, tutte presenti (lv_drop = 0); albero di gen_links e anelli solo fra le celle sinistre;
;  - colonne: un muro su una griglia di 3 caselle (x = 2, 5 .. 20; y = 2, 5 .. 44) dove il quadrato 3x3 intorno e' tutto
;    pavimento, cioe' dentro le sale: un muro con 8 vicini di pavimento non separa mai nulla;
;  - passaggi sull'asse: da 1 a 4 corridoi dritti dalla sala della colonna 1 fino all'asse (x = 24), sulla riga rcy della
;    sala (porte allineate: lo specchio li completa nella sala gemella); almeno uno, quindi il piano e' collegato;
;  - specchio: colonne 24..47 della mappa = colonne 23..0; celle 2-3 = specchio delle 1-0 (rx' = 48 - rx - rw,
;    rcx' = 46 - rcx: i corridoi larghi 2 in rcx, rcx+1 restano sull'asse della sala gemella).
; Le scale (gen_stairs) vengono dopo lo specchio: l'unica cosa non simmetrica.
; Il codice (cit_finish) NON sta qui: e' in src/game/gen_citadel.asm, parte del codice del piano del capitolo 4
; (src/game/ovl_decor.asm, coda di GFX7, a OVP_AT): c'e' solo quando servono i piani della cittadella.
; ---------------------------------------------------------------------------------------------------------------------
lv_cit  .byte 0                 ; LK_CIT se il piano e' una cittadella
cit_finish = OVP_AT+OVJ_GEN     ; (19/11) gen_citadel.asm nel codice del piano del capitolo 4 (ovl_decor.asm)

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

; A = confine (numero del piano da cui si esce) -> A = byte casuale del confine, dipende da tutto il seed e dal confine
; (19/11: prima la somma delle 6 cifre + gr_tab, solo ~195 valori e uguale per i seed anagrammi). Stato del PRNG
; come seed_level, con il confine | $c0 al posto del piano (mai uguale a quello di un piano 1..63); rnd conservato.
gate_hash:
        ora #$c0
        tax
        lda rnd
        pha
        lda rnd+1
        pha
        txa
        jsr seed_mix
        jsr rand                ; A = rnd+1
        sta gr_h
        pla
        sta rnd+1
        pla
        sta rnd
        lda gr_h
        rts

; A = confine -> A = punto del cancello sul lato, 6..41
gate_row:
        jsr gate_hash
        jsr mod36
        clc
        adc #6
        rts

gr_h    .byte 0                 ; risultato di gate_hash

; A = confine -> A = direzione a caso 0..3 (senza vincoli)
gate_hd:
        jsr gate_hash
        sta gr_b
        lsr
        lsr
        lsr
        clc
        adc gr_b
        and #3
        rts

; A = piano L (>= sw_first) -> A = d(L), direzione dal piano L al piano L+1, mai l'opposto di d(L-1)
dir_of:
        sta sw_t
        lda sw_first
        sta sw_k
        jsr gate_hd
        sta sw_d
_l      lda sw_k
        cmp sw_t
        beq _d
        inc sw_k
        lda sw_k
        jsr gate_hd
        sta sw_n
        lda sw_d
        eor #2
        cmp sw_n
        bne +
        inc sw_n
+       lda sw_n
        and #3
        sta sw_d
        jmp _l
_d      lda sw_d
        rts

; A = punto, X = lato (0 nord, 1 est, 2 sud, 3 ovest): cancello in (gx, gy) sul bordo, passerella fino al centro dell'isola
; della sua fascia sul quel lato; ritorna X = stanza
gate_put:
        stx sw_s
        sta sw_p
        ldx #0                  ; fascia = punto / 12
-       cmp #12
        bcc +
        sbc #12
        inx
        bne -
+       txa                     ; X = fascia
        ldy sw_s
        cpy #1
        beq _e
        cpy #3
        beq _w
        cpy #2                  ; nord / sud: cella = fascia (+12 a sud), cancello in (punto, 1) o (punto, 46)
        bne +
        adc #11                 ; (C = 1) + 12
+       sta sw_c
        lda sw_p
        sta tx
        sta gx
        lda #1
        cpy #2
        bne +
        lda #MAPH-2
+       sta ty
        sta gy
        ldx sw_c
        lda rcy,x
        sta pk_e
        jsr pk_v
        ldx sw_c
        lda rcx,x
        sta pk_e
        jsr pk_h
        ldx sw_c
        rts
_e      asl                     ; est / ovest: cella = fascia * 4 (+3 a est), cancello in (46, punto) o (1, punto)
        asl
        ora #3
        bne +
_w      asl
        asl
+       sta sw_c
        lda sw_p
        sta ty
        sta gy
        lda #1
        cpy #3
        beq +
        lda #MAPW-2
+       sta tx
        sta gx
        ldx sw_c
        lda rcx,x
        sta pk_e
        jsr pk_h
        ldx sw_c
        lda rcy,x
        sta pk_e
        jsr pk_v
        ldx sw_c
        rts

; cancelli d'ingresso e d'uscita del piano. (19/11, committente: piano 9 del seed ANOANO con i due cancelli vicinissimi)
; I due cancelli di un piano devono stare ad almeno SW_DMIN caselle (|dx| + |dy|): se il punto del cancello d'uscita e' troppo
; vicino a quello d'ingresso si prova lo stesso lato 12 o 24 caselle piu' in la' (sw_adj), poi si tiene il piu' lontano.
; Il punto d'ingresso di un piano e' quello d'uscita del piano prima, quindi si calcola la catena dal primo piano del capitolo
; (ingresso dal villaggio: gate_row senza correzione): i due piani vicini trovano sempre lo stesso punto.
SW_DMIN = 40
swamp_gates:
        lda cur_level           ; primo piano generato del capitolo
        jsr lv_grp
        txa
        eor #$ff
        sec
        adc cur_level
        sta sw_first
        clc
        adc #CH_LV-2
        sta sw_last
        lda sw_first            ; catena dei punti: ingresso del primo piano dal villaggio
        sec
        sbc #1
        jsr gate_row
        sta sw_pin
        lda sw_first
        sta sw_kk
_k      lda sw_kk
        jsr sw_sin
        sta sw_in
        lda sw_kk
        jsr sw_sout
        sta sw_out
        jsr sw_adj              ; sw_pout
        lda sw_kk
        cmp cur_level
        beq +
        inc sw_kk
        lda sw_pout
        sta sw_pin
        jmp _k
+       lda sw_pin              ; ingresso (scale su)
        ldx sw_in
        jsr gate_put
        stx st_s
        lda gx
        sta st_up_x
        sta tx
        lda gy
        sta st_up_y
        sta ty
        lda #T_STAIRSU
        jsr set_tile
        lda sw_pout             ; uscita (scale giu')
        ldx sw_out
        jsr gate_put
        stx st_e
        lda gx
        sta st_dn_x
        sta tx
        lda gy
        sta st_dn_y
        sta ty
        lda #T_STAIRSD
        jmp set_tile

; A = piano k -> lato del cancello d'ingresso: opposto a d(k-1); nel primo piano a caso, diverso dall'uscita d(k)
sw_sin:
        sta sw_q
        cmp sw_first
        bne +
        jsr dir_of
        sta sw_n2
        lda sw_q
        sec
        sbc #1
        jsr gate_hd
        cmp sw_n2
        bne _r
        adc #0                  ; (C = 1) +1
        and #3
_r      rts
+       sec
        sbc #1
        jsr dir_of
        eor #2
        rts

; A = piano k -> lato del cancello d'uscita: d(k); nell'ultimo piano generato a caso, diverso dall'ingresso
sw_sout:
        cmp sw_last
        beq +
        jmp dir_of
+       sta sw_q
        jsr sw_sin
        sta sw_n2
        lda sw_q
        jsr gate_hd
        cmp sw_n2
        bne _r
        adc #0
        and #3
_r      rts

; A = punto, X = lato -> sw_cx, sw_cy = casella del cancello (come gate_put)
sw_xy:
        cpx #1
        beq _e
        cpx #3
        beq _w
        sta sw_cx               ; nord / sud
        lda #1
        cpx #2
        bne +
        lda #MAPH-2
+       sta sw_cy
        rts
_e      sta sw_cy
        lda #MAPW-2
        sta sw_cx
        rts
_w      sta sw_cy
        lda #1
        sta sw_cx
        rts

; sw_pout = punto d'uscita del piano sw_kk: gate_row(sw_kk), o 12 / 24 piu' in la' (nel giro 6..41) se il primo e' a meno di
; SW_DMIN caselle dal cancello d'ingresso (sw_pin, sw_in); se nessuno basta, il piu' lontano
sw_adj:
        lda sw_pin
        ldx sw_in
        jsr sw_xy
        lda sw_cx
        sta sw_ix
        lda sw_cy
        sta sw_iy
        lda sw_kk
        jsr gate_row
        sta sw_p0
        lda #0
        sta sw_bd
        sta sw_t2
_t      lda sw_p0
        ldx sw_out
        jsr sw_xy
        lda sw_cx               ; distanza = |dx| + |dy|
        sec
        sbc sw_ix
        bcs +
        eor #$ff
        adc #1
+       sta sw_dd
        lda sw_cy
        sec
        sbc sw_iy
        bcs +
        eor #$ff
        adc #1
+       clc
        adc sw_dd
        cmp sw_bd
        bcc +
        sta sw_bd
        ldx sw_p0
        stx sw_pout
+       cmp #SW_DMIN
        bcs _ok
        inc sw_t2
        lda sw_t2
        cmp #3
        bcs _x
        lda sw_p0               ; 12 piu' in la' nel giro 6..41
        clc
        adc #12
        cmp #42
        bcc +
        sbc #36
+       sta sw_p0
        jmp _t
_ok     lda sw_p0
        sta sw_pout
_x      rts

        .virtual $a5e3          ; (19/11) variabili della palude fuori dalla RAM sotto l'I/O: coda degli slot sprite 20-23
sw_last  .byte ?
sw_pin   .byte ?                ; punto d'ingresso e d'uscita del piano sw_kk
sw_pout  .byte ?
sw_kk    .byte ?
sw_q     .byte ?
sw_n2    .byte ?
sw_cx    .byte ?
sw_cy    .byte ?
sw_ix    .byte ?
sw_iy    .byte ?
sw_p0    .byte ?
sw_bd    .byte ?
sw_t2    .byte ?
sw_dd    .byte ?
sw_first .byte ?                ; primo piano generato del capitolo
sw_t    .byte ?
sw_k    .byte ?
sw_d    .byte ?
sw_n    .byte ?
sw_s    .byte ?                 ; gate_put: lato, punto, cella
sw_p    .byte ?
sw_c    .byte ?
gx      .byte ?                 ; cancello
gy      .byte ?
sw_vend
        .endv
        .cerror sw_vend > $a600, "variabili della palude oltre $A5FF"

; ---------------------------------------------------------------------------------------------------------------------
; (19/11) PIANO LASCIATO PER PORTALE O MORTE (levels.asm "stato del piano lasciato"; docs/wiki/salvataggi.md). Lo stato
; compatto e' gia' nello slot (save_level); qui solo cio' che le scale perderebbero:
;  - mostri: il boss (lb_boss) se vivo, poi fino a SX_MAXM in tutto scelti uno alla volta per chiave (so_best): prima i
;    feriti (vita massima - attuale, il piu' ferito prima), poi i svegli (mwake) dal piu' vicino all'eroe; gli altri
;    tornano come con le scale (al loro posto, vita piena, addormentati);
;  - bauli lasciati dai mostri e non ancora aperti (ch_t: bit 3 si', bit 7 no; non il baule del boss, che sta nello slot):
;    fino a SX_MAXC, con casella, numero di oggetti e livello del bottino (il contenuto si genera all'apertura, come prima).
; ---------------------------------------------------------------------------------------------------------------------
so_sel  .fill 32                ; mostri gia' scelti
so_hx   .byte 0                 ; casella dell'eroe
so_hy   .byte 0
so_i    .byte 0
so_bh   .byte 0                 ; chiave migliore (16 bit) e suo mostro
so_bl   .byte 0
so_bx   .byte 0
so_kh   .byte 0
so_kl   .byte 0

st_out:
        lda cur_level
        sta SX_LVL
        lda #0
        sta SX_NM
        sta SX_NC
        ldx #31
-       sta so_sel,x
        dex
        bpl -
        lda px
        ldx px+1
        jsr pix2tile
        sta so_hx
        lda py
        ldx py+1
        jsr pix2tile
        sta so_hy
        ldx lb_boss             ; il boss del piano, se vivo, sempre
        beq _l
        dex
        lda malive,x
        beq _l
        jsr so_add
_l      lda SX_NM
        cmp #SX_MAXM
        bcs _ch
        jsr so_best
        bmi _ch                 ; X = $FF: nessun altro mostro ferito o sveglio
        jsr so_add
        jmp _l
_ch     ldx #0                  ; bauli lasciati dai mostri, non aperti
_c      lda ch_t,x
        and #$88
        cmp #$08
        bne _cn
        inx                     ; il baule del boss (lb_bch = posto + 1) e' gia' nello slot
        cpx lb_bch
        php
        dex
        plp
        beq _cn
        lda SX_NC
        cmp #SX_MAXC
        bcs _d
        asl                     ; Y = SX_NC * 5
        asl
        adc SX_NC
        tay
        lda cx_x,x
        sta SX_CH,y
        lda cx_y,x
        sta SX_CH+1,y
        lda ch_t,x
        sta SX_CH+2,y
        stx so_i
        txa
        asl
        asl
        tax
        lda ch_i,x
        sta SX_CH+3,y
        lda ch_b,x
        sta SX_CH+4,y
        ldx so_i
        inc SX_NC
_cn     inx
        cpx #CH_MAX
        bne _c
_d      rts

; mostro X nella STASH (SX_MON + SX_NM * 8)
so_add:
        stx so_i
        lda #1
        sta so_sel,x
        lda SX_NM
        asl
        asl
        asl
        tay
        txa
        sta SX_MON,y
        lda mix,x
        sta SX_MON+1,y
        lda miy,x
        sta SX_MON+2,y
        lda mhp,x
        sta SX_MON+3,y
        lda mhph,x
        sta SX_MON+4,y
        lda mhm,x
        sta SX_MON+5,y
        lda mhmh,x
        sta SX_MON+6,y
        lda mwake,x
        sta SX_MON+7,y
        inc SX_NM
        ldx so_i
        rts

; X = mostro vivo, non ancora scelto, con la chiave piu' alta (> 0), $FF se nessuno (N = 1). Chiave: ferito = $8000 +
; vita mancante; sveglio = $4000 + 255 - distanza dall'eroe (|dx| + |dy|); altrimenti 0 (non si conserva).
so_best:
        lda #0
        sta so_bh
        sta so_bl
        lda #$ff
        sta so_bx
        ldx #0
_m      cpx lb_cnt
        bcc +
        jmp _r
+       lda malive,x
        beq _n
        lda so_sel,x
        bne _n
        lda mhm,x               ; vita mancante = massima - attuale
        sec
        sbc mhp,x
        sta so_kl
        lda mhmh,x
        sbc mhph,x
        sta so_kh
        ora so_kl
        beq _w
        lda so_kh
        ora #$80
        sta so_kh
        bne _cmp
_w      lda mwake,x
        beq _n
        lda mix,x               ; distanza dall'eroe
        sec
        sbc so_hx
        bcs +
        eor #$ff
        adc #1
+       sta so_kl
        lda miy,x
        sec
        sbc so_hy
        bcs +
        eor #$ff
        adc #1
+       clc
        adc so_kl
        eor #$ff                ; 255 - distanza
        sta so_kl
        lda #$40
        sta so_kh
_cmp    lda so_kh               ; chiave > migliore?
        cmp so_bh
        bcc _n
        bne _b
        lda so_kl
        cmp so_bl
        bcc _n
        beq _n
_b      lda so_kh
        sta so_bh
        lda so_kl
        sta so_bl
        stx so_bx
_n      inx
        jmp _m
_r      ldx so_bx
        rts

; rientro nello stesso piano: dopo la rigenerazione (scale) i mostri e i bauli della STASH tornano come erano
st_in:
        ldy #0
_m      cpy SX_NM
        bcs _ch
        sty so_i
        tya
        asl
        asl
        asl
        tay
        ldx SX_MON,y
        cpx lb_cnt
        bcs _mn
        lda malive,x
        beq _mn
        lda SX_MON+1,y
        sta mix,x
        lda SX_MON+2,y
        sta miy,x
        lda SX_MON+3,y
        sta mhp,x
        lda SX_MON+4,y
        sta mhph,x
        lda SX_MON+5,y
        sta mhm,x
        lda SX_MON+6,y
        sta mhmh,x
        lda SX_MON+7,y
        sta mwake,x
        stx so_bx
        lda mix,x               ; posizione fine dalla casella (come init_monsters_rt)
        jsr tile_to_pix
        ldx so_bx
        lda tmp0
        sta mxl,x
        lda tmp1
        sta mxh,x
        lda miy,x
        jsr tile_to_pix
        ldx so_bx
        lda tmp0
        sta myl,x
        lda tmp1
        sta myh,x
_mn     ldy so_i
        iny
        bne _m
_ch     lda tp_on               ; set_tile di chest_add: niente ridisegno (VIC spento qui)
        pha
        lda #0
        sta tp_on
        ldy #0
_c      cpy SX_NC
        bcs _d
        sty so_i
        tya
        asl
        asl
        adc so_i
        tay
        lda SX_CH,y
        sta loot_x
        lda SX_CH+1,y
        sta loot_y
        sty so_bl
        lda SX_CH+2,y
        jsr chest_add           ; X = posto
        bcs _d                  ; bauli pieni
        txa
        asl
        asl
        tax
        ldy so_bl
        lda SX_CH+3,y
        sta ch_i,x
        lda SX_CH+4,y
        sta ch_b,x
        ldy so_i
        iny
        bne _c
_d      pla
        sta tp_on
        rts

