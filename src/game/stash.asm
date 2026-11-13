; ===================================================================
;  baule di casa: spostamenti, ordinamento, messaggi (08/11: dal modulo della locanda; la schermata e' in src/menu/inn.asm)
; ===================================================================
; il baule (st_id, st_b, st_du, st_m) sta nel blocco dell'eroe (CHRBLK, src/game/game.asm, 08/11 sera)

; messaggi: riga 23 in rosso chiaro
h_msg:  jsr h_msgclr
        #at 1,23
        lda #10
        sta ui_col
        rts
h_msgclr:
        ldy #23
        jmp clear_row


st_sort lda #<sd_st
        ldx #>sd_st
        jmp sort4
sd_st   .byte STASH_N
        .word st_id, st_b, st_du, st_m

; ---- modulo MENU (11/11, TODO D6/D13): i menu del villaggio (locanda e negozi, src/menu.asm) in due zone di RAM,
;  compressi ZX0 in un file. Si carica all'ingresso nel villaggio (enter_gfx) se non c'e' (ovl_cur = 0: lo azzerano
;  game_start e il LOBBY, che copre la zona 1) e poi resta: niente altro scrive nelle due zone.
;  File "menu1".."menu3" (tools/build/pack_menu.py, docs/FORMATO_DATI.md; 11/11 ramo fast-loader: un file per parte):
;  ogni parte compressa ha come indirizzo di caricamento (ml_end - lunghezza), cioe' il fondo della sua zona;
;  Krill la carica li' (C=0) e lascia l'inizio in krill_loadaddrlo/hi; poi si decomprime sul posto all'inizio
;  della zona (ml_dst): pack_menu.py verifica che la scrittura non raggiunga i dati non ancora letti.
MR1_AT  = $c900                 ; zona 1: $C900-$CFFF (la mappa finisce a $C8FF; il LOBBY arriva a $CBFF)
MR1_END = $d000
MR2_AT  = GFX_DUN_AT+4*GFX_DSTRIP+GFX_MONS+GFX_STRONG   ; zona 2: dopo la cache del tema ($F4E0), sotto il KERNAL
MR2_END = PF_END                ; ($FD00: FMAP)
MR3_AT  = $a700                 ; zona 3: slot sprite 28-31 del banco VIC 2, liberi nel gioco (out/memory-map/mappa_ram.html)
MR3_END = $a800                 ; (charset del gioco)
MPARTS  = 3
OVL_AT  = MR1_AT                ; tabella dei salti del modulo (src/menu.asm)
MENU_INN  = OVL_AT              ; locanda
MENU_SHOP = OVL_AT+3            ; negozio A (0 fabbro, 1 alchimista) (jsr mk_off + jmp enter_shop: 6 B)
ml_src  = $5c                   ; (pagina zero libera dopo ZX_ZP) inizio dei dati compressi di ogni parte
ml_i    = ml_src+2*MPARTS

; carica il modulo se non c'e' (ovl_cur = 0). C=1 se non si puo' caricare (il chiamante non salta nel modulo)
ovl_town:
        lda ovl_cur
        beq ml_read
        clc
        rts
ml_read:                        ; (lettura dei file MENU1..3: la contano i test)
        lda #2                  ; schermata "loading..." generica
        sta io_what
        ldy #nm_menu-nm_tab
        jsr set_name4           ; "menu" + cifra in cmdbuf+7, 0 finale in cmdbuf+8
        lda #0
        sta cmdbuf+8
        ldx #0
_p      stx ml_i
        txa
        lsr
        clc
        adc #$31                ; "1".."3"
        sta cmdbuf+7
        jsr load_file           ; all'indirizzo del file (fondo della zona)
        bcs _r
        ldx ml_i
        lda krill_loadaddrlo
        sta ml_src,x
        lda krill_loadaddrhi
        sta ml_src+1,x
        lda #1
        sta io_quiet            ; la schermata una volta sola
        inx
        inx
        cpx #2*MPARTS
        bne _p
        lda #0
        sta io_quiet
        php                     ; decompressione con il KERNAL escluso (la zona 2 e' nella RAM sotto il KERNAL)
        sei
        lda #<nmi_stub          ; (RESTORE: vettore NMI nella RAM sotto il KERNAL)
        sta $fffa
        lda #>nmi_stub
        sta $fffb
        lda #$35
        sta $01
        ldx #0
_u      stx ml_i
        lda ml_src,x
        sta zx_src
        lda ml_src+1,x
        sta zx_src+1
        lda ml_dst,x
        sta zx_dst
        lda ml_dst+1,x
        sta zx_dst+1
        jsr zx0_unpack
        ldx ml_i
        inx
        inx
        cpx #2*MPARTS
        bne _u
        lda #$36
        sta $01
        plp
        inc ovl_cur
        clc
        rts
_r      lda #0
        sta io_quiet
        sec
        rts
ml_end  .word MR1_END, MR2_END, MR3_END   ; (pack_menu.py: indirizzo di ogni file = fine zona - lunghezza)
ml_dst  .word MR1_AT, MR2_AT, MR3_AT

ZX_ZP   = $50                   ; 12 byte della pagina zero del BASIC, liberi nel gioco (come in START, boot.asm)
        .include "zx0.inc"
