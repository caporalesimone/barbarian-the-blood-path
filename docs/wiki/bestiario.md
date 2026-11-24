# Bestiario — mostri per capitolo (11/11)

Copyright © 2026 - Simone Caporale

Richiesta del committente (11/11): un **bestiario** con mostri dalle caratteristiche diverse, **uno per capitolo** (il
bestiario di un capitolo sostituisce quello del capitolo precedente); il **boss finale** (Lord of Ruin) va nel bestiario
dell'**ultimo capitolo**; il **capitolo 1 ha un boss nuovo**; concept per altri 3 capitoli (un boss, mostri comuni e
varianti potenziate come oggi). Modello: il database dei mostri di Diablo (DevilutionX).

**Stato**: la tabella `data/monsters/bestiary.tsv` è il **database dei mostri** (`tools/build/bestiary.py`). **Dal 24/11 le
statistiche sono formule** (sezione "Statistiche: formule del bestiario" sotto): vita, CA, ATT, danno, salvezza ed esperienza
di ogni mostro a ogni piano escono dalla sua riga, e gioco, simulatori, manuale e test le leggono dallo stesso modulo
(`tools/build/mon_stats.py`). Le righe `implemented = yes` sono nel gioco: i 9 tipi del capitolo 1 (con il boss finale) e i
tipi 1–8 del **capitolo 2** (`own_stats: true` in `data/chapters.yaml`). **Dal 15/11 ogni capitolo ha nel gioco i suoi
mostri**: sprite, colore e nome delle 4 famiglie e delle 4 varianti forti del capitolo, e il boss del capitolo nel suo piano
del boss (sezione sotto). **L'IA non cambia** (il tipo *t* si muove come il tipo *t* del capitolo 1). I capitoli 3–4 usano le
statistiche del capitolo 1; le loro righe (e quelle dei boss di capitolo) sono concept.

## Nel gioco: i mostri dei capitoli (15/11)

Richiesta del committente (15/11): "disegna i mostri per capitolo oltre che i boss, poi falli includere nel gioco".

| Capitolo | Tipo 1 (stat. Fallen) | 2 (Skeleton) | 3 (Zombie) | 4 (Demon) | 5 (Fallen Warchief) | 6 (Skeleton King) | 7 (Lich) | 8 (Balrog) | Posto del boss (9) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Fallen (10) | Skeleton (1) | Zombie (13) | Demon (4) | Fallen Warchief (3) | Skeleton King (7) | Lich (14) | Balrog (8) | dungeon: Lord of Ruin (2); piano 5: The Hollow Abbot (14) |
| 2 | Drowned (3) | Bog Crawler (5) | Mire Witchling (4) | Will-o'-Wisp (13) | Drowned Hulk (14) | Crawler Queen (13) | Hag of the Mere (10) | Corpse Light (7) | dungeon: Lord of Ruin; piano 10: The Miller of Bad Water (8) |
| 3 | Ash Ghoul (12) | Bone Archer (1) | Hellhound (2) | Frost Wight (14) | Pyre Ghoul (8) | Bone Marksman (7) | Hellhound Alpha (10) | Wight Lord (3) | dungeon: Lord of Ruin; piano 15: Varok the Oathbreaker (7) |
| 4 | Imp (10) | Blood Knight (2) | Gargoyle (12) | Cultist (4) | Imp Overseer (8) | Blood Champion (4) | Stone Gargoyle (15) | High Cultist (7) | Lord of Ruin (2) (piano 20, sala del trono) |

Fra parentesi il colore C64 dello sprite. Il tipo decide IA ed evocazioni del boss finale (tipi base del piano 20: nel
capitolo 4 Imp, Blood Knight, Gargoyle, Cultist). Statistiche, primo piano, velocità e bottino vengono dalla riga del tipo: nel
capitolo 2 le sue righe (24/11, sezione sotto: tutti dal piano 6), nei capitoli 3–4 quelle del capitolo 1 (il tipo 3 è lento come lo zombie: Hellhound, Gargoyle). Il boss con nome dei piani normali resta
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

