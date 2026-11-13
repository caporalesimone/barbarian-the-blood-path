#!/bin/sh
# PulseAudio di sistema con scheda nulla; client locali (socket) e TCP (guacd) senza autenticazione
mkdir -p /run/pulse
pulseaudio --system --disallow-exit --exit-idle-time=-1 -n \
  -L "module-null-sink sink_name=out rate=44100" -L "module-native-protocol-unix auth-anonymous=1 socket=/run/pulse/native" \
  -L "module-native-protocol-tcp auth-anonymous=1 port=4713" -L "module-always-sink" --daemonize=yes --log-target=stderr 2>/tmp/pulse.log
sleep 1; pactl -s unix:/run/pulse/native set-default-sink out 2>/dev/null
exec sh /opt/viewer/start.sh
