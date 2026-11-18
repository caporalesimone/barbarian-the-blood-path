; ===================================================================
;  chapter.asm - sequenza dei capitoli (12/11, TODO M1; docs/wiki/capitoli.md)
;  Ogni capitolo c = 1..CHAPTERS ha il suo villaggio (file TWNc, cur_level = 0) e CH_LV piani: i primi CH_LV-1
;  generati, l'ultimo e' il piano del boss del capitolo (mappa fissa BOSSCHc, segnaposto; nel capitolo CHAPTERS e' il
;  piano finale MAXLEVEL, la sala del trono). I piani si contano internamente da 1 a MAXLEVEL (profondita' globale:
;  decide la difficolta'). c_chap = capitolo in cui si gioca, c_unl = capitolo piu' alto sbloccato: uccidere il boss
;  del capitolo c sblocca c+1, e nel villaggio l'uscita (caselle "=" di data/town_map.txt, tx_exit) porta al villaggio
;  del capitolo dopo (Fire: musica sfumata, schermo nero, salvataggio di eroe e piani, villaggio nuovo).
; ===================================================================
lv_cboss .byte 0                ; 1 = il piano attuale e' quello del boss di un capitolo (non l'ultimo): load_location
bm_hdr                          ; intestazione del file BOSSCHc (tools/build/gen_bossmap.py): scale di arrivo e boss
bm_sx   .byte 0
bm_sy   .byte 0
bm_bx   .byte 0
bm_by   .byte 0

; A = capitolo 1.. -> A = suo primo piano ((c-1)*CH_LV + 1). Usa tmp7.
chap_first:
        sec
        sbc #1
        sta tmp7
        asl
        asl
        adc tmp7                ; x5
        .cerror CH_LV != 5, "chap_first: moltiplicazione per CH_LV = 5"
        adc #1
        rts

; A = piano -> C = 1 se e' il piano del boss di un capitolo (ultimo del gruppo di CH_LV, ma non MAXLEVEL). Usa X, tmp7.
is_cboss:
        cmp #MAXLEVEL
        bcs _no
        jsr lv_grp
        cpx #CH_LV-1
        bne _no
        sec
        rts
_no     clc
        rts

; all'ingresso in un piano (load_location, prima di gen_dungeon)
chap_enter:
        lda #0
        sta lv_cboss
        lda cur_level
        beq _r
        jsr is_cboss
        rol lv_cboss
_r      rts

; morte del boss del capitolo (kill_monster): il capitolo dopo e' sbloccato
chap_won:
        lda cur_level
        jsr lv_grp              ; A = capitolo
        cmp c_unl
        bcc _r
        adc #0                  ; (C = 1) c + 1
        sta c_unl
        lda #5
        ldx #25
        jmp set_flash
_r      rts

; C = 1 se il PG (ptx, pty) e' su una casella di uscita del villaggio (tx_exit, out/work/town_places.inc)
at_exit:
        lda cur_level
        bne _no
        ldx #TX_EXIT_N-1
_l      lda tx_exit_x,x
        cmp ptx
        bne _n
        lda tx_exit_y,x
        cmp pty
        bne _n
        sec
        rts
_n      dex
        bpl _l
_no     clc
        rts

; C = 1 se il PG e' sull'uscita e il capitolo dopo e' sbloccato (c_unl > c_chap)
exit_open:
        jsr at_exit
        bcc _r
        lda c_chap
        cmp c_unl               ; C = 1 se c_chap >= c_unl: chiuso
        bcs _no
        sec
        rts
_no     clc
_r      rts

; Fire sull'uscita aperta: al villaggio del capitolo dopo. (1) musica sfumata, (2) schermo nero, (3) eroe e piani del
; capitolo sul disco (gia' come capitolo nuovo, all'ingresso sud del villaggio: "continue" riparte da li'),
; (4) villaggio nuovo (change_level, arrivo dalla strada a sud come una partita nuova)
chap_travel:
        jsr scr_black
        inc c_chap
        lda #0                  ; (15/11) il villaggio nuovo si legge gia' qui: il suo ingresso (tk_nx, tk_ny) serve prima
        jsr load_gfx            ; del salvataggio ("continue" riparte da li')
        lda #0
        jsr gfx_install
        lda tk_nx
        ldx tk_ny
        jsr put_hero
        jsr tod_tick
        jsr chap_savef
        lda #0
        ldx #4
        jmp change_level
