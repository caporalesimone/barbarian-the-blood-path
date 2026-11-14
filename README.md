# Barbarian: The Blood Path

![Barbarian: The Blood Path](docs/title.png)

Action RPG per Commodore 64 scritto in assembly 6502 (64tass). Copyright © 2026 - Simone Caporale.

Avvio sul C64: `LOAD"BARBARIAN",8` e `RUN`: un menu con tre voci, la storia (lore), il manuale, il gioco
([Avvio e storia](docs/intro.md)). Il disco è per la **1541** (e compatibili): il gioco carica e salva con
Krill's Loader ([Fast loader](docs/FastLoader.md)).

## Per iniziare
Tutto gira in container Docker: sull'host servono solo sh, Docker, git e curl. **Guida completa: [docs/getting-started.md](docs/getting-started.md)**
(cartelle, container, build, test, dove finiscono i file).
```
./validate_env.sh        # controllo dell'ambiente (la prima volta; su Windows: progetto dentro WSL2)
./build.sh               # TUTTO: disco + mappe RAM/disco + atlante + smoke e sanity + manuale PDF
./build.sh --fast        # build veloce: solo il disco (salta atlante, mappe e manuale); smoke e sanity restano
./build.sh --fast --no-test   # il minimo: solo il disco, senza test
./build.sh --release     # build completa + tutti i test (anche regression ed EMU-*) + manuale (solo su richiesta)
./build.sh --view        # i test in VICE visibili dal vivo nel browser: http://localhost:6080
toolchain/run.sh builder tools/build/mkdisk.sh       # un comando qualunque in un container
```
Il disco finisce in `out/releases/latest/blood_path_vX.Y_1541.d64` (POKE 1020,1 prima del RUN = subito il gioco).

### Parametri di `./build.sh`
Si combinano liberamente (es. `./build.sh --no-atlas --no-manual`). Senza parametri si costruisce **tutto**.

