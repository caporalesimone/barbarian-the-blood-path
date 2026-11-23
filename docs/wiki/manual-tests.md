# Test manuali

Copyright © 2026 - Simone Caporale

Solo i test che **non si possono automatizzare**: aspetto, suono, sensazione dei comandi, giocabilità, hardware reale.
Sono già coperti da `tests/run_tests.sh` e quindi **non sono qui**: bilanciamento e regole d20 (simulatore, arena),
avvio e caricamento dei file (`test_start`, `test_lore`), salvataggi e cancellazione del barbaro (`test_saves`,
`test_rel`), generazione dei piani (`test_gen`), oggetti, cintura, pergamene (`test_items`, `test_belt`), mostri
(`test_ai`), riga XP dell'HUD (`test_hudxp`), ritaglio dell'HUD nell'help (`gen_help.py --check`).
Un'informazione non verificata al 100% è marcata **(da verificare)**.

## Come si usa

- Ogni test: numero a 3 cifre (da 000), categoria, titolo, passi, esito atteso. Segnare **OK / KO** e la versione;
  un KO si riporta con passi, versione e screenshot.
- Categorie: **AVV** avvio e menu, **CTL** comandi e schermi, **GIO** gioco (combattimento, oggetti, luoghi, audio),
  **HW** hardware reale e disco.
