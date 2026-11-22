; ===================================================================
;  npc_look.asm - (17/11) aspetto di un NPC del villaggio, nel modulo MENU (zona 3): disegno (npc_g, 4 disegni visti di
;  fronte, tools/build/npc_gfx.py) e colore del vestito (npc_c): (22/11) uno dei 4 colori del villaggio (npc_col), scelti a
;  mano perche' non si confondano con i suoi terreni. Chi sta nella piazza: la donna, con il primo colore.
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
        ldy #0                  ; (22/11) colore del vestito: uno dei 4 del villaggio (npc_col, scelti sui suoi terreni:
        cpx #0                  ; tools/build/villages.py NPC_COL); chi sta nella piazza ha il primo. Prima: un colore a
        beq +                   ; caso fra quelli non usati dal villaggio (anche nero o grigio scuro su un fondo scuro)
        jsr rand
        and #3
        tay
+       jsr npc_colr            ; (GAME, quest.asm)
        sta npc_c,x
        rts
