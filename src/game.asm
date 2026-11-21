; ===================================================================
;  BARBARIAN: THE BLOOD PATH  -  hack & slash per Commodore 64 (64tass)
; ===================================================================
        .cpu "6502"

; Il PRG parte a $0400 (lo schermo del BASIC: il VIC lavora nel banco 2 e il BASIC non gira): il loader
; (src/barbarian.asm) lo legge byte per byte dal suo indirizzo e salta a GAME_ENTRY. Niente stub BASIC.
GAME_ENTRY = $0400
        * = GAME_ENTRY
        jmp start

        .include "krill.inc"     ; out/work/krill.inc: indirizzi di Krill's Loader (tools/build/krill_syms.py)

; ------------------------------------------------------------------ hardware
SPR_X      = $d000
SPR_MSB    = $d010
VIC_CTRL1  = $d011
VIC_RASTER = $d012
SPR_EN     = $d015
VIC_CTRL2  = $d016
SPR_YEXP   = $d017
VIC_MEM    = $d018
SPR_PRIO   = $d01b
SPR_MC     = $d01c
SPRMC      = %11111001      ; multicolor: eroe (0), mostri (3..6), NPC del villaggio (3..7; 17/11: il 7 era hires)
SPR_XEXP   = $d01d
BORDER     = $d020
BGCOL      = $d021
BGCOL1     = $d022
BGCOL2     = $d023
SPR_MC0    = $d025
SPR_MC1    = $d026
SPR_COL    = $d027
CIA1_PRA   = $dc00
CIA1_PRB   = $dc01
COLRAM     = $d800

SCR_A      = $b400
SCR_B      = $bc00
SCR_H      = $8400          ; schermo fisso della fascia HUD (righe 20..23)
SPR_DATA   = $a000
CHARSET    = $a800

MAP        = $c000          ; 48x48 tile
LOBBY_AT    = $c000          ; modulo LOBBY (file, menu iniziale): usa la RAM della mappa, che nel menu non serve

; ---- (15/11, TODO T1) annotazioni della mappa automatica della memoria (lab64 map, docs/wiki/build.md sezione 4a; sintassi in
; docs/memory-maps.md di Lab64): "@map" = zone che il gioco scrive solo con puntatori o copie (invisibili all'analisi statica: contano come
; usate); "@free" = memoria libera e cosa ci puo' stare; "@scenario" = cosa e' in memoria insieme (moduli e file del disco).
;@map $8720..$87e8 "Schermo HUD: righe 20-24 di SCR_H (il VIC mostra solo queste, split raster)"
;@map $87e8..$87f8 "Fra schermo HUD e puntatori sprite: all'avvio grafica fissa del PRG" free-after=start
;@map $87f8..$8800 "Puntatori sprite della fascia HUD"
;@map $8800..$8a40 "Sprite della barra, set A (doppio buffer con $B000) e segnaposto della minimappa"
;@map $8c00..$8e80 "Sprite forti + boss del tema (640 B dal file GFXn, gfx_install)"
;@map SPR_DATA..$a500 "Sprite 0-19: eroe e fendenti (copy_gfx), mostri del tema (file GFXn; nel tema 8 slot 12-13 stella e cerchio)"
;@map $a600..$a6c0 "Sprite 24-26: HUD, segnaposto, anello (copy_gfx)"
;@map CHARSET..$b000 "Charset del gioco: 4 quarti da $200, tile del luogo (file TWNc / GFXn) + caratteri fissi (copy_gfx)"
;@map $b000..SCR_A "Sprite della barra, set B; nella minimappa del villaggio $B000-$B2FF sono i nomi delle case (mm_names)"
;@map SCR_A..$b800 "Schermo A del gioco; nelle UI (inventario, negozi, baule, menu) e nella minimappa lo schermo della schermata ($D018=$DE)"
;@map $b800..SCR_B "Font della UI (copy_gfx)"
;@map SCR_B..$c000 "Schermo B del gioco (doppio buffer con lo schermo A; ridisegnato all'uscita da una UI)"
;@map MAP..$c900 "MAP: mappa 48x48 del luogo (villaggio scompattato dalla cache, dungeon rigenerato dal seed)" scenario=villaggio,dungeon,salvataggio
;@map $d000+67 "CHRBUF: elenco eroi letto da START (file hl), il menu iniziale lo legge senza disco" scenario=menu-iniziale
;@scenario menu-iniziale: game lobby hl ; elenco eroi e creazione: LOBBY a $C000 sopra MAP, MENU non ancora caricato
;@scenario villaggio: game menu twn? ; MENU nelle sue tre zone ($C900, $A700, sotto il KERNAL), un villaggio nella cache a $E000
;@scenario dungeon: game menu gfx? fmap|bossch? ; il tema del capitolo copre la coda del villaggio; mappa del boss del capitolo o sala del trono a $FD00
;@scenario salvataggio: game menu ksave save-?? ; save game: immagine del file a $E000 e plugin di save di Krill (la cache del villaggio si rilegge)
;@map $87e8..$87f5 "Variabili di grotte e cittadella (gen_io.asm, 19/11: fuori dalla RAM sotto l'I/O)"
;@free $87f5..$87f8 "Fra schermo HUD e puntatori sprite (banco VIC)" use=data
;@map $a5e3..$a5fb "Variabili della palude (gen_io.asm, 19/11: fuori dalla RAM sotto l'I/O)"
;@free $a5fb..$a600 "Coda degli slot sprite 20-23 (il resto: ricerca di percorso dei mostri, mon_path)" use=data
;@free $fe96..$fffa "Fondo della cache sotto il KERNAL, dopo FMAP (si accorcia se FMAP cresce: lo dice questa verifica)" use=data
;@map $a6c0..$a6fc "Minimappa: tabella delle classi dei tile (mm_cls, 48 B) e byte esplorati della riga di celle (mm_ex, 12 B), solo mentre la minimappa e' aperta (ui.asm); il resto dello slot 27 riceve la coda della copia di copy_gfx (byte senza uso)"
;@free $a6fc..$a700 "Fine dello slot sprite 27" use=data
TOWN_MAX   = $0760          ; (15/11) intestazione + mappa RLE del villaggio (nel file TWNc dopo i tile); (21/11) file da GFX_TOWN_AT = $EC00 fino a $F900
                            ; (il file del tema comincia GFX_INFO byte prima: villaggio e dungeon non sono mai in RAM insieme)
MAPW       = 48
MAPH       = 48


; ------------------------------------------------------------------ zero page
        .virtual $02
