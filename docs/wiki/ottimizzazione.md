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

## Revisione del 18/11 (richiesta del committente: rivedere tutto il codice, commenti, ripetizioni, zone di memoria)

Un commit per blocco, smoke + sanity a ogni blocco, regression a più riprese. Comportamento invariato.

| Blocco | Cosa | Effetto |
|---|---|---|
| R1 | spioncino: `io_screen` prosegue in `ui_pwait` (era un `jmp` alla riga dopo), `mon_path` salta direttamente a `mon_put` (4 salti a un `jmp`); `ent_pl` (posizione del PG in `ent_x/ent_y`) al posto di due copie uguali in `update_player` e `bs_body` | +12 B di margine di GAME (690 → 702 B) |
| R2 | **modulo MENU in un file solo** (era un file per zona, 5 dal 17-18/11): intestazione con sorgente e destinazione di ogni parte, file che finisce alla fine della zona 2 e si appoggia nella RAM sotto il KERNAL libera nel villaggio (`ML_LO` = `$ED00` … `$FCFF`); le zone 1, 3, 4, 5 si decomprimono dall'appoggio, la zona 2 sul posto (`ml_read`, `tools/build/pack_menu.py` con la simulazione in 64 KB, `pack.py mem_unpack`). La zona 4 non ha più bisogno dei 16 B di margine in `BFP` | `menu` 3,48 → 3,10 s a ogni ingresso nel villaggio; +55 B di margine di GAME (702 → 757 B: il ciclo sulle 5 parti con le tabelle è diventato la lettura dell'intestazione) |
| R3 | chi è accanto al PG nel villaggio (`npc_here1`, `npc_offer`) da GAME alla zona 1 del MENU (`src/menu/npc_here.asm`, salto `MENU_NHERE`); in GAME resta `npc_here` con il controllo `npc_ok` | +92 B di margine di GAME (757 → 849 B); zona 1: 189 → 91 B liberi; file MENU 40 B sopra `ML_LO` |
| R4 | commenti: una riga (ingresso, uscita, cosa fa) sulle routine che non ne avevano, in GAME (`game.asm`, `game/game.asm`, `ui.asm`, `levels.asm`, `gen_io.asm`, `hud.asm`, `bar.asm`, `combat.asm`, `rel.asm`, `disk.asm`, `dungeon.asm`), nel MENU (negozi), in LOBBY, JUKEBOX, HELP, BARBARIAN, LORE e nelle parti comuni (`boot.asm`, player SID, musica del titolo, ZX0, effetti). Corretto il commento di `gen_stairs` | nessun byte cambiato |
| R5 | confronto fra programmi (codice del MENU e del LOBBY uguale a quello di GAME): `h_zeq2` della locanda era una copia di `pk_zero` di GAME, ora la chiama (il resto delle finestre uguali sono sequenze brevi senza una routine comune) | zona 2 del MENU: 19 → 31 B liberi |
| R6 | help: "autosave: levels 5-6, 10-11, 15-16" (modello a 20 piani) corretto: si salva da soli al viaggio verso il capitolo dopo e alla creazione dell'eroe | discrepanza fra help e codice |
| R7-R8 | elenco dei test e docstring aggiornati; mappa della memoria: il programma GAME comprende `menu`, `qst*`, `cheats` (11 file del disco erano senza programma) | — |
| R9 | vendita nei negozi: l'oro con `add_gold16` di GAME invece di una somma a mano | zona 1 del MENU: 91 → 101 B liberi |

### Tempi del 18/11 (fine della revisione, VICE; da ricalibrare con il committente)

Due giri: la regression completa (le misure di un test si fermano alla prima fuori limite) e un giro dei soli PERF-DISK
con i limiti moltiplicati per 10 (tutte le misure). "max" = soglia del test (90% del limite, il limite per menu, town,
stairs, save_dng, save_char).

