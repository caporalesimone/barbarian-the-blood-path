# TODO — lavori aperti (riordinato il 15/11/2026)

Solo ciò che resta da fare. Il fatto, con le decisioni datate, sta nella wiki (`docs/`) e, fino all'08/11, in
[docs/storico-todo.md](docs/storico-todo.md) (archivio, non si aggiorna). Le decisioni nuove si scrivono nella voce a
cui appartengono, con la data; una voce finita si **cancella** e la decisione va nella pagina della wiki interessata.
I lavori della toolchain stanno nel TODO di Lab64 (`TODO.md` del suo repository).

**Riordino del 15/11** (richiesta del committente): voci raggruppate per **categoria** e, dentro ogni categoria, ordinate per
**taglia**. Gli **ID** restano quelli dell'11/11 (`<lettera><numero>`, citati nella wiki e nei commit): la lettera non dice più la
categoria. Tolte le voci fatte o superate: T2 e T3 (passate a Lab64 e fatte il 15/11: tema del manuale, pubblicazione generica), M7 (1570/1571 in VICE:
`KRILL-18` passa), la parte risolta di I11, I9/I10/J10/J13 (sono lavori di Lab64).

**Taglie**: **XS** = minuti o una decisione; **S** = ore; **M** = 1–2 giorni; **L** = più giorni; **XL** = settimane.
Ogni voce: obiettivo, motivazione, cosa serve, cavilli.

Stato di riferimento (15/11, v1.256 su `main`): `SAVE_VER $C7`; smoke + sanity 33 test in ~17 s; hardware reale mai provato.

