# Refactor dei tasti e dei menu (progetto, 07/11 sera)

Copyright © 2026 - Simone Caporale

**Stato: fatto il 07/11 sera (v1.67+)** — sezione 6. Com'è nel codice: [Interfaccia](interfaccia.md#schermate-un-solo-modo-di-muoversi-0711-sera).
Questa pagina resta come progetto e storia delle decisioni. Lavoro chiuso (v1.67+); la voce del vecchio TODO sta in [storico-todo.md](storico-todo.md); ciò che resta (negozi in overlay) è in `TODO.md` 6.3.

Decisioni del committente (07/11 sera) che questo progetto deve rispettare:
1. nelle domande y/n **il tasto Fire vale come Y**;
2. nei negozi l'**uscita è una voce selezionabile** con il cursore `>`, non un tasto;
3. le **pagine e le modalità** (compra/vendi, pagine del baule) sono **tab** selezionabili con il cursore, con una
   grafica "a linguette" facile da capire; **niente destra/sinistra per spostarsi**: si seleziona la linguetta (o
   qualcosa di ancora più semplice, purché si selezioni);
4. si rivedono **tutti** i menu, anche quello dei bauli;
5. un **sistema standard riusabile** il più possibile;
6. nella casa del PG serve un riquadro con le **statistiche dell'oggetto selezionato** (fatto il 07/11 sera: c'è già);
   la schermata della casa può restare diversa dalle altre purché usi la **stessa zona di memoria** (modulo OVLT).

## 1. Come funzionano i tasti oggi

`read_input` (`src/game.asm`, chiamata ogni fotogramma da `ui_input` e dal ciclo di gioco):
- legge il joystick 2 in `joy` (bit 0 su, 1 giù, 2 sinistra, 3 destra, 4 fire) e i tasti **appena premuti** in
  `joynew`;
- legge le 8 righe della matrice della tastiera in `keyrows` e i tasti appena premuti in `keynew[riga]`;
- **W A S D e spazio sono aggiunti a `joy`** come se fossero il joystick (W su, S giù, A sinistra, D destra, spazio
  fire). È qui la radice dei tasti sovrapposti: ogni schermata che legge una lettera fra W A S D legge anche una
  direzione, e viceversa.

Le schermate leggono i bit direttamente (`lda keynew+4 / and #$02` = I, ecc.): non esiste una tabella dei tasti,
quindi ogni schermata ha la sua copia del ciclo di lettura e le sue scelte.

Bit letti nel codice (riga della matrice, maschera):

| Tasto | Lettura | Dove |
|---|---|---|
| RETURN | `keynew & $02` | `ui_fire` (= fire), uscita dal negozio, conferma del nuovo barbaro |
| DEL | `keynew & $01` | scheda del barbaro (indietro), nuovo barbaro (cancella) |
| cursore ←→ | `keynew & $04` | scheda del barbaro (start/delete) |
| cursore ↑↓ | `keynew & $80` | nuovo barbaro (cambia campo) |
| F1 | `keynew & $10` | nuovo barbaro (seed) |
| A | `keynew+1 & $04` | baule: prendi tutto |
| S | `keynew+1 & $20` | negozio: compra ↔ vendi |
| D | `keynew+2 & $04` | inventario: cancella |
| H J K L U O | righe 3–5 | gioco: abilità e poteri |
| Y | `keynew+3 & $02` | tutte le domande y/n |
| N | `keynew+4 & $80` | tutte le domande y/n |
| I | `keynew+4 & $02` | gioco: inventario; chiude inventario, baule, casa |
| M | `keynew+4 & $10` | gioco: mappa |
| 1 2 3 4 5 | righe 7, 7, 1, 1, 2 | gioco: pozioni e pergamena |
| Q | `keynew+7 & $40` | negozio: esce (**non documentato**) |
| RUN/STOP | `keynew+7 & $80` | gioco: menu; menu di gioco: resume; y/n: no; scheda, nuovo barbaro, casa: indietro |
| spazio | in `joy` bit 4 | ovunque come fire |

