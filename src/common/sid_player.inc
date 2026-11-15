; ===================================================================
;  sid_player.inc - player SID a 3 voci, unico per tutto il progetto (loader, gioco, jukebox).
;  Brani nel formato di tools/build/gen_music.py (a pattern, rilocabili: offset dall'inizio del brano).
;  Per voce: forma d'onda, ADSR, impulso con PWM a rimbalzo, vibrato triangolare, arpeggio (4 note a rotazione),
;  glissato, stacco (gate spento gcut fotogrammi prima della fine della nota), seconda forma d'onda + secondo ADSR
;  per le note con bit 7 (rullante / eco). Globale: filtro con sweep del cutoff a rimbalzo.
;  Nessuna pagina zero (letture con codice automodificante), nessun sei/cli.
;
;  Da definire prima dell'include:
;    SP_VARS        indirizzo delle variabili (SP_VSIZE byte, .virtual)
;    SP_V0/V1/V2    scostamento nel SID delle voci 0, 1, 2 del brano (0, 7, 14)
;  API:
;    sp_start       brano all'indirizzo sp_bl/sp_bh (da impostare prima): strumenti, filtro, voci da capo
;    sp_play        una volta per fotogramma (se sp_on = 0 non fa nulla)
;    sp_stop        voci spente, sp_on = 0
;    sp_release     gate spento su tutte le voci con rilascio A (0-15): dissolvenza naturale; il brano si ferma
;    sp_save        posizione del brano -> sp_sv (per riprenderlo con sp_resume dopo un altro brano)
;    sp_resume      come sp_start ma riparte dalla posizione salvata
;  sp_once = 1: il brano si ferma (sp_on = 0) alla fine invece di ricominciare.
;  sp_mute,x <> 0: la voce X non scrive nel SID (es. voce condivisa con gli effetti sonori); $80 = libera dalla
;  prossima nota. Il filtro esclude la voce 1 mentre sp_mute+1 <> 0.
; ===================================================================
SP_NI   = 17                    ; parametri di strumento (x 3 voci) nell'intestazione del brano

        .virtual SP_VARS
sp_bl   .byte ?                 ; indirizzo del brano
sp_bh   .byte ?
sp_on   .byte ?
sp_once .byte ?
sp_mute .fill 3
sp_spd  .byte ?
sp_fmin .byte ?
sp_fmax .byte ?
sp_fres .byte ?
sp_fmode .byte ?
sp_fc   .byte ?                 ; fotogrammi residui del tick corrente
sp_cut  .byte ?
sp_cutd .byte ?
sp_ins                          ; strumenti (copiati dal brano): parametro p della voce v in sp_ins + 3p + v
ins_wave  .fill 3
ins_wave2 .fill 3
ins_ad    .fill 3
ins_sr    .fill 3
ins_ad2   .fill 3
ins_sr2   .fill 3
ins_pwlo  .fill 3
ins_pwhi  .fill 3
ins_pwd   .fill 3
ins_pwmin .fill 3
ins_pwmax .fill 3
ins_vd    .fill 3
ins_vw    .fill 3
ins_arp   .fill 3
ins_slo   .fill 3
ins_shi   .fill 3
ins_gcut  .fill 3
sp_pos                          ; posizione (salvata da sp_save): 10 x 3 byte
sp_pl   .fill 3                 ; puntatore nel pattern
sp_ph   .fill 3
sp_ol   .fill 3                 ; puntatore nell'ordine
sp_oh   .fill 3
sp_tr   .fill 3                 ; trasposizione
sp_dur  .fill 3                 ; durata corrente (tick)
sp_rem  .fill 3                 ; tick residui della nota
sp_rpt  .fill 3                 ; ripetizioni residue del pattern
sp_psl  .fill 3                 ; inizio del pattern corrente (ripetizioni)
sp_psh  .fill 3
sp_o0l  .fill 3                 ; inizio dell'ordine
sp_o0h  .fill 3
sp_note .fill 3
sp_base .fill 3
sp_fl   .fill 3
sp_fh   .fill 3
sp_vc   .fill 3
sp_vd   .fill 3
sp_ai   .fill 3
sp_pwl  .fill 3
sp_pwh  .fill 3
sp_pwdir .fill 3
sp_gate .fill 3
sp_t    .byte ?
sp_tlo  .word ?                 ; tabelle degli offset dei pattern (bassi, alti)
sp_thi  .word ?
sp_sv   .fill 3*10              ; posizione salvata
SP_VEND
        .endv
SP_VSIZE = SP_VEND - SP_VARS

sp_sid  .byte SP_V0, SP_V1, SP_V2
sp_dtab .byte 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 14, 16, 24, 32, 48
sp_arp  .byte 0, 0, 0, 0,  0, 7, 12, 7,  0, 3, 7, 12,  0, 4, 7, 12
        .include "sid_freq.inc"  ; sp_flo / sp_fhi: indice 0 = pausa, 1 = C0 ... (tools/build/gen_music.py)

; ---------------------------------------------------------------- avvio
sp_start:
        lda sp_bl               ; tabella dei bassi degli offset dei pattern: brano + 65
        clc
        adc #65
        sta sp_tlo
        lda sp_bh
        adc #0
        sta sp_tlo+1
        jsr sp_hdr
        ldx #2
_v      lda sp_o0l,x
        sta sp_ol,x
        lda sp_o0h,x
        sta sp_oh,x
        lda #<sp_end            ; il primo evento legge subito l'ordine
        sta sp_pl,x
        lda #>sp_end
        sta sp_ph,x
        lda #0
        sta sp_tr,x
        sta sp_rpt,x
        lda #1
        sta sp_rem,x
        sta sp_dur,x
        dex
        bpl _v
        lda #1
        sta sp_fc
        sta sp_on
        rts

; intestazione: velocita', filtro, strumenti, inizio degli ordini, stato delle voci; SID pronto
sp_hdr:
        lda sp_bl
        sta _r+1
        lda sp_bh
        sta _r+2
        ldy #0
        jsr _r
        sta sp_spd
        jsr _r
        sta sp_cut
        jsr _r
        sta sp_fmin
        jsr _r
        sta sp_fmax
        jsr _r
        sta sp_cutd
        jsr _r
        sta sp_fres
        jsr _r
        sta sp_fmode
        ldx #0
_i      jsr _r
        sta sp_ins,x
        inx
        cpx #3*SP_NI
        bne _i
        ldx #0                  ; offset degli ordini -> indirizzi
_o      jsr _r
        clc
        adc sp_bl
        sta sp_o0l,x
        jsr _r
        adc sp_bh
        sta sp_o0h,x
        inx
        cpx #3
        bne _o
        jsr _r                  ; numero di pattern: tabella degli alti subito dopo i bassi
        clc
        adc sp_tlo
        sta sp_thi
        lda sp_tlo+1
        adc #0
        sta sp_thi+1
        ldx #2
_v      lda #0
        sta sp_note,x
        sta sp_vc,x
        sta sp_vd,x
        sta sp_ai,x
        lda ins_pwlo,x
        sta sp_pwl,x
        lda ins_pwhi,x
        sta sp_pwh,x
        lda ins_pwd,x
        sta sp_pwdir,x
        lda ins_wave,x
        and #$fe
        sta sp_gate,x
        lda sp_mute,x
        bne +
        ldy sp_sid,x
        lda #0
        sta $d404,y
        sta $d405,y
        sta $d406,y
+       dex
        bpl _v
        lda sp_fmode
        sta $d418
        rts
_r      lda $ffff,y
        iny
        rts

.weak
SP_RESUME = 1                   ; 0 = senza sp_resume e sp_release (START e LORE, src/common/boot.asm)
.endweak
.if SP_RESUME
; ripresa dalla posizione salvata (stesso brano a sp_bl/sp_bh)
sp_resume:
        jsr sp_start
        ldx #3*10-1
_c      lda sp_sv,x
        sta sp_pos,x
        dex
        bpl _c
        ldx #2                  ; la nota interrotta e' persa: si riparte dalla successiva
_n      lda #1
        sta sp_rem,x
        dex
        bpl _n
        rts
.endif

.if SP_RESUME
sp_save:
        ldx #3*10-1
_c      lda sp_pos,x
        sta sp_sv,x
        dex
        bpl _c
        rts
.endif

sp_stop:
        lda #0
        sta sp_on
        ldx #2
_v      lda sp_mute,x
        bne +
        ldy sp_sid,x
        lda #0
        sta $d404,y
+       dex
        bpl _v
        rts

.if SP_RESUME
; A = rilascio (0-15): gate spento e rilascio impostato; il brano si ferma (le note sfumano da sole)
sp_release:
        sta sp_t
        lda #0
        sta sp_on
        ldx #2
_v      lda sp_mute,x
        bne +
        ldy sp_sid,x
        lda ins_sr,x
        and #$f0
        ora sp_t
        sta $d406,y
        lda sp_gate,x
        and #$fe
        sta $d404,y
+       dex
        bpl _v
        rts
.endif

; ---------------------------------------------------------------- un fotogramma
sp_play:
        lda sp_on
        bne +
        rts
+       dec sp_fc
        bne _fx
        lda sp_spd
        sta sp_fc
        ldx #2
_t      dec sp_rem,x
        bne _nn
        jsr sp_next
        lda sp_on               ; (fine del brano in modo sp_once)
        bne _nn
        rts
_nn     dex
        bpl _t
_fx     ldx #2
_e      jsr sp_fxv
        dex
        bpl _e
        lda sp_cut              ; filtro: sweep del cutoff con rimbalzo
        clc
        adc sp_cutd
        sta sp_cut
        cmp sp_fmin
        bcc _fl
        cmp sp_fmax
        bcc _fo
_fl     lda sp_cutd
        eor #$ff
        clc
        adc #1
        sta sp_cutd
_fo     lda sp_cut
        sta $d416
        lda sp_fres
        ldx sp_mute+1           ; voce condivisa con gli effetti: fuori dal filtro
        beq +
        and #($ff ^ (1 << (SP_V1 / 7)))
+       sta $d417
        rts

; ---- letture con puntatore della voce X (pattern / ordine), con incremento
sp_rdp: lda sp_pl,x
        sta _a+1
        lda sp_ph,x
        sta _a+2
_a      lda $ffff
        inc sp_pl,x
        bne +
        inc sp_ph,x
+       rts
sp_rdo: lda sp_ol,x
        sta _a+1
        lda sp_oh,x
        sta _a+2
_a      lda $ffff
        inc sp_ol,x
        bne +
        inc sp_oh,x
+       rts
sp_end  .byte $ff               ; pattern vuoto (avvio)

; prossimo evento della voce X
sp_next:
_rd     jsr sp_rdp
        cmp #$ff
        beq _pend
        cmp #$e0
        bcs +
        jmp _note
+       and #$0f                ; nuova durata
        tay
        lda sp_dtab,y
        sta sp_dur,x
        jmp _rd
_pend   lda sp_rpt,x            ; fine pattern: ripetizione o ordine
        beq _ord
        dec sp_rpt,x
        lda sp_psl,x
        sta sp_pl,x
        lda sp_psh,x
        sta sp_ph,x
        jmp _rd
_ord    jsr sp_rdo
        cmp #$80
        bcs _cod
        tay                     ; pattern Y
        lda sp_tlo
        sta _plo+1
        lda sp_tlo+1
        sta _plo+2
        lda sp_thi
        sta _phi+1
        lda sp_thi+1
        sta _phi+2
_plo    lda $ffff,y
        clc
        adc sp_bl
        sta sp_pl,x
        sta sp_psl,x
_phi    lda $ffff,y
        adc sp_bh
        sta sp_ph,x
        sta sp_psh,x
        jmp _rd
_cod    cmp #$ff
        beq _loop
        cmp #$c0
        bcs _rep
        sbc #$9f                ; (C = 0: -$a0)
        sta sp_tr,x
        jmp _ord
_rep    sbc #$c0                ; (C = 1) ripetizioni in piu'
        sta sp_rpt,x
        jmp _ord
_loop   lda sp_once
        beq +
        jmp sp_stop             ; fine del brano (modo singolo)
+       lda sp_o0l,x
        sta sp_ol,x
        lda sp_o0h,x
        sta sp_oh,x
        lda #0
        sta sp_tr,x
        jmp _ord
_note   sta sp_note,x
        lda sp_dur,x
        sta sp_rem,x
        lda sp_mute,x           ; voce libera dagli effetti alla nota successiva
        cmp #$80
        bne +
        lda #0
        sta sp_mute,x
+       lda sp_note,x
        beq _rest
        and #$7f
        clc
        adc sp_tr,x
        sta sp_base,x
        tay
        lda sp_flo,y
        sta sp_fl,x
        lda sp_fhi,y
        sta sp_fh,x
        lda #0
        sta sp_vc,x
        sta sp_vd,x
        sta sp_ai,x
        lda sp_note,x
        bmi _w2
        lda ins_wave,x
        sta sp_gate,x
        lda ins_ad,x
        ldy ins_sr,x
        jmp _adsr
_w2     lda ins_wave2,x
        sta sp_gate,x
        lda ins_ad2,x
        ldy ins_sr2,x
_adsr   sta sp_t
        lda sp_mute,x
        bne _r
        tya
        ldy sp_sid,x
        sta $d406,y
        lda sp_t
        sta $d405,y
        lda sp_gate,x
        and #$fe                ; gate spento un attimo (riattacco)
        sta $d404,y
_r      lda sp_gate,x
        ora #1
        sta sp_gate,x
        rts
_rest   lda sp_gate,x
        and #$fe
        sta sp_gate,x
        rts

; effetti della voce X e scrittura dei registri
sp_fxv:
        lda sp_note,x
        bne +
        jmp _po
+       lda sp_rem,x            ; stacco: ultimo tick della nota, gcut fotogrammi dalla fine
        cmp #1
        bne +
        lda ins_gcut,x          ; bit 7 = "hard restart": anche AD/SR a 0 (evita il ritardo dell'attacco
        and #$7f                ; della nota seguente, bug dell'ADSR del SID con rilasci lenti)
        cmp sp_fc
        bne +
        lda sp_gate,x
        and #$fe
        sta sp_gate,x
        lda ins_gcut,x
        bpl +
        lda sp_mute,x
        bne +
        ldy sp_sid,x
        lda #0
        sta $d405,y
        sta $d406,y
+       lda ins_arp,x           ; arpeggio: nota di base + sp_arp[arp][i]
        beq _noarp
        asl
        asl
        adc sp_ai,x
        tay
        lda sp_arp,y
        clc
        adc sp_base,x
        tay
        lda sp_flo,y
        sta sp_fl,x
        lda sp_fhi,y
        sta sp_fh,x
        lda sp_ai,x
        clc
        adc #1
        and #3
        sta sp_ai,x
_noarp  lda ins_slo,x           ; glissato: frequenza += delta (16 bit con segno)
        clc
        adc sp_fl,x
        sta sp_fl,x
        lda ins_shi,x
        adc sp_fh,x
        sta sp_fh,x
        lda ins_vd,x            ; vibrato: +vd per vw fotogrammi, poi -vd per vw (onda triangolare)
        beq _nv
        inc sp_vc,x
        lda sp_vc,x
        cmp ins_vw,x
        bcc +
        lda #0
        sta sp_vc,x
        lda sp_vd,x
        eor #1
        sta sp_vd,x
+       lda sp_vd,x
        bne _down
        lda ins_vd,x
        clc
        adc sp_fl,x
        sta sp_fl,x
        bcc _nv
        inc sp_fh,x
        bcs _nv
_down   lda sp_fl,x
        sec
        sbc ins_vd,x
        sta sp_fl,x
        bcs _nv
        dec sp_fh,x
_nv     lda sp_pwl,x            ; PWM con rimbalzo fra pwmin e pwmax (byte alto)
        clc
        adc sp_pwdir,x
        sta sp_pwl,x
        lda sp_pwdir,x
        bmi _pm
        bcc _pw
        inc sp_pwh,x
        bcs _pw
_pm     bcs _pw
        dec sp_pwh,x
_pw     lda sp_pwh,x
        cmp ins_pwmin,x
        bcc _pb
        cmp ins_pwmax,x
        bcc _po
_pb     lda sp_pwdir,x
        eor #$ff
        clc
        adc #1
        sta sp_pwdir,x
_po     lda sp_mute,x
        bne _r
        ldy sp_sid,x            ; registri
        lda sp_fl,x
        sta $d400,y
        lda sp_fh,x
        sta $d401,y
        lda sp_pwl,x
        sta $d402,y
        lda sp_pwh,x
        and #$0f
        sta $d403,y
        lda sp_gate,x
        sta $d404,y
_r      rts