### Statistiche: formule del bestiario (24/11, `tools/build/mon_stats.py`)

Richiesta del committente (24/11): il bestiario come **database ufficiale** dei mostri, con **formule semplici** al posto dei
valori a un piano più una crescita comune nascosta nel codice. Proposta discussa il 24/11 (scelte del committente: calcolo sul
C64 con coefficienti, "modalità A"; capitoli 3–4 concept; Will-o'-Wisp e Corpse Light prima identici a prima, poi ritocco a parte).

**Il formato.** Nelle colonne `hp`, `ac`, `att`, `save`, `xp` una formula; in `dmg` i dadi più una formula (`1d4 + 1 + P`).
`floor` è il **primo piano** in cui il mostro compare (spawn) e da cui cresce. Variabili: `L` piano (profondità globale),
`P` = `L − FIRST` (piani dopo il primo, mai sotto 0), `FIRST` (la colonna `floor`), `C` capitolo del piano, `F` piano nel
capitolo (1–5). Operazioni `+ − * /`, parentesi, `min`, `max`, `round`; costanti con nome (anche formule) in
`data/monsters/constants.yaml` (oggi nessuna). Esempio: Skeleton `hp = 14 + 3.4*P`, `ac = 13 + P`, `dmg = 1d6 + 2 + P`.

**Vincolo**: nei piani in cui la riga si usa (capitolo 1: piani 1–20, perché i capitoli 3–4 usano i suoi tipi; gli altri: il
loro capitolo; il boss finale: il suo piano) la formula deve essere **lineare** in `L`. La build lo controlla e si ferma con
mostro, colonna e piano; si ferma anche per crescita negativa e valori fuori dai limiti (CA, ATT, danno, salvezza 0–255; vita
ed esperienza 0–65535).

**Sul C64** (`floor_types`, `src/game/combat.asm`): niente formule. La build fa di ogni formula due numeri, `A` = valore al
piano `FIRST` (arrotondato) e `B` = crescita per piano × 16, e il C64 entrando in un piano calcola per ogni tipo e statistica

    valore = A + ((B × P + 8) >> 4)          P = piano − FIRST (0 sotto il primo piano e per il boss finale)

con `mul16x8` (6 statistiche × 9 tipi: ~15.000 cicli stimati, una volta per piano; il caricamento dal disco dura secondi).
La pendenza ha la precisione di 1/16 per piano: `2.6` diventa 42/16 = 2,625 (il rapporto di `python3 tools/build/mon_stats.py`
stampa i valori veri per piano). Il danno del mostro resta: dadi + bonus, × `curve_dmg` del piano (`rules.yaml growth`).

**Tabelle** (`gen_db.py`): 20 campi per tipo (`fmin`, vita `hp_lo/hi/b`, `ac/ac_b`, `att/att_b`, dadi `dn/ds`, `dk/dk_b`,
`sv/sv_b`, esperienza `xp_lo/hi/bl/bh`, `mon_spd`, `mon_llb`) × 10 tipi, contigue in GAME a `mt_ch`, più `mt_z` (10 zeri:
parte alta delle statistiche a 8 bit). Ogni file del tema porta in coda i tipi 1–8 del suo capitolo (**160 B**, `GFX_STATS`;
prima 64 B), `gfx_install` li copia nei loro posti: le righe del capitolo 2 nel capitolo 2, quelle del capitolo 1 negli altri.
Per farci stare la coda (la cache del tema finisce sempre a `$F4E0` e ora comincia a `$EBD8`) `ring_stat` e `ui_icon` sono
passate dal segmento CORE a GAME (`ui.asm`). Costi misurati: GAME +41 B (margine del codice 1045 → 1004 B: sotto l'avviso di
1 KB), via le tabelle di crescita (`gr_*`, `cv_hp`, `mt_hpd2`, 111 B).

**Migrazione (24/11) senza ritarare.** Le formule dei capitoli 1–2 sono state ricavate dai valori che il gioco calcolava prima
(stessa aritmetica intera) scegliendo `A` e `B` con l'errore massimo più basso: scarto **≤ 3 punti vita**, **≤ 1** su ATT,
salvezza ed esperienza, **0** su CA e danno, a ogni piano. Le righe del capitolo 2 portano i numeri che il gioco usava (prima
venivano dal tipo del capitolo 1 nello stesso posto, con fattori): primo piano 6 (Will-o'-Wisp 8, Corpse Light 9, come prima),
dadi del danno del tipo del capitolo 1, velocità effettive. Will-o'-Wisp e Corpse Light ritoccati subito dopo (sotto). Le righe concept (capitoli 3–4, boss di capitolo) sono state
convertite con la crescita comune di prima, così `tools/simulators/chapters.py` dà gli stessi risultati.

Cose scoperte nella migrazione:
- **Piano 1**: la proposta del 24/11 diceva che al piano 1 la vita era × 1 invece di × 1,5. **Era sbagliato**: `cv_hp` era
  indicizzata con il piano e il suo × 1 era il piano 0 (villaggio). Nessun salto da allineare.
- **Lord of Ruin**: nel gioco ha vita media **507** (la scheda 45d10+90 = 338 × la curva del piano 20, 1,5), il simulatore lo
  escludeva dalla curva e usava 338. Ora la formula dice 507 e il simulatore la usa: i numeri del simulatore sul boss finale
  cambiano, il gioco no.

| Capitolo 2 | Primo piano | Vita | CA | ATT | Danno | Salv. | XP | Vel. |
|---|---|---|---|---|---|---|---|---|
| Drowned | 6 | `24 + 2.5*P` | `16 + P` | `5 + 0.7*P` | `1d4 + 6 + P` | `1 + 0.4*P` | `24 + 3.06*P` | 4 |
| Bog Crawler | 6 | `27 + 3.5*P` | `18 + P` | `7 + 0.7*P` | `1d6 + 7 + P` | `2 + 0.4*P` | `38 + 4.2*P` | 9 |
| Mire Witchling | 6 | `47 + 3.4*P` | `13 + P` | `6 + 0.7*P` | `1d8 + 6 + P` | `2 + 0.4*P` | `85 + 14.3*P` | 7 |
| Will-o'-Wisp | 6 | `46 + 3.4*P` | `14 + P` | `5 + 0.7*P` | `2d6 + P` | `3 + 0.25*P` | `70 + 21.5*P` | 9 |
| Drowned Hulk | 6 | `45 + 2.5*P` | `18 + P` | `7 + 0.7*P` | `1d8 + 7 + P` | `3 + 0.4*P` | `101 + 11.2*P` | 5 |
| Crawler Queen | 6 | `51 + 3.1*P` | `19 + P` | `8 + 0.75*P` | `1d10 + 6 + P` | `4 + 0.3*P` | `124 + 15.44*P` | 10 |
| Hag of the Mere | 6 | `74 + 3.5*P` | `16 + P` | `8 + 0.75*P` | `2d6 + 7 + P` | `5 + 0.3*P` | `211 + 42.2*P` | 8 |
| Corpse Light | 6 | `79 + 3.5*P` | `15 + P` | `6 + 0.75*P` | `2d8 + 1 + P` | `5 + 0.25*P` | `260 + 45*P` | 10 |

Velocità prima di `monster_speed_percent` (80%).

**Will-o'-Wisp e Corpse Light (24/11, scelta del committente: "prima identico, poi ritocco").** Nella migrazione copiavano Demon
e Balrog: Wisp solo dal piano 8, Corpse Light dal 9 e quasi senza crescita (vita 93 fissa). Ora tutti e due **dal piano 6**, con
crescita come i fratelli e gli **stessi valori di prima al piano 10** (Wisp: anche ai piani 8–9). I tipi base presenti a un piano
li conta `base_n` (`combat.asm`) da `mt_fmin` del file del tema, al posto di `maxtype_tab` (dal capitolo 1: il tipo 4 sempre dal
piano 8); `gen_db.py` controlla che i tipi base di ogni capitolo siano in ordine di primo piano. Effetto misurato (simulatore,
PG di riferimento, 400 combattimenti, boss del piano = media delle famiglie presenti come in `place_boss`): boss del piano
78 → 83% al piano 6, 91 → 93% al 7, invariato all'8–9; mostri base invariati (vita finale 90–96%). Arena al piano 6 (PG di
riferimento senza pozioni, 40 combattimenti): 3 Will-o'-Wisp vinti 100% (simulatore 100%), Corpse Light come boss **65%**
(simulatore 62%). Test `CHST-13`. Il **boss del capitolo 2** (tipo fisso, `chapter_bosses`) prende le statistiche
del suo tipo nel capitolo 2. **Simulatori**: `tools/simulators/rules.py` (`monster`, `coef_of`) usa gli stessi coefficienti e
gli stessi tipi per capitolo. `tools/simulators/fit_rules.py` tara solo la tabella dell'Abisso: le formule si scelgono a mano.
Test: `CHST-10..12` (regression, `tests/regression/chapstats`: tabelle dopo il cambio di capitolo e valori di `floor_types` =
formule per i tipi 1–9 a sei piani), `BEST-10..12`, `BAL-10`.

### IA del capitolo 2 (24/11)

**Fango degli annegati** (scelta mia, come le statistiche: il committente ha chiesto il capitolo 2 completo senza altre
decisioni; il bestiario diceva "lascia una pozza che rallenta"): con un **Drowned** (tipo 1) vivo e sveglio a meno di **24** pixel
su entrambi gli assi il PG si muove a **metà velocità** (fermo un fotogramma su due). Codice nel codice del piano degli arredi
del capitolo 2 (`ovl_decor.asm` con `DK_CHAP` 2, `OVJ_TICK`, coda di `GFX3`), in GAME solo la variabile `ovp_slow` e 12 B in
`update_player`; vale nei piani 6–9 (non nel piano del boss). Il simulatore non lo modella (non fa muovere il PG). Test `MUD-10`.
**Non fatto**: il volo dei Will-o'-Wisp sull'acqua (cambia le collisioni dei mostri in GAME: memoria e rischio), lo sputo della
Mire Witchling (attacco a distanza: progetto delle frecce non ancora nel codice).

**Resta** (TODO M9): statistiche proprie dei capitoli 3–4 (righe `implemented = yes` e `own_stats: true`, poi bilanciamento), IA nuove (distanza,
carica, teletrasporto, evocazione; nel capitolo 2 il volo dei Will-o'-Wisp), bilanciamento con i simulatori.

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
`final` = boss finale), `strong_of`, `name`, `floor` (**primo piano**, profondità globale 1..255), `level`, `hp`, `ac`,
`att`, `dmg` (dadi + formula), `save`, `xp` (formule dal 24/11), `speed`, `color` (C64), `loot_level_bonus`, `flags`
(`strong`, `final`, `stun_immune`, `chapter_boss`), `ai`, `sprite`, `implemented`, `notes`. Le statistiche dei concept sono
quelle di un mostro di oggi **cresciuto** alla stessa profondità, poi ritoccate per ruolo: resistente (più vita, più lento),
veloce (meno vita, velocità 10), picchiatore (più danno, meno CA); dal 24/11 scritte come formule con la crescita comune di
prima. Da tarare col simulatore (`tools/simulators/chapters.py`) quando i capitoli saranno nel codice.

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
| **Mother Stitch** (19/11, al posto del mugnaio) | tre **riti**: appena sveglia, sotto **2/3** e sotto **1/3** della vita; ognuno: ferma **50** fotogrammi, lampeggia bianco, bordo bianco, suono del portale, poi **2 feticci** (tipo 8 del file `GFX4`: nome "fetish", arancio) sulle caselle di pavimento accanto. I feticci sono **fermi** e non attaccano (stordimento rinnovato a ogni fotogramma, riconosciuti dal **tipo**: anche quelli rimessi dalla STASH dopo il portale), vita = vita massima del boss / **8** (24/11; / 16 fino al 23/11). **Protetta** finché un feticcio è in piedi: colpi del PG **dimezzati** (almeno 1), +1 vita ogni **25** fotogrammi, colore **giallo**. Caduto l'ultimo feticcio: **scoperta 75** fotogrammi (24/11; 100 fino al 23/11: ferma, lampeggia azzurro, lampo del bordo, colpi ×2). (24/11) **Tipo e vita fissi**: tipo del Lich (`CB2_TYPE`: nel capitolo 2 le statistiche di Hag of the Mere), **300** punti vita (`CB2_HP`). **Maledizione**: sveglia, fuori da riti e scoperta, ogni **400** fotogrammi lampeggia di rosso chiaro **40** fotogrammi (avviso, lampo del bordo), poi se il PG è entro **40** pixel su entrambi gli assi la cadenza dello Slash si allunga di 5/8 (×1,625) per **150** fotogrammi (`ovp_rate`, suono del colpo subito). **Feticci marci**: quelli ancora in piedi **500** fotogrammi dopo il rito diventano **annegati** (tipo 1, svegli, vita del tipo al piano): la protezione finisce senza scoperta. I feticci danno **esperienza ma niente bottino** (committente, 19/11: `ovp_kill`). Al rientro i riti già fatti non si ripetono | colori senza verde (committente: si confonde con la palude); se attorno non c'è pavimento libero il rito non pianta niente e non c'è fase "scoperta" |
| Varok the Oathbreaker | sveglio, libero: allineato con il PG (scarto < 8 px su un asse) a **32–143 px**: avviso **25** fotogrammi (fermo, lampeggia giallo), poi carica a **4 px** per fotogramma nella direzione del PG (massimo 60 fotogrammi): contro un muro **stordito 100** fotogrammi (grigio, lampo del bordo), se raggiunge il PG **due attacchi** e si ferma; dopo ogni carica **75** fotogrammi di pausa. Lo scudo dimezza i colpi del PG (almeno 1), non da stordito | la carica non passa sugli spigoli (nessuno scivolamento); gli altri mostri non la fermano |

Test: `OVP-11`, `OVP-12`, `OVP-13` (regression), `STITCH-10..11` (sanity: tipo e vita fissi, feticci marci, maledizione),
`ARENA-12`. **Non provato a mano in gioco** (19/11): leggibilità degli avvisi, difficoltà.

**(21/11, committente) Rabbia dell'abate** (`src/game/ovl_boss1.asm`, `ab_tick2`): sotto il **30%** della vita (1/4 + 1/32 +
1/64 = 29,7%) entra in rabbia (bordo rosso e suono, una volta): **attacca più spesso** (ricarica dell'attacco al massimo 28
fotogrammi invece di 45) e ogni **6 s** (il primo dopo 2 s) agita il **turibolo**: lampeggia di bianco per **1 s** (avviso), poi la
nube d'incenso (bordo grigio) toglie **1/8 della vita massima** al PG se è a meno di 40 pixel (2,5 caselle) su entrambi gli assi:
basta allontanarsi durante il lampeggio. Scelta mia (il committente ha lasciato libera la scelta dell'effetto); numeri da provare
in gioco. Le evocazioni del codice (2/3 e 1/3) restano; i sarcofagi a caso e la nube senza rabbia della proposta (sezione sotto)
non sono nel codice. Test: `BOSS1-10`, `BOSS1-11` (`tests/sanity/boss1/cases.py`). Nel simulatore dei boss (`boss_scripts.py`, `game`) dal 21/11: con le regole di **oggi** il PG di riferimento al livello 5 batte l'abate il **10%** delle volte (13% senza la rabbia, 22–27% con 1–2 livelli in più): l'abate del gioco di oggi è troppo duro e va tarato (vita, rigenerazione) prima di provarlo a mano.

**(22/11, D8 e D16) Abate tarato, proposta del 20/11 nel codice.** Tipo e vita **fissi** (`data/rules.yaml chapter_bosses`,
`CB1_TYPE` = Skeleton King, `CB1_HP` = 68: `ab_init` li mette al primo ingresso; al ritorno dal portale resta la vita lasciata).
Evocazioni a 2/3 e 1/3 con **uno** scheletro (prima 2: scelta del committente sulla taratura), rigenerazione ogni **50**
fotogrammi finché è vivo, **scheletri dalla cripta** (ogni 600 fotogrammi uno scheletro sveglio su una casella di pavimento a
3–9 caselle dal PG, al massimo 3 vivi: `ab_crypt`), **nube d'incenso** per tutto il combattimento (ogni 400 fotogrammi: 1 s di
lampeggio grigio chiaro, poi 3 colpi da 4 punti vita, uno al secondo, al PG entro 40 pixel: `ab_tick3`); la rabbia sotto il 30%
resta. Taratura (`sim_builds.py --fit-chapter abbot`, PG di riferimento di oggi, cintura da 4): vittorie **60%** al livello 5,
**77%** al 6, **85%** al 7. Con 2 scheletri per evocazione il 60% chiedeva un abate da ~31 punti vita (naturale 138); cripta e
nube contano poco nel simulatore, dove il combattimento dura meno di 12 s (in gioco il PG si muove: da provare a mano).
Test: `OVP-11`, `BOSS1-12`.

