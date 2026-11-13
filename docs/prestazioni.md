# Prestazioni del motore: analisi del 10/11/2026

Analisi dei **fotogrammi persi** (il ciclo principale non finisce il lavoro entro un fotogramma PAL, 19 656 cicli) nel
villaggio e nel dungeon, e di tre idee per ridurli: **colore per tile**, **scorrimento a mezza casella**, **scorrimento a
casella**. Versione del gioco misurata: **v1.146**. Il gioco non è stato modificato: tutte le prove "usa e getta" sono
state fatte in una copia del progetto, poi cancellata. Il lavoro ancora aperto è in `TODO.md` voce 1.9.

> Certezza: le percentuali sono **misure reali in VICE** (`x64sc`, PAL), ma di corse brevi (poche centinaia di
> fotogrammi) e con mostri che si comportano in modo diverso a ogni corsa: ±5 punti fra corse uguali nel dungeon. Vanno
> lette come ordini di grandezza, non come valori esatti. Il precaricamento da disco era spento (build di prova).

## 1. Come funziona il ciclo (utile per leggere i numeri)

- Il ciclo principale è cadenzato da `wait_vblank`: un giro = un fotogramma. Se il lavoro supera 19 656 cicli, il giro
  "salta" un fotogramma video: **fotogramma perso**.
- Camera: `update_camera` → `maybe_redraw` → `prefetch` / `rc_run` (11 passi) → `pend_flip` → `apply_frame`. Il doppio schermo
  (`SCR_A=$B400`, `SCR_B=$BC00`) si scambia **a ogni carattere (8 px)**: ogni 4 fotogrammi camminando, ogni 2 in Frenzy.
  (Una versione precedente di queste note diceva 16 px: era sbagliato.) Qui `prefetch` = preparare lo schermo nascosto,
  non caricare da disco (il caricamento è `pf_tick`).
- Se la previsione del ridisegno sbaglia, `_sync` ridisegna tutto in un solo fotogramma.
- Misura del ciclo con `TMDBG` (`tools/vice/tmrun.sh`, piano 1, PG fermo): lavoro del giro 5–8 mila cicli di solito, picchi
  15–18 mila (nei picchi circa il 90% del fotogramma).

## 2. Strumenti e metodo

### 2.1 Contatori nel gioco (già nel progetto, `-D TESTFZ=...`, solo `tools/build/asm.sh test`)

