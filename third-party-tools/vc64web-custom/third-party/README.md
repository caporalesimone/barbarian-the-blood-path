# third-party

Una cartella per ogni componente di terze parti, ciascuna con un `README.md` che dice cos'è, da dove viene (link) e con che licenza. **Le licenze sono quelle che ho potuto leggere nei file o ricordare: dove scrivo «non verificata» controllare prima di pubblicare.**

| Cartella | Contenuto | Incluso | Nota |
|---|---|---|---|
| `vc64web/` | emulatore (wasm + JS) | sì | licenza non verificata (GPL?) |
| `vice-roms/` | ROM Commodore compatibili (7 Kernal, 2 chargen, Basic, drive 1541 e 1541-II) | sì, anche nel repo | **diritti di ridistribuzione da verificare** |
| `open-roms/` | ROM libere | sì | LGPL-3+; font PXLfont da verificare |
| `playwright/` | Chromium headless | no | solo documentazione |
| `ffmpeg/` | encoder video | no | solo documentazione |
| `nodejs/` | runtime | no | solo documentazione |

Gli HTML generati in `out/` (portable e headless) **incorporano** vc64web e le ROM VICE di default: vanno trattati come il più restrittivo dei componenti inclusi.