## 2. Inventario schermata per schermata

Legenda: **dup** = due tasti con lo stesso effetto non detti nell'help; **ND** = non documentato; **conf** = conflitto
con W A S D / spazio; **inc** = incoerente con le altre schermate.

| Schermata (routine) | Tasti letti | Problemi |
|---|---|---|
| Gioco (`handle_keys`, `act_tick`) | stick/WASD, fire/spazio, H J K L, U O, 1–5, I, M, RUN/STOP | nessuno: tutto nell'help |
| Inventario (`ui_inventory`, 144 B + `inv_act` 176 + `inv_delete` 74) | su/giù (stick, W/S), ←→ (stick, A/D) = cambia colonna, fire/RETURN/spazio = usa, **D** = cancella, I = chiude | **conf**: D è anche "destra": premendo D con la tastiera si apre la domanda di cancellazione invece di cambiare colonna; **inc**: si esce con I (tasto), nei negozi con sinistra; RUN/STOP non chiude |
| Domanda y/n (`ui_yesno`, 28 B) | Y, N, RUN/STOP = N | manca **fire = Y** (decisione 1); con la tastiera Y/N sono lontani dalle mani (WASD + HJKL) |
| Negozio (`enter_shop` 154 B + `shop_screen` 923 + `shop_dynamic` 233 + buy/sell/repair/ask ~1160) | su/giù; **destra** o **S** = compra↔vendi; **sinistra** o **RETURN** o **Q** = esce; fire = compra/vendi; nella domanda anche **sinistra = no** | **conf**: S è "giù" con la tastiera: chi scende con S cambia modalità; **ND**: Q; **dup**: tre tasti per uscire e due per cambiare modalità; **inc**: RETURN qui esce, ovunque altro conferma; l'uscita con "sinistra" si fa anche per sbaglio |
| Baule del piano (`ui_chest` 307 B) | su/giù, fire = prendi, **A** = prendi tutto, I = chiude; "locked": un tasto qualsiasi | **conf**: A è "sinistra"; **inc**: I chiude un baule (nel negozio no); RUN/STOP non chiude |
| Casa (`ov_stash`, OVLT) | su/giù (con cambio pagina oltre il bordo), ←→ (stick, A/D) = colonna, fire = sposta, I o RUN/STOP = chiude | **conf**: A/D; le pagine si cambiano "andando oltre il bordo", invisibile a chi non lo sa (decisione 3: tab) |
| Mappa (`ui_minimap`) | un tasto qualsiasi | ok, ma **inc**: unica schermata "qualsiasi tasto" oltre a "locked" |
| Menu di gioco (`ui_gamemenu` 316 B) | su/giù, fire/RETURN = scegli, RUN/STOP = resume | ok: è già il modello "lista + cursore" |
| Quit to main menu (`_qask`) | Y/N/RUN/STOP | come y/n |
| Morte, vittoria, "game saved" (`ui_wait_fire`) | fire/RETURN/spazio | ok |
| Leva (`ui_lever` 340 B) | su/giù = cambia voce, fire | ok (lista di 2 voci) |
| Salvataggi di un'altra versione (`ui_badsave` 232 B) | Y = cancella tutto, N = reset | **attenzione** con la decisione 1: fire = Y cancellerebbe tutti i salvataggi con un tasto che si preme per abitudine; va trasformata in lista a 2 voci (vedi 4.6) |
| Menu principale (`menu.asm`) | su/giù, fire/RETURN; RUN/STOP non fa nulla | **inc**: un barbaro, create e quit sono voci: ok; manca "indietro" (non serve) |
| Scheda del barbaro (`detail_screen`) | **←→** (stick, A/D, cursore) = start/delete, fire/RETURN, RUN/STOP o DEL = indietro | **dup**: DEL e RUN/STOP; decisione 3: start / delete / back come voci in colonna, niente ←→ |
| Nuovo barbaro (`name_screen`) | lettere, DEL, RETURN = campo seguente, cursore ↑↓ = campo, F1 = seed, RUN/STOP | ok (è un modulo di testo, non un menu); **dup**: RETURN e cursore ↑↓ cambiano campo |
| Loader `BARBARIAN` (release) | stick, W/S, cursore, 1 2 3, fire/spazio/RETURN | **dup** voluti e documentati: ok |
| HELP | fire/spazio/RETURN/destra/D/cursore →; sinistra/A/DEL/cursore ←; RUN/STOP, freccia ← | **dup** voluti e documentati: ok |

