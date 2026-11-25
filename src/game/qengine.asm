; ===================================================================
;  qengine.asm - (22/11, decisioni D1-D19 del committente, docs/wiki/quests.md) motore residente delle quest: gli agganci
;  che scattano nel dungeon. Non conosce i testi: guarda le quest prese nello stato salvato (q_step, q_flag, q_cnt, q_side,
;  src/game/game.asm) e le tabelle qt_* (out/work/qtab.inc, tools/build/gen_qdata.py). Offerta, consegna e premi: modulo
;  del villaggio QGIV (da fare).
;  Posti delle quest attive (q_slot): 0 = passo della catena q_step+1 se preso (q_flag bit 0) e non ancora raggiunto
;  (bit 1); 1..4 = accessorie q_side (id 1..15 = QID 13..27, bit 7 = obiettivo raggiunto). Contatore: q_cnt per la catena,
;  il byte dopo l'id per le accessorie (indice dal q_cnt: QC_SIDE + 2k).
;  Eventi (q_ev): QE_KILL (kill_monster: K, B, P, oggetto da mostro IM), QE_CHEST (baule del boss con nome, prima apertura:
;  oggetto da baule IC, D19), QE_CBOSS (boss del capitolo o boss finale: C). Si conta solo una quest presa (Q13); la morte non
;  tocca nulla (Q10).
; ===================================================================
QGATE    = 1                           ; (22/11) 1 = cancello D4 attivo sulle scale (act_tick)
QGATE_CH = 2                           ; (22/11, D13) cancello solo nei capitoli 1..QGATE_CH (24/11: anche il capitolo 2, tipi di
                                        ; mostro verificati, QREW-14); gli altri capitoli restano aperti finche' non si estende
QE_KILL  = 1
QE_CHEST = 2
QE_CBOSS = 3
QC_SIDE  = q_side - q_cnt               ; indice dell'id della prima accessoria rispetto a q_cnt
        .cerror q_sdone != q_cnt + 1 || q_side != q_cnt + 3, "stato delle quest: q_cnt, q_sdone, q_side contigui"
QM_TIME  = 150                          ; fotogrammi del messaggio nella barra (~3 s)
QL_DONE  = 25                           ; etichette della barra (bar.asm): "quest complete"
QL_FOUND = 26                           ; "found: " + nome dell'oggetto (q_mi)
QL_SEAL  = 27                           ; (D4) "the way is sealed"

        .virtual LVLEND                 ; (variabili non salvate, dopo LVLBLK; azzerate solo da q_reset)
q_e     .byte ?                         ; evento in corso
q_sl    .byte ?                         ; posto in esame
q_ci    .byte ?                         ; indice del contatore (da q_cnt)
q_tp    .byte ?                         ; QE_KILL: tipo del mostro ucciso
q_nm    .byte ?                         ; QE_KILL: 1 = boss con nome
q_mt    .byte ?                         ; fotogrammi rimasti del messaggio (0 = nessuno)
q_ml    .byte ?                         ; etichetta del messaggio
q_mi    .byte ?                         ; oggetto di quest del messaggio "found: ..."
q_vend
        .endv
        .cerror q_vend > $9abf, "variabili del motore delle quest oltre $9ABE (mslide)"

; ---- X = posto 0..4 -> Y = QID-1, q_ci = indice del contatore; C = 1 se il posto non ha una quest da contare
q_slot:
        txa
        bne _sd
        lda q_flag              ; catena: presa e non ancora raggiunta
        and #3
        cmp #1
        bne _no
        ldy q_step
        cpy #QT_CHAIN
        bcs _no
        lda #0
        sta q_ci
        clc
        rts
_sd     asl                     ; accessoria k = X-1: id a QC_SIDE + 2k
        clc
        adc #QC_SIDE-2
        tay
        lda q_cnt,y
        beq _no                 ; posto vuoto
        bmi _no                 ; gia' raggiunta (da riscuotere)
        iny
        sty q_ci
        clc
        adc #QT_CHAIN-1         ; QID - 1 = 12 + id - 1
        tay
        clc
        rts
_no     sec
        rts

; ---- C = 1 se la quest Y-1 (Y = QID-1) vale per il capitolo corrente (tipi di mostro e boss del capitolo)
q_chap:
        lda qt_ty,y
        lsr
        lsr
        lsr
        lsr
        cmp c_chap
        beq +
        clc
        rts
+       sec
        rts

; ---- C = 1 se cur_level sta fra qt_p1 e qt_p2 della quest Y
q_inlv:
        lda cur_level
        cmp qt_p1,y
        bcc _n
        lda qt_p2,y
        cmp cur_level
        bcc _n
        sec
        rts
_n      clc
        rts

