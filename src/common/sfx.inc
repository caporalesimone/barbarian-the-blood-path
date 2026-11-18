; ===================================================================
;  sfx.inc - effetti sonori sulla voce 1 del SID (gioco e jukebox)
;  sfx_play: A = effetto (X, Y conservati); sfx_step: una volta per fotogramma.
;  La voce 1 e' condivisa con la voce 1 (accordi) dei brani: durante l'effetto e il suo rilascio il player non la
;  usa (sp_mute+1), poi la riprende alla nota successiva ($80).
;  Variabili dell'includente: sfx_t, sfx_w, sfx_sx, sfx_sy, sfx_f, sfx_d, sfx_own.
; ===================================================================
SFX_SWING  = 0
SFX_HIT    = 1
SFX_HURT   = 2
SFX_PICK   = 3
SFX_LEVEL  = 4
SFX_DIE    = 5
SFX_PORTAL = 6                  ; apertura di un portale (suono che sale)
SFX_LOWHP  = 7                  ; vita bassa: un "tum" basso (hud_warn)
SFX_N      = 8
SFX_REL    = 25                 ; fotogrammi di rilascio dopo la fine dell'effetto (voce ancora occupata)

sfx_fhi .byte $40, $14, $0c, $48, $60, $06, $08, $30
sfx_wav .byte $81, $41, $81, $11, $11, $81, $11, $11
sfx_ad  .byte $01, $02, $03, $04, $06, $08, $28, $09
sfx_sr  .byte $f2, $f4, $f6, $f4, $f8, $fa, $c9, $00
sfx_dur .byte 4, 5, 8, 6, 16, 30, 40, 12
sfx_dfh .byte 0, 0, 0, 0, 0, 0, 2, 0   ; salita della frequenza per frame (byte alto)

; A = effetto (SFX_*): la voce 1 del SID passa agli effetti (sp_mute) e suona l'effetto (frequenza, inviluppo,
; forma d'onda, durata, scivolata); X, Y conservati
sfx_play:
        stx sfx_sx
        sty sfx_sy
        tax
        lda #1
        sta sp_mute+1           ; voce 1 agli effetti
        lda #0
        sta $d404
        sta $d400
        lda sfx_fhi,x
        sta $d401
        sta sfx_f
        lda sfx_dfh,x
        sta sfx_d
        lda sfx_ad,x
        sta $d405
        lda sfx_sr,x
        sta $d406
        lda sfx_dur,x
        sta sfx_t
        clc
        adc #SFX_REL
        sta sfx_own
        lda sfx_wav,x
        sta sfx_w
        sta $d404
        ldx sfx_sx
        ldy sfx_sy
        rts

; un fotogramma dell'effetto: scivolata della frequenza, gate chiuso a fine durata, voce 1 di nuovo al brano dopo
; il rilascio (SFX_REL)
sfx_step:
        lda sfx_own
        beq _r
        dec sfx_own
        bne +
        lda #$80                ; voce 1 di nuovo al brano dalla nota successiva
        sta sp_mute+1
+       lda sfx_t
        beq _r
        lda sfx_f               ; scivolata di frequenza (solo per i suoni che la prevedono)
        clc
        adc sfx_d
        sta sfx_f
        sta $d401
        dec sfx_t
        bne _r
        lda sfx_w
        and #$fe
        sta $d404
_r      rts
