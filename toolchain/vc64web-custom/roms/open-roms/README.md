# Open ROMs (Kernal/Basic/chargen liberi)

**Cos'è**: sostituti liberi delle ROM Commodore (progetto Open ROMs, MEGA65). Qui sono le tre immagini della variante «generic» (`kernal_generic.rom`, `basic_generic.rom`, `chargen_pxlfont_2.3.rom`), usate dall'emulatore solo se mancano le ROM Commodore. Limiti noti: niente floating point nel Basic (`PRINT 2+3` dà `?NOT IMPLEMENTED ERROR`).

**Origine**: https://github.com/MEGA65/open-roms (checkout usato: commit `ad178dbe4d48cd6a317737a8e0e7e662f7e33d32`, 16/05/2026). Come sono state generate le tre immagini (build dal sorgente o copia da un rilascio) non è registrato in questo progetto.

**Licenza**: GNU LGPL v3 o successiva per il pacchetto (verificato nel file `LICENSE`, copiato qui con `CREDITS.md`); alcuni file Basic sono sotto licenza MIT (Microsoft), come indicato in `LICENSE`. Il font del chargen (PXLfont, di Retrofan secondo `CREDITS.md`) ha una licenza propria che **non ho verificato**: controllarla prima di pubblicare il chargen.
