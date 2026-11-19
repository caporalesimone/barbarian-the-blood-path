# Bestiario — mostri per capitolo (11/11)

Copyright © 2026 - Simone Caporale

Richiesta del committente (11/11): un **bestiario** con mostri dalle caratteristiche diverse, **uno per capitolo** (il
bestiario di un capitolo sostituisce quello del capitolo precedente); il **boss finale** (Lord of Ruin) va nel bestiario
dell'**ultimo capitolo**; il **capitolo 1 ha un boss nuovo**; concept per altri 3 capitoli (un boss, mostri comuni e
varianti potenziate come oggi). Modello: il database dei mostri di Diablo (DevilutionX).

**Stato**: la tabella `data/monsters/bestiary.tsv` è la **sorgente dei mostri** dall'11/11 (`tools/build/bestiary.py`: le
**statistiche** del gioco vengono dalle righe `implemented = yes`, i 9 tipi di sempre). **Dal 15/11 ogni capitolo ha nel gioco
i suoi mostri**: sprite, colore e nome delle 4 famiglie e delle 4 varianti forti del capitolo, e il boss del capitolo nel suo
piano del boss (sezione sotto). **Statistiche e IA non cambiano**: il tipo *t* di ogni capitolo ha le statistiche del tipo *t*
del capitolo 1 (`data/balance.yaml` e `rules.yaml`, crescita per profondità); le statistiche delle righe concept sono ancora
numeri provvisori (TODO M9).

## Nel gioco: i mostri dei capitoli (15/11)

Richiesta del committente (15/11): "disegna i mostri per capitolo oltre che i boss, poi falli includere nel gioco".

| Capitolo | Tipo 1 (stat. Fallen) | 2 (Skeleton) | 3 (Zombie) | 4 (Demon) | 5 (Fallen Warchief) | 6 (Skeleton King) | 7 (Lich) | 8 (Balrog) | Posto del boss (9) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Fallen (10) | Skeleton (1) | Zombie (13) | Demon (4) | Fallen Warchief (3) | Skeleton King (7) | Lich (14) | Balrog (8) | dungeon: Lord of Ruin (2); piano 5: The Hollow Abbot (14) |
| 2 | Drowned (3) | Bog Crawler (5) | Mire Witchling (4) | Will-o'-Wisp (13) | Drowned Hulk (14) | Crawler Queen (13) | Hag of the Mere (10) | Corpse Light (7) | dungeon: Lord of Ruin; piano 10: The Miller of Bad Water (8) |
| 3 | Ash Ghoul (12) | Bone Archer (1) | Hellhound (2) | Frost Wight (14) | Pyre Ghoul (8) | Bone Marksman (7) | Hellhound Alpha (10) | Wight Lord (3) | dungeon: Lord of Ruin; piano 15: Varok the Oathbreaker (7) |
| 4 | Imp (10) | Blood Knight (2) | Gargoyle (12) | Cultist (4) | Imp Overseer (8) | Blood Champion (4) | Stone Gargoyle (15) | High Cultist (7) | Lord of Ruin (2) (piano 20, sala del trono) |

Fra parentesi il colore C64 dello sprite. Il tipo decide **tutto il resto** come prima: statistiche, profondità minima
(`maxtype_tab`: il tipo 4 compare dalla profondità 8, quindi nel capitolo 2 Will-o'-Wisp e Corpse Light solo dal piano 3 del
capitolo), velocità (il tipo 3 è lento come lo zombie: Mire Witchling, Hellhound, Gargoyle), bottino, evocazioni del boss finale
(tipi base del piano 20: nel capitolo 4 Imp, Blood Knight, Gargoyle, Cultist). Il boss con nome dei piani normali resta
"nome + epiteto" (`first_names`/`epithets` di `balance.yaml`, uguale in ogni capitolo); **il boss di capitolo** (piani 5, 10, 15)
nella barra mostra il **suo nome** (prima: un nome + epiteto a caso), il boss finale "lord of ruin".

