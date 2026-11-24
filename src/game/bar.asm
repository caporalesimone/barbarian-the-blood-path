; ===================================================================
;  bar.asm - bersaglio (nome e vita del mostro, etichetta del luogo, messaggi delle quest: testo in nbuf e celle in cellf,
;  scritti nella riga 19 dell'HUD da bt_row, hud.asm; fino al 23/11 in 8 sprite in alto) e database dei nomi dei boss.
;  (23/11, committente) della vecchia barra in sprite (doppio buffer $8800/$B000, costruzione a fasi) resta solo mm_glyphs:
;  il testo della minimappa (nbuf) negli sprite BARSPR a $8800
; ===================================================================
BARSPR     = $8800              ; testo della minimappa: 8 sprite x 64 byte, visibili al VIC (banco 2)
BARPTR     = (BARSPR - $8000) / 64

        .virtual $91a8
li_t       .byte ?              ; tile sotto il giocatore (loc_id)
bar_m      .byte ?              ; mostro bersaglio + 1 (0 = nessuno)
bar_t      .byte ?              ; frame residui di visualizzazione
bar_lhp    .byte ?
bar_on     .byte ?
bar_lab    .byte ?              ; 0 = barra mostro; >0 = etichetta luogo sotto il giocatore
bt_who     .byte ?              ; contenuto del testo gia' in nbuf: mostro+1 oppure $80|etichetta
lc_x       .byte ?              ; ultima casella/chiavi esaminate da loc_check
lc_y       .byte ?
lc_k       .byte ?
lc_l       .byte ?
bh1        .byte ?
bh2        .byte ?
bh3        .byte ?
bc_i      .byte ?
bn_i       .byte ?
nbuf       .fill 24
cellf      .fill 24
gbuf       .fill 8
        .endv
        .cerror cs_end > li_t, "variabili sovrapposte: sposta il blocco della barra"
        .cerror gbuf+8 > $9200, "blocco barra oltre $9200"


mul3    .for i = 0, i < 8, i = i + 1
        .byte i*3
        .next
bar_dl  .for i = 0, i < 24, i = i + 1
        .byte <(BARSPR + (i/3)*64 + (i%3))
        .next
bar_dh  .for i = 0, i < 24, i = i + 1
        .byte >(BARSPR + (i/3)*64 + (i%3))
        .next

; hash del boss del piano (dipende solo da seed e piano): bh1..bh3
boss_hash:
        lda rnd
        pha
        lda rnd+1
        pha
        jsr seed_level
        lda rnd
        eor #$5a
        sta rnd
        lda rnd+1
        eor #$c3
        ora #1
        sta rnd+1
        jsr rand
        jsr rand
        jsr rand
        jsr rand
        sta bh1
        jsr rand
        sta bh2
        jsr rand
        sta bh3
        pla
        sta rnd+1
        pla
        sta rnd
        rts

; nome del boss del piano -> lb_bn1 / lb_bn2
boss_name_idx:
        jsr boss_hash
        lda cur_level
        asl
        clc
        adc cur_level
        clc
        adc bh1
        and #7
        sta lb_bn1
        lda cur_level
        asl
        asl
        clc
        adc cur_level
        clc
        adc bh2
        and #7
        sta lb_bn2
        rts

; piazza il boss del piano (dopo place_chests)
place_boss:
        lda cur_level
        cmp #MAXLEVEL
        bne _new
        lda lb_cnt              ; boss finale gia' creato da spawn_monsters
        sta lb_boss             ; = indice + 1 dell'ultimo
        jmp boss_name_idx
_new    ldy lb_cnt
        cpy #31
        bcs _r
        lda cur_level
        jsr base_n
        jsr rndrange
        tax
        lda mt_fmin+N_BASE+1,x  ; versione forte di una famiglia del piano, se il suo piano minimo lo permette
        sec                     ; (<= piano + STRONG_EARLY); altrimenti la prima (fallen warchief)
        sbc #STRONG_EARLY
        bcc +
        cmp cur_level
        bcc +
        beq +
        ldx #0
+       txa
        clc
        adc #N_BASE+1
        ldy lb_cnt
        sta mtype,y
        ldx st_e
        jsr mon_new
        iny
        sty lb_boss
        jmp boss_name_idx
_r      rts

; (15/11, TODO D12) ptr0 = A x 8 + Y x 256 (indirizzo del glifo: codice x 8 + pagina base); preserva X
x8p:    sta ptr0
        lda #0
        sta ptr0+1
        asl ptr0
        rol ptr0+1
        asl ptr0
        rol ptr0+1
        asl ptr0
        rol ptr0+1
        tya
        clc
        adc ptr0+1
        sta ptr0+1
        rts

; stringa (A=lo, X=hi) -> nbuf[bn_i...]
bn_put:
        sta ptr2
        stx ptr2+1
        ldy #0
_c      lda (ptr2),y
        beq _d
        stx tmp7
        ldx bn_i
        cpx #24
        bcs _s
        sta nbuf,x
        inc bn_i
_s      ldx tmp7
        iny
        bne _c
_d      rts

; nbuf <- testo della barra in alto: l'etichetta del luogo (bar_lab, loc_name) o il nome del mostro bersaglio (bar_m:
; tipo, boss del capitolo dal file del tema, boss del piano con il nome generato da bh1..bh3)
bar_name:
        ldx #23
        lda #$20
