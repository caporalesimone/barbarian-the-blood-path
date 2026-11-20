# Oggetti

Sorgenti: `out/work/db.asm` (generato), `src/game/game.asm` (`give_item`, `add_to_pack`, `use_scroll`, `gen_item`),
`src/game/ui.asm` (inventario, negozi, baule della locanda), `src/game/combat.asm` (`recalc_stats`, `drink`). Dati:
il **database degli oggetti** `data/items/items.tsv` (11/11, una riga per oggetto, colonne in
[data/items/README.md](../../data/items/README.md), letto da `tools/build/items_db.py`); le regole che non sono oggetti
(durabilità, `dex_cap`, `magic_max`, dove escono le pozioni) in `data/rules.yaml`. Set minimo deciso il 06/11.

Categorie del database: **consumabili** (`potion`, `scroll`) ed **equipaggiamento** (`weapon`, `armor`, `shield`,
`ring`). Colonna `hands` delle armi: 1 o 2 mani; con un'arma a **due mani** (`itfl` bit 0) lo scudo non si può
indossare, né nell'inventario né alla locanda (test `INV-2H-10/11`, `INN-2H-10/11`), e in combattimento non conta.

## Catalogo

Ogni oggetto ha un id (1..17, 0 = niente) e le tabelle `itcat` (categoria), `itprice` (16 bit), `itilvl`
(livello oggetto; 255 = mai nel bottino), `itdn`/`itds` (dadi), `itval` (valore principale), `itrate`, `itpen`,
`itfl` (flag).

| Id | Nome | Categoria | Valore | Altro | Liv. oggetto | Prezzo |
|---|---|---|---|---|---|---|
| 1 | dagger | arma | 1d4 | cadenza 12 | 0 | 40 |
| 2 | sword | arma | 1d8 | cadenza 14 | 3 | 200 |
| 3 | viking sword | arma | 2d6 | cadenza 20, **due mani** (niente scudo), penetrazione 1 | 12 | 2400 |
| 4 | leather armor | armatura | CA 2 | leggera (DES senza limite) | 0 | 80 |
| 5 | chain mail | armatura | CA 5 | media (DES massimo +2) | 7 | 900 |
| 6 | plate mail | armatura | CA 8 | pesante (DES non conta) | 14 | 3600 |
| 7 | small shield | scudo | CA 1 | | 0 | 60 |
| 8 | mid shield | scudo | CA 2 | | 5 | 400 |
| 9 | tower shield | scudo | CA 3 | | 10 | 1800 |
| 10 | copper ring | anello | +1 | al modificatore di FOR, DES o COS | 7 | 700 |
| 11 | silver ring | anello | +2 | | 12 | 2500 |
| 12 | gold ring | anello | +3 | | 17 | 8000 |
| 13 | minor healing (red) | pozione | cura 20 (Abisso 30) | ricarica 5 s | — | 25 |
| 14 | healing potion (yellow) | pozione | cura 50 (Abisso 75) | ricarica 7 s | — | 90 |
| 15 | greater healing (violet) | pozione | cura 40 + 4 × livello (Abisso 28 + 5 × livello) | ricarica 10 s | — | 250 |
| 16 | portal scroll | pergamena | portale per il villaggio | pila fino a 10 (08/11, prima 4) | 1 | 60 |

`itfl`: armi bit 0 = due mani, bit 1 = libero (era finesse, tolto 08/11), bit 2 = senza modificatori (non usato dal 07/11: erano i pugni); armature = limite al
modificatore di DES (99 = nessuno); pozioni = colore (2 rosso, 7 giallo, 4 viola). `itrate` delle pozioni =
ricarica / 2.