**Come arriva nel gioco** (`tools/build/gen_gfx.py`, `src/game.asm` `gfx_install`, [formato](FORMATO_DATI.md)):
- Disegni: `tools/build/monsters.py` (capitolo 1, boss dei capitoli, Lord of Ruin; `chapter_set(c, boss)`) e
  `tools/build/monsters_chap.py` (`CHAPTER_MONSTERS`, capitoli 2–4). Stesso formato: 12×21 multicolor, `b` MC0 marrone 9,
  `c` colore dello sprite, `g` MC1 grigio chiaro 15.
- Ogni file del tema `GFX(2c−1)` (piani 1–4 del capitolo) e `GFX(2c)` (piano del boss) porta il set del **suo** capitolo:
  sprite dei tipi 1–4 (slot 12–19), 5–8 e 9 (`$8C00`), e in coda un **blocco info** di 147 B (`GFX_INFO`): 9 colori, 9 indirizzi,
  9 nomi in codici schermo. `gfx_install` copia il blocco a `NM_AT` (`$8F6D`, coda degli slot sprite 58–63, dopo il motivetto
  di combattimento): `build_sprites` legge il colore da `NM_AT−1+tipo` (tolta la tabella `mon_col` e il caso `cb_col` del boss
  di capitolo), `bar_name` il nome (tolti i nomi `tn_*` da GAME). Per far stare il blocco il file comincia 147 B prima di
  `$ED00` (`GFX_DUN_AT` = `$EC6D`, coda del buffer del villaggio, libera nel dungeon) e finisce sempre a `$F4E0`.
- Costo (misurato nella build del 15/11): GAME **−115 B** (margine del codice 2283 → 2398 B: i nomi e i colori non stanno più
  in GAME, il codice nuovo è ~25 B); disco **+8 blocchi** (ogni `GFXn` da 8 a 9 blocchi: 171 → 163 liberi).
- Controlli: la build verifica che nomi e colori dei disegni coincidano con `name` (in minuscolo) e `color` del bestiario per
  ogni file; test `MON-CHAP-11..14` e `MON-CHAP-20` (regression, `tests/regression/monsters/chapters`): sprite negli slot, colori e nomi a
  `NM_AT` per un piano del dungeon e il piano del boss di ogni capitolo, il nome **disegnato** nella barra (decodificato con la
  ROM dei caratteri) per un mostro e per il boss di ogni capitolo, ritorno al capitolo 1; atlante grafico, sezione Sprite.
- Ritocco ai disegni (15/11): Stone Gargoyle, le crepe da `g` a `b` (erano grigio chiaro 15 come il corpo: sparivano).

**Resta** (TODO M9): statistiche proprie dei mostri dei capitoli 2–4 (oggi concept nel bestiario), IA nuove (distanza, carica,
teletrasporto, evocazione), meccaniche dei boss di capitolo, bilanciamento con i simulatori.

## Come fa Diablo (DevilutionX, `assets/txtdata/monsters/`)

| File | Contenuto | Colonne principali |
|---|---|---|
| `monstdat.tsv` (112 righe) | i tipi di mostro | `_monster_id`, `name`, grafica (`assetsSuffix`, `trnFile` = **palette alternativa**), `availability`, `minDunLvl`/`maxDunLvl` (finestra di piani), `level`, `hitPointsMinimum/Maximum`, `ai` (Zombie, Fallen, SkeletonMelee, SkeletonRanged, Scavenger, ...), `abilityFlags`, `intelligence`, `toHit`, `minDamage`/`maxDamage`, attacco speciale (`toHitSpecial`, danni), `reducePlayer*`, `armorClass`, `monsterClass` (Undead, Demon, Animal), `resistance` (`IMMUNE_MAGIC`, `RESIST_FIRE`, ...), `treasure`, `exp` |
| `unique_monstdat.tsv` (100 righe) | i **mostri unici** con nome (boss) | `type` (tipo di base), `name`, `trn`, `level`, `maxHp`, `ai`, danni, `resistance`, `monsterPack` (None, Independent, Leashed: il branco che lo accompagna), `customToHit`/`customArmorClass`, `talkMessage` |

