#!/bin/sh
# Avvio di c64-emu-viewer (13/11). Copyright (c) 2026 - Simone Caporale
#   schermo :99 (client locali senza autorizzazione X: -ac; solo socket, niente TCP), VNC su 5900 interno,
#   server web su 6080: pagina indice (/), noVNC (/novnc/), cartella out/ del progetto in sola lettura (/out/).
# Variabili: VIEW_SIZE (1280x1000x24), VIEW_PASSWORD (password VNC; vuota = nessuna), VIEW_DISK (disco proposto nell'indice:
#   nome o modello con *, es. game_v*.d64; vuoto = il .d64 piu' recente in /out/).
set -e
W=${VIEW_SIZE:-1280x1000x24}
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
Xvfb :99 -screen 0 "$W" -ac -nolisten tcp -extension MIT-SHM &   # niente memoria condivisa X: i client stanno in altri container
for i in $(seq 50); do [ -S /tmp/.X11-unix/X99 ] && break; sleep 0.1; done
chmod 777 /tmp/.X11-unix
if [ -n "${VIEW_PASSWORD:-}" ]; then
    x11vnc -storepasswd "$VIEW_PASSWORD" /tmp/vncpass >/dev/null 2>&1; AUTH="-rfbauth /tmp/vncpass"
else
    AUTH="-nopw"
fi
# shellcheck disable=SC2086
x11vnc -display :99 -noshm -forever -shared $AUTH -rfbport 5900 -quiet -bg -o /tmp/x11vnc.log
# radice del server web: indice + noVNC + out/ (montata dal progetto in /srv/www/out, se c'e')
mkdir -p /srv/www
cp /opt/viewer/index.html /srv/www/index.html
ln -sfn /usr/share/novnc /srv/www/novnc
D=$(printf '%s' "${VIEW_DISK:-}" | sed 's/["\\]//g')
printf 'window.VIEW_DISK = "%s";\n' "$D" > /srv/www/config.js
echo "viewer pronto: http://localhost:6080"
exec websockify --web /srv/www 6080 localhost:5900
