# Help (il manuale nel loader)

Copyright © 2026 - Simone Caporale

Sorgenti: `src/help.asm` (programma), `data/help.txt` (testo delle pagine), `data/help_hud.json` (fotografia
dell'HUD), `tools/build/gen_help.py` (genera `out/work/help.inc` e l'anteprima `out/work/atlas/help.png`). Test: `tests/regression/boot/test_lore.py`
(pagine e ritorno al menu in VICE), `tools/build/gen_help.py --check` (il ritaglio dell'HUD è ancora uguale al gioco).

## Dove sta e cosa costa

- File **`HELP`** sul disco di **release** (38 blocchi, 9,4 KB dal 15/11, con la musica), caricato dalla voce **read the game manual** del loader
  `BARBARIAN` con il trampoline, come `LORE`. Alla fine si torna a `BARBARIAN` (ricaricato dal disco).
- **Sul disco è compresso** (12/11): il file `HELP` è `out/work/helpz.prg` (20 blocchi invece di 38: il player e il brano pesano ~1,6 KB e si comprimono poco): un decompressore in testa
  (`src/help/zx0sfx.asm`) si copia a `$8000` con i dati ZX0 (`out/work/help.zx0`, `tools/build/pack.py`), decomprime `out/work/help.prg` a
  `$0801` e salta al suo `$080D`. `BARBARIAN` lo legge con il KERNAL: nell'emulatore web vc64web il manuale compare
  ~11 s dopo la scelta invece di ~20 s (misura a schermo, risoluzione 1 s). Test: `HELP-Z-10/11` (dati e disco), `LORE-10`
  (release: pagine dal disco).
- È un programma a sé: **non tocca il gioco**. `GAME`, `LOBBY` e gli altri moduli non hanno codice né dati dell'help,
  quindi nessun byte di RAM e nessun ciclo di CPU durante la partita (decisione del committente, 07/11). Il loader è
  sceso da 15 a 13 blocchi (la pagina dei tasti che conteneva è stata tolta).
- Nel disco di debug non c'è (il loader di debug non ha il menu).

```mermaid
flowchart LR
    B["BARBARIAN<br/>voce 2"] -->|trampoline| H["HELP<br/>pagina 1..5"]
    H -->|"fire dall'ultima pagina<br/>o RUN/STOP / freccia a sinistra"| B
```

## Pagine

| # | Titolo | Contenuto |
|---|---|---|
| 1 | moving and fighting | movimento (joystick 2, W A S D), attacco (fire/spazio tenuto), le abilità H J K L con il livello, Rage U e Frenzy O con livello e durata, pozioni 1–4, pergamena 5, I, M, RUN/STOP |
| 2 | fire on places | fire su scale giù/su, cripta, portale (dal piano al villaggio e ritorno), porte dei negozi e della locanda, baule (nessun mostro vicino, chiave per il baule chiuso); la fontana cura camminandoci sopra |
| 3 | inventory, chests and shops | regola comune delle schermate (W/S o leva, fire, RUN/STOP), inventario (fire usa, DEL elimina; oggetti rotti in rosso), baule (fire prende), negozi (fire compra, vende, ripara; R ripara dal fabbro), baule della locanda (pack, chest 1, chest 2, exit), mappa (fire, M o RUN/STOP) |
| 4 | menus and saving | come ci si muove in tutte le schermate (W/S o leva, fire, RUN/STOP), menu di gioco (resume, save game, quit game che salva), menu dei barbari, scheda del barbaro (start, delete, back; domande: fire = sì), nuovo barbaro (RETURN, F1, DEL, RUN/STOP; stesso seed = stesso dungeon), morte (metà dell'oro, risveglio al villaggio) |
| 5 | the hud | **ritaglio dell'HUD vero** con 8 marcatori numerati sopra e sotto, e la legenda: HP/XP, barre, icone dell'usura (lampeggiano al 20%, fisse in rosso se rotte), LV, H J K L (giallo = quella del fire), U O (giallo attiva, bianco pronta, ciano in ricarica), chiavi, cintura (pozioni blu in ricarica, pergamena); la riga in alto del gioco (luogo o mostro con la sua vita) |

Anteprima delle 5 pagine (generata dalla build di release): ![help](../out/work/atlas/help.png)

## Tasti dell'help

| Tasto | Effetto |
|---|---|
| fire, spazio, RETURN, joystick destra, D | pagina seguente; dall'ultima si torna al loader |
| joystick sinistra, A, DEL | pagina precedente |
| RUN/STOP, freccia a sinistra | di nuovo il loader |

Riga 0: titolo della pagina in giallo e "n/5" in ciano; riga 24: "fire: next  left: back  run/stop: menu".

## Tecnica

- Banco VIC 0, schermo `$0400`, charset a `$3000` (`$D018` = `$1C`): codici 0–63 = font della UI
  (`out/work/gfx/uifont.bin`, lo stesso del gioco), codici 64.. = i glifi dell'HUD usati nel ritaglio (29). Il programma
  (codice + pagine) sta in `$0801`–`$2D89` (con il player e Demon's Eye, ~1,6 KB: restano ~630 B sotto `$3000`); un `.cerror` controlla che non arrivi a `$3000`. Variabili del player a `$C000` (170 B, `SP_VARS`).
- Schermo in **modo testo multicolore** (`$D016` = `$18`): il testo ha colori < 8 (alta risoluzione: bianco testo,
  giallo tasti e titoli, ciano note), il ritaglio dell'HUD i suoi colori, con `$D022`/`$D023` del tema fotografato.
  È lo stesso trucco del loader con il logo.
- Pagine: schermo (1000 byte) e colori (1000 byte) in **RLE** (coppie conteggio, valore; 0 = fine), 5 950 byte circa per
  5 pagine. Il disegno spegne lo schermo (`$D011`), decomprime in `$0400` e `$D800`, aspetta un fotogramma e lo
  riaccende. La tastiera passa dall'IRQ del KERNAL (`GETIN`), il joystick dalla porta 2 (`$DC00`, solo le nuove pressioni).
- **Musica** (15/11, ex TODO E4): suona **Demon's Eye** (lo stesso brano del titolo e del menu principale, non piu' la Tavern of Dawn
  immaginata nel TODO: decisione del committente, un solo brano ovunque) con il player unico (`src/common/sid_player.inc`, senza
  `sp_resume` / `sp_release`) tramite `src/common/title_music.inc`, in comune con BARBARIAN. **Clock**: non l'IRQ del KERNAL com'e' (timer
  a ~60 Hz, non verificato a 50 Hz PAL) ma il **CIA1 timer A con latch a 19656 cicli** (312 righe x 63 = un fotogramma PAL): `tm_start`
  mette il vettore `$0314` su `tm_irq` (suona e prosegue in `$EA31`, cosi' `GETIN` funziona come prima) e ricarica il timer; nessun IRQ
  del VIC. **Uscita** (RUN/STOP, freccia, fire dall'ultima pagina): `tm_stop` (`sei`, `sp_stop`, SID tutto a 0 volume compreso, vettore
  `$EA31`, latch del KERNAL `$4025`, IRQ del timer in sospeso confermato) **prima** del `LOAD` del KERNAL che ricarica BARBARIAN
  (il trampolino fa anche IOINIT e RESTOR). Test: `TITLEMUSIC-10` (vettore, 1 chiamata ogni 19656 cicli, ripristino).
  Voci come in START (lead sulla voce 1 del SID), non come nel gioco e in LOBBY (lead sulla 2).

## Il ritaglio dell'HUD

Non è disegnato a mano: `tools/build/gen_help.py --snap` assembla la variante di test **`TESTUI=28`** (livello 15, piano 2,
equipaggiamento e cintura di `test_ui_fill`, arma quasi rotta, 2 chiavi, vita a 40 punti dal massimo, esperienza a metà
del livello), la avvia in VICE, lascia girare **40 giri del ciclo principale** (sempre lo stesso istante: fotografia
ripetibile) e legge dalla memoria le righe 20–23 dello schermo HUD (`SCR_H` + 800), la color RAM, i glifi usati dal
charset del gioco (`$A800`) e `$D022`/`$D023`. Le icone dell'usura, che lampeggiano rosso/giallo, si salvano rosse.
Nell'help si vedono le colonne 1–38 (l'HUD del gioco è a 38 colonne).

**Quando rifarlo**: se cambia la grafica o la disposizione dell'HUD (`src/game/hud.asm`, glifi in `tools/build/gen_gfx.py`).
Il test della release (`tools/build/gen_help.py --check`) rifà la fotografia e la confronta con `data/help_hud.json`: se
differisce fallisce con "rifare tools/build/gen_help.py --snap".

## Come si aggiorna il testo

`data/help.txt`: una pagina per sezione `=== titolo`; ogni riga del file è una riga dello schermo (dalla 2, colonne
1–38: il generatore si ferma se una riga è più lunga o se la pagina supera la riga 23). `[testo]` = giallo (tasti),
`{testo}` = ciano (note), `@hud` = il ritaglio (4 righe). **Ogni tasto o schermata cambiata nel gioco va riportata
qui nello stesso lavoro** (regola in `CLAUDE.md`).

## Tasti del gioco che si sovrappongono (segnalati il 07/11, non cambiati)

Con la tastiera W A S D fanno anche da joystick, quindi in alcune schermate un tasto ha due significati:
- **inventario**: `D` (destra) apre la cancellazione dell'oggetto (che chiede comunque Y/N);
- **baule**: `A` (sinistra) prende tutto;
- **negozi**: `S` (giù) passa da compra a vendi invece di scendere; anche `Q` esce dal negozio (non scritto nell'help).
