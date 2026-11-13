# Esempi

Copyright © 2026 Simone Caporale. Esempi eseguibili, provati sulla build 26 (API 19). Riferimento completo dei comandi: `docs/c64-cli.md`; sintassi degli script: `docs/scripting.md`.

## Prima di cominciare
```sh
python3 build.py --no-docker                  # una volta: genera out/c64-headless.html
cd headless && npm install && npx playwright install chromium
export NODE_PATH=$(npm root -g)               # solo se playwright è globale
node c64d.js &                                # demone sulla porta 7064
node c64 start                                # avvia l'emulatore
```
`ffmpeg` serve solo per i video deterministici (`06`, script `04`/`05`) e per convertire il `.webm` (`07`). I file prodotti dagli script shell finiscono in `$TMPDIR/c64-examples-output` (di solito `/tmp/c64-examples-output`; cambiabile con `OUT=/percorso`), fuori dal pacchetto.

## Script di input — `scripts/` (si lanciano con `c64 --outdir output script FILE`)
| File | Cosa mostra | Note |
|---|---|---|
| `01-ciao.txt` | `wait`, `text`, `assert screen`, `screenshot` | |
| `02-memoria.txt` | `poke`, `assert mem=`, `wait mem=` | |
| `03-joystick.txt` | joystick porta 2 (`JOY2-UP`, `JOY2-UP&JOY2-FIRE`) e lettura di `$DC00` | |
| `04-video.txt` | `video start` / `video stop` (chiusura garantita) | core fermo (`c64 pause`), ffmpeg |
| `05-video-keep.txt` | `video start … keep`, chiusura con `c64 --out lungo.mp4 videoStop` | core fermo, ffmpeg |
| `06-rec.txt` | `rec start` / `rec stop`: genera `sessione.txt` | |
| `07-regressione.txt` | `saveState`/`loadState`, `regress save`/`check` con `ignore=` | |
| `08-testo-e-call.txt` | `wait text` (screen code), `call` di una routine KERNAL, `call … nowait` | |

Partenza consigliata per gli script: `c64 reset '{"hard":true}'`, `c64 resume`, `c64 ready`, `c64 pause` (stato noto, core fermo).

## Cicli di controllo — `loops/` (`c64 runLoop "$(cat FILE)" '{"frames":300,"every":2}'` oppure `c64 video FILE`)
| File | Cosa mostra |
|---|---|
| `bot-joy.js` | `joy(porta,stato,frames)` dentro `runLoop` (preme e rilascia senza avanzare il tempo), `state` persistente |
| `bot-input.js` | bot con tutti i tipi di input (joystick tenuto e a durata, tasti tenuti e a durata) e carico CPU variabile: usato da `shell/11-determinismo.sh` |
| `conta-memoria.js` | `peek`/`poke` a ogni passo e uscita con `return false` |

## Comandi da shell — `shell/` (`sh examples/shell/NN-….sh`; usano `common.sh`)
| File | Cosa mostra |
|---|---|
| `01-avvio-e-testo.sh` | `start`, `sendText`, `runFrames`, `screenText`, `state`, `screenshot` |
| `02-memoria-e-schermo.sh` | `pokeRange`, `peek`, `peekWord`, `dump`, `find`, `findText`, `cursor`, `screenSave`, `screenDiff` |
| `03-debug.sh` | `regs`, `disasm`, `step`, `trace` (con `max`), `ramSnap`/`ramDiff`, `call`, `breakpoint` |
| `04-stati-e-regressione.sh` | `saveState`/`loadState` (anche da file), `regress save`/`check` (exit code) |
| `05-disco.sh` | crea un D64 di prova (`tools/mk_d64.py`), `attach` con core in marcia, `LOAD`/`RUN`, `driveState` |
| `06-video-deterministico.sh` | `c64 video` da script, da ciclo JS e da N fotogrammi |
| `07-video-e-audio-dal-browser.sh` | `grabBrowserVideoAndAudio` (a tempo, e start/stop separati), `audioGain`, conversione in mp4 |
| `08-job-lunghi.sh` | `status` e `abort` di un job lungo |
| `09-rom.sh` | `roms`, `rom kernal …`, ROM utente attive, `clearRoms` |
| `10-ciclo-in-pagina.sh` | `runLoop` con i file di `loops/` |
| `11-determinismo.sh [N] [PASSI]` | prova di regressione del determinismo (API 24): bersaglio che legge joystick e tastiera ($DC00 + buffer KERNAL), N esecuzioni + 2 con ripetizioni forzate, hash identici; exit 1 se diverso |

## Strumenti — `tools/`
- `mk_d64.py [uscita.d64]`: crea un disco D64 formattato con un programma BASIC `HELLO` (`10 PRINT"HELLO FROM D64"`). Provato: `LOAD"HELLO",8` + `RUN` stampa `HELLO FROM D64`.

## Cosa non è verificato
- Gli esempi sono stati eseguiti uno alla volta su un demone di sviluppo (Chromium headless, senza scheda audio). Non provati: Docker, Windows, macOS.
- `07` registra un tono SID generato con `poke`: il livello audio dipende dal core (molto basso, vedi `audioGain`).
- Nessun esempio usa un gioco reale: servono i tuoi file in `games/`.
