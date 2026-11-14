# TODO — lavori aperti (riscritto l'11/11/2026)

Solo ciò che resta da fare. Il fatto, con le decisioni datate, sta nella wiki (`docs/`) e, fino all'08/11, in
[docs/storico-todo.md](docs/storico-todo.md) (archivio, non si aggiorna). Le decisioni nuove si scrivono nella voce a
cui appartengono, con la data; una voce finita si **cancella** e la decisione va nella pagina della wiki interessata.

**ID** (riscrittura dell'11/11, richiesta del committente): `<lettera del capitolo><numero>`, da A1. Fra parentesi l'ID
del TODO precedente (es. "ex 3.1", "ex D4") per ritrovare le discussioni vecchie. Ogni voce: obiettivo, motivazione,
complessità (S = ore, M = 1–2 giorni, L = più giorni), cosa serve, cavilli.

Stato di riferimento (11/11, v1.195 su `main`): margine di GAME **2101 B** sotto `$8720`, 248 B nel blocco `$9C00-$9FFF`;
`SAVE_VER $C5`; test: smoke + sanity 31 in ~30 s, regression 96 (~8 min; `docs/test.md`); hardware reale mai provato.
Il branch `feature/stat-points` (v1.196, A1) ha `SAVE_VER $C6` e margine 1049 B.

| Capitolo | Contenuto |
|---|---|
| [A](#a--priorità-massima) | priorità massima: il branch dei punti statistica da provare e unire |
| [B](#b--decisioni-del-committente) | decisioni del committente che bloccano lavori |
| [C](#c--piccoli-lavori-s) | piccoli lavori (S) |
| [D](#d--prestazioni-e-memoria) | prestazioni e memoria (dai test PERF e da `docs/ottimizzazione.md`) |
| [E](#e--interfaccia-audio-testi) | interfaccia, audio, testi, manuale |
| [F](#f--formato-dei-salvataggi-un-solo-save_ver) | formato dei salvataggi (da fare insieme, un solo `SAVE_VER`) |
| [G](#g--oggetti-combattimento-bilanciamento) | oggetti, combattimento, bilanciamento |
| [H](#h--grandi-cantieri-l) | grandi cantieri: quest, capitoli, Abisso, intro, lingue |
| [I](#i--verifiche-e-misure) | verifiche e misure (nessun codice nuovo) |
| [J](#j--idee-per-dopo) | idee per dopo (bassa priorità) |
| [K](#k--frenzy-prove-in-gioco-del-committente) | Frenzy: prove in gioco del committente (11/11) |
| [M](#m--capitoli--loader-macro-capitolo-1211-committente) | **Capitoli + loader** (macro capitolo): sequenza dei capitoli, brano per capitolo, prestazioni dei caricamenti, fast loader, capitoli nel codice e bestiari |
| [T](#t--toolchain-condivisa-1411-committente) | **toolchain condivisa** fra piu' giochi: mappa della memoria automatica, estrazione in un repository a parte |

---

## A — Priorità massima

### A1 Punti statistica (unito a `main` l'11/11): rifiniture e verifiche a mano — **TOP PRIO**
- **Fatto**: branch `feature/stat-points` unito a `main` (v1.224, `SAVE_VER $C6`); schermata C in `src/game/charsheet.asm`
  (GAME, margine 2481 B). Descrizione in `docs/interfaccia.md` (riga "Personaggio") e `docs/quests.md` (gettoni respec).
- **Glifo dell'HUD da confermare** (decisione 11/11): oggi la **freccia verde in su** (`LVUP`, colore 5). Le 20 proposte restano
  in `lab/concept/hud_glyphs/hud_glyphs.png` (+ `glyphs.json`, `make_sheet.py`): il committente deve scegliere il migliore.
- **Menu**: la schermata C va **riportata alla stessa logica dei menu del villaggio** (modulo MENU, `$01 = $35`, tabella dei
  salti), da rivedere in seguito. Ostacolo: costa ~1 KB e le zone del MENU hanno liberi solo 272 B (170/9/93): serve una zona
  nuova o più spazio (il fast loader ha preso 1,2 KB di margine per il plugin di save: oggi 1998 B). Nel dungeon, inoltre, il MENU
  potrebbe non essere in memoria (si carica all'ingresso nel villaggio). Finché non si decide resta in GAME.
- **Da verificare a mano** (VICE o hardware): aprire C nel villaggio e nel dungeon (anche con mostri vicini), spendere,
  togliere, reset, confirm, respec con e senza gettoni, uscire salvando, ricaricare la partita, CON alzata = vita massima alzata.
- **Decisioni da confermare** (prese da me l'11/11): (a) **1 punto ogni 2 livelli** (9 al livello 20); (b) vita **retroattiva** su
  COS; (c) all'uscita i punti in attesa si **confermano**; (d) Fire su una caratteristica = +1; (e) nessun tetto per caratteristica.
- **Resta**: aggiornare il manuale (pagina dei tasti e dell'HUD) e la tabella delle caratteristiche in `docs/combattimento.md`.
- **Complessità**: S (verifica) + M (spostamento nel MENU).

---

## B — Decisioni del committente

Nessuna di queste è codice: sono scelte. Finché restano aperte, le voci che le citano non si possono chiudere.

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
| B11 (D-CAP-1..5, 11/11) | **Capitoli** (`docs/capitoli.md`): quanti (i piani sono **5 per capitolo**, regola dell'11/11 sera: `data/chapters.yaml` 5, 5, 5, 5 + Abisso 235 = profondità 255; piano locale da 1 in ogni capitolo, profondità globale per la difficoltà, `docs/quests.md` 3.8); dove vanno Demon e Balrog (oggi da profondità 8–9: fuori dal capitolo 1 di 5 piani); ritorno ai villaggi precedenti; piani dell'Abisso salvati (anello di K record) o rigenerati; mappe fisse nell'Abisso; difficoltà oltre la profondità 32 e oltre 255. | M9, H3 |
| B15 (11/11) | **Salvataggi con Krill più lenti** ([docs/FastLoader.md](docs/FastLoader.md) sez. 7): "save game" 3,2–5,4 → 7,1–8,6 s, locanda 3,1 → 8,5 s, scale fra piani 10–11 s (il piano lasciato si salva). Causa: il plugin riscrive il file dell'eroe intero (9 blocchi) dopo averlo letto, più la ricarica del plugin (si modifica da solo) e del villaggio. Da decidere: accettare; file più piccoli (un file per piano: più file sul disco, scelta contraria del committente); immagine del file sempre in RAM (niente lettura, ~2 KB); non salvare i piani alle scale ma solo con l'eroe. | D15 |
| B16 (11/11) | **A fine gioco: build con immagini disco diverse per drive?** (committente) Oggi solo 1541 (`_1541` nel nome). Krill supporta anche 1570/71, 1581, CMD FD, 1541U; SD2IEC solo con il ripiego KERNAL. Con tutti i drive l'install passa da 3225 a 6997 B e il plugin non si costruisce senza cambiare `save.s`. | I1 |
| B13 (11/11) | **Frenzy**: corsa massima +50% (≈40 fps fra i mostri) invece di +100% (≈34 fps)? Misure in `docs/prestazioni.md`. Si decide dopo le prove del capitolo K. | D3, K |
| B12 (11/11) | **Punti statistica**: conferma delle scelte di A1 (punti per livello, vita retroattiva, uscita che conferma). | A1 |

---

## C — Piccoli lavori (S)

### C1 (ex 1.2) Grafica della cintura nell'HUD: ampolle colorate
- Ampolle nei colori della pozione (rossa 2, gialla 7, viola 4) al posto dell'icona generica; in ricarica blu (già fatto).
  **Cavilli**: caratteri hires, colori < 8; i codici liberi dell'HUD sono finiti (`HUD_FREE`: 1 libero su `main`, 0 sul
  branch A1); da ripensare con la cintura a 8 (F1).

### C2 (ex 1.3) Portale della leva "nero"
- Il portale per l'Abisso (sala del trono) ha i colori del portale normale: palette scura. `gen_gfx.py` + atlante.

### C3 (ex 1.4) Piccole scelte estetiche e audio
- Tavolozza di PRESS SPACE (B5); `SFX_LOWHP` provvisorio da riascoltare nel JUKEBOX; tile del trono dietro il boss.

### C4 (ex 1.6) Salvataggio senza controllo degli errori di disco
- `gm_save` (`sv_all`), `chap_save`, `save_char` non controllano `KREADST` né il canale errori della 1541 (lettura del codice, **non
  verificato** con disco pieno/protetto): l'eroe può perdere i progressi senza saperlo. **Obiettivo**: avviso solo in caso
  di errore ("disk error: not saved"). **Serve**: lettura del canale 15 dopo `rel_wclose` (~30–50 B, non misurati),
  avviso nello standard dei menu, test con disco protetto (`tests/regression/saves`). **Complessità**: S-M.

### C5 (ex 1.8) CRC sui salvataggi
- Controllo di integrità (CRC-8/16 o somma) per eroe, piani, baule, verificato al caricamento; un record corrotto si
  riconosce. Cambia il formato (**`SAVE_VER`**, insieme a F): ~30–60 B di codice, tempo da misurare sui 3,1 s del
  salvataggio. Test con file corrotto (`test_rel.py`, `test_saves.py`). **Complessità**: M.

---

## D — Prestazioni e memoria

Misure e soglie: `tests/regression/perf` (PERF-10..23), [docs/prestazioni.md](docs/prestazioni.md). Ogni intervento si
misura prima e dopo con `python3 tests/run.py regression -k PERF`. Le voci D1–D6 sono le osservazioni P1–P6 di
[docs/ottimizzazione.md](docs/ottimizzazione.md) non ancora fatte: **suggerite da fare**.

### D1 (ex P1) Primo ingresso nel piano 1 dal villaggio ~12 s in VICE (poi 5,6–7,3 s fra i piani)
- Misurare cosa si legge (tema, brano, piano) col cronometro; il precaricamento del tema parte dopo N caselle e forse non
  finisce prima della cripta. Legato a J1 (prefetch nuovo). **Stima**: da misurare.

### D2 (ex P2) Minimappa del villaggio 0,64 s
- Disegno a quadranti 2×2 (`mm_quad`) per tutte le 48×48 caselle: tabella dei caratteri o solo le righe cambiate.
  **Stima**: 0,3–0,5 s in meno (non misurata).

### D3 (ex P3, ex 1.9) Frenzy e analisi del dungeon
- **11/11**: profilo per routine (`tools/vice/frame_prof.py`), ottimizzazioni semplici fatte (`mark_explored` a maschere,
  HUD a pannelli: camminata ai piani 10/12 da 45,6/44,2 a 47,6/48,1 fps), velocità della Frenzy provate fino a +250%: il
  −50% di fps non si raggiunge; a +100% (oggi) −21/−27%. Tabelle e scenari dal più semplice al refactoring in
  [docs/prestazioni.md](docs/prestazioni.md) ("Dungeon: analisi dell'11/11").
- **Da decidere (B13)**: corsa massima della Frenzy a +50% (~40 fps) invece di +100% (~34 fps). **Da fare**, in ordine:
  lavoro a turni (niente `hud_step` nei giri pesanti dello scorrimento, S-M); camera a casella in Frenzy (M); branchi di
  mostri (M, poco guadagno oggi: i lontani costano già poco); scorrimento rifatto (L). Catena degli IRQ fragile (sez. 3.4).

### D5 (ex P5) Piani pesanti: piano 14 al 14,5% di fotogrammi persi camminando (PERF-21), piano 15 al 3,8%
- Più mostri svegli: stesso lavoro di D3.

### D12 (11/11) Dall'analisi dell'assembly generato ([out/work/asm_audit/analisi_assembly.md](out/work/asm_audit/analisi_assembly.md))
- Già fatto: codice morto tolto (49 B), due `lda` inutili, un `jsr`+`rts` (+55 B di margine), commenti nei sorgenti generati.
- **Suggeriti**: routine per la casella del mostro (`mxl/mxh → pix2tile` e `myl/myh`, 4 copie ciascuno: ~46 B) e per i
  puntatori della grafica (`GFX_FSTRIP`, 4 copie: ~38 B); le altre ripetizioni sono da 8–15 B (~145 B in tutto, valutare una
  per una); START e LORE: escludere con `.if` il codice dell'altra variante (~155 B e ~180 B: solo tempo di caricamento).
  Rifare l'analisi dopo ogni lavoro grosso: `python3 tools/build/asm_audit.py` (test `ASM-10/11`).

### D7 (ex 6.1) Spawn dei mostri nella RAM sotto l'I/O
- `spawn_monsters`/`place_monster`/`place_boss`/`floor_types` (~600–800 B, da misurare) accanto al generatore
  (`gen_io.asm`). Attenzione a `gen_rammap.py`, arena, `test_gen.py`.

### D8 (ex 6.2) Codice del piano finale in overlay (`OVLF` a `$C900`)
- `gen_final` + tabelle, `ui_lever`, `at_lever`, parte di `place_boss`, `final_tick`: ~1 KB di GAME. Ospiterà Torvald (H1).

### D14 (11/11) Spazio del modulo MENU
- **Stato** (v1.223, [prestazioni](docs/prestazioni.md#menu-del-villaggio-modulo-menu-residente-1111-v122x)): locanda e
  negozi nel modulo MENU, tre zone (zona 1 `$C900-$CFFF` 170 B liberi, zona 2 `$F4E0-$FCFF` 9 B, zona 3 `$A700-$A7FF`
  93 B). Ogni modifica a locanda e negozi deve starci: per crescere, altre zone (slot sprite 20–23 `$A500-$A5FF`, 256 B;
  coda degli slot 41–47 e 58–63 dopo i buffer della musica) o codice più corto (`asm_audit`).
- **Attenzione** per D8 (`OVLF` a `$C900`) e per il buffer delle quest (`docs/quests.md`, `$CD00`): `$C900-$CFFF` ora è
  la zona 1 del MENU, che resta per tutta la partita.

### D10 (ex 6.4) Altri interventi misurati
- `SCR_H` da `$8400` a `$8800` (+224 B); musica sotto il KERNAL (0,8–1,3 KB); codice solo-villaggio su file; variabili sparse (~60 B).

### D11 (ex 6.5) Compressione ZX0 dei file rimasti
- MENU, GFX0, temi: ~5 s in meno all'avvio (stima). Decompressore pronto (`src/common/zx0.inc`).

---

## E — Interfaccia, audio, testi

### E1 (ex 2.2) Anelli `ring +N <stat>` e nomi corti (dopo B4)
- Nomi in `data/items/items.tsv` (dall'11/11 il database degli oggetti), `NAME_SHOW`, `docs/oggetti.md`, help, manuale.
  Gli id non cambiano: nessun `SAVE_VER`. **Cavillo**: la rarità del materiale va spiegata altrove.

### E2 (ex 2.3) Negozi: merce (dopo B1)
- Assortimento in `balance.yaml` (pool e `stock`), `docs/villaggio.md`, manuale.

### E3 (ex 2.4) Musica nel menu principale senza glitch
- Un brano del player del gioco avviato dal menu stesso (`src/lobby.asm`, un `SNDn`), `docs/musica.md`; `snd_io` prima del disco.

### E4 (ex 2.5) Musica nell'help (Tavern of Dawn)
- Programma HELP (release) con il brano del villaggio: player condiviso, un `SNDn` sul disco di release.

### E5 (ex 2.6) HUD: esperienza a 24 bit (per l'Abisso)
- Oltre 65535 xp: 3 cifre + K, barra a 24 bit (~100–130 B). Dipende dalle soglie oltre il 20 (H3).

### E6 (ex 2.8) Revisione completa del manuale e dell'help prima della prossima release
- Rilettura di `docs/manual/manuale_src.html`, `data/help.txt` (`gen_help.py --snap` se cambia l'HUD), screenshot
  (`tools/vice/shots_manual.sh`); impaginazione (pagine mezze vuote dopo il 09/11); figura della morte in pagina 7.

### E7 (11/11) Manuale in inglese, oltre all'italiano
- `tools/manual/gen_manual.py --lang en` è pronto (sorgente `docs/manual/manual_src_en.html`, PDF
  `Barbarian_Blood_Path_Manual_EN.pdf`; le parti generate hanno già le parole nelle due lingue): **manca il sorgente
  inglese** (traduzione di `manuale_src.html`, stesso impaginato e stessi segnaposto). Da fare a un certo punto, prima di
  una release pubblica; poi `tools/build/release.sh` produce i due PDF e il test `BUILD-04` controlla anche quello inglese.
  **Complessità**: M (testo). Legato a H5 (due build).

### E8 (ex 2.9) Player audio unico per la release
- **11/11**: il `JUKEBOX` è già su entrambi i dischi (deriva minima dev/release); **va rifatto esteticamente** (standard dei
  menu: titolo, riquadri, elenchi brani/effetti) diventando il music player della release.
- Un solo player per tutti i programmi; tabella di brani ed effetti generata in build (decisione del 09/11: niente
  lettura della directory); effetti letti una volta all'avvio; programma "music player" dal JUKEBOX con due elenchi
  (canzoni, effetti), play/pausa/stop, filtri. Dettagli e risposte alle domande del 09/11: storico in git
  (`TODO.md` fino a `22388f9`, voce 2.9). **Complessità**: M.

### E9 (ex 2.10) Stringhe del gioco in un file unico, traducibili (decisione dell'11/11)
- `data/strings.yaml` → `tools/gen_strings.py` → un `.inc` per PRG; classi di UI con lunghezza massima (`screen` 38,
  `title` ~34, `box36/26/20`, `hint` 38, `bar`, `hud`, `item` 16, `io` ~22, `ask`, `num`); sezione **Stringhe**
  dell'atlante; sostituzione nel codice file per file con confronto **byte per byte** dei PRG; test con stringhe "lunghe".
  Censimento: 289 letterali (~3,1 KB, approssimato). Prepara H5. **Complessità**: M-L. Dettagli: storico in git (voce 2.10).

---

## F — Formato dei salvataggi (un solo `SAVE_VER`)

Cambiano il blocco eroe: farle insieme (con C5 e A1 se possibile) per cambiare `SAVE_VER` una volta sola.

### F1 (ex 3.1) Cintura a 8 posti sbloccata da una quest (dopo B2)
- `c_beltt` 8 byte, 4 slot da 2 pozioni, tasti 1–4; flag nell'eroe. Regole decise l'08/11 (prima fila, la seconda sale,
  allineamento all'uscita dei menu; pozioni dal baule del dungeon come dall'alchimista). Quest scelta col simulatore.
  **Serve**: formato, HUD (due file da 4), purse, alchimista, baule, `give_item`, simulatore, eroe di prova con 8 pozioni,
  test `BELT-20..` (`BELT_SLOTS`, `BELT_KEYS` in `tests/lib/play.py`). Dettagli: storico in git (voce 3.1).

### F2 (ex 3.2) Pergamene fuori dallo zaino (dopo B3)
- Contatore 0..10 nell'eroe, icona col numero nel purse e nell'HUD, pile da 10 nel baule; cooldown ≥ 5 s.

### F3 (ex 3.3) Campi per quest e Abisso nell'eroe
- Stato quest (8 B), modalità normal/nightmare + eroe morto (1 B), capitolo `c_chap` (M9): tutti in un colpo.

---

## G — Oggetti, combattimento, bilanciamento

### G1 (ex 4.1) Obiettivi e curva (iterazione successiva del simulatore)
- Gruppo base, boss del piano ~75%, boss finale 60–70%; curva del PG più regolare; stordimento; Battle Cry 1 contro 1;
  set delle armi. `tools/simulators/fit_rules.py`, `cmp_rules.py`, `chapters.py`, arena. Rifare dopo F1 e A1 (punti statistica).

### G2 (ex 4.2) Economia: prezzi, oro, riparazioni (dopo B7)

### G3 (ex 4.3) Probabilità di uscita per ogni oggetto (stile Diablo)
- `w = R × g(livello area − livello oggetto)`; colonna `dropRate` in `data/items/items.tsv` come in DevilutionX
  (`itemdat.tsv`). Generatore, simulatore, `docs/bottino.md`. Prerequisito per gli oggetti dell'Abisso (H3).

### G4 (ex 4.4) Armi casuali (seed per oggetto)
- Seed per oggetto (+1 B a oggetto) e funzione seed → statistiche uguale in 6502 e Python. Cambia `SAVE_VER` (F).

### G5 (ex 4.5) Set di oggetti unici con nome
- Come `unique_itemdat.tsv` di DevilutionX: una tabella nel database degli oggetti; ~8 B a set + 40–60 B di codice.

### G6 (ex 4.6) Arena fase 2
- Bot che si muove, posizioni di partenza, strategie; confronto arena / simulatore. Prerequisito per H3.

### G7 (11/11) Combattere con due armi (dual wield), regole alla Diablo
- **Obiettivo**: poter impugnare due armi a una mano (niente scudo), come il Barbaro di Diablo 2 / i guerrieri di
  Diablo. **Serve**: (a) **logica nel codice**: colonna nel database (`hands` 1 = si può impugnare anche nella mano
  sinistra), posto "mano sinistra" che oggi è lo scudo (`c_eq+2`: arma o scudo), `recalc_stats` (danno e cadenza delle
  due armi: in Diablo 2 i colpi si alternano fra le due armi e la velocità è la media; nessun bonus fisso), inventario e
  locanda (regole delle due mani già presenti da estendere: con due armi niente scudo, un'arma a due mani esclude
  tutto), usura delle due armi, HUD; (b) **bilanciamento**: simulatore (`tools/simulators/rules.py` `Hero` con due armi), arena,
  confronto con arma + scudo e con arma a due mani (oggi la CA dello scudo bilancia i dadi della viking sword).
  **Cavilli**: formato dell'eroe (se serve un flag) → `SAVE_VER` (F); memoria (~100–200 B, non stimata a fondo).
  **Complessità**: M-L.

### G8 (11/11) Database degli oggetti: prossimi passi
- `data/items/items.tsv` è la sorgente di verità (11/11). Da valutare: affissi magici (prefissi/suffissi come
  `item_prefixes.tsv`/`item_suffixes.tsv` di DevilutionX) al posto del solo +N; oggetti unici (G5); requisiti
  (FOR/DES minime, colonne `minStrength`/`minDexterity`), utili con i punti statistica (A1).

---

## H — Grandi cantieri (L)

### H1 (ex 5.1) Quest system (dopo B8)
- **Versione 2.0** quando è pronto, mai prima (regola del 09/11). **Ogni villaggio nuovo**: locanda con lo stesso baule,
  la mappa fuori da `$C900-$CFFF` (zona 1 del modulo MENU), `tests/run.py regression -k VIL-MENU` (11/11: N e l'audit delle
  distanze non servono più).
- 15 quest (o 10), NPC, abilità solo da quest, tre villaggi, stanze fisse, compagno Torvald, pagine su disco (`QSTn`,
  tasto Q). Premi: cintura a 8 (F1), borsello a gradini (B9), **un gettone respec** (A1). Costi: ~1,1 KB di GAME (prima
  D7/D8), ~300 B in OVLT, ~550 B sotto l'I/O, ~60 blocchi. Analisi: `docs/quests.md`. Da rileggere col modello a capitoli (M9).

### H3 (ex 5.2) The Endless Abyss (dopo B10, B11, G6, E5)
- Piani 21+ (fino a 255) a temi casuali, livello = piano, `void.table`, boss ×1,5, spade dell'Abisso, `chestLevel`
  riscalato, solo pozioni viola; morte −10% xp; normal / nightmare; città dell'Abisso con prezzi ribilanciati; salvataggio
  dei piani (D-CAP-3). Gettoni respec nei bauli (A1, già nel branch). Test: PERF-22 (cammino nei piani 21–255, oggi
  SKIP) e PERF-23 (generatore su tutti i 255 piani: già oggi 0,34–0,84 s). Il generatore regge già i piani oltre il 20.

### H4 (ex 5.3) Intro (LORE) da rivedere tutta (a fine quest)
- Trama nuova (niente "20 piani", più città, niente cifre del bilanciamento), immagini con sprite e tile aggiornati,
  possibilmente lette dai file del gioco.
- (12/11, committente) **Riscrivere la storia in funzione dei capitoli** (4 villaggi + Abisso, 5 piani per capitolo,
  `docs/capitoli.md`): oggi il testo parla ancora di "twenty floors" (`data/lore.txt`).
- (12/11, committente) **Scorrimento**: la velocità va bene. **Interlinee**: sempre **una riga vuota** fra un elemento e
  l'altro; **due righe vuote** dove oggi ce n'è già una (`@gap 1`). Con le interlinee in più **accelerare di poco, circa
  il 4%**. Nota tecnica (non verificata): `LR_SPEED` = 6 fotogrammi per pixel, intero; il 4% (5,76) si ottiene a
  schema, p.es. 6-6-6-5 fotogrammi ogni 4 pixel (−4,2%). Da provare a occhio con VICE/emulatore; si tocca `src/lore/scroll.asm`
  e `data/lore.txt` (`tools/build/gen_lore.py`), poi test `LORE` e `docs/intro.md`.

### H5 (ex 5.4) Due build: inglese e italiano (dopo H4)
- Intro e testi delle quest nelle due lingue con gli stessi limiti di buffer e disco; con E7 (manuale) ed E9 (stringhe).

---

## I — Verifiche e misure

- **I1** Hardware reale (mai provato): avvio, Krill's Loader (caricamenti e salvataggi) su 1541 vera, `quit the game` (reset), OVL2 sotto il KERNAL, TOD
  senza 9 V AC, tempi di loader, LORE e ritorno al menu.
- **I2** Verifica a mano dal disco di release (`docs/manual-tests.md`, 10 minuti).
- **I3** Test manuale 019 (locanda): spostare un oggetto, spegnere senza RUN/STOP, riaccendere.
- **I4** B2 minimappa corrotta nel dungeon (05/11, mai riprodotto): servono screenshot e passi.
- **I5** RUN/STOP fantasma nelle build NOKEYS in VICE (solo strumenti di test).
- **I6** Glitch del brano del villaggio (hard restart): da riascoltare.
- **I7** (13/11) Licenze del secondo emulatore (`toolchain/vc64web-custom`) **prima di pubblicare il repository**: vc64web / VirtualC64
  (probabile GPL-3.0: sorgente corrispondente del wasm), librerie JS, `open-roms` (LGPL-3+, font PXLfont da verificare); le ROM
  Commodore (14 file in `toolchain/roms/vice-roms/` e la stessa copia in `toolchain/vc64web-custom/roms/`, **in git dal 13/11 su richiesta
  del committente**, che le toglierà dal repository prima di pubblicare: `toolchain/roms/roms.md` ha SHA-256, licenze e URL, **URL da verificare**)
  e le pagine generate di vc64web (`out/cache/vc64web/`, che le incorporano; anche l'immagine `c64-emu-vc64web`) non vanno pubblicate.
  Licenze di VICE (GPL-2.0), zx0 (BSD-3), cc1541 (MIT), Krill (BSD-3 con attribuzione): file nelle loro cartelle. Complessità S.
- **I8** (13/11) Segnalazioni al team dell'emulatore da riprovare a ogni nuova build: `runLoop` non esatto con un caricamento da disco
  dentro il ciclo (`framesActual` 490 su 480 nel passo del portale, `docs/emulatore.md`); il pacchetto dichiara quel caso non verificato.

---

- **I11** (13/11) **Primo avvio dei test dopo il riavvio della macchina**: `./build.sh` con smoke+sanity 9 PASS, 24 FAIL. PG-NEW-01
  si è fermato dopo 138 s con `monitor: no answer to 'x' in 120 s`, e i test che ne dipendono sono falliti a cascata.
  Rilanciato subito dopo: 33/33 PASS in 19 s. Causa **non trovata**. Ipotesi non verificata: primo avvio di VICE a freddo (cache dei
  file e dei font vuote; la macchina era accesa da 10 minuti). Da fare: riprodurre (riavvio + `./build.sh`); se si ripete, alzare
  il tempo del primo avvio o fare un avvio di riscaldamento in `tests/run_tests.sh`. Complessità S.
  13/11 sera: la macchina di lavoro si riavvia fra un messaggio e l'altro (uptime ~10 minuti a ogni ripresa); un secondo
  `./build.sh` dopo un riavvio (con immagini nuove) e' passato 33/33 al primo colpo: non riprodotto, ipotesi del freddo indebolita.
  13/11 sera, **seconda volta**, in `./build.sh --release` (toolchain nuova): 179 PASS, 6 FAIL, 1 SKIP. PERF-DISK-10..14 con
  `monitor: no answer to 'load /work/out/work/start.prg' in 20 s` (il monitor aveva appena risposto al comando prima) e PERF-OPT-11
  (MonitorError dopo 30 s); rilanciati da soli subito dopo: 6/6 PASS. Stesso sintomo (il monitor remoto di VICE smette di rispondere),
  in un momento qualsiasi della sessione, non solo al primo avvio. Da fare: registrare il log di VICE e del monitor quando succede.
  Release successiva (stessa sera, tool dentro le immagini): 185 PASS, 0 FAIL, 1 SKIP.
  **14/11, primo avvio a freddo: causa trovata e corretta** (analisi con un sottoagente Opus, riprodotto 1 volta su 1 dopo un vero
  riavvio della macchina, 0 su 3 senza): corsa all'avvio nel harness. VICE apre la porta del monitor ~7 s prima di aver finito il boot
  (disco lento a freddo), `tests/lib/c64.py` aspettava 1 s fisso; se il KERNAL non aveva inizializzato i vettori IRQ il C64 girava a
  vuoto e `x` scadeva a 120 s. I 24 FAIL erano un solo errore di setup copiato su tutti i test del modulo. Ora `Vice()` e `gen_help.py`
  usano `vice_rom.wait_boot` (vettori IRQ + `READY.`, tetto 30 s) e `Vice.close()` uccide il gruppo di processi. Provato **solo con una
  simulazione** (VICE fermato con SIGSTOP 3 s dopo l'apertura della porta: avvio del gioco ok due volte di fila; col codice vecchio
  l'analisi aveva misurato il fallimento gia' a 0,9 s di stallo) e a caldo (33/33); **non rivisto con un vero riavvio a freddo**:
  se capita ancora, e' un'altra causa. **Resta aperto** il sintomo del 13/11 a meta' sessione (PERF-DISK `load` senza risposta, PERF-OPT-11):
  non spiegato dalla corsa all'avvio. L'origine della lentezza sotto il guest (hypervisor o disco) e' un'ipotesi; dockerd dopo il riavvio
  e' fallito una volta al primo avvio (`failed to start containerd: timeout`), poi ok.

## J — Idee per dopo

- **I9** (13/11) Passaggio a Windows: deciso il 13/11 **WSL2 + container** (tutto gira in Docker, progetto nel filesystem di WSL,
  `.gitattributes` con `eol=lf`; `./validate_env.sh` controlla dove sta il progetto). Da fare allora: `./validate_env.sh`, `./build.sh`
  e `./build.sh --view` su WSL2 + Docker Desktop (mai provati: rilevamento WSL provato solo con un `mountinfo` di prova; costo di Docker
  misurato solo Linux su Linux). Complessità S.
- **I10** (13/11) Immagini Docker più piccole (non urgente): `c64-emu-viewer` 780 MB (14/11, KasmVNC: mesa e LLVM ~180 MB li vuole
  Xvnc; codec e GStreamer ~55 MB arrivano con `pulseaudio`), `c64-emu-vc64web` 2,12 GB (provare solo
  `chromium-headless-shell` di Playwright, togliere ffmpeg di sistema se basta quello di Playwright), `c64-emu-vice` 1,55 GB (con VICE dentro dal 13/11)
  (le librerie gtk3 e ffmpeg pesano ~650 MB). Misurare dopo ogni prova. Complessità S-M.
- **J1** Prefetch nuovo (salvataggio del piano in sottofondo, record N±1, brano successivo): 300–500 B + ~1 KB di buffer.
- **J2** Anello della velocità (ex 2.7): riuso di `fz_move`; dopo E1.
- **J3** Sprite del boss finale solo nel tema 8; da verificare con D8.
- **J4** Pozioni a cura fissa o a formula: confermare col committente che vada bene com'è.
- **J10** (13/11, segnalato dal committente; numero nuovo: J5-J9 sono gli ID vecchi spostati in M) **Test in parallelo**: oggi `tests/run.py` esegue i test VICE uno dopo l'altro.
  Obiettivo: più worker contemporanei, per tenere bassi i tempi man mano che i test crescono (i tetti di `CAPS` restano).
  Cosa serve: un display Xvfb per worker; porte del monitor remoto di VICE diverse; file temporanei separati in `out/tmp/<worker>`;
  test che assemblano varianti del gioco isolati (oggi riscrivono la build normale); report unico. Nel viewer: più schermi
  (`VIEW_SCREENS=N`, un Xvnc di KasmVNC per schermo e il server del viewer che li smista; stima ~30 righe e ~30–60 MB di RAM per
  schermo, non misurati). Complessità M (il grosso è nel runner, non nel viewer).
- **J13** (14/11) **Overlay del viewer (tastiera C64, Joy 1, Joy 2): prove che mancano e idee**. Provato solo in un browser headless sulla
  stessa macchina (vedi getting-started §6). Da fare: (a) schermo a sfioramento reale (telefono/tablet: multitocco stick + fire, rotazione,
  dimensioni dei tasti), (b) browser e tastiera reali, (c) **gamepad fisico**: la Gamepad API del browser vede il pad; basterebbe leggerlo in
  `live.html` e usare gli stessi `keyDown/keyUp` dei Joy 1/2 (stima: S, da provare con un pad vero). Limiti noti: i tasti vanno alla finestra sotto
  il puntatore (nessun window manager), quindi l'overlay riporta il puntatore al centro dello schermo (la finestra di VICE e' centrata: ipotesi,
  non verificata con altre dimensioni di schermo); con SHIFT a scatto i tasti senza equivalente PC (grafici C64) escono senza shift.
---

- **J14** (14/11) **Pubblicare le build quando si passera' a GitHub**: oggi le versioni stanno solo in `out/releases/` (ultime 5, locale).
  Per GitHub: asset del tag `v<V>` (disco, manuale, `manifest.json` con gli SHA-256) invece di conservarle in locale; niente zip dei
  sorgenti (regola del committente 14/11: lo da' gia' il tag). Da decidere con il passaggio a GitHub. Complessità S.

## K — Frenzy: prove in gioco del committente (11/11)

Il committente prova in gioco le proposte e poi decide (B13). Misure di partenza ([prestazioni](docs/prestazioni.md),
"Dungeon: analisi dell'11/11"): fra i mostri ai piani 10–12 la camminata normale fa ~45–48 fps; la Frenzy a +50% ~40,
a +100% (oggi) ~34, a +150% ~31, a +250% ~28–30 (il −50% non si raggiunge). Il costo è lo **scorrimento**
(`maybe_redraw`): lo schermo si scambia ogni 8 px, cioè ogni 2 fotogrammi a +100%.

Come si prepara un disco di prova (lo faccio io su richiesta, un disco per proposta, su un branch `feature/frenzy-*` con
la sua versione `tag.N`): eroe di prova al livello 15 (Frenzy disponibile), piano 10 o 12, godmode, mostri svegli; oppure
gioco normale con i soli valori di `rules.yaml` cambiati.

### K1 Corsa massima più bassa (solo dati, nessun codice)
- `rules.yaml skills.frenzy.run_max`: dischi con **50**, **75** e **100** (oggi) da confrontare a occhio fra i mostri.
- Cosa guardare: fluidità dello scorrimento, sprite che "saltano", sensazione di velocità della corsa.

### K2 Crescita più lenta della corsa (solo dati)
- `run_first` 25 / `run_step` 15 (oggi: +25% al primo colpo a segno, +15% ai successivi): con 15/10 il massimo arriva più
  tardi e le corse lunghe a +100% sono più rare. Disco con 15/10 e `run_max` 100.

### K3 Durata della Frenzy (solo dati)
- `duration` 250 fotogrammi (5 s): con 200 (4 s) il tempo passato a scorrere veloce cala del 20% a parità di corsa massima.

### K4 Camera a casella durante la Frenzy (codice, M)
- Durante la Frenzy la camera si muove a passi di 16 px (una casella) invece che a pixel: lo scorrimento lavora molto meno
  (prova del 10/11: dimezza i giri persi). La resa visiva cambia (la vista "scatta"): va vista in gioco. Disco di prova
  dopo il via del committente.

### K5 Lavoro a turni nei giri pesanti (codice, S-M; utile anche senza Frenzy)
- Niente ridisegno dell'HUD nei giri in cui lo scorrimento ha appena scambiato lo schermo o ridisegnato tutto: l'HUD si
  aggiorna un giro dopo. Guadagno stimato 1–2 mila cicli nei giri peggiori. Disco di prova da confrontare con quello di oggi.

### K6 Combinazioni da provare per ultime
- K1 (75) + K5; K1 (100) + K4. Esito delle prove: annotarlo qui con la data, poi decisione in B13 e voce chiusa.

---

## M — Capitoli + loader (macro capitolo, 12/11, committente)

**Per lavorare: "fai il capitolo M".** Qui sono riuniti tutto il lavoro dei capitoli e le attività rimaste del fast loader,
con quanto discusso e deciso il 12/11 (le voci originali D15, H2, H6, J5-J9 e la vecchia sezione L sono state spostate qui;
gli ID vecchi sono fra parentesi).

**Fatto il 12/11** (nella wiki, non si rifà): salvataggi solo a "save game"/nuovo eroe/cambio di capitolo, piani del capitolo
in RAM ([salvataggi](docs/salvataggi.md)); grafica per capitolo `GFX1..8`; sequenza dei capitoli con segnaposto
([capitoli](docs/capitoli.md)); un tema audio per capitolo ([musica](docs/musica.md)); `HELP` compresso
([help](docs/help.md)); errore d'install di Krill gestito e test dei drive ([FastLoader](docs/FastLoader.md)); tetti di
durata dei test ([test](docs/test.md)); fast loader provato nell'emulatore web vc64web.

**Ordine proposto**: M1 (resti, servono decisioni) → M3 (prestazioni) → M9 (contenuti veri dei capitoli) → M4/M5/M8
(loader, indipendenti) → M2, M7 (piccoli o in attesa di decisioni / ROM / hardware).

### M1 Sequenza dei capitoli: cosa resta (la sequenza con i segnaposto è fatta il 12/11, [capitoli](docs/capitoli.md))
Fatto il 12/11 (branch `capitoli`): `c_chap`/`c_unl` (`SAVE_VER` $C7), villaggi `TWN1..4` (copie), cripta al primo piano
del capitolo, piani del boss 5/10/15 con `BOSSCHc` segnaposto e boss con lo sprite del boss finale, sblocco alla sua morte,
sentiero di uscita a nord con la casella generica `=` e `travel to next chapter` → villaggio dopo (test `CHAP-SEQ-10..14`).
**Resta**:
- **Effetto grafico del passaggio** di capitolo (oggi: schermo nero, poi le schermate di salvataggio e caricamento): tbd.
- **Villaggi 2–4 veri** (mappa, tile, NPC): oggi copie; le costanti del villaggio (`TOWN_*` in `levels.asm`: portale, cripta,
  ingresso; `tx_exit`; porte per la minimappa `tp_*`) valgono per tutti e vanno trasformate in una tabella per capitolo
  (o in un'intestazione del file `TWNc`, come per `BOSSCHc`). La mappa RLE del villaggio è a 1718 B su 1792 (`TOWN_MAX`).
- **Mappe vere dei boss** (`data/maps/bosschapN.txt`) e **boss veri** (statistiche, sprite e IA propri: M9/H6). Oggi il boss è
  il boss con nome del piano (statistiche del piano) con lo sprite del boss finale; nessun altro mostro, nessun bottino
  speciale, la sala non si chiude.
- **Ritorno ai villaggi precedenti** (portale/menu): fuori da questa fase (D-CAP-2).
- **Tile di accesso al dungeon generico**: la cripta (`T_TSTAIRS`, `>`) è già un tile che si mette dove si vuole; se un
  villaggio ne avrà più d'uno con destinazioni diverse servirà una tabella (non fatto, utilità da confermare).
- **Tempi del disco** (misurati il 12/11 con 42 file sul disco): tema 1,34 s (era 0,98), `load_char` 2,84 s (3,04 s dopo le modifiche al loader del 12/11 sera: limite del test 3,4 s; stessa causa non capita, M3), save nel
  villaggio 9,45 s (soglia del committente 9,5 s: margine 0,05 s), ingresso nel villaggio 4,85 s. I tempi crescono con il
  numero di file (non capito perché: M3). Limiti dei test miei (non del committente) alzati alla misura.

(12/11, committente) **Confermato**: un tema grafico dei livelli per capitolo (`GFX1..8`, fatto) va bene così.

### M2 Temi audio veri dei villaggi (12/11)
- Fatto il 12/11: un brano per capitolo (`PLAYLIST` `town`/`level`, `snd_town_c`/`snd_lvl_c`), il brano non si rilegge se è
  già nel buffer ([musica](docs/musica.md)); scale 2,80 → 2,24 s (misurato). IRQ solo-suono e fade più corti: scartati.
- **Resta**: scegliere i temi dei villaggi 2–4 (oggi tutti Tavern of Dawn, tbd) ed eventualmente i temi dei boss dei capitoli
  (oggi il piano del boss usa il tema del capitolo).

### M3 Prestazioni dei caricamenti (ex J9)
- **Stato (12/11 sera, VICE, 42 file sul disco)**: scale nello stesso capitolo **2,24 s** (`PERF-DISK-13`; obiettivo del
  committente < 2 s), ingresso completo nel villaggio 4,8-4,9 s (`PERF-DISK-14`), tema `GFXn` 1,34 s, save nel dungeon
  8,3-9,3 s, save nel villaggio 9,45 s. Limiti in `tests/regression/perf_disk` (quelli del committente portati a misura +
  0,1 su sua indicazione: scale 4,0, save 9,4 / 9,6 s).
- **Da capire**: (1) i tempi crescono con il numero di file sul disco (30 → 36 → 42 file: tema 0,98 → 1,34 s, menu 1,96 →
  2,98 s) e non in modo monotono (prove con 32/33 file); (2) lo stesso test varia fra un run e l'altro (save nel dungeon
  8,26-9,26 s) secondo la posizione della testina lasciata dal test prima. Sospetti: ricerca nella directory di Krill e
  posizione dei settori (non verificato). **Provato e scartato**: file usati spesso vicino alla traccia 18 (`cc1541 -r 16`):
  peggiora.
- **Leve per le scale < 2 s** (non provate): non rileggere il tema `GFX(2c−1)` se non cambia (stima ~0,9 s; ma la regola del
  committente è "nessuna cache se i limiti reggono"); un solo file per tema + brano; meno file sul disco (es. un solo file
  per i 4 villaggi segnaposto finché sono uguali).
- (12/11, committente) **Test di prestazioni con tutti i file già sul disco**: misurare con il disco al completo, cioè
  con i file previsti a fine lavoro (villaggi, mappe dei boss, bestiari, temi) anche se ancora segnaposto, non con quelli
  di oggi; i tempi crescono con il numero di file, quindi le misure di oggi sono ottimistiche. **Da chiarire con il
  committente** se intendeva questo o solo "il disco di oggi, tutti i file presenti" (come già `PERF-DISK`, 42 file).
- (12/11, committente) **Testina del drive posizionata in anticipo** quando non c'è nulla da caricare: valutare fattibilità,
  costo e vantaggio reale. Valutazione iniziale, **non misurata**: (a) il vantaggio possibile è solo il tempo di passo
  della testina (la rotazione del disco non si può anticipare); si recupera solo se il prossimo file sta su una traccia
  lontana dall'ultima usata; (b) servirebbe un comando al drive "vai alla traccia N" senza trasferire dati: non so se il
  residente di Krill lo offre (da leggere nel sorgente `loader/`), altrimenti una lettura di un solo blocco del file
  successivo; (c) quale file sarà il prossimo non sempre si sa (scale: tema + brano; save: file dell'eroe e `hl`);
  (d) la variabilità dei test (save nel dungeon 8,26–9,26 s secondo la posizione lasciata dal test prima) è compatibile con
  l'effetto della testina, ma è un sospetto. **Passo 0 (poco costoso)**: misurare in VICE quanto pesa la partenza da una
  traccia lontana (stesso caricamento con la testina vicina e lontana); se il guadagno è piccolo si lascia. **Se il costo
  è troppo alto si fissa un valore massimo e quello resta come guardia** (regola del committente).
- Profilo del cambio piano (12/11, prima del brano per capitolo, 2,64 s): fade 0,18 s, tema 1,17 s, brano 0,78 s,
  generazione 0,29 s, resto ~0,2 s.

### M4 Plugin di save di Krill ottimizzato (ex J5)
(11/11, committente) **Reverse engineering del plugin di save di Krill** e una versione nostra con la
  **scrittura su disco ottimizzata**. Misurato (11/11 sera, analisi dello schema dei file, chiusa: un file per eroe): ~3,8 s fissi per chiamata + ~0,25 s per blocco.
  Dal sorgente (`loader/src/save.s`, `customdrivecode.s`): a ogni chiamata `swapdrvcod` salva nel buffer da 2 KB del C64
  il codice del loader che sta nel drive, carica nel drive il codice di scrittura, scrive, poi rimette il codice del
  loader; il nome del file viene scritto dentro il plugin stesso (i byte che cambiano). Quanto pesa ogni fase **non è
  misurato**. Piano: (0) profilo delle fasi in VICE (cronometro del C64 e del drive), ~2-3 ore; (1) plugin che non si
  modifica / si ripristina da solo: niente ricarica di `KSAVE`, −0,5 s, ~mezza giornata; (2) più file o più parti in una
  sola sessione del drive (uno scambio del codice per "save game" invece di due) o scrittura dei soli blocchi cambiati,
  ~2-4 giorni, utile solo se lo scambio è la parte grossa; (3) scrittura dentro il codice residente del drive senza
  scambio: settimane, poca RAM libera nel drive, alto rischio. Implica: una versione modificata di Krill (patch applicata
  dalla build sullo zip intatto, `tools/build/krill_build.sh`; licenza BSD: resta "Loader by Krill", con la modifica dichiarata),
  codice del drive con tempi critici provato solo in VICE (rischio sull'hardware reale, I1), aggiornamenti futuri di
  Krill da riportare a mano. Complessità: dal passo 1 al 2, M.

### M5 Altri passi del fast loader (ex J6, parte rimasta)
- **`BARBARIAN` con Krill** (install in BARBARIAN, tastiera senza KERNAL: il residente occupa le variabili del KERNAL in
  pagina 2; trampoline su `loadraw`): accelererebbe la lettura di `START` (e di `HELP`, oggi compresso: 15 blocchi). L.
- **GAME con il decompressore di Krill** (`loadcompd`): nuova build di Krill con il decompressore. M.
- **Ripiego KERNAL** per i drive non supportati (con B16): oggi un drive non supportato dà il messaggio di `kr_fail`.
- (12/11, committente: **scartati** IRQ solo-suono durante i caricamenti e fade più corti.)

### M7 Test del fast loader su 1570/1571 (resto dell'ex J8)
- Fatto il 12/11: errore d'installazione con messaggio e ritorno a `BARBARIAN` (`kr_fail`, test `KRILL-14`), 1541-II in VICE
  (`KRILL-17`). **Resta**: 1570/1571 (`KRILL-18`, SKIP: servono le ROM `dos1570`/`dos1571` in `/usr/share/vice/DRIVES` o
  un drive vero; I1). Nota: un vero errore d'install non si riesce a provocare in VICE (senza drive vero il KERNAL non
  carica nemmeno START), il test salta l'install e simula l'errore.

### M8 Cosa reintrodurre del fast loader (ex D15)
- Krill's Loader è nel gioco (ramo `fast-loader`, [docs/FastLoader.md](docs/FastLoader.md)). Cache e precaricamento sono
  stati tolti prima: **da decidere con il committente quali reintrodurre** guardando le misure (villaggio → piano 1 3,1 s,
  modulo MENU 2,3 s, tema ~1 s): oggi nessuna sembra necessaria per i caricamenti; i salvataggi sono il problema (B15).
- Da provare su hardware reale (I1). Emulatore web del committente: **vc64web funziona** (12/11, `docs/FastLoader.md` sez. 8).

### M9 Capitoli nel codice e bestiari (ex H2, H6)
- Analisi: [docs/capitoli.md](docs/capitoli.md). Già divisi per capitoli: `data/chapters.yaml` (`tools/build/chapters_db.py`:
  **piano locale** 1..n che riparte in ogni capitolo, **profondità globale** 1..255 che regola la difficoltà; decisione del
  committente dell'11/11, `docs/quests.md` 3.8), atlante grafico, `tools/simulators/chapters.py`, bestiari per capitolo
  (`data/monsters/bestiary.tsv`, [bestiario](docs/bestiario.md)). Fatto il 12/11 (M1): `c_chap`, villaggi e mappe dei boss
  per capitolo, passaggio di capitolo, gruppo di 5 = capitolo. **Da fare nel codice**: bestiario del capitolo caricato col villaggio (stesso numero di tipi, così la RAM non cresce; oggi i 4 capitoli usano
  gli stessi tipi, con la difficoltà del piano globale); nomi dei tipi per set (`src/game/bar.asm`); boss veri dei
  capitoli. **Complessità**: L.

**Bestiari dei capitoli 1–4 (ex H6)**
- Concept in [docs/bestiario.md](docs/bestiario.md): boss nuovo del capitolo 1 (The Hollow Abbot), mostri e boss dei
  capitoli 2–4, Lord of Ruin nel capitolo 4. **Serve**: taratura (prima simulazione: Abbot 13%, Miller 97%, Varok 100%:
  da rifare con `fit_rules.py`), sprite (3 comuni + 1 boss per capitolo), IA nuove (distanza, carica, teletrasporto,
  evocazione: da scegliere), H2. **Complessità**: L.

---

## T — Toolchain condivisa (14/11, committente)

Decisioni del 14/11: la toolchain diventera' un repository a parte, **senza submodule**: versione nelle immagini (`c64-builder:1.3`),
comando dell'host **`c64t`** (`c64t init` crea un progetto chiedendo nome e informazioni, scrive il `.env`); nel gioco restano sorgenti,
grafica, dati, testo del manuale, test e i generatori propri. Il codice 6502 di librerie esterne (Krill, decompressore zx0) resta
**nel gioco** con la sua versione; nella toolchain solo i programmi dell'host (cc1541 dal suo sorgente, non dallo zip di Krill).
VS Code: niente per ora. Prima la mappa della memoria (T1), poi il resto (T2).

### T1 Mappa della memoria automatica: aggiunte
- Fatto il 14/11: `toolchain/memmap/c64map.py` (generico, nessuna configurazione) -> `out/work/memory-map/index.html` + `memmap.json`:
  moduli dai listati di 64tass collegati al disco, panoramica per pagine, strati, spazio libero per banco, moduli nella stessa memoria,
  pagina zero / I/O / KERNAL per modulo, disco completo. Pagina in [docs/build.md](docs/build.md) sezione 4.
- **Verifica in VICE** (la piu' utile): RAM riempita con uno schema noto dopo il boot, poi gli scenari dei test (smoke, sanity,
  regression), poi lettura della memoria: i byte ancora uguali allo schema non sono mai stati scritti. Darebbe l'uso **vero**
  (dati copiati all'avvio, buffer dietro puntatori, schermo, sprite, decompressioni) che l'analisi statica non vede. Cavilli: un byte
  scritto con lo stesso valore dello schema sembra intatto (schema senza $00/$FF/$20, o due passate con schemi diversi); i test che
  partono con `-autostart` vanno riempiti prima del caricamento; tempo dei test in piu' (da misurare). **Complessita'**: M.
- **Annotazioni facoltative nei sorgenti** (es. `;@map "grafica fissa, morta dopo copy_gfx" free-after=start`) per descrizioni e
  dati che diventano liberi dopo l'avvio: senza, oggi il margine di 2333 B sotto `$8720` (asm.sh) non si ritrova nella mappa
  automatica, perche' `gfx_data` resta occupato. **Complessita'**: S-M.
- **Scenari** (quali moduli stanno in memoria insieme): oggi i moduli caricati a turno sono sommati e ogni scheda dice lo spazio
  libero con il solo modulo; gli scenari veri verrebbero dalla verifica in VICE o da un elenco facoltativo.
- **Coppie di etichette** inizio/fine (`x`/`x_end`) per nominare zone senza annotazioni: dipende da come ogni progetto chiama le etichette.
- **Mappe vecchie** (`tools/memory-map/gen_rammap.py`, `gen_diskmap.py`: `mappa_ram.html`, `mappa_disco.html`, curate a mano, con
  scenari e verifiche in VICE): restano finche' la mappa automatica non ha annotazioni e verifica in VICE; poi si tolgono e le
  descrizioni passano nelle annotazioni. La pagina automatica le collega ("Altre pagine").
- Una misura generica nel manifest per il viewer (`memmap.json`: RAM libera, blocchi liberi) cosi' ogni progetto ha l'andamento
  della memoria senza scrivere codice.

### T3 Toolchain in inglese (14/11, regola del committente)
- Tutto `toolchain/` in inglese: `README.md`, script (`run.sh`, `images.sh`, `viewer.sh`, `validate_env.sh`), `viewer_player.py`,
  Dockerfile, server e pagine del viewer (`index.html`, `live.html`, `server.js`), `vc64web-custom/`. Fatto: `memmap/c64map.py`.
  Cavilli: i messaggi degli script che i test o la wiki citano alla lettera vanno aggiornati insieme. **Complessita'**: M.

### T2 Estrazione della toolchain in un repository a parte
- Piano da preparare dopo T1 (14/11): rendere `toolchain/` autosufficiente (dentro: `tools/vice/` generici, `tests/lib/` motore dei
  test, `publish.py`, cache dei passi, versioni), immagini con la versione nel tag, comando `c64t` (`init`, `build`, `test`, `view`,
  `play`, `images`, `doctor`, `upgrade`), container generico del manuale (WeasyPrint + tema "manuale C64" + tasti `<kbd>`), progetto
  di esempio che prova che la toolchain e' davvero generica, prova da ambiente pulito.

