# Villaggio

**Dal 15/11 ogni capitolo ha il SUO villaggio** (TODO Z2, richiesta del committente: villaggi diversi, non lo stesso con altri
colori). Questa pagina descrive prima [i villaggi dei capitoli](#i-villaggi-dei-capitoli-1511) e il formato comune, poi il
villaggio 1 (Aldric's Crossing) in dettaglio; negozi, locanda e modulo MENU sono uguali in tutti.

## I villaggi dei capitoli (15/11)

| # | Villaggio | Struttura | Cura (`~`) | Ingresso del sotterraneo (`>`) | Entrata → uscita | Colori (sfondo, 1, 2, accento) |
|---|---|---|---|---|---|---|
| 1 | **Aldric's Crossing** | due rive di un torrente con due ponti, piazza, chiesa, cimitero | fountain of saint aldric | la **cripta** nel cimitero | strada a sud → sentiero a nord | verde, marrone, grigio chiaro, ciano |
| 2 | **Blackwater Mill** | **palafitte su un lago nero**: piattaforme di assi su pali unite da passerelle; barche, mangrovie, ninfee | the drowned bell (una campana di bronzo verde; si guarisce sui moccoli) | la **botola della cantina allagata del mulino** (isolotto a nord-est, con la ruota) | riva a sud-ovest → fondo del pontile est (il traghetto) | nero, marrone, arancio, verde |
| 3 | **The Last Camp** | **campo di guerra su tre terrazze** di una montagna innevata: pareti di roccia, scale di legno, tende, palizzata e torri | the great bonfire (ci si siede sui tronchi attorno) | la **bocca di una grotta** nella parete nord | cancello a ovest (terrazza bassa) → passo a nord-ovest (terrazza alta) | bianco, grigio scuro, marrone, rosso |
| 4 | **Ruin's Gate** | **città in rovina attorno a un cratere**: strada ad anello, quattro raggi, mura con le brecce, colonne, case sventrate | the weeping angel (una statua; le candele ai suoi piedi) | la **saracinesca delle segrete** nel corpo di guardia a nord | strada a sud → **scala di tavole che scende nel cratere** | grigio scuro, nero, grigio chiaro, rosso |
| 5 | **The City of the Abyss** (prototipo) | **isole di pietra sospese nel vuoto** unite da ponti di luce; case a cupola, cristalli, obelischi | the heart of the abyss (un cristallo che galleggia; le rune attorno) | **la Bocca**, sull'isola a nord (oggi non porta da nessuna parte) | ponte dal nulla a sud → isola a nord-est (le caselle ci sono ma non si aprono) | nero, blu, azzurro, viola |

Ogni villaggio ha fabbro, alchimista, locanda (con lo stesso baule), luogo di cura, posto del portale, ingresso e uscita. Il
villaggio 5 è un **prototipo**: ci si arriva dall'uscita del villaggio 4 dopo il boss finale (`c_unl` = 5), i piani dell'Abisso
non ci sono (TODO H3). Anteprime: `lab64 run python3 tools/build/village_preview.py` (`out/work/villages/twnN_map.png`,
`twnN_tiles.png`); atlante: set `VILLG`, `VILL2`…`VILL5`. Mappa del mondo (fan art): `tools/art/world_map.py`; dal 16/11 è nel manuale (pagina "Il mondo"), generata dalla build del manuale (`tools/manual/gen_manual.py`, nessun file in git).

### Come è fatto un villaggio

- **Tile**: 45 posti (`TOWN_TILES` in `tools/build/gen_gfx.py`), gli stessi numeri per tutti; ogni villaggio li **ridisegna e
  decide quali sono solidi** nel suo modulo `tools/build/vilN_*.py` (`PAL`, `NAME`, `HEAL`, `TILES` = posto → nome, descrizione,
  solido, griglia 8×16; attrezzi di disegno in `tools/build/tileart.py`). I posti non elencati restano quelli del villaggio 1.
  Il codice conosce solo questi **ruoli**: `DSMITH`, `DALCH`, `DHOME` (porte), `TSTAIRS` (ingresso del sotterraneo), `FOUNTAIN`
  (cura), `PORTAL`; `PATH`, `DIRT`, `BRIDGE`, `COBBLE` sono "strade" nella minimappa e `WATER`, `WATERL`, `WATERR` "acqua"; i
  posti 5, 6, 8–11, 24–26 devono essere solidi (`tools/build/villages.py`, che lo controlla).
- **Mappa**: testo 48 × 48 in `data/town_mapN.txt` con le lettere di `LEGEND` (una per posto: in ogni villaggio la stessa lettera
  disegna il tile di quel villaggio; la legenda con i nomi è in testa al file). Lettere speciali: `E` ingresso, `P` posto del
  portale (la casella sotto è l'arrivo), `=` uscita del capitolo (2 caselle). Le prime stesure vengono da
  `lab/villaggi/concept_maps.py`; da lì in poi la fonte è il testo.
- **Settori degli NPC** (17/11): ogni villaggio ha fino a 16 rettangoli (`SECTORS` in `tools/build/villages.py`, nell'intestazione
  del file) dove vivono gli NPC che vagano; vedi [quest](quests.md). `gen_maps.py` controlla misure e caselle percorribili e stampa
  il massimo di settori in una finestra di gioco (oltre 5 NPC visibili non si disegna).
- **Controlli della build** (`tools/build/gen_maps.py`): una sola porta per negozio e locanda con **2 caselle libere davanti**;
  porte, cura, ingresso del sotterraneo, uscita, portale e il suo arrivo **raggiungibili dall'ingresso**; **nessuna casella
  percorribile isolata**; intestazione + mappa entro 1888 B.
- **File `TWNc`** ([formato](FORMATO_DATI.md)): tile, poi un'**intestazione** (posizioni, colori, porte per le icone della
  minimappa, uscita, nome del luogo di cura, tile solidi), poi la mappa RLE. `gfx_install` copia l'intestazione in `town_k`
  (`src/game/levels.asm`) e in `solidtab`, e i colori nella voce 0 delle tabelle delle palette: il gioco non ha più costanti
  del villaggio (`TOWN_*`, `solid_town` e le tabelle di `town_places.inc` non ci sono più). Costo nel gioco, misurato: il margine sotto `$8720` è sceso di 50 B in tutto (villaggi, colori dei boss, capitolo 5).
- **Passaggio di capitolo**: `chap_travel` legge subito il file del villaggio nuovo (serve il suo ingresso prima di salvare:
  "continue" riparte da lì), poi salva e lo rilegge: una lettura in più (non misurata).
- Test: `VIL-TWN-11..23`, `VIL-BOSS-10` (regression dal 15/11, `tests/regression/villages`).

**Proposta scartata** (15/11): la prima stesura dei villaggi 2–5 riusava la struttura del villaggio 1 con altri tile e colori
(il committente: "devono essere diversi, non lo stesso villaggio con temi diversi"). È conservata in
`lab/villaggi/proposta-a-temi/` (script, mappe, anteprime), fuori dalla build.

**Aperto** (TODO M1): musica propria per villaggio; minimappa (i colori di "acqua" e "strade" valgono per i ruoli, non per il
disegno: nel villaggio 4 il cratere esce blu); l'etichetta dell'ingresso dice sempre "stairs down to level N"; nel villaggio 5
la Bocca non fa nulla; hardware reale e vc64web non provati con i villaggi nuovi.

# Villaggio 1: Aldric's Crossing

Sorgenti: `data/town_map.txt` (mappa 48 × 48, una lettera per casella), `tools/build/gen_maps.py` (intestazione e RLE nel file
`TWN1`), `src/game/levels.asm` (`town_post`, `place_player`), `src/game/game.asm` (`act_tick`, `tile_trigger`),
`src/game/ui.asm` (negozi, baule della locanda), `src/game/bar.asm` (nomi dei luoghi).

Il villaggio è il luogo 0 (`cur_level` = 0): mappa fissa, nessun mostro, musica propria. La mappa sta compressa
(RLE, massimo 1792 byte) nel file `GFX0` dopo la grafica dei tile e si espande in `MAP` al caricamento.

## La mappa (10/11, concept v3 approvato dal committente)

Ristrutturata il 10/11 su richiesta del committente: **locanda e cripta ai lati opposti** (per dare tempo al precaricamento),
torrente irregolare con ponti migliori, laghetto, chiesa con il campanile, case più ricche, pozzi, sentieri tortuosi che
collegano tutto, niente zone vuote. La mappa è stata generata da uno script di concept (semi 5 e 3) e poi resta un file di
testo: `data/town_map.txt` è la fonte. Controlli fatti sulla mappa: ogni casella percorribile è raggiungibile dall'ingresso,
ogni porta ha un sentiero davanti, i sentieri (`: d + x`, 4 direzioni) sono una rete unica, nessun arredo entro 3 caselle
dalle porte di negozi e locanda (`tools/build/gen_maps.py` lo controlla a ogni build), nessun arredo entro 2 caselle dai ponti.

**Sentiero di uscita** (12/11, committente, TODO M1): dalla porta della chiesa un sentiero largo 2 (colonne 26–27) sale fino
al bordo nord, dalla parte opposta all'ingresso (strada a sud, colonna 16). Le due caselle sul bordo sono scritte `=` nel
testo della mappa: è la **casella generica di uscita del capitolo** (`ALIASES` in `tools/build/gen_maps.py`: diventa un sentiero, la
posizione va nell'intestazione del file `TWNc`, `tx_exit_x/y`, 2 caselle dal 15/11). Fuori dalla mappa è solido, quindi lì il PG si
ferma: finché il capitolo dopo è chiuso la strada "continua" ma non succede nulla; dopo l'uccisione del boss del capitolo
compare `travel to next chapter` e Fire porta al villaggio dopo ([capitoli](capitoli.md)). Intestazione + mappa RLE: 1877 B su
1888 (`TOWN_MAX`; con i 66 B dei settori NPC e della casella di chi dà la quest, 17/11: è il limite del villaggio 1).

```mermaid
flowchart LR
    subgraph ovest["ovest del torrente"]
      CEM["cimitero (3..16, 3..13): steccato, lapidi in 3 file<br/>con la terra davanti, CRIPTA (porta 12,5), cancello a est (16,11-12)"]
      CH["chiesa (18..25, 2..8): campanile alto a ovest,<br/>torretta, guglie con la croce; porta chiusa (22,8)"]
      PZ["piazza (11..21, 25..33): fontana 2x2<br/>con il bordo della vasca (cura), bancarelle"]
      AL["alchimista (5..11, 38..41), porta (8,41)"]
      EN["ingresso a sud (16,46): nuova partita"]
      LK["laghetto (17..26, 38..43)<br/>con il ramo del torrente (riga 40)"]
    end
    subgraph est["est del torrente"]
      SM["fabbro (36..42, 8..11), porta (39,11)"]
      PO["piazzetta tonda del portale (37..43, 22..28)<br/>portale a (42,24), pozzo"]
      OR["orto recintato (36..40, 29..33)"]
      HO["LOCANDA (37..43, 39..42), porta (40,42)"]
    end
    EN --> PZ --> CH --> CEM
    PZ --> AL
    CH -->|ponte nord| SM --> PO --> OR
    PZ -->|ponte sud| HO
    PO --> HO
```

- **Torrente**: entra dal bordo nord ed esce da quello sud (attraversa gli alberi del bordo); percorso irregolare fra le colonne
  27 e 33, dritto ai due ponti. Il 10/11 il committente ha chiesto di ammorbidire la curva fra il pozzo est e l'orto: scarti
  di una colonna alla volta, con più tratti dritti.
- **Ponti**: alti 3 caselle (righe 11–13 e 33–35), con gli accessi di sentiero larghi quanto il ponte e nessun arredo entro
  2 caselle (prima erano alti 2 e un lampione stava attaccato all'uscita del ponte nord: ipotesi sul perché ci si incastrava,
  dedotta dalla mappa, non misurata).
- **Laghetto** a sud, vicino al torrente, alimentato da un ramo lungo la riga 40. È fatto con i tile del torrente (acqua e
  sponde), quindi i bordi sopra e sotto sono squadrati.
- **Cimitero**: steccato orizzontale `|` e verticale a linea sola `v` (`FENCEV`, tile nuovo); 11 lapidi (`t` lapide, `Y` croce)
  in file, ognuna con la terra battuta davanti; il resto è erba; vialetto di terra dal cancello alla cripta.
- **Case**: finestre (`o`, `WINDOW`), comignoli (`c`, `CHIMNEY`), e le case chiuse con un giardino recintato (cespugli e fiori).
  Negozi e locanda **senza** steccato davanti alla porta. La **chiesa** ha il campanile alto 6 caselle attaccato al lato ovest
  (due finestre, guglia `A` con la croce, `SPIRE`) e una torretta centrale con la sua guglia.
- **Botti e fieno tolti** (non si capivano, richiesta del committente): i loro tile sono diventati finestra e comignolo; il
  recinto del fieno è un **orto** (terra e fiori).
- **Piazzetta del portale tonda** (7 caselle di diametro, bordo a gradini): il portale e l'arrivo restano a (42,24) e (42,25),
  (dal 15/11 la posizione è la lettera `P` della mappa).
- **Pozzi**: due, accanto a un sentiero (12,17) e (36,22). **Boschetti**, cespugli e fiori nelle zone vuote (alberi interni:
  da 23 a ~110; erba libera dal 54% al 46%).
- Mappa compressa: **1710 B** su 1792 (era 1289 B): restano 82 B per altri dettagli.

### Storia della mappa
- 06/11 pomeriggio: prima mappa a due rive (fiume dritto, colonne 29–31, ponti di 2 righe), script con seme 7.
- 09/11: tolto l'armaiolo (la sua porta divenne una porta chiusa), il fabbro si spostò nella sua casa a est, sentieri
  ritoccati, lapidi lontane dal cancello, piazzetta del portale collegata ai sentieri.
- 10/11: questa mappa.

### Tile del villaggio
Il file `GFX0` ha i suoi **45 tile** (`TOWN_TILES` in `tools/build/gen_gfx.py`, il massimo: `GFX_NT` = 45, gli altri 19 codici di
ogni quarto sono i caratteri fissi dell'HUD): i posti che nel dungeon sono muri, pavimenti, scale, i posti 8–11 (liberi nei
dungeon) e bauli ospitano i tile solo del villaggio (erba con pietra, ponte, terra battuta, porta chiusa, acqua e sponde,
lapide, croce, fianchi, tetto e fronte della cripta). I tile con un ruolo nel codice (porte, fontana, portale, cripta =
`T_TSTAIRS`, erba, strade) hanno lo stesso numero nei due set; i tile nei posti "speciali" (5, 6, 8–11, 24–26) sono tutti
solidi, così il codice di scale, raccolta e bauli non li incontra mai sotto il PG. La tabella dei tile solidi è in RAM
(`solidtab`: nei dungeon copiata da `solid_dun`, nel villaggio dall'intestazione del file `TWNc`, 15/11). 10/11: tolti `BARREL` e `HAY`, aggiunti `WINDOW`
(posto 33), `CHIMNEY` (42), `FENCEV` (43) e `SPIRE` (44), tutti solidi. Nomi e descrizioni di ogni tile: atlante grafico
(`out/work/atlas/`, `tools/atlas/atlas_names.py`).

Colori: in modo testo multicolor ogni schermata ha 3 colori condivisi (sfondo verde, marrone, grigio chiaro) più
**uno** per carattere, uguale per tutta la mappa (ciano: acqua, vetri, riflessi). Un colore diverso per tile
richiederebbe di riscrivere la color RAM a ogni passo di scorrimento (760 byte, con il doppio buffer che non la
copre): non è possibile con questo motore, quindi il villaggio resta a 4 colori.

## Luoghi

| Luogo | Tile | Azione (Fire sul tile) |
|---|---|---|
| Porta della cripta (cimitero, nord-ovest) | `T_TSTAIRS` (`>`) | primo piano del capitolo (1, 6, 11, 16), arrivo sulle scale su |
| Fabbro (blacksmith, nord-est, porta 39,11) | `T_DSMITH` (`S`) | negozio: armi, armature, scudi (08/11); **riparazioni** |
| Alchimista (alchemist, sud-ovest, porta 8,41) | `T_DALCH` (`L`) | negozio: red, yellow, violet, portal scroll, copper ring (ne mostra 4) |
| Locanda (sud-est, porta 40,42) | `T_DHOME` (`H`) | baule della locanda (24 posti più l'oro, salvato con l'eroe a "save game") |
| Fontana di Saint Aldric | `T_FOUNTAIN` (`~`, le 8 caselle del bordo della vasca attorno alla fontana 2×2 `1 2 / 3 4`, che è solida) | passandoci sopra: vita piena |
| Portale (piazzetta tonda a est del torrente, 42,24) | `T_PORTAL` | solo se aperto con una pergamena: torna al piano e alla posizione di partenza |
| Uscita del capitolo (bordo nord, 26–27,0; caselle `=`) | sentiero | dopo il boss del capitolo: `travel to next chapter`, al villaggio del capitolo dopo (12/11) |

Arrivi (`place_player`): nuova partita sulla strada sud (16,46); dal portale o dopo la morte accanto al
portale (42,25); dal piano 1 sulla porta della cripta (12,5).

**Porte dei negozi e della locanda** (06/11 sera): Fire apre anche stando **1 o 2 caselle davanti** alla porta (le porte
sono tutte sul muro sud; `pl_tile` in `src/game/bar.asm`, usata da `act_tick` e dall'etichetta della barra in alto,
solo nel villaggio). Nessun arredo (lampioni, cespugli, fiori, bancarelle, pozzi, alberi) entro 3 caselle (Chebyshev)
dalle porte `S L H`: lo controlla `tools/build/gen_maps.py` (errore di build).

**Portale**: tile ridisegnato (06/11 sera) come un arco di pietra in piedi con un ovale luminoso nel vano, perché
il vecchio (anelli concentrici grigio/ciano) si confondeva con l'acqua e la fontana; nel villaggio non c'è il
giallo (palette verde/marrone/grigio chiaro + ciano), quindi si distingue per la forma. Nel dungeon prende i colori
della palette del piano. Atlante: `out/work/atlas/` (`VILLGO`, `DUNGxO`).

## Abitanti (17/11, concept)
Quattro abitanti per villaggio, figure dell'eroe in altri colori (sprite 3-6): chi dà la quest, fermo vicino all'ingresso (nome nella
barra quando gli si è accanto, Fire = la sua quest), e tre che vagano piano e solo con il PG vicino. Piazzati a caso su caselle
libere attorno all'ingresso (`npc_init`, modulo MENU). Dettagli: [Quest](quests.md), "Concept del 17/11".

## Armaiolo: tolto (09/11, decisione del committente)

L'armaiolo non c'è più: armature e scudi li vende e li compra il **fabbro** (già dall'08/11). Tolti: il negozio
(`balance.yaml shops.armorer`, `shop_*` di `db.asm`: ora 2 negozi, `shop_id` 0 fabbro, 1 alchimista), il nome e l'icona del
titolo (`sn_armor`, `shop_ic`), l'etichetta `armorer` della barra in alto (`ls_armor`; gli id delle etichette dopo il 9 sono
scesi di uno), l'icona sulla minimappa (`mi_ic`: 3 icone, `MI_N`), il tile della porta `DARMOR` e quello dell'insegna `SIGNA`
(l'insegna dell'alchimista `SIGNL` è passata nel posto 19), la variante `TESTUI=16`, lo screenshot `armaiolo` e la figura del
manuale (ora l'alchimista). Il glifo dello scudo (`CH_SHLD`, 35) resta: è l'icona della categoria scudi. Nello stesso giorno
il disegno sulla porta della locanda (tile `DHOME`) e l'icona della locanda sulla minimappa sono diventati il **boccale**
(`CH_INN`, lo stesso glifo del titolo "inn"); la casetta (glifo 37, `CH_HOME`) non c'è più.

## Negozi (`enter_shop`, `sh_draw`; modulo MENU dall'11/11)

Dall'08/11 (concept con il committente) una sola schermata a riquadri, uguale per tutti i negozi, senza linguette e
senza testo descrittivo: **wares** (merce, righe 1-6, 2 colonne da 4: al massimo 8 oggetti, i posti vuoti con `-`),
**equipped** (righe 7-10, `eq_draw` come nella locanda e nell'inventario), **pack** (righe 11-16), **purse** (in basso a
sinistra: oro **totale** = addosso + baule della locanda, dal 10/11, da 100 000 in migliaia con `k`; si paga prima
con l'oro addosso e il resto dal baule, vedi [Oggetti](oggetti.md#prezzi); sotto, la cintura con 4 posti a x 2/5/8/11 e le pergamene `s N` a x 14) e **selected item** (il
riquadro standard dell'oggetto, come nell'inventario). Riga 23: messaggi e domande; riga 24: i tasti, **secondo la
voce sotto il cursore** (`sh_help`).

```mermaid
flowchart LR
    E["ingresso: shop_roll<br/>(stock a caso dal pool), sort_pack"] --> N["cursore: merce → equipped (solo fabbro)<br/>→ zaino → cintura e pergamene (solo alchimista)"]
    N -->|"fire su merce"| BUY{"pozione?"}
    BUY -->|no| ASK["buy for N g? (fire = sì)<br/>give_item, paga"]
    BUY -->|sì| SLOT["'>' sul primo posto libero della cintura<br/>W/S lo spostano · fire paga e la mette · RUN/STOP annulla senza pagare"]
    N -->|"fire su zaino, cintura, pergamene"| SELL["se il negozio compra quella categoria:<br/>sell for N g? metà prezzo (una pergamena per volta)"]
    N -->|"fabbro: fire su equipped, R su zaino o equipped"| REP["riparazione: 25% del prezzo,<br/>durabilità al massimo, massimo − 1"]
    N -->|RUN/STOP| X["uscita"]
```

- **Chi compra cosa** (`sh_cats`, indice = `shop_id`: 0 fabbro, 1 alchimista): il fabbro armi, armature e scudi; l'alchimista anelli,
  pozioni e pergamene. Gli oggetti dello zaino che il negozio non compra sono **grigi** (`pk_name`) e fire dice
  "i don't buy that.". L'equipaggiamento **non si vende mai**. Solo il fabbro ripara.
- **Riquadro dell'oggetto**: nome, caratteristiche, riga 3 secondo la voce: `buy 25g have 2` (merce: prezzo pieno;
  pozioni e pergamene: quante se ne hanno), `sell 600g d135/178` (zaino, cintura: metà prezzo; la durabilità solo se
  sta nei 18 caratteri), `fix 45g` (equipaggiamento rovinato, dal fabbro), `val ...` (oggetto che il negozio non compra).
- Voci del cursore (codici in `ui_lc`): 0-7 zaino, 8-11 equipaggiamento, 12-19 merce, 20-23 cintura, 24 pergamene;
  ordine in `sh_nav`, voci assenti saltate da `sh_fix`.
- Merce (`balance.yaml shops`, 08/11): fabbro 6 a caso fra armi, armature e scudi; alchimista 4. **Cosa e
  quanto vende ogni negozio è da decidere** (TODO E2).

L'assortimento cambia **a ogni visita** e **cresce con il livello del PG** (06/11 sera): `shop_roll` tiene solo gli
oggetti del pool con `shop_minl` ≤ livello del PG; per armi, armature, scudi e anelli `shop_minl` = livello oggetto
− `level_ahead` (3, `balance.yaml shop_rules`), per pozioni e pergamena il `shop_level` di `rules.yaml`. Se ne
restano meno di `stock` si mostrano tutti. Gli oggetti in vendita non hanno magia; la durabilità si tira
all'acquisto. Pool e quantità: `balance.yaml shops`.

| Negozio | Livello del PG 1 | dal 2 | dal 4 | dal 5 | dal 7 | dal 9 | dal 11 | dal 12 |
|---|---|---|---|---|---|---|---|---|
| Fabbro | dagger, sword, leather, small shield | mid shield | chain mail | | tower shield | viking sword | plate mail | |
| Alchimista | red, portal scroll | | copper ring | yellow | | | | violet |

## Baule della locanda (`ov_stash`, modulo MENU)

Schermata rifatta l'08/11 (progetto con il committente, concept ASCII in [Refactor dei tasti](refactor-tasti.md)):

```
               o inn o              (il boccale CH_INN ai lati del titolo, 09/11)
+ conan -----------++ selected item ---+     riquadro del PG (titolo = nome): hp massimo, ac, att | str, dex, con; dmg in fondo
|hp  125   str 16  ||+2 viking sword   |     oggetto sotto il cursore: nome, caratteristiche, valore e durabilita'
|ac  22    dex 17  ||dmg 2d6+2 2h pen 1|
|att +6    con 15  ||val 1200 d 231/231|
|dmg 2d6+2         ||                  |
+------------------++------------------+
+ equipped ----------------------------+     2 colonne con le icone: arma, armatura | scudo, anello
| % +1 sword         U +2 medium shield|
| & +3 plate mail    o silver ring dex |
+--------------------------------------+
+ pack ------------++ chest ------ 1/3 +     zaino (oro + 8) e baule (oro + 8 della pagina); 1/3 = pulsante pagina
```

- **Una sola lista** (`ui_nav`): equipped (4) → oro e oggetti dello zaino → numero di pagina → oro e oggetti del baule,
  con giro. **Destra** (solo qui, solo dallo zaino) porta al baule sulla stessa riga. Si esce con RUN/STOP o I.
- **Fire**: su zaino/baule sposta l'oggetto dall'altra parte (sull'oro dello zaino: tutto nel baule, a decine; sull'oro del baule niente, dal 10/11 il prelievo non c'è); sul
  numero di pagina sfoglia 1→2→3→1 (24 posti, 3 pagine da 8); un oggetto che entra nel baule porta la pagina dove
  è finito.
- **Fire su un posto di equipped** = **scelta**: cornice di equipped colorata, `>` fermo sul posto, zaino e baule
  mostrano solo gli oggetti di quella categoria, accorpati (`- remove` in cima, non per l'arma: l'arma si può solo
  sostituire). Fire su un oggetto lo indossa e quello tolto va al suo posto; `- remove` mette l'oggetto nello zaino (se
  pieno nel baule); un'arma a due mani fa scendere lo scudo nello zaino (o nel baule; tutto pieno: rifiutato); uno
  scudo con un'arma a due mani è rifiutato. Rifiuti: bordo rosso per un attimo, suono e messaggio rosso in riga 23.
  RUN/STOP annulla.
- **Ordinamento**: zaino e baule sempre in ordine di categoria (armi, armature, scudi, anelli, pozioni, pergamene;
  `sort4`, stabile). Il baule si ordina anche all'apertura.
- **Memoria**: la locanda sta nel modulo **MENU** con i negozi (`src/menu/inn.asm` zona 1, `src/menu/inn_eq.asm` zona 2;
  [sotto](#menu-del-villaggio-modulo-menu-1111)). Per tutta la schermata `$01 = $35` (niente KERNAL); uscendo `$01 = $36`
  (dall'11/11 sera niente salvataggio uscendo: il baule va sul disco con "save game"). Apertura 0,14 s (modulo già in memoria dall'ingresso nel villaggio).
- Il baule sta nel blocco dell'eroe, sempre in RAM: va sul disco con l'eroe a "save game" o al cambio di capitolo ([Salvataggi](salvataggi.md#baule-della-locanda)).

## Menu del villaggio: modulo MENU (11/11)

**Locanda e negozi** stanno nel modulo su disco **MENU** (`src/menu.asm`; formato in
[FORMATO_DATI](FORMATO_DATI.md#menu--menu-del-villaggio-locanda-e-negozi), memoria in [Tecnica](tecnica.md#moduli-su-disco)):
- si carica **a ogni ingresso nel villaggio** (dall'11/11, ramo `fast-loader`: niente residenza fra una visita e
  l'altra), dal 18/11 in **un file** (`menu`, cinque zone; prima un file per zona) letto con Krill's Loader: **3,1 s** con la
  decompressione (VICE, 1541 emulata, `PERF-DISK-11`; con il KERNAL erano 10,5 s);
- dentro la visita **resta**: fabbro, alchimista e locanda si aprono in **0,12–0,16 s**;
- il precaricamento del tema in sottofondo non c'è più (tolto l'11/11, [Flussi](flussi.md#8-precaricamento-del-tema-tolto)).

**Storia**: dal 09/11 al 11/11 il modulo della locanda OVL2 stava nel posto del precaricamento (`$F500`) e il
precaricamento nel villaggio partiva solo dopo **N caselle** (`TOWN_PF_N` = 8 per Aldric's Crossing, con l'audit delle
distanze `tools/village_audit.py`) per non sovrascriverlo; ogni ingresso nella locanda dopo un precaricamento costava
3,0–4,8 s. Con il modulo MENU residente N, il contatore `pf_wait` e l'audit non servono più (tolti l'11/11).

### Per ogni villaggio nuovo
1. Il villaggio **ha sempre una locanda** (tile `DHOME`) con **lo stesso baule** di tutte le altre (decisione del 09/11:
   il baule è nel record dell'eroe).
2. La mappa del villaggio (`MAP`, `$C000`–`$C8FF`) non deve usare `$C900`–`$CFFF` (zona 1 del modulo MENU).
3. `lab64 test regression -k VIL-MENU` (il file MENU non si rilegge mai nel villaggio).
4. Aggiornare `docs/wiki/quests.md` (sez. 3.6, villaggi multipli) e il `TODO.md` se resta qualcosa.
5. (15/11) Un modulo `tools/build/vilN_*.py` (tile, colori, nome della cura), la voce in `tools/build/villages.py`, la mappa
   `data/town_mapN.txt` (lettere `E`, `P`, `=`), il file `twnN` in `tools/build/asm.sh` e `tools/build/mkdisk.sh`, il brano in
   `PLAYLIST["town"]` (`tools/build/songs.py`), `data/chapters.yaml`; poi `lab64 test sanity -k VIL-TWN` (i test leggono
   l'elenco dei villaggi da `villages.py`). Vedi [Come è fatto un villaggio](#come-è-fatto-un-villaggio).

## Leva della sala del trono

Non è nel villaggio ma usa lo stesso tile della porta della locanda (`T_LEVER = T_DHOME` nel tema 8): dopo la vittoria,
nella stanza dei tesori del piano 20, Fire sulla leva apre `ui_lever` ("this lever opens the gate to the endless
abyss. are you sure?"): tirata, `c_lever` = 1 e compare il portale per *The Endless Abyss* (non ancora
implementato).
