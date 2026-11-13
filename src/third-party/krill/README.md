# Krill's Loader, Repository Version 194

Copyright © 2026 - Simone Caporale (note); il loader è © 2022 Gunnar Ruthenberg ("Krill"/Plush).

| | |
|---|---|
| File | `loader-v194.zip` (archivio ufficiale, non modificato) |
| Versione | Repository Version 194 |
| Data di rilascio | 24 novembre 2022 |
| Autore | Krill (Gunnar Ruthenberg), Plush — `Krill@Plush.de` |
| Fonte | CSDb, "Krill's Loader, Repository Version 194 by Plush (2022)": https://csdb.dk/release/?id=226124 |
| Documentazione | dentro lo zip: `loader/README` (uso, configurazione, limiti, licenza), `loader/docs/Protocol.txt`, `loader/include/config.inc`, `loader/include/loader.inc`, `loader/samples/*` |
| Licenza | BSD a 3 clausole **con attribuzione obbligatoria**: "Loader by Krill" nella produzione e/o nella documentazione che la accompagna (il solo sito web non basta). Testo completo in `loader/README`, sezione License. Strumenti e decompressori di terzi (`loader/tools`, `loader/src/decompress`) hanno le loro licenze. |

Lo zip sta qui **compresso** e **non si scompatta nel repository**: la build lo scompatta nella cartella usa e getta
`out/krill/` e da lì costruisce loader, plugin di salvataggio e `cc1541` (vedi `docs/FastLoader.md`).

## Commenti dal sito (CSDb), conservati come informazione

- **alwyz, 6/10/2026**: bug su 1581: un file il cui primo blocco è sulla traccia 80 non si carica; corretto cambiando un byte
  (che controlla il caso) nell'immagine del disco 1581 dell'autore del commento. Non usato dal gioco (solo 1541).
- **Krill, 14/9/2024**: la prossima versione cambia solo il formato dei bit-stream compressi (puntatore di destinazione da
  big-endian a little-endian, bit di controllo spostati a sinistra byte per byte), con alcune correzioni e funzioni nuove.
  La r194 qui è quindi **più vecchia** di una versione successiva.
- **Burglar, 14/9/2024**: questa versione supporta Dali 0.3 ma **non** Dali 0.3.2; meglio usare solo i compressori inclusi
  (`make tools` in `loader`). Il gioco non usa i compressori del loader (carica file non compressi).
- **Krill, 24/11/2022**: per SD2IEC usare il firmware https://github.com/thierer/sd2iec, che supporta questo loader.

## Note di costruzione trovate sul campo (11/11/2026, cc65 2.18 Ubuntu 2.19-1)

- Costruisce con `ca65`/`ld65`, `make`, `perl`, `gcc` (per `tools/cc1541`).
- `make clean` cancella anche la cartella `build/intermediate`: ricrearla (`mkdir -p build/intermediate`) prima di ricostruire.
- Il target `save` si lancia da `loader/src` e **con la configurazione di default fallisce** su questa versione di `ca65`:
  `save.s(716): 1581 save code below loadfile81 position` (`loadfile81` è a `$0596` invece di `$0594`; fallisce anche l'esempio
  `samples/save`). Con `ONLY_1541_AND_COMPATIBLE = 1` il codice 1581 non c'è e il target passa senza modifiche.
  Per costruire il plugin con tutti i drive bisognerebbe cambiare `.org $0594` in `.org $0596` in `save.s` (non provato su 1581).
- Misure (configurazione del gioco, `PLATFORM=c64`): vedi `docs/FastLoader.md`, sezione "Misure".
