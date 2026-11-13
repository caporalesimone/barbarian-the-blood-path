# Changelog

Formato: **Add** (nuovo) · **Fix** (corretto) · **Change** (comportamento cambiato).
"Build" = numero in `VirtualC64-vNN.html` e nel nome dello zip. "API" = versione di `c64-api.js` (`c64.apiVersion`).
Le voci più recenti sono in alto. Per le build fino alla 10 il legame build↔API non è registrato: sono elencate per API.

## Dopo la build 32 (non ancora numerata, 13/11)
- Add: pagina portable con **`?disk=URL[&program=NOME]`**: scarica il disco e lo avvia (con "Autoload + RUN" se attivo). `fetch` con
  `cache:'no-cache'` (riscaricato solo se cambiato sul server). Senza parametro la pagina non fa richieste di rete, come prima. Solo da
  un server web (da `file://` il browser blocca `fetch`). Provato con il viewer del gioco (server di websockify).

## Build 32 (API 25) — dal report Barbarian su v31
- Verifica sul gioco (report v31): R12–R16 risolti; bot completo del boss con hash identico con 0, 1 reale, forzato a ogni passo, 2 ogni 3, `exact:false`; `c64-batch -j 3` 9/9 identici.
- Fix R17: `retries` troncato a 200 voci senza avviso → `retriesTotal`, `retriesTruncated`; `c64-batch` usa il totale; `11-determinismo.sh` stampa il totale.
- Doc: `_forceRetry`/`_forceEvery` come opzioni di prova per verificare un bot; misura del costo del passo esatto (44 ms → 82 ms per passo da 2 fotogrammi, dovuto al core dopo il ripristino; causa interna non verificata).

