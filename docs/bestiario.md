# Bestiario — mostri per capitolo (11/11)

Copyright © 2026 - Simone Caporale

Richiesta del committente (11/11): un **bestiario** con mostri dalle caratteristiche diverse, **uno per capitolo** (il
bestiario di un capitolo sostituisce quello del capitolo precedente); il **boss finale** (Lord of Ruin) va nel bestiario
dell'**ultimo capitolo**; il **capitolo 1 ha un boss nuovo**; concept per altri 3 capitoli (un boss, mostri comuni e
varianti potenziate come oggi). Modello: il database dei mostri di Diablo (DevilutionX).

**Stato**: la tabella `data/monsters/bestiary.tsv` è la **sorgente dei mostri** dall'11/11 (`tools/build/bestiary.py`: nel gioco
entrano le righe `implemented = yes`, out/work/db.asm identico a prima). Il gioco **non conosce ancora i capitoli** (TODO M9):
oggi usa i 9 mostri di sempre su 20 piani. Le altre righe sono **concept** (numeri provvisori, niente sprite).

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

| Capitolo (profondità) | Comuni | Forti (stesso sprite, altro colore) | Boss |
|---|---|---|---|
| 1 — Aldric's Crossing (1–5) | Fallen, Skeleton, Zombie, Demon (**oggi**) | Fallen Warchief, Skeleton King, Lich, Balrog (oggi) | **The Hollow Abbot** (nuovo) |
| 2 — Blackwater Mill (6–10) | Drowned, Bog Crawler, Mire Witchling | Drowned Hulk, Crawler Queen, Hag of the Mere | **The Miller of Blackwater** |
| 3 — The Last Camp (11–15) | Ash Ghoul, Bone Archer, Hellhound | Pyre Ghoul, Bone Marksman, Hellhound Alpha | **Varok the Oathbreaker** |
| 4 — The Throne of Ruin (16–20) | Imp, Blood Knight, Gargoyle | Imp Overseer, Blood Champion, Stone Gargoyle | **Lord of Ruin** (il boss finale di oggi, spostato qui) |
| Abisso (21–255) | tutti i bestiari precedenti, mescolati (proposta) | idem | boss con nome a ogni piano; nessun boss di capitolo (D-CAP-4) |