| Misura | Giro 1 (s) | Giro 2 (s) | Limite (s) | Soglia (s) | Esito |
|---|---|---|---|---|---|
| boot | 11.56 | 11.56 | 16.0 | 14.40 | ok |
| menu | 2.91 | 2.91 | 3.1 | 3.10 | ok (3,10-3,12 in altri giri) |
| town | 0.74 | 0.74 | 1.5 | 1.50 | ok |
| theme | 0.56 | 0.56 | 1.5 | 1.35 | ok |
| song | 0.20 | 0.20 | 2.0 | 1.80 | ok |
| hdr | 0.61 | 0.61 | 1.0 | 0.90 | ok |
| load_char | 2.44 | 2.44 | 3.4 | 3.06 | ok |
| stairs | 2.51 | 2.31 | 4.0 | 4.00 | ok |
| town_in | 2.70 | 2.74 | 5.6 | 5.04 | ok (5,76 in un giro precedente) |
| save_dng | 7.16 | 7.16 | 9.4 | 9.40 | ok |
| save_char | 8.29 | 8.29 | 9.6 | 9.60 | ok |
| hdr_write | 5.80 | 5.80 | 6.8 | 6.12 | ok (6,20 in giri precedenti) |
| theme1 | 0.56 | 0.56 | 1.1 | 0.99 | ok |
| twn1 | 2.44 | 2.44 | 2.0 | 1.80 | **fuori** (1,76 prima del 17/11) |
| stairs1 | — | 1.36 | 3.2 | 2.88 | ok |
| boss1 | — | 1.50 | 3.0 | 2.70 | ok |
| in1 | — | 5.76 | 5.7 | 5.13 | **fuori** |
| theme2 | 0.72 | 0.92 | 1.1 | 0.99 | ok |
| twn2 | 0.68 | 2.08 | 2.2 | 1.98 | variabile: **fuori** nel giro 2 |
| stairs2 | 1.52 | 1.73 | 3.2 | 2.88 | ok |
| boss2 | 1.17 | 1.13 | 3.0 | 2.70 | ok |
| in2 | 3.45 | 3.43 | 5.3 | 4.77 | ok |
| theme3 | 0.65 | 0.65 | 1.4 | 1.26 | ok |
| twn3 | 2.75 | 1.15 | 2.1 | 1.89 | variabile: **fuori** nel giro 1 |
| stairs3 | — | 1.55 | 3.2 | 2.88 | ok |
| boss3 | — | 1.50 | 3.0 | 2.70 | ok |
| in3 | — | 3.88 | 5.0 | 4.50 | ok |
| theme4 | 0.52 | 0.52 | 0.8 | 0.72 | ok |
| twn4 | 0.88 | 0.88 | 2.8 | 2.52 | ok |
| stairs4 | 1.88 | 1.68 | 3.2 | 2.88 | ok |
| in4 | 4.69 | 3.47 | 5.0 | 4.50 | variabile: **fuori** nel giro 1 |
| twn5 | 0.80 | 0.80 | 1.6 | 1.44 | ok |
| in5 | 4.19 | 4.04 | 4.6 | 4.14 | variabile: **fuori** nel giro 1 |

Gli altri tempi (tutti nei limiti): villaggio 0,0% di fotogrammi persi (PERF-10), inventario 0,10 s e minimappa 0,26 s
(PERF-11), negozi e locanda 0,12-0,14 s (PERF-19), cambi di piano 4,63 / 2,46 / 1,60 s (PERF-12), piano 1 0,9% e con i mostri
1,6% (PERF-13/14), Frenzy 24,1% (PERF-15, limite 40%), combattimento 5,9% (PERF-16), save game 7,24 s (PERF-17), piani
5/10/15/20 2,5 / 0,4 / 0,4 / 0,0% (PERF-18), boss finale 0,4% (PERF-20), piani 1-19 al massimo 12,6% (piano 14, PERF-21),
generatore 0,33-0,84 s (PERF-23). Durata dei test: smoke 11,1 s (tetto 20), smoke + sanity 16,5 s (tetto 35); in regression
i piu' lunghi sono ASM-10 40,5 s, LORE-10 26,0 s, KRILL-24 25,1 s, HELP-10 16,6 s, PERF-23 16,0 s, PERF-21 14,7 s.

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

