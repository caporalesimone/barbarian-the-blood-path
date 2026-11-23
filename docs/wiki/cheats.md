# Cheat per test e screenshot

Copyright © 2026 - Simone Caporale

Strumenti **per chi sviluppa**: non sono nell'help né nel manuale. Se se ne aggiunge uno va elencato qui.
Dal 15/11 il modo principale è il **menu dei trucchi** nel gioco (sezione che segue); i POKE e il monitor di VICE
(sezioni dopo) restano per ciò che il menu non fa (oro, vita, chiavi, esperienza a piacere) e per gli screenshot automatici.

## Menu dei trucchi nel gioco (voce "cheats", 15/11)

Per provare il gioco senza giocarlo tutto: saltare piani e capitoli, salire di livello, avere gettoni respec, non morire.
(17/11) Il menu è un **modulo su file**, `CHEATS` sul disco (`src/cheats.asm` + `src/cheats/menu.asm`, assemblato con le etichette del
gioco come il LOBBY): `cheat_menu` di GAME lo legge a `$BC00` (lo schermo B del gioco, libero mentre c'è una pagina della UI) e lo
esegue; costa la schermata di attesa a ogni apertura e non occupa memoria del gioco (prima ~395 B nelle build di debug e di test).
Spazio per nuove voci: fino a **1000 B** (oggi ~440 B; la build si ferma oltre). La release non ha né il file né la voce.
Codice in `src/cheats/menu.asm` (`ct_menu`), test `CHEAT-10..22` ([Test](test.md)), screenshot
[docs/screens/trucchi.png](../screens/trucchi.png).

### Come si apre

1. In gioco **RUN/STOP**: si apre il menu di gioco (resume, save game, quit game).
2. Nelle build con i trucchi (sotto) c'è una **quarta voce, "cheats"**, sotto "quit game". Dalla prima voce **W** (o joystick su)
   fa il giro e arriva subito a "cheats"; altrimenti **S** (giù) tre volte. **Fire** la apre.
3. Nel menu dei trucchi: **W/S** o joystick scelgono la voce (il `>` indica il cursore, con giro), **Fire** la esegue,
   **RUN/STOP** torna al menu di gioco e un **secondo RUN/STOP** al gioco. Le conferme appaiono in **riga 23**.

### Le voci

| Voce | Cosa succede | Messaggio (riga 23) | Limiti |
|---|---|---|---|
| `god mode: off/on` | Inverte il byte `godmode`: lo stesso di `POKE 1021,1` e di `TESTGOD` (sezione sotto: il PG non perde vita) | nessuno: lo stato è sulla voce (`off` / `on`) | Nessuno. Resta acceso per tutta la sessione, anche cambiando piano; non si salva |
| `level up` | Esperienza = soglia del livello dopo, poi il passaggio di livello normale (`add_xp`): livello +1, **punti statistica** da `pl_pts` (da spendere nella schermata C), vita piena, lampo, suono, HUD | `level N` (il livello nuovo) | Al livello massimo (20): non cambia nulla, `limit reached` |
| `respec token` | +1 gettone respec (si usa nella schermata C) | `tokens N` (il totale) | Si ferma a `RESP_MAX` (255, `data/rules.yaml`): il messaggio mostra il totale, che non cresce più |
| `next level` | Come le scale in giù, vedi sotto | nessuno (il gioco cambia schermata) | Villaggio 5: `limit reached` |
| `next chapter` | Sblocca il capitolo dopo e **viaggia al suo villaggio** come l'uscita del capitolo (`chap_travel`): **salva** | nessuno (il gioco cambia schermata) | Villaggio 5 (l'ultimo): `limit reached` |
| `gold +1000` | (18/11, committente) **1000 monete addosso a ogni Fire** (`add_gold16`) | `gold N` (l'oro addosso) | Al massimo il tetto del borsello (dal 22/11: 300, +250 per boss di capitolo, `GOLD_MAX` = 1300): il resto va portato nel baule della locanda |

(22/11, committente) **In alto a destra il menu mostra la casella del PG nella mappa**, `x:y` (colonne e righe 0..47 della
mappa del luogo: `ptx`, `pty`), per indicare un punto preciso nelle segnalazioni.

Dettaglio di **`next level`** secondo dove si è:

| Dove | Effetto |
|---|---|
| Piano normale | Il piano sotto, come le scale in giù (il piano lasciato si salva come sempre) |
| Piano del boss di capitolo (5, 10, 15) | Come se il boss fosse morto e (23/11) il passo della catena consegnato: capitolo dopo sbloccato (`c_unl`, anche nel capitolo 1 dove nel gioco lo sblocca la consegna a `QGIV`), niente quest, **ritorno al villaggio del capitolo**, alla cripta (la via in giù), con l'uscita aperta |
| Sala del trono (piano 20) | Come il boss finale morto: `c_won` = 1, `c_unl` = 5, i gettoni respec del dono (`RESP_FINAL`), poi villaggio 4 |
| Villaggi 1-4 | Il **primo piano del capitolo**, come la cripta |
| Villaggio 5 | `limit reached` |

Dettaglio di **`next chapter`**: se `c_unl` è già abbastanza alto non lo cambia, altrimenti lo porta a capitolo + 1. Da un
villaggio parte subito. **Da un piano** il piano viene prima messo nel suo slot (`save_level`, come per le scale) e poi si
parte **senza** lasciare il portale verso il capitolo che si lascia (nessun STASH, `cur_level` e `c_loc` a 0); l'eroe si
salva nel villaggio nuovo. Quindi **dopo `next chapter` non si torna indietro con il portale**.

**Un eroe cambiato con i trucchi è un eroe normale**: nessun segno nel salvataggio né altrove (formato invariato). Un salvataggio
fatto dopo i trucchi si carica anche in una build senza trucchi. Per questo, se serve ripetere una prova, conviene tenere un
eroe "pulito" e lavorare su una copia del disco (o su un altro eroe).

### Ricette

- **Arrivare al capitolo 3 in fretta**: eroe nuovo nel villaggio 1, RUN/STOP, `cheats`, **`next chapter`** (villaggio 2, salvato),
  di nuovo RUN/STOP, `cheats`, **`next chapter`** (villaggio 3, salvato). Due passaggi, nessun piano. Per essere dentro il
  capitolo: poi **`next level`** dal villaggio (primo piano del capitolo 3).
- **Provare la schermata del personaggio con punti e gettone respec**: `level up` quante volte serve (ogni pressione = un
  livello, con i suoi punti statistica), `respec token` una o due volte, poi **RUN/STOP, RUN/STOP** al gioco e il tasto **C**
  (schermata del personaggio: punti in attesa, confirm, reset, respec; [Interfaccia](interfaccia.md)). Per riprovare il "senza punti": spendere
  tutto, il respec resta come unica voce.
- **Sopravvivere a un boss per fare uno screenshot**: `god mode` su `on`, poi `next level` dal villaggio (piano 1) e di nuovo
  fino al piano del boss (5 pressioni in tutto nel capitolo 1: arrivati al piano 5 ci si ferma). **Non ripremere `next level` sul piano del
  boss**: lo uccide e porta al villaggio. Il boss è ancora vivo all'arrivo: lo screenshot si fa lì (a mano o con
  `tools/vice/shot.sh`). Per la sala del trono: `next chapter` fino al villaggio 4, `next level`, e `next level` fino al piano 20
  (sono piani da generare e caricare: qualche secondo ciascuno). Per screenshot **ripetibili** meglio le varianti di test della
  sezione God mode (`TESTGOD=1`, posizione e piano scelti).
