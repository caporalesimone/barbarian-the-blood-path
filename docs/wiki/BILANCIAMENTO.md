# Bilanciamento completo (proposta del 05/11, ritaratura del 06/11 sera)

> **Stato (06/11 sera)**: il sistema è implementato nel gioco; questo documento resta il riferimento del
> progetto. La ritaratura dopo l'implementazione è nella sezione 10 (in fondo); le differenze residue fra
> simulatore e codice nella sezione 11.

Bilanciamento del nuovo sistema di combattimento (docs/wiki/SISTEMA_COMBATTIMENTO.md) con un **set minimo** di oggetti.
**Dungeon a 20 piani** (19 di discesa + il 20 con il boss finale), **un livello del PG per piano** (livello = piano,
tetto 20 prima dell'Abisso), poi Abisso dal piano 21 al 255 (sempre livello = piano). Il numero di piani è un
parametro (`dungeon.floors`): pozioni, riferimento e taratura seguono. Tutti i numeri sono in
`data/rules.yaml`; i mostri sono tarati automaticamente da `tools/simulators/fit_rules.py` sul PG di riferimento di ogni
piano; i confronti sono di `tools/simulators/cmp_rules.py`; il report completo è `out/work/simulators/simulazione_regole.html`
(`tools/simulators/sim_rules.py`). Il gioco in assembly usa `data/rules.yaml` + `data/balance.yaml` via `tools/build/gen_db.py`.

Vincoli del simulatore (uguali al gioco): bot fermo davanti ai mostri, attacco base ogni "cadenza" (arma + rallentamento per DES
bassa, 18/11: `player.attack_speed`, `tools/simulators/rules.py`), un mostro
attacca al contatto e poi ogni 0,9 s, ogni colpo del PG ferma il mostro per 0,1 s, 4 pozioni in cintura (rossa, rossa,
gialla, viola) bevute sotto il 35% della vita.

## 1. Obiettivi scelti

| cosa | obiettivo | perché |
|---|---|---|
| gruppo di 3 mostri base, PG di riferimento | vinto sempre, vita finale ~60%, 4–8 s | il combattimento normale: si vince ma si consuma |
| boss con nome del piano | ~70% di vittorie (piani 1–19) | la sfida del piano, con le pozioni |
| boss finale (livello 20) | ~65% con 4 pozioni | fine del gioco base |
| Abisso: boss con nome | dal 70% (livello 20) al 45% (255) | sempre più difficile salendo |
| Abisso: colpi a segno del PG | calano (dal 60% al 45%), mai 100% | i mostri "si induriscono" |
| PG senza armatura e con il pugnale | regge i piani 1–4, crolla dal 7 | la crescita viene dall'equipaggiamento |

## 2. PG

Tre caratteristiche, tutte usate. `mod = (valore − 10) / 2` per difetto.

| caratteristica | iniziale | aumenti (+1 al livello) | cosa fa |
|---|---|---|---|
| FOR | 16 (+3) | 4, 8, 12, 16, 20 → 21 (+5) | tiro per colpire e danno delle armi, CD del Battle Cry |
| DES | 13 (+1) | 10, 18 → 15 (+2) | CA (limitata dall'armatura: cuoio illimitata, maglia max +2, piastre 0); il pugnale usa il migliore tra FOR e DES |
| COS | 15 (+2) | 6, 14 → 17 (+3) | vita per livello |

- **Competenza**: 2 + (livello − 1) / 4 → +2 al livello 1, +6 al 20. Oltre il 20: +1 ogni 4 livelli.
- **Vita**: 10 + COS al livello 1 (25); +6 + mod COS a ogni livello → 192 al 20, 3507 al 255 (16 bit).
- **Un livello per piano**: il livello previsto al piano N è N; al 20 il PG si ferma finché non batte il boss finale.
- **Tiro per colpire**: d20 + competenza + mod FOR + magia dell'arma ≥ CA del bersaglio − penetrazione. 1 = manca sempre,
  20 = colpisce sempre e critico (dadi dell'arma ×2); dal livello 17 critico anche con 19.
- **CA**: 10 + mod DES (limitato) + armatura + scudo + magia.
- Oltre il 20: +1 a FOR, COS, DES a rotazione ogni 4 livelli.
- **Un'arma c'è sempre** (non esiste il PG disarmato): il pugnale è il minimo.

| livello | vita | comp. | FOR/DES/COS | ATT | abilità nuove |
|---|---|---|---|---|---|
| 1 | 25 | +2 | 16/13/15 | +5 | Slash |
| 3 | 41 | +2 | 16/13/15 | +5 | Whirlwind |
| 5 | 57 | +3 | 17/13/15 | +6 | |
| 7 | 75 | +3 | 17/13/16 | +6 | Battle Cry (dal 6) |
| 9 | 93 | +4 | 18/13/16 | +8 | Rage |
| 13 | 129 | +5 | 19/14/16 | +9 | Smash (dal 12) |
| 15 | 147 | +5 | 19/14/17 | +9 | Frenzy |
| 17 | 165 | +6 | 20/14/17 | +11 | critico su 19–20 |
| 20 | 192 | +6 | 21/15/17 | +11 | |

(ATT con il pugnale senza magia.) **Cosa dà il livello**: vita (×8 dal 1 al 20), le abilità, +6 al tiro per colpire e
+2 al danno. **Cosa dà l'equipaggiamento**: CA da 11 a 21–27, danno per colpo da 4–7 a 13–23, magia +3 al tiro.

## 3. Abilità

| abilità | livello | ricarica | durata | effetto |
|---|---|---|---|---|
| Slash | 1 | cadenza dell'arma + max(0, 12 − 3 × mod DES) (18/11) | — | attacco base |
| Whirlwind | 3 | 2 s | — | colpisce tutti i mostri adiacenti, dadi ×1 |
| Battle Cry | 6 | 15 s | stordisce 2 s | ogni mostro adiacente: d20 + salvezza ≥ 8 + competenza + mod FOR o resta fermo |
| Rage | 9 | 30 s | 6 s | danni subiti dimezzati |
| Smash | 12 | 6 s | stordisce 0,5 s | tiro con vantaggio (2d20), dadi dell'arma ×2 |
| Frenzy | 15 | 30 s | 5 s | +1 colpo per attacco; corsa: +25% al primo colpo a segno, +15% a ogni colpo a segno dopo, max +100%, fino alla fine della Frenzy |

Valore misurato (piano 13, livello 13, vittorie contro il boss con nome): tutte 72% → senza Rage 40%, senza Smash
40%; al piano 20: tutte 42% → senza Rage 11%, senza Smash 10%, senza Frenzy 3%. Whirlwind e Battle Cry valgono sui
gruppi (piano 20, vittorie contro 3 base 96% → 79% / 88%). Nessuna abilità da sola decide un combattimento ai piani
medi; al piano 20 il PG ha bisogno di tutte.

Dopo ogni azione: ricarica globale 0,2 s (come oggi).

## 4. Pozioni

Cura **fissa** (non in percentuale): la rossa vale molto ai primi piani e nulla dopo, la gialla nei piani medi, la
viola scala con il livello. Dal 15/11 (TODO J4) la cura ha due colonne: dungeon (livello PG <= 20) e Abisso (`heal_abyss`);
gialla 60 -> 50 nel dungeon. Valori, percentuali per livello e pozioni dell'Abisso: [oggetti.md](oggetti.md#cura-delle-pozioni-1511-todo-j4).
Controllo con i simulatori (n = 1500, 20 piani): la gialla a 50 invece di 60 cambia solo i piani 4–11 e di poco (piano 11 contro il
boss 68,3% -> 67,5%, vita finale 24,6 -> 22,7); media delle vittorie contro il boss 85,3% -> 85,2%, contro 3 base 99,8% invariato.
Con 55: 85,3%. Nessuna finestra obiettivo rotta: resta 50.

| pozione | cura | ricarica (nessuna pozione per) | esce nei piani (20 piani) |
|---|---|---|---|
| rossa (minor healing) | 20 (Abisso 30) | 5 s | 1–7 (poi 8: 29%, 9: 13%, 10: 5%) |
| gialla (healing) | 50 (Abisso 75) | 7 s | 8–14 (prima 7: 29%, 6: 13%, 5: 5%; dopo 15: 29%, 16: 13%, 17: 5%) |
| viola (greater healing) | 4 × livello + 40 (Abisso 5 × livello + 28) | 10 s | 15–20 e tutto l'Abisso (prima 14: 29%, 13: 13%, 12: 5%) |

| livello | vita | rossa | gialla | viola |
|---|---|---|---|---|
| 1 | 25 | 80% | piena | piena |
| 5 | 62 | 32% | 81% | 97% |
| 8 | 89 | 22% | 56% | 81% |
| 10 | 107 | 19% | 47% | 75% |
| 14 | 144 | 14% | 35% | 67% |
| 15 | 153 | 13% | 33% | 65% |
| 20 | 198 | 10% | 25% | 61% |
| 21 (Abisso) | 207 | 14% | 36% | 64% |
| 30 (Abisso) | 318 | 9% | 24% | 56% |
| 40 (Abisso) | 419 | 7% | 18% | 54% |
| 60 (Abisso) | 679 | 4% | 11% | 48% |
| 80 (Abisso) | 980 | 3% | 8% | 44% |
| 100 (Abisso) | 1321 | 2% | 6% | 40% |
| 150 (Abisso) | 2273 | 1% | 3% | 34% |
| 200 (Abisso) | 3425 | 1% | 2% | 30% |
| 255 (Abisso) | 4872 | 1% | 2% | 27% |

Dove escono: formula, non tabella. Il dungeon è diviso in tre zone (`potions.zones`: fine della zona 0 al 35% dei
piani, della zona 1 al 70%); dentro la propria zona una pozione ha peso 1, a 1/2/3 piani di distanza `ramp` =
0,4 / 0,15 / 0,05, oltre 0. Cambiando `dungeon.floors` le zone si spostano da sole. Percentuali per piano: report,
sezione 7 "quale esce per piano".

Effetto contro il boss con nome (4 pozioni dello stesso tipo): piano 4 → nessuna 4%, rosse 54%, gialle 82%, viola
58% (sprecano cura e hanno ricarica lunga); piano 10 → 54 / 78 / 96 / 96%; piano 20 → 36 / 42 / 50 / 70%.
Ricarica: dopo una pozione non se ne beve nessun'altra per la ricarica di quella bevuta (da confermare). Mentre la
pozione è in ricarica l'HUD deve mostrarlo (TODO).

## 5. Oggetti (set minimo)

Magia +N (0..3 nel dungeon) su arma (tiro e danno), armatura e scudo (CA). Livello oggetto = da quando si trova.

### Armi

| arma | dadi | cadenza | penetrazione | mani | livello | note |
|---|---|---|---|---|---|---|
| dagger (pugnale) | 1d4 | 0,24 s | 0 | 1 | 1 | usa il migliore tra FOR e DES |
| sword (spada a una mano) | 1d8 | 0,28 s | 0 | 1 | 3 | |
| viking_sword (spada vichinga) | 2d6 | 0,40 s | 1 | 2 | 12 | niente scudo; più dadi → Smash e critici più forti |

Confronto al piano 9 (livello 9, maglia, scudo medio, magia +2; vittorie contro il boss / vita finale contro 3 base):
pugnale 49% / 76%, spada 70% / 78%, vichinga 68% / 69% (CA 18 invece di 22). Al piano 15 con le piastre: pugnale 7%,
spada 30%, vichinga 79%. Fino al piano 10 spada e scudo valgono quanto la vichinga; dal 12 la vichinga è l'arma da
boss; il pugnale è l'arma di partenza e basta.

**Abisso**: la spada vichinga con più dadi, trovata dal livello indicato: 3d8 (30), 4d8 (60), 5d8 (100), 6d8 (140),
7d8 (180), 8d8 (220), penetrazione da 2 a 4. La parte casuale del danno resta il 50–60% a ogni livello.

### Armature e scudi

| armatura | CA | tipo (limite al mod DES) | livello |
|---|---|---|---|
| leather_armor | +2 | leggera (nessun limite) | 1 |
| chain_mail | +5 | media (max +2) | 7 |
| plate_mail | +8 | pesante (0) | 14 |

| scudo | CA | livello |
|---|---|---|
| small_shield | +1 | 1 |
| medium_shield | +2 | 5 |
| tower_shield | +3 | 10 |

Effetto al piano 9 (livello 9, spada, vittorie contro il boss): niente 3%, cuoio + scudo piccolo 28%, maglia + scudo
medio 70%, piastre + scudo torre 92%. Al piano 17: niente 42%, maglia + torre 82%, piastre + torre 86%.

### Anelli

+N al **modificatore** di una caratteristica (FOR, DES o COS, scelta alla nascita dell'anello): rame +1, argento +2,
oro +3 (livello oggetto 7, 12, 17). Al piano 13 (livello 13, vichinga): niente 36% contro il boss, rame di FOR 53%,
argento 72%, oro 86%; oro di COS (+42 vita) 57%. L'anello di DES non serve con maglia o piastre (limite al mod DES):
è l'anello del pugnale e del cuoio.

### Equipaggiamento di riferimento per piano

Il PG "normale" che arriva al piano (livello = piano); su questo sono tarati i mostri.

| piano | arma | armatura | scudo | magia | anello | vita | CA | ATT | danno |
|---|---|---|---|---|---|---|---|---|---|
| 1–2 | dagger | leather | small | 0 | — | 25–33 | 14 | +5 | 4–7 |
| 3–4 | sword | leather | small | +1 | — | 41–49 | 16 | +6 | 5–12 |
| 5–6 | sword | leather | medium | +1 | — | 57–66 | 17 | +7 | 5–12 |
| 7–8 | sword | chain | medium | +1 | FOR rame | 75–84 | 20 | +8/+9 | 6–14 |
| 9 | sword | chain | medium | +2 | FOR rame | 93 | 22 | +11 | 8–15 |
| 10–11 | sword | chain | tower | +2 | FOR rame | 102–111 | 24 | +11 | 8–15 |
| 12 | viking | chain | — | +2 | FOR rame | 120 | 19 | +11 | 9–19 |
| 13 | viking | plate | — | +2 | FOR argento | 129 | 20 | +13 | 10–20 |
| 14–15 | viking | plate | — | +3 | FOR argento | 138–147 | 21 | +14 | 11–21 |
| 16–20 | viking | plate | — | +3 | FOR oro | 156–192 | 21 | +16/+17 | 13–23 |

## 6. Mostri (piani 1–20)

Scheda base al piano minimo del tipo (fallen 1, skeleton 1, zombie 4, demon 8; forti: warchief 1, king 2, lich 5,
balrog 9); per ogni piano in più: +0,5 dadi di vita, CA +1, ATT +0,6, danno +1 (parte decimale troncata); poi vita
× `curve_hp[piano]` e danno × `curve_dmg[piano]`. Le due curve sono cercate da `tools/simulators/fit_rules.py` (programmazione
dinamica, curve monotone) sugli obiettivi della sezione 1: vita ×1,5 su tutti i piani; danno ×0,5 (piano 1), ×0,75
(2–7), ×1 (8), ×1,25 (9–14), ×1,75 (15–20).

Boss con nome (piani 1–19): variante forte con vita ×2,5, CA +2, ATT +2. Boss finale (`lord_of_ruin`): 60d10+120 di
vita, CA 22, ATT +13, danno 4d8+32, **immune al blocco da colpo** (altrimenti da solo non attacca mai), evoca al
75/50/25% della vita 2 mostri del piano 14 (massimo 4 vivi): tarato a mano, 72% con 4 pozioni, 56% senza, ~9 s.

Risultato sul PG di riferimento (1000 combattimenti per cella; vittorie, vita finale, durata):

| piano | PG colpisce | mostro colpisce | 3 base | 1 forte | boss con nome |
|---|---|---|---|---|---|
| 1 | 65% | 55% | 100% (68%, 3,0 s) | 100% (85%, 1,8 s) | 100% (67%, 5,6 s) |
| 2 | 60% | 55% | 100% (64%, 3,2 s) | 100% (66%, 3,7 s) | 85% (48%, 10,8 s) |
| 3 | 60% | 50% | 100% (65%, 3,0 s) | 100% (67%, 3,9 s) | 83% (43%, 11,4 s) |
| 4 | 80% | 45% | 100% (63%, 3,4 s) | 100% (60%, 5,0 s) | 58% (28%, 13,1 s) |
| 5 | 80% | 40% | 100% (59%, 4,1 s) | 100% (65%, 4,6 s) | 84% (37%, 13,3 s) |
| 6 | 75% | 45% | 100% (61%, 4,8 s) | 100% (63%, 5,0 s) | 77% (33%, 14,2 s) |
| 7 | 75% | 30% | 100% (71%, 4,9 s) | 100% (71%, 4,9 s) | 88% (38%, 14,7 s) |
| 8 | 75% | 40% | 98% (55%, 5,0 s) | 100% (66%, 4,5 s) | 57% (20%, 11,8 s) |
| 9 | 80% | 30% | 100% (79%, 4,9 s) | 100% (79%, 5,2 s) | 67% (24%, 14,1 s) |
| 10 | 75% | 25% | 100% (79%, 5,5 s) | 100% (82%, 5,6 s) | 78% (30%, 15,5 s) |
| 11 | 70% | 25% | 100% (68%, 6,8 s) | 100% (76%, 6,5 s) | 54% (17%, 16,6 s) |
| 12 | 70% | 55% | 99% (53%, 6,2 s) | 100% (77%, 4,5 s) | 59% (17%, 12,1 s) |
| 13 | 75% | 55% | 100% (59%, 5,9 s) | 100% (79%, 4,3 s) | 72% (23%, 11,6 s) |
| 14 | 75% | 50% | 100% (63%, 5,7 s) | 100% (80%, 4,0 s) | 81% (26%, 11,2 s) |
| 15 | 70% | 55% | 100% (68%, 3,6 s) | 100% (85%, 2,2 s) | 80% (32%, 8,1 s) |
| 16 | 75% | 55% | 100% (72%, 3,0 s) | 100% (87%, 1,8 s) | 94% (47%, 6,4 s) |
| 17 | 75% | 60% | 100% (72%, 3,1 s) | 100% (86%, 1,9 s) | 93% (46%, 6,5 s) |
| 18 | 70% | 65% | 100% (66%, 3,5 s) | 100% (84%, 2,1 s) | 82% (35%, 7,3 s) |
| 19 | 65% | 65% | 100% (61%, 4,1 s) | 100% (81%, 2,4 s) | 56% (20%, 8,1 s) |
| 20 | 60% | 70% | 96% (49%, 4,7 s) | 100% (80%, 2,5 s) | 39% (13%, 8,7 s) |

Il mostro singolo base è sempre vinto (1–3,7 s). Il boss con nome oscilla tra 39% e 100% (media 73%): i piani
16–17 sono i più facili (oro + magia +3 appena presi), i piani 4, 8, 11, 19–20 i più duri. Le curve monotone non
possono seguire i gradini dell'equipaggiamento; per lisciare, spostare gli oggetti del riferimento, non i mostri.

Livello diverso da quello naturale, con l'equipaggiamento del piano (boss con nome): piano 8 → livello 6: 26%,
8: 60%, 10: 98%; piano 5 → livello 3: 55%, 5: 82%, 7: 97%. **Due livelli** spostano il boss di 30–40 punti: più
morbido che con 10 piani (dove erano 10% → 95%).

Senza armatura, con il pugnale, al livello naturale (4 pozioni): gruppo di 3 base vinto al 96–100% nei piani 1–4,
84% al 5, 77% al 6, 47% al 7, poi ≤ 16%. Il boss con nome: 65% al piano 2, 12% al 3, mai dopo. Il mostro singolo
resta battibile fino al piano 17 (87%), al 20 è al 15%. **Senza oggetti il gioco finisce al piano 6–7.**

## 7. Abisso (piani 21–255, livello = piano)

Curva **separata** dal dungeon: i mostri partono dalla scheda del piano 20 e, per ogni piano V = piano − 20,
prendono da una **tabella di 16 righe** (una ogni 16 piani, interpolata in mezzo): CA +, ATT +, vita ×, danno ×.
La tabella (`void.table`) è cercata da `tools/simulators/fit_rules.py --abyss-only`: CA e ATT seguono la crescita di tiro per
colpire e CA del PG di riferimento più un **indurimento** di 6 punti di CA entro il piano 255; vita e danno sono
scelti perché il boss con nome cali dal 70% al 45% di vittorie e il gruppo di 3 resti vinto con vita finale ~60% in
4–8 s. Boss con nome nell'Abisso: vita ×3, CA +2, ATT +2.

PG di riferimento dell'Abisso (livello = piano): spada vichinga dell'Abisso più alta disponibile, piastre, magia
+3 → +8 (+1 ogni 40 piani), anello d'oro di FOR, 4 pozioni viola.

| livello = piano | arma | vita | ATT | CA | danno | PG colpisce | mostro colpisce | 3 base | boss con nome |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 2d6 | 192 | +17 | 21 | 13–23 | 60% | 70% | 100% (64%, 4,6 s) | 70% |
| 36 | 3d8 | 345 | +22 | 21 | 15–36 | 65% | 70% | 100% (67%, 6,4 s) | 76% |
| 52 | 3d8 | 506 | +27 | 21 | 16–37 | 60% | 70% | 100% (67%, 3,2 s) | 70% |
| 68 | 4d8 | 682 | +32 | 22 | 18–46 | 60% | 70% | 100% (68%, 6,5 s) | 59% |
| 84 | 4d8 | 867 | +37 | 22 | 19–47 | 55% | 70% | 100% (70%, 5,0 s) | 64% |
| 100 | 5d8 | 1060 | +43 | 23 | 22–57 | 60% | 70% | 100% (67%, 3,7 s) | 58% |
| 132 | 5d8 | 1485 | +52 | 23 | 23–58 | 55% | 70% | 100% (70%, 4,3 s) | 66% |
| 164 | 6d8 | 1950 | +62 | 24 | 26–68 | 50% | 70% | 99% (70%, 5,9 s) | 59% |
| 196 | 7d8 | 2456 | +73 | 25 | 30–79 | 55% | 70% | 100% (62%, 3,6 s) | 45% |
| 228 | 8d8 | 3009 | +83 | 26 | 33–89 | 50% | 70% | 99% (65%, 4,8 s) | 40% |
| 255 | 8d8 | 3507 | +90 | 26 | 34–90 | 45% | 70% | 96% (52%, 3,2 s) | 56% |

(1000 combattimenti per cella.) I mostri colpiscono il PG sempre al 70% (la CA del PG cresce poco: 21 → 26); il PG
scende dal 60% al 45%. Tutti i valori stanno in 8 bit (ATT, CA) e 16 bit (vita, danno): report, sezione 6.

Regole dell'Abisso già decise (TODO): un piano per livello, morte = −10% della barra di esperienza del livello,
modalità normal / nightmare, portale nero, contatori a 16 bit.

## 8. Cosa va implementato (differenze dal gioco attuale)

1. Caratteristiche FOR/DES/COS con aumenti per livello; competenza; vita 16 bit; danno di un colpo 16 bit.
2. Tiro d20 + ATT ≥ CA − penetrazione; critico (dadi ×2) su 20, dal livello 17 su 19–20; 1 manca sempre.
3. Arma con dadi, cadenza (ricarica dello Slash), penetrazione, a due mani (scudo ignorato).
4. Armature con limite al mod DES; scudi; anelli +N al modificatore; magia +N su tre pezzi.
5. Abilità con durate e ricariche della sezione 3; Frenzy con la corsa progressiva; Rage che dimezza i danni.
6. Pozioni in % con ricarica per pozione (5/10/15 s) e indicazione in HUD.
7. Mostri: scheda per tipo + crescita per piano (+0,5 dadi vita, CA, ATT, danno) × due curve (piani 1–20) oppure
   tabella di 16 righe (Abisso). Sul C64 conviene **vita fissa** per tipo e piano (media dei dadi) al posto del tiro:
   la vita dei mostri a dadi varia troppo.
8. Boss con nome: ×2,5 vita, +2 CA, +2 ATT (×3 nell'Abisso). Boss finale: scheda tarata a mano, immune al blocco da colpo.
9. Armi dell'Abisso (sei spade vichinghe), magia fino a +8, bottino oltre il livello area 40 (da progettare).
10. Dungeon a 20 piani, un livello per piano, esperienza per piano. (Tutto fatto il 06/11.)

## 9. Da confermare / incertezze

- **Ricarica delle pozioni**: blocco di tutte le pozioni per la ricarica di quella bevuta (così simulato) o
  ricarica per tipo?
- **Finestra del boss** (±2 livelli = 26% → 98% al piano 8): accettabile?
- **Boss con nome** tra 39% e 100% a seconda del piano: lisciare spostando l'equipaggiamento di riferimento.
- **Salvataggi a 20 piani**: risolto con un record per piano (docs/wiki/salvataggi.md).
- **Vita a dadi o fissa** per i mostri (vedi 8.7).
- **Rumore**: la taratura usa 60 combattimenti per punto della griglia (poi 400 di verifica); i valori delle curve
  possono cambiare di ±0,25 rifacendo la ricerca. Le tabelle di verifica hanno un errore di circa ±1–3 punti.
- Il PG di riferimento è una scelta: un giocatore che trova meno oggetti è sotto la curva (vedi "senza armatura").
- Il valore dell'anello di DES è nullo in attacco per il PG di riferimento (FOR > DES sempre).
- Il boss finale è un corpo a corpo di 9 s: tra vita ×1,5 e ×2 della scheda le vittorie passano da 70% a 13%.

## 10. Ritaratura dopo l'implementazione (06/11 sera)

Cosa è cambiato rispetto al progetto e come il simulatore lo segue (`tools/simulators/`):
- **Vita dei mostri fissa ±25%** (`mon_hp_init`): il simulatore tira la media × (96 + rnd 0..64) / 128 come
  il codice, non più i dadi della scheda.
- **Boss con nome immuni al blocco da colpo** (decisione 4b) e boss finale idem: nel simulatore `boss` /
  `stun_immune`. Smash e Battle Cry stordiscono ancora tutti.
- **Livello dei mostri** per il calo dell'esperienza: piano (+2 variante forte, +1 boss) come `kill_monster`.
- **Evocazioni del boss finale**: subito, 2 per ondata se i vivi (boss compreso) sono ≤ 4, con le statistiche
  del piano 20 (il codice usa `floor_types` del piano attuale): così anche nel simulatore.
- **Equipaggiamento di riferimento** riallineato al bottino reale (`tools/simulators/sim_chest.py`): magia 0 fino al
  piano 4, +1 dal 5 al 13, +2 dal 14 (prima: +1 dal 3, +2 dal 9, +3 dal 14). L'acquisto delle armi grosse
  (vichinga 2400, piastre 3600) è dettato dall'oro (`tools/simulators/sim_gold.py`, 20/11: ~3 000 oro trovati entro il piano 8,
  ~14 300 nei piani 1–19), i tesori danno quasi solo oggetti base e magia.
- **Durabilità** (`tools/simulators/sim_durability.py`): un'arma media dura ~3–4 piani di combattimento prima di una
  riparazione (25% del prezzo); le armature il doppio. Non entra nei combattimenti simulati (un oggetto rotto
  è un caso raro che il giocatore ripara in città).
- **Varianti forti** solo dal piano 3 e solo se il loro piano minimo è ≤ piano + 1; boss del piano con la
  stessa regola (altrimenti fallen warchief).

Risultato di `tools/simulators/fit_rules.py --final` (60 combattimenti per punto, 400 di verifica; i numeri esatti sono
in `data/rules.yaml growth` e `final_boss_hp_mult`, il report in `out/work/simulators/simulazione_regole.html`):
`ac_per_floor` 1,0, `att_per_floor` 0,7; `curve_hp` ×1,5 dal piano 1; `curve_dmg` ×0,5 ai piani 1–4, ×0,75
ai piani 5–14, ×1 dal 15 (più bassa di prima: il PG di riferimento ha meno magia). **Boss finale**: con le
evocazioni immediate e di piano 20 la vecchia scheda era imbattibile (0–25%); ora vita 45d10+90 (×0,75) e
ondate solo con al massimo 2 vivi → 73% su 400 combattimenti. Boss con nome fra il 42%
(piano 20) e il 100% (piani 1–2) con la cintura di riferimento: la finestra è rumorosa (±10 punti con 60
combattimenti) e il piano 5–6 (60–66%) e 19–20 (51–42%) sono i più duri; i gruppi di 3 base si vincono sempre
con il 60–78% di vita. Abisso: tabella `void.table` ricalcolata (CA +5 … +79, danno ×1,35 … ×30).

**Controllo del 10/11 (v1.146, usura anche per oggetti trovati e comprati dal 08/11)**: rilanciati `sim_durability.py` e
`sim_gold.py`. Arma del PG di riferimento: 7,3 → 2,3 piani per riparazione dal piano 1 al 10, ~3 ai piani 10–19 (coerente
con "~3–4 piani" qui sopra); oro raccolto 17 079 nei piani 1–19 (coerente con ~17 000); tetto di 10 000 addosso raggiunto
al piano 15 senza depositi (7 179 oro persi), nessuna perdita depositando ogni 1–5 piani. **Nessun ritocco** a
`warn_percent` né ai costi. Limite: il simulatore modella un'arma sola che si usura; l'effetto reale (più oggetti che
si usurano) si vede solo giocando.

**Oro nei primi 10 piani dell'Abisso (10/11, `sim_gold.py`, ipotesi non verificate col codice)**: stessa scheda di spawn del
piano 19 (11–22 mostri + boss), chestLevel = 8 × piano, tutto raccolto: 1962 oro al piano 21, 2702 al 30 (+82 per piano),
23 321 in tutto sui 10 piani (nei piani normali: 178 al piano 1, 862 al 10, 1798 al 19). Con il tetto di 10 000 addosso il
primo piano che non ci sta è il 25.

**Simulazione dell'oro rifatta (20/11, `python3 tools/simulators/sim_gold.py`, report in `out/work/simulators/sim_gold.txt`)**:
non più medie ma il **censimento dei piani veri** (`tools/vice/floor_census.py`: 24 semi, piani 1–20, tipi dei mostri, boss e bauli
letti in VICE; `tools/simulators/data/floor_census.json`) e un Monte Carlo delle regole del codice (chiavi disponibili per i bauli,
vendita del bottino). Oro **trovato**: 915 nel capitolo 1, 3 000 nel 2, 4 300 nel 3, 7 850 nel 4 (di cui 1 720 dei bauli epici);
cumulato 14 345 ai piani 1–19, 16 065 con il piano 20. Per piano normale: ~220 (cap. 1), ~735 (2), ~1 055 (3), ~1 540 (4); i
piani dei boss di capitolo (5, 10, 15) danno solo il bottino del boss (35–85 oro). La **vendita** del bottino (a metà prezzo
fino al 20/11) vale più dell'oro trovato dal capitolo 2 (cumulato con la vendita: 68 800 al piano 20, di cui 23 700 gli oggetti epici):
per questo la vendita passa a un quarto (decisione del 20/11, [oggetti](oggetti.md#progetto-affissi-unici-e-memoria-2011)).
Con la vendita a un quarto (dal 20/11) la vendita vale 600 nel capitolo 1, 2 070 nel 2, 4 000 nel 3, 19 700 nel 4
(di cui 11 850 gli oggetti epici): sotto l'oro trovato fino al capitolo 3.
Il 10% dell'oro dei piani 1–19 vale ~360 a baule epico (oggi 430). I numeri del 10/11 qui sotto sono superati.

**Cintura a 4 o a 8: piano intero (20/11, `python3 tools/simulators/sim_floor.py --runs 80`)**: il PG di riferimento al suo
livello combatte tutti i mostri del piano (censimento), in gruppi da 1 a 3 e il boss per ultimo, senza cure fra un gruppo e
l'altro, raccogliendo le pozioni che trova; torna in città (portale) solo con la cintura vuota e meno di metà vita. Con **4
posti** torna in città 0,25–0,39 volte per piano dal piano 3 al 14 (0,10–0,14 ai piani 1–2, quasi mai dal 15: cura viola e PG
più forte); con **8 posti** quasi mai (≤ 0,04). Le morti per piano sono uguali con 4 e con 8 (entro il rumore di 80 prove:
dipendono dai gruppi forti, non dalle pozioni). Quindi la cintura a 8 conta nei capitoli 1–3; data alla fine del capitolo 2
o all'inizio del 3 (decisione P3) toglie i ritorni del capitolo 3. Limiti: politica di ritorno semplice (`--return-below`),
nessuna cura fra i combattimenti (da verificare nel gioco), pozioni dei bauli contate a fine piano.

**Profili di PG e proposta "next" (20/11, `python3 tools/simulators/sim_builds.py --runs 100`, TODO B18)**: gli stessi giri di
piano di `sim_floor.py` (cintura 4) per cinque PG: il riferimento e quattro profili di `data/rules_next.yaml` (forza, destrezza,
costituzione 60/20/20 dei punti, bilanciato 34/33/33; il destrezza porta armatura leggera e spada con scudo). Metrica: morti +
ritorni in città per piano, media per capitolo.

| regole | riferimento | forza | destrezza | costituzione | bilanciato |
|---|---|---|---|---|---|
| oggi, cap. 1 / 2 / 3 / 4 | 0,49 / 0,46 / 0,39 / 0,17 | 0,38 / 0,44 / 0,28 / 0,06 | 0,38 / 0,84 / 1,02 / 1,30 | 0,61 / 0,83 / 1,35 / 2,06 | 0,40 / 0,58 / 0,58 / 0,11 |
| oggi, boss finale vinto | 100% | 100% | 74% | 32% | 98% |
| next, cap. 1 / 2 / 3 / 4 | — | 0,61 / 0,92 / 1,38 / 1,46 | 0,54 / 0,73 / 0,79 / 0,65 | 0,41 / 0,80 / 1,12 / 1,76 | 0,56 / 0,60 / 0,89 / 0,69 |
| next, boss finale vinto | — | 14% | 66% | 6% | 47% |

Con le regole di oggi la difficoltà **cala** dal capitolo 3 e il PG forza è il migliore (il riferimento è quasi un PG forza):
FOR dà attacco e danno, i profili destrezza e costituzione restano indietro e peggiorano verso la fine. I mostri dei piani 15–19
colpiscono il riferimento l'80–90% delle volte (non calano: misura del 20/11), ma il danno è basso rispetto alla vita e alle cure.
La proposta (primo giro, numeri da tarare) tiene il bilanciato fra 0,56 e 0,89 per tutto il gioco, ma: i primi piani non sono
ancora più facili di oggi (la cura in % della vita dà alla rossa 7 punti al livello 1 contro 20); forza e costituzione puri
restano indietro e la destrezza è il profilo migliore (tre effetti: colpire, CA, cadenza). Modello dei mostri della proposta:
attacco e CA spostati in modo che i colpi a segno medi sul bilanciato siano gli obiettivi per piano, vita e danno scalati per
avere lo stesso tempo per uccidere e lo stesso danno relativo di oggi, poi per i moltiplicatori di difficoltà. Limiti: un solo
equipaggiamento per piano (il riferimento, adattato), niente affissi, combattimento fermo (niente arco né movimento).

**Aggiornamento (20/11 sera)**: `sim_builds.py` ora misura (1) i piani **senza i piani dei boss** e con la metrica **morti +
ritorni ogni 10 mostri** (un piano del capitolo 3 ha 15–16 mostri, uno del capitolo 1 ne ha 9: i picchi dei piani 4, 6, 11 sono
mostri forti in più e piani più lunghi, non rumore: con 1000 prove per piano le medie per capitolo si spostano ≤ 0,08); (2) il PG
a livello piano, +1 e +2 (`--offsets`, il farming); (3) i **boss di capitolo e il boss finale a parte**, senza meccaniche, con
quelle del codice e con le proposte ([bestiario](bestiario.md#proposta-del-2011-più-meccaniche-e-taratura-con-il-simulatore-design-non-nel-codice)).
Ogni 10 mostri, livello = piano, capitoli 1→4: oggi riferimento 0,71 / 0,43 / 0,35 / 0,09, proposta bilanciato 0,71 / 0,51 /
0,68 / 0,46. Due livelli in più dimezzano o azzerano la metrica in entrambe le regole (il calo dell'esperienza del gioco ferma il
farming a ~3 livelli sopra il piano).

**Squilibrio delle caratteristiche (20/11 notte, `tools/simulators/fit_stats.py`)**: con i primi costi della proposta la DES
valeva fino al 180% del bilanciato (colpire + CA + cadenza) e la FOR il 68% (solo danno, +1 ogni 4 punti). Ricerca su griglia
(3888 combinazioni, modello analitico, piani 4/8/12/16/19) con l'obiettivo "ogni profilo specializzato ~10% sotto il bilanciato";
scelti: **FOR +1 danno ogni 2 punti** (era 4), **DES +1 ATT ogni 8** (era 5) e **+1 CA ogni 10** (era 8), cadenza invariata
(−1 fotogramma ogni 2), **COS +4 vita a punto** (era 3) e **−0,5% di danno subito a punto** (era 0,4, tetto 20%), **rendimento
dimezzato oltre 24 punti** (era 30). Potenza del profilo / bilanciato (modello): forza 72–99%, destrezza 76–121%,
costituzione 80–101%. Monte Carlo (`sim_builds.py --runs 100 --rules next`), ogni 10 mostri, capitoli 1→4: forza 0,74 / 0,81 /
0,90 / 0,88; destrezza 0,90 / 0,89 / 1,02 / 0,90; costituzione 0,59 / 0,80 / 0,90 / 1,19; bilanciato 0,76 / 0,62 / 0,73 / 0,51
(prima: forza fino a 1,00, destrezza 0,41 al capitolo 4). I tre profili specializzati ora si equivalgono; il bilanciato resta
avanti (fino a ~2 volte meno morti e ritorni nel capitolo 4) per il rendimento dimezzato: anche senza volerlo (obiettivo "tutti
uguali", `--margin 0`) la griglia non chiude il divario, quindi dipende dalla regola del rendimento e dagli equipaggiamenti dei
profili, non dai costi. Le oscillazioni fra piani vengono dai cambi di equipaggiamento (piano 12: spada a due mani per tutti
tranne la destrezza). Boss rifatti con `--fit-bosses` (vita ×0,68 / ×1,62 / ×0,61 / ×0,4): bilanciato 49 / 58 / 52 / 58%;
Mother Stitch resta il boss peggiore per i profili specializzati (9–20%: protezione e maledizione tagliano il danno).

**PG specializzato (21/11, richieste del committente)**: rendimento più dolce, **2/3 oltre 32 punti** (era 1/2 oltre 24).
Le caratteristiche salgono **solo con i punti** che il giocatore assegna (4 a livello, anche nell'Abisso): nessuna crescita
automatica (oggi nel gioco `epic_every`: +1 ogni 4 livelli oltre il 20). **Requisiti degli oggetti** (`requirements`, scala
della proposta, anelli compresi): spada FOR 15, spada a due mani 30, cotta di maglia 20, piastre 35, scudo medio 15, scudo torre
20; chi mette tutto in DES non porta la spada a due mani (profilo destrezza: FOR 28 al livello 20), il profilo costituzione resta
con spada, scudo e cotta. **Attacchi extra della DES** (regola del committente, versione del 21/11 notte): il primo si
sblocca dopo **16 punti** di DES sopra 10 (DES 26), poi uno ogni **8 punti**; ognuno sale di **10 / 1,85 / 1,3 % a punto** fino al
**100%**, al massimo **3** nel dungeon (nell'Abisso, con i punti dei livelli in più, salgono tutti e ne arrivano altri). Ogni
attacco extra fa il tiro normale e, se va a segno, un secondo tiro con quella probabilità (`sim_rules.fight`: `hero.extra`,
`hit(q=...)`; il successivo indipendente dal precedente, `extra_chain: false`). Profilo destrezza al livello 20: **100 / 50 /
25%** (il primo arriva al livello ~9); bilanciato 100 / 7%; forza e costituzione 10%. La DES **tiene la velocità** (decisione
del committente: −1 fotogramma di rallentamento ogni 2 punti, come oggi nel gioco) e la CA (+1 ogni 16), ma **non dà bonus a
colpire**: con il bonus (+1 ogni 10 o ogni 20) la destrezza domina i capitoli 2–3 (0,24–0,31 ogni 10 mostri). Prima versione,
scartata: 5 attacchi extra (100 / 80 / 60 / 40 / 20% al 20), con velocità la DES era di gran lunga la migliore. Ogni 10 mostri,
capitoli 1→4: forza 0,62 / 0,61 / 0,81 / 1,24; destrezza 0,82 / 0,47 / 0,40 / 0,91; costituzione 0,56 / 0,75 / 0,73 / 1,19;
bilanciato 0,65 / 0,54 / 0,68 / 0,56. Nel capitolo 4 i tre profili specializzati fanno ~2 volte il bilanciato: provati FOR +1
danno ogni 2 punti e COS +4 vita e −0,5% a punto, non cambia (resta 1,0–1,3): dipende dalla regola del rendimento (2/3 oltre 32),
dai requisiti e dalla velocità che premia solo la DES, non dai costi. Taratura dei mostri: gli attacchi extra moltiplicano solo
gli Slash (`monsters.extra_weight` 0,6). Costi: FOR +1 danno ogni 3 punti, COS +3 vita e −0,4% di danno subito a punto. Boss
(vita ×0,68 / ×1,66 / ×0,56 / ×0,42, danno del boss finale ×0,4): bilanciato 66 / 56 / 51 / 57%; il boss finale è duro per i
profili specializzati (forza 16%, destrezza 41%, costituzione 45%). **Da verificare sul C64**: fino a 4 tiri d'attacco per Slash
(8 con la Frenzy) nello stesso fotogramma (prestazioni, TODO D5; si possono spalmare su più fotogrammi).

**(superato il 20/11) Oro piano per piano, 1–100 (10/11, Abisso = ipotesi)**: piani 1–19 come
sopra (17 079 cumulati); piano 20 = i 4 bauli epici (1 720); dal 21 l'oro per piano sale da 1 962 a 2 802 al piano 32 (chestLevel
saturo a 255) e poi resta a 3 093 (anche l'oro dei mostri satura a 255); cumulato 257 241 al piano 100. Sono medie con tutto
raccolto e nessuna spesa; i mostri dell'Abisso sono assunti come quelli del piano 19.

Da rivedere giocando (non misurabile nel simulatore): il peso della durabilità sull'oro (riparazioni a 25%),
la frequenza dei tesori buoni (10% dei tiri a ≥ 0,8 T), l'oro dei bauli epici (430 ciascuno).

## 11. Differenze residue fra simulatore e codice

- Il simulatore tiene il PG fermo con i mostri a contatto: nel gioco il giocatore si muove, usa Whirlwind
  su gruppi, scappa; i numeri del simulatore sono il caso peggiore "fermo".
- Pozioni: il simulatore beve sotto il 35% della vita con la cintura di riferimento; il colore reale dipende
  dal piano (zone).
- Frenzy: il simulatore conta il colpo in più, non la corsa.
- Usura, armi rotte (danno 0 dal 07/11, prima pugni), riparazioni: solo in `sim_durability.py`.
- Bottino: `sim_chest.py` riproduce `gen_item` (categoria, L = round(T·u²), oggetto migliore ≤ L, magia da
  `bon_tab[L]`), ma non la sequenza esatta del generatore del gioco (i bauli del piano sono deterministici dal
  seed nel gioco).
- (19/11) **Meccaniche dei boss dei capitoli 1–3** (evocazioni e rigenerazione dell'abate, giro della macina, carica e scudo
  di Varok: [bestiario](bestiario.md#meccaniche-dei-boss-di-capitolo-decise-il-1511)): il simulatore (`tools/simulators/chapters.py`,
  boss di capitolo) **non le riproduce**, la percentuale di vittoria contro i boss dei capitoli è quella del boss senza meccaniche.
  Da aggiungere quando i numeri saranno decisi in gioco.

## 12. Prezzi proporzionali al guadagno — PROPOSTA (06/11 sera, non applicata)

Regola proposta: un oggetto di livello oggetto N costa circa l'oro raccolto in **1,5 piani** al piano N (oro per
piano da `tools/simulators/sim_gold.py`: mostri medi + boss + bauli, senza vendite). Applicata solo all'equipaggiamento con
livello oggetto ≥ 1; gli oggetti di partenza (livello 0) e i consumabili restano come sono (pozioni ~15–25% dell'oro
del piano in cui compaiono in negozio: già in linea). Oro iniziale già portato a 100.

| Oggetto | ilvl | Oro per piano a quel livello | Prezzo oggi | Prezzo proposto (×1,5, arrotondato) |
|---|---|---|---|---|
| dagger | 0 | 178 (piano 1) | 40 | 40 (invariato) |
| leather armor | 0 | 178 | 80 | 80 (invariato) |
| small shield | 0 | 178 | 60 | 60 (invariato) |
| sword | 3 | 276 | 200 | **410** |
| medium shield | 5 | 390 | 400 | **580** |
| chain mail | 7 | 547 | 900 | **820** |
| copper ring | 7 | 547 | 700 | **820** |
| tower shield | 10 | 862 | 1800 | **1300** |
| viking sword | 12 | 1081 | 2400 | **1600** |
| silver ring | 12 | 1081 | 2500 | **1600** |
| plate mail | 14 | 1291 | 3600 | **1950** |
| gold ring | 17 | 1559 | 8000 | **2350** |
| red / yellow / violet | 0 / 5 / 12 (negozio) | 178 / 390 / 1081 | 25 / 90 / 250 | invariati |
| portal scroll | 1 | 178 | 60 | invariato |

Effetti da valutare prima di applicarla: la spada raddoppia (con 100 monete iniziali si compra al piano 2–3), gli
oggetti alti costano molto meno (la gold ring da 8000 a 2350): si comprano 1–2 piani prima di oggi. La vendita
(metà prezzo fino al 20/11, poi un quarto) degli oggetti trovati non è nel conto: con la vendita il giocatore ha più oro di quello della
tabella. **Non certo al 100%**: l'oro per piano è una media del simulatore, non misurata in partita.
Se il committente conferma: `rules.yaml` (`price`), `tools/simulators/` (prezzi letti da `rules.yaml`), manuale cap. 5.
