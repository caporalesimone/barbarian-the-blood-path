# Per cominciare (getting started)

Copyright © 2026 Simone Caporale. Vale per la build 32 / API 25. Riferimenti completi: [`c64-cli.md`](c64-cli.md) (ogni comando), [`C64-API.md`](C64-API.md) (API), [`scripting.md`](scripting.md) (script di testo), [`../examples/`](../examples/README.md) (esempi eseguibili).

Questa guida elenca **le prime cose da provare**, in ordine, e gli errori più comuni. Tutti i comandi qui sotto sono stati eseguiti su un demone reale.

## 0. Due modi di usare il pacchetto
- **`out/VirtualC64-vNN.html`**: l'emulatore in un solo file, da aprire nel browser (anche da telefono). Nessun controllo remoto.
- **Demone + CLI (`headless/`)**: un emulatore pilotato da riga di comando, per automazione, test, script, video. È quello di cui parla il resto della guida.

## 1. Installazione e build (una volta)
```sh
python3 build.py --no-docker                 # NON usare --bump-version: è solo per le release
cd headless && npm install && npx playwright install chromium
```
Serve anche `ffmpeg` (con `libx264`) solo per i video deterministici: senza, il resto funziona. Dettagli: README, sezione Build.

## 2. Avviare il demone
```sh
cd headless
export NODE_PATH=$(npm root -g)              # solo se playwright è installato globalmente
node c64d.js &                               # porta 7064; --port N per un'altra; --headed per la finestra visibile (serve un display)
```
Si ferma con `node c64 quit`. Più emulatori insieme = più demoni su porte diverse (`--port`, e `node c64 --port N …`).

## 3. Primi comandi
```sh
node c64 start                               # accende il C64 (BASIC)
node c64 pause                               # ferma il core: da qui in poi avanza solo quando lo dici tu
node c64 sendText 'print"ciao"\n'            # digita (non aspetta)
node c64 runFrames 100                       # avanza di 100 fotogrammi esatti (2 secondi emulati), poi si ferma
node c64 screenText                          # lo schermo come testo
node c64 --out shot.png screenshot           # screenshot PNG
node c64 --compact peek 0x0400 8             # 8 byte di memoria
node c64 poke 0xC000 '[1,2,3]'               # scrive: i vettori vanno in JSON valido
```
Capire il **modello del tempo** è l'unica cosa non ovvia: dopo i comandi deterministici (`runFrames`, `runUntil`, …) l'emulatore è **fermo** tra una chiamata e l'altra; `resume` lo fa girare in tempo reale. Un fotogramma PAL = 19656 cicli.

## 4. Argomenti dei comandi
Ogni argomento è: `@@file` = testo del file; `@file` = contenuto binario (base64); altrimenti JSON valido, altrimenti stringa. Oggetti e array devono essere **JSON valido** (niente `0x…` dentro `[ ]` o `{ }`; usa numeri decimali o stringhe `"0x…"`). `--compact` stampa il JSON su una riga. `--quiet` **non stampa il risultato**: non usarlo se ti serve l'output.

## 5. Cose utili da provare, in ordine
1. **Aspettare un evento** invece di contare fotogrammi: `c64 runUntil '{"text":"READY."}'` (testo in screen code), `c64 runUntil '{"pc":"0xC002"}'`.
2. **Salvare e ripristinare uno stato**: `c64 saveState base` … `c64 loadState base` (in memoria del demone); su file: `c64 --out base.bin saveState base '{"export":true}'` e `c64 loadState @base.bin`. Per esperimenti ripetibili.
3. **Script di testo** (input temporizzato, `wait`, `assert`, screenshot, video): `c64 --outdir out script examples/scripts/01-ciao.txt`.
4. **Ciclo di controllo in pagina** (bot, misure; veloce perché senza HTTP per passo): `c64 runLoop 'c64.joy(2,{right:true},2);' '{"frames":200}'`. Esempi in `examples/loops/`.
5. **Registrare**: video deterministico muto (`c64 --out v.mp4 video script.txt`), oppure video+audio in tempo reale (`grabBrowserVideoAndAudio`). Scelta: README, sezione Registrazioni.
6. **Regressione**: `c64 regress save base` e poi `c64 regress check base` (confronto di CPU/RAM/schermo con la baseline in memoria del demone).
7. **Trovare una variabile di gioco**: `c64 ramSnap a`, fai accadere qualcosa, `c64 ramDiff a null` → indirizzi cambiati.
8. **Cicli esatti di una routine**: `c64 measure ETICHETTA_INIZIO ETICHETTA_FINE` (usa `loadLabels @@game.lbl` per i nomi).
9. **Testo del gioco**: `findText` (codifiche con nome: `loadEncoding`). Se ritorna `null` su un gioco con schermo e charset propri, leggi `c64 screenInfo`: l'HUD può stare in un'altra area (`{"addr":N}`) e avere una codifica propria (`{"map":{"0-9":45,"/":55}}`).

