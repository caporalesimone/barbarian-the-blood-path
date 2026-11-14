# Build e strumenti

Copyright © 2026 - Simone Caporale

Come si passa dai **sorgenti** (`src/`, `data/`, `tools/`) al **disco** e ai documenti generati (stato del 13/11, v1.227).
**Panoramica di build e test, container e comandi: [Getting started](getting-started.md)** (da leggere prima). Le regole (quando si
fa la build di release, versioni, commit) sono in `CLAUDE.md`; i test in [Test](test.md); la struttura del codice in
[Architettura](architettura.md). Tutti i passi girano nel container `lab64-tools` (i test in `lab64-tools`).

## 1. Il percorso completo (`./build.sh` -> `tools/build/build_game.sh`)

```mermaid
flowchart TD
    V["1. versioni<br/>bump_version.py (version.yaml +1 se i sorgenti cambiano)<br/>gen_version.py -> out/work/version.inc"] --> G
    G["2. generatori<br/>gen_gfx, gen_final, gen_font, gen_music, gen_db"] --> A
    A["3. assemblaggio: tools/build/asm.sh<br/>(sotto, sezione 2)"] --> D
    D["4. disco: tools/build/mkdisk.sh<br/>out/work/disk.d64"] --> M
    M["5. mappe e atlante<br/>out/work/memory-map/, out/work/atlas/<br/>(atlante solo se cambiano i suoi ingressi)"] --> C
    C["6. disco di lavoro out/work/disk.d64"] --> T{"--no-test?"}
    T -->|si'| E1["fine"]
    T -->|no| R["7. test in lab64-tools: tests/run_tests.sh<br/>debug: smoke + sanity; --release: anche regression ed EMU-*"]
```

| Comando | Cosa fa |
|---|---|
| `./build.sh` | **tutto**: disco, mappe, atlante, smoke e sanity (devono passare prima di ogni commit) e manuale PDF |
| `./build.sh --fast` | solo il disco + smoke e sanity (salta atlante, mappe, manuale: `--no-atlas`, `--no-maps`, `--no-manual`, tutti separati) |
| `./build.sh --no-test` | salta smoke e sanity (si combina con `--fast`) |
| `./build.sh --release` | la stessa build (GAME compresso in modo ottimo, `ZX0_BEST=1`) con **tutti** i test (anche regression ed `EMU-*`), manuale PDF (`lab64-pdf-gen`) e `tools/build/release.sh` (senza zip dei sorgenti) (disco, mappe, zip dei sorgenti in `out/`); solo quando la chiede il committente |
| `./build.sh --manual` | solo il manuale (`out/work/manual/`, poi copiato in `out/releases/v<V>/`) |
| `./build.sh --keep N` | quante versioni tenere in `out/releases/` (default 5, anche `KEEP_VERSIONS=N`) |
| `../lab64/run.sh tools tools/build/asm.sh [test]` | solo generatori del gioco + assemblaggio (con `test`: varianti `TESTUI`, `NOKEYS`... per screenshot e prove) |

## 2. Assemblaggio (`tools/build/asm.sh`)

