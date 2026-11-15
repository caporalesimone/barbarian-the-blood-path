# Ottimizzazione del codice — analisi dell'11/11

Copyright © 2026 - Simone Caporale

Analisi generale del codice (v1.175): codice morto, procedure duplicate, generalizzazioni possibili, prestazioni,
organizzazione. Le voci **semplici** (nessun cambiamento di comportamento, verificabili dai test) sono già state fatte;
le altre sono **da valutare** dal committente. Le stime in byte non marcate "misurato" sono calcolate dal listato
(`out/work/game.lst`) o dal sorgente, non provate.

## Metodo

- **Codice morto**: script sul sorgente (`src/**/*.asm|inc`): ogni etichetta globale definita e mai citata altrove
  (anche come `<etichetta`, `etichetta+N`), poi controllo a mano di ognuna sul listato (routine, tabelle, variabili) e
  nei test/strumenti (`tests/`, `tools/`), perché alcune servono solo a loro (`lv`, `mod_*`, `gfx_end`, `T_LEVER`).
- **Duplicati**: finestre di 7 istruzioni normalizzate (salti senza destinazione) ripetute in punti diversi del
  sorgente, raggruppate e controllate a mano: 47 gruppi, i più utili sotto.
- **Prestazioni**: i test PERF-10..18 ([prestazioni](prestazioni.md)).
- Margine di GAME (`.cerror` della build): **1434 B** prima, **1765 B** dopo le voci fatte (misurato).

## Fatto (11/11, senza revisione: comportamento invariato, test verdi)

| Voce | Dove | Risparmio |
|---|---|---|
| `mulhi` (A × X / 256) mai chiamata, con le sue 4 variabili `mh_*` | `game/game.asm` | 53 B di GAME + 4 B di RAM |
| `pk_get` (posto dello zaino → `it_*`) mai chiamata | `game/ui.asm` | 25 B |
| `sp_text` (testo in sprite) mai chiamata: la barra ne ha una sua; con `spt_*` | `game/ui.asm` | 131 B + 3 B di RAM |
| `ui_tabs` (fila di linguette) mai chiamata: nessuna schermata ha linguette (`tb_n` = 0 ovunque); con `tb_lo/hi/x/y` | `game/ui.asm` | 92 B + 4 B di RAM |
| `bit_r` (tabella dei bit) mai letta | `game/game.asm` | 8 B |
| `chest_open` cercava il baule sotto il PG con un ciclo uguale a `chest_here` (barra): ora la chiama | `game/game.asm` | ~14 B |
| `h_div` mai chiamata | `ovl2.asm` (OVL2) | 4 B di OVL2 |
| `pr_y` mai usata | `barbarian.asm` (loader) | 1 B |
| 32 variabili mai usate (`la_l/h`, `ha_ed`, `bh_*`, `lk`, `hp_x/y`, `hv_n`, `xn`, `xpv`, `xrem`, `xdig`, `xfill`, `acc_l/h`, `thr_l/h`, `bar_bt`, `bar_r`, `mm_orig/pcol/prow`, `ui_have`, `ui_mode`, `sh_mc`) | variabili `.virtual` | ~40 B di RAM delle variabili (spazio libero nelle zone `$91xx`–`$98xx`) |
| `ui_exit` azzera `joynew`/`keynew` (correzione di un bug, generalizza il `jmp` di inventario e minimappa) | `game/ui.asm` | +11 B |

Totale GAME: **+331 B** di margine (1434 → 1765 B, misurato), sopra la soglia di 1 KB richiesta da 5.1.

## Da valutare: codice e generalizzazioni

In ordine di resa stimata. "Rischio" = cosa può rompersi; tutte le aree hanno test (indicati).

