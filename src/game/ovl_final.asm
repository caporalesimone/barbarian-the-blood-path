; ===================================================================
;  ovl_final.asm - (19/11) CODICE DEL PIANO 20 (sala del trono): src/game/final.asm assemblato a OVP_AT ($C900) con le
;  etichette del gioco (out/work/game.lbl, tools/build/asm.sh) -> out/work/ovl_final.bin, nella coda di GFX8
;  (tools/build/bundle.py); gfx_tail (src/game/music.asm) lo copia a OVP_AT entrando nel piano 20. Tabella dei salti fissa
;  (OVJ_INIT, OVJ_TICK, OVJ_FIRE: src/game/theme.asm).
; ===================================================================
        .include "../out/work/game.lbl"
        .include "macros.inc"
        * = OVP_AT
.if OVP_RES                     ; build ARENA / TESTUI 36: il codice del piano 20 e' gia' in GAME (theme.asm)
        rts
.else
        jmp final_init          ; OVJ_INIT
        jmp final_tick          ; OVJ_TICK
        jmp ui_lever            ; OVJ_FIRE
        rts                     ; OVJ_DMG: nessun cambio del danno
        nop
        nop
        .include "final.asm"
.endif
ovf_end
        .cerror ovf_end > OVP_END, "codice del piano 20 oltre $CFFF"
