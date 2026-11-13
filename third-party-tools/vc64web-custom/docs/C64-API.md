# API di controllo esterno — `window.c64`

Versione: `c64.apiVersion` / `c64.info()` (numero API in `headless/APIVER`, build in `BUILD`)

Copyright © 2026 Simone Caporale

## Struttura del repo
- `build.py` genera in `out/`: `VirtualC64-vNN.html` (pagina portable, nessuna API di controllo) e `c64-headless.html` (solo emulatore, aperta dal demone).
- `headless/c64-api.js`: l'API `window.c64`, **iniettata** nella pagina dopo il caricamento (il demone lo fa da solo; a mano basta incollarla nella console). La versione API è in `headless/APIVER`, sostituita al posto del segnaposto all'iniezione.
- `headless/c64d.js`: demone Node (Chromium headless via Playwright, usato solo internamente) che apre la pagina, inietta `c64-api.js` ed espone `window.c64` via HTTP su 127.0.0.1.
- `headless/c64`: client da riga di comando. `c64 docs [parola]` stampa questa documentazione (o le sezioni il cui titolo contiene la parola).
- `docs/`, `README.md`, `CHANGELOG.md`, `third-party/` (emulatore e ROM, un README per componente), `Dockerfile`.

L'API non usa l'interfaccia: niente click sui bottoni, niente coordinate. Nei metodi sotto la forma è JavaScript `c64.metodo(args)`; da shell è
`c64 metodo arg1 arg2…` (ogni argomento è JSON, `@file` = file in base64, `@@file` = file di testo, `--out file` salva PNG/GIF/video/disco).

```sh
NODE_PATH=$(npm root -g) node c64d.js &   # una volta, da headless/ (usa ../out/c64-headless.html e c64-api.js accanto a c64d.js; --page/--api per altri percorsi)
c64 start
c64 sendText 'print"ciao"\n'
c64 waitFor CIAO
c64 screenText                    # schermo come testo, senza visione
c64 quit
```

Molti metodi sono asincroni. Gli errori hanno un codice (`e.code`; da shell `ERRORE CODICE: messaggio`, exit 1),
es. `NOT_STARTED: emulatore non avviato: chiama c64.start()`.
Codici nuovi in API 18: `ABORTED` (job interrotto da `abort()`/client chiuso), `STALL` (il core non avanza da 5 s durante una esecuzione), `CALL_TIMEOUT` (`call`: la routine non è tornata), `CLIENT_GONE` (il client si è disconnesso prima che il job partisse; solo demone).

