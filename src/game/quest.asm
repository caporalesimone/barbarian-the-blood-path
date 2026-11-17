; ===================================================================
;  quest.asm - (17/11, concept con testi segnaposto) pagina della quest e NPC del villaggio.
;  Pagina: tasto Q ovunque, o Fire davanti a chi da' la quest (NPC 0, fermo); il testo e' nel file QSTn (data/quests.yaml,
;  tools/build/gen_quests.py), letto a ogni apertura in QBUF = schermo B del gioco (si ridisegna all'uscita: ui_exit).
;  NPC: figure dell'eroe in altri colori (sprite 3-7, liberi nel villaggio; 5 al massimo disegnati insieme): lo 0 fermo (quest),
;  gli altri vagano piano (una casella alla volta, a caso) solo con il PG vicino e SOLO nel loro settore (17/11, tk_sec).
;  docs/wiki/quests.md, "Concept del 17/11".
; ===================================================================
        .enc "screen"
QBUF    = SCR_B
NPC_N   = NSEC+1                ; (17/11) lo 0 da' la quest (fermo); gli altri NSEC vagano ognuno nel suo settore (tk_sec, villaggio)
NPC_R   = 10                    ; gli NPC vaganti si muovono solo con il PG a meno di 10 caselle (su entrambi gli assi)
QL_ID   = 20                    ; etichetta del luogo (bar.asm): nome di chi da' la quest
Q_CUR   = 1                     ; (concept) la quest dell'NPC del villaggio

; Le tabelle degli NPC stanno nella tabella della ricerca di percorso dei mostri (BFP, $A500, 169 B): nel villaggio non ci sono
; mostri, e ogni ricerca (mon_path) la riempie di $ff prima di usarla. Annotazione @map di BFP in game.asm.
        .virtual BFP
npc_xl  .fill NPC_N
npc_xh  .fill NPC_N             ; $ff = NPC assente
npc_yl  .fill NPC_N
npc_yh  .fill NPC_N
npc_d   .fill NPC_N             ; direzione (0 +x, 1 -x, 2 +y, 3 -y)
npc_mv  .fill NPC_N             ; pixel di cammino rimasti (0 = fermo)
npc_tend
        .endv
        .cerror npc_tend > BFQ, "tabelle degli NPC oltre BFP (169 B)"

        .virtual SND_FBUF_end   ; (coda degli slot sprite 58-63, prima di NM_AT)
npc_tx0 .byte ?                 ; casella dell'NPC 0
npc_ty0 .byte ?
npc_pend .byte ?                ; 1 = da piazzare (ingresso nel villaggio)
npc_s   .byte ?                 ; prossimo sprite libero in npc_draw
npc_k   .byte ?
q_p     .word ?                 ; (src/qpage.asm) puntatore del testo
q_y     .byte ?
npc_vend
        .endv
;@map SND_FBUF_end..npc_vend "Quest e NPC del villaggio (quest.asm): posizioni, cammino, puntatore del testo"
        .cerror npc_vend > NM_AT, "variabili di quest.asm oltre NM_AT"

; ------------------------------------------------------------------ pagina della quest
; La pagina e' un modulo su file: QSTn = codice della pagina (src/qpage.asm) + testo della quest n (QST0 = "no quest"),
; caricato a QBUF ed eseguito (finisce con ui_exit). Nel gioco restano solo queste righe.
ui_quest:
        ldy #nm_qst-nm_tab      ; "QST" + numero della quest (0 = nessuna)
        jsr set_name4
        lda c_qst
        clc
        adc #$30
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

; ------------------------------------------------------------------ NPC del villaggio
; C=1 se il PG e' accanto all'NPC 0 (a una casella, anche in diagonale) nel villaggio
npc_here:
        lda cur_level
        bne _n
        lda npc_xh
        cmp #$ff
        beq _n
        lda ptx
        sec
        sbc npc_tx0
        clc
        adc #1
        cmp #3
        bcs _n
        lda pty
        sec
        sbc npc_ty0
        clc
        adc #1
        cmp #3
        bcs _n
        sec
        rts
_n      clc
        rts

; A = numero a caso da 0 a A-1 (A = 1..63). Y conservato.
npc_rm:
        sta tmp7
        jsr rand
        and #63
-       cmp tmp7
        bcc +
        sbc tmp7
        bcs -
+       rts

npc_px  ldy #0                  ; A = casella -> A/Y = 16 * A + 8
        sty tmp7
        asl
        rol tmp7
        asl
        rol tmp7
        asl
        rol tmp7
        asl
        rol tmp7
        ora #8
        ldy tmp7
        rts

; C=0 se la casella (tx,ty) e' dentro la mappa, calpestabile e non e' quella del PG. X conservato.
npc_free:
        lda tx
        cmp #MAPW
        bcs _s
        lda ty
        cmp #MAPH
        bcs _s
        lda tx
        cmp ptx
        bne +
        lda ty
        cmp pty
        beq _s
+       jsr get_tile
        tay
        lda solidtab,y
        lsr
        rts
_s      sec
        rts

; (npc_init: nel modulo MENU, zona 1, src/menu/npc.asm, per il margine di GAME; si chiama con MENU_NPC)

; un passo per fotogramma alterno: i vaganti, se il PG e' vicino, partono a caso (1 volta su 64) per una casella
npc_tick:
        lda cur_level
        beq +                  
        jmp _r
+
        lda npc_pend
        beq +
        lda ovl_cur             ; modulo MENU in memoria (letto entrando nel villaggio): piazza gli NPC
        beq +
        lda #0
        sta npc_pend
        jsr player_tile         ; (ptx, pty dell'ingresso: al primo giro non sono ancora aggiornati)
        jsr MENU_NPC
+       lda frame
        and #1
        beq +                  
        jmp _r
+
        ldx #NPC_N-1
_l      lda npc_xh,x
        cmp #$ff
        bne +                  
        jmp _n
+
        lda npc_mv,x
        bne _mv
        cpx #0                  ; chi da' la quest resta fermo
        bne +                  
        jmp _n
+
        jsr npc_tile
        lda tx
        sec
        sbc ptx
        clc
        adc #NPC_R
        cmp #2*NPC_R+1
        bcc +                  
        jmp _n
+
        lda ty
        sec
        sbc pty
        clc
        adc #NPC_R
        cmp #2*NPC_R+1
        bcc +
        jmp _n
+       jsr rand                ; (17/11) parte 1 volta su 16 (era 64: sembravano tutti fermi)
        and #15
        beq +
        jmp _n
+
        jsr rand
        and #3
        sta npc_d,x
        jsr npc_in              ; la casella dopo il passo e' fuori dal settore: resta fermo
        bcc +
        jmp _n
+
        lda #8                  ; 8 passi da 2 px = una casella
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
+
_r      rts
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

; X = NPC -> (tx, ty) = la sua casella
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

; sprite degli NPC (villaggio: al posto dei mostri, sprite 3..7), da build_sprites: gli NPC visibili prendono gli sprite
; liberi uno dopo l'altro (i settori garantiscono che non siano piu' di 5 insieme; oltre il quinto non si disegna)
npc_draw:
        lda #3
        sta npc_s
        ldx #0
_l      stx npc_k
        lda npc_xh,x
        cmp #$ff
        beq _n
        sta ent_x+1
        lda npc_xl,x
        sta ent_x
        lda npc_yl,x
        sta ent_y
        lda npc_yh,x
        sta ent_y+1
        ldx npc_s
        jsr spr_pos
        bcc _n
        lda bs_en
        ora bitmask,x
        sta bs_en
        ldy npc_k
        lda npc_col,y
        sta sh_col,x
        lda npc_d,y             ; figura dell'eroe nella sua direzione; passo animato mentre cammina
        asl
        sta tmp7
        lda npc_mv,y
        beq +
        lda frame
        lsr
        lsr
        lsr
        and #1
+       ora tmp7
        clc
        adc #$80
        sta sh_ptr,x
        inc npc_s
        lda npc_s
        cmp #8
        beq _e
_n      ldx npc_k
        inx
        cpx #NPC_N
        bne _l
_e      rts
npc_col .byte 7, 5, 14, 15, 13, 3, 2, 4, 8, 6, 9, 11, 12, 1, 5, 14, 15   ; colori (pool): 0 = chi da' la quest, poi uno per settore
        .cerror * - npc_col != NPC_N, "npc_col: un colore per NPC"