| # | Categoria | Voci (in ordine di taglia) |
|---|---|---|
| 1 | [Priorità massima](#1--priorità-massima) | A1 |
| 2 | [Decisioni del committente](#2--decisioni-del-committente) | B1–B17 (XS ciascuna) |
| 3 | [Verifiche e misure](#3--verifiche-e-misure) | I2, I3, I4, I5, I6, I8, I7, I11, I1 |
| 4 | [Interfaccia, grafica, audio, testi, manuale](#4--interfaccia-grafica-audio-testi-manuale) | C2, C3, E2, E3, E4, E5, C1, E1, M2, E6, E7, E8, E9 |
| 5 | [Salvataggi](#5--salvataggi-un-solo-save_ver-dove-possibile) | C4, F2, F3, C5, F1 |
| 6 | [Prestazioni e memoria](#6--prestazioni-e-memoria) | D2, D12, D14, D1, D5, D7, D10, D11, D8, D3 |
| 7 | [Loader e disco](#7--loader-e-disco) | M8, M3, M4, M5 |
| 8 | [Frenzy: prove in gioco](#8--frenzy-prove-in-gioco-del-committente) | K1, K2, K3, K6, K5, K4 |
| 9 | [Oggetti, combattimento, bilanciamento](#9--oggetti-combattimento-bilanciamento) | G2, G5, G4, G1, G3, G6, G8, G7 |
| 10 | [Contenuti: capitoli, quest, Abisso, intro, lingue](#10--contenuti-capitoli-quest-abisso-intro-lingue) | H4, M1, H5, M9, H1, H3 |
| 11 | [Build, test e strumenti del gioco](#11--build-test-e-strumenti-del-gioco) | J14, T1 |
| 12 | [Idee per dopo](#12--idee-per-dopo) | J4, J3, J2, J1 |
| Z | [Note urgenti](#z--note-urgenti) | Z3, Z4, Z6 |

---

## 1 — Priorità massima

### A1 Punti statistica: rifiniture e verifiche a mano — **TOP PRIO** — S (verifica) + M (spostamento nel MENU)
- Unito a `main` l'11/11 (schermata C in `src/game/charsheet.asm`, `docs/interfaccia.md`, `docs/quests.md`).
- **Glifo dell'HUD da confermare** (decisione 11/11): oggi la **freccia verde in su** (`LVUP`, colore 5). Le 20 proposte restano
  in `lab/concept/hud_glyphs/hud_glyphs.png` (+ `glyphs.json`, `make_sheet.py`): il committente deve scegliere il migliore.
- **Menu**: la schermata C va **riportata alla stessa logica dei menu del villaggio** (modulo MENU, `$01 = $35`, tabella dei
  salti). Ostacolo: costa ~1 KB e le zone del MENU hanno liberi solo 272 B (170/9/93): serve una zona nuova o più spazio (D14).
  Nel dungeon il MENU potrebbe non essere in memoria (si carica all'ingresso nel villaggio). Finché non si decide resta in GAME.
- **Da verificare a mano** (VICE o hardware): aprire C nel villaggio e nel dungeon (anche con mostri vicini), spendere,
  togliere, spostare fra le caratteristiche, undo, confirm (sì/no), uscita con punti in attesa (sì/no), respec con e senza gettoni,
  ricaricare la partita, CON alzata = vita massima alzata (schermata rifatta il 15/11, Z5: `docs/interfaccia.md`).
- **Decisioni da confermare** (B12, prese da me l'11/11): (a) **1 punto ogni 2 livelli** (9 al livello 20); (b) vita
  **retroattiva** su COS; ~~(c) all'uscita i punti in attesa si **confermano**~~ **superata il 15/11 dalla richiesta del
  committente (Z5)**: nulla si spende senza conferma esplicita; "confirm" chiede "spend N points for good?", RUN/STOP con
  punti in attesa chiede "spend N points before leaving?" (no = si esce e i punti tornano da spendere); (d) Fire su una
  caratteristica = +1; (e) nessun tetto. Da confermare (15/11, mie): il "no" all'uscita esce comunque (non torna alla
  schermata); la sola voce respec senza punti (cs_mode 1).
- **Resta**: aggiornare il manuale (pagina dei tasti e dell'HUD) e la tabella delle caratteristiche in `docs/combattimento.md`.

---

## 2 — Decisioni del committente

Nessuna di queste è codice: sono scelte (taglia **XS** ciascuna per chi decide). Finché restano aperte, le voci che le citano
non si possono chiudere.

| ID | Decisione | Blocca |
|---|---|---|
| B1 (ex D2) | **Merce dei negozi**: cosa e quanti oggetti vende ciascuno a ogni ingresso (oggi `balance.yaml`: fabbro 6 da armi+armature+scudi, alchimista 4 da pozioni+pergamena+anello; massimo 8). | E2 |
| B2 (ex D4) | **Cintura a 8 posti**: quale quest la sblocca (da scegliere col simulatore). | F1 |
| B3 (ex D5) | **Pergamene fuori dallo zaino**: contatore 0..10 addosso (tasto 5), pile da 10 nel baule della locanda, opzione "riga dell'oro nella locanda con `s N`". Cooldown della pergamena ≥ 5 s (08/11). | F2 |
| B4 (ex D6) | **Anelli e nomi**: formato `ring +N <stat>` e quali nomi accorciare (candidati: leather armor, greater healing, healing potion, minor healing, portal scroll, tower shield, viking sword). | E1 |
| B5 (ex D8) | **Tavolozza di PRESS SPACE**: A sangue (oggi) / B oro antico / C acciaio. | C3 |
| B6 (ex D9) | **Una pergamena garantita per piano?** | G1 |
| B7 (ex D10) | **Prezzi proporzionali al guadagno** (`docs/BILANCIAMENTO.md` sez. 12). | G2 |
| B8 (ex D11) | **Quest system** (`docs/quests.md` sez. 5 e 11): villaggi, numero delle quest, pergamena, Torvald, generatori, lore, manuale su disco. | H1 |
| B9 (ex D14) | **Borsello a gradini**: valori (es. 500 / 1000 / 3000 / 5000, 10 000 al boss finale) e quali tre quest. | H1 |
| B10 (ex D12) | **Abisso**: ripopolamento, prezzi della città, tetto dell'oro oltre i 16 bit. | H3 |
| B11 (D-CAP-1..5, 11/11) | **Capitoli** (`docs/capitoli.md`): quanti (i piani sono **5 per capitolo**: `data/chapters.yaml` 5, 5, 5, 5 + Abisso 235 = profondità 255; piano locale da 1 in ogni capitolo, profondità globale per la difficoltà, `docs/quests.md` 3.8); dove vanno Demon e Balrog (oggi da profondità 8–9: fuori dal capitolo 1 di 5 piani); ritorno ai villaggi precedenti; piani dell'Abisso salvati (anello di K record) o rigenerati; mappe fisse nell'Abisso; difficoltà oltre la profondità 32 e oltre 255. | M9, H3 |
| B12 (11/11) | **Punti statistica**: conferma delle scelte di A1 (punti per livello, vita retroattiva; l'uscita che confermava in silenzio è stata cambiata il 15/11 dalla richiesta del committente, Z5: ora chiede). | A1 |
| B13 (11/11) | **Frenzy**: corsa massima +50% (≈40 fps fra i mostri) invece di +100% (≈34 fps)? Misure in `docs/prestazioni.md`. Si decide dopo le prove della categoria 8. | D3, K |
| B15 (11/11) | **Salvataggi con Krill più lenti** ([docs/FastLoader.md](docs/FastLoader.md) sez. 7): "save game" 3,2–5,4 → 7,1–8,6 s, locanda 3,1 → 8,5 s, scale fra piani 10–11 s (il piano lasciato si salva). Causa: il plugin riscrive il file dell'eroe intero (9 blocchi) dopo averlo letto, più la ricarica del plugin (si modifica da solo) e del villaggio. Da decidere: accettare; file più piccoli (un file per piano: più file sul disco, scelta contraria del committente); immagine del file sempre in RAM (niente lettura, ~2 KB); non salvare i piani alle scale ma solo con l'eroe. | M4, M8 |
| B16 (11/11) | **A fine gioco: build con immagini disco diverse per drive?** Oggi solo 1541 (`_1541` nel nome). Krill supporta anche 1570/71, 1581, CMD FD, 1541U; SD2IEC solo con il ripiego KERNAL. Con tutti i drive l'install passa da 3225 a 6997 B e il plugin non si costruisce senza cambiare `save.s`. | I1, M5 |
| B17 (15/11) | **A fine sviluppo: trucchi nella release? quali e come?** Oggi il menu **cheats** (RUN/STOP, `src/game/cheats.asm`, [docs/cheats.md](docs/cheats.md)) c'e' nelle build di debug e di test (`CHEATS=1`) e **non** nella release (`CHEATS=0`, 0 B). **Da decidere a fine sviluppo** (non prima: dipende da quanto serve provare il gioco e dalla memoria libera). **Opzioni**: **(a) nessuno** (oggi): release identica a prima dei trucchi, nessuna sorpresa; si perde la comodita' per chi prova la release e per i giocatori in difficolta'. **(b) menu nascosto dietro un codice** digitato al titolo o una sequenza di tasti/joystick (stile Konami): chi lo sa lo accende, gli altri non lo vedono; costa codice in piu' (lettura del codice) oltre ai 395 B del menu e serve decidere se il codice e' per sessione o si ricorda (byte da salvare, **SAVE_VER**). **(c) solo alcuni** (es. god mode e salto di capitolo, senza level up e gettoni): meno byte e meno modi di rovinare il bilanciamento, ma `cheats.asm` va diviso con `.if` per voce (oggi solo `CHEATS` 0/1). **(d) oggetti o oggetti speciali** (anello, pergamena, uscita dal gioco con un bottino particolare) invece del menu: dentro il mondo di gioco, ma toccano formato oggetti e bilanciamento. **(e) segno "barato"** sull'eroe o nella sala della fama (bit nel blocco dell'eroe, **SAVE_VER** nuovo, `docs/FORMATO_DATI.md`): onesto verso i punteggi, serve in qualunque opzione con trucchi in release; con l'opzione (a) non serve. **Cavilli**: (1) **memoria in release**: 395 B di GAME (nella build di debug il margine del codice scende da 2397 a 2002 B); la release ha oggi lo stesso margine di prima, da rimisurare (`lab64 run tools/build/asm.sh release-game`, test `CHEAT-22`, che oggi **vieta** i trucchi nella release e va cambiato se si decide di tenerli); (2) il flag **`CHEATS`** (`tools/build/asm.sh`, `lab64.env`): con trucchi in release va scelta la variante (`CHEATS=1 RELEASE=1` o un flag nuovo), con il manuale e gli screenshot sempre a `CHEATS=0`; (3) **i salvataggi fatti con i trucchi** oggi sono eroi normali **senza segno**: se si adotta (e) quelli vecchi restano senza; (4) i trucchi aggirano la progressione (capitoli, boss, `c_unl`): vanno provati con **`next chapter` dai piani 2-3** (non verificato; il blocco entrando nei villaggi, ex A2, era un difetto del loader, corretto il 15/11: [FastLoader](docs/FastLoader.md) 4.1); (5) il manuale e l'help non parlano di trucchi: se restano in release vanno scritti o taciuti apposta. | H1, E6 |

---

## 3 — Verifiche e misure

Nessun codice nuovo (salvo una correzione se la verifica trova un errore).

- **I2** — S. Verifica a mano dal disco di release (`docs/manual-tests.md`, 10 minuti).
- **I3** — S. Test manuale 019 (locanda): spostare un oggetto, spegnere senza RUN/STOP, riaccendere.
- **I4** — S. B2 minimappa corrotta nel dungeon (05/11, mai riprodotto): servono screenshot e passi.
- **I5** — S. RUN/STOP fantasma nelle build NOKEYS in VICE (solo strumenti di test).
- **I6** — S. Glitch del brano del villaggio (hard restart): da riascoltare.
- **I8** — S. (13/11) Segnalazioni al team dell'emulatore da riprovare a ogni nuova build: `runLoop` non esatto con un caricamento
  da disco dentro il ciclo (`framesActual` 490 su 480 nel passo del portale, `docs/emulatore.md`); il pacchetto dichiara quel caso
  non verificato.
- **I7** — S. (13/11) Licenze **prima di pubblicare il repository**: Krill (BSD-3 con attribuzione), zx0 (BSD-3), file nelle loro
  cartelle del gioco. Le licenze dei componenti di Lab64 (vc64web, ROM Commodore in git, `open-roms`) sono nel TODO di Lab64.
- **I11** — S-M. **Il monitor remoto di VICE smette di rispondere a metà sessione** (13/11, due volte in `./build.sh --release`:
  PERF-DISK-10..14 con `monitor: no answer to 'load ...' in 20 s`, PERF-OPT-11 `MonitorError` dopo 30 s; rilanciati da soli: PASS).
  La parte "primo avvio a freddo" è stata corretta il 14/11 (`wait_boot` in Lab64, vedi `docs/test.md`). **Da fare** quando si
  ripresenta: registrare il log di VICE e del monitor; capire se dipende dalla macchina (riavvii, disco lento sotto il guest).
- **I1** — L. Hardware reale (mai provato): avvio, Krill's Loader (caricamenti e salvataggi) su 1541 vera e su 1570/1571 (in VICE
  passano: `KRILL-17`, `KRILL-18`), `quit the game` (reset), OVL2 sotto il KERNAL, TOD senza 9 V AC, tempi di loader, LORE e
  ritorno al menu. Serve l'hardware del committente.

---

## 4 — Interfaccia, grafica, audio, testi, manuale

### C2 (ex 1.3) Portale della leva "nero" — S
- Il portale per l'Abisso (sala del trono) ha i colori del portale normale: palette scura. `gen_gfx.py` + atlante.

### C3 (ex 1.4) Piccole scelte estetiche e audio — S
- Tavolozza di PRESS SPACE (B5); `SFX_LOWHP` provvisorio da riascoltare nel JUKEBOX; tile del trono dietro il boss.

### E2 (ex 2.3) Negozi: merce (dopo B1) — S
- Assortimento in `balance.yaml` (pool e `stock`), `docs/villaggio.md`, manuale.

### E3 (ex 2.4) Musica nel menu principale senza glitch — S
- Un brano del player del gioco avviato dal menu stesso (`src/lobby.asm`, un `SNDn`), `docs/musica.md`; `snd_io` prima del disco.

### E4 (ex 2.5) Musica nell'help (Tavern of Dawn) — S
- Programma HELP (release) con il brano del villaggio: player condiviso, un `SNDn` sul disco di release.

### E5 (ex 2.6) HUD: esperienza a 24 bit (per l'Abisso) — S
- Oltre 65535 xp: 3 cifre + K, barra a 24 bit (~100–130 B). Dipende dalle soglie oltre il 20 (H3).

### C1 (ex 1.2) Grafica della cintura nell'HUD: ampolle colorate — S-M
- Ampolle nei colori della pozione (rossa 2, gialla 7, viola 4) al posto dell'icona generica; in ricarica blu (già fatto).
  **Cavilli**: caratteri hires, colori < 8; i codici liberi dell'HUD sono finiti (`HUD_FREE`); da ripensare con la cintura a 8 (F1).

### E1 (ex 2.2) Anelli `ring +N <stat>` e nomi corti (dopo B4) — S-M
- Nomi in `data/items/items.tsv`, `NAME_SHOW`, `docs/oggetti.md`, help, manuale. Gli id non cambiano: nessun `SAVE_VER`.
  **Cavillo**: la rarità del materiale va spiegata altrove.

### M2 Temi audio veri dei villaggi — S-M
- Brano per capitolo fatto il 12/11 ([musica](docs/musica.md)). **Resta**: scegliere i temi dei villaggi 2–4 (oggi tutti Tavern
  of Dawn) ed eventualmente i temi dei boss dei capitoli (oggi il piano del boss usa il tema del capitolo).

### E6 (ex 2.8) Revisione completa del manuale e dell'help prima della prossima release — M
- Rilettura di `docs/manual/manuale_src.html`, `data/help.txt` (`gen_help.py --snap` se cambia l'HUD), screenshot
  (`tools/vice/shots_manual.sh`); impaginazione (pagine mezze vuote dopo il 09/11); figura della morte in pagina 7.
- (15/11) Il generatore (Lab64) segnala le pagine che traboccano; in `--release` e' un errore (`lab64 manual --strict`).

### E7 (11/11) Manuale in inglese, oltre all'italiano — M
- `tools/manual/gen_manual.py --lang en` è pronto (sorgente `docs/manual/manual_src_en.html`, PDF
  `Barbarian_Blood_Path_Manual_EN.pdf`; le parti generate hanno già le parole nelle due lingue; dal 15/11 la build fa da sola tutti
  i manuali che hanno il sorgente e li pubblica): **manca il sorgente
  inglese** (traduzione di `manuale_src.html`, stesso impaginato e stessi segnaposto). Prima di una release pubblica; poi
  `tools/build/release.sh` produce i due PDF e il test `BUILD-04` controlla anche quello inglese. Legato a H5.

### E8 (ex 2.9) Player audio unico per la release — M
- Il `JUKEBOX` è già sul disco; **va rifatto esteticamente** (standard dei menu: titolo, riquadri, elenchi brani/effetti)
  diventando il music player della release. Un solo player per tutti i programmi; tabella di brani ed effetti generata in build
  (decisione del 09/11: niente lettura della directory); effetti letti una volta all'avvio; due elenchi (canzoni, effetti),
  play/pausa/stop, filtri. Dettagli: storico in git (`TODO.md` fino a `22388f9`, voce 2.9).

### E9 (ex 2.10) Stringhe del gioco in un file unico, traducibili (decisione dell'11/11) — M-L
- `data/strings.yaml` → `tools/gen_strings.py` → un `.inc` per PRG; classi di UI con lunghezza massima (`screen` 38,
  `title` ~34, `box36/26/20`, `hint` 38, `bar`, `hud`, `item` 16, `io` ~22, `ask`, `num`); sezione **Stringhe**
  dell'atlante; sostituzione nel codice file per file con confronto **byte per byte** dei PRG; test con stringhe "lunghe".
  Censimento: 289 letterali (~3,1 KB, approssimato). Prepara H5. Dettagli: storico in git (voce 2.10).

---

## 5 — Salvataggi (un solo `SAVE_VER` dove possibile)

Le voci che cambiano il blocco eroe (C5, F1–F3, G4) vanno fatte insieme per cambiare `SAVE_VER` una volta sola.

### C4 (ex 1.6) Salvataggio senza controllo degli errori di disco — S-M
- `gm_save` (`sv_all`), `chap_save`, `save_char` non controllano `KREADST` né il canale errori della 1541 (lettura del codice, **non
  verificato** con disco pieno/protetto): l'eroe può perdere i progressi senza saperlo. **Obiettivo**: avviso solo in caso
  di errore ("disk error: not saved"). **Serve**: lettura del canale 15 dopo `rel_wclose` (~30–50 B, non misurati),
  avviso nello standard dei menu, test con disco protetto (`tests/regression/saves`).

### F2 (ex 3.2) Pergamene fuori dallo zaino (dopo B3) — M
- Contatore 0..10 nell'eroe, icona col numero nel purse e nell'HUD, pile da 10 nel baule; cooldown ≥ 5 s.

### F3 (ex 3.3) Campi per quest e Abisso nell'eroe — M
- Stato quest (8 B), modalità normal/nightmare + eroe morto (1 B): tutti in un colpo (`c_chap` c'è dal 12/11).

### C5 (ex 1.8) CRC sui salvataggi — M
- Controllo di integrità (CRC-8/16 o somma) per eroe, piani, baule, verificato al caricamento; un record corrotto si
  riconosce. Cambia il formato (**`SAVE_VER`**): ~30–60 B di codice, tempo da misurare sul salvataggio. Test con file corrotto
  (`test_rel.py`, `test_saves.py`).

### F1 (ex 3.1) Cintura a 8 posti sbloccata da una quest (dopo B2) — L
- `c_beltt` 8 byte, 4 slot da 2 pozioni, tasti 1–4; flag nell'eroe. Regole decise l'08/11 (prima fila, la seconda sale,
  allineamento all'uscita dei menu; pozioni dal baule del dungeon come dall'alchimista). Quest scelta col simulatore.
  **Serve**: formato, HUD (due file da 4), purse, alchimista, baule, `give_item`, simulatore, eroe di prova con 8 pozioni,
  test `BELT-20..` (`BELT_SLOTS`, `BELT_KEYS` in `tests/lib/play.py`). Dettagli: storico in git (voce 3.1).

---

## 6 — Prestazioni e memoria

Misure e soglie: `tests/regression/perf` (PERF-10..23), [docs/prestazioni.md](docs/prestazioni.md). Ogni intervento si
misura prima e dopo con `lab64 test regression -k PERF`. D1–D5 sono le osservazioni P1–P5 di
[docs/ottimizzazione.md](docs/ottimizzazione.md) non ancora fatte: **suggerite da fare**.

### D2 (ex P2) Minimappa del villaggio 0,64 s — S
- Disegno a quadranti 2×2 (`mm_quad`) per tutte le 48×48 caselle: tabella dei caratteri o solo le righe cambiate.
  **Stima**: 0,3–0,5 s in meno (non misurata).

### D12 (11/11) Dall'analisi dell'assembly generato (`out/work/asm_audit/analisi_assembly.md`) — S
- **Suggeriti**: routine per la casella del mostro (`mxl/mxh → pix2tile` e `myl/myh`, 4 copie ciascuno: ~46 B) e per i
  puntatori della grafica (`GFX_FSTRIP`, 4 copie: ~38 B); le altre ripetizioni sono da 8–15 B (~145 B in tutto, valutare una
  per una); START e LORE: escludere con `.if` il codice dell'altra variante (~155 B e ~180 B: solo tempo di caricamento).
  Rifare l'analisi dopo ogni lavoro grosso: `lab64 run python3 tools/build/asm_audit.py` (test `ASM-10/11`).

### D14 (11/11) Spazio del modulo MENU — S (per ogni zona nuova)
- **Stato** (v1.223, [prestazioni](docs/prestazioni.md#menu-del-villaggio-modulo-menu-residente-1111-v122x)): locanda e
  negozi nel modulo MENU, tre zone (zona 1 `$C900-$CFFF` 170 B liberi, zona 2 `$F4E0-$FCFF` 9 B, zona 3 `$A700-$A7FF`
  93 B). Ogni modifica a locanda e negozi deve starci: per crescere, altre zone (slot sprite 20–23 `$A500-$A5FF`, 256 B;
  coda degli slot 41–47 e 58–63 dopo i buffer della musica) o codice più corto (`asm_audit`).
- **Attenzione** per D8 (`OVLF` a `$C900`) e per il buffer delle quest (`docs/quests.md`, `$CD00`): `$C900-$CFFF` ora è
  la zona 1 del MENU, che resta per tutta la partita.

### D1 (ex P1) Primo ingresso nel piano 1 dal villaggio ~12 s in VICE (poi 5,6–7,3 s fra i piani) — S (misura) + ?
- Misurare cosa si legge (tema, brano, piano) col cronometro; il precaricamento del tema parte dopo N caselle e forse non
  finisce prima della cripta. Legato a J1 (prefetch nuovo). La taglia del rimedio dipende dalla misura.

### D5 (ex P5) Piani pesanti: piano 14 al 14,5% di fotogrammi persi camminando (PERF-21), piano 15 al 3,8% — M
- Più mostri svegli: stesso lavoro di D3.

### D7 (ex 6.1) Spawn dei mostri nella RAM sotto l'I/O — M
- `spawn_monsters`/`place_monster`/`place_boss`/`floor_types` (~600–800 B, da misurare) accanto al generatore
  (`gen_io.asm`). Attenzione a `gen_rammap.py`, arena, `test_gen.py`.

### D10 (ex 6.4) Altri interventi misurati — M
- `SCR_H` da `$8400` a `$8800` (+224 B); musica sotto il KERNAL (0,8–1,3 KB); codice solo-villaggio su file; variabili sparse (~60 B).

### D11 (ex 6.5) Compressione ZX0 dei file rimasti — M
- MENU, GFX0, temi: ~5 s in meno all'avvio (stima). Decompressore pronto (`src/common/zx0.inc`).

### D8 (ex 6.2) Codice del piano finale in overlay (`OVLF` a `$C900`) — M-L
- `gen_final` + tabelle, `ui_lever`, `at_lever`, parte di `place_boss`, `final_tick`: ~1 KB di GAME. Ospiterà Torvald (H1).
  Conflitto con la zona 1 del MENU (D14).

### D3 (ex P3, ex 1.9) Frenzy e analisi del dungeon — L
- **11/11**: profilo per routine (`tools/vice/frame_prof.py`), ottimizzazioni semplici fatte, velocità della Frenzy provate fino a
  +250%: il −50% di fps non si raggiunge; a +100% (oggi) −21/−27%. Tabelle e scenari in
  [docs/prestazioni.md](docs/prestazioni.md) ("Dungeon: analisi dell'11/11").
- **Da decidere (B13)**. **Da fare**, in ordine: lavoro a turni (K5, S-M); camera a casella in Frenzy (K4, M); branchi di
  mostri (M, poco guadagno oggi); scorrimento rifatto (L). Catena degli IRQ fragile (sez. 3.4).

---

## 7 — Loader e disco

### M8 Cosa reintrodurre del fast loader (ex D15) — S (decisione) + ?
- Krill's Loader è nel gioco ([docs/FastLoader.md](docs/FastLoader.md)). Cache e precaricamento sono stati tolti prima: **da
  decidere con il committente quali reintrodurre** guardando le misure (villaggio → piano 1 3,1 s, modulo MENU 2,3 s, tema ~1 s):
  oggi nessuna sembra necessaria per i caricamenti; i salvataggi sono il problema (B15). Da provare su hardware reale (I1).

### M3 Prestazioni dei caricamenti (ex J9) — M
- **Stato (12/11 sera, VICE, 42 file sul disco)**: scale nello stesso capitolo **2,24 s** (`PERF-DISK-13`; obiettivo del
  committente < 2 s), ingresso completo nel villaggio 4,8-4,9 s (`PERF-DISK-14`), tema `GFXn` 1,34 s, save nel dungeon
  8,3-9,3 s, save nel villaggio 9,45 s (soglia 9,5 s). Limiti in `tests/regression/perf_disk` (quelli del committente portati a
  misura + 0,1 su sua indicazione: scale 4,0, save 9,4 / 9,6 s). `load_char` 2,84–3,04 s (limite del test 3,4 s).
- **Da capire**: (1) i tempi crescono con il numero di file sul disco (30 → 36 → 42 file: tema 0,98 → 1,34 s, menu 1,96 →
  2,98 s) e non in modo monotono (prove con 32/33 file); (2) lo stesso test varia fra un run e l'altro (save nel dungeon
  8,26-9,26 s) secondo la posizione della testina lasciata dal test prima. Sospetti: ricerca nella directory di Krill e
  posizione dei settori (non verificato). **Provato e scartato**: file usati spesso vicino alla traccia 18 (`cc1541 -r 16`).
- **Leve per le scale < 2 s** (non provate): non rileggere il tema `GFX(2c−1)` se non cambia (stima ~0,9 s; ma la regola del
  committente è "nessuna cache se i limiti reggono"); un solo file per tema + brano; meno file sul disco (es. un solo file
  per i 4 villaggi segnaposto finché sono uguali).
- (12/11, committente) **Test di prestazioni con tutti i file già sul disco** (villaggi, mappe dei boss, bestiari, temi previsti a
  fine lavoro, anche segnaposto): le misure di oggi sono ottimistiche. **Da chiarire con il committente** se intendeva questo o
  solo "il disco di oggi, tutti i file presenti" (come già `PERF-DISK`).
- (12/11, committente) **Testina del drive posizionata in anticipo**: valutazione iniziale **non misurata**: il vantaggio è solo il
  tempo di passo della testina; servirebbe un "vai alla traccia N" nel residente di Krill (da leggere in `loader/`) o la lettura
  di un blocco del file successivo; il prossimo file non sempre si sa. **Passo 0**: misurare in VICE la partenza da una traccia
  lontana e vicina; se il guadagno è piccolo si lascia. **Se il costo è troppo alto si fissa un valore massimo come guardia**.
- Profilo del cambio piano (12/11, 2,64 s): fade 0,18 s, tema 1,17 s, brano 0,78 s, generazione 0,29 s, resto ~0,2 s.

### M4 Plugin di save di Krill ottimizzato (ex J5) — M (passi 0–2) / XL (passo 3)
- (11/11, committente) **Reverse engineering del plugin di save di Krill** e una versione con la **scrittura ottimizzata**.
  Misurato: ~3,8 s fissi per chiamata + ~0,25 s per blocco. Dal sorgente (`loader/src/save.s`, `customdrivecode.s`): a ogni
  chiamata `swapdrvcod` salva nel buffer da 2 KB del C64 il codice del loader che sta nel drive, carica il codice di scrittura,
  scrive, poi rimette il codice del loader; il nome del file viene scritto dentro il plugin stesso. Peso delle fasi **non misurato**.
- Piano: (0) profilo delle fasi in VICE, ~2-3 ore; (1) plugin che non si modifica / si ripristina da solo: niente ricarica di
  `KSAVE`, −0,5 s, ~mezza giornata; (2) più file in una sola sessione del drive o scrittura dei soli blocchi cambiati, ~2-4 giorni;
  (3) scrittura dentro il codice residente del drive senza scambio: settimane, alto rischio. Implica una versione modificata di
  Krill (patch applicata dalla build, `tools/build/krill_build.sh`; licenza BSD con la modifica dichiarata), codice del drive con
  tempi critici provato solo in VICE (I1), aggiornamenti di Krill da riportare a mano.

### M5 Altri passi del fast loader (ex J6, parte rimasta) — M / L
- **GAME con il decompressore di Krill** (`loadcompd`): nuova build di Krill con il decompressore. M.
- **Ripiego KERNAL** per i drive non supportati (con B16): oggi un drive non supportato dà il messaggio di `kr_fail`. M.
- **`BARBARIAN` con Krill** (install in BARBARIAN, tastiera senza KERNAL: il residente occupa le variabili del KERNAL in
  pagina 2; trampoline su `loadraw`): accelererebbe la lettura di `START` e di `HELP`. L.
- (12/11, committente: **scartati** IRQ solo-suono durante i caricamenti e fade più corti.)

---

## 8 — Frenzy: prove in gioco del committente

Il committente prova in gioco le proposte e poi decide (B13). Misure di partenza ([prestazioni](docs/prestazioni.md),
"Dungeon: analisi dell'11/11"): fra i mostri ai piani 10–12 la camminata normale fa ~45–48 fps; la Frenzy a +50% ~40,
a +100% (oggi) ~34, a +150% ~31, a +250% ~28–30. Il costo è lo **scorrimento** (`maybe_redraw`): lo schermo si scambia ogni
8 px, cioè ogni 2 fotogrammi a +100%. Disco di prova (su richiesta, uno per proposta, branch `feature/frenzy-*` con versione
`tag.N`): eroe di prova al livello 15, piano 10 o 12, godmode, mostri svegli; oppure gioco normale con i valori di `rules.yaml`.

### K1 Corsa massima più bassa (solo dati) — XS
- `rules.yaml skills.frenzy.run_max`: dischi con **50**, **75** e **100** (oggi). Guardare: fluidità, sprite che "saltano",
  sensazione di velocità.

### K2 Crescita più lenta della corsa (solo dati) — XS
- `run_first` 25 / `run_step` 15 (oggi): con 15/10 il massimo arriva più tardi. Disco con 15/10 e `run_max` 100.

### K3 Durata della Frenzy (solo dati) — XS
- `duration` 250 fotogrammi (5 s): con 200 (4 s) il tempo passato a scorrere veloce cala del 20%.

### K6 Combinazioni da provare per ultime — XS
- K1 (75) + K5; K1 (100) + K4. Esito delle prove: annotarlo qui con la data, poi decisione in B13 e voce chiusa.

### K5 Lavoro a turni nei giri pesanti (codice; utile anche senza Frenzy) — S-M
- Niente ridisegno dell'HUD nei giri in cui lo scorrimento ha appena scambiato lo schermo o ridisegnato tutto: l'HUD si
  aggiorna un giro dopo. Guadagno stimato 1–2 mila cicli nei giri peggiori. Disco di prova da confrontare con quello di oggi.

### K4 Camera a casella durante la Frenzy (codice) — M
- Durante la Frenzy la camera si muove a passi di 16 px invece che a pixel: lo scorrimento lavora molto meno (prova del 10/11:
  dimezza i giri persi). La vista "scatta": va vista in gioco. Disco di prova dopo il via del committente.

---

## 9 — Oggetti, combattimento, bilanciamento

### G2 (ex 4.2) Economia: prezzi, oro, riparazioni (dopo B7) — M

### G5 (ex 4.5) Set di oggetti unici con nome — M
- Come `unique_itemdat.tsv` di DevilutionX: una tabella nel database degli oggetti; ~8 B a set + 40–60 B di codice.

### G4 (ex 4.4) Armi casuali (seed per oggetto) — M
- Seed per oggetto (+1 B a oggetto) e funzione seed → statistiche uguale in 6502 e Python. Cambia `SAVE_VER` (categoria 5).

### G1 (ex 4.1) Obiettivi e curva (iterazione successiva del simulatore) — M
- Gruppo base, boss del piano ~75%, boss finale 60–70%; curva del PG più regolare; stordimento; Battle Cry 1 contro 1;
  set delle armi. `tools/simulators/fit_rules.py`, `cmp_rules.py`, `chapters.py`, arena. Rifare dopo F1 e A1.

### G3 (ex 4.3) Probabilità di uscita per ogni oggetto (stile Diablo) — M
- `w = R × g(livello area − livello oggetto)`; colonna `dropRate` in `data/items/items.tsv` come in DevilutionX
  (`itemdat.tsv`). Generatore, simulatore, `docs/bottino.md`. Prerequisito per gli oggetti dell'Abisso (H3).

### G6 (ex 4.6) Arena fase 2 — M-L
- Bot che si muove, posizioni di partenza, strategie; confronto arena / simulatore. Prerequisito per H3.

### G8 (11/11) Database degli oggetti: prossimi passi — M-L
- `data/items/items.tsv` è la sorgente di verità. Da valutare: affissi magici (prefissi/suffissi come
  `item_prefixes.tsv`/`item_suffixes.tsv` di DevilutionX) al posto del solo +N; oggetti unici (G5); requisiti
  (FOR/DES minime, colonne `minStrength`/`minDexterity`), utili con i punti statistica (A1).

### G7 (11/11) Combattere con due armi (dual wield), regole alla Diablo — M-L
- **Obiettivo**: due armi a una mano (niente scudo), come il Barbaro di Diablo 2. **Serve**: (a) **codice**: colonna `hands`
  nel database, posto "mano sinistra" che oggi è lo scudo (`c_eq+2`), `recalc_stats` (in Diablo 2 i colpi si alternano e la
  velocità è la media; nessun bonus fisso), inventario e locanda (con due armi niente scudo, un'arma a due mani esclude tutto),
  usura delle due armi, HUD; (b) **bilanciamento**: simulatore (`Hero` con due armi), arena, confronto con arma + scudo e con
  arma a due mani. **Cavilli**: formato dell'eroe (flag) → `SAVE_VER`; memoria (~100–200 B, non stimata a fondo).

---

## 10 — Contenuti: capitoli, quest, Abisso, intro, lingue

### H4 (ex 5.3) Intro (LORE) da rivedere tutta (a fine quest) — M
- Trama nuova (niente "20 piani", più città, niente cifre del bilanciamento), immagini con sprite e tile aggiornati,
  possibilmente lette dai file del gioco.
- (12/11, committente) **Riscrivere la storia in funzione dei capitoli** (4 villaggi + Abisso, 5 piani per capitolo,
  `docs/capitoli.md`): oggi il testo parla ancora di "twenty floors" (`data/lore.txt`).
- (12/11, committente) **Scorrimento**: la velocità va bene. **Interlinee**: sempre **una riga vuota** fra un elemento e
  l'altro; **due righe vuote** dove oggi ce n'è già una (`@gap 1`). Con le interlinee in più **accelerare di circa il 4%**.
  Nota tecnica (non verificata): `LR_SPEED` = 6 fotogrammi per pixel, intero; il 4% si ottiene a schema, p.es. 6-6-6-5
  fotogrammi ogni 4 pixel (−4,2%). Si tocca `src/lore/scroll.asm` e `data/lore.txt` (`tools/build/gen_lore.py`), poi test
  `LORE` e `docs/intro.md`.

### M1 Sequenza dei capitoli: cosa resta ([capitoli](docs/capitoli.md)) — L
- **Effetto grafico del passaggio** di capitolo (oggi: schermo nero, poi le schermate di salvataggio e caricamento): tbd.
- **Villaggi** (15/11, fatto sul branch `villaggi`, da rivedere con il committente: [villaggio](docs/villaggio.md)): i capitoli
  2–4 e la città dell'Abisso (prototipo) hanno tile, mappa, colori e posizioni propri (file `TWNc` con intestazione). **Resta**:
  la revisione del committente (i quattro villaggi sono prototipi; la proposta scartata è in `lab/villaggi/proposta-a-temi/`);
  NPC; un **brano per villaggio** (oggi lo stesso, M2); la **minimappa** dei villaggi nuovi (i colori "acqua" e "strade" seguono
  i ruoli dei posti: nel villaggio 4 il cratere esce blu); l'etichetta dell'ingresso del sotterraneo ("stairs down to level N"
  per tutti: una per villaggio costa una stringa nell'intestazione); prova su **vc64web** e su hardware reale; il passaggio di
  capitolo legge il file del villaggio nuovo due volte (tempo non misurato); la posizione dei villaggi sul disco è decisa e misurata
  (15/11, disposizione `hubchap`, soglie per villaggio: [FastLoader](docs/FastLoader.md) 7.1); la **città dell'Abisso** oggi si raggiunge
  dall'uscita del villaggio 4 dopo il boss finale e la Bocca non fa nulla (da rifare con H3; la leva della sala del trono resta).
- **Fan art della mappa del mondo** (15/11): `tools/art/world_map.py` (`out/work/art/world_map.png`); dal 16/11 sta nel
  **manuale italiano** (pagina "IL MONDO", prima del capitolo 4; la genera la build del manuale, non e' in git). Restano da decidere
  la wiki e la scatola, e se la geografia (4 zone + Abisso sotto il cratere) va bene; il testo del manuale non racconta la trama
  (in revisione): da rivedere con E6, e da tradurre con E7.
- **Mappe vere dei boss** (`data/maps/bosschapN.txt`) e **boss veri**: dal 15/11 i boss dei capitoli 1–3 hanno il loro **sprite**
  e il loro colore; **meccaniche decise** ([bestiario](docs/bestiario.md#meccaniche-dei-boss-di-capitolo-decise-il-1511)) ma
  non nel codice (~550 B stimati: M9); dal 15/11 hanno anche il **loro nome** nella barra e i **mostri del capitolo** intorno
  (solo grafica, colore e nome: M9); statistiche proprie, bottino speciale, sala che si chiude: da fare.
- **Ritorno ai villaggi precedenti** (portale/menu): fuori da questa fase (D-CAP-2).
- **Tile di accesso al dungeon generico**: la cripta (`T_TSTAIRS`) è già un tile da mettere dove si vuole; più ingressi con
  destinazioni diverse richiederebbero una tabella (utilità da confermare).
- (12/11, committente) **Confermato**: un tema grafico dei livelli per capitolo (`GFX1..8`) va bene così.

### H5 (ex 5.4) Due build: inglese e italiano (dopo H4) — L
- Intro e testi delle quest nelle due lingue con gli stessi limiti di buffer e disco; con E7 (manuale) ed E9 (stringhe).

### M9 Capitoli nel codice e bestiari (ex H2, H6) — L
- Analisi: [docs/capitoli.md](docs/capitoli.md). Già divisi per capitoli: `data/chapters.yaml` (piano locale 1..n, profondità
  globale 1..255 per la difficoltà), atlante, `tools/simulators/chapters.py`, bestiari per capitolo (`data/monsters/bestiary.tsv`).
  **Fatto (15/11, branch `villaggi`)**: ogni capitolo ha nel gioco i **suoi mostri** (4 famiglie + 4 varianti forti, boss di
  capitolo nel piano del boss): sprite, colori e nomi nei file del tema del capitolo, nomi e colori copiati a `NM_AT`
  ([bestiario](docs/bestiario.md#nel-gioco-i-mostri-dei-capitoli-1511)). **Statistiche e IA non sono cambiate**: il tipo *t* di
  ogni capitolo ha quelle del tipo *t* del capitolo 1 (per profondità).
  **Da fare nel codice**: **statistiche proprie** per capitolo (le tabelle `mt_*`/`mon_spd`/`mon_llb` da caricare col tema,
  come i nomi: ~120 B per file; oggi le righe dei capitoli 2–4 nel bestiario sono concept); **IA nuove** (distanza per Bone
  Archer e Cultist, carica, teletrasporto per l'Imp, volo sull'acqua per Will-o'-Wisp e Gargoyle, rallentamento per Drowned e
  Frost Wight: da scegliere); meccaniche dei boss di capitolo; **bilanciamento** (prima simulazione: Abbot 13%, Miller 97%,
  Varok 100%: da rifare con `fit_rules.py` e `tools/simulators/chapters.py`, ora con 4 famiglie per capitolo).
- **Da decidere con il committente** (15/11): i colori dei disegni (Hellhound e Blood Knight sono rossi, 2, come il Lord of Ruin:
  nel capitolo 4 il Blood Knight è fra le evocazioni del boss finale e si confonde con lui; l'Ash Ghoul, grigio 12, nel tema
  grigio del capitolo 3 si legge poco sui muri chiari: screenshot `out/work/villages/monsters3.png` dei test `MON-CHAP-*`); se i boss con nome dei piani normali devono avere nomi per capitolo (oggi `first_names`/`epithets` comuni).

### H1 (ex 5.1) Quest system (dopo B8) — XL
- **Versione 2.0** quando è pronto, mai prima (regola del 09/11). **Ogni villaggio nuovo**: locanda con lo stesso baule,
  la mappa fuori da `$C900-$CFFF` (zona 1 del modulo MENU), `lab64 test regression -k VIL-MENU`.
- 15 quest (o 10), NPC, abilità solo da quest, tre villaggi, stanze fisse, compagno Torvald, pagine su disco (`QSTn`,
  tasto Q). Premi: cintura a 8 (F1), borsello a gradini (B9), **un gettone respec** (A1). Costi: ~1,1 KB di GAME (prima
  D7/D8), ~300 B in OVLT, ~550 B sotto l'I/O, ~60 blocchi. Analisi: `docs/quests.md`. Da rileggere col modello a capitoli (M9).

### H3 (ex 5.2) The Endless Abyss (dopo B10, B11, G6, E5) — XL
- Piani 21+ (fino a 255) a temi casuali, livello = piano, `void.table`, boss ×1,5, spade dell'Abisso, `chestLevel`
  riscalato, solo pozioni viola; morte −10% xp; normal / nightmare; città dell'Abisso con prezzi ribilanciati; salvataggio
  dei piani (D-CAP-3). Gettoni respec nei bauli (A1). Test: PERF-22 (cammino nei piani 21–255, oggi SKIP) e PERF-23
  (generatore su tutti i 255 piani: già oggi 0,34–0,84 s). Il generatore regge già i piani oltre il 20.

---

## 11 — Build, test e strumenti del gioco

Lab64 (toolchain) ha il suo TODO; qui solo cio' che riguarda il gioco.

### J14 (14/11) Pubblicare le build quando si passera' a GitHub — S
- Oggi le versioni stanno solo in `out/releases/` (ultime 5, locale). Per GitHub: asset del tag `v<V>` (disco, manuale,
  `manifest.json` con gli SHA-256) invece di conservarle in locale; niente zip dei sorgenti (regola del committente 14/11: lo
  da' gia' il tag). Da decidere con il passaggio a GitHub.

### T1 Mappa della memoria automatica: lavoro dalla parte del gioco — M
- La mappa automatica e la sonda in VICE sono di Lab64 (`lab64 map`, [docs/build.md](docs/build.md) sezione 4). Prima misura della
  sonda (14/11, 39 sessioni): **1791 B mai scritti** contro 6398 B liberi per l'analisi statica. Da guardare [non verificato, sono
  indizi]: zone libere per l'analisi statica ma scritte durante i test (`$8E39-$8FFF` 455 B, `$B701-$BDFF` con un byte libero a
  ogni inizio pagina = probabile tabella o buffer dietro puntatori, `$D000-$D47F` sotto l'I/O); `$B300-$B3FE` (modulo `lore`) mai
  scritto = il modulo non e' caricato da nessun test.
- **Annotazioni** (Lab64 le legge dal 15/11: `;@map` e `;@scenario` nei sorgenti, README di Lab64): scriverle nei sorgenti
  del gioco (descrizioni; `free-after=start` per i dati che si liberano dopo l'avvio: oggi il margine di 2333 B sotto `$8720` di
  `asm.sh` non si ritrova nella mappa automatica perche' `gfx_data` resta occupato; scenari villaggio / dungeon / menu) e poi
  **togliere le mappe vecchie** (`tools/memory-map/gen_rammap.py`, `gen_diskmap.py`: curate a mano), portando le loro
  descrizioni nelle annotazioni. Fino ad allora restano (la pagina automatica le collega).
- Sonda anche in `--release` (oggi a mano: `C64_MEMPROBE=1 lab64 test regression`, poi `lab64 map`); seconda passata con
  `C64_MEMPROBE=2` (altro schema: toglie i byte che sembravano mai scritti per caso).

---

## 12 — Idee per dopo

- **J4** — XS. Pozioni a cura fissa o a formula: confermare col committente che vada bene com'è.
- **J3** — S. Sprite del boss finale solo nel tema 8; da verificare con D8.
- **J2** — S-M. Anello della velocità (ex 2.7): riuso di `fz_move`; dopo E1.
- **J1** — M. Prefetch nuovo (salvataggio del piano in sottofondo, record N±1, brano successivo): 300–500 B + ~1 KB di buffer.

---

## Z — Note urgenti

Richieste del committente del 15/11, da lanciare così come sono (ogni voce dice a quale modello e in quale branch). Non sono ancora
dimensionate. Finita una voce: si cancella e la decisione va nella wiki o nel README interessato.

### Z3 — Fable — Lab64: review completa (branch a parte di lab64)
- Fai una review completa di lab64 e vedi se trovi problemi; quelli che sei in grado di fixare, fixali subito in autonomia. Il resto
  mettilo nel TODO di lab64.

### Z4 — Fable — Barbarian: review del gioco (altro branch)
- Fai una review anche di barbarian. Fixa bug, ottimizza la memoria e la velocità di caricamento.

### Z6 — Opus — Lab64: mappe di memoria multiple
- La mappa di memoria è solo per il gioco o anche per intro e menù?
- Come si può fare per avere mappe diverse? Il menù è un programma a sé, idem il jukebox.
- Cosa bisogna specificare per farsi generare tutte le mappe?
- Come si può fare per mostrare più mappe nella pagina web di lab64?
- Implementa questa logica.