| Simbolo | Significato |
|---|---|
| `TESTFZ=1` | Frenzy permanente alla corsa `TESTFZR` (0..100, +0..100%), `levels.asm` |
| `TESTFZ=2` | solo contatori |
| `$03F8` | fotogrammi video (incrementato nell'IRQ, 16 bit) |
| `$03FA` | giri del ciclo principale (16 bit) |
| `$0340` | campioni da 5 B ogni 32 giri: persi cumulati, px, py |
| `TESTFZS=0/1/2` | corsa scriptata orizzontale / verticale / diagonale (`testscript` in `data.asm`) |
| `TESTGOD=1` | PG invulnerabile (per correre fra i mostri senza morire) |
| `TESTLVL`, `TESTX`, `TESTY` | piano di partenza e posizione (villaggio: `TESTLVL=0 TESTX=16 TESTY=31`; dungeon: `TESTLVL=8`) |

**Fotogrammi persi = `$03F8` − `$03FA`** (fra due letture, con warp spento), in percentuale dei fotogrammi video.

### 2.2 VICE e monitor remoto

- `x64sc -silent -sounddev dummy ... -warp -8 disco.d64 -remotemonitor` dentro `xvfb-run -a` (nessuno schermo vero).
- Il monitor remoto è la porta TCP **6510**: si invia un comando per riga e si legge fino al prompt `(C:$xxxx)`.
  Comandi usati: `l "game.prg" 0` (carica), `g 0400` (parte), `m a b` (legge memoria), `break <addr>`, `x` (continua),
  `del`, `warp off`, `screenshot "f.png" 2`, `r` (registri; serve a far aggiornare il quadro dopo una fermata).
- Attesa all'avvio: ciclo di tentativi di connessione alla 6510 (con `sleep` fisso la corsa partiva in modo casuale).
- **Misura veloce** (numeri): corsa a velocità normale per ~12 s, poi lettura di `$03F8`, `$03FA` e dei campioni.
- Tempi del ciclo: `tools/vice/tmrun.sh` (TMDBG), profilo di funzione con `tools/vice/prof.sh` (contatore di cicli).

### 2.3 Corsa scriptata `TESTFZS=3` (solo nella copia di prova, ~10 s, ripetuta)

Sequenza (byte: direzione, durata, ...): destra, giù, sinistra, su, due diagonali, ripetuta due volte. È l'unica cosa che
serve per confrontare varianti con lo **stesso input**; i mostri restano comunque non deterministici.
Se serve di nuovo va riaggiunta in `testscript` (`data.asm`) con un blocco `.for` che ripete le direzioni
`8,2,4,1,10,5` (valori della tastiera/joystick del motore) con durata 40/30 giri.

### 2.4 Prove nella copia (varianti)

- **Colore per tile** (`COLPROVA=1`): colore per codice carattere nella tabella `COLTAB` (`$CD00`, 256 B); ombra dei colori
  `COLSH` (`$C900`, 880 B) scritta dal ridisegno insieme alle 4 caselle del tile; `col_copy` (800 B nella color RAM `$D800`)
  a ogni scambio, subito dopo i registri VIC e sprite. Tile ritoccati per usare il 4° colore: tetti (`BROOF`, `BROOFA`,
  `BROOFL`), guglia `SPIRE`, ponte `BRIDGE` (in `gen_gfx.py`, funzione `make_tile` avvolta). Costo contato sulle istruzioni:
  ~7,7–8 mila cicli la copia + ~7 mila nel ridisegno; +250 B di codice, +880 B ombra, +256 B tabella.
- **Camera a passi** (`CAMQ=8` mezza casella, `CAMQ=16` casella): in `update_camera` si conservano le coordinate vere
  (`camxr`, `camyr`) e `camx`/`camy` si troncano con `and #<(-CAMQ)`; il PG si muove sempre a pixel, scatta solo la vista.
  La previsione (`prefetch`) si adatta con `QM = CAMQ-1` e `QS = CAMQ/8` (passo di `pf_tx`/`pf_ty`, soglie `(QM+1)/4`,
  `(QM+1)*5/8`, limiti `59-QS` e `76-QS`).
- Ogni variante è stata assemblata con `tools/build/asm.sh test` e provata con le stesse variabili.

### 2.5 Registrazione fotogramma per fotogramma (video)

Script di cattura: assembla la variante, avvia VICE con `-refreshonbreak`, parte in warp fino a `main_loop` (breakpoint),
poi **warp spento** e breakpoint su `main_loop+3` (subito dopo `wait_vblank`, quando il fotogramma è disegnato). A ogni
fermata: lettura del contatore `$03F8`, `r` + attesa di 20 ms, `screenshot` PNG, `x`. Si salva l'**indice del fotogramma
video** di ogni PNG. Così quando il gioco perde un fotogramma, l'indice salta e nel video l'immagine **resta ferma** per quel
fotogramma, come la vede il giocatore.

Montaggio (Python + Pillow + `ffmpeg`): per ogni istante `t` di 500 fotogrammi (50/s, saltando i primi 45 per l'avvio) si
sceglie per ogni variante l'ultimo PNG con indice ≤ `t`, lo si scala (×2, vicino più prossimo) in riquadri da 576×408
con etichetta e "fotogrammi persi in questi 10 s", si compone una griglia 2×2 e si codifica con
`ffmpeg -framerate 50 -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p`.
Video prodotti: villaggio (oggi / colore / colore+8 px / colore+16 px), dungeon piano 8 (stesse quattro varianti),
pixel contro casella senza colore (villaggio e dungeon). Consegnati all'utente e poi cancellati con la copia di prova.

## 3. Risultati

### 3.1 Prima misura (v1.146, camminata e Frenzy)

| Scenario | Fotogrammi persi |
|---|---|
| Villaggio, camminata (3 direzioni) | 0% |
| Villaggio, Frenzy (`TESTFZR=100`) | 0–3% |
| Piano 8, camminata diagonale, mostri vicini | circa 16% |
| Piano 8, Frenzy diagonale | circa 38% |
| Piano 8, Frenzy verticale (il PG si ferma presto contro un muro, poi combatte) | 4,7% sull'intera corsa |
| Piano 12, Frenzy diagonale | circa 32% |

### 3.2 Seconda misura (corsa `TESTFZS=3`, nel solo tratto in movimento)

| Variante | Villaggio, passo | Villaggio, Frenzy | Piano 8, passo | Piano 8, Frenzy |
|---|---|---|---|---|
| oggi (a pixel) | 0% | circa 1% | circa 8% | circa 22% |
| oggi, camera a casella | 0% | 0% | circa 7% | circa 11% |
| colore per tile, a pixel | circa 20% (*) | circa 35% | circa 23% | circa 35% |
| colore, mezza casella | circa 20% (*) | circa 35% | circa 23% | circa 35% |
| colore, casella | circa 10% (*) | circa 17% | circa 17% | circa 23% |

(*) nel solo movimento; sull'intera corsa di 10 s (il PG sta spesso fermo contro un ostacolo) circa 5% (a casella circa 2%).

### 3.3 Conclusioni

- **Mezza casella non fa risparmiare nulla**: lo scambio degli schermi avviene già ogni 8 px.
- **Casella (16 px)** dimezza gli scambi e circa i fotogrammi persi, anche senza colore (dungeon in Frenzy da ~22% a ~11%).
  Costo: la vista scatta di 16 px (da valutare a mano: idea "solo in Frenzy o nei combattimenti affollati").
- **Colore per tile: non adottato.** Villaggio da 0% a ~20% camminando; nel dungeon anche a casella resta peggio di oggi.
  Anteprime del 10/11: hires puro peggiore; multicolor con il 4° colore per tile più bello ma troppo costoso con lo
  scorrimento a carattere.
- Il dungeon di oggi perde già il 6–8% camminando e il 22–38% in Frenzy (a seconda della corsa): non investigato ancora
  (cosa pesa: voce 1.9 del TODO).

### 3.4 Fragilità della catena degli IRQ (osservata, non risolta)

Con il carico in più del colore a pixel o a mezza casella la catena degli IRQ si è **desincronizzata** e non si è più
ripresa: il contatore dei fotogrammi video si è fermato mentre il ciclo continuava; bordo e sfondo sbagliati e registri
VIC persistentemente errati (in VICE `d011 0b`, `d018 0b`, bordo grigio); nel villaggio è successo dopo l'accensione
dell'etichetta in alto (`bar_on`). Tentativo non riuscito: spostare `col_copy` dopo i registri. **Ipotesi, non verificata**:
`apply_frame` che arriva dopo la riga raster dell'IRQ programmato (`IRQ_BAR`). Due misure (colore a pixel e a mezza casella
nel dungeon) sono **invalide** per questo e i video relativi mostrano colori sbagliati. Le misure "colore a casella" non
hanno il problema. Importante per il quest system: il motore deve riprendersi da un fotogramma lungo.

## 4. Limiti delle misure

- Build di prova: precaricamento (`pf_tick`) spento; il gioco vero può andare un po' peggio.
- Mostri non deterministici (±5 punti), corse di poche centinaia di fotogrammi, un solo seme.
- Copia del progetto con modifiche solo per la prova (non è il gioco).
- Il PG in "casella" si muove comunque a pixel: muoverlo a scatti cambierebbe il gioco senza far risparmiare CPU
  (non provato).

## 5. Come ripetere la misura

1. `tools/build/asm.sh test` con `TESTFZ=2 TESTFZS=<n> TESTLVL=<piano> [TESTGOD=1] [TESTX/TESTY]`, poi `tools/build/mkdisk.sh dev`.
2. VICE con monitor remoto come in 2.2; caricare `out/game.prg`, partire con `g 0400`, attendere.
3. Leggere `$03F8..$03FB` all'inizio e alla fine di una finestra (warp spento): persi = Δ`$03F8` − Δ`$03FA`.
4. Per il tempo per funzione: `tools/vice/prof.sh`; per il ciclo: `TMDBG` + `tools/vice/tmrun.sh`.
5. Stesso seme, stesso script, stessa versione per confrontare prima/dopo; annotare i numeri qui.

## Caricamenti con Krill's Loader (11/11, ramo `fast-loader`)

Misure e confronto con il KERNAL in [FastLoader.md](FastLoader.md), sezione 7: caricamenti dal 26% al 78% più veloci
(avvio 105 → 34,5 s, modulo MENU 10,5 → 2,3 s, villaggio → piano 1 11,1 → 3,1 s), salvataggi più lenti (3,2–5,4 → 7,1–8,6 s).

## Test di prestazione automatici (11/11, `tests/regression/perf`, PERF-10..23)

Durata di ogni fotogramma = cicli fra due letture dell'input nel ciclo principale (contatore di cicli del C64, il warp
di VICE non conta); **perso** = più di 1,5 fotogrammi PAL. Le soglie sono le misure qui sotto più un margine: il test
fallisce se il gioco diventa più lento di oggi. Eroe in godmode (non deve morire mentre si misura), disco di sviluppo,
1541 emulata. Misure dell'11/11 (v1.171):

