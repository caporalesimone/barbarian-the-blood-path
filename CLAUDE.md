# CLAUDE.md — regole generali del progetto "Barbarian: The Blood Path" (C64, 6502, 64tass)

Regole valide per **tutto il progetto**. Le regole di dettaglio stanno vicino a cio' che regolano (13/11, regola del committente):
- **[docs/getting-started.md](docs/getting-started.md)**: da leggere **la prima volta** in ogni sessione nuova, per capire come
  funzionano build e test (cartelle, container, flussi, comandi). Si aggiorna nello stesso lavoro se cambia la build o i test.
- **[src/CLAUDE.md](src/CLAUDE.md)**: regole di **sviluppo** del gioco (sorgenti, memoria, loader, salvataggi, UI, grafica e atlante,
  musica, dati e bilanciamento, simulatori). Valgono anche per `tools/` e `data/` quando si cambia il gioco.
- **[tests/CLAUDE.md](tests/CLAUDE.md)**: regole dei **test** (suite, ID, eroe di prova, emulatore secondario).

## Chi e come
- Progetto di Simone Caporale (ingegnere). Risposte in **italiano**, precise e tecniche, dirette.
  Segnalare SEMPRE quando un'informazione non è certa al 100%.
- I file per Simone si consegnano come file (SendUserFile), non come artifact pubblicati.
- Tutto il testo **nel gioco** è in inglese; i nomi di oggetti, mostri e abilità non si traducono mai.
- (14/11, regola del committente) **La toolchain, Lab64, è tutta in inglese**: codice, commenti, script, pagine generate,
  README, messaggi e **commit** (ha il suo `CLAUDE.md`). Il resto del progetto (wiki, TODO, commit del gioco) resta in italiano.
- Copyright: "COPYRIGHT 2026 - SIMONE CAPORALE" nel gioco, "Copyright © 2026 - Simone Caporale" nei documenti.

## Ambiente: tutto nei container (13/11, regola del committente)
- Build e test girano **solo nei container Docker**. La **toolchain** (13/11, regola del committente) e' generica per il C64 e non
  sa nulla del gioco. **Dal 14/11 e' un repository a parte, Lab64** (scelta del committente: niente submodule, storia non conservata).
  (15/11, regola del committente) **Il gioco usa Lab64 solo come ci si aspetta da un progetto**: il comando **`lab64`** nel PATH
  (`lab64 install`), mai un percorso verso Lab64 (niente `../lab64`); nei container il comando `lab64` e la libreria Python di Lab64
  (`vicemon`, `c64test`, `c64manual`, `psid`) ci sono gia'. Immagini **`lab64-<nome>`**: `lab64-tools`
  (build **e** test e strumenti in VICE: builder e VICE uniti il 14/11), `lab64-vc64web` emulatore secondario, `lab64-viewer` vista
  dal vivo con l'audio (KasmVNC). Le immagini proprie del gioco si chiamano **`barbarian-<nome>`** e stanno accanto al loro codice
  (oggi nessuna: dal 14/11 il manuale si fa con `lab64-pdf-gen` di Lab64). La configurazione di Lab64 per il gioco
  sta in `lab64.env`. Sull'host servono solo sh, Docker (con Compose v2), git, curl. Python gira **solo nei container**. Comandi (dalla cartella del
  gioco): `./build.sh [...]` (o `lab64 build`), `lab64 test [--view|--no-view] [--emu] [...]`, `lab64 up|down|ps|view` (stack compose: con `lab64 up` i comandi girano
  nel container `lab64-tools` sempre acceso), `lab64 run <comando>`, `lab64 manual`, `lab64 map`,
  `lab64 check-env`. Immagini con la versione di Lab64 nel tag (`lab64-tools:1.2`); il gioco la fissa con `LAB64_VERSION` in
  `lab64.env`. Motore dei test, libreria VICE e generatore del manuale stanno in Lab64; `tools/vice/vice_env.sh` del gioco aggiunge
  solo `ROOT` a quello di Lab64.
