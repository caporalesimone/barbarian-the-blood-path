#!/bin/sh
# avvio del viewer: schermo :99 (accesso libero ai client locali: -ac, solo socket, niente TCP), VNC su 5900 interno, noVNC su 6080
set -e
W=${VIEW_SIZE:-1280x1000x24}
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
Xvfb :99 -screen 0 "$W" -ac -nolisten tcp -extension MIT-SHM &   # niente memoria condivisa X: i client stanno in altri container
for i in $(seq 50); do [ -S /tmp/.X11-unix/X99 ] && break; sleep 0.1; done
chmod 777 /tmp/.X11-unix
x11vnc -display :99 -noshm -forever -shared -nopw -rfbport 5900 -quiet -bg -o /tmp/x11vnc.log
echo "viewer pronto: http://localhost:6080"
exec websockify --web /usr/share/novnc 6080 localhost:5900
