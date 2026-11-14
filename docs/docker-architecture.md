# Architettura Docker

Copyright © 2026 - Simone Caporale (note)

Come sono fatte le immagini e i container del progetto, chi dipende da chi, e come si parlano. Aggiornato al 14/11/2026 (versione 1.239).
Per l'uso pratico (comandi, prerequisiti) vedi [getting-started.md](getting-started.md); per i dettagli di ciascuna immagine
[toolchain/README.md](../toolchain/README.md).

**Legenda delle affermazioni**: *[misurato]* = verificato con una prova; *[dal codice]* = letto negli script o nel Dockerfile, non rieseguito
per questo documento; *[non verificato]* = ipotesi.

## 1. Due livelli: immagini e container

- **Immagini** (si costruiscono una volta, `toolchain/images.sh`): modelli di sola lettura. Sono 5: quattro generiche (`c64-*`, nella
  cartella `toolchain/`, che non sa nulla del gioco) e una del gioco (`barbarian-manual`).
- **Container** (nascono e muoiono a ogni comando): quasi tutti con `--rm`. **Nessuno è sempre acceso**: dipendono da cosa chiedi a
  `build.sh` o a `viewer.sh`. Il progetto sta sull'host e si monta in `/work`.

## 2. Immagini e parentela

Un solo Dockerfile multi-stage (`toolchain/docker/Dockerfile`) produce tre immagini; `vc64web` ha un Dockerfile a parte; il manuale ne ha uno nel progetto.

```mermaid
flowchart TD
    UB["ubuntu:24.04<br/>(ARG UBUNTU: unico punto da cambiare)"] --> BASE["stage base<br/>CA + locale + /work<br/>senza nome, non si avvia mai"]

    BASE --> TB["stage tools-builder<br/>compilatori e librerie -dev"]
    TB --> VB["stage vice-build<br/>compila VICE 3.10"]
    TB --> ZB["stage zx0-build<br/>compila ZX0"]
    TB --> CB["stage cc1541-build<br/>compila cc1541 (da Krill)"]

    BASE --> BLD["c64-builder<br/>64tass, cc65, make, perl, zip, git,<br/>Python + Pillow/PyYAML/NumPy/Matplotlib"]
    ZB -. "copia /opt/c64/bin/zx0" .-> BLD
    CB -. "copia /opt/c64/bin/cc1541" .-> BLD

    BLD --> EVICE["c64-emu-vice<br/>+ gtk3, Xvfb, ffmpeg"]
    VB -. "copia /opt/vice (x64sc, c1541, share)" .-> EVICE

    BASE --> VN["stage viewer-node<br/>npm + modulo nativo pulseaudio2"]
    BASE --> VW["c64-emu-viewer<br/>Xvnc (KasmVNC) + PulseAudio + server Node"]
    VN -. "copia node_modules" .-> VW

    BLD --> MAN["barbarian-manual<br/>+ WeasyPrint (tools/manual/Dockerfile)"]

    NODE["node:22-bookworm-slim"] --> VC["c64-emu-vc64web<br/>Playwright + Chromium + ffmpeg<br/>(toolchain/vc64web-custom/Dockerfile)"]

    classDef gen fill:#e8f0ff,stroke:#4a6fb5;
    classDef game fill:#fff0e0,stroke:#b5834a;
    classDef stage fill:#f2f2f2,stroke:#999,stroke-dasharray:4 3;
    class BLD,EVICE,VW,VC gen;
    class MAN game;
    class BASE,TB,VB,ZB,CB,VN stage;
```

Linea tratteggiata = si copia solo il risultato: **i compilatori non finiscono mai nelle immagini finali** (restano nella cache di BuildKit).
Linea piena = `FROM`, cioè si ereditano tutti i layer.

| Immagine | Target / Dockerfile | Cosa contiene | Dimensione [misurato 14/11] |
|---|---|---|---|
| `c64-builder` | `builder` | 64tass, cc65, make, perl, zip, git, Python, zx0, cc1541 | 868 MB |
| `c64-emu-vice` | `emu-vice` | il builder + VICE 3.10 (gtk3), Xvfb, ffmpeg | 1553 MB |
| `c64-emu-viewer` | `viewer` | Xvnc di KasmVNC 1.5.2, PulseAudio, Node + `server.js` | 780 MB |
| `c64-emu-vc64web` | `toolchain/vc64web-custom/Dockerfile` | Node, Playwright, Chromium, ffmpeg, demone dell'emulatore nel browser | 2116 MB |
| `barbarian-manual` | `tools/manual/Dockerfile` | il builder + WeasyPrint 70 | 937 MB |

