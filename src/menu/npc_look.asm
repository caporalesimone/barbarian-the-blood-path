; ===================================================================
;  npc_look.asm - (17/11) aspetto di un NPC del villaggio, nel modulo MENU (zona 3): disegno (npc_g, 4 disegni visti di
;  fronte, tools/build/npc_gfx.py) e colore del vestito (npc_c). Il colore non e' nessuno dei colori del villaggio (tk_pal:
;  sfondo, multicolor 1 e 2, accento) ne' uno dei due multicolor degli sprite (9 marrone, 15 grigio chiaro): con un colore del
;  terreno l'NPC sembrava trasparente (richiesta del committente, 17/11). Chi da' la quest: la donna, a partire dal giallo.
; ===================================================================
NPC_HILDE = 1                   ; disegno di chi da' la quest (npc_gfx.py HILDE)

; X = NPC (conservato)
npc_look:
        lda #NPC_HILDE
        cpx #0
        beq +
        jsr rand
        and #3
+       sta npc_g,x
        lda #7                  ; chi da' la quest: dal giallo; gli altri a caso
        cpx #0
        beq _t
        jsr rand
_t      and #15
        sta tmp7
        ldy #2
-       cmp tk_pal,y            ; sfondo, multicolor 1, multicolor 2
        beq _nx
        dey
        bpl -
        lda tk_pal+3            ; accento (color RAM = 8 + accento)
        and #7
        cmp tmp7
        beq _nx
        lda tmp7
        cmp #9                  ; multicolor degli sprite
        beq _nx
        cmp #15
        beq _nx
        sta npc_c,x
        rts
_nx     lda tmp7                ; il colore dopo
        clc
        adc #1
        jmp _t