| # | Proposta | Dove | Stima | Rischio / test |
|---|---|---|---|---|
| O1 ✓ | **Linguette di `ui_nav`**: con `tb_n` sempre 0, i rami delle linguette (`ui_tsel`, `ui_tab`, giro lista ↔ linguette) non servono più. Togliere il supporto o tenerlo per le quest (schermate a schede)? | `game/ui.asm` `ui_nav` (righe ~640–730) | 60–90 B | tutti i menu passano da `ui_nav`: smoke + `UI-*`, `PG-NEW-*` |
| O2 ✓ | **Oro totale** (`c_gold` + 10 × `c_sgold`) calcolato uguale in 3 punti: una routine `gold_total` in GAME (LOBBY la può chiamare: è assemblato con le etichette del gioco) | `lobby.asm:409`, `ui.asm` `shop_gold`, `stash_io.asm` | LOBBY −19 B (ha ~150 B liberi), GAME +4 B | `GOLD-*`, `SHOP-*`, scheda del barbaro |
| O3 ✓ | **Nome di file a 4 caratteri** (`cmdbuf+3`, `nlen` = 4, `io_dir` = 1) ripetuto 4 volte: una routine `set_name4` | `disk.asm` ×3, `stash.asm` | ~25 B | `SAVE-*`, `VIL-OVL2-*`, cambio piano |
| O4 ✓ | **Riempimento di pagine** (`sta (ptr0),y` / `iny` / `inc ptr0+1` / `dex`) 3 volte | `gen_io.asm` (sotto l'I/O), `dungeon.asm`, `game.asm` | ~10–20 B | `GEN-10` (il generatore deve restare uguale) |
| O5 ✓ | **Cura della pozione** (`itval + itdn × livello`) calcolata in `drink` e nella scheda dell'oggetto: una routine | `combat.asm:847`, `ui.asm:1653` | ~12 B | `POTION-1x` |
| O6 ✓ | **Colore RAM** riempita in 2 punti uguali (`COLRAM`, 4 pagine) | `game.asm:491`, `ui.asm:160` | ~12 B | screenshot dei menu |
| O7 ✓ | **Indirizzo della casella** (`maprow_lo/hi` + `tx`) uguale in `get_tile` e `set_tile` | `game.asm:552`, `:567` | ~8 B | tutto il gioco |
| O8 ✓ | **Cursore `>`** disegnato uguale in 3 schermate (inventario, leva, menu) | `ui.asm:1968`, `:3634`, `menu.asm:167` | ~15 B | smoke, `THRONE-10` |
| O9 ✓ | **Chiave + numero** nel riquadro purse disegnati uguali 2 volte | `ui.asm:1193`, `:1898` | ~10 B | screenshot |
| O10 ✓ | **Seed in testo** (cifre/lettere) scritto uguale 2 volte (scheda, minimappa) | `ui.asm:3365`, `:3782` | ~15 B | `MAP-*` |
| O11 ✓ | **Negazione a 16 bit** di `tmp0/1` 2 volte (c'è già `sabs`): routine `neg16` | `game.asm:297`, `ui.asm:2578`, `bar.asm:450/473` | ~10 B | combattimento, barra |
| O12 ✓ | **Ritorno alla posizione salvata** (`c_retx`/`c_rety` → `px`/`py`) 2 volte | `levels.asm:280`, `:892` | ~15 B | `PORTAL-*`, `DEATH-*` |
| O13 ✓ | Inizializzazione VIC/colori uguale in loader, help e lore (programmi diversi: nessun byte di GAME, solo un'`.include` comune) | `barbarian.asm`, `help.asm`, `lore/scroll.asm` | 0 B di RAM, meno sorgente | `BOOT-*`, `LORE-10`, `HELP-10` |
| O14 ✓ | Costanti mai usate (nessun byte): `KLOAD`, `KSAVE`, `LOC_NONE`, `UC_UNIQUE`, `HUDSPR`, `master_seed`, `FREE_RAM_START` tolte; `RES_*` dell'arena tenute (le legge `tools/vice/arena.py`, documentano il formato) | vari | 0 B | nessuno |

Totale stimato O1–O12: **~200–260 B** di GAME (non misurato), più 19 B di LOBBY.

## Da valutare: prestazioni (misure dei test PERF, 11/11) — riportate nel TODO come suggerite (capitolo B)

| # | Osservazione | Idea | Stima |
|---|---|---|---|
| P1 | **Primo ingresso nel piano 1 dal villaggio ~12 s** in VICE (poi 5,6–7,3 s fra i piani) | il precaricamento del tema parte dopo N caselle: forse non finisce prima della cripta; misurare cosa si legge (tema, brano, piano) con il cronometro; vedi TODO 8 (prefetch nuovo) | da misurare |
| P2 ✓ | **Minimappa del villaggio 0,64 s** a disegnarsi (inventario 0,10 s) — **fatto il 15/11 (TODO D2): 0,64 s → 0,26 s misurati da PERF-11** (stesso VICE, stesso eroe; soglia del test 1 s → 0,5 s) | prima ogni cella 24×24 chiamava 4 volte `mm_tile` (`get_tile` + catena di confronti, ~280 cicli a quadrante). Ora: tabella `mm_cls` di 48 byte (classe del tile: pavimento/strada, scale giù, scale su, acqua, strada) costruita **una volta** all'ingresso (`mm_build`; villaggio: gli stessi confronti con le costanti `T_*` di prima, eseguiti 48 volte invece di 2304; dungeon: `solidtab`), due puntatori di riga (`MAP + 2·mmy·48`, `+48`) e i bit «esplorato» con uno scorrimento (`mm_ex`, 12 byte copiati per riga di celle; villaggio: `$FF`). Semantica dei quadranti (maschere 1/2/4/8, l'ultima scala vince, cella blu se solo acqua) invariata: verificato byte per byte (schermo, color RAM, registri VIC, sprite) su villaggio e piani 1 e 4 con la nebbia mezza esplorata | **−0,38 s**; GAME **−41 B** di codice (margine 1573 → 1614 B), 60 B di lavoro nella coda dello slot sprite 27 (`$A6C0`, byte senza uso; annotati `@map`) |
| P3 | **Frenzy: 27% di fotogrammi persi** fra i mostri | TODO D3: camera a casella in Frenzy, AI distribuita su più fotogrammi | vedi [prestazioni](prestazioni.md) |
| P4 | **"save game" 5,4 s** (eroe + piano) | salvare il piano solo se è cambiato; CRC di 1.8 lo allungherà | 1–2 s (stima) |
| P5 | Piano 15: 3,8% di fotogrammi persi camminando (piano 1: 2%); dal PERF-21 (11/11) il più pesante è il **piano 14: 14,5%** | più mostri svegli: stesso lavoro di P3 | — |
| P6 | (PERF-19, 11/11) **Prima apertura della locanda ~9,2 s** (OVLT + OVL2 dal disco; le successive 0,14 s) | caricare OVLT nel precaricamento del villaggio (come OVL2 dopo N caselle) o una barra/"please wait" (regola della barra: solo con avanzamento vero) | 7–8 s in meno alla prima visita (stima) |

## Da valutare: organizzazione del progetto

| # | Proposta | Note |
|---|---|---|
| G1 ✓ | I **file generati** stanno ancora in `src/` (`out/work/db.asm`, `out/work/gfx_consts.inc`, `out/work/final_map.inc`, `out/work/town_places.inc`, `out/work/music_tab.inc`, `out/work/version.inc`, `out/work/start_data.inc`, `out/work/sid_freq.inc`): spostarli in `out/` (l'assemblaggio ha già `-I out`) e toglierli da git, come la grafica dell'11/11 | servono i generatori aggiornati e `.gitignore`; i diff di git non mostrerebbero più le tabelle generate (oggi utili per vedere cosa cambia) |
| G2 ✓ | Gli **script storici dei test** (`tests/regression/*/test_*.py`) hanno ciascuno una propria classe `Vice` e messaggi in italiano: portarli su `tests/lib/c64.py` / `play.py` | TODO 1.11 |
| G3 ✓ | `tools/vice/arena.py` ha un suo client del monitor: usare `tests/lib/c64.py` | come G2 |
| G4 | Fatto l'11/11: `lab/music` fuori dal repository e dalla storia (filter-repo), regola in CLAUDE.md | — |
