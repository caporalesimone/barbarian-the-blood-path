# VirtualC64 (v10, API 10): cosa manca

Copyright © 2026 Simone Caporale

Legenda: [V] da verificare (esiste ma non provato), [F] fattibile (so che il core lo offre), [?] non so se fattibile, [L] limite del core (non risolvibile da qui).

## 1. Da verificare su quanto già fatto
- [V] Breakpoint e watchpoint dopo `loadState`: sopravvivono? Oggi vanno ricontrollati a mano.
- [V] `type`/`sendText` in tempo reale: provati (GET, F1, SHIFT+A, W+D, stringhe di ~130 caratteri), stesso esito dell'emulatore fermo. Non provati: browser in background (timer rallentati), warp, NTSC.
- [V] `{LEFT}` a 9 fotogrammi da `{UP}` perso in un programma BASIC con GET (API 6, con default 3/2): non riprodotto con i nuovi default 3/3; causa non nota. Con rilascio di 1 fotogramma gli errori sono misurati (pressione 3–4: 1 prova su 8 corretta), il meccanismo non è chiarito.
- [V] `replay` con emulatore in corsa (tempo reale): non esatto per costruzione, non misurato.
- [V] Demone `c64d`: sessioni lunghe (ore), più client insieme, memoria di Chromium.
- [V] `storeSet/storeGet` tra build con nomi file diversi: provato solo in Chromium; Firefox e Safari no.
- [V] NTSC: i fotogrammi sono tarati su PAL (19656 cicli), niente prova con NTSC.
- [V] Telefono: il file HTML non è stato provato su un telefono reale con questa API (solo Chromium headless).
- [V] `type`/`sendText` perdono i tasti quando il C64 non legge la tastiera (interruzioni disattivate, LOAD in corso): non rilevabile dall'esterno, si attende il prompt. (Boot dopo reset: risolto in API 8.)
- [V] Fantasmi della matrice (3 tasti ai vertici di un rettangolo) e interferenza joystick/tastiera: non so se il core li emula; non verificato. Con più tasti simultanei il KERNAL (`GET`) riporta un solo tasto.
- [V] Tempi minimi dei tasti (pressione 1, rilascio 2) misurati nel BASIC con 8 sfasamenti; non su altri programmi o con tastiere lette meno di una volta per fotogramma.

## 2. Funzioni non fatte
- [F] Breakpoint condizionali con registri (oggi `when` controlla solo la memoria). Richiede la lettura dei registri a ogni stop.
- [F] `step`/`trace` con registri A/X/Y/P/SP per istruzione (oggi solo pc/byte/asm/cicli): il registro stampato dal shell ha i nibble invertiti, serve un'altra via (stub 6502 che altera i cicli).
- [F] Cambio PAL/NTSC dall'API (probabilmente `wasm_configure`, non provato).
- [F] Esporta/Importa impostazioni dell'interfaccia (JSON) nel menu; oggi c'è solo `store*` via API.
- [F] Test automatici dell'API nel repository (oggi gli script di prova stanno nello scratchpad).
- [?] Audio: `wasm_get_sound_buffer_address` / `wasm_copy_into_sound_buffer` esistono; non so se si può registrare un WAV in modo ripetibile (il core produce campioni solo mentre gira).
- [?] CPU e memoria del drive 1541: `? drive8` dà lo stato; non ho verificato se il debugger legge la RAM del drive (servirebbe per capire Krill).
- [?] Cartucce, REU, nastro (`wasm_press_play`...): il core li gestisce, non toccati.
- [?] Mappa degli accessi alla memoria (heatmap) come copertura del codice: l'opzione `HEATMAP` non si attiva con `wasm_configure`; altre vie non cercate.
- [?] Registrazione in tempo reale come alternativa al replay a fotogrammi.

## 3. Limiti del core (non risolvibili da qui)
- [L] Granularità minima: 1 fotogramma (19656 cicli); `runCycles` arrotonda per eccesso.
- [L] Il warp rompe l'esattezza dei fotogrammi.
- [L] Solo la famiglia 1541 (1540/1571/1581 rifiutate come "Unknown ROM").
- [L] `wasm_rewind` riavvolge il nastro, non lo stato; il core non ha un buffer delle istruzioni passate oltre alle ultime 8 che il shell mostra.
- [L] `wasm_sprite_info` dà solo x,y; il resto si legge dai registri.
- [L] I comandi `f` e `m` del shell non accettano gli argomenti provati; `find` è fatto in JS.
- [L] Dopo una pausa di 15–260 ms il core recupera fino a 3 fotogrammi: `runFrames` attende 260 ms (≈0,3 s per chiamata).
- [L] Non è VICE: i risultati sui cicli vanno confermati in VICE nativo.

## 4. Idee (non richieste)
- Variante di `c64d` con CDP diretto, senza Playwright (proposta e declinata il 12/11).
- (fatto in API 10: `regressSave/regressCheck`.) Da verificare: baseline su più sessioni/daemon riavviato; confronto con tolleranza per schermi con sprite animati.
- Video deterministico (PNG fotogramma per fotogramma + ffmpeg lato Node) e audio: non fatti; `recordVideo` è in tempo reale, solo Chromium verificato.