Conseguenze della struttura:
- **Layer condivisi** [misurato 13/11]: `c64-builder`, `c64-emu-vice` e `c64-emu-viewer` hanno gli stessi layer fino a `base`, quindi occupano
  disco una volta sola per la parte comune. `vc64web` parte da un'altra base e non condivide nulla.
- **Cambiare Ubuntu**: `ARG UBUNTU` in un solo punto, poi `toolchain/images.sh --force` ricompila tutto (VICE, zx0 e cc1541 compresi) sulla base nuova.
- **`barbarian-manual`** eredita dal builder (`FROM c64-builder`): per questo `images.sh` non lo costruisce, lo fa `build.sh` (funzione `manual_image`).
- **Sorgenti scaricati sull'host, non nel build**: il tarball di VICE e il `.deb` di KasmVNC li scarica `images.sh` con `curl` dell'host
  (certificati e proxy del computer) in `toolchain/vice/download/` e `toolchain/kasmvnc/download/`, e li passa al Dockerfile come *build context*
  (`--build-context vicesrc=...`, `kasmvnc=...`; anche `zx0src` e `krill`). Un eventuale proxy che intercetta TLS entra come segreto
  (`C64_CA_BUNDLE`) solo per le build che usano npm.
- Le pagine di `vc64web` si generano **nel builder** (`build.py`) e poi entrano nell'immagine come build context `pages`.

## 3. Container a runtime

Chi li avvia: `build.sh` (build e test), `toolchain/run.sh` (qualsiasi comando in un'immagine) e `toolchain/viewer.sh` (viewer e VICE dal vivo).

```mermaid
flowchart LR
    subgraph HOST["Host (sh, Docker, git, curl)"]
        BSH["build.sh"]
        VSH["viewer.sh"]
        PROJ[("progetto<br/>→ /work")]
        OUT[("out/")]
    end

    subgraph NETC["rete Docker «c64» (creata da build.sh)"]
        TEST["container di test<br/>c64-emu-vice<br/>(tests/run_tests.sh)"]
        VC64["c64-emu-vc64web<br/>demone su :7064<br/>(solo se --emu o --release)"]
    end

    BLDC["c64-builder<br/>(solo durante la build)"]
    MANC["barbarian-manual<br/>(--manual, --release)"]

    subgraph VOL["volume «c64-x11» → /tmp/.X11-unix"]
        XSOCK(["socket X: X99<br/>socket audio: pulse"])
    end

    VIEW["c64-emu-viewer<br/>:6080 su 127.0.0.1<br/>(--view, viewer.sh start)"]
    PLAY["c64-emu-vice<br/>play.sh: VICE dal vivo<br/>(viewer.sh exec)"]
    BR(["browser"])

    BSH -->|"1. docker run"| BLDC
    BSH -->|"2. docker run"| TEST
    BSH -->|"docker run -d"| VC64
    BSH -->|"--manual / --release"| MANC
    BSH -->|"--view"| VSH
    VSH -->|"start"| VIEW
    VSH -->|"exec"| PLAY

    PROJ -. "montato" .-> BLDC
    PROJ -. "montato" .-> TEST
    PROJ -. "montato" .-> MANC
    PROJ -. "montato" .-> PLAY
    OUT -. "sola lettura → /srv/out" .-> VIEW

    TEST -->|"HTTP EMU_URL=http://c64-emu-vc64web:7064"| VC64

    VIEW --- XSOCK
    TEST -. "solo con --view" .- XSOCK
    PLAY --- XSOCK
    BR -->|"http://localhost:6080"| VIEW
```

Chi crea cosa:

| Comando | Container che nascono (in ordine) |
|---|---|
| `./build.sh` | `c64-builder` (build) → container di test su `c64-emu-vice` (smoke + sanity) |
| `./build.sh --no-test` | solo `c64-builder` |
| `./build.sh --emu` | come sopra, più `c64-emu-vc64web` (demone, spento a fine comando) |
| `./build.sh --view` | come sopra, più `c64-emu-viewer` (resta acceso dopo la fine) e il test sul suo schermo |
| `./build.sh --manual` | solo `barbarian-manual` |
| `./build.sh --release` | tutto: `--emu`, tutti i test, `barbarian-manual`, poi `c64-builder` per il pacchetto |
| `toolchain/viewer.sh start` | `c64-emu-viewer` |
| `toolchain/viewer.sh exec tools/vice/play.sh` | `c64-emu-viewer` se non c'è, poi `c64-emu-vice` con VICE dal vivo e audio |
| `toolchain/run.sh builder …` | un container `c64-builder` per quel comando |

Il container di test e quello di `play.sh` sono lo stesso tipo di immagine (`c64-emu-vice`) con parametri diversi. [dal codice]

## 4. Reti, volumi, porte

| Risorsa | Chi la usa | A cosa serve |
|---|---|---|
| Rete `c64` | il container di test, `c64-emu-vc64web` | i test raggiungono il demone `vc64web` per nome (`http://c64-emu-vc64web:7064`). Il demone **non** pubblica la porta sull'host |
| Volume `c64-x11` | `c64-emu-viewer`, container VICE collegati allo schermo | contiene il socket X (`X99`) e il socket audio (`pulse`) |
| `/work` | quasi tutti | il progetto dell'host, con l'utente (uid/gid) dell'host |
| `/srv/out` | solo `c64-emu-viewer`, **in sola lettura** | la cartella `out/` mostrata dal viewer |
| Porta `127.0.0.1:6080` | `c64-emu-viewer` | unica porta pubblicata: **solo localhost** (HTTP e WebSocket) |

Il viewer **non** sta sulla rete `c64`: parla con gli altri container solo attraverso il volume `c64-x11`. [dal codice: `viewer.sh` non passa `--network`]

Variabili d'ambiente del viewer: `VIEW_PORT` (6080), `VIEW_PASSWORD` (facoltativa, protegge tutto), `VIEW_SIZE` (1280x1000), `C64_VIEW_DISK` (disco proposto per primo nell'indice).
Per i container emulatori: `EMU_URL`, `C64_VIEW`, `DISPLAY`, `PULSE_SERVER`.

