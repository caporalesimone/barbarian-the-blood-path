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
| `c64-emu-viewer` | `viewer` | Xvnc di KasmVNC (pacchetto ufficiale) + PulseAudio + server Node (`docker/viewer/server.js`): centro di controllo, schermo con audio, `out/`, overlay con tastiera C64 e joystick (`/input`), `/control` verso il lettore. |
| `c64-emu-vc64web` | (Dockerfile di `vc64web-custom/`) | node, Playwright + Chromium, ffmpeg, demone dell'emulatore nel browser |

Cambiare Ubuntu: `ARG UBUNTU` in `docker/Dockerfile`, poi `images.sh --force` (ricompila anche VICE, zx0 e cc1541 sulla base nuova).

## Script

| Script | Cosa fa |
|---|---|
| `images.sh [--force] [nomi]` | costruisce le immagini mancanti (`builder emu-vice emu-viewer emu-vc64web`); scarica sull'host il tarball di VICE se manca |
| `run.sh <immagine> [comando]` | esegue un comando con il progetto in `/work`, con l'utente dell'host; `builder` = `c64-builder`, un nome completo si usa cosi' com'e' |
| `viewer.sh start\|stop\|exec` | http://localhost:6080: centro di controllo (stato di build e test, una scheda per versione di `out/releases/`, andamento e confronto), schermo dal vivo con audio (KasmVNC + PulseAudio), vc64web nel browser, `out/` del progetto; `exec <comando>` = comando in `c64-emu-vice` collegato a schermo e audio. Con `C64_VIEW_PLAYER` avvia anche `c64-emu-player` |
| `viewer_player.py` | lettore del viewer (container `c64-emu-player`): avvia `C64_VIEW_PLAYER <file>` sullo schermo dal vivo quando lo chiede la pagina (`POST /control`), da un socket Unix nel volume `c64-x11`; il viewer non ha il socket di Docker |
| `memmap/c64map.py` | mappa della memoria e del disco **automatica**, senza configurazione (nel container `c64-builder`): legge i listati di 64tass (`-L`), le etichette (`-l`), i PRG e il `.d64`; scrive `index.html` e `memmap.json`. `--work`, `--disk`, `--out`, `--title` (default `C64_VIEW_TITLE`). Analisi statica: limiti nella pagina |
| `validate_env.sh` | controlla l'host: sistema, WSL e posizione del progetto, Docker, fine riga, ROM, immagini, tool |

## Configurazione del progetto (`toolchain.env`)

