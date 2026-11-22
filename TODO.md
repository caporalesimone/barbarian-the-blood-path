# TODO — lavori aperti (riordinato il 15/11/2026)

Solo ciò che resta da fare. Il fatto, con le decisioni datate, sta nella wiki (`docs/`) e, fino all'08/11, in
[docs/wiki/storico-todo.md](docs/wiki/storico-todo.md) (archivio, non si aggiorna). Le decisioni nuove si scrivono nella voce a
cui appartengono, con la data; una voce finita si **cancella** e la decisione va nella pagina della wiki interessata.
I lavori della toolchain stanno nel TODO di Lab64 (`TODO.md` del suo repository).

**Riordino del 15/11** (richiesta del committente): voci raggruppate per **categoria** e, dentro ogni categoria, ordinate per
**taglia**. Gli **ID** restano quelli dell'11/11 (`<lettera><numero>`, citati nella wiki e nei commit): la lettera non dice più la
categoria. Tolte le voci fatte o superate: B5 (15/11, committente: resta la tavolozza A, sangue), T2 e T3 (passate a Lab64 e fatte il 15/11: tema del manuale, pubblicazione generica), M7 (1570/1571 in VICE:
`KRILL-18` passa), la parte risolta di I11, I9/I10/J10/J13 (sono lavori di Lab64).

**Taglie**: **XS** = minuti o una decisione; **S** = ore; **M** = 1–2 giorni; **L** = più giorni; **XL** = settimane.
Ogni voce: obiettivo, motivazione, cosa serve, cavilli.

Stato di riferimento (15/11, v1.256 su `main`): `SAVE_VER $C7`; smoke + sanity 33 test in ~17 s; hardware reale mai provato.