### Cura delle pozioni (15/11, TODO J4)
Due colonne di `data/items/items.tsv`, formato `B` oppure `A*L+B` (L = livello del PG): `heal` nel dungeon (livello PG <= 20,
`MAXLEVEL`) e `heal_abyss` nell'Abisso (livello > 20). `pot_heal` (`combat.asm`) usa `itval`/`itdn` fino al 20 e `pab_val`/`pab_dn`
(emessi da `gen_db.py`, 3 byte ciascuno: rossa, gialla, viola) oltre; la cura è tagliata alla vita massima. Prezzi di negozio
invariati.

**Interpretazione**: il livello del PG decide quanto cura una pozione; il piano decide quali pozioni escono. Nell'Abisso livello = piano per
scelta di progetto.

| | rossa | gialla | viola |
|---|---|---|---|
| dungeon (`heal`) | 20 | 50 (era 60) | 4 × L + 40 |
| Abisso (`heal_abyss`) | 30 | 75 | 5 × L + 28 |

Percentuale della vita massima (vita da `rules.py pg_hpmax`):

| livello | vita | rossa | gialla | viola |
|---|---|---|---|---|
| 1 | 25 | 80% | piena | piena |
| 5 | 62 | 32% | 81% | 97% |
| 8 | 89 | 22% | 56% | 81% |
| 10 | 107 | 19% | 47% | 75% |
| 14 | 144 | 14% | 35% | 67% |
| 15 | 153 | 13% | 33% | 65% |
| 20 | 198 | 10% | 25% | 61% |
| 21 (Abisso) | 207 | 14% | 36% | 64% |
| 30 (Abisso) | 318 | 9% | 24% | 56% |
| 40 (Abisso) | 419 | 7% | 18% | 54% |
| 60 (Abisso) | 679 | 4% | 11% | 48% |
| 80 (Abisso) | 980 | 3% | 8% | 44% |
| 100 (Abisso) | 1321 | 2% | 6% | 40% |
| 150 (Abisso) | 2273 | 1% | 3% | 34% |
| 200 (Abisso) | 3425 | 1% | 2% | 30% |
| 255 (Abisso) | 4872 | 1% | 2% | 27% |

La viola cura tutta la vita solo ai livelli 1–4 (4 × L + 40 supera la vita); `piena` = cura tagliata alla vita massima.

**Pozioni che escono nell'Abisso** (non ancora implementato in asm, TODO H3; la formula è in `data/rules.yaml`
`potions.abyss_drop: {red: [30, 40], yellow: [50, 70]}`): peso 1 fino ad `a`, poi (b + 1 − piano) / (b + 1 − a) per a < piano <= b, 0 oltre `b`;
la viola sempre 1. Quindi le rosse escono ai piani 21–40, le gialle 21–70, dal piano 71 solo le viola. `rules.py potion_weights`
e `abyss_weights` la calcolano; i simulatori usano `heal_abyss` oltre il livello 20.

Test: `POT-10` (sanity, ogni pozione a 8 livelli contro la formula in Python), `POTION-10..12` (in gioco). Il livello oggetto 0 degli oggetti base li fa uscire in qualunque tesoro ([Bottino](bottino.md)).