_f      sta nbuf,x
        dex
        bpl _f
        lda #0
        sta bn_i
        lda bar_lab
        beq _nl
        jmp loc_name
_nl
        ldx bar_m
        lda mtype-1,x
        cmp #T_FINAL
        beq _type
        cpx lb_boss
        bne _type
        lda #T_FINAL            ; (15/11) boss del capitolo: il nome del posto del boss del file del tema ("the hollow abbot")
        ldy lv_cboss
        bne _type
        ldx lb_bn1
        lda fn_lo,x
        pha
        lda fn_hi,x
        tax
        pla
        jsr bn_put
        inc bn_i
        ldx lb_bn2
        lda ep_lo,x
        pha
        lda ep_hi,x
        tax
        pla
        jmp bn_put
_type   tax                     ; (15/11) A = tipo 1..9: nome del set del capitolo (blocco info del file del tema a NM_AT,
        lda NM_AT+8,x           ; tools/build/gen_gfx.py: 9 colori, 9 byte bassi degli indirizzi, nomi; una sola pagina)
        ldx #>NM_AT
        jmp bn_put

; vita del bersaglio in cellf (celle piene) e, se il bersaglio e' cambiato, il suo nome in nbuf
bar_build:
        lda #0
        sta bar_lab
        ; celle piene: i-esima piena se hp*24 > i*max
        ldx bar_m
        dex
        lda mhp,x
        sta bar_lhp
        sta sc_n                ; celle piene = vita x 24 / vita massima (16 bit); almeno una se vivo
        lda mhph,x
        sta sc_n+1
        lda mhm,x
        sta sc_d
        lda mhmh,x
        sta sc_d+1
        lda #24
        sta sc_k
        jsr scale
        bne +
        lda #1
+       sta tmp3
        ldy #0
_cl     lda #0
        cpy tmp3
        bcs +
        lda #1
+       sta cellf,y
        iny
        cpy #24
        bne _cl
        lda bar_m               ; (23/11) la vita va nella riga del bersaglio dell'HUD (bt_row, da cellf); il nome in nbuf
        cmp bt_who
        beq _r
        sta bt_who
        jsr bar_name
_r      rts


