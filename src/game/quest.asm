; ===================================================================
;  quest.asm - (17/11) NPC del villaggio e ingresso nelle quest: nel gioco restano le variabili, la pagina Q e i punti
;  d'ingresso; il codice degli NPC sta nel modulo MENU (zona 5, $8C00, src/menu/npc.asm, 18/11). (22/11) Le quest sono quelle
;  vere (decisioni D1-D19, docs/wiki/quests.md): motore src/game/qengine.asm, modulo QGIV src/qgiv.asm (Fire accanto a un NPC
;  fisso, e la pagina Q con il tasto Q ovunque). Il concept del 17-18/11 (QST0..QST8, src/qpage.asm) e' stato tolto.
;  NPC: lo 0 (il primo NPC fisso) fermo nella piazza della fontana; gli altri fissi al loro posto (npc_fix); i vaganti nel loro
;  settore (tk_sec). Il "!" sopra gli NPC fissi (sprite 1 e 2): giallo una quest da dare, verde una da ritirare (D12).
; ===================================================================
        .enc "screen"
NPC_N   = NSEC+1                ; (17/11) lo 0 da' la quest (fermo); gli altri NSEC vagano ognuno nel suo settore (tk_sec, villaggio)
QL_ID   = 20                    ; etichetta del luogo (bar.asm): nome di chi da' la quest
QL_GV   = 21                    ; (18/11) "quest giver" (concept; 22/11: nessun vagante da' quest)

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
npc_q   .fill NPC_N             ; (22/11, D12) segno degli NPC fissi: $87 "!" giallo, $97 "?" giallo, 0 niente (q_marks)
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
npc_vend
        .endv
;@map SND_FBUF_end..npc_vend "Quest e NPC del villaggio (quest.asm): posizioni, cammino, quest da aprire"
        .cerror npc_vend > NM_AT, "variabili di quest.asm oltre NM_AT"

; ------------------------------------------------------------------ pagina delle quest
; (22/11) tasto Q: la pagina delle quest prese nel modulo QGIV (q_k = $ff)
ui_quest:                       ; (22/11) pagina Q nel modulo QGIV (q_k = $ff): src/qgiv.asm
        lda #$ff
        sta q_k
        jmp q_load

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

; (21/11) NPC fissi (npc_fix) e colore del vestito (npc_colr): (22/11) nel modulo MENU, zona 1 (src/menu/npc_fix.asm), per
; recuperare memoria in GAME

; ------------------------------------------------------------------ chi e' accanto al PG
; C=1 se il PG e' accanto (a una casella, anche in diagonale) a Hilde o a un NPC con una quest da dare: X = NPC, Y = etichetta
; del luogo. (18/11, revisione R3) Il codice sta nel modulo MENU (zona 1, src/menu/npc_here.asm, MENU_NHERE): qui solo il controllo
npc_here:
        jsr npc_ok
        bcc +
        jmp MENU_NHERE
+       rts