## Ciclo di vita
| Metodo | Descrizione |
|---|---|
| `start({disk:{name,data}, autoload=true, program, port, driveRom, timeout})` | Avvia l'emulatore. `data` = base64, array o `Uint8Array`. Ritorna `state()` a boot finito. |
| `ready(timeout=30000)` | Attende emulatore avviato e prompt BASIC (>3M cicli). |
| `stop()` | Spegne (rimuove l'iframe). |
| `reset()` | Reset del C64. |
| `pause()` / `resume()` | Pausa / ripresa. |
| `warp(on)` | Warp on/off. |
| `state()` | `{started, running, frozen, warp, cycles, disk8, disk, port, kbd, roms}`. |
| `runKeyTest()` | Riavvia e carica il test tasti/joystick (come il bottone 🧪): scandisce la matrice della tastiera e i joystick via IRQ (routine 6502 a `$C000–$C60F`, hook su IRQ/NMI) e inverte il tasto premuto entro 1 fotogramma. Mostra SHIFT sx/dx, F1–F8, RESTORE, porte 1 e 2. |

## Input
| Metodo | Descrizione |
|---|---|
| `type(tasto|[tasti], {frames:3, releaseFrames:3, shift, ctrl, cbm, noWait})` | **Un solo tasto** (carattere o nome: `'w'`, `'RETURN'`, `'F1'`, `'RUN/STOP'`, `'SHIFT+A'`, `'CTRL+3'`) o un **elenco di tasti simultanei** (`['w','d']`). Matrice del C64, `frames` di pressione (min 1) + `releaseFrames` (min 2). Una stringa lunga → `BAD_ARG`: usa `sendText`. Ritorna `{keys,frames}`. |
| `keyDown(tasto|[tasti])` / `keyUp(...)` | Tenuta di uno o più tasti; effetto al prossimo fotogramma emulato. |
| `sendText(testo, {framesPerKey:3, releaseFrames:3, keepCase, noWait})` | Per le stringhe: vedi «Novità API 6» e «Novità API 9». |
| `joy(dir, on, port?)` | `dir` = `up|down|left|right|fire`, `on` = 1/0. Porta di default: quella scelta (J2). |
| `joyPulse(dir, ms=150)` / `fire(ms=120)` | Pressione breve. |

Nomi dei tasti (maiuscole indifferenti): `RETURN` (`ENTER`,`CR`), `RUN/STOP` (`RUNSTOP`,`STOP`), `F1`…`F8` (F2/F4/F6/F8 = SHIFT+F1/F3/F5/F7), `SPACE`, `HOME`, `CLR`, `DEL`, `INST`, `UP` `DOWN` `LEFT` `RIGHT` (anche `CRSR_*`), `RESTORE`, `CTRL`, `CBM` (`C=`), `SHIFT`, `RSHIFT`, `POUND`, `ARROW_UP`, `ARROW_LEFT`; combinazioni con `+` (`'SHIFT+A'`, `'C=+Q'`). `keyNames()` li elenca.
Attenzione: con il Fire premuto la porta 2 disturba la tastiera (come su un C64 vero).

## File
| Metodo | Descrizione |
|---|---|
| `loadFile(nome, dati, {autoload, program})` | Monta `.d64/.g64/.prg/.t64/.crt`. Per `.prg/.t64`: reset + `RUN` automatico. Per `.d64` (autoload attivo di default, `autoload:false` per disattivarlo): `LOAD"programma*",8,1` + `RUN`. |
| `eject()` | Espelle il disco dal drive 8. |

## Memoria
Vista della CPU, I/O compreso (vale per RAM, ROM e registri). `a` = indirizzo 0–65535.

| Metodo | Descrizione |
|---|---|
| `peek(a)` / `peekWord(a)` | Un byte / una word little-endian. |
| `peekRange(a, n)` | Array di `n` byte. |
| `dump(a, n)` | Hex dump testuale, 16 byte per riga. |
| `poke(a, v)` / `pokeRange(a, bytes)` | Scrittura. |

Nota (non verificato): leggere certi registri I/O (es. CIA `$DC00-$DD0F`, VIC `$D000-$D3FF`) potrebbe avere effetti collaterali. Per dump estesi evita `$D000–$DFFF` se non serve.

## Schermo
| Metodo | Descrizione |
|---|---|
| `screenText()` | 25 righe × 40 colonne dalla pagina schermo del KERNAL (`$0288`). I caratteri grafici appaiono come `▒`. |
| `cursor()` | `{col,row}` dalle locazioni `$D3` / `$D6`. |
| `waitFor(testo, timeout=15000)` | Attende che il testo compaia sullo schermo (maiuscole ignorate). `true`/`false`. |
| `screenshot()` | `data:image/png;base64,...` del canvas. |

`screenText()` legge la RAM schermo del KERNAL: nei giochi che usano un altro bank VIC o la modalità bitmap non è significativo.

## Controllo deterministico (API v2)
Modello: dopo `runFrames`, `runCycles`, `runUntil` e `call` l'emulatore resta **fermo**; `peek`/`poke` avvengono a stato congelato; `resume()` lo riporta in tempo reale. 1 fotogramma PAL = 19656 cicli.

| Metodo | Descrizione |
|---|---|
| `cycles()` / `frames()` | Cicli totali / fotogrammi (cicli ÷ 19656). |
| `runFrames(n)` | `n` fotogrammi esatti, poi si ferma. Ritorna `{reason, cycles, frames}`. |
| `runCycles(n)` | Come sopra, arrotondando per eccesso a fotogrammi interi. |
| `runUntil(cond, {timeoutFrames=3000})` | `cond`: `{pc}` (numero, `'$0840'`, etichetta o array), `{addr, value, mask?, not?}`, `{screenText:'testo'}`, `{screenRegex:'^READY'}`, `{text:'testo'|[codici]}` (API 18: ricerca in screen code, vedi `findText`), `{cycles}`; vale la prima verificata. Timeout → eccezione `timeout: pc $0840 non raggiunto in 600 fotogrammi`. `pc` ferma sull'istruzione esatta. |
| `pause()` / `resume()` | Ferma / riparte in tempo reale. |
| `regs({full:true})` | `{pc, line, cycle, cycles, a, x, y, p, sp}`. A/X/Y/P/SP via stub 6502 in `$0334–$0367` (ripristinata, ~40 cicli). `{full:false}` legge solo PC/raster. |
| `setRegs({pc,a,x,y,p})` | SP non modificabile. |
| `call(addr, {a,x,y}, {timeoutFrames=600, scratch=0x0334, noWait, frames})` | `JSR addr` e ritorno con registri/PC ripristinati; ritorna `{a,x,y,p}`. Se non ritorna: errore `CALL_TIMEOUT`. `noWait:true` (API 18): `JMP` alla routine, la lascia girare `frames` fotogrammi (default 2), ritorna `{started,pc,frames}`; vedi «Novità API 18». |
| `abort()` / `progress()` | API 18. `abort()`: interrompe il job in corso (errore `ABORTED` a quel job, core fermo). `progress()`: `{frozen,cycles,run,loop}` del job in corso. Da shell: `c64 abort`, `c64 status` (non passano dalla coda). |
| `findText(testo\|codici, {raw,all,exact})` / `screenCodes()` | API 18. Ricerca di testo nella RAM schermo come screen code: `{row,col,addr}` o `null` (`all:true` → elenco). `screenCodes()`: i 1000 codici schermo grezzi. |
| `breakpoint(a)` / `breakpoints()` / `clearBreakpoints()` | Breakpoint del core. |
| `peek(a, n?, {ram?})` | Byte o array di `n`. `ram:true` = RAM pura (imposta temporaneamente `$01`). `a` = numero, `'$C000'` o etichetta. |
| `poke(a, v \| bytes, {ram?})` | Scrive byte o array. |
| `loadLabels(testo)` / `label(nome)` | Etichette VICE `.lbl` (`al C:0840 .nome`) o `nome = $0840`. |
| `attach(8, dati, nome)` / `detach()` | Monta / espelle disco (solo drive 8). |
| `diskImage(8, {bytes?})` | d64 corrente (base64, o `Uint8Array`). |
| `driveState(8)` | `{type, hasDisk, motor, powerSave, syncMark, readMode, halftrack, track, headOffset}`; LED non esposto; `track=(halftrack+1)/2` non verificato. |
| `joy(porta, {up,down,left,right,fire}, frames)` | Stato completo; con `frames` lo rilascia dopo; `joy(2,{})` rilascia. Il rilascio è visibile al `runFrames` successivo. |
| `screenInfo()` | `{bank, screen, charset, charsetRom, lowercase, bitmap, ecm, multicolor, textMode}`. |
| `screenText()` | Ora usa lo schermo scelto dal VIC (`$D018`/`$DD00`). |
| `border()` / `background()` | `$D020` / `$D021`. |

**Misurato** (Chromium headless, `file://`): `runFrames(7)` = 7 fotogrammi esatti con pause di 0–350 ms tra le chiamate; stesso hash della RAM `$0000–$07FF` dopo `reset()` + 300 fotogrammi in due sessioni; `regs`/`setRegs` (a=0x12,x=0x34,y=0x56 riletti identici); `call(0xFFD2,{a:0x58})` scrive «X»; SAVE da BASIC e nome ritrovato in `diskImage`; breakpoint su `$EA31` ferma sull'istruzione.

**Limiti / non verificato**
- Con `warp(true)` `runFrames` non è esatto (misurato 26 invece di 10): usa il warp solo con `runUntil`.
- Dopo una pausa di 15–260 ms il core recupera fino a 3 fotogrammi persi: `runFrames` attende fino a 260 ms per evitarlo (costo fino a ~0,3 s di orologio per chiamata).
- `runCycles` non scende sotto il fotogramma. NTSC non testato.
- Watchpoint e modifica di SP non sono esposti dal core. IRQ/NMI possono cadere durante stub e `call`.
- La finestra deve restare in primo piano: timer rallentati in una scheda in background potrebbero alterare i tempi di attesa (non verificato).

## Menu: POKE / PEEK manuale
Nel menu ☰ c'è un pannello con indirizzo e valore (decimale, `$HEX`, `0x..`, `%bin`, oppure un'etichetta caricata) con i pulsanti POKE e PEEK e l'opzione «RAM pura». Funziona in qualsiasi momento.

## Versioni
Build = numero progressivo della pagina (`VirtualC64-vNN.html`); l'API ha una versione propria, dentro `c64-api.js`. L'API ha **un solo numero intero** che aumenta di 1 a ogni modifica dell'API. **1** controllo base; **2** `runKeyTest`; **3** controllo deterministico (`runFrames`/`runUntil`/`regs`/`call`/breakpoint/`diskImage`/`driveState`/etichette, `joy(porta,stato,frames)`, `peek(a,n,opt)`, `screenText` da VIC, `start({driveRom})`); **4** test tasti in linguaggio macchina (latenza 1 fotogramma, F2/F4/F6/F8, RESTORE); **5** «Autoload + RUN» attivo di default (anche per `start({disk})` e `loadFile` di un d64: passa `autoload:false` per disattivarlo); il test tasti compare in ~4 s invece di ~20 s. **6** `sendText`, watchpoint, `saveState`/`loadState`, `step`/`trace`, `inspect`/`sid`/`sidTrace`, `screenDiff`/`recordGif`, `runUntil` con `pcIn`/`mem`/`watch`/`when`/`all`, errori con codice, `frames()` intero (prima frazionario: ora `framesExact()`). **7** `sprites`, `stateHash`, `disasm`, `find`, `ramSnap`/`ramDiff`, `recordStart`/`recordStop`/`replay`, `sendJoy`, `store*`. **8** `type` e `sendText` attendono la fine del boot dopo un reset (`{noWait:true}` per disattivare). **9** tastiera: `type` = un tasto o più tasti simultanei, `sendText` = stringhe, `key()` rimosso, tempi minimi 1/2 (default 3/3). **10** regressione (`regressSave`/`regressCheck`/`regressList`) e `recordVideo`. **11** `runScript`/`scriptCheck` (script di input da file di testo); l'API è ora un file a parte (`c64-api. **12** `recordVideo({scale})` (ingrandimento intero 1-4 a pixel nitidi; 13: massimo portato a 4) **14** `runLoop`, video deterministico con input (`c64 video`), `runFrames({fast})` esatto con il warp, insiemi di etichette, `runUntil({screenMatch})`, `driveTrace`, `recordStop({format:'text'})`, `stateHash` senza CPU, nome programma in minuscolo..js`), iniettato nella pagina.