tmp0       .byte ?
tmp1       .byte ?
tmp2       .byte ?
tmp3       .byte ?
tmp4       .byte ?
tmp5       .byte ?
tmp6       .byte ?
tmp7       .byte ?
ptr0       .word ?
ptr1       .word ?
ptr2       .word ?
ptr3       .word ?
rnd        .word ?
px         .word ?
py         .word ?
camx       .word ?
camy       .word ?
cam_cx     .byte ?
cam_cy     .byte ?
hx         .byte ?
hy         .byte ?
drawn_cx   .byte ?
drawn_cy   .byte ?
front      .byte ?
pend_flip  .byte ?
force_redraw .byte ?
ent_x      .word ?
ent_y      .word ?
sa_x       .word ?
sa_y       .word ?
tx         .byte ?
ty         .byte ?
frame      .byte ?
joy        .byte ?
joyold     .byte ?
joynew     .byte ?
scr_ptr    .word ?
cp         .word ?
cidx       .byte ?
inv        .byte ?
ccp        .word ?          ; puntatore color RAM per ui_putc
ui_cur     .byte ?          ; (11/11: qui dalla RAM $94xx, istruzioni piu' corte) motore dei menu: voce del cursore
ui_n       .byte ?          ; voci
ui_col     .byte ?          ; colore del testo (ui_putc)
ui_ib      .byte ?
ui_sel     .byte ?
ui_lc      .byte ?          ; voce della lista con il cursore ($FF = cursore sulle linguette): per i disegni
zp_end
        .endv
        .cerror zp_end > $50, "pagina zero del gioco oltre $4F (da $50: ZX_ZP, menu)"
        .cerror zp_end > krill_loader_zp_first, "pagina zero del gioco sopra quella di Krill ($41-$47; $41-$57 nel save)"

; ------------------------------------------------------------------ variabili (non zp)
        .virtual $9000
cur_level  .byte ?
rx         .fill 16
ry         .fill 16
rw         .fill 16
rh         .fill 16
rcx        .fill 16
rcy        .fill 16
vis        .fill 16
stk        .fill 16
cand       .fill 4
sp_        .byte ?
ncand      .byte ?
cur        .byte ?
cc_a       .byte ?
sd_n       .byte ?          ; (19/11) numero mescolato al seed da seed_mix (piano o confine della palude)
ci_try     .byte ?          ; (18/11) tentativi del baule in una stanza (chest_in_room)
sw_in      .byte ?          ; (18/11) palude: lato del cancello d'ingresso (0 nord, 1 est, 2 sud, 3 ovest; gen_io.asm swamp_gates)
sw_out     .byte ?          ; lato del cancello d'uscita
cc_b       .byte ?
ch_y       .byte ?
ch_x0      .byte ?
ch_x1      .byte ?
st_up_x    .byte ?
st_up_y    .byte ?
st_dn_x    .byte ?
st_dn_y    .byte ?
st_s       .byte ?
st_e       .byte ?
tmpv       .byte ?
rr_n       .byte ?
rr_a       .byte ?
pdx        .byte ?
pdy        .byte ?
pdir       .byte ?
panim      .byte ?
pstep      .byte ?
nx         .word ?
st_d       .byte ?
st_nz      .byte ?              ; 1 = passo di aggiustamento sugli spigoli in corso (niente ricorsione)
st_pb      .byte ?              ; sonde bloccate: bit 0 = prima (lato -), bit 1 = seconda (lato +)
; ombre sprite
sh_x       .fill 8
sh_y       .fill 8
sh_ptr     .fill 8
sh_col     .fill 8
sh_msb     .byte ?
sh_en      .byte ?
bs_en      .byte ?              ; shadow in costruzione (vedi build_sprites)
bs_msb     .byte ?
sh_xexp    .byte ?
sh_yexp    .byte ?
keyrows    .fill 8
keyprev    .fill 8
keynew     .fill 8
rs_n1      .byte ?
rs_n2      .byte ?
rs_r       .byte ?
scr_cnt    .byte ?
scr_key    .byte ?
pf_valid   .byte ?          ; 1 = il buffer nascosto e' in preparazione per (pf_cx,pf_cy)
pf_cx      .byte ?
pf_cy      .byte ?
pf_step    .byte ?          ; passi gia' eseguiti (0..13)
pf_oddy    .byte ?
pf_tot     .byte ?
pf_p0      .word ?
pf_p1      .word ?
pf_n1      .byte ?
pf_n2      .byte ?
rc_cnt     .byte ?
pf_tx      .byte ?
pf_ty      .byte ?
rd_sync    .byte ?          ; (19/11) maybe_redraw: ridisegno completo in questo fotogramma (npc_draw, quest.asm)
npc_enm    .byte ?          ; (19/11) sprite e bit alti degli NPC dell'ultimo npc_draw completo
npc_msbm   .byte ?
main_vend
        .endv
        .cerror main_vend > $9100, "variabili di main.asm oltre $90FF"

; ------------------------------------------------------------------ avvio
start:
        sei
        cld
        ldx #$ff
        txs
        lda #$36
        sta $01
        jsr copy_gfx            ; per prima: la coda del PRG copre $8000-$9FFF
        lda #$7f
        sta $dc0d
        sta $dd0d
        lda $dc0d
        lda $dd0d
        lda #0
        sta $d01a
        sta SPR_EN
        jsr irq_init            ; (21/11) anche i vettori della CPU sotto il KERNAL (IRQ, NMI), poi il KERNAL esce per sempre
        lda #MEMCFG
        sta $01
        lda #$ff
        sta $dc02
        sta $dc00
        lda #$00
        sta $dc03
        lda $dd02
        ora #3
        sta $dd02
        lda #$01                ; banco VIC 2. Con Krill installato i 6 bit alti di $DD00 vanno scritti a 0
        sta $dd00               ; (niente lettura-modifica: README di Krill, "Setting the VIC bank")
        jsr init_vic
        jmp game_start

; NMI (RESTORE): nessun effetto (vettori $FFFA/$FFFB e $0318, irq_init)
nmi_stub:
        rti

; Segnale lasciato da START (src/common/boot.asm) in pagina zero (11/11, ramo fast-loader: la pagina 2 e' del
; residente di Krill; $41-$57 sono di Krill e del suo plugin): 1 = LOBBY gia' a $C000 (si consuma al primo menu_run).
; $8F = CHRPRE (src/lobby.asm).
LDFLAGS = $8e
; (21/11, TODO D15) configurazione di memoria del gioco, sempre: KERNAL escluso (RAM a $E000-$FFFF), I/O visibile, BASIC escluso.
; Il KERNAL non serve piu' dopo START (Krill non lo usa, tastiera e IRQ sono del gioco); $37 solo per "quit" e il ritorno a BARBARIAN
MEMCFG  = $35

; build arena (tools/vice/arena.py): ARENA=1 -> out/work/arena_game.prg + modulo out/work/arena.prg a AR_BASE
        .weak
ARENA = 0
        .endweak
OVP_RES = ARENA || (TESTUI == 36)   ; (19/11) codice del piano 20 in GAME (theme.asm, src/game/final.asm)
AR_BASE  = $c900                ; tabella di salto del modulo arena (src/test/arena.asm), RAM libera dopo MAP
AR_MAIN  = AR_BASE              ; avvio (da game_start)
AR_INPUT = AR_BASE+3            ; ogni fotogramma (da read_input): bot -> joy, fine combattimento
AR_KILL  = AR_BASE+6            ; mostro ucciso (tmp0/tmp1 = esperienza), al posto di add_xp
AR_DEAD  = AR_BASE+9            ; PG morto, al posto di player_die
AR_WAIT  = AR_BASE+12           ; al posto di wait_vblank (modalita' veloce)

; copia la grafica dal PRG alle destinazioni nel banco VIC 2. Va chiamata PRIMA di ogni altra
; scrittura in RAM: il PRG puo' arrivare fino a $9FFF e la sua coda (dato morto dopo la copia)
; copre schermo HUD, sprite barra e variabili a $9000. Ordine: prima i blocchi con destinazione
; sopra $A000 (nessuna sovrapposizione col PRG), per ultimo sprites2 -> $8C00, la cui sorgente
; e' all'inizio di gfx_data (sotto $8C00), mentre la destinazione puo' coprire sorgenti gia' copiate.
copy_gfx:
        lda #<gen_img           ; (21/11) generatore compresso ZX0 -> RAM sotto l'I/O (gen_io.asm); prima di tutto: la
        sta zx_src              ; sorgente sta dove poi andranno le variabili ($9000). Compresso da tools/build/gen_imgz.py
        lda #>gen_img           ; (asm.sh, due passate): il PRG e' ~1 KB piu' corto e GAME resta sotto $9C00 (CODE2)
        sta zx_src+1
        lda #<GEN_AT
        sta zx_dst
        lda #>GEN_AT
        sta zx_dst+1
        php
        sei
        lda #$34
        sta $01
        jsr zx0_unpack
        lda #$36
        sta $01
        plp
        lda #3                  ; sprite 0..11: $A000-$A2FF
        sta tmp7
        lda #<gd_core
        ldx #>gd_core
        ldy #$a0
        jsr cp_pages
        lda #1                  ; sprite 24..26: $A600 (la coda della pagina finisce nello slot 27, inutilizzato)
        sta tmp7
        lda #<(gd_core+768)
        ldx #>(gd_core+768)
        ldy #$a6
        jsr cp_pages
        lda #<gd_fchr           ; caratteri fissi: in ogni quarto del charset, dopo i tile (15/11, D12: un ciclo, non 4 copie;
        sta ptr0                ; cp_n lascia ptr0 sulla striscia successiva e ptr1 a fine striscia)
        lda #>gd_fchr
        sta ptr0+1
        lda #<(CHARSET+GFX_TSTRIP)
        sta ptr1
        lda #>(CHARSET+GFX_TSTRIP)
        sta ptr1+1
        ldx #3
_fq     lda #<GFX_FSTRIP
        sta tmp6
        lda #>GFX_FSTRIP
        sta tmp7
        jsr cp_n                ; (preserva X)
        lda ptr1                ; prossimo quarto: +$200 meno la striscia appena scritta
        clc
        adc #<($200-GFX_FSTRIP)
        sta ptr1
        lda ptr1+1
        adc #>($200-GFX_FSTRIP)
        sta ptr1+1
        dex
        bpl _fq
        lda #4                  ; font UI: $B800
        sta tmp7
        lda #<gd_font
        ldx #>gd_font
        ldy #$b8
        jmp cp_pages

; ptr0 -> ptr1, tmp6/tmp7 = numero di byte (16 bit)
cp_n:
        ldy #0
_l      lda tmp6
        ora tmp7
        beq _e
        lda (ptr0),y
        sta (ptr1),y
        inc ptr0
        bne +
        inc ptr0+1
+       inc ptr1
        bne +
        inc ptr1+1
+       lda tmp6
        bne +
        dec tmp7
+       dec tmp6
        jmp _l
_e      rts

; RLE: ptr0 -> ptr1 fino a 48*48 byte. b < $C0 = tile; b >= $C0: ripete il byte seguente (b & $3F) + 2 volte
rle_unpack:
        lda #<(MAP+48*48)
        sta tmp6
        lda #>(MAP+48*48)
        sta tmp7
_l      ldy #0
        lda (ptr0),y
        cmp #$c0
        bcc _one
        and #$3f
        clc
        adc #2
        tax
        iny
        lda (ptr0),y
        jsr _adv
_r      sta (ptr1),y
        iny
        dex
        bne _r
        tya
        clc
        adc ptr1
        sta ptr1
        bcc _ck
        inc ptr1+1
        bne _ck
_one    ldy #0
        sta (ptr1),y
        inc ptr1
        bne +
        inc ptr1+1
+
_ck     jsr _adv
        lda ptr1+1
        cmp tmp7
        bcc _l
        lda ptr1
        cmp tmp6
        bcc _l
        rts
_adv    inc ptr0                ; un byte di sorgente (preserva A)
        bne +
        inc ptr0+1
+       ldy #0
        rts

; ---- grafica dei luoghi: cache nella RAM sotto il KERNAL ($E000 villaggio, $E600 tema del dungeon)
; installa la grafica in cache: A = 0 villaggio, altro = dungeon (tile + sprite, colori e nomi dei mostri del capitolo)
        .cerror GFX_INFO > 256 || (>NM_AT) != (>(NM_AT+GFX_INFO-1)), "blocco info dei mostri (NM_AT) a cavallo di una pagina"
;@free npc_vend..NM_AT-1 "Coda degli slot sprite 58-63 (fino al blocco info dei mostri), dopo le variabili di quest.asm" use=data
;@map NM_AT..$9000 "Colori e nomi dei mostri del capitolo: blocco info del file GFXn copiato da gfx_install"
        .cerror SND_FBUF + SND_FMAX > NM_AT || NM_AT + GFX_INFO > $9000, "NM_AT sovrapposto al motivetto di combattimento o oltre $8FFF"
; A = 0 villaggio, altro = dungeon: dalla cache sotto il KERNAL installa tile (4 strisce del charset), intestazione,
; tile solidi, colori e mappa del villaggio; nel dungeon sprite dei mostri, sprite forti e boss ($8C00), colori e nomi (NM_AT)
gfx_install:
        sta tmp5
        sei
        ldx #0
_q      lda gi_src_lo,x         ; 4 strisce di tile -> charset
        ldy tmp5
        beq +
        lda gi_dsrc_lo,x
+       sta ptr0
        lda gi_src_hi,x
        ldy tmp5
        beq +
        lda gi_dsrc_hi,x
+       sta ptr0+1
        lda #0
        sta ptr1
        txa
        asl
        adc #>CHARSET
        sta ptr1+1
        lda #<GFX_TSTRIP        ; villaggio: tutti i tile; dungeon: solo i suoi (GFX_DSTRIP)
        ldy tmp5
        beq +
        lda #<GFX_DSTRIP
+       sta tmp6
        lda #>GFX_TSTRIP
        ldy tmp5
        beq +
        lda #>GFX_DSTRIP
+       sta tmp7
        stx tmp4
        jsr cp_n
        ldx tmp4
        inx
        cpx #4
        bne _q
        lda tmp5
        bne _dn
        ldy #TK_LEN-1           ; (15/11) villaggio: dopo i tile l'intestazione (posizioni, colori, nome della cura)...
-       lda TK_AT,y
        sta town_k,y
        dey
        bpl -
        ldy #TK_SOLID-1         ; ...e i tile solidi di questo villaggio
-       lda TK_AT+TK_LEN,y
        sta solidtab,y
        dey
        bpl -
        ldy #3
-       lda tk_pal,y            ; colori del villaggio: voce 0 delle tabelle (pal_bg, pal_c1, pal_c2, pal_ram)
        ldx gi_pal,y
        sta pal_bg,x
        dey
        bpl -
        lda #<(TK_AT+TK_LEN+TK_SOLID)   ; poi la mappa (RLE) -> MAP
        sta ptr0
        lda #>(TK_AT+TK_LEN+TK_SOLID)
        sta ptr0+1
        lda #<MAP
        sta ptr1
        lda #>MAP
        sta ptr1+1
        jsr rle_unpack
        jmp _x
_dn     lda #<SPR_DATA+12*64    ; ptr0 prosegue: mostri base -> slot 12..19
        sta ptr1
        lda #>SPR_DATA+12*64
        sta ptr1+1
        lda #<GFX_MONS
        sta tmp6
        lda #>GFX_MONS
        sta tmp7
        jsr cp_n
        lda #$00                ; varianti forti + boss finale -> $8C00
        sta ptr1
        lda #$8c
        sta ptr1+1
        lda #<GFX_STRONG
        sta tmp6
        lda #>GFX_STRONG
        sta tmp7
        jsr cp_n
        lda #<NM_AT             ; (15/11) blocco info del set (colori e nomi dei 9 tipi, tools/build/gen_gfx.py) -> NM_AT
        sta ptr1
        lda #>NM_AT
        sta ptr1+1
        lda #GFX_INFO
        sta tmp6
        lda #0
        sta tmp7
        jsr cp_n
_x      cli
        rts
TK_AT = GFX_TOWN_AT+4*GFX_TSTRIP         ; intestazione del villaggio (TK_LEN + TK_SOLID byte), poi la mappa RLE
gi_pal     .byte 0, pal_c1-pal_bg, pal_c2-pal_bg, pal_ram-pal_bg
gi_src_lo  .byte <(GFX_TOWN_AT+range(4)*GFX_TSTRIP)
gi_src_hi  .byte >(GFX_TOWN_AT+range(4)*GFX_TSTRIP)
gi_dsrc_lo .byte <(GFX_DUN_AT+range(4)*GFX_DSTRIP)
gi_dsrc_hi .byte >(GFX_DUN_AT+range(4)*GFX_DSTRIP)

; A/X = sorgente, Y = pagina di destinazione, tmp7 = pagine
cp_pages:
        sta ptr0
        stx ptr0+1
        sty ptr1+1
        lda #0
        sta ptr1
_pg     ldy #0
_by     lda (ptr0),y
        sta (ptr1),y
        iny
        bne _by
        inc ptr0+1
        inc ptr1+1
        dec tmp7
        bne _pg
        rts

; registri del VIC all'avvio del gioco: bordo e sfondo neri, sprite spenti, multicolor degli sprite (9, 15)
init_vic:
        lda #0
        sta BORDER
        sta BGCOL
        sta SPR_EN
        sta SPR_XEXP
        sta SPR_YEXP
        sta SPR_PRIO
        lda #9
        sta SPR_MC0
        lda #15
        sta SPR_MC1
        lda #SPRMC
        sta SPR_MC
        lda #0
        sta front
        sta pend_flip
        lda #$ff
        sta drawn_cx
        sta drawn_cy
        ; SID: volume massimo
        lda #$0f
        sta $d418
        lda #0
        sta $d402
        lda #8
        sta $d403
        rts

; ------------------------------------------------------------------ palette
; A = indice palette (0 citta', 1..4 dungeon)
set_palette:
        tax
        lda pal_bg,x
        sta BGCOL
        sta bg_cur
        lda pal_c1,x
        sta BGCOL1
        lda pal_c2,x
        sta BGCOL2
        lda pal_ram,x
                                ; (prosegue in col_fill)
; (11/11, O6) tutta la color RAM con il colore A (esce con Y = 0). Anche la minimappa (ui.asm)
col_fill:
        ldy #0
-       sta COLRAM,y
        sta COLRAM+$100,y
        sta COLRAM+$200,y
        sta COLRAM+$300,y
        iny
        bne -
        rts

; palette 0 villaggio, 1-8 dungeon (scelte da pal_for_level); dal 18/11 palette fisse dei piani (data/chapters.yaml
; map.palettes, tabella lv_look): 9 grotta innevata (bianca), 10 grotta di roccia (grigia), 11 grotta di ghiaccio (azzurrina),
; 12 palude (una per tutti i piani). Coppie di bit: 01 = pal_c1, 10 = pal_c2, 11 = colore della RAM (0-7)
pal_bg  .byte 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
pal_c1  .byte 9, 11, 11, 6, 2, 9, 5, 4, 11, 15, 12, 14, 9
pal_c2  .byte 15, 9, 8, 14, 10, 7, 13, 10, 12, 1, 15, 1, 5
pal_ram .byte 11, 15, 15, 11, 15, 15, 15, 15, 15, 14, 8, 14, 13

; ------------------------------------------------------------------ PRNG xorshift16
; ritorna A casuale (hi)
rand:
        lda rnd+1
        lsr
        lda rnd
        ror
        eor rnd+1
        sta rnd+1
        lda #0
        ror
        eor rnd
        sta rnd
        lda rnd+1
        lsr
        eor rnd
        sta rnd
        eor rnd+1
        sta rnd+1
        rts

; A = n (>=1) -> A = 0..n-1 ; preserva X,Y
rndrange:
        sta rr_n
        txa
        pha
        jsr rand
        sta rr_a            ; moltiplicatore
        lda #0
        sta tmpv            ; byte basso del prodotto
        ldx #8
_l      lsr rr_a
        bcc _s
        clc
        adc rr_n
_s      ror
        ror tmpv
        dex
        bne _l
        sta tmpv            ; byte alto = (rand*n)>>8
        pla
        tax
        lda tmpv
        rts

; ------------------------------------------------------------------ mappa
; tile (tx,ty) -> A
get_tile:
        ldy ty
        lda maprow_lo,y
        clc
        adc tx
        sta ptr0
        lda maprow_hi,y
        adc #0
        sta ptr0+1
        ldy #0
        lda (ptr0),y
        rts

; imposta tile A in (tx,ty)
set_tile:
        sta tmpv
        jsr get_tile            ; (11/11, O7) ptr0 = casella (tx,ty), Y = 0: stesso calcolo di get_tile
        lda tmpv
        sta (ptr0),y
        lda tp_on
        bne tile_patch
        rts

; ridisegna il tile (tx,ty) nei due schermi di gioco (al posto di un ridisegno completo):
; buffer visibile (o quello che lo diventa al prossimo flip) con origine drawn_cx/cy,
; buffer nascosto con origine del pre-rendering pf_cx/cy. Preserva X.
tile_patch:
        txa
        pha
        jsr get_tile
        sta tp_t
        lda front
        eor pend_flip
        sta tp_b                ; 0 = SCR_A visibile
        lda drawn_cx
        sta tp_ox
        lda drawn_cy
        sta tp_oy
        jsr tp_draw
        lda tp_b
        eor #1
        sta tp_b
        lda pf_cx
        sta tp_ox
        lda pf_cy
        sta tp_oy
        jsr tp_draw
        pla
        tax
        rts

; (tx, ty) = casella appena cambiata da set_tile: la ridisegna sullo schermo visibile se e' nella finestra (tp_ox/tp_oy)
tp_draw:
        lda tx
        asl
        sec
        sbc tp_ox
        sta tp_c
        lda ty
        asl
        sec
        sbc tp_oy
        sta tp_r
        ldx #0
_q      lda tp_r
        clc
        adc tp_qy,x
        cmp #22                 ; righe di gioco sopra l'HUD
        bcs _s
        tay
        lda tp_c
        clc
        adc tp_qx,x
        cmp #40
        bcs _s
        clc
        adc scrrow_lo,y
        sta ptr0
        lda scrrow_hi,y
        adc #0
        ldy tp_b
        beq _a
        clc
        adc #>(SCR_B-SCR_A)
_a      sta ptr0+1
        lda tp_t
        ora tp_qo,x
        ldy #0
        sta (ptr0),y
_s      inx
        cpx #4
        bne _q
        rts
tp_qx   .byte 0, 1, 0, 1
tp_qy   .byte 0, 0, 1, 1
tp_qo   .byte 0, 64, 128, 192

; C=1 se (sa_x, sa_y) e' su tile solido
solid_at:
        lda sa_x
        lsr
        lsr
        lsr
        lsr
        sta tx
        lda sa_x+1
        asl
        asl
        asl
        asl
        ora tx
        sta tx
        lda sa_y
        lsr
        lsr
        lsr
        lsr
        sta ty
        lda sa_y+1
        asl
        asl
        asl
        asl
        ora ty
        sta ty
        lda tx                  ; fuori dalla mappa = solido (bordi aperti, es. strada a sud)
        cmp #MAPW
        bcs _out
        lda ty
        cmp #MAPH
        bcs _out
        jsr get_tile
        tay
        lda solidtab,y
        lsr
_out    rts

HALFB   = 5

; muove ent_x di A (signed). C=1 se bloccato
try_step_x:
        sta st_d
        clc
        adc ent_x
        sta nx
        lda #0
        bit st_d
        bpl +
        lda #$ff
+       adc ent_x+1
        sta nx+1
        ; punto di sonda: nx +- HALFB
        lda st_d
        bmi _neg
        lda nx
        clc
        adc #HALFB
        sta sa_x
        lda nx+1
        adc #0
        sta sa_x+1
        jmp _chk
_neg    lda nx
        sec
        sbc #HALFB
        sta sa_x
        lda nx+1
        sbc #0
        sta sa_x+1
_chk    lda ent_y
        sec
        sbc #HALFB
        sta sa_y
        lda ent_y+1
        sbc #0
        sta sa_y+1
        jsr solid_at
        rol st_pb               ; (bit 0 dopo il secondo rol: sonda alta)
        lda ent_y
        clc
        adc #HALFB
        sta sa_y
        lda ent_y+1
        adc #0
        sta sa_y+1
        jsr solid_at
        rol st_pb
        lda st_pb
        and #3
        bne _blk
        lda nx
        sta ent_x
        lda nx+1
        sta ent_x+1
        clc
        rts
_blk    ldy #1                  ; spigolo: una sola sonda bloccata -> 1 px di lato verso la parte libera
        cmp #2                  ; (2 = sonda alta bloccata: giu'; 1 = bassa: su; 3 = muro pieno)
        beq _nz
        ldy #$ff
        cmp #1
        bne _no
_nz     lda st_nz
        bne _no
        inc st_nz
        tya
        jsr try_step_y
        dec st_nz
_no     sec
        rts

; A = passo verticale con segno (px): ent_y si sposta se le caselle d'arrivo (colonne del corpo) non sono solide;
; C=1 se bloccato (ent_y invariato)
try_step_y:
        sta st_d
        clc
        adc ent_y
        sta nx
        lda #0
        bit st_d
        bpl +
        lda #$ff
+       adc ent_y+1
        sta nx+1
        lda st_d
        bmi _neg
        lda nx
        clc
        adc #HALFB
        sta sa_y
        lda nx+1
        adc #0
        sta sa_y+1
        jmp _chk
_neg    lda nx
        sec
        sbc #HALFB
        sta sa_y
        lda nx+1
        sbc #0
        sta sa_y+1
_chk    lda ent_x
        sec
        sbc #HALFB
        sta sa_x
        lda ent_x+1
        sbc #0
        sta sa_x+1
        jsr solid_at
        rol st_pb
        lda ent_x
        clc
        adc #HALFB
        sta sa_x
        lda ent_x+1
        adc #0
        sta sa_x+1
        jsr solid_at
        rol st_pb
        lda st_pb
        and #3
        bne _blk
        lda nx
        sta ent_y
        lda nx+1
        sta ent_y+1
        clc
        rts
_blk    ldy #1                  ; spigolo: una sola sonda bloccata -> 1 px di lato verso la parte libera
        cmp #2                  ; (2 = sonda sinistra bloccata: a destra; 1 = destra: a sinistra)
        beq _nz
        ldy #$ff
        cmp #1
        bne _no
_nz     lda st_nz
        bne _no
        inc st_nz
        tya
        jsr try_step_x
        dec st_nz
_no     sec
        rts

; ------------------------------------------------------------------ input
read_input:
        lda joy
        sta joyold
        lda CIA1_PRA
        eor #$ff
        and #$1f
        sta joy
        ; scansione tastiera
        ldx #7
        lda #$7f
        sta tmp0
_row    lda keyrows,x
        sta keyprev,x
        lda tmp0
        sta CIA1_PRA
        lda CIA1_PRB
        eor #$ff
        sta keyrows,x
        lda tmp0
        sec
        ror
        sta tmp0
        dex
        bpl _row
        lda #$ff
        sta CIA1_PRA
        ; nuovi tasti premuti
        ldx #7
_kn     lda keyprev,x
        eor #$ff
        and keyrows,x
        sta keynew,x
        dex
        bpl _kn
        ; WASD e spazio come joystick alternativo
        lda keyrows+1
        and #$02            ; W
        beq +
        lda joy
        ora #$01
        sta joy
+       lda keyrows+1
        and #$20            ; S
        beq +
        lda joy
        ora #$02
        sta joy
+       lda keyrows+1
        and #$04            ; A
        beq +
        lda joy
        ora #$04
        sta joy
+       lda keyrows+2
        and #$04            ; D
        beq +
        lda joy
        ora #$08
        sta joy
+       lda keyrows+7
        and #$10            ; spazio
        beq +
        lda joy
        ora #$10
        sta joy
+
.if ARENA
        jsr AR_INPUT
.elsif TESTBUILD
        jsr test_input
.endif
        lda joyold
        eor #$ff
        and joy
        sta joynew
        rts

.if TESTBUILD
; script: joy, riga tasto, maschera tasto, durata (frame)  ; durata 0 = fine
test_input:
        lda scr_cnt
        bne _run
        ldy #0
        lda (scr_ptr),y
        sta scr_key+0        ; usa scr_key come temp joy
        iny
        lda (scr_ptr),y
        sta tmp1             ; riga
        iny
        lda (scr_ptr),y
        sta tmp2             ; maschera
        iny
        lda (scr_ptr),y
        sta scr_cnt
        beq _end
        lda scr_ptr
        clc
        adc #4
        sta scr_ptr
        bcc +
        inc scr_ptr+1
+       lda tmp1
        cmp #$ff
        beq _run
        tax
        lda tmp2
        sta keynew,x
        ora keyrows,x
        sta keyrows,x
_run    dec scr_cnt
        lda scr_key
        sta joy
        rts
_end    lda #0
        sta joy
        sta scr_cnt
; fine delle varianti di test del ciclo (TESTUI, script dei tasti): niente da fare
test_done:
        rts
.endif

; ------------------------------------------------------------------ loop principale
main_loop:
        lda core_ok             ; (21/11, TODO D15) segmento CORE da rileggere (dopo un salvataggio o una lettura dell'eroe)
        bne +
        jsr core_need
+
.if ARENA
        jsr AR_WAIT
.else
        jsr wait_vblank
.endif
.if TESTFZ
        inc $03fa               ; test: giri del ciclo principale (16 bit)
        bne +
        inc $03fb
+       lda $03fa               ; ogni 32 giri: fotogrammi persi (8 bit), px, py -> $0340 + 5 x n
        and #31
        bne +
        ldx $03fc
        cpx #170
        bcs +
        lda $03f8
        sec
        sbc $03fa
        sta $0340,x
        lda px
        sta $0341,x
        lda px+1
        sta $0342,x
        lda py
        sta $0343,x
        lda py+1
        sta $0344,x
        txa
        clc
        adc #5
        sta $03fc
+
.endif
.if TMDBG
        jsr tm_sample
.endif
        jsr apply_frame
        inc frame
        jsr read_input
.if NOKEYS
        nop
.else
        jsr handle_keys
.endif
        jsr update_player
        jsr update_attack
        jsr update_monsters
        jsr drops_tick
.if (TESTUI == 9) || (TESTUI == 11)
        lda #$ff
        sta bar_t
.endif
        jsr update_world
        jsr update_camera
        jsr update_bar          ; (19/11) dopo la camera: l'etichetta del luogo non si ricalcola nei fotogrammi di ridisegno
        jsr npc_tick            ; (17/11) NPC del villaggio (quest.asm); (19/11) dopo la camera: salta i fotogrammi di ridisegno
        jsr maybe_redraw
        jsr build_sprites
.if TMDBG
        jsr tm_end
.endif
        jmp main_loop

.if TMDBG
TM_PL = $03f0
TM_PH = $03f1
TM_IDX = $03f2
TM_T0 = $03f3
; campiona il timer A di CIA2 a ogni giro: durata del giro in cicli + cam_cy
tm_sample:
        lda frame
        cmp #40
        bcc _x
        lda $dd05
        tay
        lda $dd04
        sta tmp0
        sec
        lda TM_PL
        sbc tmp0
        sta tmp1
        lda TM_PH
        sty tmp2
        sbc tmp2
        sta tmp2
        lda tmp0
        sta TM_PL
        sty TM_PH
        ldx TM_IDX
        cpx #185
        bcs _x
        lda tmp1
        sta $0340,x
        lda tmp2
        sta $0341,x
        lda $03f5
        sta $0342,x
        lda #0
        sta $03f5
        lda tmp0
        sta TM_T0
        sty TM_T0+1
_x      rts

; (TMDBG) fine del campionamento dei tempi di un giro: cicli del CIA2 timer A salvati in TM_PL/TM_PH
tm_end:
        lda frame
        cmp #40
        bcc _y
        ldx TM_IDX
        cpx #185
        bcs _y
        lda $dd05
        tay
        lda $dd04
        sta tmp0
        sec
        lda TM_T0
        sbc tmp0
        sta $0343,x
        lda TM_T0+1
        sty tmp2
        sbc tmp2
        sta $0344,x
        inx
        inx
        inx
        inx
        inx
        stx TM_IDX
_y      rts
.endif

; attende l'inizio del vblank (riga >= 252 o righe 256-311). Prima esce da un eventuale vblank
; in corso: l'IRQ di riga 250 dura qualche riga e puo' coprire la riga 252 (un confronto
; di uguaglianza la perderebbe per sempre).
wait_vblank:
_n      lda VIC_CTRL1
        bmi _n
        lda VIC_RASTER
        cmp #$fc
        bcs _n
_w      lda VIC_CTRL1
        bmi _y
        lda VIC_RASTER
        cmp #$fc
        bcc _w
_y      rts

; ------------------------------------------------------------------ giocatore
update_player:
        lda #0
        sta pdx
        sta pdy
        lda joy
        and #$01
        beq +
        lda #$fe
        sta pdy
        lda #1
        sta pdir
+       lda joy
        and #$02
        beq +
        lda #2
        sta pdy
        lda #0
        sta pdir
+       lda joy
        and #$04
        beq +
        lda #$fe
        sta pdx
        lda #2
        sta pdir
+       lda joy
        and #$08
        beq +
        lda #2
        sta pdx
        lda #3
        sta pdir
+       ; diagonale: velocita' per asse ridotta (1 px, ogni 4 frame 2 px) ~ velocita'
        ; normalizzata; in piu' evita che due assi cambino cella ravvicinati
        ; (ogni cambio cella costa ~11 passi di rendering, il frame non basta)
        lda pdx
        beq _dn
        lda pdy
        beq _dn
        lda frame
        and #3
        beq _dn
        lda pdx
        bmi _dx1
        lda #1
        bne _dx2
_dx1    lda #$ff
_dx2    sta pdx
        lda pdy
        bmi _dy1
        lda #1
        bne _dy2
_dy1    lda #$ff
_dy2    sta pdy
_dn     jsr fz_move             ; Frenzy: corsa piu' veloce (combat.asm)
        jsr ent_pl
        jsr ent_tile            ; casella attuale: il PG non entra nella casella di un mostro
        lda nt_x
        sta ot_x
        lda nt_y
        sta ot_y
        lda #$ff
        sta occ_self
        lda pdx
        beq +
        jsr try_step_x
        bcs _bx
        jsr occ_check
        bcc +
        lda px                  ; casella occupata: annulla il passo in x
        sta ent_x
        lda px+1
        sta ent_x+1
_bx     lda #0                  ; bloccato (muro o mostro): nessun movimento reale su x
        sta pdx                 ; (il prefetch del rendering usa pdx/pdy come movimento effettivo)
+       lda pdy
        beq +
        jsr try_step_y
        bcs _by
        jsr occ_check
        bcc +
        lda py
        sta ent_y
        lda py+1
        sta ent_y+1
_by     lda #0
        sta pdy
+       lda ent_x
        sta px
        lda ent_x+1
        sta px+1
        lda ent_y
        sta py
        lda ent_y+1
        sta py+1
        ; animazione
        lda pdx
        ora pdy
        beq _idle
        inc pstep
        lda pstep
        and #$08
        lsr
        lsr
        lsr
        sta panim
        rts
_idle   lda #0
        sta panim
        rts

; ------------------------------------------------------------------ camera
update_camera:
        ; camx = px - 152, limitato a 0..464
        lda px
        sec
        sbc #152
        sta camx
        lda px+1
        sbc #0
        sta camx+1
        bpl +
        lda #0
        sta camx
        sta camx+1
        jmp _cx
+       lda camx+1
        cmp #2
        bcs _maxx
        cmp #1
        bne _cx
        lda camx
        cmp #$d1
        bcc _cx
_maxx   lda #$d0
        sta camx
        lda #1
        sta camx+1
_cx     ; camy = py - 96, limitato a 0..576
        lda py
        sec
        sbc #76
        sta camy
        lda py+1
        sbc #0
        sta camy+1
        bpl +
        lda #0
        sta camy
        sta camy+1
        jmp _cy
+       lda camy+1
        cmp #3
        bcs _maxy
        cmp #2
        bne _cy
        lda camy
        cmp #$59
        bcc _cy
_maxy   lda #$58
        sta camy
        lda #2
        sta camy+1
_cy     ; coarse / fine
        lda camx
        lsr
        lsr
        lsr
        sta tmp0
        lda camx+1
        asl
        asl
        asl
        asl
        asl
        ora tmp0
        sta cam_cx
        lda camx
        and #7
        eor #7
        sta hx
        lda camy
        lsr
        lsr
        lsr
        sta tmp0
        lda camy+1
        asl
        asl
        asl
        asl
        asl
        ora tmp0
        sta cam_cy
        lda camy
        and #7
        eor #7
        sta hy
        rts

; marcatore del percorso di rendering nei record TMDBG (1 completa, 2 sync, 4 nuovo, 8 continua)
tmark   .macro v
.if TMDBG
        lda $03f5
        ora #\v
        sta $03f5
.endif
        .endm

; ridisegno della finestra di gioco: completo se force_redraw, altrimenti solo se la camera ha cambiato casella
; (scorrimento a righe/colonne nel buffer nascosto, poi pend_flip)
; (19/11) C=1 se maybe_redraw in questo fotogramma cambia cella o ridisegna tutto (dopo update_camera): il lavoro che puo'
; aspettare un fotogramma (passo degli NPC, etichetta del luogo) salta, il ridisegno da solo sta nel fotogramma
redraw_due:
        lda force_redraw
        bne _y
        lda cam_cx
        cmp drawn_cx
        bne _y
        lda cam_cy
        cmp drawn_cy
        bne _y
        clc
        rts
_y      sec
        rts

maybe_redraw:
        lda #0                  ; (19/11) 1 = ridisegno completo in questo fotogramma (npc_draw tiene gli sprite di prima)
        sta rd_sync
        lda force_redraw
        beq _nf
        lda #0
        sta force_redraw
        sta pf_valid
        beq _sync
_nf     lda cam_cx
        cmp drawn_cx
        bne _chg
        lda cam_cy
        cmp drawn_cy
        bne _chg
        jmp prefetch
_chg    lda pf_valid
        beq _sync
        lda pf_cx
        cmp cam_cx
        bne _sync
        lda pf_cy
        cmp cam_cy
        bne _sync
        #tmark 1
        lda #11                  ; completa i passi mancanti
        jsr rc_run
        jmp _flip
_sync
        #tmark 2
        inc rd_sync
        lda cam_cx
        sta pf_tx
        lda cam_cy
        sta pf_ty
        jsr rc_init
        lda #11
        jsr rc_run
_flip   lda cam_cx
        sta drawn_cx
        lda cam_cy
        sta drawn_cy
        lda #0
        sta pf_valid
        lda #1
        sta pend_flip
        rts

; pre-rendering: se la camera sta per entrare in una nuova cella (8 px),
; prepara lo schermo nascosto con pochi passi per frame
prefetch:
        lda cam_cx
        sta pf_tx
        lda cam_cy
        sta pf_ty
        lda camx
        and #7
        sta tmp0                 ; frazione x
        lda pdx
        beq _py
        bmi _xl
        lda tmp0
        cmp #2
        bcc _py
        lda cam_cx
        cmp #58
        bcs _py
        inc pf_tx
        bne _py
_xl     lda tmp0
        cmp #5
        bcs _py
        lda cam_cx
        beq _py
        dec pf_tx
_py     lda camy
        and #7
        sta tmp0
        lda pdy
        beq _pt
        bmi _yu
        lda tmp0
        cmp #2
        bcc _pt
        lda cam_cy
        cmp #75
        bcs _pt
        inc pf_ty
        bne _pt
_yu     lda tmp0
        cmp #5
        bcs _pt
        lda cam_cy
        beq _pt
        dec pf_ty
_pt     lda pf_tx               ; diagonale: se la camera sta per cambiare cella su
        cmp cam_cx              ; entrambi gli assi, prepara SOLO quello che scatta per
        beq _one                ; primo (i due assi scattano a frame diversi: un buffer
        lda pf_ty               ; predetto su entrambi non coinciderebbe mai con la camera
        cmp cam_cy              ; e costringerebbe a un ridisegno completo in un frame)
        beq _one
        jsr pf_pick
_one    lda pf_tx
        cmp cam_cx
        bne _need
        lda pf_ty
        cmp cam_cy
        beq _none
_need   lda pf_valid
        beq _new
        lda pf_cx
        cmp pf_tx
        bne _new
        lda pf_cy
        cmp pf_ty
        beq _cont
_new
        #tmark 4
        jsr rc_init
_cont
        #tmark 8
        lda #3                  ; 3 passi per frame: il 4o sforava il budget nei frame di scroll verticale
        jmp rc_run
_none   rts

; distanza (in pixel) di ciascun asse dal cambio di cella: tiene l'asse piu' vicino
pf_pick:
        lda camx
        and #7
        sta tmp0
        lda pdx
        bmi _xl
        lda #8
        sec
        sbc tmp0
        jmp _xs
_xl     lda tmp0
        clc
        adc #1
_xs     sta tmp1                ; distanza x
        lda camy
        and #7
        sta tmp0
        lda pdy
        bmi _yl
        lda #8
        sec
        sbc tmp0
        jmp _ys
_yl     lda tmp0
        clc
        adc #1
_ys     sta tmp0                ; distanza y
        sec
        sbc tmp1                ; y - x
        clc
        adc #1
        cmp #3                  ; |y-x| <= 1 px: scattano nello stesso frame
        bcc _both               ;  -> buffer combinato (entrambi gli assi)
        lda tmp0
        cmp tmp1
        bcc _keepy              ; y piu' vicino: scarta x
        lda cam_cy
        sta pf_ty
        rts
_keepy  lda cam_cx
        sta pf_tx
_both   rts

; ------------------------------------------------------------------ render
; rc_init: prepara il rendering del buffer nascosto per la cella (pf_tx,pf_ty)
rc_init:
        lda pf_tx
        sta pf_cx
        lsr
        sta tmp0                 ; tc (colonna tile)
        lda pf_tx
        and #1
        sta tmp1                 ; oddx
        lda pf_ty
        sta pf_cy
        lsr
        sta tmp2                 ; tr (riga tile)
        lda pf_ty
        and #1
        sta pf_oddy
        lda #11
        sta pf_tot
        ; n1 = 19+oddx , n2 = 2*n1
        lda #19
        clc
        adc tmp1
        sta pf_n1
        asl
        sta pf_n2
        ; pf_p0 = MAP + tr*48 + tc
        ldy tmp2
        lda maprow_lo,y
        clc
        adc tmp0
        sta pf_p0
        lda maprow_hi,y
        adc #0
        sta pf_p0+1
        ; pf_p1 = schermo nascosto - oddx
        lda front
        eor #1
        beq _bufA
        lda #<SCR_B
        ldx #>SCR_B
        jmp _bufset
_bufA   lda #<SCR_A
        ldx #>SCR_A
_bufset sec
        sbc tmp1
        sta pf_p1
        txa
        sbc #0
        sta pf_p1+1
        lda #0
        sta pf_step
        lda #1
        sta pf_valid
        rts

; A = righe da preparare in questo giro: continua il ridisegno a passi (pf_step di pf_tot) senza superare il fotogramma
rc_run:
        sta rc_cnt
_lp     lda pf_step
        cmp pf_tot
        bcc _go
        rts
_go     lda pf_p0
        sta ptr0
        lda pf_p0+1
        sta ptr0+1
        lda pf_p1
        sta ptr1
        lda pf_p1+1
        sta ptr1+1
        lda pf_n1
        sta rs_n1
        lda pf_n2
        sta rs_n2
        lda pf_oddy
        beq _ev
        lda pf_step              ; oddy=1: passo 0 = meta' bassa di tr, poi 10 coppie
        bne _pair
        lda #1
        sta rs_r
        jsr render_single
        jsr next_row_single
        jmp _nextmap
_ev     lda pf_step              ; oddy=0: 10 coppie, poi meta' alta di tr+10
        cmp #10
        bne _pair
        lda #0
        sta rs_r
        jsr render_single
        jmp _save
_pair   jsr render_pair
        lda ptr1
        clc
        adc #80
        sta ptr1
        bcc _nextmap
        inc ptr1+1
_nextmap
        lda ptr0
        clc
        adc #MAPW
        sta ptr0
        bcc _save
        inc ptr0+1
_save   lda ptr0
        sta pf_p0
        lda ptr0+1
        sta pf_p0+1
        lda ptr1
        sta pf_p1
        lda ptr1+1
        sta pf_p1+1
        inc pf_step
        dec rc_cnt
        beq _done
        jmp _lp
_done   rts

; ptr1 += 40 (riga di caratteri successiva)
next_row_single:
        lda ptr1
        clc
        adc #40
        sta ptr1
        bcc +
        inc ptr1+1
+       rts

; due righe di caratteri da una riga di tile
render_pair:
        lda ptr1
        sta rp_s0+1
        lda ptr1+1
        sta rp_s0+2
        lda ptr1
        clc
        adc #1
        sta rp_s1+1
        lda ptr1+1
        adc #0
        sta rp_s1+2
        lda ptr1
        clc
        adc #40
        sta rp_s2+1
        lda ptr1+1
        adc #0
        sta rp_s2+2
        lda ptr1
        clc
        adc #41
        sta rp_s3+1
        lda ptr1+1
        adc #0
        sta rp_s3+2
        ldy rs_n1
        ldx rs_n2
; cuore della copia di una riga di tile: i 4 caratteri di ogni tile (+$40, +$80, +$C0) con indirizzi automodificati
rp_lp   lda (ptr0),y
rp_s0   sta $c000,x
        ora #$40
rp_s1   sta $c000,x
        ora #$80
rp_s3   sta $c000,x
        eor #$40
rp_s2   sta $c000,x
        dex
        dex
        dey
        bpl rp_lp
        rts

; una sola riga: rs_r = 0 (meta' alta) o 1 (meta' bassa)
render_single:
        lda ptr1
        sta rs_s0+1
        lda ptr1+1
        sta rs_s0+2
        lda ptr1
        clc
        adc #1
        sta rs_s1+1
        lda ptr1+1
        adc #0
        sta rs_s1+2
        lda rs_r
        beq _top
        lda #$80
        sta rs_o0+1
        lda #$c0
        sta rs_o1+1
        jmp _go
_top    lda #$00
        sta rs_o0+1
        lda #$40
        sta rs_o1+1
_go     ldy rs_n1
        ldx rs_n2
rs_lp   lda (ptr0),y
rs_o0   ora #$00
rs_s0   sta $c000,x
        lda (ptr0),y
rs_o1   ora #$40
rs_s1   sta $c000,x
        dex
        dex
        dey
        bpl rs_lp
        rts

; ------------------------------------------------------------------ sprite
; ent_x/ent_y -> slot X. C=1 se visibile
spr_pos:
        lda ent_x
        sec
        sbc camx
        sta tmp0
        lda ent_x+1
        sbc camx+1
        sta tmp1
        lda tmp0
        clc
        adc #19
        sta tmp0
        lda tmp1
        adc #0
        sta tmp1
        bmi _hide
        bne _hi
        lda tmp0
        cmp #8
        bcc _hide
        bcs _xok
_hi     cmp #2
        bcs _hide
        lda tmp0
        cmp #79
        bcs _hide
_xok    lda ent_y
        sec
        sbc camy
        sta tmp2
        lda ent_y+1
        sbc camy+1
        sta tmp3
        lda tmp2
        clc
        adc #45
        sta tmp2
        lda tmp3
        adc #0
        sta tmp3
        bne _hide
        lda tmp2
        cmp #35
        bcc _hide
        cmp #192
        bcs _hide
        sta sh_y,x
        lda tmp0
        sta sh_x,x
        lda tmp1
        beq +
        lda bs_msb
        ora bitmask,x
        sta bs_msb
+       sec
        rts
_hide   clc
        rts

; inizio del fotogramma (dopo wait_vblank): scambio dei due schermi se pend_flip, $D018, sfondo, ombre degli sprite
; nei registri del VIC e puntatori negli schermi
apply_frame:
        lda pend_flip
        beq +
        lda front
        eor #1
        sta front
        lda #0
        sta pend_flip
+       ldx front
        lda d018_tab,x
        sta VIC_MEM
        sta ap_d018
        lda bg_cur
        sta BGCOL
        sta ap_bg
        lda hy
        cmp #5
        bcc _il
        lda #1
_il     clc
        adc #209
        sta $d012
        sta ap_l1
        lda hx
        ora #$10
        sta VIC_CTRL2
        sta ap_d016
        lda hy
        ora #$10
        sta VIC_CTRL1
        sta ap_d011
        lda bar_on
        beq spr_copy
        jsr bar_regs
        lda #IRQ_BAR
        sta $d012
        lda #3
        sta irq_ph
        rts

; registri sprite di gioco dalle shadow (anche da IRQ)
spr_copy:
        ldx #7
_sl     txa
        asl
        tay
        lda sh_x,x
        sta SPR_X,y
        lda sh_y,x
        sta SPR_X+1,y
        lda sh_col,x
        sta SPR_COL,x
        lda sh_ptr,x
        sta SCR_A+$3f8,x
        sta SCR_B+$3f8,x
        sta SCR_H+$3f8,x
        dex
        bpl _sl
        lda sh_msb
        sta SPR_MSB
        lda sh_xexp
        sta SPR_XEXP
        lda sh_yexp
        sta SPR_YEXP
        lda #SPRMC
        sta SPR_MC
        lda sh_en
        sta SPR_EN
        rts

d018_tab .byte $da, $fa
bitmask  .byte 1, 2, 4, 8, 16, 32, 64, 128

        .include "version.inc"
; etichette di inizio modulo: nomi dei moduli nei listati e nella mappa automatica (lab64 map)
mod_db
        .include "db.asm"
        .include "quests.inc"           ; (17/11) titoli e nomi delle quest (tools/build/gen_quests.py)
mod_dungeon
        .include "dungeon.asm"
mod_data
        .include "data.asm"
mod_game
        .include "game/game.asm"
mod_combat
        .include "combat.asm"
mod_levels
        .include "levels.asm"
mod_ui
        .include "ui.asm"
        .include "charsheet.asm"         ; (11/11) schermata C: punti statistica, respec
        .include "quest.asm"             ; (17/11, concept) pagina della quest (Q) e NPC del villaggio
        .include "stash.asm"
mod_hud
        .include "hud.asm"
mod_bar
        .include "bar.asm"
mod_music
        .include "music.asm"
mod_theme
        .include "theme.asm"
mod_rel
        .include "rel.asm"
mod_chap
        .include "backmenu.asm"          ; (16/11) trampoline e pagina di attesa per "back to main menu" (LOBBY)
        .include "chapter.asm"           ; (12/11) sequenza dei capitoli: TODO M1
.if OVP_RES
        .include "final.asm"             ; (19/11) codice del piano 20 residente solo nelle build ARENA e TESTUI 36 (theme.asm)
.endif
.if CHEATS
; (17/11) menu dei trucchi per i test: solo con CHEATS = 1 (debug e test, non release). Il menu e' il file CHEATS
; (src/cheats.asm), letto a CHT_AT (lo schermo B) quando si apre ed eseguito; qui resta solo il caricamento.
CHT_AT  = SCR_B
mod_cheats
; (CHEATS = 1) voce cheats del menu di gioco: il modulo CHEATS dal disco a CHT_AT (schermo B) ed eseguito; se non si
; legge, di nuovo il menu di gioco
cheat_menu:
        ldy #nm_cht-nm_tab
        lda #6
        jsr set_name
        lda #2                  ; schermata di attesa generica
        sta io_what
        lda #<CHT_AT
        sta ptr0
        lda #>CHT_AT
        sta ptr0+1
        jsr load_raw
        bcs +
        jmp CHT_AT
+       jmp ui_gamemenu
.endif


; ------------------------------------------------------------------ dati grafici
; ===================================================================
;  MEMORIA RECUPERABILE (non ancora usata)
;  gfx_data..gfx_end viene copiato UNA SOLA VOLTA da copy_gfx (chiamata in `start`)
;  a $A000 (sprite), $A800 (charset), $8C00 (sprite 2), $B800 (font UI).
;  Dopo la copia questi byte sono dato morto: l'area gfx_data..FREE_RAM_END
;  (fino a $9FFF) e' libera per DATI DI RUNTIME (buffer, tabelle
;  generate, variabili), MAI per codice/dati statici del PRG (sarebbero
;  sovrascritti dal caricamento di gfx_data).
;  Regole per usarla:
;   - scrivere nell'area solo dopo `jsr copy_gfx` (in `start`, prima di game_start);
;   - nessun altro punto del sorgente deve leggere gfx_data (verificato: solo copy_gfx);
;   - gfx_data deve restare l'ULTIMA cosa del PRG: non aggiungere codice/dati dopo gfx_end;
;   - se la grafica cresce, FREE_RAM_START si sposta in avanti (guardia .cerror sotto).
;  Mappa: out/work/memory-map/program-game.html (lab64 map; annotazioni @map / @free nei sorgenti).
; ===================================================================
;@map gfx_data..$8720 "All'avvio grafica fissa del PRG, dato morto dopo copy_gfx" free-after=start
;@free gfx_data..$8720 "Margine del programma principale: codice e dati di main.asm (guardia .cerror a $8720, righe HUD)" use=code
gfx_data:                       ; solo la grafica fissa: tile del villaggio e dei dungeon e mostri sono su file (gfxN)
gd_fchr .binary "../out/work/gfx/fixed_chr.bin"  ; caratteri fissi (glifi HUD, minimappa): 4 strisce da GFX_FSTRIP byte
gd_core .binary "../out/work/gfx/spr_core.bin"   ; sprite 0..11 (eroe, fendenti) + 24..26
gd_font .binary "../out/work/gfx/uifont.bin"
gfx_end:

; generatore dei piani: nel PRG dopo la grafica (anche lui dato morto dopo l'avvio), eseguito sotto l'I/O.
; (21/11) COMPRESSO ZX0, in due passate (tools/build/asm.sh, asm_game): GENPASS=1 mette il codice del generatore dopo CODE2
; (solo per leggerne i byte: gen_raw..gen_raw_end, tools/build/gen_imgz.py li comprime in out/work/gen_img.zx0); GENPASS=2
; mette qui i byte compressi e il generatore in un blocco virtuale (solo le etichette). Le etichette sono le stesse nelle due
; passate (il codice prima di gfx_end non cambia, il generatore e' a GEN_AT); copy_gfx lo decomprime all'avvio.
GEN_AT = STASH_END                  ; $D080: RAM sotto l'I/O dopo la STASH (levels.asm; fino al 18/11 $D480)
.if GENPASS == 2
gen_img:
        .binary "../out/work/gen_img.zx0"
gen_img_end:
        .virtual GEN_AT
        .include "gen_io.asm"
gen_io_end:
        .endv
.else
gen_img = gen_raw
gen_img_end = gen_raw_end
.endif
        .cerror gen_io_end > $e000, "generatore sotto l'I/O oltre $DFFF"

; (21/11, TODO D15) segmento CORE (src/game/core.asm): nella seconda passata solo le etichette, nella prima i byte dopo il PRG
CORE_AT = $e000
;@map CORE_AT..core_end "CORE: liste, inventario e descrizione degli oggetti (file core, src/game/core.asm); lo coprono l'immagine del salvataggio e il plugin di save (si rilegge)" scenario=villaggio,dungeon
.if GENPASS == 2
        .virtual CORE_AT
        .include "core.asm"
core_end:
        .endv
.endif
        .cerror core_end > GFX_TOWN_AT || core_end > GFX_DUN_AT, "segmento CORE oltre il file del villaggio o del tema"

FREE_RAM_END   = $9fff              ; il PRG puo' arrivare fino a $9FFF: la coda di gfx_data e' dato morto dopo
                                    ; copy_gfx (prima istruzione utile di `start`) e copre $8000-$9FFF (schermo HUD,
                                    ; sprite barra, sprites2, variabili $9000: tutti scritti DOPO la copia)
        .cerror gfx_data > SCR_H + 800, "codice oltre $8720: le righe HUD (SCR_H+800) lo sovrascriverebbero"
        .cerror GENPASS == 2 && gen_img_end > CODE2, "grafica fissa + generatore (compresso) oltre $9C00 (secondo blocco di codice)"

; ------------------------------------------------------------------ secondo blocco di codice: $9C00-$9FFF
; RAM non toccata a runtime (le variabili finiscono a $9BFF, azzerate da game_start fino a $9BFF).
CODE2 = $9c00
        * = CODE2
        .include "disk.asm"
        .include "stash_io.asm"
        .include "monpath.asm"
; cheat god mode (docs/wiki/cheats.md): diverso da 0 = il PG non perde vita. Byte del PRG in CODE2 (game_start non lo
; azzera): lo scrive START dal POKE 1021,1 dato prima del RUN, il monitor di VICE o TESTGOD=1 (11/11)
godmode .byte 0
core_ok .byte 0                         ; (21/11, TODO D15) 1 = segmento CORE in memoria (fuori dalle variabili azzerate da game_start)
code2_end:
;@free code2_end..$a000 "Coda di CODE2: piccolo codice residente (disco, caricamenti)" use=code
        .cerror code2_end > FREE_RAM_END + 1, "secondo blocco di codice oltre $9FFF"
.if GENPASS == 1
        * = FREE_RAM_END + 1                ; (21/11) prima passata: il generatore non compresso, solo per gen_imgz.py
gen_raw:
        .logical GEN_AT
        .include "gen_io.asm"
gen_io_end:
        .here
gen_raw_end:
core_raw:                               ; (21/11) segmento CORE: byte per tools/build/gen_imgz.py (file core)
        .logical CORE_AT
        .include "core.asm"
core_end:
        .here
core_raw_end:
.endif
