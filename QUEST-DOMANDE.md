# Quest: domande per chiudere il progetto (22/11 notte, usa e getta)

Per ogni domanda: contesto, alternative, **la mia raccomandazione**. Con le risposte posso scrivere il quest system dal
passo 1 al passo 5 dell'ordine di lavoro di `QUEST-IMPLEMENTAZIONE.md` senza fermarmi. Testi e premi stanno in
`data/quests/next/quests.yaml`. Le risposte finiscono in `docs/wiki/quests.md`; poi questo file si cancella.

Numeri nuovi di stanotte, misurati (test `QUESTDB-NEXT-11`):
- **testi a 5 bit**: 33 file, 8 826 B (12 689 B in codici schermo: −30%); ZX0 toglie solo altri 795 B (−9%), non conviene;
- un file per quest = **50 blocchi e 33 voci** di directory; un file per capitolo = **36 blocchi e 5 voci** (capitoli 1-4:
  1 986, 1 868, 2 014, 1 708 B; ripetibili 1 250 B). Sul disco restano 94 blocchi;
- ogni voce in più nella directory allunga il caso peggiore dei caricamenti (FastLoader 7.5).

---

## Q1. Dove mettere i 32 B di stato delle quest nell'eroe
Il blocco dell'eroe (`CHRBLK`, 254 B) è pieno e il file di salvataggio (3 blocchi) ha 23 B liberi.
- **(a) Il baule della locanda (120 B) esce dal blocco dell'eroe** e va in coda al file, come previsto dal piano F7 già
  approvato. Il blocco libera 120 B: ci stanno le quest e restano ~88 B per il futuro (cintura a 8, Abisso). Lavoro: `rel.asm`,
  `stash.asm`, `SAVE_VER` nuovo. Il file resta di 3 blocchi.
- (b) Le quest in coda al file dopo i piani: serve un quarto blocco (+1 blocco per eroe, salvataggio ~0,3 s più lungo).
- (c) Stato ridotto a 23 B (2 ripetibili senza oggetto premio preparato, 3 accessorie attive invece di 4).

**Raccomando (a)**: era già il piano approvato, libera spazio per le prossime cose e non allunga il file.

## Q2. Come stanno i testi sul disco
- (a) Un file per quest, come oggi (`QSTn`): 50 blocchi, 33 voci.
- **(b) Un file per capitolo** (+ uno per le ripetibili), letto a `$EC00` (la zona della scheda C: 2 272 B, ci sta il capitolo
  più lungo, 2 014 B): 36 blocchi, 5 voci. Aprendo la pagina Q o parlando con un NPC si legge il file del capitolo (~0,5 s); la
  scheda C si rilegge dopo, come già succede dopo ogni caricamento.
- (c) ZX0 sui file: −4 blocchi, decompressione in più. Non conviene.

**Raccomando (b)**: meno blocchi e soprattutto 28 voci di directory in meno, che è la leva che serve anche ai caricamenti.

## Q3. Dove gira il codice dell'offerta e della consegna (villaggio)
- **(a) File `QGIV` caricato a `QBUF` (schermo B, 1 000 B) quando si preme Fire su un NPC**, come oggi `QST0`: niente spazio
  fisso, ~0,4 s in più alla prima pressione.
- (b) Nel modulo MENU: le zone 3–6 sono piene; servirebbe ingrandirlo (MENU più lungo = ingresso nel villaggio più lento).
- (c) In GAME: ~600 B del margine (oggi 1 928 B).

**Raccomando (a)**. Il "!" sopra gli NPC si calcola all'ingresso nel villaggio con una tabella di 2 B per quest in GAME
(~60 B), senza caricare `QGIV`.

## Q4. Cancello del piano del boss (C3, regola Q14)
La scala del piano 4 (9, 14, 19) porta al boss solo con il passo "uccidi il boss" preso.
- **(a) Scala chiusa con un messaggio** nella riga della barra ("the way is sealed"): ~30 B, nessuna grafica.
- (b) Un cancello disegnato sul tile della scala, che sparisce: grafica nuova in 4 temi e codice di stato del tile.
- (c) Nessun cancello: il boss si può uccidere quando si vuole, il capitolo si sblocca solo alla consegna.

**Raccomando (a)**: semplice e chiaro; (c) è accettabile se preferisci non bloccare il giocatore.

## Q5. Quando scatta la vittoria (C3)
- **(a) Alla consegna del passo 12 a the Penitent** (testo `done` = epilogo), poi la pagina di vittoria e la leva come oggi.
- (b) Alla morte del Lord of Ruin, come oggi.

**Raccomando (a)**: chiude la storia con un NPC e usa lo stesso meccanismo degli altri capitoli.

