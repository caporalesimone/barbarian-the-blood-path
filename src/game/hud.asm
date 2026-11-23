;===================================================================
;  hud.asm - fascia HUD fissa in basso (testo) + IRQ raster di split
;
;  Schermo: campo di gioco fino alla riga raster 207 (scroll fine), 208-214 nere
;           riga 20     = (23/11) riga del bersaglio: nome e vita del mostro, o etichetta del luogo / messaggio delle quest,
;                         o il nome dell'abilita' appena scelta (bt_row; prima: 8 sprite in alto, nascondevano il PG)
;           riga 21     = vuota (spazio nero), regolo nell'ultima linea di pixel
;           righe 22-23 = barre della vita e dell'esperienza, cintura (2 file da 4 + pergamena), abilita' (2 file da 3)
;  IRQ1 (linea 207, 206 con hy = 7): ECM (+ scroll 7) -> nero dalla 208
;  IRQ2 (linea 213): scroll 7 + ECM, schermo HUD, D021 nero; alla 215 via l'ECM, D016 -> MCM, xscroll 0
;  apply_frame (linea $fc) ripristina i registri dello scroll per il frame dopo.
; ===================================================================
HUD_ROW0   = SCR_H + 800        ; riga 20 nello schermo HUD
BTR_SCR     = SCR_H + 800        ; (23/11) riga 20: riga del bersaglio (bt_row)
BT_COLR    = COLRAM + 800
IRQ_L1     = 207                ; (23/11) era 209 (secondo hy): fine del campo di gioco fissa alla 207, HUD dalla 215 (riga 20)
IRQ_L2     = 213                ; era 217 (2 righe prima della 215: margine anche con un IRQ in ritardo, vc64web)

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
ap_ph      .byte ?              ; (23/11) fase dell'IRQ di inizio HUD: 0, o 3 con hy = 7 (IRQ nella 206)
ap_p0      .byte ?              ; (23/11) valore di $D011 della fase 0 ($57, o scroll hy + ECM con hy = 0)
hw_low     .byte ?              ; 1 = vita bassa (avviso attivo: le celle piene della barra HP lampeggiano)
bt_hold    .byte ?              ; (23/11) fotogrammi di testo tenuto dopo lo spegnimento della barra (bt_row)
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

; (21/11 sera) il beq di irq_entry e il suo bersaglio nella stessa pagina (cicli come nella ROM): 6 byte di riempimento se serve
        .if (>(*+11)) != (>(*+13)) || (>(*+13)) != (>(*+16))
        .fill 6, $ea
        .endif
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
; 2 = riga 250, campo di gioco ripristinato (ap_*); esce da irq_exit. (23/11) Niente piu' fase 3 (barra di sprite in alto)
irq_h:
        lda #$ff
        sta $d019
        lda irq_ph
        beq _ph0
        cmp #2
        beq _p2
        cmp #3
        beq _ph3
        bne _p1
