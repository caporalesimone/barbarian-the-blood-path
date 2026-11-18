; ===================================================================
;  game.asm  -  stato, statistiche, mostri, combattimento, HUD, sprite
; ===================================================================

; ---- runtime mostri (non salvato)
;@map $9600+384 "MRT: mostri in gioco (12 tabelle x 32: posizione fine, vita, ricarica, stordimento...), copiati in STASHM"
        .virtual $9600
mxl     .fill 32
mxh     .fill 32
myl     .fill 32
myh     .fill 32
mhp     .fill 32
mcd     .fill 32
mstun   .fill 32
macc    .fill 32
mwake   .fill 32
mhph    .fill 32        ; vita attuale: byte alto (mhp = byte basso)
mhm     .fill 32        ; vita massima (16 bit)
mhmh    .fill 32
        .endv

; ---- occupazione caselle (un solo essere per casella)
        .virtual $9420
ot_x      .byte ?               ; casella attuale dell'essere che si muove
ot_y      .byte ?
nt_x      .byte ?               ; casella di arrivo proposta
nt_y      .byte ?
occ_self  .byte ?               ; indice mostro da ignorare ($ff = giocatore)
occ_x     .byte ?
pm_try    .byte ?
mo_xl     .byte ?               ; posizione di partenza del mostro (per annullare il passo)
mo_xh     .byte ?
mo_yl     .byte ?
mo_yh     .byte ?
        .endv

; ---- stato livello (salvato su disco)
;@map LVLBLK..LVLEND "LVLBLK: stato del piano (mostri, bauli, nebbia EXPL), salvato compatto negli slot LVRAM e copiato in STASH" layout
        .virtual $9800
LVLBLK
lb_lvl  .byte ?          ; piano di questo stato
lb_cnt  .byte ?          ; mostri del piano
lb_boss .byte ?          ; indice boss + 1 (0 = nessuno)
lb_bn1  .byte ?          ; nome boss: nome / epiteto
lb_bn2  .byte ?          ; (seconda parte del nome del boss)
lb_bch  .byte ?          ; baule del boss: posto + 1 (0 = nessuno); si salva finche' non e' aperto
mtype   .fill 32         ; tipo dei 32 mostri
malive  .fill 32         ; mostri vivi
mix     .fill 32         ; casella X dei mostri
miy     .fill 32         ; casella Y dei mostri
CH_MAX  = 15            ; bauli nel piano al massimo (generati + lasciati dai mostri)
CH_GEN_MAX = 4          ; bauli generati con il piano al massimo (posti 0..3; + il baule del boss)
cx_x    .fill CH_MAX     ; casella X dei bauli
cx_y    .fill CH_MAX     ; casella Y dei bauli
ch_t    .fill CH_MAX      ; 0 vuoto, 1 normale, 2 chiave, 3 oro; bit3 = lasciato da un mostro, contenuto da
                          ; generare all'apertura (ch_i = oggetti, ch_b = livello bottino nel 1o posto);
                          ; bit4 = generato con il piano, bit5 = aperto, bit6 = epico, bit7 = contenuto generato
ch_i    .fill CH_MAX*4   ; contenuto dei bauli: id oggetto (4 posti)
ch_b    .fill CH_MAX*4   ; contenuto dei bauli: bonus (4 posti)
EXPL    .fill 288        ; mappa esplorata: 1 bit per tile (48x48)
LVLEND
        .endv

; ---- personaggio (salvato su disco)
NAME_LEN = 12                   ; caratteri del nome dell'eroe
STASH_N  = 24                   ; oggetti nel baule di casa (07/11 sera: da 48 a 24), nel blocco dell'eroe (08/11 sera)
PACK_N   = 8                    ; posti dello zaino (07/11 sera: da 16 a 8); l'equipaggiamento segue: indici PACK_N..PACK_N+3
;@map CHRBLK..CHREND "CHRBLK: eroe e baule della locanda, il blocco salvato nel file save-0N (docs/wiki/FORMATO_DATI.md)" layout
        .virtual $9500