## Struttura (da API 10, build 11)
- `VirtualC64-v11.html` = solo emulatore + interfaccia, nessun controllo remoto.
- `c64-headless.html` = pagina minima per il demone (solo emulatore, nessuna interfaccia); `c64-api.js` viene iniettato dal demone.
- Da verificare: uso manuale di `c64-api.js` incollato nella console della pagina standalone (la pagina non ha più `window.c64`, ma l'iniezione dovrebbe funzionare perché usa le stesse variabili globali; non provato).
- Il guadagno di `c64-headless.html` è soprattutto a runtime (niente UI/CSS/layout): la dimensione è quasi uguale (~4,0 MB, dominata da wasm e ROM).

## Script di input (API 11)
- Non fatti per scelta: if/goto/cicli/variabili/include (per la logica: JavaScript con l'API).
- Da fare se serve: esportare le registrazioni (`recordStop`) in formato testo; verificare script molto lunghi e `wait pc=`.

## Docker
- Dockerfile e docker-compose.yml NON provati: nell'ambiente di sviluppo non c'era il demone Docker. Provati solo il demone con C64_HOST=0.0.0.0 e C64_NO_SANDBOX=1 e il client con --host.
- Da verificare: build (playwright@1.63.0 + `playwright install --with-deps chromium` su node:22-bookworm-slim), healthcheck, uso con --shm-size=1g.

## Dopo la valutazione del 12/11 (todo-emulatore-web.md della chat Barbarian), build 17 / API 14
Fatto: ciclo in pagina (`runLoop`), `runFrames({fast})` esatto con il warp, video deterministico con input (`c64 video`), insiemi di etichette, `runUntil({screenMatch})`, `driveTrace`, `recordStop({format:'text'})` (parziale), `--quiet`/`--compact`, nome programma minuscolo, `stateHash` senza CPU. Stati su file: già possibile (documentato).
Non fatto: audio (video e WAV), più istanze in parallelo, profilatore per routine (cicli per etichetta), breakpoint condizionali su registri / `step` con A/X/Y/P.
Da verificare:
- `video` su durate lunghe (decine di minuti) e con `every:1`; ffmpeg lato demone (nel Docker è installato nel Dockerfile, non provato).
- `runFrames({fast})` su un disco reale con Krill (provato solo su BASIC/schermata di avvio).
- `recordStop({format:'text'})`: i `joy` a stato e `sendJoy` non sono esportati; il tempo parte dall'inizio della registrazione.
- Warp: il primo `runFrames` dopo `warp(false)` avanza di ~26 fotogrammi di troppo (misurato in un caso); la causa nel core non è nota.
- `runLoop`: ~25 passi/s a 2 fotogrammi (tempo reale); più veloce solo con warp (non esatto).

## Script e video (build 19, API 15)
- [V] Non provati: script molto lunghi; `assert` e `wait mem=` in tempo reale con tempi lunghi; `wait mem=` in warp; video `keep` di molti minuti (memoria della coda, ffmpeg); script con errore mentre un video `keep` è aperto (resta aperto: chiudere con `videoStop`).
- [V] Docker: Dockerfile/compose aggiornati (volumi `scripts/` e `out/`, scripting.md) ma MAI costruiti né provati (nessun demone Docker disponibile qui).
- [L] **Audio nel video**: non fatto. Il core (`wasm_copy_into_sound_buffer[_stereo]`) restituisce blocchi da 1024 campioni; in 100 fotogrammi ~79k campioni invece di 88,2k (44,1 kHz), ampiezza ~0,002 con un tono SID acceso, comportamento diverso dopo `wasm_open_main_thread_audio`. Causa non indagata. Alternativa non provata: sintetizzare il SID offline dai registri (`sidTrace`) con un modello SID in JS (lavoro grande, risultato diverso da reSID).
- [F] `call` con parametri sullo stack o con scratch diverso; `assert pc=`; `wait` composti (testo OR mem): non fatti.

## grabBrowserVideoAndAudio (build 22, API 16)
- [V] Non provati: registrazioni lunghe (memoria dei blocchi nel browser), deriva audio/video, pannello con tastiera/joystick virtuali della pagina, audio disattivato dalla pagina, tutte le combinazioni di `keyboard`/`joy1`/`joy2` (provate: tutte below, tutte overlay, solo joy2 overlay, kb below+joy1 overlay, joy1+joy2 overlay, kb+joy2 overlay, joy1 below+joy2 overlay).
- [F] Non fatto: pannello con CRSR su/sinistra (mostra SHIFT + CRSR giù/destra), FIRE/joystick del tasto per-porta con più direzioni, conversione automatica in mp4 lato demone.

## ROM e struttura (build 23, API 17)
- [V] `third-party/*/README.md`: licenze di vc64web, PXLfont e diritti di ridistribuzione delle ROM Commodore NON verificati (scritto nei README).
- [V] ROM drive: provate solo 1541 e 1541-II; 1540/1551/2031 bloccate in LOADING (prova interrotta); 1570/1571/1581 rifiutate dal core.
- [?] JiffyDOS / SpeedDOS / Dolphin DOS e cartridge (Final Cartridge, Action Replay, Epyx FastLoad): non forniti (proprietari); non verificato se il core le accetta. Dolphin/SpeedDOS richiedono il cavo parallelo (porta utente), che il core non emula (da conoscenza generale, non verificato).
- [V] Docker con la nuova struttura (`COPY headless/ docs/ third-party/vice-roms`): mai costruito.

## Repo e build (build 24)
- [V] `build.py` con Docker: mai eseguito qui (nessun demone Docker); provate solo la generazione di `out/` e il demone.
- [V] `game NOME` per `.crt`/`.t64`/`.prg` usa `loadFile` (documentato come supportato dall'API): non provato con cartucce reali; i `.d64` sì (attach).
- [V] Versione minima di Node non verificata (provato con la 22).
- [?] Il headless potrebbe leggere l'emulatore direttamente da `third-party/vc64web` senza pagina generata: non fatto (la pagina in `out/` incorpora wasm e ROM).