## Limiti riscontrati (leggere prima di scrivere test)

**Tempo e determinismo**
- `runFrames(n)` è esatto solo senza warp: con `warp(true)` misurato 26 fotogrammi invece di 10. Con il warp usa `runUntil`.
- Dopo una pausa di 15–260 ms il core "recupera" fino a 3 fotogrammi persi (misurato +3 con pausa 100 ms; nessun recupero con pause ≤20 ms o ≥200 ms). `runFrames` attende fino a 260 ms prima di ripartire: ogni chiamata può costare ~0,3 s di orologio.
- Granularità minima: 1 fotogramma (19656 cicli, PAL). `runCycles` arrotonda per eccesso. `step(n)` (API 6) esegue istruzioni singole ma costa ~20 ms di orologio ciascuna. NTSC non testato.
- Il core gira in tempo reale (≈985 000 cicli/s): 1000 fotogrammi ≈ 20 s di orologio senza warp.
- Determinismo verificato solo come hash della RAM `$0000–$07FF` dopo `reset()` + 300 fotogrammi (due sessioni identiche). Il numero assoluto di cicli dopo `start()` NON è riproducibile (`start()` attende il boot a orologio): usa `pause()` + `reset()` + `runFrames` per partire da uno stato noto.
- Scheda in background: i timer del browser possono rallentare e dilatare i tempi di attesa (non verificato).

**CPU e debugger**
- `regs()` completo, `setRegs` e `call` eseguono uno stub 6502 in RAM (`$0334–$0367`, ripristinata): ~40 cicli, spostano il tempo emulato. Cambia `scratch` se il programma usa il buffer cassetta. IRQ/NMI possono cadere durante lo stub (effetto non misurato).
- Il core non permette di modificare SP, né A/X/Y/P direttamente (solo PC e posizione raster dal prompt del debugger). Dall'API 6 ci sono i watchpoint (`watch`); il registro stampato dal comando `s` del shell ha i nibble invertiti (X=1 appare «10») e non viene usato.
- `setRegs` e `call` vanno usati a emulatore fermo.
- Il debugger resta attivo dopo il primo uso di `regs/breakpoint/runUntil({pc})/driveState`: impatto sulle prestazioni non verificato.

**Memoria e I/O**
- `peek`/`poke` usano la vista della CPU (rispetta `$01`). `{ram:true}` imposta temporaneamente `$01` e lo ripristina.
- Leggere registri I/O (CIA `$DC00–$DD0F`, VIC) potrebbe avere effetti collaterali (non verificato); `$DC00`, `$D018`, `$DD00` sono stati letti senza problemi.
- I registri I/O con bit non usati leggono 1 (`POKE $D020,2` si rilegge `$F2`).

**Input**
- Con Fire o una direzione sulla porta 2 la tastiera riceve tasti fantasma (linee condivise, come su un C64 vero). La tastiera fisica→joystick è disattivata di default.
- Su/giù e sinistra/destra condividono l'asse: `joy(porta,{...})` invia prima i rilasci, poi le pressioni.
- Il rilascio di tasto/joystick si vede solo al `runFrames` successivo (emulatore fermo).
- Le lettere in `type`/`sendText` sono sempre senza SHIFT: per i grafici `type('a',{shift:true})` o `'SHIFT+A'`.
- Tempi dei tasti (BASIC, 8 sfasamenti): pressione 1–4 fotogrammi con rilascio ≥2 = tutto corretto; rilascio 1 = errori. Minimi: pressione 1, rilascio 2; default 3 e 3.
- Autoload di un d64 dopo una riga BASIC digitata a metà (es. `"A"` senza RETURN) può fallire; la pagina azzera `$D4/$D8` per mitigare, il caso residuo non è escluso.

**Schermo, disco, ROM**
- `screenText()` legge la RAM schermo del VIC: in bitmap o con set caratteri in RAM non è significativo (`screenInfo()`). I grafici appaiono come `▒`; il testo invertito non è distinto.
- `driveState()`: LED non disponibile; `track=(halftrack+1)/2` non verificato. Solo drive 8.
- Drive: il core emula solo la famiglia 1541. Incorporate 1541-II (predefinita) e 1541 originale (`start({driveRom:'1541'})` o menu). Provate e NON funzionanti: 1540 (resta in «SEARCHING»), 1570/1571 e 1581 (`?DEVICE NOT PRESENT`): 1571/1581, doppia faccia e MFM non disponibili.
- Le ROM VICE incorporate sono usate di default (le ROM utente le sostituiscono). Le Open ROMs non hanno il floating point (`PRINT 2+3` → `?NOT IMPLEMENTED ERROR`).
- Le funzioni `wasm_*` vivono nell'iframe dell'emulatore, non nella pagina: usa `c64.eval()` o l'API. `wasm_get_cpu_cycles()` ritorna un BigInt: `cycles()` lo converte in Number.
- Nessuna richiesta di rete (verificato). Non provata su telefono/iOS né l'audio.

