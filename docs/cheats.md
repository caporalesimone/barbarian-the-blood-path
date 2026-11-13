# Cheat per test e screenshot

Copyright © 2026 - Simone Caporale

Strumenti **per chi sviluppa**: non sono nell'help né nel manuale. Costano pochi byte e nessun tempo di CPU
misurabile. Se se ne aggiunge uno va elencato qui.

## God mode (il PG non perde vita)

- **Che cosa fa**: `hurt_player` (`src/game/combat.asm`) salta la sottrazione della vita se il byte `godmode` è
  diverso da 0. Tutto il resto (suoni, stordimento, avvisi dell'HUD, usura) resta com'è. Costo: 5 B di codice.
- **Indirizzo**: `godmode` è un byte del PRG di GAME nel secondo blocco di codice (`CODE2`, `src/game.asm`): l'indirizzo
  cambia con le build, leggerlo da `out/game.lbl` (`grep '^godmode' out/game.lbl`). `game_start` **non** lo azzera:
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

**quit the game** (menu dei barbari) fa il reset del KERNAL e riporta al BASIC (`READY.`). **Non c'è rientro**: `SYS 49158`,
`bb_entry`, `game_warm`, la copia di `$0400-$07FF` in `$CC00` e i POKE dal BASIC sono stati tolti l'11/11 (ramo
`fast-loader`: dopo l'install di Krill il drive non risponde più al KERNAL e il residente occupa le pagine 2-3).

## Tabella dei POKE

Tranne le prime due righe (prima del `RUN`), si danno dal **monitor di VICE** con il gioco in
pausa (`> aaaa vv`, poi `x` per riprendere) o con un cartridge freezer su hardware reale (**non provato**).
`POKE a,v` in BASIC = `> aaaa vv` nel monitor (esadecimale). I valori a 16 bit si scrivono basso, alto.

`godmode` è una variabile di GAME. I dati dell'eroe stanno nel blocco `CHRBLK` a `$9500` e cambiano solo se cambia il formato del
salvataggio; `hud_dirty` può spostarsi a ogni build. Indirizzi della **v1.64**: in dubbio leggerli da `out/game.lbl`
(`grep '^c_hp' out/game.lbl`).

| Che cosa | Etichetta | Indirizzo | POKE (decimale) | Monitor VICE | Note |
|---|---|---|---|---|---|
| God mode on | `godmode` | da `out/game.lbl` | `POKE 1021,1` prima del `RUN` | `> <indirizzo> 01` | `0` per spegnere |
| Avvio diretto (senza menu del loader) | `POKE_SKIP` | `$03FC` | `POKE 1020,1` prima del `RUN` | — | subito `START`, senza il menu del loader |
| Vita 999 | `c_hp` | `$950A` | `POKE 38154,231: POKE 38155,3` | `> 950a e7 03` | 999 = `$03E7`; sopra la vita massima: comportamento **da verificare** (probabilmente riportata al massimo al primo `recalc_stats`/cura) |
| Oro addosso 10000 (massimo) | `c_gold` | `$9508` | `POKE 38152,16: POKE 38153,39` | `> 9508 10 27` | 10000 = `$2710` = `GOLD_MAX`; oltre, il gioco lo riporta a 10000 al primo oro raccolto |
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
