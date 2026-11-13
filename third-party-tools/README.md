# third-party-tools/ — programmi esterni (non codice per il C64)

Copyright © 2026 - Simone Caporale (note). Ogni cartella ha la licenza del programma e il suo `.gitignore`.

| Cartella | Programma | Licenza | Come si ottiene |
|---|---|---|---|
| `vice/` | VICE 3.10 (emulatore di riferimento, interfaccia gtk3) | GPL-2.0 (`vice/LICENSE`) | `third-party-tools/build.sh vice`: tarball ufficiale scaricato sull'host in `vice/src/`, compilato in `vice/bin/` |
| `zx0/` | ZX0 v2.2 di Einar Saukas (compressore) | BSD-3 (`zx0/LICENSE`) | sorgenti C in git; `third-party-tools/build.sh zx0` -> `zx0/bin/zx0` |
| `cc1541/` | cc1541 (scrive i dischi .d64) | MIT (`cc1541/LICENSE`) | dallo zip di Krill (`src/third-party/krill`); `third-party-tools/build.sh cc1541` -> `cc1541/bin/cc1541` |
| `vc64web-custom/` | la nostra variante di vc64web: emulatore nel browser + controllo da riga di comando | vedi `vc64web-custom/docs/INCLUSIONE.md` (non verificata) | pacchetto autonomo; immagine `barbarian-emu-vc64web` (`docker/images.sh emu-vc64web`) |

`build.sh` (sull'host) crea il container usa e getta `barbarian-tools-builder` (`docker/tools-builder`), vi esegue `build_tools.sh`
e poi cancella container e immagine: i programmi si compilano **una volta** e restano in `*/bin` (non in git). `./build.sh` lo chiama
da solo se manca un binario. Dettagli: `docs/build.md` sezione 4b.