## Novità API 6
- `sendText(testo,{framesPerKey:3,releaseFrames:3,keepCase,noWait})`: tasti nella MATRICE (non `$0277`), coda in tempo emulato, a emulatore fermo avanza da sé. `\n`=RETURN, lettere senza SHIFT salvo `keepCase`. Token: `{RUN/STOP} {F1}..{F8} {HOME} {CLR} {DEL} {INST} {UP} {DOWN} {LEFT} {RIGHT} {RESTORE} {SHIFT+A} {CTRL+3} {C=+Q} {WAIT:30} {{}`. Verificato F1…F8 = 133,137,134,138,135,139,136,140, CTRL+3=28. Osservato: `{LEFT}` 9 fotogrammi dopo `{UP}` perso in un programma BASIC con GET (11 no), causa non verificata: per programmi lenti `framesPerKey` 4–6 o `{WAIT:n}`. `keyNames()`.
- `saveState(nome)`/`loadState(nome|dati)`/`states()`/`dropState(nome)`: snapshot completo (~790 KB) in memoria JS; `{export:true}` → base64. Verificato: cicli e schermo identici dopo il ripristino. Non verificato: sopravvivenza di breakpoint/watchpoint.
- `watch(a)`/`watchpoints()`/`clearWatchpoints()`/`runUntil({watch})`: stop DOPO l'istruzione che accede (scrittura e lettura verificate), `reason:'watch'`, max 16.
- `runUntil`: `{pcIn:[a,b]}` (max 64), `{mem:[a,v,maschera]}`, `{watch}`, `{pc, when:{addr,value}}`, opzioni `{timeoutFrames, all:true}`.
- `step(n)`, `trace({until,max,last})`: istruzioni singole `{pc,bytes,asm,cycles}`, ~20 ms ciascuna; post-mortem = `loadState` + `trace`. Il registro stampato dal shell per `s` ha i nibble invertiti: non usato (per i registri `regs()`).
- `inspect(nome)` (`vic cia1 cia2 cpu mem sid c64 drive8`) → `{config,state,raw}`; `sid()` registri + voci decodificate; `sidTrace(frames,{every})`. Nessuna registrazione audio.
- `screenshot({rect,raw})`, `screenSave(nome)`, `screenDiff(a,b,{tolerance,rect,image})`, `recordGif({frames,every,rect})`.
- `loadFile(...,{wait})`: con autoload attende la fine della sequenza reset+LOAD+RUN (prima tornava dopo 0,6 s e l'autoload poteva resettare la macchina a metà di un test); `{wait:false}` = vecchio comportamento; con emulatore fermo non attende.
- `reset({hard})`, `wasm(nome,...args)`, `methods()`, `framesExact()`; `frames()` ora intero. Errori con `e.code` (NOT_STARTED, NOT_READY, TIMEOUT, BAD_ARG, UNKNOWN_LABEL, NO_STATE, NO_SHOT, CORE; API 18: ABORTED, STALL, CALL_TIMEOUT, CLIENT_GONE); in postMessage anche `code` e `method`.
- Già presenti prima: `peekRange/pokeRange`, `cycles()`, `driveState`, `joy(porta,stato,frames)`, `warp`, `info`. Non fatti: CPU/memoria del drive, audio WAV, buffer istruzioni passate.
- Riga di comando (opzionale, Node; `c64d` usa Playwright solo internamente per Chromium headless): `c64d.js --page FILE.html` + `c64 metodo args…`.

## Novità API 7
- `recordStart()`/`recordStop()`/`replay(rec,{toEnd})`: registra le chiamate di input (`keyDown keyUp joy sendText type sendJoy fire joyPulse poke pokeRange`) con il fotogramma relativo e le rifà. `recordStop()` → `{startCycles,frames,events:[{f,m,a}]}`. Replay esatto con emulatore fermo e partenza dallo stesso stato (`loadState`/reset). Verificato: stesso hash di stato e stesso schermo. Non verificato in tempo reale.
- `stateHash({only,exclude})`: hash per componente dal comando `checksums` del core (Memory, CPU, CIA1/2, VIC, SID, Drive8…) + hash complessivo.
- `sprites()`: 8 sprite (abilitato, x con bit 8, y, colore, multicolor, espansioni, priorità, puntatore, indirizzo dati) + multicolor 1/2.
- `disasm(a,n)`, `find(byte[]|testo,{from,to,ram,screen,max})`, `ramSnap(nome,{from,to})`, `ramDiff(a,b|null)`.
- `sendJoy("R10 UF8 W5",{port})`: direzioni U D L R + F per N fotogrammi (default 4), `Wn` attesa.
- `storeSet/storeGet/storeDel/storeKeys/storeExport/storeImport`: JSON nel localStorage (prefisso `c64.store.`); tra build con nomi diversi solo se il browser condivide i file:// (Chromium sì; Firefox/Safari non verificato).
- Limiti scoperti: `wasm_rewind` = nastro, non stato; `HEATMAP` non attivabile con `wasm_configure`; `d` del shell accetta solo l'indirizzo (16 righe); `wasm_sprite_info` solo x,y.

## Novità API 8: perché `type()` perdeva caratteri
Causa (misurata): il KERNAL legge la tastiera solo dopo l'inizializzazione, circa 2,75 milioni di cicli (≈140 fotogrammi) dopo un reset. I tasti premuti prima vanno persi: `reset()` + 20 fotogrammi = stringa persa tutta, +80 = solo l'inizio, da +140 niente. Non c'entrano tempo reale né Playwright (con il prompt pronto nessuna perdita). Succede anche con interruzioni disattivate (verificato: un programma BASIC che ferma il timer CIA fa perdere per intero la stringa digitata nell'attesa), caricamenti da disco, programmi che non consumano i tasti.
Da API 8 `type` e `sendText` attendono da soli il boot dopo un reset (`{noWait:true}` per disattivare). Negli altri casi attendi prima il prompt (`runUntil({screenText:'READY.'})`).