; ---- evento A (QE_*) per tutte le quest prese
q_ev:
        sta q_e
        ldx #4
_s      stx q_sl
        jsr q_slot
        bcs _n
        jsr q_chk
        bcc _n
        jsr q_inc
_n      ldx q_sl
        dex
        bpl _s
        rts

; ---- C = 1 se l'evento q_e conta per la quest Y
q_chk:
        lda qt_ty,y
        and #$0f
        tax
        lda q_e
        cmp #QE_CBOSS
        beq _cb
        cmp #QE_CHEST
        beq _ch
        cpx #QG_K               ; QE_KILL
        beq _mt
        cpx #QG_IM
        beq _im
        cpx #QG_P
        beq _lv
        cpx #QG_B
        bne _no
        lda q_nm
        beq _no
_lv     jmp q_inlv
_im     jsr q_chap
        bcc _no
        lda q_tp
        cmp qt_p1,y
        bne _no
        jsr rand
        cmp qt_p2,y
        bcs _no
        bcc _fnd
_mt     jsr q_chap
        bcc _no
        lda q_tp
        cmp qt_p1,y
        bne _no
        sec
        rts
_ch     cpx #QG_IC
        bne _no
        jsr q_inlv
        bcc _no
_fnd    lda qt_it,y             ; "found: ..."
        sta q_mi
        lda #QL_FOUND
        jsr q_msg
        sec
        rts
_cb     cpx #QG_C
        bne _no
        jmp q_chap
_no     clc
        rts

; ---- contatore + 1 della quest Y (posto q_sl); raggiunta la quantita': segnata da riscuotere, messaggio e lampo
q_inc:
        ldx q_ci
        lda q_cnt,x
        cmp #255
        bcs +
        adc #1
        sta q_cnt,x
+       cmp qt_n,y
        bcc _r
        lda q_sl
        bne _sd
        lda q_flag
        ora #2
        sta q_flag
        bne _dn
_sd     dex                     ; id dell'accessoria: bit 7
        lda q_cnt,x
        ora #$80
        sta q_cnt,x
_dn     lda q_mt                ; "found: ..." appena messo dallo stesso evento: resta quello
        cmp #QM_TIME
        beq +
        lda #QL_DONE
        jsr q_msg
+       lda #SFX_LEVEL
        jsr sfx_play
        lda #5
        ldx #25
        jmp set_flash
_r      rts

; ---- messaggio A nella barra per QM_TIME fotogrammi (loc_check)
q_msg:
        sta q_ml
        lda #QM_TIME
        sta q_mt
        rts

; ---- agganci
; kill_monster: X = mostro ucciso (conservato)
q_kill:
        lda mtype,x
        sta q_tp
        lda #0
        sta q_nm
        jsr mon_named           ; (X conservato)
        bcc +
        inc q_nm
+       lda #QE_KILL
        jsr q_ev
        ldx km_i
        rts
q_chest:
        lda #QE_CHEST
        jmp q_ev
q_cboss:
        lda #QE_CBOSS
        jmp q_ev

; ---- (D4) cancello: C = 1 se la scala verso il piano del boss del capitolo e' chiusa. Si passa se il passo "uccidi il boss"
; del capitolo (3c) e' preso, o gia' consegnato. A = piano di destinazione.
q_gate:
        jsr is_cboss
        bcc _r
        lda c_chap
        cmp #QGATE_CH+1
        bcs _op
        lda c_chap              ; passo 3c - 1 = q_step che lo precede
        asl
        adc c_chap
        sec
        sbc #1
        cmp q_step
        bcc _r                  ; q_step > 3c-1: passo gia' consegnato (C = 0)
        bne _sl                 ; q_step < 3c-1: passo non ancora offerto
        lda q_flag
        lsr                     ; C = bit 0 (preso)
        bcs _op
_sl     lda #QL_SEAL
        jsr q_msg
        sec
        rts
_op     clc
_r      rts

