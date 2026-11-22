# Quest system: come implementarlo (documento usa e getta, 22/11)

**File temporaneo** (regola del `CLAUDE.md`: si cancella a lavoro finito; le decisioni passano in `docs/wiki/quests.md`).
Serve a chi implementa il TODO H1. Fonti:

- **Regole e trama**: [docs/wiki/quests.md](docs/wiki/quests.md) (Q1–Q16, The Blood Tithe, premi).
- **Definizione di tutte le quest, con i testi**: [data/quests/next/quests.yaml](data/quests/next/quests.yaml) (22/11: 12 passi della
  catena, 15 accessorie, 6 modelli ripetibili; controllata dal test `QUESTDB-NEXT-10`). In questo documento ogni quest è citata
  con il suo `id` in quel file (`1`..`12`, `a1.1`..`a4.3`, `r.cull`..`r.offering`): testo d'offerta = campo `text`, riga gialla
  = `goal_text`, consegna = `done`.
- **Unici dati dalle quest**: `data/items/next/uniques.tsv` (nel gioco dal 22/11: suffisso `$80 + u`).

Le voci marcate **proposta** nel file (`proposal: true`) non sono ancora approvate dal committente: premio del passo 2
(*tam's amulet*), premi di `a1.3` e `a3.4` (chiarimento C6), *bottle tree* in `a2.1`, cintura a 8 in `a2.2` (P3).

---

## 1. Cosa c'è già nel codice (concept del 17–21/11)

| Pezzo | Dove | Stato |
|---|---|---|
| Pagina Q (elenco e dettaglio) | `src/qpage.asm` → file `QST0` (codice + indice), caricata a `QBUF` = `SCR_B`; testo di una quest nel file `QSTn` letto a `QTXT` = `$B000` | funziona con 8 quest segnaposto; **`QST0` è pieno** (1021 B su 1024) |
| Stato | `c_qst` (1 byte nel blocco dell'eroe: maschera delle quest prese) | da sostituire |
| NPC | `src/game/quest.asm` (variabili in `BFP`, ingressi), modulo MENU: `src/menu/npc.asm` (zona 5), `npc_tick.asm` (zona 6), `npc_here.asm` (zona 1), `npc_look.asm` (zona 3) | NPC fissi con nome al loro posto (`npc_fix`, `tk_fix`), vaganti con "!" 1 volta su 4; solo Hilde dà la quest 1 |
| Generatore dei file | `tools/build/gen_quests.py` da `data/quests.yaml` | 8 quest, testo in codici schermo |
| Capitoli | `src/game/chapter.asm`: `chap_won` (morte del boss → `c_unl`), `exit_open`, `chap_travel` | lo sblocco è alla morte del boss, non alla consegna |
| Abilità | sbloccate dal solo livello (3, 6, 9, 12, 15) | manca la condizione della catena |
| Borsello | `GOLD_MAX` costante (`add_gold16`, `purse_room`) | deve diventare una variabile |
| Cintura | 4 posti | 8 posti = TODO F1 |
| Gettone respec | `c_resp` | c'è |

Memoria (misure del 22/11, da rifare prima di cominciare): GAME 1973 B di margine; CORE 62 B; zone del MENU piene (lo stampa
la build); blocco dell'eroe `CHRBLK` 254 B con il vincolo `HERO_LEN - LV_SLOT <= 255` (`rel.asm`); disco con circa 70 blocchi
liberi (da verificare con `lab64 map`).

---

## 2. Architettura proposta

### 2.1 Tre moduli, come per il MENU
Il quest system non sta in GAME: quasi tutto il suo codice serve solo nel villaggio o nella pagina Q.

1. **Motore residente (GAME, obiettivo ≤ 350 B)**: solo gli agganci che scattano nel dungeon e lo stato.
   - `q_kill` (da `kill_monster`): contatori K, B, P, e tiro degli oggetti di quest (I da mostro).
   - `q_chest` (apertura del baule del piano): oggetto di quest I "da baule".
   - `q_cboss` (da `chap_won`): obiettivo C.
   - `q_gate` (scala del piano prima del boss): cancello Q14.
   - `q_done`: segna "da riscuotere", lampo e suono, riga nella barra dei messaggi ("quest complete").
2. **Modulo del villaggio (file su disco, caricato con il MENU o al suo posto in una zona)**: offerta, accettazione, consegna,
   premi, estrazione delle ripetibili. Gira solo con il PG accanto a un NPC. Proposta: un file **`QGIV`** caricato a `QBUF`
   (= `SCR_B`, 1000 B) quando si preme Fire accanto a un NPC, come oggi `QST0`. Così non pesa sulle zone del MENU.
3. **Pagina Q (`QST0`)**: solo lettura dello stato, elenco e dettaglio. Va riscritta sul formato nuovo dei testi (sotto) e con
   la riga gialla calcolata dallo stato (Q16).

### 2.2 Dati su disco
- **`QIDX`** (o in testa a `QGIV`): tabella di tutte le quest non ripetibili, 8 B l'una (27 quest = 216 B):
  `capitolo/tipo` (3 bit + 2), `NPC che la dà` (4 bit) e `NPC che la ritira` (4 bit), `prerequisito` (id, 0 = nessuno),
  `obiettivo` (tipo 3 bit + parametro: tipo di mostro o piano), `quantità`, `1/k` della caduta, `premio` (indice in una tabella
  di premi), `oggetto di quest` (3 bit).
- **Tabella dei premi**: righe da 4 B: oro (in decine, 1 B), codice 1 (abilità / borsello / cintura / gettone), codice 2 (unico
  `$80 + u`, oppure "oggetto magico della categoria c"), pozioni (colore × quantità in un byte).
- **Testi**: un file per quest come oggi (`QSTn`, n in base 36: `QST1`..`QSTR` per 27 quest + 6 modelli = 33 file da 1–2
  blocchi) con `title`, `goal_text`, `text`, `done` **a 5 bit** (TODO H7: codificatore in `gen_quests.py` con la tabella della
  macro `t5`, stampa con `ui_puts5` / `d5_get` di GAME). I testi di `quests.yaml` usano già solo i caratteri della tabella.
  Stima: testo medio 330 caratteri → ~210 B a 5 bit; con `done` e titolo ~350 B: **2 blocchi** a quest, ~66 blocchi in tutto.
  Se il disco non basta: `text` e `done` nello stesso blocco con ZX0 (decompressore già in GAME), o un file per capitolo.
- `tools/build/gen_quests.py` va riscritto su `data/quests/next/quests.yaml`; quando il gioco lo legge, il file passa a
  `data/quests.yaml` e la cartella `next` sparisce.

### 2.3 Stato nell'eroe (32 B, `SAVE_VER` nuovo)
Come deciso in `quests.md` 4.3:

| Campo | Byte | Contenuto |
|---|---|---|
| `q_step` | 1 | passi della catena **consegnati** (0..12) |
| `q_flag` | 1 | bit 0 passo corrente preso; bit 1 obiettivo raggiunto (da riscuotere); bit 2–3 liberi; bit 4–7 gradino del borsello / cintura a 8 |
| `q_cnt` | 1 | contatore del passo corrente |
| `q_sdone` | 2 | accessorie fatte (15 bit) |
| `q_side` | 4 × 2 | 4 accessorie attive: id (bit 7 = da riscuotere), contatore |
| `q_rep` | 2 × 5 | 2 ripetibili: modello e capitolo, parametro (tipo o piano), quantità, contatore, premio (bit: pozioni, oggetto) |
| `q_item` | 2 × 3 | oggetto premio preparato per le 2 ripetibili (id, prefisso, suffisso) |
| liberi | 3 | |

Abilità sbloccate, tetto del borsello e testo della pagina si **ricavano** da `q_step` (tabelle di 13 B in `QGIV` e 5 B in
GAME per le abilità: `sk_step` = passo minimo 2, 4, 6, 8, 9).

**Dove metterli**: il blocco dell'eroe è pieno (254 B). Due strade:
- (a) baule della locanda fuori dal blocco (`st_*`, 120 B) in un secondo blocco del file `save-0N`, come nel progetto F7
  ("baule della locanda sotto l'I/O"): libera 120 B, costa una modifica a `rel.asm` e a `stash.asm`;
- (b) i 32 B delle quest in coda al file dopo i piani (offset `HERO_LEN + 5 × LV_SLOT`), letti e scritti con il blocco:
  più semplice (il file ha già 739 B su 3 blocchi = 762), ma restano 23 B − 32: **non ci sta**, serve un quarto blocco.

Consiglio (a), che era già approvato. Va deciso prima di scrivere il motore (cancello G2).

---

## 3. Il motore residente

### 3.1 Tabella degli obiettivi attivi (in RAM, non salvata)
All'ingresso in un piano (`load_location`) e dopo ogni consegna, il modulo del villaggio o una routine corta di GAME
ricostruisce una tabella `qa_*` di al massimo **7 voci** (1 catena + 4 accessorie + 2 ripetibili):

```
qa_ty   tipo: 0 vuota, K, B, P, I-da-mostro, I-da-baule, C     (1 B)
qa_par  tipo di mostro 1..8 (K, I), piano (P, B, I-da-baule; 0 = qualsiasi)   (1 B)
qa_k    1/k della caduta (I-da-mostro)                          (1 B)
qa_n    quantità da raggiungere                                 (1 B)
qa_ptr  indice del contatore nello stato salvato                (1 B)
```

35 B di variabili. Il motore nel dungeon guarda solo questa tabella: non conosce le quest. La costruisce `QGIV` quando è in
memoria (villaggio) e la tabella **si salva con lo stato del piano o si ricostruisce** leggendo `QIDX` all'avvio di una partita
("continue" dal villaggio: nessun problema; "continue" non parte mai dentro un piano).

### 3.2 Agganci

| Aggancio | Dove | Cosa fa | Costo (stima) |
|---|---|---|---|
| `q_kill` | `kill_monster` (`game.asm`), dopo `ovp_kill` | per ogni voce: K se `mtype == qa_par`; P se `cur_level == qa_par`; B se il mostro è il boss con nome (`mon_boss`) e piano giusto; I-da-mostro se tipo giusto e `rand < 256/k`. Incrementa il contatore fino a `qa_n`, poi `q_done` | ~110 B |
| `q_chest` | apertura del baule del piano (`ui.asm`, baule del piano) | I-da-baule: se `cur_level == qa_par` e il baule è **il baule del boss con nome** del piano (così è uno solo e si sa dov'è), contatore + 1 e messaggio "found: tam's amulet" nella riga 23 | ~40 B |
| `q_cboss` | `chap_won` (`chapter.asm`) | obiettivo C della catena raggiunto; **non** tocca più `c_unl` | ~15 B |
| `q_gate` | scala verso il piano del boss (`change_level` o `tile_trigger`) | Q14: se il passo "uccidi il boss" (3, 6, 9, 12) non è preso, la scala è chiusa: messaggio "the way is sealed" (chiarimento C3: proposta = messaggio, niente tile nuovo) | ~30 B |
| `q_done` | interno | bit "da riscuotere", `set_flash`, effetto sonoro, etichetta "quest complete" | ~35 B |
| abilità | controllo del livello minimo (dove oggi si confronta `c_lvl`) | in più `q_step >= sk_step[abilità]` (Q15) | ~20 B |
| borsello | `add_gold16`, `purse_room` | `GOLD_MAX` diventa `q_purse` (2 B, ricavata da `q_step` a ogni caricamento e consegna) | ~25 B |
| sblocco del capitolo | `exit_open` (`chapter.asm`) | `c_unl` cresce alla **consegna** dei passi 3, 6, 9 (lo fa `QGIV`) | 0 B in GAME |

Totale residente ~275 B + 35 B di variabili. Q10 (la morte non tocca le quest) e Q13 (si conta solo dopo aver preso la quest)
sono automatiche: la tabella esiste solo per le quest prese e `player_die` non la tocca.

### 3.3 Oggetti di quest
Sono contatori (Q8): niente zaino. Nomi in `quest_items` del file: servono solo al messaggio "found: ..." e alla riga gialla.
Caduta da mostro: tiro in `q_kill` (non in `roll_loot`: così non cambia il bottino). Baule: vedi `q_chest`.

---

## 4. Il modulo del villaggio (`QGIV`)

Fire accanto a un NPC (`npc_here` → oggi `npc_take` in `src/menu/npc.asm`): si carica `QGIV` a `QBUF` e gli si passa il
numero dell'NPC (nome `k` di `tk_fix`, o "vagante"). Sequenza:

1. **Consegna**: se l'NPC ritira una quest "da riscuotere" (catena: `turn_in`; accessorie; un vagante qualunque per le
   ripetibili, Q4): controlla lo zaino (Q12: se il premio ha un oggetto e lo zaino è pieno, messaggio "your pack is full" e
   la quest resta da riscuotere), dà il premio, mostra `done`, aggiorna lo stato (`q_step`+1, bit dell'accessoria,
   ripetibile di nuovo nel mazzo).
2. **Obiettivo G / V**: se la quest attiva dell'NPC chiede oro (`a1.2`, `a2.4`, `a3.4`, `r.offering`): "give N gold? yes/no"
   (`ui_yesno` c'è già); con l'oro giusto la quest è subito consegnata. V (`a3.4`): il Fire è sul falò (`tile_trigger` della
   cura) con la quest attiva.
3. **Offerta**: la prima quest dell'NPC non presa e offribile: catena = passo `q_step + 1` se l'NPC è il suo `giver` e il
   capitolo è giusto; accessorie = dopo il primo passo della catena del capitolo (Q9), prerequisito `after` fatto, meno di 4
   attive (Q2). Catena e accessorie si prendono subito (Q11) e si apre il dettaglio (`text`). Ripetibili: i vaganti con il
   "!" estraggono modello e parametri (tabella per capitolo) e chiedono **accept / decline**.
4. Ricostruisce `qa_*` e torna al gioco (`ui_exit`).

**Il "!"**: oggi lo decide `npc_q` (zona 5 del MENU). Regola nuova: "!" giallo sopra chi ha qualcosa da **offrire**, "?"
(o "!" di un altro colore) sopra chi ha qualcosa da **ritirare**. Serve una routine corta che, entrando nel villaggio,
riempia `npc_q` dai dati di `QIDX`: proposta = la fa `QGIV` stesso, caricato una volta all'ingresso nel villaggio dopo il
MENU (costo: un caricamento di 4 blocchi in più, ~0,4 s; in alternativa i 27 × 2 byte "chi dà / chi ritira" in GAME).

**Premi** (routine uniche in `QGIV`):
- oro: `add_gold16` (rispetta il borsello: prima si alza il tetto, poi si dà l'oro);
- pozioni: `give_item` nella cintura o nello zaino;
- unico: `ap_s = $80 + u`, `ap_b = 0`, `add_to_pack` con la base `un_base[u]` (la durabilità la tira `dur_roll`, `af_dur`
  applica DUR e indistruttibile);
- oggetto magico: `af_gen` con `af_m = 1` (magico d'ufficio) e `af_l` = livello del boss del capitolo. **Attenzione**: `af_gen`
  gira sotto l'I/O e le sue tabelle ci sono sempre, ma `gen_item` sceglie la base con `lt_scan`: nel villaggio funziona
  (chiarimento C4 risolto: non serve preparare l'oggetto nel dungeon; `q_item` nello stato serve solo se si vuole mostrare il
  premio delle ripetibili **prima** di accettare);
- abilità: nessun dato da scrivere (si ricava da `q_step`), solo il messaggio "you remember: whirlwind";
- borsello, cintura a 8, gettone (`c_resp`), reliquia (solo testo).

---

## 5. Pagina Q

Riscrivere `src/qpage.asm` (oggi 1021 B con l'indice dentro):
- l'indice (capitolo e titolo) esce dal file: i titoli stanno in testa ai file `QSTn` e l'elenco legge solo quelli delle quest
  attive (al massimo 7 letture da 1 blocco: ~0,15 s l'una; oppure un file `QTIT` con tutti i titoli a 5 bit, ~330 B);
- riga gialla = `goal_text` con `{n}`/`{t}` sostituiti dal contatore (`qa_*` / stato) (Q16); riga del premio generata dalla
  tabella dei premi ("120 gold, osric's cudgel");
- "abandon" solo sulle ripetibili (Q7);
- testo a 5 bit con `d5_get`; andata a capo a build time (`gen_quests.py`, 36 colonne) come oggi.

---

## 6. Le quest, una per una

Per ognuna: testi nel file (id), cosa serve nel motore, note. **Tipi di mostro** = tipo 1..8 del capitolo (ordine di
`docs/wiki/bestiario.md`).

### 6.1 Catena (testi: id `1`..`12`)

| Id | Titolo | Motore | Note di implementazione |
|---|---|---|---|
| 1 | a sword for the crypt | K tipo 1 (fallen) × 8 | premio: tetto del borsello 1000 (gradino 1), *osric's cudgel* (u = 0). **Partenza**: oggi l'eroe nasce con 100 monete e `GOLD_MAX`; il tetto iniziale 500 va messo in `levels.asm` |
| 2 | the widow's son | I da baule, piano 3, 1 oggetto | la dà **Hilde**, si consegna a **Osric** (`turn_in`): il "!" passa da Hilde a Osric quando l'amuleto è trovato. Whirlwind: `sk_step[0] = 2`. Premio proposto *tam's amulet* (anello) |
| 3 | the abbot's censer | C | `q_gate`: la scala del piano 4 è chiusa finché il passo non è preso. Alla consegna `c_unl = 2` (l'uscita del villaggio si apre). Il testo `done` dice dove andare (traghetto) |
| 4 | the silent village | K tipo 1 del capitolo 2 (drowned) × 12 | Battle Cry (`sk_step[1] = 4`), borsello 3000 |
| 5 | dolls with names | I da mostro tipo 3 (mire witchling), 1 su 3, × 5 | attesa media 15 uccisioni: verificare col simulatore del piano che i piani 6–9 ne abbiano abbastanza (altrimenti 1 su 2). Premio *doll-hide* (ha THORNS: senza effetto fino alla 2.0, TODO G5) |
| 6 | the silver needle | C | cancello sul piano 9; Rage (`sk_step[2] = 6`); `c_unl = 3` alla consegna |
| 7 | cold fires | K tipo 4 del capitolo 3 (frost wight) × 10 | borsello 5000 |
| 8 | the oath roll | I da baule, piano 14 | la dà **Chaplain Edric**, si consegna a **Brenna**. Smash (`sk_step[3] = 8`) |
| 9 | the oathbreaker | C | *bastion door*, Frenzy (`sk_step[4] = 9`); `c_unl = 4` |
| 10 | where the carts end | K tipo 4 del capitolo 4 (cultist) × 12 | — |
| 11 | the last cart | B sul piano 19 | il boss con nome del piano 19 c'è sempre (`place_boss`); nella riga gialla "the jailer". Premio: oggetto magico generato (`af_m = 1`, categoria a caso) |
| 12 | the saint's heart | C | consegna = **vittoria**: il testo `done` è l'epilogo (T5); poi il menu di vittoria (`ui_victory`) diventa questa pagina, la leva (`ui_lever`) e l'Abisso restano come oggi. Borsello 10 000, gettone, *aldric's heart*. C3: la vittoria scatta alla consegna a the Penitent (proposta), non alla morte del boss |

### 6.2 Accessorie (testi: id `a1.1`..`a4.3`)

| Id | Titolo | Motore | Note |
|---|---|---|---|
| a1.1 | grom's old hammer | I da baule, piani 2–4 (il primo baule del boss aperto in quei piani) | premio: spada magica (`af_m = 1` sulla base `sword`) |
| a1.2 | iron for the forge | G 300 | dopo `a1.1` (`after`). *gravedigger* |
| a1.3 | a name on the stone | B nel capitolo 1 (piano qualsiasi) | premio **proposta** |
| a1.4 | candles for the saint | P piano 4 × 10 | — |
| a2.1 | marsh glass | I da mostro tipo 2 (bog crawler), 1 su 2, × 6 | premio **proposta** (*bottle tree*) |
| a2.2 | bottles for the tree | K tipo 6 (crawler queen) × 2 | dopo `a2.1`. Le varianti forti sono rare: verificare quante ne nascono nei piani 6–9. Cintura a 8 = TODO F1 (**proposta** P3) |
| a2.3 | lanterns on the water | K tipo 4 (will-o'-wisp) × 8 | gettone respec |
| a2.4 | corbeau's toll | G 600 | *ferryman's oar* |
| a3.1 | the frozen scout | I da baule, piano 11 | — |
| a3.2 | the wight lord's crown | K tipo 8 (wight lord) × 2 | dopo `a3.1`. *frostbound* |
| a3.3 | hounds at the pass | K tipo 3 (hellhound) × 14 | la dà Brenna (che dà anche la catena): l'NPC offre prima la catena, poi l'accessoria. *hound's tooth* |
| a3.4 | the bonfire vigil | V + G 1000 al falò | Fire sul falò con la quest attiva: `tile_trigger` della cura chiama `QGIV` invece di curare (o dopo). Premio **proposta** |
| a4.1 | the king's diary | I da baule × 3: piani 16, 17, 18, una pagina per piano | il contatore non basta: servono 3 bit "pagina del piano presa" (nel byte del contatore) |
| a4.2 | stone that walks | K tipo 7 (stone gargoyle) × 3 | *angel's tear* |
| a4.3 | tears of the angel | P piano 18 × 15 | la dà the Penitent; gettone respec |

### 6.3 Ripetibili (testi: id `r.*`, titoli per capitolo nel campo `chapters`)

| Modello | Motore | Parametri estratti all'offerta |
|---|---|---|
| r.cull | K tipo 1–4 | tipo `rand & 3`, N 8–15 |
| r.hunt | K tipo 5–8 | tipo, N 2–4 |
| r.bounty | B capitolo | — |
| r.recovery | I da mostro qualsiasi, 1 su 4 | N 3–6 |
| r.patrol | P | piano 1–4 del capitolo, N 10–20 |
| r.offering | G | oro del capitolo (`repeatable_rewards`), solo capitoli 2–4 |

Premi: tabella `repeatable_rewards` del file (oro ≈ un quarto di piano, 1–2 pozioni, oggetto magico 1 su 4). Q5: cambiando
capitolo (`chap_travel`) i 2 slot si azzerano. Il titolo mostrato è uno di quelli del capitolo per quel modello (il primo
per i tipi 1–2, il secondo per i tipi 3–4 in `r.cull`).

---

## 7. Ordine di lavoro consigliato (un commit per passo, build verde)

1. **Formato**: stato nel blocco dell'eroe (scelta (a) o (b) del 2.3), `SAVE_VER`, `FORMATO_DATI.md`. Test: salva e ricarica.
2. **Generatore**: `gen_quests.py` su `quests.yaml` nuovo (file `QSTn` a 5 bit, `QIDX`, tabella dei premi); pagina Q
   riscritta in sola lettura con lo stato messo a mano (poke). Test: `QPAGE-*` aggiornati.
3. **Motore residente**: `qa_*`, `q_kill`, `q_chest`, `q_cboss`, `q_done`. Test con poke dello stato: uccidi, trova, boss.
4. **`QGIV`**: offerta e consegna della catena del capitolo 1 (passi 1–3), premi, "!" dai dati. Test: catena 1–3 completa.
5. **Progressione**: `q_gate`, sblocco del capitolo alla consegna, abilità e borsello da `q_step`. Test: cancello, capitolo.
6. **Accessorie** (4 slot, `after`, G e V). 7. **Ripetibili** (2 slot, accept / decline, abandon).
8. **Contenuti** dei capitoli 2–4, vittoria alla consegna del passo 12, manuale ("Quests"), help (tasto Q), taratura
   dell'oro col simulatore (`sim_gold.py` ha già le ipotesi dei premi). → versione 2.0.

## 8. Rischi e punti aperti

- **Spazio**: il motore residente (~310 B) entra nel margine di GAME (1973 B), ma con le quest arrivano anche la cintura a 8
  (F1) e i boss. Il resto è su file: nessun peso fisso.
- **Disco**: ~66 blocchi di testi + `QGIV` (4) + `QIDX` (1): oltre i blocchi liberi di oggi se non si comprime. Misurare
  subito al passo 2; soluzioni: ZX0 dei testi, un file per capitolo, o testi più corti (limite 400 caratteri).
- **Tempi**: Fire su un NPC = caricamento di `QGIV` (4 blocchi, ~0,5 s) + testo (2 blocchi): sotto la soglia di 3 s dei menu.
- **Varianti forti rare** (`a2.2`, `a3.2`, `r.hunt`): se un piano non ne genera, la quest si blocca fino al piano dopo:
  contare con `tools/simulators/sim_floor.py` prima di fissare le quantità.
- **Da decidere dal committente**: C3 (cancello a messaggio e vittoria alla consegna), C6 (premi proposti), P3 (cintura a 8
  in `a2.2`), scelta (a)/(b) per lo stato, se mostrare il premio delle ripetibili prima di accettare.
