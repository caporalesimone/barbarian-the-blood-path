#!/bin/sh
# PROTOTIPO: schermo :99 = Xvnc di KasmVNC (client web su 6901), audio = PulseAudio (scheda auto_null) + kclient (6900)
set -e
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99; mkdir -p /tmp/.X11-unix /run/pulse; chmod 1777 /tmp/.X11-unix
pulseaudio --system --disallow-exit --exit-idle-time=-1 -n \
  -L "module-null-sink sink_name=auto_null rate=44100" \
  -L "module-native-protocol-unix auth-anonymous=1 socket=/run/pulse/native" \
  -L "module-native-protocol-unix auth-anonymous=1 socket=/tmp/.X11-unix/pulse" \
  -L "module-always-sink" --daemonize=yes --log-target=stderr 2>/tmp/pulse.log
mkdir -p /root/.vnc; touch /root/.kasmpasswd
Xvnc :99 -geometry ${VIEW_SIZE:-1280x1000} -depth 24 -ac -nolisten tcp -extension MIT-SHM \
  -PublicIP 127.0.0.1 -websocketPort 6901 -interface 0.0.0.0 -disableBasicAuth -SecurityTypes None -sslOnly 0 -AlwaysShared \
  -httpd /usr/share/kasmvnc/www -RectThreads 0 -Log '*:stderr:30' > /tmp/xvnc.log 2>&1 &
for i in $(seq 50); do [ -S /tmp/.X11-unix/X99 ] && break; sleep 0.1; done
chmod 777 /tmp/.X11-unix/pulse 2>/dev/null || true
cd /kclient && PULSE_SERVER=unix:/run/pulse/native exec node index.js