```mermaid
flowchart TD
    subgraph DATI["data/"]
        Y["rules.yaml, balance.yaml"]
        IT["items/items.tsv"]
        BE["monsters/bestiary.tsv"]
        TM["town_map.txt"]
        LT["lore.txt, help.txt,<br/>help_hud.json, title_src.png"]
        CH["chapters.yaml<br/>(solo atlante e simulatori)"]
    end
    subgraph GEN["generatori (tools/)"]
        GDB["gen_db.py<br/>(items_db.py, bestiary.py)"]
        GGF["gen_gfx.py"]
        GFO["gen_font.py"]
        GMU["gen_music.py<br/>(songs.py)"]
        GMA["gen_maps.py"]
        GFI["gen_final.py"]
        GTI["gen_title.py"]
        GST["gen_start.py"]
        GLO["gen_lore.py (cache)"]
        GHE["gen_help.py (cache)"]
    end
    Y --> GDB
    IT --> GDB
    BE --> GDB
    TM --> GMA
    LT --> GLO
    LT --> GHE
    LT --> GTI
    GDB --> DB["out/work/db.asm"]
    GGF --> GC["out/work/gfx_consts.inc,<br/>out/work/gfx/*.bin, gfx0/1/2.prg"]
    GFO --> UF["out/work/gfx/uifont.bin"]
    GMU --> MT["out/work/music_tab.inc,<br/>out/work/snd/sndN.prg"]
    GMA --> TP["out/work/town.map,<br/>out/work/town_places.inc"]
    GFI --> FM["out/work/final_map.inc,<br/>out/work/fmap.prg"]
    GTI --> TI["out/work/title.prg"]
    GST --> SD["out/work/start_data.inc"]
    GLO --> LD["out/work/ldat.prg, out/work/lore.inc"]
    GHE --> HI["out/work/help.inc"]
    DB --> GAME
    UF --> GAME
    UF --> GST
    UF --> GHE
    GC --> GAME
    MT --> GAME
    TP --> GAME
    FM --> GAME
    GAME["64tass src/game.asm<br/>-> out/work/game.prg, game.lbl, game.lst"]
    GAME --> ARENA["build arena: ARENA=1<br/>out/work/arena_game.prg + src/test/arena.asm"]
    GAME -->|game.lbl| LOB["src/lobby.asm -> out/work/lobby.prg"]
    GAME -->|game.lbl| MEN["src/menu.asm -> out/work/menu.bin<br/>(immagine piatta, 3 zone)"]
    MEN --> PM["pack_menu.py: ZX0 per zona,<br/>verifica sul posto -> out/work/menu.prg"]
    GAME --> PK["pack.py: ZX0 di GAME<br/>-> out/work/game.zx0, out/work/pack.inc"]
    PK --> STA["src/start.asm (+ pack.inc, start_data.inc)<br/>-> out/work/start.prg"]
    SD --> STA
    LD --> LOR["src/lore.asm -> out/work/lore.prg"]
    HI --> HEL["src/help.asm -> out/work/help.prg"]
    HEL --> HZ["pack.py: ZX0 di HELP -> out/work/help.zx0<br/>src/help/zx0sfx.asm -> out/work/helpz.prg (file HELP sul disco)"]
    BAR["src/barbarian.asm -> out/work/barbarian.prg"]
    JUK["src/jukebox.asm -> out/work/jukebox.prg"]
    GC --> G0["out/work/gfx0.prg = gfx0 + town.map"]
    TP --> G0
```

- **Ordine obbligato**: GAME per primo (le sue etichette `out/work/game.lbl` servono a LOBBY e MENU, che lo chiamano);
  `pack.py` dopo GAME (START deve sapere dove caricare il flusso compresso: `out/work/pack.inc`); START dopo (conosce anche la
  dimensione di GAME + LOBBY + GFX0 per dosare la barra, `OTHERS`).
- **Controlli in assemblaggio**: margine del codice (`.cerror`, avviso sotto 1 KB sotto `$8720`), zone del MENU, cache
  del tema, pagina zero, generatore sotto l'I/O. La build stampa i margini:
  `margine codice: N B (di cui M prima del plugin di Krill)` e `menu: zona 1 ... libera N B`.
- **Passi lenti in cache** (`tools/build/cache_run.py`): girano solo se cambiano i loro ingressi (storia `gen_lore`, manuale
  `gen_help`, atlante `gen_atlas`); impronta SHA-1 di ingressi e uscite.
- **Compressione** (`tools/build/pack.py`, zx0 di `lab64-tools`): modo rapido nelle build normali, ottimo con `ZX0_BEST=1`
  (`tools/build/release.sh`); cache in `out/cache/zx0/`; decompressore di riferimento `tools/build/zx0dec.py`.

## 3. Il disco (`tools/build/mkdisk.sh`)

```mermaid
flowchart LR
    SV["salvataggi vuoti: hl (versione attuale),<br/>save-01..05 (SV_LEN da out/work/game.lbl)"] --> W
    W["cc1541 di Krill (-M 8): barbarian (primo), start, game (ZX0), lobby,<br/>menu1..3, gfx0, fmap, gfx1..n, snd0..n, title, lore, ldat,<br/>help, jukebox, hl, ksave, save-01..05"] --> DR["out/work/disk.d64 (release)"]
```

**Un solo disco** (11/11 sera, regola del committente): per lo sviluppo `POKE 1020,1` prima del `RUN` salta il menu del
loader. Comporre il disco costa ~0,1 s. Dall'11/11 il disco lo scrive il `cc1541` di Krill's Loader
(hash dei nomi a 8 caratteri, collisioni rifiutate); i salvataggi sono file preallocati ([FastLoader](FastLoader.md)).

### Krill's Loader (`tools/build/krill_build.sh`, dall'11/11)

