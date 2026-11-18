; ===================================================================
;  quest.asm - (17/11, concept con testi segnaposto) quest e NPC del villaggio: nel gioco restano le variabili, l'apertura
;  delle pagine e i punti d'ingresso; il codice degli NPC sta nel modulo MENU (zona 5, $8C00, src/menu/npc.asm, 18/11).
;  Pagine (18/11, committente): tasto Q ovunque = elenco delle quest prese; Fire accanto a chi da' una quest = la si prende
;  e si apre il suo dettaglio. Pagina = file QST0 (codice + indice: capitolo e titolo di ogni quest, src/qpage.asm) letto in
;  QBUF = schermo B del gioco; il testo di una quest (QSTn) lo legge la pagina in QTXT. docs/wiki/quests.md.
;  NPC: lo 0 (Hilde, quest 1) fermo nella piazza della fontana; gli altri vagano nel loro settore (tk_sec) e ogni tanto
;  offrono una quest (npc_q). Chi ha una quest da dare ha un "!" sopra la testa (sprite 1 e 2).
; ===================================================================
        .enc "screen"
QBUF    = SCR_B
QTXT    = $b000                 ; (18/11) testo della quest aperta (file QSTn): sprite della barra, set B ($B000-$B3FF; come la
                                ; minimappa, la pagina li usa e all'uscita la barra si ricostruisce: qp_out in src/qpage.asm)
QTXT_END = SCR_A
NPC_N   = NSEC+1                ; (17/11) lo 0 da' la quest (fermo); gli altri NSEC vagano ognuno nel suo settore (tk_sec, villaggio)
QL_ID   = 20                    ; etichetta del luogo (bar.asm): nome di chi da' la quest
QL_GV   = 21                    ; (18/11) "quest giver": NPC che vaga con una quest da dare
Q_CUR   = 1                     ; (concept) la quest di Hilde
        .cerror Q_N > 8, "quest: al massimo 8 (c_qst e' una maschera di 8 bit)"

; Le tabelle degli NPC stanno nella tabella della ricerca di percorso dei mostri (BFP, $A500, 169 B): nel villaggio non ci sono
; mostri, e ogni ricerca (mon_path) la riempie di $ff prima di usarla. Annotazione @map di BFP in game.asm.
        .virtual BFP
npc_xl  .fill NPC_N
npc_xh  .fill NPC_N             ; $ff = NPC assente
npc_yl  .fill NPC_N
npc_yh  .fill NPC_N
npc_d   .fill NPC_N             ; direzione (0 +x, 1 -x, 2 +y, 3 -y)
npc_mv  .fill NPC_N             ; pixel di cammino rimasti (0 = fermo)
npc_g   .fill NPC_N             ; (17/11) disegno: 0..3 (tools/build/npc_gfx.py, slot 12-19)
npc_c   .fill NPC_N             ; (17/11) colore del vestito, diverso dai colori del villaggio (npc_look, src/menu/npc_look.asm)
npc_q   .fill NPC_N             ; (18/11) quest da dare (1..Q_N), 0 = nessuna; lo 0 ha sempre la quest 1
npc_tend
        .endv
        .cerror npc_tend > BFQ, "tabelle degli NPC oltre BFP (169 B)"

        .virtual SND_FBUF_end   ; (coda degli slot sprite 58-63, prima di NM_AT)
npc_tx0 .byte ?                 ; casella dell'NPC 0
npc_ty0 .byte ?
npc_pend .byte ?                ; 1 = da piazzare (ingresso nel villaggio)
npc_s   .byte ?                 ; prossimo sprite libero in npc_draw
npc_k   .byte ?
npc_b   .byte ?                 ; (18/11) prossimo sprite del "!" (1, 2; 3 = finiti)
npc_am  .byte ?                 ; (18/11) quest gia' offerte in questo villaggio (maschera, npc_init)
q_open  .byte ?                 ; (18/11) quest da aprire subito nella pagina (0 = elenco)
npc_vend
        .endv
;@map SND_FBUF_end..npc_vend "Quest e NPC del villaggio (quest.asm): posizioni, cammino, quest da aprire"
        .cerror npc_vend > NM_AT, "variabili di quest.asm oltre NM_AT"

; ------------------------------------------------------------------ pagina delle quest
; A = quest da aprire subito (0 = elenco). Il file QST0 (codice + indice) a QBUF, eseguito (finisce con ui_exit).
ui_quest:
        sta q_open
        ldy #nm_qst-nm_tab      ; "QST0"
        jsr set_name4
        lda #$30
        sta cmdbuf+6
        lda #2                  ; schermata di attesa generica (titolo e "please wait")
        sta io_what
        lda #<QBUF
        sta ptr0
        lda #>QBUF
        sta ptr0+1
        jsr load_raw
        bcs +
        jmp QBUF
+       jmp ui_exit             ; file non letto: di nuovo nel gioco

; ------------------------------------------------------------------ NPC del villaggio: ingressi nel modulo MENU (zona 5)
; Il codice c'e' solo nel villaggio, con il modulo MENU in memoria e gli NPC gia' piazzati (npc_pend = 0).
NPC_R    = 10                   ; i vaganti si muovono solo con il PG a meno di 10 caselle (su entrambi gli assi)
NPC_STOP = 2                    ; (18/11) ... e stanno fermi con il PG a 2 caselle o meno
npc_draw:
        jsr npc_ok
        bcc +
        jmp NPC_JDRAW
+       rts


; C=1 se il codice degli NPC si puo' chiamare (villaggio, modulo MENU in memoria, NPC piazzati)
npc_ok: lda cur_level
        ora npc_pend
        bne _n
        lda ovl_cur
        beq _n
        sec
        rts
_n      clc
        rts

; ------------------------------------------------------------------ un giro (dal ciclo principale, nel villaggio)
; al primo giro piazza gli NPC; poi, a fotogrammi alterni, un passo per i vaganti: con il PG vicino (NPC_R) partono a caso
; (1 volta su 16) per una casella, ma non se il PG e' a NPC_STOP caselle o meno (18/11)
npc_tick:
        lda cur_level
        bne _r0
        lda ovl_cur             ; modulo MENU in memoria (letto entrando nel villaggio)
        bne +
_r0     rts
+       lda npc_pend
        beq +
        lda #0
        sta npc_pend
        jsr player_tile         ; (ptx, pty dell'ingresso: al primo giro non sono ancora aggiornati)
        jsr NPC_JINIT           ; npc_init (src/menu/npc.asm)
+       lda frame
        and #15
        bne +
        lda #$ff                ; (18/11) ogni 16 fotogrammi l'etichetta del luogo si ricalcola (bar.asm, loc_check): un NPC
        sta lc_x                ; arrivato accanto al PG fermo, o la quest appena presa
+       lda frame
        and #1
        beq +
        rts
+       ldx #NPC_N-1
_l      lda npc_xh,x
        cmp #$ff
        bne +
        jmp _n
+       lda npc_mv,x
        bne _mv
        cpx #0                  ; chi da' la quest resta fermo
        bne +
        jmp _n
+       jsr npc_tile
        lda tx
        sec
        sbc ptx
        clc
        adc #NPC_R
        cmp #2*NPC_R+1
        bcc +
        jmp _n
+       sec
        sbc #NPC_R-NPC_STOP     ; dx + NPC_STOP (0..2 x NPC_STOP = vicino)
        sta tmp6
        lda ty
        sec
        sbc pty
        clc
        adc #NPC_R
        cmp #2*NPC_R+1
        bcc +
        jmp _n
+       sec
        sbc #NPC_R-NPC_STOP     ; dy + NPC_STOP
        cmp #2*NPC_STOP+1
        bcs _go
        lda tmp6
        cmp #2*NPC_STOP+1
        bcs _go
        jmp _n                  ; PG a NPC_STOP caselle o meno su entrambi gli assi: fermo
_go     jsr rand                ; (17/11) parte 1 volta su 16 (era 64: sembravano tutti fermi)
        and #15
        beq +
        jmp _n
+       jsr rand
        and #3
        sta npc_d,x
        jsr npc_in              ; la casella dopo il passo e' fuori dal settore: resta fermo
        bcc +
        jmp _n
+       lda #8                  ; 8 passi da 2 px = una casella
        sta npc_mv,x
_mv     lda npc_xl,x
        sta ent_x
        lda npc_xh,x
        sta ent_x+1
        lda npc_yl,x
        sta ent_y
        lda npc_yh,x
        sta ent_y+1
        stx npc_k
        lda #0
        sta st_nz
        ldy npc_d,x
        lda npc_st,y
        cpy #2
        bcs _y
        jsr try_step_x
        jmp _c
_y      jsr try_step_y
_c      ldx npc_k
        bcs _stop
        lda ent_x               ; non sulla casella del PG
        ldy ent_x+1
        jsr pix_t
        cmp ptx
        bne _ok
        lda ent_y
        ldy ent_y+1
        jsr pix_t
        cmp pty
        beq _stop
_ok     lda ent_x
        sta npc_xl,x
        lda ent_x+1
        sta npc_xh,x
        lda ent_y
        sta npc_yl,x
        lda ent_y+1
        sta npc_yh,x
        dec npc_mv,x
        jmp _n
_stop   lda #0
        sta npc_mv,x
_n      dex
        bmi +
        jmp _l
+       rts
npc_st  .byte 2, $fe, 2, $fe

; X = NPC (1..), (tx, ty) = la sua casella: C=1 se il prossimo passo (npc_d) esce dal suo settore (tk_sec, voce X-1). Cambia tx, ty
npc_in:
        ldy npc_d,x
        lda tx
        clc
        adc npc_dx,y
        sta tx
        lda ty
        clc
        adc npc_dy,y
        sta ty
        txa
        asl
        asl
        tay
        lda tx
        sec
        sbc tk_sec-4,y          ; x - x0
        cmp tk_sec-2,y          ; >= larghezza (anche se negativo: grande)
        bcs +
        lda ty
        sec
        sbc tk_sec-3,y
        cmp tk_sec-1,y
+       rts
npc_dx  .byte 1, $ff, 0, 0
npc_dy  .byte 0, 0, 1, $ff

; X = NPC -> (tx, ty) = la sua casella. X conservato
npc_tile:
        lda npc_xl,x
        ldy npc_xh,x
        jsr pix_t
        sta tx
        lda npc_yl,x
        ldy npc_yh,x
        jsr pix_t
        sta ty
        rts
pix_t   sty tmp7                ; A/Y = pixel -> A = casella
        lsr tmp7
        ror
        lsr tmp7
        ror
        lsr tmp7
        ror
        lsr tmp7
        ror
        rts

; ------------------------------------------------------------------ chi e' accanto al PG
; C=1 se il PG e' accanto (a una casella, anche in diagonale) a Hilde o a un NPC con una quest da dare: X = NPC, Y = etichetta
; del luogo (QL_ID Hilde, QL_GV "quest giver"). tx, ty conservati (loc_id, bar.asm)
npc_here:
        jsr npc_ok
        bcs +
        rts
+       lda tx
        pha
        lda ty
        pha
        ldx #0
_l      lda npc_xh,x
        cmp #$ff
        beq _n
        txa
        beq _t                  ; Hilde: sempre (anche con la quest gia' presa: la si rilegge)
        tay
        jsr npc_offer
        bcc _n
_t      jsr npc_tile
        lda tx
        sec
        sbc ptx
        clc
        adc #1
        cmp #3
        bcs _n
        lda ty
        sec
        sbc pty
        clc
        adc #1
        cmp #3
        bcs _n
        ldy #QL_GV
        txa
        bne +
        ldy #QL_ID
+       sec
        bcs _x
_n      inx
        cpx #NPC_N
        bne _l
        clc
_x      pla
        sta ty
        pla
        sta tx
        rts

; Y = NPC: C=1 se ha una quest da dare (A = quest). Cambia Y
npc_offer:
        lda npc_q,y
        beq _no
        tay
        lda bitmask-1,y
        and c_qst
        bne _no
        tya
        sec
        rts
_no     clc
        rts