- Un cambiamento a Lab64 si committa **nel suo repository** (in inglese, con le sue regole) e deve lasciare verde la build del gioco.
- I container devono restare **minimi**: ognuno ha solo cio' che serve al suo compito; niente strumenti usati una volta sola
  (compilatori dei tool: solo negli stage `*-build` del Dockerfile, che non diventano immagini). Immagini con la **versione** nel tag
  (es. `ubuntu:24.04`), mai il digest. Le immagini di Lab64 vengono da **un solo Dockerfile multi-stage**
  (`docker/Dockerfile` di Lab64): lo stage `base` (senza nome di immagine, non si avvia) e' il genitore comune e contiene la
  **versione di Ubuntu in un solo punto** (`ARG UBUNTU`). vc64web ha il suo Dockerfile (pacchetto autonomo, base node).
- (14/11, regola del committente) I programmi esterni sono **all'ultima versione** e si compilano **dai sorgenti** dove si puo'
  (VICE, 64tass, cc65, cc1541, zx0: stage `*-build` del Dockerfile di Lab64; la cache di BuildKit evita di ricompilarli); nelle
  immagini entrano **solo i binari e le licenze**, i sorgenti si buttano. Versioni, URL e SHA-256 **solo** in `sources.conf` di Lab64;
  `lab64 images` scarica i sorgenti sull'host in `downloads/` di Lab64 e li cancella a immagini fatte.
- **Script**: shell POSIX/bash quando lo script lancia solo comandi; Python quando c'e' logica vera. Mai un Python che fa solo da
  involucro a comandi shell. Librerie Python esterne ammesse solo se sono nel container.
- **Percorsi**: **nessun percorso assoluto** nel progetto, **solo relativi**, e **tutti i file che servono stanno nel progetto**.
  Gli script shell ricavano la radice dalla posizione del file, i Python da `__file__`; Lab64 solo con il comando `lab64` (sull'host
  e nei container) e con la sua libreria Python (importabile nei container). ROM solo quelle di Lab64 (`vicemon.ROMS_C64`,
  `vicemon.ROMS`). Gli unici percorsi assoluti ammessi sono `/work` (il progetto) e, solo se inevitabile, `$LAB64` nei container. Dopo ogni modifica a uno script: provarlo
  lanciandolo da un'altra cartella.