; (23/11) fine del campo di gioco alla riga 207 per ogni hy, senza scritture a tempo critiche:
; fase 0 (IRQ nella 207): ECM (con l'MCM del campo = modo illegale, pixel neri) e scroll 7 all'inizio della 208; dalla 208
;   alla 214 nessuna riga e' "7": nessuna riga cattiva nuova fino all'HUD. Se la scrittura arriva qualche ciclo prima o dopo,
;   solo la parte di una riga (207 o 208) cambia colore. La riga 20 del campo (riga cattiva a 208 + hy) puo' partire, ma nera:
;   la sua memoria colore (riga 20) e' quella della riga del bersaglio. Con hy = 0 la 208 e' quella riga cattiva: in vc64web
;   cambiare lo scroll li' (anche prima del ciclo 12) spostava l'HUD di una riga (provato): con hy = 0 solo l'ECM qui, lo
;   scroll 7 nella fase 1. Con hy = 7 la 207 e' una riga cattiva del campo (l'IRQ arriverebbe a meta' della 208): IRQ nella
;   206 (fase 3), attesa della 207 e del fermo della CPU.
; fase 1 (IRQ nella 213): scroll 7 + ECM (la 213 e la 214 non sono mai righe "7"), schermo dell'HUD e sfondo nero; poi alla
;   215 (riga cattiva dell'HUD: VC 800, la riga 20 del campo non arriva a RC 7) via l'ECM e MCM dell'HUD: la 215 e' la riga
;   vuota in cima ai glifi, va bene in qualunque ciclo.
_ph3
-       lda $d012               ; aspetta la 207 (o oltre: mai un fotogramma intero); poi una lettura nei cicli 12-54 della 207
        cmp #IRQ_L1             ; (riga cattiva) ferma la CPU fino al 55
        bcc -
        nop
        nop
        nop
        nop
        nop
        nop
_ph0    lda ap_p0               ; all'inizio della 208: ECM (nero dalla 208 alla 214) e scroll 7 (con hy = 0 solo ECM)
        sta $d011
.if TESTFZ
        inc $03f8               ; test: fotogrammi video (16 bit) contro giri del ciclo ($03fa)
        bne +
        inc $03f9
+
.endif
        lda #IRQ_L2
        sta $d012
        lda #1
        sta irq_ph
        jmp irq_exit
_p1     lda #$57                ; scroll 7 + ECM (gia' scritti nella fase 0 se hy <> 0)
        sta $d011
        lda #$1a                ; schermo HUD (SCR_H = $8400), stesso charset
        sta $d018
        lda #0
        sta $d021
-       lda $d012
        cmp #IRQ_L2+2
        bcc -
        lda #$17                ; 215: via l'ECM
        sta $d011
        lda #$10                ; MCM, 38 col, xscroll 0
        sta $d016
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
        lda ap_ph
        sta irq_ph
_ps     jsr spr_copy
        jsr sfx_update
        jmp irq_exit

; ------------------------------------------------------------------ primitive
p10l    .byte <10000, <1000, <100, <10, <1
p10h    .byte >10000, >1000, >100, >10, >1

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

; (23/11) riga del bersaglio, riga 20 dello schermo HUD (BTR_SCR): nome del mostro bersaglio
; (colonne 1-24) e sua vita (12 caratteri G_BAR, colonne 26-37, viola), oppure l'etichetta del luogo o il messaggio delle quest
; (nbuf, bar.asm: codici schermo della ROM tradotti nei glifi dell'HUD; lettere, cifre, "/" e "." - il resto spazio). Prima
; stavano in 8 sprite in cima allo schermo, che coprivano il PG in cima alla mappa. Ogni 4 fotogrammi; quando la barra si
; spegne il testo resta BTH_FR fotogrammi (tra un colpo e l'altro bar_on si spegne e si riaccende: lampeggio). Ogni cella si
; scrive una volta sola con il valore finale (niente riga cancellata e riscritta mentre il raster la disegna).
BTH_FR   = 50
BT_NC     = 1                   ; colonna del nome
BT_BC     = 26                  ; colonna della vita
bt_row:
        lda BTR_SCR             ; colonna 0 sempre vuota quando la riga e' scritta da qui: se no (avvio: c'e' la grafica copiata
        cmp #G_BLANK            ; da copy_gfx) la riga si svuota subito
        bne _bk
        lda sk_t                ; (23/11) abilita' appena scelta (o oggetto rotto): il suo nome per SK_SHOW fotogrammi, in giallo
        beq +
        lda frame
        and #3
        bne _x
        ldx #40
        jsr hb_clear
        ldx hud_nm
        lda sk_off,x
        tax
        ldy #0
-       lda sk_nm,x
        sta hb+BT_NC,y
        lda #7
        sta hc+BT_NC,y
        inx
        iny
        cpy #10
        bne -
        lda #2                  ; finito il nome: la riga si ridisegna (o si svuota) subito
        sta bt_hold
        jmp _fl
+       lda bar_on
        bne _on
        lda bt_hold             ; barra spenta: il testo resta BTH_FR fotogrammi, poi la riga si svuota
        beq +
        dec bt_hold
        beq _bk
_x      rts
+       lda frame               ; e si riscrive vuota ogni 16 fotogrammi: altre schermate (UI, attese) usano SCR_H e la sporcano
        and #15
        bne _x
_bk     lda #0
        sta bt_hold
        ldx #40
        jsr hb_clear
        jmp _fl
_on     lda #BTH_FR
        sta bt_hold
        lda frame
        and #3
        bne _x
        ldx #40
        jsr hb_clear
        ldx #23
_t      lda nbuf,x
        jsr bt_ch
        sta hb+BT_NC,x
        dex
        bpl _t
        lda bar_lab
        bne _fl
        ldx #23                 ; vita del mostro: celle piene di cellf (bar_build) x 4 pixel su 12 caratteri
        lda #0
-       ldy cellf,x
        beq +
        clc
        adc #4
+       dex
        bpl -
        ldx #12
        stx bar_n
        ldx #4                  ; viola: diversa dalla vita del PG (rossa) e dall'esperienza (gialla)
        stx bar_c
        ldx #BT_BC
        jsr bar
_fl     ldx #39
-       lda hb,x
        sta BTR_SCR,x
        lda hc,x
        sta BT_COLR,x
        dex
        bpl -
        rts
bt_ch:                          ; A = codice schermo -> glifo HUD (Y usato)
        tay
        dey
        cpy #26
        bcs +
        lda bt_xl,y
        rts
+       sec
        sbc #48
        cmp #10
        bcs +
        adc #G_0
        rts
+       ldy #G_SLASH
        cmp #(47-48) & $ff
        beq +
        ldy #G_DOT
        cmp #(46-48) & $ff
        beq +
        ldy #G_BLANK
+       tya
        rts
; codici schermo 1-26 (lettere) -> glifi HUD (le cifre 48-57 sono G_0..G_9 di seguito)
bt_xl   .byte G_A, G_B, G_C, G_D, G_E, G_F, G_G, G_H, G_I, G_J, G_K, G_L, G_M, G_N, G_O
        .byte G_P, G_Q, G_R, G_S, G_T, G_U, G_V, G_W, G_X, G_Y, G_Z
        .cerror G_9 != G_0 + 9, "bt_xl: cifre HUD non di seguito"

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

; (23/11, committente) HUD compatto, righe 20-23 dello schermo HUD:
;   20 riga del bersaglio (bt_row) · 21 vuota con il regolo · 22 vita · 23 esperienza
;   riga 22: barra rossa della vita (colonne 1-17, 136 pixel; la 18 vuota) · avvisi degli oggetti (19-21) · pozioni 1-4 (23, 25, 27, 29) · pergamena (31) · H J K (33, 35, 37)
;   riga 23: barra gialla dell'esperienza (1-17) · freccia verde del level up (20) · posti 5-8 (23-29, cintura da 8) · L U O
; Niente numeri, niente "LV", niente chiavi (nell'inventario) ne' capitolo e piano (minimappa e menu di gioco).
HB_BARW  = 17                   ; celle delle barre (23/11: una in meno di 18, resta la colonna 18 vuota)
HB_HP    = 80                   ; offset da HUD_ROW0: riga 22
HB_XP    = 120                  ; riga 23
HB_POT   = 23                   ; colonna del primo posto della cintura
HB_SK    = 33                   ; colonna della prima abilita'
HP_ROWC  = COLRAM + 880         ; color RAM della riga 22
HP_ROWS  = SCR_H + 880          ; schermo HUD, riga 22

; ---- riga 22: barra della vita
hud_p0:
        ldx #HB_BARW+1
        jsr hb_clear
        lda c_hp
        sta sc_n
        lda c_hp+1
        sta sc_n+1
        lda hpmax
        sta sc_d
        lda hpmax+1
        sta sc_d+1
        lda #HB_BARW*8
        sta sc_k
        jsr scale
        cmp #0
        bne _px
        lda c_hp
        ora c_hp+1
        beq _px
        lda #1                  ; vivo: almeno un pixel
_px     ldx #HB_BARW
        stx bar_n
        ldx #2
        stx bar_c
        ldx #1
        jsr bar
        lda #HB_HP
        ldx #HB_BARW+1
        jmp hflush

; ------------------------------------------------------------------ avvisi (chiamato ogni 16 fotogrammi)
; Vita bassa (c_hp <= hpmax / 4): le celle piene della barra della vita (riga 22) alternano rosso e giallo; al passaggio
; sotto la soglia un suono (SFX_LOWHP), una volta. Oggetto indossato che si sta per rompere (durabilita' <= WARN_PC % del
; massimo): icona rossa/gialla lampeggiante in riga 22, colonne 19..21.
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
        ldx #HB_BARW
_c      ldy HP_ROWS,x           ; solo le celle piene (il binario vuoto resta blu)
        cpy #G_BAR0
        beq +
        sta HP_ROWC,x
+       dex
        bne _c
        jmp hw_icons
_ok     lda hw_low
        beq hw_icons
        lda #0                  ; fine della vita bassa: si ridisegna la barra (colori normali)
        sta hw_low
        lda hud_pend
        ora #1
        sta hud_pend
; icone degli oggetti che si stanno per rompere -> riga 22, colonne 19..21 (schermo HUD e color RAM)
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
        lda #HB_HP+HB_BARW+2    ; colonna 19
        ldx #3
        jmp hflush
hw_gl   .byte G_WSWORD, G_WARMOR, G_WSHIELD

; ---- riga 23: barra dell'esperienza (frazione del livello) e freccia verde del level up
hud_p1:
        ldx #HB_BARW+4
        jsr hb_clear
        lda c_lvl
        cmp #PL_MAXLVL
        bcc _lv
        lda #HB_BARW*8          ; livello massimo: barra piena
        jmp _bar
_lv     tax                     ; (xp - soglia precedente) / (soglia - precedente), differenze a 16 bit
        dex
        lda #0
        sta tmp5
        sta tmp6
        cpx #0
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
        lda #HB_BARW*8
        sta sc_k
        jsr scale
_bar    ldx #HB_BARW
        stx bar_n
        ldx #7
        stx bar_c
        ldx #1
        jsr bar
        jsr pts_avail           ; (11/11) punti statistica da spendere: freccia verde in su (G_LVUP)
        beq +
        lda #G_LVUP
        sta hb+HB_BARW+3
        lda #5                  ; verde (colore < 8: carattere hires)
        sta hc+HB_BARW+3
+       lda #HB_XP
        ldx #HB_BARW+4
        jmp hflush

; ---- riga 21 (regolo) e abilita' H J K / L U O (righe 22-23, colonne 33, 35, 37)
hud_p2:
        ldx #40
        jsr hb_clear
        lda COLRAM+760          ; colore della mappa (riga 19 della memoria colore, del campo di gioco)
        sta tmp4
        ldx #39
_r      lda #G_RULE
        sta hb,x
        lda tmp4
        sta hc,x
        dex
        bpl _r
        lda #40
        ldx #40
        jsr hflush
        ldx #12
        jsr hb_clear            ; hb 0..5 = riga 22, 6..11 = riga 23 (una cella si' e una no)
        ldx #0
_k      lda c_lvl               ; abilita' non ancora disponibile: niente lettera (07/11)
        cmp sk_req,x
        bcc _kn
        lda sk_g,x
        ldy sk_pos,x
        sta hb,y
        cpx #4
        bcs _bf
        lda #1                  ; H J K L: bianco, giallo quella scelta
        cpx c_skill
        bne _kc
        lda #7
        bne _kc
_bf     lda bf_t-4,x            ; U (Rage) e O (Frenzy): attiva = giallo, pronta = bianco, ricarica = ciano
        tay
        lda tmr,y
        ora tmr+1,y
        beq +
        lda #7
        bne _kc
+       lda sk_cdl,x
        ora sk_cdh,x
        beq +
        lda #3
        bne _kc
+       lda #1
_kc     ldy sk_pos,x
        sta hc,y
_kn     inx
        cpx #6
        bne _k
        lda #HB_HP+HB_SK
        ldx #5
        jsr hflush
        ldx #5                  ; riga 23: hb+6..11 -> hb+0..5
-       lda hb+6,x
        sta hb,x
        lda hc+6,x
        sta hc,x
        dex
        bpl -
        lda #HB_XP+HB_SK
        ldx #5
        jmp hflush

SK_SHOW = 100                   ; 2 secondi
sk_off  .byte 0, 10, 20, 30, 40
sk_g    .byte G_H, G_J, G_K, G_L, G_U, G_O
sk_pos  .byte 0, 2, 4, 6, 8, 10 ; H J K in riga 22, L U O in riga 23 (in hb: 6..11 = riga 23)
bf_t    .byte T_RAGE, T_FZ
sk_nm
        .enc "hud"              ; testo normale: ogni lettera diventa il suo glifo HUD (mostrato nella riga del bersaglio)
        .text "slash     "
        .text "whirlwind "
        .text "battle cry"
        .text "smash     "
        .text "broken    "
        .enc "none"

; ---- cintura (23/11, committente): due file da 4 pozioni, riga 22 posti 1-4 e riga 23 posti 5-8 (oggi vuoti: la cintura
; da 8 arrivera'), colonne 23..29; la pergamena nella prima fila, a destra delle pozioni (colonna 31). Posto vuoto: trattino blu
hud_p3:
        ldx #9
        jsr hb_clear
        ldy #0
_i      tya
        asl
        tax
        lda #G_DOT              ; vuoto: trattino
        sta hb,x
        lda #6
        sta hc,x
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
        sta hc,x
        lda #G_POT
        sta hb,x
_n      iny
        cpy #4
        bne _i
        jsr scr_find            ; pergamene: icona se ce n'e' almeno una (quantita' nell'inventario)
        bcs _ns
        lda #1
        sta hc+8
        lda #G_SCR
        sta hb+8
_ns     lda #HB_HP+HB_POT
        ldx #9
        jsr hflush
        ldx #7                  ; riga 23: posti 5-8, vuoti (trattini)
        jsr hb_clear
        ldx #6
-       lda #G_DOT
        sta hb,x
        lda #6
        sta hc,x
        dex
        dex
        bpl -
        lda #HB_XP+HB_POT
        ldx #7
        jmp hflush
