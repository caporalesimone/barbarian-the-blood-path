; ===================================================================
;  zx0.inc - decompressore ZX0 v2 (formato di Einar Saukas, toolchain/zx0/LICENSE; specifica in tools/build/zx0dec.py)
;  Ingresso: zx_src = dati compressi, zx_dst = destinazione. jsr zx0_unpack. Sul posto: l'ultimo byte compresso
;  deve stare almeno "delta" byte sopra l'ultimo byte decompresso (tools/build/pack.py lo calcola e lo verifica).
;  Prima dell'include definire ZX_ZP = primo di 12 byte liberi in pagina zero. Non usa sei (la musica in IRQ
;  continua). Usa A, X, Y. Verificato byte per byte in VICE da tests/test_loader.py (GAME, 39 KB).
; ===================================================================
zx_src  = ZX_ZP                 ; (2) puntatore ai dati compressi
zx_dst  = ZX_ZP+2               ; (2) puntatore alla destinazione
zx_cp   = ZX_ZP+4               ; (2) sorgente della copia
zx_len  = ZX_ZP+6               ; (2) lunghezza / valore Elias
zx_off  = ZX_ZP+8               ; (2) ultimo offset
zx_bv   = ZX_ZP+10              ; byte dei bit (con un 1 sentinella in coda)
zx_t    = ZX_ZP+11

zx_bit  .macro                  ; un bit -> C (20 cicli, 35 con la ricarica)
        asl zx_bv
        bne +
        jsr zx_rf
+
        .endm

zx0_unpack:
        lda #1
        sta zx_off
        lda #0
        sta zx_off+1
        lda #$80                ; solo la sentinella: il primo bit ricarica il byte
        sta zx_bv
_lit    jsr zx_el0              ; letterali: n = elias, n byte copiati
        lda zx_src
        sta zx_cp
        lda zx_src+1
        sta zx_cp+1
        jsr zx_copy
        lda zx_cp
        sta zx_src
        lda zx_cp+1
        sta zx_src+1
        #zx_bit
        bcs _new
        jsr zx_el0              ; copia dall'ultimo offset
        jsr zx_match
        #zx_bit
        bcc _lit
_new    lda #1                  ; nuovo offset: MSB = elias con i bit di valore invertiti; 256 = fine
        sta zx_len
        lda #0
        sta zx_len+1
_m      #zx_bit
        bcs _md
        #zx_bit
        lda #0
        rol
        eor #1
        lsr
        rol zx_len
        rol zx_len+1
        jmp _m
_md     lda zx_len+1
        beq +
        rts
+       lda zx_len              ; offset = MSB x 128 - (byte >> 1)
        lsr
        sta zx_off+1
        lda #0
        ror
        sta zx_off
        jsr zx_rb
        lsr                     ; C = bit 0 del byte = primo bit di controllo della lunghezza
        sta zx_t
        php
        lda zx_off
        sec
        sbc zx_t
        sta zx_off
        lda zx_off+1
        sbc #0
        sta zx_off+1
        lda #1                  ; lunghezza = elias + 1
        sta zx_len
        lda #0
        sta zx_len+1
        plp
        bcs +                   ; controllo 1: elias = 1
        jsr zx_elv              ; controllo 0: un bit di valore, poi il ciclo normale
+       inc zx_len
        bne +
        inc zx_len+1
+       jsr zx_match
        #zx_bit
        bcs _new
        jmp _lit

; copia zx_len byte da zx_dst - zx_off
zx_match:
        lda zx_dst
        sec
        sbc zx_off
        sta zx_cp
        lda zx_dst+1
        sbc zx_off+1
        sta zx_cp+1
; copia zx_len (>= 1) byte da zx_cp a zx_dst, avanzando entrambi (X = conteggio basso, zx_len+1 = blocchi da 256)
zx_copy:
        ldy #0
        ldx zx_len
        beq +
        inc zx_len+1
+
_c      lda (zx_cp),y           ; 21 cicli per byte
        sta (zx_dst),y
        iny
        bne +
        inc zx_cp+1
        inc zx_dst+1
+       dex
        bne _c
        dec zx_len+1
        bne _c
        tya                     ; avanza i puntatori della parte non ancora contata
        clc
        adc zx_cp
        sta zx_cp
        bcc +
        inc zx_cp+1
+       tya
        clc
        adc zx_dst
        sta zx_dst
        bcc +
        inc zx_dst+1
+       rts

; Elias gamma interlacciato (bit di valore diretti) -> zx_len
zx_el0: lda #1
        sta zx_len
        lda #0
        sta zx_len+1
zx_ell  #zx_bit
        bcs zx_elr
zx_elv  #zx_bit                 ; (ingresso dal secondo bit: lunghezza dopo un nuovo offset)
        rol zx_len
        rol zx_len+1
        jmp zx_ell
zx_elr  rts

; ricarica del byte dei bit (chiamata da zx_bit quando esce la sentinella): MSB in C, sentinella in fondo
zx_rf:  jsr zx_rb
        sec
        rol
        sta zx_bv
        rts

; un byte dal flusso -> A
zx_rb:  ldy #0
        lda (zx_src),y
        inc zx_src
        bne +
        inc zx_src+1
+       rts