Cosa si impara:
- **Famiglie di 4 varianti** dello stesso sprite con un'altra palette e numeri più alti (Zombie → Ghoul → Rotting Carcass →
  Black Death; Fallen One → Carver → Devil Kin → Dark One), ognuna con la sua **finestra di piani** (`minDunLvl`..`maxDunLvl`).
  Da noi: base + variante **forte** (stesso sprite, altro colore, `strong_of`), come già nel gioco.
- **Unici** = un tipo di base + nome + statistiche proprie + branco. Da noi: il **boss con nome** di ogni piano (vita × 2,5,
  nome da `first_names` + `epithets` di `balance.yaml`) e i **boss di capitolo** (come Butcher, Skeleton King, Lazarus).
- **IA per famiglia** (`ai`): da noi oggi c'è un'IA sola (inseguimento e mischia); la colonna `ai` del bestiario descrive
  quella voluta per i concept (veloce, distanza, evocazione, carica): ogni IA nuova è codice da scrivere (TODO M9).
- `monsterClass` e `resistance` servirebbero con armi/abilità che ne tengono conto: oggi non ci sono (concept).

## La tabella `data/monsters/bestiary.tsv`

Colonne (README in `data/monsters/README.md`): `id`, `chapter`, `tier` (`base`, `strong`, `boss` = boss di capitolo,
`final` = boss finale), `strong_of`, `name`, `floor` (**profondità globale** minima, 1..255), `level`, `hp` (dadi), `ac`,
`att`, `dmg`, `save`, `xp`, `speed`, `color` (C64), `loot_level_bonus`, `flags` (`strong`, `final`, `stun_immune`,
`chapter_boss`), `ai`, `sprite`, `implemented`, `notes`. Le statistiche dei concept sono quelle di un mostro di oggi
**cresciuto** alla stessa profondità (demone + crescita per piano di `rules.yaml`), poi ritoccate per ruolo: resistente
(più vita, più lento), veloce (meno vita, velocità 10), picchiatore (più danno, meno CA). Da tarare col simulatore
(`tools/simulators/chapters.py`) quando i capitoli saranno nel codice.

## Bestiari (proposta, capitoli di [Capitoli](capitoli.md))

