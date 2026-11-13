#!/bin/sh
# Avvio di c64-emu-viewer (13/11). Copyright (c) 2026 - Simone Caporale
#   schermo :99 = Xvnc di KasmVNC (client locali senza autorizzazione X: -ac; solo socket, niente TCP; WebSocket su 127.0.0.1:6901)
#   audio = PulseAudio, scheda virtuale "c64"; i client (VICE negli altri container) usano il socket anonimo /tmp/.X11-unix/pulse
#   server web su 6080 (server.js): indice, schermo dal vivo con audio, out/ del progetto
# Variabili: VIEW_SIZE (1280x1000), VIEW_PASSWORD (facoltativa), VIEW_DISK (disco proposto nell'indice).
set -e
G=$(printf '%s' "${VIEW_SIZE:-1280x1000}" | cut -dx -f1,2)          # accetta anche il vecchio formato 1280x1000x24
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99 /tmp/.X11-unix/pulse
mkdir -p /tmp/.X11-unix /run/pulse; chmod 1777 /tmp/.X11-unix
pulseaudio --system --disallow-exit --disallow-module-loading --exit-idle-time=-1 -n \
  -L "module-null-sink sink_name=c64 rate=44100" \
  -L "module-native-protocol-unix auth-anonymous=1 socket=/run/pulse/native" \
  -L "module-native-protocol-unix auth-anonymous=1 socket=/tmp/.X11-unix/pulse" \
  -L "module-always-sink" --daemonize=yes --log-target=stderr 2>/tmp/pulse.log
mkdir -p /root/.vnc; touch /root/.kasmpasswd
# -PublicIP: senza, Xvnc 1.5 interroga server STUN su Internet prima di aprire la porta web
Xvnc :99 -geometry "$G" -depth 24 -ac -nolisten tcp -extension MIT-SHM -PublicIP 127.0.0.1 \
  -websocketPort 6901 -interface 127.0.0.1 -disableBasicAuth -SecurityTypes None -sslOnly 0 -AlwaysShared \
  -httpd /usr/share/kasmvnc/www -RectThreads 0 -Log '*:stderr:30' > /tmp/xvnc.log 2>&1 &
for i in $(seq 50); do [ -S /tmp/.X11-unix/X99 ] && break; sleep 0.1; done
chmod 777 /tmp/.X11-unix/pulse 2>/dev/null || true
cd /opt/viewer && PULSE_SERVER=unix:/run/pulse/native exec node server.js
