; (17/11, concept delle quest) piazzamento degli NPC del villaggio: nel modulo MENU (zona 1) per il margine di GAME.
; Chiamato da npc_tick (src/game/quest.asm) con MENU_NPC al primo giro nel villaggio (il modulo e' gia' in memoria).
; Variabili e il resto degli NPC (anche npc_rm, npc_px e npc_free, per il margine di questa zona): src/game/quest.asm.

; piazza gli NPC: lo 0 (quest) a caso attorno al PG (+-7 caselle); gli altri, uno per settore (tk_sec, voce X-1): presenti a
; caso con probabilita' 1/2, su una casella libera presa a caso nel settore. 16 tentativi per NPC, poi assente.
npc_init:
        ldx #NPC_N-1
_i      lda #$ff
        sta npc_xh,x
        lda #0
        sta npc_mv,x
        lda #16
        sta npc_k
        cpx #0
        beq _t
        jsr rand                ; presente solo con probabilita' 1/2
        and #1
        beq _nx
_t      txa
        asl
        asl
        tay
        cpx #0
        bne _s
        lda #15                 ; chi da' la quest: attorno al PG
        jsr npc_rm
        clc
        adc ptx
        sec
        sbc #7
        sta tx
        lda #15
        jsr npc_rm
        clc
        adc pty
        sec
        sbc #7
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
        cpx #0
        bne _nx
        lda tx
        sta npc_tx0
        lda ty
        sta npc_ty0
_nx     dex
        bmi +
        jmp _i
+       rts