## 5. Dentro il viewer: video, audio, tasti

Non c'è un flusso video «tra container»: VICE è un normale client X e disegna direttamente sullo schermo X dell'altro container, perché
il socket Unix sta nel volume condiviso. Il resto è del viewer.

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser<br/>(client KasmVNC + overlay)
    participant N as server.js (Node)<br/>:6080
    participant X as Xvnc :99<br/>(KasmVNC)
    participant P as PulseAudio<br/>(scheda «c64»)
    participant V as VICE<br/>(container c64-emu-vice)

    Note over V,X: volume c64-x11: socket X99 e socket «pulse»
    V->>X: richieste di disegno (protocollo X, socket Unix)
    X-->>N: aggiornamenti dello schermo (RFB su WebSocket 127.0.0.1:6901)
    N-->>B: inoltrati tali e quali su /websockify
    V->>P: audio PCM (socket «pulse»)
    P-->>N: monitor della scheda «c64» (PCM s16le stereo 44100 Hz)
    N-->>B: /audio (WebSocket), riprodotto con WebAudio (~30 ms di margine)
    B->>N: tastiera fisica → /websockify
    N->>X: inoltrata tale e quale
    B->>N: overlay (tastiera C64, Joy 1, Joy 2) → /input
    N->>X: tasti iniettati come secondo client RFB
    X->>V: eventi tasto sulla finestra sotto il puntatore
