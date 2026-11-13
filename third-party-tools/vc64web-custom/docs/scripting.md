# Scripting — guida al linguaggio di script di c64d

Copyright © 2026 Simone Caporale · versione: `c64.info()`

Uno script è un file di testo che descrive **input a tempo** (tasti, joystick, testo), **attese**, **controlli** (assert, regressione), **modifiche alla memoria** e **registrazioni** (video, input). Gira dentro l'emulatore con tempo emulato esatto: stesso script + stesso stato iniziale = stesso risultato.

```
c64 scriptCheck prova.txt                     # solo validazione (errori con numero di riga)
c64 script prova.txt                          # esegue
c64 --outdir out script prova.txt             # esegue e salva screenshot / video / registrazioni in out/
```
Exit code: 0 = ok, 1 = errore (sintassi, `ASSERT`, `REGRESS`, `TIMEOUT`, `CALL_TIMEOUT`, `ABORTED`, `STALL`, ...). Il messaggio contiene sempre il numero di riga: `ERRORE ASSERT: script riga 12: assert fallito: mem[$0400]=$05, atteso == $06`.
Da JavaScript: `await c64.runScript(testo)` / `c64.scriptCheck(testo)`.

---

## 1. Modello del tempo

- Il tempo è in **fotogrammi PAL** (19656 cicli) dall'inizio dello script, dopo l'attesa automatica del boot (il KERNAL scansiona la tastiera solo dopo ~2,75 M cicli dal reset; `{noWait:true}` la disattiva).
- Riga con tempo: `<N>` = assoluto, `+<N>` = N fotogrammi dopo la riga precedente. Le righe vanno in ordine crescente.
- **Punti di sequenza**: `wait ...` e ogni comando **senza** fotogramma davanti (vedi §4) attendono che gli eventi precedenti (compreso il rilascio dei tasti) siano finiti; poi **il tempo riparte da 0**.
- I comandi possono anche avere un fotogramma davanti (`120 screenshot s1`): in quel caso scattano a quel tempo, senza spezzare il segmento e senza azzerare il tempo (eccetto `loadState`, che vuole la forma senza fotogramma).
- Non ci sono `if`, `goto`, cicli, variabili, `include` (scelta di progetto: per la logica usa JavaScript, vedi §9).

## 2. Input

| Riga | Significato |
|---|---|
| `0 L` | tasto `L` premuto al fotogramma 0 (durata default 3 fotogrammi) |
| `140 O 5` | tasto `O`, premuto 5 fotogrammi (minimo 1) |
| `10 SHIFT+A` · `10 RUN/STOP` · `10 F1` | stessi nomi di `c64.type()` |
| `10 W&D` | tasti simultanei con `&` |
| `300 JOY2-UP 30` | joystick porta 1 o 2: `UP DOWN LEFT RIGHT FIRE`, anche con `&` |
| `0 text "print 6*7\n"` | stringa JSON (`\n` = RETURN), come `sendText`; durata opzionale = fotogrammi per tasto |
| `# ...` | commento (anche a fine riga) |

Tasti e joystick non si mescolano nella stessa riga. `text` blocca lo script finché la stringa è digitata. Un tasto ripremuto a meno di 2 fotogrammi dal rilascio genera un avviso (misurato: pressioni perse).

## 3. Attese

| Riga | Attende |
|---|---|
| `wait 50` | 50 fotogrammi |
| `wait "READY." 5s` | testo a schermo (maiuscole/minuscole indifferenti). Timeout in fotogrammi, o secondi con `s`; default 3000 fotogrammi |
| `wait pc=0xC000 600` | PC all'indirizzo (o etichetta) |
| `wait text "TESTO" 5s` | testo nella RAM schermo come **screen code** (API 18): funziona anche con charset propri; vedi `findText` in C64-API.md |
| `assert text "XP" enc=hud addr=$8400` | (API 24) come `wait text` ma senza attesa: errore `ASSERT` subito se il testo (screen code) non c'è; opzioni `enc= addr= len=` |
| `wait text "LV 21" enc=hud addr=$8400 3000` | (API 23) con codifica caricata (`loadEncoding`), area (`addr=`, anche etichetta) e lunghezza lineare (`len=`) |
| `wait mem=0x02A7 0x03 600` | `mem[addr] == valore` |
| `wait mem=lives 0 &0x0F 10s` | con maschera: `(mem & 0x0F) == (valore & 0x0F)` |
| `wait mem!=0x02A7 0` | `mem[addr] != valore` |