| # | Categoria | Voci (in ordine di taglia) |
|---|---|---|
| 1 | [Priorità massima](#1--priorità-massima) | A1 |
| 2 | [Decisioni del committente](#2--decisioni-del-committente) | B2, B3, B6, B8–B18 (XS ciascuna) |
| 3 | [Verifiche e misure](#3--verifiche-e-misure) | I2, I3, I4, I5, I6, I8, I7, I11, I1 |
| 4 | [Interfaccia, grafica, audio, testi, manuale](#4--interfaccia-grafica-audio-testi-manuale) | C3, E5, C1, M2, E6, E7, E8, E9, E10 |
| 5 | [Salvataggi](#5--salvataggi-un-solo-save_ver-dove-possibile) | C4, F2, F3, C5, F1 |
| 6 | [Prestazioni e memoria](#6--prestazioni-e-memoria) | D12, D14, D1, D5, D7, D10, D11, D3 |
| 7 | [Loader e disco](#7--loader-e-disco) | M8, M10, M3, M4, M5 |
| 8 | [Frenzy: prove in gioco](#8--frenzy-prove-in-gioco-del-committente) | K1, K2, K3, K6, K5, K4 |
| 9 | [Oggetti, combattimento, bilanciamento](#9--oggetti-combattimento-bilanciamento) | G2, G5, G4, G1, G3, G6, G8, G7 |
| 10 | [Contenuti: capitoli, quest, Abisso, intro, lingue](#10--contenuti-capitoli-quest-abisso-intro-lingue) | H4, M1, H5, M9, H7, H1, H3 |
| 11 | [Build, test e strumenti del gioco](#11--build-test-e-strumenti-del-gioco) | J14 |
| 12 | [Idee per dopo](#12--idee-per-dopo) | J3, J2, J1 |
| Z | [Note urgenti](#z--note-urgenti) | Z4 |

---

> **(22/11) Analisi d'insieme del codice e della memoria**: [docs/fable-analisi.md](docs/fable-analisi.md) (mappa della memoria e
> zone riusabili, difetti trovati, duplicazioni, risparmi possibili, oggetti, menu, mostri, abilità, test). Le proposte non
> fatte stanno lì, sezione 4 (memoria) e sezione 2 righe 7–10 (difetti aperti).

## 1 — Priorità massima

### A1 Punti statistica: rifiniture e verifiche a mano — **TOP PRIO** — S (verifica) + M (spostamento nel MENU)
- Unito a `main` l'11/11 (schermata C in `src/csheet/charsheet.asm` dal 21/11 sera, `docs/wiki/interfaccia.md`, `docs/wiki/quests.md`).
- **Glifo dell'HUD da confermare** (decisione 11/11): oggi la **freccia verde in su** (`LVUP`, colore 5). Le 20 proposte restano
  in `lab/concept/hud_glyphs/hud_glyphs.png` (+ `glyphs.json`, `make_sheet.py`): il committente deve scegliere il migliore.
- **Fatto (21/11 sera, soglia del committente portata a 2 s)**: la schermata C e' il modulo su disco `csheet`
  ([interfaccia](docs/wiki/interfaccia.md)), letto a `$EC00` col tasto C se un caricamento o un salvataggio l'hanno coperto
  (`cs_load`): villaggio 0,50 s, dungeon dopo le scale 0,80-1,41 s (PERF-DISK, peggiore su 6 fasi); margine di GAME 1534 -> 2874 B.
- **Da verificare a mano** (VICE o hardware): aprire C nel villaggio e nel dungeon (anche con mostri vicini), spendere,
  togliere, spostare fra le caratteristiche, undo, confirm (sì/no), uscita con punti in attesa (sì/no), respec con e senza gettoni,
  ricaricare la partita, CON alzata = vita massima alzata (schermata rifatta il 15/11, Z5: `docs/wiki/interfaccia.md`).
- **Decisioni da confermare** (B12, prese da me l'11/11): (a) **1 punto ogni 2 livelli** (9 al livello 20); (b) vita
  **retroattiva** su COS; ~~(c) all'uscita i punti in attesa si **confermano**~~ **superata il 15/11 dalla richiesta del
  committente (Z5)**: nulla si spende senza conferma esplicita; "confirm" chiede "spend N points for good?", RUN/STOP con
  punti in attesa chiede "spend N points before leaving?" (no = si esce e i punti tornano da spendere); (d) Fire su una
  caratteristica = +1; (e) nessun tetto. Da confermare (15/11, mie): il "no" all'uscita esce comunque (non torna alla
  schermata); la sola voce respec senza punti (cs_mode 1).
- **Resta**: aggiornare il manuale (pagina dei tasti e dell'HUD) e la tabella delle caratteristiche in `docs/wiki/combattimento.md`.

---

## 2 — Decisioni del committente

Nessuna di queste è codice: sono scelte (taglia **XS** ciascuna per chi decide). Finché restano aperte, le voci che le citano
non si possono chiudere.

| ID | Decisione | Blocca |
|---|---|---|
| B2 (ex D4) | **Cintura a 8 posti** (20/11, committente): premio importante a fine capitolo 2 o inizio capitolo 3; quest e momento decisi col simulatore ([quests](docs/wiki/quests.md) sez. 7). | F1 |
| B3 (ex D5) | **Pergamene fuori dallo zaino**: contatore 0..10 addosso (tasto 5), pile da 10 nel baule della locanda, opzione "riga dell'oro nella locanda con `s N`". Cooldown della pergamena ≥ 5 s (08/11). | F2 |
| B6 (ex D9) | **Una pergamena garantita per piano?** | G1 |
| B8 (ex D11) | **Quest system**: decisioni prese il 20/11 ([quests](docs/wiki/quests.md)); restano i chiarimenti C3–C7 della pagina (sez. 8). | H1 |
| B9 (ex D14) | **Borsello a gradini** (deciso il 20/11): 500 → 1000 → 3000 → 5000 con i passi 1, 4, 7 della catena, 10 000 con il passo 12 (numeri da ricontrollare col simulatore dell'oro). | H1 |
| B10 (ex D12) | **Abisso**: ripopolamento, prezzi della città, tetto dell'oro oltre i 16 bit. | H3 |
| B11 (D-CAP-1..5, 11/11) | **Capitoli** (`docs/wiki/capitoli.md`): quanti (i piani sono **5 per capitolo**: `data/chapters.yaml` 5, 5, 5, 5 + Abisso 235 = profondità 255; piano locale da 1 in ogni capitolo, profondità globale per la difficoltà, `docs/wiki/quests.md` 3.8); dove vanno Demon e Balrog (oggi da profondità 8–9: fuori dal capitolo 1 di 5 piani); ritorno ai villaggi precedenti; piani dell'Abisso salvati (anello di K record) o rigenerati; mappe fisse nell'Abisso; difficoltà oltre la profondità 32 e oltre 255. | M9, H3 |
| B12 (11/11) | **Punti statistica**: conferma delle scelte di A1 (punti per livello, vita retroattiva; l'uscita che confermava in silenzio è stata cambiata il 15/11 dalla richiesta del committente, Z5: ora chiede). | A1 |
| B13 (11/11) | **Frenzy**: corsa massima +50% (≈40 fps fra i mostri) invece di +100% (≈34 fps)? Misure in `docs/wiki/prestazioni.md`. Si decide dopo le prove della categoria 8. | D3, K |
| B15 (11/11) | **Salvataggi con Krill più lenti** ([docs/wiki/FastLoader.md](docs/wiki/FastLoader.md) sez. 7): "save game" 3,2–5,4 → 7,1–8,6 s, locanda 3,1 → 8,5 s, scale fra piani 10–11 s (il piano lasciato si salva). Causa: il plugin riscrive il file dell'eroe intero (9 blocchi) dopo averlo letto, più la ricarica del plugin (si modifica da solo) e del villaggio. Da decidere: accettare; file più piccoli (un file per piano: più file sul disco, scelta contraria del committente); immagine del file sempre in RAM (niente lettura, ~2 KB); non salvare i piani alle scale ma solo con l'eroe. | M4, M8 |
| B16 (11/11) | **A fine gioco: build con immagini disco diverse per drive?** Oggi solo 1541 (`_1541` nel nome). Krill supporta anche 1570/71, 1581, CMD FD, 1541U; SD2IEC solo con il ripiego KERNAL. Con tutti i drive l'install passa da 3225 a 6997 B e il plugin non si costruisce senza cambiare `save.s`. | I1, M5 |
| B18 (20/11) | **Caratteristiche e difficoltà** (proposta in `data/rules_next.yaml`, il gioco non la usa; misure con `tools/simulators/sim_builds.py`, [BILANCIAMENTO](docs/wiki/BILANCIAMENTO.md) sez. 10). **Deciso (20/11)**: seconda metà più dura; FOR = solo danno; DES = probabilità di colpire (+ CA col tetto dell'armatura, + cadenza); COS = vita, pozioni più efficaci, danno subito un po' ridotto; 4 punti a livello (80 al 20); caratteristiche iniziali più basse e primi piani più facili; cura delle pozioni in % della vita con un tetto; mostri con colpi a segno costanti per piano e mostri diversi per capitolo; **arco per il PG e per i mostri** (da progettare: tiro a distanza, posizione nel combattimento, il simulatore oggi tiene tutti a contatto). **Boss (20/11)**: più difficili, farming dei livelli come manopola (il calo dell'esperienza resta); obiettivo ~60% al livello del piano, 80–90% con 2 livelli in più; meccaniche in più proposte e simulate ([bestiario](docs/wiki/bestiario.md#proposta-del-2011-più-meccaniche-e-taratura-con-il-simulatore-design-non-nel-codice)). **Costi delle caratteristiche** riequilibrati il 20/11 notte (`fit_stats.py`, [BILANCIAMENTO](docs/wiki/BILANCIAMENTO.md) sez. 10): profili specializzati alla pari fra loro; (21/11) rendimento 2/3 oltre 32 punti; caratteristiche solo dai punti assegnati (anche nell'Abisso, niente crescita automatica); requisiti di FOR sugli oggetti; attacchi extra della DES (regola del committente: fino a 4 nel dungeon, il primo dopo 20 punti, poi uno ogni 7, 100/50/25/10% al 20 per il profilo destrezza); la DES dà velocità, CA e sempre la probabilità di colpire (+1 ATT ogni 20 punti, committente). **Soluzione finale del simulatore (21/11 notte)**: basi nuove con requisiti in scala nuova, armature e scudi sulla robustezza (FOR+COS)/2, FOR +4% del danno dell'arma a punto e +1 penetrazione ogni 25 punti (maneggevolezza scartata): profili specializzati entro ~2 volte il bilanciato ([BILANCIAMENTO](docs/wiki/BILANCIAMENTO.md) sez. 10). **Da decidere**: auto-fire o un Fire per colpo (21/11, in discussione), il minimo fisso di cura delle pozioni ai primi livelli, tutti gli altri numeri della proposta (costi per effetto, rendimento decrescente, obiettivi per piano, cura), quali meccaniche nuove dei boss tenere (poi codice del piano, `ovl_boss*.asm`, memoria da misurare), il farming senza tornare al menu (ripetibili o ripopolamento). Quando c'è l'accordo: regole nel gioco, `fit_rules.py` sui nuovi obiettivi, `SAVE_VER` se cambia il blocco dell'eroe (i valori restano sotto 255: massimo ~110). | A1, M9 |
| B17 (15/11) | **A fine sviluppo: trucchi nella release? quali e come?** Oggi il menu **cheats** (RUN/STOP, `src/game/cheats.asm`, [docs/wiki/cheats.md](docs/wiki/cheats.md)) c'e' nelle build di debug e di test (`CHEATS=1`) e **non** nella release (`CHEATS=0`, 0 B). **Da decidere a fine sviluppo** (non prima: dipende da quanto serve provare il gioco e dalla memoria libera). **Opzioni**: **(a) nessuno** (oggi): release identica a prima dei trucchi, nessuna sorpresa; si perde la comodita' per chi prova la release e per i giocatori in difficolta'. **(b) menu nascosto dietro un codice** digitato al titolo o una sequenza di tasti/joystick (stile Konami): chi lo sa lo accende, gli altri non lo vedono; costa codice in piu' (lettura del codice) oltre ai 395 B del menu e serve decidere se il codice e' per sessione o si ricorda (byte da salvare, **SAVE_VER**). **(c) solo alcuni** (es. god mode e salto di capitolo, senza level up e gettoni): meno byte e meno modi di rovinare il bilanciamento, ma `cheats.asm` va diviso con `.if` per voce (oggi solo `CHEATS` 0/1). **(d) oggetti o oggetti speciali** (anello, pergamena, uscita dal gioco con un bottino particolare) invece del menu: dentro il mondo di gioco, ma toccano formato oggetti e bilanciamento. **(e) segno "barato"** sull'eroe o nella sala della fama (bit nel blocco dell'eroe, **SAVE_VER** nuovo, `docs/wiki/FORMATO_DATI.md`): onesto verso i punteggi, serve in qualunque opzione con trucchi in release; con l'opzione (a) non serve. **Cavilli**: (1) **memoria in release**: 395 B di GAME (nella build di debug il margine del codice scende da 2397 a 2002 B); la release ha oggi lo stesso margine di prima, da rimisurare (`lab64 run tools/build/asm.sh release-game`, test `CHEAT-22`, che oggi **vieta** i trucchi nella release e va cambiato se si decide di tenerli); (2) il flag **`CHEATS`** (`tools/build/asm.sh`, `lab64.env`): con trucchi in release va scelta la variante (`CHEATS=1 RELEASE=1` o un flag nuovo), con il manuale e gli screenshot sempre a `CHEATS=0`; (3) **i salvataggi fatti con i trucchi** oggi sono eroi normali **senza segno**: se si adotta (e) quelli vecchi restano senza; (4) i trucchi aggirano la progressione (capitoli, boss, `c_unl`): vanno provati con **`next chapter` dai piani 2-3** (non verificato; il blocco entrando nei villaggi, ex A2, era un difetto del loader, corretto il 15/11: [FastLoader](docs/wiki/FastLoader.md) 4.1); (5) il manuale e l'help non parlano di trucchi: se restano in release vanno scritti o taciuti apposta. | H1, E6 |

---

## 3 — Verifiche e misure

Nessun codice nuovo (salvo una correzione se la verifica trova un errore).

- **I2** — S. Verifica a mano dal disco di release (`docs/wiki/manual-tests.md`, 10 minuti).
- **I3** — S. Test manuale 019 (locanda): spostare un oggetto, spegnere senza RUN/STOP, riaccendere.
- **I4** — S. B2 minimappa corrotta nel dungeon (05/11, mai riprodotto): servono screenshot e passi.
- **I5** — S. RUN/STOP fantasma nelle build NOKEYS in VICE (solo strumenti di test).
- **I6** — S. Glitch del brano del villaggio (hard restart): da riascoltare.
- **I8** — S. (13/11) Segnalazioni al team dell'emulatore da riprovare a ogni nuova build: `runLoop` non esatto con un caricamento
  da disco dentro il ciclo (`framesActual` 490 su 480 nel passo del portale, `docs/wiki/emulatore.md`); il pacchetto dichiara quel caso
  non verificato.
- **I7** — S. (13/11) Licenze **prima di pubblicare il repository**: Krill (BSD-3 con attribuzione), zx0 (BSD-3), file nelle loro
  cartelle del gioco. Le licenze dei componenti di Lab64 (vc64web, ROM Commodore in git, `open-roms`) sono nel TODO di Lab64.
- **I11** — S-M. **Il monitor remoto di VICE smette di rispondere a metà sessione** (13/11, due volte in `./build.sh --release`:
  PERF-DISK-10..14 con `monitor: no answer to 'load ...' in 20 s`, PERF-OPT-11 `MonitorError` dopo 30 s; rilanciati da soli: PASS).
  La parte "primo avvio a freddo" è stata corretta il 14/11 (`wait_boot` in Lab64, vedi `docs/wiki/test.md`). **Da fare** quando si
  ripresenta: registrare il log di VICE e del monitor; capire se dipende dalla macchina (riavvii, disco lento sotto il guest).
- **I1** — L. Hardware reale (mai provato): avvio, Krill's Loader (caricamenti e salvataggi) su 1541 vera e su 1570/1571 (in VICE
  passano: `KRILL-17`, `KRILL-18`), `quit the game` (reset), OVL2 sotto il KERNAL, TOD senza 9 V AC, tempi di loader, LORE e
  ritorno al menu. Serve l'hardware del committente.

---

## 4 — Interfaccia, grafica, audio, testi, manuale

### C3 (ex 1.4) Piccole scelte estetiche e audio — S
- `SFX_LOWHP` provvisorio da riascoltare nel JUKEBOX; tile del trono dietro il boss.

### E5 (ex 2.6) HUD: esperienza a 24 bit (per l'Abisso) — S
- Oltre 65535 xp: 3 cifre + K, barra a 24 bit (~100–130 B). Dipende dalle soglie oltre il 20 (H3).

### C1 (ex 1.2) Grafica della cintura nell'HUD: ampolle colorate — S-M
- Ampolle nei colori della pozione (rossa 2, gialla 7, viola 4) al posto dell'icona generica; in ricarica blu (già fatto).
  **Cavilli**: caratteri hires, colori < 8; i codici liberi dell'HUD sono finiti (`HUD_FREE`); da ripensare con la cintura a 8 (F1).

### M2 Temi audio veri dei villaggi — S-M
- Brano per capitolo fatto il 12/11 ([musica](docs/wiki/musica.md)). **Resta**: scegliere i temi dei villaggi 2–4 (oggi tutti Tavern
  of Dawn) ed eventualmente i temi dei boss dei capitoli (oggi il piano del boss usa il tema del capitolo).

### E6 (ex 2.8) Revisione completa del manuale e dell'help prima della prossima release — M
- Rilettura di `manual/manuale_src.html`, `data/help.txt` (`gen_help.py --snap` se cambia l'HUD), screenshot
  (`tools/vice/shots_manual.sh`); impaginazione (pagine mezze vuote dopo il 09/11); figura della morte in pagina 7.
- (15/11) Il generatore (Lab64) segnala le pagine che traboccano; in `--release` e' un errore (`lab64 manual --strict`).

### E7 (11/11) Manuale in inglese, oltre all'italiano — M
- `tools/manual/gen_manual.py --lang en` è pronto (sorgente `manual/manual_src_en.html`, PDF
  `Barbarian_Blood_Path_Manual_EN.pdf`; le parti generate hanno già le parole nelle due lingue; dal 15/11 la build fa da sola tutti
  i manuali che hanno il sorgente e li pubblica): **manca il sorgente
  inglese** (traduzione di `manuale_src.html`, stesso impaginato e stessi segnaposto). Prima di una release pubblica; poi
  `tools/build/release.sh` produce i due PDF e il test `BUILD-04` controlla anche quello inglese. Legato a H5.

### E8 (ex 2.9) Player audio unico per la release — M
- Il `JUKEBOX` è già sul disco; **va rifatto esteticamente** (standard dei menu: titolo, riquadri, elenchi brani/effetti)
  diventando il music player della release. Un solo player per tutti i programmi; tabella di brani ed effetti generata in build
  (decisione del 09/11: niente lettura della directory); effetti letti una volta all'avvio; due elenchi (canzoni, effetti),
  play/pausa/stop, filtri. Dettagli: storico in git (`TODO.md` fino a `22388f9`, voce 2.9).

### E10 Continuita' vera della musica del titolo (START -> GAME -> LOBBY) — M
- Fatto il 15/11 (ex E3 ed E4): Demon's Eye suona anche in `LOBBY` e nell'help (HELP, [help](docs/wiki/help.md)) e nel loader (BARBARIAN, [intro](docs/wiki/intro.md)); player e clock CIA in `src/common/title_music.inc` ([musica](docs/wiki/musica.md), `SND_MENU`), ma **sempre da capo**: START/LORE usano
  un altro player (`$BE00`) e `game_start` azzera lo stato del player del gioco, quindi fra un programma e l'altro c'e' una pausa e
  un riavvio. **Resta**: continuita' reale (stesso brano senza stacco) START -> GAME -> LOBBY e dopo ogni LOAD KERNAL, e rinunciare alla
  lettura di disco (~1,5 s) all'ingresso del menu (dati nel LOBBY non entrano: restano ~290 B liberi in `$C000-$CBFF`, il brano ne pesa 259).
  **Non verificato**: l'ascolto reale (solo VICE senza audio: byte e stato del player).

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
- Stato quest (~32 B, [quests](docs/wiki/quests.md) sez. 4.3), modalità normal/nightmare + eroe morto (1 B). (20/11) Il formato nuovo
  dell'eroe (oggetti a 7 B, baule della locanda sotto l'I/O, 5 piani nel file) è nel progetto di [oggetti](docs/wiki/oggetti.md#progetto-affissi-unici-e-memoria-2011).

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

Misure e soglie: `tests/regression/perf` (PERF-10..23), [docs/wiki/prestazioni.md](docs/wiki/prestazioni.md). Ogni intervento si
misura prima e dopo con `lab64 test regression -k PERF`. D1–D5 sono le osservazioni P1–P5 di
[docs/wiki/ottimizzazione.md](docs/wiki/ottimizzazione.md) non ancora fatte: **suggerite da fare**.

### D12 (11/11) Dall'analisi dell'assembly generato (`out/work/asm_audit/analisi_assembly.md`) — S
- **Fatto il 15/11** (+210 B di margine in GAME, +25 B nel blocco `$9C00`; START −172 B, LORE −170 B): casella del mostro,
  `GFX_FSTRIP`, 9 ripetizioni sicure, START/LORE con `.if` ([ottimizzazione](docs/wiki/ottimizzazione.md) O15–O23).
- **Restano, lasciate apposta** (motivi in [ottimizzazione](docs/wiki/ottimizzazione.md)): `px/py → ent_x/ent_y` (giro per fotogramma,
  9 B), prologo di `rel_put`/`rel_get` (cambio di `$01` con interrupt spenti, 9 B), ripetizioni in `gen_io.asm` (sotto l'I/O,
  25 B), due finestre di LOBBY (25 B, nessun guadagno per GAME), 58 B di player non usati nel JUKEBOX (`SP_RESUME = 0`).
  Rifare l'analisi dopo ogni lavoro grosso: `lab64 run python3 tools/build/asm_audit.py` (test `ASM-10/11`).

### D14 (11/11) Spazio del modulo MENU — S (per ogni zona nuova)
- **Stato** (v1.223, [prestazioni](docs/wiki/prestazioni.md#menu-del-villaggio-modulo-menu-residente-1111-v122x)): locanda e
  negozi nel modulo MENU, tre zone (zona 1 `$C900-$CFFF` 170 B liberi, zona 2 `$F4E0-$FCFF` 9 B, zona 3 `$A700-$A7FF`
  93 B). Ogni modifica a locanda e negozi deve starci: per crescere, altre zone (slot sprite 20–23 `$A500-$A5FF`, 256 B;
  coda degli slot 41–47 e 58–63 dopo i buffer della musica) o codice più corto (`asm_audit`).
- (19/11, verificato nel codice) `$C900-$CFFF` (zona 1 del MENU) **è libera in tutti i piani del dungeon**: ogni chiamata nel
  modulo (`MENU_INN`, `MENU_SHOP`, `MENU_NHERE`, `npc_tick`) passa da `cur_level` = 0, ed `enter_gfx` rilegge il MENU a ogni
  ingresso nel villaggio (`ovl_cur` = 0). La nota di prima ("resta per tutta la partita") era sbagliata. Dal 19/11 nel dungeon
  ci sta il **codice del piano** ([dungeon](docs/wiki/dungeon.md#codice-del-piano-1911); ex D8, fatto per il piano 20).

### D1 (ex P1) Primo ingresso nel piano 1 dal villaggio ~12 s in VICE (poi 5,6–7,3 s fra i piani) — S (misura) + ?
- Misurare cosa si legge (tema, brano, piano) col cronometro; il precaricamento del tema parte dopo N caselle e forse non
  finisce prima della cripta. Legato a J1 (prefetch nuovo). La taglia del rimedio dipende dalla misura.

### D5 (ex P5) Piani pesanti: fotogrammi persi con i mostri svegli e con la Frenzy — M
- (19/11) Con le grotte del capitolo 3 il piano 14 è cambiato: PERF-21 (camminata dalle scale, 160 fotogrammi) dà 1,3% (era 14,5%
  con le stanze); il più pesante ora è il 13 (8,2%). Video in tempo reale (`tools/vice/video_perf.py`, un fotogramma del video =
  un fotogramma PAL, 8 s per segmento): piano 1 camminata 2,1%, Frenzy +25/+50/+100% 4,5 / 10,5 / 25,1%; piano 14 camminata
  6,7%, fra i mostri 13,8%, Frenzy +25/+50/+100% 14,3 / 12,4 / 15,3%. La perdita dipende dai mostri svegli vicini più che dal piano.
- Più mostri svegli: stesso lavoro di D3.

### D7 (ex 6.1) Spawn dei mostri nella RAM sotto l'I/O — M
- `spawn_monsters`/`place_monster`/`place_boss`/`floor_types` (~600–800 B, da misurare) accanto al generatore
  (`gen_io.asm`). Attenzione alle annotazioni `@map` / `@free` di `src/game/rel.asm` (RAM sotto l'I/O), arena, `test_gen.py`.

### D15 (21/11) Memoria di GAME: KERNAL escluso e segmento `CORE` sotto il KERNAL — M + M — **passi 1-3 fatti (21/11)**
- **Perché**: con il solo inventario nuovo (branch `liste-menu`) GAME sfora di 571 B; il database degli oggetti di oggi pesa
  637 B, quindi spostare solo quello (F7) non basta. A regime la RAM sotto il KERNAL è quasi vuota (5,3 KB nel villaggio,
  7,4 KB nel dungeon). Analisi completa e alternative scartate: consegnata il 21/11 (`analisi_memoria_liste.3.md`).
- **Fatto (21/11), passo 1**: KERNAL sempre escluso (`MEMCFG`, `irq_entry`/`irq_exit`, vettori in RAM): +66 B in GAME, +18 B nel
  blocco `$9C00`, +27 B nella zona 1 del MENU; regression ed EMU verdi ([architettura](docs/wiki/architettura.md#banchi-di-memoria-01)).
- **Fatto (21/11), passi 2-3**: segmento CORE a `$E000` (file `core`, 2461 B; `core_need`), con dentro liste a scorrimento,
  inventario nuovo e descrizione degli oggetti; villaggio letto a `$EC00`; letture dell'eroe senza scrittura a `SV_ALT` (`$EC00`, non
  coprono CORE): CORE si rilegge solo dopo una scrittura (`sv_write`) o se manca (`ui_begin`, `ui_inventory`, `main_loop`).
  Margine di GAME: 1855 B (era −571 con il solo inventario nuovo). Misure in [FastLoader](docs/wiki/FastLoader.md) 7.4: salvataggio
  +0,4/+1,7 s (rilettura di `core`), ingresso nel villaggio 3 +1,3 s per la posizione dei file. **Deciso (21/11, committente)**: i limiti di PERF-DISK restano come sono (niente nuova disposizione per ora); PERF-24 si tratta
  come test instabile per ora. Erano: PERF-DISK-21/23 a cavallo
  della soglia (in3 4,55 s da sola, 3,34 s nella regression completa; twn1 2,28 s, in1 4,91 s e in2 4,34 s nella completa contro 0,91 / 2,73 / 3,14 da sola; soglie al 90% dei
  limiti): alzare i limiti o cercare un'altra disposizione del disco. PERF-24 (village 1, worst 2,11 contro 2,1) passa da solo (2,02).
- **Passi**: (1) KERNAL sempre escluso (`$01=$35`, ingresso e uscita dell'IRQ in RAM con gli stessi cicli della ROM, vettori
  `$FFFA-$FFFF`); (2) segmento `CORE` a `$E000-$EBD4` (file `core`, ZX0, letto all'avvio della partita e dopo ogni save; il
  villaggio si legge a `$EC78`); (3) `slist.asm`, inventario, azioni e descrizione degli oggetti in `CORE` (2918 B misurati).
- **Atteso**: margine di GAME ~+2300 B (misura) e ~+100–150 B dal passo 1 (stima). Avvio e save al massimo +1 s.
- **Attenzioni**: `CORE` finisce dove comincia l'appoggio del file MENU (`.cerror`); un caricamento di Krill con `$01=$35` non è
  ancora provato (dal sorgente il residente non tocca `$01`); il disco ha 75 blocchi liberi; con gli affissi (database ~2470 B)
  servirà una leva di riserva: scheda del personaggio letta all'apertura (+1517 B, tempo da misurare), D10. (21/11 sera) Fatti testo a 5 bit e font della UI compattato: margine 1534 B ([tecnica](docs/wiki/tecnica.md)).
- (21/11, **da fare** con gli affissi) Database degli oggetti diviso per momento d'uso e generazione da un sottoinsieme
  preparato durante i caricamenti: [oggetti](docs/wiki/oggetti.md#memoria-e-salvataggi-f7-approvato). Non cambia i passi qui sopra.
  **(21/11 sera, fase 3 degli affissi fatta senza sottoinsieme)**: le tabelle di generazione (`af_min`, `af_ty`, `af_ch`, `af_pl`/`af_ph`,
  `mag_t`, `shm_t`: ~370 B) e `af_gen`/`af_pick`/`it_cost` stanno in GAME, il cui margine e' sceso a **~950 B** (sotto la soglia di
  avviso di 1 KB). Il sottoinsieme (o una tabella di generazione caricata con il tema / il MENU) e' la prima leva per riprenderli.
  **(21/11 sera, fase 4)**: i poteri nuovi costano ~180 B; le tabelle di sola generazione (`af_min`, `af_ty`, `af_ch`, `mag_t`, `shm_t`,
  209 B) sono passate sotto l'I/O con il generatore (`out/work/afgen.asm` in fondo a `gen_io.asm`; `af_gen` le legge con `$01 = $34`):
  margine **942 B**; sotto l'I/O restano ~30 B (`LVRAM_end` = `$DFE1`). Provato e scartato: `ui_badsave` nel LOBBY (37 B oltre `$CBFF`).
  Leve rimaste (da decidere): la scheda C (1517 B) nella coda dei file del tema e del villaggio, gia' letti a ogni ingresso
  (niente accesso in piu' al disco, ~6 blocchi in piu' per file; da rileggere dopo un salvataggio); il sottoinsieme qui sopra;
  (fatto il 21/11 sera: testo a 5 bit e font compattato, margine 1534 B).
- **Fatto (21/11), fase B**: negozi, locanda e baule del piano sulle liste a scorrimento, vecchia interfaccia comune tolta
  (margine di GAME 2437 B, zone 1 e 2 del MENU con 863 e 523 B liberi); branch `liste-menu` unito a `main` il 21/11.
- (21/11 sera, committente) **Budget portato a 5 s, anche per portale e morte** (PERF-DISK: limiti `town_in`, `in1`-`in5`,
  `portal_in`, `portal_out`, `death` a 5,0 s contro il limite stesso). Misure del 21/11 sera: `town_in` 4,81, `in1` 4,83, `in2` 4,44,
  `in3`/`in4` 3,04, `in5` 3,73, portale 2,43 / 1,69, morte 2,43 s.
- (21/11, committente) **Budget del passaggio fra dungeon e villaggio: al massimo 3 s**: entro quel tempo si può caricare
  dal disco anche altro codice o dati (es. un modulo del dungeon, leva DNG dell'analisi). (21/11, chiarito) 3 s **in tutto**, si può salire di poco ma
  l'attesa non deve diventare noiosa. Oggi l'ingresso nel villaggio misura 2,7-4,6 s secondo il capitolo (PERF-DISK): già sopra.

### G10 (21/11) Bauli del piano: seme, farming e bauli aperti a metà — S — **da rivedere più avanti** (decisione del committente)
- **Oggi** (verificato nel codice): contenuto dal seme del mondo + piano + posizione (`chest_gen_seed`); nel record del piano 1 bit
  per baule generato ("tolto"): un baule aperto, anche non vuoto, sparisce cambiando piano; il baule del boss si salva intero
  solo finché non è aperto; i bauli lasciati dai mostri restano solo nella STASH (portale, morte). A ogni "continue" i piani si
  ripopolano (`c_game`) con **lo stesso contenuto**.
- **Opzioni**: (a) lasciare così: ogni seme ha i suoi bauli, alcuni semi migliori di altri (preferenza del committente del 21/11);
  (b) aggiungere `c_game` al seme del baule: contenuti nuovi a ogni partita dopo un save, ricaricare senza salvare non cambia
  l'oggetto, ~6 B, nessun `SAVE_VER` (da verificare in `rel.asm` che il "continue" non scriva `c_game`); (c) seme del bottino
  casuale salvato nell'eroe (2 B, `SAVE_VER`): scartata, (b) fa lo stesso senza byte.
- **Dubbi**: con (a) si "coltiva" un baule buono riaprendolo a ogni partita (copie da vendere): rimedi possibili, baule già
  aperto che si rigenera solo come oro, o tolto per sempre (1 bit per baule nel record del piano); con (a) rigiocando lo stesso
  eroe la sorpresa resta solo nel bottino dei mostri (casuale dopo `init_monsters_rt`, dalla wiki); bauli aperti a metà da
  conservare (1 bit per posto, con il contenuto rigenerato dal seme: ~2 B per piano + baule del boss) o no: regola da decidere.
- Legata a F7 (rigenerazione dei bauli dal seme, sottoinsieme della generazione deterministico per piano).

### D10 (ex 6.4) Altri interventi misurati — M
- `SCR_H` da `$8400` a `$8800` (+224 B); musica sotto il KERNAL (0,8–1,3 KB); codice solo-villaggio su file; variabili sparse (~60 B).
- **Analisi del 22/11 (richiesta del committente)**, con GAME a 2656 B di margine (dopo testo a 5 bit, font compattato, scheda C su
  disco e fase 5 degli affissi): nessuna di queste leve serve oggi.
  - **Musica sotto il KERNAL**: il brano del luogo serve anche nel villaggio, dove sotto il KERNAL non c'e' posto (CORE fino a
    `$EBF1`, scheda C da `$EC00`, zona 2 del MENU da `$F4E0`). Fattibile solo il **motivetto di combattimento** (buffer `$8E80`,
    384 B): suona solo nel dungeon (boss con nome a schermo, `docs/wiki/musica.md`), dove la zona 2 del MENU (`$F4E0`-`$FCFF`) e'
    libera. Da verificare che nessun caricamento del dungeon la tocchi (tema fino a `$F4DF`, plugin di save e suo buffer fino a
    `$F4DF`) e che il player legga con `$01 = $35` (si', KERNAL sempre escluso). Guadagno 384 B.
  - **`SCR_H` spostato** (+224 B): cambia la disposizione del banco VIC (schermo HUD, puntatori degli sprite, split raster): rischio
    alto per poco.
  - **Variabili sparse** (~60 B) e **codice solo-villaggio su file**: guadagni piccoli; il codice solo-villaggio e' gia' quasi tutto
    nel modulo MENU.
  - Ordine se servira' spazio: motivetto nella zona 2 del MENU, poi sottoinsieme della generazione (D15), poi il resto.

### D11 (ex 6.5) Compressione ZX0 dei file rimasti — M
- MENU, GFX0, temi: ~5 s in meno all'avvio (stima). Decompressore pronto (`src/common/zx0.inc`).

### D3 (ex P3, ex 1.9) Frenzy e analisi del dungeon — L
- **11/11**: profilo per routine (`tools/vice/frame_prof.py`), ottimizzazioni semplici fatte, velocità della Frenzy provate fino a
  +250%: il −50% di fps non si raggiunge; a +100% (oggi) −21/−27%. Tabelle e scenari in
  [docs/wiki/prestazioni.md](docs/wiki/prestazioni.md) ("Dungeon: analisi dell'11/11").
- **Da decidere (B13)**. **Da fare**, in ordine: lavoro a turni (K5, S-M); camera a casella in Frenzy (K4, M); branchi di
  mostri (M, poco guadagno oggi); scorrimento rifatto (L). Catena degli IRQ fragile (sez. 3.4).

---

## 7 — Loader e disco

### M8 Cosa reintrodurre del fast loader (ex D15) — S (decisione) + ?
- Krill's Loader è nel gioco ([docs/wiki/FastLoader.md](docs/wiki/FastLoader.md)). Cache e precaricamento sono stati tolti prima: **da
  decidere con il committente quali reintrodurre** guardando le misure (villaggio → piano 1 3,1 s, modulo MENU 2,3 s, tema ~1 s):
  oggi nessuna sembra necessaria per i caricamenti; i salvataggi sono il problema (B15). Da provare su hardware reale (I1).

### M10 (16/11) Menu BARBARIAN con Krill incluso: carica LORE, HELP e START con Krill — M
- **Richiesta del committente (16/11)**: il menu iniziale va rivisto in modo che **parta con Krill's Loader gia' incluso** (install nel file
  `BARBARIAN`, residente a `$0200`) e lo usi per caricare **LORE, HELP e START/gioco** (`loadraw`) invece del KERNAL con il trampolino.
  Cosi' sparisce anche il doppio caricamento che si vede oggi (BARBARIAN carica START con il KERNAL, START poi carica il resto con Krill).
- **Cosa implica** (analisi del 16/11, da `docs/wiki/FastLoader.md`; nessuna misura fatta):
  - Il residente occupa `$0200-$0312`, compreso il buffer tastiera del KERNAL (`$0277-$0280`): dopo l'install **l'IRQ del KERNAL non puo'
    scandire la tastiera** (scriverebbe sul codice di Krill). Il menu (e `HELP`) non possono piu' usare `GETIN`: servono un IRQ proprio e la
    lettura diretta della matrice (come `read_input` del gioco) per W/S, RETURN, spazio, 1-4 e le pagine dell'help.
  - Dopo l'install nessun programma puo' usare `LOAD`: i ritorni a BARBARIAN (da LORE, HELP, `bb_menu` della lobby) passano da Krill, senza
    `IOINIT`/`RESTOR`/pulizia delle pagine 2-3 del trampolino; START e LORE non reinstallano (oggi installano e LORE disinstalla);
    `exit game` e `bb_quit` fanno `krill_uninstall`, azzeramento delle pagine 2-3 e reset.
  - `BARBARIAN` passa da ~4,8 a ~8 KB (install 3225 B + residente 277 B), START si alleggerisce di 3,2 KB; piu' tempo dal `RUN` al menu
    (install del drive), oppure install alla prima scelta (ma allora il menu resta senza Krill fino a li').
  - Test da rivedere: BOOT-10..14, TITLEMUSIC-10/11, LORE-10/11, `POKE 1020,1`; da provare su vc64web e (I1) su hardware reale.
  - Guadagno atteso: i tre LOAD del KERNAL (START 7,6 KB, LORE 8,9 KB, HELP 9,6 KB) diventano letture Krill; collega con E10 (con gli IRQ
    accesi nei caricamenti la musica potrebbe continuare).
- **Non verificato**: i tempi attuali e quelli attesi (da misurare prima: `START`, `LORE`, `HELP` con il KERNAL in VICE); il comportamento
  dell'install di Krill dal menu su vc64web.
- Alternativa piu' piccola (non valutata a fondo): lasciare il KERNAL al menu e ridurre solo il primo caricamento (START).

### M3 Prestazioni dei caricamenti (ex J9) — M
- (22/11) **Posizione di CSHEET sul disco — decisione del committente in sospeso**. Misurate 3 posizioni (variabile provvisoria
  in `tools/build/mkdisk.sh`, tolta): dopo CORE (oggi), dopo la voce doppia di gfx1, in fondo prima delle quest. In fondo:
  in1 4,86 → 2,46 s, in2 4,63 → 3,09, in4 3,34 → 2,78, scheda nel dungeon 1,23 → 0,84 s; peggiorano in3 3,07 → 3,95, twn1 → 2,14 s
  (limite 2,0 del committente) e boss2 → 2,71 s (oltre il 90% di 3,0). Per adottarla: limiti twn1 2,5 e boss2 3,2 (solo con l'OK).
  Causa non verificata (probabile: tracce dei file seguenti e salti della testina).
  **(22/11, dopo la fase 6: GAME +680 B) PERF-DISK fallisce anche con la scheda dopo CORE**: town_in / in1 5,10 s (limite 5,0 del
  committente; prima 4,86). Con la scheda in fondo: in1 2,70, town_in 2,69, ma twn1 2,20 (limite 2,0), boss2 2,78 e boss3 2,93
  (oltre il 90% di 3,0). Serve la decisione del committente (limiti o altra disposizione dei file).
- (22/11 notte) **Studio della disposizione dei file** con le soglie proposte dal committente (villaggio ⇄ dungeon, morte e
  portale 4 s; menu 3 s; salvataggio libero): [FastLoader 7.5](docs/wiki/FastLoader.md). Caso tipico già dentro le soglie
  (ingresso 2,5–2,7 s, scale 1,7–2,4 s); il **caso peggiore** (ingresso nel villaggio dopo scheda C, pagina Q o salvataggio:
  5,1 s) dipende dalla ricerca in avanti di Krill nella directory e **nessun ordine dei file lo garantisce sotto i 4 s** (5
  disposizioni provate, anche con voci doppie: 4,1–4,7 s secondo la sequenza). **Da fare, in ordine di robustezza**: (a) `MENU`
  in coda a ogni `TWNc` (un solo file per ingresso nel villaggio: ~3,5 s nel caso peggiore, +56 blocchi); (b) meno voci nella
  directory (`QSTn` in 1–2 file, brani del solo jukebox fuori); (c) Krill con file aperti per traccia e settore. **Oggi
  `PERF-DISK-14` e `PERF-DISK-21` falliscono** (5,10 s su 5,0): serve una di queste o un limite diverso.
- (18/11) **PERF-DISK deterministici**: ogni misura parte da uno snapshot di VICE (macchina e drive) e si ripete in 6 fasi del
  disco (un giro diviso in 6, attesa nel buffer della cassetta): conta la piu' lenta (la fase sposta al massimo ~0,2 s). E una
  misura fuori limite non interrompe piu' la sequenza: prima saltava il resto del capitolo e il capitolo dopo partiva da
  un'altra testina e un altro settore della directory (twn3 2,35 s in un run, 0,95 s nell'altro). Ora due run danno gli
  stessi numeri (±0,04 s). Ricalibrati con la regola del 15/11 (1,15 x la misura, per eccesso a 0,1 s): in1 5,7 → 6,6,
  twn2 2,2 → 2,5, boss1 3,0 → 3,2; soglie del committente invariate. Da capire perche' in1 (5,66 s) costa ~2 s piu' di in2-in5.
- (18/11) **Directory e finestra di Krill** (risolto per PERF-12, [docs/wiki/FastLoader.md](docs/wiki/FastLoader.md) 7.2):
  Krill cerca i file in una finestra di 11 voci e va solo in avanti nella directory; con 52 voci un giro costa ~1,3 s e i
  tempi cambiano a scatti spostando un file. Scelto (19 dischi misurati) l'ordine L6 con la directory a interleave 2:
  villaggio → piano 1 dopo un salvataggio 6,0 → 3,8 s, in1 5,6 → 2,8 s, totale delle misure −7,7 s. (18/11 pomeriggio)
  code dei file (FastLoader 7.3): brani e mappe del boss dentro `TWNc`/`GFXn`, niente `BOSSCHc`, totale 73,6 s. **Resta**: le
  pagine QST1-QST8 (8 voci) in meno file quando i testi delle quest saranno veri (oggi segnaposto: si deciderà sulle misure).
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

Il committente prova in gioco le proposte e poi decide (B13). Misure di partenza ([prestazioni](docs/wiki/prestazioni.md),
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

### G9 Ribilanciamento dopo 1 punto statistica per livello (17/11) — M
- Il 17/11 il committente ha scelto 1 punto a ogni livello dal 2 al 20 (19 punti al 20, prima 9): il PG di riferimento
  (`reference_alloc`) e' piu' forte e i mostri non sono stati ritoccati. Da fare: simulatori e arena
  (`tools/simulators/`, `tools/vice/arena.py`) sui piani 1-20, confronto con le curve di prima, ritocco di CA e vita dei
  mostri in `data/rules.yaml` se il PG colpisce o resiste troppo. Test di bilanciamento con `./build.sh --release`.
- (18/11) In piu' la **cadenza dello Slash dipende dalla DES** (`player.attack_speed`: + max(0, 12 - 3 x mod DES) fotogrammi):
  all'inizio il PG colpisce piu' lentamente (pugnale 0,24 -> 0,42 s), dalla DES 18 come prima. Il simulatore lo riproduce
  (`tools/simulators/rules.py`); il PG di riferimento spende in DES un punto ogni 4 (DES 18 solo verso il livello 16):
  i primi piani diventano piu' duri. Da misurare con il resto di questo punto.

### G2 (ex 4.2) Economia: prezzi, oro, riparazioni — M
- **Deciso (21/11, committente, ex B7)**: per ora i prezzi della prima stesura dei `.tsv` (`data/items/next/`); **da fare dopo**:
  tarare tutti i prezzi con **formule** che dipendono da prefisso, suffisso e livello dell'oggetto (non più la regola "1,5 piani"
  del 06/11, [BILANCIAMENTO](docs/wiki/BILANCIAMENTO.md) sez. 12, superata), poi verifica col simulatore dell'oro.

### G5 (ex 4.5) Unici: cosa resta dopo la fase 6 — M
- (22/11) **Fatti** gli unici di `data/items/next/uniques.tsv` (fase 6, [oggetti](docs/wiki/oggetti.md)): poteri, nome giallo, prezzo,
  generazione a caso nella finestra di livelli (uno su 64 se c'è un candidato).
- **Da fare**: unici **garantiti** da boss, quest e bauli epici (colonna `source`: The Hollow Abbot, Mother Stitch, Varok, passi delle
  quest, bauli epici degli anelli e delle armature), con le quest (H1); furto di vita e spine (LEECH, THORNS) dopo la 2.0 (O5): oggi
  tre unici hanno quel potere senza effetto; taratura di `unique_one_in` e dei prezzi con i simulatori (`sim_gold.py`, `sim_chest.py`).
- Regola di `uniques.tsv`: righe nuove solo in fondo (numero dell'unico nei salvataggi), altrimenti `SAVE_VER` nuovo.

### G11 (22/11) Furto di vita e spine: come funzionano e cosa serve — S-M (dopo la 2.0, decisione O5)
Oggi i due poteri esistono nei dati (`PW_LEECH` = 15, `PW_THORNS` = 16; affissi *of the leech* (3%), *of blood* (5%) e *of thorns* (2) con peso 0, cioe' mai generati; unici
*censer-bearer* LEECH 3, *tithe-taker* LEECH 5, *doll-hide* THORNS 2) ma **nel gioco non fanno niente**: `af_one` li salta e nel
riquadro dell'oggetto compaiono solo le sigle `lch` e `thn`. Dinamica proposta (da approvare prima di scrivere il codice):

- **Furto di vita (LEECH N)**: N è una **percentuale del danno inflitto**. Ogni colpo del PG che toglie vita a un mostro
  (attacco base, Whirlwind su ogni mostro colpito, Smash; non il Battle Cry, che non fa danno) cura il PG di
  `danno × N / 100`, arrotondato per difetto, **almeno 1** se il colpo ha fatto danno, mai oltre la vita massima. Conta il danno
  realmente tolto (dopo lo scudo di Varok o la protezione dei feticci di Mother Stitch, non oltre la vita rimasta al mostro),
  così un colpo di grazia su un mostro quasi morto cura poco. I valori di più oggetti si sommano (arma + anello).
  - Esempio con i dati di oggi: *censer-bearer* (3%) ai piani 6–10, danno medio per colpo ~15 → +1 a colpo (il minimo);
    *tithe-taker* (5%) ai piani 17–20, danno ~40 → +2 a colpo, circa +4/5 punti al secondo con la cadenza di un'ascia: da confrontare
    con il danno subito al secondo in quei piani (simulatore) per non rendere inutili le pozioni.
  - Codice: un totale in più in `recalc_stats` (`af_lch`, accanto ad `af_spd`); in `hit_one`, dopo aver calcolato il danno,
    `mul16x8` per `N × 256 / 100` e byte alto; somma a `c_hp`, `hp_cap`, `hud_pend |= 1`. Stima **~45 B** in GAME.
- **Spine (THORNS N)**: N è **danno fisso restituito**. Ogni volta che un mostro colpisce il PG **in corpo a corpo**
  (`mon_attack` andato a segno, non i colpi a distanza degli arcieri quando ci saranno, non le aree dei boss) il mostro
  perde N punti vita, senza tiro per colpire e senza armatura; può morire (esperienza e bottino normali, `kill_monster`), non
  viene stordito. I valori si sommano.
  - **Problema di scala**: 2 punti fissi (*doll-hide*, piani 9–13) contro mostri da 60–150 punti vita non si notano. Due
    alternative da decidere: (a) N **per livello del PG / 4** (2 → 6–8 danni al livello 13); (b) N × 25% del danno ricevuto
    prima delle riduzioni (2 → 50%). Consiglio (a): resta un numero fisso leggibile nel riquadro ("thn+2") e cresce da solo.
  - Codice: totale `af_thn`; in `mon_attack` dopo `hurt_player` sottrazione a 16 bit da `mhp`/`mhph` del mostro `ho_i` e
    salto a `kill_monster` se arriva a 0. **Attenzione**: `kill_monster` verrebbe chiamata mentre `update_monsters` sta
    scorrendo proprio quel mostro: va verificato che il ciclo regga un mostro che muore durante il suo attacco (oggi i mostri
    muoiono solo per mano del PG, fuori da quel ciclo). Stima **~40 B** + la verifica.
- **Per tutti e due**: peso > 0 delle righe degli affissi in `gen_db.py` (oggi forzato a 0), `it_pw` mostra già le sigle con il
  valore; simulatore (`rules.py` `Hero(affixes=)`: cura per colpo e danno di ritorno nel ciclo del combattimento,
  `sim_builds.py` per vedere quanto valgono rispetto a +danno e +vita); test: un colpo con danno noto cura il giusto e si
  ferma alla vita massima; un mostro con 1 punto vita muore colpendo il PG con le spine e lascia bottino; arena per il
  confronto col simulatore. `SAVE_VER` non cambia (gli id delle righe ci sono già).

### G4 (ex 4.4) Armi casuali (seed per oggetto) — M
- Seed per oggetto (+1 B a oggetto) e funzione seed → statistiche uguale in 6502 e Python. Cambia `SAVE_VER` (categoria 5).

### G1 (ex 4.1) Obiettivi e curva (iterazione successiva del simulatore) — M
- Gruppo base, boss del piano ~75%, boss finale 60–70%; curva del PG più regolare; stordimento; Battle Cry 1 contro 1;
  set delle armi. `tools/simulators/fit_rules.py`, `cmp_rules.py`, `chapters.py`, arena. Rifare dopo F1 e A1.

### G3 (ex 4.3) Probabilità di uscita per ogni oggetto (stile Diablo) — M
- `w = R × g(livello area − livello oggetto)`; colonna `dropRate` in `data/items/items.tsv` come in DevilutionX
  (`itemdat.tsv`). Generatore, simulatore, `docs/wiki/bottino.md`. Prerequisito per gli oggetti dell'Abisso (H3).

### G6 (ex 4.6) Arena fase 2 — M-L
- Bot che si muove, posizioni di partenza, strategie; confronto arena / simulatore. Prerequisito per H3.

### G8 (11/11) Database degli oggetti: prossimi passi — M-L
- `data/items/items.tsv` è la sorgente di verità. Da valutare: affissi magici (prefissi/suffissi come
  `item_prefixes.tsv`/`item_suffixes.tsv` di DevilutionX) al posto del solo +N (fatto il 21/11); oggetti unici (G5, fatti il 22/11 salvo i garantiti); requisiti
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
  `docs/wiki/capitoli.md`): oggi il testo parla ancora di "twenty floors" (`data/lore.txt`).
- (12/11, committente) **Scorrimento**: la velocità va bene. **Interlinee**: sempre **una riga vuota** fra un elemento e
  l'altro; **due righe vuote** dove oggi ce n'è già una (`@gap 1`). Con le interlinee in più **accelerare di circa il 4%**.
  Nota tecnica (non verificata): `LR_SPEED` = 6 fotogrammi per pixel, intero; il 4% si ottiene a schema, p.es. 6-6-6-5
  fotogrammi ogni 4 pixel (−4,2%). Si tocca `src/lore/scroll.asm` e `data/lore.txt` (`tools/build/gen_lore.py`), poi test
  `LORE` e `docs/wiki/intro.md`.
  (15/11, committente) **Fatto**: interlinea fra le righe di testo (una riga vuota; due fra i paragrafi: `LINE_GAP`/`PARA_GAP` in
  `gen_lore.py`) e **fire del joystick 2 tenuto = velocità doppia** ([intro](docs/wiki/intro.md)). La storia passa da 220 a 292 righe
  (4 min 13 s a velocità normale): **il 4% di accelerazione di sopra non è stato fatto** (non richiesto): resta da decidere.
- (19/11, committente) **Storia e intro da rivedere in toto quando gli sviluppi del capitolo 2 sono pronti**: Bad Water al
  posto di "Blackwater Mill", tema voodoo, boss *Mother Stitch, the Dollmaker* al posto del mugnaio, piani dei boss con luogo
  proprio. `data/lore.txt` cita ancora il mulino. (20/11) **Trama nuova decisa**: The Blood Tithe ([quests](docs/wiki/quests.md)
  sez. 3); il testo dell'intro va scritto e approvato (chiarimento C7).

### M1 Sequenza dei capitoli: cosa resta ([capitoli](docs/wiki/capitoli.md)) — L
- **Effetto grafico del passaggio** di capitolo (oggi: schermo nero, poi le schermate di salvataggio e caricamento): tbd.
- **Villaggi** (15/11, fatto sul branch `villaggi`, da rivedere con il committente: [villaggio](docs/wiki/villaggio.md)): i capitoli
  2–4 e la città dell'Abisso (prototipo) hanno tile, mappa, colori e posizioni propri (file `TWNc` con intestazione). **Resta**:
  la revisione del committente (i quattro villaggi sono prototipi; la proposta scartata è in `lab/villaggi/proposta-a-temi/`);
  NPC; un **brano per villaggio** (oggi lo stesso, M2); la **minimappa** dei villaggi nuovi (i colori "acqua" e "strade" seguono
  i ruoli dei posti: nel villaggio 4 il cratere esce blu); l'etichetta dell'ingresso del sotterraneo ("stairs down to level N"
  per tutti: una per villaggio costa una stringa nell'intestazione); prova su **vc64web** e su hardware reale; il passaggio di
  capitolo legge il file del villaggio nuovo due volte (tempo non misurato); la posizione dei villaggi sul disco è decisa e misurata
  (15/11, disposizione `hubchap`, soglie per villaggio: [FastLoader](docs/wiki/FastLoader.md) 7.1); la **città dell'Abisso** oggi si raggiunge
  dall'uscita del villaggio 4 dopo il boss finale e la Bocca non fa nulla (da rifare con H3; la leva della sala del trono resta).
- **Fan art della mappa del mondo** (15/11): `tools/art/world_map.py` (`out/work/art/world_map.png`); dal 16/11 sta nel
  **manuale italiano** (pagina "IL MONDO", prima del capitolo 4; la genera la build del manuale, non e' in git). (19/11) v3
  approvata dal committente: 1920x1200, tono crepuscolo, neve a nord, capitolo 4 a est in basso, cittadella e poi l'Abisso al
  centro del cratere di lava, cammino rosso. Restano da decidere la wiki e la scatola; il testo del manuale non racconta la trama
  (in revisione): da rivedere con E6, e da tradurre con E7.
- **Boss veri** (le **mappe vere** dei piani del boss dei capitoli 1–3 sono fatte il 19/11: cripta, isola nella palude, grotta
  crollata, [dungeon](docs/wiki/dungeon.md#piani-del-boss-dei-capitoli-13-5-10-15-gen_cboss-1211-mappe-vere-dal-1911); da
  provare in gioco a mano): dal 15/11 i boss dei capitoli 1–3 hanno il loro **sprite**
  e il loro colore; **meccaniche nel codice dal 19/11** (codice del piano, [bestiario](docs/wiki/bestiario.md#meccaniche-dei-boss-di-capitolo-decise-il-1511)):
  i numeri sono miei, **da provare in gioco e da tarare** (simulatori: non riproducono le meccaniche); dal 15/11 hanno anche il
  **loro nome** nella barra e i **mostri del capitolo** intorno (solo grafica, colore e nome: M9); statistiche proprie, bottino
  speciale, sala che si chiude, pentacolo che brucia del Lord of Ruin: da fare (decisioni del committente).
- **Ritorno ai villaggi precedenti** (20/11, D-CAP-2 decisa): parzialmente distruttivo, dall'ingresso del villaggio ([quests](docs/wiki/quests.md), C1); fase 3 del piano delle quest.
- **Tile di accesso al dungeon generico**: la cripta (`T_TSTAIRS`) è già un tile da mettere dove si vuole; più ingressi con
  destinazioni diverse richiederebbero una tabella (utilità da confermare).
- (12/11, committente) **Confermato**: un tema grafico dei livelli per capitolo (`GFX1..8`) va bene così.

### M11 (18/11) Stile delle mappe per capitolo — L
- **Fatto (18/11)**: grotte nel capitolo 3 (piano 11 innevato, 12 ghiaccio azzurrino, 13-14 roccia grigia): [dungeon](docs/wiki/dungeon.md) "Grotte".
  Da rivedere con il committente in gioco: forma (macchie e gallerie), colori delle palette 9 e 10, tempo di generazione
  (0,8-0,95 s contro 0,3 s delle stanze).
- **Palude** (capitolo 2, prototipo del 18/11 pomeriggio: [dungeon](docs/wiki/dungeon.md) "Palude"): piani 6-9 affiancati lungo un
  percorso a caso (uscita su un lato qualsiasi), cancelli sui bordi al posto delle scale (il caricamento resta), isole, passerelle, palette 12 unica. (19/11) cancelli dello stesso piano ad almeno 40 caselle, `gate_hash` da tutto il seed. Da rivedere con il
  committente in gioco: colori dell'acqua, cancelli, isole; restano facoltativi le pozze che rallentano e i mostri sull'acqua.
- **Cittadella** (capitolo 4, prototipo del 19/11: [dungeon](docs/wiki/dungeon.md) "Cittadella"): sale con colonne, simmetria
  sinistra/destra. Da rivedere con il committente in gioco: palette (oggi casuale), colonne, passaggi sull'asse.
- **Memoria del generatore** (19/11): il PRG `GAME` (codice + grafica fissa + immagine del generatore) deve finire prima di
  `$9C00`: oggi `$99BF` (build normale), `$9B80` nella build di test più grande (`TESTUI=28`, 128 B di margine). (21/11) Con armi,
  NPC fissi e requisiti la build di test sforava: l'immagine del generatore ora è **compressa ZX0** (3243 → 2177 B,
  `tools/build/gen_imgz.py`, GAME in due passate in `asm.sh`) e GAME finisce a `$96F6` (build normale). Il "margine
  codice" stampato dalla build (fino a `$8720`) non lo dice: va aggiunto alla stampa. Per altro codice di uno stile solo
  conviene la strada della cittadella (codice nella coda del file del tema, `GFX_DUN_END`).
- **Attenzione**: ogni stile cambia i piani salvati di quel capitolo (`GVER`, `test_gen`).

### H5 (ex 5.4) Due build: inglese e italiano (dopo H4) — L
- Intro e testi delle quest nelle due lingue con gli stessi limiti di buffer e disco; con E7 (manuale) ed E9 (stringhe).

### M9 Capitoli nel codice e bestiari (ex H2, H6) — L
- Analisi: [docs/wiki/capitoli.md](docs/wiki/capitoli.md). Già divisi per capitoli: `data/chapters.yaml` (piano locale 1..n, profondità
  globale 1..255 per la difficoltà), atlante, `tools/simulators/chapters.py`, bestiari per capitolo (`data/monsters/bestiary.tsv`).
  **Fatto (15/11, branch `villaggi`)**: ogni capitolo ha nel gioco i **suoi mostri** (4 famiglie + 4 varianti forti, boss di
  capitolo nel piano del boss): sprite, colori e nomi nei file del tema del capitolo, nomi e colori copiati a `NM_AT`
  ([bestiario](docs/wiki/bestiario.md#nel-gioco-i-mostri-dei-capitoli-1511)). **Statistiche e IA non sono cambiate**: il tipo *t* di
  ogni capitolo ha quelle del tipo *t* del capitolo 1 (per profondità).
  **Da fare nel codice**: **statistiche proprie** per capitolo (le tabelle `mt_*`/`mon_spd`/`mon_llb` da caricare col tema,
  come i nomi: ~120 B per file; oggi le righe dei capitoli 2–4 nel bestiario sono concept); **IA nuove** (distanza per Bone
  Archer e Cultist (21/11: progetto delle frecce in [bestiario](docs/wiki/bestiario.md#arcieri-e-frecce-2111-progetto-non-nel-codice): al massimo 2 in volo, sprite 2 + uno slot dei mostri), carica, teletrasporto per l'Imp, volo sull'acqua per Will-o'-Wisp e Gargoyle, rallentamento per Drowned e
  Frost Wight: da scegliere); meccaniche dei boss di capitolo; **bilanciamento** (prima simulazione: Abbot 13%, Miller 97% (19/11: oggi Mother Stitch, stesse statistiche, meccanica nuova),
  Varok 100%: da rifare con `fit_rules.py` e `tools/simulators/chapters.py`, ora con 4 famiglie per capitolo).
- **Da decidere con il committente** (15/11): i colori dei disegni (Hellhound e Blood Knight sono rossi, 2, come il Lord of Ruin:
  nel capitolo 4 il Blood Knight è fra le evocazioni del boss finale e si confonde con lui; l'Ash Ghoul, grigio 12, nel tema
  grigio del capitolo 3 si legge poco sui muri chiari: screenshot `out/work/villages/monsters3.png` dei test `MON-CHAP-*`); se i boss con nome dei piani normali devono avere nomi per capitolo (oggi `first_names`/`epithets` comuni).

### H7 (21/11 sera, committente) Testi delle quest: meno caratteri speciali, 5 bit e compressione — S
- **Obiettivo**: far stare piu' quest e testi piu' lunghi nei file `QSTn` (1024 B ciascuno: oggi `QST0` 999 B, cioe' indice e codice
  della pagina quasi pieni, e `QST2` 931 B).
- **Passi decisi dal committente**:
  1. **Rivedere i testi** di `data/quests.yaml` per usare il minor numero possibile di caratteri speciali (es. niente `;`, che
     non e' fondamentale: si riscrive la frase). Ideale: solo lettere, spazio, `:` `.` `/` (5 bit) e pochi segni della tabella
     `T5X` (10 bit).
  2. **Testo a 5 bit** come nel gioco (`docs/wiki/tecnica.md`, "Testo a 5 bit"): codificatore Python in `tools/build/gen_quests.py`
     (stessa tabella della macro `t5` di `src/common/macros.inc`), stampa con `ui_puts5` di GAME in `src/qpage.asm`; titoli
     dell'indice e righe del dettaglio. Testo leggibile in `quests.yaml` (regola: il testo a 5 bit si scrive sempre leggibile).
  3. **Compressione** se ha senso: valutare ZX0 dei file `QSTn` (decompressore gia' in GAME, `src/common/zx0.inc`) o un dizionario
     di parole frequenti, misurando i byte risparmiati contro il codice in piu' in `QST0` e il tempo di caricamento.
- **Quando**: con H1 o prima di aggiungere una quest (in `QST0` restano 25 B). Test: le pagine delle quest a video uguali.

### H1 (ex 5.1) Quest system — XL
- **Progetto deciso il 20/11** ([quests](docs/wiki/quests.md)): regole, trama The Blood Tithe, catena di 12 passi, 15 accessorie,
  ripetibili per capitolo, premi, **piano di lavoro in 4 fasi con 3 cancelli** (sez. 8). Il concept del 17–18/11 (NPC, "!",
  vaganti, pagina Q, `QST0`/`QSTn`, `c_qst` a 8 bit) è descritto in [villaggio](docs/wiki/villaggio.md#abitanti-1718-11-concept).
- Prima delle quest: oggetti ed economia (fase 2, [oggetti](docs/wiki/oggetti.md#progetto-affissi-unici-e-memoria-2011)).
- **`QST0` è pieno** (1021 B su 1024): la pagina Q va riprogettata (cancello G2).
- (22/11) **Tutte le quest definite** con testi e premi in `data/quests/next/quests.yaml` (test `QUESTDB-NEXT-10`); **come
  implementare** motore, modulo del villaggio, pagina Q e ogni singola quest: [QUEST-IMPLEMENTAZIONE.md](QUEST-IMPLEMENTAZIONE.md)
  (usa e getta: si cancella a quest finite). Da approvare: i premi `proposal: true`, C3, C6, P3 e dove mettere i 32 B di stato.
- (22/11 notte) **Domande per chiudere il progetto**, con alternative e raccomandazione: [QUEST-DOMANDE.md](QUEST-DOMANDE.md) (13
  domande: stato, testi sul disco, codice del villaggio, cancello, vittoria, premi, boss del capitolo, unici, ripetibili, segni,
  ordine). Misurato (`QUESTDB-NEXT-11`): testi a 5 bit 8 826 B; un file per quest 50 blocchi e 33 voci, un file per capitolo 36
  blocchi e 5 voci; ZX0 −9%, non conviene.
- **Versione 2.0** quando è pronto, mai prima (regola del 09/11).

### H3 (ex 5.2) The Endless Abyss (dopo B10, B11, G6, E5) — XL
- Piani 21+ (fino a 255) a temi casuali, livello = piano, `void.table`, boss ×1,5, spade dell'Abisso, `chestLevel`
  riscalato, solo pozioni viola; morte −10% xp; normal / nightmare; città dell'Abisso con prezzi ribilanciati; salvataggio
  dei piani (D-CAP-3). Gettoni respec nei bauli (A1). Test: PERF-22 (cammino nei piani 21–255, oggi SKIP) e PERF-23
  (generatore su tutti i 255 piani: già oggi 0,34–0,84 s). Il generatore regge già i piani oltre il 20.
- Pozioni nell'Abisso: pozioni per piano da `rules.yaml` `potions.abyss_drop`; `pot_heal` è già pronta (colonna `heal_abyss`, `docs/wiki/oggetti.md`).

---

## 11 — Build, test e strumenti del gioco

Lab64 (toolchain) ha il suo TODO; qui solo cio' che riguarda il gioco.

### J15 (22/11) Bot che gioca da solo: prossime capacità — M
- `tests/bot/` ([README](tests/bot/README.md)): gioca in VICE via TCP, esplora, combatte, usa le abilità, indossa, spende i punti,
  registra i tempi per piano e capitolo. **Da fare**: negozi veri (oggi vendita e acquisto sono scorciatoie in memoria), inventario
  e scheda C navigati davvero, pergamena del portale, riparazioni, bersaglio ragionato (evocati dei boss), capitoli 2–4 provati
  a fondo (palude con i cancelli, sala del trono), più semi in fila con un rapporto unico per il bilanciamento.
- (22/11 notte, committente) **Migliorare il bot e usarlo per verificare se il bottino dei piani basta.** Prima partita con i
  trucchi (`out/work/bot/cheat3.json`): nei bauli dei piani 1-4 solo pugnali, scudi piccoli e cuoio (10 oggetti, nessuna arma
  migliore del pugnale); senza comprare dal fabbro l'eroe arriva all'abate con l'arma di partenza; con ascia da guerra, cotta
  di maglia e scudo medio (livello 6, CA 19) muore 4 volte lasciando all'abate 21-57 punti vita su 210. **Da fare**: (1) bot
  senza trucchi su 10+ semi in fila, rapporto unico per piano (oggetti trovati per categoria e livello oggetto, oro, pozioni,
  morti, livello dell'eroe all'ingresso) da confrontare con `sim_chest.py` e `sim_gold.py`; (2) capire se il problema e' il
  livello oggetto L = T × u² dei bauli (quasi sempre 0 nei primi piani: `docs/wiki/bottino.md`) o il numero di bauli; (3)
  bot capace di battere l'abate (prima gli scheletri, ritirata e ritorno) per misurare la difficolta' vera del boss; (4) poi
  capitoli 2-4.

### J14 (14/11) Pubblicare le build quando si passera' a GitHub — S
- Oggi le versioni stanno solo in `out/releases/` (ultime 5, locale). Per GitHub: asset del tag `v<V>` (disco, manuale,
  `manifest.json` con gli SHA-256) invece di conservarle in locale; niente zip dei sorgenti (regola del committente 14/11: lo
  da' gia' il tag). Da decidere con il passaggio a GitHub.

---

## 12 — Idee per dopo

- **J3** — S. Sprite del boss finale solo nel tema 8; da verificare con il codice del piano (ex D8, [dungeon](docs/wiki/dungeon.md#codice-del-piano-1911)).
- **J2** — S-M. Anello della velocità (ex 2.7): riuso di `fz_move`; dopo E1.
- **J1** — M. Prefetch nuovo (salvataggio del piano in sottofondo, record N±1, brano successivo): 300–500 B + ~1 KB di buffer.

---

## Z — Note urgenti

Richieste del committente del 15/11, da lanciare così come sono (ogni voce dice a quale modello e in quale branch). Non sono ancora
dimensionate. Finita una voce: si cancella e la decisione va nella wiki o nel README interessato.

### Z4 — Fable — Barbarian: review del gioco (altro branch)
- Fai una review anche di barbarian. Fixa bug, ottimizza la memoria e la velocità di caricamento.
