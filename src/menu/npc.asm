; ===================================================================
;  menu/npc.asm - (18/11) NPC del villaggio nel modulo MENU, zona 5 ($8C00-$8E7F: sprite forti del tema nel dungeon, liberi
;  nel villaggio; il modulo si rilegge a ogni ingresso nel villaggio): piazzamento, sprite e "!", Fire. Il passo dei vaganti
;  e chi e' accanto al PG restano in GAME (src/game/quest.asm, con variabili, tabelle in BFP e punti d'ingresso).
;  In testa: lo sprite del "!" (puntatore $30) e la tabella dei salti NPC_JT (src/game/stash.asm).
;  (18/11, committente) chi ha una quest da dare ha un "!" sopra la testa (sprite 1 e 2, ondeggia; 22/11, D12: giallo da
;  dare, verde da ritirare, solo gli NPC fissi: q_marks); un NPC con il PG vicino (2 caselle o meno) non parte per un altro
;  passo, cosi' e' facile fermarsi accanto a lui e premere Fire. (22/11) I vaganti non danno piu' quest (concept tolto: le
;  ripetibili verranno dopo, D18).
; ===================================================================
NPC_BPTR = (NPC_BANG-$8000)/64  ; $30
NPC_BUP  = 18                   ; il "!" sta 18 righe sopra lo sprite dell'NPC (14 righe disegnate: 4 righe di stacco)
NPC_BMIN = 80                   ; sopra questa riga c'e' la barra in alto (IRQ_BAR, bar.asm): li' il "!" non si disegna

        .binary "../out/work/gfx/npc_bang.bin"  ; NPC_BANG (64 B, tools/build/npc_gfx.py BANG)
        .cerror * != NPC_JT, "zona 5: la tabella dei salti degli NPC deve seguire lo sprite del !"
        jmp npc_init            ; NPC_JINIT
        jmp npc_draw5           ; NPC_JDRAW
        jmp _rts                ; NPC_JTALK (22/11: niente, il Fire va a QGIV)
        jmp npc_px              ; NPC_JPX (21/11, npc_fix in GAME)
        jmp npc_look            ; NPC_JLOOK

_rts    rts

; ------------------------------------------------------------------ piazzamento (ingresso nel villaggio)
; lo 0 (il primo NPC fisso del villaggio, k = 0) nella piazza della fontana (tk_g); gli altri, uno per settore (tk_sec, voce
; X-1): presenti a caso con probabilita' 7/8, su una casella libera presa a caso nel settore (16 tentativi, poi assente).
npc_init:
        ldx #NPC_N-1
_i      lda #$ff
        sta npc_xh,x
        lda #0
        sta npc_mv,x
        sta npc_q,x
        sta npc_d,x             ; (21/11) bit 7 = NPC fisso (npc_fix): i vaganti partono da 0
        lda #16
        sta npc_k
        cpx #0
        beq _t
        jsr rand                ; presente con probabilita' 7/8 (assente con 0 su 0..7)
        and #7
        bne _t
        jmp _nx
_t      txa
        asl
        asl
        tay
        cpx #0
        bne _s
        lda tk_g                ; chi da' la quest: la sua casella nella piazza della fontana (intestazione del villaggio)
        sta tx
        lda tk_g+1
        sta ty
        jmp _f
_s      lda tk_sec-2,y
        beq _nx                 ; voce non usata (larghezza 0)
        jsr npc_rm
        clc
        adc tk_sec-4,y
        sta tx
        lda tk_sec-1,y
        jsr npc_rm
        clc
        adc tk_sec-3,y
        sta ty
_f      jsr npc_free
        bcc _put
        dec npc_k
        bne _t
        beq _nx                 ; nessun posto: NPC assente
_put    lda tx                  ; casella -> pixel (centro)
        jsr npc_px
        sta npc_xl,x
        tya
        sta npc_xh,x
        lda ty
        jsr npc_px
        sta npc_yl,x
        tya
        sta npc_yh,x
        jsr npc_look            ; (17/11) disegno e colore (zona 3, npc_look.asm)
        cpx #0
        bne _w
        lda #$80                ; (21/11) fisso, nome 0 del villaggio (tk_fnb, npc_here1)
        sta npc_d
        lda tx
        sta npc_tx0
        lda ty
        sta npc_ty0
_w
_nx     dex
        bmi +
        jmp _i
+       jmp npc_fix             ; (21/11) gli NPC fissi al posto dei vaganti dei loro settori (zona 1, npc_here.asm)

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

; C=0 se la casella (tx,ty) e' dentro la mappa, calpestabile per gli NPC e non e' quella del PG. X conservato.
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
        lda solidtab,y          ; (19/11) bit 0 solido, bit 1 barriera per gli NPC (il traghetto): C=1 se uno dei due
        cmp #1
        rts
_s      sec
        rts

; ------------------------------------------------------------------ sprite (da build_sprites, nel villaggio)
; gli NPC visibili prendono gli sprite 3..7 uno dopo l'altro (i settori garantiscono che non siano piu' di 5 insieme; oltre il
; quinto non si disegna); chi ha una quest da dare ha il "!" (sprite 1, poi 2 se l'effetto del colpo non lo usa)
npc_draw5:
        lda #3
        sta npc_s
        lda #1
        sta npc_b
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
        lda npc_c,y
        sta sh_col,x
        lda npc_g,y             ; (17/11) il suo disegno, visto di fronte; passo animato mentre cammina
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
        adc #(MR4_AT-$8000)/64  ; slot 12 ($8C)
        sta sh_ptr,x
        jsr npc_bmark
        inc npc_s
        lda npc_s
        cmp #8
        beq _e
_n      ldx npc_k
        inx
        cpx #NPC_N
        bne _l
_e      rts

; X = sprite dell'NPC npc_k appena messo: se ha una quest da dare, il "!" sopra la sua testa nello sprite npc_b. X conservato
npc_bmark:
        ldy npc_k
        jsr npc_offer
        bcc _r
        sta tmp6                ; (22/11, D12) colore del segno: giallo da dare, verde da ritirare
        ldy npc_b
        cpy #3
        bcs _r                  ; gia' due "!" sullo schermo
        cpy #2
        bne +
        lda bs_en               ; lo sprite 2 e' dell'effetto del colpo quando c'e'
        and #4
        bne _r
+       lda frame               ; ondeggia: 2 righe su e giu' ogni 16 fotogrammi
        and #16
        lsr
        lsr
        lsr
        sta tmp7
        lda sh_y,x
        sec
        sbc #NPC_BUP
        sbc tmp7
        bcc _r
        cmp #NPC_BMIN
        bcc _r
        sta sh_y,y
        lda sh_x,x
        sta sh_x,y
        lda bs_msb
        and bitmask,x
        beq +
        lda bs_msb
        ora bitmask,y
        sta bs_msb
+       lda bs_en
        ora bitmask,y
        sta bs_en
        lda #NPC_BPTR
        sta sh_ptr,y
        lda tmp7                ; il suo colore, bianco quando e' in alto
        beq +
        lda #1
        .byte $2c               ; (bit abs: salta lda tmp6)
+       lda tmp6
        sta sh_col,y
        inc npc_b
_r      rts