- **Vedere la fine del gioco**: dal piano 20, `next level` (boss finale morto, ritorno al villaggio 4 con il dono di gettoni).

### Quali build li hanno, come accenderli e spegnerli

Il flag dell'assemblatore **`CHEATS`** (`-D CHEATS=...`) lo sceglie `tools/build/asm.sh` ([Build](build.md)):

| Build | `CHEATS` |
|---|---|
| debug normale (`./build.sh`, `./build.sh --fast`) | **1** |
| varianti di test (`tools/build/asm.sh test`, anche durante la release) | **1** |
| release (`RELEASE=1`, `./build.sh --release`) | **0** |

Una `CHEATS` esplicita nell'ambiente **vince sempre** (è in `C64_PASS_ENV` di `lab64.env`, quindi arriva ai container):

- `CHEATS=0 ./build.sh --fast`: debug **senza** trucchi (i test `CHEAT-10..21` diventano SKIP);
- `CHEATS=1 RELEASE=1 ./build.sh ...`: release **con** i trucchi (solo per prove: non è la release da consegnare);
- `lab64 run tools/build/asm.sh release-game`: assembla **solo GAME** con i flag della release in `out/tmp/release_game.prg/.lst/.lbl`
  (serve una build già fatta), il controllo di `CHEAT-22`.

