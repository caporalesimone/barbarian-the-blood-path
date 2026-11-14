# Prototipo di Krill's Loader fuori dal gioco (11/11/2026)

`proto.asm` (64tass): installa il loader, carica due file e il plugin di salvataggio, salva 1 e 8 blocchi, rilegge, e
cronometra ogni passo con i timer della CIA2. `run_vice.py` lo esegue in `x64sc` (disco vero emulato) con il monitor remoto e
stampa i tempi. `loaderconfig.inc` è la configurazione (solo 1541, senza decompressore, uninstall e end-address attivi,
nomi da 8 caratteri) con cui sono stati costruiti i binari. Non fa parte della build.

## Prova a schermo (11/11)
`p3_screen.asm`: install, load, plugin di save, save di 1 blocco e rilettura con esiti scritti a schermo (richiede i binari
di Krill e i file `data`, `save`, `s1` come in proto.asm; disco con `cc1541 -M 8`). VICE x64sc true drive: `INST 0000 LOAD 00 PLUG 00 SAVE 00 READ 00` (tutto ok).
L'emulatore web del committente (VirtualC64 build v32, API 25: demone `c64d` + client `c64`) sta dal 13/11 **nel repository**, in `../lab64/vc64web-custom/` (guida: [docs/emulatore.md](../../docs/emulatore.md), test `EMU-10..16`). Gli script miei per le versioni precedenti sono stati cancellati su richiesta del committente (13 e 12/11).
Prova sull'ordine dei file in directory (106 file da 1 blocco prima/dopo): NON conclusiva (il prototipo non arriva alla fine, save8 = $ff), nessun numero da citare.
