; ===================================================================
;  music.asm - musica del gioco: player unico (src/common/sid_player.inc) a 3 voci; la voce 1 del SID e' condivisa con
;  gli effetti sonori (src/common/sfx.inc: mentre suona un effetto la voce 1 del brano tace).
;  Brani: file SND0..SNDn sul disco (tools/build/songs.py -> tools/build/gen_music.py; elenco in src/game/music_tab.inc):
;    villaggio, livelli (uno a caso a ogni piano, diverso dal precedente), boss finale (piano MAXLEVEL),
;    combattimento (uno a caso per piano, scelto al caricamento del piano).
;  Al caricamento di un luogo il brano scelto va nel buffer del livello (SND_LBUF) e il motivetto in quello del
;  combattimento (SND_FBUF), sempre dal disco: un brano alla volta, nessuna copia in RAM (06/11 sera).
;
;  API (tutte chiamabili in qualsiasi momento):
;    music_request  A = 0 silenzio / MUS_LVL brano del luogo / MUS_FIGHT combattimento,
;                   X = fotogrammi di rilascio per unita' (la dissolvenza dura 16 x X fotogrammi)
;    music_fadeout  dissolve a silenzio in modo bloccante (prima di caricare un livello)
;    music_town / music_dungeon  scelta e caricamento dei brani del luogo (a ogni cambio di luogo)
;    music_update   una volta per frame (da sfx_update: in gioco dall'IRQ di fine HUD, nelle schermate da ui_input):
;                   dissolvenza, brano e tema di combattimento
;  Il tema di combattimento parte quando un mostro FORTE o un boss con nome e' a contatto col PG (game.asm scrive
;  mus_cmb); acceso, lo tiene qualsiasi mostro a contatto; si spegne CMB_HOLD x 4 frame (12 s) dopo l'ultimo
;  contatto; poi si riprende il brano del luogo da dove era. Ogni operazione su disco zittisce il SID (snd_io).
; ===================================================================
CMB_HOLD   = 150                ; isteresi del tema di combattimento, in unita' di 4 frame (12 s senza contatti)
CMB_DROP   = 100                ; frame dopo l'ultimo contatto con un mostro qualsiasi: fine combattimento (bauli)
FADE_SLOW  = 2                  ; frame per passo: cambio livello / fine combattimento
FADE_FAST  = 1                  ; inizio combattimento
MUS_LVL    = 1
MUS_FIGHT  = 2
SND_LBUF   = $8a40              ; brano del luogo (slot sprite 41-47 liberi, fino a $8BFF)
SND_FBUF   = $8e80              ; motivetto di combattimento (slot sprite 58-63 liberi, fino a $8FFF)
        .include "music_tab.inc"
SND_LBUF_end = SND_LBUF + SND_SMAX  ; (15/11) fine dei buffer: coppie di etichette per la mappa automatica (TODO T1)
SND_FBUF_end = SND_FBUF + SND_FMAX
;@map SND_LBUF "Brano del luogo (SND_LBUF): file SNDn senza indirizzo, letto qui dal disco; grande quanto il brano piu' lungo"
;@map SND_LBUF_end..$8c00 "Coda degli slot sprite 41-47: sotto gd_font (copiato da init), libera dopo l'avvio" free-after=start
;@map SND_FBUF "Motivetto di combattimento (SND_FBUF): file SNDn, grande quanto il motivetto piu' lungo"
        .cerror SND_SMAX > $8c00 - SND_LBUF, "brano troppo lungo per SND_LBUF"
        .cerror SND_FMAX > $9000 - SND_FBUF, "motivetto troppo lungo per SND_FBUF"

        .virtual $93a0          ; (azzerate da game_start)
mus_trk .byte ?                 ; brano in riproduzione (0 = nessuno)
mus_want .byte ?                ; brano richiesto
mus_fo  .byte ?                 ; frame residui di dissolvenza in uscita (rilascio)
mus_fsp .byte ?                 ; frame per passo
mus_cmb .byte ?                 ; tema di combattimento: unita' di 4 frame residue (scritto da game.asm)
cmb_t   .byte ?                 ; frame residui di combattimento con qualsiasi mostro (game.asm, drops_tick)
mus_fr  .byte ?                 ; contatore dei fotogrammi della musica
mus_mute .byte ?                ; 1 = SID zittito per un'operazione su disco (snd_io): volume da ripristinare
mus_inc .byte ?                 ; 1 = tema di combattimento richiesto
mus_flt .byte ?                 ; modo del filtro per $d418 (alto nibble)
mus_sv  .byte ?                 ; 1 = posizione del brano del luogo salvata (ripresa dopo il combattimento)
snd_cur .fill 2                 ; brano nel buffer del luogo / del combattimento (+1; 0 = nessuno)
snd_id  .byte ?
snd_b   .byte ?
snd_try .byte ?                 ; (15/11) letture rimaste del brano (snd_get, ex TODO A2)
mus_end
        .endv
        .cerror mus_end > $93b0, "variabili musicali sovrapposte"