Scaduto il timeout: errore `TIMEOUT` con numero di riga (exit 1). Indirizzi: `0x..`, `$..`, decimale o **etichette** caricate con `c64.loadLabels` (anche `set:nome`). La memoria è letta come la vede la CPU (I/O e ROM visibili secondo `$01`).

## 4. Comandi

Si scrivono da soli (punto di sequenza, poi il tempo riparte da 0) oppure con un fotogramma davanti.

| Comando | Effetto |
|---|---|
| `poke ADDR v1,v2,.. [ram]` | scrive byte (0-255). `ram` = scrive nella RAM sotto ROM/I-O |
| `assert mem=ADDR VALORE [&MASCHERA]` | se falso: errore `ASSERT`, script interrotto. Anche `mem!=` |
| `assert screen "testo"` | il testo deve essere sullo schermo (maiuscole indifferenti) |
| `saveState NOME` · `loadState NOME` | snapshot completo del core in memoria (CPU, RAM, VIC, SID, CIA, drive, disco). `loadState` riporta anche il contatore dei cicli |
| `screenshot FILE` | PNG (estensione `.png` aggiunta se manca), salvato dal client in `--outdir` |
| `regress save NOME` | baseline (hash componenti + RAM + schermo) |
| `regress check NOME [tolerance=N] [ignore=A-B ...]` | confronta con la baseline; se diversa: errore `REGRESS` con le ragioni. `ignore=0x0400-0x07E7` esclude intervalli |
| `call ADDR [a=N] [x=N] [y=N] [timeout=N] [nowait]` | JSR a una subroutine e ritorno (registri e PC ripristinati); registri d'uscita nel campo `log` del risultato | Con `nowait` (API 18) salta alla routine senza attendere il ritorno: per routine che non tornano (cambio livello); il core continua da lì. Se la routine non ritorna e manca `nowait`: errore `CALL_TIMEOUT`.
| `video start [NOME] [every=N] [scale=N] [crf=N] [keep]` | inizia a registrare un video mp4 (vedi §5) |
| `video stop` | chiude il video |
| `rec start [NOME] [keep]` · `rec stop` | registra gli input dello script come script di testo (vedi §6) |

I nomi (stati, baseline, file) possono contenere solo lettere, cifre, `_`, `.`, `-`. Stati e baseline vivono nella pagina finché il demone resta acceso: possono essere riusati fra script diversi.

## 5. Video: `video start` / `video stop`

```
video start intro every=2 scale=3          # intro.mp4, 25 fps, 1152x810
...
video stop
```
- Cattura **deterministica**: uno screenshot ogni `every` fotogrammi emulati (default 2 → 25 fps; `fps = 50/every`), codificato da ffmpeg nel demone. Il video non dipende dalla velocità del computer.
- `scale` 1-4 (ingrandimento intero con pixel nitidi, default 3; 4 = 1536×1080), `crf` 0-51 (qualità H.264, default 20, più basso = migliore).
- **Requisiti**: demone `c64d` con `ffmpeg` nel PATH e **emulatore fermo** (`c64 pause`). Chiamando `runScript` direttamente da JavaScript senza demone: errore `NO_RECORDER`.
- Un solo video attivo alla volta (un secondo `video start` senza stop è un errore di sintassi).

