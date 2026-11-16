# Nuovo sistema di combattimento — regole (bozza 2, 05/11)

Stato: **regole proposte**, niente è implementato. Ordine di lavoro deciso: (1) regole in questo documento,
(2) simulatore Python fedele alle regole e tarato, (3) assembly, verificato contro l'arena.
I numeri marcati *(da tarare)* sono il punto di partenza per il simulatore.

## 0. Decisioni prese
| Data | Decisione |
|---|---|
| 05/11 | Regole in stile **D&D** (d20, classe armatura, modificatori (valore − 10) / 2), caratteristiche in scala D&D |
| 05/11 | **Vita a 16 bit** (PG e mostri): serve per salire fino al livello 255 (Abisso) |
| 05/11 | **Danno di un colpo a 16 bit** in entrambe le direzioni (PG → mostri e mostri → PG): una sola routine di danno; il tiro dei dadi resta a 8 bit |
| 05/11 | Livello del PG previsto per il boss finale: **20**; oltre il 20 progressione "epica" lenta fino al 255 |
| 05/11 | Armatura: **solo classe armatura**, nessuna riduzione del danno |
| 05/11 | Anelli ribilanciati sulla scala D&D (sezione 7) |
| 05/11 | Danno a ogni colpo: tiro tra minimo e massimo (modificatori compresi), notazione a dadi nella tabella delle armi |
| 05/11 | Vita al livello 1: si decide con il simulatore (bilanciamento del piano 1) |
| 05/11 | Penetrazione: diventa "−N alla CA del bersaglio" (armi pesanti) |
| 05/11 | Il PG resta al livello 20 finché non sconfigge il boss finale (l'esperienza oltre la soglia del 21 non fa salire) |
| 05/11 | Abilità nuove Rage (9) e Frenzy (15): sì |
| 05/11 | Abisso: i mostri dipendono dal piano e crescono al ritmo del PG previsto per quel piano (livello = piano + 10); un PG più alto del previsto vince facilmente |
| 05/11 | Pozioni: rossa (debole, 25% della vita), gialla (intermedia, 40%), viola (potente, 60%) — percentuali da tarare |
| 05/11 | Differenza di livello: un mostro con livello ≤ livello del PG − **4** non dà esperienza né bottino |
| 05/11 | Bottino stile Diablo: livello oggetto + formula di probabilità (sezione 9b); set di oggetti unici se c'è memoria |

## 1. Vincoli del C64
- Caratteristiche, modificatori, bonus di attacco, CA, singolo dado: **8 bit** (bastano fino al livello 255).
- Vita e danno di un colpo (modificatori, critico, Smash, fattore del piano): **16 bit**. Esperienza: **24 bit**.
- Niente divisioni: spostamenti di bit e tabelle. Dadi: `rndrange` (esiste).
- Niente valori casuali da salvare: ciò che è casuale si rigenera dal seed (mostri) o si tira una volta e va
  nel byte bonus già esistente (oggetti).

## 2. Caratteristiche del PG (barbaro)
Tre caratteristiche (il barbaro non usa INT/SAG/CAR). Modificatore = (valore − 10) / 2, per difetto.

| | FOR forza | DES destrezza | COS costituzione |
|---|---|---|---|
| Iniziale | 16 (+3) | 13 (+1) | 15 (+2) |
| Aumenti 1–20 | +1 ai livelli 4, 8, 12, 16, 20 | +1 ai livelli 10, 18 | +1 ai livelli 6, 14 |
| Livello 20 | 21 (+5) | 15 (+2) | 17 (+3) |
| Oltre il 20 | +1 a una caratteristica ogni 4 livelli, a rotazione FOR → COS → DES | | |
| Livello 255 | 41 (+15) | 34 (+12) | 36 (+13) |

Effetti:
- **FOR**: per colpire e danno in mischia; difficoltà del Battle Cry.
- **DES**: classe armatura (limitata dall'armatura, sezione 4); critico allargato ai livelli alti (sezione 5).
- **COS**: vita a ogni livello.
- Anelli (sezione 7) sommano alla caratteristica prima del modificatore.

Si ricavano dal livello: nei salvataggi non c'è niente in più.

## 3. Progressione del PG

| Valore | Formula |
|---|---|
| Bonus di competenza (BC) | livelli 1–20: 2 + (livello − 1) / 4 (da +2 a +6); oltre: +1 ogni 4 livelli (al 255: +64) |
| Bonus di attacco (ATT) | BC + mod FOR + magia dell'arma |
| Vita massima | livello 1: 12 + mod COS; ogni livello in più: 7 (media del d12, fissa) + mod COS |
| Classe armatura (CA) | 10 + armatura + scudo + magia + mod DES (limitato dall'armatura) |

| Livello | FOR | DES | COS | BC | ATT (senza magia) | Vita |
|---|---|---|---|---|---|---|
| 1 | 16 | 13 | 15 | +2 | +5 | 14 |
| 5 | 17 | 13 | 15 | +3 | +6 | 50 |
| 10 | 18 | 14 | 16 | +4 | +8 | 100 |
| 15 | 19 | 14 | 17 | +5 | +9 | 150 |
| 20 | 21 | 15 | 17 | +6 | +11 | 200 |
| 50 | 24 | 17 | 19 | +13 | +20 | 523 |
| 100 | 28 | 21 | 24 | +26 | +35 | 1148 |
| 255 | 41 | 34 | 36 | +64 | +79 | 3750 |

*(da tarare)*: vita iniziale bassa (14) come in D&D: va provato se il piano 1 resta giocabile; alternativa
12 + COS (non il modificatore) al livello 1.

## 4. Armature e scudi
Armatura = bonus alla CA; tipo = limite al mod DES. Magia +N: +N alla CA.

| Oggetto | Tipo | CA | Limite mod DES |
|---|---|---|---|
| quilted armor | leggera | +1 | nessuno |
| leather armor | leggera | +2 | nessuno |
| chain mail | media | +4 | +2 |
| plate mail | pesante | +6 | 0 |
| full plate | pesante | +8 | 0 |
| buckler / round / kite / tower shield | scudo | +1 / +1 / +2 / +3 | – |

CA del PG con equipaggiamento tipico: livello 1 (leather) 13; livello 10 (chain mail, round shield +1) 18;
livello 20 (full plate +3, tower shield +2) 26. *(da tarare)*

## 5. Risoluzione di un attacco (PG e mostri, stessa regola)
1. **Per colpire**: d20 + ATT ≥ CA del bersaglio. 20 naturale colpisce sempre, 1 naturale manca sempre.
2. **Danno**: tiro tra minimo e massimo dell'arma (modificatori compresi: magia + mod FOR), es. long sword
   "1d8+FOR". La **penetrazione** sparisce come numero a sé (era contro l'armatura sottratta); se si vuole
   tenere, diventa "−N alla CA del bersaglio" per le armi pesanti *(da decidere con le armi)*.
3. **Critico**: 20 naturale (dal livello 17: 19–20; caratteristica del barbaro "Brutal Critical"):
   i dadi dell'arma si tirano due volte, i modificatori una sola.
4. **Vita**: si sottrae il danno (16 bit); a 0 il bersaglio muore.

Probabilità di colpire (%):

| ATT \ CA | 12 | 16 | 20 | 24 | 28 |
|---|---|---|---|---|---|
| +5 | 70 | 50 | 30 | 10 | 5 |
| +8 | 85 | 65 | 45 | 25 | 5 |
| +11 | 95 | 80 | 60 | 40 | 20 |

Obiettivo *(da tarare)*: al livello "giusto" per il piano il PG colpisce il 60–70% delle volte, i mostri il 40–55%.

## 6. Abilità del barbaro (livelli 3–15)
Lo Slash è l'attacco base (sempre disponibile, non è un'abilità). Proposta:

| Livello | Abilità | Effetto con le nuove regole |
|---|---|---|
| 3 | Whirlwind | un attacco contro ogni nemico attorno (tiro per colpire per ognuno) |
| 6 | Battle Cry | i nemici vicini fanno un tiro salvezza (d20 + salvezza del mostro ≥ 8 + BC + mod FOR); chi fallisce è stordito |
| 9 | Rage *(nuova)* | per 10 s: +2 danno a colpo, danno subito dimezzato |
| 12 | Smash | un attacco con vantaggio (2d20, si tiene il più alto) e dadi dell'arma raddoppiati |
| 15 | Frenzy *(nuova)* | per 6 s: un colpo in più a ogni Fire; in più, dopo aver colpito un mostro, velocità di movimento aumentata per un certo tempo *(da fare nel gioco)* |

Ricariche come oggi *(da tarare)*. Le abilità nuove costano codice, un tasto e un nome nell'HUD:
si decide dopo il simulatore se servono.

## 7. Anelli (ribilanciati sulla scala D&D)
Bonus a una caratteristica, tirato quando l'anello nasce (salvato nel byte bonus):

| Materiale | Dado | Bonus alla caratteristica | Effetto sul modificatore |
|---|---|---|---|
| copper ring | 1d4 | +1..4 | +0..2 |
| silver ring | 1d4+2 | +3..6 | +1..3 |
| gold ring | 1d6+4 | +5..10 | +2..5 |

Modificatori del nome *(da completare)*: "of might" FOR, "of agility" DES, "of vigor" COS, "of speed" velocità di movimento *(bonus da definire)*.
Molto rari (probabilità per oggetto: da definire). Un anello d'oro di forza al livello 20 porta FOR da 21 a
26–31: +2..5 a colpire e al danno. *(da tarare)*

## 8. Mostri
Blocco di statistiche per tipo, in stile D&D, più una crescita per piano. Per esemplare in RAM: vita (16 bit),
CA, danno; ATT e salvezza si calcolano al volo da tipo + piano.

| Campo (per tipo) | Esempio skeleton |
|---|---|
| Livello base del mostro (LM) | 1 |
| Vita: dadi | 2d8+4 (6..20) |
| CA | 13 |
| ATT | +4 |
| Danno | 1d6+2 |
| Salvezza (contro Battle Cry) | +1 |
| Velocità, esperienza, bottino, colore, tratti | come oggi |

Crescita per piano (P = piano − livello minimo del tipo) *(da tarare)*: vita +1 dado ogni piano, CA +1 ogni 3
piani, ATT +1 ogni 2 piani, danno +1 ogni 2 piani. Varianti forti e boss: +2 CA, +2 ATT, vita × 2..3.
Boss finale (piano 10): blocco proprio, obiettivo 60–70% di vittorie con il PG di livello 20 ed equipaggiamento
medio (misura con l'arena).
Abisso: crescita fino al piano `void_cap`, poi ferma (sezione 10).

Casualità (già così oggi, verificato): con le scale i mostri si rigenerano dal seed (vita piena, stessi valori);
con portale o morte restano esattamente come lasciati (STASH).

## 9. Esperienza
- 24 bit; curva: tabella dei livelli 1–20 come oggi, poi incremento lineare fino al 255 (≈ 16,7 milioni).
- Differenza di livello: un mostro con livello ≤ livello del PG − 4 non dà esperienza né bottino.

## 9b. Bottino: livello oggetto e probabilità (stile Diablo)
Ogni oggetto ha un **livello oggetto** (LO) e una **rarità** R (peso 1..255: comune 100, non comune 40, raro 10,
molto raro 2–3: anelli, unici 1). Ogni piano ha un **livello area** LA (proposta: 2 × piano, quindi 2..20;
nell'Abisso continua a salire, fino a `void_cap` per il bottino).
Peso di un oggetto: **w = R × g(LA − LO)**:
- LA < LO: **0** (l'oggetto non può ancora uscire: niente armi del piano 9 al piano 1);
- g sale nei primi livelli dopo LO (l'oggetto "compare"), ha un massimo, poi scende per gli oggetti superati;
- gli oggetti "da caccia" (rarità molto rara e unici) hanno g che non scende mai a 0: restano possibili, con
  probabilità bassa, anche oltre il livello 20 (motivo per continuare a cercare nell'Abisso).
Probabilità = w / somma dei w degli oggetti della stessa categoria (prima si sceglie la categoria come oggi).

Esempio di g (tabella di 32 byte, indice = LA − LO, oltre 31 vale l'ultimo) *(da tarare col simulatore)*:
`1 2 4 6 8 8 7 6 5 4 3 3 2 2 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1` (comuni: dopo ~20 livelli g = 0;
da caccia: minimo 1 per sempre).

Costo: per oggetto LO + R = 2 byte (oggi loot_level min/max: 2 byte, quindi a pari memoria); tabella g 32 B;
il calcolo (somma di ~10–15 prodotti 8×8 → 16 bit, poi un tiro) avviene solo quando esce un oggetto: trascurabile.
Il bonus magico +N continua a dipendere dal livello area.

### Set *(se c'è memoria)*
Oggetti unici con nome che appartengono a un set (arma, armatura, scudo, anello). Indossando i pezzi dello stesso
set si ottiene un bonus in più (es. 2 pezzi: +1 CA; 4 pezzi: +2 a colpire e +1 dado di danno *(da progettare)*).
Memoria stimata: per set 4 id + bonus ≈ 8 B; controllo in `recalc_stats` ≈ 40–60 B di codice. Fattibile con il
margine attuale; si decide dopo il nuovo combattimento.

## 10. Abisso (riepilogo, dettagli nel TODO)
- Morte: −10% dell'esperienza del livello attuale (mai sotto la soglia del livello); modalità normal / nightmare.
- `void_cap`: piano oltre il quale mostri e bottino smettono di crescere *(da tarare con il simulatore)*.

## 11. Memoria (stima)
| Dove | Prima | Dopo | Differenza |
|---|---|---|---|
| Variabili del PG | hpmax, s_str, s_dex, s_vit, s_def... | + BC, CA, mod ×3, hpmax 16 bit | ~+6 B |
| Mostri in RAM (32) | mhp, mhm 8 bit | 16 bit | +64 B (spazio libero a $9318) |
| Database mostri (9 tipi) | vita/armatura/danno min-max + crescita | dadi vita, CA, ATT, danno, salvezza | ~+3 B a tipo |
| Database armi | danno, velocità, penetrazione | dadi (2 B), velocità | ~+1 B a tipo |
| Salvataggio eroe | c_hp 8 bit, c_xp 16 bit | c_hp 16, c_xp 24, c_deaths 16, modalità | +5 B (124 liberi) |
| Codice | – | d20, dadi, confronti e sottrazioni a 16 bit, tiri salvezza | ~+300–500 B (margine 1146 + 625) |

## 11b. Simulatore
`tools/simulators/sim_rules.py` (motore `tools/simulators/rules.py`, parametri `data/rules.yaml`) applica queste regole con i tempi
del gioco (fotogrammi, ricariche, stordimento a ogni colpo, evocazioni del boss) e lo stesso bot dell'arena.
`python3 tools/simulators/sim_rules.py` produce `out/work/simulators/simulazione_regole.html` (circa 1 minuto).
Iterazione 1 (05/11): crescita per piano di CA (+1) e ATT (+1,6) dei mostri; curva di vita e danno per piano
cercata dal simulatore; vita al livello 1 = 12 + COS. Risultati e problemi nel report.

## 12. Decisioni aperte
1. Vita al livello 1: con il simulatore.
3. Tabella delle armi a dadi (dopo il simulatore).
4. Valori di rarità, livello area e tabella g (con il simulatore).
5. Set: elenco, pezzi e bonus (dopo il combattimento).
