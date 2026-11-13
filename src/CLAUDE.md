# src/CLAUDE.md — regole di sviluppo del gioco

Regole per chi cambia il gioco: sorgenti in `src/`, e i generatori e i dati che lo producono (`tools/`, `data/`). Le regole generali
del progetto sono nel `CLAUDE.md` della radice; come si costruisce e si prova: `docs/getting-started.md`; regole dei test:
`tests/CLAUDE.md`. Ogni modifica a una dinamica del gioco va riportata nella wiki (`docs/`) **nello stesso lavoro**.

## Sorgenti (`src/`, 07/11)
- In `src/` solo: **sorgenti del gioco**, **librerie esterne del gioco** (`src/third-party/`, es. Krill's Loader, con licenza e
  `.gitignore`), **solo codice per la CPU del C64**. Emulatori e programmi dell'host stanno in `toolchain/` (13/11, regola del
  committente).
- Sorgenti principali, **uno per file del disco**: `barbarian.asm` (BARBARIAN, il loader), `start.asm` (START), `game.asm` (GAME),
  `lobby.asm` (LOBBY), `menu.asm` (MENU: menu del villaggio, parti in `menu/`, compresso da `tools/build/pack_menu.py`), `lore.asm`
  (LORE), `help.asm` (HELP), `jukebox.asm` (JUKEBOX). Le parti incluse stanno in sottocartelle: `common/` (condivise: trampoline,
  avvio con titolo `boot.asm`, player SID, ZX0, macro, versione, effetti), `game/` (moduli del gioco), `lore/`, `help/`, `menu/`,
  `test/` (`arena.asm`, solo per `tools/vice/arena.py`).
- Assemblaggio con `-I src -I src/common -I src/game -I out` (`tools/build/asm.sh`): le `.include` usano il nome semplice. I sorgenti
  generati (tabelle, grafica, versione) stanno in `out/`.
- Un file nuovo sul disco = un sorgente nuovo in `src/`; il resto nella sottocartella della sua componente.
- **Margine di memoria**: controllato dalla build (`.cerror` e avviso sotto 1 KB). Mai chiudere un lavoro con il margine negativo.

## Memoria, loader, salvataggi
- **Generatore dei piani**: gira nella RAM sotto l'I/O (`src/game/gen_io.asm`, `gen_call` con `$01=$34` e interrupt spenti):
  lì niente accessi a VIC/SID/CIA/colori/KERNAL/disco. Ogni cambiamento della generazione cambia i piani salvati:
  `tests/regression/gen/test_gen.py` (mappe di riferimento) deve passare; se il cambiamento è voluto, `--update` e `c_gver`.
- **Krill's Loader** (11/11, [docs/FastLoader.md](../docs/FastLoader.md)): dopo `START` il drive non risponde più al KERNAL;
  `$0200-$0312` è del residente (niente buffer o segnali lì: `LDFLAGS`/`CHRPRE` a `$8E`/`$8F`, `YN_SAV` a `$0340`),
  `$41-$47` della sua pagina zero (`$41-$57` durante un salvataggio); `$DD00` si scrive solo con il banco VIC (6 bit alti
  a 0, niente lettura-modifica); i salvataggi sono file preallocati riscritti interi dal plugin (`save-0N`, `hl`). Il loader si
  costruisce a ogni build dallo zip (`src/third-party/krill`, `tools/build/krill_build.sh`, configurazione `src/common/krill/`).
- **Salvataggi** (11/11 sera, regola del committente, [docs/salvataggi.md](../docs/salvataggi.md)): il disco si scrive **solo**
  con "save game", alla creazione dell'eroe e al cambio di capitolo; "quit game" non salva; scale, locanda, scheda del
  personaggio e portale lavorano in RAM (slot dei piani del capitolo, `LVRAM`). **5 piani per capitolo** (`CH_LV`,
  `data/chapters.yaml`): un capitolo più lungo richiede di rivedere gli slot in RAM. Formato: `docs/FORMATO_DATI.md`, `SAVE_VER`.

## Interfaccia e regole di gioco del committente
- **Movimento** (09/11): ci si muove **solo con WASD o con il joystick** (porta 2), in ogni schermata, menu, gioco, loader e help.
  Nessun altro tasto (tasti cursore compresi). Dove W/A/S/D servono come lettere (nome e seed del nuovo barbaro) mentre si scrive
  non ci si muove: si conferma con ENTER. Unica eccezione tollerata: `JUKEBOX` usa ancora anche i tasti cursore.
- **Niente barre di caricamento** (11/11 sera): ogni attesa di disco (caricamenti, salvataggi, "deleting ...") ha solo il titolo e
  "please wait" (`io_screen`, `ui_pwait`); `START` mostra "the crypt door creaks open" e "please wait" (`txt_init`).