`tools/build/asm.sh` lo chiama per primo: scompatta `src/third-party/krill/loader-v194.zip` in `out/work/krill/pkg` (usa e getta),
costruisce install, residente e plugin di save con `ca65`/`ld65` e `src/common/krill/loaderconfig.inc` (indirizzi:
`INSTALL` `$0840`, `RESIDENT` `$0200`, `TRANSIENT` `$7D00`, pagina zero `$41`), compila `cc1541` e scrive
`out/work/krill.inc` (`tools/build/krill_syms.py`) per 64tass. ~1,3 s.

## 4. Strumenti di supporto

| Strumento | Uso |
|---|---|
| `../lab64/memmap/c64map.py` (14/11, generico) | `out/work/memory-map/index.html` + `memmap.json` a ogni build: mappa **automatica**, senza configurazione, dai listati di 64tass (`-L`), dalle etichette (`-l`) e dal disco. Moduli = listati il cui file e' sul disco (stesso contenuto o stesso nome: `game` compresso, `menu` diviso in `menu1..3`); per ogni byte: indirizzo nel file, indirizzo di esecuzione (`.logical`) e file sorgente; variabili di `.virtual`; indirizzi usati dalle istruzioni (pagina zero, I/O, KERNAL). Mostra: panoramica per pagine, strati per modulo, spazio libero per banco, moduli nella stessa memoria (overlay), disco completo. **Analisi statica**: non vede dati copiati o decompressi all'avvio, buffer dietro puntatori, dati che diventano liberi (es. `gfx_data` dopo `copy_gfx`). Verifica: il libero `$9E7B-$9FFF` = 389 B coincide con il margine del blocco `$9C00` di `asm.sh`. **Sonda in VICE** (14/11, `./build.sh --probe`, `../lab64/memmap/probe.py`): con `C64_MEMPROBE=1` ogni sessione VICE dei test (`tests/lib/c64.py`) riempie la RAM (`$033C-$03FB`, `$0400-$07FF`, `$0803-$FFFF`, anche sotto ROM e I/O) con uno schema noto subito dopo il boot e la salva alla fine in `out/work/memprobe/` (scenario = modulo dei test, impronta del disco); `c64map.py` usa solo i dump fatti con lo stesso disco e aggiunge la sezione "Measured in VICE" (byte mai scritti per banco e per pagina, confronto con l'analisi statica, scenari) e la misura `ram_never_written`. Misurato [14/11]: smoke + sanity con la sonda 28,6 s contro 29,8 s senza (una misura per parte: costo trascurabile); mai scritti 1862 B in 3 sessioni, fra cui `$9E7D-$9FFF` (387 B: il libero statico del blocco `$9C00` meno 2 byte). Limiti: vede solo cio' che i test eseguono; le scorciatoie del monitor contano come scritture; un byte scritto con lo stesso valore dello schema sembra intatto (schema senza `$00`/`$FF`/`$20`). `memmap.json` porta anche `metrics` (`ram_free_static`, `ram_never_written`), che `publish.py` mette nel manifest quando pubblica le mappe. Aggiunte: TODO T1 |
| `tools/memory-map/gen_rammap.py`, `tools/memory-map/gen_diskmap.py` | `out/work/memory-map/mappa_ram.html`, `out/work/memory-map/mappa_disco.html` a ogni build: mappe **curate a mano** con scenari e verifiche in VICE (se cambia la memoria o il disco vanno aggiornate); restano finche' la mappa automatica non le sostituisce (TODO T1) |
| `tools/atlas/gen_atlas.py` (+ `atlas_names.py`, `atlas_template.html`) | atlante grafico `out/work/atlas/` ([regole in CLAUDE.md](../CLAUDE.md)) |
| `tools/build/asm_audit.py` | analisi del codice assemblato (`out/work/asm_audit/analisi_assembly.md`, test `ASM-10`) |
| `tools/manual/gen_manual.py` | manuale per la release |
| `tools/vice/arena.py` + `src/test/arena.asm` | combattimenti veri in VICE per controllare i simulatori |
| `tools/vice/*` | screenshot (`shots_menus.sh`, `shots_manual.sh`), profilo per fotogramma (`frame_prof.py`), cronometro del MENU (`menu_time.py`) |
| `tools/simulators/*.py` | simulatori di combattimento, progressione, economia ([Bilanciamento](balancing-guide.md)) |
| `tests/run.py` | i test: `smoke`, `sanity`, `regression` ([Test](test.md)) |

## 4b. Programmi esterni compilati dentro le immagini (13/11; 14/11 ultime versioni dai sorgenti)
(14/11, regola del committente) i programmi esterni sono **all'ultima versione** e si compilano **dai sorgenti** dentro la build
delle immagini di Lab64 (`../lab64/docker/Dockerfile`, stage `vice-build`, `tass64-build`, `cc65-build`, `cc1541-build`,
`zx0-build`, tutti da `tools-builder` = base + compilatori e librerie di sviluppo). Versioni, URL e SHA-256 stanno **solo** in
`../lab64/sources.conf`; `../lab64/build-images.sh` scarica i sorgenti sull'host (curl o git) in `../lab64/downloads/`, li
controlla e li cancella a immagini fatte. Nelle immagini finali entrano **solo i binari e le licenze** (`/opt/c64/licenses/`).
I compilatori non ci sono. La cache di BuildKit tiene gli stage
compilati: si ricompila solo se cambia un sorgente o la base (`docker builder prune` svuota la cache: poi VICE si ricompila, ~5 min
misurati il 13/11 insieme alle tre immagini). `./build.sh` costruisce le immagini mancanti da solo (`../lab64/build-images.sh`).

| Programma | Versione (14/11) | Sorgente | Dove finisce | Licenza |
|---|---|---|---|---|
| VICE (gtk3) | 3.10 | tarball ufficiale (SourceForge) | `lab64-tools`: `/opt/vice/bin/x64sc`, `/opt/vice/bin/c1541`, dati in `/opt/vice/share/vice` (gli altri emulatori di VICE non entrano) | GPL-2.0 |
| 64tass | 1.60.3243 (prima 1.59 di Ubuntu) | zip dei sorgenti (SourceForge) | `lab64-tools`: `/opt/c64/bin/64tass` | GPL-2.0 |
| cc65 (cc65, ca65, ld65) | master dell'08/11/2026 (ultimo tag V2.19 del 2020; prima 2.19 di Ubuntu) | GitHub, commit fisso | `lab64-tools`: `/opt/c64/bin`, librerie in `/opt/c64/share/cc65` | zlib |
| cc1541 | 4.2 (prima 4.0, dallo zip di Krill) | tarball originale conservato da Debian (il repository Bitbucket rispondeva 404 il 14/11) | `lab64-tools`: `/opt/c64/bin/cc1541` | MIT |
| zx0 | ultimo commit (17/12/2021, formato v2: uguale ai sorgenti di prima) | GitHub, commit fisso | `lab64-tools`: `/opt/c64/bin/zx0` | BSD-3 |

- Effetto misurato il 14/11 del passaggio a 64tass 1.60 e cc1541 4.2: **tutti i `.prg` identici** byte per byte; il **disco cambia**
  (cc1541 4.2 scrive la stessa lista di file in modo diverso) e passa smoke, sanity e regression (Krill su 1541, 1541-II, 1570/1571,
  salvataggi, `EMU-*` su vc64web).
- Per aggiornare un programma: versione, URL o commit e SHA-256 in `../lab64/sources.conf`, poi `../lab64/build-images.sh --force tools`.
- **Prova da ambiente pulito** (14/11): immagini, cache di BuildKit, rete e volume cancellati; clone dei due repository affiancati;
  `./validate_env.sh`, `./build.sh --release` (immagini ricostruite da zero, tutto ricompilato: ~8 min; 185 PASS + 1 SKIP, `EMU-*`
  compresi), `../lab64/build-images.sh --force` (riscarica i sorgenti, la cache resta valida), progetto di esempio di `lab64 init`
  (build e test passati). Unico intoppo esterno: Docker Hub ha risposto 429 (troppe richieste) all'immagine `node`, riuscito dopo
  qualche minuto.
- VICE e' installato con `--prefix=/opt/vice` e sta in `/opt/vice` anche nell'immagine finale: trova i suoi dati (keymap, risorse)
  dove li cerca. Prima (fino al passo A del 13/11) era compilato nel progetto in `../lab64/vice/bin` con i dati copiati accanto
  all'eseguibile per renderlo spostabile.
- **Stessa base** (stage `base`, ubuntu:24.04) per gli stage di compilazione e per le immagini che eseguono i binari: i binari
  compilati su una base più recente non partono su una più vecchia (una VICE compilata su 26.04 vuole glibc 2.42, la 24.04 ha la
  2.39) [MISURATO]. Con un solo Dockerfile la cosa non puo' piu' sfuggire.
- **VICE headless provato e scartato** [MISURATO 13/11]: la 3.10 con `--enable-headlessui` va in segfault all'avvio (`log_archdep` con
  un puntatore nullo mentre scrive "ROM image not found" per i drive 2000/3000/4000), anche con `-logfile`/`-console`: niente
  screenshot. Resta gtk3 con Xvfb. Non provato: fornire anche le ROM di quei drive.