SP_VARS = $9b4e                 ; variabili del player (dopo le variabili REL)
SP_V0   = 7                     ; lead sulla voce 2 del SID
SP_V1   = 0                     ; accordi sulla voce 1 (condivisa con gli effetti)
SP_V2   = 14                    ; basso e batteria sulla voce 3
        .include "sid_player.inc"
        .cerror SP_VARS < rel_end || SP_VARS + SP_VSIZE > $9c00, "variabili del player fuori da $9B4E-$9BFF"

        .virtual $95e0          ; (08/11 sera: dopo il blocco dell'eroe, che contiene il baule di casa)
mfar    .fill 32                ; 1 = mostro lontano (game.asm: riesame ridotto)
mfar_end
        .endv
        .cerror mfar_end > $9600, "mfar oltre $9600 (mostri)"

        .virtual $93b0          ; (08/11 sera: da $95D4) set_tile, mostri che si muovono, scorrimento
tp_on   .byte ?                 ; 1 = set_tile aggiorna anche lo schermo (solo in gioco)
tp_t    .byte ?
tp_b    .byte ?
tp_ox   .byte ?
tp_oy   .byte ?
tp_c    .byte ?
tp_r    .byte ?
sel_cu  .fill 4                 ; mostri che si muovono (scelti al frame precedente)
sel_nx  .fill 4                 ; selezione in costruzione
sel_d   .fill 4
sel_v   .byte ?
sel_w   .byte ?
sel_k   .byte ?
sel_on  .byte ?
sp_ox   .word ?
sp_oy   .word ?
sp_tx   .word ?
sp_ty   .word ?
sp_a    .byte ?
sp_n    .byte ?
sp_d    .byte ?
sp_i    .byte ?
tp_end
        .endv
        .cerror tp_end > $93e0, "variabili di set_tile oltre $93DF (motore dei menu)"

; ---------------------------------------------------------------- richieste
music_request:
        sta mus_want
        stx mus_fsp
        rts

; silenzio con dissolvenza, bloccante (~16-32 frame): chiamare prima di operazioni lunghe su disco
music_fadeout:
        lda #0
        sta mus_cmb
        sta mus_inc
        lda mus_trk
        ora mus_fo
        beq _r
        lda #0
        ldx #1
        jsr music_request
_w      jsr wait_vblank
        jsr music_update
        lda mus_trk
        ora mus_fo
        bne _w
_r      rts

; prima di ogni operazione su disco (load_raw, salvataggi): il caricamento tiene il processore e il SID
; resterebbe a suonare la nota corrente (glitch). Se suona qualcosa: dissolvenza del volume (15 frame), poi voci
; spente e volume 0; music_update rimette il volume alla prima chiamata dopo.
snd_io:
        lda mus_mute
        bne _r
        inc mus_mute
        lda sp_on
        ora sfx_t
        beq +
        jsr snd_fade            ; (levels.asm: volume a zero e voci spente)
        jmp _m
+       jsr snd_mute
_m      lda #0
        sta $d417
_r      rts

; villaggio: il tema del villaggio del capitolo (12/11, TODO M2: un tema per villaggio, snd_town_c)
music_town:
        ldx c_chap
        lda snd_town_c-1,x
        jmp mus_place

; nuovo piano: il tema del capitolo (12/11, TODO M2: uguale per i 5 piani del capitolo, anche il piano del boss), o il
; brano del boss finale al piano MAXLEVEL; motivetto di combattimento a caso (senza usare rnd: non deve alterare la
; generazione). Se il brano e' gia' nel buffer non si rilegge (snd_get): fra i piani dello stesso capitolo niente disco.
music_dungeon:
        lda #SND_NFIG
        ldx #SND_FIG0
        ldy #1
        jsr mus_pick
        ldx #1
        jsr snd_get
        lda cur_level
        cmp #MAXLEVEL
        bcc _l
        lda #SND_BOSS
        jmp mus_place
_l      jsr lv_grp              ; A = capitolo
        tax
        lda snd_lvl_c-1,x
; A = brano: nel buffer del luogo (dal disco solo se non c'e' gia'), poi richiesta (dissolvenza lenta)
mus_place:
        ldx #0
        jsr snd_get
        lda #0
        sta mus_sv
        sta mus_cmb
        sta mus_inc
        lda #MUS_LVL
        ldx #FADE_SLOW
        jmp music_request

; A = n, X = primo, Y = buffer (0 luogo, 1 combattimento) -> A = brano a caso fra X e X+n-1, diverso da quello
; gia' nel buffer se n > 1 (ogni cambio di piano cambia musica)
mus_pick:
        sta snd_id
        stx snd_b
        lda $dc04
        eor frame
        eor $d012
        and #$7f
_m      cmp snd_id
        bcc +
        sbc snd_id
        bcs _m
+       clc
        adc snd_b
        tax
        inx                     ; (snd_cur = brano + 1)
        txa
        cmp snd_cur,y
        bne _ok
        lda snd_id
        cmp #2
        bcc _ok
        txa                     ; uguale al precedente: il successivo nell'elenco (circolare)
        sec
        sbc snd_b
        cmp snd_id
        bcc +
        lda #0
+       clc
        adc snd_b
        rts
_ok     dex
        txa
        rts

; A = brano, X = buffer (0 luogo, 1 combattimento): brano nel buffer, letto dal disco (un brano alla volta: nessuna
; copia in RAM, 06/11 sera; se e' gia' nel buffer non si rilegge)
snd_get:
        sta snd_id
        stx snd_b
        tay
        iny
        tya
        cmp snd_cur,x           ; (12/11, TODO M2) gia' nel buffer: niente disco (il buffer e' solo dei brani)
        bne +
        rts
+       sta snd_cur,x
        ldy snd_id
_disk   lda #$53                ; "SND" + cifra
        sta cmdbuf+3
        lda #$4e
        sta cmdbuf+4
        lda #$44
        sta cmdbuf+5
        lda snd_digit,y
        sta cmdbuf+6
        lda #0                  ; 0 finale del nome (Krill)
        sta cmdbuf+7
        lda #4
        sta nlen
        lda #1
        sta io_dir
        sta io_quiet
        lda #3                  ; (15/11, ex TODO A2) fino a 3 letture
        sta snd_try
_ld     jsr _buf0
        jsr load_raw
        bcs _bad
        ldy snd_id              ; (15/11, ex TODO A2) fine del file = buffer + lunghezza del brano (snd_llo/hi): una lettura piu'
        ldx snd_b               ; corta o piu' lunga (Krill non da' errore) si rifa'; il player non parte mai su un buffer
        lda snb_lo,x            ; letto a meta' (sp_next ci girerebbe all'infinito nell'IRQ)
        clc
        adc snd_llo,y
        eor krill_endaddrlo     ; (eor: il riporto resta per il byte alto)
        bne _bad
        lda snb_hi,x
        adc snd_lhi,y
        eor krill_endaddrhi
        beq _ok
