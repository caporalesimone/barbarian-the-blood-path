# Analisi del codice e della memoria (22/11, richiesta del committente)

Analisi d'insieme di tutto il gioco fatta il 22/11: memoria (chi scrive dove e quando), difetti, duplicazioni, risparmi
possibili, sistema degli oggetti, menu, mostri, abilità, test. **Cosa è stato corretto subito** è in fondo (sezione 9), con i
commit. Le voci "da fare" sono proposte: nessuna è nel codice.

Metodo e limiti (da leggere prima del resto):
- **Automatico, su tutto**: mappa della memoria (`lab64 map`: aree annotate, zone libere, scenari), sovrapposizioni dei blocchi
  `.virtual` di tutti i sorgenti (script sulle etichette di `game.lbl`), etichette mai usate, sequenze di codice uguali
  byte per byte nei listati, `tools/build/asm_audit.py` (codice non raggiunto, spioncino, routine più grandi), tempi dei test.
- **Letto riga per riga**: `combat.asm` (regole, affissi, abilità, pozioni), `quest.asm`, `gen_citadel.asm`, `ovl_decor.asm`,
  `npc_look.asm`, `slist.asm` (parti), `inv.asm` (`ui_item`), la coda di `game.asm` (PRG, generatore, CORE), `chapter.asm`,
  `load_location`, `mkdisk.sh`, la ricerca dei file nel drive di Krill.
- **Non letto riga per riga** (28 000 righe in tutto): `game.asm` di gioco (movimento, mostri, bottino), `ui.asm`, `hud.asm`,
  `bar.asm`, `rel.asm`, `lobby.asm`, il modulo MENU, il player SID. Per questi valgono i controlli automatici e i 268 test di
  regressione (tutti verdi tranne i due di caricamento della sezione 7). **Un difetto in queste parti può essermi sfuggito.**

---

## 1. Mappa della memoria: chi usa cosa, e quando

Indirizzi della build del 22/11 (dopo le modifiche di oggi). "Riusabile" = cosa ci si può mettere e a quale condizione.