## Novità API 9: tastiera
Due comandi: `type` per **un tasto** (o più tasti simultanei) e `sendText` per le **stringhe**. `key()` rimosso, vecchio `type(stringa)` non esiste più (nessuna retrocompatibilità). Entrambi premono nella matrice del C64 con gli stessi tempi: `frames`/`framesPerKey` (pressione, min 1, default 3), `releaseFrames` (min 2, default 3); valori inferiori → `BAD_ARG`.
Limiti:
- Più tasti simultanei: nella matrice sì (verificato su `$DC00/$DC01` con CIA fermo: `[WD]`), ma il KERNAL (`GET`) riporta un solo tasto per scansione (con W+D solo D).
- Fantasmi (3 tasti ai vertici di un rettangolo ne attivano un quarto) e condivisione linee con i joystick: su C64 reale; se il core li emula non è verificato.
- Tasti persi se il C64 non legge la tastiera: boot dopo reset (attesa automatica), interruzioni disattivate, LOAD in corso, programmi che non leggono i tasti.
- Tempi misurati (BASIC, 8 sfasamenti): pressione 1–4 con rilascio ≥2 = ok; rilascio 1 = errori. Un programma che campiona ogni N fotogrammi richiede pressione ≥ N.
- Tempo reale: provato con `type` e `sendText` (GET, F1, SHIFT+A, W+D, ~130 caratteri in ~10 s): come a emulatore fermo; l'attesa usa il contatore dei cicli. Non provato: browser in background, warp, NTSC.
- Caratteri non digitabili (`{ | ~`): `BAD_ARG`; `\` → sterlina, `_` → freccia sinistra.

## Novità API 10: regressione, screenshot e video
`regressSave(nome,{ram,screen,only,exclude})` registra una baseline (hash componenti, RAM, schermo PNG, cicli) e ritorna il bundle JSON. `regressCheck(nome|bundle|JSON,{ignore,tolerance,only,exclude,ram,screen,strict,includeCpu,image,maxGroups})` confronta e ritorna `{pass,reasons,hash,ram:{groups},screen:{diffPixels,bbox,image}}`. `regressList()`.
Limiti: hash CPU escluso (instabile, dipende dalla cronologia del debugger) salvo `includeCpu:true`; baseline e prova devono partire dallo stesso stato deterministico (`loadState` + stessi input a emulatore fermo).
Screenshot: `screenshot`, `screenSave`/`screenDiff`. Animazione deterministica: `recordGif`. Video: `recordVideo({frames|seconds,fps,mime,bitrate,scale})` → `{data(base64),mime,bytes,frames,width,height}` via `MediaRecorder` (WebM VP9/VP8). `scale` = intero 1-4 (ingrandimento senza interpolazione: 3 → 1152×810, 4 → 1536×1080, circa full HD; oltre non è consentito); `bitrate` (bit/s, default 2.500.000) è solo una richiesta al codificatore: misurato a scala 3, 60 fotogrammi, 8 Mbit/s ha prodotto un file più piccolo (52 KB) di quello a default (66 KB), quindi non è una garanzia di qualità. Niente CRF/keyframe/preset (non esposti da `MediaRecorder`). Limiti: codifica in tempo reale (non deterministica, ≈2 s per 100 fotogrammi anche a emulatore fermo), senza audio, 384×270 (× scale), richiede `MediaRecorder` (`UNSUPPORTED`), provato solo su Chromium.
```sh
c64 regress save base --out base.json
c64 regress check @@base.json --out diff.png      # exit 0/1
c64 --out clip.webm recordVideo '{"seconds":3}'
```

## Script di input (API 11)
`runScript(testo,{noWait})` esegue una sequenza di input descritta in un file di testo; `scriptCheck(testo)` valida soltanto (errori con numero di riga). Da shell: `c64 script file.txt`, `c64 scriptCheck file.txt`.
```
# commento (anche a fine riga)
0   L              # <fotogramma> <input> [durata]
140 O
280 A
300 JOY2-UP 30     # joystick 2 su, tenuto 30 fotogrammi
+100 JOY2-FIRE     # +N = N fotogrammi dopo la riga precedente
wait "READY." 5s   # attende il testo a schermo (timeout: fotogrammi, o secondi con s; default 3000 fotogrammi)
0 text "print 6*7\n"
wait 50            # attende 50 fotogrammi
wait pc=0xC000 600
```
- Il tempo è in fotogrammi PAL dall'inizio dello script, **dopo l'attesa automatica del boot** (come `type`/`sendText`; `{noWait:true}` per disattivarla). Dopo ogni `wait` il tempo riparte da 0. Le righe fra due `wait` vanno in ordine crescente di fotogramma.
- Input: un tasto (`L`, `RETURN`, `F1`, `SHIFT+A`, `RUN/STOP`: stessi nomi di `type`), tasti simultanei con `&` (`W&D`), `JOY1-` o `JOY2-` + `UP|DOWN|LEFT|RIGHT|FIRE` (anche con `&`; tasti e joystick nella stessa riga non si mischiano), `text "stringa"` (stringa JSON: `\n` = RETURN; stesse regole di `sendText`, durata opzionale = fotogrammi per tasto).
- Durata: fotogrammi di pressione, default 3, minimo 1. Un tasto ripremuto a meno di 2 fotogrammi dal rilascio produce un avviso (misurato: rilascio troppo breve = pressioni perse).
- `text` blocca lo script finché la stringa è digitata: gli eventi successivi già scaduti partono subito.
- Prima di partire lo script è validato per intero (tasto sconosciuto, durata non valida, righe fuori ordine, `wait` malformato).
- Nessun `if`/`goto`/cicli/variabili/`include`: per la logica usare uno script JavaScript con l'API (`runUntil`, `screenText`, ...).
- **Dal build 19 (API 15) lo script ha anche comandi** (`poke`, `assert`, `wait mem=`, `saveState`/`loadState`, `screenshot`, `regress`, `call`, `video start|stop`, `rec start|stop`): vedi `scripting.md` (guida completa con esempi).
- Ritorna `{events,frames,warnings}` (più `outputs`, `log`, `videoOpen`, `recOpen` se usati i comandi). Provato a emulatore fermo e in tempo reale (L-O-A, joystick su/fuoco/sinistra+fuoco letti da `$DC00`, `wait` su testo con timeout, errori di sintassi). Non provato: script molto lunghi, `wait pc=`.
- `runScript` è registrato da `recordStart` come singolo evento.

## Novità API 14: strumenti per i test lunghi e i video
**`runLoop(codice,{frames,every})`**: esegue DENTRO la pagina un ciclo di controllo (nessuna chiamata HTTP per passo). `codice` è il corpo di una funzione JS con parametri `(c64,i,state)`; `return false` termina; `every` = fotogrammi per passo (default 2), `frames` = massimo. Da shell: `c64 runLoop 'codice' '{"frames":600,"every":2}'`.
Misurato: 300 passi da 2 fotogrammi in 12,2 s (≈ tempo reale, 25 passi/s) contro 3 passi/s con una chiamata HTTP per passo (`runFrames` via HTTP aspetta ~0,26 s: serve a non perdere fotogrammi dopo una pausa del core). Il ciclo è limitato dal tempo reale dell'emulatore (a meno di usare warp, non esatto).
```
c64 runLoop 'const hp=c64.peek("c_hp"); if(hp===0) return false; c64.joy(2,{right:true},2);' '{"frames":3000}'
```
**Dentro `runLoop`, `joy(porta,stato,frames)` non fa avanzare l'emulatore** (API 18): preme subito e rilascia dopo `frames` fotogrammi del ciclo; non serve `await`. Fuori da `runLoop` resta com'era (ritorna una promessa che avanza di `frames` fotogrammi). Prima, dentro `runLoop`, faceva un `runFrames` proprio in concorrenza con quello del ciclo e il ciclo non tornava più (riprodotto: timeout a 60 s).
**Video deterministico con input: `c64 video`**. Gli screenshot sono catturati dentro la pagina ogni `every` fotogrammi emulati mentre gira uno script di input, un ciclo JS o N fotogrammi; il demone li codifica con **ffmpeg** (libx264, deve essere nel PATH: il Dockerfile lo installa). Richiede l'emulatore fermo (`pause`). Nessun salto di fotogrammi, nessuna dipendenza dal tempo reale.
```
c64 --out clip.mp4 video prova.txt                     # script di input (.txt)
c64 --out clip.mp4 video bot.js '{"loopOpts":{"frames":3000}}'   # ciclo JS in pagina (.js)
c64 --out clip.mp4 video 500                            # 500 fotogrammi senza input
```
Opzioni (JSON): `every` (2 = 25 fps), `fps` (default 50/every), `scale` (1-4, pixel nitidi, default 3 = 1152×810), `crf` (qualità x264, default 20), `preset`. Il file arriva al client (`--out`). Senza audio. Metodi sottostanti, usabili anche da codice: `capStart({every})`, `capRun('script'|'loop'|'frames',arg)`, `capTake(n)`, `capStop()`. Provato: script di 350 fotogrammi (178 immagini) e ciclo che si ferma su un testo a schermo, in mp4 H.264. Non provato: durate di decine di minuti (le immagini non ancora codificate stanno in coda, max 200).
**`runFrames(n,{fast:true})`**: esatto anche con il warp. Il grosso gira in warp, gli ultimi 70 fotogrammi a velocità normale (più un passo che assorbe la latenza del warp). Misurato: 500 fotogrammi in 0,64 s (normale: 10 s), 1500 in 2,2 s (normale: 30 s), differenza dai cicli attesi 0 in tutte le prove, stesso `stateHash` della modalità normale. Sotto i 140 fotogrammi non usa il warp. Se il margine non basta ritorna `exact:false`.
**Warp: latenza all'uscita (misurata)**: dopo `warp(false)` il PRIMO `runFrames` avanza ancora a velocità warp (+26 fotogrammi in una prova). Un `loadState` subito dopo la annulla. In warp `runFrames(30)` ne ha eseguiti 53. Per questo il warp semplice non è esatto: usa `{fast:true}`.
**`stateHash`**: il componente CPU dipende dalla cronologia del debugger (la prima chiamata dopo l'avvio del debugger differisce dalle successive, mentre Memory, VIC, SID, CIA e drive sono identici): l'hash complessivo ora lo **esclude** (`includeCpu:true` per includerlo). I componenti sono sempre elencati.
**Etichette per insiemi** (moduli/overlay con indirizzi diversi): `loadLabels(testo,{set:'lobby'})` crea un insieme e lo attiva (`activate:false` per non attivarlo); `useLabels('lobby')`; `labelSets()`; da qualunque insieme si legge con `lobby:nome` (es. `peek('lobby:read_input')`).
**`runUntil({screenMatch:'nome',maxDiff:0,tolerance:0,rect})`**: attende che lo schermo corrisponda a uno screenshot salvato con `screenSave` (al più `maxDiff` pixel diversi). Utile per i giochi con font e bitmap propri, dove `screenText` non serve.
**`driveTrace(frames,{every,drive})`**: storia della testina (traccia, mezza traccia, offset, motore, sync) campionata ogni `every` fotogrammi; il LED non è esposto.
**`recordStop({format:'text'})`**: esporta la registrazione come script di input (`{text,frames,events,notExported}`). Converte `type`, `sendText` e `joy(porta,stato,fotogrammi)`; tutto il resto (poke, joy a stato, sendJoy, runScript...) diventa un commento `# non esportato`. Il tempo è dall'inizio della registrazione: avviarla dopo il boot.
**`loadFile`/`start` con `program`**: il nome è convertito in minuscolo (il programma si carica digitando `load"nome*"` sulla tastiera: il nome maiuscolo produrrebbe grafici PETSCII e `FILE NOT FOUND`).
**Stati su file**: già possibile: `c64 --out s.state saveState nome '{"export":true}'` e `c64 loadState @s.state` (provato: cicli identici dopo il ricaricamento).
**Client**: `--quiet` (nessun output, solo errori e codice di uscita) e `--compact` (JSON su una riga).
Non fatti: audio (né nel video né WAV), più istanze in parallelo, profilatore per routine, breakpoint condizionali su registri.