**(23/11) Verifica in arena e nuova taratura: `CB1_HP` = 123.** L'arena fa girare il codice del piano ([dungeon](dungeon.md)):
con 68 punti vita il PG di riferimento vinceva il **98/96/96%** ai livelli 5/6/7, contro 60/77/85% del simulatore. Confronto
evento per evento (durata, attacchi del boss, danni per fonte, colpi del PG per bersaglio) e quattro correzioni del simulatore
(`boss_scripts.py`, `data/rules_next.yaml bosses`): (1) gli evocati nascono accanto al boss e colpiscono la prima volta dopo
5–90 fotogrammi (`arrive`, mediana misurata 46); (2) la pausa dell'evocazione è uno **stordimento**: la ricarica dell'attacco del
boss si ferma (`stun_for`, come `mstun`); (3) **Slash colpisce tutta la sua area** (`slash_area` 0,7); (4) contro l'abate il PG
colpisce **lui**, non prima gli scheletri (`Abbot.adds_first = False`): gli scheletri gli nascono accanto e Slash li prende con
lui. Con queste il simulatore coincide con l'arena (100 punti vita: durata 473 contro 472 fotogrammi, 8,5 contro 8,4 attacchi
del boss, 60 contro 58 punti vita persi). Ritaratura `--fit-chapter`: **123 punti vita** → simulatore **59/74/81%**, arena
**68/81/84%** (150 combattimenti per livello, ±4 punti).

