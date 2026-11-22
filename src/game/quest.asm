; ===================================================================
;  quest.asm - (17/11, concept con testi segnaposto) quest e NPC del villaggio: nel gioco restano le variabili, l'apertura
;  delle pagine e i punti d'ingresso; il codice degli NPC sta nel modulo MENU (zona 5, $8C00, src/menu/npc.asm, 18/11).
;  Pagine (18/11, committente): tasto Q ovunque = elenco delle quest prese; Fire accanto a chi da' una quest = la si prende
;  e si apre il suo dettaglio. Pagina = file QST0 (codice + indice: capitolo e titolo di ogni quest, src/qpage.asm) letto in
;  QBUF = schermo B del gioco; il testo di una quest (QSTn) lo legge la pagina in QTXT. docs/wiki/villaggio.md (Abitanti), progetto in docs/wiki/quests.md.
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
; (19/11) nel fotogramma di un ridisegno completo (rd_sync) gli NPC tengono gli sprite del fotogramma prima (posizioni in
; sh_x/sh_y, solo i bit di bs_en e bs_msb da rimettere): ridisegno + sprite degli NPC sforavano il fotogramma. Un fotogramma
; con gli NPC spostati di 1-2 pixel rispetto allo scorrimento al posto di un fotogramma perso.
npc_draw:
        jsr npc_ok
        bcc _r
        lda rd_sync
        bne _old
        lda bs_en
        pha
        lda bs_msb
        pha
        jsr NPC_JDRAW
        pla
        eor bs_msb
        sta npc_msbm            ; bit aggiunti da npc_draw5 (lui li accende soltanto)
        pla
        eor bs_en
        sta npc_enm
_r      rts
_old    lda bs_en               ; sprite liberi in questo fotogramma fra quelli degli NPC
        eor #$ff
        and npc_enm
        sta tmp7
        ora bs_en
        sta bs_en
        lda npc_msbm
        and tmp7
        ora bs_msb
        sta bs_msb
        rts


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
; (19/11) dopo update_camera: nei fotogrammi in cui maybe_redraw ridisegna (la camera cambia cella, o force_redraw) il passo
; salta: ridisegno + NPC + i loro sprite sforavano il fotogramma (fotogrammi persi 0,3% -> 3-4% camminando vicino agli NPC)
npc_tick:                       ; (18/11, revisione R11) il passo dei vaganti sta nel modulo MENU (zona 6, src/menu/npc_tick.asm)
        lda cur_level
        bne +
        lda ovl_cur             ; modulo MENU in memoria (letto entrando nel villaggio)
        beq +
        jsr redraw_due
        bcs +
        jmp MR6_AT
+       rts

; (21/11, committente) NPC fissi 1..NFIX (tk_fix, intestazione del villaggio: tools/build/gen_maps.py fixed): ognuno prende il
; posto del vagante del suo settore (NPC numero = settore), fermo (npc_d bit 7, nome k nei bit 4-5), senza quest per ora,
; con il suo disegno e un colore a caso (npc_look). Lo chiama npc_init (zona 5 del MENU) alla fine; sta in GAME perche' le zone del MENU sono piene (usa npc_px della
; zona 5 e npc_look della zona 3: c'e' solo nel villaggio, con il modulo in memoria).
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
        jsr NPC_JPX
        sta npc_xl,x
        tya
        sta npc_xh,x
        lda ty
        jsr NPC_JPX
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
        jmp MENU_QMARK          ; (22/11, D12) segni delle quest sopra gli NPC fissi

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

; ------------------------------------------------------------------ chi e' accanto al PG
; C=1 se il PG e' accanto (a una casella, anche in diagonale) a Hilde o a un NPC con una quest da dare: X = NPC, Y = etichetta
; del luogo. (18/11, revisione R3) Il codice sta nel modulo MENU (zona 1, src/menu/npc_here.asm, MENU_NHERE): qui solo il controllo
npc_here:
        jsr npc_ok
        bcc +
        jmp MENU_NHERE
+       rts