; ---- (25/11, committente: "una quest si deve sempre poter concludere") entrando in un piano, DOPO lo stato salvato
; (load_level: mostri morti tolti), per ogni quest presa e non ancora raggiunta che conta in questo piano:
;  1. ripopolamento mirato: se il piano non le offre piu' niente - K, IM (tipo del capitolo), P (piano nel suo intervallo):
;     nessun mostro vivo; B (boss con nome nei piani p1..p2): boss morto; IC (baule del boss nei piani p1..p2): boss morto e
;     il suo baule gia' aperto - tutti i mostri rigenerati del piano tornano vivi (come in una partita nuova; i bauli no);
;  2. (D11, 22/11) K e IM: se nel piano non c'e' un mostro VIVO del tipo, il primo mostro vivo che non e' il boss lo diventa.
; Niente nei piani del boss del capitolo (solo il boss) e nel villaggio. Prima del 25/11 q_spawn girava prima di load_level
; (contava e convertiva anche mostri poi tolti perche' morti) e non c'era il ripopolamento: un piano ripulito prima di prendere
; la quest la bloccava (boss con nome gia' ucciso, piano vuoto).
q_spawn:
        lda lv_cboss
        bne _r0
        lda cur_level
        bne +
_r0     rts
+
        ldx #4                  ; 1. ripopolamento
_s      stx q_sl
        jsr q_slot
        bcs _n
        jsr q_need
        bcc _n
        ldx lb_cnt              ; tutti vivi
        lda #1
-       dex
        bmi _n
        sta malive,x
        bpl -
_n      ldx q_sl
        dex
        bpl _s
        ldx #4                  ; 2. D11
_c      stx q_sl
        jsr q_slot
        bcs _m
        lda qt_ty,y
        and #$0f
        cmp #QG_K
        beq +
        cmp #QG_IM
        bne _m
+       jsr q_chap
        bcc _m
        lda qt_p1,y
        sta q_tp
        ldx lb_cnt              ; ce n'e' gia' uno vivo?
-       dex
        bmi _cv
        lda malive,x
        beq -
        lda mtype,x
        cmp q_tp
        bne -
        beq _m
_cv     ldx #0                  ; il primo vivo che non e' il boss
-       cpx lb_cnt
        bcs _m
        lda malive,x
        beq +
        txa
        clc
        adc #1
        cmp lb_boss
        beq +
        lda q_tp
        sta mtype,x
        bne _m
+       inx
        bne -
_m      ldx q_sl
        dex
        bpl _c
_r      rts

; ---- C = 1 se la quest Y conta in questo piano e il piano non le offre piu' niente (q_spawn, punto 1)
q_need:
        lda qt_ty,y
        and #$0f
        cmp #QG_K
        beq _k
        cmp #QG_IM
        beq _k
        cmp #QG_P
        beq _p
        cmp #QG_IC
        beq _ic
        cmp #QG_B
        bne _no
        jsr q_inlv              ; B: boss del piano morto
        bcc _no
        bcs _bd
_ic     jsr q_inlv              ; IC: boss morto e il suo baule non c'e' piu' (aperto)
        bcc _no
        lda lb_bch
        bne _no
_bd     ldx lb_boss
        beq _no                 ; piano senza boss: il ripopolamento non aiuta
        lda malive-1,x
        bne _no
        sec
        rts
_k      jsr q_chap
        bcc _no
        bcs _any
_p      jsr q_inlv
        bcc _no
_any    ldx lb_cnt              ; K, IM, P: nessun mostro vivo
-       dex
        bmi _y
        lda malive,x
        beq -
_no     clc
        rts
_y      sec
        rts

; ===================================================================
;  (22/11) NPC del villaggio: chi da' e chi ritira. Usati dal modulo QGIV (src/qgiv.asm) e dai segni (D12). La quest Y
;  (QID-1) e' del capitolo qt_ty bit 4-6; qt_np: bit 0-1 NPC fisso che la da', bit 2-3 chi la ritira, bit 7 = serve la
;  quest precedente (accessorie: "after").
; ===================================================================
        .virtual q_vend
q_k     .byte ?                 ; NPC fisso (k di villages.FIXED) con cui si parla
q_t     .byte ?
q_t2    .byte ?
q_t3    .byte ?                 ; (q_sdn: Y salvato)
q_vend2
        .endv
        .cerror q_vend2 > $9abf, "variabili del motore delle quest oltre $9ABE (mslide)"

; q_sdn, q_sfind, q_offer, q_tin: nel modulo MENU (src/menu/q_who.asm, zona 1: servono solo nel villaggio), MENU_QOFFER /
; MENU_QTIN

; Fire accanto all'NPC fisso X (act_tick, npc_here): il modulo QGIV (file "qstg") a CORE_AT, eseguito (finisce con ui_exit).
; Copre il segmento CORE (core_ok = 0: ui_exit lo rilegge a schermo nero)
q_talk:
        lda npc_d,x             ; nome k = bit 4-5
        lsr
        lsr
        lsr
        lsr
        and #3
        sta q_k
q_load: ldy #nm_qst-nm_tab      ; "QST" + "G" (q_k: NPC, $ff = pagina Q)
        jsr set_name4
        lda #$47                ; "G" (PETSCII maiuscolo, come i nomi di nm_tab)
        sta cmdbuf+6
        lda #2
        sta io_what
        lsr core_ok
        lda #<CORE_AT
        sta ptr0
        lda #>CORE_AT
        sta ptr0+1
        jsr load_raw
        bcs +
        jmp CORE_AT
+       jmp ui_exit