**(24/11) Mother Stitch: meccaniche nuove, taratura e arena.** Il committente ha chiesto il capitolo 2 completo senza altre
decisioni: la proposta del 20/11 è nel codice (feticci / 8, scoperta 1,5 s, maledizione, feticci marci; tabella sopra). Taratura
(`sim_builds.py --fit-chapter stitch`): **431** punti vita per il 60% al livello 10 (69/75/99% ai livelli 10/11/12). In arena il PG
di riferimento al livello 10 vinceva lo **0%** con 431 punti vita, con ogni bot: fermo (colpisce sempre lei, protetta: colpi
dimezzati e rigenerazione), che si avvicina (il più vicino è lei), e il bot nuovo `adds` (BOT 2: prima gli altri mostri, poi il
boss; aggira gli ostacoli). Differenze misurate con `adds`: stessa quota di colpi su di lei protetta (45% contro 40%), ma il
PG in arena fa il 45% di danno in meno al fotogramma (cammina fra feticci e boss, non schiva mai la maledizione, Slash prende quasi
sempre un solo mostro: `slash_area` di Mother Stitch 0,2 invece di 0,7, stima). Il salto al livello 12 (85–100% in arena) è
Smash, che prende boss e feticci insieme. **Scelta**: **300** punti vita, fra i due: simulatore **94/99/100%**, arena (bot
`adds`) **35/48/100%** ai livelli 10/11/12 (40 combattimenti per livello). Un giocatore vero sta in mezzo (si muove meglio del bot,
schiva la maledizione): **non verificato**, da provare a mano.

