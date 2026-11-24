# Guida al bilanciamento di Barbarian: The Blood Path

Copyright © 2026 - Simone Caporale

Questa guida dice **come si bilancia il gioco**: quali numeri si toccano, con quali strumenti si misurano gli
effetti, quante prove servono, in che ordine procedere e cosa deve risultare vero alla fine. È scritta per chi
deve ripetere il lavoro fatto finora (Fable, 05–06/11) allo stesso modo, senza doverlo riscoprire. Le regole di
progetto che valgono sempre sono in `CLAUDE.md`; i numeri correnti e le decisioni prese sono in
`docs/wiki/BILANCIAMENTO.md` (progetto a 20 piani e ritarature) e nelle pagine della wiki
(`combattimento.md`, `mostri.md`, `oggetti.md`, `bottino.md`, `villaggio.md`).

## 0. Le tre regole che non si violano

1. **Il gioco è quello nel codice, non quello nel simulatore.** Ogni regola nuova o cambiata nel codice (o negli
   yaml) va riportata **nello stesso lavoro** nei simulatori di `tools/simulators/`, e viceversa: un numero deciso al
   simulatore non vale finché il codice non fa la stessa cosa. Le differenze note e accettate stanno in
   `docs/wiki/BILANCIAMENTO.md` § "Differenze fra simulatore e codice": se ne aggiungi una, scrivila lì.
2. **Si cambiano i dati, non il codice**, finché si può: `data/rules.yaml` (regole del combattimento: PG,
   mostri, crescita per piano, pozioni, oggetti, durabilità) e `data/balance.yaml` (mondo: piazzamento dei mostri,
   bottino, chestLevel, bauli, negozi, oro). `tools/build/gen_db.py` li trasforma in `out/work/db.asm` e **controlla**
   limiti a 8/16 bit e coerenze (fallisce con un messaggio chiaro): leggere sempre il suo output.
3. **Ogni cambio di bilanciamento si chiude con**: `./build.sh` verde (comprende `tests/regression/balance/test_balance.py`, che
   gira sul simulatore con soglie larghe), la pagina della wiki corrispondente aggiornata con i numeri nuovi, una
   nota datata in `docs/wiki/BILANCIAMENTO.md` con la motivazione (il `TODO.md` tiene solo i lavori aperti), e — se il
   cambio è grande — una sezione nuova in `docs/wiki/BILANCIAMENTO.md` ("Ritaratura del gg/mm: cosa è cambiato e perché").

## 1. Gli strumenti e cosa misurano