Con `CHEATS=0` **non si assembla un solo byte** del menu né della quarta voce: GAME della release uguale byte per byte a quello di
prima dei trucchi (a parte la versione e la riga del `-D` nel listato).

**Costo**: **395 B** di GAME nella build di debug (margine del codice da 2397 a 2002 B), **0 B** nella release.

### Rapporto con i cheat più vecchi

| Cheat | Quando serve ancora |
|---|---|
| God mode dal menu | Stesso byte `godmode` di `POKE 1021,1` e `TESTGOD=1`: acceso dal menu o dal POKE, vale uguale |
| [`POKE 1021,1`](#god-mode-il-pg-non-perde-vita) | Acceso già all'avvio, prima di aprire un menu |
| [`POKE 1020,1`](#avvio-diretto-del-gioco-poke-1020) | Salta il menu del loader: il menu dei trucchi è **dentro** il gioco, quindi si usa dopo l'avvio |
| [`TESTGOD=1`](#god-mode-il-pg-non-perde-vita) | Build di test per screenshot e test automatici, posizione e piano scelti |
| [Tabella dei POKE](#tabella-dei-poke) | Oro, vita, chiavi, esperienza e livello a valori a piacere, che il menu non dà |

### Non verificato

- **Hardware reale** e **vc64web**: i trucchi sono provati solo in VICE (test `CHEAT-*`).
- **`next chapter` da un piano dei capitoli 2 e 3**: i test lo provano dal villaggio 1 (piano 1 -> villaggio 2) e fra villaggi; non dai piani
  dei capitoli 2-3.
- I passaggi **piano -> villaggio** possono incappare nel blocco della musica del villaggio ([TODO](../../TODO.md) A2, c'è anche
  senza i trucchi): per questo `CHEAT-18..19` evitano alcuni percorsi. Se il gioco si pianta dopo `next level` su un
  boss o `next chapter` da un piano, è probabile quello.

## God mode (il PG non perde vita)

- **Dal menu** (15/11): RUN/STOP, `cheats`, prima voce, vedi sopra: stesso byte, nessun POKE.
- **Che cosa fa**: `hurt_player` (`src/game/combat.asm`) salta la sottrazione della vita se il byte `godmode` è
  diverso da 0. Tutto il resto (suoni, stordimento, avvisi dell'HUD, usura) resta com'è. Costo: 5 B di codice.
- **Indirizzo**: `godmode` è un byte del PRG di GAME nel secondo blocco di codice (`CODE2`, `src/game.asm`): l'indirizzo
  cambia con le build, leggerlo da `out/work/game.lbl` (`grep '^godmode' out/work/game.lbl`). `game_start` **non** lo azzera:
  resta acceso per tutta la sessione. Non è nel blocco dell'eroe: non finisce nei salvataggi.
- **Come si attiva**:
  - **Prima del `RUN`** (hardware reale o VICE, 11/11): `LOAD"*",8` poi **`POKE 1021,1`** e `RUN`. `START` legge il
    byte `$03FD` prima di installare Krill (che usa `$0200-$03FF`) e lo scrive in `godmode`. Il byte è libero (dopo il
    trampoline, che finisce prima di `$03FC`) e vale 0 all'accensione e al reset.
  - **VICE, monitor** (partita in corso): `> <indirizzo di godmode> 01` (spegnere: `00`), poi `x`. Monitor remoto (porta
    6510): `printf '> <indirizzo> 01\nx\n' | nc -q1 127.0.0.1 6510`.
  - **Build di test** (`tools/build/asm.sh test`): variabile d'ambiente **`TESTGOD=1`** (`levels.asm`, subito dopo
    `recalc_stats`/`hp_full` dell'eroe di prova). Esempio per uno screenshot nella sala del trono con il boss attivo:
    ```
    env NOKEYS=1 TESTGOD=1 TESTLVL=20 TESTCL=19 TESTSP=1 TESTX=24 TESTY=28 tools/build/asm.sh test
    tools/vice/shot.sh out.png 4 live
    ```
    Senza `TESTGOD=1` il PG di prova (livello `TESTCL`) muore in pochi secondi davanti al boss e lo screenshot
    mostra "you have died".
- **Test automatici**: `tests/regression/balance/test_arena.py` e i bot non lo usano (il bilanciamento deve vedere la morte);
  

## Avvio diretto del gioco (POKE 1020)

`LOAD"*",8`, **`POKE 1020,1`**, `RUN`: `BARBARIAN` salta il suo menu (storia / manuale / gioco) e avvia subito `START`,
come faceva il vecchio disco di sviluppo (tolto l'11/11 sera: c'è un solo disco). Byte `$03FC` (`POKE_SKIP`,
`src/barbarian.asm`), azzerato all'accensione e al reset. Si può combinare con `POKE 1021,1` (god mode):
`LOAD"*",8` / `POKE 1020,1:POKE 1021,1` / `RUN`. Provato in VICE (1541 emulato) l'11/11.

## Quit the game

**quit the game** (oggi solo la schermata dei salvataggi di un'altra versione; il menu dei barbari ha **back to main menu**, 16/11, che ricarica il menu iniziale, mentre **exit game** del menu iniziale torna al BASIC) fa il reset del KERNAL e riporta al BASIC (`READY.`). **Non c'è rientro**: `SYS 49158`,
`bb_entry`, `game_warm`, la copia di `$0400-$07FF` in `$CC00` e i POKE dal BASIC sono stati tolti l'11/11 (ramo
`fast-loader`: dopo l'install di Krill il drive non risponde più al KERNAL e il residente occupa le pagine 2-3).

## Tabella dei POKE

Tranne le prime due righe (prima del `RUN`), si danno dal **monitor di VICE** con il gioco in
pausa (`> aaaa vv`, poi `x` per riprendere) o con un cartridge freezer su hardware reale (**non provato**).
`POKE a,v` in BASIC = `> aaaa vv` nel monitor (esadecimale). I valori a 16 bit si scrivono basso, alto.

`godmode` è una variabile di GAME. I dati dell'eroe stanno nel blocco `CHRBLK` a `$9500` e cambiano solo se cambia il formato del
salvataggio; `hud_dirty` può spostarsi a ogni build. Indirizzi della **v1.64**: in dubbio leggerli da `out/work/game.lbl`
(`grep '^c_hp' out/work/game.lbl`).

| Che cosa | Etichetta | Indirizzo | POKE (decimale) | Monitor VICE | Note |
|---|---|---|---|---|---|
| God mode on | `godmode` | da `out/work/game.lbl` | `POKE 1021,1` prima del `RUN` | `> <indirizzo> 01` | `0` per spegnere |
| Avvio diretto (senza menu del loader) | `POKE_SKIP` | `$03FC` | `POKE 1020,1` prima del `RUN` | — | subito `START`, senza il menu del loader |
| Vita 999 | `c_hp` | `$950A` | `POKE 38154,231: POKE 38155,3` | `> 950a e7 03` | 999 = `$03E7`; sopra la vita massima: comportamento **da verificare** (probabilmente riportata al massimo al primo `recalc_stats`/cura) |
| Oro addosso 1300 (massimo dal 22/11) | `c_gold` | `$9508` | `POKE 38152,20: POKE 38153,5` | `> 9508 14 05` | 1300 = `$0514` = `GOLD_MAX` (ultimo gradino del borsello); oltre il tetto del gradino (`q_flag` bit 4-7), il gioco lo riporta al tetto al primo oro raccolto |
| Oro nel baule 600000 | `c_sgold` | `$956C` | `POKE 38252,96: POKE 38253,234` | `> 956c 60 ea` | 60000 decine = `$EA60` (10/11: il baule conta le decine); massimo 65535 = 655350 monete; si salva con l'eroe |
| 10 chiavi | `c_keys` | `$954E` | `POKE 38222,10` | `> 954e 0a` | massimo 10 |
| Esperienza 12345 | `c_xp` | `$9505` | `POKE 38149,57: POKE 38150,48: POKE 38151,0` | `> 9505 39 30 00` | 24 bit; il livello sale al prossimo guadagno di XP |
| Livello 10 | `c_lvl` | `$9504` | `POKE 38148,10` | `> 9504 0a` | vita massima, attacco ecc. si ricalcolano al prossimo `recalc_stats` (cambio piano, equipaggiamento) |
| Ridisegna l'HUD | `hud_dirty` | `$9120` | `POKE 37152,1` | `> 9120 01` | dopo vita, oro, chiavi; altrimenti l'HUD si aggiorna al prossimo evento |

Esempio dal monitor (god mode + oro + HUD aggiornato, poi si riprende il gioco):
```
> <indirizzo di godmode> 01
> 9508 10 27
> 9120 01
x
```