## Q6. Premi ancora da approvare
| Quest | Proposta nel file | Raccomandazione |
|---|---|---|
| passo 2 "the widow's son" | 150 oro, Whirlwind, *tam's amulet* (anello unico: vita 8, danno subito −1) | **sì** (lega Tam alla storia) |
| a1.3 "a name on the stone" | 150 oro + anello di rame magico | **sì** |
| a3.4 "the bonfire vigil" | 2 pozioni viola + anello d'argento magico (costa 1 000 oro) | **sì**, oppure un gettone respec (sarebbe il quarto) |
| a2.1 "marsh glass" | 2 pozioni gialle + *bottle tree* (scudo unico) | **sì** |
| a2.2 "bottles for the tree" | **cintura a 8 posti** (P3) | **sì, qui**: fine del capitolo 2, come proposto il 20/11 (`sim_floor.py`: con 4 posti 0,25–0,39 ritorni per piano dal piano 3 al 14) |

## Q7. Il boss del capitolo ha le statistiche di un mostro forte a caso (trovato stanotte)
Nel piano 5 (10, 15) il boss è il "boss con nome" del piano: `place_boss` sceglie a caso una variante forte (Fallen
Warchief, Skeleton King, Lich, Balrog) e il gioco gli mette sprite e nome del boss del capitolo. **Vita, CA e danni dell'abate
cambiano quindi da partita a partita** (nella partita del bot era un Lich: 210 punti vita). Le sue meccaniche (scheletri,
rigenerazione) sono invece quelle del codice del piano.
- **(a) Statistiche proprie per i 3 boss dei capitoli** (riga del bestiario, tipo fisso: ~20 B in `place_boss`), tarate col
  simulatore dei boss (`boss_scripts.py`) e col bot.
- (b) Lasciare il caso (varietà), tarando il caso peggiore.

**Raccomando (a)**: il boss del capitolo è il muro della catena delle quest, deve essere uguale per tutti.

## Q8. Unici garantiti dai boss
*censer-bearer* (abate), *stitchripper* (Mother Stitch), *oath blade* (Varok), *tithe-taker* (un boss con nome del capitolo 4).
- **(a) Sempre alla prima uccisione** del boss del capitolo (nel baule del boss); *tithe-taker* 1 su 8 dai boss con nome del
  capitolo 4.
- (b) Con una probabilità (es. 1 su 3) a ogni uccisione: il boss non ricompare (regola C1), quindi rischio di non vederlo mai.

**Raccomando (a)**.

## Q9. Unici a caso: con quale livello confrontare la finestra
Oggi la finestra (es. *oath blade* 13–17) si confronta con il **livello dell'oggetto** L = T × u², quasi sempre molto sotto
il piano: al piano 19 escono ancora gli unici dei piani 2–6, quelli alti quasi mai (1 unico ogni 120–300 oggetti).
- **(a) Confrontarla con il piano** (T = livello del tesoro / 8) e tenere 1 su 64 dentro la finestra.
- (b) Lasciare L ma alzare la probabilità.

**Raccomando (a)**: fa uscire l'unico giusto nel posto giusto; la probabilità si tara poi col bot.

## Q10. Ripetibili: mostrare il premio prima di accettare
- **(a) Oro e pozioni scritti, l'oggetto magico (1 su 4) generato alla consegna**: niente oggetto preparato nello stato
  (−6 B).
- (b) Oggetto generato all'offerta e mostrato (serve salvarlo: 6 B per ripetibile).

**Raccomando (a)**.

## Q11. Oggetti e uccisioni rari
`a2.2` (2 crawler queen) e `a3.2` (2 wight lord) chiedono varianti forti, che possono non nascere per diversi piani.
- **(a) Contano anche i boss con nome di quel tipo** e la variante forte del tipo diventa più probabile nei piani della
  quest attiva (spawn).
- (b) Solo uccisioni normali, quantità basse (1 invece di 2).

**Raccomando (b)** per partire (0 B di codice), poi misura col bot e passo ad (a) se serve.

## Q12. Segno sopra gli NPC
- **(a) "!" giallo = ha una quest da offrire, "!" verde = ha una quest da ritirare** (stesso sprite, colore diverso: 0 B di
  grafica).
- (b) Due sprite: "!" e "?".

**Raccomando (a)**.

## Q13. Ordine del lavoro
- **(a) Prima il capitolo 1 intero** (stato, file, motore, `QGIV`, pagina Q, passi 1–3 e accessorie del capitolo 1) giocabile
  e provato, anche dal bot; poi i capitoli 2–4 sono quasi solo dati.
- (b) Tutto il motore per tutti i capitoli, poi i contenuti.

**Raccomando (a)**: un risultato giocabile presto e i problemi di memoria e disco si vedono subito.