| Zona | Villaggio | Dungeon | Altro | Riusabile |
|---|---|---|---|---|
| `$0002-$0040` pagina zero | variabili | variabili | `$41-$47` Krill, `$41-$57` durante un salvataggio, `$4A/$4B` flusso `rel`, `$50-$5B` ZX0 | no: piena. `rpt` (`$4A`) è dentro la zona del plugin di salvataggio: va usato solo prima di chiamarlo (oggi è così) |
| `$0340-$03FF` | libera (i test ci mettono le loro routine) | idem | `YN_SAV` `$0340` | ~190 B di dati non salvati, **non usata dal gioco** |
| `$0400-$7F97` GAME | codice e dati | idem | — | margine **1928 B** fino a `$871F` (di cui `$8000-$871F` nel banco VIC: buono anche per sprite) |
| `$8720-$87E7` | righe dell'HUD | idem | — | no |
| `$87E8-$87F4` | variabili di grotte e cittadella | idem | — | 3 B |
| `$8800-$8A3F` | sprite della barra (set A) | idem | all'avvio: coda del PRG | no |
| `$8A40-$8B77` `SND_LBUF` | brano del luogo | idem | — | no |
| `$8B78-$8BFF` | **libera** (136 B) | **libera** | all'avvio sotto il font | **sì**: 136 B di dati o codice (non usati) |
| `$8C00-$8E7F` | **MENU zona 5** (NPC) | sprite forti e boss del tema | — | zona 5: 8 B liberi |
| `$8E80-$8F0D` `SND_FBUF` | (motivetto, non suona) | motivetto di combattimento | — | no: il motivetto resta in memoria fra un piano e l'altro e non si rilegge |
| `$8F16-$8F77` | **libera** (97 B) | **libera** | all'avvio: coda del PRG | **sì**, dopo l'avvio (`lab64 map` la segnala "not free" perché il PRG la copre al caricamento) |
| `$8F78-$8FFF` `NM_AT` | (nomi dei mostri) | colori e nomi dei mostri | — | no |
| `$9000-$94FF` | variabili | variabili | `$9480-$94F6` anche variabili del LOBBY (`slot_*`) | buchi: `$93D4-$93DF` (12), `$93E7-$93FF` (25), `$9448-$944F` (8), `$9475-$947F` (11) |
| `$9500-$95FF` `CHRBLK` | eroe e baule (salvato) | idem | — | 2 B |
| `$9600-$97FF` | **MENU zona 6** (passo degli NPC) | `MRT` mostri in gioco | — | zona 6: 28 B |
| `$9800-$9A87` `LVLBLK` | (azzerato) | stato del piano | — | nel villaggio **647 B liberi** (nessuno li usa: candidati per dati del solo villaggio) |
| `$9C00-$9FF0` `CODE2` | disco, baule, ricerca di percorso | idem | — | 15 B |
| `$A000-$A4FF` | sprite eroe; slot 12–19 = **MENU zona 4** (sprite NPC) | sprite eroe e mostri del tema | — | no |
| `$A500-$A5FB` | tabelle degli NPC (in `BFP`) | ricerca di percorso | variabili della palude | no (5 B) |
| `$A700-$A7FF` | **MENU zona 3** | (codice morto del MENU) | — | nel dungeon **256 B liberi** (slot sprite 28–31) |
| `$A800-$AFFF` | charset del luogo | idem | — | no |
| `$B000-$B3FF` | sprite della barra (set B) | idem | pagina Q: testo della quest (`QTXT`), poi ricostruiti | solo dentro una schermata che ridisegna la barra all'uscita |
| `$B400-$B7FF`, `$BC00-$BFFF` | schermi A e B | idem | `$BC00`: `QST0`, `CHEATS` (codice su file mentre lo schermo A mostra la UI) | 1000 B di codice su file **dentro una schermata** (già usato così) |
| `$B800-$BBFF` | font della UI + tabelle di GAME | idem | — | 56 B |
| `$C000-$C8FF` | `MAP` | `MAP` | LOBBY (`$C000-$CAA1`) al menu iniziale | no |
| `$C900-$CFFF` | **MENU zona 1** | codice del piano (`OVL`/`OVP`: boss, arredi, cittadella; ≤ 524 B) | — | villaggio: 875 B liberi in coda; dungeon: **~1250 B liberi** dopo il codice del piano |
| `$D000-$D07F` (sotto l'I/O) | `STASH` | `STASH` | elenco eroi al menu iniziale | no |
| `$D080-$DDFB` | generatore dei piani | idem | — | no |
| `$DDFC-$DFFF` | slot dei 5 piani del capitolo + 31 B | idem | — | 31 B |
| `$E000-$EBC1` (sotto il KERNAL) | `CORE` | `CORE` | immagine del salvataggio e plugin di Krill la coprono: `core_ok` = 0 e si rilegge | 62 B |
| `$EC00-$F4DF` | file del villaggio in arrivo, poi **libera**; appoggio del MENU; `CSHEET` quando aperta | file del tema in arrivo, poi **libera**; `CSHEET` | buffer del plugin di salvataggio | **2272 B per un modulo su file alla volta** (oggi solo la scheda C, 1431 B) |
| `$F4E0-$FCFF` | **MENU zona 2** (492 B liberi) | coda del tema fino a `$FB13` durante il caricamento, poi **libera** | — | **nel dungeon 2080 B liberi** dopo `gfx_install` (nessuno li usa) |
| `$FD00-$FFF9` | cache della sala del trono (`FMAP`) + **356 B liberi** | idem | — | 356 B di dati |

### 1.1 Zone riusabili che oggi nessuno usa (in ordine di valore)
1. **`$F4E0-$FCFF` nel dungeon (2080 B)**: codice o dati che servono solo nel dungeon. Va ricaricato dopo ogni lettura di un
   tema (la coda del tema ci passa sopra) o messo **in coda al file del tema** come già brano, mappa del boss e codice del piano.
2. **`$EC00-$F4DF` (2272 B)**: un secondo, terzo... modulo "schermata su file" oltre alla scheda C (minimappa, menu di gioco,
   morte, baule del piano): uno alla volta, con un byte "quale modulo c'è" al posto di `cs_ok`.
3. **`$C900-$CFFF` nel dungeon (~1250 B dopo il codice del piano)**.
4. **`LVLBLK` nel villaggio (647 B)** e **`$A700-$A7FF` nel dungeon (256 B)**.
5. Buchi piccoli di dati: `$8B78` (136 B), `$8F16` (97 B), `$FE96` (356 B), `$0340` (190 B).

### 1.2 Sovrascritture controllate
| Coppia | Esito |
|---|---|
| Variabili delle liste (`slist.asm`, `$9480`) sopra le variabili del LOBBY (`slot_name`...) | **Difetto trovato e corretto** (sezione 9.2): c'erano finite le variabili del testo a 5 bit, usate anche dal LOBBY |
| `CSHEET` a `$EC00` contro file del villaggio, tema, appoggio del MENU, immagine e buffer del salvataggio | corretto: ogni caricamento (`disk.asm`) e ogni salvataggio (`rel.asm`) azzerano `cs_ok`. Effetto collaterale: **qualunque** caricamento, anche di un brano, fa rileggere la scheda (vedi 4.4). `lab64 map` avvisa della sovrapposizione `ML_LO` / `CS_AT`: è nel tempo, non nello spazio |
| `CORE` contro immagine del salvataggio (`$E000`) e plugin (`$E820`) | corretto: `core_ok` = 0, `core_need` rilegge alla prima schermata |
| Zone 5 e 6 del MENU contro sprite del tema e tabelle dei mostri | corretto: nel dungeon `ovl_cur` = 0 e `npc_ok` blocca le chiamate; nel villaggio nessuno scrive `MRT` |
| Tabelle degli NPC in `BFP` contro la ricerca di percorso | corretto: nel villaggio non ci sono mostri |
| File del villaggio (`$EC00-$F9B1`) contro zona 2 del MENU (`$F4E0`) | corretto per ordine: prima il villaggio (installato), poi il MENU. Chi cambia l'ordine in `enter_gfx` rompe i negozi |
| `QTXT` (`$B000`) e `QBUF` (`$BC00`) | corretto: la pagina ricostruisce la barra all'uscita |

---

## 2. Difetti trovati

| # | Difetto | Gravità | Stato |
|---|---|---|---|
| 1 | Nome del **quarto eroe** rovinato nel menu dei barbari (caratteri 2–6) e forse scritto nel file `hl` | alta | **corretto** (9.2) |
| 2 | **Modificatore di FOR ~+126 e danno fisso 255** con oggetti maledetti (*of weakness* su 3–4 pezzi, arma *bent*/*dull*) | alta (trucco di gioco) | **corretto** (9.1) |
| 3 | Caratteristica +1 quando il totale degli affissi è negativo (riporto) | bassa | **corretto** (9.1) |
| 4 | `lab64 map` si fermava: annotazione `@map` con un'espressione | media (strumento) | **corretto** (9.1) |
| 5 | NPC con il **colore dell'eroe** o scuro su fondo scuro | media | **corretto** (9.5) |
| 6 | Test `AFX-12` e `DECOR-10` rotti da modifiche precedenti | bassa | **corretti** |
| 7 | **Unici a caso sbagliati per il piano**: `un_roll` confronta la finestra dell'unico con il **livello dell'oggetto** L, che è quasi sempre molto sotto il piano (L = T × u²). Al piano 19 l'unico più probabile è *osric's cudgel* (finestra 2–6); *tithe-taker*, *angel's tear*, *ruin's crown*, *aldric's heart* non escono praticamente mai. In tutto ~1 unico ogni 130–300 oggetti | media (bilanciamento) | **da decidere**: confrontare la finestra con T (il livello del tesoro) invece che con L, e alzare la probabilità |
| 8 | Unici deboli per la loro finestra: *stitchripper* (pugnale 1d4+3 ai piani 9–13, contro asce 1d12), *osric's cudgel* (1d6+2) | bassa (dati) | da tarare col simulatore |
| 9 | `PERF-DISK-14/21`: ingresso nel villaggio 5,10 s nel caso peggiore | media | **aperto** (sezione 7) |
| 11 | **Il boss del capitolo ha le statistiche di un mostro forte a caso**: nel piano 5 (10, 15) `place_boss` sceglie una variante forte qualsiasi (Fallen Warchief, Skeleton King, Lich, Balrog) e `build_sprites` le dà sprite e nome del boss del capitolo. Vita, CA e danni dell'abate cambiano da seme a seme (con il seme del bot era un Lich da 210 punti vita). Trovato con il bot | media (bilanciamento) | **deciso** il 22/11 (D8 di `wiki/quests.md`): boss predefiniti, tarati, sala disegnata |
| 10 | `docs/wiki/bestiario.md`, tabella "Nel gioco": al piano 10 scrive ancora *The Miller of Bad Water* | bassa (documento) | da correggere con la prossima revisione del bestiario |

---

## 3. Codice ripetuto e codice morto

- **Sequenze uguali byte per byte in GAME** (finestre ≥ 14 B, risparmio stimato facendone una routine): **~400 B** in tutto,
  ma i pezzi grossi sono voluti: 4 copie di 24 B nella minimappa (`mm_cls`, ciclo srotolato), 3 nelle grotte (sotto l'I/O),
  2 nel movimento (`solid_at`, percorso caldo). Realmente recuperabili senza toccare cicli critici: **~80 B** (`maprow` → `ptr0/ptr1`
  13 B, apertura di `QST0`/`CHEATS` 12 B, colore del valore in `ui.asm` 10 B, cornici `bx_g` 9 B, `nbuf` 9 B, pulizia della riga
  del riquadro 16 B, `ui_cic` + prefisso/suffisso 7 B).
- **`asm_audit.py`**: GAME 9 B non raggiunti (falso positivo: tabella dei salti), LOBBY 6 B (`detail_screen`, solo test),
  JUKEBOX 57 B di player non usato (`sp_resume`, `sp_save`, `sp_release`: basta `SP_RESUME = 0` come START e LORE),
  HELP 9 B (`tm_wait`), MENU: `NPC_JLOOK` non più chiamato da GAME dopo le modifiche di oggi (3 B).
- **Tolti oggi** (9.6): `shop_msg_clear`, `ob_half`, `wbuf`, `af_pf`, cinque `jsr`+`rts`.

---

## 4. Risparmi di memoria possibili (non fatti: vanno decisi)

Ordine: prima ciò che rende di più per rischio.

### 4.1 Schermate su file nella zona `$EC00` (come la scheda C) — fino a ~1900 B di GAME
Con la soglia di 3 s per i menu, una schermata può stare su disco. Misure della scheda C: 0,3–1,4 s.

| Schermata | Byte in GAME | Note |
|---|---|---|
| Minimappa (`ui_minimap`, `mm_sprites`, `mm_setgrp`, testi) | ~1050 | la più usata nel dungeon: resta in memoria finché non si legge altro (stesso meccanismo di `cs_ok`) |
| Baule del piano (`ui_chest`, `chest_take1`) | ~470 | solo dungeon: meglio nella zona `$F4E0` con il tema (4.2) |
| Morte (`ui_died`) | 176 | c'è già un caricamento subito dopo |
| Menu di gioco (`ui_gamemenu`) | 162 | |
| Salvataggio non valido (`ui_badsave`) | 209 | serve solo al caricamento di un eroe: va nel LOBBY (oggi mancano 37 B: liberarli lì) |

### 4.2 Codice del solo dungeon in coda al tema, a `$F4E0` — ~1500 B di GAME
`mon_path` (602 B, già in `CODE2`), `spawn_monsters` (269), `place_chests` (162), `place_monster` (166), `chest_gen_seed` (187),
`ui_chest` (470): tutto codice che gira solo nel dungeon. Il file del tema si legge già a ogni piano: 6 blocchi in più = ~0,4 s
per piano (le scale passano da 1,7–2,4 a 2,1–2,8 s, dentro la soglia di 4 s). Costo sul disco: 6 blocchi × 8 temi = 48 blocchi
(ne restano 94: **in conflitto con i testi delle quest**, ~66 blocchi). Alternativa senza costo sul disco: un file `DUNG` unico
riletto dopo ogni tema (+1 file a piano: +0,5–1,7 s secondo la directory, vedi sezione 7): **sconsigliato**.

### 4.3 Salvataggio su file — ~700 B di GAME
Il committente accetta salvataggi anche di 10 s. In `rel.asm` (1431 B) la parte che **scrive** il file (`rel_put`, `hdr_write`,
`sv_write`, `chap_copy`, costruzione dell'immagine) serve solo a "save game", cambio di capitolo e creazione dell'eroe: può
stare nel file del plugin (`ksave`, già letto a ogni salvataggio) o in un modulo a `$EC00`. Restano in GAME gli slot in RAM
(`lv_get`/`lv_put`). Da fare con cura (è il codice più delicato del gioco): test `SAVE-*` e `CHAP-SAVE-*` ci sono.

### 4.4 Piccoli
- `cs_ok` azzerato solo dai caricamenti che toccano `$EC00-$F4DF` (oggi da tutti, anche dai brani): niente byte, ma la scheda C
  non si rilegge dopo ogni cambio di musica.
- Motivetto di combattimento a `$F4E0` nel dungeon: 384 B di buffer (TODO D10).
- Tabelle di sola generazione ancora in GAME: `un_base`/`un_lo`/`un_hi` sono già nel font; `shop_items`/`shop_minl` (solo
  villaggio) nel modulo MENU (zona 1: 875 B liberi): ~60 B.
- Creazione dell'eroe (`new_character`, `game_start`: 311 B) usata una volta per partita: nel LOBBY o in un modulo.
- Codice ripetuto recuperabile: ~80 B (sezione 3). JUKEBOX: 57 B (solo tempo di caricamento).

### 4.5 Somma
Senza toccare il disco: 4.1 (minimappa, morte, menu di gioco: ~1400 B) + 4.3 (~700 B) + 4.4 (~450 B) ≈ **2500 B**, che portano
il margine di GAME da 1928 a ~4400 B. Bastano per il motore delle quest (~310 B), la cintura a 8 e le meccaniche dei boss.

---

## 5. Oggetti e armi

Controllati dati (`bases.tsv`, `prefixes.tsv`, `suffixes.tsv`, `uniques.tsv`), generatore (`gen_db.py`), codice
(`af_one`, `af_pair`, `af_dur`, `af_gen`, `af_pick`, `un_roll`, `it_cost`, `recalc_stats`, `ui_item`, `it_pw`, `it_qcol`).

- **Corretto**: 31 basi coerenti (ilvl crescente con il prezzo, requisiti FOR 13–19 e DES 14 raggiungibili: l'eroe parte da
  FOR 16, DES 13); 19 prefissi e 32 suffissi, tutti con valore fisso in un byte con segno; pesi dentro un byte; prezzi con segno
  (i maledetti costano meno, minimo 1); durabilità +50/+100/−50 e indistruttibile alla nascita; un oggetto rotto o lo scudo con
  un'arma a due mani non danno affissi; unici con base, prezzo e poteri come nel `.tsv` (test `UNQ-10`).
- **Difetti**: i tre della sezione 2 (righe 2, 3, 7).
- **Osservazioni**:
  - Valori negativi solo su DMG, ATT_DMG, AC, STR, DUR: gli altri totali (`af_life`, `af_gh`, `af_pen`, `af_spd`) non hanno
    protezione contro un valore negativo. Se un domani si aggiunge un affisso maledetto di vita o cadenza, serve il controllo
    (dal 22/11 `gen_db.py` ferma la build se una riga ha un valore negativo su un potere diverso da questi).
  - La cadenza minima `RATE_MIN` = 6 fotogrammi: con *stitchripper* (SPEED 2) e un suffisso di cadenza si arriva vicino; da
    verificare nel simulatore che non sia il modo migliore di giocare.
  - Furto di vita e spine: senza effetto (TODO G11, con la dinamica proposta).
  - Gli unici garantiti (boss, quest, bauli epici) non esistono ancora: oggi un unico esce solo a caso (riga 7 della sezione 2).

## 6. Menu, mostri, abilità

- **Menu**: le liste (inventario, locanda, baule, negozi) usano tutte `slist.asm`; nome intero dal 22/11. Le schermate sono
  coperte dai test `UI-*`, `SHOP-*`, `INN-*`, `AFU-*` e dagli screenshot in `docs/screens/` (rifatti quelli cambiati).
  Punti deboli: la riga dei poteri (`it_pw`) si ferma alla colonna 34 senza segnalarlo (un unico con 4 poteri "fuori dai
  numeri" ne mostrerebbe 3: oggi nessuno ne ha più di 3); `ui_w` va impostato da ogni chiamante di `ui_item` (3 chiamanti:
  se se ne aggiunge uno e lo dimentica, il nome non si vede).
- **Mostri**: statistiche per tipo e piano in `floor_types` (lette e ricontrollate: curva della vita, esperienza, CA e ATT
  crescono con il piano; boss con nome × `BOSS_HPH`/2); attacco dei mostri e usura corretti. Le 4 famiglie + 4 forti per
  capitolo cambiano solo grafica, colore e nome (stesse statistiche: TODO M9). Boss dei capitoli: modelli e colori coerenti con
  il loro piano (controllati sugli screenshot dei piani 5, 10, 15: abate azzurro nella cripta, Mother Stitch viola nella
  palude, Varok giallo nel bastione grigio); nessuna modifica.
- **Abilità**: ricariche e durate a 16 bit (`tick_timers`), Rage e Frenzy (`buff_act`), corsa della Frenzy (`fz_move`),
  Battle Cry con tiro salvezza, Smash con vantaggio e dadi doppi, critico da 19 dal livello `CRIT_LVL`: letti, nessun difetto.
  Lo sblocco è per solo livello (3, 6, 9, 12, 15): con le quest servirà anche il passo della catena (`QUEST-IMPLEMENTAZIONE.md`).
- **Cittadella**: 4 colonne per sala della navata (32 a piano) al posto di una ogni 3 caselle (9.3).
- **Villaggio**: NPC ridisegnati e colori per villaggio (9.5).

## 7. Disco e tempi di caricamento
Studio completo in [FastLoader 7.5](wiki/FastLoader.md). In breve: il caso tipico è dentro le soglie proposte (ingresso nel
villaggio 2,5–2,7 s, scale 1,7–2,4 s, morte e portale 2,7 s, scheda C ≤ 1,4 s, salvataggio 5–7 s). Il caso peggiore
dell'ingresso nel villaggio (5,1 s dopo scheda C, pagina Q o salvataggio) dipende dalla ricerca in avanti di Krill nella
directory: 5 disposizioni provate, nessuna lo garantisce sotto i 4 s. Soluzione robusta: **un solo file per passaggio**
(`MENU` in coda a `TWNc`), o meno voci nella directory, o file aperti per traccia e settore.

## 8. Test
- 36 smoke + sanity (17 s), 268 regression. **Tempi**: regressione completa da ~780 a ~685 s dopo le ottimizzazioni di oggi
  (`ASM-10` 67 → 1 s, `CHAP-11` 48 → 20 s). I più lenti rimasti sono legati al tempo emulato: `LORE-10` 32 s (lo scorrimento
  dell'intro), `KRILL-24` 26 s, `PERF-24`/`PERF-23` ~20 s, `DECOR-10` 18 s, `GEN-10..13` 10–17 s l'uno.
  Idee non fatte: `GEN-11/12/13` e `DECOR-10` aprono ognuno una sessione VICE e rifanno avvio e partita nuova (~3 s l'uno):
  una sessione sola per i quattro; `LORE-10` può partire da uno snapshot a metà testo.
- **Scenari scoperti** (non c'è un test):
  - vendere, riparare e mettere nel baule della locanda un **unico** (oggi provati solo nome, colore, poteri, prezzo calcolato);
  - menu dei barbari con **5 eroi** e nomi lunghi (c'è `LOBBY-13` per il quarto, aggiunto oggi);
  - un oggetto maledetto comprato o venduto (prezzo minimo 1);
  - la sequenza reale "scheda C nel dungeon → villaggio" (è il caso peggiore dei caricamenti: oggi lo misura per caso la
    catena dei `PERF-DISK`);
  - partita lunga senza scorciatoie: la copre il **bot** di `tests/bot/` (22/11).
- I test che dipendono dall'ordine (`CHAIN`) nascondono difetti quando si lancia un sottoinsieme: `AFX-12` è rimasto rotto un
  commit perché avevo rilanciato solo alcuni gruppi. Regola pratica: prima di un commit che tocca le liste o gli oggetti,
  `lab64 test regression -k AF` e `-k UI`.

## 9. Fatto il 22/11 (un commit per voce)
1. `b7bc694` modificatori e danno fisso con gli affissi maledetti; annotazione `@map` (test `AFP-14`).
2. `7d6b275` nome del quarto eroe nel menu dei barbari (test `LOBBY-13`).
3. `6df0e2c`, `bd766d6` cittadella con 4 colonne per sala della navata, `GVER` 12; test `DECOR-10`.
4. `cf035b0` test più veloci (`asm_audit.py`, `items_model.py`).
5. `de02b21` NPC del villaggio ridisegnati, colori per villaggio.
6. `47320ab` codice e variabili morte.
7. `0d50077` definizione di tutte le quest e documento di implementazione; `b4cda0f` TODO G11 (furto di vita e spine) e
   proposta grafica dell'eroe (`lab/proposte/hero_proposal.py`); `378f48c` studio del disco.

## 10. Grafica dell'eroe (proposta, non nel gioco)
`lab/proposte/hero_proposal.py` disegna `out/work/proposals/hero_proposal.png`: eroe nuovo, camminata a 4 passi, aspetto
secondo l'equipaggiamento.
- **Più sprite per il movimento: si può.** Oggi 8 sprite (2 per direzione). Con 3 sprite per direzione (passo sinistro,
  fermo, passo destro: ciclo di 4 passi) sono 12: **+256 B** nel banco VIC. Lo spazio c'è nel margine di GAME (`$8000-$871F`
  è nel banco) oppure negli slot sprite 20–23 se la ricerca di percorso cambia posto. Codice: l'indice del fotogramma passa da
  1 a 2 bit (~20 B).
- **Aspetto secondo l'equipaggiamento**: due strade. (a) *Colore*: il colore dello sprite segue l'armatura (pelle, cuoio,
  maglia): 0 B di grafica, ~15 B di codice, ma oggi quel colore è la pelle. (b) *Righe sostituite*: torso (6 righe × 3 byte) e
  mano con scudo o arma copiati negli sprite dell'eroe quando cambia l'equipaggiamento: ~450 B di tabelle per 3 armature, 3 armi
  e lo scudo su 12 sprite, ~80 B di codice, nessun costo per fotogramma.
- Limite comune: i due multicolor degli sprite (marrone e grigio) sono condivisi con i mostri: le parti marroni dell'eroe
  spariscono sul terreno marrone come succedeva agli NPC. La bozza usa il colore dello sprite per la sagoma.