## Build 31 (API 24) — dal report Barbarian su v30
- **Fix R12 (bloccante)**: il ripristino dei passi esatti perdeva joystick e tasti tenuti. Cause misurate: (1) porte joystick e matrice tastiera non sono nello snapshot del core; (2) il ripristino non è trasparente nemmeno senza input (un passo ripetuto cambiava lo stato dei CIA); (3) gli eventi di tastiera programmati restano nella coda del core attraverso il ripristino e `loadState` (e passavano da un'esecuzione alla successiva: la prima esecuzione di un demone nuovo differiva dalle altre). Correzioni: modello degli input riapplicato a ogni ripristino (rilascia tutto, ripreme, riprogramma i consumati); ogni passo parte da uno stato appena ripristinato; `type()` in `runLoop` con rilascio gestito dal ciclo; `saveState`/`loadState` con gli input.
- **R13**: `11-determinismo.sh` con bersaglio che legge `$DC00` + buffer KERNAL, `loops/bot-input.js` (sostituisce `bot-chiuso.js`), ripetizioni forzate. Esito: stesso hash con 0, 1 per passo, 2 ogni 3 ripetizioni; 6/6 uguali su 3 istanze.
- **R14** `.cdef` con simboli e `.enc`; **R15** `assert text`; **R16** `retriesCount` in `c64-batch`.
- Costo: un ripristino in più per passo (~6 ms) oltre allo snapshot (~5 ms); a una istanza la velocità resta tempo reale (non rimisurata in dettaglio sul gioco).
- Non verificato: `gfx_consts.inc` vero del gioco (provato un file con la stessa struttura); `sendText` lungo a cavallo di un ripristino (usa finestre di eventi programmati: dovrebbe essere coperto dalla riprogrammazione, non provato); joystick/tastiera con `--headed` e mani dell'utente sulla finestra.

## Build 30 (API 23) — dal report Barbarian su v29
- **Fix determinismo** (R4/R5/R6): `runFrames`/`runLoop` esatti con snapshot+verifica+ripristino; `runLoop` ritorna `framesActual`, `exact`, `retries`. Riprodotto senza gioco (1 passo su 1000 a +1 fotogramma con carico CPU variabile) e corretto: 3/3 hash identici su 1000 passi; prova `examples/shell/11-determinismo.sh` + `examples/loops/bot-chiuso.js`.
- Add (R1): `loadEncoding` (oggetto o righe `.cdef` 64tass), `encodings`, opzione `enc` in `findText`/`runUntil`/`wait text`.
- Add (R2): `findText {len}` ricerca lineare in un buffer, ritorna `{offset,addr}`.
- R3: le etichette in `addr` funzionavano già; documentato.
- Add (R9): `headless/c64-batch` (più esecuzioni su più demoni, `RUN` nel codice del ciclo, raccolta risultati JSON).
- Fix: messaggio d'errore per `JOY2-UP&FIRE` negli script; `findText` con `map`: maiuscole/minuscole equivalenti.
- Non fatti, con misura del motivo: R7 (nessuna chiamata wasm sincrona; `SPEED_BOOST` 500% senza effetto), R8 (inutile: la cadenza è il tempo reale, non il costo di disegno), R10 profilatore (nessun aggancio per istruzione nel core), `whenRegs` veloce (la RetroShell non legge i registri CPU).
- Non verificato: `loadEncoding` con il `.cdef` vero del gioco; sintassi `.cdef` di 64tass ricostruita (intervallo `"AZ"` e `"A","Z"`), non dalla sua documentazione; restauro dello snapshot con caricamenti da disco in corso (solo testo digitato provato).

## Build 29 (API 22)
- Add: `measure(from,to,{n})` con min/max/media.
- Change: gli esempi shell scrivono in `$TMPDIR/c64-examples-output` (non più `output/` nel pacchetto).
- Doc: `whenRegs` documentato come lento (≈0,2 s per stop, misurato dall'altra chat); `getting-started.md` §7 su come cercare la causa di esiti diversi dallo stesso stato.
- Non fatto: `whenRegs` più veloce (il costo è nei 3 halt/run per stop e nell'attesa che evita il recupero di fotogrammi; toglierla farebbe avanzare l'emulazione in modo non esatto: non verificato se e come eliminarla); mappa delle lettere dell'HUD (serve il codice del gioco, che non ho). Determinismo del bot nel gioco: non riproducibile qui; senza il gioco il ciclo è esatto (3/3 uguali).

## Build 28 (API 21)
- Add: `findText(...,{map})` (codifica propria), `measure(from,to)` (cicli tra due PC), `runUntil({pc,whenRegs})`.
- Fix: `c64 games` non trovava `games/` se lanciato da `headless/` (ora cerca anche `<repo>/games`).
- Doc: `docs/getting-started.md` (prime cose da provare), più istanze in parallelo (provate: due), misura del warp (salti di ~26 fotogrammi).
- Non fatto: `runLoop` in warp (inesatto per la granularità misurata), profilatore per routine, stato RAM/CPU del drive 1541, video deterministico più veloce del tempo reale. `change_level` (12 s): non riprodotto senza il gioco; ipotesi, non verificata: la routine ritorna davvero dopo ~600 fotogrammi (generazione livello), cioè vicino al timeout di `call` (600).

## Build 27 (API 20)
- Add: opzione `--headed` / `C64_HEADED=1` del demone: Chromium con finestra visibile, comandato dalla CLI come in headless. Serve un display; chiudere la finestra termina il demone. Provato solo sotto Xvfb (avvio + comandi); l'aspetto della finestra su un desktop reale non è stato visto.
- Add: `screenCodes({addr})` e `findText(testo,{addr})` leggono la RAM schermo da un indirizzo scelto invece di quello del VIC (giochi con schermo di testo altrove o doppio buffer). Non verificato sul gioco Barbarian (segnalato `findText` nullo sulla stanza del boss: causa non accertata).
- Doc: diagrammi Mermaid (architettura, flusso job/status/abort, scelta registrazione, pipeline di build, procedura di release).

## Build 26 (API 19)
- Fix: `reset({hard:true})` non funzionava (`wasm_hard_reset is not a function`).
- Fix: il demone andava in crash con risultati contenenti BigInt (es. `c64 wasm wasm_get_cpu_cycles`).
- Fix: `roms()` sovrastimava di 1 byte; Change: `c64 rom` senza argomenti = ROM utente attive; `c64 rom KIND NOME` passa il nome del file.
- Doc: nuovo `docs/c64-cli.md` (ogni comando del client e dell'API con output reali e cosa non è verificato) e cartella `examples/` (8 script, 2 cicli, 10 script shell, generatore di D64 di prova), tutti provati.

## Build 25 (API 18)
Correzioni dalle prove sul campo (gioco «Barbarian»); dettaglio in `docs/C64-API.md` (API 18).
- Fix: `runLoop` con `joy(porta,stato,frames)` non tornava più (due `runFrames` concorrenti si fermavano a vicenda). Ora le esecuzioni sono serializzate e dentro `runLoop` `joy(...,frames)` preme/rilascia senza far avanzare il tempo. Era anche la causa dei «9 minuti» di `c64 video` con un bot.
- Add: watchdog `STALL` (core fermo da 5 s durante una esecuzione).
- Add: `abort()` / `c64 abort` (interrompe il job in corso); un client chiuso o ucciso interrompe il suo job; `c64 status` / `progress()` (job in corso e avanzamento).
- Fix: `call` che non ritorna → errore `CALL_TIMEOUT` chiaro (ripristina PC e area di lavoro); Add: `call(...,{noWait})` e `call ADDR nowait` negli script.
- Add: `findText`, `screenCodes`, `runUntil({text})`, `wait text "..."` (ricerca in screen code, anche con charset propri).
- Add: `grabBrowserVideoAndAudio({audioGain})` per alzare il livello dell'audio registrato (molto basso).
- Doc: `timeoutFrames` 3000 è il default, non un limite; il video deterministico gira a tempo reale; `POKE` prima di `loadFile` con autoload viene perso (reset).

## Build 24 (API 17)
- Change: `build.py` non incrementa più `BUILD` di default; l'incremento richiede `--bump-version` (sostituisce `--no-bump`).
- Add: `build.py` controlla ffmpeg (PATH + encoder libx264) a fine build; se manca stampa un WARNING senza bloccare. Il README spiega come installarlo.
- Change: l'immagine Docker contiene solo il necessario all'esecuzione dell'headless (pagina già buildata, `headless/`, docs API e scripting, ROM): allowlist in `.dockerignore`.
- Change: repo con `build.py` che genera tutto in `out/` (HTML portable con ROM e emulatore incorporati, pagina headless, immagine Docker se c'è Docker). `portable/` e `headless/` contengono solo sorgenti; `out/` non è nel repo. Le ROM sono nel repo (`third-party/`).
- Add: pagina portable con menu per scegliere Kernal (7 varianti), chargen (2) e drive (1541-II/1541); predefinite le standard. Headless: solo le standard incorporate (altre con `c64 rom`).
- Change: tolte le ROM drive non compatibili (1540, 1551, 2031, 1570/71/81, 1001, 2040…9000).
- Add: client `c64 games` / `c64 game NOME` (cartella `games/`, `$C64_GAMES`); `$C64_ROMS` accetta più cartelle separate da `:`.
- Change: Docker incorpora tutto il repo (incl. `out/`), volumi `/games`, `/roms`, `/scripts`, `/output`.
- Change: la versione API è nel file `headless/APIVER` (letto dal demone); `headless/package.json` dichiara l'unica dipendenza, `playwright`.

## Build 23 (API 17)
- Change: nuova struttura dello zip: `README.md` e `CHANGELOG.md` in root, `Dockerfile` in root, `docs/`, `headless/` (ex `src`), `portable/` (HTML standalone), `third-party/` (emulatore e ROM, un README per componente con origine e licenza).
- Add: `loadRom`, `clearRoms`, `roms`, `start({roms})` e client `c64 roms` / `c64 rom KIND NOME`: ROM alternative (Kernal, Basic, chargen, drive 1541) dalla cartella `third-party`. Tutti i Kernal VICE si avviano; dei drive solo famiglia 1541.
- Change: `c64 docs` cerca `C64-API.md` anche in `docs/` e `../docs/`; Docker: copia `headless/`, `docs/` e le ROM VICE (`C64_ROMS=/app/roms`).

## Build 22 (API 16)
- Add: `grabBrowserVideoAndAudio` — registra video e audio del browser (webm VP9+Opus) in tempo reale, in un registratore a parte, senza alcuna sincronizzazione con l'emulatore. Pannello comandi con scelta indipendente `keyboard`/`joy1`/`joy2` = `none|below|overlay` (FIRE a sinistra, stick a destra; in overlay stick a due cerchi), `scale`.
- Nota: `c64 video` e `video start` negli script restano deterministici e muti.

## Build 19 (API 15)
- Add: comandi nello script: `poke`, `assert mem=`/`assert screen`, `wait mem=` (anche `!=`, maschera), `saveState`/`loadState`, `screenshot`, `regress save|check`, `call`. Errori con numero di riga e codici `ASSERT`/`REGRESS`/`TIMEOUT` (exit 1 da shell).
- Add: `video start|stop` e `rec start|stop` nello script; senza `keep` la chiusura è garantita a fine script (anche in errore), con `keep` continuano oltre lo script e si chiudono a mano (`c64 videoStop`, `recordStop`).
- Add: `scripting.md` (guida completa con esempi) nel pacchetto; client `--outdir`; Docker: cartelle `scripts/` e `out/` montate.
- Change: gli errori di `runScript` portano `outputs` e `log` (il client salva comunque i file prodotti).
- Nota: audio nel video non fatto (campioni del core non deterministici, vedi C64-API.md).

## Build 17 (API 14)
- Add: `runLoop` (ciclo di controllo dentro la pagina, ~8x più veloce dei passi via HTTP).
- Add: `c64 video` (mp4 deterministico con input, ffmpeg lato demone; `capStart/capRun/capTake/capStop`).
- Add: `runFrames(n,{fast:true})` esatto anche con il warp (500 fotogrammi: 0,64 s invece di 10 s).
- Add: insiemi di etichette (`loadLabels({set})`, `useLabels`, `set:nome`), `runUntil({screenMatch})`, `driveTrace`, `recordStop({format:'text'})`.
- Add: client `--quiet` e `--compact`; Dockerfile con ffmpeg.
- Fix: `stateHash` instabile alla prima chiamata (il componente CPU dipende dal debugger): escluso dall'hash complessivo (`includeCpu`).
- Fix: `loadFile`/`start` con `program` in maiuscolo non trovava il file (ora minuscolo).
- Change: documentato che il primo `runFrames` dopo `warp(false)` avanza di ~26 fotogrammi di troppo.

## Build 16 (API 13)
- Change: `recordVideo({scale})` massimo 4 (1536×1080, circa full HD); prima 8.

## Build 15 (API 12)
- Add: `recordVideo({scale})`, ingrandimento intero con pixel nitidi (es. 3 → 1152×810).

## Build 14 (API 11)
- Fix: `c64 sendText 'testo\n'` da shell scriveva `\n` letterale; ora preme RETURN.

## Build 13 (API 11)
- Add: `Dockerfile` e `docker-compose.yml` (non provati). Demone: variabili `C64_HOST`, `C64_NO_SANDBOX`; client: `--host`.

## Build 12 (API 11)
- Add: `runScript` / `scriptCheck` e `c64 script file.txt` (righe `<fotogramma> <input> [durata]` e `wait`).
- Change: lo zip ha il numero di versione nel nome.

## Build 11 (API 10)
- Change: l'HTML standalone non contiene più controllo remoto né documentazione. L'API è nel file `c64-api.js`, iniettato dal demone.
- Change: il demone apre `c64-headless.html` (solo emulatore, senza interfaccia). Nome HTML senza `-apiN`.
- Change: la documentazione è `C64-API.md` (anche `c64 docs [parola]`); il metodo `docs()` non esiste più.
- Add: `C64-TODO.md` e questo changelog nello zip.

## API 10
- Add: `regressSave` / `regressCheck` / `regressList` e `c64 regress` (confronto stato registrato vs nuovo: hash, RAM, schermo).
- Add: `recordVideo` (WebM, tempo reale, non deterministico).
- Fix: l'hash della CPU è escluso dal confronto (instabile), salvo `includeCpu`.

## API 9
- Change: `type` = un tasto o più tasti simultanei; `sendText` = stringhe. `key()` e il vecchio `type(stringa)` rimossi (nessuna retrocompatibilità).
- Change: tempi minimi pressione 1 / rilascio 2 fotogrammi (default 3 / 3).
- Add: `framesPerKey` e `releaseFrames` in `sendText`.

## API 8
- Fix: `type` e `sendText` perdevano caratteri dopo un reset (il KERNAL legge la tastiera dopo ~140 fotogrammi): ora attendono il boot (`noWait` per disattivare).

## API 7
- Add: `sprites`, `stateHash`, `disasm`, `find`, `ramSnap` / `ramDiff`, `recordStart` / `recordStop` / `replay`, `sendJoy`, `store*`.
- Add: demone Node `c64d` e client da riga di comando `c64`.

## API 6
- Add: `sendText`, watchpoint, `saveState` / `loadState`, `step` / `trace`, `inspect` / `sid` / `sidTrace`, `screenDiff` / `recordGif`, `runUntil` con `pcIn` / `mem` / `watch` / `when` / `all`, errori con codice.
- Change: `frames()` ritorna un intero (il frazionario è `framesExact()`).
- Fix: `loadFile` con autoload tornava prima della fine della sequenza (ora attende; `wait:false` per il vecchio comportamento).
- Fix: `setRegs` con un'etichetta in `pc` impostava 0.

## API 5
- Change: «Autoload + RUN» attivo di default (anche per `start({disk})` e `loadFile` di un d64; `autoload:false` per disattivarlo).
- Change: il test tasti compare in ~4 s invece di ~20 s.

## API 4
- Change: test tasti riscritto in linguaggio macchina (latenza 1 fotogramma; F2/F4/F6/F8, RESTORE).

## API 3
- Add: controllo deterministico (`runFrames`, `runUntil`, `regs`, `call`, breakpoint, `diskImage`, `driveState`, etichette, `joy(porta,stato,frames)`, `peek(a,n,opt)`, `start({driveRom})`).
- Change: `screenText` legge dal VIC.

## API 2
- Add: `runKeyTest`.

## API 1
- Add: controllo base (start, tasti, joystick, peek/poke, `screenText`).
