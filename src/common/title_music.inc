; ===================================================================
;  title_music.inc - Demon's Eye (brano del titolo) con il player unico, per i programmi che girano con l'IRQ del KERNAL
;  (HELP e BARBARIAN, 15/11, TODO E3/E4). In comune fra i due: il codice sta qui, ognuno dice dove tiene le variabili.
;
;  Da definire prima dell'include:   SP_VARS = indirizzo delle variabili del player (SP_VSIZE byte, RAM libera)
;  (si includono qui anche sid_player.inc senza sp_resume / sp_release, sid_title.inc = il brano di START e LORE)
;  API (tutte con gli interrupt gestiti qui dentro):
;    tm_start   azzera il SID, avvia il brano da capo e installa il clock; torna con l'I flag **acceso** (il chiamante fa cli)
;    tm_stop    sei, brano fermo, SID tutto a 0 (volume compreso), vettore IRQ e CIA1 come all'accensione: da chiamare
;               PRIMA di ogni LOAD del KERNAL (il codice del programma verra' sovrascritto) o dell'uscita
;
;  Clock: NON l'IRQ del KERNAL com'e' (e' un timer a ~60 Hz, non verificato a 50 Hz PAL): CIA1 timer A con latch a
;  19656 cicli = 312 righe x 63 cicli, un fotogramma PAL esatto (stesso passo del raster IRQ di START e LORE). Il vettore $0314
;  punta a tm_irq: suona e prosegue nella routine del KERNAL ($EA31: tastiera per GETIN, conferma del CIA), quindi GETIN
;  e il programma non cambiano. Nessun IRQ del VIC.
;  Voci: come START (lead sulla voce 1 del SID: SP_V0 = 0), non come il gioco (7, 0, 14).
; ===================================================================
TM_LATCH = 19656 - 1            ; il timer conta latch + 1 cicli
KERNAL_LATCH = $4025            ; 16421 cicli: valore del KERNAL PAL (IOINIT), per il ripristino
KERNAL_IRQ   = $ea31

SP_V0   = 0
SP_V1   = 7
SP_V2   = 14
SP_RESUME = 0                   ; niente sp_resume / sp_release
        .include "sid_player.inc"
        .include "sid_title.inc"        ; out/work/sid_title.inc (tools/build/gen_music.py): il brano
        .cerror SP_VARS + SP_VSIZE > $d000, "variabili del player oltre $CFFF"

; Demon's Eye con il player unico: SID azzerato, brano dall'inizio, vettore IRQ su tm_irq e CIA1 timer A con il
; latch di un fotogramma PAL (TM_LATCH), ricaricato subito
tm_start:
        sei
        ldx #$18                ; SID azzerato
        lda #0
_c      sta $d400,x
        dex
        bpl _c
        sta sp_mute
        sta sp_mute+1
        sta sp_mute+2
        sta sp_once
        lda #<sid_title
        sta sp_bl
        lda #>sid_title
        sta sp_bh
        jsr sp_start
        lda #<tm_irq
        sta $0314
        lda #>tm_irq
        sta $0315
        lda #<TM_LATCH
        sta $dc04
        lda #>TM_LATCH
        sta $dc05
        lda $dc0e               ; bit 4 = carica il latch subito (il conto riparte da qui)
        ora #$11
        sta $dc0e
        rts

; musica ferma: player fermo, SID tutto a 0, IRQ e CIA come prima (prima del LOAD del KERNAL)
tm_stop:
        sei
        jsr sp_stop
        ldx #$18                ; SID tutto a 0: voci, filtro e volume
        lda #0
_c      sta $d400,x
        dex
        bpl _c
        lda #<KERNAL_IRQ
        sta $0314
        lda #>KERNAL_IRQ
        sta $0315
        lda #<KERNAL_LATCH
        sta $dc04
        lda #>KERNAL_LATCH
        sta $dc05
        lda $dc0e
        ora #$11
        sta $dc0e
        lda $dc0d               ; eventuale IRQ del timer in sospeso: confermato
        rts

; IRQ del CIA1 a 50 Hz: un passo del player, poi l'IRQ del KERNAL (tastiera)
tm_irq:
        jsr sp_play
        jmp KERNAL_IRQ