## Novità API 15: comandi nello script
Dettaglio e esempi in **`scripting.md`**. Riassunto: `poke ADDR v,..`, `assert mem=ADDR VAL [&MASK]` / `assert screen "t"` (errore `ASSERT`), `wait mem=ADDR VAL [&MASK] [timeout]`, `saveState/loadState NOME`, `screenshot FILE`, `regress save|check NOME` (errore `REGRESS`), `call ADDR [a= x= y=]`, `video start [NOME] [every= scale= crf=] [keep]` / `video stop`, `rec start [NOME] [keep]` / `rec stop`. Senza `keep` la chiusura di video e registrazione è garantita a fine script (anche in caso di errore); con `keep` restano aperti e si chiudono a mano (`c64 --out f.mp4 videoStop`, `c64 recordStop '{"format":"text"}'`).
Il video negli script richiede il demone (usa `capArm`/`capClipStop` + ffmpeg) ed emulatore fermo. Client: `--outdir DIR` scrive i file prodotti (screenshot, video, registrazioni) anche se lo script fallisce. Un errore di script porta `outputs` e `log` (`e.outputs`, `e.log`).
**Audio nel video: non fatto.** Misurato: `wasm_copy_into_sound_buffer` restituisce blocchi da 1024 campioni, ~79k campioni per 100 fotogrammi (attesi 88,2k a 44,1 kHz), ampiezza ~0,002 con un tono SID acceso, e cambia dopo `wasm_open_main_thread_audio`: non deterministico. Strada alternativa non provata: sintetizzare il SID offline dai registri (`sidTrace`). L'audio in tempo reale è invece disponibile con `grabBrowserVideoAndAudio` (API 16).

