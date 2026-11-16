# Storico del TODO (archivio, fino all'08/11/2026)

Copia del vecchio `TODO.md` al momento della riscrittura (08/11 sera, v1.112). Contiene i lavori fatti con la data,
le decisioni prese e le analisi (memoria, salvataggi, Abisso). Si consulta per capire **perche'** una cosa e' stata
fatta cosi'; i lavori ancora aperti stanno in `TODO.md` (riscritto e ordinato). Non si aggiorna piu'.

---

# TODO (da fare al prossimo rilascio, non subito)

- [x] (03/11) Rinominare i file con il nuovo titolo "Barbarian: The Blood Path":
      - immagine disco: release/barbarians_descent.d64 -> nome nuovo (es. blood_path.d64)
      - nome del programma sul disco ("barbarian") e del disco ("barbarian,01")
        -> aggiornare anche il comando di caricamento LOAD"...",8,1 nel manuale/README
      - eventuali riferimenti nel manuale PDF e in NOTE.md
      FATTO: release/blood_path.d64, programma "bloodpath" (LOAD"BLOODPATH",8,1), disco "blood path,bp".
- [x] (04/11) Manuale PDF rigenerato: release/Barbarian_Blood_Path_Manuale.pdf (tools/gen_manual.py).

## Refactoring in corso (04/11) — dopo: bilanciamento
- [x] Grafica su file (GFX0 villaggio, GFX1..GFX8 temi) + cache sotto il KERNAL.
- [ ] Codice solo-villaggio su file (in cache con GFX0) per liberare memoria.
- [ ] Baule di casa su disco: NON ora (oggi 32 B dentro il blocco eroe, gia' salvato su disco; il codice per
      leggerlo/scriverlo a parte costerebbe piu' dei 32 B risparmiati). Da rivalutare se il baule cresce:
      allora caricato in una zona di scratch entrando in casa (max ~3 s accettati).
- [x] Villaggio: piazzetta in mattoni con portale al centro (est), fiori/piante, strada che esce a sud.
- [x] (05/11) 10 livelli: 9 casuali + piano 10 = sala del trono (mappa fissa generata da tools/gen_final.py).
- [ ] Sala del trono su disco: vedi sezione "Piano finale su file" sotto.
- [x] (05/11) Sala del trono: corridoio da sud a nord; alla morte del boss si apre un muro a nord -> corridoio -> grande stanza
      con 4 forzieri e "a suspicious lever". Azione sulla leva: schermata (congratulazioni, uccidere <boss> e' solo l'inizio;
      la leva apre la porta dell'Abisso; "sei sicuro?") con "give up" (esce) / "pull the lever" (al posto della leva un
      portale nero "The Endless Abyss").
- [x] (05/11) Salvataggi: personaggio solo dal menu RUN/STOP (uscita dal menu = salvataggio automatico) + alla creazione;
      stato del piano salvato quando lo si lascia per scale; portale piano<->villaggio senza salvataggio (stato in memoria);
      dal villaggio per scale verso un altro piano: prima si salva lo stato in memoria.
- [x] (05/11) Salvataggio del piano piu' piccolo (formato compatto, REL).
- [ ] The Endless Abyss: temi scelti a caso; piani non salvati, si salva solo il piano raggiunto; portali in citta'.
      PIANO TECNICO (da docs/REFACTOR.md sezione E, cancellato il 06/11): livello = piano anche nell'Abisso, V = piano - 20;
      i mostri partono dalla scheda del piano 20 con la tabella rules.yaml void.table (16 righe: V, CA +, ATT +, vita x,
      danno x) interpolata a 8 bit (128 B); boss con nome vita x1,5 CA +2 ATT +2 (void.boss_hp_mult); 6 spade vichinghe
      dell'Abisso (void_weapons, 3d8..8d8, pen 2..4, magia fino a +8), bottino con chestLevel = 8 x piano (satura a 255
      al piano 31: il chestLevel va riscalato per l'Abisso, es. per_floor 4 oltre il 20); solo pozioni viola; limiti
      8/16 bit verificati nel report (docs/simulazione_regole.html sezione 6). HUD: esperienza a 24 bit (idea: oltre 65535 mostrarla in migliaia con una "k", ~60 B).
      Memoria: oggi ~750 B liberi: serve prima liberare RAM (grafica fissa su file, overlay della sala del trono).
      Ripopolamento nell'Abisso (06/11, da decidere a gioco completato): o si salva solo "piano completato" (niente
      mostri rigenerati) o un bit per mostro ucciso per piano come nel dungeon; i piani dell'Abisso oggi non si salvano.
      - Morte nell'Abisso (05/11, SOSTITUISCE la regola "-2 livelli"): non si perdono livelli ma esperienza.
        Si perde il 10% dell'esperienza richiesta per passare dal livello attuale al successivo, mai sotto la soglia
        del livello attuale: morendo molte volte di fila si svuota solo la barra del livello attuale, l'esperienza
        accumulata nei livelli precedenti resta intatta. La schermata della morte scrive quanta esperienza si perde.
        (Con la curva a 24 bit: perdita = (soglia del livello successivo - soglia attuale) / 10.)
      - Ingresso nell'Abisso: la scelta non e' "procedere o no" ma la modalita': "normal" o "nightmare"
        (nomi nel gioco). Nightmare = morte permanente: alla prima morte l'eroe e' morto per sempre; non si puo' piu' giocare, ma dal menu si possono
        ancora vedere le sue statistiche e l'equipaggiamento. Serve un flag nel blocco eroe (modalita' + morto),
        +1 byte; l'elenco eroi deve mostrare gli eroi caduti (e non farli selezionare per giocare).
      - NOTA: la schermata della leva oggi offre "give up" / "pull the lever": va rifatta con la scelta della modalita'.
      - Citta' nuova nell'Abisso (07/11 sera, richiesta del committente): un secondo villaggio, tutto dell'Abisso, con
        **tutti i mercanti vicini e comodi** (fabbro, armaiolo, alchimista, casa/baule piu' a portata di mano che nel
        villaggio di superficie: pochi passi fra una porta e l'altra), portale per tornare al piano raggiunto.
        **I prezzi dei suoi mercanti si ribilanciano** in base al **livello del giocatore** e al **piano massimo
        raggiunto** (`c_maxd`), non sono fissi come nel villaggio di superficie: l'oro cresce con il piano, quindi i
        prezzi devono seguirlo. Da decidere: formula (prezzo base x fattore del livello/piano massimo?), se vale anche
        per la vendita, assortimento (armi/armature dell'Abisso, `void_weapons`), tetto dell'oro a 16 bit (il baule
        regge 65535: con prezzi in crescita va rivisto, vedi l'oro a 24 bit), e il simulatore (`sim/sim_gold.py`) esteso
        ai piani 21+ e alla vendita degli oggetti. Costo di memoria da stimare (mappa nuova, prezzi calcolati): oggi il
        margine e' ~1,8 KB sotto $8720, i negozi in overlay sono previsti nel TODO.
      DA SVILUPPARE DOPO i bot che combattono nell'arena (test automatici di bilanciamento).
- [ ] Manuale da rivedere tutto (nuovo avvio, salvataggi, bauli, nomi a 12, livelli, immagini da rigenerare).
- [ ] Trono dietro il boss (tile nuovo) - da rivedere.
- [x] (05/11) Titolo "epic chest" nella schermata del baule epico (e nell'etichetta in alto).

- [x] (05/11) Salvataggi in 2 file REL (record da 254 B, riscritti sul posto): prova in VICE prima
      (tempo atteso ~1 s invece di 8,5 s).
      CHARS: record 1 = versione + numero eroi + 5 nomi (12 car.); record 2..6 = blocchi eroe (posizione fissa).
      LEVELS: record 1 = versione; poi 2 record per eroe x piano. Versione diversa: si ricreano i file. Formato compatto con le nuove regole (bauli aperti persi
      cambiando piano, solo i mostri mossi salvano la posizione, niente oggetti a terra/cadaveri).

- [x] (05/11) Un solo file REL "saves" (156 record): piani 1..150, eroi 151..155, elenco eroi 156.
      RUN/STOP e nuovo eroe con una sola apertura del file (rel_hold / rel_done). SAVE_VER $BE.
      Misurato: gm_save 5,8 -> 4,5 s, nuova partita 5,3 -> 4,7 s; MA load_char 1,3 -> 1,7-2,1 s e
      hdr_read 1,0 -> 1,5 s (aprire un REL grande costa ~0,5 s in piu'; ipotesi: 2 side sector invece di 1).
- [x] (05/11) Deciso: file unico. Prova a 2 record per piano SCARTATA (armi con statistiche casuali in arrivo:
      servira' piu' spazio, non meno). Si accetta ~0,5 s in piu' su "continua" ed elenco eroi.
- [ ] Armi con statistiche casuali - vincoli dei salvataggi:
      - eroe: 1 record = 253 B (oggi 129; guardia .cerror in rel.asm). Oggetti dell'eroe: zaino 8 + equip. 4 (baule di casa in un record a parte)
        = 36: +3 B a oggetto = +108 B -> 237 B, al limite. Oltre: 2 record per eroe (cambia la numerazione, SAVE_VER).
      - piano: 3 record = 759 B (caso peggiore oggi ~605 B). Bauli col contenuto salvato: 15 x 4 oggetti.
        Serve un controllo in lv_put (la passata di conteggio c'e' gia'): oltre 759 B non salvare le posizioni dei mostri.
      - Proposta: statistiche ricavate da un seed per oggetto (1 byte) invece di salvarle tutte: +1 B a oggetto.
- [ ] ARMI CON DANNO A DADI + ARMI CASUALI (da decidere in dettaglio prima di implementare; discussione 05/11).
      Notazione nella tabella delle armi (balance.yaml), convertita da uno script (gen_db.py):
        "1d10+2" = 1..10 + 2 = 3..12;  "1d6+2d4+3" = min 1+2+3 = 6, max 6+8+3 = 17.
      La notazione serve anche a capire a colpo d'occhio il danno; lo script calcola e controlla min e max.
      Da decidere:
      1. Tiro a ogni colpo: somma dei dadi veri (curva a campana con piu' dadi) oppure uniforme tra min e max.
         Proposta: dadi veri (fino a 2 gruppi di dadi + costante = 5 B per tipo di arma nel database).
      2. Arma casuale (diversa da un'altra dello stesso tipo): cosa varia quando nasce. Minimo: il
         modificatore magico (+N, esiste gia': 1 B per oggetto, nessun cambio ai salvataggi). Se varia di piu'
         (dadi diversi, proprieta'), serve il seed per oggetto (+1 B) e una funzione seed -> statistiche
         identica in 6502 e Python (xorshift/LFSR, ordine dei tiri fisso, 1..N senza divisione, test VICE=Python).
         Generata quando l'oggetto nasce (baule, drop, negozio) dal generatore deterministico del piano, come oggi.
      3. Limiti: tutto il combattimento e' a 8 bit (danno, vita mostri mhp, vita eroe: max 255).
         Lo script deve verificare danno massimo (dadi + costante + magia + forza) <= 255.
         La vita dei mostri a 255 e' il vero tetto della difficolta': oltre servono 16 bit (+32 B RAM e codice).
      4. Void: un livello tetto (void_cap in balance.yaml) oltre il quale ne' mostri ne' bottino crescono
         (statistiche calcolate con min(piano, void_cap)); la profondita' continua a contare (punteggio).
         Il valore si sceglie con la simulazione (bot nell'arena): al tetto il mostro piu' forte deve restare
         sotto 255 di vita e l'arma migliore deve ucciderlo in un numero di colpi deciso.
      5. Interfaccia: mostrare il danno come "1d10+2" o "3-12" (stampato dai byte del database, niente stringhe).

## Arena e bot (05/11)
- [x] Fase 1: build ARENA (out/arena_game.prg + modulo src/test/arena.asm a $C900), tools/arena.py, test automatico.
      PG e mostri adiacenti, bot fermo che si gira e attacca; abilita' e pozioni con regole semplici.
- [ ] Fase 2: bot che si muove (BOT 1 "approach" c'e' gia' come base), posizioni di partenza a distanza, strategie.
- [ ] Usare l'arena sul combattimento attuale per avere i numeri di riferimento, poi rifare il combat system
      (stile D&D: caratteristiche, bonus di attacco, CA, critici) e confrontare.
- [ ] Confronto arena / tools/sim_combat.py: stessi scenari, medie coerenti.

## Nuovo combat system - decisioni aperte (05/11, dopo la prova dell'arena sul boss finale)
Ordine deciso (05/11): prima le regole nuove (docs/wiki/SISTEMA_COMBATTIMENTO.md), poi il simulatore Python fedele
al codice (verificato contro l'arena), infine l'assembly.
Riferimento misurato (sistema attuale, arena): boss finale con spada lunga +2, cotta di maglia, scudo rotondo:
livello 10-11 perde sempre; dal 12 (sblocco di smash) vince 17-20 su 20 con pozioni; senza pozioni 0-16 su 20.
Causa: armatura sottratta fissa (18 - penetrazione 1) -> la spada fa 1-5 a colpo; smash raddoppia prima della sottrazione.
- [x] (05/11) Il PG non supera il livello 20 finche' non sconfigge il boss finale. Penetrazione = -N alla CA del bersaglio.
- [x] (05/11) Livello con cui si arriva al boss finale: 20. Armatura: solo classe armatura (niente riduzione del danno).
- [x] (05/11) Regole in stile D&D (scala D&D delle caratteristiche), vita a 16 bit, anelli ribilanciati: regole complete
      in docs/wiki/SISTEMA_COMBATTIMENTO.md (bozza 2), decisioni aperte nella sezione 12.
- [x] (05/11) Differenza di livello: un mostro con livello <= livello PG - 4 non da' esperienza ne' bottino.
- [x] (05/11) Abilita' dal 3 al 15: Whirlwind 3, Battle Cry 6, Rage 9 (nuova), Smash 12, Frenzy 15 (nuova).
- [ ] Il boss finale deve essere impegnativo (obiettivo da fissare con l'arena: es. % di vittorie al livello previsto).
- [x] (05/11) Cintura fissa: 4 posti, una pozione ciascuno (tasti 1-4), + pergamena (tasto 5). Al massimo 4 pozioni:
      la quinta non si prende (baule: "the belt is full", negozio: non si compra). Pergamene: una pila nello zaino
      (un posto, quantita' scritta "3x portal scroll", al massimo 4). HUD: icone + un trattino sotto ogni posto.
      Tolti gli oggetti cintura (sash, belt, war belt): il 4o posto equipaggiamento resta libero (anelli).
      Pesi del bottino: belt 10 -> weapon 39, armor 23, shield 18 (da rivedere con le probabilita' per oggetto).
- [ ] Una pergamena garantita per piano? Da decidere.
- [x] (05/11) Ricarica delle pozioni: 5 secondi (250 fotogrammi) per tutte, dopo aver bevuto (data/rules.yaml, potions.cooldown).
- [ ] HUD: durante la ricarica (5/10/15 s per rossa/gialla/viola) mostrare una pozione (o un'icona di ricarica) sulla cintura, cosi' si vede quando si puo' bere di nuovo
      (es. i 4 slot pozione in grigio/con icona clessidra, o solo l'ultima pozione bevuta in ricarica).
- [x] (05/11) Pozioni: 3 tipi. Rossa (minor healing, 25% della vita massima), GIALLA (healing, intermedia, 40%),
      viola (greater healing, 60%). Percentuali da tarare col simulatore. Colori dell'HUD: rosso 2, giallo 7, viola 4
      (devono stare in 0-7: caratteri hires). Oggi nel gioco ci sono solo 2 pozioni (minor / greater, cura fissa).
- [ ] Grafica della cintura da rivedere: mostrare direttamente le ampolle colorate nella cintura.
- [ ] Probabilita' di uscita per OGNI oggetto (05/11): regola stile Diablo, livello oggetto + rarita' e formula
      w = R x g(livello area - livello oggetto) (docs/wiki/SISTEMA_COMBATTIMENTO.md, 9b): zero sotto il livello dell'oggetto,
      cresce scendendo; oggetti "da caccia" con probabilita' bassa anche oltre il 20.
- [ ] Set di oggetti unici con nome (arma, armatura, scudo, anello): bonus con piu' pezzi indossati. Se c'e' memoria
      (stima ~8 B a set + 40-60 B di codice).
- [ ] Frenzy (05/11): oltre al colpo in piu', aumenta per un certo tempo la velocita' di movimento del PG, ma solo
      dopo aver colpito un mostro (non serve nel simulatore fermo; da fare nel gioco e nell'arena fase 2).
- [ ] Anello della velocita' (05/11): aumenta la velocita' di movimento del PG (nuovo modificatore degli anelli).
- [ ] (08/11, committente) ARMAIOLO: valutare di toglierlo dal gioco; il fabbro gestirebbe armi, armature e scudi
      (merce unita: oggi 3 + 5 oggetti a ogni ingresso). Da decidere: edificio del villaggio, aiuto, manuale, balance.yaml.
      RESTA DA VEDERE (08/11, committente): (1) se il venditore di armature (armaiolo) va rimosso; (2) se il fabbro deve
      vedere (vendere e comprare) sia armi che armature. Le due scelte vanno prese insieme: se l'armaiolo resta, il
      fabbro potrebbe restare solo armi (e scudi?).
- [ ] (08/11, committente) NEGOZI rifatti come la casa (concept in attesa di conferma): fabbro e alchimista identici,
      niente testo "about", niente linguette; fire su merce = buy, su pack = sell, su equipped = repair, tasto R = repair
      su pack ed equipped; l'equipaggiamento non si vende mai. "selected item" diventa un riquadro standard riusabile.
      Merce e acquisti (08/11): fabbro vende e compra armi, armature, scudi (NON compra anelli); alchimista vende
      pozioni, pergamene, anelli, compra gli anelli (pergamene: da confermare); l'alchimista non ripara. Cintura nel
      riquadro purse (2 file da 4); comprando una pozione ">" sul posto libero, si paga solo alla conferma.
- [ ] (08/11, committente) Eroe di prova con 8 pozioni appena c'e' la cintura a 8 (CLAUDE.md); purse gia' con il posto.
- [ ] (08/11, committente) CINTURA A 8 POSTI sbloccata da una quest (docs/wiki/quests.md, 6bis): 4 slot da 2 pozioni,
      tasti 1-4 invariati. DA STUDIARE BENE la disposizione automatica delle pozioni negli slot (raccolta, acquisto,
      cosa si beve per prima). Acquisto (08/11, committente): Fire su una pozione -> ">" sul primo posto libero
      della cintura e il giocatore sceglie dove metterla (resta da studiare la raccolta nei dungeon). Poi: formato dell'eroe (SAVE_VER), HUD, inventario, bilanciamento e simulatore.
- [ ] (08/11, committente) PERGAMENE FUORI DALLO ZAINO: contatore dedicato (0..10, icona con il numero, tasto 5), lo
      zaino non ha mai una voce pergamena. Baule di casa: pile da 10, ogni 10 una pila nuova (un posto del baule
      ciascuna). Vendita dal riquadro purse dei negozi. Cambia il formato dell'eroe (SAVE_VER): farlo insieme alla
      cintura a 8 posti se possibile.
      OPZIONE (08/11, da decidere): in casa le pergamene addosso nel riquadro pack sulla riga dell'oro ("$$ 2350  s 7"):
      Fire su "s" sposta tutte le pergamene nel baule riempiendo prima la pila non piena, poi pile nuove; dal baule
      si prende dalla pila selezionata quanto sta nel contatore. Oggi in casa non c'e' uno slot pergamene a parte.
- [x] (08/11) NEGOZI rifatti (fabbro, armaiolo, alchimista: stessa schermata, docs/wiki/villaggio.md). Corretti anche: bonus
      magico dell'arma nel riquadro oggetto (usciva un numero a caso: tmp5 usato da ui_puts/ui_num), durabilita' degli
      oggetti nuovi (add_to_pack: bottino e negozi non si usuravano mai). [ ] Bilanciamento: con l'usura vera degli
      oggetti trovati e comprati le riparazioni costano di piu' di quanto si vedeva in gioco (il simulatore la contava gia').
- [ ] (08/11, committente) MERCE DEI NEGOZI da decidere: cosa e quanto vende ogni negozio. Oggi (balance.yaml): fabbro
      6 oggetti a caso da armi + armature + scudi, alchimista 4 da pozioni + pergamena + anello, armaiolo 5. Al massimo
      8 (riquadro merce da 8, i posti vuoti con '-'); non sempre 8.
- [ ] (08/11) RIVEDERE GLI ANELLI: togliere i nomi copper/silver/gold e mostrare "ring +N <stat>" (es. "ring +3 dex").
      Insieme (08/11, committente): ACCORCIARE I NOMI dove si puo' (fatto: medium shield -> mid shield). Candidati:
      leather armor, greater healing, healing potion, minor healing, portal scroll, tower shield, viking sword.
      Da decidere: dove sta il dado del materiale, lunghezza del nome (limite NAME_SHOW), salvataggi.
- [ ] (08/11) Inventario: xp mostrata come numero (16 bit bassi); nel concept era "9999/27K" come nell'HUD.
- [ ] ANELLI (05/11): oggetti molto rari, danno un bonus a una caratteristica; 4o posto equipaggiamento.
      Materiale = dado del bonus, tirato quando l'anello nasce (salvato nel byte bonus gia' esistente):
        copper ring D6 (1-6), silver ring D8+4 (5-12), gold ring D12+8 (9-20).
      Modificatore = caratteristica (nome corto per lo spazio nell'inventario, 17 caratteri con "+NN "), es.
        "of might" = +FOR, "of agility" = +DES (esempi dell'utente: "del potere", "dell'agilita'"); testo in inglese.
      Memoria: materiale x modificatore = id oggetto (es. 3 x 3 = 9 id), bonus nel byte bonus: 0 byte in piu' nei salvataggi.
      Dipende dal nuovo sistema delle caratteristiche (scala dei valori: vedi docs/wiki/SISTEMA_COMBATTIMENTO.md).

## Simulatore delle regole nuove (05/11)
- [x] sim/rules.py + sim/sim_rules.py + data/rules.yaml; report docs/simulazione_regole.html. Iterazione 1 fatta.
- [ ] Decidere gli obiettivi (gruppo di 3 base: vita finale ~60%, 4-8 s; boss del piano ~75%; boss finale 60-70%).
- [ ] Curva del PG piu' regolare (armi a 2 colpi e Frenzy fanno salti): rivedere la tabella delle armi, poi la curva dei mostri.
- [ ] Stordimento a ogni colpo: un mostro da solo non attacca quasi mai (ricarica ferma). Tenerlo o ridurlo?
- [ ] Bottino oltre il livello area ~37 (Abisso): nessun oggetto comune resta -> servono oggetti da Abisso / da caccia.
- [ ] Boss finale: vita circa x5,5 della scheda attuale per ~65% di vittorie con 4 pozioni.
- [x] (05/11) Abisso fino al 255: i mostri crescono per PIANO seguendo la crescita del PG di riferimento (livello =
      20 + piano - 10): CA +0,31, ATT +0,02 a piano, danno x(1 + 0,071 x piani), vita x(1 + 0,0037 x piani).
      Simulato: difficolta' costante lungo tutta la diagonale; un PG piu' alto del piano vince sempre
      (es. livello 100 al piano 30: 100%), uno piu' basso di ~15-20 livelli perde.
- [x] (05/11) Danno di un colpo a 16 bit in entrambe le direzioni (PG e mostri): una sola routine di danno; dadi a 8 bit.
      Stima: ~40-80 B di codice, 2 B di variabile temporanea, fattore del piano (1-2 B); nessun byte in piu' per mostro.
- [x] (05/11) Armi dell'Abisso con piu' dadi (provvisorie: 3d8 al livello 30 ... 7d10 al 220): la parte casuale resta
      ~55-60% del danno anche al 255 (con il solo doom blade scendeva al 27%).
- [ ] Indurimento dell'Abisso: il PG non deve mai arrivare al 100% di colpi e deve faticare sempre di piu'. Proposta:
      +9 punti di CA dei mostri entro il piano 245 oltre alla crescita che segue il PG -> colpi del PG 85% -> 55%,
      boss con nome 96% -> 58% (report sezione 10, confronto 0/6/9/12). Da confermare.
- [ ] Oggetti dell'Abisso (bottino oltre il livello area ~37) restano da progettare.

## Piano finale su file (per piu' RAM libera e caricamenti veloci) - DA FARE PIU' AVANTI
- [x] (07/11) Mappa della sala del trono pregenerata: file FMAP (tools/gen_final.py, RLE ~400 B, cache sotto il KERNAL dopo la mappa del villaggio (~$EAA8, ordine: $FCE0-$FFF9 resta un blocco unico), letto una
      volta per sessione), via gen_final con le figure e le tabelle fin_rect/fin_star/fin_circ (+300 B sotto $8720).
      Porta del muro nord = 3 caselle che diventano pavimento (fin_doors, come alla morte del boss). Mappe identiche.
- [x] (07/11) Generatore dei piani nella RAM sotto l'I/O ($D480, src/game/gen_io.asm, copiato all'avvio da copy_gfx,
      eseguito da gen_call con $01=$34 e sei): +1,1 KB sotto $8720. Tolto enter_level_dbg (codice di debug mai
      chiamato). Mappe dei piani 1-20 identiche alla v1.15 (VICE, byte per byte); test: tests/test_gen.py.
      Restano possibili: spawn_monsters/place_monster/place_boss sotto l'I/O (~600-800 B, da misurare).
Obiettivo: nessun byte del piano 10 in RAM durante gli altri piani, e spazio per arricchirlo in futuro.
- [ ] Overlay "throne" (o in coda a gfx8): tileset + codice + dati della sala del trono in un solo file,
      precaricato in background al piano 9 (e nel villaggio se il portale porta al 10): 0 s in piu' entrando
      se il precaricamento e' finito; nessuna apertura di file in piu'. (Scartato: codice letto solo all'ingresso,
      ~1-2 s a ogni ingresso nel piano 10.)
- [ ] Spostare nell'overlay tutto il codice solo-piano-10 (misurato 05/11, ~1 KB residente oggi):
      gen_final + tabelle (487 B), ui_lever (340 B), ui_victory (138 B), at_lever (20 B), parte di place_boss.
      fin_doors (~30 B) puo' restare residente o stare nell'overlay (l'overlay resta in RAM per tutto il piano 10).
- [ ] Dove eseguirlo: $C900-$CFFF (1792 B dopo la mappa, RAM normale: il codice gira senza commutare le ROM;
      nel menu e' del modulo MENU, nei piani e' libera - verificato in VICE 05/11).
- [ ] Colonna sonora del boss: dati della musica nell'overlay (il player resta residente).
- [ ] Arricchire la sala del trono (decorazioni, eventi) dentro l'overlay, senza costo per gli altri piani.
- [ ] Verificare: sprite del boss finale (in GFX_STRONG di ogni tema?) solo nel tema/overlay del piano 10:
      ogni file tema potrebbe accorciarsi.
- [ ] Mappa della sala: NON salvarla generata (2304 B, o RLE stimato piu' grande del codice): meglio codice+tabelle.

## RAM di scratch (verificata in VICE 05/11: intatta dopo cambi di piano, portali, salvataggi)
- $0400-$07FF   1024 B  RAM normale (schermo del BASIC, non usato dal gioco)
- $C900-$CFFF   1792 B  RAM normale (dopo MAP; nel menu la usa il modulo MENU)
- $9318-$93FF    232 B  buco tra le variabili
- $9D90-$9FFF    624 B  coda del blocco CODE2 (riservato al codice)
- $D2E0-$DFFF   3360 B  RAM sotto l'I/O (dopo STASH; solo dati, accesso con $01=$34 e IRQ spenti)
- $EA60-$ECFF    672 B  RAM sotto il KERNAL (dopo il villaggio)
- $FD00-$FFF9    762 B  RAM sotto il KERNAL (dopo il posto del precaricamento)
- $9B4C-$9BFF    180 B  libera (prima la azzerava clear_lvlblk: bug corretto)
- [x] (05/11) Mappa della RAM: docs/mappa_ram.html (tools/gen_rammap.py). tools/memmap.py tolto (05/11).
- [x] (05/11) BUG corretto: clear_lvlblk azzerava $9800-$9BFF (4 pagine) cancellando le variabili REL a $9B00 (file aperto,
      record corrente): ora 3 pagine + guardia .cerror. Verificato in VICE (RUN/STOP nel villaggio con piano in memoria).

## Bug segnalati (05/11, versione 1.7)
- [x] B1 Cambio piano: glitch grafici mentre si riscrivono i caratteri (gfx_install con lo schermo di gioco
      ancora visibile: con cache/precaricamento non c'e' piu' la schermata di caricamento a coprirlo).
      Correzione: schermo nero come primissima cosa del cambio piano, poi tutto il resto.
- [ ] B2 Minimappa corrotta, solo nel dungeon (nel villaggio e' corretta). NON riprodotto in VICE
      (minimappa del piano 1 vuota e poi tutta esplorata: corretta): servono screenshot e passi precisi.
- [ ] Portale della leva "nero": oggi ha i colori del portale normale.
- [~] Cambio piano verso un tema non in cache: ~7 s di grafica in piu'. (05/11) Temi uguali = un solo file: oggi i
      temi 1-7 sono identici, quindi tra i piani 1-9 la grafica non si ricarica mai (piano 2 -> 1: 11,6 -> 5,5 s);
      disco: 6 file e 48 blocchi in meno. Tornera' quando i temi avranno grafica diversa (precaricamento: solo in avanti).
- [x] B3 Audio glitchato a ogni cambio piano (es. citta' -> dungeon) e al portale.
      Correzione: sempre prima dissolvenza a zero del volume (tutte le voci, $D418) e poi il resto.

## Dopo il refactoring
- [ ] Statistiche dell'eroe (05/11): contatore delle morti e contatore dei mostri uccisi, entrambi a 16 bit.
      Mostri uccisi: c'e' gia' (c_kills, 16 bit, nel blocco eroe). Morti: nuovo c_deaths (+2 byte nel record
      eroe, oggi 124 liberi). Da mostrare nella scheda dell'eroe; si fermano a 65535.
- [x] (05/11) Bilanciamento completo con set minimo (docs/wiki/BILANCIAMENTO.md, data/rules.yaml, sim/fit_rules.py, sim/cmp_rules.py):
      PG 1-20 + Abisso 21-255, 3 armi / 3 armature / 3 scudi / 3 anelli / 3 pozioni, abilita' con durate e ricariche.
      Da confermare: ricarica pozioni (blocco totale o per tipo), finestra del boss (+-2 livelli), vita dei mostri fissa.
- [x] (06/11) DUNGEON A 20 PIANI: 19 piani di discesa + piano 20 = boss finale; un livello del PG per piano (tetto 20 prima
      dell'Abisso). Salvataggi a 1 record per piano, 5 slot (106 record). Regole d20 in src/game/combat.asm, Rage/Frenzy,
      pozioni a cura fissa con blocco totale, anelli, tesori generati alla prima apertura. Wiki: docs/index.md.
      Resta: Abisso (piano tecnico sopra).
- [x] (06/11) RITARATURA dopo l'implementazione del nuovo sistema (Fable): simulatore allineato al codice (vita +-25%,
      boss immuni al blocco, livelli dei mostri, evocazioni), tabella di riferimento con la magia reale del bottino,
      sim/fit_rules.py rilanciato: risultati in docs/wiki/BILANCIAMENTO.md.
- [x] (06/11) chestLevel (1..255) dei tesori e motore di generazione del contenuto dei bauli: docs/wiki/bottino.md.
- [x] (06/11) Durabilita' di armi, armature, scudi (usura, rottura, pugni, riparazione dal fabbro): docs/wiki/combattimento.md.
- [x] (06/11) Numero di partita + minuti giocati + morti nel blocco eroe; piani ripopolati a ogni nuova partita.
- [x] (06/11) Baule di casa su disco (48 posti, modulo OVLT), help nel menu RUN/STOP, tasti H J K L / U O.
- [x] (06/11) Villaggio ridisegnato (cimitero con la cripta, ruscello e ponte, pozzo, case) e minimappa con icone.
      NON FATTO: colori diversi per tile (impossibile con la color RAM condivisa dal doppio buffer: docs/wiki/villaggio.md).
- [x] (06/11) GAME caricato a $0400 (+1 KB di codice), modulo OVLT a $C900 (+1,5 KB). Margine ~750 B.
- [x] (06/11 sera) Lavori di PER-OPUS.md fatti (file cancellato): test del baule di casa su disco (test_rel.py), di riparazione,
      rottura dell'arma, orologio TOD e 255 oggetti generati (test_items.py); arena con --dur; pulizia (loot.window, dt_div60,
      spaccato 3 della mappa RAM); manuale riscritto. Restano qui: HUD xp 24 bit (per l'Abisso), verifica a mano.
- [x] (06/11 sera) BUG GRAVE corretto: gen_item, categoria pergamena (5% degli oggetti generati): un `.byte $2c` saltava
      anche il primo byte di `stx gi_cat` e il programma finiva in BRK (ritorno al BASIC). Ora `beq _got`; test in test_items.py.
- [ ] (05/11) IDEA per dopo: boss intermedi e mini quest. Es. una quest al piano 5 con stanza speciale e boss; altri piani
      speciali ogni tot fino al 20; un mini dungeon raggiungibile da un altro passaggio, di difficolta' pari a un piano
      dato (es. 10 o 15). La lore puo' cambiare (certi piani raggiunti da passaggi diversi): e' solo grafica. Non ora.
- [ ] (05/11) Pozioni: cura fissa (rossa 20, gialla 60) o a formula (viola 4 x livello + 40), ricariche 5/7/10 s, zone di
      uscita a formula (tre terzi del dungeon con sovrapposizione decrescente: potions.zones / ramp in data/rules.yaml),
      nell'Abisso solo la viola. Il piano massimo si cambia senza rifare i conti.
- [x] (06/11) Il PG ha SEMPRE un'arma: l'arma non si toglie e non si vende (si sostituisce); recalc_stats mette il pugnale se manca.
- [x] (06/11) Cadenza dell'attacco base per arma (pugnale 12, spada 14, vichinga 20 fotogrammi) e arma a due mani (scudo ignorato).
- [x] (06/11) Frenzy: corsa +25% al primo colpo a segno, +15% a ogni colpo a segno dopo, max +100%, fino a fine Frenzy (5 s).
      Misurato in VICE (TESTFZ, 06/11 sera, villaggio): a 4 px/fotogramma (+100%) nessun fotogramma perso in
      orizzontale, verticale e diagonale (fz_move corretto: prima l'accumulatore cresceva senza limite e la corsa
      non superava +50%). Nei dungeon le diagonali perdono qualche fotogramma anche senza Frenzy (limite del motore).
      Tetto confermato a +100% (FZ_RUN_MAX).
- [x] (06/11 sera) Manuale riscritto (tasti H J K L / U O, help, regole d20, abilita', pozioni, durabilita' e riparazione,
      baule di casa 48 posti, chestLevel, villaggio nuovo, 20 piani, partite e ripopolamento, capitolo finale sul tempo
      giocato fermo); screenshot rigenerati (tools/shots_manual.sh); gen_manual.py segnala le pagine che traboccano.
- [x] (07/11 sera) Oro nel baule di casa (c_sgold nell'eroe; Fire sulla riga dell'oro sposta tutto; morendo si perde meta'
      del solo oro addosso; scheda del barbaro = oro totale a 17 bit), zaino da 16 a 8 posti (PACK_N, due colonne da 4
      in inventario e vendita), baule di casa da 48 a 24 (2 pagine da 12), SAVE_VER $C2 (eroe 110 B, baule 97 B).
      Cancellando un barbaro si svuota anche il suo baule di casa (prima il nuovo barbaro nello stesso posto lo ereditava).
      Test: tests/test_gold.py, test_saves caso 7. Costo: margine del gioco -8 B (1828 B), OVLT da 1007 a 1399 B (max 1792), MENU 2784 B.
- [x] (07/11 sera) Oro addosso al massimo 10000 (GOLD_MAX, player.gold_max): raccolta oltre il tetto persa (add_gold16),
      vendita rifiutata ("your purse is full.", purse_room), prelievo dal baule di casa fino al tetto (gd_add con tetto).
      Test: tests/test_gold.py (13 casi). [ ] sim/sim_gold.py non modella il tetto (conta l'oro raccolto, non dove sta).
- [x] (07/11 sera) quit the game -> BASIC con rientro: bb_quit copia $0400-$07FF in $CC00 e $0800-$0802 in MENU prima
      del reset; SYS 49158 (bb_entry, $C006) li rimette e riparte da game_warm (menu, dati riletti dal disco).
      godmode spostato da $9105 a $02A9 (POKE 681,1, non azzerato da game_start). docs/wiki/cheats.md, test_saves caso 6.
      [ ] Non provato su C64 reale. [ ] ui_badsave ("N" = esci) fa ancora il reset senza copia: SYS 49158 da li' non funziona.
- [ ] (07/11 sera) Baule di casa e salvataggio: il baule si scrive su disco uscendo di casa, l'eroe no. Spegnendo senza
      salvare, un oggetto messo nel baule resta nel baule e torna anche nello zaino (duplicato). L'oro no (sta nell'eroe).
      Da decidere: salvare anche l'eroe uscendo di casa (~4 s) o accettarlo.
- [x] (07/11 sera) HUD: da 10000 di XP (e di soglia, ciascuno per conto suo) in migliaia senza decimali, 10K..65K (soglia scelta dal committente: "30k era un esempio") (hput_k, +29 B nel gioco, margine
      1836 B, tests/test_hudxp.py). [ ] Resta il 24 bit (oltre 65535: 3 cifre + K, dec5 e scala della barra a 24 bit, stimati
      100-130 B) quando si decidono le soglie dei livelli oltre il 20 (oggi le tabelle finiscono al 20).
- [ ] Rifare il set delle armi (piu' casuali).
- [ ] Simulazione: Battle Axe peggiore della Broad Sword; Battle Cry poco utile 1 contro 1.
- [x] (06/11 sera) Tempo giocato dall'orologio TOD del CIA2 al posto del contatore di fotogrammi (contano anche menu,
      negozi e caricamenti; in memoria solo il contatore dei minuti in c_game, ore:minuti calcolate solo nella scheda).
      tod_start/tod_tick (src/game/game.asm), letto ogni 256 fotogrammi e ai salvataggi. Nessuna protezione se il TOD e' fermo
      (alimentatore senza 9 V AC): spiegato nel capitolo finale del manuale. Test: tests/test_items.py.
- [x] (06/11 sera) Menu principale senza musica (il passaggio della musica dal loader al menu dava un glitch audio).
- [ ] Musica nel menu principale da rifare senza glitch (idea: un brano del player del gioco, invece di proseguire
      quello del loader).
- [ ] (06/11) Verifica a mano dal disco di release (10 minuti): nuova partita -> villaggio (strada sud) -> casa (baule,
      3 pagine) -> fabbro (compra, vendi, ripara) -> cripta -> piano 1 -> H J K L / U O -> morte -> ritorno; RUN/STOP
      help; salva, esci, continua: numero della partita 2, minuti plausibili, mostri del piano 1 di nuovo vivi;
      menu principale in silenzio senza click.
- [x] (06/11 pom.) Avvisi nell'HUD: HP lampeggiante rosso/giallo sotto 1/4 della vita + suono una volta; icone
      arma/armatura/scudo lampeggianti in riga 21 colonne 29-31 se durabilita' <= 20 o <= max/8 (hud_warn, ogni 16
      fotogrammi). Nessuno sprite. Usura portata a 2/1/1 (una riparazione ogni ~3 piani, sim/sim_durability.py).
- [ ] (06/11 pom.) MEMORIA, analisi di Fable. Stato: codice $0400-$849D (33,0 KB) con limite $8720 (righe HUD dello
      schermo fisso): margine 643 B; CODE2 559 B; OVLT pieno (10 B). Grafica fissa gfx_data $849D-$8EDD (2624 B) e' gia'
      dato morto dopo copy_gfx (non e' sotto il limite: non da' nulla). Non serve un refactoring generale: la struttura
      (moduli MENU/OVLT, cache sotto KERNAL, STASH sotto I/O) e' gia' quella giusta. Interventi mirati, in ordine di resa:
      1. CODICE DI CALCOLO PURO NELLA RAM SOTTO L'I/O ($D300-$DFFF, 3328 B liberi dopo lo STASH): dungeon.asm (1661 B:
         gen_dungeon, gen_rooms, gen_links, carve_*, gen_stairs, post_walls, gen_final, fin_*; unico accesso I/O e'
         set_palette in enter_level_dbg, debug) + spawn_monsters/place_monster/place_boss/floor_types (~600-800 B).
         Caricato UNA volta dal loader (che gia' scrive sotto l'I/O: CHRBUF), eseguito con sei / $01=$34 / jsr / $01=$36 /
         cli da uno stub (le routine non toccano VIC/SID/CIA/KERNAL; lo schermo e' spento durante il cambio di piano;
         NMI: il vettore $FFFA in RAM punta gia' a nmi_stub). Resa stimata: 2,2-2,5 KB sotto $8720, zero costo a runtime,
         zero accessi al disco in piu'. Attenzione: tools/gen_rammap.py (spaccato 4), FORMATO_DATI (file nuovo "CALC"),
         test_rel/test_loader (il file in piu' da caricare), arena (deve caricarlo anche lei: tools/arena.py).
      2. SCR_H da $8400 a $8800: le righe 20-24 cadono a $8B20-$8BE7 (slot sprite 41-47, liberi) e i puntatori sprite a
         $8BF8; il VIC non legge mai le righe 0-19 dello schermo HUD (split a 209). Il limite del codice passa da $8720 a
         $8800: +224 B. Costo: una costante + .cerror + gen_rammap. Verificare in VICE la barra della minimappa ($8A00).
      3. Dati della musica (music_data.asm, 1345 B) sotto il KERNAL a $FCE0-$FFF9 (794 B liberi: non bastano tutti) o
         nell'area del prefetch se si riduce il buffer: il player legge con $01=$35 (I/O visibile, KERNAL no) dentro
         l'IRQ e rimette $36 prima di jmp $ea81. Resa 0,8-1,3 KB, costo ~40 cicli per IRQ. Meno pulito del punto 1.
      4. Piccoli: $87E8-$87F7 (16 B), $90F1-$90FF, $91FC, $9230-$923F, $9416-$941F: variabili sparse, ~60 B in tutto.
      Da NON fare: UI/negozi sotto l'I/O (scrivono la color RAM $D800), compattare la pagina zero (33 B liberi, serve a
      poco), rimettere il PRG oltre $8720 (le righe HUD sono li').
- [x] (06/11 pom.) Villaggio ridisegnato: fiume centrale (colonne 29-31, due anse) con due ponti, strade sinuose (niente
      croce), fabbro/piazza/casa/cimitero a ovest, armaiolo/portale/alchimista a est; minimappa con il fiume in blu
      (mm_wat). BUG corretto: la mappa precedente non aveva il tile FOUNTAIN (~) e la fontana non curava; ora le 8
      caselle del bordo della vasca curano. Script di generazione usa e getta (non nel repo): data/town_map.txt e'
      la sorgente. Arredi: recinto con covoni (tile HAY nuovo, l'ultimo codice libero del charset: HUD_FREE in
      gen_gfx.py ne tiene 4 per gli avvisi dell'HUD), botti, siepi, boschetti, bancarelle, secondo pozzo.
- [x] (06/11 pom.) Atlante grafico docs/grafica/ (HTML + un PNG per tile + tiles.json, id = 5 lettere del set + lettera
      della mappa; gruppi di tile composti; titolo con celle usate/libere): generato da tools/gen_atlas.py. Regola in
      CLAUDE.md: ogni modifica grafica si riflette nell'atlante.
- [x] (06/11 pom.) PRESS SPACE: onda sinusoidale (±4 px, SPACE in controfase) e tavolozza "fuoco freddo"; righe a
      Y 188 e 224 per il multiplexing (prima la lettera 0 di SPACE, che il raster raggiunge per prima).
- [x] (06/11 pom.) GAME compresso ZX0 (tools/pack.py + compressore C in tools/zx0/, decompressore 6502 src/common/zx0.inc,
      sul posto nel loader, ~4 s): avvio release da 154 a 111 s (misurato), sviluppo da 120 a 86 s. Verificato byte
      per byte in VICE (tests/test_loader.py).
- [ ] Compressione dei file rimasti (stima ~5 s): MENU e GFX0 (li ricarica anche il gioco, servirebbe il
      decompressore in CODE2 e un buffer), temi GFX1/GFX2 (precaricamento in sottofondo in meta' tempo: decompressione
      da $F500 a $ED00 sotto il KERNAL con $01=$35 e sei, ~0,2 s al cambio di piano). Decompressore gia' pronto
      (src/common/zx0.inc, parametrico in pagina zero).
- [x] (06/11 pom.) DECISIONE: l'immagine del titolo (TITLE) NON si comprime, per ora (resta la comparsa riga per riga).
- [ ] MEMORIA: margine del codice sceso a ~430 B (avvisi HUD, minimappa del fiume, orologio TOD). Prossimo passo
      consigliato: generatore dei dungeon + spawn nella RAM sotto l'I/O (vedi la voce "MEMORIA, analisi" sopra).
- [x] (06/11 pom.) Container Docker completo: compressore ZX0 compilato nell'immagine (stage ctools), NumPy e Matplotlib
      (mancavano: gen_title.py non partiva), ROM dell'unita' disco 1541 e 1541-II in roms/ collegate in VICE (mancavano:
      loader e test bloccati). ./build.sh completo verificato nel container (target dev). Target release non ricostruito.
- [x] (06/11 sera) BUG corretto: il loader leggeva l'elenco eroi dal record 156 di SAVES (valore dei tempi dei 30 piani);
      il file ha REC_HDR = 111 record -> all'avvio "salvataggi di un'altra versione". Ora REC_HDR arriva da game.lbl.
- [x] (06/11 sera) Prova del disco, correzioni fatte (Opus):
      - MUSICA nuova (docs/wiki/musica.md): player unico src/common/sid_player.inc (loader, gioco, jukebox), brani in tools/songs.py
        compilati da tools/gen_music.py in file SND0..SNDn sul disco; titolo Demon's Eye; livelli Iron Crown, Blood Path,
        Fear Below, Black Chant (a caso, mai uguale al piano prima); boss finale Abyss Gate; combattimento Fight 1 (a caso
        per piano, elenco estendibile); villaggio: la vecchia Taverna dell'Alba portata nel formato nuovo (DA CONFERMARE
        col committente). 3 voci anche nel gioco: la voce 1 e' condivisa con gli effetti. JUKEBOX sul disco di sviluppo.
      - avviso durabilita' al 20% del massimo (warn_percent); arma iniziale sempre a durabilita' 10 (rnd = 0 dopo
        game_start: xorshift fermo) -> seme dal CIA; ap_d/ap_m azzerati dopo ogni uso. Il "pugnale senza durabilita'"
        NON riprodotto: con la build nuova l'arma iniziale ha durabilita' (test_music.py). Ipotesi (non certa): eroe
        di una versione precedente caricato quando il controllo di versione leggeva il record sbagliato.
      - PRESS SPACE: righe 172/220, onda +-7, IRQ_MID con 8 righe di margine; 3 tavolozze (LDCOL 0/1/2) in attesa
        della scelta; test_loader controlla l'elenco eroi (REC_HDR) e fa screenshot (--shot).
      - oro iniziale 100; negozi per livello del PG (level_ahead 3, shop_level di pozioni e pergamena).
      - villaggio: niente arredi entro 3 caselle dalle porte (controllo in gen_maps), Fire anche 1-2 caselle davanti
        alla porta (pl_tile), portale ridisegnato (arco) e spostato a (42,24).
      - barra in alto: ultimo mostro colpito; senza bersaglio chi attacca o si sveglia.
      - help: "loading help..." senza schermata, tasti in giallo, page 1/2 e 2/2. Hero -> barbarian nei testi.
      - BUG quit to main menu: "bne +" della voce help saltava al "+" sbagliato e tornava al menu di gioco: corretto.
- [ ] (06/11 sera) PREZZI proporzionali al guadagno: proposta in docs/wiki/BILANCIAMENTO.md sez. 12, da confermare.
- [ ] (06/11 sera) Scelta della tavolozza di PRESS SPACE (A sangue / B oro antico / C acciaio): oggi A.
- [ ] (06/11 sera) Suono SFX_LOWHP provvisorio: da ascoltare nel JUKEBOX.
- [x] (06/11 sera) Docker, target release: stadio release costruito sopra l'immagine dev esistente e provato
      (gen_manual.py nel container: PDF di 14 pagine). Nell'ambiente di Claude Docker Hub ha dato 429 e il proxy
      richiede il suo certificato per pip: aggiunto solo nel Dockerfile temporaneo di prova, non in docker/Dockerfile.
- [x] (06/11 sera) PRESS SPACE: lettere dal font della UI del gioco (Reliquia, x3 / x2,5, grassetto), non piu'
      data/loader_font.txt (cancellato).

- [x] (06/11 sera, dopo la prova) Errore "saved games from a different version" al primo avvio: NON riprodotto in VICE
      con l'unita' 1541 emulata (disco nuovo: elenco letto, versione giusta). Leggendo un SAVES assente o illeggibile il
      vecchio codice dava proprio quell'errore (versione = byte a caso): ora l'avviso esce solo con un elenco vero di
      un'altra versione (byte "presente" 0/1 e almeno un eroe). Ipotesi (non certa): nell'emulatore del committente
      il file REL non si legge (unita' senza emulazione vera / dispositivo virtuale). tests/test_saves.py.
- [x] (06/11 sera) SID zittito prima di ogni operazione su disco (snd_io in ld_open / rel_open).
- [x] (06/11 sera) Musica a tempo: sfx_update nell'IRQ di fine HUD (prima nel ciclo principale, che nel villaggio sfora).
      Brano del villaggio con hard restart (gcut | $80). Glitch del villaggio: da riascoltare (non certo che siano spariti).
- [x] (07/11) Conferma prima di eliminare un oggetto dell'inventario (D -> "delete this item? y:yes n:no"); routine
      ui_yesno riusata anche dalla domanda di uscita al menu.
- [x] (07/11) Help semplificato nel menu iniziale (una pagina, solo tasti; modulo MENU, +785 B -> usati ~510 B), tolto dal
      menu di gioco e da OVLT (ora 1007 B, 785 B liberi). Margine sotto $8720 +76 B (voce del menu di gioco).
- [x] (07/11) DECISO (quest system): tre villaggi, tre generatori (GEN1 stanze, GEN2 grotte, GEN3 cittadella), abilita' solo
      da quest; compagno Torvald in posizione fissa, camminante solo nel corridoio principale del piano 20 con codice
      solo in un modulo OVLF caricato in quel piano; nel villaggio NPC animati (2 fotogrammi) e al massimo uno camminante
      su un giro fisso (codice in OVLT). Dettagli: docs/wiki/quests.md sez. 13.
- [x] (07/11) BUG segnalato dal committente: RUN/STOP nel menu iniziale. Riprodotto in VICE con tasti veri (xdotool): nella
      scheda dell'eroe salvato ("saved game") la riga in basso dice "run/stop: exit" ma si usciva solo con DEL o stick a
      sinistra. Corretto in detail_screen (src/menu.asm), v1.34. Il resto del menu (elenco, nuovo eroe, menu di gioco,
      quit to main menu) risponde a RUN/STOP come indicato.
- [ ] (07/11) QUEST SYSTEM: analisi in docs/wiki/quests.md (seconda parte: abilita' solo da quest, compagno Torvald, revisione dei tile
      dei dungeon (27 posti per tema, 11 usati, 12 avanzi del villaggio), generatori su disco GEN1-3 con tetto 2944 B, avvio
      leggero FRONT + LORE + MANUAL + main menu, testo della lore e del manuale, struttura dei sorgenti) (trama, 15 quest, 3 villaggi, stanze fisse, costi ~1,1 KB in GAME,
      open point per Opus). Da decidere i punti della sezione 5, poi tappa 1 (stato, NPC, pagine, hook, abilita').
- [ ] (07/11) Idee concordate, da fare: leva/vittoria/morte (ui_lever 340 B, ui_victory 138 B) in OVLT, ora che ha spazio
      (caricamento al bisogno: da verificare); negozi in overlay quando si
      rivedono i tasti dei negozi (oggi 2414 B, la zona overlay e' 1792 B).
- [x] (06/11 sera) Tema di combattimento solo per mostri forti / boss con nome, poi tenuto da tutti, 12 s di isteresi.
- [x] (06/11 sera) MP3 dei brani nel progetto: assets/music/ (gioco) e assets/music/candidati/ (tutti i candidati).
- [x] (06/11 sera) Screenshot del manuale: il PG deve stare in posizioni valide (regola in CLAUDE.md). Corretti
      villaggio (era dentro la fontana, 16,29 -> 16,31), ponte (era nel torrente, 30,13 -> 30,11), avvisi HUD.
      tools/check_pos.py controlla le posizioni del villaggio in tools/shots_manual.sh.
- [x] (06/11 sera) Brani: un brano alla volta dal disco, tolta la copia sotto l'I/O (decisione del committente): RAM
      $D480-$DFFF libera (2944 B). Costo ~+1,5 s a ogni cambio di piano (lettura nel cambio di piano, a schermo spento).
- [x] (06/11 sera) BUG della v1.11/v1.12, corretto: bauli invisibili nei dungeon (la scritta "chest" compariva, il tile
      no). Togliendo i tile degli oggetti a terra da tools/gen_gfx.py era stato tagliato anche il disegno dei bauli
      (CHEST/KCHEST/GCHEST): ripristinato da sources_v1.9.zip; i posti liberi consumano il generatore casuale come
      prima, cosi' gli altri tile sono identici byte per byte alla v1.10 (GFX0/1/2 confrontati). gen_gfx.py ora si
      ferma se un tile usato nei dungeon e' vuoto. Seed di prova ANOANO, piano 1: bauli a (6,8) (15,15) (42,18) (4,29).
- [x] (06/11 sera) Minimappa: coordinate x,y del PG in basso (debug).
- [ ] (06/11 sera) FUTURO, quando il gioco sara' considerato stabile: valutare se c'e' spazio (RAM e codice) per
      1) salvataggio del piano lasciato in sottofondo (stato compatto in un buffer, scritto su SAVES a pochi byte per
      fotogramma nel piano nuovo: niente "saving level N"); 2) precaricamento in sottofondo dei record dei piani
      N+1 / N-1 gia' visitati (niente "loading level N"); 3) brano del piano successivo in sottofondo (secondo buffer
      ~312 B). Stima: 300-500 B di codice, ~1 KB di buffer; cambio di piano da ~3,5-5 s a ~1-2 s (da misurare).
      Decisione del committente: per ora nessun prefetch nuovo.
- [x] (06/11 sera) Mostri fermi negli angoli (ANOANO piano 2, PG a 34,20): inseguimento solo "greedy". Aggiunto lo
      scorrimento lungo il muro (mon_slide) e lo scivolamento sugli spigoli per mostri e PG (try_step_x/y). Non e'
      un pathfinding completo: in un labirinto lungo un mostro puo' ancora fermarsi (da rivalutare se succede).
      Costo ~300 B di codice (margine 509 B sotto $8720: e' ora del refactoring della memoria).

- [ ] (07/11) LORE con piu' grafica: logo ridisegnato per la griglia (stima ~126 caratteri unici, da verificare), charset a due
      slot che si scambiano, ~14 immagini, budget disco ~30 blocchi (22 con testo ZX0). Dettagli: docs/wiki/quests.md sez. 14.

- [x] (07/11) FRONT + LORE (v1.27): BARBARIAN = menu (hear the legend / read the game manual / walk the blood path),
      LORE = loader con titolo + la storia a scorrimento con immagini (copertina, scene del gioco, sprite), LOADER = il
      loader del gioco di prima. Test tests/test_lore.py. Pagina docs/wiki/intro.md.
- [x] (07/11 sera) HELP (v1.34): programma a se' sul disco di release (src/help.asm, data/help.txt, tools/gen_help.py),
      voce 2 del loader; 5 pagine con tutti i tasti del gioco e delle schermate e il ritaglio dell'HUD vero (fotografia
      in VICE della variante TESTUI=28, data/help_hud.json; test --check nella release). Nessun impatto su GAME.
      Pagina docs/wiki/help.md. 29 blocchi (pagine in RLE): si possono ridurre con ZX0 se serve spazio (non misurato).
- [x] (07/11 sera) Test automatico della cancellazione del barbaro (tests/test_saves.py caso 7) e RUN/STOP = N in
      tutte le domande y/n (ui_yesno, shop_ask; +14 B nel gioco, margine 1865 B). Verificato che il test fallisce senza la correzione.
- [x] (08/11) PERGAMENE: pila da 10 nello zaino e da 10 nel baule di casa, si accumulano spostandole (fatto, provato in VICE).
- [x] (08/11) INVENTARIO: tolte le linguette (use/drop/close): fire = usa, DEL = elimina, RUN/STOP o I chiudono.
- [x] (08/11) NUMERI GIALLI: tutte le statistiche, quantita' e prezzi in giallo (UC_VALUE = 7), nomi degli oggetti bianchi.
- [ ] (08/11, vecchia voce) PERGAMENE: per ora restano un oggetto nello zaino (il portale si usa solo con le pergamene
      nello zaino; quelle nel baule di casa non contano). Il committente ricordava una pila da 10: nel codice e' 4
      (SCR_MAX, game.asm). Da decidere: pila da 10 nello zaino e da 10 nel baule, con le pergamene che si accumulano
      spostandole (oggi nel baule ogni spostamento occupa un posto a parte). Mostrate come "3 portal scroll" (08/11).
- [ ] (08/11, committente) INVENTARIO: tolta? la linguetta close (basta RUN/STOP); a cosa serve use (vedi risposta
      dell'08/11): decidere se tenere use/drop come modalita' o un'altra soluzione per eliminare.
- [ ] (08/11, committente) DA DECIDERE come gestire pozioni e pergamene (proposta del committente qui sotto, da
      confermare prima di implementare). PERGAMENE E POZIONI SOLO NELLA CINTURA: "non vanno nell'inventario, hanno il loro slot
      dedicato nella cintura e basta". Oggi le pozioni vanno gia' solo nella cintura (4 posti), le pergamene invece sono una
      pila nello zaino (fino a 4, occupano un posto). Da fare: posto pergamene nella cintura (contatore nell'eroe: nuovo
      SAVE_VER, avvisare che i salvataggi si perdono), give_item, scr_find, tasto 5, HUD, inventario, vendita nei negozi,
      baule di casa (le pozioni/pergamene nel baule restano o no? da decidere), test_belt.
- [ ] (08/11, committente) REFACTOR CON I GLIFI NUOVI: usare le icone dell'equipaggiamento (spada CH_SWORD 97,
      armatura CH_ARMOR 98, scudo CH_SHLD 35, anello CH_RING 99, font UI) dove possibile: inventario e vendita dei negozi
      (al posto delle etichette weapon/armor/shield/ring), riquadro dell'oggetto, help/manuale. Libera spazio sullo schermo.
- [x] (08/11) BUG trovato e corretto: nel villaggio con un piano lasciato per portale, "save game" (gm_save: pend_save
      + clear_lvlblk) cancellava in RAM il baule di casa (in EXPL) lasciando st_ok = 1: rientrando in casa il baule
      sembrava vuoto e, spostando qualcosa, veniva salvato vuoto su disco. Ora gm_save azzera st_ok (rilettura dal disco).
      Non provato in VICE con un caso reale (da verificare: test manuale 019 con un portale aperto).
- [x] (08/11) CASA DEL PG rifatta (docs/wiki/villaggio.md): riquadri PG/oggetto, equipped con icone, zaino e baule
      ordinati per categoria (sort4), 3 pagine da 8 con il numero come pulsante, scelta dell'equipaggiamento con lista
      filtrata e - remove, destra zaino -> baule. Memoria: modulo OVL2 nel posto del precaricamento ($F500, $01 = $35),
      disco e oro del baule nella coda di CODE2. [ ] Non provato su hardware reale; [ ] tempi di caricamento di OVL2
      (~0,8 KB a ogni ingresso in casa dopo un precaricamento) da misurare.
- [x] (08/11, committente) FINESSE TOLTO (codice, dati, simulatore, documenti). Era: non interessa, da togliere (oggi solo il pugnale: usa il migliore fra mod FOR e DES
      per attacco e danno, recalc_stats in combat.asm, itfl bit 1, rules.yaml "finesse", sim/rules.py, testo "finesse"
      nel riquadro dell'oggetto, docs/wiki/oggetti.md e combattimento.md). Toglierlo cambia il bilanciamento del pugnale:
      rifare i controlli del simulatore. Effetto: per il PG di riferimento nessuno (FOR > DES sempre).
- [ ] (08/11, committente) MAI SENZA ARMA: la condizione "PG senza arma" non deve esistere. Controllare tutti i punti
      del codice in cui c_eq (arma) puo' diventare 0 o restare 0 (equipaggiamento, vendita, rottura, baule di casa,
      morte, caricamento di un salvataggio, eroe nuovo, varianti di test, arena) e SEGNALARLI al committente.
      Fatto subito (08/11): tolto il pugnale messo d'ufficio da recalc_stats se c_eq = 0 (era l'unico codice che lo
      "regalava"; l'arma iniziale dell'eroe nuovo, start_weapon in rules.yaml, resta).
- [x] (07/11 sera, FATTO in v1.67+: stato in docs/wiki/refactor-tasti.md sezione 6; costo -400 B di margine; "quit to main
      menu" -> "quit game"; baule del piano a riquadri. [ ] Negozi in overlay: non fatti. [ ] RUN/STOP fantasma in VICE
      nelle build NOKEYS prima del ciclo di gioco: causa non trovata) REFACTOR TASTI E MENU: progetto completo in **docs/wiki/refactor-tasti.md**
      (entry point: quella pagina; qui solo il riassunto). Analisi di tutte le schermate (tasti letti, duplicati,
      non documentati come Q nel negozio, conflitti con W A S D: D inventario, A baule, S negozio, A/D casa e scheda),
      sistema standard "lista di voci": su/giu' + fire + RUN/STOP, uscita come voce selezionabile, modalita' e pagine
      come linguette (tab) selezionabili, niente destra/sinistra, fire = Y nelle domande y/n, badsave da y/n a lista
      (fire per abitudine non deve cancellare i salvataggi), casa del PG custom in OVLT con il riquadro dell'oggetto
      (gia' fatto). Costo stimato ~+50 B nel gioco (motore ~180 B + linguette ~120 B, meno 7 cicli di tasti copiati).
      Punti da decidere e ordine dei lavori: sezione 5 del documento. Dopo ogni parte: data/help.txt, docs/wiki/help.md,
      docs/wiki/interfaccia.md, manuale, test (test_saves c7, test_rel) nello stesso lavoro.
- [x] (07/11 sera) Cancellazione di un barbaro: nella scheda (menu) voci "start" e "delete barbarian" con
      sinistra/destra, conferma y/n; hero_delete in src/menu.asm (solo il record REC_HDR). Provato in VICE: cancellato,
      nuovo eroe nello stesso posto, elenco riletto dal disco dopo quit to main menu.
- [ ] Musica nell'help (Tavern of Dawn, come da progetto in docs/wiki/quests.md sez. 10): non fatta.
- [x] Menu del loader BARBARIAN: logo della copertina (v1.30).
- [ ] Tempi veri su 1541 (non emulato) del loader, di LORE (titolo + LDAT) e del ritorno al menu: non misurati.
- [ ] LORE 23 blocchi: quasi tutto START, sprite di PRESS SPACE e musica; si puo' ridurre solo togliendo il titolo.
- [x] (07/11) Due build: debug (./build.sh, tutti i giorni: BARBARIAN = loader senza menu -> START senza titolo -> gioco)
      e release (./build.sh --release, solo su richiesta: menu, LORE, LDAT, TITLE). Nomi: il loader = BARBARIAN
      (src/barbarian.asm, ex FRONT), START = avvio del gioco (src/start.asm, ex loader), test_start.py (ex test_loader.py).
- [x] (07/11, prova del committente sulla v1.29) Loader: logo della copertina al posto del titolo a caratteri, pagina
      dei tasti nella voce 2 (tolta dal menu dei barbari). START di release: barra di caricamento, subito il menu del
      gioco (niente titolo/PRESS SPACE: il titolo resta solo nella storia). Storia: 1 pixel ogni 6 fotogrammi, fire
      inerte fino alla fine, RUN/STOP anche durante il caricamento e a PRESS SPACE. Menu dei barbari: righe 5-9 eroi
      e "-", create in riga 12, "quit the game" (reset) in riga 14. HUD: J K L U O solo se disponibili, niente
      colori >= 8 (lettere illeggibili). Bug: baule aperto che restava sulla mappa tornando al piano (seed ANOANO,
      Fire non lo apriva): lv_get rimette il pavimento (test_rel lo controlla).
- [x] (07/11) Armi rotte: restano equipaggiate con danno 0 (niente pugni, tolti da rules.yaml: id -1, SAVE_VER $C1),
      nome in rosso nell'inventario, icona fissa nell'HUD. Deciso poi (07/11 pom.): armatura e scudo uguali, a 0
      restano, in rosso, senza CA.
- [x] (07/11) Test lenti solo in release (o tests/run_tests.sh --all): debug = test veloci + bilanciamento. Misurato nel
      container: debug ./build.sh 1 min 5 s; release ./build.sh --release 11 min 30 s (prima la debug eseguiva tutti
      i test, ~10 min). Test lento di un'area toccata: da lanciare a mano (CLAUDE.md).
- [x] (07/11 sera) Scheda del barbaro (menu): senza equipaggiamento, riquadri barbarian / progress / stats / scelta come
      inventario e negozi, valori allineati a destra, "deepest lvl", "time" (v1.40). Solo nel modulo MENU (fuori dal gioco).