### Parametro di chiusura: autostop (default) o `keep`
| Forma | Cosa succede alla fine dello script |
|---|---|
| `video start clip` (= `autostop`) | **la chiusura è garantita**: se non c'è un `video stop`, il video viene chiuso alla fine dello script, **anche se lo script termina con un errore** (il file parziale viene comunque salvato) |
| `video start clip keep` | il video **resta aperto** dopo lo script e continua a registrare ogni fotogramma emulato delle chiamate successive (`runFrames`, altri script, ...). Si ferma a mano: `c64 --out clip.mp4 videoStop`, oppure con `video stop` in un altro script (in questo caso il file esce fra gli `outputs` di quello script) |

Con `keep` il risultato dello script contiene `"videoOpen": "clip.mp4"`. Se lo script che ha lanciato un `keep` fallisce, il video resta aperto (chiuderlo con `videoStop`).
Senza il file di destinazione `--out`/`--outdir` il client non salva nulla: ricordarsi di passarlo.

## 6. Registrazione degli input: `rec start` / `rec stop`

Registra gli eventi di input eseguiti da quel punto (tasti, joystick, `text` dello script e le chiamate API di input fatte dopo con `keep`) e li esporta come **script di testo** rieseguibile (`recordStop({format:'text'})`).
```
rec start sessione           # sessione.txt
...
rec stop                     # (o autostop a fine script; con keep resta attiva)
```
Stessa regola di chiusura: default = chiusa a fine script (anche in caso di errore); `keep` = resta attiva e si chiude con `c64 recordStop '{"format":"text"}'`. Gli eventi non esprimibili come riga di script (es. `poke`) finiscono come commento `# non esportato`. Verificato: l'esportazione di tasti, joystick e `text` si rilegge senza errori con `scriptCheck`.
Ricorda che il tempo esportato è relativo all'inizio della registrazione.

## 7. Risultato e file prodotti

`runScript` ritorna `{events, frames, warnings, outputs?, log?, videoOpen?, recOpen?}`.
- `outputs`: screenshot, video, registrazioni (con i dati binari). Il client `c64` li scrive in `--outdir` (default: cartella corrente), con il solo nome base del file, e li toglie dal JSON stampato.
- `log`: risultati di `call` e `regress check`.
- In caso di errore il client scrive comunque i file già prodotti (anche il video parziale) prima di uscire con 1.

## 8. Esempi pratici

### 8.1 Caricare e avviare un programma
```
wait "READY." 10s
0 text "load\"*\",8,1\n"
wait "READY." 30s
0 text "run\n"
wait 200
screenshot avvio
```

### 8.2 Test di un gioco: salvare lo stato dopo il menu, poi provare mosse diverse
```
# prepara.txt  (si esegue una volta)
wait "PRESS FIRE" 20s
0 JOY2-FIRE 5
wait mem=0x0800 1 30s          # 1 = livello caricato (indirizzo di esempio)
saveState livello1
```
```
# prova_salto.txt
loadState livello1
0   JOY2-RIGHT 40
+10 JOY2-FIRE 6
wait 60
assert mem=0x0801 0x03          # es. flag "in aria" = 3
screenshot salto
```
Un `loadState` al posto del reset rende ogni prova indipendente e velocissima.

### 8.3 Forzare una condizione e verificare l'effetto
```
loadState livello1
poke 0x0802 99                  # vite = 99 (indirizzo di esempio)
0 JOY2-LEFT 30
wait 100
assert mem=0x0802 99            # le vite non devono cambiare camminando
assert screen "SCORE"
```

### 8.4 Regressione dopo una modifica del codice
```
# 1) con la versione buona
loadState livello1
0 JOY2-RIGHT 100
wait 50
regress save camminata
```
```
# 2) con la versione nuova (stesso stato di partenza)
loadState livello1
0 JOY2-RIGHT 100
wait 50
regress check camminata ignore=0x0400-0x07E7 ignore=0xD800-0xDBE7
```
`c64 script ...; echo $?` → 0 se uguale, 1 se diverso: usabile in CI.

