# Come questo pacchetto sta nel repository del gioco

Copyright © 2026 - Simone Caporale (note di inclusione). Il contenuto del pacchetto è descritto dal suo `README.md`.

| | |
|---|---|
| Pacchetto | `vc64web-custom` = `c64-tools` build **32**, API **25** (file `BUILD`, `headless/APIVER`), con le modifiche qui sotto |
| Archivio ricevuto | `c64-tools-v32-api25.zip`, 13/11/2026 (fornito dal committente, prodotto da un'altra chat; non è un repository git) |
| Cosa contiene | emulatore C64 nel browser (**vc64web**, VirtualC64 in WebAssembly, `third-party/vc64web/`) + il nostro controllo da riga di comando (demone `headless/c64d.js`, client `headless/c64`, `headless/c64-batch`), la pagina portable (`portable/`), documentazione ed esempi |
| Dove lo usiamo | container `barbarian-emu-vc64web` (test di regression `EMU-*`, `tests/lib/emu.py`), video dimostrativi, prove con un bot. Guida: [docs/emulatore.md](../../../docs/emulatore.md) |
| Ruolo | **secondario**: VICE resta l'unico riferimento autorevole |
| Futuro | il committente lo pubblicherà come repository a sé; allora qui resterà solo l'artefatto (l'immagine o le pagine generate). Per questo il pacchetto è **autonomo**: nessun percorso verso il progetto del gioco |

## Struttura (13/11)
```
build.py  BUILD  README.md  Dockerfile  docker-compose.yml  .dockerignore  .gitignore
headless/      demone, client, API (sorgenti del controllo remoto)
portable/      pagina standalone (shell.html, asm/)
roms/          ROM: vice-roms/{C64,DRIVES}/, open-roms/, roms.md (quali file servono, SHA-256, licenze, dove trovarli)
third-party/   vc64web (emulatore), README di ffmpeg, nodejs, playwright
docs/          documentazione del pacchetto, CHANGELOG.md, questo file
examples/      esempi eseguibili
work/          cartelle di lavoro montate in Docker: games/, roms/ (ROM aggiuntive), scripts/
out/           (non in git) pagine generate, se non si passa --out
```
Rispetto allo zip: `roms/` sostituisce `third-party/vice-roms/` e `third-party/open-roms/` (stesso sottoalbero di `roms/` del progetto,
**identico file per file**: lo controlla `./validate_env.sh` del gioco); `games/`, `roms/` (ROM aggiuntive) e `scripts/` sono in
`work/`; `CHANGELOG.md` e queste note in `docs/`; tolti `headless/x` (un PNG con il nome sbagliato) e le cache di Python. I nomi
`headless/` e `portable/` sono rimasti: li usano la documentazione e l'API del pacchetto.

## Modifiche nostre rispetto allo zip
- `build.py`: cartelle come **parametri** (`--vice-roms`, `--open-roms`, `--out`, `--tag`, o le variabili `C64_VICE_ROMS`,
  `C64_OPEN_ROMS`, `C64_OUT`, `C64_IMAGE`), con default relativi al pacchetto (`roms/vice-roms`, `roms/open-roms`, `out`, `c64d`);
  ROM facoltative (le varianti mancanti non entrano nel menu della pagina portable); immagine Docker costruita con il contesto
  `pages=<out>` (`--build-context`) e, se c'e' `C64_CA_BUNDLE`, con la CA come segreto; `--no-ffmpeg-check`.
- `portable/shell.html`: 2 righe (il menu della pagina portable elenca solo le varianti incorporate).
- `Dockerfile`: le pagine arrivano dal contesto `pages`, le ROM da `roms/`; CA facoltativa (`--secret id=ca`) per `npm`/Playwright.
- `.dockerignore`, `docker-compose.yml` (`additional_contexts: pages: ./out`, volumi in `work/`), `headless/c64` (cerca le ROM in
  `roms/` e i giochi in `work/games`).
- Verificato il 13/11 [MISURATO]: con le ROM della nuova `roms/` le due pagine generate sono **byte per byte identiche** a quelle
  della build precedente; l'immagine si costruisce e il demone risponde (`/ping` 200, `c64 start`).

## Nel progetto del gioco
- `docker/images.sh emu-vc64web`: pagine generate nel container `barbarian-builder` (`build.py --no-docker --no-ffmpeg-check --out
  out/vc64web`), poi `docker build -t barbarian-emu-vc64web --build-context pages=out/vc64web third-party-tools/vc64web-custom`.
  Si rifa' solo se cambia il pacchetto (`docker/images.sh --force emu-vc64web`). **Mai** `--bump-version`.
- `./build.sh --emu` / `--release` accendono il container e passano `EMU_URL` ai test.

## Aggiornare il pacchetto
1. Estrarre il nuovo zip in una cartella vuota in `out/tmp/`.
2. Sostituire i file del pacchetto, **senza** `.git` e **senza** `out/`, e **rifare le modifiche** della sezione sopra (si vedono
   con `git diff` sul commit del 13/11); rimettere `roms/` com'è (identica a quella del progetto).
3. `docker/images.sh --force emu-vc64web`, poi `./build.sh --emu` e `docker/run.sh emu-vice python3 tests/run.py -k EMU` (con il demone
   acceso); `git status` pulito tranne i file del pacchetto.
4. Aggiornare [docs/emulatore.md](../../../docs/emulatore.md) se cambiano API o comportamento.

## Licenza
**Non verificata** (vedi `third-party/vc64web/README.md`: forse GPL-3.0 per VirtualC64; le librerie JS hanno licenze proprie).
Prima di pubblicare: controllare licenza di vc64web e di `open-roms` (font PXLfont), e non pubblicare le pagine generate né le
ROM Commodore di `roms/vice-roms/` (TODO `I7` del gioco).