| Variabile | Uso |
|---|---|
| `C64_PASS_ENV` | variabili dell'host passate ai container da `run.sh` (oltre a `EMU_URL`, `C64_VIEW`, `DISPLAY`) |
| `C64_EXTRA_IMAGES` | immagini del progetto controllate da `validate_env.sh` |
| `C64_VIEW_DISK` | disco proposto per primo nella pagina del viewer (modello con `*`, vince la versione piu' alta) |
| `C64_VIEW_TITLE` | nome del progetto nella testata della pagina del viewer |
| `C64_VIEW_PLAYER` | comando che apre un file (`.d64 .g64 .prg .t64 .crt`, percorso relativo al progetto; `--bare` = senza disco) sullo schermo del viewer; se manca, i pulsanti VICE della pagina sono spenti |
| `C64_KRILL_ZIP` | zip di Krill's Loader da cui si compila cc1541 |

Altre variabili: `C64_CA_BUNDLE` (CA di un proxy che intercetta TLS, segreto per npm/pip nelle build), `C64_DOCKER_ARGS` (opzioni di
`docker run` in piu'), `VIEW_PORT`, `VIEW_PASSWORD` (password di tutto il viewer, di default nessuna), `VIEW_SIZE`, `VIEW_HOSTS` (nomi di host ammessi oltre
a localhost: il server rifiuta gli altri contro il DNS rebinding).

## Manifest per il viewer (contratto con il progetto, 14/11)

La pagina del viewer (`docker/viewer/www/index.html`) e' generica: legge solo questi file, che scrive il progetto. Tutto e' facoltativo
tranne `files`; un campo che manca non si mostra.

`out/releases/v<V>/manifest.json` (una cartella per versione; `out/releases/latest` = collegamento all'ultima):

| Campo | Contenuto |
|---|---|
| `schema` | 1 |
| `version`, `branch`, `built_at`, `updated_at`, `release` | versione, ramo git, date ISO 8601 UTC, `true` se e' una release |
| `files` | `{nome: {group, type: file\|dir, files, bytes, sha256, produced}}`: i `.d64` fra questi hanno i pulsanti vc64web / VICE / download |
| `groups` | `{gruppo: etichetta}`: come mostrare i gruppi di `files` e di `missing` |
| `missing` | gruppi non generati in questa versione |
| `tests` | `{ran, suites[], total, pass, fail, skip, seconds}`; il dettaglio in `test_report.json` (`{suites, total_s, results: [{id, suite, desc, result PASS\|FAIL\|SKIP, reason, time}]}`) |
| `stats.metrics` | misure del progetto: `[{id, label, value, unit: B\|s\|"", better: up\|down\|null, hint}]` (schede, andamento, confronto) |
| `stats.info` | `[{label, value}]`: dati da mostrare e confrontare, senza grafico |
| `stats.disk` | `{blocks_total, blocks_free, blocks_used, files: [{name, type, blocks}]}` (directory del disco) |
| `stats.git` | `{commit, subject, dirty}` |
| `stats.build_seconds` | durata della build |

Stato dal vivo, in `out/tmp/` (riscritti in modo atomico: file temporaneo e rinomina):
- `build.json`: `{state: running|ok|fail, phase, flags, started, updated}` (tempi in secondi Unix);
- `tests.json`: `{state, suites, filter, total, started, updated, seconds, current: {id, suite, desc, since}, results: [come sopra], caps}`.

In questo progetto li scrivono `tools/build/publish.py`, `build.sh` e `tests/run.py`.

## Programmi esterni

| Cartella | Programma | Licenza | Come si ottiene |
|---|---|---|---|
| `vice/` | VICE 3.10 (emulatore di riferimento, interfaccia gtk3) | GPL-2.0 (`vice/LICENSE`) | tarball ufficiale scaricato sull'host in `vice/download/` (`VICE_VERSION`, `VICE_URL`), compilato nello stage `vice-build` |
| `zx0/` | ZX0 v2.2 di Einar Saukas (compressore) | BSD-3 (`zx0/LICENSE`) | sorgenti C in git, compilati nello stage `zx0-build` |
| `cc1541/` | cc1541 (scrive i dischi .d64) | MIT (`cc1541/LICENSE`) | dallo zip di Krill (`C64_KRILL_ZIP`), compilato nello stage `cc1541-build` |
| `vc64web-custom/` | la nostra variante di vc64web: emulatore nel browser + controllo da riga di comando | vedi `vc64web-custom/docs/INCLUSIONE.md` (non verificata) | pacchetto autonomo; immagine `c64-emu-vc64web` (`images.sh emu-vc64web`) |
| `kasmvnc/` | KasmVNC 1.5.2 (server X con client web) | GPL-2.0 (`kasmvnc/LICENSE`) | pacchetto ufficiale `.deb` per Ubuntu 24.04, scaricato sull'host in `kasmvnc/download/` (`KASMVNC_VERSION`), estratto nel target `viewer` |
| `roms/` | ROM del C64 (`vice-roms/{C64,DRIVES}`, `open-roms/`) | vedi `roms/roms.md` | in git; identica a `vc64web-custom/roms/` (`validate_env.sh` lo controlla) |

Dettagli per il gioco: `docs/getting-started.md` e `docs/build.md` (sezione 4b) del progetto.