Conteggio: 5 schermate con conflitto W A S D (inventario, negozio, baule, casa, scheda), 1 tasto non documentato (Q), 4
modi diversi di uscire (I, sinistra, RUN/STOP, "qualsiasi tasto"), 3 modi di cambiare modalità/pagina (destra, S,
oltre il bordo).

Codice d'ingresso duplicato: il ciclo "`ui_input` → RUN/STOP? → su? → giù? → fire?" è copiato 7 volte (inventario,
negozio, baule, casa, menu di gioco, leva, menu principale), ~40–60 B l'uno.

## 3. Il sistema standard: "lista di voci"

Un solo modello per tutte le schermate: **ogni cosa su cui si può agire è una voce**, il cursore `>` passa da una
voce all'altra con **su/giù**, **fire conferma**, **RUN/STOP torna indietro**. Niente lettere di scorciatoia nelle
schermate (restano solo nel gioco: H J K L U O, 1–5, I, M).

### 3.1 Tasti

| Azione | Tasti | Note |
|---|---|---|
| voce precedente / seguente | **joystick su/giù oppure W/S** (W = su, S = giù, come nel gioco), cursore ↑↓ | con giro (dall'ultima alla prima); nei menu ci si muove con W A S D o con il joystick, mai con altre lettere |
| conferma | fire, spazio, RETURN | `ui_fire` com'è oggi |
| indietro / annulla / no | RUN/STOP | in ogni schermata; chiude anche la schermata quando non c'è nulla da annullare |
| sinistra / destra (stick, A/D) | **nessun effetto** nelle schermate | tolti ovunque (decisione 3); alternativa da decidere: ←→ = ↑↓ (stessa voce precedente/seguente), così A/D non fanno danni |
| domanda y/n | **fire** / Y = sì; RUN/STOP / N = no | decisione 1; Y e N restano come alias documentati |
| I, M, A, D, S, Q, DEL, cursore ←→ | **non letti** nelle schermate | il tasto che ha aperto una schermata (I, M) la chiude ancora? vedi 5.1 |

### 3.2 Linguette (tab)

Prima riga utile della schermata (riga 1): le modalità o le pagine come voci in fila, disegnate come linguette,
quella attiva in giallo con il bordo aperto verso il contenuto, le altre grigie:

```
 ┌───────┐┌───────┐┌──────┐
 │ wares ││ sell  ││ exit │
─┘       └────────┴───────┴──────────────
```

Le linguette sono **voci come le altre**: il cursore ci arriva con su (dalla prima voce della lista si sale alle
linguette, da lì si gira all'ultima voce) e **fire** attiva la linguetta (cambia modalità/pagina o esce). Nella fila
delle linguette su/giù si muovono fra le linguette (la fila è una riga di voci orizzontale: l'ordine delle voci
è lineare, "prima le linguette da sinistra a destra, poi la lista dall'alto in basso").

**Uscita**: sempre l'**ultima linguetta** `exit` (o `close`, `back`), così è nello stesso posto in ogni schermata, più
RUN/STOP come scorciatoia.

Con i glifi del font della UI si usano i caratteri del riquadro (`BOX_TL`… già usati da `ui_box`): nessun carattere
nuovo. Costo stimato del disegno delle linguette: ~120 B (una routine condivisa).

### 3.3 Il motore (`ui_menu`, residente in GAME)

Tabella per schermata, in ROM del modulo che la usa:

```
; voce: x, y, tipo, argomento
; tipo: 0 = linguetta (arg = id modalita'/pagina), 1 = voce di lista (arg = indice nell'elenco),
;       2 = azione (arg = id), $FF = fine
menu_shop_buy  .byte 2,1,0,0,  10,1,0,1,  18,1,0,2,  1,3,1,0,  1,4,1,1, ... $ff
```

Routine:
- `ui_menu_run`: ciclo `ui_input` → RUN/STOP → su/giù (cursore sulla voce precedente/seguente nella tabella, con
  giro) → fire → ritorna con A = tipo e X = argomento della voce (RUN/STOP: A = $FF). Chiama una routine di
  disegno del chiamante (`ui_menu_draw`, puntatore) dopo ogni spostamento, che ridisegna solo il cursore (la
  tabella dà x,y di ogni voce) e il riquadro dell'oggetto selezionato.
- `ui_tabs_draw`: disegna le linguette da una tabella di testi, quella attiva in giallo.
- `ui_yesno`: come oggi + fire = sì.

Chi chiama decide cosa fare con (tipo, argomento): è l'unica parte che resta per schermata. Il vecchio codice di
lettura dei tasti (7 copie) sparisce.

Costo stimato (non misurato): motore ~180 B + linguette ~120 B + tabelle ~15 B per schermata; risparmio dai 7 cicli
copiati ~300 B, dalle letture di A/D/S/Q/I/←→ tolte ~80 B. **Netto: circa +50 B nel gioco**, forse zero. Il
margine oggi è 1828 B: non è un problema. OVLT e LOBBY hanno le loro tabelle (OVLT 393 B liberi, LOBBY usa la zona
$C000–$CBFF con `.cerror`).

## 4. Piano schermata per schermata

### 4.1 Inventario
Linguette: `use` · `drop` · `close`. In `use` fire usa/equipaggia (come oggi); in `drop` fire chiede "drop this item?"
(fire/Y = sì). Il tasto D sparisce, I non si legge più (vedi 5.1). Voci: equipaggiamento (4) poi zaino (8) in
ordine di lettura (colonna sinistra 4, colonna destra 4). Le due colonne restano per il disegno; il cursore le
percorre in sequenza senza ←→.

### 4.2 Negozi
Linguette: `buy` · `sell` · `exit` (dal fabbro `sell` fa anche la riparazione, come oggi: fire su un oggetto
indossato usurato = "repair for … g?"). Voci: in `buy` la merce; in `sell` equipaggiamento (4) + zaino (8). Via
S, Q, RETURN-esce, sinistra-esce, destra. La domanda di conferma: fire/Y sì, RUN/STOP/N no (via "sinistra = no").
È la schermata che cambia di più (~2,4 KB oggi): il refactor è il momento giusto per portarla in overlay
(`TODO.md`: negozi in overlay, 1792 B di zona, oggi OVLT ne usa 1399 → **non ci stanno insieme**: servirebbe un
secondo overlay o ridurre il codice; da misurare dopo il refactor).

### 4.3 Baule del piano
Voci: i 4 oggetti, poi due azioni in basso `take all` · `close`. Via A e I. "locked": fire o RUN/STOP (non "un
tasto qualsiasi").

### 4.4 Casa del PG (OVLT)
Linguette: `pack` · `chest 1` · `chest 2` · `exit`. La linguetta attiva dice **in quale colonna sta il cursore**
e quale pagina del baule è mostrata; le due colonne restano affiancate (la schermata resta "custom", nel modulo
OVLT: decisione 6). Voci della colonna attiva: la riga dell'oro, poi gli oggetti. Fire sposta dall'altra parte
(l'oro: tutto). Via A/D e il cambio pagina "oltre il bordo". Il riquadro delle statistiche dell'oggetto c'è già.

### 4.5 Scheda del barbaro (LOBBY)
Voci in colonna nel riquadro basso: `start` · `delete barbarian` · `back`. Via ←→ e DEL. RUN/STOP = back.

### 4.6 Salvataggi di un'altra versione
Da y/n a lista di 2 voci: `delete all saved games and play` · `quit the game`, cursore su **quit** all'apertura:
così fire per abitudine non cancella nulla. (Senza questo cambio la decisione 1 renderebbe pericolosa la
schermata.)

### 4.7 Mappa, morte, vittoria, "game saved", "locked"
Fire o RUN/STOP chiudono (al posto di "qualsiasi tasto" nella mappa e in "locked"). Nessuna lista.

### 4.8 Menu di gioco, leva, menu principale, loader, HELP
Già liste: si portano sul motore comune (menu di gioco, leva, menu principale) senza cambiare i tasti. Loader e
HELP restano com'erano (programmi a sé, tasti documentati). Nel menu principale `quit the game` resta una voce.

### 4.9 Nuovo barbaro
Resta un modulo di testo. Unica modifica: RETURN sull'ultimo campo conferma, cursore ↑↓ cambia campo (come oggi);
da decidere se togliere il **dup** (RETURN = campo seguente).

## 4bis. Bozze delle schermate (40 × 25, come verranno sul C64)

Convenzioni delle bozze: `>` = cursore; la linguetta attiva è scritta fra `[ ]` (nel gioco: gialla, bordo aperto
verso il contenuto), le altre fra `( )` (grigie); `exit` è sempre l'ultima linguetta. Il cursore passa dalle
linguette alla lista con **giù** e torna su con **su** (giro: dall'ultima voce della lista si risale alle linguette).
Righe 23–24: aiuto in grigio, sempre lo stesso testo: `w/s or stick: move   fire: select   run/stop: back`.

### Negozio, linguetta `buy`

```
                 BLACKSMITH
 [ buy ]( sell )( exit )
 +------------------------------+-------+
 | wares                        | stats |
 |> dagger                 40 g | dmg   |
 |  sword                 200 g | 1d4+4 |
 |                              |finesse|
 |                              |       |
 +----------------+-------------+-------+
 | purse     5000 | backpack: 3 free    |
 +----------------+---------------------+
 | about                                |
 | welcome, warrior! the finest steel   |
 | in the realm is forged right here.   |
 | sell your goods for half their price.|
 | the stock changes at every visit.    |
 +--------------------------------------+
 | message                              |
 | buy for 40 g?  fire: yes  run/stop: no|
 +--------------------------------------+
 w/s or stick: move  fire: select  run/stop: back
```

Con il cursore sulla fila in alto: `>[ buy ]( sell )( exit )` → fire su `sell` passa alla vendita, su `exit`
esce. Dal fabbro la seconda linguetta è `( sell/repair )`.

### Negozio, linguetta `sell`

```
                 BLACKSMITH
 ( buy )[ sell ]( exit )
 +--------------------------------------+
 | equipped                             |
 |  weapon   +1 sword                   |
 |  armor    +3 plate mail              |
 |  shield   +2 medium shield           |
 |  ring     silver ring dex            |
 +--------------------------------------+
 | pack                                 |
 |> +2 viking sword    3 portal scroll  |
 |  dagger             gold ring con    |
 |  +1 chain mail      leather armor    |
 |  tower shield       copper ring str  |
 +----------------+---------------------+
 | purse     5000 | selected item       |
 | offer     450 g| dmg 2d6+2  2h pen 1 |
 |                | val 450  d 168/168  |
 +----------------+---------------------+
 | message                              |
 |                                      |
 +--------------------------------------+
 w/s or stick: move  fire: select  run/stop: back
```

Ordine del cursore nella lista: weapon, armor, shield, ring, poi lo zaino colonna sinistra dall'alto, poi colonna
destra (12 voci, con giro). Dal fabbro fire su un pezzo indossato usurato chiede `repair for 50 g?`.

### Inventario

```
 inventory - conan                 2350
 lvl 1   xp 340            [ use ]( drop )( close )
 hp 25/25  att +6  ac 22   str 16 dex 17 con 15
 +--------------------------------------+
 | equipped                             |
 |  weapon   +1 sword                   |
 |  armor    +3 plate mail              |
 |  shield   +2 medium shield           |
 |  ring     silver ring dex            |
 +--------------------------------------+
 | pack                                 |
 |> +2 viking sword    3 portal scroll  |
 |  dagger             gold ring con    |
 |  +1 chain mail      leather armor    |
 |  tower shield       copper ring str  |
 +----------------+---------------------+
 | belt           | selected item       |
 |  o  -  o  o  s | dmg 2d6+2  2h pen 1 |
 |                | val 450  d 168/168  |
 +----------------+---------------------+
 drop this item?  fire: yes  run/stop: no   (solo in modalita' drop)
 w/s or stick: move  fire: select  run/stop: back
```

In `use` fire usa/equipaggia; in `drop` fire chiede la conferma; `close` o RUN/STOP chiudono (e `I`, se si
decide così: punto 5.1).

### Baule del piano

```
                 golden chest
 gold +120   keys 2/10
 +--------------------------------------+
 |> +1 sword                            |
 |  healing potion                      |
 |  leather armor                       |
 |  -                                   |
 +--------------------------------------+
 ( take all )( close )
 w/s or stick: move  fire: select  run/stop: back
```

Le due azioni stanno **sotto** la lista: il cursore scende dagli oggetti a `take all` e `close`. Niente A, I.
Baule chiuso: `it is locked. you need a key.` + `fire or run/stop: close`.

### Casa del PG (OVLT)

```
                  your home
 ( pack )[ chest 1 ]( chest 2 )( exit )
 +------------------+-------------------+
 | pack             | chest        1/2  |
 |   2350           |>  64000           |
 |  +2 viking sword |   +1 sword        |
 |  dagger          |   -               |
 |  +1 chain mail   |   -               |
 |  tower shield    |   -               |
 |  3 portal scroll |   -               |
 |  gold ring con   |   -               |
 |  leather armor   |   -               |
 |  copper ring str |   -               |
 |                  |   -               |
 |                  |   -               |
 |                  |   -               |
 |                  |   -               |
 +------------------+-------------------+
 |                  | selected item     |
 |                  |                   |
 +------------------+-------------------+
 w/s or stick: move  fire: move item/gold  run/stop: back
```

La linguetta dice **quale colonna è attiva** (`pack`, `chest 1`, `chest 2`): il cursore sta solo lì; fire sposta
l'oggetto (o tutto l'oro) dall'altra parte. Le due colonne restano visibili insieme (schermata custom di OVLT).

### Scheda del barbaro (LOBBY)

```
                 saved game
 +--------------------------------------+
 | barbarian                            |
 |  name   conan            game    1   |
 |  seed   r93818           time  0h 0m |
 +------------------+-------------------+
 | progress         | stats             |
 |  level        1  |  max hp       25  |
 |  experience 340  |  attack        6  |
 |  gold     66350  |  armor class  22  |
 |  deepest lvl  5  |  str          16  |
 |  kills      137  |  dex          17  |
 |  deaths       0  |  con          15  |
 +------------------+-------------------+
 |> start                               |
 |  delete barbarian                    |
 |  back                                |
 +--------------------------------------+
 w/s or stick: move  fire: select  run/stop: back
```

### Salvataggi di un'altra versione (da y/n a lista)

```
   saved games from a different version
   of the game were found on this disk.

      delete all saved games and play
   >  quit the game

 w/s or stick: move  fire: select
```

Il cursore parte su `quit the game`: fire premuto per abitudine non cancella nulla.

### Domanda y/n (ovunque)

```
 delete this barbarian?  fire/y: yes  run/stop/n: no
```

## 5. Punti da decidere (committente) — chiusi il 07/11 sera con le proposte

Il committente ha chiesto di implementare senza scegliere: si sono applicate le proposte (1: I e M chiudono la loro
schermata; 2: ←→ senza effetto; 3: `take all` come azione — una linguetta-azione in riga 1, senza modalità attiva;
4: negozio in overlay **dopo**, non fatto; 5: ordine seguito in un'unica passata). In più: "quit to main menu" si chiama
**quit game** (richiesta del 07/11 sera: stessa azione, salva e torna al menu dei barbari) e il baule del piano ha i
riquadri come le altre schermate.

1. **Il tasto che apre chiude?** I apre l'inventario: lasciare che I lo chiuda anche (comodo, un alias documentato)
   o solo `close`/RUN/STOP (più pulito)? Proposta: **sì, I e M chiudono la loro schermata**, documentato nell'help
   come "[i] again or [run/stop]: close".
2. **←→ nelle schermate**: nessun effetto, oppure uguali a ↑↓? Proposta: nessun effetto (decisione 3 letterale).
3. **Baule del piano**: `take all` come azione in lista (4.3) o come linguetta? Proposta: azioni in lista (è un
   comando, non una modalità).
4. **Negozio in overlay** insieme al refactor, o dopo?
5. **Ordine dei lavori**: 1) `ui_yesno` con fire (10 minuti, isolato, chiude la decisione 1); 2) motore + linguette
   + inventario + baule (un pomeriggio); 3) negozi; 4) casa (OVLT); 5) scheda, badsave, mappa; 6) help, manuale,
   wiki, test (`tests/regression/saves/test_saves.py` c7 simula ←→ e fire nella scheda: va riscritto; `test_items.py` chiama
   `shop_repair` direttamente: ok; `test_rel.py` chiama `st_move` con `st_col`/`ui_cur`: da adattare).