## 6. Errori comuni
| Sintomo | Causa e rimedio |
|---|---|
| Il demone sembra bloccato | `c64 status` (non si accoda) mostra il job; `c64 abort` lo interrompe (l'emulatore resta fermo). Un client ucciso interrompe da solo il suo job: non serve `pkill -9`. |
| `ERRORE STALL` | il core non avanza da 5 s durante un'esecuzione: `c64 abort`, poi `c64 status`. |
| `poke` prima di `loadFile` sparisce | l'autoload fa un reset: poke dopo il ritorno di `loadFile`, o `{"autoload":false}`. |
| Un disco non risulta montato | montarlo con il core in marcia (`resume`), non fermo. |
| Registrazione dal browser = immagine ferma | `grabBrowserVideoAndAudio` registra in tempo reale: il core deve girare (`resume`, o un `runLoop` in corso). |
| `call` su una routine che non ritorna | `CALL_TIMEOUT` dopo `timeoutFrames` (default 600); per cambi livello e simili: `{"noWait":true,"frames":N}`. |
| `c64 games` non trova nulla | cerca in `$C64_GAMES`, poi `./games`, poi `<repo>/games`, poi `/games`. |
| `trace`/`poke` con valori `0x…` in un array dà errori o gira all'infinito | JSON non valido passato come stringa: usa numeri decimali. |
| Warp e passo-passo | dopo `warp(true)` il core avanza a salti di ~26 fotogrammi (misurato): niente `runLoop` in warp se serve precisione; per saltare fotogrammi in modo esatto `runFrames N '{"fast":true}'`. |

## 7. Esiti diversi dallo stesso stato?
Dalla API 24 (la 23 aveva un difetto con gli input tenuti) `runFrames` e `runLoop` sono esatti anche quando il browser è in ritardo: stesso stato + stesso codice del bot = stesso esito (anche se il gioco usa numeri "casuali": il generatore del gioco legge timer e raster, che fanno parte dello stato). Controllo: il risultato di `runLoop` ha `exact:true` e `framesActual` uguale a `frames`; `retriesTotal` conta le ripetizioni (`retries` ne elenca al massimo 200). Per verificare un bot: stesso `stateHash` con e senza `{"_forceRetry":1}` (`c64-cli.md` §14). Prova: `examples/shell/11-determinismo.sh`.
Se ci sono ancora differenze:
1. I due run partono da `loadState` identico e **con il core fermo**? Niente `type`/`sendText` ancora in corso al momento di `saveState`/`loadState` (la coda tastiera del core non si svuota: `loadState` avvisa). Niente `grabBrowserVideoAndAudio`, `resume`, `sleep` o `waitFor` in mezzo (tempo reale = non ripetibile), niente `{"exact":false}`.
2. Il bot usa qualcosa di esterno all'emulatore (`Math.random()`, `Date.now()`, tempi dell'host)? Allora non è ripetibile per costruzione.
3. `ramSnap`/`ramDiff` ogni M fotogrammi per trovare il primo fotogramma in cui divergono.
Per esplorare molte varianti: `c64-batch` (più istanze in parallelo, il bot varia i parametri con `RUN`).

## 8. Cosa non è verificato
Docker (build e run), `--headed` su un desktop reale (provato solo sotto Xvfb), `game` con `.prg/.t64/.crt` diversi dai dischi, JiffyDOS, versione minima di Node, Windows/macOS, tempi su video molto lunghi. Il core emula la famiglia 1541: stato interno del drive (RAM/CPU del 1541) non esposto. Le misure di cicli vanno confermate con VICE per decisioni di temporizzazione.