## Novità API 16: `grabBrowserVideoAndAudio` (video + audio del browser, in tempo reale)
Registratore **indipendente dall'emulatore**: un `MediaRecorder` del browser (codifica in un suo thread) cattura il canvas e l'audio della pagina in un unico `.webm` (VP9 + Opus). Non usa `run0`/`runFrames`, non ferma né fa avanzare l'emulatore e non è sincronizzato con il tempo emulato: l'emulatore deve girare in tempo reale (`resume()`); a emulatore fermo il video è un'immagine ferma (avviso nel risultato). **Non deterministico**; la registrazione deterministica (`c64 video`, `video start` negli script) resta com'è, ma muta.
```
c64 grabBrowserVideoAndAudio '{"action":"start","keyboard":"below","joy2":"below"}'
... (si usa l'emulatore normalmente, anche con c64 script)
c64 --out clip.webm grabBrowserVideoAndAudio '{"action":"stop"}'
c64 --out clip.webm grabBrowserVideoAndAudio '{"seconds":10,"joy2":"overlay"}'   # avvia, attende 10 s, ferma (blocca il demone per 10 s)
```
Opzioni: `action` (`start`|`stop`|`status`; con `seconds` registra e ferma da sola), **`keyboard`, `joy1`, `joy2`** (ciascuno `none` default | `below` | `overlay`, indipendenti), `scale` (1-4, default 2), `fps` (50), `bitrate` (4000000), `audio` (true), `audioGain` (API 18, default 1: guadagno applicato solo alla registrazione; l'audio del core è molto basso), `mime`. Il `stop` ritorna `{data(base64),mime,bytes,seconds,width,height,audio,audioPeak,controls,warnings}`; `audioPeak` è il picco (0-1) del segnale registrato: ~0 = silenzio.
**Pannello comandi** (tasti premuti e joystick, dal vivo), una scelta per elemento: `none` = non mostrato; `below` = nel pannello sotto il video (il video diventa più alto): prima i joystick (per ciascuno **FIRE a sinistra, stick a croce a destra**), sotto la tastiera C64 completa; `overlay` = sovrapposto allo schermo, semi-trasparente (tastiera 50%, joystick 65%), dimensioni del video invariate. In overlay lo stick è disegnato come **due cerchi** (base + pomello che si sposta nella direzione premuta, arancione) e FIRE è un cerchio (rosso se premuto). Posizione in overlay: tastiera in basso a sinistra, joystick in basso a destra (FIRE a sinistra dello stick); **se la tastiera non è in overlay e c'è un solo joystick in overlay**, FIRE va nell'angolo in basso a sinistra dello schermo e lo stick in basso a destra (ingranditi); se non è in overlay e i joystick in overlay sono due, joy1 è a sinistra e joy2 a destra (ciascuno con FIRE a sinistra dello stick; questo caso è una mia interpretazione, non specificata). Esempi: `{"keyboard":"below","joy1":"below","joy2":"below"}`, `{"joy2":"overlay"}`, `{"keyboard":"overlay","joy1":"overlay","joy2":"overlay"}`. Si accende ciò che passa da `wasm_schedule_key` e `action` (API, script, tastiera e joystick virtuali della pagina). Tasti ritardati (`delay`) sono mostrati a tempo di orologio (20 ms per fotogramma), quindi in tempo reale sono allineati, a emulatore fermo/warp no.
Misurato (Chromium headless, senza scheda audio): l'AudioContext della pagina è `running`, la traccia audio è presente e un tono SID acceso risulta nel file (`max_volume` ≈ −19 dB con `volumedetect`); video 768×870 con tastiera e joystick `below`, 768×540 con `overlay`/`none` a scala 2. **Non verificato**: durate lunghe (memoria dei blocchi), sincronismo audio/video fine (derive possibili: sono due orologi), audio con l'audio disattivato dalla pagina (`gainNode` assente → solo video, avviso), tastiera/joystick virtuali della pagina completa. Conversione: `ffmpeg -i clip.webm clip.mp4`.

## Novità API 17: ROM alternative
`loadRom(kind,data,{name})` (kind `kernal` 8192 byte | `basic` 8192 | `chargen` 4096 | `floppy` 16384), `clearRoms([kind])`, `roms()` (ROM utente attive), `start({roms:{kernal:..}})`. Valgono dal prossimo `start()` (da avviato: `stop`, `loadRom`, `start`). Client: `c64 roms [filtro]` elenca i file in `third-party/vice-roms`, `third-party/open-roms`, `./roms`, `$C64_ROMS`; `c64 rom kernal 251104-04` carica per parte di nome (`drive` = `floppy`).
Provato: tutti i Kernal C64 di VICE (`901227-01/-02/-03`, `251104-04` SX-64, `390852-01` Games System, `901246-01` 4064, `906145-02`) e il chargen `906143-02` si avviano; drive: `1541` e `1541-II` funzionano (LOAD"$",8 + LIST da un D64 di prova); `1540`, `1551`, `2031` (16 KB) restano in LOADING (prova interrotta a 2500 fotogrammi); `1570/1571/1581` (32 KB) sono rifiutate (il core emula solo la famiglia 1541). JiffyDOS e simili: non fornibili da qui (proprietari); con una copia propria si carica come ROM utente, ma **non è verificato** che il core la accetti né che funzioni. Le ROM di terzi non sono verificate per licenza: `third-party/vice-roms/README.md`.

## Varie
`eval(codice)` esegue JS nel contesto dell'emulatore (funzioni `wasm_*`, `action(...)`, ...). `sleep(ms)`.

## Canale `postMessage`
Per una pagina contenitore o un bridge: invia `{c64:'call', id, method:'peek', args:[49152]}` alla finestra della pagina;
la risposta torna al mittente come `{c64:'result', id, ok:true, value}` oppure `{c64:'result', id, ok:false, error}`.

## Esempi (riga di comando)
```sh
c64 dump 0x0400 64                 # schermo, prime 64 celle
c64 peek 0x2B 2                    # puntatore a inizio BASIC
c64 poke 0xD020 2                  # bordo rosso
c64 loadFile gioco.d64 @gioco.d64 '{"autoload":true,"program":"GAME"}'
c64 pause; c64 runFrames 200
c64 runUntil '{"pc":"read_input","when":{"addr":"cur_level","value":0}}'
c64 saveState prima; c64 trace '{"until":"read_input","last":8}'
c64 screenSave a; c64 sendText x; c64 screenDiff a null
c64 --out clip.gif recordGif '{"frames":60,"every":2}'
c64 --out disco.d64 diskImage
```

## Novità API 18: correzioni dalle prove sul campo
**Esecuzioni serializzate.** `runFrames`/`runUntil`/`call`/`runScript` ecc. passano da una coda interna: una alla volta. Prima due `runFrames` concorrenti si fermavano a vicenda (il `halt()` del primo lasciava il secondo ad aspettare cicli che non arrivavano). In più: se il core non avanza per 5 s durante una esecuzione, errore `STALL` (invece di attendere per sempre).

**Interrompere un job: `abort()`, `c64 abort`, disconnessione del client.** `c64 abort` (POST `/abort`, non passa dalla coda) interrompe il job in corso (`runFrames`, `runUntil`, `runLoop`, script, video): errore `ABORTED` al client di quel job; l'emulatore resta fermo; i job in coda continuano. Se il client viene chiuso o ucciso mentre attende, il demone fa `abort` da solo (se il job era ancora in coda viene saltato, `CLIENT_GONE`). Non serve più `pkill -9`. Provato: runFrames da 200000 fermato in <1 s; client ucciso con SIGKILL, demone di nuovo libero.

**Stato dei job lunghi: `c64 status`** (GET `/status`, non passa dalla coda, funziona mentre un altro client attende): `{busy, method, elapsedMs, queued, progress:{frozen,cycles,run:{frames,of},loop:{iterations,frames,of}}}`. `progress()` è anche un metodo dell'API.

**`call(a,r,{timeoutFrames,noWait,frames})`.** Se la routine non ritorna: errore `CALL_TIMEOUT` con messaggio chiaro (indirizzo, PC, suggerimento); vengono ripristinati solo PC e area di lavoro (`$0334`), non i registri. `{noWait:true,frames:N}` (default 2): salta alla routine con `JMP` (registri a/x/y in ingresso), la lascia girare N fotogrammi e ritorna `{started:true,pc,frames}` senza attendere il ritorno: per routine che non tornano (es. cambio livello). In uno script: `call ADDR nowait`. Con `noWait` lo scratch `$0334` non viene ripristinato e il core continua dalla routine.

**Testo in screen code: `findText(testo|codici,{raw,all,exact})`, `screenCodes()`, `runUntil({text})`, script `wait text "TESTO" [timeout]`.** Cerca nella RAM schermo scelta dal VIC come screen code, non come testo KERNAL: vale anche con charset propri se i codici sono quelli standard (A-Z = 1-26, 0x20-0x3F come ASCII). Lettere indifferenti da maiuscolo/minuscolo, bit 7 (inverso) ignorato salvo `exact`. Per codici di un font proprio: array (`findText([18,5,1,4,25])`). Ritorna `{row,col,addr}` (righe e colonne da 0) o `null`; `all:true` → elenco; la corrispondenza sta in una riga. Limiti: non vede glifi grafici né testo disegnato sulla bitmap; non verificato con un gioco che usa codici non standard. Provato: READY., COMMODORE, assente → `null`, `runUntil`, `wait text` (ok e timeout).

**`grabBrowserVideoAndAudio({audioGain})`.** Guadagno applicato solo alla registrazione (default 1). Misurato: l'audio del core è molto basso (picco ~0,002 = circa −54 dBFS con un tono SID: vedi anche API 16); con `audioGain` 8 e 30 il picco sale di circa +19 e +31 dB come atteso. Quale valore usare dipende dal gioco: controlla `audioPeak` nel risultato (0–1; vicino a 1 = saturazione). Non verificato se il livello basso dipenda dal SID del core o da un guadagno della pagina.

**Chiarimenti (non erano bug dell'API).**
- `runUntil({timeoutFrames})`: 3000 è solo il **default**, non un limite; provato con 4000 (scade dopo 4000 fotogrammi = 80 s a tempo reale).
- **Il video deterministico gira a tempo reale**: 200 fotogrammi emulati (`every=2`) ≈ 4–5 s di orologio, anche a scala 1; un bot con `joy` da 302 fotogrammi: 6,4 s. I «9 minuti» osservati erano il blocco di `joy` in `runLoop` (sopra), non la cattura. Non c'è modo di andare più veloce del tempo reale in cattura (il warp non è usato con la cattura attiva); misurato solo con scala 1 e 3 e senza gioco reale.
- `POKE` prima di `loadFile` con autoload: l'autoload fa un reset, quindi i `poke` fatti prima si perdono (comportamento atteso). Fai il `poke` **dopo** che `loadFile` è tornato (attende la fine dell'autoload) o usa `{autoload:false}`.
- Registrazione in tempo reale (`grabBrowserVideoAndAudio`) con il core fermo: il filmato è un'immagine ferma (il risultato contiene un avviso).
- Non investigato: vita massima dell'eroe 198 contro 192 nella documentazione del gioco (riguarda il gioco, non l'emulatore).