- **gtk3, non sdl2** [MISURATO 13/11]: con sdl2 gli stessi test erano 3,2-3,6 volte più lenti (causa non indagata).
- Gli hash dei tarball non sono verificati contro valori ufficiali (lo script stampa lo sha256 scaricato).

## 5. I test nella build

```mermaid
flowchart LR
    RT["tests/run_tests.sh<br/>(container lab64-tools)"] --> RU["tests/run.py smoke sanity<br/>(--release / --all: + regression)"]
    RU --> LIB["tests/lib/c64.py: VICE (x64sc) con il monitor remoto"]
    LIB --> FAST["Game.to_menu(): GAME, LOBBY, villaggio scritti in RAM;<br/>menu_return(): modulo MENU scritto in RAM (out/work/menu_zK.prg)"]
    RU --> REP["out/work/test_report.txt / .json"]
    RU --> FIN["ricostruzione finale del disco<br/>(le varianti di test non restano)"]
```

## 6. Container, programmi esterni, Windows e WSL (13/11)
Nel progetto stanno **tutti i file** (sorgenti, dati, ROM in `../lab64/roms/`, sorgenti di VICE, zx0 e cc1541). I
**programmi** stanno nei container (`../lab64/docker/Dockerfile`, `tools/manual/Dockerfile`, tabella in
[Getting started](getting-started.md) sezione 3); sull'host servono solo
sh, Docker con BuildKit, git e curl (`./validate_env.sh` li controlla).

