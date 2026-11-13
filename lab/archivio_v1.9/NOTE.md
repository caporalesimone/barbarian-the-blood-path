# Barbarian: The Blood Path - C64 (6502, 64tass)

Avvio: monta `blood_path.d64` su unita' 8 (VICE o hardware), `LOAD"*",8,1` poi `RUN`
(da VICE: autostart). I salvataggi vengono scritti sullo stesso disco (non protetto da scrittura):
`CHR0..CHR4` (eroe) e `Ls n` (stato livello: slot, livello).

## Comandi
- Joystick porta 2: muovi, FIRE = attacco. In alternativa WASD + SPAZIO.
- F1 / F3 / F5 / F7: abilita' (Slash L1, Whirlwind L4, Battle Cry L8, Smash L12); il nome compare 2 s nell'HUD al posto di F1..F7.
- 1-4: pozioni (colonne cintura), 5: pergamena portale. I: inventario. M: minimappa.
- Versione: `version.yaml` (`version` software, incrementata da tools/build/release.sh dopo ogni release; `save_version` formato salvataggi, da cambiare a mano). Mostrata nel menu iniziale e nel menu di gioco (RUN/STOP) e nel nome del d64.
- Menu iniziale: fino a 5 eroi, "create new hero", nome max 16 caratteri, univoco (serve la tastiera).
  Selezionato un eroe: schermata riepilogo (livello, XP, oro, piano piu' profondo, statistiche) con conferma / indietro.
- Negozi (porte in citta'): su/giu' scegli, FIRE compra/vende, destra/S = compra<->vende, sinistra/RETURN = esci.

## HUD (fascia fissa in basso, testuale)
Nessuno sprite usato. Righe 21-23 dello schermo, posizione fissa grazie a due IRQ raster per frame (linee 209 e 217):
- riga 1: `HP cur/max` + barra rossa (8 celle); riga 2: `XP cur/prossimo livello` + barra gialla (11 celle);
- riga 3: livello e abilita' F1/F3/F5/F7 (bianco = sbloccata, giallo = selezionata, blu = bloccata);
- riquadro cintura in basso a destra: tasti 1-5, icona (pozione rossa/viola, pergamena) e quantita'.
Il campo di gioco e' alto 20 righe di caratteri (10 tile), sopra una riga-regolo.

## Struttura
src/main.asm (motore, scroll, render incrementale), hud.asm (HUD testuale + IRQ di split), dungeon.asm (generatore da seed), game.asm (combattimento, mostri, HUD, loot),
levels.asm (citta', cambio livello, nuovo eroe), disk.asm (KERNAL SAVE/LOAD), ui.asm (menu, inventario, negozi, minimappa),
tools/build/gen_gfx.py (genera charset e sprite). Build completa + test: `./build.sh` (`--no-test` per saltare i test; richiede 64tass 1.59, Python+Pillow, c1541, VICE per il test di avvio); solo assemblaggio: `tools/build/asm.sh [test]`. Versioni (software e salvataggi): `version.yaml`.

## Raccordo mappa/HUD (schermo SCR_H)
La mappa usa 21 righe (0..20) con scroll fine; a linea 209+hy un IRQ imposta D011 (yscroll 7) e D018 su SCR_H
($8400), uno schermo dedicato con il regolo in riga 20 e il testo HUD in righe 21..23. Il campo termina quindi
sempre a linea 214 e l'HUD cade a 223/231/239: nessun bordo che oscilla. Residuo: 1-2 px di nero a hy=5/6.

## Seed e generazione dei piani
- Il seed e' di 6 cifre in base 36 (0-9, A-Z). Alla creazione del PG la schermata 'new hero' propone un seed casuale, modificabile a mano (CRSR giu'/su cambia campo, F1 ne estrae un altro) prima di confermare il nome. Salvato nel file eroe; visibile nella scheda eroe e nella mappa (non piu' nell'inventario).
- Ogni piano parte da uno stato PRNG ricavato dal seed e dal numero del piano (seed_level): stesso seed + stesso piano = stesso dungeon, mostri compresi.
- Lo stato del PRNG di generazione e' a 16 bit: per ogni piano esistono al piu' 65535 layout distinti (seed diversi possono dare lo stesso piano, raro).
- Ogni piano ha uno stile (lv_style): dimensioni minime delle stanze, probabilita' di stanze assenti (0-3/8), frequenza dei collegamenti extra.
- Salvataggi con versione generatore (c_gver): i vecchi eroi vengono migrati (seed dai 16 bit vecchi, piani rigenerati).
- Bug corretto: rndrange sbagliava il prodotto (moltiplicatore shiftato due volte), restituiva quasi sempre 0.

## Scale e disco
- Sulle scale (giu', su, scale citta') dopo ~1 s fermi compare "S: yes / N: no". Dopo N non richiede finche' non si esce dalla casella.
- Salvataggio/caricamento: schermata testuale con barra a 24 celle x 4 passi (blocchi da 16 byte, OPEN/CHKIN/CHKOUT al posto di LOAD/SAVE).

## Fase 1 (menu, portale)
- RUN/STOP apre il menu di gioco: resume / save game (salva piano + eroe) / quit to main menu (con conferma, senza salvare).
- Uscendo da un negozio non si salva piu'; si salva solo cambiando piano o dal menu.
- Portale: la pergamena lo apre su un tile libero adiacente (il precedente sparisce); da fermi ~1 s sul portale compare la conferma; il portale resta aperto fino alla pergamena successiva. Record: c_portal/c_retlvl/c_retx,c_rety (tile).
- Al salvataggio del piano le posizioni dei mostri vivi vengono aggiornate (sync_monsters); gli HP tornano pieni al ricaricamento.

## Stadi A/B/C (oggetti, bauli, boss)
- Oggetti: id + bonus +N (zaino/equip); armi con danno, swing speed (colpi per Fire), penetrazione; 20 armi uniche (id 25..44).
- Piani: 8 palette (seed+piano). Bauli normali/chiave/oro, chiavi dai mostri, loot dei mostri in baule accanto al corpo.
- Boss: 1 per piano, nome da database 8x8 (seed+piano), HP x3 (max 255), armatura +3. Arma unica dal seed su 1 boss su 5.
- Barra vita+nome: 8 sprite sovrapposti alle prime righe del campo (linee 55..68), IRQ raster a linea 70 ripristina gli sprite di gioco.
  Nota: gli sprite nel bordo superiore chiuso NON sono visibili (il bordo li copre), quindi non e' possibile metterla nel bordo.
- Eroi creati con versioni precedenti non sono compatibili (GVER 4).

## Mostri, bauli, manuale (04/11)
- Mostri comuni per piano: min/max in data/balance.yaml (spawn.min_monsters_per_level / max_monsters_per_level: 5..10, 5..11, 6..13, 7..15, 8..17, 9..19, 10..20, ultimo piano 0 = solo boss finale); il boss del piano e' in piu'.
- Corretto un bug storico in spawn_monsters: roll_mm termina con ldx, il flag Z non era quello del tiro, quindi le stanze con 0 mostri ne ricevevano fino al tetto (29): il numero reale di mostri era sempre ~29.
- Bauli di mostri: la cassa viene messa in coda e piazzata a fine combattimento (mus_cmb = 0), una per frame, nella prima casella libera (nessun baule/oggetto/mostro vivo/PG) raggiungibile dal corpo (BFS, find_free); flush_drops forzato prima di salvare il piano. CH_MAX = 24 per piano (LVLBLK cresce: azzeramento $9000-$9BFF).
- SAVE_VER = $bb (formato cambiato: i salvataggi vecchi vengono segnalati).
- Manuale: sorgente editabile `release/manual/manuale_src.html` (+ `stile.css`, immagini `img/`, `mon/`); segnaposto `{{MONSTER_ROWS}}`, `{{STEP_HDR}}`, `{{MIN_ROW}}`, `{{MAX_ROW}}` riempiti da `tools/manual/gen_manual.py` con `data/balance.yaml`. Rigenera il PDF: `python3 tools/manual/gen_manual.py` (richiede Chrome). Screenshot grezzi in `release/manual/shots` (tools/shots_manual.sh, tools/nametest.py, build 'test' con NOKEYS=1); gen_manual.py li ritaglia in `img/`.
- Testi nell'HUD: codifica 64tass `.enc "hud"` (generata da tools/build/gen_gfx.py in src/gfx_consts.inc): `.text "slash"` produce i glifi HUD; tutte le 26 lettere A-Z, cifre, spazio e '/' hanno il loro glifo.
- Bilanciamento: `python3 tools/sim_combat.py [--scale S]` (Montecarlo vettoriale, ~1,9 M combattimenti a scala 1) -> `release/report/bilanciamento.html` con grafici per armi, armature, scudi, bonus, abilita', mostri e controlli automatici.
