# Bot: il gioco che si gioca da solo (22/11, richiesta del committente)

Un programma Python che gioca *Barbarian: The Blood Path* in VICE senza nessuno alla tastiera. Serve a vedere il
bilanciamento vero di oggetti e armi e la difficoltà reale dei piani: gioca il gioco com'è (stesso disco, stesso codice),
esplora i sotterranei che non conosce, combatte, apre i bauli, indossa il meglio che trova, spende i punti statistica, usa
le abilità quando il livello le dà, e scrive **quanto tempo passa in ogni piano e in ogni capitolo**.

Non è un test: non fa parte di `lab64 test` e non ha un esito verde o rosso. È uno strumento di misura.

## Come si lancia

```
lab64 run python3 tests/bot/run.py                       # fino al piano 19, al massimo 20 minuti veri
lab64 run python3 tests/bot/run.py --max-level 5 --minutes 5 --seed abc123 --name prova
```

- `--max-level N`: si ferma quando l'eroe entra in un piano più profondo di N (predefinito 19).
- `--minutes M`: limite di tempo vero (predefinito 20).
- `--seed`: seme del mondo (6 caratteri, come nella schermata di creazione); `--name`: nome del rapporto.

Sullo schermo una riga a ogni cambio di piano e a ogni evento (morte, oggetto indossato, punto statistica, vendita); alla
fine la tabella dei piani e dei capitoli e l'eroe com'è arrivato. Il rapporto completo è `out/work/bot/<name>.json`:
`summary` (piani e capitoli: visite, secondi emulati, morti, pozioni, bauli, livello dell'eroe all'ingresso e all'uscita),
`hero`, `visits` (ogni visita di un piano, con i contatori e quante decisioni ha preso ogni capacità), `events`.

**Diario degli oggetti e delle azioni** (22/11): ogni evento ha il tempo di gioco e finisce in tre posti: una riga a schermo,
la lista `events` del JSON e il file di testo `out/work/bot/<name>.log` (una riga per evento, comodo da leggere e da cercare).

| Evento | Quando | Cosa registra |
|---|---|---|
| `chest` | un baule aperto | piano, casella, se era chiuso a chiave, oro trovato, **contenuto** (nomi completi) e cosa è rimasto dentro (zaino pieno) |
| `shop` | a ogni visita del villaggio | la **merce** fra cui il bot sceglie: oggetti base del fabbro per il livello dell'eroe, con prezzo, punteggio e requisito mancante. È l'elenco della scorciatoia, non la merce a caso della schermata vera del negozio |
| `withdraw`, `take_off`, `cheat` | oro preso dal baule della locanda; scudo tolto per un'arma a due mani; trucco usato | oro, oggetto, quale trucco |
| `found` | un oggetto è entrato nello zaino | piano, nome completo (prefisso, suffisso o nome dell'unico), tipo, qualità (normal, magic, cursed, unique), durabilità, dadi e cadenza o CA, requisito, **punteggio** usato per scegliere e, se non viene indossato, **il motivo** (`not_worn`: requisito non raggiunto, a due mani con lo scudo addosso, punteggio più basso di quello indossato) |
| `wear` | il bot indossa un oggetto | piano, posto (weapon, armor, shield), oggetto e punteggio, cosa ha tolto e il suo punteggio |
| `sell`, `buy`, `no_gold` | nel villaggio | oggetto e oro; `no_gold` quando la cintura resta vuota perché l'oro non basta |
| `drink` | una pozione bevuta | piano, vita **prima** della pozione, posto della cintura |
| `meet` | un mostro compare sullo schermo la prima volta in questa visita del piano | nome (dal bestiario del capitolo; *named* = il boss con nome del piano), vita, casella, se è sveglio, vita dell'eroe |
| `attack` | ogni colpo dell'eroe (ogni decisione di attacco, 4 fotogrammi con Fire premuto) | nome del mostro, sua vita prima del colpo, vita dell'eroe, abilità in uso |
| `hurt` | la vita dell'eroe scende | vita prima e dopo, il mostro più vicino (chi con ogni probabilità ha colpito) e la sua vita |
| `avoid` | il boss con nome di un piano normale ha più di 10 colpi medi dell'eroe di vita | nome, vita, danno medio dell'eroe: il bot lo lascia stare (se lo insegue, interviene `Flee`) |
| `give_up` | un mostro non perde vita per 120 decisioni (irraggiungibile) | tipo, casella, vita: il bot lo lascia stare per quella visita |
| `skill` | un'abilità scelta o un potere attivato | piano, abilità, mostri attorno, se il bersaglio è un boss, vita |
| `level_up`, `stat` | livello nuovo, punto speso | livello, piano, vita massima; statistica scelta |
| `retreat`, `death`, `chapter`, `stuck` | ritirata, morte, capitolo finito, bot bloccato | piano, livello, vita o motivo |

La tabella finale ha in più, per piano, **uccisioni, oggetti trovati e oro trovato**, seguita dall'elenco degli oggetti trovati
e di quelli indossati.

**Tempi**: i secondi sono **tempo di gioco emulato** (fotogrammi giocati / 50); i caricamenti dal disco non sono contati.
Accanto c'è il tempo vero. Velocità misurata il 22/11: circa **5 volte** il tempo reale (un capitolo in ~80 s veri).

## Molte partite e rapporto del bottino (`run_many.py`)
```
lab64 run python3 tests/bot/run_many.py --seeds 10 --max-level 5 --minutes 5 --name loot
```
Un seme diverso per partita (sempre gli stessi, generati da un numero fisso: le misure si ripetono), una VICE per partita,
poi un rapporto unico `out/work/bot/<name>_report.md` (e `.json`): per piano visite, tempi, morti, pozioni, bauli, uccisioni, oro,
**oggetti nei bauli per categoria**, quanti magici, livello oggetto medio dell'equipaggiamento, quante armi migliori del pugnale
e quanti pezzi di livello oggetto ≥ 3, **accanto a quello che prevede il simulatore** (`tools/simulators/sim_chest.py`, tesoro di un
mostro comune e del boss con nome), livello dell'eroe all'ingresso; gli oggetti più frequenti per piano; l'eroe a fine partita.
`--merge-only` rifà solo il rapporto dalle partite già in `out/work/bot`. Una partita che serve solo per il capitolo 1
(`--max-level 5`) si ferma quando il capitolo è finito.

## Trucchi (`--cheat`) e limiti di una partita
- `--cheat potions`: nel sotterraneo, quando la cintura è vuota, compare una pozione rossa nel primo posto.
- `--cheat gold`: all'inizio 10 000 monete nel baule della locanda; nel villaggio il bot le prende (fino al tetto del borsello)
  e compra dal fabbro arma, armatura e scudo migliori per il suo livello (scorciatoia), poi le pozioni.
- Ogni uso di un trucco è un evento `cheat` del diario: una partita con i trucchi si riconosce dal rapporto.
- (22/11) **Sempre**: il bot non fa le quest, quindi all'inizio mette il passo 3 della catena come preso (`q_step` 2, `q_flag` 1). Così
  la scala verso il boss del capitolo 1 non è chiusa (cancello D4, `q_gate`). È l'evento `cheat` `gate`.
- `--max-deaths N`: si ferma all'N-esima morte. In ogni caso si ferma dopo **4 morti di fila sullo stesso piano senza
  esperienza guadagnata**.

## Com'è fatto (un file per strato)

| File | Strato | Cosa fa |
|---|---|---|
| `emu.py` | emulatore | VICE (`x64sc`, warp) via il monitor remoto su **TCP** (la libreria `vicemon` di Lab64, la stessa dei test). Scrive in memoria un piccolo **aggancio dell'input** (`$03A0`) e fa passare da lì le tre chiamate di `read_input` del gioco: joystick e tasti sono quelli del bot, e la macchina si ferma solo ogni N fotogrammi (un passo = una scrittura e un "vai") |
| `state.py` | conoscenza | legge dalla memoria eroe, cintura, mostri e mappa. **Nel sotterraneo il bot usa solo le caselle che sono passate sullo schermo** (`seen`, 20 × 10 caselle attorno all'eroe) e ricorda i piani già percorsi; **nel villaggio conosce tutta la mappa** |
| `nav.py` | cammino | percorso più breve sulle caselle viste (ricerca in ampiezza) e controllo al pixel (prima al centro della casella, poi avanti) |
| `skills.py` | capacità | una classe per capacità, con `ready(bot)` e `act(bot)`: vedi sotto |
| `brain.py` | cervello | a ogni decisione legge lo stato e fa agire la **prima capacità pronta**, nell'ordine di priorità |
| `logbook.py` | diario | tempi e contatori per piano e capitolo, eventi, rapporto |
| `run.py` | avvio | riga di comando |

### Capacità di oggi (in ordine di priorità)

| Capacità | Cosa fa | Come |
|---|---|---|
| `Screens` | chiude una schermata che nessuno ha chiesto (la morte) | Fire, poi RUN/STOP |
| `Drink` | beve una pozione sotto il 45% della vita | tasti 1–4 |
| `Flee` | sotto il 30% della vita e senza pozioni: risale le scale fino al villaggio (non nei piani dei boss) | cammino e Fire |
| `Fight` | il mostro più vicino sullo schermo: gli va accanto, si gira, tiene premuto Fire. **Abilità**: le conosce dal livello (`sk_req`) e le usa a ricarica finita (`sk_cd`): Whirlwind con 2 o più mostri attorno, Battle Cry con 3 o più, Smash e Frenzy su un boss, Rage sotto metà vita con 2 o più attorno | joystick e tasti H J K L U O |
| `Stats` | spende i punti statistica a ogni livello: FOR fino a 18, poi DES fino a 18, poi COS | **scorciatoia** |
| `Gear` | indossa l'arma, l'armatura e lo scudo migliori dello zaino (danno medio per fotogramma, CA, affissi e unici compresi, requisiti rispettati) | **scorciatoia** |
| `Town` | nel villaggio va a curarsi (la fontana o il suo equivalente), vende ciò che non indossa, riempie la cintura di pozioni rosse, poi va all'ingresso del sotterraneo; a boss del capitolo morto va all'uscita verso il villaggio dopo | cammino vero; vendita e acquisto **scorciatoia** |
| `Loot` | apre i bauli che ha visto (anche quelli lasciati dai mostri) e prende tutto | Fire sul baule e nella sua schermata |
| `Ascend` | piano del boss ripulito: risale le scale fino al villaggio | cammino e Fire |
| `Descend` | piano finito (niente bauli, niente caselle da scoprire, o 4 minuti di gioco): alle scale giù | cammino e Fire |
| `Explore` | va alla casella vista più vicina che ne ha accanto una mai vista | cammino |

**Scorciatoia** = il bot non naviga ancora quel menu: scrive in memoria lo stesso risultato che darebbe il menu e chiama la
routine del gioco (`recalc_stats`, `it_cost` per i prezzi veri). Le regole (requisiti, prezzi di vendita a un quarto, punti
disponibili da `pts_avail`) sono quelle del gioco. Sono i primi candidati a diventare capacità "vere".

### Aggiungere una capacità
1. In `skills.py` una classe con `name`, `ready(bot)` (vuole il turno?) e `act(bot)` (una decisione: di solito
   `bot.emu.step(joy=..., key=..., n=fotogrammi)`).
2. Metterla nella lista `self.caps` di `brain.py` al posto giusto della priorità.
3. Per premere un tasto nuovo: aggiungerlo a `KEYS` in `emu.py` (riga e maschera della matrice, come in `handle_keys`).

Esempi pronti da scrivere: **comprare davvero in un negozio** (camminare alla porta, Fire, muovere il cursore delle liste
`sl_cur`, Fire: la lista della merce è `l8_id`/`l8_b`/`l8_s`), riparare dal fabbro, usare il baule della locanda, la
pergamena del portale quando la cintura è vuota, la ritirata, le quest.

## Limiti di oggi (da sapere prima di leggere i numeri)
- **Non è un buon giocatore**: si ritira solo a piedi, non usa il portale, non ripara, compra solo pozioni rosse. Le morti che conta
  sono un limite superiore della difficoltà, non la difficoltà per una persona.
- Bersaglio = il mostro più vicino: non sceglie fra un boss e i suoi evocati (contro l'abate conta).
- La mappa si rilegge dopo ogni uccisione e ogni 60 decisioni (i bauli lasciati dai mostri); niente linea di vista: "visto"
  = passato nel riquadro dello schermo.
- Capitoli 2–4 (palude con i cancelli, grotte, cittadella) e sala del trono: il codice è lo stesso, ma il 22/11 il bot è
  stato provato a fondo solo sul capitolo 1. Dove si ferma lo scrive (`stuck`, `stop`).
- I tempi non contano i caricamenti; la velocità (5×) è limitata dal monitor (una decina di comandi a decisione), non da VICE.
- L'altro emulatore (vc64web) non è usato: VICE ha il monitor su TCP con memoria, punti di arresto e chiamate di routine.