| Parametro | Effetto |
|---|---|
| *(nessuno)* | disco + mappe RAM/disco + atlante grafico + smoke e sanity + manuale PDF |
| `--fast` | salta atlante, mappe e manuale (= `--no-atlas --no-maps --no-manual`): resta il disco e i test smoke e sanity |
| `--no-atlas` | salta l'atlante grafico (`out/atlas/`) |
| `--no-maps` | salta le mappe della RAM e del disco (`out/memory-map/`) |
| `--no-manual` | salta il manuale PDF |
| `--no-test` | salta smoke e sanity |
| `--release` | build completa + **tutti** i test (anche regression ed `EMU-*` su vc64web) + manuale + `tools/build/release.sh` (GAME compresso in modo ottimo) |
| `--emu` | i test con il demone vc64web acceso (`EMU-*`) |
| `--view` | i test aprono VICE sullo schermo del viewer (http://localhost:6080) |
| `--manual` | **solo** il manuale PDF, senza rifare il disco |
| `--images` | rifa' tutte le immagini Docker, poi la build |
| `--keep N` | quante versioni tenere in `out/releases/` (default 5; anche `KEEP_VERSIONS=N`) |

Ogni build pubblica i suoi artefatti in `out/releases/v<versione>/` (con `manifest.json`: cosa contiene, SHA-256, esito dei test, cosa manca)
e aggiorna `out/releases/latest`. Il manuale di una versione c'e' solo se e' stato generato per quella versione.
Versione del gioco e del formato dei salvataggi: `version.yaml`.

## Struttura
| Cartella | Contenuto |
|---|---|
| `src/` | sorgenti assembly del gioco: uno per file del disco (`barbarian.asm` loader, `start.asm` avvio, `game.asm`, `lobby.asm`, `menu.asm`, `lore.asm`, `help.asm`, `jukebox.asm`), parti incluse in `common/`, `game/`, `menu/`, `lore/`, `test/`; librerie esterne per il C64 in `third-party/` (Krill's Loader) |
| `data/` | dati sorgente (regole e bilanciamento, mappa del villaggio, testi, immagine del titolo, gruppi dell'atlante) |
| `tools/` | `build/` generatori e build, `atlas/` atlante grafico, `memory-map/` mappe RAM e disco, `manual/` manuale, `simulators/` simulatori, `vice/` strumenti in VICE (screenshot, misure, arena), `font/` font della UI |
| `tests/` | test automatici: `smoke/`, `sanity/`, `regression/`, libreria in `lib/` ([docs/test.md](docs/test.md)) |
| `docs/` | wiki del gioco ([indice](docs/README.md)), sorgente del manuale (`docs/manual/`), schermate dei menu (`docs/screens/`) |
| `toolchain/` | toolchain C64 generica ([toolchain/README.md](toolchain/README.md)): immagini Docker `c64-*` (`docker/Dockerfile`) e script `run.sh`, `images.sh`, `viewer.sh`, `validate_env.sh`; sorgenti di VICE, zx0, cc1541 (compilati dentro le immagini); `vc64web-custom/` (secondo emulatore); ROM del C64 in `roms/` (elenco con SHA-256 e licenze in [toolchain/roms/roms.md](toolchain/roms/roms.md)) |
| `toolchain.env` | configurazione della toolchain per il gioco |
| `lab/` | materiale di studio, non usato dalla build ([lab/README.md](lab/README.md)) |
| `out/` | tutto ciò che si genera (non in git): `out/releases/v<versione>/` (ultime 5: disco, atlante, mappe, manuale, report dei test) e gli intermedi della build in corso |

## Arena di combattimento (test e bilanciamento)
Build a parte con lo stesso codice di combattimento del gioco: niente loader, menu, villaggio, disco,
zaino e drop; una stanza, il PG con l'equipaggiamento indossato e da 1 a 8 mostri, comandati da un bot.
La build produce `out/arena_game.prg` (gioco con `ARENA=1`) e `out/arena.prg` (modulo `src/test/arena.asm`
a `$C900`: bot, avvio, fine combattimento, parametri `$CF00`, risultati `$CF40`, registro `$CF80`).
`tools/vice/arena.py` (nel container `c64-emu-vice`: `toolchain/run.sh emu-vice python3 tools/vice/arena.py ...`) avvia VICE, carica i due file e il tema grafico, scrive i parametri ed esegue la serie:
```
toolchain/run.sh emu-vice python3 tools/vice/arena.py --lvl 5 --plvl 5 --weapon sword+1 --armor leather_armor --monster zombie --fights 20 --potions red:3
toolchain/run.sh emu-vice python3 tools/vice/arena.py --help         # tutti i parametri (piano, livello, equipaggiamento, mostri, boss, abilita', pozioni...)
```
Da Python, piu' scenari nella stessa sessione: `from arena import Arena` (vedi `tools/vice/arena.py`).
Fase 1: PG e mostri adiacenti, il bot non si sposta (`--bot stand`): si gira verso il mostro piu' vicino e
attacca (Rage e Frenzy appena pronte, poi l'abilita' migliore pronta, pozione sotto la soglia `--pot`). Nessun seed: stessi parametri,
stessi risultati. Modalita' veloce (default): circa 25 volte il tempo reale in VICE warp.

## Simulatore delle regole nuove
`toolchain/run.sh builder python3 tools/simulators/sim_rules.py` simula il nuovo sistema di combattimento (docs/SISTEMA_COMBATTIMENTO.md) con i
parametri di `data/rules.yaml` e scrive `out/simulators/simulazione_regole.html`. Un solo gruppo:
`python3 tools/simulators/sim_rules.py --fight 5 9 demon skeleton` (piano 5, PG di livello 9).
`python3 tools/simulators/fit_rules.py` ritara i mostri (curve dei piani 1-10, boss finale, tabella dell'Abisso) sul PG di
riferimento e scrive `data/rules.yaml` (`--abyss-only` solo l'Abisso, `--dry` senza scrivere); `python3 tools/simulators/cmp_rules.py`
stampa i confronti di oggetti, abilita' e pozioni (Markdown). Bilanciamento: docs/BILANCIAMENTO.md; piano di
implementazione: la wiki in docs/ (indice docs/README.md).

## Software di terzi

- **Loader by Krill** — Krill's Loader, Repository Version 194 (© 2022 Gunnar Ruthenberg, licenza BSD a 3 clausole
  con attribuzione obbligatoria), https://csdb.dk/release/?id=226124: caricamenti e salvataggi del gioco, e `cc1541`
  (incluso nell'archivio) per scrivere il disco. Archivio, licenza e note in
  [src/third-party/krill/](src/third-party/krill/README.md); come lo usiamo in [docs/FastLoader.md](docs/FastLoader.md).
  Nel gioco il credito è nel menu dei barbari: "loader by krill - v194".
- **vc64web / c64-tools** (13/11, `toolchain/vc64web-custom/`): VirtualC64 di Dirk W. Hoffmann in WebAssembly (porting vc64web) con il
  controllo da riga di comando, usato come **secondo emulatore** per i test `EMU-*` e per i video (VICE resta il riferimento).
  Licenza **non verificata** (probabile GPL-3.0, vedi `toolchain/vc64web-custom/third-party/vc64web/README.md`); la build prende le ROM
  Commodore da `toolchain/roms/` (in git su richiesta, [toolchain/roms/roms.md](toolchain/roms/roms.md); da togliere prima di pubblicare). Provenienza e uso: [toolchain/vc64web-custom/docs/INCLUSIONE.md](toolchain/vc64web-custom/docs/INCLUSIONE.md),
  [docs/emulatore.md](docs/emulatore.md). TODO `I7`.
- **ZX0** v2 di Einar Saukas (BSD-3, `toolchain/zx0/LICENSE`): compressione di `GAME`, `LDAT` e del modulo `MENU`.
- **VICE** 3.10 (GPL-2.0, `toolchain/vice/LICENSE`): emulatore di riferimento per test e misure, compilato dai sorgenti ufficiali.
- **cc1541** (MIT, `toolchain/cc1541/LICENSE`, dal pacchetto di Krill): scrive il disco.
- **Open ROMs** (LGPL-3.0+, `toolchain/roms/open-roms/LICENSE`): ROM libere, ripiego di vc64web.
