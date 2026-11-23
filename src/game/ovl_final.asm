; ===================================================================
;  ovl_final.asm - (19/11) CODICE DEL PIANO 20 (sala del trono): src/game/final.asm assemblato a OVP_AT ($C900) con le
;  etichette del gioco (out/work/game.lbl, tools/build/asm.sh) -> out/work/ovl_final.bin, nella coda di GFX8
;  (tools/build/bundle.py); gfx_tail (src/game/music.asm) lo copia a OVP_AT entrando nel piano 20. Tabella dei salti fissa
;  (OVJ_INIT, OVJ_TICK, OVJ_FIRE: src/game/theme.asm).
; ===================================================================
        .weak
ARENA_OVL = 0                   ; (23/11) 1 = versione per l'arena (tools/build/asm.sh: etichette di arena_game, OVP_AT = $F4E0)
        .endweak
.if ARENA_OVL
        .include "../out/work/arena_game.lbl"
.else
        .include "../out/work/game.lbl"
.endif
        .include "macros.inc"
        * = OVP_AT
.if OVP_RES                     ; build TESTUI 36: il codice del piano 20 e' gia' in GAME (theme.asm)
        rts
.else
        jmp final_init          ; OVJ_INIT
        jmp final_tick          ; OVJ_TICK
.if ARENA                       ; (23/11) versione per l'arena: niente leva (final.asm)
        rts                     ; OVJ_FIRE
        nop
        nop
.else
        jmp ui_lever            ; OVJ_FIRE
.endif
        rts                     ; OVJ_DMG: nessun cambio del danno
        nop
        nop
        sec                     ; OVJ_KILL: piano 20, ne' il boss ne' i mostri evocati lasciano bottino
        rts
        nop
        clc                     ; OVJ_DECOR (sala del trono: mappa fissa)
        rts
        nop
        clc                     ; OVJ_GEN
        rts
        nop
        .include "final.asm"
.endif
ovf_end
        .cerror ovf_end > OVP_END, "codice del piano 20 oltre $CFFF"
