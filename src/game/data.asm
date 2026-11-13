; ===================================================================
;  tabelle e dati
; ===================================================================
        .include "gfx_consts.inc"

maprow_lo
        .for i = 0, i < 49, i = i + 1
        .byte <(MAP + i*MAPW)
        .next
maprow_hi
        .for i = 0, i < 49, i = i + 1
        .byte >(MAP + i*MAPW)
        .next
mul12   .byte 0, 12, 24, 36

.if TESTBUILD && TESTFZ
testscript                      ; corsa nel villaggio (TESTLVL=0, TESTX/TESTY): TESTFZS 0 orizzontale,
.if TESTFZS == 0                ; 1 verticale, 2 diagonale (misura dei fotogrammi persi: TESTFZ)
        .byte 0, 255, 0, 30
        .byte 8, 255, 0, 90
        .byte 4, 255, 0, 90
.elsif TESTFZS == 1
        .byte 0, 255, 0, 30
        .byte 2, 255, 0, 110
        .byte 1, 255, 0, 110
.else
        .byte 0, 255, 0, 30
        .byte 10, 255, 0, 22
        .byte 5, 255, 0, 22
        .byte 10, 255, 0, 22
        .byte 5, 255, 0, 22
        .byte 10, 255, 0, 22
        .byte 5, 255, 0, 22
.endif
        .byte 0, 0, 0, 0
.elsif TESTBUILD && TSV
testscript                      ; camminata verticale lunga (misure di scroll)
        .byte 0, 255, 0, 30
        .byte 2, 255, 0, 120
        .byte 1, 255, 0, 120
        .byte 2, 255, 0, 120
        .byte 0, 0, 0, 0
.elsif TESTBUILD && TESTSK
testscript                      ; tasto F1 dopo 20 frame
        .byte 0, 255, 0, 20
        .byte 0, 0, $10, 4
        .byte 0, 255, 0, 200
        .byte 0, 0, 0, 0
.elsif TESTBUILD && TESTFIRE
testscript                      ; un passo a sinistra (sulla scala), attende, poi Fire (4 frame)
        .byte 0, 255, 0, 20
        .byte 4, 255, 0, TESTFIRE
        .byte 0, 255, 0, 40
        .byte 16, 255, 0, 4
        .byte 0, 0, 0, 0
.elsif TESTBUILD && TESTX
testscript                      ; posizione fissata: nessun input scriptato
        .byte 0, 0, 0, 0
.elsif TESTBUILD
testscript
        .byte 0, 255, 0, 20
        .byte 16, 255, 0, 4
        .byte 0, 255, 0, 20
        .byte 16, 255, 0, 4
        .byte 0, 255, 0, 60
        .byte 0, 7, 128, 4
        .byte 0, 255, 0, 20
        .byte 2, 255, 0, 4
        .byte 0, 255, 0, 8
        .byte 2, 255, 0, 4
        .byte 0, 255, 0, 8
        .byte 16, 255, 0, 4
        .byte 0, 255, 0, 20
        .byte 0, 1, 32, 4
        .byte 0, 255, 0, 250
        .byte 0, 0, 0, 0
        .byte 0, 0, 0, 0
.endif
