; ===================================================================
;  qpage.asm - (17/11, concept) pagina della quest: modulo su file, in testa a ogni file QSTn (tools/build/gen_quests.py:
;  codice + testo della quest), caricato a QBUF (= SCR_B) da ui_quest (src/game/quest.asm) ed eseguito; finisce con ui_exit.
;  Assemblato a parte con le etichette del gioco (out/work/game.lbl), come il LOBBY. Testo dopo il codice (qp_text):
;  nome di chi la da' 0, titolo 0, premio 0, righe 0 ..., $FF (QST0: solo $FF = "no quest").
; ===================================================================
        .include "../out/work/game.lbl"
        .include "macros.inc"
        * = QBUF
        .enc "screen"
        jmp qpage
tt_q    .text "quest", 0

; ------------------------------------------------------------------ pagina della quest
qpage:  jsr ui_begin
        lda #<tt_q
        ldx #>tt_q
        ldy #0
        jsr ui_title
        lda qp_text             ; QST0: nessun testo ($FF subito)
        cmp #$ff
        bne _full
        #ubox 0,8,40,5
        #at 4,10
        #msg "no quest: talk to the villagers"
        jmp _wait
_full   #ubox 0,1,40,3          ; da chi, testo (titolo sulla cornice), premio, stato
        #ubox 0,4,40,13
        #ubox 0,17,40,3
        #ubox 0,20,40,3
        jsr ui_labels
        .byte 2,1
        .text " from "
        .byte 0,2,17
        .text " reward "
        .byte 0,2,20
        .text " status "
        .byte 0,$ff
        lda #<qp_text
        sta q_p
        lda #>qp_text
        sta q_p+1
        #at 3,2
        jsr q_val               ; nome di chi la da'
        #at 2,4
        lda #$20
        jsr ui_putc
        jsr q_put               ; titolo, sulla cornice
        lda #$20
        jsr ui_putc
        #at 3,18
        jsr q_val               ; premio
        lda #5                  ; righe del testo
        sta q_y
_ln     lda q_p
        sta ptr2
        lda q_p+1
        sta ptr2+1
        ldy #0
        lda (ptr2),y
        cmp #$ff
        beq _st
        ldx #2
        ldy q_y
        jsr ui_at
        lda #UC_ITEM
        sta ui_col
        jsr q_put
        inc q_y
        bne _ln
_st     #at 3,21
        lda #UC_VALUE
        sta ui_col
        #msg "active"
_wait   #at 1,24
        #msg "fire/q/run/stop:back"
_k      jsr ui_input
        jsr ui_fire
        bne _x
        lda keynew+7
        and #$c0                ; RUN/STOP o Q
        beq _k
_x      jmp ui_exit

q_val   lda #UC_VALUE
        sta ui_col
; stringa a q_p (0 finale) alla posizione corrente; q_p passa alla stringa dopo
q_put   lda q_p
        ldx q_p+1
        jsr ui_puts
        lda q_p
        sec                     ; +1: lo 0 finale
        adc tmp5
        sta q_p
        bcc +
        inc q_p+1
+       rts

qp_text                         ; il testo della quest segue (gen_quests.py)
