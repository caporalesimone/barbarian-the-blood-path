# Prototipo: audio degli emulatori nel browser (13/11, passo C)

Copyright © 2026 - Simone Caporale

Materiale di **studio**, non usato dalla build. Confronto fra due modi di portare nel browser **immagine e audio** dello schermo
degli emulatori (oggi il viewer usa noVNC, che non trasporta l'audio). Decisione aperta nel TODO (J12).

## Cosa e' stato provato
| | Guacamole | KasmVNC |
|---|---|---|
| Componenti | `c64-emu-viewer` + PulseAudio (scheda nulla, socket e TCP anonimi) + `guacd` 1.6.0 (immagine ufficiale) + tunnel `guacamole-lite` 1.2.0 (Node) + pagina con `guacamole-common-js` 1.5.0 | immagine `lscr.io/linuxserver/baseimage-kasmvnc:ubuntunoble` (Xvnc di KasmVNC + client web + kclient Node per l'audio + PulseAudio + nginx + openbox) |
| Audio | da PulseAudio, letto da `guacd` e mandato **nello stesso WebSocket** dell'immagine | kclient legge PulseAudio e lo manda su un **canale separato** (socket.io), riprodotto con WebAudio |
| Cartella | `viewer/`, `guac/` | (immagine pronta, nessun file) |

Evento di prova (`viewer/event.sh`, `event_kasm.sh`): a un istante T (orologio della macchina) il fondo dello schermo X diventa
rosso (`xsetroot`) e parte un tono da 1 kHz (`paplay tone.wav`), 10 volte. Nel browser (Chromium headless di Playwright, sulla
stessa macchina) `hook.js` registra quando il rosso compare sul canvas (controllo a ogni fotogramma, ~16 ms) e quando il tono
supera la soglia all'uscita audio della pagina (AnalyserNode inserito prima della destinazione, controllo ogni 2-4 ms).
`measure.py URL CONTAINER N [click]` stampa i ritardi.

## Risultati [MISURATO 13/11, due serie da 10 eventi ciascuna, macchina cloud, browser headless locale]
| | Guacamole | KasmVNC |
|---|---|---|
| Immagine (ritardo mediano, min-max) | 124 / 137 ms (100-155) | 97 / 99 ms (47-107) |
| Audio (ritardo mediano, min-max) | 248 / 246 ms (242-311) | 13 / 20 ms (9-27) |
| Audio rispetto all'immagine | **in ritardo** di ~120 ms (94-197) | **in anticipo** di ~80 ms (26-95) |
| Immagini Docker | guacd 377 MB + tunnel 332 MB (base node:22 gia' usata da vc64web: propri ~3 MB) + viewer con PulseAudio 1,08 GB (+280 MB rispetto a 803) | 3,02 GB (la base di linuxserver contiene un desktop intero) |
| Memoria a riposo | viewer 55 MB + guacd 11 MB + tunnel 15 MB | 90 MB |
| VICE vero (`c64-emu-vice`, `-sounddev pulse`, tono continuo del SID da `sidtone.prg`) | **funziona** al primo colpo: `PULSE_SERVER=tcp:viewer:4713`, schermo con il volume X come oggi | **funziona** dopo 4 aggiustamenti (sotto) |

VICE 3.10 della toolchain e' compilato con PulseAudio (`Sound: Available sound devices: pulse alsa dummy ...`).

## Aggiustamenti necessari per KasmVNC (immagine di linuxserver)
- `DISABLE_IPV6=true`: senza, nginx non parte in una macchina senza IPv6.
- Un `xterm` a tutto schermo parte da solo (autostart): va tolto.
- Schermo da un altro container: cartella del socket X con permessi 1777 prima dell'avvio, e `xhost +local:`.
- PulseAudio chiede il cookie: serve un socket anonimo in piu' (`pactl load-module module-native-protocol-unix auth-anonymous=1
  socket=/tmp/.X11-unix/pulse`). Montare `/defaults` come volume rompe l'audio di kclient ("unable to init audio").
- VICE si apre massimizzato (openbox).

## Limiti delle misure
- Browser e server sulla stessa macchina (niente rete vera, niente WSL2/Windows); browser headless.
- L'immagine passa da strade diverse: con Guacamole x11vnc **legge** lo schermo di Xvfb a intervalli, KasmVNC e' lui stesso il server X.
- Non misurati: ritardo dei comandi (tastiera, joystick), consumo con VICE a 50 fps per molti minuti, qualita' dell'audio.
- La variante "noVNC + flusso HTTP Opus di ffmpeg" non e' stata misurata (stima del 13/11: 1-3 s di ritardo).
- Una KasmVNC "leggera" (solo Xvnc + client web + un ponte audio) al posto dell'immagine di linuxserver dovrebbe pesare molto meno:
  **non provata**.

## Rifarlo
```sh
cd lab/viewer-audio && python3 make_files.py && cp tone.wav viewer/
docker build -t proto-viewer-audio viewer && docker build -t proto-guac-lite guac     # guac: --secret id=ca,... dietro proxy
docker network create proto; docker run -d --name viewer --network proto proto-viewer-audio
docker run -d --name guacd --network proto guacamole/guacd:1.6.0
docker run -d --name guaclite --network proto -p 127.0.0.1:8080:8080 -p 127.0.0.1:8081:8081 proto-guac-lite
python3 measure.py http://localhost:8081/ viewer 10                 # serve Playwright per Python
```