| O15 ✓ | **(15/11, TODO D12)** Casella del mostro `mxl/mxh → pix2tile` e `myl/myh → pix2tile`, 4 copie ciascuno: `mon_tx` / `mon_ty` (X non preservato: i chiamanti ricaricano l'indice) | `game.asm` (`sync_monsters`, `bfs`, `kill_monster`, `chest_blocked`) | ~53 B (stima dalle istruzioni) | `MON-*`, `DUNG-CHEST-*`, `PERF-*` |
| O16 ✓ | **Puntatori della grafica `GFX_FSTRIP`**: 4 copie di `cp_n` (`.for`) → un ciclo (`cp_n` lascia già `ptr0` sulla striscia dopo e `ptr1` a fine striscia; +`$200`−striscia) | `game.asm` `copy_gfx` | ~63 B (stima; con O15 **+116 B misurati**: margine 1614 → 1730 B) | verificati i 4×152 byte dei caratteri fissi in VICE; tutti i test |
| O17 ✓ | `scr_black` (audio a zero, schermo nero, brano fermato) in `change_level` e `chap_travel` | `levels.asm`, `chapter.asm` | ~18 B (stima) | `CHAP-*`, `PERF-DISK-*`, `CHEAT-*` |
| O18 ✓ | `x8p` (indirizzo del glifo = codice × 8 + pagina) in `mm_names` e nel testo della barra | `ui.asm`, `bar.asm` | ~15 B (stima) | `MON-CHAP-*`, `MAP-*`, `PERF-*` |
| O19 ✓ | `mon_new` (posizione = centro della stanza, vivo, `lb_cnt`+1) in `place_boss` e nel piano finale | `game.asm`, `bar.asm` | ~13 B (stima) | `THRONE-10`, `MON-*` |
| O20 ✓ | `bx_g` (glifo del riquadro nel colore delle cornici) 4 volte in `ui_box` | `ui.asm` | ~27 B (stima) | screenshot, `UI-*` |
| O21 ✓ | `ui_k` ("k" dei kilo nel colore dei valori) 2 volte; `t01_addg` (`tmp0:1 += c_gold`) in `gold_total` e `g_mul10`; `row24` (riga dei tasti) 2 volte; `ch_floor` (baule tolto, casella a pavimento) in `ui.asm` e `rel.asm` | `ui.asm`, `stash_io.asm`, `rel.asm` | ~12 + 8 + 6 + 14 B (stime) | `INN-GOLD-*`, `SHOP-*`, `SAVE-*`, `DUNG-CHEST-*`, `LOOT-*` |
| O22 ✓ | `fin_rd` (puntatori `FIN_AT`..`FIN_END` + `load_raw`) in `fin_load` e `bmap_load` (blocco `$9C00`) | `disk.asm` | ~13 B nel blocco `$9C00` | `THRONE-10`, `GEN-10` |
| O23 ✓ | **START e LORE**: codice dell'altra variante escluso con `.if` (`boot.asm`: PRESS SPACE, `set_x`/`set_y` in START; `start_game` in LORE; `sid_player.inc`: `SP_RESUME = 0` toglie `sp_resume`, `sp_save`, `sp_release`) | `boot.asm`, `sid_player.inc` | START **−172 B** (2375 → 2203 di codice), LORE **−170 B** (4099 → 3929): solo tempo di caricamento | `BOOT-*`, `LORE-10`, `DISK-*`, `PERF-DISK-*` |

**Misura D12 (15/11)**: margine di GAME sotto `$8720` **1614 → 1824 B (+210 B)**, blocco `$9C00` **389 → 414 B (+25 B)**; GAME 29360 → 29125 B di codice (analisi). Le singole stime sopra sono dalle dimensioni delle istruzioni (O15+O16 = +116 B misurati insieme; il resto +94 B misurati insieme).
**Lasciate (non fatte) e perche'**: `px/py → ent_x/ent_y` (2 copie, 9 B: nel giro per fotogramma del movimento e dello sprite del PG, un `jsr` costa 12 cicli); `rel_put`/`rel_get` `stx rsx / sty rsy / php / sei` (9 B: chiamate per ogni byte del salvataggio, con cambio di `$01` e interrupt spenti: il rischio non si copre con i test che ho); `maprow → ptr0` e `lda #1 / sta vis...` in `gen_io.asm` (25 B in tutto: codice che gira con `$01=$34` e interrupt spenti, volutamente autonomo); le due finestre di LOBBY (`by/bw/bh`, 25 B: programma a parte con spazio libero, nessun guadagno per GAME); il JUKEBOX ha ancora 58 B di player non usati (`SP_RESUME = 0` ci starebbe, ma e' fuori da questo lavoro).

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