### Nomi: lunghezza massima (08/11)
Il nome si mostra in colonne da **17 caratteri** (`ui_item` riempie di spazi fino a 17): zaino e baule della locanda,
equipped (dopo l'icona), inventario, negozi, riquadro dell'oggetto selezionato. Il **nome mostrato** deve stare in
**16 caratteri** (`NAME_SHOW` in `tools/build/gen_db.py`, che ferma la build se un nome è più lungo), così resta sempre uno
spazio prima della cornice o della colonna accanto:

| Categoria | Come si mostra | Nome in `items.tsv` al massimo |
|---|---|---|
| arma, armatura, scudo | `+3 leather armor` (`+N ` davanti) | 13 caratteri |
| anello | `silver ring dex` (` str`/` dex`/` con` dietro) | 12 |
| pergamena | `3 portal scroll` (quantità davanti, 08/11: senza la `x`; si contano 3 caratteri per una pila fino a 10) | 13 |
| pozione | `greater healing` | 16 |

Oggi i più lunghi sono `leather armor` (13: mostrati 16; `medium shield` è diventato `mid shield` l'08/11) e `greater healing` (15). Caratteri ammessi:
minuscole, cifre, spazio, `'`, `-`, `.` (`asm_str`). Il nome del PG è a parte: 12 caratteri (`NAME_LEN`).

### I byte accanto all'id (`c_eqb`/`c_packb`, `c_eqd`/`c_packd`, `c_eqm`/`c_packm`)
Ogni oggetto posseduto ha tre byte accanto all'id (le tabelle dello zaino proseguono in quelle
dell'equipaggiamento: indice 16..19):
- **bonus**: armi, armature, scudi = **magia +N** (0..3), sommata ad ATT e danno (armi) o alla CA; anelli = la
  **caratteristica** (1 FOR, 2 DES, 3 COS, il nome mostra il suffisso `copper ring str`); pergamene = la
  **quantità** della pila (1..4, `SCR_MAX`); pozioni: non usato;
- **durabilità attuale** e **massima** (armi, armature, scudi; 0 = non si usura).

### Durabilità
Generata quando l'oggetto entra nello zaino (`give_item` → `dur_roll`: bottino, acquisto; dal baule della locanda
arriva con la sua) secondo `rules.yaml durability`:

```mermaid
flowchart LR
    R["rnd 0..99"] -->|"< 75 (DUR_WP)"| P["pesato: minimo = 10 + 8 × ilvl<br/>(DUR_MIN + DUR_PI × ilvl)"]
    R -->|"altrimenti"| U["uniforme: minimo = 10"]
    P --> D["durata = minimo + rnd(0 .. 255 − minimo)<br/>= massima"]
    U --> D
```

In media gli oggetti durano molto (pugnale ~135, spada vichinga ~170) ma ogni tanto un bell'oggetto dura poco
(viking sword sotto 50: ~4%). Usura e rottura: [Combattimento](combattimento.md#durabilità-e-usura-wear-dur_roll);
riparazione dal fabbro: costo 25% del prezzo (`REPAIR_PC`), durabilità al massimo e **massimo − 1** (un
oggetto da 100 si ripara al più 100 volte). Numeri: `tools/simulators/sim_durability.py`.
**Correzione dell'08/11**: `add_to_pack` chiamava `dur_roll` con A = 0 invece dell'oggetto, quindi gli oggetti
nuovi (bottino dei bauli, negozi) avevano durabilità 0 = **non si usuravano**; solo quelli dell'eroe di prova e del
baule della locanda (durabilità già data) si usuravano. Ora la durabilità si tira davvero, come nel simulatore.

Usura misurata con il simulatore (`tools/simulators/sim_durability.py`, PG di riferimento, usura 2/1/1 del 06/11
pomeriggio): l'arma perde ~20 punti per piano ai piani 1–3 e 55–65 ai piani 10–19, **~880 punti in tutto nei
piani 1–19**: con l'arma della sua profondità e la durabilità media **una riparazione ogni ~3 piani** (2,1–3,2
dal piano 8; 6–7 ai primi piani, dove i colpi sono pochi); armatura e scudo 20–45 punti per piano. Un
combattimento con il boss del piano costa all'arma 6–14 punti (12–27 colpi a segno): **con durabilità ≥ 25 non
si rompe mai**, con 20 l'1% al piano 11, con 15 fino al 35% (piani 9–11). L'avviso nell'HUD si accende al
**20% della durabilità massima** (`warn_percent`, dal 06/11 sera; prima "≤ 20 o ≤ 1/8": un pugnale nuovo da 10–15
risultava già danneggiato): con l'arma media della profondità la soglia è 27–34 punti, sopra il rischio del boss
(colonna "avviso" di `tools/simulators/sim_durability.py`). Boss finale: ~28 colpi, ~14 punti, rottura solo con durabilità ≤ 20.

Arma iniziale: fino al 06/11 sera aveva sempre durabilità 10 (`DUR_MIN`) perché `rnd` è 0 dopo `game_start` e lo
xorshift resta fermo; ora `new_character` semina `rnd` dal timer del CIA prima di `dur_roll`. Dopo ogni uso
`ap_d`/`ap_m` si azzerano (`ap_clr`, anche con lo zaino pieno), così un oggetto preso dopo non eredita la
durabilità di un altro.

## Dove stanno gli oggetti

```mermaid
flowchart LR
    B["bottino / negozio"] --> GI{"give_item"}
    GI -->|pozione| BE["cintura c_beltt: 4 posti,<br/>una pozione per posto"]
    GI -->|pergamena| SC["pila nello zaino (max 10)"]
    GI -->|altro| PK["zaino c_pack: 8 posti"]
    PK <-->|Fire nell'inventario| EQ["equipaggiamento c_eq:<br/>arma, armatura, scudo, anello"]
    PK <-->|"baule della locanda (nella locanda)"| ST["baule della locanda: 24 posti<br/>(nel record dell'eroe) + oro (c_sgold)"]
    PK -->|negozio: vendita a un quarto del prezzo| G["oro"]
    EQ -->|"usura a 0"| X["rotto: resta, in rosso,<br/>senza effetto (danno 0, CA 0)"]
```

- **Equipaggiamento** (4 posti, indice = categoria − 1): l'arma non si toglie né si vende (si sostituisce:
  il PG ha sempre un'arma; rotta resta in mano, con danno 0 e il nome in rosso, finché non si ripara o si scambia); uno scudo con la
  vichinga equipaggiata è rifiutato; equipaggiando la vichinga lo scudo torna nello zaino (se c'è posto). Ogni
  cambio chiama `recalc_stats`. Nella locanda (08/11) l'equipaggiamento si cambia dal riquadro equipped, prendendo
  dallo zaino o dal baule; l'arma si può solo sostituire. Il PG senza arma non deve esistere (08/11: tolto il pugnale
  messo d'ufficio da `recalc_stats`). **Audit del 09/11** (lettura del codice, v1.132): `c_eq` non può diventare 0 da nessun
  comando del giocatore. Inventario: l'arma non si toglie (`_unequip`, `cpx #PACK_N`) e la sostituzione scambia con un oggetto non vuoto;
  locanda: `remove` non è offerto per l'arma (`h_rm` = 0 in `h_enter`) e la sostituzione scrive sempre l'oggetto scelto; negozi: l'equipaggiamento
  si ripara ma non si vende (`sh_fire`, voci 8..11); `DEL` (`inv_delete`) agisce solo sullo zaino; rottura: resta in mano a danno 0; morte: tocca solo
  l'oro (`player_die`); baule del dungeon: non tocca l'equipaggiamento; nuovo eroe: `I_START`; varianti di test: `tu_eq` ha un'arma. **Unica lacuna**:
  `load_char` / `migrate_char` non controllano `c_eq` = 0 in un salvataggio (impossibile con i comandi di oggi, ma non verificato per i
  salvataggi creati da build precedenti). Risolta alla radice (decisione del committente, 09/11): nessun controllo al caricamento, `SAVE_VER` alzata a `$C4` così i
  salvataggi precedenti vengono scartati (avviso "bad save file version").
- **Zaino**: 8 posti (`PACK_N`, 07/11 sera; prima 16), dopo ogni cambio compattato e **ordinato per categoria**
  (`sort_pack` → `sort4`, stabile, 08/11: armi, armature, scudi, anelli, pozioni, pergamene). Nell'inventario la
  tasto DEL elimina l'oggetto selezionato (08/11; prima la linguetta `drop`).
- **Pergamene** (08/11): una pila nello zaino (`SCR_MAX` = 10, quantità nel byte del bonus; solo quelle dello zaino
  aprono il portale) e una pila nel baule della locanda (fino a 10): spostandole si accumulano sulla pila che c'è già
  (`st_move`, modulo MENU), quello che non ci sta resta dov'era; con la pila piena: "max 10 scrolls." / "the chest is
  full". Mostrate come `3 portal scroll` / `10 portal scroll`.
- **Cintura**: 4 pozioni (tasti 1–4); se è piena la pozione resta nel baule.
- **Pergamena di portale** (tasto 5): apre un portale accanto al PG verso il villaggio (`c_portal`,
  `c_retlvl` = piano, `c_retx`/`c_rety` = posizione); il portale precedente sparisce. Nel villaggio il portale
  riporta al piano e alla posizione salvati.
- **Baule della locanda** (porta della locanda nel villaggio): 24 posti (`STASH_N`, 07/11 sera; prima 48), su 3 pagine da 8 (08/11), sempre ordinato per categoria. Sta nel **blocco dell'eroe** (dall'08/11 sera: `st_id`, `st_b`,
  `st_du`, `st_m`, 24 × 4 byte), sempre in RAM, e si salva con l'eroe (file `save-0N`, [Salvataggi](salvataggi.md)) con
  "save game" o al cambio di capitolo (dall'11/11 sera uscendo dalla locanda non si salva); il codice della schermata è nel modulo MENU ([Tecnica](tecnica.md#moduli-su-disco)).
- **Oro nel baule della locanda** (07/11 sera): nella schermata del baule la prima riga di ogni colonna è l'oro (zaino =
  `c_gold`, baule = `c_sgold`); Fire sulla riga dello zaino mette **tutto** l'oro nel baule (quello che non ci sta resta addosso, con "the chest is
  full"). **Dal 10/11 niente prelievo** (decisione del committente): Fire sull'oro del baule non fa nulla (`K_GC` in
  `ovlt.asm`), perché i negozi spendono anche l'oro del baule e nel dungeon l'oro addosso non serve (a vita 0 se ne perde
  metà). **Dal 10/11 il baule conta le decine** (decisione del committente):
  `c_sgold` = numero di decine (16 bit, al massimo 65 535 = **655 350 monete**); si spostano solo multipli di 10 e il resto
  (0..9) resta sempre addosso (`st_gold`: `g_div10` / `g_mul10` in `stash_io.asm`). Il baule mostra il **totale in monete** (decine × 10, 6 cifre:
  `ui_x10` + `ui_num6` in `ui.asm`). `c_sgold` sta nell'eroe (`CHRBLK`), non nel
  record del baule: si salva con l'eroe, come l'oro addosso, quindi lo spostamento non può duplicare oro. **Morendo si
  perde metà del solo oro addosso**; quello nel baule resta. L'**oro totale** (scheda del barbaro nel menu) è
  `c_gold + 10 × c_sgold` (24 bit, al massimo 665 350: 6 cifre con `ui_num6`; prima del 10/11 17 bit). Test: `tests/sanity/gold/cases.py`.