- Disco: `blood_path_vX.Y_1541.d64` (un solo disco dall'11/11 sera; per partire subito dal gioco `POKE 1020,1` prima del `RUN`)
  (loader con menu, storia, manuale). I test *solo release* non si fanno col debug.
- Avvio: `LOAD"*",8,1` e `RUN`, joystick nella porta 2; in alternativa W A S D e spazio (fire).

| Categoria | Test |
|---|---|
| AVV – avvio e menu | 000–005 |
| CTL – comandi e schermi | 006–013 |
| GIO – gioco | 014–024 |
| HW – hardware reale e disco | 025–028 |

---

## AVV – avvio e menu

### 000 · AVV · Loader di release: logo, voci e tasti (solo release)
1. Avviare la release: logo e tre voci (hear the legend, read the game manual, walk the blood path).
2. Scegliere con joystick su/giù, `W`/`S`, cursori, `1` `2` `3`; confermare con fire, spazio, RETURN.

**Atteso**: logo con i colori giusti, voce selezionata ben visibile, ogni metodo funziona.

### 001 · AVV · Storia a scorrimento (solo release)
1. Scegliere **hear the legend** e guardarla fino in fondo; a metà premere `RUN/STOP`, poi rifarla.
2. Interlinea (15/11): una riga vuota fra le righe di testo, due fra i paragrafi, nessuna immagine sul testo. Tenere premuto **fire (joystick 2)** durante lo scorrimento: velocità doppia, al rilascio normale; tenuto fino alla fine non salta e non esce (si esce con una nuova pressione); lo spazio non accelera.

**Atteso**: immagini e colori corretti, testo leggibile, ritmo di lettura adeguato, nessun glitch (anche a velocità doppia: sprite, colori delle immagini); `RUN/STOP` torna al menu.

### 002 · AVV · Manuale HELP: leggibilità (solo release)
1. **read the game manual**, sfogliare le 5 pagine avanti e indietro.
2. Alla pagina 5 confrontare il ritaglio con l'HUD vero del gioco (test 006).

**Atteso**: nessun testo oltre il bordo o illeggibile, colori coerenti (tasti gialli, note ciano), legenda coerente col ritaglio.

### 003 · AVV · Scheda del barbaro: layout
1. Selezionare un barbaro salvato e guardare la scheda; spostare la selezione con su/giù fra start game, delete <nome>, back.
2. Su delete aprire la domanda "delete this barbarian?" e annullare con `RUN/STOP`; provare che sinistra/destra non fanno nulla.

**Atteso**: riquadri allineati (etichette ciano a sinistra, valori gialli a destra), nessun elenco di oggetti, freccia gialla
sulla voce scelta, domanda leggibile sulla riga dei tasti.

### 004 · AVV · Nuovo barbaro con tastiera reale
1. **create new barbarian**: scrivere il nome, `DEL`, RETURN; seed a mano (6 caratteri) e `F1` (casuale) più volte; `RUN/STOP`.

**Atteso**: caratteri e cancellazione corretti, `F1` cambia il seed, nessun tasto che si ripete da solo.

### 005 · AVV · Elenco dei barbari
1. Con 0, 2 e 5 barbari guardare l'elenco e muovere il cursore.

**Atteso**: "-" per i posti vuoti, il cursore si ferma solo su barbari, create e quit; con 5 barbari "create" non porta a errori.

---

## CTL – comandi e schermi

### 006 · CTL · HUD: aspetto
1. Entrare in gioco e guardare le righe 20–23; salire di livello, cambiare equipaggiamento, riempire la cintura.
2. Provare XP sotto e sopra 10000 (con la variante di test, o giocando): `9999/27K`, `12K/27K`.

**Atteso**: nessun carattere illeggibile o "multicolore", nessuno sfarfallio; ogni lettera abilità (H 1, J 3, K 6, L 12, U 9, O 15)
solo quando disponibile; la riga XP non tocca la barra.

### 007 · CTL · HUD: avvisi (vita bassa, usura)
1. Scendere sotto il 25% di vita; usare un'arma fino al 20% di durabilità e fino alla rottura.

**Atteso**: "HP" lampeggia rosso/giallo con un suono una sola volta; l'icona dell'oggetto lampeggia, poi resta fissa in rosso a
durabilità 0 con "broken". Lampeggio fluido e suono gradevole (giudizio soggettivo).

### 008 · CTL · Movimento: sensazione
1. Camminare nel villaggio e in un dungeon con il joystick 2 e con W A S D.

**Atteso**: scorrimento fine senza scatti, il PG si ferma al rilascio, ostacoli e muri bloccano.
**(da verificare)** con joystick e tastiera premuti insieme.

### 009 · CTL · Schermate e linguette: usabilità
1. Inventario (`I`): fire usa/equipaggia; `DEL` elimina un oggetto (fire = sì, `RUN/STOP` = no); `RUN/STOP` o `I` chiudono.
2. Negozio: `buy` → `sell` (dal fabbro `sell/repair`) → `exit`; comprare e vendere confermando con fire.
3. Baule del piano: fire prende, RUN/STOP chiude, pozione con la cintura piena -> "the belt is full."; locanda: `pack`, `chest 1`, `chest 2`, `exit`.
4. In ogni schermata provare tastiera (W/S, spazio, RETURN, `RUN/STOP`) e joystick; sinistra/destra e A/D non devono fare nulla.

**Atteso**: la linguetta attiva in negativo giallo, il `>` sempre visibile (sulla linguetta o sulla lista), riga 24
uguale ovunque; nessuna lettera "a sorpresa" (D, A, S, Q tolte). Giudizio di comodità: soggettivo.

### 010 · CTL · Mappa (M) e riga del bersaglio
1. Premere `M` nel dungeon e nel villaggio; guardare la riga del bersaglio vicino a porte, fontana, mostri.

**Atteso**: mappa leggibile (villaggio: fiume blu, strade ciano, icone sopra le porte); la barra mostra luogo o mostro con la vita per ~5 s.

### 011 · CTL · Schermi a tutto schermo ripetuti
1. Aprire e chiudere 20 volte inventario, mappa, menu di gioco, negozio, baule.

**Atteso**: dopo ogni chiusura HUD e campo di gioco integri, nessun blocco, nessun residuo.

### 012 · CTL · Menu di gioco
1. `RUN/STOP`: resume, save game, quit game (con `N`, `RUN/STOP`, fire).

**Atteso**: `RUN/STOP` dal menu torna al gioco; quit game con fire salva e porta al menu dei barbari.

### 013 · CTL · Testi in inglese
1. Scorrere menu, HUD, negozi, morte, vittoria.

**Atteso**: tutto in inglese, nomi di oggetti, mostri e abilità non tradotti, copyright "COPYRIGHT 2026 - SIMONE CAPORALE".

---

## GIO – gioco

### 014 · GIO · Abilità: sensazione e durate
1. Con livello adeguato provare H J K L in combattimento, poi Rage (`U`, ~6 s) e Frenzy (`O`, ~5 s).

**Atteso**: la lettera scelta è gialla; Rage dimezza il danno subito, Frenzy dà due colpi per fire; ricarica in ciano.
Fluidità e feedback adeguati (soggettivo).

### 015 · GIO · Giocabilità dei piani 1–5
1. Giocare un barbaro nuovo fino al piano 5 usando negozi e bauli.

**Atteso**: difficoltà ragionevole, nessun picco ingiocabile; annotare morti, pozioni usate, noia. I numeri sono nel
simulatore, ma l'impressione di gioco è solo manuale.

### 016 · GIO · Morte e risveglio
1. Morire con dell'oro addosso.

**Atteso**: "you have died", metà dell'oro persa, risveglio al villaggio vicino al portale, morti +1 nella scheda.

### 017 · GIO · Bauli: mostri vicini, chiavi
1. Fire su un baule con un mostro entro 2 caselle, poi senza; baule con chiave senza e con chiave.

**Atteso**: con mostri vicini non si apre; il baule con chiave richiede la chiave; aperto sparisce dalla mappa al rientro nel piano.

### 018 · GIO · Negozi: acquisto, vendita, riparazione
1. Fabbro, alchimista: comprare, vendere, riparare un oggetto usurato (fire su indossato).

**Atteso**: acquisto a prezzo pieno, vendita a metà, riparazione al 25% del prezzo; senza oro o posto non compra.
L'assortimento cambia a ogni visita e cresce col livello. **(da verificare)**: quali acquisti chiedono la conferma y/n.

### 019 · GIO · Baule della locanda
1. Entrare nella locanda, spostare oggetti zaino ⇄ baule (24 posti, 3 pagine); Fire sulla riga dell'oro di ciascuna colonna (sposta tutto l'oro, addosso al massimo 10000); uscire con `I` o `RUN/STOP`: compare "saving barbarian..." (~3 s).
2. Spegnere **senza** passare dal menu RUN/STOP, riaccendere e continuare.
3. Entrare e uscire dalla locanda senza premere Fire.