## Novità API 25
- `runLoop` ritorna `retriesTotal` (totale vero) e `retriesTruncated` (la lista `retries` si ferma a 200 voci: con 300 passi forzati ne mostrava 200, segnalato dalla chat Barbarian). `c64-batch`: `retriesCount` dal totale vero e `retriesTruncated`.
- Documentate le opzioni di prova `_forceRetry`/`_forceEvery` per verificare che un bot sia ripetibile.
- Misura del costo del passo esatto: il tempo in più viene dal core dopo il ripristino (vedi `c64-cli.md` §14).

## Novità API 24
- **Fix (R12)**: con le ripetizioni dei passi esatti la API 23 perdeva joystick e tasti tenuti (il core non li salva nello snapshot) → esiti diversi. Ora: modello degli input riapplicato a ogni ripristino, primo tentativo sempre da stato ripristinato, eventi di tastiera consumati riprogrammati. `type()` dentro `runLoop` non fa avanzare il core e non lascia eventi nella coda del core.
- `saveState(nome)` salva anche gli input tenuti (solo in memoria); `loadState(nome)` li ripristina, `loadState(file/base64)` li rilascia tutti; avviso se c'erano eventi di tastiera ancora programmati (la coda del core non si svuota).
- **R13**: `examples/shell/11-determinismo.sh` riscritto con un bersaglio che legge joystick e tastiera e ripetizioni forzate.
- **R14**: `loadEncoding` accetta simboli (`NOME = valore`, etichette) e blocchi `.enc`; opzione `{block}`.
- **R15**: script `assert text "…" [enc=] [addr=] [len=]`.
- **R16**: `c64-batch` riporta `retriesCount` (con la correzione le ripetizioni non cambiano più l'esito: nessun avviso necessario).

## Novità API 23
- **Passi esatti**: `runFrames` e `runLoop` prendono uno snapshot prima di ogni avanzamento (≈5 ms) e, se il core ha sforato (il browser in ritardo fa calcolare 2 fotogrammi in un colpo: misurato ~1 passo su 800–1000, più spesso con più istanze), ripristinano e ripetono. Bot ad anello chiuso dallo stesso stato ⇒ stesso esito. `runLoop` ritorna `framesActual`, `exact`, `retries`. `{exact:false}` = comportamento precedente. In modalità esatta il primo tentativo salta l'attesa anti-recupero (260 ms), i ripetuti no.
- `loadEncoding(nome, mappa|testo .cdef)`, `encodings()`, `findText(…,{enc,len})`, `runUntil({text,textOpts:{enc,addr,len}})`, script `wait text "…" enc= addr= len=`.
- `headless/c64-batch`: più esecuzioni su più demoni in parallelo (vedi `c64-cli.md` §14).
- Messaggio d'errore per `JOY2-UP&FIRE` negli script: suggerisce `JOY2-UP&JOY2-FIRE`.
- Non fattibili con questo core (misurato): esecuzione sincrona più veloce del tempo reale (nessuna funzione wasm esportata; `SPEED_BOOST` senza effetto), profilatore per routine (servirebbe un aggancio per istruzione: con breakpoint/step costa ≥45 ms per evento), `whenRegs` veloce (`r` della RetroShell mostra solo CIA/VIC/SID, non i registri CPU).

## Novità API 22
- `measure(from,to,{n})`: `n` ripetizioni con `{min,max,mean,samples}`.
- Determinismo verificato (senza il gioco): stesso stato salvato + stesso `runLoop` con un bot che decide leggendo la memoria → stessi cicli e stesso hash `regress`, 3 volte su 3. Se un gioco dà esiti diversi dallo stesso stato, la causa non è nel ciclo `runLoop` in sé; vedi `getting-started.md` §7.
- Esempi: l'output degli script shell va in `$TMPDIR/c64-examples-output` invece che nel pacchetto.

## Novità API 21
- `findText(testo,{map})`: codifica propria del gioco (`{"0-9":45,"/":55}`); funziona anche in `runUntil({text,textOpts:{map,addr}})`.
- `measure(from,to,{timeoutFrames})`: cicli esatti tra due PC (via `runUntil` su breakpoint).
- `runUntil({pc, whenRegs:{a,x,y,p}})`: stop sul PC solo con i registri indicati.
- Client: `c64 games` cerca `games/` anche accanto al repo (non solo nella cartella corrente).
- Verificato che il warp non serve per i cicli passo-passo: dopo `warp(true)` ogni `runFrames` avanza a salti di ~26 fotogrammi (misurato: 2→27, 2→26, 2→52), perciò `runLoop` in warp non è esatto né fine; `runFrames(n,{fast:true})` resta l'unico uso esatto.

## Novità API 20
- `screenCodes({addr})`, `findText(testo,{…,addr})`: `addr` = indirizzo RAM dei 1000 codici schermo (default: quello del VIC da `$D018`/`$DD00`). Se `findText` ritorna `null` su una schermata di gioco, controlla `screenInfo()`: con `bitmap:true` il testo è disegnato come grafica e non esiste nella RAM schermo; altrimenti prova `addr` con l'indirizzo della RAM testo del gioco (`c64 dump`/`screenCodes` per individuarlo). Il demone ha l'opzione `--headed` (vedi `docs/c64-cli.md` §2).

## Novità API 19: correzioni trovate documentando ogni comando (`docs/c64-cli.md`)
- **`reset({hard:true})`** dava `w.wasm_hard_reset is not a function` (usava il nome sbagliato): ora fa davvero spegni/riaccendi (il contatore dei cicli riparte da 0; provato).
- **Il demone andava in crash** se un risultato conteneva un BigInt (es. `c64 wasm wasm_get_cpu_cycles`: `TypeError: Do not know how to serialize a BigInt`): ora i BigInt diventano numeri (stringhe oltre 2^53) e un risultato non serializzabile dà un errore `DAEMON` invece di fermare il demone.
- **`roms()`**: i byte erano sovrastimati di 1 (8193 invece di 8192).
- **Client**: `c64 rom` senza argomenti mostra le ROM utente attive (`roms()` dell'API; `c64 roms` resta l'elenco dei file); `c64 rom KIND NOME` passa il nome del file alla ROM caricata (prima `name:"kernal"`).
- **Documentazione**: `docs/c64-cli.md` (ogni comando), `examples/` (esempi eseguibili). Chiarito che gli oggetti/array JSON non accettano `0x..` come numero, che i dischi si montano con il core in marcia e che `waitFor` ritorna `false` allo scadere.