### 8.5 Chiamare una routine del programma
```
loadState livello1
call 0xC000 a=3                 # JSR $C000 con A=3
call spriteInit x=1 y=2         # con etichetta (loadLabels)
```
Il risultato (a, x, y, p all'uscita) è in `log`.

### 8.6 Video di una sessione, chiusura garantita
```
video start demo every=2 scale=3
wait "READY." 10s
0 text "10 for i=1 to 5:print i:next\n"
+80 text "run\n"
wait 150
```
Termina senza `video stop`: `demo.mp4` viene chiuso comunque a fine script.
```
c64 pause ; c64 --outdir out script demo.txt
```

### 8.7 Video che continua oltre lo script (`keep`) e chiusura a mano
```
video start lungo keep
wait "READY." 10s
0 text "run\n"
```
```
c64 script avvia.txt                       # -> "videoOpen":"lungo.mp4"
c64 runFrames 500                          # registrati anche questi
c64 sendText 'print 1\n'
c64 --out lungo.mp4 videoStop              # ferma e salva
```

### 8.8 Più clip in un solo script
```
video start parte1 every=2
...
video stop
loadState livello2
video start parte2 every=1 scale=2
...
video stop
```

### 8.9 Registrare le proprie mosse e rigiocarle
```
rec start mosse keep
```
poi si gioca via API (`c64 type ...`, `c64 joy ...`) e infine:
```
c64 recordStop '{"format":"text"}' --compact     # testo dello script, rieseguibile con c64 script
```

### 8.10 Attendere un testo del gioco (screen code) e saltare in una routine che non ritorna
```
loadState villaggio
wait text "LORD OF RUIN" 10s          # cerca in screen code: vale anche con charset propri (API 18)
0 call 0xC000 a=20 x=0 nowait        # salta a una routine che non ritorna (es. cambio livello); il core continua da lì
wait 60
screenshot dopo_cambio
```
`wait text` non vede glifi grafici né testo disegnato sulla bitmap. `call` senza `nowait` su una routine che non ritorna termina con `CALL_TIMEOUT`.

### 8.11 Interrompere uno script o un job in corso
Da un altro terminale: `c64 abort` interrompe il job in corso (lo script termina con `ABORTED`, l'emulatore resta fermo; i file già prodotti, video parziale compreso, vengono comunque consegnati: provato con `video start`, exit 1), `c64 status` mostra job e avanzamento. Se il client `c64` viene chiuso o ucciso, il demone interrompe da solo il suo job.

## 9. Quando serve la logica

Per condizioni, cicli e decisioni che dipendono dallo stato usa JavaScript con l'API (`runUntil`, `screenText`, `peek`, `runLoop` in pagina). Un'ottima combinazione: lo script di testo per le sequenze di input e un `.js` per la logica.

## 10. Limiti e cose non verificate

- **Audio nel video deterministico: non disponibile** (per audio in tempo reale vedi `grabBrowserVideoAndAudio` in C64-API.md: si può avviare prima e fermare dopo uno script, con il pannello joystick/tastiera). Il core espone un buffer di campioni, ma nelle misure fatte (100 fotogrammi) i campioni ricevuti erano ~79k invece di 88,2k attesi a 44,1 kHz, con ampiezza quasi nulla, e il comportamento cambia se si apre l'audio principale: non è deterministico, quindi non viene registrato. Il video è muto.
- Il video richiede emulatore fermo; con emulatore in tempo reale `video start` dà errore.
- Provato: poke, assert (ok e fallito), `wait mem=` (ok e timeout), saveState/loadState, screenshot, regress save/check (uguale e diverso), call, video autostop, video `keep` + `videoStop`, `rec`. **Non provato**: script molto lunghi, `assert`/`wait mem=` in tempo reale con tempi lunghi, `wait mem=` in modalità warp, video `keep` di molti minuti (memoria/ffmpeg), Docker (mai costruito qui).