**Atteso**: oggetti al loro posto, pagine corrette, il baule è per barbaro; dopo lo spegnimento l'oggetto messo nel baule è solo nel baule (non anche nello zaino); al punto 3 nessun salvataggio.

### 020 · GIO · Villaggio: percorsi, porte e fontana
1. Dall'ingresso a sud raggiungere fabbro, alchimista, locanda, fontana, portale e cripta (passando i due ponti).
2. Fire davanti alle porte (anche a 1–2 caselle) e alle case decorative.

**Atteso**: tutto raggiungibile, porte dei negozi e della locanda aperte, case decorative chiuse; la fontana cura camminando sul bordo.

### 021 · GIO · Dungeon: aspetto e scale
1. Scendere fino al piano 8 usando scale e cripta; guardare le mappe e le palette.

**Atteso**: stanze collegate, nessun PG bloccato, palette leggibili, piano 8 con tema rosso; salendo, il piano ricorda
mostri e bauli (stessa partita).

### 022 · GIO · Musica e suoni
1. Ascoltare villaggio, dungeon, combattimento, boss; colpi, bere, aprire un baule.

**Atteso**: un brano per luogo, cambio in combattimento e ripresa, nessun glitch; effetti riconoscibili. Gusto musicale: soggettivo.
Con il disco debug provare anche `JUKEBOX`.

### 023 · GIO · Boss finale, sala del trono e leva
1. Con un barbaro alto (o variante di test) raggiungere il piano 20, battere il boss, tirare la leva.

**Atteso**: "this lever opens the gate to the endless abyss. are you sure?", poi il portale. L'Abisso non è implementato.
**(da verificare)**: tempi e difficoltà su un percorso completo non sono mai stati misurati.

### 024 · GIO · Sessione lunga
1. Giocare 30–60 minuti tra villaggio, 3–4 piani, negozi e baule.

**Atteso**: nessun crash, degrado grafico o sonoro, perdita di dati.

---

## HW – hardware reale e disco

### 025 · HW · Tempi su 1541 reale
1. Su C64 + 1541 (o drive fedele) cronometrare il caricamento di START (release), un cambio piano, un salvataggio completo.

**Atteso**: tempi accettabili (da annotare). **Non misurati finora**: in VICE il salvataggio completo dura ~4–5 s.

### 026 · HW · Salva e continua su disco reale
1. Salvare con `RUN/STOP` → save game, spegnere, riaccendere, riprendere il barbaro.

**Atteso**: livello, oro, equipaggiamento, cintura, chiavi, posizione identici; nessun errore del drive.

### 027 · HW · Disco protetto e file dei salvataggi
1. Provare con disco protetto da scrittura e con `HL` assente.

**Atteso**: nessun crash; senza `HL` si gioca ma l'elenco eroi non si salva (il plugin di Krill non crea file). **(da verificare)**: il comportamento con disco protetto non è definito nei documenti.

### 028 · HW · Tempo giocato (orologio TOD)
1. Giocare 3–5 minuti con alimentatore a 50 Hz originale, salvare, guardare "time" nella scheda.

**Atteso**: "time" cresce dei minuti giocati. Con alimentatori senza segnale a 50 Hz il tempo resta fermo (noto); l'uso del TOD su hardware reale non è verificato.