Nota: con il capitolo 1 di 5 piani (regola dell'11/11 sera: 5 piani per capitolo), **Demon e Balrog** (profondità minima 8 e 9) non comparirebbero più nel capitolo 1:
o passano al capitolo 2 (che oggi ha tre concept propri) o si abbassa la loro profondità. Da decidere con B11.

### Concept dei boss
- **The Hollow Abbot** (capitolo 1, mappa finale del capitolo): l'abate della cripta sotto Aldric's Crossing, uno scheletro
  in una tonaca marcia con un turibolo di fuoco verde. Al 66% e al 33% della vita rialza 2 scheletri. Immune al blocco.
- **The Miller of Blackwater** (capitolo 2): un mugnaio gigante posseduto; il mulino allagato è la mappa finale. Mena una
  macina legata a una catena (colpo ad area come Whirlwind) e chiama 2 Drowned.
- **Varok the Oathbreaker** (capitolo 3): il cavaliere che ha tradito l'ultimo accampamento. Carica (scatto verso il PG) e
  colpo di scudo (stordisce); chiama 2 Ash Ghoul.
- **Lord of Ruin** (capitolo 4): invariato (sala del trono, evocazioni a ondate, leva verso l'Abisso).

### Meccaniche dei boss di capitolo (decise il 15/11)

Richiesta del committente (15/11, TODO Z2): decidere quale meccanica di gioco ha ogni boss di capitolo. **Decise qui, non nel
codice**: oggi il boss di capitolo è il boss con nome del piano (statistiche del piano, l'IA di tutti: inseguimento e mischia)
con il **suo sprite** (15/11: `tools/build/monsters.py`, `ABBOT`, `MILLER`, `VAROK`; colori 14, 8, 7). Ogni meccanica insegna una
cosa sola e si legge dallo schermo (un avviso prima del colpo). Le stime sono a occhio, non misurate.

| Boss | Capitolo | Meccanica | Cosa insegna | Come si vede | Cosa serve nel codice (stima) |
|---|---|---|---|---|---|
| **The Hollow Abbot** | 1 | **Evoca i morti**: al 66% e al 33% della vita si ferma, agita il turibolo e fa alzare 2 scheletri. Finché uno scheletro evocato è vivo, l'abate **si rigenera** (1 punto vita ogni mezzo secondo) | scegliere il bersaglio: prima gli evocati | l'abate lampeggia verde per 1 s, bordo verde; gli scheletri compaiono accanto a lui | soglie di vita (2 byte), `spawn` di 2 mostri a piano avviato, rigenerazione a tempo: ~120 B |
| **The Miller of Blackwater** | 2 | **Il giro della macina**: ogni 4 s carica il colpo (1 s fermo), poi colpisce **tutto attorno a sé** entro 2 caselle (danno doppio); dopo il colpo resta **scoperto** 1,5 s (subisce danno doppio). Al 50% chiama 2 Drowned | entrare e uscire a tempo: colpire nella finestra, scappare durante la carica | il mugnaio lampeggia bianco mentre carica; un anello (lo sprite del Whirlwind) al colpo | stato a tempo (carica / colpo / scoperto), colpo ad area riusando `fz_*` del Whirlwind: ~150 B |
| **Varok the Oathbreaker** | 3 | **La carica**: quando è allineato con l'eroe (stessa riga o colonna) parte in linea retta a velocità doppia finché non urta; se urta **un muro** resta stordito 2 s (unico momento in cui lo scudo è giù). Fuori dallo stordimento lo **scudo** dimezza i danni | usare la sala: mettersi davanti a un muro e scansarsi | Varok lampeggia giallo e si ferma mezzo secondo prima di partire; da stordito è grigio | movimento in linea con velocità propria, urto, stato stordito, riduzione del danno: ~180 B |
| **Lord of Ruin** | 4 | **Il pentacolo brucia** (in più a quello che fa oggi): al 75%, 50% e 25% le linee della stella sul pavimento si accendono per 3 s e chi ci sta sopra prende danno; all'ultimo quarto di vita è più veloce | leggere il pavimento, non solo il boss | le linee della stella cambiano colore (già tile propri: `T_FSTAR`) prima di bruciare | soglie, timer, danno sulla casella (il tile è già riconoscibile): ~100 B |

Vincoli: il generatore e i mostri stanno in memoria stretta (margine sotto `$8720`: ~2,3 KB il 15/11); le quattro meccaniche
insieme costano ~550 B stimati, da mettere in un modulo caricato con il piano del boss se il margine non basta (TODO M9).
**Da decidere con il committente**: se i boss di capitolo lasciano un bottino proprio, se la sala si chiude, i numeri (vita,
danno, tempi) dopo la taratura con i simulatori.

### Concept dei comuni (in breve)
- Capitolo 2 (palude, mulino): **Drowned** (cadavere gonfio, lento e resistente; lascia una pozza che rallenta), **Bog
  Crawler** (scarabeo d'acqua, veloce, in branco), **Mire Witchling** (piccola strega, cugina dei Fallen; sputo a corto raggio).
- Capitolo 3 (accampamento bruciato): **Ash Ghoul** (soldato bruciato, danno nel tempo), **Bone Archer** (scheletro con
  l'arco: serve l'IA a distanza), **Hellhound** (cane nero, molto veloce, branchi da 3).
- Capitolo 4 (cittadella): **Imp** (piccolo demone, veloce, si teletrasporta vicino al PG), **Blood Knight** (soldato
  demone corazzato, lento), **Gargoyle** (demone di pietra, vola sopra acqua e fosse).

## Prima simulazione (11/11, `tools/simulators/chapters.py --fights 30`)

Ogni capitolo coi suoi mostri alla sua profondità globale (PG di riferimento, numeri provvisori dei concept): i comuni
si vincono sempre; i boss di capitolo con 4 pozioni della zona sono **sbilanciati**: The Hollow Abbot (profondità 6)
**13%** (troppo forte), The Miller of Blackwater (11) **97%**, Varok the Oathbreaker (16) **100%** (troppo deboli), Lord of
Ruin (20) 93%. Da tarare con `tools/simulators/fit_rules.py` (obiettivo dei boss: ~65–75%, `docs/balancing-guide.md`) prima di
disegnarli.

## Cosa serve per metterli nel gioco (stime, da verificare)

| Lavoro | Note |
|---|---|
| Sprite | 3 comuni + 1 boss per capitolo (le varianti forti cambiano solo colore). Oggi gli sprite dei mostri stanno nei file dei temi: un set per capitolo su disco, caricato col villaggio del capitolo |
| Tipi di mostro nel codice | oggi `N_MTYPES` = 9 e le tabelle sono per tipo: il bestiario del capitolo attuale sostituisce le righe (stesso numero di tipi per capitolo: 3–4 base + forti + boss), così la RAM non cresce |
| IA nuove | veloce (c'è: `speed`), distanza (arcieri), evocazione (c'è per il boss finale), carica, teletrasporto: ognuna 50–200 B, da decidere quali |
| Boss di capitolo | mappa finale per capitolo (`FMAPn`), boss con nome fisso e regole proprie |
| Bilanciamento | `tools/simulators/chapters.py` per capitolo, `fit_rules.py` sulle nuove schede |
| Test | il controllo della tabella (`BEST-*`), il gioco = tabella per il capitolo attuale |
