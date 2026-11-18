# Barbarian: The Blood Path — dati su disco

Tutti i file stanno sul disco del gioco (`blood_path_vX.Y_1541.d64`, periferica 8). I file del giocatore
(personaggi e piani) sono scritti dal gioco; i file "media" sono creati dalla build (`tools/build/mkdisk.sh`).


## 1. Elenco dei file

| Nome sul disco | Tipo | Contenuto | Chi lo scrive |
|---|---|---|---|
| `BARBARIAN` | PRG | il **loader**, primo file (`LOAD"BARBARIAN",8` + `RUN`, `src/barbarian.asm`): release = menu con tre voci; debug = nessun menu, carica subito `START` ([Avvio e storia](intro.md)) | build |
| `START` | PRG | avvio del gioco (`src/start.asm`), avviato dal loader: schermata di attesa e musica; **installa Krill's Loader** (codice d'installazione a `$0840` nel file, [FastLoader.md](FastLoader.md)) e carica con Krill `GAME`, `LOBBY` e l'elenco eroi (`hl`) | build |
| `LORE` | PRG | la storia: `START` con `LORE=1` (titolo + `LDAT`, PRESS SPACE) e lo scorrimento (`src/lore/scroll.asm`) | build |
| `HELP` | PRG | il manuale (`src/help.asm`), a `$0801`; pagine in RLE (schermo e colori), font della UI e glifi dell'HUD; **compresso ZX0** con il decompressore in testa (`src/help/zx0sfx.asm`, 12/11); [Help](help.md) | `tools/build/gen_help.py`, `tools/build/asm.sh` |
| `LDAT` | PRG | dati della storia compressi ZX0 (charset, sprite, forme delle immagini, righe RLE con eventi), decompressi sul posto a `$2000`; formato in [Avvio e storia](intro.md#formato-di-ldat) | `tools/build/gen_lore.py` |
| `GAME` | PRG | il gioco **compresso ZX0** (06/11): indirizzo di caricamento = quello del flusso compresso (`GAME_ZX_AT`, ~`$44B3`), decompresso sul posto dal loader in `$0400` (`GAME_ENTRY`, nessuno stub BASIC). Vedi «Compressione» | build (`tools/build/pack.py`) |
| `LOBBY` | PRG | modulo del menu iniziale (codice, caricato a `$C000`) | build |
| `MENU` | PRG | (11/11; 18/11 un file solo, prima `MENU1`…`MENU5`) menu del villaggio e NPC (`src/menu.asm`): intestazione + le cinque zone di RAM compresse ZX0; si legge all'ingresso nel villaggio. Vedi «MENU» | build (`tools/build/pack_menu.py`) |
| `TITLE` | PRG | schermata del titolo: bitmap multicolor + schermo + colore, 10000 byte | build |
| `TWN1` … `TWN5` | PRG | (12/11; 15/11) villaggio del capitolo *c* (`c_chap`): tile + intestazione + mappa RLE; ognuno con tile, colori e mappa suoi (`tools/build/villages.py`); `TWN5` = città dell'Abisso (prototipo) | build |
| `BOSSCH1` … `BOSSCH3` | PRG | (12/11) mappa del piano del boss dei capitoli 1–3 (piani 5, 10, 15): 4 byte (scale x, y; boss x, y) + RLE come `FMAP`, caricata a `FIN_AT`; segnaposto (`data/maps/bosschapN.txt`, `tools/build/gen_bossmap.py`) | build |
| `FMAP` | PRG | mappa di base della sala del trono (piano 20), RLE come la mappa del villaggio (`b < $C0` tile, `$C0 + n` ripete il byte seguente `n + 2` volte), 48 × 48 caselle; caselle della stella e del cerchio = `$80 \| tile` (marcatori risolti da `post_walls`). Indirizzo di carico = `FIN_AT` = `$FD00` (`fin_load` la legge nella cache sotto il KERNAL, in fondo: da `PF_END` ai vettori `$FFFA`, 762 B; dal 10/11) | `tools/build/gen_final.py` |
| `GFX1` … `GFX8` | PRG | (12/11) grafica per capitolo: tile + sprite dei mostri; per il capitolo *c*: `GFX(2c−1)` = piani del dungeon, `GFX(2c)` = piano del boss (sala del trono). Oggi i file dei capitoli 2–4 sono copie del capitolo 1 (segnaposto) | build |
| `SND0` … `SNDn` | PRG | un brano per file (villaggio, livelli, boss finale, combattimento: ordine e nomi nel commento di `out/work/music_tab.inc`); indirizzo di caricamento 0 (ignorato: il gioco li legge nel buffer del luogo o del combattimento). Formato in [Musica](musica.md) | build (`tools/build/gen_music.py`) |
| `JUKEBOX` | PRG | prova di brani ed effetti (`src/jukebox.asm`) | build |
| `HL` | PRG, 1 blocco | elenco eroi: versione, 5 byte "eroe presente", 5 nomi (66 B) | creato dalla build (versione attuale, nessun eroe), scritto dal gioco |
| `SAVE-01` … `SAVE-05` | PRG, 9 blocchi | un file per eroe: blocco dell'eroe + 20 stati dei piani (2070 B) | creati vuoti dalla build, scritti dal gioco |
| `KSAVE` | PRG | plugin di save di Krill's Loader (`out/work/krill/save.prg`, a `$7D00`): il gioco lo ricarica prima di ogni salvataggio | build (`tools/build/krill_build.sh`) |

Nomi in PETSCII maiuscolo. I file PRG hanno i 2 byte iniziali dell'indirizzo di caricamento. Il disco lo scrive il
`cc1541` (4.2, `tools/build/mkdisk.sh`, opzioni `-M 8` e `-S 4` = interleave 4): Krill cerca i file per **hash del nome** (8 caratteri), e
`cc1541` rifiuta i nomi che collidono. `BARBARIAN` è il primo file (`LOAD"*",8`).

**Salvataggi (dall'11/11, ramo `fast-loader`).** Il plugin di save di Krill **riscrive solo file già presenti e con
lo stesso numero di blocchi** (altrimenti errore `$F9`): la build crea `HL` e `SAVE-01..05` con la lunghezza giusta e
la directory non cambia mai. Ogni scrittura riscrive il file intero (il gioco legge il file, cambia la parte e lo
riscrive: [salvataggi.md](salvataggi.md)).

**`SAVE-0N`** (eroe `N-1`, `SV_LEN` = 2070 byte):

| Offset | Byte | Contenuto |
|---|---|---|
| 0 | 210 (`HERO_LEN`) | blocco dell'eroe (`CHRBLK`, vedi sotto), con il baule della locanda |
| 210 + (piano − 1) × 93 | 93 (`LV_SLOT`) | stato compatto del piano 1…20 (82 o 93 byte usati) |

**`HL`** (66 byte): versione (`save_version`), 5 byte "eroe presente", 5 nomi da 12 caratteri (scritto solo creando
un eroe o cancellandolo; `START` e il menu leggono solo questo file).

Fino all'11/11 (prima di Krill) i salvataggi stavano in un solo file REL `SAVES` da 106 record (`tools/mkrel.py`):
formato e tempi in `docs/wiki/storico-todo.md` e nella storia di git.

## 2. Personaggio — `SAVE-0N`, offset 0 (`HERO_LEN` byte)

In memoria: blocco `CHRBLK` a `$9500` (`src/game/game.asm`); i primi `HERO_LEN` byte del file sono la copia esatta del blocco.
Dal formato $BF: esperienza `c_xp` a 24 bit, vita `c_hp` a 16 bit, `c_vis` 3 byte (24 piani); il 4o posto
dell'equipaggiamento (`c_eq+3`, `c_eqb+3`) è l'anello (bonus = caratteristica: 1 FOR, 2 DES, 3 COS).
Dal formato $C0: il baule della locanda non è più nel blocco (record a parte); ogni oggetto dello zaino e
dell'equipaggiamento ha durabilità attuale e massima (`c_packd`/`c_eqd`, `c_packm`/`c_eqm`, contigui come
`c_pack`/`c_eq`); `c_game` (3 byte: bit 0..8 numero della partita, bit 9..23 minuti giocati); `c_deaths`
(16 bit).
Dal formato **$C5** (10/11): `c_sgold` conta le **decine** di monete (stessi byte, cambia il significato: 65 535 = 655 350
monete); oro totale = `c_gold + 10 × c_sgold`.
Dal formato **$C6** (11/11, branch `feature/stat-points`): dopo `c_sgold` **`c_sadd`** (3 byte: punti statistica spesi in FOR,
DES, COS) e **`c_resp`** (gettoni respec, 0..255), prima del baule della locanda. Blocco da 206 a 210 byte.
Dal formato **$C7** (12/11, branch `capitoli`): dopo `c_resp` **`c_chap`** (capitolo in cui si gioca, 1..4) e **`c_unl`**
(capitolo più alto sbloccato): blocco da 212 byte, file `SAVE-0N` da 2072 byte (sempre 9 blocchi). Il generatore passa alla
versione `GVER` 5 (i piani 5, 10, 15 sono mappe fisse). (18/11) `GVER` 6: grotte nel capitolo 3; un eroe salvato con la 5 tiene il seed (6 cifre) e rigenera i piani
(`c_vis` azzerato, `migrate_char`); solo dalle versioni prima della 5 si ricava ancora il seed da quello a 16 bit.
Dal formato **$C8** (17/11, concept delle quest): in fondo al blocco, dopo il baule della locanda, **`c_qst`**: blocco da 213
byte. (18/11) `c_qst` è una **maschera** delle quest prese (bit *n*-1 = quest *n*, al massimo 8); i valori di prima (0 nessuna,
1 = quest 1) restano validi, quindi il formato non cambia. File delle quest (`data/quests.yaml`, `tools/build/gen_quests.py`):
- `QST0` (caricato a `$BC00`, schermo B, ed eseguito): codice della pagina (`src/qpage.asm`) + **indice**: per ogni quest 1..`Q_N`
  il capitolo (1 byte) e il titolo (codici dello schermo, 0 finale). Al massimo 1024 B.
- `QST1` … `QST8` (caricati a `$B000` dalla pagina): premio (0 finale), numero di righe dello stato (1 byte), righe dello stato e
  poi del testo (36 colonne, ciascuna con lo 0 finale), `$FF`. Al massimo 1024 B.
Dal formato **$C2** (07/11 sera): zaino da **8** posti (`PACK_N`; `c_pack`, `c_packb`, `c_packd`, `c_packm` da 8 byte,
l'equipaggiamento segue all'indice 8..11) e in fondo `c_sgold` (16 bit) = oro nel baule della locanda. Blocco da 140 a 110 byte.
Dal formato **$C3** (08/11 sera): in fondo al blocco il **baule della locanda** (`st_id`, `st_b`, `st_du`, `st_m`, 24 byte
ciascuno: id, bonus, durabilità, massimo), prima in un record a parte. Blocco da 110 a 206 byte:
fino all'11/11 uscendo dalla locanda dopo una modifica si salvava l'eroe; dall'11/11 sera il baule va sul disco solo con l'eroe (save game, cambio di capitolo). Le variabili `mfar`
passano a `$95E0` e `tp_*`/`sel_*`/`sp_*` a `$93B0` per fare posto.
La tabella campo per campo (offset, byte, significato) è generata a ogni build da `src/game/game.asm` (annotazione `@map ... layout`
su `CHRBLK`, commenti dei campi) nella mappa automatica: [`program-game.html`](../../out/work/memory-map/program-game.html#layout-CHRBLK),
"Fields of CHRBLK"; lo stesso per `LVLBLK` (stato del piano in RAM). È sempre allineata al codice.

## 3. Stato di un piano — `SAVE-0N`, offset 210 + (piano − 1) × 93 (formato compatto)

In memoria: blocco `LVLBLK` a `$9800`. La **mappa non è salvata**, e nemmeno mostri e bauli
del piano: entrando nel piano si rigenera tutto dal seed (`seed_level`), poi si applicano le differenze
salvate (formato del 06/11, `save_version` $C0; $C1 dal 07/11: stessi campi, ma gli id degli oggetti sono
scesi di 1 perché i pugni non esistono più):

| Byte | Contenuto |
|---|---|
| 1 | numero del piano (controllo: se non coincide lo stato è ignorato) |
| 2 | numero della partita (9 bit di `c_game`): se è un'altra partita, i mostri tornano tutti vivi e i bauli del piano chiusi, il baule del boss si scarta; resta la nebbia |
| 1 | numero di mostri al salvataggio (informativo) |
| 4 | 1 bit per mostro: vivo (bit 7 del primo byte = mostro 0) |
| 1 | bauli del piano tolti: bit *i* = 1 se il baule del piano nel posto *i* (0..3) è stato aperto |
| 1 o 12 | baule del boss: `0` = nessuno; `1` + X, Y, `ch_t` + 4 × `ch_i` + 4 × `ch_b` se c'è e non è aperto. Il baule non ancora aperto ha il bit 3 di `ch_t` (tesoro di un mostro): `ch_i[0]` = numero di oggetti, `ch_b[0]` = chestLevel; oro e oggetti si generano alla prima apertura |
| 72 | nebbia a settori 2×2 caselle: 24 righe × 3 byte, 1 bit per settore (esplorato se lo è almeno una casella) |

Totale 82 o 93 byte (11/11: con i 2 byte della partita; prima scritto "81 o 92", sbagliato di 1): sta nel suo posto
da `LV_SLOT` = 93 byte. Regole:
- **posizioni dei mostri non salvate**: tornando nel piano (scale o caricamento) i vivi ripartono dalla
  casella di partenza del seed, con la vita piena. Con il portale o alla morte invece lo stato resta in
  memoria (STASH, sotto) con le posizioni esatte;
- i **bauli aperti spariscono** cambiando piano, anche se non vuoti (bit 5 di `ch_t`);
- i **tesori lasciati dai mostri non si salvano**: spariscono cambiando piano (con le scale, salvando o
  uscendo); il baule del boss invece resta finché non è aperto;
- la nebbia in memoria resta a caselle (`EXPL`, 288 byte): solo quella salvata è a settori.

Bauli: al massimo 4 generati con il piano (`CH_GEN_MAX`, posti 0..3, bit 4 di `ch_t`: prima quello d'oro,
poi stanza per stanza) + il baule del boss, 15 in tutto (`CH_MAX`) con i tesori dei mostri. Un mostro
comune lascia un tesoro solo se bauli presenti + in coda < 15, tenendo un posto per il boss finché è vivo;
altrimenti solo il tiro dell'oro.

Non salvati (ricalcolati al caricamento): vita, armatura, danno e posizione dei mostri
(`init_monsters_rt`, generatore deterministico del piano).

## 4. Media — `GFXn`

Prodotti da `tools/build/gen_gfx.py` (cartella `gfx/`). Vengono caricati nella **cache nella RAM sotto il
KERNAL** e da lì copiati dove il VIC li vede (`gfx_install`).

### `TWNc` (ex `GFX0`) — villaggio (caricato a `$E000`)

| Offset | Byte | Contenuto | Destinazione |
|---|---|---|---|
| 0 | 4 × 360 | caratteri dei 45 tile (43 dal 09/11 al 10/11; il 10/11 tolti barile e fieno, aggiunti finestra, comignolo, steccato verticale e guglia), una striscia per quarto del tile (alto-sx, alto-dx, basso-sx, basso-dx) | charset `$A800`, `$AA00`, `$AC00`, `$AE00` |
| 1440 | 111 (`TK_LEN`) | (15/11) **intestazione del villaggio**: portale x, y · ingresso del sotterraneo x, y · ingresso del villaggio x, y · colori (sfondo, multicolor 1, multicolor 2, color RAM = 8 + accento) · porte di fabbro, alchimista, locanda (x, y ciascuna) · uscita del capitolo (x delle 2 caselle, poi y) · nome del luogo di cura (25 byte, codici schermo, con lo 0 finale) · (17/11) **16 settori degli NPC vaganti**, 4 byte l'uno: x, y, larghezza, altezza in caselle (larghezza 0 = voce non usata) · (17/11) casella di chi da' la quest, nella piazza della fontana (x, y) | `town_k` (`src/game/levels.asm`); i colori anche nella voce 0 di `pal_bg`/`pal_c1`/`pal_c2`/`pal_ram` |
| 1551 | 48 (`TK_SOLID`) | (15/11) tile solidi del villaggio (1 byte per posto: 1 = solido) | `solidtab` |
| 1599 | fino a 1795 | mappa 48 × 48 in RLE (byte < `$C0` = tile; ≥ `$C0` = ripeti il byte dopo (b & `$3F`) + 2 volte). Intestazione + mappa ≤ 1888 B (`TOWN_MAX`: il file arriva al massimo a `$ED00`; dal 15/11 il tema del dungeon comincia prima, a `$EC6D`: villaggio e dungeon non sono mai in RAM insieme) | `MAP` |

Scritto da `tools/build/gen_gfx.py` (tile), `tools/build/gen_maps.py` (intestazione e mappa, con i controlli) e
`tools/build/asm.sh` (li unisce in `out/work/twnN.prg`). Sorgenti: `tools/build/vilN_*.py`, `data/town_mapN.txt`.

### `GFX1` … `GFXn` — temi di dungeon (2016 + `GFX_INFO` byte = 2163 byte, 9 blocchi; caricati a `GFX_DUN_AT` = `$EC6D`)

Il file del piano (12/11: due per capitolo, `GFX(2c−1)` dungeon e `GFX(2c)` boss; capitolo da `lv_grp`) lo sceglie `lvl_theme` (`src/game/theme.asm`; `tools/build/gen_gfx.py`, `chapter_sets`); i file non si deduplicano (dall'11/11, ramo `fast-loader`, la grafica si rilegge a ogni ingresso: niente cache).
**Dal 15/11** ogni file porta i **mostri del suo capitolo** (`tools/build/monsters.py` `chapter_set`: capitolo 1 i mostri di sempre, capitoli 2–4 `tools/build/monsters_chap.py`): sprite, colori e nomi dei tipi 1…8 e del posto del boss (tipo 9: Lord of Ruin nei file del dungeon e in `GFX8`, il boss del capitolo in `GFX2`, `GFX4`, `GFX6`).
Il file **finisce sempre a `$F4E0`** (`GFX_DUN_END`, inizio della zona 2 del MENU) e comincia `GFX_INFO` byte prima di `$ED00`: quei byte sono la coda del buffer del villaggio (`TOWN_MAX`), libera nel dungeon perché il villaggio si rilegge a ogni ingresso.

| Offset | Byte | Contenuto | Destinazione |
|---|---|---|---|
| 0 | 4 × 216 | caratteri dei tile 0…26 (muri, pavimenti, scale, portale, baule; 10/11: un solo tile per i bauli, i posti 25–26 sono liberi); i tile del villaggio non si toccano | charset, come sopra |
| 864 | 512 | sprite dei 4 mostri base del capitolo (tipi 1…4, 2 fotogrammi ciascuno, slot 12…19) | `$A300` |
| 1376 | 640 | sprite delle 4 varianti forti (tipi 5…8) e del posto del boss (tipo 9), 10 sprite | `$8C00` |
| 2016 | 9 | (15/11) **blocco info**: colore dello sprite dei tipi 1…9 | `NM_AT` … `NM_AT+8` (`build_sprites`, `src/game/game.asm`) |
| 2025 | 9 | byte basso dell'indirizzo del nome dei tipi 1…9 (blocco tutto in una pagina: byte alto = `>NM_AT`) | `NM_AT+9` … (`bar_name`, `src/game/bar.asm`) |
| 2034 | fino a `GFX_INFO` − 18 | nomi dei tipi 1…9, codici schermo (lettere 1–26, spazio, `'`, `-`), 0 finale, al massimo 24 caratteri (larghezza della barra); poi zeri fino a `GFX_INFO` (147 B: il blocco più lungo, quello di `GFX4`) | `NM_AT` = `$9000` − `GFX_INFO` (`$8F6D`, fine degli slot sprite 58–63, dopo il motivetto `SND_FBUF`) |

`gfx_install` copia tile e sprite e poi il blocco info intero a `NM_AT`: il buffer del tema sotto il KERNAL non serve più dopo
l'installazione (un salvataggio lo sovrascrive: buffer del plugin `SV_SCR`).

File del piano: `GFX(2c−1)` per i piani 1–4 del capitolo *c*, `GFX(2c)` per il suo piano del boss (5, 10, 15, 20) (`lvl_theme`,
`src/game/theme.asm`). Nei file `GFX(2c)` gli slot dei tile 12 e 13 contengono la grafica del pentacolo (stella e cerchio) della
sala del trono e lo slot della porta della locanda la leva.

### Mappa della cache (RAM sotto il KERNAL)

| Area | Contenuto |
|---|---|
| `$E000`–`$E57F` | villaggio (`GFX0`), riletto a ogni ingresso (11/11; il primo lo carica START) |
| `$EC6D`–`$F4DF` | tema del piano attuale (`GFXn`), riletto a ogni ingresso (11/11: precaricamento e cache tolti; 15/11: comincia `GFX_INFO` byte prima di `$ED00`, nella coda del villaggio) |
| `$F4E0`–`$FCFF` | (11/11) zona 2 del modulo MENU (fino all'11/11: tema precaricato in background, ora scritto direttamente nel buffer del tema) |
| `$D000`–`$DFFF` | sotto l'I/O: all'avvio villaggio e sprite del loader, poi i salvataggi letti dal loader (fino al primo menu); in gioco `STASH` `$D000`–`$D47F` e il generatore dei piani da `$D480` (copiato dal PRG `GAME` all'avvio) |

### Precaricamento in background (tolto)
Tolto l'11/11 nel ramo `fast-loader` (con le cache `gfx_town`, `gfx_theme`, `fin_ok`): vedi [Flussi](flussi.md#8-precaricamento-del-tema-tolto).

### `TITLE` — schermata del titolo (10000 byte)

Prodotto da `tools/build/gen_title.py` da `data/title_src.png` (bitmap multicolor 160×200, sfondo nero).
Ordine dei byte, per ognuna delle 25 righe di caratteri `r`:

| Byte | Contenuto | Destinazione |
|---|---|---|
| 40 | schermo (colori 01/10 delle 40 celle) | `$CC00 + r×40` |
| 40 | colore (colore 11 delle 40 celle) | `$D800 + r×40` |
| 8 × 40 | le 8 righe di pixel, ognuna da sinistra a destra | `$E000 + r×320 + cella×8 + riga` |

### Avvio — `START` (`src/start.asm`, codice in `src/common/boot.asm`), avviato dal loader `BARBARIAN`

Tre varianti dello stesso codice (07/11; la catena dei programmi è in [Avvio e storia](intro.md)):

| Variante | Flag | Schermo durante il caricamento | Dopo |
|---|---|---|---|
| (`INTRO=0`, non più assemblata dall'11/11) | `INTRO=0` | nessuno (schermo com'era) | subito il gioco |
| `START` | `INTRO=1 TITLE=0` (`TXT`) | **schermata di attesa** (testo "the crypt door creaks open" e "please wait", banco 3: schermo `$CC00`, font a `$E000`; niente barra dall'11/11 sera), musica del titolo | subito il gioco (niente PRESS SPACE) |
| `LORE` | `INTRO=1 LORE=1` (titolo) | titolo riga per riga, musica | PRESS SPACE, la storia |

1. Lo stub BASIC copia il corpo a `$A000` (RAM sotto la ROM del BASIC) e lo esegue; con `INTRO` parte la musica
   (IRQ raster): **Demon's Eye** (`tools/build/songs.py`, `PLAYLIST["title"]`, compilato in `out/work/sid_title.inc`) con il
   player del gioco (`src/common/sid_player.inc`, variabili a `$BE00`). Durante il caricamento **nessuno sprite**: vedi sotto.
2. (`START`, dall'11/11) **install di Krill** (`krill_install`, KERNAL acceso), residente a `$0200`, poi con
   `krill_loadraw`: `GAME` (compresso) → `GAME_ZX_AT`, decompresso **sul posto** in `$0400` (`zx0_unpack`,
   `src/common/zx0.inc`, ~4 s; la musica continua), `LOBBY` → `$C000`, `HL` → `CHRTMP` + 1 (`$B800`; `CHRTMP` = 1 se
   letto). Niente barra (11/11 sera). Il villaggio non si precarica più.
   (`LORE`, sempre con il KERNAL: `LDAT` a blocchi alternati ai blocchi di 40 byte di `TITLE`.)
   `tests/regression/boot/test_start.py` controlla lo stato = 1 e la versione = `SAVE_VER` a `start_game`.
   Tempo dal `RUN` di `BARBARIAN` (con `POKE 1020,1`) alla fine dei caricamenti: 34,5 s (VICE, 1541 emulato, 11/11;
   prima, con il KERNAL: 105 s).

### `MENU` — menu del villaggio (locanda e negozi)
Dall'11/11 (TODO D13): sostituisce i file `OVLT` e `OVL2`; dalla v1.21x contiene anche i negozi. Un file per tutti i
villaggi. `src/menu.asm` è assemblato in sei zone di RAM (le parti in `src/menu/`):

| Zona | Indirizzi | Contenuto (oggi) |
|---|---|---|
| 1 | `MR1_AT` `$C900`–`$CFFF` (RAM normale; il LOBBY la copre) | tabella dei salti (`MENU_INN` = `$C900`, `MENU_SHOP` = `$C903`), `mk_off`/`mk_exit`, locanda (`menu/inn.asm`), negozi: comprare e vendere (`menu/shop_act.asm`) |
| 2 | `MR2_AT` `$F4E0`–`$FCFF` (RAM sotto il KERNAL, dopo la cache del tema) | locanda: scelta dell'equipaggiamento (`menu/inn_eq.asm`), negozi: schermata e cursore (`menu/shop.asm`) |
| 3 | `MR3_AT` `$A700`–`$A7FF` (slot sprite 28–31, liberi nel gioco) | negozi: riparazione e tetto dell'oro (`menu/shop_fix.asm`); aspetto degli NPC (`menu/npc_look.asm`, 17/11) |
| 4 | `MR4_AT` `$A300`–`$A4FF` (slot sprite 12–19: mostri del tema nel dungeon, ricopiati da `gfx_install` a ogni ingresso) | (17/11) sprite degli NPC del villaggio: 4 disegni × 2 fotogrammi (`tools/build/npc_gfx.py`), solo dati |
| 5 | `MR5_AT` `$8C00`–`$8E7F` (sprite forti e boss del tema nel dungeon, ricopiati da `gfx_install` a ogni ingresso) | (18/11) sprite del "!" (`$8C00`, puntatore `$30`), tabella dei salti `NPC_JT` (`$8C40`: `npc_init`, `npc_draw5`, `npc_talk5`), capitoli delle quest `q_ch`, piazzamento e sprite degli NPC (`menu/npc.asm`) |
| 6 | `MR6_AT` = `MRT` `$9600`–`$977F` (tabelle dei mostri del piano: nel villaggio non servono, `lb_cnt` = 0; entrando in un piano le riscrivono `init_monsters_rt` o la STASH) | (18/11, revisione R11) passo dei vaganti `npc_tick6` (`menu/npc_tick.asm`), chiamato da `npc_tick` di GAME a `MR6_AT`. Per questo `pend_save` (salvataggio nel villaggio) copia dalla STASH solo `LVLBLK`, non `MRT` |

File **`MENU`** (18/11, revisione R2: **un file solo**; dall'11/11 era un file per zona, `MENU1`…`MENU5`, e ogni file in più
costava ~0,4 s a ogni ingresso nel villaggio). Struttura (`tools/build/pack_menu.py`):

| Byte | Contenuto |
|---|---|
| 0 | numero di parti *N* (= `MPARTS`, 6) |
| 1 … 4*N* | per ogni parte, nell'ordine di decompressione: indirizzo dei dati compressi (2 B), destinazione = inizio della zona (2 B) |
| … | le parti compresse ZX0: prima le zone 1, 3, 4, 5, 6, per ultima la zona 2 |

Il file **finisce a `MR2_END`** (`$FD00`, fine della zona 2): Krill lo carica al suo indirizzo (`load_file`, C = 0), nella RAM
sotto il KERNAL fra `$E000` (`ML_LO`: dal 18/11 il villaggio si installa prima del MENU, quindi il suo file non serve più) e
`$FCFF`. Il gioco
(`ovl_town` / `ml_read`, `src/game/stash.asm`) lo legge all'**ingresso nel villaggio** se `ovl_cur` = 0 (lo azzerano
`game_start`, il caricamento del LOBBY e `enter_gfx`, perché il dungeon copre le zone 4 e 5), controlla che finisca a
`ml_end` (altrimenti lo rilegge, fino a 3 volte), poi con `$01 = $35`, interruzioni spente e NMI su `nmi_stub` scorre
l'intestazione: le zone 1, 3, 4, 5, 6 si decomprimono dall'appoggio nelle loro zone, la zona 2 per ultima **sul posto**.
`pack_menu.py` simula tutto in 64 KB (nessuna scrittura su dati non ancora letti, ogni zona uguale byte per byte, file
sopra `ML_LO`) e scrive anche `out/work/menu_zK.prg` (le zone decompresse, per i test). Oggi (18/11, R11): 4328 B (18 blocchi),
3096 B sopra `ML_LO` (prima del 18/11 l'appoggio partiva da `$ED00` e restavano 57 B). Zone: 1 1691 → 1439 B, 2 2049 → 1670 B,
3 231 → 226 B, 4 512 → 183 B, 5 602 → 503 B, 6 353 → 282 B; spazio libero: zona 1 101 B, zona 2 31 B, zona 3 25 B, zona 4 0 B,
zona 5 38 B, zona 6 31 B (la build lo stampa). Tempo della lettura con la decompressione: 3,1 s (`PERF-DISK-11`; con cinque file 3,5 s).

### Compressione (ZX0)
- Compressore: **ZX0 v2** di Einar Saukas (C, compilato dai sorgenti ufficiali in Lab64: `build-scripts/sources.conf` di Lab64, licenza BSD-3), compilato con
  gcc da `tools/build/pack.py` (chiamato da `tools/build/asm.sh`). Modo rapido (`-q`, ~1,5 s) nei build normali, modo ottimo
  (`ZX0_BEST=1`, ~20 s) in `tools/build/release.sh`. Cache in `out/cache/zx0/`.
- Formato del flusso: `tools/build/zx0dec.py` (decompressore Python di riferimento, = `dzx0.c` originale).
- **Sul posto**: il file compresso si carica in modo che il suo ultimo byte stia `delta` byte sopra l'ultimo byte
  del gioco (regola di ZX0; `delta` lo stampa il compressore, 2–3 byte) e sotto `$A000` (corpo del loader).
  `pack.py` verifica in Python la decompressione sul posto in una memoria di 64 KB e scrive `out/work/pack.inc`
  (`GAME_ZX_AT`, `GAME_ZX_DST`, `GAME_ZX_LEN`) per il loader.
- Decompressore 6502 `src/common/zx0.inc` (~240 B, 12 byte di pagina zero: nel loader `$50`–`$5B`), senza `sei`:
  ~4,0 s per i 39 KB del gioco (misurato in VICE con il cronometro dei cicli). `tests/test_loader.py` lo verifica
  **byte per byte** contro `out/work/game.prg` (fermata dopo `jsr zx0_unpack` e `save` del monitor di VICE).
- `out/work/game.prg` resta non compresso: lo usano `tools/vice/shot.sh`, l'arena e i test che caricano il gioco dal
  monitor.
- Compresso anche `MENU` (11/11, sopra; decompressore anche in GAME, `stash.asm`, `ZX_ZP` = `$50`).
- Non compressi, per scelta (06/11): `TITLE` (**decisione: per ora no**; si disegna riga per riga mentre carica), `LOBBY` e `GFX0` (li ricarica anche il gioco, che non ha RAM per un
  buffer: ~5 s), i temi `GFX1`/`GFX2` (letti in sottofondo dal precaricamento). Vedi `TODO.md`.
3. Solo `LORE`: **PRESS / SPACE** (sprite a `$DD00`, RAM sotto l'I/O, lettere dal font della UI del gioco `out/work/gfx/uifont.bin` ingrandito ×3 in larghezza e ×2,5 in altezza, `tools/gen_loader.py`; 5 sprite riusati su due
   righe con due IRQ per fotogramma; le lettere ondeggiano su una sinusoide (`ld_sin`, 64 voci, ±`SIN_A` = 7 px,
   fase +1 per fotogramma, +6 per lettera, SPACE in controfase: `sin_y`). Righe: PRESS a `ROW1_Y` = 172, SPACE a
   `ROW2_Y` = 220 (06/11 sera: più in alto e onda più ampia); l'IRQ di metà fotogramma (`IRQ_MID` = `ROW1_Y` +
   `SIN_A` + 22) cade almeno 8 righe sopra il punto più alto di SPACE (`.cerror`): con 1–2 righe di margine una
   lettera già iniziata veniva riposizionata e "tracciava una linea" (la A). Colori: tavolozza scelta con
   `-D LDCOL=0/1/2` (`tools/build/asm.sh`, variabile `LDCOL`): 0 sangue (predefinita), 1 oro antico, 2 acciaio (15/11, committente: si resta sulla 0, decisione B5 chiusa; le varianti 1 e 2 restano nel codice)
   (`ld_col0..2`, `tools/gen_loader.py`; in attesa della scelta del committente). A fine caricamento (`START`) o con SPAZIO (`LORE`, che poi passa alla storia): segnale in pagina zero `$8E` (`LDFLAGS`: `LOBBY` già a `$C000`; 11/11, la
   pagina 2 è del residente di Krill), elenco eroi `CHRTMP` → `$D000` con `$8F` (`CHRPRE`) = 1 (il menu lo legge da lì
   senza schermata di caricamento, solo al primo ingresso), `POKE 1021` → `godmode`, musica del titolo ferma (il menu
   principale suona Demon's Eye dal 15/11, avviata da `LOBBY`: [Musica](musica.md)) e salto a `$0400` (`GAME_ENTRY`).

Un solo disco (11/11 sera): con `POKE 1020,1` prima del `RUN` `BARBARIAN` salta il menu.

Sprite e caricamento KERNAL (solo `LORE`): sulle righe con sprite (più le *badline* del VIC) la CPU perde i bit
del 1541 e il caricamento si blocca (provato in VICE). Per questo gli sprite compaiono solo a caricamento finito.
Krill invece permette sprite, IRQ e badline durante i caricamenti.

## 5. Quando si legge e si scrive il disco

- **Personaggio** (`SAVE-0N`): solo con "save game" del menu RUN/STOP, una volta alla creazione dell'eroe e al
  **cambio di capitolo** (gruppi di 5 piani, 11/11 sera). "Quit game" **non** salva. Mai alla morte o alla vittoria,
  né uscendo dalla locanda o dalla scheda del personaggio.
- **Stato del piano** (`SAVE-0N`, offset 210 + (piano − 1) × 93):
  - lasciandolo per le **scale**: copiato nel suo **slot in RAM** (`LVRAM`, 5 slot del capitolo, RAM sotto l'I/O);
    sul disco va con "save game" o al cambio di capitolo, insieme all'eroe;
  - lasciandolo per **portale o morte**: copiato in memoria (`STASH`, `$D000`, RAM sotto l'I/O),
    nessun accesso al disco. Tornando in quel piano si riprende dalla memoria;
  - entrando in un **altro** piano con uno stato ancora in memoria: prima lo si copia nel suo slot;
  - menu RUN/STOP: piano attuale (o quello in memoria, se si è nel villaggio) + personaggio.
- Il bit di `c_vis` dice che il piano ha uno stato su `SAVE-0N`; finisce sul disco col personaggio, quindi un
  piano salvato dopo l'ultimo salvataggio del personaggio si rigenera da zero alla ripresa.
- Cambio piano: 1) salva/conserva lo stato del piano attuale, 2) grafica del nuovo piano (cache o
  precaricamento), 3) stato del nuovo piano (memoria, disco o nuovo).

**Struttura dei piani**
- Piani 1–19 casuali dal seed (temi 1–7 a rotazione); il **piano 20 è la sala del trono** (tema 8),
  a mappa fissa: file `FMAP` generato da `tools/build/gen_final.py` (corridoio da sud, pentacolo e boss; alla morte del
  boss si apre il muro nord: stanza con 4 bauli epici e "a suspicious lever").
- La leva (`ui_lever`): "give up" esce, "pull the lever" mette al suo posto il portale per
  The Endless Abyss (`c_lever` = 1, suono del portale). L'Abisso si svilupperà dopo i bot dell'arena.

## 6. Tempi misurati (VICE, emulazione reale del 1541)

Dall'11/11 (Krill) i tempi sono in [FastLoader.md](FastLoader.md), sezione 7. Tabella storica (KERNAL standard, 05/11):

| Operazione | Byte | Tempo |
|---|---|---|
| Caricamento tema di dungeon | 2016 | 7,1 s |
| Caricamento villaggio (solo la prima volta) | 1440 + mappa (fino a 1792) | ~4,3 s |
| Salvataggio stato del piano, vecchio file PRG (scratch + scrittura) | 830 | 8,4–8,7 s (200 B: 6,7 s) |
| Salvataggio stato del piano, REL compatto (file unico SAVES) | 40–150 | 3,0 s |
| Lettura stato del piano, REL compatto | 40–150 | 1,5 s |
| Salvataggio eroe / lettura eroe (REL) | 129 | 3,5 s / 1,7–2,1 s |
| Elenco eroi: scrittura / lettura (REL, ultimo record) | 66 | 3,3 s / 1,5 s |
| Salvataggio da RUN/STOP (piano + eroe, una sola apertura) | – | 4,6 s |
| Cambio piano per le scale, tema gia' in cache (es. piano 2 → 1) | – | 5,5 s |
| Avvio release: `TITLE` + `GAME` + `LOBBY` + `GFX0` + elenco eroi, fino a PRESS SPACE (GAME non compresso, fino al 06/11) | 53000 | 154 s |
| Avvio release con `GAME` compresso ZX0 (modo ottimo, disco di release; decompressione compresa) | 38900 | 111 s |
| Avvio release con `GAME` compresso ZX0 (modo rapido, build di sviluppo) | 40200 | 116 s |
| Avvio sviluppo: `GAME` (compresso) + `LOBBY` + `GFX0` + elenco eroi, fino al menu (prima 120 s) | 30300 | 86 s |
| Decompressione di `GAME` (39 377 B) in `$0400` | – | 4,0 s |

## Mappa della RAM
Mappa automatica (Lab64, a ogni build con le mappe): `out/work/memory-map/program-game.html`, con le zone annotate, la memoria libera per uso e gli scenari (villaggio, dungeon, menu iniziale, salvataggio): [build.md](build.md) sezione 4a.
