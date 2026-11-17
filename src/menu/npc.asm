; (17/11, concept delle quest) piazzamento degli NPC del villaggio: nel modulo MENU (zona 1) per il margine di GAME.
; Chiamato da npc_tick (src/game/quest.asm) con MENU_NPC al primo giro nel villaggio (il modulo e' gia' in memoria).
; Variabili e il resto degli NPC: src/game/quest.asm.

; piazza gli NPC attorno al PG (ingresso nel villaggio): lo 0 due caselle a sinistra se libere, gli altri a caso a +-7
npc_init:
        ldx #NPC_N-1
_i      lda #$ff
        sta npc_xh,x
        lda #0
        sta npc_mv,x
        lda #16                 ; 16 tentativi per NPC
        sta npc_k
        cpx #0
        bne _rnd
        lda ptx
        sec
        sbc #2
        sta tx
        lda pty
        sta ty
        jsr npc_free
        bcc _put
_rnd    jsr rand
        and #15
        sec
        sbc #7
        clc
        adc ptx
        sta tx
        jsr rand
        and #15
        sec
        sbc #7
        clc
        adc pty
        sta ty
        jsr npc_free
        bcc _put
        dec npc_k
        bne _rnd
        beq _nx                 ; nessun posto: NPC assente
_put    lda tx                  ; casella -> pixel (centro)
        jsr _px
        sta npc_xl,x
        tya
        sta npc_xh,x
        lda ty
        jsr _px
        sta npc_yl,x
        tya
        sta npc_yh,x
        cpx #0
        bne _nx
        lda tx
        sta npc_tx0
        lda ty
        sta npc_ty0
_nx     dex
        bpl _i
        rts
_px     ldy #0                  ; A = casella -> A/Y = 16 * A + 8
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

