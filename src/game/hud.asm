; ===================================================================
;  hud.asm - fascia HUD fissa in basso (testo) + IRQ raster di split
;
;  Schermo: righe 0..19 = campo di gioco (scroll fine)
;           riga 20     = riga "regolo" (separatore, mostrata due volte: la prima e' vuota)
;           righe 21..23 = HUD (3 righe di testo, posizione fissa)
;  IRQ1 (linea 209): D011 -> yscroll 7 (la riga 20 viene ripresa a linea 215,
;                    cosi' le righe 21..23 cadono sempre a 223/231/239)
;  IRQ2 (linea 217): D016 -> xscroll 0, D021 -> nero
;  apply_frame (linea $fc) ripristina i registri dello scroll per il frame dopo.
; ===================================================================
HUD_ROW0   = SCR_H + 800        ; riga 20 nello schermo HUD
IRQ_L1     = 209
IRQ_L2     = 217

        .virtual $9780
hud_pend   .byte ?
irq_ph     .byte ?
bg_cur     .byte ?
hf_o       .byte ?
hf_n       .byte ?
bar_n      .byte ?
bar_c      .byte ?
hv         .word ?
sc_n       .word ?
sc_d       .word ?
sc_k       .byte ?
dbuf       .fill 5
hb         .fill 40
hc         .fill 40
ap_d018    .byte ?              ; ultimi registri del campo di gioco applicati da apply_frame:
ap_bg      .byte ?              ; l'IRQ di fine HUD li ripristina, cosi' un frame in ritardo del
ap_d016    .byte ?              ; ciclo principale non lascia lo schermo HUD su tutto il campo
ap_d011    .byte ?
ap_l1      .byte ?
hw_low     .byte ?              ; 1 = vita bassa (avviso attivo: "HP nnn/nnn" lampeggia)
        .endv

; ------------------------------------------------------------------ IRQ
; (21/11, TODO D15) KERNAL sempre escluso ($01 = MEMCFG = $35): i vettori della CPU sono nella RAM sotto il KERNAL. IRQ ->
; irq_entry, copia esatta dell'ingresso della ROM ($FF48: stesse istruzioni, stessi cicli, salto da ($0314)); NMI (RESTORE) ->
; nmi_stub. Anche $0314 resta su irq_h: con il KERNAL visibile (bar.asm, $01 = $32 per 8 letture) l'ingresso della ROM porta
; allo stesso posto, e l'uscita irq_exit sta in RAM.
irq_init:
        lda #<irq_h
        sta $0314
        lda #>irq_h
        sta $0315
        lda #<irq_entry
        sta $fffe
        lda #>irq_entry
        sta $ffff
        lda #<nmi_stub
        sta $fffa
        sta $0318
        lda #>nmi_stub
        sta $fffb
        sta $0319
        rts

; ingresso dell'IRQ (copia di $FF48-$FF5A della ROM, BRK compreso)
irq_entry:
        pha
        txa
        pha
        tya
        pha
        tsx
        lda $0104,x
        and #$10
        beq _irq
        jmp ($0316)
_irq    jmp ($0314)
        .cerror (>(irq_entry+11)) != (>(irq_entry+13)), "irq_entry: il beq non deve cambiare pagina (cicli come nella ROM)"
; uscita dell'IRQ (copia di $EA81-$EA86 della ROM)
irq_exit:
        pla
        tay
        pla
        tax
        pla
        rti

; accende l'IRQ a raster del gioco (fasi irq_ph: barra in alto, HUD, fine HUD), con il vettore su irq_h
irq_on:
        sei
        lda #0
        sta irq_ph
        lda #IRQ_L1
        sta $d012
        lda #$ff
        sta $d019
        lda #1
        sta $d01a
        cli
        rts

; spegne l'IRQ a raster (schermate della UI, disco): niente split, niente musica dal raster
irq_off:
        sei
        lda #0
        sta $d01a
        lda #$ff
        sta $d019
        rts

; IRQ a raster, una fase per riga (irq_ph): 0 = inizio dell'HUD (schermo SCR_H, 24 righe), 1 = HUD multicolore,
; 2 = riga 250, campo di gioco ripristinato (ap_*), 3 = barra in alto e sprite di gioco (bar.asm); esce da irq_exit
irq_h:
        lda #$ff
        sta $d019
        lda irq_ph
        beq _ph0
        cmp #3
        beq _top
        cmp #2
        beq _p2
        bne _p1
_ph0
.if TESTFZ
        inc $03f8               ; test: fotogrammi video (16 bit) contro giri del ciclo ($03fa)
        bne +
        inc $03f9
+
.endif
        lda #$17                ; yscroll 7, 24 righe, DEN
        sta $d011
        lda #$1a                ; schermo HUD (SCR_H = $8400), stesso charset
        sta $d018
        lda #IRQ_L2
        sta $d012
        inc irq_ph
        jmp irq_exit
_p1     lda #$10                ; MCM, 38 col, xscroll 0
        sta $d016
        lda #0
        sta $d021
        lda #250                ; dopo l'HUD: ripristino del campo di gioco
        sta $d012
        lda #2
        sta irq_ph
        jmp irq_exit

; riga 250 (fine HUD): ripristina i registri del campo di gioco dell'ultimo apply_frame.
; Se il ciclo principale sfora il frame, il frame dopo mostra comunque il campo di gioco
; (prima restava lo schermo HUD su tutto lo schermo: lampo a schermo intero).
_p2     lda ap_d018
        sta $d018
        lda ap_bg
        sta $d021
        lda ap_d016
        sta $d016
        lda ap_d011
        sta $d011
        lda ap_l1
        sta $d012
        lda #0
        sta irq_ph
        lda bar_on
        beq _ps
        jsr bar_regs
        lda #IRQ_BAR
        sta $d012
        lda #3
        sta irq_ph
        jsr sfx_update          ; effetti e musica: una volta per fotogramma, a tempo anche se il ciclo sfora
        jmp irq_exit
_ps     jsr spr_copy
        jsr sfx_update
        jmp irq_exit

_top    jsr spr_copy
        lda hy
        cmp #5
        bcc _t1
        lda #1
_t1     clc
        adc #209
        sta $d012
        lda #0
        sta irq_ph
        jmp irq_exit

; ------------------------------------------------------------------ primitive
p10l    .byte <10000, <1000, <100, <10, <1
p10h    .byte >10000, >1000, >100, >10, >1

; hv -> dbuf[0..4] (glifi, zeri iniziali = vuoto)
dec5:
        ldx #0
_dl     ldy #0
_ds     lda hv
        sec
        sbc p10l,x
        sta tmp0
        lda hv+1
        sbc p10h,x
        bcc _dd
        sta hv+1
        lda tmp0
        sta hv
        iny
        bne _ds
_dd     tya
        clc
        adc #G_0
        sta dbuf,x
        inx
        cpx #5
        bne _dl
        ldx #0
_z      lda dbuf,x
        cmp #G_0
        bne _zd
        lda #G_BLANK
        sta dbuf,x
        inx
        cpx #4
        bne _z
_zd     rts

; A = valore a 8 bit -> dbuf
dec5b:
        sta hv
        lda #0
        sta hv+1
        jmp dec5

; sc_n * sc_k / sc_d -> A (0..sc_k)
scale:
_r      lda sc_d+1
        beq _8
        lsr sc_d+1
        ror sc_d
        lsr sc_n+1
        ror sc_n
        jmp _r
_8      lda sc_d
        bne _nz
        inc sc_d
_nz     lda sc_n+1
        beq _go
        lda sc_k
        rts
_go     lda sc_n
        sta tmp7
        lda #0
        sta tmp5
        sta tmp0
        sta tmp1
        lda sc_k
        sta tmp6
        ldx #8
_ml     lsr tmp6
        bcc _ns
        clc
        lda tmp0
        adc tmp7
        sta tmp0
        lda tmp1
        adc tmp5
        sta tmp1
_ns     asl tmp7
        rol tmp5
        dex
        bne _ml
        lda #0
        sta tmp2
        ldx #16
_dv     asl tmp0
        rol tmp1
        rol tmp2
        bcs _sub
        lda tmp2
        cmp sc_d
        bcc _nx
_sub    lda tmp2
        sec
        sbc sc_d
        sta tmp2
        inc tmp0
_nx     dex
        bne _dv
        lda tmp1
        bne _max
        lda tmp0
        cmp sc_k
        bcc _ok
_max    lda sc_k
_ok     rts

; barra: A = pixel pieni, X = prima cella in hb, bar_n celle, bar_c colore
bar:
        sta tmp0
_b      lda tmp0
        cmp #8
        bcc _p
        lda #8
_p      sta tmp1
        lda tmp0
        sec
        sbc tmp1
        sta tmp0
        lda tmp1
        clc
        adc #G_BAR0
        sta hb,x
        lda bar_c
        ldy tmp1
        bne _cc
        lda #6                  ; cella vuota: binario blu scuro
_cc     sta hc,x
        inx
        dec bar_n
        bne _b
        rts

; azzera hb/hc[0..X-1] a vuoto/bianco
hb_clear:
_c      dex
        lda #G_BLANK
        sta hb,x
        lda #1
        sta hc,x
        cpx #0
        bne _c
        rts

; copia hb/hc nei due schermi e nella color ram: A = offset da riga 20, X = lunghezza
hflush:
        sta hf_o
        stx hf_n
        lda #<HUD_ROW0
        clc
        adc hf_o
        sta ptr0
        lda #>HUD_ROW0
        adc #0
        sta ptr0+1
        lda #<(COLRAM + 800)
        clc
        adc hf_o
        sta ptr2
        lda #>(COLRAM + 800)
        adc #0
        sta ptr2+1
        ldy #0
_l      lda hb,y
        sta (ptr0),y
        lda hc,y
        sta (ptr2),y
        iny
        cpy hf_n
        bne _l
        rts

; copia le cifre di dbuf in hb da X saltando gli spazi iniziali; X = colonna successiva
hput:
        ldy #0
_s      lda dbuf,y
        cmp #G_BLANK
        bne _c
        iny
        cpy #4
        bne _s
_c      lda dbuf,y
        sta hb,x
        inx
        iny
        cpy #5
        bne _c
        rts

; come hput, ma da 10000 in su in migliaia senza decimali ("10K", "65K": 16 bit, 07/11 sera): dbuf = cifre di dec5,
; la prima e' la decina di migliaia (G_BLANK se 0); solo la riga XP la usa
hput_k:
        lda dbuf
        cmp #G_0 + 1
        bcc hput
        cmp #G_BLANK
        beq hput
        sta hb,x
        lda dbuf+1
        sta hb+1,x
        lda #G_K
        sta hb+2,x
        inx
        inx
        inx
        rts

; ------------------------------------------------------------------ pannelli
; sincrono: ridisegna tutta la fascia (dopo UI / cambio livello)
hud_full:
        ldx #40
        jsr hb_clear
        lda #0
        sta tmp3
_r      ldx tmp3
        lda rowoff,x
        ldx #40
        jsr hflush
        inc tmp3
        lda tmp3
        cmp #4
        bne _r
        lda #$0f
        sta hud_pend
_s      jsr hud_step
        lda hud_pend
        bne _s
        rts

rowoff  .byte 40, 80, 120, 160

; chiamato ogni frame: ridisegna un pannello alla volta
hud_step:
        lda hud_dirty
        beq _go
        lda #0
        sta hud_dirty
        lda #$0f
        sta hud_pend
_go     lda hud_pend
        beq _x
        and #1
        beq _n1
        dec hud_pend
        jmp hud_p0
_n1     lda hud_pend
        and #2
        beq _n2
        lda hud_pend
        and #$fd
        sta hud_pend
        jmp hud_p1
_n2     lda hud_pend
        and #4
        beq _n3
        lda hud_pend
        and #$fb
        sta hud_pend
        jmp hud_p2
_n3     lda hud_pend
        and #$f7
        sta hud_pend
        jmp hud_p3
_x      rts

; ---- riga 21: HP  nnn/nnn + barra rossa (8 celle)
hud_p0:
        ldx #26
        jsr hb_clear
        lda #G_H
        sta hb+1
        lda #G_P
        sta hb+2
        lda #2
        sta hc+1
        sta hc+2
        lda c_hp
        sta hv
        lda c_hp+1
        sta hv+1
        jsr dec5
        ldx #4
        jsr hput
        lda #G_SLASH
        sta hb,x
        inx
        stx tmp4
        lda hpmax
        sta hv
        lda hpmax+1
        sta hv+1
        jsr dec5
        ldx tmp4
        jsr hput
        lda c_hp
        sta sc_n
        lda c_hp+1
        sta sc_n+1
        lda hpmax
        sta sc_d
        lda hpmax+1
        sta sc_d+1
        lda #80
        sta sc_k
        jsr scale
        cmp #0
        bne _px
        lda c_hp
        ora c_hp+1
        beq _px
        lda #1
_px     ldx #10
        stx bar_n
        ldx #2
        stx bar_c
        ldx #16
        jsr bar
        lda #40
        ldx #26
        jmp hflush

; ------------------------------------------------------------------ avvisi (chiamato ogni 16 fotogrammi)
; Vita bassa (c_hp <= hpmax / 4): le celle "HP nnn/nnn" (riga 21, colonne 1..11) alternano rosso e giallo;
; al passaggio sotto la soglia un suono (SFX_LOWHP), una volta. Oggetto indossato che si sta per rompere
; (durabilita' <= WARN_PC % del massimo): icona rossa/gialla lampeggiante in riga 21, colonne 29..31.
HW_COL   = COLRAM + 840             ; color RAM della riga 21
hud_warn:
        lda hpmax+1             ; tmp0/tmp1 = hpmax / 4
        lsr
        sta tmp1
        lda hpmax
        ror
        lsr tmp1
        ror
        sta tmp0                ; vita bassa se hpmax / 4 >= c_hp (11/11: A e' gia' tmp0)
        cmp c_hp
        lda tmp1
        sbc c_hp+1
        bcc _ok
        lda hw_low
        bne _bl
        lda #1
        sta hw_low
        lda #SFX_LOWHP
        jsr sfx_play
_bl     lda frame               ; lampeggio: bit 4 di frame (la routine gira ogni 16 fotogrammi)
        and #16
        beq +
        lda #7
        .byte $2c               ; (bit abs: salta lda #2)
+       lda #2
        ldx #10
_c      sta HW_COL+1,x
        dex
        bpl _c
        jmp hw_icons
_ok     lda hw_low
        beq hw_icons
        lda #0                  ; fine della vita bassa: si ridisegna la riga HP (colori normali)
        sta hw_low
        lda hud_pend
        ora #1
        sta hud_pend
; icone degli oggetti che si stanno per rompere -> riga 21, colonne 29..31 (schermo HUD e color RAM)
hw_icons:
        ldx #2
_i      lda #G_BLANK
        sta hb,x
        lda c_eqm,x
        beq _n                  ; non si usura (o slot vuoto)
        lda #0                  ; durabilita' x WARN_MUL <= massimo (WARN_MUL = 100 / percentuale)
        ldy #WARN_MUL
_m      clc
        adc c_eqd,x
        bcs _n                  ; oltre 255: sopra la soglia
        dey
        bne _m
        cmp c_eqm,x
        beq _w
        bcs _n
_w      lda hw_gl,x
        sta hb,x
        lda c_eqd,x             ; rotta (arma a 0, 07/11): icona fissa in rosso; si sta rompendo: lampeggia
        bne _n
        lda #2
        bne _sc
_n      lda frame
        and #16
        beq +
        lda #7
        .byte $2c
+       lda #2
_sc     sta hc,x
        dex
        bpl _i
        lda #69
        ldx #3
        jmp hflush
hw_gl   .byte G_WSWORD, G_WARMOR, G_WSHIELD

; (12/11, committente) riga 21, colonne 34..38 (hb+6..+10 del riquadro da 28): "C3 L4" = capitolo e piano del
; capitolo (nel villaggio solo "C3"). Internamente i piani restano 1..MAXLEVEL (lv_grp).
hud_cl:
        lda cur_level
        bne _d
        lda c_chap
        ldx #0
        beq _w
_d      jsr lv_grp              ; A = capitolo, X = indice
        inx
_w      stx tmp3
        clc
        adc #G_0
        sta hb+7
        lda HG_C
        sta hb+6
        ldx tmp3
        beq _r
        lda HG_L
        sta hb+9
        txa
        clc
        adc #G_0
        sta hb+10
_r      rts
        .enc "hud"
HG_C    .byte "c"               ; glifi HUD di "c" e "l" (letti come costanti sotto)
HG_L    .byte "l"
        .enc "none"

; ---- riga 22: XP cur/need + barra gialla (11 celle)
hud_p1:
        ldx #26
        jsr hb_clear
        lda #G_X
        sta hb+1
        lda #G_P
        sta hb+2
        lda #7
        sta hc+1
        sta hc+2
        lda c_lvl
        cmp #PL_MAXLVL
        bcc _lv
        lda #G_M
        sta hb+4
        lda #G_A
        sta hb+5
        lda #G_X
        sta hb+6
        lda #80
        jmp _bar
_lv     tax                     ; xp_n*[livello - 1]: esperienza per il livello successivo (24 bit)
        dex
        stx tmp7
        lda c_xp                ; mostrati i 16 bit bassi (nel dungeon l'esperienza sta sotto 65536)
        sta hv
        lda c_xp+1
        sta hv+1
        jsr dec5
        ldx #4
        jsr hput_k
        lda #G_SLASH
        sta hb,x
        inx
        stx tmp4
        ldx tmp7
        lda xp_n0,x
        sta hv
        lda xp_n1,x
        sta hv+1
        jsr dec5
        ldx tmp4
        jsr hput_k
        ; barra: (xp - soglia precedente) / (soglia - precedente), differenze a 16 bit
        lda #0
        sta tmp5
        sta tmp6
        ldx tmp7
        beq _np
        lda xp_n0-1,x
        sta tmp5
        lda xp_n1-1,x
        sta tmp6
_np     lda c_xp
        sec
        sbc tmp5
        sta sc_n
        lda c_xp+1
        sbc tmp6
        sta sc_n+1
        lda xp_n0,x
        sec
        sbc tmp5
        sta sc_d
        lda xp_n1,x
        sbc tmp6
        sta sc_d+1
        lda #80
        sta sc_k
        jsr scale
_bar    ldx #10
        stx bar_n
        ldx #7
        stx bar_c
        ldx #16
        jsr bar
        lda #80
        ldx #26
        jmp hflush

; ---- riga regolo + riga 23: LV nn  H J K L  U O  chiave nn
hud_p2:
        ldx #40
        jsr hb_clear
        lda COLRAM+760          ; colore della mappa (la riga e' mostrata anche come riga di mappa)
        sta tmp4
        ldx #39
_r      lda #G_RULE
        sta hb,x
        lda tmp4
        sta hc,x
        dex
        bpl _r
        lda #0
        ldx #40
        jsr hflush
        ldx #26
        jsr hb_clear
        lda #G_L
        sta hb+1
        lda #G_V
        sta hb+2
        lda c_lvl
        jsr dec5b
        lda dbuf+3
        sta hb+4
        lda dbuf+4
        sta hb+5
        jsr pts_avail           ; (11/11) punti statistica da spendere: freccia verde in su (G_LVUP) accanto al livello; glifo da confermare, TODO A1
        beq +
        lda #G_LVUP
        sta hb+6
        lda #5                  ; verde (colore < 8: carattere hires)
        sta hc+6
+       lda #G_KEY              ; chiavi: icona + numero (0..10)
        sta hb+22
        lda #7
        sta hc+22
        lda c_keys
        jsr dec5b
        ldx #23
        jsr hput
        ldx #4                  ; U (Rage) e O (Frenzy): attiva = giallo, pronta = bianco, ricarica = ciano;
_bf     lda c_lvl               ; abilita' non ancora disponibile: niente lettera (07/11). Solo colori < 8: con un
        cmp sk_req,x            ; colore >= 8 il carattere diventa multicolore e la lettera non si legge
        bcc _bn
        lda bf_g-4,x
        sta hb+14,x
        lda bf_t-4,x
        tay
        lda tmr,y
        ora tmr+1,y
        beq +
        lda #7
        bne _bc
+       lda sk_cdl,x
        ora sk_cdh,x
        beq +
        lda #3
        bne _bc
+       lda #1
_bc     sta hc+14,x
_bn     inx
        cpx #6
        bne _bf
        lda sk_t                ; nome dell'abilita' al posto di H J K L (SK_SHOW frame)
        beq _fk
        ldx hud_nm
        lda sk_off,x
        tax
        ldy #0
_nm     lda sk_nm,x
        sta hb+8,y              ; (12/11) nome dalla colonna 8 (le lettere sono a 9-15)
        lda #7
        sta hc+8,y
        inx
        iny
        cpy #10
        bne _nm
        lda #120
        ldx #26
        jmp hflush
_fk     ldy #0
_s      sty tmp3
        tya
        asl
        clc
        adc #7
        adc #2              ; (12/11, committente: lettere un po' piu' a destra) colonna 9, 11, 13, 15
        tax
        lda c_lvl               ; abilita' non ancora disponibile: niente lettera
        cmp sk_req,y
        bcc _nx
        lda sk_g,y
        sta hb,x
        cpy c_skill
        bne _w
        lda #7
        bne _c
_w      lda #1
_c      sta hc,x
_nx     ldy tmp3
        iny
        cpy #4
        bne _s
        lda #120
        ldx #26
        jmp hflush

SK_SHOW = 100                   ; 2 secondi
sk_off  .byte 0, 10, 20, 30, 40
bf_g    .byte G_U, G_O
sk_g    .byte G_H, G_J, G_K, G_L
bf_t    .byte T_RAGE, T_FZ
sk_nm
        .enc "hud"              ; testo normale: ogni lettera diventa il suo glifo HUD
        .text "slash     "
        .text "whirlwind "
        .text "battle cry"
        .text "smash     "
        .text "broken    "
        .enc "none"

; ---- cintura: 5 posti (4 pozioni, una per posto, + pergamena), riquadro in basso a destra
; righe 21..23, colonne 28..38 ; posto j in colonna 29+2j. Riga 22: icone; riga 23: un trattino
; sotto ogni posto (la posizione, al posto dei numeri dei tasti 1..5)
hud_p3:
        ldx #11                 ; riga 21: vuota, poi a destra capitolo e piano del capitolo
        jsr hb_clear
        jsr hud_cl
        lda #68
        ldx #11
        jsr hflush
        jsr hw_icons            ; avvisi degli oggetti (colonne 29..31) subito, senza aspettare hud_warn
        ldx #11                 ; riga 22: icone
        jsr hb_clear
        ldy #0
_i      tya
        asl
        tax
        lda c_beltt,y
        beq _n
        sty tmp3
        tay
        lda itfl,y              ; colore della pozione; in ricarica (tutte bloccate): blu
        ldy tmr+T_POT
        bne _pb
        ldy tmr+T_POT+1
        beq _pc
_pb     lda #6
_pc     ldy tmp3
        sta hc+1,x
        lda #G_POT
        sta hb+1,x
_n      iny
        cpy #4
        bne _i
        jsr scr_find            ; pergamene: icona se ce n'e' almeno una (quantita' nell'inventario)
        bcs _ns
        lda #1
        sta hc+9
        lda #G_SCR
        sta hb+9
_ns     lda #108
        ldx #11
        jsr hflush
        ldx #11                 ; riga 23: trattini
        jsr hb_clear
        ldx #0
_d      lda #G_DOT
        sta hb+1,x
        lda #6                  ; blu (carattere hires)
        sta hc+1,x
        inx
        inx
        cpx #10
        bne _d
        lda #148
        ldx #11
        jmp hflush