- **Locanda** (09/11): la "casa del PG" si chiama **locanda** (inglese *inn*: titolo "inn", "inn chest") in gioco, help, manuale e
  wiki; **ogni villaggio ha una locanda** e in ognuna c'è **lo stesso baule**. Titolo "inn" con il boccale. Identificatori e
  commenti del codice (`T_DHOME`, `home`, `stash`, `ov_stash`, `ls_home`) restano com'erano.
- **Menu del villaggio** (11/11): locanda e negozi stanno nel modulo **MENU** (`src/menu.asm`, tre zone di RAM, caricato a ogni
  ingresso nel villaggio). **Per ogni villaggio nuovo**: la mappa non deve usare `$C900-$CFFF` (zona 1 del MENU), il tile `DHOME`
  della locanda c'è; poi `toolchain/run.sh emu-vice python3 tests/run.py regression -k VIL-MENU`. Lo spazio libero delle zone lo stampa
  la build (`menu: zona 1 ... libera N B`): ogni modifica a locanda e negozi deve starci (`.cerror`).
- **Help**: se cambia un tasto o una schermata, `data/help.txt` nello stesso lavoro (vedi `CLAUDE.md` della radice).
- **Musica** ([docs/musica.md](../docs/musica.md)): i brani sono dati in `tools/build/songs.py` (elenchi del gioco in `PLAYLIST`),
  compilati da `tools/build/gen_music.py` in file `SNDn` sul disco; un solo player (`src/common/sid_player.inc`) per loader, gioco
  e jukebox. Brani ed effetti si provano con `JUKEBOX` (da rifare più bello, TODO E8). MP3 di ascolto: `gen_music.py --render`
  nel container `c64-emu-vice` (VICE + ffmpeg) in `out/music/`.

## Atlante grafico (`out/atlas/`): a ogni modifica grafica
- L'atlante (`index.html`, un PNG per tile, `tiles.json` con gli id `SET`+lettera) si rigenera a ogni build
  (`tools/atlas/gen_atlas.py`, modello `tools/atlas/atlas_template.html`) dai file che legge il C64. **Ogni modifica grafica** (tile,
  palette, mappa del villaggio, gruppi, titolo, font della UI, glifi dell'HUD e della minimappa) deve risultare corretta lì,
  nello stesso lavoro: dopo la build aprire la pagina (o farne uno screenshot) e controllarla.
- **Ogni tile e ogni glifo ha il suo nome e la sua descrizione** (10/11) in `tools/atlas/atlas_names.py`: `TILE` (villaggio, dungeon,
  sala del trono), `UI` (icone e cornici del font della UI, con la costante `CH_*`/`BOX_*`), `HUD` e `MINI` (glifi dell'HUD e della
  minimappa, con il tasto della codifica `hud` o la costante `G_*`). Lettere, cifre e punteggiatura del font della UI hanno nome e
  tasto automatici. Se manca una voce, `gen_atlas.py` si ferma (la build non passa).
- Se si aggiunge o si sposta un tile: `LEGEND` (`tools/build/gen_maps.py`) o `DUN_LEGEND` (`tools/build/gen_gfx.py`), la voce in
  `tools/atlas/atlas_names.py`, i gruppi in `data/atlas_groups.json` e, per un tile nuovo dei dungeon, `data/atlas_dungeon.txt`.
- Se si aggiunge un glifo al font della UI (`tools/build/gen_font.py` `ICON` + costante in `src/game/ui.asm`) o all'HUD
  (`HUD_A`/`HUD_B`/`HUD_WARN` in `tools/build/gen_gfx.py`): la voce in `tools/atlas/atlas_names.py`.
- In cima all'atlante la sezione **Spazio libero** (10/11): se cambia cosa conta come "usato" (`DUN_USED`, `TRONO_USED`, codici
  riservati) va aggiornato `gen_atlas.py`.
- `post_walls` (src/game/gen_io.asm) è duplicata in Python in `tools/atlas/gen_atlas.py`: se cambia una, cambiare l'altra.

## Dati e bilanciamento
- Regole del combattimento: `data/rules.yaml`; mondo, bottino, negozi: `data/balance.yaml`. Il gioco usa i dati
  generati da `tools/build/gen_db.py` (`out/db.asm`).
- `tools/simulators/` contiene TUTTI gli script di simulazione delle partite (`sim_rules.py` combattimenti e progressione,
  `fit_rules.py` taratura, `cmp_rules.py` confronti, `rules.py` modello condiviso, `sim_durability.py`, `sim_gold.py`,
  `sim_chest.py`; report in `out/simulators/`). **Ogni cambio di regola nel codice o negli yaml va riportato nello stesso
  lavoro nei simulatori**: il simulatore deve riprodurre il gioco com'è (differenze note: `docs/BILANCIAMENTO.md`,
  sezione "Differenze tra simulatore e codice").
- Come si bilancia (strumenti, obiettivi, procedura, numero di prove): `docs/balancing-guide.md`. Seguirla.
- L'arena (`tools/vice/arena.py` + `src/test/arena.asm`) fa girare il codice vero in VICE: serve a verificare che il simulatore
  non menta.
