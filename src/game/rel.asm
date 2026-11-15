;===================================================================
;  rel.asm - salvataggi con il plugin di save di Krill's Loader r194 (11/11, ramo fast-loader; docs/salvataggi.md)
;
;  Quando si scrive (11/11 sera, decisione del committente, docs/salvataggi.md): SOLO con "save game" (menu RUN/STOP), alla
;  creazione dell'eroe e al cambio di capitolo (gruppi di CH_LV = 5 piani). Gli stati dei piani del capitolo corrente stanno
;  in RAM (slot LVRAM, sotto l'I/O): le scale, il portale, la locanda e la scheda del personaggio non scrivono il disco.
;
;  Un file per eroe, "save-01".."save-05" (scelta del committente: pochi file sul disco), SV_LEN byte:
;    +0                       blocco dell'eroe CHRBLK..CHREND (con il baule della locanda)
;    +HERO_LEN + (piano-1)*LV_SLOT   stato compatto del piano (lv_put / lv_get, al massimo LV_SLOT byte)
;  Elenco eroi: file "hl" (HDR_LEN byte: versione SAVE_VER, 5 byte "eroe presente", 5 nomi da NAME_LEN).
;  I file li crea la build (tools/build/mkdisk.sh) con la lunghezza giusta: il plugin di Krill riscrive solo file gia'
;  presenti e con lo stesso numero di blocchi. Ogni scrittura riscrive il file intero: si legge il file (sv_read),
;  si cambia la parte (eroe o un piano) e lo si riscrive (sv_write). Lo stato del piano non porta con se' l'eroe:
;  salvando un piano la parte dell'eroe resta quella del disco (come con il REL: l'eroe si salva solo quando lo
;  si sceglie, cosi' spegnendo non si duplica nulla).
;  RAM, solo durante un salvataggio, sotto il KERNAL: immagine del file SV_IMG ($E000), plugin di save krill_save ($E820,
;  file KSAVE), buffer del plugin SV_SCR ($ECE0, $0800 byte, fino a $F4DF: subito sotto la zona 2 del MENU). Liberi nel
;  dungeon; nel villaggio $E000-$ECFF e' il villaggio (GFX0), che dopo si rilegge (sv_end, town_at). Il plugin
;  si carica dal file KSAVE prima di ogni save (si modifica da solo: va comunque ricaricato). Durante il save: $01 = $35,
;  interrupt spenti (il plugin gira nella RAM sotto il KERNAL).
;
;  Stato compatto del piano (lv_put / lv_get), a partire dal piano rigenerato dal seed (82 o 93 byte):
;    piano, partita (2 byte: se e' un'altra partita mostri e bauli del piano si ripopolano), numero mostri, 4 byte "vivo" (1 bit per mostro; le posizioni NON si salvano: i vivi ripartono
;    dalla casella di partenza), 1 byte "bauli del piano tolti" (bit i = posto i, CH_GEN_MAX posti),
;    baule del boss non aperto: 1 + X, Y, tipo + 4 x (oggetto, bonus) oppure 0 (finche' non e' aperto ha il
;    bit 3 del tipo: primo oggetto = numero di oggetti, primo bonus = livello bottino),
;    nebbia a settori 2x2: 72 byte (24 righe x 3 byte, 1 bit per settore).
;  I bauli aperti (bit 5) e i tesori lasciati dai mostri spariscono cambiando piano (non si salvano).
; ===================================================================
        .enc "none"
HDR_LEN  = 1 + 5 + 5*NAME_LEN
HERO_LEN = CHREND - CHRBLK
LV_SLOT  = 93                   ; stato compatto di un piano: 82 o 93 byte (9 + baule del boss 1 o 12 + nebbia 72)
SV_LEN   = HERO_LEN + MAXLEVEL*LV_SLOT
SV_IMG   = $e000                ; immagine del file (RAM sotto il KERNAL)
SV_SCR   = $ece0                ; buffer del plugin ($0800 byte, "drive-code buffer" di Krill)
        .cerror SV_IMG + SV_LEN > krill_save, "immagine del salvataggio sopra il plugin di save (tools/build/krill_build.sh, TRANSIENT)"
        .cerror krill_save + KRILL_SAVE_LEN > SV_SCR, "plugin di save sopra il suo buffer"
        .cerror SV_SCR + $800 > MR2_AT, "buffer del plugin sopra la zona 2 del modulo MENU"
        .cerror SV_LEN + 2 > 9*254, "file dell'eroe oltre 9 blocchi (tools/build/mkdisk.sh)"
rpt     = $4a                   ; puntatore del flusso rel_put / rel_get (pagina zero libera fuori da Krill: $41-$47)
; piani del capitolo in RAM (11/11 sera): CH_LV slot da LV_SLOT byte nella RAM sotto l'I/O, dopo il generatore
CH_LV    = 5                    ; piani per capitolo (regola del committente, docs/quests.md 3.8)
LVRAM    = gen_io_end           ; slot del piano (L-1) mod CH_LV
LVRAM_end = LVRAM + CH_LV*LV_SLOT   ; (15/11) coppia di etichette per la mappa automatica (TODO T1)
;@free LVRAM_end..$e000 "RAM sotto l'I/O dopo generatore e slot dei piani: codice che gira con $01=$34 e interrupt spenti (come gen_io.asm), o dati" use=code-io-off
;@map SV_SCR+2048 "Buffer del plugin di save di Krill (drive-code buffer)" scenario=salvataggio
;@map LVRAM "Piani del capitolo: CH_LV slot da LV_SLOT byte (stato compatto), sul disco solo con save game o cambio di capitolo"
        .cerror LVRAM + CH_LV*LV_SLOT > $e000, "slot dei piani del capitolo oltre $DFFF"

        .virtual $9b00
lv_same .byte ?                 ; lv_get: $FF se il record e' di un'altra partita (mostri e bauli ripopolati)
rsx     .byte ?
rsy     .byte ?
rel_hold .byte ?                ; 1 = piu' parti in una sola riscrittura del file: la scrive rel_done (gm_save, nuovo eroe)
sv_in   .byte ?                 ; 1 = SV_IMG contiene il file dell'eroe cur_slot letto (e forse cambiato) sotto rel_hold
hdrbuf  .fill HDR_LEN           ; file "hl"
cur_chap .byte ?                ; capitolo dei piani negli slot LVRAM (1.., 0 = nessuno: si leggono dal file all'ingresso)
rel_end
        .endv
        .cerror rel_end > SP_VARS, "variabili dei salvataggi sopra il player SID"
        .cerror LVLEND > $9b00, "LVLBLK oltre $9AFF"

; un byte (A) nel flusso (X, Y conservati). Il flusso puo' stare nella RAM sotto l'I/O (slot LVRAM) o sotto il KERNAL
; (immagine del file): l'accesso si fa con $01 = $34 e interrupt spenti, poi $01 e P tornano come prima
rel_put:
        stx rsx
        sty rsy
        php
        sei
        ldx $01
        ldy #$34
        sty $01
        ldy #0
        sta (rpt),y
        stx $01
        plp
        inc rpt
        bne +
        inc rpt+1
+       ldx rsx
        ldy rsy
        rts

; un byte dal flusso -> A (N/Z secondo il byte letto; X, Y conservati)
rel_get:
        stx rsx
        sty rsy
        php
        sei
        ldx $01
        ldy #$34
        sty $01
        ldy #0
        lda (rpt),y
        stx $01
        plp
        inc rpt
        bne +
        inc rpt+1
+       ldx rsx
        ldy rsy
        ora #0
        rts

rel_done:
        lda #0
        sta rel_hold
        lda sv_in
        beq _x
        lda #0
        sta sv_in
        jsr sv_write
        jmp sv_end
_x      rts

; immagine del file: letta una sola volta sotto rel_hold (sv_in), altrimenti a ogni operazione
; C=1 se il file non si legge (11/11, review: senza questo controllo si sarebbe riscritto il file con l'immagine sbagliata)
sv_get:
        lda sv_in
        bne _ok
        jsr sv_read
        bcs _x
        lda rel_hold
        sta sv_in
_ok     clc
_x      rts
; dopo il cambiamento: si scrive subito se non c'e' rel_hold (poi rel_done)
sv_put:
        lda rel_hold
        bne _x
        jsr sv_write
        jmp sv_end
_x      rts

; nome del file dell'eroe cur_slot: "save-0N" in sv_nm
sv_name:
        ldx #5
-       lda _s,x
        sta sv_nm,x
        dex
        bpl -
        lda cur_slot
        clc
        adc #$31
        sta sv_nm+6
        lda #0
        sta sv_nm+7
        rts
_s      .text "save-0"

; file dell'eroe cur_slot -> SV_IMG. C=1 errore
sv_read:
        jsr snd_io
        jsr io_begin
        jsr sv_name
        lda #<SV_IMG
        sta krill_loadaddrlo
        lda #>SV_IMG
        sta krill_loadaddrhi
        sec
        ldx #<sv_nm
        ldy #>sv_nm
        jmp krill_loadraw

; SV_IMG -> file dell'eroe cur_slot. C=1 errore
sv_write:
        lda #<sv_nm
        ldx #>sv_nm
        ldy #<SV_IMG
        sty sv_par+2
        sty sv_par+6
        ldy #>SV_IMG
        sty sv_par+3
        sty sv_par+7
        ldy #<SV_LEN
        sty sv_par+4
        ldy #>SV_LEN
        sty sv_par+5
        ; (fallthrough)
; plugin di save: nome A/X, gia' scritti da/lunghezza/indirizzo in sv_par+2..+7. C=1 errore
sv_save:
        sta sv_par
        stx sv_par+1
        clc                     ; plugin ricaricato dal disco (file KSAVE) a ogni save: modifica il proprio codice
        ldx #<nm_ksave          ; (17 byte, provato in VICE l'11/11) e una seconda chiamata senza ricarica si blocca
        ldy #>nm_ksave
        jsr krill_loadraw
        bcs _e2
        lda #<SV_SCR
        sta sv_par+8
        lda #>SV_SCR
        sta sv_par+9
        php
        sei
        lda $01                 ; (chi chiama puo' girare sotto il KERNAL, $01 = $35: modulo MENU, zona 2)
        pha
        lda #<nmi_stub          ; (RESTORE: vettore NMI nella RAM sotto il KERNAL)
        sta $fffa
        lda #>nmi_stub
        sta $fffb
        lda #$35                ; KERNAL escluso: buffer e immagine nella RAM sotto il KERNAL
        sta $01
        ldx #<sv_par
        ldy #>sv_par
        jsr krill_save
        pla                     ; (pla non tocca C)
        sta $01
        bcs _e
        plp
        clc
        rts
_e      plp
_e2     sec
        rts
nm_ksave .text "ksave"
        .byte 0

; lettura di SV_IMG (RAM sotto il KERNAL): interrupt spenti e KERNAL escluso; img_off rimette tutto (C conservato)
img_on:
        pla                     ; (indirizzo di ritorno sotto i valori salvati)
        sta tmp6
        pla
        sta tmp7
        php
        sei
        lda $01
        pha
        lda #$35
        sta $01
        lda tmp7
        pha
        lda tmp6
        pha
        rts
img_off:
        pla
        sta tmp6
        pla
        sta tmp7
        pla
        sta $01
        pla                     ; P del chiamante (interrupt), ma C di adesso
        and #$fe
        sta tmp5
        php
        pla
        and #1
        ora tmp5
        pha
        plp
        lda tmp7
        pha
        lda tmp6
        pha
        rts

; dopo un'operazione con SV_IMG: se il villaggio era a $E000 lo si rilegge (solo la RAM: grafica gia' installata)
sv_end:
        php
        lda sv_in               ; immagine ancora da scrivere (rel_hold): il villaggio si rilegge dopo rel_done
        bne _x
        lda town_at
        beq _x
        lda io_quiet
        pha
        lda #1
        sta io_quiet
        lda #0
        jsr load_gfx
        pla
        sta io_quiet
_x      plp
        rts

; ---------------------------------------------------------------- eroi
; solo l'eroe (creazione dell'eroe, prove): le parti dei piani restano quelle del disco
save_char:
        jsr char_pos
        jsr sv_get
        bcc +
        jmp sv_fail
+       jsr char_img
        jmp sv_put

; salvataggio completo (save game, cambio di capitolo): eroe + piani del capitolo negli slot, una sola riscrittura.
; C=1 se il file non si legge (niente scrittura)
sv_all:
        jsr char_pos
        lda #1
        sta rel_hold
        jsr sv_get
        bcc +
        lda #0
        sta rel_hold
        jmp sv_fail
+       jsr char_img
        lda #0                  ; slot -> immagine (blocco contiguo del capitolo)
        jsr chap_copy
        jsr rel_done
        clc
        rts

; posizione dell'eroe nel blocco; schermata "saving barbarian"
char_pos:
        lda px
        sta c_px
        lda px+1
        sta c_px+1
        lda py
        sta c_py
        lda py+1
        sta c_py+1
        lda #0
        sta io_dir
        sta io_what
        rts
; CHRBLK -> immagine del file (scrittura nella RAM sotto il KERNAL: con il KERNAL acceso va alla RAM)
char_img:
        ldx #0
_l      lda CHRBLK,x
        sta SV_IMG,x
        inx
        cpx #HERO_LEN
        bne _l
        rts

; C=1 se l'eroe cur_slot non c'e' o e' di un'altra versione (sv_old = 1)
load_char:
        lda #1
        sta io_dir
        lda #0
        sta io_what
        jsr sv_read
        bcs _bad
        jsr img_on
        ldx #0
_l      lda SV_IMG,x
        sta CHRBLK,x
        inx
        cpx #HERO_LEN
        bne _l
        jsr img_off
        jsr sv_end
        lda c_magic
        cmp #SAVE_VER
        beq _ok
_old    lda #1
        sta sv_old
        sec
        rts
_bad    jsr sv_end
        jmp _old
_ok     jsr migrate_char
        clc
        rts

; file "hl" <- versione + eroi presenti + nomi (slot_valid / slot_name)
hdr_write:
        lda #SAVE_VER
        sta hdrbuf
        ldx #4
_v      lda slot_valid,x
        sta hdrbuf+1,x
        dex
        bpl _v
        ldy #0                  ; nomi: slot_name ha passo 16
        ldx #0
_n      sty tmp7
        tya
        asl
        asl
        asl
        asl
        tay
        lda #NAME_LEN
        sta tmp6
_c      lda slot_name,y
        sta hdrbuf+6,x
        inx
        iny
        dec tmp6
        bne _c
        ldy tmp7
        iny
        cpy #5
        bne _n
        jsr snd_io
        lda #<hdrbuf
        sta sv_par+2
        sta sv_par+6
        lda #>hdrbuf
        sta sv_par+3
        sta sv_par+7
        lda #HDR_LEN
        sta sv_par+4
        lda #0
        sta sv_par+5
        lda #<nm_hl
        ldx #>nm_hl
        jsr sv_save             ; (il plugin si carica a $E820: nel villaggio copre il villaggio)
        jmp sv_end
nm_hl   .text "hl"
        .byte 0

; file "hl" -> hdrbuf (HDR_LEN byte). Se manca o non si legge: tutto a 0 (nessun eroe)
hdr_read:
        jsr snd_io
        lda #<hdrbuf
        sta krill_loadaddrlo
        lda #>hdrbuf
        sta krill_loadaddrhi
        sec
        ldx #<nm_hl
        ldy #>nm_hl
        jsr krill_loadraw
        bcc +
        lda #0
        ldx #HDR_LEN-1
-       sta hdrbuf,x
        dex
        bpl -
+       clc
        rts

; cancella tutti i salvataggi: nessun eroe presente, versione attuale
scratch_all:
        ldx #4
        lda #0
_z      sta slot_valid,x
        dex
        bpl _z
        jmp hdr_write

; ---------------------------------------------------------------- piani
; rpt = SV_IMG + HERO_LEN + (A-1)*LV_SLOT (A = piano 1..MAXLEVEL)
rec_level:
        tax
        lda #<(SV_IMG+HERO_LEN-LV_SLOT)
        sta rpt
        lda #>(SV_IMG+HERO_LEN-LV_SLOT)
        sta rpt+1
-       lda rpt
        clc
        adc #LV_SLOT
        sta rpt
        bcc +
        inc rpt+1
+       dex
        bne -
        rts

;ptr del capitolo: A = piano 1..MAXLEVEL -> A = capitolo 1.. ((A-1)/CH_LV + 1), X = (A-1) mod CH_LV
lv_grp:
        sec
        sbc #1
        ldx #0
-       cmp #CH_LV
        bcc +
        sbc #CH_LV
        inx
        bne -
+       stx tmp7
        tax
        lda tmp7
        clc
        adc #1
        rts

; rpt = slot del piano A (A-1) mod CH_LV in LVRAM
slot_ptr:
        jsr lv_grp
        lda #<LVRAM
        sta rpt
        lda #>LVRAM
        sta rpt+1
        inx
-       dex
        beq +
        lda rpt
        clc
        adc #LV_SLOT
        sta rpt
        bcc -
        inc rpt+1
        bne -
+       rts

; A = piano: LVLBLK (compatto) -> il suo slot in RAM (11/11 sera: niente disco). C=1 se il piano non e' del
; capitolo negli slot (non dovrebbe succedere: si ignora)
save_lvlblk:
        sta lb_lvl
        jsr lv_grp
        cmp cur_chap
        beq +
        sec
        rts
+       lda lb_lvl
        jsr vis_bit
        ora c_vis,x
        sta c_vis,x
        lda lb_lvl
        jsr slot_ptr
        jsr lv_put
        clc
        rts

; il file dell'eroe non si legge: niente scrittura (C=1); il villaggio, se era a $E000, si rilegge
sv_fail:
        jsr sv_end
        sec
        rts

; stato compatto del piano dal suo slot, sopra il piano appena rigenerato. C=1 se non valido
load_level:
        lda cur_level
        jsr slot_ptr
        jmp lv_get

; slot <-> immagine del file per il capitolo cur_chap: A = 0 slot -> immagine, 1 immagine -> slot. RAM sotto l'I/O e
; sotto il KERNAL: $01 = $34, interrupt spenti
chap_copy:
        sta tmp6
        lda cur_chap
        beq _x
        sec                     ; primo piano del capitolo: (cur_chap-1)*CH_LV + 1
        sbc #1
        sta tmp7
        asl
        asl
        adc tmp7                ; (CH_LV = 5)
        adc #1
        jsr rec_level           ; rpt = immagine del primo piano
        lda #<LVRAM
        sta ptr2
        lda #>LVRAM
        sta ptr2+1
        lda #<(CH_LV*LV_SLOT)   ; contatore a 16 bit
        sta tmp4
        lda #>(CH_LV*LV_SLOT)
        sta tmp5
        php
        sei
        lda $01
        pha
        lda #$34
        sta $01
        ldy #0
_l      lda tmp6
        bne _in
        lda (ptr2),y            ; slot -> immagine
        sta (rpt),y
        jmp _n
_in     lda (rpt),y             ; immagine -> slot
        sta (ptr2),y
_n      iny
        bne +
        inc rpt+1
        inc ptr2+1
+       lda tmp4
        bne +
        dec tmp5
+       dec tmp4
        lda tmp4
        ora tmp5
        bne _l
        pla
        sta $01
        plp
_x      rts
        .cerror CH_LV != 5, "chap_copy: primo piano del capitolo calcolato per CH_LV = 5"

; cambio di capitolo (change_level, prima di cambiare piano): eroe + piani del capitolo sul disco; gli slot si
; rileggono all'ingresso nel piano nuovo (chap_ensure). Il piano lasciato per portale o morte (STASH) va prima nel suo slot
chap_save:
        lda cur_chap
        bne chap_savef
        rts
chap_savef:                     ; (12/11) anche con cur_chap = 0: passaggio di capitolo (chapter.asm, chap_travel)
        lda pend_lvl
        beq +
        jsr pend_save
        lda #0
        sta pend_lvl
+       jsr sv_all
        lda #0
        sta cur_chap
_x      rts

; ingresso in un piano (load_location, prima dello stato del piano): se il capitolo degli slot non e' quello di
; cur_level, gli slot si leggono dal file dell'eroe (file illeggibile: slot vuoti, i piani si rigenerano)
chap_ensure:
        lda cur_level
        jsr lv_grp
        cmp cur_chap
        beq _x
        sta cur_chap
        lda #1
        sta io_dir
        sta io_what
        lda cur_level
        sta io_lvl
        jsr sv_read
        bcs _bad
        lda #1                  ; immagine -> slot
        jsr chap_copy
        jmp sv_end
_bad    jsr sv_end
        lda #0                  ; slot vuoti: primo byte 0 (lv_get li scarta perche' diverso dal piano)
        sta tmp6
-       lda tmp6
        clc
        adc #1
        jsr slot_ptr
        lda #0
        jsr rel_put
        inc tmp6
        lda tmp6
        cmp #CH_LV
        bne -
_x      rts

; ---- scrittura dello stato compatto (rel_put)
; piano, numero mostri, 4 byte "vivo", 1 byte "bauli del piano tolti", baule del boss, nebbia a settori 2x2
lv_put:
        lda lb_lvl
        jsr rel_put
        lda c_game              ; numero della partita (9 bit): mostri e bauli valgono solo nella stessa partita
        jsr rel_put
        lda c_game+1
        and #1
        jsr rel_put
        lda lb_cnt
        jsr rel_put
        ldy #0                  ; 32 bit "vivo"
_ab     lda #0
        sta tmp0
        ldx #7
_ab1    tya
        pha
        tya
        asl
        asl
        asl
        sta tmp1
        txa
        clc
        adc tmp1
        tay
        lda malive,y
        cmp #1
        rol tmp0
        pla
        tay
        dex
        bpl _ab1
        lda tmp0
        jsr rel_put
        iny
        cpy #4
        bne _ab
        ; bauli del piano (posti 0..CH_GEN_MAX-1, bit 4): bit i = 1 se il baule i non c'e' piu' (aperto)
        lda #0
        sta tmp0
        ldx #CH_GEN_MAX-1
_gm     lda ch_t,x
        and #$30
        eor #$10                ; 0 = ancora li', chiuso
        cmp #1
        rol tmp0
        dex
        bpl _gm
        lda tmp0
        jsr rel_put
        ; baule del boss non aperto: 1, X, Y, tipo, 4 oggetti, 4 bonus (altrimenti 0)
        ldx lb_bch
        beq _nb
        dex
        lda ch_t,x
        beq _nb
        and #$20
        bne _nb
        lda #1
        jsr rel_put
        lda cx_x,x
        jsr rel_put
        lda cx_y,x
        jsr rel_put
        lda ch_t,x
        jsr rel_put
        txa
        asl
        asl
        tay
        ldx #8
_bi     lda ch_i,y
        jsr rel_put
        lda ch_b,y
        jsr rel_put
        iny
        dex
        dex
        bne _bi
        beq ex_put
_nb     lda #0
        jsr rel_put
; nebbia: settori 2x2 (24 x 24 bit = 72 byte); settore esplorato se lo e' almeno una delle sue caselle
ex_put:
        jsr ex_beg
_rp     ldy #0
_by     jsr ex_pk               ; colonna pari -> nibble alto, dispari -> nibble basso
        asl
        asl
        asl
        asl
        sta tmp3
        iny
        jsr ex_pk
        ora tmp3
        jsr rel_put
        iny
        cpy #6
        bne _by
        jsr ex_next
        bne _rp
        rts

; Y = colonna (0..5) della coppia di righe ptr2: (riga pari OR riga dispari) -> A = 4 bit, uno per coppia di
; caselle (bit 3 = caselle dei bit 7-6). Preserva Y.
ex_pk:
        lda (ptr2),y
        sta tmp0
        tya
        clc
        adc #6
        tay
        lda (ptr2),y
        ora tmp0
        sta tmp0
        tya
        sec
        sbc #6
        tay
        lda #0
        sta tmp1
        ldx #4
_bb     lda tmp0
        and #$c0
        cmp #1
        rol tmp1
        asl tmp0
        asl tmp0
        dex
        bne _bb
        lda tmp1
        rts

; inizio della nebbia: ptr2 = EXPL, tmp3.. contatore delle coppie di righe (tmp4 = 24)
ex_beg:
        lda #<EXPL
        sta ptr2
        lda #>EXPL
        sta ptr2+1
        lda #24
        sta tmp4
        rts
; coppia di righe successiva (ptr2 += 12). Z=1 a fine nebbia
ex_next:
        lda ptr2
        clc
        adc #12
        sta ptr2
        bcc +
        inc ptr2+1
+       dec tmp4
        rts

; ---- lettura dello stato compatto (rel_get) sopra il piano rigenerato dal seed
; I mostri vivi ripartono dalla casella di partenza (posizioni non salvate); i bauli del piano tolti spariscono.
lv_get:
        jsr rel_get
        cmp cur_level
        beq +
        sec
        rts
+       jsr rel_get             ; partita diversa: il piano si ripopola (mostri vivi, bauli del piano chiusi);
        cmp c_game              ; restano la nebbia e il baule del boss non aperto
        bne _old
        jsr rel_get
        eor c_game+1
        and #1
        beq _same
        bne _old2
_old    jsr rel_get
_old2   lda #$ff
        sta lv_same
        bne _cnt
_same   lda #0
        sta lv_same
_cnt    jsr rel_get             ; numero di mostri salvato: si tengono quelli rigenerati (le evocazioni no)
        ldy #0                  ; bit "vivo"
_ab     jsr rel_get
        ora lv_same             ; partita diversa: tutti vivi
        sta tmp0
        ldx #7
_ab1    lda #0
        asl tmp0
        rol
        pha
        tya
        asl
        asl
        asl
        sta tmp1
        txa
        clc
        adc tmp1
        stx tmp2
        tax
        pla
        cpx lb_cnt
        bcs +
        sta malive,x
+       ldx tmp2
        dex
        bpl _ab1
        iny
        cpy #4
        bne _ab
        jsr rel_get             ; bauli del piano tolti (bit i = posto i)
        ldx lv_same             ; partita diversa ($FF): nessun baule tolto
        beq +
        lda #0
+       sta tmp0
        ldx #0
_gm     lsr tmp0
        bcc +
        lda ch_t,x
        and #$10                ; solo se nel posto c'e' davvero il baule rigenerato del piano
        beq +
        lda #0
        sta ch_t,x
        lda cx_x,x              ; e la casella torna pavimento: place_chests ci aveva messo il tile del baule
        sta tx                  ; (07/11: senza, il baule aperto restava sulla mappa e Fire non faceva nulla)
        lda cx_y,x
        sta ty
        stx tmp7
        lda #T_FLOOR
        jsr set_tile
        ldx tmp7
+       inx
        cpx #CH_GEN_MAX
        bne _gm
        jsr rel_get             ; baule del boss
        beq _ex
        ldx lv_same             ; partita diversa: il boss rinasce, il suo vecchio baule si scarta
        beq _bok
        ldx #11
_sk     jsr rel_get
        dex
        bne _sk
        beq _ex
_bok    jsr rel_get
        sta loot_x
        jsr rel_get
        sta loot_y
        jsr rel_get
        and #$8f                ; (non aperto, non del piano)
        pha
        and #3
        jsr chest_add
        pla
        sta ch_t,x
        inx
        stx lb_bch
        dex
        txa
        asl
        asl
        tay
        ldx #8
_bi     jsr rel_get
        sta ch_i,y
        jsr rel_get
        sta ch_b,y
        iny
        dex
        dex
        bne _bi
_ex     jsr ex_beg              ; nebbia: ogni bit del settore -> 2 x 2 caselle
_rp     ldy #0
_by     jsr rel_get
        pha
        lsr
        lsr
        lsr
        lsr
        jsr _x4
        pla
        and #15
        iny
        jsr _x4
        iny
        cpy #6
        bne _by
        jsr ex_next
        bne _rp
        clc
        rts
; A = 4 bit -> 8 bit (ogni bit raddoppiato) nelle due righe, colonna Y
_x4     asl
        asl
        asl
        asl
        sta tmp0
        lda #0
        sta tmp1
        ldx #4
_xl     asl tmp1
        asl tmp1
        asl tmp0
        bcc +
        lda tmp1
        ora #3
        sta tmp1
+       dex
        bne _xl
        lda tmp1
        sta (ptr2),y
        sty tmp2
        pha
        tya
        clc
        adc #6
        tay
        pla
        sta (ptr2),y
        ldy tmp2
        rts
