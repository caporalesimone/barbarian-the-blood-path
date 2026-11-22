; ===================================================================
;  menu/npc_fix.asm - (22/11) parte del modulo MENU, zona 1: NPC fissi del villaggio (npc_fix), colore del vestito
;  (npc_colr) e "!" delle quest sulla minimappa (mm_qmark). Fino al 22/11 in GAME (src/game/quest.asm, src/game/ui.asm):
;  spostati per riportare il margine di GAME sopra 1 KB. Ci sono solo nel villaggio, con il modulo in memoria.
; ===================================================================
; (21/11, committente) NPC fissi 1..NFIX (tk_fix, intestazione del villaggio: tools/build/gen_maps.py fixed): ognuno prende il
; posto del vagante del suo settore (NPC numero = settore), fermo (npc_d bit 7, nome k nei bit 4-5), con il suo disegno e
; il colore del suo nome. Lo chiama npc_init (zona 5 del MENU) alla fine. (22/11) Spostato da GAME (src/game/quest.asm).
npc_fix:
        lda #NFIX
        sta npc_k
_l      lda npc_k
        asl
        tay
        lda tk_fix-2,y
        beq _n
        and #31
        tax                     ; X = NPC = settore
        lda tk_fix-1,y
        sta tmp6
        txa
        asl
        asl
        tay                     ; Y = 4 x settore: tk_sec-4,y = sua voce
        lda tmp6
        and #15
        clc
        adc tk_sec-4,y
        sta tx
        lda tmp6
        lsr
        lsr
        lsr
        lsr
        clc
        adc tk_sec-3,y
        sta ty
        lda tx
        jsr npc_px
        sta npc_xl,x
        tya
        sta npc_xh,x
        lda ty
        jsr npc_px
        sta npc_yl,x
        tya
        sta npc_yh,x
        lda npc_k
        asl
        asl
        asl
        asl
        ora #$80
        sta npc_d,x
        lda #0
        sta npc_mv,x
        sta npc_q,x
        lda npc_k               ; (22/11) colore fisso per nome: il k-esimo dei 4 del villaggio (prima a caso a ogni ingresso)
        and #3
        tay
        jsr npc_colr
        sta npc_c,x
        lda npc_k
        asl
        tay
        lda tk_fix-2,y
        lsr
        lsr
        lsr
        lsr
        lsr
        sta npc_g,x
_n      dec npc_k
        bne _l
        jmp q_marks             ; (22/11, D12) segni delle quest sopra gli NPC fissi

; (22/11) Y = 0..3 -> A = colore del vestito numero Y degli NPC del villaggio c_chap (npc_col, out/work/town_places.inc:
; tools/build/villages.py NPC_COL, scelti perche' non si confondano con i terreni). X conservato
npc_colr:
        sty tmp7
        lda c_chap
        asl
        asl
        adc tmp7                ; (C = 0)
        tay
        lda npc_col-4,y
        rts


; (22/11, committente) minimappa del villaggio: un "!" (glifo del font della UI, 8x8) sopra ogni NPC fisso con un segno
; (npc_q, q_marks: giallo una quest da dare, verde una da ritirare), negli sprite MI_N..MI_N+NFIX-1, nel colore del segno.
; Glifo 8x8 (mq_gl) a doppia grandezza. Casella dell'NPC come in npc_fix (tk_fix + tk_sec); x = 82 + 4 col (glifo
; centrato sulla casella, 9 bit), y = 34 + 4 riga (glifo appena sopra la casella). Uscita: tmp1 = bit di SPR_EN, tmp2 = bit di SPR_MSB
        .cerror MI_N + NFIX > 7, "segni delle quest nella minimappa: sprite oltre il 6"
mm_qmark:
        lda #0                  ; (22/11) il blocco del "?" ($B100) non lo azzera mm_names
        ldy #63
-       sta $b000+64*MI_N+64,y
        dey
        bpl -
        ldx #7
-       ldy mul3,x
        lda mq_gl,x
        sta $b000+64*MI_N,y
        lda mq_gq,x             ; (22/11) "?" nel blocco dopo
        sta $b000+64*MI_N+64,y
        dex
        bpl -
        lda #0
        sta tmp1
        sta tmp2
        lda npc_pend            ; NPC non ancora piazzati: npc_q non valido
        bne _r
        ldx #NFIX
_l      stx tmp0                ; tmp0 = k (1..NFIX)
        txa
        asl
        tay                     ; Y = 2k: tk_fix-2,y / tk_fix-1,y
        lda tk_fix-2,y
        beq _n
        and #31
        tax                     ; X = NPC = settore
        lda npc_q,x
        beq _n
        ldx tmp0
        pha
        and #$10
        sta mq_q-1,x            ; (22/11) "?" o "!"
        pla
        and #15
        sta SPR_COL+MI_N-1,x    ; colore del segno
        lda mq_bit-1,x
        ora tmp1
        sta tmp1
        lda tk_fix-1,y          ; (x - x0) | (y - y0) << 4
        sta tmp3
        lda tk_fix-2,y
        and #31
        asl
        asl
        tax                     ; X = 4 x settore: tk_sec-4,x = sua voce
        lda tmp0
        asl
        tay                     ; Y = 2k: SPR_X+2*(MI_N-1),y = registri dello sprite
        lda tmp3
        lsr
        lsr
        lsr
        lsr
        clc
        adc tk_sec-3,x          ; riga
        asl
        asl                     ; (righe < 64: C = 0)
        adc #34
        sta SPR_X+2*(MI_N-1)+1,y
        lda tmp3
        and #15
        clc
        adc tk_sec-4,x          ; colonna
        asl
        asl                     ; (colonne < 64: C = 0)
        adc #82
        sta SPR_X+2*(MI_N-1),y
        bcc +
        ldx tmp0                ; x oltre 255: bit MSB dello sprite
        lda mq_bit-1,x
        ora tmp2
        sta tmp2
+       ldx tmp0
        ldy #MG_B+MI_N          ; blocco del "!" (da dare) o del "?" (da ritirare: bit 4 di npc_q)
        lda mq_q-1,x
        beq +
        iny
+       tya
        sta SCR_A+$3f8+MI_N-1,x
_n      ldx tmp0
        dex
        bne _l
_r      rts
mq_gl   .byte $18, $18, $18, $18, $18, $00, $18, $00   ; "!" largo 2 pixel (il glifo del font e' largo 1: non si vedeva)
mq_gq   .byte $3c, $66, $06, $0c, $18, $00, $18, $00   ; (22/11) "?" largo 2 pixel (quest da ritirare)
mq_q    .fill NFIX              ; (22/11) per NPC fisso: $10 = "?"
mq_bit  .for i = 0, i < NFIX, i = i + 1
        .byte 1 << (MI_N + i)
        .next

