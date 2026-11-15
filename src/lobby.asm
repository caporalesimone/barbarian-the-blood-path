; ===================================================================
;  menu iniziale: elenco eroi, scheda eroe salvato, nuovo eroe (file LOBBY, eseguito a $C000)
;  Modulo su file: assemblato a parte (tools/build/asm.sh) con le etichette del gioco (out/work/game.lbl).
; ===================================================================
        .include "../out/work/game.lbl"
        .include "macros.inc"
        * = LOBBY_AT
        jmp menu_main
        jmp detail_screen
        jmp bb_quit             ; $C006: libero (era il rientro SYS 49158, tolto l'11/11), per non spostare $C009
        jmp bb_quit             ; $C009: quit the game (anche da ui_badsave, nel gioco)
        .enc "screen"

; menu iniziale con Demon's Eye (15/11, TODO E3; dal 06/11 era muto: il passaggio della musica del titolo dal loader dava un
; glitch). Ora il brano e' un file SND_MENU suonato dal player del gioco (ui_menu). Gli interrupt restano spenti come in tutte
; le schermate a tutto schermo (ui_begin): la musica gira da ui_input.
menu_main:
        lda mus_trk             ; uscita dal gioco: prima si spegne la musica del gioco (dissolvenza)
        beq +
        jsr music_fadeout
+       sei
        lda #0                  ; SID in silenzio
        sta $d404
        sta $d40b
        sta $d412
        lda #$0f                ; volume come lo vuole il gioco
        sta $d418
.if TESTUI == 31
        jsr scan_slots          ; screenshot: subito la schermata del nuovo barbaro
        jsr name_entry
.endif
        jmp ui_menu             ; (torna con gli interrupt disattivati)