| Programma | Container | A cosa serve |
|---|---|---|
| `64tass` 1.60, `cc65` (master 08/11/2026), `cc1541` 4.2, `zx0` (dai sorgenti); `make`, `perl`, `unzip`, `zip`, `git` | `lab64-tools` | assemblaggio, Krill's Loader, release, versione dei branch |
| `python3` 3.12 + Pillow, PyYAML, NumPy, Matplotlib | `lab64-tools` | generatori, atlante, mappe, simulatori |
| VICE (`x64sc`, `c1541`) e le sue librerie (gtk3), `xvfb-run`, `pkill`, `ffmpeg` | `lab64-tools` (= builder + questi) | test, screenshot, arena, MP3 dei brani |
| node 22, Playwright 1.63 + Chromium, ffmpeg | `lab64-vc64web` | demone di vc64web (test `EMU-*`, video) |
| WeasyPrint 70 (+ PyYAML, Pillow, pango, font DejaVu) | `lab64-pdf-gen` (14/11, di Lab64: 276 MB) | PDF del manuale |
| Xvnc di KasmVNC 1.5.2, PulseAudio, node (server del viewer) | `lab64-viewer` | vista dal vivo nel browser, con l'audio |
| gcc e librerie di sviluppo | stage `tools-builder` (non e' un'immagine) | compilare VICE, zx0, cc1541 |

Dimensioni misurate il 13/11 (`docker image inspect`, layer comuni contati in ogni immagine), con i nomi di oggi: lab64-tools
1553 MB (il builder e VICE: dal 14/11 un'immagine sola; il builder da solo era 868 MB), lab64-vc64web 2116 MB, lab64-viewer 803 MB;
lab64-pdf-gen 276 MB (14/11; il vecchio barbarian-manual era 937 MB, 1620 MB quando partiva da lab64-tools). Lo stage `base` (ubuntu + CA + `/work`) e' in comune fra
lab64-tools e lab64-viewer [MISURATO 13/11: stessi id dei layer]. **Costo di Docker** [MISURATO 13/11, Linux su Linux]: smoke in container 15,1 s di media contro 15,6 s sull'host (3
prove): nessuna perdita misurabile. **Non misurato** su Docker Desktop / WSL2.

**Windows**: si lavora **dentro WSL2** con il progetto nel filesystem di WSL (`~/...`), non in `/mnt/c` (accessi lenti, permessi e fine
riga). `./validate_env.sh` lo riconosce dal tipo di filesystem del punto di montaggio che contiene il progetto (`/proc/self/mountinfo`:
`9p`/`drvfs`/`virtiofs` = disco Windows o condiviso, `ext4` & simili = filesystem Linux) e dai segni di WSL (`microsoft` nel kernel,
`WSL_DISTRO_NAME`). **Non provato su Windows** (solo la logica, con un `mountinfo` di prova). Fine riga: `.gitattributes` forza LF.
Windows nativo (senza WSL) non è supportato: gli script sono shell Unix.

Per giocare si usa un VICE con interfaccia installato sull'host (o un C64 vero): è indipendente dal progetto.