### Proposta del 20/11: più meccaniche e taratura con il simulatore (design, non nel codice)

Richiesta del committente (20/11): boss di capitolo più difficili (oggi i piani 5, 10, 15 sono i più facili, salvo l'abate),
con più di una meccanica ciascuno. Le meccaniche del codice (tabella sopra) e queste aggiunte sono **simulate** dal 20/11
(`tools/simulators/boss_scripts.py`, numeri in `data/rules_next.yaml` sezione `bosses`, misure con
`tools/simulators/sim_builds.py`). Il simulatore non si muove: un attacco annunciato è schivato con probabilità `skill` (0,5),
le cariche di Varok partono ogni 6 s (nel gioco solo quando è allineato).

| Boss | Già nel gioco | Proposte (20/11) | Cosa chiede al giocatore |
|---|---|---|---|
| The Hollow Abbot | 2 scheletri a 2/3 e 1/3, rigenerazione finché vivono | **scheletri che si alzano dai sarcofagi** in punti a caso della cripta ogni 12 s (massimo 3 vivi; camminano fino al PG; niente rigenerazione da questi); **nube d'incenso** ogni 8 s attorno all'abate (avviso 1 s, 3 colpi da 0,5 colpi del boss); rigenerazione dimezzata (1 ogni 50 fotogrammi) | uccidere prima gli evocati senza farsi circondare; uscire dalla nube |
| Mother Stitch | feticci fermi che la proteggono (colpi dimezzati, rigenerazione), scoperta 2 s quando cadono | **maledizione** ogni 8 s (avviso 0,8 s; se presa: cadenza del PG ×1,6 per 3 s); **feticcio che marcisce**: se resta in piedi 10 s diventa un annegato; feticci più robusti (vita /8 invece di /16), scoperta 1,5 s | abbattere i feticci in fretta, scansare la maledizione |
| Varok the Oathbreaker | carica (muro = stordito 2 s), scudo che dimezza i colpi | a metà vita **chiama 2 Ash Ghoul** e **getta lo scudo**: niente più dimezzamento, ma attacca 1,5 volte più spesso e carica ogni 5 s; prima della metà cariche ogni 7 s | due fasi: prima usare i muri, poi reggere l'urto |
| Lord of Ruin | ondate di evocazioni a 3/4, 1/2, 1/4 | **pentacolo che brucia** alle stesse soglie (già deciso il 15/11, non nel codice: 3 colpi da 0,5); **furia** nell'ultimo quarto (attacca 1,5 volte più spesso); **la decima** ogni 12 s (avviso 1,5 s: ruba il 6% della vita massima del PG e si cura del triplo) | leggere il pavimento, stare fuori dal cerchio della decima, chiudere in fretta |

Obiettivo (committente, 20/11): al livello del piano, con la cintura piena, vittorie ~60%; con 2 livelli in più 80–90% (il
farming come manopola della difficoltà). **Misure (100 combattimenti per caso)**: con le regole di **oggi** e le meccaniche del
codice il PG di riferimento vince l'abate il 13% (54% con 2 livelli in più), Mother Stitch il 100%, Varok il 39% (79%), il
boss finale il 100%: difficoltà disordinata. Con la **proposta** (`rules_next.yaml`, regole e mostri nuovi) e le meccaniche
nuove, vita e danno dei boss tarati sul profilo bilanciato (`--fit-bosses`: vita ×0,73 / ×1,66 / ×0,61 / ×0,5, danno ×0,8 /
×1 / ×0,65 / ×0,5): il bilanciato vince 55 / 59 / 59 / 52% al livello del piano e 100 / 99 / 95% con 2 livelli in più (il boss
finale è al livello massimo: niente farming). I profili specializzati restano sotto (forza 20–54%, costituzione 26–53%): è
lo stesso squilibrio delle caratteristiche (TODO B18). Limiti: niente movimento, schivata a probabilità fissa, statistiche dei
boss = boss con nome del piano (le schede proprie del bestiario non sono nel gioco).

### Arcieri e frecce (21/11, progetto: non nel codice)

Richiesta del committente: mostri arcieri (Bone Archer del capitolo 3, Cultist) e, più avanti, l'arco del PG. **Sprite nel
dungeon** (`bs_body`, `src/game/game.asm`): 0 eroe, 1 fendente, 2 effetto delle abilità, 3–7 mostri (al massimo 5 visibili),
nessun multiplexer (fino al 23/11 la barra in alto usava gli 8 sprite in un'altra fascia del raster; ora il bersaglio e' testo nell'HUD). **Una o due frecce insieme ci stanno**:
- prima freccia sullo **sprite 2** (l'effetto delle abilità dura pochi fotogrammi: con una freccia in volo l'effetto non si
  disegna, la freccia ha la precedenza);
- seconda freccia sullo **slot dei mostri più lontano** (lo sprite 7: con due frecce in volo si vedono al massimo 4 mostri);
- più di due frecce: non con gli sprite (servirebbero caratteri disegnati sullo schermo a passi di 8 pixel, o un multiplexer:
  costi alti con il doppio buffer). Proposta: **al massimo 2 frecce in volo** (un arciere aspetta che una si liberi).
Grafica: una freccia hires in 4 direzioni (o 8 con le diagonali): 4 × 64 B nella zona degli sprite forti del tema; logica:
posizione a 16 bit, passo di 3–4 pixel a fotogramma, fine su un muro (tile solido) o sul PG (colpo con il tiro per colpire
dell'arciere), ~150–250 B di codice stimati (GAME o codice del piano del capitolo). IA dell'arciere: resta a 3–6 caselle, tira
se allineato e se la linea è libera (stessa riga o colonna, come la carica di Varok), scappa se il PG si avvicina. Da decidere:
quanti arcieri per capitolo, danno della freccia, se la freccia si schiva muovendosi (sì: è uno sprite che viaggia).

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
Ruin (20) 93%. Da tarare (obiettivo dei boss: ~65–75%, `docs/wiki/balancing-guide.md`) prima di disegnarli.

## Cosa serve per metterli nel gioco (stime, da verificare)

| Lavoro | Note |
|---|---|
| Sprite | **fatto il 15/11** (sezione "Nel gioco"): 4 famiglie + 4 forti + boss per capitolo, nei file dei temi del capitolo, con colori e nomi |
| Tipi di mostro nel codice | `N_MTYPES` = 9, tabelle per tipo; **fatto il 24/11** per il capitolo 2: le statistiche arrivano col file del tema (formule del bestiario) |
| IA nuove | veloce (c'è: `speed`), distanza (arcieri), evocazione (c'è per il boss finale), carica, teletrasporto: ognuna 50–200 B, da decidere quali |
| Boss di capitolo | mappa finale per capitolo (`FMAPn`), boss con nome fisso e regole proprie |
| Bilanciamento | `tools/simulators/chapters.py` per capitolo, `sim_rules.py`, `sim_builds.py`, arena; le formule si ritoccano a mano |
| Test | il controllo della tabella (`BEST-*`), il gioco = tabella per il capitolo attuale |