| Test | Situazione | Misura | Soglia |
|---|---|---|---|
| PERF-10 | villaggio, cammino in 8 direzioni (320 fot.) | 0% persi, peggiore 1,05 | 2%, 2 |
| PERF-11 | apertura inventario / minimappa (villaggio), ritorno al gioco | 0,10 s / **0,64 s**, 0,06–0,08 s | 0,3 s / 1 s, 0,3 s |
| PERF-12 | cambio di piano con le scale: villaggio → 1, 1 → 2, 2 → 1 | con Krill (11/11, ramo `fast-loader`): **3,1 s**, 10,2 s, 11,4 s (il piano lasciato si salva: file intero); prima, KERNAL con cache: 12,1–12,5 s, 5,6–5,8 s, 6,8–7,3 s; KERNAL senza cache: 11,1, 13,8, 15,8 s | 5, 13, 13 s |
| PERF-13 | piano 1, cammino | 1,9–2,2%, peggiore 2,00 | 6%, 2,5 |
| PERF-14 | piano 1, cammino fra i mostri (svegli) | 4,4–5,0%, 2,07 | 10%, 2,5 |
| PERF-15 | Frenzy (+100%) fra i mostri | **27%**, 2,07 | 40%, 3 |
| PERF-16 | combattimento con 5 mostri addosso | 7,9–9,2%, 2,02 | 15%, 3 |
| PERF-17 | "save game" dal menu di gioco | con Krill (11/11): **7,1 s** nel dungeon (piano + eroe in una riscrittura del file, 9 blocchi), 8,6 s nel villaggio; prima, REL: 3,2–5,4 s | 10 s (provvisoria) |
| PERF-18 | cammino ai piani 5, 10, 15, 20 | 0%, 0–0,8%, 3,8%, 0–0,4% (peggiore al 20: fino a 2,95) | 5/6/10/5%, 2,5 (20: 4) |
| PERF-19 | (11/11) apertura del fabbro, della locanda due volte, ritorno; dalla v1.223 con il modulo MENU già in memoria (caricato all'ingresso nel villaggio: 10,5 s con il KERNAL, 2,3 s con Krill, `MENU-11`) | 0,12 s; 0,14 s; 0,14 s; 0,06 s (v1.195: la locanda la prima volta **9,18 s**) | 0,5 s |
| PERF-20 | combattimento col boss finale nella sala del trono (Fire tenuto, 240 fot.) | 0,4%, 2,00 | 25%, 4 |
| PERF-21 | cammino su **ogni** piano 1–19 (160 fot. per piano, discesa con le scale) | 0–14,5% (massimo al 14), peggiore 2,03 | 20%, 3 |
| PERF-22 | cammino nei piani dell'Abisso 21–255 | — (SKIP: l'Abisso non c'è nel gioco) | — |
| PERF-23 | **generatore** su ogni piano 1–19 e su **ogni piano dell'Abisso 21–255** (`gen_dungeon` chiamata fra due letture dell'input; il piano 20 è la mappa fissa) | 1–19: 0,38–0,73 s (media 0,58); 21–255: 0,34–0,84 s (media 0,58); una sola scala in salita ovunque | 1,5 s |

