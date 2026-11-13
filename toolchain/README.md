# toolchain/ — toolchain C64 in container

Copyright © 2026 - Simone Caporale (note). Ogni programma esterno ha nella sua cartella la licenza e il suo `.gitignore`.

Ambiente **generico** per costruire e provare programmi per il Commodore 64: immagini Docker, programmi esterni compilati una volta,
ROM e script per usarli. **Non sa nulla del gioco**: il progetto che la usa la configura con un file `toolchain.env` nella sua
radice (la cartella sopra `toolchain/`, oppure `C64_PROJECT`). Il progetto si monta nei container in `/work`.

## Immagini

Un solo Dockerfile multi-stage, `docker/Dockerfile`: una immagine per target, tutte con lo stesso genitore.

| Immagine | Target | Contenuto |
|---|---|---|
| (nessuna) | `base` | ubuntu (`ARG UBUNTU`, oggi 24.04) + CA + locale + `/work`. Genitore comune: **non ha un nome**, non si avvia mai |
| (nessuna) | `tools-builder`, `vice-build`, `zx0-build`, `cc1541-build` | compilatori e librerie di sviluppo; compilano i programmi esterni. Restano nella cache di BuildKit, non diventano immagini |
| `c64-builder` | `builder` | 64tass, cc65, make, perl, zip, git, Python 3 con Pillow, PyYAML, NumPy, Matplotlib; zx0 e cc1541 in `/opt/c64/bin` |
| `c64-emu-vice` | `emu-vice` | builder + VICE (`x64sc`, `c1541` e i dati in `/opt/vice`), librerie gtk3, Xvfb, ffmpeg |
| `c64-emu-viewer` | `viewer` | Xvfb + x11vnc + noVNC + pagina indice (`docker/viewer/`) |
| `c64-emu-vc64web` | (Dockerfile di `vc64web-custom/`) | node, Playwright + Chromium, ffmpeg, demone dell'emulatore nel browser |

Cambiare Ubuntu: `ARG UBUNTU` in `docker/Dockerfile`, poi `images.sh --force` (ricompila anche VICE, zx0 e cc1541 sulla base nuova).

## Script

| Script | Cosa fa |
|---|---|
| `images.sh [--force] [nomi]` | costruisce le immagini mancanti (`builder emu-vice emu-viewer emu-vc64web`); scarica sull'host il tarball di VICE se manca |
| `run.sh <immagine> [comando]` | esegue un comando con il progetto in `/work`, con l'utente dell'host; `builder` = `c64-builder`, un nome completo si usa cosi' com'e' |
| `viewer.sh start\|stop` | pagina indice su http://localhost:6080: VICE dal vivo (noVNC), ultima build in vc64web nel browser, `out/` del progetto |
| `validate_env.sh` | controlla l'host: sistema, WSL e posizione del progetto, Docker, fine riga, ROM, immagini, tool |

## Configurazione del progetto (`toolchain.env`)

| Variabile | Uso |
|---|---|
| `C64_PASS_ENV` | variabili dell'host passate ai container da `run.sh` (oltre a `EMU_URL`, `C64_VIEW`, `DISPLAY`) |
| `C64_EXTRA_IMAGES` | immagini del progetto controllate da `validate_env.sh` |
| `C64_VIEW_DISK` | disco proposto per primo nella pagina del viewer (modello con `*`, vince la versione piu' alta) |
| `C64_KRILL_ZIP` | zip di Krill's Loader da cui si compila cc1541 |

Altre variabili: `C64_CA_BUNDLE` (CA di un proxy che intercetta TLS, segreto per npm/pip nelle build), `C64_DOCKER_ARGS` (opzioni di
`docker run` in piu'), `VIEW_PORT`, `VIEW_PASSWORD` (password VNC, di default nessuna), `VIEW_SIZE`.

## Programmi esterni

| Cartella | Programma | Licenza | Come si ottiene |
|---|---|---|---|
| `vice/` | VICE 3.10 (emulatore di riferimento, interfaccia gtk3) | GPL-2.0 (`vice/LICENSE`) | tarball ufficiale scaricato sull'host in `vice/download/` (`VICE_VERSION`, `VICE_URL`), compilato nello stage `vice-build` |
| `zx0/` | ZX0 v2.2 di Einar Saukas (compressore) | BSD-3 (`zx0/LICENSE`) | sorgenti C in git, compilati nello stage `zx0-build` |
| `cc1541/` | cc1541 (scrive i dischi .d64) | MIT (`cc1541/LICENSE`) | dallo zip di Krill (`C64_KRILL_ZIP`), compilato nello stage `cc1541-build` |
| `vc64web-custom/` | la nostra variante di vc64web: emulatore nel browser + controllo da riga di comando | vedi `vc64web-custom/docs/INCLUSIONE.md` (non verificata) | pacchetto autonomo; immagine `c64-emu-vc64web` (`images.sh emu-vc64web`) |
| `roms/` | ROM del C64 (`vice-roms/{C64,DRIVES}`, `open-roms/`) | vedi `roms/roms.md` | in git; identica a `vc64web-custom/roms/` (`validate_env.sh` lo controlla) |

Dettagli per il gioco: `docs/getting-started.md` e `docs/build.md` (sezione 4b) del progetto.