- **Uscite** (14/11, regola del committente): tutto cio' che si genera sta in `out/` (non in git, tranne `out/.gitkeep`), in **quattro cartelle**:
  `out/work/` = intermedi e uscite della build in corso (`.prg`, `.lst`, `.lbl`, `.inc`, log, `gfx/`, `snd/`, `krill/`, `atlas/`,
  `memory-map/`, `manual/`, `simulators/`, `disk.d64`, report dei test...; ogni strumento nella sua sottocartella; riscrivibili, si possono
  cancellare); `out/cache/` = cio' che si riusa fra le build e non si cancella (`zx0/`, `steps/`, `vc64web/`); `out/tmp/` = usa e getta
  (si puo' cancellare sempre; **mai** `/tmp`); `out/releases/` = **artefatti per versione**: ogni build pubblica in
  `out/releases/v<versione>/` (disco; atlante, mappe, report dei test e manuale solo se generati in quella build; **niente zip dei
  sorgenti**) con `manifest.json` (`tools/build/publish.py`: scelte del gioco sopra `c64publish` di Lab64); `out/releases/latest` punta all'ultima; si tengono le ultime **5** versioni
  (`./build.sh --keep N`, `KEEP_VERSIONS`). Nel codice i percorsi sono `out/work/...`: **mai** scrivere in `out/` direttamente.
  La pubblicazione fuori dal computer (GitHub) verra' dopo.
- Fine riga sempre LF (`.gitattributes`); il progetto su Windows sta nel filesystem di WSL2, non su `/mnt/c` (`lab64 check-env`).

## Cartelle
`src/` (gioco e librerie per il C64, `src/third-party/`), `data/`, `tools/` (`build/`, `atlas/`, `memory-map/`, `manual/`,
`simulators/`, `vice/`, `font/`), `tests/` (`smoke/`, `sanity/`, `regression/`), `docs/` (solo documentazione **scritta**: cio'
che si puo' rigenerare va in `out/`, i suoi generatori in `tools/`), `lab64.env` (configurazione di Lab64), `lab/` (studio, non usato dalla build: [lab/README.md](lab/README.md)),
`out/`. Fuori dal repository: Lab64 (dove si vuole, usato solo con il comando `lab64`: immagini Docker, programmi esterni,
ROM, emulatore secondario, mappa automatica, manuale; README di Lab64). Tabella completa: [docs/getting-started.md](docs/getting-started.md) sezione 2. Uno script di verifica che controlla qualcosa
diventa un test in `tests/`, non resta in `tools/`.

## Documentazione: SEMPRE allineata al codice
- `docs/` è la **wiki del gioco** (indice: `docs/README.md`). Ogni modifica a una dinamica del gioco
  (generazione, combattimento, oggetti, mostri, bottino, salvataggi, disco, memoria, UI, strumenti) va riportata
  nella pagina corrispondente **nello stesso lavoro**, non dopo. Se una pagina non esiste, si crea e si
  aggiunge all'indice. Diagrammi e flussi in Mermaid (controllati con `mmdc`).
- La wiki descrive il gioco **com'è nel codice**; ciò che è solo progettato sta nelle pagine di progetto
  (`SISTEMA_COMBATTIMENTO.md`, `BILANCIAMENTO.md`) o in una sezione "Progetto / da fare" marcata come tale.
- **Architettura** (11/11, richiesta del committente): `docs/architettura.md` (struttura), `docs/flussi.md` (come gira il
  codice), `docs/build.md` (pipeline) e `docs/getting-started.md` (build e test, container) si aggiornano nello stesso lavoro quando
  cambia un modulo, un flusso, la memoria, un'interruzione, la build o i test.
- Documenti generati (in `out/work/`, pubblicati in `out/releases/`): mappe della RAM e del disco (`tools/memory-map/`), atlante grafico (`tools/atlas/`,
  regole in `src/CLAUDE.md`), manuale (`tools/manual/`, sorgente in `docs/manual/`), report dei simulatori. Se cambia cio' che
  descrivono, si aggiornano i generatori.
- `docs/FORMATO_DATI.md`: formato esatto dei file su disco e dei salvataggi; aggiornarlo con `SAVE_VER`.
- **Screenshot dei menu** (08/11, regola del committente): si conservano **in git** in `docs/screens/` (uno per schermata +
  mosaico `tutti_i_menu.png`; 13/11: restano versionati). Si rifanno solo quelli cambiati:
  `lab64 run tools/vice/shots_menus.sh inventario locanda ...` (senza nomi: tutti), il mosaico si rigenera da solo.
- **Manuale**: PDF con WeasyPrint nel container `lab64-pdf-gen` (`./build.sh --manual` o `lab64 manual`, `tools/manual/gen_manual.py`):
  (15/11) tema base "c64" di Lab64 (pagina, colori, tasti, numeri di pagina) + `docs/manual/tema.css` (solo le regole del gioco);
  la build fa **tutti i manuali che hanno il sorgente** (oggi italiano; inglese quando ci sara' `manual_src_en.html`), una pagina
  che trabocca e' un avviso, in `--release` un errore.
  **Copertina** sempre con il **tema rosso** dei dungeon (palette 4): screenshot `dungeon` in `tools/vice/shots_manual.sh` (piano 8
  con il seed di prova). **Screenshot del manuale**: il PG sta sempre in una posizione valida (casella percorribile); per il
  villaggio lo controlla `tools/vice/check_pos.py`, nei dungeon guardare lo screenshot prima di consegnare.
- **Help** (`HELP`, [docs/help.md](docs/help.md)): testo in `data/help.txt`, ritaglio dell'HUD in `data/help_hud.json`.
  Se cambia un tasto o una schermata, aggiornare `data/help.txt` nello stesso lavoro; se cambia la grafica o la
  disposizione dell'HUD, `lab64 run python3 tools/build/gen_help.py --snap` (il test della release lo controlla).
- `TODO.md`: **solo lavori aperti**, divisi in **capitoli** con ID `<lettera><numero>` (A1, B2, ...; A = priorità massima): ogni voce
  con obiettivo, motivazione, complessità, cosa serve, cavilli. Le decisioni nuove si scrivono nella voce a cui appartengono, con la
  data; una voce finita si **cancella** e la decisione va nella pagina della wiki interessata. Le decisioni e i lavori
  fatti fino all'08/11 sono in `docs/storico-todo.md` (archivio, non si aggiorna).
- File usa e getta (istruzioni per un altro modello, piani temporanei): si cancellano a lavoro finito.

## Git
- (10/11, regola del committente) Repository git, branch `main`. **Un commit per ogni attività conclusa**, di norma **prima di
  iniziare un argomento nuovo** (niente commit infiniti). "Conclusa" = build verde, **smoke + sanity passati** (`./build.sh`), wiki e
  TODO aggiornati nello stesso lavoro. Messaggio in italiano: titolo breve + corpo con cosa e perché, più le righe di attribuzione
  della sessione (`Co-Authored-By` compreso). Autore dei commit: **Simone Caporale `<caporalesimone@gmail.com>`** (configurazione
  locale del repository; storia ricreata in un solo commit il 13/11 su richiesta del committente).
- Fuori da git: `out/` (tranne `.gitkeep`), cache, log. Le ROM Commodore **sono nel git di Lab64** (13/11,
  richiesta del committente, per esportare il progetto; le toglierà lui prima di pubblicare, TODO di Lab64).
- (14/11) **Quando il committente chiede di scaricare il repository, consegnare anche Lab64** (il gioco non si costruisce senza).
- Prima di consegnare `git status` pulito; non si riscrive la storia senza che il committente lo chieda.
- **MP3 fuori dal repository** (11/11, regola del committente): `lab/music/` (~13 MB) **non è in git e non c'è mai stato**.
  **Quando il committente chiede di scaricare il repository, includere anche `lab/music/`** (zip a parte o insieme al bundle git).

## Build, versioni, release
- `./build.sh` = **tutto** (disco, mappe, atlante, smoke e sanity, manuale); parametri per saltare gli artefatti: tabella nel [README](README.md).
  **Regola del committente (14/11): salvo diversa richiesta, quando costruisco io uso `./build.sh --fast`** (solo il disco + smoke e sanity,
  build veloce), e le build accessorie (atlante, mappe, manuale, release) le faccio solo se richieste o se cambia cio' che descrivono.
  `./build.sh --release` (anche regression, `EMU-*`, manuale): **solo quando la chiede il committente**. Dettagli: [docs/getting-started.md](docs/getting-started.md), [docs/build.md](docs/build.md).
- **Un solo disco** (11/11 sera, regola del committente): `out/work/disk.d64` (disco di lavoro) -> `out/releases/vX.Y/blood_path_vX.Y_1541.d64`. Per lo sviluppo:
  `LOAD"*",8`, `POKE 1020,1` (subito `START`; `POKE 1021,1` = god mode), `RUN` ([docs/cheats.md](docs/cheats.md)).
- **Versione**: cresce da sola (numero minore di `version.yaml`) a **ogni build con cambiamenti** ai sorgenti
  (`tools/build/bump_version.py`; impronta in `version.yaml`, `source_hash`). **Ogni file consegnato porta la versione nel nome**
  (`blood_path_vX.Y_1541.d64`; lo stesso per manuale e altri file quando ha senso).
- **Versione 2.0** (09/11, regola del committente): il gioco passa a **2.0 appena il quest system è pronto (TODO H1) e mai prima**:
  fino ad allora 1.x (il numero minore è un intero e cresce senza limite: 1.999 → 1.1000).
- **Versione dei branch** (11/11, regola del committente): build su un branch diverso da `main` = versione `tag.N`
  (`tools/build/verinfo.py`, `branch_versions` in fondo a `version.yaml`), così non bruciano i numeri di `main`.
- Il formato dei salvataggi ha una versione (`save_version` in `version.yaml`, `SAVE_VER`): cambiarla a ogni modifica del formato
  del personaggio o del piano salvato.
- **VICE** (`x64sc` 3.10, compilato nell'immagine `lab64-tools`) è l'**unico riferimento autorevole** (cicli, tempi,
  drive, debug). Il gioco deve andare anche sull'emulatore secondario vc64web ([docs/emulatore.md](docs/emulatore.md),
  regole in `tests/CLAUDE.md`).