Osservazioni (da valutare, non verificate a fondo): il primo ingresso nel piano 1 dal villaggio è il passaggio più lento
(tema, brano e piano: ~12 s in VICE); la minimappa del villaggio impiega 0,64 s a disegnarsi; la Frenzy perde ~1/4 dei
fotogrammi (TODO D3). Dall'11/11 (PERF-19..23): la **prima** apertura della locanda costava ~9 s (caricamento di OVLT e
OVL2 dal disco; dalla v1.223 il modulo MENU si carica all'ingresso nel villaggio, sezione sotto), le successive 0,14 s; il piano 14 è il più pesante nel cammino (14,5% di persi); il generatore regge
tutti i 255 piani (oltre il 20 senza scala in discesa, come vuole `gen_stairs` con `cur_level` ≥ `MAXLEVEL`): l'unica parte
dell'Abisso misurabile oggi. Attenzione: con `fz_run` > 0 rimasto da una Frenzy interrotta a mano (test) il cammino ai piani
profondi arrivava al 33% di persi: la misura dipende dalla velocità della corsa.

## Menu del villaggio: modulo MENU residente (11/11, v1.223)

Richiesta del committente (11/11): "la soluzione più ottimale" per tutti i menu del villaggio con le priorità **1. spazio
del codice, 2. velocità, 3. RAM**. Fatto: locanda **e negozi** nel modulo MENU (tre zone di RAM, compresso), caricato
**una volta** all'ingresso nel villaggio e poi residente; il precaricamento del tema scrive direttamente nella cache del
tema ([Tecnica](tecnica.md#moduli-su-disco)). Misure (VICE, 1541 emulata, contatore di cicli; `tools/vice/menu_time.py`,
`PERF-19`, `MENU-11`):

| | v1.205 (OVLT + OVL2) | v1.210 (file MENU = locanda) | **v1.223 (MENU = locanda + negozi, residente)** |
|---|---|---|---|
| codice di GAME libero (sotto `$8720`) | 2071 B | 1558 B | **3501 B** |
| caricamento all'ingresso nel villaggio (avvio partita / dopo il LOBBY) | — | — | **10,5 s** (3227 B, una volta) |
| fabbro, alchimista | 0,12 s | 0,12 s | 0,12–0,14 s |
| locanda, prima apertura | 8,45 s | 6,37 s | **0,14 s** |
| locanda dopo un precaricamento (ritorno dal dungeon) | ~3,6 s | 3,27 s | **0,14 s** (niente più conflitto) |

**Da dove viene lo spazio** (+1943 B di GAME rispetto alla v1.210): i negozi tolti da GAME (~1,77 KB, restano solo le
routine condivise con inventario e baule e `ch_item`, 75 B), `ui_cur`/`ui_n`/`ui_col`/`ui_ib`/`ui_sel`/`ui_lc` in pagina
zero (istruzioni più corte in tutto il gioco), il precaricamento senza copia e senza `pf_wait`/`ovl2_ok`, il caricamento
del MENU senza la parte "solo OVL2". **RAM usata in cambio**: `$F4E0`–`$FCFF` (era del precaricamento), gli slot sprite
28–31 (`$A700`–`$A7FF`, liberi), pagina zero `$3B`–`$40` e `$5C`–`$8C` (liberi).

**Costi e limiti** (da sapere):
- il caricamento di 10,5 s all'inizio di ogni partita (e dopo ogni passaggio dal LOBBY), al posto dei 6,4 s della
  prima locanda e dei 3,3 s a ogni ritorno dal dungeon. Alternativa a costo zero di codice: caricarlo alla prima porta
  invece che all'ingresso (stessi 10,5 s, ma solo se si entra in un menu);
- il precaricamento nel villaggio legge in pratica **1 byte per fotogramma** (~40 s per un tema, misurato 11/11): con
  il MENU in fondo (3227 B) un precaricamento in sottofondo del modulo non avrebbe senso;
- il tema precaricato sovrascrive quello in cache: tornando a un piano col tema di prima (solo 19 ↔ 20: i piani 1–19
  hanno tutti `GFX1`) il tema si rilegge (~5 s), prima no;
- lo spazio libero delle zone è poco (zona 1 170 B, zona 2 9 B, zona 3 93 B: 272 B in tutto); la build lo stampa.

## Locanda: file MENU compresso (11/11, v1.210): prima apertura da 8,45 a 6,37 s (superato dalla sezione sopra)

Dall'11/11 la locanda (OVLT + OVL2) sta in **un file solo, `MENU`, compresso ZX0** (`tools/build/pack_menu.py`, formato in
[FORMATO_DATI](FORMATO_DATI.md#menu--menu-del-villaggio-locanda-e-negozi)): una sola apertura, una sola sfumatura della musica,
1874 B invece di 2354 (8 blocchi invece di 10). Misura con `tools/vice/inn_time.py` (oggi `menu_time.py`) (VICE, 1541 emulata, cronometro di
cicli; dal Fire davanti alla porta alla schermata disegnata, prima chiamata di `h_flash`), stesso metodo prima e dopo:

| Caso | Prima (v1.205, OVLT + OVL2) | Dopo (v1.210, `MENU`) |
|---|---|---|
| prima apertura | **8,45 s** | **6,37 s** (sfumatura 0,31 + apertura 0,03 + lettura 5,65 + decompressione 0,26 + disegno 0,12) |
| di nuovo (moduli in memoria) | 0,055 s | 0,06 s |
| solo OVL2 da rileggere (`ovl2_ok` = 0, dopo il precaricamento) | ~3,6 s (misura precedente, non rifatta: lo script sulla v1.205 non ha ricaricato, da capire) | **3,27 s** (si legge solo la parte A e si chiude il file) |

Decompressione: ~0,09 s OVL2, ~0,15 s OVLT (sul posto, in fondo alle loro zone). Costo: GAME +513 B (decompressore ZX0
~240 B + `ovl_town`/`ovl2_load` riscritte con l'intestazione e la barra), margine 2071 → 1558 B; `CODE2` +43 B liberi.
Test: `MENU-10/11/12` (file, prima apertura < 7 s, solo OVL2 < 3,5 s), `VIL-OVL2-10/11`.

## Locanda: perché la prima apertura durava ~9 s (analisi dell'11/11, prima del file MENU)

Misura in VICE (1541 emulata, cronometro di cicli; disco di sviluppo v1.197, eroe nuovo davanti alla porta, Fire):
punti di fermata in `ovl_town`, `ld_open`, dopo `snd_io`, dopo `KOPEN`, al primo byte (`load_raw`), `ld_ok`, `ovl2_load`.

| Fase | OVLT (1413 B, 6 blocchi, traccia 12) | OVL2 (937 B, 4 blocchi, traccia 11) | Totale |
|---|---|---|---|
| sfumatura della musica prima del disco (`snd_io` → `snd_fade`) | 0,31 s | 0,23 s | 0,54 s |
| schermata "loading" (`io_screen`) + `KOPEN` | 0,03 s | 0,03 s | 0,07 s |
| apertura del file: ricerca nella directory e primo settore (`KCHKIN`/primo `KCHRIN`) | 0,66 s | 0,94 s | 1,60 s |
| trasferimento dei dati (KERNAL, ~385–390 B/s) | 3,69 s | 2,39 s | 6,08 s |
| disegno della schermata della locanda (ordinamento, statistiche, riquadri) | — | — | ~0,9 s |
| **totale** (PERF-19: 9,18 s) | 4,71 s | 3,59 s | **~9,2 s** |

Le volte dopo: 0,14 s (OVLT resta a `$C900` finché non si carica il LOBBY; OVL2 resta a `$F500` finché il precaricamento
non lo sovrascrive: allora si ricarica solo OVL2, ~3,6 s, vedi [villaggio](villaggio.md)).

**Cosa impatta**: due terzi del tempo sono il trasferimento a velocità KERNAL (2350 B a ~390 B/s), poi le due aperture
di file (1,6 s) e le due sfumature della musica (0,5 s). La posizione sul disco conta poco (tracce 11–12, a 6–7 tracce dalla
directory). Il codice dei due moduli non c'entra.

**Come ottimizzare** (stime dell'11/11; 1 e 2 **fatti** il giorno stesso, file `MENU`: sopra):
1. **Un file solo** `INN` con OVLT + OVL2, letto in due pezzi (i primi N byte a `$C900`, il resto a `$F500`): −1 apertura
   e −1 sfumatura ≈ **−1,1 s**. Costo: ~20 B di codice (`load_raw` con un secondo intervallo), `mkdisk.sh`, test VIL-OVL2.
   Quando il precaricamento sovrascrive OVL2 si rilegge tutto il file (oggi solo OVL2): +1,1 s in quel caso.
2. **Comprimere con ZX0** (decompressore già nel gioco): OVLT 1413 → 1117 B, OVL2 937 → 750 B (misurato con `zx0`):
   −480 B ≈ **−1,2 s**. Serve un buffer per il file compresso (la decompressione ZX0 non lavora sul posto in avanti) e il
   tempo di decompressione (~0,05 s, non misurato). Insieme a 1: ~9,2 → ~6,9 s.
3. **Sfumatura più corta o una sola** per caricamenti di fila: −0,2/0,3 s, banale.
4. **Precaricamento in sottofondo** dei moduli della locanda nel villaggio (come il tema del dungeon dopo N caselle):
   prima apertura ~0,15 s se il PG non entra subito. Costo M: il posto di OVL2 è lo stesso del precaricamento del tema
   (oggi si escludono a vicenda) e la priorità fra i due va decisa.
5. **Fast loader** (codice nel drive): trasferimento 5–10 volte più veloce per **tutto** il gioco (piani, temi, salvataggi).
   Costo L e rischio sull'hardware reale (drive compatibili, mai provato: TODO I1).

## Dungeon: analisi dell'11/11 (profilo per routine) e prime ottimizzazioni

**Strumento**: `tools/vice/frame_prof.py --level N --fz F` (VICE, contatore di cicli): una fermata dopo ogni `jsr` di
`main_loop`, cicli di ogni routine a ogni giro (IRQ compresi), camminata in 8 direzioni con teletrasporto vicino ai
mostri (li sveglia), Frenzy con la corsa `fz_run` = F tenuta fissa; 200 giri per misura; godmode. "fps" = 50 / fotogrammi
video per giro (il ciclo è agganciato al vblank: 50, 25, 16,7...).

**Dove va il tempo** (piano 10, camminata, prima delle ottimizzazioni; cicli per giro, media / 95° percentile):

| Routine | media | p95 | Cosa fa |
|---|---|---|---|
| `build_sprites` | 4 029 | 7 987 | sprite (PG, effetto, 5 mostri) **+ `hud_step`/`hud_warn`**: il p95 alto è il ridisegno dei pannelli dell'HUD |
| `maybe_redraw` | 2 465 | 5 563 | scorrimento: preparazione dello schermo nascosto, scambio ogni 8 px; il ridisegno completo `_sync` arriva a ~15 000 |
| `update_monsters` | 2 439 | 5 095 | IA (già a livelli di dettaglio: lontani 1 giro su 16, addormentati fuori raggio 1 su 8, svegli a giri alterni, solo i 4 più vicini si muovono) |
| `update_player` | 1 782 | 2 768 | movimento e collisioni |
| `update_world` | 797 | 4 488 | il picco è `mark_explored` a ogni casella nuova (63 bit uno per volta, ~2,8 mila cicli) |
| `update_bar`, `update_camera`, `apply_frame`, `update_attack`, altri | < 700 | < 3 000 | |

**Ottimizzazioni semplici fatte** (nessun cambiamento visibile; test `PERF-OPT-10/11`, PERF-10..23 ancora verdi):
1. `mark_explored` a maschere: una riga = 1 o 2 byte con una maschera (9 colonne al massimo), ~0,4 mila cicli.
2. HUD a pannelli: un colpo subito ridisegna solo la riga della vita, l'esperienza solo la riga XP, un'abilità di nuovo
   pronta o la fine di Rage/Frenzy/ricarica delle pozioni solo la riga 23 (e la cintura), una pozione bevuta vita + cintura
   (`hud_pend`), invece dei 4 pannelli (`hud_dirty`) per 4 giri. Il passaggio di livello e i casi rari ridisegnano tutto.

| Misura (200 giri) | prima | dopo |
|---|---|---|
| piano 10, camminata: giri lunghi / fps | 19 / 45,6 | **10 / 47,6** |
| piano 12, camminata | 26 / 44,2 | **8 / 48,1** |
| piano 10, Frenzy +100% | 96 / 33,5 | 81 / 35,5 |
| piano 12, Frenzy +100% | 84 / 35,0 | 80 / 35,7 |
| `update_world` p95 (piano 10) | 4 488 | 1 151 |
| `build_sprites` p95 (piano 10) | 7 987 | 4 683 |

**Frenzy: velocità della corsa e fps** (prima delle ottimizzazioni, piani 10 e 12 dove ci sono più mostri; `fz_run` = corsa
in più in %, oggi massimo 100 = 4 px a fotogramma):

| `fz_run` | 0 | 50 | 100 (oggi max) | 150 | 200 | 250 |
|---|---|---|---|---|---|---|
| piano 10: fps (giri lunghi su 199) | 45,6 (19) | 39,5 (52) | 33,5 (96) | 30,7 (122) | 33,2 (100) | 29,6 (136) |
| piano 12 | 44,2 (26) | 41,1 (43) | 35,0 (84) | 30,9 (123) | 29,5 (138) | 27,8 (158) |
| calo rispetto a `fz_run` 0 | — | −8/−13% | −21/−27% | −30/−33% | −27/−33% | −35/−37% |

Il **−50%** (25 fps fissi) non si raggiunge nemmeno a 250 (il massimo di un byte): oltre 150 i giri lunghi si stabilizzano
(~2 fotogrammi l'uno quasi sempre). Il costo della Frenzy è tutto in `maybe_redraw` (lo scorrimento: p95 14 000 a +100%):
lo schermo si scambia ogni 2 fotogrammi e la preparazione non tiene il passo. **Proposta di taratura**: corsa massima
**+50%** (`rules.yaml skills.frenzy.run_max`): ~40 fps (−10% circa) invece di ~34 (−25%). È un cambio di gioco (la Frenzy
corre meno): da decidere (TODO D3).

### Scenari, dal più semplice al refactoring

| # | Scenario | Resa attesa (stima) | Costo | Note |
|---|---|---|---|---|
| 1 | **Fatto**: `mark_explored` a maschere, HUD a pannelli | camminata: giri lunghi da ~10% a ~5% | S | sopra |
| 2 | Taratura della Frenzy (`run_max` 50) | Frenzy da ~34 a ~40 fps | dato | cambia il gioco: decisione |
| 3 | Lavoro a turni: niente `hud_step` nei giri in cui `maybe_redraw` ha già fatto lo scambio o un ridisegno pesante | −1/−2 mila cicli nei giri peggiori | S-M | l'HUD si aggiorna un giro dopo |
| 4 | **Branchi** (proposta del committente): ogni mostro con il suo branco (la stanza in cui nasce); il test "lontano" si fa sul riquadro del branco, i mostri di un branco lontano non si guardano uno per uno; i mostri esistono solo vicino alla finestra o se inseguono | `update_monsters` −0,5/−1 mila cicli (oggi i lontani costano già poco: 1 giro su 16) | M | spawn/despawn per branco tocca il salvataggio del piano (REL) e il bottino dei mostri: rischio alto per poco guadagno oggi |
| 5 | Camera a casella (16 px) solo in Frenzy / combattimento affollato | dimezza i giri persi in Frenzy (prova del 10/11) | M | cambia la resa visiva dello scorrimento |
| 6 | Scorrimento rifatto (preparazione distribuita meglio, ridisegno per colonne/righe invece di `_sync` completo) | Frenzy vicino a 50 fps | L | il cuore del motore grafico |