## Prezzi

Acquisto = `itprice`; vendita = metà di `itprice` (la magia +N non aumenta il prezzo). **Oro addosso al massimo
10 000** (`GOLD_MAX`, `player.gold_max` in `data/balance.yaml`, 07/11 sera): oro raccolto (mostri, bauli, bauli epici)
oltre il tetto **si perde** (`add_gold16`); la **vendita** che lo supererebbe **non fa nulla**
(`purse_room`, l'oggetto resta nello zaino; dal 10/11 senza messaggio, decisione del committente: caso rarissimo). Oro nel baule della locanda in decine (655 350, dal 10/11).
**Pagamento nei negozi (10/11, decisione del committente)**: acquisto e riparazione si pagano con l'**oro totale**
(addosso + baule della locanda): prima tutto l'oro addosso, il resto dal baule a decine arrotondate per eccesso, e le
unità che avanzano tornano addosso (`gold_need` / `gold_pay` in `ui.asm`; es. 7 addosso, prezzo 15: una decina dal
baule, 2 tornano addosso). Il purse dei negozi mostra il **totale** (`shop_gold` con `sh_mask` <> 0, somma in `gold_total`, anche nella scheda del barbaro; da 100 000 in
migliaia, `657k`); nei bauli dei dungeon mostra solo l'oro addosso. La vendita resta addosso (tetto `GOLD_MAX`).
Test: `tests/sanity/gold/cases.py` (casi del negozio). Salvataggi della v1.58–1.60 con più di 10 000 monete addosso: l'eccedenza si perde al primo oro raccolto
(formato invariato, niente SAVE_VER). Oro iniziale **100** (`PL_START_GOLD`, dal 06/11 sera; prima 1000). Nei negozi l'assortimento dipende
dal livello del PG ([Villaggio](villaggio.md#negozi-enter_shop-sh_draw)). Prezzi proporzionali al guadagno:
**proposta** in [BILANCIAMENTO](BILANCIAMENTO.md) (non applicata, in attesa di conferma).

## Progetto: affissi, unici e memoria (20/11)

**Progetto, non ancora nel codice** (decisioni del committente del 20/11, domande O, E, C1; analisi della memoria F7). Il
database proposto sta in `data/items/next/` (il gioco non lo legge ancora): `bases.tsv` (31 basi, colonna `status`: `today` o
`new`), `prefixes.tsv` (19), `suffixes.tsv` (32), `uniques.tsv` (16, con la finestra `min_level`..`max_level`: prima stesura da
approvare, chiarimento C5) e `affix_rules.yaml` (qualità, scelta degli affissi, formula del valore, anelli, negozi, limiti dei
nomi). Modello: `tools/simulators/items_model.py` (generazione, nome completo, prezzo, controlli: test `ITEMDB-NEXT-10`).
Struttura e scala vengono dai file di DevilutionX (Diablo 1: `itemdat.tsv`, `item_prefixes.tsv`, `item_suffixes.tsv`,
`unique_itemdat.tsv`), riscalate alle nostre regole; i nomi degli affissi sono parole comuni di quelle tabelle, quelli degli
unici sono nostri. I file di DevilutionX non sono nel repository. Quest e premi: [Quest](quests.md).

### Regole decise
| ID | Regola |
|---|---|
| O1, O14 | **31 basi**: 13 armi (dagger, sword, viking sword + 7 nuove a una mano + battle axe, maul, great sword a due mani), 11 armature, 4 scudi, 3 anelli; nessuna grafica nuova (le liste mostrano l'icona della categoria) |
| O2 | Un oggetto è **magico** con probabilità 8% + 3% × T (T = livello del baule / 8), al massimo 60%; fra i magici 40% solo prefisso, 40% solo suffisso, 20% entrambi (da tarare) |
| O3, O12 | **Unici** con valori fissi (pezzi della storia): garantiti da boss, quest e bauli epici; a caso solo dentro la loro **finestra di livelli**, con probabilità alta; ce ne sono anche a basso livello, utili solo lì |
| O4 | Affissi **maledetti** rari (peso 1), prezzo ridotto, **a ogni livello** (20/11: saltano la finestra dei livelli degli affissi) |
| O5 | Meccaniche nuove subito: vita fissa, danno subito ridotto, cadenza, indistruttibile; **dopo la 2.0**: furto di vita e spine |
| O6 | **Requisiti** di FOR/DES (`min_str`, `min_dex`): non si equipaggia senza |
| O7 | Colore del nome: normale bianco, magico azzurro (`UC_MAGIC` = 14, c'è già), unico giallo, maledetto grigio (12: l'11 è "posto vuoto") |
| O8 | **Interfaccia "variante D"**: menu di oggi; nella lista il nome dell'oggetto sotto il cursore scorre nella sua colonna da 16; **riga 22** = icona + nome completo centrato nel colore della qualità (nel baule del piano i messaggi passano alla riga 23); il riquadro "selected item" usa le 3 righe per statistiche e prezzo, prefisso, suffisso (e requisito). Nessun nome oltre 37 caratteri ("of craftsmanship" diventa "of the craft") |
| O9 | Anelli: il metallo decide gli affissi (copper 1, silver 2, gold 2 con almeno uno del livello più alto); il +N alla caratteristica di oggi diventa il suffisso of strength / of dexterity / of vitality |
| O10 | Valore dell'affisso = formula alla nascita (intervallo `value1..value2` della riga, scalato con il livello dell'oggetto da una curva di 2–3 parametri, + un tiro), **salvato nell'oggetto** e fisso per sempre: nell'Abisso i valori crescono (es. of might +10..+25) |
| O11 | Riparazione: 25% del prezzo **con gli affissi** |
| O13 | Basi dell'Abisso con l'Abisso (TODO H3) |
| E1 | **Vendita a un quarto** del prezzo (come Diablo 1): **fatto il 20/11** (`shop_rules.sell_divisor` = 4 in `balance.yaml`, `SELL_SHIFT` in `db.asm`) |
| E2, E3 | I negozi comprano tutto; vendono anche oggetti magici, sempre di più con il livello del PG (all'inizio pochi, ai livelli alti solo magici) |
| E4 | Bauli epici del piano 20: oro casuale **2 000–4 000 a baule** (20/11; abbastanza per l'arma più cara con gli affissi, ~11 600, e qualche riparazione) |
| E5 | Prezzi dei `.tsv` come prima stesura, poi taratura con il simulatore dell'oro |

### Memoria e salvataggi (F7, approvato)
Misure sulla build v1.437: GAME ha 1345 B di margine, le zone del MENU 223 B; il blocco dell'eroe 11 B liberi; il file di
salvataggio 7 B (immagine a `$E000`, plugin di Krill a `$E820`). Il database (2451 B di dati, misurati assemblando le tabelle)
non sta in GAME. Architettura:
- **`IDAT`** a `$E000` (RAM sotto il KERNAL, libera nel villaggio dopo `gfx_install` e nel dungeon, fuori dai salvataggi):
  statistiche e nomi degli oggetti, affissi, poteri degli unici, routine del nome completo, del prezzo e di `dur_roll`. ~2470 B su
  3095 (stima). Si legge entrando nel villaggio, dopo ogni salvataggio e all'avvio della partita (~10 blocchi, ~0,7 s).
  Budget comune con il file MENU, che si appoggia subito sopra: `$E000-$FCFF` = 7424 B.
- **`IGEN`** a `$F817` (codice del MENU morto nel dungeon, fuori da tema e salvataggi): generazione degli oggetti e tabelle che
  servono solo a generare (~730 B su 1257). Si legge scendendo nel dungeon. Prepara anche, uscendo dal dungeon, la **merce
  dei negozi** (buffer di ~56 B a `$FE96`) e l'**oggetto premio** delle ripetibili.
- Accesso con `$01 = $35`, interruzioni spente e NMI su `nmi_stub` (come la zona 2 del MENU), solo nelle schermate.
- **GAME**: escono tabelle, nomi e generatore di oggi, entrano interfaccia, affissi e agganci delle quest: margine ~1250 B (stima).
- **Bauli del piano**: contenuto **rigenerato** dal seme (seme del mondo, piano, nonce del baule) a ogni apertura, salvando solo
  quali oggetti sono presi: ~45 B invece dei 120 di `ch_i`/`ch_b` (generatore deterministico per baule: da verificare).
- **Oggetto** = id + prefisso (id, valore) + suffisso (id, valore) + durabilità + massima = 7 B (oggi 4).
- **Baule della locanda** sotto l'I/O (168 B nei 260 liberi a `LVRAM_end`); blocco dell'eroe ~189 B nella pagina `$9500`.
- **File di salvataggio**: solo i 5 piani del capitolo in corso (C1): ~790 B, 4 blocchi invece di 9.
- Rischi: budget comune MENU + `IDAT`; NPC fissi nelle zone 5–6 del MENU; pagina Q (`QST0` pieno).