; (23/11) testo della minimappa: nbuf (24 codici schermo) negli sprite BARSPR a $8800, 3 caratteri per sprite, dalla
; char ROM. Sincrona (la minimappa la chiama una volta, all'apertura)
mm_glyphs:
        ldy #0
        tya
-       sta BARSPR,y
        sta BARSPR+$100,y
        iny
        bne -
        sty bc_i
_g      ldx bc_i
        lda nbuf,x
        ldy #$d0                ; ptr0 = $D000 (char ROM) + codice x 8
        jsr x8p
        ldy #7
        sei                     ; char ROM visibile solo per 8 letture
        lda #$32
        sta $01
_gy     lda (ptr0),y
        sta gbuf,y
        dey
        bpl _gy
        lda #MEMCFG
        sta $01
        cli
        ldx bc_i
        lda bar_dl,x
        sta ptr1
        lda bar_dh,x
        sta ptr1+1
        ldx #0
_gr     lda gbuf,x
        ldy mul3,x
        sta (ptr1),y
        inx
        cpx #8
        bne _gr
        inc bc_i
        lda bc_i
        cmp #24
        bne _g
        rts

; chiamata ogni frame dopo update_monsters
update_bar:                     ; (23/11) testo in nbuf e vita in cellf: bt_row (hud.asm) li scrive nell'HUD
        lda bar_t
        bne _act
        lda lb_boss
        beq _off
        tax
        dex
        lda malive,x
        beq _off
        lda mwake,x
        beq _off
        jsr bar_far
        bcs _off
        txa
        clc
        adc #1
        jsr bar_set
        lda #2
        sta bar_t
_act    dec bar_t
        ldx bar_m
        beq _off
        dex
        lda malive,x
        beq _off
        jsr bar_far             ; bersaglio fuori dallo schermo: via nome e barra
        bcs _off
        lda mhp,x
        cmp bar_lhp
        beq _on
        jsr bar_build
_on     lda #1
        sta bar_on
        rts
_off    lda #0
        sta bar_t
        jmp loc_check

; C=1 se il mostro X e' fuori dalla zona visibile (|dx| >= 176 o |dy| >= 112 px dal PG); X preservato
bar_far:                        ; (11/11, O11: valore assoluto con sabs, game.asm)
        lda mxl,x
        sec
        sbc px
        sta tmp0
        lda mxh,x
        sbc px+1
        sta tmp1
        jsr sabs                ; |dx| saturato a 255
        cmp #176
        bcs _far
        lda myl,x
        sec
        sbc py
        sta tmp0
        lda myh,x
        sbc py+1
        sta tmp1
        jsr sabs
        cmp #112
        rts                     ; C=1 se |dy| >= 112
_far    rts

; A = bersaglio+1
bar_set:
        cmp bar_m
        beq _r
        sta bar_m
        lda #0
        sta bar_lhp
_r      rts

; un mostro e' stato colpito: mostra la barra
bar_target:                     ; X = indice mostro (preservato)
        txa
        clc
        adc #1
        jsr bar_set
        lda #250
        sta bar_t
        rts

; ===================================================================
;  etichetta del luogo: scale, portali, porte dei negozi, bauli, fontana
;  (usa gli stessi 8 sprite della barra del mostro, che ha la precedenza)
; ===================================================================
loc_lo  .byte 0, <ls_down, <ls_up, <ls_tdown, <ls_portal, <ls_chest, <ls_kchest, <ls_gchest
        .byte <ls_smith, <ls_alch, <ls_fount, <ls_uptown, <ls_ptown, <ls_nokey, <ls_home, <ls_near, <ls_abyss
        .byte <ls_lever, <ls_epic, <ls_travel, <fix_nm, <ls_qgv, <ls_gdn, <ls_gup, <ls_gtown
        .byte <ls_qdone, <ls_found, <ls_seal                         ; (22/11) quest: QL_DONE, QL_FOUND, QL_SEAL
loc_hi  .byte 0, >ls_down, >ls_up, >ls_tdown, >ls_portal, >ls_chest, >ls_kchest, >ls_gchest
        .byte >ls_smith, >ls_alch, >ls_fount, >ls_uptown, >ls_ptown, >ls_nokey, >ls_home, >ls_near, >ls_abyss
        .byte >ls_lever, >ls_epic, >ls_travel, >fix_nm, >ls_qgv, >ls_gdn, >ls_gup, >ls_gtown
        .byte >ls_qdone, >ls_found, >ls_seal
gate_id .byte 22, 23, 0, 0, 0, 0, 0, 0, 0, 0, 24   ; (18/11) palude: id 1, 2, 11 -> cancelli
; numero da accodare: 0 nessuno, 1 = livello+1, 2 = livello-1, 3 = livello di ritorno del portale, 4 = 1; (22/11) 5 = nome
; dell'oggetto di quest q_mi
loc_numk .byte 0, 1, 2, 4, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 0, 0, 5, 0
        .enc "screen"
ls_down   .text "stairs down to level ", 0        ; (12/11, committente) + piano del capitolo 1..5 (loc_cl)
ls_up     .text "stairs up to level ", 0
ls_tdown  .text "stairs down to level ", 0
ls_portal .text "portal to level ", 0
ls_ptown  .text "portal to town", 0
ls_qgv    .text "quest giver", 0       ; (18/11) NPC che vaga con una quest da dare (QL_GV)
ls_chest  .text "chest", 0
ls_kchest .text "locked chest", 0
ls_gchest .text "golden chest", 0
ls_smith  .text "blacksmith", 0
ls_alch   .text "alchemist", 0
ls_uptown .text "stairs up to town", 0
ls_nokey  .text "locked: missing key!", 0
ls_home   .text "inn", 0
ls_near   .text "monster too close!", 0
ls_abyss  .text "the endless abyss", 0
ls_lever  .text "a suspicious lever", 0
ls_epic   .text "epic chest", 0
ls_travel .text "travel to next chapter", 0     ; (12/11, testo provvisorio del committente)
ls_gdn    .text "gate to level ", 0              ; (18/11) palude: cancello est (verso il piano dopo)
ls_gup    .text "gate back to level ", 0         ; cancello ovest
ls_gtown  .text "gate back to town", 0
ls_qdone  .text "quest complete", 0                ; (22/11) motore delle quest (qengine.asm)
ls_found  .text "found: ", 0                       ; + nome dell'oggetto di quest (qi_*, D19)
ls_seal   .text "the way is sealed", 0             ; (D4) scala verso il boss del capitolo senza il passo della catena
        .enc "none"

; id etichetta (0 = nessuna) per il tile sotto il giocatore -> A
; A = tile sotto il PG (tx/ty = ptx/pty). Nel villaggio, se non e' una porta, la porta di un negozio o di casa
; 1 o 2 caselle sopra (le porte sono sul muro sud: si entra anche da davanti). X conservato.
pl_tile:
        lda ptx
        sta tx
        lda pty
        sta ty
        jsr get_tile
        ldy cur_level
        bne _r
        jsr _door
        bcs _r
        lda pty
        cmp #2
        bcc _no
        dec ty
        jsr get_tile
        jsr _door
        bcs _r
        dec ty
        jsr get_tile
        jsr _door
        bcs _r
_no     lda pty
        sta ty
        jmp get_tile
_r      rts
_door   cmp #T_DHOME            ; C=1 se A e' una porta di negozio o di casa
        beq _y
        cmp #T_DSMITH
        bcc _n
        cmp #T_DALCH+1
        bcs _n
_y      sec
        rts
_n      clc
        rts

; A = etichetta del luogo sotto il PG (0 = nessuna): uscita del villaggio, scale, portali, porte, bauli, fontana,
; leva, chi da' una quest (npc_here); tx, ty conservati
loc_id:
        lda tx
        pha
        lda ty
        pha
        jsr pl_tile
        tax
        pla
        sta ty
        pla
        sta tx
        stx li_t
        jsr exit_open           ; (12/11) uscita del villaggio aperta: "travel to next chapter"
        bcc +
        lda #19
        rts
+       lda li_t
        cmp #T_BPORTAL          ; sala del trono: il portale nero della leva (Abisso): "the endless abyss"
        bne +
        lda #16
        rts
+       ldy #1
        cmp #T_STAIRSD
        bne +
        jmp _gate
+       cmp #T_STAIRSU
        bne _n2
        ldy #2
        lda cur_level           ; (12/11) primo piano del capitolo: "stairs up to town"
        jsr lv_grp
        cpx #0
        beq +
        jmp _gate
+
        ldy #11
_gate   txa                     ; (18/11) palude: "gate to ..." al posto di "stairs ..." (id 1, 2, 11 -> 22, 23, 24)
        pha
        ldx cur_level
        lda lv_look,x
        and #LK_SWAMP
        beq +
        lda gate_id-1,y
        tay
+       pla
        tax
        tya
        rts
_n2     ldy #3
        cmp #T_TSTAIRS
        beq _r
        cmp #T_PORTAL
        bne _n4
        ldy #4
        lda cur_level
        beq _r
        ldy #16                 ; sala del trono: il portale della leva
        jsr at_lever
        beq _r
        ldy #12
        bne _r
_n4     cmp #T_CHEST
        bne _n5
        ldy ch_blk              ; Fire rifiutato: mostro troppo vicino
        beq _cb
        ldy #15
        bne _r
_cb        jsr chest_here       ; baule epico: etichetta propria; X = indice del baule (negativo: non trovato)
        bcc +
        ldy #18
        bne _r
+       ldy #5
        txa
        bmi _r                  ; (non succede: ogni tile baule ha la sua voce in ch_t)
        lda ch_t,x              ; 10/11: il tipo viene da ch_t (1 normale, 2 chiave, 3 oro), non dal tile
        and #3
        tax
        dex                     ; 0..2 = tipo di baule
        txa
        clc
        adc #5
        tay                     ; id 5..7
        lda ch_keyr,x
        beq _r
        lda c_keys
        bne _r
        ldy #13                 ; serve una chiave e non ce n'e'
        bne _r
_n5        ldy #14
        cmp #T_DHOME
        bne _n6
        lda cur_level
        cmp #MAXLEVEL
        bne _r
        ldy #17                 ; sala del trono: la leva
        bne _r
_n6        lda li_t
        ldy #8
        cmp #T_DSMITH
        beq _r
        iny
        cmp #T_DALCH
        beq _r
        iny
        cmp #T_FOUNTAIN
        beq _r
        jsr npc_here            ; (17/11) nessun luogo: accanto a chi da' una quest, il suo nome (Y, quest.asm)
        bcs _r
        ldy #0
_r      tya
        rts

; Z=1 se il giocatore e' sulla leva / portale della sala del trono (Y conservato)
at_lever:
        lda cur_level
        cmp #MAXLEVEL
        bne _r
        lda ptx
        cmp #FIN_AX
        bne _r
        lda pty
        cmp #FIN_AY
_r      rts

; C=1 se sotto il giocatore c'e' un baule epico (bit 6); X = indice del baule in ch_t, $FF se non c'e'
chest_here:
        ldx #CH_MAX-1
_l      lda ch_t,x
        beq _n
        lda cx_x,x
        cmp ptx
        bne _n
        lda cx_y,x
        cmp pty
        bne _n
        lda ch_t,x
        asl
        asl                     ; bit 6 -> C
        rts
_n      dex
        bpl _l
        clc
        rts

; aggiorna la barra con l'etichetta del luogo (chiamata quando non c'e' un mostro)
loc_check:
        lda q_mt                ; (22/11) messaggio delle quest (qengine.asm q_msg): al posto dell'etichetta del luogo
        beq +
        dec q_mt
        lda q_ml
        jmp _have
+       lda ptx                 ; ricalcola solo se cambia casella o numero di chiavi
        cmp lc_x
        bne _calc
        lda pty
        cmp lc_y
        bne _calc
        lda c_keys
        cmp lc_k
        bne _calc
        lda lc_l
        jmp _have
_calc   jsr redraw_due          ; (19/11) fotogramma di ridisegno: l'etichetta di prima, si ricalcola al prossimo
        lda lc_l
        bcs _have
        lda ptx
        sta lc_x
        lda pty
        sta lc_y
        lda c_keys
        sta lc_k
        jsr loc_id
        sta lc_l
_have   cmp #0
        beq _none
        cmp bar_lab
        beq _on
        sta bar_lab
        ora #$80
        sta bt_who
        lda #0
        sta bar_m
        sta bar_lhp
        jsr bar_name
_on     lda #1
        sta bar_on
        rts
_none   lda #0
        sta bar_lab
        sta bar_on
        rts

; nbuf <- testo etichetta bar_lab (+ numero)
loc_name:
        ldx bar_lab
        lda loc_lo,x
        pha
        lda loc_hi,x
        tax
        pla
        jsr bn_put
        ldx bar_lab
        lda loc_numk,x
        beq nb_r
        cmp #5                  ; (22/11) "found: " + oggetto di quest
        bne _k0
        ldx q_mi
        lda qi_lo,x
        pha
        lda qi_hi,x
        tax
        pla
        jmp bn_put
_k0     cmp #4
        bne _k1
        lda c_chap              ; (12/11) cripta: primo piano del capitolo
        jsr chap_first
        jmp loc_cl
_k1     cmp #3
        bne _k2
        lda c_retlvl
        jmp loc_cl
_k2     cmp #2
        bne _k3
        lda cur_level
        sec
        sbc #1
        jmp loc_cl
_k3     lda cur_level
        clc
        adc #1
; (12/11, committente) A = piano globale -> piano del capitolo (1..CH_LV) in nbuf: le etichette dicono "level 3"
loc_cl:
        jsr lv_grp              ; X = indice nel capitolo
        inx
        txa
loc_num:                        ; A = 0..99 -> nbuf
        ldx #0
        sec
_t      sbc #10
        bcc _d
        inx
        bcs _t
_d      adc #10
        pha
        txa
        beq _u
        clc
        adc #$30
        jsr nb_chr
_u      pla
        clc
        adc #$30
; A = carattere in coda a nbuf (24 al massimo)
nb_chr  ldx bn_i
        cpx #24
        bcs nb_r
        sta nbuf,x
        inc bn_i
nb_r    rts