| Strumento | Cosa fa | Tempo | Quando usarlo |
|---|---|---|---|
| `tools/simulators/rules.py` | modello condiviso: legge gli yaml, calcola statistiche di PG e mostri per piano (`floor_types`, `monster`, `Hero`, `ref_hero`), probabilità di colpire (`hit_chance`) | — | importato dagli altri |
| `tools/simulators/sim_rules.py` | Monte Carlo dei combattimenti (d20, abilità, pozioni, stordimenti, boss, evocazioni) e **report HTML** `out/work/simulators/simulazione_regole.html` | ~2 min per il report | ogni volta che cambiano PG, mostri, abilità, pozioni, crescita |
| `tools/simulators/sim_rules.py --fight PIANO LIVELLO MOSTRO [MOSTRO…]` | una serie singola, stampa vittorie, durata, vita finale, colpi | secondi | per rispondere a una domanda precisa |
| `tools/simulators/fit_rules.py` | **taratura automatica** delle curve dei mostri (`growth.*`, `final_boss_hp_mult`, tabella dell'Abisso) sugli obiettivi del § 3 | 10–25 min | dopo un cambio che sposta la forza del PG (nuova arma, abilità, pozioni) |
| `tools/simulators/cmp_rules.py` | confronto A/B di due set di regole sugli stessi combattimenti | minuti | per decidere fra due varianti |
| `tools/simulators/sim_chest.py` | chestLevel e probabilità di ogni oggetto per piano (riproduce `gen_item`) | secondi | bottino, livelli oggetto, magia |
| `tools/simulators/sim_gold.py` | oro trovato e vendita per piano (Monte Carlo sul censimento dei piani veri, 20/11), bauli epici, borsello | secondi | prezzi, oro iniziale, premi |
| `tools/simulators/sim_floor.py` | (20/11) piano intero con la cintura a 4 o a 8 pozioni: morti e ritorni in città per piano | minuti | cintura, pozioni, difficoltà del piano |
| `tools/simulators/sim_builds.py` | (20/11) profili di PG (forza, destrezza, costituzione, bilanciato) con le regole di oggi e con la proposta `data/rules_next.yaml`: morti + ritorni ogni 10 mostri, PG a livello piano +0/+1/+2, boss di capitolo e finale con le meccaniche (`boss_scripts.py`), `--fit-bosses` | secondi | caratteristiche, punti per livello, difficoltà per piano |
| `tools/simulators/fit_stats.py` | (20/11) costi delle caratteristiche della proposta: modello analitico e griglia (2 min), `--show` | minuti | FOR, DES, COS, rendimento decrescente |
| `tools/simulators/sim_durability.py` | durabilità generata, usura per piano, piani per riparazione, rottura contro i boss | ~1 min | durabilità, usura, soglia degli avvisi |
| `tools/vice/arena.py` | **il codice vero in VICE**: una stanza, PG configurabile, 1–8 mostri, N combattimenti; vittorie, durata, vita, danni, pozioni, xp, usura (`--dur`) | 10–60 s per serie | per verificare che il simulatore non menta su un caso preciso |
| `tests/regression/balance/test_balance.py` | guardia di regressione (PG di riferimento vince ai piani 1–19, PG di livello 1 perde al piano 10, vita crescente) | 2 s | in ogni build |
| `tests/regression/balance/test_arena.py` | una serie di arena ripetibile (seme fisso): se i numeri cambiano, il codice di combattimento è cambiato | 30 s | in ogni build |

Regole d'uso:
- **Quante prove.** Il rumore di una percentuale di vittorie su N combattimenti è circa ±100/√N punti: con 40
  prove ±16, con 150 ±8, con 400 ±5. Per **esplorare** bastano 40–60 (è quello che fa `fit_rules.py` dentro la
  ricerca), per **decidere** servono 150–400 (`--check 400`, `cmp_rules.py --fights 400`), per **documentare**
  (report) 150. I semi sono fissi: la stessa domanda dà la stessa risposta, e due varianti si confrontano sugli
  stessi tiri.
- **Il simulatore è il caso peggiore "fermo"**: PG immobile con i mostri a contatto. Nel gioco si gira, si usa
  Whirlwind sui gruppi, si scappa: i numeri veri sono un po' più favorevoli. Per questo gli obiettivi (§ 3) sono
  prudenti e la verifica finale si fa anche **giocando** (§ 8).
- **L'arena serve a smentire il simulatore**, non a tararlo: quando un risultato del simulatore sorprende, si
  rifà lo stesso scontro in arena (`tools/vice/arena.py --lvl 10 --plvl 10 --weapon sword+1 --armor chain_mail
  --shield medium_shield --ring copper+1 --monster skeleton_king --boss 1 --potions red:2,yellow:2 --fights 30`).
  Se i due differiscono per più del rumore, c'è un errore nel modello o nel codice: cercarlo prima di toccare i
  numeri. Attenzione: l'arena azzera il seme a ogni serie (`seed`, di solito `$1234`); per statistiche indipendenti
  variare il seme fra le serie (vedi `tests/regression/items/test_items.py`). (23/11) Nei piani dei boss (5, 10, 15, 20)
  l'arena carica il codice del piano (meccaniche dei boss, evocazioni del piano 20) e gioca un combattimento alla volta con
  seme + 7919·k; `ovl=False` per lo scontro senza meccaniche ([dungeon](dungeon.md)). (24/11) Il bot fermo (`--bot stand`) colpisce il mostro più
  vicino: con evocati o feticci lontani dal PG serve `--bot adds` (prima gli altri mostri, poi il boss, aggirando gli ostacoli).
  Nemmeno lui gioca come un giocatore (cammina male, non schiva): con Mother Stitch simulatore e arena restano lontani
  ([bestiario](bestiario.md)).

## 2. Che cosa governa che cosa (mappa dei parametri)

| Elemento | Parametri | File | Simulatore |
|---|---|---|---|
| PG: caratteristiche, vita, competenza per livello | `player.scores`, `increases`, `hp_*`, `proficiency` | rules.yaml | sim_rules |
| Esperienza e livelli | `xp_needed` (auto = ~1,3 livelli per piano esplorato), `xp_per_floor`, xp dei mostri, calo per differenza di livello | rules.yaml | sim_rules (`progression`) |
| Abilità: livello, ricarica, area, effetto | `skills.*` | rules.yaml | sim_rules |
| Rage / Frenzy | `skills.rage`, `skills.frenzy` (durata, ricarica, corsa) | rules.yaml | sim_rules (corsa esclusa) |
| Pozioni: cura, ricarica, zone per piano | `potions.*` | rules.yaml | sim_rules (beve sotto il 35%) |
| Oggetti: dadi, CA, livello oggetto, prezzo, due mani/penetrazione | `weapons`, `armors`, `shields`, `rings` | rules.yaml | rules, sim_chest, sim_gold |
| Equipaggiamento atteso per piano | `reference[piano]` | rules.yaml | tutto: è "il PG di riferimento" |
| Mostri: scheda base, piano minimo, livello, xp | `monsters.*` | rules.yaml | sim_rules, sim_gold |
| Crescita per piano: CA, ATT, danno, dadi di vita, moltiplicatori | `growth.*` (`curve_hp`, `curve_dmg` per piano) | rules.yaml | **tarati da fit_rules** |
| Boss con nome e boss finale | `boss.*` (vita ×, CA +, ATT +, xp ×), `lord_of_ruin`, `final_boss_hp_mult`, `final_summons` | rules + balance | sim_rules, fit_rules |
| Quanti mostri per piano, varianti forti | `spawn.*` (tabelle per gradino, `strong_*`) | balance.yaml | sim_gold (quantità), sim_durability |
| Bottino: cosa lasciano i mostri, bauli del piano | `drops`, `chests` | balance.yaml | sim_gold, sim_chest |
| chestLevel e generazione degli oggetti | `chest_level`, `loot` (pesi, `bonus`), `boss.loot_*` | balance.yaml | sim_chest |
| Oro: iniziale, per mostro, bauli, epici | `player.start_gold`, `drops.gold`, `final_gold` | balance.yaml | sim_gold |
| Negozi: assortimento, vendita, riparazione | `shops.*`, `durability.repair_cost_percent` | balance / rules | sim_gold (spesa), sim_durability |
| Durabilità e usura | `durability.*` (min, max, peso del livello oggetto, wear, avviso) | rules.yaml | sim_durability |
| Abisso (piani 21+) | `void.*` | rules.yaml | fit_rules (`--abyss-only`) |

Tutto ciò che non è in questa tabella (velocità, aree in pixel, tempi delle ricariche in fotogrammi, raggio
d'aggro) è nel codice e si misura solo giocando o in arena.

## 3. Gli obiettivi (cosa deve risultare vero)

Sono gli obiettivi usati finora (`docs/wiki/BILANCIAMENTO.md` § 1 e § 10, `tools/simulators/fit_rules.py`); cambiarli è una
decisione del committente, da scrivere in `BILANCIAMENTO.md`.

| Misura | Obiettivo | Dove si legge |
|---|---|---|
| Probabilità di colpire (PG di riferimento contro il mostro base più forte del piano, e viceversa) | il più **stabile** possibile dal piano 1 al 20 (PG ~60–70%, mostri ~40–55%) | `fit_rules` fase 1, report § 2 |
| Boss con nome del piano, PG di riferimento con 4 pozioni (rossa, rossa, gialla, viola) | **~70%** di vittorie (finestra 55–85) | report § 4, `fit_rules` fase 2 |
| Gruppo di 3 mostri base del piano | ≥ **95%** di vittorie, vita finale ~60%, durata 4–8 s | report § 4 |
| 1 mostro base | ~100%, durata 1–3 s | report § 4 |
| Boss finale (livello 20, 4 pozioni) | **~65–75%** | report § 5, `fit_rules --final` |
| PG sotto livello (livello 1 al piano 10) | perde quasi sempre (< 30%) | `test_balance.py` |
| Progressione | ~1,3 livelli per piano esplorato tutto; livello 20 attorno al piano 19 | report § 3 (`xp_needed: auto`) |
| Oro | la spada vichinga (2400) e le piastre (3600) comprabili verso il piano 8–10; ~17 000 oro raccoglibile in tutto; bauli epici = 10% del totale diviso 4 | `sim_gold.py` |
| Bottino | i tesori danno quasi sempre roba base; l'oggetto "che permette di scendere" (vichinga, ilvl 12) compare dal piano 11 nei tesori del boss, 2–11% dei tiri d'arma; magia +1 dal 5, +2 dal 14 | `sim_chest.py` |
| Durabilità | una riparazione dell'arma ogni ~3 piani in profondità; **un'arma sana non si rompe in un combattimento col boss** (≥ 25 punti: 0%) | `sim_durability.py` |
| Regressioni | `tests/regression/balance/test_balance.py` e `tests/regression/balance/test_arena.py` verdi | build |

## 4. Il procedimento standard (in ordine)

Ogni bilanciamento, piccolo o grande, segue questi passi. Saltarne uno è il modo in cui si introducono errori
silenziosi (è successo: `loot.window` rimasta negli yaml senza effetto nel codice; la fontana senza il tile che
cura; il pugnale "sano" segnalato come rotto per una soglia assoluta).

1. **Formulare la domanda in una misura** del § 3 ("il boss del piano 6 si vince il 60%: voglio 70").
2. **Guardare lo stato attuale** con lo strumento giusto (report, `--fight`, `sim_chest`…) e scrivere il
   numero di partenza.
3. **Cambiare un parametro alla volta** negli yaml; `python3 tools/build/gen_db.py` deve passare (limiti 8/16 bit!).
4. **Misurare di nuovo** con lo stesso strumento, stesse prove, stesso seme. Se la differenza è dentro il
   rumore (± 100/√N), non è un risultato: alzare N o cambiare di più.
5. **Guardare gli effetti collaterali**: un cambio ai mostri sposta esperienza (progressione), oro
   (`sim_gold`), usura (`sim_durability`: più colpi per uccidere = più usura). Rilanciare i simulatori toccati.
6. **Verificare nel codice vero** quando il cambio tocca qualcosa che il simulatore approssima: una serie in
   arena sul caso più rappresentativo, oppure una prova in VICE.
7. **Rigenerare il report** (`python3 tools/simulators/sim_rules.py`) se sono cambiati PG, mostri o abilità, **build con
   test**, wiki, e una nota datata in `BILANCIAMENTO.md` (la voce del `TODO.md` si chiude).

Per i cambi grandi (una regola nuova: durabilità, chestLevel, pozioni a cura fissa) l'ordine è: scrivere prima
la regola nel simulatore e in un **documento di progetto** (una sezione in `BILANCIAMENTO.md` con tabella dei
valori previsti), far vedere i numeri al committente, poi implementare nel codice **con gli stessi nomi** dei
parametri, poi arena/test per confermare che codice e simulatore coincidono.

## 5. Procedure per elemento

### 5.1 Mostri e crescita per piano (il cuore)
- Non tarare a mano `growth.*`: lanciare `python3 tools/simulators/fit_rules.py` (`--fights 60 --check 400`, ~20 min;
  `--dry` per vedere senza scrivere; `--final` per ritarare anche il boss finale). Fa tre cose in ordine:
  (1) `ac_per_floor`/`att_per_floor` per probabilità di colpire stabili (solo conti), (2) `curve_hp` e
  `curve_dmg` piano per piano, monotone, sugli obiettivi boss ~70% / gruppo ≥ 95% / durata 4–8 s, (3) il
  boss finale. Scrive `rules.yaml` e un commento con la data.
- Poi **leggere il report** (`out/work/simulators/simulazione_regole.html`): la riga dei boss per piano non deve avere buchi
  (piani al 40% o al 100%); se ce ne sono, è di solito l'equipaggiamento di riferimento (`reference`) sbagliato
  per quel piano, non la curva.
- Scheda base di un mostro nuovo: scegliere vita, CA, ATT, danno, salvezza in linea con i vicini di piano minimo
  (tabella in `docs/wiki/mostri.md`), poi `fit_rules` ritara le curve attorno.
- Esperienza: `xp` della scheda × crescita; se la progressione (report § 3) esce dall'obiettivo, si corregge
  `xp_needed` (lasciarlo `auto` a meno di motivi) o gli `xp` delle schede, non le curve.
- Verifica in arena di un piano: `tools/vice/arena.py --lvl N --plvl N … --monster <base più forte> ×3 --fights 40`
  e `--boss 1`.

### 5.2 PG, abilità, Rage/Frenzy
- Caratteristiche e vita: `player.*`; ogni cambio sposta **tutto**: dopo, rilanciare `fit_rules`.
- Abilità: ricarica e area sono in fotogrammi/pixel nel codice e in secondi nel simulatore: tenerli uguali
  (tabella in `docs/wiki/combattimento.md`). Il simulatore non conta la corsa della Frenzy né lo spostamento: le
  abilità "di posizione" (Whirlwind sui gruppi) sono sottostimate; giudicarle anche giocando.
- Soglia di critico, vantaggio dello Smash, CD del Battle Cry: `rules.yaml`, visibili subito nel report § 4.

### 5.3 Pozioni
- Cura fissa per colore (`potions.*`), ricarica che blocca tutte le pozioni, zone per piano (`zones`/`ramp`).
  Il simulatore beve sotto il 35% con la cintura di riferimento (rossa, rossa, gialla, viola): cambiare la
  cintura di riferimento in `fit_rules.POTS` e `test_balance.POT` se cambia la regola delle zone.
- Misura: vita finale e pozioni bevute per combattimento (report § 4: colonne "vita", "pozioni").

### 5.4 Oggetti, livelli oggetto, prezzi
- Il **livello oggetto** (`ilvl`) decide quando un oggetto compare nei tesori (`sim_chest.py`: tabella per piano)
  e nei negozi (`shop_minl` ≤ livello del PG: livello oggetto − `level_ahead`, villaggio.md). Regola: un oggetto di
  ilvl N è pensato per il piano/livello N; il "salto" (vichinga 12, piastre 14) deve arrivare quando l'oro lo
  permette (`sim_gold.py`).
- **Prezzi**: proporzionali all'oro che un PG guadagna al livello in cui l'oggetto serve: tabella "livello →
  oro per piano" da `sim_gold.py`; regola proposta: un oggetto di ilvl N costa l'oro di ~1,5 piani al livello N.
  Vendita a metà, riparazione al 25%. Oro iniziale 100 (06/11).
- `reference[piano]` va aggiornato se cambiano prezzi o ilvl: è la base di tutte le misure dei mostri.
- Test: `gen_db.py` controlla che ogni categoria abbia un oggetto di ilvl 0 (altrimenti un tesoro di basso
  livello resta vuoto).

### 5.5 Bottino, chestLevel, oro
- `sim_chest.py --n 20000`: per ogni piano, probabilità di ogni oggetto e della magia; gli obiettivi sono "quasi
  solo base, ogni tanto il salto". Parametri: `chest_level` (per piano, bonus del tipo, forte, vita), `loot`
  (pesi delle categorie, `bonus.per_loot_level`), `boss.loot_level_add`.
- `sim_gold.py` (20/11): oro trovato e valore di vendita per piano, Monte Carlo sul censimento dei piani veri
  (`tools/vice/floor_census.py`); `final_gold` = 10% del totale / 4 (bauli epici); borsello a gradini. Dopo un cambio a `drops`,
  `chests` o ai prezzi rilanciarlo; dopo un cambio a `spawn` o al generatore (`GVER`) rifare prima il censimento.
- Attenzione al **ritmo dei tesori** (uno su cinque mostri, max 15 bauli per piano): non è simulato; si
  giudica giocando.

### 5.6 Durabilità, usura, riparazione
- `sim_durability.py --n 20000`: durabilità generata per oggetto, usura per piano misurata **con i combattimenti
  del simulatore** (colpi a segno e subiti), piani per riparazione con l'arma del PG di riferimento, rottura
  contro il boss del piano e il boss finale.
- Obiettivi: riparazione ogni ~3 piani in profondità; nessuna rottura in un combattimento col boss partendo
  sani (P < 1% con durabilità ≥ 25): da qui la soglia dell'avviso (20%).
- Verifica nel codice: `tools/vice/arena.py … --dur N --fights 30 --boss 1` (usura reale in una serie).

### 5.7 Villaggio e negozi
- Assortimento per negozio (`shops.*`: pool, `stock`, dal 06/11 `level_ahead`), prezzi, riparazione. Nessun
  simulatore oltre a `sim_gold` per la spesa: si giudica con la regola del § 5.4 e giocando (si deve poter
  comprare qualcosa di utile a ogni ritorno in città, senza che il negozio regali il salto).

### 5.8 Abisso (piani 21+)
- `void.table` (CA +, danno ×) tarata da `fit_rules.py --abyss-only` con livello = piano; obiettivo: curva di
  vittorie che scende dolcemente. Non è ancora giocabile: solo simulatore.

## 6. Come leggere il report (`out/work/simulators/simulazione_regole.html`)

1. **Tabelle del PG e dei mostri per piano**: controllare prima i numeri (CA, ATT, vita) per vedere a occhio
   un salto anomalo (un mostro che al piano 8 ha vita doppia del piano 7).
2. **Probabilità di colpire**: due curve piatte; se una scende sotto il 40% o sale sopre l'80% in qualche
   piano, i combattimenti diventano o lunghissimi o banali.
3. **Progressione**: livello del PG per piano esplorato; deve arrivare a 20 verso il piano 19.
4. **Vittorie per piano e gruppo** (1 base, 3 base, 1 forte, boss): le colonne "vita finale", "pozioni",
   "durata" dicono *perché* si vince o si perde (si vince ma con il 10% di vita = troppo tirato; si perde con 4
   pozioni avanzate = colpisce troppo poco).
5. **Boss finale**: percentuale con e senza pozioni e per livello.
Quando un numero non torna, prima si rifà lo scontro singolo (`--fight`) e lo si legge colpo per colpo (il
simulatore stampa la cronaca con `-v` se presente, altrimenti aumentare `n` e guardare la distribuzione).

## 7. Errori già fatti (da non ripetere)

- Tarare con 20–40 prove e credere al risultato: ±15 punti di rumore.
- Cambiare due cose insieme (vita del boss e pozioni) e non sapere quale ha avuto effetto.
- Lasciare un parametro negli yaml che il codice non legge più (`loot.window`): `gen_db.py` deve usare **tutto**
  ciò che legge, o il parametro va tolto.
- Soglie assolute dove serve una percentuale (avviso di durabilità a 20 punti: un pugnale da 15/15 è "rotto").
- Dimenticare la differenza fra livello e piano (livello = piano nel dungeon, +2 forte, +1 boss per l'esperienza).
- Non rigenerare il report e la wiki: i numeri scritti nelle pagine devono essere quelli degli yaml **di oggi**.
- Fidarsi dell'arena con un seme solo come fosse una statistica.

## 8. La prova giocata (obbligatoria alla fine)

Il simulatore non vede: movimento, scorrimento, raggio d'aggro, ritmo dei tesori, tempo ai negozi, noia.
Dopo una ritaratura si gioca dal disco di release per **almeno 10 minuti** (lista in `TODO.md`, sezione 7 "Verifiche e
misure"): nuova partita → villaggio → piano 1–3 con le abilità, un boss, una morte, un ritorno, una riparazione.
Si annota in `TODO.md` (sezione 4, bilanciamento) ciò che non torna con il numero del piano e del livello del PG: è l'unico modo per
scoprire i problemi che i simulatori non vedono (es. le pozioni gialle in vendita al livello 1, i tesori
troppo rari ai primi piani).