CHRPRE  = $8f                   ; 1 = elenco eroi (file hl) gia' letto da START, in CHRBUF (11/11: pagina zero, Krill occupa $0200-$0312)
CHRBUF  = $d000                 ; stato (1 = letto) + file hl (RAM sotto l'I/O)

; elenco eroi dal file hl (versione, eroi presenti, nomi): una sola lettura
scan_slots:
        lda CHRPRE
        beq _disk
        lda #0
        sta CHRPRE              ; la copia del loader vale solo per il primo ingresso nel menu
        sei
        lda #$34
        sta $01
        lda CHRBUF
        sta tmp0
        ldx #HDR_LEN-1
_cb     lda CHRBUF+1,x
        sta hdrbuf,x
        dex
        bpl _cb
        lda #$36
        sta $01
        cli
        lda tmp0
        bne scan_parse
_disk   lda #1
        sta io_dir
        lda #0
        sta io_what
        jsr io_screen_scan
        jsr hdr_read
scan_parse                      ; (anche dopo la cancellazione di un barbaro: hdrbuf gia' aggiornato, niente disco)
        lda #0
        sta nvalid
        sta cur_slot
        ldx #4
_z      sta slot_valid,x
        dex
        bpl _z
        lda hdrbuf
        cmp #SAVE_VER
        beq _ok
        ldx #4                  ; versione diversa: e' davvero un elenco di eroi? (byte "presente" 0/1, almeno un 1)
        ldy #0
_v      lda hdrbuf+1,x
        beq _vn
        cmp #1
        bne _none               ; altro (record vuoto, file mancante, errore di lettura): nessun eroe, nessun errore
        iny
_vn     dex
        bpl _v
        tya
        beq _none
        lda #1                  ; salvataggi di un'altra versione
        sta sv_old
_none   rts
_ok     ldx #0
_l      lda hdrbuf+1,x
        sta slot_valid,x
        beq _n
        ldy nvalid
        txa
        sta slot_idx,y
        inc nvalid
        stx tmp1
        ldy mm_n12,x            ; nome: hdrbuf+6+12*x -> slot_name+16*x
        txa
        asl
        asl
        asl
        asl
        tax
        lda #NAME_LEN
        sta tmp2
_c      lda hdrbuf+6,y
        sta slot_name,x
        inx
        iny
        dec tmp2
        bne _c
        ldx tmp1
_n      inx
        cpx #5
        bne _l
        rts
mm_n12  .byte 0, 12, 24, 36, 48

; elenco (09/11, standard dei menu): righe 3-7 i barbari salvati (riquadro " barbarians ") e "-" per i posti vuoti,
; riga 10 "create new barbarian", riga 11 "back to main menu" (secondo riquadro; fino al 15/11 "quit the game"). Voci del cursore: 0..nvalid-1 eroi,
; nvalid create, nvalid+1 quit.
MR_HERO = 3
MR_NEW  = 10
MR_QUIT = 11
MR_X    = 9
menu_draw:
        ldx #0
_l      stx tmp3
        txa
        clc
        adc #MR_HERO
        tay
        ldx #MR_X
        jsr ui_at
        ldx tmp3
        cpx nvalid
        bcs _dash
        jsr md_arrow
        ldx tmp3
        lda slot_idx,x
        jsr ui_name
        jmp _n
_dash   ldx #$ff                ; posto vuoto: niente freccia, "-"
        jsr md_arrow
        lda #$2d
        jsr ui_putc
_n      ldx tmp3
        inx
        cpx #5
        bne _l
        ldx #MR_X
        ldy #MR_NEW
        jsr ui_at
        ldx nvalid
        jsr md_arrow
        #msg "create new barbarian"
        ldx #MR_X
        ldy #MR_QUIT
        jsr ui_at
        ldx nvalid
        inx
        jsr md_arrow
        #msg "back to main menu"
        rts
; X = voce: "> " se e' quella del cursore, altrimenti due spazi
md_arrow:
        jsr ui_mark             ; (11/11, O8)
        lda #$20
        jmp ui_putc

ui_menu:
        lda #SND_MENU           ; (15/11, TODO E3) Demon's Eye (file SND_MENU) con il player del gioco: snd_get lo legge
        jsr mus_place           ; (snd_io + io_quiet, via load_raw) e music_request(MUS_LVL, FADE_SLOW); parte da music_update
                                ; (in ui_input). Gia' nel buffer (snd_cur): niente disco, niente riavvio.
_scan   lda #0
        sta sv_old
        jsr scan_slots
        lda sv_old
        beq _top
        jsr ui_badsave          ; C=1: cancellare e ripetere la scansione
        bcs _scan
_top    jsr ui_begin        ; (09/11) titolo standard con le spade, "the blood path" rosso; due riquadri
        lda #<tt_menu
        ldx #>tt_menu
        ldy #CH_SWORD
        jsr ui_title
        ldx #13                 ; "the blood path" (colonne 18-31 della riga 0) in rosso
        lda #2
_red    sta COLRAM+18,x
        dex
        bpl _red
        lda #<mn_box
        ldx #>mn_box
        ldy #8
        jsr ui_boxes
        jsr ui_labels
        .byte 9,2
        .text " barbarians "
        .byte 0,$ff
        #at VER_X,16
        lda #UC_HELP
        sta ui_col
        jsr ui_pi
        .text "version ", VERSION
        .byte 0
        #at 9,18                ; (11/11) credito del loader (licenza di Krill's Loader: docs/FastLoader.md)
        #msg "loader by krill - v194"
        #at 4,21
        lda #UC_HELP
        sta ui_col
        #msg "copyright 2026 - simone caporale"
        #at 1,24
        #msg "fire:select"
        lda nvalid
        clc
        adc #2                  ; eroi + "create new barbarian" + "quit the game"
        sta ui_n
        lda #0
        sta ui_cur
_dr     jsr menu_draw
.if TESTUI == 30
_hg     jmp _hg                 ; screenshot: la schermata resta com'e' (tasti fantasma in VICE)
.endif
_in     lda $d012
        eor rnd
        sta rnd
        lda frame
        eor rnd+1
        ora #1
        sta rnd+1
        jsr rand
        jsr ui_input
        lda joynew
        and #$01
        beq _a
        jsr cur_up
        jmp _dr
_a      lda joynew
        and #$02
        beq _b
        jsr cur_dn
        jmp _dr
_b      jsr ui_fire
        beq _in
        lda ui_cur
        cmp nvalid
        beq _create
        bcc _hero
        jmp bb_menu             ; back to main menu: si ricarica il loader BARBARIAN (16/11, committente; prima "quit the game" -> BASIC)
_hero   tax
        lda slot_idx,x
        sta cur_slot
        jsr load_char
        jsr recalc_stats
        jsr detail_screen
        bne _cf
        jsr scan_parse          ; il barbaro puo' essere stato cancellato: elenco di nuovo da hdrbuf
        jmp _top
_cf
        lda #0
        jmp lb_leave
_create lda nvalid
        cmp #5
        bcc _free
        #at 9,14
        #msg "all 5 slots are used."
        jmp _in
_free   ldx #0
_f      lda slot_valid,x
        beq _got
        inx
        bne _f
_got    stx cur_slot
        jsr name_entry
        bne _nf
        jmp _top
_nf
        lda #1
; uscita dal menu verso il gioco: la musica del menu si spegne con la dissolvenza PRIMA che music_town / music_dungeon
; riempiano il buffer del luogo (se il player girasse ancora, snd_get gli cambierebbe i dati sotto i piedi). A preservato.
lb_leave
        pha
        jsr music_fadeout
        pla
        rts

tt_menu .text "barbarian: the blood path", 0
mn_box  .byte 7,2,26,7, 7,9,26,4

dt_n5:                          ; A/X = valore 16 bit -> ui_num5
        sta tmp0
        stx tmp1
        jmp ui_num5

; tmp0/tmp1 / 60: quoziente in tmp2/tmp3, resto in A (sottrazioni ripetute: fino a 546 giri)
dt_div60:
        lda #0
        sta tmp2
        sta tmp3
_l      lda tmp0
        sec
        sbc #60
        tax
        lda tmp1
        sbc #0
        bcc _d
        sta tmp1
        stx tmp0
        inc tmp2
        bne _l
        inc tmp3
        bne _l
_d      lda tmp0
        rts


; scheda del barbaro salvato. In basso "start" e "delete barbarian" (sinistra/destra, 07/11 sera); fire/RETURN su
; start = in partita (A=1), su delete = domanda y/n e cancellazione (A=0); RUN/STOP o DEL = di nuovo l'elenco (A=0)
DT_ROW  = 19                    ; start game / delete <nome> / back, in colonna (08/11: riquadro 18-22, riga 23 per la domanda)
dt_tt   .text "saved game", 0
detail_screen:
        lda #0
        sta dt_sel
dt_redraw
        jsr ui_begin
        #ubox 0,2,40,4          ; riquadri attaccati (08/11): barbaro, progressi e caratteristiche, quest, scelta
        #ubox 0,6,20,8
        #ubox 20,6,20,8
        #ubox 0,14,40,4
        #ubox 0,18,40,5
        #at 2,2
        #msg " barbarian "
        #at 2,6
        #msg " progress "
        #at 22,6
        #msg " stats "
        #at 2,14
        #msg " quests "
        lda #UC_LABEL
        sta ui_col
        jsr ui_labels           ; etichette: x, y, testo, 0 ... $ff
        .byte 2,3
        .text "name"
        .byte 0,2,4
        .text "seed"
        .byte 0,25,3
        .text "sessions"
        .byte 0,25,4
        .text "time"
        .byte 0,2,7
        .text "level"
        .byte 0,2,8
        .text "exp"
        .byte 0,2,10
        .text "deaths"
        .byte 0,2,11
        .text "kills"
        .byte 0,2,12
        .text "abyss depth"
        .byte 0,22,7
        .text "max hp"
        .byte 0,22,8
        .text "attack"
        .byte 0,22,9
        .text "armor class"
        .byte 0,22,10
        .text "str"
        .byte 0,22,11
        .text "dex"
        .byte 0,22,12
        .text "con"
        .byte 0,2,15
        .text "current quest:"
        .byte 0,2,16
        .text "completed quests:"
        .byte 0,1,24
        .text "fire:select  run/stop:back"
        .byte 0,$ff
        lda #1                  ; titolo (routine unica ui_title, riga 1)
        sta ti_row
        lda #<dt_tt
        ldx #>dt_tt
        ldy #0
        jsr ui_title
        lda #7                  ; valori in giallo, allineati a destra (colonna 17 a sinistra, 37 a destra)
        sta ui_fc
        sta ui_col
        #at 8,3
        jsr ui_cname
        #at 8,4
        lda #7
        sta ui_col
        jsr ui_seed
        #at 19,15               ; quest: segnaposto finche' le quest non esistono (08/11)
        lda #7
        sta ui_col
        #msg "-"
        #at 21,16
        lda #7
        sta ui_col
        #msg "0 / -"
        #at 15,7
        lda c_lvl
        jsr ui_b3
        #at 13,8
        lda c_xp
        ldx c_xp+1
        jsr dt_n5
        #at 2,9                 ; oro: la moneta al posto della parola (08/11)
        jsr ui_coin
        #at 12,9               ; oro totale = addosso + baule (10/11: il baule conta le decine), fino a 665350: 6 cifre
        jsr gold_total          ; (11/11, O2: routine comune di GAME)
        jsr ui_num6
        #at 15,12               ; (12/11, committente) profondita' raggiunta nell'Abisso (capitolo 5, piani dopo MAXLEVEL):
        lda c_maxd              ; prima dell'Abisso "-"
        cmp #MAXLEVEL+1
        bcc +
        sbc #MAXLEVEL
        jsr ui_b3
        jmp ++
+       #at 17,12
        #msg "-"
+
        #at 13,11
        lda c_kills
        ldx c_kills+1
        jsr dt_n5
        #at 13,10
        lda c_deaths
        ldx c_deaths+1
        jsr dt_n5
        #at 33,7
        lda hpmax               ; vita massima (16 bit)
        ldx hpmax+1
        jsr dt_n5
        #at 35,8
        lda s_att
        jsr ui_b3
        #at 35,9
        lda s_ac
        jsr ui_b3
        #at 35,10
        lda s_str
        jsr ui_b3
        #at 35,11
        lda s_dex
        jsr ui_b3
        #at 35,12
        lda s_con
        jsr ui_b3
        #at 35,3                ; sessioni = numero della partita (9 bit, 1..511): 3 cifre, fino alla colonna 37
        lda c_game+1
        and #1
        sta tmp1
        lda c_game
        sta tmp0
        jsr ui_num3
        #at 30,4                ; tempo: ore in 3 cifre (colonne 30-32), "h", minuti in 2 (35-36), "m" (37)
        lda c_game+1            ; minuti: bit 9..23 -> ore e minuti
        sta tmp0
        lda c_game+2
        sta tmp1
        lsr tmp1
        ror tmp0
        lda tmp0                ; tmp0/tmp1 = minuti (15 bit)
        jsr dt_div60            ; tmp0/tmp1 / 60 -> ore (tmp2/tmp3), resto minuti (A)
        pha
        lda tmp2
        sta tmp0
        lda tmp3
        sta tmp1
        jsr ui_num3
        #msg "h"
        pla
        jsr ui_b3
        #msg "m"
.if NOKEYS
        jsr dt_opts
_hg     jmp _hg
.endif
        lda #3                  ; lista di 3 voci (motore ui_nav del gioco)
        sta ui_n
        jsr nav_init
        lda dt_sel
        sta ui_cur
        jsr nav_sync
_dr     jsr dt_opts
_in     jsr ui_nav
        cmp #NAV_MOVE
        bne +
        lda ui_cur
        sta dt_sel
        jmp _dr
+       cmp #NAV_BACK
        beq _no
        cmp #NAV_FIRE
        bne _in
        lda dt_sel
        beq _st
        cmp #1
        beq _ask
_no     lda #0                  ; back
        rts
_st     lda #1                  ; start
        rts
_ask    ldy #23                 ; domanda nella riga 23, libera sotto i riquadri (08/11)
        jsr clear_row
        #at 1,23
        lda #7
        sta ui_col
        #msg "delete this barbarian?"
        jsr ui_yesno
        bcs _del
        jmp dt_redraw           ; no: di nuovo la scheda (resta su delete)
_del    jsr ui_begin        ; (09/11) come io_screen: un solo record da scrivere
        #at 11,9
        #msg "deleting barbarian"
        jsr ui_pwait
        jsr hero_delete
        lda #0
        rts

; posto cur_slot libero: byte "eroe presente" a 0 e nome a spazi nell'elenco (record REC_HDR di SAVES). Il record
; dell'eroe e quelli dei suoi piani restano sul disco: il prossimo eroe di quel posto li sovrascrive o li ignora
; (c_vis = 0: nessun piano visitato, docs/salvataggi.md)
hero_delete:
        ldx cur_slot
        lda #0
        sta slot_valid,x
        sta hdrbuf+1,x
        txa
        asl
        asl
        asl
        asl
        tax
        ldy #NAME_LEN
        lda #$20
_n      sta slot_name,x
        inx
        dey
        bne _n
        jmp hdr_write           ; (08/11 sera) il baule sta nell'eroe: un barbaro nuovo nasce con il blocco azzerato

; righe DT_ROW..DT_ROW+2: start game, delete <nome>, back; la scelta in giallo con la freccia
dt_opts:
        #at 2,DT_ROW
        ldx #0
        jsr dt_arw
        #msg "start game"
        #at 2,DT_ROW+1
        ldx #1
        jsr dt_arw
        #msg "delete "
        jsr ui_cname
        #at 2,DT_ROW+2
        ldx #2
        jsr dt_arw
        #msg "back"
        rts
dt_arw  lda #1                  ; bianco, oppure giallo con la freccia
        ldy #$20
        cpx dt_sel
        bne +
        lda #7
        ldy #$3e
+       sta ui_col
        tya
        jsr ui_putc
        lda #$20
        jmp ui_putc
dt_sel  .byte 0

name_add:
        ldx nlen2
        cpx #NAME_LEN
        bcs _r
        sta namebuf,x
        inc nlen2
_r      rts

; riquadri di name_entry (09/11): name, seed, start; cornice del campo attivo verde (UC_CURSOR)
ne_boxes:
        ldx #0
_l      stx tmp3
        lda #UC_BOX
        cpx nfield
        bne +
        lda #UC_CURSOR
+       sta ui_bc
        txa
        asl
        asl
        adc #<ne_box            ; (C=0: asl di un valore < 3)
        pha
        lda #>ne_box
        adc #0
        tax
        pla
        ldy #4
        jsr ui_boxes
        ldx tmp3
        inx
        cpx #3
        bne _l
        lda #UC_BOX
        sta ui_bc
        jsr ui_labels
        .byte 6,2
        .text " name "
        .byte 0,6,6
        .text " seed "
        .byte 0,$ff
        rts
ne_box  .byte 4,2,32,4, 4,6,32,4, 4,10,32,3

name_draw:
        jsr ne_boxes
        lda #0
        sta ui_fc
        #at 6,3
        lda #$20
        ldx nfield
        bne _m1
        lda #$3e
_m1     jsr ui_putc
        #at 6,7
        lda #$20
        ldx nfield
        cpx #1
        bne _m2
        lda #$3e
_m2     jsr ui_putc
        #at 6,11
        lda #$20
        ldx nfield
        cpx #2
        bne _m3
        lda #$3e
_m3     jsr ui_putc
        lda #$ff                ; cursore solo mentre si scrive
        ldx nedit
        beq _c0
        ldx nfield
        bne _c0
        lda nlen2
_c0     sta fcur
        #at 8,3
        lda #7                  ; testo digitato: giallo
        sta ui_col
        ldx #0
_l      stx tmp3
        cpx nlen2
        bcc _ch
        cpx fcur
        beq _cur
        lda #$2e
        jmp _p
_ch     lda namebuf,x
        jmp _p
_cur    lda #$40                ; inverso = +$40 nel charset UI
        sta inv
        lda #$20
        jsr ui_putc
        lda #0
        sta inv
        jmp _n
_p      jsr ui_putc
_n      ldx tmp3
        inx
        cpx #NAME_LEN
        bne _l
        rts

seed_draw:
        lda #$ff
        ldx nedit
        beq _c0
        ldx nfield
        cpx #1
        bne _c0
        lda slen
_c0     sta fcur
        #at 8,7
        lda #7
        sta ui_col
        ldx #0
_l      stx tmp3
        cpx slen
        bcc _ch
        cpx fcur
        beq _cur
        lda #$2e
        jmp _p
_ch     lda seedbuf,x
        cmp #10
        bcs _a
        adc #$30
        bne _p
_a      sbc #9
        jmp _p
_cur    lda #$40
        sta inv
        lda #$20
        jsr ui_putc
        lda #0
        sta inv
        jmp _n
_p      jsr ui_putc
_n      ldx tmp3
        inx
        cpx #6
        bne _l
        rts

char_add:                       ; A = codice tasto; aggiunge al campo attivo (Y preservato)
        ldx nfield
        bne _sd
        jmp name_add
_sd     cpx #2                  ; sul pulsante start i tasti non scrivono
        beq _r
        cmp #$20
        bcs _dg
        clc
        adc #9                  ; a-z (1..26) -> 10..35
        bne _st
_dg     cmp #$31                ; '0' escluso (confusione con la O)
        bcc _r
        cmp #$3a
        bcs _r
        sec
        sbc #$30
_st     pha
        lda sfresh
        beq _ap
        lda #0                  ; primo carattere dopo l'ingresso nel campo: riparte da zero
        sta slen
        sta sfresh
_ap     pla
        ldx slen
        cpx #6
        bcs _r
        sta seedbuf,x
        inc slen
_r      rts

NE_ERR  = 14                    ; riga del messaggio "name already in use."
nedit   .byte 0                 ; 1 = si scrive il campo nfield, 0 = scelta con joystick/W-S (dopo il seed)
tt_new  .text "new barbarian", 0
name_entry:
        lda #0
        sta nlen2
        ldx #15
        lda #$20
_c      sta namebuf,x
        dex
        bpl _c
        jsr ui_begin
.if TESTUI == 31
        ldx #NAME_LEN-1         ; screenshot: nome di prova gia' scritto
-       lda tu_name,x
        sta namebuf,x
        dex
        bpl -
        lda #NAME_LEN
        sta nlen2
.endif
        lda #0
        sta nfield
        lda #1                  ; si parte scrivendo il nome
        sta nedit
        lda rnd                 ; mescola il PRNG col tempo (seed iniziale casuale)
        eor frame
        sta rnd
        lda rnd+1
        eor $d012
        sta rnd+1
        ora rnd
        bne _rok
        inc rnd
_rok    jsr seed_roll
        lda #<tt_new            ; (09/11) standard: titolo, tre riquadri (ne_boxes), suggerimento nel riquadro seed
        ldx #>tt_new
        ldy #CH_SWORD
        jsr ui_title
        #at 27,8
        lda #UC_HELP
        sta ui_col
        #msg "a-z 1-9"
        #at 8,11
        lda #1
        sta ui_col
        #msg "start"
        #at 1,23
        #msg "f1:random seed"
        #at 1,24
        #msg "enter:confirm  run/stop:exit"
_dr     jsr name_draw
        jsr seed_draw
.if TESTUI == 31
_hg     jmp _hg                 ; screenshot
.endif
_in     jsr ui_input
        jsr rand
        lda keynew+7            ; RUN/STOP: esce
        and #$80
        beq _a2
        lda #0
        rts
_a2     lda keynew
        and #$10                ; F1: nuovo seed casuale (sempre)
        beq _a
        jsr seed_roll
        jmp _dr
_a      lda nedit
        bne _a3
        ; --- scelta (09/11): dopo il seed il cursore si muove fra nome, seed e start SOLO con joystick o W/S
        ;     (regola: ci si muove con WASD o joystick); fire/spazio/RETURN su start crea, su nome o seed lo riapre
        lda joynew
        lsr
        bcs _up
        lsr
        bcs _dw
        jsr ui_fire
        beq _ign
        lda nfield
        cmp #2
        bne _ed
        lda #1                  ; start: nome e seed sono gia' stati validati
        rts
_ed     inc nedit               ; si riscrive il campo: da qui la logica riparte (ENTER valida e passa al campo dopo)
        lda #1
        sta sfresh
        jmp _dr
_up     lda nfield
        beq _ign
        dec nfield
        jmp _dr
_dw     lda nfield
        cmp #2
        beq _ign
        inc nfield
        jmp _dr
_ign    jmp _in
        ; --- scrittura del campo nfield (0 nome, 1 seed): lettere, DEL, ENTER (nessun tasto di movimento)
_a3     lda keynew
        and #$01
        beq _b
        lda nfield
        beq _dn
        lda slen
        beq _ign
        dec slen
        lda #0
        sta sfresh
        jmp _dr
_dn     lda nlen2
        beq _ign
        dec nlen2
        ldx nlen2
        lda #$20
        sta namebuf,x
        ldy #NE_ERR
        jsr clear_row
        jmp _dr
_b      lda keynew
        and #$02
        beq _chars
        jmp _confirm
_chars  ldy #1
_r      lda keynew,y
        beq _nr
        sta tmp2
        tya
        asl
        asl
        asl
        sta tmp4
        ldx #0
_bt     lsr tmp2
        bcc _nb
        txa
        clc
        adc tmp4
        stx tmp5
        tax
        lda keymap,x
        ldx tmp5
        cmp #0                  ; flag sul codice tasto (non su X)
        beq _nb
        jsr char_add
        tya
        pha
        ldy #NE_ERR
        jsr clear_row
        pla
        tay
        ldx tmp5
_nb     inx
        cpx #8
        bne _bt
_nr     iny
        cpy #8
        bne _r
        jmp _dr
_confirm                        ; ENTER (09/11): valida il campo e passa al dopo: nome -> seed -> scelta su start
        lda nfield
        bne _seed
        jmp _name
_seed   lda slen                ; seed: 6 caratteri
        cmp #6
        bcc _ig2
        lda #2                  ; cursore su start, fine della scrittura
        sta nfield
        lda #0
        sta nedit
        jmp _dr
_ig2    jmp _in
_name   ldx #NAME_LEN-1         ; nome: non vuoto (non di soli spazi) e non gia' usato
_ns     lda namebuf,x
        cmp #$20
        bne _sok
        dex
        bpl _ns
        bmi _ig2
_sok    ldx #0                  ; slot
_sl     lda slot_valid,x
        beq _nx
        txa
        asl
        asl
        asl
        asl
        tay
        ldx #0
_cm     lda namebuf,x
        cmp slot_name,y
        bne _diff
        iny
        inx
        cpx #NAME_LEN
        bne _cm
        ; uguale
        #at 10,14
        #msg "name already in use."
        jmp _in                 ; il cursore resta sul nome
_diff   ; ripristina indice slot
        tya
        and #$f0
        lsr
        lsr
        lsr
        lsr
        tax
_nx     inx
        cpx #5
        bne _sl
        inc nfield              ; nome valido: si scrive il seed (il primo tasto lo fa ripartire)
        lda #1
        sta sfresh
        jmp _dr

        .enc "none"

; ------------------------------------------------------------------ quit the game
; Disinstalla Krill's Loader (il drive torna alla sua ROM: reset del drive, provato in VICE l'11/11: dopo, il KERNAL
; legge di nuovo il disco), poi reset del KERNAL (jmp ($fffc)): BASIC (READY.), pagine 2-3 reinizializzate. Nessun
; rientro nel gioco (SYS 49158 tolto l'11/11).
bb_quit:
        sei
        jsr krill_uninstall
        sei
        lda #$37
        sta $01
        jmp ($fffc)

; ------------------------------------------------------------------ back to main menu (16/11, committente)
; Come lore_exit (src/lore/scroll.asm): Krill disinstallato (il drive torna alla sua ROM), pagine 2-3 azzerate (il residente
; le ha sporcate: con le variabili RS-232 sporche il KERNAL si blocca), poi il trampoline ricarica BARBARIAN con il KERNAL.
bb_menu:
        sei
        lda #0
        sta $d01a               ; niente raster IRQ ne' sprite
        sta $d015
        sta $d418               ; SID muto (la musica del menu e' del player del gioco)
        lda #$ff
        sta $d019
        lda #$0b
        sta $d011
        jsr krill_uninstall
        sei
        lda #0
        tax
_bz     sta $0200,x
        sta $0300,x
        inx
        bne _bz
        lda #4                  ; pagina dello schermo del KERNAL
        sta $0288
        lda #$37
        sta $01
        ldx #<bm_name
        ldy #>bm_name
        lda #bm_name_n
        jmp tramp_run
bm_name .text "barbarian"
bm_name_n = * - bm_name
        .include "tramp.inc"
menu_end
        .cerror menu_end > MAP + $1000, "modulo menu oltre $CFFF"
        .cerror menu_end > $cc00, "LOBBY oltre $CBFF: copre lo schermo del titolo durante il caricamento (src/barbarian.asm)"
