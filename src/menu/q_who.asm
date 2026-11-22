; ===================================================================
;  menu/q_who.asm - (22/11) quest: chi da' e chi ritira, nel modulo MENU (zona 1: servono solo nel villaggio; in GAME
;  costavano ~300 B di margine). Li usano il modulo QGIV (src/qgiv.asm, attraverso MENU_QOFFER / MENU_QTIN) e i segni
;  degli NPC (D12). Tabelle e variabili in GAME (src/game/qengine.asm, out/work/qtab.inc).
; ===================================================================
; A = id dell'accessoria (1..15): C = 1 se gia' consegnata (bit id-1 di q_sdone). X, Y conservati
q_sdn:
        sty q_t3
        sec
        sbc #1
        pha
        and #7
        tay
        pla
        cmp #8
        lda bitmask,y
        bcs +
        and q_sdone
        jmp ++
+       and q_sdone+1
+       ldy q_t3
        cmp #1                  ; C = 1 se il bit c'e'
        rts

; A = id dell'accessoria: C = 1 se e' in q_side (X = suo indice 0, 2, 4, 6). Y conservato
q_sfind:
        sta q_t
        ldx #6
-       lda q_side,x
        and #$7f
        cmp q_t
        beq _f
        dex
        dex
        bpl -
        clc
        rts
_f      sec
        rts

; A = NPC: C = 1 se ha una quest da dare, A = Y = QID-1. Catena: il passo q_step+1 non preso, del capitolo corrente. Accessorie
; del capitolo (Q9: dopo il primo passo della catena del capitolo), non fatte, non prese, con la precedente fatta se serve, e un
; posto libero in q_side (Q2: al massimo 4)
q_offer:
        sta q_k
        ldy q_step
        cpy #QT_CHAIN
        bcs _sd
        lda q_flag
        lsr
        bcs _sd
        jsr q_chap
        bcc _sd
        lda qt_np,y
        and #3
        cmp q_k
        bne _sd
        tya
        sec
        rts
_sd     lda c_chap              ; 3c - 2 = primo passo del capitolo: consegnato?
        asl
        adc c_chap
        sbc #2                  ; (C = 0: 3c - 3)
        cmp q_step
        bcs _no                 ; q_step <= 3c - 3
        ldx #6
-       lda q_side,x
        beq +
        dex
        dex
        bpl -
        bmi _no
+       ldy #QT_CHAIN
_l      jsr q_chap
        bcc _nx
        lda qt_np,y
        and #3
        cmp q_k
        bne _nx
        tya
        sbc #QT_CHAIN-1         ; (C = 1) id
        sta q_t2
        jsr q_sdn
        bcs _nx
        lda q_t2
        jsr q_sfind
        bcs _nx
        lda qt_np,y
        bpl _ok
        lda q_t2                ; la precedente (id - 1) fatta?
        sec
        sbc #1
        jsr q_sdn
        bcc _nx
_ok     tya
        sec
        rts
_nx     iny
        cpy #QT_NUM
        bne _l
_no     clc
        rts

; A = NPC: C = 1 se ha una quest da ritirare, A = Y = QID-1, X = indice in q_side ($ff = catena). Catena: passo raggiunto e
; chi lo ritira e' l'NPC. Accessorie: raggiunte (bit 7), o con l'obiettivo G (oro da consegnare all'NPC) prese
q_tin:
        sta q_k
        lda q_flag
        and #3
        cmp #3
        bne _sd
        ldy q_step
        lda qt_np,y
        lsr
        lsr
        and #3
        cmp q_k
        bne _sd
        ldx #$ff
        tya
        sec
        rts
_sd     ldx #6
_l      lda q_side,x
        beq _n
        sta q_t
        and #$7f
        clc
        adc #QT_CHAIN-1
        tay
        lda qt_np,y
        lsr
        lsr
        and #3
        cmp q_k
        bne _n
        lda q_t
        bmi _y
        lda qt_ty,y
        and #$0f
        cmp #QG_G
        beq _y
_n      dex
        dex
        bpl _l
        clc
        rts
_y      tya
        sec
        rts


; (22/11, D12) segni degli NPC fissi: npc_q = $85 (verde: una quest da ritirare), $87 (giallo: una da dare), 0 niente. Li
; chiamano npc_fix (ingresso nel villaggio) e QGIV prima di uscire (MENU_QMARK)
q_marks:
        ldx #NPC_N-1
_l      lda npc_d,x
        bpl _n
        txa
        pha
        lda npc_d,x
        lsr
        lsr
        lsr
        lsr
        and #3
        pha
        jsr q_tin
        pla
        ldy #$85
        bcs _s
        jsr q_offer
        ldy #$87
        bcs _s
        ldy #0
_s      pla
        tax
        tya
        sta npc_q,x
_n      dex
        bpl _l
        rts
