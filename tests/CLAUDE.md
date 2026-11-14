# tests/CLAUDE.md — regole dei test

Regole generali nel `CLAUDE.md` della radice; come girano i test (container, flussi, comandi): `docs/getting-started.md` sezione 5;
dettagli di suite e runner: `docs/test.md`.

## Dove girano
- Nel container **`lab64-tools`** (VICE 3.10 compilato nell'immagine, Xvfb): `./build.sh` (smoke + sanity),
  `./build.sh --release` (anche regression), `lab64 test -k ID`. Mai sull'host.
- VICE si avvia sempre con `-default` e con **tutte** le ROM di `roms/vice-roms/` di Lab64 passate a mano (`py/vicemon.py` di Lab64,
  `py/vice_env.sh` di Lab64; nel gioco `tools/vice/vice_env.sh` aggiunge solo `ROOT`): niente configurazione o cartella dati dell'utente.
- Test sull'emulatore secondario (`EMU-*`): il demone sta in `lab64-vc64web`, acceso da `./build.sh --emu` o `--release`
  (`EMU_URL`); senza demone sono SKIP, non FAIL.

## Suite (11/11, regole del committente)
- Tre suite in tre cartelle, un runner (`lab64 test`, report con ID, esito, tempo e motivo in `out/work/test_report.txt` / `.json`):
  - `smoke/`: pochi test **veloci** sull'**happy path** delle funzioni principali, con le scorciatoie di VICE (memoria,
    routine chiamate, teletrasporto, tasti scritti all'uscita di `read_input`).
  - `sanity/`: i test della **feature appena implementata**. **Quando si passa a una feature nuova, i test di `sanity/` si
    spostano in `smoke/` (happy path veloce) o in `regression/` (casi particolari, lenti)**, poi si scrivono i sanity
    della feature nuova. Ogni feature nuova ha i suoi sanity prima di essere consegnata.
  - `regression/`: **tutti i casi particolari**, il più vicino possibile al gioco vero (anche lenti).
- **Tetti di durata** (`C64_TEST_CAPS` in `lab64.env`, letti dal motore dei test di Lab64): smoke 20 s, smoke + sanity 35 s, singolo test 10 s; oltre, la build fallisce.
  Sono un freno contro l'aumento dei tempi, non un obiettivo; con il viewer (`--view`) non contano.
- **debug = smoke + sanity** (deve passare prima di ogni consegna e di ogni commit); **release = anche regression**. Se si tocca
  un'area coperta da un test di regression (generatore, salvataggi, oggetti, mostri, musica, regole) lanciare a mano quei test
  (`lab64 test regression -k SAVE`) prima di consegnare, anche in debug.
- **Ogni correzione di un difetto** (11/11): valutare un test che l'avrebbe trovato. Si scrive se ha senso (il difetto può
  tornare, il caso è realistico) e se non è troppo lungo né troppo complicato; altrimenti scrivere nel commit (o nel TODO) perché
  non c'è. Il test va nella suite giusta (smoke se veloce e sull'happy path, altrimenti regression).

## Come si scrive un test
- Una cartella per feature in ogni suite, con un `cases.py` che registra i test (gli altri file sono script e dati della feature).
- **ID** maiuscoli e significativi `AREA-NN` (`SHOP-01`, `INN-CHEST-01`): `01`–`09` smoke, `10`+ sanity e regression; un test
  spostato conserva l'ID. Test (ID, descrizioni, motivi, commenti) **in inglese**.
- Il più veloce possibile: niente tempi fissi verso VICE (si aspetta il prompt o la fermata, `Vice` di `py/vicemon.py` di Lab64, usata da `tests/lib/c64.py`). **All'avvio si aspetta il
  C64, non un tempo** (14/11, TODO I11): `Vice()` chiama `wait_boot` (Lab64) (vettori IRQ `$0314/5` = `$EA31` e `READY.` sullo schermo; tetto 30 s),
  perche' VICE apre la porta del monitor ~7 s prima di finire il boot a freddo. Un VICE lanciato con `-autostart` non mostra `READY.`:
  `Vice(boot_wait=<s>)`. `Vice.close()` uccide l'intero gruppo di processi (xvfb-run, Xvfb, x64sc).
  `Game.to_menu()` carica `START` dal monitor e lo avvia (Krill's Loader installato, tutto in ~1 s reale); il modulo MENU lo scrive
  il monitor (`C64_REALMENU=1` per leggerlo dal disco). Gli strumenti in VICE partono da `START` (`g 080d`), mai da GAME a `$0400`.
- File temporanei in `out/` (mai `/tmp`); un test che assembla una variante del gioco deve lasciare la build normale
  (`tests/run_tests.sh` la rifà alla fine).

## Eroe di prova (regole del committente)
- **Nome** (08/11): sempre un nome che usa tutti i 12 caratteri (`NAME_LEN`) e contiene uno spazio: oggi **`black thorne`**
  (`tu_name` in `src/game/levels.asm`), anche negli screenshot e sull'emulatore secondario.
- **Baule della locanda pieno al limite** (08/11): oro `c_sgold` = 65535 decine = 655350 monete (`TU_SGOLD`; nelle varianti della
  locanda, TESTUI 21/29, anche i 24 posti pieni) e **oro nello zaino** (2350): il totale (657700) usa tutte le 6 cifre.
- **Pozioni** (08/11): sempre **8 pozioni** (cintura a 8 posti, 4 slot da 2, `docs/quests.md` 6bis). Il riquadro purse ha sempre il
  posto per 8 (2 file da 4). Oggi la cintura del codice ha 4 posti: finché la cintura a 8 non c'è, l'eroe di prova ne ha 4 (TODO).

## Emulatore secondario (vc64web, 13/11)
- **VICE resta l'unico riferimento autorevole**: i numeri misurati su vc64web non sono misure del gioco, si confermano in VICE.
- Il gioco deve andare anche lì: test `EMU-10..16` (`tests/regression/emu/`, `tests/lib/emu.py`, ~2 minuti). Se si tocca loader,
  salvataggi, avvio, HUD o input: `./build.sh --emu` e `lab64 test regression -k EMU`.
- I test non assumono l'ordine delle merci dell'alchimista (casuale a ogni visita).