CHRBLK
c_magic .byte ?          ; versione del formato di salvataggio (SAVE_VER): primo byte del file
c_seed  .word ?          ; seed numerico del mondo (dai 6 caratteri di c_seedt)
c_loc   .byte ?          ; luogo attuale: 0 villaggio, 1..20 piano
c_lvl   .byte ?          ; livello dell'eroe
c_xp    .fill 3          ; esperienza (24 bit)
c_gold  .word ?          ; oro (16 bit)
c_hp    .word ?          ; vita attuale (16 bit)
c_vis   .fill 3          ; 1 bit per piano (1..24): stato salvato su SAVES
c_retlvl .byte ?         ; piano a cui riporta il portale
c_retx  .word ?          ; X di ritorno del portale (pixel)
c_rety  .word ?          ; Y di ritorno del portale (pixel)
c_portal .byte ?         ; 1 = portale aperto nel villaggio
c_beltt .fill 4          ; cintura: 4 posti, una pozione ciascuno (id, 0 = vuoto). Pergamene: pila nello zaino
c_skill .byte ?          ; abilita' selezionata
c_kills .word ?          ; mostri uccisi (16 bit)
c_won   .byte ?          ; 1 = boss finale sconfitto
c_lever .byte ?          ; 1 = leva tirata: portale per The Endless Abyss nella sala del trono
c_maxd  .byte ?          ; piano piu' profondo raggiunto
c_name  .fill NAME_LEN   ; nome (NAME_LEN codici schermo)
c_px    .word ?          ; X dell'eroe (pixel)
c_py    .word ?          ; Y dell'eroe (pixel)
c_pack  .fill PACK_N     ; zaino: id oggetto (0 = vuoto), PACK_N posti
c_eq    .fill 4          ; equipaggiamento: arma, armatura, scudo, cintura
c_seedt .fill 6          ; seed: 6 cifre in base 36 (0-9, A-Z = 0..35)
c_gver  .byte ?          ; versione del generatore dungeon
c_packb .fill PACK_N         ; bonus +N degli oggetti nello zaino (anelli: caratteristica; pergamene: quantita')
c_eqb   .fill 4          ; bonus +N degli oggetti equipaggiati
c_keys  .byte ?          ; chiavi possedute
c_packd .fill PACK_N         ; durabilita' attuale degli oggetti nello zaino (armi, armature, scudi; 0 = non si usura)
c_eqd   .fill 4          ; ... e dell'equipaggiamento (segue lo zaino: indice PACK_N..PACK_N+3 come c_pack/c_eq)
c_packm .fill PACK_N         ; durabilita' massima
c_eqm   .fill 4          ; durabilita' massima (equipaggiamento)
c_game  .fill 3          ; bit 0..8: numero della partita (1..511); bit 9..23: minuti giocati (0..32767)
c_deaths .word ?         ; morti (16 bit, si ferma a 65535)
c_sgold .word ?          ; oro nel baule di casa in DECINE (10/11; 16 bit = 655350 monete): la morte non lo tocca; totale = c_gold + 10 x c_sgold
c_sadd  .fill 3          ; (11/11, SAVE_VER $C6) punti statistica spesi in FOR, DES, COS (schermata C, charsheet.asm)
c_resp  .byte ?          ; gettoni respec (0..RESP_MAX)
c_chap  .byte ?          ; (12/11, SAVE_VER $C7, TODO M1) capitolo in cui si gioca 1..CHAPTERS (villaggio TWNc, src/game/chapter.asm)
c_unl   .byte ?          ; capitolo piu' alto sbloccato (uccidere il boss del capitolo c sblocca c+1)
; baule di casa (08/11 sera, SAVE_VER $C3): dentro il blocco dell'eroe, un solo record per eroe e baule. Uscendo di
; casa dopo una modifica si salva tutto con una sola scrittura (prima: record a parte e l'eroe non si salvava, TODO 2.6)
st_id   .fill STASH_N    ; baule della locanda: id dei 24 oggetti (0 = vuoto)
st_b    .fill STASH_N    ; baule della locanda: bonus
st_du   .fill STASH_N    ; baule della locanda: durabilita' attuale
st_m    .fill STASH_N    ; baule della locanda: durabilita' massima
c_qst   .byte ?          ; (17/11, SAVE_VER $C8, concept) quest prese: (18/11) maschera, bit n-1 = quest n (file QSTn); in fondo al blocco
CHREND
        .endv
        .cerror CHREND > mfar, "blocco personaggio sovrapposto a mfar"

; ---- variabili (non salvate)
        .virtual $9100
ap_b       .byte ?
ap_d       .byte ?          ; give_item: durabilita' attuale e massima (0 = da generare)
ap_m       .byte ?
tod_cnt    .byte ?          ; fotogrammi alla prossima lettura dell'orologio TOD (tod_tick, ogni 256)
gi_force   .byte ?          ; gen_item: categoria imposta (0 = dai pesi del bottino)
        .endv
        .virtual $9200
solidtab   .fill 48         ; tile solidi del luogo attuale (copia di solid_dun / solid_town, load_location)
        .endv
        .virtual gi_force+1
gi_t       .byte ?          ; gen_item: livello oggetto obiettivo (CL / CL_PF)
gi_l       .byte ?          ; gen_item: livello oggetto tirato (0..MAXLL): candidati e magia
ps_n       .byte ?
gi_cat     .byte ?
rm_min     .byte ?
rm_max     .byte ?
la_p       .byte ?
tmpv2      .byte ?
dc_t       .byte ?
dc_n       .byte ?
gi_ll      .byte ?
ch_cur     .byte ?
af_x       .byte ?
af_y       .byte ?
ch_cnt     .byte ?
ch_gold    .word ?          ; oro trovato nell'ultimo baule aperto (16 bit: i bauli epici superano 255)
ch_msg     .byte ?
pc_k       .byte ?
gv_why     .byte ?          ; give_item fallito: 0 zaino pieno, 1 cintura piena, 2 pergamene al massimo
hud_dirty  .byte ?
cur_m      .byte ?
km_i       .byte ?
rt_i       .byte ?
m_dxl      .byte ?
m_dxh      .byte ?
m_dyl      .byte ?
m_dyh      .byte ?
m_adx      .byte ?
m_ady      .byte ?
m_steps    .byte ?
ha_x       .word ?
ha_y       .word ?
ha_hw      .byte ?
ha_hh      .byte ?
cur_sk     .byte ?
gcd        .byte ?
fx_kind    .byte ?
fx_timer   .byte ?
fx_x       .word ?
fx_y       .word ?
flash_t    .byte ?
ptx        .byte ?
pty        .byte ?
lptx       .byte ?
lpty       .byte ?
me_x       .byte ?
me_y       .byte ?
me_x0      .byte ?
me_x1      .byte ?
me_y1      .byte ?
new_lvl    .byte ?
spawn_mode .byte ?
sfx_t      .byte ?
sfx_w      .byte ?
sfx_sx     .byte ?
sfx_sy     .byte ?
sfx_f      .byte ?              ; frequenza attuale (byte alto) e salita per frame
sfx_d      .byte ?
sfx_own    .byte ?              ; fotogrammi in cui la voce 1 resta agli effetti (rilascio compreso)
loot_x     .byte ?
loot_y     .byte ?
lv         .byte ?
sp_cnt     .byte ?
sp_strong  .byte ?
bs_m       .byte ?
bs_slot    .byte ?
lv_style   .byte ?
lv_drop    .byte ?
lv_xl      .byte ?
lv_minw    .byte ?
lv_minh    .byte ?
gs_try     .byte ?
gf_n       .byte ?
gf_t       .byte ?
fb_wave    .byte ?              ; ondate di evocazione gia' fatte dal boss finale (0..3)
gl_start   .byte ?
st_hold    .byte ?
pend_lvl    .byte ?              ; piano lasciato per portale/morte: stato in STASH, non salvato (0 = nessuno)
sk_t        .byte ?              ; frame residui di visualizzazione del nome dell'abilita' nell'HUD
ch_blk      .byte ?              ; 1 = Fire su baule rifiutato (mostro vicino)
cb_i        .byte ?
st_kind    .byte ?
io_dir     .byte ?
io_what    .byte ?
io_lvl     .byte ?
io_quiet   .byte ?
wbuf       .fill 16
cs_pend    .fill 3          ; (11/11) schermata C: punti in attesa su FOR, DES, COS (0 fuori dalla schermata: pts_avail)
cs_mode    .byte ?          ; (15/11) schermata C: 0 tutte le voci, 1 solo respec, 2 nessuna (prima nel codice)
cs_nv      .fill 12         ; (15/11) schermata C: hpmax..s_dk con i punti in attesa (anteprima)
cs_sg      .byte ?          ; (15/11) schermata C: bit 7 = valore con '+' (cs_pv)
cs_nw      .byte ?
cs_cu      .byte ?
cs_k       .byte ?
cs_end
        .endv
GVER       = 5


; categorie, id oggetti e tutte le tabelle di bilanciamento: vedi db.asm (generato)

        .include "sfx.inc"      ; effetti sonori (tabelle, sfx_play, sfx_step)

exprow_lo
        .for i = 0, i < 48, i = i + 1
        .byte <(EXPL + i*6)
        .next
exprow_hi
        .for i = 0, i < 48, i = i + 1
        .byte >(EXPL + i*6)
        .next

; ===================================================================
;  utilita'
; ===================================================================
; (15/11, TODO D12) casella del mostro X: A = casella x / y; X NON preservato (i chiamanti ricaricano l'indice)
mon_tx: lda mxl,x
        pha
        lda mxh,x
        jmp mon_tp
mon_ty: lda myl,x
        pha
        lda myh,x
mon_tp  tax
        pla
; A = lo, X = hi (pixel) -> A = tile
pix2tile:
        sta tmp6
        txa
        asl
        asl
        asl
        asl
        sta tmp7
        lda tmp6
        lsr
        lsr
        lsr
        lsr
        ora tmp7
        rts

; (11/11, O11) tmp0/tmp1 = -tmp0/tmp1 (anche ui.asm gold_need)
neg16:
        lda #0
        sec
        sbc tmp0
        sta tmp0
        lda #0
        sbc tmp1
        sta tmp1
        rts

; |tmp0/tmp1| saturato a 255 -> A
sabs:
        lda tmp1
        bpl _p
        jsr neg16
_p      lda tmp1
        beq _s
        lda #255
        rts
_s      lda tmp0
        rts

; A = colore bordo, X = durata
set_flash:
        sta BORDER
        stx flash_t
        rts

; ===================================================================
;  oggetti e inventario
; ===================================================================
; A = id. C=0 ok, C=1 zaino pieno
add_to_pack:
        ldy #0
_f      ldx c_pack,y
        beq _put
        iny
        cpy #PACK_N
        bne _f
        jsr ap_clr              ; zaino pieno: la durabilita' data non resta per il prossimo oggetto
        sec
        rts
_put    sta c_pack,y
        ldx ap_m                ; durabilita': quella data (baule di casa) o nuova (bottino, negozio)
        bne _d
        jsr dur_roll            ; A = oggetto (08/11: prima riceveva ap_m = 0 e gli oggetti nuovi non si usuravano)
_d      lda ap_b
        sta c_packb,y
        lda ap_d
        sta c_packd,y
        lda ap_m
        sta c_packm,y
        jsr ap_clr
        clc
        rts
ap_clr  lda #0                  ; ap_b/ap_d/ap_m consumati
        sta ap_b
        sta ap_d
        sta ap_m
        rts

; durabilita' nuova per l'oggetto A (arma, armatura, scudo; altri: 0): ap_d = ap_m = tiro.
; Con probabilita' DUR_WP% il livello oggetto pesa: uniforme fra DUR_MIN + DUR_PI x ilvl e DUR_MAX;
; altrimenti uniforme fra DUR_MIN e DUR_MAX (tools/simulators/sim_durability.py). Prezzo 0 (pugni): 0.
dur_roll:
        pha
        stx wr_x                ; X e Y conservati
        sty wr_y
        tax
        lda #0
        sta ap_d
        sta ap_m
        lda itcat,x
        cmp #CAT_SHIELD+1
        bcs _r
        txa
        asl
        tay
        lda itprice,y
        ora itprice+1,y
        beq _r
        lda #DUR_MIN
        sta tmp4                ; minimo
        lda #100
        jsr rndrange
        cmp #DUR_WP
        bcs _u
        lda itilvl,x            ; caso pesato: minimo = DUR_MIN + DUR_PI x ilvl
        ldx #DUR_PI
        jsr mul8
        clc
        adc #DUR_MIN
        sta tmp4
_u      lda #<(DUR_MAX+1)
        sec
        sbc tmp4
        jsr rndrange
        clc
        adc tmp4
        sta ap_d
        sta ap_m
_r      ldx wr_x
        ldy wr_y
        pla
        rts

SCR_MAX = 10                    ; pergamene al massimo (08/11, prima 4): una pila nello zaino e una nel baule di casa

; A = id, ap_b = bonus: pozione -> primo posto libero della cintura; pergamena -> pila nello zaino
; (ap_b = quantita', 0 = 1); altro -> zaino. C=1 se non c'e' posto (motivo in gv_why).
give_item:
        tax
        lda itcat,x
        cmp #CAT_POTION
        beq _pot
        cmp #CAT_SCROLL
        beq _scr
        lda #0
        sta gv_why
        txa
        jmp add_to_pack
_pot    lda #1
        sta gv_why
        ldy #0
_pf     lda c_beltt,y
        beq _pp
        iny
        cpy #4
        bne _pf
        sec
        rts
_pp     txa
        sta c_beltt,y
        lda #0
        sta ap_b
        jmp _ok
_scr    lda ap_b                ; quantita'
        bne +
        lda #1
        sta ap_b
+       lda #2
        sta gv_why
        jsr scr_find
        bcs _new
        lda c_packb,y
        clc
        adc ap_b
        cmp #SCR_MAX+1
        bcs _no
        sta c_packb,y
        lda #0
        sta ap_b
        jmp _ok
_new    lda #0
        sta gv_why
        lda #I_SCROLL
        jsr add_to_pack
        bcs _no
_ok     lda #1
        sta hud_dirty
        clc
        rts
_no     sec
        rts

; Y = posto dello zaino con la pila di pergamene. C=1 se non c'e'
scr_find:
        ldy #0
_l      lda c_pack,y
        cmp #I_SCROLL
        beq _y
        iny
        cpy #PACK_N
        bne _l
        sec
        rts
_y      clc
        rts

; pergamena di portale (tasto 5)
use_scroll:
        lda cur_level
        beq _no
        jsr scr_find
        bcs _no
        jsr find_adj
        bcs _no
        jsr scr_find            ; una pergamena in meno (la pila vuota libera il posto dello zaino)
        lda c_packb,y
        sec
        sbc #1
        sta c_packb,y
        bne +
        sta c_pack,y
+       lda #1
        sta hud_dirty
        ; il portale precedente sparisce ovunque fosse
        lda c_portal
        beq _np
        lda c_retlvl
        cmp cur_level
        bne _np
        lda tx
        pha
        lda ty
        pha
        lda c_retx
        sta tx
        lda c_rety
        sta ty
        lda #T_FLOOR
        jsr set_tile
        pla
        sta ty
        pla
        sta tx
_np     lda cur_level
        sta c_retlvl
        lda tx
        sta c_retx
        lda ty
        sta c_rety
        lda #1
        sta c_portal
        lda #SFX_PORTAL
        jsr sfx_play
        lda #T_PORTAL
        jsr set_tile
        lda #1
        sta force_redraw
        sta hud_dirty
_no     rts

; tile libero adiacente al giocatore -> tx,ty ; C=1 se nessuno
find_adj:
        ldx #0
_t      stx gl_start
        lda ptx
        clc
        adc fa_dx,x
        sta tx
        lda pty
        clc
        adc fa_dy,x
        sta ty
        jsr get_tile
        cmp #T_FLOOR
        bcc _n
        cmp #T_FLOORC+1
        bcs _n
        clc
        rts
_n      ldx gl_start
        inx
        cpx #4
        bne _t
        sec
        rts
fa_dx   .byte 1, $ff, 0, 0
fa_dy   .byte 0, 0, 1, $ff

; il portale (unico) rimane nel livello c_retlvl alla posizione tile c_retx,c_rety
place_portal_tile:
        lda c_portal
        beq _r
        lda c_retlvl
        cmp cur_level
        bne _r
        lda c_retx
        sta tx
        lda c_rety
        sta ty
        lda #T_PORTAL
        jmp set_tile
_r      rts

; ===================================================================
;  oggetti a terra / bottino
; ===================================================================
; aggiorna mix/miy dei mostri vivi con la posizione attuale (per STASH: portale / morte)
sync_monsters:
        ldx #0
_l      cpx lb_cnt
        bcs _d
        stx rt_i
        lda malive,x
        beq _n
        jsr mon_tx
        ldx rt_i
        sta mix,x
        jsr mon_ty
        ldx rt_i
        sta miy,x
_n      ldx rt_i
        inx
        jmp _l
_d      rts


; ===================================================================
;  bauli e loot
; ===================================================================
dxs     .byte 1, $ff, 0, 0
dys     .byte 0, 0, 1, $ff

; ---- supporto database --------------------------------------------
; A = min, X = max -> A = min + rnd(0..max-min). Preserva X.
roll_mm:
        sta rm_min
        stx rm_max
        txa
        sec
        sbc rm_min
        clc
        adc #1
        beq _all                ; intervallo 0..255
        jsr rndrange
        clc
        adc rm_min
        ldx rm_max
        rts
_all    jsr rand
        ldx rm_max
        rts

; A = A + tmpv2 con saturazione a 255
add_sat:
        clc
        adc tmpv2
        bcc _r
        lda #255
_r      rts

; A * X -> A (saturato)
mul8:
        sta la_p
        lda #0
        cpx #0
        beq _r
_l      clc
        adc la_p
        bcs _cap
        dex
        bne _l
_r      rts
_cap    lda #255
        rts

; stat mostro: Y = indice tabella (tipo), X = offset campo -> A
; campi consecutivi min/max/lvl a mon_hp_min + X*... (vedi chiamanti)

; genera un oggetto di livello bottino gi_ll (1..MAXLL): A = id, ap_b = bonus.
; Categoria dai pesi loot_cum; pozione: colore secondo il piano (pot_t1/pot_t2); pergamena; altrimenti un
; oggetto della categoria: il migliore con livello oggetto <= L (lt_scan, L dal chestLevel: vedi sotto).
; Magia +N (armi, armature, scudi) fino a bon_tab[gi_ll]; anello: caratteristica 1 FOR, 2 DES, 3 COS.
gen_item:
        lda gi_ll               ; chestLevel -> livello oggetto obiettivo T = CL / CL_PF (0..31)
        lsr
        lsr
        lsr
        .cerror CL_PF != 8, "gen_item: CL_PF fisso a 8"
        sta gi_t
_cat    ldx gi_force            ; categoria imposta (bauli epici: 1..4) o dai pesi
        bne _fx
        lda #100
        jsr rndrange
        ldx #0
_c      cmp loot_cum,x
        bcc _got
        inx
        cpx #5
        bne _c
        beq _got                ; (sempre: X = 5, ultima categoria; NON .byte $2c: saltava anche il primo
_fx     dex                     ;  byte di stx gi_cat e la pergamena mandava il programma in BRK)
_got    stx gi_cat              ; categoria - 1
        lda #0
        sta ap_b
        cpx #CAT_POTION-1
        beq _pot
        cpx #CAT_SCROLL-1
        beq _scr
        lda gi_t                ; L = T x u^2 (u = rand / 256): quasi sempre sotto T, a volte vicino
        ldx gi_force
        bne _lt                 ; bauli epici: L = T
        jsr rand
        sta mw_l
        sta mw_k
        lda #0
        sta mw_h
        jsr mul16x8             ; mu1 = u^2 x 256
        lda gi_t
        sta mw_l
        lda mu1
        sta mw_k
        lda #0
        sta mw_h
        jsr mul16x8             ; mu1 = T x u^2, arrotondato
        lda mu0
        asl
        lda mu1
        adc #0
_lt     cmp #MAXLL+1
        bcc +
        lda #MAXLL
+       sta gi_l
        jsr lt_scan             ; A = oggetto migliore con ilvl <= L (0: nessuno -> altra categoria)
        beq _cat
        pha
        ldx gi_cat
        cpx #CAT_RING-1
        beq _ring
        lda cat_bonus+1,x
        beq _nb
        ldx gi_l
        lda bon_tab,x
        clc
        adc #1
        jsr rndrange
        sta ap_b
_nb     pla
        rts
_ring   lda #3
        jsr rndrange
        clc
        adc #1
        sta ap_b
        pla
        rts
_scr    lda #I_SCROLL
        rts
_pot    ldx cur_level
        cpx #MAXLEVEL+1
        bcc +
        ldx #MAXLEVEL
+       jsr rand
        cmp pot_t1,x
        bcc _pr
        cmp pot_t2,x
        bcc _py
        lda #I_POTV
        rts
_py     lda #I_POTY
        rts
_pr     lda #I_POTR
        rts

; candidati della categoria gi_cat+1 per il livello bottino gi_ll: tmp3 = quanti (tmp2 = $ff), oppure
; A = id del candidato numero tmp2 (0..)
; oggetto della categoria gi_cat con il livello oggetto piu' alto <= gi_l -> A (0 se nessuno). Y conservato.
lt_scan:
        lda #0
        sta tmp3                ; miglior id
        sta tmp2                ; suo ilvl
        ldy #1
_l      ldx itcat,y
        dex
        cpx gi_cat
        bne _n
        lda itilvl,y
        cmp gi_l
        beq +
        bcs _n                  ; livello oggetto > L
+       cmp tmp2
        bcc _n
        sta tmp2
        sty tmp3
_n      iny
        cpy #N_ITEMS
        bne _l
        lda tmp3
        rts

; oro automatico: A = quantita' (byte); add_gold16: A basso, X alto. Tetto GOLD_MAX addosso: l'eccedenza si perde
add_gold:
        ldx #0
; A/X = monete da aggiungere (16 bit; add_gold: A, X = 0): oro addosso al massimo GOLD_MAX, HUD da ridisegnare
add_gold16:
        clc
        adc c_gold
        sta c_gold
        txa
        adc c_gold+1
        sta c_gold+1
        bcs _cap
        lda c_gold              ; c_gold > GOLD_MAX ?
        cmp #<(GOLD_MAX+1)
        lda c_gold+1
        sbc #>(GOLD_MAX+1)
        bcc _o
_cap    lda #<GOLD_MAX
        sta c_gold
        lda #>GOLD_MAX
        sta c_gold+1
_o      lda #1
        sta hud_dirty
        rts

; tile (tx,ty) pavimento libero? C=0 si
floor_ok:
        jsr get_tile
        cmp #T_FLOOR
        bcc _n
        cmp #T_FLOORC+1
        bcs _n
        clc
        rts
_n      sec
        rts

; cerca una tile libera adiacente a (loot_x,loot_y) -> loot_x/loot_y. C=1 se nessuna
adj_floor:
        lda loot_x
        sta af_x
        lda loot_y
        sta af_y
        ldx #0
_d      stx tmp7
        lda af_x
        clc
        adc dxs,x
        sta tx
        lda af_y
        clc
        adc dys,x
        sta ty
        jsr floor_ok
        bcc _f
        ldx tmp7
        inx
        cpx #4
        bne _d
        sec
        rts
_f      lda tx
        sta loot_x
        lda ty
        sta loot_y
        clc
        rts

; A = tipo, (loot_x,loot_y) -> crea baule. X = slot. C=1 se pieno
chest_add:
        pha
        ldx #0
_f      lda ch_t,x
        beq _ok
        inx
        cpx #CH_MAX
        bne _f
        pla
        sec
        rts
_ok     pla
        sta ch_t,x
        stx ch_cur
        lda loot_x
        sta cx_x,x
        lda loot_y
        sta cx_y,x
        txa
        asl
        asl
        tay
        lda #0
        sta ch_i,y
        sta ch_i+1,y
        sta ch_i+2,y
        sta ch_i+3,y
        sta ch_b,y
        sta ch_b+1,y
        sta ch_b+2,y
        sta ch_b+3,y
        lda loot_x
        sta tx
        lda loot_y
        sta ty
        lda #T_CHEST            ; 10/11: un solo tile per tutti i bauli (il tipo sta in ch_t)
        jsr set_tile
        ldx ch_cur
        clc
        rts

; riempie il baule ch_cur con A oggetti di livello gi_ll; marca generato
chest_fill:
        sta ch_cnt
        lda ch_cur
        asl
        asl
        sta tmp6
        lda #0
        sta tmp5
_l      jsr gen_item
        pha
        lda tmp6
        clc
        adc tmp5
        tax
        pla
        sta ch_i,x
        lda ap_b
        sta ch_b,x
        lda #0
        sta ap_b
        inc tmp5
        lda tmp5
        cmp ch_cnt
        bne _l
        ldx ch_cur
        lda ch_t,x
        ora #$80
        sta ch_t,x
        rts

; bauli del piano (ch_t, cx_x, cx_y) sulla mappa: il tile T_CHEST nella casella di ognuno (il tipo resta in ch_t)
apply_chests:
        ldx #0
_l      lda ch_t,x
        beq _n
        lda #T_CHEST            ; 10/11: un solo tile per tutti i bauli (il tipo sta in ch_t)
        pha
        lda cx_x,x
        sta tx
        lda cx_y,x
        sta ty
        stx tmp7
        pla
        jsr set_tile
        ldx tmp7
_n      inx
        cpx #CH_MAX
        bne _l
        rts

; baule in una stanza casuale: A = tipo, cur = stanza
chest_in_room:
        sta tmp4
        ldx cur
        lda rw,x
        sec
        sbc #2
        jsr rndrange
        ldx cur
        clc
        adc rx,x
        adc #1
        sta loot_x
        lda rh,x
        sec
        sbc #2
        jsr rndrange
        ldx cur
        clc
        adc ry,x
        adc #1
        sta loot_y
        sta ty
        lda loot_x
        sta tx
        jsr floor_ok
        bcs _r
        lda tmp4
        jsr chest_add
        jsr ch_gen
        bcs _r
        lda tmp4
        cmp #2
        bne _r
        inc pc_k
_r      rts

; genera i bauli del piano (dopo spawn_monsters)
; al massimo CH_GEN_MAX bauli generati; prima quello d'oro (piu' raro), poi stanza per stanza
place_chests:
        ; baule d'oro: vicino al mostro piu' forte (piano >= 3)
        lda cur_level
        cmp #CH_G_MINLVL
        bcc _gd
        lda #0
        sta tmp3
        sta tmp2
        ldx #0
_m      cpx lb_cnt
        bcs _gm
        lda mtype,x
        cmp tmp3
        bcc _mn
        beq _mn
        sta tmp3
        stx tmp2
_mn     inx
        bne _m
_gm     lda tmp3
        cmp #3
        bcc _gd
        jsr rand
        cmp #CH_G_CHANCE
        bcs _gd
        ldx tmp2
        lda mix,x
        sta loot_x
        lda miy,x
        sta loot_y
        jsr adj_floor
        bcs _gd
        lda #3
        jsr chest_add
        jsr ch_gen              ; baule del piano (si salva se aperto)
_gd     lda #0
        sta pc_k
        ldx #0
_cell   stx cur
        lda vis,x
        cmp #1
        bne _skip
        cpx st_s
        beq _skip
        jsr gen_full
        bcs _done
        lda cur_level
        cmp #CH_N_MINLVL
        bcc _k
        jsr rand
        cmp #CH_N_ROOM
        bcs _k
        lda #1
        jsr chest_in_room
_k      jsr gen_full
        bcs _done
        lda cur_level
        cmp #CH_K_MINLVL
        bcc _skip
        lda pc_k
        cmp #CH_K_MAX
        bcs _skip
        jsr rand
        cmp #CH_K_ROOM
        bcs _skip
        lda #2
        jsr chest_in_room
_skip   ldx cur
        inx
        cpx #16
        bne _cell
_done   rts

; dopo chest_add (C=0, X = posto): marca il baule come generato con il piano (bit 4). Preserva C.
ch_gen:
        bcs _r
        lda ch_t,x
        ora #$10
        sta ch_t,x
        clc
_r      rts

; C=1 se i bauli generati hanno raggiunto CH_GEN_MAX
gen_full:
        ldx #CH_MAX-1
        ldy #0
_c      lda ch_t,x
        beq +
        iny
+       dex
        bpl _c
        cpy #CH_GEN_MAX
        ldx cur
        rts

; loot di un mostro morto in (loot_x,loot_y)
roll_loot:
        lda loot_x
        sta tx
        lda loot_y
        sta ty
        jsr get_tile
        cmp #T_FLOOR            ; il bottino cade solo su pavimento (niente scale/muri)
        bcc _no
        cmp #T_STAIRSD
        bcc _ok
_no     rts
_ok     lda km_i
        clc
        adc #1
        cmp lb_boss
        beq _boss
        jsr chest_room          ; C=0: c'e' posto per un altro baule
        jsr rand                ; chiave
        cmp #DROP_KEY
        bcs _g
        jsr give_key
_g      jsr rand                ; esito unico: solo oro / cassa (oro + oggetti) / niente
        cmp #DROP_T_GOLD
        bcc _gold
        ldx cr_full             ; bauli al completo: niente tiro della cassa
        bne _r
        cmp #DROP_T_CHEST
        bcc _chest
        rts
_gold   lda #DROP_GOLD_LVL      ; oro: direttamente nel PG (+ DROP_GOLD_LVL per piano)
        ldx dungeon_level
        jsr mul8
        sta tmpv2
        lda #DROP_GOLD_MIN
        ldx #DROP_GOLD_MAX
        jsr roll_mm
        jsr add_sat
        jmp add_gold
_chest  jsr mon_ll              ; cassa: all'apertura da' sempre oro + gli oggetti
        lda #DROP_IMIN
        ldx #DROP_IMAX
        jsr roll_mm
        tax
        lda #0
        sta dc_b
        lda #1
        jsr defer_drop          ; la cassa compare a fine combattimento
_r      rts
_boss
.if BOSS_KEY
        jsr give_key
.endif
        jsr mon_ll
        lda gi_ll
        sta tmpv2
        lda #BOSS_LL_ADD
        jsr add_sat
        sta gi_ll
        lda #1
        sta dc_b                ; boss: il baule si salva con il piano finche' non e' aperto
        ldx #BOSS_ITEMS
        jsr defer_drop
_r2     rts

; ---- drop dei bauli: differito a fine combattimento, un baule per frame ----------------
        .virtual $9240
bq_x    .fill 48                ; coda BFS
bq_y    .fill 48
bm_x    .fill 32                ; tile dei mostri vivi ($ff = nessuno)
bm_y    .fill 32
pd_x    .fill PD_MAX            ; drop in attesa
pd_y    .fill PD_MAX
pd_n    .fill PD_MAX
pd_ll   .fill PD_MAX
pd_f    .fill PD_MAX            ; 0 libero, 1 normale, 2 boss
pd_any  .byte ?
cr_full .byte ?                 ; 1 = niente piu' bauli dai mostri comuni (chest_room)
pd_i    .byte ?
dc_b    .byte ?
bq_h    .byte ?
bq_t    .byte ?
bf_x    .byte ?
bf_y    .byte ?
bf_d    .byte ?
bf_m    .byte ?
mon_cap .byte ?                 ; tetto di mostri comuni del piano
mon_min .byte ?                 ; minimo garantito
sm_n    .byte ?
sm_m    .byte ?
sm_r    .byte ?
sm_k    .byte ?
        .endv
PD_MAX  = 8
BQ_MAX  = 48

; C=0 (e cr_full = 0) se un mostro comune puo' ancora lasciare un baule: bauli nel piano + in coda
; < CH_MAX, tenendo un posto per il boss finche' e' vivo
chest_room:
        ldx #CH_MAX-1
        ldy #0
_c      lda ch_t,x
        beq +
        iny
+       dex
        bpl _c
        ldx #PD_MAX-1
_p      lda pd_f,x
        beq +
        iny
+       dex
        bpl _p
        lda lb_boss             ; boss vivo: un posto riservato al suo baule
        beq _n
        tax
        lda malive-1,x
        beq _n
        iny
_n      cpy #CH_MAX
        lda #0
        rol
        sta cr_full
        lsr
        rts

; A = tipo, X = n oggetti, gi_ll, loot_x/y, dc_b (1 = boss): mette in coda (o piazza subito se piena)
defer_drop:
        ldy #0
_f      lda pd_f,y
        beq _put
        iny
        cpy #PD_MAX
        bne _f
        lda #1
        jmp drop_now
_put    lda dc_b
        clc
        adc #1
        sta pd_f,y
        lda loot_x
        sta pd_x,y
        lda loot_y
        sta pd_y,y
        txa
        sta pd_n,y
        lda gi_ll
        sta pd_ll,y
        lda #1
        sta pd_any
        rts

drop_now:                       ; A = tipo, X = n oggetti, dc_b
        jsr drop_chest
        bcs _r
        lda dc_b
        beq _r
        ldx ch_cur              ; baule del boss: si salva con il piano finche' non e' aperto
        inx
        stx lb_bch
_r      rts

; chiamata ogni frame: a fine combattimento piazza un baule in coda
drops_tick:
        lda pd_any
        beq _r
        lda cmb_t
        bne _r
        jmp flush_one
_r      rts

; un baule in attesa (pd_f, lasciato da un mostro durante il combattimento) compare sulla mappa; pd_any = 0 se non ce ne sono piu'
flush_one:
        ldy #PD_MAX-1
_s      lda pd_f,y
        bne _g
        dey
        bpl _s
        lda #0
        sta pd_any
        rts
_g      sty pd_i
        sec
        sbc #1
        sta dc_b
        lda #0
        sta pd_f,y
        lda pd_x,y
        sta loot_x
        lda pd_y,y
        sta loot_y
        lda pd_ll,y
        sta gi_ll
        ldx pd_n,y
        lda #1
        jmp drop_now

flush_drops:                    ; tutti subito (prima di salvare/lasciare il piano)
        lda pd_any
        beq _r
        jsr flush_one
        jmp flush_drops
_r      rts

; prima casella libera (pavimento, niente baule/oggetto, mostri, PG) raggiungibile dal corpo
; (loot_x,loot_y) -> loot_x/loot_y. C=1 se nessuna
find_free:
        ldx #0
_bm     cpx lb_cnt
        bcs _bd
        lda #$ff
        sta bm_x,x
        lda malive,x
        beq _bn
        stx bf_m
        jsr mon_tx
        ldx bf_m
        sta bm_x,x
        jsr mon_ty
        ldx bf_m
        sta bm_y,x
_bn     inx
        bne _bm
_bd     lda loot_x
        sta bq_x
        lda loot_y
        sta bq_y
        lda #0
        sta bq_h
        lda #1
        sta bq_t
_pop    ldx bq_h
        cpx bq_t
        beq _none
        inc bq_h
        lda bq_x,x
        sta bf_x
        lda bq_y,x
        sta bf_y
        jsr bf_cand
        bcs _exp
        lda bf_x
        sta loot_x
        lda bf_y
        sta loot_y
        clc
        rts
_exp    ldx #0
_nb     stx bf_d
        lda bf_x
        clc
        adc dxs,x
        sta tx
        lda bf_y
        clc
        adc dys,x
        sta ty
        jsr bf_walk
        bcs _nx
        jsr bf_seen
        bcs _nx
        ldx bq_t
        cpx #BQ_MAX
        bcs _nx
        lda tx
        sta bq_x,x
        lda ty
        sta bq_y,x
        inc bq_t
_nx     ldx bf_d
        inx
        cpx #4
        bne _nb
        jmp _pop
_none   sec
        rts

bf_cand:                        ; (bf_x,bf_y) libera? C=0 si
        lda bf_x
        sta tx
        lda bf_y
        sta ty
        jsr floor_ok
        bcs _no
        lda bf_x
        cmp ptx
        bne _pm
        lda bf_y
        cmp pty
        beq _no
_pm     ldx #0
_l      cpx lb_cnt
        bcs _ok
        lda bm_x,x
        cmp bf_x
        bne _n
        lda bm_y,x
        cmp bf_y
        beq _no
_n      inx
        bne _l
_ok     clc
        rts
_no     sec
        rts

bf_walk:                        ; (tx,ty) percorribile (pavimento, scale, leva, bauli)? C=0 si
        jsr get_tile
        cmp #T_FLOOR
        bcc _n
        cmp #T_DHOME+1
        bcc _y
        cmp #T_CHEST
        bne _n
_y      clc
        rts
_n      sec
        rts

bf_seen:                        ; (tx,ty) gia' in coda? C=1 si
        ldx #0
_l      cpx bq_t
        bcs _no
        lda bq_x,x
        cmp tx
        bne _nx
        lda bq_y,x
        cmp ty
        beq _yes
_nx     inx
        bne _l
_no     clc
        rts
_yes    sec
        rts

; livello bottino del mostro km_i: piano + loot_level_bonus (max MAXLL)
; chestLevel del tesoro del mostro km_i -> gi_ll (byte 1..255, saturato): CL_PF x piano + loot_level_bonus
; del tipo x CL_LLB + CL_STRONG (variante forte) +/- CL_HP (vita massima del mostro oltre/sotto +-1/8 della
; vita media del tipo al piano). Il boss aggiunge BOSS_LL_ADD (roll_loot).
mon_ll:
        ldy km_i
        ldx mtype,y
        lda mon_llb,x
        asl
        asl                     ; (CL_LLB = 4)
        .cerror CL_LLB != 4, "mon_ll: CL_LLB fisso a 4"
        sta tmpv2
        lda dungeon_level
        ldx #CL_PF
        jsr mul8
        jsr add_sat
        sta tmpv2
        ldx mtype,y
        cpx #N_BASE+1
        bcc _hp
        cpx #T_FINAL
        bcs _hp
        lda #CL_STRONG
        jsr add_sat
        sta tmpv2
_hp     lda ft_hpl,x            ; soglie: vita media +/- 1/8
        sta tmp0
        lda ft_hph,x
        sta tmp1
        lsr tmp1
        ror tmp0
        lsr tmp1
        ror tmp0
        lsr tmp1
        ror tmp0                ; tmp0/1 = media / 8
        lda ft_hpl,x
        clc
        adc tmp0
        sta tmp2
        lda ft_hph,x
        adc tmp1
        sta tmp3                ; tmp2/3 = media + 1/8
        lda mhm,y
        cmp tmp2
        lda mhmh,y
        sbc tmp3
        bcc _lo
        lda #CL_HP              ; vita alta: +
        jsr add_sat
        sta tmpv2
        jmp _o
_lo     lda ft_hpl,x
        sec
        sbc tmp0
        sta tmp2
        lda ft_hph,x
        sbc tmp1
        sta tmp3                ; tmp2/3 = media - 1/8
        lda mhm,y
        cmp tmp2
        lda mhmh,y
        sbc tmp3
        bcs _o
        lda tmpv2               ; vita bassa: -
        sec
        sbc #CL_HP
        bcs +
        lda #1
+       sta tmpv2
_o      lda tmpv2
        bne +
        lda #1
+       sta gi_ll
        rts

; A = tipo, X = n oggetti, gi_ll = livello: baule accanto al corpo
drop_chest:
        sta dc_t
        stx dc_n
        jsr find_free           ; prima casella libera e raggiungibile (BFS dal corpo)
        bcc _p
        jsr adj_floor           ; ripiego: adiacente, altrimenti resta sul corpo
_p
        lda dc_t
        ora #8                  ; contenuto (oro + oggetti) generato alla prima apertura
        jsr chest_add
        bcs _r
        txa
        asl
        asl
        tay
        lda dc_n
        sta ch_i,y
        lda gi_ll
        sta ch_b,y
        clc
_r      rts

; una chiave in piu' (al massimo 10), con il suono della raccolta
give_key:
        lda c_keys
        cmp #10                 ; massimo 10 chiavi
        bcs _r
        inc c_keys
        lda #1
        sta hud_dirty
        lda #SFX_PICK
        jsr sfx_play
_r      rts


; ---- apertura baule alla posizione del giocatore
chest_open:
        jsr chest_here          ; (11/11) stessa ricerca della barra: X = baule sotto il PG, $FF se non c'e'
        txa
        bpl _found
        rts
_found  stx ch_cur
        lda #0
        sta ch_msg
        sta ch_gold
        sta ch_gold+1
        lda ch_t,x
        bmi _show
        and #8                  ; tesoro di un mostro: oro e oggetti ora, dal suo livello bottino
        bne _drop
        lda ch_t,x
        and #$40                ; baule epico: nessuna chiave
        bne _gen
        lda ch_t,x
        and #3
        tay
        lda ch_keyr-1,y
        beq _gen
        lda c_keys
        beq _locked
        dec c_keys
        lda #1
        sta hud_dirty
_gen    jsr chest_gen_seed
_show   ldx ch_cur              ; baule aperto: sparisce cambiando piano (rel.asm)
        inx
        cpx lb_bch
        bne +
        lda #0
        sta lb_bch
+       dex
        lda ch_t,x
        ora #$20
        sta ch_t,x
        jmp ui_chest
_locked lda #1
        sta ch_msg
        jmp ui_chest
_drop   txa
        asl
        asl
        tay
        lda ch_b,y
        sta gi_ll
        lda ch_i,y
        pha
        lda #0
        sta ch_i,y
        sta ch_b,y
        lda ch_t,x
        and #$f7
        sta ch_t,x
        jsr ch_goldroll
        pla
        jsr chest_fill
        jmp _show

; contenuto del baule determinato dal seed (piano + posizione)
chest_gen_seed:
        lda rnd
        pha
        lda rnd+1
        pha
        jsr seed_level
        ldx ch_cur
        lda rnd
        eor cx_x,x
        sta rnd
        lda rnd+1
        eor cx_y,x
        ora #1
        sta rnd+1
        jsr rand
        jsr rand
        jsr rand
        ldx ch_cur
        lda ch_t,x
        and #3
        sec
        sbc #1
        sta tmp4
        tax
        lda ch_llmin,x          ; livello bottino = piano + tiro (bias_low: il minore di due)
        pha
        lda ch_llmax,x
        tax
        pla
        jsr roll_mm
        sta tmp3
        ldx tmp4
        lda ch_bias,x
        beq _nb
        lda ch_llmin,x
        pha
        lda ch_llmax,x
        tax
        pla
        jsr roll_mm
        cmp tmp3
        bcs _nb
        sta tmp3
_nb     lda tmp3
        clc
        adc dungeon_level
        ldx #CL_PF              ; chestLevel = CL_PF x (piano + offset), saturato
        jsr mul8
        sta tmp3
        ldx ch_cur
        lda ch_t,x
        and #$40
        beq _norm
        lda #255                ; baule epico (sala del trono): chestLevel massimo, una sola categoria
        sta gi_ll               ; (posto 0..3 = armi, armature, scudi, anelli), FIN_GOLD monete, EPIC_ITEMS oggetti
        txa
        clc
        adc #1
        sta gi_force
        lda #<FIN_GOLD
        ldx #>FIN_GOLD
        jsr add_gold16
        lda #<FIN_GOLD
        sta ch_gold
        lda #>FIN_GOLD
        sta ch_gold+1
        lda #EPIC_ITEMS
        jsr chest_fill
        lda #0
        sta gi_force
        jmp _done
_norm   lda tmp3
        sta gi_ll
        jsr ch_goldroll
        ldx tmp4
        lda ch_imin,x
        pha
        lda ch_imax,x
        tax
        pla
        jsr roll_mm
        jsr chest_fill
_done   pla
        sta rnd+1
        pla
        sta rnd
        rts

; oro automatico all'apertura: T x CH_GOLD_LLMIN .. T x CH_GOLD_LLMAX (T = chestLevel / CL_PF, saturato a 255) -> ch_gold
ch_goldroll:
        lda gi_ll               ; T = chestLevel / CL_PF
        lsr
        lsr
        lsr
        sta tmp7
        ldx #CH_GOLD_LLMIN
        jsr mul8
        sta tmp2
        lda tmp7
        ldx #CH_GOLD_LLMAX
        jsr mul8
        tax
        lda tmp2
        jsr roll_mm
        sta ch_gold
        jsr add_gold
; (11/11) nell'Abisso (piano > MAXLEVEL) un gettone respec con probabilita' RESP_DROP / 256, preso come l'oro
resp_roll:
        lda cur_level
        cmp #MAXLEVEL+1
        bcc +
        jsr rand
        cmp #RESP_DROP
        bcs +
        jsr resp_add
        lda #2                  ; ui_chest: "respec token found!"
        sta ch_msg
+       rts

; ===================================================================
;  mostri
; ===================================================================
clear_lvlblk:
        lda #<LVLBLK
        sta ptr0
        lda #>LVLBLK
        sta ptr0+1
        lda #0
        ldx #3                  ; $9800-$9AFF: NON oltre (a $9B00 ci sono le variabili REL)
        jmp fill_pages
        .cerror LVLEND > LVLBLK + $300, "clear_lvlblk: LVLBLK oltre 3 pagine"

; un mostro nuovo nella stanza scelta da spawn_monsters (tipo a caso fino a maxtype_tab del piano; una variante
; forte per stanza se il piano lo permette); niente se il piano ha gia' mon_cap mostri
place_monster:
        lda lb_cnt
        cmp mon_cap
        bcc +
        rts
+       ldx cur_level
        lda maxtype_tab,x
        jsr rndrange
        clc
        adc #1
        ldx sp_strong
        beq _bt
        ldx #0
        stx sp_strong
        tax
        lda mt_fmin+N_BASE,x    ; variante forte (una per stanza) solo se il suo piano minimo <= piano + STRONG_EARLY
        sec
        sbc #STRONG_EARLY
        bcc _st
        cmp cur_level
        bcc _st
        beq _st
        txa                     ; troppo presto: resta il tipo base
        jmp _bt
_st     txa
        clc
        adc #N_BASE
_bt     ldy lb_cnt
        sta mtype,y
        lda #12                 ; max tentativi: una sola creatura per casella
        sta pm_try
_pos    ldx cur
        lda rw,x
        sec
        sbc #2
        jsr rndrange
        clc
        adc rx,x
        adc #1
        sta tmp0
        lda rh,x
        sec
        sbc #2
        jsr rndrange
        clc
        adc ry,x
        adc #1
        sta tmp1
        ldx #0                  ; casella gia' occupata da un altro mostro?
_oc     cpx lb_cnt
        bcs _free
        lda mix,x
        cmp tmp0
        bne _on
        lda miy,x
        cmp tmp1
        beq _taken
_on     inx
        bne _oc
_taken  dec pm_try
        bne _pos                ; ritenta; a tentativi finiti rinuncia (stanza piena)
        rts
_free   ldy lb_cnt
        lda tmp1
        sta miy,y
        lda tmp0
        sta mix,y
        lda #1
        sta malive,y
        inc lb_cnt
        rts

; popola il piano: fra mon_min e mon_cap mostri nelle stanze abitabili (vis = 1, non quella di partenza);
; il piano del boss di un capitolo ha solo il boss (place_boss)
spawn_monsters:
        lda #0
        sta lb_cnt
        lda lv_cboss            ; (12/11) piano del boss di un capitolo (segnaposto): solo il boss (place_boss)
        beq +
        rts
+
        ldx cur_level
        lda maxmon_tab,x
        sta mon_cap
        lda minmon_tab,x
        sta mon_min
        lda #0                  ; stanze abitabili
        sta sm_n
        ldx #15
_cn     lda vis,x
        cmp #1
        bne _cx
        cpx st_s
        beq _cx
        inc sm_n
_cx     dex
        bpl _cn
        lda mon_cap             ; max per stanza = ceil(tetto*5/4 / stanze), al massimo SPAWN_MAX
        lsr
        lsr
        clc
        adc mon_cap
        sta tmp0
        lda #0
        sta sm_m
        lda sm_n
        beq _nm
_dv     lda tmp0
        beq _dd
        inc sm_m
        sec
        sbc sm_n
        bcs _s2
        lda #0
_s2     sta tmp0
        jmp _dv
_dd     lda sm_m
        cmp #SPAWN_MAX+1
        bcc _nm
        lda #SPAWN_MAX
        sta sm_m
_nm     lda #16                 ; si parte da una stanza a caso: il tetto non penalizza sempre le stesse
        jsr rndrange
        sta sm_r
        lda #0
        sta sm_k
_cell   lda sm_k
        clc
        adc sm_r
        and #15
        tax
        stx cur
        lda vis,x
        cmp #1
        bne _skip
        cpx st_s
        beq _skip
        lda #SPAWN_MIN
        ldx sm_m
        jsr roll_mm
        sta sp_cnt
        cmp #0                  ; roll_mm termina con ldx: il flag Z non e' quello del tiro
        beq _skip
        lda #0
        sta sp_strong
        jsr rand
        ldx cur_level
        cmp strong_tab,x
        bcs _one
        inc sp_strong
_one    jsr place_monster
        dec sp_cnt
        bne _one
_skip   inc sm_k
        lda sm_k
        cmp #16
        beq _dn
        jmp _cell
_dn     lda #64                 ; minimo del piano: aggiunge mostri in stanze a caso
        sta sm_k
_fl     lda lb_cnt
        cmp mon_min
        bcs _fd
        dec sm_k
        beq _fd
        lda #16
        jsr rndrange
        tax
        lda vis,x
        cmp #1
        bne _fl
        cpx st_s
        beq _fl
        stx cur
        lda #0
        sta sp_strong
        jsr place_monster
        jmp _fl
_fd     lda cur_level
        cmp #MAXLEVEL
        bne _done
        ldy lb_cnt
        ldx st_e
        lda #T_FINAL
        sta mtype,y
        jmp mon_new             ; (15/11, D12: comune con place_boss)
_done   rts

; X = stanza logica, Y = indice del mostro appena creato: posizione = centro della stanza, vivo, lb_cnt + 1
mon_new:
        lda rcx,x
        sta mix,y
        lda rcy,x
        sta miy,y
        lda #1
        sta malive,y
        inc lb_cnt
        rts

; dati runtime dei mostri dopo spawn / caricamento (floor_types gia' chiamato per il piano)
init_monsters_rt:
        ldx #0
init_rt_from:                   ; X = primo mostro da inizializzare
_m      cpx lb_cnt
        bcc _go
        rts
_go     stx rt_i
        lda malive,x
        beq _next
        lda mix,x
        jsr tile_to_pix
        ldx rt_i
        lda tmp0
        sta mxl,x
        lda tmp1
        sta mxh,x
        lda miy,x
        jsr tile_to_pix
        ldx rt_i
        lda tmp0
        sta myl,x
        lda tmp1
        sta myh,x
        jsr mon_hp_init         ; vita (16 bit): media del tipo al piano +-25%, boss con nome x BOSS_HPH/2
        ldx rt_i
        lda #0
        sta mcd,x
        sta mstun,x
        sta macc,x
        sta mwake,x
_next   ldx rt_i
        inx
        jmp _m

; ---- boss finale: evocazioni quando la vita scende sotto 3/4, 1/2, 1/4 (2 mostri, max 4 evocati vivi)
EPIC_ITEMS = 3
; a ogni giro nella sala del trono: quando la vita del boss finale scende sotto la soglia dell'ondata (fb_th) evoca
; un'ondata di mostri, se i vivi sono pochi (final_summons in data/rules.yaml)
final_tick:
        lda cur_level
        cmp #MAXLEVEL
        beq _go
_q      rts
_go     ldx lb_boss
        beq _q
        dex
        lda malive,x
        beq _q
        lda fb_wave
        cmp #3
        bcs _q
        jsr fb_th               ; vita <= soglia dell'ondata corrente?
        bcc _q
        inc fb_wave
        ldy #0                  ; mostri vivi oltre al boss
        ldx #0
_c      cpx lb_cnt
        bcs _cd
        lda malive,x
        beq +
        iny
+       inx
        bne _c
_cd     cpy #SUM_MAXALIVE+1     ; (boss compreso)
        bcs _r
        lda #SUM_WAVE
        sta gf_n
        lda #5
        jsr rndrange
        sta gf_t                ; prima punta della stella
_s      ldy lb_cnt
        cpy #32
        bcs _r
        ldx #SUM_FLOOR          ; tipi comuni del piano SUM_FLOOR (statistiche del piano del boss)
        lda maxtype_tab,x
        jsr rndrange
        clc
        adc #1
        sta mtype,y
        lda gf_t
        asl
        tax
        lda fin_tip,x
        sta mix,y
        lda fin_tip+1,x
        sta miy,y
        lda #1
        sta malive,y
        lda #0
        sta mfar,y
        inc lb_cnt
        tya
        tax
        jsr init_rt_from
        ldx lb_cnt
        dex
        lda #1
        sta mwake,x
        lda gf_t                ; punta successiva (due oltre: mai vicine)
        clc
        adc #2
        cmp #5
        bcc +
        sbc #5
+       sta gf_t
        dec gf_n
        bne _s
_r      rts

; X = boss: C=1 se la vita e' sotto la soglia dell'ondata fb_wave (max x (3 - fb_wave) / 4). Preserva X.
fb_th:
        lda mhm,x               ; tmp0/tmp1 = max / 4
        sta tmp0
        lda mhmh,x
        lsr
        ror tmp0
        lsr
        ror tmp0
        sta tmp1
        lda #0
        sta tmp2
        sta tmp3
        lda #3
        sec
        sbc fb_wave
        tay
_t      dey
        bmi _e
        clc
        lda tmp2
        adc tmp0
        sta tmp2
        lda tmp3
        adc tmp1
        sta tmp3
        jmp _t
_e      lda tmp2                ; C = (soglia >= vita) e vita != soglia
        cmp mhp,x
        lda tmp3
        sbc mhph,x
        bcc _no
        lda tmp2
        cmp mhp,x
        bne _y
        lda tmp3
        cmp mhph,x
        beq _no
_y      sec
        rts
_no     clc
        rts

; all'ingresso nell'ultimo piano: le ondate gia' superate (vita del boss sotto la soglia) non si ripetono
final_init:
        lda #0
        sta fb_wave
        lda cur_level
        cmp #MAXLEVEL
        bne _r
        ldx lb_boss
        beq _r
        dex
_l      lda fb_wave
        cmp #3
        bcs _r
        jsr fb_th
        bcc _r
        inc fb_wave
        bne _l
_r      rts

; X = indice mostro. Preserva X.
kill_monster:
        stx km_i
        lda #0
        sta malive,x
        jsr mon_tx
        sta loot_x
        jsr mon_ty
        sta loot_y
                            ; nessun cadavere sul terreno (rimosso: creava confusione con i bauli)
_nc     ldx km_i                ; esperienza del tipo al piano (floor_types)
        ldy mtype,x
        lda ft_xpl,y
        sta tmp0
        lda ft_xph,y
        sta tmp1
        lda #0
        sta km_nl
        lda cur_level           ; livello del mostro: piano, +2 variante forte, +3 boss con nome
        sta tmp2
        cpy #N_BASE+1
        bcc +
        inc tmp2
        inc tmp2
+       jsr mon_named
        bcc _xn
        inc tmp2
        lda tmp0                ; boss con nome: esperienza x BOSS_XP_MUL
        sta mw_l
        lda tmp1
        sta mw_h
        lda #BOSS_XP_MUL
        jsr _xm
_xn     lda c_lvl               ; PG sopra il mostro di d livelli: 75 / 50 / 25 %, da 4 niente (ne' bottino)
        sec
        sbc tmp2
        bcc _xb
        beq _xb
        cmp #4
        bcc _xd
        lda #0
        sta tmp0
        sta tmp1
        inc km_nl
        bcs _xb
_xd     eor #$ff
        sec
        adc #4                  ; 4 - d
        ldx tmp0
        stx mw_l
        ldx tmp1
        stx mw_h
        jsr _xm
        lsr tmp1
        ror tmp0
        lsr tmp1
        ror tmp0
        jmp _xb
_xm     sta mw_k                ; tmp0/tmp1 = mw x A
        jsr mul16x8
        lda mu0
        sta tmp0
        lda mu1
        sta tmp1
        ldx km_i
        rts
_xb
.if ARENA
        jsr AR_KILL
.else
        jsr add_xp
.endif
        inc c_kills
        bne _k1
        inc c_kills+1
_k1     ldx km_i
        inx
        cpx bar_m
        bne _kb
        lda #0
        sta bar_t
        sta bar_m
_kb
.if ARENA == 0                  ; arena: niente vittoria, niente bottino
        ldx km_i
        lda mtype,x
        cmp #T_FINAL
        bne _nb
        lda #1
        sta c_won
        lda #CHAPTERS+1         ; (15/11, prototipo) l'ultimo boss apre la discesa nel cratere: la citta' dell'Abisso (TWN5)
        sta c_unl
        ldx #RESP_FINAL         ; (11/11) il boss finale regala gettoni respec
-       jsr resp_add
        dex
        bne -
        jsr fin_doors           ; si aprono le stanze dei tesori
_nb     lda lv_cboss            ; (12/11) boss del capitolo ucciso: il capitolo dopo si sblocca
        beq _nb2
        lda km_i
        clc
        adc #1
        cmp lb_boss
        bne _nb2
        jsr chap_won
_nb2    lda cur_level           ; ultimo piano: ne' il boss ne' i mostri evocati lasciano bottino
        cmp #MAXLEVEL
        beq _nl
        lda km_nl               ; mostro troppo debole: niente bottino
        bne _nl
        jsr roll_loot
_nl
.endif
        lda #SFX_DIE
        jsr sfx_play
        ldx km_i
        rts

; colpisce i mostri nell'area (ha_x,ha_y,ha_hw,ha_hh) con l'abilita' ha_kind
hit_area:
        ldx #0
_m      cpx lb_cnt
        bcc _a
        rts
_a      lda malive,x
        beq _n
        lda mxl,x
        sec
        sbc ha_x
        sta tmp0
        lda mxh,x
        sbc ha_x+1
        sta tmp1
        jsr sabs
        cmp ha_hw
        bcs _n
        lda myl,x
        sec
        sbc ha_y
        sta tmp0
        lda myh,x
        sbc ha_y+1
        sta tmp1
        jsr sabs
        cmp ha_hh
        bcs _n
        jsr hit_one             ; tiro per colpire e danno (combat.asm)
_n      inx
        jmp _m

; ------------------------------------------------------------------ IA
update_monsters:
        lda #0
        sta cur_m
        sta pz_used             ; (17/11) al massimo una ricerca di percorso (mon_path) per giro
        inc pz_age
        lda frame               ; scelta dei 4 piu' vicini: raccolta sui frame 0 e 1 di ogni 4
        and #3                  ; (i mostri svegli sono elaborati a frame alterni)
        sta sel_on
        bne _loop
        jsr sel_begin
_loop   ldx cur_m
        cpx lb_cnt
        bcc _a
        lda sel_on
        cmp #1
        bne _nc
        jmp sel_commit
_nc     rts
_a      lda malive,x
        bne _a2
        jmp _next
_a2     lda mfar,x              ; bit 7 = lontano (fuori schermo): riesame 1 frame su 16
        and #$c0                ; bit 6 = addormentato fuori dal raggio di risveglio: 1 frame su 8
        beq _act
        bmi _fr
        txa
        eor frame
        and #7
        beq _b
        jmp _next
_fr     txa
        eor frame
        and #15
        beq _b
        jmp _next
_act    lda mwake,x             ; svegli: elaborati a frame alterni (meta' dei mostri per frame)
        beq _b
        txa
        eor frame
        and #1
        beq _b
        jmp _next
_b      lda px              ; distanze con valore assoluto in linea (niente sabs: e' il ciclo piu' caldo)
        sec
        sbc mxl,x
        sta m_dxl
        lda px+1
        sbc mxh,x
        sta m_dxh
        beq _xp
        cmp #$ff
        bne _far
        lda m_dxl
        beq _far                ; -256
        eor #$ff
        clc
        adc #1
        jmp _xs
_xp     lda m_dxl
_xs     sta m_adx
        cmp #200
        bcs _far
        lda py
        sec
        sbc myl,x
        sta m_dyl
        lda py+1
        sbc myh,x
        sta m_dyh
        beq _yp
        cmp #$ff
        bne _far
        lda m_dyl
        beq _far
        eor #$ff
        clc
        adc #1
        jmp _ys
_yp     lda m_dyl
_ys     sta m_ady
        cmp #160
        bcc _near
_far    lda #$80
        sta mfar,x
        jmp _next
_near   lda mfar,x              ; vicino: resta solo l'attesa (bit 0-4)
        and #$1f
        sta mfar,x
        lda mstun,x             ; stordimento: -2 (elaborato a frame alterni)
        beq _ai
        sec
        sbc #2
        bcs _st
        lda #0
_st     sta mstun,x
        jmp _next
_ai     lda mwake,x
        bne _awake
        lda mtype,x
        cmp #T_FINAL
        bne _aw0
        lda m_adx               ; boss finale: si sveglia quando il PG entra nel cerchio del pentacolo
        cmp #FIN_R_PX
        bcs _nx1
        lda m_ady
        cmp #FIN_R_PX
        bcc _wk
        bcs _nx1
_aw0    lda m_adx
        cmp #112
        bcs _nx1
        lda m_ady
        cmp #96
        bcc _wk
_nx1    lda #$40                ; addormentato e fuori dal raggio di risveglio: riesame 1 frame su 8
        sta mfar,x
        jmp _next
_wk     lda #1
        sta mwake,x
        lda bar_t               ; risveglio (aggro): la barra lo mostra se non ce n'e' gia' una
        bne +
        jsr bar_target
+
_awake  lda mcd,x                ; ricarica dell'attacco: -2 (frame alterni)
        beq _c0
        sec
        sbc #2
        bcs _cs
        lda #0
_cs     sta mcd,x
_c0     lda sel_on
        cmp #2
        bcs _so
        jsr sel_offer           ; candidato fra i 4 piu' vicini (per la prossima scelta)
_so
        jsr sel_has             ; si muove solo se e' fra i 4 piu' vicini scelti
        bcs _mv                 ; (gia' a frame alterni: passi da 2 px)
        jmp _contact
_mv     lda mfar,x              ; bloccato di recente: aspetta prima di riprovare
        and #$1f
        beq _mv2
        dec mfar,x
        jmp _contact
_mv2    ldy mtype,x
        lda macc,x
        clc
        adc mon_spd,y
        clc
        adc mon_spd,y           ; due frame di velocita'
        sta macc,x
        lsr
        lsr
        lsr
        lsr                     ; pixel/2 = passi da 2 px
        sta m_steps
        lda macc,x
        and #15
        sta macc,x
        lda m_adx
        cmp #9
        bcs _go
        lda m_ady
        cmp #9
        bcc _contact
_go     lda m_steps
        beq _contact
_step   jsr mon_step
        lda mxl,x               ; nessun movimento riuscito: bloccato, aspetta 16 frame
        cmp mo_xl               ; (8 frame di movimento: il mostro si muove a frame alterni)
        bne _mok
        lda myl,x
        cmp mo_yl
        bne _mok
        lda pz_wt               ; (17/11) ricerca di percorso in corso: riprova al prossimo turno
        bne +
        lda #STUCK_WAIT
+       sta mfar,x
        jmp _contact
_mok    dec m_steps
        bne _step
_contact lda m_adx              ; i mostri non entrano nella casella del PG: si fermano
        cmp #20                 ; sulla casella adiacente, da cui colpiscono
        bcs _next
        lda m_ady
        cmp #20
        bcs _next
        lda #CMB_DROP           ; mostro a contatto: combattimento in corso (bauli in coda: drops_tick)
        sta cmb_t               ; (17/11) il tema di combattimento non dipende piu' dai contatti: solo dal boss sullo schermo
        lda mcd,x
        bne _next
        lda #MON_ATK_T
        sta mcd,x
        jsr mon_attack          ; tiro per colpire e danno (combat.asm)
_next   inc cur_m
        jmp _loop

STUCK_WAIT = 8                  ; turni di movimento (= 16 frame) di attesa per un mostro bloccato

        .virtual $9abf          ; (azzerate con LVLBLK da clear_lvlblk e da load_location)
mslide  .fill 32                ; (17/11) percorso (mon_path): bit 0-1 = mossa 5, bit 3 = esplora, bit 4-6 = mosse rimaste (0 = insegue), bit 7 = casella nuova
mslc    .fill 32                ; mosse 1-4 del percorso (2 bit ciascuna, la corrente nei bit bassi)
md_d    .byte ?                 ; direzione del passo (mon_try_d)
mslide_end
        .endv
        .cerror LVLEND > mslide || mslide_end > $9b00, "mslide/mslc fuori da LVLEND..$9AFF"

; ---- i 4 mostri piu' vicini che si muovono (scelta con un frame di ritardo)
SEL_N = 4
; inizio della scelta dei SEL_N mostri piu' vicini di questo giro (sel_nx vuota)
sel_begin:
        ldy #SEL_N-1
        lda #$ff
_c      sta sel_nx,y
        sta sel_d,y
        dey
        bpl _c
        rts

; fine del giro: la scelta diventa quella valida per il giro dopo (sel_cu, letta da sel_has)
sel_commit:
        ldy #SEL_N-1
_c      lda sel_nx,y
        sta sel_cu,y
        dey
        bpl _c
        rts

; X = mostro: C=1 se scelto al frame precedente. Preserva X.
sel_has:
        txa
        ldy #SEL_N-1
_c      cmp sel_cu,y
        beq _y
        dey
        bpl _c
        clc
        rts
_y      sec
        rts

; X = mostro sveglio, distanza = max(m_adx, m_ady): sostituisce il piu' lontano dei 4 se piu' vicino. Preserva X.
sel_offer:
        lda m_adx
        cmp m_ady
        bcs _m
        lda m_ady
_m      sta sel_v
        ldy #0                  ; trova lo slot con distanza massima
        sty sel_k
        lda sel_d
        sta sel_w
        ldy #1
_f      lda sel_d,y
        cmp sel_w
        bcc _n
        sta sel_w
        sty sel_k
_n      iny
        cpy #SEL_N
        bne _f
        lda sel_v
        cmp sel_w
        bcs _r
        ldy sel_k
        sta sel_d,y
        txa
        sta sel_nx,y
_r      rts

; X = mostro sveglio: un passo verso il PG (o lungo il percorso trovato da mon_path); occ_check evita gli altri mostri.
; ent_x/ent_y = posizione nuova (mon_put la scrive), mo_* = quella di partenza (mon_undo)
mon_step:
        lda mxl,x
        sta ent_x
        sta mo_xl
        lda mxh,x
        sta ent_x+1
        sta mo_xh
        lda myl,x
        sta ent_y
        sta mo_yl
        lda myh,x
        sta ent_y+1
        sta mo_yh
        stx occ_self
        jsr ent_tile            ; casella di partenza
        lda nt_x
        sta ot_x
        lda nt_y
        sta ot_y
        lda mslide,x            ; (17/11) percorso in corso (mon_path): lo segue
        and #$70
        beq _gx
        jmp mon_follow
_gx     lda mslide,x            ; percorso finito senza aver visto il PG (bit 3, "esplora"): subito un'altra ricerca
        and #8
        beq _greedy
        jmp _path
_greedy lda m_adx
        cmp m_ady
        bcc _ypref
        lda m_adx
        cmp #2
        bcc _try_y
        jsr mon_try_x
        bcc _store
_try_y  lda m_ady
        cmp #2
        bcc _store
        jsr mon_try_y
        jmp _store
_ypref  lda m_ady
        cmp #2
        bcc _try_x
        jsr mon_try_y
        bcc _store
_try_x  lda m_adx
        cmp #2
        bcc _store
        jsr mon_try_x
_store  jsr no_progress         ; (17/11) nessun avvicinamento al PG (muro, o solo lo scivolamento di 1 px di uno spigolo,
        bcc mon_put             ; che faceva oscillare il mostro negli angoli): percorso breve con una ricerca sulle caselle
        jsr mon_undo
_path   jsr mon_path
        lda mslide,x
        and #$70
        beq mon_put             ; nessun percorso (o ricerca gia' fatta in questo giro): fermo, il chiamante aspetta
        jmp mon_follow
; X = mostro: la posizione ent_x/ent_y diventa la sua (mxl/mxh, myl/myh)
mon_put lda ent_x
        sta mxl,x
        lda ent_x+1
        sta mxh,x
        lda ent_y
        sta myl,x
        lda ent_y+1
        sta myh,x
        rts

; (no_progress: in monpath.asm, blocco CODE2)

; ---- (17/11) percorso breve dei mostri bloccati. Ricerca in ampiezza (BFS) sulle caselle in una finestra 13x13 attorno al
; mostro (BF_R = 6): fino alla casella del PG, o alla casella della finestra piu' vicina a lui. Del percorso trovato restano
; le prime 5 mosse (2 bit ciascuna, la prima nei bit bassi): mslc = mosse 1-4, mslide bit 0-1 = mossa 5, bit 3 = "esplora"
; (PG non raggiunto nella finestra: a fine percorso un'altra ricerca invece dell'inseguimento; in una sacca senza caselle piu'
; vicine al PG il percorso va alla casella del bordo della finestra piu' vicina a lui), bit 4-6 = numero di mosse rimaste,
; bit 7 = casella nuova gia' raggiunta (mon_follow). Al massimo una ricerca per giro (pz_used): costa fino
; a ~2 frame con la finestra piena, di solito molto meno (si ferma appena trova il PG). Al posto dello scorrimento lungo i
; muri del 06/11 (che restava negli angoli): docs/wiki/mostri.md.
BF_R  = 6
BF_W  = 2*BF_R+1                ; 13
BF_N  = BF_W*BF_W               ; 169 caselle
BF_C  = BF_R*BF_W+BF_R          ; casella centrale (il mostro)
BF_QN = 32                      ; coda circolare (la frontiera di una finestra 13x13 non supera ~26 caselle)
BFP   = $a500                   ; direzione dal genitore per casella: $ff = non vista, $fd = muro, $fe = partenza
BFQ   = BFP+BF_N                ; coda
BF_END = BFQ+BF_QN+26           ; fine delle variabili (26 B, vedi .virtual sotto)
;@map BFP..BF_END "Ricerca di percorso dei mostri bloccati (mon_path): direzioni, coda e variabili; nel villaggio (senza mostri) le tabelle degli NPC (quest.asm)"
        .virtual BFQ+BF_QN
pz_wx   .byte ?                 ; origine della finestra sulla mappa (con segno: fuori mappa = muro)
pz_wy   .byte ?
pz_hx   .byte ?                 ; PG nelle coordinate della finestra (con segno)
pz_hy   .byte ?
pz_qh   .byte ?
pz_qt   .byte ?
pz_c    .byte ?                 ; casella corrente
pz_cx   .byte ?
pz_cy   .byte ?
pz_n    .byte ?
pz_d    .byte ?
pz_best .byte ?
pz_bd   .byte ?
pz_rl   .byte ?                 ; registro delle mosse (12 bit)
pz_rh   .byte ?
pz_used .byte ?
mf_d    .byte ?                 ; mossa corrente (mon_follow: mon_try_d riscrive md_d)
pz_bb   .byte ?                 ; casella del bordo della finestra piu' vicina al PG, e la sua distanza
pz_bbd  .byte ?
pz_ex   .byte ?                 ; 8 = percorso "esplora" (PG non raggiunto)
pz_cnt  .byte ?                 ; caselle che si possono ancora esaminare in questo giro
pz_tot  .byte ?                 ; ... in tutta la ricerca
pz_run  .byte ?                 ; 1 = ricerca in corso (stato in BFP/BFQ/pz_*) per il mostro pz_own
pz_own  .byte ?
pz_age  .byte ?                 ; giri dall'ultima ripresa della ricerca (update_monsters)
pz_wt   .byte ?                 ; 1 = ricerca in corso per questo mostro: aspetta un turno solo (non STUCK_WAIT)
        .endv
PZ_MAXC = 120
PZ_STEP = 14
        .cerror BFQ+BF_QN+26 > $a600, "mon_path: tabelle oltre $a600"

; X = mostro bloccato: ricerca del percorso (descrizione completa sopra); al massimo una ricerca per giro (pz_used)
mon_path:
        lda #0
        sta pz_wt
        lda pz_used
        beq +
        rts                     ; (ricerca gia' fatta in questo giro: lo stato del mostro resta com'e')
+       inc pz_used
        lda #0
        sta mslide,x
        sta mslc,x
        stx occ_x
        lda pz_run              ; (17/11, PERF-21) ricerca a rate: PZ_STEP caselle per giro, PZ_MAXC in tutto
        beq _new
        cpx pz_own
        beq _cont               ; la ricerca di questo mostro continua
        lda pz_age
        cmp #8
        bcs _new                ; quella di un altro e' ferma da 8 giri (mostro morto, sbloccato): la si riprende per questo
        rts                     ; un altro mostro sta cercando: questo aspetta
_new    stx pz_own
        lda #1
        sta pz_run
        lda #PZ_MAXC
        sta pz_tot
        lda #$ff
        sta pz_bbd              ; migliore casella del bordo della finestra (per uscire da una sacca)
        ldy #BF_N-1
        lda #$ff
-       sta BFP,y
        dey
        cpy #$ff
        bne -
        lda ot_x
        sec
        sbc #BF_R
        sta pz_wx
        lda ot_y
        sec
        sbc #BF_R
        sta pz_wy
        lda ptx
        sec
        sbc pz_wx
        sta pz_hx
        lda pty
        sec
        sbc pz_wy
        sta pz_hy
        lda #$fe
        sta BFP+BF_C
        lda #BF_C
        sta BFQ
        sta pz_best
        lda #BF_R
        sta pz_cx
        sta pz_cy
        jsr pz_h
        sta pz_bd
        lda #0
        sta pz_qh
        lda #1
        sta pz_qt
_cont   lda #0
        sta pz_age
        lda #PZ_STEP            ; caselle esaminate in questo giro (meno di un frame)
        sta pz_cnt
_loop   lda pz_bd
        bne +                  ; PG raggiunto
        jmp _done
+
        ldy pz_qh
        cpy pz_qt
        bne +                  ; finestra esplorata
        jmp _done
+
        dec pz_tot              ; tetto della ricerca: si usa il migliore trovato finora
        bne +
        jmp _done
+       dec pz_cnt              ; fine del giro: si riprende al prossimo (il mostro aspetta un turno solo)
        bne +
        lda #1
        sta pz_wt
        ldx occ_x
        rts
+       lda BFQ,y
        sta pz_c
        iny
        tya
        and #BF_QN-1
        sta pz_qh
        lda pz_c                ; colonna e riga: c = 13 * riga + colonna
        ldy #0
-       cmp #BF_W
        bcc +
        sbc #BF_W
        iny
        bne -
+       sta pz_cx
        sty pz_cy
        lda #0
        sta pz_d
_dir    ldy pz_d
        lda pz_cx
        clc
        adc pz_ddx,y
        cmp #BF_W
        bcc +                  ; fuori dalla finestra (anche -1 = $ff)
        jmp _nd
+
        sta tx
        lda pz_cy
        clc
        adc pz_ddy,y
        cmp #BF_W
        bcc +                  
        jmp _nd
+
        sta ty
        lda pz_c
        clc
        adc pz_dc,y
        sta pz_n
        tay
        lda BFP,y
        cmp #$ff
        beq +                  ; gia' vista (o muro)
        jmp _nd
+
        lda tx                  ; muro? (casella sulla mappa; fuori mappa = muro)
        pha
        clc
        adc pz_wx
        sta tx
        cmp #MAPW
        bcc +                  
        jmp _wall
+
        lda ty
        pha
        clc
        adc pz_wy
        sta ty
        cmp #MAPH
        bcs _wall2
        jsr get_tile
        tay
        lda solidtab,y
        lsr
        bcs _wall2
        pla
        sta ty
        pla
        sta tx
        ldy pz_n
        lda pz_d
        sta BFP,y
        tya
        ldy pz_qt
        sta BFQ,y
        iny
        tya
        and #BF_QN-1
        sta pz_qt
        lda pz_cx               ; distanza di Manhattan dal PG della casella nuova
        pha
        lda pz_cy
        pha
        lda tx
        sta pz_cx
        lda ty
        sta pz_cy
        jsr pz_h
        tay
        pla
        sta pz_cy
        pla
        sta pz_cx
        lda tx                  ; casella sul bordo della finestra: candidata per uscire da una sacca
        beq _bb
        cmp #BF_W-1
        beq _bb
        lda ty
        beq _bb
        cmp #BF_W-1
        bne _bn
_bb     cpy pz_bbd
        bcs _bn
        sty pz_bbd
        lda pz_n
        sta pz_bb
_bn     cpy pz_bd
        bcs _nd
        sty pz_bd
        lda pz_n
        sta pz_best
        jmp _nd
_wall2  pla
_wall   pla
        ldy pz_n
        lda #$fd
        sta BFP,y
_nd     inc pz_d
        lda pz_d
        cmp #4
        bcs +                  
        jmp _dir
+
        jmp _loop
_done   lda #0                  ; PG non raggiunto: percorso "esplora" (bit 3), e in una sacca (nessuna casella piu' vicina al PG
        sta pz_run              ; della partenza) la casella del bordo della finestra piu' vicina al PG
        sta pz_ex
        lda pz_bd
        beq _bk
        lda #8
        sta pz_ex
        lda pz_best
        cmp #BF_C
        bne _bk
        lda pz_bbd
        cmp #$ff
        beq _bk
        lda pz_bb
        sta pz_best
_bk     lda #0                  ; dal migliore indietro fino al mostro: le mosse piu' vicine al mostro restano nei bit bassi
        sta pz_rl
        sta pz_rh
        sta pz_n                ; numero di mosse (massimo 5)
        ldy pz_best
_back   lda BFP,y
        cmp #4
        bcs _end                ; partenza
        sta pz_d
        asl pz_rl               ; registro = registro * 4 + d (10 bit)
        rol pz_rh
        asl pz_rl
        rol pz_rh
        ora pz_rl
        sta pz_rl
        lda pz_rh
        and #$03
        sta pz_rh
        lda pz_n
        cmp #5
        bcs +
        inc pz_n
+       tya                     ; casella del genitore = casella - passo della direzione
        ldy pz_d
        sec
        sbc pz_dc,y
        tay
        jmp _back
_end    ldx occ_x
        lda pz_n
        beq _r
        asl
        asl
        asl
        asl
        ora pz_rh
        ora pz_ex
        sta mslide,x
        lda pz_rl
        sta mslc,x
_r      rts

; (pz_h, pz_ddx/pz_ddy/pz_dc, mon_follow: in monpath.asm, nel secondo blocco di codice CODE2)


; A = direzione (0 +x, 1 -x, 2 +y, 3 -y): passo di 2 px (o 1) con controllo occupazione. C=1 bloccato
mon_try_d:
        sta md_d
        tay
        lda md_s2,y
        jsr _one
        bcc _ok
        ldy md_d
        lda md_s1,y
        jsr _one
        bcs _r
_ok     jsr occ_check
        bcc _r
        jmp mon_undo
_r      rts
_one    ldy md_d
        cpy #2
        bcs +
        jmp try_step_x
+       jmp try_step_y
md_s2   .byte 2, $fe, 2, $fe
md_s1   .byte 1, $ff, 1, $ff

; passo del mostro con controllo occupazione: se la casella di arrivo e' di un altro
; essere, il passo viene annullato (C=1 come "bloccato")
mon_try_x:
        jsr step_x_toward
        bcs _r
        jsr occ_check
        bcc _r
        jmp mon_undo
_r      rts

; X = mostro: passo verticale verso il PG; C=1 (e posizione di prima) se c'e' un muro o un altro mostro
mon_try_y:
        jsr step_y_toward
        bcs _r
        jsr occ_check
        bcc _r
        jmp mon_undo
_r      rts

; torna alla posizione di partenza del passo (mo_*); C=1 = passo non fatto
mon_undo:
        lda mo_xl
        sta ent_x
        lda mo_xh
        sta ent_x+1
        lda mo_yl
        sta ent_y
        lda mo_yh
        sta ent_y+1
        sec
        rts

; ent_x/ent_y -> casella (nt_x, nt_y)
ent_tile:
        lda ent_x
        lsr
        lsr
        lsr
        lsr
        sta nt_x
        lda ent_x+1
        asl
        asl
        asl
        asl
        ora nt_x
        sta nt_x
        lda ent_y
        lsr
        lsr
        lsr
        lsr
        sta nt_y
        lda ent_y+1
        asl
        asl
        asl
        asl
        ora nt_y
        sta nt_y
        rts

; ---- separazione in pixel: un essere non si avvicina a un altro sotto SEPX x SEPY
; (confronta il PG e i 4 mostri che si muovono). Un passo e' bloccato solo se entra nel
; riquadro E avvicina i due: chi e' gia' sovrapposto puo' sempre allontanarsi.
SEPX = 18                       ; < 20 = portata dell'attacco dei mostri
SEPY = 18
sep_check:                      ; ent_x/ent_y = posizione proposta, occ_self = chi si muove. C=1 bloccato
        lda occ_self
        cmp #$ff
        beq _pl
        tax                     ; mostro: vecchia posizione, bersaglio = PG
        lda mxl,x
        sta sp_ox
        lda mxh,x
        sta sp_ox+1
        lda myl,x
        sta sp_oy
        lda myh,x
        sta sp_oy+1
        lda px
        sta sp_tx
        lda px+1
        sta sp_tx+1
        lda py
        sta sp_ty
        lda py+1
        sta sp_ty+1
        jsr sep_one
        bcs _r
        jmp _ml
_pl     lda px                  ; PG: vecchia posizione
        sta sp_ox
        lda px+1
        sta sp_ox+1
        lda py
        sta sp_oy
        lda py+1
        sta sp_oy+1
_ml     ldy #3
_l      lda sel_cu,y
        cmp occ_self
        beq _n
        cmp #32
        bcs _n
        tax
        lda malive,x
        beq _n
        lda mxl,x
        sta sp_tx
        lda mxh,x
        sta sp_tx+1
        lda myl,x
        sta sp_ty
        lda myh,x
        sta sp_ty+1
        sty sp_i
        jsr sep_one
        ldy sp_i
        bcs _r
_n      dey
        bpl _l
        clc
_r      rts

; C=1 se la posizione proposta e' dentro SEPX x SEPY dal bersaglio e piu' vicina della vecchia
sep_one:
        lda ent_x
        sec
        sbc sp_tx
        sta sp_a
        lda ent_x+1
        sbc sp_tx+1
        jsr dist8
        cmp #SEPX
        bcs _no
        sta sp_n
        lda ent_y
        sec
        sbc sp_ty
        sta sp_a
        lda ent_y+1
        sbc sp_ty+1
        jsr dist8
        cmp #SEPY
        bcs _no
        clc
        adc sp_n
        sta sp_n                ; distanza nuova (dx+dy)
        lda sp_ox
        sec
        sbc sp_tx
        sta sp_a
        lda sp_ox+1
        sbc sp_tx+1
        jsr dist8
        sta sp_d
        lda sp_oy
        sec
        sbc sp_ty
        sta sp_a
        lda sp_oy+1
        sbc sp_ty+1
        jsr dist8
        clc
        adc sp_d
        bcs _no                 ; vecchia distanza > 255: si sta avvicinando da lontano, ok
        cmp sp_n
        beq _no
        bcc _no                 ; la nuova non e' minore: si allontana o resta, ok
        sec
        rts
_no     clc
        rts

; A = byte alto, sp_a = byte basso di una differenza con segno -> A = |valore| (max 255)
dist8:  cmp #0
        beq _p
        cmp #$ff
        bne _c
        lda sp_a
        beq _c
        eor #$ff
        clc
        adc #1
        rts
_p      lda sp_a
        rts
_c      lda #255
        rts

; ent_x/ent_y = posizione proposta, (ot_x,ot_y) = casella attuale, occ_self = mostro da
; ignorare ($ff = giocatore). C=1 se la casella di arrivo e' diversa e occupata da un altro
; essere (giocatore o mostro vivo). Preserva X, Y.
occ_check:
        stx occ_x
        tya
        pha
        jsr sep_check           ; distanza minima in pixel fra gli esseri (oltre alla casella)
        bcs _blk
        jsr ent_tile
        lda nt_x
        cmp ot_x
        bne _chg
        lda nt_y
        cmp ot_y
        bne _chg
        jmp _free               ; stessa casella: nessun vincolo
_chg    lda occ_self
        cmp #$ff
        beq _mons               ; il giocatore non si confronta con se stesso
        lda nt_x
        cmp ptx
        bne _mons
        lda nt_y
        cmp pty
        beq _blk
_mons   ldx #0
_l      cpx lb_cnt
        bcs _free
        cpx occ_self
        beq _n
        lda malive,x
        beq _n
        lda mxl,x
        lsr
        lsr
        lsr
        lsr
        sta tmp7
        lda mxh,x
        asl
        asl
        asl
        asl
        ora tmp7
        cmp nt_x
        bne _n
        lda myl,x
        lsr
        lsr
        lsr
        lsr
        sta tmp7
        lda myh,x
        asl
        asl
        asl
        asl
        ora tmp7
        cmp nt_y
        beq _blk
_n      inx
        jmp _l
_free   pla
        tay
        ldx occ_x
        clc
        rts
_blk    pla
        tay
        ldx occ_x
        sec
        rts

; passi da 2 px (i mostri si muovono a frame alterni); se 2 px sono bloccati prova 1 px
step_x_toward:
        lda m_dxh
        bmi _l
        lda #2
        jsr try_step_x
        bcc _r
        lda #1
        jmp try_step_x
_l      lda #$fe
        jsr try_step_x
        bcc _r
        lda #$ff
        jmp try_step_x
_r      rts

; passo verticale di 2 px verso il PG (m_dyh = segno), poi di 1 px se il primo urta; C=1 se bloccato
step_y_toward:
        lda m_dyh
        bmi _l
        lda #2
        jsr try_step_y
        bcc _r
        lda #1
        jmp try_step_y
_l      lda #$fe
        jsr try_step_y
        bcc _r
        lda #$ff
        jmp try_step_y
_r      rts

; ===================================================================
;  giocatore: attacco, abilita', tasti
; ===================================================================
update_attack:
        jsr tick_timers         ; ricariche, Rage, Frenzy, pozioni (combat.asm)
        lda gcd
        beq _g
        dec gcd
_g      lda joy
        and #$10
        beq _no
        lda gcd
        bne _no
        ldx c_skill
        lda sk_cdl,x
        ora sk_cdh,x
        bne _no
        jmp perform_skill
_no     rts

; centro d'attacco: 16 px davanti al giocatore
front_center:
        lda px
        sta ha_x
        lda px+1
        sta ha_x+1
        lda py
        sta ha_y
        lda py+1
        sta ha_y+1
        lda pdir
        beq _dn
        cmp #1
        beq _up
        cmp #2
        beq _lf
        lda ha_x
        clc
        adc #16
        sta ha_x
        bcc _r
        inc ha_x+1
_r      rts
_dn     lda ha_y
        clc
        adc #16
        sta ha_y
        bcc _r2
        inc ha_y+1
_r2     rts
_up     lda ha_y
        sec
        sbc #16
        sta ha_y
        bcs _r3
        dec ha_y+1
_r3     rts
_lf     lda ha_x
        sec
        sbc #16
        sta ha_x
        bcs _r4
        dec ha_x+1
_r4     rts

; area del colpo (ha_*) ed effetto (fx_*) centrati sul PG: Whirlwind, Battle Cry, Smash
centre_on_player:
        lda px
        sta ha_x
        sta fx_x
        lda px+1
        sta ha_x+1
        sta fx_x+1
        lda py
        sta ha_y
        sta fx_y
        lda py+1
        sta ha_y+1
        sta fx_y+1
        rts

; X = abilita' (0..3): un attacco, due con Frenzy (Battle Cry sempre uno)
perform_skill:
        stx cur_sk
        lda #1
        cpx #2
        beq _ps
        ldy tmr+T_FZ
        bne _f2
        ldy tmr+T_FZ+1
        beq _ps
_f2     lda #2
_ps     sta ps_n
_pl     ldx cur_sk
        jsr perform_skill1
        dec ps_n
        bne _pl
        rts

; X = abilita' (0..3): un'esecuzione. Ricarica (lo Slash: la cadenza s_rate), ricarica comune GCD_T, suono,
; area del colpo e effetto secondo l'abilita', poi hit_area
perform_skill1:
        stx cur_sk
        stx ha_kind
        lda sk_cd_lo,x          ; ricarica: dalla tabella, lo Slash dalla cadenza dell'arma
        bne _cd
        lda sk_cd_hi,x
        bne _cd
        lda s_rate
_cd     sta sk_cdl,x
        lda sk_cd_hi,x
        sta sk_cdh,x
        lda #GCD_T
        sta gcd
        lda #SFX_SWING
        jsr sfx_play
        ldx cur_sk
        beq _slash
        cpx #1
        beq _whirl
        cpx #2
        beq _cry
        ; Smash
        jsr centre_on_player
        lda #44
        sta ha_hw
        sta ha_hh
        lda #6
        sta fx_kind
        lda #10
        sta fx_timer
        jmp hit_area
_slash  jsr front_center
        lda ha_x
        sta fx_x
        lda ha_x+1
        sta fx_x+1
        lda ha_y
        sta fx_y
        lda ha_y+1
        sta fx_y+1
        lda pdir
        clc
        adc #1
        sta fx_kind
        lda #6
        sta fx_timer
        lda #15
        sta ha_hw
        sta ha_hh
        jmp hit_area
_whirl  jsr centre_on_player
        lda #26
        sta ha_hw
        sta ha_hh
        lda #5
        sta fx_kind
        lda #8
        sta fx_timer
        jmp hit_area
_cry    jsr centre_on_player
        lda #80
        sta ha_hw
        lda #64
        sta ha_hh
        lda #6
        sta fx_kind
        lda #14
        sta fx_timer
        jmp hit_area

; X = abilita' (0..3): diventa quella del Fire se il livello basta (sk_req); il nome compare per un po' nell'HUD
sel_skill:
        lda c_lvl
        cmp sk_req,x
        bcc _no
        stx c_skill
        stx hud_nm
        lda #SK_SHOW            ; il nome compare nell'HUD al posto di H J K L
        sta sk_t
        lda #1
        sta hud_dirty
_no     rts

; tasti del gioco (una volta per giro, solo i tasti appena premuti, keynew): abilita', poteri, cintura, pergamena,
; Q, C, I, M, RUN/STOP. Le schermate si aprono con jmp: al ritorno il giro ricomincia da capo
handle_keys:
; abilita': H J K L (riga 3 bit 5, riga 4 bit 2, riga 4 bit 5, riga 5 bit 2); Rage U (riga 3 bit 6), Frenzy O (riga 4 bit 6)
        lda keynew+3
        and #$20
        beq _k1
        ldx #0
        jsr sel_skill
_k1     lda keynew+4
        and #$04
        beq _k2
        ldx #1
        jsr sel_skill
_k2     lda keynew+4
        and #$20
        beq _k3
        ldx #2
        jsr sel_skill
_k3     lda keynew+5
        and #$04
        beq _kr
        ldx #3
        jsr sel_skill
_kr     lda keynew+3            ; U: Rage
        and #$40
        beq _kf
        ldx #4
        jsr buff_act
_kf     lda keynew+4            ; O: Frenzy
        and #$40
        beq _k4
        ldx #5
        jsr buff_act
_k4     lda keynew+7
        and #$01
        beq _p2
        ldx #0
        jsr use_potion
_p2     lda keynew+7
        and #$08
        beq _p3
        ldx #1
        jsr use_potion
_p3     lda keynew+1
        and #$01
        beq _p4
        ldx #2
        jsr use_potion
_p4     lda keynew+1
        and #$08
        beq _p5
        ldx #3
        jsr use_potion
_p5     lda keynew+2
        and #$01
        beq _kc
        jsr use_scroll
_kc     lda keynew+7            ; (17/11) Q: pagina delle quest (quest.asm; 18/11: l'elenco)
        and #$40
        beq +
        lda #0
        jmp ui_quest
+       lda keynew+2            ; (11/11) C: schermata del personaggio (punti statistica, respec)
        and #$10
        beq _inv
        jmp ui_charsheet
_inv    lda keynew+4
        and #$02
        beq _map
        jmp ui_inventory        ; (10/11) jmp: dopo la chiusura con RUN/STOP non si apre anche il menu di gioco
_map    lda keynew+4
        and #$10
        beq _end
        jmp ui_minimap          ; (stesso motivo: keynew contiene ancora il tasto di chiusura)
_end    lda keynew+7
        and #$80                ; RUN/STOP: menu di gioco
        beq _x
        jsr ui_gamemenu
_x      rts

; ===================================================================
;  mondo: trigger tile, esplorazione, timer
; ===================================================================
player_tile:
        lda px
        ldx px+1
        jsr pix2tile
        sta ptx
        lda py
        ldx py+1
        jsr pix2tile
        sta pty
        rts

; orologio, timer dell'effetto e del lampo del bordo, boss finale, esplorazione, tile sotto il PG, bauli in attesa
update_world:
        dec tod_cnt             ; minuti giocati: orologio TOD del CIA2 letto ogni 256 fotogrammi (5 s)
        bne _f
        jsr tod_tick
_f      lda fx_timer
        beq _f2
        dec fx_timer
_f2     lda flash_t
        beq _g
        dec flash_t
        bne _g
        lda #0
        sta BORDER
_g      jsr final_tick
        lda sk_t                ; scadenza del nome dell'abilita'
        beq _sk
        dec sk_t
        bne _sk
        lda hud_pend            ; (11/11) torna "H J K L": solo la riga 23
        ora #4
        sta hud_pend
_sk                             ; (effetti e musica: dall'IRQ di fine HUD, hud.asm)
        jsr player_tile
        lda ptx
        cmp lptx
        bne _newt
        lda pty
        cmp lpty
        beq _same
_newt   lda #0
        sta ch_blk
        lda ptx
        sta lptx
        lda pty
        sta lpty
        lda cur_level           ; nel villaggio EXPL ospita il baule della locanda (niente nebbia)
        beq _tt
        jsr mark_explored
_tt     jsr tile_trigger
_same   jsr act_tick
        lda c_hp
        ora c_hp+1
        bne _alive
.if ARENA
        jmp AR_DEAD
.else
        jmp player_die
.endif
_alive  rts                     ; (08/11: nessun menu di vittoria; tornera' con il quest system, docs/wiki/quests.md 6ter)

; esplorazione per la minimappa: le caselle a 4 o meno dal PG diventano viste (bit per settore)
mark_explored:
        lda ptx
        sec
        sbc #4
        bcs _a
        lda #0
_a      sta me_x0
        lda ptx
        clc
        adc #4
        cmp #47
        bcc _b
        lda #47
_b      clc
        adc #1
        sta me_x1
        lda pty
        sec
        sbc #3
        bcs _c
        lda #0
_c      sta me_y
        lda pty
        clc
        adc #3
        cmp #47
        bcc _d
        lda #47
_d      clc
        adc #1
        sta me_y1
        ; (11/11, prestazioni) una riga = 1 o 2 byte con una maschera ciascuno (al massimo 9 colonne: 2 byte), invece di
        ; un bit per volta: ~0,4 mila cicli a casella nuova invece di ~2,8 mila
        lda me_x0
        lsr
        lsr
        lsr
        sta me_x                ; primo byte della riga
        lda me_x0
        and #7
        tax
        lda me_lm,x
        sta me_x0               ; maschera del primo byte
        lda me_x1
        sec
        sbc #1                  ; ultima colonna
        tax
        and #7
        tay
        txa
        lsr
        lsr
        lsr
        cmp me_x
        beq _one
        lda me_rm,y             ; due byte: la maschera del secondo
        sta me_x1
        jmp _row
_one    lda me_rm,y             ; un byte solo: le due maschere insieme
        and me_x0
        sta me_x0
        lda #0
        sta me_x1
_row    ldx me_y
        lda exprow_lo,x
        sta ptr2
        lda exprow_hi,x
        sta ptr2+1
        ldy me_x
        lda (ptr2),y
        ora me_x0
        sta (ptr2),y
        lda me_x1
        beq +
        iny
        ora (ptr2),y
        sta (ptr2),y
+       inc me_y
        lda me_y
        cmp me_y1
        bne _row
        rts
me_lm   .byte $ff, $fe, $fc, $f8, $f0, $e0, $c0, $80     ; colonne da x a 7 del byte
me_rm   .byte $01, $03, $07, $0f, $1f, $3f, $7f, $ff     ; colonne da 0 a x del byte

; tile sotto il PG appena raggiunto: solo la fontana fa qualcosa da sola (cura); il resto aspetta il Fire (act_tick)
tile_trigger:
        lda ptx
        sta tx
        lda pty
        sta ty
        jsr get_tile
        cmp #T_CHEST            ; i bauli si aprono con Fire (act_tick -> chest_fire)
        bne _c0
        rts
_c0     cmp #T_FOUNTAIN         ; scale, portali, negozi, casa e bauli: solo con Fire (act_tick)
        beq _fount
        rts
_fount  lda c_hp
        cmp hpmax
        lda c_hp+1
        sbc hpmax+1
        bcc _heal
        rts                     ; gia' in piena salute: niente lampo del bordo
_heal   jsr hp_full
        lda #1
        sta hud_dirty
        lda #3
        ldx #6
        jmp set_flash

; scale e passaggi: cambiano luogo con change_level (A = piano, X = da dove si arriva: 0 scale giu', 1 su, 2 portale)
go_down lda cur_level
        cmp #MAXLEVEL           ; The Endless Abyss: non ancora disponibile
        bcc +
        rts
+       clc
        adc #1
        ldx #0
        jmp change_level
go_up   lda cur_level           ; (12/11) dal primo piano del capitolo: al villaggio (alla cripta)
        jsr lv_grp
        cpx #0
        bne _u1
        lda #0
        ldx #0
        jmp change_level
_u1     lda cur_level
        sec
        sbc #1
        ldx #1
        jmp change_level
; portale: dal piano al villaggio; dal villaggio al piano lasciato (c_retlvl)
go_portal
        lda cur_level
        beq _ft
        lda #0
        ldx #2
        jmp change_level
_ft     lda c_retlvl
        ldx #2
        jmp change_level
go_tdown                        ; ingresso del sotterraneo: primo piano del capitolo (12/11)
        lda c_chap
        cmp #CHAPTERS+1         ; (15/11) citta' dell'Abisso: la Bocca non porta ancora da nessuna parte (i piani non ci sono)
        bcs go_tdx
        jsr chap_first
        ldx #0
        jmp change_level
go_tdx  rts

; azioni sul tile: Fire (appena premuto) su scale / portali / negozi / casa / bauli.
; Il nome del luogo e' gia' mostrato in alto (loc_check).
act_tick:
        lda joynew
        and #$10
        beq _r
        jsr exit_open           ; (12/11) uscita del villaggio aperta: al capitolo dopo
        bcc +
        jmp chap_travel
+
        jsr pl_tile             ; (villaggio: anche la porta 1-2 caselle sopra)
        ldx #1
        cmp #T_STAIRSD
        beq _st
        inx
        cmp #T_STAIRSU
        beq _st
        inx
        cmp #T_TSTAIRS
        beq _st
        inx
        cmp #T_PORTAL
        bne +
        jsr at_lever            ; sala del trono: il portale per The Endless Abyss (non ancora aperto)
        beq _r
        lda #T_PORTAL
        bne _st
+       cmp #T_CHEST
        bne _n1
        jmp chest_fire
_n1     cmp #T_DHOME
        bne _shp
        lda cur_level
        cmp #MAXLEVEL
        bne +
        jmp ui_lever            ; sala del trono: la leva
+       jsr ovl_town            ; locanda: modulo MENU (gia' in memoria dall'ingresso nel villaggio)
        bcs _r
        jmp MENU_INN
_shp    cmp #T_DSMITH
        bcc _np
        cmp #T_DALCH+1
        bcs _np
        sbc #T_DSMITH-1         ; (C=0) negozio 0 fabbro, 1 alchimista
        pha
        jsr ovl_town            ; negozi: modulo MENU
        pla
        bcs _r
        jmp MENU_SHOP
_np     jsr npc_here            ; (17/11) nessun luogo sotto il PG: accanto a chi da' una quest (18/11: Hilde o un NPC che
        bcc _r                  ; vaga con il "!"), la quest e' presa e si apre il suo dettaglio (NPC_JTALK, src/menu/npc.asm)
        jmp NPC_JTALK
_r      rts
_st     stx st_kind
        cpx #2
        beq _gu
        cpx #3
        beq _gt
        cpx #4
        beq _gp
        jmp go_down
_gp     jmp go_portal
_gu     jmp go_up
_gt     jmp go_tdown

; Fire su un baule: nessun mostro vivo entro 2 caselle (distanza di Chebyshev < 3), poi chest_open (chiave)
chest_fire:
        jsr chest_blocked
        bcc _ok
        lda #1
        sta ch_blk
        lda #$ff
        sta lc_x                ; forza il ricalcolo dell'etichetta ("monster too close")
        rts
_ok     jmp chest_open

; C=1 se c'e' un mostro vivo a meno di 3 caselle dal PG
chest_blocked:
        ldx #0
_l      cpx lb_cnt
        bcs _free
        lda malive,x
        beq _n
        stx cb_i
        jsr mon_tx
        sec
        sbc ptx
        bcs _x
        eor #$ff
        clc
        adc #1
_x      cmp #3
        bcs _nx
        ldx cb_i
        jsr mon_ty
        sec
        sbc pty
        bcs _y
        eor #$ff
        clc
        adc #1
_y      cmp #3
        bcs _nx
        sec
        rts
_nx     ldx cb_i
_n      inx
        jmp _l
_free   clc
        rts

; morte del PG: suono, conteggio, schermata, meta' dell'oro addosso perso, risveglio al villaggio
player_die:
        jsr tod_tick            ; minuti giocati aggiornati prima del salvataggio
        lda #SFX_DIE
        jsr sfx_play
        inc c_deaths            ; morti (16 bit, si ferma a 65535)
        bne +
        inc c_deaths+1
        bne +
        dec c_deaths
+       jsr ui_died
        lsr c_gold+1
        ror c_gold
        jsr hp_full
        lda #1
        sta hud_dirty
        lda #0
        ldx #3
        jmp change_level

; ------------------------------------------------------------------ tempo giocato (TOD del CIA2)
; L'orologio TOD del CIA2 conta da solo (50 Hz della rete, anche con gli interrupt spenti, nei menu e durante
; i caricamenti). tod_start lo azzera all'avvio della partita; tod_tick somma i minuti interi ai bit 9..23 di
; c_game e rimette a 0 minuti e ore conservando secondi e decimi. Senza il segnale a 50 Hz dell'alimentatore
; il TOD resta fermo e il tempo giocato non cresce (nessuna protezione: decisione 06/11, spiegato nel manuale).
tod_start:
        lda $dd0f
        and #$7f                ; le scritture vanno all'orologio, non alla sveglia
        sta $dd0f
        lda $dd0e
        ora #$80                ; TOD a 50 Hz (PAL)
        sta $dd0e
        lda #0
        sta tod_cnt
        sta $dd0b               ; ore (ferma l'orologio)
        sta $dd0a
        sta $dd09
        sta $dd08               ; decimi: riparte
        rts

; minuti giocati: legge l'orologio TOD del CIA2 (ore, minuti, secondi, decimi: l'ordine che sblocca il latch), aggiunge
; ore x 60 + minuti ai bit 9-23 di c_game e fa ripartire l'orologio da 0 minuti con secondi e decimi conservati
tod_tick:
        lda $dd0b               ; ore: congela i registri (latch)
        and #$1f                ; senza il bit PM
        tax
        lda $dd0a               ; minuti BCD
        sta tmp2
        lda $dd09               ; secondi (da conservare)
        sta tmp0
        lda $dd08               ; decimi: sblocca il latch
        sta tmp1
        lda tmp2
        bne +
        txa
        beq _r                  ; meno di un minuto: niente da scrivere
+       txa
        jsr bcd2bin
        tax                     ; X = ore
        lda tmp2
        jsr bcd2bin             ; A = minuti 0..59
_h      asl a                   ; c_game bit 9..23 += A
        clc
        adc c_game+1
        sta c_game+1
        bcc +
        inc c_game+2
+       lda #60                 ; + 60 minuti per ogni ora (di norma 0 ore)
        dex
        bpl _h
        lda #0
        sta $dd0b               ; ferma
        sta $dd0a               ; minuti = 0
        lda tmp0
        sta $dd09
        lda tmp1
        sta $dd08               ; riparte con secondi e decimi conservati
_r      rts

bcd2bin:                        ; A BCD 00..99 -> binario: A - 6 x decine (usa tmp3)
        pha
        lsr a
        lsr a
        lsr a
        lsr a
        sta tmp3
        asl a
        adc tmp3
        asl a
        sta tmp3
        pla
        sec
        sbc tmp3
        rts

; ===================================================================
;  suoni (voce 1)
; ===================================================================
sfx_update:
        jsr sfx_step
        jmp music_update

; ===================================================================
;  sprite
; ===================================================================
; costruisce le shadow degli sprite in bs_en/bs_msb e le pubblica tutte insieme alla fine:
; l'IRQ (riga 70 con la barra, riga 250) copia le shadow e non deve mai vederle a meta'
; (sh_en azzerato a inizio costruzione = mostri spariti per un frame: lampeggio).
; (18/11) ent_x/ent_y = posizione del PG (px, py): update_player e bs_body (prima due copie uguali)
ent_pl: lda px
        sta ent_x
        lda px+1
        sta ent_x+1
        lda py
        sta ent_y
        lda py+1
        sta ent_y+1
        rts

build_sprites:
        jsr bs_body
        sei
        lda bs_en
        sta sh_en
        lda bs_msb
        sta sh_msb
        cli
        rts

; costruisce le ombre degli sprite del giro (sh_*): PG (0), effetto (2), mostri o NPC (3-7); HUD a pezzi (hud_step)
bs_body:
        jsr hud_step
        lda frame               ; avvisi dell'HUD: una volta ogni 16 fotogrammi
        and #15
        bne +
        jsr hud_warn
+
        lda #0
        sta bs_msb
        sta bs_en
        sta sh_xexp
        sta sh_yexp
        ; giocatore (sprite 0)
        jsr ent_pl
        ldx #0
        jsr spr_pos
        bcc _hud
        lda bs_en
        ora #1
        sta bs_en
        lda pdir
        asl
        ora panim
        clc
        adc #$80
        sta sh_ptr
        lda #10                 ; pelle dell'eroe (rosa chiaro)
        sta sh_col
_hud
        ; effetto (sprite 2)
        lda fx_timer
        beq _mon
        lda fx_x
        sta ent_x
        lda fx_x+1
        sta ent_x+1
        lda fx_y
        sta ent_y
        lda fx_y+1
        sta ent_y+1
        ldx #2
        jsr spr_pos
        bcc _mon
        lda bs_en
        ora #4
        sta bs_en
        ldx fx_kind
        cpx #5
        bcs _ring
        txa
        clc
        adc #$87
        sta sh_ptr+2
        lda #1
        sta sh_col+2
        jmp _mon
_ring   lda #$9a
        sta sh_ptr+2
        lda #7
        cpx #6
        bne _rc
        lda #10
_rc     sta sh_col+2
        ; mostri (sprite 3..7); nel villaggio gli NPC (17/11, quest.asm)
_mon    lda cur_level
        bne +
        jmp npc_draw
+       lda #3
        sta bs_slot
        lda #0
        sta bs_m
_ml     ldx bs_m
        cpx lb_cnt
        bcc +
        jmp _end
+
        lda malive,x
        bne +
        jmp _nm
+       lda mxl,x
        sta ent_x
        lda mxh,x
        sta ent_x+1
        lda myl,x
        sta ent_y
        lda myh,x
        sta ent_y+1
        ldx bs_slot
        jsr spr_pos
        bcc _nm
        ldx bs_slot
        lda bs_en
        ora bitmask,x
        sta bs_en
        ldx bs_m                ; (17/11) boss con nome sullo schermo: tema di combattimento (finche' resta sullo schermo,
        jsr mon_named           ; poi CMB_HOLD x 4 frame). Il boss finale ha il suo brano (mon_named lo esclude)
        bcc +
        lda #CMB_HOLD
        sta mus_cmb
+       ldx bs_slot
        ldy bs_m
        lda mtype,y
        tay
        lda lv_cboss            ; (12/11) boss del capitolo: il suo sprite sta nel posto del boss (tipo T_FINAL) del file
        beq _nob                ; del piano del boss (15/11, tools/build/monsters.py chapter_set), con il suo colore
        lda bs_m
        clc
        adc #1
        cmp lb_boss
        bne _nob
        ldy #T_FINAL
_nob    lda NM_AT-1,y           ; (15/11) colore del tipo nel set del capitolo (blocco info del file del tema)
        sta sh_col,x
        lda mon_ptr,y
        sta tmp0
        lda bs_m                ; boss del piano: colore lampeggiante
        clc
        adc #1
        cmp lb_boss
        bne _nf
        cpy #T_FINAL
        beq _nf
        lda frame
        and #8
        beq _nf
        lda #1
        sta sh_col,x
_nf
        lda frame
        lsr
        lsr
        lsr
        lsr
        and #1
        clc
        adc tmp0
        sta sh_ptr,x
        inc bs_slot
        lda bs_slot
        cmp #7
        beq _end
_nm     inc bs_m
        jmp _ml
_end    rts

