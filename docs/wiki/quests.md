# Quest, trama e premi — progetto (20/11)

**Pagina di progetto: niente di quello che c'è qui è ancora nel codice.** Riscritta il 20/11 dopo le decisioni del
committente (piano di lavoro del 20/11, domande D, O, E, Q, P, T, C). Ciò che è già nel gioco sta nelle pagine del codice:
NPC e "!" del villaggio in [villaggio](villaggio.md#abitanti-1718-11-concept), pagina Q in [interfaccia](interfaccia.md), file
stato nel salvataggio in [FORMATO_DATI](FORMATO_DATI.md), capitoli e profondità in [capitoli](capitoli.md). Il progetto degli oggetti
(affissi, unici, memoria) è in [oggetti](oggetti.md#progetto-affissi-unici-e-memoria-2011). L'analisi del 07/11 (tre villaggi su un
dungeon unico, mulino, Torvald, generatori su disco) è superata e resta solo nella storia di git.

**(22/11) Definizione completa di tutte le quest, con i testi in inglese e i premi**: `data/quests/next/quests.yaml` (12 passi della
catena, 15 accessorie, 6 modelli ripetibili, sorgenti degli unici; il gioco non lo legge ancora; test `QUESTDB-NEXT-10`). I premi
ancora da approvare sono marcati `proposal: true` (passo 2 *tam's amulet*; `a1.3`, `a3.4`: C6; *bottle tree* in `a2.1`; cintura a 8
in `a2.2`: P3). Come implementare il sistema e ogni quest: `QUEST-IMPLEMENTAZIONE.md` nella radice (documento usa e getta).

## Indice
1. [Regole fissate](#1-regole-fissate)
2. [Villaggi, NPC e boss](#2-villaggi-npc-e-boss)
3. [Trama: The Blood Tithe](#3-trama-the-blood-tithe)
4. [Il sistema](#4-il-sistema)
5. [Catena principale](#5-catena-principale)
6. [Quest accessorie e ripetibili](#6-quest-accessorie-e-ripetibili)
7. [Premi e oro](#7-premi-e-oro)
8. [Piano di lavoro](#8-piano-di-lavoro)

---

## 0. Decisioni del 22/11 (committente: risposte alle 13 domande con alternative)

Valgono sopra a quanto scritto nelle sezioni seguenti, dove c'è differenza.

| # | Tema | Decisione |
|---|---|---|
| D1 | Stato (32 B) | Il **baule della locanda esce dal blocco dell'eroe** (in coda al file di salvataggio, piano F7): il blocco libera 120 B per le quest e il futuro. **Se servisse spazio, le ripetibili si possono non salvare.** **Fatto il 22/11** (formato $CE): baule a `INN_AT` = `$FF80` e nel file dopo il blocco, stato `q_step`..`q_free` in fondo al blocco ([FORMATO_DATI](FORMATO_DATI.md)). |
| D2 | Testi | **Un file per capitolo** (+ uno per le ripetibili), a 5 bit, letto a `$EC00` come la scheda C: 36 blocchi, 5 voci di directory. |
| D3 | Codice del villaggio | **File `QGIV`** caricato quando si preme Fire su un NPC (22/11: file `qstg` a `CORE_AT`, non a `QBUF`, che era troppo piccolo; fa anche la pagina Q). Verificato il 22/11: il tasto Q (pagina delle quest, file `QST0` allo stesso indirizzo) funziona anche nel dungeon; `QGIV` serve solo nel villaggio. |
| D4 | Cancello del boss (Q14) | **Messaggio** "the way is sealed" sulla scala del piano 4 (9, 14, 19) se il passo "uccidi il boss" non è preso. |
| D5 | Finale | **Finale in due tempi.** Ucciso il Lord of Ruin, **al posto della leva compare un portale** che riporta in città (gratis, come una pergamena del portale). **Vicino al portale, nella piazza, compare l'NPC che dà il finale** (passo 12, the Penitent: epilogo). La quest si chiude con la possibilità di scendere nell'Abisso ("un'impresa a cui solo gli dei possono ambire"): chiusa la schermata della quest, **compare un portale nero nella piazza accanto a quello già aperto**. Il portale vecchio riporta nella sala del boss; **il portale nero resta per sempre** e porta tra l'Abisso e i villaggi. |
| D6 | Abisso | **Solo una modalità sfida senza trama**: si scende finché si riesce (classifica della profondità). |
| D7 | Premi | Approvati: *tam's amulet* al passo 2, oro + anello di rame magico in `a1.3`, pozioni viola + anello d'argento magico in `a3.4`, *bottle tree* in `a2.1`. **La cintura a 8 posti è premio del passo 6** (Mother Stitch: la ottiene sempre chi finisce il capitolo 2); `a2.2` dà oro e pozioni. |
| D8 | Boss dei capitoli | **Boss predefinito con statistiche tarate**, **livello del boss disegnato a mano** (come la sala del trono), **mostri casuali solo se il boss li evoca**. Corregge il difetto trovato con il bot (statistiche di un forte a caso). |
| D9 | Unici | **Unici della trama solo dalle quest.** Gli altri unici sono **casuali e solo dai boss**, ognuno da un sottoinsieme del suo capitolo: **boss del capitolo 50%**, **boss con nome di ogni piano 12,5%**. **Mai unici dai tesori normali** (`un_roll` della fase 6 va tolto dai tesori). **Fatto il 22/11** (`bu_roll`, [bottino](bottino.md)): sottoinsiemi di oggi da rivedere con D8. |
| D10 | Ripetibili | Se il premio estratto comprende l'oggetto magico, la riga dice solo **"magical item"**; l'oggetto si genera alla consegna **in base al capitolo** (più alto il capitolo, migliore l'oggetto). Le regole fini di generazione sono da decidere più avanti (TODO). |
| D11 | Mostri delle quest di caccia | (correzione del committente alla risposta) **Con la quest attiva il generatore crea sempre il mostro richiesto** quando l'eroe arriva nel piano: va modificato il generatore dei mostri. Vale per `a2.2`, `a3.2`, `r.hunt` e gli obiettivi B della catena. |
| D12 | Segni sopra gli NPC | **"!" giallo = quest da offrire, "!" verde = quest da ritirare** (stesso sprite; il verde ha la precedenza). (22/11, committente) Il verde sul prato non si vedeva: da ritirare è un **"?" giallo** (sprite `NPC_QMARK` in fondo alla zona 5 del MENU, `npc_q` = $97, bit 4; sulla minimappa il glifo `mq_gq`). (22/11, committente) Lo stesso "!" sta anche **sulla minimappa del villaggio**, sopra la casella di ogni NPC fisso con un segno (`mm_qmark`, [interfaccia](interfaccia.md)). |
| D13 | Ordine del lavoro | Prima lo stato nel salvataggio (D1), poi motore nel dungeon e `QGIV` nel villaggio, tutto sul **capitolo 1**; quando il sistema è stabile si estende a tutti i capitoli. |
| D14 | Tempi del disco (salvataggio da 4 blocchi) | Si accettano i tempi di oggi: limiti dei temi alzati (`theme2`, `theme4` a 1,4 s); il disco si ottimizza alla fine, prima della 2.0. Le ripetibili restano salvate. |
| D15 | Ingresso nel villaggio (5,08 s) | Si rimisura dopo il riordino dei file delle quest (D2); intanto `town_in` e `in1` a 5,2 s. |
| D16 | Boss dei capitoli | **Boss a fasi con meccaniche** (sotto una soglia di vita evoca, cambia attacco, si cura), codice nella coda del file del tema (`ovl_*`, come la sala del trono), modello in `tools/simulators/boss_scripts.py`. **Approvata (22/11)** la proposta del 20/11 (`new` di `data/rules_next.yaml`): un commit per boss, statistiche fisse tarate con il simulatore, verifica nell'arena. **Abate fatto il 22/11** ([bestiario](bestiario.md), uno scheletro per evocazione, vita fissa 68); restano Mother Stitch, Varok, Lord of Ruin. L'arena non fa ancora girare il codice del piano dei boss (TODO). |
| D17 | Unici del capitolo 1 | **Due unici nuovi** di livello 2-6 per i boss del capitolo 1 (proposta di nome, base, poteri, prezzo prima del commit), in fondo a `uniques.tsv`. **Fatto il 22/11** (approvati): warchief's hide (leather armor, CA +2, vita +6, GETHIT 1, 800) e bone king's ward (small shield, CA +2, DES +1, DUR +50, 700); il boss li tira a caso dal sottoinsieme, il legame con Fallen Warchief e Skeleton King è solo nel nome. |
| D18 | Prima versione del motore | Catena e accessorie del capitolo 1 (motore, `QGIV`, segni, pagina Q); **ripetibili dopo**, quando il resto è stabile. |
| D19 | Oggetti di quest "da baule" | Nel **baule del boss con nome** del piano giusto, con la quest attiva ("found: tam's amulet"). |

## 1. Regole fissate

| ID | Regola (committente, 20/11 salvo dove indicato) |
|---|---|
| Tipi | **Catena principale** (una per tutto il gioco, fino al Lord of Ruin), **accessorie** del capitolo (uniche, singole o a catena), **ripetibili** (offerte a caso dai vaganti, un insieme per capitolo) |
| Q14 | **La catena comanda la progressione**: il piano del boss del capitolo ha un cancello che si apre solo con il passo "uccidi il boss" attivo; il capitolo dopo si sblocca **consegnando** l'ultimo passo della catena del capitolo (non più con la sola uccisione del boss) |
| C1 | **Ritorno ai capitoli precedenti, parzialmente distruttivo**: dall'ingresso di ogni villaggio si torna al villaggio del capitolo precedente; uscendo da un capitolo il suo dungeon si azzera (stesse mappe dal seme, mostri e bauli di nuovo, mappa esplorata persa); il boss di un capitolo finito non ricompare; i salvataggi tengono solo i 5 piani del capitolo in corso |
| Q15 | Le **abilità** le sbloccano i passi della catena, **e** serve il livello minimo di oggi (3, 6, 9, 12, 15); le quest non danno livelli né punti statistica |
| Q1 | Accessorie date da **2–3 NPC fissi** per villaggio, nei loro posti della mappa, oltre a chi dà la catena |
| Q2, Q3 | Attive insieme: tutte le accessorie del capitolo (massimo 4; delle catene solo il passo corrente) e **2 ripetibili** |
| Q4 | Le ripetibili si consegnano a **qualunque vagante** del villaggio |
| Q5, Q14b | Cambiando capitolo una ripetibile non finita **si perde**; un'accessoria non finita **resta valida** (con C1 si può tornare) |
| Q6 | Ripetibili anche nell'Abisso (the Keeper e vaganti), con l'Abisso (TODO H3) |
| Q7 | Si può rinunciare solo alle ripetibili (pagina Q) |
| Q8 | Gli **oggetti di quest** sono contatori nella pagina Q, non stanno nello zaino |
| Q9 | Le accessorie di un capitolo si offrono dopo che il PG ha preso il primo passo della catena del capitolo |
| Q10 | La morte non tocca le quest (contatori compresi) |
| Q11 | Catena e accessorie si prendono subito con Fire; le ripetibili mostrano obiettivo e premio con **accept / decline** |
| Q12 | Zaino pieno alla consegna: la quest resta "da riscuotere" |
| Q13 | Uccisioni e oggetti di quest contano solo dopo aver preso la quest |
| Q16 | Pagina Q: una riga gialla con obiettivo e contatore + una riga con il premio, sopra il testo che scorre |
| 09/11 | **Versione 2.0** quando il quest system è pronto, mai prima |

---

## 2. Villaggi, NPC e boss

| Cap. | Villaggio | Com'è | Cura | Ingresso del sotterraneo | Piani | Boss e luogo |
|---|---|---|---|---|---|---|
| 1 | **Aldric's Hollow** | valle verde a sud: torrente con due ponti, piazza, chiesa, cimitero | fountain of saint aldric | la cripta nel cimitero | 1–4 stanze e corridoi | **The Hollow Abbot**, *The Crypt of the Abbot* (piano 5) |
| 2 | **Bad Water** | palafitte su un lago nero, passerelle, mangrovie, pali con teschi, tamburi; il pontile dalla riva è spezzato e il **traghetto** porta alle palafitte | the bottle tree | il cancello d'ossa della casa degli spiriti, con il grande idolo | 6–9 palude | **Mother Stitch, the Dollmaker**, *The Dollmaker's Isle* (piano 10) |
| 3 | **The Last Camp** | campo di guerra su tre terrazze di una montagna innevata | the great bonfire | la bocca di una grotta nella parete nord | 11–14 grotte | **Varok the Oathbreaker**, *The Broken Bastion* (piano 15) |
| 4 | **Ruin's Gate** | città in rovina attorno al cratere | the weeping angel | la saracinesca del corpo di guardia | 16–19 cittadella | **Lord of Ruin**, *The Throne of Ruin* (piano 20) |
| 5 | **The City of the Abyss** | isole di pietra sospese, ponti di luce | the heart of the abyss | la Bocca | Abisso (H3) | nessuno |

**NPC** (nomi approvati come prima stesura, T6):

| Villaggio | Catena | NPC fissi delle accessorie |
|---|---|---|
| Aldric's Hollow | **Father Osric** (chiesa) | Hilde (vedova), Grom (fabbro), the gravedigger (cimitero) |
| Bad Water | **Mama Sabine** (albero delle bottiglie) | Corbeau (traghettatore), Little Pip (passerelle), the drummer (tamburi) |
| The Last Camp | **Sergeant Brenna** (terrazza alta) | Chaplain Edric (grande falò), Quartermaster Ulf (tende e carri) |
| Ruin's Gate | **the Penitent** (angelo che piange) | the Scavenger (case sventrate), the Gatewarden (corpo di guardia) |
| City of the Abyss | — | the Keeper (solo ripetibili) |

Vincoli del codice di oggi (da rispettare nelle mappe): al massimo 5 NPC visibili insieme (sprite 3–7) e 2 "!" (sprite 1–2):
gli NPC fissi vanno messi lontani fra loro. **(21/11) Nel codice**: gli NPC fissi stanno nel villaggio con il loro nome, fermi,
ognuno al posto del vagante del suo settore ([villaggio](villaggio.md#abitanti-1718-11-concept), `tools/build/villages.py`
`FIXED`); nomi abbreviati per l'etichetta (15 caratteri): Quartermaster Ulf = "quartermaster". Le quest vere non sono ancora
collegate (oggi solo la segnaposto 1 di Hilde).

---

## 3. Trama: The Blood Tithe

Approvata il 20/11 (T1–T5). Testi in inglese da scrivere (intro `data/lore.txt`, TODO H4; quest).

**L'antefatto.** Cento inverni fa **Ruin**, a est, era la città più ricca della costa. Il suo re, per non morire, aprì una
porta sotto la città e strinse un patto con ciò che c'era sotto: il **Lord of Ruin**. La città bruciò e sprofondò in un
cratere di lava; sul bordo restò la cittadella del re, al centro si aprì l'**Abisso**. Un monaco guerriero, **Saint
Aldric**, chiuse il cratere con un sigillo di **quattro reliquie** (il suo **turibolo**, il suo **ago d'argento**, la
**spada del giuramento** e il suo **cuore**) e lungo la strada dalla valle al cratere fondò quattro santuari, uno per
reliquia, ognuno con un custode.

**La decima.** Il demone non poteva uscire, ma poteva parlare. A ogni custode offrì ciò che desiderava in cambio della
reliquia e del **sangue**: all'abate la vita senza fine, alla guaritrice il potere sulle anime, al cavaliere la vita dei
suoi uomini, ai guardiani della porta un posto alla sua tavola. Il sigillo si indebolì e le genti della strada pagano da
allora **la Decima**: ogni inverno ogni villaggio manda persone al cratere. Il cammino dei pellegrini è diventato la strada
dei carri: **the Blood Path** (il cammino rosso della mappa del mondo).
- **The Hollow Abbot** tiene il turibolo e sceglie chi parte dalla valle; morto da tempo, non ha smesso.
- **Mother Stitch** tiene l'ago d'argento: cuce l'anima dei prescelti dentro bambole e feticci; i drowned sono i prescelti
  caduti dai carri nel lago nero.
- **Varok the Oathbreaker** tiene la spada del giuramento, spezzata: scorta i carri sul passo; il Last Camp è ciò che
  resta della compagnia che ha rifiutato; i frost wight sono i loro morti nel gelo.
- **I cultisti di Ruin's Gate** consegnano la decima alla cittadella, dove il **Lord of Ruin** tiene il cuore del santo.

**L'eroe (T2).** Un **sopravvissuto alla decima**: preso da bambino, fuggito da un carro, cresciuto fra i barbari del nord,
torna a percorrere la strada al contrario. Proposta di dettaglio, da confermare con i testi (chiarimento C7): nato a
Aldric's Hollow, porta sul braccio il segno della decima (un'impronta rossa); fuggì dal carro sul passo del nord.

**Le abilità (T3).** Sono **memorie del nord**: le forme di guerra le aveva imparate dai barbari che lo crebbero; ogni
tappa della catena ne risveglia una.

| Cap. | Cosa scopre l'eroe | Fine del capitolo |
|---|---|---|
| 1 | la gente sparisce ogni inverno; Tam, il figlio di Hilde, è sceso nella cripta; il suo amuleto ha lo stesso segno del braccio dell'eroe | ucciso l'Abbot riprende il **turibolo**; i carri vanno a Bad Water |
| 2 | le bambole sono anime; Mama Sabine le libera all'albero delle bottiglie | uccisa Mother Stitch riprende l'**ago**; i carri salgono al passo |
| 3 | il Last Camp è la compagnia che ha detto no; il rotolo dei giuramenti prova il tradimento di Varok | ucciso Varok riprende la **spada**; il passo si apre sulla cenere |
| 4 | il diario del re di Ruin; l'ultimo carro dell'inverno è nella cittadella, con Tam vivo (T4, solo testo) | ucciso il Lord of Ruin il **cuore** torna al santo: il sigillo è rifatto, la decima finisce |
| 5 | il sigillo chiude il cratere, non ciò che sta sotto: dalla Bocca si scende nell'Abisso | gioco senza fine |

**Epilogo (T5, menu di vittoria, bozza):** "the four relics are home. the tithe is paid in full. but the seal closes the
crater, not what lies beneath it." Poi la leva e l'Abisso. Il menu di vittoria (oggi `ui_victory`, tre righe residenti)
diventa una pagina del file della quest finale, aperta con la routine della pagina Q; la leva (`ui_lever`) va rifatta.

---

## 4. Il sistema

### 4.1 Stati
`offerta` ("!") → `attiva` (contatore) → `da riscuotere` (obiettivo raggiunto, si torna dall'NPC) → `fatta`. Le ripetibili
dopo `fatta` tornano nel mazzo del capitolo.

### 4.2 Obiettivi

| Sigla | Obiettivo | Aggancio |
|---|---|---|
| K | uccidi N mostri di un tipo del capitolo | `kill_monster` |
| B | uccidi un boss con nome (ogni piano generato ne ha uno: `place_boss`) | `kill_monster` |
| C | uccidi il boss del capitolo | `chap_won` |
| R | raggiungi il piano N | `change_level` |
| I | trova N oggetti di quest (contatore): cadono da un tipo di mostro con probabilità 1/k o stanno in un baule di un piano | `roll_loot`, apertura del baule |
| G | consegna oro | Fire sull'NPC |
| P | uccidi N mostri qualsiasi nel piano N | `kill_monster` |
| V | Fire su un luogo del villaggio (idolo, falò, angelo) | `tile_trigger` |

### 4.3 Stato nell'eroe (stima 32 B, con il formato nuovo: [oggetti](oggetti.md#progetto-affissi-unici-e-memoria-2011))
- **Catena**: un **contatore** dei passi fatti (0..12) + **1 bit** "obiettivo raggiunto, da consegnare"; da questo si
  ricavano abilità, gradini del borsello e testo. Progresso del passo: 1 byte.
- **Accessorie**: bitmap "fatta" (2 B) + 4 slot attivi (id, contatore).
- **Ripetibili**: 2 slot (modello e parametro, contatore, premio) + l'oggetto premio preparato nel dungeon (7 B l'uno).
- `c_qst` (maschera di 8 bit del concept): non più usato dal 22/11.
- (22/11, formato $CE) **Fatto**: campi `q_step`, `q_flag`, `q_cnt`, `q_sdone`, `q_side`, `q_rep`, `q_item` ([FORMATO_DATI](FORMATO_DATI.md)).

### 4.4 Motore residente (22/11, `src/game/qengine.asm`)
Le quest **non ripetibili** hanno un numero nel gioco (QID): 1..12 i passi della catena, 13..27 le accessorie nell'ordine di
`quests.yaml` (a1.1 = 13). `tools/build/gen_qdata.py` scrive `out/work/qtab.inc`: per ogni QID tipo dell'obiettivo e capitolo
(`qt_ty`), parametri (`qt_p1`, `qt_p2`: tipo di mostro, piani, soglia della caduta 256/k), quantità (`qt_n`), oggetto di quest
(`qt_it`, nomi `qi_*` per "found: ..."). Il tipo di mostro di un capitolo è la sua posizione nel bestiario (base, poi forti).

Posti delle quest **prese**: la catena (passo `q_step` + 1 se `q_flag` bit 0 e non ancora raggiunto) e le 4 accessorie di
`q_side` (id 1..15, bit 7 = raggiunta). Eventi:

| Evento | Aggancio | Obiettivi |
|---|---|---|
| uccisione (`q_kill`) | `kill_monster`, prima del bottino | K (tipo del capitolo corrente), B (boss con nome nei piani p1..p2), P (piani p1..p2), oggetto da mostro (tipo, `rand` < soglia) |
| baule (`q_chest`) | prima apertura del baule del boss con nome (`chest_open`, dopo `bu_roll`) | oggetto da baule nei piani p1..p2 (D19) |
| boss del capitolo (`q_cboss`) | `chap_won` e boss finale | C |

Raggiunta la quantità: catena `q_flag` bit 1, accessoria bit 7 dell'id; nella barra "quest complete" (o "found: <oggetto>")
per ~3 s (`q_msg`, `loc_check`), lampo e suono. **D11** (`q_spawn`, `load_location` dopo `place_boss`): con una quest K o
"oggetto da mostro" presa e non raggiunta, se nel piano (del capitolo della quest, non il piano del boss del capitolo) non c'è
un mostro del tipo, il primo mostro che non è il boss lo diventa. **D4** (`q_gate`): la scala verso il piano del boss del
capitolo è chiusa ("the way is sealed") finché il passo 3c non è preso o consegnato; acceso (`QGATE` = 1) **solo nel capitolo 1**
(`QGATE_CH`): `QGIV` dà le quest di tutti i capitoli, ma i tipi di mostro dei capitoli 2-4 sono da verificare (D13). Costo: ~870 B di GAME (codice ~470, tabelle e nomi ~270, barra).
Test: `QENG-10`..`14`.

### 4.5 Modulo del villaggio `QGIV` (22/11, `src/qgiv.asm`)
Fire accanto a un **NPC fisso** del villaggio (numero k di `villages.FIXED`: nel capitolo 1 0 hilde, 1 father osric, 2 grom, 3
the gravedigger) → `q_talk` (GAME) legge il file **`qstg`** a `CORE_AT` (`$E000`: copre il segmento CORE, che `ui_exit`
rilegge all'uscita a schermo nero, prima di ridisegnare il gioco (23/11: prima lo rileggeva `main_loop` con il gioco già a
schermo, un fotogramma di ~1,7 s; test `QGIV-19`); per questo il modulo usa `ui_begin0`) e lo esegue. I vaganti restano quelli del concept (D18: ripetibili dopo).
1. **Consegna** (`q_tin`, nel modulo MENU: `src/menu/q_who.asm`, `MENU_QTIN`): passo della catena raggiunto e ritirato da
   quell'NPC, o accessoria raggiunta, o accessoria con obiettivo G presa ("give 300 gold?", solo l'oro addosso). Se il premio
   non ha posto (zaino per unico e oggetto, cintura per le pozioni: Q12) "no room in your pack or belt" e la quest resta.
   Premio (4 B per quest, `qgiv_rw.inc`): oro, unico (base `un_base`, suffisso $80+u), oggetto magico della base (`af_gen` con
   `af_m` = 1, livello 5 × capitolo; `$ff` = qualsiasi, vedi sotto), pozioni, gettone respec, gradino del borsello (`q_flag` bit 4-7). Poi `q_step` + 1
   (catena) o il bit in `q_sdone` (accessoria) e il testo "done" con la riga del premio.
2. **Offerta** (`q_offer`, `MENU_QOFFER`): il passo `q_step` + 1 se quell'NPC lo dà, oppure un'accessoria del capitolo (dopo il
   primo passo della catena del capitolo, non fatta, non presa, con la precedente fatta se serve, con un posto libero in
   `q_side`). La quest è **presa subito** (Q11) e si mostrano titolo, obiettivo in giallo (con "0/N"), testo e premio.
3. Altrimenti "nothing for you now."

Testi: un file per capitolo **`QTX1`..`QTX4`** a 5 bit (`gen_qdata.py`, letto a `QTX` = `$EC00`; 1879-2204 B, al massimo 2272):
n, n × (QID-1, indirizzo), poi per ogni quest titolo, obiettivo (fino a "{n}"), contatore sì/no, righe del testo, della
consegna e del premio (36 colonne). Il testo scorre con W/S o con il joystick, una riga per volta. (22/11, prova del committente) Fra una riga e l'altra c'è una
riga vuota: nel riquadro di 12 righe se ne vedono 6 (`QG_VIS`); al posto di "up" e "more" c'è la **barra di scorrimento**
sulla cornice destra, come nelle liste (`qg_bar`: `CH_THUMB` grigio chiaro, lunghezza 12 × 6 / righe, solo se il testo non
sta nella finestra). Il premio resta a righe consecutive. File su disco in fondo: `qstg` 6 blocchi, `qtx1-4`
35 blocchi. **Segni (D12)**: `q_marks` (`src/menu/q_who.asm`, `MENU_QMARK`, all'ingresso nel villaggio dopo `npc_fix` e all'uscita da
`QGIV`) mette in `npc_q` degli NPC fissi `$87` (giallo: una quest da dare), `$85` (verde: una da ritirare) o 0; `npc_offer`
ne ricava il colore del "!" (`npc_bmark`, bianco quando è in alto). I vaganti del concept restano gialli.
**Pagina Q** (22/11): il tasto Q apre lo stesso modulo con `q_k` = `$ff` (`ui_quest` → `q_load`): elenco delle quest prese
(titolo dal file del capitolo corrente, "a quest of chapter N" per una di un altro capitolo; stato "n/N" o "done"), Fire = il
testo dell'offerta con il contatore vero. Anche nel sotterraneo (QTX copre la coda del tema, come la scheda C; i segni si
rifanno solo nel villaggio). Il concept del 17-18/11 (`QST0`..`QST8`, `src/qpage.asm`, `gen_quests.py`, `data/quests.yaml`,
le quest dei vaganti) è stato tolto.
(23/11) **Abilità dalla catena (Q15)**: `sk_ok` (GAME) vuole il livello (`sk_req`) e `q_step` >= il passo che dà l'abilità
(`sk_qs`, scritta da `gen_qdata.py` dai premi `skill:` della catena: Whirlwind 2, Battle Cry 4, Rage 6, Smash 8, Frenzy 9); la
usano `sel_skill`, `buff_act` e l'HUD. **Sblocco del capitolo alla consegna**: in `qg_give`, consegnato il passo 3c con *c* <=
`QGATE_CH` (i capitoli con il cancello D4, che garantisce il passo preso prima del boss) → `c_unl` = *c*+1; `chap_won` non
sblocca più quei capitoli. Test: `QGIV-10`..`19`, `QREW-10`..`12`. (23/11) **Oggetto "qualsiasi"** (`$ff`, passo 11): categoria a caso fra arma,
armatura, scudo e anello, la base migliore fino al livello oggetto 5 × capitolo (`lt_scan`, come i bauli), poi magico come
l'oggetto di una base (`af_gen`, `af_m` = 1); test `QREW-13`. **Da fare**: cintura a 8,
cancello D4 nei capitoli 2-4 (`QGATE_CH`: con il cancello anche lo sblocco alla consegna), ripetibili (D18).

---

## 5. Catena principale

12 passi, 3 per capitolo. Livello = piano ([bilanciamento](BILANCIAMENTO.md)). Oro e oggetti: prima stesura, da tarare
(sezione 7). Testi: bozze in inglese.

| # | Titolo | NPC | Obiettivo | Premio |
|---|---|---|---|---|
| 1 | **a sword for the crypt** | Father Osric | K: 8 fallen | oro, *osric's cudgel* (unico) |
| 2 | **the widow's son** | Hilde → Osric | I: l'amuleto di Tam (baule del piano 3) | oro, **Whirlwind** |
| 3 | **the abbot's censer** | Father Osric | C: The Hollow Abbot (piano 5) | oro, borsello **550** (22/11, committente), pozioni, il turibolo |
| 4 | **the silent village** | Mama Sabine | K: 12 drowned | oro, **Battle Cry** |
| 5 | **dolls with names** | Mama Sabine | I: 5 bambole cucite (dalle mire witchling) | oro, *doll-hide* (unico) |
| 6 | **the silver needle** | Mama Sabine | C: Mother Stitch (piano 10) | oro, borsello **800**, pozioni, **Rage**, l'ago |
| 7 | **cold fires** | Sergeant Brenna | K: 10 frost wight | oro, pozioni |
| 8 | **the oath roll** | Chaplain Edric → Brenna | I: il rotolo dei giuramenti (baule del piano 14) | oro, **Smash** |
| 9 | **the oathbreaker** | Sergeant Brenna | C: Varok the Oathbreaker (piano 15) | oro, borsello **1050**, *bastion door* (unico), **Frenzy**, la spada |
| 10 | **where the carts end** | the Penitent | K: 12 cultist | oro, pozioni |
| 11 | **the last cart** | the Penitent | B: il boss con nome del piano 19 (il carceriere) | oro, un oggetto magico del piano |
| 12 | **the saint's heart** | the Penitent | C: Lord of Ruin (piano 20) | borsello **1300**, gettone respec (c'è già), *aldric's heart* (unico), vittoria e Abisso |

Abilità e piani (Q15): Whirlwind (livello 3) al passo 2 (piano 3), Battle Cry (6) al 4 (piani 6–7), Rage (9) al 6 (piano 10),
Smash (12) all'8 (piani 13–14), Frenzy (15) al 9 (piano 15): da verificare col simulatore. (23/11) Nel codice: `sk_qs`, `sk_ok`
(sezione 4.5).

---

## 6. Quest accessorie e ripetibili

### 6.1 Accessorie (⛓ = a catena)

| # | Titolo | NPC | Obiettivo | Premio |
|---|---|---|---|---|
| A1.1 ⛓ | grom's old hammer | Grom | I: il martello (baule dei piani 2–4) | sword magica |
| A1.2 ⛓ | iron for the forge | Grom | G: 300 oro | *gravedigger* (unico) |
| A1.3 | a name on the stone | the gravedigger | B: un boss con nome dei piani 1–4 | **da decidere (C6)** |
| A1.4 | candles for the saint | the gravedigger | P: 10 mostri nel piano 4 | pozioni, oro |
| A2.1 ⛓ | marsh glass | the drummer | I: 6 vetri di palude (dai bog crawler) | pozioni |
| A2.2 ⛓ | bottles for the tree | the drummer | K: 2 crawler queen | candidata per la **cintura a 8** (P3: col simulatore) |
| A2.3 | lanterns on the water | Little Pip | K: 8 will-o'-wisp | **gettone respec** |
| A2.4 | corbeau's toll | Corbeau | G: 600 oro | *ferryman's oar* (unico) |
| A3.1 ⛓ | the frozen scout | Quartermaster Ulf | I: la mappa dello scout (baule del piano 11) | pozioni, oro |
| A3.2 ⛓ | the wight lord's crown | Quartermaster Ulf | K: 2 wight lord | *frostbound* (unico) |
| A3.3 | hounds at the pass | Sergeant Brenna | K: 14 hellhound | *hound's tooth* (unico) |
| A3.4 | the bonfire vigil | Chaplain Edric | V+G: 1000 oro al falò | **da decidere (C6)** |
| A4.1 ⛓ | the king's diary | the Scavenger | I: 3 pagine (bauli dei piani 16, 17, 18) | gold ring magico; la storia del re |
| A4.2 | stone that walks | the Gatewarden | K: 3 stone gargoyle | *angel's tear* (unico) |
| A4.3 | tears of the angel | the Penitent | P: 15 mostri nel piano 18 | **gettone respec**, pozioni |

### 6.2 Ripetibili
Le offrono i vaganti con il "!" (1/4 per vagante, come oggi), pescando un modello del capitolo e i parametri a caso.

| Modello | Obiettivo | Parametri |
|---|---|---|
| cull | K: N di un tipo base del capitolo | tipo 1–4, N 8–15 |
| hunt | K: N varianti forti | tipo 5–8, N 2–4 |
| bounty | B: un boss con nome qualsiasi del capitolo | — |
| recovery | I: N oggetti di quest qualsiasi ("lost goods") | N 3–6 |
| patrol | P: N mostri nel piano N | piano 1–4 del capitolo, N 10–20 |
| offering | G: oro (capitoli 2–5), premio in pozioni | quantità del capitolo |

Titoli per capitolo (al massimo 24 caratteri): 1 thin the fallen, bones in the crypt, the warchief's guard, a name on the
stone, grave goods, the gravedigger's watch · 2 lay the drowned, beetles in the reeds, the hag of the mere, a doll with a
name, sunken bundles, candles for the drowned · 3 ash and frost, arrows in the dark, the pack alpha, an oath to settle,
frozen supplies, the snow cave watch · 4 hoods and blades, wings of stone, the champion's guard, a high hood, relics of
ruin, the citadel watch.

---

## 7. Premi e oro

| Premio | Regola |
|---|---|
| Oro della catena (P4) | un passo ≈ metà / due terzi dell'oro di un piano del suo capitolo; numeri dal simulatore dell'oro |
| Ripetibili (P5) | oro (~1/4 di un piano del capitolo) + 1–2 pozioni + oggetto magico del capitolo con probabilità 1/4; mai respec, unici o premi speciali |
| Gettoni respec (P1) | A2.3, A4.3 + boss finale (+ i rari dei bauli dell'Abisso) |
| Borsello (P2) | (22/11, committente, nel codice) **300 all'inizio, +250 a ogni boss di capitolo**: 550 (passo 3), 800 (passo 6), 1050 (passo 9), 1300 (passo 12); `balance.yaml player.purse`, `gold_cap` in GAME (gradino = `q_flag` bit 4-7, uno per premio "purse" consegnato): tetto della raccolta (`add_gold16`) e delle vendite (`purse_room`; 23/11: rifiuto con "your purse is full."). Riga del premio: "purse: upgrade ¤550" (prima "a purse of N", che sembrava oro). Analisi: `sim_purse.py` (PG medio = metà dell'incasso massimo: ~0,4 ritorni in città per piano dovuti al tetto nel capitolo 1, ~0,7 nei capitoli 2-4). **Effetto collaterale da decidere**: un oggetto che vale più del tetto (vendita a 1/4: prezzo > 4 × tetto) non si vende |
| Cintura a 8 (P3) | premio importante, fine capitolo 2 o inizio capitolo 3: quest e momento decisi col simulatore del piano intero (`sim_floor.py`, 20/11: con 4 posti 0,25–0,39 ritorni in città per piano dal piano 3 al 14, con 8 quasi nessuno; [bilanciamento](BILANCIAMENTO.md)). 8 posti = 4 slot da 2 pozioni, tasti 1–4; il tasto beve la prima fila, la seconda sale (08/11) |
| Quest che chiedono oro (P6) | iron for the forge, corbeau's toll, the bonfire vigil, modello "offering" |
| Oro di riferimento | simulatore dell'oro del 20/11 ([bilanciamento](BILANCIAMENTO.md)): ~220 oro per piano nel capitolo 1, ~735 nel 2, ~1055 nel 3, ~1540 nel 4 (oro trovato, piani normali) |

---

## 8. Piano di lavoro

Ordine deciso il 20/11: prima oggetti ed economia, poi quest. Ogni passo un commit con build verde.

| Fase | Contenuto | Stato |
|---|---|---|
| 1 | documenti (questa pagina); simulatore dell'oro nuovo; database degli oggetti nei dati e modello nei simulatori; vendita a un quarto; taratura sulla carta (da approvare); testi dell'intro e del capitolo 1 (da approvare); piano della memoria (F7, fatto: [oggetti](oggetti.md#progetto-affissi-unici-e-memoria-2011)) | in corso |
| **G1** | cancello: architettura di memoria approvata e C1 deciso (20/11) | **passato** |
| 2 | oggetti nel gioco, un commit per strato: formato nuovo dei salvataggi (5 piani, baule della locanda sotto l'I/O, bauli rigenerati, cintura a 8); basi nuove e requisiti; affissi; interfaccia (variante D); meccaniche semplici e unici; negozi con merce preparata nel dungeon, bauli epici | da fare |
| **G2** | cancello: dettagli del cancello del boss e dello sblocco con la catena (C3); pagina Q riprogettata (`QST0` è pieno) | da chiarire |
| 3 | motore delle quest (stato, agganci, consegna, abilità, borsello); NPC fissi; cancello del boss; ritorno ai villaggi (C1, ~60 B) | da fare |
| **G3** | cancello: lista degli unici per finestre (C5), premi di A1.3 e A3.4 (C6), testo dell'intro (C7) | da chiarire |
| 4 | contenuti (catena, accessorie, ripetibili), menu di vittoria e leva, taratura finale, manuale ("Quests", E6), help, test → **versione 2.0** | da fare |
| dopo la 2.0 | furto di vita e spine, oggetti e quest dell'Abisso (H3), due armi (G7) | — |

**Chiarimenti in coda:** C3 cancello del boss (scala del piano 4 rifiutata con un messaggio o cancello disegnato; la
vittoria del capitolo 4 dopo aver parlato con the Penitent?); C4 oggetti magici generati nel villaggio (negozi e premi delle
ripetibili, se la merce preparata nel dungeon non basta); C5 unici per finestre di livello; C6 premi di A1.3 e A3.4; C7
testo dell'intro e dettagli dell'eroe.

**Test previsti:** catena con poke dello stato (prendi, uccidi, raggiungi, consegna), una ripetibile per capitolo, zaino pieno,
salvataggio e ricarica, cancello del boss e sblocco del capitolo, ritorno al villaggio precedente.