```

Il server Node ha una sola porta e queste rotte [dal codice, `server.js`]:

| Rotta | Contenuto |
|---|---|
| `/`, `/live.html`, `/config.js` | indice, schermo dal vivo con overlay e audio, disco proposto |
| `/vnc/` | il client web di KasmVNC (file del pacchetto ufficiale) |
| `/websockify` | WebSocket verso Xvnc, byte passati senza modifiche |
| `/audio` | WebSocket con l'audio (registrazione di `c64.monitor`, un solo flusso finché c'è almeno un ascoltatore) |
| `/input` | WebSocket dei tasti dell'overlay (`d <keysym>`, `u <keysym>`, `f`) |
| `/out/` | la cartella `out/` del progetto, in sola lettura, con elenco dei file |

Con `VIEW_PASSWORD` impostata, **tutte** le rotte chiedono HTTP Basic, WebSocket compresi [misurato 14/11: `/input` risponde 401 senza password o con password errata].

Particolarità di KasmVNC emerse durante il lavoro (se tocchi `/input` ti servono) [misurato]:
- Xvnc accetta il WebSocket solo con l'intestazione `Origin`, altrimenti risponde 404.
- Il `PointerEvent` è di **11 byte** (maschera da 2 byte più due scorrimenti), non 6 come nell'RFB standard: con il formato standard
  il server chiude la connessione (`invalid pixel format`) e i tasti dopo il primo puntatore vanno persi.
- Un tasto del tastierino numerico mandato come keysym `KP_8` fa accendere a Xvnc il NumLock da solo: il joystick 2 non dipende quindi dal NumLock del browser.
- `-PublicIP 127.0.0.1` è obbligatorio, altrimenti Xvnc interroga server STUN su Internet prima di aprire la porta web.

Misure di latenza [misurato 14/11, browser headless sulla stessa macchina]: immagine ~55 ms, audio ~41 ms, audio e immagine entro ~15 ms.
In un browser reale e su una macchina diversa **non** sono state misurate.

## 6. Dentro i container di test

- Senza `--view` il VICE di test usa un proprio schermo virtuale (`xvfb-run -a`) ed è **senza suono** (`-sounddev dummy`, quasi sempre in warp):
  non serve il viewer.
- Con `--view` (o `C64_VIEW=1`) apre la sua finestra sullo schermo del viewer, sempre senza suono.
- `play.sh` è l'unico caso con il suono: usa `-sounddev pulse`, il tastierino numerico per il joystick 2 e il keyset 1 su F13-F17 per il joystick 1
  (`tools/vice/play.vicerc`, caricato con `-addconfig`).
- `vc64web` è un secondo emulatore, usato solo dai test `EMU-*`. Gira dentro il suo container con un Chromium headless pilotato da Playwright; il
  container ha un `HEALTHCHECK` su `/ping` e `--shm-size 1g`.

## 7. Perché è fatto così

| Scelta | Motivo |
|---|---|
| Toolchain generica in `toolchain/`, progetto che la configura con `toolchain.env` | si può riusare per altri giochi per C64 senza copiare nulla del gioco |
| Un Dockerfile multi-stage con base comune senza nome | un solo punto per cambiare Ubuntu, layer condivisi, nessuna immagine «base» da gestire |
| Compilatori solo negli stage `*-build` | le immagini finali restano piccole; la cache di BuildKit evita di ricompilare VICE a ogni build |
| Due emulatori in due container separati (VICE, vc64web) | decisione del committente: basi e dipendenze molto diverse (gtk3/Xvfb contro Node/Chromium) |
| Viewer separato dagli emulatori | si può guardare e provare senza il builder; schermo e audio condivisi con qualunque container tramite un volume |
| Video e audio via volume e socket Unix | niente rete tra container, nessun codec lato emulatore; Xvnc codifica una volta sola per il browser |
| Porta solo su `127.0.0.1` | lo schermo X non ha autenticazione (`-ac`): chi monta il volume può disegnarci; l'accesso da fuori richiede un tunnel (SSH) |

## 8. Cosa non è verificato

- **Docker su Windows (WSL2/Docker Desktop)**: tutto qui è stato provato in un solo ambiente Linux. Il comportamento di `127.0.0.1:6080`, del volume
  `c64-x11` e dei socket Unix su Windows è *[non verificato]* (TODO I9).
- **Memoria condivisa X (MIT-SHM)**: non può essere condivisa fra due container (IPC separati). Se VICE la richiede, ripiega sul socket, ma non ho verificato che lo faccia.
- **Browser e tastiera reali, schermo a sfioramento, gamepad fisico** per l'overlay (TODO J13); **audio con un browser vero** in WSL2/Windows.
- **Client VNC nativi** (TigerVNC, ecc.): oggi non ci si può collegare, perché Xvnc non pubblica una porta RFB; vedi la discussione nel TODO se verrà aggiunta.
- Il **monitor remoto di VICE** nei test si blocca di tanto in tanto (TODO I11): durante le prove di questa sessione si è bloccato quando chiudevo la
  connessione subito dopo il comando `x`; non è dimostrato che sia la stessa causa dei blocchi nei test.