| Capitolo (profondità) | Comuni | Forti (stesso sprite con un'aggiunta, altro colore) | Boss |
|---|---|---|---|
| 1 — Aldric's Hollow (1–5) | Fallen, Skeleton, Zombie, Demon (**oggi**) | Fallen Warchief, Skeleton King, Lich, Balrog (oggi) | **The Hollow Abbot** (nuovo) |
| 2 — Bad Water (6–10) | Drowned, Bog Crawler, Mire Witchling, Will-o'-Wisp (15/11) | Drowned Hulk, Crawler Queen, Hag of the Mere, Corpse Light | **Mother Stitch, the Dollmaker** (19/11; prima The Miller) |
| 3 — The Last Camp (11–15) | Ash Ghoul, Bone Archer, Hellhound, Frost Wight (15/11) | Pyre Ghoul, Bone Marksman, Hellhound Alpha, Wight Lord | **Varok the Oathbreaker** |
| 4 — The Throne of Ruin (16–20) | Imp, Blood Knight, Gargoyle, Cultist (15/11) | Imp Overseer, Blood Champion, Stone Gargoyle, High Cultist | **Lord of Ruin** (il boss finale di oggi, spostato qui) |
| Abisso (21–255) | tutti i bestiari precedenti, mescolati (proposta) | idem | boss con nome a ogni piano; nessun boss di capitolo (D-CAP-4) |

Nota: con il capitolo 1 di 5 piani (regola dell'11/11 sera: 5 piani per capitolo), **Demon e Balrog** (profondità minima 8 e 9) non comparirebbero più nel capitolo 1:
o passano al capitolo 2 (che oggi ha tre concept propri) o si abbassa la loro profondità. Da decidere con B11.

### Concept dei boss
- **The Hollow Abbot** (capitolo 1, mappa finale del capitolo): l'abate della cripta sotto Aldric's Hollow, uno scheletro
  in una tonaca marcia con un turibolo di fuoco verde. Al 66% e al 33% della vita rialza 2 scheletri. Immune al blocco.
- **Mother Stitch, the Dollmaker** (capitolo 2, 19/11, decisione del committente: tema voodoo al posto del mulino e del
  mugnaio): la bambolaia della palude, cappello a tesa larga con le piume, viso pallido cucito, veste viola con le toppe, un
  ago enorme. Pianta **feticci** (bambole di paglia su un palo) che la proteggono. Nel gioco il nome è "mother stitch" (i nomi
  dei mostri sono al massimo 24 caratteri, senza virgola).
- **Varok the Oathbreaker** (capitolo 3): il cavaliere che ha tradito l'ultimo accampamento. Carica (scatto verso il PG) e
  colpo di scudo (stordisce); chiama 2 Ash Ghoul.
- **Lord of Ruin** (capitolo 4): invariato (sala del trono, evocazioni a ondate, leva verso l'Abisso).

### Meccaniche dei boss di capitolo (decise il 15/11)

Richiesta del committente (15/11, TODO Z2): decidere quale meccanica di gioco ha ogni boss di capitolo. **Decise qui, non nel
codice**: oggi il boss di capitolo è il boss con nome del piano (statistiche del piano, l'IA di tutti: inseguimento e mischia)
con il **suo sprite** (15/11: `tools/build/monsters.py`, `ABBOT`, `STITCH` dal 19/11, `VAROK`; colori 14, 4, 7). Ogni meccanica insegna una
cosa sola e si legge dallo schermo (un avviso prima del colpo). Le stime sono a occhio, non misurate.

| Boss | Capitolo | Meccanica | Cosa insegna | Come si vede | Cosa serve nel codice (stima) |
|---|---|---|---|---|---|
| **The Hollow Abbot** | 1 | **Evoca i morti**: al 66% e al 33% della vita si ferma, agita il turibolo e fa alzare 2 scheletri. Finché uno scheletro evocato è vivo, l'abate **si rigenera** (1 punto vita ogni mezzo secondo) | scegliere il bersaglio: prima gli evocati | l'abate lampeggia verde per 1 s, bordo verde; gli scheletri compaiono accanto a lui | soglie di vita (2 byte), `spawn` di 2 mostri a piano avviato, rigenerazione a tempo: ~120 B |
| ~~The Miller of Bad Water~~ (sostituito il 19/11 da Mother Stitch) | 2 | **Il giro della macina**: ogni 4 s carica il colpo (1 s fermo), poi colpisce **tutto attorno a sé** entro 2 caselle (danno doppio); dopo il colpo resta **scoperto** 1,5 s (subisce danno doppio). Al 50% chiama 2 Drowned | entrare e uscire a tempo: colpire nella finestra, scappare durante la carica | il mugnaio lampeggia bianco mentre carica; un anello (lo sprite del Whirlwind) al colpo | stato a tempo (carica / colpo / scoperto), colpo ad area riusando `fz_*` del Whirlwind: ~150 B |
| **Varok the Oathbreaker** | 3 | **La carica**: quando è allineato con l'eroe (stessa riga o colonna) parte in linea retta a velocità doppia finché non urta; se urta **un muro** resta stordito 2 s (unico momento in cui lo scudo è giù). Fuori dallo stordimento lo **scudo** dimezza i danni | usare la sala: mettersi davanti a un muro e scansarsi | Varok lampeggia giallo e si ferma mezzo secondo prima di partire; da stordito è grigio | movimento in linea con velocità propria, urto, stato stordito, riduzione del danno: ~180 B |
| **Lord of Ruin** | 4 | **Il pentacolo brucia** (in più a quello che fa oggi): al 75%, 50% e 25% le linee della stella sul pavimento si accendono per 3 s e chi ci sta sopra prende danno; all'ultimo quarto di vita è più veloce | leggere il pavimento, non solo il boss | le linee della stella cambiano colore (già tile propri: `T_FSTAR`) prima di bruciare | soglie, timer, danno sulla casella (il tile è già riconoscibile): ~100 B |

Vincoli: il generatore e i mostri stanno in memoria stretta (margine sotto `$8720`: ~2,3 KB il 15/11); le quattro meccaniche
insieme costano ~550 B stimati, da mettere in un modulo caricato con il piano del boss se il margine non basta (TODO M9).
**Da decidere con il committente**: se i boss di capitolo lasciano un bottino proprio, se la sala si chiude, i numeri (vita,
danno, tempi) dopo la taratura con i simulatori.

**Nel codice dal 19/11** (boss dei capitoli 1–3; il Lord of Ruin resta com'era): ogni meccanica è **codice del piano**
(`src/game/ovl_boss1..3.asm` + parti comuni `src/game/ovl_boss.inc`, nella coda di `GFX2`, `GFX4`, `GFX6`, copiato a `$C900`
entrando nel piano: [dungeon](dungeon.md#codice-del-piano-1911)); in GAME solo gli agganci (`ovp_tick`, `ovp_init`, `ovp_dmg` nel
colpo del PG, `ovp_tint` per il colore del boss in `build_sprites`). Numeri messi da me il 19/11 (dalla tabella sopra, **da provare
in gioco e da tarare**):

| Boss | Come è fatta | Scelte mie (19/11) |
|---|---|---|
| The Hollow Abbot | sotto **2/3** e **1/3** della vita: fermo 50 fotogrammi (1 s), lampeggia verde, bordo verde, suono del portale; poi 2 **Skeleton** (tipo 2) sulle caselle di pavimento accanto, svegli. Finché uno è vivo: +1 vita ogni **25** fotogrammi (verde a tratti), mai oltre il massimo. Al rientro le soglie già superate non si ripetono | nessun limite al numero di rigenerazioni; gli scheletri sono mostri normali del piano 5 |
| **Mother Stitch** (19/11, al posto del mugnaio) | tre **riti**: appena sveglia, sotto **2/3** e sotto **1/3** della vita; ognuno: ferma **50** fotogrammi, lampeggia bianco, bordo bianco, suono del portale, poi **2 feticci** (tipo 8 del file `GFX4`: nome "fetish", arancio) sulle caselle di pavimento accanto. I feticci sono **fermi** e non attaccano (stordimento rinnovato a ogni fotogramma, riconosciuti dal **tipo**: anche quelli rimessi dalla STASH dopo il portale), vita = vita massima del boss / **16**. **Protetta** finché un feticcio è in piedi: colpi del PG **dimezzati** (almeno 1), +1 vita ogni **25** fotogrammi, colore **giallo**. Caduto l'ultimo feticcio: **scoperta 100** fotogrammi (ferma, lampeggia azzurro, lampo del bordo, colpi ×2). I feticci danno **esperienza ma niente bottino** (committente, 19/11: `ovp_kill`). Al rientro i riti già fatti non si ripetono | colori senza verde (committente: si confonde con la palude); se attorno non c'è pavimento libero il rito non pianta niente e non c'è fase "scoperta" |
| Varok the Oathbreaker | sveglio, libero: allineato con il PG (scarto < 8 px su un asse) a **32–143 px**: avviso **25** fotogrammi (fermo, lampeggia giallo), poi carica a **4 px** per fotogramma nella direzione del PG (massimo 60 fotogrammi): contro un muro **stordito 100** fotogrammi (grigio, lampo del bordo), se raggiunge il PG **due attacchi** e si ferma; dopo ogni carica **75** fotogrammi di pausa. Lo scudo dimezza i colpi del PG (almeno 1), non da stordito | la carica non passa sugli spigoli (nessuno scivolamento); gli altri mostri non la fermano |

Test: `OVP-11`, `OVP-12`, `OVP-13` (regression). **Non provato a mano in gioco** (19/11): leggibilità degli avvisi, difficoltà.

### Concept dei comuni (in breve)
- Capitolo 2 (palude, mulino): **Drowned** (cadavere gonfio, lento e resistente; lascia una pozza che rallenta), **Bog
  Crawler** (scarabeo d'acqua, veloce, in branco), **Mire Witchling** (piccola strega, cugina dei Fallen; sputo a corto raggio).
- Capitolo 3 (accampamento bruciato): **Ash Ghoul** (soldato bruciato, danno nel tempo), **Bone Archer** (scheletro con
  l'arco: serve l'IA a distanza), **Hellhound** (cane nero, molto veloce, branchi da 3).
- Capitolo 4 (cittadella): **Imp** (piccolo demone, veloce, si teletrasporta vicino al PG), **Blood Knight** (soldato
  demone corazzato, lento), **Gargoyle** (demone di pietra, vola sopra acqua e fosse).
- (15/11, quarta famiglia per capitolo, disegnata con gli sprite): **Will-o'-Wisp** / Corpse Light (capitolo 2: fuoco fatuo,
  veloce, galleggia sull'acqua), **Frost Wight** / Wight Lord (capitolo 3: re morto di ghiaccio, lento, il tocco rallenta),
  **Cultist** / High Cultist (capitolo 4: servo incappucciato del Lord of Ruin, incantesimo a distanza). Righe concept nel
  bestiario con statistiche ricavate dalle sorelle del capitolo.

## Prima simulazione (11/11, `tools/simulators/chapters.py --fights 30`)

Ogni capitolo coi suoi mostri alla sua profondità globale (PG di riferimento, numeri provvisori dei concept): i comuni
si vincono sempre; i boss di capitolo con 4 pozioni della zona sono **sbilanciati**: The Hollow Abbot (profondità 6)
**13%** (troppo forte), The Miller of Bad Water (11, oggi Mother Stitch con le stesse statistiche) **97%**, Varok the Oathbreaker (16) **100%** (troppo deboli), Lord of
Ruin (20) 93%. Da tarare con `tools/simulators/fit_rules.py` (obiettivo dei boss: ~65–75%, `docs/wiki/balancing-guide.md`) prima di
disegnarli.

## Cosa serve per metterli nel gioco (stime, da verificare)

| Lavoro | Note |
|---|---|
| Sprite | **fatto il 15/11** (sezione "Nel gioco"): 4 famiglie + 4 forti + boss per capitolo, nei file dei temi del capitolo, con colori e nomi |
| Tipi di mostro nel codice | `N_MTYPES` = 9 e le tabelle sono per tipo: oggi i capitoli cambiano solo grafica, colore e nome (stesse statistiche); statistiche per capitolo = tabelle `mt_*` per capitolo (da caricare col tema, come i nomi) |
| IA nuove | veloce (c'è: `speed`), distanza (arcieri), evocazione (c'è per il boss finale), carica, teletrasporto: ognuna 50–200 B, da decidere quali |
| Boss di capitolo | mappa finale per capitolo (`FMAPn`), boss con nome fisso e regole proprie |
| Bilanciamento | `tools/simulators/chapters.py` per capitolo, `fit_rules.py` sulle nuove schede |
| Test | il controllo della tabella (`BEST-*`), il gioco = tabella per il capitolo attuale |