_bad    dec snd_try
        bne _ld
        ldx snd_b               ; file mancante o incompleto: niente musica in questo buffer
        lda #0
        sta snd_cur,x
_ok     lda #0
        sta io_quiet
        rts
_buf0   ldx snd_b               ; ptr0 = buffer
        lda snb_lo,x
        sta ptr0
        lda snb_hi,x
        sta ptr0+1
        rts
snb_lo   .byte <SND_LBUF, <SND_FBUF
snb_hi   .byte >SND_LBUF, >SND_FBUF

; ---------------------------------------------------------------- aggiornamento (1 volta per frame)
music_update:
        lda cmb_t
        beq +
        dec cmb_t
+
.if NOMUSIC
        rts
.endif
        lda mus_mute            ; dopo un'operazione su disco: volume di nuovo pieno
        beq +
        lda #0
        sta mus_mute
        lda mus_flt
        ora #$0f
        sta $d418
+       ; --- tema di combattimento (solo mostri forti e boss; isteresi CMB_HOLD x 4 frame)
        lda mus_cmb
        beq _nc
        lda mus_inc
        bne _cd
        lda #1
        sta mus_inc
        lda #MUS_FIGHT
        ldx #FADE_FAST
        jsr music_request
_cd     inc mus_fr
        lda mus_fr
        and #3
        bne _nc
        dec mus_cmb
        bne _nc
        lda #0
        sta mus_inc
        lda #MUS_LVL
        ldx #FADE_SLOW
        jsr music_request
_nc     lda mus_fo
        beq _nf
        dec mus_fo
        bne _ret
        beq _switch
_nf     lda mus_trk
        cmp mus_want
        beq _steady
        lda mus_trk             ; il brano cambia: rilascio lungo su tutte le note (dissolvenza naturale)
        beq _switch
        cmp #MUS_LVL
        bne +
        jsr sp_save             ; il brano del luogo riprendera' da qui
        lda #1
        sta mus_sv
+       lda mus_fsp
        asl
        asl
        asl
        asl
        sta mus_fo              ; 16 frame per unita' di velocita'
        lda #$08                ; rilascio: veloce 300 ms, lento 750 ms
        ldx mus_fsp
        cpx #FADE_SLOW
        bcc +
        lda #$09
+       jsr sp_release
        lda #0
        sta mus_trk             ; (in dissolvenza: nessun brano)
_ret    rts
_switch lda mus_want
        sta mus_trk
        beq _silent
        tax
        lda snd_cur-1,x
        beq _none               ; buffer vuoto (file non letto)
        lda snb_lo-1,x
        sta sp_bl
        lda snb_hi-1,x
        sta sp_bh
        cpx #MUS_LVL
        bne _fresh
        lda mus_sv
        beq _fresh
        jsr sp_resume
        jmp +
_fresh  jsr sp_start
+       lda sp_fmode
        and #$f0
        sta mus_flt
        rts
_none   lda #0
        sta mus_trk
        sta mus_want
_silent jsr sp_stop
        lda #0
        sta $d417
        sta mus_flt
        lda #$0f
        sta $d418
        rts
_steady jmp sp_play