## 6. Stato

| Parte | Stato |
|---|---|
| `ui_yesno`: fire = Y | fatto |
| motore `ui_nav` + linguette `ui_tabs` + `nav_help` | fatto (`src/game/ui.asm`; motore a voci lineari, non a tabella x/y: ogni schermata disegna il suo cursore con `ui_lc`) |
| inventario | 07/11 linguette `use` · `drop` · `close`; **08/11 niente linguette**: fire = usa, **DEL** = elimina (con conferma), RUN/STOP o I chiudono (decisione del committente) |
| negozi | fatto (`buy` · `sell`/`sell/repair` · `exit`; S, Q, RETURN-esce, ←→ tolti). Overlay: non fatto |
| baule del piano | fatto (riquadri; `take all` · `close`; A e I tolti; "locked": fire o RUN/STOP) |
| casa (OVLT) | 07/11: linguette; **08/11 rifatta senza linguette** (concept con il committente): una sola lista, numero di pagina come pulsante, scelta dell'equipaggiamento, **destra** dallo zaino al baule (unica eccezione a "niente sinistra/destra"); [Villaggio](villaggio.md#baule-di-casa-ov_stash-modulo-ovlt) |
| scheda del barbaro | fatto (`start` · `delete barbarian` · `back` in colonna; ←→ e DEL tolti) |
| badsave come lista | fatto (cursore su quit; quit = `bb_quit`, rientro con `SYS 49158`) |
| mappa / locked / morte / vittoria / game saved | fatto (fire o RUN/STOP; la mappa anche M) |
| menu di gioco, leva | fatto (sul motore; la leva: RUN/STOP non fa nulla, si sceglie una voce) |
| menu principale (LOBBY) | invariato (era già una lista; riga dei tasti uniformata) |
| help, manuale, wiki, test | fatto: `data/help.txt`, `manuale_src.html`, [Interfaccia](interfaccia.md), `test_saves.py` caso 7 (giù + fire) |

Costo misurato: margine di GAME da 1761 a 1361 B (**-400 B**, più della stima di +50 B: il motore e le linguette
costano ~250 B, i riquadri del baule ~90 B, e i vecchi cicli tolti erano più corti del previsto); OVLT da 1399 a
1354 B; LOBBY 2915 B.
