# vc64web (emulatore C64 nel browser)

**Cos'è**: porting WebAssembly di VirtualC64 (emulatore C64/1541). In questa cartella c'è il sottoinsieme necessario per girare: `index.html`, `vc64.js`, `vc64.wasm`, `js/`, `css/`, `sounds/` (più `UPSTREAM-README.md`, il README originale). È il componente che viene **incorporato** (in base64) in `portable/VirtualC64-vNN.html` e in `headless/c64-headless.html`: pubblicare uno di quei due file significa pubblicare anche questo codice.

**Origine**: https://github.com/vc64web/vc64web.github.io (checkout usato: commit `469b63818d1a8f4d654fd3985b82aeb4e03fabba`, 28/10/2026). Il core C++ compilato in `vc64.wasm` è VirtualC64 di Dirk W. Hoffmann: https://github.com/dirkwhoffmann/virtualc64

**Licenza**: **non verificata.** Nel checkout non c'è un file di licenza e il README originale non ne parla. Per quanto ne so, VirtualC64 è sotto GPL-3.0 (da conoscenza generale, non controllato qui): da verificare sui due repository prima di pubblicare. Se è GPL, distribuire l'HTML con il wasm incorporato richiede di rendere disponibile il sorgente corrispondente e di mantenere la licenza.

**Librerie incluse in `js/`** (licenze dedotte dalle intestazioni dei file o dalla mia conoscenza, da controllare):
| File | Cos'è | Licenza |
|---|---|---|
| `jszip.min.js` | JSZip 3.10.1 | MIT o GPLv3 (doppia, dichiarato nell'intestazione del file) |
| `eruda.js` | Eruda 3.1.0 (console per mobile) | non verificata (credo MIT) |
| `jquery-3.7.1.min.js` | jQuery 3.7.1 | non verificata (credo MIT) |
| `bootstrap.bundle.min.js` | Bootstrap | non verificata (credo MIT) |
| `cm6/` | CodeMirror 6 bundle + JSHint | non verificata (credo MIT) |

**Modifiche nostre**: nessun file di questa cartella è stato modificato. La build produce una copia modificata dell'`index.html` (rimozione di manifest/analytics, ROM e risorse incorporate) solo dentro gli HTML generati.
