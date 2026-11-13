; ===================================================================
;  theme.asm - tema grafico di un piano e bit di visita
;
;  (11/11, ramo fast-loader) Il precaricamento in sottofondo del tema (pf_*, ex prefetch.asm) e le cache della
;  grafica (gfx_town, gfx_theme, fin_ok), del modulo MENU e del brano sono stati tolti per provare il caricatore
;  veloce senza trucchi: ogni ingresso in un luogo rilegge i suoi file dal disco. Restano le due tabelle.
; ===================================================================
PF_END  = $fd00                 ; fine della zona del modulo MENU (MR2_END) e inizio di FMAP (FIN_AT)

; A = piano (1..) -> A = numero del file GFXn (12/11: un file per capitolo c = 1..CHAPTERS, tile + sprite dei mostri):
; GFX(2c-1) = piani del dungeon del capitolo, GFX(2c) = piano del boss (oggi solo il piano MAXLEVEL, sala del trono;
; i file del boss dei capitoli 1-3 sono segnaposto non ancora usati). Calcolo: lv_grp (rel.asm, A = capitolo 1..).
lvl_theme:
        cmp #MAXLEVEL
        bne +
        lda #2*CHAPTERS         ; boss dell'ultimo capitolo
        rts
+       jsr lv_grp
        asl                     ; 2c
        cpx #CH_LV-1            ; piano del boss del capitolo: GFX(2c), tile della sala del trono (12/11)
        beq +
        sec
        sbc #1                  ; 2c - 1
+       rts

; A = piano (1..16) -> X = byte di c_vis (0/1), A = bit del piano
vis_bit:
        sec
        sbc #1
        pha
        lsr
        lsr
        lsr
        tax
        pla
        and #7
        tay
        lda bitmask,y
        rts
