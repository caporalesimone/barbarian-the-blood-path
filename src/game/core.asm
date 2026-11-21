; ===================================================================
;  core.asm - (21/11, TODO D15) segmento CORE: codice di GAME che sta nella RAM sotto il KERNAL (CORE_AT = $E000), non
;  nel PRG. Il KERNAL e' sempre escluso ($01 = MEMCFG), quindi si chiama come il resto del gioco. Costruito come il
;  generatore (tools/build/asm.sh, due passate): la prima passata lo assembla dopo il PRG (core_raw..core_raw_end) e
;  tools/build/gen_imgz.py ne scrive il file "core" (out/work/core.prg); la seconda passata ha solo le etichette.
;  Si legge dal disco (core_need, src/game/stash.asm) alla prima schermata e dopo ogni uso dell'immagine del salvataggio
;  (SV_IMG e il plugin di save stanno sopra CORE): sv_read e sv_save lo segnano da rileggere (core_ok = 0), sv_write lo
;  rilegge subito, ui_begin e main_loop lo rileggono se manca.
;  Ci stanno solo routine delle schermate (dopo ui_begin CORE c'e' sempre). Fine: core_end, al massimo dove comincia
;  l'appoggio del file MENU (ML_LO = core_end, tools/build/pack_menu.py) e prima del file del villaggio (GFX_TOWN_AT).
; ===================================================================
        .enc "screen"                   ; (testo delle schermate; alla fine "none", come gli altri moduli)
        .include "slist.asm"            ; liste a scorrimento (inventario, negozi, locanda)
        .include "inv.asm"              ; schermata dell'inventario e descrizione degli oggetti
        .enc "none"
