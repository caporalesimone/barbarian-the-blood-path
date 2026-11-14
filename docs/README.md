# Wiki di Barbarian: The Blood Path

Copyright © 2026 - Simone Caporale

Documentazione di **come funziona il gioco nel codice** (6502, 64tass). Ogni pagina indica i sorgenti di
riferimento; i numeri citati sono quelli generati da `data/rules.yaml` e `data/balance.yaml` (via
`tools/build/gen_db.py` → `out/work/db.asm`) alla data dell'ultimo aggiornamento della pagina. Se una pagina e il codice
non coincidono, ha ragione il codice: la pagina va corretta (regola in `CLAUDE.md`).

## Pagine

| Pagina | Argomento |
|---|---|
| [Avvio e storia](intro.md) | Build di debug e di release, il loader `BARBARIAN` (menu nella release), `START`, trampoline di caricamento, la storia a scorrimento (LORE): immagini, tecnica, formato di `LDAT` |
| [Architettura](architettura.md) | (11/11) Struttura del codice: programmi su disco, moduli di GAME e dipendenze, memoria e ciclo di vita, banchi `$01`, interruzioni, pagina zero, decisioni architetturali |
| [Flussi del codice](flussi.md) | (11/11) Diagrammi di come gira il codice: avvio, partita, ciclo per fotogramma, IRQ, input, cambio di luogo, generazione, precaricamento, disco, salvataggi, combattimento, IA, morte e portale, schermate, menu del villaggio, musica, sala del trono |
| [Getting started](getting-started.md) | (13/11) **Da leggere per prima**: cartelle, container Docker, come girano build e test, comandi |
| [Architettura Docker](docker-architecture.md) | (14/11) immagini, container, reti e volumi, flusso video/audio/tasti del viewer, con diagrammi Mermaid |
| [Build e strumenti](build.md) | (11/11) Dai sorgenti al disco: generatori, assemblaggio, compressione, dischi, mappe, test |
| [Panoramica](panoramica.md) | Flusso del programma dal caricamento alla vittoria, ciclo di gioco per fotogramma, moduli |
| [Dungeon](dungeon.md) | Generazione dei piani dal seed: stanze, corridoi, scale, temi grafici, sala del trono |
| [Mostri](mostri.md) | Tipi, piazzamento, statistiche per piano, vita, intelligenza, boss del piano, boss finale ed evocazioni |
| [Combattimento](combattimento.md) | Regole d20: PG, attacco, difesa, danni, abilità, Rage/Frenzy, pozioni, esperienza e livelli, morte |
| [Oggetti](oggetti.md) | Catalogo (armi, armature, scudi, anelli, pozioni, pergamena), equipaggiamento, zaino, cintura, baule della locanda |
| [Bottino e bauli](bottino.md) | Cosa lasciano i mostri, bauli del piano, tesori, generazione degli oggetti, oro, chiavi |
| [Villaggio](villaggio.md) | Mappa, negozi, fontana, baule della locanda, portale, leva della sala del trono |
| [Interfaccia](interfaccia.md) | Comandi, HUD, schermate (inventario, negozi, baule, mappa, menu) |
| [Help](help.md) | Il manuale nel loader (programma `HELP`): pagine, ritaglio dell'HUD, come si aggiorna |
| [Refactor dei tasti](refactor-tasti.md) | **Progetto, non nel codice** (07/11 sera): analisi di tasti e menu di ogni schermata, sistema standard a voci e linguette, piano per schermata |
| [Storico del TODO](storico-todo.md) | **Archivio** (08/11): il vecchio `TODO.md` con i lavori fatti, le decisioni datate e le analisi (memoria, salvataggi, Abisso); i lavori aperti stanno in `TODO.md` |
| [Cheat](cheats.md) | God mode (`$9105`, `TESTGOD=1`) e variabili comode dal monitor di VICE, per test e screenshot |
| [Test manuali](manual-tests.md) | 29 test da fare a mano (000–028), solo quelli non automatizzabili: avvio, comandi, gioco, hardware reale |
| [Salvataggi](salvataggi.md) | Cosa si salva, quando, STASH in memoria; formato esatto in [FORMATO_DATI](FORMATO_DATI.md) |
| [Musica](musica.md) | Brani (titolo, villaggio, livelli, boss, combattimento), player unico, file `SNDn`, effetti sonori, jukebox |
| [Prestazioni](prestazioni.md) | Analisi del 10/11: fotogrammi persi nel villaggio e nel dungeon, strumenti e metodo di misura (VICE + monitor remoto), prove colore per tile e scorrimento a casella (non adottate), catena IRQ fragile |
| [Ottimizzazione](ottimizzazione.md) | Analisi dell'11/11: codice morto tolto, procedure duplicate e generalizzazioni da valutare, prestazioni (test PERF), organizzazione |
| [Test](test.md) | Suite smoke / sanity / regression, ID, runner con report, libreria VICE veloce, elenco dei test |
| [Tecnica](tecnica.md) | Memoria, disco, loader, moduli, precaricamento, build, test, arena, simulatori (`tools/simulators/`) |
| [Secondo emulatore](emulatore.md) | (13/11) **vc64web** in `toolchain/vc64web-custom`: cosa sa fare (con i riferimenti ai suoi documenti), quando usarlo al posto o oltre a VICE, test `EMU-10..16`, trappole misurate |
| [Fast loader](FastLoader.md) | (11/11, ramo `fast-loader`) **Krill's Loader r194**: architettura (chi installa, residente, caricamenti, salvataggi con il plugin, memoria), build, misure prima/dopo, compatibilità |
| [Quest system](quests.md) | **Progetto, non nel codice** (07/11): quest, NPC, tre villaggi, trama e sottotrama, stanze fisse e dal seed, costi, open point |
| [Analisi dell'assembly](../out/work/asm_audit/analisi_assembly.md) | Analisi del codice assemblato (11/11, `tools/build/asm_audit.py`): codice non raggiunto, ripetuto, spioncino, routine più grandi |
| [Bestiario](bestiario.md) | Mostri per capitolo (11/11): `data/monsters/bestiary.tsv` (sorgente dei mostri, modello `monstdat.tsv` di Diablo), boss di capitolo e concept di 3 capitoli |
| [Capitoli](capitoli.md) | **Analisi, non nel codice** (11/11): gioco diviso in capitoli (villaggio, piani, mappa finale) e Abisso a 255 piani; `data/chapters.yaml` per atlante e simulatori |

## Documenti di riferimento

| Documento | Contenuto |
|---|---|
| [FORMATO_DATI.md](FORMATO_DATI.md) | Formato byte per byte dei file su disco e dei salvataggi |
| [memory-map/index.html](../out/work/memory-map/index.html) | Mappa automatica della memoria e del disco (toolchain, a ogni build) |
| [mappa_ram.html](../out/work/memory-map/mappa_ram.html) / [mappa_disco.html](../out/work/memory-map/mappa_disco.html) | Mappe curate a mano, generate a ogni build |
| [grafica/index.html](../out/work/atlas/index.html) | Atlante grafico (generato a ogni build): tutti i tile di villaggio, dungeon (8 palette) e sala del trono con id e lettere, mappe a griglia con zoom al passaggio del mouse, composizioni, titolo, charset, sprite, font; `out/work/atlas/tiles.json` |
| [SISTEMA_COMBATTIMENTO.md](SISTEMA_COMBATTIMENTO.md) | Progetto del sistema d20 (05/11) |
| [BILANCIAMENTO.md](BILANCIAMENTO.md) | Proposta di bilanciamento a 20 piani (05/11) e ritarature |
| [balancing-guide.md](balancing-guide.md) | **Guida al bilanciamento**: strumenti, obiettivi, procedura passo per passo, quante prove, errori da non ripetere |
| [simulazione_regole.html](../out/work/simulators/simulazione_regole.html) | Report del simulatore (`tools/simulators/sim_rules.py`) |

## Stato (07/11/2026)

- 07/11 (v1.27): menu d'avvio nel loader `BARBARIAN` e la storia a scorrimento LORE con immagini; v1.28: build di debug
  (di tutti i giorni) e di release (su richiesta), `START` = avvio del gioco ([Avvio e storia](intro.md)); v1.30:
  logo e pagina dei tasti nel loader, `START` di release con la barra di caricamento, storia più lenta, menu dei
  barbari nuovo (quit = BASIC, nessun rientro), oggetti rotti che restano senza effetto (armi danno 0, armature e scudi CA 0; niente pugni, `SAVE_VER` $C1), lettere
  dell'HUD solo per le abilità disponibili, baule aperto che restava sulla mappa dopo il ritorno al piano.
  v1.34: RUN/STOP esce dalla scheda del barbaro; il manuale `HELP` nel loader (5 pagine, ritaglio dell'HUD); test
  lenti solo nella build di release.

- Implementato: 20 piani (19 + sala del trono), regole d20, abilità H J K L con Rage (U) e Frenzy (O), pozioni a
  cura fissa con ricarica, anelli, durabilità con riparazione dal fabbro (arma rotta: danno 0), chestLevel e nuovo motore del
  bottino, bauli epici per categoria, salvataggi compatti con numero di partita (piani ripopolati a ogni avvio),
  tempo giocato dall'orologio TOD del CIA e morti, baule della locanda su disco (24 posti e l'oro), help, villaggio nuovo con cimitero e cripta, ruscello,
  ponte e minimappa a icone, musica nuova (player unico, brani su disco scelti a caso per piano, jukebox sul disco di
  sviluppo). Simulatori in `tools/simulators/` allineati al codice.
- Non ancora implementato: The Endless Abyss (piani 21+), boss intermedi / mini quest (idea), colori per tile
  nel villaggio (limite del motore: `villaggio.md`), musica nel menu principale (tolta il 06/11). Lavori aperti in
  `TODO.md`.
